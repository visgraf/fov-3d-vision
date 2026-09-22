# MultiObject-2c checks

Run from the repository root:

```bash
.venv/bin/python -m py_compile \
  tools/multiobject2c_public.py \
  tools/multiobject2c_policy.py \
  tools/multiobject2c_run.py \
  tools/multiobject2c_compare.py \
  tools/dev/check_multiobject2c.py

.venv/bin/python tools/dev/check_multiobject2c.py
```

Expected pure-check lines:

```text
[multiobject2c-growth] PASS parent_selected=true preexisting_read_only=true selected_only=true frozen_fsg6f=true seed_scoped_history=true
[multiobject2c-instrument] PASS generic_renderer=true object_scoped_watchdog=true empty_evidence=true texture_diagnostic=true scheduler=false
[multiobject2c-check] SUMMARY passed=6 failed=0
```

Genuine source-mutation controls; each must exit 1 and name a detector:

```bash
for n in handpick crossfuse copypolicy priorhistory legacyrenderer globalwatchdog texturegate; do
  .venv/bin/python tools/dev/check_multiobject2c.py --negative "$n"
done
```

The controls reject: a hard-picked target id, cross-object target admission, copied/changed controller, replay of pre-seed history, return to the legacy globally capped renderer, a global-step watchdog, and use of texture diagnostics as a gate.

## Workstation run

Locate the completed MultiObject-2b parent by manifest, then run into a new output directory, for example:

```bash
.venv/bin/python tools/multiobject2c_run.py \
  --repo . \
  --parent previews/multiobject2b/full-seed2111 \
  --out previews/multiobject2c/full-seed2111 \
  --device OPTIX
```

Use the actual parent path on the workstation; do not assume the example path if the manifest lives elsewhere.

Then:

```bash
.venv/bin/python tools/multiobject2c_compare.py previews/multiobject2c/full-seed2111
```

The run is allowed to end either at the frozen policy's scientific stop or at the 24-fixation engineering watchdog. A watchdog termination must not be reported as scientific success.
