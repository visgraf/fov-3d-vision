# Cyclopean-1e — Epistemic Gaze

## Question

Cyclopean-1d split the old `UNOBSERVED` shoreline into distinct epistemic causes.  On seed 2111, the residual internal cells with a usable range reference were all `OBSERVED_TARGET_NO_DEPTH`, while the remaining deep exterior slot was one `NEVER_OBSERVED` arc.  Cyclopean-1e asks one deliberately small question:

> If the refined state is allowed to choose exactly one new fixation from genuinely `NEVER_OBSERVED` exterior shoreline, does it aim a useful look while ignoring the already-seen/no-depth residue?

## Frozen context

The experiment uses seed 2111 only.  Scene, fixed head, stereo path, fusion, chart, 0.1 degree full-profile grid, 12 mm association radius, object id, empty-look semantics, and every FSG6f source remain frozen.  Cyclopean-1d is the direct parent and is read only.

## Candidate entity

Only cells satisfying all three conditions are eligible:

1. they lie on the current shoreline;
2. their complement component is `EXTERIOR`;
3. Cyclopean-1d refines them as `NEVER_OBSERVED`.

In particular, `OBSERVED_TARGET_NO_DEPTH` is not a candidate for an identical blind repeat.

## Selection

No threshold or learned/tuned score is added.  Among eligible exterior components, choose the one whose `NEVER_OBSERVED` shoreline reaches the greatest inherited exterior border distance.  Within it, select the deepest `NEVER_OBSERVED` shoreline cell.  Ties use distance to the tied plateau centroid and then raster order.  A previously visited gaze is skipped using that same deterministic ordering.

Thus the action is the literal read-out

`refined epistemic state -> deepest genuinely unseen exterior shoreline -> one foveation`.

## Acquisition

Exactly one fixation may be added.  It is rendered through the existing Reality Check fixation path and processed by the frozen stereo pipeline.  Target depth is fused through the frozen 12 mm FSG3 association rule.  If the fixation contains fewer than the inherited minimum target points, it remains a valid empty/negative observation under the Reality Check 2b contract and fuses nothing.

The new observation is then added to the spherical evidence, the geometric shoreline is rebuilt, and the Cyclopean-1d observation-versus-measurement refinement is recomputed on the updated map.

## What is measured

The report records, without a quality gate:

- selected gaze and inherited border depth;
- whether the look contains target points;
- new and matched surfels;
- idempotent replay;
- map point count before/after;
- complement/support/shoreline structure;
- refined state counts before/after;
- number and maximum depth of exterior `NEVER_OBSERVED` shoreline cells.

No evaluator truth is opened, so internal coherence is not an accuracy claim.

## Non-goals

Cyclopean-1e does not change stopping, does not call FSG6f, does not introduce a repeated epistemic loop, does not solve low-texture stereo, and does not decide what alternate instrument action should follow `OBSERVED_TARGET_NO_DEPTH`.  It tests exactly one consequence of refined entities: whether they can simplify the next action.

## Results

To be filled by Code after workstation execution.
