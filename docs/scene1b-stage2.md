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

Run 2026-09-20 on the workstation. HEAD before `a49a28b`, clean `main`, `9d03829`
confirmed an ancestor.

**Final status: `SCENE1B_STAGEII_FAIL` — 0 of 4 full trials passed. The miss is
preserved. Scene-1b is NOT closed.**

**But the abstraction under test worked.** Scene-1a's starvation is gone
completely, the new rule is demonstrably load-bearing rather than decorative, and
reconstruction quality improved sharply. The failure is a different, structural
one, described below.

### Preservation and frozen source

`git diff --name-status 9d03829 HEAD` shows exactly ten files, **all additions**.
`git diff 9d03829` over the FSG1 stereo modules, `fsg3_surface_map.py`, **every
FSG6/6b/6c/6d/6e/6f module, every FSG7a module and every `scene1a_*` module**
(including `tools/dev/check_scene1a.py`), `rig.py`, `bl_common.py` and
`requirements-fsg.txt` is **empty**. Scene-1a remains a formal FAIL; no prior
decision block was edited.

`scene1b_policy.py` imports `fsg6f_frontier as object_policy` and calls
`object_policy.choose_next(...)` at one site, defining none of FSG6f's frontier
extraction, state classifier, consensus, corridor, `_new_box_area` or ranking.
Neither `scene1b_policy.py` nor `scene1b_run.py` contains `scene1b_scene`,
`evaluation_only` or any `witness` reference. The implemented rule string is
`least_service_then_predicted_new_area_then_frontier_score_then_instance_id`.

Environment: `.venv/bin/python` — Python 3.12.3, NumPy 2.2.6, OpenCV 4.13.0,
Pillow 12.3.0; Blender 5.2.1 LTS; NVIDIA GeForce RTX 4090 driver 595.84, OPTIX.

### Checks

```text
[scene1b-scene] PASS fixtures=fair_triad_c,fair_triad_d objects=[201, 202, 203] fixed_head=true static_scene=true witness_lt_budget=true
[scene1b-policy] PASS frozen_fsg6f=true scheduler=least_service_then_area_then_score fairness=true opportunistic=true all_object_completion=true
[scene1b-check] SUMMARY passed=9 failed=0
```

