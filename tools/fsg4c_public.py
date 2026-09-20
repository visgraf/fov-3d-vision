"""Truth-free public contract for FSG4c fresh active-versus-scan validation.

FSG4c prospectively re-tests the FSG4 efficiency hypothesis on fresh fixtures and
fresh rendering seeds after FSG4b showed that per-fixation novelty/gain gates are
not valid experiment-integrity gates near surface completion.  The active policy,
fixed scan, stereo instrument, fusion rule, camera budget, exact paired-view reuse,
AUC definition and aggregate comparison thresholds remain unchanged.
"""
from __future__ import annotations
import hashlib
import json

SPEC_ID = "FSG4c-active-vs-fixed-scan-fresh-v1"
INSTRUMENT_ID = "FSG1-HDR-SGBM-one-original-update-original-validity-v1"
OBJECT_ID = 81
BACKGROUND_ID = 82
FIXTURES = ("case_c", "case_d")
SEEDS = (503, 557)
DEFAULT_SPP = {"small": 64, "full": 256}
SEED_GAZE_YAW_DEG = 0.0
PITCH_DEG = 0.0
VERGENCE_DISTANCE_M = 2.10
MAX_BUDGET_FIXATIONS = 5

# Frozen FSG4 control.  It is intentionally identical to FSG4a/b.
SCAN_YAWS_DEG = (0.0, -5.0, 5.0, -10.0, 10.0)

FUSION = {
    "association_radius_m": 0.012,
    "hash_cell_m": 0.012,
}

# Frozen FSG3/FSG4 frontier policy parameters.  fsg4c_run imports the existing
# fsg4_policy implementation and checks these values against fsg4_public.
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
    # Run validity / map quality.  Per-fixation novelty and coverage gain are
    # deliberately descriptive in FSG4c; efficiency is judged by the curve/AUC.
    "active_fixation_count_min": 4,
    "active_fixation_count_max": MAX_BUDGET_FIXATIONS,
    "patch_object_coverage_min": 0.90,
    "minimum_matched_points_each": 5000,
    "overlap_median_distance_max_m": 0.010,
    "overlap_p95_distance_max_m": 0.025,
    "map_point_plane_median_max_m": 0.010,
    "map_point_plane_p95_max_m": 0.030,
    "active_final_truth_coverage_min": 0.90,
    "coverage_drop_tolerance": 0.005,
    # Paired efficiency comparison, unchanged from FSG4a/b.
    "pair_auc_wins_required": 4,
    "mean_auc_gain_min": 0.10,
    "mean_final_coverage_gain_min": 0.10,
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
    "scan_yaws_deg": list(SCAN_YAWS_DEG),
    "fusion": FUSION,
    "policy": POLICY,
    "targets": TARGETS,
    "per_fixation_novelty_and_gain_are_descriptive_only": True,
    "fixed_head_frame": True,
    "oracle_instance_segmentation": True,
    "no_icp": True,
    "no_hole_fill": True,
    "no_mesh": True,
    "horizontal_frontier_only": True,
    "paired_render_noise_by_fixture_seed_yaw": True,
    "exact_shared_view_artifact_reuse": True,
}


def public_digest() -> str:
    return hashlib.sha256(json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def fixture_index(fixture: str) -> int:
    if fixture not in FIXTURES:
        raise ValueError(f"unknown FSG4c fixture {fixture}")
    return FIXTURES.index(fixture)


def yaw_lattice_index(yaw_deg: float) -> int:
    step = float(POLICY["step_deg"])
    q = round(float(yaw_deg) / step)
    if abs(float(yaw_deg) - q * step) > 1e-8:
        raise ValueError("yaw is not on the frozen 5-degree lattice")
    lo = int(round(POLICY["yaw_min_deg"] / step))
    hi = int(round(POLICY["yaw_max_deg"] / step))
    if q < lo or q > hi:
        raise ValueError("yaw outside frozen FSG4c range")
    return q - lo


def render_seed(fixture: str, seed: int, yaw_deg: float, eye_id: int) -> int:
    if seed not in SEEDS:
        raise ValueError("seed not in frozen FSG4c schedule")
    if eye_id not in (0, 1):
        raise ValueError("eye_id must be 0 or 1")
    return 100000 * int(seed) + 1000 * fixture_index(fixture) + 10 * yaw_lattice_index(yaw_deg) + eye_id
