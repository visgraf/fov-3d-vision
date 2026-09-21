"""Combine the two full Reality Check 1 observations without inventing a score."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
import reality1_public as public
from fsg_geometry import json_write


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--root",type=Path,required=True); ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args(); rows=[]
    for seed in public.SEEDS:
        p=a.root/f"full-seed{seed}-eval"/"metrics.json"
        m=json.loads(p.read_text()); rows.append(m)
    fails=[f"seed {m['seed']} integrity failed: {m['integrity_fails']}" for m in rows if m["integrity_fails"]]
    cov=[float(m["visible_truth_coverage_final"]) for m in rows]
    med=[float(m["approx_surface_median_m"]) for m in rows]
    p95=[float(m["approx_surface_p95_m"]) for m in rows]
    fix=[int(m["fixation_count"]) for m in rows]
    out={"schema":"RealityCheck1-comparison-v1","status":"REALITY1_COMPLETE" if not fails else "REALITY1_INTEGRITY_FAIL",
         "integrity_fails":fails,"seeds":list(public.SEEDS),"runs":rows,
         "descriptive":{
             "final_coverage_range":[min(cov),max(cov)],"final_coverage_abs_seed_difference":abs(cov[0]-cov[1]),
             "surface_median_range_m":[min(med),max(med)],"surface_p95_range_m":[min(p95),max(p95)],
             "fixation_counts":fix,"termination_reasons":[m["termination_reason"] for m in rows],
             "same_trajectory":rows[0]["fixation_gazes_deg"]==rows[1]["fixation_gazes_deg"]},
         "quality_gated":False,
         "decision":"Luiz/Chat decide whether this is good enough for the next practical step; do not tune this record."}
    a.out.mkdir(parents=True,exist_ok=False); json_write(a.out/"comparison.json",out)
    print("[reality1-compare] "+out["status"],json.dumps(out["descriptive"],sort_keys=True),flush=True)
    raise SystemExit(0 if not fails else 2)

if __name__=="__main__": main()
