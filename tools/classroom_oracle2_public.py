"""Public contract for Classroom-Oracle-2: boundary ablation.

This experiment changes exactly one scientific variable relative to
Classroom-Oracle-1: the controller angular domain is widened from yaw +/-25 deg,
pitch +/-20 deg to yaw +/-35 deg, pitch +/-30 deg.  The scene, the 25 target
instances, their original oracle seed gazes, the oracle local-measurement
semantics, FSG6f, the Cyclopean handoff, 12 mm fusion, render profile, and
24-fixation watchdog remain unchanged.
"""
from __future__ import annotations

import hashlib
import json

SPEC_ID = "Classroom-Oracle-2-Boundary-Ablation-v1"
PARENT_COMMIT = "f9fb196"
BASELINE_SPEC_ID = "Classroom-Oracle-1-v1"
BASELINE_RUN_DEFAULT = "previews/classroom-oracle-1-full"
SCENE = "scenes/classroom/classroom_eye.blend"
DEFAULT_PROFILE = "full"
DEFAULT_DEVICE = "OPTIX"
TARGET_INSTANCE_COUNT = 25
SEED_SCAN_STEP_DEG = 0.25
CYCLOPEAN_GRID_DEG = 0.10
MAX_OBJECT_FIXATIONS = 24

ORIGINAL_DOMAIN = {
    "yaw_min_deg": -25.0,
    "yaw_max_deg": 25.0,
    "pitch_min_deg": -20.0,
    "pitch_max_deg": 20.0,
}

WIDE_DOMAIN = {
    "yaw_min_deg": -35.0,
    "yaw_max_deg": 35.0,
    "pitch_min_deg": -30.0,
    "pitch_max_deg": 30.0,
}

FUSION = {
    "association_radius_m": 0.012,
    "hash_cell_m": 0.012,
}

SCIENTIFIC_CONTRACT = {
    "single_changed_variable": "controller angular extent",
    "baseline_domain_deg": {"yaw": [-25.0, 25.0], "pitch": [-20.0, 20.0]},
    "wide_domain_deg": {"yaw": [-35.0, 35.0], "pitch": [-30.0, 30.0]},
    "same_scene": True,
    "same_target_instance_set": True,
    "same_original_seed_per_target": True,
    "same_local_oracle_measurement": True,
    "same_fsg6f_logic": True,
    "same_cyclopean_rule": True,
    "same_12mm_fusion": True,
    "same_profile": "full",
    "same_watchdog": 24,
    "foreground_background_decomposition": False,
    "no_policy_retuning": True,
    "no_quality_pass_fail_threshold": True,
}

EVALUATION_CONTRACT = {
    "scope_a": "original +/-25 yaw, +/-20 pitch reachable samples",
    "scope_b": "wide +/-35 yaw, +/-30 pitch reachable samples",
    "recompute_baseline_sample_coverage": True,
    "measure_recovery_of_baseline_misses": True,
    "measure_regressions_on_baseline_hits": True,
    "measure_new_boundary_concentration": True,
    "coverage_radius_m": 0.012,
}

DEMO_CONTRACT = {
    "sequential_foveations": True,
    "object_surface_growth": True,
    "cyclopean_state": True,
    "final_object_point_clouds": True,
    "combined_scene_cloud": True,
    "rgb_depth_instance_panoramas": True,
    "blender_reference_comparison": True,
    "synchronised_four_view_video_when_available": True,
    "observational_only": True,
}

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent_commit": PARENT_COMMIT,
    "baseline_spec": BASELINE_SPEC_ID,
    "scene": SCENE,
    "target_instance_count": TARGET_INSTANCE_COUNT,
    "seed_scan_step_deg": SEED_SCAN_STEP_DEG,
    "cyclopean_grid_deg": CYCLOPEAN_GRID_DEG,
    "original_domain": ORIGINAL_DOMAIN,
    "wide_domain": WIDE_DOMAIN,
    "fusion": FUSION,
    "scientific_contract": SCIENTIFIC_CONTRACT,
    "evaluation_contract": EVALUATION_CONTRACT,
    "demo_contract": DEMO_CONTRACT,
}


def public_digest() -> str:
    payload = json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def self_test() -> list[str]:
    fails: list[str] = []
    if ORIGINAL_DOMAIN != {
        "yaw_min_deg": -25.0, "yaw_max_deg": 25.0,
        "pitch_min_deg": -20.0, "pitch_max_deg": 20.0,
    }:
        fails.append("original domain changed")
    if WIDE_DOMAIN != {
        "yaw_min_deg": -35.0, "yaw_max_deg": 35.0,
        "pitch_min_deg": -30.0, "pitch_max_deg": 30.0,
    }:
        fails.append("wide domain is not +/-35 yaw, +/-30 pitch")
    if FUSION != {"association_radius_m": 0.012, "hash_cell_m": 0.012}:
        fails.append("fusion rule is not the frozen 12 mm rule")
    if MAX_OBJECT_FIXATIONS != 24:
        fails.append("watchdog is not 24")
    if TARGET_INSTANCE_COUNT != 25:
        fails.append("target instance count is not the frozen 25-object set")
    if SCIENTIFIC_CONTRACT["foreground_background_decomposition"]:
        fails.append("foreground/background decomposition is forbidden")
    if not SCIENTIFIC_CONTRACT["same_original_seed_per_target"]:
        fails.append("baseline seed replay is required")
    if not DEMO_CONTRACT["observational_only"]:
        fails.append("demo must be observational only")
    return fails


if __name__ == "__main__":
    bad = self_test()
    for item in bad:
        print("[classroom-oracle2-public] FAIL", item)
    print("[classroom-oracle2-public] self-test", "FAILED" if bad else "PASS", public_digest())
    raise SystemExit(bool(bad))
