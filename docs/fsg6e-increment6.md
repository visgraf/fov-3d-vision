# FSG6e — Increment 6: persistent OPEN frontier state

## Status before acquisition

Prospective experiment. FSG6a, FSG6b, FSG6c and FSG6d remain formal FAIL records and must not be rewritten.

FSG6d settled the continuation-veto problem: its projected, candidate-local binocular corridor rescued the FSG6b corner-exit failure, avoided the FSG6c one-component walk-off, and all four full trials passed every measurement, geometry, purity, overlap, curvature and 2D-gaze gate. The sole failure was termination: raw tangent-asymmetry frontier counts remained high on a thin ribbon even after 98.7–99.0% reconstruction, leaving interior already-swept lattice candidates at the six-fixation budget.

FSG6e changes the **state of a raw frontier**, not the FSG6d continuation corridor and not the numerical gates.

## Scientific question

Can the observer decide that exploration is complete from its own persistent 3D memory and completed binocular observations, rather than requiring the raw geometric frontier population itself to disappear?

Equivalently: can FSG6 distinguish a geometric one-sided surface boundary from an **unresolved exploration frontier**?

## Frozen substrate

The following remain unchanged from FSG6d:

- FSG1 instrument `FSG1-HDR-SGBM-one-original-update-original-validity-v1`;
- fixed head frame H and exact acquisition poses;
- FSG3 surfel map and 12 mm association/hash cells;
- PCA/tangent-asymmetry raw frontier extraction, including 0.12 m look-ahead target;
- frontier/candidate alignment threshold and minimum support;
- candidate ranking and sort key;
- FSG6d projected candidate-local binocular exit corridor;
- continuation threshold 0.15 and band fraction 0.04;
- 5 degree yaw/pitch 8-neighbour lattice;
- maximum six logical fixations;
- vergence 2.10 m;
- all measurement, overlap, map-accuracy, purity, idempotence, curvature-bias, coverage and pitch-span gates.

No ICP, surface fitting, meshing, filling, learned policy, evaluator truth, fixture identity or analytic surface parameters are available to the runtime controller.

## FSG6e persistent frontier state

For every raw frontier surfel `x_i`, the unchanged frontier extractor already produces a missing-tangent look-ahead target

`t_i = x_i + 0.12 m * missing_i`.

FSG6e classifies that hypothesis into exactly one of three states.

### 1. MAP_RESOLVED

If `t_i` lies within the frozen FSG3/FSG4 association radius of any surfel already in persistent memory,

`min_s ||t_i - s|| < 0.012 m`,

then the purported missing continuation is already represented in the map. The strict `< 0.012 m` test and 0.012 m spatial-hash cell are exactly the frozen fusion semantics; no new distance threshold is introduced.

### 2. BOUNDARY_RESOLVED

If `t_i` is not map-resolved, search the observer's **completed binocular fixation history**. In each completed fixation, project `t_i` through that fixation's calibration into both rectified/cropped foveal cores. Around the projected target, use a small supported patch whose radius is derived from the already-frozen `edge_band_fraction = 0.04`.

A historical observation resolves the target as a physical boundary only when:

- the projected target is calibration-supported in **both** eyes; and
- `max(f_L, f_R) < 0.15`, where `f_L` and `f_R` are target-object fractions in those supported patches.

Thus an eye swap cannot change the state, and one eye still seeing the object keeps the frontier unresolved. A target that was looked at but whose stereo reconstruction is missing is **not** declared empty when oracle object segmentation still supports it.

### 3. OPEN

A raw frontier is OPEN only if it is neither MAP_RESOLVED nor BOUNDARY_RESOLVED.

Only OPEN frontiers contribute to the unchanged candidate-direction support count and frontier score. The already-frozen minimum remains eight supporting frontier surfels.

After that OPEN-state filter, the **unchanged FSG6d projected exit corridor** still performs the current-view physical-continuation veto and candidate ranking remains unchanged.

The intended termination meaning is therefore:

`no_frontier` = no candidate direction has enough OPEN frontier support after the settled FSG6d continuation veto.

It does **not** mean that raw tangent-asymmetry frontiers literally vanish.

## Scope of BOUNDARY_RESOLVED

