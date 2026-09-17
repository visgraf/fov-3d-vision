# Step C1 — the stereo field: a matcher that works over the whole disc, with an uncertainty per cell

Written 2026-09-16 before the workstation run. Numbers are **predicted**, **assumed**, or from
the stub (plumbing and geometry, not content) until the log records a measurement.

## What C1 is

Phase C closes the loop (D17): observe a pair, infer depth with an uncertainty everywhere the
pair looked, choose the next fixation from what is known, observe again. The first thing the
loop needs is the inference over the whole field, not the fovea: B3's instrument matched a
±2° map about the gaze at s_eval and "never saw the non-uniform lattice" (D15). C1 extends
that instrument to every eccentricity a pair covers, at the scale the samples support there,
and returns per cell an inverse-depth measurement with a variance. It is numpy-only so the C2
loop can import it inside the Blender session; its `main()` is the host-side check against
`truth.npz`. No rendering: it runs on Phase B's existing runs.

## Levels

The warp's spacing is s(e) = s₀ (1 + e/E₂), so a grid at one cell size is right for one band of
eccentricity. Level l has cell c_l = eval_factor × s₀ × 2^l (D9's s_eval at l = 0) and owns the
cells whose eccentricity from the L gaze lies in (e_{l−1}, e_l], with
e_l = E₂ (eval_factor 2^l − 1): the band in which one cell holds at least one sample spacing.
At the standard warp that is 2, 6, 14, 30 and 62° for l = 0…4 — five grids of roughly 400,
900, 1200, 1400 and 800 cells at small, because a log-polar warp has about the same number of
cells per octave. Level 0 within 2° is the instrument's map exactly; check (p) holds it to that.
Cells within `--axis-deg` of the baseline axis are not owned (φ is ill-conditioned there, as in
B2). A pair's field is ~3000 cells, 0.17 s on the stub.

## The matcher, per level

Both eyes' samples are integrated finest-owns onto a local epipolar grid about each eye's own
gaze (rows φ, columns θ; B3's `FoveaGrid` and `accumulate`), the R map wider by the search
range, `--search-deg` (3°) converted to cells per level. From level 2 up (`--smooth-from`)
both maps are smoothed along θ by [1, 2, 1]/4 — measured on a synthetic wall (see the
self-test): at the coarse levels a cell holds one or two samples, the map has power up to the
grid's Nyquist, and the Lucas–Kanade step, which models the map as piecewise linear between
cells, recovers only half of a fractional shift (bias +0.09 cells at level 4 for true shifts
of −0.16; none on a wall at 20 m where the shift is ~0); one pass of smoothing halves that
bias. Not at levels 0–1: the first workstation run measured that on the rendered room the
smoothing costs level 0 (0.29 → 0.39 s₀, gross 8.9 → 14.6%: the cards' texture is at the cell
scale and smoothing removes what the instrument matches on) while the coarse levels gain
(levels 3–4: 0.45/0.27 → 0.40/0.23 cells). The synthetic wall had said the opposite for level
0 because its texture was oversampled there — the instrument's lesson about instruments,
again. Then B3's matcher unchanged: NCC over a 5×5 window along the row,
winner-take-all, two LK steps. Parallax = (θ_gaze,R − θ_gaze,L) + shift × cell.

**Left–right consistency.** The R map is matched back against the L map; a cell is
*consistent* when the two shifts agree within `--lr-tol` (1 cell). This is bioeye's validity
test and the quantity bio-3d-vision found worth 65:1 over the variance: where measurement is
possible. On the stub it rejects 5–12% of matchable cells per level and lowers the gross
fraction from 14% to 6% at level 0. Check (r) requires it to reject something and to reject
wrong peaks.

**The variance.** σ_p² = (κ × bound)² + (β × cell)². The bound is B3's, 1/√I with I the Fisher
information over the window (computed on the smoothed map, since that is what the estimator
sees); κ is the instrument's measured RMS/bound ratio (`--kappa`, 2.5 small, 3.8 full from B3).
The floor β × cell is new and needed: at the coarse levels the error is set by the model —
the window straddles surfaces whose parallax varies across it — not by noise. On the stub the
inlier RMS is 0.32–0.39 cells at every level from 1 to 4 while the bound is 0.02–0.03 cells, so
without the floor the belief would trust the periphery a hundred times too much.
`--floor-cells` defaults to 0.3 (assumed from the stub); the check reports the measured value
per level, which is the number C2 should take.

**Inverse depth.** ρ = 1/|P − C_L| = sin p / (ipd sin(θ_L + p)) by the sine rule, and
σ_ρ = |∂ρ/∂p| σ_p with the exact Jacobian ∂ρ/∂p = sin θ_L / (ipd sin²(θ_L + p)) (self-tested
against a numerical derivative). Inverse depth, not depth, because parallax is nearly linear in
it, and because the periphery's measurements are of "roughly how far", which is a ρ with a large
σ, not a depth with an infinite one.

## Output

Per pair, `<run>/field/p<NNN>.npz`, one row per owned matchable cell: `dir` (head-frame unit,
from L), `theta_L`, `phi`, `level`, `cell_deg`, `parallax_deg`, `sigma_p_deg`, `bound_deg`,
`rho`, `sigma_rho`, `consistent`, `ecc_deg`, `row`, `col`; with truth present also
`truth_parallax_deg`, `truth_rho`, `truth_visible`. About 200 KB per pair. `<run>/field.json`:
per pair and per level, the checks. `--sheet`: a composite per pair at level-0 resolution
about the L gaze, every level drawn as blocks — L radiance | parallax estimate | truth | error
in cells | σ in cells.

## Checks (`stereo_field.py`)

- **self-test** (`--self-test`): the Jacobian against a numerical derivative and ρ against the
  sine rule; the level edges (level 0 = the instrument's 2°, five levels reach 45°);
  `direction_of` inverts `rig.epipolar`; and a synthetic pair (`synthetic_pair`: two eyes
  verged on a textured fronto-parallel wall at 2 m with a 30 cm card at 1 m, sampled on the
  warp, non-periodic texture — a periodic one lies to a matcher) on which, per level, the
  LR-consistent cells must be unbiased to 0.15 cells, at most 20% of the wall cells may be off
  by more than half a cell, the σ model must be right within 3× (z RMS in [0.3, 3] at the
  wall's measured floor of 0.1 cells), and the card's edge must be rejected by the LR test more
  often than the rest. Found this way while building: the periodic texture (75% gross), the
  LK shrinkage at coarse levels, and the missing floor.
- **(o) ownership** — the levels' owned solid angle covers ≥ 90% of the disc's 2π(1 − cos e_max)
  (the rest: band quantisation and the axis exclusion). Stub: 0.986.
- **(p) regression** — level 0's inlier RMS, pooled over the LR-consistent inlier cells within
  2° of the L gaze on the instrument's judged pairs, is not worse than `stereo.json`'s pooled
  instrument RMS by more than 25%: the field *is* the instrument where they overlap. Better
  passes and is reported (at `full` it is 27% better: the LR test removes what the instrument
  keeps). The first run's (p) was the RMS of per-pair RMS against a pooled number, which alone
  cost 15%, and it pooled the wire pairs the instrument never judges (Code's fix). Stub: −11%
  (0.0452 vs 0.0510°). Negative: `--eval-factor 4` fails it at +61%.
- **(q) bound** — per level with ≥ 200 judged cells, bound RMS ≤ inlier RMS. The measured
  RMS/bound and the floor at the assumed κ are reported per level.
- **(r) consistency** — per level, the LR-consistent subset's gross fraction is below the
  matchable set's, and the test rejects something. Negative: `--no-lr` fails it on every level.

Reported per level: inlier RMS in deg, cells and s₀; gross before and after LR; bias; bound;
RMS/bound; floor; ρ RMS (1/m); depth RMS to first order (m); z RMS and median |z| of the
calibration. On the stub the depth RMS is 0.3 m at level 0 and 8 m at level 4: the periphery at
3° cells does not measure depth, it measures that something is at roughly the fixated distance.
That is the number the policy will have to improve by looking.

## Commands (host side, seconds each; no rendering)

```bash
.venv/bin/python tools/stereo_field.py --self-test
.venv/bin/python tools/stereo_field.py previews/pairs/calib_room_sp --sheet
.venv/bin/python tools/stereo_field.py previews/pairs/calib_room_control_sp --search-deg 4 --sheet
.venv/bin/python tools/stereo_field.py previews/pairs/calib_room_full_sp --kappa 3.8 --sheet
for s in e2_1 e2_2 e2_4 emax_30 emax_60; do .venv/bin/python tools/stereo_field.py previews/sweep_b3/$s; done
# negatives
.venv/bin/python tools/stereo_field.py previews/pairs/calib_room_sp --no-lr ; echo "exit $?"
.venv/bin/python tools/stereo_field.py previews/pairs/calib_room_sp --eval-factor 4 ; echo "exit $?"
```

## After the first run (2026-09-17)

Three of the four checks passed on all eight runs and both negatives failed as designed; (p)
failed on seven. Two causes, both measured by Code: the check pooled pairs the instrument never
judges (fixed), and the θ-smoothing, which the synthetic wall had recommended for every level,
costs level 0 on the rendered room. Decision: smooth from level 2 up, keep levels 0–1 as the
instrument; make (p) pooled like for like and one-sided. Predicted for the second run, from
Code's diagnostics: (p) at `small` within 10% (0.0250 vs 0.0269 pooled, unsmoothed), `full`
27% better and passing, level-0 κ and floor to be read fresh for C2 — the first run's level-0
values are the smoothed matcher's and do not apply. The first run's record follows as Code
wrote it.

## Results

Run 2026-09-17 on the workstation, host side in the venv, on Phase B's existing runs (nothing
rendered). All numbers below are measured, from each run's `field.json` (per level) and
`stereo.json` (the instrument's reference for (p)), unless marked assumed. Wall times are
`time` on the command. Sheet: `docs/reference/c1_field_calib_room_small.png` (first four
pairs of `calib_room_sp`).

**Summary.** Self-test ok. (o), (q) and (r) pass on all eight runs at every level; both
negatives fail as designed with the named lines and exit 1. **(p) fails on 7 of 8 runs**, in
the direction the prediction did not anticipate on `small` (the field's level 0 is *worse*
than the instrument, 38–74% apart) and in the anticipated direction on `full` (the field 27%
*better*). Only the control passes, at 22%. Diagnosis below; no threshold, κ, floor or the
smoothing was changed. One plumbing fix in the check's pair selection (item 1 below): the per-pair `judged` flag is no
longer overwritten, the judged-cell count is now `judged_cells` in `field.json`.

**Diagnosis of (p), measured on `calib_room_sp` unless noted.**

1. *Pair selection (fixed).* `main()` overwrote the per-pair `judged` flag (kind in
   ring/ladder/point, the instrument's set) with the judged-cell count before (p) read it, so
   the 8 `wire` pairs, which the instrument reports but never judges (level-0 per-pair RMS
   0.026–0.104°), were pooled into the field's number. As shipped (p) read 0.0505 vs 0.0269
   (87%); over the instrument's pairs it reads 0.0460 (71%). Same on every run: control 27% → 22%,
   full 15% → 27%, e2_1 89% → 46%, e2_4 98% → 74%, emax_30 66% → 38%, emax_60 80% → 49%.
2. *Aggregation (not changed).* (p) is the RMS of per-pair RMS; `stereo.json`'s
   `inlier_rms_deg` is pooled over cells. The instrument's own per-pair RMS over its judged
   pairs is 0.0308, 15% above its pooled 0.0269, so the two aggregations alone use most of the
   tolerance. Pooled like for like (level-0 LR-consistent inliers within 2° of the L gaze, the
   instrument's pairs): field **0.0362 vs 0.0269 (35%)** on `calib_room_sp`; control 0.0580 vs
   0.0535 (8%); full 0.0152 vs 0.0208 (27%).
3. *The θ-smoothing costs level 0 at `small` (not changed: a reading for Chat).* With
   `smooth=False` (field_of_pair's keyword, patched from a harness; the tool has no flag) and
   nothing else changed, `calib_room_sp` level 0 goes from 0.0394 to 0.0291° over all cells
   (0.39 → 0.29 s₀ against the instrument's 0.269), gross before LR 14.6% → 8.9%, pooled
   like-for-like **0.0250 vs 0.0269 (7%)**, and (p) as coded 0.0278 vs 0.0269 (3%, pass).
   Control: (p) 0.0574 vs 0.0535 (7%, pass; pooled 0.0523 vs 0.0535). Full: level 0 unchanged
   (0.0160 vs 0.0156°), (p) 0.0150 vs 0.0208 (28%, still the field better). The coarse levels
   go the other way without smoothing, as the synthetic wall predicted, but modestly: levels
   3–4 inlier RMS 0.40/0.23 → 0.45/0.27 cells, bias +0.42/+0.48 → +0.51/+0.61°. The wider
   level-0 grid (σ measured over ±4.6° rather than the instrument's ±2°) is not the cause:
   `margin_deg=0` moves level 0 by 0.0000°.

So at `small` the field is the instrument at level 0 only without the smoothing; at `full`
the field is 27% better than the instrument with or without it (LR consistency removes 5% of
its cells; the instrument has no LR test). Whether to smooth only the coarse levels, or
change (p) to the pooled comparison, or both, is Chat's call; C2 should not read κ or floor
from level 0 until it is made.

**Per level, all runs.** κ and floor are the measured values at the assumed κ (2.5 small,
3.8 full) and floor 0.3 cells. The predicted floor of 0.2–0.4 cells at levels 1–4 holds at
levels 2–3 (0.29–0.40 cells on every run) and is lower at levels 1 and 4 (0.10–0.22); at
level 0 it is 0.12–0.27. RMS/bound is 3.2–3.7 at level 0 on `small` (predicted near 2.5) and
7.2 at level 0 on `full` (predicted near 3.8); 4–9 at the coarse levels. z RMS is 0.5–0.6 at
level 0 (σ too large by ~2×) and 1.0–1.2 at levels 2–3 on `small`; the model is right within
3× everywhere. The coarse levels carry a positive bias (+0.15° at level 2, +0.4–0.5° at
levels 3–4, i.e. 0.15–0.3 cells) visible on the sheet as red over the cards: the estimate
overshoots toward the nearer surface where the window straddles a depth edge. Depth RMS (1st
order): 0.35 m at level 0 and 5.6 m at level 4 on `small`; 0.08 m and 3.8 m on `full`.
Level edges scale with E₂ as designed (E₂ 1: six levels, cells 0.20–6.36°; e_max 30: four).
`owned/covered` is 1.029 on e2_1 (>1: the level bands overrun the disc's solid angle at the
band quantisation with E₂ 1; harmless for (o), noted).

**`calib_room_sp`** — verged, seed pair; κ 2.5; 50 pairs, 5 levels, cells/pair median 2100 (consistent 2002), owned/covered 0.986; wall 5.0 s. (p): field 0.0460 vs instrument 0.0269 deg (71%, tol 25%) — **FAIL**. Other fails: none.

| level | cell (deg) | judged | LR rej. % | gross → after LR | inlier RMS deg / cells / s₀ | bias (deg) | bound (deg) | RMS/bound | floor (cells) | ρ RMS (1/m) | depth RMS (m) | z RMS / med |z| |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.20 | 9997 | 10.6 | 14.6% → 10.0% | 0.0394 / 0.20 / 0.39 | +0.0116 | 0.0121 | 3.25 | 0.13 | 0.0440 | 0.351 | 0.57 / 0.29 |
| 1 | 0.40 | 19110 | 7.9 | 25.3% → 22.1% | 0.1062 / 0.26 / 1.06 | +0.0302 | 0.0284 | 3.75 | 0.20 | 0.0922 | 0.890 | 0.73 / 0.29 |
| 2 | 0.80 | 24617 | 3.2 | 17.0% → 16.7% | 0.3109 / 0.39 / 3.10 | +0.1516 | 0.0582 | 5.34 | 0.34 | 0.1342 | 2.086 | 1.12 / 0.38 |
| 3 | 1.60 | 29386 | 2.1 | 0.5% → 0.2% | 0.6458 / 0.40 / 6.44 | +0.4229 | 0.1028 | 6.28 | 0.37 | 0.2401 | 4.879 | 1.20 / 0.68 |
| 4 | 3.21 | 13334 | 2.3 | 0.3% → 0.2% | 0.7433 / 0.23 / 7.42 | +0.4832 | 0.1389 | 5.35 | 0.20 | 0.3666 | 5.569 | 0.71 / 0.49 |

**`calib_room_control_sp`** — vergence off, `--search-deg 4`; κ 2.5; 50 pairs, 5 levels, cells/pair median 2090 (consistent 1898), owned/covered 0.985; wall 5.4 s. (p): field 0.0652 vs instrument 0.0535 deg (22%, tol 25%) — pass. Other fails: none.

| level | cell (deg) | judged | LR rej. % | gross → after LR | inlier RMS deg / cells / s₀ | bias (deg) | bound (deg) | RMS/bound | floor (cells) | ρ RMS (1/m) | depth RMS (m) | z RMS / med |z| |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.20 | 9133 | 32.1 | 32.2% → 13.9% | 0.0599 / 0.30 / 0.60 | +0.0313 | 0.0104 | 5.77 | 0.27 | 0.0470 | 0.377 | 0.91 / 0.63 |
| 1 | 0.40 | 18725 | 13.9 | 27.6% → 21.6% | 0.1117 / 0.28 / 1.11 | +0.0299 | 0.0293 | 3.81 | 0.21 | 0.0854 | 0.833 | 0.77 / 0.35 |
| 2 | 0.80 | 24444 | 3.4 | 17.3% → 16.6% | 0.2992 / 0.37 / 2.99 | +0.1343 | 0.0570 | 5.25 | 0.33 | 0.1175 | 1.923 | 1.08 / 0.34 |
| 3 | 1.60 | 28742 | 1.6 | 0.3% → 0.2% | 0.6232 / 0.39 / 6.22 | +0.3833 | 0.1033 | 6.03 | 0.35 | 0.2046 | 4.704 | 1.16 / 0.57 |
| 4 | 3.21 | 12608 | 2.0 | 0.1% → 0.1% | 0.6453 / 0.20 / 6.44 | +0.2628 | 0.1633 | 3.95 | 0.16 | 0.2332 | 4.665 | 0.63 / 0.35 |

**`calib_room_full_sp`** — full profile, `--kappa 3.8`; 50 pairs, 5 levels, cells/pair median 9848 (consistent 8536), owned/covered 0.988; wall 16.5 s. (p): field 0.0152 vs instrument 0.0208 deg (27%, tol 25%) — **FAIL**. Other fails: none.

| level | cell (deg) | judged | LR rej. % | gross → after LR | inlier RMS deg / cells / s₀ | bias (deg) | bound (deg) | RMS/bound | floor (cells) | ρ RMS (1/m) | depth RMS (m) | z RMS / med |z| |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.10 | 47904 | 5.2 | 11.7% → 8.1% | 0.0156 / 0.16 / 0.31 | +0.0008 | 0.0022 | 7.21 | 0.13 | 0.0113 | 0.079 | 0.49 / 0.19 |
| 1 | 0.20 | 80689 | 13.8 | 26.1% → 19.9% | 0.0451 / 0.23 / 0.90 | +0.0065 | 0.0107 | 4.22 | 0.10 | 0.0393 | 0.384 | 0.63 / 0.27 |
| 2 | 0.40 | 120535 | 13.3 | 23.2% → 18.0% | 0.1048 / 0.26 / 2.10 | +0.0296 | 0.0241 | 4.35 | 0.13 | 0.0773 | 0.807 | 0.78 / 0.28 |
| 3 | 0.80 | 135732 | 8.7 | 18.9% → 16.4% | 0.2670 / 0.33 / 5.35 | +0.1159 | 0.0352 | 7.58 | 0.29 | 0.1086 | 1.750 | 1.04 / 0.29 |
| 4 | 1.60 | 56946 | 2.5 | 2.3% → 1.3% | 0.5408 / 0.34 / 10.83 | +0.2722 | 0.0582 | 9.29 | 0.31 | 0.1955 | 3.844 | 1.06 / 0.48 |

**`sweep_b3/e2_1`** — E₂ 1; 50 pairs, 6 levels, cells/pair median 740 (consistent 714), owned/covered 1.029; wall 3.6 s. (p): field 0.0396 vs instrument 0.0270 deg (46%, tol 25%) — **FAIL**. Other fails: none.

| level | cell (deg) | judged | LR rej. % | gross → after LR | inlier RMS deg / cells / s₀ | bias (deg) | bound (deg) | RMS/bound | floor (cells) | ρ RMS (1/m) | depth RMS (m) | z RMS / med |z| |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.20 | 2027 | 15.4 | 19.0% → 13.9% | 0.0482 / 0.24 / 0.48 | +0.0159 | 0.0136 | 3.56 | 0.17 | 0.0687 | 0.543 | 0.72 / 0.41 |
| 1 | 0.40 | 5282 | 10.7 | 24.6% → 20.1% | 0.1058 / 0.27 / 1.06 | +0.0317 | 0.0289 | 3.67 | 0.19 | 0.0856 | 0.783 | 0.73 / 0.37 |
| 2 | 0.80 | 7161 | 3.8 | 20.7% → 20.3% | 0.3130 / 0.39 / 3.15 | +0.1584 | 0.0580 | 5.40 | 0.35 | 0.1263 | 1.996 | 1.10 / 0.40 |
| 3 | 1.59 | 7360 | 2.8 | 0.1% → 0.1% | 0.7014 / 0.44 / 7.05 | +0.4956 | 0.1147 | 6.11 | 0.40 | 0.2490 | 5.222 | 1.26 / 0.85 |
| 4 | 3.18 | 8055 | 2.1 | 0.2% → 0.1% | 0.7875 / 0.25 / 7.92 | +0.5542 | 0.1908 | 4.13 | 0.20 | 0.4593 | 6.645 | 0.73 / 0.59 |
| 5 | 6.36 | 3371 | 1.4 | 0.8% → 0.5% | 0.9371 / 0.15 / 9.42 | +0.3612 | 0.3394 | 2.76 | 0.06 | 1.2779 | 12.152 | 0.44 / 0.26 |

**`sweep_b3/e2_2`** — E₂ 2 (= calib_room_sp); 50 pairs, 5 levels, cells/pair median 2100 (consistent 2002), owned/covered 0.986; wall 4.7 s. (p): field 0.0460 vs instrument 0.0269 deg (71%, tol 25%) — **FAIL**. Other fails: none.

| level | cell (deg) | judged | LR rej. % | gross → after LR | inlier RMS deg / cells / s₀ | bias (deg) | bound (deg) | RMS/bound | floor (cells) | ρ RMS (1/m) | depth RMS (m) | z RMS / med |z| |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.20 | 9997 | 10.6 | 14.6% → 10.0% | 0.0394 / 0.20 / 0.39 | +0.0116 | 0.0121 | 3.25 | 0.13 | 0.0440 | 0.351 | 0.57 / 0.29 |
| 1 | 0.40 | 19110 | 7.9 | 25.3% → 22.1% | 0.1062 / 0.26 / 1.06 | +0.0302 | 0.0284 | 3.75 | 0.20 | 0.0922 | 0.890 | 0.73 / 0.29 |
| 2 | 0.80 | 24617 | 3.2 | 17.0% → 16.7% | 0.3109 / 0.39 / 3.10 | +0.1516 | 0.0582 | 5.34 | 0.34 | 0.1342 | 2.086 | 1.12 / 0.38 |
| 3 | 1.60 | 29386 | 2.1 | 0.5% → 0.2% | 0.6458 / 0.40 / 6.44 | +0.4229 | 0.1028 | 6.28 | 0.37 | 0.2401 | 4.879 | 1.20 / 0.68 |
| 4 | 3.21 | 13334 | 2.3 | 0.3% → 0.2% | 0.7433 / 0.23 / 7.42 | +0.4832 | 0.1389 | 5.35 | 0.20 | 0.3666 | 5.569 | 0.71 / 0.49 |

**`sweep_b3/e2_4`** — E₂ 4; 50 pairs, 4 levels, cells/pair median 4872 (consistent 4429), owned/covered 0.984; wall 8.4 s. (p): field 0.0456 vs instrument 0.0262 deg (74%, tol 25%) — **FAIL**. Other fails: none.

| level | cell (deg) | judged | LR rej. % | gross → after LR | inlier RMS deg / cells / s₀ | bias (deg) | bound (deg) | RMS/bound | floor (cells) | ρ RMS (1/m) | depth RMS (m) | z RMS / med |z| |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.20 | 33897 | 8.5 | 18.8% → 14.3% | 0.0416 / 0.21 / 0.41 | +0.0066 | 0.0114 | 3.65 | 0.15 | 0.0387 | 0.331 | 0.60 / 0.28 |
| 1 | 0.40 | 59138 | 10.8 | 26.6% → 23.2% | 0.1215 / 0.30 / 1.21 | +0.0385 | 0.0327 | 3.72 | 0.22 | 0.0966 | 0.951 | 0.86 / 0.38 |
| 2 | 0.80 | 85376 | 6.3 | 17.5% → 15.9% | 0.2868 / 0.36 / 2.86 | +0.1227 | 0.0628 | 4.57 | 0.30 | 0.1225 | 1.844 | 1.05 / 0.36 |
| 3 | 1.60 | 50934 | 3.4 | 1.5% → 0.7% | 0.5571 / 0.35 / 5.56 | +0.3094 | 0.0787 | 7.08 | 0.33 | 0.2084 | 3.985 | 1.09 / 0.53 |

**`sweep_b3/emax_30`** — e_max 30; 50 pairs, 4 levels, cells/pair median 1813 (consistent 1736), owned/covered 0.989; wall 4.4 s. (p): field 0.0406 vs instrument 0.0293 deg (38%, tol 25%) — **FAIL**. Other fails: none.

| level | cell (deg) | judged | LR rej. % | gross → after LR | inlier RMS deg / cells / s₀ | bias (deg) | bound (deg) | RMS/bound | floor (cells) | ρ RMS (1/m) | depth RMS (m) | z RMS / med |z| |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.20 | 9471 | 11.1 | 17.3% → 11.5% | 0.0360 / 0.18 / 0.36 | +0.0072 | 0.0110 | 3.28 | 0.12 | 0.0427 | 0.344 | 0.54 / 0.25 |
| 1 | 0.40 | 18911 | 8.1 | 24.9% → 21.7% | 0.1077 / 0.27 / 1.08 | +0.0312 | 0.0285 | 3.78 | 0.20 | 0.0862 | 0.837 | 0.74 / 0.32 |
| 2 | 0.80 | 24689 | 3.1 | 17.2% → 16.8% | 0.3093 / 0.39 / 3.10 | +0.1457 | 0.0578 | 5.35 | 0.34 | 0.1266 | 2.043 | 1.11 / 0.39 |
| 3 | 1.60 | 30638 | 2.5 | 1.0% → 0.6% | 0.6517 / 0.41 / 6.52 | +0.4100 | 0.0922 | 7.07 | 0.38 | 0.2482 | 4.913 | 1.24 / 0.72 |

**`sweep_b3/emax_60`** — e_max 60; 50 pairs, 5 levels, cells/pair median 2471 (consistent 2311), owned/covered 0.990; wall 4.9 s. (p): field 0.0425 vs instrument 0.0285 deg (49%, tol 25%) — **FAIL**. Other fails: none.

| level | cell (deg) | judged | LR rej. % | gross → after LR | inlier RMS deg / cells / s₀ | bias (deg) | bound (deg) | RMS/bound | floor (cells) | ρ RMS (1/m) | depth RMS (m) | z RMS / med |z| |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.20 | 9237 | 11.1 | 16.6% → 11.1% | 0.0379 / 0.19 / 0.38 | +0.0090 | 0.0117 | 3.25 | 0.12 | 0.0451 | 0.368 | 0.55 / 0.27 |
| 1 | 0.40 | 19080 | 8.0 | 24.4% → 21.2% | 0.1089 / 0.27 / 1.09 | +0.0289 | 0.0282 | 3.86 | 0.21 | 0.0863 | 0.846 | 0.75 / 0.31 |
| 2 | 0.80 | 24590 | 3.0 | 16.9% → 16.6% | 0.3098 / 0.39 / 3.09 | +0.1430 | 0.0574 | 5.40 | 0.34 | 0.1277 | 2.044 | 1.11 / 0.38 |
| 3 | 1.60 | 28865 | 2.3 | 0.6% → 0.3% | 0.6458 / 0.40 / 6.44 | +0.4273 | 0.1043 | 6.19 | 0.37 | 0.2500 | 4.941 | 1.19 / 0.69 |
| 4 | 3.21 | 28434 | 4.6 | 0.9% → 0.3% | 0.7085 / 0.22 / 7.07 | +0.3445 | 0.1614 | 4.39 | 0.18 | 0.3556 | 4.852 | 0.66 / 0.39 |


### Second run (2026-09-17, after `64b1dc7`: smoothing from level 2, (p) pooled and one-sided)

Same eight runs, same commands, host side, nothing rendered; all numbers measured, from each
run's `field.json` and `stereo.json`. **Every check passes on every run**: (o), (q), (r) at
every level and (p) on all eight, the field's level 0 *better* than the instrument on each
(−2% to −31%), none between +10% and +25%. Negatives: `--no-lr` fails (r) on all five levels
(10 lines, exit 1) and now passes (p) at −2%, as allowed; `--eval-factor 4` fails (p) at
+206% (exit 1). Self-test ok. No code changed. Sheet replaced
(`docs/reference/c1_field_calib_room_small.png`).

Levels 0–1 are the unsmoothed matcher's, as predicted from the first run's diagnostic
(`calib_room_sp` level 0: inlier RMS 0.29 s₀, gross before LR 8.9%, RMS/bound 4.58, floor
0.12 cells; the prediction of RMS/bound "near 3" was off: the bound halves without the
smoothing, 0.0121 → 0.0063°, while the error drops less). Levels 2–4 are identical to the first
run. The `full` run's level 0 is unchanged to 3% (0.0156 → 0.0160°) and (p) there reads −24%
(the first run's −27% was per-pair, this is pooled). The measured κ and floor per level are the
numbers C2 reads: on `small` κ 4.6 / 4.3 / 5.3 / 6.3 / 5.4 and floor 0.12 / 0.20 / 0.34 /
0.37 / 0.20 cells; on `full` κ 7.7 / 4.3 / 4.4 / 7.6 / 9.3 and floor 0.14 / 0.11 / 0.13 /
0.29 / 0.31 cells. The floor over all runs and levels spans 0.06–0.40 cells (0.29–0.40 at
levels 2–3 everywhere). `e2_1`'s owned/covered is still 1.029 (band quantisation at E₂ 1).

| run | (p) field vs instrument (deg) | rel. | cells pooled | cells/pair (consistent) | owned/covered | fails | wall |
|---|---|---|---|---|---|---|---|
| `calib_room_sp` | 0.0250 vs 0.0269 | -7% | 9148 | 1984 (1880) | 0.986 | 0 | 5.0 s |
| `calib_room_control_sp` | 0.0523 vs 0.0535 | -2% | 6554 | 1959 (1780) | 0.985 | 0 | 5.4 s |
| `calib_room_full_sp` | 0.0158 vs 0.0208 | -24% | 40194 | 9655 (8430) | 0.988 | 0 | 16.7 s |
| `sweep_b3/e2_1` | 0.0187 vs 0.0270 | -31% | 2426 | 746 (716) | 1.029 | 0 | 3.6 s |
| `sweep_b3/e2_2` | 0.0250 vs 0.0269 | -7% | 9148 | 1984 (1880) | 0.986 | 0 | 4.7 s |
| `sweep_b3/e2_4` | 0.0234 vs 0.0262 | -10% | 9027 | 4594 (4208) | 0.984 | 0 | 8.3 s |
| `sweep_b3/emax_30` | 0.0262 vs 0.0293 | -11% | 8623 | 1686 (1564) | 0.989 | 0 | 4.4 s |
| `sweep_b3/emax_60` | 0.0261 vs 0.0285 | -8% | 8529 | 2320 (2190) | 0.990 | 0 | 4.9 s |

**`calib_room_sp`, per level** (κ assumed 2.5, floor assumed 0.3 cells):

| level | cell (deg) | judged | LR rej. % | gross → after LR | inlier RMS deg / cells / s₀ | bias (deg) | bound (deg) | RMS/bound (κ measured) | floor (cells) | ρ RMS (1/m) | depth RMS (m) | z RMS / med |z| |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.20 | 10752 | 5.9 | 8.9% → 5.7% | 0.0291 / 0.14 / 0.29 | +0.0125 | 0.0063 | 4.58 | 0.12 | 0.0348 | 0.279 | 0.45 / 0.20 |
| 1 | 0.40 | 15677 | 10.1 | 23.3% → 20.0% | 0.1001 / 0.25 / 1.00 | +0.0420 | 0.0235 | 4.26 | 0.20 | 0.1050 | 0.948 | 0.73 / 0.25 |
| 2 | 0.80 | 24617 | 3.2 | 17.0% → 16.7% | 0.3109 / 0.39 / 3.10 | +0.1516 | 0.0582 | 5.34 | 0.34 | 0.1342 | 2.086 | 1.12 / 0.38 |
| 3 | 1.60 | 29386 | 2.1 | 0.5% → 0.2% | 0.6458 / 0.40 / 6.44 | +0.4229 | 0.1028 | 6.28 | 0.37 | 0.2401 | 4.879 | 1.20 / 0.68 |
| 4 | 3.21 | 13334 | 2.3 | 0.3% → 0.2% | 0.7433 / 0.23 / 7.42 | +0.4832 | 0.1389 | 5.35 | 0.20 | 0.3666 | 5.569 | 0.71 / 0.49 |

**`calib_room_full_sp`, per level** (κ assumed 3.8, floor assumed 0.3 cells):

| level | cell (deg) | judged | LR rej. % | gross → after LR | inlier RMS deg / cells / s₀ | bias (deg) | bound (deg) | RMS/bound (κ measured) | floor (cells) | ρ RMS (1/m) | depth RMS (m) | z RMS / med |z| |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.10 | 47371 | 5.0 | 11.4% → 8.0% | 0.0160 / 0.16 / 0.32 | +0.0023 | 0.0021 | 7.70 | 0.14 | 0.0108 | 0.068 | 0.50 / 0.17 |
| 1 | 0.20 | 73949 | 14.2 | 27.9% → 21.8% | 0.0442 / 0.22 / 0.89 | +0.0106 | 0.0102 | 4.34 | 0.11 | 0.0399 | 0.378 | 0.62 / 0.26 |
| 2 | 0.40 | 120535 | 13.3 | 23.2% → 18.0% | 0.1048 / 0.26 / 2.10 | +0.0296 | 0.0241 | 4.35 | 0.13 | 0.0773 | 0.807 | 0.78 / 0.28 |
| 3 | 0.80 | 135732 | 8.7 | 18.9% → 16.4% | 0.2670 / 0.33 / 5.35 | +0.1159 | 0.0352 | 7.58 | 0.29 | 0.1086 | 1.750 | 1.04 / 0.29 |
| 4 | 1.60 | 56946 | 2.5 | 2.3% → 1.3% | 0.5408 / 0.34 / 10.83 | +0.2722 | 0.0582 | 9.29 | 0.31 | 0.1955 | 3.844 | 1.06 / 0.48 |

## What C1 leaves open

- The floor β is one number per run; it is probably a function of the surface slant within
  the window. C2 takes the measured per-level value; a per-cell floor from the window's
  parallax spread (which the truth shows but the matcher cannot) is not attempted.
- Gross errors survive the LR test at depth edges (foreground fattening, 4–10% per level on
  the stub). The belief's fusion in C2 has to be robust to them; the truth will say how many
  reach it.
- Rows are spaced by 1/sin θ_mid for the whole level, so at ±45° cells are up to 30% off
  square; fine for matching along rows, and the belief in C2 is keyed by direction, not by
  these cells.
- Near the baseline axis (θ within 5°) nothing is owned; a policy that fixates there gets no
  field. The scenes' targets do not sit there.
