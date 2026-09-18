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

_To be filled by Code from the runs: per run, the `[diag]` lines verbatim (the five level
lines, the right-peaks lines, the oracle lines, the area line, (y1)), the two negatives' exit
codes, the wall time, and the five predictions each marked held / failed with the number.
Figures: copy `previews/loop3/class_coverage_full/gross_diagnosis.png` to
`docs/reference/d1_diagnosis_classroom_full.png` and the `calib_room_full_sp` one to
`docs/reference/d1_diagnosis_calib_room_full.png`._
