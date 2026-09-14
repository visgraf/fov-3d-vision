"""A5: integrate a fixation sequence into a sphere and measure error against budget. Host side.

    .venv/bin/python tools/integrate_sphere.py previews/sequence/calib_room \
        --reference previews/reference_small/calib_room --out previews/integrated/calib_room \
        --k-list 1,2,5,10,20,50 --uniform previews/uniform/calib_room --bound 0.0263 \
        --calibration previews/uniform/calib_room/w3600_seed0 --calibration-b previews/uniform/calib_room/w3600_seed1

Accumulation (finest-owns, D9 pass): every sample (D1 record) splats over the equirect
cells whose centres lie inside a disc of angular radius sqrt(footprint/pi) around its
direction, on the profile's reference grid. Per cell, the samples whose footprint is within
--finest-factor of the finest footprint present there form the FINEST layer (weighted
1/footprint among themselves); every coarser sample goes to a separate FILL layer.

Reconstruction at s_eval = --eval-factor x s0 (0.2 deg small, 0.1 deg full): the finest layer
box-filtered to s_eval where it covers; blocks with no finest coverage take the fill layer;
blocks covered by nothing are uncovered, excluded from the error and always reported as a
fraction beside it. A block is covered if at least one of its cells is; the fraction of
blocks only partly covered is reported too.

Metric (D9): relative RMS = RMS(reconstruction - reference at s_eval) / mean(reference at
s_eval), solid-angle weighted, mean over RGB, (i) at the targets (blocks within --target-deg
of every gaze of the full sequence) and (ii) over the covered sphere. A uniform render is
upsampled to the reference grid (nearest) and then box-filtered to s_eval, so its blur is
charged like everyone else's. The resampling floor at s_eval (reference vs its bilinear
half-pixel shift, both filtered to s_eval, at the targets) is reported beside the numbers.

Checks that can fail (exit 1):
  (1) identity     the reference's own pixels fed in as samples come out equal to the
                   reference at s_eval to 1e-6 over |lat| <= --identity-lat (a polar pixel's
                   disc spans its longitude neighbours, so the poles are reported, not judged)
  (2) control      every gaze yawed --control-yaw deg gives a target error at least
                   --control-factor times the largest-K value
  (3) calibration  a uniform render at the full s0 resolution and the fixation spp, scored by
                   the metric, must show its noise: --calibration-expect +- --calibration-tol
                   (0.073 +- 0.01 on the calib room, A2's 64 spp median-tile figure). Reported
                   next to it, from a second seed of that render when given: the same render's
                   noise measured at s_eval as the seed pair's RMS / sqrt(2), which is what the
                   metric should charge when there is nothing but noise to charge.
  (4) D8 validation  the per-cell footprint-aware comparison of A5's first pass, binned to
                   0.5 deg at the targets, below --bound (the median measured (b) bound)
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


def nearest_gaze_deg(d: np.ndarray, gazes: np.ndarray) -> np.ndarray:
    best = np.full(len(d), -1.0)
    for g in gazes:
        best = np.maximum(best, d @ g)
    return np.degrees(np.arccos(np.clip(best, -1.0, 1.0)))


def candidates(H: int, W: int, d: np.ndarray, fp: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Flat cell indices inside each sample's disc (radius sqrt(fp/pi)), with the sample index."""
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
            out_idx.append((rows[si, ci] * W + cols[si, ci]).astype(np.int64))
            out_s.append(s[si].astype(np.int32))
    return np.concatenate(out_idx), np.concatenate(out_s)


# ----------------------------------------------------------------------------------------
# finest-owns accumulation
# ----------------------------------------------------------------------------------------

