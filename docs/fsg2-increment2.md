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

Run 2026-09-19 on the workstation by Code. Every number is read from files under
`previews/fsg2/`.

**`FSG2_INCREMENT2_PASS`** on the single prescribed full seed-211 acquisition.
Every prospective gate is met with an empty `fails` list. **Increment 3
(automatic single-object frontier growth) is AUTHORIZED BUT NOT IMPLEMENTED** -
no frontier selection, policy, ICP, meshing or hole filling was written.

### Integrity

HEAD `bd67270c8f007cb3eabf9d7c990a94ee6c69c5fd` on clean `main`, `4637961` an
ancestor. The FSG1 frozen-instrument diff over the fifteen pinned modules,
`rig.py`, `bl_common.py` and `requirements-fsg.txt` is EMPTY; seven files added
by the handoff and none modified. Python 3.12.3, NumPy 2.2.6, OpenCV 4.13.0,
Pillow 12.3.0; Blender 5.2.1 LTS, OPTIX on an RTX 4090. D-FSG2a and a prospective
`docs/log.md` entry were recorded BEFORE any acquisition.

Instrument wiring verified by reading `tools/fsg2_eval.py` before running: it
imports `compute_once` and `check_kernel_equivalence` from
`fsg_stereo_supported`, never `compute_variants`. Both evaluations report
`instrument: FSG1-HDR-SGBM-one-original-update-original-validity-v1`.

`[fsg2-scene] PASS cases=2 object=61 overlap_prescribed=true`,
`[fsg2-map] PASS matched=658 new=842 idempotent=true`,
`[fsg2-check] SUMMARY passed=4 failed=0`. The three negatives each exit 1:

    [fsg2-check] FAIL AssertionError deliberate 5cm shift detected: overlap collapses
    [fsg2-check] FAIL AssertionError deliberate wrong-instance patch detected
    [fsg2-check] FAIL AssertionError duplicate patch correctly refused to alter map

All eight FSG1 regression suites pass unchanged: 24 / 29 / 34 / 48 / 37 / 46 /
7 / 8, zero failures.

`prediction_manifest.json` reads `truth_opened: false` in both runs, so the
RGB-derived patches and the fused map were written before any geometry metric was
computed.

### Full seed 211 - every gate

| gate | target | measured | result |
| --- | --- | ---: | --- |
| patch coverage `fix_left` | >= 90% | **99.132%** | PASS |
| patch coverage `fix_right` | >= 90% | **100.000%** | PASS |
| B points matched to A | >= 5,000 | **32,222** | PASS |
| B points remaining new | >= 15% | **50.833%** | PASS |
| matched A/B distance median | <= 10 mm | **1.907 mm** | PASS |
| matched A/B distance p95 | <= 25 mm | **6.187 mm** | PASS |
| fused point-to-true-plane median | <= 10 mm | **3.548 mm** | PASS |
| fused point-to-true-plane p95 | <= 30 mm | **9.740 mm** | PASS |
| fixed-grid coverage, fused | >= 70% | **90.225%** | PASS |
| coverage gain over patch A alone | >= 12 pp | **30.485 pp** | PASS |
| replaying patch B idempotent | required | **true** | PASS |

Patch point counts 58,627 (`fix_left`) and 65,536 (`fix_right`). The fused map
holds **91,941 surfels**, of which **16,860 carry two-look support** and 75,081
one look - a histogram that matches `matched_points = 32,222` collapsing into
16,860 fused surfels plus 33,314 new B points extending the surface. Fixed-grid
coverage rises **59.740% -> 90.225%**.

Only object ID 61 entered the map: `instance_id` is uniformly 61 across all
91,941 points and across both patch NPZ files, with background ID 62 absent. No
numerical FAIL line was emitted at full.

### Small smoke, diagnostic

`FSG2_INCREMENT2_FAIL`, exit 2, on exactly two gates - fused-map plane error
median 13.837 mm (limit 10) and p95 34.370 mm (limit 30). Every other gate passed
at small: coverage 97.474% / 100.000%, matched 7,950, new fraction 51.477%,
overlap median 3.812 mm and p95 8.330 mm, fused grid coverage 85.005% with a
30.363 pp gain, idempotent replay true, no background ID in the map. Under the
handoff a numerical miss at small is diagnostic and does not alter the
full-profile gates; integrity, geometry, idempotence and instrument wiring were
all sound, so the full run proceeded. Both plane-error figures cleared
comfortably at full - 13.837 -> 3.548 mm and 34.370 -> 9.740 mm, a factor of
about 3.9 and 3.5 - consistent with the resolution dependence measured throughout
FSG1. Nothing was tuned, rerendered or re-seeded.

### Visual and PLY inspection

`fusion.png` at both profiles shows the result the increment exists to test:
`fix A` covers the left portion of the object, `fix B` the right, and the fused
panel is visibly wider than either with a distinctly darker central band where
both looks contributed. That band is the 16,860 two-look surfels; the lighter
wings on each side are the one-look regions that each fixation alone supplied.

`surface_map.ply` carries `comment fixed head frame H`, 91,941 vertices, no
faces, and a per-vertex `support` property whose values are exactly {1: 75,081,
2: 16,860}, matching the NPZ. Head-frame geometry lands on the frozen fixture:
Z median -2.0497 m against the prescribed object centre -2.05 m, spans
0.621 x 0.444 m against a 0.68 x 0.48 m object, X in [-0.330, +0.291] and Y in
[-0.222, +0.222]. Missing regions remain missing - there is no meshing, no fill,
no interpolation, and no registration was estimated at any point.

### Cost

Measured primary camera samples: smoke 2 x 13,107,200 = 26,214,400; full
2 x 209,715,200 = **419,430,400**. Timings: smoke render 1.717 s Blender wall
(0.218-0.265 s per fixation), smoke evaluation exit 2; full render 3.966 s
(0.930 and 1.008 s), full evaluation 37.539 s wall. Batch class throughout.

### Scope

Two prescribed overlapping foveal RGB-D patches from the frozen FSG1 instrument
accumulate into one persistent surface in the fixed head frame, extending
coverage from 59.7% to 90.2% of the object while holding plane accuracy at
3.5 mm median, with exact calibrated poses and no registration.

It is one finite planar tilted object under oracle segmentation, two fixations
3 degrees apart, one seed, and a 12 mm Euclidean nearest-neighbour association
rule fixed in advance - an engineering baseline, not a claim that this is a final
surface model. Same-object folds and self-occlusions are deferred, surfel normals
are unused, the proximity rule is not a calibrated uncertainty model, and the
completeness grid samples only this known finite object. Nothing here speaks to
active frontier selection, multi-object switching, or scenes outside the
controlled opaque diffuse calibration setting. Increment 3 is authorized on that
basis and was not implemented. Stopped for Luiz and Chat.
