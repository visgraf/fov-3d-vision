# MultiObject-3a checks

Pure checker:

```bash
python tools/dev/check_multiobject3a.py
```

Expected lines:

```text
[multiobject3a-selection] PASS read_only=true updated_history=true uninstantiated_only=true valid_depth_support=true
[multiobject3a-progress] PASS handpicked=false seed_deferred=true revisit_scheduler=false quality_gated=false
[multiobject3a-check] SUMMARY passed=6 failed=0
```

Genuine source-mutation negatives; each must exit 1 because a real invariant is detected:

```bash
for n in acquire hardcode oldhistoryonly visibleonly threshold scheduler; do
  python tools/dev/check_multiobject3a.py --negative "$n"; test $? -eq 1 || exit 2
done
```

The selection run itself is read-only: no Blender, no acquisition, no fusion,
no growth and no revisit loop.
