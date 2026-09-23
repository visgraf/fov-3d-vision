"""Public contract for the oracle-assisted Classroom concept demonstration."""
from __future__ import annotations

import hashlib
import json

SPEC_ID = "DemoClassroom1-oracle-assisted-concept-v1"
BASELINE_COMMIT = "cafad30"  # DEMO_TABLETOP1_COMPLETE
RUN_BRANCH = "demo-classroom-1"
SCENE_ID = "classroom"
BLEND_REL = "scenes/classroom/classroom_eye.blend"
SEED = 2111
PROFILE = "full"
PANO_WIDTH = 2048
PANO_HEIGHT = 1024
MAX_OBJECT_FIXATIONS = 24
MAX_ORACLE_REDIRECTS = 6
MAX_TOTAL_FIXATIONS = 256
DEMO_TARGET_COVERAGE = 0.85
# Demo-only measurement validation; not a learned/scientific confidence model.
DEPTH_GATE_ABS_M = 0.10
DEPTH_GATE_REL = 0.05
# Preferred scene-adaptive soft background band. The live adapter may use the
# same rule in an equivalent representation, but must record the exact rule.
BACKGROUND_NEAR_QUANTILE = 0.70
BACKGROUND_FAR_QUANTILE = 0.90
MIN_FOREGROUND_SUPPORT_FRACTION = 0.0025
BACKGROUND_OBJECT_KEY = "__BACKGROUND__"

PUBLIC_SPEC = {
    "schema": SPEC_ID,
    "purpose": (
        "Second concept demonstration of active foveal stereo scene construction, now on the "
        "realistic Blender Classroom. Blender truth is explicitly permitted as supervisory "
        "scaffold for grouping/identity, visibility/gaze guidance, measurement validation, and "
        "a single adaptive visual background object. Stereo/fusion remains the source of metric "
        "foreground geometry."
    ),
    "baseline_commit": BASELINE_COMMIT,
    "branch": RUN_BRANCH,
    "scene": {"id": SCENE_ID, "blend": BLEND_REL, "profile": PROFILE},
    "scientific_claims_not_made": [
        "autonomous discovery or semantic instance segmentation",
        "autonomous gaze policy",
        "truth-free measurement validation",
        "controller optimality",
        "autonomous foreground/background decomposition",
        "background geometry inferred by the observer",
        "complete reconstruction of every Blender mesh component",
    ],
    "oracle_assistance": {
        "object_grouping_identity_and_masks": True,
        "visibility_and_seed_guidance": True,
        "next_gaze_guidance_when_local_control_stalls": True,
        "reference_depth_for_measurement_validation": True,
        "reference_depth_inserted_into_metric_foreground": False,
        "scene_adaptive_foreground_background_plan": True,
        "reference_rgb_and_soft_depth_for_background": True,
    },
    "foreground_contract": [
        "all metric foreground 3-D points originate from the established foveated stereo front end",
        "Blender instance/depth may reject a stereo point but may not replace its xyz/depth",
        "accepted stereo depth must satisfy |z_stereo-z_ref| <= max(abs_gate, rel_gate*z_ref)",
        "reuse the established 12 mm association/fusion and local FSG machinery where applicable",
        "reuse the live Classroom foveated-pair/stereo path rather than inventing a new stereo algorithm",
        "when local control stalls but oracle target support remains, bounded oracle attention assistance may redirect gaze",
        "resource limits are demo engineering guardrails, never completion claims",
    ],
    "background_contract": {
        "role": "one special scene background object, separate from metric foreground reconstruction",
        "selection": (
            "scene-dependent and deterministic from Blender reference support/depth; preferred soft band "
            "uses occupied-scene depth quantiles rather than hand-picked Classroom object names"
        ),
        "preferred_soft_band": {
            "near_quantile": BACKGROUND_NEAR_QUANTILE,
            "far_quantile": BACKGROUND_FAR_QUANTILE,
            "interpretation": "smooth transition from foreground-like to background-like with increasing reference range",
        },
        "geometry": "trivial spherical shell/support with recorded soft-depth statistics",
        "appearance": "rich reference RGB texture over the aggregate background mask",
        "separation": "background scaffold must never be counted as stereo-reconstructed foreground geometry",
    },
    "limits": {
        "max_object_fixations": MAX_OBJECT_FIXATIONS,
        "max_oracle_redirects": MAX_ORACLE_REDIRECTS,
        "max_total_fixations": MAX_TOTAL_FIXATIONS,
        "demo_target_coverage": DEMO_TARGET_COVERAGE,
        "depth_gate_abs_m": DEPTH_GATE_ABS_M,
        "depth_gate_rel": DEPTH_GATE_REL,
        "min_foreground_support_fraction": MIN_FOREGROUND_SUPPORT_FRACTION,
    },
    "required_outputs": {
        "preflight": ["scene_preflight.json", "scene_plan.json"],
        "foreground_observer": [
            "foreground_scene_points.npz",
            "foreground_scene_points.ply",
            "objects/object_<id>.npz",
            "objects/object_<id>.ply",
            "foreground_depth.npy",
            "foreground_instance.npy",
            "foreground_valid.png",
            "foreground_rgb_mosaic.png",
        ],
        "background_scaffold": [
            "background_rgb.png",
            "background_mask.png",
            "background_soft_depth.json",
            "background_shell.ply",
        ],
        "demo_composite": [
            "demo_rgb.png",
            "demo_depth.npy",
            "demo_depth_preview.png",
            "demo_instance.npy",
            "demo_layer.npy",
            "demo_layer_provenance.json",
        ],
        "reference": [
            "reference_rgb.png",
            "reference_depth.npy",
            "reference_instance.npy",
        ],
        "story": [
            "timeline/fix_<step>.png",
            "demo.mp4 (when ffmpeg is available; otherwise timeline PNGs are sufficient)",
            "fixation_history.json",
            "demo_manifest.json",
            "demo_report.json",
            "demo_report.md",
        ],
    },
    "demo_success": [
        "the real Classroom blend is opened and its metric EYE/head convention is verified",
        "reference-visible scene groups are dynamically inventoried and assigned a documented foreground/background role",
        "foreground metric geometry is stereo-derived throughout; Blender depth only rejects/validates",
        "one special adaptive background object supplies contextual appearance without polluting foreground metrics",
        "all oracle aids and layer provenance are explicit in plan/manifest/report",
        "foreground-only and composite products are both exported so the distinction is inspectable",
        "timeline/movie makes fixation -> stereo -> validation -> fusion -> persistent scene accumulation visible",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
