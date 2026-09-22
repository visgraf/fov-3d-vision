# MultiObject-3b — seed the scene-selected fourth object

## Motivation

MultiObject-3a repeated the scene-level next-object decision on the updated saved memory and selected one uninstantiated object by accumulated **valid-depth** support. Existing unfinished objects remained persistent and did not block progress.

MultiObject-3b turns that decision into exactly one action: **one prescribed fixation that instantiates the selected object as a fourth persistent scene entity**.

Small is beautiful: this is still not a growth experiment.

## Parent-selected object

The selected id is consumed from the completed MultiObject-3a parent. It is not declared or hand-picked in this step. The already-instantiated object-id set is likewise consumed from the current scene memory rather than hard-coded.

The current measured parent result selects object 145, but the implementation validates and consumes whatever positive uninstantiated id the parent actually recorded.

## Evidence scope and seed direction

Use exactly the complete saved observation scope that MultiObject-3a used for its decision: the older MultiObject-1b2 scene history plus the MultiObject-2b/2c third-object history.

For the parent-selected id:

1. collect only samples for which the existing stereo front end produced valid depth and the saved oracle instance id equals the selected id;
2. convert their reconstructed head-frame xyz positions to yaw/pitch;
3. quantize directions on the inherited 0.1-degree scene grid;
4. compute the spherical mean of occupied cells;
5. choose the occupied cell nearest that mean, using the unchanged MultiObject-1a seed selector.

Quantizing before the mean prevents repeated pixels or views from winning merely by sample density. Choosing an occupied cell anchors the new fixation in already-supported evidence even when the spherical mean falls on an occluder or another object.

## Acquisition

Add exactly one fixation at

```text
max(MultiObject-3a evidence global steps) + 1
```

using `tools/scene_render_fix.py`.

Do not rerender any saved history.

## Scene representation

Every previously instantiated object remains a separate read-only `SURFEL_MAP` entity. The newly selected object is added as a separate `SEED_SURFEL_PATCH` entity.

The shared cyclopean chart records raw angular footprints for all objects. Pairwise and all-object overlaps are **measurements only**, never integrity failures: later scenes may contain occlusion or shared angular support.

## Scope

There is no object growth, no fusion into an existing object, no revisit of retained unfinished objects, no semantic ranking, no saliency model, no quality threshold and no scene scheduler.

Seed point count and seed-view depth recovery are measurements. They do not alter the rule.

## Next stage

If the seed record is structurally clean, grow the newly seeded fourth object independently while every existing object remains stable.
