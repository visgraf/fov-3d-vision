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

## Results

Run 2026-09-19 on the workstation by Code. Every number is read from files under
`previews/fsg4c/`.

**Final status: `FSG4C_INCREMENT4_PASS`**, exit 0, empty `fails`. Every fresh
full pair is valid for both policies, exactly paired, and active wins on every
comparison measure. **Increment 4 is CLOSED. The next experiment is AUTHORIZED
BUT NOT IMPLEMENTED** — no design or code for it was written.

The formal **FSG4b FAIL is preserved** and every earlier record is unchanged.
This is a fresh validation on new fixtures and new seeds, not a reinterpretation.

### Integrity, and what was and was not changed

HEAD `ee2698ce29e7a672bac523bcf4960aeea29788c7` on clean `main`, `373d853` an
ancestor. `git diff 373d853` over `fsg4_policy.py`, `fsg4_public.py`,
`fsg4_metrics.py`, `fsg4_scene.py`, `fsg4_eval.py`, `fsg4_compare.py`,
`fsg4_pair.py`, `fsg4_run.py`, the FSG1 stereo modules, `fsg3_surface_map.py`,
`rig.py`, `bl_common.py` and `requirements-fsg.txt` is **EMPTY** — FSG4b and
everything earlier are untouched. Ten files were added and none modified.
Python 3.12.3, NumPy 2.2.6, OpenCV 4.13.0, Pillow 12.3.0; Blender 5.2.1 LTS,
OPTIX on an RTX 4090. D-FSG4c and a prospective `docs/log.md` entry were recorded
BEFORE any acquisition.

Verified by reading the code first, not assumed: `fsg4c_run.py` imports the
**existing unchanged `fsg4_policy`**, calls `compute_once` with
`check_kernel_equivalence` and never `compute_variants`, imports no fixture
geometry and opens no `evaluation_only` asset. `fsg4c_public.SCAN_YAWS_DEG =
(0.0, -5.0, 5.0, -10.0, 10.0)`, `FIXTURES = ("case_c","case_d")`,
`SEEDS = (503,557)`. `fsg4c_pair.py` still compares with `np.array_equal` — the
exact-pairing gate is unchanged and no tolerance exists anywhere.
`fsg4c_eval.py` declares `per_fixation_novelty_and_gain_gated: False`.

All eight new Python files compile. `[fsg4c-check] SUMMARY passed=7 failed=0`.
All five negatives exit 1:

    [fsg4c-check] FAIL AssertionError deliberate hard-coded/wrong frontier direction detected
    [fsg4c-check] FAIL AssertionError deliberate fixture-favouring scan mutation detected
    [fsg4c-check] FAIL AssertionError paired observation differs or was not reused at shared yaw -10.0
    [fsg4c-check] FAIL AssertionError deliberate no-active-advantage curve detected
    [fsg4c-check] FAIL AssertionError deliberate obsolete per-fixation gain gate detected; residual closure would be 100%

All eleven FSG1/FSG2/FSG3/FSG4 regression suites pass unchanged: 24 / 29 / 34 /
48 / 37 / 46 / 4 / 5 / 7 / 7 / 8.

### Pairing and budget, all four fresh pairs

| pair | shared yaws | n | arrays exact | seeds exact | scan reused | active reuse |
| --- | --- | ---: | --- | --- | ---: | ---: |
| case_c/503 | -10, -5, 0 | 3 | true | true | 3 | **0** |
| case_c/557 | -10, -5, 0 | 3 | true | true | 3 | **0** |
| case_d/503 | 0, +5, +10 | 3 | true | true | 3 | **0** |
| case_d/557 | 0, +5, +10 | 3 | true | true | 3 | **0** |

| pair | active logical | scan logical | active <= scan | active newly rendered | scan newly rendered |
| --- | ---: | ---: | --- | ---: | ---: |
| case_c/503 | 838,860,800 | 1,048,576,000 | yes | 838,860,800 | 419,430,400 |
| case_c/557 | 838,860,800 | 1,048,576,000 | yes | 838,860,800 | 419,430,400 |
| case_d/503 | 1,048,576,000 | 1,048,576,000 | yes (equal) | 1,048,576,000 | 419,430,400 |
| case_d/557 | 1,048,576,000 | 1,048,576,000 | yes (equal) | 1,048,576,000 | 419,430,400 |

Active's newly rendered samples equal its logical samples in every pair, which
independently proves it received no paired cache; its manifest reuse count is 0
in all four. `truth_opened` is false for all eight runs. Reuse never reduced any
logical budget: the scan is still charged five fixations everywhere.

### Trajectories, curves, AUC, final coverage

