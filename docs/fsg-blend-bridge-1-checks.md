# FSG Blend Bridge 1 - checks

## Chat-side prospective checks

The package is additive and the three Python files compile syntactically.

Static contract check:

```text
[fsg-blend-bridge-check] SUMMARY passed=13 failed=0
```

Five deliberate negatives must exit 1:

- `warp` - forbids routing the bridge back through the Phase A-C warp.
- `truthfill` - forbids Blender depth/XYZ in the FSG observation.
- `nonperspective` - requires a local perspective tangent camera.
- `nostereo_contract` - requires `stereo_field` to remain out of the bridge.
- `nogrouping` - requires the explicit deterministic parent-root grouping contract.

These checks do not execute Blender and make no claim about Classroom runtime behavior.

## Workstation checks

Run, in order:

```bash
.venv/bin/python tools/fsg_geometry.py --self-test
.venv/bin/python tools/rig.py --self-test
.venv/bin/python tools/dev/check_fsg_blend_bridge.py
```

Then all negatives:

```bash
for n in warp truthfill nonperspective nostereo_contract nogrouping; do
  .venv/bin/python tools/dev/check_fsg_blend_bridge.py --negative "$n"
done
```

Each negative must exit 1 with a `[fsg-blend-bridge-check] FAIL ...` line.

The real single-fixation acquisition is then run on the Classroom and fed directly to the
UNCHANGED `tools/fsg_stereo.py`. `tools/fsg_blend_bridge_evaluate.py` must print one
`[fsg-blend-bridge-eval] PASS ...` line and write `bridge_evaluation.json`.

## Stop conditions

Stop before changing anything if:

- EYE/head frame extracted from the Classroom disagrees with the existing manifest/demo;
- FSG calibration and repository rig disagree;
- the bridge would require modifying `fsg_stereo.py` or `fsg_geometry.py`;
- `observation.npz` needs depth/XYZ to make stereo run;
- the local perspective cameras cannot be made geometrically consistent with the FSG1
  calibration;
- the single run yields fewer than 100 accepted FSG points after confirming the acquisition
  itself is nonempty.

Diagnose first. Do not tune SGBM, FSG thresholds, core FOV, search depth, profile, SPP or
fusion rules in this handoff.
