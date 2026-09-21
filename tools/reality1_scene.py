"""Evaluator-side scene description for Reality Check 1.

The target is a shallow, irregular cloth/poster-like surface in a small tabletop
still life.  It is intentionally more ordinary than the calibration ribbons:
non-constant curvature, mixed spatial frequencies, a broad low-contrast area,
and unrelated clutter around it.  It is not an adversarial torture test.

Prediction-side code must not import this module.
"""
from __future__ import annotations
import hashlib
import json
import math
import numpy as np
from fsg_scene import quad
import reality1_public as public

TARGET_W_M = 0.90
TARGET_H_M = 0.64
TARGET_CENTRE_Y_M = 0.04
TARGET_BASE_Z_M = -2.12
GRID_NX = 11
GRID_NY = 7
TRUTH_GRID_WH = (181, 129)
TRUTH_COVER_RADIUS_M = 0.020


def _rz(deg: float) -> np.ndarray:
    a = math.radians(float(deg)); c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]], float)

ROLL_DEG = -6.0
R = _rz(ROLL_DEG)


def cloth_local(x: np.ndarray | float, y: np.ndarray | float) -> np.ndarray:
    x = np.asarray(x, float); y = np.asarray(y, float)
    x, y = np.broadcast_arrays(x, y)
    xn = x / TARGET_W_M
    yn = (y - TARGET_CENTRE_Y_M) / TARGET_H_M
    # 7-8 cm total depth range: enough to break planar/cylindrical assumptions,
    # shallow enough to stay first-hit visible from the fixed head.
    dz = (-0.034 * np.sin(2.1 * np.pi * xn + 0.35) * np.cos(1.6 * np.pi * yn - 0.2)
          -0.018 * np.sin(3.0 * np.pi * yn + 0.8)
          +0.010 * xn)
    return np.stack((x, y, TARGET_BASE_Z_M + dz), axis=-1)


def cloth_point(x: np.ndarray | float, y: np.ndarray | float) -> np.ndarray:
    p = cloth_local(x, y)
    # Rotate the whole hanging surface a little in the image plane; this is not a
    # privileged axis-aligned calibration patch.
    return p @ R.T


def _target_quads() -> list[dict]:
    xs = np.linspace(-TARGET_W_M / 2.0, TARGET_W_M / 2.0, GRID_NX)
    ys = np.linspace(TARGET_CENTRE_Y_M - TARGET_H_M / 2.0,
                     TARGET_CENTRE_Y_M + TARGET_H_M / 2.0, GRID_NY)
    out = []
    for j in range(GRID_NY - 1):
        for i in range(GRID_NX - 1):
            x0, x1 = xs[i], xs[i+1]; y0, y1 = ys[j], ys[j+1]
            verts = np.array([cloth_point(x0,y0), cloth_point(x1,y0),
                              cloth_point(x1,y1), cloth_point(x0,y1)], float)
            u0, u1 = i/(GRID_NX-1), (i+1)/(GRID_NX-1)
            v0, v1 = j/(GRID_NY-1), (j+1)/(GRID_NY-1)
            out.append({"name": f"rc1_cloth_{j:02d}_{i:02d}", "vertices_h": verts,
                        "instance_id": public.OBJECT_ID,
                        "uv": np.array([[u0,v0],[u1,v0],[u1,v1],[u0,v1]], float)})
    return out


def scene_objects(_fixture: str = public.FIXTURE) -> list[dict]:
    if _fixture != public.FIXTURE:
        raise ValueError("unknown Reality Check 1 fixture")
    out = _target_quads()
    # Ordinary surroundings.  They are not intended as occluders of the target;
    # they provide unrelated image structure, surfaces and illumination context.
    out += [
        quad([0.0, 0.0, -3.35], [1,0,0], [0,1,0], 4.0, 2.8, 143, "rc1_wall"),
        quad([0.0,-0.58,-2.20], [1,0,0], [0,0,-1], 3.4, 2.2, 142, "rc1_table"),
        quad([-0.92,-0.05,-2.48], [1,0,0], [0,1,0], 0.42, 0.52, 144, "rc1_book_left"),
        quad([+0.96,+0.02,-2.58], [1,0,0], [0,1,0], 0.50, 0.70, 145, "rc1_box_right"),
    ]
    return out


