# Stage II / Scene-1c — Certified composition of active object reconstructions

## Question

Does active reconstruction compose across several objects under the already-settled fair scene scheduler?

More precisely: if each object placement is **prospectively certified** to be solvable by the frozen FSG6f controller within its unchanged six-look budget, in the exact complete three-object rendering context, can the unchanged Scene-1b fair scheduler interleave those object processes and complete the whole scene within the unchanged 18-look scene budget?

Scene-1a and Scene-1b remain preserved formal FAILs. Scene-1a established the multi-object memory/identity substrate but exposed starvation under unconstrained area-first scheduling. Scene-1b eliminated starvation decisively, but its three objects did not all independently reach `no_frontier` inside six looks, so budget sufficiency could not be separated cleanly from component solvability.

## Frozen substrate

Scene-1c introduces **no new runtime perception or scheduling mechanism**. Frozen:

- FSG1 stereo instrument: `FSG1-HDR-SGBM-one-original-update-original-validity-v1`;
- FSG3 12 mm surfel association / hash cell;
- all FSG6f frontier extraction, persistent OPEN/MAP_RESOLVED/BOUNDARY_RESOLVED state, candidate consensus, projected binocular corridor, ranking and 5-degree lattice;
- Scene-1b least-autonomous-service eligibility and its within-class area / frontier-score / instance-ID ordering;
- six target fixations maximum per object;
- 18 physical fixations maximum for three objects;
- fixed head, static scene, 2.10 m vergence;
- oracle instance segmentation;
- opportunistic all-known-object processing from every ensemble fixation;
- global physical no-revisit;
- scene completion only when every object independently reports `no_frontier`;
- every Scene-1b numerical per-object and scene-level acceptance gate.

`scene1c_policy.py` imports the frozen Scene-1b policy layer rather than reproducing it. Scene-1b in turn imports FSG6f.

## New experimental protocol: certify the actors before the ensemble

For every `(fixture, seed, object)` triple, run a full-profile **component certification control** before any Scene-1c ensemble acquisition.

A component control:

1. renders the **complete three-object fixture** with exactly the same renderer, geometry, textures, seed and target object's prescribed seed gaze used by the later ensemble;
2. reconstructs only the nominated object;
3. lets the unchanged FSG6f controller choose that object's subsequent gazes;
4. allows at most the unchanged six target looks including the seed;
5. sees no evaluator geometry or truth during prediction;
6. is evaluated afterward with exactly the Scene-1b per-object gates and must terminate `no_frontier`.

There are `2 fixtures x 2 Monte-Carlo seeds x 3 objects = 12` prospectively fixed full component controls. **All twelve must pass before the ensemble stage is allowed to run.** A failed actor is not replaced, resized, reseeded, or tuned. If certification fails, Scene-1c stops with `SCENE1C_COMPONENT_CERTIFICATION_FAIL` and no ensemble full acquisition is run.

The certification result is an experimental authorization condition only. It is not supplied to the scene policy as a runtime input.

## Fresh scenes

Two fresh non-mirror base scenes are used:

- `cert_triad_e`;
- `cert_triad_f`.

Each contains three compact convex cylindrical ribbons, instance IDs 201, 202 and 203, arranged in angularly disjoint regions. The shapes are intentionally in the already successful FSG6f qualitative family; Stage II is not asking a new geometry question here. Front surfaces remain near the validated 2.10 m working distance.

Fresh Monte-Carlo seeds: **1847, 1901**.

Each object has one prescribed partial seed. Evaluator-only geometry also carries a three-look 5-degree-lattice **box-coverage witness** beginning at that seed. Every witness reaches at least 98% ideal angular coverage while using only three of the six available object looks. This is only a prospective geometry sanity check; it is neither a policy prediction nor the component certification. The actual certification is the full rendered FSG6f control above.

## Prospective component-certification gates

For each of the twelve full controls:

- at least one autonomous post-seed target fixation;
- targeted patch object-measurement fraction >= 90%;
- targeted post-seed overlap matched points >= 5,000;
- targeted post-seed overlap median <= 10 mm, P95 <= 25 mm;
- idempotent fusion replay for every patch;
- final map contains only the nominated object's instance ID;
- >= 5,000 multi-look surfels;
- final analytic surface median <= 10 mm, P95 <= 30 mm;
- final truth coverage >= 90%;
- final coverage gain over the seed-state map >= 25 percentage points;
- no physical fixation repeats;
- <= 6 total target looks including the seed;
- final FSG6f state and termination are both `no_frontier`.

The twelve-control aggregate must return `SCENE1C_COMPONENT_CERTIFICATION_PASS` before the ensemble proceeds.

## Prospective ensemble gates

Unchanged from Scene-1b:

- the first three fixations are exactly the prescribed seeds, one per object;
- every later target/gaze decision is autonomous;
- every decision obeys the frozen least-service-first Scene-1b scheduler;
- every object receives autonomous post-seed attention;
- at least two post-seed attention switches occur;
- every fused patch replays idempotently and every final object map is pure;
- the same per-object measurement, overlap, support, surface-error, coverage and coverage-gain gates listed above hold;
- no physical fixation repeats;
- no object exceeds six target looks;
- total scene fixations <= 18;
- every final object policy state is `no_frontier`;
- final scene termination is `scene_complete`;
- all four fresh full ensemble trials pass.

Opportunistic non-target fusion remains part of the Scene-1b substrate but is descriptive rather than a gate.

## Composition diagnostic

For each `(fixture, seed, object)`, compare the object's target-gaze sequence in the certified single-object control with that object's target subsequence inside the ensemble. Exact equality is **not** a gate: interleaved observations enter all object histories by design and can legitimately alter later FSG6f state. Report the common prefix and first divergence, if any. This diagnostic distinguishes simple temporal interleaving from a genuinely scene-induced interaction.

## Decision rule

Three outcomes are possible and fixed prospectively:

1. If any of the twelve component controls fails, report `SCENE1C_COMPONENT_CERTIFICATION_FAIL`, preserve the controls, do not run the full ensemble, and stop for Luiz/Chat.
2. If all components certify but any of the four ensemble trials fails, report `SCENE1C_STAGEII_FAIL`. This is evidence that individually solvable active object processes did not compose under the frozen scene substrate.
3. Only if all twelve component controls and all four ensemble trials pass may the aggregate report `SCENE1C_STAGEII_PASS` and Scene-1c close.

Do not increase either budget, change an actor after certification, alter the scheduler, retune FSG6f, change a fixture/seed/gate, or rerender after a numerical miss.

## Deferred

Object discovery, object-object occlusion, semantic reasoning, moving objects and moving observers remain later Stage-II/future-stage questions.

## Results

Pending prospective workstation acquisition.
