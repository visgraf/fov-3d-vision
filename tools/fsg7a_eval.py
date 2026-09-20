"""Post-hoc evaluator for FSG7a prescribed head-motion self-occlusion trials."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
import cv2
import fsg7a_public as public
import fsg7a_scene as scene
from fsg3_surface_map import load_map
from fsg_geometry import json_write

def combined_coverage(fixture,xyz):
    a=scene.truth_part_points(fixture,"front"); b=scene.truth_part_points(fixture,"return"); ca=scene.part_coverage(fixture,"front",xyz); cb=scene.part_coverage(fixture,"return",xyz); return float((len(a)*ca+len(b)*cb)/(len(a)+len(b)))

def write_visual(path,fixture,maps,metrics):
    W=760; H=360; canvas=np.full((H,W,3),245,np.uint8); colors=[(110,110,110),(20,20,20)]
    for k,m in enumerate(maps):
        x0=30+360*k; x=m.xyz_h[:,0]; z=m.xyz_h[:,2]; px=np.clip((x+.75)/1.5*300+x0,x0,x0+300).astype(int); py=np.clip((-z-2.2)/1.3*250+60,60,310).astype(int)
        cv2.rectangle(canvas,(x0,50),(x0+300,320),(205,205,205),1); cv2.putText(canvas,"H0 seed" if k==0 else "after head translation",(x0,25),cv2.FONT_HERSHEY_SIMPLEX,.48,(20,20,20),1,cv2.LINE_AA)
        for X,Y in zip(px[::2],py[::2]): canvas[Y,X]=colors[k]
    cv2.putText(canvas,f"front {100*metrics['front_coverage_final']:.1f}%  return {100*metrics['return_coverage_final']:.1f}%",(30,345),cv2.FONT_HERSHEY_SIMPLEX,.48,(20,20,20),1,cv2.LINE_AA); cv2.imwrite(str(path),canvas)

def evaluate(root:Path,out:Path,mode:str)->dict:
    root=root.resolve(); out=out.resolve()
    if out.exists(): raise FileExistsError("output must be new")
    mfest=json.loads((root/"prediction_manifest.json").read_text())
    if mfest.get("truth_opened") is not False or mfest.get("public_spec_sha256")!=public.public_digest(): raise ValueError("prediction provenance invalid")
    f=mfest.get("fixture"); seed=int(mfest.get("seed"));
    if f not in public.FIXTURES or seed not in public.SEEDS or mfest.get("instrument")!=public.INSTRUMENT_ID: raise ValueError("wrong FSG7a fixture/seed/instrument")
    if len(mfest.get("views",[]))!=2: raise ValueError("FSG7a requires exactly two prescribed views")
    maps=[]
    for step in range(2):
        v=public.view(f,step); got=mfest["views"][step]
        if got["role"]!=v["role"] or not np.allclose(got["head_translation_h0_m"],v["head_translation_h0_m"],atol=1e-9) or not np.allclose(got["gaze_yaw_pitch_deg"],v["gaze_yaw_pitch_deg"],atol=1e-9): raise ValueError("view schedule mismatch")
        maps.append(load_map(root/"maps"/f"map_{step:02d}.npz")); acq=root/"acquisitions"/f"fix_{step:02d}"; case=acq/f"fix_{step:02d}"; rr=json.loads((acq/"run.json").read_text())
        if rr.get("truth_spec_sha256")!=scene.truth_digest(f) or not np.allclose(rr["head_translation_h0_m"],v["head_translation_h0_m"],atol=1e-9): raise ValueError("acquisition truth/motion mismatch")
        with np.load(case/"evaluation_only"/"mesh.npz",allow_pickle=False) as z: mesh={k:z[k] for k in z.files}
        scene.validate_mesh(f,mesh,v["head_translation_h0_m"])
    seed_map,final=maps; err=scene.surface_distance(f,final.xyz_h); front0=scene.part_coverage(f,"front",seed_map.xyz_h); ret0=scene.part_coverage(f,"return",seed_map.xyz_h); front1=scene.part_coverage(f,"front",final.xyz_h); ret1=scene.part_coverage(f,"return",final.xyz_h); overall=combined_coverage(f,final.xyz_h)
    fixed=scene.binocular_return_visibility(f,(0,0,0)); moved=scene.binocular_return_visibility(f,public.view(f,1)["head_translation_h0_m"]); supported=int((final.support_count>=2).sum())
    metrics={"schema":"FSG7a-run-evaluation-v1","profile":mfest["profile"],"fixture":f,"seed":seed,"views":mfest["views"],"patch_stats":mfest["patch_stats"],"association_stats":mfest["association_stats"],"map_points":int(len(final.xyz_h)),"supported_surfels":supported,"map_surface_median_m":float(np.median(err)),"map_surface_p95_m":float(np.percentile(err,95)),"front_coverage_seed":front0,"return_coverage_seed":ret0,"front_coverage_final":front1,"return_coverage_final":ret1,"return_coverage_gain":ret1-ret0,"final_truth_coverage":overall,"fixed_head_return_visibility":fixed,"moved_head_return_visibility":moved,"primary_camera_samples":int(mfest["primary_camera_samples"])}
    t=public.TARGETS; fails=[]
    if metrics["map_surface_median_m"]>t["map_surface_median_max_m"]: fails.append("final map median folded-surface error")
    if metrics["map_surface_p95_m"]>t["map_surface_p95_max_m"]: fails.append("final map p95 folded-surface error")
    if set(final.instance_id.tolist())!={public.OBJECT_ID}: fails.append("map contains non-object instance")
    if supported<t["supported_surfels_min"]: fails.append("too few multi-look surfels")
    if front0<t["front_seed_coverage_min"]: fails.append("seed does not reconstruct front wing")
    if ret0>t["return_seed_coverage_max"]: fails.append("supposedly hidden return already reconstructed at H0")
    if ret1<t["return_final_coverage_min"]: fails.append("head motion failed to reconstruct hidden return")
    if ret1-ret0<t["return_coverage_gain_min"]: fails.append("hidden return coverage gain too small")
    if overall<t["final_truth_coverage_min"]: fails.append("final folded-object coverage")
    if fixed["either_max"]>t["fixed_head_return_visibility_max"]: fails.append("return is not genuinely self-occluded at fixed head")
    if moved["both_min"]<t["moved_head_return_visibility_min"]: fails.append("prescribed head motion does not reveal return binocularly")
    for p in mfest["patch_stats"]:
        if p["object_reference_count"]<100: fails.append(f"{p['patch_id']} too little oracle object support")
        if p["object_measurement_fraction"] is None or p["object_measurement_fraction"]<t["patch_object_coverage_min"]: fails.append(f"{p['patch_id']} object measurement coverage")
    a=mfest["association_stats"][1]
    if a["matched"]<t["minimum_matched_points_reveal"]: fails.append("reveal patch too few fixed-frame overlap matches")
    if a["overlap_median_distance_m"] is None or a["overlap_median_distance_m"]>t["overlap_median_distance_max_m"]: fails.append("reveal patch fixed-frame overlap median")
    if a["overlap_p95_distance_m"] is None or a["overlap_p95_distance_m"]>t["overlap_p95_distance_max_m"]: fails.append("reveal patch fixed-frame overlap p95")
    if not a.get("idempotent_replay",False): fails.append("reveal patch replay not idempotent")
    metrics["fails"]=fails; metrics["status"]="FSG7A_HEAD_MOTION_RUN_PASS" if not fails else "FSG7A_HEAD_MOTION_RUN_FAIL"; out.mkdir(parents=True); json_write(out/"metrics.json",metrics); write_visual(out/"growth_truth.png",f,maps,metrics); print("[fsg7a-eval] "+metrics["status"],json.dumps(metrics,sort_keys=True),flush=True); return metrics

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("record",type=Path); ap.add_argument("--out",type=Path,required=True); ap.add_argument("--mode",choices=("smoke","full"),required=True); a=ap.parse_args(); m=evaluate(a.record,a.out,a.mode); raise SystemExit(0 if not m["fails"] else 2)
if __name__=="__main__": main()
