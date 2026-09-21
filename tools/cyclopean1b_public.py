"""Public contract for Cyclopean-1b: spherical shoreline / boundary audit.

Cyclopean-1a showed that an apparent interior gap may instead be an exterior-
connected bay.  This step is deliberately read-only: it audits the boundary of
the final Cyclopean-1a target support using only the already-acquired
prediction-side observations.  It renders nothing and changes no controller.
"""
from __future__ import annotations
import hashlib
import json

import cyclopean1a_public as cyclopean1a

SPEC_ID = "Cyclopean1b-spherical-boundary-audit-v1"
PARENT_SPEC_ID = cyclopean1a.SPEC_ID
OBJECT_ID = cyclopean1a.OBJECT_ID
SEEDS = tuple(cyclopean1a.SEEDS)
FIXTURE = cyclopean1a.FIXTURE
GRID_DEG_BY_PROFILE = dict(cyclopean1a.GRID_DEG_BY_PROFILE)
FUSION = dict(cyclopean1a.FUSION)
NO_ACQUISITION = True

STATES = (
    "UNOBSERVED",
    "TARGET_CONTINUATION",
    "PHYSICAL_DEPTH_BREAK",
    "AMBIGUOUS",
)

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent": PARENT_SPEC_ID,
    "question": (
        "Does the fixed-head cyclopean domain expose unresolved boundary arcs, "
        "including exterior-connected bays, and distinguish them from observed "
        "physical depth breaks using only already-acquired prediction-side evidence?"
    ),
    "fixture": FIXTURE,
    "seeds": list(SEEDS),
    "fixed_head": True,
    "static_scene": True,
    "object_id": OBJECT_ID,
    "grid_deg_by_profile": GRID_DEG_BY_PROFILE,
    "support_footprint": cyclopean1a.PUBLIC_SPEC["support_footprint"],
    "boundary_domain": (
        "complement cells 8-adjacent to final Cyclopean-1a target support; each "
        "cell retains the identity of its complement component (internal or exterior)"
    ),
    "boundary_states": {
        "UNOBSERVED": "no completed target or non-target observation at the shoreline cell",
        "TARGET_CONTINUATION": "completed target evidence exists at the shoreline cell and non-target evidence does not",
        "PHYSICAL_DEPTH_BREAK": (
            "completed non-target-only evidence exists and its range differs from "
            "the nearby target-boundary range by more than the frozen FSG3 12 mm association radius"
        ),
        "AMBIGUOUS": "all other observed shoreline cases",
    },
    "exterior_depth": (
        "8-connected shortest-path distance in complement cells from the padded chart border; "
        "reported descriptively only, with no threshold or action rule"
    ),
    "quality_contract": (
        "observational only; report boundary-arc states and exterior penetration depth. "
        "No completeness PASS gate, no probe selection and no new acquisition."
    ),
    "integrity_contract": [
        "completed Cyclopean-1a records and all ancestors are read only",
        "no Blender/Cycles acquisition is launched",
        "no evaluator truth is opened",
        "the exact Cyclopean-1a chart scale and frozen 12 mm-derived footprint are reused",
        "no mesh reconstruction, hole filling, morphology tuning or minimum-arc filter is introduced",
        "FSG6f, Reality Check and Cyclopean-1a sources are not modified or copied",
        "exterior-connected complement is not silently equated with a resolved physical boundary",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
