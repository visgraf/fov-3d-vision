"""Generic fixed-head scene acquisition using the frozen Reality physical instrument.

This is acquisition plumbing, not a new perception policy.  It intentionally
matches Reality Check 2's scene, texture, camera calibration, vergence, SPP,
physical-view RNG seed function, Cycles backend and oracle first-hit masks, but
it does not inherit Reality Check 2's experiment-specific global step interval.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import time
import traceback
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fsg_validation_render as base
import reality2_public as instrument
import reality1_scene as scene_spec
from fsg_geometry import json_write, make_calibration, pixels, rays_h
from fsg_scene import ray_mesh

SCHEMA_ID = "SceneFixation-generic-v1"


def public_digest() -> str:
    spec = {
        "id": SCHEMA_ID,
        "instrument": instrument.INSTRUMENT_ID,
        "fixture": instrument.FIXTURE,
        "fixed_head": True,
        "static_scene": True,
        "vergence_distance_m": instrument.VERGENCE_DISTANCE_M,
        "spp": instrument.DEFAULT_SPP,
        "render_seed": "delegate reality2_public.render_seed",
        "difference_from_reality2_render_fix": "no experiment-specific global-step admission interval",
    }
    return hashlib.sha256(json.dumps(spec, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def configure_backend() -> None:
    base.validation_objects = lambda _case: scene_spec.scene_objects(instrument.FIXTURE)
    base.validation_texture = lambda instance, size=512: scene_spec.scene_texture(instrument.FIXTURE, instance, size)


def acquire_one(args: argparse.Namespace) -> dict:
    if args.seed not in instrument.SEEDS:
        raise ValueError("seed outside frozen Reality instrument seeds")
    if args.step < 0:
        raise ValueError("global acquisition step must be non-negative")
    spp = instrument.DEFAULT_SPP[args.profile]
    from bl_common import PROFILES
    if int(PROFILES[args.profile]["fix_spp"]) != spp:
        raise ValueError("repository profile spp changed")
    out = Path(args.out).resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"output must be new or empty: {out}")
    out.mkdir(parents=True, exist_ok=True)
    case = f"fix_{args.step:02d}"
    folder = out / case
    folder.mkdir()
    ev = folder / "evaluation_only"
    ev.mkdir()
    calibration = make_calibration(args.profile, args.yaw, args.pitch, instrument.VERGENCE_DISTANCE_M)
    configure_backend()
    base.check_renderer_equivalence()
    backend = base.ValidationBackend(args.device, args.save_blend)
    t_all = time.perf_counter()
    mesh = backend.prepare(case, calibration, folder, spp)
    np.savez_compressed(ev / "mesh.npz", **mesh)
    scene_spec.validate_mesh(mesh)
    obs = {}
    seconds = []
    seeds = []
    t_oracle = 0.0
    w, h = calibration["image_size_wh"]
    uv = pixels(w, h)
    for eye_id, eye in enumerate(calibration["eyes"]):
        rseed = instrument.render_seed(args.seed, args.yaw, args.pitch, eye_id)
        rgb, secs = backend.render_eye(eye_id, calibration, folder, spp, rseed)
        if rgb.shape != (h, w, 3) or not np.isfinite(rgb).all():
            raise RuntimeError("bad RGB buffer")
        obs["rgb_" + eye["name"]] = rgb.astype(np.float32)
        t0 = time.perf_counter()
        oracle = ray_mesh(np.asarray(eye["centre_h_m"]), rays_h(eye, uv), mesh)
        t_oracle += time.perf_counter() - t0
        obs["instance_" + eye["name"]] = oracle["instance_id"]
        seconds.append(secs)
        seeds.append(rseed)
    if seeds[0] == seeds[1]:
        raise RuntimeError("inter-eye seeds must differ")
    np.savez_compressed(folder / "observation.npz", **obs)
    json_write(folder / "calibration.json", calibration)
    acq = {
        "schema": "SceneFixation-acquisition-v1",
        "scene_renderer": SCHEMA_ID,
        "scene_renderer_public_sha256": public_digest(),
        "instrument_public_sha256": instrument.public_digest(),
        "source": backend.source,
        "case": case,
        "step": args.step,
        "fixture": instrument.FIXTURE,
        "profile": args.profile,
        "yaw_deg": args.yaw,
        "pitch_deg": args.pitch,
        "spp": spp,
        "seeds_lr": seeds,
        "blender_version": backend.version,
        "device": backend.device,
        "render_seconds_lr": seconds,
        "oracle_seconds": t_oracle,
        "primary_camera_samples": 2 * w * h * spp if backend.source == "blender_cycles" else 0,
        "nominal_camera_samples": 2 * w * h * spp,
        "adaptive_sampling": False,
        "segmentation": "oracle first-hit exported Blender mesh; pixel centre; not antialiased",
        "scene_character": "unchanged Reality Check 1 mixed-texture nonplanar target with tabletop clutter",
        "checks": backend.checks,
    }
    json_write(folder / "acquisition.json", acq)
    run = {
        "schema": "SceneFixation-run-v1",
        "scene_renderer": SCHEMA_ID,
        "scene_renderer_public_sha256": public_digest(),
        "instrument_public_sha256": instrument.public_digest(),
        "source": backend.source,
        "complete": True,
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "case": case,
        "step": args.step,
        "fixture": instrument.FIXTURE,
        "profile": args.profile,
        "seed": args.seed,
        "yaw_deg": args.yaw,
        "pitch_deg": args.pitch,
        "spp": spp,
        "seeds_lr": seeds,
        "primary_camera_samples": acq["primary_camera_samples"],
        "truth_spec_sha256": scene_spec.truth_digest(),
        "total_wall_seconds": time.perf_counter() - t_all,
    }
    json_write(out / "run.json", run)
    print(
        f"[scene-render] COMPLETE seed={args.seed} step={args.step} "
        f"yaw={args.yaw:.3f} pitch={args.pitch:.3f} samples={acq['primary_camera_samples']}",
        flush=True,
    )
    return run


def parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--profile", choices=("small", "full"), required=True)
    ap.add_argument("--seed", type=int, choices=instrument.SEEDS, required=True)
    ap.add_argument("--step", type=int, required=True)
    ap.add_argument("--yaw", type=float, required=True)
    ap.add_argument("--pitch", type=float, required=True)
    ap.add_argument("--device", choices=("OPTIX", "CUDA", "CPU"), default="OPTIX")
    ap.add_argument("--save-blend", action="store_true")
    return ap.parse_args(argv)


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    acquire_one(parse_args(argv))


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        if isinstance(exc, SystemExit) and exc.code in (0, None):
            raise
        traceback.print_exc()
        print("[scene-render] FAILED", flush=True)
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)