def _smooth_noise(size: int, seed: int, sigma: float) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = rng.normal(size=(size,size))
    fy = np.fft.fftfreq(size)[:,None]; fx = np.fft.rfftfreq(size)[None,:]
    f2 = fx*fx + fy*fy
    a = np.fft.irfft2(np.fft.rfft2(n) * np.exp(-2*np.pi**2*sigma**2*f2), s=n.shape)
    return a / max(float(a.std()), 1e-9)


def target_texture(size: int = 512) -> np.ndarray:
    y, x = np.mgrid[0:size,0:size]
    u = (x + 0.5)/size; v = (y + 0.5)/size
    fine = _smooth_noise(size, 8101, 1.4)
    broad = _smooth_noise(size, 8102, 18.0)
    base = np.empty((size,size,3), np.float32)
    base[:] = np.array([0.54,0.42,0.31], np.float32)
    # Subtle fabric variation, intentionally not the high-contrast random texture
    # used by the calibration fixtures.
    base *= (1.0 + 0.025*fine[...,None] + 0.035*broad[...,None])
    # Broad almost-uniform left panel.
    low = u < 0.36
    mean = np.array([0.52,0.405,0.30], np.float32)
    base[low] = mean + 0.010*fine[low,None]
    # Printed vertical band and simple emblem; ordinary featureful regions, not
    # uniformly rich texture everywhere.
    band = (u > 0.58) & (u < 0.69)
    base[band] = np.array([0.10,0.20,0.28], np.float32) + 0.012*fine[band,None]
    disk = (u-0.80)**2 + (v-0.34)**2 < 0.060**2
    base[disk] = np.array([0.72,0.17,0.12], np.float32)
    # Mild repetitive weave only in a lower strip.
    strip = v > 0.78
    weave = 0.025*np.sin(2*np.pi*18*u)
    base[strip] *= (1.0 + weave[strip,None])
    return np.clip(base, 0.03, 0.95).astype(np.float32)


def scene_texture(_fixture: str, instance: int, size: int = 512) -> np.ndarray:
    if _fixture != public.FIXTURE:
        raise ValueError("unknown Reality Check 1 fixture")
    if int(instance) == public.OBJECT_ID:
        return target_texture(size)
    y, x = np.mgrid[0:size,0:size]; u=(x+.5)/size; v=(y+.5)/size
    n = _smooth_noise(size, 9000+int(instance), 5.0)
    if int(instance) == 142:  # wood-like table
        c = np.stack((0.35+0.06*np.sin(2*np.pi*(7*u+.15*n)),
                      0.22+0.035*np.sin(2*np.pi*(7*u+.15*n)),
                      0.12+0.025*np.sin(2*np.pi*(7*u+.15*n))),axis=-1)
    elif int(instance) == 143:  # quiet wall
        g = 0.60 + 0.012*n
        c = np.stack((g*1.03,g,g*0.96),axis=-1)
    elif int(instance) == 144:
        c = np.zeros((size,size,3),np.float32); c[:] = [0.20,0.31,0.48]
        label=(u>.18)&(u<.82)&(v>.38)&(v<.62); c[label]=[0.78,0.74,0.58]
    else:
        c = np.zeros((size,size,3),np.float32); c[:] = [0.42,0.20,0.14]
        stripe=(u>.48)&(u<.55); c[stripe]=[0.78,0.68,0.42]
    return np.clip(c,0.02,0.95).astype(np.float32)


