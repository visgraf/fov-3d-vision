"""Software checks for FSG1d; synthetic records cannot produce a real validation pass.

 python tools/dev/check_fsg_validation.py --self-test --report OUT.json
 python tools/dev/check_fsg_validation.py --negative visibility  # must exit 1
 python tools/dev/check_fsg_validation.py --negative leakage     # must exit 1
 python tools/dev/check_fsg_validation.py --negative geometry    # must exit 1
"""
from __future__ import annotations
import argparse
import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import numpy as np
TOOLS=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(TOOLS),str(TOOLS/"dev")]
import fsg_geometry as g
import fsg_scene as original_scene
import fsg_evaluate as e
import fsg_stereo as s
import fsg_stereo_hdr as h
import fsg_coverage_audit as audit
import fsg_hdr_compare as old_compare
import fsg_validation_scene as spec
import fsg_validation_render as render
import fsg_validation_eval as evaluation


def require(ok: bool, text: str="assertion") -> None:
    if not ok: raise AssertionError(text)


def raises(kind, fn):
    try: fn()
    except kind: return
    raise AssertionError("expected " + kind.__name__)


def fixture(name="step_right", profile="small"):
    c=g.make_calibration(profile,*spec.CASE_GAZE[name])
    mesh=original_scene.triangulate_objects(spec.validation_objects(name))
    return c,mesh,e.ground_reference(c,mesh)


class SyntheticValidationBackend:
    """Test-only analytic texture sampler, NOT a Blender or radiance simulation."""
    source="synthetic_stub"
    version="NOT BLENDER: FSG1d analytic software fixture"
    device="CPU synthetic fixture"
    checks={"independent_blender_checks":False,"fixture_only":True}

    def prepare(self,name,c,folder,spp):
        self.mesh=original_scene.triangulate_objects(spec.validation_objects(name))
        return self.mesh

    def render_eye(self,eye_id,c,folder,spp,seed):
        start=time.perf_counter();eye=c["eyes"][eye_id];w,height=c["image_size_wh"]
        hit=original_scene.ray_mesh(np.asarray(eye["centre_h_m"]),g.rays_h(eye,g.pixels(w,height)),self.mesh)
        ids=hit["instance_id"];rgb=np.full((height,w,3),.05,np.float32)
        for ident in np.unique(ids):
            if ident<=0:continue
            mask=ids==ident;tex=spec.validation_texture(int(ident));n=len(tex)
            uv=np.einsum("ni,nij->nj",hit["barycentric"][mask],self.mesh["triangle_uv"][hit["triangle"][mask]])
            xy=np.clip(uv*n-.5,0,n-1-1e-6);xy0=np.floor(xy).astype(int)
            x,y=xy0[:,0],xy0[:,1];a,b=(xy[:,0]-x)[:,None],(xy[:,1]-y)[:,None]
            rgb[mask]=(1-b)*((1-a)*tex[y,x]+a*tex[y,x+1])+b*((1-a)*tex[y+1,x]+a*tex[y+1,x+1])
        rgb+=np.random.default_rng(seed).normal(0,.001,rgb.shape).astype(np.float32)
        return rgb,time.perf_counter()-start


def make_synthetic(path:Path,profile="small",seed=31):
    args=render.parse_args(["--out",str(path),"--profile",profile,"--seed",str(seed)])
    return render.acquire_validation(args,SyntheticValidationBackend())


def negative_visibility():
    c=g.make_calibration("small")
    mesh=original_scene.triangulate_objects(original_scene.case_objects("step"))
    mono=e.ground_reference(c,mesh)[3]
    evaluation.occlusion_reference("step_right","small",mono)


def negative_leakage():
    c,mesh,(_,_,_,mono)=fixture()
    core,desc=evaluation.occlusion_reference("step_right","small",mono)
    mask=np.zeros_like(mono);mask[tuple(np.argwhere(core)[0])]=True
    r=evaluation.occlusion_result(mask,mono,core,desc)
    require(r["checks_pass"], f"accepted {r['accepted_core']} singly-visible core pixels; limit=0")


def negative_geometry():
    _,mesh,_=fixture();mesh["triangles_h"]=mesh["triangles_h"].copy();mesh["triangles_h"][:,:,2]+=.1
    spec.validate_mesh("step_right",mesh)


