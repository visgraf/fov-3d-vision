# FSG1b: diagnose coverage loss without changing the instrument

Date: 2026-09-19. Chat implementation and Code execution handoff.
Basis: Code-report-FSG1-followup.md, reported HEAD 8ac6137, the frozen initial
FSG1 package, and the repository working agreement and source at 8ac6137.
Status: a read-only diagnostic is supplied. No workstation audit result is known.

## Decision

FSG1 remains FAIL. The small run failed the background accuracy criteria; the
full run failed step coverage (87.502%) and foreground coverage (79.319%). All
reported full-profile interior median/p95 errors are within their limits, ON
ACCEPTED PIXELS. This does not validate the estimates that were rejected.

Code correctly preserved the settings and stopped. The fixed 5x5 score and 0.5
cutoff came from Chat's implementation, not an unauthorized Code adjustment.

Authorize analysis of the existing three recorded acquisitions ONLY. There is no
new render, seed, sample count, matching algorithm, acceptance mask, gate, fixture,
or segmentation/depth-fusion decision. This step cannot approve FSG1 or FSG2.

Before the audit, append the following block verbatim to DECISIONS.md, using the
execution date when appropriate. Stop if D-FSG1b already exists; do not overwrite
or renumber it silently. Append a prospective log entry before execution.

```markdown
## D-FSG1b - Audit the full-profile coverage miss on saved records (2026-09-19)
Authorize the additive read-only coverage audit on the existing small/64, full/256 and diagnostic-small/1024 seed-17 records; both FSG1 failures stand and no FSG2 work is authorized.
Why: frequent texture rejection identifies a gate, not whether rejected correspondences are correct; fixed pixel support, display clipping, quantization and genuinely weak evidence must be distinguished.
Preserve the estimator, all thresholds, fixtures, reference denominators, provenance, failed records and prior decisions; no new acquisition or automatic adoption follows from counterfactual statistics.
Overturned if: frozen source hashes, exact replay, gate reconstruction or reference metrics disagree; stop and return evidence before drawing a diagnostic conclusion.
```

## The question this step answers

For each fixed evaluation population, distinguish:

1. **Accepted** by every original condition.
2. **Rejected solely by texture**: every other original condition passes.
3. **Rejected for another reason**, possibly also failing texture.

These three populations must be disjoint and exhaustive. The reported 99.7%
"fails texture" is not assumed to mean 99.7% "fails ONLY texture".

Reproject saved, ungated disparities ONLY inside the audit and score the second
population against the fixed evaluation reference. No rejected point is inserted
into a model, exported to PLY, or written back into the original result.npz.

The audit also measures RGB-only diagnostics, without changing any hypothesis:

- The exact original 5x5 uint8 score; float64 recomputation of its arithmetic;
  floating display-intensity contrast before uint8 quantization; unclipped linear
  luminance contrast; and clipping fractions. The original conversion clips linear
  RGB to [0,1] before quantization. A zero score there does not establish constant
  original radiance. Nonzero linear gradients can include noise, not just signal.
- One predeclared approximately angle-matched window: the small profile's +/-2
  pixel-centre span, yielding 5x5 at small and 9x9 at full for these calibrations.
  The actual focal lengths and spans are recorded. This is a support diagnostic,
  NOT a replacement matcher/refiner or authorization to use the larger score.
  The associated subgroup requires the larger left window to stay inside one ID;
  that does not prove a single smooth surface or sufficient right-eye evidence.
- Horizontal versus vertical gradient RMS. These are evidence descriptors, NOT
  calibrated uncertainty or confidence probabilities.
- Raw SGBM and refined error on the same named cohorts. Inspect finite counts.
  Do not compare different accepted populations as a causal estimator ablation.

It writes a labelled counterfactual aggregate with the texture veto absent, while
all other vetoes and the fixed reference remain in force. This answers what the
stored hypotheses would do under that omission; it does not remove the veto from
the production instrument or emit a new scientific pass.

All three records are evaluated separately. Their supports differ across profiles;
there is no automatic common-surface resampling or controlled noise experiment.
Do not call the previous gain "purely geometric" as an identified causal result.
The first-order sigma_d/d ratios explain how a gain is compatible with larger
pixel scatter, but do not isolate sampling, noise, support and selection effects.

