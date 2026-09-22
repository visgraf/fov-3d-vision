# MultiObject-3c checks

Run from the repository root:

```bash
.venv/bin/python -m py_compile \
  tools/multiobject3c_public.py \
  tools/multiobject3c_run.py \
  tools/multiobject3c_compare.py \
  tools/dev/check_multiobject3c.py

.venv/bin/python tools/dev/check_multiobject3c.py
```

Expected pure-check lines:

```text
[multiobject3c-growth] PASS parent_selected=true preexisting_read_only=true selected_only=true reused_frozen_adapter=true seed_scoped_history=true
[multiobject3c-instrument] PASS generic_renderer=true object_scoped_watchdog=true empty_evidence=true texture_diagnostic=true scheduler=false
[multiobject3c-check] SUMMARY passed=6 failed=0
```

Genuine source-mutation controls; each must exit 1 and name a detector:

```bash
for n in handpick crossfuse copypolicy priorhistory legacyrenderer globalwatchdog texturegate; do
  .venv/bin/python tools/dev/check_multiobject3c.py --negative "$n"
done
```

The controls reject: a hard-picked target id, cross-object target admission, copying/replacing the already-frozen adapter, replay of pre-seed history, return to the legacy globally capped renderer, a global-step watchdog, and use of texture diagnostics as a gate.

## Workstation run

Locate the completed MultiObject-3b parent by manifest, then run into a new output directory, for example:

```bash
.venv/bin/python tools/multiobject3c_run.py \
  --repo . \
  --parent previews/multiobject3b/full-seed2111 \
  --out previews/multiobject3c/full-seed2111 \
  --device OPTIX
```

Use the actual parent path on the workstation; do not assume the example path if the manifest lives elsewhere.

Then:

```bash
.venv/bin/python tools/multiobject3c_compare.py previews/multiobject3c/full-seed2111
```

The run is allowed to end either at the frozen policy's scientific stop or at the 24-fixation engineering watchdog. A watchdog termination must not be reported as scientific success.
