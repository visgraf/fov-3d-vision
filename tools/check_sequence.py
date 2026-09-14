"""Check a fixation sequence against the scene's reference panorama. Host side (venv).

    .venv/bin/python tools/check_sequence.py previews/sequence/calib_room \
        --reference previews/reference_small/calib_room

Checks, each of which can fail (exit 1), written to <sequence>/check.json:
  reader     samples.npz values and distances equal fix.exr's Combined and Depth at the stored
             raster indices (OpenEXR reader here vs exr_lite inside Blender): exact
  (a) warp   the stored EYE-frame directions (analytic warp composed with the gaze) land in
             the reference panorama within one reference pixel (p99.9) of where the Position
             pass says the ray went; samples that hit nothing are excluded
  (b) fovea  within --fovea-deg of the gaze, samples are binned into --cell-deg cells on the
             sphere (gnomonic coordinates about the gaze); per cell the footprint-weighted
             mean of the fixation's samples is compared with the cos(lat)-weighted box mean
             of the reference pixels in the same cell. Statistic: median over cells of the
             relative difference. The bound is measured per fixation from the seed pair the
             sequence rendered: noise_fix = the same binned statistic between seed 0 and
             seed 1 divided by sqrt(2); the reference term is noise_fix/4 (D7: both profiles
             have the reference at >= 16x the fixation spp); the binned alignment floor (the
             reference against its own half-pixel shift, binned the same way) enters in
             quadrature: bound = 1.5 * sqrt(noise_fix^2 + (noise_fix/4)^2 + floor_binned^2) (D10).
             With --plain, only plain-content fixations are judged (calib room: the wire
             targets; Classroom: gazes whose binned alignment floor is below 0.03); the rest
             report the statistic and the floor, labelled registration-limited, and never fail.
  (c) control  (b) with the whole fixation rotated --control-yaw degrees about the EYE's up
             axis must FAIL; if the texture were featureless it could not
  (d) cap    footprints over a fixation's disc sum to 2*pi*(1 - cos e_max) to 1%

Also reported, not a criterion: resampling_floor, the per-sample statistic (b) used before
2026-09-13: nearest reference pixel at each sample direction, median relative difference.
It measures sub-pixel alignment on texture edges (measured: it tracks the reference's own
disagreement with a half-pixel shift of itself), and A5 reports it as the floor of any
per-sample comparison. Its per-sample alignment floor is kept next to it.
"""
from __future__ import annotations

import argparse
import json
import math
import os

import numpy as np
import OpenEXR


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


def eye_rotation(eye: dict) -> np.ndarray:
    """EYE local axes as world columns: x = right = forward x up, y = up, z = -forward."""
    fwd, up = np.array(eye["forward"], float), np.array(eye["up"], float)
    right = np.cross(fwd, up)
    return np.stack([right, up, -fwd], axis=1)


def to_equirect_px(d: np.ndarray, w: int, h: int) -> np.ndarray:
    """EYE-frame unit directions -> continuous pixel coordinates in the reference."""
    lon = np.arctan2(d[:, 0], -d[:, 2])
    lat = np.arcsin(np.clip(d[:, 1], -1.0, 1.0))
    return np.stack([(lon / (2 * np.pi) + 0.5) * w, (0.5 - lat / np.pi) * h], axis=1)


def rot_y(deg: float) -> np.ndarray:
    a = math.radians(deg)
    return np.array([[math.cos(a), 0.0, math.sin(a)], [0.0, 1.0, 0.0], [-math.sin(a), 0.0, math.cos(a)]])


def rel_diff_median(value: np.ndarray, d: np.ndarray, ref: np.ndarray) -> tuple[float, int]:
    """Per-sample: nearest reference pixel at each direction. Kept as resampling_floor."""
    h, w = ref.shape[:2]
    p = to_equirect_px(d, w, h)
    x = np.clip(np.floor(p[:, 0]).astype(int) % w, 0, w - 1)
    y = np.clip(np.floor(p[:, 1]).astype(int), 0, h - 1)
    r = ref[y, x, :3].mean(-1)
    v = value.mean(-1)
    rel = np.abs(v - r) / np.maximum(r, 1e-3)
    return float(np.median(rel)), int(len(rel))


