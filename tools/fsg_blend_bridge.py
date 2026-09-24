"""Generic .blend -> FSG1 local tangent-pair acquisition bridge.

Run inside Blender on an already loaded mesh scene:

    blender -b scenes/classroom/classroom_eye.blend --python-exit-code 1 \
      -P tools/fsg_blend_bridge.py -- \
      --out previews/fsg-bridge1/classroom-small --profile small \
      --yaw-deg 0 --pitch-deg 0 --vergence-m 2.10 --device OPTIX

The bridge deliberately does NOT use the foveated warp or stereo_field.  A fixation
creates the same padded local perspective cameras used by FSG1, renders RGB in the
original .blend, and writes the existing FSG1 observation contract:

    calibration.json
    observation.npz  # exactly rgb_L, rgb_R, instance_L, instance_R

Blender ray casting supplies oracle instance IDs and evaluator-only first-hit range.
No Blender depth/range is written into observation.npz.  The unchanged host-side
fsg_stereo.py performs rectification, SGBM and head-frame reconstruction.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback

import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bl_common import ensure_cycles, find_eye, pin_seed, rigid, setup_device
from fsg_geometry import (
    CV_TO_BLENDER,
    gaze_direction,
    head_to_world,
    json_write,
    make_calibration,
    pixels,
    rays_h,
    world_to_head,
)
import rig


SOURCE = "blender_scene_tangent_perspective"
SCHEMA = "FSG-BLEND-BRIDGE1-acquisition-v1"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def root_name(obj: bpy.types.Object) -> str:
    cur = getattr(obj, "original", obj)
    while cur.parent is not None:
        cur = cur.parent
    return cur.name


def instance_table(scene: bpy.types.Scene) -> tuple[dict[str, int], dict]:
    """Deterministic parent-root grouping; zero is reserved for no mesh hit."""
    mesh_objects = [o for o in scene.objects if o.type == "MESH" and not o.hide_render]
    roots = sorted({root_name(o) for o in mesh_objects})
    mapping = {name: i + 1 for i, name in enumerate(roots)}
    return mapping, {
        "rule": "topmost parent root over renderable mesh objects; sorted root names; ids 1..N",
        "mesh_object_count": len(mesh_objects),
        "group_count": len(mapping),
        "groups": [{"id": mapping[name], "root": name} for name in roots],
    }


def configure_scene(scene: bpy.types.Scene, c: dict, spp: int, prefer_device: str) -> str:
    ensure_cycles(scene)
    device = setup_device(scene, prefer_device)
    if device == "CPU" and prefer_device != "CPU":
        raise RuntimeError("requested GPU backend unavailable; use --device CPU only deliberately")
    pin_seed(scene)
    scene.render.resolution_x, scene.render.resolution_y = c["image_size_wh"]
    scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = scene.render.pixel_aspect_y = 1.0
    scene.render.use_border = False
    scene.render.use_compositing = False
    scene.render.use_sequencer = False
    scene.render.film_transparent = False
    scene.render.use_motion_blur = False
    scene.render.image_settings.media_type = "IMAGE"
    scene.render.image_settings.file_format = "OPEN_EXR"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "32"
    scene.render.image_settings.exr_codec = "ZIP"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    scene.cycles.samples = spp
    scene.cycles.use_adaptive_sampling = False
    scene.cycles.use_denoising = False
    scene.cycles.time_limit = 0.0
    scene.cycles.pixel_filter_type = "BOX"
    scene.cycles.filter_width = 1.0
    return device


def create_cameras(scene: bpy.types.Scene, c: dict) -> list[bpy.types.Object]:
    """Create temporary Blender perspective cameras exactly from FSG calibration."""
    head_r = np.asarray(c["head_R_wh"], float)
    head_o = np.asarray(c["head_origin_w_m"], float)
    target_h = gaze_direction(*c["gaze_yaw_pitch_deg"]) * c["prescribed_vergence_distance_m"]
    pair = rig.pair_for_point(head_to_world(c, target_h), head_o, head_r, c["ipd_m"])
    out = []
    w, _ = c["image_size_wh"]
    for k, eye in enumerate(c["eyes"]):
        g = pair["eyes"][k]
        pos_w, rb = rig.camera_pose(
            head_o,
            head_r,
            rig.eye_offsets_local(c["ipd_m"])[k],
            g["yaw"],
            g["pitch"],
        )
        actual_r_hc = head_r.T @ rb @ CV_TO_BLENDER
        if not np.allclose(actual_r_hc, np.asarray(eye["R_hc"]), atol=1e-9):
            raise RuntimeError("repository rig and FSG calibration disagree")
        if not np.allclose(world_to_head(c, pos_w), np.asarray(eye["centre_h_m"]), atol=1e-9):
            raise RuntimeError("repository rig and FSG eye centres disagree")

        data = bpy.data.cameras.new("FSG_BRIDGE_" + eye["name"])
        data.type = "PERSP"
        data.sensor_fit = "HORIZONTAL"
        data.sensor_width = 36.0
        data.sensor_height = 36.0
        data.shift_x = data.shift_y = 0.0
        data.lens = float(eye["K"][0][0]) * data.sensor_width / float(w)
        data.clip_start = 0.01
        data.clip_end = 100.0
        data.dof.use_dof = False
        cam = bpy.data.objects.new("FSG_BRIDGE_" + eye["name"], data)
        scene.collection.objects.link(cam)
        m = np.eye(4)
        m[:3, :3] = rb
        m[:3, 3] = pos_w
        cam.matrix_world = Matrix(m.tolist())
        out.append(cam)
    bpy.context.view_layer.update()
    return out


def projection_check(scene: bpy.types.Scene, c: dict, cameras: list[bpy.types.Object]) -> dict:
    """Independent Blender projection check against declared FSG pixel geometry."""
    from bpy_extras.object_utils import world_to_camera_view
    w, h = c["image_size_wh"]
    rng = np.random.default_rng(812)
    uv = rng.uniform([7, 7], [w - 8, h - 8], (41, 2))
    worst = 0.0
    for eye, cam in zip(c["eyes"], cameras):
        d = rays_h(eye, uv)
        origin = np.asarray(eye["centre_h_m"], float)
        xyz_h = origin + 2.0 * d
        for p_w, expected in zip(head_to_world(c, xyz_h), uv):
            ndc = world_to_camera_view(scene, cam, Vector(p_w.tolist()))
            got = np.array([ndc.x * w - 0.5, (1.0 - ndc.y) * h - 0.5])
            worst = max(worst, float(np.max(np.abs(got - expected))))
    if worst > 0.002:
        raise RuntimeError(f"Blender/FSG projection mismatch: {worst:.6g} px > 0.002")
    return {"projection_max_error_px": worst, "projection_samples_per_eye": len(uv)}


def render_rgb(scene: bpy.types.Scene, camera: bpy.types.Object, path: Path, spp: int, seed: int) -> tuple[np.ndarray, float]:
    scene.camera = camera
    scene.cycles.samples = spp
    scene.cycles.seed = seed
    scene.update_tag()
    bpy.context.view_layer.update()
    t0 = time.perf_counter()
    bpy.ops.render.render()
    elapsed = time.perf_counter() - t0
    if scene.cycles.seed != seed:
        raise RuntimeError("Cycles seed did not remain pinned")
    bpy.data.images["Render Result"].save_render(str(path), scene=scene)
    loaded = bpy.data.images.load(str(path), check_existing=False)
    try:
        w, h = scene.render.resolution_x, scene.render.resolution_y
        n = len(loaded.pixels)
        channels = n // (w * h)
        if channels < 3 or n != w * h * channels:
            raise RuntimeError("EXR RGB buffer unavailable")
        a = np.empty(n, np.float32)
        loaded.pixels.foreach_get(a)
        rgb = a.reshape(h, w, channels)[::-1, :, :3].copy()
    finally:
        bpy.data.images.remove(loaded)
    if not np.isfinite(rgb).all() or float(rgb.std()) < 1e-6:
        raise RuntimeError("rendered RGB is empty, non-finite, or constant")
    return rgb, elapsed


def raycast_ids_and_truth(scene: bpy.types.Scene, c: dict, eye: dict, group_ids: dict[str, int]) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Pixel-centre first-hit IDs plus evaluator-only range/position.

    This is intentionally simple and one-fixation oriented.  It is not the final
    high-throughput implementation.  Truth arrays are written only under
    evaluation_only/ and are never included in observation.npz.
    """
    w, h = c["image_size_wh"]
    uv = pixels(w, h)
    dirs_h = rays_h(eye, uv).reshape(-1, 3)
    head_r = np.asarray(c["head_R_wh"], float)
    origin_h = np.asarray(eye["centre_h_m"], float)
    origin_w = head_to_world(c, origin_h)
    dirs_w = dirs_h @ head_r.T
    ids = np.zeros(len(dirs_w), np.int32)
    ranges = np.full(len(dirs_w), np.nan, np.float32)
    xyz_h = np.full((len(dirs_w), 3), np.nan, np.float32)
    dg = bpy.context.evaluated_depsgraph_get()
    ovec = Vector(origin_w.tolist())
    t0 = time.perf_counter()
    unknown_roots = set()
    for i, dw in enumerate(dirs_w):
        hit, loc, normal, face, obj, matrix = scene.ray_cast(
            dg, ovec, Vector(dw.tolist()), distance=100.0
        )
        if not hit or obj is None:
            continue
        name = root_name(obj)
        gid = group_ids.get(name)
        if gid is None:
            unknown_roots.add(name)
            continue
        p_h = world_to_head(c, np.asarray(loc, float))
        ids[i] = gid
        xyz_h[i] = p_h.astype(np.float32)
        ranges[i] = np.float32(np.linalg.norm(p_h - origin_h))
    if unknown_roots:
        raise RuntimeError("ray cast hit roots outside deterministic instance table: " + ", ".join(sorted(unknown_roots)[:8]))
    return ids.reshape(h, w), ranges.reshape(h, w), xyz_h.reshape(h, w, 3), time.perf_counter() - t0


