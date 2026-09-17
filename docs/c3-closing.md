# Step C3 — closing: the classroom, one `full` run, the engine's front page

Written 2026-09-17 before the workstation run. Numbers are **predicted** or from the calib
room until the log records a measurement.

## What C3 is

C2 closed on the calibration room, where only the cards are richly textured — the right scene
to break a gain model on (it broke it three times) and the wrong one to rank policies on. C3
runs the loop on the Classroom (`scenes/classroom/classroom_eye.blend`, Phase A's realistic
interior, textured everywhere, depths from a desk's edge to the far wall) with the four
policies that need no target list, at `small`, 50 fixations each; then one run at `full` to
show the engine at the profile it was built for. Nothing new is built: C3 is the runs, the
comparison, and the writing — `docs/phase-c-summary.md` and the README rewritten as the front
page of what the repository now is, a foveated stereo rendering engine for Blender that
renders a verged pair in 30 ms and runs an active loop in one command.

## Commands (workstation)

```bash
B=scenes/classroom/classroom_eye.blend
for p in random coverage info oracle; do
  blender -b $B -P tools/active_loop.py -- --out previews/loop3/class_$p --profile small --policy $p --fixations 50
done
.venv/bin/python tools/active_eval.py previews/loop3/class_random previews/loop3/class_coverage \
    previews/loop3/class_info previews/loop3/class_oracle --out previews/loop3/class_compare
# the engine at full: one run, info, 50 fixations (predicted 2-3 min: 4x the cells per field)
blender -b $B -P tools/active_loop.py -- --out previews/loop3/class_info_full --profile full --policy info --fixations 50 --kappa 3.8
.venv/bin/python tools/active_eval.py previews/loop3/class_info_full
# the Phase B tools on a classroom loop run (reported; no card pairs to judge)
.venv/bin/python tools/check_pairs.py previews/loop3/class_info
.venv/bin/python tools/stereo_truth.py previews/loop3/class_info
```

## What to expect, and what would be a finding

- The classroom's walls, floor and furniture are textured, so the fine band should be much
  larger than the calib room's 5–14% of the cap at 50 fixations, and the periphery's gross
  fraction (depth edges everywhere in the room) is the number to watch.
- Predicted ranking, from the calib room and the stub: info ≈ coverage < random < oracle on
  median ρ error; coverage first on fine coverage. If info separates from coverage here, the
  objective matters on a textured scene — a finding either way, reported as such.
- Vergence from the periphery: the classroom has near desks and a far wall; the median
  vergence error should stay under 0.5 m and inside the 6° search range. A fixation whose
  centre lands more than a factor of two from ẑ is worth a line in the report.
- `full`: the same loop with 0.1° cells; ~10 000 cells per field; z RMS in band with κ 3.8.

## Checks

C2's (s)–(v) on the four `small` runs and on the `full` run (its own, no random to bracket:
(v) does not apply). Nothing new; C3 adds no check because it adds no code.

## Results

