# FullScene-1c checks

Run from the repository root while on `fullscene-calibration-1`.

```bash
.venv/bin/python -m py_compile \
  tools/fullscene1c_public.py \
  tools/fullscene1c_run.py \
  tools/fullscene1c_compare.py \
  tools/dev/check_fullscene1c.py

.venv/bin/python tools/dev/check_fullscene1c.py
```

Expected pure-check lines:

```text
[fullscene1c-growth] PASS parent_seed=true selected_from_parent=true preexisting_read_only=true selected_only=true frozen_adapter=true
[fullscene1c-control] PASS seed_scoped_history=true generic_renderer=true object_watchdog=true empty_evidence=true handoff=false
[fullscene1c-scene] PASS deferred_prior_action=false scheduler=false truth=false productivity_gate=false
[fullscene1c-check] SUMMARY passed=9 failed=0
```

Genuine source-mutation controls; each must exit 1 and name a detector:

```bash
for n in handpick crossfuse copypolicy priorhistory legacyrenderer globalwatchdog emptyabort execute_deferred handoff productivitygate scheduler truth; do
  .venv/bin/python tools/dev/check_fullscene1c.py --negative "$n"
done
```

The controls reject: a hard-picked target id, cross-object target admission, copying/replacing the frozen adapter, leakage of older scene history into local control, return to the legacy globally capped renderer, a global-step watchdog, treating an empty look as abort semantics, execution of the prior object's deferred action, introduction of an epistemic handoff, synthesis of a productivity gate/score, automatic scene scheduling, and opening evaluator truth.

## Workstation run

Locate the unique completed `FullScene1b-seed-snapshot-selected-object-v1` parent by manifest. Do not assume a path merely from this example.

Then run into a new output directory, for example:

```bash
.venv/bin/python tools/fullscene1c_run.py \
  --repo . \
  --parent previews/fullscene1b/full-seed2111 \
  --out previews/fullscene1c/full-seed2111 \
  --device OPTIX
```

Then:

```bash
.venv/bin/python tools/fullscene1c_compare.py previews/fullscene1c/full-seed2111
```

The run is allowed to terminate either at the frozen policy's scientific stop or at the 24-fixation engineering watchdog. A watchdog termination must not be reported as scientific success.

Do not execute the prior object's deferred action. Do not add a handoff after local stop in this stage. Stop after recording and reporting the FullScene-1c result.
