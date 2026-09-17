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

## After the run (2026-09-17)

Five runs, no lock, the `full` run in 79 s at 1.6 s per fixation with a 1803 × 3606 belief and
no memory trouble. Two things to settle before the writing.

**(u) was a wrong check, not a wrong loop.** It compared the median error over all measured
cells at the end with the median after fixation 0 — two medians over different sets; fifty
fixations of coarse periphery raise the second without any measured cell getting worse (on the
calib room the sets happened to order the other way, which is why it passed there). (u) now
takes the cells measured and judged after fixation 0 and asks whether *those same cells* are
worse at the end, with 5% tolerance; on the stub they improve from 0.114 to 0.07 /m, which is
what "the loop learns" should mean. No loop run is re-done for it; the eval re-judges the
records.

**The classroom at `small` is at the sensor's noise limit.** Its per-pixel noise is 2.5× the
calib room's at the same spp (0.18 relative; the manifest records 0.092 at 256 spp and it
scales as expected), fields have half the matchable cells, the fine band is 4–7% of the cap
against the calib room's 8–20%, and half of the measured cells are gross — depth edges
everywhere, in a scene where the fovea barely resolves the texture. In that regime the
variance-driven policy loses to the two that ignore the model: info last on error and on fine
coverage, random first, coverage second, the spread among random / coverage / oracle inside
the fine band's fixation-to-fixation noise. The reading: `info` optimises a variance model
that is wrong for half the cells it scores (gross errors are not in it), so its looks go where
the model says the gain is, not where the error is; `coverage` and `random` do not consult the
model and are robust to it. The objective costs when the error model is wrong; it bought
nothing when it was right (the calib room, within 3% of coverage). Either way the
predecessors' finding holds, now with a mechanism.

`full` is this scene's profile: noise 0.09, gross 0.355, median ρ error 0.0435 /m (0.0186 on the
fine band, 14 cm at 2.7 m). To rank the policies where the sensor works, the four run again at
`full` — four more runs of eighty seconds. The summary and the front page are written on that.

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

### Full profile (2026-09-17, after `5001865`: (u) on the fixation-0 cells)

Random, coverage and oracle at `full` on the classroom (κ 3.8, 50 fixations, 1.287e9 rays each),
beside the info run from the first step; then every earlier run re-judged under the new (u)
without re-rendering. All measured. Figure: `docs/reference/c3_compare_classroom_full.png`.

| policy | profile | rays | wall | distinct dirs | cover any / fine | ρ err median all / fine (1/m) | depth err median all / fine (m) | gross | z RMS | vergence err median (m) | (u) fixation-0 cells, ρ err start → end |
|---|---|---|---|---|---|---|---|---|---|---|---|
| random | full | 1.287e9 | 68.4 s | 49 | 0.924 / 0.078 | 0.0385 / 0.0155 | 0.325 / 0.104 | 0.314 | 1.02 | 0.33 | 27427: 0.0397 → 0.0190 |
| coverage | full | 1.287e9 | 74.9 s | 50 | 0.930 / 0.094 | 0.0427 / 0.0177 | 0.351 / 0.134 | 0.344 | 1.01 | 0.38 | 27427: 0.0397 → 0.0180 |
| info | full | 1.287e9 | 78.6 s | 50 | 0.920 / 0.059 | 0.0435 / 0.0186 | 0.375 / 0.140 | 0.355 | 0.85 | 0.71 | 27427: 0.0397 → 0.0195 |
| oracle | full | 1.287e9 | 77.5 s | 50 | 0.868 / 0.064 | 0.0453 / 0.0139 | 0.438 / 0.231 | 0.374 | 0.74 | 0.61 | 27427: 0.0397 → 0.0183 |

Per-fixation timings, medians (choose + render + infer + judge, s): random 0.023 + 0.724 + 0.465
+ 0.146; coverage 0.135 + 0.724 + 0.460 + 0.146; info 0.293 + 0.637 + 0.465 + 0.147; oracle 0.291
+ 0.639 + 0.441 + 0.143 — 1.4–1.6 s per fixation, 4400–4600 matchable cells per field (info
3400), gross by band fine / mid / coarse 0.20–0.28 / 0.21–0.23 / 0.38–0.43.

Rankings at `full` (reported, not judged): by median ρ error, **random 0.0385 < coverage 0.0427
< info 0.0435 < oracle 0.0453**; by fine coverage, **coverage 0.094 > random 0.078 > oracle 0.064
> info 0.059**. On the fine band's own error oracle 0.0139 < random 0.0155 < coverage 0.0177 <
info 0.0186.

**Checks: (s), (t), (u), (v) pass on all thirteen runs** (four `full`, four `small`, five on the
calib room); every eval exits 0. The new (u) line, the cells measured and judged after
fixation 0 and the same cells at the end (median ρ error, 1/m):

- classroom `full`: 27427 cells, 0.0397 → 0.0190 (random), 0.0180 (coverage), 0.0195 (info),
  0.0183 (oracle);
- classroom `small`: 5627 cells, 0.0799 → 0.0417 (random), 0.0412 (coverage), 0.0535 (info),
  0.0511 (oracle);
- calib room `small`: 10820 cells, 0.2160 → 0.2081 (targets), 0.2045 (random), 0.2155
  (coverage), 0.2118 (info), 0.2009 (oracle).

The fixation-0 cells improve on every run: by half on the classroom (the loop learns), by 0–7%
on the calib room, where fixation 0's cells are the central cards and their surround, measured
finely at once and gross at the depth edges thereafter (0.216 /m is a floor the periphery's
coarse looks cannot lower).

**Does info recover at `full`?** Partly. With the error model closer to the truth (gross 0.36
against 0.55 at `small`) info moves from last to third on median error, within 2% of coverage
(0.0435 against 0.0427), and stays last on fine coverage. Random stays first on error at both
profiles, by 10% at `full`, and coverage first on fine coverage at both. The spread among the
four is 18% on median error at `full`; the chart's fine-band curves cross each other through
the run. What the two profiles say together: on a scene textured everywhere the objective does
not buy error at equal rays; spreading does, and random spreads as well as anything. The
`small` rankings and (u) lines are unchanged from the first step (the runs were re-judged,
not re-rendered).
