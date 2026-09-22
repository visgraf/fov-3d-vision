# MultiObject-1b2 — resume object-143 growth past the legacy renderer ceiling

## Status of this revision

The first MultiObject-1b2 attempt stopped before global step 24 because its renderer-equivalence gate required bitwise equality of stored RGB arrays. Workstation evidence showed that this criterion is unsatisfiable on the current Blender/Cycles/OPTIX platform: the frozen legacy renderer, rerun at the same saved gaze with the same sample budget and configuration, also fails to reproduce its own saved RGB bit-for-bit, while calibration and both oracle instance masks remain exact.

This revision corrects **the equivalence specification only**. It is not a new scientific experiment and it does not change the perception/control mechanism.

The distinction is now explicit:

- **bit reproducibility** is required for quantities that this instrument reproduces deterministically;
- **instrument reproducibility** is established by exact configuration/provenance plus deterministic geometry/segmentation outputs;
- RGB re-render differences from Cycles/OPTIX are measured and recorded, but are not treated as an identity gate.

No RGB epsilon or post-hoc tolerance is introduced.

### Evidence from the blocked first attempt (`c588700`)

At the saved step-23 gaze, calibration and both 640x640 integer instance masks were bitwise identical between the generic renderer and the saved legacy acquisition. The RGB arrays differed at 47.408% (left) and 45.770% (right) of float32 elements, with maximum absolute difference `7.748604e-07`. Crucially, rerunning the **frozen legacy renderer itself** against its own saved acquisition produced essentially the same behavior: 47.458% / 45.669% differing RGB elements with maximum differences `7.15e-07` / `8.34e-07`, while the instance masks remained bitwise exact. This is the empirical reason the old RGB-byte gate is removed.

## Question

MultiObject-1b transferred the frozen FSG6f local grower to object 143 successfully for five new looks, but the experiment was truncated by `reality2_render_fix.py` at global step 24. The policy was still returning `continue`; the stop was infrastructural, not scientific.

The question remains unchanged:

> If the five successful MultiObject-1b looks are reused exactly and only the obsolete Reality-2 scheduling gate is removed from acquisition plumbing, does object 143 continue to the frozen policy's own stop or the genuine object-scoped watchdog?

## What changes

One generic acquisition entry point is used: `tools/scene_render_fix.py`.

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

## Corrected equivalence before flight

Before any new object-143 acquisition, the generic renderer is run once at the already-saved global step-23 gaze.

The following are blocking exact checks:

1. calibration JSON object equality;
2. exact selected acquisition-contract fields: source/backend identity, fixture, profile, gaze, SPP, left/right render seeds, Blender version, device, sample-budget fields, adaptive-sampling flag and segmentation contract;
3. identical observation keys, shapes and dtypes;
4. bitwise-identical left/right oracle instance masks.

RGB arrays are **not** required to be bitwise identical. Instead the run records, separately for `rgb_L` and `rgb_R`:

- whether they happen to be bitwise equal;
- number and fraction of differing elements;
- maximum absolute difference;
- mean absolute difference;
- RMS difference;
- p99 absolute difference.

Those RGB values are descriptive measurements only. There is no RGB tolerance, epsilon or quality threshold.

This is justified by the preceding blocked run, where the frozen legacy renderer itself differed from its own saved RGB by the same ~ulp-scale while calibration and instance masks reproduced exactly. Therefore RGB bit equality was measuring GPU accumulation determinism rather than instrument identity.

## Reuse, do not rerender

The blocked MultiObject-1b record is replayed from disk:

- seed map at global step 18;
- completed growth acquisitions/maps at steps 19–23.

The frozen policy is replayed through that history and must reproduce each saved gaze and each saved object-143 map exactly at saved float32 representation. Those five looks are **not rerendered**.

The first new scientific acquisition is global step 24. Global chronology is preserved; nothing is renumbered into an object-local step namespace.

## Scientific mechanism

Everything else is unchanged from MultiObject-1b:

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

MultiObject-1b2 remains the completion of the interrupted MultiObject-1b experiment. The specification correction removes an impossible reproducibility demand without adding a numerical tolerance and without changing any scientific control variable.

If the continuation reaches the frozen policy stop, the next scientific step is cyclopean completion for object 143. If the object-scoped watchdog is reached instead, that is recorded descriptively and interpreted separately; the watchdog is not success.
