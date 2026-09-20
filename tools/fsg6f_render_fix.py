"""Blender-side acquisition of one FSG6f yaw/pitch fixation pair."""
from __future__ import annotations
import argparse
import datetime as dt
import os
import sys
import time
import traceback
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fsg_validation_render as base
import fsg6f_public as public
import fsg6f_scene as scene_spec
from fsg_geometry import json_write, make_calibration, pixels, rays_h
from fsg_scene import ray_mesh


def configure_backend(fixture: str) -> None:
    base.validation_objects = lambda _case: scene_spec.scene_objects(fixture)
    base.validation_texture = lambda instance, size=512: scene_spec.scene_texture(fixture, instance, size)


def acquire_one(args: argparse.Namespace) -> dict:
    if args.fixture not in public.FIXTURES or args.seed not in public.SEEDS:
        raise ValueError("fixture/seed outside frozen FSG6f schedule")
    if args.step < 0 or args.step >= public.MAX_BUDGET_FIXATIONS:
        raise ValueError("step outside frozen FSG6f budget")
    spp = public.DEFAULT_SPP[args.profile]
    from bl_common import PROFILES
    if int(PROFILES[args.profile]["fix_spp"]) != spp:
        raise ValueError("repository profile spp changed")
    out=Path(args.out).resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"output must be new or empty: {out}")
    out.mkdir(parents=True, exist_ok=True); case=f"fix_{args.step:02d}"; folder=out/case; folder.mkdir(); ev=folder/"evaluation_only"; ev.mkdir()
    calibration=make_calibration(args.profile,args.yaw,args.pitch,public.VERGENCE_DISTANCE_M)
    configure_backend(args.fixture); base.check_renderer_equivalence(); backend=base.ValidationBackend(args.device,args.save_blend)
    t_all=time.perf_counter(); mesh=backend.prepare(case,calibration,folder,spp); np.savez_compressed(ev/"mesh.npz",**mesh); scene_spec.validate_mesh(args.fixture,mesh)
    obs={}; seconds=[]; seeds=[]; t_oracle=0.0; w,h=calibration["image_size_wh"]; uv=pixels(w,h)
    for eye_id,eye in enumerate(calibration["eyes"]):
        seed=public.render_seed(args.fixture,args.seed,args.yaw,args.pitch,eye_id)
        rgb,secs=backend.render_eye(eye_id,calibration,folder,spp,seed)
        if rgb.shape!=(h,w,3) or not np.isfinite(rgb).all(): raise RuntimeError("bad RGB buffer")
        obs["rgb_"+eye["name"]]=rgb.astype(np.float32); t0=time.perf_counter(); oracle=ray_mesh(np.asarray(eye["centre_h_m"]),rays_h(eye,uv),mesh); t_oracle+=time.perf_counter()-t0
        obs["instance_"+eye["name"]]=oracle["instance_id"]; seconds.append(secs); seeds.append(seed)
    if seeds[0]==seeds[1]: raise RuntimeError("inter-eye seeds must differ")
    np.savez_compressed(folder/"observation.npz",**obs); json_write(folder/"calibration.json",calibration)
    acq={"schema":"FSG6f-fixation-acquisition-v1","source":backend.source,"case":case,"step":args.step,"fixture":args.fixture,"profile":args.profile,
         "yaw_deg":args.yaw,"pitch_deg":args.pitch,"spp":spp,"seeds_lr":seeds,"blender_version":backend.version,"device":backend.device,
         "render_seconds_lr":seconds,"oracle_seconds":t_oracle,"primary_camera_samples":2*w*h*spp if backend.source=="blender_cycles" else 0,
         "nominal_camera_samples":2*w*h*spp,"adaptive_sampling":False,"segmentation":"oracle first-hit Blender pass_index; not antialiased","checks":backend.checks}
    json_write(folder/"acquisition.json",acq)
    run={"schema":"FSG6f-fixation-run-v1","source":backend.source,"complete":True,"created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
         "case":case,"step":args.step,"fixture":args.fixture,"profile":args.profile,"seed":args.seed,"yaw_deg":args.yaw,"pitch_deg":args.pitch,"spp":spp,
         "seeds_lr":seeds,"primary_camera_samples":acq["primary_camera_samples"],"public_spec_sha256":public.public_digest(),
         "truth_spec_sha256":scene_spec.truth_digest(args.fixture),"total_wall_seconds":time.perf_counter()-t_all}
    json_write(out/"run.json",run)
    print(f"[fsg6f-render] COMPLETE fixture={args.fixture} seed={args.seed} step={args.step} yaw={args.yaw:.3f} pitch={args.pitch:.3f} samples={acq['primary_camera_samples']}",flush=True)
    return run


def parse_args(argv:list[str])->argparse.Namespace:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--out",required=True); ap.add_argument("--profile",choices=("small","full"),required=True)
    ap.add_argument("--fixture",choices=public.FIXTURES,required=True); ap.add_argument("--seed",type=int,choices=public.SEEDS,required=True); ap.add_argument("--step",type=int,required=True)
    ap.add_argument("--yaw",type=float,required=True); ap.add_argument("--pitch",type=float,required=True); ap.add_argument("--device",choices=("OPTIX","CUDA","CPU"),default="OPTIX"); ap.add_argument("--save-blend",action="store_true")
    return ap.parse_args(argv)


def main()->None:
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else sys.argv[1:]; acquire_one(parse_args(argv))

if __name__=="__main__":
    try: main()
    except BaseException as exc:
        if isinstance(exc,SystemExit) and exc.code in (0,None): raise
        traceback.print_exc(); print("[fsg6f-render] FAILED",flush=True); sys.stdout.flush(); sys.stderr.flush(); os._exit(1)