All eight negatives exited 1, including `areaonly` (detects a return to
Scene-1a's scheduler) and `underdesigned`. All twenty-two prior suites stayed
green — Scene-1a (8), FSG6f (14), FSG7a (7) among them — and Scene-1a's seven,
FSG6f's fifteen and FSG7a's six negatives all still exit 1.

### Design-only preflight — EVALUATOR-SIDE, NOT USED BY THE PREDICTOR

```text
fair_triad_c  bounds yaw x pitch                       seed ideal cov   3-look witness -> ideal cov
  201 plane     [-22.997,-7.003] x [+4.955,+10.998]        0.6250        (-19,8)(-14,8)(-9,8)  -> 1.0000
  202 cylinder  [ -8.596,+8.596] x [-12.042, -5.958]       0.5000        (-6,-9)(-1,-9)(4,-9)  -> 1.0000
  203 cylinder  [ +6.353,+23.647] x [+4.929,+11.071]       0.5000        (9,8)(14,8)(19,8)     -> 1.0000
fair_triad_d
  201 plane     [ -7.826,+7.826] x [-12.027, -5.919]       0.6272        (-4,-9)(1,-9)(6,-9)   -> 1.0000
  202 cylinder  [-23.087,-6.913] x [+5.958,+12.042]        0.5000        (-21,9)(-16,9)(-11,9) -> 1.0000
  203 cylinder  [ +4.634,+21.366] x [+5.973,+12.027]       0.5000        (7,9)(12,9)(17,9)     -> 1.0000
```

Every witness reaches **1.0000** ideal coverage using **three of six** available
looks. **The witness paths were not used by the predictor**: the prediction-side
grep for `witness`, `scene1b_scene` and `evaluation_only` in
`scene1b_policy.py` and `scene1b_run.py` returns False on all three tokens, and
`check_scene1b.py` asserts it.

### Smoke — COMPLETED, exit 2 (numerical only)

`fair_triad_c` / 1723 / small, run 78.4 s exit 0, eval 9.4 s exit 2.
18 fixations, `max_scene_fixations`, service counts {201:5, 202:5, 203:5},
14 switches, 43 numerical fails, opportunistic 0.
Target sequence a near-perfect round-robin:
`[201,202,203,201,202,203,201,202,203,201,202,203,201,202,203,201,203,202]`.
Blocker checks all clear — scheduler integrity **16/16 decisions rule-compliant,
0 violations**; fairness/service provenance present
(`fair_eligible_object_ids`, `minimum_autonomous_target_count`,
`fairness_restricted_decisions` = 10); FSG6f payload intact in every proposal;
`truth_opened: false`, fixed head, static scene; 18/18 unique gazes; first three
fixations exactly the contract's prescribed seeds. Full acquisition allowed.

### The four full trials

Each run once, 3,774,873,600 samples each (15,099,494,400 total). All four ended
at the 18-look global cap.

| Trial | Fix | Termination | Switches | Service counts | Fairness-restricted | Samples | Loop / Blender |
|---|---:|---|---:|---|---:|---:|---|
| c/1723 | 18 | `max_scene_fixations` | 13 | {201:5, 202:5, 203:5} | 10 | 3,774,873,600 | 256.2 / 175.8 s |
| c/1789 | 18 | `max_scene_fixations` | 13 | {201:5, 202:5, 203:5} | 10 | 3,774,873,600 | 255.7 / 175.1 s |
| d/1723 | 18 | `max_scene_fixations` | 14 | {201:5, 202:5, 203:5} | 9 | 3,774,873,600 | 244.1 / 175.7 s |
| d/1789 | 18 | `max_scene_fixations` | 14 | {201:5, 202:5, 203:5} | 9 | 3,774,873,600 | 242.3 / 175.6 s |

Physical gaze sequences:

```text
c (both seeds) (-19,+8)(-6,-9)(+9,+8)(-14,+13)(-1,-14)(+14,+13)(-9,+13)(+4,-14)(+19,+13)
               (-4,+13)(+9,-14)(+24,+13)(-4,+8)(+9,-9)(+24,+8)(+24,+3)(-9,+3)(+4,-4)
d/1723         (-4,-9)(-21,+9)(+7,+9)(-16,+14)(+1,-14)(+12,+14)(-11,+14)(+6,-14)(+17,+14)
               (+11,-14)(-6,+14)(+22,+9)(-1,+9)(+11,-9)(+22,+4)(-1,+4)(+11,-4)(+17,+4)
target seq c   [201,202,203,201,202,203,201,202,203,201,202,203,201,202,203,203,201,202]
target seq d   [201,202,203,202,201,203,202,201,203,201,202,203,202,201,203,202,201,203]
```

### Per-object results

| Trial | Obj | Type | Steps | Post | Cov seed→final (gain) | Median | P95 | Points | sup>=2 | Pure | Final state |
|---|---|---|---|---:|---|---:|---:|---:|---:|---|---|
| c/1723 | 201 | plane | 0,3,6,9,12,16 | 5 | 0.4826→**1.0000** (+0.5174) | 5.339 mm | 16.817 mm | 41,568 | 16,775 | ✓ | `no_frontier` |
| c/1723 | 202 | cyl | 1,4,7,10,13,17 | 5 | 0.4550→**1.0000** (+0.5450) | 5.132 mm | 16.529 mm | 41,183 | 20,406 | ✓ | continue |
| c/1723 | 203 | cyl | 2,5,8,11,14,15 | 5 | 0.4974→0.9287 (+0.4313) | 4.544 mm | 16.084 mm | 42,203 | 17,247 | ✓ | continue |
| c/1789 | 201 | plane | 0,3,6,9,12,16 | 5 | 0.4825→**1.0000** (+0.5175) | 5.293 mm | 16.900 mm | 41,553 | 16,776 | ✓ | `no_frontier` |
| c/1789 | 202 | cyl | 1,4,7,10,13,17 | 5 | 0.4549→**1.0000** (+0.5451) | 5.154 mm | 16.601 mm | 41,206 | 20,365 | ✓ | `no_frontier` |
| c/1789 | 203 | cyl | 2,5,8,11,14,15 | 5 | 0.4971→0.9288 (+0.4316) | 4.503 mm | 16.172 mm | 42,228 | 17,214 | ✓ | continue |
| d/1723 | 201 | plane | 0,4,7,9,13,16 | 5 | 0.5833→0.9427 (+0.3594) | 3.872 mm | 15.520 mm | 35,313 | 12,681 | ✓ | continue |
| d/1723 | 202 | cyl | 1,3,6,10,12,15 | 5 | 0.3501→0.8413 (+0.4911) | 5.170 mm | 15.825 mm | 33,859 | 15,408 | ✓ | `no_frontier` |
| d/1723 | 203 | cyl | 2,5,8,11,14,17 | 5 | 0.4951→**1.0000** (+0.5049) | 4.674 mm | 16.049 mm | 42,709 | 18,506 | ✓ | continue |
| d/1789 | 201 | plane | 0,4,7,9,13,16 | 5 | 0.5833→0.9428 (+0.3594) | 3.834 mm | 15.519 mm | 35,294 | 12,698 | ✓ | continue |
| d/1789 | 202 | cyl | 1,3,6,10,12,15 | 5 | 0.3504→0.8427 (+0.4923) | 5.142 mm | 15.784 mm | 33,846 | 15,364 | ✓ | `no_frontier` |
| d/1789 | 203 | cyl | 2,5,8,11,14,17 | 5 | 0.4952→0.9332 (+0.4381) | 4.676 mm | 15.928 mm | 39,166 | 17,000 | ✓ | continue |

**Every per-object surface, purity, multi-look and idempotence gate passed on all
twelve object-instances**: median 3.834–5.339 mm (<=10), P95 15.519–16.900 mm
(<=30), all maps pure in their own ID, 12,681–20,406 multi-look surfels
(>=5,000), every fused patch idempotent, every object >=1 autonomous look, every
gain >=0.3594 (>=0.25). **Three object-instances reached exactly 1.0000
coverage.** Ten of twelve passed the 90% coverage gate; the two that did not are
`fair_triad_d` object 202 at 0.8413/0.8427.

Targeted patch coverage ran 0.7736–0.9651; the sub-0.90 values are confined to
`fair_triad_d` (201 fix_13/fix_16, 202 fix_12/fix_15). Targeted post-seed overlap
medians 2.02–2.94 mm and P95 4.63–9.41 mm all passed; a few matched counts fell
below 5,000 on `fair_triad_d` (as low as 1,385).

### Fair scheduler audit — the rule is load-bearing

**64 autonomous decisions across the four trials. 64 rule-compliant. 0
violations.** In every decision the selected object was inside the least-served
live class **and** ranked first within that class by area, then frontier score,
then instance ID.

```text
Trial     decisions  rule-compliant  violations  fairness-restricted  fairness rejected a STRICTLY higher-area proposal
c/1723        16          16              0             10                          7
c/1789        16          16              0             10                          7
d/1723        16          16              0              9                          9
d/1789        16          16              0              9                          8
TOTAL         64          64              0             38                         31
```

**38 of 64 decisions had a fairness class strictly smaller than the live set, and
in 31 of 64 fairness rejected a proposal with strictly larger predicted new
area.** The rule is decisively load-bearing, not decorative. Worked example from
`c/1723` after step 4 — Scene-1a would have taken 201 at area 134.29; fairness
forced 203 at 119.35 because 203 had been served once fewer:

```text
after sel nmin fair-eligible   per live object: id(service) area / score   [! = rejected by fairness, higher area]
 4   203   0    [203]          201(1)! a=124.99 s=12.83 | 202(1)! a=121.17 s=19.44 | 203(0)* a=119.35 s=14.16
 7   203   1    [203]          201(2)! a=134.29 s= 9.26 | 202(2)! a=124.33 s=16.57 | 203(1)* a=119.80 s=13.42
10   203   2    [203]          201(3)! a=129.72 s=12.58 | 202(3)  a=115.17 s=20.03 | 203(2)* a=123.91 s=11.59
```

Service counts finished **perfectly equal at {201:5, 202:5, 203:5} in all four
trials**, with 13–14 attention switches, 18/18 unique gazes, per-object targets
{6,6,6} all within the six-look budget and totals exactly 18 <= 18.
**Scene-1a's starvation does not occur anywhere in Scene-1b.**

### Why all four still failed

The binding failure is arithmetic, and it is structural rather than a defect.
**Three objects x six per-object looks = 18 = `MAX_SCENE_FIXATIONS`.** Under
least-served-first the three objects advance in lockstep, so by the time any one
of them could complete, all three have consumed nearly the same number of looks
and there is no slack left to redistribute. Every trial therefore ends at exactly
18 fixations with each object having used its full six-look allowance, and
`scene_complete` requires **all three** objects to reach `no_frontier` within six
looks each. Only **5 of 12 object-instances** did (201 and 202 on `c/1789`; 201
on `c/1723`; 202 on both `d` trials).

Scene-1a failed the opposite way: it stopped at 11–13 fixations with budget
unspent and objects starved. Scene-1b spends the whole budget and starves no one,
but the fixed budget is exactly consumed by equal service.

### Every FAIL line, verbatim

```text
--- fair_triad_c/1723 (3) ---
scene scheduler did not terminate with all objects complete
object 202 did not independently terminate no_frontier
object 203 did not independently terminate no_frontier
--- fair_triad_c/1789 (2) ---
scene scheduler did not terminate with all objects complete
object 203 did not independently terminate no_frontier
--- fair_triad_d/1723 and fair_triad_d/1789 (13 each, identical) ---
target object 201 fix_13 measurement coverage
target object 201 fix_16 measurement coverage
object 201 fix_09 too few overlap matches
object 201 fix_13 too few overlap matches
object 201 fix_16 too few overlap matches
object 202 final coverage
target object 202 fix_12 measurement coverage
target object 202 fix_15 measurement coverage
object 202 fix_12 too few overlap matches
object 202 fix_15 too few overlap matches
scene scheduler did not terminate with all objects complete
object 201 did not independently terminate no_frontier
object 203 did not independently terminate no_frontier

[scene1b-compare] SCENE1B_STAGEII_FAIL
  fair_triad_c/1723 scene run failed | fair_triad_c/1789 scene run failed
  fair_triad_d/1723 scene run failed | fair_triad_d/1789 scene run failed
  trial_passes 0 | mean_fixation_count 18.0
  mean_scene_final_coverage 0.946676 | min_object_final_coverage 0.841270
```

`fair_triad_c/1789` came within **two** fail lines of passing: its only misses
are scene completion and object 203's final state.

### Opportunistic processing — zero, reported honestly

**Opportunistic non-target fused updates were 0 in all four full trials** (and 0
in the smoke), against 1–2 per trial in Scene-1a. Non-target objects were still
processed at every fixation, but none cleared the 100-valid-point threshold. Two
reasons, both properties of this design rather than of the mechanism: the
`fair_triad` objects are more widely separated than Scene-1a's, and fair
round-robin scheduling makes consecutive fixations jump between distant objects,
so a fixation aimed at one object almost never lands enough of another in the
12-degree fovea. The mechanism is exercised and inert here; Scene-1a already
showed it can fire.

### Visuals and PLY

`scene_map.png` is the clearest single contrast with Scene-1a. All three
persistent maps are substantially built up and the numbered fixation markers are
spread evenly around all three objects — six per object — where Scene-1a's
equivalent image showed one object holding a lone seed patch and a single marker.
`scene_surface_map.ply` carries `comment fixed head frame H; Stage II Scene-1b`,
has **no `element face`** (no meshing), with 124,954 vertices (`fair_triad_c`)
and 111,881 (`fair_triad_d`).

### Code fixes

**NONE.** No source file was modified; this run changed documentation only.

### Outcome

The scheduler is faithfully implemented — 64 decisions, 0 violations — and the
scene still does not complete. Per the frozen contract that is a
**scientific/specification result**, preserved rather than repaired. Scene-1b is
not closed and no next Stage-II experiment is authorized.

What Scene-1b did establish, short of the gate: **least-served-first eliminates
the Scene-1a starvation fixed point completely** — equal service {5,5,5} on every
trial, every object attended, no object ever frozen out — while **preserving the
frozen utility ordering within the fairness class** and introducing no weight,
timer or learned term. It is load-bearing (31 of 64 decisions overrode a strictly
higher-area bid) and it improved reconstruction sharply: three object-instances
reached exactly 1.0000 coverage, ten of twelve passed the 90% gate, and every
per-object surface, purity, multi-look and idempotence gate passed everywhere.

What is unresolved is **budget sufficiency, not fairness**. With three objects,
six looks each and an 18-look scene cap, perfectly fair service consumes the
global budget precisely when the per-object budgets are consumed, leaving no
slack for an object that needs one more look. Any successor has to address the
relationship between the per-object budget, the scene budget and the number of
objects — not the ordering rule.
