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

Run 2026-09-18 on the workstation, host side; **no render: the rule landed in between**, so the
live run was not made and `--fusion` keeps its default (`mean`). No code changed. No FAIL line.

**Self-tests** `belief`, `second_look`: ok. **`second_look.py`** on the 500-fixation record
(8.5 s, 0.70 GB): exit 0, every other line as in D4, and (z1) as corrected:

```
[look2] (z1) fine cells here 355601, in belief.npz 354179: missing here 0; fine looks the belief's gate dropped 1422 (reported)
```

**The re-fusion** (`active_eval.py --refuse consensus` on `class_coverage_full_500`: 5 min 09 s,
1.73 GB resident; exit 0, 0 failures; (s), (t), (u) ok; `belief.npz` and `loop.json` untouched
by mtime and size; `belief_consensus.npz`, `refuse_consensus.json`, `loop_fig_consensus.png`
written). The recorded checkpoints reproduce D4's to the digit; (r) reads 2.8e-16, a rounding
of the cap's area, not a displaced look.

```
[eval] class_coverage_full_500 coverage k 500 rays 1.287e+10 | cover any 0.993 fine 0.295 | rho err med 0.0387 (fine 0.0187) /m | depth med 0.331 (fine 0.188) m | gross 0.336 = coarse 0.200 + outlier 0.136 (outlier fine/mid/coarse 0.206/0.154/0.086; gross 0.216/0.239/0.451) | z 1.66 | verg err med 0.35 m | (s) replay ok; (u) fixation-0 cells 27427: rho err median 0.0397 -> 0.0160 -> loop_fig.png
[eval] class_coverage_full_500 checkpoints (recorded):   K |      rays | cover any / fine | rho err med / p90 / fine (1/m) | gross = coarse + outlier | outlier fine / mid / coarse | z RMS | undecided of cap | policy phase
[eval] class_coverage_full_500 checkpoint    10 | 2.574e+08 | 0.813 / 0.021 | 0.0515 / 0.3574 / 0.0132 | 0.384 = 0.296 + 0.088 | 0.208 / 0.168 / 0.059 | 0.77 | - | coverage
[eval] class_coverage_full_500 checkpoint    25 | 6.434e+08 | 0.876 / 0.048 | 0.0415 / 0.2903 / 0.0163 | 0.332 = 0.237 + 0.095 | 0.193 / 0.157 / 0.057 | 0.85 | - | coverage
[eval] class_coverage_full_500 checkpoint    50 | 1.287e+09 | 0.930 / 0.094 | 0.0423 / 0.2992 / 0.0177 | 0.345 = 0.241 + 0.104 | 0.218 / 0.154 / 0.058 | 1.01 | - | coverage
[eval] class_coverage_full_500 checkpoint   100 | 2.574e+09 | 0.960 / 0.171 | 0.0404 / 0.3193 / 0.0177 | 0.344 = 0.228 + 0.116 | 0.205 / 0.156 / 0.067 | 1.17 | - | coverage
[eval] class_coverage_full_500 checkpoint   200 | 5.148e+09 | 0.980 / 0.230 | 0.0391 / 0.3148 / 0.0186 | 0.337 = 0.211 + 0.126 | 0.213 / 0.149 / 0.075 | 1.38 | - | least-looked
[eval] class_coverage_full_500 checkpoint   300 | 7.721e+09 | 0.989 / 0.266 | 0.0386 / 0.3092 / 0.0185 | 0.336 = 0.202 + 0.135 | 0.209 / 0.157 / 0.085 | 1.48 | - | least-looked
[eval] class_coverage_full_500 checkpoint   500 | 1.287e+10 | 0.993 / 0.295 | 0.0387 / 0.3035 / 0.0187 | 0.336 = 0.200 + 0.136 | 0.206 / 0.154 / 0.086 | 1.66 | - | least-looked
[eval] class_coverage_full_500 distinct directions 469 of 500; least-looked from k = 146
[eval] class_coverage_full_500 checkpoints (re-fused consensus):   K |      rays | cover any / fine | rho err med / p90 / fine (1/m) | gross = coarse + outlier | outlier fine / mid / coarse | z RMS | undecided of cap | policy phase
[eval] class_coverage_full_500 checkpoint    10 | 2.574e+08 | 0.813 / 0.021 | 0.0517 / 0.3574 / 0.0135 | 0.384 = 0.296 + 0.088 | 0.212 / 0.169 / 0.059 | 0.77 | 0.0000 | coverage
[eval] class_coverage_full_500 checkpoint    25 | 6.434e+08 | 0.876 / 0.048 | 0.0416 / 0.2912 / 0.0162 | 0.332 = 0.237 + 0.095 | 0.196 / 0.157 / 0.057 | 0.84 | 0.0000 | coverage
[eval] class_coverage_full_500 checkpoint    50 | 1.287e+09 | 0.930 / 0.094 | 0.0420 / 0.3007 / 0.0167 | 0.345 = 0.242 + 0.103 | 0.210 / 0.155 / 0.058 | 0.97 | 0.0001 | coverage
[eval] class_coverage_full_500 checkpoint   100 | 2.574e+09 | 0.960 / 0.167 | 0.0398 / 0.3237 / 0.0165 | 0.343 = 0.228 + 0.115 | 0.200 / 0.157 / 0.067 | 1.06 | 0.0036 | coverage
[eval] class_coverage_full_500 checkpoint   200 | 5.148e+09 | 0.980 / 0.209 | 0.0379 / 0.3195 / 0.0159 | 0.333 = 0.213 + 0.120 | 0.190 / 0.152 / 0.075 | 1.14 | 0.0207 | least-looked
[eval] class_coverage_full_500 checkpoint   300 | 7.721e+09 | 0.989 / 0.239 | 0.0370 / 0.3119 / 0.0154 | 0.330 = 0.204 + 0.127 | 0.180 / 0.158 / 0.085 | 1.19 | 0.0274 | least-looked
[eval] class_coverage_full_500 checkpoint   500 | 1.287e+10 | 0.993 / 0.263 | 0.0365 / 0.3025 / 0.0151 | 0.328 = 0.203 + 0.126 | 0.171 / 0.156 / 0.086 | 1.27 | 0.0322 | least-looked
[eval] class_coverage_full_500 re-fused consensus vs recorded at K = 500: outlier 0.136 -> 0.126, fine outlier 0.206 -> 0.171, fine coverage 0.295 -> 0.263, rho err 0.0387 -> 0.0365 (fine 0.0187 -> 0.0151), z RMS 1.66 -> 1.27; (u) fixation-0 cells 0.0397 -> 0.0154; (r) fixation 0 coverage differs by 2.8e-16
[eval] ok (0 failures)
```

