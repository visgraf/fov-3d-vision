"""Measure the Monte Carlo noise floor at the reference sampling scale.

    blender -b scene.blend -P tools/noise_floor.py -- --out previews/noise/calib \
        [--s0 0.05] [--tile-px 128] [--tiles 6] [--spp 16,32,64,128,256,512] [--device OPTIX]

Renders small tiles of the *full-resolution* reference panorama, using Cycles' border render
so each tile costs a tile but has exactly the reference pixel scale. Every tile is rendered
twice with different seeds. For two independent renders A and B of the same view,
RMS(A-B)/sqrt(2) is an unbiased estimate of one render's noise, with no converged reference
needed and no bias smuggled in from one.

Answers three questions at once:
  noise        relative noise per spp, and the smallest spp meeting --target
  overhead     a least-squares fit of seconds = a + b*spp per tile; a is the fixed cost of a
               render call, which matters because a foveated fixation is a small render
  reference    projected cost of the full panorama at the chosen spp, from measured per-pixel
               time, so you can decide whether tiling it is worth building

Writes noise.json and noise.csv to --out. Nothing here is a claim about reconstruction
quality; it is only the floor below which such claims cannot be read.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import os
import sys
import time
import traceback

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bl_common import (configure_multilayer_exr, ensure_cycles, find_eye, rigid,  # noqa: E402
                       script_args, setup_device)


def read_rgb(path: str) -> np.ndarray:
    """Read a single-layer EXR back through Blender's own loader.

    This script runs in Blender's bundled Python, which ships numpy but not OpenEXR, so it
    must not depend on the venv (see CLAUDE.md). Verified against the OpenEXR reader on a
    real tile: identical to the last bit. img.pixels is bottom-up, hence the [::-1]; and the
    file must be single-layer, because Blender loads a multilayer EXR as type MULTILAYER
    with size (0, 0) and no accessible pixels.
    """
    img = bpy.data.images.load(path)
    try:
        if img.type == "MULTILAYER" or img.size[0] == 0:
            raise RuntimeError(f"{path} is multilayer; this reader needs single-layer EXR")
        w, h, n = img.size[0], img.size[1], img.channels
        return np.array(img.pixels[:], dtype=np.float32).reshape(h, w, n)[::-1, :, :3]
    finally:
        bpy.data.images.remove(img)


def tile_centres(n: int) -> list[tuple[float, float]]:
    """Deterministic spread over the panorama, avoiding the poles where pixels crowd."""
    cols = max(1, int(round(math.sqrt(n * 2))))
    rows = max(1, int(math.ceil(n / cols)))
    out = []
    for r, c in itertools.product(range(rows), range(cols)):
        out.append(((c + 0.5) / cols, 0.30 + 0.40 * (r + 0.5) / rows))
    return out[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blend")
    ap.add_argument("--out", required=True)
    ap.add_argument("--s0", type=float, default=0.05, help="reference spacing, deg/px")
    ap.add_argument("--tile-px", type=int, default=128)
    ap.add_argument("--tiles", type=int, default=6)
    ap.add_argument("--spp", default="16,32,64,128,256,512")
    ap.add_argument("--target", type=float, default=0.01, help="relative noise to reach")
    ap.add_argument("--device", default="OPTIX", choices=["OPTIX", "CUDA", "CPU"])
    args = ap.parse_args(script_args())

    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args.blend))
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    spp_list = [int(x) for x in args.spp.split(",")]

    scene = bpy.context.scene
    ensure_cycles(scene)
    backend = setup_device(scene, args.device)
    bpy.context.view_layer.update()
    eye, eye_note = find_eye(scene)

    width = int(round(360.0 / args.s0))
    height = width // 2
    cam_data = bpy.data.cameras.new("REFERENCE")
    cam_data.type, cam_data.panorama_type = "PANO", "EQUIRECTANGULAR"
    cam_data.latitude_min, cam_data.latitude_max = -math.pi / 2, math.pi / 2
    cam_data.longitude_min, cam_data.longitude_max = -math.pi, math.pi
    cam_data.clip_start, cam_data.clip_end = 0.001, 1.0e5
    cam_data.dof.use_dof = False
    cam = bpy.data.objects.new("REFERENCE", cam_data)
    scene.collection.objects.link(cam)
    cam.matrix_world = rigid(eye.matrix_world)
    scene.camera = cam
    bpy.context.view_layer.update()

    r = scene.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = width, height, 100
    r.use_border = r.use_crop_to_border = True
    r.use_compositing = r.use_sequencer = False
    r.use_single_layer = True
    r.film_transparent = r.use_motion_blur = False
    c = scene.cycles
    c.use_adaptive_sampling = False       # adaptive sampling makes noise spp-dependent in a
    c.pixel_filter_type, c.filter_width = "BOX", 1.0   # way that would confound this measurement
    try:
        c.use_denoising = False
    except (AttributeError, TypeError):
        pass
    vl = bpy.context.view_layer
    vl.use_pass_combined = True
    vl.use_pass_z = vl.use_pass_normal = vl.use_pass_position = False
    im = r.image_settings          # single-layer: only Combined is needed, and read_rgb
    im.media_type = "IMAGE"        # cannot read multilayer back through bpy
    im.file_format = "OPEN_EXR"
    im.color_mode, im.color_depth, im.exr_codec = "RGBA", "32", "ZIP"
    r.use_persistent_data = True

    print(f"[noise] {eye_note}; device {backend}; reference {width}x{height} at s0={args.s0} deg; "
          f"{args.tiles} tiles of {args.tile_px}px; spp {spp_list}")

    rows = []
    scratch = os.path.join(out, "_tile.exr")
    try:
        for ti, (cx, cy) in enumerate(tile_centres(args.tiles)):
            fx, fy = args.tile_px / width, args.tile_px / height
            r.border_min_x = min(max(cx - fx / 2, 0.0), 1.0 - fx)
            r.border_min_y = min(max(cy - fy / 2, 0.0), 1.0 - fy)
            r.border_max_x = r.border_min_x + fx
            r.border_max_y = r.border_min_y + fy
            for spp in spp_list:
                imgs, secs = [], []
                for seed in (0, 1):
                    c.samples, c.seed = spp, seed
                    t0 = time.time()
                    bpy.ops.render.render(write_still=False)
                    secs.append(time.time() - t0)   # file I/O deliberately outside the timer
                    bpy.data.images["Render Result"].save_render(scratch, scene=scene)
                    imgs.append(read_rgb(scratch))
                a, b = imgs
                tile_pixels = a.shape[0] * a.shape[1]   # border rounding: not always tile_px**2
                mean = 0.5 * (a + b)
                level = float(mean.mean())
                diff = a - b
                sigma = float(np.sqrt((diff ** 2).mean() / 2.0))          # one render's RMS noise
                per_px = np.abs(diff).mean(-1) / math.sqrt(2.0)
                rows.append({
                    "tile": ti, "centre": [round(cx, 4), round(cy, 4)], "spp": spp,
                    "pixels": tile_pixels,
                    "level": level, "sigma": sigma,
                    "rel_rms": sigma / max(level, 1e-9),
                    "rel_p99": float(np.percentile(per_px, 99)) / max(level, 1e-9),
                    "seconds": round(float(np.mean(secs)), 3),
                })
                print(f"[noise] tile {ti} spp {spp:5d}  rel_rms {rows[-1]['rel_rms']:.5f}  "
                      f"{rows[-1]['seconds']:.2f}s", flush=True)
    finally:
        if os.path.exists(scratch):
            os.remove(scratch)
    by_spp = {}
    for spp in spp_list:
        sel = [x for x in rows if x["spp"] == spp]
        by_spp[spp] = {
            "rel_rms_median": float(np.median([x["rel_rms"] for x in sel])),
            "rel_rms_worst": float(max(x["rel_rms"] for x in sel)),
            "rel_p99_worst": float(max(x["rel_p99"] for x in sel)),
            "seconds_median": float(np.median([x["seconds"] for x in sel])),
        }

    # seconds = a + b*spp, fitted per tile then averaged: a is the fixed cost of a render call.
    fits = []
    for ti in range(args.tiles):
        sel = sorted([x for x in rows if x["tile"] == ti], key=lambda x: x["spp"])
        if len(sel) >= 2:
            m, k = np.polyfit([x["spp"] for x in sel], [x["seconds"] for x in sel], 1)
            fits.append((float(k), float(m)))
    overhead = float(np.median([f[0] for f in fits])) if fits else None
    per_spp_s = float(np.median([f[1] for f in fits])) if fits else None

    meeting = [s for s in spp_list if by_spp[s]["rel_rms_worst"] <= args.target]
    chosen = min(meeting) if meeting else None
    projection = None
    if chosen is not None and per_spp_s is not None:
        tile_pixels = float(np.median([x["pixels"] for x in rows]))
        seconds_full = per_spp_s * chosen * (width * height) / tile_pixels
        projection = {
            "spp": chosen,
            "reference_pixels": width * height,
            "measured_tile_pixels": int(tile_pixels),
            "projected_seconds": round(seconds_full, 1),
            "projected_minutes": round(seconds_full / 60.0, 2),
            "exr_gigabytes_4_passes": round(width * height * 44 / 1e9, 2),
        }

    result = {
        "blend": bpy.data.filepath, "device": backend, "eye_note": eye_note,
        "s0_deg": args.s0, "reference": [width, height],
        "tile_px": args.tile_px, "tiles": args.tiles, "spp_list": spp_list,
        "target_rel_rms": args.target,
        "estimator": "sigma = RMS(A-B)/sqrt(2) from two seeds; no converged reference used",
        "by_spp": by_spp,
        "render_call_overhead_seconds": None if overhead is None else round(overhead, 3),
        "seconds_per_spp_per_tile": None if per_spp_s is None else float(f"{per_spp_s:.6g}"),
        "chosen_spp": chosen,
        "reference_projection": projection,
        "rows": rows,
    }
    with open(os.path.join(out, "noise.json"), "w") as fh:
        json.dump(result, fh, indent=1)
    with open(os.path.join(out, "noise.csv"), "w") as fh:
        fh.write("tile,spp,level,sigma,rel_rms,rel_p99,seconds\n")
        for x in rows:
            fh.write(f"{x['tile']},{x['spp']},{x['level']:.6g},{x['sigma']:.6g},"
                     f"{x['rel_rms']:.6g},{x['rel_p99']:.6g},{x['seconds']}\n")

    print(f"[noise] fixed cost per render call: {overhead}s")
    if chosen is None:
        print(f"[noise] no spp in {spp_list} reached rel_rms <= {args.target}; extend --spp")
    else:
        print(f"[noise] spp {chosen} meets {args.target}; full reference projected at "
              f"{projection['projected_minutes']} min, {projection['exr_gigabytes_4_passes']} GB")


def run():
    """Blender does not propagate an uncaught exception to the exit code: `blender -b -P`
    prints the traceback and still exits 0. A tool that fails invisibly is the thing the
    second hard rule in CLAUDE.md exists to prevent, so failure is made loud here."""
    try:
        main()
    except BaseException:
        traceback.print_exc()
        print("[noise] FAILED: no noise.json was written", flush=True)
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)


run()
