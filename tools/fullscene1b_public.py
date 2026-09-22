"""Public contract for FullScene-1b: seed the S0-selected next object with one fixation.

FullScene-1a froze the post-MultiObject-3h scene as initial condition S0 and
selected the sole next uninstantiated object under the established valid-depth
scene-memory rule.  FullScene-1b consumes that decision and takes exactly one
prescribed fixation to instantiate the selected object as a separate persistent
seed entity.

No scene scheduler, revisit, growth loop, semantic rule, quality gate or
evaluator truth is introduced.  The still-deferred local action of the prior
active object remains unexecuted.
"""
from __future__ import annotations

import hashlib
import json

import fullscene1a_public as parent
import multiobject1a_public as seed_base

SPEC_ID = "FullScene1b-seed-snapshot-selected-object-v1"
PARENT_SPEC_ID = parent.SPEC_ID
SEED = parent.SEED
FIXTURE = parent.FIXTURE
GRID_DEG = float(seed_base.GRID_DEG)
MAX_ADDED_FIXATIONS = 1
SCENE_RENDERER = "tools/scene_render_fix.py"
NEW_OBJECT_INSTANTIATED = True
NEXT_STAGE = "FullScene-1c: grow the newly seeded scene-selected object with the frozen local machinery"

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent": PARENT_SPEC_ID,
    "question": (
        "Can FullScene initial condition S0 turn its automatically selected next uninstantiated object "
        "into one clean persistent seed entity with exactly one prescribed fixation, while all existing "
        "scene objects and the deferred prior-object action remain untouched?"
    ),
    "principle": "Back to Occam + Bounded Boldness: one scene-level selection becomes one physical look",
    "fixture": FIXTURE,
    "seed": SEED,
    "fixed_head": True,
    "static_scene": True,
    "parent_state": (
        "consume the unique completed FullScene-1a S0 record; use its selected_object_id and current live "
        "scene graph, and leave its deferred prior-object local action unexecuted"
    ),
    "evidence_scope": (
        "reuse exactly the complete FullScene-1a declared scene-memory history through MultiObject-3h; "
        "do not rerender history and do not broaden backward into the older object-141 lineage"
    ),
    "seed_rule": (
        "for the FullScene-1a selected id, collect only saved valid-depth xyz evidence over the complete "
        "S0 history and reuse multiobject3b_seed.select_seed_from_saved_evidence, which in turn reuses the "
        "unchanged MultiObject-1a occupied-cell spherical-mean selector on the inherited 0.1-degree grid"
    ),
    "acquisition_rule": (
        "add exactly one new global fixation at max(S0 observation steps)+1 through the generic scene "
        "renderer; no prior fixation is rerendered"
    ),
    "scene_representation": (
        "retain every S0 persistent object as a separate read-only SURFEL_MAP entity and append the selected "
        "object as one separate SEED_SURFEL_PATCH entity on a shared cyclopean chart"
    ),
    "quality_contract": (
        "seed point count, visibility, valid-depth recovery, footprint area and overlap are diagnostics only; "
        "the historical low valid fraction of the selected object is not a gate and causes no special treatment"
    ),
    "next_stage": NEXT_STAGE,
    "integrity_contract": [
        "the FullScene-1a S0 parent and all consumed history remain byte-identical",
        "selected and instantiated object ids are consumed from S0 rather than hard-coded",
        "the complete S0 valid-depth evidence scope is reused for the prescribed seed gaze",
        "all pre-existing persistent object maps remain byte-identical and instance-id pure",
        "the deferred prior-object local action remains unexecuted",
        "exactly one new global fixation is added through tools/scene_render_fix.py",
        "the selected seed patch contains only the selected object id and is never fused into existing objects",
        "no local growth, revisit, epistemic handoff, automatic scene scheduling, semantic ranking or quality threshold is introduced",
        "evaluator truth remains closed",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
