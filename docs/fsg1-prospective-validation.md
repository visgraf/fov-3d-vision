# FSG1d - prospective validation of the frozen HDR candidate

## Decision and scope

This is the next Chat-to-Code handoff after Code's FSG1c report at `edfe1d2`.
That report established a **candidate pass on the existing full seed-17 record**,
not an adopted instrument. Full foreground coverage rose from 79.319% to 99.361%;
newly accepted estimates had 0.176% median / 0.867% P95 range error. The old small
far-surface failure, the newly admitted 29-pixel weak-evidence cohort, and the
analytic bright-full coverage failure remain on record. None is overwritten.

Keep `FSG1c-fixed-soft-hdr-srgb-v1` exactly fixed. Do not change its curve, scale,
SGBM settings, texture cutoff, windows, refinement, search bounds, or acceptance.
New work here is **stimuli and validation**, not another estimator candidate.

The new real Cycles observations have not been seen by Chat. The geometry and
sampling schedule below were frozen before analytic software checks. Those
checks do exercise the geometry and an analytic image proxy; therefore call this
prospective simulator validation, not a secret benchmark or an independent
real-world dataset. No fixture or instrument parameter was selected from its
analytic accuracy results. Two Monte Carlo seeds repeat each scene; they are
not two independent geometries.

The intended next decision is narrow: does the fixed full-profile local sensor
retain its accuracy and coverage on new textured planar geometry, while refusing
a surface visible only to the left eye? A pass is evidence for a limited adoption
and a two-patch experiment to be decided by Luiz/Chat. It does not authorize Code
to change defaults, close FSG1, or implement fusion.

## New observations, same instrument

Two new fixtures are added without replacing `fronto`, `tilted`, or `step`:

| Case | Frozen geometry |
|---|---|
| `tilted_holdout` | Gaze yaw -12 degrees, pitch +8 degrees. Plane centre at 2.6 m along that gaze, signed horizontal tilt -32 degrees relative to its local tangent frame, size 3.2 x 3.2 m, instance 1. |
| `step_right` | Foreground on head-frame X in [0, 1.65] m, Z=-1.8 m, height 3.3 m, instance 1. Background Z=-3.2 m, size 4.2 x 4.2 m, instance 2. Gaze forward. This reverses the old step's occluding-edge orientation and also changes its depths. |

Textures use the unchanged generator with `instance_id + 20000` as its input.
The texture is fixed per object, common to both eyes, and unchanged across the
two rendering seeds. Instance labels themselves remain 1 and 2. Materials,
lighting, linear EXR extraction, optical settings, default spp, baseline and
calibration machinery are inherited unchanged. Vergence remains the declared
2.0 m prescription; it is not set from the true surface depth.

The fixed head frame remains the map frame. No head translation, eye-centre
motion, extra observation channel, learned segmentation, or texture enhancement
is added. Depth/mesh is evaluator-only; both estimators receive only calibration,
RGB, and the acknowledged per-eye oracle instance masks.

The validation renderer subclasses the old backend. Its setup method is a
mechanically checked copy with only fixture and texture dispatch substituted.
The acquisition orchestration is AST-identical to the original. Rendering,
Blender projection/ray-cast checks, and evaluated-mesh export are inherited.
Export verification accepts either legal diagonal of a planar quad, not an
arbitrary missing or duplicated triangle.

### Fixed acquisition schedule and budget

Run each entry **once**, including both cases and both eyes:

| Run | Profile | Seed | Spp | Primary camera samples |
|---|---|---:|---:|---:|
| Instrument/fixture smoke test | small | 31 | 64 | 26,214,400 |
| Prospective validation A | full | 31 | 256 | 419,430,400 |
| Prospective validation B | full | 73 | 256 | 419,430,400 |
| Total | | | | **865,075,200** |

These are calculated primary-camera-sample counts, including the raw image
margins, not measured runtimes or secondary light-path rays. No peripheral
preview is acquired. Stereo/evaluation require no additional camera samples.
The real run must record actual counts and times.

There is no `--spp` or `--case` override in the new render CLI. Production seeds
are restricted to this schedule. Small is a plumbing/visibility diagnostic, not
a prerequisite numerical pass for full. A numerical small failure is reported;
a source, provenance, geometry, visibility-reference, or integrity exception
stops the experiment. Do not repeat an acquisition to obtain a favorable sample.

## Frozen gates and the additional safety check

