# FSG1f - One update and footprint-supported reciprocity

Status at handoff: **unmeasured on the workstation Cycles records**. This is one
opt-in candidate plus two fixed ablation controls. No default adoption, FSG1
closure, fusion, new rendering, or fresh-validation claim is authorized.

Base reviewed: `7073594` (Code's FSG1e report). Read `CLAUDE.md` first.

## 1. Decision to append BEFORE execution

Check that `D-FSG1f` does not already exist. If it does, stop rather than duplicating it.
Append this block to `DECISIONS.md` and a prospective entry to `docs/log.md`:

```text
## D-FSG1f - One update and footprint-supported reciprocity (2026-09-19)
Authorize one opt-in HDR candidate: exactly one original photometric update, separate checks on all positive-weight right disparity contributors, and full 5x5 reciprocal support around both matched endpoints. Encoding, matcher settings, geometric calibration, original vetoes, reference masks and numerical evaluation gates remain unchanged.
Why: FSG1e confirms damaging repeated updates and mixed interpolation failures, including one self-consistent wrong cycle. Report one-update-only and endpoint-only controls to separate geometry changes from support rejection; neither is an automatic fallback candidate.
Run the seven existing full-profile pairs once, replay both stored baselines exactly, persist RGB-only predictions before evaluation and preserve all historical failures. Seeds 17/31/73 are development/diagnostic data; no new rays, tuning, default, closure or fusion is authorized.
Overturned if: source/provenance/replay/reference integrity fails, or the named candidate fails any unchanged full per-instance interior gate or the existing zero-accepted-occlusion-core rule. Complete numerical comparisons, then return the results; never select whichever control happens to pass.
```

## 2. What the report supports, and what remains interpretation

FSG1e measured, on the original final accepted support:

- On the seed-31 legacy 3.2 m background, raw / first update / third update
  median-P95 errors were 0.099/0.359%, 0.386/1.650%, and 1.053/3.123%.
  Roughly 88% of the final >3% errors were at a refinement cap. The measured
  disparity atoms were 24 -/+ 0.75 pixels. The original SGBM estimate was
  already close to the true 23.976198-pixel disparity at many points.
- On the older 3.4 m background, raw / first / third were 1.620/1.888%,
  0.328/1.135%, and 0.785/2.497%. Removing refinement would regress that case.
- Of six accepted singly visible points across the old instrument variants,
  five depended on interpolation of incompatible endpoints. One had zero weight
  on its second endpoint: its valid single-endpoint cycle was still wrong.
- The seven observations have now been inspected and are not held-out data.

The selected one-update rule is a SMALL ENGINEERING CANDIDATE based on those
observations, not a proof of optimal stopping or a correction of every numerical
conditioning problem. The one-step gradient denominator is unchanged and may
still be ill-conditioned. The original 0.5-pixel per-update clip is retained;
the old 0.75-pixel total cap is unreachable from the initial value in one update.

Do not infer a universal rule from disparity phase. SGBM emits subpixel values;
these fixtures also differ in texture, gradients, geometry and noise. The old
background remains a mandatory regression case.

## 3. Exact algorithm, frozen before the workstation comparison

### 3.1 Geometry candidate

Keep the FSG1c fixed HDR encoding, the original SGBM calls and all their settings.
Replace `range(3)` in the original refiner with `range(1)` in an additive module.
Everything inside that first update is identical, in both eyes. The checker
compares its source structurally and independently checks exact equality with
the existing audit's first stage. No module globals are monkey-patched.

The **one_step_control** recomputes the entire original validity predicate at
those newly estimated disparities, including its old interpolated LR check.
It is not scored using the old third-update acceptance mask.

### 3.2 Positive-weight endpoint consistency

Let `q = u - d_L(u)`, `j0 = floor(q)`, `j1 = j0 + 1`, and `a = q - j0`.
The interpolation weights are `(1-a, a)`. Every contributor with STRICTLY POSITIVE
weight must be in range, supported, have the same oracle instance ID, and satisfy

```text
abs(d_L(u) + d_R(j)) <= existing LR_TOLERANCE_PX = 1.0
```

Test each contributor separately, not their weighted residual. Ignore exactly
zero-weight contributors: rejecting an unused invalid neighbour would be a bug,
not a visibility safeguard. Use the floating coordinate without rounding it to
OpenCV's interpolation table. The old LR predicate is still retained in the
final intersection; this is an additional veto, not a relaxed replacement.

The **endpoint_control** is the one-step result intersected with this left-to-right
endpoint predicate. It explicitly does NOT solve a self-consistent wrong match.

### 3.3 Footprint-supported reciprocity

Compute the endpoint predicate in BOTH directions. At a pixel in either image,
require every member of the existing `BLOCK_SIZE x BLOCK_SIZE = 5 x 5` footprint
to pass its OWN endpoint predicate. Also require that full support at every
active right contributor of the left candidate match.

This is implemented by constant-zero-border binary erosion of each reciprocal
support map and exact active-contributor sampling in the other eye. It does NOT
require all disparities in a footprint to be equal: a slanted surface may have
a different valid disparity at each pixel. Texture scores are NOT eroded; the
existing centre texture veto is unchanged. Geometry, truth and evaluation masks
play no part in constructing this support.

The named **candidate** is:

```text
fresh one-step original validity
AND active endpoint agreement
AND full reciprocal footprint in the left image
AND full reciprocal footprint at every active right contributor
```

The two-sided rule can remove more than a simple two-pixel outline. It can also
reject correct interior points next to missing correspondences, narrow objects,
or difficult boundaries. All of that cost is charged against the UNCHANGED
reference coverage. Do not shrink reference masks to accommodate the candidate.

This is a conservative spatial-support hypothesis, NOT a complete visibility
model. A sufficiently large, mutually consistent but wrong disparity field can
still pass. A software test explicitly demonstrates this limitation. A zero
leak count on these fixtures is an observed result, not a theorem.

## 4. Fixed comparison, not a parameter search

Report these columns in this order:

1. Stored/freshly replayed three-update **legacy baseline**.
2. Stored/freshly replayed three-update **HDR baseline**.
3. Fresh **one_step_control**, with its own recomputed original validity.
4. **endpoint_control**, same fresh geometry with endpoint-only additional veto.
5. The named **candidate**, same fresh geometry with full reciprocal footprint.

The last three share the same newly computed disparity arrays; their supports
are nested. They isolate accuracy changes from rejection changes. The named
candidate is fixed in advance: do not choose a control as the winner afterward.
No alternate iteration count, tolerance, window, encoding, seed, noise level,
cap or matcher is offered as a command-line tuning parameter.

Only the following existing FULL records are used:

```text
previews/fsg1/full-seed17
previews/fsg1/hdr-candidate-seed17                  # its saved HDR results
previews/fsg1/validation-full-seed31
previews/fsg1/validation-full-seed73
previews/fsg1/validation-full-evaluation            # saved legacy/HDR results
```

Three original geometries plus two validation geometries at two seeds = seven
pairs. Original data remain byte-identical. No image or geometry is regenerated.
The original small failures remain on record; this comparison is deliberately
limited to the already-declared full reporting configuration, as was FSG1e.

New primary camera samples: exactly zero. Offline inference time is measured.
This does not erase or refund acquisition cost already spent on the records.

## 5. Workstation instructions for Claude Code

### 5.1 Preflight - Interactive

Read the working agreement and this document. Require clean `main`, and:

```bash
git merge-base --is-ancestor 7073594 HEAD
git status --short
.venv/bin/python -c "import sys,numpy,cv2,PIL; print(sys.version); print(numpy.__version__,cv2.__version__,PIL.__version__)"
```

Use the SAME environment as saved predictions. Expected from Code's report:
Python 3.12.3, NumPy 2.2.6, OpenCV 4.13.0, Pillow 12.3.0. Do not upgrade to match
Chat's environment. An environment mismatch is an integrity stop, not permission
to loosen exact replay. Verify all five input directories and saved predictions.
Record D-FSG1f and the prospective log entry now, BEFORE comparison.

Set up logs in a NEW directory `previews/fsg1/supported-candidate-logs` and use
`set -o pipefail` when piping a command through `tee`. A numerical exit 2 is
reported and retained; a source/provenance/logic exception exits 1 and stops.

### 5.2 Software checks - Interactive individually; Batch as one sequence

Run the unchanged regression suites and the new checks. Do not modify checks.

```bash
.venv/bin/python tools/dev/check_fsg.py --self-test --repo-check
.venv/bin/python tools/dev/check_fsg_coverage_audit.py --self-test
.venv/bin/python tools/dev/check_fsg_hdr.py --self-test
.venv/bin/python tools/dev/check_fsg_validation.py --self-test
.venv/bin/python tools/dev/check_fsg_failure_audit.py --self-test
.venv/bin/python tools/dev/check_fsg_supported.py --self-test --report previews/fsg1/supported-candidate-logs/software.json
.venv/bin/python -m py_compile tools/fsg_stereo_supported.py tools/fsg_supported_compare.py tools/dev/check_fsg_supported.py
```

Each of these four negatives must exit 1 with the stated class of failure:

```bash
.venv/bin/python tools/dev/check_fsg_supported.py --negative iterations
.venv/bin/python tools/dev/check_fsg_supported.py --negative cycle
.venv/bin/python tools/dev/check_fsg_supported.py --negative footprint
.venv/bin/python tools/dev/check_fsg_supported.py --negative replay
```

Expected causes, respectively: three updates are not the first update;
interpolated cancellation is not endpoint agreement; isolated endpoint agreement
is not full footprint support; altered stored disparity is not exact replay.

The new suite also checks zero-weight endpoints, a valid constant field's
support semantics, missing-data NaNs, independent fixed-reference evaluation,
truth removal, overwrite refusal, blank images, and the existing zero-core-leak
rule. It contains an explicit known limitation: a coherent wrong cycle field
can pass the support rule. Do not reverse that test to pretend safety is proven.

### 5.3 ONE fixed offline comparison - Batch

Require the output path not to exist. Run once; do not append `--allow-synthetic`.

```bash
.venv/bin/python -u tools/fsg_supported_compare.py \
  --development previews/fsg1/full-seed17 \
  --development-results previews/fsg1/hdr-candidate-seed17 \
  --validation previews/fsg1/validation-full-seed31 previews/fsg1/validation-full-seed73 \
  --validation-results previews/fsg1/validation-full-evaluation \
  --out previews/fsg1/supported-candidate-comparison
```

The comparator replays both saved baselines exactly, computes and saves every
new prediction plus its RGB-only trace BEFORE opening evaluation geometry, and
uses the same fixed reference for all five instruments. Reference intersection
is computed once per pair for efficiency; software tests independently compare
the reused-reference metrics against the original evaluator.

All numerical misses are collected for all seven pairs; do not abort merely
because a control or early case fails. No extra run is authorized afterward.
Input hashes are checked before/after, including historical result files.

No Blender command, additional ray, or external model download is needed.

### 5.4 Interpretation and stopping - Interactive

The named candidate must meet the ORIGINAL gates in every adequately populated
case/instance: coverage >=90%, median relative left-eye range error <=1%, P95
<=3%. The existing FSG1d singly-visible reference and fixed eroded core are
unchanged; zero accepted core points is still required. Empty reference groups
are NOT_EXERCISED, never invented passes.

A candidate pass on all seven records is only
`CANDIDATE_PASS_ON_DIAGNOSTIC_RECORDS`. It supports proposing a fresh validation
later. A miss is `CANDIDATE_FAIL_ON_DIAGNOSTIC_RECORDS`. Both leave:

```text
full_profile_milestone_pass=false
adopted_default=false
fusion_authorized=false
```

Do not adopt an ablation because it passes when the named candidate fails.
Do not weaken the 90% coverage rule for a conservative filter. Do not recast
rejected geometry as completed surface coverage or fill any holes.

### 5.5 Most likely failures and permitted diagnosis

1. **Coverage loss from reciprocal-footprint support.** Read `acceptance_populations`
   and the one-step -> endpoint -> candidate contrasts. This is a candidate
   failure, not an orchestration bug; do not reduce the footprint or change masks.
2. **Residual depth errors after one update.** The gradient conditioning and
   first-step cap remain. Compare the old 3.4 m case and new 3.2 m case; do not
   select different update counts per scene or per true disparity phase.
3. **A self-consistent occlusion leak remains or moves.** Read every row in
   `occlusion_tracking.csv`, including newly appearing leaks. This is possible
   by design; do not claim the support rule proves visibility.
4. **Exact replay/source/environment failure.** Stop immediately and diagnose
   path/version/source differences. No threshold or hash bypass is authorized.
5. **A demonstrated CLI/path/serialization error in the NEW wrapper.** Code may
   correct an execution-only bug outside checks, describe the diff and rerun
   in a new output directory after preserving the failure. Do not change the
   estimator arithmetic, endpoint weights, masks, fixtures, or selection rule.

## 6. Required report

Return a paste-ready report with:

- HEAD before/after, branch/push, D-FSG1f recorded before execution, frozen-source
  diff and exact environment; unchanged original failure statuses.
- Every software summary and negative exit/failure line verbatim. Any fixes,
  their exact scope, and every unexpected exception.
- Exact command, new output paths, source verification, replay, input-preservation
  result, prediction-before-truth and identical-reference flags.
- Per pair AND instance: all five instruments' coverage/median/P95/>3% fractions,
  plus every numerical FAIL line. Keep both seeds separate.
- HDR -> one-step common/gained/lost support and errors, then endpoint and footprint
  rejection counts. In particular: old 3.4 m regression and new 3.2 m background.
- Every previous OR new singly visible accepted location from the CSV: its new
  estimate, which controls accept it, and which predicate rejects it (or fails to).
  Do not assume the previous leak positions remain the only possible ones.
- Fixed raw/core visibility denominators and accepted counts per instrument/seed;
  boundary metrics and wrong-instance counts. Zero support is not safety proof.
- Inspected `supported_comparison.png` images and candidate head-frame PLYs.
  Holes must remain missing; no mesh, fill, registration or fusion is authorized.
- Runtime, zero new primary samples, final status and all non-adoption flags.

Update this document's Results, `DECISIONS.md` (append outcome, preserve old
blocks), `docs/log.md`, and the README FSG row. Do not commit regenerable previews.
Commit and push to main per CLAUDE.md, then stop for Luiz/Chat even on a pass.

