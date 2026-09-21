"""Aggregate structural report for completed Cyclopean-1g records."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default="previews/cyclopean1g")
    a = ap.parse_args()
    rows = []
    fails = []
    for p in sorted(Path(a.root).rglob("prediction_manifest.json")):
        m = json.loads(p.read_text())
        if m.get("schema") != "Cyclopean1g-recentered-measurement-v1":
            continue
        pr = m.get("probe_result", {})
        if (
            m.get("truth_opened") is not False
            or int(m.get("parent_fixations_rerendered", -1)) != 0
            or int(m.get("added_fixations", -1)) != 1
            or m.get("branch_disposition") != "STOP_AFTER_ONE_LOOK_REGARDLESS_OF_OUTCOME_THEN_MOVE_TO_MULTI_OBJECT"
        ):
            fails.append(str(p))
        rows.append({
            "seed": int(m["seed"]),
            "probe_gaze_deg": pr.get("probe_gaze_deg"),
            "measurement_outcome": pr.get("measurement_outcome"),
            "selected_residue_cells": pr.get("selected_residue_cells"),
            "recovered_valid_target_cells": pr.get("selected_residue_recovery", {}).get("recovered_valid_target_cells"),
            "probe_target_points": pr.get("probe_target_points"),
            "map_point_gain": int(m.get("map_points_after", 0)) - int(m.get("map_points_before", 0)),
            "observed_target_no_depth_before": m.get("observed_target_no_depth_before"),
            "observed_target_no_depth_after": m.get("observed_target_no_depth_after"),
            "branch_disposition": m.get("branch_disposition"),
        })
    if not rows:
        raise SystemExit("no Cyclopean-1g records found")
    print("[cyclopean1g-compare] CYCLOPEAN1G_COMPLETE " + json.dumps({"records": rows, "structural_fails": fails}, sort_keys=True))
    if fails:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
