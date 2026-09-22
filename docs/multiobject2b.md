# MultiObject-2b — seed the scene-selected third object

## Motivation

MultiObject-2a performed the first scene-level next-object decision entirely from memory.  It selected one uninstantiated object by accumulated **valid-depth** support while leaving objects 141 and 143 unchanged.

MultiObject-2b turns that decision into action, but introduces only one new thing: **one prescribed fixation that instantiates the selected object as a third persistent entity**.

This is still not a growth experiment.

## Parent-selected object

The selected id is consumed from the completed MultiObject-2a parent.  It is not declared or hand-picked in this source step.  The current measured parent result is expected to select id 142, but the implementation validates and consumes whatever positive uninstantiated id the parent actually recorded.

## Seed-direction rule

Use exactly the saved observation scope that MultiObject-2a used for selection.

For the parent-selected id:

1. collect only samples for which the existing stereo front end produced valid depth and the saved oracle instance id equals the selected id;
2. convert their reconstructed head-frame xyz positions to yaw/pitch;
3. quantize directions on the inherited 0.1-degree scene grid;
4. compute the spherical mean of occupied cells;
5. choose the occupied cell nearest that mean, using the unchanged MultiObject-1a seed selector.

Quantizing before the mean prevents heavily sampled views from winning merely because they contributed more pixels.  Choosing an occupied cell anchors the fixation in already-supported evidence even if the spherical mean itself lies on an occluder or another object.

## Acquisition

Add exactly one fixation at

```text
max(MultiObject-2a evidence global steps) + 1
```

using `tools/scene_render_fix.py`.

Do not rerender any saved history.

## Scene representation

Objects 141 and 143 remain separate read-only `SURFEL_MAP` entities.  The selected object is added as a separate `SEED_SURFEL_PATCH` entity.

The shared cyclopean chart records raw angular footprints for all three objects and reports pairwise/triple overlap as **measurements only**.  Overlap is not a failure: future scene configurations may contain occlusion or shared angular support.

## Scope

There is no object growth, no fusion into an existing object, no revisit of object 143, no automatic scheduler, no semantic ranking and no quality threshold.

A zero or small seed-point count is a measurement, not a reason to silently change the rule.  The experiment asks whether the scene-level selection can be converted into one clean third entity under the current instrument.

## Next stage

If the seed record is structurally clean, grow the newly seeded object independently while keeping objects 141 and 143 stable.
