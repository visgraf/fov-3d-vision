"""Structural comparator for MultiObject-1b."""
from __future__ import annotations
import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("records", nargs="+"); a = ap.parse_args()
    out = []; fails = []
    for r in map(Path, a.records):
        m = json.loads((r / "prediction_manifest.json").read_text())
        if m.get("schema") != "MultiObject1b-object143-growth-v1":
            fails.append(f"{r}: wrong schema"); continue
        if m.get("object_ids") != [141, 143]: fails.append(f"{r}: object ids changed")
        if not m.get("object_1_read_only"): fails.append(f"{r}: object 141 not read-only")
        if m.get("object_1_sha256_before") != m.get("object_1_sha256_after"):
            fails.append(f"{r}: object 141 changed")
        if not m.get("object_2_map_pure"): fails.append(f"{r}: object 143 purity broken")
        if m.get("policy_adapter") != "id143_to_frozen_fsg6f_target_label":
            fails.append(f"{r}: frozen-policy adapter missing")
        if m.get("policy_source_modified") is not False: fails.append(f"{r}: FSG6f policy modified")
        if m.get("truth_opened") is not False: fails.append(f"{r}: truth opened")
        if m.get("automatic_object_discovery") is not False: fails.append(f"{r}: discovery introduced")
        out.append({
            "object_1_map_points": m.get("object_1_map_points"),
            "object_2_seed_points": m.get("object_2_seed_points"),
            "object_2_map_points": m.get("object_2_map_points"),
            "object_2_fixations_total": m.get("object_2_fixations_total"),
            "added_fixations": m.get("added_fixations"),
            "empty_steps": m.get("empty_steps"),
            "termination_reason": m.get("termination_reason"),
            "scientific_stop_reached": m.get("scientific_stop_reached"),
            "footprint_overlap_cells": m.get("scene_footprint_overlap_cells"),
        })
    print("[multiobject1b-compare] MULTIOBJECT1B_COMPLETE " + json.dumps({"records": out, "structural_fails": fails}, sort_keys=True))
    raise SystemExit(1 if fails else 0)


if __name__ == "__main__": main()
