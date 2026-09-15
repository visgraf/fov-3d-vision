# Step B3 — the stereo instrument, the bound, and the E₂ / e_max sweep with a disparity objective

Written 2026-09-15 before the workstation run. Numbers are **predicted**, **assumed**, or from
the stub (plumbing only) until the log records a measurement.

## What B3 is

D11 left E₂ = 2°, e_max = 45° standing because Phase A's two criteria disagreed and named the
criterion that decides: disparity error at the fixated targets, per ray. An error needs an
estimate. This step supplies one as an instrument (D15) and, beside it, a number that needs no
matcher at all, so the sweep's ranking can be read two ways. Then A6's five settings are re-run
as fixation pairs and ranked.

## The maps

Per pair, each eye's foveal samples (±2° about its gaze, `--fovea-deg`) are integrated
finest-owns onto a local grid in the epipolar frame (D13) at s_eval = 2 s₀ (D9): rows are
epipolar planes φ, shared by the two eyes; columns are θ from each eye's own gaze, so a
correspondence is a shift along a row. Row spacing is scaled by 1/sin θ_mid so cells are square
on the sphere at the fovea. The R map is wider than the L map by the search range on both
sides, so a correspondence within range always lies inside it. Values are the mean of RGB, as
in Phase A's checks. 21×21 cells at small, 41×41 at full; interactive class per run.

## The instrument (D15)

Per L cell: normalised cross-correlation of a 5×5 window against the R row over integer shifts
in ±12 cells (`--search`; ±2.4° at small), winner-take-all, then two Lucas–Kanade steps on the
mean-removed windows with R interpolated linearly along θ for the sub-cell part. A 3-point
parabola on the NCC peak was tried first and locks to the integer by up to a quarter cell on an
exact peak (measured in the self-test); the gradient step does not. Estimated parallax =
(θ_gaze,R − θ_gaze,L) + shift × cell; error against `truth.npz`'s parallax on cells the other
eye sees. A cell is *matchable* when its window has texture above 3σ of the two maps' noise
and the bound below one cell — a window with no gradient along θ (a horizontal stripe, the
aperture problem) correlates at every shift and must not be judged. Reported per pair and per
run: inlier RMS (|error| ≤ 1 cell) in degrees, cells and s₀, the gross fraction, the bias, the
depth RMS via triangulation; and the same split into edge-free cells and cells whose window
spans a depth edge (foreground fattening), because the two failure modes are different.

## The bound

