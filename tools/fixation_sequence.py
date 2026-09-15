"""Render a sequence of fixations in one Blender session and emit D1 sample records.

    blender -b scene.blend -P tools/fixation_sequence.py -- --out previews/sequence/calib_room \
        --profile small --targets scenes/calib_room/calib_room.targets.json
    blender -b scene.blend -P tools/fixation_sequence.py -- --out previews/sequence/classroom \
        --profile small --gazes "0,0;30,0;-30,0;0,20"

The scene is opened once and the foveated OSL camera set up once (render_foveated.py); each
gaze is a rotation of that camera about the eye centre (D2, D3). Per fixation, under
--out/f<NNN>/:
    fix_b.exr, samples_b.npz   the same fixation at seed 1 (--seed-pair, default on): only so
                  the checker can measure this fixation's own noise; not part of the record
    fix.exr       Combined + Depth + Normal + Position, 32-bit, single part, UNCOMPRESSED so
                  exr_lite can read it back here (Blender's Python has no OpenEXR reader and
                  cannot load a multilayer EXR through bpy)
    meta.json     pose actually rendered, warp, spp, timing, sample count
    samples.npz   float32 arrays, one row per sample inside the disc (r <= 1):
                    origin        (3,)   eye position, metres, constant over the sequence (D3)
                    direction     (N,3)  unit, EYE frame, from the analytic warp composed with
                                         the gaze, NOT from the Position pass
                    value         (N,3)  Combined RGB, linear
                    footprint     (N,)   solid angle, sr: |d_x x d_y| of the raster-to-sphere
                                         map by central differences over one pixel
                    distance      (N,)   ray distance from the Depth pass, metres; 1e10 = no hit
                    fixation_id   (N,)   int32
                    raster_index  (N,2)  int32 (row, col), row 0 = top of fix.exr
    columns.json  names, shapes, frames and units of every array above
And --out/sequence.json: the gaze list, settings, per-fixation timings, the warm-up, and the
marginal-cost fit from --spp-sweep (seconds = floor + slope * samples_in_disc * spp, fitted on
spp >= --fit-min-spp with noise_floor.fit_timing).

Timing: each render is timed with perf_counter around the render call only; saving, reading
and writing samples happen outside it. The first render of the session is a warm-up: timed,
reported, excluded.

Checks that can fail live host-side in tools/check_sequence.py.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import traceback

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

CAP_45_SR = 2.0 * math.pi * (1.0 - math.cos(math.radians(45.0)))  # see warp.cap_sr


# The analytic warp and the gaze composition moved to tools/warp.py and tools/rig.py for Phase B
# (pure numpy, importable host-side). Re-exported here so nothing that imported them breaks.
from rig import gaze_of_world_direction, gaze_rotation, to_eye_frame  # noqa: E402,F401
from warp import raster_samples, warp_direction  # noqa: E402,F401


def load_gazes(targets_path: str | None, gazes: str | None, eye_rot3: np.ndarray) -> list[dict]:
    out = []
    if targets_path:
        t = json.load(open(targets_path))
        for k, tg in enumerate(t["targets"]):
            if "dir_world" in tg:
                d = tg["dir_world"]
            elif "azimuth_deg" in tg:            # wires: horizontal at eye height, like the ladders
                az = math.radians(tg["azimuth_deg"])
                d = [math.sin(az), math.cos(az), 0.0]
            else:
                raise ValueError(f"target {tg.get('name', k)} has neither dir_world nor azimuth_deg")
            yaw, pitch = gaze_of_world_direction(d, eye_rot3)
            out.append({"name": tg.get("name", f"t{k}"), "yaw": round(yaw, 4), "pitch": round(pitch, 4),
                        "kind": tg.get("kind")})
    if gazes:
        for k, item in enumerate(x for x in gazes.split(";") if x.strip()):
            yaw, pitch = (float(v) for v in item.split(","))
            out.append({"name": f"g{k}", "yaw": yaw, "pitch": pitch, "kind": "gaze"})
    if not out:
        raise ValueError("no gazes: pass --targets or --gazes")
    return out


COLUMNS = {
    "origin": {"shape": "(3,)", "frame": "world", "unit": "m", "note": "eye position, constant over the sequence (D3)"},
    "direction": {"shape": "(N,3)", "frame": "EYE (x right, y up, -z primary gaze)", "unit": "unit vector",
                  "note": "analytic warp composed with the gaze; not from the Position pass"},
    "value": {"shape": "(N,3)", "frame": "-", "unit": "linear RGB (Combined)", "note": ""},
    "footprint": {"shape": "(N,)", "frame": "-", "unit": "sr", "note": "|d_x x d_y| of the raster-to-sphere map, central differences over one pixel"},
    "distance": {"shape": "(N,)", "frame": "-", "unit": "m", "note": "Depth pass = ray distance from the eye; 1e10 means no hit"},
    "fixation_id": {"shape": "(N,)", "frame": "-", "unit": "int32", "note": "index into sequence.json gazes"},
    "raster_index": {"shape": "(N,2)", "frame": "fix.exr (row, col), row 0 = top", "unit": "int32", "note": "only r <= 1 rows are kept"},
}


def main():
    import bpy
    from bl_common import add_profile, ensure_cycles, find_eye, rigid, script_args, setup_device
    from exr_lite import read_uncompressed_exr
    from noise_floor import IDENTICAL_REL_RMS, check_pair_differs, fit_timing, noise_from_pair
    from render_foveated import (HERE, fixation_meta, raster_size, render_fixation, s0_of,
                                 save_render_result, set_gaze, setup_foveated_camera)

    ap = argparse.ArgumentParser()
    ap.add_argument("--blend")
    ap.add_argument("--out", required=True)
    ap.add_argument("--targets", help="calib_room.targets.json: one gaze per target")
    ap.add_argument("--gazes", help='"yaw,pitch;yaw,pitch;..." in degrees')
    ap.add_argument("--e2", type=float, default=2.0)
    ap.add_argument("--emax", type=float, default=45.0)
    ap.add_argument("--s0", type=float, default=0.05)
    ap.add_argument("--n", type=int, default=None)
    ap.add_argument("--spp", type=int, default=64)
    ap.add_argument("--device", default="OPTIX", choices=["OPTIX", "CUDA", "CPU"])
    ap.add_argument("--shader", default=os.path.join(HERE, "foveated_camera.osl"))
    ap.add_argument("--spp-sweep", default="16,64,256",
                    help="timing-only renders of the whole gaze list at these spp; '' to skip")
    ap.add_argument("--fit-min-spp", type=int, default=64)
    ap.add_argument("--seed-pair", dest="seed_pair", action="store_true", default=True,
                    help="also render every fixation at seed 1 (fix_b.exr, samples_b.npz) so the "
                         "checker can measure noise locally; the record is seed 0 (default on)")
    ap.add_argument("--no-seed-pair", dest="seed_pair", action="store_false")
    add_profile(ap, script_args(), s0="s0", spp="fix_spp")
    args = ap.parse_args(script_args())

    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args.blend))
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    t_seq0 = time.perf_counter()

    scene = bpy.context.scene
    ensure_cycles(scene)
    backend = setup_device(scene, args.device)
    bpy.context.view_layer.update()
    eye, eye_note = find_eye(scene)
    eye_m = rigid(eye.matrix_world)
    eye_rot3 = np.array([[eye_m[r][c] for c in range(3)] for r in range(3)])
    origin = np.array([eye_m.translation[k] for k in range(3)], dtype=np.float32)
    gazes = load_gazes(args.targets, args.gazes, eye_rot3)

    n = args.n if args.n else raster_size(args.s0, args.e2, args.emax)
    s0 = s0_of(n, args.e2, args.emax)
    rs = raster_samples(n, args.e2, args.emax)
    inside = rs["inside"]
    n_inside = int(inside.sum())
    print(f"[sequence] {eye_note}; device {backend}; raster {n}x{n}; s0 {s0:.4f} deg; "
          f"E2 {args.e2}; e_max {args.emax}; {len(gazes)} gazes at {args.spp} spp; "
          f"{n_inside} samples per fixation", flush=True)

    cam = setup_foveated_camera(scene, eye, args.shader, args.e2, args.emax, n, args.spp, exr_codec="NONE")

    set_gaze(cam, eye, gazes[0]["yaw"], gazes[0]["pitch"])
    warmup = render_fixation(scene, args.spp)
    print(f"[sequence] warm-up render {warmup:.3f}s (discarded)", flush=True)

    def grab_samples(fid: int, g: dict, exr_path: str) -> tuple[dict, np.ndarray]:
        """Save the live Render Result, read it back, and build the D1 record."""
        save_render_result(scene, exr_path)             # before the next render: shared buffer
        ch = read_uncompressed_exr(exr_path)
        rgb = np.stack([ch[[k for k in ch if k.endswith(f"Combined.{c}")][0]] for c in "RGB"], -1)
        depth = ch[[k for k in ch if k.endswith("Depth.Z")][0]]
        if rgb.shape[:2] != (n, n):
            raise RuntimeError(f"fixation {fid}: file is {rgb.shape[:2]}, raster is {n}x{n}")
        d_eye = to_eye_frame(rs["direction_cam"][inside], g["yaw"], g["pitch"])
        return {
            "origin": origin,
            "direction": d_eye.astype(np.float32),
            "value": rgb[inside].astype(np.float32),
            "footprint": rs["footprint"][inside].astype(np.float32),
            "distance": depth[inside].astype(np.float32),
            "fixation_id": np.full(n_inside, fid, dtype=np.int32),
            "raster_index": rs["raster_index"][inside].astype(np.int32),
        }, depth

    fixations = []
    for fid, g in enumerate(gazes):
        fdir = os.path.join(out, f"f{fid:03d}")
        os.makedirs(fdir, exist_ok=True)
        set_gaze(cam, eye, g["yaw"], g["pitch"])
        secs = render_fixation(scene, args.spp)
        t_io = time.perf_counter()
        samples, depth = grab_samples(fid, g, os.path.join(fdir, "fix.exr"))
        np.savez(os.path.join(fdir, "samples.npz"), **samples)
        meta = fixation_meta(scene, eye, eye_note, cam, backend, n, s0, args.e2, args.emax, args.spp,
                             g["yaw"], g["pitch"], secs, args.profile, seconds_include_write=False)
        meta.update({"fixation_id": fid, "name": g["name"], "target_kind": g["kind"],
                     "samples_inside_disc": n_inside, "exr_codec": "NONE",
                     "footprint_sum_sr": float(samples["footprint"].sum()), "cap_45_sr": CAP_45_SR})
        with open(os.path.join(fdir, "meta.json"), "w") as fh:
            json.dump(meta, fh, indent=1)
        with open(os.path.join(fdir, "columns.json"), "w") as fh:
            json.dump(COLUMNS, fh, indent=1)
        io_secs = time.perf_counter() - t_io
        fixations.append({"id": fid, "name": g["name"], "yaw": g["yaw"], "pitch": g["pitch"],
                          "render_seconds": round(secs, 4), "io_seconds": round(io_secs, 4),
                          "samples": n_inside, "hits": int((depth[inside] < 1e9).sum())})
        print(f"[sequence] f{fid:03d} {g['name']:<16} yaw {g['yaw']:7.2f} pitch {g['pitch']:6.2f}  "
              f"render {secs:.3f}s  io {io_secs:.3f}s", flush=True)

    # Second pass at seed 1, after the timed pass so the seed change (which forces a scene
    # re-sync) is paid once, not inside every timed render. Same gazes, same settings; only
    # the noise differs. The record is seed 0; this exists so check_sequence.py can measure
    # the noise of each fixation where it compares it.
    if args.seed_pair:
        t_b0 = time.perf_counter()
        for fid, g in enumerate(gazes):
            fdir = os.path.join(out, f"f{fid:03d}")
            set_gaze(cam, eye, g["yaw"], g["pitch"])
            secs_b = render_fixation(scene, args.spp, seed=1)
            samples_b, _ = grab_samples(fid, g, os.path.join(fdir, "fix_b.exr"))
            np.savez(os.path.join(fdir, "samples_b.npz"), **samples_b)
            fixations[fid]["render_seconds_seed1"] = round(secs_b, 4)
        render_fixation(scene, args.spp, seed=0)           # back to the record's seed
        print(f"[sequence] seed-1 pass: {len(gazes)} renders in {time.perf_counter() - t_b0:.1f}s "
              f"(fix_b.exr, samples_b.npz; not part of the record)", flush=True)

    sweep = [int(x) for x in args.spp_sweep.split(",") if x.strip()]
    rows, fit, pairs = [], None, []
    if sweep:
        scratch = os.path.join(out, "_sweep.exr")

        def grab_rgb() -> np.ndarray:
            save_render_result(scene, scratch)
            ch = read_uncompressed_exr(scratch)
            return np.stack([ch[[k for k in ch if k.endswith(f"Combined.{c}")][0]] for c in "RGB"], -1)

        try:
            for spp in sorted(sweep):
                # Did the sample count take? Two seeds at the first gaze, read before the next
                # render (shared buffer), and the pair's noise must scale as 1/sqrt(spp) across
                # levels. This is the check that caught the stale-samples behaviour.
                set_gaze(cam, eye, gazes[0]["yaw"], gazes[0]["pitch"])
                render_fixation(scene, spp, seed=0); a = grab_rgb()
                render_fixation(scene, spp, seed=1); b = grab_rgb()
                st = noise_from_pair(a[inside][:, None, :], b[inside][:, None, :])
                check_pair_differs(st, (0, 1))
                pairs.append({"spp": spp, "rel_rms": st["rel_rms"]})
                render_fixation(scene, spp, seed=0)        # settle: back to seed 0, untimed
                for fid, g in enumerate(gazes):
                    set_gaze(cam, eye, g["yaw"], g["pitch"])
                    secs = render_fixation(scene, spp)     # timing only; nothing saved
                    rows.append({"tile": fid, "spp": spp, "seconds": secs, "pixels": n_inside})
                med = float(np.median([x["seconds"] for x in rows if x["spp"] == spp]))
                print(f"[sequence] sweep spp {spp:4d}: median {med:.4f}s over {len(gazes)} gazes; "
                      f"seed-pair rel_rms {st['rel_rms']:.4f}", flush=True)
        finally:
            if os.path.exists(scratch):
                os.remove(scratch)
        for lo, hi in zip(pairs, pairs[1:]):
            expect = math.sqrt(hi["spp"] / lo["spp"])
            ratio = lo["rel_rms"] / max(hi["rel_rms"], 1e-12)
            hi["norm_ratio_vs_prev"] = ratio / expect
            if not (0.8 <= ratio / expect <= 1.25):
                raise RuntimeError(f"sample count did not take between {lo['spp']} and {hi['spp']} spp: "
                                   f"rel_rms ratio {ratio:.3f} vs sqrt ratio {expect:.3f}")
        fit = fit_timing(rows, args.fit_min_spp)
        render_fixation(scene, args.spp)                   # leave the session at the profile spp

    rsec = np.array([f["render_seconds"] for f in fixations])
    total = time.perf_counter() - t_seq0
    result = {
        "blend": bpy.data.filepath, "device": backend, "blender": bpy.app.version_string,
        "profile": args.profile, "eye_note": eye_note,
        "origin_m": [float(x) for x in origin],
        "warp": {"E2_deg": args.e2, "e_max_deg": args.emax, "s0_deg": s0, "raster": n},
        "spp": args.spp, "samples_per_fixation": n_inside, "seed_pair": args.seed_pair,
        "gazes": gazes,
        "warmup_seconds_discarded": warmup,
        "fixations": fixations,
        "render_seconds_median": float(np.median(rsec)),
        "render_seconds_min": float(rsec.min()), "render_seconds_max": float(rsec.max()),
        "render_seconds_sum": float(rsec.sum()),
        "sequence_wall_seconds": total,
        "timing_sweep": {"spp": sorted(sweep), "fit_min_spp": args.fit_min_spp, "rows": rows, "fit": fit,
                         "seed_pairs": pairs, "identical_guard_rel_rms": IDENTICAL_REL_RMS},
    }
    if fit and fit.get("floor_seconds"):
        fl, ns = fit["floor_seconds"], fit["ns_per_pixel_sample"]
        result["timing_sweep"]["floor_share_of_render_at_spp"] = fl["median"] / result["render_seconds_median"]
        print(f"[sequence] call floor {fl['median']:.4f}s (range {fl['min']:.4f}-{fl['max']:.4f}); "
              f"marginal {ns['median']:.2f} ns/sample (range {ns['min']:.2f}-{ns['max']:.2f}, fit on "
              f"spp>={args.fit_min_spp}, worst rel resid {fit['fit_max_rel_resid_worst']:.3f}); floor is "
              f"{100 * result['timing_sweep']['floor_share_of_render_at_spp']:.0f}% of a {args.spp} spp render")
    with open(os.path.join(out, "sequence.json"), "w") as fh:
        json.dump(result, fh, indent=1)
    print(f"[sequence] {len(gazes)} fixations: render {result['render_seconds_median']:.3f}s median "
          f"(range {rsec.min():.3f}-{rsec.max():.3f}), sum {rsec.sum():.1f}s, wall {total:.1f}s -> {out}", flush=True)


def run():
    try:
        main()
    except BaseException:
        traceback.print_exc()
        print("[sequence] FAILED", flush=True)
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)


if __name__ == "__main__":
    run()
