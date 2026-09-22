"""Structural comparator for completed MultiObject-1c read-only audits."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import multiobject1c_public as public


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
        if not m.get("object_1_read_only") or not m.get("object_2_read_only") or not m.get("object_2_map_pure"):
            fails.append(f"{p}: object integrity broken")
        s = m.get("summary", {})
        if s.get("scene_disposition") != "MOVE_TO_NEXT_OBJECT":
            fails.append(f"{p}: scene progress unexpectedly gated")
        rows.append({
            "seed": m.get("seed"),
            "observation_count": m.get("observation_count"),
            "shoreline_cells": s.get("shoreline_cells"),
            "max_exterior_border_distance_cells": s.get("max_exterior_border_distance_cells"),
            "refined": s.get("refined_unobserved_cells_by_state"),
            "exterior_refined": s.get("exterior_refined_cells_by_state"),
            "object_143_status": s.get("object_143_status"),
            "scene_disposition": s.get("scene_disposition"),
        })
    status = "MULTIOBJECT1C_COMPLETE" if not fails else "MULTIOBJECT1C_INTEGRITY_FAIL"
    print("[multiobject1c-compare]", status, json.dumps({"records": rows, "structural_fails": fails}, sort_keys=True))
    raise SystemExit(0 if not fails else 2)


if __name__ == "__main__":
    main()
