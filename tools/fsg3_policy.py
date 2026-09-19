"""Truth-free horizontal frontier policy for FSG3 Increment 3.

Inputs are only the persistent RGB-D map, the current rectified oracle instance
mask, calibration and fixation history. No scene geometry or evaluation data.
"""
from __future__ import annotations
import math
import numpy as np
import fsg3_public as public

def map_yaws_deg(xyz_h: np.ndarray) -> np.ndarray:
    x = np.asarray(xyz_h, float).reshape(-1,3)
    good = np.isfinite(x).all(1) & (x[:,2] < -1e-6)
    if good.sum() < 100:
        raise ValueError("too few finite forward map points for policy")
    return np.degrees(np.arctan2(x[good,0], -x[good,2]))

def edge_evidence(instance_id: np.ndarray, raw_support: np.ndarray, object_id: int) -> dict:
    ids = np.asarray(instance_id)
    sup = np.asarray(raw_support, bool)
    if ids.shape != sup.shape or ids.ndim != 2:
        raise ValueError("instance/support arrays must share a 2D shape")
    h,w = ids.shape
    band = max(2, int(round(w * public.POLICY["edge_band_fraction"])))
    obj = (ids == object_id) & sup
    denom_l = max(1, int(sup[:,:band].sum())); denom_r = max(1, int(sup[:,-band:].sum()))
    lf = float(obj[:,:band].sum()/denom_l); rf = float(obj[:,-band:].sum()/denom_r)
    th = public.POLICY["edge_object_fraction_min"]
    return {"band_px":band,"left_fraction":lf,"right_fraction":rf,
            "touch_left":lf>=th,"touch_right":rf>=th}

def choose_next(current_yaw_deg: float, calibration: dict, instance_id: np.ndarray,
                raw_support: np.ndarray, map_xyz_h: np.ndarray,
                visited_yaws_deg: list[float]) -> dict:
    ev = edge_evidence(instance_id, raw_support, public.OBJECT_ID)
    y = map_yaws_deg(map_xyz_h)
    q = public.POLICY["map_extent_quantile"]
    lo,hi = (float(np.quantile(y,q)), float(np.quantile(y,1-q)))
    half = float(calibration["nominal_core_fov_deg"]) / 2.0
    step = public.POLICY["step_deg"]
    seen = np.asarray(visited_yaws_deg, float)
    candidates=[]
    for side, touch in ((-1,ev["touch_left"]),(1,ev["touch_right"])):
        yaw = float(current_yaw_deg + side*step)
        if not touch or yaw < public.POLICY["yaw_min_deg"]-1e-9 or yaw > public.POLICY["yaw_max_deg"]+1e-9:
            continue
        if np.any(np.isclose(seen,yaw,atol=1e-9)):
            continue
        wl,wh = yaw-half, yaw+half
        overlap = max(0.0, min(wh,hi)-max(wl,lo))
        new_deg = max(0.0, lo-wl) if side < 0 else max(0.0, wh-hi)
        if overlap + 1e-12 < public.POLICY["minimum_overlap_deg"]:
            continue
        candidates.append({"yaw_deg":yaw,"side":"left" if side<0 else "right",
                           "overlap_deg":overlap,"predicted_new_deg":new_deg})
    candidates.sort(key=lambda c:(-c["predicted_new_deg"], abs(c["yaw_deg"]-current_yaw_deg), c["yaw_deg"]))
    best = candidates[0] if candidates else None
    stop = best is None or best["predicted_new_deg"] < public.POLICY["minimum_predicted_new_deg"]
    return {"current_yaw_deg":float(current_yaw_deg),"map_yaw_extent_deg":[lo,hi],
            "core_half_angle_deg":half,"edge":ev,"candidates":candidates,
            "stop":bool(stop),"reason":"no_frontier" if stop else "continue",
            "next_yaw_deg":None if stop else float(best["yaw_deg"]),
            "selected":None if stop else best}

def self_test() -> None:
    n=128; ids=np.full((n,n),71,np.int32); sup=np.ones((n,n),bool)
    c={"nominal_core_fov_deg":12.0}
    def xyz_for(lo,hi):
        yaw=np.radians(np.linspace(lo,hi,2000)); z=-2*np.cos(yaw); x=2*np.sin(yaw)
        return np.c_[x,np.zeros_like(x),z]
    # Both image edges say the object continues. Map extent decides the direction.
    a=choose_next(-2,c,ids,sup,xyz_for(-10,4),[-7,-2])
    if a["next_yaw_deg"] != 3.0: raise AssertionError("map-left-heavy state should choose right frontier")
    b=choose_next(2,c,ids,sup,xyz_for(-4,10),[7,2])
    if b["next_yaw_deg"] != -3.0: raise AssertionError("map-right-heavy state should choose left frontier")
    # If the right edge no longer contains the object and left expansion is already covered, stop.
    ids2=ids.copy();ids2[:,-8:]=0
    d=choose_next(13,c,ids2,sup,xyz_for(-10,15),[-7,-2,3,8,13])
    if not d["stop"]: raise AssertionError("resolved frontier should stop")
    print("[fsg3-policy] PASS map_state_changes_direction=true resolved_frontier_stops=true")

if __name__ == "__main__":
    self_test()
