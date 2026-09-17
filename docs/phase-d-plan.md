# Phase D — plan: coarse-to-fine in the field

Written 2026-09-17, for tomorrow. Nothing here has run.

## The question

Phase C's depth is right where the fovea has been (10–14 cm at 2.7 m) and wrong by more
than 25% on a third of the measured cells at `full`, half at `small` — gross errors at depth
edges, where a 5 × 5 window straddles two surfaces and the block matcher picks the wrong peak.
The picture (`docs/reference/views_classroom_full.png`) shows it as speckle; the summary lists
it first among what Phase C left open. The levels exist (C1) but each is matched
independently over the full ±3–6° search range. The question is whether initialising each
level from the one above it — pyramid stereo, the standard remedy — cuts the gross fraction
at every level and improves the loop's depth at equal rays, and by how much.

## D1 — coarse-to-fine matching (`stereo_field.py`)

Match the levels from the coarsest down. At level l, each cell's search is centred on level
l+1's parallax at the same direction (its LR-consistent estimate, upsampled: the four cells of
level l under one of level l+1 take its value) and spans ±`--c2f-cells` (2) — a cell or two,
not the ±15 cells the fovea searches today. Cells with no consistent coarse estimate under
them keep the full search (the fallback the first fixation needs). LR consistency, the bound,
the two-part variance and the visit map stay as they are. The coarsest level searches as now.
Two consequences beyond the gross fraction: the fovea's search range no longer has to cover
a wrong vergence estimate from the periphery (it covers the periphery's own parallax at that
direction), and the NCC cost per level falls with the range. `--no-c2f` keeps C1's matcher
for the comparison.

Checks, each of which can fail:
- **(w) C1's runs, level by level** — on `calib_room_sp` and `calib_room_full_sp`, the gross
  fraction after LR falls at every level with ≥ 200 judged cells, or stays within 1% where it
  was already under 1%; (o), (p), (q), (r) still pass; `--no-c2f` reproduces C1's numbers to
  the third digit (the negative).
- **(x) the loop** — the classroom at `full`, coverage-first, 50 fixations, against C3b's run
  at the same settings: median ρ error over measured cells (0.0427 /m) and gross fraction
  (0.344). Decision rule, written now: coarse-to-fine wins if the gross fraction falls by a
  third or the error by more than the run-to-run spread (10%); it loses if either rises; in
  between, the fine band's error decides.
- **(s)–(v)** as before.

Predicted: gross at levels 1–2 from 18–22% to under 10% at `full`; the loop's error from
0.0427 toward 0.035 /m; a fixation's `infer` time down, not up.

## D2 — a gross-error term in the fusion (only if D1 leaves gross above 20% in the loop)

The variance model does not contain gross errors, which is why the belief cannot down-weight
them and why expected information could not beat coverage-first. A mixture weight per
measurement — the probability it is an inlier, from the LR residual and the NCC peak ratio —
scales its precision at fusion. One day; D19's overturn clause names the experiment that
follows.

## D3 — the 500-fixation run (to decide next week)

Fine coverage grows at ~0.2% of the cap per fixation and the periphery does not improve
with repetition, so more fixations convert periphery into fovea roughly linearly until the
cap is covered at foveal quality — ~500 fixations, 13 minutes and 13 G rays at `full`, 16×
fewer than the panorama. One run, coverage-first, with the curves to saturation; whether the
error over measured cells reaches the fine band's 0.015–0.019 /m is the number.

## Not in Phase D

The warp as an action (E₂, e_max), head motion, lookahead policies, truth beyond what the
eyes sampled: still open, still not this.
