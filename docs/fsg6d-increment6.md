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

## Results

Run 2026-09-20 on the workstation. HEAD before `103d8b4`, working tree clean,
`fc35bc8` confirmed an ancestor (`git merge-base --is-ancestor` exit 0).

**Final status: `FSG6D_INCREMENT6_FAIL` — 0 of 4 full trials passed.** Every trial
fails on **exactly one gate, the same one**: termination `max_fixations` instead
of `no_frontier`. The miss is preserved. Increment 6 is NOT closed and no next
experiment is authorized.

### FSG6a, FSG6b and FSG6c preserved

All three remain formal FAILS with Results, log entries, decision outcomes,
README rows and all `previews/fsg6/`, `previews/fsg6b/` and `previews/fsg6c/`
artifacts untouched. The accepted `z -> gaze` repair is present in all four
runners (`fsg6_run.py:64`, `fsg6b_run.py:65`, `fsg6c_run.py:65`,
`fsg6d_run.py:65`). `git diff fc35bc8` over the FSG1 stereo modules,
`fsg3_surface_map.py`, **all FSG6a, FSG6b and FSG6c modules**, `rig.py`,
`bl_common.py` and `requirements-fsg.txt` is empty.

### Constants and normalized policy comparison

`SURFACE_FRONTIER` and `TARGETS` are **exactly equal** to `fsg6c_public` with no
differing keys; `FUSION == fsg4_public.FUSION = {0.012, 0.012}`;
`edge_object_fraction_min` 0.15; `edge_band_fraction` 0.04; step 5.0; budget 6;
minimum frontier support 8; `alignment_cos_min` 0.50; vergence 2.10; object 121.
Corridor geometry is derived, not new: core 128 -> 5 px longitudinal / 2 px
transverse half-width; core 256 -> 10 px / 5 px.

The naming-normalized diff confines the functional change to the veto:
`_project_rectified_core`, `_ray_exit`, `_exit_corridor_mask`,
`_corridor_eye_evidence`, `_project_frontier_pairs`,
`_candidate_continuation_from_projected`, `candidate_continuation_evidence`, plus
`_retired_component_max_allowed` for diagnostics; and in `choose_next` the
continuation test now runs after the candidate's supporting surfels are known,
since the corridor is built from those surfels. **Verified unchanged**: the
candidate sort key is byte-identical; `alignment_cos_min` appears exactly once in
both; the look-ahead `target = x + cfg["lookahead_m"] * missing` is computed
identically at `fsg6c_frontier.py:127` and `fsg6d_frontier.py:123` — FSG6d only
**returns** it as `target_xyz_h`, which is data plumbing. `_voxel_centroids`, the
PCA/tangent extraction and `_new_box_area` are untouched. `fsg6d_eval.py`,
`fsg6d_compare.py`, `fsg6d_render_fix.py` are identical to FSG6c modulo naming;
`fsg6d_run.py` differs in exactly one line, the policy label string.

Python 3.12.3, NumPy 2.2.6, OpenCV 4.13.0, Pillow 12.3.0, Blender 5.2.1 LTS,
Cycles OPTIX on an NVIDIA GeForce RTX 4090.

### Checks

```text
[fsg6d-scene] PASS up_right=[-13.883,13.645]x[-9.355,9.253] down_left=[-14.091,13.085]x[-9.965,9.483] horizontal_ideal_max=0.460 chord_max_mm=0.156 corridor_preflight=true all_permitted_neighbours_population_checked=true
[fsg6d-frontier] PASS map_state_changes_2d_direction=true eye_swap_invariant=true projected_frontier_corridor=true one_component_cannot_license_other=true resolved_boundary_stops=true
[fsg6d-check] SUMMARY passed=11 failed=0
```

All eleven negatives exited 1, including the three historical guards:
`conjunction`, `componentmax` and `full_edge`. All seventeen FSG1–FSG6c
regression suites stayed green, and FSG6a's seven, FSG6b's eight and FSG6c's nine
negatives all still exit 1.

### Corridor preflight

