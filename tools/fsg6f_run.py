"""Run one FSG6f active trial with the truth-free 3D surfel-frontier policy."""
from __future__ import annotations
import argparse
import json
import subprocess
import time
from pathlib import Path
import numpy as np
import cv2
from PIL import Image
import fsg6f_public as public
import fsg6f_frontier as policy
import fsg4_public as frozen_public
from fsg3_surface_map import Patch, SurfaceMap, initialize, fuse, save_map
import fsg_stereo_hdr as hdr
from fsg_stereo_supported import compute_once, check_kernel_equivalence
from fsg_geometry import json_write
from fsg_stereo import support_mask


def patch_from_record(pid:str,rec:dict)->Patch:
    m=rec["valid"]&(rec["instance_id"]==public.OBJECT_ID); return Patch(pid,rec["xyz_h"][m],rec["rgb_left"][m],rec["instance_id"][m])

def object_measurement_stats(rec:dict):
    ref=(rec["instance_id"]==public.OBJECT_ID)&rec["raw_support_L"]; nref=int(ref.sum()); nvalid=int((rec["valid"]&ref).sum()); return nref,nvalid,(float(nvalid/nref) if nref else None)

def write_patch_visual(path:Path,rec:dict)->None:
    obj=(rec["instance_id"]==public.OBJECT_ID)&rec["raw_support_L"]; valid=rec["valid"]&obj; im=np.zeros((*obj.shape,3),np.uint8); im[obj]=(120,120,120); im[valid]=(255,255,255); Image.fromarray(im).save(path)

def save_ply(path:Path,sm:SurfaceMap)->None:
    xyz=np.asarray(sm.xyz_h,float); rgb=np.clip(np.asarray(sm.rgb,float),0,1); c=np.rint(255*rgb).astype(np.uint8)
    with path.open("w",encoding="ascii") as f:
        f.write("ply\nformat ascii 1.0\ncomment fixed head frame H\n"); f.write(f"element vertex {len(xyz)}\n"); f.write("property float x\nproperty float y\nproperty float z\nproperty uchar red\nproperty uchar green\nproperty uchar blue\nproperty ushort support\nend_header\n")
        for p,q,n in zip(xyz,c,sm.support_count): f.write(f"{p[0]:.8g} {p[1]:.8g} {p[2]:.8g} {int(q[0])} {int(q[1])} {int(q[2])} {int(n)}\n")

def write_growth(path:Path,snapshots:list[np.ndarray],supports:list[np.ndarray],gazes:list[tuple[float,float]])->None:
    h=320; w=330*len(snapshots); canvas=np.full((h,w,3),245,np.uint8)
    for k,(xyz,sup,g) in enumerate(zip(snapshots,supports,gazes)):
        yaw=np.degrees(np.arctan2(xyz[:,0],-xyz[:,2])); pit=np.degrees(np.arctan2(xyz[:,1],np.sqrt(xyz[:,0]**2+xyz[:,2]**2))); x0=k*330
        cv2.rectangle(canvas,(x0+20,35),(x0+310,285),(210,210,210),1); cv2.putText(canvas,f"{k}: yaw {g[0]:.1f} pitch {g[1]:.1f}",(x0+24,22),cv2.FONT_HERSHEY_SIMPLEX,.40,(20,20,20),1,cv2.LINE_AA)
        px=np.clip(((yaw+22)/44)*270+x0+30,x0+30,x0+300).astype(int); py=np.clip(((18-pit)/36)*225+48,48,273).astype(int); strong=sup>1
        for X,Y,S in zip(px[::2],py[::2],strong[::2]): canvas[Y,X]=(25,25,25) if S else (145,145,145)
    cv2.imwrite(str(path),canvas)