## Scope and preserved gaps

No new render and zero new primary camera samples. No cutoff search, window sweep,
exposure change, alternate matcher, rerun until pass, hole filling, revised
interior mask, texture-qualified reference denominator, or changed acceptance gate.
Truth remains evaluator-only; the RGB-only replay accepts calibration/RGB/IDs and
has no path from which to load truth. The subsequent audit is explicitly an
evaluator, not an inference component.

The left-eye half-occlusion population remains NOT EXERCISED when its reference
count is zero. A mirrored fixture/opposite-eye test is still a separate additive
step BEFORE fusion. Boundary results are not validated by interior accuracy.
No new fixture is included here, so coverage diagnosis and fixture repair are not
confounded in this handoff.

## Files added; no legacy source is replaced

- tools/fsg_coverage_audit.py: read-only saved-record replay, gate attribution,
  evaluator-side counterfactual measurements, JSON and diagnostic contact sheets.
- tools/dev/check_fsg_coverage_audit.py: software invariants and deliberate negatives.
- docs/fsg1-coverage-audit.md: this decision, instructions and Results location.
- docs/fsg1-coverage-audit-validation.md: Chat's actual local tests and limitations.

The new tool enforces SHA-256 fingerprints of the four original geometry, scene,
stereo and evaluator modules it calls. Those bytes come from the initial handoff;
Code's reports say they remain unchanged at 8ac6137. The complete scientific
sources, renderer, checks, rig and dependency file are additionally checked by the
preflight git diff below. No dependency changes are needed.

## Code execution prompt

Read CLAUDE.md and this document in full. Work on main with a clean tree and the
handoff committed. Do not reset or clean unrelated work. Code may fix a demonstrated
bug ONLY in the new audit implementation and must describe it. The legacy code,
scientific checks, audit assertions, fingerprints and stated population definitions
must not be changed to obtain a pass. Unexpected replay/reference discrepancies
are a stop condition, not permission to relax equality or tolerances.

### 1. Preflight - Interactive (estimate under 10 seconds)

Record HEAD, status, Python/NumPy/OpenCV/Pillow versions. No GPU/Blender execution is
needed. Verify no dependency was upgraded since the records were produced.

```bash
git status --short
git branch --show-current
git rev-parse HEAD
git diff 8ac6137 -- tools/fsg_geometry.py tools/fsg_scene.py tools/fsg_render.py tools/fsg_stereo.py tools/fsg_evaluate.py tools/dev/check_fsg.py tools/dev/fake_blender_fsg.py tools/rig.py tools/bl_common.py requirements-fsg.txt
.venv/bin/python -c "import sys,numpy,cv2,PIL; print(sys.version); print(numpy.__version__,cv2.__version__,PIL.__version__)"
```

Expected: the source diff is empty. A nonempty diff requires reconciliation, not
execution on a silently different baseline. Verify the following saved records
exist and preserve them byte-for-byte:

```
previews/fsg1/small-seed17
previews/fsg1/full-seed17
previews/fsg1/diag-small-spp1024-seed17
```

Each must contain run.json, calibration.json, observation.npz, acquisition.json,
stereo/result.npz, stereo/summary.json, and evaluation_only/mesh.npz for each case.
The diagnostic run need not have an old evaluation.json; the original evaluator
can be invoked IN MEMORY with write=False. Do not generate one by running its CLI.
If an asset is missing, report its exact path and stop; no reacquisition is authorized.

Create a NEW gitignored logs directory, e.g. previews/fsg1/coverage-audit-logs.
Do not reuse a nonempty directory. Capture stdout/stderr and exit codes. With tee,
use bash pipefail and handle expected negative exits separately.
Record D-FSG1b and the prospective log entry before the saved-record audit.

### 2. Software checks - Interactive / short Batch (estimates)

```bash
.venv/bin/python tools/dev/check_fsg.py --self-test --repo-check --report previews/fsg1/coverage-audit-logs/legacy-checks.json
.venv/bin/python tools/dev/check_fsg_coverage_audit.py --self-test --report previews/fsg1/coverage-audit-logs/audit-checks.json
.venv/bin/python tools/dev/check_fsg_coverage_audit.py --negative replay
.venv/bin/python tools/dev/check_fsg_coverage_audit.py --negative partition
```

