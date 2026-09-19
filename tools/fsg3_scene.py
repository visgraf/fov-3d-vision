"""FSG3 Increment-3 fixture: one wide finite tilted surface and a background.

This module contains evaluation geometry and MUST NOT be imported by the active
host loop or frontier policy. It is used by Blender acquisition and by the
post-hoc evaluator only.
"""
from __future__ import annotations
import hashlib, json, math
import numpy as np
from fsg_scene import quad, texture
import fsg3_public as public

OBJECT_CENTRE = np.array([0.08, 0.0, -2.10], dtype=float)
TILT_DEG = 10.0
OBJECT_WIDTH_M = 0.95
OBJECT_HEIGHT_M = 0.32
BACKGROUND_Z_M = -3.50
BACKGROUND_SIZE_M = (4.0, 2.8)
TRUTH_GRID_WH = (238, 80)
TRUTH_COVER_RADIUS_M = 0.015

TRUTH_SPEC = {
    "public_spec_sha256": public.public_digest(),
    "object_centre_h_m": OBJECT_CENTRE.tolist(),
    "object_size_m": [OBJECT_WIDTH_M, OBJECT_HEIGHT_M],
    "object_tilt_deg": TILT_DEG,
    "background_z_h_m": BACKGROUND_Z_M,
    "truth_grid_wh": list(TRUTH_GRID_WH),
    "truth_cover_radius_m": TRUTH_COVER_RADIUS_M,
}

def object_axes() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    a = math.radians(TILT_DEG)
    right = np.array([math.cos(a), 0.0, math.sin(a)], dtype=float)
    up = np.array([0.0, 1.0, 0.0], dtype=float)
    normal = np.cross(right, up)
    normal /= np.linalg.norm(normal)
    return right, up, normal

def scene_objects(_: str) -> list[dict]:
    r, u, _ = object_axes()
    return [
        quad(OBJECT_CENTRE, r, u, OBJECT_WIDTH_M, OBJECT_HEIGHT_M,
             public.OBJECT_ID, "fsg3_object"),
        quad([0.0, 0.0, BACKGROUND_Z_M], [1,0,0], [0,1,0],
             BACKGROUND_SIZE_M[0], BACKGROUND_SIZE_M[1],
             public.BACKGROUND_ID, "fsg3_background"),
    ]

def scene_texture(instance: int, size: int = 512) -> np.ndarray:
    return texture(int(instance) + 70000, size)

def truth_digest() -> str:
    return hashlib.sha256(json.dumps(TRUTH_SPEC, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def validate_mesh(mesh: dict) -> None:
    wanted = scene_objects("fixture")
    triangles = mesh["triangles_h"]
    ids = mesh["instance_ids"]
    if triangles.shape != (4,3,3) or ids.shape != (4,):
        raise ValueError("unexpected FSG3 mesh size")
    if set(ids.tolist()) != {public.OBJECT_ID, public.BACKGROUND_ID}:
        raise ValueError("unexpected FSG3 object IDs")
    for obj in wanted:
        exp = np.asarray(obj["vertices_h"], float)
        got = triangles[ids == obj["instance_id"]]
        if len(got) != 2:
            raise ValueError("two triangles required per quad")
        d = np.linalg.norm(got[:,:,None,:] - exp[None,None,:,:], axis=-1)
        if np.max(np.min(d, axis=-1)) > 2e-5:
            raise ValueError("exported Blender mesh disagrees with FSG3 specification")

def surface_coordinates(xyz: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    r, u, n = object_axes()
    q = np.asarray(xyz, float) - OBJECT_CENTRE
    return q @ r, q @ u, q @ n

def angular_span_deg() -> tuple[float, float]:
    r, _, _ = object_axes()
    a = OBJECT_CENTRE - 0.5 * OBJECT_WIDTH_M * r
    b = OBJECT_CENTRE + 0.5 * OBJECT_WIDTH_M * r
    return tuple(float(np.degrees(np.arctan2(x[0], -x[2]))) for x in (a,b))

def self_test() -> None:
    r,u,n = object_axes()
    if not np.allclose([np.linalg.norm(r), np.linalg.norm(u), np.linalg.norm(n)], [1,1,1], atol=1e-12):
        raise AssertionError("axes not unit")
    if max(abs(r@u), abs(r@n), abs(u@n)) > 1e-12:
        raise AssertionError("axes not orthogonal")
    lo, hi = angular_span_deg()
    seed = public.SEED_GAZE_YAW_DEG
    half = 6.0
    # The seed must contain the left boundary but leave a right frontier outside its foveal core.
    if not (seed-half < lo < seed+half < hi):
        raise AssertionError(f"seed/frontier geometry wrong: object=[{lo:.3f},{hi:.3f}] seed=[{seed-half:.3f},{seed+half:.3f}]")
    # Five 5-degree centres from the seed should be enough to see beyond the right boundary.
    fifth = seed + 4*public.POLICY["step_deg"]
    if not (fifth-half < hi < fifth+half):
        raise AssertionError("designed five-look traversal does not bracket right object edge")
    print(f"[fsg3-scene] PASS angular_span=[{lo:.3f},{hi:.3f}] seed={seed:.1f} five_looks_reach=true")

if __name__ == "__main__":
    self_test()
