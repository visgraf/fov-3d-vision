"""Run one Stage II / Scene-1b seeded multi-object active reconstruction trial."""
from __future__ import annotations
import argparse, json, subprocess, time
from pathlib import Path
import numpy as np
import cv2
from PIL import Image
import scene1b_public as public
import scene1b_policy as scene_policy
import fsg6f_public as frozen_public
from fsg3_surface_map import Patch, SurfaceMap, initialize, fuse, save_map
import fsg_stereo_hdr as hdr
from fsg_stereo_supported import compute_once, check_kernel_equivalence
from fsg_stereo import support_mask
from fsg_geometry import json_write


def patch_for_object(pid:str, rec:dict, object_id:int)->Patch:
    m=rec["valid"]&(rec["instance_id"]==int(object_id))
    return Patch(pid,rec["xyz_h"][m],rec["rgb_left"][m],rec["instance_id"][m])


def measurement_stats(rec:dict,object_id:int)->tuple[int,int,float|None]:
    ref=(rec["instance_id"]==int(object_id))&rec["raw_support_L"]; nref=int(ref.sum()); nvalid=int((rec["valid"]&ref).sum())
    return nref,nvalid,(float(nvalid/nref) if nref else None)


def raw_observation(c,rec,ids_R,raw_support_R)->dict:
    return {"calibration":c,"instance_L":rec["instance_id"].copy(),"raw_support_L":rec["raw_support_L"].copy(),
            "instance_R":ids_R.copy(),"raw_support_R":raw_support_R.copy()}


def write_patch_visual(path:Path,rec:dict,target_object:int)->None:
    obj=(rec["instance_id"]==int(target_object))&rec["raw_support_L"]; valid=rec["valid"]&obj
    im=np.zeros((*obj.shape,3),np.uint8); im[obj]=(120,120,120); im[valid]=(255,255,255); Image.fromarray(im).save(path)


def save_scene_ply(path:Path,maps:dict[int,SurfaceMap])->None:
    rows=[]
    for oid in public.OBJECT_IDS:
        m=maps.get(oid)
        if m is None: continue
        rgb=np.rint(255*np.clip(np.asarray(m.rgb,float),0,1)).astype(np.uint8)
        for p,c,n,i in zip(m.xyz_h,rgb,m.support_count,m.instance_id): rows.append((p,c,int(n),int(i)))
    with path.open("w",encoding="ascii") as f:
        f.write("ply\nformat ascii 1.0\ncomment fixed head frame H; Stage II Scene-1b\n")
        f.write(f"element vertex {len(rows)}\nproperty float x\nproperty float y\nproperty float z\nproperty uchar red\nproperty uchar green\nproperty uchar blue\nproperty ushort support\nproperty int instance_id\nend_header\n")
        for p,c,n,i in rows: f.write(f"{p[0]:.8g} {p[1]:.8g} {p[2]:.8g} {int(c[0])} {int(c[1])} {int(c[2])} {n} {i}\n")




def write_scene_overview(path:Path,maps:dict[int,SurfaceMap],gazes:list[tuple[float,float]],targets:list[int])->None:
    canvas=np.full((620,900,3),245,np.uint8); cv2.rectangle(canvas,(55,55),(845,520),(210,210,210),1)
    shades={201:35,202:105,203:170}
    for oid in public.OBJECT_IDS:
        m=maps.get(oid)
        if m is None: continue
        p=np.asarray(m.xyz_h,float); y=np.degrees(np.arctan2(p[:,0],-p[:,2])); q=np.degrees(np.arctan2(p[:,1],np.sqrt(p[:,0]**2+p[:,2]**2)))
        xx=np.clip(((y+25)/50)*760+70,70,830).astype(int); yy=np.clip(((20-q)/40)*435+70,70,505).astype(int); v=shades[oid]
        for X,Y in zip(xx[::3],yy[::3]): canvas[Y,X]=(v,v,v)
        cv2.putText(canvas,f"obj {oid}",(65,545+22*(oid-201)),cv2.FONT_HERSHEY_SIMPLEX,.48,(v,v,v),1,cv2.LINE_AA)
    for k,(g,oid) in enumerate(zip(gazes,targets)):
        X=int(np.clip(((g[0]+25)/50)*760+70,70,830)); Y=int(np.clip(((20-g[1])/40)*435+70,70,505)); cv2.circle(canvas,(X,Y),4,(20,20,20),1); cv2.putText(canvas,str(k),(X+4,Y-4),cv2.FONT_HERSHEY_SIMPLEX,.30,(20,20,20),1,cv2.LINE_AA)
    cv2.putText(canvas,"Scene-1b final persistent maps and physical fixations",(55,30),cv2.FONT_HERSHEY_SIMPLEX,.60,(20,20,20),1,cv2.LINE_AA)
    cv2.imwrite(str(path),canvas)

