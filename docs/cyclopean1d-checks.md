# Cyclopean-1d checks

The pure check must print:

```text
[cyclopean1d-epistemic] PASS never_observed=true seen_no_depth=true measured=true mixed=true projection=true
[cyclopean1d-policy] PASS parent=cyclopean1c read_only=true observation_separate_from_depth=true no_acquisition=true no_policy=true quality_gated=false
[cyclopean1d-check] SUMMARY passed=6 failed=0
```

The synthetic control verifies that image observation does **not** require valid
stereo depth: a target-labelled projected pixel with `valid == false` is
`OBSERVED_TARGET_NO_DEPTH`, and changing only `valid` to true yields
`OBSERVED_TARGET_WITH_DEPTH`.

Every deliberate negative must exit 1:

```text
depthonly
acquire
truth
policy
threshold
mutateparent
```

These protect the refinement itself: do not collapse observation into depth,
do not render another fixation, do not open evaluator truth, do not add a gaze
policy, do not invent a texture/quality threshold, and do not mutate the parent.
