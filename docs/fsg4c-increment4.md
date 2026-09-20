# FSG4c — Fresh active-versus-scan efficiency validation

## Status before this handoff

FSG1, FSG2 and FSG3 are closed. FSG4a stopped before the full comparison because repeated OptiX renders were not bit-reproducible. FSG4b repaired exact pairing by reusing the active observation artifact at shared yaws and completed all four full pairs. Its primary comparison was strong (active AUC wins 4/4; mean AUC gain 0.164873; mean final-coverage gain 0.165546), but the prospective FSG4b status is **FAIL** because `case_b`'s terminal active patch had only ~3.9% new points and +1.28 pp coverage, below inherited FSG3 terminal thresholds of 5% and +2 pp. Preserve that FAIL.

The diagnosis is conceptual: once coverage before the terminal fixation is 98.72%, at most 1.28 pp remains. A `>=2 pp` terminal-gain requirement is therefore impossible even for a view that closes 100% of the residual surface. In an efficiency experiment, a wasteful fixation should hurt the coverage-vs-budget curve and its AUC; it should not invalidate the trial through a second, per-fixation utility gate.

## D-FSG4c — Fresh validation of the efficiency question

**Decision to record prospectively before acquisition:** FSG4c removes the FSG3 per-fixation novelty/new-fraction and minimum coverage-gain conditions from the FSG4 *validity* contract. Those quantities remain measured and reported. No numerical replacement threshold is introduced. All other scientific elements remain frozen: FSG1 instrument, FSG3/FSG4 frontier policy and parameters, fixed scan `0,-5,+5,-10,+10`, 12 mm fusion, exact shared-view artifact reuse, five-fixation logical camera budget, normalized AUC definition, map accuracy/purity gates, active final coverage >=90%, and aggregate comparison thresholds (4/4 AUC wins, mean AUC gain >=0.10, mean final-coverage gain >=0.10).

FSG4b observations are development/diagnostic data and are not reused. Validate on fresh opaque fixtures `case_c`, `case_d` and fresh Monte-Carlo seeds 503 and 557. The fixtures change placement, extent, depth, tilt and procedural texture while retaining the same controlled single opaque planar-object problem. Run small `case_c`/503 only as smoke. Then run all four full pairs exactly once and aggregate all four regardless of numerical exit-2 misses; stop early only for an integrity/provenance/runtime exception.

**Overturned if:** exact pairing/reuse/provenance fails, the frozen policy or scan changes, or the fresh full comparison misses the prospective FSG4c aggregate/map-quality gates. Never tune fixture, policy, scan, seed, SPP, fusion radius, AUC, or thresholds after seeing results.

## Frozen scientific contract

- Instrument: `FSG1-HDR-SGBM-one-original-update-original-validity-v1`.
- Active policy: existing `tools/fsg4_policy.py`, unchanged in substance and constants.
- Scan: `(0, -5, +5, -10, +10)` degrees.
- Vergence: 2.10 m; horizontal 5-degree lattice; fixed head frame.
- Fusion: existing FSG3 multi-look map, 12 mm association/hash cell.
- Segmentation: oracle object ID, as before.
- Shared yaws: scan reuses the exact already-rendered active acquisition; exact array/seed equality remains a hard integrity gate. Active receives no cache.
- Budget: each policy is charged logical camera samples for every consumed fixation. Reuse only reduces execution provenance (`new_primary_camera_samples`). Active logical samples must not exceed scan logical samples.

## Fresh fixtures

`case_c`: object centre x=-0.38 m, z=-2.18 m, width=1.00 m, height=0.34 m, tilt=9 degrees, fresh procedural texture tag 7.

`case_d`: object centre x=+0.34 m, z=-2.05 m, width=1.02 m, height=0.30 m, tilt=8 degrees, fresh procedural texture tag 11.

The pre-render analytic design check reports approximately 78.7% fixed-scan ideal angular coverage for `case_c` and 74.2% for `case_d`, while five one-direction looks span each fixture. These are design calculations, not Blender results and not acceptance numbers.

## Run validity gates

For **both** active and scan maps:

- final map point-to-plane median <=10 mm;
- final map point-to-plane P95 <=30 mm;
- map contains only object ID 81;
- no material coverage decrease >0.5 pp at any fusion step;
- every post-seed fusion replay is idempotent.

Additionally for **active**:

- 4–5 fixations;
- termination reason `no_frontier`;
- local non-repeating <=5-degree saccades;
- every patch has >=100 oracle object reference pixels and >=90% object measurement coverage;
- every post-seed patch has >=5,000 overlap matches;
- overlap disagreement median <=10 mm and P95 <=25 mm;
- final fixed-grid visible-surface coverage >=90%.

**Descriptive only, never run-failure gates:** per-fixation `new_fraction`, coverage gain, and residual-closure fraction. A poor fixation is penalized through `C(k)` and AUC.

For **scan**: exactly five prescribed yaws and `fixed_budget` termination. There is no scan completeness gate.

## Aggregate FSG4c pass

All four fresh full pairs must be complete and exact-paired. Pass requires:

1. all four active runs valid;
2. all four scan maps valid;
3. exact reused observations/seeds at every shared yaw;
4. active logical camera samples <= scan for all four;
5. active AUC > scan AUC in 4/4 pairs;
6. mean normalized-AUC advantage >=0.10;
7. mean final-coverage advantage >=0.10.

If all pass: record `FSG4C_INCREMENT4_PASS`, close Increment 4, and authorize but do not implement the next experiment. The limited claim is that frontier feedback improves visible-surface acquisition efficiency over this one frozen nonadaptive scan on the controlled fresh planar family. This is not policy optimality or a population estimate.

If any miss: record `FSG4C_INCREMENT4_FAIL`, preserve all four fresh pairs, keep Increment 4 open, and stop for Luiz/Chat.

## Exact command schedule for Code

From repository root after the handoff commit:

```bash
.venv/bin/python tools/dev/check_fsg4c.py --self-test
.venv/bin/python tools/dev/check_fsg4c.py --negative frontier
.venv/bin/python tools/dev/check_fsg4c.py --negative scan
.venv/bin/python tools/dev/check_fsg4c.py --negative pairing
.venv/bin/python tools/dev/check_fsg4c.py --negative auc
.venv/bin/python tools/dev/check_fsg4c.py --negative novelty
```

Each negative must exit 1. Run all existing FSG1/FSG2/FSG3/FSG4 checks unchanged as regressions.

Smoke:

```bash
.venv/bin/python -u tools/fsg4c_pair.py --out previews/fsg4c/smoke-case_c-seed503 --profile small --fixture case_c --seed 503 --mode smoke --device OPTIX
```

A numerical exit 2 is diagnostic and does not block full. An integrity exception/exit 1 does.

Full, exactly once each:

```bash
.venv/bin/python -u tools/fsg4c_pair.py --out previews/fsg4c/full-case_c-seed503 --profile full --fixture case_c --seed 503 --mode full --device OPTIX
.venv/bin/python -u tools/fsg4c_pair.py --out previews/fsg4c/full-case_c-seed557 --profile full --fixture case_c --seed 557 --mode full --device OPTIX
.venv/bin/python -u tools/fsg4c_pair.py --out previews/fsg4c/full-case_d-seed503 --profile full --fixture case_d --seed 503 --mode full --device OPTIX
.venv/bin/python -u tools/fsg4c_pair.py --out previews/fsg4c/full-case_d-seed557 --profile full --fixture case_d --seed 557 --mode full --device OPTIX
```

Then aggregate all four:

```bash
.venv/bin/python -u tools/fsg4c_compare.py \
  previews/fsg4c/full-case_c-seed503 \
  previews/fsg4c/full-case_c-seed557 \
  previews/fsg4c/full-case_d-seed503 \
  previews/fsg4c/full-case_d-seed557 \
  --out previews/fsg4c/full-comparison
```

## Report back

Return a single paste block containing: HEAD before/after, decision/log timing, frozen-source diff; environment; all check summaries and five negative FAIL lines; every command/exit/time/sample count; exact shared-yaw reuse table and proof active received no cache; active and scan trajectories; all five-point coverage curves, AUCs and final coverage; every active per-fixation matched/new/new-fraction/coverage-gain/residual-closure number (descriptive); both final map median/P95 errors and purity; aggregate 4/4 win count, mean AUC gain and mean final gain; every numerical FAIL line; visual observations from `growth_truth.png` and `coverage_vs_budget.png`; code fixes if any; final status exactly `FSG4C_INCREMENT4_PASS` or `FSG4C_INCREMENT4_FAIL`. If PASS, close Increment 4 and authorize but do not implement the next experiment.
