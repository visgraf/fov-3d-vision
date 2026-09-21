"""Run one Scene-1c prospective single-object certification control.

The complete three-object fixture is rendered, but only one nominated object is
reconstructed and controlled.  The frozen FSG6f controller acts alone for at
most six target looks.  These controls certify component solvability before the
multi-object ensemble is allowed to run; they are not policy training data.
"""
from __future__ import annotations
import argparse, json, subprocess, time
from pathlib import Path
import numpy as np
from PIL import Image
import scene1c_public as public
import scene1c_policy as policy
import fsg6f_public as frozen_public
from fsg3_surface_map import Patch, initialize, fuse, save_map
import fsg_stereo_hdr as hdr
from fsg_stereo_supported import compute_once, check_kernel_equivalence
from fsg_stereo import support_mask
from fsg_geometry import json_write


def patch_for_object(pid:str, rec:dict, object_id:int)->Patch:
    m=rec["valid"]&(rec["instance_id"]==int(object_id))
    return Patch(pid,rec["xyz_h"][m],rec["rgb_left"][m],rec["instance_id"][m])


def measurement_stats(rec:dict,object_id:int)->tuple[int,int,float|None]:
    ref=(rec["instance_id"]==int(object_id))&rec["raw_support_L"]
    nref=int(ref.sum()); nvalid=int((rec["valid"]&ref).sum())
    return nref,nvalid,(float(nvalid/nref) if nref else None)


def raw_observation(c,rec,ids_R,raw_support_R)->dict:
    return {"calibration":c,"instance_L":rec["instance_id"].copy(),"raw_support_L":rec["raw_support_L"].copy(),
            "instance_R":ids_R.copy(),"raw_support_R":raw_support_R.copy()}


def write_patch_visual(path:Path,rec:dict,target_object:int)->None:
    obj=(rec["instance_id"]==int(target_object))&rec["raw_support_L"]; valid=rec["valid"]&obj
    im=np.zeros((*obj.shape,3),np.uint8); im[obj]=(120,120,120); im[valid]=(255,255,255); Image.fromarray(im).save(path)


def run_blender(args,step:int,gaze:tuple[float,float],root:Path):
    yaw,pitch=gaze; out=root/f"fix_{step:02d}"
    cmd=[args.blender,"-b","--python-exit-code","1","-P","tools/scene1c_render_fix.py","--","--out",str(out),
         "--profile",args.profile,"--fixture",args.fixture,"--seed",str(args.seed),"--step",str(step),
         "--target-object",str(args.object_id),"--yaw",f"{yaw:.12g}","--pitch",f"{pitch:.12g}","--device",args.device]
    if args.save_blend: cmd.append("--save-blend")
    p=subprocess.run(cmd,cwd=args.repo,text=True,capture_output=True)
    log=args.out/"logs"/f"render_{step:02d}.log"; log.write_text(p.stdout+"\n--- STDERR ---\n"+p.stderr)
    if p.returncode!=0: raise RuntimeError(f"Blender fixation {step} failed; see {log}")
    rr=json.loads((out/"run.json").read_text()); case=out/f"fix_{step:02d}"
    if not rr.get("complete") or rr.get("fixture")!=args.fixture or int(rr.get("seed"))!=args.seed or int(rr.get("target_object_id"))!=args.object_id or abs(float(rr["yaw_deg"])-yaw)>1e-8 or abs(float(rr["pitch_deg"])-pitch)>1e-8:
        raise RuntimeError("incomplete or wrong Scene-1c component acquisition")
    return case,rr


