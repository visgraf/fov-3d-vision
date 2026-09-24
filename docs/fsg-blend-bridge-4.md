# FSG Blend Bridge-4 — Controlled Epipolar Capture Sweep

## Purpose

Bridge-3 established, for one sealed Classroom fixation, that the gross far-surface error is not a thin boundary rim. Accepted far pixels can be captured onto the near disparity plateau in a detached, horizontally organized band extending tens of pixels along epipolar rows.

Bridge-4 does **not** repair the matcher. It asks a causal, controlled question:

> With camera, near silhouette, texture realization, baseline, vergence, tangent frame, and the unchanged FSG matcher fixed, how does foreground disparity-capture change when only the farther plane depth is varied?

A second control asks whether capture is strongly suppressed when no near support exists on the pixel's own epipolar row.

## Why a synthetic analytic scene

The Classroom result confounds disparity gap, image distance, object geometry, texture, and occlusion structure. Bridge-4 therefore uses an analytic two-plane tangent scene rather than another natural scene.

The scene contains:

- a finite near fronto-parallel rectangle at `1.40 m`;
- a full far fronto-parallel plane;
- fixed FSG `small` camera geometry at yaw/pitch `0/0`;
- `2.10 m` prescribed vergence;
- `0.063 m` IPD;
- `baseline_projected` tangent frame;
- deterministic rich continuous surface textures.

The near rectangle is fixed across the entire sweep, so the first-hit instance mask is byte-identical for every far depth.

## Manipulation

Far-plane depth only:

```text
1.60, 1.80, 2.00, 2.20, 2.40, 2.80, 3.20 m
```

Each depth is repeated with three fixed texture seeds:

```text
2111, 2112, 2113
```

Total: 21 conditions.

The texture seeds are blocks, not another searched variable: every seed is run at every depth.

## Measurement contract

The generator writes the ordinary FSG observation contract only:

```text
rgb_L
rgb_R
instance_L
instance_R
```

Analytic range/XYZ truth is stored only under `evaluation_only/` and is read only after stereo.

Every condition is processed by the existing `tools/fsg_stereo.py` unchanged. Bridge-4 does not contain an SGBM implementation and does not call Blender, `stereo_field`, a controller, fusion, or FSG6f.

## Capture definition

For an accepted pixel that truly belongs to the far plane:

```text
alpha = (d_est - d_true) / (d_near - d_true)
```

where `d_near` is the median true disparity of the near rectangle.

- `alpha = 0`: correct far disparity;
- `alpha = 1`: near disparity plateau;
- `alpha >= 0.5`: estimate lies closer to the near plateau than to its own true disparity.

The midpoint is geometric, not a tuned stereo threshold.

## Primary measurements

For every depth/texture condition:

- true near/far disparity and median gap;
- far accepted fraction;
- far capture fraction among accepted pixels;
- same-row capture fraction;
- no-near-row capture fraction;
- capture reach along the epipolar row (P50/P90/P95/max);
- row-distance capture profile;
- matched Euclidean-distance comparisons between pixels with and without near support on the same row.

Across texture repeats, Bridge-4 reports mean/standard deviation per depth and a descriptive linear fit of P90 same-row capture reach versus controlled true disparity gap.

The fit is an empirical description of this synthetic regime, not a universal law.

## Interpretation

Three broad outcomes are useful:

1. **Reach increases with controlled disparity gap.** This supports a disparity-dependent scale for foreground capture and rejects a fixed-width silhouette model under this regime.
2. **Capture remains strongly same-row but reach does not scale simply with gap.** The epipolar organization is causal, but the simple gap-scaling hypothesis is insufficient.
3. **The synthetic scene does not reproduce capture.** Then depth separation and scanline geometry alone are insufficient; the Classroom texture/occlusion/path context is an essential part of the beast.

No matcher change follows automatically from any of these outcomes.

## Stop rule

Bridge-4 ends after the 21-condition frozen-instrument sweep and evaluator-only analysis. No SGBM tuning, wider guard, alternative mode, WLS, Census, edge-aware P2, or learned matcher is tested here.

## Results

**BRIDGE4_NO_CAPTURE 2026-09-24 on branch `fsg-blend-bridge-4`.** The sweep ran to
completion: 21 conditions generated, 21 frozen-matcher runs, one analysis pass. The
outcome is the third of the three anticipated ones. **Capture is exactly zero in all 21
conditions.** Nothing in `tools/` was modified.

Manipulating the disparity gap alone, in a clean two-plane scene, does not reproduce the
Classroom failure. What scales with the gap is not the capture zone but the **rejection**
zone.

### Control integrity

