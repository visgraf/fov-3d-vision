# MultiObject-3f — frontier reactivation audit

## Motivation

MultiObject-3e gave the first bounded hierarchical handoff.  Frozen FSG6f had stopped with `no_frontier`; the established cyclopean epistemic selector supplied one gaze outside the previously visited envelope; that gaze acquired useful selected-object depth and fused a small amount of new geometry; then one call to the unchanged local controller returned `continue` with a concrete next gaze.

The striking diagnostic was the local frontier jump:

```text
before handoff: frontier 72, OPEN 30, candidates before consensus 0
after handoff:  frontier 488, OPEN 391, candidates before consensus 4
```

while the persistent selected-object map itself changed only modestly.

Before treating that reactivation as mechanistically understood, one confound must be separated explicitly: **FSG6f frontier extraction is local to the current gaze**.  The handoff did not merely add geometry; it also moved the current gaze to a region the local controller had never reached.  Therefore `72 -> 488` cannot be attributed to the fused surfels from the raw counts alone.

This increment is the small diagnostic step that separates those effects.

## Central question

> What, exactly, changed inside the frozen local representation when the one epistemic handoff reactivated FSG6f?

More specifically:

1. How much of the frontier-count jump comes from moving the **current gaze/window** over geometry that already existed?
2. How much comes from the **map update** itself?
3. Among the final frontier sources, which are persistent, newly exposed, newly frontier-active on pre-existing map voxels, or supported by newly occupied map voxels?
4. Which frozen candidate-generation gate changed for each of the eight local lattice directions?
5. Are the reactivated candidates supported mostly by newly exposed frontier structure or by genuinely new geometry?

## Read-only 2x2 decomposition

The audit extracts the geometric frontier in four combinations, without acting on any of them:

```text
PRE_MAP_PRE_GAZE    actual state before the handoff
PRE_MAP_POST_GAZE   moved gaze/window, but no fused map update
POST_MAP_PRE_GAZE   fused map update, but old local gaze/window
POST_MAP_POST_GAZE  actual state after the handoff
```

This uses the same frozen `extract_frontier` function in every case.  It adds no threshold and makes no new policy decision.

Two policy-level counterfactuals are also recorded descriptively:

- **ATTENTION_ONLY_PRE_FUSION_MAP** — use the handoff gaze/current observation and updated observation history, but keep the pre-fusion map;
- **GEOMETRY_ONLY_OLD_ATTENTION_CONTEXT** — use the post-fusion map under the old current gaze/current observation and old history.

Their returned actions are diagnostics only and are never executed.

## Frontier identity

To avoid inventing a matching tolerance, frontier sources are matched only by the controller's own already-frozen voxel grid:

```text
source_voxel_key = floor(source_xyz_h / SURFACE_FRONTIER["voxel_m"])
```

This partitions the actual pre/post frontier into:

- persistent source voxels;
- appeared source voxels;
- disappeared source voxels.

For persistent voxels the audit reports `OPEN`, `MAP_RESOLVED`, and `BOUNDARY_RESOLVED` transitions plus continuous source/target displacement diagnostics.

For appeared post-handoff frontier voxels it distinguishes exactly:

- `EXPOSED_BY_POST_GAZE_ON_PRE_MAP` — already a frontier on the pre-map when viewed from the handoff gaze;
- `CREATED_BY_MAP_UPDATE_ON_PREEXISTING_VOXEL` — source map voxel existed before, but became frontier only after the map update;
- `FRONTIER_FROM_NEW_MAP_VOXEL` — frontier source belongs to a map voxel absent before the handoff.

Nearest distances to the saved handoff patch are reported continuously.  They gate nothing.

## Candidate-gate ledger

For each of the eight frozen 5-degree lattice directions, before and after the handoff, the audit records:

- policy bounds;
- previously visited status;
- raw aligned frontier support;
- `OPEN`, `MAP_RESOLVED`, and `BOUNDARY_RESOLVED` aligned support;
- the already-frozen minimum OPEN-support gate;
- the unchanged projected continuation-corridor result;
- the unchanged strict OPEN-majority state consensus;
- whether the direction reached `candidates_before_consensus`;
- whether it became admissible.

The ledger reuses the frozen FSG6f projection, continuation and consensus functions.  It is a diagnostic replay, not a replacement controller.

For post-handoff OPEN support it also reports the frontier-origin composition, so a reactivated direction can be traced back to persistent, gaze-exposed, map-update-created, or new-map-voxel frontier sources.

## Integrity

MultiObject-3f is strictly read-only:

- no Blender;
- no new fixation;
- no fusion;
- no watchdog extension;
- no controller or matcher change;
- no second local action;
- no scheduler;
- no evaluator truth.

Both the actual pre-handoff and post-handoff frozen policy decisions must replay exactly before any comparison is accepted.

## Expected output

The completed record contains:

- `object_<id>_frontier_reactivation_report.json` — exact policy replays, 2x2 map/gaze decomposition, counterfactual policy summaries, frontier lineage and candidate-gate tables;
- `frontier_reactivation.npz` — machine-readable pre/post frontier source keys, source/target geometry and state codes;
- `frontier_reactivation_details.json` — per-frontier persistent/appeared/disappeared details;
- `prediction_manifest.json` — integrity and compact summary.

## Deliberately deferred

- executing the returned local gaze;
- a second epistemic handoff;
- an automatic hierarchical loop;
- changing the FSG6f frontier extractor or candidate generator;
- tuning any threshold;
- revisiting other objects;
- scene scheduling.

The next step is chosen only after interpreting this audit.
