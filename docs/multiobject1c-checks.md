# MultiObject-1c checks

Run from the repository root:

```bash
.venv/bin/python tools/dev/check_multiobject1c.py
```

Expected positive lines:

```text
[multiobject1c-audit] PASS read_only=true object143_only=true observation_separate_from_depth=true no_watchdog_extension=true
[multiobject1c-progress] PASS descriptive_only=true scene_progress_unblocked=true next=next_object
[multiobject1c-check] SUMMARY passed=6 failed=0
```

The six deliberate negatives are genuine source-mutation controls.  Each must be detected and exit 1; exit 2 means the mutation escaped detection:

```bash
for n in acquire object1active depthonly threshold watchdog qualitygate; do
  .venv/bin/python tools/dev/check_multiobject1c.py --negative "$n"
done
```

Expected detectors:

- `acquire` -> `read_only_no_acquisition`
- `object1active` -> `object143_only_object141_read_only`
- `depthonly` -> `observation_separate_from_depth`
- `threshold` -> `frozen_scale_no_new_threshold`
- `watchdog` -> `watchdog_not_extended_no_policy_loop`
- `qualitygate` -> `scene_progress_not_quality_gated`

This package is intentionally read-only.  The workstation run must add no acquisition and must not alter object 141, object 143, the parent record, FSG6f, or any watchdog.
