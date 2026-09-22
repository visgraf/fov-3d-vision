# FullScene-1a checks

Run from the repository root in the normal project environment.

```bash
python -m py_compile tools/fullscene1a_public.py tools/fullscene1a_run.py tools/fullscene1a_compare.py tools/dev/check_fullscene1a.py
python tools/dev/check_fullscene1a.py
```

Expected pure-check lines:

```text
[fullscene1a-snapshot] PASS parent_3h=true read_only=true history_through_3h=true
[fullscene1a-inventory] PASS live_scene_graph=true object_maps_read_only=true status_descriptive=true
[fullscene1a-selection] PASS valid_depth_only=true frozen_selector=true no_threshold=true
[fullscene1a-check] SUMMARY passed=9 failed=0
```

Run all nine genuine source-mutation negatives; every command must exit 1, never 0 or 2:

```bash
python tools/dev/check_fullscene1a.py --negative acquire
python tools/dev/check_fullscene1a.py --negative hardcode
python tools/dev/check_fullscene1a.py --negative oldhistoryonly
python tools/dev/check_fullscene1a.py --negative visibleonly
python tools/dev/check_fullscene1a.py --negative crossobject
python tools/dev/check_fullscene1a.py --negative execute_deferred
python tools/dev/check_fullscene1a.py --negative scheduler
python tools/dev/check_fullscene1a.py --negative truth
python tools/dev/check_fullscene1a.py --negative threshold
```

After producing a completed record, run:

```bash
python tools/fullscene1a_compare.py <completed-record>
```

The comparator must print `FULLSCENE1A_COMPLETE`, show an empty `structural_fails` list and exit 0.

Also run prior regression suites according to current repository practice. FullScene-1a must not weaken earlier checks or mutation negatives.
