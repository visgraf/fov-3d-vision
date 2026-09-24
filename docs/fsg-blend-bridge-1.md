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

To be filled by Code after the single workstation run. Record:

- exact branch/commit and frozen-source audit;
- selected gaze and how it was obtained from existing guidance;
- Blender/device/profile/SPP;
- bridge render and ray-cast times;
- scene/group counts and left/right hit fractions;
- FSG stereo accepted count/fraction;
- median/P95 absolute and relative range error from `bridge_evaluation.json`;
- wrong-ID count from the same file;
- every FAIL line, if any;
- whether the next step is authorized.
