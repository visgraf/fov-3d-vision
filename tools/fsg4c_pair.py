"""Run one paired FSG4c fresh active-versus-fixed-scan trial.

The active run is acquired first. The scan then reuses the active acquisition
artifact for every yaw the two policies share, and renders only scan-only yaws.
Thus the paired-noise contract remains bit-exact even when repeated OptiX renders
of the same seeded view differ by last-ulp floating-point accumulation.
"""
from __future__ import annotations
import argparse
import json
import shutil
import time
from pathlib import Path
import numpy as np
import fsg4c_public as public
import fsg4c_run as fsg4_run
import fsg4c_eval as fsg4_eval
import fsg4_metrics as metrics
from fsg_geometry import json_write


def _ns(base, out: Path, policy_name: str, view_provider=None):
    return argparse.Namespace(repo=base.repo,out=str(out),profile=base.profile,fixture=base.fixture,seed=base.seed,
                              policy_name=policy_name,device=base.device,blender=base.blender,save_blend=base.save_blend,
                              view_provider=view_provider)


def _observation_path(root: Path, step: int) -> Path:
    return root/"acquisitions"/f"fix_{step:02d}"/f"fix_{step:02d}"/"observation.npz"


def _acq_path(root: Path, step: int) -> Path:
    return root/"acquisitions"/f"fix_{step:02d}"/f"fix_{step:02d}"/"acquisition.json"


def _yaw_to_step(manifest: dict) -> dict[float,int]:
    return {round(float(y),8):i for i,y in enumerate(manifest["fixation_yaws_deg"])}


def active_view_cache(active_root: Path, manifest: dict) -> dict[float, Path]:
    """Index complete active acquisition roots by yaw; contains no policy truth."""
    out={}
    for step,yaw in enumerate(manifest["fixation_yaws_deg"]):
        root=active_root/"acquisitions"/f"fix_{step:02d}"
        if not (root/"run.json").is_file():
            raise FileNotFoundError(f"missing active acquisition for paired cache: {root}")
        out[round(float(yaw),8)] = root
    return out


def clone_paired_view(source_root: Path, args, step: int, yaw: float, acq_root: Path) -> tuple[Path, dict]:
    """Clone one already-rendered same-yaw acquisition into another policy step.

    The RGB/oracle/calibration/evaluator assets remain byte-identical. Only the
    step-local metadata is rewritten. `primary_camera_samples` remains the
    logical camera budget charged to this policy; `new_primary_camera_samples`
    records that this execution rendered zero new primary samples for the clone.
    """
    t0=time.perf_counter()
    source_root=Path(source_root).resolve();acq_root=Path(acq_root).resolve()
    src_run=json.loads((source_root/"run.json").read_text())
    if (not src_run.get("complete") or src_run.get("fixture")!=args.fixture or
        src_run.get("profile")!=args.profile or int(src_run.get("seed"))!=int(args.seed) or
        abs(float(src_run.get("yaw_deg"))-float(yaw))>1e-8 or
        src_run.get("public_spec_sha256")!=public.public_digest()):
        raise AssertionError("paired cache source does not match requested fixture/profile/seed/yaw/spec")
    src_case_name=str(src_run.get("case"))
    src_case=source_root/src_case_name
    if not src_case.is_dir():
        raise FileNotFoundError(f"paired cache source case missing: {src_case}")
    out=acq_root/f"fix_{step:02d}"
    if out.exists():
        raise FileExistsError(f"paired cache destination already exists: {out}")
    shutil.copytree(source_root,out)
    copied_case=out/src_case_name
    dest_case_name=f"fix_{step:02d}"
    dest_case=out/dest_case_name
    if copied_case!=dest_case:
        if dest_case.exists():
            raise FileExistsError(f"paired cache destination case already exists: {dest_case}")
        copied_case.rename(dest_case)
    acq_path=dest_case/"acquisition.json"
    acq=json.loads(acq_path.read_text())
    if acq.get("seeds_lr")!=src_run.get("seeds_lr"):
        raise AssertionError("paired cache source seed metadata disagrees")
    acq["case"]=dest_case_name
    acq["step"]=int(step)
    acq["paired_observation_reused"]=True
    acq["paired_source_step"]=int(src_run.get("step"))
    acq["paired_source_case"]=src_case_name
    acq["new_primary_camera_samples"]=0
    acq["render_seconds_lr"]=[0.0,0.0]
    json_write(acq_path,acq)
    run=dict(src_run)
    run["case"]=dest_case_name
    run["step"]=int(step)
    run["paired_observation_reused"]=True
    run["paired_source_step"]=int(src_run.get("step"))
    run["paired_source_case"]=src_case_name
    run["new_primary_camera_samples"]=0
    run["total_wall_seconds"]=time.perf_counter()-t0
    json_write(out/"run.json",run)
    return dest_case,run


