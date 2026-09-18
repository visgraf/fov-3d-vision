# Step D1a — the diagnosis: where the gross errors come from

Written 2026-09-18 before the workstation run. Numbers are **predicted**, from the stub, or
quoted from C1/C3 Results until the log records a measurement. No rendering, no matcher change.

## What it is

`tools/gross_diagnosis.py` rebuilds each saved pair's field with the settings the run used,
carries the truth sidecar through the same accumulation, and sorts every LR-consistent cell
(the ones the belief fuses) by what is wrong with it. The plan named three kinds — occluded,
near a depth edge, far from one. Writing the tool added a fourth, and it changes what D1's
number can mean, so it is said here before anything runs.

**The repository has two "gross" and they are not the same thing.** `stereo_field.py` calls a
cell gross when its parallax is off by more than one cell: a wrong peak. `belief.metrics`
calls a belief cell gross when ρ is off by more than 25% — the 0.344 in D20's decision rule.
A right peak can be beyond 25%: a coarse cell's inlier error is 0.3–0.4 cells, and 0.3 of a
1.6° cell is 0.5° where the parallax of a wall at 3 m is 1.2°. C1's own table says so (measured,
`calib_room_full_sp`): level 4 has 1.3% wrong peaks after LR and an inlier RMS of 0.54°; level 3
16.4% and 0.27°. C3b's coarse band is 0.38–0.43 gross by the 25% rule. Most of that cannot be
wrong peaks. No search strategy moves a right peak; only a finer look does.

So each judged cell is one of: **occluded** (wrong or beyond 25%, and the other eye sees less
than half of it), **window** (wrong peak within a window radius — 2 cells, Chebyshev — of a
depth edge), **search** (wrong peak farther from any edge), **resolution** (right peak, beyond
25% all the same), **good**. A depth edge is judged per *sample* (a 4-neighbour in the L raster
differing by more than 25% in ρ), and a cell is an edge cell when it holds one — between cell
means a straddling cell splits the jump into two steps that each pass under the threshold.

Reported per level: the kinds; P(wrong peak) and P(beyond 25%) against the distance to an edge
(the figure, one panel per level); the share of the near-edge wrong peaks that is excess over
the far rate; for the right peaks, the level's bias and how much of "beyond 25%" goes away with
the bias removed (a constant is removable, a spread is not); and **the parent oracle** — for
every cell with a consistent parent, whether a search within ±2 cells of the parent's parallax
would have *cured* it (wrong now, truth inside the interval, the wrong peak outside) or put it
*at risk* (right now, truth outside). That is coarse-to-fine's ceiling and its cost, read off
the saved records before a line of it is written. Over all levels: the kinds weighted by cell
area, which is how the loop's gross fraction counts them.

## Commands (workstation) — all host side

```bash
.venv/bin/python tools/gross_diagnosis.py --self-test                                   # interactive
# refresh field.json with the standard settings: C1's negatives (--no-lr, --eval-factor 4) wrote it last
.venv/bin/python tools/stereo_field.py previews/pairs/calib_room_sp                     # interactive
.venv/bin/python tools/stereo_field.py previews/pairs/calib_room_full_sp --kappa 3.8    # batch
.venv/bin/python tools/gross_diagnosis.py previews/pairs/calib_room_sp                  # interactive
.venv/bin/python tools/gross_diagnosis.py previews/pairs/calib_room_full_sp             # batch (< 1 min)
# the loop runs need the truth sidecar first (no rendering: fix.exr's Position pass)
.venv/bin/python tools/stereo_truth.py previews/loop3/class_coverage                    # interactive
.venv/bin/python tools/stereo_truth.py previews/loop3/class_coverage_full               # batch
.venv/bin/python tools/gross_diagnosis.py previews/loop3/class_coverage                 # interactive
.venv/bin/python tools/gross_diagnosis.py previews/loop3/class_coverage_full            # batch (< 1 min)
# negatives: each must exit 1
.venv/bin/python tools/gross_diagnosis.py previews/pairs/calib_room_sp --search-deg 4 ; echo "exit $?"   # (y1)
.venv/bin/python tools/gross_diagnosis.py previews/pairs/calib_room_sp --edge-jump 10 ; echo "exit $?"   # (y2)
```

