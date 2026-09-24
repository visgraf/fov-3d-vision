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

## Results

**BRIDGE1R_COMPLETE 2026-09-24 on branch `fsg-blend-bridge-1`.** The native FSG
tangent-plane + rectification + SGBM pipeline ran on the real Classroom at the
exact fixation that stopped Bridge-1, and produced a non-trivial metric patch.
**No source was modified during this run** — `tools/` is byte-identical to the
Bridge-1R commit `4c24789`, and `tools/fsg_stereo.py` is byte-identical to
`ae8c876`.

### Preflight

`git status --short` clean; branch `fsg-blend-bridge-1`; Bridge-1R commit
`4c24789` present. All three checks green:

```text
[fsg-geometry] self-test PASS
[fsg-tangent-frame] SUMMARY checked=92 failed=0 selected=(179.912109375, -89.912109375)
[fsg-blend-bridge-check] SUMMARY passed=13 failed=0
```

Host-side confirmation of the repair at the identical gaze, before spending a
Blender run:

| tangent frame | P2[0,3] | verdict |
|---|---:|---|
| `legacy_upright` | **+38.36192** | rejected by `fsg_stereo` |
| `baseline_projected` | **−38.36192** | accepted |

Camera +X becomes the projected physical baseline, `(0.99989, ±0.015, ∓2e-05)`.

### Acquisition

Gaze unchanged: **yaw 179.912109375, pitch −89.912109375** (Classroom oracle
seed, object_id 52, `sol`, global_step 129 — provenance only).

```text
[fsg-blend-bridge] COMPLETE scene=classroom_eye.blend profile=small
  gaze=(179.912,-89.912) raster=320x320 groups=206 hitsL=1.0000 hitsR=1.0000
```

Blender 5.2.1 LTS / OPTIX, `small` / 64 spp / seed 2111, scene sha256
`dca66a3257b909ae…`, 206 instance groups, 19.7 s wall,
`tangent_frame_mode: baseline_projected`.

### Rectification

| quantity | value |
|---|---|
| `P2[0,3]` | **−38.36192** |
| `P2[1,3]` | **0.0** — horizontal |
| disparity convention | positive L−R |
| padded raster | 320×320 |
| rectified core | **128×128**, crop `[96, 96, 128, 128]` |
| rectified focal | 608.919 px |
| search window | `min_disparity 0`, `num_disparities 64` |

Depth bounds `[0.75, 4.5] m` map to 8.5–51.1 px; the floor sits at a median
**31.9 px**, comfortably interior — no clipping at either end.

### SGBM

```text
[fsg-stereo] classroom-small-seed2111 valid=13216/16384 fraction=0.8066 ndisp=64 seconds=0.0623
```

Matcher unchanged: `SGBM_3WAY+bounded_photometric_refinement`, block 5,
uniqueness 10, LR tolerance 1.0 px, instance guard 3 px, texture floor 0.5 u8,
3 refinement iterations bounded at 0.75 px.

**13,216 accepted of 16,384 core pixels (80.66%).** Rejections are
**left–right consistency, not texture**: invalid pixels carry
`lr_error_px` median **1.504** against the 1.0 px tolerance, while valid ones
sit at **0.283**; meanwhile `left_gray_std` is essentially identical on both
(invalid **13.22**, valid **13.06**, floor 0.5). The carpet is richly textured
everywhere — it is fine-grained and quasi-repetitive, which is exactly what
breaks LR consistency rather than the texture gate.

### Accuracy against quarantined Blender truth

All 13,216 accepted points reprojected into raw tangent truth; 13,216 compared.

| statistic | absolute | relative |
|---|---:|---:|
| P50 | **22.673 mm** | 1.884% |
| P75 | 30.285 mm | 2.514% |
| P90 | 37.853 mm | 3.139% |
| P95 | **50.605 mm** | 4.208% |
| P99 | 65.821 mm | — |
| max | 336.205 mm | 27.854% |
| mean | 22.672 mm | — |

| within | count | fraction |
|---|---:|---:|
| ≤ 10 mm | 3,096 | 23.43% |
| ≤ 25 mm | 7,172 | 54.27% |
| ≤ 50 mm | 12,501 | **94.59%** |
| ≤ 100 mm | 13,202 | 99.89% |

Signed bias is negligible: median **+2.49 mm**, mean +2.32 mm.
`wrong_instance_count = 0`; every accepted point carries group 159 = `sol`, so
purity is 1.000000 — trivially, because the whole core is one object.

**The result is disparity-quantisation-limited, not broken.** At the measured
range 1 px of disparity is **37.97 mm**, so:

- median error 22.67 mm = **0.60 px**
- P90 37.85 mm = **1.00 px**
- P95 50.61 mm = **1.33 px**

