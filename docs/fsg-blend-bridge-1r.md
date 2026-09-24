# FSG Blend Bridge 1R — canonical 360-degree stereo tangent frame

Status: prospective repair handoff after `BRIDGE1_STOPPED` at commit `ae8c876`.

## Question

Can the exact Classroom fixation that stopped Bridge-1 be expressed in a canonical local stereo tangent frame, so the unchanged `tools/fsg_stereo.py` proceeds into rectification/SGBM?

The physical fixation is unchanged:

- yaw: `179.912109375 deg`
- pitch: `-89.912109375 deg`
- provenance: completed Classroom oracle seed, object id 52, step 129

Do **not** select a more convenient fixation.

## What Bridge-1 already established

Bridge-1 proved the `.blend -> local perspective observation` half of the seam:

- the real Classroom `.blend` opens correctly;
- the live `EYE` pose defines the head frame;
- the padded FSG perspective pair renders correctly;
- independent Blender projection agrees with FSG pixel geometry;
- `observation.npz` remains exactly RGB + instance IDs;
- evaluator truth remains quarantined.

It stopped before stereo because the legacy tangent-frame convention lets the local camera horizontal axis reverse relative to the physical L→R baseline on the rear hemisphere. At the selected gaze OpenCV returned `P2[0,3] > 0`, while FSG stereo deliberately requires horizontal positive L-R disparity (`P2[0,3] < 0`).

## Repair principle

Do **not** relax `tools/fsg_stereo.py` and do not swap eyes after the fact.

The calibration layer must emit a canonical binocular tangent chart.

For each eye let

- `z` be the eye-to-fixation optical axis in head coordinates;
- `b = (1,0,0)` be the physical left-to-right head baseline.

In the new bridge mode, define local image +X by projecting the baseline into the tangent plane:

```
x_raw = b - dot(b,z) z
x     = normalize(x_raw)
y     = cross(z,x)
```

This is the stronger form of the earlier 180-degree roll idea. A sign flip alone fixes the rear-hemisphere sign seam but does **not** guarantee horizontal rectification at large pitch. The projected-baseline rule does.

The unavoidable singularity is now physically meaningful: looking exactly along `+/- head X` makes the projected baseline vanish. Those two look directions are explicitly rejected instead of assigning an arbitrary image horizontal.

## Backward compatibility

`make_calibration(...)` keeps the historical behavior by default:

```
tangent_frame="legacy_upright"
```

Existing FSG experiments therefore retain their old camera prescription.

The Blender bridge opts in explicitly:

```
tangent_frame="baseline_projected"
```

No previous calibration output should change unless this new mode is requested.

## Authorized edits

This repair authorizes exactly one previously frozen research source edit:

- `tools/fsg_geometry.py` — add the optional baseline-projected tangent-frame mode.

The bridge integration file is also updated:

- `tools/fsg_blend_bridge.py` — request the new mode and instantiate Blender cameras directly from the declared calibration rotation.

Remain frozen:

- `tools/fsg_stereo.py`
- `tools/fsg3_surface_map.py`
- FSG6/controller files
- `tools/rig.py`
- Classroom `.blend`
- Phase A-C warp / `stereo_field`

## Why the bridge camera no longer calls the legacy rig orientation

`rig.camera_pose` implements the repository's historical zero-torsion view convention. Bridge-1R intentionally uses a different roll convention for full-sphere binocular stereo.

Therefore Blender camera world orientation is constructed directly from the calibration:

```
R_wb = R_wh @ R_hc @ CV_TO_BLENDER
```

while the eye world position still comes directly from the fixed-head eye centre. The existing independent Blender projection check remains the runtime guard that the rendered camera actually matches the FSG calibration.

## Pure regression check before Blender

Run:

```
.venv/bin/python tools/fsg_geometry.py --self-test
.venv/bin/python tools/dev/check_fsg_tangent_frame.py
```

The tangent-frame checker must establish:

1. default and explicit `legacy_upright` calibration are identical on historical FSG cases;
2. a coarse full-sphere grid, including the exact stopped fixation, yields horizontal positive-disparity rectification (`P2[1,3] ~= 0`, `P2[0,3] < 0`);
3. the two exact look-along-baseline directions `(yaw,pitch)=(+/-90,0)` fail explicitly.

## One-fixation rerun

Use a new output folder so Bridge-1 evidence remains untouched:

```
previews/fsg-bridge1r/classroom-small
```

Run the same physical fixation:

```
blender -b scenes/classroom/classroom_eye.blend --python-exit-code 1 \
  -P tools/fsg_blend_bridge.py -- \
  --out previews/fsg-bridge1r/classroom-small \
  --profile small \
  --yaw-deg 179.912109375 \
  --pitch-deg -89.912109375 \
  --vergence-m 2.10 \
  --device OPTIX

.venv/bin/python tools/fsg_stereo.py previews/fsg-bridge1r/classroom-small
.venv/bin/python tools/fsg_blend_bridge_evaluate.py previews/fsg-bridge1r/classroom-small
```

Then inspect:

- `rectified_L.png`
- `rectified_R.png`
- `disparity.png`
- `validity.png`
- `points_head.ply`
- `bridge_evaluation.json`

## Stop rule

Stop after this one repaired fixation.

Do not proceed to:

- another gaze;
- fusion;
- FSG6;
- controller work;
- full Classroom reconstruction;
- matcher tuning.

The scientific question is simply whether native FSG tangent-plane stereo finally runs on the exact Classroom look that exposed the 360-degree convention seam.

## Result fields for Code

Report:

- branch / commits / frozen-source audit;
- pure tangent-frame check result;
- exact selected gaze unchanged;
- new projection error;
- rectification `P2[0,3]`, `P2[1,3]`;
- accepted FSG point count / fraction;
- median / P95 absolute range error;
- wrong-instance count / fraction;
- visual inspection of rectified pair, disparity, validity and cloud;
- whether the bridge is now complete enough to proceed to a small multi-fixation FSG Classroom probe.
