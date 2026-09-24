# FSG Blend Bridge 1 - one Classroom fixation on the native FSG instrument

Status: prospective handoff. No workstation Blender run has been made by Chat.

## Question

Can an arbitrary loaded Blender mesh scene provide one local FSG observation without
changing the frozen FSG stereo instrument?

For the first test the scene is `scenes/classroom/classroom_eye.blend`. The bridge must
turn one declared fixation into the same padded perspective pair and calibration contract
that `tools/fsg_stereo.py` already consumes.

This is deliberately an integration experiment, not another Classroom demo and not a
controller experiment.

## Why this is now first priority

The completed Classroom O3 demo did not exercise the FSG local stereo path. It used the
Phase A-C foveated-warp pair renderer plus `stereo_field`, while FSG1 was designed around
a directly acquired local perspective pair, host-side rectification and SGBM. The two
lineages had never been connected on a `.blend` scene.

The bridge restores the intended division of labor:

    sphere / head -> choose fixation
                    -> local tangent perspective pair
                    -> rectification + SGBM
                    -> head-frame 3D patch
                    -> later: persistent FSG map and controller

The first bridge step stops after ONE patch.

## Frozen machinery

Do not modify for this step:

- `tools/fsg_geometry.py`
- `tools/fsg_stereo.py`
- `tools/fsg3_surface_map.py`
- FSG6 frontier/controller files
- `tools/rig.py`
- the Phase A-D foveated sensor, `stereo_field`, belief or policies
- the Classroom `.blend`

The bridge is additive.

## New files

- `tools/fsg_blend_bridge.py`
  - Blender-side acquisition adapter.
  - Reads the scene's `EYE` pose.
  - Builds the existing FSG1 calibration for the requested yaw/pitch and fixed-head rig.
  - Creates two temporary local `PERSP` cameras.
  - Renders the padded FSG1 RGB pair in the original scene.
  - Uses Blender first-hit ray casting only for oracle instance IDs and evaluator-only truth.
  - Writes `observation.npz` with exactly RGB + instance IDs.

- `tools/fsg_blend_bridge_evaluate.py`
  - Host-side post-stereo evaluator.
  - Reads evaluator-only Blender truth after stereo is complete.
  - Reports accepted count and range/instance diagnostics.
  - Declares no new Classroom stereo-quality threshold in Bridge-1.

- `tools/dev/check_fsg_blend_bridge.py`
  - Static architectural contract check with deliberate negatives.

## Measurement contract

The bridge does NOT re-use the Phase A-C foveated warp for stereo.

At a fixation `(yaw,pitch)` it uses `fsg_geometry.make_calibration(...)`, producing the
same local padded pinhole pair FSG1 was built around. `tools/fsg_stereo.py` then performs
its existing full-raster rectification, SGBM, bounded photometric refinement, validity and
head-frame reconstruction unchanged.

The key invariant is:

    observation.npz = {rgb_L, rgb_R, instance_L, instance_R}

No depth, XYZ, normals, correspondences or Blender range may enter that file.
Evaluator truth lives only below `evaluation_only/`.

## Instance identity

Bridge-1 uses the deterministic parent-root grouping discovered by the Classroom preflight:
renderable mesh objects are assigned to their topmost parent root; sorted root names get
IDs 1..N; zero is no hit.

This is only oracle identity for correspondence guards. It does not infer semantics.

## One-fixation protocol

1. Branch from the completed Classroom result.
2. Run all pure checks and deliberate negatives.
3. Select ONE already-known visible, textured Classroom fixation from the completed
   Classroom reference/guidance. Do not invent a new gaze policy.
4. Run `fsg_blend_bridge.py` at `small` profile on that exact gaze.
5. Run the unchanged `tools/fsg_stereo.py` on the bridge folder.
6. Run `fsg_blend_bridge_evaluate.py`.
7. Inspect `rectified_L.png`, `rectified_R.png`, disparity, validity and points.
8. Stop and report. Do not proceed to multiple fixations, FSG fusion, FSG6, or the full
   Classroom demo in this handoff.

