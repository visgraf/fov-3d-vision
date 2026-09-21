"""Pure-array shoreline analysis for Cyclopean-1b.

This module knows nothing about Blender, evaluator truth or scene fixtures.  It
receives a binary cyclopean support plus already-rasterized prediction-side
observation evidence and classifies the complement cells immediately adjacent
to support.  Exterior and internal complement components stay distinct.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import deque
import math
import numpy as np

STATE_CODE = {
    "UNOBSERVED": 1,
    "TARGET_CONTINUATION": 2,
    "PHYSICAL_DEPTH_BREAK": 3,
    "AMBIGUOUS": 4,
}
CODE_STATE = {v: k for k, v in STATE_CODE.items()}


@dataclass
class EvidenceArrays:
    seen_target: np.ndarray
    seen_nontarget: np.ndarray
    target_range_m: np.ndarray
    nontarget_range_m: np.ndarray


@dataclass
class BoundaryAudit:
    shoreline: np.ndarray
    component_labels: np.ndarray
    component_touches_border: dict[int, bool]
    exterior_distance_cells: np.ndarray
    state_code: np.ndarray
    local_target_range_m: np.ndarray
    range_gap_m: np.ndarray
    arcs: list[dict]
    components: list[dict]


def _components(mask: np.ndarray) -> tuple[np.ndarray, list[np.ndarray]]:
    m = np.asarray(mask, bool)
    h, w = m.shape
    labels = np.full((h, w), -1, np.int32)
    out: list[np.ndarray] = []
    nbr = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    label = 0
    for y0, x0 in zip(*np.nonzero(m)):
        if labels[y0, x0] >= 0:
            continue
        q = [(int(y0), int(x0))]
        labels[y0, x0] = label
        cells: list[tuple[int,int]] = []
        while q:
            y, x = q.pop()
            cells.append((y, x))
            for dy, dx in nbr:
                yy, xx = y + dy, x + dx
                if 0 <= yy < h and 0 <= xx < w and m[yy, xx] and labels[yy, xx] < 0:
                    labels[yy, xx] = label
                    q.append((yy, xx))
        out.append(np.asarray(cells, np.int32))
        label += 1
    return labels, out


def _touches_border(cells: np.ndarray, shape: tuple[int,int]) -> bool:
    h, w = shape
    return bool(np.any(
        (cells[:,0] == 0) | (cells[:,0] == h-1) |
        (cells[:,1] == 0) | (cells[:,1] == w-1)
    ))


def _shoreline(support: np.ndarray) -> np.ndarray:
    s = np.asarray(support, bool)
    h, w = s.shape
    neigh = np.zeros_like(s)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0:
                continue
            sy0 = max(0, -dy); sy1 = min(h, h - dy)
            sx0 = max(0, -dx); sx1 = min(w, w - dx)
            neigh[sy0+dy:sy1+dy, sx0+dx:sx1+dx] |= s[sy0:sy1, sx0:sx1]
    return (~s) & neigh


def _exterior_distance(complement: np.ndarray) -> np.ndarray:
    """8-connected shortest complement-path distance from the raster border."""
    c = np.asarray(complement, bool)
    h, w = c.shape
    dist = np.full((h, w), -1, np.int32)
    q: deque[tuple[int,int]] = deque()
    border = []
    border.extend((0, x) for x in range(w))
    border.extend((h-1, x) for x in range(w))
    border.extend((y, 0) for y in range(1, h-1))
    border.extend((y, w-1) for y in range(1, h-1))
    for y, x in border:
        if c[y, x] and dist[y, x] < 0:
            dist[y, x] = 0
            q.append((y, x))
    nbr = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    while q:
        y, x = q.popleft()
        nd = int(dist[y, x]) + 1
        for dy, dx in nbr:
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w and c[yy, xx] and dist[yy, xx] < 0:
                dist[yy, xx] = nd
                q.append((yy, xx))
    return dist


def _local_target_median(
    raw_support: np.ndarray,
    target_range_m: np.ndarray,
    y: int,
    x: int,
    radius: int,
) -> float:
    h, w = raw_support.shape
    y0 = max(0, y-radius); y1 = min(h, y+radius+1)
    x0 = max(0, x-radius); x1 = min(w, x+radius+1)
    yy, xx = np.ogrid[y0:y1, x0:x1]
    disk = (yy-y)**2 + (xx-x)**2 <= radius*radius
    use = disk & raw_support[y0:y1, x0:x1]
    vals = target_range_m[y0:y1, x0:x1][use]
    vals = vals[np.isfinite(vals)]
    return float(np.median(vals)) if len(vals) else math.nan


def _centroid_deg(cells: np.ndarray, yaw0_deg: float, pitch0_deg: float, grid_deg: float) -> tuple[float,float]:
    # Cell-centre average is enough for this descriptive boundary audit; the
    # chart is only a few tens of degrees wide.
    yaw = yaw0_deg + cells[:,1] * grid_deg
    pitch = pitch0_deg + cells[:,0] * grid_deg
    return float(np.mean(yaw)), float(np.mean(pitch))


def analyze_boundary(
    *,
    raw_support: np.ndarray,
    support: np.ndarray,
    target_range_m: np.ndarray,
    evidence: EvidenceArrays,
    grid_deg: float,
    yaw0_deg: float,
    pitch0_deg: float,
    footprint_cells: int,
    association_radius_m: float,
) -> BoundaryAudit:
    raw = np.asarray(raw_support, bool)
    sup = np.asarray(support, bool)
    rr = np.asarray(target_range_m, float)
    shape = sup.shape
    for a in (raw, rr, evidence.seen_target, evidence.seen_nontarget,
              evidence.target_range_m, evidence.nontarget_range_m):
        if a.shape != shape:
            raise ValueError("boundary audit array shape mismatch")
    if not (grid_deg > 0 and footprint_cells >= 1 and association_radius_m > 0):
        raise ValueError("invalid inherited geometry scale")

    complement = ~sup
    labels, comps = _components(complement)
    touches = {i: _touches_border(cells, shape) for i, cells in enumerate(comps)}
    ext_dist = _exterior_distance(complement)
    shore = _shoreline(sup)
    state = np.zeros(shape, np.uint8)
    local = np.full(shape, np.nan, float)
    gap = np.full(shape, np.nan, float)

    # Reuse the same local target-reference radius as Cyclopean-1a's hole cue.
    local_radius = int(footprint_cells) + 1
    for y, x in zip(*np.nonzero(shore)):
        bmed = _local_target_median(raw, rr, int(y), int(x), local_radius)
        local[y, x] = bmed
        t = bool(evidence.seen_target[y, x])
        n = bool(evidence.seen_nontarget[y, x])
        nr = float(evidence.nontarget_range_m[y, x]) if n else math.nan
        g = abs(nr - bmed) if math.isfinite(nr) and math.isfinite(bmed) else math.nan
        gap[y, x] = g
        if t and not n:
            st = "TARGET_CONTINUATION"
        elif n and not t and math.isfinite(g) and g > association_radius_m:
            st = "PHYSICAL_DEPTH_BREAK"
        elif not t and not n:
            st = "UNOBSERVED"
        else:
            st = "AMBIGUOUS"
        state[y, x] = STATE_CODE[st]

    component_rows: list[dict] = []
    for i, cells in enumerate(comps):
        sh = shore[cells[:,0], cells[:,1]]
        shore_cells = cells[sh]
        component_rows.append({
            "component_id": int(i),
            "kind": "EXTERIOR" if touches[i] else "INTERNAL",
            "cell_count": int(len(cells)),
            "shoreline_cell_count": int(len(shore_cells)),
            "max_border_distance_cells": (
                int(np.max(ext_dist[cells[:,0], cells[:,1]])) if touches[i] else None
            ),
        })

    arcs: list[dict] = []
    arc_id = 0
    for comp_id, cells in enumerate(comps):
        comp_mask = np.zeros(shape, bool)
        comp_mask[cells[:,0], cells[:,1]] = True
        kind = "EXTERIOR" if touches[comp_id] else "INTERNAL"
        for code, name in CODE_STATE.items():
            mask = shore & comp_mask & (state == code)
            _, pieces = _components(mask)
            for piece in pieces:
                cyaw, cpitch = _centroid_deg(piece, yaw0_deg, pitch0_deg, grid_deg)
                finite_gap = gap[piece[:,0], piece[:,1]]
                finite_gap = finite_gap[np.isfinite(finite_gap)]
                d = ext_dist[piece[:,0], piece[:,1]]
                arcs.append({
                    "arc_id": int(arc_id),
                    "component_id": int(comp_id),
                    "component_kind": kind,
                    "state": name,
                    "cell_count": int(len(piece)),
                    "centroid_yaw_deg": cyaw,
                    "centroid_pitch_deg": cpitch,
                    "yaw_span_deg": float((piece[:,1].max()-piece[:,1].min()+1) * grid_deg),
                    "pitch_span_deg": float((piece[:,0].max()-piece[:,0].min()+1) * grid_deg),
                    "seen_target_cells": int(evidence.seen_target[piece[:,0], piece[:,1]].sum()),
                    "seen_nontarget_cells": int(evidence.seen_nontarget[piece[:,0], piece[:,1]].sum()),
                    "range_gap_median_m": float(np.median(finite_gap)) if len(finite_gap) else None,
                    "border_distance_cells_min": int(np.min(d)) if kind == "EXTERIOR" else None,
                    "border_distance_cells_median": float(np.median(d)) if kind == "EXTERIOR" else None,
                    "border_distance_cells_max": int(np.max(d)) if kind == "EXTERIOR" else None,
                })
                arc_id += 1

    arcs.sort(key=lambda a: (
        0 if a["component_kind"] == "EXTERIOR" else 1,
        -int(a["border_distance_cells_max"] or -1),
        -a["cell_count"],
        a["state"],
        a["centroid_yaw_deg"],
        a["centroid_pitch_deg"],
    ))
    return BoundaryAudit(shore, labels, touches, ext_dist, state, local, gap, arcs, component_rows)


def _synthetic_arrays() -> tuple[np.ndarray,np.ndarray,np.ndarray,EvidenceArrays]:
    h, w = 30, 42
    support = np.zeros((h,w), bool)
    support[5:25, 5:37] = True
    # A bay opening through the left side of the sampled rectangle.
    support[11:19, 5:24] = False
    raw = support.copy()
    rr = np.full((h,w), np.nan, float)
    rr[raw] = 2.0
    ev = EvidenceArrays(
        np.zeros((h,w), bool), np.zeros((h,w), bool),
        np.full((h,w), np.nan, float), np.full((h,w), np.nan, float),
    )
    return raw, support, rr, ev


def self_test() -> None:
    raw, support, rr, ev = _synthetic_arrays()
    a = analyze_boundary(raw_support=raw, support=support, target_range_m=rr,
                         evidence=ev, grid_deg=0.1, yaw0_deg=-2.0, pitch0_deg=-1.5,
                         footprint_cells=1, association_radius_m=0.012)
    ext_unobs = [q for q in a.arcs if q["component_kind"]=="EXTERIOR" and q["state"]=="UNOBSERVED"]
    if not ext_unobs:
        raise AssertionError("synthetic exterior bay did not produce an unobserved shoreline arc")
    if max(q["border_distance_cells_max"] for q in ext_unobs) <= 1:
        raise AssertionError("synthetic bay did not retain exterior penetration depth")

    # Add target-only evidence to one shoreline cell: continuation, not physical.
    ys, xs = np.nonzero(a.shoreline)
    k = int(np.argmax(a.exterior_distance_cells[ys, xs]))
    y, x = int(ys[k]), int(xs[k])
    ev.seen_target[y,x] = True; ev.target_range_m[y,x] = 2.0
    b = analyze_boundary(raw_support=raw, support=support, target_range_m=rr,
                         evidence=ev, grid_deg=0.1, yaw0_deg=-2.0, pitch0_deg=-1.5,
                         footprint_cells=1, association_radius_m=0.012)
    if b.state_code[y,x] != STATE_CODE["TARGET_CONTINUATION"]:
        raise AssertionError("target shoreline evidence was not classified as continuation")

    # Replace it by deeper non-target-only evidence: physical depth break.
    ev.seen_target[y,x] = False; ev.target_range_m[y,x] = np.nan
    ev.seen_nontarget[y,x] = True; ev.nontarget_range_m[y,x] = 2.8
    c = analyze_boundary(raw_support=raw, support=support, target_range_m=rr,
                         evidence=ev, grid_deg=0.1, yaw0_deg=-2.0, pitch0_deg=-1.5,
                         footprint_cells=1, association_radius_m=0.012)
    if c.state_code[y,x] != STATE_CODE["PHYSICAL_DEPTH_BREAK"]:
        raise AssertionError("depth-break shoreline evidence was not classified physical")

    # An enclosed island of complement must remain INTERNAL, not be relabelled exterior.
    support2 = np.ones((20,20), bool)
    support2[:2,:] = False; support2[-2:,:] = False; support2[:,:2] = False; support2[:,-2:] = False
    support2[8:12,8:12] = False
    raw2 = support2.copy(); rr2=np.full((20,20),np.nan,float); rr2[raw2]=2.0
    ev2=EvidenceArrays(np.zeros((20,20),bool),np.zeros((20,20),bool),np.full((20,20),np.nan),np.full((20,20),np.nan))
    d=analyze_boundary(raw_support=raw2,support=support2,target_range_m=rr2,evidence=ev2,
                       grid_deg=.1,yaw0_deg=-1,pitch0_deg=-1,footprint_cells=1,association_radius_m=.012)
    if not any(q["kind"]=="INTERNAL" for q in d.components):
        raise AssertionError("synthetic internal component lost")
    print("[cyclopean1b-boundary] PASS exterior_bay=true internal_distinct=true continuation=true physical_depth_break=true")


if __name__ == "__main__":
    self_test()
