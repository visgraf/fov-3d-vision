"""FSG1 evaluator. This is the ONLY host reconstruction tool that opens truth.

    .venv/bin/python tools/fsg_evaluate.py previews/fsg1/small

Default requires real Blender provenance AND independent Blender geometry checks.
--allow-synthetic is for software fixtures only and can NEVER approve the milestone.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import numpy as np
import cv2
from PIL import Image
from fsg_geometry import json_write,pixels,project_h,rays_h,unit
from fsg_scene import CASES,ray_mesh
from fsg_stereo import rectification,sha256,save_gray

# Frozen, prospective targets from the agreed first-patch experiment.
MIN_COVERAGE = .90
MAX_MEDIAN_RELATIVE_RANGE = .01
MAX_P95_RELATIVE_RANGE = .03
BOUNDARY_RADIUS = {"small":4,"full":8}


def describe_errors(pred: np.ndarray,truth: dict,centre: np.ndarray,
                    accepted: np.ndarray,reference: np.ndarray) -> dict:
    m=reference&accepted&np.isfinite(pred).all(axis=-1)
    count=int(reference.sum()); n=int(m.sum())
    d={"reference_pixels":count,"accepted_pixels":n,
       "coverage":float(n/count) if count else None,
       "median_relative_range_error":None,"p95_relative_range_error":None,
       "median_position_error_m":None,"p95_position_error_m":None,
       "median_point_to_plane_error_m":None,"fraction_relative_error_over_3pct":None}
    if n:
        er=np.abs(np.linalg.norm(pred[m]-centre,axis=-1)-truth["range_m"][m])/truth["range_m"][m]
        ep=np.linalg.norm(pred[m]-truth["position_h"][m],axis=-1)
        en=np.abs(np.sum((pred[m]-truth["position_h"][m])*truth["normal_h"][m],axis=-1))
        d.update(median_relative_range_error=float(np.median(er)),p95_relative_range_error=float(np.quantile(er,.95)),
                 median_position_error_m=float(np.median(ep)),p95_position_error_m=float(np.quantile(ep,.95)),
                 median_point_to_plane_error_m=float(np.median(en)),fraction_relative_error_over_3pct=float(np.mean(er>.03)))
    return d


def gate(metrics: dict) -> list[str]:
    fails=[]
    if metrics["reference_pixels"]<100:
        fails.append("fewer than 100 independently eligible interior pixels")
    for key,op,threshold in (("coverage","min",MIN_COVERAGE),
                             ("median_relative_range_error","max",MAX_MEDIAN_RELATIVE_RANGE),
                             ("p95_relative_range_error","max",MAX_P95_RELATIVE_RANGE)):
        v=metrics[key]
        if v is None or not np.isfinite(v) or (v<threshold if op=="min" else v>threshold):
            fails.append(f"{key}={v} fails {op} {threshold}")
    return fails


def ground_reference(c: dict,mesh: dict) -> tuple[dict,np.ndarray,np.ndarray,np.ndarray]:
    """Fixed reference, independent of predicted depth and its validity mask."""
    r=rectification(c); x,y,w,h=map(int,r["crop_xywh"])
    kl=r["P1"][:,:3].copy(); kl[0,2]-=x; kl[1,2]-=y
    rl=np.asarray(c["eyes"][0]["R_hc"]) @ r["R1"].T
    lcentre=np.asarray(c["eyes"][0]["centre_h_m"])
    virtual={"K":kl,"R_hc":rl,"centre_h_m":lcentre}
    directions=rays_h(virtual,pixels(w,h))
    truth=ray_mesh(lcentre,directions,mesh)
    hit=truth["instance_id"]>0
    cr=np.asarray(c["eyes"][1]["centre_h_m"])
    valid_xyz=np.where(hit[...,None],truth["position_h"],np.array([0,0,-2.]))
    dr=unit(valid_xyz-cr); right_hit=ray_mesh(cr,dr,mesh)
    target_range=np.linalg.norm(valid_xyz-cr,axis=-1)
    joint=hit&(right_hit["instance_id"]==truth["instance_id"])&(np.abs(right_hit["range_m"]-target_range)<1e-4)
    observed=np.ones(hit.shape,bool)
    for eye in c["eyes"]:
        uv,z=project_h(eye,valid_xyz); rw,rh=c["image_size_wh"]
        observed &= (z>0)&(uv[...,0]>=1)&(uv[...,0]<rw-2)&(uv[...,1]>=1)&(uv[...,1]<rh-2)
    eligible=joint&observed
    # Boundaries include an ID transition or a >5% adjacent range jump.
    ids=truth["instance_id"]; depth=truth["range_m"]
    edge=np.zeros(hit.shape,bool)
    for axis in (0,1):
        aa=[slice(None),slice(None)]; bb=aa.copy(); aa[axis]=slice(1,None); bb[axis]=slice(None,-1)
        aa,bb=tuple(aa),tuple(bb)
        da,db=depth[aa],depth[bb]
        with np.errstate(invalid="ignore"):
            jump=(ids[aa]!=ids[bb])|(np.abs(da-db)>.05*np.minimum(da,db))
        edge[aa] |= jump; edge[bb] |= jump
    rad=BOUNDARY_RADIUS[c["profile"]]
    band=cv2.dilate(edge.astype(np.uint8),np.ones((2*rad+1,2*rad+1),np.uint8)).astype(bool)
    return truth,eligible,band,hit&observed&~joint


def evaluate_pair(folder: Path,allow_synthetic: bool=False,write: bool=True) -> dict:
    c=json.loads((folder/"calibration.json").read_text())
    acq=json.loads((folder/"acquisition.json").read_text())
    stereo=json.loads((folder/"stereo"/"summary.json").read_text())
    for n,digest in stereo["input_sha256"].items():
        if sha256(folder/n)!=digest: raise ValueError(f"stale stereo inputs: {n}")
    with np.load(folder/"evaluation_only"/"mesh.npz",allow_pickle=False) as f:
        mesh={k:f[k] for k in f.files}
    with np.load(folder/"stereo"/"result.npz",allow_pickle=False) as f:
        result={k:f[k] for k in f.files}
    truth,eligible,band,monocular=ground_reference(c,mesh)
    if result["xyz_h"].shape!=truth["position_h"].shape: raise ValueError("prediction/reference shape mismatch")
    centre=np.asarray(c["eyes"][0]["centre_h_m"])
    m=result["valid"].astype(bool); xyz=result["xyz_h"]
    interior=describe_errors(xyz,truth,centre,m,eligible&~band)
    boundary=describe_errors(xyz,truth,centre,m,eligible&band)
    mono=describe_errors(xyz,truth,centre,m,monocular)
    full=describe_errors(xyz,truth,centre,m,eligible)
    failures=gate(interior)
    real=acq.get("source")=="blender_cycles" and bool(acq.get("checks",{}).get("independent_blender_checks"))
    if not real and not allow_synthetic: failures.append("not a Blender measurement with independent geometry checks")
    per_object={}
    for i in sorted(set(mesh["instance_ids"].tolist())):
        support=(truth["instance_id"]==i)&eligible&~band
        per_object[str(i)]=describe_errors(xyz,truth,centre,m,support)
        # Do not allow the large background to hide a failed foreground.
        if int(support.sum())>=100:
            failures += [f"instance {i}: {x}" for x in gate(per_object[str(i)])]
    wrong=(result["instance_id"]!=truth["instance_id"])&m&eligible
    if np.any(wrong&~band): failures.append("accepted interior has incorrect object identity")
    res={"schema":"FSG1-evaluation-v1","case":folder.name,"source":acq["source"],
         "interior":interior,"boundary":boundary,"jointly_visible_all":full,
         "singly_visible":mono,"per_object_interior":per_object,
         "wrong_instance_accepted_count":int(wrong.sum()),
         "thresholds":{"minimum_coverage":MIN_COVERAGE,"maximum_median_relative_range":MAX_MEDIAN_RELATIVE_RANGE,
                       "maximum_p95_relative_range":MAX_P95_RELATIVE_RANGE,"boundary_radius_px":BOUNDARY_RADIUS[c["profile"]]},
         "primary_camera_samples":acq["primary_camera_samples"],
         "render_seconds":sum(acq["render_seconds_lr"]),"stereo_seconds":stereo["seconds"],
         "fails":failures,"checks_pass":not failures,"real_blender_measurement":real}
    if write:
        out=folder/"evaluation"; out.mkdir(exist_ok=True)
        json_write(out/"metrics.json",res)
        lo,hi=c["depth_search_z_rect_m"]
        save_gray(out/"truth_range_left.png",truth["range_m"],truth["instance_id"]>0,lo,hi)
        Image.fromarray((eligible&~band).astype(np.uint8)*255).save(out/"reference_interior.png")
        Image.fromarray((eligible&band).astype(np.uint8)*255).save(out/"reference_boundary.png")
        err=np.abs(np.linalg.norm(xyz-centre,axis=-1)-truth["range_m"])/truth["range_m"]
        save_gray(out/"relative_range_error.png",err,m&eligible,0,.05)
    return res


def evaluate_run(run_path: Path,allow_synthetic: bool=False) -> dict:
    run=json.loads((run_path/"run.json").read_text())
    if not run.get("complete"): raise ValueError("incomplete acquisition")
    rs=[evaluate_pair(run_path/n,allow_synthetic) for n in run["cases"]]
    fails=[f"{r['case']}: {a}" for r in rs for a in r["fails"]]
    complete=set(run["cases"])==set(CASES)
    if not complete: fails.append("the gate requires all three cases: fronto, tilted, step")
    all_real=all(r["real_blender_measurement"] for r in rs)
    standard_spp=run["spp"]==run.get("profile_default_spp",{"small":64,"full":256}[run["profile"]])
    milestone=not fails and all_real and run["profile"]=="full" and standard_spp
    result={"schema":"FSG1-suite-v1","source":run["source"],"profile":run["profile"],
            "cases":rs,"fails":fails,"checks_pass":not fails,
            "full_profile_milestone_pass":milestone,
            "status":("MILESTONE_PASS" if milestone else "DIAGNOSTIC_PASS_NONDEFAULT_SPP" if not fails and all_real and not standard_spp else "SMALL_PROFILE_PASS" if not fails and all_real else
                       "SYNTHETIC_FIXTURE_PASS_NOT_A_RENDER_RESULT" if not fails else "FAIL")}
    json_write(run_path/"evaluation.json",result)
    for r in rs:
        a=r["interior"]
        print(f"[fsg-eval] {r['case']} source={r['source']} interior_coverage={a['coverage']} "
              f"median_relative_range={a['median_relative_range_error']} p95_relative_range={a['p95_relative_range_error']} "
              f"primary_samples={r['primary_camera_samples']}")
    for f in fails: print("[fsg-eval] FAIL",f)
    print("[fsg-eval]",result["status"])
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("run",type=Path)
    ap.add_argument("--allow-synthetic",action="store_true",help="software checks only; never approves the experiment")
    a=ap.parse_args(); r=evaluate_run(a.run,a.allow_synthetic)
    raise SystemExit(0 if r["checks_pass"] else 1)


if __name__=="__main__":
    try: main()
    except Exception as e:
        print(f"[fsg-eval] FAIL {type(e).__name__}: {e}",file=sys.stderr)
        raise SystemExit(1)