Per L cell, the Fisher information of a shift over the matcher's window,
I = Σ g² / (σ_L² + σ_R²), with g the L map's gradient along θ and σ per cell measured from the
seed pair (RMS of the two seeds' maps over the fovea, / √2); 1/√I bounds the RMS of any
unbiased estimator. The noise's own gradient (variance σ²/2cell² for a central difference)
would count as information on a flat surface — measured on the stub, a striped card got a
half-cell bound from noise alone — so only gradients above 2σ of that count, and the noise
variance is subtracted from them. Summed over the fovea without a window and divided by the
pair's rays, it is the matcher-free objective: **disparity information per ray**. On a run
without a seed pair σ is assumed from `--noise-rel` and labelled so; the sweep renders with
`--seed-pair`.

## Checks (`stereo_instrument.py`)

- **self-test** (`--self-test`): on a synthetic smooth texture shifted by a fractional number
  of cells (Fourier shift) plus white noise, the recovered median is within 0.1 cell, gross
  errors under 5%, and the inlier RMS between 1× and 3× the bound. Fails on a wrong shift sign,
  a wrong gather offset (both found this way) or a bound above the achieved error.
- **(l) self-shift** — the L map against itself shifted by 3 cells returns 3 on ≥ 99% of
  matchable cells (within 0.25 cell: pixel locking of an exact integer peak).
- **(m) recovery** — on every judged card, over the judged edge-free cells of the fixated
  surface (truth parallax within half a cell of the centre block's), the median estimate equals
  the median truth within one cell. On the `--vergence off` run that is a shift of ~1.8° (9
  cells at small; run it with `--search 24` so the 0.5 m ladder's 21 cells are in range); on the
  verged run ~0. A matcher that returned the map centre fails the control and the self-shift
  (shown on the stub: 23 failures). Judged only with ≥ 20 such cells; small cards whose fovea
  is mostly wall are reported.
- **(n) bound** — on every judged card the bound RMS is at most the inlier RMS (a bound above
  the measured error means σ or the model is wrong; a 3× σ fails it on the stub). The ratio
  inlier RMS / bound is reported; 1.5–3 is what a block matcher typically achieves (assumed).

## The sweep

A6's five settings — E₂ 1, 2, 4 at e_max 45; e_max 30, 60 at E₂ 2 — as `fixation_pairs.py`
runs at the small profile with `--seed-pair`, each through `stereo_truth.py` and
`stereo_instrument.py`, collected by `stereo_sweep.py` into a table and a chart of error at the
fixated cards against rays per pair, with the bound beside the instrument and the information
per ray as a column. The objective D11 named is the instrument's inlier RMS at the fixated
cards against its cost; the bound reads the same trade without the matcher. Decision rule, as
agreed: if the instrument and the bound rank E₂ the same way, D11 closes with that value; if
they disagree, the disagreement is the result and the instrument is the suspect (D15).

Predicted: E₂ = 4 has the lowest error per pair (denser sampling across the fovea: spacing at
2° is 1.5 s₀ against 3 s₀ at E₂ = 1) at 2.5× the rays of E₂ = 2; whether it also carries the
most information per ray is the question, and it is not obvious, because information adds over
cells and the extra rays at large E₂ go to the fovea where the texture is.

## Commands (small profile; batch class in total, each run seconds)

```bash
.venv/bin/python tools/stereo_instrument.py --self-test
# the standard setting, verged and control (B1's runs lack seed pairs; calib_room_sp has one)
.venv/bin/python tools/stereo_instrument.py previews/pairs/calib_room_sp --sheet
blender -b scenes/calib_room/calib_room.blend -P tools/fixation_pairs.py -- --out previews/pairs/calib_room_control_sp \
    --profile small --targets scenes/calib_room/calib_room.targets.json --vergence off --seed-pair
.venv/bin/python tools/stereo_truth.py previews/pairs/calib_room_control_sp
.venv/bin/python tools/stereo_instrument.py previews/pairs/calib_room_control_sp --search 24 --sheet
# the sweep
for s in "e2_1 --e2 1" "e2_2 --e2 2" "e2_4 --e2 4" "emax_30 --emax 30" "emax_60 --emax 60"; do
  set -- $s; name=$1; shift
  blender -b scenes/calib_room/calib_room.blend -P tools/fixation_pairs.py -- --out previews/sweep_b3/$name \
      --profile small --targets scenes/calib_room/calib_room.targets.json --seed-pair "$@"
  .venv/bin/python tools/stereo_truth.py previews/sweep_b3/$name
  .venv/bin/python tools/stereo_instrument.py previews/sweep_b3/$name --sheet
done
.venv/bin/python tools/stereo_sweep.py previews/sweep_b3/e2_1 previews/sweep_b3/e2_2 previews/sweep_b3/e2_4 \
    previews/sweep_b3/emax_30 previews/sweep_b3/emax_60 --out previews/sweep_b3
```

Full profile once, for the standard setting only (`calib_room_full` has no seed pair; render
one with `--seed-pair --profile full`, batch class, ~30 s), so the reported number is at the
reported profile.

## Results

Not yet run. To be filled: the instrument on the standard setting (verged and control, small
and full): (l), (m), (n) outcomes, inlier RMS in s₀ and cells, gross fraction split edge-free /
edges, RMS/bound ratio, information per ray; the sweep table and chart; the decision.

## What B3 leaves open

- The instrument's gross fraction on the Siemens-star cards, whose spokes alias at the centre
  (Phase A, learning 8), is expected to be the dominant term; it is reported, not hidden in an
  RMS. If it dominates the ranking, the sweep should also be read on the Classroom.
- Coverage. This sweep ranks by the fovea alone, as D11 named; A6's covered-sphere criterion
  still prefers a small E₂, and a gaze policy (Phase C) is what trades the two.
