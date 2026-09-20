# fov-3d-vision

A foveated stereo rendering engine for Blender, and the active loop that uses it.

Two eyes on a fixed head, each a Cycles camera that samples the scene on a log-polar warp —
dense at the fovea, coarse in the periphery, 51× fewer rays than a uniform image of the same
field — verged on a point, rendering a pair in 30 ms at the `small` profile and 270 ms at
`full` on an RTX 4090. On top of it, in one command: a stereo field that turns a pair into
inverse depth with an uncertainty everywhere the pair looked, a belief on the head sphere that
fuses the pairs, and a policy that chooses the next fixation from what is known.

    blender -b scenes/classroom/classroom_eye.blend -P tools/active_loop.py -- \
        --out previews/loop/classroom --profile full --policy coverage --fixations 50
    .venv/bin/python tools/active_eval.py previews/loop/classroom

Fifty fixations of the Classroom at `full`: 1.3 G rays, 68–79 s, 92% of a 60° field of regard
measured, 8–9% of it at foveal quality, median inverse-depth error 0.04 /m overall and
0.015–0.019 /m where the fovea has been (10–14 cm at 2.7 m), the vergence for each fixation
taken from the periphery of the ones before. The four-panel figure — posterior depth with the
scanpath, its uncertainty, its error, the curves against rays — is `loop_fig.png` in the run.

The premise: a camera samples uniformly and an eye does not. Foveation is a bandwidth decision
before it is an attention mechanism, so the question is what a controlled, gaze-directed
sampling of a scene costs and what it buys. The answer this repository reached, phase by
phase: at the targets, foveation beats uniform sampling at equal rays at every budget (Phase
A); the disparity a pair yields is flat in the warp's shape at the scale the samples support,
so the cheaper warp wins per ray (Phase B); and in the loop, at equal rays, spreading buys
error and the objective does not — random, coverage-first and expected information end within
12% of each other and target order well behind, on both scenes and both profiles (Phase C).
Coverage-first is the default policy for that reason.

This is the fourth of a sequence: `bioeye` (the loop that ran, on a uniform sensor),
`active-stereo` (the framework, whose loop never ran), `bio-3d-vision` (thirteen experiments
that found coverage was what a loop buys and named the foveated sensor as the untested
form), and this. The summaries are `docs/phase-a-summary.md`, `docs/phase-b-summary.md`,
`docs/phase-c-summary.md`; the reports on the sequence are VISGRAF TR-09-2026 and the
methodology notes it cites.

## What is here

| | tool | what it does |
|---|---|---|
| sensor | `render_foveated.py`, `foveated_camera.osl`, `warp.py` | the log-polar warp as a Cycles camera; `warp.py` is the pure-numpy definition both interpreters import |
| rig | `rig.py`, `fixation_pairs.py` | two eyes at ±ipd/2 on the head's X; a verged pair at a world point; the epipolar frame on the sphere; `PairRenderer` for a session |
| record | `fixation_sequence.py`, `check_pairs.py`, `stereo_truth.py` | the D1 sample record (direction, value, footprint, distance per ray), its checks, and the ground-truth correspondence from the Position pass |
| field | `stereo_field.py` (`stereo_instrument.py` beneath it) | a pair → inverse depth per cell with a two-part variance, at five scales from 0.2° to 3.2°, with left–right consistency |
| loop | `belief.py`, `active_loop.py`, `active_eval.py` | the belief on the head sphere, the policies (targets, random, coverage, info, oracle), the loop in one Blender session, the replay and the figures |
| integration | `integrate_sphere.py`, `preview360.py`, `noise_floor.py` | finest-owns integration of a sequence, the references and the noise floor Phase A judged against |
| views | `sphere_views.py` | (RGB, depth) of a scene as it is and as the engine saw it, equirectangular and on the epipolar sphere, from a loop run and a `preview360` panorama at the eye; the engine's depth drawn by confidence |

Every tool has a check that can fail and most have a control; `--self-test` on the numpy
ones. `DECISIONS.md` holds the nineteen decisions and what would overturn each;
`docs/log.md` the dated record; `docs/<step>.md` one note per step with its Results as the
run left them.

