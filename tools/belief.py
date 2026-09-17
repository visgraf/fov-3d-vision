"""The belief on the head sphere and the gaze policies (C2, D17). Numpy only: imported inside
the Blender session by active_loop.py and host-side by active_eval.py.

    python tools/belief.py --self-test

The belief: a grid over the sphere in the epipolar frame (D13: theta from the head's +X, the
baseline axis; phi the plane about it), cell `cell_deg` (default s_eval, D9), holding per cell
a Gaussian over inverse depth rho = 1/|P - C_L| as a precision sum P and a weighted sum S
(mean S/P, variance 1/P). The head is fixed (D3) and directions are stored in the head frame,
so a cell means the same direction in every pair: fusing a field (stereo_field.field_of_pair)
is inverse-variance averaging, with a measurement of cell c splatted over the belief cells it
covers. Two things the fusion is not naive about, both from the predecessors' record:
  * a measurement coarser than the belief that disagrees with it by more than 3 sigma is
    gated (bio-3d-vision: the matcher's confident wrong match at a depth edge must not move a
    fovea's estimate; a finer measurement always enters and re-weights);
  * the visit map: every cell the field OWNED at some level, matchable or not, so the policy
    can tell "not yet looked at" from "looked at and nothing to measure" (bio-3d-vision's
    validity mask, 65:1 over the variance; its lock-up on an unmeasurable pixel).
Truth: the L eye's own ray distances (the D1 record's `distance`), accumulated on the same grid
as a footprint-weighted mean of 1/distance, so the belief is judged in the session without
OpenEXR — on the cells the L eye has sampled.

The policies choose the next fixation direction from the belief; the vergence distance is the
belief's estimate along that direction (or the target's, for the target-order baseline).
  targets    the target list in order (Phase B's runs; the baseline)
  random     uniform over the field of regard (a cap of --regard-deg about the primary gaze)
  coverage   the candidate whose foveal disc (levels 0-1, 6 deg) holds the most cells not yet
             looked at finely (the visit map, measurable or not); bio-3d-vision's "not looking
             twice" and nothing else
  info       expected information: sum over the cells a pair would measure, out to
             --policy-levels, of 1/2 log(1 + sigma_c^2 I(e)), with I(e) the precision the
             field delivers at eccentricity e (the running median sigma_rho per level of this
             run's own fields) and sigma_c the belief's; unseen cells at the prior, cells
             looked at finely and found unmeasurable at zero (the reviewer's policy, with the
             visit map)
  oracle     the same sum with the belief's actual squared error where truth exists ("look
             where you are most wrong"), with an explicit inhibition of return (3 deg) because a
             depth edge the fovea cannot resolve is "wrong" forever; the upper bracket, not a
             policy
"""
from __future__ import annotations

import math
import sys

import numpy as np

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from rig import epipolar  # noqa: E402
from stereo_field import direction_of, level_edges, n_levels_for  # noqa: E402

FORWARD = np.array([0.0, 0.0, -1.0])            # head frame primary gaze
UNVISITED = 127


