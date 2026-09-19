# FSG1 follow-up: assess the unchanged full profile

Date: 2026-09-19
Type: execution-only handoff; no implementation or dependency changes.
Basis: Code-FSG1.md, reported checkout 03029a2, and the FSG1 handoff and working agreement at that commit.
Status: supplied by Chat for Luiz to apply and forward to Code. No full-profile result is claimed.

## Decision and historical record

The small/default-spp suite remains FAIL. Its step background instance has
1.136% median and 4.111% p95 relative left-eye range error, against 1% and 3%.
The pooled step pass does not override the per-instance failures.

Code correctly stopped: sections 4 and 5 of docs/fsg1-code-prompt.md explicitly
required a small-profile pass before the full run. This follow-up is a documented
exception to that execution prerequisite, not a claim that small was never gated.
Do not edit the earlier failure, replace its records, or retroactively relabel it.

Authorize one unchanged full-profile suite, seed 17, at the recorded default
256 spp. The suite, matcher, refinement, validity rules, evaluation masks,
thresholds and profile definitions remain frozen. A sample-count override is
not authorized for this run. No algorithm patch is requested.

Reason: software and independent Blender geometry checks passed; the remaining
reported failure concerns measurement accuracy rather than an identified
calibration/integration defect. Full was already the declared reporting profile
before these measurements. Its performance is still unmeasured and may fail.

Before acquisition, append this decision block to DECISIONS.md (do not rewrite
D-FSG1 or its outcome). Use the execution date if different; preserve the decision
identifier unless it already exists, in which case stop and reconcile with Luiz.

### Exact decision block

```markdown
## D-FSG1a - Assess the unchanged full profile after the small-profile miss (2026-09-19)
Authorize one default full/256-spp FSG1 suite at seed 17; small/64-spp remains FAIL, and no FSG2 work is authorized.
Why: software/calibration checks passed; the remaining small-profile miss warrants measuring the already-declared reporting configuration, not retuning it.
Supersedes only the small-pass prerequisite in sections 4-5 of fsg1-code-prompt.md; preserve every threshold, fixture, estimator setting, failed record and per-instance gate.
Overturned if: calibration/provenance fails or full misses its gate; stop and return the evidence to Luiz/Chat without tuning or beginning fusion.
```

Add a dated, prospective entry to docs/log.md before acquisition linking to this
handoff and recording the command/settings. Afterward, append measured outcomes.
Leave the original execution prompt intact; this named exception governs this
continuation only. Do not weaken its rule for unrelated future failures.

## Interpretation of the existing report

The 1024-spp small-profile diagnostic is evidence that acquisition noise contributes
to the current estimator's error. It does not establish that all residual error is
render noise, prove an information-theoretic limit, or rule out estimator changes.
Use that qualified description in the new write-up; preserve the historical report.

At the prescribed dimensions, three cases and two eyes give:

| Configuration | Nominal primary camera samples |
| --- | ---: |
| small, 320 x 320, 64 spp | 39,321,600 |
| diagnostic small, 320 x 320, 1024 spp | 629,145,600 |
| full, 640 x 640, 256 spp | 629,145,600 |

These are arithmetic counts, not measured execution times or secondary-ray counts.
The equal-count diagnostic/full comparison may be reported, but cannot isolate
resolution from noise, support size or acceptance changes. Do not claim an
end-to-end efficiency improvement from this calibration experiment.

## Non-negotiable boundaries

Read current CLAUDE.md, docs/fsg1-single-patch.md and the original code prompt.
Preserve per-eye oracle instance IDs only; RGB/calibration produce geometry.
The head frame stays fixed. Ground truth stays evaluator-only.
No source-code, dependency, matcher, profile, threshold, fixture, boundary-margin,
reference-denominator, mask, provenance or negative-check change is authorized.
Do not use --allow-synthetic, --spp, denoising or adaptive sampling as a workaround.
No fusion, surface growing, peripheral discovery, new scene, learned matcher,
mirrored fixture, parameter sweep, or additional seed is part of this handoff.