Every full-profile case and each of its declared instance interiors must pass
all the original targets independently, on each seed: coverage >=90%, median
relative range error <=1%, P95 <=3%. The original truth-based interior reference
and boundary exclusion are used without alteration. No pooling across instances
or seeds can conceal a failure. Required instance interiors must contain at
least 100 reference pixels; a missing object is a fixture failure.

The added `step_right` must exercise left-eye half-occlusion. The raw singly
visible reference is computed with the frozen evaluator: left first-hit points
whose projections lie within both acquired images but are not visible from the
right eye. Its eroded core is selected **from ground truth alone**, before any
prediction is examined. It is not a changed production validity mask.

| Profile | Required raw pixels | Required core pixels | Core erosion radius |
|---|---:|---:|---:|
| small | >=64 | >=32 | 1 pixel |
| full | >=256 | >=128 | 2 pixels |

This fixed erosion scales with resolution and keeps the core away from raster
and visibility boundaries. It removes only the safety-test perimeter; every raw
singly visible pixel, including that perimeter, remains in the report.

The new safety criterion is **zero accepted candidate points inside that core**.
An estimate remains unsupported by binocular visibility even when regularization
happens to place it near the true depth. This is a separate new safety check,
not a retrospective FSG1 threshold change. Empty or insufficient reference is
`NOT_EXERCISED` and is fatal for the step fixture, never a pass. The tilted
plane is expected to have no singly visible reference and explicitly reports
`NOT_EXERCISED` for that subtest.

Wrong-instance interior acceptance remains an error. Boundary accuracy,
coverage, all raw monocular acceptances, gained/lost support, and cohort tails
must be reported. Boundary completeness has no newly invented pass threshold.
The 29-pixel weak cohort and the analytic bright-full failure from FSG1c remain
limitations even if this prescribed full validation passes.

## Data flow and files

For each pair, compute and persist the frozen legacy and HDR predictions before
opening `evaluation_only/mesh.npz`. Evaluate their common, gained, lost, and
neither-accepted populations on the same fixed reference. The new validator
reuses the previous comparison's cohort metrics. No old rejected points are
resurrected, no hole filling occurs, and no true geometry enters either matcher.

All source record files are fingerprinted before/after analysis. Frozen old
modules and both candidate modules are pinned in `fsg_validation_scene.py`.
The new validation modules are also hashed before and after execution.
Outputs, including PLYs, are written to separate new evaluation directories.
No historical acquisition or prediction is touched.

New files in this handoff:

- `tools/fsg_validation_scene.py`: specification, fixture/texture definitions, source guards, exported-geometry verification.
- `tools/fsg_validation_render.py`: Blender-only acquisition entrypoint.
- `tools/fsg_validation_eval.py`: paired RGB inference, fixed-reference evaluation, occlusion test and visuals.
- `tools/dev/check_fsg_validation.py`: tests, analytic backend, failing controls.
- This note and `docs/fsg1-prospective-validation-checks.md`.

## Code execution prompt

Read `CLAUDE.md`, this entire note, and the accompanying validation report.
Do not infer success from the candidate's previous development-set pass.
Work on `main`, use the existing `.venv`, keep all pins and all old code unchanged.

### 0. Preflight and prospective decision - Interactive

Start from a clean tree containing this handoff, descended from `edfe1d2`.
Record HEAD and versions. Read the actual new modules; confirm no hidden setup
change. Check there is no `D-FSG1d` collision and none of the output paths exists.
Verify an empty diff from `edfe1d2` for all original FSG1 files, the audit and HDR
candidate tools/checks, `rig.py`, `bl_common.py`, and `requirements-fsg.txt`.
If not empty, stop and report rather than reconciling silently.

Before any new acquisition, append this decision verbatim to `DECISIONS.md` and
write a prospective `docs/log.md` entry (not a measured result):

> **D-FSG1d - frozen HDR prospective validation.** Preserve all FSG1/FSG1a failures,
> FSG1b diagnostics and FSG1c development-set outcomes. Keep the FSG1c encoding,
> matcher and acceptance unchanged. Authorize only the FSG1d two-fixture schedule:
> small seed 31 once, full seeds 31 and 73 once each, at their default spp. Keep
> the existing per-instance interior accuracy/coverage gates. Add a nonempty
> left-eye singly visible reference and zero accepted points in its fixed eroded
> core. A numerical small miss does not block the predeclared full tests;
> integrity or unexercised-reference failures do. Analyze every prescribed full
> record irrespective of numerical misses; no retry, tuning, default adoption,
> milestone closure, or fusion is authorized. A candidate validation pass is
> limited evidence on these new opaque textured planar fixtures. What would
> overturn it: a failed full case/instance/seed, an unsafe core acceptance,
> invalid reference/provenance, or input/source mutation. Stop for Luiz/Chat
> after the report.

