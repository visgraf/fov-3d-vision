# Phase D — plan: a reliable multiscale depth from the field

Written 2026-09-17; revised 2026-09-18 after a third-party review
(`docs/reviews/2026-09-18-phase-d-suggestions.md`). Nothing here has run.

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
