"""Collect the stereo instrument's results over the E2 / e_max sweep into one table and chart (B3).

    .venv/bin/python tools/stereo_sweep.py previews/sweep_b3/e2_1 previews/sweep_b3/e2_2 previews/sweep_b3/e2_4 \\
        previews/sweep_b3/emax_30 previews/sweep_b3/emax_60 --out previews/sweep_b3

Each argument is a fixation_pairs.py run that has been through stereo_truth.py and
stereo_instrument.py (stereo.json present). Writes <out>/sweep.json, sweep.csv and sweep.png:
per setting, rays per pair, the instrument's inlier RMS and gross fraction at the fixated cards,
the bound RMS, and the information per ray; the chart is error against rays per pair (log x) with
the bound beside the instrument. The objective D11 named is the first column pair (disparity
error at the fixated targets against its cost); the information per ray is the matcher-free
reading of the same trade. Host side, venv. No check here: the checks ran per setting.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys

import numpy as np


def draw(path: str, rows: list[dict]) -> None:
    from PIL import Image, ImageDraw, ImageFont
    Wp, Hp, L, R, T, B = 960, 640, 90, 30, 50, 70
    im = Image.new("RGB", (Wp, Hp), "white"); dr = ImageDraw.Draw(im)
    try:
        dr.font = ImageFont.load_default(size=15)
    except TypeError:
        pass
    xs = [r["rays_per_pair"] for r in rows]
    ys = [v for r in rows for v in (r["inlier_rms_s0"], r["bound_rms_s0"]) if v is not None]
    x0, x1 = math.log10(min(xs)) - 0.15, math.log10(max(xs)) + 0.15
    ymax = max(ys) * 1.2
    def X(v): return L + (math.log10(v) - x0) / (x1 - x0) * (Wp - L - R)
    def Y(v): return Hp - B - min(v, ymax) / ymax * (Hp - T - B)
    dr.rectangle([L, T, Wp - R, Hp - B], outline="black")
    for k in range(4, 9):
        for m in (1, 2, 5):
            v = m * 10 ** k
            if x0 <= math.log10(v) <= x1:
                dr.line([X(v), Hp - B, X(v), Hp - B + 5], fill="black"); dr.text((X(v) - 18, Hp - B + 8), f"{v:.0e}".replace("e+0", "e"), fill="black")
    step = 0.1 if ymax < 1.5 else 0.5
    for v in np.arange(0, ymax + 1e-9, step):
        dr.line([L - 5, Y(v), L, Y(v)], fill="black"); dr.text((L - 50, Y(v) - 8), f"{v:.1f}", fill="black")
        dr.line([L, Y(v), Wp - R, Y(v)], fill=(230, 230, 230))
    for key, col, label in (("inlier_rms_s0", (200, 40, 40), "instrument: inlier RMS at fixated cards"),
                            ("bound_rms_s0", (40, 80, 200), "bound: 1/sqrt(Fisher information)")):
        pts = sorted((r["rays_per_pair"], r[key], r["setting"]) for r in rows if r[key] is not None)
        for (xa, ya, _), (xb, yb, _) in zip(pts, pts[1:]):
            dr.line([X(xa), Y(ya), X(xb), Y(yb)], fill=col, width=2)
        for x, y, name in pts:
            dr.ellipse([X(x) - 5, Y(y) - 5, X(x) + 5, Y(y) + 5], fill=col)
            if key == "inlier_rms_s0":
                dr.text((X(x) + 8, Y(y) - 18), name, fill="black")
    dr.line([Wp - R - 330, T + 14, Wp - R - 295, T + 14], fill=(200, 40, 40), width=3); dr.text((Wp - R - 285, T + 6), "instrument: inlier RMS at fixated cards", fill="black")
    dr.line([Wp - R - 330, T + 38, Wp - R - 295, T + 38], fill=(40, 80, 200), width=3); dr.text((Wp - R - 285, T + 30), "bound: 1/sqrt(Fisher information)", fill="black")
    dr.text((L, 15), "B3: disparity error at the fixated cards against rays per pair (units of s0)", fill="black")
    dr.text((Wp // 2 - 40, Hp - 22), "rays per pair (log)", fill="black"); dr.text((8, T - 30), "err / s0", fill="black")
    im.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    rows = []
    for run in args.runs:
        st = json.load(open(os.path.join(run, "stereo.json")))["summary"]
        pj = json.load(open(os.path.join(run, "pairs.json")))
        s0 = st["s0_deg"]
        rows.append({"setting": f"E2 {st['E2_deg']:g} e_max {st['e_max_deg']:g}", "run": os.path.abspath(run),
                     "E2_deg": st["E2_deg"], "e_max_deg": st["e_max_deg"], "raster": pj["warp"]["raster"],
                     "samples_per_fixation": st["samples_per_fixation"], "rays_per_pair": st["rays_per_pair"],
                     "judged_pairs": st["judged_pairs"], "judged_cells": st["judged_cells"],
                     "inlier_rms_deg": st["inlier_rms_deg"], "inlier_rms_s0": st["inlier_rms_s0"],
                     "gross_frac": st["gross_frac"], "gross_frac_edge_free_median": st.get("gross_frac_edge_free_median"),
                     "bound_rms_deg": st["bound_rms_deg"], "bound_rms_s0": None if st["bound_rms_deg"] is None else st["bound_rms_deg"] / s0,
                     "rms_over_bound_median": st["rms_over_bound_median"],
                     "info_per_ray_median": st["info_per_ray_median"], "info_per_ray_mean": st["info_per_ray_mean"],
                     "matchable_frac_median": st["matchable_frac_median"], "noise": st["noise"], "fails": st["fails"],
                     "pair_seconds_median": pj.get("pair_seconds_median")})
    rows.sort(key=lambda r: r["rays_per_pair"])
    keys = ["setting", "raster", "samples_per_fixation", "rays_per_pair", "judged_pairs", "judged_cells", "inlier_rms_deg", "inlier_rms_s0",
            "gross_frac", "gross_frac_edge_free_median", "bound_rms_deg", "bound_rms_s0", "rms_over_bound_median", "info_per_ray_median", "info_per_ray_mean",
            "matchable_frac_median", "pair_seconds_median", "noise"]
    with open(os.path.join(args.out, "sweep.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in keys})
    with open(os.path.join(args.out, "sweep.json"), "w") as fh:
        json.dump(rows, fh, indent=1)
    draw(os.path.join(args.out, "sweep.png"), rows)
    print(f"{'setting':<18} {'raster':>6} {'rays/pair':>10} {'RMS s0':>7} {'gross':>6} {'bound s0':>8} {'RMS/bnd':>7} {'info/ray':>10} {'fails':>5}")
    for r in rows:
        print(f"{r['setting']:<18} {r['raster']:>6} {r['rays_per_pair']:>10} {r['inlier_rms_s0'] if r['inlier_rms_s0'] is None else round(r['inlier_rms_s0'], 3):>7} "
              f"{'-' if r['gross_frac'] is None else f'{100 * r['gross_frac']:.1f}%':>6} {'-' if r['bound_rms_s0'] is None else round(r['bound_rms_s0'], 3):>8} "
              f"{'-' if r['rms_over_bound_median'] is None else round(r['rms_over_bound_median'], 2):>7} {'-' if r['info_per_ray_median'] is None else f'{r['info_per_ray_median']:.3e}':>10} {len(r['fails']):>5}")
    best_i = min((r for r in rows if r["inlier_rms_s0"] is not None), key=lambda r: r["inlier_rms_s0"])
    best_b = max((r for r in rows if r["info_per_ray_median"] is not None), key=lambda r: r["info_per_ray_median"])
    print(f"[sweep] lowest instrument error at the fixated cards: {best_i['setting']} ({best_i['inlier_rms_s0']:.3f} s0 at {best_i['rays_per_pair']} rays/pair); "
          f"most information per ray: {best_b['setting']} ({best_b['info_per_ray_median']:.3e}). "
          f"{'They agree.' if best_i is best_b else 'They disagree: that is the result, not a tie-break.'} -> {args.out}")


if __name__ == "__main__":
    main()
