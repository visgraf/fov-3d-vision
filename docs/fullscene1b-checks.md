# FullScene-1b checks

Run the pure structural checker before any Blender acquisition:

```bash
.venv/bin/python tools/dev/check_fullscene1b.py
```

Expected lines:

```text
[fullscene1b-seed] PASS parent_s0=true selected_from_parent=true one_fixation=true
[fullscene1b-history] PASS full_s0_history=true valid_depth_seed=true no_rerender=true
[fullscene1b-progress] PASS existing_read_only=true deferred_action=false growth=false scheduler=false
[fullscene1b-check] SUMMARY passed=8 failed=0
```

Each negative is a genuine source mutation and must exit **1** because the named invariant detects it:

```bash
for n in handpick oldhistoryonly visibleonly multiprobe legacyrenderer crossfuse execute_deferred grow scheduler truth; do
  .venv/bin/python tools/dev/check_fullscene1b.py --negative "$n"
done
```

A negative exiting 0 means the mutation was not rejected. Exit 2 means the mutation escaped all checks and is a blocker.

After execution, run:

```bash
.venv/bin/python tools/fullscene1b_compare.py previews/fullscene1b/full-seed2111
```

The comparator must exit 0 with `FULLSCENE1B_COMPLETE` and an empty `structural_fails` list.