Expected: legacy 24/0 on the workstation (23/0 without the repository rig check);
new checks 29/0. Each negative MUST exit 1 with, respectively, "replay mismatch"
and "partition overlaps or misses reference pixels". These are software test
outcomes, not FSG1 performance claims. Any unexpected failure blocks the audit.

### 3. Audit the three existing acquisitions - Batch (estimate under 5 minutes)

```bash
.venv/bin/python tools/fsg_coverage_audit.py \
  previews/fsg1/small-seed17 \
  previews/fsg1/full-seed17 \
  previews/fsg1/diag-small-spp1024-seed17 \
  --out previews/fsg1/coverage-audit-seed17
```

The output path must not exist and cannot overlap an input. Choose and record a
new suffix if necessary, without erasing earlier output. Do not use
--allow-synthetic: it is solely for the tool's local tests.

The tool requires exact replay of every saved estimator array, reconstructs the
original gate conjunction, verifies the unchanged fixed-reference metrics through
the original evaluator in non-writing mode, and checks input JSON/NPZ hashes before
and after. It writes only under the new output directory. Source fingerprints are
checked before and after. It does not call the renderer or write new geometry.

Expected exit 0 means the AUDIT completed consistently, not that FSG1 passed.
Expected final label: AUDIT_COMPLETE_NOT_A_MILESTONE. The full baseline scientific
failures must still be recorded inside the audit. Do not change them.

The saved small/1024-spp record is comparison evidence, not a candidate reporting
configuration. No parameter is selected by this command.

### 4. Inspect and interpret - Interactive

Inspect <out>/<run>/<case>/diagnostic.png and audit.json for all three cases and
records, emphasizing full/step instance 1. The contact sheet explicitly separates
accepted points, texture-only rejection, other rejection, clipping, contrast and
rejected-hypothesis error. Never describe its rejected hypotheses as added coverage.

From reference_groups, report for each case and interior instance:

- Fixed reference count and original coverage/median/p95, confirming reproduction.
- Counts in all three exclusive groups and the overlapping texture-failure count.
- Texture-only group's refined AND raw-SGBM median/p95, finite counts, and fraction
  exceeding 3%, with group size. Zero-count groups have null errors, not a pass.
- Counterfactual-without-texture coverage/median/p95, explicitly not accepted output.
- Zero-score fraction; original U8, floating-display and unclipped-linear contrast;
  all/any high-clipping fractions and horizontal gradient descriptors for that group.
- The angle-window kernel and the size/error of its contrast-bearing subgroup.
- Boundary and singly-visible counts; retain NOT EXERCISED at zero denominator.

No automatic promotion follows, even if counterfactual numbers clear the original
90%/1%/3% criteria. They are post-hoc diagnosis on inspected seed-17 records.

Interpretation for Chat's next decision, not permission for Code to implement:

A. Rejected hypotheses are accurate and the score discards available RGB evidence:
   investigate photometric preprocessing or a justified confidence/support rule;
   evaluate any later change as a NEW candidate while preserving both baselines.
B. Many rejected hypotheses are wrong despite larger-support contrast:
   the veto is serving a purpose; investigate estimator/support quality, not merely
   lowering a threshold.
C. Missing regions lack usable evidence or have inconsistent correspondences:
   retain unresolved geometry. Do not use the instance label to fill a plane.
D. Clipping/quantization is prominent: fix the representation only through a
   separately specified experiment; do not alter exposure or conversion here.

A claimed cause must be qualified: clipping and quantization can destroy variation,
but this audit alone does not prove that retained variation is noise-free or that a
new stereo method can exploit it. A future candidate needs a prospective validation
plan including uninspected evidence, not just retesting this inspected record.

Likely execution failures, in order: missing untracked acquisition assets; changed
legacy source/environment; saved-array replay discrepancy; gate/reference mismatch;
new diagnostic serialization/visualization bug. The first four block conclusions.
A demonstrated bug solely in the new analysis code can be fixed without changing
its assertions or legacy sources; report and rerun software checks, then use a NEW
output directory. No Blender fallback is allowed.

### 5. Write up and return - Interactive

