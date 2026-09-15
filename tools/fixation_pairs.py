"""Render verged fixation pairs — two eyes on the EYE rig — in one Blender session (B1, D12).

    blender -b scenes/calib_room/calib_room.blend -P tools/fixation_pairs.py -- \\
        --out previews/pairs/calib_room --profile small --targets scenes/calib_room/calib_room.targets.json
    blender -b scenes/calib_room/calib_room.blend -P tools/fixation_pairs.py -- \\
        --out previews/pairs/calib_room_control --profile small --targets ... --vergence off
    blender -b scene.blend -P tools/fixation_pairs.py -- --out previews/pairs/x --profile small \\
        --points "0,2,1.6;-1,3,1.2"

The rig (tools/rig.py): EYE is the head frame and the cyclopean point; the eyes sit at
+-ipd/2 on its local X. A pair fixates one world point P: with --vergence on (default) each
eye's gaze is P - C_i; with --vergence off both eyes take the cyclopean gaze (the control:
parallel lines of sight that miss P by a predicted amount). Each eye is a rotation of the
foveated OSL camera about its own centre (D2, D3); nothing in the scene changes.

Output, --out/:
    pairs.json         rig (origin, head rotation, ipd, centres), settings, per pair: target,
                       P, both gazes, vergence, predicted distances and misses, render seconds,
                       and an in-session measurement of the central pixels' Position and Depth
                       (exr_lite; the host-side check_pairs.py re-measures with OpenEXR and judges)
    L/, R/             one Phase A sequence per eye: f<NNN>/{fix.exr, samples.npz, meta.json,
                       columns.json} and sequence.json, so per-eye tools run on them unchanged.
                       samples.npz is the D1 record plus (D12): origin is this eye's centre,
                       eye_id (N,) int32 0=L 1=R, pair_id (N,) int32; fixation_id == pair_id.
                       Directions stay in the head (EYE) frame for both eyes.
Checks that can fail live host-side in tools/check_pairs.py.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
import time
import traceback

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rig import (DEFAULT_IPD_M, EYE_NAMES, eye_centres, eye_offsets_local, pair_for_point,  # noqa: E402
                 target_point, to_eye_frame)
from warp import cap_sr, centre_pixels, raster_samples, raster_size, s0_of  # noqa: E402

SCHEMA = "D1v2"

COLUMNS = {
    "origin": {"shape": "(3,)", "frame": "world", "unit": "m", "note": "this eye's centre, constant over the sequence (D3, D12)"},
    "direction": {"shape": "(N,3)", "frame": "EYE = head (x right, y up, -z primary gaze); shared by both eyes", "unit": "unit vector",
                  "note": "analytic warp composed with this eye's gaze; not from the Position pass"},
    "value": {"shape": "(N,3)", "frame": "-", "unit": "linear RGB (Combined)", "note": ""},
    "footprint": {"shape": "(N,)", "frame": "-", "unit": "sr", "note": "|d_x x d_y| of the raster-to-sphere map, central differences over one pixel"},
    "distance": {"shape": "(N,)", "frame": "-", "unit": "m", "note": "Depth pass = ray distance from this eye's centre; 1e10 means no hit"},
    "fixation_id": {"shape": "(N,)", "frame": "-", "unit": "int32", "note": "index into this eye's sequence.json gazes; equals pair_id"},
    "raster_index": {"shape": "(N,2)", "frame": "fix.exr (row, col), row 0 = top", "unit": "int32", "note": "only r <= 1 rows are kept"},
    "eye_id": {"shape": "(N,)", "frame": "-", "unit": "int32", "note": "0 = L, 1 = R (D12)"},
    "pair_id": {"shape": "(N,)", "frame": "-", "unit": "int32", "note": "index into pairs.json pairs (D12)"},
    "_schema": SCHEMA,
}


def load_points(targets_path: str | None, points: str | None, head_origin: np.ndarray) -> list[dict]:
    out = []
    if targets_path:
        t = json.load(open(targets_path))
        for k, tg in enumerate(t["targets"]):
            p = target_point(tg, head_origin)
            if p is None:
                raise ValueError(f"target {tg.get('name', k)} has no usable geometry")
            out.append({"name": tg.get("name", f"t{k}"), "kind": tg.get("kind"), "point_m": p.tolist(),
                        "target": {k_: v for k_, v in tg.items() if k_ != "dir_world"}})
    if points:
        for k, item in enumerate(x for x in points.split(";") if x.strip()):
            p = [float(v) for v in item.split(",")]
            if len(p) != 3:
                raise ValueError(f"--points item {item!r} is not x,y,z")
            out.append({"name": f"p{k}", "kind": "point", "point_m": p, "target": None})
    if not out:
        raise ValueError("no fixation points: pass --targets or --points")
    return out


def main():
    import bpy
    from bl_common import add_profile, ensure_cycles, eye_record, find_eye, rigid, script_args, setup_device
    from exr_lite import read_uncompressed_exr
    from render_foveated import HERE, fixation_meta, render_fixation, save_render_result, set_gaze, setup_foveated_camera

    ap = argparse.ArgumentParser()
    ap.add_argument("--blend")
    ap.add_argument("--out", required=True)
    ap.add_argument("--targets", help="calib_room.targets.json: one pair per target")
    ap.add_argument("--points", help='"x,y,z;x,y,z;..." world fixation points, metres')
    ap.add_argument("--ipd", type=float, default=DEFAULT_IPD_M, help="interocular distance, metres")
    ap.add_argument("--vergence", choices=["on", "off"], default="on",
                    help="on: each eye fixates P; off: both eyes take the cyclopean gaze (the control)")
    ap.add_argument("--e2", type=float, default=2.0)
    ap.add_argument("--emax", type=float, default=45.0)
    ap.add_argument("--s0", type=float, default=0.05)
    ap.add_argument("--n", type=int, default=None)
    ap.add_argument("--spp", type=int, default=64)
    ap.add_argument("--device", default="OPTIX", choices=["OPTIX", "CUDA", "CPU"])
    ap.add_argument("--shader", default=os.path.join(HERE, "foveated_camera.osl"))
    ap.add_argument("--seed-pair", dest="seed_pair", action="store_true", default=False,
                    help="also render every fixation at seed 1 (fix_b.exr, samples_b.npz), as fixation_sequence.py "
                         "does; off by default here because B1's checks are geometric")
    add_profile(ap, script_args(), s0="s0", spp="fix_spp")
    args = ap.parse_args(script_args())
    verged = args.vergence == "on"

    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args.blend))
    out = os.path.abspath(args.out)
    for e in EYE_NAMES:
        os.makedirs(os.path.join(out, e), exist_ok=True)
    t_seq0 = time.perf_counter()

    scene = bpy.context.scene
    ensure_cycles(scene)
    backend = setup_device(scene, args.device)
    bpy.context.view_layer.update()
    eye, eye_note = find_eye(scene)
    eye_m = rigid(eye.matrix_world)
    head_rot3 = np.array([[eye_m[r][c] for c in range(3)] for r in range(3)], dtype=np.float64)
    head_origin = np.array([eye_m.translation[k] for k in range(3)], dtype=np.float64)
    centres = eye_centres(head_origin, head_rot3, args.ipd)
    offsets = eye_offsets_local(args.ipd)
    points = load_points(args.targets, args.points, head_origin)
    pairs = [dict(pt, **pair_for_point(np.array(pt["point_m"]), head_origin, head_rot3, args.ipd, verged))
             for pt in points]

    n = args.n if args.n else raster_size(args.s0, args.e2, args.emax)
    s0 = s0_of(n, args.e2, args.emax)
    rs = raster_samples(n, args.e2, args.emax)
    inside = rs["inside"]
    n_inside = int(inside.sum())
    cp = centre_pixels(n)
    print(f"[pairs] {eye_note}; device {backend}; raster {n}x{n}; s0 {s0:.4f} deg; E2 {args.e2}; e_max {args.emax}; "
          f"ipd {args.ipd} m; vergence {args.vergence}; {len(pairs)} pairs at {args.spp} spp; "
          f"{n_inside} samples per fixation", flush=True)
    print(f"[pairs] head origin {head_origin.round(4).tolist()}; eye L {centres[0].round(4).tolist()} "
          f"R {centres[1].round(4).tolist()}", flush=True)

    cam = setup_foveated_camera(scene, eye, args.shader, args.e2, args.emax, n, args.spp, exr_codec="NONE")

    g0 = pairs[0]["eyes"][0]
    set_gaze(cam, eye, g0["yaw"], g0["pitch"], offsets[0])
    warmup = render_fixation(scene, args.spp)
    print(f"[pairs] warm-up render {warmup:.3f}s (discarded)", flush=True)

    def grab(pid: int, k: int, g: dict, point_m: list, exr_path: str) -> tuple[dict, dict]:
        """Save the live Render Result, read it back, build the D1 v2 record and measure the
        centre pixels (in-session, exr_lite; the host checker judges)."""
        save_render_result(scene, exr_path)             # before the next render: shared buffer
        ch = read_uncompressed_exr(exr_path)
        rgb = np.stack([ch[[c_ for c_ in ch if c_.endswith(f"Combined.{c}")][0]] for c in "RGB"], -1)
        depth = ch[[c_ for c_ in ch if c_.endswith("Depth.Z")][0]]
        pos = np.stack([ch[[c_ for c_ in ch if c_.endswith(f"Position.{a}")][0]] for a in "XYZ"], -1)
        if rgb.shape[:2] != (n, n):
            raise RuntimeError(f"pair {pid} eye {EYE_NAMES[k]}: file is {rgb.shape[:2]}, raster is {n}x{n}")
        d_head = to_eye_frame(rs["direction_cam"][inside], g["yaw"], g["pitch"])
        rec = {
            "origin": centres[k].astype(np.float32),
            "direction": d_head.astype(np.float32),
            "value": rgb[inside].astype(np.float32),
            "footprint": rs["footprint"][inside].astype(np.float32),
            "distance": depth[inside].astype(np.float32),
            "fixation_id": np.full(n_inside, pid, dtype=np.int32),
            "raster_index": rs["raster_index"][inside].astype(np.int32),
            "eye_id": np.full(n_inside, k, dtype=np.int32),
            "pair_id": np.full(n_inside, pid, dtype=np.int32),
        }
        c_pos = pos[cp[:, 0], cp[:, 1]]
        c_dep = depth[cp[:, 0], cp[:, 1]]
        p = np.array(point_m, dtype=np.float64)
        measured = {
            "centre_pixels": cp.tolist(),
            "centre_position_m": c_pos.mean(0).round(6).tolist(),
            "centre_depth_m": float(c_dep.mean()),
            "centre_hit": bool((c_dep < 1e9).all()),
            "miss_m": float(np.linalg.norm(c_pos.mean(0) - p)),
            "hits": int((depth[inside] < 1e9).sum()),
        }
        return rec, measured

    seq_fix = {e: [] for e in EYE_NAMES}
    for pid, g_pair in enumerate(pairs):
        g_pair["render"] = {}
        line = f"[pairs] p{pid:03d} {g_pair['name']:<16} verg {g_pair['vergence_deg']:5.2f} deg"
        for k, g in enumerate(g_pair["eyes"]):
            en = EYE_NAMES[k]
            fdir = os.path.join(out, en, f"f{pid:03d}")
            os.makedirs(fdir, exist_ok=True)
            set_gaze(cam, eye, g["yaw"], g["pitch"], offsets[k])
            secs = render_fixation(scene, args.spp)
            t_io = time.perf_counter()
            rec, measured = grab(pid, k, g, g_pair["point_m"], os.path.join(fdir, "fix.exr"))
            np.savez(os.path.join(fdir, "samples.npz"), **rec)
            meta = fixation_meta(scene, eye, eye_note, cam, backend, n, s0, args.e2, args.emax, args.spp,
                                 g["yaw"], g["pitch"], secs, args.profile, seconds_include_write=False)
            meta.update({"schema": SCHEMA, "fixation_id": pid, "pair_id": pid, "eye": en, "eye_id": k,
                         "eye_centre_m": centres[k].round(6).tolist(), "eye_offset_local_m": offsets[k].tolist(),
                         "ipd_m": args.ipd, "vergence": args.vergence, "point_m": g_pair["point_m"],
                         "name": g_pair["name"], "target_kind": g_pair["kind"],
                         "samples_inside_disc": n_inside, "exr_codec": "NONE",
                         "footprint_sum_sr": float(rec["footprint"].sum()), "cap_sr": cap_sr(args.emax),
                         "rendered_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")})
            with open(os.path.join(fdir, "meta.json"), "w") as fh:
                json.dump(meta, fh, indent=1)
            with open(os.path.join(fdir, "columns.json"), "w") as fh:
                json.dump(COLUMNS, fh, indent=1)
            io_secs = time.perf_counter() - t_io
            g["measured_in_session"] = measured
            g["render_seconds"] = round(secs, 4)
            seq_fix[en].append({"id": pid, "name": g_pair["name"], "yaw": g["yaw"], "pitch": g["pitch"],
                                "render_seconds": round(secs, 4), "io_seconds": round(io_secs, 4),
                                "samples": n_inside, "hits": measured["hits"], "pair_id": pid, "eye": en})
            line += (f"  {en}: {secs:.3f}s miss {1e3 * measured['miss_m']:6.2f} mm "
                     f"(pred {1e3 * g['predicted_miss_m']:6.2f}) depth {measured['centre_depth_m']:.4f} "
                     f"(pred {g['predicted_distance_m']:.4f})")
        print(line, flush=True)

    if args.seed_pair:
        t_b0 = time.perf_counter()
        for pid, g_pair in enumerate(pairs):
            for k, g in enumerate(g_pair["eyes"]):
                fdir = os.path.join(out, EYE_NAMES[k], f"f{pid:03d}")
                set_gaze(cam, eye, g["yaw"], g["pitch"], offsets[k])
                secs_b = render_fixation(scene, args.spp, seed=1)
                rec_b, _ = grab(pid, k, g, g_pair["point_m"], os.path.join(fdir, "fix_b.exr"))
                np.savez(os.path.join(fdir, "samples_b.npz"), **rec_b)
                seq_fix[EYE_NAMES[k]][pid]["render_seconds_seed1"] = round(secs_b, 4)
        render_fixation(scene, args.spp, seed=0)
        print(f"[pairs] seed-1 pass: {2 * len(pairs)} renders in {time.perf_counter() - t_b0:.1f}s", flush=True)

    total = time.perf_counter() - t_seq0
    common = {"blend": bpy.data.filepath, "device": backend, "blender": bpy.app.version_string,
              "profile": args.profile, "eye_note": eye_note, "schema": SCHEMA,
              "warp": {"E2_deg": args.e2, "e_max_deg": args.emax, "s0_deg": s0, "raster": n},
              "spp": args.spp, "samples_per_fixation": n_inside, "seed_pair": args.seed_pair,
              "warmup_seconds_discarded": warmup}
    rig = {"head": eye_record(eye), "head_origin_m": head_origin.tolist(),
           "head_rot3_world_from_local": head_rot3.tolist(), "ipd_m": args.ipd,
           "eye_offsets_local_m": offsets.tolist(), "eye_centres_m": centres.tolist(),
           "gaze_composition": "intrinsic yaw-then-pitch about the eye centre, Ry(-yaw) Rx(pitch); no torsion (assumed, B1)"}
    for k, en in enumerate(EYE_NAMES):
        rsec = np.array([f["render_seconds"] for f in seq_fix[en]])
        seq = dict(common)
        seq.update({"eye": en, "eye_id": k, "origin_m": centres[k].tolist(), "rig": rig,
                    "vergence": args.vergence,
                    "gazes": [{"name": p["name"], "yaw": p["eyes"][k]["yaw"], "pitch": p["eyes"][k]["pitch"],
                               "kind": p["kind"], "pair_id": i} for i, p in enumerate(pairs)],
                    "fixations": seq_fix[en],
                    "render_seconds_median": float(np.median(rsec)),
                    "render_seconds_min": float(rsec.min()), "render_seconds_max": float(rsec.max()),
                    "render_seconds_sum": float(rsec.sum()), "sequence_wall_seconds": total,
                    "timing_sweep": None, "note": "per-eye view of a fixation-pair run; see ../pairs.json"})
        with open(os.path.join(out, en, "sequence.json"), "w") as fh:
            json.dump(seq, fh, indent=1)

    all_sec = np.array([g["render_seconds"] for p in pairs for g in p["eyes"]])
    result = dict(common)
    result.update({"rig": rig, "vergence": args.vergence, "verged": verged,
                   "targets_file": os.path.abspath(args.targets) if args.targets else None,
                   "pairs": pairs, "eyes": list(EYE_NAMES),
                   "render_seconds_median_per_fixation": float(np.median(all_sec)),
                   "render_seconds_sum": float(all_sec.sum()),
                   "pair_seconds_median": float(np.median([sum(g["render_seconds"] for g in p["eyes"]) for p in pairs])),
                   "sequence_wall_seconds": total,
                   "measured_in_session_note": "centre_* and miss_m are read with exr_lite inside Blender and are "
                                               "reported only; tools/check_pairs.py re-measures and judges"})
    with open(os.path.join(out, "pairs.json"), "w") as fh:
        json.dump(result, fh, indent=1)
    miss = np.array([g["measured_in_session"]["miss_m"] for p in pairs for g in p["eyes"] if p["kind"] != "wire"])
    print(f"[pairs] {len(pairs)} pairs: {result['pair_seconds_median']:.3f}s median per pair, sum {all_sec.sum():.1f}s, "
          f"wall {total:.1f}s; centre miss on cards median {1e3 * np.median(miss) if len(miss) else float('nan'):.2f} mm, "
          f"max {1e3 * miss.max() if len(miss) else float('nan'):.2f} mm (in-session; judged by check_pairs.py) -> {out}",
          flush=True)


def run():
    try:
        main()
    except BaseException:
        traceback.print_exc()
        print("[pairs] FAILED", flush=True)
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)


if __name__ == "__main__":
    run()
