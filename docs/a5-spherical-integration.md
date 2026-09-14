# Step A5 — spherical integration and the error-versus-budget curve

State on 2026-09-13, second pass: `tools/integrate_sphere.py` now integrates finest-owns
(D9 pass), reconstructs the sphere at a declared evaluation scale s_eval = 2 s0 and measures
the error there (D9); the per-sample footprint-aware comparison (D8) is kept as a validation
check. Run on both mesh scenes at `--profile small`. Everything here was measured on the
workstation unless marked assumed.

The result: **at the targets foveation beats uniform sampling at every budget on both
scenes** (1.8x on the calibration room and 5x on the Classroom at the largest K); **over the
sphere uniform wins on the calibration room until the largest budget**, where the two are
level on the part the fixations cover, and on the Classroom they are level at K = 10, in both
cases with the foveated leaving a reported fraction of the sphere uncovered.

## Why the metric moved (D9)

D8 compares each cell to the reference at the cell's own footprint, so a coarse uniform
render is charged only for its noise and never for its blur; that is why 2.3 deg pixels
"won" at K = 1 in the first pass. The curve is now measured at s_eval = 0.2 deg (small
profile): the representation is reconstructed at s_eval and compared to the reference
box-filtered to s_eval. A uniform render is upsampled to the reference grid (nearest) and
filtered the same way, so its blur is charged like everyone else's. D8 stays as the
validation check, judged at the 0.5 deg bin against the median measured (b) bound.

Integration is finest-owns: per cell, only samples whose footprint is within 1.5x the finest
footprint present there contribute (weighted 1/footprint among themselves); coarser samples
go to a separate fill layer, used only where the finest layer has no coverage. This removes
the blur leak of the first pass (coarse share 0.50 at the targets). Cells covered by nothing
are excluded from the error and their fraction is always reported beside it; an s_eval block
counts as covered when at least one of its cells is, and the partly covered fraction is
reported too (0.2 to 3% here).

## Commands (D9 pass)

```bash
# calibration point: uniform at the full s0 resolution and the fixation spp, two seeds
blender -b scenes/calib_room/calib_room.blend -P tools/preview360.py -- --out previews/uniform/calib_room/w3600_seed0 --width 3600 --spp 64 --filter BOX --no-backface --seed 0
blender -b scenes/calib_room/calib_room.blend -P tools/preview360.py -- --out previews/uniform/calib_room/w3600_seed1 --width 3600 --spp 64 --filter BOX --no-backface --seed 1
.venv/bin/python tools/integrate_sphere.py previews/sequence/calib_room --reference previews/reference_small/calib_room \
    --out previews/integrated/calib_room --uniform previews/uniform/calib_room --bound 0.0263 \
    --calibration previews/uniform/calib_room/w3600_seed0 --calibration-b previews/uniform/calib_room/w3600_seed1
.venv/bin/python tools/integrate_sphere.py previews/sequence/classroom --reference previews/reference_small/classroom \
    --out previews/integrated/classroom --k-list 1,2,5,10 --uniform previews/uniform/classroom --bound 0.0614
```
About 60 s and 25 s. Outputs `curve.json`, `curve.csv`, `curve.png`, `integrated.npz`,
`rgb.png`, `min_footprint.png` under `previews/integrated/<scene>/`; the two charts are also
committed as `docs/reference/a5_curve_<scene>_small.png`.

## The D9 curve, calibration room (50 targets, small profile, 64 spp, s_eval 0.2 deg)

Foveated (F) against uniform (U) at the same ray budget; relative RMS at s_eval. "uncov" is
the fraction of the sphere the foveated representation leaves uncovered, excluded from its
sphere error. Seconds: seed-0 renders from `sequence.json` (warm-up 0.309 s excluded) and
preview360's timer (includes the EXR write).