Settings come from the run's own record (`loop.json` on a loop run: search 6°, κ, the carried
noise; `field.json` on a pairs run), so nothing is passed — which is why `field.json` is refreshed
first: the tool prints the settings it took, and they must read eval_factor 2.0, search_deg 3.0,
window 2 on the pairs runs. `class_coverage_full` is the run in
D20's decision rule.

## Checks, each of which can fail

- **(y1) the diagnosed field is the field on record.** Loop run: the rebuilt rows are the saved
  `field/p<NNN>.npz` rows on ≥ 99.9% of them (on the stub: 100.000% of 44 459). Pairs run: the
  per-level gross after LR, judged as `stereo_field.py` judges it, equals `field.json`'s to the
  third digit. Negative: `--search-deg 4`.
- **(y2) the edge axis means something.** Pooled over levels 0–1, P(wrong peak) within a window
  radius of an edge exceeds P(wrong peak) beyond it, and edge cells exist. Negative:
  `--edge-jump 10`.

## Predictions, written before the run

1. **Levels 0–1: the window's.** P(wrong) near an edge several times the far rate, excess share
   above 70%; resolution under 5%. (Stub, measured: 16–27% near against 2.5–5% far.)
2. **Levels 3–4: the resolution's, not the search's.** This revises the plan's prediction
   ("the search's at levels 3–4"), which C1's table already contradicted at level 4. On the
   classroom at `full`, resolution is more than half of the judged cells at level 4 and the
   largest kind at level 3; search under 10% at level 4.
3. **By area, resolution is the largest share of the bad cells** on both scenes at both
   profiles (stub, measured: 90%; the renders' texture is poorer and their wrong peaks more
   frequent, so predicted 50–80%).
4. **The parent oracle cures a minority.** Under half of the wrong peaks at levels 0–2 (stub:
   34–54% on a loop run, 17–21% on the card pairs), and puts under 5% of the right ones at risk (stub: 0.1–3.3%).
5. **The bias matters less than the spread**: removing the level's bias lowers P(beyond 25%)
   among right peaks by under a quarter at levels 3–4. If it lowers it by more, the bias is the
   cheapest fix in Phase D and goes first.

## What the numbers decide

Not decided here; Code reports, Chat and Luiz decide. The reading they would support:

- If prediction 3 holds, D20's rule ("gross 0.344 down by a third") is not reachable by any
  matcher change, and (x) has to be judged on what a matcher can move: the wrong-peak fraction
  per level and the fine and mid bands' gross. The rule is then rewritten *before* coarse-to-fine
  runs, with the diagnosis as the reason, and D20 gets its "overturned if" exercised.
- If the window's share at levels 0–1 is what prediction 1 says and the oracle cures little
  there, D2 (the window) is the step that moves the fine band and coarse-to-fine is for speed
  and for level 1–3's far-from-edge wrong peaks; the order D1 → D2 may swap.
- If the oracle cures most wrong peaks at levels 1–3 on the renders (where the far rate is 16–22%
  by C1's table, far above the stub's), coarse-to-fine goes ahead as planned.

## Results

Run 2026-09-18 on the workstation, all host side (`.venv`), nothing rendered. Self-test ok
(0.3 s). `field.json` refreshed first on both pairs runs (standard flags; exit 0, 0 failures,
the numbers of C2's second run: (p) 0.0260 vs 0.0269° (−3%, 9614 cells), RMS/bound 5.82 at
`sp`; 0.0159 vs 0.0208° (−24%), 9.76 at `full`). `stereo_truth.py` on the two loop runs:
`class_coverage` visible 93.4% occluded 3.4% outside 0.7% inconsistent 2.54%, 0.7 s;
`class_coverage_full` visible 95.6% occluded 2.7% outside 0.5% inconsistent 1.17%, 2.1 s; both
ok, (h) reports `None` on a loop run (no target/hit record). The settings line read
eval_factor 2.0, search_deg 3.0, window 2 on both pairs runs; search_deg 6.0 and κ 3.8 at
`full` on the loop runs, from `loop.json`. No FAIL line on any of the four runs. The
negatives: `--search-deg 4` exit 1 ((y1) worst difference 0.0083, levels 0, 1 and 4 fail);
`--edge-jump 10` exit 1 ((y2) "no edge cells at levels 0-1"). The standard `sp` diagnosis
was re-run afterwards (ok, worst difference 0.0000). Wall: diagnosis 4.8 s `sp`, 15.1 s
`full_sp`, 6.0 s `class_coverage`, 20.4 s `class_coverage_full`; field refresh 4.8 s and
16.1 s. The two loop runs print numpy RuntimeWarnings from `stereo_instrument.py:244–262`
(divide by zero, overflow in the cumulative sum) that the loop itself silences; they leave the
rebuilt rows equal to the record, and nothing was changed.

