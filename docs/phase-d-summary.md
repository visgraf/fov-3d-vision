# Phase D — summary

`visgraf/fov-3d-vision`, 2026-09-18, one day. State at `a5048b0` plus this closing commit, Phase D
closed. Every number below was measured on the lab workstation (Blender 5.2.1 LTS, OptiX,
RTX 4090) unless marked otherwise; the notes in `docs/` hold the commands. Six steps, five of
them offline on saved records in under a minute each; one render, of twelve minutes.

## The question

Phase C left an engine and a number that looked bad: on the classroom at `full` a third of the
measured cells (0.344) were wrong by more than 25%, and the picture showed it as speckle. D20
read that as the block matcher's wrong peaks at depth edges, named a remedy — coarse-to-fine
— and wrote a rule: the gross fraction down by a third. Phase D's question was whether the
existing field could be made reliable: find where the gross errors come from, remove the
removable, represent the rest, and see how far the belief gets as the budget grows.

## What was accomplished

**D1a — the diagnosis** (`gross_diagnosis.py`, `docs/d1-gross-diagnosis.md`). Each saved pair's
field is rebuilt with the run's own settings ((y1): the rebuilt rows are the record's on
99.999% of 213 541), the truth sidecar is carried through the same accumulation, depth edges
are judged per sample in the L raster, and every LR-consistent cell falls in one kind:
*occluded*, *window* (a wrong peak within a window radius of an edge), *search* (a wrong peak
elsewhere), *resolution* (the right peak, beyond 25% all the same), *good*. Beside it the
*parent oracle*: what a ±2-cell search about the level above would cure or put at risk —
coarse-to-fine's ceiling, read off the records before a line of it was written.

**D2a — the judge, and five features** (`docs/d2-wrong-or-right.md`). `belief.metrics` splits
gross = *coarse* (beyond 25%, within 3σ of the belief's own σ) + *outlier* (beyond both),
exactly; the thirteen Phase C runs were re-judged without rendering. `field_of_pair(features=
True)` exposes the NCC peak, its rival and the LR residual; with the bound and the parent's
disagreement, five things a confidence test could read without the truth, each judged by
what it rejects of the wrong peaks while keeping 90% of the right ones. The 3 × 3 window as a
what-if.

**D2b — the neighbour test** (`docs/d2b-neighbour-test.md`). A sixth feature — distance from
the median parallax of the consistent neighbours —, a logistic score of all six fitted on even
pairs and judged on odd ones, and the test itself behind `--nb-tol`, with an offline rule that
decided whether the loop would run.

**D4 — the run to saturation** (`docs/d4-long-run.md`). Coverage-first, `full`, 500 fixations,
12.0 minutes, 1.287 × 10¹⁰ rays, 1.43 s per fixation, no lock. The policy had to change to make
it: its gain is zero everywhere once the cap is covered (k = 146), so it continues as
*least-looked*. The first fifty directions are C3b's; the numbers differ in the fourth digit
(OptiX is not bit-deterministic; the loop is). `second_look.py` reads the record: every fine
look of every cell, whether bad looks repeat, whether two looks agree, four fusions.

**D5 — the consensus belief** (`docs/d5-consensus.md`, D23). `ConsensusBelief`, a subclass: a
cell's fine looks are kept apart from its coarse stream; its verdict is the fusion of the
largest set of mutually agreeing looks when that is a strict majority; no majority is
*undecided*, falls back to the coarse stream, and is exported. Judged by re-fusing D4's record
(`active_eval.py --refuse consensus`), five minutes, no render.

## The result

**Three quarters of "gross" was not error.** On `class_coverage_full`, by area, 41.5% of the
fused cells are wrong or beyond 25%; of that, resolution 74.6%, window 11.3%, occluded 9.2%,
search 4.9%. A coarse cell's right peak carries 0.3 of a cell of error, and 0.3 of a 1.6° cell
is 0.5° where a wall at 3 m has 1.2° of parallax. Those cells are inside the variance model.
Re-judged, the classroom at `full` is gross 0.31–0.37 = coarse 0.22–0.27 + **outlier
0.098–0.104**; in the fine band outlier ≈ gross (0.19–0.27), in the coarse band 0.06. What the
model does not contain is a tenth of the area, not a third (D21).

**At one look, what is left is the scene's.** Tried against the wrong peaks, each against a
rule written first:

| remedy | what it did | verdict |
|---|---|---|
| the parent as a prior (coarse-to-fine) | oracle ceiling: 3044 of 18 527 wrong peaks cured at levels 0–3, 1504 right ones put at risk; on the calib room 2780 cured against 8327 at risk at level 2 | not written |
| 3 × 3 window | classroom level 0: cells 4736 → 1557, wrong peaks 26.1 → 45.7%; loses at every level on both scenes | no |
| five truth-free features | best: the parent, 44.5% rejected at 90% kept; AUC ≤ 0.71; the NCC peak below a coin at the fine levels (0.45) | none is a test |
| agreement with the neighbours | best feature at every level (49 / 50 / 44% at levels 0–2); as a one-cell test, wrong peaks −32 / −32 / −23% for 2% of the right | rule (a third) missed by a point; an option, off |
| all six, logistic, cross-validated | AUC 0.72–0.79 | no |

The neighbour test removes 54% of the search kind and 17% of the window kind; outside-the-model
area goes 10.5 → 9.2% of the judged area, of which occluded + window are 8.2. Depth edges and
half-occlusions agree with their neighbours along the edge and with their parents across
scales (where a fine cell is wrong the level above is wrong too, 31–37%, or silent, 15–33%).
That is a block matcher's floor on this sensor: **about 8% of the area** (D22).

**More looks, with Phase C's fusion, buy almost nothing past coverage.** Median ρ error 0.0423
/m at 50 fixations, 0.0391 at 200, 0.0387 at 500 — ten times the rays for 9%. Fine coverage
stops at 0.295: seven tenths of this cap has nothing the fovea can match at 0.1–0.2°. The fine
band's own error *rises* as it grows (0.0132 → 0.0187), z RMS climbs 0.77 → 1.66, and the
inverse-variance mean is worse than a cell's first look at every multiplicity (27.9% of the
fine cells beyond 25%, against 25.2%). Bad looks repeat — P(second bad | first bad) 61.8%
against 11.3% — and the cells bad twice *and agreeing* are 8.6% of the twice-seen: the same
floor, from another side.

