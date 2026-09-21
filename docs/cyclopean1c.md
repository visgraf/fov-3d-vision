# Cyclopean-1c — one deep-bay probe

## Question

Cyclopean-1a showed that the cyclopean chart can turn an enclosed sampling hole
into one useful foveation. Cyclopean-1b then showed why internal holes are not
the whole story: seed 2111 contains a large **exterior-connected bay** whose
shoreline is dominantly `UNOBSERVED`, and whose exterior penetration depth is
far larger than ordinary shoreline structure.

Cyclopean-1c asks one deliberately small action question:

> If we foveate **once** at the deepest point of that unresolved bay, does the
> existing stereo/fusion pipeline acquire useful target surface and reduce the
> bay, without changing FSG6f or the stopping policy?

This is not a new controller loop.

## Parent and scope

The only scheduled record is the completed Cyclopean-1b `full` audit for seed
2111. The parent is located by manifest, not by assumed path.

Cyclopean-1b itself is read-only, so Cyclopean-1c follows its `parent_record` to
the completed Cyclopean-1a record, reconstructs the exact inherited chart and
prediction-side evidence, and uses the final Cyclopean-1a `surface_map.npz` as
the map to extend.

Seed 2179 is intentionally not run. Its principal internal hole was already
probed in Cyclopean-1a and is not the question here.

## Bay selection

Reuse the exact Cyclopean-1b semantics and exterior-distance field.

An eligible bay component is an `EXTERIOR` complement component whose shoreline
contains at least one `UNOBSERVED` cell.

If more than one eligible exterior component exists, choose the one whose
`UNOBSERVED` shoreline reaches the greatest inherited border distance. Ties are
resolved by more unobserved shoreline cells, then component id. There is no
threshold saying how deep is deep enough.

Within that selected component, choose a complement cell at the greatest
8-connected shortest-path distance from the padded chart border:

\[
\omega_{probe}=\arg\max_{\omega\in B} d_{border}(\omega).
\]

If several cells share the maximum distance, choose the one nearest the raster
centroid of that maximum-depth plateau. If that exact angular gaze was already
visited, continue deterministically through the same depth ordering until the
first unvisited cell.

This is a one-off geometric readout of the representation, not a new ranking
family.

## Acquisition and fusion

Acquire exactly one binocular fixation with the existing Reality/FSG rendering
path. No parent fixation is rerendered.

The observation uses the same Reality Check 2b empty-look semantics:

- if the fixation contains enough target points under the inherited contract,
  fuse them with the frozen FSG3 12 mm association radius and hash cell;
- if it is empty/nearly empty, retain it as negative evidence and fuse nothing.

Any fused patch must be replay-idempotent and preserve target-map purity.

The before and after shoreline audits are rebuilt on the **same inherited
Cyclopean chart** so the structural change is directly comparable.

## Frozen / forbidden

Frozen: fixed head/static scene, seed 2111 parent acquisition history, FSG1
stereo instrument, FSG3 fusion scale, FSG6f, Reality Check semantics,
Cyclopean-1a chart scale and footprint, Cyclopean-1b boundary semantics.

Forbidden: a second probe, a repeated bay loop, stopping-rule change, FSG6f
ranking modification, evaluator truth, mesh reconstruction, hole filling,
morphology tuning, minimum-arc pruning, normal cue, new depth threshold,
coverage gate or reconstruction-quality PASS threshold.

## What to report

The experiment is observational. Report:

- selected component and deepest-cell gaze;
- whether a revisit fallback was needed;
- target points at the new fixation;
- map point gain and idempotence;
- before/after support, complement, internal/exterior components and maximum
  exterior penetration depth;
- visual reading of the before/after shoreline maps and the probe RGB.

Do not infer success from a tuned numerical threshold. The scientific question
is simply whether one representation-driven bay foveation acquires useful
missing surface and what it does to the spherical structure.

## Results

Pending workstation execution.