def run_blender(args,step:int,target:int,gaze:tuple[float,float],root:Path):
    yaw,pitch=gaze; out=root/f"fix_{step:02d}"
    cmd=[args.blender,"-b","--python-exit-code","1","-P","tools/scene1b_render_fix.py","--","--out",str(out),"--profile",args.profile,"--fixture",args.fixture,"--seed",str(args.seed),"--step",str(step),"--target-object",str(target),"--yaw",f"{yaw:.12g}","--pitch",f"{pitch:.12g}","--device",args.device]
    if args.save_blend: cmd.append("--save-blend")
    p=subprocess.run(cmd,cwd=args.repo,text=True,capture_output=True); log=args.out/"logs"/f"render_{step:02d}.log"; log.write_text(p.stdout+"\n--- STDERR ---\n"+p.stderr)
    if p.returncode!=0: raise RuntimeError(f"Blender fixation {step} failed; see {log}")
    rr=json.loads((out/"run.json").read_text()); case=out/f"fix_{step:02d}"
    if not rr.get("complete") or rr.get("fixture")!=args.fixture or int(rr.get("seed"))!=args.seed or int(rr.get("target_object_id"))!=target or abs(float(rr["yaw_deg"])-yaw)>1e-8 or abs(float(rr["pitch_deg"])-pitch)>1e-8:
        raise RuntimeError("incomplete or wrong Scene-1b Blender record")
    return case,rr


def _state(oid:int,maps,hist,last_obs,last_gaze,autonomous_target_counts)->dict:
    return {"object_id":oid,"map":maps[oid],"observation_history":hist[oid],
            "last_target_observation":last_obs[oid],"last_target_gaze_deg":last_gaze[oid],
            "autonomous_target_count":int(autonomous_target_counts[oid])}


