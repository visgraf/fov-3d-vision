# FSG6 Chat-side checks

Chat prepared FSG6 after re-reading the repository working agreement and the
committed Increment-5 result. This handoff is additive. It does not modify the
closed FSG1 stereo instrument or the FSG3 persistent surfel map.

The scientific change is isolated to a new truth-free 3D surfel-frontier policy
and a fixture family that cannot be covered by horizontal gaze alone.

## Local checks intended before handoff

- all new Python modules compile;
- the analytic diagonal-cylinder geometry accepts its own truth and keeps strip
  chord error below 0.2 mm;
- a plausible four-look diagonal angular trace covers >97% of the fixture, while
  a five-look horizontal-only trace stays below 65%;
- the 3D policy receives the same all-edge object mask with two different map
  states and must select opposite diagonal directions;
- a mask whose physical object boundary is resolved must stop despite the map
  retaining a geometric surface boundary;
- the curved metric rejects a planar chord and detects a 15 mm radial bias.

Seven deliberate negatives are provided: `policy`, `mapstate`, `horizontal`,
`flat`, `shift`, `bias`, and `purity`. Every one must exit 1.

No Blender/Cycles result is claimed by this file. The workstation run is the
scientific experiment.

## Analytic policy plumbing trace (not a render result)

Using the analytic fixture truth only as a synthetic point cloud and rasterizing
an approximate oracle mask, the policy plumbing produced mirror-image traces:

```text
diag_up_right:  (-8,-8) -> (-3,-3) -> (2,2) -> (7,7) -> (12,7)
ideal angular coverage: 0.386 -> 0.571 -> 0.764 -> 0.998 -> 1.000

diag_down_left: (8,8) -> (3,3) -> (-2,-2) -> (-7,-7) -> (-12,-7)
ideal angular coverage: 0.386 -> 0.571 -> 0.764 -> 0.998 -> 1.000
```

This is a design/plumbing sanity check only. It uses analytic truth to synthesize
the map and mask, so it is **not** evidence for the workstation experiment and
is not an expected-trajectory gate. The real loop sees stereo-reconstructed
surfels and rendered oracle masks only.
