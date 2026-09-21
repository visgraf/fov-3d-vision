"""Cyclopean angular support and topology for the fixed-head surfel scene.

Pure NumPy/Pillow module: no evaluator truth, no Blender and no meshing.  The
metric surfel map remains authoritative; this module only organizes it on a
local chart of the head/cyclopean sphere.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import math
import numpy as np
from PIL import Image

import cyclopean1a_public as public


@dataclass(frozen=True)
class Chart:
    yaw0_deg: float
    pitch0_deg: float
    grid_deg: float
    width: int
    height: int

    @property
    def yaw1_deg(self) -> float:
        return self.yaw0_deg + self.grid_deg * (self.width - 1)

    @property
    def pitch1_deg(self) -> float:
        return self.pitch0_deg + self.grid_deg * (self.height - 1)


@dataclass
class Evidence:
    seen_target: np.ndarray
    seen_nontarget: np.ndarray
    target_range_m: np.ndarray
    nontarget_range_m: np.ndarray


@dataclass
class Topology:
    chart: Chart
    raw_support: np.ndarray
    support: np.ndarray
    target_range_m: np.ndarray
    holes: list[dict]
    footprint_cells: int
    footprint_radius_deg: float


def xyz_to_angles(xyz: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    p = np.asarray(xyz, float).reshape(-1, 3)
    rho = np.linalg.norm(p, axis=1)
    good = np.isfinite(p).all(1) & np.isfinite(rho) & (rho > 0)
    yaw = np.full(len(p), np.nan, float)
    pitch = np.full(len(p), np.nan, float)
    yaw[good] = np.degrees(np.arctan2(p[good, 0], -p[good, 2]))
    pitch[good] = np.degrees(np.arctan2(p[good, 1], np.hypot(p[good, 0], p[good, 2])))
    return yaw, pitch, rho


def angles_to_dir(yaw_deg: np.ndarray | float, pitch_deg: np.ndarray | float) -> np.ndarray:
    y = np.radians(yaw_deg)
    p = np.radians(pitch_deg)
    cp = np.cos(p)
    return np.stack((np.sin(y) * cp, np.sin(p), -np.cos(y) * cp), axis=-1)


def _disk_offsets(radius: int) -> list[tuple[int, int]]:
    r = int(radius)
    return [(dy, dx) for dy in range(-r, r + 1) for dx in range(-r, r + 1)
            if dx * dx + dy * dy <= r * r]


def dilate(mask: np.ndarray, radius: int) -> np.ndarray:
    m = np.asarray(mask, bool)
    if radius <= 0:
        return m.copy()
    h, w = m.shape
    out = np.zeros_like(m)
    for dy, dx in _disk_offsets(radius):
        sy0 = max(0, -dy); sy1 = min(h, h - dy)
        sx0 = max(0, -dx); sx1 = min(w, w - dx)
        dy0 = sy0 + dy; dy1 = sy1 + dy
        dx0 = sx0 + dx; dx1 = sx1 + dx
        out[dy0:dy1, dx0:dx1] |= m[sy0:sy1, sx0:sx1]
    return out


def _components(mask: np.ndarray) -> list[np.ndarray]:
    m = np.asarray(mask, bool)
    h, w = m.shape
    seen = np.zeros_like(m)
    out: list[np.ndarray] = []
    # 8-connectivity: diagonal samples belong to one angular region.
    nbr = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    for y0, x0 in zip(*np.nonzero(m & ~seen)):
        if seen[y0, x0]:
            continue
        stack = [(int(y0), int(x0))]
        seen[y0, x0] = True
        cells = []
        while stack:
            y, x = stack.pop(); cells.append((y, x))
            for dy, dx in nbr:
                yy, xx = y + dy, x + dx
                if 0 <= yy < h and 0 <= xx < w and m[yy, xx] and not seen[yy, xx]:
                    seen[yy, xx] = True; stack.append((yy, xx))
        a = np.asarray(cells, np.int32)
        out.append(a)
    return out


def _indices(chart: Chart, yaw: np.ndarray, pitch: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = np.rint((yaw - chart.yaw0_deg) / chart.grid_deg).astype(np.int64)
    y = np.rint((pitch - chart.pitch0_deg) / chart.grid_deg).astype(np.int64)
    good = np.isfinite(yaw) & np.isfinite(pitch) & (x >= 0) & (x < chart.width) & (y >= 0) & (y < chart.height)
    return y, x, good


def build_chart(xyz: np.ndarray, profile: str) -> tuple[Chart, int, float]:
    if profile not in public.GRID_DEG_BY_PROFILE:
        raise ValueError(f"unknown profile {profile}")
    grid = float(public.GRID_DEG_BY_PROFILE[profile])
    yaw, pitch, rho = xyz_to_angles(xyz)
    good = np.isfinite(yaw) & np.isfinite(pitch) & np.isfinite(rho) & (rho > 0)
    if not np.any(good):
        raise ValueError("no finite surfels")
    med_rho = float(np.median(rho[good]))
    footprint_deg = public.footprint_radius_deg(med_rho)
    footprint_cells = max(1, int(math.ceil(footprint_deg / grid)))
    # Pad by more than the support footprint so exterior complement is guaranteed
    # to touch the raster border.  This is bookkeeping, not a scene threshold.
    pad = footprint_cells + 1
    ymin = math.floor(float(np.min(pitch[good])) / grid) - pad
    ymax = math.ceil(float(np.max(pitch[good])) / grid) + pad
    xmin = math.floor(float(np.min(yaw[good])) / grid) - pad
    xmax = math.ceil(float(np.max(yaw[good])) / grid) + pad
    chart = Chart(xmin * grid, ymin * grid, grid, xmax - xmin + 1, ymax - ymin + 1)
    return chart, footprint_cells, footprint_deg


def rasterize_target(xyz: np.ndarray, chart: Chart, footprint_cells: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    yaw, pitch, rho = xyz_to_angles(xyz)
    yy, xx, good = _indices(chart, yaw, pitch)
    raw = np.zeros((chart.height, chart.width), bool)
    rr = np.full((chart.height, chart.width), np.inf, float)
    gy = yy[good]; gx = xx[good]; gr = rho[good]
    raw[gy, gx] = True
    flat = gy * chart.width + gx
    np.minimum.at(rr.ravel(), flat, gr)
    support = dilate(raw, footprint_cells)
    rr[~np.isfinite(rr)] = np.nan
    return raw, support, rr


def empty_evidence(chart: Chart) -> Evidence:
    shape = (chart.height, chart.width)
    return Evidence(np.zeros(shape, bool), np.zeros(shape, bool),
                    np.full(shape, np.nan, float), np.full(shape, np.nan, float))


def add_observation(e: Evidence, chart: Chart, xyz: np.ndarray, instance_id: np.ndarray, valid: np.ndarray, object_id: int) -> None:
    p = np.asarray(xyz, float).reshape(-1, 3)
    ids = np.asarray(instance_id).reshape(-1)
    v = np.asarray(valid, bool).reshape(-1)
    if len(p) != len(ids) or len(p) != len(v):
        raise ValueError("observation arrays have inconsistent sizes")
    yaw, pitch, rho = xyz_to_angles(p)
    yy, xx, inside = _indices(chart, yaw, pitch)
    use = v & inside & np.isfinite(rho) & (rho > 0)
    if not np.any(use):
        return
    gy = yy[use]; gx = xx[use]; gr = rho[use]; gi = ids[use]
    t = gi == int(object_id); n = ~t
    if np.any(t):
        e.seen_target[gy[t], gx[t]] = True
        flat = gy[t] * chart.width + gx[t]
        cur = np.where(np.isfinite(e.target_range_m), e.target_range_m, np.inf)
        np.minimum.at(cur.ravel(), flat, gr[t]); cur[~np.isfinite(cur)] = np.nan
        e.target_range_m[:] = cur
    if np.any(n):
        e.seen_nontarget[gy[n], gx[n]] = True
        flat = gy[n] * chart.width + gx[n]
        cur = np.where(np.isfinite(e.nontarget_range_m), e.nontarget_range_m, np.inf)
        np.minimum.at(cur.ravel(), flat, gr[n]); cur[~np.isfinite(cur)] = np.nan
        e.nontarget_range_m[:] = cur


def _hole_centroid(chart: Chart, cells: np.ndarray) -> tuple[float, float]:
    y = chart.pitch0_deg + cells[:, 0] * chart.grid_deg
    x = chart.yaw0_deg + cells[:, 1] * chart.grid_deg
    d = angles_to_dir(x, y)
    m = d.mean(axis=0); m /= max(1e-12, float(np.linalg.norm(m)))
    yaw = math.degrees(math.atan2(float(m[0]), -float(m[2])))
    pitch = math.degrees(math.atan2(float(m[1]), math.hypot(float(m[0]), float(m[2]))))
    return yaw, pitch


def analyze(xyz_target: np.ndarray, profile: str, evidence: Evidence | None = None, *, chart: Chart | None = None, footprint_cells: int | None = None, footprint_deg: float | None = None) -> Topology:
    if chart is None:
        chart, auto_cells, auto_deg = build_chart(xyz_target, profile)
        footprint_cells = auto_cells
        footprint_deg = auto_deg
    else:
        if footprint_cells is None or footprint_deg is None:
            raise ValueError("fixed-chart analysis requires footprint_cells and footprint_deg")
    raw, support, target_range = rasterize_target(xyz_target, chart, int(footprint_cells))
    if evidence is not None and evidence.seen_target.shape != support.shape:
        raise ValueError("evidence chart shape mismatch")
    comp = _components(~support)
    holes: list[dict] = []
    h, w = support.shape
    for cells in comp:
        touches = bool(np.any((cells[:,0] == 0) | (cells[:,0] == h-1) | (cells[:,1] == 0) | (cells[:,1] == w-1)))
        if touches:
            continue
        mask = np.zeros_like(support); mask[cells[:,0], cells[:,1]] = True
        # Nearby raw target surfels supply a local range reference.
        ring = dilate(mask, int(footprint_cells) + 1) & raw
        ring_range = target_range[ring]
        ring_range = ring_range[np.isfinite(ring_range)]
        yawc, pitc = _hole_centroid(chart, cells)
        area = float(np.sum(np.cos(np.radians(chart.pitch0_deg + cells[:,0] * chart.grid_deg))) * chart.grid_deg * chart.grid_deg)
        target_cells = non_cells = 0
        nt_range = np.empty(0, float)
        if evidence is not None:
            target_cells = int(evidence.seen_target[mask].sum())
            non_cells = int(evidence.seen_nontarget[mask].sum())
            nt_range = evidence.nontarget_range_m[mask]
            nt_range = nt_range[np.isfinite(nt_range)]
        boundary_med = float(np.median(ring_range)) if len(ring_range) else None
        non_med = float(np.median(nt_range)) if len(nt_range) else None
        gap = abs(non_med - boundary_med) if boundary_med is not None and non_med is not None else None
        physical = bool(non_cells > target_cells and gap is not None and gap > public.FUSION["association_radius_m"])
        if physical:
            state = "PHYSICAL_DEPTH_BREAK"
        elif target_cells > non_cells:
            state = "TARGET_EVIDENCE_HOLE"
        elif target_cells == 0 and non_cells == 0:
            state = "UNOBSERVED_HOLE"
        else:
            state = "AMBIGUOUS_HOLE"
        holes.append({
            "cell_count": int(len(cells)),
            "angular_area_deg2": area,
            "centroid_yaw_deg": yawc,
            "centroid_pitch_deg": pitc,
            "state": state,
            "probe_candidate": bool(not physical),
            "target_observed_cells": target_cells,
            "nontarget_observed_cells": non_cells,
            "boundary_target_range_median_m": boundary_med,
            "interior_nontarget_range_median_m": non_med,
            "range_gap_m": gap,
            "cells": cells,
        })
    holes.sort(key=lambda q: (-q["angular_area_deg2"], q["centroid_yaw_deg"], q["centroid_pitch_deg"]))
    return Topology(chart, raw, support, target_range, holes, int(footprint_cells), float(footprint_deg))


def select_probe(topology: Topology, visited_gazes: list[tuple[float, float]]) -> dict | None:
    candidates = [h for h in topology.holes if h["probe_candidate"]]
    if not candidates:
        return None
    h = candidates[0]
    yaw = round(float(h["centroid_yaw_deg"]) * 10.0) / 10.0
    pit = round(float(h["centroid_pitch_deg"]) * 10.0) / 10.0
    if not (-25.0 <= yaw <= 25.0 and -20.0 <= pit <= 20.0):
        return None
    if any(abs(yaw-a) < 1e-9 and abs(pit-b) < 1e-9 for a,b in visited_gazes):
        # Use the hole cell farthest in angular L1 distance from all visited gazes.
        cells = h["cells"]
        cy = topology.chart.pitch0_deg + cells[:,0] * topology.chart.grid_deg
        cx = topology.chart.yaw0_deg + cells[:,1] * topology.chart.grid_deg
        if visited_gazes:
            dist = np.min(np.stack([np.abs(cx-a)+np.abs(cy-b) for a,b in visited_gazes], axis=1), axis=1)
            k = int(np.argmax(dist)); yaw = round(float(cx[k])*10)/10; pit = round(float(cy[k])*10)/10
        if any(abs(yaw-a) < 1e-9 and abs(pit-b) < 1e-9 for a,b in visited_gazes):
            return None
    return {
        "gaze_deg": [yaw, pit],
        "hole_state": h["state"],
        "hole_area_deg2": float(h["angular_area_deg2"]),
        "hole_cell_count": int(h["cell_count"]),
        "centroid_unsnapped_deg": [float(h["centroid_yaw_deg"]), float(h["centroid_pitch_deg"])],
    }


def write_visual(path: Path, topology: Topology, evidence: Evidence | None = None, selected: dict | None = None) -> None:
    h, w = topology.support.shape
    im = np.full((h, w, 3), 245, np.uint8)
    im[topology.support] = (150,150,150)
    if evidence is not None:
        im[evidence.seen_nontarget & ~topology.support] = (210,225,245)
    for hole in topology.holes:
        cells = hole["cells"]
        if hole["state"] == "PHYSICAL_DEPTH_BREAK": col = (80,130,220)
        elif hole["state"] == "UNOBSERVED_HOLE": col = (235,110,70)
        elif hole["state"] == "TARGET_EVIDENCE_HOLE": col = (240,170,60)
        else: col = (190,120,190)
        im[cells[:,0], cells[:,1]] = col
    if selected is not None:
        yaw, pit = selected["gaze_deg"]
        x = int(round((yaw-topology.chart.yaw0_deg)/topology.chart.grid_deg))
        y = int(round((pit-topology.chart.pitch0_deg)/topology.chart.grid_deg))
        for d in range(-3,4):
            if 0 <= y < h and 0 <= x+d < w: im[y,x+d]=(0,0,0)
            if 0 <= y+d < h and 0 <= x < w: im[y+d,x]=(0,0,0)
    # Pitch increases upward; image row zero should be top.
    Image.fromarray(np.flipud(im)).resize((max(1,w*3), max(1,h*3)), Image.Resampling.NEAREST).save(path)


def _synthetic_case(physical: bool) -> tuple[np.ndarray, Evidence, str]:
    # A fronto-parallel angular annulus at 2 m.  For the physical-hole case the
    # center was observed as non-target at 2.8 m; for sampling it was never seen.
    grid = 0.2
    ys, xs = np.mgrid[-5:5.0001:grid, -7:7.0001:grid]
    ring = (np.abs(xs) <= 7) & (np.abs(ys) <= 5) & ~((np.abs(xs)<2.2)&(np.abs(ys)<1.8))
    yaw = xs[ring].ravel(); pit = ys[ring].ravel(); rho=np.full_like(yaw,2.0,float)
    d=angles_to_dir(yaw,pit); xyz=d*rho[:,None]
    chart, fc, _ = build_chart(xyz, "small")
    ev=empty_evidence(chart)
    if physical:
        hy,hx=np.mgrid[-1.4:1.4001:grid,-1.8:1.8001:grid]
        dd=angles_to_dir(hx.ravel(),hy.ravel()); q=dd*2.8
        ids=np.full(len(q),999,np.int32); valid=np.ones(len(q),bool)
        add_observation(ev,chart,q,ids,valid,public.OBJECT_ID)
        expected="PHYSICAL_DEPTH_BREAK"
    else:
        expected="UNOBSERVED_HOLE"
    return xyz, ev, expected


def self_test() -> None:
    for physical in (False, True):
        xyz, ev, expected = _synthetic_case(physical)
        topo=analyze(xyz,"small",ev)
        if not topo.holes:
            raise AssertionError("synthetic annulus hole not detected")
        if topo.holes[0]["state"] != expected:
            raise AssertionError(f"expected {expected}, got {topo.holes[0]['state']}")
        pr=select_probe(topo,[])
        if physical and pr is not None:
            raise AssertionError("physical depth-break hole was proposed for closure")
        if not physical and pr is None:
            raise AssertionError("unobserved sampling hole did not produce a probe")
    # Exterior notch: complement remains connected to padded border and is not a hole.
    ys,xs=np.mgrid[-4:4.0001:.2,-6:6.0001:.2]
    keep=(np.abs(xs)<=6)&(np.abs(ys)<=4)&~((xs>3)&(np.abs(ys)<1.5))
    d=angles_to_dir(xs[keep].ravel(),ys[keep].ravel()); xyz=d*2.0
    topo=analyze(xyz,"small",None)
    if topo.holes:
        raise AssertionError("exterior notch incorrectly became an internal hole")
    print("[cyclopean1a-topology] PASS sampling_hole=true physical_hole_resolved=true exterior_not_hole=true")


if __name__ == "__main__":
    self_test()
