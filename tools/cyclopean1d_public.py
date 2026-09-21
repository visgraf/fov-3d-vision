"""Public contract for Cyclopean-1d: observation-versus-measurement audit.

Cyclopean-1c showed that a topology-driven fixation can fill a deep bay, but
left a tiny residual where RGB/instance observation existed while frozen stereo
returned no valid depth.  This step is deliberately read-only.  It refines only
the epistemic meaning of shoreline cells that Cyclopean-1b would call
UNOBSERVED; it adds no fixation and changes no controller or stopping rule.
"""
from __future__ import annotations
import hashlib
import json

import cyclopean1c_public as cyclopean1c

SPEC_ID = "Cyclopean1d-observation-measurement-audit-v1"
PARENT_SPEC_ID = cyclopean1c.SPEC_ID
OBJECT_ID = cyclopean1c.OBJECT_ID
SEEDS = (2111,)
FIXTURE = cyclopean1c.FIXTURE
GRID_DEG_BY_PROFILE = dict(cyclopean1c.GRID_DEG_BY_PROFILE)
FUSION = dict(cyclopean1c.FUSION)
NO_ACQUISITION = True

REFINED_UNOBSERVED_STATES = (
    "NEVER_OBSERVED",
    "OBSERVED_TARGET_NO_DEPTH",
    "OBSERVED_TARGET_WITH_DEPTH",
    "OBSERVED_NONTARGET_ONLY",
    "MIXED_OBSERVATION",
    "NO_RANGE_REFERENCE",
)

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent": PARENT_SPEC_ID,
    "question": (
        "After the one Cyclopean-1c bay probe, which shoreline cells that the "
        "existing boundary audit still calls UNOBSERVED were truly never imaged, "
        "and which were imaged as target but yielded no valid stereo depth?"
    ),
    "fixture": FIXTURE,
    "seeds": list(SEEDS),
    "fixed_head": True,
    "static_scene": True,
    "object_id": OBJECT_ID,
    "grid_deg_by_profile": GRID_DEG_BY_PROFILE,
    "fusion": FUSION,
    "scope": (
        "refine only final shoreline cells whose frozen Cyclopean-1b state is "
        "UNOBSERVED; preserve PHYSICAL_DEPTH_BREAK and AMBIGUOUS semantics"
    ),
    "observation_definition": (
        "a continuation test point at the inherited local target-boundary range "
        "projects into the completed left rectified core at a calibration-supported "
        "pixel labelled with the target instance, regardless of stereo validity"
    ),
    "measurement_definition": (
        "the same projected target-labelled pixel also satisfies the already-saved "
        "frozen stereo valid mask; observation and depth measurement are therefore "
        "separate fields"
    ),
    "continuation_test_point": (
        "for one UNOBSERVED shoreline cell, use that cell's cyclopean ray and the "
        "existing Cyclopean-1b local target-range median. This point is only a "
        "projection hypothesis for reading past images; it is not fused geometry"
    ),
    "refined_states": {
        "NEVER_OBSERVED": "no completed supported projection carried target or non-target image evidence",
        "OBSERVED_TARGET_NO_DEPTH": "target image evidence exists but no projected target sample has valid stereo depth",
        "OBSERVED_TARGET_WITH_DEPTH": "target image evidence and valid target depth both exist although the cell remains outside support",
        "OBSERVED_NONTARGET_ONLY": "only non-target image evidence exists under the continuation projection hypothesis",
        "MIXED_OBSERVATION": "both target and non-target image evidence exist across completed views",
        "NO_RANGE_REFERENCE": "the inherited local target-boundary range is undefined, so no continuation projection is made",
    },
    "quality_contract": (
        "read-only descriptive audit; no state is a PASS gate and no refined state "
        "selects a fixation or changes stopping"
    ),
    "integrity_contract": [
        "the completed Cyclopean-1c record and every ancestor are read only",
        "no Blender/Cycles acquisition is launched",
        "no evaluator truth is opened",
        "the exact inherited chart, support footprint, stereo valid masks and 12 mm boundary semantics are reused",
        "image observation is explicitly separated from valid stereo depth",
        "only existing oracle instance masks already admitted by the project are used as segmentation evidence",
        "no mesh, morphology tuning, minimum-arc pruning, normal cue, texture threshold or new geometric tolerance is introduced",
        "no FSG6f policy, ranking or stopping rule is imported, modified or replaced",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
