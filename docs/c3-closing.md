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

*(filled by Code from the workstation run)*
