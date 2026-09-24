"""Bridge-4 evaluator-only analysis of the controlled two-plane depth sweep.

Reads only already-computed FSG stereo results plus quarantined analytic truth.
It never runs or modifies the matcher.

For every accepted far-surface pixel:
    alpha = (d_est - d_true) / (d_near - d_true)
alpha >= 0.5 means the estimate lies closer to the near disparity plateau than to the
pixel's own true far disparity.

The sweep manipulates only far-plane depth while keeping camera, near silhouette,
texture realization (within each seed block), baseline, vergence, tangent frame and
matcher fixed. Three repeated texture seeds are aggregated per depth.
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

SCHEMA = "FSG-BLEND-BRIDGE4-analysis-v1"
CAPTURE_ALPHA_THRESHOLD = 0.5
ROW_DISTANCE_EDGES_PX = (0.0, 4.0, 8.0, 16.0, 32.0, 64.0, float("inf"))
EUCLIDEAN_CONTROL_BANDS_PX = ((4.0, 12.0), (12.0, 24.0))


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
    for y in range(h):
        xs = np.flatnonzero(mask[y])
        if not len(xs):
            continue
        q = np.arange(w)
        out[y] = np.min(np.abs(q[:, None] - xs[None, :]), axis=1)
    return out


def _rectified_truth(cal: dict[str, Any], truth: dict[str, np.ndarray]) -> dict[str, np.ndarray | float]:
    rect = rectification(cal)
    w, h = map(int, cal["image_size_wh"])
    x, y, core_w, core_h = map(int, np.asarray(rect["crop_xywh"]).tolist())
    k = np.asarray(cal["eyes"][0]["K"], float)
    r1 = np.asarray(rect["R1"], float)
    p1 = np.asarray(rect["P1"], float)
    p2 = np.asarray(rect["P2"], float)
    mapx, mapy = cv2.initUndistortRectifyMap(
        k, np.zeros(5), r1, p1[:, :3], (w, h), cv2.CV_32FC1
    )
    mapx = mapx[y:y + core_h, x:x + core_w]
    mapy = mapy[y:y + core_h, x:x + core_w]
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
    xyz_c = (xyz - centre) @ r_hc
    xyz_rect = xyz_c @ r1.T
    z_rect = xyz_rect[..., 2]
    bf = float(-p2[0, 3])
    if not (bf > 0.0 and abs(float(p2[1, 3])) < 1e-7):
        raise ValueError("Bridge-4 expects horizontal positive-disparity FSG rectification")
    with np.errstate(divide="ignore", invalid="ignore"):
        disp = bf / z_rect
    disp[(ids <= 0) | ~np.isfinite(z_rect) | (z_rect <= 0)] = np.nan
    return {"instance_id": ids, "xyz_h": xyz, "z_rect_m": z_rect, "disparity_px": disp, "bf_px_m": bf}


def _capture_map(path: Path, near: np.ndarray, far: np.ndarray, valid: np.ndarray, captured: np.ndarray) -> None:
    h, w = near.shape
    img = np.full((h, w, 3), 96, np.uint8)
    img[near] = (235, 235, 235)
    img[far & ~valid] = (20, 20, 20)
    img[far & valid & ~captured] = (60, 180, 60)
    img[far & valid & captured] = (50, 50, 230)
    cv2.imwrite(str(path), cv2.resize(img, (w * 5, h * 5), interpolation=cv2.INTER_NEAREST))


def _row_profile(far_valid: np.ndarray, captured: np.ndarray, row_dist: np.ndarray) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lo, hi in zip(ROW_DISTANCE_EDGES_PX[:-1], ROW_DISTANCE_EDGES_PX[1:]):
        m = far_valid & (row_dist >= lo) & (row_dist < hi)
        rows.append({
            "lo_px": float(lo),
            "hi_px": None if math.isinf(hi) else float(hi),
            "accepted_far_count": int(m.sum()),
            "capture_fraction": float(captured[m].mean()) if int(m.sum()) else None,
        })
    no_row = far_valid & ~np.isfinite(row_dist)
    rows.append({
        "lo_px": None,
        "hi_px": None,
        "label": "no_near_support_on_row",
        "accepted_far_count": int(no_row.sum()),
        "capture_fraction": float(captured[no_row].mean()) if int(no_row.sum()) else None,
    })
    return rows


def analyze_condition(run: Path) -> dict[str, Any]:
    run = run.resolve()
    acq = json.loads((run / "acquisition.json").read_text())
    if acq.get("source") != "analytic_two_plane_tangent_perspective":
        raise ValueError(f"not a Bridge-4 analytic condition: {run}")
    if acq.get("truth_in_observation") is not False or acq.get("blender_used") is not False:
        raise ValueError("Bridge-4 provenance contract missing")
    if acq.get("stereo_field_used") or acq.get("foveated_warp_used"):
        raise ValueError("wrong measurement lineage")
    cal = json.loads((run / "calibration.json").read_text())
    with np.load(run / "stereo" / "result.npz", allow_pickle=False) as z:
        result = {k: z[k] for k in z.files}
    with np.load(run / "evaluation_only" / "truth_L.npz", allow_pickle=False) as z:
        truth = {k: z[k] for k in z.files}

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
        raise ValueError("near truth surface absent from rectified core")
    near_disp = float(np.median(near_true))
    gap = near_disp - true_disp
    alpha = np.full(valid.shape, np.nan, float)
    ok = far & valid & np.isfinite(est_disp) & np.isfinite(true_disp) & (gap > 1e-6)
    alpha[ok] = (est_disp[ok] - true_disp[ok]) / gap[ok]
    captured = np.zeros(valid.shape, bool)
    captured[ok] = alpha[ok] >= CAPTURE_ALPHA_THRESHOLD

    dist = cv2.distanceTransform((~near).astype(np.uint8), cv2.DIST_L2, 5).astype(np.float32)
    row_dist = _same_row_distance(near)
    far_valid = ok
    far_captured = far_valid & captured
    far_correct = far_valid & ~captured

    # Matched Euclidean-distance control: same image distance, but either with or without
    # any near support on the pixel's own epipolar row.
    controls = []
    for lo, hi in EUCLIDEAN_CONTROL_BANDS_PX:
        band = far_valid & (dist >= lo) & (dist < hi)
        onrow = band & np.isfinite(row_dist)
        offrow = band & ~np.isfinite(row_dist)
        controls.append({
            "euclidean_lo_px": lo,
            "euclidean_hi_px": hi,
            "same_row_count": int(onrow.sum()),
            "same_row_capture_fraction": float(captured[onrow].mean()) if int(onrow.sum()) else None,
            "no_near_row_count": int(offrow.sum()),
            "no_near_row_capture_fraction": float(captured[offrow].mean()) if int(offrow.sum()) else None,
        })

    captured_row_dist = row_dist[far_captured & np.isfinite(row_dist)]
    captured_euclid = dist[far_captured]
    far_true_vals = true_disp[far & np.isfinite(true_disp)]
    far_disp = float(np.median(far_true_vals)) if len(far_true_vals) else float("nan")
    out = {
        "schema": SCHEMA,
        "analysis_only": True,
        "stereo_rerun": False,
        "estimator_output_modified": False,
        "truth_used_only_after_stereo": True,
        "condition": {
            "run": str(run),
            "far_depth_m": float(acq["far_depth_m"]),
            "texture_seed": int(acq["texture_seed"]),
            "near_depth_m": float(acq["near_depth_m"]),
            "near_instance_id": near_id,
            "far_instance_id": far_id,
            "left_instance_mask_sha256": acq["instance_mask_sha256"]["L"],
        },
        "disparity_truth": {
            "near_median_px": near_disp,
            "far_median_px": far_disp,
            "gap_median_px": float(near_disp - far_disp),
        },
        "far_surface": {
            "truth_pixels": int(far.sum()),
            "accepted_pixels": int(far_valid.sum()),
            "accepted_fraction": float(far_valid.sum() / far.sum()) if int(far.sum()) else None,
            "captured_pixels": int(far_captured.sum()),
            "capture_fraction_of_accepted": float(far_captured.sum() / far_valid.sum()) if int(far_valid.sum()) else None,
            "alpha": _stats(alpha[far_valid]),
            "captured_euclidean_distance_px": _stats(captured_euclid),
            "captured_same_row_distance_px": _stats(captured_row_dist),
            "same_row_accepted_pixels": int((far_valid & np.isfinite(row_dist)).sum()),
            "same_row_capture_fraction": float(captured[far_valid & np.isfinite(row_dist)].mean()) if int((far_valid & np.isfinite(row_dist)).sum()) else None,
            "no_near_row_accepted_pixels": int((far_valid & ~np.isfinite(row_dist)).sum()),
            "no_near_row_capture_fraction": float(captured[far_valid & ~np.isfinite(row_dist)].mean()) if int((far_valid & ~np.isfinite(row_dist)).sum()) else None,
        },
        "row_distance_profile": _row_profile(far_valid, captured, row_dist),
        "euclidean_matched_scanline_controls": controls,
        "notes": [
            "Only far-plane depth is manipulated within each texture-seed block.",
            "The near silhouette is fixed and mask hashes are required to match across the sweep.",
            "alpha>=0.5 is the geometric midpoint between own truth and near plateau, not a tuned threshold.",
        ],
    }
    (run / "bridge4_condition.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    _capture_map(run / "bridge4_capture_map.png", near, far, valid, captured)
    return out


def _mean_sd(vals: list[float | None]) -> tuple[float | None, float | None, int]:
    x = np.array([v for v in vals if v is not None and np.isfinite(v)], float)
    if not len(x):
        return None, None, 0
    return float(np.mean(x)), float(np.std(x, ddof=1)) if len(x) > 1 else 0.0, int(len(x))


def _csv_write(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = sorted({k for r in rows for k in r.keys()})
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def analyze_root(root: Path) -> dict[str, Any]:
    root = root.resolve()
    manifest = json.loads((root / "bridge4_manifest.json").read_text())
    dirs = sorted(p for p in root.iterdir() if p.is_dir() and (p / "acquisition.json").is_file())
    if len(dirs) != int(manifest["condition_count"]):
        raise ValueError("condition count does not match Bridge-4 manifest")
    results = []
    for run in dirs:
        if not (run / "stereo" / "result.npz").is_file():
            raise ValueError(f"missing sealed stereo result: {run}")
        results.append(analyze_condition(run))

    # Control invariant: the near/far first-hit silhouette is exactly identical across sweep.
    mask_hashes = {r["condition"]["left_instance_mask_sha256"] for r in results}
    if len(mask_hashes) != 1:
        raise ValueError("near silhouette changed across sweep")

    condition_rows: list[dict[str, Any]] = []
    for r in results:
        fr = r["far_surface"]
        row = {
            "far_depth_m": r["condition"]["far_depth_m"],
            "texture_seed": r["condition"]["texture_seed"],
            "true_gap_median_px": r["disparity_truth"]["gap_median_px"],
            "far_accepted_fraction": fr["accepted_fraction"],
            "far_capture_fraction": fr["capture_fraction_of_accepted"],
            "captured_count": fr["captured_pixels"],
            "same_row_capture_fraction": fr["same_row_capture_fraction"],
            "no_near_row_capture_fraction": fr["no_near_row_capture_fraction"],
            "capture_row_p50_px": fr["captured_same_row_distance_px"].get("median"),
            "capture_row_p90_px": fr["captured_same_row_distance_px"].get("p90"),
            "capture_row_p95_px": fr["captured_same_row_distance_px"].get("p95"),
            "capture_row_max_px": fr["captured_same_row_distance_px"].get("max"),
        }
        condition_rows.append(row)

    depth_rows: list[dict[str, Any]] = []
    for depth in manifest["far_depths_m"]:
        subset = [r for r in condition_rows if math.isclose(float(r["far_depth_m"]), float(depth), abs_tol=1e-9)]
        if not subset:
            continue
        gap_mean, gap_sd, n = _mean_sd([r["true_gap_median_px"] for r in subset])
        cap_mean, cap_sd, _ = _mean_sd([r["far_capture_fraction"] for r in subset])
        acc_mean, acc_sd, _ = _mean_sd([r["far_accepted_fraction"] for r in subset])
        p90_mean, p90_sd, p90_n = _mean_sd([r["capture_row_p90_px"] for r in subset])
        p95_mean, p95_sd, p95_n = _mean_sd([r["capture_row_p95_px"] for r in subset])
        same_mean, same_sd, _ = _mean_sd([r["same_row_capture_fraction"] for r in subset])
        off_mean, off_sd, _ = _mean_sd([r["no_near_row_capture_fraction"] for r in subset])
        depth_rows.append({
            "far_depth_m": float(depth),
            "n_texture_seeds": n,
            "gap_mean_px": gap_mean,
            "gap_sd_px": gap_sd,
            "far_accepted_fraction_mean": acc_mean,
            "far_accepted_fraction_sd": acc_sd,
            "capture_fraction_mean": cap_mean,
            "capture_fraction_sd": cap_sd,
            "capture_row_p90_mean_px": p90_mean,
            "capture_row_p90_sd_px": p90_sd,
            "capture_row_p90_n": p90_n,
            "capture_row_p95_mean_px": p95_mean,
            "capture_row_p95_sd_px": p95_sd,
            "capture_row_p95_n": p95_n,
            "same_row_capture_fraction_mean": same_mean,
            "same_row_capture_fraction_sd": same_sd,
            "no_near_row_capture_fraction_mean": off_mean,
            "no_near_row_capture_fraction_sd": off_sd,
        })

    # Descriptive fit across manipulated depth conditions. A slope is reported, not
    # interpreted as a universal law. Only depths with a finite mean reach enter.
    fit_rows = [r for r in depth_rows if r["gap_mean_px"] is not None and r["capture_row_p90_mean_px"] is not None]
    fit: dict[str, Any] = {"n_depth_conditions": len(fit_rows)}
    if len(fit_rows) >= 3:
        x = np.array([r["gap_mean_px"] for r in fit_rows], float)
        y = np.array([r["capture_row_p90_mean_px"] for r in fit_rows], float)
        slope, intercept = np.polyfit(x, y, 1)
        pred = slope * x + intercept
        ss_res = float(np.sum((y - pred) ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        fit.update({
            "slope_px_reach_per_px_gap": float(slope),
            "intercept_px": float(intercept),
            "r2": float(1.0 - ss_res / ss_tot) if ss_tot > 1e-12 else None,
            "gap_min_px": float(np.min(x)),
            "gap_max_px": float(np.max(x)),
        })

    summary = {
        "schema": "FSG-BLEND-BRIDGE4-sweep-analysis-v1",
        "analysis_only": True,
        "stereo_rerun_by_analyzer": False,
        "estimator_output_modified": False,
        "truth_used_only_after_stereo": True,
        "manipulation": {
            "variable": "far_plane_depth_m",
            "near_depth_m": manifest["near_depth_m"],
            "far_depths_m": manifest["far_depths_m"],
            "texture_seeds": manifest["texture_seeds"],
            "fixed_near_silhouette": True,
            "left_mask_sha256": next(iter(mask_hashes)),
        },
        "condition_count": len(results),
        "depth_summary": depth_rows,
        "descriptive_gap_to_capture_reach_fit": fit,
        "interpretation_contract": [
            "A monotone reach-vs-gap relation would support disparity-dependent capture scale under this synthetic texture regime.",
            "A weak or absent relation would reject the simple depth-gap scaling hypothesis for this controlled setup.",
            "Same-row versus no-near-row comparisons test epipolar organization independently of depth sweep.",
            "No matcher repair is attempted in Bridge-4.",
        ],
    }
    (root / "bridge4_sweep_analysis.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    _csv_write(root / "bridge4_conditions.csv", condition_rows)
    _csv_write(root / "bridge4_depth_summary.csv", depth_rows)
    print(
        "[fsg-bridge4-analyze] COMPLETE "
        f"conditions={len(results)} depths={len(depth_rows)} fit_n={fit.get('n_depth_conditions', 0)}"
    )
    return summary


def self_test() -> None:
    near = np.zeros((20, 30), bool)
    near[5:15, 10:16] = True
    row = _same_row_distance(near)
    assert np.isinf(row[2]).all()
    assert row[10, 16] == 1.0 and row[10, 20] == 5.0
    valid = np.ones_like(near, bool)
    captured = np.zeros_like(near, bool)
    captured[5:15, 16:20] = True
    prof = _row_profile(valid, captured, row)
    vals = [r.get("capture_fraction") for r in prof if r.get("capture_fraction") is not None]
    assert vals and max(vals) > 0.0
    print("[fsg-bridge4-analyze] self-test PASS")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", nargs="?", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.root is None:
        ap.error("root is required unless --self-test is used")
    analyze_root(args.root)


if __name__ == "__main__":
    main()
