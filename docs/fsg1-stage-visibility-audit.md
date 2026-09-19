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

Run 2026-09-19 on the workstation by Code. Every number is read from files under
`previews/fsg1/stage-visibility-audit/`. Chat's QA record in
`docs/fsg1-stage-visibility-checks.md` is untouched and none of its synthetic
numbers is repeated as a real result. **Zero new camera samples**; no Blender ran.

Status `AUDIT_COMPLETE_NOT_A_MILESTONE`, exit 0, 7 pairs / 14 instrument-pair
combinations, `exact_replay=true`, `inputs_unchanged=true`, 15.948 s.
`full_profile_milestone_pass`, `adopted_default` and `fusion_authorized` false.

**Both hypotheses are answered. The refinement-cap explanation is CONFIRMED for
the new 3.2 m background. The leaks are NOT a single mechanism: five of six are
endpoint failures masked by interpolation, one is a genuine self-consistent
wrong cycle.** Neither finding authorizes a change; both are handed back.

### Integrity

HEAD `3ca52de4b7093cbd0ff6b67b6fff1ba12af99270` on clean `main`, `d274fac` an
ancestor. The diff from `d274fac` over the eighteen instrument modules, checks,
`rig.py`, `bl_common.py` and `requirements-fsg.txt` is EMPTY before and after;
the tool independently verified 11 frozen source hashes and recorded its own 2.
Only four files were added by the handoff. Python 3.12.3, NumPy 2.2.6, OpenCV
4.13.0, Pillow 12.3.0, matching the saved prediction metadata. D-FSG1e and a
prospective log entry were recorded BEFORE execution.

`exact_replay`, `no_acceptance_change` and `trace_saved_before_truth` are true for
all 14 combinations. The tool hashed 268 input files before and after and I
re-hashed the same 268 independently: byte-identical. `full-seed17/evaluation.json`
still reads `FAIL` and FSG1d still reads `FROZEN_CANDIDATE_VALIDATION_FAIL`.

Checks: `[fsg-check] passed=24 failed=0`, `[fsg-audit-check] passed=29 failed=0`,
`[fsg-hdr-check] passed=34 failed=0`, `[fsg-validation-check] passed=48 failed=0`,
`[fsg-failure-check] passed=37 failed=0`, all `blender_executed=False`;
`py_compile` clean. The three negatives each exit 1:

    [fsg-failure-check] FAIL AssertionError: lower-cap classification lost its sign
    [fsg-failure-check] FAIL ValueError: replay mismatch in disparity; no counterfactual analysis authorized
    [fsg-failure-check] FAIL AssertionError: interpolated consistency does not establish endpoint consistency

### Question 1 and 2 - the stages, on the FIXED final accepted support

These are conditional stage diagnostics. Intermediate stages never faced their own
acceptance decision, so they are NOT scores of alternative pipelines.

| pair / instrument / instance | n | raw med/p95 | iter 1 | iter 2 | iter 3 = final | bad | good->bad | bad->good |
| --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: |
| s17/fronto/legacy inst 1 | 62119 | 0.787/0.952 | 0.111/0.383 | 0.180/0.792 | 0.285/1.159 | 0 | 0 | 0 |
| s17/tilted/legacy inst 1 | 64509 | 0.366/0.659 | 0.119/0.496 | 0.215/0.944 | 0.318/1.348 | 0 | 0 | 0 |
| s17/step/legacy inst 1 | 29037 | 0.099/0.099 | 0.054/0.208 | 0.094/0.382 | 0.137/0.595 | 0 | 0 | 0 |
| **s17/step/legacy inst 2 (3.4 m)** | 24276 | **1.620/1.888** | 0.328/1.135 | 0.551/1.945 | **0.785/2.497** | 675 | 675 | 0 |
| s31/tilted_holdout/legacy | 65504 | 0.472/0.814 | 0.116/0.454 | 0.178/0.757 | 0.258/1.123 | 20 | 20 | 0 |
| s31/step_right/legacy inst 1 | 24325 | 0.729/0.874 | 0.119/0.313 | 0.129/0.462 | 0.195/0.722 | 0 | 0 | 0 |
| **s31/step_right/legacy inst 2 (3.2 m)** | 32308 | **0.099/0.359** | 0.386/1.650 | 0.741/2.886 | **1.053/3.123** | 3499 | **3482** | 71 |
| **s31/step_right/hdr inst 2** | 32270 | **0.099/0.617** | 0.388/1.654 | 0.743/2.856 | **1.053/3.123** | 3379 | 3370 | 82 |
| **s73/step_right/legacy inst 2** | 32277 | **0.099/0.359** | 0.386/1.662 | 0.740/2.976 | **1.060/3.126** | 3675 | 3667 | 37 |
| **s73/step_right/hdr inst 2** | 32270 | **0.099/0.359** | 0.387/1.667 | 0.741/2.945 | **1.066/3.126** | 3581 | 3568 | 58 |

