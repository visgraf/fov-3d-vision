"""Public contract: one-round visible-seed recovery after FullScene-REAL-1."""
from __future__ import annotations
import hashlib, json

SPEC_ID = "FullSceneREAL1-visible-seed-recovery-one-round-v1"
BASELINE_RESULT_COMMIT = "f49ec8e"
RUN_BRANCH = "fullscene-real-1"
BASELINE_OUT = "previews/fullscene-real1/full-seed2111"
SEED = 2111
GRID_STEP_DEG = 5.0
# One Moore-neighborhood ring on the already established 5-degree action lattice.
RING_OFFSETS = [
    (-1, -1), (0, -1), (1, -1),
    (-1,  0),          (1,  0),
    (-1,  1), (0,  1), (1,  1),
]
TARGET_BASELINE_STATUS = "NOT_VISIBLE_OR_NO_TARGET_SUPPORT"

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "baseline_result_commit": BASELINE_RESULT_COMMIT,
    "run_branch": RUN_BRANCH,
    "baseline_out": BASELINE_OUT,
    "question": (
        "When an oracle-supplied object-centre seed is occluded, can exactly one bounded "
        "prediction-side 5-degree visibility-survey ring recover a usable seed without truth geometry?"
    ),
    "target_selection": (
        "dynamically select baseline REAL-1 object rows with status NOT_VISIBLE_OR_NO_TARGET_SUPPORT; "
        "no scene object id may be hard-coded"
    ),
    "one_round": {
        "centre": "the failed baseline seed direction",
        "lattice_step_deg": GRID_STEP_DEG,
        "offsets": RING_OFFSETS,
        "probe_count_per_target": len(RING_OFFSETS),
        "render_all_probes": True,
        "no_radius_expansion": True,
        "no_second_ring": True,
        "reuse_winning_probe_as_seed": True,
        "no_extra_seed_render": True,
    },
    "probe_evidence": (
        "rank probes only by observer-side target valid-depth count, then target visible-pixel count, "
        "then fixed ring order; instance masks and stereo validity are allowed; evaluator geometry/depth is forbidden"
    ),
    "seed_semantics": (
        "materialize the winning observation with the established selected-object seed extraction/purity semantics; "
        "do not invent a new quality threshold"
    ),
    "stop": "stop immediately after the one survey ring and optional recovered seed; no growth, audit, handoff, revisit, or scheduler",
    "integrity": [
        "baseline REAL-1 artifacts are read-only",
        "all pre-existing scene-object maps are read-only",
        "use existing generic renderer/stereo unchanged",
        "do not open or consult reference RGB/depth/exact geometry during probe selection",
        "do not modify pre-REAL-1 or REAL-1 mechanism source; integration stays in new seed-round files",
    ],
    "required_outputs": [
        "seed_recovery_manifest.json",
        "seed_recovery_report.json",
        "probe_ledger.json",
        "recovered_seed_patch.npz when recovery succeeds",
    ],
}

def public_digest() -> str:
    return hashlib.sha256(json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
