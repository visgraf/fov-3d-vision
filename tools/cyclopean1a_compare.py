"""Aggregate the two Cyclopean-1a hole-probe records."""
from __future__ import annotations
import argparse,json
from pathlib import Path


def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument("records",nargs="+"); args=ap.parse_args()
    rows=[]; structural=[]
    for p in map(Path,args.records):
        m=json.loads((p/"prediction_manifest.json").read_text())
        if m.get("schema")!="Cyclopean1a-probe-v1" or m.get("truth_opened") is not False or m.get("parent_fixations_rerendered")!=0:
            structural.append(f"{p}: integrity")
        cand=[h for h in m["holes_before"] if h["probe_candidate"]]
        after=[h for h in m["holes_after"] if h["probe_candidate"]]
        rows.append({"seed":m["seed"],"candidate_holes_before":len(cand),"largest_before_deg2":cand[0]["angular_area_deg2"] if cand else 0.0,"probe_taken":m["probe_result"]["probe_taken"],"probe_target_points":m["probe_result"].get("probe_target_points"),"candidate_holes_after":len(after),"largest_after_deg2":after[0]["angular_area_deg2"] if after else 0.0,"map_point_gain":m["map_points_after"]-m["map_points_before"]})
    status="CYCLOPEAN1A_COMPLETE" if not structural else "CYCLOPEAN1A_INTEGRITY_FAIL"
    print("[cyclopean1a-compare]",status,json.dumps({"records":rows,"structural_fails":structural},sort_keys=True))
    raise SystemExit(0 if not structural else 2)
if __name__=="__main__": main()
