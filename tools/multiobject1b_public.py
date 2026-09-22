"""Public contract for MultiObject-1b: grow object 143 independently.

MultiObject-1a established coexistence: object 141 is a completed inherited surfel
entity and object 143 is one separate seed patch.  This step introduces exactly one
new difficulty: apply the already-established local single-object FSG6f growth
mechanism to object 143 while object 141 remains byte-for-byte read only.

The FSG6f policy is not copied or retuned.  A thin label adapter presents object 143
as the policy's historical single-object target label while mapping every other
instance to non-target.  Geometry, frontier rules, 12 mm fusion, 5 degree local
saccade step, and all FSG6f numerical constants remain frozen.  Empty target looks
retain the Reality-2b semantics: record the binocular observation, fuse nothing,
and let the unchanged policy reconsider.
"""
from __future__ import annotations

import hashlib
import json

import fsg6f_public as frozen
import multiobject1a_public as parent

SPEC_ID = "MultiObject1b-object143-growth-v1"
PARENT_SPEC_ID = parent.SPEC_ID
FIXTURE = parent.FIXTURE
SEED = parent.SEED
OBJECT_ID_1 = parent.OBJECT_ID_1
OBJECT_ID_2 = parent.OBJECT_ID_2
OBJECT_IDS = parent.OBJECT_IDS
TARGET_ALIAS_ID = frozen.OBJECT_ID
INSTRUMENT_ID = frozen.INSTRUMENT_ID
FUSION = dict(frozen.FUSION)
SURFACE_FRONTIER = dict(frozen.SURFACE_FRONTIER)
MIN_TARGET_POINTS = 100
OBJECT2_WATCHDOG_FIXATIONS = 24  # engineering guardrail, including the 1a seed look

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent": PARENT_SPEC_ID,
    "question": (
        "Can the frozen single-object FSG6f growth mechanism grow object 143 from "
        "its MultiObject-1a seed while object 141 remains a separate, byte-identical entity?"
    ),
    "fixture": FIXTURE,
    "seed": SEED,
    "fixed_head": True,
    "static_scene": True,
    "object_ids": list(OBJECT_IDS),
    "object_1_role": "inherited object-141 SURFEL_MAP remains read-only and is never fused",
    "object_2_role": "initialize from the MultiObject-1a seed patch and grow only id 143",
    "growth_policy": (
        "reuse tools/fsg6f_frontier.py unchanged through a pure instance-label adapter: "
        "143 is presented as the frozen FSG6f target label 141 and every other id is non-target"
    ),
    "history_scope": (
        "object-143 active growth begins at its prescribed MultiObject-1a seed observation; "
        "earlier incidental id-143 observations were used to choose that seed but are not replayed "
        "as growth-policy history in this transfer test"
    ),
    "empty_look_semantics": (
        "fewer than 100 reconstructed id-143 points is valid negative evidence: record the "
        "binocular observation, fuse nothing, keep the object-143 map unchanged, and continue"
    ),
    "scientific_stop": "the frozen FSG6f policy returns stop/no_frontier",
    "watchdog": {
        "object_143_fixations_total_max": OBJECT2_WATCHDOG_FIXATIONS,
        "role": "engineering guardrail only; reaching it is not scientific success",
    },
    "quality_contract": (
        "structural experiment only; point gain, number of looks, footprint overlap, coverage, "
        "and geometry values are measurements, not PASS gates"
    ),
    "next_stage": (
        "if independent growth is structurally sound, bring object 143 into the cyclopean "
        "completion machinery; automatic next-object discovery remains deferred"
    ),
    "integrity_contract": [
        "MultiObject-1a parent and the object-141 geometry source remain read only",
        "object 141 and object 143 stay separate entities and are never cross-fused",
        "only object-143 pixels may enter the object-143 surfel map",
        "FSG6f frontier/controller source and all its numerical rules remain unchanged",
        "the frozen 12 mm FSG3/FSG6f fusion rule remains unchanged",
        "the existing Reality renderer, rectification and stereo front end remain unchanged",
        "no evaluator truth or scene-geometry oracle is opened",
        "no automatic object discovery, object scheduler, mesh, interpolation, or scene-completion rule is introduced",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
