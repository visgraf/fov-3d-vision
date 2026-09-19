# FSG4 Increment 4 — active frontier policy versus fixed scan

## Status

Prospective Chat handoff. FSG1, FSG2 and FSG3 are closed. FSG3 established feasibility: one seed fixation plus the evolving head-frame map and current oracle mask chose the subsequent 5-degree saccades, stopped at the visible object boundary, and grew one planar visible surface from 33.6% to 100% coverage. FSG4 changes the scientific question from **can the loop work?** to **does the feedback loop buy sampling efficiency over a non-adaptive scan?**

This increment does not learn a policy, change stereo, change fusion, estimate pose, use ICP, move the head, control vergence, introduce folds/self-occlusion, switch objects, mesh, or fill holes.

## Scientific question

> At the same allowed camera-sample budget, does the frozen frontier policy acquire visible object surface more efficiently than one prospectively fixed non-adaptive symmetric scan?

The claim, if the gates pass, is deliberately limited to this controlled mirrored planar fixture family. It is **not** a claim that the frontier policy is optimal, nor a population-level statistical result.

## Frozen sensor, map and policy

- FSG1 instrument: `FSG1-HDR-SGBM-one-original-update-original-validity-v1`.
- Persistent frame: fixed head frame H.
- Oracle instance segmentation remains the only object-membership cue.
- Exact calibrated eye/head pose; no registration or ICP.
- FSG3 multi-look surfel map and 12 mm Euclidean association/hash cell.
- Fixed vergence distance 2.10 m.
- Active policy: the FSG3 horizontal frontier rule in substance: current mask edge evidence + current map extent, local +/-5 degree candidates, >=4 degree overlap, no revisit, stop on no frontier.
- Full profile: 256 spp. Small: 64 spp smoke only.

## Paired experimental design

Two **new**, opaque fixture IDs are used. Both are the same 0.95 x 0.32 m opaque diffuse tilted rectangle at z approximately -2.10 m, but at mirrored horizontal placements and with distinct procedural textures. Their geometry exists only in `fsg4_scene.py`; the active host/policy does not import it.

- `case_a`: one visible frontier from the common seed points left.
- `case_b`: its mirror; one visible frontier points right.

The names are opaque in the public contract; the active code never branches on them.

Two fresh Cycles Monte-Carlo seeds are frozen: **401 and 443**. Thus the full comparison contains four paired trials: 2 placements x 2 rendering seeds.

Every policy begins at yaw 0 degrees. The active policy chooses subsequent fixations from its evolving evidence. The non-adaptive control is frozen before acquisition as

```
0, -5, +5, -10, +10 degrees
```

for every fixture and seed. The scan consults neither RGB, segmentation, map nor geometry.

### Paired rendering noise

A view's Cycles seed is a deterministic function only of `(fixture, MC seed, yaw, eye)`, never policy or step. Therefore, whenever active and scan happen to visit the same yaw, their RGB and oracle arrays must be **exactly identical**. `fsg4_pair.py` verifies this after both runs. A mismatch is an integrity failure, not a numerical policy result.

## Equal-budget curve

The fixed scan always spends five fixations. Active may stop after 4 or 5 if the frontier is resolved. For comparison, define coverage after budget allowance k as the surface coverage obtained using **at most** k fixations. If active stops early, its final coverage is carried forward for the unused budget slots; its actually spent camera samples are still reported separately and must never exceed the scan's.

For each paired trial:

```
C_active(k), C_scan(k), k = 1..5
```

are evaluated on the same fixed object-surface truth grid. The normalized discrete trapezoidal area is

```
AUC(C) = (1/4) * sum_{k=1..4} 0.5 * (C(k) + C(k+1)).
```

The seed fixation is common to both policies, so the first curve point should agree up to exact paired rendering/reconstruction identity.

## Prospective gates

### A. Run integrity and metric geometry

Both policies, every full trial:

- final map point-to-plane median <= 10 mm;
- final map point-to-plane p95 <= 30 mm;
- map contains only object ID 81;
- duplicate replay is idempotent for every fused post-seed patch;
- coverage may not decrease by more than 0.5 percentage point at any step.

The scan is **not** required to achieve high completeness; poor spatial allocation is the quantity being measured, not an integrity failure.

### B. Active-policy validity

Every full active trial:

- 4 to 5 fixations total;
- termination must be `no_frontier`, not budget exhaustion;
- every active saccade is nonzero, <=5 degrees and never repeats a fixation;
- every active patch has >=90% object measurement coverage;
- each post-seed active patch has >=5,000 matched points;
- overlap median <=10 mm and p95 <=25 mm;
- nonterminal patches: >=15% new points and >=10 percentage points truth-coverage gain;
- terminal patch: >=5% new points and >=2 percentage points truth-coverage gain;
- final active truth coverage >=90%;
- gain over the seed >=35 percentage points.

