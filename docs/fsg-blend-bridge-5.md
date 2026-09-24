# FSG Blend Bridge-5 — controlled texture × slant factorial

## Question

Bridge-4 rejected the simple hypothesis that disparity separation alone produces the detached foreground-disparity capture seen in the Classroom. At a matched gap, two measured differences remained: the Classroom foreground had about twice the local texture evidence of the background, and the background was a vertically slanted disparity surface (~0.0478 px/px) rather than fronto-parallel.

Bridge-5 asks, with the native FSG matcher frozen:

> Are background slant and/or foreground/background texture-strength asymmetry sufficient to trigger the detached epipolar foreground-disparity capture?

## Design

A predeclared 2×2 factorial, repeated for texture seeds 2111, 2112, 2113:

| Cell | Far geometry | Far texture gain | Purpose |
|---|---|---:|---|
| A | flat (`k=0`) | 1.0 | Bridge-4-like control |
| B | flat | 0.44 | texture asymmetry only |
| C | slanted (`k=1.8`) | 1.0 | slant only |
| D | slanted | 0.44 | slant + texture asymmetry |

Everything else is fixed: small profile, yaw/pitch 0/0, vergence 2.10 m, IPD 63 mm, baseline-projected tangent frame, near plane 1.40 m, far base depth 2.40 m, near silhouette, near texture, and unchanged `tools/fsg_stereo.py`.

The far base depth 2.40 m gives approximately the Bridge-4 11.4 px gap, close to the sealed Classroom ~12.2 px case. `k=1.8` was selected prospectively from camera geometry because it yields approximately 0.047 px/px vertical true-disparity slant, close to the sealed Classroom ~0.0478 px/px. The far texture gain 0.44 targets the sealed Classroom near/far local-texture ratio near 2:1; the analyzer reports the measured ratio rather than assuming it.

## Measurement

Capture uses the unchanged Bridges 3/4 definition:

`alpha = (d_est - d_true) / (d_near - d_true)`

`alpha >= 0.5` means the estimate is closer to the foreground disparity plateau than to its own far-surface truth.

Per condition the evaluator reports measured true disparity gap/slant, local 5×5 texture evidence, far acceptance, capture fraction/count, capture reach, and same-row versus no-near-row behavior. The aggregate reports all four factorial cells and descriptive contrasts B−A, C−A, D−C, D−B, and the interaction `D-C-B+A`.

## Boundaries

This experiment does not tune or repair SGBM. It does not change block size, mode, P1/P2, LR tolerance, the 3-px instance guard, depth bounds, or texture threshold. It does not launch Blender, use the Classroom fixation, run a controller, or fuse observations. Analytic truth remains under `evaluation_only/` and is used only after stereo.

## Results

**BRIDGE5_NO_CAPTURE 2026-09-24 on branch `fsg-blend-bridge-5`.** 12 conditions generated,
12 frozen-matcher runs, one analysis pass. **Capture is exactly zero in all four cells and
all 12 conditions.** Every factorial contrast is exactly 0.0. Nothing in `tools/` changed.

One important qualification, measured below: the slant factor was a valid manipulation and
is shown insufficient. The texture factor, as implemented, **did not change the matcher's
evidence at all**, so the texture-asymmetry hypothesis is not so much refuted as untested.

### Control integrity

| control | evidence |
|---|---|
| 12 conditions, exactly the declared grid | 12 distinct (slant, texture, seed) triples |
| near silhouette identical | **1** distinct L mask sha256, **1** distinct R, across all 12 |
| same foreground as Bridge-4 | L mask `abf973db590f3314...` is byte-identical to Bridge-4's |
| camera/geometry fixed | 1 distinct `(near 1.40, far base 2.40, +2.0 deg, 5.0, 6.0)` |
| observation contract | 1 distinct key set: `{rgb_L, rgb_R, instance_L, instance_R}` |
| matcher unchanged | **1** distinct config in all 12 summaries: block 5, LR 1.0, guard 3, `SGBM_3WAY+bounded_photometric_refinement`, ndisp 64, bounds [0.75, 4.5], texture floor 0.5 |
| truth quarantined | truth only under `evaluation_only/`; 12/12 summaries' `input_sha256` match the file on disk |
| no stereo before Phase B | `find -type d -name stereo` empty |
| analyzer changed nothing | 8/8 recorded sha256 identical before and after |

Pre-stereo controls, seed 2111, all four cells: near bounding box identical
(`x159-211 y128-191`), L-R silhouette shift 9 px, near mean RGB identical to four decimals
(`[0.4853, 0.3821, 0.2844]`). Far mean RGB is unchanged by the texture gain
(`[0.3401,...]` vs `[0.3400,...]`), so the manipulation is **contrast only, with no
brightness confound**.

**Unplanned replication check:** cell A reproduces Bridge-4's 2.40 m flat condition
bit-exactly - valid counts 13927 / 14091 / 14060 for seeds 2111/2112/2113 in both
experiments. The control cell is a literal re-run of the matched Bridge-4 case.