The fixture's left-eye singly-visible reference count was zero. This is not proof
that half-occlusion rejection works. Report it as NOT EXERCISED. A mirrored depth
step or an explicitly opposite-eye reference is a separate additive follow-up for
Chat to implement before surface fusion is authorized. Do not alter the existing
three-case suite to repair that coverage gap in this run.

## 1. Preflight - Interactive

Record branch, HEAD, working-tree status, Blender/GPU, and host dependency versions.
Start on main with no unrelated tracked or untracked changes. Do not reset, clean,
or overwrite someone else's work. The newly applied handoff must be committed.

Verify that the FSG1 executable sources/checks and relevant rig/profile definitions
are unchanged from the reported 03029a2 baseline. If they have changed, show the
diff and stop for reconciliation rather than silently testing a different estimator.
Do not move dependency pins. Keep failed and diagnostic output directories intact.

Commands to inspect (run from the repository root):

```bash
git status --short
git branch --show-current
git rev-parse HEAD
git diff 03029a2 -- tools/fsg_geometry.py tools/fsg_scene.py tools/fsg_render.py tools/fsg_stereo.py tools/fsg_evaluate.py tools/dev/check_fsg.py tools/dev/fake_blender_fsg.py tools/rig.py tools/bl_common.py requirements-fsg.txt
blender --version
.venv/bin/python -c "import sys,numpy,cv2,PIL; print(sys.version); print('numpy',numpy.__version__,'opencv',cv2.__version__,'Pillow',PIL.__version__)"
```

Keep all generated reports/logs under a NEW gitignored directory such as
previews/fsg1/full-followup-logs. Do not overwrite an existing directory; choose a
recorded new suffix. Save stdout/stderr for each command and record its exit code.
Use bash pipefail when piping through tee; inspect each exit before continuing.

## 2. Reconfirm software checks - Interactive (prior reported time about 2 s)

```bash
.venv/bin/python tools/dev/check_fsg.py --self-test --repo-check --report previews/fsg1/full-followup-logs/software-checks.json
.venv/bin/python tools/dev/check_fsg.py --negative baseline
.venv/bin/python tools/dev/check_fsg.py --negative crop
```

Expected suite: 24 passed, 0 failed with this unchanged implementation.
Each deliberate negative must exit 1 with its specific geometry FAIL line.
Run the negatives separately so their expected nonzero codes do not abort the
whole execution session. Any unexpected result blocks acquisition. Record both
expected negatives separately from empirical accuracy failures.

## 3. Acquire one real full-profile suite - Batch (estimated under 5 min)

Use a new output path, initially previews/fsg1/full-seed17. If it already exists,
inspect its provenance, preserve it, and use a new recorded suffix; do not erase
it or silently rerender it. There is exactly one new full-suite acquisition in
this authorization, not repeated attempts until a seed passes.

```bash
FULL=previews/fsg1/full-seed17
blender -b --python-exit-code 1 -P tools/fsg_render.py -- --out "$FULL" --profile full --device OPTIX --seed 17 --save-blend
```

Expected prescription: 640 x 640 RGB per eye; 256 x 256 accepted core; 256 spp;
three cases; 629,145,600 primary camera samples. Read actual stored settings.
A changed default is a reason to stop, not permission to force a matching label.

Before stereo, verify the real provenance, backend, completed run.json marker,
independent L/R seeds and in-session checks for every case. Projection discrepancy
must be <=0.002 px and ray-cast discrepancy <=20 micrometres, with matching IDs.
Preserve the existing checks; do not infer success from shell exit alone.

If a command threatens to exceed 5 minutes, stop and report rather than promote
it to an overnight run. No silent CPU fallback. Record actual render, oracle,
within-script and whole-process times distinctly.

## 4. Stereo, evaluation and inspection - Interactive/short Batch (estimate)

