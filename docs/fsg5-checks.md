# FSG5 Chat-side checks

Chat prepared FSG5 after re-reading the current repository working agreement and
the recorded FSG4c outcome. This handoff is additive; it does not modify closed
FSG1–FSG4 code.

## Local software checks

The seven new Python modules compile under the Chat environment.

Using temporary dependency stubs only to exercise the NumPy/public-contract part
(the stubs are **not** in the ZIP), the new check produced:

```text
[fsg5-scene] PASS right=[-8.487,14.866] left=[-14.866,8.487] chord_max_mm=0.100
[fsg5-check] SUMMARY passed=6 failed=0
```

The two scene meshes were also synthesized from the same 40 strip quads and
passed `validate_mesh`: 82 exported triangles per fixture (80 curved-object + 2
background).

Five deliberate negatives exit 1:

```text
policy -> deliberate hard-coded/wrong curved frontier direction detected
flat   -> deliberate flat substitute for curved surface detected
shift  -> deliberate 5cm map shift detected
bias   -> deliberate 15mm fusion contraction detected
purity -> deliberate background contamination detected
```

The `flat` negative matters scientifically: the analytic curved-surface metric
must reject a chord/planar substitute, otherwise a planarized map could pass a
"curvature" experiment. The `bias` negative independently proves that signed
radial contraction is detectable.

## What was not run here

No Blender/Cycles acquisition was run. No workstation `.venv` or current repo
checkout is present in this environment. Therefore there is no scientific FSG5
result here, no prediction of the actual trajectory, and no claim that the 12 mm
association will pass curvature.

The only numerical design estimates are the analytic angular spans and the
0.100 mm maximum strip-chord approximation error printed above. They are fixture
construction checks, not measured stereo performance.
