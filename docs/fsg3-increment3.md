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

Pending workstation execution.
