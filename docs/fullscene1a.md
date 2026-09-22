# FullScene-1a — Scene State Snapshot

## Purpose

FullScene-1a is the formal starting point of the first bounded full-scene calibration. It freezes the exact post-MultiObject-3h state and asks one scene-level question without taking another look:

> What does the observer currently believe the scene contains, and which already-observed but uninstantiated object is next under the existing scene-selection rule?

This is the `S0` initial condition for FullScene-1.

## Why now

The MultiObject sequence established persistent multi-object geometry, scene-memory selection, epistemic audits, one global-to-local attention handoff, causal attentional reactivation, and two bounded post-handoff local actions. MultiObject-3h left another local action available but unexecuted. FullScene-1a deliberately defers that action and zooms out to the scene executive.

## Frozen experiment

FullScene-1a:

1. consumes the unique completed MultiObject-3h parent;
2. reads the live scene graph and verifies every persistent object map is pure and unchanged;
3. reconstructs the established scene-level observation scope from global steps 18 through the MultiObject-3h final step;
4. reports all positive observed instance ids and all ids that ever carried valid stereo depth;
5. excludes every currently instantiated object id;
6. reuses `multiobject3a_select.accumulate_candidate_support` and `select_next_object` unchanged;
7. writes a scene-state snapshot and a deterministic next-object selection;
8. executes no acquisition, fusion, growth, handoff, deferred local action or revisit.

The declared history intentionally preserves the earlier scene-selection scope beginning at step 18. It does not silently broaden the experiment backward into the older object-141 Reality/Cyclopean acquisition lineage.

## Scene inventory

For each live persistent object the snapshot records:

- object id;
- geometry type;
- current point count;
- current raw angular footprint-cell count;
- read-only snapshot status;
- prior epistemic status only where a still-current dedicated audit is reachable in the ancestry;
- for the currently active object, its current local-policy status, latest measurement status and deferred unexecuted gaze.

These are separate descriptive fields. FullScene-1a does not manufacture a single object-completeness score.

## Next-object rule

The candidate set is

\[
\mathcal C = \{\text{positive ids with valid-depth evidence in the declared history}\}
- \{\text{currently instantiated ids}\}.
\]

For each candidate, accumulated valid-depth support is summed over the saved observations. The next object is the largest support, with smaller integer id as the exact tie-break. This is the unchanged MultiObject-3a rule.

If a candidate is selected, the next increment is **FullScene-1b: one prescribed seed fixation for that selected object**. If no candidate remains, the first scene tour is frozen and evaluator truth may be opened only in a later evaluation increment.

## Not part of FullScene-1a

- no Blender/Cycles render or rerender;
- no new fixation;
- no surfel fusion;
- no local FSG6f action;
- no epistemic handoff;
- no revisit scheduler;
- no automatic scene scheduler;
- no semantic ranking or saliency score;
- no productivity, recovery, support or completeness threshold;
- no evaluator truth.
