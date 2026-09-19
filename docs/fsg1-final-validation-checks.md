# FSG1g handoff checks run by Chat

Date: 2026-09-19.

## Executed here

- Python syntax compilation of `fsg_final_scene.py`, `fsg_final_render.py`, `fsg_final_eval.py`, and `check_fsg_final_validation.py`: **passed**.
- Static inspection: final evaluator calls `fsg_stereo_supported.compute_once()` and does not call `compute_variants()`; endpoint/footprint vetoes are therefore absent from the prospective candidate.
- Arithmetic for the declared camera-sample schedule was independently checked: 78,643,200 small-smoke samples, 1,258,291,200 per full seed, 2,516,582,400 for both full seeds, 2,595,225,600 including smoke.
- The scene file contains four predeclared target disparity phases and two mirrored finite occluders; no result-dependent parameter is exposed by the render command.

## Not executed here

This environment did not run Blender, the repository `.venv`, or the repository modules together. The workstation must therefore run the supplied self-tests, negative controls, renderer-equivalence guard and actual Cycles acquisitions before any scientific interpretation.

The current public repository and working agreement were read before this handoff. The working agreement assigns Blender/GPU execution and workstation compatibility diagnosis to Code and requires measured results to remain distinct from assumptions.

## Known design limitations

- The suite is controlled planar geometry with opaque diffuse materials and oracle instance segmentation.
- The four phase cases stress disparity phase but are not a substitute for varied natural geometry.
- The two full seeds vary Monte-Carlo noise, not geometry.
- The boundary criterion is an accuracy/safety gate on accepted boundary points, not a completeness requirement.
- Passing FSG1g qualifies the local measurement instrument for Increment 2; it does not validate surface fusion or active exploration.
