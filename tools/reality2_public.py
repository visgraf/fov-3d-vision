"""Public contract for Reality Check 2.

Reality Check 1 showed coherent geometry where the observer looked, but both
records were interrupted by the inherited six-fixation experimental limit while
FSG6f still reported CONTINUE.  Reality Check 2 asks the literal follow-up:
continue those exact saved records, without rerendering their first six views,
until the frozen FSG6f policy says ``no_frontier``.

The only new bound is a defensive watchdog.  It is not a quality criterion and
reaching it is an observation, not a scientific FAIL.
"""
from __future__ import annotations
import hashlib
import json
import reality1_public as parent
import fsg6f_public as frozen

SPEC_ID = "RealityCheck2-continue-until-no-frontier-v1"
PARENT_SPEC_ID = parent.SPEC_ID
INSTRUMENT_ID = parent.INSTRUMENT_ID
FROZEN_POLICY_ID = parent.FROZEN_POLICY_ID
OBJECT_ID = parent.OBJECT_ID
BACKGROUND_IDS = tuple(parent.BACKGROUND_IDS)
FIXTURE = parent.FIXTURE
SEEDS = tuple(parent.SEEDS)
SEED_GAZE_DEG = tuple(parent.SEED_GAZE_DEG)
VERGENCE_DISTANCE_M = parent.VERGENCE_DISTANCE_M
DEFAULT_SPP = dict(parent.DEFAULT_SPP)
FUSION = dict(parent.FUSION)
PARENT_FIXATIONS = parent.MAX_FIXATIONS

# Engineering guard only.  Scientific stopping is frozen FSG6f ``no_frontier``.
# Four times the old experimental interruption gives generous room while keeping
# an accidental non-terminating run bounded.
WATCHDOG_TOTAL_FIXATIONS = 4 * PARENT_FIXATIONS

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent_reality_check": PARENT_SPEC_ID,
    "question": "If the exact Reality Check 1 state is not interrupted after six looks, does frozen FSG6f eventually finish usefully and stop by no_frontier?",
    "fixture": FIXTURE,
    "seeds": list(SEEDS),
    "seed_gaze_deg": list(SEED_GAZE_DEG),
    "fixed_head": True,
    "static_scene": True,
    "oracle_instance_segmentation": True,
    "object_id": OBJECT_ID,
    "background_ids": list(BACKGROUND_IDS),
    "instrument": INSTRUMENT_ID,
    "frozen_object_policy": FROZEN_POLICY_ID,
    "prescribed_vergence_distance_m": VERGENCE_DISTANCE_M,
    "spp": DEFAULT_SPP,
    "fusion": FUSION,
    "parent_fixations_reused_without_rerender": PARENT_FIXATIONS,
    "scientific_stopping_rule": "frozen FSG6f no_frontier",
    "watchdog_total_fixations": WATCHDOG_TOTAL_FIXATIONS,
    "watchdog_role": "engineering guard only; reaching it is descriptive, not a numerical quality or integrity failure",
    "quality_contract": "observational; report completion, coverage, geometry, efficiency and seed convergence without a tuned numerical PASS threshold",
    "integrity_contract": [
        "exact saved Reality Check 1 parent state is reused; first six views are not rerendered",
        "prediction does not open evaluator truth",
        "map contains only target instance",
        "every newly fused patch is replay-idempotent",
        "no repeated physical fixation",
        "frozen FSG6f policy imported rather than copied",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def render_seed(seed: int, yaw_deg: float, pitch_deg: float, eye_id: int) -> int:
    """Delegate exactly to the corrected Reality Check 1 physical-view seed."""
    return parent.render_seed(seed, yaw_deg, pitch_deg, eye_id)
