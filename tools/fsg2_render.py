"""Acquire the two prescribed FSG2 fixation pairs in Blender."""
from __future__ import annotations
import argparse, json, os, sys, traceback
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import fsg_validation_render as base
import fsg2_scene as spec
from fsg_geometry import json_write

def configure_base() -> None:
    base.CASES=spec.CASES; base.CASE_GAZE=spec.CASE_GAZE
    base.validation_objects=spec.scene_objects; base.validation_texture=spec.scene_texture

def acquire_fsg2(args: argparse.Namespace) -> dict:
    if args.seed != spec.SEED: raise ValueError("only the prospective FSG2 seed is authorized")
    if args.spp != spec.DEFAULT_SPP[args.profile] or args.case != "all":
        raise ValueError("only the complete prescribed two-fixation suite at default spp is authorized")
    configure_base(); base.check_renderer_equivalence()
    out=Path(args.out).resolve(); run=base.acquire(args,base.ValidationBackend(args.device,args.save_blend))
    try:
        meshes=[]
        for name in spec.CASES:
            with np.load(out/name/"evaluation_only"/"mesh.npz",allow_pickle=False) as f: mesh={k:f[k] for k in f.files}
            spec.validate_mesh(mesh); meshes.append(mesh)
        if not np.array_equal(meshes[0]["instance_ids"],meshes[1]["instance_ids"]) or not np.allclose(meshes[0]["triangles_h"],meshes[1]["triangles_h"],atol=0,rtol=0):
            raise ValueError("geometry must be identical across fixations")
        json_write(out/"fsg2_spec.json",{"spec":spec.SPEC,"sha256":spec.spec_digest()})
        run.update(fsg2_spec_id=spec.SPEC_ID,fsg2_spec_sha256=spec.spec_digest())
        json_write(out/"run.json",run)
    except BaseException:
        (out/"run.json").unlink(missing_ok=True); raise
    print("[fsg2-render] COMPLETE spec="+spec.spec_digest(),flush=True); return run

def parse_args(argv:list[str])->argparse.Namespace:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--out",required=True)
    ap.add_argument("--profile",choices=("small","full"),required=True); ap.add_argument("--seed",type=int,default=spec.SEED)
    ap.add_argument("--device",choices=("OPTIX","CUDA","CPU"),default="OPTIX"); ap.add_argument("--save-blend",action="store_true")
    a=ap.parse_args(argv); a.case="all"; a.spp=spec.DEFAULT_SPP[a.profile]; a.profile_default_spp=a.spp; return a

def main()->None:
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else sys.argv[1:]; a=parse_args(argv)
    from bl_common import PROFILES
    if int(PROFILES[a.profile]["fix_spp"])!=a.spp: raise ValueError("repository profile spp changed")
    acquire_fsg2(a)
if __name__=="__main__":
    try: main()
    except BaseException as exc:
        if isinstance(exc,SystemExit) and exc.code in (0,None): raise
        traceback.print_exc(); print("[fsg2-render] FAILED",flush=True); sys.stdout.flush();sys.stderr.flush();os._exit(1)
