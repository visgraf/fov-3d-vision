# Reality Check 1 — good enough for an ordinary static scene?

## Question

After FSG6f and the failed Stage-II Scene-1a/1b/1c sequence, the immediate question is no longer whether another scheduler can be invented.  It is whether the existing single-object mechanism is already useful on geometry and texture that are less laboratory-like.

Reality Check 1 therefore asks one deliberately pragmatic question:

> Does the frozen FSG6f mechanism produce a recognisable, metrically sane active reconstruction of one moderately irregular, mixed-texture target in a small cluttered static scene?

This is a **reality check, not a benchmark**.  It is not adversarial and it does not attempt to establish worst-case robustness.

## Frozen assumptions

- fixed head;
- static scene;
- frozen FSG1 local stereo instrument;
- frozen FSG3 12 mm surface fusion;
- frozen FSG6f frontier/state/consensus/corridor/ranking policy, imported directly;
- frozen six-fixation object budget;
- oracle target-instance segmentation remains allowed;
- no head motion, object discovery, learned policy, ICP, meshing or hole filling.

## Scene

The target is a shallow hanging cloth/poster-like surface, approximately 0.90 m × 0.64 m at the validated ~2.1 m range.  Its depth varies non-periodically by about 8 cm across the visible surface.  It is represented by 120 rendered triangles rather than by a plane or a constant-radius cylinder.

The target texture is intentionally **mixed rather than uniformly rich**: a broad low-contrast region, a modest printed band/emblem, subtle fabric variation and a small repetitive weave region.  The surrounding scene contains a table, wall and two unrelated side props with their own textures.  The target is not deliberately occluded.

The scene remains opaque and diffuse because Reality Check 1 is meant to change as little as possible at once.  Specularity, strong shadows, thin structure and adversarial materials are later reality checks if this one is promising.

## Schedule

Two fresh stochastic seeds are frozen prospectively: 2111 and 2179.  Both begin from the same prescribed seed fixation `(-6°, -4°)` and then hand control entirely to the unchanged FSG6f policy for at most six physical fixations.

Develop on `small`; report each seed once at `full`.

## What is gated

Only structural integrity is gated:

- prediction never imports/open evaluator truth;
- map contains only the target instance;
- every fused patch replays idempotently;
- no physical fixation repeats;
- FSG6f is imported rather than copied/reimplemented;
- the six-look budget and 12 mm fusion rule remain unchanged.

## What is deliberately *not* gated

No new coverage, error, overlap, measurement-fraction or termination threshold decides PASS/FAIL.  The following are reported descriptively:

- visible-surface coverage by fixation;
- approximate point-to-surface median and P95 distance;
- overlap consistency;
- target measurement support;
- multi-look surfels;
- fixation trajectory and termination reason;
- variation between the two render seeds;
- RGB fixation previews, map growth and PLY.

The outcome is `REALITY1_OBSERVATION_COMPLETE` if the run is structurally valid.  Luiz/Chat then decide whether the behaviour is **good enough** to justify the next practical step.  Numerical misses are evidence, not an invitation to tune this record.

## Results

Run on the workstation 2026-09-21 (Blender 5.2.1 LTS headless, Cycles, OPTIX on
RTX 4090, driver 595.84; host-side scripts under `.venv/bin/python` 3.12.3 per
the working agreement).  Each seed was acquired **once** at `full`.  Status:
**`REALITY1_COMPLETE`** - both records are structurally valid.

### Provenance audited before acquisition

HEAD `46d9699`, clean, on `main`.  `git diff --name-status HEAD~1 HEAD` is
exactly nine files, all `A` (additions).  `git diff HEAD~1` restricted to every
FSG1/FSG3/FSG6f source, `rig.py`, `bl_common.py` and the pins is **empty**,
confirmed additionally by per-file sha256 against the pre-install parent
`ed851ef`: `fsg_stereo_supported` 683ae91eaca7b6af, `fsg_stereo_hdr`
67e2ec4667bcc179, `fsg_stereo` faebf0f1b3acbfde, `fsg_evaluate`
a5134b8d8537714d, `fsg_geometry` d9537d8ebc23b60c, `fsg3_surface_map`
1b9dbeb873105ec9, `fsg6f_public` c79f58c9b51f33d4, `fsg6f_frontier`
d636c9405d719916 - all SAME.

