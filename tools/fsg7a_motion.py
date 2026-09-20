"""Truth-free moving-head coordinate utilities for FSG7a."""
from __future__ import annotations
import numpy as np
import fsg7a_public as public

def points_ht_to_h0(xyz_ht: np.ndarray, translation_h0_m) -> np.ndarray:
    return np.asarray(xyz_ht,float) + np.asarray(translation_h0_m,float).reshape(1,3)

def points_h0_to_ht(xyz_h0: np.ndarray, translation_h0_m) -> np.ndarray:
    return np.asarray(xyz_h0,float) - np.asarray(translation_h0_m,float).reshape(1,3)

def head_origin_world(translation_h0_m) -> np.ndarray:
    from fsg_geometry import HEAD_ORIGIN_W, HEAD_R_WH
    t=np.asarray(translation_h0_m,float).reshape(3)
    return np.asarray(HEAD_ORIGIN_W,float) + t @ np.asarray(HEAD_R_WH,float).T

def make_view_calibration(profile:str, fixture:str, step:int) -> dict:
    from fsg_geometry import make_calibration
    v=public.view(fixture,step); yaw,pitch=v["gaze_yaw_pitch_deg"]; t=v["head_translation_h0_m"]
    c=make_calibration(profile,yaw,pitch,public.VERGENCE_DISTANCE_M,head_origin_w=head_origin_world(t))
    c["initial_map_frame"]="H0"
    c["head_translation_h0_m"]=list(t)
    c["view_role"]=v["role"]
    return c

def self_test() -> None:
    rng=np.random.default_rng(7); p=rng.normal(size=(50,3)); t=np.array([.45,-.03,.02])
    q=points_h0_to_ht(p,t); r=points_ht_to_h0(q,t)
    if not np.allclose(p,r,atol=1e-14): raise AssertionError("H0/Ht translation round-trip")
    # Omitting transport must be a large, fail-capable error for the prescribed motion.
    err=np.median(np.linalg.norm(q-p,axis=1))
    if not np.isclose(err,np.linalg.norm(t),atol=1e-12): raise AssertionError("moving-frame negative is not measurable")
    for f in public.FIXTURES:
        if np.linalg.norm(public.view(f,0)["head_translation_h0_m"])!=0: raise AssertionError("seed head must be H0")
        if not np.isclose(abs(public.view(f,1)["head_translation_h0_m"][0]),.45): raise AssertionError("reveal translation drifted")
    print("[fsg7a-motion] PASS h0_ht_roundtrip=true moving_frame_negative_m=%.3f"%err)

if __name__=="__main__": self_test()
