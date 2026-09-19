# FSG1c - A fixed radiometric encoding candidate, not deletion of the texture veto

Date: 2026-09-19. Chat implementation and Code execution handoff.
Basis: the supplied `Code-FSG1-audit.md`, reported HEAD `64e02af`, and the
working agreement/current interfaces read from that repository. FSG1, FSG1a
and their saved failures remain unchanged. This document authorizes a NEW
candidate on EXISTING observations; it cannot authorize fusion or promotion.

## Decision and rationale

The audit reports that 7,549 of the 7,571 rejected full-step foreground interior
pixels fail only texture. Their stored refined hypotheses have 0.178% median,
0.889% p95 error and no pixel over 3%. Those results are diagnostic, not a new
accepted mask. Removing the veto is not justified: 10 of the 29 texture-only
small/tilted hypotheses are over 3%, and smoothness propagation on the flat
fixture is a plausible explanation for some otherwise good rejected depths.
Equal error quantiles alone do not prove a spatially constant disparity field.

The audit reports that all of the 7,549-pixel cohort has at least one RGB channel
at or above the converter's clamp, and 92.489% has all three. Its float-display
score is zero for 51.835%, versus 69.029% after uint8 conversion. The unclipped
linear score is nonzero throughout that cohort. The 'roughly three quarters'
clipping interpretation refers to the zero-score fraction, not three quarters
of all errors or all rejected measurements. Nonzero linear contrast can contain
Monte Carlo noise; it is not proof of a good correspondence.

Chat's interpretation: this identifies avoidable **post-render radiometric
clipping**. It does not establish lost information at acquisition: the original
floating RGB still exists. The original clip-at-one preprocessing was Chat's
implementation choice. The inference problem is not yet solved, but this
particular coverage miss is not evidence against active foveal stereo.

Choose one fixed mapping for the matching images AND their texture score:

    a = max(scene_linear_RGB, 0)
    b = a / (1 + a)
    uint8_RGB = round(255 * sRGB(b))

The scale is exactly one scene-linear unit, anchored to the old clamp level,
not estimated from these records. It is the same per-channel function for both
eyes, every pixel, all profiles, and all fixations. No histogram, percentile,
per-eye exposure, local enhancement, gain search or ground truth is involved.
This is a deliberately simple experimental encoding, not a biological model.

It avoids hard saturation at finite scene-linear 1 before quantization. It is
NOT lossless: quantization remains, very bright values can still round to 255,
and weak gradients can still fail the veto. The same numerical 0.5-code-unit
cutoff is retained, but its relationship to scene radiance changes with the
encoding. Thus this is a new instrument candidate, not identical acceptance
under a cosmetic display edit.

SGBM sees the encoded images; so does the original 5x5 texture score. The bounded
photometric refinement continues to see ORIGINAL float RGB. This changes the
evidence for initial correspondence as well as acceptance; it does not merely
resurrect old disparities. All parameters, support windows, search bounds,
instance guards, LR checks, refinement iterations and evaluator rules remain.

## Prospective record to append BEFORE running the candidate

Read CLAUDE.md first. Stop if D-FSG1c already exists: do not overwrite it or
silently select another identifier. Use the actual execution date if different.
Append this block to DECISIONS.md and a prospective docs/log.md entry:

