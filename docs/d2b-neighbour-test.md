# Step D2b — the neighbour test: one more feature, a what-if, and the loop if it earns it

Written 2026-09-18 after D2a's report (374e211), before the workstation run. Numbers are
**predicted** or from the stub until the log records a measurement.

## What D2a said

Measured, thirteen runs and four records. The judge split holds exactly where predicted: on
the classroom at `full` gross 0.31–0.37 is coarse 0.22–0.27 plus **outlier 0.098–0.104**; in
the fine band outlier ≈ gross (0.19–0.27), in the coarse band 0.06. D21's "overturned if"
does not fire. The fine band's one-in-five is Phase D's number.

None of the five features is a test. On `class_coverage_full`, levels 0–2, at 90% of the right
peaks kept the best single feature rejects 44.5% of the wrong ones (the parent, level 1); no
AUC above 0.71. The NCC peak is worse than a coin at the fine levels (AUC 0.45: wrong peaks
correlate *better* than right ones), the bound does not rank them (0.54), and the 3 × 3 window
loses on both scenes at every level (classroom level 0: cells 4736 → 1557, wrong peaks
26 → 46%). By D2a's own rule none of its three options is supported. My stated reason for
the parent's value was also wrong: the uncured are not mostly "inside the interval" at levels
0–2 (15–33%); they are "parent wrong too" (31–37%) and "no parent" (15–33%) — where a fine
cell is wrong, the level above is wrong or silent too.

What that pattern says (a reading, not a measurement): the classroom's fine levels hold few
matchable cells (about 95 of 1250 per pair at level 0), so what passes the texture gate is
the gate's margin, and a marginal cell's peak lands anywhere in ±60 cells with a respectable
NCC. Everything the matcher knows about such a cell *by itself* looks fine. A sandbox wall
with smooth shading and noise reproduces the regime (measured: at the margin 59% of matchable
cells are wrong and the LR test keeps 51%; below it the gates reject everything, above it
nothing is wrong). What D2a did not try is the one thing a wrong peak cannot fake: agreeing
with its neighbours.

## What D2b is

**A sixth feature.** `neighbours`: |parallax − median of the LR-consistent neighbours'
parallax| in cells, over radius window + 1 (7 × 7), at least three neighbours; cells with fewer
are *isolated* and counted apart (share of the right, share of the wrong). And **`combined`**:
a logistic score of all six plus the isolated flag, fitted on the even pairs and judged on the
odd ones — the honest ceiling of a π built from these.

**The test itself, behind a flag.** `field_of_pair(nb_tol_cells=1.0)`: an LR-consistent cell
more than one cell from that median is no longer consistent (so it is not fused); 
`nb_drop_isolated` drops the isolated too. Off by default: the record's fields rebuild exactly
((y1) 100.000% on the stub loop run). In the diagnostic it runs as a what-if (`--nb-tol 1 --tag
nb1`), which says directly what it buys: wrong peaks and cells kept per level, and the area
line now ends with *outside the model (occluded + window + search) X% of N deg² judged*.
`active_loop.py --nb-tol 1` turns it on in the loop; a loop run made with it carries it in
`loop.json`, and the diagnostic rebuilds it from there.

Self-test (`stereo_field.py`): the median against brute force; on the synthetic wall and card
the test drops wrong peaks at more than three times the rate of right ones and under 5% of the
right (measured: 22.8% of 92 wrong, 0.3% of the right — the card's edge errors are coherent
along the edge, so this is the window kind, the hard one for it).

## Commands (workstation)

```bash
for t in stereo_instrument stereo_field belief gross_diagnosis; do .venv/bin/python tools/$t.py --self-test; done   # interactive
# 1. the standard diagnoses again: the sixth feature and `combined` (levels, oracle, area as before)   # batch < 1 min each
.venv/bin/python tools/gross_diagnosis.py previews/pairs/calib_room_full_sp
.venv/bin/python tools/gross_diagnosis.py previews/loop3/class_coverage_full
# 2. the what-ifs                                                                                       # batch < 1 min each
for r in previews/pairs/calib_room_full_sp previews/loop3/class_coverage_full; do
  .venv/bin/python tools/gross_diagnosis.py $r --nb-tol 1 --tag nb1
  .venv/bin/python tools/gross_diagnosis.py $r --nb-tol 1 --nb-drop-isolated --tag nb1i
done
# 3. ONLY IF the offline rule below is met — the loop, once (batch, ~80 s), and its judgement against C3b's run
B=scenes/classroom/classroom_eye.blend
blender -b $B -P tools/active_loop.py -- --out previews/loop4/class_coverage_full_nb --profile full --policy coverage --fixations 50 --kappa 3.8 --nb-tol 1
.venv/bin/python tools/active_eval.py previews/loop3/class_coverage_full previews/loop4/class_coverage_full_nb --out previews/loop4/compare_nb
.venv/bin/python tools/stereo_truth.py previews/loop4/class_coverage_full_nb
.venv/bin/python tools/gross_diagnosis.py previews/loop4/class_coverage_full_nb
```

