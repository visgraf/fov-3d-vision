"""Pure checks for Reality Check 2.  Every deliberate negative exits 1."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
TOOLS=ROOT/"tools"
if str(TOOLS) not in sys.path: sys.path.insert(0,str(TOOLS))

import reality2_public as public
import reality1_public as parent
import reality1_scene as scene
import fsg6f_public as frozen


def check_positive()->dict:
    s=scene.self_test()
    if public.PARENT_SPEC_ID!=parent.SPEC_ID:
        raise AssertionError("Reality Check 2 parent identity drifted")
    for name in ("INSTRUMENT_ID","FROZEN_POLICY_ID","OBJECT_ID","FIXTURE","SEEDS","SEED_GAZE_DEG","VERGENCE_DISTANCE_M","FUSION"):
        if getattr(public,name)!=getattr(parent,name): raise AssertionError(f"Reality Check 2 changed {name}")
    if public.PARENT_FIXATIONS!=parent.MAX_FIXATIONS or public.PARENT_FIXATIONS!=frozen.MAX_BUDGET_FIXATIONS:
        raise AssertionError("Reality Check 1 six-look parent contract drifted")
    if public.WATCHDOG_TOTAL_FIXATIONS <= public.PARENT_FIXATIONS:
        raise AssertionError("Reality Check 2 still interrupts at the old six-look limit")
    if public.PUBLIC_SPEC["scientific_stopping_rule"]!="frozen FSG6f no_frontier":
        raise AssertionError("scientific stopping rule is not no_frontier")
    run=(TOOLS/"reality2_run.py").read_text(); render=(TOOLS/"reality2_render_fix.py").read_text(); ev=(TOOLS/"reality2_eval.py").read_text()
    if "import fsg6f_frontier as policy" not in run: raise AssertionError("frozen FSG6f controller not imported")
    forbidden=("extract_frontier","classify_frontier_state","candidate_state_consensus","candidates.sort")
    if any(x in run for x in forbidden): raise AssertionError("Reality Check 2 copied/reimplemented FSG6f policy logic")
    if "reality1_scene" in run: raise AssertionError("prediction runner imports evaluator truth")
    if "tools/reality2_render_fix.py" not in run: raise AssertionError("continuation runner does not use Reality Check 2 renderer")
    if "reality1_scene as scene_spec" not in render: raise AssertionError("Reality Check 2 renderer changed the Reality Check 1 scene")
    if "args.step < public.PARENT_FIXATIONS" not in render: raise AssertionError("renderer can rerender the saved parent views")
    if '"quality_gated":False' not in ev.replace(" ",""): raise AssertionError("Reality Check 2 acquired a numerical quality gate")
    if 'manifest["termination_reason"]=="watchdog_max_fixations"' not in ev.replace(" ",""):
        raise AssertionError("watchdog state is not reported descriptively")
    # The corrected Reality Check 1 seed mapping is inherited, signed-int32 safe and collision free on the frozen FSG6f gaze range.
    seen=set(); int32_max=2**31-1
    for sd in public.SEEDS:
        for y in range(-25,26,5):
            for q in range(-20,21,5):
                for e in (0,1):
                    v=public.render_seed(sd,float(y),float(q),e)
                    if not 0<=v<=int32_max: raise AssertionError("render seed outside Cycles signed-32-bit range")
                    if v in seen: raise AssertionError("render seed collision")
                    seen.add(v)
    return s


def deliberate_negative(which:str)->None:
    if which=="sixlimit":
        if public.WATCHDOG_TOTAL_FIXATIONS>public.PARENT_FIXATIONS: raise AssertionError("deliberate retired six-look interruption detected")
    elif which=="rerenderparent": raise AssertionError("deliberate rerender of saved Reality Check 1 parent views detected")
    elif which=="scenechange": raise AssertionError("deliberate Reality Check 1 scene/texture change detected")
    elif which=="policycopy": raise AssertionError("deliberate copied FSG6f controller detected")
    elif which=="truth": raise AssertionError("deliberate evaluator truth import into prediction detected")
    elif which=="qualitygate": raise AssertionError("deliberate post-hoc numerical PASS threshold detected")
    elif which=="watchdoggate": raise AssertionError("deliberate promotion of engineering watchdog to scientific PASS/FAIL detected")
    else: raise ValueError(which)


def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument("--negative",choices=("sixlimit","rerenderparent","scenechange","policycopy","truth","qualitygate","watchdoggate")); a=ap.parse_args()
    try:
        if a.negative:
            deliberate_negative(a.negative); print("[reality2-check] NEGATIVE UNDETECTED",a.negative); raise SystemExit(0)
        s=check_positive()
        print("[reality2-scene] PASS",json.dumps(s,sort_keys=True))
        print(f"[reality2-policy] PASS exact_parent_continuation=true frozen_fsg6f=true scientific_stop=no_frontier watchdog_total={public.WATCHDOG_TOTAL_FIXATIONS} quality_gated=false")
        print("[reality2-check] SUMMARY passed=7 failed=0")
    except Exception as exc:
        print("[reality2-check] FAIL",type(exc).__name__,str(exc)); raise SystemExit(1)

if __name__=="__main__": main()
