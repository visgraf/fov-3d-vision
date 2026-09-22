# MultiObject-3g structural checks

The prospective package is intentionally small. The pure checker asserts nine source-level contracts:

1. the active object and action gaze are consumed from the MultiObject-3f/3e parent chain, not hand-picked;
2. the MultiObject-3f attention-only/geometry-only causal result is required before execution;
3. the MultiObject-3e returned decision is replayed exactly before acting;
4. exactly one new fixation uses the generic scene renderer and no history is rerendered;
5. only valid selected-object points may fuse and pre-existing objects remain read-only;
6. the inherited `<100` empty-look rule and 12 mm fusion rule remain unchanged;
7. frozen FSG6f is called once to replay the parent action and once after the new observation; only the latter is the new subsequent decision, and its action is not executed;
8. no watchdog, threshold, quality gate, scheduler or automatic loop is introduced;
9. measurement and subsequent-policy classifications are descriptive only.

Expected positive lines:

```text
[multiobject3g-progress] PASS threshold_free=true one_action=true one_next_decision=true auto_loop=false
[multiobject3g-action] PASS parent_action_consumed=true one_fixation=true generic_renderer=true selected_only=true
[multiobject3g-return] PASS pre_action_replay=true one_next_decision=true next_action_executed=false auto_loop=false
[multiobject3g-check] SUMMARY passed=9 failed=0
```

Ten genuine source-mutation negatives are provided:

```text
handpick
ignorecausal
skipreplay
multiprobe
legacyrenderer
crossfuse
skipempty
executeagain
autoloop
qualitygate
```

Each must exit 1 because a named invariant detected the mutation. Exit 2 means the mutation escaped detection.

The completed workstation record must additionally verify parent/input hashes, exact pre-action replay, object purity, idempotent fusion when non-empty, exactly one acquisition, no historical rerender, one subsequent frozen-policy decision, no execution of that subsequent action, and closed evaluator truth.
