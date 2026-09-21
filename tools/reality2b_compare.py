"""Aggregate the two Reality Check 2b descriptive records without quality gating."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from fsg_geometry import json_write


def load_metrics(path: Path) -> dict:
    p = path / "metrics.json" if path.is_dir() else path
    return json.loads(p.read_text())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("records", nargs=2, type=Path)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    ms = [load_metrics(p) for p in a.records]
    structural = []
    for m in ms:
        if m.get("status") != "REALITY2B_OBSERVATION_COMPLETE":
            structural.append(f"seed {m.get('seed')} integrity record incomplete")
        structural.extend([f"seed {m.get('seed')}: {x}" for x in m.get("integrity_fails", [])])
    finals = [float(m["visible_truth_coverage_final"]) for m in ms]
    summary = {
        "status": "REALITY2B_COMPLETE" if not structural else "REALITY2B_INTEGRITY_FAIL",
        "structural_fails": structural,
        "seeds": [int(m["seed"]) for m in ms],
        "termination_reasons": [m["termination_reason"] for m in ms],
        "fixation_counts": [int(m["fixation_count"]) for m in ms],
        "empty_observation_counts": [int(m["empty_observation_count"]) for m in ms],
        "empty_observation_steps": [m["empty_observation_steps"] for m in ms],
        "recovered_after_first_empty": [bool(m["recovered_after_first_empty"]) for m in ms],
        "final_coverage_range": [min(finals), max(finals)],
        "final_coverage_abs_seed_difference": abs(finals[0] - finals[1]),
        "coverage_gain_after_reality1_stop": [m["visible_truth_coverage_gain_after_reality1_stop"] for m in ms],
        "surface_median_range_m": [min(float(m["approx_surface_median_m"]) for m in ms), max(float(m["approx_surface_median_m"]) for m in ms)],
        "surface_p95_range_m": [min(float(m["approx_surface_p95_m"]) for m in ms), max(float(m["approx_surface_p95_m"]) for m in ms)],
        "quality_gated": False,
        "interpretation": "descriptive two-seed comparison; no numerical quality threshold",
    }
    a.out.mkdir(parents=True, exist_ok=False)
    json_write(a.out / "comparison.json", summary)
    print("[reality2b-compare] " + summary["status"], json.dumps(summary, sort_keys=True), flush=True)
    raise SystemExit(0 if not structural else 2)


if __name__ == "__main__":
    main()
