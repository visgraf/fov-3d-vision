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

Run 2026-09-19 by Code. Every number is read from
`previews/fsg1/hdr-candidate-seed17/comparison.json` and its per-case files.
Chat's validation record in `docs/fsg1-hdr-validation.md` is untouched, and the
bright-full stress failure recorded there stands. **Zero new primary camera
samples**; no Blender or GPU process ran.

Process exit 2 - completed with at least one candidate numerical miss. Per run:

| record | status | candidate gates |
| --- | --- | --- |
| `small-seed17` | `CANDIDATE_FAIL_ON_EXISTING_RECORD` | step instance 2 median/p95 |
| **`full-seed17`** | **`CANDIDATE_PASS_ON_EXISTING_RECORD`** | **all pass, no fails** |
| `diag-small-spp1024-seed17` | `CANDIDATE_PASS_ON_EXISTING_RECORD` | all pass, no fails |

The exit-2 miss is the **small** record's pre-existing background accuracy
failure, not a full-profile miss. Suite-level flags stay
`full_profile_milestone_pass: false`, `fusion_authorized: false`,
`adopted_default: false`, status `CANDIDATE_COMPARISON_COMPLETE_NOT_A_MILESTONE`.

### Integrity

HEAD `85aee968894b2eaa16dd8428d87da6185d14aefb` on clean `main`, with `64e02af`
verified an ancestor. `git diff 64e02af` over the twelve original modules, checks,
`rig.py`, `bl_common.py` and `requirements-fsg.txt` is EMPTY before and after.
The runtime additionally pinned the four frozen hashes (`fsg_geometry`,
`fsg_scene`, `fsg_stereo`, `fsg_evaluate`). Python 3.12.3, NumPy 2.2.6, OpenCV
4.13.0, Pillow 12.3.0 - the same venv that produced the records; no pin moved.

`legacy_replay_exact: true` and `baseline_preserved: true` for all nine
case-records. `input_sha256_before == input_sha256_after` across 167 paths, and
I fingerprinted the same 167 files myself before and after: byte-identical. The
original `evaluation.json` of both baselines still reads `status: FAIL` with two
fails each. Candidate artifacts went to a new disjoint tree under
`stereo_candidate/` and `candidate_points_head.ply`; the legacy `stereo/` was
never written.

Checks: `[fsg-check] SUMMARY passed=24 failed=0 seconds=1.869`,
`[fsg-audit-check] SUMMARY passed=29 failed=0 seconds=1.992`,
`[fsg-hdr-check] SUMMARY passed=34 failed=0 seconds=2.357`, all
`blender_executed=False`. The three deliberate negatives each exit 1:
collapsed HDR values, altered saved validity, and the 20% depth-scale corruption.

The mapping is `sRGB(max(x,0)/(1+max(x,0)))` then `round(255*y)`, fixed scale 1.0
scene-linear unit, identical for both eyes, `per_eye_normalization: false`. Read
directly: `hdr_to_u8` calls the FROZEN legacy `linear_to_u8` for the sRGB and
quantization step, where that function's clip is a no-op, so the only new
arithmetic is the pre-transfer compression. SGBM and the unchanged 5x5 texture
score see the encoded image; the bounded refiner still receives ORIGINAL
scene-linear float RGB. Cutoff, windows, search bounds, instance guard, LR check,
refinement iterations and every evaluator rule are unchanged.

### Baseline -> candidate, same fixed reference

