"""Sphere views (the cherry on top): (RGB, Depth) of a scene as it is and as the engine saw it,
in two formats — equirectangular (lat-long about the primary gaze, preview360's convention)
and the project's own sphere map in epipolar coordinates (D13: phi about the baseline across,
theta from the head's +X down, so the baseline axis is the top and bottom edge, the primary gaze
the centre, and every epipolar line a horizontal row). Host side, venv.

    .venv/bin/python tools/sphere_views.py previews/loop3/class_coverage_full \\
        --truth previews/reference_small/classroom_L [--cell 0.2] [--width 1800]

Sources:
  as it is        RGB from --truth's pano.exr (a preview360 render at the L eye; pass the
                  per-eye reference from B2, or render one with preview360.py --eye-offset)
                  and its Depth pass (ray distance from the eye). Without --truth, the L eye's
                  own rays from the loop's record stand in: Blender's radiance and Z per sample,
                  finest-owns over the cells the eye sampled — labelled so on the sheet.
  as the engine   RGB: the loop's fixations integrated finest-owns on the sphere (D8/D9 —
  saw it          sharp where the fovea has been, blurred in the periphery, dark where never
                  looked). Depth: 1 / the belief's inverse-depth mean from belief.npz — the
                  stereo reconstruction, on the cells the belief measured.

Output, <run>/views/: {truth,engine}_{equirect,sphere}_{rgb,depth}.png, the depths also as
.npy (metres, NaN where unknown), and sheet.png — two rows (as it is / as the engine saw it),
four columns (equirect RGB, equirect depth, sphere RGB, sphere depth), the scanpath drawn on
the engine's equirect RGB, one shared depth scale.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rig import epipolar  # noqa: E402
from stereo_field import direction_of  # noqa: E402

FORWARD = np.array([0.0, 0.0, -1.0])


# ----------------------------------------------------------------------------------------
# geometry: the two formats
# ----------------------------------------------------------------------------------------

def equirect_dirs(width: int) -> np.ndarray:
    """(H, W, 3) head-frame directions of an equirect image, preview360's convention:
    lon = (u - 0.5) 2pi, lat = (0.5 - v) pi, v = 0 top; d = (sin lon cos lat, sin lat, -cos lon cos lat)."""
    H = width // 2
    u = (np.arange(width) + 0.5) / width; v = (np.arange(H) + 0.5) / H
    lon = (u - 0.5) * 2 * np.pi; lat = (0.5 - v) * np.pi
    cl, sl = np.cos(lat)[:, None], np.sin(lat)[:, None]
    return np.stack([np.sin(lon)[None, :] * cl, sl + np.zeros((1, width)), -np.cos(lon)[None, :] * cl], -1)


def sphere_dirs(cell: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(theta, phi, dirs) of the epipolar sphere map at `cell` deg: theta 0..180 down (rows),
    phi -180..180 across (columns)."""
    th = (np.arange(int(round(180 / cell))) + 0.5) * cell
    ph = (np.arange(int(round(360 / cell))) + 0.5) * cell - 180.0
    return th, ph, direction_of(th[:, None] + np.zeros((1, len(ph))), ph[None, :] + np.zeros((len(th), 1)))


def pano_lookup(d: np.ndarray, W: int, H: int) -> tuple[np.ndarray, np.ndarray]:
    """Pixel (row, col) of a head-frame direction in a preview360 pano."""
    lon = np.arctan2(d[..., 0], -d[..., 2]); lat = np.arcsin(np.clip(d[..., 1], -1, 1))
    u = lon / (2 * np.pi) + 0.5; v = 0.5 - lat / np.pi
    return np.clip((v * H).astype(int), 0, H - 1), np.clip((u * W).astype(int), 0, W - 1) % W


# ----------------------------------------------------------------------------------------
# the sources
# ----------------------------------------------------------------------------------------

