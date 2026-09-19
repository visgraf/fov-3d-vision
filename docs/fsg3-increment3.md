# FSG3 Increment 3 — automatic single-object frontier growth

## Status
Prospective Chat handoff. FSG1 / Increment 1 and FSG2 / Increment 2 are closed. FSG2 established that two prescribed local RGB-D observations can fuse coherently in the fixed head frame. FSG3 changes only the **choice and stopping of subsequent fixations**: after a prescribed seed, the persistent map plus the current oracle instance mask chooses the next close horizontal saccade.

This increment does **not** compare gaze policies, learn a policy, estimate pose, run ICP, mesh/fill the surface, switch objects, reconstruct folds, move the head, or activate vergence control. Those remain later questions.

## Scientific question

> Starting from one fixation on a segmented object, can a truth-free frontier policy use the evolving persistent RGB-D map to choose nearby fixations and stop at the visible object boundary while growing a coherent 3D surface?

The claim is feasibility, not optimality. A fixed-scan comparison is deliberately deferred until the active loop itself works.

## Frozen sensor and frame

- Local RGB-D instrument: `FSG1-HDR-SGBM-one-original-update-original-validity-v1`.
- Oracle segmentation: Blender `pass_index`; only object ID 71 may enter the persistent map.
- Persistent coordinates: fixed head frame H (+X right, +Y up, -Z forward).
- Exact calibrated eye/head poses; no registration estimation.
- Association radius / hash cell: 12 mm / 12 mm, as in FSG2.
- Default profile SPP only: small 64, full 256.
- Master rendering seed: 307. Each fixation receives a deterministic, distinct left/right Cycles seed from the step index.
- Vergence is fixed at the prescribed 2.10 m in this increment. Only gaze direction is active.

## Fixture

One opaque, diffuse, textured tilted rectangle (ID 71) against a textured background (ID 72). The object is intentionally wider than one foveal core but vertically contained by it.

Truth geometry lives only in `fsg3_scene.py`, which may be imported by Blender acquisition and post-hoc evaluation. `fsg3_loop.py` and `fsg3_policy.py` are checked not to import it.

The fixture's analytically computed horizontal angular span is about -10.075 to +15.190 degrees. The seed fixation is yaw -7 degrees. A 12-degree core therefore contains the object's left boundary while the object continues outside the right edge. The scene self-test checks that geometry before Blender.

## Active policy

This is deliberately a minimal **horizontal frontier policy**.

After each fixation:

1. Reconstruct the local patch with the frozen FSG1 instrument.
2. Fuse accepted object points into the persistent head-frame surfel map.
3. From the current rectified oracle instance mask, measure whether object ID 71 reaches the left and/or right edge band of the current foveal core.
4. From the reconstructed map only, compute robust 1% / 99% head-yaw extents of the accumulated surface.
5. Consider only the two close candidate saccades at current yaw +/- 5 degrees.
6. A candidate must correspond to an edge where the object continues, overlap the current map by at least 4 degrees, lie in the frozen yaw range [-12,+18] degrees, and not revisit a fixation.
7. Score it by the angular support it is predicted to add beyond the current reconstructed map extent.
8. Select the candidate with the largest predicted new support. Stop when no candidate predicts at least 1 degree of new support.

Thus the scene does **not** contain a hard-coded fixation sequence. The next direction is a function of the current segmentation frontier and accumulated map. A software check supplies the same two-sided mask with two different map extents and requires the policy to choose opposite directions.

The expected traversal of this particular fixture is approximately five looks at -7, -2, +3, +8, +13 degrees, but that is a design expectation, **not an execution gate**. The full run reports the actual policy trajectory.

## Multi-look map

FSG3 generalises the FSG2 two-look map without changing its geometric association rule.

- Each new patch associates against a snapshot of the map that existed before that patch.
- Same instance ID and Euclidean distance < 12 mm are the only association cues.
- Several samples from one patch may associate to one old surfel; they are reduced to one patch contribution.
- The old surfel and that patch contribution are averaged using the number of distinct prior patch supports.
- `support_count` is the number of distinct contributing patches, not the number of raw samples.
- `provenance_mask` records the distinct patch IDs.
- Replaying any already fused patch ID must leave geometry, colour, support and provenance byte-identical.

This remains an engineering baseline, not the final surface representation.

## Evidence ordering

The active host loop may use only:

- RGB from the two eyes;
- the oracle instance masks in the acquired pair;
- calibration;
- the persistent reconstructed map;
- fixation history.

