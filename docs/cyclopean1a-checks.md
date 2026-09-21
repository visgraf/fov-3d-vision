# Cyclopean-1a checks

The pure check must print:

```text
[cyclopean1a-topology] PASS sampling_hole=true physical_hole_resolved=true exterior_not_hole=true
[cyclopean1a-policy] PASS cyclopean_domain=true topology=true physical_hole_depth_break=true one_probe_max=true no_mesh=true quality_gated=false
[cyclopean1a-check] SUMMARY passed=6 failed=0
```

The synthetic controls are deliberately topological rather than scene-specific:

- an annulus with an unobserved center is an unresolved sampling hole and produces a probe;
- the same annulus with non-target depth at 2.8 m behind a 2.0 m target boundary is resolved as a physical depth break and produces no probe;
- a notch connected to the exterior raster boundary is not an internal hole.

Every negative must exit 1:

```text
fillhole
physicalclose
exteriorhole
truth
mesh
multiprobe
```

These protect the narrow question: detect spherical topology, do not fill geometry, do not close a true depth-break opening, do not use evaluator truth or a mesh, and do not quietly turn the one-probe experiment into a new controller.