| pair | policy | trajectory (deg) | term | C(1..5) | AUC | final |
| --- | --- | --- | --- | --- | ---: | ---: |
| case_c/503 | active | 0, -5, -10, -15 | no_frontier | 0.390625, 0.601423, 0.823335, 1.0, 1.0 | 0.780018 | 1.000000 |
| case_c/503 | scan | 0, -5, +5, -10, +10 | fixed_budget | 0.390625, 0.601423, 0.601423, 0.823335, 0.823335 | 0.658290 | 0.823335 |
| case_c/557 | active | 0, -5, -10, -15 | no_frontier | 0.390625, 0.601469, 0.823428, 1.0, 1.0 | 0.780053 | 1.000000 |
| case_c/557 | scan | 0, -5, +5, -10, +10 | fixed_budget | 0.390625, 0.601469, 0.601469, 0.823428, 0.823428 | 0.658348 | 0.823428 |
| case_d/503 | active | 0, +5, +10, +15, +20 | no_frontier | 0.363002, 0.546828, 0.733073, 0.917969, 1.0 | 0.719843 | 1.000000 |
| case_d/503 | scan | 0, -5, +5, -10, +10 | fixed_budget | 0.363002, 0.363002, 0.546828, 0.546828, 0.733073 | 0.501174 | 0.733073 |
| case_d/557 | active | 0, +5, +10, +15, +20 | no_frontier | 0.363049, 0.546828, 0.732840, 0.917969, 1.0 | 0.719791 | 1.000000 |
| case_d/557 | scan | 0, -5, +5, -10, +10 | fixed_budget | 0.363049, 0.363049, 0.546828, 0.546828, 0.732840 | 0.501163 | 0.732840 |

The first curve point is identical between policies in every pair, as exact
pairing requires. Active reaches 100.000% final coverage in all four. The policy
discovered opposite directions on the two mirrored placements without being told
which: leftward on `case_c`, rightward on `case_d`.

### Active per-fixation measurements — DESCRIPTIVE, never gated

| pair | step | yaw | matched | new | new fraction | coverage | gain pp | residual closure |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| case_c/503 | 0 | 0 | — | 39,299 | 1.00000 | 0.39062 | 39.062 | n/a |
| case_c/503 | 1 | -5 | 27,555 | 19,922 | 0.41961 | 0.60142 | 21.080 | 34.592% |
| case_c/503 | 2 | -10 | 26,654 | 20,032 | 0.42908 | 0.82334 | 22.191 | 55.676% |
| case_c/503 | 3 | -15 | 25,445 | 15,442 | 0.37768 | 1.00000 | 17.666 | **100.000%** |
| case_c/557 | 1..3 | -5,-10,-15 | 27,549 / 26,652 / 25,464 | 19,928 / 20,034 / 15,422 | 0.41974 / 0.42912 / 0.37720 | — | 21.084 / 22.196 / 17.657 | 34.600% / 55.694% / **100.000%** |
| case_d/503 | 0 | 0 | — | 33,633 | 1.00000 | 0.36300 | 36.300 | n/a |
| case_d/503 | 1 | +5 | 25,025 | 18,451 | 0.42440 | 0.54683 | 18.383 | 28.858% |
| case_d/503 | 2 | +10 | 24,948 | 19,036 | 0.43279 | 0.73307 | 18.624 | 41.098% |
| case_d/503 | 3 | +15 | 24,498 | 20,095 | 0.45063 | 0.91797 | 18.490 | 69.268% |
| case_d/503 | 4 | +20 | 23,717 | 8,877 | 0.27235 | 1.00000 | 8.203 | **100.000%** |
| case_d/557 | 1..4 | +5,+10,+15,+20 | 25,035 / 24,936 / 24,499 / 23,701 | 18,441 / 19,048 / 20,094 / 8,891 | 0.42417 / 0.43307 / 0.45061 / 0.27280 | — | 18.378 / 18.601 / 18.513 / 8.203 | 28.853% / 41.047% / 69.295% / **100.000%** |

The terminal fixation closes **100.000% of the residual surface** in all four
pairs. That is the quantity the FSG4b diagnosis argued should be visible, and it
is now reported rather than converted into a threshold.

**An honest note on the contract correction: it was not load-bearing here.** On
`case_c` the terminal new fraction is 0.377-0.378 with a 17.66 pp gain, and on
`case_d` it is 0.272-0.273 with an 8.20 pp gain. Both would have satisfied the
retired FSG3 terminal rules of >=5% and >=2 pp. So no run in this validation was
rescued by removing those gates; the fresh fixtures simply produced runs that are
valid under either framing. The correction remains right in principle — a >=2 pp
rule is unsatisfiable once 98.72% is already covered — but this PASS does not
depend on it.

### Run validity — all gates, both policies, all four pairs

