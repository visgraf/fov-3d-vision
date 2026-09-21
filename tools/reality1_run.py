"""Run Reality Check 1 with the frozen FSG6f active object policy."""
from __future__ import annotations
import argparse
import json
import subprocess
import time
from pathlib import Path
import numpy as np
from PIL import Image

import reality1_public as public
import fsg6f_frontier as policy
import fsg6f_public as frozen_public
import fsg6f_run as fsg6run
from fsg3_surface_map import initialize, fuse, save_map
import fsg_stereo_hdr as hdr
from fsg_stereo_supported import compute_once, check_kernel_equivalence
from fsg_geometry import json_write
from fsg_stereo import support_mask


def _tone_preview(rgb: np.ndarray) -> np.ndarray:
    a=np.maximum(np.asarray(rgb,float),0.0)
    a=a/(1.0+a)
    a=np.where(a<=0.0031308,12.92*a,1.055*np.power(a,1/2.4)-0.055)
    return np.clip(np.rint(a*255),0,255).astype(np.uint8)


def run_blender(args,step:int,gaze:tuple[float,float],acq_root:Path):
    yaw,pitch=gaze; out=acq_root/f"fix_{step:02d}"
    cmd=[args.blender,"-b","--python-exit-code","1","-P","tools/reality1_render_fix.py","--",
         "--out",str(out),"--profile",args.profile,"--seed",str(args.seed),"--step",str(step),
         "--yaw",f"{yaw:.12g}","--pitch",f"{pitch:.12g}","--device",args.device]
    if args.save_blend: cmd.append("--save-blend")
    p=subprocess.run(cmd,cwd=args.repo,text=True,capture_output=True)
    log=args.out/"logs"/f"render_{step:02d}.log"; log.write_text(p.stdout+"\n--- STDERR ---\n"+p.stderr)
    if p.returncode!=0: raise RuntimeError(f"Blender fixation {step} failed; see {log}")
    rr=json.loads((out/"run.json").read_text()); case=out/f"fix_{step:02d}"
    if not rr.get("complete") or rr.get("fixture")!=public.FIXTURE or int(rr.get("seed"))!=args.seed:
        raise RuntimeError("incomplete or wrong Reality Check 1 Blender record")
    if abs(float(rr["yaw_deg"])-yaw)>1e-8 or abs(float(rr["pitch_deg"])-pitch)>1e-8:
        raise RuntimeError("Blender record gaze mismatch")
    return case,rr


def execute(args)->dict:
    args.repo=Path(args.repo).resolve(); args.out=Path(args.out).resolve()
    if args.out.exists(): raise FileExistsError("output must be new")
    args.out.mkdir(parents=True)
    for d in ("logs","acquisitions","patches","maps","rgb"):
        (args.out/d).mkdir()
    check_kernel_equivalence()
    if public.FUSION != frozen_public.FUSION or public.MAX_FIXATIONS != frozen_public.MAX_BUDGET_FIXATIONS:
        raise AssertionError("Reality Check 1 must preserve FSG6f fusion and fixation budget")
    gazes=[]; patch_stats=[]; assoc_stats=[]; policy_trace=[]; observation_history=[]
    samples=0; render_seconds=0.0; snapshots=[]; supports=[]; sm=None
    gaze=tuple(float(x) for x in public.SEED_GAZE_DEG); termination=None; t0=time.perf_counter()
    for step in range(public.MAX_FIXATIONS):
        if any(np.allclose(g,gaze,atol=1e-9) for g in gazes):
            raise AssertionError("policy revisited an existing fixation")
        case,rr=run_blender(args,step,gaze,args.out/"acquisitions")
        samples+=int(rr["primary_camera_samples"]); render_seconds+=float(rr["total_wall_seconds"])
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
            raise ValueError("Reality Check 1 fixation has too few target points")
        if sm is None:
            sm=initialize(p,public.OBJECT_ID)
            assoc={"duplicate_patch":False,"matched":0,"new":len(p.xyz_h),"affected_surfels":0,
                   "distances_m":np.empty(0),"input_points":len(p.xyz_h),"base_points":0}
            idempotent=True
        else:
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
    if termination is None: termination="max_fixations"
    save_map(args.out/"surface_map.npz",sm); fsg6run.save_ply(args.out/"surface_map.ply",sm)
    fsg6run.write_growth(args.out/"growth.png",snapshots,supports,gazes)
    json_write(args.out/"policy_trace.json",{"policy":"frozen_fsg6f_on_reality_check_1","trace":policy_trace})
    manifest={"schema":"RealityCheck1-prediction-v1","instrument":public.INSTRUMENT_ID,
              "frozen_object_policy":public.FROZEN_POLICY_ID,"public_spec_sha256":public.public_digest(),
              "profile":args.profile,"fixture":public.FIXTURE,"seed":args.seed,
              "fixation_gazes_deg":[list(g) for g in gazes],"termination_reason":termination,
              "patch_stats":patch_stats,"association_stats":assoc_stats,"truth_opened":False,
              "fixed_head":True,"static_scene":True,
              "policy_inputs":["persistent map xyz_h","current rectified oracle target mask L/R",
                               "raw calibration support L/R","calibration","fixation history",
                               "completed binocular oracle/support history"],
              "primary_camera_samples":samples,"blender_recorded_wall_seconds":render_seconds,
              "loop_wall_seconds":time.perf_counter()-t0}
    json_write(args.out/"prediction_manifest.json",manifest)
    print("[reality1-run] COMPLETE",json.dumps({"seed":args.seed,"fixations":len(gazes),
          "gazes":gazes,"termination":termination,"samples":samples},sort_keys=True),flush=True)
    return manifest


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo",default="."); ap.add_argument("--out",required=True)
    ap.add_argument("--profile",choices=("small","full"),required=True)
    ap.add_argument("--seed",type=int,choices=public.SEEDS,required=True)
    ap.add_argument("--device",choices=("OPTIX","CUDA","CPU"),default="OPTIX")
    ap.add_argument("--blender",default="blender"); ap.add_argument("--save-blend",action="store_true")
    execute(ap.parse_args())

if __name__=="__main__": main()
