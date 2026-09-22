"""Public contract for MultiObject-2c: grow the scene-selected third object.

MultiObject-2b consumed the scene-memory decision and instantiated exactly one
new foreground entity with one prescribed seed fixation.  This step introduces
one new difficulty only: apply the already-established FSG6f local growth
mechanism to that parent-selected entity while the pre-existing objects remain
byte-for-byte read only.

The target id is consumed from the completed MultiObject-2b parent; it is not
hard-coded here.  FSG6f is not copied or retuned.  A pure label adapter presents
the selected object under FSG6f's historical single-object target label and maps
all other scene ids to non-target for policy input only.  The actual surfel map
retains the selected scene instance id.  The frozen 12 mm fusion contract, 5 deg
local saccade lattice, Reality-2b empty-look semantics, and generic fixed-head
scene renderer are reused unchanged.
"""
from __future__ import annotations

import hashlib
import json

import fsg6f_public as frozen
import multiobject2b_public as parent

SPEC_ID = "MultiObject2c-grow-selected-object-v1"
PARENT_SPEC_ID = parent.SPEC_ID
FIXTURE = parent.FIXTURE
SEED = parent.SEED
PREEXISTING_OBJECT_IDS = tuple(parent.EXISTING_OBJECT_IDS)
TARGET_ALIAS_ID = frozen.OBJECT_ID
INSTRUMENT_ID = frozen.INSTRUMENT_ID
FUSION = dict(frozen.FUSION)
SURFACE_FRONTIER = dict(frozen.SURFACE_FRONTIER)
MIN_TARGET_POINTS = 100
OBJECT3_WATCHDOG_FIXATIONS = 24  # engineering guardrail, including the 2b seed look
SCENE_RENDERER = "tools/scene_render_fix.py"

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent": PARENT_SPEC_ID,
    "question": (
        "Can the frozen single-object FSG6f mechanism grow the object selected and seeded by "
        "MultiObject-2a/2b while the two pre-existing scene objects remain separate and byte-identical?"
    ),
    "fixture": FIXTURE,
    "seed": SEED,
    "fixed_head": True,
    "static_scene": True,
    "target_object_source": (
        "consume MultiObject-2b selected_object_id; do not hand-pick or hard-code the scene id in this step"
    ),
    "preexisting_objects": list(PREEXISTING_OBJECT_IDS),
    "growth_policy": (
        "reuse tools/fsg6f_frontier.py unchanged through a pure target-label adapter: the parent-selected "
        "scene id is presented as frozen FSG6f target label 141 and every other id is non-target"
    ),
    "history_scope": (
        "active growth begins at the prescribed MultiObject-2b seed observation; earlier observations used "
        "for scene selection and seed placement are not replayed as growth-policy history"
    ),
    "empty_look_semantics": (
        "fewer than 100 reconstructed target-object points is valid negative evidence: record the binocular "
        "observation, fuse nothing, leave the selected-object map unchanged, and continue"
    ),
    "scientific_stop": "the frozen FSG6f policy returns stop/no_frontier",
    "watchdog": {
        "selected_object_fixations_total_max": OBJECT3_WATCHDOG_FIXATIONS,
        "role": "engineering guardrail only; reaching it is not scientific success",
    },
    "texture_diagnostics": (
        "record per-look visible target pixels, valid target depth points, and recovered fraction; these are "
        "descriptive measurements of the textured object's stereo yield, never a policy or PASS gate"
    ),
    "quality_contract": (
        "structural growth experiment only; point gain, fixation count, stereo recovery, footprint overlap, "
        "coverage and geometry values are measurements, not PASS gates"
    ),
    "next_stage": (
        "use the completed or watchdog-bounded third-object record to continue scene progress; automatic "
        "scene scheduling and semantic prioritization remain deferred"
    ),
    "integrity_contract": [
        "the completed MultiObject-2b parent remains read only",
        "objects 141 and 143 remain byte-identical and are never fused",
        "only pixels with the parent-selected instance id may enter the selected-object surfel map",
        "FSG6f frontier/controller source and all numerical rules remain unchanged",
        "the frozen 12 mm FSG3/FSG6f fusion rule remains unchanged",
        "the generic scene renderer continues global acquisition numbering without rerendering history",
        "the existing rectification and stereo front end remain unchanged",
        "no evaluator truth or scene-geometry oracle is opened",
        "no automatic object discovery, scene scheduler, interpolation, mesh completion, or quality gate is introduced",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