### 1. Software checks - Interactive per command; Batch as a group

Create `previews/fsg1/prospective-validation-logs` as a NEW directory.
Capture stdout/stderr and exit codes separately for every command.

```bash
.venv/bin/python tools/dev/check_fsg.py --self-test --repo-check --report previews/fsg1/prospective-validation-logs/legacy.json
.venv/bin/python tools/dev/check_fsg_coverage_audit.py --self-test --report previews/fsg1/prospective-validation-logs/audit.json
.venv/bin/python tools/dev/check_fsg_hdr.py --self-test --report previews/fsg1/prospective-validation-logs/hdr.json
.venv/bin/python tools/dev/check_fsg_validation.py --self-test --report previews/fsg1/prospective-validation-logs/new.json
.venv/bin/python tools/dev/check_fsg_validation.py --negative visibility
.venv/bin/python tools/dev/check_fsg_validation.py --negative leakage
.venv/bin/python tools/dev/check_fsg_validation.py --negative geometry
```

Expected: 24 legacy checks including the workstation rig, 29 audit, 34 candidate,
48 new checks; all zero failures. The last three commands must each exit 1 with
its intended failure, not an unrelated import error. Verify the actual wording.
Use `python -m py_compile` on all four new scripts as well.
Do not weaken a test, frozen hash, or target to continue.

### 2. Small fixture acquisition and smoke comparison - Batch ceiling

```bash
blender -b --python-exit-code 1 -P tools/fsg_validation_render.py -- --out previews/fsg1/validation-small-seed31 --profile small --seed 31 --device OPTIX --save-blend
.venv/bin/python tools/fsg_validation_eval.py previews/fsg1/validation-small-seed31 --mode smoke --out previews/fsg1/validation-small-evaluation
```

The Blender command must exit 0, with both original `[fsg-render]` lines and the
new `[fsg-validation-render] COMPLETE` marker. Inspect `run.json` and the
specification; the completion message alone is not sufficient.
The comparison returns 0 for all numerical checks passing, 2 for a completed
comparison with numerical misses, 1 for an exception. Both 0 and 2 allow the
prescribed full acquisitions; 1 stops. Preserve the log and every numerical miss.
Do not let a shell `set -e` mistake an anticipated exit 2 for a software exception.
For example, capture an evaluator command using `rc=0; command >log 2>&1 || rc=$?`,
then print its log and inspect rc explicitly.

Actually inspect both `validation.png` files, rectified images, PLYs, JSON
metrics, and the occlusion masks. Confirm right-side foreground, nonempty
left-eye half-occlusion, fixed-head coordinates, correct scale and labels.
A successful-looking RGB picture is not a numerical pass.

### 3. Two full acquisitions - Batch, not Overnight

```bash
blender -b --python-exit-code 1 -P tools/fsg_validation_render.py -- --out previews/fsg1/validation-full-seed31 --profile full --seed 31 --device OPTIX --save-blend
blender -b --python-exit-code 1 -P tools/fsg_validation_render.py -- --out previews/fsg1/validation-full-seed73 --profile full --seed 73 --device OPTIX --save-blend
```

No intervening estimator, fixture, light, exposure, texture, or sample-count
change. A failed acquisition stops; preserve its partial record. No self-authorized
replacement seed or rerender. Expected total runtime is comfortably below five
minutes based on the previous workstation reports, but this is an estimate.
An unexpected cost beyond the Batch class requires a new decision, not an
unreported Overnight run or CPU fallback.

### 4. Frozen paired validation - Batch ceiling

```bash
.venv/bin/python tools/fsg_validation_eval.py previews/fsg1/validation-full-seed31 previews/fsg1/validation-full-seed73 --mode full --out previews/fsg1/validation-full-evaluation
```

The validator requires **both** full seeds. It reports every numerical result
before returning 0 or 2. An integrity/provenance/reference exception exits 1.
Never replace the two-seed outcome with the better seed. Never pass
`--allow-synthetic` on a workstation measurement.

