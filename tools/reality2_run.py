"""Continue an exact saved Reality Check 1 record until FSG6f says no_frontier.

The first six fixations are never rerendered.  Their saved map, observation
history, policy trace and gaze history are loaded as the initial state.  Only
post-six views are newly acquired.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path
import numpy as np
from PIL import Image

import reality2_public as public
import reality1_public as parent_public
import fsg6f_frontier as policy
import fsg6f_run as fsg6run
from fsg3_surface_map import load_map, fuse, save_map
import fsg_stereo_hdr as hdr
from fsg_stereo_supported import compute_once, check_kernel_equivalence
from fsg_geometry import json_write
from fsg_stereo import support_mask
from reality1_run import _tone_preview


def _sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()


def _load_parent_history(parent:Path, manifest:dict, gazes:list[tuple[float,float]])->list[dict]:
    hist=[]
    for step,_g in enumerate(gazes):
        acq=parent/"acquisitions"/f"fix_{step:02d}"/f"fix_{step:02d}"
        c=json.loads((acq/"calibration.json").read_text())
        with np.load(parent/"patches"/f"fix_{step:02d}.npz",allow_pickle=False) as z:
            hist.append({"calibration":c,
                         "instance_L":z["oracle_instance_id"].copy(),
                         "raw_support_L":z["raw_support_L"].copy(),
                         "instance_R":z["oracle_instance_id_R"].copy(),
                         "raw_support_R":z["raw_support_R"].copy()})
    return hist


def _validate_parent(parent:Path)->tuple[dict,list[dict],list[tuple[float,float]]]:
    m=json.loads((parent/"prediction_manifest.json").read_text())
    if m.get("public_spec_sha256")!=parent_public.public_digest():
        raise AssertionError("parent is not the current Reality Check 1 public record")
    if m.get("truth_opened") is not False or not m.get("fixed_head") or not m.get("static_scene"):
        raise AssertionError("parent Reality Check 1 integrity contract broken")
    if m.get("instrument")!=public.INSTRUMENT_ID or m.get("frozen_object_policy")!=public.FROZEN_POLICY_ID:
        raise AssertionError("parent instrument/policy differs from Reality Check 2")
    if m.get("termination_reason")!="max_fixations":
        raise AssertionError("Reality Check 2 requires a parent interrupted only by the six-look limit")
    gazes=[tuple(map(float,g)) for g in m.get("fixation_gazes_deg",[])]
    if len(gazes)!=public.PARENT_FIXATIONS:
        raise AssertionError("parent does not contain exactly the six Reality Check 1 looks")
    if len({(round(a,9),round(b,9)) for a,b in gazes})!=len(gazes):
        raise AssertionError("parent contains a repeated gaze")
    trace=json.loads((parent/"policy_trace.json").read_text())["trace"]
    if len(trace)!=len(gazes) or trace[-1].get("stop"):
        raise AssertionError("parent final policy state is not a live CONTINUE decision")
    if "next_gaze_deg" not in trace[-1]:
        raise AssertionError("parent final decision lacks continuation gaze")
    return m,trace,gazes


def run_blender(args,step:int,gaze:tuple[float,float],acq_root:Path):
    yaw,pitch=gaze; out=acq_root/f"fix_{step:02d}"
    cmd=[args.blender,"-b","--python-exit-code","1","-P","tools/reality2_render_fix.py","--",
         "--out",str(out),"--profile",args.profile,"--seed",str(args.seed),"--step",str(step),
         "--yaw",f"{yaw:.12g}","--pitch",f"{pitch:.12g}","--device",args.device]
    if args.save_blend: cmd.append("--save-blend")
    p=subprocess.run(cmd,cwd=args.repo,text=True,capture_output=True)
    log=args.out/"logs"/f"render_{step:02d}.log"; log.write_text(p.stdout+"\n--- STDERR ---\n"+p.stderr)
    if p.returncode!=0: raise RuntimeError(f"Blender fixation {step} failed; see {log}")
    rr=json.loads((out/"run.json").read_text()); case=out/f"fix_{step:02d}"
    if not rr.get("complete") or rr.get("fixture")!=public.FIXTURE or int(rr.get("seed"))!=args.seed:
        raise RuntimeError("incomplete or wrong Reality Check 2 Blender record")
    if abs(float(rr["yaw_deg"])-yaw)>1e-8 or abs(float(rr["pitch_deg"])-pitch)>1e-8:
        raise RuntimeError("Blender record gaze mismatch")
    return case,rr


def execute(args)->dict:
    args.repo=Path(args.repo).resolve(); args.parent=Path(args.parent).resolve(); args.out=Path(args.out).resolve()
    if args.out.exists(): raise FileExistsError("output must be new")
    if not args.parent.exists(): raise FileNotFoundError(args.parent)
    args.out.mkdir(parents=True)
    for d in ("logs","acquisitions","patches","maps","rgb"):
        (args.out/d).mkdir()
    check_kernel_equivalence()
    if public.FUSION != parent_public.FUSION:
        raise AssertionError("Reality Check 2 changed fusion")
    pm, parent_trace, gazes = _validate_parent(args.parent)
    args.seed=int(pm["seed"]); args.profile=str(pm["profile"])
    if args.seed not in public.SEEDS:
        raise AssertionError("parent seed outside Reality Check 2 schedule")

    # Carry exact saved state forward.  No parent view is rerendered.
    observation_history=_load_parent_history(args.parent,pm,gazes)
    sm=load_map(args.parent/"surface_map.npz")
    patch_stats=[dict(x) for x in pm["patch_stats"]]
    assoc_stats=[dict(x) for x in pm["association_stats"]]
    policy_trace=[dict(x) for x in parent_trace]
    snapshots=[]; supports=[]
    for step in range(public.PARENT_FIXATIONS):
        src=args.parent/"maps"/f"map_{step:02d}.npz"; dst=args.out/"maps"/f"map_{step:02d}.npz"
        shutil.copy2(src,dst)
        mm=load_map(src); snapshots.append(mm.xyz_h.copy()); supports.append(mm.support_count.copy())

    gaze=tuple(float(x) for x in parent_trace[-1]["next_gaze_deg"])
    if any(np.allclose(g,gaze,atol=1e-9) for g in gazes):
        raise AssertionError("parent continuation decision revisits an existing fixation")
    termination=None; new_samples=0; new_render_seconds=0.0; t0=time.perf_counter()

    while len(gazes) < public.WATCHDOG_TOTAL_FIXATIONS:
        step=len(gazes)
        if any(np.allclose(g,gaze,atol=1e-9) for g in gazes):
            raise AssertionError("policy revisited an existing fixation")
        case,rr=run_blender(args,step,gaze,args.out/"acquisitions")
        new_samples+=int(rr["primary_camera_samples"]); new_render_seconds+=float(rr["total_wall_seconds"])
        c,obs=hdr.read_observation(case); rec,meta,state=compute_once(c,obs)
        pid=f"fix_{step:02d}"; p=fsg6run.patch_from_record(pid,rec)
        nref,nvalid,cov=fsg6run.object_measurement_stats(rec)
        x,y,cw,ch=map(int,rec["crop_xywh"]); sl=np.s_[y:y+ch,x:x+cw]
        ids_R=state["ids_right"][sl]; raw_support_R=support_mask(c,rec,"R")[sl]
        if not np.array_equal(rec["instance_id"],state["ids_left"][sl]):
            raise AssertionError("left rectified ID replay mismatch")
        np.savez_compressed(args.out/"patches"/f"{pid}.npz",xyz_h=p.xyz_h.astype(np.float32),
                            rgb=p.rgb.astype(np.float32),instance_id=p.instance_id,valid=rec["valid"],
                            oracle_instance_id=rec["instance_id"],raw_support_L=rec["raw_support_L"],
                            oracle_instance_id_R=ids_R,raw_support_R=raw_support_R)
        fsg6run.write_patch_visual(args.out/"patches"/f"{pid}_mask.png",rec)
        Image.fromarray(_tone_preview(rec["rgb_left"])).save(args.out/"rgb"/f"{pid}_left.png")
        if len(p.xyz_h)<100:
            raise ValueError("Reality Check 2 fixation has too few target points")
        sm,assoc=fuse(sm,p,public.OBJECT_ID,public.FUSION["association_radius_m"],public.FUSION["hash_cell_m"])
        replay,dup=fuse(sm,p,public.OBJECT_ID,public.FUSION["association_radius_m"],public.FUSION["hash_cell_m"])
        idempotent=bool(dup["duplicate_patch"] and np.array_equal(sm.xyz_h,replay.xyz_h)
                        and np.array_equal(sm.support_count,replay.support_count)
                        and np.array_equal(sm.provenance_mask,replay.provenance_mask))
        if not idempotent: raise AssertionError("patch replay is not idempotent")
        save_map(args.out/"maps"/f"map_{step:02d}.npz",sm)
        snapshots.append(sm.xyz_h.copy()); supports.append(sm.support_count.copy()); gazes.append(gaze)
        dist=assoc["distances_m"]
        assoc_stats.append({"step":step,"patch_id":pid,"input_points":int(assoc["input_points"]),
                            "matched":int(assoc["matched"]),"new":int(assoc["new"]),
                            "affected_surfels":int(assoc["affected_surfels"]),
                            "new_fraction":float(assoc["new"]/max(1,assoc["input_points"])),
                            "overlap_median_distance_m":float(np.median(dist)) if len(dist) else None,
                            "overlap_p95_distance_m":float(np.percentile(dist,95)) if len(dist) else None,
                            "idempotent_replay":idempotent})
        patch_stats.append({"step":step,"patch_id":pid,"yaw_deg":gaze[0],"pitch_deg":gaze[1],
                            "object_reference_count":nref,"object_valid_count":nvalid,
                            "object_measurement_fraction":cov,"point_count":len(p.xyz_h),
                            "instrument":public.INSTRUMENT_ID})
        observation_history.append({"calibration":c,"instance_L":rec["instance_id"].copy(),
                                    "raw_support_L":rec["raw_support_L"].copy(),
                                    "instance_R":ids_R.copy(),"raw_support_R":raw_support_R.copy()})
        decision=policy.choose_next(gaze[0],gaze[1],c,rec["instance_id"],rec["raw_support_L"],
                                    ids_R,raw_support_R,sm.xyz_h,gazes,observation_history)
        decision["step"]=step; policy_trace.append(decision)
        if decision["stop"]:
            termination=decision["reason"]; break
        gaze=tuple(float(x) for x in decision["next_gaze_deg"])

    if termination is None:
        termination="watchdog_max_fixations"
    save_map(args.out/"surface_map.npz",sm); fsg6run.save_ply(args.out/"surface_map.ply",sm)
    fsg6run.write_growth(args.out/"growth.png",snapshots,supports,gazes)
    json_write(args.out/"policy_trace.json",{"policy":"frozen_fsg6f_reality1_exact_continuation","trace":policy_trace})
    parent_hashes={name:_sha256(args.parent/name) for name in ("prediction_manifest.json","policy_trace.json","surface_map.npz")}
    manifest={"schema":"RealityCheck2-prediction-v1","instrument":public.INSTRUMENT_ID,
              "frozen_object_policy":public.FROZEN_POLICY_ID,"public_spec_sha256":public.public_digest(),
              "parent_reality1_public_spec_sha256":parent_public.public_digest(),
              "parent_record":str(args.parent),"parent_hashes":parent_hashes,
              "continued_from_parent_without_rerender":True,"parent_fixation_count":public.PARENT_FIXATIONS,
              "watchdog_total_fixations":public.WATCHDOG_TOTAL_FIXATIONS,
              "scientific_stopping_rule":"frozen FSG6f no_frontier",
              "profile":args.profile,"fixture":public.FIXTURE,"seed":args.seed,
              "fixation_gazes_deg":[list(g) for g in gazes],"termination_reason":termination,
              "patch_stats":patch_stats,"association_stats":assoc_stats,"truth_opened":False,
              "fixed_head":True,"static_scene":True,
              "policy_inputs":["persistent map xyz_h","current rectified oracle target mask L/R",
                               "raw calibration support L/R","calibration","fixation history",
                               "completed binocular oracle/support history"],
              "parent_primary_camera_samples":int(pm["primary_camera_samples"]),
              "continuation_primary_camera_samples":int(new_samples),
              "primary_camera_samples":int(pm["primary_camera_samples"])+int(new_samples),
              "continuation_blender_recorded_wall_seconds":new_render_seconds,
              "continuation_loop_wall_seconds":time.perf_counter()-t0}
    json_write(args.out/"prediction_manifest.json",manifest)
    print("[reality2-run] COMPLETE",json.dumps({"seed":args.seed,"total_fixations":len(gazes),
          "new_fixations":len(gazes)-public.PARENT_FIXATIONS,"gazes":gazes,
          "termination":termination,"new_samples":new_samples},sort_keys=True),flush=True)
    return manifest


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo",default="."); ap.add_argument("--parent",required=True); ap.add_argument("--out",required=True)
    ap.add_argument("--device",choices=("OPTIX","CUDA","CPU"),default="OPTIX")
    ap.add_argument("--blender",default="blender"); ap.add_argument("--save-blend",action="store_true")
    execute(ap.parse_args())

if __name__=="__main__": main()
