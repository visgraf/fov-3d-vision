"""Run one cyclopean-topology probe from a completed Reality Check 2b parent.

No parent fixation is rerendered.  The final parent map and all completed
prediction-side observations are read, an internal angular hole is identified,
and at most one new fixation is acquired at the largest unresolved hole.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image

import cyclopean1a_public as public
import cyclopean1a_topology as topo
import fsg_stereo_hdr as hdr
from fsg_stereo_supported import compute_once, check_kernel_equivalence
from fsg_stereo import support_mask
from fsg3_surface_map import Patch, load_map, save_map, fuse
import fsg6_run as fsg6run
from fsg_geometry import json_write
from reality1_run import _tone_preview


def _sha256(path: Path) -> str:
    h=hashlib.sha256();
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()


def _validate_parent(parent: Path) -> dict:
    m=json.loads((parent/"prediction_manifest.json").read_text())
    if m.get("schema") != "RealityCheck2b-prediction-v1":
        raise AssertionError("Cyclopean-1a requires a completed Reality Check 2b parent")
    if m.get("public_spec_sha256") != __import__("reality2b_public").public_digest():
        raise AssertionError("parent Reality Check 2b public digest mismatch")
    if m.get("termination_reason") != "no_frontier":
        raise AssertionError("parent must have ended by Reality Check 2b no_frontier")
    if m.get("truth_opened") is not False or not m.get("fixed_head") or not m.get("static_scene"):
        raise AssertionError("parent integrity contract broken")
    if int(m.get("seed")) not in public.SEEDS:
        raise AssertionError("parent seed outside Cyclopean-1a schedule")
    return m


def _case_for_step(parent: Path, pm: dict, step: int) -> Path:
    n0=int(pm["parent_fixation_count"])
    if step < n0:
        root=Path(pm["parent_record"])
        return root/"acquisitions"/f"fix_{step:02d}"/f"fix_{step:02d}"
    return parent/"acquisitions"/f"fix_{step:02d}"/f"fix_{step:02d}"


def _evidence_from_parent(parent: Path, pm: dict, chart: topo.Chart) -> topo.Evidence:
    e=topo.empty_evidence(chart)
    for step in range(len(pm["fixation_gazes_deg"])):
        case=_case_for_step(parent,pm,step)
        c,obs=hdr.read_observation(case); rec,_,_=compute_once(c,obs)
        topo.add_observation(e,chart,rec["xyz_h"],rec["instance_id"],rec["valid"],public.OBJECT_ID)
    return e


def _strip_cells(holes: list[dict]) -> list[dict]:
    out=[]
    for h in holes:
        q={k:v for k,v in h.items() if k!="cells"}
        out.append(q)
    return out


def _analyze_parent(parent: Path, pm: dict, sm) -> tuple[topo.Topology, topo.Evidence, dict|None]:
    chart,fc,fd=topo.build_chart(sm.xyz_h, str(pm["profile"]))
    e=_evidence_from_parent(parent,pm,chart)
    t=topo.analyze(sm.xyz_h,str(pm["profile"]),e)
    gazes=[tuple(map(float,g)) for g in pm["fixation_gazes_deg"]]
    pr=topo.select_probe(t,gazes)
    return t,e,pr


def _run_blender(args, seed:int, step:int, gaze:tuple[float,float]) -> Path:
    out=args.out/"acquisition"; out.mkdir()
    cmd=[args.blender,"-b","--python-exit-code","1","-P","tools/reality2_render_fix.py","--",
         "--out",str(out),"--profile",args.profile,"--seed",str(seed),"--step",str(step),
         "--yaw",f"{gaze[0]:.12g}","--pitch",f"{gaze[1]:.12g}","--device",args.device]
    p=subprocess.run(cmd,cwd=args.repo,text=True,capture_output=True)
    (args.out/"render.log").write_text(p.stdout+"\n--- STDERR ---\n"+p.stderr)
    if p.returncode!=0: raise RuntimeError("Cyclopean-1a Blender probe failed; see render.log")
    return out/f"fix_{step:02d}"


def execute(args) -> dict:
    args.repo=Path(args.repo).resolve(); args.parent=Path(args.parent).resolve(); args.out=Path(args.out).resolve()
    if args.out.exists(): raise FileExistsError("output must be new")
    args.out.mkdir(parents=True)
    check_kernel_equivalence()
    pm=_validate_parent(args.parent); args.profile=str(pm["profile"]); seed=int(pm["seed"])
    sm=load_map(args.parent/"surface_map.npz")
    parent_hash={n:_sha256(args.parent/n) for n in ("prediction_manifest.json","policy_trace.json","surface_map.npz")}
    before_topo,evidence,probe=_analyze_parent(args.parent,pm,sm)
    topo.write_visual(args.out/"cyclopean_before.png",before_topo,evidence,probe)
    save_map(args.out/"map_before.npz",sm)
    gazes=[tuple(map(float,g)) for g in pm["fixation_gazes_deg"]]
    result={"probe_taken":False,"probe_gaze_deg":None,"probe_target_points":None,"probe_fused":False,"idempotent_replay":None}
    after=before_topo; after_e=evidence; out_map=sm
    if probe is not None:
        gaze=tuple(float(x) for x in probe["gaze_deg"])
        if any(np.allclose(g,gaze,atol=1e-9) for g in gazes): raise AssertionError("topology probe revisits an existing gaze")
        step=len(gazes); case=_run_blender(args,seed,step,gaze)
        c,obs=hdr.read_observation(case); rec,_,state=compute_once(c,obs); pid=f"cyclopean_probe_{step:02d}"
        m=rec["valid"] & (rec["instance_id"] == public.OBJECT_ID)
        p=Patch(pid,rec["xyz_h"][m],rec["rgb_left"][m],rec["instance_id"][m])
        np.savez_compressed(args.out/"probe_patch.npz",xyz_h=p.xyz_h.astype(np.float32),rgb=p.rgb.astype(np.float32),instance_id=p.instance_id,valid=rec["valid"],oracle_instance_id=rec["instance_id"],raw_support_L=rec["raw_support_L"])
        Image.fromarray(_tone_preview(rec["rgb_left"])).save(args.out/"probe_rgb.png")
        contract=__import__("reality2b_public").empty_observation_contract(len(p.xyz_h))
        if contract["fuse_target_points"]:
            out_map,assoc=fuse(sm,p,public.OBJECT_ID,public.FUSION["association_radius_m"],public.FUSION["hash_cell_m"])
            replay,dup=fuse(out_map,p,public.OBJECT_ID,public.FUSION["association_radius_m"],public.FUSION["hash_cell_m"])
            idem=bool(dup["duplicate_patch"] and np.array_equal(out_map.xyz_h,replay.xyz_h) and np.array_equal(out_map.support_count,replay.support_count) and np.array_equal(out_map.provenance_mask,replay.provenance_mask))
            if not idem: raise AssertionError("topology probe replay is not idempotent")
        else:
            assoc={"new":0,"matched":0,"input_points":len(p.xyz_h)}; idem=None
        if set(np.unique(out_map.instance_id).tolist()) != {public.OBJECT_ID}:
            raise AssertionError("topology probe contaminated target map")
        # Reuse exactly the before chart so before/after hole areas are comparable.
        topo.add_observation(after_e,before_topo.chart,rec["xyz_h"],rec["instance_id"],rec["valid"],public.OBJECT_ID)
        after=topo.analyze(out_map.xyz_h,args.profile,after_e,chart=before_topo.chart,footprint_cells=before_topo.footprint_cells,footprint_deg=before_topo.footprint_radius_deg)
        topo.write_visual(args.out/"cyclopean_after.png",after,after_e,None)
        result={"probe_taken":True,"probe_gaze_deg":list(gaze),"probe_target_points":int(len(p.xyz_h)),"probe_fused":bool(contract["fuse_target_points"]),"idempotent_replay":idem,"new_surfels":int(assoc.get("new",0)),"matched_surfels":int(assoc.get("matched",0))}
    save_map(args.out/"surface_map.npz",out_map)
    fsg6run.save_ply(args.out/"surface_map.ply",out_map)
    before_holes=_strip_cells(before_topo.holes); after_holes=_strip_cells(after.holes)
    manifest={
        "schema":"Cyclopean1a-probe-v1","public_spec_sha256":public.public_digest(),"parent_spec":public.PARENT_SPEC_ID,
        "parent_record":str(args.parent),"parent_hashes":parent_hash,"seed":seed,"profile":args.profile,"fixture":public.FIXTURE,
        "fixed_head":True,"static_scene":True,"truth_opened":False,"parent_fixations_rerendered":0,"added_fixations":1 if result["probe_taken"] else 0,
        "grid_deg":before_topo.chart.grid_deg,"footprint_cells":before_topo.footprint_cells,"footprint_radius_deg":before_topo.footprint_radius_deg,
        "holes_before":before_holes,"holes_after":after_holes,"selected_probe":probe,"probe_result":result,
        "map_points_before":int(len(sm.xyz_h)),"map_points_after":int(len(out_map.xyz_h)),
    }
    json_write(args.out/"prediction_manifest.json",manifest)
    print("[cyclopean1a-probe] COMPLETE",json.dumps({"seed":seed,"holes_before":len(before_holes),"probe":result,"holes_after":len(after_holes)},sort_keys=True),flush=True)
    return manifest


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--repo",default="."); ap.add_argument("--parent",required=True); ap.add_argument("--out",required=True); ap.add_argument("--device",choices=("OPTIX","CUDA","CPU"),default="OPTIX"); ap.add_argument("--blender",default="blender")
    execute(ap.parse_args())


if __name__=="__main__": main()