These preserve the FSG3 feasibility contract while changing only the comparison question.

### C. Active-versus-scan comparison

Across the four full paired trials:

1. active AUC must exceed scan AUC in **all 4 / 4 pairs**;
2. mean paired AUC advantage must be >= **0.10** (10 coverage-percentage-point AUC units);
3. mean final-coverage advantage must be >= **0.10**;
4. active actual camera samples must be <= scan samples in every pair;
5. all shared-yaw observations must be exactly paired as specified above.

No alternate scan, threshold, placement, seed, or AUC definition may be selected after seeing results.

## Analytic design check — not a result

Before rendering, `fsg4_scene.py` checks only that the geometry makes the comparison non-degenerate. With ideal 12-degree angular intervals, the fixed scan covers roughly 0.84 of `case_a` and 0.79 of `case_b`, while five monotone local looks can bracket the far boundary in either direction. These are **design estimates**, not Blender measurements and not acceptance numbers.

## Execution order

### 1. Preflight / software checks — Interactive

```bash
.venv/bin/python tools/fsg4_scene.py
.venv/bin/python tools/fsg4_policy.py
.venv/bin/python tools/fsg4_metrics.py
.venv/bin/python tools/dev/check_fsg4.py --self-test
```

Expected new summary:

```text
[fsg4-check] SUMMARY passed=6 failed=0
```

Run all existing FSG1/FSG2/FSG3 regression suites unchanged.

Negative controls — each must exit 1:

```bash
.venv/bin/python tools/dev/check_fsg4.py --negative frontier
.venv/bin/python tools/dev/check_fsg4.py --negative scan
.venv/bin/python tools/dev/check_fsg4.py --negative pairing
.venv/bin/python tools/dev/check_fsg4.py --negative auc
```

They demonstrate respectively that a wrong/hard-coded frontier can fail, the fixed scan cannot silently become a one-sided favourable sweep, same-yaw paired render noise cannot drift with policy/step, and a no-advantage coverage curve cannot pass the AUC rule.

### 2. One small paired smoke — Batch / diagnostic

```bash
.venv/bin/python -u tools/fsg4_pair.py \
  --repo . --out previews/fsg4/smoke-case_a-seed401 \
  --profile small --fixture case_a --seed 401 --mode smoke --device OPTIX
```

Inspect both truth-free `growth.png` files, both post-hoc `growth_truth.png` files, both manifests, and `pair.json`. Numerical small-profile misses are diagnostic, as in the prior increments. Stop before full only on an integrity/provenance/runtime failure.

### 3. Four full paired trials — each command is Batch

Run all four predeclared pairs once. A numerical exit 2 from one completed pair does **not** authorize tuning and does not cancel the remaining predeclared pairs; an integrity exception does.

```bash
.venv/bin/python -u tools/fsg4_pair.py --repo . --out previews/fsg4/full-case_a-seed401 --profile full --fixture case_a --seed 401 --mode full --device OPTIX
.venv/bin/python -u tools/fsg4_pair.py --repo . --out previews/fsg4/full-case_a-seed443 --profile full --fixture case_a --seed 443 --mode full --device OPTIX
.venv/bin/python -u tools/fsg4_pair.py --repo . --out previews/fsg4/full-case_b-seed401 --profile full --fixture case_b --seed 401 --mode full --device OPTIX
.venv/bin/python -u tools/fsg4_pair.py --repo . --out previews/fsg4/full-case_b-seed443 --profile full --fixture case_b --seed 443 --mode full --device OPTIX
```

Then aggregate exactly those four:

```bash
.venv/bin/python tools/fsg4_compare.py \
  previews/fsg4/full-case_a-seed401 \
  previews/fsg4/full-case_a-seed443 \
  previews/fsg4/full-case_b-seed401 \
  previews/fsg4/full-case_b-seed443 \
  --out previews/fsg4/full-comparison
```

Inspect `coverage_vs_budget.png` and `comparison.json`.

## Decision D-FSG4a

Record before acquisition:

> **D-FSG4a — Compare active frontier growth with one fixed symmetric scan.** Keep the closed FSG1 instrument, FSG3 frontier policy in substance, FSG3 multi-look head-frame fusion and all metric-geometry gates. On two new mirrored planar placements with distinct textures and fresh seeds 401/443, compare the active policy against the single frozen non-adaptive scan `0,-5,+5,-10,+10` at a five-fixation camera budget. Pair rendering noise by fixture/seed/yaw/eye. The primary number is truth-grid surface coverage versus budget and its fixed normalized AUC. A pass requires all four active runs to remain valid, all four scan maps to remain metrically valid, exact same-yaw pairing, active AUC wins in 4/4 pairs, mean AUC advantage >=0.10 and mean final-coverage advantage >=0.10. No alternative scan or threshold may be selected after results.
>
> If the full comparison passes, close Increment 4 and record that active frontier feedback improves sampling efficiency over this fixed-scan control on the controlled mirrored planar family. Authorize, but do not implement, the next experiment. If it misses, preserve all pairs and stop for Luiz/Chat. Code may fix only demonstrated implementation/orchestration defects that violate this written experiment; never change the instrument, policy, scan, geometry, texture, seed, fusion radius, budget or gates to obtain a pass.

