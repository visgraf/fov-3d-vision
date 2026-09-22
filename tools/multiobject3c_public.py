"""Public contract for MultiObject-3c: grow the scene-selected fourth object.

MultiObject-3b consumed the second scene-memory decision and instantiated one
new foreground entity with one prescribed seed fixation. This step repeats the
already-established selected-object growth experiment on that newly seeded
entity while every previously instantiated scene object remains byte-for-byte
read only.

The target id and the pre-existing object-id set are consumed from the completed
MultiObject-3b parent; neither is hard-coded here. The exact generic target-label
adapter already introduced for MultiObject-2c is reused unchanged, as are frozen
FSG6f, the 12 mm association rule, the 5 degree local saccade lattice,
Reality-2b empty-look semantics, and the generic fixed-head scene renderer.
"""
from __future__ import annotations

import hashlib
import json

import fsg6f_public as frozen
import multiobject3b_public as parent

SPEC_ID = "MultiObject3c-grow-selected-object-v1"
PARENT_SPEC_ID = parent.SPEC_ID
FIXTURE = parent.FIXTURE
SEED = parent.SEED
TARGET_ALIAS_ID = frozen.OBJECT_ID
INSTRUMENT_ID = frozen.INSTRUMENT_ID
FUSION = dict(frozen.FUSION)
SURFACE_FRONTIER = dict(frozen.SURFACE_FRONTIER)
MIN_TARGET_POINTS = 100
SELECTED_OBJECT_WATCHDOG_FIXATIONS = 24  # engineering guardrail, including the 3b seed look
SCENE_RENDERER = "tools/scene_render_fix.py"
POLICY_ADAPTER = "tools/multiobject2c_policy.py"

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent": PARENT_SPEC_ID,
    "question": (
        "Can the same frozen selected-object growth machinery repeat on the object chosen and seeded by "
        "MultiObject-3a/3b while every previously instantiated scene object remains separate and byte-identical?"
    ),
    "fixture": FIXTURE,
    "seed": SEED,
    "fixed_head": True,
    "static_scene": True,
    "target_object_source": (
        "consume MultiObject-3b selected_object_id; do not hand-pick or hard-code the scene id in this step"
    ),
    "preexisting_object_source": (
        "consume MultiObject-3b existing_object_ids_before and live scene graph; do not hard-code scene ids"
    ),
    "growth_policy": (
        "reuse tools/multiobject2c_policy.py unchanged; it delegates to tools/fsg6f_frontier.py unchanged through "
        "a pure target-label adapter, presenting only the parent-selected scene id as frozen FSG6f target label 141"
    ),
    "history_scope": (
        "active growth begins at the prescribed MultiObject-3b seed observation; the earlier scene-memory "
        "observations used for selection and seed placement are not replayed as growth-policy history"
    ),
    "empty_look_semantics": (
        "fewer than 100 reconstructed selected-object points is valid negative evidence: record the binocular "
        "observation, fuse nothing, leave the selected-object map unchanged, and continue"
    ),
    "scientific_stop": "the frozen FSG6f policy returns stop/no_frontier",
    "watchdog": {
        "selected_object_fixations_total_max": SELECTED_OBJECT_WATCHDOG_FIXATIONS,
        "role": "engineering guardrail only; reaching it is not scientific success",
    },
    "texture_diagnostics": (
        "record per-look visible selected-object pixels, valid selected-object depth points, and recovered fraction; "
        "these measurements are descriptive only and never a policy, selection, stopping, or PASS gate"
    ),
    "quality_contract": (
        "structural repeatability experiment only; point gain, fixation count, stereo recovery, footprint overlap, "
        "coverage and geometry values are measurements, not PASS gates"
    ),
    "next_stage": (
        "audit the selected object's residual epistemic state and continue scene progress; revisit scheduling and "
        "broader scene policy remain deferred"
    ),
    "integrity_contract": [
        "the completed MultiObject-3b parent remains read only",
        "all previously instantiated object geometry sources remain byte-identical and are never fused",
        "only pixels with the parent-selected instance id may enter the selected-object surfel map",
        "the existing MultiObject-2c target-label adapter is reused unchanged",
        "FSG6f frontier/controller source and all numerical rules remain unchanged",
        "the frozen 12 mm FSG3/FSG6f fusion rule remains unchanged",
        "the generic scene renderer continues global acquisition numbering without rerendering history",
        "the existing rectification and stereo front end remain unchanged",
        "no evaluator truth or scene-geometry oracle is opened",
        "no automatic object discovery, revisit scheduler, scene scheduler, interpolation, mesh completion, or quality gate is introduced",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
