"""Public contract for Cyclopean-1e: one epistemically selected fixation.

Cyclopean-1d separated shoreline that was truly NEVER_OBSERVED from shoreline
that had already been imaged but could not be measured in depth.  This step
uses that refined state once: exactly one new foveation may be selected from
EXTERIOR NEVER_OBSERVED shoreline, and no other refined state is eligible.
The FSG6f controller and stopping policy remain untouched.
"""
from __future__ import annotations
import hashlib
import json

import cyclopean1d_public as cyclopean1d

SPEC_ID = "Cyclopean1e-epistemic-gaze-v1"
PARENT_SPEC_ID = cyclopean1d.SPEC_ID
OBJECT_ID = cyclopean1d.OBJECT_ID
SEEDS = (2111,)
FIXTURE = cyclopean1d.FIXTURE
GRID_DEG_BY_PROFILE = dict(cyclopean1d.GRID_DEG_BY_PROFILE)
FUSION = dict(cyclopean1d.FUSION)
MAX_ADDED_FIXATIONS = 1

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent": PARENT_SPEC_ID,
    "question": (
        "If the refined Cyclopean-1d state is allowed to choose exactly one new "
        "foveation from genuinely NEVER_OBSERVED exterior shoreline, does it aim "
        "a useful look while excluding shoreline that was already seen but lacked depth?"
    ),
    "fixture": FIXTURE,
    "seeds": list(SEEDS),
    "fixed_head": True,
    "static_scene": True,
    "object_id": OBJECT_ID,
    "grid_deg_by_profile": GRID_DEG_BY_PROFILE,
    "fusion": FUSION,
    "candidate_state": "NEVER_OBSERVED",
    "excluded_states": [
        "OBSERVED_TARGET_NO_DEPTH",
        "OBSERVED_TARGET_WITH_DEPTH",
        "OBSERVED_NONTARGET_ONLY",
        "MIXED_OBSERVATION",
        "NO_RANGE_REFERENCE",
        "PHYSICAL_DEPTH_BREAK",
        "AMBIGUOUS",
    ],
    "selection_rule": (
        "among EXTERIOR shoreline cells refined by Cyclopean-1d as NEVER_OBSERVED, "
        "choose the cell with greatest inherited exterior border distance; ties use "
        "the cell nearest the tied plateau centroid, then raster y/x; if already visited, "
        "walk that same deterministic ordering to the first unvisited cell"
    ),
    "acquisition_rule": (
        "render exactly one fixation at the selected gaze; process it through the frozen "
        "Reality/FSG stereo path; an empty look is valid negative evidence under the "
        "existing Reality Check 2b contract"
    ),
    "quality_contract": (
        "structural experiment only; no coverage, surfel-gain or geometry number is a PASS gate"
    ),
    "integrity_contract": [
        "the completed Cyclopean-1d record and all ancestors are read only",
        "exactly zero or one fixation may be added, never more than one",
        "only EXTERIOR NEVER_OBSERVED shoreline is eligible for selection",
        "OBSERVED_TARGET_NO_DEPTH is explicitly ineligible for blind repetition",
        "the inherited chart, support footprint, fusion radius and stereo path are reused unchanged",
        "no evaluator truth is opened",
        "no mesh, morphology tuning, normal cue, texture threshold or new geometric tolerance is introduced",
        "no FSG6f policy, ranking or stopping rule is imported, modified or replaced",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
