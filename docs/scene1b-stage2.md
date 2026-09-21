# Stage II / Scene-1b — Fair multi-object active reconstruction

## Question

Can the fixed-head, static-scene observer complete a small scene of several known objects when scene-level attention is constrained to be fair, while the per-object FSG6f controller remains frozen?

Scene-1a is preserved as a formal FAIL. Its multi-object memory/identity substrate worked, but its unconstrained area-first scheduler admitted a starvation fixed point: a live object could remain unvisited because its bid did not change while other objects kept winning the primary key.

## Frozen substrate

Scene-1b does **not** repair or alter the object controller. It imports the existing FSG6f controller unchanged. Frozen:

- FSG1 stereo instrument: `FSG1-HDR-SGBM-one-original-update-original-validity-v1`;
- FSG3 12 mm surfel association / hash cell;
- all FSG6f frontier extraction, persistent OPEN/MAP_RESOLVED/BOUNDARY_RESOLVED state, candidate consensus, projected binocular corridor, candidate ranking and 5-degree lattice;
- six target fixations maximum per object;
- fixed head, static scene, 2.10 m vergence;
- oracle instance segmentation;
- opportunistic all-known-object processing from each physical fixation;
- global physical no-revisit;
- scene completion only when every object independently reports `no_frontier`;
- no ICP, meshing, hole filling, object discovery, learned policy, semantics, head motion or object-object occlusion logic.

## New abstraction: fairness before utility

For each live object `i`, let `n_i` be the number of **autonomous post-seed target fixations** already allocated to that object.

First compute:

`n_min = min_i n_i` over live objects only.

Only objects with `n_i == n_min` are eligible for the next scene action. Within that fairness class, Scene-1a's utility ordering is retained exactly:

1. largest FSG6f `predicted_new_angular_area_deg2`;
2. largest FSG6f `frontier_score`;
3. smaller instance ID only as a deterministic final tie-break.

Thus no fitted weight, learned utility, confidence threshold or starvation timeout is introduced. Fairness is a structural eligibility constraint; the old utility remains the within-class ranking.

A completed object (`no_frontier`) leaves the live set and does not constrain the service count of remaining objects.

## Fresh base scenes

The first fair-scheduling experiment uses two fresh, deliberately easier non-occluding scenes:

- `fair_triad_c`: upper-left plane, lower-centre convex ribbon, upper-right convex ribbon;
- `fair_triad_d`: lower-centre plane, upper-left convex ribbon, upper-right convex ribbon.

All front surfaces lie near the already validated 2.10 m vergence regime. The objects are compact and angularly disjoint. This isolates scene scheduling from the harder geometry that confounded interpretation in Scene-1a.

Fresh Monte-Carlo seeds: **1723, 1789**.

Each object has one prescribed partial seed. Evaluator-only geometry contains a three-look, 5-degree-lattice **design witness** beginning at that seed. Every witness covers at least 98% of the analytic object under ideal 12-degree boxes and uses only three of the six available object looks. The witness is not exposed to the prediction loop, is not a prescribed path, and is not a policy prediction; it is only a prospective scene-design reachability check.

## Prospective gates

Per object, unchanged from Scene-1a:

- at least one autonomous post-seed target fixation;
- targeted patch object-measurement fraction >= 90%;
- targeted post-seed overlap matched points >= 5,000;
- targeted post-seed overlap median <= 10 mm, P95 <= 25 mm;
- idempotent fusion replay for every fused patch;
- final map contains only the object's own instance ID;
- >= 5,000 multi-look surfels;
- final analytic surface median <= 10 mm, P95 <= 30 mm;
- final truth coverage >= 90%;
- final coverage gain over the object's seed-state map >= 25 percentage points;
- final per-object policy state is `no_frontier`.

Scene-level:

- first three fixations are exactly the prescribed object seeds;
- after the seeds, all gaze selection is autonomous;
- every scheduler decision obeys least-service eligibility before the frozen area/score/ID utility ordering;
- every object receives autonomous post-seed attention;
- at least two post-seed attention switches occur;
- no physical fixation repeats;
- no object exceeds the frozen six-target-fixation budget;
- total scene budget <= 18 physical fixations;
- final termination is `scene_complete`;
- all four fresh full trials pass.

Poor opportunistic visibility remains descriptive rather than a per-patch gate: only nominal target patches carry the inherited measurement/overlap gates.

## Decision rule

Scene-1b passes only if all four prospective full trials return `SCENE1B_RUN_PASS` and the four-trial aggregate returns `SCENE1B_STAGEII_PASS` with every prospective gate above satisfied.

A faithfully implemented miss is preserved. Do not retune geometry, seed gazes, service rule, within-class ranking, FSG6f constants, budgets, fusion or gates after observing outcomes.

## Deferred

If Scene-1b succeeds, later Stage-II work may make the scene harder. Object discovery, object-object occlusion, semantics and moving observers remain separate questions.

## Results

Pending prospective workstation acquisition.
