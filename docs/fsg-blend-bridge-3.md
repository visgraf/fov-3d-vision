# FSG Blend Bridge-3 — foreground-fattening structure audit

## Purpose

Bridge-1R established the `.blend -> tangent pair -> rectification -> unchanged SGBM -> metric patch` path on a near-ideal planar fixation. Bridge-2 froze that instrument and introduced real local structure. The dominant near surface remained accurate, but a large tail appeared on the farther floor: many accepted far-surface pixels were reconstructed at approximately the near chair-seat disparity even after the fixed boundary guard and LR-consistency test had removed the immediate boundary band.

Bridge-3 does **not acquire another fixation and does not rerun stereo**. It analyzes the already sealed Bridge-2 result to describe the spatial and disparity structure of that foreground capture.

## One question

> Within the fixed Bridge-2 result, how far into the farther surface does the near-surface disparity plateau capture accepted pixels, and how is that capture associated with image-space distance and true disparity separation?

This is a descriptive structure audit of one fixation. It cannot establish a universal scaling law.

## Capture coordinate

For an accepted pixel whose evaluator truth belongs to the dominant farther surface,

```text
alpha = (d_est - d_true) / (d_near - d_true)
```

where `d_near` is the median evaluator-truth disparity of the dominant near surface.

- `alpha = 0`: estimated at its own true far disparity.
- `alpha = 1`: estimated at the near-surface plateau.
- `alpha >= 0.5`: estimate is closer to the near plateau than to its own truth.

The `0.5` split is a geometric midpoint, not a tuned quality threshold.

## Controls

Bridge-3 must:

- consume the existing Bridge-2 run only;
- not call Blender;
- not call or modify SGBM;
- not change validity, disparity, XYZ, or accepted points;
- keep Blender truth evaluator-only;
- derive estimated disparity from the already sealed estimator XYZ plus frozen rectification;
- use the dominant two truth instances dynamically, not hard-coded Classroom IDs.

## Measurements

The audit writes:

- `bridge3_fattening.json`
- `bridge3_distance_profile.csv`
- `bridge3_alpha.npy`
- `bridge3_distance_to_near_px.npy`
- `bridge3_truth_disparity_px.npy`
- `bridge3_est_disparity_px.npy`
- `bridge3_capture_map.png`

It reports:

1. dominant near/far instance IDs, support, range and true disparity;
2. accepted fraction on the farther surface;
3. capture fraction among accepted far pixels;
4. P50/P75/P90/P95/max capture distance from the near surface;
5. fraction of captured pixels beyond 3, 6, 12 and 24 px;
6. validity/capture/error profile by distance band;
7. capture by true disparity-gap quartile;
8. a distance x disparity-gap interaction table;
9. simple within-fixation correlations;
10. same-row and same-column distances for captured vs non-captured far pixels.

## Interpretation boundary

A result showing capture well beyond three pixels would strengthen the Bridge-2 conclusion that a fixed-width boundary guard does not match the observed failure support. A dependence on true disparity gap would motivate a later controlled depth-sweep experiment. Neither conclusion is universal from this one fixation alone.

Bridge-3 is analysis, not a repair.
