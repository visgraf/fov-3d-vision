"""A second look as the test (D4, D22) — host side, venv, no rendering.

    .venv/bin/python tools/second_look.py previews/loop4/class_coverage_full_500
    .venv/bin/python tools/second_look.py previews/loop4/class_coverage_full_500 --upto 100
    .venv/bin/python tools/second_look.py --self-test

D2 ended on this: at one look, nothing the matcher knows tells most of its wrong peaks from its
right ones. A loop has something a matcher does not: it can look again, from another gaze, with
another window over the same surface. This tool reads a loop run's record and asks what that is
worth, before any fusion is changed.

It replays the fields in order and keeps, per belief cell of the field of regard, every FINE
look (LR-consistent, level <= --max-level (1)): its rho, its sigma, its fixation — up to
--max-looks (8) per cell — and the truth as the loop accumulates it (the L eye's own rays). A
look is BAD when it is off by more than 25% of the true rho and by more than 3 of its own
sigma: the judge's outlier (D21), per look.

Reported, over the cells with truth:
  multiplicity   the share of finely measured cells with 1, 2, 3, 4+ looks.
  repeatability  P(second look bad | first bad) against P(second bad | first good) and the base
                 rate. Equal: wrong peaks are independent across fixations and looking again
                 cures them. P(bad | bad) near 1: they are the scene's (an edge, an occlusion),
                 and no number of looks helps.
  agreement      two looks AGREE when they differ by less than 3 sqrt(s1^2 + s2^2). P(agree) for
                 good-good, good-bad and bad-bad pairs: bad-bad pairs that agree are what a
                 consensus cannot catch.
  fusion         the 25% gross fraction of the fused rho, by number of looks, under four rules:
                 first look only | inverse-variance mean (what the belief does) | median |
                 consensus (the largest set of mutually agreeing looks, inverse-variance fused;
                 two looks that disagree, or no majority, leave the cell UNDECIDED, reported).
                 The last line is the fine band as a whole: what a robust fusion would buy.

Checks, each of which can fail (exit 1):
  (z1) the fine looks collected here are the belief's: the cells with at least one are exactly
       the cells belief.npz has at best_level <= --max-level inside the cap (full run only;
       skipped with --upto).
  (z2) the four rules coincide on one-look cells (they must: there is nothing to fuse).
--self-test: three looks with one confident wrong peak — median and consensus recover the cell,
the mean does not; two looks that disagree are undecided; two that agree fuse.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from belief import SphereBelief  # noqa: E402


class Looks:
    """Per belief cell of a bounding box, up to M (rho, sigma) fine looks in arrival order."""

    def __init__(self, B: SphereBelief, box: tuple[int, int, int, int], M: int):
        self.B, self.box, self.M = B, box, M
        i0, i1, j0, j1 = box
        self.rho = np.full((M, i1 - i0, j1 - j0), np.nan, np.float32); self.sig = np.full_like(self.rho, np.nan)
        self.n = np.zeros((i1 - i0, j1 - j0), np.int32)

    def add(self, f: dict, max_level: int):
        keep = f["consistent"] & (f["level"] <= max_level) & np.isfinite(f["rho"]) & np.isfinite(f["sigma_rho"]) & (f["sigma_rho"] > 0)
        i0, i1, j0, j1 = self.box
        new = np.zeros(self.n.shape, bool); r_new = np.zeros(self.n.shape, np.float32); s_new = np.full(self.n.shape, np.inf, np.float32)
        order = np.argsort(-f["sigma_rho"][keep], kind="stable")     # surest last: where two rows of one pass land on a cell, the last write stands
        rho, sig = f["rho"][keep][order].astype(np.float32), f["sigma_rho"][keep][order].astype(np.float32)
        th_, ph_, cl_ = f["theta_L"][keep][order], f["phi"][keep][order], f["cell_deg"][keep][order]
        def fn(i, j, sel):
            ok = (i >= i0) & (i < i1) & (j >= j0) & (j < j1)
            ii, jj = i[ok] - i0, j[ok] - j0
            better = sig[sel][ok] < s_new[ii, jj]                  # one look per fixation per cell: the surest of its overlapping cells
            ii, jj = ii[better], jj[better]
            new[ii, jj] = True; r_new[ii, jj] = rho[sel][ok][better]; s_new[ii, jj] = sig[sel][ok][better]
        self.B._splat(th_, ph_, cl_, fn)
        slot = np.minimum(self.n, self.M - 1)
        a, b = np.nonzero(new & (self.n < self.M))
        self.rho[slot[a, b], a, b] = r_new[a, b]; self.sig[slot[a, b], a, b] = s_new[a, b]
        self.n += new


def agree(r1, s1, r2, s2, k: float = 3.0):
    return np.abs(r1 - r2) <= k * np.sqrt(s1 ** 2 + s2 ** 2)


def fuse_rules(rho: np.ndarray, sig: np.ndarray) -> dict:
    """rho, sig: (M, N) with NaN in empty slots. Returns the fused rho (N,) under each rule;
    consensus is NaN where undecided."""
    v = np.isfinite(rho); n = v.sum(0)
    w = np.where(v, 1.0 / np.maximum(sig, 1e-12) ** 2, 0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = np.where(v, rho, 0.0).__mul__(w).sum(0) / w.sum(0)
        med = np.nanmedian(np.where(v, rho, np.nan), axis=0)
    M = rho.shape[0]
    votes = np.zeros(rho.shape, np.int32)
    for a in range(M):
        for b in range(M):
            with np.errstate(invalid="ignore"):
                votes[a] += (v[a] & v[b] & agree(rho[a], sig[a], rho[b], sig[b])).astype(np.int32)
    score = np.where(v, votes - 1e-3 * np.nan_to_num(sig / np.nanmax(sig)), -1.0)      # ties: the surer look
    lead = np.argmax(score, axis=0); cols = np.arange(rho.shape[1])
    top = votes[lead, cols]
    with np.errstate(invalid="ignore"):
        member = v & agree(rho, sig, rho[lead, cols][None], sig[lead, cols][None])
    wc = np.where(member, w, 0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        cons = (np.where(member, rho, 0.0) * wc).sum(0) / wc.sum(0)
    decided = (n == 1) | (top * 2 > n)                                                  # a strict majority agrees with the leader
    return {"first": rho[0], "mean": mean, "median": med, "consensus": np.where(decided, cons, np.nan), "n": n}


def analyse(L: Looks, truth: np.ndarray, rel: float = 0.25, k: float = 3.0) -> dict:
    ok = (L.n > 0) & np.isfinite(truth) & (truth > 0)
    rho, sig, t, n = L.rho[:, ok].astype(np.float64), L.sig[:, ok].astype(np.float64), truth[ok].astype(np.float64), L.n[ok]
    out = {"cells": int(ok.sum()), "multiplicity": {str(q): float((n == q).mean()) for q in (1, 2, 3)} | {"4+": float((n >= 4).mean())},
           "looks_median": float(np.median(n)) if ok.any() else None}
    with np.errstate(invalid="ignore"):
        bad = (np.abs(rho - t) > rel * t) & (np.abs(rho - t) > k * sig)
    seen = np.isfinite(rho)
    out["bad_rate_per_look"] = float(bad[seen].mean()) if seen.any() else None
    two = n >= 2
    if two.sum() >= 100:
        b1, b2 = bad[0, two], bad[1, two]
        ag = agree(rho[0, two], sig[0, two], rho[1, two], sig[1, two], k)
        pr = lambda m: float(m.mean()) if len(m) else None
        out["repeatability"] = {"cells": int(two.sum()), "p_bad_first": pr(b1), "p_bad_second": pr(b2),
                                "p_second_bad_given_first_bad": pr(b2[b1]), "p_second_bad_given_first_good": pr(b2[~b1])}
        out["agreement"] = {"good_good": pr(ag[~b1 & ~b2]), "one_bad": pr(ag[b1 ^ b2]), "bad_bad": pr(ag[b1 & b2]),
                            "pairs": {"good_good": int((~b1 & ~b2).sum()), "one_bad": int((b1 ^ b2).sum()), "bad_bad": int((b1 & b2).sum())},
                            "p_bad_given_agree": pr((b1 | b2)[ag]), "p_bad_given_disagree": pr((b1 | b2)[~ag]), "agree_frac": pr(ag)}
    F = fuse_rules(rho, sig)
    gross = lambda x: np.abs(x - t) > rel * t
    rows = []
    for label, m in (("1", n == 1), ("2", n == 2), ("3", n == 3), ("4+", n >= 4), ("all", n >= 1), ("2+", n >= 2)):
        if m.sum() < 50:
            continue
        dec = m & np.isfinite(F["consensus"])
        rows.append({"looks": label, "cells": int(m.sum()), "first": float(gross(F["first"])[m].mean()), "mean": float(gross(F["mean"])[m].mean()),
                     "median": float(gross(F["median"])[m].mean()), "consensus": float(gross(F["consensus"])[dec].mean()) if dec.any() else None,
                     "undecided": float(1.0 - dec.sum() / m.sum())})
    out["fusion"] = rows
    one = n == 1
    out["z2_max_diff_one_look"] = float(max(np.nanmax(np.abs(F[a][one] - F["first"][one])) for a in ("mean", "median", "consensus"))) if one.any() else 0.0
    return out


def print_report(a: dict, tag: str = "[look2]"):
    pc = lambda x: "  -  " if x is None else f"{100 * x:5.1f}"
    m = a["multiplicity"]
    print(f"{tag} {a['cells']} finely measured cells with truth: looks 1 / 2 / 3 / 4+ = {pc(m['1'])} / {pc(m['2'])} / {pc(m['3'])} / {pc(m['4+'])}% (median {a['looks_median']:.0f}); "
          f"a look is bad (beyond 25% and 3 sigma) {pc(a['bad_rate_per_look'])}% of the time")
    if "repeatability" in a:
        r, g = a["repeatability"], a["agreement"]
        print(f"{tag} repeatability on {r['cells']} cells with two looks: P(second bad | first bad) {pc(r['p_second_bad_given_first_bad'])}%  P(second bad | first good) "
              f"{pc(r['p_second_bad_given_first_good'])}%  (base rate first {pc(r['p_bad_first'])}%, second {pc(r['p_bad_second'])}%)")
        print(f"{tag} agreement of the first two looks (within 3 sigma): good-good {pc(g['good_good'])}%  one bad {pc(g['one_bad'])}%  bad-bad {pc(g['bad_bad'])}%  "
              f"(pairs {g['pairs']['good_good']} / {g['pairs']['one_bad']} / {g['pairs']['bad_bad']}); P(a bad look in the pair | agree) {pc(g['p_bad_given_agree'])}%  | disagree {pc(g['p_bad_given_disagree'])}%; {pc(g['agree_frac'])}% agree")
    for r in a["fusion"]:
        print(f"{tag} fusion, {r['looks']:>3} looks, {r['cells']:8d} cells: gross (25%) first look {pc(r['first'])}%  mean {pc(r['mean'])}%  median {pc(r['median'])}%  "
              f"consensus {pc(r['consensus'])}% with {pc(r['undecided'])}% undecided")


def self_test() -> list[str]:
    fails = []
    nan = np.nan
    #            three looks, one confident wrong | two that disagree | two that agree | one look
    rho = np.array([[0.40, 0.40, 0.40, 0.40], [0.90, 0.90, 0.42, nan], [0.41, nan, nan, nan]])
    sig = np.array([[0.02, 0.02, 0.02, 0.02], [0.01, 0.01, 0.02, nan], [0.02, nan, nan, nan]])
    F = fuse_rules(rho, sig)
    if not (abs(F["median"][0] - 0.41) < 1e-9 and abs(F["consensus"][0] - 0.405) < 1e-9 and F["mean"][0] > 0.6):
        fails.append(f"three looks, one wrong: median {F['median'][0]}, consensus {F['consensus'][0]}, mean {F['mean'][0]}")
    if np.isfinite(F["consensus"][1]):
        fails.append(f"two looks that disagree should be undecided, got {F['consensus'][1]}")
    if not abs(F["consensus"][2] - 0.41) < 1e-9:
        fails.append(f"two looks that agree: consensus {F['consensus'][2]}")
    if not (F["consensus"][3] == F["mean"][3] == F["median"][3] == 0.40):
        fails.append("one look: the rules differ")
    # the collector: two fixations over the same cell give it two looks, in order, one per fixation
    B = SphereBelief(1.0)
    L = Looks(B, (80, 100, 170, 190), 4)
    f = {"theta_L": np.array([90.5, 90.5]), "phi": np.array([0.5, 0.5]), "cell_deg": np.array([0.98, 0.98]), "level": np.array([0, 1], np.int8),
         "rho": np.array([0.5, 0.7]), "sigma_rho": np.array([0.02, 0.05]), "consistent": np.array([True, True])}
    L.add(f, 1); L.add(dict(f, rho=np.array([0.52, 0.9])), 1)
    i, j = B.index(90.5, 0.5); a, b = i - 80, j - 170
    if L.n[a, b] != 2 or abs(L.rho[0, a, b] - 0.5) > 1e-6 or abs(L.rho[1, a, b] - 0.52) > 1e-6:
        fails.append(f"collector: n {L.n[a, b]}, looks {L.rho[:2, a, b]}")
    return fails


def main():
    if "--self-test" in sys.argv:
        f = self_test()
        for x in f:
            print("[look2] FAIL", x)
        print(f"[look2] self-test {'FAILED' if f else 'ok'}")
        sys.exit(1 if f else 0)
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--upto", type=int, default=None, help="read the record up to this many fixations")
    ap.add_argument("--max-level", type=int, default=1)
    ap.add_argument("--max-looks", type=int, default=8)
    args = ap.parse_args()
    run = os.path.abspath(args.run)
    lj = json.load(open(os.path.join(run, "loop.json")))
    K = len(lj["steps"]) if args.upto is None else min(args.upto, len(lj["steps"]))
    B = SphereBelief(lj["belief_cell_deg"], sigma_prior=lj["settings"]["sigma_prior"])
    cap = B.cap_mask(lj["settings"]["regard_deg"])
    ii, jj = np.nonzero(cap); box = (int(ii.min()), int(ii.max()) + 1, int(jj.min()), int(jj.max()) + 1)
    L = Looks(B, box, args.max_looks)
    for k in range(K):
        f = dict(np.load(os.path.join(run, "field", f"p{k:03d}.npz")))
        L.add(f, args.max_level)
        s = np.load(os.path.join(run, "L", f"f{k:03d}", "samples.npz"))
        B.add_truth(s["direction"], s["distance"], s["footprint"])
    i0, i1, j0, j1 = box
    capb = cap[i0:i1, j0:j1]
    truth = np.where(capb, B.truth()[i0:i1, j0:j1], np.nan)
    a = analyse(L, truth)
    print(f"[look2] {run}: {K} fixations, fine = levels 0-{args.max_level}, up to {args.max_looks} looks kept per cell")
    print_report(a)
    fails = []
    if args.upto is None or K == len(lj["steps"]):
        bz = np.load(os.path.join(run, "belief.npz"))
        mine = (L.n > 0) & capb; theirs = (bz["best_level"][i0:i1, j0:j1] <= args.max_level) & capb
        diff = int((mine ^ theirs).sum())
        a["z1_cells_differ"] = diff
        if diff:
            fails.append(f"(z1) {diff} cells differ between the fine looks collected here ({int(mine.sum())}) and belief.npz's best_level <= {args.max_level} ({int(theirs.sum())})")
        print(f"[look2] (z1) fine cells here {int(mine.sum())}, in belief.npz {int(theirs.sum())}, differ {diff}")
    else:
        print("[look2] (z1) skipped (--upto)")
    if a["z2_max_diff_one_look"] > 1e-6:
        fails.append(f"(z2) the rules differ on one-look cells by {a['z2_max_diff_one_look']:.2e}")
    for x in fails:
        print("[look2] FAIL", x)
    a.update({"run": run, "fixations": K, "max_level": args.max_level, "fails": fails})
    out = os.path.join(run, "second_look.json" if args.upto is None else f"second_look_k{K}.json")
    with open(out, "w") as fh:
        json.dump(a, fh, indent=1)
    print(f"[look2] {'FAILED' if fails else 'ok'} ({len(fails)} failures) -> {out}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
