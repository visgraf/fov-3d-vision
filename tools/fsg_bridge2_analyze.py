"""Evaluator-only structured-scene diagnostics for one completed Bridge-2 fixation.

Reads FSG stereo output and quarantined Blender truth after stereo has completed.
It never changes estimator validity or geometry.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fsg_geometry import project_h

SCHEMA = "FSG-BLEND-BRIDGE2-analysis-v1"


def _stats(err: np.ndarray) -> dict:
    err = np.asarray(err, float)
    if not len(err):
        return {"count": 0}
    return {
        "count": int(len(err)),
        "median_abs_mm": float(np.percentile(err, 50) * 1000),
        "p75_abs_mm": float(np.percentile(err, 75) * 1000),
        "p90_abs_mm": float(np.percentile(err, 90) * 1000),
        "p95_abs_mm": float(np.percentile(err, 95) * 1000),
        "within_25mm_fraction": float((err <= 0.025).mean()),
        "within_50mm_fraction": float((err <= 0.050).mean()),
        "within_100mm_fraction": float((err <= 0.100).mean()),
    }


def _interior3(ids: np.ndarray) -> np.ndarray:
    ids = np.asarray(ids, np.int32)
    h, w = ids.shape
    out = ids > 0
    pad = np.pad(ids, 1, mode="constant", constant_values=0)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0:
                continue
            out &= pad[1 + dy:1 + dy + h, 1 + dx:1 + dx + w] == ids
    return out


def analyze(run: Path) -> dict:
    run = run.resolve()
    acq = json.loads((run / "acquisition.json").read_text())
    if acq.get("truth_in_observation") is not False:
        raise ValueError("truth separation contract missing")
    if acq.get("tangent_frame_mode") != "baseline_projected":
        raise ValueError("Bridge-2 expects baseline-projected tangent frame")
    cal = json.loads((run / "calibration.json").read_text())
    with np.load(run / "stereo" / "result.npz", allow_pickle=False) as z:
        result = {k: z[k] for k in z.files}
    with np.load(run / "evaluation_only" / "truth_L.npz", allow_pickle=False) as z:
        truth = {k: z[k] for k in z.files}

    valid = np.asarray(result["valid"], bool)
    pts = np.asarray(result["xyz_h"], float)[valid]
    est_range = np.asarray(result["range_left_m"], float)[valid]
    est_id = np.asarray(result["instance_id"], int)[valid]
    uv, zcam = project_h(cal["eyes"][0], pts)
    u = np.rint(uv[:, 0]).astype(int)
    v = np.rint(uv[:, 1]).astype(int)
    h, w = truth["instance_id"].shape
    inside = (u >= 0) & (u < w) & (v >= 0) & (v < h) & np.isfinite(uv).all(1) & (zcam > 0)
    u, v = u[inside], v[inside]
    est_range, est_id = est_range[inside], est_id[inside]
    ref_range = np.asarray(truth["range_m"], float)[v, u]
    ref_id = np.asarray(truth["instance_id"], int)[v, u]
    ok = (ref_id > 0) & np.isfinite(ref_range)
    u, v = u[ok], v[ok]
    est_range, est_id, ref_range, ref_id = est_range[ok], est_id[ok], ref_range[ok], ref_id[ok]
    err = np.abs(est_range - ref_range)

    interior_map = _interior3(np.asarray(truth["instance_id"], int))
    interior = interior_map[v, u]
    boundary = ~interior

    per_instance = []
    for iid in sorted(np.unique(ref_id)):
        m = ref_id == iid
        if int(m.sum()) < 25:
            continue
        row = {"instance_id": int(iid), **_stats(err[m])}
        row["wrong_id_fraction"] = float((est_id[m] != ref_id[m]).mean())
        row["reference_range_median_m"] = float(np.median(ref_range[m]))
        per_instance.append(row)
    per_instance.sort(key=lambda r: (-r["count"], r["instance_id"]))

    q = np.percentile(ref_range, [0, 25, 50, 75, 100])
    depth_quartiles = []
    for i in range(4):
        lo, hi = float(q[i]), float(q[i + 1])
        if i < 3:
            m = (ref_range >= lo) & (ref_range < hi)
        else:
            m = (ref_range >= lo) & (ref_range <= hi)
        depth_quartiles.append({"lo_m": lo, "hi_m": hi, **_stats(err[m])})

    out = {
        "schema": SCHEMA,
        "evaluator_only": True,
        "estimator_output_modified": False,
        "accepted_points": int(valid.sum()),
        "truth_compared_points": int(len(err)),
        "wrong_instance_count": int((est_id != ref_id).sum()),
        "wrong_instance_fraction": float((est_id != ref_id).mean()),
        "overall": _stats(err),
        "single_instance_3x3_interior": _stats(err[interior]),
        "instance_boundary_3x3_band": _stats(err[boundary]),
        "boundary_fraction_of_compared": float(boundary.mean()),
        "per_reference_instance": per_instance,
        "reference_depth_quartiles": depth_quartiles,
    }
    (run / "bridge2_analysis.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(
        "[fsg-bridge2-analyze] COMPLETE "
        f"compared={len(err)} boundary={boundary.mean():.3f} wrong={out['wrong_instance_fraction']:.4f} "
        f"median={out['overall']['median_abs_mm']:.2f}mm p95={out['overall']['p95_abs_mm']:.2f}mm"
    )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run", type=Path)
    a = ap.parse_args()
    analyze(a.run)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[fsg-bridge2-analyze] FAIL {type(e).__name__}: {e}", file=sys.stderr)
        raise SystemExit(1)
