# FSG1e - frozen stage and visibility audit

Execution-only diagnosis using existing observations. This is NOT another
estimator candidate. Read `CLAUDE.md` first. Reference report commit: `d274fac`.

## Decision to record BEFORE execution

Append this block to `DECISIONS.md` if D-FSG1e does not already exist; use the
actual local date. A conflicting identifier is a stop, not permission to rename it.

### D-FSG1e - diagnose refinement and false cycles without changing the instrument

Keep FSG1d's validation FAIL, the HDR candidate, and all earlier results unchanged.
Replay seven existing full-profile pairs and audit raw SGBM, each of the three
frozen refinement updates, and every accepted singly-visible point; no new rays.
Why: the 3.1234% tail is numerically compatible with a refinement cap, and two
false matches pass all existing vetoes. Neither mechanism is established yet.
Overturned if: exact replay/provenance fails or the fixed support/reference cannot
be reproduced; stop rather than interpreting those diagnostics. No default
adoption, milestone closure, gate change, new candidate, or fusion is authorized.

Also add a prospective few-line entry to `docs/log.md` before the audit. Record the
intended seven pairs and that all validation observations reused below are now
DIAGNOSTIC data, not a fresh holdout for any future fix.

## What this step asks

1. Does the failing 3.2 m background have correct/usable discrete SGBM estimates
   that the custom subpixel refinement damages, or was its peak wrong already?
2. Do the error atoms coincide with the +/-0.75 px total refinement bounds? Are
   those updates driven by small centered gradient denominators or by other data?
3. Does the same refiner help the original 3.4 m background, where the initial
   disparity has a different fractional phase? This regression matters: success
   near an integer disparity cannot justify deleting refinement everywhere.
4. For each accepted half-occluded point, is a small LR residual due to averaging
   incompatible right endpoints or to a genuinely self-consistent but wrong
   correspondence? Both are possibilities, not assumed diagnoses.
5. Does the final tail persist at the same positions across the two noise seeds?

From the declared full calibration, the frontoparallel 3.2 m surface has
`d_true = 23.97619842464091 px`. If its SGBM initialization is 24 px and refinement
lands on 24 - 0.75 = 23.25 px, the relative range error along that viewing ray is
`23.97619842464091/23.25 - 1 = 0.03123434084477`, almost exactly the reported seed-31
P95 `0.031234338696499123`. The opposite cap, 24.75 px, gives about 3.12647%.
These are CALCULATIONS from calibration and a hypothetical initialization, not
measurements of actual cap populations. The script must confirm or refute them.

## Files added

- `tools/fsg_failure_audit.py`: exact RGB-only replay/instrumentation, followed by
  evaluation-only stage/occlusion analysis and a paired-seed report.
- `tools/dev/check_fsg_failure_audit.py`: checks and three negative controls.
- This handoff and `docs/fsg1-stage-visibility-checks.md`: instructions and Chat QA.

No existing source is replaced. The original, audit, HDR and validation source
hashes are checked. The tool refuses a different NumPy/OpenCV version from the
saved prediction metadata, an input fingerprint mismatch, or an unequal replay.
Do not upgrade dependencies or loosen equality to bypass a refusal.

## Frozen boundaries and interpretations

The tool copies the refinement arithmetic ONLY to record its intermediate
arrays, and checks its final output exactly against the unchanged original for
all pixels. It separately checks all saved result arrays, both disparity fields,
and the complete acceptance conjunction. No module globals are patched.

All raw/iteration error summaries use the SAME final accepted support for that
instrument and case. They are conditional stage diagnostics, NOT scores of
standalone alternative pipelines. Intermediate stages have not undergone their
own acceptance decisions. The tail cohorts use ground truth ONLY after replay;
they cannot become production selectors.

The denominator is the frozen centered warped-gradient variance, not the existing
texture score and not a calibrated uncertainty. All clipping/denominator
thresholds in the trace are the existing code's thresholds. `CAP_ATOL=1e-6` only
recognizes a float32 bound; it is not a depth-quality tolerance.