**`calib_room_sp`** (κ 2.5, search 3°):

```
[diag] level 0 cell 0.20 deg,   11495 cells: occluded   2.9%  window   8.0%  search   1.0%  resolution   1.5%  good  86.6%  | near an edge  34.6% of cells; P(wrong) near  23.8% far   1.6% (excess share of near-edge wrong peaks  93.5%); P(beyond 25%) near  26.6% far   2.2%
[diag] level 1 cell 0.40 deg,   19160 cells: occluded   7.9%  window  22.3%  search   1.3%  resolution   9.5%  good  59.1%  | near an edge  65.7% of cells; P(wrong) near  37.0% far   4.0% (excess share of near-edge wrong peaks  89.1%); P(beyond 25%) near  47.1% far  14.9%
[diag] level 2 cell 0.80 deg,   29330 cells: occluded   4.9%  window  15.1%  search   0.4%  resolution  31.3%  good  48.2%  | near an edge  74.6% of cells; P(wrong) near  21.5% far   1.8% (excess share of near-edge wrong peaks  91.5%); P(beyond 25%) near  59.3% far  21.5%
[diag] level 3 cell 1.60 deg,   34423 cells: occluded   4.6%  window   0.4%  search   0.0%  resolution  61.2%  good  33.8%  | near an edge  79.9% of cells; P(wrong) near   0.5% far   0.1% (excess share of near-edge wrong peaks  75.0%); P(beyond 25%) near  69.5% far  47.2%
[diag] level 4 cell 3.21 deg,   15029 cells: occluded   6.4%  window   0.1%  search   0.1%  resolution  64.0%  good  29.4%  | near an edge  79.9% of cells; P(wrong) near   0.2% far   0.4% (excess share of near-edge wrong peaks   0.0%); P(beyond 25%) near  70.5% far  63.2%
[diag] level 0 right peaks: bias +0.06 cells, RMS 0.15 cells; beyond 25%   1.7% ->   1.5% with the level's bias removed
[diag] level 1 right peaks: bias +0.11 cells, RMS 0.27 cells; beyond 25%  13.9% ->  12.0% with the level's bias removed
[diag] level 2 right peaks: bias +0.20 cells, RMS 0.40 cells; beyond 25%  39.7% ->  52.3% with the level's bias removed
[diag] level 3 right peaks: bias +0.26 cells, RMS 0.41 cells; beyond 25%  64.8% ->  74.1% with the level's bias removed
[diag] level 4 right peaks: bias +0.15 cells, RMS 0.24 cells; beyond 25%  69.0% ->  65.8% with the level's bias removed
[diag] level 0 parent oracle:  84.8% of cells have a consistent parent; coarse-to-fine would cure   6.2% of the wrong peaks (64 of 1031) and put at risk   0.6% of the right ones (57 of 10107)
[diag] level 1 parent oracle:  97.8% of cells have a consistent parent; coarse-to-fine would cure   2.5% of the wrong peaks (114 of 4515) and put at risk   1.4% of the right ones (185 of 13063)
[diag] level 2 parent oracle:  97.5% of cells have a consistent parent; coarse-to-fine would cure   4.2% of the wrong peaks (194 of 4570) and put at risk   0.0% of the right ones (2 of 23121)
[diag] level 3 parent oracle:  99.5% of cells have a consistent parent; coarse-to-fine would cure   0.7% of the wrong peaks (1 of 152) and put at risk   0.0% of the right ones (0 of 32462)
[diag] level 4 parent oracle:   0.0% of cells have a consistent parent; coarse-to-fine would cure   0.0% of the wrong peaks (0 of 30) and put at risk   0.0% of the right ones (0 of 13938)
[diag] by area (the loop's count):  67.3% of the judged area is wrong or beyond 25%; of that, occluded   8.5%  window   2.3%  search   0.2%  resolution  89.1%
[diag] (y1) per-level gross after LR vs field.json: worst difference 0.0000
```

