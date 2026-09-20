# Stage II / Scene-1a — Seeded multi-object active reconstruction

## Question

Can the fixed-head, static-scene observer maintain several persistent object models, allocate attention among them using their own unresolved state, return to objects when useful, and stop only when every object is independently complete?

This is the first experiment of **Stage II — Small-Scene Active Reconstruction**. It deliberately returns to the project's fixed-head/static-scene base case. The exploratory moving-head FSG7a record is preserved but is not continued here.

## Frozen substrate

Scene-1a imports the **existing FSG6f controller**; it does not copy or modify its frontier extraction, persistent OPEN/MAP_RESOLVED/BOUNDARY_RESOLVED state, candidate consensus, projected binocular continuation corridor, ranking, 5-degree lattice, or per-object six-fixation budget.

The following also remain frozen:

- FSG1 stereo instrument: `FSG1-HDR-SGBM-one-original-update-original-validity-v1`;
- FSG3 12 mm surfel association / hash cell;
- fixed head, static scene;
- prescribed vergence distance 2.10 m;
- oracle instance segmentation;
- no ICP, meshing, hole filling, or learned policy.

## New abstraction: scene scheduler

There are three known objects with instance IDs 201, 202 and 203. Each gets one prescribed seed fixation. Once all three seeds exist, every object asks the frozen FSG6f controller for its next action.

For object `i`, FSG6f either reports `no_frontier` or returns its already-defined selected candidate with:

- `predicted_new_angular_area_deg2`;
- `frontier_score`;
- next yaw/pitch gaze.

The scene scheduler chooses lexicographically:

1. largest predicted new angular area;
2. largest frontier score;
3. smaller instance ID only as a deterministic final tie-break.

No weight, learned utility, or fitted scene-level constant is introduced.

Scene completion is:

`scene_complete <=> every object independently reports no_frontier`.

## Opportunistic perception

A physical fixation has one nominal attention target, but the stereo observation is processed for **all known object IDs**. Any non-target object that contributes at least 100 valid stereo points is fused into its own persistent map. The completed binocular observation also enters every object's history, so later boundary resolution can profit from looks acquired while attention was elsewhere.

Physical gaze is globally no-revisit. The global fixation history is supplied to each object's frozen FSG6f controller.

## Fresh scenes

Two fresh non-mirror scenes are used:

- `triad_a`: left-upper plane, centre-lower convex ribbon, right-upper convex ribbon;
- `triad_b`: right-upper plane, left-upper convex ribbon, centre-lower convex ribbon.

The objects are angularly disjoint in this base case: **object-object occlusion is not yet part of Scene-1a**. All geometry lies inside the frozen FSG6f yaw/pitch policy domain.

Fresh Monte-Carlo seeds: **1601, 1667**.

Each object's prescribed seed is analytically partial (about 29–53% ideal 12-degree box coverage) and has at least one neighbouring 5-degree gaze that improves ideal coverage. These are design checks, not scientific results.

## Prospective gates

Per object:

- at least one autonomous post-seed target fixation;
- targeted patch object-measurement fraction >= 90%;
- targeted post-seed overlap matched points >= 5,000;
- targeted post-seed overlap median <= 10 mm, P95 <= 25 mm;
- idempotent fusion replay for every fused patch;
- final map contains only the object's own instance ID;
- >= 5,000 multi-look surfels;
- final analytic surface median <= 10 mm, P95 <= 30 mm;
- final truth coverage >= 90%;
- final coverage gain over the object's seed-state map >= 25 percentage points.

Scene-level:

- first three fixations are exactly the prescribed object seeds;
- after the seeds, all gaze selection is autonomous;
- every object receives autonomous post-seed attention;
- at least two post-seed attention switches occur;
- no physical fixation repeats;
- no object exceeds the frozen six-target-fixation budget;
- total scene budget <= 18 physical fixations;
- final termination is `scene_complete`;
- every final object policy state is `no_frontier`;
- all four fresh full trials pass.

Poor opportunistic visibility is descriptive rather than a per-patch gate: only nominal target patches carry the inherited FSG measurement/overlap gates.

## Deferred

Scene-1a does **not** address object discovery, object-object occlusion, semantics, moving objects, or head motion. Those are separate scene-stage questions once the scheduling/memory substrate works.
