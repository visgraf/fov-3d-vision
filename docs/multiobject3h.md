# MultiObject-3h — one more local productivity step

## Motivation

MultiObject-3e/3f established that the cyclopean handoff reactivated frozen FSG6f primarily by **moving attention**, not by the small amount of newly fused geometry. MultiObject-3g then executed the first local action returned by that reactivation. The controller remained live, but the step was geometrically modest: 607 of 648 associated target points matched existing surfels and only 41 were new.

MultiObject-3h asks one remaining local question before the planned FullScene-1 detour:

> **Was that low novelty merely one transitional step, or does the next already-returned local action again behave mainly as re-measurement?**

This is a measurement question, not a new stopping rule.

## One more action, one return, stop

```text
completed MultiObject-3g record
        |
        v
consume its already-returned subsequent local gaze
        |
        v
replay that frozen FSG6f decision exactly
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
measure novelty and compare with the 3g local step
        |
        v
ask frozen FSG6f for ONE subsequent decision
        |
        v
record the decision and STOP
```

The newly returned action is not executed.

## Action source

The gaze is neither selected again nor hard-coded. It is consumed from:

```text
MultiObject-3g subsequent_local_policy_decision.next_gaze_deg
```

and the complete frozen policy state is reconstructed from the seed-scoped history through the epistemic handoff and first returned local action. The saved 3g decision must replay exactly before the gaze is rendered.

On the currently measured lineage this is expected to be the next global fixation after step 80, but the implementation derives the step number from the parent record rather than encoding it.

## Productivity is a readout, not a gate

For the new look the experiment records:

- target-visible pixels and valid target-depth points;
- target-depth recovery fraction;
- matched and new surfels;
- novelty fraction `new / (new + matched)` when defined;
- map-point change;
- raw angular-footprint cell change;
- range min/median/max before and after;
- the corresponding measured quantities from the first post-handoff local action in MultiObject-3g;
- the one subsequent FSG6f decision.

No value is compared with a new productivity threshold. A second low-novelty result is evidence to interpret after the run, not a reason for the runner to stop, retry, tune or choose another gaze.

## Frozen machinery

Unchanged:

- generic `tools/scene_render_fix.py` renderer;
- existing stereo path;
- `tools/multiobject2c_policy.py` target-label adapter;
- frozen FSG6f controller;
- 12 mm association rule;
- `<100` selected-object points = valid empty evidence and no fusion;
- selected-object seed-scoped policy history;
- every previously instantiated scene object.

No watchdog, matcher, semantics, scheduler, interpolation, truth access, novelty threshold or automatic loop is added.

## Expected outputs

A completed record contains at least:

- `prediction_manifest.json`;
- `local_productivity_report.json`;
- `local_productivity_patch.npz`;
- `local_productivity_rgb.png`;
- updated `object_<id>_surface_map.npz` and `.ply`;
- updated `object_<id>_policy_trace.json`;
- `scene_graph.json`;
- `scene_cyclopean_footprints.npz` and `.png`;
- one acquisition directory containing only the newly executed action;
- `render.log`.

## Deliberately deferred

- executing the newly returned FSG6f action;
- a second epistemic handoff;
- automatic local/global alternation;
- revisiting other unfinished objects;
- scene scheduling;
- any definition of “productive enough”.

After this bounded step, interpret the two consecutive post-handoff local actions. The planned next project-scale move is the **FullScene-1 bounded full-scene calibration** detour.
