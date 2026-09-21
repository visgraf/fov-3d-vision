"""Public contract for Reality Check 1.

This is deliberately not a benchmark or a new policy.  It asks whether the
already-frozen FSG6f single-object active controller produces a useful-looking,
metrically sane reconstruction on a more ordinary mixed-texture, nonplanar
surface in a small cluttered static scene.

There is no prospective numerical quality PASS threshold.  Structural integrity
is gated; geometric/coverage/termination numbers are reported descriptively and
Luiz/Chat judge whether the result is good enough to continue toward real scenes.
"""
from __future__ import annotations
import hashlib
import json
import fsg6f_public as frozen

SPEC_ID = "RealityCheck1-good-enough-static-scene-v1"
INSTRUMENT_ID = frozen.INSTRUMENT_ID
FROZEN_POLICY_ID = frozen.SPEC_ID
OBJECT_ID = frozen.OBJECT_ID          # keep the FSG6f policy's expected object id
BACKGROUND_IDS = (142, 143, 144, 145)
FIXTURE = "tabletop_cloth"
SEEDS = (2111, 2179)
SEED_GAZE_DEG = (-6.0, -4.0)
VERGENCE_DISTANCE_M = frozen.VERGENCE_DISTANCE_M
MAX_FIXATIONS = frozen.MAX_BUDGET_FIXATIONS
DEFAULT_SPP = dict(frozen.DEFAULT_SPP)
FUSION = dict(frozen.FUSION)

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "question": "Does the frozen FSG6f mechanism remain useful on one moderately irregular, mixed-texture target in an ordinary cluttered static scene?",
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
    "maximum_fixations": MAX_FIXATIONS,
    "spp": DEFAULT_SPP,
    "fusion": FUSION,
    "quality_contract": "observational: report coverage, surface error, overlap, measurement support, trajectory and termination; do not turn them into a tuned PASS gate",
    "integrity_contract": [
        "prediction does not open evaluator truth",
        "map contains only target instance",
        "every fused patch is replay-idempotent",
        "no repeated physical fixation",
        "frozen FSG6f policy imported rather than copied",
    ],
}

def public_digest() -> str:
    return hashlib.sha256(json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def render_seed(seed: int, yaw_deg: float, pitch_deg: float, eye_id: int) -> int:
    if seed not in SEEDS:
        raise ValueError("seed outside Reality Check 1 schedule")
    if eye_id not in (0, 1):
        raise ValueError("eye_id must be 0 or 1")
    # Physical-view deterministic seed, independent of step number.
    iy = int(round((float(yaw_deg) + 30.0) * 10.0))
    ip = int(round((float(pitch_deg) + 25.0) * 10.0))
    return 1_000_000 * int(seed) + 1000 * iy + 2 * ip + eye_id
