# FSG5 / Increment 5 — active growth on a convex curved surface

## Decision to record before acquisition

`D-FSG5a — Curvature stress test with the existing active observer.`

Increment 4 closed the controlled planar efficiency question: the frozen frontier
policy beat the fixed scan on all four fresh paired trials. Increment 5 changes
**geometry, not intelligence**. Keep the closed FSG1 local RGB-D instrument,
existing FSG4 frontier policy and constants, FSG3 persistent head-frame surfel
fusion with the fixed 12 mm association radius, oracle instance segmentation,
exact calibrated poses, fixed 2.10 m vergence, no ICP, no meshing and no hole
filling. Replace the planar target by a finite convex cylindrical ribbon.

The scientific question is:

> Can the already validated active loop grow a metrically correct curved visible
> surface without a new policy, registration step or surface model?

A full pass closes Increment 5 and authorizes — but does not implement — the next
experiment. A miss is preserved and returned to Luiz/Chat. Code may fix only a
demonstrated implementation/orchestration defect; it may not change the stereo
instrument, policy, fusion radius, geometry, texture, seeds, SPP, vergence,
coverage radius or numerical gates to obtain a pass.

## What is frozen

- Instrument: `FSG1-HDR-SGBM-one-original-update-original-validity-v1`.
- Existing `tools/fsg4_policy.py`, unchanged.
- Existing `tools/fsg3_surface_map.py`, unchanged.
- 5 degree horizontal saccades and the FSG4 policy constants.
- FSG3/FSG4 12 mm Euclidean association and 12 mm spatial hash.
- Fixed head/cyclopean map frame H; exact eye/head geometry; no ICP.
- Oracle object membership only. Truth geometry is post-hoc evaluation data.
- Full profile at its repository default 256 spp; small at 64 spp only for smoke.
- Per-fixation new fraction and coverage gain are **descriptive**, not validity
  gates, following the closed FSG4c contract.

The active host (`fsg5_run.py`) must not import `fsg5_scene` and must not open any
`evaluation_only` asset. The current policy is intentionally **not upgraded to a
3D frontier policy in this increment**. That would confound curvature with a new
controller. If FSG5 passes, a true surface-frontier controller becomes a clean
next question.

## Fresh curved fixtures

Two opaque diffuse cylindrical ribbons are horizontal mirrors and use different
procedural textures. Both have vertical cylinder axis, radius 0.75 m, height
0.34 m, cylinder centre z = -2.80 m, and 75 degrees of cylinder arc. Rendering
uses 40 quad strips; the prospective geometry check requires the maximum chord
error against the analytic cylinder to stay below 0.2 mm.

- `curve_right`: centre x = +0.15 m, cylinder theta -40 to +35 deg, seed yaw -7 deg.
  Its visible angular span is about -8.49 to +14.87 deg, so the seed exposes only
  the right unresolved frontier.
- `curve_left`: exact horizontal mirror, centre x = -0.15 m, theta -35 to +40 deg,
  seed yaw +7 deg. Its visible span is about -14.87 to +8.49 deg.

Fresh Monte-Carlo seeds: **601** and **647**. The expected directional sequences
`-7,-2,+3,+8,+13` and `+7,+2,-3,-8,-13` are design sanity traces only; they are
not acceptance criteria. The policy chooses the actual trajectories from its map
and current segmentation evidence.

The evaluator samples the continuous analytic cylinder on a fixed 256 x 84
(theta,y) grid. A truth sample is covered when a reconstructed surfel lies within
15 mm. Thus the reported completeness is curved-surface coverage, not image
coverage.

## Prospective gates

Every full fixture/seed trial is judged independently. All four must pass.

### Acquisition / local RGB-D

- active fixations: 4–6;
- termination reason: `no_frontier`;
- every saccade is exactly 5 deg and no fixation repeats;
- every patch has at least 100 oracle object reference pixels;
- valid object measurement coverage >= 90% on every patch.

### Overlap / persistent map

For every post-seed patch:

- matched measurements >= 5,000;
- overlap median distance <= 10 mm;
- overlap P95 distance <= 25 mm;
- duplicate replay exactly idempotent;
- fixed-grid coverage may not drop by more than 0.5 percentage points.

### Curved geometry

On the final map:

- analytic finite-cylinder point-to-surface median <= 10 mm;
- analytic finite-cylinder point-to-surface P95 <= 30 mm;
- final curved-surface coverage >= 90%;
- coverage gain over the seed fixation >= 35 percentage points;
- map contains only object instance 81;
- at least 5,000 surfels have support from >=2 distinct fixations;
- for those multi-look surfels, absolute median signed radial error <= 7.5 mm.

The last gate is curvature-specific. Averaging nearby samples on a curved surface
can contract a map inward even when association distances are small. Signed
radial error is therefore recorded separately from unsigned point-to-surface
error. It is not a learned uncertainty model; it is a direct geometric check.

## Schedule

