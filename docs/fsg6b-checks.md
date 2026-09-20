# FSG6b Chat-side checks

No Blender/Cycles scientific run was executed in the Chat environment.

The handoff was checked against the current repository working agreement and built additively so the FSG6a FAIL remains untouched. The accepted one-token `z -> gaze` workstation repair is assumed present in the base repository; FSG6b does not overwrite FSG6a files.

Local checks performed with the shipped FSG6 sources plus the same lightweight dependencies used for the previous Chat-side FSG6 checks:

- all eight new Python files `py_compile` clean;
- `check_fsg6b.py`: **8 passed, 0 failed**;
- existing FSG6 check: **7 passed, 0 failed**;
- all eight FSG6b negatives exited 1 as intended: `policy`, `mapstate`, `horizontal`, `monocular`, `flat`, `shift`, `bias`, `purity`;
- the new `monocular` negative proves the retired left-eye-only continuation decision changes when the eye inputs are swapped;
- `fsg6b_frontier.self_test()` proves the binocular combined edge evidence and selected gaze are invariant to `L <-> R` while the persistent map can still reverse the selected 2D gaze;
- the public-contract check requires FSG6b `SURFACE_FRONTIER` constants and `TARGETS` to equal FSG6a exactly, including `edge_object_fraction_min = 0.15`;
- the fresh fixtures are deliberately not exact mirror copies; analytic construction checks give horizontal-only ideal coverage <=0.471 and render-strip chord error <=0.156 mm;
- `fsg6b_run.py` / `fsg6b_frontier.py` contain no evaluator-scene import or `evaluation_only` access;
- the FSG6b host policy is supplied rectified oracle IDs and raw calibration support for **both** eyes; the 3D map still creates/ranks candidates and the binocular segmentation evidence only vetoes them.

Measured local summary:

```text
[fsg6b-scene] PASS up_right=[-14.559,14.033]x[-9.902,9.659] down_left=[-12.902,12.157]x[-11.340,10.770] horizontal_ideal_max=0.471 chord_max_mm=0.156
[fsg6b-frontier] PASS map_state_changes_2d_direction=true eye_swap_invariant=true resolved_boundary_stops=true
[fsg6b-check] SUMMARY passed=8 failed=0
```

These are software/design checks only, not evidence that FSG6b passes Increment 6. The real result requires the prescribed workstation Blender runs.
