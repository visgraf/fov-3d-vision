# Cyclopean-1b checks

The pure check must print:

```text
[cyclopean1b-boundary] PASS exterior_bay=true internal_distinct=true continuation=true physical_depth_break=true
[cyclopean1b-policy] PASS parent=cyclopean1a read_only=true acquisition=false boundary_arcs=true no_mesh=true quality_gated=false
[cyclopean1b-check] SUMMARY passed=6 failed=0
```

The synthetic controls exercise four distinctions:

- an exterior-connected notch/bay remains `EXTERIOR` and produces an unobserved shoreline;
- an enclosed complement component remains `INTERNAL`;
- target-only shoreline evidence is `TARGET_CONTINUATION`;
- deeper non-target-only evidence is `PHYSICAL_DEPTH_BREAK` using the frozen 12 mm scale.

Every deliberate negative must exit 1:

```text
holeonly
exteriorresolved
depthblind
truth
mesh
acquire
```

These protect the narrow question: audit both lakes and bays; never equate
border-touching with a resolved physical boundary; retain the inherited depth
cue; do not use evaluator truth or a mesh; and do not quietly turn the audit into
another acquisition/controller step.
