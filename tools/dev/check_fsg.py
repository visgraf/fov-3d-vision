"""FSG1 software checks and deliberate negatives. No pytest, Blender, or assets needed.

    python tools/dev/check_fsg.py --self-test
    python tools/dev/check_fsg.py --self-test --repo-check
    python tools/dev/check_fsg.py --negative baseline  # MUST exit 1
    python tools/dev/check_fsg.py --negative crop      # MUST exit 1

The synthetic backend exercises fsg_render.acquire, not BlenderBackend's bpy API.
Passing these checks is NOT a Blender accuracy measurement.
"""
from __future__ import annotations
import argparse
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import time

import cv2
import numpy as np

TOOLS=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TOOLS)); sys.path.insert(0,str(TOOLS/"dev"))
import fsg_geometry as g
import fsg_scene as scene
import fsg_render as render
import fsg_stereo as stereo
import fsg_evaluate as evaluate
from fake_blender_fsg import SyntheticBackend


def exact_geometry(control: str | None=None) -> tuple[bool,str]:
    worst=0.
    rng=np.random.default_rng(9001)
    for yaw,pitch in ((0,0),(14,-7),(-24,11)):
        c=g.make_calibration("small",yaw,pitch); r=stereo.rectification(c)
        uv=rng.uniform([100,100],[220,220],(60,2))
        xyz=np.asarray(c["eyes"][0]["centre_h_m"])+g.rays_h(c["eyes"][0],uv)*rng.uniform(1.,4.,(60,1))
        rect=[]
        for k,side in enumerate(("L","R")):
            e=c["eyes"][k]; p,_=g.project_h(e,xyz)
            rect.append(cv2.undistortPoints(p.reshape(-1,1,2),np.array(e["K"]),np.zeros(5),
                                           R=r["R1" if k==0 else "R2"],P=r["P1" if k==0 else "P2"]).reshape(-1,2))
        if np.max(np.abs(rect[0][:,1]-rect[1][:,1]))>1e-8: return False,"epipolar rows differ"
        left_xy=(29,17); right_xy=(43,17)
        lp=rect[0]-left_xy; rp=rect[1]-right_xy
        q=g.crop_q(r["Q_full"],left_xy,right_xy)
        if control=="baseline":
            q=q.copy(); q[3,:]/=1.2
        elif control=="crop":
            q=r["Q_full"]  # intentionally forget all crop offsets
        out=g.rect_to_head(c,r["R1"],g.reproject_q(q,lp,lp[:,0]-rp[:,0]))
        worst=max(worst,float(np.max(np.linalg.norm(out-xyz,axis=-1))))
    return worst<1e-7,f"max known-point 3D error={worst:.9g} m; limit=1e-7 m"


def assert_raises(cls,fn):
    try: fn()
    except cls: return
    raise AssertionError(f"expected {cls.__name__}")


def check_repo_rig_only():
    # Import rig, not bl_common: the latter belongs to Blender's interpreter.
    import rig
    for yaw,pitch in ((0,0),(14,-7),(-24,11)):
        c=g.make_calibration("small",yaw,pitch)
        h=np.array(c["head_R_wh"]); o=np.array(c["head_origin_w_m"])
        target=g.head_to_world(c,g.gaze_direction(yaw,pitch)*2.)
        pair=rig.pair_for_point(target,o,h,c["ipd_m"])
        for k,e in enumerate(c["eyes"]):
            p=pair["eyes"][k]
            pos,rb=rig.camera_pose(o,h,rig.eye_offsets_local(c["ipd_m"])[k],p["yaw"],p["pitch"])
            assert np.allclose(g.world_to_head(c,pos),e["centre_h_m"],atol=1e-9)
            assert np.allclose(h.T@rb@g.CV_TO_BLENDER,e["R_hc"],atol=1e-9)


