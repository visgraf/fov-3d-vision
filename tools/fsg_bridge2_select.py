"""Pre-stereo deterministic gaze selector for FSG Blend Bridge-2.

The selector reads only Bridge acquisition products and evaluator-only Blender truth.
It MUST run before any candidate has a stereo/ directory, so SGBM outcome cannot
influence gaze selection.

A candidate is eligible only if the 128x128 FSG core (or declared core size):
- is >=95% covered by Blender first-hit truth,
- contains at least two instance groups, each with >=10% core support,
- has robust depth span P90-P10 >=0.40 m,
- has median truth depth jump >=0.20 m across instance boundaries,
- has grayscale texture std >=8 on the fixed FSG u8 transfer.

Among eligible candidates, choose lexicographically by:
1. larger second-instance support fraction,
2. larger median boundary depth jump,
3. larger grayscale texture std,
4. larger robust depth span,
5. smaller |pitch|,
6. smaller wrapped yaw in [-180,180).

These are predeclared selection heuristics, not stereo-quality thresholds.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any

import numpy as np

MIN_HIT_FRACTION = 0.95
MIN_SECOND_INSTANCE_FRACTION = 0.10
MIN_RANGE_SPAN_M = 0.40
MIN_BOUNDARY_JUMP_MEDIAN_M = 0.20
MIN_GRAY_STD_U8 = 8.0
SCHEMA = "FSG-BLEND-BRIDGE2-selection-v1"


def _linear_to_u8(rgb: np.ndarray) -> np.ndarray:
    a = np.clip(np.asarray(rgb, float), 0.0, 1.0)
    a = np.where(a <= 0.0031308, 12.92 * a, 1.055 * np.power(a, 1 / 2.4) - 0.055)
    return np.rint(255 * a).astype(np.uint8)


def _gray_u8(rgb: np.ndarray) -> np.ndarray:
    u = _linear_to_u8(rgb).astype(np.float32)
    return np.rint(u[..., 0] * 0.299 + u[..., 1] * 0.587 + u[..., 2] * 0.114).astype(np.uint8)


def _wrapped_yaw(yaw: float) -> float:
    x = (float(yaw) + 180.0) % 360.0 - 180.0
    return 180.0 if math.isclose(x, -180.0) and yaw > 0 else x


def _core_slice(cal: dict[str, Any]) -> tuple[slice, slice]:
    w, h = map(int, cal["image_size_wh"])
    core = int(cal["core_size"])
    if w != h or core <= 0 or core > min(w, h):
        raise ValueError("unexpected bridge raster/core geometry")
    x = (w - core) // 2
    y = (h - core) // 2
    return slice(y, y + core), slice(x, x + core)


def metrics_from_arrays(ids: np.ndarray, ranges: np.ndarray, rgb: np.ndarray) -> dict[str, Any]:
    ids = np.asarray(ids, dtype=np.int32)
    ranges = np.asarray(ranges, dtype=np.float64)
    rgb = np.asarray(rgb, dtype=np.float32)
    if ids.ndim != 2 or ranges.shape != ids.shape or rgb.shape != ids.shape + (3,):
        raise ValueError("candidate core arrays have inconsistent shapes")

    valid = (ids > 0) & np.isfinite(ranges) & (ranges > 0)
    hit_fraction = float(valid.mean())
    n = int(ids.size)
    support: list[tuple[int, int, float]] = []
    if valid.any():
        u, c = np.unique(ids[valid], return_counts=True)
        support = sorted(
            [(int(i), int(k), float(k / n)) for i, k in zip(u, c) if i > 0],
            key=lambda x: (-x[2], x[0]),
        )
    second_fraction = float(support[1][2]) if len(support) >= 2 else 0.0

    rv = ranges[valid]
    p10 = float(np.percentile(rv, 10)) if len(rv) else float("nan")
    p50 = float(np.percentile(rv, 50)) if len(rv) else float("nan")
    p90 = float(np.percentile(rv, 90)) if len(rv) else float("nan")
    span = float(p90 - p10) if len(rv) else float("nan")

    jumps = []
    for dy, dx in ((0, 1), (1, 0)):
        a_ids = ids[: ids.shape[0] - dy or None, : ids.shape[1] - dx or None]
        b_ids = ids[dy:, dx:]
        a_r = ranges[: ranges.shape[0] - dy or None, : ranges.shape[1] - dx or None]
        b_r = ranges[dy:, dx:]
        ok = (a_ids > 0) & (b_ids > 0) & (a_ids != b_ids) & np.isfinite(a_r) & np.isfinite(b_r)
        if ok.any():
            jumps.append(np.abs(a_r[ok] - b_r[ok]))
    bj = np.concatenate(jumps) if jumps else np.empty(0, dtype=float)
    jump_p50 = float(np.percentile(bj, 50)) if len(bj) else 0.0
    jump_p90 = float(np.percentile(bj, 90)) if len(bj) else 0.0

    gray = _gray_u8(rgb)
    gray_std = float(gray[valid].std()) if valid.any() else 0.0

    return {
        "core_pixels": n,
        "hit_fraction": hit_fraction,
        "instance_support": [
            {"instance_id": i, "count": k, "fraction_core": f} for i, k, f in support
        ],
        "instance_count": len(support),
        "second_instance_fraction": second_fraction,
        "range_p10_m": p10,
        "range_median_m": p50,
        "range_p90_m": p90,
        "range_span_p90_p10_m": span,
        "boundary_pair_count": int(len(bj)),
        "boundary_jump_median_m": jump_p50,
        "boundary_jump_p90_m": jump_p90,
        "gray_std_u8": gray_std,
    }


def evaluate_candidate(run: Path) -> dict[str, Any]:
    run = run.resolve()
    if (run / "stereo").exists():
        raise ValueError(f"candidate already has stereo output; selection must precede SGBM: {run}")
    acq = json.loads((run / "acquisition.json").read_text())
    if acq.get("source") != "blender_scene_tangent_perspective":
        raise ValueError(f"not a bridge tangent acquisition: {run}")
    if acq.get("truth_in_observation") is not False:
        raise ValueError("truth separation contract missing")
    if acq.get("foveated_warp_used") or acq.get("stereo_field_used"):
        raise ValueError("selection candidate came from the wrong measurement lineage")
    if acq.get("tangent_frame_mode") != "baseline_projected":
        raise ValueError("Bridge-2 requires the baseline-projected tangent frame")

    cal = json.loads((run / "calibration.json").read_text())
    sy, sx = _core_slice(cal)
    with np.load(run / "observation.npz", allow_pickle=False) as z:
        if set(z.files) != {"rgb_L", "rgb_R", "instance_L", "instance_R"}:
            raise ValueError("observation contract changed")
        rgb = np.asarray(z["rgb_L"])[sy, sx]
        ids_obs = np.asarray(z["instance_L"])[sy, sx]
    with np.load(run / "evaluation_only" / "truth_L.npz", allow_pickle=False) as z:
        ids = np.asarray(z["instance_id"])[sy, sx]
        ranges = np.asarray(z["range_m"])[sy, sx]
    if not np.array_equal(ids_obs, ids):
        raise ValueError("observation instance IDs and evaluator first-hit IDs disagree in raw core")

    m = metrics_from_arrays(ids, ranges, rgb)
    yaw, pitch = map(float, acq["gaze_yaw_pitch_deg"])
    eligible = (
        m["hit_fraction"] >= MIN_HIT_FRACTION
        and m["second_instance_fraction"] >= MIN_SECOND_INSTANCE_FRACTION
        and m["range_span_p90_p10_m"] >= MIN_RANGE_SPAN_M
        and m["boundary_jump_median_m"] >= MIN_BOUNDARY_JUMP_MEDIAN_M
        and m["gray_std_u8"] >= MIN_GRAY_STD_U8
    )
    m.update({
        "run": str(run),
        "yaw_deg": yaw,
        "pitch_deg": pitch,
        "eligible": bool(eligible),
    })
    return m


def rank_key(m: dict[str, Any]) -> tuple[float, ...]:
    # max() with this key implements the declared lexicographic rule.
    return (
        float(m["second_instance_fraction"]),
        float(m["boundary_jump_median_m"]),
        float(m["gray_std_u8"]),
        float(m["range_span_p90_p10_m"]),
        -abs(float(m["pitch_deg"])),
        -_wrapped_yaw(float(m["yaw_deg"])),
    )


def select(root: Path) -> dict[str, Any]:
    candidates = sorted(p for p in root.resolve().iterdir() if p.is_dir() and (p / "acquisition.json").is_file())
    if not candidates:
        raise ValueError(f"no Bridge acquisition candidates found under {root}")
    rows = [evaluate_candidate(p) for p in candidates]
    eligible = [m for m in rows if m["eligible"]]
    if not eligible:
        raise RuntimeError("no candidate satisfies the predeclared Bridge-2 structured-scene criteria; do not relax thresholds post hoc")
    winner = max(eligible, key=rank_key)
    return {
        "schema": SCHEMA,
        "selection_is_pre_stereo": True,
        "quality_thresholds_are_selection_only": True,
        "criteria": {
            "min_hit_fraction": MIN_HIT_FRACTION,
            "min_second_instance_fraction": MIN_SECOND_INSTANCE_FRACTION,
            "min_range_span_p90_p10_m": MIN_RANGE_SPAN_M,
            "min_boundary_jump_median_m": MIN_BOUNDARY_JUMP_MEDIAN_M,
            "min_gray_std_u8": MIN_GRAY_STD_U8,
            "ranking": [
                "second_instance_fraction descending",
                "boundary_jump_median_m descending",
                "gray_std_u8 descending",
                "range_span_p90_p10_m descending",
                "abs(pitch) ascending",
                "wrapped yaw ascending",
            ],
        },
        "candidate_count": len(rows),
        "eligible_count": len(eligible),
        "winner": winner,
        "candidates": rows,
    }


def self_test() -> None:
    h = w = 20
    ids = np.ones((h, w), np.int32)
    ids[:, 10:] = 2
    rr = np.ones((h, w), np.float32)
    rr[:, 10:] = 2.0
    x = np.linspace(0.05, 0.75, w, dtype=np.float32)
    rgb = np.repeat(np.tile(x, (h, 1))[..., None], 3, axis=2)
    m = metrics_from_arrays(ids, rr, rgb)
    assert math.isclose(m["hit_fraction"], 1.0)
    assert m["instance_count"] == 2
    assert math.isclose(m["second_instance_fraction"], 0.5)
    assert m["range_span_p90_p10_m"] >= 0.9
    assert m["boundary_jump_median_m"] == 1.0
    assert m["gray_std_u8"] > 8.0
    print("[fsg-bridge2-select] self-test PASS")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
        return
    if a.root is None or a.out is None:
        ap.error("--root and --out are required unless --self-test is used")
    result = select(a.root)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    w = result["winner"]
    print(
        "[fsg-bridge2-select] COMPLETE "
        f"candidates={result['candidate_count']} eligible={result['eligible_count']} "
        f"winner=({w['yaw_deg']:.3f},{w['pitch_deg']:.3f}) "
        f"second={w['second_instance_fraction']:.3f} "
        f"span={w['range_span_p90_p10_m']:.3f}m "
        f"jump50={w['boundary_jump_median_m']:.3f}m graystd={w['gray_std_u8']:.2f}"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[fsg-bridge2-select] FAIL {type(e).__name__}: {e}", file=sys.stderr)
        raise SystemExit(1)
