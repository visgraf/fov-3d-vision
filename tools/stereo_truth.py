"""Ground-truth stereo correspondence for a fixation-pair run — host side, venv (B2, D13).

    .venv/bin/python tools/stereo_truth.py previews/pairs/calib_room
    .venv/bin/python tools/stereo_truth.py previews/pairs/calib_room_control     # vergence off

No rendering: everything comes from B1's fix.exr (Position and Depth passes), samples.npz and
pairs.json. For every sample of each eye, the world point its ray hit and where that point is
seen from the other eye. Written as a sidecar next to samples.npz, <run>/<L|R>/f<NNN>/truth.npz
(the D1 record stays what the renderer emitted; derived labels are sidecars):
    hit_world      (N,3)  world point of this sample, from the Position pass
    theta, phi     (N,)   epipolar coordinates of the sample's own (analytic) direction, deg
    theta_other    (N,)   epipolar theta of the hit point seen from the other eye's centre
    phi_other      (N,)   its phi; equal to phi up to the direction error of check (a)
    dir_other      (N,3)  that direction, head frame, unit
    parallax       (N,)   theta_R - theta_L, deg (positive for every finite point; equals the
                          vergence at the fixated point)
    other_raster   (N,2)  continuous (row, col) where the point falls in the other eye's raster
                          of the same pair (inverse warp); NaN outside its disc
    other_visible  (N,)   int8: 1 the other eye sees this point (its depth there agrees within
                          --vis-tol), 0 occluded (something nearer), -1 outside the other eye's
                          disc, 2 inconsistent (the other eye sees farther than the point: a
                          depth-edge average or an error; counted, reported)
    truth_columns.json
And <run>/truth.json: per-pair and run-level statistics, the checks, and their bounds.

Checks, each of which can fail (exit 1):
  (i) epipolar  phi of the own direction and phi_other agree, as a great-circle distance across
      epipolar lines, within --epi-tol x s0 at p99.9. Samples within --axis-deg of the baseline
      axis are excluded (phi is ill-conditioned there) and counted.
  (j) inverse warp  each eye's own hit points, sent through the other-eye path with its OWN
      gaze, land back on their own raster index: nearest pixel must match for >= --roundtrip
      of samples.
  (k) triangulation identity  triangulate(theta, theta_other) reproduces the Position pass's
      ray distance for every hit: the implied angular error |dD|/D * tan(gamma) is within
      --epi-tol x s0 at p99.9 (same exclusion as (i)).
  (h) depth at the fixated cards  the L centre pixels' hit point, triangulated from L's gaze
      direction and the point's theta seen from R, must give the cyclopean distance the Position
      pass reports for that point, within one depth quantum (rig.depth_quantum_m: one spacing of
      parallax at that distance, 0.11 m at 2 m small) — on any run. On a verged run it must also
      match the target's distance_m (the check named in the Phase A summary). Judged on cards;
      wires reported. A second estimator, 'naive', assumes zero parallax at the centre
      (theta_R from R's own gaze): it must pass against the target on a verged run and FAIL on a
      --vergence off run (parallel rays triangulate to infinity). That is this tool's control.
Reported: parallax at the centre against the vergence; visibility fractions; theta range.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np
import OpenEXR

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rig import EYE_NAMES, depth_quantum_m, epipolar, phi_distance_deg, to_camera_frame, to_eye_frame, triangulate  # noqa: E402
from warp import centre_pixels, raster_of_direction  # noqa: E402

JUDGED_KINDS = {"ring", "ladder", "point"}

TRUTH_COLUMNS = {
    "hit_world": {"shape": "(N,3)", "frame": "world", "unit": "m", "note": "Position pass at the sample's raster index"},
    "theta": {"shape": "(N,)", "unit": "deg", "note": "epipolar theta of the own analytic direction: angle from the head +X (baseline) axis"},
    "phi": {"shape": "(N,)", "unit": "deg", "note": "epipolar plane of the own direction: atan2(d_y, -d_z), 0 forward-horizontal, +90 up"},
    "theta_other": {"shape": "(N,)", "unit": "deg", "note": "theta of hit_world seen from the other eye's centre"},
    "phi_other": {"shape": "(N,)", "unit": "deg", "note": "phi of the same; equals phi up to check (a)'s direction error"},
    "dir_other": {"shape": "(N,3)", "frame": "head", "unit": "unit vector", "note": "(hit_world - C_other) normalised"},
    "parallax": {"shape": "(N,)", "unit": "deg", "note": "theta_R - theta_L; positive for finite points; the vergence at the fixated point"},
    "other_raster": {"shape": "(N,2)", "frame": "other eye's fix.exr of the same pair, continuous (row, col), pixel centres at integers", "note": "NaN outside its disc"},
    "other_visible": {"shape": "(N,)", "unit": "int8", "note": "1 visible, 0 occluded, -1 outside disc, 2 inconsistent"},
    "_schema": "truth-v1 (D13)",
}


def read_exr(path: str) -> dict[str, np.ndarray]:
    chans: dict[str, np.ndarray] = {}
    with OpenEXR.File(path) as f:
        for part in f.parts:
            for name, ch in part.channels.items():
                chans[name] = np.asarray(ch.pixels)
    return chans


def find(chans, suffix):
    for k, v in chans.items():
        if k.endswith(suffix):
            return v
    raise KeyError(f"no channel ending in {suffix!r}; have {sorted(chans)}")


def unit(v: np.ndarray) -> np.ndarray:
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-300)


def load_eye(run: str, en: str, pid: int) -> dict:
    fdir = os.path.join(run, en, f"f{pid:03d}")
    s = np.load(os.path.join(fdir, "samples.npz"))
    ch = read_exr(os.path.join(fdir, "fix.exr"))
    z = find(ch, "Depth.Z"); z = z[..., 0] if z.ndim == 3 else z
    pos = np.stack([find(ch, f"Position.{a}") for a in "XYZ"], -1).astype(np.float64)
    return {"dir": s["direction"].astype(np.float64), "ri": s["raster_index"], "dist": s["distance"].astype(np.float64),
            "origin": s["origin"].astype(np.float64), "z": z.astype(np.float64), "pos": pos, "fdir": fdir}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--epi-tol", type=float, default=1.0, help="(i), (k): tolerance in units of s0, p99.9")
    ap.add_argument("--axis-deg", type=float, default=5.0, help="exclude samples within this angle of the baseline axis from (i), (k)")
    ap.add_argument("--vis-tol", type=float, default=0.02, help="relative depth agreement for 'visible'")
    ap.add_argument("--roundtrip", type=float, default=0.99, help="(j): fraction of samples whose inverse warp lands on their own pixel")
    ap.add_argument("--depth-quanta", type=float, default=1.0, help="(h): tolerance in depth quanta")
    args = ap.parse_args()

    run = os.path.abspath(args.run)
    pj = json.load(open(os.path.join(run, "pairs.json")))
    verged = bool(pj["verged"])
    s0 = float(pj["warp"]["s0_deg"])
    e2, emax, n = pj["warp"]["E2_deg"], pj["warp"]["e_max_deg"], int(pj["warp"]["raster"])
    ipd = float(pj["rig"]["ipd_m"])
    head_rot3 = np.array(pj["rig"]["head_rot3_world_from_local"], dtype=np.float64)
    head_origin = np.array(pj["rig"]["head_origin_m"], dtype=np.float64)
    centres = np.array(pj["rig"]["eye_centres_m"], dtype=np.float64)
    cp = centre_pixels(n)
    fails, per = [], []
    epi_all, tri_all, rt_ok, rt_n = [], [], 0, 0
    vis_counts = np.zeros(4, dtype=np.int64)      # visible, occluded, outside, inconsistent

    for pid, pair in enumerate(pj["pairs"]):
        eyes = [load_eye(run, en, pid) for en in EYE_NAMES]
        gazes = [(g["yaw"], g["pitch"]) for g in pair["eyes"]]
        rec = {"pair_id": pid, "name": pair["name"], "kind": pair["kind"], "judged": pair["kind"] in JUDGED_KINDS,
               "vergence_pred_deg": pair["vergence_deg"], "eyes": []}
        for k in range(2):
            me, other = eyes[k], eyes[1 - k]
            en = EYE_NAMES[k]
            hit = me["dist"] < 1e9
            Q = me["pos"][me["ri"][:, 0], me["ri"][:, 1]]                       # world hit points
            d_own = me["dir"]
            th, ph = epipolar(d_own)
            d_oth_w = unit(Q - centres[1 - k])
            d_oth = d_oth_w @ head_rot3                                        # world -> head frame
            th_o, ph_o = epipolar(d_oth)
            parallax = (th_o - th) if k == 0 else (th - th_o)
            # where the point falls in the other eye's raster (same pair, its gaze)
            rc, inside = raster_of_direction(to_camera_frame(d_oth, *gazes[1 - k]), n, e2, emax)
            rc = np.where(inside[:, None] & hit[:, None], rc, np.nan)
            vis = np.full(len(Q), -1, dtype=np.int8)
            ok = inside & hit
            rr = np.clip(np.rint(rc[ok, 0]).astype(int), 0, n - 1); cc = np.clip(np.rint(rc[ok, 1]).astype(int), 0, n - 1)
            z_o = other["z"][rr, cc]
            D_o = np.linalg.norm(Q[ok] - centres[1 - k], axis=-1)
            tol = args.vis_tol * D_o
            v = np.where(np.abs(z_o - D_o) <= tol, 1, np.where(z_o < D_o - tol, 0, 2)).astype(np.int8)
            vis[ok] = v
            for code, slot in ((1, 0), (0, 1), (-1, 2), (2, 3)):
                vis_counts[slot] += int((vis[hit] == code).sum())
            np.savez(os.path.join(me["fdir"], "truth.npz"),
                     hit_world=Q.astype(np.float32), theta=th.astype(np.float32), phi=ph.astype(np.float32),
                     theta_other=th_o.astype(np.float32), phi_other=ph_o.astype(np.float32),
                     dir_other=d_oth.astype(np.float32), parallax=parallax.astype(np.float32),
                     other_raster=rc.astype(np.float32), other_visible=vis)
            with open(os.path.join(me["fdir"], "truth_columns.json"), "w") as fh:
                json.dump(TRUTH_COLUMNS, fh, indent=1)

            # (i) epipolar agreement and (k) triangulation identity, away from the axis
            off_axis = hit & (th > args.axis_deg) & (th < 180.0 - args.axis_deg)
            epi = phi_distance_deg(ph, ph_o, th)[off_axis] / s0
            th_l, th_r = (th, th_o) if k == 0 else (th_o, th)
            Dl, Dr, gam = triangulate(th_l, th_r, ipd)
            D_me = np.linalg.norm(Q - centres[k], axis=-1)
            D_tri = Dl if k == 0 else Dr
            with np.errstate(invalid="ignore", divide="ignore"):
                implied = np.abs(D_tri - D_me) / D_me * np.tan(np.radians(gam))
            tri = np.degrees(implied[off_axis]) / s0
            # (j) inverse warp round trip on this eye's own hits with its own gaze
            rc_self, ins_self = raster_of_direction(to_camera_frame(unit(Q - centres[k]) @ head_rot3, *gazes[k]), n, e2, emax)
            same = ins_self[hit] & (np.rint(rc_self[hit]).astype(int) == me["ri"][hit]).all(axis=1)
            rt_ok += int(same.sum()); rt_n += int(hit.sum())
            er = {"eye": en, "hits": int(hit.sum()), "off_axis": int(off_axis.sum()),
                  "epi_s0_p999": float(np.percentile(epi, 99.9)) if len(epi) else None,
                  "epi_s0_max": float(epi.max()) if len(epi) else None,
                  "tri_s0_p999": float(np.nanpercentile(tri, 99.9)) if len(tri) else None,
                  "roundtrip_frac": float(same.mean()) if hit.any() else None,
                  "parallax_deg_range": [float(parallax[hit].min()), float(parallax[hit].max())] if hit.any() else None,
                  # sign judged off-axis only: within ~0.05 deg of the axis the geometric parallax
                  # (ipd sin theta / D, 2e-5 deg at 0.001 deg) is below check (a)'s direction residual
                  # (0.017 s0 = 0.0009 deg at full), so its sign is not resolvable there; the near-axis
                  # count is reported beside it
                  "parallax_neg_count": int((parallax[off_axis] <= 0).sum()),
                  "parallax_neg_count_near_axis": int((parallax[hit & ~off_axis] <= 0).sum()),
                  "visible_frac": float((vis[hit] == 1).mean()) if hit.any() else None,
                  "occluded_frac": float((vis[hit] == 0).mean()) if hit.any() else None,
                  "outside_frac": float((vis[hit] == -1).mean()) if hit.any() else None,
                  "inconsistent_frac": float((vis[hit] == 2).mean()) if hit.any() else None}
            epi_all.append(epi); tri_all.append(tri)
            rec["eyes"].append(er)

        # (h) depth at the fixated point: L's centre pixels, triangulated two ways
        L, R = eyes
        Qc = L["pos"][cp[:, 0], cp[:, 1]].mean(0)
        D_cyc_true = float(np.linalg.norm(Qc - head_origin))
        # gaze directions in the head frame: to_eye_frame of the camera-shader +Z axis
        gL = to_eye_frame(np.array([[0.0, 0.0, 1.0]]), *gazes[0])[0]
        gR = to_eye_frame(np.array([[0.0, 0.0, 1.0]]), *gazes[1])[0]
        thL, _ = epipolar(gL)
        thR_truth, _ = epipolar(unit(Qc - centres[1]) @ head_rot3)
        thR_naive, _ = epipolar(gR)
        est = {}
        for name, thR in (("truth", thR_truth), ("naive", thR_naive)):
            Dl, _, gam = triangulate(float(thL), float(thR), ipd)
            P_est = centres[0] + float(Dl) * (head_rot3 @ gL) if np.isfinite(Dl) else None
            D_cyc = float(np.linalg.norm(P_est - head_origin)) if P_est is not None else float("inf")
            est[name] = {"parallax_deg": float(gam), "distance_L_m": float(Dl), "cyclopean_m": D_cyc}
        target_D = float(pair["target"]["distance_m"]) if pair.get("target") and "distance_m" in pair["target"] else pair["cyclopean_distance_m"]
        q_hit = float(depth_quantum_m(D_cyc_true, s0, ipd))          # one spacing of parallax at the hit's distance
        q_target = float(depth_quantum_m(target_D, s0, ipd))
        rec.update({"h_target_distance_m": target_D, "h_position_pass_cyclopean_m": D_cyc_true,
                    "h_depth_quantum_hit_m": q_hit, "h_depth_quantum_target_m": q_target,
                    "h_truth": est["truth"], "h_naive": est["naive"],
                    "centre_parallax_deg": est["truth"]["parallax_deg"]})
        if rec["judged"]:
            # the correspondence must triangulate the point the centre ray actually hit, on any run
            e_hit = abs(est["truth"]["cyclopean_m"] - D_cyc_true)
            rec["h_truth_pass"] = e_hit <= args.depth_quanta * q_hit
            if not rec["h_truth_pass"]:
                fails.append(f"p{pid:03d}: (h) truth triangulation {est['truth']['cyclopean_m']:.4f} m vs the Position pass's "
                             f"{D_cyc_true:.4f} (tol {args.depth_quanta * q_hit:.4f})")
            # against the target's known distance: truth on a verged run; naive passes verged, fails control
            e_target_truth = abs(est["truth"]["cyclopean_m"] - target_D)
            e_target_naive = abs(est["naive"]["cyclopean_m"] - target_D)
            rec["h_target_truth_pass"] = e_target_truth <= args.depth_quanta * q_target
            rec["h_target_naive_pass"] = e_target_naive <= args.depth_quanta * q_target
            if verged and not rec["h_target_truth_pass"]:
                fails.append(f"p{pid:03d}: (h) truth triangulation {est['truth']['cyclopean_m']:.4f} m vs target {target_D:.4f} "
                             f"(tol {args.depth_quanta * q_target:.4f})")
            if verged and not rec["h_target_naive_pass"]:
                fails.append(f"p{pid:03d}: (h) naive (zero-parallax) estimate {est['naive']['cyclopean_m']:.4f} m vs target "
                             f"{target_D:.4f} on a verged run (tol {args.depth_quanta * q_target:.4f})")
            if not verged and rec["h_target_naive_pass"]:
                fails.append(f"p{pid:03d}: (h) control: naive estimate {est['naive']['cyclopean_m']:.4f} m still within "
                             f"{args.depth_quanta * q_target:.4f} of the target with vergence off")
        per.append(rec)

    epi_cat, tri_cat = np.concatenate(epi_all), np.concatenate(tri_all)
    tri_cat = tri_cat[np.isfinite(tri_cat)]
    summary = {"run": run, "verged": verged, "pairs": len(per), "s0_deg": s0, "ipd_m": ipd,
               "epi_s0_p999": float(np.percentile(epi_cat, 99.9)), "epi_s0_max": float(epi_cat.max()),
               "tri_s0_p999": float(np.percentile(tri_cat, 99.9)), "tri_s0_max": float(tri_cat.max()),
               "roundtrip_frac": rt_ok / max(rt_n, 1), "axis_excluded": int(sum(e["hits"] - e["off_axis"] for r in per for e in r["eyes"])),
               "parallax_nonpositive": int(sum(e["parallax_neg_count"] for r in per for e in r["eyes"])),
               "parallax_nonpositive_near_axis_reported": int(sum(e["parallax_neg_count_near_axis"] for r in per for e in r["eyes"])),
               "visibility": {"visible": int(vis_counts[0]), "occluded": int(vis_counts[1]), "outside_disc": int(vis_counts[2]),
                              "inconsistent": int(vis_counts[3]), "vis_tol_rel": args.vis_tol},
               "h_judged": int(sum(r["judged"] for r in per)),
               "h_truth_err_vs_hit_m_max": float(max(abs(r["h_truth"]["cyclopean_m"] - r["h_position_pass_cyclopean_m"]) for r in per if r["judged"])),
               "h_truth_err_vs_target_m_max": float(max(abs(r["h_truth"]["cyclopean_m"] - r["h_target_distance_m"]) for r in per if r["judged"])),
               "h_quantum_target_m_range": [float(min(r["h_depth_quantum_target_m"] for r in per)), float(max(r["h_depth_quantum_target_m"] for r in per))],
               "centre_parallax_minus_vergence_deg_max": float(max(abs(r["centre_parallax_deg"] - (r["vergence_pred_deg"] if verged else r["centre_parallax_deg"]))
                                                                  for r in per if r["judged"])) if verged else None,
               "fails": fails}
    if summary["epi_s0_p999"] > args.epi_tol:
        fails.append(f"(i) epipolar phi disagreement {summary['epi_s0_p999']:.3f} s0 at p99.9")
    if summary["tri_s0_p999"] > args.epi_tol:
        fails.append(f"(k) triangulation identity off by {summary['tri_s0_p999']:.3f} s0 (implied angle) at p99.9")
    if summary["roundtrip_frac"] < args.roundtrip:
        fails.append(f"(j) inverse warp round trip lands on the own pixel for only {100 * summary['roundtrip_frac']:.2f}%")
    if summary["parallax_nonpositive"]:
        fails.append(f"{summary['parallax_nonpositive']} samples have non-positive parallax (sign or centre error)")
    if summary["parallax_nonpositive_near_axis_reported"]:
        print(f"[truth] reported: {summary['parallax_nonpositive_near_axis_reported']} samples within {args.axis_deg} deg of the axis "
              f"have non-positive parallax (sign unresolvable there: geometric parallax below check (a)'s residual); not judged")
    summary["fails"] = fails
    with open(os.path.join(run, "truth.json"), "w") as fh:
        json.dump({"summary": summary, "pairs": per}, fh, indent=1)

    for r in per:
        line = (f"[truth] p{r['pair_id']:03d} {r['name']:<16} {'' if r['judged'] else '(reported) '}"
                f"parallax {r['centre_parallax_deg']:6.3f} (verg {r['vergence_pred_deg']:6.3f})  "
                f"depth truth {r['h_truth']['cyclopean_m']:7.4f} naive {r['h_naive']['cyclopean_m']:9.4f} target {r['h_target_distance_m']:.4f} "
                f"(quantum {r['h_depth_quantum_target_m']:.4f})  vis {r['eyes'][0]['visible_frac']:.3f}/{r['eyes'][1]['visible_frac']:.3f}")
        print(line)
    v = summary["visibility"]; tot = max(sum(v[x] for x in ("visible", "occluded", "outside_disc", "inconsistent")), 1)
    print(f"[truth] {'verged' if verged else 'CONTROL (vergence off)'}: {len(per)} pairs; (i) epipolar {summary['epi_s0_p999']:.3f} s0 p99.9 "
          f"(max {summary['epi_s0_max']:.3f}); (k) triangulation {summary['tri_s0_p999']:.3f} s0; (j) round trip {100 * summary['roundtrip_frac']:.3f}%; "
          f"{summary['axis_excluded']} samples within {args.axis_deg} deg of the axis excluded; "
          f"visible {100 * v['visible'] / tot:.1f}% occluded {100 * v['occluded'] / tot:.1f}% outside {100 * v['outside_disc'] / tot:.1f}% "
          f"inconsistent {100 * v['inconsistent'] / tot:.2f}%; (h) truth max error {summary['h_truth_err_vs_hit_m_max']:.4f} m vs the hit, "
          f"{summary['h_truth_err_vs_target_m_max']:.4f} m vs the target (target quantum {summary['h_quantum_target_m_range'][0]:.3f}-"
          f"{summary['h_quantum_target_m_range'][1]:.3f} m)")
    for f in fails:
        print("[truth] FAIL", f)
    print(f"[truth] {'FAILED' if fails else 'ok'} ({len(fails)} failures) -> {os.path.join(run, 'truth.json')}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