class SphereBelief:
    def __init__(self, cell_deg: float, sigma_prior: float = 1.0):
        self.cell = float(cell_deg)
        self.nth = int(round(180.0 / self.cell)); self.nph = int(round(360.0 / self.cell))
        shape = (self.nth, self.nph)
        self.P = np.zeros(shape); self.S = np.zeros(shape)         # weights 1/sigma^2 (total) and weighted rho: the mean
        self.Pn = np.zeros(shape); self.F = np.full(shape, np.inf)  # noise-only precision (averages) and the smallest floor seen (does not)
        self.n = np.zeros(shape, np.int32)
        self.best_level = np.full(shape, UNVISITED, np.int8)      # finest level that MEASURED the cell
        self.visited = np.full(shape, UNVISITED, np.int8)         # finest level that OWNED the cell
        self.tW = np.zeros(shape); self.tS = np.zeros(shape); self.tn = np.zeros(shape, np.int32)
        self.sigma_prior = float(sigma_prior)
        self.gated = 0
        th = (np.arange(self.nth) + 0.5) * self.cell; ph = (np.arange(self.nph) + 0.5) * self.cell - 180.0
        self.theta = th; self.phi = ph
        self.sin_theta = np.sin(np.radians(th))
        self.dirs = direction_of(th[:, None] + np.zeros((1, self.nph)), ph[None, :] + np.zeros((self.nth, 1))).astype(np.float32)
        self.area = (np.radians(self.cell) ** 2) * self.sin_theta[:, None] + np.zeros((1, self.nph))   # sr per cell

    # ---------------------------------------------------------------- indexing
    def index(self, theta, phi):
        i = np.clip(np.floor(np.asarray(theta) / self.cell).astype(int), 0, self.nth - 1)
        j = np.floor(((np.asarray(phi) + 180.0) % 360.0) / self.cell).astype(int) % self.nph
        return i, j

    def _spans(self, theta, phi, cell):
        """Belief-cell index ranges [i0, i1) x [j0, j1) covered by a measurement cell of size
        `cell` deg at (theta, phi), rows scaled by 1/sin theta as the field grids are."""
        i0 = np.floor((theta - 0.5 * cell) / self.cell).astype(int); i1 = np.floor((theta + 0.5 * cell) / self.cell).astype(int) + 1
        half_phi = 0.5 * cell / np.maximum(np.sin(np.radians(theta)), 1e-3)
        j0 = np.floor(((phi - half_phi) + 180.0) / self.cell).astype(int); j1 = np.floor(((phi + half_phi) + 180.0) / self.cell).astype(int) + 1
        i0 = np.clip(i0, 0, self.nth - 1); i1 = np.clip(i1, i0 + 1, self.nth)
        j1 = np.minimum(j1, j0 + self.nph)
        return i0, i1, j0, j1

    def _splat(self, theta, phi, cell, fn):
        """Call fn(i, j, sel) for every (measurement, covered belief cell) pair, in vectorised
        passes over the offsets."""
        i0, i1, j0, j1 = self._spans(theta, phi, cell)
        di, dj = i1 - i0, j1 - j0
        for a in range(int(di.max()) if len(di) else 0):
            for b in range(int(dj.max()) if len(dj) else 0):
                sel = (a < di) & (b < dj)
                if not sel.any():
                    continue
                fn((i0 + a)[sel], ((j0 + b)[sel]) % self.nph, sel)

    # ---------------------------------------------------------------- updates
    def visit(self, visits: dict):
        for l in np.unique(visits["level"]):
            m = visits["level"] == l
            def fn(i, j, sel, l=int(l)):
                self.visited[i, j] = np.minimum(self.visited[i, j], l)
            self._splat(visits["theta_L"][m], visits["phi"][m], visits["cell_deg"][m], fn)

    def fuse(self, f: dict, consistent_only: bool = True, gate_sigmas: float = 3.0) -> dict:
        """Fuse a field (field_of_pair's rows). Returns counts."""
        keep = f["consistent"] if consistent_only else np.ones(len(f["rho"]), bool)
        keep &= np.isfinite(f["rho"]) & np.isfinite(f["sigma_rho"]) & (f["sigma_rho"] > 0)
        n_in, n_gated = 0, 0
        has_parts = "sigma_rho_noise" in f
        for l in np.unique(f["level"][keep]):
            m = keep & (f["level"] == l)
            rho, var = f["rho"][m], f["sigma_rho"][m] ** 2
            vn = f["sigma_rho_noise"][m] ** 2 if has_parts else var
            fl = f["sigma_rho_floor"][m] if has_parts else np.zeros(int(m.sum()))
            def fn(i, j, sel, l=int(l), rho=rho, var=var, vn=vn, fl=fl):
                nonlocal n_in, n_gated
                r, v = rho[sel], var[sel]
                P, S = self.P[i, j], self.S[i, j]
                Pn, F = self.Pn[i, j], self.F[i, j]
                with np.errstate(divide="ignore", invalid="ignore"):
                    mean = np.where(P > 0, S / P, 0.0)
                    bvar = np.where(P > 0, 1.0 / Pn + np.where(np.isfinite(F), F, 0.0) ** 2, np.inf)
                coarser = (P > 0) & (v > bvar)
                gate = coarser & ((r - mean) ** 2 > gate_sigmas ** 2 * (v + bvar))
                ok = ~gate
                np.add.at(self.P, (i[ok], j[ok]), 1.0 / v[ok])
                np.add.at(self.S, (i[ok], j[ok]), r[ok] / v[ok])
                np.add.at(self.Pn, (i[ok], j[ok]), 1.0 / np.maximum(vn[sel][ok], 1e-12))
                self.F[i[ok], j[ok]] = np.minimum(self.F[i[ok], j[ok]], fl[sel][ok])
                np.add.at(self.n, (i[ok], j[ok]), 1)
                self.best_level[i[ok], j[ok]] = np.minimum(self.best_level[i[ok], j[ok]], l)
                n_in += int(ok.sum()); n_gated += int(gate.sum())
            self._splat(f["theta_L"][m], f["phi"][m], f["cell_deg"][m], fn)
        self.gated += n_gated
        if "visits" in f:
            self.visit(f["visits"])
        return {"cells_in": n_in, "gated": n_gated}

    def add_truth(self, direction: np.ndarray, distance: np.ndarray, footprint: np.ndarray):
        """The L eye's own rays: footprint-weighted mean of 1/distance per cell, hits only."""
        hit = distance < 1e9
        th, ph = epipolar(direction[hit].astype(np.float64))
        i, j = self.index(th, ph)
        w = 1.0 / footprint[hit].astype(np.float64)
        np.add.at(self.tW, (i, j), w); np.add.at(self.tS, (i, j), w / distance[hit].astype(np.float64)); np.add.at(self.tn, (i, j), 1)

    # ---------------------------------------------------------------- readouts
    def mean(self):
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.where(self.P > 0, self.S / self.P, np.nan)

    def variance(self):
        """1/Pn + F^2: the noise part averages over pairs, the model floor does not (the coarse
        levels' error is the same window on the same edge every time; averaging it would make
        the periphery look sure after ten fixations it is not)."""
        with np.errstate(divide="ignore"):
            return np.where(self.P > 0, 1.0 / self.Pn + np.where(np.isfinite(self.F), self.F, 0.0) ** 2, self.sigma_prior ** 2)

    def sigma(self):
        return np.sqrt(self.variance())

    def truth(self):
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.where(self.tW > 0, self.tS / self.tW, np.nan)

    def cap_mask(self, regard_deg: float, forward=FORWARD) -> np.ndarray:
        return (self.dirs @ np.asarray(forward, np.float32)) >= math.cos(math.radians(regard_deg))

    def rho_along(self, direction: np.ndarray, radius_deg: float) -> float | None:
        """Precision-weighted mean rho of the measured cells within radius of a direction."""
        c = self.dirs @ np.asarray(direction, np.float32)
        m = (c >= math.cos(math.radians(radius_deg))) & (self.P > 0)
        if not m.any():
            return None
        return float(self.S[m].sum() / self.P[m].sum())

    def metrics(self, cap: np.ndarray, rel_inlier: float = 0.25) -> dict:
        """Over the cap: coverage (any level / foveated at levels 0-1 / visited) as area fractions,
        and against the truth on the measured cells with truth: median |rho error|, inlier RMS
        (relative error <= rel_inlier), gross fraction, median |depth error| (m), calibration
        z RMS on inliers."""
        A = self.area; capA = A[cap].sum()
        meas = self.P > 0
        out = {"coverage_any": float(A[cap & meas].sum() / capA), "coverage_fine": float(A[cap & (self.best_level <= 1)].sum() / capA),
               "visited_any": float(A[cap & (self.visited < UNVISITED)].sum() / capA),
               "visited_fine_unmeasured": float(A[cap & (self.visited <= 1) & ~meas].sum() / capA), "gated_total": int(self.gated)}
        j = cap & meas & (self.tW > 0)
        if j.any():
            m, t = self.mean()[j], self.truth()[j]
            err = m - t; rel = np.abs(err) / np.maximum(t, 1e-6)
            inl = rel <= rel_inlier
            z = err / self.sigma()[j]
            bl = self.best_level[j]; dep = np.abs(1.0 / np.maximum(m, 1e-6) - 1.0 / t)
            for band, sel in (("fine", bl <= 1), ("mid", bl == 2), ("coarse", bl >= 3)):
                if sel.any():
                    out[f"{band}_cells"] = int(sel.sum()); out[f"{band}_rho_err_median"] = float(np.median(np.abs(err[sel])))
                    out[f"{band}_depth_err_median_m"] = float(np.median(dep[sel])); out[f"{band}_gross_frac"] = float(1.0 - inl[sel].mean())
            out.update({"judged_cells": int(j.sum()), "rho_err_median": float(np.median(np.abs(err))),
                        "rho_inlier_rms": float(np.sqrt(np.mean(err[inl] ** 2))) if inl.any() else None,
                        "gross_frac": float(1.0 - inl.mean()),
                        "depth_err_median_m": float(np.median(dep)),
                        "z_rms_inliers": float(np.sqrt(np.mean(z[inl] ** 2))) if inl.any() else None,
                        "z_median_abs": float(np.median(np.abs(z)))})
        else:
            out.update({"judged_cells": 0})
        return out

    def snapshot(self) -> dict:
        return {"cell_deg": self.cell, "mean": self.mean().astype(np.float32), "sigma": self.sigma().astype(np.float32),
                "n": self.n.astype(np.int16), "best_level": self.best_level, "visited": self.visited,
                "truth": self.truth().astype(np.float32), "truth_n": self.tn.astype(np.int16)}