Expected status is either `FROZEN_CANDIDATE_VALIDATION_PASS` or
`FROZEN_CANDIDATE_VALIDATION_FAIL`; which one is unknown. In both cases,
`adopted_default`, `full_profile_milestone_pass` and `fusion_authorized` stay false.
Actual visuals and both candidate PLYs per seed must be inspected, not merely
listed. Missing regions remain missing.

### Likely failures and delegated fixes

1. A numerical miss on the new tilted/background surface, or nonzero accepted
   monocular core. This is a result. The instrument, reference, cutoff, window,
   fixture, spp and seeds MUST NOT be changed. Finish prescribed comparisons if
   integrity holds; stop for Chat/Luiz.
2. Frozen hash, existing output, stale branch, changed spec or versions. Stop;
   do not refresh hashes, delete an old result, or upgrade packages to continue.
3. An actual new orchestration/I/O bug. Code may diagnose and make the minimum
   fix outside the checks, explaining the diff and rerunning software controls.
   This does not authorize a second real acquisition or altered experiment;
   request a decision if either is required.
4. Blender triangulation/API mismatch. The helper already accepts both valid
   quad diagonals. Do not loosen geometric tolerance, substitute synthetic
   acquisition, or disable independent projection/ray checks. Diagnose and stop
   if a change would alter acquisition or require another render.

No other operation is delegated. In particular: no default adoption, no
surface fusion, no saccade policy, no HDR parameter sweep, no masking away an
unsafe correspondence after inspecting truth.

### Required report and repository updates

Fill the Results section below, append measured results to `docs/log.md`, append
an outcome to D-FSG1d without rewriting its prospective text, and update the
README row with the exact scope/status. Commit and push documentation; include
any permitted orchestration fix with an explicit explanation. Do not commit
`previews/`, renders, generated `.blend` files or point clouds.

Return a paste-ready report containing:

1. HEAD before/after, branch, push, prospective decision timing; preserved old failures; empty frozen-source diff.
2. Versions/backend; software SUMMARY lines and all three negative exits/FAIL lines verbatim; every unexpected failure.
3. Exact commands, new paths, per-case seeds, specification and source hashes; independent Blender projection/raycast checks; texture independence from seed/eye.
4. Small/full, each seed/case/instance: legacy and candidate reference counts, coverage, median/P95 errors, fraction above 3%, original gate failures. No pooled substitute.
5. Per instance: common/gained/lost/neither counts and errors, especially newly accepted and lost support. Label small cohorts and never infer calibrated confidence from a pass.
6. Per step/seed: raw and core singly visible reference/accepted counts, core erosion, false-acceptance fraction, exact safety status; all raw perimeter results; NOT_EXERCISED elsewhere.
7. Boundary reference count, coverage and errors; wrong-instance counts; clipping and score distributions from the saved paired metrics.
8. All source-record fingerprints unchanged; evidence predictions were saved before truth use; point counts, head-frame geometry and what was actually seen in each inspected visual.
9. Actual primary samples per run and total, render/oracle/stereo/evaluation/wall times; separate calculated budgets from measurements.
10. Exact final status and process exits, all true/false flags, changed files, no default or fusion adoption, stopped for Luiz/Chat.

## Results

Run 2026-09-19 on the workstation by Code. Every number is read from files under
`previews/fsg1/validation-*`. Chat's analytic record in
`docs/fsg1-prospective-validation-checks.md` is untouched and none of its numbers
is repeated here as a real result.

**Status `FROZEN_CANDIDATE_VALIDATION_FAIL`.** Two independent failures, on top of
one clear success. `adopted_default`, `full_profile_milestone_pass` and
`fusion_authorized` are all false, as is `prospective_blender_validation_pass`.

### Integrity

HEAD `af9ec3876b40a01a74371b024df20635a99839b1` on clean `main`, `edfe1d2` verified
an ancestor. The diff from `edfe1d2` over the fifteen original, audit and HDR
candidate modules, `rig.py`, `bl_common.py` and `requirements-fsg.txt` is EMPTY
before and after, and `fsg_validation_scene.check_frozen()` confirmed all eight
pinned hashes against this checkout. Only six files were added by the handoff.
Spec digest `c7f8c67b56c73321315c1b32750fcec36de86af267eaec51433fbfc1730a7299`,
echoed by every `[fsg-validation-render] COMPLETE` line and stored in each
`run.json`. Python 3.12.3, NumPy 2.2.6, OpenCV 4.13.0, Pillow 12.3.0; Blender
5.2.1 LTS on OPTIX (RTX 4090). No pin moved.

