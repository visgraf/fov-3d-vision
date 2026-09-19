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

Pending Code execution. Chat's separate software-validation record is
`docs/fsg1-supported-checks.md`; synthetic results are not Cycles measurements.
