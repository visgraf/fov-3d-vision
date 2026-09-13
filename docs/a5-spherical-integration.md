# Step A5 — spherical integration and the error-versus-budget curve

State on 2026-09-13: `tools/integrate_sphere.py` accumulates a sequence's D1 samples into an
equirect sphere at the profile's reference resolution and measures the footprint-aware error
(D8) against the ray budget, with an equal-budget uniform baseline. Run on both mesh scenes
at `--profile small`. Everything here was measured on the workstation unless marked assumed.
The result on the calibration room is that uniform sampling wins under this metric at every
budget, and the two measured reasons are below; on the Classroom foveation wins at the
targets and loses slightly over the sphere.

## Commands

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

## What the tool does

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

## The metric (D8)

Each covered cell is compared with the reference box-filtered over an angular square of
side sqrt(min_footprint) centred on the cell's sample centroid; a uniform render's pixel is
compared with the reference box over the pixel itself. Relative RMS over a set of cells is
RMS(value - box) / mean(box), solid-angle weighted, on the mean over RGB (the A2 convention).
Bands are by eccentricity from the nearest of the K fixation centres; "targets" are cells
within 1 deg of every gaze of the full sequence. The same box centred on the cell centre is
reported as `rel_rms_cell_centre`: it is worse by 0.02 to 0.03 because a cell's value comes
from a sample up to sqrt(footprint/pi) away (median centroid offset 0.10 deg, p99 0.62 deg).

## Checks

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

## The curve, calibration room (50 targets, small profile, 64 spp, 12,492 samples per fixation)

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

**Where uniform wins: everywhere on the calibration room, at every budget, at the targets
and over the sphere**, and the foveated target error rises with K (0.16 at K = 1 to 0.35 at
K = 50). Three measured reasons. The uniform image sits on the same lon-lat grid as the
reference, so its box comparison is exactly registered and its error is its 64 spp noise
alone (0.075 to 0.078 over the sphere, against A2's 0.073 median-tile figure at 64 spp). The
foveated samples are off-grid, so at 0.1 deg on Siemens stars they pay the resampling floor.
And the 1/footprint rule adds blur at the targets as K grows (coarse share 0.50 at K = 50).
Removing the blur (finest-only, or 1/footprint^2) brings the K = 50 target error to 0.259
and 0.274 with medians 0.119 and 0.129, still above uniform's 0.125 RMS. The one band where
foveated beats uniform on this scene is 10 to 20 deg at K = 50 (0.064 vs 0.077), where the
sample footprint is coarse enough for registration not to matter.

## The curve, Classroom (10 gazes, targets = the 10 gaze centres)

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

## Assumed

- The 91% lattice coverage of an area-equivalent disc (geometry, not measured directly; the
  0.118 of the sphere per fixation is measured).
- Uniform render seconds include the EXR write (preview360's timer); at these sizes the
  write is a few ms (assumed from the 0.1 s measured for the 128 MB small reference).
- The equal-budget widths are rounded to even: budgets match within 0.4% (measured).

## Untested

- **The full profile.** Nothing in A4 or A5 has run at `--profile full`. Projected
  (assumed): 0.14 s per fixation, a 7200x3600 grid, four times the cells, so about 3 min
  per integration run; the 2 GB Classroom reference read.
- The error metric on the fixation record's `distance` (depth): only radiance is compared.
- Sequences other than target order; a gaze policy is Phase C.
