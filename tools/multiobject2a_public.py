"""Public contract for MultiObject-2a: choose the next scene object from saved evidence.

MultiObject-1c established that scene progress should continue even though object
143 retains unresolved attention/measurement residue.  This step introduces the
first scene-level selection decision, but deliberately no new acquisition.

The candidate set is formed only from positive oracle instance ids that already
appear with valid stereo depth in the saved scene-history observations and that
are not already instantiated foreground entities.  The next object is the
candidate with the largest accumulated valid-depth support; ties use the smaller
integer object id.  No threshold, semantic ranking, saliency model or hand-picked
object id is introduced.
"""
from __future__ import annotations
import hashlib
import json

import multiobject1c_public as parent

SPEC_ID = "MultiObject2a-next-object-selection-v1"
PARENT_SPEC_ID = parent.SPEC_ID
SEED = parent.SEED
FIXTURE = parent.FIXTURE
INSTANTIATED_OBJECT_IDS = tuple(parent.OBJECT_IDS)
NO_ACQUISITION = True
NEW_OBJECT_INSTANTIATED = False
NEXT_STAGE = "seed the selected next object with one prescribed fixation"

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent": PARENT_SPEC_ID,
    "question": (
        "Given the saved scene observations after objects 141 and 143 have been instantiated, "
        "which already-observed but uninstantiated object should receive the next seed fixation?"
    ),
    "fixture": FIXTURE,
    "seed": SEED,
    "fixed_head": True,
    "static_scene": True,
    "instantiated_object_ids": list(INSTANTIATED_OBJECT_IDS),
    "no_acquisition": True,
    "new_object_instantiated": False,
    "candidate_rule": (
        "positive integer instance ids present in saved scene-history observations with valid "
        "stereo depth, excluding all already-instantiated object ids"
    ),
    "selection_rule": (
        "sum valid-depth sample support over the saved scene-history observations for each "
        "candidate; select the largest accumulated support, breaking an exact tie by smaller "
        "integer object id"
    ),
    "evidence_scope": (
        "the saved object-143-stage scene-history observations already registered by the "
        "MultiObject-1c ancestry (global steps 18 through the final MultiObject-1b2 step); "
        "no render or evaluator truth is added"
    ),
    "quality_contract": (
        "candidate support counts are measurements and ordering evidence, not quality thresholds; "
        "no minimum support, saliency score, semantic priority or tuned ranking is introduced"
    ),
    "next_stage": NEXT_STAGE,
    "integrity_contract": [
        "MultiObject-1c and its entire scene ancestry are read only",
        "objects 141 and 143 remain instantiated and unchanged",
        "no Blender/Cycles acquisition is launched",
        "no surfel fusion, object growth, watchdog extension or revisit is run",
        "candidate support uses saved valid-depth evidence rather than mere visibility",
        "the selected object id is computed from evidence and is not declared or hand-picked in advance",
        "no evaluator truth, semantic scene oracle beyond the already-saved instance masks, or geometry oracle is opened",
        "no scene scheduler beyond this single next-object selection is introduced",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