def build_calibration(scene: bpy.types.Scene, profile: str, yaw: float, pitch: float, vergence: float, ipd: float) -> tuple[dict, str]:
    eye, source = find_eye(scene)
    m = rigid(eye.matrix_world)
    head_r = np.asarray(m.to_3x3(), float)
    head_o = np.asarray(m.translation, float)
    c = make_calibration(
        profile,
        yaw,
        pitch,
        vergence_distance=vergence,
        ipd=ipd,
        head_r_wh=head_r,
        head_origin_w=head_o,
    )
    c["scene_eye_source"] = source
    return c, source


def acquire(args: argparse.Namespace) -> dict:
    out = Path(args.out).resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"output must be new or empty: {out}")
    out.mkdir(parents=True, exist_ok=True)
    eval_dir = out / "evaluation_only"
    eval_dir.mkdir()

    scene = bpy.context.scene
    blend = Path(bpy.data.filepath).resolve() if bpy.data.filepath else None
    if blend is None or not blend.is_file():
        raise RuntimeError("bridge requires a saved .blend opened by Blender")
    c, eye_source = build_calibration(scene, args.profile, args.yaw_deg, args.pitch_deg, args.vergence_m, args.ipd_m)
    spp = args.spp
    if spp is None:
        from bl_common import PROFILES
        spp = int(PROFILES[args.profile]["fix_spp"])
    device = configure_scene(scene, c, spp, args.device)
    group_ids, grouping = instance_table(scene)
    cams = create_cameras(scene, c)
    geometry_checks = projection_check(scene, c, cams)

    obs = {}
    render_seconds = []
    raycast_seconds = []
    seeds = []
    truth_summary = {}
    for eye_id, eye in enumerate(c["eyes"]):
        seed = 10000 * args.seed + eye_id
        rgb, rsec = render_rgb(scene, cams[eye_id], out / f"{eye['name']}.exr", spp, seed)
        ids, ranges, xyz_h, tsec = raycast_ids_and_truth(scene, c, eye, group_ids)
        obs["rgb_" + eye["name"]] = rgb.astype(np.float32)
        obs["instance_" + eye["name"]] = ids.astype(np.int32)
        np.savez_compressed(eval_dir / f"truth_{eye['name']}.npz", instance_id=ids, range_m=ranges, xyz_h=xyz_h)
        render_seconds.append(rsec)
        raycast_seconds.append(tsec)
        seeds.append(seed)
        truth_summary[eye["name"]] = {
            "hit_pixels": int((ids > 0).sum()),
            "hit_fraction": float((ids > 0).mean()),
        }

    if set(obs) != {"rgb_L", "rgb_R", "instance_L", "instance_R"}:
        raise RuntimeError("observation contract changed unexpectedly")
    np.savez_compressed(out / "observation.npz", **obs)
    json_write(out / "calibration.json", c)
    json_write(eval_dir / "instance_groups.json", grouping)
    meta = {
        "schema": SCHEMA,
        "source": SOURCE,
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "scene_path": str(blend),
        "scene_sha256": sha256(blend),
        "scene_name": scene.name,
        "eye_source": eye_source,
        "profile": args.profile,
        "spp": spp,
        "seed": args.seed,
        "seeds_lr": seeds,
        "device": device,
        "blender_version": bpy.app.version_string,
        "gaze_yaw_pitch_deg": [args.yaw_deg, args.pitch_deg],
        "vergence_m": args.vergence_m,
        "ipd_m": args.ipd_m,
        "render_seconds_lr": render_seconds,
        "raycast_seconds_lr": raycast_seconds,
        "truth_summary": truth_summary,
        "instance_grouping": grouping,
        "geometry_checks": geometry_checks,
        "sensor_contract": "local padded perspective pair; FSG1 tangent-plane acquisition",
        "stereo_contract": "host tools/fsg_stereo.py unchanged",
        "truth_in_observation": False,
        "foveated_warp_used": False,
        "stereo_field_used": False,
    }
    json_write(out / "acquisition.json", meta)
    json_write(out / "run.json", {
        "schema": "FSG-BLEND-BRIDGE1-run-v1",
        "complete": True,
        "case": "single_fixation",
        "source": SOURCE,
        "profile": args.profile,
        "scene_sha256": meta["scene_sha256"],
    })
    print(
        "[fsg-blend-bridge] COMPLETE "
        f"scene={blend.name} profile={args.profile} gaze=({args.yaw_deg:.3f},{args.pitch_deg:.3f}) "
        f"raster={c['image_size_wh'][0]}x{c['image_size_wh'][1]} groups={grouping['group_count']} "
        f"hitsL={truth_summary['L']['hit_fraction']:.4f} hitsR={truth_summary['R']['hit_fraction']:.4f}"
    )
    return meta


def parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--profile", choices=("small", "full"), default="small")
    ap.add_argument("--yaw-deg", type=float, required=True)
    ap.add_argument("--pitch-deg", type=float, required=True)
    ap.add_argument("--vergence-m", type=float, default=2.10)
    ap.add_argument("--ipd-m", type=float, default=0.063)
    ap.add_argument("--device", choices=("OPTIX", "CUDA", "CPU"), default="OPTIX")
    ap.add_argument("--spp", type=int, default=None)
    ap.add_argument("--seed", type=int, default=2111)
    args = ap.parse_args(argv)
    if args.vergence_m <= 0 or args.ipd_m <= 0:
        ap.error("vergence and ipd must be positive")
    if args.spp is not None and args.spp < 1:
        ap.error("spp must be positive")
    return args


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    acquire(parse_args(argv))


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        if isinstance(e, SystemExit) and e.code in (0, None):
            raise
        traceback.print_exc()
        print(f"[fsg-blend-bridge] FAILED {type(e).__name__}: {e}", flush=True)
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)
