"""Descriptive evaluation for Reality Check 1.

Unlike the preceding closed FSG increments, this reality check does not encode a
numerical quality PASS threshold.  It gates provenance/integrity and reports the
quality measures needed for Luiz/Chat to judge whether the result is useful enough.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import cv2

import reality1_public as public
import reality1_scene as scene
from fsg3_surface_map import load_map
from fsg_geometry import json_write


def _bins(points: np.ndarray, cell: float) -> dict:
    out={}
    for p in np.asarray(points,float):
        if np.isfinite(p).all():
            out.setdefault(tuple(np.floor(p/cell).astype(int)),[]).append(p)
    return out


def spatial_coverage(xyz: np.ndarray) -> float:
    truth=scene.truth_points(); cell=scene.TRUTH_COVER_RADIUS_M; bins=_bins(xyz,cell); hit=0
    for q in truth:
        k=tuple(np.floor(q/cell).astype(int)); best=cell
        for a in (-1,0,1):
            for b in (-1,0,1):
                for c in (-1,0,1):
                    for p in bins.get((k[0]+a,k[1]+b,k[2]+c),()):
                        best=min(best,float(np.linalg.norm(q-p)))
        hit += best < cell
    return float(hit/len(truth))


def approximate_surface_distance(xyz: np.ndarray) -> np.ndarray:
    """Nearest dense analytic truth sample; descriptive, not a fitted estimator."""
    truth=scene.truth_points(); cell=0.030; bins=_bins(truth,cell); out=[]
    for q in np.asarray(xyz,float):
        if not np.isfinite(q).all(): continue
        k=tuple(np.floor(q/cell).astype(int)); best=np.inf
        for r in range(0,3):
            for a in range(-r,r+1):
                for b in range(-r,r+1):
                    for c in range(-r,r+1):
                        for p in bins.get((k[0]+a,k[1]+b,k[2]+c),()):
                            best=min(best,float(np.linalg.norm(q-p)))
            if np.isfinite(best): break
        out.append(best)
    return np.asarray(out,float)


def write_growth_truth(path:Path,maps:list,coverage:list[float],gazes:list[tuple[float,float]])->None:
    n=len(maps); W=300*n; H=330; canvas=np.full((H,W,3),245,np.uint8)
    truth=scene.truth_points(); ty,tp=scene.angular_coordinates(truth)
    yl,yh=ty.min(),ty.max(); pl,ph=tp.min(),tp.max()
    for k,(m,cov,g) in enumerate(zip(maps,coverage,gazes)):
        y,p=scene.angular_coordinates(m.xyz_h); x0=300*k
        cv2.rectangle(canvas,(x0+20,45),(x0+280,285),(210,210,210),1)
        cv2.putText(canvas,f"{k}: {g[0]:.1f},{g[1]:.1f}",(x0+25,20),cv2.FONT_HERSHEY_SIMPLEX,.42,(20,20,20),1,cv2.LINE_AA)
        cv2.putText(canvas,f"visible cover {100*cov:.1f}%",(x0+25,38),cv2.FONT_HERSHEY_SIMPLEX,.40,(20,20,20),1,cv2.LINE_AA)
        px=np.clip((y-yl)/max(1e-9,yh-yl)*240+x0+30,x0+30,x0+270).astype(int)
        py=np.clip((ph-p)/max(1e-9,ph-pl)*210+60,60,270).astype(int)
        strong=m.support_count>1
        for X,Y,S in zip(px[::2],py[::2],strong[::2]): canvas[Y,X]=(25,25,25) if S else (145,145,145)
    cv2.imwrite(str(path),canvas)


def evaluate(root:Path,out:Path)->dict:
    root=root.resolve(); out=out.resolve()
    if out.exists(): raise FileExistsError("output must be new")
    manifest=json.loads((root/"prediction_manifest.json").read_text())
    fails=[]
    if manifest.get("truth_opened") is not False: fails.append("prediction opened evaluator truth")
    if manifest.get("public_spec_sha256") != public.public_digest(): fails.append("public spec digest mismatch")
    if manifest.get("instrument") != public.INSTRUMENT_ID: fails.append("wrong stereo instrument")
    if manifest.get("frozen_object_policy") != public.FROZEN_POLICY_ID: fails.append("wrong object policy")
    if not manifest.get("fixed_head") or not manifest.get("static_scene"): fails.append("fixed-head/static-scene contract broken")
    seed=int(manifest.get("seed"));
    if seed not in public.SEEDS: fails.append("seed outside prospective schedule")
    gazes=[tuple(map(float,g)) for g in manifest["fixation_gazes_deg"]]
    if len({(round(a,8),round(b,8)) for a,b in gazes}) != len(gazes): fails.append("repeated physical fixation")
    maps=[]
    for step,(yaw,pitch) in enumerate(gazes):
        maps.append(load_map(root/"maps"/f"map_{step:02d}.npz"))
        acq=root/"acquisitions"/f"fix_{step:02d}"; case=acq/f"fix_{step:02d}"
        rr=json.loads((acq/"run.json").read_text())
        if rr.get("truth_spec_sha256")!=scene.truth_digest() or rr.get("fixture")!=public.FIXTURE:
            fails.append(f"fix_{step:02d} truth/fixture provenance mismatch")
        with np.load(case/"evaluation_only"/"mesh.npz",allow_pickle=False) as f:
            mesh={k:f[k] for k in f.files}
        try: scene.validate_mesh(mesh)
        except Exception as exc: fails.append(f"fix_{step:02d} exported scene mesh invalid: {exc}")
    final=maps[-1]
    if len(final.xyz_h)<100: fails.append("final target map is effectively empty")
    if len(final.instance_id) and set(final.instance_id.tolist()) != {public.OBJECT_ID}: fails.append("map contains non-target instance")
    for a in manifest["association_stats"][1:]:
        if not a.get("idempotent_replay",False): fails.append(f"{a['patch_id']} replay not idempotent")
    cov=[spatial_coverage(m.xyz_h) for m in maps]
    err=approximate_surface_distance(final.xyz_h)
    supported=np.asarray(final.support_count)>=2
    patch=manifest["patch_stats"]; assoc=manifest["association_stats"]
    trace=json.loads((root/"policy_trace.json").read_text())["trace"]
    mf=[p["object_measurement_fraction"] for p in patch if p.get("object_measurement_fraction") is not None]
    overlap_med=[a["overlap_median_distance_m"] for a in assoc[1:] if a.get("overlap_median_distance_m") is not None]
    overlap_p95=[a["overlap_p95_distance_m"] for a in assoc[1:] if a.get("overlap_p95_distance_m") is not None]
    metrics={
        "schema":"RealityCheck1-evaluation-v1",
        "status":"REALITY1_OBSERVATION_COMPLETE" if not fails else "REALITY1_INTEGRITY_FAIL",
        "integrity_fails":fails,
        "profile":manifest["profile"],"seed":seed,"fixture":public.FIXTURE,
        "fixation_count":len(gazes),"fixation_gazes_deg":[list(g) for g in gazes],
        "termination_reason":manifest["termination_reason"],
        "visible_truth_coverage_by_fixation":cov,
        "visible_truth_coverage_seed":cov[0],"visible_truth_coverage_final":cov[-1],
        "visible_truth_coverage_gain":cov[-1]-cov[0],
        "map_points":int(len(final.xyz_h)),"supported_surfels":int(supported.sum()),
        "approx_surface_median_m":float(np.median(err)) if len(err) else None,
        "approx_surface_p95_m":float(np.percentile(err,95)) if len(err) else None,
        "measurement_fraction_min":float(min(mf)) if mf else None,
        "measurement_fraction_median":float(np.median(mf)) if mf else None,
        "overlap_median_max_m":float(max(overlap_med)) if overlap_med else None,
        "overlap_p95_max_m":float(max(overlap_p95)) if overlap_p95 else None,
        "patch_stats":patch,"association_stats":assoc,"policy_trace":trace,
        "primary_camera_samples":int(manifest["primary_camera_samples"]),
        "quality_gated":False,
        "interpretation":"descriptive reality check; numerical quality is intentionally not auto-classified as PASS/FAIL",
    }
    out.mkdir(parents=True); json_write(out/"metrics.json",metrics)
    write_growth_truth(out/"growth_truth.png",maps,cov,gazes)
    print("[reality1-eval] "+metrics["status"],json.dumps({k:metrics[k] for k in (
        "seed","fixation_count","termination_reason","visible_truth_coverage_seed",
        "visible_truth_coverage_final","visible_truth_coverage_gain","approx_surface_median_m",
        "approx_surface_p95_m","supported_surfels","measurement_fraction_min",
        "overlap_median_max_m","integrity_fails")},sort_keys=True),flush=True)
    return metrics


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("record",type=Path); ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args(); m=evaluate(a.record,a.out); raise SystemExit(0 if not m["integrity_fails"] else 2)

if __name__=="__main__": main()