def run_blender(args,step:int,gaze:tuple[float,float],acq_root:Path):
    yaw,pitch=gaze; out=acq_root/f"fix_{step:02d}"; cmd=[args.blender,"-b","--python-exit-code","1","-P","tools/fsg6f_render_fix.py","--","--out",str(out),"--profile",args.profile,"--fixture",args.fixture,"--seed",str(args.seed),"--step",str(step),"--yaw",f"{yaw:.12g}","--pitch",f"{pitch:.12g}","--device",args.device]
    if args.save_blend: cmd.append("--save-blend")
    p=subprocess.run(cmd,cwd=args.repo,text=True,capture_output=True); log=args.out/"logs"/f"render_{step:02d}.log"; log.write_text(p.stdout+"\n--- STDERR ---\n"+p.stderr)
    if p.returncode!=0: raise RuntimeError(f"Blender fixation {step} failed; see {log}")
    rr=json.loads((out/"run.json").read_text()); case=out/f"fix_{step:02d}"
    if not rr.get("complete") or rr.get("fixture")!=args.fixture or int(rr.get("seed"))!=args.seed or abs(float(rr["yaw_deg"])-yaw)>1e-8 or abs(float(rr["pitch_deg"])-pitch)>1e-8: raise RuntimeError("incomplete or wrong FSG6f Blender record")
    return case,rr

