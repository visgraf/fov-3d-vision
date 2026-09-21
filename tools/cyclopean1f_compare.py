"""Aggregate structural report for completed Cyclopean-1f records."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default="previews/cyclopean1f")
    a = ap.parse_args()
    rows = []
    fails = []
    for p in sorted(Path(a.root).rglob("prediction_manifest.json")):
        m = json.loads(p.read_text())
        if m.get("schema") != "Cyclopean1f-epistemic-loop-v1":
            continue
        if m.get("truth_opened") is not False or int(m.get("parent_fixations_rerendered", -1)) != 0:
            fails.append(str(p))
        rows.append({
            "seed": int(m["seed"]),
            "scientific_stop_reached": bool(m.get("scientific_stop_reached")),
            "stop_reason": m.get("stop_reason"),
            "added_fixations": int(m.get("added_fixations", 0)),
            "watchdog_total_fixations": int(m.get("watchdog_total_fixations", 0)),
            "never_observed_cells_before": m.get("epistemic_before", {}).get("exterior_never_observed_cells"),
            "never_observed_cells_after": m.get("epistemic_after", {}).get("exterior_never_observed_cells"),
            "max_never_observed_depth_before": m.get("epistemic_before", {}).get("max_exterior_never_observed_depth_cells"),
            "max_never_observed_depth_after": m.get("epistemic_after", {}).get("max_exterior_never_observed_depth_cells"),
            "map_point_gain": int(m.get("map_points_after", 0)) - int(m.get("map_points_before", 0)),
        })
    if not rows:
        raise SystemExit("no Cyclopean-1f records found")
    print("[cyclopean1f-compare] CYCLOPEAN1F_COMPLETE " + json.dumps({"records": rows, "structural_fails": fails}, sort_keys=True))
    if fails:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
