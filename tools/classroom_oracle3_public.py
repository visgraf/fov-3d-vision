"""Public contract for Classroom-Oracle-3: eligibility audit.

Oracle-3 is a read-only diagnostic experiment.  It changes no controller,
measurement, fusion, scene, seed, gaze, budget, or domain parameter.  It replays
the final Oracle-1 controller state, reconstructs the Cyclopean epistemic state,
and only after those replays are complete opens evaluation truth to ask why
reachable-but-uncovered surface was not actionable.
"""
from __future__ import annotations

import hashlib
import json

SPEC_ID = "Classroom-Oracle-3-Eligibility-Audit-v1"
PARENT_COMMIT = "20bce24"
ORACLE1_RESULT_COMMIT = "f9fb196"
ORACLE2_RESULT_COMMIT = "20bce24"
ORACLE1_RUN_DEFAULT = "previews/classroom-oracle-1-full"
ORACLE2_RUN_DEFAULT = "previews/classroom-oracle-2-full"
DEFAULT_OUT = "previews/classroom-oracle-3-audit"
FOCUS_OBJECT_COUNT = 6
CYCLOPEAN_GRID_DEG = 0.10
COVERAGE_RADIUS_M = 0.012

ORIGINAL_DOMAIN = {
    "yaw_min_deg": -25.0,
    "yaw_max_deg": 25.0,
    "pitch_min_deg": -20.0,
    "pitch_max_deg": 20.0,
}

SCIENTIFIC_CONTRACT = {
    "read_only": True,
    "new_acquisitions": 0,
    "new_fixations": 0,
    "new_fusion": 0,
    "controller_source_modified": False,
    "fsg6f_rule_modified": False,
    "cyclopean_rule_modified": False,
    "fusion_rule_modified": False,
    "watchdog_modified": False,
    "domain_modified": False,
    "truth_opened_during_controller_replay": False,
    "truth_allowed_only_after_controller_phase": True,
    "no_quality_pass_fail_threshold": True,
    "focus_selection": "six largest Oracle-1 miss counts from Oracle-2 Scope-A evaluation",
}

FSG_TERMINAL_STAGES = (
    "NO_OPEN_FRONTIER",
    "OPEN_BUT_NO_CANDIDATE",
    "CANDIDATES_REJECTED_BY_CONSENSUS",
    "STOP_OTHER",
    "ACTIVE",
)

CYCLOPEAN_FIRST_REJECTION_REASONS = (
    "NOT_SHORELINE",
    "INTERNAL_COMPONENT",
    "ALREADY_OBSERVED",
    "PREVIOUSLY_FIXATED_CELL",
    "ELIGIBLE_NEVER_OBSERVED_EXTERIOR",
    "OUT_OF_CHART",
)

TRUTH_SUBTYPES = (
    "ANGULAR_SUPPORT_BUT_3D_UNCOVERED",
    "COMPLEMENT_NONSHORELINE",
    "INTERNAL_NEVER_OBSERVED",
    "INTERNAL_TARGET_NO_DEPTH",
    "INTERNAL_TARGET_WITH_DEPTH",
    "INTERNAL_NONTARGET_ONLY",
    "INTERNAL_MIXED",
    "INTERNAL_OTHER_OBSERVED",
    "EXTERIOR_TARGET_NO_DEPTH",
    "EXTERIOR_TARGET_WITH_DEPTH",
    "EXTERIOR_NONTARGET_ONLY",
    "EXTERIOR_MIXED",
    "EXTERIOR_OTHER_OBSERVED",
    "EXTERIOR_NEVER_OBSERVED_VISITED",
    "EXTERIOR_NEVER_OBSERVED_ELIGIBLE",
    "OUT_OF_CHART",
)

DEMO_CONTRACT = {
    "posthoc_only": True,
    "sequential_saved_fixations": True,
    "binocular_observation": True,
    "evolving_cyclopean_state": True,
    "trajectory_view": True,
    "truth_rejection_overlay": True,
    "focus_object_final_frames": True,
    "overview_png": True,
    "mp4_when_available": True,
    "demo_md": True,
}

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent_commit": PARENT_COMMIT,
    "oracle1_result_commit": ORACLE1_RESULT_COMMIT,
    "oracle2_result_commit": ORACLE2_RESULT_COMMIT,
    "oracle1_run_default": ORACLE1_RUN_DEFAULT,
    "oracle2_run_default": ORACLE2_RUN_DEFAULT,
    "original_domain": ORIGINAL_DOMAIN,
    "coverage_radius_m": COVERAGE_RADIUS_M,
    "focus_object_count": FOCUS_OBJECT_COUNT,
    "scientific_contract": SCIENTIFIC_CONTRACT,
    "fsg_terminal_stages": FSG_TERMINAL_STAGES,
    "cyclopean_first_rejection_reasons": CYCLOPEAN_FIRST_REJECTION_REASONS,
    "truth_subtypes": TRUTH_SUBTYPES,
    "demo_contract": DEMO_CONTRACT,
}


def public_digest() -> str:
    payload = json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def self_test() -> list[str]:
    fails: list[str] = []
    if not SCIENTIFIC_CONTRACT["read_only"]:
        fails.append("Oracle-3 must be read-only")
    if any(SCIENTIFIC_CONTRACT[k] != 0 for k in ("new_acquisitions", "new_fixations", "new_fusion")):
        fails.append("Oracle-3 may not add acquisitions, fixations, or fusion")
    if not SCIENTIFIC_CONTRACT["truth_allowed_only_after_controller_phase"]:
        fails.append("truth phase separation is required")
    if COVERAGE_RADIUS_M != 0.012:
        fails.append("coverage radius must remain 12 mm")
    if CYCLOPEAN_GRID_DEG != 0.10:
        fails.append("Cyclopean grid must remain 0.1 degree")
    if FOCUS_OBJECT_COUNT != 6:
        fails.append("focus set must contain six deterministic largest-deficit objects")
    if not DEMO_CONTRACT["posthoc_only"]:
        fails.append("demo must remain post-hoc")
    return fails


if __name__ == "__main__":
    bad = self_test()
    for item in bad:
        print("[classroom-oracle3-public] FAIL", item)
    print("[classroom-oracle3-public] self-test", "FAILED" if bad else "PASS", public_digest())
    raise SystemExit(bool(bad))