`reality1_run.py` imports `fsg6f_frontier as policy` and calls
`policy.choose_next(...)` at a single site; it does **not** import
`reality1_scene`, opens no `evaluation_only` asset, and defines none of FSG6f's
frontier extraction, state classifier, consensus, corridor or ranking.
`FUSION` {0.012, 0.012}, `MAX_FIXATIONS` 6 and `INSTRUMENT_ID` are measurably
equal to `fsg6f_public`.  Both prediction manifests record the same
`public_spec_sha256` **baa71ce4b0ae8e36bc0ccf80addad1c0e0e02ec76d7bc8369c37e4258c528f22**.

### Checks

`[reality1-scene] PASS {"bounds_deg": [-12.5409, 12.9278, -8.4808, 10.6397],
"depth_range_m": 0.08711, "target_triangles": 120, "texture":
{"dynamic_range": 0.3475, "feature_region_std": 0.11710, "low_panel_std":
0.010764, "whole_std": 0.078158}}` -
the target really is non-planar (8.7 cm), really is 120 triangles, and the
texture really is mixed: the low-contrast panel's standard deviation (0.0108) is
**an order of magnitude below** the printed feature region's (0.1171).

`[reality1-policy] PASS frozen_fsg6f=true quality_gated=false fixed_head=true
static_scene=true`, `[reality1-check] SUMMARY passed=6 failed=0`.  All six
negatives exit 1 for their intended reasons: `flat`, `uniformrich`,
`policycopy`, `truth`, `qualitygate`, `budgetbump`.  All twenty-four prior
suites green after the code fixes (`fsg`, `fsg2`, `fsg3`, `fsg4`, `fsg4c`,
`fsg5`, `fsg6`, `fsg6b`-`fsg6f`, `fsg7a`, `fsg_hdr`, `fsg_supported`,
`fsg_validation`, `fsg_final_validation`, `fsg_finalh_validation`,
`fsg_coverage_audit`, `fsg_failure_audit`, `scene1a`, `scene1b`, `scene1c`,
`reality1`).

### Smoke (seed 2111, `small`, run once)

`REALITY1_OBSERVATION_COMPLETE`, `integrity_fails: []`; 78,643,200 samples,
26.2 s run + 16.2 s eval.  Coverage 0.2565 -> 0.5276, approximate surface median
17.597 mm / P95 46.199 mm, measurement fraction min 0.8589, worst overlap median
5.96 mm, 5,609 multi-look surfels, termination `max_fixations`.  Its six gazes
`(-6,-4) (-1,-9) (4,-9) (9,-9) (14,-4) (14,1)` are **identical** to the full
seed-2111 run's: on this seed the trajectory is profile-independent.  Nothing
was changed in response to the smoke.

### Full runs, each acquired once

| | seed 2111 | seed 2179 |
|---|---|---|
| status | `REALITY1_OBSERVATION_COMPLETE` | `REALITY1_OBSERVATION_COMPLETE` |
| `integrity_fails` | `[]` | `[]` |
| fixations / termination | 6 / `max_fixations` | 6 / `max_fixations` |
| gazes (deg) | (-6,-4) (-1,-9) (4,-9) (9,-9) (14,-4) (14,1) | (-6,-4) (-1,1) (4,6) (9,11) (14,11) (14,6) |
| visible coverage, seed -> final | 0.2603 -> **0.5345** (+0.2742) | 0.2604 -> **0.7329** (+0.4725) |
| coverage by fixation | 0.2603, 0.3273, 0.4000, 0.4267, 0.4764, 0.5345 | 0.2604, 0.5141, 0.6745, 0.7034, **0.7034**, 0.7329 |
| approx surface median / P95 | **6.188 mm** / 19.812 mm | **5.720 mm** / 18.106 mm |
| measurement fraction min / median | 0.8516 / 0.8740 | 0.8400 / 0.8750 |
| worst overlap median / P95 | 3.025 mm / 8.534 mm | 2.897 mm / 8.670 mm |
| map points | 78,656 | 113,874 |
| multi-look surfels (support >= 2) | 21,927 (27.9%) | 27,660 (24.3%) |
| per-patch points | 37910, 21414, 24440, 18538, 14057, 18628 | 37855, 61772, 47763, 16166, **6128**, 14161 |
| per-patch measurement fraction | .8582 .9061 .9091 .8826 .8516 .8655 | .8570 .9426 .9278 .8931 .8400 .8471 |
| new-point fraction per fusion | 1.000 .491 .442 .219 .501 .448 | 1.000 .660 .544 .257 **.001** .365 |
| primary camera samples | 1,258,291,200 | 1,258,291,200 |
| wall (run / eval) | 78.6 s / 62.3 s (Blender 52.46 s) | 84.0 s / 94.0 s (Blender 51.30 s) |

