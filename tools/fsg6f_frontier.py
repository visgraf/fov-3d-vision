"""Truth-free 3D surfel-frontier controller for FSG6f.

FSG6f preserves the FSG6e three-state surfel classifier and the settled FSG6d
projected-frontier corridor/ranking.  It adds one candidate-level semantic rule:
aligned OPEN frontier support must strictly outnumber aligned MAP_RESOLVED plus
BOUNDARY_RESOLVED support, while still satisfying the frozen >=8 OPEN support
minimum.  This is strict state consensus, not a fitted numerical threshold.
"""
from __future__ import annotations
from collections import defaultdict
import math
import numpy as np
import fsg6f_public as public


def angular_coordinates(xyz_h: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    p = np.asarray(xyz_h, float).reshape(-1, 3)
    good = np.isfinite(p).all(1) & (p[:, 2] < -1e-6)
    p = p[good]
    if len(p) < 100:
        raise ValueError("too few finite forward map points for FSG6f policy")
    yaw = np.degrees(np.arctan2(p[:, 0], -p[:, 2]))
    pitch = np.degrees(np.arctan2(p[:, 1], np.sqrt(p[:, 0] ** 2 + p[:, 2] ** 2)))
    return yaw, pitch


def edge_evidence(instance_id: np.ndarray, raw_support: np.ndarray, object_id: int) -> dict:
    """Legacy per-eye edge evidence, retained only for diagnostics/regressions."""
    ids = np.asarray(instance_id); sup = np.asarray(raw_support, bool)
    if ids.shape != sup.shape or ids.ndim != 2:
        raise ValueError("instance/support arrays must share a 2D shape")
    h, w = ids.shape; cfg = public.SURFACE_FRONTIER
    bx = max(2, int(round(w * cfg["edge_band_fraction"])))
    by = max(2, int(round(h * cfg["edge_band_fraction"])))
    obj = (ids == object_id) & sup
    def frac(a, b):
        den = max(1, int(b.sum())); return float(a.sum() / den)
    vals = {
        "left_fraction": frac(obj[:, :bx], sup[:, :bx]),
        "right_fraction": frac(obj[:, -bx:], sup[:, -bx:]),
        "top_fraction": frac(obj[:by, :], sup[:by, :]),
        "bottom_fraction": frac(obj[-by:, :], sup[-by:, :]),
    }
    th = cfg["edge_object_fraction_min"]
    vals.update({
        "band_x_px": bx, "band_y_px": by,
        "touch_left": vals["left_fraction"] >= th,
        "touch_right": vals["right_fraction"] >= th,
        "touch_top": vals["top_fraction"] >= th,
        "touch_bottom": vals["bottom_fraction"] >= th,
    })
    return vals


def binocular_edge_evidence(instance_L: np.ndarray, raw_support_L: np.ndarray,
                              instance_R: np.ndarray, raw_support_R: np.ndarray,
                              object_id: int) -> dict:
    """Retired FSG6b/FSG6c per-edge binocular evidence, diagnostics only."""
    left = edge_evidence(instance_L, raw_support_L, object_id)
    right = edge_evidence(instance_R, raw_support_R, object_id)
    th = public.SURFACE_FRONTIER["edge_object_fraction_min"]
    out = {"per_eye": {"L": left, "R": right}}
    for name in ("left", "right", "top", "bottom"):
        f = max(float(left[f"{name}_fraction"]), float(right[f"{name}_fraction"]))
        out[f"{name}_fraction"] = f
        out[f"touch_{name}"] = bool(f >= th)
    out["band_x_px"] = int(left["band_x_px"]); out["band_y_px"] = int(left["band_y_px"])
    return out


def _voxel_centroids(xyz: np.ndarray, cell: float) -> np.ndarray:
    p = np.asarray(xyz, float).reshape(-1, 3)
    p = p[np.isfinite(p).all(1) & (p[:, 2] < -1e-6)]
    if len(p) < 100:
        raise ValueError("too few map points for frontier")
    keys = np.floor(p / cell).astype(np.int64)
    uk, inv = np.unique(keys, axis=0, return_inverse=True)
    cnt = np.bincount(inv)
    sums = np.empty((len(uk), 3), float)
    for d in range(3):
        sums[:, d] = np.bincount(inv, weights=p[:, d], minlength=len(uk))
    return sums / cnt[:, None]


def extract_frontier(map_xyz_h: np.ndarray, current_yaw_deg: float, current_pitch_deg: float,
                     calibration: dict) -> dict:
    """FSG6a frontier extraction, unchanged except exposing its 3D look-ahead point."""
    cfg = public.SURFACE_FRONTIER
    pts = _voxel_centroids(map_xyz_h, cfg["voxel_m"])
    yaw = np.degrees(np.arctan2(pts[:, 0], -pts[:, 2]))
    pitch = np.degrees(np.arctan2(pts[:, 1], np.sqrt(pts[:, 0] ** 2 + pts[:, 2] ** 2)))
    half = float(calibration["nominal_core_fov_deg"]) / 2.0
    margin = cfg["current_view_margin_deg"]
    in_view = ((np.abs(yaw - current_yaw_deg) <= half + margin) &
               (np.abs(pitch - current_pitch_deg) <= half + margin))
    rad = cfg["neighbour_radius_m"]; bins: dict[tuple[int,int,int], list[int]] = defaultdict(list)
    for i, x in enumerate(pts):
        bins[tuple(np.floor(x / rad).astype(np.int64).tolist())].append(i)
    offsets = [(a,b,c) for a in (-1,0,1) for b in (-1,0,1) for c in (-1,0,1)]
    rows = []
    for i in np.flatnonzero(in_view):
        x = pts[i]; k = tuple(np.floor(x / rad).astype(np.int64).tolist()); ids = []
        for o in offsets:
            ids.extend(bins.get((k[0]+o[0], k[1]+o[1], k[2]+o[2]), ()))
        ids = np.asarray(ids, np.int64); ids = ids[ids != i]
        if len(ids) < cfg["minimum_neighbours"]:
            continue
        d = pts[ids] - x; dist = np.linalg.norm(d, axis=1); keep = dist <= rad
        d = d[keep]; dist = dist[keep]
        if len(d) < cfg["minimum_neighbours"]:
            continue
        cov = (d.T @ d) / len(d); _, vec = np.linalg.eigh(cov); normal = vec[:, 0]
        mu = d.mean(axis=0); tangent_mu = mu - normal * float(np.dot(mu, normal))
        nmu = float(np.linalg.norm(tangent_mu)); scale = float(np.mean(dist))
        if nmu <= 1e-12 or scale <= 1e-12:
            continue
        strength = nmu / scale
        if strength < cfg["tangent_asymmetry_min"]:
            continue
        missing = -tangent_mu / nmu
        target = x + cfg["lookahead_m"] * missing
        tyaw = math.degrees(math.atan2(target[0], -target[2]))
        tpitch = math.degrees(math.atan2(target[1], math.sqrt(target[0]**2 + target[2]**2)))
        rows.append((x, target, float(yaw[i]), float(pitch[i]), tyaw, tpitch, strength))
    if rows:
        return {
            "xyz_h": np.vstack([r[0] for r in rows]),
            "target_xyz_h": np.vstack([r[1] for r in rows]),
            "yaw_deg": np.array([r[2] for r in rows]),
            "pitch_deg": np.array([r[3] for r in rows]),
            "target_yaw_deg": np.array([r[4] for r in rows]),
            "target_pitch_deg": np.array([r[5] for r in rows]),
            "strength": np.array([r[6] for r in rows]),
            "voxel_count": int(len(pts)),
        }
    return {
        "xyz_h": np.empty((0,3),float), "target_xyz_h": np.empty((0,3),float),
        "yaw_deg": np.empty(0,float), "pitch_deg": np.empty(0,float),
        "target_yaw_deg": np.empty(0,float), "target_pitch_deg": np.empty(0,float),
        "strength": np.empty(0,float), "voxel_count": int(len(pts)),
    }


def _target_mapped_mask(target_xyz_h: np.ndarray, map_xyz_h: np.ndarray, radius: float | None = None, cell: float | None = None) -> np.ndarray:
    """Return which frontier look-ahead targets are already represented in memory.

    The neighbourhood criterion is deliberately the frozen FSG3/FSG4 fusion
    association rule: same 12 mm radius and 12 mm hash cell, strict d < radius.
    The target is 0.12 m from its source frontier surfel, so the source point
    cannot resolve itself.
    """
    tgt=np.asarray(target_xyz_h,float).reshape(-1,3)
    pts=np.asarray(map_xyz_h,float).reshape(-1,3)
    if radius is None: radius=float(public.FUSION["association_radius_m"])
    if cell is None: cell=float(public.FUSION["hash_cell_m"])
    if radius <= 0 or cell <= 0:
        raise ValueError("map-resolution radius/cell must be positive")
    good=np.isfinite(pts).all(1)
    pts=pts[good]
    bins: dict[tuple[int,int,int], list[int]] = defaultdict(list)
    for i,x in enumerate(pts):
        bins[tuple(np.floor(x/cell).astype(np.int64).tolist())].append(i)
    reach=max(1,int(math.ceil(radius/cell)))
    offsets=[(a,b,c) for a in range(-reach,reach+1) for b in range(-reach,reach+1) for c in range(-reach,reach+1)]
    out=np.zeros(len(tgt),bool)
    for j,x in enumerate(tgt):
        if not np.isfinite(x).all():
            continue
        k=tuple(np.floor(x/cell).astype(np.int64).tolist())
        for o in offsets:
            ids=bins.get((k[0]+o[0],k[1]+o[1],k[2]+o[2]),())
            if ids and np.any(np.linalg.norm(pts[np.asarray(ids,np.int64)]-x,axis=1) < radius):
                out[j]=True; break
    return out


def _target_patch_eye_evidence(instance_id: np.ndarray, raw_support: np.ndarray,
                               object_id: int, target_uv: np.ndarray, target_depth: np.ndarray) -> dict:
    """Object evidence around projected 3D look-ahead targets in one eye.

    Patch radius is derived from the already-frozen edge_band_fraction exactly as
    FSG6d derives its corridor width; no new numerical policy constant is added.
    """
    ids=np.asarray(instance_id); sup=np.asarray(raw_support,bool)
    if ids.shape!=sup.shape or ids.ndim!=2:
        raise ValueError("instance/support arrays must share a 2D shape")
    h,w=ids.shape
    band=max(2,int(round(min(h,w)*public.SURFACE_FRONTIER["edge_band_fraction"])))
    radius=max(1,band//2)
    uv=np.asarray(target_uv,float).reshape(-1,2); depth=np.asarray(target_depth,float).reshape(-1)
    if len(uv)!=len(depth): raise ValueError("target uv/depth length mismatch")
    observable=np.zeros(len(uv),bool); frac=np.zeros(len(uv),float)
    object_pixels=np.zeros(len(uv),np.int32); support_pixels=np.zeros(len(uv),np.int32)
    for i,(q,z) in enumerate(zip(uv,depth)):
        if not (np.isfinite(q).all() and np.isfinite(z) and z>1e-6): continue
        cx,cy=int(round(q[0])),int(round(q[1]))
        if cx<0 or cx>=w or cy<0 or cy>=h: continue
        x0,x1=max(0,cx-radius),min(w,cx+radius+1); y0,y1=max(0,cy-radius),min(h,cy+radius+1)
        den=int(sup[y0:y1,x0:x1].sum())
        if den<=0: continue
        num=int(((ids[y0:y1,x0:x1]==object_id)&sup[y0:y1,x0:x1]).sum())
        observable[i]=True; object_pixels[i]=num; support_pixels[i]=den; frac[i]=float(num/den)
    return {"observable":observable,"fraction":frac,"object_pixels":object_pixels,
            "support_pixels":support_pixels,"patch_radius_px":int(radius)}


def classify_frontier_state(frontier: dict, map_xyz_h: np.ndarray, observation_history: list[dict]) -> dict:
    """Persistent frontier state from 3D memory plus past binocular observations.

    MAP_RESOLVED: the existing look-ahead target is represented in the persistent
    map within the frozen 12 mm FSG3 association radius.

    BOUNDARY_RESOLVED: in at least one completed fixation the same 3D target
    projected into supported local patches in BOTH rectified eyes and the
    binocular object fraction max(f_L,f_R) was below the unchanged 0.15 physical-
    continuation threshold.  Thus the observer has actually looked at that
    hypothesis and found no continuation of the target object there.

    OPEN: neither resolved condition has been observed.  Only OPEN frontiers may
    support a new gaze.  This is a convex-visible-surface completion rule, not a
    hidden-surface/occlusion model; later self-occlusion work must distinguish an
    occluder from a true physical boundary.
    """
    mapped=_target_mapped_mask(frontier["target_xyz_h"],map_xyz_h)
    boundary=np.zeros(len(mapped),bool)
    threshold=float(public.SURFACE_FRONTIER["edge_object_fraction_min"])
    exercised=0
    for obs in observation_history:
        c=obs["calibration"]
        per=[]
        for side in ("L","R"):
            uv,z=_project_rectified_core(c,frontier["target_xyz_h"],side)
            per.append(_target_patch_eye_evidence(obs[f"instance_{side}"],obs[f"raw_support_{side}"],
                                                   public.OBJECT_ID,uv,z))
        both=per[0]["observable"] & per[1]["observable"]
        combined=np.maximum(per[0]["fraction"],per[1]["fraction"])
        boundary |= (~mapped) & both & (combined < threshold)
        exercised += int(both.sum())
    open_mask=~(mapped|boundary)
    return {
        "map_resolved":mapped,"boundary_resolved":boundary,"open":open_mask,
        "raw_count":int(len(mapped)),"map_resolved_count":int(mapped.sum()),
        "boundary_resolved_count":int(boundary.sum()),"open_count":int(open_mask.sum()),
        "historical_target_tests":int(exercised),
        "rule":"lookahead_target_mapped_or_binocular_history_says_object_absent",
        "radius_m":float(public.FUSION["association_radius_m"]),
        "threshold":threshold,
    }


def _project_rectified_core(calibration: dict, xyz_h: np.ndarray, side: str) -> tuple[np.ndarray, np.ndarray]:
    """Project H-frame points into the same rectified/cropped core used by FSG1."""
    from fsg_stereo import rectification
    if side not in ("L", "R"):
        raise ValueError("side must be L or R")
    r = rectification(calibration)
    eye = calibration["eyes"][0 if side == "L" else 1]
    p = np.asarray(xyz_h, float).reshape(-1, 3)
    xyz_c = (p - np.asarray(eye["centre_h_m"], float)) @ np.asarray(eye["R_hc"], float)
    rr = np.asarray(r["R1" if side == "L" else "R2"], float)
    xyz_rect = xyz_c @ rr.T
    krect = np.asarray(r["P1" if side == "L" else "P2"], float)[:, :3]
    a = xyz_rect @ krect.T
    with np.errstate(divide="ignore", invalid="ignore"):
        uv = a[:, :2] / a[:, 2:3]
    x, y, _, _ = map(int, r["crop_xywh"])
    uv -= np.array([x, y], float)
    return uv, xyz_rect[:, 2]


def _ray_exit(q: np.ndarray, d: np.ndarray, w: int, h: int) -> np.ndarray | None:
    """Forward intersection of a 2D ray with the closed core rectangle."""
    u, v = map(float, q); du, dv = map(float, d)
    ts = []
    if du > 1e-12: ts.append((w - 1.0 - u) / du)
    elif du < -1e-12: ts.append((0.0 - u) / du)
    if dv > 1e-12: ts.append((h - 1.0 - v) / dv)
    elif dv < -1e-12: ts.append((0.0 - v) / dv)
    ts = [t for t in ts if t >= 0.0 and np.isfinite(t)]
    if not ts:
        return None
    p = np.asarray(q, float) + min(ts) * np.asarray(d, float)
    if p[0] < -1e-6 or p[0] > w - 1 + 1e-6 or p[1] < -1e-6 or p[1] > h - 1 + 1e-6:
        return None
    return p


def _exit_corridor_mask(shape: tuple[int,int], start_uv: np.ndarray, target_uv: np.ndarray, dx: int, dy: int) -> tuple[np.ndarray, int]:
    """Rasterize the last legacy-band-width portion of projected frontier rays.

    No new numerical policy constant is introduced: both longitudinal length and
    transverse half-width are derived from the already-frozen edge_band_fraction.
    """
    h, w = map(int, shape)
    band = max(2, int(round(min(h, w) * public.SURFACE_FRONTIER["edge_band_fraction"])))
    radius = max(1, band // 2)
    mask = np.zeros((h, w), bool); used = 0
    s = np.asarray(start_uv, float).reshape(-1,2); t = np.asarray(target_uv, float).reshape(-1,2)
    for q, z in zip(s, t):
        if not (np.isfinite(q).all() and np.isfinite(z).all()):
            continue
        # The current frontier must actually be observable in the current core.
        if q[0] < 0 or q[0] > w-1 or q[1] < 0 or q[1] > h-1:
            continue
        d = z - q; n = float(np.linalg.norm(d))
        if n <= 1e-9:
            continue
        e = _ray_exit(q, d, w, h)
        if e is None:
            continue
        # A diagonal candidate must be supported in its own forward image sector,
        # not by an exit on the opposite half of a component edge.  This is the
        # local distinction missed by both the retired all() and max() rules.
        cx, cy = (w - 1.0) / 2.0, (h - 1.0) / 2.0
        if dx < 0 and e[0] > cx + 1e-9: continue
        if dx > 0 and e[0] < cx - 1e-9: continue
        # +pitch is upward, while image v grows downward.
        if dy > 0 and e[1] > cy + 1e-9: continue
        if dy < 0 and e[1] < cy - 1e-9: continue
        used += 1
        u = d / n
        # Sample only the terminal band-length segment, backwards from the exit.
        for a in np.linspace(0.0, float(band), band + 1):
            p = e - a * u
            cx, cy = int(round(p[0])), int(round(p[1]))
            x0, x1 = max(0, cx-radius), min(w, cx+radius+1)
            y0, y1 = max(0, cy-radius), min(h, cy+radius+1)
            if x0 < x1 and y0 < y1:
                mask[y0:y1, x0:x1] = True
    return mask, used


def _corridor_eye_evidence(instance_id: np.ndarray, raw_support: np.ndarray, object_id: int,
                           start_uv: np.ndarray, target_uv: np.ndarray, dx: int, dy: int) -> dict:
    ids = np.asarray(instance_id); sup = np.asarray(raw_support, bool)
    if ids.shape != sup.shape or ids.ndim != 2:
        raise ValueError("instance/support arrays must share a 2D shape")
    corridor, rays = _exit_corridor_mask(ids.shape, start_uv, target_uv, dx, dy)
    denom_mask = corridor & sup
    den = int(denom_mask.sum())
    num = int(((ids == object_id) & denom_mask).sum())
    frac = float(num / den) if den else 0.0
    return {"fraction": frac, "object_pixels": num, "support_pixels": den,
            "projected_frontier_rays": int(rays), "corridor_pixels": int(corridor.sum())}


def _project_frontier_pairs(calibration: dict, frontier_xyz_h: np.ndarray,
                            frontier_target_xyz_h: np.ndarray) -> dict:
    xyz=np.asarray(frontier_xyz_h,float).reshape(-1,3)
    tgt=np.asarray(frontier_target_xyz_h,float).reshape(-1,3)
    if xyz.shape!=tgt.shape: raise ValueError("frontier and target 3D arrays must match")
    out={}
    for side in ("L","R"):
        uv0,z0=_project_rectified_core(calibration,xyz,side); uv1,z1=_project_rectified_core(calibration,tgt,side)
        good=np.isfinite(z0)&np.isfinite(z1)&(z0>1e-6)&(z1>1e-6)
        out[side]={"start_uv":uv0,"target_uv":uv1,"good":good}
    return out


def _candidate_continuation_from_projected(dx: int, dy: int,
                                            instance_L: np.ndarray, raw_support_L: np.ndarray,
                                            instance_R: np.ndarray, raw_support_R: np.ndarray,
                                            projected: dict, support_mask: np.ndarray,
                                            object_id: int) -> dict:
    support_mask=np.asarray(support_mask,bool).reshape(-1)
    per_eye={}
    for side,ids,sup in (("L",instance_L,raw_support_L),("R",instance_R,raw_support_R)):
        q=projected[side]; use=support_mask&q["good"]
        per_eye[side]=_corridor_eye_evidence(ids,sup,object_id,q["start_uv"][use],q["target_uv"][use],dx,dy)
    value=max(float(per_eye["L"]["fraction"]),float(per_eye["R"]["fraction"]))
    threshold=float(public.SURFACE_FRONTIER["edge_object_fraction_min"])
    return {"direction":[int(dx),int(dy)],"per_eye":per_eye,"combined_fraction":value,
            "threshold":threshold,"allowed":bool(value>=threshold),
            "rule":"projected_frontier_exit_corridor_forward_sector_binocular_max"}


def candidate_continuation_evidence(dx: int, dy: int, calibration: dict,
                                    instance_L: np.ndarray, raw_support_L: np.ndarray,
                                    instance_R: np.ndarray, raw_support_R: np.ndarray,
                                    frontier_xyz_h: np.ndarray, frontier_target_xyz_h: np.ndarray,
                                    object_id: int) -> dict:
    """Candidate-local, binocular, projected-frontier exit-corridor evidence."""
    if dx not in (-1,0,1) or dy not in (-1,0,1) or (dx==0 and dy==0):
        raise ValueError("candidate direction must be a nonzero 8-neighbour lattice step")
    projected=_project_frontier_pairs(calibration,frontier_xyz_h,frontier_target_xyz_h)
    return _candidate_continuation_from_projected(dx,dy,instance_L,raw_support_L,instance_R,raw_support_R,
                                                   projected,np.ones(len(np.asarray(frontier_xyz_h).reshape(-1,3)),bool),object_id)


def _retired_component_conjunction_allowed(dx: int, dy: int, ev: dict) -> bool:
    ok = []
    if dx < 0: ok.append(ev["touch_left"])
    if dx > 0: ok.append(ev["touch_right"])
    if dy > 0: ok.append(ev["touch_top"])
    if dy < 0: ok.append(ev["touch_bottom"])
    return bool(ok and all(ok))


def _retired_component_max_allowed(dx: int, dy: int, ev: dict) -> bool:
    vals = []
    if dx < 0: vals.append(ev["left_fraction"])
    if dx > 0: vals.append(ev["right_fraction"])
    if dy > 0: vals.append(ev["top_fraction"])
    if dy < 0: vals.append(ev["bottom_fraction"])
    return bool(vals and max(vals) >= public.SURFACE_FRONTIER["edge_object_fraction_min"])


def _new_box_area(candidate: tuple[float,float], half: float, yaw_extent: tuple[float,float], pitch_extent: tuple[float,float]) -> float:
    cy, cp = candidate; a,b = cy-half, cy+half; c,d = cp-half, cp+half
    yl,yh = yaw_extent; pl,ph = pitch_extent
    inter = max(0.0, min(b,yh)-max(a,yl)) * max(0.0, min(d,ph)-max(c,pl))
    return float((2*half)**2 - inter)


def candidate_state_consensus(n_open: int, n_map_resolved: int, n_boundary_resolved: int) -> dict:
    """Aggregate persistent surfel states into an action-level exploration state.

    A direction is exploration-open only when OPEN strictly outnumbers the two
    resolved states together.  Ties are resolved.  The frozen >=8 OPEN support
    gate remains a separate requirement in choose_next().
    """
    vals = [int(n_open), int(n_map_resolved), int(n_boundary_resolved)]
    if any(v < 0 for v in vals):
        raise ValueError("candidate frontier-state counts must be nonnegative")
    no, nm, nb = vals
    nr = nm + nb
    return {
        "open_support_count": no,
        "map_resolved_support_count": nm,
        "boundary_resolved_support_count": nb,
        "resolved_support_count": nr,
        "raw_support_count": no + nr,
        "allowed": bool(no > nr),
        "rule": "strict_open_majority_over_resolved_state",
    }


def _retired_any_open_allowed(n_open: int) -> bool:
    """FSG6e candidate rule retained only as a diagnostic negative control."""
    return int(n_open) >= int(public.SURFACE_FRONTIER["minimum_candidate_frontier_support"])


def choose_next(current_yaw_deg: float, current_pitch_deg: float, calibration: dict,
                instance_L: np.ndarray, raw_support_L: np.ndarray,
                instance_R: np.ndarray, raw_support_R: np.ndarray,
                map_xyz_h: np.ndarray, visited_gazes_deg: list[tuple[float,float]],
                observation_history: list[dict]) -> dict:
    cfg = public.SURFACE_FRONTIER
    frontier = extract_frontier(map_xyz_h, current_yaw_deg, current_pitch_deg, calibration)
    frontier_state = classify_frontier_state(frontier, map_xyz_h, observation_history)
    map_yaw, map_pitch = angular_coordinates(map_xyz_h)
    q = cfg["map_extent_quantile"]
    ye = (float(np.quantile(map_yaw, q)), float(np.quantile(map_yaw, 1-q)))
    pe = (float(np.quantile(map_pitch, q)), float(np.quantile(map_pitch, 1-q)))
    half = float(calibration["nominal_core_fov_deg"]) / 2.0
    step = cfg["component_step_deg"]
    seen = np.asarray(visited_gazes_deg, float).reshape(-1,2) if visited_gazes_deg else np.empty((0,2))
    candidates = []
    consensus_rejected_candidates = []
    fy, fp = frontier["yaw_deg"], frontier["pitch_deg"]
    fty, ftp = frontier["target_yaw_deg"], frontier["target_pitch_deg"]
    fs = frontier["strength"]
    projected_all = _project_frontier_pairs(calibration, frontier["xyz_h"], frontier["target_xyz_h"])
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            if dx == 0 and dy == 0:
                continue
            yaw = float(current_yaw_deg + dx*step); pitch = float(current_pitch_deg + dy*step)
            if not (cfg["yaw_min_deg"]-1e-9 <= yaw <= cfg["yaw_max_deg"]+1e-9 and
                    cfg["pitch_min_deg"]-1e-9 <= pitch <= cfg["pitch_max_deg"]+1e-9):
                continue
            if len(seen) and np.any(np.all(np.isclose(seen, [yaw,pitch], atol=1e-9), axis=1)):
                continue
            u = np.array([dx,dy], float); u /= np.linalg.norm(u)
            if len(fs):
                delta = np.c_[fty-fy, ftp-fp]
                dn = np.linalg.norm(delta, axis=1); good = dn > 1e-12
                align = np.zeros(len(delta), float); align[good] = (delta[good] / dn[good,None]) @ u
                raw_support = align >= cfg["alignment_cos_min"]
                support = raw_support & frontier_state["open"]
                n_raw_support = int(raw_support.sum())
                n_support = int(support.sum())
                n_map_resolved_support = int((raw_support & frontier_state["map_resolved"]).sum())
                n_boundary_resolved_support = int((raw_support & frontier_state["boundary_resolved"]).sum())
                frontier_score = float(np.sum(fs[support] * align[support]))
            else:
                raw_support = np.zeros(0,bool); support = np.zeros(0,bool)
                n_raw_support = 0; n_support = 0; n_map_resolved_support = 0; n_boundary_resolved_support = 0; frontier_score = 0.0
            if n_raw_support != n_support + n_map_resolved_support + n_boundary_resolved_support:
                raise AssertionError("candidate frontier-state partition is not exhaustive")
            consensus = candidate_state_consensus(n_support, n_map_resolved_support, n_boundary_resolved_support)
            if n_support < cfg["minimum_candidate_frontier_support"]:
                continue
            continuation = _candidate_continuation_from_projected(
                dx, dy, instance_L, raw_support_L, instance_R, raw_support_R,
                projected_all, support, public.OBJECT_ID)
            if not continuation["allowed"]:
                continue
            new_area = _new_box_area((yaw,pitch), half, ye, pe)
            record = {
                "yaw_deg": yaw, "pitch_deg": pitch,
                "delta_yaw_deg": float(dx*step), "delta_pitch_deg": float(dy*step),
                "frontier_support_count": n_support,
                "raw_frontier_support_count": n_raw_support,
                "map_resolved_support_count": n_map_resolved_support,
                "boundary_resolved_support_count": n_boundary_resolved_support,
                "resolved_frontier_support_count": int(consensus["resolved_support_count"]),
                "candidate_state_consensus": consensus,
                "frontier_score": frontier_score,
                "predicted_new_angular_area_deg2": new_area,
                "continuation": continuation,
            }
            if not consensus["allowed"]:
                consensus_rejected_candidates.append(record)
                continue
            candidates.append(record)
    candidates.sort(key=lambda c: (-c["predicted_new_angular_area_deg2"], -c["frontier_score"],
                                   abs(c["delta_yaw_deg"])+abs(c["delta_pitch_deg"]),
                                   c["yaw_deg"], c["pitch_deg"]))
    best = candidates[0] if candidates else None
    return {
        "current_gaze_deg": [float(current_yaw_deg), float(current_pitch_deg)],
        "map_yaw_extent_deg": list(ye), "map_pitch_extent_deg": list(pe),
        "frontier_voxel_count": int(frontier["voxel_count"]),
        "frontier_count": int(len(frontier["strength"])),
        "frontier_raw_count": frontier_state["raw_count"],
        "frontier_map_resolved_count": frontier_state["map_resolved_count"],
        "frontier_boundary_resolved_count": frontier_state["boundary_resolved_count"],
        "frontier_open_count": frontier_state["open_count"],
        "frontier_state_rule": frontier_state["rule"],
        "frontier_state_radius_m": frontier_state["radius_m"],
        "frontier_state_threshold": frontier_state["threshold"],
        "frontier_historical_target_tests": frontier_state["historical_target_tests"],
        "candidates": candidates,
        "consensus_rejected_candidates": consensus_rejected_candidates,
        "consensus_rejected_candidate_count": int(len(consensus_rejected_candidates)),
        "candidate_state_rule": "strict_open_majority_over_resolved_state",
        "candidates_before_consensus_count": int(len(candidates) + len(consensus_rejected_candidates)),
        "stop": best is None,
        "reason": "no_frontier" if best is None else "continue",
        "next_gaze_deg": None if best is None else [float(best["yaw_deg"]), float(best["pitch_deg"])],
        "selected": best,
    }


def _xyz_patch(yaw_range: tuple[float,float], pitch_range: tuple[float,float], r: float = 2.1) -> np.ndarray:
    y = np.radians(np.linspace(yaw_range[0], yaw_range[1], 45)); p = np.radians(np.linspace(pitch_range[0], pitch_range[1], 35))
    Y,P = np.meshgrid(y,p)
    x = r*np.cos(P)*np.sin(Y); yy = r*np.sin(P); z = -r*np.cos(P)*np.cos(Y)
    return np.c_[x.ravel(), yy.ravel(), z.ravel()]


def _rolled_strip_mask(n: int, object_id: int, background_id: int) -> np.ndarray:
    a=np.full((n,n),background_id,np.int32)
    # exits high on the right boundary but does not touch the top row
    for row in range(14, max(15, n//2)):
        x0=max(0,int(88-0.55*(row-14)))
        a[row,x0:]=object_id
    return a


def self_test() -> None:
    from fsg_geometry import make_calibration
    n=128; sup=np.ones((n,n),bool); cal=make_calibration("small",0.0,0.0,public.VERGENCE_DISTANCE_M)
    full=np.full((n,n),public.OBJECT_ID,np.int32)
    bg=np.full((n,n),public.BACKGROUND_ID,np.int32)

    # Frontier-state unit controls. The source frontier itself must not resolve its
    # 0.12 m look-ahead target; an actual map point within the frozen 12 mm radius must.
    target=np.array([[0.0,0.0,-2.10]],float)
    source=np.array([[-public.SURFACE_FRONTIER["lookahead_m"],0.0,-2.10]],float)
    if bool(_target_mapped_mask(target,source)[0]):
        raise AssertionError("frontier source incorrectly resolves its own look-ahead target")
    mapped_map=np.vstack([source,target+np.array([[0.005,0.0,0.0]])])
    if not bool(_target_mapped_mask(target,mapped_map)[0]):
        raise AssertionError("frozen 12 mm map association failed to resolve represented target")
    f={"target_xyz_h":target}
    hist_bg=[{"calibration":cal,"instance_L":bg,"raw_support_L":sup,
              "instance_R":bg,"raw_support_R":sup}]
    st_bg=classify_frontier_state(f,source,hist_bg)
    if not bool(st_bg["boundary_resolved"][0]) or bool(st_bg["open"][0]):
        raise AssertionError("completed binocular background observation did not boundary-resolve target")
    hist_obj=[{"calibration":cal,"instance_L":full,"raw_support_L":sup,
               "instance_R":full,"raw_support_R":sup}]
    st_obj=classify_frontier_state(f,source,hist_obj)
    if bool(st_obj["boundary_resolved"][0]) or not bool(st_obj["open"][0]):
        raise AssertionError("observed object target was incorrectly treated as a resolved stereo hole/boundary")
    st_map=classify_frontier_state(f,mapped_map,hist_bg)
    if not bool(st_map["map_resolved"][0]) or bool(st_map["open"][0]):
        raise AssertionError("mapped target did not become MAP_RESOLVED")
    # Eye-swap invariance of historical evidence: one eye object + one background
    # remains OPEN under binocular max in either ordering.
    hmix1=[{"calibration":cal,"instance_L":full,"raw_support_L":sup,
            "instance_R":bg,"raw_support_R":sup}]
    hmix2=[{"calibration":cal,"instance_L":bg,"raw_support_L":sup,
            "instance_R":full,"raw_support_R":sup}]
    if not np.array_equal(classify_frontier_state(f,source,hmix1)["open"],
                          classify_frontier_state(f,source,hmix2)["open"]):
        raise AssertionError("historical frontier state changed under eye swap")

    # Same current masks, different persistent 3D maps: 3D map state controls direction.
    a=choose_next(0.0,0.0,cal,full,sup,full,sup,_xyz_patch((-11,1),(-11,1)),[(0.0,0.0)],[])
    b=choose_next(0.0,0.0,cal,full,sup,full,sup,_xyz_patch((-1,11),(-1,11)),[(0.0,0.0)],[])
    if a["next_gaze_deg"] != [5.0,5.0] or b["next_gaze_deg"] != [-5.0,-5.0]:
        raise AssertionError(f"3D map state must reverse the gaze: {a['next_gaze_deg']} / {b['next_gaze_deg']}")

    # FSG6d continuation remains eye-symmetric and preserves the valid corner move.
    strip=_rolled_strip_mask(n,public.OBJECT_ID,public.BACKGROUND_ID)
    R=strip.copy(); R[:,-12:]=public.BACKGROUND_ID
    c1=choose_next(0.0,0.0,cal,strip,sup,R,sup,_xyz_patch((-11,1),(-11,1)),[(0.0,0.0)],[])
    c2=choose_next(0.0,0.0,cal,R,sup,strip,sup,_xyz_patch((-11,1),(-11,1)),[(0.0,0.0)],[])
    if c1["next_gaze_deg"] != c2["next_gaze_deg"]:
        raise AssertionError("selected gaze changed under eye swap")
    # Symmetric strip is the stronger deterministic corner control.
    c=choose_next(0.0,0.0,cal,strip,sup,strip,sup,_xyz_patch((-11,1),(-11,1)),[(0.0,0.0)],[])
    if c["next_gaze_deg"] != [5.0,5.0]:
        raise AssertionError(f"projected frontier corridor rejected valid up-right continuation: {c['next_gaze_deg']}")

    # Dual FSG6c regression: a strong right edge cannot license a down-right local exit.
    down_map=_xyz_patch((-11,1),(-1,11))
    d=choose_next(0.0,0.0,cal,strip,sup,strip,sup,down_map,[(0.0,0.0)],[])
    if d["next_gaze_deg"] == [5.0,-5.0]:
        raise AssertionError("strong right edge incorrectly licensed a down-right candidate")

    # Candidate-level persistent-state consensus: OPEN must strictly outnumber
    # resolved support. A tie is not an exploration action.
    if not candidate_state_consensus(9,4,4)["allowed"]:
        raise AssertionError("strict OPEN-majority candidate consensus rejected a true majority")
    if candidate_state_consensus(8,4,4)["allowed"]:
        raise AssertionError("candidate state tie incorrectly remained exploration-open")

    # Fully inset object boundary in current binocular view -> no eligible continuation.
    inset=np.full((n,n),public.OBJECT_ID,np.int32); q=12
    inset[:q,:]=public.BACKGROUND_ID; inset[-q:,:]=public.BACKGROUND_ID; inset[:,:q]=public.BACKGROUND_ID; inset[:,-q:]=public.BACKGROUND_ID
    z=choose_next(0.0,0.0,cal,inset,sup,inset,sup,_xyz_patch((-5,5),(-5,5)),[(0.0,0.0)],[])
    if not z["stop"] or z["reason"] != "no_frontier":
        raise AssertionError("resolved current object boundary must stop 3D frontier exploration")
    print("[fsg6f-frontier] PASS map_state_changes_2d_direction=true persistent_state_three_way=true historical_boundary_state=true stereo_hole_not_boundary=true eye_swap_invariant=true projected_frontier_corridor=true resolved_boundary_stops=true candidate_state_consensus=true")

if __name__ == "__main__":
    self_test()
