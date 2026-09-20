# FSG6f checks

Prospective local validation of the FSG6f candidate-level frontier-state consensus package.

Expected positive summaries include:

```text
[fsg6f-scene] PASS up_right=[-13.948,13.877]x[-9.115,9.088] down_left=[-13.959,13.145]x[-11.153,10.659] horizontal_ideal_max=0.450 chord_max_mm=0.170 corridor_preflight=true persistent_state_preflight=true candidate_consensus_preflight=true traces={consensus_up_right:6fix/1.0000, consensus_down_left:5fix/0.9991}
[fsg6f-frontier] PASS map_state_changes_2d_direction=true persistent_state_three_way=true historical_boundary_state=true stereo_hole_not_boundary=true eye_swap_invariant=true projected_frontier_corridor=true resolved_boundary_stops=true candidate_state_consensus=true
[fsg6f-check] SUMMARY passed=14 failed=0
```

All fifteen deliberate negatives must exit 1:

```text
policy
mapstate
horizontal
monocular
conjunction
componentmax
full_edge
rawtermination
forget_history
stereo_hole
anyopen
flat
shift
bias
purity
```

`anyopen` protects the new FSG6f semantic boundary: FSG6e's `OPEN >= 8` rule alone is insufficient when MAP_RESOLVED + BOUNDARY_RESOLVED support is the majority.

Development controls from the preserved FSG6e report verify that productive candidates remain strict OPEN majorities, while the two pathological survivors `11 OPEN / 96 raw` and `8 OPEN / 25 raw` are rejected. These controls are not fresh validation data.

Fresh evaluator-only closed-loop preflight exercises consensus on both fixtures and makes it load-bearing for final `no_frontier` on at least one fixture. Analytic preflights and local software checks are design evidence only; they are not Blender/Cycles scientific results.
