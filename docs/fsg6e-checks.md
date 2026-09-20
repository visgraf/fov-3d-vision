# FSG6e checks

Prospective local validation of the FSG6e persistent OPEN-frontier package.

Expected positive summaries include:

```text
[fsg6e-scene] PASS ... corridor_preflight=true persistent_state_preflight=true raw_frontier_termination_rejected=true ...
[fsg6e-frontier] PASS map_state_changes_2d_direction=true persistent_state_three_way=true historical_boundary_state=true stereo_hole_not_boundary=true eye_swap_invariant=true projected_frontier_corridor=true resolved_boundary_stops=true
[fsg6e-check] SUMMARY passed=13 failed=0
```

All fourteen deliberate negatives must exit 1:

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
flat
shift
bias
purity
```

The inherited continuation negatives preserve the FSG6a–d lessons. The new controls specifically protect the termination semantics:

- `rawtermination`: raw PCA/tangent frontiers alone remain eligible in a completed ideal swept state;
- `forget_history`: completed binocular evidence is required to resolve a persistent physical boundary;
- `stereo_hole`: target-object segmentation keeps an unmapped look-ahead target OPEN, so absence of stereo reconstruction is not silently treated as background.

FSG6e introduces no new numerical threshold: map resolution reuses the frozen 12 mm fusion association rule; historical physical-boundary resolution reuses the frozen 0.15 object-continuation threshold and a patch scale derived from the frozen 0.04 band fraction.

Local checks and analytic preflights are software/design evidence only. They are not Blender/Cycles scientific results.