### Measured manipulation strength

| | cell | k | gain | gap px | slant px/px | near std | far std | ratio |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| A | flat/equal | 0.0 | 1.00 | 11.417 | -0.0000 | 5.18-6.42 | 5.64-7.38 | 0.86-0.99 |
| B | flat/near2x | 0.0 | 0.44 | 11.417 | -0.0000 | 5.18-6.42 | 2.48-3.26 | **1.97-2.26** |
| C | slanted/equal | 1.8 | 1.00 | 11.417 | **0.0472** | 5.18-6.42 | 5.83-7.02 | 0.86-0.96 |
| D | slanted/near2x | 1.8 | 0.44 | 11.417 | **0.0472** | 5.18-6.42 | 2.56-3.12 | **1.98-2.19** |

Sealed Classroom targets: gap 12.2 px, slant 0.0478 px/px, ratio 1.98. Both manipulations
land on target - slant to within 1.3%, texture ratio to within 1% in the seed-2111 cells.
The design did not undershoot.

### Stereo behaviour - all 12 rows

| cell | condition | far accepted | captured | capture frac | reach | same-row | no-row |
|---|---|---:|---:|---:|---|---:|---:|
| A | flat-equal-2111/2112/2113 | 0.8732 / 0.8807 / 0.8790 | 0 / 0 / 0 | 0.0000 | n/a | 0.0000 | 0.0000 |
| B | flat-near2x-2111/2112/2113 | 0.8762 / 0.8775 / 0.8782 | 0 / 0 / 0 | 0.0000 | n/a | 0.0000 | 0.0000 |
| C | slanted-equal-2111/2112/2113 | 0.8732 / 0.8794 / 0.8792 | 0 / 0 / 0 | 0.0000 | n/a | 0.0000 | 0.0000 |
| D | slanted-near2x-2111/2112/2113 | 0.8765 / 0.8762 / 0.8754 | 0 / 0 / 0 | 0.0000 | n/a | 0.0000 | 0.0000 |

No cell is omitted; all twelve are zero. Matched 4-12 px same-row and no-row capture
fractions are undefined or 0.0000 throughout - there are no captured pixels to compare.

### Four-cell aggregate (mean +- SD, n = 3)

| cell | gap px | slant px/px | near/far ratio | far accepted | capture |
|---|---:|---:|---:|---:|---:|
| A | 11.417 +- 0.000 | -0.0000 +- 0.0000 | 0.91 +- 0.07 | 0.8776 +- 0.0039 | 0.0000 +- 0.0000 |
| B | 11.417 +- 0.000 | -0.0000 +- 0.0000 | 2.07 +- 0.17 | 0.8773 +- 0.0010 | 0.0000 +- 0.0000 |
| C | 11.417 +- 0.000 | 0.0472 +- 0.0000 | 0.91 +- 0.05 | 0.8773 +- 0.0036 | 0.0000 +- 0.0000 |
| D | 11.417 +- 0.000 | 0.0472 +- 0.0000 | 2.08 +- 0.10 | 0.8761 +- 0.0006 | 0.0000 +- 0.0000 |

Neither factor moved far acceptance measurably: all four cells sit at 0.876-0.878.

### Factorial contrasts (capture fraction)

| contrast | value |
|---|---:|
| B - A, texture when flat | **0.0** |
| C - A, slant when balanced | **0.0** |
| D - C, texture when slanted | **0.0** |
| D - B, slant when asymmetric | **0.0** |
| D - C - B + A, interaction | **0.0** |

No significance test is introduced; the outcome is structurally degenerate.

### The result is not an analyzer artifact

Recomputed with the Bridge-3 machinery on the sealed Bridge-5 outputs, `d_near` constant at
27.401 px and gap at 11.417 px in every condition:

| cell | alpha median | alpha P95 | alpha max | capture | far err median |
|---|---:|---:|---:|---:|---:|
| A | -0.0009 | 0.0026 | 0.0726 | 0.0000 | 2.62 mm |
| B | -0.0010 | 0.0025 | 0.0780 | 0.0000 | 2.62 mm |
| C | -0.0008 | 0.0192 | 0.0989 | 0.0000 | 9.21 mm |
| D | -0.0006 | 0.0197 | 0.1117 | 0.0000 | 8.95 mm |

The maximum alpha anywhere in the experiment is **0.112** - a factor of 4.5 short of the
0.5 capture threshold, and 22x short of the Classroom's alpha P75 of 1.13.

### The factorial on continuous outcomes, where capture is degenerate

| contrast | alpha P95 | alpha max | far err median | far err P95 |
|---|---:|---:|---:|---:|
| B - A, texture when flat | +0.00007 | +0.018 | +0.017 mm | +0.49 mm |
| **C - A, slant when balanced** | **+0.01541** | +0.023 | **+6.42 mm** | **+35.74 mm** |
| D - C, texture when slanted | +0.00008 | +0.006 | -0.38 mm | +1.16 mm |
| **D - B, slant when asymmetric** | **+0.01542** | +0.011 | **+6.02 mm** | **+36.41 mm** |
| interaction D-C-B+A | +0.00000 | -0.012 | -0.40 mm | +0.67 mm |

