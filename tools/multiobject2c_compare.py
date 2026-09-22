"""Structural comparator for MultiObject-2c selected-object growth records."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("records", nargs="+")
    a = ap.parse_args()
    out = []
    fails = []
    for r in map(Path, a.records):
        m = json.loads((r / "prediction_manifest.json").read_text())
        if m.get("schema") != "MultiObject2c-grow-selected-object-v1":
            fails.append(f"{r}: wrong schema")
            continue
        target_id = int(m.get("selected_object_id", -1))
        if target_id <= 0 or target_id in {141, 143}:
            fails.append(f"{r}: invalid selected object id")
        if not m.get("preexisting_objects_read_only"):
            fails.append(f"{r}: pre-existing objects not read-only")
        before = m.get("preexisting_object_hashes_before", {})
        after = m.get("preexisting_object_hashes_after", {})
        if before != after:
            fails.append(f"{r}: pre-existing object hash changed")
        if not m.get("selected_object_map_pure"):
            fails.append(f"{r}: selected-object purity broken")
        if m.get("policy_adapter") != "parent_selected_id_to_frozen_fsg6f_target_label":
            fails.append(f"{r}: frozen-policy adapter missing")
        if m.get("policy_source_modified") is not False:
            fails.append(f"{r}: FSG6f policy modified")
        if m.get("parent_fixations_rerendered") != 0:
            fails.append(f"{r}: history rerendered")
        if m.get("renderer_entrypoint") != "tools/scene_render_fix.py":
            fails.append(f"{r}: generic scene renderer missing")
        if m.get("truth_opened") is not False:
            fails.append(f"{r}: truth opened")
        if m.get("automatic_scene_scheduler") is not False:
            fails.append(f"{r}: scheduler introduced")
        if m.get("quality_gate_used") is not False:
            fails.append(f"{r}: quality gate introduced")
        if m.get("texture_diagnostics_are_gates") is not False:
            fails.append(f"{r}: texture diagnostics became a gate")
        out.append({
            "selected_object_id": target_id,
            "seed_points": m.get("selected_object_seed_points"),
            "map_points": m.get("selected_object_map_points"),
            "fixations_total": m.get("selected_object_fixations_total"),
            "termination_reason": m.get("termination_reason"),
            "scientific_stop_reached": m.get("scientific_stop_reached"),
            "recovery_fraction_median": m.get("target_depth_recovery_fraction_median"),
        })
    print("[multiobject2c-compare] MULTIOBJECT2C_COMPLETE " + json.dumps({
        "records": out,
        "structural_fails": fails,
    }, sort_keys=True))
    raise SystemExit(1 if fails else 0)


if __name__ == "__main__":
    main()