```bash
.venv/bin/python tools/fsg_stereo.py "$FULL"
.venv/bin/python tools/fsg_evaluate.py "$FULL"
```

Capture the evaluator exit code and every FAIL line. A failing evaluation is a
reportable experimental outcome, not permission to tune, rerender or change a
check. Preserve the generated evaluation.json and all per-case metrics.

Frozen gates: coverage >=90%, median absolute relative left-eye range error <=1%,
and p95 <=3%, on each case and each adequately supported instance (existing rule:
at least 100 eligible interior pixels). Use the existing full-profile boundary
margin of 8 pixels, not a newly enlarged exclusion.

Read per_object_interior, boundary, singly_visible and object-label mismatch counts,
not merely pooled figures. A zero reference count means NOT EXERCISED, not PASS.

Inspect rectified L/R, disparity, validity, estimated/reference range, relative
error, interior/boundary masks and head-frame points for all three cases. Record
which files were inspected and what they show. Compare far-background error with
the earlier small result without substituting a favorable pooled number.

Reuse the report's diagnostic analysis to record SGBM and refined signed disparity
bias/scatter on accepted interior pixels, separately by instance. State the support
used so acceptance differences are not confused with estimator improvement. Keep
truth-based diagnosis strictly evaluation-side. If this requires new production
code, do not write it here; report what the existing tools make available instead.

Only the unmodified evaluator may emit MILESTONE_PASS for the real default full
suite. A pass applies to these controlled textured opaque fixtures and this
configuration/seed, not full object reconstruction or general robustness.
FSG2 is not automatically authorized even if the evaluator passes.

## 5. Documentation, commit and return - Interactive

Append measured results to the existing workstation section of
 docs/fsg1-single-patch.md and docs/log.md. Update the README status with both the
small failure and the new full outcome. Preserve the earlier Chat/synthetic
validation and Code report. The new decision is append-only; do not rewrite D-FSG1.

Record the half-occlusion test-coverage gap and the qualified noise diagnosis in
new text. Do not claim that boundary accuracy is validated by the interior gate.

No production code or test changes are expected. Check git diff --check, inspect
all staged paths, stage only the intended documentation, commit and push to main
as prescribed by CLAUDE.md. Generated data stay in previews. Report any failure
to push accurately. Do not reset history or stage unrelated files.

Return this paste-ready report:

```text
FSG1 FULL-PROFILE FOLLOW-UP REPORT
HEAD before / after; branch / push result:
D-FSG1a recorded before acquisition; original small FAIL preserved:
Executable source/check/profile changes from 03029a2: none (otherwise stop)
Environment versions / GPU backend:
Software-check SUMMARY (verbatim):
Expected negative baseline: exit code + FAIL line
Expected negative crop: exit code + FAIL line
Exact commands and NEW output/log paths:
Per-case source/profile/spp/seeds/completion metadata:
Per-eye projection / ray-cast maxima and object-ID agreement:
Per-case AND per-instance coverage / median / p95, with file paths:
Boundary coverage / median / p95 / over-3% fraction:
Singly-visible reference/accepted counts: NOT EXERCISED if denominator is zero
Wrong-instance accepted counts:
SGBM/refined disparity bias/scatter and diagnostic support (or unavailable):
Camera sample counts / render / oracle / stereo / total times:
Visuals actually inspected and observations:
All accuracy FAIL lines and unexpected failures (verbatim):
Final evaluator exit code and status (verbatim):
Files changed (documentation only):
No code/check/threshold/fixture/default modifications:
No fusion/policy implementation; stopped for Luiz/Chat:
```

## Local handoff validation and limits

Chat compared Code's attached report against the original package and read the
working agreement, decision record, execution prompt and evaluator at 03029a2.
The earlier package SHA-256 was reconfirmed. Camera-sample arithmetic was checked.
The archive for this follow-up contains this one new Markdown file only.
No Blender render, full-profile estimator run, or workstation measurement was
performed by Chat for this follow-up. No empirical pass is claimed here.
