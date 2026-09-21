"""Structural comparator for MultiObject-1a."""
from __future__ import annotations
import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("records", nargs="+")
    a = ap.parse_args()
    out = []
    fails = []
    for r in map(Path, a.records):
        m = json.loads((r / "prediction_manifest.json").read_text())
        if m.get("schema") != "MultiObject1a-second-object-seed-v1":
            fails.append(f"{r}: wrong schema"); continue
        if m.get("object_ids") != [141, 143]: fails.append(f"{r}: object ids changed")
        if not m.get("object_1_parent_pure") or not m.get("object_2_patch_pure"):
            fails.append(f"{r}: object purity broken")
        if int(m.get("added_fixations", -1)) > 1: fails.append(f"{r}: >1 fixation")
        out.append({
            "object_ids": m.get("object_ids"),
            "object_1_map_points": m.get("object_1_map_points"),
            "object_2_seed_target_points": m.get("object_2_seed_target_points"),
            "probe_gaze_deg": m.get("probe_gaze_deg"),
            "footprint_overlap_cells": m.get("scene_footprint_overlap_cells"),
        })
    print("[multiobject1a-compare] MULTIOBJECT1A_COMPLETE " + json.dumps({"records": out, "structural_fails": fails}, sort_keys=True))
    raise SystemExit(1 if fails else 0)

if __name__ == "__main__": main()