**`calib_room_full_sp`** (κ 3.8, search 3°):

```
[diag] level 0 cell 0.10 deg,   46919 cells: occluded   2.2%  window   7.0%  search   1.3%  resolution   0.1%  good  89.3%  | near an edge  21.0% of cells; P(wrong) near  34.1% far   1.7% (excess share of near-edge wrong peaks  95.0%); P(beyond 25%) near  33.9% far   1.2%
[diag] level 1 cell 0.20 deg,   74500 cells: occluded   5.5%  window  15.9%  search   5.8%  resolution   2.6%  good  70.2%  | near an edge  41.1% of cells; P(wrong) near  41.2% far  10.5% (excess share of near-edge wrong peaks  74.6%); P(beyond 25%) near  42.6% far  12.8%
[diag] level 2 cell 0.40 deg,  117678 cells: occluded   4.5%  window  12.8%  search   3.9%  resolution  10.2%  good  68.5%  | near an edge  46.1% of cells; P(wrong) near  29.3% far   7.7% (excess share of near-edge wrong peaks  73.9%); P(beyond 25%) near  45.0% far  14.1%
[diag] level 3 cell 0.80 deg,  137424 cells: occluded   3.1%  window  11.6%  search   5.2%  resolution  21.3%  good  58.9%  | near an edge  56.8% of cells; P(wrong) near  21.1% far  12.6% (excess share of near-edge wrong peaks  40.4%); P(beyond 25%) near  51.0% far  24.2%
[diag] level 4 cell 1.60 deg,   59322 cells: occluded   3.0%  window   0.4%  search   1.2%  resolution  50.8%  good  44.6%  | near an edge  60.4% of cells; P(wrong) near   0.8% far   3.1% (excess share of near-edge wrong peaks   0.0%); P(beyond 25%) near  61.9% far  42.9%
[diag] level 0 right peaks: bias +0.02 cells, RMS 0.16 cells; beyond 25%   0.1% ->   0.1% with the level's bias removed
[diag] level 1 right peaks: bias +0.06 cells, RMS 0.23 cells; beyond 25%   3.6% ->   3.4% with the level's bias removed
[diag] level 2 right peaks: bias +0.07 cells, RMS 0.26 cells; beyond 25%  13.0% ->  11.8% with the level's bias removed
[diag] level 3 right peaks: bias +0.14 cells, RMS 0.33 cells; beyond 25%  26.7% ->  34.0% with the level's bias removed
[diag] level 4 right peaks: bias +0.17 cells, RMS 0.34 cells; beyond 25%  53.6% ->  62.1% with the level's bias removed
[diag] level 0 parent oracle:  97.8% of cells have a consistent parent; coarse-to-fine would cure   5.7% of the wrong peaks (222 of 3894) and put at risk   0.8% of the right ones (321 of 41883)
[diag] level 1 parent oracle:  94.1% of cells have a consistent parent; coarse-to-fine would cure  15.8% of the wrong peaks (2561 of 16184) and put at risk   5.0% of the right ones (2719 of 53947)
[diag] level 2 parent oracle:  94.8% of cells have a consistent parent; coarse-to-fine would cure  14.1% of the wrong peaks (2780 of 19738) and put at risk   9.0% of the right ones (8327 of 92118)
[diag] level 3 parent oracle:  99.9% of cells have a consistent parent; coarse-to-fine would cure  33.0% of the wrong peaks (7633 of 23103) and put at risk   0.0% of the right ones (36 of 109458)
[diag] level 4 parent oracle:   0.0% of cells have a consistent parent; coarse-to-fine would cure   0.0% of the wrong peaks (0 of 957) and put at risk   0.0% of the right ones (0 of 56250)
[diag] by area (the loop's count):  48.6% of the judged area is wrong or beyond 25%; of that, occluded   6.5%  window  10.8%  search   5.7%  resolution  76.9%
[diag] (y1) per-level gross after LR vs field.json: worst difference 0.0000
```