## 7. Results

Run 2026-09-19 on the workstation by Code. Every number is read from
`previews/fsg1/supported-candidate-comparison/`. Chat's software record in
`docs/fsg1-supported-checks.md` is untouched and none of its synthetic numbers is
repeated as a Cycles result. **Zero new primary camera samples**; no Blender ran.

**Status `CANDIDATE_PASS_ON_DIAGNOSTIC_RECORDS`**, exit 0,
`candidate_all_gates_pass=true`, `inputs_unchanged=true`, 16.625 s, 7 pairs.
`full_profile_milestone_pass`, `adopted_default`, `fusion_authorized` all false;
`development_data_only=true`. **This is not validation.** Seeds 17, 31 and 73 have
all been inspected in earlier steps, so a pass here cannot be relabelled
prospective; it supports proposing a fresh validation later, nothing more.

### Integrity

HEAD `f3eb838cb3219a04e13b1816c9ef2364810b3e12` on clean `main`, `7073594` an
ancestor. The diff from `7073594` over the twenty-one instrument modules, checks,
`rig.py`, `bl_common.py` and `requirements-fsg.txt` is EMPTY before and after;
only five files were added by the handoff and none was modified. Python 3.12.3,
NumPy 2.2.6, OpenCV 4.13.0, Pillow 12.3.0 - the environment that produced the
saved predictions. D-FSG1f and a prospective log entry were recorded BEFORE the
comparison.

