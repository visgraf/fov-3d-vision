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