```markdown
## D-FSG1c - Test a fixed soft HDR encoding on saved FSG1 observations (2026-09-19)
Authorize one opt-in candidate: max(x,0)/(1+max(x,0)), then the existing sRGB transfer and uint8 quantization, shared by both eyes for SGBM and its texture score. Keep the original linear-RGB refiner and every numerical matching/acceptance/evaluation setting.
Why: FSG1b identifies post-render clipping in the old encoding, while its tilted counterexample does not justify deleting the texture veto. No fitted exposure or threshold sweep is authorized.
Compare on the existing small/64, full/256 and diagnostic-small/1024 seed-17 records, with exact legacy replay and unchanged fixed reference populations. Preserve all original files and failures; record the candidate separately. No new acquisition, default change, milestone promotion or FSG2 work.
A numerical miss on small does not block the prescribed full comparison: all three existing records are processed once. A source, provenance, replay or integrity exception stops execution immediately. A candidate numerical miss is reported, not tuned away.
The candidate is successful on the existing full record only if it satisfies the original per-case/per-instance 90% coverage, 1% median and 3% p95 range-error rules and identity checks. This is development-set evidence, not independent validation; the synthetic bright-full stress miss and the unexercised half-occlusion case remain explicit. Report any regression on other records.
Overturned if: frozen-source/replay checks fail, or the candidate cannot recover coverage without violating the fixed accuracy rules. Stop for Luiz/Chat; do not alter the mapping, windows, thresholds, fixtures or tests.
```

## Files and isolation

| New file | Role |
| --- | --- |
| tools/fsg_stereo_hdr.py | RGB-only candidate kernel and candidate artifact writer |
| tools/fsg_hdr_compare.py | Read-only legacy replay, candidate execution and separate evaluation |
| tools/dev/check_fsg_hdr.py | Positive software checks and three negative controls |
| docs/fsg1-hdr-candidate.md | This handoff and Code prompt |
| docs/fsg1-hdr-validation.md | What Chat actually tested, including the stress failure |

All legacy source files stay byte-identical. The small copied compute kernel is
mechanically compared against the frozen original: apart from its function name,
only `linear_to_u8` -> `hdr_to_u8` may differ. This is temporary experiment
isolation, not a request to maintain divergent stereo implementations forever.
No global monkeypatch is used. `compute_candidate` accepts only calibration and
the same four RGB/instance arrays. It has no evaluator import, file path to truth,
known plane model or access to scene geometry.

The comparison replays legacy arrays exactly before using the new estimator.
Candidate predictions are saved BEFORE evaluator access to geometry. It uses
`ground_reference`, `describe_errors` and `gate` from the unchanged evaluator.
It does NOT call the old suite's automatic milestone-status function.

Every file under every source run (including optional .blend and images) is
hashed before and after. Output must be a new, disjoint directory. The saved
legacy `stereo/`, evaluation JSON, observation NPZ and acquisition metadata are
never overwritten, copied back or relabeled.

## What is measured

Each case reports the old and candidate interior/per-instance coverage and error
against exactly the same reference. Boundary and singly visible populations
remain separate and are NOT_EXERCISED if empty. The latter is not a pass.

The paired table additionally reports common, newly accepted, lost and neither
support. It compares both estimates on common support, evaluates newly accepted
geometry, and follows the OLD texture-only cohort under the new estimator. The
old rejected hypotheses remain diagnostic: they are never written into candidate
points. A lost pixel and a newly acquired pixel need not have the same error.

The visualization shows legacy clipped RGB, candidate RGB, candidate error,
both validity maps, newly accepted/lost support and both texture-score maps.
Missing pixels remain missing, not interpolated for appearance. Candidate point
clouds are labeled `candidate_points_head.ply` and remain experimental outputs,
not a persistent map.

## Important known limitation BEFORE the workstation experiment

The 34 new software checks pass in Chat's sandbox. Ordinary analytic small/full
fixtures pass the numerical gate with the candidate. A separate analytic HDR
stress, defined as `RGB_bright = 1.2 + 2 * RGB_analytic` for BOTH eyes, passes at
small but FAILS full coverage: fronto 79.097%, tilted 78.828%, pooled step 86.809%
(foreground 85.760%, background 88.388%). The corresponding accepted errors are
inside the numerical error limits. The old clipped encoder accepts no points
in that artificial bright stress. No curve, threshold, test or fixture was
changed to conceal these results.

