"""Report completed Cyclopean-1c bay probes without a quality gate."""
from __future__ import annotations
import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("records", nargs="+")
    args = ap.parse_args()
    rows = []
    structural = []
    for p in map(Path, args.records):
        m = json.loads((p / "prediction_manifest.json").read_text())
        if (m.get("schema") != "Cyclopean1c-bay-probe-v1" or
                m.get("truth_opened") is not False or
                int(m.get("added_fixations", -1)) != 1 or
                int(m.get("parent_fixations_rerendered", -1)) != 0 or
                int(m.get("seed", -1)) != 2111):
            structural.append(f"{p}: integrity")
            continue
        r = m["probe_result"]
        rows.append({
            "seed": m["seed"],
            "probe_gaze_deg": r["probe_gaze_deg"],
            "probe_target_points": r["probe_target_points"],
            "map_point_gain": int(m["map_points_after"] - m["map_points_before"]),
            "max_exterior_depth_before": m["boundary_before"]["max_exterior_border_distance_cells"],
            "max_exterior_depth_after": m["boundary_after"]["max_exterior_border_distance_cells"],
            "internal_components_before": m["boundary_before"]["internal_components"],
            "internal_components_after": m["boundary_after"]["internal_components"],
        })
    status = "CYCLOPEAN1C_COMPLETE" if not structural else "CYCLOPEAN1C_INTEGRITY_FAIL"
    print("[cyclopean1c-compare]", status,
          json.dumps({"records": rows, "structural_fails": structural}, sort_keys=True))
    raise SystemExit(0 if not structural else 2)


if __name__ == "__main__":
    main()
