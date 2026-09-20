# FSG6d — Increment 6: projected 3D-frontier exit corridors

## Status before acquisition

Prospective experiment. FSG6a, FSG6b and FSG6c remain formal FAIL records and must not be rewritten.
FSG6a established that the 3D surfel frontier itself can drive genuinely two-dimensional gaze, but exposed a left-eye-only continuation-veto asymmetry. FSG6b repaired eye symmetry and exposed the diagonal component-conjunction defect. FSG6c replaced conjunction by `max()` over compatible full edges; its smoke then showed the dual defect: one strong edge could license a diagonal step across an orthogonal boundary that was exactly resolved.

FSG6d changes the *spatial support of the continuation measurement*, not its numerical threshold.

## Scientific question

Can a truth-free persistent 3D surfel frontier drive the next foveal fixation when the oracle segmentation veto is made local to the **same projected frontier** and **same candidate direction**, rather than being a Boolean combination of whole image-edge bands?

## Frozen substrate

The following remain unchanged from the accepted FSG6/FSG6c contract:

- FSG1 instrument `FSG1-HDR-SGBM-one-original-update-original-validity-v1`;
- fixed head frame H and exact acquisition poses;
- FSG3 surfel map and 12 mm association/hash cells;
- PCA/tangent-asymmetry frontier extraction constants;
- frontier/candidate alignment threshold and minimum support;
- candidate ranking and sort key;
- 5 degree yaw/pitch 8-neighbour lattice;
- maximum six logical fixations;
- vergence 2.10 m;
- binocular oracle object masks only as a physical-boundary veto;
- continuation threshold 0.15;
- all measurement, overlap, map-accuracy, purity, idempotence, curvature-bias, coverage and pitch-span gates.

No ICP, surface fitting, meshing, filling, learned policy or evaluator truth is available to the runtime controller.

## FSG6d continuation rule

For a candidate direction, FSG6d first computes candidate-supporting 3D frontier surfels exactly as FSG6c did. Each supporting surfel already has a 3D look-ahead target from the unchanged tangent-asymmetry frontier construction.

For each rectified eye independently:

1. project the supporting frontier surfel and its 3D look-ahead target into the current rectified/cropped foveal core using the repository calibration and rectification;
2. extend that projected frontier ray to the core boundary;
3. keep only exits in the candidate's own forward image sector (`+yaw` right, `+pitch` up);
4. rasterize only the terminal corridor around those exits. Corridor longitudinal length and transverse width are both derived from the already-frozen `edge_band_fraction = 0.04`; FSG6d introduces no new numerical policy constant;
5. measure object fraction over calibration-valid support inside that corridor.

The two eyes are combined with the already accepted FSG6b symmetry:

`f_cont = max(f_L, f_R)`.

The candidate is permitted iff

`f_cont >= 0.15`.

Thus a strong full right edge cannot by itself justify a down-right move if the supporting 3D frontier exits in a different part of the image. Conversely, a legitimate up-right frontier that leaves through the high-right boundary does not need to touch the entire top edge.

The persistent 3D map still creates and ranks the candidates. Segmentation can only veto them.

## Fresh prospective validation

Fixtures and renderer seeds are fresh and are not the FSG6a/b/c records.

- `corridor_up_right`: radius 0.74 m, centre-z -2.86 m, cylinder arc -58 to +55 degrees, height 0.252 m, roll +29 degrees; seed gaze (-8,-7) degrees.
- `corridor_down_left`: radius 0.70 m, centre-z -2.70 m, cylinder arc -50 to +63 degrees, height 0.246 m, roll +211 degrees; seed gaze (+8,+7) degrees.
- seeds: 1009 and 1061.

The fixtures are deliberately non-mirror. Their analytic angular bounds are approximately:

- `corridor_up_right`: yaw [-13.883,+13.645], pitch [-9.355,+9.253] degrees;
- `corridor_down_left`: yaw [-14.091,+13.085], pitch [-9.965,+9.483] degrees.

A five-look horizontal-only ideal scan covers at most 0.460 of the fresh surface, while diagonal geometry-only construction traces cover 0.984 and 0.968 respectively. These traces are fixture-design checks only and are not prescribed runtime trajectories.

## Pre-acquisition software/integrity requirements

`tools/dev/check_fsg6d.py` must report `passed=11 failed=0`.

The positive suite includes:

- exact equality of frozen FSG6c frontier constants and numerical gates;
- fresh fixture geometry and curvature checks;
- map-state-dependent gaze reversal;
- eye-swap invariance with deliberately different L/R masks;
- the historical FSG6b/FSG6c bracket: valid corner continuation survives while one-component licensing is rejected;
- rectified-core projection checked numerically against OpenCV `undistortPoints`;
- runtime source isolation from fixture/evaluator truth;
- flat-chord, registration-shift and radial-bias sensitivity;
- horizontal-only inadequacy.

Every construction-state neighbour permitted by the analytic corridor preflight is also checked to land on a next view with at least the already-frozen 100 oracle reference pixels in each eye.

All eleven deliberate negatives must exit 1:

`policy mapstate horizontal monocular conjunction componentmax full_edge flat shift bias purity`.

In particular:

- `conjunction` protects against returning to the too-strict FSG6b rule;
- `componentmax` protects against returning to the too-permissive FSG6c rule;
- `full_edge` protects against replacing the local corridor by a whole-edge statistic.

## Runtime schedule

1. Run all FSG6d software/integrity checks and all prior regressions.
2. Record `D-FSG6d` and the prospective log entry **before acquisition**.
3. Run one small `corridor_up_right / 1009` diagnostic smoke.
4. A numerical small-profile exit 2 may proceed to full if integrity/provenance/runtime remains sound. A runtime, provenance or truth-isolation failure blocks full.
5. Run exactly four full trials once each: both fixtures x both seeds.
6. Evaluate all four and aggregate the prospectively fixed set.
7. Preserve every result. No threshold, geometry, seed, texture, SPP, vergence, fusion, budget, lattice or gate changes after acquisition begins.

## Full-trial gates

The inherited FSG6c gates remain unchanged. In particular:

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
- every nonterminal selected candidate has >=8 3D frontier surfels.

Per-fixation novelty/gain remains descriptive only.

## Interpretation discipline

A PASS supports only the narrow claim that a projected, candidate-local binocular continuation veto can coexist with the previously demonstrated 3D surfel frontier on these fresh rolled cylinders. It does not establish optimal policy, uncertainty calibration, self-occlusion reasoning, hidden-surface discovery, multiple objects, free head motion, or learned gaze.

A FAIL is preserved. Do not tune around it. Diagnose whether it is measurement, frontier extraction, candidate ranking, continuation geometry, budget/termination, or another specification consequence.
