# MultiObject-3e package checks

Run from the repository root after applying the package:

```bash
python -m py_compile \
  tools/multiobject3e_public.py \
  tools/multiobject3e_progress.py \
  tools/multiobject3e_run.py \
  tools/multiobject3e_compare.py \
  tools/dev/check_multiobject3e.py

.venv/bin/python tools/multiobject3e_progress.py
.venv/bin/python tools/dev/check_multiobject3e.py

for n in handpick newselector multiprobe legacyrenderer crossfuse skipempty autoloop qualitygate; do
  .venv/bin/python tools/dev/check_multiobject3e.py --negative "$n"
done
```

Expected positive lines:

```text
[multiobject3e-progress] PASS threshold_free=true one_return_decision=true auto_loop=false
[multiobject3e-handoff] PASS parent_policy_exhausted=true epistemic_selector_reused=true one_fixation=true
[multiobject3e-return] PASS frozen_local_policy=true one_decision=true returned_action_executed=false auto_loop=false
[multiobject3e-check] SUMMARY passed=8 failed=0
```

Every named negative must exit 1 because its real source mutation is detected. Exit 2 means a mutation escaped detection and blocks the run.