`exact_legacy_and_hdr_replay`, `predictions_saved_before_truth` and
`same_fixed_references` are true for all seven pairs. The tool hashed 268 input
files before and after; I re-hashed the same 268 independently: byte-identical.
Before running I read the module and confirmed the frozen spec: `range(1)` with a
structural check admitting only `range(3)` -> `range(1)`; endpoint reciprocity
tested at each strictly-positive-weight contributor separately, no coordinate
rounding, exactly-zero-weight neighbours ignored; 5x5 reciprocal footprint in the
left image and at every active right contributor; the old interpolated LR check
retained in the intersection.

Checks: `[fsg-check] passed=24 failed=0`, `[fsg-audit-check] passed=29 failed=0`,
`[fsg-hdr-check] passed=34 failed=0`, `[fsg-validation-check] passed=48 failed=0`,
`[fsg-failure-check] passed=37 failed=0`, `[fsg-supported-check] passed=46
failed=0`, all `blender_executed=False`; `py_compile` clean on all three new
files. The four negatives each exit 1:

    [fsg-supported-check] FAIL AssertionError: first update must equal stage 1, not the old three-update result
    [fsg-supported-check] FAIL AssertionError: averaged cancellation must not pass the endpoint gate
    [fsg-supported-check] FAIL AssertionError: isolated endpoint agreement does not establish patch support
    [fsg-supported-check] FAIL ValueError: replay mismatch in disparity_px; no counterfactual analysis authorized