def alignment_floor(d: np.ndarray, ref: np.ndarray) -> float:
    """Per-sample: the reference against itself half a pixel away at these directions."""
    h, w = ref.shape[:2]
    p = to_equirect_px(d, w, h)
    x = np.floor(p[:, 0]).astype(int) % w; y = np.clip(np.floor(p[:, 1]).astype(int), 0, h - 1)
    xs = np.floor(p[:, 0] + 0.5).astype(int) % w; ys = np.clip(np.floor(p[:, 1] + 0.5).astype(int), 0, h - 1)
    r0, r1 = ref[y, x, :3].mean(-1), ref[ys, xs, :3].mean(-1)
    return float(np.median(np.abs(r0 - r1) / np.maximum(r0, 1e-3)))


def equirect_directions(h: int, w: int) -> np.ndarray:
    """EYE-frame unit direction of every reference pixel centre, (h, w, 3) float32."""
    v, u = np.mgrid[0:h, 0:w]
    lon = ((u + 0.5) / w - 0.5) * 2 * np.pi
    lat = (0.5 - (v + 0.5) / h) * np.pi
    return np.stack([np.sin(lon) * np.cos(lat), np.sin(lat), -np.cos(lon) * np.cos(lat)], -1).astype(np.float32)


class Fovea:
    """Cells of --cell-deg on the sphere around a gaze: gnomonic (tangent-plane) coordinates in
    the fixation's own right/up/forward frame, which within 2 deg are angles to 0.04%."""

    def __init__(self, fwd: np.ndarray, up_hint: np.ndarray, fovea_deg: float, cell_deg: float):
        self.fwd = fwd / np.linalg.norm(fwd)
        right = np.cross(self.fwd, up_hint); right /= np.linalg.norm(right)
        self.right, self.up = right, np.cross(right, self.fwd)
        self.fovea_deg, self.cell_deg = fovea_deg, cell_deg
        self.ncell = int(math.ceil(2 * fovea_deg / cell_deg))

    def cells(self, d: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """(cell index or -1, eccentricity deg) for directions d."""
        f = d @ self.fwd
        ecc = np.degrees(np.arccos(np.clip(f, -1.0, 1.0)))
        ok = (ecc <= self.fovea_deg) & (f > 0)
        gx = np.degrees((d @ self.right) / np.maximum(f, 1e-9)) + self.fovea_deg
        gy = np.degrees((d @ self.up) / np.maximum(f, 1e-9)) + self.fovea_deg
        ix = np.clip(np.floor(gx / self.cell_deg).astype(int), 0, self.ncell - 1)
        iy = np.clip(np.floor(gy / self.cell_deg).astype(int), 0, self.ncell - 1)
        idx = np.where(ok, iy * self.ncell + ix, -1)
        return idx, ecc

    def bin_mean(self, d: np.ndarray, values: np.ndarray, weights: np.ndarray) -> np.ndarray:
        """Weighted mean of values (N,) per cell; NaN where a cell has no weight."""
        idx, _ = self.cells(d)
        m = idx >= 0
        n = self.ncell ** 2
        wsum = np.bincount(idx[m], weights=weights[m], minlength=n)
        vsum = np.bincount(idx[m], weights=weights[m] * values[m], minlength=n)
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where(wsum > 0, vsum / wsum, np.nan)


def binned_rel_median(a: np.ndarray, b: np.ndarray) -> tuple[float, int]:
    """Median over cells present in both of |a - b| / b."""
    m = np.isfinite(a) & np.isfinite(b)
    if not m.any():
        return float("nan"), 0
    rel = np.abs(a[m] - b[m]) / np.maximum(b[m], 1e-3)
    return float(np.median(rel)), int(m.sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sequence")
    ap.add_argument("--reference", required=True, help="preview360 folder of the same scene and profile")
    ap.add_argument("--fovea-deg", type=float, default=2.0)
    ap.add_argument("--cell-deg", type=float, default=0.5)
    ap.add_argument("--bound-factor", type=float, default=1.5)
    ap.add_argument("--ref-noise-ratio", type=float, default=0.25, help="reference noise as a fraction of the fixation's (D7)")
    ap.add_argument("--control-yaw", type=float, default=90.0)
    ap.add_argument("--px-tol", type=float, default=1.0, help="reference pixels, on the p99.9")
    ap.add_argument("--cap-tol", type=float, default=0.01)
    ap.add_argument("--plain", default=None,
                    help="which fixations (b) is judged on: 'kind=wire' (targets of that kind in sequence.json) or "
                         "'floor=0.03' (binned alignment floor below this). The rest are reported, labelled "
                         "registration-limited, and never fail. Default: all fixations are judged.")
    args = ap.parse_args()

    seq = json.load(open(os.path.join(args.sequence, "sequence.json")))
    ref_meta = json.load(open(os.path.join(args.reference, "meta.json")))
    ref = find(read_exr(os.path.join(args.reference, "pano.exr")), "Combined")[..., :3].astype(np.float32)
    H, W = ref.shape[:2]
    ref_dir = equirect_directions(H, W)
    ref_mean = ref.mean(-1)
    lat_w = np.cos((0.5 - (np.arange(H) + 0.5) / H) * np.pi).astype(np.float32)  # pixel solid angle ~ cos(lat)
    # the reference shifted half a pixel: same values, directions of the centres + (0.5, 0.5) px
    v_, u_ = np.mgrid[0:H, 0:W]
    lon_s = ((u_ + 1.0) / W - 0.5) * 2 * np.pi; lat_s = (0.5 - (v_ + 1.0) / H) * np.pi
    ref_dir_shift = np.stack([np.sin(lon_s) * np.cos(lat_s), np.sin(lat_s), -np.cos(lon_s) * np.cos(lat_s)], -1).astype(np.float32)
    R_eye = eye_rotation(ref_meta["eye"])
    eye_pos = np.array(ref_meta["eye"]["position_m"], float)
    emax = seq["warp"]["e_max_deg"]
    cap = 2 * math.pi * (1 - math.cos(math.radians(emax)))
    fails, per = [], []
    if not seq.get("seed_pair", False):
        fails.append("sequence has no seed pair (run fixation_sequence.py with --seed-pair); (b) bound cannot be measured")

    for f in seq["fixations"]:
        fdir = os.path.join(args.sequence, f"f{f['id']:03d}")
        s = np.load(os.path.join(fdir, "samples.npz"))
        meta = json.load(open(os.path.join(fdir, "meta.json")))
        ch = read_exr(os.path.join(fdir, "fix.exr"))
        comb, z = find(ch, "Combined"), find(ch, "Depth.Z")
        pos = np.stack([find(ch, f"Position.{a}") for a in "XYZ"], -1)
        z = z[..., 0] if z.ndim == 3 else z
        ri = s["raster_index"]; rows, cols = ri[:, 0], ri[:, 1]
        d = s["direction"].astype(np.float64)
        rec = {"id": f["id"], "name": f["name"], "samples": int(len(d))}

        rec["reader_max_abs_diff"] = float(max(np.abs(s["value"] - comb[rows, cols, :3]).max(),
                                               np.abs(s["distance"] - z[rows, cols]).max()))
        if rec["reader_max_abs_diff"] != 0.0:
            fails.append(f"f{f['id']:03d}: samples.npz differs from fix.exr by {rec['reader_max_abs_diff']:.3e}")
        if not np.allclose(s["origin"], eye_pos, atol=1e-5):
            fails.append(f"f{f['id']:03d}: origin {s['origin']} is not the eye position {eye_pos}")

        # (a) analytic direction vs Position pass, in reference pixels
        hit = s["distance"] < 1e9
        dw = pos[rows, cols] - eye_pos
        dp = (dw / np.maximum(np.linalg.norm(dw, axis=-1, keepdims=True), 1e-12)) @ R_eye
        pa, pb = to_equirect_px(d[hit], W, H), to_equirect_px(dp[hit], W, H)
        dx = np.abs(pa[:, 0] - pb[:, 0]); dx = np.minimum(dx, W - dx)
        dist = np.hypot(dx, pa[:, 1] - pb[:, 1])
        rec["warp_px_p999"] = float(np.percentile(dist, 99.9)); rec["warp_px_max"] = float(dist.max())
        rec["hits"] = int(hit.sum())
        if not (rec["warp_px_p999"] <= args.px_tol):
            fails.append(f"f{f['id']:03d}: (a) directions off the Position pass by {rec['warp_px_p999']:.2f} px at p99.9")

        # (b) binned foveal agreement with a per-fixation measured bound; (c) the rotated control
        fwd_eye = R_eye.T @ np.array(meta["camera_forward"], float)
        up_eye = R_eye.T @ np.array(meta["camera_up"], float)
        val = s["value"].mean(-1).astype(np.float64); fp = s["footprint"].astype(np.float64)
        have_b = os.path.exists(os.path.join(fdir, "samples_b.npz"))
        val_b = np.load(os.path.join(fdir, "samples_b.npz"))["value"].mean(-1).astype(np.float64) if have_b else None

        def fovea_stats(rot: np.ndarray | None) -> dict:
            dd = d if rot is None else d @ rot.T
            fw = fwd_eye if rot is None else rot @ fwd_eye
            upv = up_eye if rot is None else rot @ up_eye
            fov = Fovea(fw, upv, args.fovea_deg, args.cell_deg)
            near = (ref_dir.reshape(-1, 3) @ fw.astype(np.float32)) > math.cos(math.radians(args.fovea_deg * 1.5))
            rd, rv, rw = ref_dir.reshape(-1, 3)[near], ref_mean.reshape(-1)[near], np.repeat(lat_w, W)[near]
            r_cell = fov.bin_mean(rd, rv, rw)
            f_cell = fov.bin_mean(dd[hit], val[hit], fp[hit])
            out = {}
            out["binned_rel_median"], out["cells"] = binned_rel_median(f_cell, r_cell)
            rs_ = ref_dir_shift.reshape(-1, 3)[near]
            s_cell = fov.bin_mean(rs_, rv, rw)
            out["align_floor_binned"], _ = binned_rel_median(s_cell, r_cell)
            if val_b is not None:
                b_cell = fov.bin_mean(dd[hit], val_b[hit], fp[hit])
                m = np.isfinite(f_cell) & np.isfinite(b_cell) & np.isfinite(r_cell)
                pair = np.abs(f_cell[m] - b_cell[m]) / np.maximum(r_cell[m], 1e-3)
                out["noise_fix"] = float(np.median(pair)) / math.sqrt(2.0)
                nf, fl = out["noise_fix"], out["align_floor_binned"]
                # D10: the bound carries this fixation's own binned alignment floor in quadrature
                out["bound"] = args.bound_factor * math.sqrt(nf ** 2 + (args.ref_noise_ratio * nf) ** 2 + fl ** 2)
            # the per-sample statistics, kept as the resampling floor
            ecc = np.degrees(np.arccos(np.clip(dd @ fw, -1.0, 1.0)))
            fs = (ecc <= args.fovea_deg) & hit
            out["resampling_floor"], out["fovea_samples"] = rel_diff_median(s["value"][fs], dd[fs], ref)
            out["align_floor_per_sample"] = alignment_floor(dd[fs], ref)
            return out

        fb = fovea_stats(None)
        rec.update({"fovea_binned_rel_median": fb["binned_rel_median"], "fovea_cells": fb["cells"],
                    "noise_fix_binned": fb.get("noise_fix"), "bound": fb.get("bound"),
                    "align_floor_binned": fb["align_floor_binned"],
                    "resampling_floor": fb["resampling_floor"], "align_floor_per_sample": fb["align_floor_per_sample"],
                    "fovea_samples": fb["fovea_samples"]})
        fc = fovea_stats(rot_y(args.control_yaw))
        rec["control_binned_rel_median"] = fc["binned_rel_median"]
        rec["control_resampling"] = fc["resampling_floor"]
        kind = seq["gazes"][f["id"]].get("kind") if f["id"] < len(seq.get("gazes", [])) else None
        if args.plain is None:
            plain = True
        elif args.plain.startswith("kind="):
            plain = kind == args.plain[5:]
        elif args.plain.startswith("floor="):
            plain = rec["align_floor_binned"] < float(args.plain[6:])
        else:
            raise SystemExit(f"--plain must be kind=<kind> or floor=<value>, got {args.plain!r}")
        rec["kind"] = kind
        rec["b_judged"] = bool(plain)
        rec["b_label"] = "plain" if plain else "registration-limited"
        if rec["bound"] is None:
            fails.append(f"f{f['id']:03d}: no seed pair, (b) has no bound")
        else:
            if plain and not (rec["fovea_binned_rel_median"] < rec["bound"]):
                fails.append(f"f{f['id']:03d}: (b) binned foveal median {rec['fovea_binned_rel_median']:.4f} >= bound {rec['bound']:.4f}")
            if not (rec["control_binned_rel_median"] >= rec["bound"]):
                fails.append(f"f{f['id']:03d}: (c) control at {args.control_yaw} deg yaw still passes "
                             f"({rec['control_binned_rel_median']:.4f} < {rec['bound']:.4f})")

        # (d) footprints sum to the cap
        rec["footprint_sum_sr"] = float(fp.sum())
        rec["cap_rel_err"] = (rec["footprint_sum_sr"] - cap) / cap
        if not (abs(rec["cap_rel_err"]) <= args.cap_tol):
            fails.append(f"f{f['id']:03d}: (d) footprints sum to {rec['footprint_sum_sr']:.4f} sr vs cap {cap:.4f}")
        per.append(rec)

    def agg(key):
        v = np.array([r[key] for r in per if r.get(key) is not None], float)
        if not len(v):
            return None
        return {"median": float(np.median(v)), "min": float(v.min()), "max": float(v.max())}

    report = {
        "sequence": args.sequence, "reference": args.reference, "fixations": len(per),
        "fovea_deg": args.fovea_deg, "cell_deg": args.cell_deg,
        "bound_how": f"{args.bound_factor} * sqrt(noise_fix^2 + ({args.ref_noise_ratio} noise_fix)^2 + floor_binned^2), noise_fix = binned "
                     f"median |seed0 - seed1| / ref / sqrt(2), floor_binned = reference vs its half-pixel shift binned, per fixation (D10)",
        "cap_sr": cap, "px_tol": args.px_tol,
        "warp_px_p999": agg("warp_px_p999"), "warp_px_max": agg("warp_px_max"),
        "fovea_binned_rel_median": agg("fovea_binned_rel_median"), "bound": agg("bound"),
        "noise_fix_binned": agg("noise_fix_binned"), "align_floor_binned": agg("align_floor_binned"),
        "control_binned_rel_median": agg("control_binned_rel_median"),
        "resampling_floor": agg("resampling_floor"), "align_floor_per_sample": agg("align_floor_per_sample"),
        "fovea_cells": agg("fovea_cells"), "fovea_samples": agg("fovea_samples"),
        "fovea_pass_count": int(sum(r["bound"] is not None and r["fovea_binned_rel_median"] < r["bound"] for r in per)),
        "plain_rule": args.plain, "plain_count": int(sum(r["b_judged"] for r in per)),
        "plain_pass_count": int(sum(r["b_judged"] and r["bound"] is not None and r["fovea_binned_rel_median"] < r["bound"] for r in per)),
        "registration_limited_count": int(sum(not r["b_judged"] for r in per)),
        "registration_limited_pass_count": int(sum((not r["b_judged"]) and r["bound"] is not None and r["fovea_binned_rel_median"] < r["bound"] for r in per)),
        "control_fail_count": int(sum(r["bound"] is not None and r["control_binned_rel_median"] >= r["bound"] for r in per)),
        "cap_rel_err": agg("cap_rel_err"), "reader_max_abs_diff": agg("reader_max_abs_diff"),
        "per_fixation": per, "checks_failed": fails,
    }
    with open(os.path.join(args.sequence, "check.json"), "w") as fh:
        json.dump(report, fh, indent=1)
    print(json.dumps({k: v for k, v in report.items() if k != "per_fixation"}, indent=1))
    raise SystemExit(1 if fails else 0)


if __name__ == "__main__":
    main()