## What Code may fix

Only a demonstrated implementation/orchestration defect, such as repository API drift, wrong path/serialization, a frame-conversion bug, a mismatch between the written paired-seed rule and its implementation, or a comparison arithmetic bug. A fix must not change any scientific setting above and must be described before rerunning the affected command.

## What Code must report

Return a paste-ready report containing:

- HEAD before/after, branch, push, D-FSG4a timing and frozen-source diff;
- environment and all regression/new-check summaries plus all four expected negative FAIL lines;
- exact smoke and four full pair commands, exit codes, samples and timings;
- every active trajectory and stop reason;
- per-policy coverage curve for every full pair;
- per-pair active/scan AUC and AUC gain;
- final coverage and final coverage gain per pair;
- paired shared-yaw count and exact-observation result;
- final map median/p95 plane error and purity for both policies in every pair;
- aggregate win count, mean AUC gain, mean final-coverage gain and every FAIL line;
- visual observations from `coverage_vs_budget.png` and representative growth plots;
- any code fix, one sentence each;
- final status exactly `FSG4_INCREMENT4_PASS` or `FSG4_INCREMENT4_FAIL`;
- if PASS, state Increment 4 closed and the next experiment authorized but not implemented. Do not design or implement the next increment.

## Results

Run 2026-09-19 on the workstation by Code. Every number is read from files under
`previews/fsg4/`.

**Execution STOPPED at the small paired smoke on an integrity failure. The four
full paired trials and the comparison were NOT run. Increment 4 is NOT closed and
no next experiment is authorized.** No `FSG4_INCREMENT4_PASS` / `FSG4_INCREMENT4_FAIL`
status exists, because `fsg4_compare.py` was never executed.

    AssertionError: paired observation differs at shared yaw -10.0

`fsg4_pair.py` exit 1. Under section 2 an integrity/provenance/runtime failure
stops before full, and the handoff states explicitly that a paired-observation
mismatch "is an integrity failure, not a numerical policy result". This is **not**
a numerical result about either policy.

### Diagnosis: the renderer is not bit-reproducible on this GPU

The paired-noise rule itself is implemented exactly as written and works. At all
three shared yaws the Cycles seeds are identical and the oracle instance masks are
bit-exact; only the RGB float arrays differ, by one to two float32 ulp:

| shared yaw | active step / scan step | seeds_lr equal | instance_L/R equal | rgb_L / rgb_R differing elements | max abs diff |
| ---: | --- | --- | --- | --- | ---: |
| 0.0 | 0 / 0 | true (40100050, 40100051) | true | 177,748 / 186,798 of 307,200 | 5.96e-07 |
| -5.0 | 1 / 1 | true (40100040, 40100041) | true | 175,544 / 175,029 | 4.77e-07 |
| -10.0 | 2 / 3 | true (40100030, 40100031) | true | 173,508 / 174,289 | 4.77e-07 |

A controlled reproducibility test settles the cause. Rendering the **identical
command** twice - same fixture, seed, yaw AND same step - produces the same
discrepancy as two renders at different steps:

| comparison | seeds | instance masks | rgb differing elements | max abs diff |
| --- | --- | --- | --- | ---: |
| r1 vs r2, identical command, same step 2 | identical | bit-exact | 174,461 / 173,449 | 4.768e-07 |
| r1 vs r3, same yaw, step 2 vs step 3 | identical | bit-exact | 174,386 / 173,221 | 4.768e-07 |

The seed rule is confirmed step-independent - all three renders report
`seeds_lr = [40100030, 40100031]`. So the difference is **not** policy or step
leakage: Cycles/OptiX floating-point accumulation is non-associative under
parallel scheduling, and identical inputs give last-ulp differences on this
hardware. `fsg4_public.render_seed(fixture, seed, yaw_deg, eye_id)` takes no
policy or step argument and behaves exactly as specified.

The scientific purpose of the pairing control - that both policies see the same
observation at a shared yaw - is satisfied in substance. At yaw -10.0 every
reconstruction statistic is bit-identical between the two policies:

| quantity at shared yaw -10.0 | active step 2 | scan step 3 | identical |
| --- | ---: | ---: | --- |
| point_count / object_valid_count | 10,911 | 10,911 | yes |
| object_reference_count | 11,754 | 11,754 | yes |
| object_measurement_fraction | 0.9282797345584481 | 0.9282797345584481 | yes |
| matched / new | 6,069 / 4,842 | 6,069 / 4,842 | yes |
| overlap median | 0.003912357932249099 m | 0.003912357932249099 m | yes |