If the existing Classroom preview/guidance is absent, rebuild only enough reference data
to recover the already-defined oracle seed. Do not hand-pick an object name in source.

## Success criterion

Bridge-1 is an INTEGRATION PASS if all of the following hold:

- the bridge Blender process exits nonzero on failure and completes on the real Classroom;
- the output calibration passes the existing FSG geometry/rig assumptions;
- `observation.npz` contains exactly RGB + instance IDs;
- evaluator truth remains outside estimator input;
- the unchanged `tools/fsg_stereo.py` runs successfully on the produced observation;
- at least 100 valid FSG stereo points are produced in the accepted core;
- the evaluator can reproject at least 100 accepted points onto independent first-hit truth;
- visual inspection shows the local tangent pair and disparity are coherent.

Range errors and wrong-ID diagnostics are MEASURED and reported, not thresholded in this
first bridge seam. A wildly bad numerical result is evidence for the next diagnosis, not a
reason to tune the bridge or matcher inside this run.

## Nonclaims

Bridge-1 does not establish:

- full Classroom reconstruction;
- controller compatibility;
- FSG6 generalization;
- autonomous attention;
- foreground/background decomposition;
- better accuracy than `stereo_field`;
- efficiency relative to the foveated warp;
- a production-speed instance-mask implementation.

The direct tangent render is the same deliberate hybrid-sensor approximation already used
by FSG1: it tests the movable high-quality foveal measurement. It does not claim that a
low-resolution peripheral sample can be magnified into new information.

## Results

**BRIDGE1_STOPPED 2026-09-24 on branch `fsg-blend-bridge-1`.** The acquisition half
of the bridge works on the real Classroom. The run stopped at a genuine seam between
two frozen sources, before any FSG stereo output existed. No frozen file was modified.

### What worked

The bridge opened the real `scenes/classroom/classroom_eye.blend`
(sha256 `dca66a3257b909ae...`), took the fixed head frame from the scene's own `EYE`,
built local `PERSP` cameras directly from the frozen `make_calibration`, and rendered
the padded FSG1 tangent pair in the original scene:

| fact | value |
|---|---|
| Blender / device | 5.2.1 LTS / OPTIX |
| profile / spp / seed | `small` / 64 / 2111 (per-eye 21110000, 21110001) |
| raster | 320x320 (core 128 + 2x96 margin), raw FOV 29.445 deg |
| scene / eye source | `_mainScene` / `EYE object` |
| instance groups | **206** |
| L / R hit fraction | **1.0000 / 1.0000** (102,400 px each) |
| render seconds L/R | 0.840 / 0.747 |
| ray-cast seconds L/R | 8.666 / 8.705 |
| **projection_max_error_px** | **6.227e-05** (tolerance 0.002) |

`observation.npz` contains exactly `rgb_L`, `rgb_R`, `instance_L`, `instance_R`; all
evaluator range/XYZ lives under `evaluation_only/`; `foveated_warp_used` and
`stereo_field_used` are both false.

### Where it stopped

The unchanged `tools/fsg_stereo.py` refused the calibration:

```text
[fsg-stereo] FAIL ValueError: expected horizontal rectification with positive L-R disparity
```

`fsg_stereo.rectification` requires `P2[0,3] < 0`. For this gaze it is **+38.3619**.

### The seam, measured

The boundary is razor sharp and lies purely in **yaw**, not in pitch:

| gaze | P2[0,3] | verdict |
|---|---:|---|
| yaw 0, 30, 60, 85, 89, **90.0**, pitch 0 | -38.3619 | accepted |
| yaw **90.1**, 91, 95, 120, 150, 179.9 | +38.3619 | **rejected** |
| yaw -89.9, **-90.0** | -38.3619 | accepted |
| yaw **-90.1**, -120, -179.9 | +38.3619 | **rejected** |
| yaw 0 at pitch -45, -80, -89, -89.9, **-89.99**, +89.9 | -38.3619 | accepted |