**But two looks are a test where one is not.** A pair that disagrees holds a bad look 94.4%
of the time; a pair that agrees, 13.8%. Nothing at one look came near that. Re-fusing the same
500 fixations with a consensus among the fine looks:

| at K = 500 | mean (recorded) | consensus (re-fused) |
|---|---|---|
| ρ error, median over measured cells (1/m) | 0.0387 | **0.0365** |
| ρ error, fine band | 0.0187 | **0.0151** |
| fine outlier / outlier | 0.206 / 0.136 | **0.171** / **0.126** |
| fine coverage | 0.295 | 0.263 + 0.032 undecided |
| z RMS | 1.66 | **1.27** |

With the consensus the fine band's error *falls* with the looks (0.0167 at 50, 0.0151 at 500)
where the mean's rose, and the overall curve is no longer flat (0.0420 → 0.0365). The mid and
coarse bands do not move (0.156 / 0.086): it touches the fine band only. D5's rule asked for
outlier ≤ 0.125 and fine coverage ≥ 0.265 and got 0.1257 and 0.2625: **in between**, by 0.0007
and 0.0025, so the live run was not made and the loop's default fusion is still the mean. Two
things about that, said after the fact and therefore not used to change the verdict: the
coverage clause counted the undecided cells as lost (0.2625 + 0.0322 = 0.2947 — they are the
cells the mean called measured and whose looks disagree), and both margins are smaller than
the difference between two identical runs on this renderer (gross 0.3440 against 0.3452).
Whether consensus becomes the default is the next phase's first decision, with its live run.

## What we learned

1. **A threshold relative to the quantity calls a coarse measurement wrong for being coarse.**
   The 25% rule was the judge's since C2 and nobody had asked what it meant at a 1.6° cell.
   C1's own table said it (level 4: 1.3% wrong peaks, inlier RMS 0.54°) a phase earlier. The
   first hour of Phase D, spent not touching the matcher, changed what every later number
   meant.

2. **An oracle before the build.** The parent oracle, the truth-free features at a fixed
   keep-rate, the what-ifs behind `--tag`, the re-fusion of a record: each answered "would this
   remedy work" from saved data in under a minute. Coarse-to-fine, the step the phase was
   opened for, was never written, and nothing is missing because of it.

3. **Rules written first were missed by a hair twice, and held both times.** D2b by one point,
   D5 by 0.0007. Both times the account did not depend on the verdict — the area line said
   why D2b's would not have mattered, the table above says what D5 found — which is what a
   rule is for: it keeps the decision from being made by whoever wants the result.

