"""Truth-free public contract for FSG4 Increment 4.

FSG4 compares the frozen FSG3 frontier policy with one prospectively fixed,
non-adaptive symmetric scan under the same local RGB-D instrument, fusion rule,
profile and per-view rendering noise. This module intentionally contains no
fixture geometry or evaluation truth.
"""
from __future__ import annotations
import hashlib
import json

SPEC_ID = "FSG4-active-vs-fixed-scan-v1"
INSTRUMENT_ID = "FSG1-HDR-SGBM-one-original-update-original-validity-v1"
OBJECT_ID = 81
BACKGROUND_ID = 82
FIXTURES = ("case_a", "case_b")  # opaque identifiers; geometry is evaluator-only
SEEDS = (401, 443)
DEFAULT_SPP = {"small": 64, "full": 256}
SEED_GAZE_YAW_DEG = 0.0
PITCH_DEG = 0.0
VERGENCE_DISTANCE_M = 2.10
MAX_BUDGET_FIXATIONS = 5

# One fixed non-adaptive baseline for every fixture and seed. It is symmetric
# about the common seed and never consults the image, map, fixture or truth.
SCAN_YAWS_DEG = (0.0, -5.0, 5.0, -10.0, 10.0)

FUSION = {
    "association_radius_m": 0.012,
    "hash_cell_m": 0.012,
}

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
    # Active-run integrity / reconstruction gates, inherited from FSG3 where applicable.
    "active_fixation_count_min": 4,
    "active_fixation_count_max": MAX_BUDGET_FIXATIONS,
    "patch_object_coverage_min": 0.90,
    "minimum_matched_points_each": 5000,
    "minimum_new_fraction_nonterminal": 0.15,
    "minimum_new_fraction_terminal": 0.05,
    "overlap_median_distance_max_m": 0.010,
    "overlap_p95_distance_max_m": 0.025,
    "map_point_plane_median_max_m": 0.010,
    "map_point_plane_p95_max_m": 0.030,
    "active_final_truth_coverage_min": 0.90,
    "active_truth_coverage_gain_over_seed_min": 0.35,
    "minimum_incremental_coverage_gain_nonterminal": 0.10,
    "minimum_incremental_coverage_gain_terminal": 0.02,
    "coverage_drop_tolerance": 0.005,
    # Policy-comparison gates. These are paired, prospectively fixed and apply
    # only after all four full fixture/seed pairs have been completed.
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
    "fixed_head_frame": True,
    "oracle_instance_segmentation": True,
    "no_icp": True,
    "no_hole_fill": True,
    "no_mesh": True,
    "horizontal_frontier_only": True,
    "paired_render_noise_by_fixture_seed_yaw": True,
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def fixture_index(fixture: str) -> int:
    if fixture not in FIXTURES:
        raise ValueError(f"unknown FSG4 fixture {fixture}")
    return FIXTURES.index(fixture)


def yaw_lattice_index(yaw_deg: float) -> int:
    step = float(POLICY["step_deg"])
    q = round(float(yaw_deg) / step)
    if abs(float(yaw_deg) - q * step) > 1e-8:
        raise ValueError("yaw is not on the frozen 5-degree lattice")
    lo = int(round(POLICY["yaw_min_deg"] / step))
    hi = int(round(POLICY["yaw_max_deg"] / step))
    if q < lo or q > hi:
        raise ValueError("yaw outside frozen FSG4 range")
    return q - lo


def render_seed(fixture: str, seed: int, yaw_deg: float, eye_id: int) -> int:
    """Deterministic per-view seed, intentionally independent of policy and step.

    Thus an active and scan observation at the same fixture/MC seed/yaw have the
    same left/right Cycles seed even if they reach that yaw at different steps.
    """
    if seed not in SEEDS:
        raise ValueError("seed not in frozen FSG4 schedule")
    if eye_id not in (0, 1):
        raise ValueError("eye_id must be 0 or 1")
    return 100000 * int(seed) + 1000 * fixture_index(fixture) + 10 * yaw_lattice_index(yaw_deg) + eye_id
