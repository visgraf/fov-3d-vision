"""Check a fixation-pair run (fixation_pairs.py) — host side, venv. No reference panorama needed.

    .venv/bin/python tools/check_pairs.py previews/pairs/calib_room --sheet
    .venv/bin/python tools/check_pairs.py previews/pairs/calib_room_control --sheet   # vergence off

Checks, each of which can fail (exit 1), written to <run>/check.json:
  reader   samples.npz value and distance equal fix.exr's Combined and Depth at the stored raster
           indices (OpenEXR here vs exr_lite inside Blender): exact. origin equals this eye's
           centre in pairs.json.
  (a) warp the stored head-frame directions (analytic warp composed with this eye's gaze) agree
           with the Position pass seen from THIS eye's centre within --warp-tol x s0 (p99.9, hits
           only). This is the OSL-vs-numpy test vector, now with the eye off the head origin.
  (d) cap  footprints over the disc sum to 2 pi (1 - cos e_max) within --cap-tol.
  (e) foveae on target  the mean world Position of the raster's centre pixel(s) is within one
           sample spacing at the target's distance of the fixation point P: miss <= D_i * s0
           (radians), D_i the eye's predicted ray distance; the centre Depth equals D_i to the
           same tolerance. Judged on card and point targets; wires (thinner than a sample at the
           centre) are reported only.
  (f) control  when the run was made with --vergence off, (e) must FAIL on every judged
           fixation, by the amount rig.py predicts: where the centre ray hit the card plane
           (depth within tolerance of the predicted parallel-ray distance) the miss equals the
           predicted (ipd/2) sqrt(1 - (right . g)^2) within tolerance; where it left the card,
           the miss is at least that.
Reported, not judged: the measured vergence (angle at P between the two eyes' centre rays from
the Position pass) against the predicted one; wires' centre depth against 1.5 m.

--sheet writes sheet.png: the central +-<--sheet-deg> of L | R for the first --sheet-pairs pairs,
nearest-upscaled, crosshair at the raster centre. Verged: the target sits on the cross in both;
control: it sits off it by the predicted amount.
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
from rig import EYE_NAMES  # noqa: E402
from warp import cap_sr, centre_pixels, r_of_eccentricity  # noqa: E402

JUDGED_KINDS = {"ring", "ladder", "point"}


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


def angle_deg(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    c = np.einsum("...i,...i->...", a, b) / (np.linalg.norm(a, axis=-1) * np.linalg.norm(b, axis=-1))
    return np.degrees(np.arccos(np.clip(c, -1.0, 1.0)))


def tonemap(rgb: np.ndarray, white: float) -> np.ndarray:
    v = np.clip(rgb / max(white, 1e-6), 0.0, 1.0) ** (1.0 / 2.2)
    return (v * 255.0 + 0.5).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", help="folder written by fixation_pairs.py (pairs.json, L/, R/)")
    ap.add_argument("--warp-tol", type=float, default=1.0, help="(a) tolerance in units of s0, on the p99.9")
    ap.add_argument("--cap-tol", type=float, default=0.01)
    ap.add_argument("--centre-tol", type=float, default=1.0, help="(e) tolerance in sample spacings at the target's distance")
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--sheet-pairs", type=int, default=6)
    ap.add_argument("--sheet-deg", type=float, default=2.0)
    ap.add_argument("--sheet-scale", type=int, default=8)
    args = ap.parse_args()

    run = os.path.abspath(args.run)
    pj = json.load(open(os.path.join(run, "pairs.json")))
    verged = bool(pj["verged"])
    s0 = float(pj["warp"]["s0_deg"]); s0_rad = math.radians(s0)
    e2, emax, n = pj["warp"]["E2_deg"], pj["warp"]["e_max_deg"], int(pj["warp"]["raster"])
    centres = np.array(pj["rig"]["eye_centres_m"], dtype=np.float64)
    head_rot3 = np.array(pj["rig"]["head_rot3_world_from_local"], dtype=np.float64)   # world = R @ head-local
    cap = cap_sr(emax)
    cp = centre_pixels(n)
    fails, per = [], []
    crops: list[tuple[str, np.ndarray, np.ndarray, tuple[float, float]]] = []
    r_px = max(1, int(round(r_of_eccentricity(args.sheet_deg, e2, emax) * n / 2.0)))

    for pid, pair in enumerate(pj["pairs"]):
        p = np.array(pair["point_m"], dtype=np.float64)
        judged = pair["kind"] in JUDGED_KINDS
        rec = {"pair_id": pid, "name": pair["name"], "kind": pair["kind"], "judged": judged,
               "vergence_pred_deg": pair["vergence_deg"], "eyes": []}
        centre_dirs = []
        for k, g in enumerate(pair["eyes"]):
            en = EYE_NAMES[k]
            fdir = os.path.join(run, en, f"f{pid:03d}")
            s = np.load(os.path.join(fdir, "samples.npz"))
            ch = read_exr(os.path.join(fdir, "fix.exr"))
            comb, z = find(ch, "Combined"), find(ch, "Depth.Z")
            z = z[..., 0] if z.ndim == 3 else z
            pos = np.stack([find(ch, f"Position.{a}") for a in "XYZ"], -1).astype(np.float64)
            ri = s["raster_index"]; rows, cols = ri[:, 0], ri[:, 1]
            tag = f"p{pid:03d}/{en}"
            er = {"eye": en}

            # reader + origin
            er["reader_max_abs_diff"] = float(max(np.abs(s["value"] - comb[rows, cols, :3]).max(),
                                                  np.abs(s["distance"] - z[rows, cols]).max()))
            if er["reader_max_abs_diff"] != 0.0:
                fails.append(f"{tag}: samples.npz differs from fix.exr by {er['reader_max_abs_diff']:.3e}")
            if not np.allclose(s["origin"], centres[k], atol=1e-5) or not np.allclose(s["origin"], g["centre_m"], atol=1e-5):
                fails.append(f"{tag}: origin {s['origin'].tolist()} is not eye {en}'s centre {centres[k].tolist()}")
            if not (s["eye_id"] == k).all() or not (s["pair_id"] == pid).all():
                fails.append(f"{tag}: eye_id / pair_id columns wrong")

            # (a) analytic direction vs Position pass from this eye's centre, in units of s0
            hit = s["distance"] < 1e9
            dw = (pos[rows, cols] - centres[k]) @ head_rot3       # world -> head frame, as the record stores it
            ang = angle_deg(s["direction"].astype(np.float64)[hit], dw[hit])
            er["warp_s0_p999"] = float(np.percentile(ang, 99.9) / s0) if hit.any() else float("nan")
            er["warp_s0_max"] = float(ang.max() / s0) if hit.any() else float("nan")
            er["hits"] = int(hit.sum())
            if not (er["warp_s0_p999"] <= args.warp_tol):
                fails.append(f"{tag}: (a) directions off the Position pass by {er['warp_s0_p999']:.3f} s0 at p99.9")

            # (d) cap
            er["cap_ratio"] = float(s["footprint"].sum() / cap)
            if abs(er["cap_ratio"] - 1.0) > args.cap_tol:
                fails.append(f"{tag}: (d) footprints sum to {er['cap_ratio']:.4f} of the cap")

            # (e) the foveal centre on the target
            c_pos, c_dep = pos[cp[:, 0], cp[:, 1]], z[cp[:, 0], cp[:, 1]].astype(np.float64)
            D = float(g["predicted_distance_m"])
            tol = args.centre_tol * D * s0_rad
            miss = float(np.linalg.norm(c_pos.mean(0) - p))
            dep_err = float(abs(c_dep.mean() - D))
            on_plane = bool((c_dep < 1e9).all() and dep_err <= tol)
            er.update({"centre_position_m": c_pos.mean(0).round(6).tolist(), "centre_depth_m": float(c_dep.mean()),
                       "predicted_distance_m": D, "miss_m": miss, "miss_pred_m": g["predicted_miss_m"],
                       "miss_in_spacings": miss / (D * s0_rad), "tol_m": tol, "centre_on_plane": on_plane})
            centre_dirs.append(c_pos.mean(0) - centres[k])
            if judged:
                if verged:
                    er["e_pass"] = miss <= tol and on_plane
                    if not er["e_pass"]:
                        fails.append(f"{tag}: (e) centre misses P by {1e3 * miss:.2f} mm (tol {1e3 * tol:.2f}), "
                                     f"depth off by {1e3 * dep_err:.2f} mm")
                else:
                    pred = float(g["predicted_miss_m"])
                    # A target nearly on the interocular axis (the ladders at azimuth 83 deg) has a
                    # predicted parallel-ray miss below one spacing: the control cannot resolve it
                    # at this s0, so it is reported, not judged. Where it can, (e) must fail.
                    er["control_resolvable"] = pred > tol
                    er["e_fails_as_required"] = miss > tol
                    er["f_matches_prediction"] = (abs(miss - pred) <= tol) if on_plane else (miss >= pred - tol)
                    if er["control_resolvable"] and not er["e_fails_as_required"]:
                        fails.append(f"{tag}: (f) control still on target: miss {1e3 * miss:.2f} mm <= tol {1e3 * tol:.2f}")
                    elif not er["f_matches_prediction"]:
                        fails.append(f"{tag}: (f) control miss {1e3 * miss:.2f} mm vs predicted {1e3 * pred:.2f} "
                                     f"(on card: {on_plane})")
            rec["eyes"].append(er)
            if args.sheet and len(crops) < 2 * args.sheet_pairs:
                c0 = n // 2
                crop = comb[c0 - r_px:c0 + r_px, c0 - r_px:c0 + r_px, :3].astype(np.float32)
                crops.append((f"p{pid:03d} {pair['name']} {en}", crop, None, (miss, tol)))

        # measured vergence (reported)
        if len(centre_dirs) == 2:
            rec["vergence_meas_deg"] = float(angle_deg(np.array(centre_dirs[0]), np.array(centre_dirs[1])))
            rec["vergence_meas_minus_pred_deg"] = rec["vergence_meas_deg"] - (pair["vergence_deg"] if verged else 0.0)
        per.append(rec)

    # summary
    judged = [r for r in per if r["judged"]]
    miss_all = np.array([e["miss_m"] for r in judged for e in r["eyes"]])
    tol_all = np.array([e["tol_m"] for r in judged for e in r["eyes"]])
    summary = {
        "run": run, "verged": verged, "pairs": len(per), "judged_pairs": len(judged),
        "s0_deg": s0, "ipd_m": pj["rig"]["ipd_m"],
        "warp_s0_p999_max": float(max(e["warp_s0_p999"] for r in per for e in r["eyes"])),
        "cap_ratio_range": [float(min(e["cap_ratio"] for r in per for e in r["eyes"])),
                            float(max(e["cap_ratio"] for r in per for e in r["eyes"]))],
        "miss_mm_median": float(1e3 * np.median(miss_all)) if len(miss_all) else None,
        "miss_mm_max": float(1e3 * miss_all.max()) if len(miss_all) else None,
        "miss_in_spacings_max": float((miss_all / (tol_all / args.centre_tol)).max()) if len(miss_all) else None,
        "tol_mm_range": [float(1e3 * tol_all.min()), float(1e3 * tol_all.max())] if len(tol_all) else None,
        "vergence_meas_minus_pred_deg_max_abs": float(max(abs(r.get("vergence_meas_minus_pred_deg", 0.0)) for r in judged)) if judged else None,
        "fails": fails,
    }
    if not verged:
        summary["control_pred_miss_mm_range"] = [float(1e3 * min(e["miss_pred_m"] for r in judged for e in r["eyes"])),
                                                 float(1e3 * max(e["miss_pred_m"] for r in judged for e in r["eyes"]))]
        summary["control_on_card"] = int(sum(e["centre_on_plane"] for r in judged for e in r["eyes"]))
        summary["control_unresolvable"] = [f"p{r['pair_id']:03d}/{e['eye']}" for r in judged for e in r["eyes"]
                                           if not e["control_resolvable"]]
    with open(os.path.join(run, "check.json"), "w") as fh:
        json.dump({"summary": summary, "pairs": per}, fh, indent=1)

    for r in per:
        line = f"[check_pairs] p{r['pair_id']:03d} {r['name']:<16} {'' if r['judged'] else '(reported only) '}"
        for e in r["eyes"]:
            line += (f"{e['eye']}: miss {1e3 * e['miss_m']:7.2f} mm ({e['miss_in_spacings']:5.2f} s0"
                     + (f", pred {1e3 * e['miss_pred_m']:6.2f}" if not verged else "")
                     + f") warp {e['warp_s0_p999']:.3f} s0  ")
        if "vergence_meas_deg" in r:
            line += f"verg {r['vergence_meas_deg']:.3f} ({r['vergence_pred_deg']:.3f} pred)"
        print(line)
    if not verged and summary["control_unresolvable"]:
        print(f"[check_pairs] control not resolvable at this s0 (predicted miss below one spacing), reported only: "
              f"{' '.join(summary['control_unresolvable'])}")
    print(f"[check_pairs] {'verged' if verged else 'CONTROL (vergence off)'}: {len(judged)} judged pairs of {len(per)}; "
          f"miss median {summary['miss_mm_median']:.2f} mm, max {summary['miss_mm_max']:.2f} mm "
          f"({summary['miss_in_spacings_max']:.2f} spacings); (a) worst {summary['warp_s0_p999_max']:.3f} s0; "
          f"cap {summary['cap_ratio_range'][0]:.4f}-{summary['cap_ratio_range'][1]:.4f}")
    for f in fails:
        print("[check_pairs] FAIL", f)

    if args.sheet and crops:
        from PIL import Image, ImageDraw
        white = float(np.percentile(np.concatenate([c[1].reshape(-1, 3) for c in crops]), 99.0))
        sz = 2 * r_px * args.sheet_scale
        ncol = 2
        nrow = (len(crops) + 1) // 2
        sheet = Image.new("RGB", (ncol * (sz + 8) + 8, nrow * (sz + 24) + 8), (30, 30, 30))
        dr = ImageDraw.Draw(sheet)
        for i, (label, crop, _, (miss, tol)) in enumerate(crops):
            im = Image.fromarray(tonemap(crop, white)).resize((sz, sz), Image.NEAREST)
            x, y = 8 + (i % ncol) * (sz + 8), 8 + (i // ncol) * (sz + 24)
            sheet.paste(im, (x, y + 16))
            c = sz // 2
            dr.line([(x, y + 16 + c), (x + sz, y + 16 + c)], fill=(255, 0, 0))
            dr.line([(x + c, y + 16), (x + c, y + 16 + sz)], fill=(255, 0, 0))
            dr.text((x, y), f"{label}  miss {1e3 * miss:.1f} mm", fill=(230, 230, 230))
        dr.text((8, sheet.height - 12), f"central +-{args.sheet_deg} deg, {'verged' if verged else 'vergence OFF (control)'}, "
                f"s0 {s0} deg, x{args.sheet_scale}", fill=(200, 200, 200))
        sheet.save(os.path.join(run, "sheet.png"))
        print(f"[check_pairs] sheet -> {os.path.join(run, 'sheet.png')}")

    print(f"[check_pairs] {'FAILED' if fails else 'ok'} ({len(fails)} failures) -> {os.path.join(run, 'check.json')}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
