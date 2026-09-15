"""The stereo instrument (B3, D15): a reference matcher and the matcher-free bound on a pair run.

    .venv/bin/python tools/stereo_instrument.py previews/pairs/calib_room_sp --sheet
    .venv/bin/python tools/stereo_instrument.py previews/pairs/calib_room_control --sheet

Host side, venv. Input: a fixation_pairs.py run after stereo_truth.py (truth.npz beside every
samples.npz). No rendering.

Per pair, both eyes' foveal samples are integrated onto a local epipolar grid at s_eval =
--eval-factor x s0 (D9): rows are epipolar planes phi (shared by the two eyes), columns are
theta from each eye's own gaze, so a correspondence is a shift along a row. Finest-owns within
the cell (samples within --finest-factor of the cell's finest footprint, footprint-weighted).

The instrument: per L cell, normalised cross-correlation of a (2h+1)^2 window against the R
row over shifts in [-S, S] cells, winner-take-all, parabolic sub-cell refinement. Estimated
parallax = (theta_gaze_R - theta_gaze_L) + shift x cell. Error against truth.npz's parallax
on cells the other eye sees. NOT the research matcher (D5): it runs on a uniform grid at
s_eval and exists so the E2 sweep has a number.

The bound: per L cell, the Fisher information of a shift, I = sum over the window of
g^2 / (sigma_L^2 + sigma_R^2), g the L map's gradient along theta; 1/sqrt(I) bounds any
unbiased estimator's RMS. Sigma per cell is measured from the seed pair (samples_b.npz) when
the run has one, else assumed from --noise-rel (the profile's per-pixel rel RMS from the
manifest, divided by the root of the samples per cell) and labelled so. Total information per
pair over the fovea, divided by the pair's rays, is the matcher-free objective: disparity
information per ray.

Checks, each of which can fail (exit 1), in <run>/stereo.json:
  (l) self-shift   the L map matched against itself shifted by --self-shift cells returns that
                   shift on >= --self-frac of matchable cells (within 0.1 cell)
  (m) recovery     on every judged card, over the judged edge-free cells of the fixated surface
                   (truth parallax within half a cell of the centre block's), the median estimate
                   agrees with the median truth within one cell. On a --vergence off run that is
                   a shift of ~1.8 deg (9 cells at small); on a verged run ~0. A matcher that
                   returned the map centre would pass the second and fail the first. Judged only
                   with >= --centre-min-cells such cells; else reported.
  (n) bound        on every judged card the bound RMS is at most --bound-slack x the inlier RMS
                   (a bound far above the measured error means sigma or the model is wrong);
                   the ratio inlier RMS / bound is reported.
Reported (the result, not a criterion): inlier RMS and gross fraction (|err| > 1 cell) of the
parallax error at the fixated cards, in deg, cells and s0; depth RMS via triangulation; bound
RMS; information per pair and per ray; matchable and covered fractions.
--sheet: L map | R map | truth parallax | estimate | error for the first --sheet-pairs pairs.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rig import EYE_NAMES, epipolar, to_eye_frame, triangulate  # noqa: E402

JUDGED_KINDS = {"ring", "ladder", "point"}


# ----------------------------------------------------------------------------------------
# foveal epipolar maps
# ----------------------------------------------------------------------------------------

class FoveaGrid:
    """J x J cells of `cell` degrees about (theta_c, phi_c); columns along theta, rows along phi,
    rows scaled by 1/sin(theta_mid) so cells are square on the sphere at the centre."""

    def __init__(self, theta_c: float, phi_c: float, theta_mid: float, half_deg: float, cell: float, extra_cols: int = 0):
        self.theta_c, self.phi_c, self.cell = theta_c, phi_c, cell
        self.h = int(math.ceil(half_deg / cell))
        self.hj = self.h + extra_cols                       # half-width in columns (theta) may exceed the rows'
        self.J = 2 * self.h + 1                             # rows
        self.W = 2 * self.hj + 1                            # columns
        self.dphi = cell / max(math.sin(math.radians(theta_mid)), 1e-6)

    def cell_of(self, theta: np.ndarray, phi: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        j = np.rint((theta - self.theta_c) / self.cell).astype(int) + self.hj
        dphi = (phi - self.phi_c + 180.0) % 360.0 - 180.0
        r = np.rint(dphi / self.dphi).astype(int) + self.h
        ok = (j >= 0) & (j < self.W) & (r >= 0) & (r < self.J)
        return r, j, ok

    def theta_of_col(self, j) -> np.ndarray:
        return self.theta_c + (np.asarray(j) - self.hj) * self.cell


def accumulate(grid: FoveaGrid, theta, phi, val, fp, finest_factor: float, extra: dict | None = None) -> tuple[np.ndarray, np.ndarray, dict]:
    """Finest-owns footprint-weighted mean per cell. Returns (map, covered, extras) where extras
    holds the same accumulation of any extra per-sample arrays (truth parallax, distance...)."""
    r, j, ok = grid.cell_of(theta, phi)
    n = grid.J * grid.W
    idx = (r * grid.W + j)[ok]
    fpo = fp[ok]
    finest = np.full(n, np.inf)
    np.minimum.at(finest, idx, fpo)
    own = fpo <= finest_factor * finest[idx]
    w = np.where(own, 1.0 / fpo, 0.0)
    wsum = np.bincount(idx, weights=w, minlength=n)
    out = {}
    with np.errstate(invalid="ignore", divide="ignore"):
        m = np.bincount(idx, weights=w * val[ok], minlength=n) / wsum
        for k, arr in (extra or {}).items():
            out[k] = (np.bincount(idx, weights=w * arr[ok], minlength=n) / wsum).reshape(grid.J, grid.W)
    covered = (wsum > 0).reshape(grid.J, grid.W)
    return np.where(covered, m.reshape(grid.J, grid.W), np.nan), covered, out


# ----------------------------------------------------------------------------------------
# the instrument
# ----------------------------------------------------------------------------------------

def ncc_match(A: np.ndarray, B: np.ndarray, h: int, S: int, texture_min: float, min_valid: float = 0.6, texture_abs: float = 0.0):
    """Per cell of A (J x J): best shift d in [-S, S] so that A[r, j] ~ B[r, pad + j + d], by NCC
    over a (2h+1)^2 window, with parabolic refinement. B is J x (J + 2 pad) with pad >= S so a
    correspondence within the search range always lies inside B. A window is scored only where
    at least min_valid of ITS OWN valid cells (not of the full window) have a valid partner, so
    edge rows are scored on what they have rather than dropped. Returns (shift, ncc_peak,
    matchable)."""
    J = A.shape[0]
    pad = (B.shape[1] - J) // 2
    if pad < S:
        raise ValueError(f"B must be at least 2S wider than A: pad {pad} < S {S}")
    va, vb = np.isfinite(A), np.isfinite(B)
    Az, Bz = np.where(va, A, 0.0), np.where(vb, B, 0.0)
    scores = np.full((2 * S + 1, J, J), np.nan)
    # window sums by integral images over the valid masks
    def wsum(X):
        P = np.pad(X, h + 1)
        C = P.cumsum(0).cumsum(1)
        return (C[2 * h + 1:, 2 * h + 1:] - C[:-2 * h - 1, 2 * h + 1:] - C[2 * h + 1:, :-2 * h - 1] + C[:-2 * h - 1, :-2 * h - 1])[:J, :J]
    nA = wsum(va.astype(float))
    for k, d in enumerate(range(-S, S + 1)):
        o = pad + d
        Bs, Vs = Bz[:, o:o + J], vb[:, o:o + J]
        V = va & Vs
        nV = wsum(V.astype(float))
        a, b = np.where(V, Az, 0.0), np.where(V, Bs, 0.0)
        sa, sb = wsum(a), wsum(b)
        saa, sbb, sab = wsum(a * a), wsum(b * b), wsum(a * b)
        with np.errstate(invalid="ignore", divide="ignore"):
            ma, mb = sa / nV, sb / nV
            cov = sab - nV * ma * mb
            vara, varb = saa - nV * ma * ma, sbb - nV * mb * mb
            ncc = cov / np.sqrt(vara * varb)
        ncc[(nV < min_valid * nA) | (nV < 4)] = np.nan
        scores[k] = ncc
    # texture: the L window's relative std must exceed texture_min
    nV0 = wsum(va.astype(float)); sa0 = wsum(Az); saa0 = wsum(Az * Az)
    with np.errstate(invalid="ignore", divide="ignore"):
        m0 = sa0 / nV0; std0 = np.sqrt(np.maximum(saa0 / nV0 - m0 * m0, 0.0))
        rel_std = std0 / np.abs(m0)
    # matchable: the L window has texture above texture_min relative to its mean AND above
    # texture_abs (3 sigma of the two maps' noise, set by the caller), so noise is not matched
    matchable = va & (rel_std > texture_min) & (std0 > texture_abs) & np.isfinite(scores).any(0)
    best = np.nanargmax(np.where(np.isfinite(scores), scores, -np.inf), axis=0)
    rr, cc = np.indices((J, J))
    pk = scores[best, rr, cc]
    d0 = best - S
    # sub-cell refinement: two Lucas-Kanade steps about the integer peak on mean-removed windows,
    # B linearly interpolated along theta. A 3-point parabola on the NCC peak locks to the
    # integer by up to a quarter cell (measured in the self-test); the gradient step does not.
    frac = lk_refine(Az, va, Bz, vb, pad + d0, h)
    shift = np.where(matchable, d0 + np.clip(frac, -1.0, 1.0), np.nan)
    peak = np.where(matchable, pk, np.nan)
    return shift, peak, matchable


def lk_refine(Az, va, Bz, vb, off: np.ndarray, h: int, iters: int = 2) -> np.ndarray:
    """Fractional shift per cell of A: minimise sum over the window of (B(j + off + f) - A(j))^2
    with B interpolated linearly, both windows mean-removed. off is the per-cell integer offset
    (pad + d0) so that column j of A is matched to column j + off of B."""
    J, W = Az.shape[0], Bz.shape[1]
    rr, cc = np.indices((J, J))
    offs = [(dr, dj) for dr in range(-h, h + 1) for dj in range(-h, h + 1)]
    def gather(Xz, vX, colshift):
        vals, valid = [], []
        for dr, dj in offs:
            col = cc + off + dj + colshift
            r = np.clip(rr + dr, 0, J - 1); c = np.clip(col, 0, W - 1)
            inside = (rr + dr >= 0) & (rr + dr < J) & (col >= 0) & (col < W)
            vals.append(Xz[r, c]); valid.append(vX[r, c] & inside)
        return np.stack(vals), np.stack(valid)
    def gatherA():
        vals, valid = [], []
        for dr, dj in offs:
            r = np.clip(rr + dr, 0, J - 1); c = np.clip(cc + dj, 0, J - 1)
            inside = (rr + dr >= 0) & (rr + dr < J) & (cc + dj >= 0) & (cc + dj < J)
            vals.append(Az[r, c]); valid.append(va[r, c] & inside)
        return np.stack(vals), np.stack(valid)
    a, vA = gatherA()
    bm, vm = gather(Bz, vb, -1); b0, v0 = gather(Bz, vb, 0); bp, vp = gather(Bz, vb, 1)
    f = np.zeros((J, J))
    for _ in range(iters):
        fpos = f >= 0
        # B at fractional offset f: between b0 and bp for f >= 0, between bm and b0 for f < 0
        b = np.where(fpos, b0 + f * (bp - b0), b0 + f * (b0 - bm))
        g = np.where(fpos, bp - b0, b0 - bm)                  # local slope, per cell
        V = vA & v0 & np.where(fpos, vp, vm)
        n = V.sum(0)
        with np.errstate(invalid="ignore", divide="ignore"):
            am = np.where(V, a, 0.0).sum(0) / n; bmn = np.where(V, b, 0.0).sum(0) / n
            ar, br = np.where(V, a - am, 0.0), np.where(V, b - bmn, 0.0)
            gg = np.where(V, g, 0.0)
            step = (gg * (ar - br)).sum(0) / (gg * gg).sum(0)
        f = f + np.clip(np.nan_to_num(step), -0.5, 0.5)
    return f


def gradient_theta(M: np.ndarray, cell: float) -> np.ndarray:
    """Central differences along columns (theta), per degree; NaN where a neighbour is missing."""
    g = np.full_like(M, np.nan)
    g[:, 1:-1] = (M[:, 2:] - M[:, :-2]) / (2.0 * cell)
    return g


def signal_information(g: np.ndarray, sig_a: float, sig_b: float, cell: float, k: float = 2.0) -> np.ndarray:
    """Per-cell Fisher information of a shift, g^2 / (sig_a^2 + sig_b^2), with the noise's own
    contribution to the gradient removed: a central difference of white noise has variance
    sig_a^2 / (2 cell^2), which would count as information on a flat surface (measured on the
    stub: a striped card got a 0.5-cell bound from noise alone). Only gradients above k sigma of
    that count, and the noise variance is subtracted from them."""
    var_g = sig_a ** 2 / (2.0 * cell ** 2)
    g2 = np.where(np.isfinite(g), g ** 2, 0.0)
    return np.where(g2 > (k ** 2) * var_g, g2 - var_g, 0.0) / (sig_a ** 2 + sig_b ** 2)


def window_range(X: np.ndarray, h: int) -> np.ndarray:
    """Max minus min of X over each cell's (2h+1)^2 window, NaNs ignored (inf where all NaN)."""
    J = X.shape[0]
    P = np.pad(X, h, constant_values=np.nan)
    mx = np.full((J, J), -np.inf); mn = np.full((J, J), np.inf)
    for dr in range(2 * h + 1):
        for dj in range(2 * h + 1):
            w = P[dr:dr + J, dj:dj + J]
            mx = np.fmax(mx, w); mn = np.fmin(mn, w)
    return mx - mn