It must not import the FSG3 fixture geometry and must not open any `evaluation_only` asset. It writes the complete trajectory, every patch, every map snapshot, final map and `prediction_manifest.json` with `truth_opened=false` **before** post-hoc evaluation is run.

Only `fsg3_eval.py` opens the fixture geometry and exported Blender meshes.

## Prospective full-profile gates

All gates below are fixed before workstation execution.

### Loop / policy

- 4 to 6 fixations total, including the seed;
- termination reason must be `no_frontier`, not exhaustion of the six-fixation budget;
- every saccade is nonzero and no larger than 5 degrees;
- no repeated fixation.

### Per patch

- oracle-object measurement coverage >= 90%.

This is an instrument/support check using the oracle mask, not the fixed truth-grid completeness metric.

### Every non-seed overlap

- >= 5,000 new-patch points associate to the existing map;
- overlap A/B distance median <= 10 mm;
- overlap A/B distance p95 <= 25 mm;
- duplicate replay is exactly idempotent.

Surface extension gate:

- every **nonterminal** added patch: at least 15% of its points remain new;
- the **terminal boundary-closing patch**: at least 5% remain new.

The asymmetric terminal rule is prospective: the final foveal placement is expected to include already reconstructed surface plus only the remaining strip up to the object boundary.

### Persistent surface

Using a fixed evaluation-only grid on the known object surface:

- final surface coverage >= 90%;
- final coverage improves by >= 35 percentage points over the seed patch;
- every nonterminal post-seed fixation increases coverage by >= 10 percentage points;
- the terminal boundary-closing fixation increases it by >= 2 percentage points;
- no step may reduce coverage by more than 0.5 percentage point;
- final point-to-plane median <= 10 mm;
- final point-to-plane p95 <= 30 mm;
- every map point remains instance ID 71.

The coverage thresholds are about this controlled visible planar surface; no completeness claim is made for hidden surfaces.

## Execution order

### 1. Preflight and software checks — Interactive

```bash
.venv/bin/python tools/fsg3_scene.py
.venv/bin/python tools/fsg3_surface_map.py
.venv/bin/python tools/fsg3_policy.py
.venv/bin/python tools/dev/check_fsg3.py --self-test
```

Expected new summary:

```text
[fsg3-check] SUMMARY passed=5 failed=0
```

Run all existing FSG1 and FSG2 regression suites unchanged.

Negative controls — **each must exit 1**:

```bash
.venv/bin/python tools/dev/check_fsg3.py --negative frontier
.venv/bin/python tools/dev/check_fsg3.py --negative resolved
.venv/bin/python tools/dev/check_fsg3.py --negative shift
.venv/bin/python tools/dev/check_fsg3.py --negative duplicate
```

They show respectively that the map state can change the chosen frontier, the policy must stop when the boundary is resolved, a 5 cm registration error is detectable, and duplicate patch replay is rejected as a new observation.

### 2. Small active smoke — Interactive / Batch

```bash
.venv/bin/python -u tools/fsg3_loop.py \
  --repo . --out previews/fsg3/active-small-seed307 \
  --profile small --seed 307 --device OPTIX

.venv/bin/python tools/fsg3_eval.py previews/fsg3/active-small-seed307 \
  --mode smoke --out previews/fsg3/active-small-evaluation
```

Inspect:

- `growth.png` — truth-free angular accumulation generated by the active loop;
- `policy_trace.json` — each frontier decision;
- every `patches/fix_XX_mask.png`;
- final `surface_map.npz`;
- `growth_truth.png` from the evaluator.

A numerical small-profile miss is diagnostic. Stop before full on an integrity failure, wrong instrument, truth leakage, repeated fixation, renderer failure, invalid object ID, non-idempotent map, or a policy/runtime bug that violates the written algorithm.

### 3. Full reported run — Batch

Only after the smoke/integrity path is sound:

```bash
.venv/bin/python -u tools/fsg3_loop.py \
  --repo . --out previews/fsg3/active-full-seed307 \
  --profile full --seed 307 --device OPTIX

.venv/bin/python tools/fsg3_eval.py previews/fsg3/active-full-seed307 \
  --mode full --out previews/fsg3/active-full-evaluation
```

One full active run only. The number of rendered fixations is decided by the frozen policy, not by Code after results are seen. No rerender, new seed, threshold change, scene change, step change, association-radius change, instrument change, or manual gaze edit after a numerical miss.

## Decision D-FSG3a

