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

## Results

Run 2026-09-20 on the workstation by Code. Every number is read from files under
`previews/fsg5/`.

**Final status: `FSG5_INCREMENT5_PASS`**, exit 0, `trial_passes: 4`, empty
`fails`. All four full trials returned `FSG5_CURVED_RUN_PASS` with empty fail
lists. **Increment 5 is CLOSED. The next experiment is AUTHORIZED BUT NOT
IMPLEMENTED** — no design or code for it was written.

The already validated active loop grew a metrically correct curved visible
surface with **no new policy, no registration step and no surface model**.

### Integrity — what was frozen

HEAD `18cfd0a2ca8cb32a89f0c5fadf1df5fef810bcbf` on clean `main`, `47ba474`
verified an ancestor. `git diff 47ba474` over the FSG1 stereo modules
(`fsg_stereo_supported`, `fsg_stereo_hdr`, `fsg_stereo`, `fsg_evaluate`,
`fsg_geometry`), **`fsg4_policy.py`**, **`fsg3_surface_map.py`**,
`fsg4_public.py`, `rig.py`, `bl_common.py` and `requirements-fsg.txt` is
**EMPTY**. Nine files were added and none modified.

Verified by reading the code before running: `fsg5_run.py` imports the EXISTING
`fsg4_policy` and the EXISTING `fsg3_surface_map`, calls `compute_once` with
`check_kernel_equivalence` and never `compute_variants`, imports no fixture
geometry and opens no `evaluation_only` asset. `fsg5_public` fixes
`association_radius_m = 0.012`, `hash_cell_m = 0.012`,
`VERGENCE_DISTANCE_M = 2.10`, `FIXTURES = (curve_right, curve_left)`,
`SEEDS = (601, 647)`.

Environment: Python 3.12.3, NumPy 2.2.6, OpenCV 4.13.0, Pillow 12.3.0; Blender
5.2.1 LTS; OPTIX on an NVIDIA RTX 4090.

All seven new Python files compile.
`[fsg5-scene] PASS right=[-8.487,14.866] left=[-14.866,8.487] chord_max_mm=0.100`
(requirement < 0.2 mm) and `[fsg5-check] SUMMARY passed=6 failed=0`. The five
negatives each exit 1:

    [fsg5-check] FAIL AssertionError deliberate hard-coded/wrong curved frontier direction detected
    [fsg5-check] FAIL AssertionError deliberate flat substitute for curved surface detected
    [fsg5-check] FAIL AssertionError deliberate 5cm map shift detected
    [fsg5-check] FAIL AssertionError deliberate 15mm fusion contraction detected
    [fsg5-check] FAIL AssertionError deliberate background contamination detected

All twelve existing FSG1–FSG4c regression suites remain green: 24 / 29 / 34 / 48 /
37 / 46 / 4 / 5 / 7 / 7 / 7 / 8.

### Smoke, diagnostic only

`curve_right` / 601 at small: run exit 0, evaluation exit 2 —
`FSG5_CURVED_RUN_FAIL` on four numerical gates: final map median curved-surface
error 12.225 mm (limit 10), p95 30.546 mm (limit 30), and `fix_00` / `fix_04`
object measurement coverage 87.756% / 89.819% (limit 90%). The familiar
small-profile gap. Integrity was sound — no provenance or runtime exception — so
the full schedule proceeded. Notably the curvature-specific gate already passed
at small: supported signed radial median **-4.295 mm** on 12,146 multi-look
surfels, inside the ±7.5 mm limit.

### The four full trials — all PASS, empty fail lists

| trial | trajectory (deg) | term | fixations | map points | support>=2 | coverage final | gain over seed |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| curve_right/601 | -7, -2, +3, +8, +13 | `no_frontier` | 5 | 90,675 | 55,383 | 99.995% | 69.792 pp |
| curve_right/647 | -7, -2, +3, +8, +13 | `no_frontier` | 5 | 90,689 | 55,317 | 100.000% | 69.810 pp |
| curve_left/601 | +7, +2, -3, -8, -13 | `no_frontier` | 5 | 91,719 | 54,526 | 100.000% | 62.900 pp |
| curve_left/647 | +7, +2, -3, -8, -13 | `no_frontier` | 5 | 91,723 | 54,767 | 99.991% | 62.891 pp |

Every saccade is exactly 5 degrees with no repeat, and the policy produced the
mirrored trajectory on the mirrored fixture **unaided** — it was given no fixture
identity and no direction. The design traces in the handoff were sanity notes,
not instructions, and the policy matched them from its own evidence.

Curved geometry on the final maps — the gates that matter for this increment:

| trial | surface median | surface p95 | signed radial median (multi-look) | purity | idempotent |
| --- | ---: | ---: | ---: | --- | --- |
| curve_right/601 | 3.647 mm | 11.263 mm | **+1.335 mm** | ID 81 only | true |
| curve_right/647 | 3.654 mm | 11.309 mm | **+1.335 mm** | ID 81 only | true |
| curve_left/601 | 3.362 mm | 10.769 mm | **+1.251 mm** | ID 81 only | true |
| curve_left/647 | 3.363 mm | 10.797 mm | **+1.252 mm** | ID 81 only | true |

