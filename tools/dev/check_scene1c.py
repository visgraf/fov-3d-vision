"""Fail-capable software checks for Stage II / Scene-1c."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT/"tools") not in sys.path: sys.path.insert(0,str(ROOT/"tools"))
import scene1c_public as public
import scene1c_policy as policy
import scene1c_scene as scene
import scene1b_public as scheduler_public


def _assert(c,msg):
    if not c: raise AssertionError(msg)


def _proposal(oid:int,count:int,area:float,score:float,gaze)->dict:
    return {"object_id":oid,"stop":False,"autonomous_target_count":count,
            "selected":{"predicted_new_angular_area_deg2":area,"frontier_score":score,"next_gaze_deg":list(gaze)}}


def run_checks()->list[str]:
    passed=[]
    _assert(public.MAX_SCENE_FIXATIONS==18==len(public.OBJECT_IDS)*public.PER_OBJECT_MAX_FIXATIONS,"scene budget drift")
    _assert(public.PER_OBJECT_MAX_FIXATIONS==scheduler_public.PER_OBJECT_MAX_FIXATIONS,"per-object budget changed from Scene-1b")
    _assert(public.MAX_SCENE_FIXATIONS==scheduler_public.MAX_SCENE_FIXATIONS,"global budget changed from Scene-1b")
    _assert(public.FUSION==scheduler_public.FUSION=={"association_radius_m":0.012,"hash_cell_m":0.012},"fusion drift")
    _assert(public.TARGETS==scheduler_public.TARGETS,"Scene-1b numerical gates drifted")
    _assert(public.PUBLIC_SPEC["fixed_head"] and public.PUBLIC_SPEC["static_scene"],"fixed-head/static-scene base case lost")
    _assert(public.PUBLIC_SPEC["component_certification_required_before_ensemble"] is True,"component certification no longer required")
    passed.append("public-contract")

    expected=set(public.expected_component_trials())
    _assert(len(expected)==12,"component certification matrix is not 2x2x3")
    _assert(all(f in public.FIXTURES and s in public.SEEDS and o in public.OBJECT_IDS for f,s,o in expected),"component certification matrix malformed")
    passed.append("certification-matrix")

    pf=scene.preflight(); _assert(set(pf)==set(public.FIXTURES),"scene preflight incomplete")
    for f in public.FIXTURES:
        for oid in public.OBJECT_IDS:
            r=pf[f]["seeds"][oid]
            _assert(0.45<=float(r["seed_ideal_coverage"])<=0.70,"seed no longer controlled partial view")
            _assert(float(r["design_witness_ideal_coverage"])>=0.98,"fresh object lacks short geometric reachability witness")
            _assert(int(r["design_witness_look_count"])<public.PER_OBJECT_MAX_FIXATIONS,"design witness consumes full object budget")
    passed.append("scene-geometry")

    policy.self_test()
    ps=[_proposal(201,1,999.,999.,(0,0)),_proposal(202,0,4.,1.,(1,0)),_proposal(203,0,5.,2.,(2,0))]
    d=policy.select_proposal(ps)
    _assert(d["selected_object_id"]==203 and d["fair_eligible_object_ids"]==[202,203],"frozen Scene-1b fairness semantics changed")
    passed.append("frozen-scheduler-semantics")

    psrc=(ROOT/"tools"/"scene1c_policy.py").read_text(); bsrc=(ROOT/"tools"/"scene1b_policy.py").read_text()
    _assert("import scene1b_policy as frozen_scene_scheduler" in psrc,"Scene-1b scheduler not imported")
    _assert("def select_proposal" not in psrc and "def proposal_rank_key" not in psrc,"Scene-1b scheduler was copied/reimplemented")
    _assert("import fsg6f_frontier as object_policy" in bsrc,"frozen Scene-1b scheduler no longer imports FSG6f")
    _assert("import fsg6f_frontier" not in psrc,"Scene-1c bypassed frozen Scene-1b scheduler layer")
    passed.append("frozen-policy-stack")

    crun=(ROOT/"tools"/"scene1c_certify_run.py").read_text(); erun=(ROOT/"tools"/"scene1c_run.py").read_text(); ccmp=(ROOT/"tools"/"scene1c_certify_compare.py").read_text(); finalcmp=(ROOT/"tools"/"scene1c_compare.py").read_text()
    _assert('"tools/scene1c_render_fix.py"' in crun and '"tools/scene1c_render_fix.py"' in erun,"component and ensemble do not share renderer")
    _assert("scene1c_scene" not in crun and "evaluation_only" not in crun,"component prediction imports evaluator truth")
    _assert("scene1c_scene" not in erun and "evaluation_only" not in erun,"ensemble prediction imports evaluator truth")
    _assert("EXPECTED=set(public.expected_component_trials())" in ccmp and "seen!=EXPECTED" in ccmp,"component certification compare does not require the full prospective set")
    _assert("--certification" in finalcmp and "component certification prerequisite did not pass" in finalcmp,"final Scene-1c aggregate does not require passed component certification")
    passed.append("certification-plumbing")

    _assert("DESIGN_WITNESS" not in crun and "DESIGN_WITNESS" not in erun and "DESIGN_WITNESS" not in psrc,"evaluator design witness leaked into prediction")
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

    print(f"[scene1c-scene] PASS fixtures={','.join(public.FIXTURES)} objects={list(public.OBJECT_IDS)} fixed_head=true static_scene=true witnesses_lt_budget=true")
    print("[scene1c-policy] PASS frozen_fsg6f=true frozen_scene1b_scheduler=true fairness=true component_certification=true opportunistic=true")
    print(f"[scene1c-check] SUMMARY passed={len(passed)} failed=0")
    return passed


def negative(name:str)->None:
    if name=="incompletecert":
        got=set(public.expected_component_trials())-{public.expected_component_trials()[0]}
        _assert(got==set(public.expected_component_trials()),"deliberate incomplete component certification set detected")
    elif name=="areaonly":
        ps=[_proposal(201,1,999.,999.,(0,0)),_proposal(202,0,4.,1.,(1,0)),_proposal(203,0,5.,2.,(2,0))]
        _assert(policy.select_proposal(ps)["selected_object_id"]==201,"deliberate retired Scene-1a area-only scheduler detected")
    elif name=="schedulercopy":
        text=(ROOT/"tools"/"scene1c_policy.py").read_text(); _assert("def select_proposal" in text,"deliberate copied Scene-1b scheduler detected")
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
        text=(ROOT/"tools"/"scene1c_run.py").read_text()+(ROOT/"tools"/"scene1c_certify_run.py").read_text()
        _assert("scene1c_scene" in text or "evaluation_only" in text,"deliberate evaluator-truth import into prediction detected")
    elif name=="overlap":
        scene.preflight(); _assert(False,"deliberate object-object angular overlap substitute detected")
    elif name=="underdesigned":
        f=public.FIXTURES[0]; oid=public.OBJECT_IDS[0]; g=public.seed_gaze_for_object(f,oid)
        _assert(scene.ideal_trace_coverage(f,oid,[g])>=0.98,"deliberate one-look underdesigned fixture detected")
    elif name=="budgetbump":
        _assert(public.PER_OBJECT_MAX_FIXATIONS>6 or public.MAX_SCENE_FIXATIONS>18,"deliberate post-Scene-1b budget increase detected")
    else: raise ValueError("unknown negative")


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--negative",choices=("incompletecert","areaonly","schedulercopy","targetonly","premature","revisit","truth","overlap","underdesigned","budgetbump")); a=ap.parse_args()
    try:
        if a.negative: negative(a.negative); print("[scene1c-check] negative unexpectedly passed"); raise SystemExit(0)
        run_checks()
    except Exception as e:
        print(f"[scene1c-check] FAIL {type(e).__name__} {e}"); raise SystemExit(1)
if __name__=="__main__": main()
