"""Render one fixation through the foveated OSL custom camera.

    blender -b scene.blend -P tools/render_foveated.py -- --out fix/f000 [--yaw 20 --pitch -5]

Writes to --out:
    fix.exr    Combined + Depth (ray distance) + Normal + Position, 32-bit, single part
    meta.json  camera pose actually rendered, warp parameters, raster size, device, timing

The raster is square and the warp fills its inscribed disc; everything outside the disc
gets zero throughput. Mask with the analytic r <= 1 test on the raster index, never with
alpha (see the note in tools/foveated_camera.osl).

Resolution follows from the warp: N = 2 * (E2/s0) * ln(1 + e_max/E2), so --s0 sets the
foveal spacing and the raster size together. Pass --n to override and let s0 follow instead.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import traceback

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bl_common import (add_profile, configure_multilayer_exr, ensure_cycles, eye_record,  # noqa: E402
                       find_eye, pin_seed, rigid, script_args, setup_device)

HERE = os.path.dirname(os.path.abspath(__file__))


def raster_size(s0_deg: float, e2_deg: float, emax_deg: float) -> int:
    """Pixels across so that spacing at the centre is s0."""
    return int(round(2.0 * (e2_deg / s0_deg) * math.log(1.0 + emax_deg / e2_deg)))


def s0_of(n: int, e2_deg: float, emax_deg: float) -> float:
    return 2.0 * e2_deg * math.log(1.0 + emax_deg / e2_deg) / n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blend", help="open this file first")
    ap.add_argument("--out", required=True)
    ap.add_argument("--e2", type=float, default=2.0, help="eccentricity at which spacing doubles, deg")
    ap.add_argument("--emax", type=float, default=45.0, help="half-field of the warp, deg")
    ap.add_argument("--s0", type=float, default=0.05, help="foveal spacing, deg/sample")
    ap.add_argument("--n", type=int, default=None, help="raster size override; s0 is then derived")
    ap.add_argument("--yaw", type=float, default=0.0, help="gaze, deg right, about the eye centre")
    ap.add_argument("--pitch", type=float, default=0.0, help="gaze, deg up, about the eye centre")
    ap.add_argument("--spp", type=int, default=64)
    ap.add_argument("--device", default="OPTIX", choices=["OPTIX", "CUDA", "CPU"])
    ap.add_argument("--shader", default=os.path.join(HERE, "foveated_camera.osl"))
    add_profile(ap, script_args(), s0="s0", spp="fix_spp")
    args = ap.parse_args(script_args())

    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args.blend))
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)

    scene = bpy.context.scene
    ensure_cycles(scene)
    backend = setup_device(scene, args.device)
    bpy.context.view_layer.update()  # rotation_euler does not reach matrix_world until the depsgraph runs
    eye, eye_note = find_eye(scene)

    n = args.n if args.n else raster_size(args.s0, args.e2, args.emax)
    s0 = s0_of(n, args.e2, args.emax)
    print(f"[foveated] {eye_note}; device {backend}; raster {n}x{n}; "
          f"s0 {s0:.4f} deg; E2 {args.e2} deg; e_max {args.emax} deg")

    text = bpy.data.texts.load(os.path.abspath(args.shader))
    cam_data = bpy.data.cameras.new("FOVEATED")
    cam_data.type = "CUSTOM"
    cam_data.custom_mode = "INTERNAL"
    cam_data.custom_shader = text
    cam_data.clip_start, cam_data.clip_end = 0.001, 1.0e5
    cam_data.dof.use_dof = False
    if not cam_data.custom_bytecode:
        raise SystemExit("OSL camera shader did not compile; see the console above for the error.")
    for name, value in (("E2", args.e2), ("e_max", args.emax)):
        cam_data.cycles_custom[name] = value

    cam = bpy.data.objects.new("FOVEATED", cam_data)
    scene.collection.objects.link(cam)
    # Gaze is a rotation about the eye centre. Intrinsic yaw-then-pitch, so the resulting
    # elevation equals --pitch exactly; the Y sign is negated so +yaw turns right.
    cam.matrix_world = (rigid(eye.matrix_world)
                        @ Matrix.Rotation(math.radians(-args.yaw), 4, "Y")
                        @ Matrix.Rotation(math.radians(args.pitch), 4, "X"))
    scene.camera = cam
    bpy.context.view_layer.update()

    r = scene.render
    r.resolution_x = r.resolution_y = n
    r.resolution_percentage = 100
    r.film_transparent = r.use_motion_blur = False
    r.use_compositing = r.use_sequencer = False
    r.use_single_layer = True
    c = scene.cycles
    for what in pin_seed(scene):        # a keyframed seed would silently reuse one seed per session
        print(f"[foveated] removed {what}")
    c.samples, c.seed = args.spp, 0
    c.use_adaptive_sampling = False
    c.pixel_filter_type, c.filter_width = "BOX", 1.0
    try:
        c.use_denoising = False
    except (AttributeError, TypeError):
        pass

    vl = bpy.context.view_layer
    vl.use_pass_combined = vl.use_pass_z = vl.use_pass_normal = vl.use_pass_position = True
    configure_multilayer_exr(scene)
    r.filepath = os.path.join(out, "fix.exr")
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    seconds = time.time() - t0

    m = cam.matrix_world.to_3x3()
    meta = {
        "blend": bpy.data.filepath, "scene": scene.name,
        "fov_kind": scene.get("fov_kind", "unknown"), "blender": bpy.app.version_string,
        "eye": eye_record(eye), "eye_note": eye_note,
        "profile": args.profile,
        "gaze_yaw_deg": args.yaw, "gaze_pitch_deg": args.pitch,
        "camera_position_m": [round(x, 6) for x in cam.matrix_world.translation],
        "camera_forward": [round(x, 6) for x in (m @ Vector((0.0, 0.0, -1.0)))],
        "camera_right": [round(x, 6) for x in (m @ Vector((1.0, 0.0, 0.0)))],
        "camera_up": [round(x, 6) for x in (m @ Vector((0.0, 1.0, 0.0)))],
        "warp": {"form": "e(r) = E2 * ((1 + e_max/E2)^r - 1), r = 2*hypot(u-0.5, v-0.5)",
                 "E2_deg": args.e2, "e_max_deg": args.emax, "s0_deg": s0, "raster": n},
        "spp": args.spp, "device": backend, "pixel_filter": "BOX", "filter_width": 1.0,
        "render_seconds": round(seconds, 3),
        "depth_pass": "ray distance from the camera centre; background = 1e10",
        "mask": "valid samples are r <= 1; alpha is NOT a valid mask",
    }
    with open(os.path.join(out, "meta.json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    print(f"[foveated] wrote {out} ({seconds:.2f}s on {backend})")


def run():
    """`blender -b -P` exits 0 even when the script raised (CLAUDE.md), so a tool that writes an
    artifact must make its own failure loud: traceback, a FAILED line, exit 1."""
    try:
        main()
    except BaseException:
        traceback.print_exc()
        print("[foveated] FAILED", flush=True)
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)


if __name__ == "__main__":
    run()