(Add `--nb-drop-isolated` to the loop command if, and only if, the offline rule is met by
`nb1i` and not by `nb1`.)

## The rules, written before the run

**Offline (step 2 → step 3), on `class_coverage_full`:** the what-if cuts the wrong-peak
fraction (of the cells with a correspondence) by at least a third at each of levels 0, 1 and
2, and keeps at least 85% of the *right* peaks at each (right peaks = judged cells with a
correspondence × (1 − wrong fraction), what-if over standard). Met by `nb1`: run the loop with
it. Met only by `nb1i`: run the loop with both flags. Met by neither: stop; D2 closes with
"at one look, the field's outliers cannot be told from the matcher's own evidence", and what
remains is D4, where a second look is the test.

**The loop (step 3), against C3b's `class_coverage_full`** (outlier 0.104, fine outlier 0.219,
fine coverage 0.094, fine ρ error 0.0177 /m, 75 s): the test **wins** if the outlier fraction
falls by a quarter (≤ 0.078) *and* the fine band's by a third (≤ 0.146), with fine coverage
≥ 0.085 and the fine band's error not above 0.0195; it **loses** if either outlier fraction
rises or fine coverage falls below 0.075; otherwise reported as in between. (s)–(v) as ever;
`infer` per fixation reported (the median costs a 48-layer stack per level: predicted +0.05 s).
Coverage-first chooses from the visit map, which the test does not touch, so the two runs fixate
almost the same directions and differ by the vergence the belief supplies.

## Predictions

1. `neighbours` is the best single feature on `class_coverage_full` at every level: rejects
   45–65% at levels 0–2 at 90% kept (stub: 75–86%; the renders have so far delivered about
   six tenths of the stub's numbers), search above window.
2. Isolated: 10–35% of the right peaks at level 0 on the classroom, and wronger than the rest
   (share of the wrong above share of the right).
3. `combined` adds 5–15 points to the best single feature, AUC 0.75–0.85 on the odd pairs.
4. `nb1` on `class_coverage_full`: wrong peaks at levels 0–2 from 26 / 23 / 16% to about half
   that, under 15% of the cells lost per level; outside-the-model area from 10.5% to 6–8%.
   The offline rule is met by `nb1`. (Stub loop, measured: wrong peaks 7.2 → 2.0, 4.9 → 2.3,
   2.6 → 1.3% for 2–6% of the cells; outlier 0.061 → 0.038, fine 0.087 → 0.048, fine coverage
   0.154 → 0.150.)
5. The window kind survives it (coherent along the edge): under 35% of the window's wrong
   peaks rejected at levels 0–1. If so, what is left after D2b is edges and occlusions — about
   half of today's outside-the-model area — and that is the honest floor of a block matcher.

## Results

Run 2026-09-18 on the workstation, host side (`.venv`), nothing rendered. **The loop did not run:
the offline rule is met by neither what-if** (the arithmetic below). No code changed. The four
self-tests ok. No FAIL line on any of the six diagnoses.

**The standard diagnoses** (`calib_room_full_sp` 18.2 s, `class_coverage_full` 22.7 s): exit 0,
(y1) 0.0000 and 99.999% of 213541 rows, (y2) ok. The level, right-peaks, parent-oracle and
uncured lines are D2a's, string-equal on both runs (20 lines each); the area line's first part
is D1a's, with the new tail — `calib_room_full_sp`: *outside the model (occluded + window +
search) 11.2% of 261183 deg2 judged*; `class_coverage_full`: *10.5% of 162647 deg2 judged*.
`combined` is present at every level (no level under 50 wrong or right peaks on either parity).
The loop run prints the `stereo_instrument.py` RuntimeWarnings known from D1a (now at lines
250–268); no nanmedian warning printed on any run. The "telling" lines:

`calib_room_full_sp`:

```
[diag] level 0 telling wrong from right at 90% of the right kept (3894 wrong, 41883 right) — rejects all / window / search, AUC: peak  14.8/ 16.6/  5.1% 0.43; margin  44.6/ 35.6/ 92.8% 0.72; lr_resid  35.9/ 29.8/ 69.0% 0.69; bound  52.6/ 48.0/ 77.7% 0.85; parent  30.1/ 20.4/ 82.0% 0.58; neighbours  35.8/ 26.6/ 86.3% 0.63; combined  52.7/ 44.0/ 98.8% 0.85; isolated (< 3 consistent neighbours):   0.0% of the right,   0.3% of the wrong
[diag] level 1 telling wrong from right at 90% of the right kept (16184 wrong, 53947 right) — rejects all / window / search, AUC: peak  14.8/ 18.1/  6.0% 0.51; margin  33.7/ 19.5/ 72.7% 0.68; lr_resid  22.6/ 16.7/ 38.9% 0.67; bound  25.3/ 13.1/ 58.7% 0.70; parent  43.2/ 34.2/ 67.9% 0.70; neighbours  34.0/ 23.1/ 63.8% 0.68; combined  34.1/ 20.2/ 79.4% 0.71; isolated (< 3 consistent neighbours):   0.0% of the right,   0.0% of the wrong
[diag] level 2 telling wrong from right at 90% of the right kept (19738 wrong, 92118 right) — rejects all / window / search, AUC: peak  23.7/ 28.6/  7.7% 0.65; margin  19.7/  9.0/ 54.8% 0.67; lr_resid  28.7/ 33.7/ 12.5% 0.70; bound   6.1/  4.6/ 10.7% 0.42; parent  17.3/  6.7/ 51.8% 0.61; neighbours  43.8/ 38.9/ 59.8% 0.74; combined  43.2/ 36.9/ 69.0% 0.79; isolated (< 3 consistent neighbours):   0.0% of the right,   0.0% of the wrong
[diag] level 3 telling wrong from right at 90% of the right kept (23103 wrong, 109458 right) — rejects all / window / search, AUC: peak   9.5/  8.5/ 11.8% 0.58; margin  23.4/ 15.3/ 41.3% 0.72; lr_resid  18.9/ 20.7/ 14.9% 0.66; bound   5.5/  4.5/  7.6% 0.40; parent  36.9/ 10.6/ 94.9% 0.62; neighbours  23.7/ 17.4/ 37.4% 0.64; combined  47.5/ 26.8/ 92.5% 0.83; isolated (< 3 consistent neighbours):   0.0% of the right,   0.0% of the wrong
[diag] level 4 telling wrong from right at 90% of the right kept (957 wrong, 56250 right) — rejects all / window / search, AUC: peak  23.6/ 31.9/ 20.5% 0.72; margin  33.8/ 30.0/ 35.2% 0.69; lr_resid  49.9/ 55.1/ 48.0% 0.79; bound  72.5/ 45.6/ 82.7% 0.91; parent   0.0/  0.0/  0.0% 0.50; neighbours  75.8/ 82.5/ 73.2% 0.87; combined  88.3/ 82.5/ 90.6% 0.96; isolated (< 3 consistent neighbours):   0.0% of the right,   0.0% of the wrong
```

`class_coverage_full`:

```
[diag] level 0 telling wrong from right at 90% of the right kept (1160 wrong, 3289 right) — rejects all / window / search, AUC: peak  11.4/  7.1/ 13.9% 0.45; margin  31.5/ 18.6/ 39.2% 0.71; lr_resid  13.1/ 15.6/ 11.6% 0.57; bound  18.0/ 11.3/ 22.1% 0.54; parent  33.9/ 24.4/ 39.6% 0.56; neighbours  49.0/ 28.2/ 62.1% 0.72; combined  39.9/ 21.1/ 59.3% 0.72; isolated (< 3 consistent neighbours):   0.4% of the right,   3.3% of the wrong
[diag] level 1 telling wrong from right at 90% of the right kept (3950 wrong, 13418 right) — rejects all / window / search, AUC: peak  14.4/ 10.3/ 17.0% 0.46; margin  34.4/ 15.0/ 47.0% 0.70; lr_resid  20.1/ 19.8/ 20.3% 0.63; bound  21.5/  8.6/ 29.9% 0.55; parent  44.5/ 27.7/ 55.3% 0.64; neighbours  50.4/ 30.3/ 63.7% 0.75; combined  56.0/ 23.2/ 76.3% 0.76; isolated (< 3 consistent neighbours):   0.2% of the right,   0.9% of the wrong
[diag] level 2 telling wrong from right at 90% of the right kept (6648 wrong, 34059 right) — rejects all / window / search, AUC: peak  15.8/ 14.8/ 17.5% 0.51; margin  28.4/ 12.9/ 54.7% 0.64; lr_resid  26.7/ 16.1/ 44.7% 0.64; bound  21.3/  7.7/ 44.5% 0.51; parent  39.7/ 25.6/ 63.6% 0.67; neighbours  43.6/ 21.6/ 81.4% 0.71; combined  52.0/ 31.1/ 83.0% 0.79; isolated (< 3 consistent neighbours):   0.1% of the right,   0.4% of the wrong
[diag] level 3 telling wrong from right at 90% of the right kept (6769 wrong, 56177 right) — rejects all / window / search, AUC: peak  17.3/ 18.0/ 14.5% 0.55; margin  24.8/ 13.4/ 70.8% 0.59; lr_resid  25.7/ 18.0/ 56.6% 0.64; bound  17.2/  5.7/ 63.1% 0.44; parent  37.3/ 26.2/ 81.9% 0.70; neighbours  40.0/ 28.2/ 87.5% 0.70; combined  41.4/ 32.6/ 82.6% 0.77; isolated (< 3 consistent neighbours):   0.0% of the right,   0.0% of the wrong
[diag] level 4 telling wrong from right at 90% of the right kept (2106 wrong, 39613 right) — rejects all / window / search, AUC: peak  19.4/ 18.4/ 21.2% 0.62; margin  23.7/ 11.2/ 46.1% 0.63; lr_resid  32.2/ 22.9/ 48.9% 0.69; bound  27.9/  3.5/ 71.5% 0.53; parent   0.0/  0.0/  0.0% 0.50; neighbours  52.7/ 39.2/ 77.2% 0.78; combined  52.6/ 34.6/ 86.3% 0.78; isolated (< 3 consistent neighbours):   0.1% of the right,   0.5% of the wrong
```

**The what-ifs** (exit 0 each; wall 20.0 / 20.0 s on the calib room, 24.3 / 24.3 s on the
classroom; (y1) "not judged"; the standard `gross_diagnosis.json` files kept their mtime;
`gross_diagnosis_nb1.*` and `_nb1i.*` written beside them). The first line of each names the
test: *neighbour test 1.0 cells (--nb-tol)*, *neighbour test 1.0 cells, isolated dropped
(--nb-tol)*. Per level, with a correspondence = the by_distance n summed (equal to the json's
`with_correspondence`); right peaks = that × (1 − wrong fraction); kept = what-if over standard:

`class_coverage_full`:

| what-if | level | judged cells std → w | with a correspondence std → w | wrong peaks % std → w | cut | right peaks w / std | kept |
|---|---|---|---|---|---|---|---|
| `nb1` | 0 | 4736 → 4166 | 4449 → 3928 | 26.07 → 17.62 | 32.4% ✗ | 3236 / 3289 | 98.4% ✓ ✗ |
| `nb1` | 1 | 18340 → 16482 | 17368 → 15596 | 22.74 → 15.38 | 32.4% ✗ | 13197 / 13418 | 98.4% ✓ ✗ |
| `nb1` | 2 | 42525 → 40198 | 40707 → 38448 | 16.33 → 12.55 | 23.2% ✗ | 33624 / 34059 | 98.7% ✓ ✗ |
| `nb1` | 3 | 65854 → 64248 | 62946 → 61383 | 10.75 → 9.03 | 16.1% ✗ | 55843 / 56177 | 99.4% ✓ |
| `nb1` | 4 | 44329 → 43743 | 41719 → 41194 | 5.05 → 4.08 | 19.3% ✗ | 39515 / 39613 | 99.8% ✓ |
| `nb1i` | 0 | 4736 → 4115 | 4449 → 3877 | 26.07 → 16.87 | 35.3% ✓ | 3223 / 3289 | 98.0% ✓ ✓ |
| `nb1i` | 1 | 18340 → 16422 | 17368 → 15537 | 22.74 → 15.22 | 33.1% ✗ | 13173 / 13418 | 98.2% ✓ ✗ |
| `nb1i` | 2 | 42525 → 40143 | 40707 → 38393 | 16.33 → 12.50 | 23.4% ✗ | 33593 / 34059 | 98.6% ✓ ✗ |
| `nb1i` | 3 | 65854 → 64220 | 62946 → 61355 | 10.75 → 9.03 | 16.1% ✗ | 55817 / 56177 | 99.4% ✓ |
| `nb1i` | 4 | 44329 → 43711 | 41719 → 41163 | 5.05 → 4.05 | 19.7% ✗ | 39494 / 39613 | 99.7% ✓ |

