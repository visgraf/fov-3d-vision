"""Structural comparator for completed FullScene-1d read-only epistemic audits."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import fullscene1d_public as public


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("records", nargs="+")
    a = ap.parse_args()
    rows, fails = [], []
    for p in map(Path, a.records):
        m = json.loads((p / "prediction_manifest.json").read_text())
        if m.get("schema") != public.SPEC_ID:
            fails.append(f"{p}: wrong schema")
            continue
        if m.get("public_spec_sha256") != public.public_digest():
            fails.append(f"{p}: public digest mismatch")
        if m.get("truth_opened") is not False or int(m.get("acquisitions_added", -1)) != 0:
            fails.append(f"{p}: audit acquired data or opened truth")
        if int(m.get("growth_iterations_added", -1)) != 0 or int(m.get("fusion_iterations_added", -1)) != 0:
            fails.append(f"{p}: audit grew/fused geometry")
        if int(m.get("epistemic_handoffs_added", -1)) != 0:
            fails.append(f"{p}: audit executed a handoff")
        if m.get("watchdog_changed") is not False or m.get("parent_files_modified") is not False:
            fails.append(f"{p}: parent/watchdog modified")
        if not m.get("scene_objects_read_only") or not m.get("selected_object_read_only") or not m.get("selected_object_map_pure"):
            fails.append(f"{p}: object integrity broken")
        if m.get("scene_object_sha256_before") != m.get("scene_object_sha256_after"):
            fails.append(f"{p}: scene object geometry hash changed")
        if m.get("deferred_prior_object_action_executed") is not False:
            fails.append(f"{p}: prior deferred action executed")
        if m.get("parent_termination_reason") != "no_frontier" or m.get("parent_scientific_stop_reached") is not True:
            fails.append(f"{p}: wrong parent stop")
        if int(m.get("parent_frontier_open_count", -1)) != 0:
            fails.append(f"{p}: parent is not the zero-OPEN stop")
        if m.get("final_policy_stop_replayed_exactly") is not True or int(m.get("replayed_frontier_open_count", -1)) != 0:
            fails.append(f"{p}: zero-OPEN final policy stop was not exactly replayed")
        if m.get("older_s0_scene_history_added_to_audit") is not False:
            fails.append(f"{p}: audit history scope broadened")
        if m.get("reused_multiobject3d_audit_helpers") is not True:
            fails.append(f"{p}: established audit machinery not reused")
        if m.get("automatic_scene_scheduler") is not False or m.get("revisit_scheduler_used") is not False:
            fails.append(f"{p}: scheduler introduced")
        if m.get("automatic_object_discovery") is not False:
            fails.append(f"{p}: discovery introduced")
        if m.get("quality_gate_used") is not False or m.get("new_threshold_added") is not False:
            fails.append(f"{p}: quality/threshold gate introduced")
        s = m.get("summary", {})
        if s.get("scene_disposition") != "RETURN_TO_SCENE_INVENTORY":
            fails.append(f"{p}: wrong scene disposition")
        rows.append({
            "selected_object_id": m.get("selected_object_id"),
            "observation_steps": m.get("observation_steps"),
            "shoreline_cells": s.get("shoreline_cells"),
            "base_shoreline": s.get("base_shoreline_cells_by_state"),
            "refined": s.get("refined_unobserved_cells_by_state"),
            "exterior_refined": s.get("exterior_refined_cells_by_state"),
            "object_status": s.get("object_status"),
            "stop_interpretation": s.get("stop_interpretation"),
            "local_stop_subtype": s.get("local_stop_subtype"),
            "frontier_relation": s.get("frontier_state_to_cyclopean_cell_counts"),
            "scene_disposition": s.get("scene_disposition"),
        })
    status = "FULLSCENE1D_COMPLETE" if not fails else "FULLSCENE1D_INTEGRITY_FAIL"
    print("[fullscene1d-compare] " + status + " " + json.dumps({"records": rows, "structural_fails": fails}, sort_keys=True))
    raise SystemExit(0 if not fails else 2)


if __name__ == "__main__":
    main()
