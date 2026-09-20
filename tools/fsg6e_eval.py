"""Post-hoc evaluation of one FSG6e 3D-frontier active run."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
import cv2
import fsg6e_public as public
import fsg6e_scene as scene
from fsg3_surface_map import load_map
from fsg_geometry import json_write


def spatial_coverage(fixture:str,xyz:np.ndarray)->float:
    truth=scene.truth_points(fixture); cell=scene.TRUTH_COVER_RADIUS_M; bins={}
    for p in np.asarray(xyz,float):
        if np.isfinite(p).all(): bins.setdefault(tuple(np.floor(p/cell).astype(int)),[]).append(p)
    hit=0
    for q in truth:
        k=tuple(np.floor(q/cell).astype(int)); best=cell
        for a in (-1,0,1):
            for b in (-1,0,1):
                for c in (-1,0,1):
                    for p in bins.get((k[0]+a,k[1]+b,k[2]+c),()): best=min(best,float(np.linalg.norm(q-p)))
        hit+=best<cell
    return float(hit/len(truth))

def write_visual(path:Path,fixture:str,maps:list,coverage:list[float],gazes:list[tuple[float,float]])->None:
    n=len(maps); W=300*n; H=330; canvas=np.full((H,W,3),245,np.uint8); truth=scene.truth_points(fixture); ty,tp=scene.angular_coordinates(truth); yl,yh=ty.min(),ty.max(); pl,ph=tp.min(),tp.max()
    for k,(m,cov,g) in enumerate(zip(maps,coverage,gazes)):
        y,p=scene.angular_coordinates(m.xyz_h); x0=300*k; cv2.rectangle(canvas,(x0+20,45),(x0+280,285),(210,210,210),1); cv2.putText(canvas,f"{k}: {g[0]:.1f},{g[1]:.1f}",(x0+25,20),cv2.FONT_HERSHEY_SIMPLEX,.42,(20,20,20),1,cv2.LINE_AA); cv2.putText(canvas,f"coverage {100*cov:.1f}%",(x0+25,38),cv2.FONT_HERSHEY_SIMPLEX,.42,(20,20,20),1,cv2.LINE_AA)
        px=np.clip((y-yl)/max(1e-9,yh-yl)*240+x0+30,x0+30,x0+270).astype(int); py=np.clip((ph-p)/max(1e-9,ph-pl)*210+60,60,270).astype(int); strong=m.support_count>1
        for X,Y,S in zip(px[::2],py[::2],strong[::2]): canvas[Y,X]=(25,25,25) if S else (145,145,145)
    cv2.imwrite(str(path),canvas)

def evaluate(root:Path,out:Path,mode:str)->dict:
    root=root.resolve(); out=out.resolve()
    if out.exists(): raise FileExistsError("output must be new")
    manifest=json.loads((root/"prediction_manifest.json").read_text())
    if manifest.get("truth_opened") is not False or manifest.get("public_spec_sha256")!=public.public_digest(): raise ValueError("prediction provenance invalid")
    fixture=manifest.get("fixture"); seed=int(manifest.get("seed"))
    if fixture not in public.FIXTURES or seed not in public.SEEDS or manifest.get("instrument")!=public.INSTRUMENT_ID: raise ValueError("wrong FSG6e fixture/seed/instrument")
    gazes=[tuple(map(float,g)) for g in manifest["fixation_gazes_deg"]]; maps=[]
    for step,(yaw,pitch) in enumerate(gazes):
        maps.append(load_map(root/"maps"/f"map_{step:02d}.npz")); acq=root/"acquisitions"/f"fix_{step:02d}"; case=acq/f"fix_{step:02d}"; rr=json.loads((acq/"run.json").read_text())
        if rr.get("truth_spec_sha256")!=scene.truth_digest(fixture) or rr.get("fixture")!=fixture or int(rr.get("seed"))!=seed or abs(float(rr["yaw_deg"])-yaw)>1e-8 or abs(float(rr["pitch_deg"])-pitch)>1e-8: raise ValueError("acquisition truth spec/fixture/seed/gaze mismatch")
        with np.load(case/"evaluation_only"/"mesh.npz",allow_pickle=False) as f: mesh={k:f[k] for k in f.files}
        scene.validate_mesh(fixture,mesh)
    out.mkdir(parents=True); cov=[spatial_coverage(fixture,m.xyz_h) for m in maps]; gains=[cov[0]]+[cov[i]-cov[i-1] for i in range(1,len(cov))]; closure=[None]
    for i in range(1,len(cov)):
        rem=max(0,1-cov[i-1]); closure.append(None if rem<=1e-12 else float(gains[i]/rem))
    final=maps[-1]; err=scene.surface_distance(fixture,final.xyz_h); signed=scene.signed_radial_error(fixture,final.xyz_h); supported=final.support_count>=2; sc=int(supported.sum()); sb=float(np.median(signed[supported])) if sc else None
    patch=manifest["patch_stats"]; assoc=manifest["association_stats"]; trace=json.loads((root/"policy_trace.json").read_text())["trace"]
    ys=np.array([g[0] for g in gazes]); ps=np.array([g[1] for g in gazes])
    frontier_state=[{"step":int(d.get("step",i)),"raw":int(d.get("frontier_raw_count",d.get("frontier_count",0))),"map_resolved":int(d.get("frontier_map_resolved_count",0)),"boundary_resolved":int(d.get("frontier_boundary_resolved_count",0)),"open":int(d.get("frontier_open_count",d.get("frontier_count",0))),"candidate_count":int(len(d.get("candidates",[])))} for i,d in enumerate(trace)]
    metrics={"schema":"FSG6e-run-evaluation-v1","profile":manifest["profile"],"fixture":fixture,"seed":seed,"instrument":manifest["instrument"],"fixation_count":len(gazes),"fixation_gazes_deg":[list(g) for g in gazes],"termination_reason":manifest["termination_reason"],"patch_stats":patch,"association_stats":assoc,"policy_trace":trace,"frontier_state_by_fixation":frontier_state,"truth_coverage_by_fixation":cov,"truth_coverage_gain_by_fixation":gains,"residual_closure_fraction_by_fixation":closure,"truth_coverage_seed":cov[0],"truth_coverage_final":cov[-1],"truth_coverage_gain_over_seed":cov[-1]-cov[0],"yaw_span_deg":float(ys.max()-ys.min()),"pitch_span_deg":float(ps.max()-ps.min()),"map_points":int(len(final.xyz_h)),"map_support_histogram":{str(int(k)):int(v) for k,v in zip(*np.unique(final.support_count,return_counts=True))},"map_surface_median_m":float(np.median(err)),"map_surface_p95_m":float(np.percentile(err,95)),"supported_surfels":sc,"supported_signed_radial_median_m":sb,"primary_camera_samples":int(manifest["primary_camera_samples"]),"per_fixation_novelty_and_gain_gated":False}
    t=public.TARGETS; fails=[]
    if metrics["map_surface_median_m"]>t["map_surface_median_max_m"]: fails.append("final map median curved-surface error")
    if metrics["map_surface_p95_m"]>t["map_surface_p95_max_m"]: fails.append("final map p95 curved-surface error")
    if set(final.instance_id.tolist())!={public.OBJECT_ID}: fails.append("map contains non-object instance")
    if sc<t["supported_surfels_min"]: fails.append("too few multi-look surfels")
    elif abs(float(sb))>t["supported_signed_radial_bias_abs_max_m"]: fails.append("multi-look fusion radially biases curved surface")
    if not(t["active_fixation_count_min"]<=len(gazes)<=t["active_fixation_count_max"]): fails.append("active fixation count outside prospective range")
    if manifest["termination_reason"]!="no_frontier": fails.append("3D frontier policy did not terminate by resolving the frontier")
    if metrics["pitch_span_deg"]+1e-9<t["pitch_span_min_deg"]: fails.append("3D frontier policy did not materially change pitch")
    for i in range(1,len(gazes)):
        dy=ys[i]-ys[i-1]; dp=ps[i]-ps[i-1]; s=public.SURFACE_FRONTIER["component_step_deg"]
        if (abs(dy)>s+1e-8 or abs(dp)>s+1e-8 or (abs(dy)<1e-8 and abs(dp)<1e-8) or
            (abs(dy)>1e-8 and abs(abs(dy)-s)>1e-8) or (abs(dp)>1e-8 and abs(abs(dp)-s)>1e-8)):
            fails.append(f"fixation {i} is not one 5-degree yaw/pitch lattice move")
    if len({(round(a,8),round(b,8)) for a,b in gazes})!=len(gazes): fails.append("active policy revisited a fixation")
    for p in patch:
        if p["object_reference_count"]<100: fails.append(f"{p['patch_id']} too little oracle object support")
        if p["object_measurement_fraction"] is None or p["object_measurement_fraction"]<t["patch_object_coverage_min"]: fails.append(f"{p['patch_id']} object measurement coverage")
    for i,a in enumerate(assoc[1:],start=1):
        if a["matched"]<t["minimum_matched_points_each"]: fails.append(f"{a['patch_id']} too few overlap matches")
        if a["overlap_median_distance_m"] is None or a["overlap_median_distance_m"]>t["overlap_median_distance_max_m"]: fails.append(f"{a['patch_id']} overlap median")
        if a["overlap_p95_distance_m"] is None or a["overlap_p95_distance_m"]>t["overlap_p95_distance_max_m"]: fails.append(f"{a['patch_id']} overlap p95")
        if not a.get("idempotent_replay",False): fails.append(f"{a['patch_id']} replay not idempotent")
        if gains[i]<-t["coverage_drop_tolerance"]: fails.append(f"coverage decreased materially at fixation {i}")
    for i,d in enumerate(trace[:-1]):
        if not d.get("stop",False):
            sel=d.get("selected") or {}
            if int(sel.get("frontier_support_count",0))<public.SURFACE_FRONTIER["minimum_candidate_frontier_support"]: fails.append(f"policy decision {i} lacks 3D frontier support")
    if cov[-1]<t["final_truth_coverage_min"]: fails.append("active final curved-surface coverage")
    if cov[-1]-cov[0]<t["truth_coverage_gain_over_seed_min"]: fails.append("active curved-surface coverage gain over seed")
    metrics["fails"]=fails; metrics["status"]="FSG6E_3D_FRONTIER_RUN_PASS" if not fails else "FSG6E_3D_FRONTIER_RUN_FAIL"; json_write(out/"metrics.json",metrics); write_visual(out/"growth_truth.png",fixture,maps,cov,gazes); print("[fsg6e-eval] "+metrics["status"],json.dumps(metrics,sort_keys=True),flush=True); return metrics

def main()->None:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("record",type=Path); ap.add_argument("--out",type=Path,required=True); ap.add_argument("--mode",choices=("smoke","full"),required=True); a=ap.parse_args(); m=evaluate(a.record,a.out,a.mode); raise SystemExit(0 if not m["fails"] else 2)
if __name__=="__main__": main()