def execute(args)->dict:
    args.repo=Path(args.repo).resolve(); args.out=Path(args.out).resolve()
    if args.out.exists(): raise FileExistsError("output must be new")
    args.out.mkdir(parents=True); [ (args.out/d).mkdir() for d in ("logs","acquisitions","patches","maps") ]
    check_kernel_equivalence()
    if public.FUSION != frozen_public.FUSION:
        raise AssertionError("FSG6f must preserve the frozen 12 mm FSG3/FSG4 fusion rule")
    if args.fixture not in public.FIXTURES or args.seed not in public.SEEDS: raise ValueError("fixture/seed outside frozen FSG6f schedule")
    gazes=[]; patch_stats=[]; assoc_stats=[]; policy_trace=[]; observation_history=[]; samples=0; render_seconds=0.0; snapshots=[]; supports=[]; sm=None
    gaze=tuple(float(x) for x in public.SEED_GAZE_DEG[args.fixture]); termination=None; t0=time.perf_counter()
    for step in range(public.MAX_BUDGET_FIXATIONS):
        if any(np.allclose(g,gaze,atol=1e-9) for g in gazes): raise AssertionError("policy revisited an existing fixation")
        case,rr=run_blender(args,step,gaze,args.out/"acquisitions"); samples+=int(rr["primary_camera_samples"]); render_seconds+=float(rr["total_wall_seconds"])
        c,obs=hdr.read_observation(case); rec,meta,state=compute_once(c,obs); pid=f"fix_{step:02d}"; p=patch_from_record(pid,rec); nref,nvalid,cov=object_measurement_stats(rec)
        x,y,cw,ch=map(int,rec["crop_xywh"]); sl=np.s_[y:y+ch,x:x+cw]
        ids_R=state["ids_right"][sl]; raw_support_R=support_mask(c,rec,"R")[sl]
        if not np.array_equal(rec["instance_id"],state["ids_left"][sl]): raise AssertionError("left rectified ID replay mismatch")
        np.savez_compressed(args.out/"patches"/f"{pid}.npz",xyz_h=p.xyz_h.astype(np.float32),rgb=p.rgb.astype(np.float32),instance_id=p.instance_id,valid=rec["valid"],oracle_instance_id=rec["instance_id"],raw_support_L=rec["raw_support_L"],oracle_instance_id_R=ids_R,raw_support_R=raw_support_R); write_patch_visual(args.out/"patches"/f"{pid}_mask.png",rec)
        if len(p.xyz_h)<100: raise ValueError("active FSG6f fixation has too few object points")
        if sm is None:
            sm=initialize(p,public.OBJECT_ID); assoc={"duplicate_patch":False,"matched":0,"new":len(p.xyz_h),"affected_surfels":0,"distances_m":np.empty(0),"input_points":len(p.xyz_h),"base_points":0}; idempotent=True
        else:
            sm,assoc=fuse(sm,p,public.OBJECT_ID,public.FUSION["association_radius_m"],public.FUSION["hash_cell_m"]); replay,dup=fuse(sm,p,public.OBJECT_ID,public.FUSION["association_radius_m"],public.FUSION["hash_cell_m"])
            idempotent=bool(dup["duplicate_patch"] and np.array_equal(sm.xyz_h,replay.xyz_h) and np.array_equal(sm.support_count,replay.support_count) and np.array_equal(sm.provenance_mask,replay.provenance_mask))
            if not idempotent: raise AssertionError("patch replay is not idempotent")
        save_map(args.out/"maps"/f"map_{step:02d}.npz",sm); snapshots.append(sm.xyz_h.copy()); supports.append(sm.support_count.copy()); gazes.append((float(gaze[0]),float(gaze[1])))
        dist=assoc["distances_m"]; assoc_stats.append({"step":step,"patch_id":pid,"input_points":int(assoc["input_points"]),"matched":int(assoc["matched"]),"new":int(assoc["new"]),"affected_surfels":int(assoc["affected_surfels"]),"new_fraction":float(assoc["new"]/max(1,assoc["input_points"])),"overlap_median_distance_m":float(np.median(dist)) if len(dist) else None,"overlap_p95_distance_m":float(np.percentile(dist,95)) if len(dist) else None,"idempotent_replay":idempotent})
        patch_stats.append({"step":step,"patch_id":pid,"yaw_deg":gaze[0],"pitch_deg":gaze[1],"object_reference_count":nref,"object_valid_count":nvalid,"object_measurement_fraction":cov,"point_count":len(p.xyz_h),"instrument":public.INSTRUMENT_ID})
        observation_history.append({
            "calibration": c,
            "instance_L": rec["instance_id"].copy(),
            "raw_support_L": rec["raw_support_L"].copy(),
            "instance_R": ids_R.copy(),
            "raw_support_R": raw_support_R.copy(),
        })
        decision=policy.choose_next(gaze[0],gaze[1],c,rec["instance_id"],rec["raw_support_L"],ids_R,raw_support_R,sm.xyz_h,gazes,observation_history); decision["step"]=step; policy_trace.append(decision)
        if decision["stop"]: termination=decision["reason"]; break
        gaze=tuple(float(x) for x in decision["next_gaze_deg"])
    if termination is None: termination="max_fixations"
    save_map(args.out/"surface_map.npz",sm); save_ply(args.out/"surface_map.ply",sm); write_growth(args.out/"growth.png",snapshots,supports,gazes); json_write(args.out/"policy_trace.json",{"policy":"fsg6f_persistent_frontier_candidate_consensus_with_projected_corridor","trace":policy_trace})
    manifest={"schema":"FSG6f-prediction-v1","instrument":public.INSTRUMENT_ID,"public_spec_sha256":public.public_digest(),"profile":args.profile,"fixture":args.fixture,"seed":args.seed,"fixation_gazes_deg":[list(g) for g in gazes],"termination_reason":termination,"patch_stats":patch_stats,"association_stats":assoc_stats,"truth_opened":False,"policy_inputs":["persistent map xyz_h","current rectified oracle instance masks L/R","raw calibration support L/R","calibration","fixation history","completed binocular oracle/support history"],"primary_camera_samples":samples,"blender_recorded_wall_seconds":render_seconds,"loop_wall_seconds":time.perf_counter()-t0}
    json_write(args.out/"prediction_manifest.json",manifest); print("[fsg6f-run] COMPLETE",json.dumps({"fixture":args.fixture,"seed":args.seed,"fixations":len(gazes),"gazes":gazes,"termination":termination,"samples":samples},sort_keys=True),flush=True); return manifest

def main()->None:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--repo",default="."); ap.add_argument("--out",required=True); ap.add_argument("--profile",choices=("small","full"),required=True); ap.add_argument("--fixture",choices=public.FIXTURES,required=True); ap.add_argument("--seed",type=int,choices=public.SEEDS,required=True); ap.add_argument("--device",choices=("OPTIX","CUDA","CPU"),default="OPTIX"); ap.add_argument("--blender",default="blender"); ap.add_argument("--save-blend",action="store_true"); execute(ap.parse_args())
if __name__=="__main__": main()
