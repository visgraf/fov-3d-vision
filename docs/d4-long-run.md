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

Run 2026-09-18 on the workstation. The log sentence (entry "D4: the run to saturation
scheduled") was written before the render. No code changed. One FAIL line, (z1), diagnosed
below and left as it is.

**The run.** `previews/loop4/class_coverage_full_500`: 500 fixations, 1.287e10 rays, Blender
exit 0, **wall 717.7 s** (12.0 min; 721 s including Blender's start and exit; predicted 13–15).
Console totals: choose 88.7, render 311.1, infer 239.1, judge 78.8 s. **Per fixation, medians:
choose 0.191 / render 0.623 / infer 0.463 / judge 0.159 s**, 1.43 s in all (C3b's 50-fixation
run: 0.135 / 0.724 / 0.460 / 0.146 — choose is up 0.06 s, the looks map). No lock: the longest
run of one direction is 1; 469 distinct directions of 500; the phase switched to least-looked
at k = 146 (fine coverage 0.203 → 0.204 across the switch). Disk: 14 GB (L 6.7, R 6.7, field
0.16); backed up to `/home/lvelho/data/loop4/class_coverage_full_500` (rsync, 14 GB). The
manifest is not touched.

**The eval** (2 min 9 s, exit 0, 0 failures; (s), (t), (u) pass):

```
[eval] class_coverage_full_500 coverage k 500 rays 1.287e+10 | cover any 0.993 fine 0.295 | rho err med 0.0387 (fine 0.0187) /m | depth med 0.331 (fine 0.188) m | gross 0.336 = coarse 0.200 + outlier 0.136 (outlier fine/mid/coarse 0.206/0.154/0.086; gross 0.216/0.239/0.451) | z 1.66 | verg err med 0.35 m | (s) replay ok; (u) fixation-0 cells 27427: rho err median 0.0397 -> 0.0160 -> loop_fig.png
[eval] class_coverage_full_500 checkpoints:   K |      rays | cover any / fine | rho err med / p90 / fine (1/m) | gross = coarse + outlier | outlier fine / mid / coarse | z RMS | policy phase
[eval] class_coverage_full_500 checkpoint    10 | 2.574e+08 | 0.813 / 0.021 | 0.0515 / 0.3574 / 0.0132 | 0.384 = 0.296 + 0.088 | 0.208 / 0.168 / 0.059 | 0.77 | coverage
[eval] class_coverage_full_500 checkpoint    25 | 6.434e+08 | 0.876 / 0.048 | 0.0415 / 0.2903 / 0.0163 | 0.332 = 0.237 + 0.095 | 0.193 / 0.157 / 0.057 | 0.85 | coverage
[eval] class_coverage_full_500 checkpoint    50 | 1.287e+09 | 0.930 / 0.094 | 0.0423 / 0.2992 / 0.0177 | 0.345 = 0.241 + 0.104 | 0.218 / 0.154 / 0.058 | 1.01 | coverage
[eval] class_coverage_full_500 checkpoint   100 | 2.574e+09 | 0.960 / 0.171 | 0.0404 / 0.3193 / 0.0177 | 0.344 = 0.228 + 0.116 | 0.205 / 0.156 / 0.067 | 1.17 | coverage
[eval] class_coverage_full_500 checkpoint   200 | 5.148e+09 | 0.980 / 0.230 | 0.0391 / 0.3148 / 0.0186 | 0.337 = 0.211 + 0.126 | 0.213 / 0.149 / 0.075 | 1.38 | least-looked
[eval] class_coverage_full_500 checkpoint   300 | 7.721e+09 | 0.989 / 0.266 | 0.0386 / 0.3092 / 0.0185 | 0.336 = 0.202 + 0.135 | 0.209 / 0.157 / 0.085 | 1.48 | least-looked
[eval] class_coverage_full_500 checkpoint   500 | 1.287e+10 | 0.993 / 0.295 | 0.0387 / 0.3035 / 0.0187 | 0.336 = 0.200 + 0.136 | 0.206 / 0.154 / 0.086 | 1.66 | least-looked
[eval] class_coverage_full_500 distinct directions 469 of 500; least-looked from k = 146
[eval] ok (0 failures)
```

z RMS at the checkpoints 0.77 / 0.85 / 1.01 / 1.17 / 1.38 / 1.48 / 1.66: climbing as the stub's
did, and inside (t)'s band at 500.

**(z0) the first fifty are C3b's — the directions yes, the numbers to three digits, not four.**
All 50 `dir_head` of `loop.json` are identical to `loop3/class_coverage_full`'s (50 of 50).
At k = 50, loop3 / loop4: coverage 0.9302 / 0.9299 (both print 0.930), fine 0.0939 / 0.0943
(both 0.094), ρ error 0.0427 / 0.0423, fine 0.0177 / 0.0177, gross 0.3440 / 0.3452 (0.344 /
0.345) = coarse 0.240 / 0.241 + outlier 0.104 / 0.104, z 1.006 / 1.012, rays equal. The cause
is the engine: fixation 0's `fix.exr` and `samples.npz` have different checksums in the two
runs at the same seed, and its field `p000.npz` differs by up to 1e-5° of parallax in 4 cells
and 3e-6 /m of ρ in 2 cells with the same directions, levels and LR consistency. OptiX is not
bit-deterministic at a fixed seed; the loop is — a finding about the engine, as the check
allowed, not a failure of D4.

**`second_look.py`** (8.6 s, 0.70 GB resident at the default 8 looks; `--max-looks` not
lowered). The 500-fixation report exits 1 on (z1); the two `--upto` reports exit 0. (z2)
silent on all three.

```
[look2] /home/lvelho/rd/fov-3d-vision/previews/loop4/class_coverage_full_500: 500 fixations, fine = levels 0-1, up to 8 looks kept per cell
[look2] 352015 finely measured cells with truth: looks 1 / 2 / 3 / 4+ =  19.1 /  17.5 /  17.1 /  46.3% (median 3); a look is bad (beyond 25% and 3 sigma)  20.8% of the time
[look2] repeatability on 284648 cells with two looks: P(second bad | first bad)  61.8%  P(second bad | first good)  11.3%  (base rate first  21.6%, second  22.2%)
[look2] agreement of the first two looks (within 3 sigma): good-good  98.3%  one bad  13.8%  bad-bad  64.4%  (pairs 197921 / 48700 / 38027); P(a bad look in the pair | agree)  13.8%  | disagree  94.4%;  79.3% agree
[look2] fusion,   1 looks,    67367 cells: gross (25%) first look  32.2%  mean  32.2%  median  32.2%  consensus  32.2% with   0.0% undecided
[look2] fusion,   2 looks,    61478 cells: gross (25%) first look  28.9%  mean  32.5%  median  33.6%  consensus  15.4% with  27.2% undecided
[look2] fusion,   3 looks,    60023 cells: gross (25%) first look  27.6%  mean  32.5%  median  21.8%  consensus  19.2% with   7.8% undecided
[look2] fusion,  4+ looks,   163147 cells: gross (25%) first look  20.0%  mean  22.8%  median  16.1%  consensus  12.8% with   6.9% undecided
[look2] fusion, all looks,   352015 cells: gross (25%) first look  25.2%  mean  27.9%  median  23.2%  consensus  18.3% with   9.3% undecided
[look2] fusion,  2+ looks,   284648 cells: gross (25%) first look  23.5%  mean  26.9%  median  21.1%  consensus  14.6% with  11.5% undecided
[look2] (z1) fine cells here 355601, in belief.npz 354179, differ 1422
[look2] FAIL (z1) 1422 cells differ between the fine looks collected here (355601) and belief.npz's best_level <= 1 (354179)
[look2] FAILED (1 failures) -> /home/lvelho/rd/fov-3d-vision/previews/loop4/class_coverage_full_500/second_look.json
```

```
[look2] /home/lvelho/rd/fov-3d-vision/previews/loop4/class_coverage_full_500: 100 fixations, fine = levels 0-1, up to 8 looks kept per cell
[look2] 197237 finely measured cells with truth: looks 1 / 2 / 3 / 4+ =  87.4 /  12.6 /   0.0 /   0.0% (median 1); a look is bad (beyond 25% and 3 sigma)  20.0% of the time
[look2] repeatability on 24854 cells with two looks: P(second bad | first bad)  64.0%  P(second bad | first good)   7.3%  (base rate first  17.5%, second  17.2%)
[look2] agreement of the first two looks (within 3 sigma): good-good  99.0%  one bad  12.3%  bad-bad  74.4%  (pairs 19008 / 3064 / 2782); P(a bad look in the pair | agree)  11.5%  | disagree  94.9%;  85.6% agree
[look2] fusion,   1 looks,   172383 cells: gross (25%) first look  22.4%  mean  22.4%  median  22.4%  consensus  22.4% with   0.0% undecided
[look2] fusion,   2 looks,    24789 cells: gross (25%) first look  18.9%  mean  21.0%  median  21.7%  consensus  11.5% with  14.4% undecided
[look2] fusion,   3 looks,       65 cells: gross (25%) first look  18.5%  mean  21.5%  median  21.5%  consensus  19.0% with   3.1% undecided
[look2] fusion, all looks,   197237 cells: gross (25%) first look  22.0%  mean  22.2%  median  22.3%  consensus  21.2% with   1.8% undecided
[look2] fusion,  2+ looks,    24854 cells: gross (25%) first look  18.9%  mean  21.1%  median  21.7%  consensus  11.6% with  14.4% undecided
[look2] (z1) skipped (--upto)
[look2] ok (0 failures) -> /home/lvelho/rd/fov-3d-vision/previews/loop4/class_coverage_full_500/second_look_k100.json
```

```
[look2] /home/lvelho/rd/fov-3d-vision/previews/loop4/class_coverage_full_500: 200 fixations, fine = levels 0-1, up to 8 looks kept per cell
[look2] 274596 finely measured cells with truth: looks 1 / 2 / 3 / 4+ =  45.9 /  40.8 /  12.7 /   0.7% (median 2); a look is bad (beyond 25% and 3 sigma)  20.9% of the time
[look2] repeatability on 148655 cells with two looks: P(second bad | first bad)  63.8%  P(second bad | first good)   9.2%  (base rate first  19.5%, second  19.8%)
[look2] agreement of the first two looks (within 3 sigma): good-good  98.5%  one bad  14.9%  bad-bad  71.6%  (pairs 108764 / 21451 / 18440); P(a bad look in the pair | agree)  13.3%  | disagree  93.3%;  83.1% agree
[look2] fusion,   1 looks,   125941 cells: gross (25%) first look  27.0%  mean  27.0%  median  27.0%  consensus  27.0% with   0.0% undecided
[look2] fusion,   2 looks,   111962 cells: gross (25%) first look  21.1%  mean  23.9%  median  24.7%  consensus  12.5% with  18.1% undecided
[look2] fusion,   3 looks,    34878 cells: gross (25%) first look  20.2%  mean  21.2%  median  16.0%  consensus  15.3% with   2.9% undecided
[look2] fusion,  4+ looks,     1815 cells: gross (25%) first look  24.1%  mean  26.5%  median  19.8%  consensus  17.4% with   7.9% undecided
[look2] fusion, all looks,   274596 cells: gross (25%) first look  23.7%  mean  25.0%  median  24.6%  consensus  20.1% with   7.8% undecided
[look2] fusion,  2+ looks,   148655 cells: gross (25%) first look  20.9%  mean  23.3%  median  22.6%  consensus  13.3% with  14.4% undecided
[look2] (z1) skipped (--upto)
[look2] ok (0 failures) -> /home/lvelho/rd/fov-3d-vision/previews/loop4/class_coverage_full_500/second_look_k200.json
```

**(z1): 1422 cells (0.4% of 354179), all one way, not the rim.** Every one is a cell where
`second_look` holds a fine look and `belief.npz` has `best_level` 2 (1353 cells) or 3 (69);
no cell goes the other way. They lie across the cap (rows 390–1502, columns 1259–2128 of the
belief grid), hold 1 fine look in 1195 cases (2 in 171, 3–5 in 56), have been fused 23–321
times (median 198) from the coarse levels, and the belief's own `looks` counts 2–9 fine
ownerships on each. The cause is the belief's gate (`belief.py`, `add`): a measurement whose
variance is above the belief's current variance counts as *coarser*, and is dropped when it
disagrees by more than the gate's sigmas; on a cell fused two hundred times from levels 2–4
the belief is surer than one fine look (median σ ratio 1.36), so the fine look is the coarser
one and, when it disagrees, is gated — and `best_level` is set only for measurements that
pass. `second_look` collects every LR-consistent fine look regardless. The check is left
failing; which side should change is Chat's. It is the same mechanism as the climbing z RMS:
the inverse-variance mean gets sure of a cell from coarse looks and then refuses the fine one.

**The picture** (3 min 43 s; `docs/reference/views_classroom_full_500.png`):

```
[views] engine vs truth on 3346579 shared cells: median |rho err| 0.0919 /m, median |depth err| 0.405 m
[views] engine depth drawn solid on 4.3% of the sphere, at half confidence or better on 9.4% (solid at sigma <= 0.021, grey at >= 0.091 /m)
[views] sphere at 0.0998261 deg: 66.4% of it seen by the L eye, 53.1% with a depth from the belief; white 1.922, depth scale 0.54-4.98 m
[views] -> /home/lvelho/rd/fov-3d-vision/previews/loop4/class_coverage_full_500/views/sheet.png (+ 8 panels, 4 depth .npy, the scanpath)
```

C3b's 50-fixation sheet had depth solid on 1.1% of the sphere and at half confidence on 5.5%;
at 500 it is 4.3% and 9.4%.

### The six predictions against the run

1. **Least-looked at K = 110–150, no lock, ≥ 450 distinct — held.** From k = 146; 469 distinct
   directions of 500; no direction repeated even twice in a row.
2. **Fine coverage 0.094 → 0.17–0.22 at the switch → ≤ 0.30 at 500 — held.** 0.094 at 50,
   0.204 at k = 146, 0.230 at 200, 0.295 at 500.
3. **Median ρ error 0.0427 → 0.025–0.032 at 500, saturating above the fine band's — failed on
   the number, held on the saturation.** 0.0423 at 50, 0.0404 at 100, 0.0391 at 200, 0.0386
   at 300, **0.0387 at 500**: flat from K = 200, at 0.039 rather than 0.025–0.032, and twice
   the fine band's 0.0187. The 90th percentile 0.30–0.32 throughout.
4. **Gross falls and changes composition: coarse 0.240 → 0.10–0.15, outlier 0.104 → 0.13–0.18
   — outlier held, coarse failed.** Gross 0.345 → 0.336; coarse 0.241 → **0.200** (falls by a
   sixth, not by half); outlier 0.104 → **0.136**, in the predicted range; by band the outlier
   is 0.206 / 0.154 / 0.086 (fine / mid / coarse) at 500 against 0.218 / 0.154 / 0.058 at 50:
   the coarse band's outlier rate grows with the looks, the fine band's does not.
5. **Bad looks repeat: P(second bad | first bad) 0.45–0.65 against P(second bad | first good)
   0.08–0.15 — held.** 61.8% against 11.3% on 284648 cells with two looks (base rate 21.6 /
   22.2%); at 100 fixations 64.0 against 7.3%, at 200 63.8 against 9.2%. D22's "overturned
   if" does not fire.
6. **Consensus a quarter to a third below the mean with under 10% undecided; the median about
   half of that; bad–bad pairs agree more often than not — held, on all looks.** Fine gross
   (25%) over all 352015 fine cells with truth: first look 25.2%, mean 27.9%, median 23.2%,
   consensus 18.3% with 9.3% undecided — consensus 34% below the mean (a shade over a third),
   the median 17% below (half of that). On the 284648 cells with two or more looks: mean 26.9%,
   consensus 14.6% (46% below) with 11.5% undecided — over the 10%. Bad–bad pairs agree
   64.4% of the time (stub 67%); good–good 98.3%, one bad 13.8%. The mean is *worse* than
   the first look at every multiplicity (2 looks: 28.9 → 32.5%; 4+: 20.0 → 22.8%).

Reported, not decided: prediction 6 holds, so by the note's own reading Phase D's last step
would be a consensus fusion re-fused from this record; prediction 5 holds, so D22 stands.
