"""Post-hoc evaluation for one Stage II / Scene-1a multi-object run."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
import scene1a_public as public
import scene1a_scene as scene
import scene1a_policy as scene_policy
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


def _seed_step(fixture:str,oid:int)->int:
    for i,(o,_g) in enumerate(public.SEED_SEQUENCE[fixture]):
        if int(o)==int(oid): return i
    raise ValueError("object has no prescribed seed")


def evaluate(root:Path,out:Path,mode:str)->dict:
    root=root.resolve(); out=out.resolve()
    if out.exists(): raise FileExistsError("output must be new")
    manifest=json.loads((root/"prediction_manifest.json").read_text())
    if manifest.get("truth_opened") is not False or manifest.get("public_spec_sha256")!=public.public_digest(): raise ValueError("prediction provenance invalid")
    fixture=manifest.get("fixture"); seed=int(manifest.get("seed"))
    if fixture not in public.FIXTURES or seed not in public.SEEDS or manifest.get("instrument")!=public.INSTRUMENT_ID: raise ValueError("wrong Scene-1a fixture/seed/instrument")
    if manifest.get("fixed_head") is not True or manifest.get("static_scene") is not True: raise ValueError("Scene-1a base assumptions violated")
    gazes=[tuple(map(float,g)) for g in manifest["fixation_gazes_deg"]]; targets=[int(x) for x in manifest["target_object_sequence"]]
    if len(gazes)!=len(targets): raise ValueError("gaze/target sequence mismatch")
    for step,(g,target) in enumerate(zip(gazes,targets)):
        acq=root/"acquisitions"/f"fix_{step:02d}"; case=acq/f"fix_{step:02d}"; rr=json.loads((acq/"run.json").read_text())
        if rr.get("truth_spec_sha256")!=scene.truth_digest(fixture) or rr.get("fixture")!=fixture or int(rr.get("seed"))!=seed or int(rr.get("target_object_id"))!=target or abs(float(rr["yaw_deg"])-g[0])>1e-8 or abs(float(rr["pitch_deg"])-g[1])>1e-8:
            raise ValueError("acquisition truth spec/fixture/seed/target/gaze mismatch")
        with np.load(case/"evaluation_only"/"mesh.npz",allow_pickle=False) as f: mesh={k:f[k] for k in f.files}
        scene.validate_mesh(fixture,mesh)
    trace=json.loads((root/"scene_policy_trace.json").read_text())["trace"]
    out.mkdir(parents=True)
    objects={}; fails=[]; t=public.TARGETS
    assoc=manifest["association_stats"]
    opportunistic=sum(bool(r.get("fused")) and not bool(r.get("targeted")) for r in assoc)
    for oid in public.OBJECT_IDS:
        final=load_map(root/f"object_{oid}_surface_map.npz"); ss=_seed_step(fixture,oid); seed_map=load_map(root/"maps"/f"obj_{oid}"/f"map_{ss:02d}.npz")
        cov_seed=spatial_coverage(fixture,oid,seed_map.xyz_h); cov_final=spatial_coverage(fixture,oid,final.xyz_h); err=scene.surface_distance(fixture,oid,final.xyz_h)
        supported=final.support_count>=2; sc=int(supported.sum()); radial=scene.signed_radial_error(fixture,oid,final.xyz_h); rb=None if radial is None or sc==0 else float(np.median(radial[supported]))
        target_steps=[i for i,x in enumerate(targets) if x==oid]; post=[r for r in assoc if int(r["object_id"])==oid and bool(r["targeted"]) and int(r["step"])!=ss]
        obj={"object_id":oid,"type":scene.spec(fixture,oid)["type"],"target_fixation_steps":target_steps,"postseed_target_fixations":len(post),"seed_truth_coverage":cov_seed,"final_truth_coverage":cov_final,"coverage_gain_over_seed":cov_final-cov_seed,
             "map_points":int(len(final.xyz_h)),"supported_surfels":sc,"map_surface_median_m":float(np.median(err)),"map_surface_p95_m":float(np.percentile(err,95)),"supported_signed_radial_median_m":rb,
             "map_support_histogram":{str(int(k)):int(v) for k,v in zip(*np.unique(final.support_count,return_counts=True))}}
        objects[str(oid)]=obj
        if set(final.instance_id.tolist())!={oid}: fails.append(f"object {oid} map purity")
        if sc<t["supported_surfels_min_each_object"]: fails.append(f"object {oid} too few multi-look surfels")
        if obj["map_surface_median_m"]>t["map_surface_median_max_m"]: fails.append(f"object {oid} final map median surface error")
        if obj["map_surface_p95_m"]>t["map_surface_p95_max_m"]: fails.append(f"object {oid} final map p95 surface error")
        if cov_final<t["final_truth_coverage_min_each_object"]: fails.append(f"object {oid} final coverage")
        if cov_final-cov_seed<t["truth_coverage_gain_over_seed_min_each_object"]: fails.append(f"object {oid} coverage gain over seed")
        if len(post)<t["minimum_postseed_target_fixations_each_object"]: fails.append(f"object {oid} was not actively revisited after seed")
        for r in [x for x in assoc if int(x["object_id"])==oid and bool(x["targeted"])]:
            if int(r["object_reference_count"])<100: fails.append(f"target object {oid} fix_{int(r['step']):02d} too little oracle support")
            if r["object_measurement_fraction"] is None or float(r["object_measurement_fraction"])<t["patch_object_coverage_min"]: fails.append(f"target object {oid} fix_{int(r['step']):02d} measurement coverage")
        for r in post:
            if int(r["matched"])<t["minimum_matched_points_each_targeted_postseed"]: fails.append(f"object {oid} fix_{int(r['step']):02d} too few overlap matches")
            if r["overlap_median_distance_m"] is None or float(r["overlap_median_distance_m"])>t["overlap_median_distance_max_m"]: fails.append(f"object {oid} fix_{int(r['step']):02d} overlap median")
            if r["overlap_p95_distance_m"] is None or float(r["overlap_p95_distance_m"])>t["overlap_p95_distance_max_m"]: fails.append(f"object {oid} fix_{int(r['step']):02d} overlap p95")
    for r in assoc:
        if bool(r.get("fused")) and not bool(r.get("idempotent_replay",False)): fails.append(f"object {r['object_id']} fix_{int(r['step']):02d} replay not idempotent")
    if manifest.get("termination_reason")!="scene_complete": fails.append("scene scheduler did not terminate with all objects complete")
    final_states=manifest.get("final_object_policy_states",{})
    for oid in public.OBJECT_IDS:
        s=final_states.get(str(oid),{})
        if not bool(s.get("stop",False)) or s.get("reason")!="no_frontier": fails.append(f"object {oid} did not independently terminate no_frontier")
        if int(manifest["target_counts"].get(str(oid),0))>public.PER_OBJECT_MAX_FIXATIONS: fails.append(f"object {oid} exceeded frozen per-object budget")
    if len(gazes)>public.MAX_SCENE_FIXATIONS: fails.append("scene exceeded global budget")
    if len({(round(a,8),round(b,8)) for a,b in gazes})!=len(gazes): fails.append("scene revisited a physical fixation")
    active_targets=targets[len(public.OBJECT_IDS):]
    switches=sum(a!=b for a,b in zip(active_targets[:-1],active_targets[1:]))
    if switches<t["minimum_scene_target_switches"]: fails.append("scene did not materially switch attention between objects")
    if set(active_targets)!=set(public.OBJECT_IDS): fails.append("not every object received autonomous post-seed attention")
    # Recompute every scheduler choice from the recorded per-object proposals.
    for j,d in enumerate(trace):
        recomputed=scene_policy.select_proposal(d["proposals"])
        if bool(recomputed["stop"])!=bool(d["stop"]): fails.append(f"scheduler decision {j} stop mismatch")
        if not recomputed["stop"]:
            if int(recomputed["selected_object_id"])!=int(d["selected_object_id"]) or not np.allclose(recomputed["next_gaze_deg"],d["next_gaze_deg"],atol=1e-9): fails.append(f"scheduler decision {j} violates prospective lexicographic rule")
    metrics={"schema":"Scene1a-run-evaluation-v1","profile":manifest["profile"],"fixture":fixture,"seed":seed,"fixation_count":len(gazes),"fixation_gazes_deg":[list(g) for g in gazes],"target_object_sequence":targets,"termination_reason":manifest["termination_reason"],"objects":objects,"scene_min_final_coverage":float(min(o["final_truth_coverage"] for o in objects.values())),"scene_mean_final_coverage":float(np.mean([o["final_truth_coverage"] for o in objects.values()])),"active_target_switches":switches,"opportunistic_fused_updates":int(opportunistic),"primary_camera_samples":int(manifest["primary_camera_samples"]),"fails":fails}
    metrics["status"]="SCENE1A_RUN_PASS" if not fails else "SCENE1A_RUN_FAIL"
    json_write(out/"metrics.json",metrics); print("[scene1a-eval] "+metrics["status"],json.dumps(metrics,sort_keys=True),flush=True); return metrics


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("record",type=Path); ap.add_argument("--out",type=Path,required=True); ap.add_argument("--mode",choices=("smoke","full"),required=True); a=ap.parse_args(); m=evaluate(a.record,a.out,a.mode); raise SystemExit(0 if not m["fails"] else 2)
if __name__=="__main__": main()