**The 50-fixation record** (`loop3/class_coverage_full --refuse consensus`, 29 s, exit 0; its
`belief.npz` and `loop.json` untouched). Its recorded steps predate the judge split, so the
"recorded" outlier reads nan on the comparison line; the recorded values are the [eval] line's
0.104 / 0.219. No recorded checkpoint table: the run has 50 steps (the table needs more than
60).

```
[eval] class_coverage_full    coverage k  50 rays 1.287e+09 | cover any 0.930 fine 0.094 | rho err med 0.0427 (fine 0.0177) /m | depth med 0.351 (fine 0.134) m | gross 0.344 = coarse 0.240 + outlier 0.104 (outlier fine/mid/coarse 0.219/0.154/0.058; gross 0.227/0.225/0.425) | z 1.01 | verg err med 0.38 m | (s) replay ok; (u) fixation-0 cells 27427: rho err median 0.0397 -> 0.0180 -> loop_fig.png
[eval] class_coverage_full checkpoints (re-fused consensus):   K |      rays | cover any / fine | rho err med / p90 / fine (1/m) | gross = coarse + outlier | outlier fine / mid / coarse | z RMS | undecided of cap | policy phase
[eval] class_coverage_full checkpoint    50 | 1.287e+09 | 0.930 / 0.094 | 0.0424 / 0.3049 / 0.0165 | 0.344 = 0.240 + 0.103 | 0.214 / 0.155 / 0.058 | 0.97 | 0.0001 | -
[eval] class_coverage_full re-fused consensus vs recorded at K = 50: outlier nan -> 0.103, fine outlier nan -> 0.214, fine coverage 0.094 -> 0.094, rho err 0.0427 -> 0.0424 (fine 0.0177 -> 0.0165), z RMS 1.01 -> 0.97; (u) fixation-0 cells 0.0397 -> 0.0179; (r) fixation 0 coverage differs by 2.8e-16
[eval] ok (0 failures)
```

### The rule at K = 500 — in between

Re-fused against recorded, the exact values from `refuse_consensus.json`:

| clause | recorded | re-fused | needed to win | |
|---|---|---|---|---|
| fine outlier | 0.206 | **0.1715** | ≤ 0.175 | met |
| outlier | 0.136 | **0.1257** | ≤ 0.125 | missed by 0.0007 |
| fine coverage | 0.295 | **0.2625** | ≥ 0.265 | missed by 0.0025 |
| ρ error median | 0.0387 | 0.0365 | not above +2% | met (−5.6%) |
| fine ρ error | 0.0187 | 0.0151 | not above +2% | met (−19%) |

Neither outlier rises and fine coverage stays above 0.250, so it does not lose; two clauses
miss by the last printed digit, so it does not win. **In between**: the flag stays an option,
no live run, no default change. Phase D closes with it.

**The picture** (3 min 44 s; `docs/reference/views_classroom_full_500_consensus.png`, from
`belief_consensus.npz`; the mean's sheet is `views_classroom_full_500.png`):

```
[views] engine vs truth on 3346001 shared cells: median |rho err| 0.0898 /m, median |depth err| 0.397 m
[views] engine depth drawn solid on 3.6% of the sphere, at half confidence or better on 9.2% (solid at sigma <= 0.021, grey at >= 0.091 /m)
[views] sphere at 0.0998261 deg: 66.4% of it seen by the L eye, 53.1% with a depth from the belief; white 1.922, depth scale 0.54-4.98 m
[views] -> /home/lvelho/rd/fov-3d-vision/previews/loop4/class_coverage_full_500/views_belief_consensus/sheet.png (+ 8 panels, 4 depth .npy, the scanpath)
```

Against the mean's sheet: median |ρ err| 0.0919 → 0.0898 /m, depth solid on 4.3 → 3.6% of the
sphere (the undecided cells fall back to the coarse stream and lose their fine σ), half
confidence 9.4 → 9.2%.

### The five predictions against the run

1. **Fine outlier 0.155–0.175, outlier 0.110–0.125 — fine held, outlier failed by 0.0007.**
   0.206 → 0.1715; 0.136 → 0.1257. By band at 500 the outlier is 0.171 / 0.156 / 0.086 (fine /
   mid / coarse) against 0.206 / 0.154 / 0.086 recorded: the consensus moves the fine band only,
   as the design says; the mid and coarse bands, where the wrong peaks of levels 2–4 live, are
   unchanged, and they are two thirds of the outlier area.
2. **Fine coverage 0.265–0.285, undecided 2–4% of the cap and 8–12% of the finely looked-at
   cells — coverage failed by 0.0025, undecided held.** 0.295 → 0.2625; undecided 0.0322 of the
   cap, which is exactly the fine coverage lost (0.2625 + 0.0322 = 0.2947) and 10.9% of the
   finely looked-at cells. Undecided grows with the looks: 0.0001 at 50, 0.0036 at 100, 0.0207
   at 200, 0.0322 at 500.
3. **ρ error median unchanged within 2%, the fine band's better by up to 5%, the 90th
   percentile falling more than the median — failed on all three, two of them in the good
   direction.** Median 0.0387 → 0.0365 (−5.6%), fine 0.0187 → 0.0151 (−19%), p90 0.3035 →
   0.3025 (−0.3%): the tail is the coarse cells' and the consensus does not reach it.
4. **z RMS stays at 1.55–1.66 — failed, downward.** 1.66 → 1.27 (0.97 at 50, 1.06 at 100, 1.14
   at 200). D23 said the climb was not the outliers' doing; a third of it goes with them all
   the same — the fine verdict replaces a mean whose noise variance had averaged down over
   correlated looks with a fusion of the agreeing members only, so the fine cells' σ is
   honest again where the looks disagreed. The rest of the climb (0.77 → 1.27) stays open.
5. **The rule is met — failed.** In between, by 0.0007 of outlier and 0.0025 of fine coverage.

Not decided here. What the numbers say for the record: on this scene the consensus removes a
sixth of the fine band's outliers (0.206 → 0.171) at the price of a ninth of its coverage
(0.295 → 0.263), moves the whole-cap outlier by a tenth (0.136 → 0.126) because the mid and
coarse bands carry two thirds of it and are untouched, and lowers the median error by 6% and
the fine band's by 19%. D23's "overturned if" (undecided cells that do not resolve on a
third look) is not tested by a re-fusion; it would need a loop that looks where its looks
disagree.
