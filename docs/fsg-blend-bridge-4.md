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
