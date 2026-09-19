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
