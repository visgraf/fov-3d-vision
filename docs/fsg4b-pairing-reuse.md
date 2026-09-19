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
