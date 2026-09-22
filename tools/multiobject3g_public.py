"""Public contract for MultiObject-3g: execute one returned local action.

MultiObject-3f established that the MultiObject-3e reactivation was primarily
attentional: moving the current gaze alone reproduced the returned local
FSG6f decision exactly, whereas updating geometry alone under the old gaze
reproduced the stop.  MultiObject-3g now asks the one remaining bounded
question: if we execute exactly that already-recorded local action, does local
exploration actually resume in the world?

Exactly one returned gaze is executed, its observation is processed with the
unchanged stereo/fusion semantics, frozen FSG6f is queried exactly once more,
and the newly returned action is recorded but not executed.
"""
from __future__ import annotations

import hashlib
import json

import multiobject3f_public as parent
import multiobject3e_public as state_parent

SPEC_ID = "MultiObject3g-one-returned-local-action-v1"
PARENT_SPEC_ID = parent.SPEC_ID
EXECUTION_PARENT_SPEC_ID = state_parent.SPEC_ID
SEED = parent.SEED
FIXTURE = parent.FIXTURE
GRID_DEG = state_parent.GRID_DEG
FUSION = dict(state_parent.FUSION)
MIN_TARGET_POINTS = int(state_parent.MIN_TARGET_POINTS)
SCENE_RENDERER = state_parent.SCENE_RENDERER
POLICY_ADAPTER = state_parent.POLICY_ADAPTER
MAX_NEW_FIXATIONS = 1
SUBSEQUENT_POLICY_DECISIONS = 1

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent": PARENT_SPEC_ID,
    "execution_parent": EXECUTION_PARENT_SPEC_ID,
    "question": (
        "After MultiObject-3f shows that attention alone is sufficient to reactivate frozen FSG6f, "
        "does executing exactly the already-returned local gaze produce a useful local observation "
        "and leave the same frozen controller with a meaningful subsequent decision?"
    ),
    "principle": "Bounded Boldness: execute one already-justified local action, then stop after one new decision",
    "fixture": FIXTURE,
    "seed": SEED,
    "fixed_head": True,
    "static_scene": True,
    "required_parent_reactivation_status": "LOCAL_POLICY_REACTIVATION_REPRODUCED",
    "action_source": (
        "consume returned_next_gaze_deg from the completed MultiObject-3f audit and cross-check it "
        "against the unexecuted MultiObject-3e returned_local_policy_decision; never hand-pick a gaze"
    ),
    "action": (
        "render exactly one new globally numbered fixation through the generic scene renderer, process "
        "it through the unchanged stereo path, and apply the inherited selected-object-only 12 mm fusion "
        "rule unless the existing fewer-than-100-points empty-look rule fires"
    ),
    "return_to_local_policy": (
        "append exactly the executed gaze and observation to the selected object's seed-scoped history, "
        "query the unchanged MultiObject-2c/FSG6f local policy exactly once, record the decision, and stop"
    ),
    "boundedness": {
        "new_fixations_max": MAX_NEW_FIXATIONS,
        "execute_parent_returned_action": True,
        "subsequent_local_policy_decisions": SUBSEQUENT_POLICY_DECISIONS,
        "execute_subsequent_local_action": False,
        "automatic_loop": False,
        "scene_scheduler": False,
        "revisit_scheduler": False,
    },
    "measurement_contract": (
        "target visibility, target depth recovery, empty-look status, matched/new surfels, map gain, and the "
        "subsequent FSG6f state are outcomes only; none becomes a new quality gate or threshold"
    ),
    "next_stage": "interpret the one executed returned action before any further local/global alternation",
    "integrity_contract": [
        "the completed MultiObject-3f audit and its MultiObject-3e execution state remain read only",
        "the selected object id and returned gaze are consumed from the parent chain rather than hard-coded",
        "the MultiObject-3e returned decision must replay exactly before its gaze is executed",
        "the MultiObject-3f attention-only causal result must still identify the same returned gaze",
        "the generic scene renderer is used for exactly one new globally numbered fixation and no history is rerendered",
        "the frozen stereo path, 12 mm fusion rule and fewer-than-100 empty-look semantics are unchanged",
        "only valid points of the selected object may be fused; all previously instantiated objects remain byte-identical",
        "the selected-object policy history remains seed-scoped and includes the prior epistemic handoff look",
        "the already-frozen MultiObject-2c target-label adapter and FSG6f controller remain unchanged",
        "exactly one subsequent local-policy decision is recorded and its action is not executed",
        "no evaluator truth, matcher change, interpolation, mesh completion, watchdog change, scheduler or automatic alternation is introduced",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