# ----------------------------------------------------------------------------------------
# policies
# ----------------------------------------------------------------------------------------

class LevelSigma:
    """Running median sigma_rho per level from this run's own fields (what the field delivers
    at each eccentricity), starting from C1's small-profile numbers."""

    DEFAULT = [0.035, 0.105, 0.134, 0.240, 0.367]

    def __init__(self, n_levels: int, start=None):
        self.vals = list((start or self.DEFAULT)[:n_levels]) + [self.DEFAULT[-1]] * max(0, n_levels - len(start or self.DEFAULT))
        self.samples = [[] for _ in range(n_levels)]

    def update(self, f: dict):
        for l in range(len(self.vals)):
            m = (f["level"] == l) & f["consistent"] & np.isfinite(f["sigma_rho"])
            if m.sum() >= 20:
                self.samples[l].append(float(np.median(f["sigma_rho"][m])))
                self.vals[l] = float(np.median(self.samples[l]))


def candidates(regard_deg: float, step_deg: float) -> np.ndarray:
    """Directions (head frame) on a yaw/pitch grid within the cap about the primary gaze."""
    a = np.arange(-regard_deg, regard_deg + 1e-9, step_deg)
    yy, pp = np.meshgrid(a, a)
    y, p = np.radians(yy.ravel()), np.radians(pp.ravel())
    d = np.stack([np.sin(y) * np.cos(p), np.sin(p), -np.cos(y) * np.cos(p)], -1)
    return d[d @ FORWARD >= math.cos(math.radians(regard_deg))]