Append measured results below and in docs/log.md. Update README with the baseline
FAIL plus audit status, not an FSG1 pass. Preserve previous decisions and outcomes.
Review git diff --check and all staged paths; stage only these additive files and
the intended documentation. Commit and push as CLAUDE.md prescribes. Do not stage
previews, logs, generated images, arrays or unrelated files.

Return this report:

```text
FSG1b COVERAGE AUDIT REPORT
HEAD before/after; branch; push:
D-FSG1b recorded before audit; earlier failures preserved:
Legacy source diff and source-fingerprint verification:
Environment versions; pins unchanged:
Legacy and audit software SUMMARY lines verbatim:
Expected negative exits and FAIL lines:
Exact commands, input records, output and log paths:
Exact replay/gate/reference checks; input hashes unchanged:
Per run/case/instance: reference count; original coverage/median/p95:
Exclusive accepted/texture-only/other counts; overlapping texture failures:
Texture-only raw/refined count/median/p95/fraction-over-3%, per instance:
Counterfactual aggregate metrics, explicitly diagnostic-only:
Quantization/clipping/linear-contrast/gradient diagnostics on texture-only groups:
Angle-window size and contrast-bearing subgroup count/errors:
Boundary and singly-visible counts; NOT EXERCISED where empty:
Visuals actually inspected and observations:
Final status, runtime, zero new camera samples:
Unexpected FAIL lines; demonstrated analysis-code fixes, if any:
Changed files; no production/threshold/fixture changes:
No render, new seed, acceptance adoption, fusion or policy; stopped for Luiz/Chat:
```

## Workstation results

Run 2026-09-19 by Code on the workstation. Every number is read from files under
`previews/fsg1/coverage-audit-seed17/`. Chat's synthetic validation record in
`docs/fsg1-coverage-audit-validation.md` is untouched, and nothing here is a
Blender measurement: **zero new primary camera samples**.

Status `AUDIT_COMPLETE_NOT_A_MILESTONE`, 3 runs, 2.974 s, `diagnostic_only: true`,
`fsg1_authorized_pass: false`, `inputs_unchanged: true`. FSG1 remains FAIL.

### Preflight and preservation

HEAD `444107762c0fb41c20495b9ee7ddf15f3ad6ea32` on `main`, clean tree, handoff
committed. `git diff 8ac6137` over the ten legacy files is EMPTY. Environment
Python 3.12.3, NumPy 2.2.6, OpenCV 4.13.0, Pillow 12.3.0 - the same interpreter
and pins that produced the records; nothing was upgraded. D-FSG1b was absent
beforehand, was appended verbatim, and a prospective `docs/log.md` entry was
written before the audit ran.

Preservation was checked twice and independently of the tool. All 167 files of
the three records were SHA-256 fingerprinted before the run into
`previews/fsg1/coverage-audit-logs/00-records-before.sha256` and re-hashed after:
**byte-identical**, in addition to the tool's own `inputs_unchanged: true` and its
before/after source fingerprints. The legacy diff was re-checked as empty after
the write-up.

Software: legacy `[fsg-check] SUMMARY passed=24 failed=0 seconds=1.842
blender_executed=False`; new `[fsg-audit-check] SUMMARY passed=29 failed=0
seconds=1.988 blender_executed=False`. Both deliberate negatives exit 1:
`[fsg-audit-check] FAIL ValueError: replay mismatch in valid; no counterfactual analysis authorized`
and `[fsg-audit-check] FAIL ValueError: partition overlaps or misses reference pixels`.

`replay_exact: true` for all nine case-records, every partition exact
(accepted + texture-only + other = reference, disjoint and exhaustive), and the
original evaluator's metrics reproduced through the non-writing path. Both
baseline failures are preserved inside the audit output verbatim, including
`coverage=0.8750164128151261 fails min 0.9` and
`instance 1: coverage=0.7931872814685315 fails min 0.9`.

### The question the audit was built to settle

The previous report said 99.7% of the rejected foreground pixels "fail texture".
That is not the same claim as "fail ONLY texture", and the audit separates them.
For `full-seed17/step` instance 1: reference 36,608; accepted 29,037; rejected
7,571; of those, 7,552 fail texture at all, and **7,549 fail texture and nothing
else**. Only 22 pixels fail for another reason (all `lr_consistent`), and 3 fail
texture together with something else. So the stricter statement holds: 99.71% of
the rejections on the failing instance are a texture-only veto.

