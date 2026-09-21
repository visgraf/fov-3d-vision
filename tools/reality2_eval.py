"""Descriptive evaluation of Reality Check 2 exact continuation records."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

import reality2_public as public
import reality1_public as parent_public
import reality1_scene as scene
import reality1_eval as base_eval
from fsg3_surface_map import load_map
from fsg_geometry import json_write


def _sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()


def evaluate(root:Path,out:Path)->dict:
    root=root.resolve(); out=out.resolve()
    if out.exists(): raise FileExistsError("output must be new")
    manifest=json.loads((root/"prediction_manifest.json").read_text()); fails=[]
    if manifest.get("truth_opened") is not False: fails.append("prediction opened evaluator truth")
    if manifest.get("public_spec_sha256") != public.public_digest(): fails.append("public spec digest mismatch")
    if manifest.get("parent_reality1_public_spec_sha256") != parent_public.public_digest(): fails.append("parent public spec digest mismatch")
    if manifest.get("instrument") != public.INSTRUMENT_ID: fails.append("wrong stereo instrument")
    if manifest.get("frozen_object_policy") != public.FROZEN_POLICY_ID: fails.append("wrong object policy")
    if not manifest.get("fixed_head") or not manifest.get("static_scene"): fails.append("fixed-head/static-scene contract broken")
    if manifest.get("continued_from_parent_without_rerender") is not True: fails.append("parent was not reused as exact continuation state")
    if int(manifest.get("parent_fixation_count",-1)) != public.PARENT_FIXATIONS: fails.append("wrong parent fixation count")
    if int(manifest.get("watchdog_total_fixations",-1)) != public.WATCHDOG_TOTAL_FIXATIONS: fails.append("watchdog drifted")
    seed=int(manifest.get("seed"));
    if seed not in public.SEEDS: fails.append("seed outside prospective schedule")
    gazes=[tuple(map(float,g)) for g in manifest["fixation_gazes_deg"]]
    if len(gazes) < public.PARENT_FIXATIONS: fails.append("combined record lost parent fixations")
    if len(gazes) > public.WATCHDOG_TOTAL_FIXATIONS: fails.append("combined record exceeded watchdog")
    if len({(round(a,8),round(b,8)) for a,b in gazes}) != len(gazes): fails.append("repeated physical fixation")

    parent=Path(manifest["parent_record"]).resolve()
    if not parent.exists(): fails.append("parent Reality Check 1 record missing")
    else:
        for name,want in manifest.get("parent_hashes",{}).items():
            p=parent/name
            if not p.exists() or _sha256(p)!=want: fails.append(f"parent {name} changed after continuation")
        pm=json.loads((parent/"prediction_manifest.json").read_text())
        pg=[tuple(map(float,g)) for g in pm.get("fixation_gazes_deg",[])]
        if pg != gazes[:public.PARENT_FIXATIONS]: fails.append("combined first six gazes differ from exact parent")
        # Reality Check 2 must not create replacement acquisitions for parent steps.
        for step in range(public.PARENT_FIXATIONS):
            if (root/"acquisitions"/f"fix_{step:02d}").exists(): fails.append(f"parent fix_{step:02d} was rerendered")
            src=parent/"maps"/f"map_{step:02d}.npz"; dst=root/"maps"/f"map_{step:02d}.npz"
            if not src.exists() or not dst.exists() or _sha256(src)!=_sha256(dst):
                fails.append(f"combined map_{step:02d} is not an exact copy of the parent state")

    maps=[]
    for step in range(len(gazes)):
        mp=root/"maps"/f"map_{step:02d}.npz"
        if not mp.exists(): fails.append(f"missing combined map_{step:02d}"); continue
        maps.append(load_map(mp))
        if step < public.PARENT_FIXATIONS:
            continue
        acq=root/"acquisitions"/f"fix_{step:02d}"; case=acq/f"fix_{step:02d}"
        rr=json.loads((acq/"run.json").read_text())
        if rr.get("truth_spec_sha256")!=scene.truth_digest() or rr.get("fixture")!=public.FIXTURE:
            fails.append(f"fix_{step:02d} truth/fixture provenance mismatch")
        with np.load(case/"evaluation_only"/"mesh.npz",allow_pickle=False) as f:
            mesh={k:f[k] for k in f.files}
        try: scene.validate_mesh(mesh)
        except Exception as exc: fails.append(f"fix_{step:02d} exported scene mesh invalid: {exc}")
    if len(maps)!=len(gazes): fails.append("map sequence incomplete")
    final=maps[-1] if maps else None
    if final is None or len(final.xyz_h)<100: fails.append("final target map is effectively empty")
    elif len(final.instance_id) and set(final.instance_id.tolist()) != {public.OBJECT_ID}: fails.append("map contains non-target instance")
    for a in manifest["association_stats"][1:]:
        if not a.get("idempotent_replay",False): fails.append(f"{a['patch_id']} replay not idempotent")

    cov=[base_eval.spatial_coverage(m.xyz_h) for m in maps]
    err=base_eval.approximate_surface_distance(final.xyz_h) if final is not None else np.empty(0)
    supported=np.asarray(final.support_count)>=2 if final is not None else np.zeros(0,dtype=bool)
    patch=manifest["patch_stats"]; assoc=manifest["association_stats"]
    trace=json.loads((root/"policy_trace.json").read_text())["trace"]
    mf=[p["object_measurement_fraction"] for p in patch if p.get("object_measurement_fraction") is not None]
    overlap_med=[a["overlap_median_distance_m"] for a in assoc[1:] if a.get("overlap_median_distance_m") is not None]
    overlap_p95=[a["overlap_p95_distance_m"] for a in assoc[1:] if a.get("overlap_p95_distance_m") is not None]
    at6=cov[public.PARENT_FIXATIONS-1] if len(cov)>=public.PARENT_FIXATIONS else None
    metrics={
        "schema":"RealityCheck2-evaluation-v1",
        "status":"REALITY2_OBSERVATION_COMPLETE" if not fails else "REALITY2_INTEGRITY_FAIL",
        "integrity_fails":fails,"profile":manifest["profile"],"seed":seed,"fixture":public.FIXTURE,
        "fixation_count":len(gazes),"new_fixation_count":max(0,len(gazes)-public.PARENT_FIXATIONS),
        "fixation_gazes_deg":[list(g) for g in gazes],"termination_reason":manifest["termination_reason"],
        "terminated_by_no_frontier":manifest["termination_reason"]=="no_frontier",
        "watchdog_reached":manifest["termination_reason"]=="watchdog_max_fixations",
        "visible_truth_coverage_by_fixation":cov,
        "visible_truth_coverage_seed":cov[0] if cov else None,
        "visible_truth_coverage_at_reality1_stop":at6,
        "visible_truth_coverage_final":cov[-1] if cov else None,
        "visible_truth_coverage_gain_after_reality1_stop":(cov[-1]-at6) if cov and at6 is not None else None,
        "map_points":int(len(final.xyz_h)) if final is not None else 0,
        "supported_surfels":int(supported.sum()),
        "approx_surface_median_m":float(np.median(err)) if len(err) else None,
        "approx_surface_p95_m":float(np.percentile(err,95)) if len(err) else None,
        "measurement_fraction_min":float(min(mf)) if mf else None,
        "measurement_fraction_median":float(np.median(mf)) if mf else None,
        "overlap_median_max_m":float(max(overlap_med)) if overlap_med else None,
        "overlap_p95_max_m":float(max(overlap_p95)) if overlap_p95 else None,
        "patch_stats":patch,"association_stats":assoc,"policy_trace":trace,
        "parent_primary_camera_samples":int(manifest["parent_primary_camera_samples"]),
        "continuation_primary_camera_samples":int(manifest["continuation_primary_camera_samples"]),
        "primary_camera_samples":int(manifest["primary_camera_samples"]),
        "quality_gated":False,
        "interpretation":"descriptive continuation; no_frontier is the scientific stop, watchdog is only a guard and is not auto-classified as quality failure",
    }
    out.mkdir(parents=True); json_write(out/"metrics.json",metrics)
    if maps: base_eval.write_growth_truth(out/"growth_truth.png",maps,cov,gazes)
    print("[reality2-eval] "+metrics["status"],json.dumps({k:metrics[k] for k in (
        "seed","fixation_count","new_fixation_count","termination_reason","terminated_by_no_frontier",
        "watchdog_reached","visible_truth_coverage_at_reality1_stop","visible_truth_coverage_final",
        "visible_truth_coverage_gain_after_reality1_stop","approx_surface_median_m",
        "approx_surface_p95_m","supported_surfels","measurement_fraction_min",
        "overlap_median_max_m","integrity_fails")},sort_keys=True),flush=True)
    return metrics


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("record",type=Path); ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args(); m=evaluate(a.record,a.out); raise SystemExit(0 if not m["integrity_fails"] else 2)

if __name__=="__main__": main()
