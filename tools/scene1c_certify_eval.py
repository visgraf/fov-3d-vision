"""Post-hoc evaluation of one Scene-1c component certification control."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
import scene1c_public as public
import scene1c_scene as scene
from fsg3_surface_map import load_map
from fsg_geometry import json_write


def spatial_coverage(fixture:str,object_id:int,xyz:np.ndarray)->float:
    truth=scene.truth_points(fixture,object_id); cell=scene.TRUTH_COVER_RADIUS_M; bins={}
    for p in np.asarray(xyz,float):
        if np.isfinite(p).all(): bins.setdefault(tuple(np.floor(p/cell).astype(int)),[]).append(p)
    hit=0
    for q in truth:
        k=tuple(np.floor(q/cell).astype(int)); best=cell
        for a in (-1,0,1):
            for b in (-1,0,1):
                for c in (-1,0,1):
                    for p in bins.get((k[0]+a,k[1]+b,k[2]+c),()): best=min(best,float(np.linalg.norm(q-p)))
        hit += best < cell
    return float(hit/len(truth))


def evaluate(root:Path,out:Path,mode:str)->dict:
    root=root.resolve(); out=out.resolve()
    if out.exists(): raise FileExistsError("output must be new")
    manifest=json.loads((root/"prediction_manifest.json").read_text())
    if manifest.get("truth_opened") is not False or manifest.get("public_spec_sha256")!=public.public_digest(): raise ValueError("component prediction provenance invalid")
    fixture=manifest.get("fixture"); seed=int(manifest.get("seed")); oid=int(manifest.get("object_id"))
    if fixture not in public.FIXTURES or seed not in public.SEEDS or oid not in public.OBJECT_IDS or manifest.get("instrument")!=public.INSTRUMENT_ID: raise ValueError("wrong Scene-1c component fixture/seed/object/instrument")
    if manifest.get("complete_three_object_scene_rendered") is not True or manifest.get("fixed_head") is not True or manifest.get("static_scene") is not True: raise ValueError("component control context invalid")
    gazes=[tuple(map(float,g)) for g in manifest["fixation_gazes_deg"]]
    for step,g in enumerate(gazes):
        acq=root/"acquisitions"/f"fix_{step:02d}"; case=acq/f"fix_{step:02d}"; rr=json.loads((acq/"run.json").read_text())
        if rr.get("truth_spec_sha256")!=scene.truth_digest(fixture) or rr.get("fixture")!=fixture or int(rr.get("seed"))!=seed or int(rr.get("target_object_id"))!=oid or abs(float(rr["yaw_deg"])-g[0])>1e-8 or abs(float(rr["pitch_deg"])-g[1])>1e-8: raise ValueError("component acquisition mismatch")
        with np.load(case/"evaluation_only"/"mesh.npz",allow_pickle=False) as f: mesh={k:f[k] for k in f.files}
        scene.validate_mesh(fixture,mesh)
    out.mkdir(parents=True); t=public.TARGETS; fails=[]
    final=load_map(root/"surface_map.npz"); seed_map=load_map(root/"maps"/"map_00.npz")
    cov_seed=spatial_coverage(fixture,oid,seed_map.xyz_h); cov_final=spatial_coverage(fixture,oid,final.xyz_h); err=scene.surface_distance(fixture,oid,final.xyz_h)
    supported=final.support_count>=2; sc=int(supported.sum()); radial=scene.signed_radial_error(fixture,oid,final.xyz_h); rb=None if sc==0 else float(np.median(radial[supported]))
    assoc=manifest["association_stats"]; post=[r for r in assoc if int(r["step"])>0]
    if set(final.instance_id.tolist())!={oid}: fails.append("component map purity")
    if sc<t["supported_surfels_min_each_object"]: fails.append("component too few multi-look surfels")
    med=float(np.median(err)); p95=float(np.percentile(err,95))
    if med>t["map_surface_median_max_m"]: fails.append("component final map median surface error")
    if p95>t["map_surface_p95_max_m"]: fails.append("component final map p95 surface error")
    if cov_final<t["final_truth_coverage_min_each_object"]: fails.append("component final coverage")
    if cov_final-cov_seed<t["truth_coverage_gain_over_seed_min_each_object"]: fails.append("component coverage gain over seed")
    if len(post)<t["minimum_postseed_target_fixations_each_object"]: fails.append("component lacks autonomous post-seed fixation")
    for r in assoc:
        if int(r["object_reference_count"])<100: fails.append(f"component fix_{int(r['step']):02d} too little oracle support")
        if r["object_measurement_fraction"] is None or float(r["object_measurement_fraction"])<t["patch_object_coverage_min"]: fails.append(f"component fix_{int(r['step']):02d} measurement coverage")
        if not bool(r.get("idempotent_replay",False)): fails.append(f"component fix_{int(r['step']):02d} replay not idempotent")
    for r in post:
        if int(r["matched"])<t["minimum_matched_points_each_targeted_postseed"]: fails.append(f"component fix_{int(r['step']):02d} too few overlap matches")
        if r["overlap_median_distance_m"] is None or float(r["overlap_median_distance_m"])>t["overlap_median_distance_max_m"]: fails.append(f"component fix_{int(r['step']):02d} overlap median")
        if r["overlap_p95_distance_m"] is None or float(r["overlap_p95_distance_m"])>t["overlap_p95_distance_max_m"]: fails.append(f"component fix_{int(r['step']):02d} overlap p95")
    fs=manifest.get("final_object_policy_state",{})
    if manifest.get("termination_reason")!="no_frontier" or not bool(fs.get("stop",False)) or fs.get("reason")!="no_frontier": fails.append("component did not independently terminate no_frontier")
    if len(gazes)>public.PER_OBJECT_MAX_FIXATIONS: fails.append("component exceeded frozen six-look budget")
    if len({(round(a,8),round(b,8)) for a,b in gazes})!=len(gazes): fails.append("component revisited a physical fixation")
    metrics={"schema":"Scene1c-component-evaluation-v1","profile":manifest["profile"],"fixture":fixture,"seed":seed,"object_id":oid,"fixation_count":len(gazes),"fixation_gazes_deg":[list(g) for g in gazes],"termination_reason":manifest["termination_reason"],
             "seed_truth_coverage":cov_seed,"final_truth_coverage":cov_final,"coverage_gain_over_seed":cov_final-cov_seed,"map_points":int(len(final.xyz_h)),"supported_surfels":sc,"map_surface_median_m":med,"map_surface_p95_m":p95,"supported_signed_radial_median_m":rb,
             "map_support_histogram":{str(int(k)):int(v) for k,v in zip(*np.unique(final.support_count,return_counts=True))},"association_stats":assoc,"primary_camera_samples":int(manifest["primary_camera_samples"]),"fails":fails}
    metrics["status"]="SCENE1C_COMPONENT_RUN_PASS" if not fails else "SCENE1C_COMPONENT_RUN_FAIL"
    json_write(out/"metrics.json",metrics); print("[scene1c-certify-eval] "+metrics["status"],json.dumps(metrics,sort_keys=True),flush=True); return metrics


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("record",type=Path); ap.add_argument("--out",type=Path,required=True); ap.add_argument("--mode",choices=("smoke","full"),required=True); a=ap.parse_args(); m=evaluate(a.record,a.out,a.mode); raise SystemExit(0 if not m["fails"] else 2)
if __name__=="__main__": main()
