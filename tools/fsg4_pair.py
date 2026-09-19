"""Run one paired FSG4 active-versus-fixed-scan trial.

Both policies use the same fixture, profile and Monte-Carlo seed. Because render
seeds are keyed by yaw rather than step/policy, any yaw visited by both policies
must produce exactly identical RGB/oracle arrays; this script verifies that.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import fsg4_public as public
import fsg4_run
import fsg4_eval
import fsg4_metrics as metrics
from fsg_geometry import json_write


def _ns(base, out: Path, policy_name: str):
    return argparse.Namespace(repo=base.repo,out=str(out),profile=base.profile,fixture=base.fixture,seed=base.seed,
                              policy_name=policy_name,device=base.device,blender=base.blender,save_blend=base.save_blend)


def _observation_path(root: Path, step: int) -> Path:
    return root/"acquisitions"/f"fix_{step:02d}"/f"fix_{step:02d}"/"observation.npz"


def _acq_path(root: Path, step: int) -> Path:
    return root/"acquisitions"/f"fix_{step:02d}"/f"fix_{step:02d}"/"acquisition.json"


def _yaw_to_step(manifest: dict) -> dict[float,int]:
    return {round(float(y),8):i for i,y in enumerate(manifest["fixation_yaws_deg"])}


def verify_shared_views(active_root: Path, scan_root: Path, ma: dict, ms: dict) -> dict:
    aa=_yaw_to_step(ma); ss=_yaw_to_step(ms); shared=sorted(set(aa)&set(ss))
    if not shared:
        raise AssertionError("paired policies do not share even the seed fixation")
    rows=[]
    for y in shared:
        ia,ib=aa[y],ss[y]
        with np.load(_observation_path(active_root,ia),allow_pickle=False) as fa, np.load(_observation_path(scan_root,ib),allow_pickle=False) as fb:
            keys=sorted(fa.files)
            if keys!=sorted(fb.files):raise AssertionError("paired observation keys differ")
            exact=all(np.array_equal(fa[k],fb[k]) for k in keys)
        ca=json.loads(_acq_path(active_root,ia).read_text());cb=json.loads(_acq_path(scan_root,ib).read_text())
        seed_exact=ca["seeds_lr"]==cb["seeds_lr"]
        if not exact or not seed_exact:
            raise AssertionError(f"paired observation differs at shared yaw {y}")
        rows.append({"yaw_deg":float(y),"active_step":ia,"scan_step":ib,"arrays_exact":True,"seeds_exact":True,"seeds_lr":ca["seeds_lr"]})
    return {"shared_yaws_deg":[float(x) for x in shared],"shared_view_count":len(shared),"rows":rows,"all_exact":True}


def execute(args)->dict:
    out=Path(args.out).resolve()
    if out.exists():raise FileExistsError("pair output must be new")
    out.mkdir(parents=True)
    ar=out/"active";sr=out/"scan";ae=out/"active-evaluation";se=out/"scan-evaluation"
    ma=fsg4_run.execute(_ns(args,ar,"active"))
    ea=fsg4_eval.evaluate(ar,ae,args.mode)
    ms=fsg4_run.execute(_ns(args,sr,"scan"))
    es=fsg4_eval.evaluate(sr,se,args.mode)
    paired=verify_shared_views(ar,sr,ma,ms)
    ca=metrics.pad_curve(ea["truth_coverage_by_fixation"],public.MAX_BUDGET_FIXATIONS)
    cs=metrics.pad_curve(es["truth_coverage_by_fixation"],public.MAX_BUDGET_FIXATIONS)
    auc_a=metrics.normalized_auc(ca);auc_s=metrics.normalized_auc(cs)
    result={
        "schema":"FSG4-pair-v1","profile":args.profile,"fixture":args.fixture,"seed":args.seed,
        "active_status":ea["status"],"scan_status":es["status"],"active_fails":ea["fails"],"scan_fails":es["fails"],
        "active_fixations":ea["fixation_count"],"scan_fixations":es["fixation_count"],
        "active_primary_camera_samples":ea["primary_camera_samples"],"scan_primary_camera_samples":es["primary_camera_samples"],
        "logical_budget_fixations":public.MAX_BUDGET_FIXATIONS,
        "active_coverage_by_budget":ca,"scan_coverage_by_budget":cs,
        "active_auc":auc_a,"scan_auc":auc_s,"auc_gain":auc_a-auc_s,
        "active_final_coverage":ca[-1],"scan_final_coverage":cs[-1],"final_coverage_gain":ca[-1]-cs[-1],
        "paired_observation_identity":paired,
    }
    json_write(out/"pair.json",result)
    print("[fsg4-pair] COMPLETE",json.dumps(result,sort_keys=True),flush=True)
    return result


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("--repo",default=".");ap.add_argument("--out",required=True)
    ap.add_argument("--profile",choices=("small","full"),required=True);ap.add_argument("--fixture",choices=public.FIXTURES,required=True)
    ap.add_argument("--seed",type=int,choices=public.SEEDS,required=True);ap.add_argument("--mode",choices=("smoke","full"),required=True)
    ap.add_argument("--device",choices=("OPTIX","CUDA","CPU"),default="OPTIX");ap.add_argument("--blender",default="blender");ap.add_argument("--save-blend",action="store_true")
    r=execute(ap.parse_args())
    # Numerical misses are exit 2 but the pair is complete; integrity exceptions propagate as exit 1.
    raise SystemExit(0 if not r["active_fails"] and not r["scan_fails"] else 2)

if __name__=="__main__":main()
