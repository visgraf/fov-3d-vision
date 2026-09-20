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

Prospective section intentionally left blank for workstation execution.
