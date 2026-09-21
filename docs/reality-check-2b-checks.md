# Reality Check 2b checks

The package adds a pure contract check at `tools/dev/check_reality2b.py`.

Expected positive summary:

```text
[reality2b-policy] PASS exact_parent_continuation=true frozen_fsg6f=true empty_look_is_evidence=true empty_fuses=false scientific_stop=no_frontier watchdog_total=24 quality_gated=false
[reality2b-check] SUMMARY passed=7 failed=0
```

The check verifies that Reality Check 2b keeps the Reality Check 1 scene, seeds, instrument, FSG6f identity, fusion and exact six-look parent; keeps Reality Check 2's watchdog; reuses the existing Reality Check 2 renderer; imports rather than copies FSG6f; keeps evaluator truth out of prediction; and encodes the former `<100 target points` abort as a recorded, no-fusion negative observation.

Ten deliberate negatives must each exit 1:

```text
abortempty    retired abort-on-empty semantics
skipempty     empty binocular evidence discarded from history
dropgaze      empty physical fixation not marked visited
fuseempty     target surfels fused from an empty observation
sixlimit      retired six-look interruption restored
rerenderparent exact Reality Check 1 parent views rerendered
policycopy    FSG6f controller copied/reimplemented
truth         evaluator scene imported prediction-side
qualitygate   post-hoc numerical quality threshold added
watchdoggate  engineering watchdog promoted to scientific PASS/FAIL
```

Prior checks to rerun before acquisition:

```text
.venv/bin/python tools/dev/check_reality1.py
.venv/bin/python tools/dev/check_reality2.py
.venv/bin/python tools/dev/check_fsg6f.py
```

All prior negative sets relevant to these modules should still fail for their own intended reasons.