Throughout, the head is fixed. Eyes rotate about their own centres.

## Layout

    CLAUDE.md       how we work
    DECISIONS.md    what is settled, and what would unsettle it
    docs/log.md     dated record of what was run and what came out
    docs/           one note per step; docs/phase-{a,b,c}-summary.md are the phase summaries,
                    docs/phase-a-result.md the result page; docs/reference/ holds baseline images;
                    docs/reviews/ third-party reviews with their reading
    tools/          scripts, all runnable from the repository root; warp.py and rig.py are pure numpy
                (both interpreters import them; each has --self-test)
    scenes/         scene sources; only manifest.json and asset.json are committed
    previews/       generated, gitignored

Nothing a command can rebuild is committed. Scenes and previews are absent by design:
`workshop_8k.exr` alone is 324 MB, and every scene here is either generated by a script or
downloaded by one, pinned by md5 or URL.

## Setup

Blender 5.2.1 LTS on `PATH` as `blender`, plus a small venv for `inspect_preview.py`:

    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

## History — the three phases

### Phase A — monocular

One camera, one centre of projection.

| | Step | State |
|---|---|---|
| A1 | Scene sources: gather and check 3D scenes | **done** — three tiers verified on GPU; `docs/a1-scene-gathering.md` |
| A2 | Reference render at foveal spacing, plus the uniform-cost baseline and the noise floor | **done** — both references at 8192 spp, 32.3 / 35.8 min measured; D7 met on the Classroom, 2-5% short on the calib room; `docs/a2-reference-and-noise-floor.md` |
| A3 | Single foveated image: the warp, first in numpy, then as a Cycles camera | **done** — OSL camera verified on GPU; `docs/a3-foveated-camera.md` |
| A4 | A sequence of fixations | **done** — `fixation_sequence.py` writes the D1 record at 15 ms (small) and 140 ms (full) per fixation; warp, footprint, reader and control checks pass at both profiles, the binned foveal check is registration-limited on the cards; `docs/a4-fixation-sequence.md` |
| A5 | Integration of the sequence into a spherical representation | **done** — finest-owns integration and the D9 curve at both profiles with equal-budget uniform baselines; foveation wins at the targets, uniform over the sphere below the largest budget; `docs/phase-a-result.md` |
| A6 | The E2 and e_max sweep | **done, choice made in D16 (B3)** — at equal rays E2 4 wins the fixated targets and E2 1 the covered sphere; e_max 45 and 30; profiles unchanged (D11); `docs/a6-warp-sweep.md` |

The three warp parameters are settled as far as Phase A can settle them: s₀ is the profile
(0.1° small, 0.05° full), and E₂ = 2°, e_max = 45° stand under D11 after the A6 sweep, which
found that a larger E₂ buys foveal accuracy per ray and a smaller one buys coverage, so the
choice belongs to the objective.

### Phase B — binocular

A second eye at a second fixed centre, plus vergence. With both centres fixed, the baseline
is fixed in the head frame, so the epipolar geometry is constant and rectification is one
change of coordinates on the sphere. Phase A's per-eye spherical maps are already the data
structure this needs.

| | Step | State |
|---|---|---|
| B1 | The second eye on the EYE rig, verged fixation pairs, the foveae-on-target check and its control | **done** 2026-09-15 — `fixation_pairs.py`, `check_pairs.py`, `rig.py`, `warp.py`; D12; results in `docs/b1-verged-pairs.md`: all checks pass on both profiles, (e) within 0.002 spacings, control matches prediction to 3 µm; 29 ms / 271 ms per pair |
| B2 | Ground-truth stereo correspondence from the Position pass, epipolar coordinates on the sphere, the triangulation check and its control; per-eye references | **done** 2026-09-15 — `stereo_truth.py`, `preview360.py --eye-offset`; D13, D14; results in `docs/b2-stereo-truth.md`: (i), (k) at 0.015 s₀, (j) 100%, (h) within 0.006 quanta on both profiles, naive control inf on every card; small per-eye references pinned (full ones not rendered); per-eye (b) 36/35 of 50 against Phase A's 40, wires 6/8 and 5/8 read as lattice phase |
| B3 | The E₂ / e_max sweep with the disparity error as the objective (D11): a reference matcher as an instrument, and the matcher-free information bound beside it | **done** 2026-09-15 — `stereo_instrument.py`, `stereo_sweep.py`; D15; D16 closes D11: E₂ = 2, e_max = 45 as the middle of a flat optimum (instrument 0.272 / 0.269 / 0.261 s₀, bound 0.121 / 0.085 / 0.088 s₀ for E₂ 1 / 2 / 4); `docs/b3-stereo-instrument.md` |

