"""FSG1d frozen HDR validation on new observations; no estimator adaptation.

 python tools/fsg_validation_eval.py RUN --mode smoke --out NEW_DIRECTORY
 python tools/fsg_validation_eval.py FULL31 FULL73 --mode full --out NEW_DIRECTORY

Both RGB-only predictions for each pair are persisted BEFORE its geometry is
opened. All source records are fingerprinted and remain read-only. The new
half-occlusion safety gate is distinct from the unchanged FSG1 interior gates.
A validation pass does NOT adopt a default, close FSG1, or authorize fusion.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import time
import numpy as np
import cv2
from PIL import Image, ImageDraw
import fsg_geometry as g
import fsg_stereo as s
import fsg_stereo_hdr as h
import fsg_evaluate as e
import fsg_coverage_audit as a
import fsg_hdr_compare as paired
import fsg_validation_scene as spec


def require(ok: bool, message: str) -> None:
    if not ok: raise ValueError(message)


def source_hashes() -> dict:
    root=Path(__file__).resolve().parent
    return {n:s.sha256(root/n) for n in ("fsg_validation_scene.py", "fsg_validation_render.py", "fsg_validation_eval.py")}


def read_run(path: Path, allow_synthetic: bool) -> dict:
    meta=json.loads((path/"run.json").read_text())
    stored=json.loads((path/"validation_spec.json").read_text())
    require(stored == {"spec":spec.SPEC, "sha256":spec.spec_digest(), "frozen_sources":spec.FROZEN},
            "validation specification does not match the frozen handoff")
    require(meta.get("validation_spec_id")==spec.SPEC_ID and meta.get("validation_spec_sha256")==spec.spec_digest(),
            "record specification ID/hash mismatch")
    require(meta.get("complete") is True and meta.get("cases")==list(spec.CASES), "incomplete or different case suite")
    profile=meta.get("profile"); seed=meta.get("seed")
    require(profile in spec.DEFAULT_SPP and seed in spec.SPEC["seed_schedule"][profile], "unprescribed acquisition")
    spp=spec.DEFAULT_SPP[profile]
    require(meta.get("spp")==spp and meta.get("profile_default_spp")==spp, "nondefault sample count")
    real=meta.get("source")=="blender_cycles"
    require(real or (allow_synthetic and meta.get("source")=="synthetic_stub"), "real Blender observations required")
    expected_samples=0
    for ci, name in enumerate(spec.CASES):
        folder=path/name
        calibration=json.loads((folder/"calibration.json").read_text())
        require(calibration==g.make_calibration(profile,*spec.CASE_GAZE[name]), "changed calibration prescription")
        acq=json.loads((folder/"acquisition.json").read_text())
        w,height=calibration["image_size_wh"]
        nominal=2*w*height*spp
        for key,value in {"case":name,"profile":profile,"spp":spp,"profile_default_spp":spp,
                          "seeds_lr":[10000*seed+100*ci,10000*seed+100*ci+1],
                          "adaptive_sampling":False,"source":meta["source"],
                          "primary_camera_samples":nominal if real else 0,
                          "nominal_camera_samples":nominal}.items():
            require(acq.get(key)==value, f"changed acquisition field {name}/{key}")
        if real:
            checks=acq.get("checks",{})
            require(checks.get("independent_blender_checks") is True, "missing independent Blender checks")
            require(0 <= checks.get("projection_max_error_px",np.inf) <= .002, "Blender projection check missing or failed")
            require(0 <= checks.get("raycast_max_error_m",np.inf) <= 2e-5, "Blender ray-cast check missing or failed")
            require(checks.get("raycast_hits_checked",0)>=100, "too few independent Blender rays")
        expected_samples+=nominal if real else 0
    require(meta.get("primary_camera_samples")==expected_samples, "run sample budget does not equal its pairs")
    return meta


def validate_schedule(metas: list[dict], mode: str) -> None:
    got=sorted((m["profile"],m["seed"]) for m in metas)
    expected=[("small",31)] if mode=="smoke" else [("full",31),("full",73)]
    require(got==expected, f"expected exactly schedule {expected}, received {got}")


def occlusion_reference(name: str, profile: str, mono: np.ndarray) -> tuple[np.ndarray,dict]:
    """Fixed truth-only mask, independent of predictions. Empty is not a pass."""
    radius=spec.SPEC["occlusion_core_erosion_px"][profile]
    core=cv2.erode(mono.astype(np.uint8),np.ones((2*radius+1,2*radius+1),np.uint8),
                   borderType=cv2.BORDER_CONSTANT,borderValue=0).astype(bool)
    raw_n,core_n=int(mono.sum()),int(core.sum())
    if name=="step_right":
        require(raw_n>=spec.SPEC["occlusion_min_raw_pixels"][profile], "half-occlusion NOT_EXERCISED: raw reference too small")
        require(core_n>=spec.SPEC["occlusion_min_core_pixels"][profile], "half-occlusion NOT_EXERCISED: core reference too small")
    else:
        require(raw_n==0, "unexpected monocular pixels in tilted-plane fixture")
    return core,{"status":"EXERCISED" if raw_n else "NOT_EXERCISED", "reference_pixels":raw_n,
                 "core_pixels":core_n,"erosion_radius_px":radius,
                 "criterion":"zero accepted in fixed eroded core; all raw mono pixels also reported"}


def occlusion_result(valid: np.ndarray, mono: np.ndarray, core: np.ndarray, desc: dict) -> dict:
    raw=int(np.count_nonzero(valid&mono)); accepted=int(np.count_nonzero(valid&core))
    return dict(desc, accepted_raw=raw, accepted_core=accepted,
                fraction_raw_accepted=raw/desc["reference_pixels"] if desc["reference_pixels"] else None,
                fraction_core_accepted=accepted/desc["core_pixels"] if desc["core_pixels"] else None,
                checks_pass=(accepted==0) if desc["core_pixels"] else None)


def infer_pair(folder: Path, dest: Path) -> tuple[dict,dict,dict,dict]:
    """No evaluation_only reads here. Returns predictions after persisting them."""
    calibration,obs=h.read_observation(folder)
    legacy,old_meta=s.compute(calibration,obs)
    candidate,new_meta=h.compute_candidate(calibration,obs)
    fingerprints={n:s.sha256(folder/n) for n in ("calibration.json","observation.npz")}
    require(not dest.exists(), "pair output already exists")
    old_dest=dest/"stereo_legacy"; old_dest.mkdir(parents=True)
    old_meta.update(input_sha256=fingerprints, instrument="frozen FSG1 legacy", validation_spec_sha256=spec.spec_digest())
    np.savez_compressed(old_dest/"result.npz",**legacy); g.json_write(old_dest/"summary.json",old_meta)
    s.write_ply(old_dest/"points_head.ply",legacy["xyz_h"][legacy["valid"]],
                s.linear_to_u8(legacy["rgb_left"])[legacy["valid"]],legacy["instance_id"][legacy["valid"]])
    new_meta.update(input_sha256=fingerprints,validation_spec_sha256=spec.spec_digest())
    h.save_candidate(dest/"stereo_candidate",calibration,candidate,new_meta)
    # This reconstructs the legacy acceptance populations, using RGB only.
    trace=a.trace_rgb(calibration,obs,legacy)
    return calibration,trace,candidate,{"legacy":old_meta["seconds"],"candidate":new_meta["seconds"]}


def draw_visual(dest: Path, name: str, trace: dict, candidate: dict, ctx: dict, core: np.ndarray) -> None:
    truth=ctx["truth"]; mono=ctx["refs"]["singly_visible"]; old=trace["fresh"]
    interior=ctx["refs"]["interior"]; accepted=candidate["valid"]
    def byte(x): return np.rint(255*np.clip(np.nan_to_num(x,nan=0.),0.,1.)).astype(np.uint8)
    with np.errstate(invalid="ignore",divide="ignore"):
        error=np.abs(np.linalg.norm(candidate["xyz_h"]-ctx["centre"],axis=-1)-truth["range_m"])/truth["range_m"]
    panels=[("Legacy clipped RGB",s.linear_to_u8(old["rgb_left"])),
            ("Fixed HDR candidate RGB",h.hdr_to_u8(candidate["rgb_left"])),
            ("Accepted interior error / 3%",byte(np.where(accepted&interior,error/.03,0))),
            ("Legacy validity (all core)",byte(old["valid"])),
            ("Candidate validity (all core)",byte(accepted)),
            ("New accepted interior",byte(accepted&~old["valid"]&interior)),
            ("Truth: singly visible reference",byte(mono)),
            ("Truth: eroded occlusion core",byte(core)),
            ("Unsafe: accepted occlusion core",byte(accepted&core))]
    size=256; line=32; top=60
    canvas=Image.new("RGB",(3*size,3*(size+line)+top),"white");draw=ImageDraw.Draw(canvas)
    draw.text((8,8),"FSG1d PROSPECTIVE VALIDATION - "+name,fill="black")
    draw.text((8,29),"Black error is ambiguous: read validity. Missing points are not filled.",fill="black")
    for i,(label,data) in enumerate(panels):
        x,y=(i%3)*size,top+(i//3)*(size+line)
        draw.text((x+4,y+6),label,fill="black")
        canvas.paste(Image.fromarray(data).convert("RGB").resize((size,size),Image.Resampling.NEAREST),(x,y+line))
    canvas.save(dest/"validation.png")
    np.savez_compressed(dest/"evaluation_masks.npz",interior=interior,boundary=ctx["refs"]["boundary"],
                        singly_visible=mono,occlusion_core=core)


def evaluate_pair(folder: Path, dest: Path, meta: dict, allow_synthetic: bool) -> dict:
    c,trace,candidate,times=infer_pair(folder,dest)
    # Geometry is first opened only AFTER both predictions have been written.
    mesh=a.load_npz(folder/"evaluation_only"/"mesh.npz"); spec.validate_mesh(folder.name,mesh)
    real=meta["source"]=="blender_cycles"
    old_metrics,ctx=paired.candidate_evaluation(c,trace["fresh"],mesh,real,allow_synthetic)
    new_metrics,_=paired.candidate_evaluation(c,candidate,mesh,real,allow_synthetic)
    # Original per-instance gate used to skip tiny populations. Here both
    # fixtures have predeclared substantial interiors; a missing one is fatal.
    for ident in sorted(set(mesh["instance_ids"].tolist())):
        key=f"instance_{ident}_interior"
        require(new_metrics["metrics"][key]["reference_pixels"]>=100,"required instance interior NOT_EXERCISED")
    mono=ctx["refs"]["singly_visible"]
    core,description=occlusion_reference(folder.name,c["profile"],mono)
    occlusion={"legacy":occlusion_result(trace["fresh"]["valid"],mono,core,description),
               "candidate":occlusion_result(candidate["valid"],mono,core,description)}
    fails=list(new_metrics["fails"])
    if occlusion["candidate"]["checks_pass"] is False:
        fails.append(f"accepted {occlusion['candidate']['accepted_core']} singly-visible core pixels; limit=0")
    cohorts=paired.paired_metrics(trace,candidate,ctx)
    report={"case":folder.name,"candidate_id":h.CANDIDATE_ID,"source":meta["source"],
            "legacy":old_metrics,"candidate":new_metrics,"occlusion":occlusion,"paired":cohorts,
            "candidate_checks_pass":not fails,"fails":fails,"inference_seconds":times,
            "predictions_saved_before_truth":True,"original_interior_gates_unchanged":True,
            "full_profile_milestone_pass":False,"adopted_default":False,"fusion_authorized":False}
    g.json_write(dest/"validation.json",report);draw_visual(dest,folder.name,trace,candidate,ctx,core)
    for key,m in new_metrics["metrics"].items():
        if key=="interior" or key.startswith("instance_"):
            print(f"[fsg-validation] {meta['profile']}/seed{meta['seed']}/{folder.name}/{key} "
                  f"reference={m['reference_pixels']} coverage={m['coverage']} "
                  f"median={m['median_relative_range_error']} p95={m['p95_relative_range_error']}")
    print(f"[fsg-validation] {folder.name} occlusion={description['status']} raw={description['reference_pixels']} "
          f"core={description['core_pixels']} accepted_core={occlusion['candidate']['accepted_core']}")
    for fail in fails: print(f"[fsg-validation] NUMERICAL_FAIL {folder.name}: {fail}")
    return report


def compare(runs: list[Path], out: Path, mode: str, allow_synthetic: bool=False) -> dict:
    start=time.perf_counter();frozen=spec.check_frozen(); own=source_hashes();h.check_kernel_equivalence()
    require(mode in ("smoke","full"),"unknown validation mode")
    runs,out=a.validate_paths(runs,out)
    metas=[read_run(run,allow_synthetic) for run in runs];validate_schedule(metas,mode)
    before=paired.snapshot(runs);reports=[]
    try:
        for run,meta in zip(runs,metas):
            cases={name:evaluate_pair(run/name,out/run.name/name,meta,allow_synthetic) for name in spec.CASES}
            fails=[f"{name}: {error}" for name,r in cases.items() for error in r["fails"]]
            reports.append({"run":str(run),"profile":meta["profile"],"seed":meta["seed"],
                            "source":meta["source"],"cases":cases,"fails":fails,"candidate_checks_pass":not fails,
                            "acquisition_primary_samples":meta["primary_camera_samples"]})
    finally:
        after=paired.snapshot(runs)
        require(after==before,"validation input files changed; discard interpretation")
        require(spec.check_frozen()==frozen and source_hashes()==own,"source files changed during comparison")
        h.check_kernel_equivalence()
    passed=all(r["candidate_checks_pass"] for r in reports)
    all_real=all(m["source"]=="blender_cycles" for m in metas)
    status=("SYNTHETIC_VALIDATION_NOT_A_RENDER_RESULT" if not all_real else
            "SMOKE_COMPLETE_NOT_A_MILESTONE" if mode=="smoke" else
            "FROZEN_CANDIDATE_VALIDATION_PASS" if passed else "FROZEN_CANDIDATE_VALIDATION_FAIL")
    result={"schema":"FSG1d-validation-v1","status":status,"mode":mode,"spec_sha256":spec.spec_digest(),
            "candidate_id":h.CANDIDATE_ID,"all_prescribed_candidate_gates_pass":passed,
            "prospective_blender_validation_pass":bool(passed and all_real and mode=="full"),
            "inputs_unchanged":True,"input_sha256_before":before,"input_sha256_after":after,
            "frozen_sources":frozen,"validation_sources":own,"numpy":np.__version__,"opencv":cv2.__version__,
            "runs":reports,"inference_new_primary_samples":0,
            "acquisition_primary_samples":sum(m["primary_camera_samples"] for m in metas),
            "seconds":time.perf_counter()-start,"full_profile_milestone_pass":False,
            "adopted_default":False,"fusion_authorized":False,
            "limitation":"Two planar calibration geometries, fixed known poses and oracle segmentation. "
                         "Two MC seeds are not independent scenes. Boundary completeness is not validated by the interior gate. "
                         "Analytic software fixtures may have been exercised after specification freeze; the real Cycles records are new."}
    g.json_write(out/"validation.json",result)
    print(f"[fsg-validation] SUMMARY mode={mode} runs={len(runs)} checks_pass={str(passed).lower()} "
          f"inputs_unchanged=true inference_new_primary_samples=0 seconds={result['seconds']:.3f} status={status}")
    return result


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("runs",type=Path,nargs="+");ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--mode",choices=("smoke","full"),required=True)
    ap.add_argument("--allow-synthetic",action="store_true",help="software tests only; cannot validate the real instrument")
    args=ap.parse_args();result=compare(args.runs,args.out,args.mode,args.allow_synthetic)
    raise SystemExit(0 if result["all_prescribed_candidate_gates_pass"] else 2)


if __name__=="__main__":
    try:main()
    except Exception as exc:
        print(f"[fsg-validation] FAIL {type(exc).__name__}: {exc}",file=sys.stderr);raise SystemExit(1)