| K | rays | F s | targets F | targets U | sphere F | uncov | sphere U | U W | U s |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.80 M | 0.016 | 0.292 | 0.347 | 0.546 | 0.868 | 0.296 | 158 | 0.35 |
| 2 | 1.60 M | 0.033 | 0.284 | 0.323 | 0.535 | 0.852 | 0.280 | 224 | 0.34 |
| 5 | 4.00 M | 0.082 | 0.276 | 0.315 | 0.524 | 0.840 | 0.251 | 354 | 0.36 |
| 10 | 7.99 M | 0.162 | 0.261 | 0.300 | 0.503 | 0.822 | 0.227 | 500 | 0.41 |
| 20 | 15.99 M | 0.319 | 0.240 | 0.302 | 0.428 | 0.779 | 0.194 | 706 | 0.49 |
| 50 | 39.97 M | 0.779 | 0.161 | 0.294 | 0.140 | 0.416 | 0.151 | 1118 | 0.71 |

Resampling floor at s_eval (reference vs its bilinear half-pixel shift, both filtered to
s_eval): 0.217 at the targets, 0.089 over the sphere. The foveated target error at K = 50
sits below that floor, so the floor as defined overstates registration: a bilinear
half-pixel shift is also a 2x2 blur, which on Siemens stars costs more than the shift.

Targets: foveated wins at every K, by 0.05 at K = 1 rising to 1.8x at K = 50; targets not
yet fixated are reached by other fixations' peripheries (33% of target blocks uncovered at
K = 1, 0% at K = 50). **Sphere: uniform wins at every K below 50**, and by a wide margin (0.25
against 0.52 at K = 5), because the foveated coverage is mostly periphery reconstructed at
0.2 deg and charged for its 0.5 to 1.2 deg footprints, while leaving 78 to 87% of the sphere
uncovered. At K = 50 the two are level (0.140 on the covered 58% against 0.151 everywhere).

## The D9 curve, Classroom (10 gazes, targets = the 10 gaze centres)

| K | rays | F s | targets F | targets U | sphere F | uncov | sphere U | U W | U s |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.80 M | 0.031 | 0.282 | 0.904 | 0.564 | 0.868 | 0.764 | 158 | 0.73 |
| 2 | 1.60 M | 0.060 | 0.279 | 0.879 | 0.708 | 0.809 | 0.663 | 224 | 0.79 |
| 5 | 4.00 M | 0.143 | 0.149 | 0.816 | 0.577 | 0.639 | 0.579 | 354 | 0.79 |
| 10 | 7.99 M | 0.283 | 0.152 | 0.759 | 0.520 | 0.314 | 0.516 | 500 | 0.90 |