### Why I did not fix it

`fsg4_pair.py` uses `np.array_equal`, which faithfully implements the written
requirement that the arrays "must be exactly identical". The implementation is
not defective; the specification's bit-exactness assumption is unachievable for
RGB on this renderer. That makes it a specification question, not "a demonstrated
implementation/orchestration defect that violates the written experiment", which
is the only category D-FSG4a delegates to Code.

Relaxing the comparison to a tolerance would also change gate C5 - "all
shared-yaw observations must be **exactly** paired as specified above" - and
would blunt the `--negative pairing` control, whose whole purpose is to prove
this check can fail. Choosing a tolerance is a scientific judgement with no
prescribed value. Nothing was altered: `git diff` against the handoff commit
shows no change under `tools/`, and no scan, policy, geometry, texture, seed,
fusion radius, budget, threshold or gate was touched.

### What the smoke did show, diagnostic only

The small paired smoke completed both runs before the pairing assertion, so these
numbers exist but are **small-profile diagnostics on one pair, not a result**, and
the prescribed full comparison was not run. Both runs reported
`FSG4_..._RUN_FAIL` on their own small-profile gates (plane error median/p95 for
both; `fix_03` object coverage 89.76% for active).

The active policy chose `0, -5, -10, -15` degrees and stopped on `no_frontier`
after 4 fixations using 52,428,800 samples, reaching 94.67% coverage. The fixed
scan spent all five fixations and 65,536,000 samples, reaching 85.73%. Its third
look at +5 added 2.33 percentage points and its fifth at +10 landed essentially
off-object - 384 reference points, 58 valid, `skipped_too_few_object_points: true`
- adding 0.00 points of coverage. That is precisely the "poor spatial allocation"
the experiment is built to measure, and the handoff is explicit that it is not an
integrity failure for the scan. It is also exactly why these numbers must not be
reported as the outcome: one small-profile pair is not the four-pair full
comparison, and the AUC aggregation never ran.

### Integrity of everything else

HEAD `4166d0c14702f41e9ccbd997adab8177108d67a8` on clean `main`, `cf3601a` an
ancestor. The FSG1/FSG2/FSG3 frozen diff over the twenty-one pinned modules,
`rig.py`, `bl_common.py` and `requirements-fsg.txt` is EMPTY; eleven files added
by the handoff and none modified. Python 3.12.3, NumPy 2.2.6, OpenCV 4.13.0,
Pillow 12.3.0; Blender 5.2.1 LTS, OPTIX on an RTX 4090. D-FSG4a and a prospective
`docs/log.md` entry were recorded BEFORE any acquisition.

Structural invariants verified by reading the code beforehand: `fsg4_run.py` and
`fsg4_policy.py` import no fixture geometry and open no evaluator-only asset;
the loop calls `compute_once` with `check_kernel_equivalence`, never
`compute_variants`; `SCAN_YAWS_DEG = (0.0, -5.0, 5.0, -10.0, 10.0)` is the single
frozen control.

`[fsg4-scene] PASS case_a=[-19.847,4.189] scan_ideal=0.840 case_b=[-3.874,21.329] scan_ideal=0.789`,
`[fsg4-policy] PASS mirrored_frontiers=true resolved_frontier_stops=true`,
`[fsg4-metrics] PASS known_auc_gain=0.220000 early_stop_padding=true`,
`[fsg4-check] SUMMARY passed=6 failed=0`. All four negatives exit 1:

    [fsg4-check] FAIL AssertionError deliberate hard-coded/wrong frontier direction detected
    [fsg4-check] FAIL AssertionError deliberate fixture-favouring scan mutation detected
    [fsg4-check] FAIL AssertionError deliberate paired-noise mismatch detected
    [fsg4-check] FAIL AssertionError deliberate no-active-advantage curve detected

All ten FSG1/FSG2/FSG3 regression suites pass unchanged: 24 / 29 / 34 / 48 / 37 /
46 / 4 / 5 / 7 / 8.

### What has to be decided

The pairing criterion needs a decision that is Chat's and Luiz's, not mine:
whether "exactly identical" should remain bit-exact - in which case this
comparison cannot run on this GPU as specified and needs a deterministic
rendering path - or whether the control should be restated as bit-exact seeds and
oracle masks plus an explicit RGB tolerance, with a stated value and gate C5
reworded to match. Either way the four full pairs and the AUC aggregation remain
unrun and unprejudiced; no alternate scan, threshold, placement, seed or AUC
definition has been seen or selected. Increment 4 stays open. Stopped for Luiz
and Chat.
