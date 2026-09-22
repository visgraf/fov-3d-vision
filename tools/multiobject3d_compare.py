"""Structural comparator for completed MultiObject-3d read-only stop audits."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import multiobject3d_public as public


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
        if m.get("truth_opened") is not False or int(m.get("acquisitions_added", -1)) != 0:
            fails.append(f"{p}: audit acquired data or opened truth")
        if int(m.get("growth_iterations_added", -1)) != 0 or m.get("watchdog_changed") is not False:
            fails.append(f"{p}: growth/watchdog changed")
        if m.get("parent_files_modified") is not False:
            fails.append(f"{p}: parent modified")
        if not m.get("scene_objects_read_only") or not m.get("selected_object_read_only") or not m.get("selected_object_map_pure"):
            fails.append(f"{p}: object integrity broken")
        if m.get("parent_termination_reason") != "no_frontier" or m.get("parent_scientific_stop_reached") is not True:
            fails.append(f"{p}: wrong parent stop")
        if m.get("final_policy_stop_replayed_exactly") is not True:
            fails.append(f"{p}: final frozen policy stop was not exactly replayed")
        s = m.get("summary", {})
        if s.get("scene_disposition") != "MOVE_TO_NEXT_OBJECT":
            fails.append(f"{p}: scene progress was blocked")
        rows.append({
            "selected_object_id": m.get("selected_object_id"),
            "shoreline_cells": s.get("shoreline_cells"),
            "refined": s.get("refined_unobserved_cells_by_state"),
            "exterior_refined": s.get("exterior_refined_cells_by_state"),
            "object_status": s.get("object_status"),
            "stop_interpretation": s.get("stop_interpretation"),
            "final_open_frontier_to_cyclopean_cell_counts": s.get("final_open_frontier_to_cyclopean_cell_counts"),
            "final_open_targets_inside_visited_gaze_envelope": s.get("final_open_targets_inside_visited_gaze_envelope"),
            "final_open_targets_outside_visited_gaze_envelope": s.get("final_open_targets_outside_visited_gaze_envelope"),
            "scene_disposition": s.get("scene_disposition"),
        })
    status = "MULTIOBJECT3D_COMPLETE" if not fails else "MULTIOBJECT3D_INTEGRITY_FAIL"
    print("[multiobject3d-compare]", status, json.dumps({"records": rows, "structural_fails": fails}, sort_keys=True))
    raise SystemExit(0 if not fails else 2)


if __name__ == "__main__":
    main()
