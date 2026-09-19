"""Truth-free horizontal frontier policy for FSG4 Increment 4.

This is the FSG3 policy transferred unchanged in substance to the FSG4 public
contract: current oracle mask + persistent reconstructed map + calibration +
fixation history; no fixture geometry or evaluator assets.
"""
from __future__ import annotations
import numpy as np
import fsg4_public as public


def map_yaws_deg(xyz_h: np.ndarray) -> np.ndarray:
    x = np.asarray(xyz_h, float).reshape(-1, 3)
    good = np.isfinite(x).all(1) & (x[:, 2] < -1e-6)
    if good.sum() < 100:
        raise ValueError("too few finite forward map points for policy")
    return np.degrees(np.arctan2(x[good, 0], -x[good, 2]))


def edge_evidence(instance_id: np.ndarray, raw_support: np.ndarray, object_id: int) -> dict:
    ids = np.asarray(instance_id)
    sup = np.asarray(raw_support, bool)
    if ids.shape != sup.shape or ids.ndim != 2:
        raise ValueError("instance/support arrays must share a 2D shape")
    h, w = ids.shape
    band = max(2, int(round(w * public.POLICY["edge_band_fraction"])))
    obj = (ids == object_id) & sup
    denom_l = max(1, int(sup[:, :band].sum()))
    denom_r = max(1, int(sup[:, -band:].sum()))
    lf = float(obj[:, :band].sum() / denom_l)
    rf = float(obj[:, -band:].sum() / denom_r)
    th = public.POLICY["edge_object_fraction_min"]
    return {
        "band_px": band,
        "left_fraction": lf,
        "right_fraction": rf,
        "touch_left": lf >= th,
        "touch_right": rf >= th,
    }


def choose_next(current_yaw_deg: float, calibration: dict, instance_id: np.ndarray,
                raw_support: np.ndarray, map_xyz_h: np.ndarray,
                visited_yaws_deg: list[float]) -> dict:
    ev = edge_evidence(instance_id, raw_support, public.OBJECT_ID)
    y = map_yaws_deg(map_xyz_h)
    q = public.POLICY["map_extent_quantile"]
    lo, hi = float(np.quantile(y, q)), float(np.quantile(y, 1-q))
    half = float(calibration["nominal_core_fov_deg"]) / 2.0
    step = public.POLICY["step_deg"]
    seen = np.asarray(visited_yaws_deg, float)
    candidates = []
    for side, touch in ((-1, ev["touch_left"]), (1, ev["touch_right"])):
        yaw = float(current_yaw_deg + side*step)
        if not touch or yaw < public.POLICY["yaw_min_deg"]-1e-9 or yaw > public.POLICY["yaw_max_deg"]+1e-9:
            continue
        if np.any(np.isclose(seen, yaw, atol=1e-9)):
            continue
        wl, wh = yaw-half, yaw+half
        overlap = max(0.0, min(wh, hi)-max(wl, lo))
        new_deg = max(0.0, lo-wl) if side < 0 else max(0.0, wh-hi)
        if overlap + 1e-12 < public.POLICY["minimum_overlap_deg"]:
            continue
        candidates.append({
            "yaw_deg": yaw,
            "side": "left" if side < 0 else "right",
            "overlap_deg": overlap,
            "predicted_new_deg": new_deg,
        })
    candidates.sort(key=lambda c: (-c["predicted_new_deg"], abs(c["yaw_deg"]-current_yaw_deg), c["yaw_deg"]))
    best = candidates[0] if candidates else None
    stop = best is None or best["predicted_new_deg"] < public.POLICY["minimum_predicted_new_deg"]
    return {
        "current_yaw_deg": float(current_yaw_deg),
        "map_yaw_extent_deg": [lo, hi],
        "core_half_angle_deg": half,
        "edge": ev,
        "candidates": candidates,
        "stop": bool(stop),
        "reason": "no_frontier" if stop else "continue",
        "next_yaw_deg": None if stop else float(best["yaw_deg"]),
        "selected": None if stop else best,
    }


def self_test() -> None:
    n = 128
    sup = np.ones((n, n), bool)
    c = {"nominal_core_fov_deg": 12.0}
    def xyz_for(lo: float, hi: float) -> np.ndarray:
        yaw = np.radians(np.linspace(lo, hi, 2000))
        return np.c_[2*np.sin(yaw), np.zeros_like(yaw), -2*np.cos(yaw)]
    # Right-only frontier in the current mask.
    ids_r = np.full((n, n), public.OBJECT_ID, np.int32)
    ids_r[:, :12] = public.BACKGROUND_ID
    r = choose_next(0, c, ids_r, sup, xyz_for(-4, 6), [0])
    if r["next_yaw_deg"] != 5.0:
        raise AssertionError("right-only frontier must choose +5")
    # Left-only mirror.
    ids_l = np.full((n, n), public.OBJECT_ID, np.int32)
    ids_l[:, -12:] = public.BACKGROUND_ID
    l = choose_next(0, c, ids_l, sup, xyz_for(-6, 4), [0])
    if l["next_yaw_deg"] != -5.0:
        raise AssertionError("left-only frontier must choose -5")
    # Resolved right boundary should stop when the opposite candidate is a revisit.
    ids_stop = np.full((n, n), public.OBJECT_ID, np.int32)
    ids_stop[:, -12:] = public.BACKGROUND_ID
    d = choose_next(20, c, ids_stop, sup, xyz_for(-4, 22), [0, 5, 10, 15, 20])
    if not d["stop"]:
        raise AssertionError("resolved frontier should stop")
    print("[fsg4-policy] PASS mirrored_frontiers=true resolved_frontier_stops=true")


if __name__ == "__main__":
    self_test()
