# FSG2 Increment 2 — two overlapping foveal RGB-D patches

## Status
Prospective implementation handoff. Increment 1 is closed. This step tests only whether two independently reconstructed local patches can be accumulated into one persistent surface in the fixed head frame. It does **not** implement active frontier selection, ICP, learned fusion, meshing, hole filling, or multi-object switching.

## Frozen inputs
- FSG1 instrument: `FSG1-HDR-SGBM-one-original-update-original-validity-v1`.
- Oracle segmentation: Blender `pass_index`; only object ID 61 enters the surface map.
- Persistent frame: fixed head frame H (+X right, +Y up, -Z forward), never the rotating gaze frame.
- Two prescribed fixations: yaw -3 deg and +3 deg, pitch 0 deg; default 2 m vergence.
- One finite tilted object (ID 61), one background plane (ID 62), identical geometry and texture across both observations.
- No pose estimation: the calibrated head/eye transforms are exact inputs.

## Map model
Patch A initializes one surfel per accepted object point. Patch B associates only against the snapshot of patch A using same object ID and Euclidean distance <= 12 mm. A matched surfel is averaged with its B observations and records support from both patch IDs; unmatched B observations extend the map. Samples within patch B are never collapsed with one another. Replaying the same patch ID must leave the map byte-identical in geometry/support.

This simple association is an engineering baseline, not a claim that Euclidean nearest-neighbour fusion is a final surface model. The single-object oracle prevents cross-object fusion; same-object multi-sheet discontinuities are deferred.

## Prospective gates
All gates are fixed before workstation execution.

Per patch:
- eroded object-reference coverage >= 90%.

Overlap/fusion:
- >= 5,000 B points associated to patch A;
- >= 15% of B points remain new and extend the surface;
- matched A/B distance median <= 10 mm and p95 <= 25 mm;
- fused-map point-to-true-plane distance median <= 10 mm and p95 <= 30 mm;
- fixed object-surface grid coverage after fusion >= 70%;
- fusion increases that fixed-grid coverage by >= 12 percentage points over patch A alone;
- replaying patch B is idempotent.

The truth grid and plane are evaluation-only. RGB-derived patches and the fused map are written before those geometry metrics are computed.

## Execution order
### 1. Software checks — Interactive
```bash
.venv/bin/python tools/fsg2_scene.py
.venv/bin/python tools/fsg2_surface_map.py
.venv/bin/python tools/dev/check_fsg2.py --self-test
```
Expected: all PASS.

Negative controls; every command must exit 1:
```bash
.venv/bin/python tools/dev/check_fsg2.py --negative shift
.venv/bin/python tools/dev/check_fsg2.py --negative instance
.venv/bin/python tools/dev/check_fsg2.py --negative duplicate
```
They demonstrate that a 5 cm registration error, wrong object identity, and duplicate-patch replay are detectable.

Run the existing FSG1 regression suites required by the current repository working agreement before rendering. Do not alter them.

### 2. Small smoke — Interactive
```bash
blender -b --python-exit-code 1 -P tools/fsg2_render.py -- \
  --out previews/fsg2/two-patch-small-seed211 --profile small --seed 211 --device OPTIX --save-blend

.venv/bin/python tools/fsg2_eval.py previews/fsg2/two-patch-small-seed211 \
  --mode smoke --out previews/fsg2/two-patch-small-evaluation
```
Inspect `fusion.png`, `surface_map.ply`, both patch NPZ files, `prediction_manifest.json`, and `metrics.json`.

A numerical miss at small is diagnostic and does not by itself change the full-profile gates. An integrity failure, geometry mismatch, non-idempotence, or wrong instrument wiring stops the step.

### 3. Full reported run — Batch
Only if the smoke/integrity checks are sound:
```bash
blender -b --python-exit-code 1 -P tools/fsg2_render.py -- \
  --out previews/fsg2/two-patch-full-seed211 --profile full --seed 211 --device OPTIX --save-blend

.venv/bin/python tools/fsg2_eval.py previews/fsg2/two-patch-full-seed211 \
  --mode full --out previews/fsg2/two-patch-full-evaluation
```
One full acquisition only. No rerender, seed change, threshold change, association-radius change, or instrument change after seeing a numerical miss.

## Decision D-FSG2a
Record before acquisition:

> **D-FSG2a — Minimal two-patch fusion.** Test whether two prescribed, overlapping foveal RGB-D observations from the frozen FSG1 instrument can extend and fuse one segmented object surface in the fixed head frame without registration or hole filling. Use the prospectively fixed geometry, seed 211, fusion radius 12 mm, and gates in `docs/fsg2-increment2.md`. A full-profile pass authorizes Increment 3 (automatic single-object frontier growth) but does not implement it. A miss is preserved and returned to Luiz/Chat; Code may fix only demonstrated orchestration/implementation bugs, never the checks, fixture, thresholds, seed, instrument, or fusion parameters to obtain a pass.

## What Code may fix
Only a demonstrated implementation/orchestration defect: incompatible repository API, serialization error, wrong frame conversion, wrong candidate wiring, or an error that violates the written algorithm. Diagnose first and describe every change.

Do **not** change geometry, gaze directions, seed, SPP, FSG1 settings, object IDs, association radius, hash size, truth-grid radius, numerical gates, or negative controls to make the experiment pass.

## Required report
Return one paste block containing:
1. HEAD before/after, branch and push; D-FSG2a timing.
2. Python/OpenCV/Blender/GPU versions.
3. All new and existing check summaries; all negative FAIL lines and exit codes.
4. Exact smoke/full commands and paths; measured primary camera samples and timings.
5. Per-patch point count and object-reference coverage.
6. Matched/new counts, B-new fraction, overlap median/p95 distance.
7. Fused map point count, two-look support count, plane median/p95 error.
8. Fixed-grid coverage for A alone and fused map, and the gain.
9. Idempotence result and confirmation that no background ID entered the map.
10. Visual/PLY inspection notes.
11. Every numerical FAIL line and any code fix made.
12. Final status: `FSG2_INCREMENT2_PASS` or `FSG2_INCREMENT2_FAIL`; whether Increment 3 is authorized. Do not implement Increment 3.

If full passes, fill the Results section below, update `README.md`, `DECISIONS.md`, and `docs/log.md`, commit and push. If it fails, preserve the failure, update those records, commit and push, and stop for Luiz/Chat.

## Results
Pending workstation execution.
