# MultiObject-1b2 checks

Pure structural checks must print:

```text
[multiobject1b2-resume] PASS partial_reuse=true renderer_equivalence=true global_history_preserved=true object143_only=true
[multiobject1b2-policy] PASS frozen_fsg6f=true object_scoped_watchdog=true auto_discovery=false quality_gated=false
[multiobject1b2-check] SUMMARY passed=6 failed=0
```

Six genuine source-mutation negatives must each exit 1:

- `globalcap` — reintroduce the legacy global step ceiling into the generic renderer;
- `instrument` — alter the frozen vergence source;
- `rerenderpartial` — permit rerendering the five successful partial looks;
- `noequivalence` — remove the required renderer-equivalence gate;
- `crossfuse` — admit both scene object IDs to the object-143 map;
- `globalwatchdog` — replace the object-scoped watchdog with a global-step bound.

During execution additionally verify:

1. the blocked MultiObject-1b partial record contains exactly maps 18–23 and completed acquisitions 19–23;
2. replay through the frozen policy reproduces each saved gaze and map exactly;
3. `scene_render_fix.py` at the saved step-23 gaze reproduces calibration and observation arrays exactly;
4. the first new acquisition is global step 24;
5. object 141 and all parent/partial key files remain byte-identical;
6. every object-143 map remains pure id 143;
7. no evaluator truth or automatic object discovery is used;
8. the run terminates only by frozen policy stop or the 24-object-fixation watchdog.