FSG6e is intentionally limited to a single convex visible object surface with oracle instance segmentation. In this scope, a supported binocular observation of the 3D target location with no target-object evidence is a valid physical-boundary resolution.

This is not yet a hidden-surface or occlusion state machine. If a future self-occlusion case projects the target onto target-object pixels, it remains OPEN rather than being prematurely completed. Explicit OCCLUDED/UNSEEN reasoning is deferred to the next research step if Increment 6 closes.

## Fresh prospective validation

Fresh non-mirror curved fixtures and fresh renderer seeds are used. FSG6d records are development evidence only and are never counted as FSG6e validation.

- `closure_up_right`: radius 0.77 m, centre-z -2.88 m, cylinder arc -57 to +57 degrees, height 0.250 m, roll +31 degrees; seed gaze `(-8,-7)` degrees.
- `closure_down_left`: radius 0.69 m, centre-z -2.72 m, cylinder arc -51 to +64 degrees, height 0.248 m, roll +214 degrees; seed gaze `(+8,+7)` degrees.
- fresh seeds: `1123`, `1181`.

The fixtures are deliberately non-mirror. Analytic angular bounds are approximately:

- `closure_up_right`: yaw [-14.097,+14.097], pitch [-9.942,+9.942] degrees;
- `closure_down_left`: yaw [-13.569,+12.671], pitch [-10.365,+9.861] degrees.

A five-look horizontal-only ideal scan covers at most 0.452 of the fresh surface.

## Evaluator-only closed-loop preflight

Before any Blender acquisition, `fsg6e_scene.py` performs a design/plumbing simulation using continuous analytic cylinder truth only on the evaluator side. At each fixation it:

1. constructs the exact analytic binocular oracle masks through repository calibration/rectification;
2. inserts only analytic truth samples visible and supported in both rectified cores into an idealized persistent map;
3. stores the completed binocular observation in idealized history;
4. calls the **actual runtime `fsg6e_frontier.choose_next()`** to choose the next gaze.

The runtime policy still has no access to this truth. This is only a prospective sanity check that the written controller semantics and fixture design agree.

The expected design traces are not prescribed to Blender, but the preflight must terminate in 4–6 fixations, achieve >=90% ideal coverage, span >=10 degrees of pitch, and show that removing completed binocular history from the same final state recreates at least one eligible raw-frontier candidate. That last control makes the FSG6e state correction load-bearing rather than cosmetic.

Current local design sanity gives six-look traces with ideal coverage approximately 0.9996 and 1.0000. These numbers are **not scientific results**.

## Pre-acquisition software/integrity requirements

`tools/dev/check_fsg6e.py` must report:

`[fsg6e-check] SUMMARY passed=13 failed=0`.

The positive suite includes:

- exact equality of FSG6d frontier constants and numerical gates;
- exact preservation of the settled FSG6d projected-corridor/ranking helpers;
- three-way MAP_RESOLVED / BOUNDARY_RESOLVED / OPEN state controls;
- strict reuse of the frozen 12 mm association semantics;
- completed-history boundary resolution;
- a stereo-hole guard: an observed object target remains OPEN if not mapped;
- eye-swap invariance;
- map-state-dependent gaze reversal;
- the FSG6b/FSG6c continuation-regression bracket and FSG6d candidate-local corridor;
- target projection checked numerically against OpenCV rectification;
- source isolation from fixture/evaluator truth;
- fresh scene, curvature, flat-chord, registration-shift, radial-bias and horizontal-only controls;
- evaluator-only closed-loop preflight showing that completed history is load-bearing for termination.

All fourteen deliberate negatives must exit 1:

`policy mapstate horizontal monocular conjunction componentmax full_edge rawtermination forget_history stereo_hole flat shift bias purity`.

The new termination-specific negatives are:

- `rawtermination`: detects returning to FSG6d's raw-frontier notion of completion;
- `forget_history`: detects a controller that does not persist completed binocular boundary evidence;
- `stereo_hole`: detects the invalid shortcut "looked there but no map point means boundary" when target-object segmentation is still present.

## Runtime schedule

