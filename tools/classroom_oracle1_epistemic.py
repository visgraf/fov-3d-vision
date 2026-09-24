"""Cyclopean epistemic handoff used by Classroom-Oracle-1.

The metric surfel map remains authoritative.  This module adds only a fixed-head
angular bookkeeping chart.  It records what the completed tangent observations
actually sampled and, after frozen FSG6f says ``no_frontier``, may return one
additional fixation at a map shoreline cell that is BOTH:

* in the EXTERIOR complement component, and
* NEVER_OBSERVED by the completed binocular history.

Among eligible cells it chooses the deepest inherited border-distance.  This is
an epistemic query, not truth completion: no Blender geometry is consulted here.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import math

import cv2
import numpy as np

import classroom_oracle1_public as public
from fsg_stereo import rectification


@dataclass
class Evidence:
    yaw_min_deg: float
    yaw_max_deg: float
    pitch_min_deg: float
    pitch_max_deg: float
    grid_deg: float
    seen_any: np.ndarray
    seen_target: np.ndarray
    seen_nontarget: np.ndarray
    target_depth_valid: np.ndarray

    @property
    def shape(self) -> tuple[int, int]:
        return self.seen_any.shape


def make_evidence() -> Evidence:
    import fsg6f_public as frozen
    cfg = frozen.SURFACE_FRONTIER
    g = float(public.CYCLOPEAN_GRID_DEG)
    y0, y1 = float(cfg["yaw_min_deg"]), float(cfg["yaw_max_deg"])
    p0, p1 = float(cfg["pitch_min_deg"]), float(cfg["pitch_max_deg"])
    w = int(round((y1 - y0) / g)) + 1
    h = int(round((p1 - p0) / g)) + 1
    z = np.zeros((h, w), bool)
    return Evidence(y0, y1, p0, p1, g, z.copy(), z.copy(), z.copy(), z.copy())


def angular_coordinates(xyz_h: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    p = np.asarray(xyz_h, float).reshape(-1, 3)
    yaw = np.degrees(np.arctan2(p[:, 0], -p[:, 2]))
    pitch = np.degrees(np.arctan2(p[:, 1], np.hypot(p[:, 0], p[:, 2])))
    return yaw, pitch


def _cells(ev: Evidence, yaw: np.ndarray, pitch: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = np.rint((np.asarray(yaw) - ev.yaw_min_deg) / ev.grid_deg).astype(np.int64)
    y = np.rint((np.asarray(pitch) - ev.pitch_min_deg) / ev.grid_deg).astype(np.int64)
    h, w = ev.shape
    ok = np.isfinite(yaw) & np.isfinite(pitch) & (x >= 0) & (x < w) & (y >= 0) & (y < h)
    return y, x, ok


def _rectified_core_directions_h(calibration: dict, side: str) -> np.ndarray:
    """Direction of each rectified core pixel in fixed head frame H."""
    r = rectification(calibration)
    x0, y0, w, h = map(int, r["crop_xywh"])
    vv, uu = np.mgrid[:h, :w]
    uv = np.stack((uu + x0, vv + y0), axis=-1).astype(float)
    k = np.asarray(r["P1" if side == "L" else "P2"], float)[:, :3]
    rr = np.asarray(r["R1" if side == "L" else "R2"], float)
    a = np.concatenate((uv, np.ones((h, w, 1))), axis=-1)
    d_rect = a @ np.linalg.inv(k).T
    d_c = d_rect @ rr
    eye = calibration["eyes"][0 if side == "L" else 1]
    d_h = d_c @ np.asarray(eye["R_hc"], float).T
    n = np.linalg.norm(d_h, axis=-1, keepdims=True)
    return d_h / np.maximum(n, 1e-15)


def _mark(ev: Evidence, mask: np.ndarray, directions_h: np.ndarray, dst: np.ndarray) -> None:
    m = np.asarray(mask, bool)
    if m.shape != directions_h.shape[:2]:
        raise ValueError("evidence mask/direction shape mismatch")
    d = directions_h[m]
    if len(d) == 0:
        return
    yaw = np.degrees(np.arctan2(d[:, 0], -d[:, 2]))
    pitch = np.degrees(np.arctan2(d[:, 1], np.hypot(d[:, 0], d[:, 2])))
    y, x, ok = _cells(ev, yaw, pitch)
    dst[y[ok], x[ok]] = True


def add_observation(ev: Evidence, calibration: dict,
                    instance_L: np.ndarray, raw_support_L: np.ndarray,
                    instance_R: np.ndarray, raw_support_R: np.ndarray,
                    valid_L: np.ndarray, target_object_id: int) -> None:
    """Accumulate only completed binocular observation evidence."""
    for side, ids, support in (
        ("L", instance_L, raw_support_L), ("R", instance_R, raw_support_R)
    ):
        ids = np.asarray(ids)
        support = np.asarray(support, bool)
        if ids.shape != support.shape or ids.ndim != 2:
            raise ValueError("instance/support arrays must share a 2D shape")
        d = _rectified_core_directions_h(calibration, side)
        _mark(ev, support, d, ev.seen_any)
        _mark(ev, support & (ids == int(target_object_id)), d, ev.seen_target)
        _mark(ev, support & (ids != int(target_object_id)), d, ev.seen_nontarget)
        if side == "L":
            _mark(ev, support & (ids == int(target_object_id)) & np.asarray(valid_L, bool), d,
                  ev.target_depth_valid)


def _map_support(ev: Evidence, xyz_h: np.ndarray) -> tuple[np.ndarray, int, float]:
    p = np.asarray(xyz_h, float).reshape(-1, 3)
    if len(p) == 0:
        return np.zeros(ev.shape, bool), 0, float("nan")
    yaw, pitch = angular_coordinates(p)
    y, x, ok = _cells(ev, yaw, pitch)
    raw = np.zeros(ev.shape, np.uint8)
    raw[y[ok], x[ok]] = 1
    ranges = np.linalg.norm(p[np.isfinite(p).all(axis=1)], axis=1)
    med = float(np.median(ranges)) if len(ranges) else float("nan")
    if not np.isfinite(med) or med <= 0:
        radius_cells = 1
    else:
        radius_deg = math.degrees(math.atan(public.FUSION["association_radius_m"] / med))
        radius_cells = max(1, int(math.ceil(radius_deg / ev.grid_deg)))
    yy, xx = np.mgrid[-radius_cells:radius_cells + 1, -radius_cells:radius_cells + 1]
    kernel = ((xx * xx + yy * yy) <= radius_cells * radius_cells).astype(np.uint8)
    support = cv2.dilate(raw, kernel).astype(bool)
    return support, radius_cells, med


def _exterior_and_distance(complement: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Exterior complement and its shortest 8-neighbour distance from chart border."""
    m = np.asarray(complement, bool)
    h, w = m.shape
    ext = np.zeros_like(m)
    dist = np.full((h, w), -1, np.int32)
    q: deque[tuple[int, int]] = deque()
    for x in range(w):
        for y in (0, h - 1):
            if m[y, x] and not ext[y, x]:
                ext[y, x] = True; dist[y, x] = 0; q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if m[y, x] and not ext[y, x]:
                ext[y, x] = True; dist[y, x] = 0; q.append((y, x))
    nbr = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    while q:
        y, x = q.popleft()
        nd = int(dist[y, x] + 1)
        for dy, dx in nbr:
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w and m[yy, xx] and not ext[yy, xx]:
                ext[yy, xx] = True; dist[yy, xx] = nd; q.append((yy, xx))
    return ext, dist


