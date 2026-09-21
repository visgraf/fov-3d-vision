# Cyclopean-1b — spherical shoreline audit

## Question

Cyclopean-1a established that the cyclopean chart can distinguish an enclosed
sampling hole from the exterior and can turn one genuine internal hole into one
useful foveation.  It also corrected the visual interpretation of seed 2111:
the conspicuous missing region is not a lake but a **bay**, connected to the
exterior through a left-side channel.

Cyclopean-1b asks the next smaller question:

> Can the same fixed-head cyclopean domain describe the *shoreline* of the
> sampled object, distinguish internal from exterior-connected complement, and
> say which boundary arcs are observed physical depth breaks versus continuation,
> unobserved, or ambiguous — without taking another fixation?

This is an audit, not a controller extension.

## Representation

The metric surfel map remains authoritative.  Cyclopean-1b reuses the exact
Cyclopean-1a angular chart: D9's `2*s0` grid and the support footprint derived
from the frozen FSG3 12 mm association radius.  No new geometric tolerance is
introduced.

A **shoreline cell** is a complement cell that is 8-adjacent to current target
support.  Every shoreline cell retains the identity of the complement component
it belongs to:

- `INTERNAL`: the component does not touch the padded chart border;
- `EXTERIOR`: the component does touch the padded chart border.

Border-touching therefore means only *topologically exterior*.  It does **not**
mean that the object has been observed to end there.

## Boundary semantics

Existing completed prediction-side observations are projected into the same
chart.  Each shoreline cell is labelled:

- `UNOBSERVED`: neither target nor non-target evidence was acquired there;
- `TARGET_CONTINUATION`: target-only evidence exists there;
- `PHYSICAL_DEPTH_BREAK`: non-target-only evidence exists and its range differs
  from the nearby target boundary by more than the already-frozen 12 mm FSG3
  association radius;
- `AMBIGUOUS`: all other observed cases.

Adjacent cells with the same state and complement-component identity form a
boundary arc.  No minimum arc length, smoothing rule or tuned morphology is
introduced.

For exterior complement only, the audit also reports the 8-connected shortest
path distance, in complement cells, from the padded chart border.  This is a
purely descriptive **exterior penetration depth**.  A deep bay can therefore be
reported without inventing a threshold that declares it important.

## Experiment

Inputs are the two completed **Cyclopean-1a full records**, seeds 2111 and 2179,
after the one-probe experiment.  They are located by manifest, not by assumed
path.

For each record:

1. load `map_before.npz` to reconstruct the exact Cyclopean-1a chart;
2. load the final `surface_map.npz` as current target geometry;
3. rebuild prediction-side evidence from the Reality Check 2b ancestry and, when
   present, the single Cyclopean-1a probe;
4. rasterize the final target support on the inherited chart;
5. enumerate internal/exterior complement components and their shoreline;
6. classify shoreline cells and connected same-state arcs;
7. report exterior penetration depth and write one diagnostic image.

There is **no Blender invocation, no new fixation, no map fusion and no stopping
rule** in Cyclopean-1b.

## Contract

Frozen:

- fixed head and static scene;
- all Reality Check 2b and Cyclopean-1a acquisitions and maps;
- FSG1 stereo instrument;
- FSG3 12 mm association scale;
- FSG6f;
- Cyclopean-1a grid and support footprint.

Forbidden: evaluator truth, mesh reconstruction, hole filling, boundary
smoothing/tuning, a minimum-arc filter, a new ranking policy, a probe selection,
new acquisition, completeness percentage, or numerical quality PASS threshold.

Structural completion means only that both parents are audited read-only and the
reported artifacts satisfy provenance/integrity checks.  The scientific outputs
are descriptive.

## Results

Pending workstation execution.