Record this before acquisition:

> **D-FSG3a — Automatic single-object frontier growth.** Starting from the frozen seed fixation, test whether the evolving persistent RGB-D map plus oracle segmentation can choose nearby horizontal 5-degree saccades, stop when the segmented surface frontier is resolved, and grow one visible object surface under the fixed FSG1 instrument and FSG2 head-frame fusion principle. Use seed 307, the frozen geometry/policy/fusion parameters and the prospective gates in `docs/fsg3-increment3.md`. A full pass closes Increment 3 and authorizes—but does not implement—the next experiment. It does not establish policy optimality because no competing gaze policy is evaluated here.

A miss is preserved and returned to Luiz/Chat. Code may fix only demonstrated implementation/orchestration defects that violate this written algorithm, never the checks, geometry, seed, policy parameters, SPP, instrument, fusion radius or numerical gates to obtain a pass.

## What Code may fix

Only a demonstrated implementation/orchestration defect, for example:

- repository API drift;
- wrong path or serialization;
- frame conversion bug;
- failure to call the frozen one-update instrument;
- policy implementation differing from the algorithm above;
- Blender nonzero-exit propagation / orchestration bug.

Diagnose first. Do not change the scientific specification to obtain a pass.

## Required report

Return one paste block containing:

1. HEAD before/after, branch/push, and D-FSG3a timing.
2. Python/OpenCV/Blender/GPU versions.
3. All new/existing check summaries and every negative FAIL line/exit code.
4. Exact small/full commands, output paths, actual fixation count, primary camera samples and timings.
5. Actual fixation trajectory, every policy decision (edge evidence, map yaw extent, selected candidate, stop reason).
6. Per-patch point count and oracle-object measurement coverage.
7. For every post-seed patch: matched/new counts, new fraction, affected surfels, overlap median/p95.
8. Persistent-map point count and support-count histogram.
9. Fixed-grid surface coverage after every fixation and incremental gains.
10. Final point-to-plane median/p95 and object purity.
11. Idempotence results.
12. Visual inspection of `growth.png`, `growth_truth.png`, patch masks and final map geometry.
13. Every numerical FAIL line and every code fix, if any.
14. Final status `FSG3_INCREMENT3_PASS` or `FSG3_INCREMENT3_FAIL`. If pass, state only that the next increment is authorized; do not implement it.

If the full run passes, fill a Results section here and update `README.md`, `DECISIONS.md` and `docs/log.md`, commit and push. If it fails, preserve the result, update the records, commit and push, and stop for Luiz/Chat.

## Results

Run 2026-09-19 on the workstation by Code. Every number is read from files under
`previews/fsg3/`.

**`FSG3_INCREMENT3_PASS`** on the single prescribed full seed-307 active run.
Every prospective gate is met with an empty `fails` list, and the final surface
reaches **100.0%** of the fixed evaluation grid. **Increment 3 is closed. The next
experiment is AUTHORIZED BUT NOT IMPLEMENTED** - no competing policy, learned
policy, pose estimation, ICP, meshing, hole filling, object switching, fold
reconstruction, head motion or vergence control was written.

This is feasibility, not optimality: no competing gaze policy was evaluated here.

### Integrity and evidence ordering

HEAD `8e4bcb247bdd69d1edeb1a8f396361256ac7d4bc` on clean `main`, `7b8d39b` an
ancestor. The FSG1/FSG2 frozen diff over the nineteen pinned modules, `rig.py`,
`bl_common.py` and `requirements-fsg.txt` is EMPTY; ten files added by the
handoff and none modified. Python 3.12.3, NumPy 2.2.6, OpenCV 4.13.0, Pillow
12.3.0; Blender 5.2.1 LTS, OPTIX on an RTX 4090. D-FSG3a and a prospective
`docs/log.md` entry were recorded BEFORE any acquisition.

Two structural invariants were verified by reading the code before running, not
inferred: `fsg3_loop.py` and `fsg3_policy.py` import no fixture geometry and
touch no `evaluation_only` asset - only `fsg3_eval.py` does - and the loop calls
`compute_once` with `check_kernel_equivalence`, never `compute_variants`. Every
patch and both runs report instrument
`FSG1-HDR-SGBM-one-original-update-original-validity-v1`.
`prediction_manifest.json` records `truth_opened: false` with
`policy_inputs = [persistent map xyz_h, current rectified oracle instance mask,
raw calibration support, calibration, fixation history]`, and the complete
trajectory, all five patches, all five map snapshots and the final map were
written before the evaluator opened any geometry.