| pair | policy | plane median | plane p95 | purity | idempotent | min step gain |
| --- | --- | ---: | ---: | --- | --- | ---: |
| case_c/503 | active | 4.378 mm | 14.327 mm | ID 81 only | true | +17.666 pp |
| case_c/503 | scan | 4.341 mm | 13.765 mm | ID 81 only | true | 0.000 pp |
| case_c/557 | active | 4.389 mm | 14.380 mm | ID 81 only | true | +17.657 pp |
| case_c/557 | scan | 4.356 mm | 13.804 mm | ID 81 only | true | 0.000 pp |
| case_d/503 | active | 4.520 mm | 14.762 mm | ID 81 only | true | +8.203 pp |
| case_d/503 | scan | 4.318 mm | 13.590 mm | ID 81 only | true | 0.000 pp |
| case_d/557 | active | 4.514 mm | 14.808 mm | ID 81 only | true | +8.203 pp |
| case_d/557 | scan | 4.308 mm | 13.626 mm | ID 81 only | true | 0.000 pp |

All within the 10 mm / 30 mm limits; no coverage decrease anywhere. Active: 4-5
fixations, `no_frontier` termination, non-repeating 5-degree saccades, minimum
object reference 34,730 px per patch (gate >=100), minimum object measurement
coverage 93.844% (gate >=90%), post-seed matches 23,701-27,555 (gate >=5,000),
overlap medians and p95 within 10 mm / 25 mm everywhere, final coverage 100%
(gate >=90%). Every active and scan run reports an empty `fails` list. The scan
has no completeness gate and is not penalised for its low coverage.

### Aggregate — all seven conditions pass

1. all four active runs valid — yes;
2. all four scan maps valid — yes;
3. exact reused observations and seeds at every shared yaw — yes, 12 of 12 rows;
4. active logical samples <= scan in all four — yes;
5. active AUC > scan AUC in **4 / 4** pairs;
6. mean normalized-AUC advantage **0.170182** (required >= 0.10);
7. mean final-coverage advantage **0.221831** (required >= 0.10).

Per-pair AUC gains 0.121727, 0.121704, 0.218669, 0.218628; final-coverage gains
0.176665, 0.176572, 0.266927, 0.267160. No numerical FAIL line was emitted by any
full pair or by the aggregation.

### Visual inspection

`coverage_vs_budget.png`: in all four pairs both curves start at the identical
seed point and the active curve is above the scan from k=2 onward. The scan's
flat segments are the visible cost of nonadaptive allocation — `case_c` gains
nothing from k=2 to k=3, `case_d` nothing from k=1 to k=2 and from k=3 to k=4.

`growth_truth.png` for `case_d/503` is the clearest single view: active marches
monotonically rightward 0 -> +5 -> +10 -> +15 -> +20 with coverage
36.3 -> 54.7 -> 73.3 -> 91.8 -> 100.0%, while the scan spends its -5 look and its
-10 look entirely off the object, its coverage unchanged at 36.3% and 54.7%,
finishing at 73.3%. The truth-free `growth.png` files show the same accumulation
without any truth overlay.

### Cost and code changes

Smoke 78,643,200 primary camera samples (27.8 s). Full pairs: `case_c` 2m42.0s
and 2m39.9s, `case_d` 3m0.8s and 3m1.0s; aggregation 0.1 s. Logical samples
838,860,800 or 1,048,576,000 per policy per pair as tabulated; the harness newly
rendered 419,430,400 per scan instead of 1,048,576,000, which is execution
provenance only and never reduced a budget.

**No code fix was required or made.** Nothing was tuned: no change to policy,
scan, fixture geometry, texture, seed, SPP, stereo instrument, fusion radius,
budget, AUC, accuracy thresholds, final-coverage threshold, aggregate thresholds
or exact pairing; no rerender after any miss; no FSG4b observation entered this
comparison; no per-fixation utility gate was reintroduced.

### Scope of the closure

**Increment 4 is closed** on this evidence: on this controlled fresh planar
family, with exactly paired observations and equal-or-lower logical camera
budget, the frozen frontier policy acquired visible object surface more
efficiently than the one frozen nonadaptive scan — winning AUC in 4/4 pairs by a
mean 0.170 and reaching 100% final coverage against 73-82%.

The claim is deliberately narrow. Two opaque diffuse planar placements, two
Monte-Carlo seeds, oracle segmentation, exact calibrated poses, horizontal
saccades only, fixed 2.10 m vergence, one policy and **one** comparison scan.
This is **not** policy optimality, not a population-level statistical result, and
says nothing about folds, self-occlusion, multi-object scenes, head motion,
vergence control or calibrated uncertainty. The next experiment is authorized on
that basis and was not implemented. Stopped for Luiz and Chat.
