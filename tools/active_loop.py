"""The active loop (C2, D17): observe a verged pair, infer inverse depth everywhere the pair
looked, choose the next fixation from what is known, observe again — in one Blender session.

    blender -b scenes/calib_room/calib_room.blend -P tools/active_loop.py -- \\
        --out previews/loop/calib_info --profile small --policy info --fixations 50
    blender -b scenes/calib_room/calib_room.blend -P tools/active_loop.py -- \\
        --out previews/loop/calib_targets --profile small --policy targets --fixations 50 \\
        --targets scenes/calib_room/calib_room.targets.json
    .venv/bin/python tools/dev/fake_blender_loop.py --out /tmp/loop/info --policy info --fixations 20 --profile small

Per fixation k: the policy (tools/belief.py) names a direction omega in the head frame; the
vergence distance z_hat is the belief's inverse-depth estimate within 2 deg of omega, else
its estimate over the field of regard, else --z0 (fixation 0 always: nothing is known); the
target-order policy takes its target's distance as Phase B did. P = origin + z_hat omega_world
is rendered as a pair by fixation_pairs.PairRenderer (the D1 record, unchanged, so
check_pairs.py, stereo_truth.py and stereo_field.py run on the result); the pair's field
(stereo_field.field_of_pair) is fused into the belief; the L eye's ray distances are
accumulated as truth; the belief is judged over the field of regard; the next fixation is
chosen. Noise for the field's bound: fixation 0 is rendered twice (a seed pair) and the
per-level sigma it measures is carried as an equivalent per-level relative noise for the rest
of the run (assumed thereafter, labelled); --noise-rel overrides.

Output, --out/: everything fixation_pairs.py writes (pairs.json with the policy record per
pair, L/, R/), field/p<NNN>.npz per pair, belief.npz (the final belief: mean, sigma, counts,
best measured level, visited level, truth, truth counts), loop.json (settings, the per-fixation
metrics and timings, the per-level sigma the policy used). The figure and the comparison
across policies are host side: tools/active_eval.py.
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
from belief import FORWARD, LevelSigma, Policy, SphereBelief  # noqa: E402
from fixation_pairs import PairRenderer, add_render_args, load_points  # noqa: E402
from rig import epipolar, gaze_of_world_direction, to_eye_frame  # noqa: E402
from stereo_field import field_of_pair, n_levels_for  # noqa: E402

POLICIES = ("targets", "random", "coverage", "info", "oracle")


def main():
    import bpy
    from bl_common import add_profile, script_args

    ap = argparse.ArgumentParser()
    add_render_args(ap)
    ap.add_argument("--policy", choices=POLICIES, required=True)
    ap.add_argument("--fixations", type=int, default=50)
    ap.add_argument("--targets", help="targets json; required by --policy targets, optional otherwise (unused)")
    ap.add_argument("--regard-deg", type=float, default=60.0, help="field of regard: cap about the primary gaze the policies choose in")
    ap.add_argument("--cand-deg", type=float, default=2.0, help="candidate grid step")
    ap.add_argument("--policy-levels", type=int, default=3, help="the policy scores the cells out to this many levels (3: 14 deg)")
    ap.add_argument("--belief-deg", type=float, default=None, help="belief cell; default s_eval = eval_factor x s0")
    ap.add_argument("--eval-factor", type=float, default=2.0)
    ap.add_argument("--z0", type=float, default=2.0, help="vergence distance when nothing is known, m")
    ap.add_argument("--sigma-prior", type=float, default=1.0, help="prior sigma of inverse depth, 1/m")
    ap.add_argument("--search-deg", type=float, default=6.0, help="the fovea's search range: a wrong vergence estimate from the periphery must stay inside it")
    ap.add_argument("--kappa", type=float, default=2.5)
    ap.add_argument("--floor-cells", type=float, default=0.3)
    ap.add_argument("--noise-rel", type=float, default=None, help="assumed per-pixel relative RMS; default: calibrated on fixation 0's seed pair")
    ap.add_argument("--nb-tol", type=float, default=None, help="D2b: drop LR-consistent cells more than this many cells from the median of their consistent neighbours (off by default)")
    ap.add_argument("--nb-drop-isolated", action="store_true", help="with --nb-tol: also drop cells with fewer than three consistent neighbours")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--ior-deg", type=float, default=None, help="explicit inhibition of return; default 0 for the policies, 3 for the oracle")
    add_profile(ap, script_args(), s0="s0", spp="fix_spp")
    args = ap.parse_args(script_args())
    if args.policy == "targets" and not args.targets:
        raise SystemExit("--policy targets needs --targets")

    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args.blend))
    R = PairRenderer(args, args.out)
    out = R.out
    os.makedirs(os.path.join(out, "field"), exist_ok=True)
    E2, emax, s0 = args.e2, args.emax, R.s0
    cell_b = args.belief_deg or args.eval_factor * s0
    nlev = n_levels_for(E2, args.eval_factor, emax)
    B = SphereBelief(cell_b, sigma_prior=args.sigma_prior)
    ls = LevelSigma(nlev)
    pol = Policy(args.policy, B, E2, args.eval_factor, emax, regard_deg=args.regard_deg, cand_deg=args.cand_deg,
                 policy_levels=args.policy_levels, seed=args.seed, level_sigma=ls, ior_deg=args.ior_deg)
    cap = pol.cap
    rays_per_pair = 2 * R.n_inside * args.spp
    targets = load_points(args.targets, None, R.head_origin) if args.policy == "targets" else None
    n_fix = min(args.fixations, len(targets)) if targets else args.fixations
    R.banner(n_fix)
    print(f"[loop] policy {args.policy}; belief {B.nth}x{B.nph} cells of {cell_b:.3f} deg; regard {args.regard_deg} deg, "
          f"{len(pol.cand)} candidates at {args.cand_deg} deg; policy radius {pol.R:.0f} deg; IOR {pol.ior_deg:g} deg; rays/pair {rays_per_pair}", flush=True)

    def fwd_world(d_head):
        return R.head_rot3 @ np.asarray(d_head, np.float64)

    def loads(rec):
        th, ph = epipolar(rec["direction"].astype(np.float64))
        return {"theta": th, "phi": ph, "val": rec["value"].astype(np.float64).mean(-1), "fp": rec["footprint"].astype(np.float64)}

    pairs, steps = [], []
    noise_rel = args.noise_rel
    noise_note = f"assumed --noise-rel {noise_rel}" if noise_rel is not None else "calibrated on fixation 0 (seed pair), then carried"
    t_loop0 = time.perf_counter()
    for k in range(n_fix):
        t0 = time.perf_counter()
        # ---- choose
        if targets:
            pt = targets[k]
            d_head = R.head_rot3.T @ (np.array(pt["point_m"]) - R.head_origin); d_head /= np.linalg.norm(d_head)
            z_hat, z_src, info = float(np.linalg.norm(np.array(pt["point_m"]) - R.head_origin)), "target", {"score": None}
            point = {"name": pt["name"], "kind": pt["kind"], "point_m": pt["point_m"], "target": pt["target"]}
        else:
            if k == 0:
                d_head, info = FORWARD.copy(), {"score": None}
                pol.history.append(d_head)
            else:
                d_head, info = pol.choose()
            z = B.rho_along(d_head, 2.0)
            if z is not None and z > 0:
                z_hat, z_src = 1.0 / z, "belief@2deg"
            else:
                zc = float(B.S[cap & (B.P > 0)].sum() / B.P[cap & (B.P > 0)].sum()) if (cap & (B.P > 0)).any() else 0.0
                z_hat, z_src = (1.0 / zc, "belief@cap") if zc > 0 else (args.z0, "z0")
            z_hat = float(np.clip(z_hat, 0.2, 50.0))
            P = R.head_origin + z_hat * fwd_world(d_head)
            point = {"name": f"k{k:03d}", "kind": "policy", "point_m": P.tolist(), "target": None}
        pair = R.pair_for(point)
        pair["policy"] = dict(info, name=args.policy, dir_head=np.asarray(d_head).round(6).tolist(), z_hat_m=z_hat, z_source=z_src)
        pairs.append(pair)
        if k == 0:
            R.warm_up(pair["eyes"][0])
        t1 = time.perf_counter()
        # ---- observe
        recs = R.render_pair(k, pair, quiet=True)
        L, Rr = loads(recs["L"]), loads(recs["R"])
        if k == 0 and noise_rel is None:
            from render_foveated import render_fixation, set_gaze
            for e, kk in (("L", 0), ("R", 1)):
                g = pair["eyes"][kk]
                set_gaze(R.cam, R.eye, g["yaw"], g["pitch"], R.offsets[kk])
                render_fixation(R.scene, args.spp, seed=[1, 3][kk])
                rec_b, _ = R.grab(k, kk, g, pair["point_m"], os.path.join(out, e, f"f{k:03d}", "fix_b.exr"))
                np.savez(os.path.join(out, e, f"f{k:03d}", "samples_b.npz"), **rec_b)
                (L if kk == 0 else Rr)["val_b"] = rec_b["value"].astype(np.float64).mean(-1)
        t2 = time.perf_counter()
        # ---- infer
        gaze = [to_eye_frame(np.array([[0.0, 0.0, 1.0]]), g["yaw"], g["pitch"])[0] for g in pair["eyes"]]
        f = field_of_pair(L, Rr, gaze[0], gaze[1], s0, E2, emax, args.ipd, eval_factor=args.eval_factor, search_deg=args.search_deg,
                          kappa=args.kappa, floor_cells=args.floor_cells, noise_rel=noise_rel,
                          nb_tol_cells=args.nb_tol, nb_drop_isolated=args.nb_drop_isolated)
        if k == 0 and noise_rel is None:
            noise_rel = [lv["noise_rel_equiv"] for lv in f["levels"]]
            L.pop("val_b", None); Rr.pop("val_b", None)
        np.savez_compressed(os.path.join(out, "field", f"p{k:03d}.npz"),
                            **{kk: v for kk, v in f.items() if kk not in ("levels", "gaze", "visits") and not kk.startswith("x_")})
        fused = B.fuse(f)
        ls.update(f)
        B.add_truth(recs["L"]["direction"], recs["L"]["distance"], recs["L"]["footprint"])
        t3 = time.perf_counter()
        m = B.metrics(cap)
        t4 = time.perf_counter()
        step = {"k": k, "name": pair["name"], "dir_head": pair["policy"]["dir_head"], "z_hat_m": z_hat, "z_source": z_src,
                "score": info.get("score"), "phase": info.get("phase"), "vergence_deg": pair["vergence_deg"],
                "centre_depth_m": pair["eyes"][0]["measured_in_session"]["centre_depth_m"],
                "vergence_err_m": abs(pair["eyes"][0]["measured_in_session"]["centre_depth_m"] - z_hat) if pair["eyes"][0]["measured_in_session"]["centre_hit"] else None,
                "rays_cum": (k + 1) * rays_per_pair, "field_cells": int(len(f["rho"])), "field_consistent": int(f["consistent"].sum()),
                "fused_cells": fused["cells_in"], "gated": fused["gated"], "level_sigma": list(ls.vals), "level_sigma_noise": list(ls.noise), "level_sigma_floor": list(ls.floor),
                "seconds": {"choose": round(t1 - t0, 3), "render": round(t2 - t1, 3), "infer": round(t3 - t2, 3), "judge": round(t4 - t3, 3)}}
        step.update(m)
        steps.append(step)
        print(f"[loop] k{k:03d} {args.policy:<8} dir ({math.degrees(math.atan2(d_head[0], -d_head[2])):+6.1f},{math.degrees(math.asin(np.clip(d_head[1], -1, 1))):+6.1f}) deg "
              f"z_hat {z_hat:5.2f} ({z_src:<11}) centre {step['centre_depth_m']:5.2f} m | cells {step['field_cells']:5d} fused {fused['cells_in']:6d} gated {fused['gated']:4d} | "
              f"cover any {m['coverage_any']:.3f} fine {m['coverage_fine']:.3f} | rho err med {m.get('rho_err_median', float('nan')):.4f} gross {m.get('gross_frac', float('nan')):.3f} "
              f"depth med {m.get('depth_err_median_m', float('nan')):.3f} m z {m.get('z_rms_inliers', float('nan')) or float('nan'):.2f} | "
              f"{t1 - t0:.2f}+{t2 - t1:.2f}+{t3 - t2:.2f}+{t4 - t3:.2f} s", flush=True)

    total = time.perf_counter() - t_loop0
    R.finish(pairs, extra={"loop": {"policy": args.policy, "fixations": n_fix, "regard_deg": args.regard_deg}})
    np.savez_compressed(os.path.join(out, "belief.npz"), **B.snapshot(), cap=cap, regard_deg=args.regard_deg)
    settings = {k_: v for k_, v in vars(args).items() if k_ not in ("shader",)}
    with open(os.path.join(out, "loop.json"), "w") as fh:
        json.dump({"settings": settings, "policy": args.policy, "s0_deg": s0, "belief_cell_deg": cell_b, "levels": nlev,
                   "rays_per_pair": rays_per_pair, "noise": noise_note, "noise_rel_per_level": noise_rel if isinstance(noise_rel, list) else [noise_rel] * nlev,
                   "level_sigma_final": list(ls.vals), "level_sigma_noise_final": list(ls.noise), "level_sigma_floor_final": list(ls.floor), "candidates": int(len(pol.cand)), "policy_radius_deg": pol.R,
                   "wall_seconds": total, "steps": steps}, fh, indent=1)
    last = steps[-1]
    sec = {kk: sum(s["seconds"][kk] for s in steps) for kk in ("choose", "render", "infer", "judge")}
    print(f"[loop] {args.policy}: {n_fix} fixations, {last['rays_cum']} rays, wall {total:.1f}s (choose {sec['choose']:.1f} render {sec['render']:.1f} "
          f"infer {sec['infer']:.1f} judge {sec['judge']:.1f}); final cover any {last['coverage_any']:.3f} fine {last['coverage_fine']:.3f}, "
          f"rho err median {last.get('rho_err_median', float('nan')):.4f} /m, gross {last.get('gross_frac', float('nan')):.3f}, "
          f"depth err median {last.get('depth_err_median_m', float('nan')):.3f} m, z RMS {last.get('z_rms_inliers') or float('nan'):.2f}; gated {last['gated_total']} -> {out}", flush=True)


def run():
    try:
        main()
    except BaseException:
        traceback.print_exc()
        print("[loop] FAILED", flush=True)
        sys.stdout.flush(); sys.stderr.flush()
        os._exit(1)


if __name__ == "__main__":
    run()
