# Step D5 — the consensus belief, judged by re-fusing D4's record

Written 2026-09-18 after D4's report (3c65e49), before the workstation run. Numbers are
**predicted** or from the stub until the log records a measurement. One short render at the
end, and only if the rule is met.

## What D4 said

Measured, `previews/loop4/class_coverage_full_500`. The curve is flat once the cap is covered:
median ρ error 0.0423 /m at 50 fixations, 0.0391 at 200, 0.0387 at 500, twice the fine band's
0.0187; fine coverage stops at 0.295 because seven tenths of this cap has nothing the fovea can
match at 0.1–0.2°. Bad looks repeat (61.8% against 11.3%): D22 stands, and the cells bad twice
*and agreeing* are 8.6% of the twice-seen — the edge floor again, from another side. The
belief's mean is worse than a cell's first look at every multiplicity (27.9% against 25.2%).
And two looks are a test: disagreeing pairs hold a bad look 94% of the time, agreeing pairs
14%; a consensus leaves 16.6 bad cells in a hundred where the mean leaves 27.9, and says
"undecided" of 9.3.

(z1) failed by 1422 cells and the check was wrong, not the run: the belief's gate drops a
noisy fine look when two hundred coarse fusions have made it surer, by design. (z1) now asks
that every fine cell of the belief has a fine look in the collection, and *reports* the
other direction as the gate's count.

One thing I had wrong in the reading: the consensus will not repair the climbing z RMS. That
statistic is computed on inliers, so the wrong peaks are not in it; it climbs because the noise
part of the variance averages down over looks whose errors are correlated. Left open (D23).

## What D5 is

`belief.ConsensusBelief`, a subclass: everything that reads a belief reads it unchanged (P, S,
Pn, F, n, best_level are the final arrays), and `SphereBelief` is untouched, so every recorded
run replays as before. Inside, a cell keeps two things apart: its **coarse stream** (levels
2–4, fused as now, gated as now) and its **fine looks** (levels 0–1, one per fixation — a
fixation's overlapping rows merged as the mean merges them — up to six). The cell's fine
*verdict* is `consensus_of` its looks: the leader is the look most others agree with (within
3σ), its members are fused, and the cell is decided when it has one look or the members are a
strict majority. No majority: **undecided** — the cell falls back to its coarse stream and is
exported (`belief.npz: undecided`), which is where a loop should look again. Verdict and
coarse stream are summed when they agree and the surer stands when they do not.

Judged without rendering: `active_eval.py <run> --refuse consensus` replays the record through
the other belief, prints the re-fused checkpoints under the recorded ones, and writes
`belief_consensus.npz`, `refuse_consensus.json`, `loop_fig_consensus.png`; nothing the run
wrote is touched. Coverage-first chooses from the visit map, which no fusion touches, so the
500 directions are the ones a consensus loop would have taken; only the vergence it would have
supplied differs (stub: live 0.172 against re-fused 0.175 outlier on the same directions).

Self-tests (`belief.py`): with one fine look per cell agreeing with its coarse stream the two
beliefs are equal to the last digit; three looks with one confident wrong peak — the
consensus holds 0.405, the mean 0.6+; two looks that disagree — undecided, the coarse value and
level stand; a third look settles it.

## Commands (workstation)

```bash
for t in belief second_look; do .venv/bin/python tools/$t.py --self-test; done                                     # interactive
.venv/bin/python tools/second_look.py previews/loop4/class_coverage_full_500                                       # batch: (z1) as corrected
.venv/bin/python tools/active_eval.py previews/loop4/class_coverage_full_500 --refuse consensus                    # batch, ~5 min (two replays of 500)
.venv/bin/python tools/active_eval.py previews/loop3/class_coverage_full --refuse consensus                        # batch: the 50-fixation record, for step 3's comparison
# ONLY IF the rule below says "wins": the live path, once (batch, ~80 s), and its picture
B=scenes/classroom/classroom_eye.blend
blender -b $B -P tools/active_loop.py -- --out previews/loop5/class_coverage_full_consensus --profile full --policy coverage --fixations 50 --kappa 3.8 --fusion consensus
.venv/bin/python tools/active_eval.py previews/loop3/class_coverage_full previews/loop5/class_coverage_full_consensus --out previews/loop5/compare
.venv/bin/python tools/sphere_views.py previews/loop4/class_coverage_full_500 --truth previews/reference_full_L/classroom --belief belief_consensus.npz   # -> views_belief_consensus/
```

## The rule, written before the run

On D4's record at K = 500, re-fused against recorded (fine outlier 0.206, outlier 0.136, fine
coverage 0.295, ρ error 0.0387, fine 0.0187): consensus **wins** if the fine outlier is ≤ 0.175
*and* the outlier ≤ 0.125, with fine coverage ≥ 0.265 and neither ρ error above the recorded
one by more than 2%; it **loses** if either outlier fraction rises or fine coverage falls
below 0.250; otherwise in between. Wins: the live run is made, and if it passes (s)–(u) with
its K = 50 numbers within 5% of the re-fused 50-fixation record's, `--fusion consensus` becomes
the loop's default (one line, Code's to change, in `active_loop.py`'s `add_argument`). Loses
or in between: the flag stays an option. Phase D closes either way.

Check (r), which can fail: re-fused fixation 0 covers the cap exactly as the record says
(the looks are the record's looks).

## Predictions

1. Fine outlier 0.206 → 0.155–0.175; outlier 0.136 → 0.110–0.125. (Stub, 70 fixations on a 20°
   cap, measured: 0.228 → 0.175 both.) Smaller than `second_look`'s 27.9 → 18.3%, because the
   belief's mid-level looks already vote in the mean.
2. Fine coverage 0.295 → 0.265–0.285; undecided 2–4% of the cap, 8–12% of the finely looked-at
   cells. (Stub: 0.993 → 0.946, 4.7%.)
3. ρ error median unchanged within 2%; the fine band's improves by up to 5%; the 90th
   percentile falls more than the median (stub: 0.172 → 0.150).
4. z RMS stays where it is (1.66 → 1.55–1.66). Not the outliers' doing; see above.
5. The rule is met.

## Results

_To be filled by Code: second_look's (z1) line; both checkpoint tables and the "re-fused vs
recorded" line verbatim, for the 500 and the 50 record; the rule's verdict with its four
numbers; if the live run was made: both [eval] lines, the 5% comparison, the default changed or
not (commit); the five predictions held / failed with the number._
