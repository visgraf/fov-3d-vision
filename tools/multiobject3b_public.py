"""Public contract for MultiObject-3b: seed the next object selected from updated scene memory.

MultiObject-3a made the second scene-level next-object decision from the updated
saved history while retaining unfinished existing objects for possible revisit.
This step consumes that decision and adds exactly one new fixation to instantiate
the selected object as a fourth persistent foreground entity.

The selected id and the already-instantiated id set are both consumed from the
completed MultiObject-3a parent. The seed direction is derived only from the
same combined valid-depth evidence scope used by MultiObject-3a, using the
already-established MultiObject-1a occupied-cell spherical-mean rule. All
pre-existing scene objects remain read only. No growth or revisit scheduler is
introduced yet.
"""
from __future__ import annotations

import hashlib
import json

import multiobject3a_public as parent
import multiobject1a_public as seed_base

SPEC_ID = "MultiObject3b-seed-selected-object-v1"
PARENT_SPEC_ID = parent.SPEC_ID
SEED = parent.SEED
FIXTURE = parent.FIXTURE
GRID_DEG = float(seed_base.GRID_DEG)
MAX_ADDED_FIXATIONS = 1
SCENE_RENDERER = "tools/scene_render_fix.py"
NEW_OBJECT_INSTANTIATED = True

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent": PARENT_SPEC_ID,
    "question": (
        "Can the next object selected automatically from updated scene memory be turned into one clean "
        "fourth persistent foreground entity with exactly one prescribed fixation, while every already-"
        "instantiated object remains unchanged?"
    ),
    "fixture": FIXTURE,
    "seed": SEED,
    "fixed_head": True,
    "static_scene": True,
    "existing_object_source": (
        "consume the instantiated_object_ids and live scene graph reached through MultiObject-3a; "
        "do not hard-code scene ids in this step"
    ),
    "selected_object_source": (
        "consume MultiObject-3a selected_object_id; do not declare or hand-pick the id in this step"
    ),
    "seed_rule": (
        "collect saved valid-depth xyz samples for the parent-selected object over exactly the complete "
        "MultiObject-3a evidence scope, quantize directions on the inherited 0.1-degree grid, compute the "
        "spherical mean of occupied cells, and choose the occupied cell nearest that mean; reuse the "
        "unchanged MultiObject-1a seed selector"
    ),
    "acquisition_rule": (
        "add exactly one new global fixation at max(parent evidence steps)+1 using the generic scene "
        "renderer; never rerender any saved scene history"
    ),
    "scene_representation": (
        "retain every already-instantiated object as a separate read-only SURFEL_MAP entity and add the "
        "parent-selected object as one separate SEED_SURFEL_PATCH entity on the shared cyclopean chart"
    ),
    "quality_contract": (
        "structural seed experiment only; seed point count, valid-depth fraction, footprint area and "
        "overlap are measurements, not PASS gates"
    ),
    "next_stage": (
        "grow the newly seeded fourth object independently; revisit scheduling and broader scene policy "
        "remain deferred"
    ),
    "integrity_contract": [
        "the completed MultiObject-3a selection and its scene ancestry remain read only",
        "the selected object id and instantiated object set come from the parent result rather than hard-coded ids",
        "all already-instantiated object geometry sources remain byte-identical",
        "the complete updated MultiObject-3a evidence scope is reused, not only the older half",
        "exactly one physical fixation maximum is added",
        "the seed gaze uses only prior valid-depth evidence for the parent-selected object",
        "the generic fixed-head scene renderer continues global acquisition numbering and does not rerender history",
        "the existing stereo front end is reused unchanged",
        "the selected object's seed patch contains only its own instance id and is never fused into existing objects",
        "no evaluator truth is opened",
        "no growth loop, revisit loop, semantic ranking, saliency model, quality gate or scheduler is introduced",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
