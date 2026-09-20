"""Truth-free 3D surfel-frontier controller for FSG6c.

The frontier is extracted from local asymmetry of the persistent 3D surfel map:
a boundary surfel has neighbours predominantly on the already-reconstructed side.
A local PCA removes normal/curvature bias before measuring that asymmetry.  The
oracle mask is used only as an object-continuation veto for the current image
edge(s); it does not create or score the frontier.
"""
from __future__ import annotations
from collections import defaultdict
import math
import numpy as np
import fsg6c_public as public


def angular_coordinates(xyz_h: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    p = np.asarray(xyz_h, float).reshape(-1, 3)
    good = np.isfinite(p).all(1) & (p[:, 2] < -1e-6)
    p = p[good]
    if len(p) < 100:
        raise ValueError("too few finite forward map points for FSG6c policy")
    yaw = np.degrees(np.arctan2(p[:, 0], -p[:, 2]))
    pitch = np.degrees(np.arctan2(p[:, 1], np.sqrt(p[:, 0] ** 2 + p[:, 2] ** 2)))
    return yaw, pitch


def edge_evidence(instance_id: np.ndarray, raw_support: np.ndarray, object_id: int) -> dict:
    """Per-eye directional object-continuation evidence in a rectified core."""
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
    """Eye-swap-invariant continuation evidence; threshold is unchanged from FSG6a.

    For each directional edge, the physical-boundary veto accepts continuation if
    EITHER rectified eye sees sufficient object support.  The 3D map still creates
    and ranks frontier candidates; this function can only veto them.
    """
    left = edge_evidence(instance_L, raw_support_L, object_id)
    right = edge_evidence(instance_R, raw_support_R, object_id)
    th = public.SURFACE_FRONTIER["edge_object_fraction_min"]
    out = {"per_eye": {"L": left, "R": right}}
    for name in ("left", "right", "top", "bottom"):
        f = max(float(left[f"{name}_fraction"]), float(right[f"{name}_fraction"]))
        out[f"{name}_fraction"] = f
        out[f"touch_{name}"] = bool(f >= th)
    out["band_x_px"] = int(left["band_x_px"]); out["band_y_px"] = int(left["band_y_px"])
    if out["band_x_px"] != int(right["band_x_px"]) or out["band_y_px"] != int(right["band_y_px"]):
        raise ValueError("left/right edge-band geometry differs")
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
        rows.append((x, float(yaw[i]), float(pitch[i]), tyaw, tpitch, strength))
    if rows:
        return {
            "xyz_h": np.vstack([r[0] for r in rows]),
            "yaw_deg": np.array([r[1] for r in rows]),
            "pitch_deg": np.array([r[2] for r in rows]),
            "target_yaw_deg": np.array([r[3] for r in rows]),
            "target_pitch_deg": np.array([r[4] for r in rows]),
            "strength": np.array([r[5] for r in rows]),
            "voxel_count": int(len(pts)),
        }
    return {k: np.empty((0,3),float) if k == "xyz_h" else np.empty(0,float)
            for k in ("xyz_h","yaw_deg","pitch_deg","target_yaw_deg","target_pitch_deg","strength")} | {"voxel_count": int(len(pts))}


def directional_continuation_evidence(dx: int, dy: int, ev: dict) -> dict:
    """Candidate-aligned physical-boundary evidence on the forward perimeter.

    A movement direction defines the part of the current foveal perimeter through
    which the surface may legitimately leave.  Axis-aligned moves have one
    compatible edge.  Diagonal moves have two compatible edges, and continuation
    through EITHER is sufficient; requiring both is the retired FSG6a/FSG6b
    component-conjunction defect.  `ev` is already binocular and eye-swap
    invariant, so no reference eye is privileged here.
    """
    if dx not in (-1, 0, 1) or dy not in (-1, 0, 1) or (dx == 0 and dy == 0):
        raise ValueError("candidate direction must be a nonzero 8-neighbour lattice step")
    edges = []
    if dx < 0: edges.append("left")
    if dx > 0: edges.append("right")
    if dy > 0: edges.append("top")
    if dy < 0: edges.append("bottom")
    fractions = {name: float(ev[f"{name}_fraction"]) for name in edges}
    value = max(fractions.values())
    threshold = float(public.SURFACE_FRONTIER["edge_object_fraction_min"])
    return {
        "direction": [int(dx), int(dy)],
        "compatible_edges": list(edges),
        "edge_fractions": fractions,
        "combined_fraction": float(value),
        "threshold": threshold,
        "allowed": bool(value >= threshold),
        "rule": "max_over_direction_compatible_edges",
    }


def _candidate_edge_allowed(dx: int, dy: int, ev: dict) -> bool:
    return bool(directional_continuation_evidence(dx, dy, ev)["allowed"])


def _retired_component_conjunction_allowed(dx: int, dy: int, ev: dict) -> bool:
    """FSG6a/FSG6b rule retained only for fail-capable diagnostics."""
    ok = []
    if dx < 0: ok.append(ev["touch_left"])
    if dx > 0: ok.append(ev["touch_right"])
    if dy > 0: ok.append(ev["touch_top"])
    if dy < 0: ok.append(ev["touch_bottom"])
    return bool(ok and all(ok))


def _new_box_area(candidate: tuple[float,float], half: float, yaw_extent: tuple[float,float], pitch_extent: tuple[float,float]) -> float:
    cy, cp = candidate; a,b = cy-half, cy+half; c,d = cp-half, cp+half
    yl,yh = yaw_extent; pl,ph = pitch_extent
    inter = max(0.0, min(b,yh)-max(a,yl)) * max(0.0, min(d,ph)-max(c,pl))
    return float((2*half)**2 - inter)


def choose_next(current_yaw_deg: float, current_pitch_deg: float, calibration: dict,
                instance_L: np.ndarray, raw_support_L: np.ndarray,
                instance_R: np.ndarray, raw_support_R: np.ndarray,
                map_xyz_h: np.ndarray, visited_gazes_deg: list[tuple[float,float]]) -> dict:
    cfg = public.SURFACE_FRONTIER
    ev = binocular_edge_evidence(instance_L, raw_support_L, instance_R, raw_support_R, public.OBJECT_ID)
    frontier = extract_frontier(map_xyz_h, current_yaw_deg, current_pitch_deg, calibration)
    map_yaw, map_pitch = angular_coordinates(map_xyz_h)
    q = cfg["map_extent_quantile"]
    ye = (float(np.quantile(map_yaw, q)), float(np.quantile(map_yaw, 1-q)))
    pe = (float(np.quantile(map_pitch, q)), float(np.quantile(map_pitch, 1-q)))
    half = float(calibration["nominal_core_fov_deg"]) / 2.0
    step = cfg["component_step_deg"]
    seen = np.asarray(visited_gazes_deg, float).reshape(-1,2) if visited_gazes_deg else np.empty((0,2))
    candidates = []
    fy, fp = frontier["yaw_deg"], frontier["pitch_deg"]
    fty, ftp = frontier["target_yaw_deg"], frontier["target_pitch_deg"]
    fs = frontier["strength"]
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
            continuation = directional_continuation_evidence(dx, dy, ev)
            if not continuation["allowed"]:
                continue
            u = np.array([dx,dy], float); u /= np.linalg.norm(u)
            if len(fs):
                delta = np.c_[fty-fy, ftp-fp]
                dn = np.linalg.norm(delta, axis=1); good = dn > 1e-12
                align = np.zeros(len(delta), float); align[good] = (delta[good] / dn[good,None]) @ u
                support = align >= cfg["alignment_cos_min"]
                n_support = int(support.sum()); frontier_score = float(np.sum(fs[support] * align[support]))
            else:
                n_support = 0; frontier_score = 0.0
            if n_support < cfg["minimum_candidate_frontier_support"]:
                continue
            new_area = _new_box_area((yaw,pitch), half, ye, pe)
            candidates.append({
                "yaw_deg": yaw, "pitch_deg": pitch,
                "delta_yaw_deg": float(dx*step), "delta_pitch_deg": float(dy*step),
                "frontier_support_count": n_support, "frontier_score": frontier_score,
                "predicted_new_angular_area_deg2": new_area,
                "continuation": continuation,
            })
    candidates.sort(key=lambda c: (-c["predicted_new_angular_area_deg2"], -c["frontier_score"],
                                   abs(c["delta_yaw_deg"])+abs(c["delta_pitch_deg"]),
                                   c["yaw_deg"], c["pitch_deg"]))
    best = candidates[0] if candidates else None
    return {
        "current_gaze_deg": [float(current_yaw_deg), float(current_pitch_deg)],
        "map_yaw_extent_deg": list(ye), "map_pitch_extent_deg": list(pe),
        "edge": ev,
        "frontier_voxel_count": int(frontier["voxel_count"]),
        "frontier_count": int(len(frontier["strength"])),
        "candidates": candidates,
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


def self_test() -> None:
    n=128; sup=np.ones((n,n),bool); cal={"nominal_core_fov_deg":12.0}
    ids=np.full((n,n), public.OBJECT_ID, np.int32)
    # Same binocular masks, different persistent maps: map state must reverse gaze.
    a=choose_next(0.0,0.0,cal,ids,sup,ids,sup,_xyz_patch((-11,1),(-11,1)),[(0.0,0.0)])
    b=choose_next(0.0,0.0,cal,ids,sup,ids,sup,_xyz_patch((-1,11),(-1,11)),[(0.0,0.0)])
    if a["next_gaze_deg"] != [5.0,5.0] or b["next_gaze_deg"] != [-5.0,-5.0]:
        raise AssertionError(f"3D map state must reverse the gaze: {a['next_gaze_deg']} / {b['next_gaze_deg']}")

    # Eye-swap invariance remains mandatory after FSG6b.
    L=np.full((n,n), public.OBJECT_ID, np.int32); R=L.copy(); k=12
    L[:k,:]=public.BACKGROUND_ID; L[:,-k:]=public.BACKGROUND_ID
    ev1=binocular_edge_evidence(L,sup,R,sup,public.OBJECT_ID)
    ev2=binocular_edge_evidence(R,sup,L,sup,public.OBJECT_ID)
    for q in ("left_fraction","right_fraction","top_fraction","bottom_fraction","touch_left","touch_right","touch_top","touch_bottom"):
        if ev1[q] != ev2[q]: raise AssertionError(f"binocular continuation changed under eye swap: {q}")
    c1=choose_next(0.0,0.0,cal,L,sup,R,sup,_xyz_patch((-11,1),(-11,1)),[(0.0,0.0)])
    c2=choose_next(0.0,0.0,cal,R,sup,L,sup,_xyz_patch((-11,1),(-11,1)),[(0.0,0.0)])
    if c1["next_gaze_deg"] != c2["next_gaze_deg"]:
        raise AssertionError("selected gaze changed under L/R swap")

    # Diagonal corner continuation: right edge clearly continues while the top
    # edge is genuinely resolved.  Candidate-aligned semantics must permit the
    # up-right move; the retired component conjunction must veto it.
    C=np.full((n,n), public.BACKGROUND_ID, np.int32)
    # A rolled strip exits high on the right side but never touches the top row.
    for row in range(14,n):
        x0=max(0, int(88 - 0.55*(row-14)))
        C[row, x0:]=public.OBJECT_ID
    ev=binocular_edge_evidence(C,sup,C,sup,public.OBJECT_ID)
    new=directional_continuation_evidence(+1,+1,ev)
    old=_retired_component_conjunction_allowed(+1,+1,ev)
    if not new["allowed"] or old:
        raise AssertionError(f"candidate-aligned diagonal continuation not distinguished from retired conjunction: new={new} old={old}")

    # True physical termination on all forward-compatible edges still vetoes.
    T=np.full((n,n), public.OBJECT_ID, np.int32); q=12
    T[:q,:]=public.BACKGROUND_ID; T[:,-q:]=public.BACKGROUND_ID
    evT=binocular_edge_evidence(T,sup,T,sup,public.OBJECT_ID)
    if directional_continuation_evidence(+1,+1,evT)["allowed"]:
        raise AssertionError("resolved forward perimeter must veto a diagonal candidate")

    # Fully resolved object boundary in BOTH eyes -> stop even with geometric frontier.
    ids2=np.full((n,n), public.OBJECT_ID, np.int32); q=10
    ids2[:q,:]=public.BACKGROUND_ID; ids2[-q:,:]=public.BACKGROUND_ID; ids2[:,:q]=public.BACKGROUND_ID; ids2[:,-q:]=public.BACKGROUND_ID
    z=choose_next(0.0,0.0,cal,ids2,sup,ids2,sup,_xyz_patch((-5,5),(-5,5)),[(0.0,0.0)])
    if not z["stop"] or z["reason"] != "no_frontier":
        raise AssertionError("resolved object boundary must stop 3D frontier exploration")
    print("[fsg6c-frontier] PASS map_state_changes_2d_direction=true eye_swap_invariant=true diagonal_corner_continuation=true resolved_boundary_stops=true")

if __name__ == "__main__":
    self_test()