This is precisely why the candidate is NOT declared fixed or adopted. Avoiding
the hard clamp does not guarantee that an eight-bit, fixed-window system will
retain every weak gradient. The actual Cycles records have a different radiance
and texture distribution, which Chat does not possess. A paired reprocessing is
cheap and tests whether this single intervention solves the actual reported
coverage miss. Even if it does, it is not a universal HDR stereo solution.

The analytic backend is a SOFTWARE TEST, not Blender. Its truth is available
only to the evaluator. The stress definition uses no depth-specific correction.
The existing experimental fixtures and records remain unchanged.

## Code prompt: execution in order

### 1. Preflight and prospective decision - Interactive

Read CLAUDE.md and both new docs, including the known stress failure. Verify a
clean main branch and that the prior report's commit 64e02af is an ancestor.
Record D-FSG1c and the prospective log BEFORE the candidate command. Keep prior
decisions and numerical failures intact. Do not edit historical outcome text.

Use the SAME host .venv that produced the records. Record Python, NumPy, OpenCV,
Pillow versions; do not upgrade or change dependency pins. No Blender process
is needed. Save logs in a NEW `previews/fsg1/hdr-candidate-logs` directory.
Stop if an intended output/log directory is already present rather than reusing
it. This handoff is one run, not a sweep.

Confirm an empty executable-source diff against 64e02af for all original FSG
modules, original checks, rig.py, bl_common.py and requirements-fsg.txt. The
runtime additionally checks the four frozen reconstruction/evaluation hashes.

### 2. Software checks - Interactive each, estimated

```bash
.venv/bin/python tools/dev/check_fsg.py --self-test --repo-check --report previews/fsg1/hdr-candidate-logs/legacy-checks.json
.venv/bin/python tools/dev/check_fsg_coverage_audit.py --self-test --report previews/fsg1/hdr-candidate-logs/audit-checks.json
.venv/bin/python tools/dev/check_fsg_hdr.py --self-test --report previews/fsg1/hdr-candidate-logs/hdr-checks.json
```

Expected summaries: 24/0 on the workstation legacy checks (23/0 without its rig
integration test), 29/0 audit, and 34/0 candidate. The tests do NOT mean that all
radiometric cases meet the experiment's accuracy/coverage gate. In particular,
the supplementary bright-full stress is known to fail as documented above.

The deliberately failing commands, separately logged, MUST exit 1:

```bash
.venv/bin/python tools/dev/check_fsg_hdr.py --negative encoder
.venv/bin/python tools/dev/check_fsg_hdr.py --negative replay
.venv/bin/python tools/dev/check_fsg_hdr.py --negative geometry
```

They must respectively detect collapsed HDR values, altered saved validity,
and a 20% depth-scale corruption under the original metric gate. A zero exit is
a broken check. Do not chain expected failures under an unhandled `set -e`, and
capture PIPESTATUS if using tee. Warnings on intentionally invalid disparity
in the analytic no-texture stress are documented, not a reason to relax checks.

### 3. One comparison command - Batch (<5 min estimate; no acquisition)

First verify that all three source runs and their original stereo results are
complete. Do NOT use `--allow-synthetic` on the workstation records.

```bash
.venv/bin/python tools/fsg_hdr_compare.py \
  previews/fsg1/small-seed17 \
  previews/fsg1/full-seed17 \
  previews/fsg1/diag-small-spp1024-seed17 \
  --out previews/fsg1/hdr-candidate-seed17
```

Exit 0: completed and all requested numerical gates passed. Exit 2: completed
with at least one candidate numerical miss. Both are valid experiment outcomes;
inspect the PER-RUN full result rather than mistaking an unchanged small miss
for a full miss. Exit 1: implementation/provenance/integrity exception; STOP.
No automatic retry, new exposure, alternate curve, seed or sample count.

The command always keeps `full_profile_milestone_pass=false` and
`fusion_authorized=false`. A passing full candidate on these old records is
`CANDIDATE_PASS_ON_EXISTING_RECORD`, not an independent validation. The source
observations already informed the diagnosis and candidate selection.