def finest_owns(theta, phi, val, fp, dist, cell: float, factor: float = 1.5):
    """Finest-owns integration onto the (theta, phi) grid, each sample painted over the cells
    its footprint covers (a periphery sample at 2.4 deg spacing covers a 12 x 12 block of 0.2 deg
    cells; without this the map at s_eval is 18% filled and the picture is a scatter of dots).
    Per cell: the finest covering footprint, then the 1/footprint-weighted mean of the covering
    samples within `factor` of it (D9's rule). Returns rgb (nph, nth, 3), depth (nph, nth) as
    the same mean of ray distance over hits, and the finest footprint per cell (sr). Maps are
    (theta rows, phi columns)."""
    nth, nph = int(round(180 / cell)), int(round(360 / cell))
    n = nth * nph
    spacing = np.degrees(np.sqrt(fp))                                    # deg, the sample's own cell
    half = np.maximum(np.rint(0.5 * spacing / cell).astype(int), 0)      # half-width in grid cells along theta
    sin_t = np.maximum(np.sin(np.radians(theta)), 0.05)
    half_p = np.maximum(np.rint(0.5 * spacing / (cell * sin_t)).astype(int), 0)
    i0 = np.floor(theta / cell).astype(int); j0 = np.floor(((phi + 180.0) % 360.0) / cell).astype(int)
    order = np.argsort(half); theta, phi, val, fp, dist = theta[order], phi[order], val[order], fp[order], dist[order]
    half, half_p, i0, j0 = half[order], half_p[order], i0[order], j0[order]
    def each_cover(fn):
        """Call fn(idx, sel) for every (sample, covered cell) in vectorised passes over offsets."""
        hmax, hpmax = int(half.max()), int(half_p.max())
        for a in range(-hmax, hmax + 1):
            for b in range(-hpmax, hpmax + 1):
                sel = (np.abs(a) <= half) & (np.abs(b) <= half_p)
                if not sel.any():
                    continue
                i = np.clip(i0[sel] + a, 0, nth - 1); j = (j0[sel] + b) % nph
                fn(i * nph + j, sel)
    finest = np.full(n, np.inf)
    each_cover(lambda idx, sel: np.minimum.at(finest, idx, fp[sel]))
    wsum = np.zeros(n); acc = np.zeros((n, 3)); wd = np.zeros(n); dacc = np.zeros(n)
    hit = dist < 1e9
    def add(idx, sel):
        own = fp[sel] <= factor * finest[idx]
        w = np.where(own, 1.0 / fp[sel], 0.0)
        np.add.at(wsum, idx, w)
        for c in range(3):
            np.add.at(acc[:, c], idx, w * val[sel, c])
        wh = w * hit[sel]
        np.add.at(wd, idx, wh); np.add.at(dacc, idx, wh * np.where(hit[sel], dist[sel], 0.0))
    each_cover(add)
    with np.errstate(invalid="ignore", divide="ignore"):
        rgb = acc / wsum[:, None]; dep = dacc / wd
    return rgb.reshape(nth, nph, 3), dep.reshape(nth, nph), finest.reshape(nth, nph)