1. Read `CLAUDE.md`, verify clean `main`, and verify `ab13eae` is an ancestor.
2. Record `D-FSG6e` and the prospective `docs/log.md` entry **before acquisition**.
3. Run FSG6e positive checks, all fourteen negatives, and all prior regressions including FSG6d and its eleven negatives.
4. Run one small `closure_up_right / 1123` diagnostic smoke.
5. A completed small numerical exit 2 may proceed to full if integrity/provenance/runtime remains sound. Any integrity/provenance/runtime/truth-isolation failure blocks full.
6. Run exactly four full trials once each: both fresh fixtures x both fresh seeds.
7. Evaluate all four and aggregate exactly the prospectively fixed set.
8. Preserve every result. No threshold, geometry, seed, texture, SPP, vergence, fusion, budget, lattice or gate changes after acquisition begins.

## Full-trial gates

All inherited FSG6d gates remain unchanged:

- fixation count 4..6 and terminal reason `no_frontier`;
- pitch span >=10 degrees;
- every move is one nonzero 5 degree lattice step and no gaze repeats;
- object measurement fraction >=0.90 at every patch;
- >=5000 post-seed matched points;
- overlap median <=10 mm and P95 <=25 mm;
- replay idempotent and no material coverage decrease;
- final analytic curved-surface error median <=10 mm and P95 <=30 mm;
- >=5000 multi-look surfels;
- absolute supported signed radial median <=7.5 mm;
- object-pure map;
- final truth coverage >=0.90 and gain over seed >=35 percentage points;
- every nonterminal selected candidate has >=8 **OPEN** 3D frontier surfels.

Raw/map-resolved/boundary-resolved/open frontier counts are descriptive diagnostics at every step. Per-fixation novelty/gain remains descriptive only. No new numerical acceptance gate is introduced by FSG6e.

## Outcome rule

If all four prospectively fixed full trials pass, status is `FSG6E_INCREMENT6_PASS`: close Increment 6 and authorize, but do not implement, the next experiment.

If any full trial fails, status is `FSG6E_INCREMENT6_FAIL`: preserve the miss, keep Increment 6 open, and stop for Luiz/Chat. Do not tune around the outcome.

## Interpretation discipline

A PASS supports only the narrow claim that, on fresh single convex visible curved surfaces, persistent 3D memory plus completed binocular observations can distinguish raw geometric boundary from unresolved exploration frontier well enough to produce truth-free `no_frontier` termination while preserving the validated FSG6d 3D-frontier/corridor behavior.

It does not establish self-occlusion reasoning, hidden-surface discovery, multiple objects, free head motion, learned gaze, optimality or calibrated uncertainty.

## Results

Run 2026-09-20 on the workstation. HEAD before `27170a4`, working tree clean,
`ab13eae` confirmed an ancestor (`git merge-base --is-ancestor` exit 0).

**Final status: `FSG6E_INCREMENT6_FAIL` — 2 of 4 full trials passed.** The miss is
preserved. Increment 6 is NOT closed and no next experiment is authorized.

**The central FSG6e claim is nevertheless demonstrated on real acquisitions.**
Both `closure_down_left` trials terminated `no_frontier` with the raw
tangent-asymmetry frontier still at **169–170** surfels while OPEN had collapsed
to **6–9** and every candidate direction fell below the frozen minimum of eight.
Raw frontier count can remain high while OPEN resolves and `no_frontier` occurs —
which is exactly what FSG6d could not do.

### FSG6a–FSG6d preserved

All four remain formal FAILS with Results, log entries, decision outcomes, README
rows and all `previews/fsg6/`, `previews/fsg6b/`, `previews/fsg6c/` and
`previews/fsg6d/` artifacts untouched. The accepted `z -> gaze` repair is present
in all five runners (`fsg6_run.py:64`, `fsg6b/c/d/e_run.py:65`). `git diff
ab13eae` over the FSG1 stereo modules, `fsg3_surface_map.py`, **all FSG6a, FSG6b,
FSG6c and FSG6d modules**, `rig.py`, `bl_common.py` and `requirements-fsg.txt` is
empty.

### Constants and normalized policy comparison

