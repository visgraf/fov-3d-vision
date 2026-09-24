"""Public contract for Classroom-FSG-1 controlled replay reconstruction.

This milestone returns from the SGBM microscope to the Classroom.  Attention is
held fixed by replaying the already-sealed Demo-Classroom-1 oracle fixation
history.  Every replayed fixation is re-acquired through the generic Blender ->
local tangent pair bridge and measured by the unchanged FSG stereo instrument.

For this experiment there is NO foreground/background decomposition and NO
background panorama/shell.  Every positive Blender instance id is treated as an
ordinary scene entity.  Two reconstructions are accumulated in parallel:

* native  : unchanged FSG stereo validity only;
* guarded : a pure subset of native rows, with Blender truth allowed only to
            reject gross range errors after stereo.  Truth never supplies xyz.
"""
from __future__ import annotations

import hashlib
import json

SPEC_ID = "ClassroomFSG1-controlled-replay-v1"
BASELINE_COMMIT = "605fdfc"  # BRIDGE5_NO_CAPTURE
RUN_BRANCH = "classroom-fsg-1"
SCENE_REL = "scenes/classroom/classroom_eye.blend"
SOURCE_DEMO_BRANCH = "demo-classroom-1"
SOURCE_DEMO_FINAL_COMMIT = "d15642f"
DEFAULT_FIXATION_HISTORY = "previews/demo-classroom1/full-seed2111/fixation_history.json"
DEFAULT_SOURCE_MANIFEST = "previews/demo-classroom1/full-seed2111/demo_manifest.json"
EXPECTED_FIXATIONS = 225

PROFILE = "small"
SPP = 64
SEED = 2111
VERGENCE_M = 2.10
IPD_M = 0.063
DEVICE = "OPTIX"

# Demo-only damage-control gate inherited from the earlier Classroom demo.
# It is NOT an observer confidence model.  It may reject a native stereo row;
# it may never replace or alter the row's geometry.
GUARD_ABS_M = 0.10
GUARD_REL = 0.05

# fsg3_surface_map stores a uint64 patch-provenance mask and therefore supports
# at most 63 packet ids per object.  Deterministically packet four contributing
# fixations together, so at most ceil(225/4)=57 packets/object can be fused.
FUSION_PACKET_CONTRIBUTIONS = 4
FSG3_MIN_PATCH_POINTS = 100

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "purpose": (
        "Replay the sealed 225-fixation Classroom attention sequence through the "
        "generic tangent-plane FSG stereo bridge, then accumulate ordinary scene "
        "entities without any foreground/background panorama decomposition."
    ),
    "baseline_commit": BASELINE_COMMIT,
    "branch": RUN_BRANCH,
    "scene": SCENE_REL,
    "source_attention": {
        "branch": SOURCE_DEMO_BRANCH,
        "final_commit": SOURCE_DEMO_FINAL_COMMIT,
        "history": DEFAULT_FIXATION_HISTORY,
        "manifest": DEFAULT_SOURCE_MANIFEST,
        "expected_fixations": EXPECTED_FIXATIONS,
        "policy_reexecuted": False,
        "gazes_reselected": False,
        "use": "gaze yaw/pitch and ordering only; historical foreground/background roles are ignored",
    },
    "instrument": {
        "acquisition": "tools/fsg_blend_bridge.py",
        "stereo": "tools/fsg_stereo.py",
        "profile": PROFILE,
        "spp": SPP,
        "seed": SEED,
        "vergence_m": VERGENCE_M,
        "ipd_m": IPD_M,
        "device": DEVICE,
        "matcher_tuned": False,
    },
    "scene_representation": {
        "foreground_background_decomposition_used": False,
        "background_panorama_used": False,
        "background_shell_used": False,
        "special_background_object_used": False,
        "positive_instance_ids_are_ordinary_scene_entities": True,
        "instance_grouping": "generic fsg_blend_bridge evaluated-depsgraph parent-root ids",
    },
    "streams": {
        "native": "all rows accepted by unchanged fsg_stereo validity",
        "guarded": "native rows only, additionally passing the post-stereo oracle range rejection gate",
    },
    "guard": {
        "absolute_m": GUARD_ABS_M,
        "relative": GUARD_REL,
        "truth_available_only_after_stereo": True,
        "truth_can_reject": True,
        "truth_can_insert_or_replace_geometry": False,
        "scientific_status": "demo damage control; not a truth-free measurement-validity model",
    },
    "fusion": {
        "implementation": "unchanged fsg3_surface_map initialize/fuse",
        "association_radius_source": "fsg6f_public.FUSION",
        "packet_contributing_fixations": FUSION_PACKET_CONTRIBUTIONS,
        "minimum_points_source": "fsg3_surface_map inherited 100-point floor",
        "reason_for_packetization": "keep <=63 provenance packets/object while replaying up to 225 fixations",
    },
    "claims_not_made": [
        "autonomous Classroom attention",
        "truth-free measurement validation for the guarded stream",
        "foreground/background decomposition",
        "background panorama or inferred background shell",
        "SGBM optimality",
        "complete room reconstruction",
        "semantic segmentation beyond Blender oracle instance ids",
    ],
    "required_outputs": [
        "classroom_fsg1_manifest.json",
        "classroom_fsg1_report.json",
        "classroom_fsg1_report.md",
        "replayed_fixations.json",
        "native_scene_points.npz",
        "native_scene_points.ply",
        "guarded_scene_points.npz",
        "guarded_scene_points.ply",
        "objects/native/object_<id>.npz/.ply",
        "objects/guarded/object_<id>.npz/.ply",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