Aggregate, `previews/reality1/comparison/comparison.json`:
**`[reality1-compare] REALITY1_COMPLETE`**, `integrity_fails: []`,
`quality_gated: false`, `same_trajectory: false`, final coverage range
[0.5345, 0.7329] with an absolute seed difference of **0.1984**, surface median
range [5.720, 6.188] mm, P95 range [18.106, 19.812] mm, fixation counts [6, 6],
terminations ["max_fixations", "max_fixations"].

### Structural integrity, re-verified independently of the evaluator

Both records: `truth_opened` **False**; `fixed_head` and `static_scene`
**True**; final map instance ids exactly **{141}**; **every** fused patch
`idempotent_replay` **True**; **6 of 6 gazes unique**, no physical fixation
repeated; `frozen_object_policy`
`FSG6f-candidate-frontier-consensus-v1` and `instrument`
`FSG1-HDR-SGBM-one-original-update-original-validity-v1`; budget 6 and fusion
{0.012, 0.012} unchanged.  **No FAIL line was produced anywhere in either run.**

### Descriptive observations - reported, not gated

- **Neither seed terminated `no_frontier`.**  Both exhausted the six-look budget
  still reporting `continue`, the same mode five of Scene-1c's twelve controls
  showed.
- **The two seeds diverge completely after the prescribed seed fixation.**  From
  the identical `(-6,-4)` start, 2111's first autonomous move is `(1,-1)`
  (down-right) and 2179's is `(1,+1)` (up-right); the trajectories never
  reconverge.  The two runs differ **only** in Monte-Carlo render seed - same
  scene, same policy, same budget - and end 19.8 coverage points apart.  This is
  the same seed-sensitivity Scene-1c's object 203 showed.
- **Seed 2179's fifth fixation was nearly wasted.**  At `(14,11)` the target
  fills only the lower-left corner of the view: 6,128 points, new-point fraction
  **0.001**, and visible coverage unchanged at 0.7034 -> 0.7034.
- **Measurement fraction never reached the calibration-like values.**  The
  minimum is 0.8400-0.8516 and the median 0.8740-0.8750 - consistent with the
  deliberately broad low-contrast panel, which the FSG1 matcher has little to
  lock onto.
- **Overlap consistency is millimetric and better than on the calibration
  fixtures**: worst per-fusion overlap medians 2.897-3.025 mm across every
  fusion of both runs.
- **The point-to-surface medians, 5.72 and 6.19 mm, sit inside the 4.3-6.6 mm
  band every earlier FSG6/Scene increment produced** - the non-periodic 8.4 cm
  target did not inflate them.

### Visual reading (part of the report; explicitly NOT a PASS criterion)

RGB fixation previews (`previews/reality1/full-seed*/rgb/fix_**_left.png`).
`fix_00` is almost featureless: a cream cloth with faint horizontal fabric
banding against a grey wall, which is exactly the "broad low-contrast region"
the fixture was built to contain.  Seed 2111's `fix_02` at `(4,-9)` brings in
the printed blue band and a red-orange emblem with the brown tabletop below;
`fix_04` at `(14,-4)` catches the cloth's right edge, the wall and a brown side
prop.  Seed 2179's `fix_04` at `(14,11)` is mostly wall, which is the visual
counterpart of that step's 0.001 new-point fraction.