Run 2026-09-17 on the workstation (RTX 4090, Blender 5.2.1), Classroom (`classroom_eye.blend`),
50 fixations per run, one Blender session each. All numbers measured (`loop.json`,
`compare.json`, the evals' lines). Figures: `docs/reference/c3_compare_classroom_small.png`,
`c3_loop_info_classroom_small.png`, `c3_loop_info_classroom_full.png`.

| policy | profile | rays | wall | distinct dirs | cover any / fine | ρ err median all / fine (1/m) | depth err median all / fine (m) | gross | z RMS | vergence err median (m) |
|---|---|---|---|---|---|---|---|---|---|---|
| random | small | 7.995e7 | 29.2 s | 49 | 0.884 / 0.054 | 0.0808 / 0.0416 | 0.626 / 0.292 | 0.492 | 0.64 | 0.38 |
| coverage | small | 7.995e7 | 31.7 s | 50 | 0.867 / 0.066 | 0.0852 / 0.0534 | 0.706 / 0.387 | 0.521 | 0.62 | 0.77 |
| info | small | 7.995e7 | 37.9 s | 50 | 0.868 / 0.044 | 0.1006 / 0.0476 | 0.756 / 0.501 | 0.552 | 0.63 | 0.58 |
| oracle | small | 7.995e7 | 36.4 s | 50 | 0.835 / 0.046 | 0.0940 / 0.0789 | 0.816 / 0.459 | 0.548 | 0.69 | 0.64 |
| info | full | 1.287e9 | 78.6 s | 50 | 0.920 / 0.059 | 0.0435 / 0.0186 | 0.375 / 0.140 | 0.355 | 0.85 | 0.71 |

Per-fixation timings, medians (choose + render + infer + judge, s): random 0.006 + 0.368 + 0.142
+ 0.035; coverage 0.068 + 0.358 + 0.144 + 0.035; info 0.215 + 0.340 + 0.144 + 0.035; oracle 0.174
+ 0.328 + 0.176 + 0.034; info at `full` 0.293 + 0.637 + 0.465 + 0.147 (1.6 s per fixation; the
belief is 1803 × 3606 cells, no memory trouble). The classroom's render is 0.33–0.37 s per pair
at `small` against the calib room's 0.08–0.11 (the manifest's per-sample cost is the same; the
scene's call floor is 0.16 s against 0.06).

Rankings at `small` (reported, not judged): by median ρ error, **random 0.0808 < coverage 0.0852
< oracle 0.0940 < info 0.1006**; by fine coverage, **coverage 0.066 > random 0.054 > oracle 0.046
> info 0.044**. On the fine band's own error: random 0.0416 < info 0.0476 < coverage 0.0534 <
oracle 0.0789.

**Checks.** (s) replay exact and (t) in band (0.62–0.69 small, 0.85 full) on all five; (v) passes
on the four `small` runs (every policy's fine coverage is at least 0.8 of random's); on the `full`
run the eval does not report (v), which needs a random run in the same call, as expected.
**(u) fails on all five**: the final median ρ error over measured cells is above the value after
fixation 0 (small: 0.0799 → 0.0808 / 0.0852 / 0.1006 / 0.0940; full: 0.0397 → 0.0435) while
coverage rises from 0.34 to 0.84–0.92. The median is taken over the measured cells, and
fixation 0's measured set is the fovea and its near periphery at the middle of the room; fifty
fixations add the whole cap, most of it coarse cells at 1.6–3.2° whose error is a floor of 0.3
cell, so the median of a larger, more peripheral set rises even though every cell that was
measured after fixation 0 is at least as well known. The check as written compares two
medians over different sets; on the calib room the sets happened to order the other way. Not
changed: reported and stopped, per the prompt; whether (u) should compare on fixation 0's cells
or on the whole cap at the prior is Chat's.

**What the classroom shows that the calib room did not.** Not what the note predicted. The
fine band at 50 fixations is 4–7% of the cap, *smaller* than the calib room's 8–14%, not
larger: the classroom is textured everywhere but it is also dark and its render three times
noisier at the same spp (the loops calibrate 0.18–0.23 relative RMS per level at 64 spp against
the calib room's 0.07; the manifest's 0.092 at 256 spp scales to 0.18 at 64, so this is the
scene's noise, measured), and fields have 760–1240 matchable cells against ~2000. The
periphery's gross fraction is 0.54–0.59 at the coarse levels (0.43 at `full`) against the calib
room's 0.67–0.82: depth edges everywhere, but real texture between them. Info does separate from
coverage, in the direction the note did not expect: it is last of the four on median error
(0.1006 against coverage's 0.0852 and random's 0.0808) and last on fine coverage. With no lock
anywhere (50 distinct directions on every scored policy; the fourth-run gain model holds) the
objective costs rather than buys on this scene at this budget, and random is the best of the
four on error. The spread is 25% on median error and the fine-band error is noisy at ±30%
between fixations (the chart), so the ranking among random, coverage and oracle is not
resolved; info's last place is. Vergence from the periphery: medians 0.38–0.77 m, and 7–9
fixations per run land more than a factor of two from ẑ (e.g. random k014 ẑ 2.42 m, centre
5.90 m; coverage k010 ẑ 2.06 m, centre 0.79 m), all inside the 6° search range. At `full` the
engine runs the same loop at 1.6 s per fixation with a median depth error of 0.375 m over the
cap (0.14 m on the fine band) and gross 0.355.

The Phase B tools on `class_info`: `check_pairs` ok (0 judged card pairs of 50, reported),
`stereo_truth` ok ((i) 0.015 s₀, (j) 100%, visible 93.4%).
