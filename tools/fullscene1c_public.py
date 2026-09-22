"""Public contract for FullScene-1c: grow the object seeded by FullScene-1b.

FullScene-1b consumed the FullScene S0 selection and instantiated exactly one
new foreground entity with one prescribed seed fixation.  FullScene-1c applies
the already-established selected-object growth mechanism to that seed while
every previously persistent scene object remains byte-for-byte read only.

The target id and the pre-existing scene-object set are consumed from the
completed FullScene-1b parent; neither is hard-coded here.  The generic
MultiObject-2c target-label adapter is reused unchanged, as are frozen FSG6f,
the 12 mm association rule, the 5 degree local saccade lattice, Reality-2b
empty-look semantics, and the generic fixed-head scene renderer.
"""
from __future__ import annotations

import hashlib
import json

import fsg6f_public as frozen
import fullscene1b_public as parent

SPEC_ID = "FullScene1c-grow-seeded-selected-object-v1"
PARENT_SPEC_ID = parent.SPEC_ID
FIXTURE = parent.FIXTURE
SEED = parent.SEED
TARGET_ALIAS_ID = frozen.OBJECT_ID
INSTRUMENT_ID = frozen.INSTRUMENT_ID
FUSION = dict(frozen.FUSION)
SURFACE_FRONTIER = dict(frozen.SURFACE_FRONTIER)
MIN_TARGET_POINTS = 100
SELECTED_OBJECT_WATCHDOG_FIXATIONS = 24  # engineering guardrail, including the FullScene-1b seed look
SCENE_RENDERER = "tools/scene_render_fix.py"
POLICY_ADAPTER = "tools/multiobject2c_policy.py"
NEXT_STAGE = "FullScene-1d: audit the grown object's epistemic residue before returning to scene-level inventory"

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent": PARENT_SPEC_ID,
    "question": (
        "Can the frozen selected-object growth machinery grow the entity seeded by FullScene-1b while "
        "every pre-existing persistent scene object and the prior object's deferred local action remain untouched?"
    ),
    "principle": "freeze what we have; let the assembled observer act without adding a new policy",
    "fixture": FIXTURE,
    "seed": SEED,
    "fixed_head": True,
    "static_scene": True,
    "target_object_source": (
        "consume FullScene-1b selected_object_id; do not hand-pick or hard-code the scene id in this step"
    ),
    "preexisting_object_source": (
        "consume FullScene-1b existing_object_ids_before and its live scene graph; do not hard-code scene ids"
    ),
    "growth_policy": (
        "reuse tools/multiobject2c_policy.py unchanged; it delegates to tools/fsg6f_frontier.py unchanged through "
        "a pure target-label adapter, presenting only the parent-selected scene id as frozen FSG6f target label 141"
    ),
    "history_scope": (
        "active local growth begins at the saved FullScene-1b seed observation only; the older FullScene S0 "
        "scene-memory history used for scene selection and seed placement is not replayed as FSG6f growth history"
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
    "progress_diagnostics": (
        "record attention/control and geometric measurements separately: per-look visibility and valid depth, "
        "fusion matched/new counts, map growth, footprint changes, empty looks, frontier/controller state and stop reason; "
        "none becomes a combined productivity score or gate"
    ),
    "quality_contract": (
        "structural growth experiment only; point gain, fixation count, stereo recovery, novelty, footprint overlap, "
        "coverage and geometry values are measurements, not PASS gates"
    ),
    "next_stage": NEXT_STAGE,
    "integrity_contract": [
        "the completed FullScene-1b parent remains read only",
        "all pre-existing persistent object geometry sources remain byte-identical and are never fused",
        "the prior object's deferred local action remains unexecuted",
        "only pixels with the parent-selected instance id may enter the selected-object surfel map",
        "the existing MultiObject-2c target-label adapter is reused unchanged",
        "FSG6f frontier/controller source and all numerical rules remain unchanged",
        "the frozen 12 mm FSG3/FSG6f fusion rule remains unchanged",
        "the generic scene renderer continues global acquisition numbering from the FullScene-1b seed without rerendering history",
        "the existing rectification and stereo front end remain unchanged",
        "no evaluator truth or scene-geometry oracle is opened",
        "no epistemic handoff, automatic object discovery, revisit scheduler, scene scheduler, interpolation, mesh completion, semantic ranking, productivity threshold, or quality gate is introduced",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