class Policy:
    def __init__(self, name: str, belief: SphereBelief, E2: float, eval_factor: float, e_max: float, regard_deg: float = 60.0,
                 cand_deg: float = 2.0, policy_levels: int = 3, seed: int = 0, level_sigma: LevelSigma | None = None,
                 policy_cell_deg: float = 1.0, ior_deg: float | None = None):
        self.name, self.b = name, belief
        self.ior_deg = float(ior_deg if ior_deg is not None else (3.0 if name == "oracle" else 0.0))
        self.edges = level_edges(E2, eval_factor, n_levels_for(E2, eval_factor, e_max))
        self.R = float(min(self.edges[min(policy_levels, len(self.edges)) - 1], e_max))
        self.R_fine = float(self.edges[min(1, len(self.edges) - 1)])          # levels 0-1: 6 deg at the standard warp
        self.regard = regard_deg
        self.cand = candidates(regard_deg, cand_deg)
        self.rng = np.random.default_rng(seed)
        self.ls = level_sigma
        self.cap = belief.cap_mask(regard_deg)
        self.history = []
        # the policy scores on a coarser grid (block means of the belief's variance): 1 deg cells
        # are 25x fewer than 0.2 deg ones and a fixation's gain is a sum over hundreds of them
        self.f = max(1, int(round(policy_cell_deg / belief.cell)))
        self.cell = belief.cell * self.f
        self.nth = belief.nth // self.f; self.nph = belief.nph // self.f
        th = (np.arange(self.nth) + 0.5) * self.cell; ph = (np.arange(self.nph) + 0.5) * self.cell - 180.0
        self.dirs = direction_of(th[:, None] + np.zeros((1, self.nph)), ph[None, :] + np.zeros((self.nth, 1))).astype(np.float32)
        self.area = (np.radians(self.cell) ** 2) * np.sin(np.radians(th))[:, None] + np.zeros((1, self.nph))

        self.cap_c = (self._reduce(self.cap.astype(float)) > 0.5).astype(float)

    def _reduce(self, X: np.ndarray) -> np.ndarray:
        f = self.f
        return X[:self.nth * f, :self.nph * f].reshape(self.nth, f, self.nph, f).mean((1, 3))

    def level_of(self, e):
        return np.searchsorted(self.edges, e, side="left")

    def _gain_field(self) -> np.ndarray:
        """Per belief cell, the variance the policy should treat it as having."""
        b = self.b
        var = b.sigma() ** 2
        if self.name == "coverage":
            return np.where(b.visited <= 1, 0.0, 1.0)            # not yet LOOKED AT finely, measurable or not
        if self.name == "oracle":
            t = b.truth(); m = b.mean()
            err2 = np.where(np.isfinite(t) & np.isfinite(m), (m - t) ** 2, np.nan)
            var = np.where(np.isfinite(err2), err2, var)
        return var

    def _allowed_maps(self):
        """On the policy grid: the finest level that has looked at each cell (block min) and
        whether any measurement exists there (block max). A cell looked at finely and never
        measured at that level is not measurable by looking again (the first loop run: three
        policies re-fixated one such direction up to 49 times); a cell measured only coarsely
        may still be worth a finer look."""
        b = self.b; f = self.f
        vis = b.visited[:self.nth * f, :self.nph * f].reshape(self.nth, f, self.nph, f).min((1, 3)).astype(np.int16)
        meas = (b.best_level[:self.nth * f, :self.nph * f].reshape(self.nth, f, self.nph, f).min((1, 3))).astype(np.int16)
        return vis, meas

    def _score(self, var_map: np.ndarray, vis: np.ndarray, meas: np.ndarray, d: np.ndarray) -> float:
        """Maps on the policy grid. The radius is the fine disc (6 deg) for coverage, the policy
        radius (levels 0..policy_levels-1) for the others."""
        R = self.R_fine if self.name == "coverage" else self.R
        th, ph = epipolar(d)
        i0 = max(0, int((th - R) / self.cell)); i1 = min(self.nth, int((th + R) / self.cell) + 1)
        hp = R / max(math.sin(math.radians(th)), 1e-3)
        j = (np.arange(int((ph - hp + 180.0) / self.cell), int((ph + hp + 180.0) / self.cell) + 1) % self.nph)
        if len(j) >= self.nph:
            j = np.arange(self.nph)
        D = self.dirs[i0:i1][:, j]
        cosang = D @ d.astype(np.float32)
        e = np.degrees(np.arccos(np.clip(cosang, -1.0, 1.0)))
        inside = e <= R
        v = var_map[i0:i1][:, j][inside]
        A = self.area[i0:i1][:, j][inside]
        if self.name == "coverage":
            return float((v * A).sum())
        lev = self.level_of(e[inside])
        # a look counts where the cell is known measurable AT THE FINE LEVELS or where this
        # fixation would look at it at least two levels finer than the finest look that found
        # nothing (levels 0 and 1 are one class: a blank wall fails both). "Measured at any
        # level" was the second run's lock: a ceiling measured coarsely, and wrongly, from
        # afar counted as measurable, the fovea found nothing there, and the gain never fell
        vi = vis[i0:i1][:, j][inside]; me = meas[i0:i1][:, j][inside]
        allowed = (me <= 1) | (lev + 1 < vi)
        I = 1.0 / (np.array(self.ls.vals)[np.minimum(lev, len(self.ls.vals) - 1)] ** 2)
        g = np.where(allowed, 0.5 * np.log1p(v * I), 0.0)
        return float((g * A).sum())

    def choose(self) -> tuple[np.ndarray, dict]:
        if self.name == "random":
            d = self.cand[self.rng.integers(len(self.cand))]
            self.history.append(d)
            return d, {"score": None}
        var_map = self._reduce(self._gain_field()) * self.cap_c          # no gain from cells outside the field of regard
        vis, meas = self._allowed_maps()
        scores = np.array([self._score(var_map, vis, meas, d) for d in self.cand])
        if self.ior_deg > 0 and self.history:
            # explicit inhibition of return: a candidate within ior_deg of a past fixation is out.
            # Off for the policies (the gain model has to retire a direction on its own, and the
            # loop's record says whether it does); on for the oracle, which is a bracket, not a
            # policy, and whose "look where you are most wrong" has nowhere else to go at a
            # depth edge the fovea cannot resolve
            H = np.stack(self.history)
            near = (self.cand @ H.T) >= math.cos(math.radians(self.ior_deg))
            scores = np.where(near.any(1), -np.inf, scores)
        k = int(np.argmax(scores))
        d = self.cand[k]
        self.history.append(d)
        return d, {"score": float(scores[k]), "score_median": float(np.median(scores[np.isfinite(scores)]))}


