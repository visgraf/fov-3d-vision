# MultiObject-3d checks

Run from the repository root:

```bash
.venv/bin/python tools/dev/check_multiobject3d.py
```

Expected positive lines:

```text
[multiobject3d-audit] PASS read_only=true parent_policy_stop=true observation_separate_from_depth=true stop_replay=true
[multiobject3d-progress] PASS descriptive_only=true scene_progress_unblocked=true next=next_object_selection
[multiobject3d-check] SUMMARY passed=7 failed=0
```

The eight deliberate negatives are genuine source-mutation controls.  Each must be detected and exit 1; exit 2 means the mutation escaped detection:

```bash
for n in acquire handpick crossobject depthonly stopreplay threshold watchdog qualitygate; do
  .venv/bin/python tools/dev/check_multiobject3d.py --negative "$n"
done
```

Expected detectors:

- `acquire` -> `read_only_no_acquisition`
- `handpick` -> `parent_selected_policy_stop_not_handpicked`
- `crossobject` -> `scene_objects_read_only_selected_only_audit`
- `depthonly` -> `observation_separate_from_depth`
- `stopreplay` -> `final_policy_stop_replayed_and_related`
- `threshold` -> `frozen_scale_no_new_threshold`
- `watchdog` -> `watchdog_not_extended_scene_progress_unblocked`
- `qualitygate` -> `watchdog_not_extended_scene_progress_unblocked`

This package is intentionally read-only.  The workstation run must add no acquisition, change no watchdog, modify no parent/source object, and must block if the saved final FSG6f stop cannot be reproduced from the saved data.