def make_scan_view_provider(cache: dict[float,Path]):
    """Return a view provider that reuses active shared yaws and renders others."""
    def provider(args, step: int, yaw: float, acq_root: Path):
        source=cache.get(round(float(yaw),8))
        if source is None:
            case,run=fsg4_run.run_blender(args,step,yaw,acq_root)
            run=dict(run)
            run["new_primary_camera_samples"]=int(run["primary_camera_samples"])
            return case,run
        return clone_paired_view(source,args,step,yaw,acq_root)
    return provider


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
        reused=bool(cb.get("paired_observation_reused",False))
        if not exact or not seed_exact or not reused:
            raise AssertionError(f"paired observation differs or was not reused at shared yaw {y}")
        rows.append({"yaw_deg":float(y),"active_step":ia,"scan_step":ib,"arrays_exact":True,"seeds_exact":True,
                     "scan_reused_active_view":True,"seeds_lr":ca["seeds_lr"]})
    return {"shared_yaws_deg":[float(x) for x in shared],"shared_view_count":len(shared),"rows":rows,
            "all_exact":True,"all_scan_shared_views_reused":True}


def execute(args)->dict:
    out=Path(args.out).resolve()
    if out.exists():raise FileExistsError("pair output must be new")
    out.mkdir(parents=True)
    ar=out/"active";sr=out/"scan";ae=out/"active-evaluation";se=out/"scan-evaluation"
    # Active runs first and is never allowed to inspect the scan or the paired cache.
    ma=fsg4_run.execute(_ns(args,ar,"active"))
    ea=fsg4_eval.evaluate(ar,ae,args.mode)
    cache=active_view_cache(ar,ma)
    # The scan is fixed in advance. At shared yaws it consumes the exact active
    # acquisition artifact; scan-only yaws are newly rendered with the frozen seed rule.
    ms=fsg4_run.execute(_ns(args,sr,"scan",make_scan_view_provider(cache)))
    es=fsg4_eval.evaluate(sr,se,args.mode)
    paired=verify_shared_views(ar,sr,ma,ms)
    ca=metrics.pad_curve(ea["truth_coverage_by_fixation"],public.MAX_BUDGET_FIXATIONS)
    cs=metrics.pad_curve(es["truth_coverage_by_fixation"],public.MAX_BUDGET_FIXATIONS)
    auc_a=metrics.normalized_auc(ca);auc_s=metrics.normalized_auc(cs)
    result={
        "schema":"FSG4c-pair-v1-exact-shared-view-reuse","profile":args.profile,"fixture":args.fixture,"seed":args.seed,
        "active_status":ea["status"],"scan_status":es["status"],"active_fails":ea["fails"],"scan_fails":es["fails"],
        "active_fixations":ea["fixation_count"],"scan_fixations":es["fixation_count"],
        "active_primary_camera_samples":ea["primary_camera_samples"],"scan_primary_camera_samples":es["primary_camera_samples"],
        "active_new_render_primary_samples":int(ma.get("new_primary_camera_samples",ma["primary_camera_samples"])),
        "scan_new_render_primary_samples":int(ms.get("new_primary_camera_samples",ms["primary_camera_samples"])),
        "scan_reused_shared_view_count":int(ms.get("paired_observation_reuse_count",0)),
        "logical_budget_fixations":public.MAX_BUDGET_FIXATIONS,
        "active_coverage_by_budget":ca,"scan_coverage_by_budget":cs,
        "active_auc":auc_a,"scan_auc":auc_s,"auc_gain":auc_a-auc_s,
        "active_final_coverage":ca[-1],"scan_final_coverage":cs[-1],"final_coverage_gain":ca[-1]-cs[-1],
        "paired_observation_identity":paired,
    }
    json_write(out/"pair.json",result)
    print("[fsg4c-pair] COMPLETE",json.dumps(result,sort_keys=True),flush=True)
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
