"""Structural comparator for completed FullScene-1c selected-object growth records."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import fullscene1c_public as public


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
        target_id = int(m.get("selected_object_id", -1))
        existing_ids = tuple(int(x) for x in m.get("preexisting_object_ids", []))
        if target_id <= 0 or not existing_ids or target_id in set(existing_ids):
            fails.append(f"{p}: invalid selected/pre-existing object ids")
        if m.get("object_ids") != list(existing_ids + (target_id,)):
            fails.append(f"{p}: object set/order changed")
        if m.get("preexisting_objects_read_only") is not True:
            fails.append(f"{p}: pre-existing objects not read-only")
        if m.get("preexisting_object_hashes_before") != m.get("preexisting_object_hashes_after"):
            fails.append(f"{p}: pre-existing object hash changed")
        if m.get("deferred_prior_object_action_executed") is not False:
            fails.append(f"{p}: prior deferred local action executed")
        if m.get("selected_object_map_pure") is not True:
            fails.append(f"{p}: selected-object purity broken")
        if int(m.get("selected_object_seed_points", -1)) <= 0:
            fails.append(f"{p}: invalid seed point count")
        total = int(m.get("selected_object_fixations_total", -1))
        added = int(m.get("added_fixations", -2))
        if total < 1 or added != total - 1 or int(m.get("parent_fixations_rerendered", -1)) != 0:
            fails.append(f"{p}: fixation chronology/rerender invariant broken")
        if m.get("growth_history_starts_at_fullscene1b_seed") is not True:
            fails.append(f"{p}: growth history did not start at FullScene-1b seed")
        if m.get("older_scene_history_replayed_into_local_policy") is not False:
            fails.append(f"{p}: older scene history leaked into local growth policy")
        if m.get("policy_adapter") != "reuse_multiobject2c_policy_target_label_adapter":
            fails.append(f"{p}: reused frozen-policy adapter missing")
        if m.get("policy_adapter_source") != public.POLICY_ADAPTER or m.get("policy_source_modified") is not False:
            fails.append(f"{p}: wrong/modified policy adapter")
        if m.get("renderer_entrypoint") != public.SCENE_RENDERER:
            fails.append(f"{p}: generic scene renderer missing")
        termination = m.get("termination_reason")
        scientific = m.get("scientific_stop_reached")
        if termination == "selected_object_watchdog" and scientific is not False:
            fails.append(f"{p}: watchdog mislabeled as scientific stop")
        if int(m.get("epistemic_handoffs_added", -1)) != 0:
            fails.append(f"{p}: epistemic handoff introduced")
        if m.get("truth_opened") is not False:
            fails.append(f"{p}: truth opened")
        if m.get("automatic_scene_scheduler") is not False or m.get("revisit_scheduler_used") is not False:
            fails.append(f"{p}: scheduler introduced")
        if m.get("automatic_object_discovery") is not False or m.get("semantic_ranking_used") is not False:
            fails.append(f"{p}: discovery/semantic ranking introduced")
        if m.get("quality_gate_used") is not False or m.get("new_threshold_added") is not False:
            fails.append(f"{p}: quality/threshold gate introduced")
        if m.get("texture_diagnostics_are_gates") is not False or m.get("productivity_score_synthesized") is not False:
            fails.append(f"{p}: diagnostics became a gate/score")
        rows.append({
            "selected_object_id": target_id,
            "seed_points": m.get("selected_object_seed_points"),
            "map_points": m.get("selected_object_map_points"),
            "fixations_total": total,
            "added_fixations": added,
            "empty_steps": m.get("empty_steps"),
            "termination_reason": termination,
            "scientific_stop_reached": scientific,
            "fusion_matched_total_after_seed": m.get("fusion_matched_total_after_seed"),
            "fusion_new_total_after_seed": m.get("fusion_new_total_after_seed"),
            "recovery_fraction_median": m.get("target_depth_recovery_fraction_median"),
        })
    status = "FULLSCENE1C_COMPLETE" if not fails else "FULLSCENE1C_INTEGRITY_FAIL"
    print("[fullscene1c-compare] " + status + " " + json.dumps({
        "records": rows,
        "structural_fails": fails,
    }, sort_keys=True))
    raise SystemExit(0 if not fails else 2)


if __name__ == "__main__":
    main()
