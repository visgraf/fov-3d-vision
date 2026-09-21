"""Public contract for Cyclopean-1c: one probe into the deepest unresolved bay.

Cyclopean-1b showed that seed 2111 contains one dominant exterior-connected
UNOBSERVED bay.  This step makes exactly one new foveation chosen from that
already-measured spherical structure.  It does not change FSG6f or the stopping
policy.
"""
from __future__ import annotations
import hashlib
import json

import cyclopean1b_public as cyclopean1b

SPEC_ID = "Cyclopean1c-deep-bay-probe-v1"
PARENT_SPEC_ID = cyclopean1b.SPEC_ID
OBJECT_ID = cyclopean1b.OBJECT_ID
SEEDS = (2111,)
FIXTURE = cyclopean1b.FIXTURE
GRID_DEG_BY_PROFILE = dict(cyclopean1b.GRID_DEG_BY_PROFILE)
FUSION = dict(cyclopean1b.FUSION)
MAX_ADDED_FIXATIONS = 1

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent": PARENT_SPEC_ID,
    "question": (
        "If the dominant exterior-connected UNOBSERVED bay in seed 2111 is "
        "foveated once at its deepest cyclopean complement cell, does that one "
        "look acquire useful target surface and reduce the unresolved bay without "
        "changing FSG6f or the stopping policy?"
    ),
    "fixture": FIXTURE,
    "seeds": list(SEEDS),
    "fixed_head": True,
    "static_scene": True,
    "object_id": OBJECT_ID,
    "grid_deg_by_profile": GRID_DEG_BY_PROFILE,
    "fusion": FUSION,
    "bay_definition": (
        "an EXTERIOR complement component whose shoreline contains at least one "
        "UNOBSERVED cell under the frozen Cyclopean-1b semantics"
    ),
    "component_rule": (
        "choose the eligible exterior component whose UNOBSERVED shoreline "
        "reaches the greatest inherited exterior border distance; ties use more "
        "UNOBSERVED shoreline cells, then smaller component id"
    ),
    "probe_rule": (
        "inside that component choose a complement cell with greatest inherited "
        "8-connected border distance; if several tie, choose the cell nearest "
        "their raster centroid; if that exact gaze was already visited, walk the "
        "same deterministic distance ordering until the first unvisited cell"
    ),
    "quality_contract": (
        "observational only; report target points, map growth, and before/after "
        "bay structure. No tuned numerical reconstruction-quality PASS gate."
    ),
    "integrity_contract": [
        "the completed Cyclopean-1b parent and its Cyclopean-1a ancestry are read only",
        "only seed 2111 is scheduled",
        "no evaluator truth is opened by selection, acquisition, fusion or analysis",
        "the exact inherited chart scale, support footprint and 12 mm FSG3 fusion scale are reused",
        "FSG6f and all earlier Reality/Cyclopean scientific sources are not modified or copied",
        "at most one physical fixation is added",
        "an empty probe is valid negative evidence and fuses no target points",
        "a fused target patch is replay-idempotent and preserves target-map purity",
        "no mesh, hole fill, morphology tuning, bay threshold, new ranking family or stopping-rule change is introduced",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