No unexpected exception occurred and no script was fixed.

### All five instruments, per pair and instance (gates 90% / 1% / 3%)

Coverage / median / p95 / fraction over 3%, on the unchanged fixed reference.

| pair / instance | ref | legacy | hdr | one_step | endpoint | **candidate** |
| --- | ---: | --- | --- | --- | --- | --- |
| s17/fronto inst 1 | 65536 | 94.786/0.284/1.159/0.000 | 99.019/0.284/1.112/0.000 | 99.104/0.098/0.359/0.000 | 99.104/0.098/0.359/0.000 | **99.104/0.098/0.359/0.000** |
| s17/tilted inst 1 | 65536 | 98.433/0.319/1.348/0.000 | 98.912/0.318/1.366/0.000 | 99.062/0.116/0.490/0.000 | 99.054/0.116/0.490/0.000 | **98.892/0.116/0.488/0.000** |
| s17/step inst 1 | 36608 | 79.319/0.137/0.595/0.000 **FAIL** | 99.361/0.142/0.649/0.000 | 99.399/0.055/0.220/0.000 | 99.399/0.055/0.220/0.000 | **99.399/0.055/0.220/0.000** |
| **s17/step inst 2 (3.4 m)** | 24320 | 99.819/0.785/2.497/2.781 | 99.572/0.796/2.572/3.023 | 99.737/0.333/1.176/0.173 | 99.737/0.333/1.176/0.173 | **99.737/0.333/1.176/0.173** |
| s31/tilted_holdout | 65536 | 99.951/0.258/1.123/0.031 | 99.763/0.251/1.106/0.026 | 99.785/0.112/0.448/0.000 | 99.785/0.112/0.448/0.000 | **99.785/0.112/0.448/0.000** |
| s31/step_right inst 1 | 25088 | 96.959/0.195/0.722/0.000 | 99.868/0.183/0.705/0.000 | 99.904/0.103/0.293/0.000 | 99.904/0.103/0.293/0.000 | **99.904/0.103/0.293/0.000** |
| **s31/step_right inst 2 (3.2 m)** | 33536 | 96.338/1.053/3.123/10.830 **FAIL** | 96.225/1.053/3.123/10.471 **FAIL** | 97.090/0.391/1.678/0.175 | 96.988/0.391/1.661/0.138 | **94.555/0.383/1.606/0.035** |
| s73/tilted_holdout | 65536 | 99.962/0.258/1.109/0.020 | 99.768/0.251/1.092/0.006 | 99.786/0.111/0.447/0.000 | 99.786/0.111/0.447/0.000 | **99.786/0.111/0.447/0.000** |
| s73/step_right inst 1 | 25088 | 96.939/0.194/0.717/0.000 | 99.904/0.182/0.706/0.000 | 99.908/0.101/0.293/0.000 | 99.908/0.101/0.293/0.000 | **99.908/0.101/0.293/0.000** |
| **s73/step_right inst 2** | 33536 | 96.246/1.060/3.127/11.386 **FAIL** | 96.225/1.066/3.127/11.097 **FAIL** | 97.006/0.390/1.688/0.111 | 96.923/0.390/1.680/0.102 | **94.665/0.382/1.632/0.000** |

