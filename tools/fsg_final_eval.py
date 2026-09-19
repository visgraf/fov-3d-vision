"""Prospective final FSG1 validation of the simple one-update instrument.

Candidate = fixed HDR encoding + original SGBM + exactly one original
photometric update + original validity logic.  No FSG1f endpoint or footprint
support veto is applied.  Predictions are persisted before evaluation geometry
is opened.
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
import fsg_evaluate as e
import fsg_hdr_compare as paired
import fsg_stereo_hdr as hdr
import fsg_stereo_supported as supported
import fsg_final_scene as spec

CANDIDATE_ID = spec.SPEC["candidate"]


def require(ok: bool, msg: str) -> None:
    if not ok: raise ValueError(msg)


def read_run(path: Path, allow_synthetic: bool) -> dict:
    meta=json.loads((path/"run.json").read_text())
    stored=json.loads((path/"final_validation_spec.json").read_text())
    require(stored == {"spec":spec.SPEC,"sha256":spec.spec_digest()}, "validation specification mismatch")
    require(meta.get("final_validation_spec_id")==spec.SPEC_ID and meta.get("final_validation_spec_sha256")==spec.spec_digest(), "run/spec mismatch")
    require(meta.get("complete") is True and meta.get("cases")==list(spec.CASES), "incomplete or different case suite")
    profile=meta.get("profile"); seed=meta.get("seed")
    require(profile in spec.DEFAULT_SPP and seed in spec.SPEC["seed_schedule"][profile], "unprescribed acquisition")
    require(meta.get("spp")==spec.DEFAULT_SPP[profile], "nondefault spp")
    real=meta.get("source")=="blender_cycles"
    require(real or (allow_synthetic and meta.get("source")=="synthetic_stub"), "real Blender observations required")
    return meta


def validate_schedule(metas: list[dict], mode: str) -> None:
    got=sorted((m["profile"],m["seed"]) for m in metas)
    expected=[("small",101)] if mode=="smoke" else [("full",101),("full",149)]
    require(got==expected, f"expected exactly {expected}, received {got}")


def eroded_core(mono: np.ndarray, profile: str) -> np.ndarray:
    r=spec.SPEC["occlusion_core_erosion_px"][profile]
    return cv2.erode(mono.astype(np.uint8), np.ones((2*r+1,2*r+1),np.uint8),
                     borderType=cv2.BORDER_CONSTANT,borderValue=0).astype(bool)


def boundary_gate(m: dict) -> list[str]:
    n=int(m.get("accepted_pixels", 0))
    t=spec.SPEC["boundary_targets"]
    fails=[]
    if n < t["minimum_accepted_points"]:
        fails.append(f"boundary accepted_points={n} fails exercise minimum {t['minimum_accepted_points']}")
        return fails
    med=m.get("median_relative_range_error"); p95=m.get("p95_relative_range_error")
    if med is None or med > t["median_range_max"]: fails.append(f"boundary median_relative_range_error={med} fails max {t['median_range_max']}")
    if p95 is None or p95 > t["p95_range_max"]: fails.append(f"boundary p95_relative_range_error={p95} fails max {t['p95_range_max']}")
    return fails


def save_prediction(folder: Path, dest: Path) -> tuple[dict,dict,dict]:
    c,obs=hdr.read_observation(folder)
    # FSG1f compute_once is exactly the desired simple candidate.  Do NOT call
    # compute_variants: endpoint/footprint vetoes are intentionally absent.
    supported.check_kernel_equivalence()
    record,meta,_state=supported.compute_once(c,obs)
    meta.update(candidate_id=CANDIDATE_ID, variant="final_one_step_original_validity",
                prospective_final_validation=True, adopted_default=False)
    dest.mkdir(parents=True)
    hdr.save_candidate(dest/"stereo_candidate",c,record,meta)
    return c,record,meta


def draw(dest: Path, candidate: dict, ctx: dict, core: np.ndarray) -> None:
    truth=ctx["truth"]; interior=ctx["refs"]["interior"]; boundary=ctx["refs"]["boundary"]
    mono=ctx["refs"]["singly_visible"]; valid=candidate["valid"]
    with np.errstate(invalid="ignore",divide="ignore"):
        err=np.abs(np.linalg.norm(candidate["xyz_h"]-ctx["centre"],axis=-1)-truth["range_m"])/truth["range_m"]
    byte=lambda x: np.rint(255*np.clip(np.nan_to_num(x,nan=0.),0.,1.)).astype(np.uint8)
    panels=[("HDR RGB",hdr.hdr_to_u8(candidate["rgb_left"])),
            ("Valid",byte(valid)),
            ("Interior error / 3%",byte(np.where(valid&interior,err/.03,0))),
            ("Boundary",byte(boundary)),
            ("Boundary error / 3%",byte(np.where(valid&boundary,err/.03,0))),
            ("Singly visible",byte(mono)),
            ("Occlusion core",byte(core)),
            ("Unsafe accepted core",byte(valid&core)),
            ("Missing",byte(~valid))]
    size=256;line=28;top=48
    canvas=Image.new("RGB",(3*size,3*(size+line)+top),"white");d=ImageDraw.Draw(canvas)
    d.text((8,8),"FSG1g FINAL PROSPECTIVE VALIDATION",fill="black")
    d.text((8,27),"Missing geometry remains missing; no fill.",fill="black")
    for i,(label,data) in enumerate(panels):
        x=(i%3)*size;y=top+(i//3)*(size+line);d.text((x+4,y+5),label,fill="black")
        canvas.paste(Image.fromarray(data).convert("RGB").resize((size,size),Image.Resampling.NEAREST),(x,y+line))
    canvas.save(dest/"validation.png")


def evaluate_pair(folder: Path, dest: Path, meta: dict, allow_synthetic: bool) -> dict:
    c,candidate,cmeta=save_prediction(folder,dest)
    # Truth is opened only after the candidate was persisted.
    with np.load(folder/"evaluation_only"/"mesh.npz",allow_pickle=False) as f:
        mesh={k:f[k] for k in f.files}
    spec.validate_mesh(folder.name,mesh)
    real=meta["source"]=="blender_cycles"
    metrics,ctx=paired.candidate_evaluation(c,candidate,mesh,real,allow_synthetic)
    fails=list(metrics["fails"])
    mono=ctx["refs"]["singly_visible"]; core=eroded_core(mono,c["profile"])
    occ={"raw_reference":int(mono.sum()),"core_reference":int(core.sum()),
         "accepted_raw":int(np.count_nonzero(candidate["valid"]&mono)),
         "accepted_core":int(np.count_nonzero(candidate["valid"]&core))}
    if folder.name.startswith("occluder_"):
        require(occ["raw_reference"]>=spec.SPEC["occlusion_min_raw_pixels"][c["profile"]],"half-occlusion NOT_EXERCISED: raw")
        require(occ["core_reference"]>=spec.SPEC["occlusion_min_core_pixels"][c["profile"]],"half-occlusion NOT_EXERCISED: core")
        if occ["accepted_core"] != 0: fails.append(f"accepted {occ['accepted_core']} singly-visible core pixels; limit=0")
        fails += boundary_gate(metrics["metrics"]["boundary"])
    else:
        require(occ["raw_reference"]==0,"unexpected monocular population in phase plane")
    report={"case":folder.name,"candidate_id":CANDIDATE_ID,"candidate":metrics,
            "occlusion":occ,"fails":fails,"checks_pass":not fails,
            "prediction_saved_before_truth":True,"boundary_accuracy_gated_on_occluders":folder.name.startswith("occluder_"),
            "full_profile_milestone_pass":False,"increment2_authorized":False}
    g.json_write(dest/"validation.json",report);draw(dest,candidate,ctx,core)
    for key,m in metrics["metrics"].items():
        if key=="interior" or key.startswith("instance_") or key=="boundary":
            print(f"[fsg-final] {meta['profile']}/seed{meta['seed']}/{folder.name}/{key} reference={m['reference_pixels']} coverage={m['coverage']} median={m['median_relative_range_error']} p95={m['p95_relative_range_error']}")
    print(f"[fsg-final] {folder.name} occlusion_raw={occ['raw_reference']} core={occ['core_reference']} accepted_core={occ['accepted_core']}")
    for x in fails: print(f"[fsg-final] NUMERICAL_FAIL {folder.name}: {x}")
    return report


def compare(runs: list[Path],out: Path,mode: str,allow_synthetic: bool=False) -> dict:
    start=time.perf_counter(); runs=[p.resolve() for p in runs]; out=out.resolve()
    require(not out.exists(),"output must be new")
    metas=[read_run(p,allow_synthetic) for p in runs]; validate_schedule(metas,mode)
    out.mkdir(parents=True);reports=[]
    for run,meta in zip(runs,metas):
        cases={name:evaluate_pair(run/name,out/run.name/name,meta,allow_synthetic) for name in spec.CASES}
        fails=[f"{name}: {msg}" for name,r in cases.items() for msg in r["fails"]]
        reports.append({"run":str(run),"profile":meta["profile"],"seed":meta["seed"],"cases":cases,"fails":fails,"checks_pass":not fails,
                        "acquisition_primary_samples":meta.get("primary_camera_samples",0)})
    passed=all(r["checks_pass"] for r in reports)
    all_real=all(m["source"]=="blender_cycles" for m in metas)
    final_pass=bool(passed and all_real and mode=="full")
    status=("SYNTHETIC_FINAL_VALIDATION_NOT_A_RENDER_RESULT" if not all_real else
            "SMOKE_COMPLETE_NOT_A_MILESTONE" if mode=="smoke" else
            "FSG1_FINAL_VALIDATION_PASS" if passed else "FSG1_FINAL_VALIDATION_FAIL")
    result={"schema":"FSG1g-final-validation-v1","status":status,"mode":mode,"candidate_id":CANDIDATE_ID,
            "all_gates_pass":passed,"prospective_blender_validation_pass":final_pass,
            "full_profile_milestone_pass":final_pass,"increment1_complete":final_pass,
            "increment2_authorized":final_pass,"adopted_as_fsg1_instrument":final_pass,
            "runs":reports,"new_inference_primary_samples":0,
            "acquisition_primary_samples":sum(m.get("primary_camera_samples",0) for m in metas),
            "seconds":time.perf_counter()-start,
            "limitation":"Controlled opaque diffuse planar calibration suite with oracle instance segmentation, known fixed camera poses and two MC seeds. A pass qualifies the local measurement instrument for Increment 2; it does not establish arbitrary-scene stereo or complete boundary coverage."}
    g.json_write(out/"validation.json",result)
    print(f"[fsg-final] SUMMARY mode={mode} runs={len(runs)} checks_pass={str(passed).lower()} status={status} increment2_authorized={str(final_pass).lower()}")
    return result


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("runs",type=Path,nargs="+");ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--mode",choices=("smoke","full"),required=True);ap.add_argument("--allow-synthetic",action="store_true")
    args=ap.parse_args();res=compare(args.runs,args.out,args.mode,args.allow_synthetic)
    raise SystemExit(0 if res["all_gates_pass"] else 2)


if __name__=="__main__":
    try: main()
    except Exception as exc:
        print(f"[fsg-final] FAIL {type(exc).__name__}: {exc}",file=sys.stderr);raise SystemExit(1)