def window_sum(X: np.ndarray, h: int) -> np.ndarray:
    Xz = np.nan_to_num(X)
    P = np.pad(Xz, h + 1); C = P.cumsum(0).cumsum(1); J = X.shape[0]
    return (C[2 * h + 1:, 2 * h + 1:] - C[:-2 * h - 1, 2 * h + 1:] - C[2 * h + 1:, :-2 * h - 1] + C[:-2 * h - 1, :-2 * h - 1])[:J, :J]


# ----------------------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------------------

def self_test(seed: int = 0) -> list[str]:
    """The instrument on synthetic maps: a smooth random texture, R = L shifted by a fractional
    number of cells (Fourier shift) plus white noise. Recovered shift must be right to a tenth
    of a cell, gross errors (> 1 cell, a wrong NCC peak) must stay under 5%, and the inlier RMS
    must sit within a factor of the bound: the bound must not exceed it (that would be a wrong
    bound) and the matcher must not be worse than 3x (that would be a broken matcher). Each of
    these can fail."""
    fails = []
    rng = np.random.default_rng(seed)
    J, h, S, cell = 41, 2, 12, 0.2
    # smooth texture: low-pass filtered noise, positive
    base = rng.normal(size=(J, J + 40))
    kx = np.fft.fftfreq(base.shape[1]); ky = np.fft.fftfreq(base.shape[0])[:, None]
    F = np.fft.fft2(base) * np.exp(-((kx ** 2 + ky ** 2) / (2 * 0.08 ** 2)))
    tex = np.real(np.fft.ifft2(F)); tex = 1.0 + tex / tex.std() * 0.3
    for true_shift, sigma in ((4.0, 0.01), (-2.3, 0.01), (0.4, 0.03)):
        # the matcher's convention: L[r, j] ~ R[r, j + d]. So R[r, j] = L[r, j - d]: the texture
        # moved by +d along columns, f(x - d) <-> F exp(-2 pi i w d)
        Fw = np.fft.fft(tex, axis=1); w = np.fft.fftfreq(tex.shape[1])
        shifted = np.real(np.fft.ifft(Fw * np.exp(-2j * np.pi * w * true_shift)[None, :], axis=1))
        Lm = tex[:, 20:20 + J] + rng.normal(0, sigma, (J, J))
        Rm = shifted[:, 20 - S:20 + J + S] + rng.normal(0, sigma, (J, J + 2 * S))       # wider by S each side
        sh, _, mt = ncc_match(Lm, Rm, h, S, 0.02)
        inner = np.zeros((J, J), bool); inner[h:J - h, :] = True                            # rows whose window is inside
        ok = mt & inner & np.isfinite(sh)
        if not ok.any():
            fails.append(f"shift {true_shift}: no matchable cells"); continue
        err = sh[ok] - true_shift
        gross = np.abs(err) > 1.0                                   # the instrument reports inliers and gross separately
        rms = float(np.sqrt(np.mean(err[~gross] ** 2)))
        if abs(float(np.median(sh[ok])) - true_shift) > 0.1:
            fails.append(f"shift {true_shift}: recovered median {float(np.median(sh[ok])):.3f}")
        if gross.mean() > 0.05:
            fails.append(f"shift {true_shift}, sigma {sigma}: gross fraction {100 * gross.mean():.1f}%")
        I = window_sum(signal_information(gradient_theta(Lm, cell), sigma, sigma, cell), h)
        bound = float(np.sqrt(np.mean(1.0 / I[ok]))) / cell             # in cells
        if bound > rms * 1.05:
            fails.append(f"shift {true_shift}, sigma {sigma}: bound {bound:.4f} cells above the achieved RMS {rms:.4f}")
        if rms > 3.0 * bound:
            fails.append(f"shift {true_shift}, sigma {sigma}: RMS {rms:.4f} cells more than 3x the bound {bound:.4f}")
    return fails