The LR endpoint report distinguishes the actual OpenCV interpolated residual
from residuals at the two contributing right pixels. Passing an average does not
imply both endpoints pass; passing both still does not prove correspondence.
Right-bin collision counts use nearest-integer projected bins across accepted
left-raster points. They are approximate sampling diagnostics, not a z-buffer
visibility proof or a proposed veto. ID-boundary distances are not distances to a
true geometric occlusion boundary.

No accepted mask, PLY, replacement disparity or candidate is exported. The new
NPZ files are explicitly diagnostic traces/evaluation arrays. The CSV enumerates
ALL accepted raw singly-visible points and marks which are inside the fixed core.
An empty CSV means no accepted point in that population, not proof of general
occlusion safety. The original FSG1d safety criterion and erosion remain unchanged.

## Code execution prompt

### 1. Preflight - Interactive

Require clean `main`, `d274fac` as an ancestor, and no D-FSG1e collision. Verify no
instrument changes have appeared since that report. Read the report's numerical
and safety failures. Record the decision and prospective log entry above. Read
`docs/fsg1-stage-visibility-checks.md`, including limitations.

Create NEW `previews/fsg1/stage-visibility-logs` and require that the audit output
`previews/fsg1/stage-visibility-audit` does not exist. Preserve stdout, stderr and
exit codes. Use the existing `.venv`, not Blender's Python. Record versions.

### 2. Regression and new software checks - Interactive each (Batch if >10 s)

```bash
.venv/bin/python tools/dev/check_fsg.py --self-test --repo-check --report previews/fsg1/stage-visibility-logs/original.json
.venv/bin/python tools/dev/check_fsg_coverage_audit.py --self-test --report previews/fsg1/stage-visibility-logs/coverage.json
.venv/bin/python tools/dev/check_fsg_hdr.py --self-test --report previews/fsg1/stage-visibility-logs/hdr.json
.venv/bin/python tools/dev/check_fsg_validation.py --self-test --report previews/fsg1/stage-visibility-logs/validation.json
.venv/bin/python tools/dev/check_fsg_failure_audit.py --self-test --report previews/fsg1/stage-visibility-logs/stage.json
.venv/bin/python -m py_compile tools/fsg_failure_audit.py tools/dev/check_fsg_failure_audit.py
```

Expected all checks pass. Chat obtained 37 new passes in its environment; do not
use this count as a substitute for the actual SUMMARY and individual checks.

Run each negative separately; ALL must exit 1 with a meaningful FAIL:

```bash
.venv/bin/python tools/dev/check_fsg_failure_audit.py --negative cap
.venv/bin/python tools/dev/check_fsg_failure_audit.py --negative replay
.venv/bin/python tools/dev/check_fsg_failure_audit.py --negative cycle
```

Do not chain expected-failing commands with `&&`. No accuracy result is inferred
from these synthetic controls. The cycle control is an intentionally constructed
cancellation example, not a claim that the actual leaks use that mechanism.

### 3. Fixed real-record audit - Batch, estimated under 5 minutes

First verify these exact acquisition/prediction directories exist and are complete:

- `previews/fsg1/full-seed17/{fronto,tilted,step}/stereo`
- `previews/fsg1/hdr-candidate-seed17/full-seed17/{fronto,tilted,step}/stereo_candidate`
- `previews/fsg1/validation-full-seed31/{tilted_holdout,step_right}`
- `previews/fsg1/validation-full-seed73/{tilted_holdout,step_right}`
- `previews/fsg1/validation-full-evaluation/validation-full-seed{31,73}/{tilted_holdout,step_right}/{stereo_legacy,stereo_candidate}`

Run exactly once in a NEW output directory:

```bash
.venv/bin/python -u tools/fsg_failure_audit.py \
  --development previews/fsg1/full-seed17 \
  --development-results previews/fsg1/hdr-candidate-seed17 \
  --validation previews/fsg1/validation-full-seed31 previews/fsg1/validation-full-seed73 \
  --validation-results previews/fsg1/validation-full-evaluation \
  --out previews/fsg1/stage-visibility-audit
```

No `--allow-synthetic` on workstation records. No small/1024-spp acquisition is
part of this audit. The original development three-case suite is a contrast and
regression reference, not a new test. All 14 instrument/pair combinations replay.