### Phase C — the active loop

Observe a pair, infer depth with an uncertainty everywhere the pair looked, choose the next
fixation from what is known, observe again (D17). The loop lives here, on the Phase B rig and
record; the end of the phase is a foveated stereo rendering engine for Blender that runs it in
one command. bioeye is the model — a running loop and a four-panel figure — and
bio-3d-vision's foreclosures are the prior: coverage is what a loop buys, not looking twice
matters more than the objective.

| | Step | State |
|---|---|---|
| C1 | The stereo field: the D15 instrument extended over the whole disc a pair covers, level by level at the scale the samples support, with left–right consistency and an inverse-depth measurement with variance per cell | **done** — `stereo_field.py`; D17; `docs/c1-stereo-field.md`: (p) −7% at small, −24% at full; floor 0.10–0.37 cells |
| C2 | The loop: `PairRenderer`, a belief on the head sphere (`belief.py`: two variances, gating, the visit map), five policies (targets, random, coverage, info, oracle), one Blender session (`active_loop.py`), bioeye's four panels and the comparison (`active_eval.py`); D18 the evaluation contract | **done** — four runs, `docs/c2-active-loop.md`; (s)–(v) pass on all five at 50 fixations; error: info 0.103 < coverage 0.105 < random 0.111 < targets 0.140 < oracle 0.146 /m; fine coverage: targets 0.201 > coverage 0.138 > random 0.116 > info 0.080 > oracle 0.074 |
| C3 | Closing: the classroom at both profiles, `docs/phase-c-summary.md`, this front page; D19 | **done** — thirteen runs pass every check; on the classroom at `full` random 0.0385 < coverage 0.0427 < info 0.0435 < oracle 0.0453 /m, coverage-first first on fine coverage everywhere but the calib room; `docs/c3-closing.md` |

### Phase D — a reliable multiscale depth from the field

Whether the existing field can be made reliable: find where the gross errors come from,
remove the removable ones, represent the rest (D20, `docs/phase-d-plan.md`).

