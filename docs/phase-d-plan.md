# Phase D — plan: a reliable multiscale depth from the field

Written 2026-09-17; revised 2026-09-18 after a third-party review
(`docs/reviews/2026-09-18-phase-d-suggestions.md`); **revised again 2026-09-18 after D1a ran
(D21)**: the section "Phase D after the diagnosis" below is the plan; D1's coarse-to-fine, D2
and D3 as first written are kept under it as the record of what was intended.

## Phase D after the diagnosis (D21)

D1a measured where the gross errors come from (`docs/d1-gross-diagnosis.md`). Three quarters
of the loop's gross, by area, is coarse right peaks — inside the variance model; about a tenth
of the judged area is outside it (window, occluded, search). Coarse-to-fine's ceiling is 16% of
the wrong peaks. On the classroom's fine levels the largest removable kind is wrong peaks *far*
from any edge (18-21% of the cells there), which neither a pyramid nor a smaller window touches.

- **D1 — closed as a diagnosis.** Coarse-to-fine is not written.
- **The judge (with D2a).** `belief.metrics` splits gross into coarse (within 3 sigma) and
  outlier (beyond); the thirteen saved runs are re-judged, no rendering. The outlier fraction
  is the loop's number from here. Predicted 0.08-0.15 on the classroom at `full`.
- **D2a — what tells a wrong peak from a right one** (`docs/d2-wrong-or-right.md`). Offline, on
  the saved pairs: NCC peak, peak minus rival, LR residual, bound in cells, disagreement with
  the parent; per level the share of wrong peaks each rejects while keeping 90% of the right
  ones, split window / search. Beside it, the 3 x 3 window as a what-if (`--window 1`). No
  matcher change.
