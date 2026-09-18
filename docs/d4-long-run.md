# Step D4 — the run to saturation, and a second look as the test

Written 2026-09-18 after D2b's report (bc7c71d), before the workstation run. Numbers are
**predicted** or from the stub until the log records a measurement.

## Where D2 ended (D22)

The neighbour test is the best thing tried and it is modest: wrong peaks at levels 0–2 on
`class_coverage_full` from 26.1 / 22.7 / 16.3% to 17.6 / 15.4 / 12.6% for 2% of the right peaks;
the offline rule (a third at each level) missed by one point at levels 0–1 and ten at level 2,
so the loop was not run with it. The rule stands; and the area line says it would not have
mattered — outside the model 10.5 → 9.2% of the judged area, of which occluded + window are
8.2. Half of the search kind goes; the window kind stays (a sixth removed). Depth edges and
half-occlusions agree with their neighbours along the edge and with their parents across
scales. At one look, that 8% is the scene's, not the matcher's.

A loop has what a matcher does not: another look, from another gaze, with another window over
the same surface. Whether that is worth anything is an empirical question about
**repeatability**, and the long run D4 was always going to make is the record that answers it.

## What D4 is

**One run**: coverage-first, `full`, the classroom, 500 fixations (predicted 13–15 min, 13 G
rays; overnight class by CLAUDE.md's definition — over five minutes — so one sentence in the
log before it starts, and the record is a pinned asset: nothing in Phase D after this renders).

**The policy had to change to make it.** Coverage-first's gain is "not yet looked at finely";
once the cap is covered (predicted K ≈ 110–150) every score is zero and `argmax` returns
candidate 0 for ever. `Policy.choose` now continues as **least-looked**: when the best disc
holds under 5% unvisited area, the score becomes Σ area / (1 + fine looks) — coverage of the
next look. `belief.looks` counts fine looks per cell (once per fixation); the step records the
phase. Until the cap is covered nothing changes, so **the first 50 fixations must reproduce
C3b's `class_coverage_full`** (check (z0)). Self-test: on a cap already covered the policy
returns six distinct directions; with the second phase disabled it returns one (the negative,
run in the sandbox).

**Read at checkpoints** K = 10, 25, 50, 100, 200, 300, 500 by `active_eval.py` from the recorded
metrics: coverage any / fine, ρ error median / 90th percentile / fine band, gross = coarse +
outlier, outlier by band, z RMS, the policy phase.

**`tools/second_look.py`, on the record.** Per belief cell of the cap, every fine look (levels
0–1, LR-consistent) in order, up to eight. A look is *bad* when it is beyond 25% and beyond 3
of its own σ (D21's outlier, per look). Reported: how many looks cells get; **P(second bad |
first bad) against P(second bad | first good)**; whether two looks *agree* (within 3σ) for
good–good, one-bad and bad–bad pairs — bad–bad pairs that agree are what a consensus cannot
catch; and the fine band's 25% gross under four fusions: first look, inverse-variance mean (what
the belief does), median, consensus (the largest set of mutually agreeing looks; no majority:
undecided, reported). Checks: (z1) the fine cells it collects are exactly `belief.npz`'s
`best_level ≤ 1` cells; (z2) the rules coincide on one-look cells.

## Commands (workstation)

```bash
for t in belief stereo_field gross_diagnosis second_look; do .venv/bin/python tools/$t.py --self-test; done          # interactive
# log one sentence first (overnight class: > 5 min). Then:
B=scenes/classroom/classroom_eye.blend
blender -b $B -P tools/active_loop.py -- --out previews/loop4/class_coverage_full_500 --profile full --policy coverage --fixations 500 --kappa 3.8
.venv/bin/python tools/active_eval.py previews/loop4/class_coverage_full_500                                        # batch: the replay re-fuses 500 fields
.venv/bin/python tools/second_look.py previews/loop4/class_coverage_full_500                                        # batch
.venv/bin/python tools/second_look.py previews/loop4/class_coverage_full_500 --upto 100
.venv/bin/python tools/second_look.py previews/loop4/class_coverage_full_500 --upto 200
.venv/bin/python tools/sphere_views.py previews/loop4/class_coverage_full_500 --truth previews/reference_full_L/classroom   # the picture, as in the Phase C summary
```

## Checks

- **(z0) the first fifty are C3b's.** Checkpoint 50 against `class_coverage_full`: coverage
  0.930 / 0.094, ρ error 0.0427 (fine 0.0177), gross 0.344 = 0.240 + 0.104. Equal to the digits
  printed if the renderer is deterministic at fixed seeds (it has been); if not equal, report
  the differences and whether the 50 directions are the same — a finding about the engine, not
  a failure of D4.
- (s), (t), (u) on the long run. (t)'s band is [0.4, 2.5]: the stub's z RMS climbs with the
  looks (1.02 → 1.60 over 70 fixations on a 20° cap) because averaging makes the belief sure
  of cells a wrong peak sits in; if (t) fails at 500, that is the same finding, reported, not
  patched.
- (z1), (z2) of `second_look.py`.

## Predictions, written before the run

1. Least-looked begins at K = 110–150; no lock: at least 450 distinct directions of 500.
2. Fine coverage 0.094 at 50 → 0.17–0.22 when the cap is covered → at most 0.30 at 500: on
   this scene about a fifth of what the fovea looks at is matchable finely, and looking again
   adds the margin's cells slowly.
3. Median ρ error 0.0427 at 50 → 0.025–0.032 at 500. It **saturates above** the fine band's
   0.015–0.019: the plan's second outcome — there is a floor the fovea does not remove,
   because most of the cap is never fine.
4. Gross falls, and changes composition: coarse 0.240 → 0.10–0.15 (looking cures resolution),
   outlier 0.104 → 0.13–0.18 (the fine and mid bands' rates take over, and a mean keeps every
   confident wrong peak it is given). Stub, measured on a 20° cap: coarse 0.336 → 0.156,
   outlier 0.173 → 0.228.
5. **Bad looks repeat**: P(second bad | first bad) 0.45–0.65 against P(second bad | first good)
   0.08–0.15 (stub: 0.535 against 0.085). That is D22's claim in one number — the outliers are
   mostly the scene's — and D22's "overturned if" is this line failing low.
6. Consensus still buys something: the fine band's gross a quarter to a third below the mean's
   with under 10% undecided (stub: 26.1 → 17.9%, 4.3% undecided); the median about half of that.
   Bad–bad pairs agree more often than not (stub 67%), which is its ceiling.

## What the numbers decide

Reported by Code, decided by Chat and Luiz. If 6 holds, Phase D's last step is a consensus
fusion in the belief (a handful of fine looks kept per cell), judged by re-fusing *this* record
— no rendering — and then D3's comparison. If 5 fails low, D22 is overturned and the same step
is worth more. If 6 fails, Phase D closes here with its account: three quarters of "gross" was
resolution; of the rest, what is removable at one look is the search kind; edges and
occlusions are a block matcher's floor on this sensor, about 8% of the area; and the budget
curve is the figure.

## Results

_To be filled by Code: the log sentence; wall time and seconds per fixation (choose / render /
infer / judge medians); the [eval] line and the checkpoint table verbatim; (z0) with the
numbers side by side; the three second_look reports verbatim (500, 100, 200); the picture's two
[views] lines and the sheet copied to docs/reference/views_classroom_full_500.png; the six
predictions held / failed with the number; disk used by the run._