Gates are <=10 mm median, <=30 mm p95, |signed radial| <= 7.5 mm on >=5,000
multi-look surfels. All four clear the median by ~2.7x and the p95 by ~2.7x, and
the signed radial error is **positive** — the map sits about 1.3 mm *outward* of
the analytic cylinder, not contracted inward. The anticipated failure mode (a),
that 12 mm Euclidean fusion would radially contract a curved surface, **did not
occur**. An independent check on the exported point clouds agrees: reconstructed
median radius 0.75075–0.75097 m against a true 0.750 m, with the y extent
[-0.168, +0.166] m against a 0.34 m ribbon height.

Per-patch and overlap measurements, across all four trials: minimum oracle object
reference 25,686 pixels (gate >=100); minimum object measurement coverage
93.561% (gate >=90%); post-seed matched counts 24,147–29,018 (gate >=5,000);
overlap medians 1.800–2.014 mm (gate <=10 mm); overlap p95 4.722–6.012 mm (gate
<=25 mm); every post-seed replay idempotent; no coverage drop beyond 0.5 pp
anywhere — the largest decrease observed was 0.005 pp.

### Aggregate

`FSG5_INCREMENT5_PASS`, `trial_passes: 4`, `fails: []`, mean final coverage
**0.9999651**. Ranges across the four trials: surface median
3.362–3.654 mm, surface p95 10.769–11.309 mm, supported signed radial median
+1.251 to +1.335 mm.

### A descriptive observation, not a failure

On `curve_left` the fifth fixation added essentially nothing: new fraction
0.00066 and 0.00074, coverage gain +0.014 pp (seed 601) and **-0.005 pp** (seed
647), because coverage was already 99.99% after four looks. Under the closed
FSG4c contract these are descriptive measurements, not validity gates, so the
runs remain valid; the tiny decrease is far inside the 0.5 pp tolerance. It is
the same slight overshoot the policy showed on FSG4b's `case_b`, and it is
recorded here rather than smoothed away. `curve_right` used its fifth fixation
productively, gaining 5.86 pp.

### Visual and PLY inspection

`growth.png` (truth-free, written by the run) and the evaluator's
`growth_truth.png` for all four trials show the two fixtures growing in
mirror-image directions: `curve_right` seeds at -7 degrees on the ribbon's left
edge and grows rightward, 30.2 -> 50.4 -> 70.3 -> 94.1 -> 100.0%; `curve_left`
seeds at +7 degrees on the right edge and grows leftward, 37.1 -> 56.6 -> 77.3 ->
100.0 -> 100.0%. The accumulated surfaces are visibly curved ribbons rather than
flat rectangles, with the strips wrapping around the cylinder and the vertical
striations following the curvature. `coverage_curved.png` shows all four curves
rising monotonically to 100.0% with the per-trial median/p95 annotated at
3.4–3.7 / 10.8–11.3 mm.

`surface_map.ply` for each trial carries `comment fixed head frame H`, has no
faces, a per-vertex `support` property, and 90,675–91,723 vertices. Support
histograms are roughly 35–37k single-look, 48–50k two-look and 5.7–6.2k
three-look surfels. Missing geometry stays missing — no meshing, filling,
interpolation or registration anywhere in the pipeline.

### Cost and code changes

Primary camera samples: smoke 65,536,000; each full trial 1,048,576,000, so
**4,194,304,000** across the four full trials. Wall times: smoke run 14.5 s and
evaluation 9.3 s; full runs 1m16.6s, 1m17.0s, 1m18.2s, 1m17.1s; the four full
evaluations a few seconds each; aggregation 0.09 s.

**No code fix was required or made.** Nothing was tuned: no change to geometry,
texture, seeds, SPP, vergence, the stereo instrument, the policy, the fusion
radius, the truth coverage radius or any numerical gate; no rerender after the
smoke's numerical miss; no ICP, normals-based registration, meshing, hole
filling, new frontier logic, competing policy or extra seed.

### Scope of the closure

**Increment 5 is closed** on this evidence: the frozen FSG1 instrument, the
unchanged FSG4 frontier policy and the unchanged FSG3 12 mm Euclidean fusion grew
a convex curved surface to ~100% completeness at 3.4–3.7 mm median accuracy, with
no inward radial contraction, on both mirror orientations and both seeds.

The claim is narrow. Two mirrored opaque diffuse cylindrical ribbons of a single
fixed radius (0.75 m) and arc (75 degrees), two Monte-Carlo seeds, oracle
segmentation, exact calibrated poses, horizontal saccades only, fixed 2.10 m
vergence. It is **not** a result about general curvature, varying radius, concave
or saddle geometry, self-occlusion, folds, multi-object scenes, head motion,
vergence control or calibrated uncertainty. The policy remains a 2D image-edge
and map-yaw controller; as the handoff notes, a true 3D surface-frontier
controller is now a clean next question and was deliberately not built here. The
next experiment is authorized on that basis and was not implemented. Stopped for
Luiz and Chat.
