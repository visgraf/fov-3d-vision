"""Offline evaluation for Classroom-Oracle-1.

This is the only host-side experiment program that opens the dense cyclopean
seed-scan truth.  It must be run only after manifest.json records
``control_complete: true``.  The truth is used solely to measure how much of the
fixed-head, controller-domain-visible surface the autonomous loop reconstructed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import classroom_oracle1_public as public


def _json(path: Path) -> Any:
    return json.loads(path.read_text())


def _write(path: Path, x: Any) -> None:
    path.write_text(json.dumps(x, indent=2, sort_keys=True) + "\n")


def _load_map(path: Path) -> np.ndarray:
    if not path.exists():
        return np.empty((0, 3), np.float64)
    with np.load(path, allow_pickle=False) as z:
        x = np.asarray(z["xyz_h"], np.float64)
    if x.ndim != 2 or x.shape[1] != 3:
        raise ValueError(f"bad map XYZ: {path}: {x.shape}")
    return x[np.isfinite(x).all(axis=1)]


def _covered(reference: np.ndarray, surfels: np.ndarray, radius: float) -> np.ndarray:
    """Exact Euclidean radius coverage using a deterministic spatial hash."""
    ref = np.asarray(reference, np.float64)
    pts = np.asarray(surfels, np.float64)
    out = np.zeros(len(ref), bool)
    if not len(ref) or not len(pts):
        return out
    cell = float(radius)
    q = np.floor(pts / cell).astype(np.int64)
    table: dict[tuple[int, int, int], list[int]] = {}
    for i, c in enumerate(q):
        table.setdefault(tuple(map(int, c)), []).append(i)
    qr = np.floor(ref / cell).astype(np.int64)
    r2 = radius * radius
    for i, c in enumerate(qr):
        candidates: list[int] = []
        cx, cy, cz = map(int, c)
        for dz in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    candidates.extend(table.get((cx + dx, cy + dy, cz + dz), ()))
        if candidates:
            d = pts[np.asarray(candidates)] - ref[i]
            out[i] = bool(np.any(np.einsum("ij,ij->i", d, d) <= r2))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True, type=Path)
    args = ap.parse_args()
    root = args.run.resolve()
    manifest = _json(root / "manifest.json")
    if not manifest.get("control_complete"):
        raise RuntimeError("refusing evaluation before the control run is complete")
    if manifest.get("smoke"):
        raise RuntimeError("smoke output is plumbing only; evaluate the full run")

    truth_path = root / "bootstrap" / "evaluation_only" / "reachable_samples.npz"
    with np.load(truth_path, allow_pickle=False) as z:
        truth_ids = np.asarray(z["instance_id"], np.int32)
        truth_xyz = np.asarray(z["xyz_h"], np.float64)
        truth_angles = np.asarray(z["yaw_pitch_deg"], np.float64)
    if len(truth_ids) != len(truth_xyz):
        raise ValueError("evaluation truth arrays disagree")

    radius = float(public.FUSION["association_radius_m"])
    rows = []
    total_ref = 0
    total_cov = 0
    total_fix = 0
    total_zero_new = 0
    terms: dict[str, int] = {}
    all_visible_ids = sorted(int(x) for x in np.unique(truth_ids) if int(x) > 0)
    run_by_id = {int(o["instance_id"]): o for o in manifest["objects"]}

    for iid in all_visible_ids:
        obj = run_by_id.get(iid)
        ref = truth_xyz[truth_ids == iid]
        ref_angles = truth_angles[truth_ids == iid]
        map_path = root / "objects" / f"instance_{iid:04d}" / "final_map.npz"
        sm = _load_map(map_path)
        cov = _covered(ref, sm, radius)
        nref, ncov = len(ref), int(cov.sum())
        total_ref += nref; total_cov += ncov
        if obj is None:
            row = {
                "instance_id": iid,
                "status": "oracle_visible_but_not_attempted",
                "reachable_samples": nref,
                "covered_samples": 0,
                "coverage_fraction": 0.0 if nref else None,
            }
        else:
            fix = int(obj["fixation_count"])
            zero_new = sum(1 for t in obj.get("trajectory", []) if int(t.get("new_surfels", 0)) == 0)
            total_fix += fix; total_zero_new += zero_new
            term = str(obj["termination"]); terms[term] = terms.get(term, 0) + 1
            if nref:
                missed = ref_angles[~cov]
                yaw_span = [float(missed[:, 0].min()), float(missed[:, 0].max())] if len(missed) else None
                pitch_span = [float(missed[:, 1].min()), float(missed[:, 1].max())] if len(missed) else None
            else:
                yaw_span = pitch_span = None
            row = {
                "instance_id": iid,
                "object_name": obj["object_name"],
                "status": "attempted",
                "termination": term,
                "fixations": fix,
                "final_map_surfels": int(obj["final_map_surfels"]),
                "zero_new_surfel_looks": zero_new,
                "incidental_instance_ids": obj.get("incidental_instance_ids", []),
                "reachable_samples": nref,
                "covered_samples": ncov,
                "coverage_fraction": float(ncov / nref) if nref else None,
                "remaining_uncovered_samples": nref - ncov,
                "uncovered_yaw_span_deg": yaw_span,
                "uncovered_pitch_span_deg": pitch_span,
            }
        rows.append(row)

    attempted_ids = set(run_by_id)
    truth_id_set = set(all_visible_ids)
    unexpected = sorted(attempted_ids - truth_id_set)
    result = {
        "schema": "ClassroomOracle1-evaluation-v1",
        "spec_id": public.SPEC_ID,
        "coverage_definition": "dense 0.25-degree cyclopean first-hit samples in the frozen controller angular domain; covered iff within 12 mm of a final surfel",
        "important_scope": "reachable here means fixed-head first-hit surface in the seed-scan/controller domain, not all hidden scene surface",
        "association_radius_m": radius,
        "oracle_visible_instances": len(all_visible_ids),
        "attempted_instances": len(manifest["objects"]),
        "unexpected_attempted_instance_ids": unexpected,
        "total_fixations": total_fix,
        "zero_new_surfel_looks": total_zero_new,
        "termination_counts": terms,
        "reachable_samples_total": total_ref,
        "covered_samples_total": total_cov,
        "coverage_fraction_micro": float(total_cov / total_ref) if total_ref else None,
        "objects": rows,
        "scientific_pass_fail_threshold": None,
        "interpretation": "diagnostic upper-bound experiment; preserve the measured result without retuning the controller",
    }
    _write(root / "evaluation.json", result)
    print("[classroom-oracle1-eval] COMPLETE", json.dumps({
        "instances": len(rows), "fixations": total_fix,
        "coverage": result["coverage_fraction_micro"], "terminations": terms,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