def audit(ev: Evidence, map_xyz_h: np.ndarray, visited_gazes_deg: list[tuple[float, float]]) -> dict:
    support, footprint_cells, median_range = _map_support(ev, map_xyz_h)
    complement = ~support
    exterior, border_distance = _exterior_and_distance(complement)
    shoreline = complement & cv2.dilate(support.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    never = ~ev.seen_any

    eligible = shoreline & exterior & never
    # A previously fixated chart cell cannot become a new epistemic action.
    for yaw, pitch in visited_gazes_deg:
        yy, xx, ok = _cells(ev, np.array([yaw]), np.array([pitch]))
        if bool(ok[0]):
            eligible[int(yy[0]), int(xx[0])] = False

    target_no_depth = ev.seen_target & ~ev.target_depth_valid
    target_with_depth = ev.target_depth_valid
    nontarget_only = ev.seen_nontarget & ~ev.seen_target
    mixed = ev.seen_target & ev.seen_nontarget
    counts = {
        "NEVER_OBSERVED": int(never.sum()),
        "OBSERVED_TARGET_NO_DEPTH": int(target_no_depth.sum()),
        "OBSERVED_TARGET_WITH_DEPTH": int(target_with_depth.sum()),
        "OBSERVED_NONTARGET_ONLY": int(nontarget_only.sum()),
        "MIXED_OBSERVATION": int(mixed.sum()),
    }

    cells = np.argwhere(eligible)
    selected = None
    if len(cells):
        d = border_distance[cells[:, 0], cells[:, 1]]
        # Primary rule: deepest inherited border distance.  The remaining ordering
        # is deterministic only, not another scientific preference.
        order = np.lexsort((cells[:, 1], cells[:, 0], -d))
        y, x = map(int, cells[int(order[0])])
        selected = {
            "cell_yx": [y, x],
            "yaw_deg": float(ev.yaw_min_deg + x * ev.grid_deg),
            "pitch_deg": float(ev.pitch_min_deg + y * ev.grid_deg),
            "exterior_border_distance_cells": int(border_distance[y, x]),
        }

    return {
        "grid_deg": ev.grid_deg,
        "chart_shape_hw": list(ev.shape),
        "map_support_cells": int(support.sum()),
        "map_footprint_cells": int(footprint_cells),
        "map_median_range_m": median_range,
        "shoreline_cells": int(shoreline.sum()),
        "exterior_cells": int(exterior.sum()),
        "eligible_never_observed_exterior_shoreline_cells": int(eligible.sum()),
        "epistemic_state_counts": counts,
        "selected": selected,
        "rule": "NEVER_OBSERVED + EXTERIOR shoreline; deepest inherited border distance",
    }


def choose_next(ev: Evidence, map_xyz_h: np.ndarray,
                visited_gazes_deg: list[tuple[float, float]]) -> dict:
    a = audit(ev, map_xyz_h, visited_gazes_deg)
    s = a["selected"]
    return {
        "stop": s is None,
        "reason": "attention_complete" if s is None else "epistemic_fixation",
        "next_gaze_deg": None if s is None else [s["yaw_deg"], s["pitch_deg"]],
        "audit": a,
    }


def self_test() -> list[str]:
    fails: list[str] = []
    ev = make_evidence()
    # Synthetic rectangular map support with a never-observed bay connected to exterior.
    yaw = np.linspace(-4.0, 4.0, 80)
    pitch = np.linspace(-3.0, 3.0, 60)
    Y, P = np.meshgrid(yaw, pitch)
    r = 2.0
    xyz = np.c_[r * np.cos(np.radians(P.ravel())) * np.sin(np.radians(Y.ravel())),
                r * np.sin(np.radians(P.ravel())),
                -r * np.cos(np.radians(P.ravel())) * np.cos(np.radians(Y.ravel()))]
    # Mark everything in a generous angular box observed except a narrow bay next to the map.
    yy0, xx0, _ = _cells(ev, np.array([-8.0]), np.array([-7.0]))
    yy1, xx1, _ = _cells(ev, np.array([8.0]), np.array([7.0]))
    ev.seen_any[int(yy0[0]):int(yy1[0]) + 1, int(xx0[0]):int(xx1[0]) + 1] = True
    # Carve a never-observed tongue from the right toward the object support.
    yc, xc, _ = _cells(ev, np.array([4.2]), np.array([0.0]))
    y = int(yc[0]); x = int(xc[0])
    ev.seen_any[y - 3:y + 4, x:x + 50] = False
    q = choose_next(ev, xyz, [])
    if q["stop"]:
        fails.append("synthetic exterior never-observed bay did not produce an epistemic fixation")
    if q["audit"]["rule"].split(";")[0] != "NEVER_OBSERVED + EXTERIOR shoreline":
        fails.append("epistemic rule changed")
    if ev.grid_deg != 0.10:
        fails.append("cyclopean grid is not 0.1 degree")
    return fails


if __name__ == "__main__":
    bad = self_test()
    for item in bad:
        print("[classroom-oracle1-epistemic] FAIL", item)
    print("[classroom-oracle1-epistemic] self-test", "FAILED" if bad else "PASS")
    raise SystemExit(bool(bad))
