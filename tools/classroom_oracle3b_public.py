"""Public contract for Classroom-Oracle-3b: Gap Anatomy.

Oracle-3b is a post-hoc, read-only diagnostic over the completed Oracle-3
eligibility audit.  It changes no controller state and executes no policy.
Its purpose is to characterize the large COMPLEMENT_NONSHORELINE residue:
how far it lies from reconstructed angular support, how it decomposes into
connected missed-surface components, and what the saved observation history
says about those components.
"""
from __future__ import annotations

import hashlib
import json

SPEC_ID = "Classroom-Oracle-3b-Gap-Anatomy-v1"
PARENT_COMMIT = "9c13905"
ORACLE3_AUDIT_DEFAULT = "previews/classroom-oracle-3-audit"
ORACLE1_RUN_DEFAULT = "previews/classroom-oracle-1-full"
DEFAULT_OUT = "previews/classroom-oracle-3b-gap-anatomy"

TARGET_FIRST_REASON = "NOT_SHORELINE"
TARGET_SUBTYPE = "COMPLEMENT_NONSHORELINE"
FOCUS_SOURCE = "Oracle-3 focus_instance_ids (six largest Oracle-1 miss counts)"

SCIENTIFIC_CONTRACT = {
    "posthoc_only": True,
    "read_only": True,
    "controller_replay": False,
    "controller_action": False,
    "new_acquisitions": 0,
    "new_fixations": 0,
    "new_fusion": 0,
    "blender_launches": 0,
    "fsg6f_rule_modified": False,
    "cyclopean_rule_modified": False,
    "fusion_rule_modified": False,
    "watchdog_modified": False,
    "domain_modified": False,
    "no_quality_pass_fail_threshold": True,
    "focus_source": FOCUS_SOURCE,
    "truth_is_evaluation_only": True,
}

MEASUREMENTS = (
    "connected components on the frozen reachable-sample angular lattice",
    "8-connected Cyclopean dilation-ring depth from current angular support",
    "Euclidean angular distance to support and to shoreline",
    "component angular span and sample/cell counts",
    "distance from component centroid to nearest completed fixation",
    "saved observation-state composition on disconnected miss cells",
    "cumulative fraction of disconnected misses reached by k support-expansion rings",
)

DEMO_CONTRACT = {
    "posthoc_only": True,
    "overview_png": True,
    "focus_object_frames": True,
    "four_panel_anatomy": True,
    "mp4_when_available": True,
    "demo_md": True,
}

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent_commit": PARENT_COMMIT,
    "oracle3_audit_default": ORACLE3_AUDIT_DEFAULT,
    "oracle1_run_default": ORACLE1_RUN_DEFAULT,
    "default_out": DEFAULT_OUT,
    "target_first_reason": TARGET_FIRST_REASON,
    "target_subtype": TARGET_SUBTYPE,
    "scientific_contract": SCIENTIFIC_CONTRACT,
    "measurements": MEASUREMENTS,
    "demo_contract": DEMO_CONTRACT,
}


def public_digest() -> str:
    raw = json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def self_test() -> list[str]:
    fails: list[str] = []
    c = SCIENTIFIC_CONTRACT
    if not c["posthoc_only"] or not c["read_only"]:
        fails.append("Oracle-3b must be post-hoc and read-only")
    if c["controller_replay"] or c["controller_action"]:
        fails.append("Oracle-3b may not execute the controller")
    if any(c[k] != 0 for k in ("new_acquisitions", "new_fixations", "new_fusion", "blender_launches")):
        fails.append("Oracle-3b may not acquire, fixate, fuse, or launch Blender")
    if any(c[k] for k in ("fsg6f_rule_modified", "cyclopean_rule_modified", "fusion_rule_modified", "watchdog_modified", "domain_modified")):
        fails.append("Oracle-3b changes no scientific rule")
    if TARGET_FIRST_REASON != "NOT_SHORELINE" or TARGET_SUBTYPE != "COMPLEMENT_NONSHORELINE":
        fails.append("Oracle-3b must anatomize the Oracle-3 dominant residue")
    if not c["no_quality_pass_fail_threshold"]:
        fails.append("no numerical quality gate is allowed")
    return fails


if __name__ == "__main__":
    bad = self_test()
    for item in bad:
        print("[classroom-oracle3b-public] FAIL", item)
    print("[classroom-oracle3b-public] self-test", "FAILED" if bad else "PASS", public_digest())
    raise SystemExit(bool(bad))
