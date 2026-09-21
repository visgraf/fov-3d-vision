# Cyclopean-1d — observation versus measurement

## Question

Cyclopean-1c established that one fixation aimed from cyclopean boundary
structure can acquire a large amount of useful missing target surface. It also
exposed a more refined epistemic distinction: a small residual on the printed
emblem was **seen in the image** but frozen stereo produced little/no valid
depth there.

Cyclopean-1d asks only:

> Of the final shoreline cells that the existing Cyclopean-1b semantics still
> call `UNOBSERVED`, which were truly never imaged, and which were imaged as
> target but not measured in depth?

This is a read-only audit. It does not take another look.

## Why refine the entity

The old state `UNOBSERVED` meant only that no valid stereo target or non-target
3D evidence landed on that cyclopean shoreline cell. Cyclopean-1c showed that
this can conflate two different situations:

1. **absence of attention** — the region was never seen;
2. **failure of measurement** — the region was seen as target, but the stereo
   instrument did not return valid depth.

These should not force the controller to invent different heuristics later. The
representation should first say what actually happened.

## Frozen base semantics

Rebuild the final Cyclopean-1c support on the exact inherited chart and reuse
Cyclopean-1b's shoreline states unchanged. `PHYSICAL_DEPTH_BREAK` and
`AMBIGUOUS` are not redefined.

Only cells whose base shoreline state is `UNOBSERVED` are refined.

## Observation versus depth

For one such shoreline cell, Cyclopean-1b already provides a nearby target
range reference: `local_target_range_m`. Use that inherited value only to build
a **continuation test point** on the cell's cyclopean ray.

The point is not geometry and is never fused. It is a query into past images:
if the same putative continuation had existed there, what did the completed
foveal observations contain at its projected image location?

For every completed left rectified core, use the exact saved calibration,
rectification, crop, oracle instance mask, calibration support and stereo
`valid` mask. Observation and measurement are independent:

- target instance at a supported projected pixel -> target was **observed**;
- the same pixel also `valid == true` -> target depth was **measured**.

No RGB texture threshold is introduced here. The audit reads the instrument's
already-saved valid mask rather than reverse-engineering why it failed.

## Refined states

The base `UNOBSERVED` shoreline is split descriptively into:

- `NEVER_OBSERVED` — no completed supported projection carried image evidence;
- `OBSERVED_TARGET_NO_DEPTH` — target image evidence exists, but no projected
  target sample has valid stereo depth;
- `OBSERVED_TARGET_WITH_DEPTH` — target image evidence and valid depth both
  exist even though the cell remains outside final support; this is diagnostic;
- `OBSERVED_NONTARGET_ONLY` — only non-target image evidence exists under the
  continuation projection hypothesis;
- `MIXED_OBSERVATION` — target and non-target evidence both occur across views;
- `NO_RANGE_REFERENCE` — the inherited local target range is undefined, so no
  continuation projection is attempted.

No state selects a fixation in this step.

## Scope

Seed 2111 only, using the completed Cyclopean-1c record and all of its already
completed acquisition ancestry. No Blender invocation, no new fixation, no
FSG6f import, no stopping change, no mesh, no morphology, no normal cue, no
new depth or texture threshold, and no evaluator truth.

The intended readout is especially simple:

- does the tiny internal residue exposed by Cyclopean-1c become
  `OBSERVED_TARGET_NO_DEPTH` rather than `NEVER_OBSERVED`?
- how much of the remaining exterior-connected bay shoreline is still genuinely
  `NEVER_OBSERVED`?

Those are measurements, not gates.

## Results

Pending workstation execution.