class Sphere:
    """Two layers per cell. Build with add() for every fixation (candidates are kept), then
    finalise(): the finest footprint per cell is known only once every sample is in."""

    def __init__(self, H: int, W: int, finest_factor: float):
        self.H, self.W, self.ff = H, W, finest_factor
        self.parts = []                      # (idx, s, d, v, fp) per fixation
        self.footprint_in, self.samples_in = 0.0, 0

    def add(self, d: np.ndarray, v: np.ndarray, fp: np.ndarray) -> None:
        idx, s = candidates(self.H, self.W, d, fp)
        self.parts.append((idx, s, d, v, fp))
        self.footprint_in += float(fp.sum()); self.samples_in += int(len(fp))

    def finalise(self) -> None:
        n = self.H * self.W
        self.min_fp = np.full(n, np.inf)
        for idx, s, d, v, fp in self.parts:
            order = np.argsort(fp[s], kind="stable")
            u, first = np.unique(idx[order], return_index=True)
            self.min_fp[u] = np.minimum(self.min_fp[u], fp[s][order][first])
        self.fine_rgb = np.zeros((n, 3)); self.fine_w = np.zeros(n); self.fine_dir = np.zeros((n, 3))
        self.fill_rgb = np.zeros((n, 3)); self.fill_w = np.zeros(n); self.fill_dir = np.zeros((n, 3))
        self.count = np.zeros(n, dtype=np.int64); self.fix_count = np.zeros(n, dtype=np.int32)
        for idx, s, d, v, fp in self.parts:
            fine = fp[s] <= self.ff * self.min_fp[idx]
            w = 1.0 / fp[s]
            for layer, m in ((True, fine), (False, ~fine)):
                if not m.any():
                    continue
                rgb, wt, dr = (self.fine_rgb, self.fine_w, self.fine_dir) if layer else (self.fill_rgb, self.fill_w, self.fill_dir)
                wt += np.bincount(idx[m], weights=w[m], minlength=n)
                for c in range(3):
                    rgb[:, c] += np.bincount(idx[m], weights=w[m] * v[s[m], c], minlength=n)
                    dr[:, c] += np.bincount(idx[m], weights=w[m] * d[s[m], c], minlength=n)
            self.count += np.bincount(idx, minlength=n)
            touched = np.zeros(n, dtype=bool); touched[idx] = True
            self.fix_count += touched

    def composite(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Per cell: value (finest where present, else fill), covered mask, finest-covered mask,
        and the centroid direction of the layer used."""
        fine = self.fine_w > 0; fill = (~fine) & (self.fill_w > 0)
        with np.errstate(invalid="ignore", divide="ignore"):
            val = np.where(fine[:, None], self.fine_rgb / self.fine_w[:, None], 0.0)
            val = np.where(fill[:, None], self.fill_rgb / self.fill_w[:, None], val)
            dr = np.where(fine[:, None], self.fine_dir, self.fill_dir)
            cen = dr / np.maximum(np.linalg.norm(dr, axis=-1, keepdims=True), 1e-300)
        return val, fine | fill, fine, cen


# ----------------------------------------------------------------------------------------
# s_eval grid
# ----------------------------------------------------------------------------------------

class EvalGrid:
    """Blocks of b x b reference cells; block means are solid-angle weighted."""

    def __init__(self, H: int, W: int, block: int):
        assert H % block == 0 and W % block == 0, (H, W, block)
        self.H, self.W, self.b = H, W, block
        self.He, self.We = H // block, W // block
        rows = np.repeat(np.arange(H), W)
        self.omega = cell_solid_angle(H, W, rows)
        self.block_of = (rows // block) * self.We + (np.tile(np.arange(W), H) // block)
        self.omega_e = np.bincount(self.block_of, weights=self.omega, minlength=self.He * self.We)
        re, ce = np.divmod(np.arange(self.He * self.We), self.We)
        lon, lat = grid_lonlat(self.He, self.We, re, ce)
        self.dir_e = dir_of(lon, lat)
        self.lat_e = lat

    def down(self, val: np.ndarray, covered: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Block mean of val over covered cells. Returns (mean, covered_block, partial_block)."""
        ne = self.He * self.We
        if covered is None:
            covered = np.ones(len(val), bool)
        w = self.omega * covered
        wsum = np.bincount(self.block_of, weights=w, minlength=ne)
        vsum = np.bincount(self.block_of, weights=w * val, minlength=ne)
        with np.errstate(invalid="ignore", divide="ignore"):
            mean = np.where(wsum > 0, vsum / wsum, 0.0)
        cov = wsum > 0
        partial = cov & (wsum < self.omega_e * (1 - 1e-9))
        return mean, cov, partial

    def rel_rms(self, a: np.ndarray, ref: np.ndarray, m: np.ndarray) -> dict | None:
        if not m.any():
            return None
        w = self.omega_e[m]; e = a[m] - ref[m]; r = ref[m]
        return {"rel_rms": float(math.sqrt((w * e * e).sum() / w.sum()) / ((w * r).sum() / w.sum())),
                "rel_median": float(np.median(np.abs(e) / np.maximum(r, 1e-3))), "blocks": int(m.sum())}

    def frac(self, m: np.ndarray) -> float:
        return float(self.omega_e[m].sum() / self.omega_e.sum())


def uniform_to_grid(img: np.ndarray, H: int, W: int) -> np.ndarray:
    """Nearest upsample of a (Hu, Wu, 3) render to the reference grid, mean over RGB, flat."""
    Hu, Wu = img.shape[:2]
    rows, cols = np.divmod(np.arange(H * W), W)
    return img[(rows * Hu) // H, (cols * Wu) // W].mean(-1)


def half_pixel_shift(ref_mean: np.ndarray) -> np.ndarray:
    """Bilinear value half a pixel right and down, (H, W), wrapping in x."""
    r = ref_mean
    rx = np.roll(r, -1, axis=1)
    ry = np.concatenate([r[1:], r[-1:]], axis=0); rxy = np.roll(ry, -1, axis=1)
    return 0.25 * (r + rx + ry + rxy)


# ----------------------------------------------------------------------------------------
# D8 validation (per-cell, footprint-aware), kept as a check
# ----------------------------------------------------------------------------------------

class RefBox:
    def __init__(self, ref_mean: np.ndarray):
        self.H, self.W = ref_mean.shape
        t = np.concatenate([ref_mean, ref_mean, ref_mean], axis=1)
        self.I = np.pad(t, ((1, 0), (1, 0))).cumsum(0).cumsum(1)

    def mean(self, cx, cy, hx, hy):
        W, H = self.W, self.H
        x0 = np.rint(cx - hx).astype(int); x1 = np.maximum(np.rint(cx + hx).astype(int), x0 + 1)
        y0 = np.clip(np.rint(cy - hy).astype(int), 0, H - 1); y1 = np.clip(np.maximum(np.rint(cy + hy).astype(int), y0 + 1), 1, H)
        x0 = np.clip(x0 + W, 0, 3 * W - 1); x1 = np.clip(x1 + W, 1, 3 * W)
        s = self.I[y1, x1] - self.I[y0, x1] - self.I[y1, x0] + self.I[y0, x0]
        return s / ((x1 - x0) * (y1 - y0))


def d8_targets_binned(sp: Sphere, refbox: RefBox, targets: np.ndarray, target_deg: float, bin_deg: float = 0.5) -> dict:
    H, W = sp.H, sp.W
    val3, covered, fine, cen = sp.composite()
    idx = np.nonzero(covered)[0]
    rows, cols = idx // W, idx % W
    d = dir_of(*grid_lonlat(H, W, rows, cols))
    near = nearest_gaze_deg(d, targets) <= target_deg
    idx, rows, cols, cen = idx[near], rows[near], cols[near], cen[idx][near]
    fp = sp.min_fp[idx]; side = np.sqrt(fp)
    lon_c, lat_c = lonlat_of(cen)
    ccx = (lon_c / (2 * np.pi) + 0.5) * W; ccy = (0.5 - lat_c / np.pi) * H
    hx = side / 2 / ((2 * np.pi / W) * np.maximum(np.cos(lat_c), 1e-9)); hy = side / 2 / (np.pi / H)
    rb = refbox.mean(ccx, ccy, hx, hy)
    val = val3[idx].mean(-1)
    omega = cell_solid_angle(H, W, rows)
    e = val - rb
    per_cell = float(math.sqrt((omega * e * e).sum() / omega.sum()) / ((omega * rb).sum() / omega.sum()))
    bsz = max(1, int(round(bin_deg / (360.0 / W))))
    key = (rows // bsz) * (W // bsz + 1) + cols // bsz
    u, inv = np.unique(key, return_inverse=True)
    wsum = np.bincount(inv, weights=omega); vb = np.bincount(inv, weights=omega * val) / wsum
    rbb = np.bincount(inv, weights=omega * rb) / wsum; eb = vb - rbb
    return {"targets_per_cell_rel_rms": per_cell, "targets_cells": int(len(idx)),
            "targets_binned_rel_rms": float(math.sqrt((wsum * eb * eb).sum() / wsum.sum()) / ((wsum * rbb).sum() / wsum.sum())),
            "bin_deg": bin_deg, "bins": int(len(u))}


# ----------------------------------------------------------------------------------------
# chart
# ----------------------------------------------------------------------------------------

def draw_curve_png(path: str, series: list[tuple[str, list[tuple[float, float]], tuple, bool]], title: str, ymax: float) -> None:
    """series: (label, [(rays, err)], colour, dotted). Log x, linear y. PIL only."""
    from PIL import Image, ImageDraw, ImageFont
    Wp, Hp, L, R, T, B = 960, 640, 90, 30, 50, 70
    im = Image.new("RGB", (Wp, Hp), "white"); dr = ImageDraw.Draw(im)
    try:
        dr.font = ImageFont.load_default(size=15)
    except TypeError:
        pass
    xs = [r for _, pts, _, _ in series for r, _ in pts]
    x0, x1 = math.log10(min(xs)) - 0.1, math.log10(max(xs)) + 0.1
    def X(r): return L + (math.log10(r) - x0) / (x1 - x0) * (Wp - L - R)
    def Y(e): return Hp - B - min(e, ymax) / ymax * (Hp - T - B)
    dr.rectangle([L, T, Wp - R, Hp - B], outline="black")
    for k in range(6, 9):
        for m in (1, 2, 5):
            r = m * 10 ** k
            if x0 <= math.log10(r) <= x1:
                dr.line([X(r), Hp - B, X(r), Hp - B + 5], fill="black"); dr.text((X(r) - 18, Hp - B + 8), f"{r:.0e}".replace("e+0", "e"), fill="black")
    for e in np.arange(0, ymax + 1e-9, 0.05):
        dr.line([L - 5, Y(e), L, Y(e)], fill="black"); dr.text((L - 50, Y(e) - 8), f"{e:.2f}", fill="black")
        dr.line([L, Y(e), Wp - R, Y(e)], fill=(230, 230, 230))
    for label, pts, col, dotted in series:
        pts = sorted(pts)
        for (ra, ea), (rb, eb) in zip(pts, pts[1:]):
            if dotted:
                n = 12
                for i in range(0, n, 2):
                    dr.line([X(ra) + (X(rb) - X(ra)) * i / n, Y(ea) + (Y(eb) - Y(ea)) * i / n,
                             X(ra) + (X(rb) - X(ra)) * (i + 1) / n, Y(ea) + (Y(eb) - Y(ea)) * (i + 1) / n], fill=col, width=3)
            else:
                dr.line([X(ra), Y(ea), X(rb), Y(eb)], fill=col, width=3)
        for r, e in pts:
            dr.ellipse([X(r) - 5, Y(e) - 5, X(r) + 5, Y(e) + 5], fill=col)
    for i, (label, _, col, dotted) in enumerate(series):
        y = T + 14 + i * 24
        dr.line([Wp - R - 290, y, Wp - R - 255, y], fill=col, width=3); dr.text((Wp - R - 245, y - 8), label + (" (dashed)" if dotted else ""), fill="black")
    dr.text((L, 15), title, fill="black"); dr.text((Wp // 2 - 30, Hp - 22), "rays (log)", fill="black"); dr.text((8, T), "rel RMS", fill="black")
    im.save(path)


# ----------------------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sequence")
    ap.add_argument("--reference", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--k-list", default="1,2,5,10,20,50")
    ap.add_argument("--uniform", help="folder holding preview360 renders w<W>/ at equal budgets")
    ap.add_argument("--bound", type=float, required=True, help="median of check_sequence's measured (b) bounds (D8 check)")
    ap.add_argument("--eval-factor", type=float, default=2.0, help="s_eval = eval_factor x s0 (D9)")
    ap.add_argument("--finest-factor", type=float, default=1.5)
    ap.add_argument("--target-deg", type=float, default=1.0)
    ap.add_argument("--control-yaw", type=float, default=90.0)
    ap.add_argument("--control-factor", type=float, default=5.0)
    ap.add_argument("--identity-lat", type=float, default=60.0)
    ap.add_argument("--calibration", help="preview360 folder: uniform at the full s0 resolution, fixation spp")
    ap.add_argument("--calibration-b", help="the same render at another seed, for its measured noise")
    ap.add_argument("--calibration-expect", type=float, default=0.073)
    ap.add_argument("--calibration-tol", type=float, default=0.01)
    ap.add_argument("--skip-identity", action="store_true")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    seq = json.load(open(os.path.join(args.sequence, "sequence.json")))
    ref_meta = json.load(open(os.path.join(args.reference, "meta.json")))
    ref = read_combined(os.path.join(args.reference, "pano.exr"))
    H, W = ref.shape[:2]
    ref_mean = ref.mean(-1)
    s0_ref = 360.0 / W
    block = int(round(args.eval_factor))
    grid = EvalGrid(H, W, block)
    s_eval = s0_ref * block
    ref_e, _, _ = grid.down(ref_mean.reshape(-1))
    refbox = RefBox(ref_mean)
    R_eye = eye_rotation(ref_meta["eye"])
    fails = []

    fixations = seq["fixations"]
    gaze_dirs = np.array([R_eye.T @ np.array(json.load(open(os.path.join(args.sequence, f"f{f['id']:03d}", "meta.json")))["camera_forward"], float)
                          for f in fixations])
    targets = gaze_dirs
    near_t = nearest_gaze_deg(grid.dir_e, targets) <= args.target_deg
    k_list = sorted({min(int(k), len(fixations)) for k in args.k_list.split(",")})
    kmax = max(k_list)
    band = np.abs(np.degrees(grid.lat_e)) <= args.identity_lat

    # resampling floor at s_eval
    shift_e, _, _ = grid.down(half_pixel_shift(ref_mean).reshape(-1))
    floor = {"targets": grid.rel_rms(shift_e, ref_e, near_t), "sphere": grid.rel_rms(shift_e, ref_e, np.ones(len(ref_e), bool)),
             "how": "reference vs its bilinear half-pixel shift, both box-filtered to s_eval"}
    print(f"[integrate] s_eval {s_eval:.3f} deg ({grid.We}x{grid.He}); resampling floor at targets {floor['targets']['rel_rms']:.4f}, sphere {floor['sphere']['rel_rms']:.4f}", flush=True)

    checks = {}
    if not args.skip_identity:
        sp = Sphere(H, W, args.finest_factor)
        rows, cols = np.divmod(np.arange(H * W), W)
        d = dir_of(*grid_lonlat(H, W, rows, cols)); fp = cell_solid_angle(H, W, rows)
        for a in range(0, H * W, 400_000):
            sl = slice(a, a + 400_000); sp.add(d[sl], ref.reshape(-1, 3)[sl], fp[sl])
        sp.finalise()
        val3, covered, fine, _ = sp.composite()
        rec, cov, _ = grid.down(val3.mean(-1), covered)
        err = np.abs(rec - ref_e)
        checks["identity"] = {"max_abs_err_within_band": float(err[band].max()), "uncovered_within_band": int((~cov[band]).sum()),
                              "max_abs_err_beyond_band": float(err[~band].max()), "identity_lat": args.identity_lat}
        if not (checks["identity"]["max_abs_err_within_band"] <= 1e-6 and checks["identity"]["uncovered_within_band"] == 0):
            fails.append(f"(1) identity: max error {checks['identity']['max_abs_err_within_band']:.3e} within |lat| <= {args.identity_lat}")
        print(f"[integrate] identity: max err {checks['identity']['max_abs_err_within_band']:.2e} within |lat|<={args.identity_lat}, "
              f"{checks['identity']['max_abs_err_beyond_band']:.2e} beyond", flush=True)
        del sp

    def load(f, rot):
        s = np.load(os.path.join(args.sequence, f"f{f['id']:03d}", "samples.npz"))
        d = s["direction"].astype(np.float64)
        return (d if rot is None else d @ rot.T), s["value"].astype(np.float64), s["footprint"].astype(np.float64)

    def build(k: int, rot) -> Sphere:
        sp = Sphere(H, W, args.finest_factor)
        for f in fixations[:k]:
            sp.add(*load(f, rot))
        sp.finalise()
        return sp

    def evaluate(sp: Sphere, k: int) -> dict:
        val3, covered, fine, _ = sp.composite()
        val = val3.mean(-1)
        rec_f, cov_f, _ = grid.down(val, fine)                  # finest layer where it covers
        rec_a, cov_a, partial = grid.down(val, covered)          # everything
        rec = np.where(cov_f, rec_f, rec_a); cov = cov_a
        rays = sum(f["samples"] * seq["spp"] for f in fixations[:k]); secs = sum(f["render_seconds"] for f in fixations[:k])
        out = {"K": k, "rays": int(rays), "render_seconds": secs,
               "targets": grid.rel_rms(rec, ref_e, near_t & cov), "sphere": grid.rel_rms(rec, ref_e, cov),
               "uncovered_frac": 1.0 - grid.frac(cov), "partial_block_frac": grid.frac(partial),
               "finest_block_frac": grid.frac(cov_f), "fill_only_block_frac": grid.frac(cov & ~cov_f),
               "targets_uncovered_frac": float(1.0 - grid.omega_e[near_t & cov].sum() / grid.omega_e[near_t].sum()),
               "cell_coverage_frac": float(cell_solid_angle(H, W, np.repeat(np.arange(H), W))[covered].sum() / (4 * np.pi)),
               "d8": d8_targets_binned(sp, refbox, targets, args.target_deg)}
        return out

    curve = {}
    for k in k_list:
        sp = build(k, None)
        curve[k] = evaluate(sp, k)
        c = curve[k]
        print(f"[integrate] K={k:2d}: rays {c['rays']:>9d} {c['render_seconds']:.3f}s  targets {c['targets']['rel_rms']:.4f}  "
              f"sphere {c['sphere']['rel_rms']:.4f} (uncovered {c['uncovered_frac']:.3f}, partial {c['partial_block_frac']:.3f}, "
              f"fill-only {c['fill_only_block_frac']:.3f})  D8 binned {c['d8']['targets_binned_rel_rms']:.4f}", flush=True)
        if k == kmax:
            val3, covered, fine, _ = sp.composite()
            np.savez(os.path.join(args.out, "integrated.npz"), rgb=val3.reshape(H, W, 3).astype(np.float32),
                     fine_weight=sp.fine_w.reshape(H, W).astype(np.float32), fill_weight=sp.fill_w.reshape(H, W).astype(np.float32),
                     min_footprint=sp.min_fp.reshape(H, W).astype(np.float32), fixation_count=sp.fix_count.reshape(H, W), K=k)
            from PIL import Image
            rgb = np.where(covered[:, None], val3, 0.0).reshape(H, W, 3)
            Image.fromarray((np.clip(rgb, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8)).save(os.path.join(args.out, "rgb.png"))
            fpm = sp.min_fp.reshape(H, W); g = np.where(np.isfinite(fpm), np.clip((np.log10(np.maximum(fpm, 1e-12)) + 6) / 3, 0, 1), 0.0)
            Image.fromarray(((1 - g) * 255).astype(np.uint8)).save(os.path.join(args.out, "min_footprint.png"))
        del sp

    t_err = curve[kmax]["targets"]["rel_rms"]
    ctrl = evaluate(build(kmax, rot_y(args.control_yaw)), kmax)
    c_err = ctrl["targets"]["rel_rms"] if ctrl["targets"] else float("nan")
    checks["control"] = {"K": kmax, "yaw": args.control_yaw, "rel_rms": c_err, "ratio": c_err / t_err}
    if not (c_err >= args.control_factor * t_err):
        fails.append(f"(2) control: rotated target error {c_err:.4f} is not {args.control_factor}x the K={kmax} value {t_err:.4f}")
    checks["d8_validation"] = {"K": kmax, "targets_binned_rel_rms": curve[kmax]["d8"]["targets_binned_rel_rms"], "bound": args.bound}
    if not (curve[kmax]["d8"]["targets_binned_rel_rms"] < args.bound):
        fails.append(f"(4) D8 validation: binned target error {curve[kmax]['d8']['targets_binned_rel_rms']:.4f} at K={kmax} is not below {args.bound:.4f}")

    def eval_uniform(folder: str) -> dict:
        meta = json.load(open(os.path.join(folder, "meta.json")))
        img = read_combined(os.path.join(folder, "pano.exr"))
        rec, _, _ = grid.down(uniform_to_grid(img, H, W))
        return {"width": img.shape[1], "spp": meta["spp"], "rays": img.shape[0] * img.shape[1] * meta["spp"],
                "render_seconds": meta["render_seconds"], "render_seconds_includes_write": True, "seed": meta.get("seed", 0),
                "targets": grid.rel_rms(rec, ref_e, near_t), "sphere": grid.rel_rms(rec, ref_e, np.ones(len(ref_e), bool)),
                "pixel_deg": 360.0 / img.shape[1], "_rec": rec}

    uniform = {}
    if args.uniform:
        for k in k_list:
            B = k * seq["samples_per_fixation"] * seq["spp"]
            Wu = int(round(math.sqrt(2 * B / 64) / 2)) * 2
            folder = os.path.join(args.uniform, f"w{Wu}")
            if Wu < 64 or not os.path.isdir(folder):
                uniform[k] = {"width": Wu, "skipped": "W < 64" if Wu < 64 else f"missing {folder}"}
                continue
            u = eval_uniform(folder); u.pop("_rec"); u["budget_ratio_to_foveated"] = u["rays"] / B
            uniform[k] = u
            print(f"[integrate] uniform W={Wu:4d} for K={k:2d}: rays {u['rays']:>9d} {u['render_seconds']:.2f}s  targets {u['targets']['rel_rms']:.4f}  sphere {u['sphere']['rel_rms']:.4f}", flush=True)

    if args.calibration:
        ca = eval_uniform(args.calibration)
        cal = {"folder": args.calibration, "width": ca["width"], "spp": ca["spp"], "rays": ca["rays"], "render_seconds": ca["render_seconds"],
               "targets_rel_rms": ca["targets"]["rel_rms"], "sphere_rel_rms": ca["sphere"]["rel_rms"],
               "expect": args.calibration_expect, "tol": args.calibration_tol}
        if args.calibration_b:
            cb = eval_uniform(args.calibration_b)
            e = ca["_rec"] - cb["_rec"]; w = grid.omega_e
            cal["seed_pair_noise_at_s_eval"] = float(math.sqrt((w * e * e).sum() / w.sum()) / ((w * ref_e).sum() / w.sum()) / math.sqrt(2))
            cal["seed_pair_noise_how"] = "RMS(seed0 - seed1) / mean(ref) / sqrt(2), both at s_eval, over the sphere"
            cal["score_over_measured_noise"] = cal["sphere_rel_rms"] / cal["seed_pair_noise_at_s_eval"]
        checks["calibration"] = cal
        if not (abs(cal["sphere_rel_rms"] - args.calibration_expect) <= args.calibration_tol):
            fails.append(f"(3) calibration: uniform at s0 scores {cal['sphere_rel_rms']:.4f} over the sphere, expected "
                         f"{args.calibration_expect} +- {args.calibration_tol}")
        print(f"[integrate] calibration W={ca['width']}: sphere {cal['sphere_rel_rms']:.4f}, targets {cal['targets_rel_rms']:.4f}"
              + (f", seed-pair noise at s_eval {cal['seed_pair_noise_at_s_eval']:.4f} (score/noise {cal['score_over_measured_noise']:.3f})" if args.calibration_b else ""), flush=True)

    series = [("foveated, targets", [(c["rays"], c["targets"]["rel_rms"]) for c in curve.values() if c["targets"]], (200, 30, 30), False),
              ("uniform, targets", [(u["rays"], u["targets"]["rel_rms"]) for u in uniform.values() if "targets" in u], (200, 30, 30), True),
              ("foveated, sphere", [(c["rays"], c["sphere"]["rel_rms"]) for c in curve.values()], (30, 60, 200), False),
              ("uniform, sphere", [(u["rays"], u["sphere"]["rel_rms"]) for u in uniform.values() if "sphere" in u], (30, 60, 200), True)]
    ymax = max(0.05, math.ceil(max(e for _, pts, _, _ in series for _, e in pts) * 20) / 20)
    draw_curve_png(os.path.join(args.out, "curve.png"), series, f"{os.path.basename(args.sequence)}: error vs rays at s_eval {s_eval:.2f} deg (D9)", ymax)

    result = {"sequence": args.sequence, "reference": args.reference, "grid": [W, H], "s_eval_deg": s_eval, "eval_grid": [grid.We, grid.He],
              "finest_factor": args.finest_factor, "profile": seq.get("profile"), "spp": seq["spp"],
              "warmup_seconds_discarded": seq["warmup_seconds_discarded"],
              "metric": "D9: relative RMS between the reconstruction at s_eval and the reference box-filtered to s_eval, "
                        "solid-angle weighted, mean over RGB; uniform renders nearest-upsampled to the reference grid then filtered the same way",
              "resampling_floor_at_s_eval": floor,
              "curve": {str(k): v for k, v in curve.items()}, "uniform": {str(k): v for k, v in uniform.items()},
              "control": ctrl, "checks": checks, "checks_failed": fails}
    with open(os.path.join(args.out, "curve.json"), "w") as fh:
        json.dump(result, fh, indent=1, default=float)
    with open(os.path.join(args.out, "curve.csv"), "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["K", "rays", "render_seconds", "targets_rel_rms", "sphere_rel_rms", "uncovered_frac", "targets_uncovered_frac",
                     "d8_targets_binned_rel_rms", "uniform_width", "uniform_rays", "uniform_seconds", "uniform_targets_rel_rms", "uniform_sphere_rel_rms"])
        for k in k_list:
            c = curve[k]; u = uniform.get(k, {})
            wr.writerow([k, c["rays"], round(c["render_seconds"], 3), c["targets"]["rel_rms"] if c["targets"] else "", c["sphere"]["rel_rms"],
                         round(c["uncovered_frac"], 4), round(c["targets_uncovered_frac"], 4), c["d8"]["targets_binned_rel_rms"],
                         u.get("width", ""), u.get("rays", ""), u.get("render_seconds", ""),
                         u["targets"]["rel_rms"] if "targets" in u else "", u["sphere"]["rel_rms"] if "sphere" in u else ""])
    print(json.dumps({"checks": checks, "checks_failed": fails}, indent=1, default=float))
    raise SystemExit(1 if fails else 0)


if __name__ == "__main__":
    main()
