# FSG4b — exact shared-view reuse for the FSG4 paired comparison

## Status

Corrective orchestration handoff after FSG4a stopped at the small paired-noise integrity gate. FSG4a produced no full-profile policy comparison and no Increment-4 scientific outcome. The existing FSG1/FSG2/FSG3 results remain closed and unchanged.

The scientific FSG4 experiment is **not changed**: same active frontier policy, same fixed scan `0,-5,+5,-10,+10`, same two fixtures, seeds 401/443, stereo instrument, fusion, five-fixation budget, AUC definition, geometry gates and pass thresholds. Gate C5 also remains exact: when the two policies consume the same `(fixture, MC seed, yaw, eye)` observation, the saved RGB/oracle arrays must be bit-identical.

## What FSG4a demonstrated

The workstation showed that two independent OptiX executions of the same seeded view are not bit-reproducible: the oracle masks and render seeds are exact, but scene-linear float32 RGB differs by roughly one to two ulp, with a measured maximum absolute discrepancy of 5.96e-7. Repeating the identical command reproduced the same effect. The discrepancy did not change the reported reconstruction statistics, but it correctly tripped the written exact-pairing gate.

This is an execution-property mismatch, not a policy result. The four full paired trials were never run.

## D-FSG4b — preserve exact pairing by reusing the observation artifact

Do **not** weaken Gate C5 and do **not** introduce an RGB tolerance.

For each paired trial:

1. run the active policy first, exactly as in FSG4a;
2. index its completed acquisition records by yaw;
3. run the fixed scan second;
4. if a scan yaw was already visited by active, clone that completed acquisition record into the scan step, rewriting only step-local metadata;
5. if a scan yaw was not visited by active, render it normally with the frozen yaw-keyed seed rule;
6. after both policies complete, require exact equality of every saved array and exact seed equality at every shared yaw, and require the scan shared-yaw record to declare that it reused the active observation.

The active run never receives the cache and cannot inspect scan state. `fsg4_run.py` remains truth-free: it imports no fixture geometry and opens no `evaluation_only` asset. The paired orchestration layer performs the file clone after the active run is complete. The fixed scan is nonadaptive, so reuse cannot influence its fixation schedule.

### Camera-sample accounting

The scientific budget remains **logical camera samples consumed by each policy**. A reused shared view is still charged to the scan exactly as one fixation, because the comparison asks how many observations the policy consumes, not how many GPU renders the test harness happened to execute.

For provenance only, the run also records `new_primary_camera_samples`: newly rendered samples during this execution. Reusing an already-rendered paired observation contributes zero to that execution-cost field but does not reduce `primary_camera_samples` or the policy's budget.

## Why this is preferable to a tolerance

Artifact reuse makes the paired condition true by construction rather than deciding after the smoke run how much RGB inequality to tolerate. It preserves the original exact integrity gate, removes OptiX scheduling nondeterminism from the paired comparison, and keeps the full-profile scientific comparison unprejudiced: no full FSG4 pair has yet been observed.

## Frozen scientific contract

Unchanged from FSG4a:

- active policy: frozen FSG3 frontier rule;
- fixed scan: `0,-5,+5,-10,+10` degrees;
- fixtures: `case_a`, `case_b`;
- seeds: 401 and 443;
- full profile: 256 spp;
- FSG1 instrument: `FSG1-HDR-SGBM-one-original-update-original-validity-v1`;
- fixed head frame, oracle segmentation, exact pose, no ICP, no mesh or fill;
- FSG3 multi-look fusion, 12 mm association;
- five-fixation allowed budget;
- same AUC and final-coverage gates;
- same active-run and map-accuracy gates.

No alternate scan, seed, fixture, threshold, AUC definition or policy is authorized.

## Execution order

### 1. Preflight — Interactive

Run the FSG4 scene/policy/metric checks, then:

```bash
.venv/bin/python tools/dev/check_fsg4.py --self-test
```

Expected new summary:

```text
[fsg4-check] SUMMARY passed=7 failed=0
```

The added seventh check constructs a synthetic completed acquisition, reuses it at a different step, verifies the observation file remains byte-identical, verifies zero newly rendered samples for the clone, and re-runs the exact shared-view verifier.

Run all existing FSG1/FSG2/FSG3 regression suites unchanged.

All four existing negatives must still exit 1:

```bash
.venv/bin/python tools/dev/check_fsg4.py --negative frontier
.venv/bin/python tools/dev/check_fsg4.py --negative scan
.venv/bin/python tools/dev/check_fsg4.py --negative pairing
.venv/bin/python tools/dev/check_fsg4.py --negative auc
```

The repaired `pairing` negative mutates one float in an otherwise reused observation and must fail the exact pairing check. Therefore FSG4b has not weakened the integrity gate.

### 2. New small smoke — Batch / diagnostic

Preserve the stopped FSG4a record. Use a new output root:

```bash
.venv/bin/python -u tools/fsg4_pair.py \
  --repo . --out previews/fsg4b/smoke-case_a-seed401 \
  --profile small --fixture case_a --seed 401 --mode smoke --device OPTIX
```

Numerical small-profile misses remain diagnostic. Stop before full only on an integrity/provenance/runtime failure. Before continuing, verify from `pair.json` that all shared yaws are exact and reused, and that logical camera samples are unchanged by reuse.

### 3. Four full pairs — Batch

Run each prescribed full pair exactly once under new paths:

```bash
.venv/bin/python -u tools/fsg4_pair.py --repo . --out previews/fsg4b/full-case_a-seed401 --profile full --fixture case_a --seed 401 --mode full --device OPTIX
.venv/bin/python -u tools/fsg4_pair.py --repo . --out previews/fsg4b/full-case_a-seed443 --profile full --fixture case_a --seed 443 --mode full --device OPTIX
.venv/bin/python -u tools/fsg4_pair.py --repo . --out previews/fsg4b/full-case_b-seed401 --profile full --fixture case_b --seed 401 --mode full --device OPTIX
.venv/bin/python -u tools/fsg4_pair.py --repo . --out previews/fsg4b/full-case_b-seed443 --profile full --fixture case_b --seed 443 --mode full --device OPTIX
```

A completed pair may exit 2 for a numerical miss; that does not authorize tuning and does not cancel the other predeclared pairs. An integrity exception stops execution.

Aggregate exactly those four:

```bash
.venv/bin/python tools/fsg4_compare.py \
  previews/fsg4b/full-case_a-seed401 \
  previews/fsg4b/full-case_a-seed443 \
  previews/fsg4b/full-case_b-seed401 \
  previews/fsg4b/full-case_b-seed443 \
  --out previews/fsg4b/full-comparison
```

Inspect `coverage_vs_budget.png`, `comparison.json`, representative active/scan growth plots and `pair.json` pairing rows.

## Decision rule

The FSG4a scientific gates remain the decision rule. If the four-pair full comparison passes them, close Increment 4 and record the limited claim that active frontier feedback improves surface acquisition efficiency over this one frozen nonadaptive scan on the controlled mirrored planar family. If the comparison misses, preserve all four pairs and stop for Luiz/Chat.

No next-increment implementation is delegated.

## What Code may fix

Only a demonstrated implementation/orchestration defect in this handoff. In particular, Code may not change the policy, scan, geometry, texture, seed, stereo instrument, fusion radius, camera budget, metric, thresholds, exact-pairing requirement or pass rule.

## Required report

In addition to the original FSG4 report fields, report for every pair:

- shared-yaw count and exact-array result;
- number of scan shared views reused from active;
- logical `primary_camera_samples` for each policy;
- `new_primary_camera_samples` actually rendered by the harness;
- confirmation that active received no cache/provider and that `fsg4_run.py` remains truth-free;
- every active and scan coverage curve, AUC, final coverage, map median/P95 error and purity;
- aggregate AUC win count, mean AUC advantage, mean final-coverage advantage and final status.

## FSG4b Results — exact shared-view reuse executed; comparison ran; Increment 4 NOT closed

Run 2026-09-19 on the workstation by Code. Every number is read from files under
`previews/fsg4b/`.

**Final status: `FSG4_INCREMENT4_FAIL`.** The pairing repair worked and the full
four-pair comparison ran for the first time. **Every comparison gate (C) passed
emphatically**, but the **active-run validity contract (B) failed on `case_b` at
both seeds**, so the increment does not close. Increment 4 remains OPEN and no
next experiment is authorized. All four pairs are preserved. Nothing was tuned.

    [fsg4-compare] fails: ["case_b/401 active run failed", "case_b/443 active run failed"]
    active fails, both case_b seeds: ["fix_04 too little new surface",
                                      "active fixation 4 added too little visible surface"]

### The exact-pairing gate was preserved, not relaxed

