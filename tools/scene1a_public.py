"""Truth-free public contract for Stage II / Scene-1a.

Scene-1a is the first fixed-head, static-scene multi-object experiment.  It keeps
FSG6f as the frozen intra-object controller and adds only a scene-level scheduler.
Three known oracle instance IDs are prescribed one seed fixation each.  Thereafter
all gaze selection is autonomous: each object's frozen FSG6f controller proposes
its next valid action, and the scene scheduler executes the proposal with the
largest already-existing FSG6f predicted-new-angular-area, then frontier score,
then instance ID as a deterministic final tie-break.

Every physical fixation is processed opportunistically for every known object.
Scene completion means every object independently reports no_frontier.
"""
from __future__ import annotations
import hashlib
import json

SPEC_ID = "StageII-Scene1a-seeded-multi-object-scheduling-v1"
INSTRUMENT_ID = "FSG1-HDR-SGBM-one-original-update-original-validity-v1"
FROZEN_OBJECT_POLICY_ID = "FSG6f-candidate-frontier-consensus-v1"

OBJECT_IDS = (201, 202, 203)
BACKGROUND_ID = 299
FIXTURES = ("triad_a", "triad_b")
SEEDS = (1601, 1667)
DEFAULT_SPP = {"small": 64, "full": 256}
VERGENCE_DISTANCE_M = 2.10
PER_OBJECT_MAX_FIXATIONS = 6
MAX_SCENE_FIXATIONS = len(OBJECT_IDS) * PER_OBJECT_MAX_FIXATIONS

# One prescribed seed per known object.  These are acquisition initial conditions,
# not scene-policy decisions.
SEED_SEQUENCE = {
    "triad_a": (
        (201, (-20.0, +5.0)),
        (202, (-8.0, -12.0)),
        (203, (+7.0, +5.0)),
    ),
    "triad_b": (
        (201, (+19.0, +5.0)),
        (202, (-8.0, +5.0)),
        (203, (-7.0, -12.0)),
    ),
}

# Frozen FSG3/FSG4/FSG6f association values.  Runtime asserts equality with the
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
    "scene_scheduler": "lexicographic max of frozen FSG6f selected predicted_new_angular_area_deg2, then frontier_score, then smaller instance ID",
    "scene_completion": "all seeded object controllers independently report no_frontier",
    "global_no_revisit": True,
    "opportunistic_fusion": "every completed binocular fixation is offered to every known object map and observation history",
    "fsg6f_is_imported_not_copied": True,
    "no_icp": True,
    "no_mesh_reconstruction": True,
    "no_hole_fill": True,
    "truth_hidden_from_prediction": True,
}


def public_digest() -> str:
    return hashlib.sha256(json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def fixture_index(fixture: str) -> int:
    if fixture not in FIXTURES:
        raise ValueError(f"unknown Scene-1a fixture {fixture}")
    return FIXTURES.index(fixture)


def render_seed(fixture: str, seed: int, yaw_deg: float, pitch_deg: float, eye_id: int) -> int:
    """Physical-view seed: independent of target object and loop step."""
    if seed not in SEEDS:
        raise ValueError("seed not in frozen Scene-1a schedule")
    if eye_id not in (0, 1):
        raise ValueError("eye_id must be 0 or 1")
    y = float(yaw_deg); p = float(pitch_deg)
    if not (-25.0 - 1e-9 <= y <= 25.0 + 1e-9 and -20.0 - 1e-9 <= p <= 20.0 + 1e-9):
        raise ValueError("gaze outside frozen FSG6f lattice domain")
    iy = int(round((y + 30.0) * 10.0)); ip = int(round((p + 25.0) * 10.0))
    if abs(y - (iy / 10.0 - 30.0)) > 1e-8 or abs(p - (ip / 10.0 - 25.0)) > 1e-8:
        raise ValueError("gaze must lie on the 0.1-degree physical-view seed lattice")
    return 1_000_000 * int(seed) + 700_000 * fixture_index(fixture) + 1000 * iy + 2 * ip + eye_id