def self_test() -> dict:
    start=time.perf_counter();checks=[];details=io.StringIO();summaries=[]
    def check(name,fn):
        try:fn();checks.append({"name":name,"pass":True});print("[fsg-validation-check] PASS",name)
        except Exception as exc:checks.append({"name":name,"pass":False,"error":repr(exc)});print("[fsg-validation-check] FAIL",name,repr(exc))
    check("frozen old renderer/estimator/evaluator sources",spec.check_frozen)
    check("renderer AST differs only in fixture and texture dispatch",render.check_renderer_equivalence)
    check("HDR candidate kernel unchanged",h.check_kernel_equivalence)
    check("spec digest is reproducible",lambda:require(spec.spec_digest()==spec.spec_digest()))
    check("development seed 17 is excluded",lambda:require(17 not in spec.SEEDS))
    check("new texture differs without changing instance identity",lambda:require(
        not np.array_equal(original_scene.texture(1),spec.validation_texture(1)) and
        np.array_equal(spec.validation_texture(1),spec.validation_texture(1))))
    check("unknown fixture rejected",lambda:raises(ValueError,lambda:spec.validation_objects("step")))
    for profile in ("small","full"):
        for name in spec.CASES:
            c,mesh,(truth,eligible,band,mono)=fixture(name,profile)
            core,desc=evaluation.occlusion_reference(name,profile,mono)
            check(f"{profile}/{name} substantial per-instance interiors",lambda tr=truth,m=mesh,el=eligible,b=band:require(
                all(np.count_nonzero(el&~b&(tr["instance_id"]==i))>=100 for i in np.unique(m["instance_ids"]))))
            check(f"{profile}/{name} geometry export equivalence",lambda n=name,m=mesh:spec.validate_mesh(n,m))
            if name=="step_right":
                check(f"{profile}/step has nonempty left half-occlusion core",lambda d=desc:require(d["core_pixels"]>0))
                check(f"{profile}/occlusion core is subset of raw mask",lambda co=core,mo=mono:require(not np.any(co&~mo)))
            else:
                check(f"{profile}/tilted no false half-occlusion test claim",lambda d=desc:require(d["status"]=="NOT_EXERCISED"))
    check("wrong old-step orientation fails visibility control",lambda:raises(ValueError,negative_visibility))
    check("one unsafe acceptance fails leakage control",lambda:raises(AssertionError,negative_leakage))
    check("wrong depth fails fixture geometry control",lambda:raises(ValueError,negative_geometry))
    _,mesh,_=fixture();permuted={k:v.copy() for k,v in mesh.items()}
    permuted["triangles_h"]=permuted["triangles_h"][::-1,::-1];permuted["instance_ids"]=permuted["instance_ids"][::-1]
    check("triangle order and winding do not invalidate correct mesh",lambda:spec.validate_mesh("step_right",permuted))
    alternative=original_scene.triangulate_objects(spec.validation_objects("step_right"))
    alternative["triangles_h"]=np.array([obj["vertices_h"][indices]
        for obj in spec.validation_objects("step_right") for indices in ([0,1,3],[1,2,3])])
    check("either legal quad diagonal is accepted",lambda:spec.validate_mesh("step_right",alternative))
    duplicate={k:v.copy() for k,v in alternative.items()};duplicate["triangles_h"][1]=duplicate["triangles_h"][0]
    check("duplicate triangles cannot hide missing surface",lambda:raises(ValueError,lambda:spec.validate_mesh("step_right",duplicate)))
    check("fixed full schedule accepted",lambda:evaluation.validate_schedule([{"profile":"full","seed":31},{"profile":"full","seed":73}],"full"))
    check("one successful seed cannot replace full schedule",lambda:raises(ValueError,lambda:evaluation.validate_schedule([{"profile":"full","seed":31}],"full")))
    check("duplicate seed cannot masquerade as repetition",lambda:raises(ValueError,lambda:evaluation.validate_schedule([{"profile":"full","seed":31}]*2,"full")))
    # Verify import-time separation of Blender and host dependencies in a clean interpreter.
    code="""import sys, importlib.abc
sys.path.insert(0,sys.argv[1])
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0] in {'cv2','PIL'}: raise ImportError('forbidden host dependency '+fullname)
sys.meta_path.insert(0,Block())
import fsg_validation_render
fsg_validation_render.check_renderer_equivalence()
"""
    check("Blender-side module imports without OpenCV or Pillow",lambda:subprocess.run([sys.executable,"-c",code,str(TOOLS)],check=True,capture_output=True))
    with tempfile.TemporaryDirectory(prefix="fsg1d-check-") as temp:
        root=Path(temp);run=root/"small31"
        with contextlib.redirect_stdout(details):make_synthetic(run)
        check("synthetic record obeys full acquisition specification",lambda:evaluation.read_run(run,True))
        check("synthetic record refused in real mode",lambda:raises(ValueError,lambda:evaluation.read_run(run,False)))
        check("new acquisition refuses overwrite",lambda:raises(FileExistsError,lambda:make_synthetic(run)))
        before=old_compare.snapshot([run])
        with contextlib.redirect_stdout(details):report=evaluation.compare([run],root/"smoke", "smoke",True)
        summaries.append(report)
        check("read-only comparison preserves every input byte",lambda:require(old_compare.snapshot([run])==before))
        check("synthetic comparison cannot grant real validation",lambda:require(
            report["status"]=="SYNTHETIC_VALIDATION_NOT_A_RENDER_RESULT" and not report["prospective_blender_validation_pass"]))
        check("no default, milestone, or fusion adoption",lambda:require(not any(report[k] for k in
            ("adopted_default","fusion_authorized","full_profile_milestone_pass"))))
        check("zero synthetic actual camera samples",lambda:require(report["acquisition_primary_samples"]==0))
        check("paired cohorts partition the fixed reference",lambda:require(all(
            sum(v["mask_counts"].values())==v["reference_pixels"] for cr in report["runs"][0]["cases"].values() for v in cr["paired"].values())))
        check("candidate artifacts exist for both fixtures",lambda:require(all(
            (root/"smoke"/run.name/name/"stereo_candidate"/"candidate_points_head.ply").is_file() for name in spec.CASES)))
        check("visual and masks exist",lambda:require(all((root/"smoke"/run.name/name/"validation.png").is_file() and
            (root/"smoke"/run.name/name/"evaluation_masks.npz").is_file() for name in spec.CASES)))
        folder=run/"tilted_holdout";c,obs=h.read_observation(folder);want=h.compute_candidate(c,obs)[0]
        truth=folder/"evaluation_only";hidden=folder/"truth_hidden";truth.rename(hidden)
        try:
            with contextlib.redirect_stdout(details):_,_,got,_=evaluation.infer_pair(folder,root/"without-truth")
            check("prediction identical when geometry is inaccessible",lambda:audit.assert_replay(want,got))
        finally:hidden.rename(truth)
        check("comparison refuses to reuse output",lambda:raises((ValueError,FileExistsError),lambda:evaluation.compare([run],root/"smoke","smoke",True)))
        def bad_record():
            copied=root/"bad-spec";shutil.copytree(run,copied)
            j=json.loads((copied/"validation_spec.json").read_text());j["sha256"]="wrong";g.json_write(copied/"validation_spec.json",j)
            evaluation.read_run(copied,True)
        check("altered specification refused",lambda:raises(ValueError,bad_record))
        def bad_seed():
            copied=root/"bad-seed";shutil.copytree(run,copied)
            p=copied/"step_right"/"acquisition.json";j=json.loads(p.read_text());j["seeds_lr"][1]=j["seeds_lr"][0];g.json_write(p,j)
            evaluation.read_run(copied,True)
        check("shared-eye seed rejected",lambda:raises(ValueError,bad_seed))
        # Known perfect geometry verifies that the evaluator can pass, independent
        # of whatever numerical result the analytic stereo happens to obtain.
        c,mesh,(truth,eligible,band,mono)=fixture()
        ideal={"xyz_h":truth["position_h"].copy(),"valid":eligible.copy(),"instance_id":truth["instance_id"].copy()}
        known,_=old_compare.candidate_evaluation(c,ideal,mesh,False,True)
        core,desc=evaluation.occlusion_reference("step_right","small",mono)
        check("known-correct independent geometry passes numerical gates",lambda:require(known["checks_pass"]))
        check("known-correct visibility does not accept hidden surface",lambda:require(evaluation.occlusion_result(ideal["valid"],mono,core,desc)["checks_pass"]))
        check("incomplete full schedule refused before inference",lambda:raises(ValueError,lambda:evaluation.compare([run],root/"bad-schedule","full",True)))
    passed=sum(x["pass"] for x in checks)
    result={"passed":passed,"failed":len(checks)-passed,"checks":checks,"seconds":time.perf_counter()-start,
            "blender_executed":False,"spec_sha256":spec.spec_digest(),"synthetic_smoke_reports":summaries,
            "detail_log":details.getvalue()}
    print(f"[fsg-validation-check] SUMMARY passed={passed} failed={result['failed']} seconds={result['seconds']:.3f} blender_executed=False")
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    mode=ap.add_mutually_exclusive_group(required=True);mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--negative",choices=("visibility","leakage","geometry"));ap.add_argument("--report",type=Path)
    args=ap.parse_args()
    if args.negative:
        {"visibility":negative_visibility,"leakage":negative_leakage,"geometry":negative_geometry}[args.negative]()
        raise AssertionError("negative control unexpectedly passed")
    result=self_test()
    if args.report:g.json_write(args.report,result)
    raise SystemExit(bool(result["failed"]))

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print(f"[fsg-validation-check] FAIL {type(exc).__name__}: {exc}",file=sys.stderr);raise SystemExit(1)
