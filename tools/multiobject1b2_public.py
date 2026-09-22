"""Public contract for MultiObject-1b2: resume object-143 growth past the legacy renderer ceiling.

MultiObject-1b showed that the frozen FSG6f transfer mechanism grows object 143
cleanly, but its run was truncated after global step 23 because the frozen
Reality-2 acquisition entry point deliberately rejects step >=24.  This step
changes acquisition plumbing only: completed 1b observations are replayed from
disk without rerendering, a generic scene-fixation entry point is checked for
physical equivalence on the last legal legacy view, and growth then resumes at
global step 24 with the same object-scoped scientific contract.
"""
from __future__ import annotations

import hashlib
import json

import multiobject1b_public as parent

SPEC_ID = "MultiObject1b2-resume-object143-growth-v1"
PARENT_SPEC_ID = parent.SPEC_ID
FIXTURE = parent.FIXTURE
SEED = parent.SEED
OBJECT_ID_1 = parent.OBJECT_ID_1
OBJECT_ID_2 = parent.OBJECT_ID_2
OBJECT_IDS = parent.OBJECT_IDS
FUSION = dict(parent.FUSION)
MIN_TARGET_POINTS = parent.MIN_TARGET_POINTS
OBJECT2_WATCHDOG_FIXATIONS = parent.OBJECT2_WATCHDOG_FIXATIONS
LEGACY_LAST_GLOBAL_STEP = 23
RESUME_FIRST_GLOBAL_STEP = 24
SCENE_RENDERER = "tools/scene_render_fix.py"

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent": PARENT_SPEC_ID,
    "question": (
        "If the five valid MultiObject-1b growth looks are reused exactly and the obsolete "
        "Reality-2 global-step ceiling is removed only at the acquisition entry point, does "
        "frozen FSG6f continue growing object 143 to its own stop or the object-scoped watchdog?"
    ),
    "fixture": FIXTURE,
    "seed": SEED,
    "fixed_head": True,
    "static_scene": True,
    "object_ids": list(OBJECT_IDS),
    "partial_record": (
        "reuse the blocked MultiObject-1b state through global step 23; do not rerender its "
        "five successful growth fixations"
    ),
    "resume": "continue monotonically at global step 24; do not renumber the acquisition history",
    "renderer_change": (
        "introduce a generic scene-fixation entry point that preserves the Reality-2 physical "
        "scene, calibration, vergence, SPP, RNG seed function, Cycles backend and oracle masks, "
        "but does not encode Reality-2's experiment-specific global fixation ceiling"
    ),
    "renderer_equivalence": (
        "before any new scientific acquisition, rerender the saved step-23 gaze through the new "
        "entry point and require exact equality of calibration plus stored RGB/instance arrays"
    ),
    "growth_policy": "reuse multiobject1b_policy.py and frozen FSG6f unchanged",
    "empty_look_semantics": (
        "fewer than 100 reconstructed id-143 points is valid negative evidence: record the "
        "observation, fuse nothing, keep the object-143 map unchanged, and continue"
    ),
    "scientific_stop": "the frozen FSG6f policy returns stop/no_frontier",
    "watchdog": {
        "object_143_fixations_total_max": OBJECT2_WATCHDOG_FIXATIONS,
        "role": "engineering guardrail only; independent of global acquisition index",
    },
    "quality_contract": (
        "structural continuation only; point gain, look count, footprint overlap, stereo yield "
        "and geometry values are measurements, not PASS gates"
    ),
    "next_stage": (
        "if object-143 local growth completes structurally, move to its cyclopean completion; "
        "automatic next-object discovery remains deferred"
    ),
    "integrity_contract": [
        "MultiObject-1a parent and blocked MultiObject-1b partial record remain read only",
        "all completed partial fixations are replay-verified against their saved object-143 maps",
        "object 141 remains byte-identical and is never fused",
        "only id-143 pixels may enter the object-143 surfel map",
        "multiobject1b_policy.py and frozen FSG6f remain unchanged",
        "the frozen 12 mm fusion rule remains unchanged",
        "the new renderer changes scheduling only, not the physical instrument",
        "no evaluator truth or scene-geometry oracle is opened by prediction code",
        "no automatic object discovery, scene scheduler, interpolation or completion rule is introduced",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