Every `NUMERICAL_FAIL` line emitted belongs to a stored BASELINE, preserved as
historical fact. The named candidate has no fail line on any pair or instance, and
`wrong_instance_accepted_count` is 0 for all five instruments everywhere.

The accuracy change is not marginal. On the same reference the candidate's median
error is roughly a third of the HDR baseline's on every surface, and on the two
failing backgrounds it moves 1.053% -> 0.383% and 1.066% -> 0.382% with p95
3.123% -> 1.606% and 3.127% -> 1.632%. The fraction over 3% collapses from
10.5-11.1% to 0.035% and 0.000%.

### HDR baseline -> one step, on common support

| pair / instance | common | gained | lost | neither | common median | common p95 | common >3% |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| s17/fronto | 64893 | 56 | 0 | 587 | 0.284% -> 0.098% | 1.112% -> 0.359% | 0.000% -> 0.000% |
| s17/tilted | 64823 | 98 | 0 | 615 | 0.318% -> 0.116% | 1.366% -> 0.489% | 0.000% -> 0.000% |
| s17/step inst 1 | 36374 | 14 | 0 | 220 | 0.142% -> 0.055% | 0.649% -> 0.220% | 0.000% -> 0.000% |
| **s17/step inst 2** | 24216 | 40 | 0 | 64 | **0.796% -> 0.333%** | **2.572% -> 1.169%** | 3.023% -> 0.173% |
| s31/tilted_holdout | 65381 | 14 | 0 | 141 | 0.251% -> 0.112% | 1.106% -> 0.447% | 0.026% -> 0.000% |
| s31/step_right inst 1 | 25055 | 9 | 0 | 24 | 0.183% -> 0.103% | 0.705% -> 0.293% | 0.000% -> 0.000% |
| **s31/step_right inst 2** | 32267 | 293 | 3 | 973 | **1.053% -> 0.388%** | **3.123% -> 1.653%** | 10.466% -> 0.152% |
| s73/step_right inst 2 | 32259 | 273 | 11 | 993 | 1.066% -> 0.387% | 3.127% -> 1.666% | 11.079% -> 0.093% |

