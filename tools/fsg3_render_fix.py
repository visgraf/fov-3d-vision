"""Blender-side acquisition of one FSG3 fixation pair.

One invocation renders exactly one yaw selected by the host frontier policy. It
never runs stereo. Geometry and texture are frozen by fsg3_scene; the host loop
cannot import that module.
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, sys, time, traceback
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import fsg_validation_render as base
import fsg3_public as public
import fsg3_scene as scene_spec
from fsg_geometry import json_write, make_calibration, pixels, rays_h
from fsg_scene import ray_mesh


def configure_backend() -> None:
    base.validation_objects = scene_spec.scene_objects
    base.validation_texture = scene_spec.scene_texture


def acquire_one(args: argparse.Namespace) -> dict:
    if args.seed != public.SEED:
        raise ValueError("only the frozen FSG3 seed is authorized")
    if args.step < 0 or args.step >= public.MAX_FIXATIONS:
        raise ValueError("step outside frozen FSG3 budget")
    expected = public.SEED_GAZE_YAW_DEG + round((args.yaw-public.SEED_GAZE_YAW_DEG)/public.POLICY["step_deg"]) * public.POLICY["step_deg"]
    if abs(expected-args.yaw) > 1e-8:
        raise ValueError("yaw is not on the frozen 5-degree policy lattice")
    if not (public.POLICY["yaw_min_deg"] <= args.yaw <= public.POLICY["yaw_max_deg"]):
        raise ValueError("yaw outside frozen policy range")
    spp = public.DEFAULT_SPP[args.profile]
    from bl_common import PROFILES
    if int(PROFILES[args.profile]["fix_spp"]) != spp:
        raise ValueError("repository profile spp changed")
    out=Path(args.out).resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"output must be new or empty: {out}")
    out.mkdir(parents=True,exist_ok=True)
    case=f"fix_{args.step:02d}"
    folder=out/case;folder.mkdir();ev=folder/"evaluation_only";ev.mkdir()
    calibration=make_calibration(args.profile,args.yaw,public.PITCH_DEG,public.VERGENCE_DISTANCE_M)
    configure_backend();base.check_renderer_equivalence()
    backend=base.ValidationBackend(args.device,args.save_blend)
    t_all=time.perf_counter();mesh=backend.prepare(case,calibration,folder,spp)
    np.savez_compressed(ev/"mesh.npz",**mesh);scene_spec.validate_mesh(mesh)
    obs={};seconds=[];seeds=[];t_oracle=0.;w,h=calibration["image_size_wh"];uv=pixels(w,h)
    for eye_id,eye in enumerate(calibration["eyes"]):
        render_seed=100000*public.SEED+100*args.step+eye_id
        rgb,secs=backend.render_eye(eye_id,calibration,folder,spp,render_seed)
        if rgb.shape!=(h,w,3) or not np.isfinite(rgb).all(): raise RuntimeError("bad RGB buffer")
        obs["rgb_"+eye["name"]]=rgb.astype(np.float32)
        t0=time.perf_counter();oracle=ray_mesh(np.asarray(eye["centre_h_m"]),rays_h(eye,uv),mesh);t_oracle+=time.perf_counter()-t0
        obs["instance_"+eye["name"]]=oracle["instance_id"]
        seconds.append(secs);seeds.append(render_seed)
    if seeds[0]==seeds[1]: raise RuntimeError("inter-eye seeds must differ")
    np.savez_compressed(folder/"observation.npz",**obs);json_write(folder/"calibration.json",calibration)
    acq={"schema":"FSG3-fixation-acquisition-v1","source":backend.source,"case":case,"step":args.step,
         "profile":args.profile,"yaw_deg":args.yaw,"pitch_deg":public.PITCH_DEG,"spp":spp,"seeds_lr":seeds,
         "blender_version":backend.version,"device":backend.device,"render_seconds_lr":seconds,
         "oracle_seconds":t_oracle,"primary_camera_samples":2*w*h*spp if backend.source=="blender_cycles" else 0,
         "nominal_camera_samples":2*w*h*spp,"adaptive_sampling":False,
         "segmentation":"oracle first-hit Blender pass_index; not antialiased","checks":backend.checks}
    json_write(folder/"acquisition.json",acq)
    run={"schema":"FSG3-fixation-run-v1","source":backend.source,"complete":True,
         "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"case":case,"step":args.step,
         "profile":args.profile,"seed":public.SEED,"yaw_deg":args.yaw,"spp":spp,
         "primary_camera_samples":acq["primary_camera_samples"],"public_spec_sha256":public.public_digest(),
         "truth_spec_sha256":scene_spec.truth_digest(),"total_wall_seconds":time.perf_counter()-t_all}
    json_write(out/"run.json",run)
    print(f"[fsg3-render] COMPLETE step={args.step} yaw={args.yaw:.3f} samples={acq['primary_camera_samples']}",flush=True)
    return run


def parse_args(argv:list[str])->argparse.Namespace:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("--out",required=True);ap.add_argument("--profile",choices=("small","full"),required=True)
    ap.add_argument("--seed",type=int,required=True);ap.add_argument("--step",type=int,required=True);ap.add_argument("--yaw",type=float,required=True)
    ap.add_argument("--device",choices=("OPTIX","CUDA","CPU"),default="OPTIX");ap.add_argument("--save-blend",action="store_true")
    return ap.parse_args(argv)


def main()->None:
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else sys.argv[1:]
    acquire_one(parse_args(argv))

if __name__=="__main__":
    try: main()
    except BaseException as exc:
        if isinstance(exc,SystemExit) and exc.code in (0,None): raise
        traceback.print_exc();print("[fsg3-render] FAILED",flush=True);sys.stdout.flush();sys.stderr.flush();os._exit(1)
