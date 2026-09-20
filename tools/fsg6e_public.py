"""Truth-free public contract for FSG6e persistent open-frontier validation.

FSG6d settled the candidate-local binocular continuation veto, but showed that
raw tangent-asymmetry frontiers do not disappear on a thin ribbon: physical
lateral boundaries remain geometrically one-sided even after the visible surface
is essentially complete.  FSG6e changes frontier *state*, not the measurement
instrument, fusion, raw frontier extraction, continuation corridor, ranking,
lattice, budget, or numerical gates.

Each raw frontier surfel keeps the existing 0.12 m look-ahead target.  If that
target is already represented by the persistent map within the frozen 12 mm
FSG3 association radius, the raw frontier is MAP_RESOLVED.  If it is not mapped
but a completed binocular fixation has explicitly observed the target location
with valid support in both eyes and object evidence below the already-frozen
0.15 continuation threshold, it is BOUNDARY_RESOLVED.  Otherwise it remains
OPEN.  Only OPEN frontiers may support a candidate, after which the unchanged
FSG6d projected-frontier corridor still checks current-view continuation.  No
new numerical threshold is introduced.
"""
from __future__ import annotations
import hashlib
import json

SPEC_ID = "FSG6e-persistent-open-frontier-v1"
INSTRUMENT_ID = "FSG1-HDR-SGBM-one-original-update-original-validity-v1"
OBJECT_ID = 131
BACKGROUND_ID = 132
FIXTURES = ("closure_up_right", "closure_down_left")
SEEDS = (1123, 1181)
DEFAULT_SPP = {"small": 64, "full": 256}
SEED_GAZE_DEG = {
    "closure_up_right": (-8.0, -7.0),
    "closure_down_left": (+8.0, +7.0),
}
VERGENCE_DISTANCE_M = 2.10
MAX_BUDGET_FIXATIONS = 6

FUSION = {
    "association_radius_m": 0.012,
    "hash_cell_m": 0.012,
}

# Byte-for-byte numerical values inherited from FSG6a-d. Do not tune in FSG6e.
SURFACE_FRONTIER = {
    "component_step_deg": 5.0,
    "yaw_min_deg": -25.0,
    "yaw_max_deg": +25.0,
    "pitch_min_deg": -20.0,
    "pitch_max_deg": +20.0,
    "edge_band_fraction": 0.04,
    "edge_object_fraction_min": 0.15,
    "voxel_m": 0.025,
    "neighbour_radius_m": 0.065,
    "minimum_neighbours": 6,
    "tangent_asymmetry_min": 0.18,
    "lookahead_m": 0.12,
    "current_view_margin_deg": 1.0,
    "minimum_candidate_frontier_support": 8,
    "alignment_cos_min": 0.50,
    "map_extent_quantile": 0.01,
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
    "pitch_span_min_deg": 10.0,
}

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "instrument": INSTRUMENT_ID,
    "object_id": OBJECT_ID,
    "background_id": BACKGROUND_ID,
    "fixtures": list(FIXTURES),
    "seeds": list(SEEDS),
    "spp": DEFAULT_SPP,
    "seed_gaze_deg": {k: list(v) for k, v in SEED_GAZE_DEG.items()},
    "prescribed_vergence_distance_m": VERGENCE_DISTANCE_M,
    "maximum_budget_fixations": MAX_BUDGET_FIXATIONS,
    "fusion": FUSION,
    "surface_frontier": SURFACE_FRONTIER,
    "targets": TARGETS,
    "fixed_head_frame": True,
    "oracle_instance_segmentation": True,
    "raw_frontier": "unchanged FSG6d local PCA/tangent asymmetry",
    "frontier_state": "MAP_RESOLVED if look-ahead target is within frozen FSG3 association radius; BOUNDARY_RESOLVED if a completed binocular supported observation sees object fraction below frozen 0.15 at that target; otherwise OPEN",
    "map_resolution_radius_is_frozen_fusion_association_radius": True,
    "boundary_resolution_uses_completed_binocular_history": True,
    "boundary_resolution_threshold_is_frozen_continuation_threshold": True,
    "boundary_patch_scale_derived_from_frozen_edge_band_fraction": True,
    "continuation_veto": "unchanged FSG6d binocular projected 3D-frontier exit corridor in the candidate forward image sector",
    "continuation_threshold_unchanged_from_fsg6d": True,
    "legacy_edge_band_fraction_reused_as_corridor_width": True,
    "no_new_frontier_state_threshold": True,
    "no_icp": True,
    "no_hole_fill": True,
    "no_mesh_reconstruction": True,
    "fsg3_surface_map_unchanged": True,
    "frontier_truth_hidden_from_policy": True,
    "per_fixation_novelty_and_gain_are_descriptive_only": True,
}


def public_digest() -> str:
    return hashlib.sha256(json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def fixture_index(fixture: str) -> int:
    if fixture not in FIXTURES:
        raise ValueError(f"unknown FSG6e fixture {fixture}")
    return FIXTURES.index(fixture)


def render_seed(fixture: str, seed: int, yaw_deg: float, pitch_deg: float, eye_id: int) -> int:
    """Deterministic physical-view seed independent of loop step."""
    if seed not in SEEDS:
        raise ValueError("seed not in frozen FSG6e schedule")
    if eye_id not in (0, 1):
        raise ValueError("eye_id must be 0 or 1")
    p = SURFACE_FRONTIER; y = float(yaw_deg); q = float(pitch_deg)
    if not (p["yaw_min_deg"] - 1e-9 <= y <= p["yaw_max_deg"] + 1e-9):
        raise ValueError("yaw outside frozen FSG6e range")
    if not (p["pitch_min_deg"] - 1e-9 <= q <= p["pitch_max_deg"] + 1e-9):
        raise ValueError("pitch outside frozen FSG6e range")
    iy = int(round((y + 30.0) * 10.0)); ip = int(round((q + 25.0) * 10.0))
    if abs(y - (iy / 10.0 - 30.0)) > 1e-8 or abs(q - (ip / 10.0 - 25.0)) > 1e-8:
        raise ValueError("gaze must lie on the 0.1-degree seed lattice")
    return 1_000_000 * int(seed) + 700_000 * fixture_index(fixture) + 1000 * iy + 2 * ip + eye_id
