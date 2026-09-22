"""Public contract for MultiObject-3h: one more local productivity step.

MultiObject-3g executed the first local action returned after the bounded
cyclopean handoff.  The controller remained live, but that action was mostly a
re-measurement: the measured novelty was small.  MultiObject-3h executes
exactly the one subsequent FSG6f action already recorded by MultiObject-3g,
measures its geometric novelty without introducing a productivity threshold,
queries frozen FSG6f exactly once more, and stops.
"""
from __future__ import annotations

import hashlib
import json

import multiobject3g_public as parent

SPEC_ID = "MultiObject3h-one-more-local-productivity-step-v1"
PARENT_SPEC_ID = parent.SPEC_ID
SEED = parent.SEED
FIXTURE = parent.FIXTURE
GRID_DEG = parent.GRID_DEG
FUSION = dict(parent.FUSION)
MIN_TARGET_POINTS = int(parent.MIN_TARGET_POINTS)
SCENE_RENDERER = parent.SCENE_RENDERER
POLICY_ADAPTER = parent.POLICY_ADAPTER
MAX_NEW_FIXATIONS = 1
SUBSEQUENT_POLICY_DECISIONS = 1

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent": PARENT_SPEC_ID,
    "question": (
        "Was MultiObject-3g's low geometric novelty merely one transitional local step, "
        "or does executing exactly the next already-returned frozen-FSG6f action again "
        "behave mainly as re-measurement rather than expansion?"
    ),
    "principle": "Bounded Boldness: take one more already-justified local step, measure novelty, then stop",
    "fixture": FIXTURE,
    "seed": SEED,
    "fixed_head": True,
    "static_scene": True,
    "required_parent_policy_status": "LOCAL_EXPLORATION_CONTINUES",
    "action_source": (
        "consume subsequent_local_policy_decision.next_gaze_deg from the completed MultiObject-3g record; "
        "replay that frozen decision exactly before rendering; never reselect or hand-pick the gaze"
    ),
    "action": (
        "render exactly one new globally numbered fixation through the generic scene renderer, process "
        "unchanged stereo, and apply inherited selected-object-only 12 mm fusion unless the existing "
        "fewer-than-100-target-points empty-look rule fires"
    ),
    "productivity_readout": (
        "report target recovery, matched/new surfels, novelty fraction, map gain, raw angular footprint "
        "change, range envelope change, and the same diagnostics from MultiObject-3g side by side; "
        "none is a gate or stopping threshold"
    ),
    "return_to_local_policy": (
        "append exactly this observation to the selected object's seed-scoped history, query unchanged "
        "MultiObject-2c/FSG6f once, record the returned decision, and do not execute it"
    ),
    "boundedness": {
        "new_fixations_max": MAX_NEW_FIXATIONS,
        "execute_parent_subsequent_action": True,
        "subsequent_local_policy_decisions": SUBSEQUENT_POLICY_DECISIONS,
        "execute_new_subsequent_action": False,
        "automatic_loop": False,
        "scene_scheduler": False,
        "revisit_scheduler": False,
    },
    "measurement_contract": (
        "novelty is measured, not defined by a new threshold: matched/new counts and fractions are outcomes only; "
        "the inherited <100 empty-look rule is the only measurement-count branch"
    ),
    "next_stage": "interpret two consecutive post-handoff local actions before FullScene-1 calibration",
    "integrity_contract": [
        "the completed MultiObject-3g record and every ancestor/history input remain read only",
        "the selected object id and next gaze are consumed from MultiObject-3g rather than hard-coded",
        "the MultiObject-3g subsequent FSG6f decision must replay exactly before its action is executed",
        "the generic scene renderer is used for exactly one new globally numbered fixation and no history is rerendered",
        "the frozen stereo path, 12 mm fusion rule and fewer-than-100 empty-look semantics are unchanged",
        "only valid points of the selected object may be fused; every pre-existing other object remains byte-identical",
        "the selected-object policy history remains seed-scoped and includes the epistemic handoff plus the first returned local action",
        "the already-frozen MultiObject-2c target-label adapter and FSG6f controller remain unchanged",
        "exactly one subsequent local-policy decision is recorded and its action is not executed",
        "productivity diagnostics are descriptive only; no novelty, recovery, map-gain or footprint threshold is introduced",
        "no evaluator truth, matcher change, interpolation, mesh completion, watchdog change, scheduler or automatic alternation is introduced",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