Mechanism: `fsg_geometry.camera_rotation_h` builds the camera basis as
`x = unit(cross(z, up))`. Once `|yaw| > 90` the gaze enters the rear hemisphere
(head-frame `z` component turns positive, forward being `-Z`), that derived x-axis
flips against the stereo baseline, and the rectified L-R disparity sign inverts.

**Two frozen sources disagree.** `fsg_geometry.make_calibration` accepts any yaw and
returns a calibration that passes its own `validate_calibration`; `fsg_stereo.py`
then rejects everything outside the forward hemisphere. The FSG lineage never
exercised this because every previous FSG gaze lived inside roughly +/-25 deg on the
procedural tabletop fixture. Resolving it means changing one of those two frozen
files, so Bridge-1 stops here by its own rules.

### The selected seed compounds it

The deterministic rule (largest accepted stereo count among `ORACLE_SEED` records,
ties by ascending object id) selected object **52 `sol`**, the floor, at
**yaw 179.912109375, pitch -89.912109375** with 1,931 accepted points at global
step 129.

That gaze is **essentially straight down**: its direction is
`[2.35e-06, -0.99999882, +0.0015340]`, only **0.1758 deg** from the same pitch at
yaw 0. At the pole the panorama's yaw label is arbitrary, and this one happens to
land 0.176 deg on the far side of the `|yaw| = 90` boundary. So the run met the seam
through a gaze whose nominal yaw carries no real information.

Both facts are reported; the seed was **not** re-chosen after seeing the result.

### Code changes after the handoff (new bridge file only)

1. `orthonormalize()` in `tools/fsg_blend_bridge.py` - mathutils is single precision,
   so the live `EYE` rotation arrived with orthonormality error **1.192e-07** and
   determinant error **-1.192e-07**; `make_calibration` builds `R_hc` purely in the
   head frame while `rig.camera_pose` routes the same pose through `head_R_wh`, so the
   two agree only when that matrix is orthonormal to float64. The residual was
   **3.95e-06** against the existing 1e-9 rig cross-check. A float64 polar
   decomposition (correction **5.96e-08**, bounded at 1e-5 so a genuinely non-rigid
   EYE still fails loudly) brings it to **5.2e-15**. FSG1 never met this because its
   `head_R_wh` is an exact float64 constant.
2. `instance_table()` now ranges over the **evaluated depsgraph** rather than
   `scene.objects`. The Classroom links eleven asset libraries as collection
   instances, so `scene.objects` sees 178 meshes over 98 roots while the depsgraph
   carries **854 mesh instances over 206 roots, 41 of them outside `scene.objects`**.
   `scene.ray_cast` returns those evaluated objects, so a scene-level table cannot
   resolve every hit (it aborted on `Box295.002`, `Cylinder813.003`, `Line122.002`).
   A 5,536-ray sample across the full padded raster now resolves **every** hit with
   zero unresolved roots. The declared rule text is unchanged; only the population it
   ranges over is the evaluated one.

### Checks

- `[fsg-geometry] self-test PASS`, `[rig] self-test ok`.
- `[fsg-blend-bridge-check] SUMMARY passed=13 failed=0`.
- All five negatives exit 1: `warp` -> `FAIL forbidden warp_import`; `truthfill` ->
  `FAIL forbidden truth_in_observation_key`; `nonperspective` -> `FAIL missing
  perspective_camera`; `nostereo_contract` -> `FAIL missing no_field_flag`;
  `nogrouping` -> `FAIL missing parent_root`.
- **359 tracked pre-bridge sources at `d15642f` are byte-identical.**

### Not established

Bridge-1 did not reach FSG stereo, so it establishes nothing about accepted point
counts, range error, wrong-ID rates, disparity quality, or any comparison with
`stereo_field`. It makes no Classroom reconstruction, controller, FSG6 or attention
claim. What it does establish is narrower and architectural: **a real `.blend` can
supply a geometrically exact FSG1 tangent observation** - verified to 6.2e-05 px -
**and the remaining obstacle is a forward-hemisphere assumption shared unevenly
between `fsg_geometry.make_calibration` and `fsg_stereo.rectification`.**
