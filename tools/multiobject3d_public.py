"""Public contract for MultiObject-3d: epistemic audit of a frozen-policy stop.

MultiObject-3c grew the object selected and seeded by scene memory with the same
unchanged selected-object machinery used previously.  For the first time in the
multi-object series the frozen FSG6f policy reached its own ``no_frontier`` stop
before the engineering watchdog, while its final trace still reported OPEN 3D
frontier voxels and zero admissible candidates.

This step is read-only.  It asks whether that stop coincides with attention
completion or instead with policy exhaustion while genuinely unseen territory
remains.  It also relates the final frozen 3D frontier state to the established
cyclopean epistemic field without changing either representation.
"""
from __future__ import annotations

import hashlib
import json

import multiobject3c_public as parent

SPEC_ID = "MultiObject3d-selected-object-epistemic-stop-audit-v1"
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
        "When frozen FSG6f stops on no_frontier with no admissible candidate but OPEN frontier voxels "
        "still present, is the selected object's cyclopean remainder attention-complete, primarily "
        "seen-but-unmeasured, or does genuinely unseen territory remain beyond the policy's reach?"
    ),
    "fixture": FIXTURE,
    "seed": SEED,
    "fixed_head": True,
    "static_scene": True,
    "active_object_source": "consume selected_object_id from the completed MultiObject-3c parent",
    "grid_deg": GRID_DEG,
    "fusion": FUSION,
    "no_acquisition": True,
    "scope": (
        "read-only audit of the completed MultiObject-3c selected-object record; no Blender, no added "
        "fixation, no watchdog extension, no controller change and no rescue action"
    ),
    "policy_stop_relation": (
        "replay the final frozen FSG6f decision exactly from saved observations and the final selected-object map; "
        "then angularly locate its 3D look-ahead frontier targets on the unchanged 0.1 degree cyclopean chart "
        "and report which epistemic cells they coincide with. This relation is descriptive and adds no threshold."
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
        "the audit may distinguish attention completion from policy exhaustion, but it never blocks scene progress; "
        "after the audit the next stage is next-object selection from updated scene memory, while unresolved "
        "territory is retained for possible revisit"
    ),
    "integrity_contract": [
        "the completed MultiObject-3c parent and every scene-object geometry source are read only",
        "the selected object id is consumed from the parent rather than hard-coded",
        "the parent must be the declared no_frontier scientific stop, not a watchdog termination",
        "the saved selected-object observation history is replayed without rerendering",
        "the final frozen FSG6f decision is reconstructed and must match the saved policy trace before interpretation",
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
