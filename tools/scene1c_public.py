"""Truth-free public contract for Stage II / Scene-1c.

Scene-1c tests a composition principle rather than a new runtime policy.  The
FSG6f object controller and the Scene-1b fair scheduler are frozen.  Before a
multi-object trial is allowed to run, every one of its three object placements
must first pass a prospectively specified single-object control, rendered in the
same complete three-object scene, with the same seed and the same six-look
FSG6f budget.  No failed component is replaced or tuned.
"""
from __future__ import annotations
import hashlib
import json
from itertools import product

SPEC_ID = "StageII-Scene1c-certified-composition-v1"
INSTRUMENT_ID = "FSG1-HDR-SGBM-one-original-update-original-validity-v1"
FROZEN_OBJECT_POLICY_ID = "FSG6f-candidate-frontier-consensus-v1"
FROZEN_SCENE_SCHEDULER_ID = "Scene1b-least-service-then-area-score-id-v1"

OBJECT_IDS = (201, 202, 203)
BACKGROUND_ID = 299
FIXTURES = ("cert_triad_e", "cert_triad_f")
SEEDS = (1847, 1901)
DEFAULT_SPP = {"small": 64, "full": 256}
VERGENCE_DISTANCE_M = 2.10
PER_OBJECT_MAX_FIXATIONS = 6
MAX_SCENE_FIXATIONS = len(OBJECT_IDS) * PER_OBJECT_MAX_FIXATIONS

# One prescribed partial seed per known object.  These are initial conditions,
# not autonomous scene-policy decisions.
SEED_SEQUENCE = {
    "cert_triad_e": (
        (201, (-19.0, +8.0)),
        (202, ( -4.0, -9.0)),
        (203, (+11.0, +8.0)),
    ),
    "cert_triad_f": (
        (201, ( -4.0, -8.0)),
        (202, (-19.0, +9.0)),
        (203, (+10.0, +9.0)),
    ),
}

# Frozen FSG3/FSG4/FSG6f association values.  Runtime asserts equality with
# the repository FSG6f contract before acquisition.
FUSION = {"association_radius_m": 0.012, "hash_cell_m": 0.012}

# Kept byte-for-byte numerically equal to Scene-1b's per-object gates.
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

COMPONENT_CERTIFICATION_STATUS_PASS = "SCENE1C_COMPONENT_CERTIFICATION_PASS"
COMPONENT_CERTIFICATION_STATUS_FAIL = "SCENE1C_COMPONENT_CERTIFICATION_FAIL"
STAGE_STATUS_PASS = "SCENE1C_STAGEII_PASS"
STAGE_STATUS_FAIL = "SCENE1C_STAGEII_FAIL"

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "instrument": INSTRUMENT_ID,
    "frozen_object_policy": FROZEN_OBJECT_POLICY_ID,
    "frozen_scene_scheduler": FROZEN_SCENE_SCHEDULER_ID,
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
    "component_certification_required_before_ensemble": True,
    "component_certification": "for each fixture/seed/object, run frozen FSG6f alone on that object in the exact complete three-object scene; all twelve full controls must pass before any Scene-1c ensemble full acquisition",
    "component_control_uses_same_scene_renderer": True,
    "component_failure_is_not_tuned_or_replaced": True,
    "scene_scheduler": "unchanged Scene-1b least autonomous post-seed service first among live objects; then lexicographic max of frozen FSG6f selected predicted_new_angular_area_deg2, frontier_score, smaller instance ID",
    "scene_completion": "all seeded object controllers independently report no_frontier",
    "global_no_revisit": True,
    "opportunistic_fusion": "unchanged Scene-1b: every completed binocular fixation is offered to every known object map and observation history",
    "object_discovery_not_in_scope": True,
    "object_object_occlusion_not_in_scope": True,
    "semantics_not_in_scope": True,
    "fsg6f_is_imported_not_copied": True,
    "scene1b_scheduler_is_imported_not_copied": True,
    "scene1a_failure_preserved": True,
    "scene1b_failure_preserved": True,
    "no_icp": True,
    "no_mesh_reconstruction": True,
    "no_hole_fill": True,
    "truth_hidden_from_prediction": True,
}


def public_digest() -> str:
    return hashlib.sha256(json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def fixture_index(fixture: str) -> int:
    if fixture not in FIXTURES:
        raise ValueError(f"unknown Scene-1c fixture {fixture}")
    return FIXTURES.index(fixture)


def seed_gaze_for_object(fixture: str, object_id: int) -> tuple[float, float]:
    for oid, gaze in SEED_SEQUENCE[fixture]:
        if int(oid) == int(object_id):
            return tuple(float(x) for x in gaze)
    raise ValueError("object has no Scene-1c prescribed seed")


def expected_component_trials() -> tuple[tuple[str, int, int], ...]:
    return tuple((f, int(s), int(o)) for f, s, o in product(FIXTURES, SEEDS, OBJECT_IDS))


def render_seed(fixture: str, seed: int, yaw_deg: float, pitch_deg: float, eye_id: int) -> int:
    """Physical-view seed: independent of target object and control/ensemble role."""
    if seed not in SEEDS:
        raise ValueError("seed not in frozen Scene-1c schedule")
    if eye_id not in (0, 1):
        raise ValueError("eye_id must be 0 or 1")
    y = float(yaw_deg); p = float(pitch_deg)
    if not (-25.0 - 1e-9 <= y <= 25.0 + 1e-9 and -20.0 - 1e-9 <= p <= 20.0 + 1e-9):
        raise ValueError("gaze outside frozen FSG6f lattice domain")
    iy = int(round((y + 30.0) * 10.0)); ip = int(round((p + 25.0) * 10.0))
    if abs(y - (iy / 10.0 - 30.0)) > 1e-8 or abs(p - (ip / 10.0 - 25.0)) > 1e-8:
        raise ValueError("gaze must lie on the 0.1-degree physical-view seed lattice")
    return 1_000_000 * int(seed) + 700_000 * fixture_index(fixture) + 1000 * iy + 2 * ip + eye_id
