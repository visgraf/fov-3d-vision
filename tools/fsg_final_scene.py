"""FSG1g final prospective validation specification.

Fresh geometry, fresh textures, fresh seeds.  The candidate is the *one-step control*
from FSG1f: fixed HDR encoding, original SGBM, exactly one original photometric
update, and the original validity predicate.  No endpoint/footprint veto is used.

NumPy + standard library only so Blender may import it.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
from fsg_geometry import make_calibration
from fsg_scene import quad, texture

SPEC_ID = "FSG1g-final-one-step-validation-v1"
CASES = ("phase_00", "phase_25", "phase_50", "phase_75", "occluder_left", "occluder_right")
CASE_GAZE = {name: (0.0, 0.0) for name in CASES}
SEEDS = (101, 149)
DEFAULT_SPP = {"small": 64, "full": 256}
TEXTURE_OFFSET = 40000
# Full-profile target disparities.  The physical plane ranges are derived from
# the frozen camera calibration, not fitted to image results.
PHASE_DISPARITY_PX = {
    "phase_00": 22.00,
    "phase_25": 22.25,
    "phase_50": 22.50,
    "phase_75": 22.75,
}
PHASE_INSTANCE = {"phase_00": 11, "phase_25": 12, "phase_50": 13, "phase_75": 14}


def _full_focal_baseline() -> tuple[float, float]:
    c = make_calibration("full", 0.0, 0.0)
    f = float(c["eyes"][0]["K"][0][0])
    a = np.asarray(c["eyes"][0]["centre_h_m"], np.float64)
    b = np.asarray(c["eyes"][1]["centre_h_m"], np.float64)
    baseline = float(np.linalg.norm(a - b))
    # Fail loudly if the repository camera prescription has drifted from the
    # FSG1 instrument that produced the development measurements.
    if abs(f - 1217.839) > 0.01 or abs(baseline - 0.063) > 1e-9:
        raise ValueError(f"FSG1 calibration drift: focal={f} baseline={baseline}")
    return f, baseline


def phase_depth_m(name: str) -> float:
    f, baseline = _full_focal_baseline()
    return f * baseline / PHASE_DISPARITY_PX[name]


SPEC = {
    "id": SPEC_ID,
    "candidate": "FSG1g-HDR-SGBM-one-original-update-original-validity-v1",
    "cases": list(CASES),
    "phase_target_disparity_px": dict(PHASE_DISPARITY_PX),
    "phase_plane_size_m": [3.4, 3.4],
    "occluder_left": {
        "background_z_h_m": -3.05,
        "foreground_z_h_m": -1.85,
        "foreground_x_interval_m": [-1.00, 0.35],
        "foreground_height_m": 2.2,
        "background_size_m": [4.6, 4.2],
        "foreground_instance": 21,
        "background_instance": 22,
    },
    "occluder_right": {
        "background_z_h_m": -3.15,
        "foreground_z_h_m": -1.95,
        "foreground_x_interval_m": [-0.35, 1.00],
        "foreground_height_m": 2.2,
        "background_size_m": [4.6, 4.2],
        "foreground_instance": 31,
        "background_instance": 32,
    },
    "texture": "fsg_scene.texture(instance_id + 40000); shared between eyes and seeds",
    "seed_schedule": {"small": [101], "full": [101, 149]},
    "spp": DEFAULT_SPP,
    "vergence_distance_m": 2.0,
    "interior_targets": {"coverage_min": 0.90, "median_range_max": 0.01, "p95_range_max": 0.03},
    "boundary_targets": {"minimum_accepted_points": 100, "median_range_max": 0.01, "p95_range_max": 0.03},
    "occlusion_core_erosion_px": {"small": 1, "full": 2},
    "occlusion_min_raw_pixels": {"small": 64, "full": 256},
    "occlusion_min_core_pixels": {"small": 32, "full": 128},
    "occlusion_max_core_accepted": 0,
    "no_hole_fill": True,
    "fixed_head_frame": True,
    "oracle_instance_segmentation": True,
}


def spec_digest() -> str:
    return hashlib.sha256(json.dumps(SPEC, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def final_objects(name: str) -> list[dict]:
    if name in PHASE_DISPARITY_PX:
        z = -phase_depth_m(name)
        return [quad([0.0, 0.0, z], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0],
                     3.4, 3.4, PHASE_INSTANCE[name], name)]
    if name in ("occluder_left", "occluder_right"):
        s = SPEC[name]
        x0, x1 = s["foreground_x_interval_m"]
        return [
            quad([0.0, 0.0, s["background_z_h_m"]], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0],
                 s["background_size_m"][0], s["background_size_m"][1], s["background_instance"], name + "_background"),
            quad([(x0+x1)/2.0, 0.0, s["foreground_z_h_m"]], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0],
                 x1-x0, s["foreground_height_m"], s["foreground_instance"], name + "_foreground"),
        ]
    raise ValueError("unknown FSG1g case: " + str(name))


def final_texture(instance: int, size: int = 512) -> np.ndarray:
    return texture(int(instance) + TEXTURE_OFFSET, size)


def validate_mesh(name: str, mesh: dict) -> None:
    wanted = final_objects(name)
    triangles = mesh["triangles_h"]
    ids = mesh["instance_ids"]
    if triangles.shape != (2*len(wanted), 3, 3) or ids.shape != (2*len(wanted),):
        raise ValueError("unexpected final-validation mesh size")
    if set(ids.tolist()) != {obj["instance_id"] for obj in wanted}:
        raise ValueError("unexpected final-validation object identity")
    for obj in wanted:
        exported = triangles[ids == obj["instance_id"]]
        if len(exported) != 2:
            raise ValueError("expected two triangles per validation quad")
        corners = np.asarray(obj["vertices_h"])
        distance = np.linalg.norm(exported[:,:,None,:] - corners[None,None,:,:], axis=-1)
        nearest = np.argmin(distance, axis=-1)
        if np.max(np.min(distance, axis=-1)) > 2e-5:
            raise ValueError("exported Blender mesh disagrees with frozen FSG1g specification")
        actual = {tuple(sorted(row.tolist())) for row in nearest}
        if actual not in ({(0,1,2),(0,2,3)}, {(0,1,3),(1,2,3)}):
            raise ValueError("exported triangles do not cover the prescribed quad exactly once")


def self_test() -> None:
    f,b = _full_focal_baseline()
    for name,d in PHASE_DISPARITY_PX.items():
        z = phase_depth_m(name)
        got = f*b/z
        if abs(got-d) > 1e-9:
            raise AssertionError(f"phase construction failed for {name}: {got} != {d}")
        if len(final_objects(name)) != 1:
            raise AssertionError("phase case must contain one plane")
    for name in ("occluder_left","occluder_right"):
        if len(final_objects(name)) != 2:
            raise AssertionError("occluder must contain foreground and background")
    print("[fsg-final-scene] PASS cases=6 phases=4 mirrored_occluders=2")


if __name__ == "__main__":
    self_test()
