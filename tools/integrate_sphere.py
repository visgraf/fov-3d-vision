"""A5: integrate a fixation sequence into a sphere and measure error against budget. Host side.

    .venv/bin/python tools/integrate_sphere.py previews/sequence/calib_room \
        --reference previews/reference_small/calib_room --out previews/integrated/calib_room \
        --k-list 1,2,5,10,20,50 --uniform previews/uniform/calib_room --bound 0.0263

Accumulation: every sample (D1 record, samples.npz) splats its value over the equirect cells
whose centres lie inside a disc of angular radius sqrt(footprint/pi) around its direction,
with weight 1/footprint, so where fixations overlap the finer samples dominate. The grid is
the profile's reference resolution. Written to --out:
    integrated.npz   rgb (H,W,3), weight (H,W), min_footprint (H,W) sr (inf = uncovered),
                     fixation_count (H,W); for the last K in --k-list
    rgb.png, min_footprint.png   for looking at (uncovered = black)
    curve.json, curve.csv        per K: error bands, coverage, budget, seconds; the uniform
                                 baselines at the same budgets; the four checks

Error (D8): footprint-aware. Each covered cell is compared with the reference box-filtered
over an angular square of side sqrt(min_footprint) centred on the weighted centroid of the
samples that reached the cell (for a uniform render, over its own pixel), so error is
measured at the resolution the sampling provides there and where the samples actually are.
The same box centred on the cell centre is reported as rel_rms_cell_centre: it is
registration-limited (a cell's value comes from a sample up to sqrt(fp/pi) away), which on
high-contrast texture dominates everything else (measured 2026-09-13).
Relative RMS over a set of cells = RMS(value - ref) / mean(ref), solid-angle weighted, on the
mean over RGB, the A2 convention. Bands are by eccentricity from the nearest fixation centre
among the K used; "targets" are cells within --target-deg of every gaze of the full sequence.

Checks that can fail (exit 1):
  (1) identity     the reference's own pixels fed in as samples (footprint = pixel solid
                   angle) reproduce the reference to 1e-6 over |lat| <= --identity-lat. Above
                   that the area-equivalent disc of a pixel spans its longitude neighbours
                   (cos lat < 0.318) and the check cannot hold by construction; the polar
                   deviation is reported, not judged.
  (2) targets      at the largest K, relative RMS at the targets is below --bound (the median
                   of check_sequence's measured (b) bounds)
  (3) control      integrating with every gaze yawed --control-yaw deg gives target error at
                   least --control-factor times the largest-K value
  (4) mass         the rasterised discs carry the footprint they represent: sum over cells of
                   cell solid angle x (samples covering it) equals the sum of footprints to 1%
                   (overlap between fixations and between neighbouring discs is reported as the
                   ratio of the covered solid angle to that sum)
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os

import numpy as np
import OpenEXR


# ----------------------------------------------------------------------------------------
# geometry
# ----------------------------------------------------------------------------------------

def read_combined(path: str) -> np.ndarray:
    with OpenEXR.File(path) as f:
        for part in f.parts:
            for name, ch in part.channels.items():
                if name.endswith("Combined"):
                    return np.asarray(ch.pixels)[..., :3].astype(np.float64)
    raise KeyError("no Combined channel")


def lonlat_of(d: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return np.arctan2(d[:, 0], -d[:, 2]), np.arcsin(np.clip(d[:, 1], -1.0, 1.0))


def dir_of(lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    return np.stack([np.sin(lon) * np.cos(lat), np.sin(lat), -np.cos(lon) * np.cos(lat)], -1)


def grid_lonlat(H: int, W: int, rows: np.ndarray, cols: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return ((cols + 0.5) / W - 0.5) * 2 * np.pi, (0.5 - (rows + 0.5) / H) * np.pi


def cell_solid_angle(H: int, W: int, rows: np.ndarray) -> np.ndarray:
    lat = (0.5 - (rows + 0.5) / H) * np.pi
    return (2 * np.pi / W) * (np.pi / H) * np.cos(lat)


def rot_y(deg: float) -> np.ndarray:
    a = math.radians(deg)
    return np.array([[math.cos(a), 0.0, math.sin(a)], [0.0, 1.0, 0.0], [-math.sin(a), 0.0, math.cos(a)]])


def eye_rotation(eye: dict) -> np.ndarray:
    fwd, up = np.array(eye["forward"], float), np.array(eye["up"], float)
    right = np.cross(fwd, up)
    return np.stack([right, up, -fwd], axis=1)


# ----------------------------------------------------------------------------------------
# accumulation
# ----------------------------------------------------------------------------------------

class Sphere:
    def __init__(self, H: int, W: int):
        self.H, self.W = H, W
        n = H * W
        self.rgb_sum = np.zeros((n, 3))
        self.dir_sum = np.zeros((n, 3))     # weighted sum of sample directions: the centroid
        self.weight = np.zeros(n)
        self.min_fp = np.full(n, np.inf)
        self.count = np.zeros(n, dtype=np.int64)
        self.fix_count = np.zeros(n, dtype=np.int32)
        self.footprint_in = 0.0      # sum of footprints fed in
        self.samples_in = 0
        self.ref_min_fp = None       # set to a min-footprint map to measure the coarse share
        self.coarse_w = np.zeros(n)  # weight from samples coarser than finest_factor x that map

    def candidates(self, d: np.ndarray, fp: np.ndarray):
        """Flat cell indices inside each sample's disc, with the sample index they belong to."""
        H, W = self.H, self.W
        rho = np.sqrt(fp / np.pi)
        lon, lat = lonlat_of(d)
        cx = (lon / (2 * np.pi) + 0.5) * W - 0.5
        cy = (0.5 - lat / np.pi) * H - 0.5
        hy = np.ceil(rho / (np.pi / H)).astype(int)
        edge = np.minimum(np.abs(lat) + rho, np.pi / 2)
        hx = np.minimum(np.ceil(rho / ((2 * np.pi / W) * np.maximum(np.cos(edge), 1e-9))).astype(int), W // 2)
        cos_rho = np.cos(rho)
        out_idx, out_s = [], []
        keys = hx * 10000 + hy
        for key in np.unique(keys):
            sel = np.nonzero(keys == key)[0]
            kx, ky = int(key // 10000), int(key % 10000)
            ox, oy = np.meshgrid(np.arange(-kx, kx + 1), np.arange(-ky, ky + 1))
            ox, oy = ox.ravel(), oy.ravel()
            step = max(1, 4_000_000 // max(len(ox), 1))
            for a in range(0, len(sel), step):
                s = sel[a:a + step]
                rows = np.rint(cy[s])[:, None].astype(int) + oy[None, :]
                cols = (np.rint(cx[s])[:, None].astype(int) + ox[None, :]) % W
                ok = (rows >= 0) & (rows < H)
                lon_c, lat_c = grid_lonlat(H, W, rows, cols)
                dc = dir_of(lon_c.ravel(), lat_c.ravel()).reshape(rows.shape + (3,))
                inside = ok & ((dc * d[s][:, None, :]).sum(-1) >= cos_rho[s][:, None])
                si, ci = np.nonzero(inside)
                out_idx.append(rows[si, ci] * W + cols[si, ci])
                out_s.append(s[si])
        return np.concatenate(out_idx), np.concatenate(out_s)

    def add(self, d: np.ndarray, v: np.ndarray, fp: np.ndarray, weight_power: float = 1.0,
            finest_only: np.ndarray | None = None, finest_factor: float = 2.0) -> None:
        """Splat one fixation. weight = 1/fp**weight_power (1 is the A5 rule). finest_only: a
        precomputed per-cell minimum footprint; when given, a sample only contributes to cells
        whose minimum is within finest_factor of its own footprint (diagnostic variant)."""
        n = self.H * self.W
        idx, s = self.candidates(d, fp)
        if finest_only is not None:
            keep = fp[s] <= finest_factor * finest_only[idx]
            idx, s = idx[keep], s[keep]
        w = 1.0 / fp[s] ** weight_power
        self.coarse_w += np.bincount(idx, weights=np.where(fp[s] > finest_factor * self.ref_min_fp[idx], w, 0.0), minlength=n) \
            if self.ref_min_fp is not None else 0.0
        self.weight += np.bincount(idx, weights=w, minlength=n)
        for c in range(3):
            self.rgb_sum[:, c] += np.bincount(idx, weights=w * v[s, c], minlength=n)
            self.dir_sum[:, c] += np.bincount(idx, weights=w * d[s, c], minlength=n)
        self.count += np.bincount(idx, minlength=n)
        order = np.argsort(fp[s], kind="stable")
        u, first = np.unique(idx[order], return_index=True)
        self.min_fp[u] = np.minimum(self.min_fp[u], fp[s][order][first])
        touched = np.zeros(n, dtype=bool); touched[idx] = True
        self.fix_count += touched
        self.footprint_in += float(fp.sum()); self.samples_in += int(len(fp))

    def centroid(self) -> np.ndarray:
        """Unit direction of the weighted centroid of the samples that reached each cell."""
        with np.errstate(invalid="ignore", divide="ignore"):
            c = self.dir_sum / np.maximum(np.linalg.norm(self.dir_sum, axis=-1, keepdims=True), 1e-300)
        return c

    def rgb(self) -> np.ndarray:
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where(self.weight[:, None] > 0, self.rgb_sum / self.weight[:, None], 0.0)


# ----------------------------------------------------------------------------------------
# error metric
# ----------------------------------------------------------------------------------------

class RefBox:
    """Box means of the reference over lon-lat rectangles, via an integral image on a
    horizontally tripled copy so boxes may cross the seam."""

    def __init__(self, ref: np.ndarray):
        self.H, self.W = ref.shape[:2]
        m = ref.mean(-1)
        t = np.concatenate([m, m, m], axis=1)
        self.I = np.pad(t, ((1, 0), (1, 0))).cumsum(0).cumsum(1)

    def mean(self, cx: np.ndarray, cy: np.ndarray, hx: np.ndarray, hy: np.ndarray) -> np.ndarray:
        """cx, cy continuous pixel coordinates of the centre (pixel k spans [k, k+1)); hx, hy
        half-widths in pixels. Boundaries rounded to the nearest pixel edge, at least one pixel."""
        W, H = self.W, self.H
        x0 = np.rint(cx - hx).astype(int); x1 = np.maximum(np.rint(cx + hx).astype(int), x0 + 1)
        y0 = np.clip(np.rint(cy - hy).astype(int), 0, H - 1); y1 = np.clip(np.maximum(np.rint(cy + hy).astype(int), y0 + 1), 1, H)
        x0 = x0 + W; x1 = x1 + W                              # into the middle copy
        x0 = np.clip(x0, 0, 3 * W - 1); x1 = np.clip(x1, 1, 3 * W)
        s = self.I[y1, x1] - self.I[y0, x1] - self.I[y1, x0] + self.I[y0, x0]
        return s / ((x1 - x0) * (y1 - y0))


def nearest_gaze_deg(d: np.ndarray, gazes: np.ndarray) -> np.ndarray:
    best = np.full(len(d), -1.0)
    for g in gazes:
        best = np.maximum(best, d @ g)
    return np.degrees(np.arccos(np.clip(best, -1.0, 1.0)))


BANDS = [(0, 2), (2, 5), (5, 10), (10, 20), (20, 45)]


def error_report(value: np.ndarray, ref_box: np.ndarray, omega: np.ndarray, ecc: np.ndarray,
                 near_target: np.ndarray, ref_box_cell: np.ndarray | None = None) -> dict:
    """value, ref_box: mean-over-RGB per cell, the reference box-filtered around the cell's
    sample centroid; ref_box_cell: the same box around the cell centre (reported as the
    registration-limited alternative); omega: cell solid angle; ecc: deg to the nearest
    fixation centre; near_target: within --target-deg of a target."""
    def rel_rms(m):
        if not m.any():
            return None
        w = omega[m]; e = value[m] - ref_box[m]; r = ref_box[m]
        out = {"rel_rms": float(math.sqrt((w * e * e).sum() / w.sum()) / ((w * r).sum() / w.sum())),
               "rel_median": float(np.median(np.abs(e) / np.maximum(r, 1e-3))),
               "cells": int(m.sum()), "solid_angle_sr": float(w.sum())}
        if ref_box_cell is not None:
            ec = value[m] - ref_box_cell[m]; rc = ref_box_cell[m]
            out["rel_rms_cell_centre"] = float(math.sqrt((w * ec * ec).sum() / w.sum()) / ((w * rc).sum() / w.sum()))
        return out
    out = {"all": rel_rms(np.ones(len(value), bool)), "targets_1deg": rel_rms(near_target)}
    for lo, hi in BANDS:
        out[f"band_{lo}_{hi}"] = rel_rms((ecc >= lo) & (ecc < hi))
    return out


def evaluate_sphere(sp: Sphere, refbox: RefBox, gazes_k: np.ndarray, targets: np.ndarray, target_deg: float) -> dict:
    H, W = sp.H, sp.W
    covered = np.nonzero(sp.weight > 0)[0]
    rows, cols = covered // W, covered % W
    lon, lat = grid_lonlat(H, W, rows, cols)
    d = dir_of(lon, lat)
    fp = sp.min_fp[covered]
    side = np.sqrt(fp)
    # the reference box sits where the cell's samples are (their weighted centroid), at the
    # cell's finest footprint; the cell-centre box is kept for comparison. A cell's value is
    # an estimate at that centroid, up to sqrt(fp/pi) away from the cell centre.
    cen = sp.centroid()[covered]
    lon_c, lat_c = lonlat_of(cen)
    ccx = (lon_c / (2 * np.pi) + 0.5) * W; ccy = (0.5 - lat_c / np.pi) * H
    hx = side / 2 / ((2 * np.pi / W) * np.maximum(np.cos(lat_c), 1e-9)); hy = side / 2 / (np.pi / H)
    rb = refbox.mean(ccx, ccy, hx, hy)
    hx0 = side / 2 / ((2 * np.pi / W) * np.maximum(np.cos(lat), 1e-9))
    rb_cell = refbox.mean(cols + 0.5, rows + 0.5, hx0, hy)
    val = sp.rgb()[covered].mean(-1)
    omega = cell_solid_angle(H, W, rows)
    ecc = nearest_gaze_deg(d, gazes_k)
    near_t = nearest_gaze_deg(d, targets) <= target_deg
    rep = error_report(val, rb, omega, ecc, near_t, rb_cell)
    off = np.degrees(np.arccos(np.clip((cen * d).sum(-1), -1, 1)))
    rep["centroid_offset_deg"] = {"median": float(np.median(off)), "p99": float(np.percentile(off, 99))}
    if sp.ref_min_fp is not None:
        share = sp.coarse_w[covered] / sp.weight[covered]
        rep["coarse_weight_share"] = {"targets_median": float(np.median(share[near_t])) if near_t.any() else None,
                                      "all_median": float(np.median(share)),
                                      "how": "weight from samples with footprint > 2x the cell's minimum, over total weight"}
    # like-for-like with check_sequence's (b) bound: bin covered target cells into 0.5 deg cells
    # (equirect blocks of 0.5 deg) and compare the solid-angle means of value and reference box
    if near_t.any():
        bsz = max(1, int(round(0.5 / (360.0 / W))))
        key = (rows[near_t] // bsz) * (W // bsz + 1) + cols[near_t] // bsz
        u, inv = np.unique(key, return_inverse=True)
        wsum = np.bincount(inv, weights=omega[near_t]); vb = np.bincount(inv, weights=omega[near_t] * val[near_t]) / wsum
        rbb = np.bincount(inv, weights=omega[near_t] * rb[near_t]) / wsum
        e = vb - rbb
        rep["targets_binned_0.5deg"] = {"rel_rms": float(math.sqrt((wsum * e * e).sum() / wsum.sum()) / ((wsum * rbb).sum() / wsum.sum())),
                                        "rel_median": float(np.median(np.abs(e) / np.maximum(rbb, 1e-3))), "cells": int(len(u))}
    all_omega = cell_solid_angle(H, W, np.repeat(np.arange(H), W)).sum()
    rep["coverage_solid_angle_frac"] = float(omega.sum() / all_omega)
    rep["coverage_cell_frac"] = float(len(covered) / (H * W))
    t_all = nearest_gaze_deg(dir_of(*grid_lonlat(H, W, *np.divmod(np.arange(H * W), W))), targets) <= target_deg
    rep["target_cells_covered_frac"] = float(near_t.sum() / max(t_all.sum(), 1))
    # (4) mass: rasterised disc area vs footprints fed in
    disc_area = float((sp.count * cell_solid_angle(H, W, np.repeat(np.arange(H), W))).sum())
    rep["mass"] = {"footprint_in_sr": sp.footprint_in, "rasterised_sr": disc_area,
                   "rel_err": (disc_area - sp.footprint_in) / sp.footprint_in,
                   "covered_over_footprint_in": float(omega.sum() / sp.footprint_in)}
    return rep


def evaluate_uniform(folder: str, refbox: RefBox, gazes_k: np.ndarray, targets: np.ndarray, target_deg: float) -> dict:
    meta = json.load(open(os.path.join(folder, "meta.json")))
    img = read_combined(os.path.join(folder, "pano.exr"))
    Hu, Wu = img.shape[:2]
    rows, cols = np.divmod(np.arange(Hu * Wu), Wu)
    lon, lat = grid_lonlat(Hu, Wu, rows, cols)
    d = dir_of(lon, lat)
    H, W = refbox.H, refbox.W
    cx = (cols + 0.5) * W / Wu; cy = (rows + 0.5) * H / Hu
    hx = np.full(len(cx), 0.5 * W / Wu); hy = np.full(len(cy), 0.5 * H / Hu)
    rb = refbox.mean(cx, cy, hx, hy)
    val = img.reshape(-1, 3).mean(-1)
    omega = cell_solid_angle(Hu, Wu, rows)
    rep = error_report(val, rb, omega, nearest_gaze_deg(d, gazes_k), nearest_gaze_deg(d, targets) <= target_deg)
    rep.update({"width": Wu, "spp": meta["spp"], "rays": Hu * Wu * meta["spp"],
                "render_seconds": meta["render_seconds"], "render_seconds_includes_write": True,
                "pixel_deg": 360.0 / Wu})
    return rep


def identity_check(ref: np.ndarray, identity_lat: float) -> dict:
    H, W = ref.shape[:2]
    sp = Sphere(H, W)
    rows, cols = np.divmod(np.arange(H * W), W)
    lon, lat = grid_lonlat(H, W, rows, cols)
    d = dir_of(lon, lat); fp = cell_solid_angle(H, W, rows); v = ref.reshape(-1, 3)
    for a in range(0, H * W, 400_000):          # chunked: the polar rows spawn wide boxes
        sl = slice(a, a + 400_000)
        sp.add(d[sl], v[sl], fp[sl])
    out = sp.rgb()
    err = np.abs(out - v).max(-1)
    band = np.abs(np.degrees(lat)) <= identity_lat
    per_lat = {}
    for lo in range(0, 90, 10):
        m = (np.abs(np.degrees(lat)) >= lo) & (np.abs(np.degrees(lat)) < lo + 10)
        per_lat[f"{lo}_{lo + 10}"] = float(err[m].max())
    return {"max_abs_err_within_band": float(err[band].max()), "identity_lat": identity_lat,
            "uncovered_within_band": int((sp.weight[band] == 0).sum()),
            "max_abs_err_by_lat_band": per_lat, "cells": int(H * W)}


def write_pngs(sp: Sphere, out: str) -> None:
    from PIL import Image
    H, W = sp.H, sp.W
    rgb = np.clip(sp.rgb().reshape(H, W, 3), 0, 1) ** (1 / 2.2)
    Image.fromarray((rgb * 255).astype(np.uint8)).save(os.path.join(out, "rgb.png"))
    fp = sp.min_fp.reshape(H, W)
    lo, hi = -6.0, -3.0
    g = np.where(np.isfinite(fp), np.clip((np.log10(np.maximum(fp, 1e-12)) - lo) / (hi - lo), 0, 1), 0.0)
    Image.fromarray(((1 - g) * 255).astype(np.uint8)).save(os.path.join(out, "min_footprint.png"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sequence")
    ap.add_argument("--reference", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--k-list", default="1,2,5,10,20,50")
    ap.add_argument("--uniform", help="folder holding preview360 renders w<W>/ at equal budgets")
    ap.add_argument("--bound", type=float, required=True, help="median of check_sequence's measured (b) bounds")
    ap.add_argument("--target-deg", type=float, default=1.0)
    ap.add_argument("--control-yaw", type=float, default=90.0)
    ap.add_argument("--control-factor", type=float, default=5.0)
    ap.add_argument("--identity-lat", type=float, default=60.0)
    ap.add_argument("--skip-identity", action="store_true")
    ap.add_argument("--weight-power", type=float, default=1.0, help="weight = 1/footprint**p; 1 is the A5 rule")
    ap.add_argument("--finest-only", action="store_true",
                    help="diagnostic: a sample contributes only to cells whose finest footprint is within "
                         "--finest-factor of its own (two passes)")
    ap.add_argument("--finest-factor", type=float, default=2.0)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    seq = json.load(open(os.path.join(args.sequence, "sequence.json")))
    ref_meta = json.load(open(os.path.join(args.reference, "meta.json")))
    ref = read_combined(os.path.join(args.reference, "pano.exr"))
    H, W = ref.shape[:2]
    refbox = RefBox(ref)
    R_eye = eye_rotation(ref_meta["eye"])
    fails = []

    fixations = seq["fixations"]
    gaze_dirs = []
    for f in fixations:
        m = json.load(open(os.path.join(args.sequence, f"f{f['id']:03d}", "meta.json")))
        gaze_dirs.append(R_eye.T @ np.array(m["camera_forward"], float))
    gaze_dirs = np.array(gaze_dirs)
    targets = gaze_dirs
    k_list = sorted({min(int(k), len(fixations)) for k in args.k_list.split(",")})

    checks = {}
    if not args.skip_identity:
        checks["identity"] = identity_check(ref, args.identity_lat)
        if not (checks["identity"]["max_abs_err_within_band"] <= 1e-6 and checks["identity"]["uncovered_within_band"] == 0):
            fails.append(f"(1) identity: max error {checks['identity']['max_abs_err_within_band']:.3e} within "
                         f"|lat| <= {args.identity_lat}, {checks['identity']['uncovered_within_band']} cells uncovered")
        print(f"[integrate] identity within |lat|<={args.identity_lat}: max err "
              f"{checks['identity']['max_abs_err_within_band']:.2e}; by band {checks['identity']['max_abs_err_by_lat_band']}", flush=True)

    def load(f, rot):
        s = np.load(os.path.join(args.sequence, f"f{f['id']:03d}", "samples.npz"))
        d = s["direction"].astype(np.float64)
        return (d if rot is None else d @ rot.T), s["value"].astype(np.float64), s["footprint"].astype(np.float64)

    def run(rot: np.ndarray | None, ks: list[int]) -> dict:
        sp = Sphere(H, W)
        out = {}
        rays = 0.0; secs = 0.0
        kmax_ = max(ks)
        # pass 0: the finest footprint per cell at K = max(ks), for the coarse-share diagnostic and
        # the finest-only variant (both are functions of the final map, so per-K numbers use it too)
        pre = Sphere(H, W)
        for k, f in enumerate(fixations, start=1):
            if k > kmax_:
                break
            pre.add(*load(f, rot))
        sp.ref_min_fp = pre.min_fp
        for k, f in enumerate(fixations, start=1):
            if k > kmax_:
                break
            d, v, fp = load(f, rot)
            sp.add(d, v, fp, weight_power=args.weight_power,
                   finest_only=pre.min_fp if args.finest_only else None, finest_factor=args.finest_factor)
            rays += f["samples"] * seq["spp"]; secs += f["render_seconds"]
            if k in ks:
                rep = evaluate_sphere(sp, refbox, gaze_dirs[:k] if rot is None else gaze_dirs[:k] @ rot.T, targets, args.target_deg)
                rep.update({"K": k, "rays": int(rays), "render_seconds": secs, "spp": seq["spp"],
                            "samples_per_fixation": seq["samples_per_fixation"]})
                out[k] = rep
                t = rep["targets_1deg"]
                print(f"[integrate] K={k:2d}: rays {int(rays):>10d}  {secs:6.3f}s  coverage {rep['coverage_solid_angle_frac']:.3f}  "
                      f"targets rel_rms {t['rel_rms'] if t else float('nan'):.4f} (cell-centre {t['rel_rms_cell_centre'] if t else float('nan'):.4f}, "
                      f"median {t['rel_median'] if t else float('nan'):.4f})  all {rep['all']['rel_rms']:.4f} (cc {rep['all']['rel_rms_cell_centre']:.4f})  "
                      f"mass err {rep['mass']['rel_err']:+.4f}  coarse share@targets "
                      f"{rep.get('coarse_weight_share', {}).get('targets_median', float('nan')):.3f}  "
                      f"targets binned0.5 {rep.get('targets_binned_0.5deg', {}).get('rel_rms', float('nan')):.4f}", flush=True)
        return out, sp

    curve, sp = run(None, k_list)
    write_pngs(sp, args.out)
    kmax = max(k_list)
    np.savez(os.path.join(args.out, "integrated.npz"), rgb=sp.rgb().reshape(H, W, 3).astype(np.float32),
             weight=sp.weight.reshape(H, W).astype(np.float32), min_footprint=sp.min_fp.reshape(H, W).astype(np.float32),
             fixation_count=sp.fix_count.reshape(H, W), K=kmax)

    t_err = curve[kmax]["targets_1deg"]["rel_rms"]
    checks["targets"] = {"K": kmax, "rel_rms": t_err, "bound": args.bound}
    if not (t_err < args.bound):
        fails.append(f"(2) targets: rel_rms {t_err:.4f} at K={kmax} is not below the bound {args.bound:.4f}")
    for k, rep in curve.items():
        if abs(rep["mass"]["rel_err"]) > 0.01:
            fails.append(f"(4) mass: K={k} rasterised {rep['mass']['rasterised_sr']:.4f} sr vs footprints {rep['mass']['footprint_in_sr']:.4f} sr")
    checks["mass"] = {k: rep["mass"] for k, rep in curve.items()}

    ctrl, _ = run(rot_y(args.control_yaw), [kmax])
    c_err = ctrl[kmax]["targets_1deg"]["rel_rms"] if ctrl[kmax]["targets_1deg"] else float("nan")
    checks["control"] = {"K": kmax, "yaw": args.control_yaw, "rel_rms": c_err, "ratio": c_err / t_err if t_err else None}
    if not (c_err >= args.control_factor * t_err):
        fails.append(f"(3) control: rotated target error {c_err:.4f} is not {args.control_factor}x the K={kmax} value {t_err:.4f}")

    uniform = {}
    if args.uniform:
        for k in k_list:
            B = k * seq["samples_per_fixation"] * seq["spp"]
            Wu = int(round(math.sqrt(2 * B / 64) / 2)) * 2
            folder = os.path.join(args.uniform, f"w{Wu}")
            if Wu < 64 or not os.path.isdir(folder):
                uniform[k] = {"width": Wu, "skipped": "W < 64" if Wu < 64 else f"missing {folder}"}
                continue
            uniform[k] = evaluate_uniform(folder, refbox, gaze_dirs[:k], targets, args.target_deg)
            uniform[k]["budget_ratio_to_foveated"] = uniform[k]["rays"] / B
            u = uniform[k]
            print(f"[integrate] uniform W={Wu:4d} for K={k:2d}: rays {u['rays']:>10d}  {u['render_seconds']:.2f}s  "
                  f"targets {u['targets_1deg']['rel_rms']:.4f}  all {u['all']['rel_rms']:.4f}", flush=True)

    result = {"sequence": args.sequence, "reference": args.reference, "grid": [W, H],
              "weight_rule": f"1/footprint^{args.weight_power}" + (f", finest-only x{args.finest_factor}" if args.finest_only else ""),
              "profile": seq.get("profile"), "spp": seq["spp"], "warmup_seconds_discarded": seq["warmup_seconds_discarded"],
              "metric": "footprint-aware relative RMS = RMS(value - ref box mean over sqrt(min_footprint) square) / mean(ref), "
                        "solid-angle weighted, mean over RGB; bands by eccentricity from the nearest of the K fixation centres",
              "curve": {str(k): v for k, v in curve.items()}, "uniform": {str(k): v for k, v in uniform.items()},
              "checks": checks, "checks_failed": fails}
    with open(os.path.join(args.out, "curve.json"), "w") as fh:
        json.dump(result, fh, indent=1)
    with open(os.path.join(args.out, "curve.csv"), "w", newline="") as fh:
        wr = csv.writer(fh)
        cols = ["K", "rays", "render_seconds", "coverage_solid_angle_frac", "targets_rel_rms", "all_rel_rms"] + \
               [f"band_{lo}_{hi}_rel_rms" for lo, hi in BANDS] + ["uniform_width", "uniform_rays", "uniform_seconds", "uniform_targets_rel_rms", "uniform_all_rel_rms"]
        wr.writerow(cols)
        for k in k_list:
            c = curve[k]; u = uniform.get(k, {})
            g = lambda rep, key: (rep[key]["rel_rms"] if rep.get(key) else "")
            wr.writerow([k, c["rays"], round(c["render_seconds"], 3), round(c["coverage_solid_angle_frac"], 4),
                         g(c, "targets_1deg"), g(c, "all")] + [g(c, f"band_{lo}_{hi}") for lo, hi in BANDS] +
                        [u.get("width", ""), u.get("rays", ""), u.get("render_seconds", ""), g(u, "targets_1deg") if "all" in u else "", g(u, "all") if "all" in u else ""])
    print(json.dumps({"checks": checks, "checks_failed": fails}, indent=1, default=float))
    raise SystemExit(1 if fails else 0)


if __name__ == "__main__":
    main()
