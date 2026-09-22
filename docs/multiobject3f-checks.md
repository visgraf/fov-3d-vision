# MultiObject-3f checks

Run from the repository root:

```bash
.venv/bin/python tools/multiobject3f_progress.py
.venv/bin/python tools/dev/check_multiobject3f.py
```

Expected positive lines:

```text
[multiobject3f-progress] PASS threshold_free=true pre_post_reactivation=true no_action=true
[multiobject3f-audit] PASS read_only=true pre_post_replay=true frozen_voxel_identity=true frontier_lineage=true
[multiobject3f-candidates] PASS frozen_gate_ledger=true action_executed=false threshold_added=false
[multiobject3f-check] SUMMARY passed=10 failed=0
```

The ten deliberate negatives are genuine source-mutation controls.  Each must be detected and exit 1; exit 2 means the mutation escaped detection:

```bash
for n in acquire handpick prereplay voxelid counterfactual lineage candidateledger crossobject threshold act; do
  .venv/bin/python tools/dev/check_multiobject3f.py --negative "$n"
done
```

Expected detectors:

- `acquire` -> `read_only_no_acquisition_or_fusion`
- `handpick` -> `parent_reactivated_target_consumed_not_handpicked`
- `prereplay` -> `exact_pre_post_frozen_policy_replay`
- `voxelid` -> `frozen_voxel_identity_no_matching_tolerance`
- `counterfactual` -> `gaze_window_and_map_counterfactual_decomposition`
- `lineage` -> `frontier_lineage_and_map_voxel_decomposition`
- `candidateledger` -> `candidate_gate_ledger_reuses_frozen_rules`
- `crossobject` -> `scene_objects_and_parent_records_read_only`
- `threshold` -> `frozen_voxel_identity_no_matching_tolerance`
- `act` -> `descriptive_no_quality_gate_scheduler_or_action`

The workstation run must add no acquisition or fusion and must block if either the pre-handoff or post-handoff saved FSG6f decision cannot be reproduced exactly.  The two counterfactual policy calls are read-only diagnostics; none of their returned actions may be executed.
