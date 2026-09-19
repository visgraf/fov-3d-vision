"""Truth-free public contract for FSG3 Increment 3.

Imported by the active host loop and policy. Deliberately contains no object
geometry or evaluation truth. The Blender fixture imports this module too so
IDs, profile/Spp, seed and policy parameters have one source of truth.
"""
from __future__ import annotations
import hashlib, json

SPEC_ID = "FSG3-active-frontier-growth-v1"
INSTRUMENT_ID = "FSG1-HDR-SGBM-one-original-update-original-validity-v1"
OBJECT_ID = 71
BACKGROUND_ID = 72
SEED = 307
DEFAULT_SPP = {"small": 64, "full": 256}
SEED_GAZE_YAW_DEG = -7.0
PITCH_DEG = 0.0
VERGENCE_DISTANCE_M = 2.10
MAX_FIXATIONS = 6

FUSION = {
    "association_radius_m": 0.012,
    "hash_cell_m": 0.012,
}

POLICY = {
    "step_deg": 5.0,
    "yaw_min_deg": -12.0,
    "yaw_max_deg": 18.0,
    "edge_band_fraction": 0.04,
    "edge_object_fraction_min": 0.15,
    "map_extent_quantile": 0.01,
    "minimum_overlap_deg": 4.0,
    "minimum_predicted_new_deg": 1.0,
}

TARGETS = {
    "fixation_count_min": 4,
    "fixation_count_max": MAX_FIXATIONS,
    "patch_object_coverage_min": 0.90,
    "minimum_matched_points_each": 5000,
    "minimum_new_fraction_nonterminal": 0.15,
    "minimum_new_fraction_terminal": 0.05,
    "overlap_median_distance_max_m": 0.010,
    "overlap_p95_distance_max_m": 0.025,
    "map_point_plane_median_max_m": 0.010,
    "map_point_plane_p95_max_m": 0.030,
    "final_truth_coverage_min": 0.90,
    "truth_coverage_gain_over_seed_min": 0.35,
    "minimum_incremental_coverage_gain_nonterminal": 0.10,
    "minimum_incremental_coverage_gain_terminal": 0.02,
    "coverage_drop_tolerance": 0.005,
}

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "instrument": INSTRUMENT_ID,
    "object_id": OBJECT_ID,
    "background_id": BACKGROUND_ID,
    "seed": SEED,
    "spp": DEFAULT_SPP,
    "seed_gaze_yaw_deg": SEED_GAZE_YAW_DEG,
    "pitch_deg": PITCH_DEG,
    "prescribed_vergence_distance_m": VERGENCE_DISTANCE_M,
    "maximum_fixations": MAX_FIXATIONS,
    "fusion": FUSION,
    "policy": POLICY,
    "targets": TARGETS,
    "fixed_head_frame": True,
    "oracle_instance_segmentation": True,
    "no_icp": True,
    "no_hole_fill": True,
    "no_mesh": True,
    "horizontal_frontier_only": True,
}

def public_digest() -> str:
    return hashlib.sha256(json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
