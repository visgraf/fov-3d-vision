"""Public contract for FullScene-REAL-1: end-to-end frozen-system benchmark.

REAL-1 runs the established procedural Reality-1/FullScene fixture as a whole.
It is not a .blend-file benchmark. The acquisition path already builds the
fixture procedurally inside the existing renderer.

The benchmark remains oracle-assisted for object enumeration/seed direction,
but the declassification boundary is explicit: a truth-side helper may inspect
the procedural scene specification and emit ONLY object identity plus one seed
direction and a label. Exact geometry/depth/normals/extent never cross into the
observer/control process. Full evaluator truth remains sealed until observer
completion.
"""
from __future__ import annotations

import hashlib
import json

SPEC_ID = "FullSceneREAL1-end-to-end-frozen-benchmark-v2"
BASELINE_PARENT_COMMIT = "651a6cb"  # completed FullScene-1d result
BASELINE_BRANCH = "fullscene-calibration-1"
RUN_BRANCH = "fullscene-real-1"
DEFAULT_FIXTURE = "tabletop_cloth"
SEED = 2111
FIXED_HEAD = True
STATIC_SCENE = True
GRID_DEG = 0.1
ASSOCIATION_RADIUS_M = 0.012
OBJECT_WATCHDOG_FIXATIONS = 24
EMPTY_TARGET_VALID_LIMIT = 100
PANO_WIDTH = 2048
PANO_HEIGHT = 1024