The improvement is on the SAME pixels, not from a changed support: the common
population is 32,267 of 33,536 on the failing background and its median drops by a
factor of 2.7 while the >3% fraction falls 69-fold. The 3 pixels lost there had a
median error of 4.10% with two-thirds over 3%; the 293 gained sit at 1.03% median.

First-update shifts on accepted support run to the original +/-0.5 per-update clip
and no further, so the old +/-0.75 total cap is unreachable in one update, as the
handoff stated. On the failing background the shift median is -0.037 px.

**The mandatory regression case does not regress.** FSG1e warned that removing
refinement would break the older 3.4 m background, whose true disparity phase is
near half-integer. One update improves it as well: 0.796% -> 0.333% median,
2.572% -> 1.176% p95, coverage 99.572% -> 99.737%, over-3% 3.023% -> 0.173%. One
update is the better stage for both the near-integer and the half-integer surface
on these records; no per-scene update count was used or needed.

### The two additional vetoes, and what they cost

| pair / instance | one_step accepted | rejected by endpoints | rejected by footprint | candidate accepted | total cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| s17/fronto | 64949 | 0 | 0 | 64949 | 0.000% |
| s17/tilted | 64921 | 5 | 106 | 64810 | 0.171% |
| s17/step inst 1 | 36388 | 0 | 0 | 36388 | 0.000% |
| s17/step inst 2 | 24256 | 0 | 0 | 24256 | 0.000% |
| s31/tilted_holdout | 65395 | 0 | 0 | 65395 | 0.000% |
| s31/step_right inst 1 | 25064 | 0 | 0 | 25064 | 0.000% |
| **s31/step_right inst 2** | 32560 | 34 | **816** | 31710 | **2.611%** |
| s73/step_right inst 2 | 32532 | 28 | **757** | 31747 | **2.413%** |

The footprint rule is where the cost sits, and it is concentrated entirely on the
occluded step background: 2.6% and 2.4% of accepted interior, against 0.17% or
nothing elsewhere. Coverage there falls to 94.555% and 94.665%, which still clears
the 90% floor with about 4.5 points to spare. That cost is charged against the
unchanged reference; no mask was shrunk.

Boundary is not gated but the cost there is larger and must be stated: on
`s31/step_right` accepted boundary pixels go 1,279 (one step) -> 1,278 (endpoint)
-> **762** (candidate) of 2,304, and on `s17/step` 2,885 -> 2,801 -> **1,381** of
4,608. Boundary accuracy improves on what remains (s31 median 0.123% -> 0.106%,
p95 0.312% -> 0.293%), but roughly half the boundary population is rejected. The
interior gate does not validate boundary behaviour and this is a real reduction.

### Occlusion: every tracked location, and an honest attribution

