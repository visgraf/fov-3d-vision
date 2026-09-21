# MultiObject-1a — Second Object Seed

## Purpose

Cyclopean-1g closes the current single-object branch for object 141.  The next step introduces exactly one new difficulty: **two foreground object entities in one fixed-head scene representation**.

Object 141 is inherited read-only from the completed Cyclopean-1g record.  Object 143 is declared in advance as the second object and receives exactly one new seed foveation.  No object-growth loop or automatic scene scheduler is introduced.

## Scientific question

> Can the completed object-141 representation coexist with a newly seeded object-143 entity in the same cyclopean scene record without cross-object contamination?

## Seed selection

This is not automatic object discovery.  Object id 143 is fixed by the experiment.  Its seed direction is determined only from object-143 samples that already appeared incidentally in completed prediction-side observations:

1. recompute completed saved stereo observations;
2. collect valid head-frame samples labelled 143;
3. quantize their directions on the inherited 0.1-degree full-profile grid;
4. take the spherical mean of occupied cells;
5. choose the occupied cell nearest that mean;
6. foveate exactly once there.

This gives object 143 a deterministic prescribed seed while avoiding scene/evaluator truth.

## Representation

The output scene contains two separate foreground entities:

- **141** — the inherited persistent surfel map, untouched;
- **143** — the new seed surfel patch from one fixation.

Both are registered on a shared 0.1-degree cyclopean chart for a first multi-object footprint visualization.  They are not merged into one surfel map.

## Deliberately not included

- no growth of object 143;
- no automatic search for a next object;
- no multi-object scheduler;
- no mesh or semantic relation inference;
- no evaluator truth;
- no quality threshold.

If this structural coexistence works, the next step can ask whether object 143 can be grown independently while object 141 remains stable.