def execute(args)->dict:
    args.repo=Path(args.repo).resolve(); args.out=Path(args.out).resolve()
    if args.out.exists(): raise FileExistsError("output must be new")
    args.out.mkdir(parents=True); [ (args.out/d).mkdir() for d in ("logs","acquisitions","patches","maps") ]
    for oid in public.OBJECT_IDS: (args.out/"maps"/f"obj_{oid}").mkdir()
    check_kernel_equivalence()
    if public.FUSION!=frozen_public.FUSION: raise AssertionError("Scene-1b must preserve frozen FSG6f/FSG3 fusion")
    if public.FROZEN_OBJECT_POLICY_ID!=frozen_public.SPEC_ID: raise AssertionError("Scene-1b must use frozen FSG6f object controller")
    if args.fixture not in public.FIXTURES or args.seed not in public.SEEDS: raise ValueError("fixture/seed outside Scene-1b schedule")

    maps={oid:None for oid in public.OBJECT_IDS}; histories={oid:[] for oid in public.OBJECT_IDS}; last_obs={oid:None for oid in public.OBJECT_IDS}; last_gaze={oid:None for oid in public.OBJECT_IDS}
    target_counts={oid:0 for oid in public.OBJECT_IDS}; autonomous_target_counts={oid:0 for oid in public.OBJECT_IDS}; global_gazes=[]; target_sequence=[]; patch_stats=[]; assoc_stats=[]; scheduler_trace=[]
    samples=0; render_seconds=0.0; termination=None; next_active=None; t0=time.perf_counter(); seeds=list(public.SEED_SEQUENCE[args.fixture])

    for step in range(public.MAX_SCENE_FIXATIONS):
        if step<len(seeds): target,gaze=seeds[step]; phase="prescribed_seed"
        else:
            if next_active is None:
                states={oid:_state(oid,maps,histories,last_obs,last_gaze,autonomous_target_counts) for oid in public.OBJECT_IDS}
                next_active=scene_policy.choose_scene_action(states,global_gazes)
            if next_active["stop"]: termination=next_active["reason"]; break
            target=int(next_active["selected_object_id"]); gaze=tuple(float(x) for x in next_active["next_gaze_deg"]); phase="autonomous"
            if target_counts[target] >= public.PER_OBJECT_MAX_FIXATIONS:
                termination="object_budget_exhausted"; break
        if scene_policy.is_global_repeat(gaze,global_gazes): raise AssertionError("scene policy revisited a physical fixation")
        case,rr=run_blender(args,step,int(target),tuple(gaze),args.out/"acquisitions"); samples+=int(rr["primary_camera_samples"]); render_seconds+=float(rr["total_wall_seconds"])
        c,obs=hdr.read_observation(case); rec,meta,state=compute_once(c,obs); x,y,cw,ch=map(int,rec["crop_xywh"]); sl=np.s_[y:y+ch,x:x+cw]
        ids_R=state["ids_right"][sl]; raw_support_R=support_mask(c,rec,"R")[sl]
        if not np.array_equal(rec["instance_id"],state["ids_left"][sl]): raise AssertionError("left rectified ID replay mismatch")
        robs=raw_observation(c,rec,ids_R,raw_support_R)
        for oid in public.OBJECT_IDS: histories[oid].append(robs)
        target_counts[int(target)]+=1
        if phase=="autonomous": autonomous_target_counts[int(target)]+=1
        last_obs[int(target)]=robs; last_gaze[int(target)]=tuple(gaze)
        global_gazes.append(tuple(float(v) for v in gaze)); target_sequence.append(int(target))
        np.savez_compressed(args.out/"patches"/f"fix_{step:02d}.npz",valid=rec["valid"],oracle_instance_id=rec["instance_id"],raw_support_L=rec["raw_support_L"],oracle_instance_id_R=ids_R,raw_support_R=raw_support_R)
        write_patch_visual(args.out/"patches"/f"fix_{step:02d}_target_mask.png",rec,int(target))

        per_fix={}
        for oid in public.OBJECT_IDS:
            pid=f"fix_{step:02d}_obj_{oid}"; p=patch_for_object(pid,rec,oid); nref,nvalid,cov=measurement_stats(rec,oid); targeted=(oid==int(target)); fused=False; assoc=None; idem=True
            if len(p.xyz_h)>=100:
                fused=True
                if maps[oid] is None:
                    maps[oid]=initialize(p,oid); assoc={"duplicate_patch":False,"matched":0,"new":len(p.xyz_h),"affected_surfels":0,"distances_m":np.empty(0),"input_points":len(p.xyz_h),"base_points":0}
                else:
                    maps[oid],assoc=fuse(maps[oid],p,oid,public.FUSION["association_radius_m"],public.FUSION["hash_cell_m"])
                    replay,dup=fuse(maps[oid],p,oid,public.FUSION["association_radius_m"],public.FUSION["hash_cell_m"])
                    idem=bool(dup["duplicate_patch"] and np.array_equal(maps[oid].xyz_h,replay.xyz_h) and np.array_equal(maps[oid].support_count,replay.support_count) and np.array_equal(maps[oid].provenance_mask,replay.provenance_mask))
                    if not idem: raise AssertionError("object patch replay is not idempotent")
                save_map(args.out/"maps"/f"obj_{oid}"/f"map_{step:02d}.npz",maps[oid])
            if targeted and len(p.xyz_h)<100: raise ValueError(f"target object {oid} has too few reconstructed points")
            dist=np.empty(0) if assoc is None else assoc["distances_m"]
            row={"step":step,"object_id":oid,"targeted":targeted,"phase":phase,"patch_id":pid,"object_reference_count":nref,"object_valid_count":nvalid,"object_measurement_fraction":cov,"point_count":int(len(p.xyz_h)),"fused":fused,"idempotent_replay":idem,
                 "matched":0 if assoc is None else int(assoc["matched"]),"new":0 if assoc is None else int(assoc["new"]),"input_points":0 if assoc is None else int(assoc["input_points"]),"overlap_median_distance_m":float(np.median(dist)) if len(dist) else None,"overlap_p95_distance_m":float(np.percentile(dist,95)) if len(dist) else None}
            per_fix[str(oid)]=row; patch_stats.append({k:v for k,v in row.items() if k not in ("matched","new","input_points","overlap_median_distance_m","overlap_p95_distance_m","idempotent_replay")}); assoc_stats.append(row)
        if maps[int(target)] is None: raise AssertionError("target object map missing after target fixation")

        if step>=len(seeds)-1:
            states={oid:_state(oid,maps,histories,last_obs,last_gaze,autonomous_target_counts) for oid in public.OBJECT_IDS}
            decision=scene_policy.choose_scene_action(states,global_gazes); decision["after_step"]=step; decision["completed_target_object_id"]=int(target); scheduler_trace.append(decision); next_active=decision
            if decision["stop"]: termination=decision["reason"]; break
        else: next_active=None

    if termination is None: termination="max_scene_fixations"
    if any(maps[oid] is None for oid in public.OBJECT_IDS): raise AssertionError("scene ended with unseeded object map")
    for oid in public.OBJECT_IDS: save_map(args.out/f"object_{oid}_surface_map.npz",maps[oid])
    save_scene_ply(args.out/"scene_surface_map.ply",maps); write_scene_overview(args.out/"scene_map.png",maps,global_gazes,target_sequence)
    json_write(args.out/"scene_policy_trace.json",{"policy":"least-served-first fair scheduler over frozen FSG6f object proposals","trace":scheduler_trace})
    final_states={}
    states={oid:_state(oid,maps,histories,last_obs,last_gaze,autonomous_target_counts) for oid in public.OBJECT_IDS}
    final_decision=scene_policy.choose_scene_action(states,global_gazes)
    for p in final_decision["proposals"]: final_states[str(p["object_id"])]={"stop":bool(p["stop"]),"reason":p["reason"],"frontier_open_count":int(p.get("frontier_open_count",0)),"candidate_count":len(p.get("candidates",[]))}
    manifest={"schema":"Scene1b-prediction-v1","instrument":public.INSTRUMENT_ID,"public_spec_sha256":public.public_digest(),"profile":args.profile,"fixture":args.fixture,"seed":args.seed,"fixed_head":True,"static_scene":True,
              "fixation_gazes_deg":[list(g) for g in global_gazes],"target_object_sequence":target_sequence,"prescribed_seed_fixations":len(seeds),"termination_reason":termination,"target_counts":{str(k):int(v) for k,v in target_counts.items()},"autonomous_target_counts":{str(k):int(v) for k,v in autonomous_target_counts.items()},"final_object_policy_states":final_states,
              "patch_stats":patch_stats,"association_stats":assoc_stats,"truth_opened":False,"policy_inputs":["three persistent object maps","current/past binocular oracle instance masks and raw support","calibration","global physical fixation history","frozen FSG6f per-object proposals","per-object autonomous service counts"],
              "opportunistic_fusion_enabled":True,"global_no_revisit":True,"primary_camera_samples":samples,"blender_recorded_wall_seconds":render_seconds,"loop_wall_seconds":time.perf_counter()-t0}
    json_write(args.out/"prediction_manifest.json",manifest)
    print("[scene1b-run] COMPLETE",json.dumps({"fixture":args.fixture,"seed":args.seed,"fixations":len(global_gazes),"targets":target_sequence,"termination":termination,"samples":samples},sort_keys=True),flush=True)
    return manifest


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--repo",default="."); ap.add_argument("--out",required=True); ap.add_argument("--profile",choices=("small","full"),required=True); ap.add_argument("--fixture",choices=public.FIXTURES,required=True); ap.add_argument("--seed",type=int,choices=public.SEEDS,required=True); ap.add_argument("--device",choices=("OPTIX","CUDA","CPU"),default="OPTIX"); ap.add_argument("--blender",default="blender"); ap.add_argument("--save-blend",action="store_true"); execute(ap.parse_args())
if __name__=="__main__": main()
