# Phase B — summary

`visgraf/fov-3d-vision`, 2026-09-14 to 2026-09-15. State at `509fc70`, Phase B closed. Every
number below was measured on the lab workstation (Blender 5.2.1 LTS, OptiX, RTX 4090) unless
marked assumed or predicted; the notes in `docs/` hold the commands that produced each one.

## The question

Phase A left one decision standing rather than made: E₂ and e_max (D11), because its two
criteria disagreed and the one that should decide — disparity error at the fixated targets,
per ray — could not yet be measured. Phase B's job was to add the second eye, produce the
ground truth a matcher is measured against, supply an estimate to measure, and close D11 with
a number. Along the way it had to keep Phase A's discipline: a check that can fail at every
step, a control that fails when it should, and a predicted number beside every measured one.

## What was accomplished

**B1 — the second eye.** `EYE` stays the head frame and the cyclopean point; the two eye
centres sit at ±ipd/2 on its local X (63 mm), each eye the Phase A foveated camera rotated
about its own centre — one translation added to `gaze_matrix`, nothing in the scenes changed
(D12). A verged pair fixates one world point, each eye's gaze P − Cᵢ. The record is D1 with the
origin per eye and two columns (`eye_id`, `pair_id`); per-eye folders are Phase A sequences, so
every Phase A tool runs on them. The foveae-on-target check: the Position pass at each eye's
central pixels lands on the fixation point within one sample spacing at the target's distance
(3.5 mm at 2 m at small) — measured 0.004 mm max, 0.002 spacings. The control, both eyes
parallel to the cyclopean gaze, misses by the amount the rig predicts, (ipd/2)√(1 − (right·ĝ)²),
to 3 µm on 72 fixations, and leaves the card on 12 as predicted. Check (a) with the eye 31.5 mm
off the head origin: 0.016 s₀, the Phase A residual; a wrong offset would have read 9 s₀. A pair
costs two fixations, 29 ms small, 271 ms full.

**B2 — the truth and the epipolar frame.** With both centres on the head's X axis every
epipolar plane contains that axis: a head-frame direction is (θ from +X, φ about X),
corresponding directions share φ, the parallax θ_R − θ_L is positive for every finite point
and equals the vergence at the fixated one, and the sine rule triangulates (D13). No rendering:
for every sample of B1's runs, the world point its ray hit, its direction from the other eye,
its position in the other eye's raster (an inverse of the warp), and whether the other eye
sees it, written as a `truth.npz` sidecar beside the record. Epipolar agreement and the
triangulation identity hold to 0.015 s₀ at p99.9 on 1.2 M and 5 M samples per run — the same
residual as check (a), so the correspondence adds no error of its own. Depth at the fixated
cards from the truth matches the target's distance to 0.005 depth quanta (one spacing of
parallax: 0.11 m at 2 m at small); the naive estimator that assumes zero parallax at the
centre passes on the verged run and gives infinity on all 42 cards of the control. Visibility:
93–95% visible, 4–6% occluded (cards in front of walls), 0.7–2.9% inconsistent at depth edges,
more at small than at full as raster resolution predicts. Per-eye small references were
rendered from the offset centres (61 s each) and pinned; the per-eye radiometric check reads
against them.

**B3 — the instrument, the bound, the sweep.** A reference matcher lives here as an
instrument, not the research matcher (D15): both eyes' foveal samples integrated finest-owns
onto a local (θ, φ) grid at s_eval = 2 s₀, NCC over 5×5 windows along the epipolar row, then two
Lucas–Kanade steps for the sub-cell part; error against the truth on cells the other eye sees,
split into inlier RMS and gross fraction, and again into edge-free cells and cells whose
window spans a depth edge. Beside it the matcher-free number: the Fisher information of
disparity per cell, one-sided gradient power over the two maps' noise², summed over the fovea
and divided by the pair's rays — disparity information per ray. Checks: a self-shift recovered
on 100% of cells, the fixated surface's parallax recovered within a cell on every judged card
(the control recovers a 9-cell shift), the bound below the achieved error on every card but
one at ratio 0.97. On the standard setting: inlier RMS 0.27 s₀ small and 0.42 s₀ full, gross
6% and 12%, RMS/bound 2.5 and 3.8. A6's five settings re-rendered as pairs and ranked:

| setting | raster | rays/pair | instrument RMS (s₀) | gross | bound (s₀) | info/ray |
|---|---|---|---|---|---|---|
| E₂ 1, e_max 45 | 77 | 0.60 M | 0.272 | 7.1% | 0.121 | 0.42 |
| E₂ 2, e_max 30 | 111 | 1.24 M | 0.294 | 10.8% | 0.095 | 0.44 |
| E₂ 2, e_max 45 | 126 | 1.60 M | 0.269 | 6.2% | 0.085 | 0.35 |
| E₂ 2, e_max 60 | 137 | 1.89 M | 0.284 | 7.8% | 0.088 | 0.27 |
| E₂ 4, e_max 45 | 200 | 4.02 M | 0.261 | 10.0% | 0.088 | 0.18 |

The error is flat in E₂ within 3.5% on both columns between E₂ 2 and 4, E₂ 1 is 40% worse on
the bound, and the cost spans 7×; per ray the cheaper setting wins on every column. D16 keeps
E₂ = 2, e_max = 45 as the middle of a flat optimum and closes D11.

## What we learned

1. **The objective D11 named is flat in E₂ at the scale the samples support.** At
   s_eval = 2 s₀ the fovea's cells are saturated for every E₂ in the sweep (spacing at 2° is
   3, 2 and 1.5 s₀), so denser foveal sampling cannot show in a disparity read at that scale.
   This is D9 doing its job, not a null result: it puts the disparity criterion on the same
   side as A6's coverage criterion, against only the fixated-RGB one, which was measured over
   whole cards up to 11°. The prediction that E₂ = 4 would win by a margin was wrong.

2. **Geometry can be verified to its own precision; the whole chain returned 0.015 s₀.**
   Check (a) with an offset eye, the epipolar identity, the triangulation identity and the
   foveae-on-target check all landed at the Position pass's residual. When a number comes out
   at the floor of the measurement, the geometry is right and the floor is the renderer's.

3. **Two eyes need two seeds.** Both eyes rendered at Cycles seed 0 on the same raster
   shared their Monte Carlo noise (correlation 0.95–0.98 on verged fronto-parallel cards),
   and a matcher then beats the noise bound by matching the noise. The stub had exactly this
   fault and it was fixed there a day earlier; it was not carried into the Blender-side tool
   and showed up on the workstation as (n) failing on ten cards. Independent seeds per eye
   (L 0/1, R 2/3) brought the correlation to 0.004.

4. **A bound has to be checked against the estimator it bounds, and it can fail.** The
   first bound took its gradient from a central difference, which has a null at the grid's
   Nyquist frequency; on Siemens-star spokes with a two-cell period it reported no gradient
   and sat above the error the instrument achieved on 14 of 37 cards at E₂ 1. One-sided
   gradient power has no null and is still below the continuous derivative's, so the bound
   it gives is a bound. Neither fault was visible in a sheet; both were a check failing by a
   small, consistent factor.

5. **The instrument's failure modes are worth separating.** Gross errors (a wrong NCC peak)
   sit on depth edges as foreground fattening and on aliased star centres; the inlier error
   is what the bound is about. Reporting one RMS over both would have hidden the flatness in
   E₂ under the gross fraction, which varies more (6–11%) than the inlier error does.

6. **Torsion is moot while the warp is isotropic (D14).** Directions are stored in the head
   frame and the warp is radially symmetric about the gaze, so an eye's torsion changes which
   raster pixel sampled which direction and nothing a consumer of the record can see.
   Listing's law enters only if D2 is overturned by an anisotropic warp.

7. **Stubs catch plumbing and lie about content.** A fake Blender with an analytic ray
   caster let every Phase B tool run end to end before a real render, and caught the map-edge
   rule, the noise-gradient information, the aperture case and the (m) block on a depth edge.
   It also had to be fixed three times — a periodic checker, sub-cell texture, shared noise —
   because a stub's texture decides what a matcher can do with it. What it verified was that
   the files, the checks and the negatives work; what it could not verify, the real run found.

