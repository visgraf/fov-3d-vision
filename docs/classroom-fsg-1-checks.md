# Classroom-FSG-1 checks

## Package checks

Run:

```bash
.venv/bin/python tools/classroom_fsg1_run.py --self-test
.venv/bin/python tools/dev/check_classroom_fsg1.py
```

Expected:

```text
[classroom-fsg1] self-test PASS
[classroom-fsg1-check] SUMMARY passed=12 failed=0
```

The repository check also requires the established measurement/fusion tools to be unchanged relative to `605fdfc`:

```text
tools/fsg_geometry.py
tools/fsg_blend_bridge.py
tools/fsg_stereo.py
tools/fsg3_surface_map.py
tools/fsg6f_public.py
```

## Source-attention checks

Before execution the runner requires:

- exactly 225 source fixation records;
- `global_step` equals the list order 0..224;
- every record has finite `[yaw,pitch]`;
- source `demo_manifest.json` says `fixation_count == 225`;
- `oracle_attention_for_all_fixations == true`.

No gaze is reselected.

## Per-fixation provenance checks

For every replayed fixation:

- `observation.npz` is produced by `fsg_blend_bridge.py`;
- `fsg_stereo.py` runs before truth evaluation;
- evaluator instance ids remapped from `evaluation_only/truth_L.npz` must match the estimator's rectified instance ids exactly;
- guarded rows must be a boolean subset of native rows;
- guarded xyz is taken from native stereo output;
- Blender xyz is never used for patch geometry;
- the evaluated-depsgraph instance-group table must remain byte-identical across all fixations.

## Fusion checks

- unchanged FSG3 initialize/fuse;
- 12 mm radius/cell read from `fsg6f_public.FUSION`;
- at most 57 deterministic fusion packets per object;
- inherited 100-point minimum retained;
- replaying each packet must be exactly idempotent;
- no cross-instance fusion.

## Post-run structural check

For a full run:

```bash
.venv/bin/python tools/classroom_fsg1_compare.py previews/classroom-fsg1/full-seed2111
```

For an integration smoke-test prefix:

```bash
.venv/bin/python tools/classroom_fsg1_compare.py previews/classroom-fsg1/smoke --allow-partial
```

The comparator rejects foreground/background decomposition, background panorama use, truth filling, matcher tuning, or a guarded point count larger than native.

## Workstation run 2026-09-24

Branch `classroom-fsg-1`, package `53965b0`, ancestor `605fdfc`. Tree clean before and after.

### Preflight

```text
[classroom-fsg1] self-test PASS
[classroom-fsg1-check] SUMMARY passed=12 failed=0
```

Individually: `no-bg-panorama`, `no-bg-shell`, `ordinary-instances`, `guard-no-truth-fill`,
`matcher-frozen`, `packet-capacity`, `gate-positive`, `new-files-present`,
`frozen-tools-diff-empty` all PASS.

`git diff 605fdfc -- fsg_geometry.py fsg_blend_bridge.py fsg_stereo.py fsg3_surface_map.py
fsg6f_public.py` was **empty before the run, during the run and after it**.

### Smoke test (4 fixations, integration only)

```text
CLASSROOM_FSG1_COMPLETE full=False fixations=4 native=7601 guarded=2910
CLASSROOM_FSG1_COMPARE full=False structural_fails=[]
```

All seven required criteria were established independently, not just read from the report:

1. tangent acquisition completes on the real Classroom (`blender_scene_tangent_perspective`);
2. unchanged SGBM runs - `SGBM_3WAY+bounded_photometric_refinement`, block 5, LR 1.0,
   guard 3, ndisp 64, bounds [0.75, 4.5], texture floor 0.5;
3. native patches non-empty (1710-2090 points);
4. guarded is a strict boolean **row** subset of native - verified by `flat_index`, with
   `xyz` and `instance_id` rows **byte-identical**, not recomputed;
5. `truth_alignment_instance_exact: true`;
6. no truth xyz in patch geometry - `truth_xyz_was_not_used_for_patch_geometry: true`, and
   0 of 400 sampled native rows equal any truth row;
7. per-instance fusion is deterministic **and idempotent** - `initialize` and `fuse` give
   identical maps on identical input, and re-fusing the same patch adds **0** surfels while
   reporting `duplicate_patch: True`.

No defect was found, so no Classroom-FSG-1 file was repaired and nothing was committed
before the full run.

Measured caveat: Blender acquisition is **not bit-reproducible**. Two identical smoke runs
gave 1735 vs 1740 native points on the same gaze (< 0.1% drift) - a Cycles/OPTIX sampling
property, not a fusion property. Fusion itself is exactly reproducible.

### Full replay

```text
CLASSROOM_FSG1_COMPLETE full=True fixations=225 native=942402 guarded=666999
                        native_surfels=355830 guarded_surfels=171361
CLASSROOM_FSG1_COMPARE full=True structural_fails=[]
```

4748.55 s (79.1 min), ~21.1 s per gaze. Cost class: overnight/batch, justified by one
Blender re-acquisition per sealed gaze; SGBM is ~0.03 s of that.

Post-run verification: 12 random fixations all carry correct truth-separation,
boolean-subset and exact-alignment flags (12/12), and the observation contract is exactly
`{rgb_L, rgb_R, instance_L, instance_R}` in 12 random fixations. Maximum 17 fusion packets
per object against a 57 ceiling (FSG3 uint64 limit 63) - no limit hit. Two objects below the
inherited 100-point floor reported, not force-fused.
