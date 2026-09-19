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

Pending workstation execution. No real Blender result is claimed in this note.
