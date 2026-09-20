"""Truth-free public contract for FSG5 curved-surface growth.

FSG5 changes one major variable relative to the closed FSG3/FSG4 experiments:
the object surface is convex and curved.  The FSG1 stereo instrument, existing
FSG4 frontier policy, FSG3 surfel fusion, fixed head frame, oracle instance
segmentation, exact poses, fixed vergence and 5-degree local saccades remain
frozen.
"""
from __future__ import annotations
import hashlib
import json

SPEC_ID = "FSG5-curved-surface-growth-v1"
INSTRUMENT_ID = "FSG1-HDR-SGBM-one-original-update-original-validity-v1"
OBJECT_ID = 81
BACKGROUND_ID = 82
FIXTURES = ("curve_right", "curve_left")
SEEDS = (601, 647)
DEFAULT_SPP = {"small": 64, "full": 256}
SEED_GAZE_YAW_DEG = {"curve_right": -7.0, "curve_left": +7.0}
PITCH_DEG = 0.0
VERGENCE_DISTANCE_M = 2.10
MAX_BUDGET_FIXATIONS = 6

FUSION = {
    "association_radius_m": 0.012,
    "hash_cell_m": 0.012,
}

# Must remain byte-for-value equivalent to tools/fsg4_public.py POLICY.
POLICY = {
    "step_deg": 5.0,
    "yaw_min_deg": -25.0,
    "yaw_max_deg": 25.0,
    "edge_band_fraction": 0.04,
    "edge_object_fraction_min": 0.15,
    "map_extent_quantile": 0.01,
    "minimum_overlap_deg": 4.0,
    "minimum_predicted_new_deg": 1.0,
}

TARGETS = {
    "active_fixation_count_min": 4,
    "active_fixation_count_max": MAX_BUDGET_FIXATIONS,
    "patch_object_coverage_min": 0.90,
    "minimum_matched_points_each": 5000,
    "overlap_median_distance_max_m": 0.010,
    "overlap_p95_distance_max_m": 0.025,
    "map_surface_median_max_m": 0.010,
    "map_surface_p95_max_m": 0.030,
    "supported_signed_radial_bias_abs_max_m": 0.0075,
    "supported_surfels_min": 5000,
    "final_truth_coverage_min": 0.90,
    "truth_coverage_gain_over_seed_min": 0.35,
    "coverage_drop_tolerance": 0.005,
}

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "instrument": INSTRUMENT_ID,
    "object_id": OBJECT_ID,
    "background_id": BACKGROUND_ID,
    "fixtures": list(FIXTURES),
    "seeds": list(SEEDS),
    "spp": DEFAULT_SPP,
    "seed_gaze_yaw_deg": SEED_GAZE_YAW_DEG,
    "pitch_deg": PITCH_DEG,
    "prescribed_vergence_distance_m": VERGENCE_DISTANCE_M,
    "maximum_budget_fixations": MAX_BUDGET_FIXATIONS,
    "fusion": FUSION,
    "policy": POLICY,
    "targets": TARGETS,
    "fixed_head_frame": True,
    "oracle_instance_segmentation": True,
    "no_icp": True,
    "no_hole_fill": True,
    "no_mesh_reconstruction": True,
    "existing_fsg4_frontier_policy_unchanged": True,
    "curved_surface_truth_hidden_from_policy": True,
    "per_fixation_novelty_and_gain_are_descriptive_only": True,
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def fixture_index(fixture: str) -> int:
    if fixture not in FIXTURES:
        raise ValueError(f"unknown FSG5 fixture {fixture}")
    return FIXTURES.index(fixture)


def render_seed(fixture: str, seed: int, yaw_deg: float, eye_id: int) -> int:
    """Deterministic per-view seed independent of loop step.

    FSG5 has no paired competing policy, but yaw-keying keeps a re-acquired view
    semantically tied to its physical gaze rather than to an iteration number.
    """
    if seed not in SEEDS:
        raise ValueError("seed not in frozen FSG5 schedule")
    if eye_id not in (0, 1):
        raise ValueError("eye_id must be 0 or 1")
    y = float(yaw_deg)
    if y < POLICY["yaw_min_deg"] - 1e-9 or y > POLICY["yaw_max_deg"] + 1e-9:
        raise ValueError("yaw outside frozen FSG5 policy range")
    q = int(round((y + 30.0) * 10.0))
    if abs(y - (q / 10.0 - 30.0)) > 1e-8:
        raise ValueError("yaw must lie on the 0.1-degree seed lattice")
    return 100000 * int(seed) + 5000 * fixture_index(fixture) + 2 * q + eye_id
