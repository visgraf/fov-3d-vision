# FSG Blend Bridge-2 checks

Prospective contract:

1. Bridge-1R complete commit `7d53b5a` is an ancestor.
2. `tools/fsg_geometry.py` and `tools/fsg_stereo.py` are unchanged by Bridge-2.
3. Candidate set is fixed before measurement: 30 yaw/pitch pairs.
4. Candidate selection occurs before stereo and the selector refuses candidate directories containing `stereo/`.
5. No post-hoc relaxation of selection heuristics.
6. Final measurement is one selected fixation at profile `small`, 64 spp, seed 2111, vergence 2.10 m and IPD 0.063 m.
7. `tools/fsg_stereo.py` runs unchanged once on the final fixation.
8. Blender truth never enters `observation.npz`, disparity, validity or reconstructed XYZ.
9. No truth-based stereo-quality gate is added.
10. No controller, fusion, FSG6f, foreground/background decomposition or second fixation is introduced.

Static selector check:

```bash
.venv/bin/python tools/fsg_bridge2_select.py --self-test
.venv/bin/python tools/dev/check_fsg_bridge2_select.py
```

Expected:

```text
[fsg-bridge2-select] self-test PASS
[fsg-bridge2-check] SUMMARY passed=8 failed=0
```