def execute(args)->dict:
    args.repo=Path(args.repo).resolve(); args.out=Path(args.out).resolve()
    if args.out.exists(): raise FileExistsError("output must be new")
    args.out.mkdir(parents=True); [(args.out/d).mkdir() for d in ("logs","acquisitions","patches","maps")]
    check_kernel_equivalence()
    if public.FUSION!=frozen_public.FUSION: raise AssertionError("Scene-1c must preserve frozen FSG6f/FSG3 fusion")
    if public.FROZEN_OBJECT_POLICY_ID!=frozen_public.SPEC_ID: raise AssertionError("Scene-1c must use frozen FSG6f object controller")
    if args.fixture not in public.FIXTURES or args.seed not in public.SEEDS or args.object_id not in public.OBJECT_IDS:
        raise ValueError("component outside Scene-1c schedule")

    oid=int(args.object_id); gaze=public.seed_gaze_for_object(args.fixture,oid)
    surf=None; history=[]; gazes=[]; patch_stats=[]; assoc_stats=[]; trace=[]
    samples=0; render_seconds=0.0; termination=None; last_obs=None; autonomous_count=0; t0=time.perf_counter()

    for step in range(public.PER_OBJECT_MAX_FIXATIONS):
        if policy.is_global_repeat(gaze,gazes): raise AssertionError("component controller revisited a physical fixation")
        case,rr=run_blender(args,step,gaze,args.out/"acquisitions"); samples+=int(rr["primary_camera_samples"]); render_seconds+=float(rr["total_wall_seconds"])
        c,obs=hdr.read_observation(case); rec,meta,state=compute_once(c,obs); x,y,cw,ch=map(int,rec["crop_xywh"]); sl=np.s_[y:y+ch,x:x+cw]
        ids_R=state["ids_right"][sl]; raw_support_R=support_mask(c,rec,"R")[sl]
        if not np.array_equal(rec["instance_id"],state["ids_left"][sl]): raise AssertionError("left rectified ID replay mismatch")
        robs=raw_observation(c,rec,ids_R,raw_support_R); history.append(robs); last_obs=robs; gazes.append(tuple(float(v) for v in gaze))
        p=patch_for_object(f"fix_{step:02d}_obj_{oid}",rec,oid); nref,nvalid,cov=measurement_stats(rec,oid)
        if len(p.xyz_h)<100: raise ValueError(f"component target object {oid} has too few reconstructed points")
        if surf is None:
            surf=initialize(p,oid); assoc={"duplicate_patch":False,"matched":0,"new":len(p.xyz_h),"affected_surfels":0,"distances_m":np.empty(0),"input_points":len(p.xyz_h),"base_points":0}
        else:
            surf,assoc=fuse(surf,p,oid,public.FUSION["association_radius_m"],public.FUSION["hash_cell_m"])
            replay,dup=fuse(surf,p,oid,public.FUSION["association_radius_m"],public.FUSION["hash_cell_m"])
            idem=bool(dup["duplicate_patch"] and np.array_equal(surf.xyz_h,replay.xyz_h) and np.array_equal(surf.support_count,replay.support_count) and np.array_equal(surf.provenance_mask,replay.provenance_mask))
            if not idem: raise AssertionError("component patch replay is not idempotent")
        idem=True if step==0 else idem
        save_map(args.out/"maps"/f"map_{step:02d}.npz",surf)
        np.savez_compressed(args.out/"patches"/f"fix_{step:02d}.npz",valid=rec["valid"],oracle_instance_id=rec["instance_id"],raw_support_L=rec["raw_support_L"],oracle_instance_id_R=ids_R,raw_support_R=raw_support_R)
        write_patch_visual(args.out/"patches"/f"fix_{step:02d}_target_mask.png",rec,oid)
        dist=assoc["distances_m"]
        row={"step":step,"object_id":oid,"phase":"prescribed_seed" if step==0 else "autonomous","object_reference_count":nref,"object_valid_count":nvalid,"object_measurement_fraction":cov,"point_count":int(len(p.xyz_h)),"idempotent_replay":idem,
             "matched":int(assoc["matched"]),"new":int(assoc["new"]),"input_points":int(assoc["input_points"]),"overlap_median_distance_m":float(np.median(dist)) if len(dist) else None,"overlap_p95_distance_m":float(np.percentile(dist,95)) if len(dist) else None}
        patch_stats.append(row); assoc_stats.append(row)

        state_obj={"object_id":oid,"map":surf,"observation_history":history,"last_target_observation":last_obs,
                   "last_target_gaze_deg":gazes[-1],"autonomous_target_count":autonomous_count}
        decision=policy.propose_for_object(state_obj,gazes); decision["after_step"]=step; trace.append(decision)
        if decision.get("stop"):
            termination=decision.get("reason"); break
        if step+1>=public.PER_OBJECT_MAX_FIXATIONS: break
        gaze=tuple(float(x) for x in decision["selected"]["next_gaze_deg"]); autonomous_count+=1

    if termination is None: termination="max_object_fixations"
    if surf is None: raise AssertionError("component ended without a map")
    save_map(args.out/"surface_map.npz",surf)
    final=trace[-1] if trace else {"stop":False,"reason":"missing"}
    json_write(args.out/"object_policy_trace.json",{"policy":"frozen FSG6f single-object control in complete Scene-1c fixture","trace":trace})
    manifest={"schema":"Scene1c-component-prediction-v1","role":"component_certification_control","instrument":public.INSTRUMENT_ID,"public_spec_sha256":public.public_digest(),
              "profile":args.profile,"fixture":args.fixture,"seed":args.seed,"object_id":oid,"fixed_head":True,"static_scene":True,"complete_three_object_scene_rendered":True,
              "fixation_gazes_deg":[list(g) for g in gazes],"termination_reason":termination,"final_object_policy_state":{"stop":bool(final.get("stop",False)),"reason":final.get("reason"),"frontier_open_count":int(final.get("frontier_open_count",0)),"candidate_count":len(final.get("candidates",[]))},
              "patch_stats":patch_stats,"association_stats":assoc_stats,"truth_opened":False,"policy_inputs":["one persistent object map","completed binocular observation history","current calibration and oracle instance mask/raw support","own physical fixation history","frozen FSG6f controller"],
              "primary_camera_samples":samples,"blender_recorded_wall_seconds":render_seconds,"loop_wall_seconds":time.perf_counter()-t0}
    json_write(args.out/"prediction_manifest.json",manifest)
    print("[scene1c-certify-run] COMPLETE",json.dumps({"fixture":args.fixture,"seed":args.seed,"object":oid,"fixations":len(gazes),"termination":termination,"samples":samples},sort_keys=True),flush=True)
    return manifest


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--repo",default="."); ap.add_argument("--out",required=True); ap.add_argument("--profile",choices=("small","full"),required=True)
    ap.add_argument("--fixture",choices=public.FIXTURES,required=True); ap.add_argument("--seed",type=int,choices=public.SEEDS,required=True); ap.add_argument("--object-id",type=int,choices=public.OBJECT_IDS,required=True)
    ap.add_argument("--device",choices=("OPTIX","CUDA","CPU"),default="OPTIX"); ap.add_argument("--blender",default="blender"); ap.add_argument("--save-blend",action="store_true"); execute(ap.parse_args())
if __name__=="__main__": main()
