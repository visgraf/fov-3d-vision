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

First workstation run 2026-09-15 (Blender 5.2.1 LTS, RTX 4090 through OptiX for the renders;
`.venv` for everything else). Every number is **measured**; sources are `stereo.json`
(`summary`) of each run, `pairs.json` for render times, `previews/sweep_b3/sweep.csv` for the
table. Cost classes as measured: a seed-pair small render is interactive (11 s per sequence of
50 pairs, 0.09 s per pair with the seed pass); the full one is batch (33 s, 0.31 s per pair);
`stereo_truth.py` 0.6–1.9 s; `stereo_instrument.py` 0.5–1.0 s per run; the whole sweep
including renders about one minute.

### What had to change before the numbers meant anything

The first verged run failed (n) on 10 of 37 cards with the inlier RMS *below* the bound by up to
4× (p006: 0.0055° against 0.0209°). Diagnosed, not tolerated: both eyes were rendered at Cycles
seed 0 on the same raster, and on a verged, equidistant, fronto-parallel card L pixel (i, j) and
R pixel (i, j) see the same card point with the same random numbers, so the two maps shared their
Monte Carlo noise. Measured on the centre pixels: correlation of (L − L_seed1) with (R − R_seed1)
0.95–0.98 on the ring cards and the ladders, RMS(L − R) a quarter of the seed-pair noise; on the
control (9-cell offset) 0.04. `fixation_pairs.py` now renders the R eye at seeds (2, 3) and the L
eye at (0, 1), recorded in `pairs.json` and each `meta.json`; after the change the correlation is
0.004 and RMS(L − R) equals the seed-pair noise. Everything below is from the re-rendered runs.
(B2's per-eye (b) on the re-rendered R eye: 34/50, cards 29/42, wires 5/8, against 35, 30, 5
before; L unchanged.)

### The standard setting (E₂ 2, e_max 45)

| | small verged (`calib_room_sp`) | small control (`calib_room_control_sp`, `--search 24`) | full verged (`calib_room_full_sp`) |
|---|---|---|---|
| maps | 21×21 at 0.200° | same | 41×41 at 0.100° |
| (l) self-shift | 100.0% | 100.0% | 100.0% |
| (m) recovery | 37/37 judged pass; not judged: ring_e0_m0, ring_e2.5 ×4 | 36/36 pass (≈9 cells recovered); not judged: those five and ladder_0.5m | 42/42 pass, none excluded |
| (n) bound ≤ error | **fails on 3**: p006, p012, p013 (ratios 0.75, 0.92, 0.95) | passes | passes |
| judged cells | 12,607 | 11,325 | 60,507 |
| inlier RMS | 0.0269° = 0.13 cells = 0.27 s₀ | 0.0535° = 0.27 cells = 0.53 s₀ | 0.0208° = 0.21 cells = 0.42 s₀ |
| edge-free inlier RMS, median per card | 0.0188° | 0.0464° | 0.0190° |
| gross fraction, all / edge-free / edge cells (medians) | 6.3% / 0.0% / 31% | 16.2% / 13% / 32% | 12.1% / 4.3% / 46% |
| bias | +0.0107° | +0.0335° | +0.0021° |
| depth RMS via triangulation, median per card | 0.031 m | 0.074 m | 0.028 m |
| bound RMS | 0.0141° | 0.0144° | 0.0065° |
| RMS / bound, median per card | 1.62 | 3.14 | 2.68 |
| information per ray, median | 1.01e-1 | 9.3e-2 | 8.3e-1 |
| matchable fraction, median | 0.87 | 0.76 | 0.96 |
| render / truth / instrument seconds | 11.0 / 0.6 / 0.6 | 10.9 / 0.6 / 0.7 | 33.2 / 1.9 / 1.0 |

The control does what it is for: parallel gazes put the card 1.8° off each fovea, the
instrument recovers the ≈9-cell shift on every judged card, and the bias and gross fraction
rise because the card sits in the coarser part of each map. The full profile passes all three
checks on all 42 cards; the small cards are judged there because 0.1° cells give them enough
edge-free cells. The gross errors are almost entirely depth-edge cells (foreground fattening of
the 5×5 window at the card border, the red rings on the sheets); edge-free gross is 0% at small
and 4% at full, so the star centres' aliasing does not dominate here (they sit in the inlier RMS).

