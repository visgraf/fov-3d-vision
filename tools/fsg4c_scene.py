"""Fresh evaluator-only fixtures for the FSG4c efficiency validation.

The two opaque planar fixtures differ from FSG4a/b in placement, extent, depth,
tilt and procedural texture tag.  Their geometry is visible to Blender acquisition
and post-hoc evaluation only; the active host/policy does not import this module.
"""
from __future__ import annotations
import hashlib
import json
import math
import numpy as np
from fsg_scene import quad, texture
import fsg4c_public as public

BACKGROUND_Z_M = -3.60
BACKGROUND_SIZE_M = (4.2, 2.9)
TRUTH_GRID_WH = (256, 84)
TRUTH_COVER_RADIUS_M = 0.015

FIXTURE = {
    # Fresh left-frontier case: intended to require the fifth -20 deg look.
    "case_c": {"centre_x_m": -0.38, "z_m": -2.18, "width_m": 1.00, "height_m": 0.34,
               "tilt_deg": 9.0, "texture_tag": 7},
    # Fresh right-frontier case with different depth/extent/tilt/texture.
    "case_d": {"centre_x_m": +0.34, "z_m": -2.05, "width_m": 1.02, "height_m": 0.30,
               "tilt_deg": 8.0, "texture_tag": 11},
}


def spec(fixture: str) -> dict:
    if fixture not in public.FIXTURES:
        raise ValueError(f"unknown fixture {fixture}")
    return FIXTURE[fixture]


def object_centre(fixture: str) -> np.ndarray:
    s=spec(fixture)
    return np.array([s["centre_x_m"], 0.0, s["z_m"]], dtype=float)


def object_axes(fixture: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    a = math.radians(float(spec(fixture)["tilt_deg"]))
    right = np.array([math.cos(a), 0.0, math.sin(a)], dtype=float)
    up = np.array([0.0, 1.0, 0.0], dtype=float)
    normal = np.cross(right, up); normal /= np.linalg.norm(normal)
    return right, up, normal


def scene_objects(fixture: str) -> list[dict]:
    s=spec(fixture); r,u,_=object_axes(fixture)
    return [
        quad(object_centre(fixture), r, u, s["width_m"], s["height_m"], public.OBJECT_ID, f"fsg4c_{fixture}_object"),
        quad([0.0,0.0,BACKGROUND_Z_M],[1,0,0],[0,1,0],BACKGROUND_SIZE_M[0],BACKGROUND_SIZE_M[1],public.BACKGROUND_ID,f"fsg4c_{fixture}_background"),
    ]


def scene_texture(fixture: str, instance: int, size: int = 512) -> np.ndarray:
    tag=int(spec(fixture)["texture_tag"])
    return texture(int(instance)+93000+137*tag,size)


def truth_spec(fixture: str) -> dict:
    s=spec(fixture)
    return {
        "id":f"FSG4c-{fixture}-truth-v1","public_spec_sha256":public.public_digest(),"fixture":fixture,
        "object_centre_h_m":object_centre(fixture).tolist(),"object_size_m":[s["width_m"],s["height_m"]],
        "object_tilt_deg":s["tilt_deg"],"background_z_h_m":BACKGROUND_Z_M,
        "truth_grid_wh":list(TRUTH_GRID_WH),"truth_cover_radius_m":TRUTH_COVER_RADIUS_M,"texture_tag":s["texture_tag"],
    }


def truth_digest(fixture: str) -> str:
    return hashlib.sha256(json.dumps(truth_spec(fixture),sort_keys=True,separators=(",",":")).encode()).hexdigest()


def validate_mesh(fixture: str, mesh: dict) -> None:
    wanted=scene_objects(fixture);triangles=mesh["triangles_h"];ids=mesh["instance_ids"]
    if triangles.shape!=(4,3,3) or ids.shape!=(4,): raise ValueError("unexpected FSG4c mesh size")
    if set(ids.tolist())!={public.OBJECT_ID,public.BACKGROUND_ID}: raise ValueError("unexpected FSG4c object IDs")
    for obj in wanted:
        exp=np.asarray(obj["vertices_h"],float);got=triangles[ids==obj["instance_id"]]
        if len(got)!=2: raise ValueError("two triangles required per quad")
        d=np.linalg.norm(got[:,:,None,:]-exp[None,None,:,:],axis=-1)
        if np.max(np.min(d,axis=-1))>2e-5: raise ValueError("exported Blender mesh disagrees with FSG4c specification")


def surface_coordinates(fixture: str, xyz: np.ndarray) -> tuple[np.ndarray,np.ndarray,np.ndarray]:
    r,u,n=object_axes(fixture);q=np.asarray(xyz,float)-object_centre(fixture)
    return q@r,q@u,q@n


def angular_span_deg(fixture: str) -> tuple[float,float]:
    s=spec(fixture);r,_,_=object_axes(fixture);c=object_centre(fixture)
    a=c-0.5*s["width_m"]*r;b=c+0.5*s["width_m"]*r
    return tuple(float(np.degrees(np.arctan2(x[0],-x[2]))) for x in (a,b))


def _interval_coverage(span:tuple[float,float],yaws:list[float],half:float=6.0)->float:
    lo,hi=span;ints=[]
    for y in yaws:
        a,b=max(lo,y-half),min(hi,y+half)
        if b>a:ints.append((a,b))
    if not ints:return 0.0
    ints.sort();s,e=ints[0];total=0.0
    for a,b in ints[1:]:
        if a<=e:e=max(e,b)
        else:total+=e-s;s,e=a,b
    total+=e-s
    return total/(hi-lo)


def truth_points(fixture: str) -> np.ndarray:
    s=spec(fixture);nx,ny=TRUTH_GRID_WH
    xs=np.linspace(-s["width_m"]/2,s["width_m"]/2,nx);ys=np.linspace(-s["height_m"]/2,s["height_m"]/2,ny)
    X,Y=np.meshgrid(xs,ys);r,u,_=object_axes(fixture);c=object_centre(fixture)
    return (c+X[...,None]*r+Y[...,None]*u).reshape(-1,3)


def self_test() -> None:
    spans={f:angular_span_deg(f) for f in public.FIXTURES}
    c,d=spans["case_c"],spans["case_d"]
    # Seed 0 must expose opposite unresolved frontiers, not an ambiguous two-sided one.
    if not (c[0] < -20.0 and 2.0 < c[1] < 5.0): raise AssertionError(f"case_c angular design drifted: {c}")
    if not (-5.0 < d[0] < -2.0 and d[1] > 22.0): raise AssertionError(f"case_d angular design drifted: {d}")
    scan=list(public.SCAN_YAWS_DEG)
    ideal={f:_interval_coverage(spans[f],scan) for f in public.FIXTURES}
    if not (0.70 < ideal["case_c"] < 0.85 and 0.70 < ideal["case_d"] < 0.85):
        raise AssertionError(f"fixed scan no longer leaves substantial unresolved surface: {ideal}")
    left=_interval_coverage(c,[0,-5,-10,-15,-20]);right=_interval_coverage(d,[0,5,10,15,20])
    if left < .99 or right < .99: raise AssertionError("five-look directional traces no longer span fixtures")
    print(f"[fsg4c-scene] PASS case_c=[{c[0]:.3f},{c[1]:.3f}] scan_ideal={ideal['case_c']:.3f} case_d=[{d[0]:.3f},{d[1]:.3f}] scan_ideal={ideal['case_d']:.3f}")

if __name__=="__main__": self_test()