**`class_coverage`** (classroom, `small`; κ 2.5, search 6°, from `loop.json`):

```
[diag] level 0 cell 0.20 deg,     508 cells: occluded   3.9%  window  16.1%  search  30.7%  resolution   2.0%  good  47.2%  | near an edge  43.4% of cells; P(wrong) near  39.8% far  58.0% (excess share of near-edge wrong peaks   0.0%); P(beyond 25%) near  33.5% far  56.1%
[diag] level 1 cell 0.40 deg,    3151 cells: occluded   4.4%  window  13.4%  search  10.2%  resolution  11.4%  good  60.6%  | near an edge  37.8% of cells; P(wrong) near  37.6% far  17.4% (excess share of near-edge wrong peaks  53.7%); P(beyond 25%) near  43.1% far  30.3%
[diag] level 2 cell 0.80 deg,    8490 cells: occluded   4.2%  window  11.9%  search   3.9%  resolution  26.5%  good  53.4%  | near an edge  46.9% of cells; P(wrong) near  27.0% far   7.9% (excess share of near-edge wrong peaks  70.7%); P(beyond 25%) near  57.8% far  33.3%
[diag] level 3 cell 1.60 deg,   14383 cells: occluded   4.8%  window   5.3%  search   1.6%  resolution  46.3%  good  42.1%  | near an edge  61.1% of cells; P(wrong) near   9.3% far   4.4% (excess share of near-edge wrong peaks  52.8%); P(beyond 25%) near  63.2% far  47.3%
[diag] level 4 cell 3.21 deg,   11054 cells: occluded   8.0%  window   1.1%  search   0.6%  resolution  58.4%  good  31.8%  | near an edge  63.1% of cells; P(wrong) near   2.0% far   1.9% (excess share of near-edge wrong peaks   6.4%); P(beyond 25%) near  68.9% far  63.8%
[diag] level 0 right peaks: bias +0.01 cells, RMS 0.38 cells; beyond 25%   4.2% ->   4.2% with the level's bias removed
[diag] level 1 right peaks: bias +0.16 cells, RMS 0.41 cells; beyond 25%  16.2% ->  12.6% with the level's bias removed
[diag] level 2 right peaks: bias +0.12 cells, RMS 0.37 cells; beyond 25%  34.0% ->  32.3% with the level's bias removed
[diag] level 3 right peaks: bias +0.12 cells, RMS 0.35 cells; beyond 25%  53.6% ->  53.5% with the level's bias removed
[diag] level 4 right peaks: bias +0.10 cells, RMS 0.29 cells; beyond 25%  66.4% ->  67.6% with the level's bias removed
[diag] level 0 parent oracle:  53.1% of cells have a consistent parent; coarse-to-fine would cure  11.8% of the wrong peaks (28 of 238) and put at risk   2.1% of the right ones (5 of 237)
[diag] level 1 parent oracle:  74.4% of cells have a consistent parent; coarse-to-fine would cure  16.8% of the wrong peaks (125 of 743) and put at risk   1.3% of the right ones (28 of 2223)
[diag] level 2 parent oracle:  77.9% of cells have a consistent parent; coarse-to-fine would cure  11.4% of the wrong peaks (154 of 1347) and put at risk   0.8% of the right ones (53 of 6629)
[diag] level 3 parent oracle:  99.2% of cells have a consistent parent; coarse-to-fine would cure  11.5% of the wrong peaks (114 of 990) and put at risk   0.2% of the right ones (25 of 12424)
[diag] level 4 parent oracle:   0.0% of cells have a consistent parent; coarse-to-fine would cure   0.0% of the wrong peaks (0 of 192) and put at risk   0.0% of the right ones (0 of 9728)
[diag] by area (the loop's count):  64.9% of the judged area is wrong or beyond 25%; of that, occluded  10.9%  window   3.9%  search   1.5%  resolution  83.7%
[diag] (y1) rebuilt field = the record on 100.000% of 46692 rows
```