def self_test(with_repo: bool=False) -> dict:
    results=[]; t0=time.perf_counter(); detail=io.StringIO()
    def check(name,fn):
        try:
            fn(); results.append({"name":name,"pass":True})
            print("[fsg-check] PASS",name)
        except Exception as e:
            results.append({"name":name,"pass":False,"error":f"{type(e).__name__}: {e}"})
            print("[fsg-check] FAIL",name,repr(e))
    def require(a,message="assertion"):
        if not a: raise AssertionError(message)
    check("NumPy head/camera geometry",lambda:require(not g.self_test(),str(g.self_test())))
    check("known triangle first-hit depths and IDs",lambda:require(not scene.self_test(),str(scene.self_test())))
    check("OpenCV off-axis vergence, rectification, unequal crops, metric triangulation",lambda:require(*exact_geometry()))
    check("wrong baseline makes geometry check fail",lambda:require(not exact_geometry("baseline")[0]))
    check("forgotten crop offset makes geometry check fail",lambda:require(not exact_geometry("crop")[0]))
    check("zero baseline rejected",lambda:assert_raises(ValueError,lambda:g.make_calibration("small",ipd=0)))
    check("unequal vertical crops rejected",lambda:assert_raises(ValueError,lambda:g.crop_q(np.eye(4),(1,2),(3,4))))
    bad=g.make_calibration("small"); bad["eyes"][0]["R_hc"][0][0]*=1.1
    check("non-rigid camera rejected",lambda:assert_raises(ValueError,lambda:g.validate_calibration(bad)))
    empty={"reference_pixels":1000,"accepted_pixels":0,"coverage":0.,
           "median_relative_range_error":None,"p95_relative_range_error":None}
    check("empty reconstruction fails scientific gate",lambda:require(bool(evaluate.gate(empty))))
    failed={"reference_pixels":1000,"coverage":.99,"median_relative_range_error":.2,"p95_relative_range_error":.2}
    check("large metric error fails scientific gate",lambda:require(bool(evaluate.gate(failed))))
    if with_repo: check("current repository rig integration",check_repo_rig_only)
    with tempfile.TemporaryDirectory(prefix="fsg1-tests-") as temp:
        root=Path(temp)
        args=render.parse_args(["--out",str(root/"run"),"--profile","small"]); args.spp=64
        with contextlib.redirect_stdout(detail):
            render.acquire(args,SyntheticBackend())
            for case in scene.CASES: stereo.process_pair(root/"run"/case)
            evaluation=evaluate.evaluate_run(root/"run",allow_synthetic=True)
        check("full file orchestration and all three synthetic fixture gates",lambda:require(evaluation["checks_pass"],str(evaluation["fails"])))
        check("synthetic result never approves full milestone",lambda:require(not evaluation["full_profile_milestone_pass"]))
        with contextlib.redirect_stdout(detail):
            rejected=evaluate.evaluate_run(root/"run",allow_synthetic=False)
        check("production gate rejects synthetic provenance",lambda:require(not rejected["checks_pass"] and any("not a Blender" in f for f in rejected["fails"])))
        one=root/"run"/"fronto"
        c=json.loads((one/"calibration.json").read_text())
        obs=dict(np.load(one/"observation.npz",allow_pickle=False))
        stored=dict(np.load(one/"stereo"/"result.npz",allow_pickle=False))
        check("valid points finite and in front of cameras",lambda:require(
            np.isfinite(stored["xyz_h"][stored["valid"]]).all() and np.all(stored["z_rect_m"][stored["valid"]]>0)))
        def range_not_z():
            m=stored["valid"]
            distances=np.linalg.norm(stored["xyz_h"]-np.array(c["eyes"][0]["centre_h_m"]),axis=-1)
            require(np.allclose(distances[m],stored["range_left_m"][m],atol=1e-6))
            require(float(np.max(np.abs(distances[m]-stored["z_rect_m"][m])))>.01)
        check("ray range is not rectified axial Z",range_not_z)
        def truth_removed():
            for case in scene.CASES:
                d=root/"run"/case
                (d/"evaluation_only").rename(d/"truth_temporarily_absent")
                try:
                    with contextlib.redirect_stdout(detail): stereo.process_pair(d,d/"replayed_without_truth")
                    a=dict(np.load(d/"stereo"/"result.npz",allow_pickle=False))
                    b=dict(np.load(d/"replayed_without_truth"/"result.npz",allow_pickle=False))
                    require(a.keys()==b.keys())
                    for key in a: require(np.array_equal(a[key],b[key],equal_nan=True),f"changed {case}/{key}")
                finally:
                    (d/"truth_temporarily_absent").rename(d/"evaluation_only")
        check("removing truth gives identical reconstruction arrays for all cases",truth_removed)
        extra=dict(obs,depth=np.zeros((320,320)))
        check("depth accidentally added to sensor input rejected",lambda:assert_raises(ValueError,lambda:stereo.compute(c,extra)))
        blank={k:v.copy() for k,v in obs.items()}; blank["rgb_L"][:]=.4; blank["rgb_R"][:]=.4
        b,_=stereo.compute(c,blank)
        check("blank binocular images cannot yield accepted geometry",lambda:require(not np.any(b["valid"])))
        # Inject a depth-scale fault into the saved prediction, not the evaluator.
        result_path=one/"stereo"/"result.npz"
        corrupted={k:v.copy() for k,v in stored.items()}
        centre=np.asarray(c["eyes"][0]["centre_h_m"])
        corrupted["xyz_h"]=(centre+1.2*(corrupted["xyz_h"]-centre)).astype(np.float32)
        np.savez_compressed(result_path,**corrupted)
        bad_eval=evaluate.evaluate_pair(one,allow_synthetic=True,write=False)
        np.savez_compressed(result_path,**stored)
        check("20-percent 3D scale corruption fails actual saved-record evaluator",lambda:require(not bad_eval["checks_pass"]))
        original=(one/"calibration.json").read_text()
        (one/"calibration.json").write_text(original+" ")
        check("stale calibration/observation fingerprints rejected",lambda:assert_raises(ValueError,lambda:evaluate.evaluate_pair(one,True,False)))
        (one/"calibration.json").write_text(original)
        check("acquisition refuses nonempty output",lambda:assert_raises(FileExistsError,lambda:render.acquire(args,SyntheticBackend())))
        class Broken(SyntheticBackend):
            def render_eye(self,*a,**kw): raise RuntimeError("intentional backend fault")
        args.out=str(root/"broken")
        check("backend failure propagates",lambda:assert_raises(RuntimeError,lambda:render.acquire(args,Broken())))
        check("failed acquisition never writes a completion marker",lambda:require(not (root/"broken"/"run.json").exists()))
    summary={"schema":"FSG1-software-checks-v1","checks":results,"passed":sum(x["pass"] for x in results),
             "failed":sum(not x["pass"] for x in results),"seconds":time.perf_counter()-t0,
             "python":sys.version,"numpy":np.__version__,"opencv":cv2.__version__,
             "repository_rig_test_requested":with_repo,"blender_executed":False,
             "fixture_log":detail.getvalue()}
    print(f"[fsg-check] SUMMARY passed={summary['passed']} failed={summary['failed']} "
          f"seconds={summary['seconds']:.3f} blender_executed=False")
    return summary


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test",action="store_true"); ap.add_argument("--repo-check",action="store_true")
    ap.add_argument("--negative",choices=("baseline","crop")); ap.add_argument("--report",type=Path)
    a=ap.parse_args()
    if a.negative:
        ok,msg=exact_geometry(a.negative)
        print(f"[fsg-check] {'PASS' if ok else 'FAIL'} deliberate {a.negative} mutation: {msg}")
        raise SystemExit(0 if ok else 1)
    if not a.self_test: ap.error("choose --self-test or --negative")
    r=self_test(a.repo_check)
    if a.report: g.json_write(a.report,r)
    raise SystemExit(1 if r["failed"] else 0)


if __name__=="__main__": main()
