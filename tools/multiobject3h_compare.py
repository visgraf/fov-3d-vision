"""Structural comparator for completed MultiObject-3h local-productivity steps."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import multiobject3h_public as public


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
        if m.get("parent_subsequent_policy_status") != public.PUBLIC_SPEC["required_parent_policy_status"]:
            fails.append(f"{p}: parent did not supply a continuing local action")
        if m.get("pre_action_policy_replayed_exactly") is not True:
            fails.append(f"{p}: parent action not replayed exactly before execution")
        if m.get("executed_parent_subsequent_local_action") is not True or int(m.get("added_fixations", -1)) != 1:
            fails.append(f"{p}: bounded second local action not executed exactly once")
        if int(m.get("subsequent_local_policy_decisions", -1)) != 1:
            fails.append(f"{p}: expected exactly one subsequent local-policy decision")
        if m.get("subsequent_local_action_executed") is not False:
            fails.append(f"{p}: newly returned local action was executed")
        if m.get("automatic_handoff_loop") is not False or m.get("automatic_local_loop") is not False:
            fails.append(f"{p}: automatic loop introduced")
        if m.get("watchdog_changed") is not False or m.get("quality_gate_used") is not False or m.get("new_threshold_added") is not False:
            fails.append(f"{p}: threshold/watchdog/quality contract changed")
        if m.get("productivity_threshold_used") is not False:
            fails.append(f"{p}: productivity outcome was turned into a gate")
        if m.get("preexisting_objects_read_only") is not True or m.get("selected_object_map_pure") is not True:
            fails.append(f"{p}: scene-object integrity broken")
        if m.get("measurement_status") is None or m.get("subsequent_policy_status") is None:
            fails.append(f"{p}: descriptive outcomes missing")
        rows.append({
            "selected_object_id": m.get("selected_object_id"),
            "executed_gaze_deg": m.get("executed_action_gaze_deg"),
            "global_step": m.get("global_step"),
            "empty_look": m.get("empty_look"),
            "valid_target_points": m.get("selected_object_valid_depth_points"),
            "matched_surfels": m.get("matched_surfels"),
            "new_surfels": m.get("new_surfels"),
            "novelty_fraction": m.get("novelty_fraction"),
            "footprint_cell_delta": m.get("raw_footprint_cell_delta"),
            "measurement_status": m.get("measurement_status"),
            "subsequent_policy_status": m.get("subsequent_policy_status"),
            "subsequent_next_gaze_deg": m.get("subsequent_local_policy_decision", {}).get("next_gaze_deg"),
        })
    status = "MULTIOBJECT3H_COMPLETE" if not fails else "MULTIOBJECT3H_INTEGRITY_FAIL"
    print("[multiobject3h-compare] " + status + " " + json.dumps({"records": rows, "structural_fails": fails}, sort_keys=True))
    raise SystemExit(0 if not fails else 2)


if __name__ == "__main__":
    main()
