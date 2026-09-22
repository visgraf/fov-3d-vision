"""Structural comparator for completed FullScene-REAL-1 benchmark records."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import fullscene_real1_public as public


def _exists(root: Path, rel: str) -> bool:
    return (root / rel).is_file()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("records", nargs="+")
    a = ap.parse_args()
    fails = []
    rows = []
    for p in map(Path, a.records):
        mp = p / "scene_manifest.json"
        if not mp.is_file():
            fails.append(f"{p}: missing scene_manifest.json")
            continue
        m = json.loads(mp.read_text())
        if m.get("schema") != public.SPEC_ID:
            fails.append(f"{p}: wrong schema")
        if m.get("public_spec_sha256") != public.public_digest():
            fails.append(f"{p}: public digest mismatch")
        if m.get("branch") != public.RUN_BRANCH:
            fails.append(f"{p}: wrong branch")
        if m.get("fixed_head") is not True or m.get("static_scene") is not True:
            fails.append(f"{p}: fixed-head/static-scene contract broken")
        if m.get("discovery_tested") is not False or m.get("instance_oracle_used_for_enumeration") is not True:
            fails.append(f"{p}: discovery/oracle scope misstated")
        if m.get("observer_sealed_before_truth") is not True or m.get("evaluator_truth_opened") is not True:
            fails.append(f"{p}: truth phase not quarantined after observer seal")
        ids = [int(x) for x in m.get("object_ids", [])]
        if not ids or ids != sorted(ids) or len(ids) != len(set(ids)) or any(x <= 0 for x in ids):
            fails.append(f"{p}: invalid/dynamic object inventory")
        if int(m.get("attempted_object_count", -1)) != len(ids):
            fails.append(f"{p}: not every enumerated object attempted")
        statuses = m.get("object_statuses", {})
        if set(statuses) != {str(x) for x in ids}:
            fails.append(f"{p}: final status missing for an attempted object")
        if m.get("structural_fails") != []:
            fails.append(f"{p}: structural_fails nonempty")
        required = [
            "observer_complete.json", "fixation_history.json", "object_status_table.json",
            "scene_points.npz", "scene_points.ply", "observer_depth.npy", "observer_instance.npy",
            "observer_valid.png", "observer_depth_preview.png", "reference_rgb.png",
            "reference_depth.npy", "reference_instance.npy", "evaluation_summary.json",
            "per_object_metrics.json", "scene_report.json", "scene_report.md",
        ]
        missing = [x for x in required if not _exists(p, x)]
        if missing:
            fails.append(f"{p}: missing outputs {missing}")
        rows.append({
            "objects": ids,
            "attempted": m.get("attempted_object_count"),
            "instantiated": m.get("instantiated_object_ids"),
            "fixations": m.get("fixation_count"),
            "statuses": statuses,
            "wall_seconds": m.get("wall_seconds"),
        })
    status = "FULLSCENE_REAL1_COMPLETE" if not fails else "FULLSCENE_REAL1_INTEGRITY_FAIL"
    print("[fullscene-real1-compare] " + status + " " + json.dumps({"records": rows, "structural_fails": fails}, sort_keys=True))
    raise SystemExit(0 if not fails else 2)


if __name__ == "__main__":
    main()