The script fingerprints ALL files below these five input roots, including older
candidate outputs, before and after. Snapshotting can dominate runtime if `.blend`
files are large. Camera samples added: exactly zero. Measure processing and hash
cost; do not infer rendering cost from the original nominal budget.

Expected exit 0 means the AUDIT completed with equal replay, not that FSG1 passed.
Any integrity exception stops the step immediately. Outputs without final
`audit.json` are INCOMPLETE and must not be used as a completed audit. Do not
rerender missing files; stop and report the missing artifact.

### 4. Read the results - Batch, human inspection required

Inspect `stage_visibility.png` for the original background and each new step,
and at least one tilt. Its stage error images use identical accepted support;
black can be missing, not zero error. Inspect the JSON distributions rather than
inferring cap populations from the image alone.

For the two known seed-31 core leaks, give every row of `accepted_occlusions.csv`
in the paste report (shorten column names, not the substantive data). Also report
any raw-strip points outside the core. Explain whether each trace confirms
endpoint cancellation or a mutually wrong cycle; uncertainty stays explicit.

Read the existing frozen outputs and all current gate results beside the audit.
Do not label any counterfactual stage or rejected point a newly accepted result.
There is no new sweep, no selected threshold, and no permitted pipeline change.

### 5. Write up, commit, push - Interactive

Update this document's Results section, README status row and `docs/log.md` with
measured results and the exact audit command. Preserve all earlier FAIL records.
If an audit bug is demonstrated, only the TWO NEW scripts may be fixed, with a
specific explanation and a regression check that exposes the original defect;
do not weaken checks or edit pinned modules. Stop for Chat if a correction would
change the scientific definition of this audit.

Commit/push documentation and any justified new-audit fix; no generated files.
Do not adopt HDR, remove refinement, change LR/texture gates, alter segmentation,
broaden windows, train a matcher, or start fusion. Chat/Luiz decide the next step.

## Required paste-ready report

1. HEAD before/after; branch; push; decision timing; source hashes and changes.
2. Versions; verbatim check summaries and each negative's exit/FAIL line.
3. Exact inputs/output/command; exact replay; all input hashes unchanged.
4. For each full case/instance and instrument, on FIXED final accepted support:
   reference and accepted counts; raw and iterations 1/2/3 median/P95 range error;
   signed disparity bias/scatter (distribution); false-to-good/good-to-false counts.
5. For the new background specifically: lower/upper cap counts and fraction of
   >3% errors; top disparity atoms; initial/true fractional phase; gradient
   denominator and unbounded-step distributions for tail vs other accepted points.
   State whether actual 24 -> 23.25 hypotheses explain the calculated tail.
6. Original 3.4 m background and tilted regressions: did refinement HELP there?
   Do not replace a global decision with one favorable integer-disparity plane.
7. Every accepted singly-visible point: raw/core membership, coordinates, IDs,
   predicted vs true depth/disparity, all three left updates, right endpoints and
   updates, residuals/supports, interpolation weights, ID-boundary distances,
   approximate collision counts. No claim that matching IDs proves visibility.
8. Same-support cross-seed correlations, bad-pixel overlap/Jaccard, and uncertainty.
   Two seeds of one geometry cannot establish independence or generalization.
9. Visuals inspected; runtime; zero new camera samples; unexpected failures/fixes.
10. Explicit flags: audit only, prior validation FAIL, no default/milestone/fusion.

## How Chat will use the report

A cap-dominated tail with good raw estimates motivates a separately specified
refinement/conditioning candidate, NOT a bigger cap or unbounded optimization.
Wrong raw peaks require a different response. Mixed evidence may require both.
If endpoint cancellation explains the leaks, examine that implementation detail;
if both endpoints support the wrong match, endpoint checking alone is insufficient
and the acceptance model needs stronger correspondence/visibility evidence.
Neither branch authorizes a fix automatically. Test any later candidate against
all preserved records and eventually new validation; these seeds are now used.

## Results

Pending Code execution. No workstation observations measured by Chat in this step.