`corridor_up_right` bounds yaw [-13.883,+13.645], pitch [-9.355,+9.253],
geometry-only ideal coverage 0.9841. `corridor_down_left` yaw
[-14.091,+13.085], pitch [-9.965,+9.483], 0.9676. Horizontal-only ideal max
0.4597; max strip chord error 0.1562 mm. Every construction transition is
reachable under the exact runtime corridor rasterizer, with combined fractions
0.7167–1.0000 over 24–36 projected frontier rays and 113–141 support pixels.
Enumerating **all** neighbours at **all** construction states, 24 and 23
directions are permitted and the worst destination still carries 2,151 and 2,269
oracle reference pixels against the >=100 gate — the control whose absence let
FSG6c walk off the fixture.

### The four full trials

Each run exactly once, 1,258,291,200 samples each (5,033,164,800 total).

| Trial | Trajectory (yaw,pitch) | Fix | Term | Final cov. | Median | P95 | Radial |
|---|---|---:|---|---:|---:|---:|---:|
| up_right/1009 | (-8,-7)(-3,-2)(2,3)(7,8)(12,8)(12,3) | 6 | `max_fixations` | 98.987% | 3.476 mm | 12.691 mm | +0.460 mm |
| up_right/1061 | (-8,-7)(-3,-2)(2,3)(7,8)(12,8)(12,3) | 6 | `max_fixations` | 99.042% | 3.463 mm | 12.657 mm | +0.445 mm |
| down_left/1009 | (8,7)(3,2)(-2,-3)(-7,-8)(-12,-8)(-12,-3) | 6 | `max_fixations` | 98.676% | 3.933 mm | 13.371 mm | +0.718 mm |
| down_left/1061 | (8,7)(3,2)(-2,-3)(-7,-8)(-12,-8)(-12,-3) | 6 | `max_fixations` | 98.712% | 3.938 mm | 13.359 mm | +0.728 mm |

Every other gate passes on every trial. Pitch span 15.0° (gate >=10); yaw span
20.0°; every move one 5° lattice step; no repeats. Selected frontier support
23–69 (gate >=8). Per-patch object measurement coverage **0.9114–0.9503**
(gate >=0.90) — FSG6a's `fix_04` class of miss is gone. Post-seed overlap
11,387–20,222 matched (>=5,000), median 1.97–3.20 mm (<=10), p95 4.77–9.90 mm
(<=25), every replay idempotent, largest coverage decrease 0.00 pp. Coverage gain
60.40–63.53 pp (gate >=35). Maps 76,259–78,092 surfels, all pure instance 121,
32,441–33,215 multi-look (>=5,000).

### All FAIL lines, verbatim

```text
corridor_up_right/1009:  3D frontier policy did not terminate by resolving the frontier
corridor_up_right/1061:  3D frontier policy did not terminate by resolving the frontier
corridor_down_left/1009: 3D frontier policy did not terminate by resolving the frontier
corridor_down_left/1061: 3D frontier policy did not terminate by resolving the frontier
[fsg6d-compare] FSG6D_INCREMENT6_FAIL   trial_passes 0/4
```

### The corridor rule works — it is not what failed

The veto behaved exactly as designed, on real acquisitions, in all four trials.
At the third fixation of every trial the corridor **permitted the diagonal that
the retired FSG6b conjunction would have vetoed**:

```text
up_right  step 2 at (+2,+3) d(+1,+1): corridor 0.7031 allowed  | retired conjunction False
          full edges left=0.4445 right=0.6250 top=0.0000 bottom=0.5629
down_left step 2 at (-2,-3) d(-1,-1): corridor 0.7787 allowed  | retired conjunction False
          full edges left=0.6590 right=0.4543 top=0.5840 bottom=0.0535
```

The top (resp. bottom) edge is 0.0000/0.0535 while the projected frontier exits
through the corner — precisely the FSG6b defect, now correctly resolved. The
trajectory follows the clean diagonal and coverage jumps 74.47% -> 96.97%
(up_right) and 75.52% -> 98.44% (down_left) at that step. Equally, the FSG6c
defect does not recur: **no trial ever steps off the ribbon**, and the corridor
veto is demonstrably active, rejecting 4 of 8 neighbours at the final fixation of
every trial. Legacy full-edge evidence is reported here for diagnosis only and
never entered selection.

### Diagnosis: the 3D frontier never resolves on a thin ribbon

The frontier count does not decay as the surface is completed:

```text
up_right/1009   frontier = [207, 214, 206, 189, 157, 164]   voxels = [446, 646, 868, 1151, 1183, 1197]
down_left/1009  frontier = [195, 215, 189, 177, 151, 163]   voxels = [392, 608, 841, 1076, 1083, 1087]
```

