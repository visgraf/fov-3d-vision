"""Public contract for MultiObject-1a: add one second-object seed entity.

Cyclopean-1g closes the present single-object branch for object 141.  This step
introduces exactly one new difficulty: coexistence of two foreground object
entities in the same fixed-head scene representation.  Object 141 is inherited
read-only.  A second declared object (id 143) receives one deterministic seed
foveation derived only from object-143 evidence that already appeared incidentally
in completed prediction-side observations.

No object growth, scene scheduler, automatic object discovery, or full-scene
completion policy is introduced here.
"""
from __future__ import annotations

import hashlib
import json

import cyclopean1g_public as parent

SPEC_ID = "MultiObject1a-second-object-seed-v1"
PARENT_SPEC_ID = parent.SPEC_ID
FIXTURE = parent.FIXTURE
SEED = 2111
OBJECT_ID_1 = parent.OBJECT_ID
OBJECT_ID_2 = 143
OBJECT_IDS = (OBJECT_ID_1, OBJECT_ID_2)
GRID_DEG = float(parent.GRID_DEG_BY_PROFILE["full"])
MAX_ADDED_FIXATIONS = 1

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent": PARENT_SPEC_ID,
    "question": (
        "Can the completed object-141 representation coexist with one newly seeded "
        "object-143 entity in the same fixed-head cyclopean scene record without "
        "cross-object contamination or any scene-level scheduling machinery?"
    ),
    "fixture": FIXTURE,
    "seed": SEED,
    "fixed_head": True,
    "static_scene": True,
    "object_ids": list(OBJECT_IDS),
    "object_1_role": "inherit completed object-141 surfel map read-only",
    "object_2_role": "create one object-143 seed surfel patch from exactly one new foveation",
    "second_object_seed_rule": (
        "object id 143 is declared in advance; collect valid depth samples labelled 143 "
        "from completed prediction-side observations only, quantize their head-frame "
        "directions on the inherited 0.1-degree full-profile grid, compute the spherical "
        "mean of occupied cells, and choose the occupied cell nearest that mean; this "
        "deterministic already-observed direction is the one prescribed seed gaze"
    ),
    "scene_representation": (
        "one scene manifest with two separate foreground entities: object 141 references "
        "its inherited surfel map, object 143 references a new seed patch; both also receive "
        "registered raw cyclopean angular footprints on one shared 0.1-degree scene chart"
    ),
    "quality_contract": (
        "structural experiment only; no target-point count, overlap, footprint size, "
        "coverage, or geometry number is a PASS gate"
    ),
    "next_stage": (
        "if the two entities coexist structurally, the next experiment may grow object 143 "
        "independently; automatic next-object discovery remains deferred"
    ),
    "integrity_contract": [
        "the completed Cyclopean-1g parent and all object-141 ancestry are read only",
        "object ids 141 and 143 remain separate entities; object 143 is never fused into object 141",
        "exactly one physical fixation maximum is added",
        "the second object id is declared before execution; this is not automatic object discovery",
        "the seed gaze is derived only from already-acquired prediction-side id-143 evidence",
        "the existing Reality/FSG renderer, rectification and stereo front end are reused unchanged",
        "no evaluator truth or scene-geometry oracle is opened",
        "no FSG6f policy, Cyclopean attention loop, object-growth loop, mesh, interpolation, or semantic scene scheduler is introduced",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
