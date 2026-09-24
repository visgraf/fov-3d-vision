"""Offline evaluation for Classroom-Oracle-2 boundary ablation.

The evaluator compares the widened-domain run against the completed
Classroom-Oracle-1 baseline on the exact same original-domain dense samples,
then measures coverage in the widened domain.  It is the only Oracle-2 program
that opens dense Blender truth.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import classroom_oracle2_public as public


def _json(path: Path) -> Any:
    return json.loads(path.read_text())


def _write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _load_map(path: Path) -> np.ndarray:
    if not path.exists():
        return np.empty((0, 3), np.float64)
    with np.load(path, allow_pickle=False) as z:
        x = np.asarray(z["xyz_h"], np.float64)
    if x.ndim != 2 or x.shape[1] != 3:
        raise ValueError(f"bad map XYZ: {path}: {x.shape}")
    return x[np.isfinite(x).all(axis=1)]


def covered(reference: np.ndarray, surfels: np.ndarray, radius: float) -> np.ndarray:
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


def _domain_distance(angles: np.ndarray, bounds: dict[str, float]) -> np.ndarray:
    a = np.asarray(angles, np.float64)
    y = a[:, 0]
    p = a[:, 1]
    return np.minimum.reduce([
        y - bounds["yaw_min_deg"], bounds["yaw_max_deg"] - y,
        p - bounds["pitch_min_deg"], bounds["pitch_max_deg"] - p,
    ])


def _edge_bins(angles: np.ndarray, cov: np.ndarray, bounds: dict[str, float]) -> list[dict[str, Any]]:
    d = _domain_distance(angles, bounds)
    edges = [0.0, 1.0, 2.0, 4.0, 6.0, 10.0, math.inf]
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (d >= lo) & (d < hi)
        n = int(m.sum())
        miss = int((m & ~cov).sum())
        rows.append({
            "distance_from_nearest_domain_edge_deg": [lo, None if math.isinf(hi) else hi],
            "samples": n,
            "covered": n - miss,
            "uncovered": miss,
            "uncovered_fraction": float(miss / n) if n else None,
        })
    return rows


def _load_truth(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    with np.load(path, allow_pickle=False) as z:
        ids = np.asarray(z["instance_id"], np.int32)
        xyz = np.asarray(z["xyz_h"], np.float64)
        angles = np.asarray(z["yaw_pitch_deg"], np.float64)
    if not (len(ids) == len(xyz) == len(angles)):
        raise ValueError(f"truth arrays disagree in {path}")
    return ids, xyz, angles


def _fraction(num: int, den: int):
    return float(num / den) if den else None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True, type=Path)
    ap.add_argument("--baseline-run", type=Path, default=Path(public.BASELINE_RUN_DEFAULT))
    args = ap.parse_args()
    root = args.run.resolve()
    baseline = args.baseline_run.resolve()

    manifest = _json(root / "manifest.json")
    base_manifest = _json(baseline / "manifest.json")
    if not manifest.get("control_complete") or manifest.get("smoke"):
        raise RuntimeError("evaluate only a completed non-smoke Oracle-2 run")
    if not base_manifest.get("control_complete") or base_manifest.get("smoke"):
        raise RuntimeError("baseline must be a completed non-smoke Oracle-1 run")
    if bool(manifest.get("dense_evaluation_truth_opened_during_control", True)):
        raise RuntimeError("Oracle-2 manifest does not certify dense-truth isolation")

    old_truth_path = root / "bootstrap" / "evaluation_only" / "original_domain_reachable_samples.npz"
    wide_truth_path = root / "bootstrap" / "evaluation_only" / "reachable_samples.npz"
    old_ids, old_xyz, old_angles = _load_truth(old_truth_path)
    wide_ids, wide_xyz, wide_angles = _load_truth(wide_truth_path)

    baseline_seeds = _json(baseline / "bootstrap" / "seeds.json")
    target_ids = [int(x["instance_id"]) for x in baseline_seeds["instances"]]
    target_set = set(target_ids)
    if len(target_ids) != public.TARGET_INSTANCE_COUNT:
        raise RuntimeError("baseline target set is not the expected 25 instances")

    wide_visible_all = sorted(int(x) for x in np.unique(wide_ids) if int(x) > 0)
    wide_only_ids = sorted(set(wide_visible_all) - target_set)
    radius = float(public.FUSION["association_radius_m"])
    run_by_id = {int(o["instance_id"]): o for o in manifest["objects"]}
    base_by_id = {int(o["instance_id"]): o for o in base_manifest["objects"]}
    if set(run_by_id) != target_set:
        raise RuntimeError("Oracle-2 full run did not attempt exactly the baseline target set")

    rows = []
    aggregate = {
        "old_samples": 0,
        "base_old_covered": 0,
        "o2_old_covered": 0,
        "baseline_misses": 0,
        "baseline_misses_recovered": 0,
        "baseline_hits_regressed": 0,
        "wide_samples": 0,
        "o2_wide_covered": 0,
    }
    old_cov_all = []
    old_angles_all = []
    wide_cov_all = []
    wide_angles_all = []

    for iid in target_ids:
        old_m = old_ids == iid
        wide_m = wide_ids == iid
        old_ref = old_xyz[old_m]
        old_ang = old_angles[old_m]
        wide_ref = wide_xyz[wide_m]
        wide_ang = wide_angles[wide_m]

        base_map = _load_map(baseline / "objects" / f"instance_{iid:04d}" / "final_map.npz")
        o2_map = _load_map(root / "objects" / f"instance_{iid:04d}" / "final_map.npz")
        base_old = covered(old_ref, base_map, radius)
        o2_old = covered(old_ref, o2_map, radius)
        o2_wide = covered(wide_ref, o2_map, radius)

        n_old = len(old_ref)
        n_wide = len(wide_ref)
        base_hits = int(base_old.sum())
        o2_old_hits = int(o2_old.sum())
        o2_wide_hits = int(o2_wide.sum())
        misses = ~base_old
        recovered = int((misses & o2_old).sum())
        regressed = int((base_old & ~o2_old).sum())

        aggregate["old_samples"] += n_old
        aggregate["base_old_covered"] += base_hits
        aggregate["o2_old_covered"] += o2_old_hits
        aggregate["baseline_misses"] += int(misses.sum())
        aggregate["baseline_misses_recovered"] += recovered
        aggregate["baseline_hits_regressed"] += regressed
        aggregate["wide_samples"] += n_wide
        aggregate["o2_wide_covered"] += o2_wide_hits
        old_cov_all.append(o2_old)
        old_angles_all.append(old_ang)
        wide_cov_all.append(o2_wide)
        wide_angles_all.append(wide_ang)

        o2_obj = run_by_id[iid]
        base_obj = base_by_id.get(iid, {})
        rows.append({
            "instance_id": iid,
            "object_name": o2_obj.get("object_name"),
            "baseline_fixations": int(base_obj.get("fixation_count", 0)),
            "oracle2_fixations": int(o2_obj.get("fixation_count", 0)),
            "oracle2_termination": o2_obj.get("termination"),
            "oracle2_looks_outside_original_domain": int(o2_obj.get("domain_audit", {}).get("looks_outside_original_domain", 0)),
            "original_domain_reachable_samples": n_old,
            "baseline_original_covered": base_hits,
            "baseline_original_coverage_fraction": _fraction(base_hits, n_old),
            "oracle2_original_covered": o2_old_hits,
            "oracle2_original_coverage_fraction": _fraction(o2_old_hits, n_old),
            "baseline_misses": int(misses.sum()),
            "baseline_misses_recovered_by_oracle2": recovered,
            "baseline_miss_recovery_fraction": _fraction(recovered, int(misses.sum())),
            "baseline_hits_regressed_in_oracle2": regressed,
            "wide_domain_reachable_samples": n_wide,
            "oracle2_wide_covered": o2_wide_hits,
            "oracle2_wide_coverage_fraction": _fraction(o2_wide_hits, n_wide),
            "oracle2_wide_uncovered": n_wide - o2_wide_hits,
        })

    old_cov_concat = np.concatenate(old_cov_all) if old_cov_all else np.empty(0, bool)
    old_ang_concat = np.concatenate(old_angles_all) if old_angles_all else np.empty((0, 2), float)
    wide_cov_concat = np.concatenate(wide_cov_all) if wide_cov_all else np.empty(0, bool)
    wide_ang_concat = np.concatenate(wide_angles_all) if wide_angles_all else np.empty((0, 2), float)

    old_n = int(aggregate["old_samples"])
    wide_n = int(aggregate["wide_samples"])
    base_old_hits = int(aggregate["base_old_covered"])
    o2_old_hits = int(aggregate["o2_old_covered"])
    o2_wide_hits = int(aggregate["o2_wide_covered"])
    misses = int(aggregate["baseline_misses"])
    recovered = int(aggregate["baseline_misses_recovered"])
    regressed = int(aggregate["baseline_hits_regressed"])

    old_dist = _domain_distance(old_ang_concat, public.ORIGINAL_DOMAIN)
    wide_dist = _domain_distance(wide_ang_concat, public.WIDE_DOMAIN)
    old_interior = old_dist > 6.0
    wide_interior = wide_dist > 6.0

    result = {
        "schema": "ClassroomOracle2-evaluation-v1",
        "spec_id": public.SPEC_ID,
        "scientific_delta": "controller angular extent only: +/-25,+/-20 -> +/-35,+/-30 degrees",
        "association_radius_m": radius,
        "target_instance_count": len(target_ids),
        "wide_visible_instance_count_all": len(wide_visible_all),
        "wide_visible_non_target_instance_ids": wide_only_ids,
        "baseline_total_fixations": int(base_manifest.get("total_fixations", 0)),
        "oracle2_total_fixations": int(manifest.get("total_fixations", 0)),
        "oracle2_looks_outside_original_domain": int(manifest.get("looks_outside_original_domain", 0)),
        "original_domain": {
            "bounds_deg": public.SCIENTIFIC_CONTRACT["baseline_domain_deg"],
            "reachable_samples": old_n,
            "baseline_covered": base_old_hits,
            "baseline_coverage_fraction": _fraction(base_old_hits, old_n),
            "oracle2_covered": o2_old_hits,
            "oracle2_coverage_fraction": _fraction(o2_old_hits, old_n),
            "coverage_change_fraction_points": None if not old_n else float((o2_old_hits - base_old_hits) / old_n),
            "baseline_misses": misses,
            "baseline_misses_recovered": recovered,
            "baseline_miss_recovery_fraction": _fraction(recovered, misses),
            "baseline_hits_regressed": regressed,
            "oracle2_interior_gt6deg_coverage_fraction": _fraction(int((old_cov_concat & old_interior).sum()), int(old_interior.sum())),
            "oracle2_within6deg_edge_coverage_fraction": _fraction(int((old_cov_concat & ~old_interior).sum()), int((~old_interior).sum())),
            "edge_bins": _edge_bins(old_ang_concat, old_cov_concat, public.ORIGINAL_DOMAIN),
        },
        "wide_domain": {
            "bounds_deg": public.SCIENTIFIC_CONTRACT["wide_domain_deg"],
            "reachable_target_samples": wide_n,
            "covered": o2_wide_hits,
            "coverage_fraction": _fraction(o2_wide_hits, wide_n),
            "uncovered": wide_n - o2_wide_hits,
            "interior_gt6deg_coverage_fraction": _fraction(int((wide_cov_concat & wide_interior).sum()), int(wide_interior.sum())),
            "within6deg_edge_coverage_fraction": _fraction(int((wide_cov_concat & ~wide_interior).sum()), int((~wide_interior).sum())),
            "edge_bins": _edge_bins(wide_ang_concat, wide_cov_concat, public.WIDE_DOMAIN),
        },
        "objects": rows,
        "scientific_pass_fail_threshold": None,
        "interpretation_contract": [
            "If Oracle-1 misses inside the old domain are recovered when they become interior to the wider controller domain, the old extent was limiting coverage.",
            "If old-domain misses remain despite additional angular room, inspect frontier/shoreline eligibility rather than retuning the matcher or fusion.",
            "If misses migrate outward and concentrate at the new +/-35,+/-30 boundary, the residual is a generic finite-domain boundary effect.",
        ],
    }
    _write(root / "evaluation.json", result)
    print("[classroom-oracle2-eval] COMPLETE", json.dumps({
        "baseline_old_coverage": result["original_domain"]["baseline_coverage_fraction"],
        "oracle2_old_coverage": result["original_domain"]["oracle2_coverage_fraction"],
        "baseline_miss_recovery": result["original_domain"]["baseline_miss_recovery_fraction"],
        "oracle2_wide_coverage": result["wide_domain"]["coverage_fraction"],
        "oracle2_fixations": result["oracle2_total_fixations"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
