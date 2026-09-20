# FSG6c software/design checks

These are pre-acquisition checks only. They are not Blender/Cycles scientific evidence.

Required positive summary:

```text
[fsg6c-scene] PASS ... runtime_preflight=true retired_conjunction_rejected_critical=true
[fsg6c-frontier] PASS map_state_changes_2d_direction=true eye_swap_invariant=true diagonal_corner_continuation=true resolved_boundary_stops=true
[fsg6c-check] SUMMARY passed=10 failed=0
```

Nine fail-capable negatives must each exit 1:

`policy`, `mapstate`, `horizontal`, `monocular`, `conjunction`, `flat`, `shift`, `bias`, `purity`.

Important integrity properties:

- `SURFACE_FRONTIER` and `TARGETS` must equal FSG6b exactly; the 0.15 threshold is not tuned.
- The FSG6b binocular eye-swap repair remains active.
- The `conjunction` negative proves the retired diagonal `AND` rule fails on a fresh analytic rectified-mask corner continuation that FSG6c permits.
- Fresh fixture preflight uses continuous-cylinder ray intersection, repository calibration/rectification and the exact runtime continuation function.
- Host `fsg6c_run.py` and `fsg6c_frontier.py` must not import `fsg6c_scene.py` or access `evaluation_only`.
- Horizontal-only ideal coverage remains <0.65; curved-surface, radial-bias and purity negatives remain fail-capable.
