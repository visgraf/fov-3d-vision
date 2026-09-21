"""Public contract for Cyclopean-1g: one re-centered measurement probe.

Cyclopean-1f exhausted genuinely NEVER_OBSERVED exterior shoreline on seed 2111.
The remaining dominant internal residue is OBSERVED_TARGET_NO_DEPTH: the target
was imaged, but frozen stereo returned no valid depth there.  This step gives
that residue exactly one deliberately different measurement by re-centering the
fovea on it.  Whatever happens, the experiment stops after this one look and the
single-object rescue branch is deferred so the project can move to multiple
objects.
"""
from __future__ import annotations

import hashlib
import json

import cyclopean1f_public as parent

SPEC_ID = "Cyclopean1g-recentered-measurement-v1"
PARENT_SPEC_ID = parent.SPEC_ID
OBJECT_ID = parent.OBJECT_ID
SEEDS = (2111,)
FIXTURE = parent.FIXTURE
GRID_DEG_BY_PROFILE = dict(parent.GRID_DEG_BY_PROFILE)
FUSION = dict(parent.FUSION)
MAX_ADDED_FIXATIONS = 1

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent": PARENT_SPEC_ID,
    "question": (
        "If the dominant INTERNAL OBSERVED_TARGET_NO_DEPTH residue is placed at "
        "the foveal/tangent-chart centre for one deliberately re-centered look, "
        "does the frozen stereo instrument recover valid target depth there?"
    ),
    "fixture": FIXTURE,
    "seeds": list(SEEDS),
    "fixed_head": True,
    "static_scene": True,
    "object_id": OBJECT_ID,
    "grid_deg_by_profile": GRID_DEG_BY_PROFILE,
    "fusion": FUSION,
    "candidate_state": "OBSERVED_TARGET_NO_DEPTH",
    "candidate_component_kind": "INTERNAL",
    "selection_rule": (
        "choose the INTERNAL component containing the most OBSERVED_TARGET_NO_DEPTH "
        "shoreline cells; within it choose the no-depth cell nearest their spherical-chart "
        "centroid, then raster y/x; if that exact gaze was already visited, walk the same "
        "centroid-distance ordering to the first unvisited no-depth cell"
    ),
    "measurement_change": (
        "re-center the existing residue on the foveal/tangent-chart centre; keep the "
        "frozen Reality/FSG stereo front end, vergence/render settings, fusion scale and scene unchanged"
    ),
    "outcomes": ["DEPTH_RECOVERED", "DEPTH_STILL_ABSENT"],
    "outcome_rule": (
        "DEPTH_RECOVERED iff the new saved observation yields valid target depth for at least "
        "one of the pre-probe OBSERVED_TARGET_NO_DEPTH cells in the selected component; otherwise "
        "DEPTH_STILL_ABSENT"
    ),
    "branch_disposition": (
        "stop after this one measurement regardless of outcome; if depth is still absent, defer "
        "the instrument-limited case for future work and move next to multiple objects"
    ),
    "quality_contract": (
        "structural/diagnostic experiment only; no recovered-cell count, surfel gain, coverage, "
        "accuracy, or geometry number is a PASS gate"
    ),
    "integrity_contract": [
        "the completed Cyclopean-1f record and all ancestors are read only",
        "exactly one fixation maximum may be added",
        "only INTERNAL OBSERVED_TARGET_NO_DEPTH shoreline is eligible",
        "NEVER_OBSERVED is not eligible in this experiment",
        "the only deliberate acquisition change is foveal re-centering of the residue",
        "the frozen chart, support footprint, stereo front end, vergence/render settings and 12 mm fusion are reused unchanged",
        "the result is reported as DEPTH_RECOVERED or DEPTH_STILL_ABSENT without a quality gate",
        "no repeated rescue loop is allowed regardless of outcome",
        "no evaluator truth is opened",
        "no mesh, interpolation, learned matcher, morphology tuning, normal cue, texture threshold or new geometric tolerance is introduced",
        "no FSG6f policy, ranking or stopping rule is modified or consulted",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