### 4. Inspect and report - Interactive

Inspect comparison.png for full/step, full/tilted, full/fronto, and small/tilted.
Read comparison.json for ALL NINE case-records; do not select a favorable panel.
Inspect the candidate point cloud and depth/validity maps, noting remaining
holes and boundary errors. All coordinates remain in fixed H.

For full/step foreground and both full/small tilted cases, report old and
candidate coverage, errors, gained/lost/common counts and errors, and old
texture-only -> candidate recovery. The small/tilted old cohort has only 29
pixels; do not turn it into a broad population estimate.

Use score distributions to distinguish improved encoding from simply accepting
bad estimates. Bright structure in a texture panel is not calibrated confidence.
If scope-limited diagnostics are useful, read saved outputs only. Do NOT recompute
another candidate or change thresholds without returning to Chat.

### 5. Outcomes and stopping

If the existing full gate passes, record candidate success on that development
record only. The next decision would be a new held-out geometry/seed and an
additive mirrored-step or opposite-eye half-occlusion test BEFORE fusion. Neither
acquisition is authorized here. A seed change alone would not validate different
geometry. The bright-full synthetic limitation must remain recorded.

If full fails, report which criterion and which instance failed. Do not delete
the veto, adopt a raw-linear score while leaving SGBM blind, increase support,
fit exposure, smooth/fill depth, or change scene brightness to pass. Decide the
next representation/support intervention with Luiz/Chat.

### Likely failures, in priority order

1. Low texture scores remain after compression/quantization: expected scientific
   possibility, as in the bright-full stress; report it, do not retune.
2. New SGBM peaks change accuracy/LR support: candidate effect, not a plumbing
   bug to hide. Compare common and gained/lost populations.
3. Replay/source mismatch: check interpreter and recorded versions, hashes,
   input paths and accidental source edits. Never relax equality or overwrite a
   record to force reproducibility.
4. Path/serialization/visualization fault demonstrated independently of numbers:
   a fix in the new orchestration code is delegated, outside tests/legacy modules.
   Describe the cause and every edit. If a partial output exists, leave it intact
   and stop for an explicitly named replacement path rather than silently erasing.

No modifications of tests, encoder, matcher, refiner, gate, fixtures, inputs,
profile/spp or truth separation are delegated.

## Paste-ready report format

```text
FSG1c FIXED HDR CANDIDATE REPORT
HEAD before/after; branch and push:
D-FSG1c recorded before candidate; all prior failures preserved:
Legacy diff and frozen hash verification:
Versions, no upgraded pins, no Blender/GPU execution:
Legacy/audit/candidate SUMMARY lines verbatim:
Three negative exits and FAIL lines verbatim:
Exact command; input, NEW output and log paths:
Legacy replay exact for all cases; all input hashes unchanged:
Mapping ID/formula; kernel-only-change check:
Per run/case/instance baseline -> candidate coverage/median/p95 and gate:
Full foreground old texture-only: count, newly accepted count and errors:
Full/small tilted: same cohorts, common/gained/lost counts and errors:
Score/saturation changes, with populations stated:
Boundary/singly-visible reference counts and NOT_EXERCISED where empty:
Wrong-instance counts; all candidate numerical FAIL lines:
Exact per-run statuses; process exit; no milestone/default/fusion adoption:
Runtime; original sample budgets; new_primary_samples=0:
Visuals and candidate PLY actually inspected, observations:
Unexpected failures and any delegated orchestration fixes:
Changed files; preserved fixtures/gates/legacy sources:
Stopped for Luiz/Chat; no new candidate/render/fusion:
```

Append measured Results below and to docs/log.md. Update the README row without
erasing historical failures, append the outcome to D-FSG1c, commit and push to
main. Regenerable data/PNGs/PLY/JSON go under previews/, not in Git.

## Results - workstation

Pending. No result from the real Blender arrays has been measured in Chat's
sandbox. Known analytic results are in the accompanying validation record.
