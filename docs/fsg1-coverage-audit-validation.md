# FSG1 coverage audit: Chat validation

Date: 2026-09-19. These are local software tests, NOT Blender measurements.

## Source and execution limits

Read the attached Code report and inspected CLAUDE.md, decisions, FSG1 notes,
stereo/evaluator code at reported commit 8ac6137 through the web tool. A repository
clone was attempted and failed because github.com could not resolve in the code
container. Local execution used the original uploaded FSG1 package: the files Code
reported unchanged in both workstation reports. The new audit checks those files'
SHA-256 fingerprints before using them on the workstation.

Blender/bpy and the user's real observation records were not available here. The
reported RTX 4090 results have NOT been independently rerun by Chat. No new real
coverage, accuracy, clipping fraction, or recovery rate is claimed.

Local environment: Python 3.13.5, NumPy 2.3.5, OpenCV 4.13.0,
Pillow 12.3.0. Code's recorded NumPy is 2.2.6; no workstation dependency change is
requested. Exact replay is checked on the workstation in its original environment.

## Executed tests

- New audit self-test: 29 passed, 0 failed, 3.941 seconds, blender_executed=False.
- Unchanged original software tests: 23 passed, 0 failed, 3.686 seconds.
  The optional repository-rig test was not run locally; Code expects 24 including it.
- Deliberate replay and overlapping-partition negatives each exited 1 as intended.
- Analytic small/full three-case acquisitions were generated with the original
  SyntheticBackend, then processed and audited. These are labelled synthetic_stub,
  not Cycles. Exact replay, original reference metrics and input preservation held.
- Visual inspection covered the analytic diagnostic contact sheet; no real
  workstation image is included or represented as inspected here.

The audit self-tests include stale-input detection, source mutation detection,
actual saved-disparity mutation, empty populations, output collision/path guards,
unchanged historical records, no production geometry/evaluation exports, blank
images remaining invalid, and RGB-only tracing with the truth directory removed.
They also distinguish U8 quantization, HDR display clipping, and horizontal versus
vertical image variation. Those controls do not predict the actual data's cause.

## Development failure retained

The first self-test run gave 27 passed and 1 failed: a deliberately tiny 1e-8 linear
ramp survived floating display conversion at the small test centre but was erased
by float32 conversion at the full test centre. Inspection showed the floating
5x5 window itself was constant there, so the test's expected positive variance
was unsupported. The synthetic unit-test ramp was changed to a centred 1e-6 step:
still below a U8 bin locally, but large enough to survive float32 conversion.
No production threshold, check, renderer fixture or scientific target was changed.
The final suite also adds an explicit HDR-clipping control (29 checks total).

## Meaning of success

AUDIT_COMPLETE_NOT_A_MILESTONE means the analysis reproduced the frozen
measurements and consistently described their rejection populations. It never
means FSG1 passed. Counterfactual errors are evaluator-side evidence, not accepted
surface points or a deployment-ready confidence rule. No fusion is authorized.

## Final verification

Final analytic small/full replay after adding the clipping diagnostic completed in
5.463 seconds; both records' JSON/NPZ fingerprints were unchanged. Contact-sheet
layout and labels were inspected. Python syntax compilation passed for both new
Python files. The ZIP contains only the two new scripts and these two new Markdown
documents; it contains no baseline sources, generated geometry, renders or fonts.