# The ONLY prediction-visible fields the pre-control enumeration oracle may emit.
ENUMERATION_OBJECT_FIELDS = ["object_id", "seed_yaw_deg", "seed_pitch_deg", "label"]

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "baseline_parent_commit": BASELINE_PARENT_COMMIT,
    "baseline_branch": BASELINE_BRANCH,
    "run_branch": RUN_BRANCH,
    "fixture": {
        "kind": "procedural",
        "default_name": DEFAULT_FIXTURE,
        "acquisition": "existing tools/scene_render_fix.py procedural Reality-1 fixture",
        "provenance": "record fixture name plus evaluator scene-spec truth_digest; no .blend path/hash is claimed",
    },
    "question": (
        "What scene representation does the current frozen foveal-stereo system produce when run end-to-end "
        "over every positive-instance object in the established procedural test fixture, and where do attention, "
        "measurement, geometry, and control debts remain?"
    ),
    "principle": "freeze the mechanisms; run the whole scene; export everything; evaluate only afterwards",
    "seed": SEED,
    "fixed_head": FIXED_HEAD,
    "static_scene": STATIC_SCENE,
    "benchmark_scope": {
        "discovery": (
            "NOT tested. A quarantined pre-control oracle enumerates benchmark objects and gives one seed direction "
            "per object so every benchmark object is attempted. This scaffold is reported explicitly."
        ),
        "enumeration_oracle": {
            "truth_side": (
                "a REAL-1-only helper may inspect the evaluator-side procedural scene specification before control"
            ),
            "declassified_fields_only": ENUMERATION_OBJECT_FIELDS,
            "forbidden_to_cross_boundary": [
                "vertices", "surface geometry", "depth", "range", "normals", "coverage", "surface extent", "masks"
            ],
            "prediction_side": (
                "observer/control code reads only the sanitized enumeration_oracle.json and must not import the "
                "evaluator-side scene-spec module"
            ),
        },
        "seed_direction": (
            "may be derived inside the quarantined oracle from benchmark object geometry/bounds, but only the final "
            "yaw/pitch cue may cross the boundary; this is benchmark scaffolding, not autonomous discovery"
        ),
        "stereo": "existing stereo front end unchanged",
        "local_growth": "existing multiobject2c_policy / frozen FSG6f unchanged",
        "association": "existing 12 mm surfel association unchanged",
        "empty_look": "existing <100 target-valid-points negative-evidence semantics unchanged",
        "object_watchdog": "24 selected-object fixations including seed, engineering guardrail only",
        "epistemic_audit": "existing MultiObject/Cyclopean audit semantics unchanged",
        "handoff": (
            "at most one established cyclopean epistemic handoff may be used for an object only after a genuine "
            "no_frontier stop with exterior NEVER_OBSERVED > 0; at most one returned local action may then execute; "
            "no recursive handoff scheduler"
        ),
        "revisit": "no second-pass revisit scheduler in REAL-1",
        "truth": (
            "sanitized object identity/seed-direction enumeration is the only pre-control oracle exception; evaluator "
            "RGB/depth/exact geometry truth must not influence stereo, fusion, growth, audit, handoff, or status"
        ),
    },
    "scene_loop": [
        "bind to the established procedural fixture name; do not claim a .blend input",
        "run the quarantined enumeration helper and validate its exact declassification whitelist",
        "enumerate positive benchmark instance IDs dynamically; never hard-code scene IDs",
        "for each enumerated object in deterministic order, attempt one seed fixation",
        "if usable seed geometry exists, grow with frozen local machinery until no_frontier or watchdog",
        "audit the resulting object state read-only",
        "if and only if no_frontier plus exterior NEVER_OBSERVED > 0, permit one established epistemic handoff and at most one returned local action",
        "freeze that object's result/status and move to the next enumerated object",
        "after every object has been attempted exactly once, seal observer state",
        "only then render/open full evaluator truth and compute benchmark metrics",
        "export final scene products and a machine-readable manifest/report",
    ],
    "determinism": {
        "object_order": "ascending positive instance ID",
        "panorama_resolution": [PANO_WIDTH, PANO_HEIGHT],
        "tie_breaks": "deterministic and recorded",
        "random_seed": SEED,
    },
    "required_outputs": {
        "observer": [
            "enumeration_oracle.json",
            "scene_manifest.json",
            "scene_report.json",
            "scene_report.md",
            "fixation_history.json",
            "object_status_table.json",
            "objects/object_<id>.npz",
            "objects/object_<id>.ply",
            "scene_points.npz",
            "scene_points.ply",
            "observer_depth.npy",
            "observer_instance.npy",
            "observer_valid.png",
            "observer_depth_preview.png",
        ],
        "reference_after_control": [
            "reference_rgb.png",
            "reference_depth.npy",
            "reference_instance.npy",
        ],
        "evaluation": [
            "evaluation_summary.json",
            "per_object_metrics.json",
            "coverage_preview.png",
        ],
    },
    "observer_panorama_semantics": (
        "observer depth/instance panoramas are produced by spherical projection of final observer geometry with a "
        "documented nearest-range z-buffer; they are sparse where the observer has no geometry. Reference RGB/depth "
        "are separate evaluator products and must never be mislabeled as observer reconstruction"
    ),
    "minimum_object_statuses": [
        "NOT_VISIBLE_OR_NO_TARGET_SUPPORT",
        "SEED_MEASUREMENT_FAILED",
        "WATCHDOG_REACHED_RETAIN_FOR_REVISIT",
        "POLICY_EXHAUSTED_WITH_UNSEEN_TERRITORY",
        "ATTENTION_COMPLETE_MEASUREMENT_PARTIAL",
        "LOCAL_FRONTIER_AND_ATTENTION_RESOLVED_UNDER_CURRENT_REPRESENTATION",
        "LOCAL_GROWTH_STOPPED_OTHER",
    ],
    "evaluation_metrics": [
        "oracle-enumerated/attempted/instantiated object inventory",
        "per-object fixation count and final status",
        "per-object surfel count and spherical footprint",
        "per-object reconstructed angular coverage against reference instance mask",
        "depth absolute error on pixels where both observer and reference depth are valid (median and p95)",
        "cross-object purity/contamination where evaluable",
        "attention residue and measurement residue from epistemic audit",
        "watchdog/local-stop/handoff counts",
        "total wall time and Blender launch count",
    ],
    "integrity_contract": [
        "start from completed FullScene-1d state but do not reuse accumulated object maps as reconstruction input",
        "do not modify any pre-REAL-1 source; integration/fixes stay in new fullscene_real1 files unless Chat explicitly approves otherwise",
        "do not hard-code test-scene object IDs",
        "the observer/control process must not import the evaluator-side scene specification",
        "the pre-control oracle may declassify ONLY object_id, seed_yaw_deg, seed_pitch_deg, label",
        "do not use evaluator depth/geometry truth to seed beyond that declared direction cue, fuse, grow, stop, handoff, rank, or complete an object",
        "all observer acquisitions, maps, audits, and control decisions are checkpointed for resume",
        "object-local watchdog is an engineering guardrail, never a scientific completion claim",
        "all statuses and metrics remain separate; do not synthesize a single quality/completeness score",
        "full truth-based evaluation runs only after observer_complete is sealed",
        "main and fullscene-calibration-1 remain untouched; work/push only on fullscene-real-1",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