def load_engine(run: str, cell: float):
    """The loop's L records integrated on the sphere, and the belief's depth."""
    lj = json.load(open(os.path.join(run, "loop.json")))
    T, P, V, F, D = [], [], [], [], []
    for k in range(len(lj["steps"])):
        s = np.load(os.path.join(run, "L", f"f{k:03d}", "samples.npz"))
        th, ph = epipolar(s["direction"].astype(np.float64))
        T.append(th); P.append(ph); V.append(s["value"].astype(np.float64)); F.append(s["footprint"].astype(np.float64)); D.append(s["distance"].astype(np.float64))
    th, ph, val, fp, dist = (np.concatenate(x) for x in (T, P, V, F, D))
    rgb, dep_rays, finest = finest_owns(th, ph, val, fp, dist, cell)
    bz = np.load(os.path.join(run, "belief.npz"))
    bcell = float(bz["cell_deg"])
    mean = bz["mean"].astype(np.float64)
    with np.errstate(divide="ignore", invalid="ignore"):
        dep_belief = np.where(np.isfinite(mean) & (mean > 0), 1.0 / mean, np.nan)     # (nth_b, nph_b): theta rows, phi cols
    # resample the belief's depth onto the view grid (theta rows, phi columns, as the belief)
    nth, nph = rgb.shape[0], rgb.shape[1]
    ti = np.clip(((np.arange(nth) + 0.5) * cell / bcell).astype(int), 0, dep_belief.shape[0] - 1)
    pj = np.clip(((np.arange(nph) + 0.5) * cell / bcell).astype(int), 0, dep_belief.shape[1] - 1)
    dep = dep_belief[np.ix_(ti, pj)]
    truth_rho = bz["truth"].astype(np.float64)
    with np.errstate(divide="ignore", invalid="ignore"):
        dep_truth_b = np.where(np.isfinite(truth_rho) & (truth_rho > 0), 1.0 / truth_rho, np.nan)[np.ix_(ti, pj)]
    scan = [np.array(st["dir_head"]) for st in lj["steps"]]
    return {"rgb": rgb, "depth": dep, "depth_rays": dep_rays, "depth_truth_belief": dep_truth_b, "finest": finest,
            "scan": scan, "policy": lj["policy"], "profile": lj["settings"].get("profile"), "fixations": len(lj["steps"])}


def load_truth(pano_dir: str):
    import OpenEXR
    chans = {}
    with OpenEXR.File(os.path.join(pano_dir, "pano.exr"), separate_channels=True) as f:
        for part in f.parts:
            for name, ch in part.channels.items():
                chans[name] = np.asarray(ch.pixels)
    def find(suffix):
        for k, v in chans.items():
            if k.endswith(suffix):
                return v
        raise KeyError(suffix)
    rgb = np.stack([find(f"Combined.{c}") for c in "RGB"], -1).astype(np.float64)
    dep = find("Depth.Z").astype(np.float64)
    dep = np.where(dep < 1e9, dep, np.nan)
    meta = json.load(open(os.path.join(pano_dir, "meta.json"))) if os.path.exists(os.path.join(pano_dir, "meta.json")) else {}
    return {"rgb": rgb, "depth": dep, "meta": meta}


# ----------------------------------------------------------------------------------------
# images
# ----------------------------------------------------------------------------------------

def tonemap(rgb: np.ndarray, white: float) -> np.ndarray:
    a = np.clip(np.nan_to_num(rgb) / max(white, 1e-9), 0, 1) ** (1 / 2.2)
    a[~np.isfinite(rgb).all(-1)] = 0.16
    return (a * 255).astype(np.uint8)


def depthmap(dep: np.ndarray, z_lo: float, z_hi: float) -> np.ndarray:
    """Depth on a log scale between z_lo and z_hi, warm near, cool far; unknown = dark grey."""
    with np.errstate(divide="ignore", invalid="ignore"):
        v = np.clip((np.log(dep) - math.log(z_lo)) / max(math.log(z_hi) - math.log(z_lo), 1e-9), 0, 1)
    v = np.nan_to_num(v)
    a = np.zeros(dep.shape + (3,), np.uint8)
    a[..., 0] = (1 - v) * 255; a[..., 1] = (0.5 - np.abs(v - 0.5)) * 2 * 200; a[..., 2] = v * 255
    a[~(np.isfinite(dep) & (dep > 0))] = (40, 40, 40)
    return a


def to_equirect(sphere_map: np.ndarray, cell: float, width: int) -> np.ndarray:
    """Sample a (theta rows, phi columns) sphere map into an equirect image (nearest)."""
    d = equirect_dirs(width)
    th, ph = epipolar(d.reshape(-1, 3))
    nth, nph = sphere_map.shape[0], sphere_map.shape[1]
    i = np.clip(np.floor(th / cell).astype(int), 0, nth - 1); j = np.floor(((ph + 180.0) % 360.0) / cell).astype(int) % nph
    return sphere_map[i, j].reshape(d.shape[0], d.shape[1], *sphere_map.shape[2:])


