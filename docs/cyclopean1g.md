# Cyclopean-1g — Re-centered Measurement Probe

## Question

Cyclopean-1f reached attention completion on seed 2111: no exterior `NEVER_OBSERVED` shoreline remained.  The dominant unresolved geometry is now qualitatively different: an internal residue that has been imaged as target but for which frozen stereo returned no valid depth.

Cyclopean-1g asks one deliberately narrow question:

> If that dominant `OBSERVED_TARGET_NO_DEPTH` residue is placed at the foveal/tangent-chart centre for one new look, does the unchanged stereo instrument recover valid target depth there?

Whatever the outcome, this experiment stops after the one look.  A still-unmeasurable residue is recorded and deferred; it does not start a new rescue subproject.  The next project stage is multiple objects.

## Frozen mechanism

- parent: completed Cyclopean-1f, seed 2111;
- fixed head and static scene;
- same cyclopean chart and 0.1 degree grid;
- same support footprint derived from the frozen 12 mm FSG3 association radius;
- same Reality/FSG renderer, rectification, SGBM front end and render/vergence settings;
- same 12 mm surfel fusion;
- no FSG6f policy or stopping logic;
- no evaluator truth.

## One deliberate measurement change

The only intentional acquisition change is **re-centering**.

1. rebuild the final Cyclopean-1f epistemic shoreline;
2. select only `INTERNAL + OBSERVED_TARGET_NO_DEPTH`;
3. choose the component containing the most such cells;
4. choose the eligible cell nearest that component's no-depth-cell chart centroid;
5. if that exact gaze was already used, take the next cell in the same centroid-distance ordering;
6. acquire exactly one fixation there.

The stereo matcher, baseline, vergence/render settings and all geometric tolerances remain frozen.  This isolates whether a more favorable foveal placement alone can recover depth.

## Outcome

The pre-probe no-depth cells of the selected component are projected into the new saved observation using their already-existing local continuation range.

- `DEPTH_RECOVERED`: at least one selected residue cell is observed as target with valid stereo depth in the new look.
- `DEPTH_STILL_ABSENT`: none is.

This is a diagnostic label, not a PASS/FAIL gate.  The target patch from the new fixation is fused normally if valid depth exists elsewhere in the fovea, and all ordinary structural/idempotence/purity checks remain in force.

## Branch disposition

Cyclopean-1g stops after exactly this one look regardless of outcome.

- If depth is recovered, record that re-centering can rescue at least part of this measurement failure.
- If depth is still absent, record the residue as unresolved under the current fixed-head stereo instrument and defer the case.

In either case, the intended next research stage is **multiple objects**, progressing afterward toward the full cyclopean scene.