On the failing 3.2 m background the raw SGBM estimate is **excellent** - median
0.099%, p95 0.359%, comfortably inside a 1%/3% gate - and each refinement update
makes it monotonically worse until it fails. 3,482 of the 3,499 bad pixels were
GOOD before refinement; only 71 went the other way. The peak was not wrong; the
refinement damaged it.

### Question 2 and 5 - the cap is the tail, and the mechanism is a tiny denominator

| pair / instrument / instance | lower cap | upper cap | % accepted | % of bad | init frac (median / at integer) | true frac |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| **s31/step_right/legacy inst 2** | 2057 | 1455 | **10.870%** | **88.45%** | 0.0000 / **90.5%** | 0.976198 |
| s31/step_right/hdr inst 2 | 2134 | 1420 | 11.013% | 87.30% | 0.0000 / 88.6% | 0.976198 |
| s73/step_right/legacy inst 2 | 2004 | 1619 | 11.225% | 88.38% | 0.0000 / 90.3% | 0.976198 |
| s73/step_right/hdr inst 2 | 2066 | 1596 | 11.348% | 88.58% | 0.0000 / 89.7% | 0.976198 |
| s17/step/legacy inst 2 (3.4 m) | 2068 | 158 | 9.170% | 21.78% | 0.8750 / 23.2% | 0.565833 |
| s31/tilted_holdout/legacy | 210 | 149 | 0.548% | 65.00% | 0.0625 / 41.5% | 0.579746 |

The arithmetic in the handoff is confirmed as a measurement, not just a
calculation. The true fractional phase is **0.976198**, i.e. `d_true =
23.976198...` px, and SGBM initialises at exactly integer 24 for **90.5%** of
accepted background pixels. The top two final-disparity atoms are **23.25 px
(1,631 pixels, 5.05%)** and **24.75 px (1,240 pixels, 3.84%)** - precisely
24 - 0.75 and 24 + 0.75. The lower-cap cohort's median relative range error is
**0.031234340844770295** against the predicted `0.03123434084477`, and the
upper-cap cohort's is **0.03126471011551888** against the predicted ~3.12647%.
The reported seed-31 p95 was `0.031234338696499123`. `refinement_shift_px` has
p05 = -0.75 and max = +0.75, and the tail's final disparity p05 is exactly 23.25.

So: **yes, the actual 24 -> 23.25 hypothesis explains the calculated tail.** The
two caps together are ~11% of accepted pixels and **~88% of every pixel over 3%**.

The driver is the frozen centred warped-gradient variance, which is tiny on this
surface. Iteration-1 `gradient_variance` median is 2.20e-05 while
`unbounded_step_px` ranges from -42.19 to +15.86 px: the Gauss-Newton step is
ill-conditioned, gets clipped to 0.5 px per iteration, and accumulates to the
0.75 px total bound. Tail pixels are systematically worse conditioned than the
rest of the same surface:

| pair / instance | tail n | tail median gvar | safe n | safe median gvar | safe/tail |
| --- | ---: | ---: | ---: | ---: | ---: |
| s31/step_right inst 2 | 3499 | 8.083e-06 | 28809 | 2.439e-05 | 3.02x |
| s73/step_right inst 2 | 3675 | 8.554e-06 | 28602 | 2.458e-05 | 2.87x |
| s17/step inst 2 | 675 | 7.866e-06 | 23601 | 3.101e-05 | 3.94x |
| s31/tilted_holdout | 20 | 2.535e-06 | 65484 | 1.007e-04 | 39.71x |
| s73/tilted_holdout | 13 | 2.337e-06 | 65498 | 1.007e-04 | 43.09x |

