"""Truth-free public contract for Stage II / Scene-1b.

Scene-1b preserves Scene-1a's fixed-head, static-scene, three-known-object setup
but replaces the starvation-prone scene scheduler with a structural fairness rule.
The frozen FSG6f controller remains the per-object action generator.  Among live
objects, only those with the least autonomous post-seed service count compete;
within that fairness class the already-existing Scene-1a lexicographic utility
(predicted new angular area, frontier score, instance ID) is unchanged.
"""
from __future__ import annotations
import hashlib
import json

SPEC_ID = "StageII-Scene1b-fair-multi-object-scheduling-v1"
INSTRUMENT_ID = "FSG1-HDR-SGBM-one-original-update-original-validity-v1"
FROZEN_OBJECT_POLICY_ID = "FSG6f-candidate-frontier-consensus-v1"

OBJECT_IDS = (201, 202, 203)
BACKGROUND_ID = 299
FIXTURES = ("fair_triad_c", "fair_triad_d")
SEEDS = (1723, 1789)
DEFAULT_SPP = {"small": 64, "full": 256}
VERGENCE_DISTANCE_M = 2.10
PER_OBJECT_MAX_FIXATIONS = 6
MAX_SCENE_FIXATIONS = len(OBJECT_IDS) * PER_OBJECT_MAX_FIXATIONS

# One prescribed seed per known object. These are acquisition initial conditions,
# not autonomous scene-policy decisions.
SEED_SEQUENCE = {
    "fair_triad_c": (
        (201, (-19.0, +8.0)),
        (202, (-6.0, -9.0)),
        (203, (+9.0, +8.0)),
    ),
    "fair_triad_d": (
        (201, (-4.0, -9.0)),
        (202, (-21.0, +9.0)),
        (203, (+7.0, +9.0)),
    ),
}

# Frozen FSG3/FSG4/FSG6f association values. Runtime asserts equality with the
# repository FSG6f public contract before acquisition.
FUSION = {"association_radius_m": 0.012, "hash_cell_m": 0.012}

TARGETS = {
    "patch_object_coverage_min": 0.90,
    "minimum_matched_points_each_targeted_postseed": 5000,
    "overlap_median_distance_max_m": 0.010,
    "overlap_p95_distance_max_m": 0.025,
    "map_surface_median_max_m": 0.010,
    "map_surface_p95_max_m": 0.030,
    "supported_surfels_min_each_object": 5000,
    "final_truth_coverage_min_each_object": 0.90,
    "truth_coverage_gain_over_seed_min_each_object": 0.25,
    "minimum_postseed_target_fixations_each_object": 1,
    "minimum_scene_target_switches": 2,
}

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "instrument": INSTRUMENT_ID,
    "frozen_object_policy": FROZEN_OBJECT_POLICY_ID,
    "object_ids": list(OBJECT_IDS),
    "background_id": BACKGROUND_ID,
    "fixtures": list(FIXTURES),
    "seeds": list(SEEDS),
    "spp": DEFAULT_SPP,
    "prescribed_seed_sequence": {k: [[int(i), list(g)] for i, g in v] for k, v in SEED_SEQUENCE.items()},
    "prescribed_vergence_distance_m": VERGENCE_DISTANCE_M,
    "per_object_max_fixations": PER_OBJECT_MAX_FIXATIONS,
    "maximum_scene_fixations": MAX_SCENE_FIXATIONS,
    "fusion": FUSION,
    "targets": TARGETS,
    "fixed_head": True,
    "static_scene": True,
    "oracle_instance_segmentation": True,
    "known_objects_are_seeded_once_before_autonomy": True,
    "object_discovery_not_in_scope": True,
    "object_object_occlusion_not_in_scope": True,
    "semantics_not_in_scope": True,
    "scene_scheduler": "least autonomous post-seed service first among live objects; then lexicographic max of frozen FSG6f selected predicted_new_angular_area_deg2, frontier_score, smaller instance ID",
    "scene_completion": "all seeded object controllers independently report no_frontier",
    "global_no_revisit": True,
    "opportunistic_fusion": "every completed binocular fixation is offered to every known object map and observation history",
    "fsg6f_is_imported_not_copied": True,
    "scene1a_failure_preserved": True,
    "no_icp": True,
    "no_mesh_reconstruction": True,
    "no_hole_fill": True,
    "truth_hidden_from_prediction": True,
}


def public_digest() -> str:
    return hashlib.sha256(json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def fixture_index(fixture: str) -> int:
    if fixture not in FIXTURES:
        raise ValueError(f"unknown Scene-1b fixture {fixture}")
    return FIXTURES.index(fixture)


def render_seed(fixture: str, seed: int, yaw_deg: float, pitch_deg: float, eye_id: int) -> int:
    """Physical-view seed: independent of target object and loop step."""
    if seed not in SEEDS:
        raise ValueError("seed not in frozen Scene-1b schedule")
    if eye_id not in (0, 1):
        raise ValueError("eye_id must be 0 or 1")
    y = float(yaw_deg); p = float(pitch_deg)
    if not (-25.0 - 1e-9 <= y <= 25.0 + 1e-9 and -20.0 - 1e-9 <= p <= 20.0 + 1e-9):
        raise ValueError("gaze outside frozen FSG6f lattice domain")
    iy = int(round((y + 30.0) * 10.0)); ip = int(round((p + 25.0) * 10.0))
    if abs(y - (iy / 10.0 - 30.0)) > 1e-8 or abs(p - (ip / 10.0 - 25.0)) > 1e-8:
        raise ValueError("gaze must lie on the 0.1-degree physical-view seed lattice")
    return 1_000_000 * int(seed) + 700_000 * fixture_index(fixture) + 1000 * iy + 2 * ip + eye_id