Fixed denominators are unchanged: 4,608 raw and 3,528 core singly-visible pixels
per `step_right` seed, `NOT_EXERCISED` on all three `full-seed17` cases and both
`tilted_holdout` seeds (zero reference, never an invented pass).

| instrument | s31 raw / core accepted | s73 raw / core accepted |
| --- | ---: | ---: |
| legacy_baseline | 2 / 2 **FAIL** | 2 / 0 |
| hdr_baseline | 2 / 2 **FAIL** | 0 / 0 |
| one_step_control | 0 / 0 | 0 / 0 |
| endpoint_control | 0 / 0 | 0 / 0 |
| **candidate** | **0 / 0** | **0 / 0** |

`occlusion_tracking.csv` holds six rows - the union of every previously accepted
singly-visible location - and **no new leak appeared anywhere**. All six are
rejected by the candidate. Per row: four at seed 31 are `in_core=True` (two that
the HDR baseline accepted at u=337, v=275/276 with 1.377 m error, and two that the
legacy baseline accepted at u=325, v=298/299 with 0.648/0.643 m error), and the
two seed-73 rows are `in_core=False` raw-strip points the legacy baseline accepted
at 0.571 m error.

The attribution must be stated carefully, because these records cannot separate
the mechanisms. For all six rows `one_step_valid=False` - the one-step original
validity ALREADY rejects every one of them, before either new veto applies - AND
`endpoint_left=False` with `max_active_endpoint_residual` between 7.0 and 43.6 px
against the 1.0 px tolerance, AND `footprint_left=False` and
`supported_cycle=False`. The rejection is redundant three times over. **So this
comparison does not demonstrate that the support rule is what prevents leakage**;
it shows only that the candidate leaks nothing on these records. Zero leaks here
is an observed result on two fixtures at two seeds, not a theorem, and the
software suite deliberately retains a test showing a coherent wrong reciprocal
field can still pass the support rule.

### Visuals and point clouds

Inspected `supported_comparison.png` for `validation-full-seed31/step_right` and
`full-seed17/step`, and the candidate head-frame PLYs for all seven pairs. On the
seed-31 sheet the four instruments share identical RGB; the baseline's
"Interior error / 3%" panel is almost entirely white across the background while
one_step, endpoint and candidate are progressively darker, so the accuracy gain is
visible rather than only tabulated. The candidate's validity panel shows a
slightly wider rejected band at the occlusion strip - the footprint cost, visible
and counted. The "Unsafe accepted occlusion core" panel is a single minute white
mark for the baseline and entirely black for all three new variants.

Candidate PLYs are head-frame with no faces and correct depths: `s31/step_right`
57,536 vertices (25,826 at Z = -1.8015 m; 31,710 at -3.2007 m) and `s73` 57,572
(25,825 at -1.8014; 31,747 at -3.2007) against the frozen -1.8 / -3.2;
`s17/step` 62,025 (-1.6004 / -3.4047); `s17/fronto` 64,949 at -1.9992;
`tilted_holdout` 65,395 / 65,396 at -2.5464 / -2.5460. Missing regions remain
missing - nothing is filled, meshed, registered or fused.

### What this does and does not establish

The named candidate, fixed in advance, meets every unchanged interior gate on all
seven pairs and both instances, leaks nothing into either occlusion population,
and improves accuracy roughly three-fold over the HDR baseline while keeping the
mandatory 3.4 m regression case comfortably better than before. The two controls
are reported for attribution only; the named candidate passed, so no question of
selecting a control arises, and neither is a fallback.

Against that: these seven pairs are development and diagnostic data that produced
the hypothesis, so this is not validation of any kind. The one-step rule is chosen
from FSG1e's evidence, not proven optimal, and the gradient denominator it uses is
still the ill-conditioned one. The footprint rule costs 2.4-2.6% of interior
coverage and roughly half the boundary population on the occluded step, and it can
reject correct interiors near missing correspondences or thin structure. A
spatially coherent wrong reciprocal field can still pass it. All prior failures
stand unaltered: the small-profile misses, the analytic bright-full stress, and
FSG1d's `FROZEN_CANDIDATE_VALIDATION_FAIL` on its own records.

No default adopted, no milestone closed, no fusion, no gate or reference changed,
nothing tuned and no control selected. Stopped for Luiz and Chat.
