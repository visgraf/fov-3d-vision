"""Where the field's gross errors come from (D1's first step, D20) — host side, venv, no rendering.

    .venv/bin/python tools/gross_diagnosis.py previews/pairs/calib_room_full_sp
    .venv/bin/python tools/gross_diagnosis.py previews/loop3/class_coverage_full    # a loop run: stereo_truth.py on it first
    .venv/bin/python tools/gross_diagnosis.py --self-test

Rebuilds each saved pair's field (stereo_field.field_of_pair, with the settings the run used:
loop.json's on a loop run, field.json's on a pairs run) and carries the truth sidecar through
the same finest-owns accumulation, so every matchable cell gets, beside its estimate:

  the truth      cell means of the L samples' true parallax and inverse depth (1/ray distance),
                 the fraction of its samples the other eye sees (other_visible == 1), the
                 fraction that hit anything;
  a depth edge   a SAMPLE is on a depth edge when a 4-neighbour in the L raster differs from
                 it by more than --edge-jump (0.25) in inverse depth; a CELL is an edge cell
                 when it holds one. Judged per sample, not between cell means: a cell that
                 straddles two surfaces has a mean between them, and the jump splits into two
                 steps that each pass under the threshold. (A floor seen at grazing incidence
                 by the far periphery's 1-2 deg samples can cross 25% per sample without a
                 discontinuity; the window's one-surface assumption fails there just the same.)
  its distance   Chebyshev distance, in cells of its own level, to the nearest edge cell (the
                 window is a square: distance <= --window (2) means the 5 x 5 window holds a
                 depth edge), capped at --dmax (8);
  its parent     the level above's LR-consistent parallax at the same direction, if any.

Two errors are judged, because the repository uses two and they are not the same thing:
  wrong peak     |parallax error| > 1 cell            (stereo_field's gross: the matcher's)
  beyond 25%     |rho error| / rho_truth > --rel (0.25) (belief.metrics' gross: the loop's, the
                                                        one in D20's decision rule)
A right peak can be beyond 25%: a cell's inlier error is 0.3-0.4 cells, and at the coarse
levels 0.3 cell of parallax is a large fraction of the parallax itself. No matcher moves that;
only a finer look does.

Every judged cell (matchable, all its samples hit, LR-consistent unless --all-matchable) falls in
one KIND, in this order:
  occluded     wrong or beyond 25%, and the other eye sees less than half of it: no
               correspondence exists (the occluded cells that come out right are 'good')
  window       wrong peak, within a window radius of a depth edge
  search       wrong peak, farther than that from any edge
  resolution   right peak, beyond 25% all the same
  good         right peak, within 25%
Reported per level: the kinds, P(wrong peak) and P(beyond 25%) against the distance to an edge
(the figure), and the share of the near-edge wrong peaks that is excess over the far rate (at
the far rate they would be the search's, edge or no edge). Over all levels: the kinds weighted by
cell area, which is how the loop's gross fraction counts them (a belief cell is a belief cell;
a level-4 cell covers 256 of them).

The parent oracle, what coarse-to-fine can do before it is written. A cell at level l with a
consistent parent searched within +-(--c2f-cells, 2) of the parent's parallax would:
  be cured       a wrong peak now, the truth inside the interval, the wrong peak outside it
  be put at risk a right peak now, the truth outside the interval (the safety valve's cases)
Counted per level, with the fraction of cells that have a parent at all, and why the uncured
stay uncured: no parent / the parent is wrong too (truth outside its interval) / the wrong peak
lies inside the interval with the truth.

What separates a wrong peak from a right one (D2). field_of_pair(features=True) gives per cell
the NCC peak, its rival (the best score more than a cell away), the LR residual; with the bound
in cells and the disagreement with the parent these are five things a confidence test could
read WITHOUT the truth. Per level and feature: the threshold that keeps --keep (0.9) of the
right peaks, the share of the wrong peaks it rejects (all / window / search), and the AUC. A
feature that rejects 10% at 90% kept is a coin; one that rejects 70% is a test.

D2b adds a sixth feature, `neighbours` (|parallax - median of the LR-consistent neighbours'| in
cells, radius window + 1, at least three; fewer: 'isolated', counted apart), and `combined`, a
logistic score of all six fitted on the even pairs and judged on the odd ones. --nb-tol T
[--nb-drop-isolated] rebuilds the fields with the neighbour test on (a what-if: needs --tag);
a loop run made with it carries it in loop.json and is rebuilt with it, so (y1) still judges.
The area line ends with what is outside the variance model: occluded + window + search.

--tag NAME marks a what-if (e.g. --window 1 --tag w1): output goes to gross_diagnosis_NAME.*,
the standard files stay, and (y1) is reported, not judged (the field is not the one on record).

Output: <run>/gross_diagnosis.json, <run>/gross_diagnosis.png (one panel per level).

Checks, each of which can fail (exit 1):
  (y1) the diagnosed field is the field on record. Loop run: the rebuilt rows are the saved
       field/p<NNN>.npz rows (same cells, parallax within 1e-6 deg) on >= 99.9% of them. Pairs
       run with a field.json: the per-level gross fraction after LR, judged as stereo_field
       judges it, is field.json's to the third digit.
  (y2) the edge axis means something: pooled over levels 0-1, P(wrong peak) within a window
       radius of an edge exceeds P(wrong peak) beyond it; and edge cells exist. A run whose
       edges the tool cannot see, or whose gross errors ignore them, fails here and says so.
--self-test: the distance transform against brute force; the sample edge flags on the synthetic
wall-and-card (every flagged sample has a neighbour on the other surface, the card's border is
found); the kinds partition the cells; P(wrong | near) > P(wrong | far) there; and the negative:
--edge-jump 10 finds no edges, so (y2) fails.
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
from stereo_field import field_of_pair, inverse_depth, load, neighbour_median, synthetic_pair  # noqa: E402

KINDS = ("occluded", "window", "search", "resolution", "good")
FEATURES = ("peak", "margin", "lr_resid", "bound", "parent", "neighbours")   # -ncc peak, -(peak - rival), LR residual, bound, |parallax - parent's|,
NF = len(FEATURES)                                                          # |parallax - median of the consistent neighbours'| (all in cells but the first two)



# ----------------------------------------------------------------------------------------
# edges and distances
# ----------------------------------------------------------------------------------------

def sample_edges(raster_index: np.ndarray, distance: np.ndarray, n: int, jump: float) -> np.ndarray:
    """Per sample: True when a 4-neighbour in the n x n raster (inside the disc) differs by
    more than `jump` in inverse depth, relative to the smaller of the two. A miss (1e10) has
    rho ~ 0, so a silhouette against the sky is an edge."""
    rho = np.full((n, n), np.nan)
    rho[raster_index[:, 0], raster_index[:, 1]] = 1.0 / np.maximum(distance.astype(np.float64), 1e-6)
    E = np.zeros((n, n), bool)
    for ax in (0, 1):
        a = rho[:-1, :] if ax == 0 else rho[:, :-1]
        b = rho[1:, :] if ax == 0 else rho[:, 1:]
        with np.errstate(invalid="ignore", divide="ignore"):
            j = np.abs(a - b) / np.maximum(np.minimum(a, b), 1e-6) > jump
        j &= np.isfinite(a) & np.isfinite(b)
        if ax == 0:
            E[:-1, :] |= j; E[1:, :] |= j
        else:
            E[:, :-1] |= j; E[:, 1:] |= j
    return E[raster_index[:, 0], raster_index[:, 1]]


def chebyshev_distance(mask: np.ndarray, dmax: int) -> np.ndarray:
    """Chebyshev distance to the nearest True cell, by 3 x 3 dilation; dmax + 1 beyond dmax."""
    D = np.where(mask, 0, dmax + 1).astype(np.int32)
    cur = mask.copy()
    for d in range(1, dmax + 1):
        P = np.pad(cur, 1)
        nxt = np.zeros_like(cur)
        for dr in (0, 1, 2):
            for dc in (0, 1, 2):
                nxt |= P[dr:dr + cur.shape[0], dc:dc + cur.shape[1]]
        D[nxt & ~cur] = d
        cur = nxt
    return D


# ----------------------------------------------------------------------------------------
# one pair
# ----------------------------------------------------------------------------------------

def diagnose_pair(f: dict, window: int, dmax: int, rel: float, c2f_cells: float) -> dict:
    """Per matchable cell of a field built with extras parallax, rho, vis, hit, edge: the
    errors, the distance to an edge, the kind, the parent's verdict. Arrays aligned with f's rows."""
    M = len(f["rho"])
    lev = f["level"].astype(int); cell = f["cell_deg"]
    dist = np.full(M, dmax + 1, np.int32)
    par_parent = np.full(M, np.nan)
    nb_dev = np.full(M, np.nan); nb_n = np.zeros(M, np.int32)
    edge_cells = []
    for lv in f["levels"]:
        l = lv["level"]
        AL, AR, own, matchable, consistent, par, sig_p, exL, gL, c0 = lv["maps"]
        J = AL.shape[0]
        with np.errstate(invalid="ignore"):
            Ecell = np.nan_to_num(exL["edge"]) > 0
        Dm = chebyshev_distance(Ecell, dmax)[:, c0:c0 + J]
        m = lev == l
        dist[m] = Dm[f["row"][m], f["col"][m]]
        edge_cells.append(int((Ecell[:, c0:c0 + J] & own).sum()))
        if m.any():
            med, cnt = neighbour_median(par, matchable & consistent, window + 1)
            nb_dev[m] = np.abs(par - med)[f["row"][m], f["col"][m]] / lv["cell_deg"]; nb_n[m] = cnt[f["row"][m], f["col"][m]]
        # the parent: level l + 1's consistent parallax at this cell's direction
        up = next((x for x in f["levels"] if x["level"] == l + 1), None)
        if up is not None and m.any():
            _, _, _, match_u, cons_u, par_u, _, _, gU, c0u = up["maps"]
            Ju = par_u.shape[0]
            r, j, ok = gU.cell_of(f["theta_L"][m], f["phi"][m])
            j = j - c0u
            ok &= (j >= 0) & (j < Ju)
            rc, jc = np.clip(r, 0, Ju - 1), np.clip(j, 0, Ju - 1)
            good = ok & match_u[rc, jc] & cons_u[rc, jc]
            par_parent[m] = np.where(good, par_u[rc, jc], np.nan)
    err_cells = (f["parallax_deg"] - f["x_parallax"]) / cell
    wrong = np.abs(err_cells) > 1.0
    with np.errstate(invalid="ignore", divide="ignore"):
        rel_err = np.abs(f["rho"] - f["x_rho"]) / np.maximum(f["x_rho"], 1e-6)
    beyond = rel_err > rel
    judged = (f["x_hit"] > 0.999) & np.isfinite(f["x_parallax"]) & np.isfinite(f["rho"])
    near = dist <= window
    occluded = f["x_vis"] < 0.5
    kind = np.full(M, 4, np.int8)                                  # good: right peak, within 25% (an occluded cell can be, by luck or a smooth background)
    kind[~wrong & beyond] = 3                                      # resolution
    kind[wrong & ~near] = 2                                        # search
    kind[wrong & near] = 1                                         # window
    kind[occluded & (wrong | beyond)] = 0
    # the parent oracle
    has_parent = np.isfinite(par_parent)
    halfw = c2f_cells * cell
    with np.errstate(invalid="ignore"):
        truth_in = has_parent & (np.abs(f["x_parallax"] - par_parent) <= halfw)
        est_in = has_parent & (np.abs(f["parallax_deg"] - par_parent) <= halfw)
    cured = wrong & truth_in & ~est_in
    at_risk = ~wrong & has_parent & ~truth_in
    why = np.full(M, -1, np.int8)                                  # of the wrong peaks: 0 cured, 1 no parent, 2 parent wrong too, 3 inside the interval
    why[wrong & cured] = 0; why[wrong & ~has_parent] = 1; why[wrong & has_parent & ~truth_in] = 2; why[wrong & truth_in & est_in] = 3
    # badness features (higher = more suspect), none of which reads the truth
    feats = None
    if "ncc_peak" in f:
        with np.errstate(invalid="ignore"):
            margin = f["ncc_peak"] - np.where(np.isfinite(f["ncc_rival"]), f["ncc_rival"], -1.0)
            feats = np.stack([-f["ncc_peak"], -margin, np.nan_to_num(f["lr_resid_cells"], nan=9.0), f["bound_deg"] / cell,
                              np.where(has_parent, np.abs(f["parallax_deg"] - par_parent) / cell, 0.0),
                              np.where(nb_n >= 3, nb_dev, np.nan)])        # NaN: fewer than three consistent neighbours — 'isolated', counted apart
    return {"judged": judged, "err_cells": err_cells, "wrong": wrong, "beyond": beyond, "dist": dist, "near": near,
            "kind": kind, "occluded": occluded, "why": why, "feats": feats, "pair_parity": None, "has_parent": has_parent, "cured": cured, "at_risk": at_risk, "edge_cells": edge_cells}


def extras_of(L: dict, raster_index: np.ndarray, distance: np.ndarray, n: int, jump: float) -> dict:
    hit = distance < 1e9
    return {"parallax": L["parallax"], "rho": np.where(hit, 1.0 / np.maximum(distance.astype(np.float64), 1e-6), 0.0),
            "vis": (L["visible"] == 1).astype(float), "hit": hit.astype(float),
            "edge": sample_edges(raster_index, distance, n, jump).astype(float)}


# ----------------------------------------------------------------------------------------
# pooling and the report
# ----------------------------------------------------------------------------------------

class Pool:
    def __init__(self, nlev: int, dmax: int, ipd_m: float = 0.063, rel: float = 0.25):
        self.nlev, self.dmax, self.ipd, self.rel = nlev, dmax, ipd_m, rel
        self.keep = 0.9; self.n_pairs = 0
        self.why = np.zeros((nlev, 4), np.int64); self.feat_rows = [[] for _ in range(nlev)]   # (5 features, wrong, near) per cell with a correspondence
        self.right_rows = [[] for _ in range(nlev)]               # right peaks with a correspondence: (err_cells, theta_L, parallax, truth rho, cell)
        z = lambda *s: np.zeros(s, np.int64)
        self.kind = z(nlev, len(KINDS)); self.n_dist = z(nlev, dmax + 2); self.wrong_dist = z(nlev, dmax + 2); self.beyond_dist = z(nlev, dmax + 2)
        self.parent = z(nlev); self.cured = z(nlev); self.at_risk = z(nlev); self.wrong = z(nlev); self.right = z(nlev)
        self.edge_cells = z(nlev); self.unhit = z(nlev); self.n_occ = z(nlev)
        self.area = np.zeros((nlev, len(KINDS)))
        # stereo_field's own judgement, for (y1) on a pairs run
        self.sf_gross = z(nlev); self.sf_n = z(nlev)

    def add(self, f: dict, d: dict, keep: np.ndarray):
        lev = f["level"].astype(int)
        self.n_pairs += 1
        for l in range(self.nlev):
            m = (lev == l) & keep
            self.unhit[l] += int((m & ~d["judged"]).sum())
            m &= d["judged"]
            if l < len(d["edge_cells"]):
                self.edge_cells[l] += d["edge_cells"][l]
            if not m.any():
                continue
            self.kind[l] += np.bincount(d["kind"][m], minlength=len(KINDS))
            self.area[l] += np.bincount(d["kind"][m], weights=f["cell_deg"][m] ** 2, minlength=len(KINDS))
            v = m & ~d["occluded"]                                  # the distance curves and the oracle are over cells with a correspondence
            self.n_occ[l] += int((m & d["occluded"]).sum())
            self.n_dist[l] += np.bincount(d["dist"][v], minlength=self.dmax + 2)
            self.wrong_dist[l] += np.bincount(d["dist"][v & d["wrong"]], minlength=self.dmax + 2)
            self.beyond_dist[l] += np.bincount(d["dist"][v & d["beyond"]], minlength=self.dmax + 2)
            self.parent[l] += int((v & d["has_parent"]).sum()); self.cured[l] += int((v & d["cured"]).sum()); self.at_risk[l] += int((v & d["at_risk"]).sum())
            self.wrong[l] += int((v & d["wrong"]).sum()); self.right[l] += int((v & ~d["wrong"]).sum())
            self.why[l] += np.bincount(d["why"][v & d["wrong"]], minlength=4)[:4]
            if d["feats"] is not None:
                self.feat_rows[l].append(np.vstack([d["feats"][:, v], d["wrong"][v][None].astype(float), d["near"][v][None].astype(float),
                                                    np.full((1, int(v.sum())), float(self.n_pairs % 2))]))
            r = v & ~d["wrong"]
            self.right_rows[l].append(np.stack([d["err_cells"][r], f["theta_L"][r], f["parallax_deg"][r], f["x_rho"][r], f["cell_deg"][r]]))
        # as stereo_field judges: visible >= 0.5, finite truth, consistent; gross = wrong peak
        sf = f["consistent"] & (f["x_vis"] >= 0.5) & np.isfinite(f["x_parallax"])
        for l in range(self.nlev):
            m = sf & (lev == l)
            self.sf_n[l] += int(m.sum()); self.sf_gross[l] += int((m & d["wrong"]).sum())

    def separation(self, l: int) -> dict | None:
        if not self.feat_rows[l]:
            return None
        X = np.concatenate(self.feat_rows[l], axis=1)
        wrong, near, odd = X[NF] > 0.5, X[NF + 1] > 0.5, X[NF + 2] > 0.5
        if wrong.sum() < 50 or (~wrong).sum() < 50:
            return None
        out = {"keep": self.keep, "wrong": int(wrong.sum()), "right": int((~wrong).sum())}

        def judge(b, sel):
            """Threshold keeping `keep` of the right peaks among sel; what it rejects of the wrong ones; AUC."""
            br = np.sort(b[sel & ~wrong]); bw = b[sel & wrong]
            t = float(np.quantile(br, self.keep))
            lo, hi = np.searchsorted(br, bw, "left"), np.searchsorted(br, bw, "right")
            rj = lambda m: float((b[sel & m] > t).mean()) if (sel & m).any() else None
            return {"threshold": t, "kept_right": float((br <= t).mean()), "rejects_wrong": rj(wrong), "rejects_window": rj(wrong & near),
                    "rejects_search": rj(wrong & ~near), "auc": float(((lo + hi) / 2.0).mean() / len(br))}
        iso = ~np.isfinite(X[NF - 1])
        out["isolated"] = {"of_right": float(iso[~wrong].mean()), "of_wrong": float(iso[wrong].mean())}
        for i, name in enumerate(FEATURES):
            sel = np.isfinite(X[i])
            if (sel & wrong).sum() >= 50 and (sel & ~wrong).sum() >= 50:
                out[name] = judge(X[i], sel)
        # all six together: a logistic score fitted on the even pairs, judged on the odd ones (the ceiling of a pi
        # built from these; a fit judged on its own data would flatter it)
        F = X[:NF].T.copy()
        F[:, NF - 1] = np.where(iso, 0.0, F[:, NF - 1]); F = np.column_stack([F, iso.astype(float)])
        tr, te = ~odd, odd
        if min((tr & wrong).sum(), (tr & ~wrong).sum(), (te & wrong).sum(), (te & ~wrong).sum()) >= 50:
            lo_, hi_ = np.quantile(F[tr], 0.01, axis=0), np.quantile(F[tr], 0.99, axis=0)
            Z = np.clip(F, lo_, hi_); mu, sd = Z[tr].mean(0), Z[tr].std(0) + 1e-9
            Z = np.column_stack([(Z - mu) / sd, np.ones(len(Z))])
            w = np.zeros(Z.shape[1]); y = wrong.astype(float)
            for _ in range(25):                                     # Newton steps, ridge 1e-3
                p_ = 1.0 / (1.0 + np.exp(-np.clip(Z[tr] @ w, -30, 30)))
                H = (Z[tr] * (p_ * (1 - p_))[:, None]).T @ Z[tr] + 1e-3 * np.eye(len(w))
                w = w + np.linalg.solve(H, Z[tr].T @ (y[tr] - p_) - 1e-3 * w)
            out["combined"] = dict(judge(Z @ w, te), trained_on=int(tr.sum()), judged_on=int(te.sum()),
                                   weights={k_: float(x) for k_, x in zip(FEATURES + ("isolated", "const"), w)})
        return out

    def report(self, window: int, cell0: float) -> dict:
        out = {"levels": []}
        for l in range(self.nlev):
            n = int(self.kind[l].sum())
            if n == 0:
                continue
            k = self.kind[l]
            nd, wd, bd = self.n_dist[l], self.wrong_dist[l], self.beyond_dist[l]
            n_near, n_far = int(nd[:window + 1].sum()), int(nd[window + 1:].sum())
            p_near = wd[:window + 1].sum() / n_near if n_near else None
            p_far = wd[window + 1:].sum() / n_far if n_far else None
            excess = None
            if p_near is not None and p_far is not None and wd[:window + 1].sum() > 0:
                excess = float(max(p_near - p_far, 0.0) * n_near / wd[:window + 1].sum())
            with np.errstate(invalid="ignore", divide="ignore"):
                pw, pb = wd / nd, bd / nd
            # the right peaks: how much of 'beyond 25%' is the level's bias (one constant, removable) and how much its spread
            rp = {"bias_cells": None, "rms_cells": None, "p_beyond": None, "p_beyond_debiased": None}
            if self.right_rows[l]:
                e, thL, par, trho, cl = np.concatenate(self.right_rows[l], axis=1)
                if len(e):
                    b = float(e.mean())
                    rho_db = inverse_depth(thL, par - b * cl, self.ipd)[0]
                    rho_as = inverse_depth(thL, par, self.ipd)[0]
                    far_ = lambda r_: float((np.abs(r_ - trho) / np.maximum(trho, 1e-6) > self.rel).mean())
                    rp = {"bias_cells": b, "rms_cells": float(np.sqrt(np.mean(e ** 2))), "p_beyond": far_(rho_as), "p_beyond_debiased": far_(rho_db)}
            out["levels"].append({
                "level": l, "cell_deg": cell0 * 2 ** l, "judged": n, "not_all_hit": int(self.unhit[l]), "edge_cells_owned": int(self.edge_cells[l]),
                "occluded_cells_frac": float(self.n_occ[l] / n), "kinds": {KINDS[i]: int(k[i]) for i in range(len(KINDS))},
                "kinds_frac": {KINDS[i]: float(k[i] / n) for i in range(len(KINDS))},
                "with_correspondence": int(nd.sum()), "near_edge_frac": float(n_near / max(nd.sum(), 1)),
                "p_wrong_near": None if p_near is None else float(p_near), "p_wrong_far": None if p_far is None else float(p_far),
                "near_wrong_excess_share": excess,
                "p_beyond_near": float(bd[:window + 1].sum() / n_near) if n_near else None, "p_beyond_far": float(bd[window + 1:].sum() / n_far) if n_far else None,
                "by_distance": {"n": nd.tolist(), "p_wrong": [None if not np.isfinite(x) else float(x) for x in pw], "p_beyond": [None if not np.isfinite(x) else float(x) for x in pb]},
                "parent": {"with_parent_frac": float(self.parent[l] / max(nd.sum(), 1)),
                           "cured_of_wrong": float(self.cured[l] / self.wrong[l]) if self.wrong[l] else None,
                           "at_risk_of_right": float(self.at_risk[l] / self.right[l]) if self.right[l] else None,
                           "cured": int(self.cured[l]), "at_risk": int(self.at_risk[l]), "wrong": int(self.wrong[l]), "right": int(self.right[l])},
                "right_peaks": rp, "p_wrong_all": float(wd.sum() / max(nd.sum(), 1)),
                "uncured": {k_: int(x) for k_, x in zip(("cured", "no_parent", "parent_wrong_too", "inside_the_interval"), self.why[l])},
                "separation": self.separation(l),
                "sf_gross_frac_consistent": float(self.sf_gross[l] / self.sf_n[l]) if self.sf_n[l] else None})
        A = self.area.sum(0); bad = A[:4].sum()
        out["area_weighted"] = {"beyond_or_wrong_frac": float(bad / max(A.sum(), 1e-12)), "outside_model_frac": float(A[:3].sum() / max(A.sum(), 1e-12)),
                                "judged_area_deg2": float(A.sum()),
                                "share_of_bad": {KINDS[i]: float(A[i] / bad) if bad > 0 else None for i in range(4)},
                                "note": "cells weighted by cell_deg^2, as the belief's cell count weights them"}
        return out


def print_report(rep: dict, tag: str = "[diag]"):
    pc = lambda x: "  -  " if x is None else f"{100 * x:5.1f}"
    for L in rep["levels"]:
        kf = L["kinds_frac"]
        print(f"{tag} level {L['level']} cell {L['cell_deg']:.2f} deg, {L['judged']:7d} cells: occluded {pc(kf['occluded'])}%  window {pc(kf['window'])}%  search {pc(kf['search'])}%  "
              f"resolution {pc(kf['resolution'])}%  good {pc(kf['good'])}%  | wrong peaks {pc(L['p_wrong_all'])}% of the cells with a correspondence; near an edge {pc(L['near_edge_frac'])}% of cells; P(wrong) near {pc(L['p_wrong_near'])}% far {pc(L['p_wrong_far'])}% "
              f"(excess share of near-edge wrong peaks {pc(L['near_wrong_excess_share'])}%); P(beyond 25%) near {pc(L['p_beyond_near'])}% far {pc(L['p_beyond_far'])}%")
    for L in rep["levels"]:
        r = L["right_peaks"]
        if r["bias_cells"] is not None:
            print(f"{tag} level {L['level']} right peaks: bias {r['bias_cells']:+.2f} cells, RMS {r['rms_cells']:.2f} cells; beyond 25% {pc(r['p_beyond'])}% -> {pc(r['p_beyond_debiased'])}% with the level's bias removed")
    for L in rep["levels"]:
        P = L["parent"]
        print(f"{tag} level {L['level']} parent oracle: {pc(P['with_parent_frac'])}% of cells have a consistent parent; coarse-to-fine would cure {pc(P['cured_of_wrong'])}% of the wrong peaks "
              f"({P['cured']} of {P['wrong']}) and put at risk {pc(P['at_risk_of_right'])}% of the right ones ({P['at_risk']} of {P['right']})")
    for L in rep["levels"]:
        u = L["uncured"]; n = max(sum(u.values()), 1)
        print(f"{tag} level {L['level']} wrong peaks under the oracle: cured {pc(u['cured'] / n)}%  no parent {pc(u['no_parent'] / n)}%  parent wrong too {pc(u['parent_wrong_too'] / n)}%  "
              f"inside the interval {pc(u['inside_the_interval'] / n)}%")
    for L in rep["levels"]:
        S_ = L.get("separation")
        if S_:
            print(f"{tag} level {L['level']} telling wrong from right at {100 * S_['keep']:.0f}% of the right kept ({S_['wrong']} wrong, {S_['right']} right) — rejects all / window / search, AUC: "
                  + "; ".join(f"{k_} {pc(S_[k_]['rejects_wrong'])}/{pc(S_[k_]['rejects_window'])}/{pc(S_[k_]['rejects_search'])}% {S_[k_]['auc']:.2f}" for k_ in FEATURES + ("combined",) if k_ in S_)
                  + f"; isolated (< 3 consistent neighbours): {pc(S_['isolated']['of_right'])}% of the right, {pc(S_['isolated']['of_wrong'])}% of the wrong")
    a = rep["area_weighted"]; s = a["share_of_bad"]
    print(f"{tag} by area (the loop's count): {pc(a['beyond_or_wrong_frac'])}% of the judged area is wrong or beyond 25%; of that, occluded {pc(s['occluded'])}%  window {pc(s['window'])}%  "
          f"search {pc(s['search'])}%  resolution {pc(s['resolution'])}%  | outside the model (occluded + window + search) {pc(a['outside_model_frac'])}% of {a['judged_area_deg2']:.0f} deg2 judged")


def figure(rep: dict, path: str, window: int, title: str, size: int = 300):
    from PIL import Image, ImageDraw
    Ls = rep["levels"]
    if not Ls:
        return
    m = 34
    im = Image.new("RGB", (len(Ls) * size, size + 18), (24, 24, 24)); dr = ImageDraw.Draw(im)
    dr.text((6, 3), f"{title}: P(wrong peak) orange, P(rho beyond 25%) blue, against distance to a depth edge (cells; last bin: farther). Grey band: inside the window.", fill=(220, 220, 220))
    for i, L in enumerate(Ls):
        x0, y0 = i * size, 18
        nb = len(L["by_distance"]["n"])
        fx = lambda b: x0 + m + b / (nb - 1) * (size - 2 * m)
        fy = lambda p: y0 + size - m - p * (size - 2 * m)
        dr.rectangle([fx(0), fy(1.0), fx(window), fy(0.0)], fill=(44, 44, 44))
        dr.rectangle([x0 + m, y0 + m, x0 + size - m, y0 + size - m], outline=(90, 90, 90))
        dr.text((x0 + m, y0 + 6), f"level {L['level']}  cell {L['cell_deg']:.2f} deg  n {L['with_correspondence']}", fill=(230, 230, 230))
        dr.text((x0 + 4, y0 + m), "1", fill=(150, 150, 150)); dr.text((x0 + 4, y0 + size - m - 10), "0", fill=(150, 150, 150))
        for b in range(nb):
            dr.text((fx(b) - 3, y0 + size - m + 4), (">" if b == nb - 1 else str(b)), fill=(150, 150, 150))
        for key, rgb in (("p_beyond", (120, 160, 255)), ("p_wrong", (255, 170, 60))):
            pts = [(fx(b), fy(p)) for b, (p, n) in enumerate(zip(L["by_distance"][key], L["by_distance"]["n"])) if p is not None and n >= 20]
            if len(pts) > 1:
                dr.line(pts, fill=rgb, width=2)
            for p in pts:
                dr.ellipse([p[0] - 2, p[1] - 2, p[0] + 2, p[1] + 2], fill=rgb)
    im.save(path)
    print(f"[diag] figure -> {path}")


def check_y2(rep: dict, window: int, max_level: int = 1) -> list[str]:
    fails = []
    n_near = n_far = w_near = w_far = 0; edges = 0
    for L in rep["levels"]:
        if L["level"] > max_level:
            continue
        nd = np.array(L["by_distance"]["n"]); pw = np.array([x if x is not None else 0.0 for x in L["by_distance"]["p_wrong"]])
        n_near += nd[:window + 1].sum(); n_far += nd[window + 1:].sum()
        w_near += (nd * pw)[:window + 1].sum(); w_far += (nd * pw)[window + 1:].sum()
        edges += L["edge_cells_owned"]
    if edges == 0:
        fails.append(f"(y2) no edge cells at levels 0-{max_level}: the tool sees no depth edges in this run")
    elif n_near == 0 or n_far == 0:
        fails.append(f"(y2) levels 0-{max_level}: {int(n_near)} cells near an edge, {int(n_far)} far: nothing to compare")
    elif not w_near / n_near > w_far / n_far:
        fails.append(f"(y2) levels 0-{max_level}: P(wrong peak) near an edge {100 * w_near / n_near:.1f}% is not above far from one {100 * w_far / n_far:.1f}%")
    return fails


# ----------------------------------------------------------------------------------------
# self-test
# ----------------------------------------------------------------------------------------

def self_test() -> list[str]:
    from warp import raster_samples, raster_size
    fails = []
    rng = np.random.default_rng(1)
    # the distance transform against brute force
    mask = rng.random((23, 31)) < 0.02
    D = chebyshev_distance(mask, 6)
    rr, cc = np.nonzero(mask)
    R, C = np.indices(mask.shape)
    brute = np.minimum(np.max(np.stack([np.abs(R[..., None] - rr), np.abs(C[..., None] - cc)]), axis=0).min(-1), 7)
    if not np.array_equal(D, brute):
        fails.append(f"chebyshev_distance differs from brute force on {int((D != brute).sum())} cells")
    # the synthetic wall (2 m) and card (1 m): sample edges are the card's border
    s0, E2, emax, ipd = 0.1, 2.0, 45.0, 0.063
    eyes = synthetic_pair(rng, s0, E2, emax, ipd)
    n = raster_size(s0, E2, emax); rs = raster_samples(n, E2, emax)
    ri = rs["raster_index"][rs["inside"]]
    L = eyes[0]
    if len(ri) != len(L["dist"]):
        fails.append(f"synthetic pair dropped samples ({len(L['dist'])} of {len(ri)}): the self-test's raster index is wrong")
        return fails
    on_card = L["dist"] < 1.5
    for jump, expect_edges in ((0.25, True), (10.0, False)):
        e = sample_edges(ri, L["dist"], n, jump)
        if expect_edges:
            lab = np.full((n, n), -1); lab[ri[:, 0], ri[:, 1]] = on_card
            nb = np.stack([np.roll(lab, s, a) for a in (0, 1) for s in (1, -1)])
            other = ((nb != lab) & (nb >= 0)).any(0)[ri[:, 0], ri[:, 1]]
            if e.sum() == 0 or not np.array_equal(e, other):
                fails.append(f"sample_edges: {int(e.sum())} flagged, {int(other.sum())} samples have a neighbour on the other surface, {int((e != other).sum())} differ")
        # true parallax of each L sample, from its ray distance (the sidecar's quantity)
        th, ph = np.radians(L["theta"]), np.radians(L["phi"])
        d = np.stack([np.cos(th), np.sin(th) * np.sin(ph), -np.sin(th) * np.cos(ph)], -1)
        P = np.array([-ipd / 2, 0, 0]) + L["dist"][:, None] * d; dR = P - np.array([ipd / 2, 0, 0])
        tp = np.degrees(np.arctan2(np.hypot(dR[:, 1], dR[:, 2]), dR[:, 0])) - L["theta"]
        ex = {"parallax": tp, "rho": 1.0 / L["dist"], "vis": np.ones(len(tp)), "hit": np.ones(len(tp)), "edge": e.astype(float)}
        f = field_of_pair(eyes[0], eyes[1], eyes[0]["gaze"], eyes[1]["gaze"], s0, E2, emax, ipd, floor_cells=0.1, extras=ex)
        dg = diagnose_pair(f, 2, 8, 0.25, 2.0)
        pool = Pool(len(f["levels"]), 8); pool.add(f, dg, f["consistent"] | True)       # all matchable: the LR test removes the edge cells the check needs
        rep = pool.report(2, 2.0 * s0)
        tot = sum(Lv["judged"] for Lv in rep["levels"])
        if tot != int(dg["judged"].sum()):
            fails.append(f"kinds do not partition the cells: {tot} in kinds, {int(dg['judged'].sum())} judged")
        y2 = check_y2(rep, 2, max_level=2)                      # the card's border sits at 8.5-12 deg: level 2's band
        if expect_edges and y2:
            fails.append("synthetic pair: " + "; ".join(y2))
        if not expect_edges and not y2:
            fails.append("negative: --edge-jump 10 finds no edges, yet (y2) passed")
        if expect_edges:
            for Lv in rep["levels"]:
                if Lv["level"] <= 2 and Lv["p_wrong_far"] is not None and Lv["p_wrong_far"] > 0.2:
                    fails.append(f"synthetic pair level {Lv['level']}: {100 * Lv['p_wrong_far']:.0f}% wrong peaks far from the card's edge")
    return fails


# ----------------------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------------------

def main():
    if "--self-test" in sys.argv:
        f = self_test()
        for x in f:
            print("[diag] FAIL", x)
        print(f"[diag] self-test {'FAILED' if f else 'ok'}")
        sys.exit(1 if f else 0)
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--edge-jump", type=float, default=0.25, help="relative jump in inverse depth between neighbouring samples that makes a depth edge")
    ap.add_argument("--rel", type=float, default=0.25, help="the loop's gross: relative rho error (belief.metrics' rel_inlier)")
    ap.add_argument("--c2f-cells", type=float, default=2.0, help="the parent oracle's interval half-width, in cells of the child level (D1's --c2f-cells)")
    ap.add_argument("--dmax", type=int, default=8)
    ap.add_argument("--all-matchable", action="store_true", help="judge every matchable cell, not only the LR-consistent ones the belief fuses")
    ap.add_argument("--search-deg", type=float, default=None); ap.add_argument("--kappa", type=float, default=None)
    ap.add_argument("--floor-cells", type=float, default=None); ap.add_argument("--window", type=int, default=None)
    ap.add_argument("--noise-rel", type=float, default=None)
    ap.add_argument("--nb-tol", type=float, default=None, help="what-if (D2b): drop consistent cells more than this many cells from the median of their consistent neighbours")
    ap.add_argument("--nb-drop-isolated", action="store_true", help="with --nb-tol: also drop cells with fewer than three consistent neighbours")
    ap.add_argument("--keep", type=float, default=0.9, help="separation: the share of right peaks a threshold must keep")
    ap.add_argument("--tag", default=None, help="a what-if run: outputs suffixed _TAG, (y1) reported but not judged")
    args = ap.parse_args()

    run = os.path.abspath(args.run)
    pj = json.load(open(os.path.join(run, "pairs.json")))
    s0 = float(pj["warp"]["s0_deg"]); E2 = float(pj["warp"]["E2_deg"]); emax = float(pj["warp"]["e_max_deg"]); n = int(pj["warp"]["raster"])
    ipd = float(pj["rig"]["ipd_m"])
    if not os.path.exists(os.path.join(run, "L", "f000", "truth.npz")):
        raise SystemExit(f"[diag] no truth.npz in {run}: run tools/stereo_truth.py on it first")
    # the settings the run's field was built with
    is_loop = os.path.exists(os.path.join(run, "loop.json"))
    kw = {"eval_factor": 2.0, "search_deg": 3.0, "window": 2, "kappa": 2.5, "floor_cells": 0.3, "lr_tol_cells": 1.0}
    noise_list, ref, rec_nb = None, None, (None, False)
    if is_loop:
        lj = json.load(open(os.path.join(run, "loop.json"))); st = lj["settings"]
        kw.update(eval_factor=st["eval_factor"], search_deg=st["search_deg"], kappa=st["kappa"], floor_cells=st["floor_cells"])
        noise_list = lj["noise_rel_per_level"]
        rec_nb = (st.get("nb_tol"), bool(st.get("nb_drop_isolated", False)))    # a loop run with the neighbour test on: part of its record
        src = "loop.json"
    elif os.path.exists(os.path.join(run, "field.json")):
        ref = json.load(open(os.path.join(run, "field.json")))["summary"]
        kw.update(eval_factor=ref["eval_factor"], search_deg=ref["search_deg"], window=(int(ref["window"]) - 1) // 2, kappa=ref["kappa_assumed"],
                  floor_cells=ref["floor_cells_assumed"], lr_tol_cells=ref["lr_tol_cells"])
        src = "field.json"
    else:
        src = "defaults (no loop.json, no field.json: (y1) has nothing to compare with)"
    for k_, v in (("search_deg", args.search_deg), ("kappa", args.kappa), ("floor_cells", args.floor_cells), ("window", args.window)):
        if v is not None:
            kw[k_] = v; src += f", --{k_.replace('_', '-')} overridden"
    nb_tol, nb_iso = (args.nb_tol, args.nb_drop_isolated) if args.nb_tol is not None else rec_nb
    if nb_tol is not None:
        src += f"; neighbour test {nb_tol} cells{', isolated dropped' if nb_iso else ''} ({'--nb-tol' if args.nb_tol is not None else 'the record'})"
    seed_pair = bool(pj.get("seed_pair", False))
    print(f"[diag] {run}: {len(pj['pairs'])} pairs, s0 {s0:.4f} deg, settings from {src}: {kw}")

    nlev = None; pool = None
    same = total = 0
    for pid, pair in enumerate(pj["pairs"]):
        ld, rd = os.path.join(run, "L", f"f{pid:03d}"), os.path.join(run, "R", f"f{pid:03d}")
        with_b = seed_pair or (is_loop and pid == 0 and args.noise_rel is None)
        L, R = load(ld, with_b), load(rd, with_b)
        s = np.load(os.path.join(ld, "samples.npz"))
        if is_loop:                                                 # the loop placed its samples by the record's float32 directions,
            for X, d_ in ((L, ld), (R, rd)):                        # stereo_field's main by the sidecar's analytic ones: 1e-5 deg apart,
                X["theta"], X["phi"] = epipolar(np.load(os.path.join(d_, "samples.npz"))["direction"].astype(np.float64))   # a cell border for a few samples
        gaze = [to_eye_frame(np.array([[0.0, 0.0, 1.0]]), g["yaw"], g["pitch"])[0] for g in pair["eyes"]]
        measured = L.get("val_b") is not None and R.get("val_b") is not None
        nr = None if measured else (args.noise_rel if args.noise_rel is not None else noise_list)
        if not measured and nr is None:
            raise SystemExit("[diag] no seed pair and no recorded noise: pass --noise-rel")
        f = field_of_pair(L, R, gaze[0], gaze[1], s0, E2, emax, ipd, noise_rel=nr,
                          extras=extras_of(L, s["raster_index"], s["distance"], n, args.edge_jump), features=True, nb_tol_cells=nb_tol, nb_drop_isolated=nb_iso, **kw)
        if pool is None:
            nlev = len(f["levels"]); pool = Pool(nlev, args.dmax, ipd, args.rel); pool.keep = args.keep
        d = diagnose_pair(f, kw["window"], args.dmax, args.rel, args.c2f_cells)
        pool.add(f, d, np.ones(len(f["rho"]), bool) if args.all_matchable else f["consistent"])
        if is_loop:
            sp = os.path.join(run, "field", f"p{pid:03d}.npz")
            if os.path.exists(sp):
                g = np.load(sp)
                key = lambda lv, r, c: lv.astype(np.int64) * 10 ** 8 + r.astype(np.int64) * 10 ** 4 + c.astype(np.int64)
                ka, kb = key(f["level"], f["row"], f["col"]), key(g["level"], g["row"], g["col"])
                ia = np.argsort(ka); ib = np.argsort(kb)
                common, xa, xb = np.intersect1d(ka[ia], kb[ib], return_indices=True)
                ok = np.abs(f["parallax_deg"][ia][xa] - g["parallax_deg"][ib][xb]) <= 1e-6
                ok &= f["consistent"][ia][xa] == g["consistent"][ib][xb]
                same += int(ok.sum()); total += max(len(ka), len(kb))
    rep = pool.report(kw["window"], kw["eval_factor"] * s0)
    print_report(rep)

    fails = []
    if is_loop:
        if total == 0:
            fails.append("(y1) the loop run has no field/ record to compare with")
        elif same / total < 0.999:
            fails.append(f"(y1) the rebuilt field matches the record on {100 * same / total:.2f}% of {total} rows (< 99.9%): this is not the field the loop fused")
        y1_note = f"(y1) rebuilt field = the record on {100 * same / max(total, 1):.3f}% of {total} rows"
    elif ref is not None:
        worst = 0.0
        for L_ in rep["levels"]:
            r_ = next((x for x in ref["per_level"] if x["level"] == L_["level"]), None)
            if r_ and r_["gross_frac_consistent"] is not None and L_["sf_gross_frac_consistent"] is not None:
                dlt = abs(r_["gross_frac_consistent"] - L_["sf_gross_frac_consistent"]); worst = max(worst, dlt)
                if dlt > 5e-4:
                    fails.append(f"(y1) level {L_['level']}: gross after LR {L_['sf_gross_frac_consistent']:.4f} here, {r_['gross_frac_consistent']:.4f} in field.json")
        y1_note = f"(y1) per-level gross after LR vs field.json: worst difference {worst:.4f}"
    else:
        y1_note = "(y1) not judged: no record of this run's field"
    if args.nb_tol is not None and not args.tag:
        raise SystemExit("[diag] --nb-tol is a what-if: give it a --tag")
    if args.tag:
        y1_note += " — a what-if (--tag): not judged"; fails = []
    fails += check_y2(rep, kw["window"])
    print(f"[diag] {y1_note}")
    for x in fails:
        print("[diag] FAIL", x)
    rep.update({"run": run, "settings": kw, "settings_from": src, "edge_jump": args.edge_jump, "rel": args.rel, "c2f_cells": args.c2f_cells,
                "cells": "all matchable" if args.all_matchable else "LR-consistent", "y1": y1_note, "fails": fails})
    stem = "gross_diagnosis" + (f"_{args.tag}" if args.tag else "")
    with open(os.path.join(run, stem + ".json"), "w") as fh:
        json.dump(rep, fh, indent=1)
    figure(rep, os.path.join(run, stem + ".png"), kw["window"], os.path.basename(run) + (f" [{args.tag}]" if args.tag else ""))
    print(f"[diag] {'FAILED' if fails else 'ok'} ({len(fails)} failures) -> {os.path.join(run, stem + '.json')}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
