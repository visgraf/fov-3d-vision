"""Judge and draw active-loop runs — host side, venv (C2, D17).

    .venv/bin/python tools/active_eval.py previews/loop/calib_info
    .venv/bin/python tools/active_eval.py previews/loop/calib_targets previews/loop/calib_random \\
        previews/loop/calib_coverage previews/loop/calib_info previews/loop/calib_oracle --out previews/loop/calib_compare

Per run: bioeye's four panels on the sphere, <run>/loop_fig.png — posterior depth with the
scanpath | posterior sigma of inverse depth | |depth error| against the L eye's own ray
distances | this run's error and coverage against cumulative rays — drawn in a yaw/pitch
equirect of the field of regard from belief.npz. With several runs and --out: one chart of
every run's curves, a table, compare.json.

Checks, each of which can fail (exit 1):
  (s) replay      the belief rebuilt host-side from field/p<NNN>.npz and the L records, in
                  order, reproduces loop.json's final coverage_any and rho_err_median to 1e-9:
                  the record is complete and the figure is of the belief the loop had.
  (t) calibration final z RMS on inliers in [--z-lo, --z-hi] (0.4, 2.5) on every run: the
                  sigma the belief carries is the error it makes, within a factor.
  (u) learning    coverage_any does not fall, and the cells measured and judged after
                  fixation 0 — the same cells at both moments — have a median |rho error| at
                  the end no worse than then by more than --u-tol (5%): later fixations do not
                  spoil what the first one measured.
  (v) not twice   with a random run present, every policy run's final coverage_fine is at
                  least --twice x random's (0.5): a policy that re-fixates fails here
                  (bio-3d-vision's lock-up).
Reported, not judged: the ranking of the runs at equal rays on coverage_fine, rho_err_median
(all measured cells and the fine band), depth error median — the result of the experiment.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from belief import FORWARD, SphereBelief  # noqa: E402
from rig import epipolar  # noqa: E402


def replay(run: str, lj: dict) -> tuple[SphereBelief, list[dict], dict]:
    """Rebuild the belief from the record. Also returns the fixed-set learning numbers for (u):
    the median |rho error| on the cells measured AND judged after fixation 0, at that moment
    and at the end — the same cells both times. (The first (u) compared the median over all
    measured cells at the end with the median after fixation 0: two medians over different
    sets, and on the classroom fifty fixations of coarse periphery raised the second without
    any measured cell getting worse.)"""
    B = SphereBelief(lj["belief_cell_deg"], sigma_prior=lj["settings"]["sigma_prior"])
    cap = B.cap_mask(lj["settings"]["regard_deg"])
    steps = []; fixed = {}
    for k in range(len(lj["steps"])):
        f = dict(np.load(os.path.join(run, "field", f"p{k:03d}.npz")))
        B.fuse(f)
        s = np.load(os.path.join(run, "L", f"f{k:03d}", "samples.npz"))
        B.add_truth(s["direction"], s["distance"], s["footprint"])
        steps.append(B.metrics(cap))
        if k == 0:
            m0 = cap & (B.P > 0) & (B.tW > 0)
            e0 = np.abs(B.mean()[m0] - B.truth()[m0])
            fixed = {"cells": int(m0.sum()), "start": float(np.median(e0)) if m0.any() else None, "mask": m0}
    if fixed:
        m0 = fixed.pop("mask")
        e1 = np.abs(B.mean()[m0] - B.truth()[m0])
        fixed["end"] = float(np.median(e1)) if m0.any() else None
    return B, steps, fixed


def equirect(B: SphereBelief, X: np.ndarray, regard: float, px_deg: float = 0.5) -> np.ndarray:
    """Sample a belief-grid map into a yaw/pitch image of the cap (nearest cell)."""
    a = np.arange(-regard, regard + 1e-9, px_deg)
    yy, pp = np.meshgrid(a, -a)                                   # pitch up = row 0
    y, p = np.radians(yy), np.radians(pp)
    d = np.stack([np.sin(y) * np.cos(p), np.sin(p), -np.cos(y) * np.cos(p)], -1)
    th, ph = epipolar(d.reshape(-1, 3))
    i, j = B.index(th, ph)
    img = X[i, j].reshape(yy.shape).astype(np.float64)
    img[(d @ FORWARD) < math.cos(math.radians(regard))] = np.nan
    return img


def colour(M: np.ndarray, lo: float, hi: float, kind: str) -> np.ndarray:
    a = np.zeros(M.shape + (3,), np.uint8)
    v = np.clip(np.nan_to_num((M - lo) / max(hi - lo, 1e-9)), 0, 1)
    if kind == "depth":        # near = warm, far = cool
        a[..., 0] = (1 - v) * 255; a[..., 1] = (0.5 - np.abs(v - 0.5)) * 2 * 200; a[..., 2] = v * 255
    elif kind == "sigma":      # green good, red bad
        a[..., 0] = v * 255; a[..., 1] = (1 - v) * 200
    else:                      # error: dark to red
        a[..., 0] = v * 255; a[..., 1] = v * 60; a[..., 2] = (1 - v) * 90
    a[~np.isfinite(M)] = (40, 40, 40)
    return a


def curves_panel(size: int, series: list[tuple[str, np.ndarray, np.ndarray, tuple]], title: str, ylabel: str, ylog: bool = False):
    """A small line chart drawn with PIL: series = [(label, x, y, rgb)]."""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (size, size), (24, 24, 24)); dr = ImageDraw.Draw(im)
    m = 36
    xs = np.concatenate([s[1] for s in series]); ys = np.concatenate([s[2][np.isfinite(s[2])] for s in series])
    if len(ys) == 0:
        dr.text((m, m), "no data", fill=(200, 200, 200)); return im
    x0, x1 = 0.0, float(xs.max()) or 1.0
    if ylog:
        ys = ys[ys > 0]; y0, y1 = float(ys.min()), float(ys.max())
        fy = lambda v: (math.log10(v) - math.log10(y0)) / max(math.log10(y1) - math.log10(y0), 1e-9)
    else:
        y0, y1 = 0.0, float(ys.max()) or 1.0
        fy = lambda v: (v - y0) / max(y1 - y0, 1e-9)
    dr.rectangle([m, m, size - m, size - m], outline=(90, 90, 90))
    dr.text((m, 8), title, fill=(230, 230, 230)); dr.text((4, size // 2), ylabel, fill=(180, 180, 180))
    dr.text((size // 2 - 20, size - m + 4), "rays", fill=(180, 180, 180))
    dr.text((m, size - m + 14), "0", fill=(150, 150, 150)); dr.text((size - m - 40, size - m + 14), f"{x1:.2g}", fill=(150, 150, 150))
    dr.text((m + 2, m + 2), f"{y1:.3g}", fill=(150, 150, 150)); dr.text((m + 2, size - m - 12), f"{y0:.3g}", fill=(150, 150, 150))
    for n, (label, x, y, rgb) in enumerate(series):
        pts = [(m + (xi - x0) / (x1 - x0) * (size - 2 * m), size - m - fy(yi) * (size - 2 * m)) for xi, yi in zip(x, y) if np.isfinite(yi) and (yi > 0 or not ylog)]
        if len(pts) > 1:
            dr.line(pts, fill=rgb, width=2)
        dr.text((size - m - 90, m + 4 + 12 * n), label, fill=rgb)
    return im


PALETTE = {"targets": (200, 200, 200), "random": (120, 160, 255), "coverage": (80, 220, 120), "info": (255, 170, 60), "oracle": (255, 90, 90)}


def figure(run: str, lj: dict, B: SphereBelief, out_path: str, size: int = 480):
    from PIL import Image, ImageDraw
    regard = lj["settings"]["regard_deg"]; px = 0.5
    mean, sig, truth = B.mean(), B.sigma(), B.truth()
    with np.errstate(divide="ignore", invalid="ignore"):
        depth = np.where(np.isfinite(mean) & (mean > 0), 1.0 / mean, np.nan)
        derr = np.where(np.isfinite(depth) & np.isfinite(truth) & (truth > 0), np.abs(depth - 1.0 / truth), np.nan)
    D = equirect(B, depth, regard, px); S = equirect(B, sig, regard, px); E = equirect(B, derr, regard, px)
    n = D.shape[0]; sc = size / n
    dhi = float(np.nanpercentile(D, 95)) if np.isfinite(D).any() else 5.0
    panels = [(colour(D, 0.0, dhi, "depth"), f"posterior depth (0..{dhi:.1f} m) + scanpath"),
              (colour(S, 0.0, 0.4, "sigma"), "posterior sigma rho (0..0.4 /m)"),
              (colour(E, 0.0, 0.5, "err"), "|depth error| vs L rays (0..0.5 m)")]
    steps = lj["steps"]; x = np.array([s["rays_cum"] for s in steps], float)
    cov = np.array([s["coverage_any"] for s in steps]); fine = np.array([s["coverage_fine"] for s in steps])
    err = np.array([s.get("rho_err_median", np.nan) for s in steps], float)
    ferr = np.array([s.get("fine_rho_err_median", np.nan) for s in steps], float)
    half = size // 2
    c1 = curves_panel(half, [("cover any", x, cov, (120, 160, 255)), ("cover fine", x, fine, (80, 220, 120))], f"{lj['policy']}: coverage vs rays", "")
    c2 = curves_panel(half, [("all cells", x, err, (255, 170, 60)), ("fine band", x, ferr, (255, 90, 90))], "rho error median vs rays", "/m")
    im = Image.new("RGB", (4 * (size + 6) + 6, size + 26), (30, 30, 30)); dr = ImageDraw.Draw(im)
    for q, (arr, label) in enumerate(panels):
        p = Image.fromarray(arr).resize((size, size), Image.NEAREST)
        if q == 0:
            d2 = ImageDraw.Draw(p)
            pts = []
            for s in steps:
                d = np.array(s["dir_head"]); yaw = math.degrees(math.atan2(d[0], -d[2])); pit = math.degrees(math.asin(np.clip(d[1], -1, 1)))
                pts.append(((yaw + regard) / px * sc, (regard - pit) / px * sc))
            if len(pts) > 1:
                d2.line(pts, fill=(255, 255, 255), width=1)
            for t, (u, v) in enumerate(pts):
                r = 3 if t < len(pts) - 1 else 5
                d2.ellipse([u - r, v - r, u + r, v + r], outline=(255, 255, 255), fill=(0, 0, 0) if t == 0 else None)
        im.paste(p, (6 + q * (size + 6), 20)); dr.text((6 + q * (size + 6), 4), label, fill=(230, 230, 230))
    cp = Image.new("RGB", (size, size), (24, 24, 24)); cp.paste(c1.resize((size, half)), (0, 0)); cp.paste(c2.resize((size, half)), (0, half))
    im.paste(cp, (6 + 3 * (size + 6), 20)); dr.text((6 + 3 * (size + 6), 4), "curves", fill=(230, 230, 230))
    im.save(out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--out", help="directory for the comparison chart and compare.json (several runs)")
    ap.add_argument("--z-lo", type=float, default=0.4)
    ap.add_argument("--z-hi", type=float, default=2.5)
    ap.add_argument("--twice", type=float, default=0.5)
    ap.add_argument("--no-replay", action="store_true", help="skip (s) and (u) (they re-fuse every field; seconds per run)")
    ap.add_argument("--u-tol", type=float, default=0.05, help="(u): the fixation-0 cells may not get worse by more than this fraction")
    args = ap.parse_args()
    fails, rows = [], []
    for run in args.runs:
        run = os.path.abspath(run)
        lj = json.load(open(os.path.join(run, "loop.json")))
        name = lj["policy"]; tag = os.path.basename(run)
        last, first = lj["steps"][-1], lj["steps"][0]
        if args.no_replay:
            bz = np.load(os.path.join(run, "belief.npz"))
            B = SphereBelief(float(bz["cell_deg"]), sigma_prior=lj["settings"]["sigma_prior"])
            B.P = np.where(bz["sigma"] > 0, 1.0 / bz["sigma"].astype(np.float64) ** 2, 0.0) * (bz["n"] > 0)
            B.S = np.nan_to_num(bz["mean"].astype(np.float64)) * B.P; B.n = bz["n"].astype(np.int32)
            B.best_level = bz["best_level"]; B.visited = bz["visited"]
            B.tW = (bz["truth_n"] > 0).astype(float); B.tS = np.nan_to_num(bz["truth"].astype(np.float64)) * B.tW
            rep_note = "(s) skipped"; fixed = {}; r = {}
        else:
            B, steps, fixed = replay(run, lj)
            r = steps[-1]
            d_cov = abs(r["coverage_any"] - last["coverage_any"]); d_err = abs((r.get("rho_err_median") or 0) - (last.get("rho_err_median") or 0))
            if d_cov > 1e-9 or d_err > 1e-9:
                fails.append(f"(s) {tag}: replay differs (coverage {d_cov:.2e}, rho err {d_err:.2e})")
            rep_note = f"(s) replay {'ok' if d_cov <= 1e-9 and d_err <= 1e-9 else 'DIFFERS'}"
        z = last.get("z_rms_inliers")
        if z is None or not (args.z_lo <= z <= args.z_hi):
            fails.append(f"(t) {tag}: final z RMS {z} outside [{args.z_lo}, {args.z_hi}]")
        if last["coverage_any"] < first["coverage_any"] - 1e-9:
            fails.append(f"(u) {tag}: coverage fell ({first['coverage_any']:.3f} -> {last['coverage_any']:.3f})")
        u_note = "(u) skipped"
        if not args.no_replay and fixed.get("start") is not None:
            u_note = f"(u) fixation-0 cells {fixed['cells']}: rho err median {fixed['start']:.4f} -> {fixed['end']:.4f}"
            if fixed["end"] > fixed["start"] * (1.0 + args.u_tol):
                fails.append(f"(u) {tag}: the cells measured after fixation 0 got worse ({fixed['start']:.4f} -> {fixed['end']:.4f} /m, {fixed['cells']} cells, tol {100 * args.u_tol:.0f}%)")
        figure(run, lj, B, os.path.join(run, "loop_fig.png"))
        verr = [st["vergence_err_m"] for st in lj["steps"] if st.get("vergence_err_m") is not None]
        row = {"run": tag, "policy": name, "fixations": len(lj["steps"]), "rays": last["rays_cum"], "wall_s": lj["wall_seconds"],
               "vergence_err_median_m": float(np.median(verr)) if verr else None,
               "coverage_any": last["coverage_any"], "coverage_fine": last["coverage_fine"], "visited_fine_unmeasured": last["visited_fine_unmeasured"],
               "rho_err_median": last.get("rho_err_median"), "fine_rho_err_median": last.get("fine_rho_err_median"),
               "depth_err_median_m": last.get("depth_err_median_m"), "fine_depth_err_median_m": last.get("fine_depth_err_median_m"),
               "gross_frac": last.get("gross_frac"), "fine_gross_frac": last.get("fine_gross_frac"), "z_rms": z,
               # D21: the split of gross, from the replayed belief (runs recorded before it have no such key in loop.json)
               "outlier_frac": r.get("outlier_frac", last.get("outlier_frac")), "coarse_frac": r.get("coarse_frac", last.get("coarse_frac")),
               "outlier_by_band": [r.get(f"{b_}_outlier_frac", last.get(f"{b_}_outlier_frac")) for b_ in ("fine", "mid", "coarse")],
               "gross_by_band": [r.get(f"{b_}_gross_frac", last.get(f"{b_}_gross_frac")) for b_ in ("fine", "mid", "coarse")], "gated": last["gated_total"],
               "level_sigma": lj["level_sigma_final"], "replay": rep_note, "learning": u_note,
               "u_fixed_cells": fixed.get("cells"), "u_start": fixed.get("start"), "u_end": fixed.get("end"), "steps": lj["steps"]}
        rows.append(row)
        def f(v, fmt=".4f"):
            return "-" if v is None else format(v, fmt)
        print(f"[eval] {tag:<22} {name:<8} k {row['fixations']:3d} rays {row['rays']:.3e} | cover any {row['coverage_any']:.3f} fine {row['coverage_fine']:.3f} | "
              f"rho err med {f(row['rho_err_median'])} (fine {f(row['fine_rho_err_median'])}) /m | depth med {f(row['depth_err_median_m'], '.3f')} (fine {f(row['fine_depth_err_median_m'], '.3f')}) m | "
              f"gross {f(row['gross_frac'], '.3f')} = coarse {f(row['coarse_frac'], '.3f')} + outlier {f(row['outlier_frac'], '.3f')} (outlier fine/mid/coarse {'/'.join(f(x, '.3f') for x in row['outlier_by_band'])}; gross {'/'.join(f(x, '.3f') for x in row['gross_by_band'])}) | z {f(z, '.2f')} | verg err med {f(row['vergence_err_median_m'], '.2f')} m | {rep_note}; {u_note} -> loop_fig.png")
    rnd = [r for r in rows if r["policy"] == "random"]
    if rnd:
        ref = rnd[0]["coverage_fine"]
        for r in rows:
            if r["policy"] not in ("random", "targets") and r["coverage_fine"] < args.twice * ref:
                fails.append(f"(v) {r['run']}: coverage_fine {r['coverage_fine']:.3f} below {args.twice} x random's {ref:.3f}")
    if len(rows) > 1:
        order = sorted(rows, key=lambda r: (r["rho_err_median"] if r["rho_err_median"] is not None else 1e9))
        print("[eval] ranking by rho err median (all measured cells): " + " < ".join(f"{r['policy']} {r['rho_err_median']:.4f}" for r in order))
        order = sorted(rows, key=lambda r: -r["coverage_fine"])
        print("[eval] ranking by coverage_fine: " + " > ".join(f"{r['policy']} {r['coverage_fine']:.3f}" for r in order))
        if args.out:
            os.makedirs(args.out, exist_ok=True)
            from PIL import Image
            size = 480
            def ser(key):
                return [(r["policy"], np.array([s["rays_cum"] for s in r["steps"]], float), np.array([s.get(key, np.nan) for s in r["steps"]], float),
                         PALETTE.get(r["policy"], (200, 200, 200))) for r in rows]
            panels = [curves_panel(size, ser("rho_err_median"), "rho error, median over measured cells", "/m"),
                      curves_panel(size, ser("fine_rho_err_median"), "rho error, fine band (levels 0-1)", "/m"),
                      curves_panel(size, ser("coverage_any"), "coverage, any level", ""),
                      curves_panel(size, ser("coverage_fine"), "coverage, fine (levels 0-1)", "")]
            im = Image.new("RGB", (4 * (size + 6) + 6, size + 12), (30, 30, 30))
            for q, p in enumerate(panels):
                im.paste(p, (6 + q * (size + 6), 6))
            im.save(os.path.join(args.out, "compare.png"))
            with open(os.path.join(args.out, "compare.json"), "w") as fh:
                json.dump({"runs": [{k: v for k, v in r.items() if k != "steps"} for r in rows], "fails": fails}, fh, indent=1)
            print(f"[eval] comparison -> {os.path.join(args.out, 'compare.png')}")
    for x in fails:
        print("[eval] FAIL", x)
    print(f"[eval] {'FAILED' if fails else 'ok'} ({len(fails)} failures)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