- **D2b — the remedy the numbers pick**, one of: a rejection test in the field (a threshold
  on the best feature; a rejected cell is not measured), the inlier probability pi in the
  fusion (the first plan's D3, if no single feature is a test but several are), or the
  photometrically weighted window (if the window's share survives rejection). Judged offline
  on the wrong-peak fraction per level and the cells kept, then once in the loop on the
  outlier fraction, the fine band's error and coverage. The rule is written in D2b's note
  before it runs, from D2a's numbers.
- **D2b as it turned out** (`docs/d2b-neighbour-test.md`): D2a supported none of the three —
  no feature is a test (best 44.5% at 90% kept), AUCs at most 0.71, the 3 x 3 window loses
  everywhere. D2b tries the one thing a marginal cell's wrong peak cannot fake, agreement with
  its neighbours: a sixth feature, a what-if, and — if the offline rule is met — one loop run.
- **D2 closed (D22).** The neighbour test cuts wrong peaks by a third at the fine levels for 2%
  of the right ones and missed its rule by a point; outside-the-model area 10.5 -> 9.2%, of
  which edges and occlusions are 8.2. `--nb-tol` stays, off by default.
- **D4 moved up** (`docs/d4-long-run.md`): one run to saturation, and on its record the
  question D2 left — is a second look a test? Coverage-first gets a second phase (least-looked)
  because its gain is zero everywhere once the cap is covered.
- **D3 — coverage-first against expected information at `full`**, once the model contains or
  rejects its outliers (the first plan's closing comparison; either outcome counts).
- **D4 — the run to saturation**, unchanged.

What would count, restated: outlier fraction at `full` halved without losing more than a
tenth of the fine coverage; the picture's speckle gone without the median filter.

---

_The first plan, as written before D1a:_

## The question

Phase C's depth is right where the fovea has been (10–14 cm at 2.7 m) and wrong by more
than 25% on a third of the measured cells at `full`, half at `small` — at depth edges, where
a 5 × 5 window straddles two surfaces and the block matcher picks the wrong peak, or where
there is no right peak because the window contains two surfaces. The picture
(`docs/reference/views_classroom_full.png`) shows it as speckle. Phase D asks whether the
existing field can be made reliable: identify where the gross errors come from, remove the
removable ones, represent the rest, and see how far the belief gets as the budget grows. Not
whether active foveated stereo works (Phase C), not a new component.

## D1 — the diagnosis, then coarse-to-fine with a safety valve (`stereo_field.py`)

**First, before any matcher change: where do the gross errors come from?** On the saved
records with their truth (no rendering): for every judged gross cell, its level, its distance
to the nearest depth edge in the truth map (a jump of more than 25% in true ρ between
neighbouring cells), and whether the truth sidecar says the point is half-occluded (not
visible to the other eye — no correspondence exists). Three kinds: *occluded* (no matcher can
fix it), *near an edge* (within one window radius — the window's), *far from any edge* (the
search's: a wrong peak in a ±3–6° range). One figure, P(gross) against distance to an edge
per level, on `calib_room_full_sp` and a classroom run. Prediction, written now: the window's
at levels 0–1, the search's at levels 3–4; coarse-to-fine alone then moves the coarse levels
and the vergence, not the fine band, and D2 is needed. An hour; it decides what D1's number
is allowed to mean.

**Then coarse-to-fine.** Match the levels from the coarsest down. At level l each cell's
search is centred on level l+1's parallax at the same direction (its LR-consistent estimate,
the four children under one parent) and spans ±`--c2f-cells` (2). The parent is a proposal,
not a prior: a cell with no consistent parent keeps the full search; a narrow result that
lands on the interval's boundary, has a weak peak ratio, or fails LR consistency is retried
with the full search. The coarsest level searches as now. LR consistency, the bound, the
two-part variance and the visit map stay. `--no-c2f` keeps C1's matcher (the negative).

Checks, each of which can fail:
- **(w) the saved runs, level by level** — on `calib_room_sp` and `calib_room_full_sp`: the gross
  fraction after LR falls at every level with ≥ 200 judged cells, or stays within 1% where it
  was under 1%; (o), (p), (q), (r) still pass; `--no-c2f` reproduces C1's numbers to the third
  digit. Reported beside it: P(child gross | parent gross) and P(child gross | parent good) —
  whether the pyramid cures or propagates.
- **(x) the loop** — the classroom at `full`, coverage-first, 50 fixations, against C3b's run:
  median ρ error over measured cells (0.0427 /m) and gross fraction (0.344). Decision rule:
  coarse-to-fine wins if gross falls by a third or the error by more than the run-to-run
  spread (10%); loses if either rises; in between, the fine band's error decides. `infer`
  time per fixation must not rise (a narrower search should make it fall).
- **(s)–(v)** as before.

Order, as in every step so far: saved pairs → offline field → closed loop. Never the matcher
and the loop at once.

## D2 — the window (if D1 leaves the fine band's gross where it was)

If the diagnosis and D1 say the remaining gross sits within a window radius of the edges,
the observation itself is wrong and the window is the fix, not the belief. Two variants, no
more: a 3 × 3 window at levels 0–1 (`--window 1`, which exists), and a photometrically
weighted 5 × 5 — NCC weights w = w_s(i,j) · exp(−(I − I₀)²/2τ²), so the support follows the
surface instead of crossing the edge (adaptive support, one function). Judged by (w) and (x)
with the same rule. The question it answers is the reviewer's: is the residual error the
correspondence search's, or the assumption that one window is one surface?

## D3 — an inlier probability in the fusion (if gross stays above 20% after D2)

A measurement becomes (ρ̂, σ_noise, σ_floor, π): π the probability the correspondence is
right, from the LR residual, the NCC peak ratio and parent–child agreement, calibrated once
against the truth on the saved runs; the fusion weights by π. This is what Phase C's variance
model lacked and what D19 names as expected information's missing model. After it, one
comparison, coverage-first against expected information at `full`, and either outcome
counts: information wins and Phase C's ranking was a bad uncertainty model; it does not and
coverage is most of what gaze control buys, now shown with a model that contains its errors.

## D4 — the run to saturation (to decide next week)

One run, coverage-first at `full`, 500 fixations (13 minutes, 13 G rays; the loop records
every step, so K = 10, 25, 50, 100, 200, 300, 500 are read off it): coverage any and fine,
median and 90th-percentile |Δρ|, gross, vergence error against rays. Whether the error over
measured cells reaches the fine band's 0.015–0.019 /m or saturates above it is the number:
the first says the periphery guides until the fovea replaces it, the second says there is a
floor the fovea does not remove.

## What would count

Minimum: gross at `full` from 0.34 to ≲ 0.23 without worsening the fine band or coverage.
Strong: gross under 0.20 and median error ≈ 0.035 /m at 50 fixations, no slower. Very strong:
the long run approaching the fine band's error.

## Not in Phase D

The warp as an action, head motion, lookahead, learned matchers, truth beyond what the eyes
sampled.
