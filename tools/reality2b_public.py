"""Public contract for Reality Check 2b: learn from an empty look.

Reality Check 2 showed that exact continuation beyond six looks is useful, but
its smoke run aborted when frozen FSG6f selected an off-target gaze whose stereo
patch contained fewer than the inherited 100 target points.  Reality Check 2b
changes only the meaning of that event: it is a valid negative binocular
observation, not a runtime failure.

The empty look is recorded in gaze and binocular observation history, contributes
no target surfels to the map, and is then handed to the unchanged FSG6f policy so
its persistent boundary evidence can respond.  Scientific stopping remains
FSG6f ``no_frontier``; the 24-look watchdog remains an engineering guard only.
"""
from __future__ import annotations
import hashlib
import json
import reality1_public as parent
import reality2_public as predecessor
import fsg6f_public as frozen

SPEC_ID = "RealityCheck2b-empty-look-is-evidence-v1"
PARENT_SPEC_ID = parent.SPEC_ID
PREDECESSOR_SPEC_ID = predecessor.SPEC_ID
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
WATCHDOG_TOTAL_FIXATIONS = predecessor.WATCHDOG_TOTAL_FIXATIONS

# Exactly the retired Reality Check 2 abort guard, now given semantics rather
# than tuned.  It is not a quality threshold and is not changed after outcomes.
EMPTY_TARGET_POINT_LIMIT = 100


def empty_observation_contract(point_count: int) -> dict:
    """Pure semantics for one acquired fixation.

    Fewer than 100 reconstructed target points is the same condition that caused
    Reality Check 2 to abort.  Here that observation is still completed: gaze and
    binocular segmentation/support enter history, no target points are fused,
    and the persistent map is unchanged before the next frozen-policy decision.
    """
    n = int(point_count)
    if n < 0:
        raise ValueError("point_count must be nonnegative")
    empty = n < EMPTY_TARGET_POINT_LIMIT
    return {
        "empty_target_observation": bool(empty),
        "record_gaze": True,
        "record_binocular_history": True,
        "fuse_target_points": bool(not empty),
        "map_must_remain_unchanged": bool(empty),
        "action": "record_negative_evidence_without_fusion" if empty else "fuse_target_measurement",
    }


PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent_reality_check": PARENT_SPEC_ID,
    "predecessor_reality_check": PREDECESSOR_SPEC_ID,
    "question": "If an exploratory fixation finds essentially no target surface, can treating that empty look as negative perceptual evidence let frozen FSG6f recover and eventually stop by no_frontier?",
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
    "empty_target_point_limit": EMPTY_TARGET_POINT_LIMIT,
    "empty_observation_semantics": "record gaze and completed binocular instance/support history; fuse no target points; leave persistent map unchanged; run the unchanged FSG6f policy again",
    "quality_contract": "observational; report recovery after empty looks, completion, coverage, geometry, efficiency and seed convergence without a tuned numerical PASS threshold",
    "integrity_contract": [
        "exact saved Reality Check 1 parent state is reused; first six views are not rerendered",
        "prediction does not open evaluator truth",
        "map contains only target instance",
        "every newly fused patch is replay-idempotent",
        "an empty target observation leaves the persistent map unchanged but is retained in gaze and binocular observation history",
        "no repeated physical fixation",
        "frozen FSG6f policy imported rather than copied",
        "Reality Check 2 area-first ranking and all FSG6f constants remain unchanged",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def render_seed(seed: int, yaw_deg: float, pitch_deg: float, eye_id: int) -> int:
    """Delegate exactly to the corrected Reality Check 1 physical-view seed."""
    return parent.render_seed(seed, yaw_deg, pitch_deg, eye_id)
