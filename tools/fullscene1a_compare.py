"""Integrity comparator for completed FullScene-1a snapshot records."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import fullscene1a_public as public


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
        if m.get("fullscene_initial_condition") is not True or m.get("snapshot_id") != public.SNAPSHOT_ID:
            fails.append(f"{p}: FullScene S0 initial condition missing")
        if int(m.get("acquisitions_added", -1)) != 0 or int(m.get("fusion_iterations_added", -1)) != 0:
            fails.append(f"{p}: snapshot changed sensing or geometry")
        if int(m.get("growth_iterations_added", -1)) != 0 or int(m.get("epistemic_handoffs_added", -1)) != 0:
            fails.append(f"{p}: snapshot executed object behavior")
        if m.get("scene_objects_read_only") is not True or m.get("parent_files_modified") is not False:
            fails.append(f"{p}: scene integrity broken")
        if m.get("deferred_local_action_executed") is not False:
            fails.append(f"{p}: deferred 3h local action was executed")
        if m.get("automatic_scene_scheduler") is not False or m.get("revisit_scheduler_used") is not False:
            fails.append(f"{p}: scheduler introduced")
        if m.get("new_threshold_added") is not False or m.get("quality_gate_used") is not False:
            fails.append(f"{p}: threshold/quality gate introduced")
        steps = [int(x) for x in m.get("observation_steps", [])]
        if not steps or steps != list(range(18, int(m.get("last_global_step", -1)) + 1)):
            fails.append(f"{p}: declared FullScene history is not contiguous from step 18")
        if len(steps) != int(m.get("observation_count", -1)):
            fails.append(f"{p}: observation count mismatch")
        rows.append({
            "snapshot_id": m.get("snapshot_id"),
            "last_global_step": m.get("last_global_step"),
            "observation_count": m.get("observation_count"),
            "instantiated_object_ids": m.get("instantiated_object_ids"),
            "positive_observed_instance_ids": m.get("positive_observed_instance_ids"),
            "candidate_object_ids": m.get("candidate_object_ids"),
            "selected_object_id": m.get("selected_object_id"),
            "selected_valid_depth_samples": m.get("selected_valid_depth_samples"),
            "selection_status": m.get("selection_status"),
            "next_stage": m.get("next_stage"),
        })
    status = "FULLSCENE1A_COMPLETE" if not fails else "FULLSCENE1A_INTEGRITY_FAIL"
    print("[fullscene1a-compare] " + status + " " + json.dumps({"records": rows, "structural_fails": fails}, sort_keys=True))
    raise SystemExit(0 if not fails else 2)


if __name__ == "__main__":
    main()