**`class_coverage_full`** (classroom, `full`, the run in D20's rule; κ 3.8, search 6°):

```
[diag] level 0 cell 0.10 deg,    4736 cells: occluded   5.2%  window   9.2%  search  15.3%  resolution   0.0%  good  70.4%  | near an edge  24.4% of cells; P(wrong) near  40.1% far  21.5% (excess share of near-edge wrong peaks  46.3%); P(beyond 25%) near  31.3% far  14.7%
[diag] level 1 cell 0.20 deg,   18340 cells: occluded   4.0%  window   8.5%  search  13.1%  resolution   0.7%  good  73.7%  | near an edge  23.6% of cells; P(wrong) near  37.9% far  18.1% (excess share of near-edge wrong peaks  52.4%); P(beyond 25%) near  32.4% far  15.1%
[diag] level 2 cell 0.40 deg,   42525 cells: occluded   3.0%  window   9.9%  search   5.8%  resolution   6.3%  good  75.0%  | near an edge  31.0% of cells; P(wrong) near  33.2% far   8.7% (excess share of near-edge wrong peaks  73.7%); P(beyond 25%) near  40.2% far  12.6%
[diag] level 3 cell 0.80 deg,   65854 cells: occluded   3.0%  window   8.2%  search   2.0%  resolution  18.7%  good  68.1%  | near an edge  41.3% of cells; P(wrong) near  20.9% far   3.6% (excess share of near-edge wrong peaks  82.5%); P(beyond 25%) near  47.0% far  18.4%
[diag] level 4 cell 1.60 deg,   44329 cells: occluded   4.2%  window   3.0%  search   1.7%  resolution  37.2%  good  53.8%  | near an edge  42.4% of cells; P(wrong) near   7.6% far   3.1% (excess share of near-edge wrong peaks  58.9%); P(beyond 25%) near  57.4% far  35.2%
[diag] level 0 right peaks: bias +0.11 cells, RMS 0.32 cells; beyond 25%   0.0% ->   0.0% with the level's bias removed
[diag] level 1 right peaks: bias +0.10 cells, RMS 0.32 cells; beyond 25%   0.9% ->   0.7% with the level's bias removed
[diag] level 2 right peaks: bias +0.07 cells, RMS 0.32 cells; beyond 25%   7.9% ->   7.4% with the level's bias removed
[diag] level 3 right peaks: bias +0.09 cells, RMS 0.31 cells; beyond 25%  21.9% ->  21.0% with the level's bias removed
[diag] level 4 right peaks: bias +0.07 cells, RMS 0.30 cells; beyond 25%  41.7% ->  42.0% with the level's bias removed
[diag] level 0 parent oracle:  75.0% of cells have a consistent parent; coarse-to-fine would cure  15.8% of the wrong peaks (183 of 1160) and put at risk   4.2% of the right ones (139 of 3289)
[diag] level 1 parent oracle:  81.4% of cells have a consistent parent; coarse-to-fine would cure  25.2% of the wrong peaks (997 of 3950) and put at risk   3.1% of the right ones (413 of 13418)
[diag] level 2 parent oracle:  81.8% of cells have a consistent parent; coarse-to-fine would cure  16.5% of the wrong peaks (1094 of 6648) and put at risk   1.7% of the right ones (581 of 34059)
[diag] level 3 parent oracle:  93.9% of cells have a consistent parent; coarse-to-fine would cure  11.4% of the wrong peaks (770 of 6769) and put at risk   0.7% of the right ones (371 of 56177)
[diag] level 4 parent oracle:   0.0% of cells have a consistent parent; coarse-to-fine would cure   0.0% of the wrong peaks (0 of 2106) and put at risk   0.0% of the right ones (0 of 39613)
[diag] by area (the loop's count):  41.5% of the judged area is wrong or beyond 25%; of that, occluded   9.2%  window  11.3%  search   4.9%  resolution  74.6%
[diag] (y1) rebuilt field = the record on 99.999% of 213541 rows
```

Figures: `docs/reference/d1_diagnosis_classroom_full.png` (from `class_coverage_full`) and
`docs/reference/d1_diagnosis_calib_room_full.png` (from `calib_room_full_sp`). On the calib
room the orange curve (P(wrong peak)) falls to its floor at the window's edge (2 cells) at
every level; on the classroom it falls at levels 2–4 but at levels 0–1 the far bins stay at
0.1–0.3 and rise again beyond 6 cells.

### The five predictions against the runs

1. **Levels 0–1 the window's — held on the calib room, failed on the classroom.** Calib room:
   P(wrong) near/far 23.8/1.6% and 37.0/4.0% at `sp`, 34.1/1.7% and 41.2/10.5% at `full`;
   excess share 89–95% at `sp`, 75–95% at `full`; window the largest bad kind at both levels;
   resolution 1.5% and 0.1% at level 0, 9.5% (`sp`, above the predicted 5%) and 2.6% at level 1.
   Classroom: excess share 46.3% and 52.4% at `full`, 0.0% and 53.7% at `small`; **search
   exceeds window at both levels at `full` and at level 0 at `small`** (`full`: 15.3 vs 9.2%,
   13.1 vs 8.5%; `small`: 30.7 vs 16.1% at level 0, 10.2 vs 13.4% at level 1); at `class_coverage` level 0
   the far rate 58.0% is above the near rate 39.8% (508 cells). The classroom's fine levels
   have far-from-edge wrong peaks at 18–22% (`full`), which is C1's table, not the stub's 2.5–5%.
2. **Levels 3–4 the resolution's — held in direction, failed on the 50% clause.**
   `class_coverage_full`: level 4 resolution 37.2% of the judged cells (predicted > 50%; it is
   80% of the level's bad cells: 37.2 of 46.2), largest kind at level 3 (18.7% vs window 8.2%,
   search 2.0%, occluded 3.0%), search 1.7% at level 4 (predicted < 10%). Calib room `full`:
   level 4 resolution 50.8%, search 1.2%. Search is under 6% at levels 3–4 on all four runs.
3. **By area, resolution the largest share of the bad cells — held on all four**, and above
   the predicted 50–80% on three: 89.1% (`calib_room_sp`), 76.9% (`calib_room_full_sp`), 83.7%
   (`class_coverage`), 74.6% (`class_coverage_full`). The bad area itself: 67.3 / 48.6 / 64.9 /
   41.5%. Window is 2.3–11.3% of the bad area, search 0.2–5.7%, occluded 6.5–10.9%.
4. **The parent oracle cures a minority — held; the "under 5% at risk" clause failed on one
   run.** Cure at levels 0–2: 6.2/2.5/4.2% (`sp`), 5.7/15.8/14.1% (`full_sp`), 11.8/16.8/11.4%
   (`class_coverage`), 15.8/25.2/16.5% (`class_coverage_full`); the best anywhere is level 3 of
   `calib_room_full_sp`, 33.0%. At risk: under 5% on three runs (max 4.2%, `class_coverage_full`
   level 0); 5.0% at level 1 and **9.0% at level 2 of `calib_room_full_sp`** (8327 of 92118 right
   peaks), where the level-3 parent's inlier RMS is 0.33 of a 0.8° cell.
5. **Bias matters less than the spread — held on all four.** Removing the level's bias lowers
   P(beyond 25%) among right peaks by at most 4.6% relative at levels 3–4 (`calib_room_sp`
   level 4, 69.0 → 65.8%) and raises it on five of the eight level rows (`calib_room_sp` level 3
   64.8 → 74.1%, `calib_room_full_sp` levels 3–4 26.7 → 34.0% and 53.6 → 62.1%): the right
   peaks' ρ error is not a constant offset of the parallax. The bias is not the cheapest fix.

Not decided here (D20's rule, the order D1b/D2): the numbers go back to Chat and Luiz.
