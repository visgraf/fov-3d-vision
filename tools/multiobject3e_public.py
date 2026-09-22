"""Public contract for MultiObject-3e: one bounded hierarchical epistemic handoff.

MultiObject-3d established that the first frozen FSG6f ``no_frontier`` stop
was policy exhaustion with genuinely unseen exterior territory still present.
This experiment tests exactly one interface between levels of the emerging
hierarchy: let the established cyclopean epistemic selector choose one unseen
look, acquire exactly one new fixation, update only the active object's map if
measurable, then ask frozen FSG6f for exactly one new decision and stop.

This is intentionally not a scheduler and not a rescue loop.  It is the
minimal executable test of local-geometry -> global-epistemic -> local-geometry
control transfer: bold in architecture, bounded in execution.
"""
from __future__ import annotations

import hashlib
import json

import multiobject3d_public as parent
import multiobject3c_public as growth_parent

SPEC_ID = "MultiObject3e-one-epistemic-handoff-v1"
PARENT_SPEC_ID = parent.SPEC_ID
SEED = parent.SEED
FIXTURE = parent.FIXTURE
GRID_DEG = parent.GRID_DEG
FUSION = dict(parent.FUSION)
MIN_TARGET_POINTS = int(growth_parent.MIN_TARGET_POINTS)
SCENE_RENDERER = growth_parent.SCENE_RENDERER
POLICY_ADAPTER = growth_parent.POLICY_ADAPTER
EPISTEMIC_SELECTOR = "tools/cyclopean1e_gaze.py"
MAX_HANDOFF_FIXATIONS = 1
RETURN_POLICY_DECISIONS = 1

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent": PARENT_SPEC_ID,
    "question": (
        "When the frozen local FSG6f controller has reproducibly stopped with no admissible candidate "
        "while exterior NEVER_OBSERVED territory remains, can the established cyclopean epistemic field "
        "supply exactly one missing gaze and hand control back to frozen FSG6f for one new decision?"
    ),
    "principle": "Bounded Boldness: bold architectural hypothesis, one bounded causal intervention",
    "fixture": FIXTURE,
    "seed": SEED,
    "fixed_head": True,
    "static_scene": True,
    "active_object_source": "consume selected_object_id from the completed MultiObject-3d parent; never hard-code it",
    "required_parent_interpretation": "POLICY_EXHAUSTED_WITH_UNSEEN_TERRITORY",
    "epistemic_selection": (
        "reuse cyclopean1e_gaze.select_epistemic_probe unchanged on the reconstructed MultiObject-3d "
        "cyclopean field: EXTERIOR NEVER_OBSERVED only, deepest inherited exterior distance first, "
        "deterministic tie-break, previously visited gazes excluded"
    ),
    "handoff_action": (
        "render exactly one fixation at the selected epistemic gaze through the generic scene renderer; "
        "process it through the frozen stereo path; under the inherited Reality-2b contract fewer than "
        "100 selected-object points is valid negative evidence and fuses nothing"
    ),
    "return_to_local_policy": (
        "append exactly that one gaze/observation to the selected object's seed-scoped history, preserve "
        "the same frozen FSG6f adapter and numerical rules, request exactly one next decision, record it, "
        "and stop without executing that decision"
    ),
    "boundedness": {
        "new_fixations_max": MAX_HANDOFF_FIXATIONS,
        "returned_local_policy_decisions": RETURN_POLICY_DECISIONS,
        "execute_returned_local_action": False,
        "automatic_loop": False,
        "scene_scheduler": False,
        "revisit_scheduler": False,
    },
    "measurement_contract": (
        "target visibility, target depth recovery, map gain, epistemic-cell changes and whether FSG6f "
        "reactivates are outcomes only; none is a PASS gate"
    ),
    "next_stage": "interpret the single handoff outcome before any second action",
    "integrity_contract": [
        "the completed MultiObject-3d audit and its completed MultiObject-3c scene parent are read only",
        "all pre-existing scene-object geometry sources remain byte-identical",
        "the active object id is consumed from the parent rather than hand-picked",
        "the established Cyclopean-1e selector is reused unchanged; no new gaze score or threshold is introduced",
        "the generic scene renderer is used for exactly one new globally numbered fixation and no history is rerendered",
        "the frozen 12 mm fusion rule and existing less-than-100 empty-look semantics are unchanged",
        "only the selected object's valid target points may be fused into its map",
        "the selected object's growth-policy history remains seed-scoped; old scene-memory observations are not imported",
        "the already-frozen MultiObject-2c target-label adapter and FSG6f controller remain unchanged",
        "the returned FSG6f decision is recorded but not executed",
        "no evaluator truth, matcher change, interpolation, mesh completion, quality gate or scheduler is introduced",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