Map growth (`growth.png`, `growth_truth.png`).  Both runs build the map as six
roughly rectangular foveal patches tiled edge to edge with real overlap, not as
scattered fragments.  Seed 2111 traces an **L**: a band across the lower half of
the target, then a column up the right edge, leaving the whole upper-left and
upper-middle unvisited - which is where its 53.5% comes from.  Seed 2179 traces
a **diagonal staircase** from lower-left to upper-right with heavier patch
overlap, reaching 73.3%.

Surface map (`surface_map.ply` / `.npz`).  Sliced into thin horizontal bands
(+/-12 mm in y) and plotted against the exported truth mesh profile, the
reconstructed points **follow the true non-periodic undulation closely wherever
points exist**, with a few-millimetre scatter about the curve and no band where
the cloud departs from the surface.  The central 98% of reconstructed depths -
2.083-2.158 m for 2111 and 2.083-2.167 m for 2179 - coincides with the true
target depth span **2.083-2.166 m**; the full extents, 2.056-2.201 m and
2.059-2.198 m, are a thin outlier tail of a few centimetres.  Colouring seed
2179's map by depth shows coherent large-scale shape - a near region across the
top and a far valley through the middle - that reads as the cloth's fold rather
than as noise.  Patch seams are faintly visible as discontinuities in the depth
colouring, but the measured disagreement across them is 2.4-3.0 mm.

**In plain terms: the reconstruction is recognisable as the hanging cloth, it is
coherent rather than fragmented, it is in the right place at the right depth,
and it has no gross wrong-depth region.  Its visible deficiency is
incompleteness - half to three-quarters of the visible surface in six looks,
with the remainder simply never visited - plus a thin few-centimetre outlier
tail.  Whether that is good enough is Luiz/Chat's decision, not this record's.**

### Code fixes

Three, all implementation defects, each diagnosed before being changed; no
scientific or numerical behaviour, constant, fixture, threshold or gate was
touched.

1. **`tools/dev/check_reality1.py`** imported three `tools/` modules without
   putting `tools/` on `sys.path` and never imported `sys`, so the check crashed
   with `ModuleNotFoundError: No module named 'reality1_public'` - and, worse,
   **the six negatives were exiting 1 only because of that crash**, making them
   false passes rather than controls; fixed by adding `import sys` and the
   `sys.path.insert(0, str(TOOLS))` that every sibling check already has, after
   which `passed=6 failed=0` and each negative fails for its own stated reason.
2. **`tools/reality1_public.py`** `render_seed` returned
   `1_000_000 * seed + ...`, which for schedule seed **2179** is 2,179,000,420
   at minimum - above Blender's signed-32-bit Cycles seed limit 2,147,483,647 -
   so **every** gaze on the lattice under seed 2179 raised
   `ValueError: CyclesRenderSettings.seed value not in 'int' range` and seed 2179
   could never render its first fixation; fixed by folding the result into the
   non-negative int32 range with `& 0x7FFF_FFFF`, which is **the identity over
   the whole of seed 2111's domain** (max 2,111,550,421) and so leaves the
   already-acquired seed-2111 record and the `public_spec_sha256` unchanged.
   Every previous experiment's schedule seeds were <= 1901 and so never reached
   the limit.
3. **`tools/dev/check_reality1.py`** gained the check that would have caught (2)
   before acquisition, per "every tool ships a check that can fail": every
   scheduled render seed must lie in [0, 2^31-1] and no two may collide.
   Verified fail-capable - restoring the pre-fix formula makes it raise
   `render seed 2179050100 outside the Cycles signed-32-bit range`.

The crashed seed-2179 attempt is preserved at
`previews/reality1/full-seed2179-crashed-int32seed/` with its Blender log.  The
frozen schedule seeds 2111 and 2179, the seed gaze, budget, policy, vergence,
fusion, scene, texture and every numerical constant are untouched; no alternate
seed was used and nothing was rerendered after a numerical result.
