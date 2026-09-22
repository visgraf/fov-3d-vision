"""Structural comparator for MultiObject-1b2."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import multiobject1b2_public as public


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("records", nargs="+")
    a = ap.parse_args()
    out = []
    fails = []
    for r in map(Path, a.records):
        m = json.loads((r / "prediction_manifest.json").read_text())
        if m.get("schema") != public.SPEC_ID:
            fails.append(f"{r}: wrong schema")
            continue
        if m.get("object_ids") != [141, 143]:
            fails.append(f"{r}: object ids changed")
        if not m.get("object_1_read_only") or m.get("object_1_sha256_before") != m.get("object_1_sha256_after"):
            fails.append(f"{r}: object 141 changed")
        if not m.get("object_2_map_pure"):
            fails.append(f"{r}: object 143 purity broken")
        if m.get("partial_fixations_rerendered") != 0:
            fails.append(f"{r}: partial history was rerendered")
        eq = m.get("renderer_equivalence", {})
        if (
            not eq.get("passed")
            or not eq.get("calibration_exact")
            or not eq.get("acquisition_contract_exact")
            or not eq.get("observation_keys_exact")
            or not eq.get("observation_shape_dtype_exact")
            or not eq.get("instance_arrays_exact")
            or not eq.get("rgb_is_diagnostic_not_gate")
            or eq.get("rgb_tolerance_used") is not False
        ):
            fails.append(f"{r}: generic renderer instrument equivalence not established")
        if m.get("global_history_renumbered") is not False:
            fails.append(f"{r}: global acquisition history renumbered")
        if m.get("policy_source_modified") is not False:
            fails.append(f"{r}: policy modified")
        if m.get("truth_opened") is not False:
            fails.append(f"{r}: truth opened")
        if m.get("automatic_object_discovery") is not False:
            fails.append(f"{r}: discovery introduced")
        out.append({
            "object_2_resume_points": m.get("object_2_resume_points"),
            "object_2_map_points": m.get("object_2_map_points"),
            "reused_global_steps": m.get("reused_global_steps"),
            "new_global_steps": m.get("new_global_steps"),
            "object_2_fixations_total": m.get("object_2_fixations_total"),
            "empty_steps": m.get("empty_steps"),
            "termination_reason": m.get("termination_reason"),
            "scientific_stop_reached": m.get("scientific_stop_reached"),
            "renderer_equivalence": eq.get("passed"),
            "footprint_overlap_cells": m.get("scene_footprint_overlap_cells"),
        })
    print("[multiobject1b2-compare] MULTIOBJECT1B2_COMPLETE " + json.dumps({"records": out, "structural_fails": fails}, sort_keys=True))
    raise SystemExit(1 if fails else 0)


if __name__ == "__main__":
    main()
