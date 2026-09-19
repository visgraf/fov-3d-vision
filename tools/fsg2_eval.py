"""Reconstruct two FSG2 patches with the frozen FSG1 instrument, fuse in H, evaluate."""
from __future__ import annotations
import argparse,json,math,time
from pathlib import Path
import numpy as np, cv2
import fsg2_scene as spec
import fsg_stereo_hdr as hdr
from fsg_stereo_supported import compute_once, check_kernel_equivalence
from fsg_geometry import json_write
from fsg2_surface_map import Patch,initialize,fuse,save_map

INSTRUMENT_ID="FSG1-HDR-SGBM-one-original-update-original-validity-v1"

def write_ply(path:Path,xyz:np.ndarray,rgb:np.ndarray,support:np.ndarray)->None:
    m=np.isfinite(xyz).all(1);x=xyz[m];c=np.clip(np.round(np.clip(rgb[m],0,1)*255),0,255).astype(np.uint8);s=support[m]
    with path.open("w") as f:
        f.write("ply\nformat ascii 1.0\ncomment fixed head frame H\nelement vertex %d\n"%len(x))
        f.write("property float x\nproperty float y\nproperty float z\nproperty uchar red\nproperty uchar green\nproperty uchar blue\nproperty ushort support\nend_header\n")
        for p,q,n in zip(x,c,s): f.write(f"{p[0]:.7g} {p[1]:.7g} {p[2]:.7g} {q[0]} {q[1]} {q[2]} {int(n)}\n")

def patch_from_record(name:str,record:dict)->Patch:
    m=record["valid"]&(record["instance_id"]==spec.OBJECT_ID)
    return Patch(name,record["xyz_h"][m],record["rgb_left"][m],record["instance_id"][m])

def object_reference_mask(record:dict)->np.ndarray:
    m=(record["instance_id"]==spec.OBJECT_ID)&record["raw_support_L"]
    return cv2.erode(m.astype(np.uint8),np.ones((5,5),np.uint8),borderType=cv2.BORDER_CONSTANT,borderValue=0).astype(bool)

def spatial_coverage(xyz:np.ndarray)->float:
    # Fixed surface grid, evaluated against reconstructed points only.
    r,u,n=spec.object_axes(); nx,ny=spec.FUSION["truth_grid_wh"]
    xs=np.linspace(-spec.OBJECT_WIDTH_M/2,spec.OBJECT_WIDTH_M/2,nx); ys=np.linspace(-spec.OBJECT_HEIGHT_M/2,spec.OBJECT_HEIGHT_M/2,ny)
    X,Y=np.meshgrid(xs,ys); truth=spec.OBJECT_CENTRE+X[...,None]*r+Y[...,None]*u; truth=truth.reshape(-1,3)
    cell=spec.FUSION["truth_cover_radius_m"]; bins={}
    for p in xyz: bins.setdefault(tuple(np.floor(p/cell).astype(int)),[]).append(p)
    hit=0
    for q in truth:
        k=tuple(np.floor(q/cell).astype(int)); best=cell
        for a in (-1,0,1):
          for b in (-1,0,1):
           for c in (-1,0,1):
            for p in bins.get((k[0]+a,k[1]+b,k[2]+c),()): best=min(best,float(np.linalg.norm(q-p)))
        hit += best < cell
    return hit/len(truth)

def plane_errors(xyz:np.ndarray)->np.ndarray:
    _,_,w=spec.surface_coordinates(xyz);return np.abs(w)

def make_visual(path:Path,pa:Patch,pb:Patch,mxyz:np.ndarray,support:np.ndarray)->None:
    W,H=1200,420; canvas=np.full((H,W,3),245,np.uint8)
    panels=[("fix A",pa.xyz_h,np.ones(len(pa.xyz_h),bool)),("fix B",pb.xyz_h,np.ones(len(pb.xyz_h),bool)),("fused (dark=2 looks)",mxyz,support>1)]
    for pi,(title,pts,strong) in enumerate(panels):
        x,y,_=spec.surface_coordinates(pts); x0=pi*400
        cv2.rectangle(canvas,(x0+20,35),(x0+380,395),(210,210,210),1);cv2.putText(canvas,title,(x0+35,25),cv2.FONT_HERSHEY_SIMPLEX,.55,(20,20,20),1,cv2.LINE_AA)
        px=np.clip(((x/spec.OBJECT_WIDTH_M)+.5)*340+x0+30,x0+30,x0+370).astype(int);py=np.clip((.5-y/spec.OBJECT_HEIGHT_M)*340+45,45,385).astype(int)
        for X,Y,S in zip(px[::2],py[::2],strong[::2]): canvas[Y,X]=(30,30,30) if S else (145,145,145)
    cv2.imwrite(str(path),canvas)

