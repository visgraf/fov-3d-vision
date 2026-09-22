# FullScene-1d checks

Run from the repository root on `fullscene-calibration-1`.

```bash
.venv/bin/python -m py_compile \
  tools/fullscene1d_public.py \
  tools/fullscene1d_run.py \
  tools/fullscene1d_compare.py \
  tools/dev/check_fullscene1d.py

.venv/bin/python tools/dev/check_fullscene1d.py
```

Expected structural lines:

```text
[fullscene1d-audit] PASS parent_1c=true read_only=true zero_open_stop=true inherited_epistemic_audit=true
[fullscene1d-history] PASS seed_plus_growth_only=true observation_separate_from_depth=true no_rerender=true
[fullscene1d-scene] PASS objects_read_only=true deferred_prior_action=false scheduler=false truth=false next=scene_inventory
[fullscene1d-check] SUMMARY passed=9 failed=0
```

Run every genuine mutation negative:

```bash
for n in acquire handpick openfrontier copyaudit oldhistory depthonly crossobject execute_deferred threshold scheduler truth; do
  .venv/bin/python tools/dev/check_fullscene1d.py --negative "$n"
done
```

Each negative must exit `1` with a named detector. Exit `0` means the mutation escaped; exit `2` means the negative harness failed.

Execution is read-only and uses no Blender:

```bash
.venv/bin/python tools/fullscene1d_run.py \
  --parent <unique-completed-fullscene1c-record> \
  --out previews/fullscene1d/full-seed2111

.venv/bin/python tools/fullscene1d_compare.py previews/fullscene1d/full-seed2111
```

The run must preserve the parent and every scene-object source byte-for-byte, replay the zero-OPEN final frozen-policy stop exactly, and add no acquisition, fusion, growth, handoff, scheduler, truth, or quality threshold.
