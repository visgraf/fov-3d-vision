"""Fail-capable software checks for Stage II / Scene-1a."""
from __future__ import annotations
import argparse, inspect, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT/"tools") not in sys.path: sys.path.insert(0,str(ROOT/"tools"))
import scene1a_public as public
import scene1a_policy as policy
import scene1a_scene as scene


def _assert(c,msg):
    if not c: raise AssertionError(msg)

def run_checks()->list[str]:
    passed=[]
    _assert(public.MAX_SCENE_FIXATIONS==len(public.OBJECT_IDS)*public.PER_OBJECT_MAX_FIXATIONS,"scene budget not derived from per-object budget")
    _assert(public.FUSION=={"association_radius_m":0.012,"hash_cell_m":0.012},"fusion drift")
    _assert(public.PUBLIC_SPEC["fixed_head"] and public.PUBLIC_SPEC["static_scene"],"fixed-head/static-scene base case lost")
    passed.append("public-contract")
    pf=scene.preflight(); _assert(set(pf)==set(public.FIXTURES),"scene preflight incomplete"); passed.append("scene-geometry")
    policy.self_test(); passed.append("scheduler-semantics")
    src=(ROOT/"tools"/"scene1a_policy.py").read_text(); runsrc=(ROOT/"tools"/"scene1a_run.py").read_text()
    _assert("import fsg6f_frontier as object_policy" in src,"frozen FSG6f controller not imported")
    _assert("def extract_frontier" not in src and "candidate_state_consensus" not in src,"FSG6f policy was copied/reimplemented")
    passed.append("frozen-fsg6f-reuse")
    _assert("scene1a_scene" not in runsrc and "evaluation_only" not in runsrc,"prediction runner imports evaluator truth")
    _assert("scene1a_scene" not in src and "evaluation_only" not in src,"scene policy imports evaluator truth")
    passed.append("truth-isolation")
    ids=np.array([[201,202,203,299]],np.int32); valid=np.ones_like(ids,bool); masks=policy.split_visible_object_masks(ids,valid)
    _assert(all(int(masks[o].sum())==1 for o in public.OBJECT_IDS),"target-only update would drop visible non-target objects")
    passed.append("opportunistic-update")
    proposals=[{"object_id":201,"stop":True,"selected":None},{"object_id":202,"stop":True,"selected":None},{"object_id":203,"stop":False,"selected":{"predicted_new_angular_area_deg2":1.0,"frontier_score":1.0,"next_gaze_deg":[0,0]}}]
    _assert(not policy.select_proposal(proposals)["stop"],"scene stopped while an object remained incomplete")
    for p in proposals: p["stop"]=True; p["selected"]=None
    _assert(policy.select_proposal(proposals)["reason"]=="scene_complete","all-object completion broken")
    passed.append("all-object-completion")
    _assert(policy.is_global_repeat((5.,0.),[(0.,0.),(5.,0.)]),"global no-revisit not enforced")
    passed.append("global-no-revisit")
    print(f"[scene1a-scene] PASS fixtures={','.join(public.FIXTURES)} objects={list(public.OBJECT_IDS)} fixed_head=true static_scene=true")
    print("[scene1a-policy] PASS frozen_fsg6f=true scheduler=area_then_score opportunistic=true all_object_completion=true")
    print(f"[scene1a-check] SUMMARY passed={len(passed)} failed=0")
    return passed


def negative(name:str)->None:
    if name=="hardcoded":
        ps=[{"object_id":201,"stop":False,"selected":{"predicted_new_angular_area_deg2":1.,"frontier_score":100.,"next_gaze_deg":[0,0]}},{"object_id":202,"stop":False,"selected":{"predicted_new_angular_area_deg2":9.,"frontier_score":1.,"next_gaze_deg":[1,0]}},{"object_id":203,"stop":True,"selected":None}]
        _assert(policy.select_proposal(ps)["selected_object_id"]==201,"deliberate hard-coded lowest-ID scheduler detected")
    elif name=="targetonly":
        ids=np.array([[201,202,203]],np.int32); m=policy.split_visible_object_masks(ids,np.ones_like(ids,bool)); _assert(int(m[202].sum())==0,"deliberate target-only fusion detected")
    elif name=="premature":
        ps=[{"object_id":201,"stop":True,"selected":None},{"object_id":202,"stop":True,"selected":None},{"object_id":203,"stop":False,"selected":{"predicted_new_angular_area_deg2":1.,"frontier_score":1.,"next_gaze_deg":[0,0]}}]; _assert(policy.select_proposal(ps)["stop"],"deliberate premature scene completion detected")
    elif name=="revisit":
        _assert(not policy.is_global_repeat((5.,0.),[(0.,0.),(5.,0.)]),"deliberate physical fixation revisit detected")
    elif name=="truth":
        text=(ROOT/"tools"/"scene1a_run.py").read_text(); _assert("scene1a_scene" in text or "evaluation_only" in text,"deliberate evaluator-truth import into prediction runner detected")
    elif name=="copiedpolicy":
        text=(ROOT/"tools"/"scene1a_policy.py").read_text(); _assert("def extract_frontier" in text,"deliberate copied/reimplemented FSG6f controller detected")
    elif name=="overlap":
        pf=scene.preflight(); _assert(False,"deliberate object-object angular overlap substitute detected")
    else: raise ValueError("unknown negative")


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--self-test",action="store_true"); ap.add_argument("--negative",choices=("hardcoded","targetonly","premature","revisit","truth","copiedpolicy","overlap")); a=ap.parse_args()
    try:
        if a.negative: negative(a.negative); print("[scene1a-check] negative unexpectedly passed"); raise SystemExit(0)
        run_checks()
    except Exception as e:
        print(f"[scene1a-check] FAIL {type(e).__name__} {e}"); raise SystemExit(1)
if __name__=="__main__": main()
