"""Run one FSG7a prescribed head-translation self-occlusion trial, truth-free."""
from __future__ import annotations
import argparse,json,subprocess,time
from pathlib import Path
import numpy as np
import cv2
from PIL import Image
import fsg7a_public as public
import fsg7a_motion as motion
import fsg4_public as frozen_public
from fsg3_surface_map import Patch,SurfaceMap,initialize,fuse,save_map
import fsg_stereo_hdr as hdr
from fsg_stereo_supported import compute_once,check_kernel_equivalence
from fsg_geometry import json_write

def object_stats(rec):
    ref=(rec["instance_id"]==public.OBJECT_ID)&rec["raw_support_L"]; nref=int(ref.sum()); nvalid=int((rec["valid"]&ref).sum()); return nref,nvalid,(float(nvalid/nref) if nref else None)

def patch_from_record(pid,rec,t):
    m=rec["valid"]&(rec["instance_id"]==public.OBJECT_ID); xyz_h0=motion.points_ht_to_h0(rec["xyz_h"][m],t); return Patch(pid,xyz_h0,rec["rgb_left"][m],rec["instance_id"][m]),xyz_h0,m

def write_mask(path,rec):
    obj=(rec["instance_id"]==public.OBJECT_ID)&rec["raw_support_L"]; val=rec["valid"]&obj; im=np.zeros((*obj.shape,3),np.uint8); im[obj]=(120,120,120); im[val]=(255,255,255); Image.fromarray(im).save(path)

def save_ply(path:Path,sm:SurfaceMap):
    xyz=np.asarray(sm.xyz_h,float); rgb=np.clip(np.asarray(sm.rgb,float),0,1); c=np.rint(255*rgb).astype(np.uint8)
    with path.open("w",encoding="ascii") as f:
        f.write("ply\nformat ascii 1.0\ncomment fixed initial head frame H0\n"); f.write(f"element vertex {len(xyz)}\nproperty float x\nproperty float y\nproperty float z\nproperty uchar red\nproperty uchar green\nproperty uchar blue\nproperty ushort support\nend_header\n")
        for p,q,n in zip(xyz,c,sm.support_count): f.write(f"{p[0]:.8g} {p[1]:.8g} {p[2]:.8g} {int(q[0])} {int(q[1])} {int(q[2])} {int(n)}\n")

def write_growth(path,snaps,supports,views):
    h=320; w=360*len(snaps); canvas=np.full((h,w,3),245,np.uint8)
    for k,(xyz,sup,v) in enumerate(zip(snaps,supports,views)):
        x0=360*k; x=xyz[:,0]; z=xyz[:,2]; px=np.clip((x+.8)/1.6*300+x0+30,x0+30,x0+330).astype(int); py=np.clip((-z-2.2)/1.4*230+45,45,275).astype(int); strong=sup>1
        cv2.rectangle(canvas,(x0+20,38),(x0+340,285),(210,210,210),1); cv2.putText(canvas,f"{k} {v['role']} head_x={v['head_translation_h0_m'][0]:+.2f}",(x0+24,20),cv2.FONT_HERSHEY_SIMPLEX,.40,(20,20,20),1,cv2.LINE_AA)
        for X,Y,S in zip(px[::2],py[::2],strong[::2]): canvas[Y,X]=(20,20,20) if S else (145,145,145)
    cv2.imwrite(str(path),canvas)

def run_blender(args,step,acq_root):
    out=acq_root/f"fix_{step:02d}"; cmd=[args.blender,"-b","--python-exit-code","1","-P","tools/fsg7a_render_fix.py","--","--out",str(out),"--profile",args.profile,"--fixture",args.fixture,"--seed",str(args.seed),"--step",str(step),"--device",args.device]
    if args.save_blend: cmd.append("--save-blend")
    p=subprocess.run(cmd,cwd=args.repo,text=True,capture_output=True); log=args.out/"logs"/f"render_{step:02d}.log"; log.write_text(p.stdout+"\n--- STDERR ---\n"+p.stderr)
    if p.returncode!=0: raise RuntimeError(f"Blender fixation {step} failed; see {log}")
    rr=json.loads((out/"run.json").read_text()); case=out/f"fix_{step:02d}"; v=public.view(args.fixture,step)
    if not rr.get("complete") or rr.get("fixture")!=args.fixture or int(rr.get("seed"))!=args.seed or not np.allclose(rr["head_translation_h0_m"],v["head_translation_h0_m"],atol=1e-9): raise RuntimeError("incomplete or wrong FSG7a Blender record")
    return case,rr