`fsg4_pair.py` still compares with `np.array_equal`; no tolerance exists anywhere.
The gate is now **stricter**: a shared yaw must have exact arrays AND exact seeds
AND a declared `paired_observation_reused` flag. The repaired `--negative pairing`
control mutates one float in an otherwise reused observation and still exits 1 —
direct proof the gate was not weakened.

Only three orchestration files differ from FSG4a: `tools/dev/check_fsg4.py`,
`tools/fsg4_pair.py`, `tools/fsg4_run.py`. `git diff d4104d9` over
`fsg4_scene.py`, `fsg4_policy.py`, `fsg4_metrics.py`, `fsg4_public.py`,
`fsg4_eval.py`, `fsg4_compare.py`, the FSG1 stereo modules,
`fsg3_surface_map.py`, `rig.py`, `bl_common.py` and `requirements-fsg.txt` is
EMPTY. `fsg4_run.py` remains truth-free and `truth_opened` is false for all eight
runs.

Checks: `[fsg4-check] SUMMARY passed=7 failed=0` including the new "exact
shared-view artifact reuse" check; all four negatives exit 1; all ten
FSG1/FSG2/FSG3 regression suites pass 24/29/34/48/37/46/4/5/7/8.

### Pairing and budget accounting, all four pairs

| pair | shared yaws | count | arrays exact | seeds exact | scan views reused | active reuse |
| --- | --- | ---: | --- | --- | ---: | ---: |
| case_a/401 | -10, -5, 0 | 3 | true | true | 3 | **0** |
| case_a/443 | -10, -5, 0 | 3 | true | true | 3 | **0** |
| case_b/401 | 0, +5, +10 | 3 | true | true | 3 | **0** |
| case_b/443 | 0, +5, +10 | 3 | true | true | 3 | **0** |

| pair | active logical | scan logical | active <= scan | active newly rendered | scan newly rendered |
| --- | ---: | ---: | --- | ---: | ---: |
| case_a/401 | 838,860,800 | 1,048,576,000 | yes | 838,860,800 | 419,430,400 |
| case_a/443 | 838,860,800 | 1,048,576,000 | yes | 838,860,800 | 419,430,400 |
| case_b/401 | 1,048,576,000 | 1,048,576,000 | yes (equal) | 1,048,576,000 | 419,430,400 |
| case_b/443 | 1,048,576,000 | 1,048,576,000 | yes (equal) | 1,048,576,000 | 419,430,400 |

Active's newly rendered samples equal its logical samples in every pair, which
independently confirms it rendered every view itself and received no cache. Reuse
never reduced any policy's logical budget: the scan is still charged five
fixations everywhere.

### Coverage curves, AUC and final coverage

| pair | policy | C(1..5) | AUC | final |
| --- | --- | --- | ---: | ---: |
| case_a/401 | active | 0.44112, 0.65625, 0.88629, 0.99995, 0.99995 | 0.815756 | 0.999947 |
| case_a/401 | scan | 0.44112, 0.65625, 0.65625, 0.88629, 0.88629 | 0.715625 | 0.886292 |
| case_a/443 | active | 0.44112, 0.65657, 0.88613, 0.99995, 0.99995 | 0.815796 | 0.999947 |
| case_a/443 | scan | 0.44112, 0.65657, 0.65657, 0.88613, 0.88613 | 0.715723 | 0.886134 |
| case_b/401 | active | 0.37815, 0.58183, 0.78262, 0.98724, 1.00000 | 0.760189 | 1.000000 |
| case_b/401 | scan | 0.37815, 0.37815, 0.58183, 0.58183, 0.78262 | 0.530548 | 0.782616 |
| case_b/443 | active | 0.37815, 0.58178, 0.78267, 0.98718, 1.00000 | 0.760176 | 1.000000 |
| case_b/443 | scan | 0.37815, 0.37815, 0.58178, 0.58178, 0.78267 | 0.530528 | 0.782668 |

The first curve point is identical between policies in every pair, as the exact
pairing requires. AUC gains 0.100131, 0.100072, 0.229642, 0.229648; final
coverage gains 0.113655, 0.113813, 0.217384, 0.217332.

### Gate C — comparison: ALL PASS

- active AUC wins **4 / 4** (required 4/4);
- mean AUC advantage **0.164873** (required >= 0.10);
- mean final-coverage advantage **0.165546** (required >= 0.10);
- active logical samples <= scan in **4 / 4**;
- all shared-yaw observations exactly paired and reused in **4 / 4**.

