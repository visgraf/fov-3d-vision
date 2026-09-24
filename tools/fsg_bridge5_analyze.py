"""Bridge-5 evaluator-only analysis for the 2x2 texture x slant factorial.

Reads sealed FSG stereo outputs and quarantined analytic truth only after matching.
No estimator parameter is changed and no stereo is rerun.

Capture definition is inherited unchanged from Bridges 3/4:
  alpha = (d_est - d_true) / (d_near - d_true)
  alpha >= 0.5  => estimate is closer to the near plateau than to own far truth.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys
from typing import Any

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fsg_stereo import rectification

SCHEMA = "FSG-BLEND-BRIDGE5-analysis-v1"
CAPTURE_ALPHA_THRESHOLD = 0.5
EUCLIDEAN_CONTROL_BAND_PX = (4.0, 12.0)


def _stats(a: np.ndarray) -> dict[str, Any]:
    x = np.asarray(a, float)
    x = x[np.isfinite(x)]
    if not len(x):
        return {"count": 0}
    return {
        "count": int(len(x)),
        "median": float(np.percentile(x, 50)),
        "p75": float(np.percentile(x, 75)),
        "p90": float(np.percentile(x, 90)),
        "p95": float(np.percentile(x, 95)),
        "max": float(np.max(x)),
        "mean": float(np.mean(x)),
    }


def _same_row_distance(mask: np.ndarray) -> np.ndarray:
    mask = np.asarray(mask, bool)
    h, w = mask.shape
    out = np.full((h, w), np.inf, np.float32)
    q = np.arange(w)
    for y in range(h):
        xs = np.flatnonzero(mask[y])
        if len(xs):
            out[y] = np.min(np.abs(q[:, None] - xs[None, :]), axis=1)
    return out


def _rect_maps(cal: dict[str, Any]) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    rect = rectification(cal)
    w, h = map(int, cal["image_size_wh"])
    x, y, core_w, core_h = map(int, np.asarray(rect["crop_xywh"]).tolist())
    k = np.asarray(cal["eyes"][0]["K"], float)
    r1 = np.asarray(rect["R1"], float)
    p1 = np.asarray(rect["P1"], float)
    mapx, mapy = cv2.initUndistortRectifyMap(k, np.zeros(5), r1, p1[:, :3], (w, h), cv2.CV_32FC1)
    return rect, mapx[y:y+core_h, x:x+core_w], mapy[y:y+core_h, x:x+core_w]


def _rectified_truth(cal: dict[str, Any], truth: dict[str, np.ndarray]) -> dict[str, np.ndarray | float]:
    rect, mapx, mapy = _rect_maps(cal)
    w, h = map(int, cal["image_size_wh"])
    uu = np.rint(mapx).astype(int)
    vv = np.rint(mapy).astype(int)
    inside = (uu >= 0) & (uu < w) & (vv >= 0) & (vv < h)
    uu_c = np.clip(uu, 0, w - 1)
    vv_c = np.clip(vv, 0, h - 1)
    ids_raw = np.asarray(truth["instance_id"], np.int32)
    xyz_raw = np.asarray(truth["xyz_h"], float)
    ids = ids_raw[vv_c, uu_c].copy()
    xyz = xyz_raw[vv_c, uu_c].copy()
    ids[~inside] = 0
    xyz[~inside] = np.nan
    centre = np.asarray(cal["eyes"][0]["centre_h_m"], float)
    r_hc = np.asarray(cal["eyes"][0]["R_hc"], float)
    r1 = np.asarray(rect["R1"], float)
    p2 = np.asarray(rect["P2"], float)
    xyz_c = (xyz - centre) @ r_hc
    xyz_rect = xyz_c @ r1.T
    z_rect = xyz_rect[..., 2]
    bf = float(-p2[0, 3])
    if not (bf > 0.0 and abs(float(p2[1, 3])) < 1e-7):
        raise ValueError("Bridge-5 expects horizontal positive-disparity rectification")
    with np.errstate(divide="ignore", invalid="ignore"):
        disp = bf / z_rect
    disp[(ids <= 0) | ~np.isfinite(z_rect) | (z_rect <= 0)] = np.nan
    return {"instance_id": ids, "disparity_px": disp, "z_rect_m": z_rect}


def _linear_to_u8(rgb: np.ndarray) -> np.ndarray:
    a = np.clip(np.asarray(rgb, np.float64), 0.0, 1.0)
    a = np.where(a <= 0.0031308, 12.92 * a, 1.055 * np.power(a, 1 / 2.4) - 0.055)
    return np.rint(255.0 * a).astype(np.uint8)


def _rectified_gray(cal: dict[str, Any], rgb: np.ndarray) -> np.ndarray:
    _, mapx, mapy = _rect_maps(cal)
    u8 = _linear_to_u8(rgb)
    gray = cv2.cvtColor(u8, cv2.COLOR_RGB2GRAY)
    return cv2.remap(gray, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT).astype(np.float32)


def _local_std(gray: np.ndarray, k: int = 5) -> np.ndarray:
    g = np.asarray(gray, np.float32)
    mean = cv2.boxFilter(g, cv2.CV_32F, (k, k), normalize=True)
    sq = cv2.boxFilter(g*g, cv2.CV_32F, (k, k), normalize=True)
    return np.sqrt(np.maximum(0.0, sq - mean*mean))


def _texture_stats(gray: np.ndarray, near: np.ndarray, far: np.ndarray) -> dict[str, Any]:
    std = _local_std(gray, 5)
    ker = np.ones((5, 5), np.uint8)
    near_i = cv2.erode(near.astype(np.uint8), ker, iterations=1).astype(bool)
    far_i = cv2.erode(far.astype(np.uint8), ker, iterations=1).astype(bool)
    n = float(np.median(std[near_i])) if near_i.any() else float("nan")
    f = float(np.median(std[far_i])) if far_i.any() else float("nan")
    return {
        "near_local5_std_median_u8": n,
        "far_local5_std_median_u8": f,
        "near_far_ratio": float(n / f) if np.isfinite(n) and np.isfinite(f) and f > 0 else None,
        "near_interior_pixels": int(near_i.sum()),
        "far_interior_pixels": int(far_i.sum()),
    }


def _slant_fit(true_disp: np.ndarray, far: np.ndarray) -> dict[str, Any]:
    yy, xx = np.indices(true_disp.shape)
    ok = far & np.isfinite(true_disp)
    if int(ok.sum()) < 100:
        return {"count": int(ok.sum())}
    A = np.c_[xx[ok], yy[ok], np.ones(int(ok.sum()))]
    coef, *_ = np.linalg.lstsq(A, true_disp[ok], rcond=None)
    return {
        "count": int(ok.sum()),
        "slope_x_px_per_px": float(coef[0]),
        "slope_y_px_per_px": float(coef[1]),
        "p05_px": float(np.percentile(true_disp[ok], 5)),
        "median_px": float(np.median(true_disp[ok])),
        "p95_px": float(np.percentile(true_disp[ok], 95)),
    }


def _capture_map(path: Path, near: np.ndarray, far: np.ndarray, valid: np.ndarray, captured: np.ndarray) -> None:
    h, w = near.shape
    img = np.full((h, w, 3), 96, np.uint8)
    img[near] = (235, 235, 235)
    img[far & ~valid] = (20, 20, 20)
    img[far & valid & ~captured] = (60, 180, 60)
    img[far & valid & captured] = (50, 50, 230)
    cv2.imwrite(str(path), cv2.resize(img, (w*5, h*5), interpolation=cv2.INTER_NEAREST))


def analyze_condition(run: Path) -> dict[str, Any]:
    run = run.resolve()
    acq = json.loads((run / "acquisition.json").read_text())
    if acq.get("source") != "analytic_texture_slant_factorial":
        raise ValueError(f"not a Bridge-5 condition: {run}")
    if acq.get("truth_in_observation") is not False or acq.get("blender_used") is not False:
        raise ValueError("Bridge-5 provenance contract missing")
    cal = json.loads((run / "calibration.json").read_text())
    with np.load(run / "stereo" / "result.npz", allow_pickle=False) as z:
        result = {k: z[k] for k in z.files}
    with np.load(run / "evaluation_only" / "truth_L.npz", allow_pickle=False) as z:
        truth = {k: z[k] for k in z.files}
    with np.load(run / "observation.npz", allow_pickle=False) as z:
        obs = {k: z[k] for k in z.files}
    if set(obs) != {"rgb_L", "rgb_R", "instance_L", "instance_R"}:
        raise ValueError("observation contract changed")

    valid = np.asarray(result["valid"], bool)
    est_disp = np.asarray(result["disparity_px"], float)
    rt = _rectified_truth(cal, truth)
    ids = np.asarray(rt["instance_id"], int)
    true_disp = np.asarray(rt["disparity_px"], float)
    if ids.shape != valid.shape:
        raise ValueError("truth and stereo core shapes differ")
    near_id = int(acq["near_instance_id"])
    far_id = int(acq["far_instance_id"])
    near = ids == near_id
    far = ids == far_id
    near_true = true_disp[near & np.isfinite(true_disp)]
    if not len(near_true):
        raise ValueError("near truth surface absent")
    near_disp = float(np.median(near_true))
    gap = near_disp - true_disp
    ok = far & valid & np.isfinite(est_disp) & np.isfinite(true_disp) & (gap > 1e-6)
    alpha = np.full(valid.shape, np.nan, float)
    alpha[ok] = (est_disp[ok] - true_disp[ok]) / gap[ok]
    captured = np.zeros(valid.shape, bool)
    captured[ok] = alpha[ok] >= CAPTURE_ALPHA_THRESHOLD
    far_captured = ok & captured

    dist = cv2.distanceTransform((~near).astype(np.uint8), cv2.DIST_L2, 5).astype(np.float32)
    row_dist = _same_row_distance(near)
    cap_row = row_dist[far_captured & np.isfinite(row_dist)]
    cap_e = dist[far_captured]
    lo, hi = EUCLIDEAN_CONTROL_BAND_PX
    band = ok & (dist >= lo) & (dist < hi)
    onrow = band & np.isfinite(row_dist)
    offrow = band & ~np.isfinite(row_dist)

    gray = _rectified_gray(cal, obs["rgb_L"])
    tex = _texture_stats(gray, near, far)
    slant = _slant_fit(true_disp, far)
    far_true = true_disp[far & np.isfinite(true_disp)]
    far_disp = float(np.median(far_true)) if len(far_true) else float("nan")
    out = {
        "schema": SCHEMA,
        "analysis_only": True,
        "stereo_rerun": False,
        "estimator_output_modified": False,
        "truth_used_only_after_stereo": True,
        "condition": {
            "run": str(run),
            "slant_level": acq["slant_level"],
            "far_plane_slope_k": float(acq["far_plane_slope_k"]),
            "texture_level": acq["texture_level"],
            "far_texture_gain": float(acq["far_texture_gain"]),
            "texture_seed": int(acq["texture_seed"]),
            "left_instance_mask_sha256": acq["instance_mask_sha256"]["L"],
        },
        "truth_disparity": {
            "near_median_px": near_disp,
            "far_median_px": far_disp,
            "gap_median_px": float(near_disp - far_disp),
            "far_plane_fit": slant,
        },
        "texture_evidence": tex,
        "far_surface": {
            "truth_pixels": int(far.sum()),
            "accepted_pixels": int(ok.sum()),
            "accepted_fraction": float(ok.sum() / far.sum()) if int(far.sum()) else None,
            "captured_pixels": int(far_captured.sum()),
            "capture_fraction_of_accepted": float(far_captured.sum() / ok.sum()) if int(ok.sum()) else None,
            "alpha": _stats(alpha[ok]),
            "captured_euclidean_distance_px": _stats(cap_e),
            "captured_same_row_distance_px": _stats(cap_row),
            "captured_beyond_3px_fraction": float((cap_e > 3.0).mean()) if len(cap_e) else None,
            "same_row_accepted_pixels": int((ok & np.isfinite(row_dist)).sum()),
            "same_row_capture_fraction": float(captured[ok & np.isfinite(row_dist)].mean()) if int((ok & np.isfinite(row_dist)).sum()) else None,
            "no_near_row_accepted_pixels": int((ok & ~np.isfinite(row_dist)).sum()),
            "no_near_row_capture_fraction": float(captured[ok & ~np.isfinite(row_dist)].mean()) if int((ok & ~np.isfinite(row_dist)).sum()) else None,
            "matched_4_12_same_row_n": int(onrow.sum()),
            "matched_4_12_same_row_capture_fraction": float(captured[onrow].mean()) if int(onrow.sum()) else None,
            "matched_4_12_no_row_n": int(offrow.sum()),
            "matched_4_12_no_row_capture_fraction": float(captured[offrow].mean()) if int(offrow.sum()) else None,
        },
    }
    (run / "bridge5_condition.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    _capture_map(run / "bridge5_capture_map.png", near, far, valid, captured)
    return out


def _mean_sd(vals: list[float | None]) -> tuple[float | None, float | None, int]:
    x = np.array([v for v in vals if v is not None and np.isfinite(v)], float)
    if not len(x):
        return None, None, 0
    return float(np.mean(x)), float(np.std(x, ddof=1)) if len(x) > 1 else 0.0, int(len(x))


def _csv_write(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = sorted({k for r in rows for k in r})
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)


def analyze_root(root: Path) -> dict[str, Any]:
    root = root.resolve()
    manifest = json.loads((root / "bridge5_manifest.json").read_text())
    dirs = sorted(p for p in root.iterdir() if p.is_dir() and (p / "acquisition.json").is_file())
    if len(dirs) != int(manifest["condition_count"]):
        raise ValueError("condition count does not match manifest")
    results = []
    for run in dirs:
        if not (run / "stereo" / "result.npz").is_file():
            raise ValueError(f"missing sealed stereo result: {run}")
        results.append(analyze_condition(run))
    hashes = {r["condition"]["left_instance_mask_sha256"] for r in results}
    if len(hashes) != 1:
        raise ValueError("near silhouette changed across factorial")

    rows: list[dict[str, Any]] = []
    for r in results:
        c, td, te, fr = r["condition"], r["truth_disparity"], r["texture_evidence"], r["far_surface"]
        rows.append({
            "slant_level": c["slant_level"],
            "texture_level": c["texture_level"],
            "texture_seed": c["texture_seed"],
            "far_slope_k": c["far_plane_slope_k"],
            "far_texture_gain": c["far_texture_gain"],
            "gap_median_px": td["gap_median_px"],
            "far_slant_y_px_per_px": td["far_plane_fit"].get("slope_y_px_per_px"),
            "near_texture_std_u8": te["near_local5_std_median_u8"],
            "far_texture_std_u8": te["far_local5_std_median_u8"],
            "near_far_texture_ratio": te["near_far_ratio"],
            "far_accepted_fraction": fr["accepted_fraction"],
            "captured_count": fr["captured_pixels"],
            "capture_fraction": fr["capture_fraction_of_accepted"],
            "capture_euclid_p50_px": fr["captured_euclidean_distance_px"].get("median"),
            "capture_euclid_p90_px": fr["captured_euclidean_distance_px"].get("p90"),
            "capture_euclid_max_px": fr["captured_euclidean_distance_px"].get("max"),
            "capture_row_p90_px": fr["captured_same_row_distance_px"].get("p90"),
            "same_row_capture_fraction": fr["same_row_capture_fraction"],
            "no_near_row_capture_fraction": fr["no_near_row_capture_fraction"],
            "matched_4_12_same_row_capture_fraction": fr["matched_4_12_same_row_capture_fraction"],
            "matched_4_12_no_row_capture_fraction": fr["matched_4_12_no_row_capture_fraction"],
        })

    cells: list[dict[str, Any]] = []
    for slant in ("flat", "slanted"):
        for texture in ("equal", "near2x"):
            ss = [r for r in rows if r["slant_level"] == slant and r["texture_level"] == texture]
            if len(ss) != 3:
                raise ValueError(f"expected 3 seeds in cell {slant}/{texture}")
            cell: dict[str, Any] = {"slant_level": slant, "texture_level": texture, "n": len(ss)}
            for field in (
                "gap_median_px", "far_slant_y_px_per_px", "near_far_texture_ratio",
                "far_accepted_fraction", "capture_fraction", "capture_euclid_p90_px",
                "capture_row_p90_px", "same_row_capture_fraction", "no_near_row_capture_fraction",
            ):
                m, sd, n = _mean_sd([r[field] for r in ss])
                cell[field + "_mean"] = m; cell[field + "_sd"] = sd; cell[field + "_n"] = n
            cell["captured_count_total"] = int(sum(int(r["captured_count"]) for r in ss))
            cells.append(cell)

    def cell(s: str, t: str) -> dict[str, Any]:
        return next(x for x in cells if x["slant_level"] == s and x["texture_level"] == t)
    A = cell("flat", "equal")["capture_fraction_mean"]
    B = cell("flat", "near2x")["capture_fraction_mean"]
    C = cell("slanted", "equal")["capture_fraction_mean"]
    D = cell("slanted", "near2x")["capture_fraction_mean"]
    contrasts = {
        "A_flat_equal": A,
        "B_flat_near2x": B,
        "C_slanted_equal": C,
        "D_slanted_near2x": D,
        "texture_effect_when_flat_B_minus_A": None if A is None or B is None else float(B-A),
        "slant_effect_when_equal_C_minus_A": None if A is None or C is None else float(C-A),
        "texture_effect_when_slanted_D_minus_C": None if C is None or D is None else float(D-C),
        "slant_effect_when_near2x_D_minus_B": None if B is None or D is None else float(D-B),
        "factorial_interaction_D_minus_C_minus_B_plus_A": None if any(v is None for v in (A,B,C,D)) else float(D-C-B+A),
    }
    summary = {
        "schema": "FSG-BLEND-BRIDGE5-factorial-analysis-v1",
        "analysis_only": True,
        "stereo_rerun_by_analyzer": False,
        "estimator_output_modified": False,
        "truth_used_only_after_stereo": True,
        "condition_count": len(results),
        "fixed_instance_mask_sha256": next(iter(hashes)),
        "cells": cells,
        "capture_fraction_factorial_contrasts": contrasts,
        "interpretation_contract": [
            "Flat/equal is the Bridge-4-like control cell.",
            "B-A isolates texture-asymmetry effect with geometry flat.",
            "C-A isolates slant effect with texture balanced.",
            "D-C and D-B show each factor in the presence of the other.",
            "The interaction contrast is descriptive; no significance test or post-hoc threshold is introduced.",
            "If all cells show zero capture, neither factor nor their tested interaction is sufficient in this synthetic regime.",
            "No matcher repair is attempted in Bridge-5.",
        ],
    }
    (root / "bridge5_factorial_analysis.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    _csv_write(root / "bridge5_conditions.csv", rows)
    _csv_write(root / "bridge5_cells.csv", cells)
    print(f"[fsg-bridge5-analyze] COMPLETE conditions={len(results)} cells={len(cells)}")
    return summary


def self_test() -> None:
    near = np.zeros((20, 30), bool); near[6:14, 10:16] = True
    row = _same_row_distance(near)
    assert np.isinf(row[2]).all() and row[10, 16] == 1.0
    gray = np.arange(600, dtype=np.float32).reshape(20, 30) % 31
    far = ~near
    tex = _texture_stats(gray, near, far)
    assert tex["near_interior_pixels"] > 0 and tex["far_interior_pixels"] > 0
    d = np.tile(np.linspace(20, 25, 20)[:, None], (1, 30))
    fit = _slant_fit(d, far)
    assert abs(float(fit["slope_y_px_per_px"]) - 5/19) < 1e-6
    print("[fsg-bridge5-analyze] self-test PASS")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", nargs="?", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test(); return
    if args.root is None:
        ap.error("root is required unless --self-test is used")
    analyze_root(args.root)


if __name__ == "__main__":
    main()