| control | evidence |
|---|---|
| only far depth manipulated | manifest `only_manipulated_scene_variable: far_plane_depth_m` |
| near silhouette fixed | **1** distinct L mask sha256 and **1** distinct R across all 21 (checked independently of the generator) |
| near geometry fixed | 1 distinct `(1.40 m, +2.0 deg, 5.0 deg, 6.0 deg)` across 21 |
| observation contract | 1 distinct key set across 21: `{rgb_L, rgb_R, instance_L, instance_R}` |
| matcher unchanged | **1** distinct config across 21 summaries: block 5, LR 1.0 px, guard 3 px, `SGBM_3WAY+bounded_photometric_refinement`, ndisp 64 |
| truth quarantined | truth only under `evaluation_only/`; every summary's `input_sha256` for `observation.npz` matches the file on disk (21/21) |
| no stereo before Phase B | `find -type d -name stereo` empty before the loop |
| analyzer touched nothing | latest stereo mtime precedes earliest Bridge-4 product by **12.77 s**; 6/6 recorded sha256 identical before and after |

L mask `abf973db590f3314...`, R mask `fbde75caf1ce56f1...`. Texture contrast is also
controlled: gray std 15.68-15.70 at every depth, near-surface std 14.24 identical
throughout, so a depth effect cannot be confused with a contrast effect.

### The sweep

| far m | gap px | far accepted (mean +- sd) | capture | same-row capture | no-row capture | reach |
|---|---:|---:|---:|---:|---:|---|
| 1.60 | 3.425 | 0.9231 +- 0.0005 | **0.0000** | 0.0000 | 0.0000 | n/a |
| 1.80 | 6.089 | 0.9081 +- 0.0012 | **0.0000** | 0.0000 | 0.0000 | n/a |
| 2.00 | 8.220 | 0.8966 +- 0.0011 | **0.0000** | 0.0000 | 0.0000 | n/a |
| 2.20 | 9.964 | 0.8862 +- 0.0023 | **0.0000** | 0.0000 | 0.0000 | n/a |
| 2.40 | 11.417 | 0.8776 +- 0.0039 | **0.0000** | 0.0000 | 0.0000 | n/a |
| 2.80 | 13.701 | 0.8651 +- 0.0028 | **0.0000** | 0.0000 | 0.0000 | n/a |
| 3.20 | 15.413 | 0.8553 +- 0.0035 | **0.0000** | 0.0000 | 0.0000 | n/a |

Gap sd is 0.000 at every depth because the gap is fixed by geometry and the three seeds
change only texture. The sweep brackets the Classroom's 12.2 px gap on both sides
(11.417 and 13.701) and finds nothing there.

`descriptive_gap_to_capture_reach_fit` reports `n_depth_conditions: 0` - the analyzer
correctly declines to fit a line to an empty set. This is a degenerate outcome, not a
defect.

### The result is not an analyzer artifact

Recomputed independently with the Bridge-3 machinery on the sealed Bridge-4 outputs:

| far m | d_near | d_far | gap | far accepted | est median | alpha median | alpha P95 | capture |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1.60 | 27.401 | 23.976 | 3.425 | 0.9236 | 23.966 | -0.0030 | 0.0107 | 0.0000 |
| 1.80 | 27.401 | 21.312 | 6.089 | 0.9094 | 21.309 | -0.0005 | 0.0236 | 0.0000 |
| 2.00 | 27.401 | 19.181 | 8.220 | 0.8957 | 19.173 | -0.0009 | 0.0125 | 0.0000 |
| 2.20 | 27.401 | 17.437 | 9.964 | 0.8836 | 17.438 | 0.0000 | 0.0166 | 0.0000 |
| 2.40 | 27.401 | 15.984 | 11.417 | 0.8732 | 15.973 | -0.0009 | 0.0026 | 0.0000 |
| 2.80 | 27.401 | 13.701 | 13.701 | 0.8622 | 13.684 | -0.0012 | 0.0083 | 0.0000 |
| 3.20 | 27.401 | 11.988 | 15.413 | 0.8514 | 11.978 | -0.0007 | 0.0022 | 0.0000 |

`d_near` is constant at 27.401 px - the near-plane control held. Accepted far pixels land
on their own true disparity to about 0.01 px of alpha. The far surface is not partially
captured; it is simply correct. Range error confirms it: near median 3.28-3.92 mm, far
median 1.3-12.2 mm, far P95 4.1-31.6 mm, against the Classroom's 27 mm median and
1,015 mm P95.

### Row-distance profiles (seed 2111)

Acceptance by distance to the near rectangle **along the row**:

| row dist px | gap 3.43 | gap 9.96 | gap 15.41 |
|---|---:|---:|---:|
| 0-4 | 0.0000 | 0.0000 | 0.0000 |
| 4-8 | 0.0898 | 0.0000 | 0.0000 |
| 8-16 | 1.0000 | 0.1895 | 0.0000 |
| 16-32 | 1.0000 | 0.9600 | 0.6777 |
| 32-64 | 1.0000 | 1.0000 | 1.0000 |
| 64+ | 1.0000 | 1.0000 | 1.0000 |
| no near on row | 0.9541 | 0.9492 | 0.9453 |

Capture is 0.0000 in every cell of this table. Maximum alpha anywhere is 0.302, and only
in the thin surviving fringe at gap 3.43; elsewhere the maximum is below 0.09. The zone
that changes with gap is the **rejected** one, and it expands exactly as the table shows:
0-8 px at gap 3.43, 0-16 px at gap 9.96, 0-32 px at gap 15.41.

### What did scale: the half-occlusion rejection band

| statistic | slope px/px | intercept px | R^2 | n |
|---|---:|---:|---:|---:|
| rejected-band P50 vs gap | +0.4705 | +1.1758 | 0.9560 | 21 |
| **rejected-band P90 vs gap** | **+0.9436** | **+2.9885** | **0.9776** | 21 |

The P90 width of the rejected far band grows essentially **one pixel per pixel of
disparity gap** - which is precisely the width of the half-occluded region, the strip of
far surface visible to one eye and hidden behind the near rectangle from the other.
The instrument is doing the geometrically correct thing: it finds no correspondence
there and rejects, rather than accepting the foreground's disparity.

### Visual inspection (seed 2111, low/mid/high gap)

All three maps show the same structure: a white rectangle, a black rejected band, solid
green everywhere else, and **not one red pixel**. The band is strongly asymmetric - thin
on the top, bottom and right edges, and widening to the **left** as the gap grows, which
is the side on which the far surface is half-occluded. Between gap 3.43 and 15.41 the
left band roughly quadruples in width while the other three edges barely change. The
support is horizontal and attached to the silhouette - the opposite of Bridge-3's
detached band.

### Comparison with Bridge-3, and why the scene did not reproduce it

Bridge-3's Classroom capture (not rerun): support began past 4 px, median Euclidean reach
~11 px, P90 ~22 px, max ~35 px, strongly same-row. Bridge-4 at a bracketing gap produces
none of it. Measured on the sealed data of both experiments, two structural differences
stand out at matched gap:

| | Classroom (gap 12.2) | synthetic (gap 11.42) |
|---|---:|---:|
| local 5x5 texture std, near | 7.97 u8 | 7.37 u8 |
| local 5x5 texture std, far | **4.02 u8** | **7.91 u8** |
| near/far texture ratio | **1.98** | **0.93** |
| far-surface disparity slant, vertical | **0.0478 px/px** | **0.0000 px/px** |
| far-surface disparity spread P5-P95 | 15.04-20.40 px | 15.98-15.98 px |
| far accepted fraction | 0.1651 | 0.8732 |

The Classroom foreground carried **twice** the local evidence of its background, and that
background was a **slanted** receding floor whose disparity varied 5.4 px across the core -
a surface the fronto-parallel block assumption penalizes. The synthetic scene equalized the
texture and removed the slant entirely while isolating the gap. Capture vanished.

This identifies two candidate drivers; it does not adjudicate between them. Bridge-4
manipulated neither.

### What this establishes, and what it does not

Established: under a frozen matcher, with a fixed near silhouette and equalized
fronto-parallel texture, **controlled disparity separation alone does not produce
foreground capture** anywhere in the range 3.4-15.4 px, across three texture realizations
and seven depths - 21/21 conditions at exactly zero. Half-occlusion is present and grows
with the gap, and the instrument rejects it correctly, with a band that scales 1:1.
The simple depth-gap scaling hypothesis is **rejected for this regime**.

Not established, and this is the important limitation: **Bridge-4 does not test Bridge-3's
epipolar claim.** With capture identically zero, the same-row and no-near-row controls are
degenerate (0.0000 versus 0.0000) and carry no information. Bridge-3's finding that capture
follows the scanline is neither confirmed nor contradicted here - it was simply not
exercised. The epipolar organization of the *rejection* band is consistent with it but is a
different measurement.

Also not established: that texture asymmetry or surface slant *causes* the Classroom
capture. Both differ sharply at matched gap, which is why each deserves a controlled sweep;
neither was manipulated here. And nothing about other scenes, baselines, vergences,
block sizes or matchers. One synthetic geometry, one gaze, one profile.

Nothing was tuned, no threshold relaxed, no repair attempted, no second scene run.