def evaluate(root:Path,out:Path,mode:str)->dict:
    if out.exists(): raise FileExistsError("output must be new")
    out.mkdir(parents=True); check_kernel_equivalence()
    run=json.loads((root/"run.json").read_text()); profile=run["profile"]
    if run.get("fsg2_spec_sha256")!=spec.spec_digest() or run.get("seed")!=spec.SEED: raise ValueError("record not from frozen FSG2 specification")
    recs={}; metas={}; patches={}; coverage={}
    for name in spec.CASES:
        c,obs=hdr.read_observation(root/name); rec,meta,_=compute_once(c,obs); recs[name]=rec;metas[name]=meta;patches[name]=patch_from_record(name,rec)
        ref=object_reference_mask(rec); coverage[name]=float((rec["valid"]&ref).sum()/max(1,ref.sum()))
    pa,pb=patches["fix_left"],patches["fix_right"]
    sm=initialize(pa,spec.OBJECT_ID)
    sm2,assoc=fuse(sm,pb,spec.OBJECT_ID,spec.FUSION["association_radius_m"],spec.FUSION["hash_cell_m"])
    # Idempotence is a hard map invariant.
    sm3,dup=fuse(sm2,pb,spec.OBJECT_ID,spec.FUSION["association_radius_m"],spec.FUSION["hash_cell_m"])
    if not dup["duplicate_patch"] or not np.array_equal(sm2.xyz_h,sm3.xyz_h): raise AssertionError("duplicate patch changes persistent map")
    # Freeze RGB-derived predictions before consulting analytic scene geometry.
    np.savez_compressed(out/"patch_fix_left.npz",xyz_h=pa.xyz_h.astype(np.float32),rgb=pa.rgb.astype(np.float32),instance_id=pa.instance_id)
    np.savez_compressed(out/"patch_fix_right.npz",xyz_h=pb.xyz_h.astype(np.float32),rgb=pb.rgb.astype(np.float32),instance_id=pb.instance_id)
    save_map(out/"surface_map.npz",sm2)
    json_write(out/"prediction_manifest.json",{"instrument":INSTRUMENT_ID,"matched_points":assoc["matched"],"new_points_second":assoc["new"],"truth_opened":False})
    cov_a=spatial_coverage(sm.xyz_h);cov_f=spatial_coverage(sm2.xyz_h)
    d=assoc["distances_m"]; pe=plane_errors(sm2.xyz_h)
    metrics={
      "schema":"FSG2-evaluation-v1","profile":profile,"instrument":INSTRUMENT_ID,"patch_coverage":coverage,
      "patch_points":{"fix_left":len(pa.xyz_h),"fix_right":len(pb.xyz_h)},"matched_points":assoc["matched"],"new_points_second":assoc["new"],
      "second_patch_new_fraction":assoc["new"]/max(1,assoc["input_points"]),"overlap_median_distance_m":float(np.median(d)) if len(d) else None,
      "overlap_p95_distance_m":float(np.percentile(d,95)) if len(d) else None,"map_points":len(sm2.xyz_h),"map_support2_points":int((sm2.support_count>1).sum()),
      "map_point_plane_median_m":float(np.median(pe)),"map_point_plane_p95_m":float(np.percentile(pe,95)),
      "truth_coverage_first":cov_a,"truth_coverage_fused":cov_f,"truth_coverage_gain":cov_f-cov_a,"idempotent_replay":True,
    }
    t=spec.TARGETS;fails=[]
    for name,v in coverage.items():
        if v<t["patch_object_coverage_min"]: fails.append(f"{name} object coverage {v:.6f} < {t['patch_object_coverage_min']}")
    if assoc["matched"]<t["minimum_matched_points"]:fails.append("too few overlap matches")
    if metrics["second_patch_new_fraction"]<t["minimum_second_patch_new_fraction"]:fails.append("second patch does not extend surface enough")
    if metrics["overlap_median_distance_m"]>t["overlap_median_distance_max_m"]:fails.append("overlap median disagreement")
    if metrics["overlap_p95_distance_m"]>t["overlap_p95_distance_max_m"]:fails.append("overlap p95 disagreement")
    if metrics["map_point_plane_median_m"]>t["map_point_plane_median_max_m"]:fails.append("fused map median plane error")
    if metrics["map_point_plane_p95_m"]>t["map_point_plane_p95_max_m"]:fails.append("fused map p95 plane error")
    if metrics["truth_coverage_fused"]<t["fused_truth_coverage_min"]:fails.append("fused visible-surface completeness")
    if metrics["truth_coverage_gain"]<t["fused_truth_coverage_gain_min"]:fails.append("insufficient surface extension over first patch")
    metrics["fails"]=fails;metrics["status"]="FSG2_INCREMENT2_PASS" if not fails else "FSG2_INCREMENT2_FAIL"
    write_ply(out/"surface_map.ply",sm2.xyz_h,sm2.rgb,sm2.support_count);make_visual(out/"fusion.png",pa,pb,sm2.xyz_h,sm2.support_count);json_write(out/"metrics.json",metrics)
    print("[fsg2-eval] "+metrics["status"],json.dumps(metrics,sort_keys=True),flush=True)
    return metrics

def main()->None:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("record",type=Path);ap.add_argument("--out",type=Path,required=True);ap.add_argument("--mode",choices=("smoke","full"),required=True);a=ap.parse_args()
    m=evaluate(a.record.resolve(),a.out.resolve(),a.mode);raise SystemExit(0 if not m["fails"] else 2)
if __name__=="__main__":main()
