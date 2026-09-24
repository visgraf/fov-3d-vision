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

## Results

**BRIDGE3_COMPLETE 2026-09-24 on branch `fsg-blend-bridge-3`.** The audit ran once on the
sealed Bridge-2 run. No Blender call, no stereo rerun, no estimator output altered; the
four sealed files carry identical sha256 before and after. Nothing in `tools/` changed.

The answer is unambiguous: **the capture is not a boundary rim.** Not one captured pixel
touches the near surface, and every captured pixel lies beyond three pixels from it.

### The dominant pair, derived dynamically

The analyzer ranks truth instances by support in the rectified core and orders the top two
by median range; no Classroom ID is hard-coded.

| | near | far |
|---|---|---|
| instance id / root | **7** `Box297.002` (chair seat) | **159** `sol` (floor) |
| truth pixels in the 128x128 core | 10,066 | 5,755 |
| median true range | 1.4232 m | 2.2792 m |
| median true disparity | 30.724 px | 18.517 px |
| accepted pixels | 4,698 | 950 |

The accepted counts reproduce Bridge-2's per-instance split (4,698 / 950) exactly, so the
audit is describing the same dominant pair.

### Far-surface acceptance and capture

| quantity | value |
|---|---:|
| far truth pixels | 5,755 |
| far accepted | **950 (16.51%)** |
| far captured (`alpha >= 0.5`) | **446 (46.95% of accepted)** |
| alpha median / P75 / P90 / P95 / max | 0.0746 / 1.1323 / 1.2921 / 1.7912 / 2.5432 |
| abs disparity error median / P90 | 4.836 / 15.734 px |

Alpha is sharply bimodal: the median accepted far pixel is nearly correct (0.07) while the
P75 already sits past the plateau (1.13). That matches Bridge-2's bimodal signed floor error.

Captured pixels genuinely sit **on the plateau**, not merely off their own truth:

| | median estimated disparity |
|---|---:|
| near surface (its own accepted pixels) | 31.875 px |
| **captured far pixels** | **32.562 px** |
| non-captured far pixels | 18.740 px |
| (captured pixels' own true disparity) | 18.386 px |

Captured far pixels land 0.69 px from the seat's own estimated disparity while being
14.2 px away from their own truth. Non-captured far pixels sit 0.94 px from their truth.

### Spatial reach - the central test

Distance from captured pixels to the near-surface support:

| statistic | px |
|---|---:|
| median | **10.98** |
| P75 | 17.19 |
| P90 | 22.28 |
| P95 | 25.73 |
| max | 34.95 |

| beyond | fraction of captured |
|---|---:|
| 3 px | **1.0000** |
| 6 px | 0.8834 |
| 12 px | 0.4372 |
| 24 px | 0.0807 |

**Every captured pixel is beyond 3 px.** The nearest is at 4.197 px, and no captured pixel
is 8-adjacent to the near support. A fixed-width boundary guard of the current size cannot
touch this failure; widening it to cover the median would cost 11 px of every silhouette.

### Distance profile

| band px | far truth | valid | valid frac | capture frac | alpha median | disp err median px |
|---|---:|---:|---:|---:|---:|---:|
| 0-3 | 667 | **0** | 0.000 | - | - | - |
| 3-6 | 768 | 83 | 0.108 | 0.6145 | 0.854 | 12.213 |
| 6-9 | 677 | 137 | 0.202 | 0.8613 | 0.892 | 12.773 |
| 9-12 | 574 | 99 | 0.172 | 0.8283 | 1.073 | 13.205 |
| 12-16 | 485 | 69 | 0.142 | **0.9710** | 1.188 | 14.317 |
| 16-24 | 784 | 108 | 0.138 | 0.8519 | 1.182 | 14.394 |
| 24-32 | 662 | 124 | 0.187 | 0.2177 | -0.027 | 1.369 |
| 32-48 | 886 | 203 | 0.229 | 0.0443 | -0.072 | 0.927 |
| 48-96 | 252 | 127 | **0.504** | 0.0000 | -0.108 | 1.222 |

The shape is a plateau, not a decay: capture stays between 61% and 97% from 3 px all the
way to 24 px, peaks at **12-16 px**, then collapses over one band to 4% and reaches zero by
48 px. Disparity error moves with it - about 12-14 px inside the capture zone against about
1 px outside. Where capture ends, both validity and accuracy recover: the 48-96 px band is
50.4% accepted with 1.2 px of error.

### True disparity gap

| quartile | gap px | n | capture frac | alpha median | distance median px |
|---|---|---:|---:|---:|---:|
| 1 | 10.246-10.922 | 238 | 0.0630 | -0.088 | 46.14 |
| 2 | 10.922-11.676 | 237 | 0.2574 | -0.018 | 34.35 |
| 3 | 11.676-13.015 | 237 | 0.8734 | 1.182 | 14.98 |
| 4 | 13.015-15.782 | 238 | 0.6849 | 0.836 | 7.20 |

Capture appears to rise with gap - but **distance falls monotonically across the same
quartiles** (46 -> 7 px). On this floor the two are confounded by construction: the floor
visible beside the seat is the deeper floor behind it, so large gap and small image
distance are the same pixels. The gap margin alone cannot be read causally.

The interaction table separates them, and distance wins:

| | 0-3 px | 3-6 px | 6-12 px | 12-24 px | 24+ px |
|---|---|---|---|---|---|
| gap Q1 | - | 1.000 (2) | 1.000 (11) | 1.000 (2) | 0.000 (223) |
| gap Q2 | - | - | 1.000 (11) | 0.697 (33) | 0.140 (193) |
| gap Q3 | - | 1.000 (10) | 1.000 (75) | 0.958 (118) | 0.265 (34) |
| gap Q4 | - | 0.549 (71) | 0.741 (139) | 0.875 (24) | 0.000 (4) |

Within 3-24 px capture is high in **every** gap quartile including the smallest; beyond
24 px it is low in every quartile including the largest. The residual ordering at 24+ px
(0.000, 0.140, 0.265) is suggestive but rests on small, unbalanced cells. This is a reason
to run a controlled depth sweep, not evidence of a depth-ratio law.

### Directional geometry - capture follows the scanline

Distance to the near surface along one axis only:

| group | n | row median | column median |
|---|---:|---:|---:|
| captured | 437 / 397 | **14.0** | 25.0 |
| not captured | 490 / 403 | 57.5 | 75.0 |

Both groups sit at a row/column ratio near 0.55 once matched on euclidean distance, which
is the seat's own wide footprint rather than a stereo effect. Conditioning on the row
distance directly removes that confound:

| same-row distance to seat | n | capture fraction |
|---|---:|---:|
| 4-8 px | 52 | **1.000** |
| 8-16 px | 187 | **1.000** |
| 16-32 px | 192 | 0.854 |
| 32-64 px | 291 | 0.113 |
| 64-128 px | 205 | 0.005 |

And the controlled comparison, holding euclidean distance at 4-12 px:

| | n | capture fraction |
|---|---:|---:|
| seat present on the same row within 24 px | 224 | **1.000** |
| seat absent from the row (>= 24 px) | 74 | 0.243 |

Equally close to the seat in the image, a far pixel is captured **only if the seat lies on
its own scanline**. The support is strongly epipolar, and along the row it reaches about
32 px - roughly ten times the 3-px guard.

### Associations (descriptive, n = 950)

| pair | r |
|---|---:|
| alpha vs distance to near | -0.597 |
| alpha vs true disparity gap | +0.199 |
| capture vs distance to near | **-0.700** |
| capture vs true disparity gap | +0.356 |

Within-fixation correlations on spatially autocorrelated pixels. They rank the two
candidates; they do not establish causation.

### Visual inspection of `bridge3_capture_map.png`

The seat fills the centre-right as a bright quadrilateral with its edge running diagonally
from top-left to bottom-centre; two small grey patches inside it are the fixings, and grey
also marks the upper-left wedge and a lower band.

The red capture region is a **broad zone, detached from the seat**. Between the seat edge
and the nearest red there is a continuous black band of rejected floor - the 0-3 px band
holds 667 far pixels and not one survived. The red then forms substantial blobs: 42
connected components, 66.1% of captured pixels in components of 20 px or more, the largest
141 px at 27x14 (aspect 1.93, horizontally elongated) spanning 4.4-23.0 px of distance.
One 38-px component sits entirely at 19.4-27.0 px, a genuine disconnected island. Only
11.2% of captured pixels are speckle under 5 px. Green - accepted and correct - appears
only farther out, dominating the lower-left corner where the floor is nearest the observer
and the seat has left the scanline.

Morphology in one line: **not a rim, but a detached horizontally-elongated band standing
off the silhouette and reaching about two dozen pixels into the floor.**

### What this establishes, and what it does not

Established, for this one sealed fixation: the foreground capture reported by Bridge-2 is
real, it places far pixels within 0.7 px of the near surface's own estimated disparity, and
its support is **disjoint from the instance boundary** - zero captured pixels adjacent to
the seat, none within 4.197 px, median reach 10.98 px, maximum 34.95 px. Capture is
governed by distance **along the scanline** (100% within 16 px of seat on the row, 0.5%
beyond 64 px), which is the signature of the matcher's own search direction. Validity and
accuracy both recover fully once the near surface leaves the row.

Not established: anything universal. One fixation, one gaze, one profile, one baseline,
one vergence, one pair of surfaces, one texture regime. The apparent disparity-gap effect
is confounded with distance here and survives only weakly after stratification. Nothing
here says what the right guard is, or that any guard is the right instrument - only that a
**fixed-width erosion around the silhouette is structurally mismatched to a failure whose
support begins at 4 px and extends past 30.** No repair was attempted, no threshold
touched, no second fixation run.