**Slant is a real and almost perfectly additive effect**: it multiplies alpha P95 by 7.3x
(0.0025 -> 0.0182), far median error by 3.5x (2.58 -> 8.80 mm) and far P95 error by 5.1x
(8.94 -> 45.02 mm), with the same magnitude whether texture is balanced or asymmetric
(+0.01541 and +0.01542). **Texture asymmetry is a null on every measure** - three to four
orders of magnitude smaller. The interaction on alpha P95 is exactly +0.00000.

So slant genuinely degrades the reconstruction and genuinely pulls estimates toward the
plateau - and still stops 4.5x short of capture.

### Morphology - Bridge-4-like in every cell

| cell | red px | rejected far | rejected P90 row | min Euclidean | 8-adjacent to near |
|---|---:|---:|---:|---:|---:|
| A | **0** | 1550-1647 | 14.0 | 1.00 | 238 |
| B | **0** | 1583-1609 | 13.7 | 1.00 | 238 |
| C | **0** | 1567-1648 | 14.1 | 1.00 | 238 |
| D | **0** | 1604-1619 | 14.0 | 1.00 | 238 |

Zero red pixels in all twelve maps. The morphology is identical in every cell and is
unambiguously **Bridge-4 attached half-occlusion rejection**, not Bridge-3 detached
capture: the band starts at Euclidean distance 1.00 px with exactly 238 pixels 8-adjacent
to the near rectangle in every condition, and its P90 row reach of ~14 px matches the
1:1 law Bridge-4 fitted at this 11.4 px gap. Bridge-3's Classroom capture, by contrast,
began at 4.197 px with **zero** pixels adjacent. Visual inspection of cells A-D at seed
2111 agrees: white rectangle, black attached band widening to the left, solid green
elsewhere, no red.

### Why the texture factor was a null - a measurement, not a guess

Match evidence on the far surface, NCC along the epipolar row (block 5, ndisp 64):

| surface | NCC peak median | peak P10 | 2nd-peak ratio median | fraction ratio > 0.9 |
|---|---:|---:|---:|---:|
| **Classroom floor** (47% captured) | **0.5444** | **0.3613** | 0.8911 | 0.4554 |
| B5 A flat/equal | 0.9515 | 0.8106 | 0.9650 | 0.8067 |
| B5 B flat/near2x | 0.9478 | 0.8118 | 0.9623 | 0.7817 |
| B5 C slanted/equal | 0.9709 | 0.8420 | 0.9631 | 0.7842 |
| B5 D slanted/near2x | 0.9612 | 0.8502 | 0.9642 | 0.7783 |

A reduced the far texture std from 6.01 to 2.62 u8 - a **2.3x contrast reduction** - and
changed the NCC peak by **0.4%** (0.9515 -> 0.9478). Normalized correlation is invariant
to a uniform contrast scale, and these images have **no noise floor**, so scaling the
texture down scaled signal without raising noise. The manipulation moved the reported
std ratio to the Classroom's ~2:1 while leaving the matcher's actual evidence untouched.

This also corrects a plausible guess: the synthetic surfaces are **more** self-similar
than the Classroom floor (2nd-peak ratio 0.963 vs 0.891; 78% vs 46% of pixels with a rival
above 0.9). Ambiguity was not the missing ingredient either. What separates the Classroom
is **absolute match strength** - peak 0.54 with a P10 of 0.36, against 0.95 and 0.81 here.
The Classroom floor's correspondence was genuinely weak; Bridge-5's, at any contrast, was
not.

### What this establishes, and what it does not

Established: with the gap held at 11.417 px and the foreground silhouette byte-identical
to Bridge-4's, **a background disparity slant matching the Classroom's to 1.3% does not
produce foreground capture** - zero in 6/6 slanted conditions, maximum alpha 0.112. Slant
is a real effect on accuracy (3.5x median error, 7.3x alpha P95, additive) and is
nonetheless **insufficient**. The morphology stays Bridge-4 attached rejection in every
cell. And the control cell reproduces Bridge-4 bit-exactly.

Not established, and this is the limitation that matters: **the texture-asymmetry factor
was not validly manipulated.** It achieved the declared 2:1 std ratio but changed match
evidence by 0.4%, because contrast scaling without a noise floor leaves normalized
correlation invariant. Cells B and D therefore do not test the hypothesis; reading them as
a refutation would be wrong. The tested interaction is likewise between a real factor and
a null one.

Also not established: that weak match strength causes the Classroom capture. The NCC
comparison identifies it as the largest remaining measured difference (0.54 vs 0.95) and
rules ambiguity out as the driver, but Bridge-5 manipulated neither. And nothing about
thin geometry, inter-eye photometric asymmetry, render noise, grazing foreshortening, or
any non-planar background - all still uncontrolled.

Nothing was tuned, no threshold relaxed, no repair attempted, no second sweep run.