`[fsg3-scene] PASS angular_span=[-10.075,15.190] seed=-7.0 five_looks_reach=true`,
`[fsg3-map] PASS B=552/648 C=504/696 idempotent=true`,
`[fsg3-policy] PASS map_state_changes_direction=true resolved_frontier_stops=true`,
`[fsg3-check] SUMMARY passed=5 failed=0`. All four negatives exit 1:

    [fsg3-check] FAIL AssertionError deliberate hard-coded/wrong frontier direction detected
    [fsg3-check] FAIL AssertionError deliberate failure to stop at resolved boundary detected
    [fsg3-check] FAIL AssertionError deliberate 5cm registration error detected
    [fsg3-check] FAIL AssertionError duplicate patch correctly refused to change map

All nine FSG1/FSG2 regression suites pass unchanged: 24 / 29 / 34 / 48 / 37 /
46 / 7 / 8 / 4.

### The trajectory the policy chose

The policy produced **5 fixations at yaw -7, -2, +3, +8, +13 degrees**, every
saccade exactly +5 degrees and nonzero, no repeat, terminating on
**`no_frontier`** rather than budget exhaustion. I selected nothing; the document's
"approximately five looks" was a design expectation and not an execution gate.

`policy_trace.json`, step by step - map yaw extent is measured from the
reconstructed map alone, edge evidence from the current oracle mask:

| step | yaw | map yaw extent (deg) | edge touch L / R | candidates | decision |
| ---: | ---: | --- | --- | --- | --- |
| 0 | -7 | [-9.709, -2.400] | false / true (0.719) | +5 -> -2, overlap 5.600, new 6.400 | continue |
| 1 | -2 | [-9.619, +2.873] | true / true | +5 -> +3, overlap 5.873, new 6.127 | continue |
| 2 | +3 | [-9.534, +8.160] | true / true | +5 -> +8, overlap 6.160, new 5.840 | continue |
| 3 | +8 | [-9.525, +13.272] | true / true | +5 -> +13, overlap 6.272, new 5.728 | continue |
| 4 | +13 | [-9.523, **+14.632**] | true / **false (0.000)** | none | **stop: no_frontier** |

The reasoning is genuinely frontier-driven at both ends. At the seed the object
does not reach the left edge (`left_fraction 0.0`), so only one candidate exists
and the policy moves right. At every middle step both edges touch, but the
leftward candidate is excluded as a revisit. At the terminal fixation the object
no longer reaches the right edge at all, so no candidate remains and the loop
stops. The map's right extent finished at **+14.632 degrees** against the
fixture's analytic right boundary of **+15.190** - it stopped at the visible
object boundary, from segmentation and map evidence only.

### Per-patch measurement (gate >= 90% oracle-object coverage)

| step | patch | yaw | points | object measurement coverage |
| ---: | --- | ---: | ---: | ---: |
| 0 | fix_00 | -7 | 28,405 | 94.050% |
| 1 | fix_01 | -2 | 45,134 | 96.564% |
| 2 | fix_02 | +3 | 45,962 | 96.603% |
| 3 | fix_03 | +8 | 46,580 | 96.723% |
| 4 | fix_04 | +13 | 31,819 | 94.756% |

### Overlap and surface extension (every post-seed patch)

| patch | matched | new | new fraction | affected surfels | overlap median | overlap p95 | idempotent |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| fix_01 | 25,720 | 19,414 | 43.014% | 14,924 | 1.992 mm | 6.336 mm | true |
| fix_02 | 26,514 | 19,448 | 42.313% | 13,616 | 1.966 mm | 6.104 mm | true |
| fix_03 | 26,608 | 19,972 | 42.877% | 15,304 | 1.823 mm | 5.455 mm | true |
| fix_04 | 26,426 | 5,393 | **16.949%** | 14,658 | 1.924 mm | 5.695 mm | true |

All matched counts clear the 5,000 minimum by more than fivefold; all medians are
under 2 mm against a 10 mm gate and all p95 under 6.4 mm against 25 mm. The three
nonterminal patches each keep >= 15% new (43.0 / 42.3 / 42.9%), and the terminal
boundary-closing patch keeps 16.9% against its prospectively relaxed 5% rule -
comfortably above it, so the asymmetric allowance was not actually needed here.
Duplicate replay is exactly idempotent at every step.

### Persistent surface

