# MultiObject-3g — execute one returned local action

## Motivation

MultiObject-3e demonstrated one bounded cyclopean-to-local handoff. MultiObject-3f then isolated the cause of the returned FSG6f reactivation: **attention was sufficient**, while the fused geometry alone was not. With the pre-fusion map but the handoff gaze/history, the frozen policy returned the same four candidates and the same next gaze. With the post-fusion map under the old gaze/history, it remained at `no_frontier`.

The returned local gaze has still never been executed. MultiObject-3g asks the remaining bounded question:

> **Does executing exactly the local action produced by attentional reactivation actually resume useful local exploration?**

## One action, one return, stop

The experiment performs exactly this sequence:

```text
completed MultiObject-3f causal audit
        |
        v
consume the already-returned local gaze
        |
        v
replay the MultiObject-3e returned decision exactly
        |
        v
execute ONE new fixation through scene_render_fix.py
        |
        v
process frozen stereo
        |
        +-- <100 target points --> valid negative evidence, no fusion
        |
        `-- otherwise ---------> selected-object-only 12 mm fusion
        |
        v
ask frozen FSG6f for ONE subsequent decision
        |
        v
record that decision and STOP
```

The subsequent action is not executed.

## Action source

The gaze is not selected again and is not hand-picked. It is consumed from:

```text
MultiObject-3f returned_next_gaze_deg
```

and must agree exactly with the unexecuted `MultiObject-3e returned_local_policy_decision.next_gaze_deg` after an exact frozen-policy replay.

This matters because 3g is testing **execution of an already-justified action**, not introducing another policy choice.

## Frozen machinery

Unchanged:

- generic `tools/scene_render_fix.py` renderer;
- existing stereo path;
- `tools/multiobject2c_policy.py` target-label adapter;
- frozen FSG6f controller;
- 12 mm association rule;
- `<100` selected-object points = valid empty evidence and no fusion;
- selected-object seed-scoped policy history;
- all previously instantiated scene objects.

No watchdog, threshold, matcher, semantics, scheduler, interpolation or truth access is added.

## Outcomes are descriptive

The executed look records:

- target visible pixels;
- valid selected-object depth points and recovery fraction;
- empty/non-empty status;
- matched/new surfels;
- map size before/after;
- idempotence and purity;
- the one subsequent FSG6f decision.

The existing `<100` empty-look rule is inherited instrument semantics, not a new MultiObject-3g quality threshold. No measured recovery, map gain or next-policy state is used as a pass gate.

Descriptive measurement outcomes are reported as one of:

```text
VALID_NEGATIVE_EVIDENCE
LOCAL_ACTION_ADDED_GEOMETRY
LOCAL_ACTION_REMEASURED_EXISTING_GEOMETRY
LOCAL_ACTION_MEASURED_NO_ASSOCIATION
```

The subsequent local-policy state is reported as one of:

```text
LOCAL_EXPLORATION_CONTINUES
LOCAL_POLICY_RESTOPS_NO_FRONTIER
LOCAL_POLICY_RETURNS_OTHER_STOP
```

## Integrity

MultiObject-3g must preserve:

- the complete MultiObject-3f audit record;
- the complete MultiObject-3e execution state;
- all selected-object historical observations through the epistemic handoff;
- all pre-existing scene-object sources.

The only new observation is the single globally next fixation. Only valid points belonging to the active selected object may be fused.

## Expected outputs

A completed record contains at least:

- `prediction_manifest.json`;
- `returned_action_report.json`;
- `returned_action_patch.npz`;
- `returned_action_rgb.png`;
- updated `object_<id>_surface_map.npz` and `.ply`;
- updated `object_<id>_policy_trace.json`;
- `scene_graph.json`;
- `scene_cyclopean_footprints.npz` and `.png`;
- one acquisition directory containing only the newly executed returned action;
- `render.log`.

## Deliberately deferred

- executing the new subsequent FSG6f action;
- a second epistemic handoff;
- automatic local/global alternation;
- revisiting other unfinished objects;
- scene scheduling;
- modifying the local controller or cyclopean selector.

The experiment stops after one executed returned action and one subsequent local-policy decision.
