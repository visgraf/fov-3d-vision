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

First workstation run 2026-09-15, instrument re-run the same day after the bound's gradient
model changed (`gradient_power_theta`: one-sided power instead of a central difference, see the
log). Every number is **measured**; sources are `stereo.json` (`summary`) of each run,
`pairs.json` for render times, `previews/sweep_b3/sweep.csv` for the table. The renders are the
first run's (no re-render was needed); the matcher did not change, so the instrument's numbers
are those of the first run except where the bound defines the matchable set (E₂ 1 lost 3% of its
judged cells, 10,948 → 10,608, and its inlier RMS moved 0.282 → 0.272 s₀; the other runs moved
by under 0.1%). Cost classes as measured: a seed-pair small render is interactive (11 s per
sequence of 50 pairs, 0.09 s per pair with the seed pass); the full one is batch (33 s, 0.31 s
per pair); `stereo_truth.py` 0.6–1.9 s; `stereo_instrument.py` 0.5–1.0 s per run.

### What had to change before the numbers meant anything

1. **Seeds.** The first verged run failed (n) on 10 of 37 cards with the inlier RMS *below* the
bound by up to 4× (p006: 0.0055° against 0.0209°). Both eyes were rendered at Cycles seed 0 on
the same raster, and on a verged, equidistant, fronto-parallel card L pixel (i, j) and R pixel
(i, j) see the same card point with the same random numbers, so the two maps shared their Monte
Carlo noise. Measured on the centre pixels: correlation of (L − L_seed1) with (R − R_seed1)
0.95–0.98 on the ring cards and the ladders, RMS(L − R) a quarter of the seed-pair noise; on the
control (9-cell offset) 0.04. `fixation_pairs.py` now renders the R eye at seeds (2, 3) and the L
eye at (0, 1), recorded in `pairs.json` and each `meta.json`; after the change the correlation is
0.004 and RMS(L − R) equals the seed-pair noise. (B2's per-eye (b) on the re-rendered R eye:
34/50, cards 29/42, wires 5/8, against 35, 30, 5 before; L unchanged.)

2. **The bound's gradient.** With independent seeds (n) still failed on 3 of 37 cards at the
standard setting and on 3–14 per sweep setting, all Siemens-star rings at e = 6°–24°, with the
edge-free inlier RMS half the bound and 0% gross (p006: 0.0085° against 0.0170° over 50 cells).
Measured and ruled out: σ too high at the card (the seed-pair noise is *higher* at the star
centre, 0.039–0.045, than over the map, 0.030–0.039, because sub-cell spokes alias under each
seed's jitter); LK shrinkage by noise in its denominator (raw over signal-only gradient power
1.02–1.05). What remained was the bound's derivative: a central difference has a null at the
grid's Nyquist frequency and reports no gradient on two-cell-period content, which the spokes
near a star centre have at s_eval, while the matcher's linear model uses the one-sided slopes.
On the failing cards the one-sided power was 4–9× the central-difference power. The bound now
takes the mean of the forward and backward squared differences (no null, still below the
continuous derivative's power) with the matching noise correction; the self-test gained a
near-Nyquist texture. Everything below is from that re-run.

### The standard setting (E₂ 2, e_max 45)

| | small verged (`calib_room_sp`) | small control (`calib_room_control_sp`, `--search 24`) | full verged (`calib_room_full_sp`) |
|---|---|---|---|
| maps | 21×21 at 0.200° | same | 41×41 at 0.100° |
| (l) self-shift | 100.0% | 100.0% | 100.0% |
| (m) recovery | 37/37 judged pass; not judged: ring_e0_m0, ring_e2.5 ×4 | 36/36 pass (≈9 cells recovered); not judged: those five and ladder_0.5m | 42/42 pass, none excluded |
| (n) bound ≤ error | passes (was 3 failures under the central-difference bound) | passes | passes |
| judged cells | 12,604 | 11,322 | 60,431 |
| inlier RMS | 0.0269° = 0.13 cells = 0.27 s₀ | 0.0535° = 0.27 cells = 0.53 s₀ | 0.0208° = 0.21 cells = 0.42 s₀ |
| edge-free inlier RMS, median per card | 0.0188° | 0.0464° | 0.0190° |
| gross fraction, all / edge-free / edge cells (medians) | 6.2% / 0.0% / 31% | 16.1% / 13% / 32% | 12.0% / 4.3% / 46% |
| bias | +0.0107° | +0.0335° | +0.0021° |
| depth RMS via triangulation, median per card | 0.031 m | 0.074 m | 0.028 m |
| bound RMS | 0.0085° (was 0.0141°) | 0.0094° (was 0.0144°) | 0.0045° (was 0.0065°) |
| RMS / bound, median per card | 2.54 (was 1.62) | 5.63 (was 3.14) | 3.84 (was 2.68) |
| information per ray, median | 3.47e-1 (was 1.01e-1) | 3.15e-1 (was 9.3e-2) | 1.63 (was 8.3e-1) |
| matchable fraction, median | 0.87 | 0.76 | 0.96 |
| render / truth / instrument seconds | 11.0 / 0.6 / 0.6 | 10.9 / 0.6 / 0.7 | 33.2 / 1.9 / 1.0 |

The control does what it is for: parallel gazes put the card 1.8° off each fovea, the
instrument recovers the ≈9-cell shift on every judged card, and the bias and gross fraction
rise because the card sits in the coarser part of each map. The full profile passes all three
checks on all 42 cards; the small cards are judged there because 0.1° cells give them enough
edge-free cells. The gross errors are almost entirely depth-edge cells (foreground fattening of
the 5×5 window at the card border, the red rings on the sheets); edge-free gross is 0% at small
and 4% at full, so the star centres' aliasing does not dominate here (they sit in the inlier
RMS). The new bound moved by a factor 1.4–1.7 across the three runs and RMS/bound sits at
2.5–5.6, where a block matcher is expected (assumed 1.5–3 before the run; the control's 5.6
is the coarse-map case).