Read before running: the Blender-side modules import only NumPy and repository
modules - no OpenCV or Pillow - the CLI exposes no `--spp` or `--case` override,
seeds are restricted to (31, 73) with small restricted to 31, and the fixtures
match the frozen spec. D-FSG1d was appended and a prospective `docs/log.md` entry
written BEFORE any acquisition.

Checks: `[fsg-check] SUMMARY passed=24 failed=0 seconds=1.875`,
`[fsg-audit-check] SUMMARY passed=29 failed=0 seconds=1.994`,
`[fsg-hdr-check] SUMMARY passed=34 failed=0 seconds=2.381`,
`[fsg-validation-check] SUMMARY passed=48 failed=0 seconds=1.917`, all
`blender_executed=False`; `py_compile` clean on all four new scripts. The three
deliberate negatives each exit 1 with their intended wording:

    [fsg-validation-check] FAIL ValueError: half-occlusion NOT_EXERCISED: raw reference too small
    [fsg-validation-check] FAIL AssertionError: accepted 1 singly-visible core pixels; limit=0
    [fsg-validation-check] FAIL ValueError: exported Blender mesh disagrees with frozen validation specification

`inputs_unchanged: true` over 32 new record paths, `predictions_saved_before_truth:
true` and `original_interior_gates_unchanged: true` for all four full case-records.
The 295 files of every prior seed-17 record and analysis output re-hashed
byte-identical. Per-eye independent Blender checks, 242 rays each, all IDs
matching: projection max 2.353e-04 px (tilted) and 8.609e-05 px (step), ray-cast
max 6.433e-07 m and 7.313e-07 m, against limits of 0.002 px and 20 um.

Seed independence is as designed: `evaluation_only/mesh.npz` and
`calibration.json` are byte-identical between seeds 31 and 73, and so are both
instance masks, while RGB differs only by Monte Carlo noise (mean |delta| 0.000643
tilted, 0.002459 step). Two seeds are two noise realisations of ONE geometry.

### Full profile, both seeds, legacy and candidate on the same fixed reference

| seed / case / instance | ref | legacy cov / med / p95 | candidate cov / med / p95 | >3% (cand) | gate |
| --- | ---: | --- | --- | ---: | --- |
| 31 / tilted_holdout | 65536 | 99.951% / 0.258% / 1.123% | 99.763% / 0.251% / 1.106% | 0.026% | **pass** |
| 73 / tilted_holdout | 65536 | 99.962% / 0.258% / 1.109% | 99.768% / 0.251% / 1.092% | 0.006% | **pass** |
| 31 / step_right inst 1 (1.8 m) | 25088 | 96.959% / 0.195% / 0.722% | 99.868% / 0.183% / 0.705% | 0.000% | **pass** |
| 73 / step_right inst 1 | 25088 | 96.939% / 0.194% / 0.717% | 99.904% / 0.182% / 0.706% | 0.000% | **pass** |
| 31 / step_right inst 2 (3.2 m) | 33536 | 96.338% / 1.053% / 3.123% | 96.225% / **1.053%** / **3.123%** | 10.471% | **FAIL** |
| 73 / step_right inst 2 | 33536 | 96.246% / 1.060% / 3.127% | 96.225% / **1.066%** / **3.127%** | 11.097% | **FAIL** |
| 31 / step_right pooled | 58624 | 96.604% / 0.461% / 3.123% | 97.784% / 0.441% / **3.123%** | 5.894% | **FAIL** |
| 73 / step_right pooled | 58624 | 96.542% / 0.462% / 3.123% | 97.800% / 0.447% / **3.127%** | 6.246% | **FAIL** |

Verbatim numerical failures, identical in kind on both seeds:

    [fsg-validation] NUMERICAL_FAIL step_right: p95_relative_range_error=0.031234338696499123 fails max 0.03
    [fsg-validation] NUMERICAL_FAIL step_right: instance_2_interior: median_relative_range_error=0.010527498989871946 fails max 0.01
    [fsg-validation] NUMERICAL_FAIL step_right: instance_2_interior: p95_relative_range_error=0.031234339254543362 fails max 0.03
    [fsg-validation] NUMERICAL_FAIL step_right: accepted 2 singly-visible core pixels; limit=0

