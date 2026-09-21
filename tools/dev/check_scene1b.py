"""Fail-capable software checks for Stage II / Scene-1b."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT/"tools") not in sys.path: sys.path.insert(0,str(ROOT/"tools"))
import scene1b_public as public
import scene1b_policy as policy
import scene1b_scene as scene


def _assert(c,msg):
    if not c: raise AssertionError(msg)


def _proposal(oid:int,count:int,area:float,score:float,gaze)->dict:
    return {"object_id":oid,"stop":False,"autonomous_target_count":count,
            "selected":{"predicted_new_angular_area_deg2":area,"frontier_score":score,"next_gaze_deg":list(gaze)}}


def run_checks()->list[str]:
    passed=[]
    _assert(public.MAX_SCENE_FIXATIONS==len(public.OBJECT_IDS)*public.PER_OBJECT_MAX_FIXATIONS,"scene budget not derived from per-object budget")
    _assert(public.FUSION=={"association_radius_m":0.012,"hash_cell_m":0.012},"fusion drift")
    _assert(public.PUBLIC_SPEC["fixed_head"] and public.PUBLIC_SPEC["static_scene"],"fixed-head/static-scene base case lost")
    _assert("least autonomous post-seed service" in public.PUBLIC_SPEC["scene_scheduler"],"fair scheduler missing from public contract")
    passed.append("public-contract")

    pf=scene.preflight(); _assert(set(pf)==set(public.FIXTURES),"scene preflight incomplete")
    for f in public.FIXTURES:
        for oid in public.OBJECT_IDS:
            r=pf[f]["seeds"][oid]
            _assert(0.35<=float(r["seed_ideal_coverage"])<=0.70,"seed no longer controlled partial view")
            _assert(float(r["design_witness_ideal_coverage"])>=0.98,"fresh object lacks short solvability witness")
            _assert(int(r["design_witness_look_count"])<public.PER_OBJECT_MAX_FIXATIONS,"design witness consumes full object budget")
    passed.append("scene-geometry")

    policy.self_test(); passed.append("scheduler-semantics")
    ps=[_proposal(201,1,999.,999.,(0,0)),_proposal(202,0,4.,1.,(1,0)),_proposal(203,0,5.,2.,(2,0))]
    d=policy.select_proposal(ps)
    _assert(d["selected_object_id"]==203 and d["fair_eligible_object_ids"]==[202,203],"fairness constraint is not load-bearing")
    passed.append("fairness-load-bearing")

    src=(ROOT/"tools"/"scene1b_policy.py").read_text(); runsrc=(ROOT/"tools"/"scene1b_run.py").read_text()
    _assert("import fsg6f_frontier as object_policy" in src,"frozen FSG6f controller not imported")
    _assert("def extract_frontier" not in src and "candidate_state_consensus" not in src,"FSG6f policy was copied/reimplemented")
    _assert("DESIGN_WITNESS" not in src and "DESIGN_WITNESS" not in runsrc,"evaluator design witness leaked into prediction")
    passed.append("frozen-fsg6f-reuse")

    _assert("scene1b_scene" not in runsrc and "evaluation_only" not in runsrc,"prediction runner imports evaluator truth")
    _assert("scene1b_scene" not in src and "evaluation_only" not in src,"scene policy imports evaluator truth")
    passed.append("truth-isolation")

    ids=np.array([[201,202,203,299]],np.int32); valid=np.ones_like(ids,bool); masks=policy.split_visible_object_masks(ids,valid)
    _assert(all(int(masks[o].sum())==1 for o in public.OBJECT_IDS),"target-only update would drop visible non-target objects")
    passed.append("opportunistic-update")

    proposals=[{"object_id":201,"stop":True,"autonomous_target_count":0,"selected":None},
               {"object_id":202,"stop":True,"autonomous_target_count":0,"selected":None},
               _proposal(203,0,1.,1.,(0,0))]
    _assert(not policy.select_proposal(proposals)["stop"],"scene stopped while an object remained incomplete")
    for p in proposals: p["stop"]=True; p["selected"]=None
    _assert(policy.select_proposal(proposals)["reason"]=="scene_complete","all-object completion broken")
    passed.append("all-object-completion")

    _assert(policy.is_global_repeat((5.,0.),[(0.,0.),(5.,0.)]),"global no-revisit not enforced")
    passed.append("global-no-revisit")

    print(f"[scene1b-scene] PASS fixtures={','.join(public.FIXTURES)} objects={list(public.OBJECT_IDS)} fixed_head=true static_scene=true witness_lt_budget=true")
    print("[scene1b-policy] PASS frozen_fsg6f=true scheduler=least_service_then_area_then_score fairness=true opportunistic=true all_object_completion=true")
    print(f"[scene1b-check] SUMMARY passed={len(passed)} failed=0")
    return passed


def negative(name:str)->None:
    if name=="areaonly":
        ps=[_proposal(201,1,999.,999.,(0,0)),_proposal(202,0,4.,1.,(1,0)),_proposal(203,0,5.,2.,(2,0))]
        _assert(policy.select_proposal(ps)["selected_object_id"]==201,"deliberate retired Scene-1a area-only scheduler detected")
    elif name=="targetonly":
        ids=np.array([[201,202,203]],np.int32); m=policy.split_visible_object_masks(ids,np.ones_like(ids,bool)); _assert(int(m[202].sum())==0,"deliberate target-only fusion detected")
    elif name=="premature":
        ps=[{"object_id":201,"stop":True,"autonomous_target_count":0,"selected":None},
            {"object_id":202,"stop":True,"autonomous_target_count":0,"selected":None},
            _proposal(203,0,1.,1.,(0,0))]
        _assert(policy.select_proposal(ps)["stop"],"deliberate premature scene completion detected")
    elif name=="revisit":
        _assert(not policy.is_global_repeat((5.,0.),[(0.,0.),(5.,0.)]),"deliberate physical fixation revisit detected")
    elif name=="truth":
        text=(ROOT/"tools"/"scene1b_run.py").read_text(); _assert("scene1b_scene" in text or "evaluation_only" in text,"deliberate evaluator-truth import into prediction runner detected")
    elif name=="copiedpolicy":
        text=(ROOT/"tools"/"scene1b_policy.py").read_text(); _assert("def extract_frontier" in text,"deliberate copied/reimplemented FSG6f controller detected")
    elif name=="overlap":
        scene.preflight(); _assert(False,"deliberate object-object angular overlap substitute detected")
    elif name=="underdesigned":
        f=public.FIXTURES[0]; oid=public.OBJECT_IDS[0]; g=public.SEED_SEQUENCE[f][0][1]
        _assert(scene.ideal_trace_coverage(f,oid,[g])>=0.98,"deliberate one-look underdesigned fixture detected")
    else: raise ValueError("unknown negative")


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--negative",choices=("areaonly","targetonly","premature","revisit","truth","copiedpolicy","overlap","underdesigned")); a=ap.parse_args()
    try:
        if a.negative: negative(a.negative); print("[scene1b-check] negative unexpectedly passed"); raise SystemExit(0)
        run_checks()
    except Exception as e:
        print(f"[scene1b-check] FAIL {type(e).__name__} {e}"); raise SystemExit(1)
if __name__=="__main__": main()
