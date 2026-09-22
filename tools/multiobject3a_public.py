"""Public contract for MultiObject-3a: select the next object from updated scene memory.

MultiObject-2d established that scene progress should continue even though the
scene-selected third object retains genuinely unseen territory for later revisit.
This step adds no fixation.  It repeats the scene-level selection rule on the
*updated* saved history, now including the third object's seed/growth views, and
excludes every object already instantiated in the current scene graph.

The next object is the uninstantiated positive instance id with the largest
accumulated valid-depth support over all saved scene observations.  Exact ties
use the smaller integer id.  No threshold, semantic priority, saliency model,
revisit scheduler or hand-picked id is introduced.
"""
from __future__ import annotations
import hashlib
import json

import multiobject2d_public as parent

SPEC_ID = "MultiObject3a-next-object-selection-v1"
PARENT_SPEC_ID = parent.SPEC_ID
SEED = parent.SEED
FIXTURE = parent.FIXTURE
NO_ACQUISITION = True
NEW_OBJECT_INSTANTIATED = False
NEXT_STAGE = "seed the selected fourth object with one prescribed fixation"

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent": PARENT_SPEC_ID,
    "question": (
        "Given the updated saved scene history after three persistent objects have been instantiated, "
        "which already-observed but uninstantiated object should receive the next seed fixation?"
    ),
    "fixture": FIXTURE,
    "seed": SEED,
    "fixed_head": True,
    "static_scene": True,
    "instantiated_object_source": (
        "consume the current object-id set from the MultiObject-2c scene graph reached through the "
        "completed MultiObject-2d parent; do not hard-code scene ids in this step"
    ),
    "no_acquisition": True,
    "new_object_instantiated": False,
    "candidate_rule": (
        "positive integer instance ids present with valid stereo depth in the complete saved scene "
        "history, excluding every id already instantiated in the current scene graph"
    ),
    "selection_rule": (
        "sum valid-depth sample support over the complete saved scene history for each candidate; "
        "select the largest accumulated support, breaking an exact tie by smaller integer object id"
    ),
    "evidence_scope": (
        "combine the previously saved MultiObject-1b2 scene history with the MultiObject-2b/2c "
        "selected-third-object history; no render, rerender or evaluator truth is added"
    ),
    "progress_contract": (
        "this is one scene-level decision only: select the next object from memory, then defer its "
        "seed fixation to the following increment; retained revisit states of existing objects do not block selection"
    ),
    "quality_contract": (
        "support counts are measurements and deterministic ordering evidence, not quality thresholds; "
        "no minimum support, semantic ranking, saliency score, revisit priority or tuned weight is introduced"
    ),
    "next_stage": NEXT_STAGE,
    "integrity_contract": [
        "MultiObject-2d and its scene ancestry are read only",
        "all currently instantiated object geometries remain byte-identical",
        "no Blender/Cycles acquisition is launched",
        "no surfel fusion, object growth, watchdog extension or revisit is run",
        "candidate support uses saved valid-depth evidence rather than mere visibility",
        "the selected id is computed from updated evidence and is not declared in advance",
        "existing ATTENTION_INCOMPLETE/measurement-partial objects remain persistent but do not block scene progress",
        "no evaluator truth, semantic ranking or automatic scheduler beyond this single selection is introduced",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
