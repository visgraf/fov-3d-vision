"""The stereo field (C1, D17): the B3 instrument extended over the whole disc a pair covers,
at the scale the samples support there, returning per cell an inverse-depth measurement with
its variance. Numpy only (no OpenEXR, no bpy): the C2 loop imports `field_of_pair` inside the
Blender session; this file's main() is the host-side check against truth.npz.

    .venv/bin/python tools/stereo_field.py previews/pairs/calib_room_sp --sheet
    .venv/bin/python tools/stereo_field.py previews/pairs/calib_room_control --sheet
    .venv/bin/python tools/stereo_field.py --self-test

Levels. The warp's spacing is s(e) = s0 (1 + e/E2), so a grid at one cell size is right for one
band of eccentricity. Level l has cell c_l = eval_factor x s0 x 2^l (D9's s_eval at l = 0) and
owns the cells whose eccentricity from the L gaze lies in (e_{l-1}, e_l] with
e_l = E2 (eval_factor 2^l - 1): the band where one cell holds at least one sample spacing. At
the standard warp (E2 2, e_max 45, eval_factor 2) that is 2, 6, 14, 30, 62 deg for l = 0..4 —
five grids of a few hundred to a thousand cells each, because a log-polar warp has about the
same number of cells per octave. Level 0 within 2 deg is the B3 instrument's map exactly.

Per level: both eyes' samples are integrated finest-owns onto a local epipolar grid about each
eye's own gaze (rows phi, columns theta), the L map is NCC-matched against the R map along the
row over shifts within --search-deg (B3's matcher, ncc_match + two Lucas-Kanade steps), and the
R map against the L map; a cell is CONSISTENT when the two shifts agree within
--lr-tol cells (left-right consistency, bioeye's validity test). Parallax = (theta_gaze_R -
theta_gaze_L) + shift x cell; its variance is (kappa x bound)^2 with the bound 1/sqrt(I) from
B3's Fisher information over the window and kappa the instrument's measured RMS/bound ratio
(--kappa; B3 measured 2.5 at small, 3.8 at full). Inverse depth rho = 1/|P - C_L| follows by the
sine rule, rho = sin p / (ipd sin(theta_L + p)), and its variance by the exact Jacobian
d rho / d p = sin theta_L / (ipd sin^2(theta_L + p)).

Output per pair, <run>/field/p<NNN>.npz, one row per owned matchable cell:
    dir            (M,3)  head-frame unit direction of the cell centre (from L)
    theta_L, phi   (M,)   deg
    level          (M,)   int8;  cell_deg (M,)
    parallax_deg   (M,)   estimate;  sigma_p_deg (M,)  sqrt((kappa bound)^2 + (floor cell)^2);  bound_deg (M,)
    rho            (M,)   1/m;  sigma_rho (M,)  1/m
    consistent     (M,)   bool, LR consistency
    truth_parallax_deg, truth_rho, truth_visible (M,)  when truth.npz exists (NaN / -1 else)
and <run>/field.json with the per-pair and per-level statistics and the checks.

Checks (host side, truth.npz present), each of which can fail (exit 1):
  (o) ownership   every covered cell of the disc within e_max - margin is owned by exactly one
                  level; owned fraction >= --own-min of covered.
  (p) regression  level 0's inlier RMS at the fixated cards is within --fovea-tol of
                  stereo.json's instrument inlier RMS on the same run (skipped, and said so,
                  without stereo.json): the field is the instrument where they overlap.
  (q) bound       per level with >= --level-min-cells judged cells, bound RMS <= inlier RMS
                  (a bound that is a bound); the measured RMS/bound per level is REPORTED as the
                  kappa C2 should use.
  (r) consistency the LR-consistent subset's gross fraction is below the matchable set's, on
                  every level with enough cells (the filter removes wrong peaks, not at random);
                  the fraction it rejects is reported. A filter that rejects nothing fails.
Reported: per level inlier RMS (deg, cells, s0), gross, bias, coverage, rho inlier RMS (1/m) and
depth RMS (m), calibration z = err / sigma (RMS over inliers, median |z|); per pair the same.
--sheet: a composite per pair at level-0 resolution: L radiance | parallax estimate | truth |
error | sigma, all levels drawn as blocks, for the first --sheet-pairs pairs.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rig import epipolar, to_eye_frame  # noqa: E402
from stereo_instrument import (FoveaGrid, accumulate, gradient_power_theta, ncc_match,  # noqa: E402
                               signal_information, window_range, window_sum)

JUDGED_KINDS = {"ring", "ladder", "point"}


# ----------------------------------------------------------------------------------------
# geometry
# ----------------------------------------------------------------------------------------

def direction_of(theta_deg, phi_deg) -> np.ndarray:
    """Inverse of rig.epipolar: head-frame unit direction of (theta, phi)."""
    t, p = np.radians(np.asarray(theta_deg, float)), np.radians(np.asarray(phi_deg, float))
    st = np.sin(t)
    return np.stack([np.cos(t), st * np.sin(p), -st * np.cos(p)], axis=-1)


def level_edges(E2: float, eval_factor: float, n_levels: int) -> np.ndarray:
    """e_l = E2 (eval_factor 2^l - 1), l = 0..n-1: the outer eccentricity each level owns."""
    return np.array([E2 * (eval_factor * 2.0 ** l - 1.0) for l in range(n_levels)])


def n_levels_for(E2: float, eval_factor: float, e_max: float) -> int:
    n = 1
    while level_edges(E2, eval_factor, n)[-1] < e_max:
        n += 1
    return n


def inverse_depth(theta_L_deg, parallax_deg, ipd_m):
    """rho = 1/|P - C_L| and d rho / d parallax (per radian), by the sine rule
    |P - C_L| = ipd sin(theta_R) / sin(parallax), theta_R = theta_L + parallax.
    parallax <= 0 (parallel or diverging) gives rho = 0 and the Jacobian at p = 0."""
    tl = np.radians(np.asarray(theta_L_deg, float)); p = np.radians(np.asarray(parallax_deg, float))
    tr = tl + p
    with np.errstate(divide="ignore", invalid="ignore"):
        rho = np.where(p > 0, np.sin(p) / (ipd_m * np.sin(tr)), 0.0)
        jac = np.sin(tl) / (ipd_m * np.sin(tr) ** 2)
    return rho, jac


def smooth_theta(X: np.ndarray) -> np.ndarray:
    """[1, 2, 1]/4 along columns (theta), NaN-aware (missing cells get no weight). Both maps are
    smoothed identically before matching: at the coarse levels a cell holds one or two samples,
    so the map has power up to the grid's Nyquist and the Lucas-Kanade step, which models the
    map as piecewise linear between cells, recovers only about half of a fractional shift
    (measured on the synthetic wall: bias +0.09 cells at level 4 for true shifts of -0.16, none
    on a wall at 20 m where the shift is ~0). One pass of smoothing halves that bias and lowers
    the level-0 RMS as well (0.14 -> 0.06 cells on the same wall)."""
    v = np.isfinite(X); Xz = np.where(v, X, 0.0); w = v.astype(float)
    P = np.pad(Xz, [(0, 0), (1, 1)]); Pw = np.pad(w, [(0, 0), (1, 1)])
    num = P[:, :-2] + 2.0 * P[:, 1:-1] + P[:, 2:]
    den = Pw[:, :-2] + 2.0 * Pw[:, 1:-1] + Pw[:, 2:]
    with np.errstate(invalid="ignore", divide="ignore"):
        S = num / den
    return np.where(v, S, np.nan)


# ----------------------------------------------------------------------------------------
# the field of one pair
# ----------------------------------------------------------------------------------------

def field_of_pair(L: dict, R: dict, gazeL: np.ndarray, gazeR: np.ndarray, s0: float, E2: float, e_max: float,
                  ipd_m: float, eval_factor: float = 2.0, search_deg: float = 3.0, window: int = 2,
                  texture_min: float = 0.03, bound_max_cells: float = 1.0, kappa: float = 2.5,
                  lr_tol_cells: float = 1.0, finest_factor: float = 1.5, noise_rel: float | None = None,
                  margin_deg: float = 2.0, axis_deg: float = 5.0, min_valid: float = 0.6,
                  smooth: bool = True, floor_cells: float = 0.3, lr: bool = True, extras: dict | None = None) -> dict:
    """L, R: dicts with 'theta', 'phi' (epipolar, deg), 'val' (N,), 'fp' (N,) sr, optional
    'val_b' (seed pair). gazeL/R: head-frame unit gaze directions. Returns the measurement rows
    (see module docstring) plus per-level diagnostics under 'levels' and, if extras is given
    ({'name': per-sample array of L}), their finest-owns cell means as 'x_<name>'."""
    (thL, phL), (thR, phR) = epipolar(gazeL), epipolar(gazeR)
    phi_c, theta_mid = 0.5 * (phL + phR), 0.5 * (thL + thR)
    edges = level_edges(E2, eval_factor, n_levels_for(E2, eval_factor, e_max))
    h = window
    rows = {k: [] for k in ("dir", "theta_L", "phi", "level", "cell_deg", "parallax_deg", "sigma_p_deg", "bound_deg", "rho", "sigma_rho", "consistent", "ecc_deg", "row", "col")}
    for k in (extras or {}):
        rows["x_" + k] = []
    levels = []
    e_lo = 0.0
    for l, e_hi in enumerate(edges):
        cell = eval_factor * s0 * 2.0 ** l
        S = max(1, int(math.ceil(search_deg / cell)))
        half = min(e_hi, e_max) + margin_deg + (h + 1) * cell
        gL = FoveaGrid(thL, phi_c, theta_mid, half, cell, extra_cols=S)
        gR = FoveaGrid(thR, phi_c, theta_mid, half, cell, extra_cols=S)
        ex = {k: v for k, v in (extras or {}).items()}
        ML, covL, exL = accumulate(gL, L["theta"], L["phi"], L["val"], L["fp"], finest_factor, ex)
        MR, covR, _ = accumulate(gR, R["theta"], R["phi"], R["val"], R["fp"], finest_factor)
        # noise per level: measured from the seed pair, else assumed from --noise-rel and the
        # samples per cell in this level's owned band (at least one spacing per cell by construction)
        if L.get("val_b") is not None and R.get("val_b") is not None:
            MLb, _, _ = accumulate(gL, L["theta"], L["phi"], L["val_b"], L["fp"], finest_factor)
            MRb, _, _ = accumulate(gR, R["theta"], R["phi"], R["val_b"], R["fp"], finest_factor)
            sigL = float(np.sqrt(np.nanmean((ML - MLb) ** 2) / 2.0)); sigR = float(np.sqrt(np.nanmean((MR - MRb) ** 2) / 2.0))
            noise = "measured"
        else:
            if noise_rel is None:
                raise ValueError("no seed pair in the run: pass noise_rel (assumed per-pixel relative RMS)")
            spc = max(1.0, (cell / (s0 * (1.0 + e_lo / E2))) ** 2)
            sigL = float(noise_rel * np.nanmean(ML) / math.sqrt(spc)); sigR = float(noise_rel * np.nanmean(MR) / math.sqrt(spc))
            noise = "assumed"
        # the centre J x J of each wide map is the grid proper; the wide map is the search partner
        J, W = gL.J, gL.W
        c0 = S
        if smooth:
            ML, MR = smooth_theta(ML), smooth_theta(MR)
            sigL, sigR = sigL * math.sqrt(6.0) / 4.0, sigR * math.sqrt(6.0) / 4.0     # [1,2,1]/4 on white noise
        AL, AR = ML[:, c0:c0 + J], MR[:, c0:c0 + J]
        info_cell = signal_information(gradient_power_theta(AL, cell), sigL, sigR, cell)
        I_win = window_sum(info_cell, h)
        with np.errstate(divide="ignore", invalid="ignore"):
            bound = np.where(I_win > 0, 1.0 / np.sqrt(I_win), np.nan)                  # deg
        tabs = 3.0 * math.sqrt(sigL ** 2 + sigR ** 2)
        sh_lr, _, tx_lr = ncc_match(AL, MR, h, S, texture_min, min_valid=min_valid, texture_abs=tabs)
        sh_rl, _, tx_rl = ncc_match(AR, ML, h, S, texture_min, min_valid=min_valid, texture_abs=tabs)
        matchable = tx_lr & np.isfinite(sh_lr) & np.isfinite(bound) & (bound <= bound_max_cells * cell)
        # LR consistency: the R cell that L cell (r, j) matched, j + d, must match back to j
        rr, cc = np.indices((J, J))
        jr = np.clip(np.rint(np.nan_to_num(sh_lr)).astype(int) + cc, 0, J - 1)
        back = sh_rl[rr, jr]
        consistent = matchable & np.isfinite(back) & (np.abs(sh_lr + back) <= lr_tol_cells) if lr else matchable.copy()
        # ownership by eccentricity from the L gaze, per cell centre
        th_cells = gL.theta_of_col(np.arange(c0, c0 + J))[None, :] + np.zeros((J, 1))
        ph_cells = phi_c + (np.arange(J) - gL.h)[:, None] * gL.dphi + np.zeros((1, J))
        d_cells = direction_of(th_cells, ph_cells)
        ecc = np.degrees(np.arccos(np.clip(d_cells @ gazeL, -1.0, 1.0)))
        own = (ecc > e_lo) & (ecc <= min(e_hi, e_max)) & covL[:, c0:c0 + J]
        own &= (th_cells > axis_deg) & (th_cells < 180.0 - axis_deg)
        par = (thR - thL) + sh_lr * cell
        sig_p = np.sqrt((kappa * bound) ** 2 + (floor_cells * cell) ** 2)       # noise term + the model floor
        rho, jac = inverse_depth(th_cells, par, ipd_m)
        sig_rho = np.abs(jac) * np.radians(sig_p)
        sel = own & matchable
        sr_cell = (math.radians(cell) ** 2) * np.sin(np.radians(th_cells)) / max(math.sin(math.radians(theta_mid)), 1e-6)   # cell solid angle, sr
        levels.append({"owned_sr": float(sr_cell[own].sum()),"level": l, "cell_deg": cell, "e_lo_deg": e_lo, "e_hi_deg": float(min(e_hi, e_max)), "grid": [J, W], "search_cells": S,
                       "sigma_L": sigL, "sigma_R": sigR, "noise": noise,
                       "covered": int(covL[:, c0:c0 + J].sum()), "owned": int(own.sum()), "matchable": int(sel.sum()),
                       "consistent": int((sel & consistent).sum()),
                       "maps": (AL, AR, own, matchable, consistent, par, sig_p, exL, gL, c0)})
        rows["dir"].append(d_cells[sel]); rows["theta_L"].append(th_cells[sel]); rows["phi"].append(ph_cells[sel])
        rows["level"].append(np.full(int(sel.sum()), l, np.int8)); rows["cell_deg"].append(np.full(int(sel.sum()), cell))
        rows["parallax_deg"].append(par[sel]); rows["sigma_p_deg"].append(sig_p[sel]); rows["bound_deg"].append(bound[sel])
        rows["rho"].append(rho[sel]); rows["sigma_rho"].append(sig_rho[sel]); rows["consistent"].append(consistent[sel])
        rows["ecc_deg"].append(ecc[sel]); rows["row"].append(rr[sel]); rows["col"].append(cc[sel])
        for k in (extras or {}):
            rows["x_" + k].append(exL[k][:, c0:c0 + J][sel])
        e_lo = float(min(e_hi, e_max))
        if e_lo >= e_max:
            break
    out = {k: (np.concatenate(v) if v else np.zeros((0, 3) if k == "dir" else 0)) for k, v in rows.items()}
    out["levels"] = levels
    out["gaze"] = {"theta_L": float(thL), "theta_R": float(thR), "phi": float(phi_c)}
    return out


# ----------------------------------------------------------------------------------------
# self-test
# ----------------------------------------------------------------------------------------

def synthetic_pair(rng, s0: float = 0.1, E2: float = 2.0, emax: float = 45.0, ipd: float = 0.063, noise: float = 0.01) -> list[dict]:
    """Two eyes at +-ipd/2 on X verged on a textured fronto-parallel wall at 2 m (head frame -Z
    forward) with a 30 cm card at 1 m in front, sampled on the warp about that gaze; the self-
    test's scene and a fixture for anyone debugging the field. Returns [L, R] dicts with the
    fields field_of_pair reads plus 'gaze', 'dist' and 'rho' per sample."""
    from warp import raster_samples, raster_size
    n = raster_size(s0, E2, emax); rs = raster_samples(n, E2, emax)
    ins = rs["inside"]
    dcam, fp = rs["direction_cam"][ins], rs["footprint"][ins]
    head_o = np.zeros(3); C = np.array([[-ipd / 2, 0, 0], [ipd / 2, 0, 0]])
    P = np.array([0.0, 0.0, -2.0])                                              # fixate the wall at 2 m, head frame -Z forward
    # a non-periodic texture: 60 sinusoids at random frequencies (0.5-12 cycles/m), orientations
    # and phases. A periodic texture is an instrument that lies to a matcher (wrong-period peaks).
    fk = rng.uniform(0.5, 12.0, 60); ak = rng.uniform(0.3, 1.0, 60) / fk ** 0.5; ok_ = rng.uniform(0, np.pi, 60); pk = rng.uniform(0, 2 * np.pi, 60)
    def tex(x, y):
        u = x[:, None] * np.cos(ok_) + y[:, None] * np.sin(ok_)
        v = (ak * np.sin(2 * np.pi * fk * u + pk)).sum(1)
        return 1.0 + 0.3 * v / np.sqrt((ak ** 2).sum() / 2)
    eyes = []
    for k in range(2):
        los = P - C[k]; los /= np.linalg.norm(los)
        yaw = math.degrees(math.atan2(los[0], -los[2])); pitch = math.degrees(math.asin(los[1]))
        dh = to_eye_frame(dcam, yaw, pitch)
        # intersect with wall z = -2 and card z = -1, |x| < 0.15, |y| < 0.15
        tw = -2.0 / dh[:, 2]; tc = -1.0 / dh[:, 2]
        hw = C[k] + tw[:, None] * dh; hc = C[k] + tc[:, None] * dh
        on_card = (np.abs(hc[:, 0]) < 0.15) & (np.abs(hc[:, 1]) < 0.15) & (tc > 0)
        val = np.where(on_card, 0.5 + 0.5 * tex(hc[:, 0] * 3, hc[:, 1] * 3), tex(hw[:, 0], hw[:, 1]))
        ok = dh[:, 2] < 0
        hit = np.where(on_card[:, None], hc, hw)
        th, ph = epipolar(dh[ok])
        dist = np.linalg.norm(hit - C[k], axis=1)[ok]
        nz = rng.normal(0, noise, (2, ok.sum()))
        eyes.append({"theta": th, "phi": ph, "val": val[ok] + nz[0], "val_b": val[ok] + nz[1], "fp": fp[ok],
                     "gaze": to_eye_frame(np.array([[0.0, 0.0, 1.0]]), yaw, pitch)[0], "dist": dist, "rho": 1.0 / dist})
    return eyes


def self_test() -> list[str]:
    fails = []
    # inverse-depth Jacobian against a numerical derivative, and rho against the sine rule
    ipd = 0.063
    for thL, p in ((90.0, 1.8), (60.0, 0.9), (120.0, 3.0), (20.0, 0.5)):
        rho, jac = inverse_depth(thL, p, ipd)
        d = 1e-6
        num = (inverse_depth(thL, p + d, ipd)[0] - inverse_depth(thL, p - d, ipd)[0]) / (2 * math.radians(d))
        if abs(num - jac) > 1e-6 * abs(jac):
            fails.append(f"jacobian at theta {thL} p {p}: analytic {jac:.6e} numeric {num:.6e}")
        D = ipd * math.sin(math.radians(thL + p)) / math.sin(math.radians(p))
        if abs(1.0 / D - rho) > 1e-9 * rho:
            fails.append(f"rho at theta {thL} p {p}: {rho:.6e} vs 1/D {1/D:.6e}")
    # level edges: level 0 is the instrument's fovea; five levels reach e_max 45 at the standard warp
    e = level_edges(2.0, 2.0, n_levels_for(2.0, 2.0, 45.0))
    if abs(e[0] - 2.0) > 1e-9 or len(e) != 5 or e[-1] < 45.0:
        fails.append(f"level edges {e.tolist()}")
    # direction_of inverts epipolar
    rng = np.random.default_rng(0)
    d = rng.normal(size=(1000, 3)); d /= np.linalg.norm(d, axis=1, keepdims=True)
    t, p = epipolar(d)
    if np.abs(direction_of(t, p) - d).max() > 1e-9:
        fails.append("direction_of does not invert epipolar")
    # the synthetic pair (synthetic_pair): a wall at 2 m with a card at 1 m. Per level, on the
    # LR-consistent cells: the parallax error must be unbiased to 0.15 cells, at most 20% of the
    # wall cells may be off by more than half a cell, and the sigma model must be right within
    # 3x (z RMS in [0.3, 3]). The card's edge is the control for the LR test: cells within one
    # cell of the edge must be rejected more often than the rest. Each of these can fail.
    eyes = synthetic_pair(rng)
    s0, E2, emax = 0.1, 2.0, 45.0
    f = field_of_pair(eyes[0], eyes[1], eyes[0]["gaze"], eyes[1]["gaze"], s0, E2, emax, ipd, floor_cells=0.1, extras={"rho": eyes[0]["rho"]})   # the floor measured on this wall
    if len(f["rho"]) < 1000:
        fails.append(f"synthetic pair: only {len(f['rho'])} matchable cells")
    thL, thR = f["gaze"]["theta_L"], f["gaze"]["theta_R"]
    D = 1.0 / f["x_rho"]; P = np.array([-ipd / 2, 0, 0]) + D[:, None] * f["dir"]; dR = P - np.array([ipd / 2, 0, 0])
    tp = np.degrees(np.arctan2(np.hypot(dR[:, 1], dR[:, 2]), dR[:, 0])) - f["theta_L"]
    e_cells = (f["parallax_deg"] - tp) / f["cell_deg"]; z = (f["parallax_deg"] - tp) / f["sigma_p_deg"]
    # card edge in the L view: the card at 1 m spans |x|, |y| < 0.15 from C_L
    hit = np.array([-ipd / 2, 0, 0]) + D[:, None] * f["dir"]
    on_card = D < 1.5
    edge_dist = np.maximum(np.abs(hit[:, 0]), np.abs(hit[:, 1])) - 0.15                # m, negative inside
    near_edge = np.abs(edge_dist) < D * np.radians(f["cell_deg"])
    rej_edge = float((~f["consistent"])[near_edge].mean()) if near_edge.any() else 0.0
    rej_rest = float((~f["consistent"])[~near_edge].mean()) if (~near_edge).any() else 0.0
    if not rej_edge > rej_rest:
        fails.append(f"synthetic pair: LR consistency rejects {100 * rej_edge:.0f}% at the card edge vs {100 * rej_rest:.0f}% elsewhere")
    for lv in range(int(f["level"].max()) + 1):
        m = (f["level"] == lv) & f["consistent"]
        if m.sum() < 50:
            continue
        inl = m & (np.abs(e_cells) <= 0.5)
        wall = m & ~on_card & ~near_edge
        if wall.sum() >= 50 and (np.abs(e_cells[wall]) > 0.5).mean() > 0.2:
            fails.append(f"synthetic pair level {lv}: {100 * (np.abs(e_cells[wall]) > 0.5).mean():.0f}% of wall cells off by more than half a cell")
        if abs(float(np.mean(e_cells[inl]))) > 0.15:
            fails.append(f"synthetic pair level {lv}: bias {float(np.mean(e_cells[inl])):+.3f} cells")
        zr = float(np.sqrt(np.mean(z[inl] ** 2)))
        if not (0.3 <= zr <= 3.0):
            fails.append(f"synthetic pair level {lv}: z RMS {zr:.2f} (sigma model off by more than 3x)")
    return fails


# ----------------------------------------------------------------------------------------
# main: a run, the check against truth
# ----------------------------------------------------------------------------------------

def load(fdir: str, with_b: bool) -> dict:
    s = np.load(os.path.join(fdir, "samples.npz"))
    out = {"val": s["value"].astype(np.float64).mean(-1), "fp": s["footprint"].astype(np.float64)}
    tp = os.path.join(fdir, "truth.npz")
    if os.path.exists(tp):
        t = np.load(tp)
        out.update({"theta": t["theta"].astype(np.float64), "phi": t["phi"].astype(np.float64),
                    "parallax": t["parallax"].astype(np.float64), "visible": t["other_visible"].astype(np.float64),
                    "hit_world": t["hit_world"].astype(np.float64)})
    else:
        th, ph = epipolar(s["direction"].astype(np.float64))
        out.update({"theta": th, "phi": ph})
    pb = os.path.join(fdir, "samples_b.npz")
    out["val_b"] = np.load(pb)["value"].astype(np.float64).mean(-1) if (with_b and os.path.exists(pb)) else None
    return out


def main():
    if "--self-test" in sys.argv:
        f = self_test()
        for x in f:
            print("[field] FAIL", x)
        print(f"[field] self-test {'FAILED' if f else 'ok'}")
        sys.exit(1 if f else 0)
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--eval-factor", type=float, default=2.0)
    ap.add_argument("--search-deg", type=float, default=3.0)
    ap.add_argument("--window", type=int, default=2)
    ap.add_argument("--texture-min", type=float, default=0.03)
    ap.add_argument("--bound-max", type=float, default=1.0, help="cells")
    ap.add_argument("--kappa", type=float, default=2.5, help="sigma_p^2 = (kappa x bound)^2 + (floor x cell)^2; B3 measured kappa 2.5 small, 3.8 full")
    ap.add_argument("--floor-cells", type=float, default=0.3, help="model-error floor of the parallax estimate, in cells (the stub's walls measured 0.36-0.39 cells at levels 1-4)")
    ap.add_argument("--lr-tol", type=float, default=1.0, help="cells")
    ap.add_argument("--noise-rel", type=float, default=None)
    ap.add_argument("--axis-deg", type=float, default=5.0)
    ap.add_argument("--no-lr", action="store_true", help="negative for (r): no left-right consistency test")
    ap.add_argument("--own-min", type=float, default=0.9, help="(o): owned solid angle over the disc's")
    ap.add_argument("--fovea-tol", type=float, default=0.25)
    ap.add_argument("--level-min-cells", type=int, default=200)
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--sheet-pairs", type=int, default=4)
    args = ap.parse_args()

    run = os.path.abspath(args.run)
    pj = json.load(open(os.path.join(run, "pairs.json")))
    s0 = float(pj["warp"]["s0_deg"]); E2 = float(pj["warp"]["E2_deg"]); emax = float(pj["warp"]["e_max_deg"])
    ipd = float(pj["rig"]["ipd_m"]); seed_pair = bool(pj.get("seed_pair", False))
    centres = np.array(pj["rig"]["eye_centres_m"], dtype=np.float64)
    rays_per_pair = 2 * int(pj["samples_per_fixation"]) * int(pj["spp"])
    if not seed_pair and args.noise_rel is None:
        raise SystemExit("run has no seed pair: pass --noise-rel")
    stereo = None
    sp = os.path.join(run, "stereo.json")
    if os.path.exists(sp):
        stereo = json.load(open(sp))
    os.makedirs(os.path.join(run, "field"), exist_ok=True)
    fails, per, panels = [], [], []
    nlev = n_levels_for(E2, args.eval_factor, emax)
    acc = [{"err": [], "sig": [], "rho_err": [], "sig_rho": [], "d_err": [], "gross_match": [], "gross_cons": [], "bnd": [], "n_match": 0, "n_cons": 0, "covered": 0, "owned": 0, "bound": [], "z": []} for _ in range(nlev)]
    cell0 = args.eval_factor * s0
    has_truth = os.path.exists(os.path.join(run, "L", "f000", "truth.npz"))
    for pid, pair in enumerate(pj["pairs"]):
        L = load(os.path.join(run, "L", f"f{pid:03d}"), seed_pair)
        R = load(os.path.join(run, "R", f"f{pid:03d}"), seed_pair)
        gaze = [to_eye_frame(np.array([[0.0, 0.0, 1.0]]), g["yaw"], g["pitch"])[0] for g in pair["eyes"]]
        extras = None
        if has_truth:
            extras = {"parallax": L["parallax"], "vis": (L["visible"] == 1).astype(float),
                      "dist": np.linalg.norm(L["hit_world"] - centres[0], axis=-1)}
        f = field_of_pair(L, R, gaze[0], gaze[1], s0, E2, emax, ipd, eval_factor=args.eval_factor, search_deg=args.search_deg,
                          window=args.window, texture_min=args.texture_min, bound_max_cells=args.bound_max, kappa=args.kappa,
                          lr_tol_cells=args.lr_tol, noise_rel=args.noise_rel, axis_deg=args.axis_deg, floor_cells=args.floor_cells, lr=not args.no_lr, extras=extras)
        rec = {"pair_id": pid, "name": pair["name"], "kind": pair["kind"], "judged": pair["kind"] in JUDGED_KINDS,
               "cells": int(len(f["rho"])), "consistent": int(f["consistent"].sum()),
               "levels": [{k: v for k, v in lv.items() if k != "maps"} for lv in f["levels"]]}
        # (o) ownership over the whole disc: every covered cell of every level within e_max is
        # counted once by construction of the bands; what can fail is coverage of the bands
        # (o): owned solid angle over the disc's, 2 pi (1 - cos e_max) less the axis exclusion
        disc_sr = 2.0 * math.pi * (1.0 - math.cos(math.radians(emax)))
        rec["owned_of_covered"] = sum(lv["owned_sr"] for lv in f["levels"]) / disc_sr
        out = {k: v for k, v in f.items() if k not in ("levels", "gaze") and not k.startswith("x_")}
        if has_truth:
            tp = f["x_parallax"]; tv = f["x_vis"] >= 0.5; td = f["x_dist"]
            t_rho = 1.0 / td
            judged = tv & np.isfinite(tp)
            err = f["parallax_deg"] - tp
            gross = np.abs(err) > f["cell_deg"]
            out.update({"truth_parallax_deg": tp, "truth_rho": t_rho, "truth_visible": tv.astype(np.int8)})
            for lv in range(nlev):
                m = (f["level"] == lv) & judged
                if not m.any():
                    continue
                a = acc[lv]
                mc = m & f["consistent"]
                a["gross_match"].append(gross[m]); a["gross_cons"].append(gross[mc])
                inl = mc & ~gross
                a["err"].append(err[inl]); a["sig"].append(f["sigma_p_deg"][inl]); a["bnd"].append(f["bound_deg"][inl])
                a["rho_err"].append((f["rho"] - t_rho)[inl]); a["sig_rho"].append(f["sigma_rho"][inl])
                a["d_err"].append(((f["rho"] - t_rho) / t_rho ** 2)[inl])                 # depth error to first order, m
                a["z"].append(err[inl] / f["sigma_p_deg"][inl])
                a["covered"] += f["levels"][lv]["covered"]; a["owned"] += f["levels"][lv]["owned"]
            inl_all = judged & f["consistent"] & ~gross
            rec.update({"judged_cells": int(judged.sum()), "gross_frac_matchable": float(gross[judged].mean()) if judged.any() else None,
                        "gross_frac_consistent": float(gross[judged & f["consistent"]].mean()) if (judged & f["consistent"]).any() else None,
                        "inlier_rms_deg": float(np.sqrt(np.mean(err[inl_all] ** 2))) if inl_all.any() else None,
                        "rho_inlier_rms": float(np.sqrt(np.mean((f["rho"] - t_rho)[inl_all] ** 2))) if inl_all.any() else None,
                        "depth_inlier_rms_m": float(np.sqrt(np.mean(((f["rho"] - t_rho) / t_rho ** 2)[inl_all] ** 2))) if inl_all.any() else None,
                        "z_rms": float(np.sqrt(np.mean((err[inl_all] / f["sigma_p_deg"][inl_all]) ** 2))) if inl_all.any() else None})
            # level-0 at the fixated card, for (p)
            m0 = (f["level"] == 0) & inl_all & (f["ecc_deg"] <= 2.0)
            rec["level0_inlier_rms_deg"] = float(np.sqrt(np.mean(err[m0] ** 2))) if m0.any() else None
        np.savez_compressed(os.path.join(run, "field", f"p{pid:03d}.npz"), **out)
        per.append(rec)
        if args.sheet and len(panels) < args.sheet_pairs:
            panels.append((f"p{pid:03d} {pair['name']}", f, has_truth))
        print(f"[field] p{pid:03d} {pair['name']:<16} cells {rec['cells']:5d} consistent {rec['consistent']:5d} owned/covered {rec['owned_of_covered']:.3f}"
              + (f"  inlier RMS {rec['inlier_rms_deg']:.4f} deg gross {100 * rec['gross_frac_matchable']:.1f}% -> {100 * rec['gross_frac_consistent']:.1f}% after LR  rho RMS {rec['rho_inlier_rms']:.4f} /m  depth RMS {rec['depth_inlier_rms_m']:.3f} m  z RMS {rec['z_rms']:.2f}" if has_truth and rec.get("inlier_rms_deg") else ""))

    # checks
    own_frac = float(np.mean([r["owned_of_covered"] for r in per]))
    if own_frac < args.own_min:
        fails.append(f"(o) owned fraction of covered cells {own_frac:.3f} < {args.own_min}")
    level_stats = []
    if has_truth:
        for lv in range(nlev):
            a = acc[lv]
            e = np.concatenate(a["err"]) if a["err"] else np.array([])
            gm = np.concatenate(a["gross_match"]) if a["gross_match"] else np.array([])
            gc = np.concatenate(a["gross_cons"]) if a["gross_cons"] else np.array([])
            s = np.concatenate(a["sig"]) if a["sig"] else np.array([])
            bn = np.concatenate(a["bnd"]) if a["bnd"] else np.array([])
            re_ = np.concatenate(a["rho_err"]) if a["rho_err"] else np.array([])
            de = np.concatenate(a["d_err"]) if a["d_err"] else np.array([])
            z = np.concatenate(a["z"]) if a["z"] else np.array([])
            cell = cell0 * 2 ** lv
            st = {"level": lv, "cell_deg": cell, "judged_matchable": int(len(gm)), "judged_consistent": int(len(gc)), "inliers": int(len(e)),
                  "rejected_by_lr": float(1.0 - len(gc) / len(gm)) if len(gm) else None,
                  "gross_frac_matchable": float(gm.mean()) if len(gm) else None, "gross_frac_consistent": float(gc.mean()) if len(gc) else None,
                  "inlier_rms_deg": float(np.sqrt(np.mean(e ** 2))) if len(e) else None,
                  "inlier_rms_cells": float(np.sqrt(np.mean(e ** 2)) / cell) if len(e) else None,
                  "inlier_rms_s0": float(np.sqrt(np.mean(e ** 2)) / s0) if len(e) else None,
                  "bias_deg": float(np.mean(e)) if len(e) else None,
                  "bound_rms_deg": float(np.sqrt(np.mean(bn ** 2))) if len(bn) else None,
                  "kappa_measured": float(np.sqrt(np.mean(e ** 2)) / np.sqrt(np.mean(bn ** 2))) if len(bn) else None,
                  "floor_measured_cells": float(math.sqrt(max(np.mean(e ** 2) - args.kappa ** 2 * np.mean(bn ** 2), 0.0)) / cell) if len(bn) else None,
                  "rho_inlier_rms": float(np.sqrt(np.mean(re_ ** 2))) if len(re_) else None,
                  "depth_inlier_rms_m": float(np.sqrt(np.mean(de ** 2))) if len(de) else None,
                  "z_rms": float(np.sqrt(np.mean(z ** 2))) if len(z) else None, "z_median_abs": float(np.median(np.abs(z))) if len(z) else None}
            level_stats.append(st)
            if len(gm) >= args.level_min_cells:
                if st["bound_rms_deg"] is not None and st["bound_rms_deg"] > st["inlier_rms_deg"]:
                    fails.append(f"(q) level {lv}: bound {st['bound_rms_deg']:.5f} deg above the inlier RMS {st['inlier_rms_deg']:.5f}")
                if st["gross_frac_consistent"] is not None and not (st["gross_frac_consistent"] < st["gross_frac_matchable"]):
                    fails.append(f"(r) level {lv}: LR consistency does not lower the gross fraction ({100 * st['gross_frac_matchable']:.1f}% -> {100 * st['gross_frac_consistent']:.1f}%)")
                if st["rejected_by_lr"] is not None and st["rejected_by_lr"] <= 0.0:
                    fails.append(f"(r) level {lv}: LR consistency rejects nothing")
        if stereo is not None:
            ref = stereo["summary"].get("inlier_rms_deg")
            l0 = [r["level0_inlier_rms_deg"] for r in per if r["judged"] and r.get("level0_inlier_rms_deg")]
            if ref and l0:
                mine = float(np.sqrt(np.mean(np.square(l0))))
                rel = abs(mine - ref) / ref
                if rel > args.fovea_tol:
                    fails.append(f"(p) level 0 at the fixated cards {mine:.4f} deg vs the instrument's {ref:.4f} ({100 * rel:.0f}% apart, tol {100 * args.fovea_tol:.0f}%)")
                p_note = f"(p) level 0 {mine:.4f} vs instrument {ref:.4f} deg ({100 * rel:.0f}%)"
            else:
                p_note = "(p) not judged: no level-0 cells at the cards"
        else:
            p_note = "(p) skipped: no stereo.json in the run"
    else:
        p_note = "no truth.npz: field written, nothing judged"

    summary = {"run": run, "s0_deg": s0, "E2_deg": E2, "e_max_deg": emax, "eval_factor": args.eval_factor, "levels": nlev,
               "kappa_assumed": args.kappa, "floor_cells_assumed": args.floor_cells, "search_deg": args.search_deg, "window": 2 * args.window + 1, "lr_tol_cells": args.lr_tol,
               "rays_per_pair": rays_per_pair, "pairs": len(per), "owned_of_covered": own_frac,
               "cells_per_pair_median": float(np.median([r["cells"] for r in per])),
               "consistent_per_pair_median": float(np.median([r["consistent"] for r in per])),
               "per_level": level_stats, "p_note": p_note, "fails": fails}
    with open(os.path.join(run, "field.json"), "w") as fh:
        json.dump({"summary": summary, "pairs": per}, fh, indent=1)
    def fmt(x, f=".4f"):
        return "-" if x is None else format(x, f)
    for st in level_stats:
        print(f"[field] level {st['level']} cell {st['cell_deg']:.2f} deg: judged {st['judged_matchable']:6d}, LR rejects {fmt(None if st['rejected_by_lr'] is None else 100 * st['rejected_by_lr'], '.1f')}%, "
              f"gross {fmt(None if st['gross_frac_matchable'] is None else 100 * st['gross_frac_matchable'], '.1f')}% -> {fmt(None if st['gross_frac_consistent'] is None else 100 * st['gross_frac_consistent'], '.1f')}%, "
              f"inlier RMS {fmt(st['inlier_rms_deg'])} deg = {fmt(st['inlier_rms_cells'], '.2f')} cells = {fmt(st['inlier_rms_s0'], '.2f')} s0, bias {fmt(st['bias_deg'], '+.4f')}, "
              f"bound {fmt(st['bound_rms_deg'])} (RMS/bound {fmt(st['kappa_measured'], '.2f')}, floor {fmt(st['floor_measured_cells'], '.2f')} cells at kappa {args.kappa}), rho RMS {fmt(st['rho_inlier_rms'])} /m, depth RMS (1st order) {fmt(st['depth_inlier_rms_m'], '.3f')} m, z RMS {fmt(st['z_rms'], '.2f')} |z| median {fmt(st['z_median_abs'], '.2f')}")
    print(f"[field] {len(per)} pairs, {nlev} levels, cells/pair median {summary['cells_per_pair_median']:.0f} (consistent {summary['consistent_per_pair_median']:.0f}), owned/covered {own_frac:.3f}; {p_note}; rays/pair {rays_per_pair}")
    for f in fails:
        print("[field] FAIL", f)

    if args.sheet and panels:
        sheet(panels, os.path.join(run, "field_sheet.png"), cell0, emax, s0)
    print(f"[field] {'FAILED' if fails else 'ok'} ({len(fails)} failures) -> {os.path.join(run, 'field.json')}")
    sys.exit(1 if fails else 0)


def sheet(panels, path, cell0, emax, s0):
    """Composite per pair at level-0 resolution about the L gaze, every level drawn as blocks:
    L radiance | parallax estimate | truth | error in cells | sigma in cells. Axes: theta - thL
    across, phi - phi_c down (rows scaled by 1/sin theta_mid as the grids are)."""
    from PIL import Image, ImageDraw
    Npx = min(int(2 * (emax + 2.0) / cell0), 600); px_deg = Npx / (2 * (emax + 2.0))
    def blit(f, fn):
        canv = np.full((Npx, Npx), np.nan)
        for lv in f["levels"]:
            AL, AR, own, matchable, consistent, par, sig_p, exL, gL, c0 = lv["maps"]
            M = fn(AL, matchable, consistent, par, sig_p, exL, c0, lv["cell_deg"]); cell = lv["cell_deg"]
            w = max(1, int(round(cell * px_deg)))
            for r, c in zip(*np.nonzero(own & np.isfinite(M))):
                th = gL.theta_of_col(c0 + c) - gL.theta_c; ph = (r - gL.h) * gL.dphi
                x0 = int((th + emax + 2.0 - 0.5 * cell) * px_deg); y0 = int((-ph + emax + 2.0 - 0.5 * cell) * px_deg)
                canv[max(y0, 0):y0 + w, max(x0, 0):x0 + w] = M[r, c]
        return canv
    J_of = lambda AL: AL.shape[0]
    ims = []
    for label, f, has_truth in panels:
        rad = blit(f, lambda AL, m, cons, par, sp, ex, c0, cell: AL)
        est = blit(f, lambda AL, m, cons, par, sp, ex, c0, cell: np.where(m & cons, par, np.nan))
        sig = blit(f, lambda AL, m, cons, par, sp, ex, c0, cell: np.where(m & cons, sp / cell, np.nan))
        if has_truth:
            tru = blit(f, lambda AL, m, cons, par, sp, ex, c0, cell: np.where(ex["vis"][:, c0:c0 + J_of(AL)] >= 0.5, ex["parallax"][:, c0:c0 + J_of(AL)], np.nan))
            err = blit(f, lambda AL, m, cons, par, sp, ex, c0, cell: np.where(m & cons & (ex["vis"][:, c0:c0 + J_of(AL)] >= 0.5), (par - ex["parallax"][:, c0:c0 + J_of(AL)]) / cell, np.nan))
        else:
            tru = err = np.full((Npx, Npx), np.nan)
        ims.append((label, rad, est, tru, err, sig))
    vmax = float(np.nanpercentile(np.concatenate([i[1].ravel() for i in ims]), 99)) or 1.0
    pref = np.concatenate([(i[3] if np.isfinite(i[3]).any() else i[2]).ravel() for i in ims])
    plo, phi_ = (float(np.nanpercentile(pref, 2)), float(np.nanpercentile(pref, 98))) if np.isfinite(pref).any() else (0.0, 1.0)
    if phi_ <= plo:
        phi_ = plo + 1.0
    def to_img(M, kind):
        a = np.zeros((Npx, Npx, 3), np.uint8)
        if kind == "map":
            v = np.clip(np.nan_to_num(M / vmax), 0, 1) ** (1 / 2.2); a[...] = (v * 255)[..., None]
        elif kind == "par":
            v = np.clip(np.nan_to_num((M - plo) / (phi_ - plo)), 0, 1); a[..., 0] = v * 255; a[..., 1] = v * 128; a[..., 2] = (1 - v) * 255
        elif kind == "sig":
            v = np.clip(np.nan_to_num(M / 0.5), 0, 1); a[..., 1] = (1 - v) * 200; a[..., 0] = v * 255
        else:
            v = np.clip(np.nan_to_num(M / 0.5), -1, 1); a[..., 0] = np.clip(v, 0, 1) * 255; a[..., 2] = np.clip(-v, 0, 1) * 255; a[..., 1] = (1 - np.abs(v)) * 100
        a[~np.isfinite(M)] = (40, 40, 40)
        return Image.fromarray(a)
    cols = 5
    im = Image.new("RGB", (cols * (Npx + 6) + 6, len(ims) * (Npx + 20) + 6), (30, 30, 30)); dr = ImageDraw.Draw(im)
    for i, (label, rad, est, tru, err, sig) in enumerate(ims):
        y = 6 + i * (Npx + 20)
        for j, (M, kind, t) in enumerate(((rad, "map", "L radiance, all levels"), (est, "par", f"parallax estimate ({plo:.2f}..{phi_:.2f} deg)"), (tru, "par", "truth parallax"), (err, "err", "error (+-0.5 cell)"), (sig, "sig", "sigma_p (0..0.5 cell)"))):
            x = 6 + j * (Npx + 6)
            im.paste(to_img(M, kind), (x, y + 14)); dr.text((x, y), f"{label} {t}" if j == 0 else t, fill=(230, 230, 230))
    im.save(path)
    print(f"[field] sheet -> {path}")


if __name__ == "__main__":
    main()
