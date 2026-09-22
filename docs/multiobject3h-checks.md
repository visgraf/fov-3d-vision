# MultiObject-3h structural checks

The pure checker asserts nine source-level contracts:

1. the active object and action gaze are consumed from the completed MultiObject-3g record, never hand-picked;
2. the saved MultiObject-3g subsequent FSG6f decision is replayed exactly before acting;
3. exactly one new fixation uses the generic scene renderer and no history is rerendered;
4. only valid selected-object points may fuse and all other persistent objects remain read-only;
5. the inherited `<100` empty-look rule and 12 mm fusion rule remain unchanged;
6. frozen FSG6f is called once for exact replay and once after the new observation; the newly returned action is not executed;
7. no watchdog, threshold, quality gate, scheduler or automatic loop is introduced;
8. matched/new counts, novelty fraction and the side-by-side 3g comparison are descriptive only and cannot gate the run;
9. measurement and subsequent-policy labels remain descriptive outcomes.

Expected positive lines:

```text
[multiobject3h-progress] PASS threshold_free=true one_action=true productivity_diagnostic=true auto_loop=false
[multiobject3h-action] PASS parent_action_consumed=true one_fixation=true generic_renderer=true selected_only=true
[multiobject3h-productivity] PASS descriptive=true parent_comparison=true threshold=false
[multiobject3h-return] PASS pre_action_replay=true one_next_decision=true next_action_executed=false auto_loop=false
[multiobject3h-check] SUMMARY passed=9 failed=0
```

Ten genuine source-mutation negatives are provided:

```text
handpick
skipreplay
multiprobe
legacyrenderer
crossfuse
skipempty
executeagain
autoloop
productivitygate
qualitygate
```

Each must exit 1 because a named invariant detected the mutation. Exit 2 means the mutation escaped detection.

The completed workstation record must additionally verify parent/input hashes, exact pre-action replay, object purity, idempotent fusion when non-empty, exactly one acquisition, no historical rerender, one subsequent frozen-policy decision, no execution of that subsequent action, no productivity gate, and closed evaluator truth.
