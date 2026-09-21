"""Public contract for Cyclopean-1f: iterate epistemic gaze to a fixed point."""
from __future__ import annotations

import hashlib
import json

import cyclopean1e_public as parent

SPEC_ID = "Cyclopean1f-epistemic-loop-v1"
PARENT_SPEC_ID = parent.SPEC_ID
OBJECT_ID = parent.OBJECT_ID
SEEDS = (2111,)
FIXTURE = parent.FIXTURE
GRID_DEG_BY_PROFILE = dict(parent.GRID_DEG_BY_PROFILE)
FUSION = dict(parent.FUSION)
WATCHDOG_TOTAL_FIXATIONS = 24

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent": PARENT_SPEC_ID,
    "question": (
        "If the Cyclopean-1e action rule is repeated without modification, does the "
        "observer exhaust eligible EXTERIOR NEVER_OBSERVED shoreline on seed 2111?"
    ),
    "fixture": FIXTURE,
    "seeds": list(SEEDS),
    "fixed_head": True,
    "static_scene": True,
    "object_id": OBJECT_ID,
    "grid_deg_by_profile": GRID_DEG_BY_PROFILE,
    "fusion": FUSION,
    "candidate_state": "NEVER_OBSERVED",
    "candidate_component_kind": "EXTERIOR",
    "selection_rule": "reuse Cyclopean-1e selector unchanged at every iteration",
    "scientific_stop": "NO_ELIGIBLE_EXTERIOR_NEVER_OBSERVED",
    "watchdog_total_fixations": WATCHDOG_TOTAL_FIXATIONS,
    "watchdog_role": "engineering guardrail only; reaching it is not scientific success",
    "empty_look_rule": "reuse Reality Check 2b negative-evidence semantics unchanged",
    "quality_contract": (
        "structural experiment only; no coverage, gain, accuracy, depth, or look-count number is a PASS gate"
    ),
    "integrity_contract": [
        "the completed Cyclopean-1e record and all ancestors are read only",
        "OBSERVED_TARGET_NO_DEPTH is never eligible for blind repetition",
        "INTERNAL shoreline is never eligible for this loop",
        "the inherited chart, support footprint, fusion radius and stereo path are reused unchanged",
        "the only scientific stop is absence of eligible EXTERIOR NEVER_OBSERVED shoreline",
        "the total-24-fixation watchdog is an engineering guardrail only",
        "no evaluator truth is opened",
        "no mesh, morphology tuning, normal cue, texture threshold or new geometric tolerance is introduced",
        "no FSG6f policy, ranking or stopping rule is imported, modified or replaced",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
