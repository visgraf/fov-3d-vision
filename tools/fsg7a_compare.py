"""Aggregate the four prospective FSG7a full trials."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import fsg7a_public as public
from fsg_geometry import json_write

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--root",type=Path,required=True); ap.add_argument("--out",type=Path,required=True); a=ap.parse_args()
    if a.out.exists(): raise FileExistsError("output must be new")
    rows=[]; fails=[]
    for f in public.FIXTURES:
        for s in public.SEEDS:
            p=a.root/f"full-{f}-seed{s}-eval"/"metrics.json"
            if not p.exists(): raise FileNotFoundError(p)
            m=json.loads(p.read_text()); rows.append({"fixture":f,"seed":s,"status":m["status"],"final_truth_coverage":m["final_truth_coverage"],"return_coverage_final":m["return_coverage_final"],"map_surface_median_m":m["map_surface_median_m"],"map_surface_p95_m":m["map_surface_p95_m"]})
            if m.get("fails"): fails.append(f"{f}/{s} moving-head run failed")
    out={"schema":"FSG7a-comparison-v1","trial_passes":4-len(fails),"trials":rows,"mean_final_coverage":sum(r["final_truth_coverage"] for r in rows)/4,"mean_return_coverage":sum(r["return_coverage_final"] for r in rows)/4,"fails":fails,"status":"FSG7A_HEAD_MOTION_FEASIBILITY_PASS" if not fails else "FSG7A_HEAD_MOTION_FEASIBILITY_FAIL"}
    a.out.mkdir(parents=True); json_write(a.out/"comparison.json",out); print("[fsg7a-compare] "+out["status"],json.dumps(out,sort_keys=True)); raise SystemExit(0 if not fails else 2)
if __name__=="__main__": main()
