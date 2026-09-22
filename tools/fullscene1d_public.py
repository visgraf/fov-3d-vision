"""Public contract for FullScene-1d: read-only epistemic audit of object 144's local stop.

FullScene-1c grew the object dynamically selected and seeded by FullScene-1a/1b
with the frozen selected-object machinery.  The local controller then reached a
genuine ``no_frontier`` scientific stop before its watchdog, with zero OPEN
frontier entries: every remaining frontier entry was boundary-resolved.

FullScene-1d does not act.  It asks whether that locally resolved stop also
corresponds to epistemic/measurement resolution of the grown object, or whether
the cyclopean field still contains unseen or seen-but-unmeasured residue.
"""
from __future__ import annotations

import hashlib
import json

import fullscene1c_public as parent

SPEC_ID = "FullScene1d-selected-object-epistemic-audit-v1"
PARENT_SPEC_ID = parent.SPEC_ID
FIXTURE = parent.FIXTURE
SEED = parent.SEED
GRID_DEG = 0.1
FUSION = dict(parent.FUSION)
NO_ACQUISITION = True
AUDIT_HISTORY_SCOPE = "FullScene-1b seed plus FullScene-1c local-growth observations only"
NEXT_STAGE = "FullScene-1e: return to scene inventory and recompute known uninstantiated candidates"

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent": PARENT_SPEC_ID,
    "question": (
        "When FullScene-1c reaches no_frontier with zero OPEN frontier entries, does that locally resolved "
        "stop coincide with attention/measurement resolution, or does epistemic residue remain around the "
        "grown selected object?"
    ),
    "principle": "read the residue; do not rescue it",
    "fixture": FIXTURE,
    "seed": SEED,
    "fixed_head": True,
    "static_scene": True,
    "target_object_source": "consume selected_object_id from the completed FullScene-1c parent; never hard-code a scene id",
    "parent_stop_required": (
        "genuine frozen-policy no_frontier scientific stop before watchdog, with final frontier_open_count == 0"
    ),
    "audit_history_scope": AUDIT_HISTORY_SCOPE,
    "audit_semantics": (
        "reuse the established MultiObject-3d / Cyclopean-1b / Cyclopean-1d audit machinery unchanged: "
        "0.1 degree cyclopean chart, 12 mm association semantics, shoreline classification, and observation-vs-depth refinement"
    ),
    "refined_states": [
        "NEVER_OBSERVED",
        "OBSERVED_TARGET_NO_DEPTH",
        "OBSERVED_TARGET_WITH_DEPTH",
        "OBSERVED_NONTARGET_ONLY",
        "MIXED_OBSERVATION",
        "NO_RANGE_REFERENCE",
    ],
    "interpretation": {
        "attention_debt": "exterior NEVER_OBSERVED > 0",
        "measurement_debt": "no exterior NEVER_OBSERVED, but OBSERVED_TARGET_NO_DEPTH > 0",
        "locally_resolved": "describes only the frozen 3D frontier state; it is not object completeness",
    },
    "scope": (
        "strictly read-only audit of the completed FullScene-1c selected-object record; no Blender, no fixation, "
        "no fusion, no growth, no handoff, no scheduler, no revisit action and no evaluator truth"
    ),
    "next_stage": NEXT_STAGE,
    "integrity_contract": [
        "the completed FullScene-1c parent and every scene-object geometry source remain byte-identical",
        "the selected object id and scene object set are consumed from the parent rather than hard-coded",
        "the parent must be the declared no_frontier scientific stop reached before its engineering watchdog",
        "the saved final policy trace must have zero OPEN frontier entries and be replayed exactly before interpretation",
        "the saved FullScene-1b seed plus FullScene-1c local observations are replayed without rerendering",
        "older S0 scene-memory observations are not added to the object-scoped audit in this increment",
        "the established MultiObject-3d epistemic helper machinery is reused rather than copied or retuned",
        "observation is separated from stereo measurement using saved instance masks and saved valid masks",
        "the frozen 12 mm association semantics and existing 0.1 degree cyclopean scale are reused",
        "the prior object's deferred local action remains unexecuted",
        "no evaluator truth, new threshold, interpolation, matcher change, completion model, or quality gate is introduced",
        "scene progress is not gated by the audit result; the next stage is a separate return to scene inventory",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
