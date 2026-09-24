# FSG Blend Bridge 1R — checks

## Static/package checks

- Only `tools/fsg_geometry.py` is authorized among pre-Bridge sources.
- `tools/fsg_stereo.py` must remain byte-identical to `ae8c876`.
- Bridge must request `tangent_frame="baseline_projected"` explicitly.
- No foveated warp or `stereo_field` may enter the bridge.
- `observation.npz` remains RGB + instance IDs only.
- Evaluator truth remains under `evaluation_only/`.

## Geometry checks

Run:

```bash
.venv/bin/python tools/fsg_geometry.py --self-test
.venv/bin/python tools/dev/check_fsg_tangent_frame.py
```

Expected final line from the second command:

```text
[fsg-tangent-frame] SUMMARY checked=92 failed=0 selected=(179.912109375, -89.912109375)
```

(The exact `checked` count is part of the supplied checker.)

## Required physical degeneracies

The new mode must reject exactly-on-baseline views such as:

```text
(yaw,pitch) = (+90,0)
(yaw,pitch) = (-90,0)
```

with a `ValueError` mentioning the stereo baseline.

This is not a coordinate workaround; binocular transverse disparity is itself singular there.

## Runtime bridge checks

For the exact Bridge-1 fixation, require:

- bridge acquisition completes;
- projection control remains `<= 0.002 px`;
- `tools/fsg_stereo.py` no longer refuses the calibration;
- `P2[1,3]` is approximately zero and `P2[0,3] < 0`;
- `stereo/summary.json` exists;
- at least 100 accepted FSG points exist, preserving the original Bridge-1 integrity criterion;
- evaluator runs and writes `bridge_evaluation.json`.

Range accuracy is still measured rather than threshold-tuned in this repair.
