"""FSG2 Increment-2 scene: one finite tilted object, two prescribed overlapping fixations.

NumPy + standard library only so Blender may import it.  The head frame is the
persistent map frame.  Geometry and textures are identical between fixations;
only gaze and independent Cycles noise change.
"""
from __future__ import annotations
import hashlib, json, math
import numpy as np
from fsg_scene import quad, texture

SPEC_ID = "FSG2-two-overlapping-patches-v1"
CASES = ("fix_left", "fix_right")
CASE_GAZE = {"fix_left": (-3.0, 0.0), "fix_right": (3.0, 0.0)}
DEFAULT_SPP = {"small": 64, "full": 256}
SEED = 211
OBJECT_ID = 61
BACKGROUND_ID = 62
OBJECT_CENTRE = np.array([0.0, 0.0, -2.05])
TILT_DEG = 12.0
OBJECT_WIDTH_M = 0.68
OBJECT_HEIGHT_M = 0.48
BACKGROUND_Z_M = -3.4
BACKGROUND_SIZE_M = (3.5, 2.8)

# Surface-map parameters are declared prospectively here and used by the host tool.
FUSION = {
    "association_radius_m": 0.012,
    "hash_cell_m": 0.012,
    "truth_cover_radius_m": 0.015,
    "truth_grid_wh": [170, 120],
}
TARGETS = {
    "patch_object_coverage_min": 0.90,
    "minimum_matched_points": 5000,
    "minimum_second_patch_new_fraction": 0.15,
    "overlap_median_distance_max_m": 0.010,
    "overlap_p95_distance_max_m": 0.025,
    "map_point_plane_median_max_m": 0.010,
    "map_point_plane_p95_max_m": 0.030,
    "fused_truth_coverage_min": 0.70,
    "fused_truth_coverage_gain_min": 0.12,
}
SPEC = {
    "id": SPEC_ID,
    "cases": list(CASES),
    "case_gaze_yaw_pitch_deg": {k: list(v) for k,v in CASE_GAZE.items()},
    "seed": SEED,
    "spp": DEFAULT_SPP,
    "object_id": OBJECT_ID,
    "background_id": BACKGROUND_ID,
    "object_centre_h_m": OBJECT_CENTRE.tolist(),
    "object_size_m": [OBJECT_WIDTH_M, OBJECT_HEIGHT_M],
    "object_tilt_deg": TILT_DEG,
    "background_z_h_m": BACKGROUND_Z_M,
    "fusion": FUSION,
    "targets": TARGETS,
    "fixed_head_frame": True,
    "oracle_instance_segmentation": True,
    "instrument": "FSG1-HDR-SGBM-one-original-update-original-validity-v1",
    "no_icp": True,
    "no_hole_fill": True,
    "no_policy": True,
}

def object_axes() -> tuple[np.ndarray,np.ndarray,np.ndarray]:
    a = math.radians(TILT_DEG)
    # Rotate the local right axis about head +Y.  Up remains +Y.
    right = np.array([math.cos(a), 0.0, math.sin(a)], dtype=float)
    up = np.array([0.0, 1.0, 0.0], dtype=float)
    normal = np.cross(right, up)
    normal /= np.linalg.norm(normal)
    return right, up, normal

def scene_objects(_: str) -> list[dict]:
    r,u,_ = object_axes()
    return [
        quad(OBJECT_CENTRE, r, u, OBJECT_WIDTH_M, OBJECT_HEIGHT_M, OBJECT_ID, "fsg2_object"),
        quad([0.0,0.0,BACKGROUND_Z_M], [1,0,0], [0,1,0], BACKGROUND_SIZE_M[0], BACKGROUND_SIZE_M[1], BACKGROUND_ID, "fsg2_background"),
    ]

def scene_texture(instance: int, size: int = 512) -> np.ndarray:
    # Distinct from all FSG1 validation texture IDs while deterministic/shared across eyes/fixations.
    return texture(int(instance) + 50000, size)

def spec_digest() -> str:
    return hashlib.sha256(json.dumps(SPEC, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def validate_mesh(mesh: dict) -> None:
    wanted = scene_objects("fix_left")
    triangles = mesh["triangles_h"]; ids = mesh["instance_ids"]
    if triangles.shape != (4,3,3) or ids.shape != (4,):
        raise ValueError("unexpected FSG2 mesh size")
    if set(ids.tolist()) != {OBJECT_ID, BACKGROUND_ID}:
        raise ValueError("unexpected FSG2 object IDs")
    for obj in wanted:
        exp = np.asarray(obj["vertices_h"], float)
        got = triangles[ids == obj["instance_id"]]
        if len(got) != 2: raise ValueError("two triangles required per quad")
        d = np.linalg.norm(got[:,:,None,:]-exp[None,None,:,:],axis=-1)
        if np.max(np.min(d,axis=-1)) > 2e-5:
            raise ValueError("exported Blender mesh disagrees with FSG2 specification")

def surface_coordinates(xyz: np.ndarray) -> tuple[np.ndarray,np.ndarray,np.ndarray]:
    r,u,n = object_axes(); q=np.asarray(xyz,float)-OBJECT_CENTRE
    return q@r, q@u, q@n

def self_test() -> None:
    r,u,n=object_axes()
    if not np.allclose([np.linalg.norm(r),np.linalg.norm(u),np.linalg.norm(n)],[1,1,1],atol=1e-12):
        raise AssertionError("axes not unit")
    if abs(r@u)>1e-12 or abs(r@n)>1e-12 or abs(u@n)>1e-12:
        raise AssertionError("axes not orthogonal")
    for case in CASES:
        objs=scene_objects(case)
        if [x["instance_id"] for x in objs] != [OBJECT_ID,BACKGROUND_ID]:
            raise AssertionError("instance IDs drift")
    # The two 12-degree foveal cores separated by 6 degrees should overlap substantially.
    if abs(CASE_GAZE["fix_right"][0]-CASE_GAZE["fix_left"][0]) >= 12.0:
        raise AssertionError("prescribed fixations do not overlap")
    print("[fsg2-scene] PASS cases=2 object=61 overlap_prescribed=true")

if __name__ == "__main__": self_test()
