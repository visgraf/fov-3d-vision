"""Structural comparator for completed MultiObject-3f frontier-reactivation audits."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import multiobject3f_public as public


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("records", nargs="+")
    a = ap.parse_args()
    rows = []
    fails = []
    for p in map(Path, a.records):
        m = json.loads((p / "prediction_manifest.json").read_text())
        if m.get("schema") != public.SPEC_ID:
            fails.append(f"{p}: wrong schema")
            continue
        if m.get("public_spec_sha256") != public.public_digest():
            fails.append(f"{p}: public digest mismatch")
        if m.get("truth_opened") is not False:
            fails.append(f"{p}: evaluator truth opened")
        if int(m.get("acquisitions_added", -1)) != 0 or int(m.get("fusion_iterations_added", -1)) != 0:
            fails.append(f"{p}: read-only contract broken")
        if m.get("returned_local_action_executed") is not False:
            fails.append(f"{p}: returned local action executed")
        if m.get("pre_policy_replayed_exactly") is not True or m.get("post_policy_replayed_exactly") is not True:
            fails.append(f"{p}: pre/post frozen policy replay not exact")
        if m.get("reactivation_status") != "LOCAL_POLICY_REACTIVATION_REPRODUCED":
            fails.append(f"{p}: parent reactivation did not reproduce")
        if m.get("preexisting_objects_read_only") is not True or m.get("selected_object_read_only") is not True:
            fails.append(f"{p}: scene object modified")
        if m.get("new_threshold_added") is not False or m.get("quality_gate_used") is not False:
            fails.append(f"{p}: threshold/quality gate introduced")
        if m.get("watchdog_changed") is not False or m.get("automatic_handoff_loop") is not False:
            fails.append(f"{p}: policy loop contract changed")
        s = m.get("frontier_lineage_summary", {})
        if int(s.get("pre_frontier_count", -1)) < 0 or int(s.get("post_frontier_count", -1)) < 0:
            fails.append(f"{p}: frontier lineage summary missing")
        if (
            int(s.get("persistent_frontier_source_voxels", -1))
            + int(s.get("appeared_frontier_source_voxels", -1))
            != int(s.get("post_frontier_count", -2))
        ):
            fails.append(f"{p}: post frontier lineage partition broken")
        if (
            int(s.get("persistent_frontier_source_voxels", -1))
            + int(s.get("disappeared_frontier_source_voxels", -1))
            != int(s.get("pre_frontier_count", -2))
        ):
            fails.append(f"{p}: pre frontier lineage partition broken")
        rows.append({
            "selected_object_id": m.get("selected_object_id"),
            "reactivation_status": m.get("reactivation_status"),
            "map_voxel_change": m.get("map_voxel_change"),
            "frontier_before": s.get("pre_frontier_count"),
            "frontier_after": s.get("post_frontier_count"),
            "persistent": s.get("persistent_frontier_source_voxels"),
            "appeared": s.get("appeared_frontier_source_voxels"),
            "disappeared": s.get("disappeared_frontier_source_voxels"),
            "appeared_on_preexisting_map_voxels": s.get("appeared_sources_on_preexisting_map_voxels"),
            "appeared_on_new_map_voxels": s.get("appeared_sources_on_new_map_voxels"),
            "candidates_before": m.get("candidate_before_consensus_before"),
            "candidates_after": m.get("candidate_before_consensus_after"),
            "directions_newly_admissible": m.get("directions_newly_admissible"),
            "returned_next_gaze_deg": m.get("returned_next_gaze_deg"),
        })
    status = "MULTIOBJECT3F_COMPLETE" if not fails else "MULTIOBJECT3F_INTEGRITY_FAIL"
    print("[multiobject3f-compare] " + status + " " + json.dumps({"records": rows, "structural_fails": fails}, sort_keys=True))
    raise SystemExit(0 if not fails else 2)


if __name__ == "__main__":
    main()
