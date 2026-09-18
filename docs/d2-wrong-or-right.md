# Step D2a — the judge split, and what tells a wrong peak from a right one

Written 2026-09-18 before the workstation run. Numbers are **predicted** or from the stub
until the log records a measurement. No rendering; the matcher's output does not change.

## What it is

Three things, all on saved records (D21).

**The judge.** `belief.metrics` now splits the gross fraction: *coarse* — beyond 25% in ρ but
within 3σ of the belief's own σ (a right peak at a coarse level: the model says it does not
know, and it does not) — and *outlier*, beyond both (what the model does not contain). coarse +
outlier = gross, exactly; also per band. `active_eval.py` prints the split from the replayed
belief, so the thirteen Phase C runs are re-judged without re-running. Control in
`belief.py --self-test`: honest coarse measurements with one cell in ten made a confident
wrong peak give outlier 0.10 and coarse ≈ 0.55 (the known answers).

**The features.** `field_of_pair(features=True)` (off in the loop; nothing else changes) adds
per cell the NCC peak, its rival (the best score more than a cell from the peak) and the LR
residual. `gross_diagnosis.py` reads five things a confidence test could read *without the
truth* — peak, margin (peak − rival), LR residual, bound in cells, disagreement with the
parent's parallax in cells — and per level and feature reports: the threshold that keeps 90%
of the right peaks, the share of the wrong peaks it rejects (all / window / search), the AUC.
10% rejected at 90% kept is a coin; 70% is a test. It also says why the oracle's uncured stay
uncured: no parent / parent wrong too / the wrong peak inside the ±2-cell interval.

**The 3 × 3 window, as a what-if.** `--window 1 --tag w1` rebuilds the fields with the small
window and writes `gross_diagnosis_w1.*` beside the standard files; (y1) is reported, not
judged. Compare per level: judged cells, wrong peaks % of the cells with a correspondence,
P(wrong) near and far. (The kinds shift because "near" is then one cell; the wrong-peak line
and the by-distance table are the comparable numbers.)

## Commands (workstation) — all host side

```bash
for t in belief stereo_instrument stereo_field gross_diagnosis; do .venv/bin/python tools/$t.py --self-test; done   # interactive
# the judge: re-judge the saved loop runs (ls previews/loop2 previews/loop3 for the names; the
# comparison calls are C2's and C3's, unchanged)                                                  # batch, seconds per run
.venv/bin/python tools/active_eval.py previews/loop3/class_random_full previews/loop3/class_coverage_full \
    previews/loop3/class_info_full previews/loop3/class_oracle_full --out previews/loop3/class_compare_full
.venv/bin/python tools/active_eval.py previews/loop3/class_random previews/loop3/class_coverage \
    previews/loop3/class_info previews/loop3/class_oracle --out previews/loop3/class_compare
.venv/bin/python tools/active_eval.py previews/loop2/calib_targets previews/loop2/calib_random \
    previews/loop2/calib_coverage previews/loop2/calib_info previews/loop2/calib_oracle --out previews/loop2/calib_compare
# the features: the four D1a records again (the standard run; (y1) and (y2) as before)              # interactive / batch < 1 min
for r in previews/pairs/calib_room_sp previews/pairs/calib_room_full_sp previews/loop3/class_coverage previews/loop3/class_coverage_full; do
  .venv/bin/python tools/gross_diagnosis.py $r
done
# the what-if                                                                                       # batch < 1 min
.venv/bin/python tools/gross_diagnosis.py previews/pairs/calib_room_full_sp --window 1 --tag w1
.venv/bin/python tools/gross_diagnosis.py previews/loop3/class_coverage_full --window 1 --tag w1
```

## Checks

(s)–(v) on the re-judged runs, unchanged (the split is additive: (s) still compares coverage
and the median error to 1e-9). (y1), (y2) on the four standard diagnoses; their D1a numbers
must reproduce exactly (the level lines of `docs/d1-gross-diagnosis.md`), since `features=True`
may not move a single row.

## Predictions, written before the run

1. **Outlier fraction on the classroom at `full`: 0.08–0.15** (gross 0.31–0.37), highest in the
   fine band, where there is no coarse kind to speak of (fine outlier ≈ fine gross, 0.20–0.28).
   Stub, measured: gross 0.359 = coarse 0.298 + outlier 0.061.
2. **No single feature is a test on the classroom's fine levels**: at 90% kept, peak and margin
   reject 30–50% of the wrong peaks at levels 0–1, the bound under 20%. (Stub: 40–50%, 4–6%.)
3. **The parent is the best single feature where there is one**, and better on search than on
   window (stub: 74–78% of all, 90% of search, 56–62% of window at levels 0–1) — the pyramid
   is worth more as a *test* than as a *prior*, because most uncured wrong peaks sit inside
   the ±2-cell interval (stub: 54–65% at levels 1–3). On the renders, where parents are rarer
   (75–81% of cells at levels 0–1) and wrong more often, predicted 40–60%.
4. **The 3 × 3 window loses on the classroom**: fewer judged cells and more wrong peaks far
   from edges than it removes near them (stub: wrong peaks 7% → 30% at level 0). On the calib
   room's cards, where levels 0–1 are the window's (excess share 75–95%), it may win at level 0;
   if it wins there and loses on the classroom, the window is a per-scene knob, not a fix.

## What the numbers decide

D2b is one of three, picked by these numbers and written with its rule before it runs: a
rejection test on the best feature (if one rejects ≥ 60% at 90% kept on the classroom's levels
0–2); π in the fusion from several (if none does but their AUCs are 0.75–0.85 and they
disagree with each other); the weighted window (if the window's share is what remains). Code
reports; Chat and Luiz decide.

## Results

_To be filled by Code: the `[eval]` line of each of the thirteen runs verbatim (they carry
gross = coarse + outlier and the bands); the four diagnoses' new lines (wrong peaks under the
oracle, telling wrong from right) verbatim, and a one-line confirmation that the level lines
equal D1a's; the two what-ifs' level lines beside the standard ones; the four predictions
marked held / failed with the number._