| run / case / instance | ref | legacy cov / med / p95 | candidate cov / med / p95 | gate |
| --- | ---: | --- | --- | --- |
| small / fronto | 16384 | 98.395% / 0.388% / 1.315% | 100.000% / 0.380% / 1.313% | pass |
| small / tilted | 16384 | 99.823% / 0.463% / 1.680% | 100.000% / 0.457% / 1.667% | pass |
| small / step inst 1 | 9088 | 90.361% / 0.187% / 0.792% | 100.000% / 0.198% / 0.822% | pass |
| small / step inst 2 | 6016 | 99.751% / 1.136% / 4.111% | 99.767% / **1.138%** / **4.065%** | FAIL |
| **full / fronto** | 65536 | 94.786% / 0.285% / 1.159% | **99.019%** / 0.284% / 1.112% | pass |
| **full / tilted** | 65536 | 98.433% / 0.318% / 1.348% | **98.912%** / 0.318% / 1.366% | pass |
| **full / step pooled** | 60928 | 87.502% / 0.268% / 1.950% | **99.445%** / 0.250% / 1.907% | pass |
| **full / step inst 1** | 36608 | **79.319%** / 0.137% / 0.595% | **99.361%** / 0.142% / 0.649% | pass |
| **full / step inst 2** | 24320 | 99.819% / 0.785% / 2.497% | 99.572% / 0.796% / 2.572% | pass |
| diag1024 / fronto | 16384 | 98.376% / 0.266% / 0.815% | 100.000% / 0.251% / 0.781% | pass |
| diag1024 / tilted | 16384 | 99.829% / 0.336% / 1.146% | 99.994% / 0.332% / 1.133% | pass |
| diag1024 / step inst 1 | 9088 | 90.284% / 0.104% / 0.363% | 99.978% / 0.101% / 0.379% | pass |
| diag1024 / step inst 2 | 6016 | 99.751% / 0.618% / 1.846% | 99.817% / 0.607% / 1.837% | pass |

The full-profile coverage miss is resolved: step foreground 79.319% -> 99.361%,
pooled step 87.502% -> 99.445%, with every median and p95 still inside the 1% and
3% limits and `wrong_instance_accepted_count` 0 for legacy and candidate alike in
all nine cases. The small record's background accuracy miss is essentially
untouched (1.136% -> 1.138% median, 4.111% -> 4.065% p95), which is what should
happen: that instance had 0.000% clipped pixels, so the encoding has nothing to
recover there. It remains an angular-resolution limit, not a radiometric one.

### Paired support, and where the recovered pixels came from

| run / case / instance | common | gained | lost | neither | old tex-only | now accepted | common med L -> C | gained med / p95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| **full / step inst 1** | 29029 | **7345** | **8** | 226 | 7549 | **7335** | 0.137% -> 0.135% | 0.176% / 0.867% |
| full / step inst 2 | 24195 | 21 | 81 | 23 | 1 | 0 | 0.782% -> 0.796% | 1.993% / 4.986% |
| full / fronto | 61825 | 3068 | 294 | 349 | 3361 | 3027 | 0.284% -> 0.281% | 0.361% / 1.389% |
| full / tilted | 64028 | 795 | 481 | 232 | 934 | 741 | 0.318% -> 0.316% | 0.563% / 1.844% |
| small / tilted | 16355 | 29 | 0 | 0 | 29 | 29 | 0.463% -> 0.457% | **1.914% / 4.084%** |
| small / step inst 1 | 8212 | 876 | 0 | 0 | 876 | 876 | 0.187% -> 0.191% | 0.268% / 1.182% |

On the failing instance the candidate accepts 7,335 of the 7,549 old texture-only
pixels (97.2%) and loses only 8. Crucially the gain is not a resurrection of the
old diagnostic hypotheses: the newly accepted pixels are re-derived from the
encoded images and independently evaluated at 0.176% median / 0.867% p95 with
**no pixel over 3%**, against those old hypotheses' 0.178% / 0.889%. On the common
support the candidate is marginally BETTER (0.137% -> 0.135%), so the new SGBM
peaks did not degrade shared pixels.

Regressions are real and small. full/step instance 2 nets -60 pixels (81 lost,
21 gained) and both error quantiles rise slightly, still inside the gate.
full/tilted loses 481 and gains 795, scattered rather than clustered.

The FSG1b counterexample survives the candidate and deserves its own line. On
small/tilted, all 29 old texture-only pixels are now ACCEPTED, and as candidate
geometry they measure 1.914% median / 4.084% p95 - far worse than that case's
0.457% / 1.667% overall, and consistent with the audit's finding that 10 of those
29 exceeded 3%. They pass only because 29 pixels among 16,384 cannot move an
aggregate. **n = 29; this is a specific observation, not a population estimate.**
It is direct evidence that the candidate admits some genuinely weak evidence
along with the clipped-but-good evidence.

### Scores and saturation: fewer dead pixels, not more contrast

Population is each instance group's full interior reference, legacy vs candidate:

| run / case / instance | legacy med score | candidate med score | legacy zero | candidate zero | candidate < 0.5 cutoff | candidate all-255 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| full / step inst 1 | 4.508 | 2.708 | 14.243% | 0.014% | 0.601% | 0.000% |
| full / fronto | 5.056 | 2.519 | 2.513% | 0.012% | 0.896% | 0.000% |
| full / tilted | 5.109 | 2.547 | 0.392% | 0.015% | 0.938% | 0.000% |
| full / step inst 2 | 5.052 | 3.398 | 0.000% | 0.000% | 0.263% | 0.000% |
| small / step inst 1 | 8.325 | 4.721 | 5.777% | 0.000% | 0.000% | 0.000% |
| diag1024 / step inst 1 | 8.335 | 4.715 | 5.843% | 0.000% | 0.022% | 0.000% |

This is the honest mechanism, and it is not "the candidate finds more texture".
Median scores roughly HALVE under compression - the candidate image has LESS
contrast overall. What changes is the dead zone: exactly-zero scores collapse
from 14.243% to 0.014% on the failing instance, and no pixel anywhere saturates
to 255 in all channels. Coverage is recovered by removing hard saturation, not by
amplifying signal. Bright structure in a score panel is not calibrated confidence.

That halving is also the visible cost, and it points at the known stress. Because
typical scores are now about half as large, the unchanged 0.5 cutoff sits
relatively closer to the bulk of the distribution: 0.6-0.9% of full-profile
reference pixels now fall below it, where at small the figure is 0.000%. On a
brighter scene the compression would push more of the distribution down, which is
exactly the regime of Chat's analytic bright-full stress (fronto 79.097%, tilted
78.828%, step pooled 86.809%, foreground 85.760%, background 88.388% - all
coverage failures with in-limit errors). **That limitation is unaltered by this
result and must travel with it.**

### Boundary, half-occlusion, visuals

Boundary is EXERCISED only on step and improves without being gated: full/step
2,362 -> 2,819 accepted, median 0.604% -> 0.484%, p95 3.266% -> 2.857%; small/step
395 -> 420 with median 0.900% -> 0.741%; diag1024/step 411 -> 430. Interior
accuracy still does not validate boundary accuracy.

`singly_visible` reference count is 0 in **all nine case-records** for legacy and
candidate alike: **NOT_EXERCISED**. Unchanged by this candidate, not a pass, and
the mirrored-step or opposite-eye test is still required before any fusion.

Inspected `comparison.png` for full/step, full/tilted, full/fronto and
small/tilted, and `comparison.json` for all nine. full/step: the legacy panel's
left half is blown to near-white while the candidate panel shows clear mid-grey
structure across it; legacy validity has large holes in that half, candidate
validity is near-solid white apart from a few specks and the boundary band;
"newly accepted" lights up exactly where the legacy holes were; "lost support" is
black but for a scatter of dots, mostly on the background side; the candidate
error panel is near-black on the foreground and visibly noisier on the 3.4 m
background, matching 0.142% against 0.796%. full/fronto and full/tilted show the
same pattern at lower severity, tilted's losses scattered rather than clustered.
small/tilted shows 29 pixels gained, none lost, exactly as tabulated. Remaining
holes are shown as missing, never interpolated.

`stereo_candidate/result.npz` and `candidate_points_head.ply` for full/step:
63,409 vertices against the legacy 55,675, no faces, head-frame comment, instance
medians Z = -1.6002 m and -3.4006 m against -1.6 and -3.4, all coordinates in the
fixed H frame. Candidate stereo cost 0.379 s for the whole full record; the
comparison took 5.713 s end to end, with original budgets of 39,321,600 /
629,145,600 / 629,145,600 samples and **0 new samples**.

### What this does and does not establish

On the existing full seed-17 record the single fixed encoding change removes the
coverage miss while holding every accuracy criterion, with recovered geometry
independently evaluated and only 8 pixels lost on that instance. That is the
cleanest possible outcome for this intervention, and it is still
**development-set evidence**: these same records produced the diagnosis and
selected the candidate, so the comparison is not independent validation. Nothing
is adopted; no default changed; the legacy encoder remains the instrument.

Three limits travel with this result: the analytic bright-full stress still fails
coverage under this same encoding, so an 8-bit fixed-window system is not solved;
the small/tilted cohort shows the candidate admitting weak evidence that the veto
used to catch; and half-occlusion remains unexercised. The next steps would be a
held-out geometry and seed, and an additive mirrored-step or opposite-eye
half-occlusion fixture, BEFORE any fusion. Neither acquisition is authorized here
and none was performed.
