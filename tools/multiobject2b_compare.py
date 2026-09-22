"""Structural comparator for MultiObject-2b selected-object seed records."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import multiobject2b_public as public


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
        selected = int(m.get("selected_object_id", -1))
        if selected <= 0 or selected in set(public.EXISTING_OBJECT_IDS):
            fails.append(f"{p}: invalid selected object id")
        if m.get("existing_object_ids_before") != list(public.EXISTING_OBJECT_IDS):
            fails.append(f"{p}: existing object set changed")
        if m.get("object_ids_after") != [*public.EXISTING_OBJECT_IDS, selected]:
            fails.append(f"{p}: third entity not appended cleanly")
        if int(m.get("added_fixations", -1)) != 1 or int(m.get("parent_fixations_rerendered", -1)) != 0:
            fails.append(f"{p}: seed did not add exactly one fresh fixation")
        if int(m.get("growth_iterations_added", -1)) != 0 or int(m.get("fusion_iterations_added", -1)) != 0:
            fails.append(f"{p}: seed step grew/fused an object")
        if m.get("truth_opened") is not False or not m.get("existing_objects_read_only"):
            fails.append(f"{p}: truth or existing-object integrity broken")
        if not m.get("selection_consumed_from_parent") or not m.get("selected_object_patch_pure"):
            fails.append(f"{p}: parent selection or seed-patch purity broken")
        steps = [int(x) for x in m.get("evidence_observation_steps", [])]
        if not steps or int(m.get("global_step", -1)) != max(steps) + 1:
            fails.append(f"{p}: global acquisition chronology broken")
        if m.get("renderer_entrypoint") != public.SCENE_RENDERER:
            fails.append(f"{p}: generic scene renderer not used")
        rows.append({
            "seed": m.get("seed"),
            "selected_object_id": selected,
            "selected_valid_depth_samples": m.get("selected_valid_depth_samples"),
            "global_step": m.get("global_step"),
            "probe_gaze_deg": m.get("probe_gaze_deg"),
            "selected_object_seed_points": m.get("selected_object_seed_points"),
            "object_ids_after": m.get("object_ids_after"),
            "scene_footprint_counts": m.get("scene_footprint_counts"),
        })
    status = "MULTIOBJECT2B_COMPLETE" if not fails else "MULTIOBJECT2B_INTEGRITY_FAIL"
    print("[multiobject2b-compare]", status, json.dumps({"records": rows, "structural_fails": fails}, sort_keys=True))
    raise SystemExit(0 if not fails else 2)


if __name__ == "__main__":
    main()
