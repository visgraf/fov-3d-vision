"""Public contract for Cyclopean-1a: one spherical-topology hole probe.

This is the first concrete use of the fixed-head cyclopean angular domain as a
persistent perceptual organization layer over the metric surfel map.  It does
not change FSG6f.  Starting from each completed Reality Check 2b record, it:

1. projects the final target surfels into a local yaw/pitch chart;
2. detects internal connected components of unsampled angular support;
3. uses completed stereo observations only to mark a hole as an already-seen
   physical depth break; and
4. if an unresolved internal hole remains, takes exactly one new foveation at
   the largest hole's spherical centroid.

The experiment is observational.  No numerical reconstruction-quality PASS
threshold is introduced.
"""
from __future__ import annotations
import hashlib
import json
import math

import reality1_public as reality1
import reality2b_public as reality2b

SPEC_ID = "Cyclopean1a-spherical-hole-probe-v1"
PARENT_SPEC_ID = reality2b.SPEC_ID
OBJECT_ID = reality2b.OBJECT_ID
SEEDS = tuple(reality2b.SEEDS)
FIXTURE = reality2b.FIXTURE
INSTRUMENT_ID = reality2b.INSTRUMENT_ID
FROZEN_POLICY_ID = reality2b.FROZEN_POLICY_ID
FUSION = dict(reality2b.FUSION)
EMPTY_TARGET_POINT_LIMIT = reality2b.EMPTY_TARGET_POINT_LIMIT
WATCHDOG_TOTAL_FIXATIONS = reality2b.WATCHDOG_TOTAL_FIXATIONS

# D9's declared full-profile evaluation scale is 2*s0 = 0.1 deg.  This is an
# angular bookkeeping grid, not a new measurement or control threshold.
GRID_DEG_BY_PROFILE = {"small": 0.2, "full": 0.1}

# Existing FSG3 association radius defines the angular footprint of one surfel
# in the cyclopean chart.  No extra spatial tolerance is introduced.
def footprint_radius_deg(range_m: float) -> float:
    r = float(range_m)
    if not math.isfinite(r) or r <= 0:
        raise ValueError("range_m must be positive and finite")
    return math.degrees(math.atan(FUSION["association_radius_m"] / r))

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent": PARENT_SPEC_ID,
    "question": "Does the fixed-head cyclopean spherical domain expose the internal sampling holes left by Reality Check 2b, and does one centroid foveation acquire useful target surface without changing FSG6f?",
    "fixture": FIXTURE,
    "seeds": list(SEEDS),
    "fixed_head": True,
    "static_scene": True,
    "object_id": OBJECT_ID,
    "instrument": INSTRUMENT_ID,
    "frozen_object_policy": FROZEN_POLICY_ID,
    "fusion": FUSION,
    "grid_deg_by_profile": GRID_DEG_BY_PROFILE,
    "support_footprint": "angular radius atan(frozen 12 mm FSG3 association radius / median target range)",
    "hole_definition": "connected component of complement of rasterized target support that does not touch the padded chart border",
    "physical_hole_evidence": "completed stereo observations in the hole are non-target-majority and their reconstructed range differs from the target boundary range by more than the frozen FSG3 association radius",
    "probe_rule": "among holes not already resolved as a physical depth break, choose the largest angular component and foveate its spherical centroid exactly once",
    "quality_contract": "observational; report topology, target points, map growth and hole-area change without a tuned numerical PASS gate",
    "integrity_contract": [
        "exact saved Reality Check 2b parent is read only; no parent view is rerendered",
        "no evaluator truth is opened by the topology or probe path",
        "cyclopean topology uses only persistent surfels plus completed prediction-side stereo/instance observations",
        "no mesh reconstruction or hole filling is performed",
        "FSG6f is not modified or copied",
        "the topology probe adds at most one physical fixation per parent record",
        "an empty probe is retained as negative evidence and fuses no target points",
        "a fused probe is replay-idempotent and preserves target-map purity",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def render_seed(seed: int, yaw_deg: float, pitch_deg: float, eye_id: int) -> int:
    # Reuse the corrected Reality Check 1 physical-view RNG mapping exactly.
    return reality1.render_seed(seed, yaw_deg, pitch_deg, eye_id)