```
std : [diag] by area (the loop's count):  41.5% of the judged area is wrong or beyond 25%; of that, occluded   9.2%  window  11.3%  search   4.9%  resolution  74.6%  | outside the model (occluded + window + search)  10.5% of 162647 deg2 judged
nb1 : [diag] by area (the loop's count):  40.6% of the judged area is wrong or beyond 25%; of that, occluded   9.3%  window  10.8%  search   2.6%  resolution  77.3%  | outside the model (occluded + window + search)   9.2% of 159677 deg2 judged
nb1i: [diag] by area (the loop's count):  40.6% of the judged area is wrong or beyond 25%; of that, occluded   9.3%  window  10.8%  search   2.6%  resolution  77.3%  | outside the model (occluded + window + search)   9.2% of 159565 deg2 judged
      [diag] (y1) rebuilt field = the record on 96.740% of 213541 rows — a what-if (--tag): not judged
      [diag] (y1) rebuilt field = the record on 96.634% of 213541 rows — a what-if (--tag): not judged
```

`calib_room_full_sp`:

| what-if | level | judged cells std → w | with a correspondence std → w | wrong peaks % std → w | cut | right peaks w / std | kept |
|---|---|---|---|---|---|---|---|
| `nb1` | 0 | 46919 → 45898 | 45777 → 44819 | 8.51 → 7.16 | 15.9% ✗ | 41612 / 41883 | 99.4% ✓ ✗ |
| `nb1` | 1 | 74500 → 68523 | 70131 → 64481 | 23.08 → 19.28 | 16.5% ✗ | 52049 / 53947 | 96.5% ✓ ✗ |
| `nb1` | 2 | 117678 → 110454 | 111856 → 104774 | 17.65 → 14.64 | 17.1% ✗ | 89440 / 92118 | 97.1% ✓ ✗ |
| `nb1` | 3 | 137424 → 130998 | 132561 → 126155 | 17.43 → 15.32 | 12.1% ✗ | 106832 / 109458 | 97.6% ✓ |
| `nb1` | 4 | 59322 → 59028 | 57207 → 56942 | 1.67 → 1.30 | 22.5% ✗ | 56204 / 56250 | 99.9% ✓ |
| `nb1i` | 0 | 46919 → 45883 | 45777 → 44804 | 8.51 → 7.13 | 16.2% ✗ | 41609 / 41883 | 99.3% ✓ ✗ |
| `nb1i` | 1 | 74500 → 68516 | 70131 → 64474 | 23.08 → 19.28 | 16.5% ✗ | 52044 / 53947 | 96.5% ✓ ✗ |
| `nb1i` | 2 | 117678 → 110445 | 111856 → 104765 | 17.65 → 14.63 | 17.1% ✗ | 89433 / 92118 | 97.1% ✓ ✗ |
| `nb1i` | 3 | 137424 → 130994 | 132561 → 126151 | 17.43 → 15.32 | 12.1% ✗ | 106828 / 109458 | 97.6% ✓ |
| `nb1i` | 4 | 59322 → 59028 | 57207 → 56942 | 1.67 → 1.30 | 22.5% ✗ | 56204 / 56250 | 99.9% ✓ |

```
std : [diag] by area (the loop's count):  48.6% of the judged area is wrong or beyond 25%; of that, occluded   6.5%  window  10.8%  search   5.7%  resolution  76.9%  | outside the model (occluded + window + search)  11.2% of 261183 deg2 judged
nb1 : [diag] by area (the loop's count):  48.0% of the judged area is wrong or beyond 25%; of that, occluded   6.7%  window  10.1%  search   4.0%  resolution  79.3%  | outside the model (occluded + window + search)   9.9% of 254934 deg2 judged
nb1i: [diag] by area (the loop's count):  48.0% of the judged area is wrong or beyond 25%; of that, occluded   6.7%  window  10.1%  search   4.0%  resolution  79.3%  | outside the model (occluded + window + search)   9.9% of 254930 deg2 judged
      [diag] (y1) per-level gross after LR vs field.json: worst difference 0.0380 — a what-if (--tag): not judged
      [diag] (y1) per-level gross after LR vs field.json: worst difference 0.0380 — a what-if (--tag): not judged
```

