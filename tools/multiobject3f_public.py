"""Public contract for MultiObject-3f: frontier reactivation audit.

MultiObject-3e demonstrated one bounded hierarchical handoff: the established
cyclopean epistemic field supplied one gaze outside the locally exhausted
FSG6f action envelope, that gaze added selected-object geometry, and the same
frozen local controller returned from ``no_frontier`` to ``continue``.

This step is deliberately read-only.  It asks what changed inside the frozen
local representation when that reactivation occurred.  The experiment
reconstructs both the pre-handoff and post-handoff FSG6f states, matches
frontier sources by the controller's own frozen voxel grid, and audits the
candidate-generation gates direction by direction.  It executes no action.
"""
from __future__ import annotations

import hashlib
import json

import multiobject3e_public as parent

SPEC_ID = "MultiObject3f-frontier-reactivation-audit-v1"
PARENT_SPEC_ID = parent.SPEC_ID
SEED = parent.SEED
FIXTURE = parent.FIXTURE
FUSION = dict(parent.FUSION)
NO_ACQUISITION = True
NEXT_STAGE = "interpret frontier reactivation before executing any returned local action"

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent": PARENT_SPEC_ID,
    "question": (
        "After one bounded epistemic handoff reactivates frozen FSG6f, why did the local frontier/action "
        "state change: genuinely new map voxels, newly frontier-active pre-existing map voxels, state "
        "reclassification, candidate-gate changes, or some combination of these?"
    ),
    "principle": "Bounded Boldness: inspect the causal seam before taking a second action",
    "fixture": FIXTURE,
    "seed": SEED,
    "fixed_head": True,
    "static_scene": True,
    "no_acquisition": True,
    "active_object_source": "consume selected_object_id from the completed MultiObject-3e parent",
    "scope": (
        "read-only comparison of the exact pre-handoff MultiObject-3c final FSG6f state and the exact "
        "post-handoff MultiObject-3e returned FSG6f state; no render, no fusion, no new fixation, no action"
    ),
    "frontier_identity": (
        "match frontier source entries only by the already-frozen FSG6f source voxel key "
        "floor(source_xyz_h / SURFACE_FRONTIER['voxel_m']); introduce no distance tolerance"
    ),
    "reactivation_decomposition": [
        "replay the pre-handoff and post-handoff frozen policy decisions exactly",
        "because FSG6f frontier extraction is current-gaze local, explicitly separate the gaze-window change from the map update",
        "extract the geometric frontier in all four map/gaze combinations: pre-map/pre-gaze, pre-map/post-gaze, post-map/pre-gaze and post-map/post-gaze",
        "run two read-only policy counterfactuals: post-attention with the pre-fusion map, and post-fusion map under the old attention context",
        "extract and classify both actual frozen 3D frontiers",
        "compare map occupancy on the same frozen FSG6f voxel grid",
        "partition frontier sources into persistent, appeared and disappeared voxel keys",
        "for persistent frontier keys, report OPEN/MAP_RESOLVED/BOUNDARY_RESOLVED state transitions",
        "for appeared frontier keys, report whether the source map voxel existed before the handoff or was newly occupied",
        "report continuous source/target displacement and nearest handoff-patch distances descriptively, without gating",
        "replay the eight frozen lattice directions as a diagnostic gate ledger using frozen support, continuation and consensus rules",
        "for each post-handoff candidate, partition OPEN support by appeared versus persistent frontier origin",
    ],
    "boundedness": {
        "new_fixations": 0,
        "fusion_iterations": 0,
        "returned_action_executed": False,
        "automatic_loop": False,
        "scene_scheduler": False,
        "revisit_scheduler": False,
    },
    "measurement_contract": (
        "all counts, transitions, distances and gate outcomes are descriptive; no measured quantity becomes "
        "a quality gate, tuning rule, new threshold or action trigger"
    ),
    "next_stage": NEXT_STAGE,
    "integrity_contract": [
        "the completed MultiObject-3e parent, its MultiObject-3c scene parent and all scene-object sources are read only",
        "the selected object id is consumed from the parent rather than hard-coded",
        "the parent must be the bounded one-handoff record with LOCAL_POLICY_REACTIVATED and returned action unexecuted",
        "both pre-handoff and post-handoff frozen policy decisions must replay exactly before interpretation",
        "frontier identity uses the frozen FSG6f voxel size and exact integer voxel keys, not a new matching tolerance",
        "candidate-gate diagnostics reuse the frozen FSG6f internal projection, continuation and consensus functions",
        "counterfactual policy calls are diagnostics only and never execute their returned actions",
        "no evaluator truth is opened",
        "no Blender, fusion, matcher change, watchdog change, controller change, scheduler or second action is introduced",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
