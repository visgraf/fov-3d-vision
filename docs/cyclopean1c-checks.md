# Cyclopean-1c checks

The pure check must print:

```text
[cyclopean1c-bay] PASS exterior_deepest=true physical_excluded=true revisit_fallback=true one_probe=true
[cyclopean1c-policy] PASS parent=cyclopean1b seed2111_only=true one_fixation_max=true frozen_fsg6f=true no_mesh=true quality_gated=false
[cyclopean1c-check] SUMMARY passed=6 failed=0
```

The synthetic bay control verifies that:

- the selected component is exterior-connected;
- the selected cell reaches the component's maximum inherited exterior distance;
- revisiting the first selected gaze triggers a deterministic fallback rather
  than a duplicate fixation;
- an exterior shoreline made entirely physical by observed deep non-target
  evidence produces no eligible bay probe.

Every deliberate negative must exit 1:

```text
internal
physical
centroid
multiprobe
truth
policy
```

These protect the narrow experiment: do not substitute an internal-hole rule,
do not probe an already-resolved physical shoreline, do not fall back to a
shoreline centroid when the declared rule is deepest complement distance, do
not turn the step into a multi-probe loop, do not use evaluator truth, and do
not modify/replace FSG6f.