1. Record `D-FSG5a` and a prospective `docs/log.md` entry.
2. Run `tools/dev/check_fsg5.py` and the five expected-failing negatives.
3. Run the existing FSG1–FSG4 regression checks unchanged.
4. Run one diagnostic small trial: `curve_right`, seed 601. A numerical exit 2 is
   diagnostic; an integrity/runtime exception stops the experiment.
5. If smoke integrity is sound, run exactly once the four full trials:
   - `curve_right` / 601
   - `curve_right` / 647
   - `curve_left` / 601
   - `curve_left` / 647
6. Evaluate each, then aggregate exactly those four with `fsg5_compare.py`.
7. Inspect each run's `growth.png`, evaluation `growth_truth.png`, final
   `surface_map.ply`, and aggregate `coverage_curved.png`.
8. No rerender after a numerical miss; no alternate radius, curvature, seed,
   texture, policy, threshold or fixation schedule.

Suggested output roots:

- `previews/fsg5/smoke-curve_right-seed601`
- `previews/fsg5/full-curve_right-seed601`
- `previews/fsg5/full-curve_right-seed647`
- `previews/fsg5/full-curve_left-seed601`
- `previews/fsg5/full-curve_left-seed647`
- `previews/fsg5/full-comparison`
- logs under `previews/fsg5/logs/`

## Exact commands

```bash
.venv/bin/python tools/dev/check_fsg5.py
for n in policy flat shift bias purity; do
  .venv/bin/python tools/dev/check_fsg5.py --negative "$n"; test $? -eq 1 || exit 1
done
```

Then run the existing repository FSG1/FSG2/FSG3/FSG4/FSG4c check commands exactly
as already recorded in `docs/log.md`; every existing summary must remain green.

Smoke:

```bash
.venv/bin/python tools/fsg5_run.py --out previews/fsg5/smoke-curve_right-seed601 --profile small --fixture curve_right --seed 601 --device OPTIX
.venv/bin/python tools/fsg5_eval.py previews/fsg5/smoke-curve_right-seed601 --out previews/fsg5/smoke-curve_right-seed601-evaluation --mode smoke
```

Full runs:

```bash
.venv/bin/python tools/fsg5_run.py --out previews/fsg5/full-curve_right-seed601 --profile full --fixture curve_right --seed 601 --device OPTIX
.venv/bin/python tools/fsg5_eval.py previews/fsg5/full-curve_right-seed601 --out previews/fsg5/full-curve_right-seed601-evaluation --mode full
.venv/bin/python tools/fsg5_run.py --out previews/fsg5/full-curve_right-seed647 --profile full --fixture curve_right --seed 647 --device OPTIX
.venv/bin/python tools/fsg5_eval.py previews/fsg5/full-curve_right-seed647 --out previews/fsg5/full-curve_right-seed647-evaluation --mode full
.venv/bin/python tools/fsg5_run.py --out previews/fsg5/full-curve_left-seed601 --profile full --fixture curve_left --seed 601 --device OPTIX
.venv/bin/python tools/fsg5_eval.py previews/fsg5/full-curve_left-seed601 --out previews/fsg5/full-curve_left-seed601-evaluation --mode full
.venv/bin/python tools/fsg5_run.py --out previews/fsg5/full-curve_left-seed647 --profile full --fixture curve_left --seed 647 --device OPTIX
.venv/bin/python tools/fsg5_eval.py previews/fsg5/full-curve_left-seed647 --out previews/fsg5/full-curve_left-seed647-evaluation --mode full
```

Aggregate:

```bash
.venv/bin/python tools/fsg5_compare.py \
  previews/fsg5/full-curve_right-seed601-evaluation/metrics.json \
  previews/fsg5/full-curve_right-seed647-evaluation/metrics.json \
  previews/fsg5/full-curve_left-seed601-evaluation/metrics.json \
  previews/fsg5/full-curve_left-seed647-evaluation/metrics.json \
  --out previews/fsg5/full-comparison
```

A completed full run may exit 2 numerically; preserve it and continue the other
predeclared full runs. Stop early only on integrity/provenance/runtime failure.

## What Code must report

Return one paste block containing:

- HEAD before/after, branch/push and proof 47ba474 is an ancestor;
- frozen-source diff statement for FSG1 instrument, `fsg4_policy.py`,
  `fsg3_surface_map.py`, rig/bl_common/pins;
- Python/NumPy/OpenCV/Pillow, Blender and GPU backend;
- FSG5 check summary, all five expected negative FAIL lines, and existing
  regression summaries;
- small smoke exit/status and every numerical FAIL line;
- for each full trial: trajectory and termination, per-patch object measurement
  coverage, every overlap matched count/median/P95/idempotence, coverage curve and
  gain over seed, final map point count/support histogram, analytic curved-surface
  median/P95 error, multi-look signed radial median and purity;
- all full FAIL lines verbatim;
- visual/PLY inspection observations;
- primary camera samples and wall times;
- aggregate comparison status and ranges;
- every code fix, or explicitly none;
- final status exactly `FSG5_INCREMENT5_PASS` or `FSG5_INCREMENT5_FAIL`.

If PASS: close Increment 5 and authorize, but do not implement, the next
experiment. If FAIL: preserve the miss and stop for Luiz/Chat.
