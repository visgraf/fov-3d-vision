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

## Results

Run 2026-09-20 on the workstation. HEAD before `0997eae`, working tree clean,
`50eb782` confirmed an ancestor.

**Final status: `SCENE1A_STAGEII_FAIL` — 0 of 4 full trials passed. The miss is
preserved. Scene-1a is NOT closed.**

### What the substrate did do

The **scheduler mechanics are all correct and verifiable**. In every trial the
first three fixations were exactly the contract's prescribed seeds, all later
gaze selection was autonomous, no physical fixation ever repeated, no object
exceeded the frozen six-target budget, and the total stayed under 18. Each
object's map is pure in its own instance ID. Every fused patch replayed
idempotently. Targeted overlap quality was good throughout (median 2.0–5.1 mm,
P95 5.4–11.3 mm), and per-object surface accuracy was comfortably inside the
gates on all twelve object-instances (median 4.37–5.20 mm, P95 13.15–18.25 mm).
**The lexicographic rule was followed exactly: 39 autonomous decisions across the
four trials, 39 rule-compliant, 0 violations.**

### What failed, and why

Every trial ended `object_budget_exhausted`, never `scene_complete`, and the
binding reason is a **starvation loop in the scheduler's primary key**.

The rule ranks objects by largest `predicted_new_angular_area_deg2`. An object
that is not selected does not acquire, so its map does not change, so **its bid
does not change**. If two objects persistently out-bid the third, the third's
proposal is frozen forever and it is never selected. On `triad_a` this is exact:

```text
SCENE SCHEDULER DECISIONS — triad_a/1601   (rule = lexicographic_predicted_new_area_then_frontier_score_then_instance_id)
 after sel   201                      202                      203
  2    202   area=132.97 score=12.86 | area=140.08 score=19.28* | area=105.48 score=18.12
  3    202   area=132.97 score=12.86 | area=133.08 score=11.88* | area=105.48 score=18.12
  4    201   area=132.97 score=12.86*| area=127.16 score=15.79  | area=105.48 score=18.12
  5    201   area=132.26 score= 8.69*| area=127.16 score=15.79  | area=105.48 score=18.12
  6    201   area=136.42 score= 7.03*| area=127.21 score=15.79  | area=105.48 score=18.12
  7    202   area=123.35 score= 5.44 | area=127.21 score=15.79* | area=105.48 score=18.12
  8    201   area=123.35 score= 5.44*| area=122.81 score=11.62  | area=105.48 score=18.12
  9    202   area=122.04 score=11.05 | area=122.81 score=11.62* | area=105.48 score=18.12
 10    202   area=122.04 score=11.05 | area=139.59 score= 6.74* | area=105.48 score=18.12
 11    202   area=122.04 score=11.05 | area=133.06 score=12.91* | area=105.48 score=18.12
```

Object 203's bid is **frozen at area 105.48 / score 18.12 for all ten
decisions**, permanently below the 122–140 deg² that 201 and 202 keep offering.
It receives **zero autonomous post-seed attention** on both `triad_a` seeds, and
its map never leaves its seed state: coverage 0.4726 → 0.4726, gain +0.0000,
23,197 points with **support histogram {1: 23197} — not one multi-look surfel**.

Note what this costs: **203 carries the highest frontier score of the three at
every decision (18.12 vs 12.86 and 19.28→6.74)**. It would have won on the second
key. But the first key never ties, so the second key is never consulted.

`triad_b` shows the same dynamic redistributed rather than a different mechanism:
202 sits frozen at area 110.93 for seven consecutive decisions before finally
winning once at step 9 and immediately reporting `no_frontier`; 203 is frozen at
119.99, gets two looks, drops to 104.40 and is never selected again. The last
decision there separates 201 from 203 by **0.01 deg²** (104.41 vs 104.40).

### The four full trials

| Trial | Fix | Termination | Switches | Targets per object | Samples | Loop / Blender |
|---|---:|---|---:|---|---:|---|
| triad_a/1601 | 12 | `object_budget_exhausted` | 4 | 201:5, 202:6, **203:1** | 2,516,582,400 | 144.9 / 118.2 s |
| triad_a/1667 | 13 | `object_budget_exhausted` | 5 | 201:6, 202:6, **203:1** | 2,726,297,600 | 161.9 / 129.0 s |
| triad_b/1601 | 11 | `object_budget_exhausted` | 3 | 201:6, 202:2, 203:3 | 2,306,867,200 | 141.9 / 110.5 s |
| triad_b/1667 | 11 | `object_budget_exhausted` | 3 | 201:6, 202:2, 203:3 | 2,306,867,200 | 141.6 / 110.3 s |

Physical fixation sequences (yaw,pitch):