def truth_points() -> np.ndarray:
    nx, ny = TRUTH_GRID_WH
    xs = np.linspace(-TARGET_W_M/2.0, TARGET_W_M/2.0, nx)
    ys = np.linspace(TARGET_CENTRE_Y_M-TARGET_H_M/2.0,
                     TARGET_CENTRE_Y_M+TARGET_H_M/2.0, ny)
    X,Y=np.meshgrid(xs,ys)
    return cloth_point(X,Y).reshape(-1,3)


def angular_coordinates(xyz_h: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
    p=np.asarray(xyz_h,float).reshape(-1,3)
    yaw=np.degrees(np.arctan2(p[:,0],-p[:,2]))
    pitch=np.degrees(np.arctan2(p[:,1],np.sqrt(p[:,0]**2+p[:,2]**2)))
    return yaw,pitch


def angular_bounds() -> tuple[float,float,float,float]:
    y,p=angular_coordinates(truth_points())
    return float(y.min()),float(y.max()),float(p.min()),float(p.max())


def depth_range_m() -> float:
    p=truth_points(); return float(p[:,2].max()-p[:,2].min())


def truth_spec() -> dict:
    return {"id":"RealityCheck1-tabletop-cloth-truth-v1","public_spec_sha256":public.public_digest(),
            "fixture":public.FIXTURE,"target_wh_m":[TARGET_W_M,TARGET_H_M],
            "target_base_z_m":TARGET_BASE_Z_M,"roll_deg":ROLL_DEG,
            "grid":[GRID_NX,GRID_NY],"truth_grid_wh":list(TRUTH_GRID_WH),
            "truth_cover_radius_m":TRUTH_COVER_RADIUS_M,
            "target_texture":"mixed household print: low-contrast panel + printed band/emblem + mild weave",
            "surroundings":"table, wall, two unrelated foreground-side props; no designed target occlusion"}


def truth_digest() -> str:
    return hashlib.sha256(json.dumps(truth_spec(),sort_keys=True,separators=(",",":")).encode()).hexdigest()


def validate_mesh(mesh: dict) -> None:
    ids=np.asarray(mesh["instance_ids"],np.int32)
    counts={int(i):int((ids==i).sum()) for i in np.unique(ids)}
    expected_target=2*(GRID_NX-1)*(GRID_NY-1)
    if counts.get(public.OBJECT_ID,0)!=expected_target:
        raise ValueError(f"target triangle count {counts.get(public.OBJECT_ID,0)} != {expected_target}")
    if set(counts)!={public.OBJECT_ID,*public.BACKGROUND_IDS}:
        raise ValueError(f"unexpected Reality Check 1 instance IDs: {sorted(counts)}")
    if any(counts.get(i,0)!=2 for i in public.BACKGROUND_IDS):
        raise ValueError("background/clutter quads changed")


def texture_profile() -> dict:
    a=target_texture(256)
    lum=0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
    left=lum[:, :80]
    feat=lum[:, 145:230]
    return {"whole_std":float(lum.std()),"low_panel_std":float(left.std()),
            "feature_region_std":float(feat.std()),"dynamic_range":float(lum.max()-lum.min())}


def self_test() -> dict:
    b=angular_bounds(); d=depth_range_m(); t=texture_profile()
    if not (18.0 < b[1]-b[0] < 30.0 and 12.0 < b[3]-b[2] < 22.0):
        raise AssertionError(f"unexpected target angular extent {b}")
    if d < 0.055:
        raise AssertionError("target accidentally became nearly planar")
    if not (t["low_panel_std"] < 0.055 and t["feature_region_std"] > t["low_panel_std"]*1.5):
        raise AssertionError(f"mixed-texture contract drifted {t}")
    return {"bounds_deg":b,"depth_range_m":d,"texture":t,"target_triangles":2*(GRID_NX-1)*(GRID_NY-1)}

if __name__=="__main__":
    print("[reality1-scene] PASS",json.dumps(self_test(),sort_keys=True))