8. **Small differences need a decision rule written before the run, and a reading after it.**
   The rule "same ranking on both columns" was met on the first run and failed by 3.5% on the
   second, on two settings within 3.5% of each other. The reading that closed D11 was the
   flatness, which the rule did not anticipate; Code was right to stop at the rule and the
   decision was taken in Chat, with the reason in the log.

## Why it matters

Phase A turned the foveation claim into a curve. Phase B turned the depth claim into a
measurement chain whose every link is checked against a prediction: a rig verified to 3 µm, a
correspondence verified to the renderer's own residual, an estimator verified against a self-
shift and a control, and a bound verified against the estimator. The result on E₂ cuts against
the prior — the setting that Phase A's RGB criterion favoured buys nothing for disparity at the
scale the samples support — which is what makes the closure of D11 credible. And the number
that decides is one a matcher cannot bias: disparity information per ray is "the same posterior
for less computation" read directly off the samples.

## How it carries into Phase C

Phase C is the gaze policy: which fixation next, given what the two eyes have. Phase B hands
it:

- **A rig and a record.** Two eyes on `EYE`, verged pairs from a world point or a target list,
  D1 v2 records per eye, and `truth.npz` for every sample — hit point, the other eye's view of
  it, visibility — regenerable in seconds.
- **The epipolar frame as one function.** (θ, φ) about the head's X axis; a matcher on the
  sphere works in it without rectification renders, and it does not depend on eye torsion.
- **Two objectives, one of them matcher-free.** The instrument's disparity error at the
  fixated cards and the disparity information per ray; the second is what a policy can
  maximise per fixation without a matcher in the loop, and both are read off a pair in a
  second.
- **The cost.** A pair is two fixations; the standard setting is 1.6 M rays per pair at
  small; information per ray falls 2.5× from E₂ 2 to E₂ 4 and rises 1.3× from e_max 45 to 30,
  so a policy that prices coverage has the numbers to trade against.
- **The check that can fail first.** A policy that chooses the next fixation by expected
  information must beat target order on information gathered per ray on the same scene, with
  the truth as the judge.
- **What is still open.** Coverage is not in the objective (D11 named the fovea; A6's
  covered-sphere criterion still prefers a small E₂, and e_max was not decided by B3).
  Correspondence across pairs, needed once a matcher works across fixations, is the same
  computation on the integrated maps and is not written. The per-eye radiometric check judged
  the wires at 5–6 of 8 against the offset references where the cyclopean run gave 8 of 8,
  read as lattice phase and not chased; it matters only if a per-eye D9 curve becomes
  load-bearing. Full-profile per-eye references (two overnight renders) were not made. The
  Classroom was not swept; D16's overturn condition names it.

## Deliverables

All in `github.com/visgraf/fov-3d-vision`, `main` at `509fc70`.

| Kind | What |
|---|---|
| Tools | `rig.py`, `warp.py` (pure numpy, both interpreters, `--self-test`), `fixation_pairs.py`, `check_pairs.py`, `stereo_truth.py`, `stereo_instrument.py` (`--self-test`), `stereo_sweep.py`, `preview360.py --eye-offset`; `render_foveated.gaze_matrix` with `offset_local`; `tools/dev/fake_blender_pairs.py` (stub Blender for plumbing) |
| Record format | D1 v2: origin per eye, `eye_id`, `pair_id`, `schema` and pose in `meta.json`; `pairs.json` per run with the rig; `truth.npz` + `truth_columns.json` sidecar per fixation |
| Assets (pinned, kept outside the checkout) | Per-eye small references from the offset centres, `reference_small_L` / `_R` in `scenes/manifest.json` |
| Results | `docs/b1-verged-pairs.md`, `docs/b2-stereo-truth.md`, `docs/b3-stereo-instrument.md` with their Results sections; `docs/reference/b3_sweep_calib_room_small.png`; per-run `check.json`, `truth.json`, `stereo.json`, sheets under `previews/` (regenerable) |
| Decisions | D12 (two eyes on the rig, origin per eye), D13 (truth as a sidecar, epipolar frame on X), D14 (torsion moot), D15 (the instrument), D16 (D11 closed) |
| Notes | `docs/log.md`, dated entries 2026-09-14 to 2026-09-15, measured-or-assumed; the bpy-less sandbox case in `CLAUDE.md` |
