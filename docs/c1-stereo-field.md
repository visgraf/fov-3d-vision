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
range, `--search-deg` (3°) converted to cells per level. Both maps are then smoothed along θ by
[1, 2, 1]/4 — measured on a synthetic wall (see the self-test): at the coarse levels a cell holds
one or two samples, the map has power up to the grid's Nyquist, and the Lucas–Kanade step,
which models the map as piecewise linear between cells, recovers only half of a fractional
shift (bias +0.09 cells at level 4 for true shifts of −0.16; none on a wall at 20 m where the
shift is ~0); one pass of smoothing halves that bias and lowers the level-0 RMS from 0.14 to
0.06 cells on the same wall. Then B3's matcher unchanged: NCC over a 5×5 window along the row,
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
- **(p) regression** — level 0's inlier RMS at the fixated cards is within 25% of `stereo.json`'s
  instrument RMS on the same run: the field *is* the instrument where they overlap. Stub: 0%
  apart (0.0512 vs 0.0510°). Negative: `--eval-factor 4` fails it at 134%.
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

## Results

*(filled by Code from the workstation run)*

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
