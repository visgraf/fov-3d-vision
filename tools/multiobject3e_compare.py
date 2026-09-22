"""Structural comparator for completed MultiObject-3e bounded handoff records."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import multiobject3e_public as public


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
        if m.get("parent_stop_interpretation") != public.PUBLIC_SPEC["required_parent_interpretation"]:
            fails.append(f"{p}: wrong parent stop interpretation")
        if int(m.get("added_fixations", -1)) != public.MAX_HANDOFF_FIXATIONS:
            fails.append(f"{p}: bounded one-fixation contract broken")
        if int(m.get("returned_local_policy_decisions", -1)) != public.RETURN_POLICY_DECISIONS:
            fails.append(f"{p}: return-decision count broken")
        if m.get("returned_local_action_executed") is not False or m.get("automatic_handoff_loop") is not False:
            fails.append(f"{p}: experiment executed beyond one returned decision")
        if m.get("parent_fixations_rerendered") != 0:
            fails.append(f"{p}: parent history rerendered")
        if not m.get("preexisting_objects_read_only") or not m.get("selected_object_map_pure"):
            fails.append(f"{p}: object separation/purity broken")
        if m.get("epistemic_selector_reused_unchanged") is not True:
            fails.append(f"{p}: established epistemic selector not reused")
        if m.get("watchdog_changed") is not False or m.get("quality_gate_used") is not False:
            fails.append(f"{p}: policy/quality contract changed")
        rows.append({
            "selected_object_id": m.get("selected_object_id"),
            "handoff_gaze_deg": m.get("handoff_gaze_deg"),
            "handoff_gaze_inside_previous_envelope": m.get("handoff_gaze_inside_previous_envelope"),
            "empty_look": m.get("empty_look"),
            "map_points_before": m.get("selected_object_map_points_before"),
            "map_points_after": m.get("selected_object_map_points_after"),
            "exterior_never_observed_before": m.get("epistemic_before", {}).get("exterior_never_observed"),
            "exterior_never_observed_after": m.get("epistemic_after", {}).get("exterior_never_observed"),
            "return_status": m.get("return_status"),
            "returned_next_gaze_deg": m.get("returned_local_policy_decision", {}).get("next_gaze_deg"),
            "returned_candidates_before_consensus_count": m.get("returned_local_policy_decision", {}).get("candidates_before_consensus_count"),
        })
    status = "MULTIOBJECT3E_COMPLETE" if not fails else "MULTIOBJECT3E_INTEGRITY_FAIL"
    print("[multiobject3e-compare]", status, json.dumps({"records": rows, "structural_fails": fails}, sort_keys=True))
    raise SystemExit(0 if not fails else 2)


if __name__ == "__main__":
    main()