`SURFACE_FRONTIER` and `TARGETS` are **exactly equal** to `fsg6d_public` with no
differing keys; `FUSION == fsg4_public.FUSION = {0.012, 0.012}` and is precisely
what MAP_RESOLVED reuses; `edge_object_fraction_min` 0.15; `edge_band_fraction`
0.04; `lookahead_m` 0.12; step 5.0; budget 6; minimum support 8;
`alignment_cos_min` 0.50; vergence 2.10; object 131. The BOUNDARY_RESOLVED patch
radius is derived, not new: core 128 -> band 5 px, radius 2 px; core 256 -> 10 px,
5 px.

The functional change is confined to the OPEN-state filter plus completed
binocular history plumbing: new `_target_mapped_mask`,
`_target_patch_eye_evidence` and `classify_frontier_state`; `choose_next` taking
`observation_history` and computing `support = raw_support & open`. **Verified
frozen by `inspect.getsource` text-identity (modulo module naming)**:
`extract_frontier`, `_project_rectified_core`, `_ray_exit`,
`_exit_corridor_mask`, `_corridor_eye_evidence`, `_project_frontier_pairs`,
`_candidate_continuation_from_projected`, `_new_box_area`, `_voxel_centroids`,
`edge_evidence`, `binocular_edge_evidence` — all identical. The candidate sort
key is verbatim identical; `alignment_cos_min` used once in each; the 0.12 m
look-ahead line identical. `angular_coordinates` differs only in an error string.
`fsg6e_compare.py`/`fsg6e_render_fix.py` identical to FSG6d modulo naming;
`fsg6e_run.py` differs only by accumulating and passing `observation_history` and
the policy label strings; `fsg6e_eval.py` differs only by adding the descriptive
`frontier_state_by_fixation` block — **the `fails` gate logic is unchanged, so
FSG6e adds no acceptance gate.**

Python 3.12.3, NumPy 2.2.6, OpenCV 4.13.0, Pillow 12.3.0, Blender 5.2.1 LTS,
Cycles OPTIX on an NVIDIA GeForce RTX 4090.

### Checks

```text
[fsg6e-scene] PASS up_right=[-14.097,14.097]x[-9.942,9.942] down_left=[-13.569,12.671]x[-10.365,9.861] horizontal_ideal_max=0.452 chord_max_mm=0.165 corridor_preflight=true persistent_state_preflight=true raw_frontier_termination_rejected=true traces={closure_up_right:6fix/0.9996, closure_down_left:6fix/1.0000}
[fsg6e-frontier] PASS map_state_changes_2d_direction=true persistent_state_three_way=true historical_boundary_state=true stereo_hole_not_boundary=true eye_swap_invariant=true projected_frontier_corridor=true resolved_boundary_stops=true
[fsg6e-check] SUMMARY passed=13 failed=0
```

All fourteen negatives exited 1, including the three termination-specific guards
`rawtermination`, `forget_history` and `stereo_hole`. All eighteen FSG1–FSG6d
regression suites stayed green, and FSG6a's seven, FSG6b's eight, FSG6c's nine
and FSG6d's eleven negatives all still exit 1.

### Closed-loop preflight — DESIGN/PLUMBING ONLY, NOT A SCIENTIFIC RESULT

Analytic cylinder truth builds an idealized map and history on the evaluator
side; every next gaze comes from the actual runtime `choose_next`.

```text
closure_up_right   raw 152,120,109,136,124,133 | OPEN 84,68,76,62,39,2  | cands 5,5,5,3,1,0 -> no_frontier, ideal cov 0.9996, pitch span 15.0
closure_down_left  raw 128,117,105,148,131,135 | OPEN 68,70,75,65,34,6  | cands 3,3,5,3,1,0 -> no_frontier, ideal cov 1.0000, pitch span 15.0
LOAD-BEARING CONTROL: same final state WITHOUT completed history -> stops=False, candidates=1 (both fixtures)
```

### Smoke — COMPLETED, exit 2 (numerical only)

`closure_up_right` / 1123 / small: 6 fixations
`(-8,-7)(-3,-2)(2,3)(7,8)(12,8)(12,3)`, `max_fixations`, coverage 90.73%, median
8.072 mm, p95 29.214 mm. State raw 233–265 with OPEN 141,121,120,124,127,86 —
OPEN does **not** collapse at small profile, because measurement coverage is only
0.842–0.897 and the hole-ridden map generates far more raw frontier. FAIL lines:
termination; `fix_00`–`fix_05` object measurement coverage; `fix_01`–`fix_05` too
few overlap matches. All resolution-scaled. No exception, so full was not blocked.