| run / case / instance | ref | accepted | texture-only | other | official cov / med / p95 |
| --- | ---: | ---: | ---: | ---: | --- |
| small / step / inst 1 | 9088 | 8212 | 876 | 0 | 90.361% / 0.187% / 0.792% |
| small / step / inst 2 | 6016 | 6001 | 0 | 15 | 99.751% / 1.136% / 4.111% |
| **full / step / inst 1** | 36608 | 29037 | **7549** | 22 | **79.319%** / 0.137% / 0.595% |
| full / step / inst 2 | 24320 | 24276 | 1 | 43 | 99.819% / 0.785% / 2.497% |
| full / fronto | 65536 | 62119 | 3361 | 56 | 94.786% / 0.285% / 1.159% |
| full / tilted | 65536 | 64509 | 934 | 93 | 98.433% / 0.318% / 1.348% |

### What the rejected hypotheses are worth

Scored against the unchanged fixed reference, on the exact texture-only cohort:

| run / case / instance | n | refined med / p95 / over-3% | raw SGBM med / p95 / over-3% |
| --- | ---: | --- | --- |
| small / fronto | 262 | 0.481% / 2.881% / 2.672% | 0.952% / 0.952% / 0.000% |
| small / tilted | 29 | 1.406% / 4.084% / **34.483%** | 0.127% / 1.366% / 0.000% |
| small / step inst 1 | 876 | 0.265% / 1.151% / 0.114% | 0.099% / 0.099% / 0.000% |
| **full / step inst 1** | 7549 | **0.178% / 0.889% / 0.000%** | 0.099% / 0.099% / 0.000% |
| full / fronto | 3361 | 0.385% / 1.320% / 0.000% | 0.952% / 0.952% / 0.000% |
| full / tilted | 934 | 0.520% / 1.806% / 0.000% | 0.221% / 0.491% / 0.000% |
| diag1024 / step inst 1 | 883 | 0.091% / 0.377% / 0.000% | 0.099% / 0.099% / 0.000% |
| small & diag1024 / step inst 2 | 0 | null - zero count is NOT a pass | null |

On the instance that actually fails, the discarded hypotheses are as accurate as
the accepted ones (0.178% vs 0.137% median; not one pixel over 3%). The labelled
counterfactual with the texture veto absent and every other veto and the fixed
reference still in force gives, for full/step instance 1, coverage 79.319% ->
**99.940%** with median 0.137% -> 0.144% and p95 0.595% -> 0.653%; pooled step
87.502% -> 99.893%. **This is diagnostic arithmetic on stored hypotheses, not
accepted output, not a new coverage number, and not an FSG1 pass.**

### Why the score is zero: clipping first, quantization second

The fixture's foreground is over-exposed. Of the full/step instance-1
texture-only cohort, **100.000% have at least one RGB channel high-clipped and
92.489% have all three clipped**; none are low-clipped. The production
conversion clips linear RGB to [0,1] before quantizing, so a saturated
neighbourhood becomes constant and scores exactly 0.

The audit separates the two mechanisms, and they are not equal partners:

| run / case / instance | u8 score = 0 | float-display score = 0 | unclipped-linear = 0 | median linear std | median grad-x RMS |
| --- | ---: | ---: | ---: | ---: | ---: |
| small / step inst 1 | 59.932% | 35.731% | **0.000%** | 0.076973 | 0.058789 |
| full / step inst 1 | 69.029% | 51.835% | **0.000%** | 0.045318 | 0.030455 |
| full / fronto | 48.825% | 20.976% | **0.000%** | 0.023660 | 0.011396 |
| full / tilted | 27.409% | 6.424% | **0.000%** | 0.016433 | 0.008467 |
| diag1024 / step inst 1 | 60.136% | 36.580% | **0.000%** | 0.076872 | 0.058622 |
| full / step inst 2 | 0.000% | 0.000% | 0.000% | 0.003155 | 0.002196 |

For full/step instance 1, 51.835% of the cohort is already flat BEFORE
quantization - that is clipping - and quantization flattens a further 17.2 points
to 69.029%. Clipping is roughly three quarters of the effect. Critically, the
unclipped linear luminance score is **never** zero anywhere: the rendered
radiance retains variation at every one of these pixels, and it is the fixed
display conversion that destroys it. The contact sheets show this directly - the
"Linear std5" panel is full of texture exactly where "Production std5" and
"Float-display std5" are black.

