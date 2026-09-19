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

Pending. Do not replace this section with Chat's synthetic test values.
