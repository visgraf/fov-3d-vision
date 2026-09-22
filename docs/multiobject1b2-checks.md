# MultiObject-1b2 checks — renderer-equivalence revision 2

Pure structural checks must print:

```text
[multiobject1b2-resume] PASS partial_reuse=true renderer_equivalence=true global_history_preserved=true object143_only=true
[multiobject1b2-policy] PASS frozen_fsg6f=true object_scoped_watchdog=true auto_discovery=false quality_gated=false
[multiobject1b2-check] SUMMARY passed=6 failed=0
```

Seven genuine source-mutation negatives must each exit 1:

- `globalcap` — reintroduce the legacy global step ceiling into the generic renderer;
- `instrument` — alter the frozen vergence source;
- `rerenderpartial` — permit rerendering the five successful partial looks;
- `noequivalence` — remove the renderer-equivalence gate;
- `rgbgate` — turn RGB bit equality back into an instrument-identity gate;
- `crossfuse` — admit both scene object IDs to the object-143 map;
- `globalwatchdog` — replace the object-scoped watchdog with a global-step bound.

During execution additionally verify:

1. the blocked MultiObject-1b partial record contains exactly maps 18–23 and completed acquisitions 19–23;
2. replay through the frozen policy reproduces each saved gaze and map exactly;
3. at the saved step-23 gaze, `scene_render_fix.py` reproduces calibration, deterministic acquisition-contract fields, observation keys/shapes/dtypes and both instance masks exactly;
4. RGB re-render differences at step 23 are recorded numerically but are not used as a PASS gate and no RGB tolerance is introduced;
5. the first new acquisition is global step 24;
6. object 141 and all parent/partial key files remain byte-identical;
7. every object-143 map remains pure id 143;
8. no evaluator truth or automatic object discovery is used;
9. the run terminates only by frozen policy stop or the 24-object-fixation watchdog.

The previous exact-RGB gate failure is itself evidence for this revision: on the workstation, the frozen legacy Cycles/OPTIX renderer did not reproduce its own saved RGB bit-exactly, while calibration and instance masks remained exact. Do not add an arbitrary RGB epsilon to compensate.
