"""Public contract for FullScene-1a: freeze and inventory the current scene state.

FullScene-1a starts the first bounded full-scene calibration from the exact
post-MultiObject-3h state.  It performs no acquisition or fusion.  It rebuilds
the declared scene-level observation history, inventories the live persistent
objects, carries forward only status evidence that is actually present in the
ancestry, and reuses the established MultiObject-3a valid-depth selector to
identify the next uninstantiated object.

The result is the formal S0 initial condition for FullScene-1.  No deferred
local action is executed and no evaluator truth is opened.
"""
from __future__ import annotations

import hashlib
import json

import multiobject3h_public as parent

SPEC_ID = "FullScene1a-scene-state-snapshot-v1"
PARENT_SPEC_ID = parent.SPEC_ID
SEED = parent.SEED
FIXTURE = parent.FIXTURE
NO_ACQUISITION = True
NO_FUSION = True
SNAPSHOT_ID = "S0"
SELECTION_SOURCE = "tools/multiobject3a_select.py"
NEXT_STAGE_IF_SELECTED = "FullScene-1b: seed the snapshot-selected next object with one prescribed fixation"
NEXT_STAGE_IF_NONE = "FullScene-1-final: freeze the first tour and open evaluator truth only for evaluation"

PUBLIC_SPEC = {
    "id": SPEC_ID,
    "parent": PARENT_SPEC_ID,
    "question": (
        "At the exact post-MultiObject-3h state, what persistent objects and scene-level evidence "
        "does the observer currently possess, what uninstantiated objects are supported by valid depth, "
        "and which object is next under the already-established deterministic scene-selection rule?"
    ),
    "principle": "Back to Occam + Bounded Boldness: begin the full-scene field test by taking a read-only snapshot",
    "snapshot_id": SNAPSHOT_ID,
    "fixture": FIXTURE,
    "seed": SEED,
    "fixed_head": True,
    "static_scene": True,
    "parent_state": (
        "consume the unique completed MultiObject-3h record; the unexecuted local action recorded there "
        "remains deferred and is not part of FullScene-1a control"
    ),
    "history_scope": (
        "reuse the established scene-selection evidence scope beginning at global step 18, then append every "
        "saved selected-object observation through the MultiObject-3h step; do not reach backward into the "
        "older object-141 Reality/Cyclopean acquisition lineage and do not rerender anything"
    ),
    "inventory_rule": (
        "consume the current scene graph from MultiObject-3h; load each referenced persistent object map, "
        "verify instance-id purity, record point count and current raw angular footprint, and keep every map read only"
    ),
    "candidate_rule": (
        "positive integer instance ids present with valid stereo depth in the complete declared FullScene-1a "
        "history, excluding every id already instantiated in the current scene graph"
    ),
    "selection_rule": (
        "reuse multiobject3a_select.accumulate_candidate_support and select_next_object unchanged: select the "
        "largest accumulated valid-depth support, breaking an exact tie by smaller integer object id"
    ),
    "status_rule": (
        "report only status evidence already recorded in the ancestry; distinguish persistent-map state, prior "
        "epistemic audit labels, and the active object's current local-policy status rather than inventing a unified score"
    ),
    "progress_contract": (
        "this increment only establishes FullScene initial condition S0 and identifies who is next; it takes no gaze, "
        "executes no deferred local action, seeds no object, grows nothing and schedules no revisit"
    ),
    "quality_contract": (
        "all support, visibility, point-count, footprint and status quantities are descriptive; no new threshold, "
        "saliency score, semantic ranking, productivity gate or revisit priority is introduced"
    ),
    "next_stage_if_selected": NEXT_STAGE_IF_SELECTED,
    "next_stage_if_none": NEXT_STAGE_IF_NONE,
    "integrity_contract": [
        "the completed MultiObject-3h parent and all reachable scene-history inputs remain byte-identical",
        "all current persistent object geometries remain byte-identical and instance-id pure",
        "no Blender/Cycles acquisition or historical rerender is launched",
        "no surfel fusion, local growth, epistemic handoff, watchdog extension or deferred local action is executed",
        "the complete declared scene-level observation scope is contiguous from global step 18 through the MultiObject-3h step",
        "candidate support uses saved valid-depth evidence, not mere visibility",
        "instantiated ids and the selected id are consumed/computed rather than declared in advance",
        "no evaluator truth, semantic ranking, automatic object discovery, scene scheduler or revisit scheduler is introduced",
    ],
}


def public_digest() -> str:
    return hashlib.sha256(
        json.dumps(PUBLIC_SPEC, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
