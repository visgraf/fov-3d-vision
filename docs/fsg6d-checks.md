# FSG6d checks

Prospective local validation of the FSG6d projected-frontier corridor package.

Expected positive summary:

```text
[fsg6d-scene] PASS ... corridor_preflight=true all_permitted_neighbours_population_checked=true
[fsg6d-frontier] PASS map_state_changes_2d_direction=true eye_swap_invariant=true projected_frontier_corridor=true one_component_cannot_license_other=true resolved_boundary_stops=true
[fsg6d-check] SUMMARY passed=11 failed=0
```

Deliberate negatives, each required to exit 1:

```text
policy
mapstate
horizontal
monocular
conjunction
componentmax
full_edge
flat
shift
bias
purity
```

The check suite deliberately protects both sides of the FSG6 failure bracket: the FSG6b full-edge conjunction is too strict for a valid diagonal corner exit, while the FSG6c full-edge maximum is too permissive when one component is resolved. FSG6d instead measures the exit corridor of the actual supporting projected 3D frontier.

Local checks are software/design checks only. They are not Blender/Cycles scientific evidence.
