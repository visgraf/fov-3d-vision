"""Truth-free public contract for FSG7a moving-head self-occlusion feasibility.

Increment 6 closed the fixed-head 3D-frontier controller.  FSG7a changes one
physical assumption: the binocular rig may translate laterally while the world
and the persistent reconstruction stay in the INITIAL head frame H0.  The
motion is prescribed, not selected by a policy.  The question is whether head
parallax can reveal a surface continuation that is geometrically self-occluded
from both eyes at H0, while the frozen FSG1 stereo instrument and frozen 12 mm
FSG3/FSG4 fusion remain metrically coherent after exact-pose transport to H0.
"""
from __future__ import annotations
import hashlib, json

SPEC_ID = "FSG7a-prescribed-head-motion-self-occlusion-v1"
INSTRUMENT_ID = "FSG1-HDR-SGBM-one-original-update-original-validity-v1"
OBJECT_ID = 151
BACKGROUND_ID = 152
FIXTURES = ("fold_right", "fold_left")
SEEDS = (1409, 1453)
DEFAULT_SPP = {"small": 64, "full": 256}
VERGENCE_DISTANCE_M = 2.10

# The schedule is acquisition-side knowledge, not evaluator truth.  H0 is the
# initial head frame; Ht has the same orientation and the listed translation.
VIEW_SCHEDULE = {
    "fold_right": (
        {"role":"front_seed", "head_translation_h0_m":(0.0,0.0,0.0), "gaze_yaw_pitch_deg":(0.0,0.0)},
        {"role":"reveal_return", "head_translation_h0_m":(+0.45,0.0,0.0), "gaze_yaw_pitch_deg":(-5.5,0.0)},
    ),
    "fold_left": (
        {"role":"front_seed", "head_translation_h0_m":(0.0,0.0,0.0), "gaze_yaw_pitch_deg":(0.0,0.0)},
        {"role":"reveal_return", "head_translation_h0_m":(-0.45,0.0,0.0), "gaze_yaw_pitch_deg":(+5.5,0.0)},
    ),
}
FUSION = {"association_radius_m":0.012, "hash_cell_m":0.012}
TARGETS = {
    "patch_object_coverage_min": 0.90,
    "minimum_matched_points_reveal": 5000,
    "overlap_median_distance_max_m": 0.010,
    "overlap_p95_distance_max_m": 0.025,
    "map_surface_median_max_m": 0.010,
    "map_surface_p95_max_m": 0.030,
    "supported_surfels_min": 5000,
    "front_seed_coverage_min": 0.80,
    "return_seed_coverage_max": 0.05,
    "return_final_coverage_min": 0.80,
    "return_coverage_gain_min": 0.75,
    "final_truth_coverage_min": 0.90,
    "fixed_head_return_visibility_max": 0.02,
    "moved_head_return_visibility_min": 0.95,
}
PUBLIC_SPEC = {
    "id": SPEC_ID, "instrument": INSTRUMENT_ID,
    "object_id": OBJECT_ID, "background_id": BACKGROUND_ID,
    "fixtures": list(FIXTURES), "seeds": list(SEEDS), "spp": DEFAULT_SPP,
    "prescribed_vergence_distance_m": VERGENCE_DISTANCE_M,
    "view_schedule": {k:[{kk:(list(vv) if isinstance(vv,tuple) else vv) for kk,vv in row.items()} for row in rows] for k,rows in VIEW_SCHEDULE.items()},
    "fusion": FUSION, "targets": TARGETS,
    "initial_map_frame": "H0: initial head frame; +X right, +Y up, -Z forward; metres",
    "head_orientation_fixed": True,
    "head_translation_prescribed": True,
    "head_translation_policy": False,
    "oracle_instance_segmentation": True,
    "self_occlusion_truth_hidden_from_runner": True,
    "no_icp": True, "no_hole_fill": True, "no_mesh_reconstruction": True,
    "fsg1_instrument_unchanged": True, "fsg3_surface_map_unchanged": True,
}

def public_digest() -> str:
    return hashlib.sha256(json.dumps(PUBLIC_SPEC,sort_keys=True,separators=(",",":" )).encode()).hexdigest()

def view(fixture:str, step:int) -> dict:
    if fixture not in FIXTURES: raise ValueError(f"unknown FSG7a fixture {fixture}")
    rows=VIEW_SCHEDULE[fixture]
    if not 0 <= int(step) < len(rows): raise ValueError("step outside FSG7a schedule")
    r=rows[int(step)]
    return {"role":r["role"], "head_translation_h0_m":tuple(map(float,r["head_translation_h0_m"])),
            "gaze_yaw_pitch_deg":tuple(map(float,r["gaze_yaw_pitch_deg"]))}

def render_seed(fixture:str, seed:int, step:int, eye_id:int) -> int:
    if fixture not in FIXTURES or seed not in SEEDS or eye_id not in (0,1): raise ValueError("invalid FSG7a render-seed key")
    if not 0 <= int(step) < len(VIEW_SCHEDULE[fixture]): raise ValueError("invalid step")
    return 1_000_000*int(seed) + 100_000*FIXTURES.index(fixture) + 1000*int(step) + eye_id
