"""Measure the Monte Carlo noise floor at the reference sampling scale.

    blender -b scene.blend -P tools/noise_floor.py -- --out previews/noise/calib \
        [--s0 0.05] [--tile-px 128] [--tiles 6] [--spp 16,...,8192] [--device OPTIX]
    blender -b scene.blend -P tools/noise_floor.py -- --out /tmp/nf --control same-seed
    blender -b scene.blend -P tools/noise_floor.py -- --out /tmp/nf --control late-read

Renders small tiles of the *full-resolution* reference panorama, using Cycles' border render
so each tile costs a tile but has exactly the reference pixel scale. Every tile is rendered
twice with different seeds. For two independent renders A and B of the same view,
RMS(A-B)/sqrt(2) is an unbiased estimate of one render's noise, with no converged reference
needed and no bias smuggled in from one.

Answers three questions at once:
  noise        relative noise per spp, and the smallest spp meeting --target (measured), or
               the spp that would by 1/sqrt(spp) extrapolation (assumed, and labelled so)
  timing       the time floor of a render call at low spp, and the marginal cost per
               pixel-sample from the linear regime, both reported with their spread over tiles
  reference    projected cost of the full panorama at that spp

Writes noise.json and noise.csv to --out. Nothing here is a claim about reconstruction
quality; it is only the floor below which such claims cannot be read.

The invariant this tool lives on
--------------------------------
`Render Result` is one live buffer. The estimator is only correct because each render is
saved and read back BEFORE the next render is issued. Issue both seed renders and then read,
and both files hold the second render: sigma collapses by six orders of magnitude and the
tool would announce a confident spp with nothing raising an exception (audit of 2026-09-12,
docs/reviews/). So the pair is checked: if the two seed renders do not differ, the run
FAILS. `--control late-read` reproduces the failure on purpose and passes only if the guard
fires; `--control same-seed` measures how close "identical" is on this device.

Two interpreters: this script runs under Blender's bundled Python (bpy, numpy, nothing
else). The analysis functions at the top import nothing from Blender, so
`tools/check_noise_floor_stats.py` can exercise them host-side.
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

import numpy as np

# Below a relative RMS of this, two "different seed" renders are treated as the same render.
# Same-seed renders differ by <= 1.5e-7 absolute on OptiX and exactly 0 on CPU (measured,
# 2026-09-12); genuinely different seeds differ by >= 1e-2 relative at any spp this tool
# will be asked for. Five orders of magnitude of headroom on each side.
IDENTICAL_REL_RMS = 1e-5
BLACK_LEVEL = 1e-6          # a tile darker than this cannot support a relative measurement
SQRT2 = math.sqrt(2.0)


# ----------------------------------------------------------------------------------------
# Analysis. Pure numpy; no Blender. Checked host-side by tools/check_noise_floor_stats.py.
# ----------------------------------------------------------------------------------------

def noise_from_pair(a: np.ndarray, b: np.ndarray) -> dict:
    """Noise statistics of one render, from two independent renders A and B of the same view.

    sigma    RMS noise of one render, over all pixels and channels
    per_px   RMS noise of one render at each pixel (over its channels) - the same statistic at
             pixel granularity, so its percentiles are on the same scale as sigma
    """
    assert a.shape == b.shape and a.ndim == 3, (a.shape, b.shape)
    diff = (a - b).astype(np.float64)
    per_px = np.sqrt((diff ** 2).mean(-1) / 2.0)
    sigma = float(np.sqrt((per_px ** 2).mean()))
    level = float((0.5 * (a + b)).mean())
    return {
        "level": level,
        "sigma": sigma,
        "rel_rms": sigma / max(level, 1e-12),
        "rel_p99": float(np.percentile(per_px, 99)) / max(level, 1e-12),
        "max_abs_diff": float(np.abs(diff).max()),
        "pixels": int(a.shape[0] * a.shape[1]),
    }


def check_pair_differs(stats: dict, seeds: tuple[int, int]) -> None:
    """The guard. Raises if the two renders are the same render."""
    if stats["level"] < BLACK_LEVEL:
        raise RuntimeError(f"tile is black (level {stats['level']:.3g}); relative noise is "
                           f"undefined here - move the tiles (see tile_centres)")
    if stats["rel_rms"] < IDENTICAL_REL_RMS:
        raise RuntimeError(
            f"renders with seeds {seeds} are identical (rel_rms {stats['rel_rms']:.3g}, "
            f"max|A-B| {stats['max_abs_diff']:.3g}). Either the seeds did not take (a keyframe "
            f"or driver on cycles.seed; see pin_seed), or the Render Result buffer was read "
            f"after the next render - the estimator is invalid")


def fit_timing(rows: list[dict], fit_min_spp: int) -> dict:
    """Timing model per tile from (spp, seconds) points, without a straight-line intercept.

    Measured 2026-09-12: seconds ~= max(floor, b*spp). A single a + b*spp fit lets `a`
    absorb the curvature, so its intercept varied 105% across tiles. Instead:
      floor   the time at the smallest spp (the plateau), per tile
      slope   least squares through the points with spp >= fit_min_spp, per tile; if fewer
              than two such points exist the two largest spp are used and this is flagged
    Everything is reported as median plus range across tiles; nothing is a single number.
    """
    tiles = sorted({x["tile"] for x in rows})
    per_tile = []
    for ti in tiles:
        sel = sorted([x for x in rows if x["tile"] == ti], key=lambda x: x["spp"])
        if len(sel) < 2:
            continue
        lin = [x for x in sel if x["spp"] >= fit_min_spp]
        fallback = len(lin) < 2
        if fallback:
            lin = sel[-2:]
        xs = np.array([x["spp"] for x in lin], dtype=np.float64)
        ys = np.array([x["seconds"] for x in lin], dtype=np.float64)
        b, a = np.polyfit(xs, ys, 1)
        resid = ys - (a + b * xs)
        pixels = float(np.median([x["pixels"] for x in lin]))
        per_tile.append({
            "tile": ti,
            "floor_seconds": float(sel[0]["seconds"]),
            "floor_spp": int(sel[0]["spp"]),
            "slope_seconds_per_spp": float(b),
            "ns_per_pixel_sample": float(b / pixels * 1e9),
            "fit_points": [int(x["spp"]) for x in lin],
            "fit_fallback_two_largest": fallback,
            "fit_max_rel_resid": float(np.max(np.abs(resid) / np.maximum(ys, 1e-12))),
        })

    def summary(key: str) -> dict:
        v = np.array([t[key] for t in per_tile], dtype=np.float64)
        med = float(np.median(v))
        return {"median": med, "min": float(v.min()), "max": float(v.max()),
                "spread_frac_of_median": float((v.max() - v.min()) / med) if med else None}

    if not per_tile:
        return {"per_tile": [], "floor_seconds": None, "ns_per_pixel_sample": None}
    return {
        "per_tile": per_tile,
        "fit_min_spp": fit_min_spp,
        "floor_seconds": summary("floor_seconds"),
        "slope_seconds_per_spp": summary("slope_seconds_per_spp"),
        "ns_per_pixel_sample": summary("ns_per_pixel_sample"),
        "fit_max_rel_resid_worst": float(max(t["fit_max_rel_resid"] for t in per_tile)),
    }


def sqrt2_check(by_spp: dict) -> dict:
    """Between consecutive spp values, rel_rms should scale as 1/sqrt(spp): the observed
    ratio divided by sqrt(hi/lo) should be 1. Reported, not enforced: a real departure
    (adaptive sampling left on, a light path that saturates) is worth seeing."""
    spps = sorted(by_spp)
    norm = []
    for lo, hi in zip(spps, spps[1:]):
        r = by_spp[lo]["rel_rms_median"] / max(by_spp[hi]["rel_rms_median"], 1e-12)
        norm.append(r / math.sqrt(hi / lo))
    if not norm:
        return {"normalised_ratios": [], "median": None, "ok": None}
    med = float(np.median(norm))
    return {"normalised_ratios": [round(r, 3) for r in norm], "expected": 1.0,
            "median": round(med, 3), "ok": bool(0.92 <= med <= 1.10)}


def choose_spp(by_spp: dict, spp_list: list[int], target: float) -> dict:
    """Smallest measured spp whose worst tile meets the target; else extrapolate (assumed)."""
    meeting = [s for s in spp_list if by_spp[s]["rel_rms_worst"] <= target]
    if meeting:
        return {"spp": int(min(meeting)), "how": "measured",
                "rel_rms_worst_at_spp": by_spp[min(meeting)]["rel_rms_worst"]}
    top = max(spp_list)
    need = by_spp[top]["rel_rms_worst"] ** 2 / target ** 2 * top
    pow2 = int(2 ** math.ceil(math.log2(need)))
    return {"spp": pow2, "how": "assumed: 1/sqrt(spp) extrapolation from the largest measured spp",
            "extrapolated_from_spp": int(top), "unrounded_spp": float(need),
            "rel_rms_worst_at_top": by_spp[top]["rel_rms_worst"]}


def project_reference(choice: dict, timing: dict, width: int, height: int) -> dict | None:
    """Full-panorama cost from the measured per-pixel-sample slope plus the call floor.
    Assumed: cost is linear in pixel count (measured only at tile size)."""
    if timing.get("ns_per_pixel_sample") is None:
        return None
    ns = timing["ns_per_pixel_sample"]["median"]
    floor = timing["floor_seconds"]["median"]
    spp = choice["spp"]
    secs = ns * 1e-9 * width * height * spp + floor
    return {
        "spp": spp, "spp_how": choice["how"],
        "reference_pixels": width * height,
        "ns_per_pixel_sample_median": ns,
        "projected_seconds": round(secs, 1),
        "projected_minutes": round(secs / 60.0, 2),
        "exr_gigabytes_4_passes": round(width * height * 44 / 1e9, 2),
        "assumed": "linear in pixel count from tile-sized measurements; the call floor is negligible here",
    }


def tile_centres(n: int) -> list[tuple[float, float]]:
    """Deterministic spread over the panorama, avoiding the poles where pixels crowd."""
    cols = max(1, int(round(math.sqrt(n * 2))))
    rows = max(1, int(math.ceil(n / cols)))
    out = []
    for r, c in itertools.product(range(rows), range(cols)):
        out.append(((c + 0.5) / cols, 0.30 + 0.40 * (r + 0.5) / rows))
    return out[:n]


# ----------------------------------------------------------------------------------------
# Blender side.
# ----------------------------------------------------------------------------------------

def read_rgb(path: str) -> np.ndarray:
    """Read a single-layer float32 EXR back through Blender's own loader.

    This script runs in Blender's bundled Python, which ships numpy but not OpenEXR, so it
    must not depend on the venv (see CLAUDE.md). Verified against the OpenEXR reader on a
    real tile: identical to the last bit. img.pixels is bottom-up, hence the [::-1]; and the
    file must be single-layer, because Blender loads a multilayer EXR as type MULTILAYER
    with size (0, 0) and no accessible pixels.

    `save_render` honours `scene.render.image_settings` (measured: color_depth "16" wrote
    float16, and file_format "PNG" wrote a PNG to a path named .exr), so the file is checked
    to be what the estimator needs: float, 32-bit RGBA, alpha exactly 1 everywhere.
    """
    import bpy
    img = bpy.data.images.load(path)
    try:
        if img.type == "MULTILAYER" or img.size[0] == 0:
            raise RuntimeError(f"{path} is multilayer; this reader needs single-layer EXR")
        w, h, n = img.size[0], img.size[1], img.channels
        if not img.is_float or n != 4 or img.depth != 128:
            raise RuntimeError(f"{path}: expected float32 RGBA (depth 128), got is_float="
                               f"{img.is_float} channels={n} depth={img.depth}; check "
                               f"scene.render.image_settings")
        buf = np.empty(w * h * n, dtype=np.float32)
        img.pixels.foreach_get(buf)        # 22x faster than pixels[:], measured
        px = buf.reshape(h, w, n)[::-1]
        alpha = px[..., 3]
        if alpha.min() != 1.0 or alpha.max() != 1.0:
            raise RuntimeError(f"{path}: alpha in [{alpha.min()}, {alpha.max()}], expected "
                               f"exactly 1; PREMUL loading would then alter RGB. Is "
                               f"film_transparent off?")
        return px[..., :3]
    finally:
        bpy.data.images.remove(img)


def main():
    import bpy
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from bl_common import (add_profile, ensure_cycles, find_eye, pin_seed, rigid, script_args,
                           setup_device)

    ap = argparse.ArgumentParser()
    ap.add_argument("--blend")
    ap.add_argument("--out", required=True)
    ap.add_argument("--s0", type=float, default=0.05, help="reference spacing, deg/px")
    ap.add_argument("--tile-px", type=int, default=128)
    ap.add_argument("--tiles", type=int, default=6)
    ap.add_argument("--spp", default="16,32,64,128,256,512,1024,2048,4096,8192")
    ap.add_argument("--target", type=float, default=0.01, help="relative noise to reach")
    ap.add_argument("--fit-min-spp", type=int, default=256,
                    help="slope is fitted on spp >= this (the linear regime; below it the "
                         "call floor dominates)")
    ap.add_argument("--device", default="OPTIX", choices=["OPTIX", "CUDA", "CPU"])
    ap.add_argument("--control", choices=["same-seed", "late-read"],
                    help="same-seed: render one tile twice with seed 0 and report how close "
                         "identical is on this device. late-read: reproduce the read-after-"
                         "both-renders failure and pass only if the guard fires. Neither "
                         "writes noise.json.")
    add_profile(ap, script_args(), s0="s0")
    args = ap.parse_args(script_args())

    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args.blend))
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    spp_list = sorted(int(x) for x in args.spp.split(","))

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
    r.film_transparent = r.use_motion_blur = False   # alpha must be 1; read_rgb asserts it
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
    for what in pin_seed(scene):        # Classroom keyframes cycles.seed; the key would win
        print(f"[noise] removed {what}", flush=True)

    def set_tile(cx: float, cy: float) -> None:
        fx, fy = args.tile_px / width, args.tile_px / height
        r.border_min_x = min(max(cx - fx / 2, 0.0), 1.0 - fx)
        r.border_min_y = min(max(cy - fy / 2, 0.0), 1.0 - fy)
        r.border_max_x = r.border_min_x + fx
        r.border_max_y = r.border_min_y + fy

    scratch = os.path.join(out, "_tile.exr")

    def render(spp: int, seed: int) -> float:
        c.samples, c.seed = spp, seed
        t0 = time.perf_counter()
        bpy.ops.render.render(write_still=False)
        dt = time.perf_counter() - t0
        if c.seed != seed or c.samples != spp:   # frame evaluation can overwrite both
            raise RuntimeError(f"seed/samples did not take: asked ({seed}, {spp}), scene has "
                               f"({c.seed}, {c.samples}) after the render; is either animated?")
        return dt

    def grab() -> np.ndarray:
        """Save and read the live Render Result NOW, before anything else renders."""
        bpy.data.images["Render Result"].save_render(scratch, scene=scene)   # outside the timer
        return read_rgb(scratch)

    print(f"[noise] {eye_note}; device {backend}; reference {width}x{height} at s0={args.s0} deg; "
          f"{args.tiles} tiles of {args.tile_px}px; spp {spp_list}", flush=True)

    try:
        if args.control:
            cx, cy = tile_centres(args.tiles)[0]
            set_tile(cx, cy)
            spp = spp_list[0]
            render(spp, 0)                         # warm-up, discarded
            if args.control == "same-seed":
                render(spp, 0); a = grab()
                render(spp, 0); b = grab()
                st = noise_from_pair(a, b)
                print(f"[noise] control same-seed: max|A-B| {st['max_abs_diff']:.3e}, "
                      f"rel_rms {st['rel_rms']:.3e}, guard threshold {IDENTICAL_REL_RMS:.0e}")
                if st["rel_rms"] >= IDENTICAL_REL_RMS:
                    raise RuntimeError("same-seed renders differ above the guard threshold; "
                                       "the guard could not tell identical from different here")
                print("[noise] control same-seed PASSED: the guard would fire on these", flush=True)
            else:
                render(spp, 0)                     # deliberately NOT read
                render(spp, 1)
                a = grab()                         # both reads see the seed-1 render
                b = grab()
                st = noise_from_pair(a, b)
                try:
                    check_pair_differs(st, (0, 1))
                except RuntimeError as e:
                    print(f"[noise] control late-read PASSED: guard fired as it must: {e}",
                          flush=True)
                else:
                    raise RuntimeError(f"control late-read FAILED: read-after-both-renders "
                                       f"went undetected (rel_rms {st['rel_rms']:.3g})")
            return

        # One throwaway render: the first call on a fresh session was 4-5x slower than the
        # same spp elsewhere (measured), and charging that to tile 0 bent its fit.
        cx, cy = tile_centres(args.tiles)[0]
        set_tile(cx, cy)
        warmup = render(spp_list[0], 0)
        print(f"[noise] warm-up render {warmup:.3f}s (discarded)", flush=True)

        rows = []
        for ti, (cx, cy) in enumerate(tile_centres(args.tiles)):
            set_tile(cx, cy)
            for spp in spp_list:
                secs, imgs = [], []
                for seed in (0, 1):
                    secs.append(render(spp, seed))
                    imgs.append(grab())            # read before the next render: the invariant
                st = noise_from_pair(*imgs)
                check_pair_differs(st, (0, 1))
                st.update({"tile": ti, "centre": [round(cx, 4), round(cy, 4)], "spp": spp,
                           "seconds": float(np.mean(secs)), "seconds_each": secs})
                rows.append(st)
                print(f"[noise] tile {ti} spp {spp:5d}  rel_rms {st['rel_rms']:.5f}  "
                      f"rel_p99 {st['rel_p99']:.5f}  {st['seconds']:.4f}s", flush=True)
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
    timing = fit_timing(rows, args.fit_min_spp)
    scaling = sqrt2_check(by_spp)
    choice = choose_spp(by_spp, spp_list, args.target)
    projection = project_reference(choice, timing, width, height)

    result = {
        "blend": bpy.data.filepath, "device": backend, "eye_note": eye_note,
        "blender": bpy.app.version_string,
        "s0_deg": args.s0, "reference": [width, height],
        "tile_px": args.tile_px, "tiles": args.tiles, "spp_list": spp_list,
        "target_rel_rms": args.target,
        "estimator": "sigma = RMS(A-B)/sqrt(2) from two seeds; no converged reference used; "
                     "rel_p99 is the 99th percentile of the per-pixel RMS on the same scale",
        "identical_guard_rel_rms": IDENTICAL_REL_RMS,
        "warmup_seconds_discarded": warmup,
        "by_spp": {str(k): v for k, v in by_spp.items()},
        "sqrt2_check": scaling,
        "timing": timing,
        "spp_choice": choice,
        "reference_projection": projection,
        "rows": rows,
    }
    with open(os.path.join(out, "noise.json"), "w") as fh:
        json.dump(result, fh, indent=1)
    with open(os.path.join(out, "noise.csv"), "w") as fh:
        fh.write("tile,spp,pixels,level,sigma,rel_rms,rel_p99,seconds\n")
        for x in rows:
            fh.write(f"{x['tile']},{x['spp']},{x['pixels']},{x['level']:.8g},{x['sigma']:.8g},"
                     f"{x['rel_rms']:.8g},{x['rel_p99']:.8g},{x['seconds']:.6g}\n")

    fs, ns = timing["floor_seconds"], timing["ns_per_pixel_sample"]
    print(f"[noise] call floor {fs['median']:.4f}s (range {fs['min']:.4f}-{fs['max']:.4f}); "
          f"marginal {ns['median']:.2f} ns/pixel-sample (range {ns['min']:.2f}-{ns['max']:.2f}, "
          f"fit on spp>={args.fit_min_spp}, worst rel resid {timing['fit_max_rel_resid_worst']:.3f})")
    print(f"[noise] 1/sqrt(spp) check: median normalised ratio {scaling['median']} "
          f"(expect 1.0) -> {'ok' if scaling['ok'] else 'OFF, look at by_spp'}")
    if choice["how"] == "measured":
        print(f"[noise] spp {choice['spp']} meets rel_rms <= {args.target} on the worst tile "
              f"(measured)")
    else:
        print(f"[noise] no spp in {spp_list} reached rel_rms <= {args.target}; "
              f"~{choice['spp']} spp would (ASSUMED, 1/sqrt extrapolation from {max(spp_list)})")
    print(f"[noise] full reference at {projection['spp']} spp projected at "
          f"{projection['projected_minutes']} min, {projection['exr_gigabytes_4_passes']} GB "
          f"(assumed linear in pixels)", flush=True)


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


if __name__ == "__main__":
    run()