Cross-seed, the tail is an aggregate regularity with **noise-selected membership**.
On the failing background the signed-error correlation between seeds is only
**0.045** (legacy) and 0.048 (hdr), bad-pixel Jaccard 0.150 and 0.145, with 910 of
6,083 union-bad pixels bad in both, and the per-pixel seed difference spans
-3.91% to +3.85%. By contrast the foreground correlates at 0.711/0.706 with zero
bad pixels, and `tilted_holdout` at 0.810/0.810. So the caps reappear in nearly
identical proportion on both seeds while landing on different pixels - consistent
with an ill-conditioned update taking a noise-driven walk to one bound or the
other. Two seeds of one geometry cannot establish independence or generalisation.

### Question 3 and 6 - the regression: refinement HELPS the original 3.4 m background

This is the decisive counterweight and it must not be skipped. On the original
3.4 m background the true phase is **0.565833** - near half-integer - so the
discrete peak cannot be nearly right: raw median is **1.620%**, which would FAIL
the 1% median gate on its own. Refinement takes it to **0.785%**, a pass. Its
tail shift median is **+0.5232** px, toward truth, and only 21.78% of its bad
pixels are at a cap. The same holds elsewhere: fronto raw median 0.787% -> 0.285%,
tilted 0.366% -> 0.318%, `tilted_holdout` 0.472% -> 0.258%, `step_right`
foreground 0.729% -> 0.195%.

**Deleting the refinement would convert the original background from a pass to a
failure.** The instrument is not simply "better without refinement"; it is better
without it exactly where the true disparity happens to sit near an integer, and
worse without it everywhere else. Any candidate must be judged on both regimes.

### Question 4 - every accepted half-occluded point, all six of them

Six accepted singly-visible points exist across all 14 combinations. Every other
combination, including all three original `full-seed17` cases and both
`tilted_holdout` seeds, has an EMPTY CSV. An empty CSV is not proof of general
occlusion safety.

| record / case / instrument | in core | (u,v) full | d raw | d final | shift | d true | pred Z | true Z | err m |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| s31/step_right/hdr | **True** | (337,275) | 42.8125 | 42.0625 | -0.75 | 23.976 | -1.8240 | -3.20 | 1.377 |
| s31/step_right/hdr | **True** | (337,276) | 42.8125 | 42.0625 | -0.75 | 23.976 | -1.8240 | -3.20 | 1.377 |
| s31/step_right/legacy | **True** | (325,298) | 30.8125 | 30.0625 | -0.75 | 23.976 | -2.5521 | -3.20 | 0.648 |
| s31/step_right/legacy | **True** | (325,299) | 30.7500 | 30.0000 | -0.75 | 23.976 | -2.5575 | -3.20 | 0.643 |
| s73/step_right/legacy | False | (324,297) | 29.9375 | 29.1875 | -0.75 | 23.976 | -2.6287 | -3.20 | 0.571 |
| s73/step_right/legacy | False | (324,298) | 29.9375 | 29.1875 | -0.75 | 23.976 | -2.6287 | -3.20 | 0.571 |

The two seed-73 legacy rows are the raw-strip points OUTSIDE the eroded core, which
is why FSG1d recorded `accepted_raw=2, accepted_core=0` there and scored it a pass;
seed-73 hdr accepted none at all.

| record / instrument | both endpoints pass | interpolated pass | res interp | res x0 | res x1 | weight x1 | x1 supported | ID dist px | right-bin count | texture |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| s31/hdr (337,275) | **False** | True | +0.1479 | **+18.472** | **-1.074** | 0.9375 | True | 3.0 | 1 | 5.714 |
| s31/hdr (337,276) | **False** | True | +0.3588 | **+18.040** | -0.820 | 0.9375 | True | 3.0 | 1 | 5.469 |
| s31/legacy (325,298) | **False** | True | +0.3164 | **+6.938** | -0.125 | 0.9375 | True | 15.0 | 1 | 8.075 |
| s31/legacy (325,299) | **False** | True | -0.2500 | -0.250 | **-82.000** | **0.0000** | **False** | 15.0 | 1 | 7.674 |
| s73/legacy (324,297) | **False** | True | +0.4141 | **+6.000** | -0.875 | 0.8125 | True | 16.0 | 1 | 6.621 |
| s73/legacy (324,298) | **False** | True | +0.3633 | **+6.000** | -0.938 | 0.8125 | True | 16.0 | 1 | 7.241 |