### The four full trials

Each run exactly once, 1,258,291,200 samples each (5,033,164,800 total).

| Trial | Trajectory | Fix | Term | Final cov. | Median | P95 | Radial | Status |
|---|---|---:|---|---:|---:|---:|---:|---|
| up_right/1123 | (-8,-7)(-3,-2)(2,3)(7,8)(12,8)(12,3) | 6 | `max_fixations` | 98.718% | 3.808 mm | 13.295 mm | +1.266 mm | **FAIL** |
| up_right/1181 | (-8,-7)(-3,-2)(2,3)(7,8)(12,13)(17,13) | 6 | `max_fixations` | 95.923% | 3.782 mm | 13.134 mm | +1.662 mm | **FAIL** |
| down_left/1123 | (8,7)(3,2)(-2,-3)(-7,-8)(-12,-8)(-12,-3) | 6 | `no_frontier` | 98.639% | 4.506 mm | 14.714 mm | -2.811 mm | PASS |
| down_left/1181 | (8,7)(3,2)(-2,-3)(-7,-8)(-12,-8)(-12,-3) | 6 | `no_frontier` | 98.840% | 4.507 mm | 14.835 mm | -2.842 mm | PASS |

Frontier state (raw / map-resolved / boundary-resolved / OPEN / candidates):

```text
up_right/1123  (215,0,91,124,5) (205,2,111,92,7) (181,7,73,101,5) (208,9,105,94,3) (173,4,103,66,2) (187,4,167,16,1)
up_right/1181  (220,0,92,128,5) (208,8,102,98,7) (188,10,68,110,6) (210,11,107,92,4) (86,0,72,14,3) (43,0,27,16,1)
down_left/1123 (185,0,81,104,3) (228,9,79,140,5) (215,14,54,147,6) (192,3,102,87,3) (162,0,111,51,2) (170,0,161,9,0)
down_left/1181 (187,0,78,109,3) (227,15,73,139,5) (214,11,56,147,6) (191,2,105,84,3) (157,0,108,49,1) (169,0,163,6,0)
```

Selected OPEN support / raw support per fixation:

```text
up_right/1123  OPEN 45,41,31,61,60,11 | raw 46,59,50,63,83,96
up_right/1181  OPEN 42,38,31, 8,14,13 | raw 44,56,49,25,21,13
down_left/1123 OPEN 45,56,45,63,48    | raw 45,65,60,74,76
down_left/1181 OPEN 48,55,43,65,45    | raw 48,64,57,77,74
```

### All FAIL lines, verbatim

```text
closure_up_right/1123:  3D frontier policy did not terminate by resolving the frontier
closure_up_right/1181:  3D frontier policy did not terminate by resolving the frontier
closure_up_right/1181:  fix_04 object measurement coverage
closure_up_right/1181:  fix_05 object measurement coverage
closure_up_right/1181:  fix_04 too few overlap matches
closure_up_right/1181:  fix_05 too few overlap matches
closure_down_left/1123: (none)
closure_down_left/1181: (none)
[fsg6e-compare] FSG6E_INCREMENT6_FAIL   trial_passes 2/4
```

### Diagnosis

**The persistent state works.** On `closure_down_left`, enumerating every
neighbour at the final fixation with the runtime functions:

```text
down_left/1123 at (-12,-3) raw=170 map_res=0 bnd_res=161 OPEN=9
   (-17,-8) raw=27  OPEN=2 | (-17,-3) raw=85 OPEN=5 | (-17,+2) raw=100 OPEN=7
   (-12,+2) raw=87  OPEN=6 | (-7,-3)  raw=32 OPEN=0 | (-7,+2)  raw=8   OPEN=3
   (-12,-8) and (-7,-8) already visited  ->  every direction below the frozen 8  ->  no_frontier
```

Raw support per direction is 8–100, OPEN is 0–7 everywhere. **This is the FSG6e
mechanism doing exactly what it was designed to do**, and it is what FSG6d could
not achieve.