Final map **92,632 surfels**, support histogram **{1: 39,551, 2: 47,660,
3: 5,421}** with 15 distinct provenance masks. Snapshots grow 28,405 -> 47,819 ->
67,267 -> 87,239 -> 92,632. Coverage on the fixed evaluation-only grid:

| after fixation | yaw | coverage | gain |
| ---: | ---: | ---: | ---: |
| 0 | -7 | 33.613% | (seed) |
| 1 | -2 | 54.601% | +20.987 pp |
| 2 | +3 | 74.785% | +20.184 pp |
| 3 | +8 | 94.758% | +19.974 pp |
| 4 | +13 | **100.000%** | +5.242 pp |

Final coverage 100.000% (gate >= 90%), improvement over the seed 66.387 pp
(gate >= 35), each nonterminal post-seed fixation ~20 pp (gate >= 10), the
terminal one 5.242 pp (gate >= 2), and no step lost any coverage at all (gate:
no loss beyond 0.5 pp). Final point-to-plane **median 4.219 mm** (gate <= 10) and
**p95 13.587 mm** (gate <= 30).

Object purity holds everywhere: all 92,632 map points carry instance ID 71, every
map snapshot is pure 71, every patch NPZ is pure 71, and background ID 72 never
enters the map.

### Small active smoke, diagnostic

Same trajectory (-7, -2, +3, +8, +13, `no_frontier`), exit 2, missing four gates:
`fix_00` and `fix_04` object measurement coverage at 89.513% and 89.547% against
90%, and final plane error median 11.884 mm and p95 31.972 mm against 10 and 30.
Every loop, overlap, extension, idempotence and coverage gate passed at small,
with final grid coverage 95.741% and a 65.961 pp gain. Under the handoff a
small-profile numerical miss is diagnostic; none of the stop conditions applied -
instrument correct, no truth leakage, no repeated fixation, no renderer failure,
no invalid object ID, map idempotent, policy within its written algorithm - so
the full run proceeded. All four cleared at full: 89.513% -> 94.050%, 89.547% ->
94.756%, 11.884 -> 4.219 mm, 31.972 -> 13.587 mm. Nothing was tuned, rerendered
or re-seeded, and no code fix was required.

### Visual inspection

`growth.png` (truth-free, written by the loop) shows the accumulated map after
each fixation: a narrow strip at yaw -7 widening rightward through -2, +3, +8 and
+13. `growth_truth.png` (evaluator) shows the same growth against the fixed truth
grid with coverage 33.6% -> 54.6% -> 74.8% -> 94.8% -> 100.0%, the final panel
fully covered. The five `patches/fix_XX_mask.png` confirm the policy's edge
evidence directly: at `fix_00` the object's left boundary sits inside the core
while the object runs off the right edge; `fix_01`-`fix_03` fill the full width;
at `fix_04` a strip of background appears at the right edge, which is the
boundary that ends the loop. Final map geometry is consistent with the fixture:
Z median -2.0992 m, X spanning [-0.385, +0.546] m and Y [-0.157, +0.156] m.
Missing geometry stays missing - no meshing, filling, interpolation or
registration anywhere in the pipeline.

### Cost

Measured primary camera samples: smoke 65,536,000 (5 fixations x 2 eyes x 320^2 x
64); full **1,048,576,000** (5 x 2 x 640^2 x 256). Timings: small loop 8.234 s
wall with 2.623 s recorded inside Blender, smoke evaluation exit 2; full loop
59.411 s wall, full evaluation 42.817 s wall. Batch class throughout.

### Scope

A truth-free frontier policy, given one seed fixation on a segmented object,
chose four further 5-degree saccades from the evolving persistent map and its
current segmentation frontier, stopped by itself at the visible object boundary,
and grew a coherent head-frame surface from 33.6% to 100% of the visible object
at 4.2 mm median plane accuracy - with the FSG1 instrument frozen and no
registration estimated.

It is one opaque diffuse textured planar tilted rectangle under oracle
segmentation, horizontal saccades only, fixed 2.10 m vergence, one seed, one
policy, and a 12 mm Euclidean association rule fixed in advance. **No competing
gaze policy was evaluated, so nothing here speaks to optimality** - a fixed-scan
comparison was deliberately deferred until the active loop worked, which it now
does. Folds, self-occlusion, multi-object switching, head motion, vergence
control, calibrated uncertainty and hidden-surface completeness all remain open.
The next experiment is authorized on that basis and was not implemented. Stopped
for Luiz and Chat.