```text
triad_a/1601  (-20,+5)(-8,-12)(+7,+5)(-3,-17)(+2,-17)(-15,0)(-10,0)(-5,0)(+7,-17)(-5,+5)(+12,-17)(+17,-17)
triad_a/1667  ... as above plus (+17,-12)(-5,+10)
triad_b/1601  (+19,+5)(-8,+5)(-7,-12)(+14,0)(+9,0)(+4,+5)(-12,-7)(-12,-2)(+4,+10)(+4,+15)(-3,+10)
triad_b/1667  identical gaze sequence to triad_b/1601
target sequences  a: [201,202,203,202,202,201,201,201,202,201,202,202(,201)]
                  b: [201,202,203,201,201,201,203,203,201,201,202]
```

### Per-object results

| Trial | Obj | Type | Seed@ | Target steps | Post-seed | Cov seed→final (gain) | Median | P95 | Points | sup>=2 | Pure |
|---|---|---|---:|---|---:|---|---:|---:|---:|---:|---|
| a/1601 | 201 | plane | 0 | 0,5,6,7,9 | 4 | 0.3837→0.7288 (+0.3451) | 4.688 mm | 14.464 mm | 36,663 | 6,205 | ✓ |
| a/1601 | 202 | cyl | 1 | 1,3,4,8,10,11 | 5 | 0.3448→0.7408 (+0.3960) | 5.096 mm | 18.146 mm | 39,247 | 11,940 | ✓ |
| a/1601 | 203 | cyl | 2 | 2 | **0** | 0.4726→0.4726 (**+0.0000**) | 4.400 mm | 14.569 mm | 23,197 | **0** | ✓ |
| a/1667 | 201 | plane | 0 | 0,5,6,7,9,12 | 5 | 0.3840→0.7919 (+0.4079) | 4.813 mm | 14.558 mm | 39,819 | 10,924 | ✓ |
| a/1667 | 202 | cyl | 1 | 1,3,4,8,10,11 | 5 | 0.3449→0.7638 (+0.4189) | 5.015 mm | 18.249 mm | 39,897 | 11,918 | ✓ |
| a/1667 | 203 | cyl | 2 | 2 | **0** | 0.4728→0.4728 (**+0.0000**) | 4.368 mm | 14.538 mm | 23,198 | **0** | ✓ |
| b/1601 | 201 | plane | 0 | 0,3,4,5,8,9 | 5 | 0.4992→0.7760 (+0.2769) | 4.604 mm | 13.255 mm | 43,881 | 11,264 | ✓ |
| b/1601 | 202 | cyl | 1 | 1,10 | 1 | 0.5392→0.5872 (+0.0480) | 4.813 mm | 17.414 mm | 30,635 | 7,796 | ✓ |
| b/1601 | 203 | cyl | 2 | 2,6,7 | 2 | 0.2841→0.3664 (+0.0823) | 5.201 mm | 17.529 mm | 17,082 | 3,932 | ✓ |
| b/1667 | 201 | plane | 0 | 0,3,4,5,8,9 | 5 | 0.4993→0.7764 (+0.2771) | 4.609 mm | 13.153 mm | 43,867 | 11,222 | ✓ |
| b/1667 | 202 | cyl | 1 | 1,10 | 1 | 0.5388→0.5871 (+0.0483) | 4.837 mm | 17.324 mm | 30,658 | 7,733 | ✓ |
| b/1667 | 203 | cyl | 2 | 2,6,7 | 2 | 0.2841→0.3664 (+0.0823) | 5.197 mm | 17.660 mm | 17,076 | 3,943 | ✓ |

Every object's surface median (4.37–5.20 mm) and P95 (13.15–18.25 mm) passed.
**No object reached the 90% final-coverage gate**; the best was 0.7919. Targeted
patch object-measurement fractions ran 0.7905–0.9567, several below the 0.90
gate. Targeted post-seed overlap medians 2.01–5.11 mm and P95 5.43–11.33 mm all
passed, but several matched counts fell below 5,000 (as low as 482). Every fused
patch in every trial replayed idempotently.

### Final object policy states — none complete

```text
triad_a/1601  201 continue (open 48, 3 cands) | 202 continue (open 33, 2) | 203 continue (open 94, 3)
triad_a/1667  201 continue (open 46, 4)       | 202 continue (open 21, 1) | 203 continue (open 98, 3)
triad_b/1601  201 continue (open 39, 2)       | 202 STOP no_frontier (0)  | 203 continue (open 46, 1)
triad_b/1667  201 continue (open 39, 2)       | 202 STOP no_frontier (0)  | 203 continue (open 52, 1)
```

Exactly two of twelve object-instances reached `no_frontier`. The scene stopped
because an object hit its six-look budget, not because the scene was complete.

### Opportunistic processing — fired, but rarely

Reported honestly. Non-target objects were processed at every fixation (22–26
non-target patches per trial), but only those clearing the 100-valid-point
threshold were fused:

```text
triad_a/1601  2 fused: step 6 obj 202 (1360 pts), step 7 obj 202 (1367 pts)
triad_a/1667  2 fused: step 6 obj 202 (1360 pts), step 7 obj 202 (1368 pts)
triad_b/1601  1 fused: step 7 obj 202 (147 pts)
triad_b/1667  1 fused: step 7 obj 202 (147 pts)
```

So the mechanism is **not dead — it fired 1–2 times per trial** — but on these
deliberately angularly disjoint base scenes a 12-degree fovea rarely holds two
objects, so it contributes little. That is a property of the separated base case,
not evidence the mechanism is wrong.

### Scene-level gate outcomes

Passed on all four: first three fixations exactly the prescribed seeds; all later
selection autonomous; no repeated physical fixation (12/12, 13/13, 11/11, 11/11
unique); no object over the six-target budget; total <= 18; at least two attention
switches (4, 5, 3, 3). Failed on all four: every object receives autonomous
post-seed attention (`triad_a` only — 203 got none); final termination
`scene_complete`; every final object state `no_frontier`.

### Every FAIL line, verbatim

```text
--- triad_a/1601 and triad_a/1667 (20 each, identical) ---
object 201 final coverage
target object 201 fix_06 measurement coverage
target object 201 fix_07 measurement coverage
object 201 fix_06 too few overlap matches
object 201 fix_07 too few overlap matches
object 201 fix_09 too few overlap matches
object 202 final coverage
target object 202 fix_03 measurement coverage
target object 202 fix_11 measurement coverage
object 202 fix_03 too few overlap matches
object 202 fix_11 too few overlap matches
object 203 too few multi-look surfels
object 203 final coverage
object 203 coverage gain over seed
object 203 was not actively revisited after seed
scene scheduler did not terminate with all objects complete
object 201 did not independently terminate no_frontier
object 202 did not independently terminate no_frontier
object 203 did not independently terminate no_frontier
not every object received autonomous post-seed attention

--- triad_b/1601 and triad_b/1667 (18 each, identical) ---
object 201 final coverage
target object 201 fix_04 measurement coverage
target object 201 fix_05 measurement coverage
target object 201 fix_08 measurement coverage
target object 201 fix_09 measurement coverage
object 201 fix_04 too few overlap matches
object 201 fix_05 too few overlap matches
object 202 final coverage
object 202 coverage gain over seed
object 203 too few multi-look surfels
object 203 final coverage
object 203 coverage gain over seed
target object 203 fix_06 measurement coverage
target object 203 fix_07 measurement coverage
object 203 fix_06 too few overlap matches
scene scheduler did not terminate with all objects complete
object 201 did not independently terminate no_frontier
object 203 did not independently terminate no_frontier

[scene1a-compare] SCENE1A_STAGEII_FAIL
  triad_a/1601 scene run failed | triad_a/1667 scene run failed
  triad_b/1601 scene run failed | triad_b/1667 scene run failed
  trial_passes 0 | mean_fixation_count 11.75
  mean_scene_final_coverage 0.619185 | min_object_final_coverage 0.366381
```

### Visuals and PLY

`scene_map.png` shows the failure directly. In `triad_a/1601` the three persistent
maps are drawn in separate greys with every physical fixation numbered: objects
201 (upper-left plane) and 202 (centre-lower ribbon) are built up across many
markers, while **object 203 (upper-right) carries a single seed patch and the
lone marker "2"** — every other fixation clusters on the other two objects. The
gaps in 201's plane are the sub-90% measurement patches.
`scene_surface_map.ply` carries `comment fixed head frame H; Stage II Scene-1a`,
has **no `element face`** (no meshing), with 99,107 vertices (`triad_a`) and
91,598 (`triad_b`).

### Code fixes

**NONE.** No source file was modified; this run changed documentation only.

### Outcome

The scheduler is faithfully implemented — the lexicographic ordering was obeyed
at all 39 autonomous decisions with zero violations — and it fails. Per the
frozen contract that is a **scientific/specification result**, preserved rather
than repaired. Scene-1a is not closed and no next Stage-II experiment is
authorized.

The substrate claims that did hold: three persistent object models were
maintained simultaneously with pure per-object identity and idempotent fusion;
attention did switch autonomously between them (3–5 times per trial); per-object
surface accuracy stayed inside the gates everywhere; and the frozen FSG6f
controller was driven unmodified, by import, with its full frontier-state,
consensus and corridor record preserved in every proposal.

What is unresolved is **attention allocation**. Ranking by largest predicted new
area is not stable under the fact that an unselected object's bid cannot change:
it admits a starvation fixed point in which the object most in need of looks —
`triad_a`'s 203, which carried the highest frontier score at every single
decision — is never selected at all.