`wrong_instance_accepted_count` is 0 for legacy and candidate on every case and
seed. Boundary is EXERCISED only on `step_right`: 2,304 reference pixels, 1,261 ->
1,263 accepted at seed 31 (median 0.318% -> 0.301%, p95 1.071% -> 1.034%) and
1,260 -> 1,259 at seed 73. Boundary has no invented pass threshold and the
interior gate does not validate it.

### What passed, and what the candidate contributed

The new tilted plane passes on both seeds by a wide margin, at a gaze
(-12, +8 degrees), a range (2.6 m) and a tilt (-32 degrees) the instrument had
never seen. So the fixed sensor does transfer to new planar geometry.

On the new right-side foreground the candidate reproduces its FSG1c benefit
prospectively: coverage 96.959% -> 99.868% at seed 31 and 96.939% -> 99.904% at
seed 73, gaining 747 and 758 pixels whose independently evaluated errors are
0.166%/0.621% and 0.177%/0.624%, with nothing over 3%. On common support the
candidate is slightly better than legacy everywhere (e.g. 0.195% -> 0.184%). The
legacy zero-score fraction on that surface is 1.375%, which the candidate drives
to 0.000%; median scores halve as before (6.763 -> 3.382), so the mechanism is
again removal of the dead zone, not added contrast.

| seed / case / instance | common | gained | lost | neither | common L -> C med | gained med / p95 |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| 31 / tilted_holdout | 65359 | 22 | 145 | 10 | 0.258% -> 0.251% | 1.264% / 2.921% |
| 31 / step_right inst 1 | 24308 | 747 | 17 | 16 | 0.195% -> 0.184% | 0.166% / 0.621% |
| 31 / step_right inst 2 | 32170 | 100 | 138 | 1128 | 1.050% -> 1.052% | 1.898% / 4.095% |
| 73 / tilted_holdout | 65370 | 14 | 141 | 11 | 0.258% -> 0.251% | 1.414% / 1.966% |
| 73 / step_right inst 1 | 24306 | 758 | 14 | 10 | 0.194% -> 0.183% | 0.177% / 0.624% |
| 73 / step_right inst 2 | 32147 | 123 | 130 | 1136 | 1.057% -> 1.063% | 1.871% / 4.368% |

### Failure 1 - the 3.2 m background, both seeds, both estimators

Legacy and candidate land within 0.006 percentage points of each other on this
surface, so it is NOT a radiometric or encoding failure: that instance has a
0.000% legacy zero-score fraction and no clipping to remove. It is the far-surface
accuracy limit again, and this time it appears at FULL profile.

It is not simply angular resolution either, and the comparison is worth recording
rather than explaining away. The old full seed-17 background sat at 3.4 m with
22.57 px of disparity and PASSED at 0.785%/2.497%; this new background sits closer,
at 3.2 m with about 23.98 px, and FAILS at 1.053%/3.123%. More disparity, worse
result. The measurable difference between them is texture: the new background's
median legacy 5x5 score is 4.430 against the old one's 5.052 (candidate 2.894
against 3.398). Lower local contrast on a more distant surface is consistent with
noisier photometric refinement, but this is an observation from two fixtures, not
an established cause, and the fixture must not be changed to test it here.
10.471% and 11.097% of accepted background pixels exceed 3% relative error.

### Failure 2 - the half-occlusion safety check, which this fixture finally exercises

`step_right` does what the old `step` could not. The left-eye singly visible
reference is nonempty at both profiles and both seeds: **4,608 raw and 3,528 core
pixels** at full (2 px erosion), 1,280 and 1,008 at small, comfortably above the
required 256/128 and 64/32. `tilted_holdout` correctly reports `NOT_EXERCISED`
for this subtest only, at every seed and profile.

| seed | estimator | raw accepted | core accepted | core fraction | safety |
| --- | --- | ---: | ---: | ---: | --- |
| 31 | legacy | 2 | 2 | 0.0567% | **FAIL** |
| 31 | candidate | 2 | 2 | 0.0567% | **FAIL** |
| 73 | legacy | 2 | 0 | 0.000% | pass |
| 73 | candidate | 0 | 0 | 0.000% | pass |

The criterion is exactly zero and seed 31 violates it. Read from the saved
outputs, the four offending pixels are geometrically impossible matches whose
truth is the background at 3.20 m:

* candidate (row 83, col 145) and (84, 145): estimated Z = -1.8240 m, essentially
  ON the 1.8 m foreground plane - a **1.377 m** range error, about 43%.