**The offline rule on `class_coverage_full`: not met by `nb1`, not met by `nb1i`.** The keep
clause holds everywhere (98.0–98.7% of the right peaks at levels 0–2: the test is nearly free
in right peaks). The cut clause fails: `nb1` cuts the wrong-peak fraction by 32.4 / 32.4 /
23.2% at levels 0 / 1 / 2, each under a third; `nb1i` by 35.3 / 33.1 / 23.4% — level 0 passes,
level 1 misses by 0.2 points (15.22 against 22.74%, ratio 0.669), level 2 by 10. Dropping the
isolated changes almost nothing because there are almost none (below). At one cell of
tolerance the test removes a quarter to a third of the wrong peaks and one in fifty right
ones; the loop is not run, and D2 closes as the rule said it would: at one look, the field's
outliers cannot be told from the matcher's own evidence. What remains is D4.

### The five predictions against the runs

1. **`neighbours` the best single feature on `class_coverage_full` at every level, 45–65% at
   levels 0–2, search above window — held, with level 2 under the range.** At 90% kept it
   rejects 49.0 / 50.4 / 43.6 / 40.0 / 52.7% at levels 0–4, above the runner-up at every
   level (parent 33.9 / 44.5 / 39.7 / 37.3%, LR residual 32.2% at level 4); level 2's 43.6% is
   1.4 points under the predicted range. Search 62.1 / 63.7 / 81.4% against window 28.2 /
   30.3 / 21.6% at levels 0–2. AUC 0.72 / 0.75 / 0.71 / 0.70 / 0.78. On the calib room it is
   the best only at levels 2 and 4 (43.8%, 75.8%); the bound leads at level 0 (52.6%), the
   parent at 1 and 3.
2. **Isolated 10–35% of the right peaks at level 0, and wronger — failed on the amount, held
   on the direction.** Isolated cells are 0.4% of the right and 3.3% of the wrong at level 0
   on the classroom (0.2 / 0.9% at level 1, 0.1 / 0.4% at level 2); 0.0% on the calib room.
   Eight times wronger, but a hundredth of the predicted share — which is why `nb1i` is `nb1`
   to within 0.7 points.
3. **`combined` adds 5–15 points over the best single feature, AUC 0.75–0.85 on the odd
   pairs — held at levels 1–2, failed at 0, 3, 4.** Classroom: +5.6 (56.0 against 50.4, AUC
   0.76) at level 1 and +8.4 (52.0 against 43.6, AUC 0.79) at level 2; −9.1 at level 0 (39.9
   against 49.0, AUC 0.72; 1160 wrong peaks split by parity), +1.4 at level 3 (AUC 0.77), −0.1
   at level 4 (AUC 0.78). Calib room: +0.1 / −9.1 / −0.6 / +10.6 / +12.5, AUC 0.85 / 0.71 /
   0.79 / 0.83 / 0.96. The single features are judged on all pairs and `combined` on the odd
   ones only, so the differences carry that split's noise.
4. **`nb1` halves the wrong peaks at levels 0–2 for under 15% of the cells, outside-the-model
   area 10.5 → 6–8%, the offline rule met — failed.** Wrong peaks 26.1 → 17.6, 22.7 → 15.4,
   16.3 → 12.5% (cuts of 32 / 32 / 23%, not half); judged cells lost 12.0 / 10.1 / 5.5% (that
   clause held); outside the model 10.5 → 9.2% of the judged area (the bad area 41.5 → 40.6%,
   search's share of it 4.9 → 2.6%); the rule not met.
5. **The window kind survives (under 35% of its wrong peaks rejected at levels 0–1) — held.**
   By the what-if's kind counts on the classroom, `nb1` removes 18% of the window cells at
   level 0 (435 → 358) and 17% at level 1 (1556 → 1287), against 54% and 54% of the
   search cells (725 → 334, 2394 → 1112); at 90% kept the feature's window column reads 28.2 /
   30.3%. After the test, occluded + window are 8.2% of the judged area out of the 9.2% outside
   the model (standard: 8.5 of 10.5%) — not half of today's outside-the-model area but nine
   tenths of what is left, since the test takes mostly the search kind.
