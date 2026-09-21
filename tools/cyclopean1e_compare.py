"""Aggregate structural report for completed Cyclopean-1e records."""
from __future__ import annotations
import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default="previews/cyclopean1e")
    a = ap.parse_args()
    root = Path(a.root)
    rows = []
    fails = []
    for p in sorted(root.rglob("prediction_manifest.json")):
        m = json.loads(p.read_text())
        if m.get("schema") != "Cyclopean1e-epistemic-gaze-v1":
            continue
        if m.get("truth_opened") is not False or int(m.get("added_fixations", -1)) > 1:
            fails.append(str(p))
        before = m.get("epistemic_before", {})
        after = m.get("epistemic_after", {})
        pr = m.get("probe_result", {})
        rows.append({
            "seed": int(m["seed"]),
            "probe_taken": bool(pr.get("probe_taken")),
            "probe_gaze_deg": pr.get("probe_gaze_deg"),
            "probe_target_points": pr.get("probe_target_points"),
            "map_point_gain": int(m.get("map_points_after", 0)) - int(m.get("map_points_before", 0)),
            "never_observed_cells_before": before.get("exterior_never_observed_cells"),
            "never_observed_cells_after": after.get("exterior_never_observed_cells"),
            "max_never_observed_depth_before": before.get("max_exterior_never_observed_depth_cells"),
            "max_never_observed_depth_after": after.get("max_exterior_never_observed_depth_cells"),
        })
    if not rows:
        raise SystemExit("no Cyclopean-1e records found")
    print("[cyclopean1e-compare] CYCLOPEAN1E_COMPLETE " + json.dumps({"records": rows, "structural_fails": fails}, sort_keys=True))
    if fails:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