Resolution is a real but secondary modulator, which corrects the emphasis of the
previous report without contradicting its measurements: the same saturated blobs
are a fixed angular size, so the fixed pixel window sits deeper inside them at
full, and the zero-score share rises 59.932% -> 69.029% between small and full on
the same instance. The earlier note's "texture halves with resolution" is the
median-contrast statement; it is true, and it is not the main mechanism.

The angle-matched window is 9x9 at full against the production 5x5, matching the
small profile's +/-2 pixel-centre span (focal 1217.839 px vs 608.919 px; centre
spans 0.00328 rad production, 0.00657 rad diagnostic). At full/step instance 1,
**3,871 of 7,549** texture-only pixels carry contrast in that larger window, with
100.000% of those windows inside one instance ID. At small and diag1024 the
angle-matched kernel IS 5x5, so this subgroup is 0 by construction, which is an
internal consistency check rather than a finding.

### Why this is not a licence to drop the veto

Three measured cautions, all of which cut against the easy reading:

1. Raw SGBM on the texture-only cohorts is frequently **degenerate**: median and
   p95 are identical to four decimals (0.0992/0.0992 on step instance 1 at all
   three records, 0.9524/0.9524 on fronto). A single constant disparity has been
   propagated across the whole saturated region by SGBM's smoothness term. It is
   correct here because the hidden surface really is a fronto-parallel plane at
   constant depth. On a surface that was not, the same propagation would be
   confidently wrong, and this fixture cannot distinguish the two.
2. Roughly half the cohort (3,678 of 7,549) has no contrast even in the 9x9
   angle-matched window, yet the contrast-bearing half scores 0.162%/0.773%
   against the whole cohort's 0.178%/0.889% - barely better. If local evidence
   were driving the accuracy, that gap would be large. It is not, which again
   points at propagation rather than recoverable local signal.
3. The veto demonstrably does useful work elsewhere. On small/tilted the
   texture-only hypotheses are worse, not better: median 1.406%, p95 4.084%, and
   **34.483% of them exceed 3%** relative error, against raw SGBM's 0.127%/1.366%
   on the same pixels. A blanket removal would have admitted those.

So interpretations A and D of this handoff are both supported - the fixed score
discards RGB evidence that demonstrably survives in linear radiance, and
clipping/quantization is prominent - while B is NOT excluded, because the
accuracy of the discarded hypotheses on this fixture is substantially inherited
from a planar-surface smoothness prior. A fix belongs in the representation
(exposure, or a score computed before the clip), specified as a separate
experiment with a prospective plan on uninspected evidence, and evaluated as a
NEW candidate against both preserved baselines. Nothing is adopted here.

### Boundary, half-occlusion, visuals

`singly_visible` reference count is 0 in all nine case-records:
**NOT EXERCISED**, at both profiles and in the diagnostic. A zero denominator is
not a pass, and the mirrored-fixture or opposite-eye test remains a separate
additive step before any fusion. `boundary` is NOT EXERCISED for fronto and
tilted (zero reference) and EXERCISED only on step: 1,280 reference / 395
accepted at small, 4,608 / 2,362 at full, 1,280 / 411 at diag1024. Boundary
accuracy is still not validated by the interior gate.

Inspected `diagnostic.png` for full/step, full/fronto and small/step, plus
`audit.json` for all nine case-records. full/step: the RGB panel shows the left
half washed out against a crisply textured right half; the texture-only mask
matches the holes in the accepted mask almost exactly; the other-veto panel is
black but for a sprinkle of isolated dots (22); production and float-display
score maps are nearly identical, which is the clipping-not-quantization result in
picture form; the clipped-channel mask coincides with the texture-only mask; the
rejected-hypothesis-error panel is essentially black against its 3% scale; and
the linear-std panel is full of structure where the others are blank. full/fronto
is the same story at lower severity, its texture-only blobs sitting on the bright
saturated patches. small/step matches with fewer and coarser blobs, and its
angle-window panel equals its production panel as expected at that kernel.
No rejected hypothesis is exported, written back, filled, or treated as coverage.