**Why `closure_up_right` failed, seed 1123.** OPEN collapsed 124 -> 16 and
candidates 5 -> 1, but one survived: `(12,-2)` with 96 raw aligned surfels of
which 82 were BOUNDARY_RESOLVED and 3 MAP_RESOLVED, leaving **11 OPEN against the
frozen minimum of 8**. The filter removed 85 of 96; three more resolutions would
have terminated the run. Its corridor was only 0.2252.

**Why `closure_up_right` failed, seed 1181 — and differently.** At fixation 3,
gaze `(7,8)`, the candidate `(12,13)` was admitted and selected despite having the
weakest support of the four (**8 OPEN, exactly the minimum**, from 25 raw) and the
weakest corridor (0.3230), because `predicted_new_angular_area` is the primary
sort key and `(12,13)` scores 134.26 against 103.65, 73.04 and 15.09. `(12,13)` is
above the fixture's `+9.942` degree pitch bound, so fixations 4 and 5 fell largely
off the ribbon: object measurement coverage 0.8268 and 0.6650, matched 3,879 and
404, and coverage flat at 95.9%.

The two seeds diverge on a knife edge. Recomputed at the identical state, the
`(12,13)` corridor fraction is:

```text
seed 1123: combined 0.1490  L f=0.1490 obj=138 sup=926 rays=6 | R f=0.0000 obj=0 sup=1031 rays=6  -> VETOED (< 0.15)
seed 1181: combined 0.3230  L f=0.3230 obj=208 sup=644 rays=6 | R f=0.0000 obj=0 sup=734  rays=6  -> PERMITTED
```

Both have OPEN support >= 8 (10 and 8). The decisive quantity is a corridor
fraction computed from only **six** projected frontier rays, landing at 0.1490
versus 0.3230 across a Monte-Carlo seed change and straddling the frozen 0.15
threshold. The right eye contributes exactly 0.0000 in both.

**This is a specification result, not an implementation defect, and no code fix
was made.** The code faithfully implements the written persistent-state rule; the
OPEN filter demonstrably works, reducing `(12,13)` support 25 -> 8 and 29 -> 10
and delivering clean `no_frontier` on both `closure_down_left` trials. What fails
is the interaction of that correctly-implemented rule with three **frozen**
pieces FSG6e was not permitted to vary: the FSG6d corridor evaluated on a
six-ray sample, the `predicted_new_angular_area` primary sort key that rewards
the most extreme move, and the minimum support of exactly 8. Per §Runtime
schedule the miss is preserved and returned to Luiz/Chat.

### Visuals and PLY

`growth_truth.png` shows `closure_down_left` sweeping cleanly
(35.7 -> 55.1 -> 77.3 -> 98.6 -> 98.7 -> 98.6%) and `closure_up_right`/1181
visibly stalling after fixation 3 (95.9% flat for three panels) as the gaze
leaves the ribbon. `coverage_3d_frontier.png` shows three curves saturating near
98.6–98.8% and the 1181 curve flat at 95.9%. Every `surface_map.ply` carries
`comment fixed head frame H`, has **no `element face`**, and independent reads
give median cylinder radius **0.77106 m against a true 0.770** and **0.68780–
0.68782 m against a true 0.690** — about +1.1 mm and −1.2 mm.

### Cost

Smoke run 17.5 s (loop 17.34 s, Blender 11.81 s) / eval 8.5 s. Full runs 1m10.5s,
1m0.6s, 1m11.4s, 1m10.9s (loop 70.36/60.43/71.28/70.75 s, Blender 34.4–34.7 s
each). Aggregation under a second. Batch class throughout.

### What holds

FSG6e answered its own scientific question in the affirmative on half the
prospectively fixed set, and the answer is visible in the diagnostics rather than
inferred: **the observer terminated from its own persistent 3D memory and
completed binocular observations while the raw geometric frontier remained at
169–170 surfels.** The distinction between a geometric one-sided surface boundary
and an unresolved exploration frontier is therefore representable with the frozen
12 mm association and the frozen 0.15 threshold, with no new numerical constant
and no completeness-percentage or low-gain shortcut. What is not yet established
is robustness: on `closure_up_right` the decision rides on a six-ray corridor
sample and a support count of exactly 8, and a Monte-Carlo seed change flips the
trajectory off the surface.