That is ordinary sub-pixel SGBM behaviour.

### Spatial behaviour

Errors do **not** cluster with eccentricity — median absolute error by radius
from the core centre: 22.69 mm (0–16 px), 22.63 (16–32), 22.66 (32–48), 23.45
(48–64), 21.63 (64–91). The central tangent core is as good as the edge.

Only **14 points (0.106%)** exceed 100 mm, sitting slightly farther out (median
radius 64.4 px vs 50.6 overall). There are no occlusion or thin-geometry
artefacts to cluster at: truth across the whole core spans **1.2000–1.2131 m**,
a 13 mm range. This fixation looks straight down at a single flat floor.

A plane fit to the accepted cloud gives residual median 22.10 mm, **rms 27.66
mm**, P95 49.68 mm — i.e. the patch *is* a plane and the residual is the stereo
noise itself, not unmodelled structure.

### Correspondence behaves as ordinary horizontal stereo

Normalised cross-correlation between the rectified pair:

- horizontal scan peaks sharply and unimodally at **32 px, NCC +0.6714**
  (0.514 at 28 px, 0.487 at 36 px) — matching SGBM's 31.9 px median disparity;
- vertical residual **at that disparity** peaks exactly at **dv = 0 px**
  (0.6714), falling symmetrically to 0.592/0.595 at ∓5 px.

Zero vertical disparity at the correct horizontal shift is the direct
confirmation that the baseline-projected tangent frame rectifies correctly.

### Visual inspection

- `rectified_L.png` / `rectified_R.png` (128×128): dark brown fine-grained
  carpet with a lighter region to the right and a soft near-vertical shadow
  boundary. The boundary is visibly displaced horizontally between the views
  and not vertically.
- `disparity.png`: near-uniform mid-grey — correct for a fronto-parallel floor
  at constant range — speckled with black dropouts.
- `validity.png`: predominantly white with scattered black speckle, somewhat
  denser toward the lower-left.
- `points_head.ply`: 13,216 coloured vertices with instance id, extent
  X ±0.26 m, Z ±0.26 m, Y −1.534…−0.919 m — a flat slab below the head, as
  expected for a floor at 1.2 m.

### Provenance

- `observation.npz` contains exactly `rgb_L`, `rgb_R`, `instance_L`,
  `instance_R`, and its sha256 on disk matches the hash the estimator recorded.
- Blender range/XYZ exist only under `evaluation_only/` and were read only
  after stereo.
- Reconstruction is triangulated, not copied: `z_rect_m` reproduces
  `f·B/disparity` to **5.96e-08 m** over every accepted pixel.
- The two rasters are not even the same shape — reconstruction is on the
  128×128 rectified core, Blender truth on the 320×320 raw tangent raster.

### Comparison with the prior `stereo_field` result at this same fixation

Classroom O3 `fixation_history.json`, global_step 129, identical gaze:

| | foveated warp + `stereo_field` | tangent plane + rectified SGBM |
|---|---:|---:|
| raw valid | 3,948 | 13,216 |
| accepted | 1,931 *(after an oracle depth gate)* | **13,216 *(no truth gate at all)*** |
| median abs error, raw | **67.617 mm** | **22.673 mm** |
| P95 abs error, raw | **748.545 mm** | **50.605 mm** |
| median abs error, gated | 27.220 mm | — (no gate applied) |
| P95 abs error, gated | 88.371 mm | — (no gate applied) |

The FSG tangent path is better on both median and P95 **before** any
truth-based rejection, and still better than `stereo_field` *after* the demo
discarded 51% of its points using Blender depth.

**This is not a like-for-like coverage comparison and must not be read as one.**
The FSG core samples a 12° fovea at ~92 points/deg², while `stereo_field`
samples out to 45° eccentricity with cells widening from 0.2° by a factor of
two per level. The point counts measure different things. What *is* comparable
is the error distribution against the same quarantined truth at the same look
direction, and there the tangent-plane instrument is markedly tighter —
especially in the tail.

### What this establishes

`real .blend → tangent pair → FSG rectification → unchanged SGBM → non-trivial
metric 3-D patch` now works end to end on the Classroom. The measurement is
sub-pixel in disparity, spatially uniform, essentially unbiased, and derived
entirely from the estimator.

### What this does NOT establish

One fixation, one gaze, one object, one profile. The core happened to contain a
single flat floor at near-constant range, so this says nothing about occlusion
boundaries, thin geometry, depth discontinuities, low-texture surfaces, or
range beyond ~1.2 m. It is not a Classroom reconstruction, involves no fusion,
no controller, no FSG6f, and no attention claim. The `stereo_field` comparison
is descriptive at one look direction, not a general accuracy ranking. No
accuracy threshold was declared and nothing was tuned.
