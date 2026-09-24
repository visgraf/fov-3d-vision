"""Evaluate one .blend -> FSG1 bridge fixation without feeding truth to stereo.

The evaluator reads evaluator-only first-hit truth after fsg_stereo.py has already
produced its result.  It reports geometry/coverage diagnostics and checks only the
bridge integrity invariants; it does not introduce a new Classroom stereo-quality
threshold in this first seam test.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fsg_geometry import project_h


SCHEMA = "FSG-BLEND-BRIDGE1-evaluation-v1"


def pct(a: np.ndarray, q: float) -> float:
    return float(np.percentile(a, q)) if len(a) else float("nan")


def evaluate(run: Path) -> dict:
    run = run.resolve()
    acq = json.loads((run / "acquisition.json").read_text())
    if acq.get("source") != "blender_scene_tangent_perspective":
        raise ValueError("not a production FSG blend-bridge acquisition")
    if acq.get("truth_in_observation") is not False:
        raise ValueError("truth separation contract not recorded")
    if acq.get("foveated_warp_used") or acq.get("stereo_field_used"):
        raise ValueError("wrong measurement lineage: bridge must use the FSG1 tangent instrument")

    with np.load(run / "observation.npz", allow_pickle=False) as z:
        if set(z.files) != {"rgb_L", "rgb_R", "instance_L", "instance_R"}:
            raise ValueError("observation must contain RGB and instance IDs only")
        obs = {k: z[k] for k in z.files}
    c = json.loads((run / "calibration.json").read_text())
    with np.load(run / "stereo" / "result.npz", allow_pickle=False) as z:
        result = {k: z[k] for k in z.files}
    summary = json.loads((run / "stereo" / "summary.json").read_text())
    with np.load(run / "evaluation_only" / "truth_L.npz", allow_pickle=False) as z:
        truth = {k: z[k] for k in z.files}

    valid = np.asarray(result["valid"], bool)
    xyz = np.asarray(result["xyz_h"], float)
    ids = np.asarray(result["instance_id"], int)
    ranges = np.asarray(result["range_left_m"], float)
    accepted = int(valid.sum())
    if accepted != int(summary["valid_count"]):
        raise ValueError("stereo result and summary valid counts disagree")
    if accepted < 100:
        raise ValueError(f"bridge produced too few accepted FSG points for an integrity probe: {accepted}")

    pts = xyz[valid]
    uv, zcam = project_h(c["eyes"][0], pts)
    u = np.rint(uv[:, 0]).astype(int)
    v = np.rint(uv[:, 1]).astype(int)
    h, w = truth["instance_id"].shape
    inside = (u >= 0) & (u < w) & (v >= 0) & (v < h) & np.isfinite(uv).all(1) & (zcam > 0)
    if int(inside.sum()) < 100:
        raise ValueError("too few accepted points reproject into the raw left tangent raster")

    u = u[inside]
    v = v[inside]
    est_range = ranges[valid][inside]
    est_id = ids[valid][inside]
    ref_range = truth["range_m"][v, u].astype(float)
    ref_id = truth["instance_id"][v, u].astype(int)
    ref_ok = (ref_id > 0) & np.isfinite(ref_range)
    if int(ref_ok.sum()) < 100:
        raise ValueError("too few accepted points have evaluator-only first-hit truth")

    est_range = est_range[ref_ok]
    est_id = est_id[ref_ok]
    ref_range = ref_range[ref_ok]
    ref_id = ref_id[ref_ok]
    abs_err = np.abs(est_range - ref_range)
    rel_err = abs_err / np.maximum(ref_range, 1e-9)
    wrong = est_id != ref_id

    # Coverage is reported on the accepted FSG core only; the first bridge test is
    # about representation compatibility, not full-object completeness.
    core_pixels = int(valid.size)
    metrics = {
        "schema": SCHEMA,
        "bridge_integrity_pass": True,
        "quality_gate_declared": False,
        "accepted_points": accepted,
        "core_pixels": core_pixels,
        "accepted_fraction_core": float(accepted / core_pixels),
        "truth_compared_points": int(len(abs_err)),
        "wrong_instance_count_nearest_raw_truth": int(wrong.sum()),
        "wrong_instance_fraction_nearest_raw_truth": float(wrong.mean()),
        "absolute_range_error_m": {
            "median": pct(abs_err, 50),
            "p95": pct(abs_err, 95),
            "max": float(abs_err.max()),
        },
        "relative_range_error": {
            "median": pct(rel_err, 50),
            "p95": pct(rel_err, 95),
            "max": float(rel_err.max()),
        },
        "note": "Nearest raw-pixel truth is diagnostic. No stereo-quality threshold is introduced by Bridge-1.",
    }
    (run / "bridge_evaluation.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(
        "[fsg-blend-bridge-eval] PASS "
        f"accepted={accepted}/{core_pixels} "
        f"median_abs_mm={1000*metrics['absolute_range_error_m']['median']:.3f} "
        f"p95_abs_mm={1000*metrics['absolute_range_error_m']['p95']:.3f} "
        f"wrong_id={metrics['wrong_instance_count_nearest_raw_truth']}"
    )
    return metrics


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run", type=Path)
    args = ap.parse_args()
    evaluate(args.run)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[fsg-blend-bridge-eval] FAIL {type(e).__name__}: {e}", file=sys.stderr)
        raise SystemExit(1)