def load(fdir: str, with_b: bool):
    s = np.load(os.path.join(fdir, "samples.npz")); t = np.load(os.path.join(fdir, "truth.npz"))
    out = {"dir": s["direction"].astype(np.float64), "val": s["value"].astype(np.float64).mean(-1),
           "fp": s["footprint"].astype(np.float64), "hit": s["distance"] < 1e9,
           "theta": t["theta"].astype(np.float64), "phi": t["phi"].astype(np.float64),
           "parallax": t["parallax"].astype(np.float64), "visible": t["other_visible"],
           "hit_world": t["hit_world"].astype(np.float64)}
    pb = os.path.join(fdir, "samples_b.npz")
    out["val_b"] = np.load(pb)["value"].astype(np.float64).mean(-1) if (with_b and os.path.exists(pb)) else None
    return out


def main():
    if "--self-test" in sys.argv:
        f = self_test()
        for x in f:
            print("[stereo] FAIL", x)
        print(f"[stereo] self-test {'FAILED' if f else 'ok'}")
        sys.exit(1 if f else 0)
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--eval-factor", type=float, default=2.0, help="s_eval = eval_factor x s0 (D9)")
    ap.add_argument("--fovea-deg", type=float, default=2.0, help="half-width of the map about each gaze")
    ap.add_argument("--finest-factor", type=float, default=1.5)
    ap.add_argument("--window", type=int, default=2, help="h: NCC window is (2h+1)^2 cells")
    ap.add_argument("--search", type=int, default=12, help="S: shifts in [-S, S] cells")
    ap.add_argument("--texture-min", type=float, default=0.03, help="relative std of the L window below which a cell is not matchable")
    ap.add_argument("--bound-max", type=float, default=1.0, help="cells: a window whose bound exceeds this has no shift information along theta and is not matchable")
    ap.add_argument("--noise-rel", type=float, default=None, help="assumed per-pixel relative RMS at the fixation spp when the run has no seed pair")
    ap.add_argument("--self-shift", type=int, default=3)
    ap.add_argument("--self-frac", type=float, default=0.99)
    ap.add_argument("--bound-slack", type=float, default=1.0)
    ap.add_argument("--card-cells", type=int, default=2, help="(m): median over the (2c+1)^2 central cells")
    ap.add_argument("--centre-min-cells", type=int, default=20, help="(m) is judged only with at least this many judged edge-free cells on the fixated surface")
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--sheet-pairs", type=int, default=6)
    args = ap.parse_args()

    run = os.path.abspath(args.run)
    pj = json.load(open(os.path.join(run, "pairs.json")))
    verged = bool(pj["verged"])
    s0 = float(pj["warp"]["s0_deg"]); cell = args.eval_factor * s0
    ipd = float(pj["rig"]["ipd_m"])
    n_inside = int(pj["samples_per_fixation"])
    rays_per_pair = 2 * n_inside * int(pj["spp"])
    head_rot3 = np.array(pj["rig"]["head_rot3_world_from_local"], dtype=np.float64)
    centres = np.array(pj["rig"]["eye_centres_m"], dtype=np.float64)
    seed_pair = bool(pj.get("seed_pair", False))
    noise_mode = "measured (seed pair)" if seed_pair else f"assumed (--noise-rel {args.noise_rel})"
    if not seed_pair and args.noise_rel is None:
        raise SystemExit("run has no seed pair: pass --noise-rel <per-pixel rel RMS at the fixation spp> (assumed; manifest fixation_*_rel_rms_median)")
    h, S = args.window, args.search
    fails, per = [], []
    panels = []
    err_cards, bound_cards, info_pairs = [], [], []

    for pid, pair in enumerate(pj["pairs"]):
        L = load(os.path.join(run, "L", f"f{pid:03d}"), seed_pair)
        R = load(os.path.join(run, "R", f"f{pid:03d}"), seed_pair)
        gaze = [to_eye_frame(np.array([[0.0, 0.0, 1.0]]), g["yaw"], g["pitch"])[0] for g in pair["eyes"]]
        (thL, phL), (thR, phR) = epipolar(gaze[0]), epipolar(gaze[1])
        phi_c = 0.5 * (phL + phR); theta_mid = 0.5 * (thL + thR)
        gL = FoveaGrid(thL, phi_c, theta_mid, args.fovea_deg, cell)
        gR = FoveaGrid(thR, phi_c, theta_mid, args.fovea_deg, cell, extra_cols=S)   # wider along theta by the search range
        ML, covL, exL = accumulate(gL, L["theta"], L["phi"], L["val"], L["fp"], args.finest_factor,
                                   {"parallax": L["parallax"], "vis": (L["visible"] == 1).astype(float),
                                    "dist": np.linalg.norm(L["hit_world"] - centres[0], axis=-1)})
        MR, covR, _ = accumulate(gR, R["theta"], R["phi"], R["val"], R["fp"], args.finest_factor)   # J x (J + 2S)
        # noise per cell
        if seed_pair:
            MLb, _, _ = accumulate(gL, L["theta"], L["phi"], L["val_b"], L["fp"], args.finest_factor)
            MRb, _, _ = accumulate(gR, R["theta"], R["phi"], R["val_b"], R["fp"], args.finest_factor)
            sigL = float(np.sqrt(np.nanmean((ML - MLb) ** 2) / 2.0)); sigR = float(np.sqrt(np.nanmean((MR - MRb) ** 2) / 2.0))
        else:
            spc = max(1.0, (cell / s0) ** 2)                      # samples per cell at the centre
            sigL = float(args.noise_rel * np.nanmean(ML) / math.sqrt(spc)); sigR = float(args.noise_rel * np.nanmean(MR) / math.sqrt(spc))
        # the bound first: it also decides where a shift along theta is determinable at all
        g = gradient_theta(ML, cell)
        info_cell = signal_information(g, sigL, sigR, cell)
        I_win = window_sum(info_cell, h)
        with np.errstate(divide="ignore", invalid="ignore"):
            bound = np.where(I_win > 0, 1.0 / np.sqrt(I_win), np.nan)
        # the instrument. Matchable = window texture above the noise AND the bound within
        # --bound-max cells: a window with no gradient along theta (a horizontal stripe, the
        # aperture problem) has a fine NCC peak at every shift and must not be judged
        shift, peak, textured = ncc_match(ML, MR, h, S, args.texture_min, texture_abs=3.0 * math.sqrt(sigL ** 2 + sigR ** 2))
        matchable = textured & np.isfinite(bound) & (bound <= args.bound_max * cell)
        est = (thR - thL) + shift * cell                             # estimated parallax, deg
        truth = exL["parallax"]
        vis = exL["vis"] >= 0.5
        judged_cells = matchable & vis & np.isfinite(truth)
        err = est - truth
        # depth edges: cells whose window sees more than one cell of truth parallax spread; the
        # instrument's window straddles the surface boundary there (foreground fattening), so
        # they are reported apart from the edge-free cells
        edge = window_range(truth, h) > cell
        e = err[judged_cells]
        gross = np.abs(e) > cell
        inl = e[~gross]
        e_free = err[judged_cells & ~edge]; gross_free = np.abs(e_free) > cell
        # depth error via triangulation on the estimate vs the truth
        thL_cells = np.broadcast_to(gL.theta_of_col(np.arange(gL.J))[None, :], (gL.J, gL.J))
        D_est = triangulate(thL_cells, thL_cells + est, ipd)[0]
        D_tru = exL["dist"]
        d_err = (D_est - D_tru)[judged_cells][~gross]
        b = bound[judged_cells]
        I_total = float(np.nansum(info_cell[covL]))
        rec = {"pair_id": pid, "name": pair["name"], "kind": pair["kind"], "judged": pair["kind"] in JUDGED_KINDS,
               "covered_L": float(covL.mean()), "covered_R": float(covR.mean()), "matchable_frac": float(matchable[covL].mean()) if covL.any() else 0.0,
               "judged_cells": int(judged_cells.sum()), "textured_frac": float(textured[covL].mean()) if covL.any() else 0.0, "sigma_L": sigL, "sigma_R": sigR,
               "gaze_parallax_deg": float(thR - thL), "truth_centre_parallax_deg": float(np.nanmedian(truth[gL.h - args.card_cells:gL.h + args.card_cells + 1, gL.h - args.card_cells:gL.h + args.card_cells + 1])),
               "inlier_rms_deg": float(np.sqrt(np.mean(inl ** 2))) if len(inl) else None,
               "all_rms_deg": float(np.sqrt(np.mean(e ** 2))) if len(e) else None,
               "gross_frac": float(gross.mean()) if len(e) else None,
               "edge_frac": float(edge[judged_cells].mean()) if judged_cells.any() else None,
               "gross_frac_edge_free": float(gross_free.mean()) if len(e_free) else None,
               "inlier_rms_deg_edge_free": float(np.sqrt(np.mean(e_free[~gross_free] ** 2))) if (~gross_free).any() else None,
               "bias_deg": float(np.mean(inl)) if len(inl) else None,
               "depth_inlier_rms_m": float(np.sqrt(np.mean(d_err ** 2))) if len(d_err) else None,
               "bound_rms_deg": float(np.sqrt(np.nanmean(b ** 2))) if np.isfinite(b).any() else None,
               "info_total": I_total, "info_per_ray": I_total / rays_per_pair}
        if rec["inlier_rms_deg"] and rec["bound_rms_deg"]:
            rec["rms_over_bound"] = rec["inlier_rms_deg"] / rec["bound_rms_deg"]
        # (m) recovery on the fixated surface: the truth parallax at the centre block names the
        # surface; every judged edge-free cell of the map whose truth is within half a cell of it
        # belongs to that surface; the median estimate over them must match the median truth
        c = slice(gL.h - args.card_cells, gL.h + args.card_cells + 1)
        tc = truth[c, c][np.isfinite(truth[c, c])]
        t_surface = float(np.median(tc)) if len(tc) else float("nan")
        m_ok = judged_cells & ~edge & (np.abs(truth - t_surface) <= 0.5 * cell)
        rec["centre_truth_parallax_deg"] = t_surface
        rec["surface_cells_judged"] = int(m_ok.sum())
        rec["centre_est_median_deg"] = float(np.median(est[m_ok])) if m_ok.any() else None
        rec["centre_truth_median_deg"] = float(np.median(truth[m_ok])) if m_ok.any() else None
        rec["centre_judged"] = rec["judged"] and int(m_ok.sum()) >= args.centre_min_cells
        if rec["judged"] and not rec["centre_judged"]:
            rec["centre_note"] = f"only {int(m_ok.sum())} judged edge-free cells on the fixated surface (texture or depth edges): (m) not judged"
        if rec["centre_judged"]:
            if abs(rec["centre_est_median_deg"] - rec["centre_truth_median_deg"]) > cell:
                fails.append(f"p{pid:03d}: (m) fixated-surface parallax {rec['centre_est_median_deg']:.4f} vs truth {rec['centre_truth_median_deg']:.4f} deg (cell {cell:.3f}, {int(m_ok.sum())} cells)")
            if rec.get("rms_over_bound") is not None and rec["bound_rms_deg"] > args.bound_slack * rec["inlier_rms_deg"]:
                fails.append(f"p{pid:03d}: (n) bound {rec['bound_rms_deg']:.5f} deg above inlier RMS {rec['inlier_rms_deg']:.5f}")
            if len(e):
                err_cards.append(e); bound_cards.append(b[np.isfinite(b)]); info_pairs.append(rec["info_per_ray"])
        per.append(rec)
        if args.sheet and len(panels) < args.sheet_pairs:
            panels.append((f"p{pid:03d} {pair['name']}", ML, MR[:, S:S + gL.J], np.where(judged_cells, truth, np.nan), np.where(judged_cells, est, np.nan), np.where(judged_cells, err, np.nan)))

    # (l) self-shift on the first judged pair's L map
    p0 = next(i for i, r in enumerate(per) if r["judged"])
    L0 = load(os.path.join(run, "L", f"f{p0:03d}"), False)
    g0 = to_eye_frame(np.array([[0.0, 0.0, 1.0]]), pj["pairs"][p0]["eyes"][0]["yaw"], pj["pairs"][p0]["eyes"][0]["pitch"])[0]
    th0, ph0 = epipolar(g0)
    grid0 = FoveaGrid(th0, ph0, th0, args.fovea_deg, cell, extra_cols=S)
    Mw, _, _ = accumulate(grid0, L0["theta"], L0["phi"], L0["val"], L0["fp"], args.finest_factor)   # wide L map
    k = args.self_shift
    A0 = Mw[:, S:S + grid0.J]                                            # the J x J centre
    Ms = np.full_like(Mw, np.nan); Ms[:, k:] = Mw[:, :-k]               # Ms[r, j] = Mw[r, j - k]: A0[r, j] ~ Ms[r, S + j + k]
    sh, _, mt = ncc_match(A0, Ms, h, S, args.texture_min)
    ok = np.isfinite(sh) & mt
    ok[:h, :] = False; ok[-h:, :] = False                                # rows whose window leaves the map
    # 0.25 cell: an integer shift's NCC peak is exact but its two neighbours are not symmetric, so the
    # parabola moves it by up to a quarter cell (pixel locking); a wrong peak is a whole cell or more
    self_frac = float((np.abs(sh[ok] - k) <= 0.25).mean()) if ok.any() else 0.0
    if self_frac < args.self_frac:
        fails.append(f"(l) self-shift by {k} cells recovered on {100 * self_frac:.1f}% of matchable cells")
    if not err_cards:
        fails.append("no judged cells on any card: nothing matchable (texture below 3 sigma of the noise, or the bound above one cell everywhere)")

    e_all = np.concatenate(err_cards) if err_cards else np.array([])
    b_all = np.concatenate(bound_cards) if bound_cards else np.array([])
    g_all = np.abs(e_all) > cell
    summary = {"run": run, "verged": verged, "s0_deg": s0, "cell_deg": cell, "fovea_deg": args.fovea_deg,
               "window": 2 * h + 1, "search_cells": S, "noise": noise_mode,
               "pairs": len(per), "judged_pairs": len(err_cards), "judged_cells": int(len(e_all)),
               "rays_per_pair": rays_per_pair, "samples_per_fixation": n_inside,
               "E2_deg": pj["warp"]["E2_deg"], "e_max_deg": pj["warp"]["e_max_deg"],
               "inlier_rms_deg": float(np.sqrt(np.mean(e_all[~g_all] ** 2))) if (~g_all).any() else None,
               "inlier_rms_cells": float(np.sqrt(np.mean(e_all[~g_all] ** 2)) / cell) if (~g_all).any() else None,
               "inlier_rms_s0": float(np.sqrt(np.mean(e_all[~g_all] ** 2)) / s0) if (~g_all).any() else None,
               "gross_frac": float(g_all.mean()) if len(e_all) else None,
               "gross_frac_edge_free_median": float(np.median([r["gross_frac_edge_free"] for r in per if r["judged"] and r["gross_frac_edge_free"] is not None])) if any(r["judged"] and r["gross_frac_edge_free"] is not None for r in per) else None,
               "inlier_rms_deg_edge_free_median": float(np.median([r["inlier_rms_deg_edge_free"] for r in per if r["judged"] and r["inlier_rms_deg_edge_free"] is not None])) if any(r["judged"] and r["inlier_rms_deg_edge_free"] is not None for r in per) else None,
               "centre_judged_pairs": int(sum(r.get("centre_judged", False) for r in per)),
               "centre_not_judged": [f"p{r['pair_id']:03d}" for r in per if r["judged"] and not r.get("centre_judged", False)],
               "bias_deg": float(np.mean(e_all[~g_all])) if (~g_all).any() else None,
               "bound_rms_deg": float(np.sqrt(np.mean(b_all ** 2))) if len(b_all) else None,
               "rms_over_bound_median": float(np.median([r["rms_over_bound"] for r in per if r.get("rms_over_bound")])) if any(r.get("rms_over_bound") for r in per) else None,
               "info_per_ray_median": float(np.median(info_pairs)) if info_pairs else None,
               "info_per_ray_mean": float(np.mean(info_pairs)) if info_pairs else None,
               "matchable_frac_median": float(np.median([r["matchable_frac"] for r in per if r["judged"]])),
               "self_shift_frac": self_frac, "fails": fails}
    with open(os.path.join(run, "stereo.json"), "w") as fh:
        json.dump({"summary": summary, "pairs": per}, fh, indent=1)
    for r in per:
        if r["inlier_rms_deg"] is None:
            print(f"[stereo] p{r['pair_id']:03d} {r['name']:<16} no judged cells (matchable {r['matchable_frac']:.2f})"); continue
        ce = f"surface est {r['centre_est_median_deg']:.3f} truth {r['centre_truth_median_deg']:.3f} ({r['surface_cells_judged']} cells)" if r["centre_est_median_deg"] is not None else "surface not matchable"
        gf = f"{100 * r['gross_frac_edge_free']:.1f}%" if r["gross_frac_edge_free"] is not None else "-"
        print(f"[stereo] p{r['pair_id']:03d} {r['name']:<16} {'' if r['judged'] else '(reported) '}cells {r['judged_cells']:4d} "
              f"inlier RMS {r['inlier_rms_deg']:.4f} deg ({r['inlier_rms_deg'] / cell:.2f} cells) gross {100 * r['gross_frac']:.1f}% "
              f"(edge-free {gf}, edges {100 * r['edge_frac']:.0f}%)  bound {r['bound_rms_deg']:.4f}  ratio {r.get('rms_over_bound', float('nan')):.2f}  "
              f"{ce}  info/ray {r['info_per_ray']:.3e}")
    def fmt(x, f=".4f"):
        return "-" if x is None else format(x, f)
    print(f"[stereo] {'verged' if verged else 'CONTROL (vergence off)'} E2 {summary['E2_deg']} e_max {summary['e_max_deg']}: "
          f"{summary['judged_pairs']} judged pairs, {summary['judged_cells']} cells; inlier RMS {fmt(summary['inlier_rms_deg'])} deg "
          f"= {fmt(summary['inlier_rms_cells'], '.2f')} cells = {fmt(summary['inlier_rms_s0'], '.2f')} s0; gross {fmt(None if summary['gross_frac'] is None else 100 * summary['gross_frac'], '.1f')}%; "
          f"bias {fmt(summary['bias_deg'], '+.4f')}; bound RMS {fmt(summary['bound_rms_deg'])} deg; RMS/bound median {fmt(summary['rms_over_bound_median'], '.2f')}; "
          f"info/ray median {fmt(summary['info_per_ray_median'], '.3e')}; rays/pair {rays_per_pair}; noise {noise_mode}; self-shift {100 * self_frac:.1f}%")
    print(f"[stereo] edge-free cells: inlier RMS median {fmt(summary['inlier_rms_deg_edge_free_median'])} deg, gross median {fmt(summary['gross_frac_edge_free_median'], '.3f')}; "
          f"(m) judged on {summary['centre_judged_pairs']} pairs" + (f", not judged: {' '.join(summary['centre_not_judged'])}" if summary['centre_not_judged'] else ""))
    for f in fails:
        print("[stereo] FAIL", f)

    if args.sheet and panels:
        from PIL import Image, ImageDraw
        sc = 10
        J = panels[0][1].shape[0]; sz = J * sc
        cols = 5
        im = Image.new("RGB", (cols * (sz + 6) + 6, len(panels) * (sz + 20) + 6), (30, 30, 30)); dr = ImageDraw.Draw(im)
        vmax = float(np.nanpercentile(np.concatenate([p[1].ravel() for p in panels] + [p[2].ravel() for p in panels]), 99))
        pmax = float(max(np.nanmax(np.abs(np.nan_to_num(p[3], nan=0.0))) for p in panels)) or 1.0
        emax_ = cell
        def panel(M, kind):
            a = np.zeros((J, J, 3), np.uint8)
            if kind == "map":
                v = np.clip(np.nan_to_num(M / max(vmax, 1e-6)), 0, 1) ** (1 / 2.2); a[...] = (v * 255)[..., None]
            elif kind == "par":
                v = np.clip(np.nan_to_num(M / pmax), 0, 1); a[..., 0] = v * 255; a[..., 1] = v * 128; a[..., 2] = (1 - v) * 255
            else:
                v = np.clip(np.nan_to_num(M / emax_), -1, 1); a[..., 0] = np.clip(v, 0, 1) * 255; a[..., 2] = np.clip(-v, 0, 1) * 255; a[..., 1] = (1 - np.abs(v)) * 100
            a[~np.isfinite(M)] = (40, 40, 40)
            return Image.fromarray(a).resize((sz, sz), Image.NEAREST)
        for i, (label, ML, MR, tr, es, er) in enumerate(panels):
            y = 6 + i * (sz + 20)
            for j, (M, kind, t) in enumerate(((ML, "map", "L"), (MR, "map", "R"), (tr, "par", "truth parallax"), (es, "par", "estimate"), (er, "err", f"error (+-{cell:.2f} deg)"))):
                x = 6 + j * (sz + 6)
                im.paste(panel(M, kind), (x, y + 14)); dr.text((x, y), f"{label} {t}" if j == 0 else t, fill=(230, 230, 230))
        im.save(os.path.join(run, "stereo_sheet.png"))
        print(f"[stereo] sheet -> {os.path.join(run, 'stereo_sheet.png')}")
    print(f"[stereo] {'FAILED' if fails else 'ok'} ({len(fails)} failures) -> {os.path.join(run, 'stereo.json')}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
