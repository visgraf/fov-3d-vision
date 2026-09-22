"""Public contract for MultiObject-2d: read-only epistemic audit of the scene-selected third object.

MultiObject-2c grew the object selected by scene memory with the frozen FSG6f
controller.  The run reached the object-scoped engineering watchdog while the
policy still returned continue.  This step does not extend the watchdog and
adds no fixation.  It asks what the remaining shoreline means in the existing
cyclopean epistemic vocabulary.

Whatever the descriptive result, scene progress continues to the next-object
selection stage.  The audited object remains persistent and may be revisited.
"""
from __future__ import annotations
import hashlib
import json

import multiobject2c_public as parent

SPEC_ID = "MultiObject2d-selected-object-epistemic-audit-v1"
PARENT_SPEC_ID = parent.SPEC_ID
SEED = parent.SEED
FIXTURE = parent.FIXTURE
GRID_DEG = 0.1
FUSION = dict(parent.FUSION)
NO_ACQUISITION = True
NEXT_STAGE = "next-object selection from updated scene memory"

REFINED_STATES = (
    "NEVER_OBSERVED",
    "OBSERVED_TARGET_NO_DEPTH",
    "OBSERVED_TARGET_WITH_DEPTH",
    "OBSERVED_NONTARGET_ONLY",
    "MIXED_OBSERVATION",
    "NO_RANGE_REFERENCE",
)

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent": PARENT_SPEC_ID,
    "question": (
        "After the scene-selected third object reaches its object-scoped watchdog while frozen FSG6f still "
        "returns continue, is the remaining cyclopean shoreline primarily genuinely unseen territory, "
        "seen-but-unmeasured target surface, or already observed boundary evidence?"
    ),
    "fixture": FIXTURE,
    "seed": SEED,
    "fixed_head": True,
    "static_scene": True,
    "active_object_source": "consume selected_object_id from the completed MultiObject-2c parent",
    "grid_deg": GRID_DEG,
    "fusion": FUSION,
    "no_acquisition": True,
    "scope": (
        "read-only audit of the completed MultiObject-2c selected-object record; no Blender, no added "
        "fixation, no watchdog extension and no controller change"
    ),
    "epistemic_states": {
        "NEVER_OBSERVED": "no completed supported projection carried target or non-target image evidence",
        "OBSERVED_TARGET_NO_DEPTH": "target image evidence exists but no projected target sample has valid stereo depth",
        "OBSERVED_TARGET_WITH_DEPTH": "target image evidence and valid target depth exist although the shoreline cell remains outside support",
        "OBSERVED_NONTARGET_ONLY": "only non-target image evidence exists under the local continuation-range hypothesis",
        "MIXED_OBSERVATION": "both target and non-target image evidence exist across completed views",
        "NO_RANGE_REFERENCE": "the inherited local target-boundary range is undefined",
    },
    "progress_contract": (
        "the audit describes the selected object's unresolved remainder but never blocks scene progress; "
        "after the audit the next stage is next-object selection from updated scene memory, while any "
        "remaining attention or measurement deficit is retained for possible revisit"
    ),
    "integrity_contract": [
        "the completed MultiObject-2c parent and every source object are read only",
        "the selected object id is consumed from the parent rather than hard-coded",
        "pre-existing scene objects remain byte-identical and are not analyzed as the active target",
        "selected-object surface geometry is read only and remains pure for its scene instance id",
        "no Blender/Cycles acquisition is launched",
        "no watchdog is raised and no new growth iteration is run",
        "the frozen 12 mm association semantics and existing 0.1 degree cyclopean scale are reused",
        "observation is separated from stereo measurement using saved oracle instance masks and saved valid masks",
        "no evaluator truth is opened",
        "no texture threshold, completion interpolation, layered occlusion model, matcher change or new geometric tolerance is introduced",
        "the result is descriptive; scene progress to the next-object stage is not quality-gated",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
