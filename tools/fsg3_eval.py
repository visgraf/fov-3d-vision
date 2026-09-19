"""Post-hoc evaluation of FSG3 active frontier growth.

The active loop must have completed and saved its prediction manifest with
truth_opened=false before this script imports the fixture geometry. Evaluation
never changes the map or policy trajectory.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np, cv2
import fsg3_public as public
import fsg3_scene as scene
from fsg3_surface_map import load_map
from fsg_geometry import json_write


def truth_points()->np.ndarray:
    nx,ny=scene.TRUTH_GRID_WH
    xs=np.linspace(-scene.OBJECT_WIDTH_M/2,scene.OBJECT_WIDTH_M/2,nx);ys=np.linspace(-scene.OBJECT_HEIGHT_M/2,scene.OBJECT_HEIGHT_M/2,ny)
    X,Y=np.meshgrid(xs,ys);r,u,_=scene.object_axes()
    return (scene.OBJECT_CENTRE+X[...,None]*r+Y[...,None]*u).reshape(-1,3)

def spatial_coverage(xyz:np.ndarray)->float:
    truth=truth_points();cell=scene.TRUTH_COVER_RADIUS_M;bins={}
    for p in np.asarray(xyz,float):
        if np.isfinite(p).all():bins.setdefault(tuple(np.floor(p/cell).astype(int)),[]).append(p)
    hit=0
    for q in truth:
        k=tuple(np.floor(q/cell).astype(int));best=cell
        for a in (-1,0,1):
          for b in (-1,0,1):
            for c in (-1,0,1):
              for p in bins.get((k[0]+a,k[1]+b,k[2]+c),()):best=min(best,float(np.linalg.norm(q-p)))
        hit += best < cell
    return float(hit/len(truth))

def plane_errors(xyz:np.ndarray)->np.ndarray:
    _,_,w=scene.surface_coordinates(np.asarray(xyz,float));return np.abs(w)

def write_visual(path:Path,maps:list,coverage:list[float],yaws:list[float])->None:
    n=len(maps);W=300*n;H=330;canvas=np.full((H,W,3),245,np.uint8)
    for k,(m,cov,yaw) in enumerate(zip(maps,coverage,yaws)):
        x,y,_=scene.surface_coordinates(m.xyz_h);x0=300*k
        cv2.rectangle(canvas,(x0+20,45),(x0+280,285),(210,210,210),1)
        cv2.putText(canvas,f"{k}: yaw {yaw:.1f}",(x0+25,20),cv2.FONT_HERSHEY_SIMPLEX,.45,(20,20,20),1,cv2.LINE_AA)
        cv2.putText(canvas,f"coverage {100*cov:.1f}%",(x0+25,38),cv2.FONT_HERSHEY_SIMPLEX,.42,(20,20,20),1,cv2.LINE_AA)
        px=np.clip(((x/scene.OBJECT_WIDTH_M)+.5)*240+x0+30,x0+30,x0+270).astype(int);py=np.clip((.5-y/scene.OBJECT_HEIGHT_M)*210+60,60,270).astype(int)
        strong=m.support_count>1
        for X,Y,S in zip(px[::2],py[::2],strong[::2]):canvas[Y,X]=(25,25,25) if S else (145,145,145)
    cv2.imwrite(str(path),canvas)

def evaluate(root:Path,out:Path,mode:str)->dict:
    root=root.resolve();out=out.resolve()
    if out.exists():raise FileExistsError("output must be new")
    manifest=json.loads((root/"prediction_manifest.json").read_text())
    if manifest.get("truth_opened") is not False or manifest.get("public_spec_sha256")!=public.public_digest():
        raise ValueError("prediction provenance invalid")
    if manifest.get("instrument")!=public.INSTRUMENT_ID or manifest.get("seed")!=public.SEED:
        raise ValueError("wrong instrument or seed")
    yaws=[float(x) for x in manifest["fixation_yaws_deg"]];n=len(yaws)
    maps=[]
    for step in range(n):
        maps.append(load_map(root/"maps"/f"map_{step:02d}.npz"))
        acq=root/"acquisitions"/f"fix_{step:02d}";case=acq/f"fix_{step:02d}"
        rr=json.loads((acq/"run.json").read_text())
        if rr.get("truth_spec_sha256")!=scene.truth_digest() or abs(float(rr["yaw_deg"])-yaws[step])>1e-8:
            raise ValueError("acquisition truth spec/yaw mismatch")
        with np.load(case/"evaluation_only"/"mesh.npz",allow_pickle=False) as f:mesh={k:f[k] for k in f.files}
        scene.validate_mesh(mesh)
    out.mkdir(parents=True)
    cov=[spatial_coverage(m.xyz_h) for m in maps]
    gains=[cov[0]]+[cov[i]-cov[i-1] for i in range(1,n)]
    final=maps[-1];pe=plane_errors(final.xyz_h);patch=manifest["patch_stats"];assoc=manifest["association_stats"]
    metrics={"schema":"FSG3-evaluation-v1","profile":manifest["profile"],"instrument":manifest["instrument"],"fixation_count":n,"fixation_yaws_deg":yaws,"termination_reason":manifest["termination_reason"],"patch_stats":patch,"association_stats":assoc,"truth_coverage_by_fixation":cov,"truth_coverage_gain_by_fixation":gains,"truth_coverage_seed":cov[0],"truth_coverage_final":cov[-1],"truth_coverage_gain_over_seed":cov[-1]-cov[0],"map_points":int(len(final.xyz_h)),"map_support_histogram":{str(int(k)):int(v) for k,v in zip(*np.unique(final.support_count,return_counts=True))},"map_point_plane_median_m":float(np.median(pe)),"map_point_plane_p95_m":float(np.percentile(pe,95)),"primary_camera_samples":int(manifest["primary_camera_samples"])}
    t=public.TARGETS;fails=[]
    if not (t["fixation_count_min"]<=n<=t["fixation_count_max"]):fails.append("fixation count outside prospective range")
    if manifest["termination_reason"]!="no_frontier":fails.append("policy did not terminate by resolving the frontier")
    dy=np.abs(np.diff(yaws))
    if len(dy) and (np.any(dy<=0) or np.any(dy>public.POLICY["step_deg"]+1e-8)):fails.append("saccade exceeds frozen local step or revisits")
    for p in patch:
        if p["object_measurement_fraction"]<t["patch_object_coverage_min"]:fails.append(f"{p['patch_id']} object measurement coverage")
    for i,a in enumerate(assoc[1:], start=1):
        if a["matched"]<t["minimum_matched_points_each"]:fails.append(f"{a['patch_id']} too few overlap matches")
        min_new=t["minimum_new_fraction_terminal"] if i==n-1 else t["minimum_new_fraction_nonterminal"]
        if a["new_fraction"]<min_new:fails.append(f"{a['patch_id']} too little new surface")
        if a["overlap_median_distance_m"] is None or a["overlap_median_distance_m"]>t["overlap_median_distance_max_m"]:fails.append(f"{a['patch_id']} overlap median")
        if a["overlap_p95_distance_m"] is None or a["overlap_p95_distance_m"]>t["overlap_p95_distance_max_m"]:fails.append(f"{a['patch_id']} overlap p95")
        if not a["idempotent_replay"]:fails.append(f"{a['patch_id']} replay not idempotent")
    if metrics["map_point_plane_median_m"]>t["map_point_plane_median_max_m"]:fails.append("final map median plane error")
    if metrics["map_point_plane_p95_m"]>t["map_point_plane_p95_max_m"]:fails.append("final map p95 plane error")
    if cov[-1]<t["final_truth_coverage_min"]:fails.append("final visible-surface coverage")
    if cov[-1]-cov[0]<t["truth_coverage_gain_over_seed_min"]:fails.append("insufficient coverage growth over seed")
    for i in range(1,n):
        if gains[i] < -t["coverage_drop_tolerance"]:fails.append(f"coverage decreased materially at fixation {i}")
        min_gain=t["minimum_incremental_coverage_gain_terminal"] if i==n-1 else t["minimum_incremental_coverage_gain_nonterminal"]
        if gains[i] < min_gain:fails.append(f"fixation {i} added too little visible surface")
    if set(final.instance_id.tolist())!={public.OBJECT_ID}:fails.append("map contains non-object instance")
    metrics["fails"]=fails;metrics["status"]="FSG3_INCREMENT3_PASS" if not fails else "FSG3_INCREMENT3_FAIL"
    json_write(out/"metrics.json",metrics);write_visual(out/"growth_truth.png",maps,cov,yaws)
    print("[fsg3-eval] "+metrics["status"],json.dumps(metrics,sort_keys=True),flush=True)
    return metrics

def main()->None:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("record",type=Path);ap.add_argument("--out",type=Path,required=True);ap.add_argument("--mode",choices=("smoke","full"),required=True);a=ap.parse_args()
    m=evaluate(a.record,a.out,a.mode);raise SystemExit(0 if not m["fails"] else 2)
if __name__=="__main__":main()