def execute(args):
    args.repo=Path(args.repo).resolve(); args.out=Path(args.out).resolve()
    if args.out.exists(): raise FileExistsError("output must be new")
    args.out.mkdir(parents=True); [(args.out/d).mkdir() for d in ("logs","acquisitions","patches","maps")]
    check_kernel_equivalence()
    if public.FUSION!=frozen_public.FUSION: raise AssertionError("FSG7a must preserve frozen 12 mm fusion")
    if args.fixture not in public.FIXTURES or args.seed not in public.SEEDS: raise ValueError("fixture/seed outside FSG7a schedule")
    views=[]; patch_stats=[]; assoc_stats=[]; samples=0; render_seconds=0.; sm=None; snaps=[]; supports=[]; t0=time.perf_counter()
    for step in range(2):
        v=public.view(args.fixture,step); t=np.asarray(v["head_translation_h0_m"],float); case,rr=run_blender(args,step,args.out/"acquisitions"); samples+=int(rr["primary_camera_samples"]); render_seconds+=float(rr["total_wall_seconds"])
        c,obs=hdr.read_observation(case); rec,meta,state=compute_once(c,obs); pid=f"fix_{step:02d}"; p,xyz_h0,mask=patch_from_record(pid,rec,t); nref,nvalid,cov=object_stats(rec)
        np.savez_compressed(args.out/"patches"/f"{pid}.npz",xyz_ht=rec["xyz_h"][mask].astype(np.float32),xyz_h0=xyz_h0.astype(np.float32),rgb=p.rgb.astype(np.float32),instance_id=p.instance_id,valid=rec["valid"],oracle_instance_id=rec["instance_id"],raw_support_L=rec["raw_support_L"],head_translation_h0_m=t.astype(np.float32)); write_mask(args.out/"patches"/f"{pid}_mask.png",rec)
        if len(p.xyz_h)<100: raise ValueError("active FSG7a fixation has too few object points")
        if sm is None:
            sm=initialize(p,public.OBJECT_ID); assoc={"duplicate_patch":False,"matched":0,"new":len(p.xyz_h),"affected_surfels":0,"distances_m":np.empty(0),"input_points":len(p.xyz_h),"base_points":0}; idem=True
        else:
            sm,assoc=fuse(sm,p,public.OBJECT_ID,public.FUSION["association_radius_m"],public.FUSION["hash_cell_m"]); replay,dup=fuse(sm,p,public.OBJECT_ID,public.FUSION["association_radius_m"],public.FUSION["hash_cell_m"]); idem=bool(dup["duplicate_patch"] and np.array_equal(sm.xyz_h,replay.xyz_h) and np.array_equal(sm.support_count,replay.support_count) and np.array_equal(sm.provenance_mask,replay.provenance_mask))
            if not idem: raise AssertionError("patch replay is not idempotent")
        save_map(args.out/"maps"/f"map_{step:02d}.npz",sm); snaps.append(sm.xyz_h.copy()); supports.append(sm.support_count.copy()); views.append(v)
        dist=assoc["distances_m"]; assoc_stats.append({"step":step,"patch_id":pid,"input_points":int(assoc["input_points"]),"matched":int(assoc["matched"]),"new":int(assoc["new"]),"affected_surfels":int(assoc["affected_surfels"]),"new_fraction":float(assoc["new"]/max(1,assoc["input_points"])),"overlap_median_distance_m":float(np.median(dist)) if len(dist) else None,"overlap_p95_distance_m":float(np.percentile(dist,95)) if len(dist) else None,"idempotent_replay":idem})
        patch_stats.append({"step":step,"patch_id":pid,"role":v["role"],"head_translation_h0_m":list(v["head_translation_h0_m"]),"gaze_yaw_pitch_deg":list(v["gaze_yaw_pitch_deg"]),"object_reference_count":nref,"object_valid_count":nvalid,"object_measurement_fraction":cov,"point_count":len(p.xyz_h),"instrument":public.INSTRUMENT_ID})
    save_map(args.out/"surface_map.npz",sm); save_ply(args.out/"surface_map.ply",sm); write_growth(args.out/"growth.png",snaps,supports,views)
    manifest={"schema":"FSG7a-prediction-v1","instrument":public.INSTRUMENT_ID,"public_spec_sha256":public.public_digest(),"profile":args.profile,"fixture":args.fixture,"seed":args.seed,"views":views,"termination_reason":"schedule_complete","patch_stats":patch_stats,"association_stats":assoc_stats,"truth_opened":False,"policy":"none; prescribed two-view head-motion feasibility","policy_inputs":[],"map_frame":"H0 initial head frame","primary_camera_samples":samples,"blender_recorded_wall_seconds":render_seconds,"loop_wall_seconds":time.perf_counter()-t0}
    json_write(args.out/"prediction_manifest.json",manifest); print("[fsg7a-run] COMPLETE",json.dumps({"fixture":args.fixture,"seed":args.seed,"views":views,"samples":samples},sort_keys=True),flush=True); return manifest

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--repo",default="."); ap.add_argument("--out",required=True); ap.add_argument("--profile",choices=("small","full"),required=True); ap.add_argument("--fixture",choices=public.FIXTURES,required=True); ap.add_argument("--seed",type=int,choices=public.SEEDS,required=True); ap.add_argument("--device",choices=("OPTIX","CUDA","CPU"),default="OPTIX"); ap.add_argument("--blender",default="blender"); ap.add_argument("--save-blend",action="store_true"); a=ap.parse_args(); execute(a)
if __name__=="__main__": main()