### Gate A — metric geometry: ALL PASS, both policies, all four pairs

| pair | active median / p95 | scan median / p95 | purity | idempotent |
| --- | --- | --- | --- | --- |
| case_a/401 | 3.994 / 12.878 mm | 3.837 / 12.283 mm | ID 81 only | true |
| case_a/443 | 3.968 / 12.833 mm | 3.813 / 12.258 mm | ID 81 only | true |
| case_b/401 | 4.325 / 14.144 mm | 4.194 / 13.185 mm | ID 81 only | true |
| case_b/443 | 4.346 / 14.139 mm | 4.201 / 13.245 mm | ID 81 only | true |

All within the 10 mm / 30 mm limits. No coverage drop beyond 0.5 pp anywhere.
The scan's low completeness is not an integrity failure, as the handoff states.

### Gate B — active validity: PASSES on case_a, FAILS on case_b

`case_a`, both seeds: 4 fixations at 0, -5, -10, -15, terminating `no_frontier`;
matched 24,741-26,880 per post-seed patch; overlap medians 1.998-2.088 mm and p95
5.972-6.169 mm; new fractions 0.4185-0.4260 nonterminal and 0.2727/0.2734
terminal; incremental gains 21.51/23.00/11.37 and 21.54/22.96/11.38 pp; final
coverage 99.995%; gain over seed 55.88 pp. **`FSG4_ACTIVE_RUN_PASS`.**

`case_b`, both seeds: 5 fixations at 0, +5, +10, +15, +20 — the mirrored
trajectory — terminating `no_frontier`. Matched 24,942-26,073; overlap medians
1.874-2.013 mm and p95 5.331-6.126 mm; nonterminal new fractions 0.4278-0.4513
and nonterminal gains 20.37/20.08/20.46 pp; final coverage 100.000%; gain over
seed 62.19 pp; plane errors well inside limits. **But the terminal fixation
fails two predeclared terminal rules:**

| quantity | gate | case_b/401 | case_b/443 |
| --- | --- | ---: | ---: |
| terminal new fraction | >= 0.05 | **0.03912** | **0.03970** |
| terminal coverage gain | >= 2 pp | **1.276 pp** | **1.282 pp** |

The cause is legible rather than mysterious. On `case_b` the policy has already
reached 98.72% after four looks, so its fifth look at +20 catches only the last
sliver of the object's right boundary at +21.329 degrees. It still reported
frontier remaining, so it spent a fixation that bought almost nothing. That is a
genuine miss of the FSG3 feasibility contract this increment inherited unchanged,
and it is preserved rather than tuned away.

Note the tension worth recording: the same trajectory that violates the terminal
rule also produces the largest advantage over the scan in the whole experiment
(AUC gain 0.2296, final gain 0.2173, reaching 100% coverage). The efficiency
question and the terminal-patch contract disagree here, and resolving that is a
specification decision, not Code's.

### Visual inspection

`coverage_vs_budget.png`: in all four pairs both curves start at the identical
seed point and the active curve lies above the scan from k=2 onward. The scan's
flat segments are the visible cost of nonadaptive allocation — `case_a` gains
nothing from k=2 to k=3, `case_b` nothing from k=1 to k=2 and from k=3 to k=4.

`growth_truth.png` for `case_b/401` is the clearest single view: active marches
monotonically rightward 0 -> +5 -> +10 -> +15 -> +20 with coverage
37.8 -> 58.2 -> 78.3 -> 98.7 -> 100.0%, while the scan spends its second look at
-5 and its fourth at -10 entirely off the object, its coverage unchanged at
37.8% and 58.2% respectively, ending at 78.3%. The truth-free `growth.png` files
show the same accumulation without any truth overlay.

### Status and scope

`FSG4_INCREMENT4_FAIL`. **Increment 4 is NOT closed and no next experiment is
authorized.** All four pairs, both policies, every map and every manifest are
preserved. No tolerance was introduced, no rerender followed a miss, and no
alternate scan, threshold, seed, geometry, texture, policy, fusion radius or AUC
definition was touched.

What the run does establish, and only this: on this controlled mirrored planar
family with exactly paired observations, the active frontier policy beat the one
frozen nonadaptive scan on every pair by a wide margin. What it does not
establish: the active run is not yet a valid FSG3-contract run on `case_b`, so
the increment's own pass rule is unmet. Stopped for Luiz and Chat.