Resampling floor at s_eval: 0.368 at the targets, 0.222 over the sphere (the Classroom's
textures are finer than the calib room's cards at this scale). Targets: foveated wins by 3x
to 5x at every K. Sphere: level at K = 5 and K = 10 (0.577 vs 0.579, 0.520 vs 0.516), with
64% and 31% of the sphere uncovered; uniform wins at K = 2 and loses at K = 1.

## Checks, D9 pass

| | calib room | Classroom |
|---|---|---|
| (1) identity of the reconstruction path, within lat 60 deg | 2.2e-16, pass (0.13 beyond 70 deg, polar discs, reported) | 4.4e-16, pass |
| (2) 90 deg control at least 5x the K max target error | 0.592 vs 0.161, 3.7x: **fails** | 1.336 vs 0.152, 8.8x: pass |
| (3) calibration: uniform at s0 (3600 px, 64 spp) scores 0.073 +- 0.01 over the sphere | scores 0.033: **fails as specified** | not run |
| (3) the same render's own noise at s_eval, seed pair / sqrt 2 | 0.0323; score / noise = 1.03 | |
| (4) D8 validation, 0.5 deg-binned target error below the (b) bound | 0.067 vs 0.026: **fails** | 0.072 vs 0.061: **fails** |

On (3): the metric charges the calibration render 3% more than its measured noise, which is
the property the check is for. It fails the specified number because 0.073 is the per-pixel
noise at the 0.1 deg pixel; at s_eval = 0.2 deg the 2x2 box halves it (0.037 by 1/sqrt(4),
assumed; 0.032 measured from the seed pair). The specified number is left in the tool's
default and the failure recorded; the expected value at s_eval is the decision.

On (2): the calib room's wrong-content error (0.59) is bounded by how different a wall can be
from a star card, while the right-content residual (0.16) is registration on the cards plus
0.032 of noise, so the ratio is 3.7. The Classroom, with more varied content, passes at 8.8x.

On (4): unchanged from the first pass; registration-limited on the cards, see the A4 note.

## Assumed

- 1/sqrt(4) for the noise at s_eval from the per-pixel figure; the measured value is 0.032.
- The 91% lattice coverage of an area-equivalent disc; the 81%-of-cap measurement stands.
- Uniform render seconds include the EXR write (a few ms at these sizes).

## Untested

- **The full profile** (s_eval 0.1 deg, 7200x3600 grid): nothing in A4 or A5 has run there;
  about four times the cells, so roughly 4 min per integration run (assumed).
- The error on `distance`; only radiance is compared.
- Sequences other than target order.

## Validation: the first pass (D8 per-cell metric)

Kept as the record of why the metric moved. Everything below is the D8 per-cell comparison
with 1/footprint weighting, measured 2026-09-13 before the finest-owns change.

### Commands (first pass)

```bash
# equal-budget uniform baselines: W x W/2 x 64 spp = K x 12,492 x 64 rays, W rounded to even
for W in 158 224 354 500 706 1118; do
  blender -b scenes/calib_room/calib_room.blend -P tools/preview360.py -- --out previews/uniform/calib_room/w$W --width $W --spp 64 --filter BOX --no-backface
done
for W in 158 224 354 500; do
  blender -b scenes/classroom/classroom_eye.blend -P tools/preview360.py -- --out previews/uniform/classroom/w$W --width $W --spp 64 --filter BOX --no-backface
done
.venv/bin/python tools/integrate_sphere.py previews/sequence/calib_room --reference previews/reference_small/calib_room \
    --out previews/integrated/calib_room --k-list 1,2,5,10,20,50 --uniform previews/uniform/calib_room --bound 0.0263
.venv/bin/python tools/integrate_sphere.py previews/sequence/classroom --reference previews/reference_small/classroom \
    --out previews/integrated/classroom --k-list 1,2,5,10 --uniform previews/uniform/classroom --bound 0.0614
```
`--bound` is the median of `check_sequence.py`'s measured (b) bounds for that sequence. The
run takes about 40 s per scene; the uniform renders 0.3 to 0.9 s each. Outputs are
regenerable (`previews/integrated/<scene>/{integrated.npz,rgb.png,min_footprint.png,curve.json,curve.csv}`).

#### What the tool does

Each sample splats its value over the cells whose centres lie inside a disc of angular
radius sqrt(footprint/pi) around its direction, with weight 1/footprint. Per cell it keeps
the weighted RGB, the weight, the finest footprint, the number of fixations, and the weighted
centroid of the contributing sample directions. Two consequences, both measured:

- **Coverage has gaps.** An area-equivalent disc on a square sample lattice covers 91% of
  the lattice (assumed, geometry) and leaves the lattice corners uncovered; one fixation
  covers 0.118 of the sphere against 0.146 for a 45 deg cap, i.e. 81% of its cap. Gaps fill
  where fixations overlap: 50 fixations cover 0.578 of the sphere. They are visible as dotted
  rings at the rim in `rgb.png`.
- **The weighting leaks blur into the fovea.** A target cell receives its fine sample and
  also the coarse samples of neighbouring fixations 3 to 6 deg away, each at roughly a tenth
  of the weight. At K = 50 on the calib room, half the weight in target cells (median 0.50)
  comes from samples coarser than twice the cell's finest footprint; over the whole covered
  sphere the share is 0.15. The value therefore no longer has the resolution `min_footprint`
  claims where fixations crowd. Two diagnostic variants are in the tool (`--weight-power`,
  `--finest-only`) and their numbers are below; the 1/footprint rule stays the default.

#### The metric (D8)

Each covered cell is compared with the reference box-filtered over an angular square of
side sqrt(min_footprint) centred on the cell's sample centroid; a uniform render's pixel is
compared with the reference box over the pixel itself. Relative RMS over a set of cells is
RMS(value - box) / mean(box), solid-angle weighted, on the mean over RGB (the A2 convention).
Bands are by eccentricity from the nearest of the K fixation centres; "targets" are cells
within 1 deg of every gaze of the full sequence. The same box centred on the cell centre is
reported as `rel_rms_cell_centre`: it is worse by 0.02 to 0.03 because a cell's value comes
from a sample up to sqrt(footprint/pi) away (median centroid offset 0.10 deg, p99 0.62 deg).

#### Checks (first pass)

| | calib room | Classroom |
|---|---|---|
| (1) identity, reference pixels as samples, abs error within lat 60 deg | 2.2e-16, pass | 2.2e-16, pass |
| (1) beyond lat 70 deg | 0.11 to 0.14: a polar pixel's disc spans its longitude neighbours (cos lat < 0.318); cannot hold by construction, reported | same |
| (2) target error at K max below the (b) bound | 0.354 vs 0.0263: **fails** | 0.223 vs 0.0614: **fails** |
| (3) 90 deg control at least 5x the K max target error | 0.518 vs 0.354, 1.46x: **fails** | 1.191 vs 0.223, 5.3x: pass |
| (4) rasterised disc area equals footprints fed in, 1% | +0.02% to +0.09%, pass | +0.07% to +0.09%, pass |

(2) fails on both scenes and the reason is measured rather than assumed. The bound is a
0.5 deg-binned noise figure (the seed pair's disagreement averaged over about 20 samples
per cell), while the metric compares single-sample cells at 0.1 deg: the fixation's own
per-sample noise at 64 spp is already 0.073 relative on the calib room (A2's table, RMS over
pixels), and on top of it sits the per-cell resampling floor on the Siemens-star cards, which
`check_sequence.py` measures at a median of 0.098 per sample. Binning the covered target
cells to 0.5 deg before comparing gives 0.067 on the calib room and 0.073 on the Classroom,
2.5x and 1.2x their bounds, the same registration-limited regime as check (b) itself. The
tolerance is untouched; whether A5's target error should be judged per cell or per 0.5 deg
is a decision.

(3) fails on the calib room because the K = 50 target error is dominated by the two floors
above, so wrong content (0.52) is only 1.5x worse than right content (0.35). On the Classroom
the floors are lower relative to the content and the control is 5.3x.

#### The curve, calibration room (50 targets, small profile, 64 spp, 12,492 samples per fixation)

Foveated (F) against uniform (U) at the same ray budget. Seconds are render time from
`sequence.json` (seed-0 renders only, warm-up 0.309 s excluded) and from `meta.json` (which
includes the EXR write). Error is relative RMS.

| K | rays | F s | U W | U s | coverage | targets F | targets U | sphere F | sphere U |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.80 M | 0.016 | 158 | 0.35 | 0.118 | 0.159 | 0.108 | 0.206 | 0.078 |
| 2 | 1.60 M | 0.033 | 224 | 0.34 | 0.144 | 0.141 | 0.131 | 0.194 | 0.076 |
| 5 | 4.00 M | 0.082 | 354 | 0.36 | 0.159 | 0.147 | 0.133 | 0.184 | 0.075 |
| 10 | 7.99 M | 0.162 | 500 | 0.41 | 0.177 | 0.189 | 0.123 | 0.192 | 0.076 |
| 20 | 15.99 M | 0.319 | 706 | 0.49 | 0.219 | 0.280 | 0.120 | 0.220 | 0.076 |
| 50 | 39.97 M | 0.780 | 1118 | 0.71 | 0.578 | 0.354 | 0.125 | 0.186 | 0.077 |

By eccentricity band from the nearest fixation centre, foveated / uniform:

| K | 0 to 2 | 2 to 5 | 5 to 10 | 10 to 20 | 20 to 45 |
|---|---|---|---|---|---|
| 1 | 0.204 / 0.263 | 0.125 / 0.113 | 0.138 / 0.101 | 0.153 / 0.108 | 0.207 / 0.125 |
| 10 | 0.293 / 0.124 | 0.166 / 0.098 | 0.194 / 0.118 | 0.179 / 0.118 | 0.187 / 0.114 |
| 50 | 0.357 / 0.133 | 0.332 / 0.107 | 0.119 / 0.090 | 0.064 / 0.077 | 0.098 / 0.068 |

Under D8, uniform won everywhere on the calibration room, at every budget, at the targets
and over the sphere, and the foveated target error rose with K (0.16 at K = 1 to 0.35 at
K = 50). Three measured reasons. The uniform image sits on the same lon-lat grid as the
reference, so its box comparison is exactly registered and its error is its 64 spp noise
alone (0.075 to 0.078 over the sphere, against A2's 0.073 median-tile figure at 64 spp). The
foveated samples are off-grid, so at 0.1 deg on Siemens stars they pay the resampling floor.
And the 1/footprint rule adds blur at the targets as K grows (coarse share 0.50 at K = 50).
Removing the blur (finest-only, or 1/footprint^2) brings the K = 50 target error to 0.259
and 0.274 with medians 0.119 and 0.129, still above uniform's 0.125 RMS. The one band where
foveated beats uniform on this scene is 10 to 20 deg at K = 50 (0.064 vs 0.077), where the
sample footprint is coarse enough for registration not to matter.

#### The curve, Classroom (10 gazes, targets = the 10 gaze centres)

| K | rays | F s | U W | U s | coverage | targets F | targets U | sphere F | sphere U |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.80 M | 0.031 | 158 | 0.73 | 0.118 | 0.286 | 0.102 | 0.304 | 0.251 |
| 2 | 1.60 M | 0.060 | 224 | 0.79 | 0.178 | 0.289 | 0.190 | 0.341 | 0.251 |
| 5 | 4.00 M | 0.143 | 354 | 0.79 | 0.345 | 0.196 | 0.214 | 0.288 | 0.243 |
| 10 | 7.99 M | 0.283 | 500 | 0.90 | 0.648 | 0.223 | 0.297 | 0.276 | 0.240 |

On the Classroom foveation wins at the targets from K = 5 on (0.196 vs 0.214, then 0.223 vs
0.297) and loses over the sphere (0.276 vs 0.240 at K = 10). The scene is noisy at 64 spp
(A2: 0.19 median-tile relative noise), which lifts the uniform's floor above the registration
effects that dominate the calib room. The coarse share at the targets is 0.03: the 10 gazes
are 30 deg apart, so the blur leak is absent here.

#### Assumed

- The 91% lattice coverage of an area-equivalent disc (geometry, not measured directly; the
  0.118 of the sphere per fixation is measured).
- Uniform render seconds include the EXR write (preview360's timer); at these sizes the
  write is a few ms (assumed from the 0.1 s measured for the 128 MB small reference).
- The equal-budget widths are rounded to even: budgets match within 0.4% (measured).

#### Untested

- **The full profile.** Nothing in A4 or A5 has run at `--profile full`. Projected
  (assumed): 0.14 s per fixation, a 7200x3600 grid, four times the cells, so about 3 min
  per integration run; the 2 GB Classroom reference read.
- The error metric on the fixation record's `distance` (depth): only radiance is compared.
- Sequences other than target order; a gaze policy is Phase C.
