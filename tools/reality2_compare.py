"""Descriptive comparison of the two Reality Check 2 continuations."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import reality2_public as public
from fsg_geometry import json_write


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--root",type=Path,required=True); ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args(); rows=[]; fails=[]
    for seed in public.SEEDS:
        p=a.root/f"full-seed{seed}-eval"/"metrics.json"
        if not p.exists(): fails.append(f"missing seed {seed} metrics"); continue
        m=json.loads(p.read_text()); rows.append(m)
        if m.get("integrity_fails"): fails.append(f"seed {seed} integrity failure")
    if len(rows)==2:
        c6=[m["visible_truth_coverage_at_reality1_stop"] for m in rows]
        cf=[m["visible_truth_coverage_final"] for m in rows]
        desc={"fixation_counts":[m["fixation_count"] for m in rows],
              "new_fixation_counts":[m["new_fixation_count"] for m in rows],
              "termination_reasons":[m["termination_reason"] for m in rows],
              "both_no_frontier":all(m["terminated_by_no_frontier"] for m in rows),
              "watchdog_reached":[m["watchdog_reached"] for m in rows],
              "coverage_at_6":[float(x) for x in c6],"final_coverage":[float(x) for x in cf],
              "coverage_gain_after_6":[float(m["visible_truth_coverage_gain_after_reality1_stop"]) for m in rows],
              "coverage_abs_seed_difference_at_6":abs(c6[0]-c6[1]),
              "coverage_abs_seed_difference_final":abs(cf[0]-cf[1]),
              "surface_median_range_m":[min(m["approx_surface_median_m"] for m in rows),max(m["approx_surface_median_m"] for m in rows)],
              "surface_p95_range_m":[min(m["approx_surface_p95_m"] for m in rows),max(m["approx_surface_p95_m"] for m in rows)],
              "same_full_trajectory":rows[0]["fixation_gazes_deg"]==rows[1]["fixation_gazes_deg"]}
    else: desc={}
    out={"schema":"RealityCheck2-comparison-v1","status":"REALITY2_COMPLETE" if not fails else "REALITY2_INTEGRITY_FAIL",
         "fails":fails,"descriptive":desc,"quality_gated":False,
         "decision":"Luiz/Chat judge whether additional looking produced useful completion and whether seed divergence became mainly an efficiency issue."}
    a.out.mkdir(parents=True,exist_ok=False); json_write(a.out/"comparison.json",out)
    print("[reality2-compare] "+out["status"],json.dumps(desc,sort_keys=True),flush=True)
    raise SystemExit(0 if not fails else 2)

if __name__=="__main__": main()
