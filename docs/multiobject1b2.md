# MultiObject-1b2 — resume object-143 growth past the legacy renderer ceiling

## Question

MultiObject-1b transferred the frozen FSG6f local grower to object 143 successfully for five new looks, but the experiment was truncated by `reality2_render_fix.py` at global step 24.  The policy was still returning `continue`; the stop was infrastructural, not scientific.

The next question is deliberately narrow:

> If the five successful MultiObject-1b looks are reused exactly and only the obsolete Reality-2 scheduling gate is removed from acquisition plumbing, does object 143 continue to the frozen policy's own stop or the genuine object-scoped watchdog?

## What changes

One new generic acquisition entry point is introduced: `tools/scene_render_fix.py`.

It preserves the Reality physical instrument:

- same Reality-1 scene and texture;
- same fixed head;
- same camera calibration and vergence;
- same SPP profile;
- same `reality2_public.render_seed(...)` physical-view RNG function;
- same Cycles backend;
- same oracle first-hit instance masks.

It differs in one respect only: it does **not** encode Reality Check 2's experiment-specific admission interval `6 <= step < 24`.

The frozen `reality2_render_fix.py` remains untouched and historically correct.

## Equivalence before flight

Before any new object-143 acquisition, the new renderer is run once at the already-saved global step 23 gaze.  Its calibration and all stored RGB/instance arrays must match the saved legacy acquisition exactly.  Failure blocks the continuation.

This check makes the change an acquisition-plumbing extension rather than a silent instrument change.

## Reuse, do not rerender

The blocked MultiObject-1b record is replayed from disk:

- seed map at global step 18;
- completed growth acquisitions/maps at steps 19–23.

The frozen policy is replayed through that history and must reproduce each saved gaze and each saved object-143 map exactly (float arrays compared at their saved float32 representation).  Those five looks are **not rerendered**.

The first new scientific acquisition is global step 24.  Global chronology is preserved; nothing is renumbered into an object-local step namespace.

## Scientific mechanism

Everything else is MultiObject-1b:

- object 141 remains read-only and byte-identical;
- object 143 alone is fused;
- `multiobject1b_policy.py` is reused unchanged;
- frozen FSG6f is reused unchanged;
- frozen 12 mm association remains unchanged;
- `<100` reconstructed id-143 points remains valid negative evidence, not failure;
- scientific stop is frozen FSG6f `no_frontier`;
- 24 **object-143 fixations including the seed** is the engineering watchdog.

The object-scoped watchdog is explicitly independent of the global acquisition index.

## Deliberately deferred

- automatic discovery of object 142/144 or any other object;
- scene-level scheduling;
- cyclopean completion of object 143;
- layered/occlusion-aware spherical representation;
- interpolation, matcher changes or texture rescue;
- evaluator truth or accuracy gates.

## Interpretation

MultiObject-1b2 is not a new perception experiment.  It is the completion of the interrupted MultiObject-1b experiment after separating a generic scene-acquisition service from the old Reality-2 experimental schedule.

If the continuation reaches the frozen policy stop, the next scientific step is cyclopean completion for object 143.  If the object-scoped watchdog is reached instead, that is recorded descriptively and interpreted separately; the watchdog is not success.