`cycle_both_endpoints_pass` is **False in all six**, while the interpolated check
passes in all six. But the six are not one mechanism, and the distinction matters:

* **One case is true cancellation.** s31/hdr (337,275): neither endpoint passes on
  its own - x0 is +18.47 px and x1 is -1.074 px, already beyond the 1.0 px
  tolerance - yet 0.0625x18.472 + 0.9375x(-1.074) = +0.148 passes comfortably. Two
  failing endpoints cancel into a passing average.
* **Four cases are endpoint masking.** s31/hdr (337,276), s31/legacy (325,298),
  and both s73 rows: the near endpoint passes alone (|res| 0.125-0.938) while the
  far endpoint is 6-18 px wrong, and the 0.8125-0.9375 weight on the passing one
  keeps the average inside tolerance. The check never sees the contradiction.
* **One case is a genuine self-consistent wrong cycle.** s31/legacy (325,299) has
  `weight1_ideal = 0.0`, so the sample sits exactly on x0 = 295 and the
  interpolated residual IS the x0 residual, -0.25 px. The right image at that pixel
  genuinely points back. It is mutually consistent and still wrong by 0.643 m. Its
  x1 neighbour carries an unsupported sentinel (-82.0, `right_x1_supported=False`)
  which contributes nothing at that weight.

So endpoint checking would have caught five of six, and **would not have caught
the sixth**. Endpoint checking alone is necessary-looking but demonstrably
insufficient; the acceptance model needs correspondence/visibility evidence that
a mutually agreeing wrong match cannot satisfy.

Three further observations, none of them a proposed veto. The oracle ID check
passes on all six because both sides carry instance 2 - the match is to another
part of the SAME background, 6-18 px from where the true surface projects
(`right_x_predicted` ~294.9 against `right_x_true_surface` 300-313). Matching IDs
do not prove visibility. `left_id_boundary_distance_px` is 3-16 px, so these are
not pixels hugging an ID edge; and these are distances to a label boundary, not to
a true geometric occlusion boundary. `right_bin_accepted_count` is 1 with
`right_bin_max_disparity_minus_this` 0.0 on every row, so the approximate
right-bin collision diagnostic would not have flagged any of them either.

Finally, **all six leaks also sit at exactly the -0.75 px cap**, with unbounded
steps of -0.33 to -13.72 px. The cap did not cause the leak - SGBM's initial peak
was already grossly wrong at 42.8 / 30.8 / 29.9 px against a true 23.976 - but the
same ill-conditioned update that produces the interior tail is running to its
bound here too. The two failures share the conditioning symptom.

### Visuals inspected

`stage_visibility.png` for `validation-full-seed31/step_right` (legacy and hdr),
`validation-full-seed73/step_right`, `full-seed17/step` (the original background)
and `validation-full-seed31/tilted_holdout`. On the new step the "Raw SGBM error /
3%" panel is almost entirely black across the background, "After update 1" shows
visible speckle, and "After update 3" is heavily white - the degradation is
visible, not only tabulated. The "At -0.75 or +0.75 cap" panel is a dense speckle
over the same region. "Accepted in occlusion core" is black but for one minute
mark at seed 31. "Cycle interpolation pass only" is a scattered population
concentrated along the occlusion strip, which is where cancellation-prone geometry
lives. The original `full-seed17/step` panel is the exact converse: its raw
background is uniformly mid-grey (~1.6-1.9%) and update 1 visibly darkens it, with
an empty occlusion core. Black can mean missing rather than zero error; the
support panel is read separately and nothing is interpolated or filled.

### Cost and flags

Runtime 15.948 s total, wall 16.130 s, including hashing 268 input files twice.
**New primary camera samples: exactly 0.** No rendering, no acquisition, no
estimator change, no acceptance change, no new candidate, no threshold selected,
no sweep. No audit bug was demonstrated and neither new script was modified.
No unexpected failure occurred.

This is an audit only. FSG1d's `FROZEN_CANDIDATE_VALIDATION_FAIL` stands, as do
the seed-17 baselines, the FSG1c limitations and the two seed-31 core leaks. No
default adopted, no milestone closed, no gate changed, no fusion. The reused
validation observations are now diagnostic data and are no longer a fresh holdout.
Stopped for Luiz and Chat.
