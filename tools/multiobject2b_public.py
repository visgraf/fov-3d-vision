"""Public contract for MultiObject-2b: seed the object selected by scene memory.

MultiObject-2a made a read-only scene-level decision from accumulated valid-depth
support.  This step consumes that decision and adds exactly one new fixation to
instantiate the selected object as a third persistent foreground entity.

The selected id is not hand-picked here: it is read from the completed
MultiObject-2a parent.  The seed direction is derived only from the same saved
valid-depth evidence used by the parent selection, using the already-established
MultiObject-1a occupied-cell spherical-mean rule.  Existing objects 141 and 143
remain read-only.  No object growth or scene scheduler is introduced yet.
"""
from __future__ import annotations

import hashlib
import json

import multiobject2a_public as parent
import multiobject1a_public as seed_base

SPEC_ID = "MultiObject2b-seed-selected-object-v1"
PARENT_SPEC_ID = parent.SPEC_ID
SEED = parent.SEED
FIXTURE = parent.FIXTURE
GRID_DEG = float(seed_base.GRID_DEG)
EXISTING_OBJECT_IDS = tuple(parent.INSTANTIATED_OBJECT_IDS)
MAX_ADDED_FIXATIONS = 1
SCENE_RENDERER = "tools/scene_render_fix.py"
NEW_OBJECT_INSTANTIATED = True

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent": PARENT_SPEC_ID,
    "question": (
        "Can the object selected automatically by MultiObject-2a be turned into one clean "
        "third persistent foreground entity with exactly one prescribed fixation, while "
        "objects 141 and 143 remain unchanged?"
    ),
    "fixture": FIXTURE,
    "seed": SEED,
    "fixed_head": True,
    "static_scene": True,
    "existing_object_ids": list(EXISTING_OBJECT_IDS),
    "selected_object_source": (
        "consume MultiObject-2a selected_object_id; do not declare or hand-pick the id in this step"
    ),
    "seed_rule": (
        "collect saved valid-depth xyz samples for the parent-selected object over exactly the "
        "MultiObject-2a evidence scope, quantize directions on the inherited 0.1-degree grid, "
        "compute the spherical mean of occupied cells, and choose the occupied cell nearest that mean; "
        "reuse the unchanged MultiObject-1a seed selector"
    ),
    "acquisition_rule": (
        "add exactly one new global fixation at max(parent evidence steps)+1 using the generic "
        "scene renderer; never rerender the saved evidence history"
    ),
    "scene_representation": (
        "retain objects 141 and 143 as read-only SURFEL_MAP entities and add the selected object "
        "as one separate SEED_SURFEL_PATCH entity on the shared cyclopean chart"
    ),
    "quality_contract": (
        "structural seed experiment only; target-point count, overlap, footprint area and geometry "
        "are measurements, not PASS gates"
    ),
    "next_stage": (
        "grow the newly seeded third object independently; automatic scene scheduling beyond the "
        "already-completed one-object selection remains deferred"
    ),
    "integrity_contract": [
        "the completed MultiObject-2a selection is consumed exactly and remains read only",
        "the selected object id comes from the parent result rather than a hard-coded id",
        "objects 141 and 143 and their geometry sources remain byte-identical",
        "exactly one physical fixation maximum is added",
        "the seed gaze uses only prior valid-depth evidence for the parent-selected object",
        "the generic fixed-head scene renderer continues global acquisition numbering and does not rerender history",
        "the existing stereo front end is reused unchanged",
        "the selected object's seed patch contains only its own instance id; it is never fused into objects 141 or 143",
        "no evaluator truth is opened",
        "no growth loop, revisit loop, scheduler, semantic ranking, saliency model or quality gate is introduced",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