4. **Chat's predictions were wrong in instructive places.** "The search's at levels 3–4" (it
   was resolution); the parent's value "because the uncured sit inside the interval" (they
   were parent-wrong-too); "the consensus will repair the overconfidence", then its
   correction "it will not, z is on inliers" — and it did, 1.66 → 1.27, because a wrong peak
   averaged with right looks lands a cell *inside* 25% and far outside its σ. Each is in a
   note's Predictions with its verdict; the stub flattered every feature by about four tenths.

5. **A check is a definition, again.** (z1) asked that the fine looks collected equal the
   belief's fine cells and failed by 1422: the belief's gate drops a noisy fine look once two
   hundred coarse fusions have made it surer. By design; the check was wrong, as (p) and (u)
   were in Phase C. Code diagnosed it and left it, as the agreement says.

6. **The long run needed a policy that did not exist.** Coverage-first has nothing to say
   once the cap is covered; `argmax` of zeros is candidate 0 for ever. Least-looked is its
   continuation, parameter-free, caught in the sandbox by a saturating stub before twelve
   minutes of GPU were spent finding it.

## Why it matters

The project's framing is that what counts is the foveated region and how it supplies a dynamic
loop. Phase C showed the loop closes and that *where* to look hardly matters once looking twice
is avoided. Phase D's positive result is the complement: **looking twice is the only thing
that tells a wrong measurement from a right one, and the fusion has to be built to use it.**
Six one-look remedies moved the outliers by a tenth between them; one change to how looks are
combined moved the fine band's error by a fifth on the same rays and made the budget curve
bend again. And the undecided map — 3% of the cap, where looks disagree and one of them is bad
nineteen times in twenty — is a gaze target that needs no truth and no variance model, which
is what Phase C's policies lacked.

The negative result is as useful: the engine's errors are now accounted for. Where it looks
finely it is good to 0.015 /m (11 cm at 2.7 m); where it looks coarsely it says so; about 8% of
the area, at depth edges and half-occlusions, is the floor of the simple matcher chosen on
purpose in B3, and no amount of looking with that matcher removes it.

## What it leaves open

- **The default fusion.** Consensus is an option; the live 50-fixation run was not made.
  A fresh rule that counts undecided as undecided, then the run.
- **The undecided map as a policy.** D23's "overturned if": do the undecided cells resolve
  when looked at a third time, or are they the scene's 8%?
- **The edge floor.** A matcher that models the edge or the occlusion — adaptive support, a
  global method, a learned one, or the native-lattice matcher the project's context names as
  its research problem. It plugs into the same record and is judged by `gross_diagnosis.py`
  as it stands: the window and occluded kinds are its number.
- **The mid band.** Outlier 0.154 and untouched by D5; its cells get some twenty looks each, so
  a robust fusion there is cheap and unexplored.
- **The variance model over repeated looks.** z RMS still climbs under the consensus (0.97 →
  1.27): the noise part averages down over looks whose errors are correlated.
- **Fine coverage 0.30.** The scene's texture at 0.1°. The warp as an action (Phase C's open
  item) is the lever: a coarser s₀ or a larger E₂ where the fovea finds nothing.
- Unchanged from Phase C: head fixed, one-step greedy, truth only where the L eye sampled.

## Deliverables

- `tools/gross_diagnosis.py` (kinds, distance to an edge, the parent oracle, six features, the
  cross-validated score, `--tag` what-ifs); `tools/second_look.py`; in `tools/belief.py` the
  judge split, `looks`, least-looked, `consensus_of`, `ConsensusBelief`; `stereo_field.py`'s
  `features`, `neighbour_median`, `nb_tol_cells`; `active_loop.py --nb-tol --fusion`;
  `active_eval.py` checkpoints and `--refuse`; `sphere_views.py --belief`. Every default is
  Phase C's: every recorded run replays to 1e-9.
- `docs/d1-gross-diagnosis.md`, `d2-wrong-or-right.md`, `d2b-neighbour-test.md`,
  `d4-long-run.md`, `d5-consensus.md` — each with its predictions and their verdicts as Code
  wrote them; `docs/phase-d-plan.md` with both plans; D21, D22, D23.
- `docs/reference/d1_diagnosis_classroom_full.png`, `d1_diagnosis_calib_room_full.png`,
  `views_classroom_full_500.png`, `views_classroom_full_500_consensus.png`.
- The record: `previews/loop4/class_coverage_full_500` (14 GB, backed up at
  `/home/lvelho/data/loop4/`), with `belief_consensus.npz`, `refuse_consensus.json`,
  `second_look*.json`. Everything in D5 and anything the next phase asks of fusion or policy
  reads it without rendering.