### The sweep (small, all with seed pair; `previews/sweep_b3/sweep.csv`)

| setting | raster | samples/fix | rays/pair | judged cells | inlier RMS s₀ (deg) | gross | gross edge-free med. | bound s₀ (deg) | RMS/bound med. | info/ray med. (mean) | matchable med. | s/pair | (n) fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E₂ 1, e_max 45 | 77 | 4,669 | 597,632 | 10,608 | 0.272 (0.0270) | 7.1% | 0.0% | 0.121 (0.0120) | 1.93 | 4.23e-1 (5.14e-1) | 0.75 | 0.109 | 0 |
| E₂ 2, e_max 30 | 111 | 9,689 | 1,240,192 | 14,083 | 0.294 (0.0293) | 10.8% | 0.3% | 0.095 (0.0095) | 2.88 | 4.44e-1 (4.54e-1) | 0.87 | 0.085 | 1 |
| E₂ 2, e_max 45 | 126 | 12,492 | 1,598,976 | 12,604 | 0.269 (0.0269) | 6.2% | 0.0% | 0.085 (0.0085) | 2.54 | 3.47e-1 (3.41e-1) | 0.87 | 0.082 | 0 |
| E₂ 2, e_max 60 | 137 | 14,745 | 1,887,360 | 12,142 | 0.284 (0.0285) | 7.8% | 0.0% | 0.088 (0.0088) | 2.56 | 2.66e-1 (2.61e-1) | 0.84 | 0.084 | 0 |
| E₂ 4, e_max 45 | 200 | 31,428 | 4,022,784 | 13,170 | 0.261 (0.0262) | 10.0% | 0.0% | 0.088 (0.0088) | 2.62 | 1.78e-1 (1.89e-1) | 0.91 | 0.094 | 0 |

All five pass (l) at 100% and (m) on 37/37 judged cards (the five small cards not judged in
each); `stereo_truth.py` passes on all five ((i)/(k) 0.008–0.029 s₀). **One (n) failure
remains**: e_max 30, p007 ring_e6_m90, bound 0.01253° against inlier RMS 0.01218° (ratio 0.97;
178 judged cells, 85% of them edge cells, gross 28%). Reported and left as it is: a third gradient
model needs discussion. Under the old bound this card was at 0.54. E₂ 1's lowest per-card ratio
is 0.68 on a card (n) does not judge (its fovea is mostly wall). Nothing complained about E₂ 1's
cap (+1.03% in A6): the instrument does not check it. Chart:
`docs/reference/b3_sweep_calib_room_small.png` (copy of `previews/sweep_b3/sweep.png`).

`stereo_sweep.py`'s line, verbatim: *lowest instrument error at the fixated cards: E2 4 e_max 45
(0.261 s0 at 4022784 rays/pair); most information per ray: E2 2 e_max 30 (4.443e-01). They
disagree: that is the result, not a tie-break.*

### The decision

No decision is added; D11 stands. The re-run moved one ranking, and the rule set before it was
that a moved ranking is written up, not decided on:

- **Instrument, error per pair** at the fixated cards: E₂ 4 (0.261 s₀) < E₂ 2 (0.269) < E₂ 1
  (0.272) — the same order as the first run, now within 4% end to end (was 8%: E₂ 1's judged
  set shrank by 3% under the new bound and its RMS fell with it).
- **Bound, per pair**: E₂ 2 (0.085 s₀) < E₂ 4 (0.088) < E₂ 1 (0.121). This is what moved: under
  the central-difference bound it was E₂ 4 (0.130) < E₂ 2 (0.141) < E₂ 1 (0.193). The E₂ 2 / E₂ 4
  difference is 3.5% either way; E₂ 1 is 40% above both. Total information per pair: 2.5e5 /
  5.5e5 / 7.2e5 for E₂ 1 / 2 / 4.
- **Bound per ray**: E₂ 1 (4.2e-1) > E₂ 2 (3.5e-1) > E₂ 4 (1.8e-1), and e_max 30 (4.4e-1) above
  all: unchanged, the cheaper settings win per ray.

What the numbers say, without the decision they were conditioned on: at s_eval the disparity
objective at the fixated targets is flat in E₂ — 0.272 / 0.269 / 0.261 s₀ on the instrument,
0.121 / 0.085 / 0.088 s₀ on the bound (E₂ 1 apart) — and per ray the cheaper settings win,
with E₂ 1 failing A6's cap check and e_max being Phase C's coverage question. That is the
content D16 was to carry; its precondition (E₂ 4 < E₂ 2 on the bound) did not hold by 3.5%,
so it is left for Luiz to write or not. What would give the sweep a slope: a finer s_eval, or
the Classroom, whose texture is not at the cell's Nyquist limit.

## What B3 leaves open

- The instrument's gross fraction on the Siemens-star cards, whose spokes alias at the centre
  (Phase A, learning 8), is expected to be the dominant term; it is reported, not hidden in an
  RMS. If it dominates the ranking, the sweep should also be read on the Classroom.
- Coverage. This sweep ranks by the fovea alone, as D11 named; A6's covered-sphere criterion
  still prefers a small E₂, and a gaze policy (Phase C) is what trades the two.
