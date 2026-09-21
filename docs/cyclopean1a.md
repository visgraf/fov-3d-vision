# Cyclopean-1a — spherical topology hole probe

## Question

Reality Check 2b showed that the fixed-head observer can continue beyond the old six-look budget, learn from empty looks, and terminate by its own `no_frontier` rule.  It also exposed the next missing abstraction: `no_frontier` can leave an enclosed unsampled region.  Seed 2111 ended with a large ring-like gap and seed 2179 with a much smaller one.

Cyclopean-1a asks the smallest next question:

> Can the persistent head/cyclopean spherical domain expose such internal sampling holes, distinguish them from an already-observed physical depth break, and place one foveation inside the largest unresolved hole without changing FSG6f?

This is the first concrete use of the cyclopean sphere as a 2-D perceptual organization layer over the metric surfel scene.

## Representation

For every target surfel `x_h`,

```
rho   = ||x_h||
yaw   = atan2(x, -z)
pitch = atan2(y, hypot(x,z))
```

The metric surfel map remains authoritative.  The chart is bookkeeping only.

The angular raster uses the already-declared D9 evaluation scale: `2*s0` (`0.2 deg` small, `0.1 deg` full).  A surfel occupies an angular disc whose radius is derived from the frozen FSG3 association radius:

```
alpha = atan(0.012 / median_range)
```

No new metric spatial tolerance is introduced.

An **internal hole** is a connected component of the complement of target support that does not touch the padded chart boundary.  The exterior component is therefore not a hole.

## Physical-hole cue

Topology alone does not imply that an internal loop should be filled.  A square-ring tabletop is the canonical counterexample.

Completed prediction-side stereo observations are projected into the same chart.  An internal hole is considered already resolved as a **physical depth break** when:

1. observed cells inside it are non-target-majority; and
2. their reconstructed range differs from the nearby target-boundary range by more than the already-frozen 12 mm association radius.

This is intentionally only a first geometric cue.  Surface-normal continuity is recorded as a future extension, not added here.  If a hole is unobserved or ambiguous, probing it is allowed: an empty/non-target result is itself useful perceptual evidence.

## Experiment

Inputs are the two completed **Reality Check 2b full records**, seeds 2111 and 2179.  Parent renders are never regenerated.

For each record:

1. load the final persistent target surfel map;
2. reconstruct completed prediction-side observation evidence from the saved acquisitions;
3. build the cyclopean support chart and enumerate internal holes;
4. mark any hole already supported as a physical depth break;
5. choose the largest remaining hole by angular area;
6. foveate its spherical centroid **once** (0.1-degree physical-view quantization);
7. fuse target stereo if the inherited Reality Check 2b `<100`-point rule says it is a target measurement; otherwise retain it as negative evidence and fuse nothing;
8. rebuild the same chart and report how the selected hole and map changed.

There is no loop of topology probes in Cyclopean-1a.  It is one probe only.  Integration with the active stopping rule is a later decision.

## Contract

Frozen:

- fixed head and static scene;
- Reality Check 2b scene, texture and seeds;
- FSG1 stereo instrument;
- FSG3 12 mm association/hash;
- FSG6f source and ranking;
- Reality Check 2b empty-look semantics;
- every saved parent fixation and map.

No evaluator truth, mesh reconstruction, hole filling, ICP, new stereo matcher, new frontier ranking, completeness percentage, or numerical quality PASS threshold is permitted.

Structural completion means that both parent records are processed faithfully and any new probe is serialized with pure target geometry and idempotent fusion.  The scientific outputs are descriptive: number/area/state of holes, selected gaze, target points found, map growth and hole-area change.

## Results

_To be filled by Code from workstation measurements.  Preserve the result even if the spherical chart finds no usable hole or the probe returns no target._