**The (n) failures, diagnosed and left standing.** On p006, p012, p013 (and 3–14 cards per sweep
setting, all Siemens-star rings at e = 6°–24°) the edge-free inlier RMS is half the bound
(p006: 0.0085° against 0.0170°, 50 cells, gross 0%). Three candidates were measured and two
ruled out: σ is not too high at the card (the seed-pair noise is *higher* at the star centre,
0.039–0.045, than over the map, 0.030–0.039, because sub-cell spokes alias under each seed's
jitter); the LK step is not shrunk by noise in its denominator (raw over signal-only gradient
power 1.02–1.05). What remains is the bound's derivative: it uses a central difference, which
cancels where adjacent one-sided slopes alternate sign, i.e. on texture at the cell's Nyquist
limit; the matcher's linear model uses the one-sided slopes. On the failing cards the one-sided
slope power is 4–9× the central-difference power, and a bound built from it puts every failing
card at 1.3–2.0× (p006 1.43, p012 1.97, p013 2.04, e2_1's p007 1.29). At full, the same spokes
span more cells, the factor drops to 1.6–2.0 and (n) passes. So the bound understates the
information of sub-cell texture by up to 9× and is not a valid lower bound there. Per the
working rule it was not changed to make the check pass; the change belongs to the bound's
gradient model and is Luiz's call. Until then the ratios in the table are read with that caveat.

### The sweep (small, all with seed pair; `previews/sweep_b3/sweep.csv`)

| setting | raster | samples/fix | rays/pair | judged cells | inlier RMS s₀ (deg) | gross | gross edge-free med. | bound s₀ (deg) | RMS/bound med. | info/ray med. (mean) | matchable med. | s/pair | (n) fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E₂ 1, e_max 45 | 77 | 4,669 | 597,632 | 10,948 | 0.282 (0.0281) | 7.2% | 0.0% | 0.193 (0.0192) | 1.30 | 1.083e-1 (1.365e-1) | 0.77 | 0.109 | 14 |
| E₂ 2, e_max 30 | 111 | 9,689 | 1,240,192 | 14,090 | 0.294 (0.0293) | 10.8% | 0.3% | 0.150 (0.0149) | 1.85 | 1.316e-1 (1.608e-1) | 0.87 | 0.085 | 11 |
| E₂ 2, e_max 45 | 126 | 12,492 | 1,598,976 | 12,607 | 0.269 (0.0269) | 6.3% | 0.0% | 0.141 (0.0141) | 1.62 | 1.010e-1 (1.073e-1) | 0.87 | 0.082 | 3 |
| E₂ 2, e_max 60 | 137 | 14,745 | 1,887,360 | 12,142 | 0.284 (0.0285) | 7.8% | 0.0% | 0.145 (0.0145) | 1.66 | 7.80e-2 (8.52e-2) | 0.84 | 0.084 | 5 |
| E₂ 4, e_max 45 | 200 | 31,428 | 4,022,784 | 13,171 | 0.261 (0.0262) | 10.0% | 0.0% | 0.130 (0.0130) | 1.69 | 5.08e-2 (6.15e-2) | 0.91 | 0.094 | 3 |

All five pass (l) at 100% and (m) on 37/37 judged cards (the five small cards not judged in
each); `stereo_truth.py` passes on all five ((i)/(k) 0.008–0.029 s₀; E₂ 1 has the largest
residual, 0.028 s₀, and e_max 60 one near-axis sample reported). Nothing complained about E₂ 1's
cap (+1.03% in A6): the instrument does not check it. Chart:
`docs/reference/b3_sweep_calib_room_small.png` (copy of `previews/sweep_b3/sweep.png`).

`stereo_sweep.py`'s line, verbatim: *lowest instrument error at the fixated cards: E2 4 e_max 45
(0.261 s0 at 4022784 rays/pair); most information per ray: E2 2 e_max 30 (1.316e-01). They
disagree: that is the result, not a tie-break.*

### The decision

The two readings do not rank E₂ the same way, so D11 stands and no decision is added.

- **Instrument, error per pair** at the fixated cards: E₂ 4 (0.261 s₀) < E₂ 2 (0.269) < E₂ 1
  (0.282). The spread is 8% across a 6.7× range of rays; the error at s_eval is set by the
  cards' texture and the window, not by the sampling density, once the fovea is sampled at or
  below the cell.
- **Bound, per pair**: the same order, E₂ 4 (0.130 s₀) < E₂ 2 (0.141) < E₂ 1 (0.193) — the
  instrument and the bound agree on what a pair delivers.
- **Bound per ray** (the cost-normalised reading): E₂ 1 (1.08e-1) ≈ E₂ 2 (1.01e-1) > E₂ 4
  (5.1e-2), and e_max 30 (1.32e-1) above all. Total information per pair is 6.5e4 / 1.6e5 /
  2.0e5 for E₂ 1 / 2 / 4: doubling E₂ from 2 to 4 buys 26% more information for 2.5× the rays,
  while 1 → 2 buys 2.5× for 2.7×. The extra rays at large E₂ go to the fovea, where the cards'
  texture is already resolved at 0.2° cells.

So: at equal cost the bound prefers a small E₂ and a small e_max (as A6's covered-sphere
criterion did); per pair both readings prefer E₂ 4 (as A6's fixated-targets criterion did),
by a margin the instrument cannot call significant. The disagreement is between per-pair and
per-ray, which is the cost model, not the matcher — and the (n) caveat above applies to the
information column (the bound's understatement is a property of the cards at 0.2° cells, the
same across settings: one-sided/central power 8.0 at E₂ 2 and 8.3 at E₂ 1 on the e = 6 cards),
so it moves all five rows together rather than reordering them, as far as measured. What would
settle it is a cost the objective actually pays — rays, or pairs — and the Classroom, whose
texture is not at the cell's Nyquist limit.

## What B3 leaves open

- The instrument's gross fraction on the Siemens-star cards, whose spokes alias at the centre
  (Phase A, learning 8), is expected to be the dominant term; it is reported, not hidden in an
  RMS. If it dominates the ranking, the sweep should also be read on the Classroom.
- Coverage. This sweep ranks by the fovea alone, as D11 named; A6's covered-sphere criterion
  still prefers a small E₂, and a gaze policy (Phase C) is what trades the two.
