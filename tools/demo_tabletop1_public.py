"""Public contract for the oracle-assisted Tabletop concept demonstration."""
from __future__ import annotations

import hashlib
import json

SPEC_ID = "DemoTabletop1-oracle-assisted-concept-v1"
BASELINE_COMMIT = "0e09f5b"  # FULLSCENE_REAL1_BUDGET_ROUND_COMPLETE
RUN_BRANCH = "demo-tabletop-1"
FIXTURE = "tabletop_cloth"
SEED = 2111
PANO_WIDTH = 2048
PANO_HEIGHT = 1024
MAX_OBJECT_FIXATIONS = 32
MAX_ORACLE_REDIRECTS = 8
# Demo-only truth gate; it is deliberately not claimed as a learned/scientific threshold.
DEPTH_GATE_ABS_M = 0.10
DEPTH_GATE_REL = 0.05
BACKGROUND_LABELS = ("rc1_wall",)

PUBLIC_SPEC = {
    "schema": SPEC_ID,
    "purpose": (
        "Concept demonstration of active foveated stereo scene construction on the procedural "
        "Tabletop fixture. Blender truth is explicitly permitted as supervisory scaffold for "
        "object identity, visibility/gaze guidance, measurement validation, and a declared "
        "background layer. Stereo/fusion remains the source of metric foreground geometry."
    ),
    "baseline_commit": BASELINE_COMMIT,
    "branch": RUN_BRANCH,
    "fixture": FIXTURE,
    "scientific_claims_not_made": [
        "autonomous discovery",
        "autonomous gaze policy",
        "truth-free measurement validation",
        "controller optimality",
        "background geometry inferred by the observer",
    ],
    "oracle_assistance": {
        "object_identity_and_masks": True,
        "visibility_and_seed_guidance": True,
        "next_gaze_guidance_when_local_control_stalls": True,
        "reference_depth_for_measurement_validation": True,
        "reference_depth_inserted_into_metric_foreground": False,
        "declared_background_layer_may_use_reference_depth_range": True,
        "reference_rgb_for_background_texture": True,
    },
    "foreground_contract": [
        "all metric foreground 3-D points originate from the established foveated stereo front end",
        "Blender instance/depth may reject a stereo point but may not replace its xyz/depth",
        "accepted stereo depth must satisfy |z_stereo-z_ref| <= max(abs_gate, rel_gate*z_ref)",
        "reuse established 12 mm association/fusion and local FSG machinery where applicable",
        "when local control has no useful action but oracle target support remains, a bounded oracle redirect may choose a new fixation",
        "resource guardrail is MAX_OBJECT_FIXATIONS and is recorded as demo engineering, not completion",
    ],
    "background_contract": {
        "labels": list(BACKGROUND_LABELS),
        "role": "special visual background object, separate from metric foreground reconstruction",
        "geometry": "trivial spherical/soft-depth support recorded as an oracle scaffold",
        "appearance": "reference RGB texture in the background mask",
        "separation": "background scaffold must never be counted as stereo-reconstructed foreground geometry",
    },
    "limits": {
        "max_object_fixations": MAX_OBJECT_FIXATIONS,
        "max_oracle_redirects": MAX_ORACLE_REDIRECTS,
        "depth_gate_abs_m": DEPTH_GATE_ABS_M,
        "depth_gate_rel": DEPTH_GATE_REL,
    },
    "required_outputs": {
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
        ],
        "demo_composite": [
            "demo_rgb.png",
            "demo_depth.npy",
            "demo_depth_preview.png",
            "demo_instance.npy",
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
            "demo_manifest.json",
            "demo_report.json",
            "demo_report.md",
        ],
    },
    "demo_success": [
        "all positive Tabletop objects represented either as stereo-derived foreground geometry or the explicitly declared background scaffold",
        "no reference depth is fused as foreground metric geometry",
        "every accepted foreground point has an oracle-validation record",
        "all oracle aids and provenance are visible in the manifest/report",
        "final composite and observer-only products are both exported so the distinction is inspectable",
        "timeline makes fixation -> stereo -> validation -> fusion -> scene accumulation visible",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
