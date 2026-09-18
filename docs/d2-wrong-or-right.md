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

Run 2026-09-18 on the workstation, host side (`.venv`), nothing rendered, no loop re-run. The
four self-tests ok. The run directories are as the note guessed (`previews/loop2/calib_*`,
`previews/loop3/class_*`, `class_*_full`); no command changed.

**The judge.** The three comparison calls exit 0 with 0 failures; (s) replay ok on all thirteen
runs, no (t)/(u)/(v) FAIL line. `compare.json` before and after (C3b's copies saved first): no
scalar changed on any run — coverage, medians, gross, z, vergence, the (u) pairs — and four
keys were added (`coarse_frac`, `outlier_frac`, `outlier_by_band`, `gross_by_band`).
gross − coarse − outlier is at most 8e-17 on every run, and per band. Wall: 47.1 s
(`class_compare_full`), 16.8 s (`class_compare`), 23.3 s (`calib_compare`). The thirteen lines:

```
[eval] class_random_full      random   k  50 rays 1.287e+09 | cover any 0.924 fine 0.078 | rho err med 0.0385 (fine 0.0155) /m | depth med 0.325 (fine 0.104) m | gross 0.314 = coarse 0.216 + outlier 0.098 (outlier fine/mid/coarse 0.194/0.144/0.060; gross 0.199/0.211/0.383) | z 1.02 | verg err med 0.33 m | (s) replay ok; (u) fixation-0 cells 27427: rho err median 0.0397 -> 0.0190 -> loop_fig.png
[eval] class_coverage_full    coverage k  50 rays 1.287e+09 | cover any 0.930 fine 0.094 | rho err med 0.0427 (fine 0.0177) /m | depth med 0.351 (fine 0.134) m | gross 0.344 = coarse 0.240 + outlier 0.104 (outlier fine/mid/coarse 0.219/0.154/0.058; gross 0.227/0.225/0.425) | z 1.01 | verg err med 0.38 m | (s) replay ok; (u) fixation-0 cells 27427: rho err median 0.0397 -> 0.0180 -> loop_fig.png
[eval] class_info_full        info     k  50 rays 1.287e+09 | cover any 0.920 fine 0.059 | rho err med 0.0435 (fine 0.0186) /m | depth med 0.375 (fine 0.140) m | gross 0.355 = coarse 0.257 + outlier 0.098 (outlier fine/mid/coarse 0.255/0.148/0.058; gross 0.267/0.220/0.427) | z 0.85 | verg err med 0.71 m | (s) replay ok; (u) fixation-0 cells 27427: rho err median 0.0397 -> 0.0195 -> loop_fig.png
[eval] class_oracle_full      oracle   k  50 rays 1.287e+09 | cover any 0.868 fine 0.064 | rho err med 0.0453 (fine 0.0139) /m | depth med 0.438 (fine 0.231) m | gross 0.374 = coarse 0.272 + outlier 0.101 (outlier fine/mid/coarse 0.268/0.149/0.064; gross 0.284/0.231/0.427) | z 0.74 | verg err med 0.61 m | (s) replay ok; (u) fixation-0 cells 27427: rho err median 0.0397 -> 0.0183 -> loop_fig.png
[eval] class_random           random   k  50 rays 7.995e+07 | cover any 0.884 fine 0.054 | rho err med 0.0808 (fine 0.0416) /m | depth med 0.626 (fine 0.292) m | gross 0.492 = coarse 0.410 + outlier 0.082 (outlier fine/mid/coarse 0.282/0.151/0.031; gross 0.334/0.420/0.539) | z 0.64 | verg err med 0.38 m | (s) replay ok; (u) fixation-0 cells 5627: rho err median 0.0799 -> 0.0417 -> loop_fig.png
[eval] class_coverage         coverage k  50 rays 7.995e+07 | cover any 0.867 fine 0.066 | rho err med 0.0852 (fine 0.0534) /m | depth med 0.706 (fine 0.387) m | gross 0.521 = coarse 0.440 + outlier 0.081 (outlier fine/mid/coarse 0.274/0.138/0.027; gross 0.396/0.450/0.573) | z 0.62 | verg err med 0.77 m | (s) replay ok; (u) fixation-0 cells 5627: rho err median 0.0799 -> 0.0412 -> loop_fig.png
[eval] class_info             info     k  50 rays 7.995e+07 | cover any 0.868 fine 0.044 | rho err med 0.1006 (fine 0.0476) /m | depth med 0.756 (fine 0.501) m | gross 0.552 = coarse 0.473 + outlier 0.079 (outlier fine/mid/coarse 0.252/0.176/0.029; gross 0.382/0.472/0.595) | z 0.63 | verg err med 0.58 m | (s) replay ok; (u) fixation-0 cells 5627: rho err median 0.0799 -> 0.0535 -> loop_fig.png
[eval] class_oracle           oracle   k  50 rays 7.995e+07 | cover any 0.835 fine 0.046 | rho err med 0.0940 (fine 0.0789) /m | depth med 0.816 (fine 0.459) m | gross 0.548 = coarse 0.456 + outlier 0.092 (outlier fine/mid/coarse 0.377/0.162/0.028; gross 0.467/0.485/0.583) | z 0.69 | verg err med 0.64 m | (s) replay ok; (u) fixation-0 cells 5627: rho err median 0.0799 -> 0.0511 -> loop_fig.png
[eval] calib_targets          targets  k  50 rays 7.995e+07 | cover any 0.993 fine 0.201 | rho err med 0.1397 (fine 0.0149) /m | depth med 1.128 (fine 0.059) m | gross 0.609 = coarse 0.419 + outlier 0.190 (outlier fine/mid/coarse 0.275/0.320/0.002; gross 0.285/0.683/0.763) | z 0.57 | verg err med 0.01 m | (s) replay ok; (u) fixation-0 cells 10820: rho err median 0.2160 -> 0.2081 -> loop_fig.png
[eval] calib_random           random   k  50 rays 7.995e+07 | cover any 0.996 fine 0.116 | rho err med 0.1111 (fine 0.0253) /m | depth med 0.864 (fine 0.153) m | gross 0.555 = coarse 0.423 + outlier 0.132 (outlier fine/mid/coarse 0.269/0.229/0.000; gross 0.326/0.487/0.688) | z 0.51 | verg err med 0.39 m | (s) replay ok; (u) fixation-0 cells 10820: rho err median 0.2160 -> 0.2045 -> loop_fig.png
[eval] calib_coverage         coverage k  50 rays 7.995e+07 | cover any 0.994 fine 0.138 | rho err med 0.1052 (fine 0.0249) /m | depth med 0.836 (fine 0.127) m | gross 0.557 = coarse 0.415 + outlier 0.142 (outlier fine/mid/coarse 0.247/0.231/0.001; gross 0.319/0.511/0.697) | z 0.49 | verg err med 0.51 m | (s) replay ok; (u) fixation-0 cells 10820: rho err median 0.2160 -> 0.2155 -> loop_fig.png
[eval] calib_info             info     k  50 rays 7.995e+07 | cover any 0.999 fine 0.080 | rho err med 0.1027 (fine 0.0321) /m | depth med 0.769 (fine 0.331) m | gross 0.539 = coarse 0.416 + outlier 0.122 (outlier fine/mid/coarse 0.240/0.221/0.001; gross 0.335/0.463/0.654) | z 0.45 | verg err med 0.59 m | (s) replay ok; (u) fixation-0 cells 10820: rho err median 0.2160 -> 0.2118 -> loop_fig.png
[eval] calib_oracle           oracle   k  50 rays 7.995e+07 | cover any 0.993 fine 0.074 | rho err med 0.1462 (fine 0.0882) /m | depth med 1.201 (fine 0.789) m | gross 0.628 = coarse 0.464 + outlier 0.164 (outlier fine/mid/coarse 0.473/0.304/0.001; gross 0.516/0.567/0.694) | z 0.50 | verg err med 2.66 m | (s) replay ok; (u) fixation-0 cells 10820: rho err median 0.2160 -> 0.2009 -> loop_fig.png
```

Outlier fraction, all cells: classroom `full` 0.098–0.104 (gross 0.314–0.374), classroom `small`
0.079–0.092 (gross 0.49–0.55), calib room 0.122–0.190 (gross 0.54–0.63). By band on the
classroom at `full`, outlier / gross: fine 0.194–0.268 / 0.199–0.284, mid 0.144–0.154 /
0.211–0.231, coarse 0.058–0.064 / 0.383–0.427. The fine band's gross *is* its outlier fraction
(the belief's σ there does not cover the wrong peaks); the coarse band's gross is 85% coarse.
D21's "overturned if" (outlier near gross) does not fire: 0.10 against 0.31–0.37.

**The features.** The four standard diagnoses exit 0, (y1) 0.0000 / 0.0000 / 100.000% of
46692 rows / 99.999% of 213541 rows, (y2) ok; wall 4.8 / 15.7 / 6.1 / 20.9 s. **The five level
lines of each run equal D1a's Results exactly** (string comparison after removing the new
"wrong peaks … of the cells with a correspondence" segment; the right-peaks, oracle and area
lines are unchanged too). The loop runs print the RuntimeWarnings from
`stereo_instrument.py:244–262` known from D1a. `calib_room_sp` has no "telling" line at level
4: 30 wrong peaks, under the 50 the tool requires. The new lines, per run:

`calib_room_sp`:

```
[diag] level 0 wrong peaks under the oracle: cured   6.2%  no parent  16.0%  parent wrong too  63.5%  inside the interval  14.3%
[diag] level 1 wrong peaks under the oracle: cured   2.5%  no parent   0.7%  parent wrong too  52.8%  inside the interval  44.0%
[diag] level 2 wrong peaks under the oracle: cured   4.2%  no parent   0.4%  parent wrong too   0.3%  inside the interval  95.1%
[diag] level 3 wrong peaks under the oracle: cured   0.7%  no parent   2.0%  parent wrong too   0.0%  inside the interval  97.4%
[diag] level 4 wrong peaks under the oracle: cured   0.0%  no parent 100.0%  parent wrong too   0.0%  inside the interval   0.0%
[diag] level 0 telling wrong from right at 90% of the right kept (1031 wrong, 10107 right) — rejects all / window / search, AUC: peak  13.1/ 12.7/ 15.9% 0.47; margin  47.2/ 41.8/ 91.2% 0.73; lr_resid  33.9/ 30.8/ 58.4% 0.69; bound  68.4/ 67.2/ 77.9% 0.86; parent  33.3/ 31.2/ 50.4% 0.64
[diag] level 1 telling wrong from right at 90% of the right kept (4515 wrong, 13063 right) — rejects all / window / search, AUC: peak  30.4/ 30.2/ 35.2% 0.67; margin  31.2/ 29.9/ 52.9% 0.73; lr_resid  19.3/ 17.6/ 49.2% 0.65; bound  19.5/ 17.8/ 48.8% 0.69; parent  31.5/ 28.4/ 85.2% 0.69
[diag] level 2 telling wrong from right at 90% of the right kept (4570 wrong, 23121 right) — rejects all / window / search, AUC: peak  19.5/ 19.2/ 28.9% 0.65; margin  18.2/ 17.0/ 61.7% 0.65; lr_resid  32.3/ 32.2/ 38.3% 0.69; bound   8.5/  8.2/ 17.2% 0.44; parent   7.0/  5.3/ 63.3% 0.49
[diag] level 3 telling wrong from right at 90% of the right kept (152 wrong, 32462 right) — rejects all / window / search, AUC: peak  13.8/ 11.2/ 55.6% 0.62; margin  40.8/ 39.2/ 66.7% 0.77; lr_resid  45.4/ 43.4/ 77.8% 0.73; bound  48.0/ 46.2/ 77.8% 0.83; parent  73.7/ 72.0/100.0% 0.90
```

`calib_room_full_sp`:

```
[diag] level 0 wrong peaks under the oracle: cured   5.7%  no parent  10.6%  parent wrong too  73.2%  inside the interval  10.5%
[diag] level 1 wrong peaks under the oracle: cured  15.8%  no parent  11.1%  parent wrong too  53.9%  inside the interval  19.2%
[diag] level 2 wrong peaks under the oracle: cured  14.1%  no parent   4.8%  parent wrong too  49.0%  inside the interval  32.1%
[diag] level 3 wrong peaks under the oracle: cured  33.0%  no parent   0.4%  parent wrong too   0.4%  inside the interval  66.2%
[diag] level 4 wrong peaks under the oracle: cured   0.0%  no parent 100.0%  parent wrong too   0.0%  inside the interval   0.0%
[diag] level 0 telling wrong from right at 90% of the right kept (3894 wrong, 41883 right) — rejects all / window / search, AUC: peak  14.8/ 16.6/  5.1% 0.43; margin  44.6/ 35.6/ 92.8% 0.72; lr_resid  35.9/ 29.8/ 69.0% 0.69; bound  52.6/ 48.0/ 77.7% 0.85; parent  30.1/ 20.4/ 82.0% 0.58
[diag] level 1 telling wrong from right at 90% of the right kept (16184 wrong, 53947 right) — rejects all / window / search, AUC: peak  14.8/ 18.1/  6.0% 0.51; margin  33.7/ 19.5/ 72.7% 0.68; lr_resid  22.6/ 16.7/ 38.9% 0.67; bound  25.3/ 13.1/ 58.7% 0.70; parent  43.2/ 34.2/ 67.9% 0.70
[diag] level 2 telling wrong from right at 90% of the right kept (19738 wrong, 92118 right) — rejects all / window / search, AUC: peak  23.7/ 28.6/  7.7% 0.65; margin  19.7/  9.0/ 54.8% 0.67; lr_resid  28.7/ 33.7/ 12.5% 0.70; bound   6.1/  4.6/ 10.7% 0.42; parent  17.3/  6.7/ 51.8% 0.61
[diag] level 3 telling wrong from right at 90% of the right kept (23103 wrong, 109458 right) — rejects all / window / search, AUC: peak   9.5/  8.5/ 11.8% 0.58; margin  23.4/ 15.3/ 41.3% 0.72; lr_resid  18.9/ 20.7/ 14.9% 0.66; bound   5.5/  4.5/  7.6% 0.40; parent  36.9/ 10.6/ 94.9% 0.62
[diag] level 4 telling wrong from right at 90% of the right kept (957 wrong, 56250 right) — rejects all / window / search, AUC: peak  23.6/ 31.9/ 20.5% 0.72; margin  33.8/ 30.0/ 35.2% 0.69; lr_resid  49.9/ 55.1/ 48.0% 0.79; bound  72.5/ 45.6/ 82.7% 0.91; parent   0.0/  0.0/  0.0% 0.50
```

`class_coverage` (classroom, `small`):

```
[diag] level 0 wrong peaks under the oracle: cured  11.8%  no parent  46.6%  parent wrong too  36.6%  inside the interval   5.0%
[diag] level 1 wrong peaks under the oracle: cured  16.8%  no parent  28.5%  parent wrong too  24.6%  inside the interval  30.0%
[diag] level 2 wrong peaks under the oracle: cured  11.4%  no parent  15.3%  parent wrong too  18.0%  inside the interval  55.2%
[diag] level 3 wrong peaks under the oracle: cured  11.5%  no parent   1.1%  parent wrong too   7.3%  inside the interval  80.1%
[diag] level 4 wrong peaks under the oracle: cured   0.0%  no parent 100.0%  parent wrong too   0.0%  inside the interval   0.0%
[diag] level 0 telling wrong from right at 90% of the right kept (238 wrong, 237 right) — rejects all / window / search, AUC: peak  14.3/  8.5/ 17.3% 0.48; margin  34.0/  9.8/ 46.8% 0.73; lr_resid  12.2/  8.5/ 14.1% 0.53; bound  25.6/ 19.5/ 28.8% 0.65; parent  38.2/ 29.3/ 42.9% 0.59
[diag] level 1 telling wrong from right at 90% of the right kept (743 wrong, 2223 right) — rejects all / window / search, AUC: peak  14.3/  7.3/ 23.4% 0.48; margin  31.4/ 10.7/ 58.6% 0.68; lr_resid  15.7/ 12.6/ 19.9% 0.59; bound  23.1/ 12.1/ 37.7% 0.59; parent  36.6/ 25.1/ 51.7% 0.59
[diag] level 2 telling wrong from right at 90% of the right kept (1347 wrong, 6629 right) — rejects all / window / search, AUC: peak  15.1/ 17.9/  6.9% 0.57; margin  26.9/ 13.7/ 66.9% 0.61; lr_resid  27.6/ 21.2/ 46.9% 0.66; bound  20.0/ 10.3/ 49.6% 0.54; parent  37.9/ 29.6/ 62.7% 0.70
[diag] level 3 telling wrong from right at 90% of the right kept (990 wrong, 12424 right) — rejects all / window / search, AUC: peak  16.1/ 17.2/ 12.2% 0.59; margin  27.3/ 13.0/ 74.7% 0.62; lr_resid  28.6/ 22.5/ 48.9% 0.66; bound  16.8/  7.0/ 49.3% 0.50; parent  52.0/ 41.1/ 88.2% 0.79
[diag] level 4 telling wrong from right at 90% of the right kept (192 wrong, 9728 right) — rejects all / window / search, AUC: peak  17.7/ 21.0/ 11.8% 0.60; margin  32.3/ 12.9/ 67.6% 0.62; lr_resid  37.0/ 27.4/ 54.4% 0.71; bound  33.3/ 15.3/ 66.2% 0.54; parent   0.0/  0.0/  0.0% 0.50
```

`class_coverage_full` (classroom, `full`):

```
[diag] level 0 wrong peaks under the oracle: cured  15.8%  no parent  33.2%  parent wrong too  36.5%  inside the interval  14.6%
[diag] level 1 wrong peaks under the oracle: cured  25.2%  no parent  22.7%  parent wrong too  31.5%  inside the interval  20.6%
[diag] level 2 wrong peaks under the oracle: cured  16.5%  no parent  14.7%  parent wrong too  35.8%  inside the interval  33.0%
[diag] level 3 wrong peaks under the oracle: cured  11.4%  no parent   5.6%  parent wrong too  22.3%  inside the interval  60.8%
[diag] level 4 wrong peaks under the oracle: cured   0.0%  no parent 100.0%  parent wrong too   0.0%  inside the interval   0.0%
[diag] level 0 telling wrong from right at 90% of the right kept (1160 wrong, 3289 right) — rejects all / window / search, AUC: peak  11.4/  7.1/ 13.9% 0.45; margin  31.5/ 18.6/ 39.2% 0.71; lr_resid  13.1/ 15.6/ 11.6% 0.57; bound  18.0/ 11.3/ 22.1% 0.54; parent  33.9/ 24.4/ 39.6% 0.56
[diag] level 1 telling wrong from right at 90% of the right kept (3950 wrong, 13418 right) — rejects all / window / search, AUC: peak  14.4/ 10.3/ 17.0% 0.46; margin  34.4/ 15.0/ 47.0% 0.70; lr_resid  20.1/ 19.8/ 20.3% 0.63; bound  21.5/  8.6/ 29.9% 0.55; parent  44.5/ 27.7/ 55.3% 0.64
[diag] level 2 telling wrong from right at 90% of the right kept (6648 wrong, 34059 right) — rejects all / window / search, AUC: peak  15.8/ 14.8/ 17.5% 0.51; margin  28.4/ 12.9/ 54.7% 0.64; lr_resid  26.7/ 16.1/ 44.7% 0.64; bound  21.3/  7.7/ 44.5% 0.51; parent  39.7/ 25.6/ 63.6% 0.67
[diag] level 3 telling wrong from right at 90% of the right kept (6769 wrong, 56177 right) — rejects all / window / search, AUC: peak  17.3/ 18.0/ 14.5% 0.55; margin  24.8/ 13.4/ 70.8% 0.59; lr_resid  25.7/ 18.0/ 56.6% 0.64; bound  17.2/  5.7/ 63.1% 0.44; parent  37.3/ 26.2/ 81.9% 0.70
[diag] level 4 telling wrong from right at 90% of the right kept (2106 wrong, 39613 right) — rejects all / window / search, AUC: peak  19.4/ 18.4/ 21.2% 0.62; margin  23.7/ 11.2/ 46.1% 0.63; lr_resid  32.2/ 22.9/ 48.9% 0.69; bound  27.9/  3.5/ 71.5% 0.53; parent   0.0/  0.0/  0.0% 0.50
```

**The 3 × 3 window, as a what-if.** Both exit 0 with (y1) "not judged" (`calib_room_full_sp`
worst difference 0.0244; `class_coverage_full` rebuilt = record on 0.089% of 213539 rows); the
standard `gross_diagnosis.json` files kept their mtime; `gross_diagnosis_w1.{json,png}` written
beside them. Wall 10.3 s and 15.5 s. Per level, 5 × 5 (standard) against 3 × 3 (`w1`); "near"
is within 2 cells for the standard and 1 cell for `w1`, so the wrong-peak column is the
comparable one:

| run | level | judged cells std / w1 | wrong peaks % std / w1 | P(wrong) near std / w1 | P(wrong) far std / w1 |
|---|---|---|---|---|---|
| `class_coverage_full` | 0 | 4736 / 1557 | 26.1 / 45.7 | 40.1 / 47.5 | 21.5 / 45.2 |
| | 1 | 18340 / 8334 | 22.7 / 38.4 | 37.9 / 47.8 | 18.1 / 36.0 |
| | 2 | 42525 / 22200 | 16.3 / 24.0 | 33.2 / 37.1 | 8.7 / 18.6 |
| | 3 | 65854 / 38312 | 10.8 / 14.9 | 20.9 / 24.3 | 3.6 / 9.4 |
| | 4 | 44329 / 31726 | 5.0 / 7.5 | 7.6 / 9.6 | 3.1 / 6.2 |
| `calib_room_full_sp` | 0 | 46919 / 35882 | 8.5 / 9.2 | 34.1 / 36.9 | 1.7 / 5.0 |
| | 1 | 74500 / 49187 | 23.1 / 23.1 | 41.2 / 44.1 | 10.5 / 13.3 |
| | 2 | 117678 / 86650 | 17.6 / 19.2 | 29.3 / 31.8 | 7.7 / 12.2 |
| | 3 | 137424 / 115312 | 17.4 / 18.5 | 21.1 / 18.9 | 12.6 / 18.2 |
| | 4 | 59322 / 52123 | 1.7 / 4.1 | 0.8 / 2.6 | 3.1 / 5.5 |

The `w1` level lines verbatim:

```
[diag] level 0 cell 0.10 deg,    1557 cells: occluded   4.6%  window   9.6%  search  33.5%  resolution   0.0%  good  52.2%  | wrong peaks  45.7% of the cells with a correspondence; near an edge  21.5% of cells; P(wrong) near  47.5% far  45.2% (excess share of near-edge wrong peaks   4.9%); P(beyond 25%) near  37.0% far  36.8%
[diag] level 1 cell 0.20 deg,    8334 cells: occluded   4.7%  window   9.1%  search  27.0%  resolution   0.5%  good  58.8%  | wrong peaks  38.4% of the cells with a correspondence; near an edge  20.3% of cells; P(wrong) near  47.8% far  36.0% (excess share of near-edge wrong peaks  24.8%); P(beyond 25%) near  40.9% far  32.6%
[diag] level 2 cell 0.40 deg,   22200 cells: occluded   3.7%  window  10.2%  search  12.5%  resolution   7.7%  good  65.8%  | wrong peaks  24.0% of the cells with a correspondence; near an edge  29.0% of cells; P(wrong) near  37.1% far  18.6% (excess share of near-edge wrong peaks  49.9%); P(beyond 25%) near  43.5% far  24.5%
[diag] level 3 cell 0.80 deg,   38312 cells: occluded   3.8%  window   8.6%  search   5.6%  resolution  22.9%  good  59.1%  | wrong peaks  14.9% of the cells with a correspondence; near an edge  37.1% of cells; P(wrong) near  24.3% far   9.4% (excess share of near-edge wrong peaks  61.3%); P(beyond 25%) near  50.3% far  32.2%
[diag] level 4 cell 1.60 deg,   31726 cells: occluded   4.9%  window   3.4%  search   3.6%  resolution  42.0%  good  46.1%  | wrong peaks   7.5% of the cells with a correspondence; near an edge  37.4% of cells; P(wrong) near   9.6% far   6.2% (excess share of near-edge wrong peaks  35.5%); P(beyond 25%) near  61.7% far  46.9%
[diag] by area (the loop's count):  50.3% of the judged area is wrong or beyond 25%; of that, occluded   9.1%  window   9.5%  search   8.8%  resolution  72.5%
[diag] (y1) rebuilt field = the record on 0.089% of 213539 rows — a what-if (--tag): not judged
[diag] level 0 cell 0.10 deg,   35882 cells: occluded   1.4%  window   4.8%  search   4.2%  resolution   0.2%  good  89.4%  | wrong peaks   9.2% of the cells with a correspondence; near an edge  13.1% of cells; P(wrong) near  36.9% far   5.0% (excess share of near-edge wrong peaks  86.5%); P(beyond 25%) near  36.3% far   3.5%
[diag] level 1 cell 0.20 deg,   49187 cells: occluded   5.0%  window  13.3%  search   8.6%  resolution   2.3%  good  70.8%  | wrong peaks  23.1% of the cells with a correspondence; near an edge  31.9% of cells; P(wrong) near  44.1% far  13.3% (excess share of near-edge wrong peaks  69.8%); P(beyond 25%) near  44.0% far  14.7%
[diag] level 2 cell 0.40 deg,   86650 cells: occluded   4.8%  window  10.7%  search   7.4%  resolution  12.7%  good  64.3%  | wrong peaks  19.2% of the cells with a correspondence; near an edge  35.6% of cells; P(wrong) near  31.8% far  12.2% (excess share of near-edge wrong peaks  61.6%); P(beyond 25%) near  48.5% far  23.6%
[diag] level 3 cell 0.80 deg,  115312 cells: occluded   3.5%  window   8.1%  search   9.7%  resolution  26.2%  good  52.6%  | wrong peaks  18.5% of the cells with a correspondence; near an edge  44.4% of cells; P(wrong) near  18.9% far  18.2% (excess share of near-edge wrong peaks   3.7%); P(beyond 25%) near  52.1% far  40.7%
[diag] level 4 cell 1.60 deg,   52123 cells: occluded   3.1%  window   1.2%  search   2.8%  resolution  55.5%  good  37.4%  | wrong peaks   4.1% of the cells with a correspondence; near an edge  47.5% of cells; P(wrong) near   2.6% far   5.5% (excess share of near-edge wrong peaks   0.0%); P(beyond 25%) near  67.7% far  56.2%
[diag] by area (the loop's count):  55.5% of the judged area is wrong or beyond 25%; of that, occluded   6.1%  window   7.5%  search   9.7%  resolution  76.7%
[diag] (y1) per-level gross after LR vs field.json: worst difference 0.0244 — a what-if (--tag): not judged
```

By area the bad fraction rises from 41.5% to 50.3% on the classroom and from 48.6% to 55.5% on
the calib room.

### The four predictions against the runs

1. **Outlier 0.08–0.15 on the classroom at `full`, highest in the fine band, fine outlier ≈ fine
   gross — held.** Outlier 0.098 / 0.104 / 0.098 / 0.101 (random / coverage / info / oracle),
   gross 0.314–0.374; fine outlier 0.194 / 0.219 / 0.255 / 0.268 against fine gross 0.199 /
   0.227 / 0.267 / 0.284 (within 0.005–0.016), mid 0.144–0.154, coarse 0.058–0.064.
2. **No single feature is a test on the classroom's fine levels — held; peak's number failed
   low.** `class_coverage_full` at 90% kept, levels 0 / 1: peak rejects 11.4 / 14.4% (predicted
   30–50%; AUC 0.45 / 0.46, a coin), margin 31.5 / 34.4% (in range, AUC 0.71 / 0.70), bound
   18.0 / 21.5% (predicted under 20%: level 1 is over by 1.5 points). The best of the five is
   parent at 33.9 / 44.5%. Nothing reaches 60% at any of levels 0–2 on the classroom (the
   highest, parent at level 1, is 44.5%), and no AUC on the classroom's levels 0–2 is above
   0.71.
3. **The parent the best single feature, better on search than window; the uncured mostly
   inside the interval — held on the classroom, failed on the calib room at levels 0 and 2,
   and the reason given failed.** `class_coverage_full`, parent rejects 33.9 / 44.5 / 39.7 /
   37.3% of the wrong peaks at levels 0–3 (predicted 40–60%: level 0 under), the best of the
   five at every level with a parent; search 39.6 / 55.3 / 63.6 / 81.9% against window 24.4 /
   27.7 / 25.6 / 26.2%. `class_coverage` likewise (38.2 / 36.6 / 37.9 / 52.0%). On the calib
   room the bound is the best at level 0 (68.4% at `sp`, 52.6% at `full`; parent 33.3 / 30.1%)
   and the LR residual at level 2 (32.3 / 28.7%; parent 7.0 / 17.3%), parent best at levels 1
   and 3 (`full`: 43.2%, 36.9%). By AUC, margin beats parent at the classroom's levels 0–1
   (0.71 / 0.70 against 0.56 / 0.64). The uncured wrong peaks on `class_coverage_full` are
   *not* mostly inside the ±2-cell interval: inside 14.6 / 20.6 / 33.0 / 60.8% at levels 0–3,
   against parent-wrong-too 36.5 / 31.5 / 35.8 / 22.3% and no-parent 33.2 / 22.7 / 14.7 / 5.6%;
   the majority is inside only at level 3 (and at levels 2–3 of the calib runs: 95.1 / 97.4%
   at `sp`, 32.1 / 66.2% at `full`). The pyramid still rejects more than it cures (level 1:
   44.5% rejected at 90% kept against 25.2% cured), so "a test more than a prior" stands on
   the numbers, for a different reason than the stub gave.
4. **The 3 × 3 window loses on the classroom — held; and it loses on the calib room at level
   0 too.** `class_coverage_full`: judged cells 4736 → 1557 at level 0, wrong peaks 26.1 →
   45.7%, P(wrong) far 21.5 → 45.2%; at every level fewer cells and more wrong peaks near and
   far. `calib_room_full_sp` level 0: 46919 → 35882 cells, wrong peaks 8.5 → 9.2%, far 1.7 →
   5.0%; levels 1–4 likewise (level 1's wrong-peak fraction equal at 23.1%, with a third fewer
   cells). The window is not a per-scene knob: 3 × 3 loses on both scenes at every level.

**Against the D2b rule in "What the numbers decide"** (reported, not decided): no feature
rejects ≥ 60% at 90% kept on the classroom's levels 0–2 (best 44.5%); the AUCs there are
0.45–0.71, below the 0.75–0.85 the second option asks for; the window's share of the bad area
on `class_coverage_full` is 11.3% (D1a), search 4.9%, occluded 9.2%.