| | Step | State |
|---|---|---|
| D1a | The diagnosis on the saved records: occluded / window / search / resolution per level, P(gross) against the distance to a depth edge, the parent oracle (what coarse-to-fine could cure) | **run** 2026-09-18 — `gross_diagnosis.py`, `docs/d1-gross-diagnosis.md`; all checks pass on the four records; by area resolution is 75–89% of the bad cells, the oracle cures 3–25% of the wrong peaks at levels 0–2; D20's rule and the order D1b/D2 to be decided |
| D1b | Coarse-to-fine | **not written** (D21): the parent oracle is its ceiling, 16% of the wrong peaks on the classroom at `full`, net harmful at levels 1–2 on the calib room |
| D2a | The judge split (gross = coarse + outlier) re-judged on the saved runs; what tells a wrong peak from a right one (five features, per level); the 3 × 3 window as a what-if | **run** 2026-09-18 — thirteen runs re-judged, (s)–(v) hold, outlier 0.10 of gross 0.31–0.37 on the classroom at `full` (the fine band's gross is all outlier); no feature rejects more than 44.5% of the wrong peaks at 90% kept on the classroom's levels 0–2 (parent the best there, AUC ≤ 0.71); the 3 × 3 window loses on both scenes at every level; D2b to be decided |
| D2b | The neighbour test: a cell's distance from the median parallax of its consistent neighbours, as a sixth feature and as a rejection (`--nb-tol`), offline what-ifs, then the loop once if the offline rule is met | **run** 2026-09-18 — `neighbours` is the best single feature on the classroom at every level (49 / 50 / 44% of the wrong peaks at 90% kept, levels 0–2); as a rejection at one cell it cuts the wrong-peak fraction by 32 / 32 / 23% at levels 0–2 for 2% of the right peaks; **the offline rule is not met** (a third at each level) by `nb1` or `nb1i`, the loop was not run; D2 closes: at one look the outliers cannot be told from the matcher's own evidence; D4 next |
| D4 | The run to saturation (coverage-first, `full`, 500 fixations, read at checkpoints) and, on its record, a second look as the test: repeatability of bad looks, agreement, mean / median / consensus fusion (`second_look.py`); coverage-first continues as least-looked once the cap is covered | **run** 2026-09-18 — 500 fixations in 12.0 min, least-looked from k = 146, 469 distinct directions; fine coverage 0.094 → 0.295, median ρ error flat at 0.039 from K = 200 (twice the fine band's 0.019), gross 0.336 = coarse 0.200 + outlier 0.136; bad looks repeat (P(second bad | first bad) 62% against 11%), consensus fusion 18.3% fine gross against the mean's 27.9% with 9.3% undecided; (z1) fails by 1422 cells the belief's gate dropped (diagnosed, left); record backed up outside the checkout |
| D5 | The consensus belief: a majority among the fine looks of a cell, undecided cells fall back to the coarse stream and are exported; `--fusion consensus` in the loop, `active_eval.py --refuse consensus` re-fuses a record without rendering; D23 | **run** 2026-09-18 — re-fused on D4's record at K = 500: fine outlier 0.206 → 0.171, outlier 0.136 → 0.126, fine coverage 0.295 → 0.263 (undecided 3.2% of the cap), ρ error 0.0387 → 0.0365 (fine 0.0187 → 0.0151), z RMS 1.66 → 1.27; **the rule lands in between** (outlier misses ≤ 0.125 by 0.0007, fine coverage ≥ 0.265 by 0.0025); no live run, `--fusion` stays `mean` by default; Phase D closes |

## State

Phases A, B and C are complete and summarised; Phase C ended 2026-09-17 with the engine
above and the finding that, at equal rays, the policy that does not look twice is as good as
the principled one (D19). Phase D is complete and summarised (`docs/phase-d-summary.md`, D21–D23): three quarters of
what the loop called gross was coarse right peaks inside the variance model; the real outliers
are a tenth of the area, of which about 8% — depth edges and half-occlusions — is the block
matcher's floor at one look; and two looks are a test where one is not, so a consensus among a
cell's fine looks (`--fusion consensus`, an option) takes the fine band's error from 0.0187 to
0.0151 /m on the same 500 fixations. Still open beyond it: the warp as an action, the fixed head, truth beyond what the eyes
sampled.

The scene tooling was first developed in the `visgraf/w3d-scenes` repository and has been
folded in here; see D6 in `DECISIONS.md`.


<!-- FSG1_HANDOFF_20260919 -->
## Foveal Surface Growing - FSG1..FSG5 (opt-in experiment)

| Step | State |
| --- | --- |
| FSG1: single-patch local stereo | **COMPLETE - Increment 1 closed 2026-09-19 (`FSG1H_FINAL_VALIDATION_PASS`).** The FSG1 local RGB-D instrument is `FSG1-HDR-SGBM-one-original-update-original-validity-v1`: fixed soft-HDR encoding -> unchanged SGBM -> exactly one original photometric refinement update -> original validity predicate (no endpoint or footprint support vetoes). Validated prospectively on fresh fixtures and fresh seeds 101/149 (Blender 5.2.1, OPTIX, 2,516,582,400 primary camera samples) against gates frozen before the data existed: four disparity-phase planes at 22.00/22.25/22.50/22.75 px cover 99.77-99.97% at 0.085-0.226% median and 0.284-0.959% p95; occluder foregrounds 100.000% coverage; occluded backgrounds 93.2-95.2% (the tightest margin) at <=0.405% median and <=1.638% p95; boundary accuracy gates pass with ~4,000 accepted points each at <=0.330% median and <=2.052% p95; and **0 accepted points in all 11,592 singly-visible occlusion-core pixels**, 0 wrong-instance acceptances. Route there: FSG1b traced the original coverage miss to over-exposure, FSG1c fixed the encoding, FSG1d failed prospectively and first exercised half-occlusion, FSG1e showed the error tail was the +/-0.75 px refinement cap on near-integer phase, FSG1f narrowed the candidate, FSG1g stopped on a fixture defect (occluder edges outside the +/-6 deg core) which FSG1h corrected. Scope: one local patch under controlled opaque, diffuse, planar, calibrated conditions with oracle segmentation - no claim about arbitrary scenes, complete boundaries (~40% of boundary reference stays unaccepted), thin structure or calibrated uncertainty. Increment 2 is now complete; see the FSG2 row below. See `docs/fsg1h-final-validation.md` and the FSG1 document chain. |
| FSG2: two-patch surface fusion (Increment 2) | **COMPLETE 2026-09-19 (`FSG2_INCREMENT2_PASS`).** Two prescribed overlapping foveal patches (fixations yaw -3 and +3 deg) from the frozen FSG1 instrument accumulate into one persistent surface in the fixed head frame, with exact calibrated poses and **no registration, ICP, meshing or hole filling**. One full seed-211 acquisition (419,430,400 primary camera samples). Every prospective gate met: patch coverage 99.1% / 100.0%; 32,222 B points matched and 50.8% still new; matched A/B distance 1.907 mm median / 6.187 mm p95; fused point-to-true-plane 3.548 mm median / 9.740 mm p95; fixed-grid coverage **59.7% -> 90.2%**, a 30.5 pp gain; idempotent replay. The map holds 91,941 surfels, 16,860 with two-look support, containing only object ID 61. Scope: one finite planar tilted object under oracle segmentation, two fixations, one seed, and a prospectively fixed 12 mm Euclidean association rule - an engineering baseline, not a final surface model; folds, self-occlusion and calibrated uncertainty are deferred. Increment 3 is now complete; see the FSG3 row below. See `docs/fsg2-increment2.md`. |
| FSG3: active frontier growth (Increment 3) | **COMPLETE 2026-09-19 (`FSG3_INCREMENT3_PASS`).** A truth-free frontier policy, given one seed fixation, chose its own subsequent fixations from the evolving persistent map plus the current oracle segmentation frontier, and **stopped by itself at the visible object boundary**. One full seed-307 active run (1,048,576,000 primary camera samples): the policy produced 5 fixations at yaw -7, -2, +3, +8, +13 deg, every saccade exactly +5 deg, no repeat, terminating on `no_frontier` - the map's right extent reached +14.632 deg against the fixture's analytic +15.190 deg edge. Surface coverage grew **33.6% -> 100.0%** (+20.99/+20.18/+19.97/+5.24 pp, no step losing coverage) at **4.219 mm median** point-to-plane error (p95 13.587 mm); 92,632 surfels with support histogram {1: 39,551, 2: 47,660, 3: 5,421}; per-patch oracle coverage 94.1-96.7%; overlaps 25,720-26,608 matched at 1.8-2.0 mm median, all idempotent; every map point ID 71. The loop and policy were verified to import no fixture geometry and open no `evaluation_only` asset. Scope: **feasibility, not optimality - no competing gaze policy was evaluated**; one opaque diffuse planar tilted rectangle, oracle segmentation, horizontal saccades only, fixed 2.10 m vergence, one seed. Folds, self-occlusion, multi-object switching, head motion, vergence control and calibrated uncertainty remain open. See `docs/fsg3-increment3.md`. |
| FSG4: active vs fixed scan (Increment 4) | **COMPLETE - Increment 4 closed 2026-09-19 (`FSG4C_INCREMENT4_PASS`).** On two fresh opaque planar placements (`case_c`/`case_d`) x two fresh seeds (503/557), with exactly paired observations and equal-or-lower logical camera budget, the frozen frontier policy acquired visible surface more efficiently than the one frozen nonadaptive scan `0,-5,+5,-10,+10`: **AUC wins 4/4**, mean AUC advantage **0.1702**, mean final-coverage advantage **0.2218**, active reaching **100.0%** final coverage in all four against the scan's 73.3-82.3%. The policy found opposite directions on the mirrored placements unaided (case_c 0,-5,-10,-15; case_d 0,+5,+10,+15,+20; both `no_frontier`). Map quality holds for both policies (plane medians 4.31-4.52 mm, p95 13.59-14.81 mm, every map pure ID 81, every fusion idempotent); active received no cache, proven by newly-rendered equalling logical samples. Route there: FSG4a stopped at the paired-noise gate (OptiX renders are not bit-reproducible); FSG4b restored exact pairing by reusing the active acquisition artifact **without relaxing the gate** and won 4/4, but formally FAILED on an inherited per-fixation terminal rule that is unsatisfiable once 98.7% is already covered - that FAIL is preserved; FSG4c made per-fixation novelty/gain descriptive (residual closure was 100.0% at every terminal fixation) and revalidated on fresh fixtures and seeds. **The correction was not load-bearing: the terminal numbers would have passed the retired rules anyway.** Scope: not policy optimality, not a population estimate, one comparison scan, oracle segmentation, horizontal saccades, fixed 2.10 m vergence. **The next experiment is authorized but NOT implemented.** See `docs/fsg4-increment4.md`, `docs/fsg4b-pairing-reuse.md`, `docs/fsg4c-increment4.md`. |
| FSG5: curved-surface growth (Increment 5) | **COMPLETE - Increment 5 closed 2026-09-20 (`FSG5_INCREMENT5_PASS`, 4/4 trials).** A curvature stress test: geometry changed, intelligence did not. With the **frozen FSG1 instrument, the unchanged `fsg4_policy` and the unchanged `fsg3_surface_map` 12 mm Euclidean fusion** - no new policy, no registration, no ICP, no meshing, no hole filling - the active loop grew a convex cylindrical ribbon (radius 0.75 m, 75 deg arc) to **~100% curved-surface completeness** at **3.36-3.65 mm median** and 10.77-11.31 mm p95 point-to-surface error, on both mirror orientations and both fresh seeds (601/647), 4,194,304,000 primary camera samples. The policy produced the mirrored trajectory on the mirrored fixture **unaided** (curve_right -7,-2,+3,+8,+13; curve_left +7,+2,-3,-8,-13), all terminating `no_frontier`. The curvature-specific gate passed in the safe direction: **signed radial median +1.25 to +1.34 mm** on 54.5-55.4k multi-look surfels against a +/-7.5 mm limit - positive, so the feared inward contraction under Euclidean fusion did **not** occur; an independent check of the exported clouds gives median radius 0.75075-0.75097 m against a true 0.750 m. Every map pure ID 81, every replay idempotent. Scope: two mirrored ribbons of ONE radius and arc, two seeds, oracle segmentation, exact poses, horizontal saccades, fixed vergence - not general curvature, varying radius, concave or saddle geometry, self-occlusion, folds or multi-object scenes. The policy is still a 2D image-edge/map-yaw controller; a true 3D surface-frontier controller is the clean next question and was deliberately not built. **The next experiment is authorized but NOT implemented.** See `docs/fsg5-increment5.md`. |

Oracle object IDs, RGB-derived geometry, fixed head/cyclopean map frame. Direct
perspective patch acquisition, not a change to the Phase C/D OSL sensor or loop.
Increment 2 added two-patch accumulation into that fixed map, Increment 3 an
active frontier policy that selects and stops its own fixations, Increment 4 the
paired efficiency comparison against a fixed scan, and Increment 5 a curvature
stress test on a convex cylindrical ribbon. Increments 1-5 are closed. No
registration, meshing, multi-object switching, head motion or vergence control is
enabled, and the policy remains a 2D image-edge/map-yaw controller.