Coverage goes 38.6% -> 99.0% while the frontier population stays at roughly
150–215 throughout. The reason is geometric: `extract_frontier` marks a voxel as
frontier from tangent asymmetry of its in-view neighbourhood, and these ribbons
are only about 6–7 degrees wide across a 12-degree fovea, so **every** fixation
sees long lateral ribbon boundaries that read as frontier no matter how complete
the reconstruction is.

Termination therefore cannot come from the frontier being resolved; it can only
come from the candidate set emptying. Recomputing the exclusion breakdown at the
final fixation of each trial with the runtime functions:

```text
up_right/1009  at (+12,+3) frontier=164: out_of_range 0, visited 2, support<8 0, corridor_veto 4, ELIGIBLE 2
               still eligible (+7,+3) sup=23 corridor=0.4909 | (+7,-2) sup=9 corridor=0.2323
up_right/1061  at (+12,+3) frontier=168: visited 2, corridor_veto 4, ELIGIBLE 2
down_left/1009 at (-12,-3) frontier=163: visited 2, support<8 1, corridor_veto 4, ELIGIBLE 1
               still eligible (-7,-3) sup=31 corridor=0.9208
down_left/1061 at (-12,-3) frontier=165: visited 2, support<8 1, corridor_veto 4, ELIGIBLE 1
```

The survivors are **interior** lattice cells inside the already-swept region —
`(+7,+3)` is the centre of the square bounded by the visited `(2,3)`, `(7,8)`,
`(12,8)`, `(12,3)` — carrying small predicted new area (22.1 and 7.7 deg^2) but
genuine frontier support and a permitted corridor. The policy is not wandering;
it is correctly reporting that a little unreconstructed surface remains. It
simply never runs out within six fixations.

Note that four fixations already suffice numerically: at step 3 coverage is
96.97–98.57% with gain 58.4–63.4 pp, inside every coverage gate. The binding
constraint is that `termination == no_frontier` is effectively unreachable on a
thin ribbon whose frontier population does not decay, under a six-fixation
budget.

**This is a specification result, not an implementation defect.** The code
implements the written FSG6d rule exactly, and the rule does what it promised:
it fixed the diagonal-corner veto without reintroducing one-component licensing.
What fails is the interaction of the **frozen** frontier-extraction termination
behaviour with the **frozen** `no_frontier` gate and the **frozen** six-fixation
budget — none of which FSG6d was permitted to vary. Per §Runtime schedule no code
fix was made and the miss is returned to Luiz/Chat.

### Visuals and PLY

`growth.png` and `growth_truth.png` show both fixtures growing along their
diagonals — `corridor_up_right` 38.6 -> 57.0 -> 74.5 -> 97.0 -> 98.2 -> 99.0%,
`corridor_down_left` 35.2 -> 54.7 -> 75.5 -> 98.4 -> 98.6 -> 98.7% — with the
last two panels of each nearly indistinguishable, the surface being essentially
complete after four looks. `coverage_3d_frontier.png` shows all four curves
rising monotonically and saturating. Every `surface_map.ply` carries
`comment fixed head frame H`, has **no `element face`** (no meshing), and an
independent read gives median cylinder radius **0.74001–0.74005 m against a true
0.740** and **0.70095–0.70096 m against a true 0.700** — sub-millimetre, and the
best radial agreement of any FSG6 increment.

### Cost

Smoke run 17.5 s (loop 17.27 s, Blender 11.89 s) / eval 8.3 s, 78,643,200
samples. Full runs 1m8.5s, 1m8.5s, 1m12.6s, 1m13.1s (loop
68.42/68.38/72.44/72.96 s, Blender 34.7–35.0 s each). Aggregation under a second.
Batch class throughout.

### What holds

The projected candidate-local corridor veto is the first of the four FSG6
continuation rules that is simultaneously eye-symmetric, permissive to a genuine
corner exit, and restrictive against one-component licensing — demonstrated by
check and on all four acquisitions. With it the 3D surfel frontier produced clean
diagonal trajectories reconstructing both fresh ribbons to 98.7–99.0% at
3.46–3.94 mm median with sub-millimetre radial agreement. The open question is no
longer the veto but **termination**: how a frontier defined by local tangent
asymmetry should ever declare a thin ribbon finished.
