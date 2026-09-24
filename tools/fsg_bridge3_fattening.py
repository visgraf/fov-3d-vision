"""Evaluator-only audit of foreground disparity-plateau capture in Bridge-2.

This tool DOES NOT render, run stereo, change validity, or alter geometry. It reads the
sealed Bridge-2 result plus quarantined Blender truth and asks a narrower question:

    how far, and in what disparity regime, does the dominant near-surface plateau
    capture accepted pixels that truly belong to the dominant farther surface?

For a farther-surface pixel, define the normalized capture coordinate

    alpha = (d_est - d_true) / (d_near - d_true)

where d_near is the median true disparity of the dominant near surface.
alpha=0 is the correct farther-surface disparity; alpha=1 is the near plateau.
alpha>=0.5 is therefore a non-tuned, midpoint definition of "nearer to the foreground
plateau than to the pixel's own true disparity".

Truth is evaluator-only throughout. No output of this script is consumed by FSG stereo.
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
from fsg_geometry import rays_h
from fsg_stereo import rectification

SCHEMA = "FSG-BLEND-BRIDGE3-fattening-v1"
CAPTURE_ALPHA_THRESHOLD = 0.5
DISTANCE_EDGES_PX = (0.0, 3.0, 6.0, 9.0, 12.0, 16.0, 24.0, 32.0, 48.0, 96.0, float("inf"))


def _finite_stats(a: np.ndarray) -> dict[str, float | int]:
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


def _corr(a: np.ndarray, b: np.ndarray) -> float | None:
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    if int(m.sum()) < 3:
        return None
    aa, bb = a[m], b[m]
    if float(np.std(aa)) < 1e-12 or float(np.std(bb)) < 1e-12:
        return None
    return float(np.corrcoef(aa, bb)[0, 1])


def _same_axis_distance(mask: np.ndarray, axis: int) -> np.ndarray:
    """Distance to nearest True pixel in same row (axis=1) or column (axis=0)."""
    mask = np.asarray(mask, bool)
    h, w = mask.shape
    out = np.full((h, w), np.inf, np.float32)
    if axis == 1:
        for y in range(h):
            xs = np.flatnonzero(mask[y])
            if not len(xs):
                continue
            q = np.arange(w)
            out[y] = np.min(np.abs(q[:, None] - xs[None, :]), axis=1)
    elif axis == 0:
        for x in range(w):
            ys = np.flatnonzero(mask[:, x])
            if not len(ys):
                continue
            q = np.arange(h)
            out[:, x] = np.min(np.abs(q[:, None] - ys[None, :]), axis=1)
    else:
        raise ValueError("axis must be 0 or 1")
    return out


def _distance_profile(
    far_mask: np.ndarray,
    valid: np.ndarray,
    captured: np.ndarray,
    alpha: np.ndarray,
    abs_disp_err: np.ndarray,
    dist: np.ndarray,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    edges = DISTANCE_EDGES_PX
    for lo, hi in zip(edges[:-1], edges[1:]):
        band = far_mask & (dist >= lo) & (dist < hi)
        bv = band & valid
        row: dict[str, Any] = {
            "lo_px": float(lo),
            "hi_px": None if math.isinf(hi) else float(hi),
            "far_truth_pixels": int(band.sum()),
            "valid_pixels": int(bv.sum()),
            "valid_fraction": float(bv.sum() / band.sum()) if int(band.sum()) else None,
        }
        if int(bv.sum()):
            row.update({
                "capture_fraction_valid": float(captured[bv].mean()),
                "alpha_median_valid": float(np.median(alpha[bv])),
                "alpha_p90_valid": float(np.percentile(alpha[bv], 90)),
                "abs_disparity_error_median_px": float(np.median(abs_disp_err[bv])),
                "abs_disparity_error_p90_px": float(np.percentile(abs_disp_err[bv], 90)),
            })
        else:
            row.update({
                "capture_fraction_valid": None,
                "alpha_median_valid": None,
                "alpha_p90_valid": None,
                "abs_disparity_error_median_px": None,
                "abs_disparity_error_p90_px": None,
            })
        rows.append(row)
    return rows


def _gap_quartiles(
    far_valid: np.ndarray,
    gap: np.ndarray,
    captured: np.ndarray,
    alpha: np.ndarray,
    dist: np.ndarray,
) -> list[dict[str, Any]]:
    vals = gap[far_valid]
    if not len(vals):
        return []
    q = np.percentile(vals, [0, 25, 50, 75, 100])
    rows: list[dict[str, Any]] = []
    for i in range(4):
        lo, hi = float(q[i]), float(q[i + 1])
        if i < 3:
            m = far_valid & (gap >= lo) & (gap < hi)
        else:
            m = far_valid & (gap >= lo) & (gap <= hi)
        rows.append({
            "lo_disparity_px": lo,
            "hi_disparity_px": hi,
            "count": int(m.sum()),
            "capture_fraction": float(captured[m].mean()) if int(m.sum()) else None,
            "alpha_median": float(np.median(alpha[m])) if int(m.sum()) else None,
            "distance_to_near_median_px": float(np.median(dist[m])) if int(m.sum()) else None,
        })
    return rows


def _interaction_table(
    far_valid: np.ndarray,
    gap: np.ndarray,
    dist: np.ndarray,
    captured: np.ndarray,
) -> dict[str, Any]:
    vals = gap[far_valid]
    if not len(vals):
        return {"gap_quartile_edges_px": [], "distance_bands_px": [], "cells": []}
    gq = np.percentile(vals, [0, 25, 50, 75, 100])
    db = [0.0, 3.0, 6.0, 12.0, 24.0, float("inf")]
    cells = []
    for gi in range(4):
        glo, ghi = float(gq[gi]), float(gq[gi + 1])
        gm = (gap >= glo) & ((gap < ghi) if gi < 3 else (gap <= ghi))
        for di, (dlo, dhi) in enumerate(zip(db[:-1], db[1:])):
            m = far_valid & gm & (dist >= dlo) & (dist < dhi)
            cells.append({
                "gap_quartile": gi + 1,
                "distance_band": di + 1,
                "count": int(m.sum()),
                "capture_fraction": float(captured[m].mean()) if int(m.sum()) else None,
            })
    return {
        "gap_quartile_edges_px": [float(x) for x in gq],
        "distance_bands_px": [0.0, 3.0, 6.0, 12.0, 24.0, None],
        "cells": cells,
    }


def _write_profile_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "lo_px", "hi_px", "far_truth_pixels", "valid_pixels", "valid_fraction",
        "capture_fraction_valid", "alpha_median_valid", "alpha_p90_valid",
        "abs_disparity_error_median_px", "abs_disparity_error_p90_px",
    ]
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def _capture_map_png(
    path: Path,
    near_mask: np.ndarray,
    far_mask: np.ndarray,
    valid: np.ndarray,
    captured: np.ndarray,
) -> None:
    # BGR diagnostic: other=gray, near=white, far-invalid=black,
    # far-valid-correct=green, far-valid-captured=red.
    h, w = near_mask.shape
    img = np.full((h, w, 3), 96, np.uint8)
    img[near_mask] = (235, 235, 235)
    img[far_mask & ~valid] = (20, 20, 20)
    img[far_mask & valid & ~captured] = (60, 180, 60)
    img[far_mask & valid & captured] = (50, 50, 230)
    img = cv2.resize(img, (w * 5, h * 5), interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(str(path), img)


def _rectified_truth(cal: dict, truth: dict[str, np.ndarray]) -> dict[str, np.ndarray | float]:
    rect = rectification(cal)
    w, h = map(int, cal["image_size_wh"])
    x, y, core_w, core_h = map(int, np.asarray(rect["crop_xywh"]).tolist())
    if core_w != core_h or core_w != int(cal["core_size"]):
        raise ValueError("unexpected FSG core geometry")

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
    range_raw = np.asarray(truth["range_m"], float)
    ids = ids_raw[vv_c, uu_c].copy()
    ranges = range_raw[vv_c, uu_c].copy()
    ids[~inside] = 0
    ranges[~inside] = np.nan

    uv_raw = np.stack((uu_c, vv_c), axis=-1).astype(float)
    dirs = rays_h(cal["eyes"][0], uv_raw.reshape(-1, 2)).reshape(core_h, core_w, 3)
    centre = np.asarray(cal["eyes"][0]["centre_h_m"], float)
    pts = centre + dirs * ranges[..., None]
    r_hc = np.asarray(cal["eyes"][0]["R_hc"], float)
    xyz_c = (pts - centre) @ r_hc
    xyz_rect = xyz_c @ r1.T
    z_rect = xyz_rect[..., 2]
    bf = float(-p2[0, 3])
    if not (bf > 0 and abs(float(p2[1, 3])) < 1e-7):
        raise ValueError("Bridge-3 expects horizontal positive-disparity FSG rectification")
    with np.errstate(divide="ignore", invalid="ignore"):
        disp = bf / z_rect
    disp[(ids <= 0) | ~np.isfinite(ranges) | (z_rect <= 0)] = np.nan
    return {
        "instance_id": ids,
        "range_m": ranges,
        "z_rect_m": z_rect,
        "disparity_px": disp,
        "map_raw_u": uu.astype(np.int32),
        "map_raw_v": vv.astype(np.int32),
        "bf_px_m": bf,
    }


def analyze(run: Path) -> dict[str, Any]:
    run = run.resolve()
    acq = json.loads((run / "acquisition.json").read_text())
    if acq.get("truth_in_observation") is not False:
        raise ValueError("truth separation contract missing")
    if acq.get("tangent_frame_mode") != "baseline_projected":
        raise ValueError("Bridge-3 expects Bridge-1R/2 baseline-projected tangent frame")
    if acq.get("foveated_warp_used") or acq.get("stereo_field_used"):
        raise ValueError("wrong measurement lineage")

    cal = json.loads((run / "calibration.json").read_text())
    with np.load(run / "stereo" / "result.npz", allow_pickle=False) as z:
        result = {k: z[k] for k in z.files}
    with np.load(run / "evaluation_only" / "truth_L.npz", allow_pickle=False) as z:
        truth = {k: z[k] for k in z.files}

    valid = np.asarray(result["valid"], bool)
    xyz = np.asarray(result["xyz_h"], float)
    if xyz.shape[:2] != valid.shape or xyz.shape[-1] != 3:
        raise ValueError("unexpected result.npz geometry")

    rt = _rectified_truth(cal, truth)
    ids = np.asarray(rt["instance_id"], int)
    true_range = np.asarray(rt["range_m"], float)
    true_disp = np.asarray(rt["disparity_px"], float)
    if ids.shape != valid.shape:
        raise ValueError("rectified evaluator truth and estimator core have different shapes")

    # Estimator disparity derived only from estimator XYZ and frozen calibration.
    rect = rectification(cal)
    r1 = np.asarray(rect["R1"], float)
    p2 = np.asarray(rect["P2"], float)
    bf = float(-p2[0, 3])
    centre = np.asarray(cal["eyes"][0]["centre_h_m"], float)
    r_hc = np.asarray(cal["eyes"][0]["R_hc"], float)
    xyz_c_est = (xyz - centre) @ r_hc
    xyz_rect_est = xyz_c_est @ r1.T
    z_est = xyz_rect_est[..., 2]
    with np.errstate(divide="ignore", invalid="ignore"):
        est_disp = bf / z_est
    est_disp[~valid] = np.nan

    good_truth = (ids > 0) & np.isfinite(true_range) & np.isfinite(true_disp)
    u, c = np.unique(ids[good_truth], return_counts=True)
    pairs = sorted([(int(i), int(k)) for i, k in zip(u, c) if i > 0], key=lambda x: (-x[1], x[0]))
    if len(pairs) < 2:
        raise ValueError("Bridge-3 needs at least two truth instances in the rectified core")
    pair_ids = [pairs[0][0], pairs[1][0]]
    med_ranges = {iid: float(np.median(true_range[ids == iid])) for iid in pair_ids}
    near_id, far_id = sorted(pair_ids, key=lambda iid: med_ranges[iid])
    near_mask = ids == near_id
    far_mask = ids == far_id

    near_disp = float(np.median(true_disp[near_mask & np.isfinite(true_disp)]))
    gap = near_disp - true_disp
    denom_ok = np.isfinite(gap) & (gap > 1e-6)
    alpha = np.full(valid.shape, np.nan, float)
    alpha[denom_ok & valid] = (
        est_disp[denom_ok & valid] - true_disp[denom_ok & valid]
    ) / gap[denom_ok & valid]
    captured = np.zeros(valid.shape, bool)
    captured[far_mask & valid & np.isfinite(alpha)] = alpha[far_mask & valid & np.isfinite(alpha)] >= CAPTURE_ALPHA_THRESHOLD
    abs_disp_err = np.abs(est_disp - true_disp)

    inv_near = (~near_mask).astype(np.uint8)
    dist = cv2.distanceTransform(inv_near, cv2.DIST_L2, 5).astype(np.float32)
    row_dist = _same_axis_distance(near_mask, axis=1)
    col_dist = _same_axis_distance(near_mask, axis=0)

    far_valid = far_mask & valid & np.isfinite(alpha)
    far_captured = far_valid & captured
    far_not_captured = far_valid & ~captured
    if int(far_valid.sum()) == 0:
        raise ValueError("no accepted farther-surface pixels available for fattening analysis")

    distance_rows = _distance_profile(far_mask, valid, captured, alpha, abs_disp_err, dist)
    gap_rows = _gap_quartiles(far_valid, gap, captured, alpha, dist)
    interaction = _interaction_table(far_valid, gap, dist, captured)

    captured_dist = dist[far_captured]
    reach = _finite_stats(captured_dist)
    for threshold in (3.0, 6.0, 12.0, 24.0):
        reach[f"fraction_captured_beyond_{int(threshold)}px"] = (
            float((captured_dist > threshold).mean()) if len(captured_dist) else None
        )

    out = {
        "schema": SCHEMA,
        "analysis_only": True,
        "stereo_rerun": False,
        "estimator_output_modified": False,
        "truth_used_only_after_stereo": True,
        "capture_definition": {
            "alpha_formula": "(d_est-d_true)/(d_near-d_true)",
            "alpha_zero_meaning": "pixel's own true farther-surface disparity",
            "alpha_one_meaning": "dominant near-surface median true disparity",
            "captured_if_alpha_ge": CAPTURE_ALPHA_THRESHOLD,
            "threshold_interpretation": "estimate is at least halfway from its own truth toward the near plateau",
        },
        "rectified_core_shape_hw": [int(valid.shape[0]), int(valid.shape[1])],
        "dominant_pair": {
            "near_instance_id": int(near_id),
            "far_instance_id": int(far_id),
            "near_truth_pixels": int(near_mask.sum()),
            "far_truth_pixels": int(far_mask.sum()),
            "near_median_range_m": med_ranges[near_id],
            "far_median_range_m": med_ranges[far_id],
            "near_median_true_disparity_px": near_disp,
            "far_median_true_disparity_px": float(np.median(true_disp[far_mask & np.isfinite(true_disp)])),
        },
        "far_surface": {
            "truth_pixels": int(far_mask.sum()),
            "accepted_pixels": int(far_valid.sum()),
            "accepted_fraction": float(far_valid.sum() / far_mask.sum()) if int(far_mask.sum()) else None,
            "captured_pixels": int(far_captured.sum()),
            "capture_fraction_of_accepted": float(far_captured.sum() / far_valid.sum()),
            "alpha": _finite_stats(alpha[far_valid]),
            "absolute_disparity_error_px": _finite_stats(abs_disp_err[far_valid]),
            "capture_reach_distance_to_near_px": reach,
            "captured_distance_same_row_px": _finite_stats(row_dist[far_captured]),
            "captured_distance_same_column_px": _finite_stats(col_dist[far_captured]),
            "not_captured_distance_same_row_px": _finite_stats(row_dist[far_not_captured]),
            "not_captured_distance_same_column_px": _finite_stats(col_dist[far_not_captured]),
        },
        "associations_within_far_accepted": {
            "corr_alpha_vs_distance_to_near": _corr(alpha[far_valid], dist[far_valid]),
            "corr_alpha_vs_true_disparity_gap": _corr(alpha[far_valid], gap[far_valid]),
            "corr_capture01_vs_distance_to_near": _corr(captured[far_valid].astype(float), dist[far_valid]),
            "corr_capture01_vs_true_disparity_gap": _corr(captured[far_valid].astype(float), gap[far_valid]),
        },
        "distance_profile": distance_rows,
        "true_disparity_gap_quartiles": gap_rows,
        "distance_x_gap_interaction": interaction,
        "notes": [
            "This is a descriptive audit of one sealed Bridge-2 fixation, not a universal fattening law.",
            "The near plateau is defined from evaluator truth only after stereo; it never changes FSG output.",
            "Distance is Euclidean distance in the rectified core to the dominant near-surface support.",
        ],
    }

    (run / "bridge3_fattening.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    _write_profile_csv(run / "bridge3_distance_profile.csv", distance_rows)
    np.save(run / "bridge3_alpha.npy", alpha.astype(np.float32))
    np.save(run / "bridge3_distance_to_near_px.npy", dist.astype(np.float32))
    np.save(run / "bridge3_truth_disparity_px.npy", true_disp.astype(np.float32))
    np.save(run / "bridge3_est_disparity_px.npy", est_disp.astype(np.float32))
    _capture_map_png(run / "bridge3_capture_map.png", near_mask, far_mask, valid, captured)

    print(
        "[fsg-bridge3-fattening] COMPLETE "
        f"near={near_id} far={far_id} far_valid={int(far_valid.sum())} "
        f"captured={int(far_captured.sum())} "
        f"capture_fraction={float(far_captured.sum()/far_valid.sum()):.4f} "
        f"capture_dist_p95={float(np.percentile(captured_dist,95)) if len(captured_dist) else float('nan'):.2f}px"
    )
    return out


def self_test() -> None:
    h, w = 24, 32
    near = np.zeros((h, w), bool)
    near[:, :8] = True
    far = ~near
    valid = np.ones((h, w), bool)
    d_near = 32.0
    d_true = np.full((h, w), 16.0, float)
    d_true[near] = d_near
    d_est = d_true.copy()
    # Deliberately fatten near disparity five pixels into the far surface.
    d_est[:, 8:13] = d_near
    gap = d_near - d_true
    alpha = np.full((h, w), np.nan, float)
    ok = far & (gap > 0)
    alpha[ok] = (d_est[ok] - d_true[ok]) / gap[ok]
    captured = np.zeros((h, w), bool)
    captured[ok] = alpha[ok] >= CAPTURE_ALPHA_THRESHOLD
    dist = cv2.distanceTransform((~near).astype(np.uint8), cv2.DIST_L2, 5)
    cap_dist = dist[captured]
    assert int(captured.sum()) == h * 5
    assert float(cap_dist.max()) >= 5.0 - 1e-6
    assert float((cap_dist > 3).mean()) > 0.0
    assert not captured[:, 13:].any()
    print("[fsg-bridge3-fattening] self-test PASS")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run", nargs="?", type=Path)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
        return
    if a.run is None:
        ap.error("run is required unless --self-test is used")
    analyze(a.run)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[fsg-bridge3-fattening] FAIL {type(e).__name__}: {e}", file=sys.stderr)
        raise SystemExit(1)
