# MultiObject-2d checks

Run from the repository root:

```bash
.venv/bin/python tools/dev/check_multiobject2d.py
```

Expected positive lines:

```text
[multiobject2d-audit] PASS read_only=true parent_selected_object=true observation_separate_from_depth=true no_watchdog_extension=true
[multiobject2d-progress] PASS descriptive_only=true scene_progress_unblocked=true next=next_object_selection
[multiobject2d-check] SUMMARY passed=6 failed=0
```

The seven deliberate negatives are genuine source-mutation controls.  Each must be detected and exit 1; exit 2 means the mutation escaped detection:

```bash
for n in acquire handpick crossobject depthonly threshold watchdog qualitygate; do
  .venv/bin/python tools/dev/check_multiobject2d.py --negative "$n"
done
```

Expected detectors:

- `acquire` -> `read_only_no_acquisition`
- `handpick` -> `parent_selected_object_not_handpicked`
- `crossobject` -> `scene_objects_read_only_selected_only_audit`
- `depthonly` -> `observation_separate_from_depth`
- `threshold` -> `frozen_scale_no_new_threshold`
- `watchdog` -> `watchdog_not_extended_scene_progress_unblocked`
- `qualitygate` -> `watchdog_not_extended_scene_progress_unblocked`

This package is intentionally read-only.  The workstation run must add no acquisition, change no watchdog, and modify no parent/source object.