# ----------------------------------------------------------------------------------------
# self-test
# ----------------------------------------------------------------------------------------

def self_test() -> list[str]:
    fails = []
    b = SphereBelief(0.5)
    # a fine measurement then a coarse disagreeing one: the coarse one is gated
    f1 = {"theta_L": np.array([90.0]), "phi": np.array([0.0]), "cell_deg": np.array([0.5]), "level": np.array([0], np.int8),
          "rho": np.array([0.5]), "sigma_rho": np.array([0.02]), "consistent": np.array([True])}
    f2 = {"theta_L": np.array([90.0]), "phi": np.array([0.0]), "cell_deg": np.array([4.0]), "level": np.array([4], np.int8),
          "rho": np.array([1.5]), "sigma_rho": np.array([0.3]), "consistent": np.array([True])}
    b.fuse(f1); r = b.fuse(f2)
    i, j = b.index(90.0, 0.0)
    if abs(b.mean()[i, j] - 0.5) > 1e-9 or r["gated"] < 1:
        fails.append(f"gating: mean {b.mean()[i, j]:.4f}, gated {r['gated']}")
    # the coarse one covers 8 x 8 cells; those away from the fine cell took it
    if b.n[i + 2, j + 2] != 1 or abs(b.mean()[i + 2, j + 2] - 1.5) > 1e-9:
        fails.append("splat: coarse measurement did not reach its cells")
    # inverse-variance averaging
    b2 = SphereBelief(0.5)
    fa = dict(f1, rho=np.array([1.0]), sigma_rho=np.array([0.1])); fb = dict(f1, rho=np.array([2.0]), sigma_rho=np.array([0.1]))
    b2.fuse(fa); b2.fuse(fb)
    if abs(b2.mean()[i, j] - 1.5) > 1e-9 or abs(b2.sigma()[i, j] - 0.1 / math.sqrt(2)) > 1e-9:
        fails.append("fusion is not inverse-variance averaging")
    # truth accumulation and metrics
    d = direction_of(np.array([90.0, 90.0]), np.array([0.0, 0.0]))
    b2.add_truth(d, np.array([0.5, 0.5]), np.array([1e-5, 1e-5]))
    mt = b2.metrics(b2.cap_mask(60.0))
    if mt["judged_cells"] != 1 or abs(mt["rho_err_median"] - 0.5) > 1e-9:
        fails.append(f"metrics: {mt}")
    # the info policy prefers the unseen: with one fine fixation forward, the argmax is not forward
    b3 = SphereBelief(1.0)
    ls = LevelSigma(5)
    pol = Policy("info", b3, 2.0, 2.0, 45.0, regard_deg=40.0, cand_deg=4.0, level_sigma=ls)
    th, ph = epipolar(FORWARD)
    cells = {"theta_L": np.array([th]), "phi": np.array([ph]), "cell_deg": np.array([6.0]), "level": np.array([0], np.int8),
             "rho": np.array([0.5]), "sigma_rho": np.array([0.02]), "consistent": np.array([True])}
    b3.fuse(cells)
    d, info = pol.choose()
    if float(d @ FORWARD) > math.cos(math.radians(6.0)):
        fails.append("info policy returned to the fixated direction")
    # coverage: a cell visited finely but unmeasured is not gain for info
    b4 = SphereBelief(1.0)
    b4.visit({"theta_L": np.array([th]), "phi": np.array([ph]), "cell_deg": np.array([6.0]), "level": np.array([0], np.int8)})
    pol4 = Policy("info", b4, 2.0, 2.0, 45.0, regard_deg=40.0, cand_deg=4.0, level_sigma=ls)
    vm = pol4._reduce(pol4._gain_field()); vis, meas = pol4._allowed_maps()
    s_here = pol4._score(vm, vis, meas, FORWARD.copy())
    s_away = pol4._score(vm, vis, meas, candidates(40.0, 4.0)[0])
    if not s_here < s_away:
        fails.append(f"a direction looked at finely and found unmeasurable still scores ({s_here:.2f} vs {s_away:.2f} elsewhere)")
    # ... but a cell measured only coarsely (level 3) still invites a finer look
    b5 = SphereBelief(1.0)
    b5.fuse({"theta_L": np.array([th]), "phi": np.array([ph]), "cell_deg": np.array([8.0]), "level": np.array([3], np.int8),
             "rho": np.array([0.5]), "sigma_rho": np.array([0.3]), "consistent": np.array([True])})
    pol5 = Policy("info", b5, 2.0, 2.0, 45.0, regard_deg=40.0, cand_deg=4.0, level_sigma=ls)
    vm5 = pol5._reduce(pol5._gain_field()); vis5, meas5 = pol5._allowed_maps()
    if not pol5._score(vm5, vis5, meas5, FORWARD.copy()) > 0:
        fails.append("a coarsely measured direction scores nothing for a fine look")
    # a coarse (wrong) measurement plus a fine look that found nothing: retired for info too
    b6 = SphereBelief(1.0)
    b6.fuse({"theta_L": np.array([th]), "phi": np.array([ph]), "cell_deg": np.array([8.0]), "level": np.array([3], np.int8),
             "rho": np.array([0.09]), "sigma_rho": np.array([0.3]), "consistent": np.array([True])})
    b6.visit({"theta_L": np.array([th]), "phi": np.array([ph]), "cell_deg": np.array([6.0]), "level": np.array([0], np.int8)})
    pol6 = Policy("info", b6, 2.0, 2.0, 45.0, regard_deg=40.0, cand_deg=4.0, level_sigma=ls)
    vm6 = pol6._reduce(pol6._gain_field()); vis6, meas6 = pol6._allowed_maps()
    if not pol6._score(vm6, vis6, meas6, FORWARD.copy()) < pol6._score(vm6, vis6, meas6, candidates(40.0, 4.0)[0]):
        fails.append("a direction measured coarsely and foveated without result still scores")
    # coverage scores the visit map, not the measurement map
    polc = Policy("coverage", b4, 2.0, 2.0, 45.0, regard_deg=40.0, cand_deg=4.0, level_sigma=ls)
    vmc = polc._reduce(polc._gain_field())
    if not polc._score(vmc, vis, meas, FORWARD.copy()) < polc._score(vmc, vis, meas, candidates(40.0, 4.0)[0]):
        fails.append("coverage still wants a direction already looked at finely")
    # candidates lie within the cap
    c = candidates(30.0, 5.0)
    if (c @ FORWARD).min() < math.cos(math.radians(30.0)) - 1e-9 or len(c) < 50:
        fails.append("candidates outside the cap")
    return fails


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        f = self_test()
        for x in f:
            print("[belief] FAIL", x)
        print(f"[belief] self-test {'FAILED' if f else 'ok'}")
        sys.exit(1 if f else 0)