* legacy (106, 133) and (107, 133): estimated Z = -2.5521 and -2.5575 m, a
  physically nonexistent intermediate depth - **0.648 m** and **0.643 m** error.

Every existing veto passed on all four: left-right residual 0.148-0.359 px against
a 1.0 px tolerance, texture std 5.5-8.1 against a 0.5 cutoff, and the oracle
instance label correct. That is the point of the new test - these errors live in
the singly visible population, which the interior reference excludes, so no
interior metric would ever have seen them.

Two attributions matter. The leak is **not** attributable to the HDR candidate:
legacy accepts the same two core pixels on seed 31, and on seed 73 the candidate
is strictly safer than legacy (0 raw accepted against 2). The weakness is in the
shared matcher and acceptance rules. And it is **seed-dependent**: identical
geometry, different Monte Carlo noise, 2 leaked pixels versus 0. A single passing
seed would therefore not have demonstrated safety, which is an argument for the
two-seed schedule rather than against it.

### Visuals and artifacts actually inspected

Small seed 31, both cases; full seeds 31 and 73, `step_right` and
`tilted_holdout`, plus both candidate PLYs per seed. In every `step_right` sheet
the legacy RGB shows a blown-out vertical strip on the RIGHT with the textured
background to its left - the reversed occluding edge - and the candidate panel
recovers texture in that strip. Validity is high for both estimators with the
occlusion and boundary bands excluded; "new accepted interior" lights up on the
right foreground. The accepted-interior error panel is dark on the foreground and
heavily white across the background, which is the instance-2 failure visible in
the image rather than only in the table. The truth singly visible strip sits at
the foreground's left edge, exactly where a right-eye occlusion belongs, and the
eroded core is its narrower interior. The "unsafe accepted occlusion core" panel
is a single minute white mark at seed 31 and entirely black at seed 73.
`tilted_holdout` shows full validity, no occlusion reference and an empty unsafe
panel. Missing regions are shown missing; nothing is interpolated or filled.

Candidate PLYs, all head-frame with no faces: seed 31 `tilted_holdout` 65,381
vertices (instance 1, Z median -2.5458 m) and `step_right` 58,590 (26,318 at
-1.8006 m; 32,272 at -3.2007 m); seed 73 65,384 and 58,593 with the same medians
to four decimals. Against the frozen spec of -1.8 m and -3.2 m, and the small
record's independently measured foreground X range [+0.010, +0.159] m and
background [-0.387, -0.038] m, the fixture is built and recovered as specified.

### Cost

Calculated budget 26,214,400 + 419,430,400 + 419,430,400 = **865,075,200** primary
camera samples; actually recorded 26,214,400 at small and 419,430,400 per full
seed, matching exactly. Inference added **0** new primary samples. Measured:
Blender wall 1.705 s (small), 3.964 s (full 31), 3.899 s (full 73); in-script
`total_wall_seconds` 1.139 / 3.429 / 3.345; render L+R per case 0.264/0.234,
0.970/1.027, 0.956/1.033 s; oracle annotation 0.047-0.058 s at small; smoke
evaluation 0.851 s, paired full validation 6.381 s. Batch class throughout, far
below the five-minute ceiling. Process exits: renders 0, smoke evaluation 2,
paired validation 2 - completed with numerical misses, never an integrity
exception.

### What this settles and what it does not

The instrument transfers to a genuinely new planar geometry, and the HDR
candidate's coverage benefit reproduces prospectively on a fixture it was not
selected on. That is real evidence and it is the first of its kind in FSG1.

It is nonetheless a validation FAIL, for two reasons neither of which is tunable
here: a far background that misses the accuracy gate on both seeds for both
estimators, and a half-occlusion safety violation on one seed. Nothing was
changed to soften either - not the instrument, encoding, cutoff, windows,
reference, erosion, fixtures, spp or seeds - and no acquisition was repeated.
The prior FSG1c limitations stand unaltered: the 29-pixel weak-evidence cohort
and the analytic bright-full coverage failure. The earlier seed-17 baselines and
their failures are preserved byte-for-byte.

This remains two opaque textured planar configurations at known poses with oracle
segmentation, and two Monte Carlo seeds are not two scenes. A zero-leak result
on seed 73 is not general occlusion handling; the seed-31 leak shows why. No
default is adopted, FSG1 is not closed, and no fusion is authorized. Stopped for
Luiz and Chat.
