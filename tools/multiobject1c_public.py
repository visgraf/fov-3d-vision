"""Public contract for MultiObject-1c: read-only object-143 epistemic audit.

MultiObject-1b2 revision 2 showed that object 143 grows coherently under the
frozen local controller but reaches the object-scoped watchdog before the
controller's own no_frontier stop.  This step does not extend the watchdog and
does not add another fixation.  It asks what the remaining object-143
shoreline means in the already-established cyclopean epistemic vocabulary.

Whatever the descriptive outcome, scene progress continues to the next-object
stage.  Object 143 may remain a persistent, partially measured entity and can
be revisited later.
"""
from __future__ import annotations
import hashlib
import json

import multiobject1b2_public as parent

SPEC_ID = "MultiObject1c-object143-epistemic-audit-v1"
PARENT_SPEC_ID = parent.SPEC_ID
SEED = parent.SEED
FIXTURE = parent.FIXTURE
OBJECT_ID_1 = parent.OBJECT_ID_1
OBJECT_ID_2 = parent.OBJECT_ID_2
OBJECT_IDS = parent.OBJECT_IDS
GRID_DEG = 0.1
FUSION = dict(parent.FUSION)
NO_ACQUISITION = True
NEXT_STAGE = "next-object discovery/selection"

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
        "After object 143 reaches the object-scoped watchdog while frozen FSG6f still "
        "returns continue, is the remaining cyclopean shoreline primarily territory "
        "that was never observed, or territory that was observed but not measured by stereo?"
    ),
    "fixture": FIXTURE,
    "seed": SEED,
    "fixed_head": True,
    "static_scene": True,
    "object_ids": list(OBJECT_IDS),
    "active_object": OBJECT_ID_2,
    "grid_deg": GRID_DEG,
    "fusion": FUSION,
    "no_acquisition": True,
    "scope": (
        "read-only audit of the completed MultiObject-1b2 object-143 record; no Blender, "
        "no added fixation, no watchdog extension, no controller change"
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
        "the audit describes object 143's unresolved remainder but never blocks scene progress; "
        "after the audit the declared next stage is next-object discovery/selection, while any "
        "remaining object-143 attention or measurement deficit is retained for possible revisit"
    ),
    "integrity_contract": [
        "the completed MultiObject-1b2 record and every source object are read only",
        "object 141 remains byte-identical and is not analyzed as the active target",
        "object 143 surface geometry is read only and remains pure id 143",
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
