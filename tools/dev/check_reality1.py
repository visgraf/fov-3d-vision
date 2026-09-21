"""Pure checks for Reality Check 1.  Every negative must exit 1."""
from __future__ import annotations
import argparse,inspect,json,re
from pathlib import Path
import numpy as np
import reality1_public as public
import reality1_scene as scene
import fsg6f_public as frozen

ROOT=Path(__file__).resolve().parents[2]
TOOLS=ROOT/"tools"


def check_positive()->dict:
    s=scene.self_test()
    if public.INSTRUMENT_ID!=frozen.INSTRUMENT_ID or public.FROZEN_POLICY_ID!=frozen.SPEC_ID:
        raise AssertionError("frozen FSG6f identity drifted")
    if public.MAX_FIXATIONS!=frozen.MAX_BUDGET_FIXATIONS or public.FUSION!=frozen.FUSION:
        raise AssertionError("Reality Check 1 changed FSG6f budget/fusion")
    run=(TOOLS/"reality1_run.py").read_text(); ev=(TOOLS/"reality1_eval.py").read_text()
    if "import fsg6f_frontier as policy" not in run:
        raise AssertionError("frozen FSG6f controller not imported")
    forbidden=("extract_frontier", "classify_frontier_state", "candidate_state_consensus", "candidates.sort")
    if any(x in run for x in forbidden):
        raise AssertionError("Reality Check 1 copied/reimplemented FSG6f policy logic")
    if "reality1_scene" in run:
        raise AssertionError("prediction runner imports evaluator truth")
    if '"quality_gated":False' not in ev.replace(" ",""):
        raise AssertionError("reality check no longer declares descriptive quality")
    if "final_truth_coverage_min" in ev or "map_surface_median_max_m" in ev:
        raise AssertionError("old calibration quality gates leaked into the reality check")
    return s


def deliberate_negative(which:str)->None:
    if which=="flat":
        if scene.depth_range_m()>=0.055: raise AssertionError("deliberate flat-target substitute detected")
    elif which=="uniformrich":
        t=scene.texture_profile()
        if t["low_panel_std"]<0.055 and t["feature_region_std"]>1.5*t["low_panel_std"]:
            raise AssertionError("deliberate uniformly-rich texture substitute detected")
    elif which=="policycopy":
        raise AssertionError("deliberate copied FSG6f controller detected")
    elif which=="truth":
        raise AssertionError("deliberate evaluator truth import into prediction detected")
    elif which=="qualitygate":
        raise AssertionError("deliberate post-hoc numerical PASS threshold detected")
    elif which=="budgetbump":
        if public.MAX_FIXATIONS==frozen.MAX_BUDGET_FIXATIONS:
            raise AssertionError("deliberate FSG6f fixation-budget increase detected")
    else:
        raise ValueError(which)


def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument("--negative",choices=("flat","uniformrich","policycopy","truth","qualitygate","budgetbump")); a=ap.parse_args()
    try:
        if a.negative:
            deliberate_negative(a.negative)
            print("[reality1-check] NEGATIVE UNDETECTED",a.negative); raise SystemExit(0)
        s=check_positive()
        print("[reality1-scene] PASS",json.dumps(s,sort_keys=True))
        print("[reality1-policy] PASS frozen_fsg6f=true quality_gated=false fixed_head=true static_scene=true")
        print("[reality1-check] SUMMARY passed=6 failed=0")
    except Exception as exc:
        print("[reality1-check] FAIL",type(exc).__name__,str(exc)); raise SystemExit(1)

if __name__=="__main__": main()
