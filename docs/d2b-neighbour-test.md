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

_To be filled by Code: for the two standard diagnoses the "telling wrong from right" lines
verbatim (now with neighbours, combined, isolated); for the four what-ifs, per level: judged
cells, wrong peaks %, right peaks kept %, and the area line verbatim, beside the standard ones;
the offline rule's verdict with its numbers; if the loop ran: both [eval] lines verbatim, the
loop rule's verdict, infer seconds per fixation (median) against C3b's 0.46, the nb run's
diagnosis area line and (y1); the five predictions held / failed with the number._
