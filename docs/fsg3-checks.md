# FSG3 Chat-side checks

These checks were run by Chat before handoff. They are software/analytic checks, **not Blender measurements**.

## Pure Python checks

Using Python 3 with NumPy/OpenCV/Pillow available and the previously frozen FSG1 modules on `PYTHONPATH`:

```text
[fsg3-scene] PASS angular_span=[-10.075,15.190] seed=-7.0 five_looks_reach=true
[fsg3-map] PASS B=552/648 C=504/696 idempotent=true
[fsg3-policy] PASS map_state_changes_direction=true resolved_frontier_stops=true
[fsg3-check] SUMMARY passed=5 failed=0
```

All eight new Python files compile with `py_compile`.

The scene number is analytic from the fixture geometry. It verifies that the seed core includes the left boundary while the object continues beyond the right edge, and that five nominal 5-degree centres can reach beyond the right boundary. It does **not** assert that the real active policy will take exactly five looks.

## Fail-capable negatives

Each deliberate negative exited 1:

```text
[fsg3-check] FAIL AssertionError deliberate hard-coded/wrong frontier direction detected
[fsg3-check] FAIL AssertionError deliberate failure to stop at resolved boundary detected
[fsg3-check] FAIL AssertionError deliberate 5cm registration error detected
[fsg3-check] FAIL AssertionError duplicate patch correctly refused to change map
```

The policy self-test is particularly important: the same two-sided segmentation mask with different persistent-map yaw extents must produce opposite next-saccade directions. This is the software guard that the policy is actually map-dependent rather than a hard-coded rightward scan.

## Analytic surface-growth sanity check

A private truth-grid simulation (not shipped as experimental evidence) sampled the designed plane through the nominal yaw sequence `-7,-2,3,8,13` with 1.5 mm synthetic point noise. Angular visible coverage grew approximately:

```text
37.4% -> 57.1% -> 76.1% -> 95.4% -> 100.0%
```

The final patch is intentionally a small boundary-closing observation: about 11.2% of its synthetic samples were new and the final coverage increment was about 4.6 percentage points. This is why the prospective gates distinguish ordinary growth steps (>=15% new, >=10 pp coverage gain) from the terminal boundary-closing patch (>=5% new, >=2 pp gain). Those thresholds were fixed **before** workstation execution.

This simulation does not run SGBM, Cycles or the active host loop and must not be reported as a measured FSG3 result.

## Limitations of Chat validation

- Blender was not available here.
- The real repository checkout and current `.venv` were not available here.
- No real FSG3 RGB pair was rendered.
- No real policy trajectory, overlap error, coverage curve or final surface accuracy has been measured.
- The experiment has one planar object and a one-dimensional horizontal frontier. It does not yet test 2D surface-frontier choice, curved surfaces, self-occlusion, policy optimality or multi-object switching.
