# Classroom-FSG-1 — controlled tangent-stereo reconstruction

## Purpose

Return from the matcher micro-study to the actual Classroom scene and test the completed generic FSG bridge as a scene-construction instrument.

The attention variable is controlled by replaying the already sealed Demo-Classroom-1 fixation history. The old demo's foreground/background role assignments are **not** reused. For this experiment every positive instance id is an ordinary scene entity.

The loop is therefore:

```text
sealed gaze
  -> Blender tangent pair
  -> unchanged rectification + SGBM
  -> native valid metric patch
  -> per-instance persistent 12 mm fusion
```

Two scene reconstructions are accumulated in parallel:

1. **native** — unchanged FSG stereo validity only;
2. **guarded** — a pure row-subset of native stereo, with Blender truth allowed only to reject gross range errors after stereo.

The guarded stream is damage control for the concept demonstration. It is not a truth-free confidence model.

## Explicitly out of scope

For this round there is:

- no autonomous gaze/controller experiment;
- no foreground/background decomposition;
- no background panorama;
- no special background object or shell;
- no SGBM tuning;
- no replacement matcher;
- no truth-derived geometry insertion.

## Frozen attention

Source:

```text
previews/demo-classroom1/full-seed2111/fixation_history.json
```

The source must contain exactly 225 ordered fixations and be accompanied by the original `demo_manifest.json`. The new runner consumes only the gaze yaw/pitch and order. Historical target ids/action labels are carried as provenance only.

## Measurement instrument

Each gaze is reacquired with:

```text
tools/fsg_blend_bridge.py
profile small
64 spp
seed 2111
vergence 2.10 m
IPD 0.063 m
baseline_projected tangent frame
```

Then `tools/fsg_stereo.py` runs unchanged. Its native validity mask is the native stream.

## Damage-control guard

After stereo, evaluator-only Blender left-eye range is remapped through the same rectification into the stereo core. A native point survives the guarded stream iff

```text
|range_stereo - range_truth| <= max(0.10 m, 0.05 * range_truth)
```

This is exactly a rejection operation. `xyz_h` in the guarded patch is copied from the corresponding native stereo row. Blender `xyz_h` is never inserted or substituted.

## No foreground/background split

The generic bridge's deterministic evaluated-depsgraph parent-root ids provide instance identity. Every positive id is eligible for ordinary persistent geometry.

This means a fixation historically aimed at the floor may also contribute valid geometry for a chair, pipe, book, wall, or any other instance visible in the tangent core. Nothing is discarded because it was historically called background.

## Fusion

The established `fsg3_surface_map.initialize/fuse` and frozen 12 mm association rule are reused unchanged.

`fsg3_surface_map` stores patch provenance in a `uint64`, limiting one object map to 63 patch ids. Replaying 225 fixations could exceed that if every fixation contributed to the same object, so Classroom-FSG-1 uses a deterministic adapter: four contributing fixations per fusion packet. Thus at most `ceil(225/4)=57` packets can reach any object. This changes only provenance granularity; the fusion algorithm and 12 mm rule remain unchanged.

Packets still obey the inherited 100-point FSG3 minimum. Final leftovers below 100 points are reported, not force-fused.

## Primary outputs

```text
classroom_fsg1_manifest.json
classroom_fsg1_report.json
classroom_fsg1_report.md
replayed_fixations.json
instance_groups.json

native_scene_points.npz
native_scene_points.ply
native_objects.json
objects/native/object_<id>.npz/.ply

guarded_scene_points.npz
guarded_scene_points.ply
guarded_objects.json
objects/guarded/object_<id>.npz/.ply
```

Every fixation also retains its tangent observation, stereo result, native/guarded patches, evaluator-only truth, and `measurement_evaluation.json` beneath `fixations/fix_<step>/`.

## Interpretation

The decisive comparison is not whether guarded is more accurate — it must be, because its rejection gate uses truth. The useful comparison is:

- how much geometry current SGBM can construct natively in the fixed Classroom attention sequence;
- how much gross corruption the oracle gate must remove;
- whether the guarded scene demonstrates that the larger tangent-stereo + persistent-memory architecture is viable when matcher failures are suppressed;
- which objects/ranges remain poorly measured even under the completed bridge.

If the guarded scene is substantially better than native and qualitatively useful, the next engineering/scientific move is to keep the architecture fixed and swap only the stereo matcher.