def to_sphere(equirect: np.ndarray, cell: float) -> np.ndarray:
    """Sample an equirect image (preview360's convention) into the (theta rows, phi columns) sphere map."""
    th, ph, d = sphere_dirs(cell)
    r, c = pano_lookup(d, equirect.shape[1], equirect.shape[0])
    return equirect[r, c]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", help="a loop run (loop.json, belief.npz, L/)")
    ap.add_argument("--truth", help="a preview360 output directory (pano.exr) rendered at the L eye")
    ap.add_argument("--cell", type=float, default=None, help="sphere-map cell, deg; default the belief's")
    ap.add_argument("--width", type=int, default=1800, help="equirect width (height is half)")
    ap.add_argument("--white", type=float, default=None, help="radiance mapped to white; default the 99th percentile of the truth (or the engine)")
    ap.add_argument("--z-range", type=float, nargs=2, default=None, metavar=("ZLO", "ZHI"), help="depth colour scale, m (log); default the 2nd and 98th percentiles of the truth depth")
    args = ap.parse_args()
    from PIL import Image, ImageDraw

    run = os.path.abspath(args.run)
    bz = np.load(os.path.join(run, "belief.npz"))
    cell = args.cell or float(bz["cell_deg"])
    out = os.path.join(run, "views"); os.makedirs(out, exist_ok=True)
    E = load_engine(run, cell)
    truth_src = None
    if args.truth:
        Tr = load_truth(args.truth)
        truth_src = f"pano.exr ({os.path.basename(os.path.abspath(args.truth))})"
        t_eq_rgb = Tr["rgb"]; t_eq_dep = Tr["depth"]
        if t_eq_rgb.shape[1] != args.width:                                    # resample to the requested width
            d = equirect_dirs(args.width); r, c = pano_lookup(d, t_eq_rgb.shape[1], t_eq_rgb.shape[0])
            t_eq_rgb, t_eq_dep = t_eq_rgb[r, c], t_eq_dep[r, c]
        t_sp_rgb, t_sp_dep = to_sphere(Tr["rgb"], cell), to_sphere(Tr["depth"], cell)
    else:
        truth_src = "the L eye's own rays (no --truth)"
        t_sp_rgb, t_sp_dep = E["rgb"], E["depth_rays"]
        t_eq_rgb, t_eq_dep = to_equirect(t_sp_rgb, cell, args.width), to_equirect(t_sp_dep, cell, args.width)
    e_sp_rgb, e_sp_dep = E["rgb"], E["depth"]
    e_eq_rgb, e_eq_dep = to_equirect(e_sp_rgb, cell, args.width), to_equirect(e_sp_dep, cell, args.width)

    white = args.white or float(np.nanpercentile(t_eq_rgb, 99))
    zref = t_eq_dep[np.isfinite(t_eq_dep) & (t_eq_dep > 0)]
    z_lo, z_hi = args.z_range or ((float(np.percentile(zref, 2)), float(np.percentile(zref, 98))) if len(zref) else (0.5, 10.0))
    z_hi = max(z_hi, z_lo * 1.01)

    panels = {"truth_equirect_rgb": tonemap(t_eq_rgb, white), "truth_equirect_depth": depthmap(t_eq_dep, z_lo, z_hi),
              "truth_sphere_rgb": tonemap(t_sp_rgb, white), "truth_sphere_depth": depthmap(t_sp_dep, z_lo, z_hi),
              "engine_equirect_rgb": tonemap(e_eq_rgb, white), "engine_equirect_depth": depthmap(e_eq_dep, z_lo, z_hi),
              "engine_sphere_rgb": tonemap(e_sp_rgb, white), "engine_sphere_depth": depthmap(e_sp_dep, z_lo, z_hi)}
    for k, a in panels.items():
        Image.fromarray(a).save(os.path.join(out, k + ".png"))
    for k, a in (("truth_equirect_depth", t_eq_dep), ("truth_sphere_depth", t_sp_dep), ("engine_equirect_depth", e_eq_dep), ("engine_sphere_depth", e_sp_dep)):
        np.save(os.path.join(out, k + ".npy"), a.astype(np.float32))

    # the scanpath on the engine's equirect RGB
    W, H = args.width, args.width // 2
    im_scan = Image.fromarray(panels["engine_equirect_rgb"]); dr = ImageDraw.Draw(im_scan)
    pts = []
    for d in E["scan"]:
        lon = math.atan2(d[0], -d[2]); lat = math.asin(max(-1.0, min(1.0, d[1])))
        pts.append(((lon / (2 * math.pi) + 0.5) * W, (0.5 - lat / math.pi) * H))
    for a, b in zip(pts[:-1], pts[1:]):
        if abs(a[0] - b[0]) < W / 2:
            dr.line([a, b], fill=(255, 255, 255), width=1)
    for t, (u, v) in enumerate(pts):
        r = 3 if t < len(pts) - 1 else 5
        dr.ellipse([u - r, v - r, u + r, v + r], outline=(255, 255, 255), fill=(0, 0, 0) if t == 0 else None)
    im_scan.save(os.path.join(out, "engine_equirect_rgb_scanpath.png"))

    # the sheet: two rows, four columns, equirect panels 2:1 and sphere panels 1:2 scaled to one height
    ph_ = 360
    def fit(a, h):
        im = Image.fromarray(a); return im.resize((int(round(im.width * h / im.height)), h), Image.NEAREST if a.shape[0] < h else Image.BILINEAR)
    row_t = [fit(panels["truth_equirect_rgb"], ph_), fit(panels["truth_equirect_depth"], ph_), fit(panels["truth_sphere_rgb"], ph_), fit(panels["truth_sphere_depth"], ph_)]
    row_e = [fit(np.asarray(im_scan), ph_), fit(panels["engine_equirect_depth"], ph_), fit(panels["engine_sphere_rgb"], ph_), fit(panels["engine_sphere_depth"], ph_)]
    widths = [im.width for im in row_t]
    band = 40
    sheet = Image.new("RGB", (sum(widths) + 6 * 5, 2 * (ph_ + band) + 22), (30, 30, 30)); d2 = ImageDraw.Draw(sheet)
    labels = ["equirectangular RGB (yaw across, pitch down)", f"equirectangular depth ({z_lo:.2f}-{z_hi:.1f} m, log; warm near)", "epipolar sphere map RGB (phi across, theta down)", "epipolar sphere map depth"]
    for ri, (row, title) in enumerate(((row_t, f"as it is — {truth_src}"), (row_e, f"as the engine saw it — {E['policy']}, {E['fixations']} fixations at {E['profile']}; RGB: the fixations integrated; depth: the belief"))):
        y = 22 + ri * (ph_ + band); x = 6
        d2.text((6, y - 16), title, fill=(230, 230, 230))
        for ci, im in enumerate(row):
            sheet.paste(im, (x, y))
            if ri == 1:
                d2.text((x, y + ph_ + 4), labels[ci], fill=(180, 180, 180))
            x += im.width + 6
    sheet.save(os.path.join(out, "sheet.png"))
    # numbers worth printing beside the picture
    both = np.isfinite(e_sp_dep) & np.isfinite(t_sp_dep) & (t_sp_dep > 0)
    if both.any():
        err = np.abs(1.0 / e_sp_dep[both] - 1.0 / t_sp_dep[both])
        print(f"[views] engine vs truth on {both.sum()} shared cells: median |rho err| {np.median(err):.4f} /m, median |depth err| {np.median(np.abs(e_sp_dep[both] - t_sp_dep[both])):.3f} m")
    seen = np.isfinite(e_sp_rgb).all(-1).mean(); measured = np.isfinite(e_sp_dep).mean()
    print(f"[views] sphere at {cell:g} deg: {100 * seen:.1f}% of it seen by the L eye, {100 * measured:.1f}% with a depth from the belief; white {white:.3f}, depth scale {z_lo:.2f}-{z_hi:.2f} m")
    print(f"[views] -> {out}/sheet.png (+ 8 panels, 4 depth .npy, the scanpath)")


if __name__ == "__main__":
    main()
