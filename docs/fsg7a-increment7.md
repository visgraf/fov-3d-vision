# FSG7a — prescribed head motion reveals self-occluded surface

## Status before acquisition

**Prospective. No scientific acquisition has been run by Chat.** Increment 6 is closed at FSG6f. FSG7a opens Increment 7 with one deliberately narrow question.

## Physics first

A true self-occluded surface cannot become visible merely because the eyes rotate. With a fixed pair of eye centres, changing fixation changes which rays receive high-resolution sampling but does not change line-of-sight visibility of a world point. Repository decision D3 anticipated this explicitly: head motion is a new phase/question.

Therefore FSG7a changes one physical assumption only: the binocular rig translates laterally while its orientation stays fixed. The surface map remains in the **initial head frame H0**. The head motion is prescribed; there is no new motion policy yet.

## Research question

> Can the frozen FSG1 local stereo instrument, followed by exact-pose transport into H0 and the frozen 12 mm FSG3/FSG4 fusion rule, reconstruct a surface continuation that is binocularly self-occluded at H0 and becomes visible only after a prescribed lateral head translation?

A PASS establishes the measurement and mapping substrate needed for active hidden-surface discovery. It does **not** establish that the observer can choose the head motion. That is the next question.

## Frozen components

- FSG1 instrument: `FSG1-HDR-SGBM-one-original-update-original-validity-v1`.
- FSG3/FSG4 fusion: 12 mm association radius and 12 mm hash cell.
- IPD, profile, SPP and 2.10 m prescribed vergence.
- Oracle instance segmentation remains object identity only.
- No ICP, mesh reconstruction, hole filling or registration optimization.

## New component

Two acquisition head frames Ht have the same orientation as H0 but different origins. Stereo reconstruction is produced in the local Ht frame by the unchanged instrument and transported exactly to H0 before fusion:

\[
\mathbf x_{H0}=\mathbf x_{Ht}+\mathbf t_{H0}.
\]

The rendered world does **not** move with the head.

## Fixtures

Two fresh connected folded ribbons use one public object instance ID:

- `fold_right`: a front panel at z = -2.50 m with a return wing folding backward from its right edge;
- `fold_left`: the mirrored physical fold on the left.

The front panel is 0.36 m wide by 0.30 m high. The return wing is 0.65 m deep by 0.30 m high. Both panels share the same rendered instance ID; evaluator-only part labels distinguish front versus return for measurement.

At H0, direct evaluator geometry gives **0.0000 return visibility in both eyes** on both fixtures. After the prescribed ±0.45 m lateral head translation, direct geometry gives **1.0000 visibility in both eyes**. These are design checks, not experimental results.

## Prescribed views

Each trial has exactly two binocular acquisitions:

- step 0: H0, gaze (0°, 0°), front seed;
- step 1: translate +0.45 m for `fold_right` / -0.45 m for `fold_left`, gaze ∓5.5° yaw, 0° pitch, revealing the return wing.

Fresh seeds: 1409 and 1453. Four full trials total.

## Prospective decision rule

A full trial passes only if all of the following pass:

- each patch object measurement coverage >= 90%;
- reveal patch has >= 5,000 fixed-H0 overlap matches;
- reveal overlap median <= 10 mm and P95 <= 25 mm;
- reveal replay is idempotent;
- final map contains only object instance 151;
- >= 5,000 final surfels have support >= 2;
- final folded-surface median error <= 10 mm and P95 <= 30 mm;
- seed front-wing coverage >= 80%;
- seed return-wing coverage <= 5%;
- final return-wing coverage >= 80%;
- return-wing coverage gain >= 75 percentage points;
- final whole-object coverage >= 90%;
- evaluator direct visibility confirms fixed-head return visibility <= 2% and moved-head binocular visibility >= 95%.

FSG7a passes only if all **4/4** fresh full trials pass. If not, preserve the failure and stop.

## What a PASS means

A PASS supports only this claim:

> Exact known head translation can reveal a genuinely self-occluded continuation and the existing local stereo/fusion stack can place the newly visible measurements coherently into persistent H0 memory without ICP.

It does not yet support active head-motion selection, occlusion classification by the controller, learned gaze, multiple objects, or free six-degree-of-freedom motion.

## Results

Run 2026-09-20 on the workstation. HEAD before `bebf23b`, working tree clean,
`3fe2864` confirmed an ancestor (`git merge-base --is-ancestor` exit 0).

**Final status: `FSG7A_HEAD_MOTION_FEASIBILITY_FAIL` — 0 of 4 full trials passed.
Every trial failed on exactly one gate, and it is the same gate in all four:
`final map median folded-surface error` (12.62–12.98 mm against a <=10 mm limit).
The miss is preserved and FSG7a feasibility is NOT closed.**

**The head-motion mechanism itself worked on every trial.** Return-wing coverage
went from 4.73–4.97% at the H0 seed to 87.49–96.20% after the prescribed lateral
translation, a gain of 82.75–91.36 percentage points, and the newly visible
measurements landed in persistent H0 memory with 2.545–2.830 mm median overlap
against the seed map. What failed is a systematic depth bias on the **front**
panel, diagnosed below as the frozen FSG1 instrument's own documented sub-pixel
behaviour rather than anything FSG7a introduced.

### Preservation and frozen source

`git diff 3fe2864` over the FSG1 stereo modules (`fsg_stereo_supported`,
`fsg_stereo_hdr`, `fsg_stereo`, `fsg_evaluate`, `fsg_geometry`, `fsg_scene`,
`fsg_validation_render`), `fsg3_surface_map.py`, **all FSG6, FSG6b, FSG6c, FSG6d,
FSG6e and FSG6f modules**, `rig.py`, `bl_common.py` and `requirements-fsg.txt` is
empty. No prior decision block was edited. `fsg7a_run.py` imports neither
`fsg7a_scene` nor any `evaluation_only` asset and calls `compute_once` behind
`check_kernel_equivalence`. Every manifest records `truth_opened: false`,
`policy: "none; prescribed two-view head-motion feasibility"` and empty
`policy_inputs`.

The head origin is moved through `fsg_geometry.make_calibration(...,
head_origin_w=...)`, a keyword that **already existed in the frozen module** with
default `HEAD_ORIGIN_W` and is already consumed by the frozen render path — so no
instrument change was needed to move the head.

Environment: Python 3.12.3, NumPy 2.2.6, OpenCV 4.13.0, Pillow 12.3.0, Blender
5.2.1 LTS, Cycles OPTIX on an NVIDIA GeForce RTX 4090. Per CLAUDE.md's
two-interpreter rule, all host-side tools were run on `.venv/bin/python`; the
checks were additionally confirmed identical under the bare `python` on PATH.

### Checks

```text
[fsg7a-motion] PASS h0_ht_roundtrip=true moving_frame_negative_m=0.451
[fsg7a-scene] fold_right hidden_LR=0.0000/0.0000 revealed_LR=1.0000/1.0000
[fsg7a-scene] fold_left hidden_LR=0.0000/0.0000 revealed_LR=1.0000/1.0000
[fsg7a-scene] PASS self_occlusion=true head_translation_reveals=true fixed_head_gaze_cannot_reveal=true
[fsg7a-check] SUMMARY passed=7 failed=0
```

All six negatives exited 1. All twenty prior regression suites stayed green,
including `[fsg6f-check] SUMMARY passed=14 failed=0`.

### Direct evaluator return visibility

```text
fold_right  FIXED HEAD  L=0.0000 R=0.0000  (gate either_max <= 0.02)
fold_right  MOVED HEAD  L=1.0000 R=1.0000  (gate both_min  >= 0.95)   t=[+0.45,0,0]
fold_left   FIXED HEAD  L=0.0000 R=0.0000
fold_left   MOVED HEAD  L=1.0000 R=1.0000                              t=[-0.45,0,0]
```

The return wing is exactly invisible to both eyes at H0 and exactly visible to
both after translation, on both fixtures. This gate passed on every trial.

### Frame-transport integrity

Measured on the saved per-patch arrays: `x_H0 - x_Ht` equals the prescribed
translation to `max|delta - t| = 1.49e-08` (float32 storage of 0.45), exactly
zero at the seed. The renderer recorded the correct translation at every step and
the scene stayed fixed in H0. The seed map spans z in [-2.623, -2.446]; after the
reveal the map extends to z = -3.025, i.e. deep along a return wing that runs from
z = -2.50 back to z = -3.15 — the head motion genuinely added surface that did
not exist in the seed map.

### Smoke — COMPLETED, exit 2 (numerical only)

`fold_right` / 1409 / small, 2.74 s run / 1.10 s eval, 26,214,400 samples.
Return coverage 0.0000 at seed -> 0.4776 after motion; reveal overlap 5.368 mm
median / 11.074 mm P95, idempotent. FAIL lines: final map median folded-surface
error; final map p95 folded-surface error; too few multi-look surfels; head
motion failed to reconstruct hidden return; hidden return coverage gain too
small; final folded-object coverage; fix_00 object measurement coverage; fix_01
object measurement coverage; reveal patch too few fixed-frame overlap matches.
All resolution-scaled. No runtime exception, provenance failure, truth leak,
frame-transform failure, wrong scene motion or orchestration defect — so full
acquisition was not blocked.

### The four full trials

Each run exactly once at `--profile full`, 419,430,400 samples each
(1,677,721,600 total). Two acquisitions per trial.

| Trial | Views (translation, gaze) | Patch cov. | Reveal matched/new | Overlap med/P95 | Return seed→final (gain) | Whole | Median | P95 |
|---|---|---|---:|---|---|---:|---:|---:|
| fold_right/1409 | (0,0,0)·(0,0) ; (+0.45,0,0)·(-5.5,0) | 0.9208 / 0.9357 | 19054 / 2732 | 2.545 / 7.037 mm | 0.0473→0.8749 (+0.8275) | 0.9193 | 12.941 mm | 21.810 mm |
| fold_right/1453 | (0,0,0)·(0,0) ; (+0.45,0,0)·(-5.5,0) | 0.9208 / 0.9358 | 19058 / 2732 | 2.548 / 7.069 mm | 0.0477→0.8774 (+0.8297) | 0.9209 | 12.983 mm | 21.777 mm |
| fold_left/1409 | (0,0,0)·(0,0) ; (-0.45,0,0)·(+5.5,0) | 0.9208 / 0.9317 | 14923 / 3283 | 2.818 / 7.741 mm | 0.0484→0.9620 (+0.9136) | 0.9755 | 12.683 mm | 21.253 mm |
| fold_left/1453 | (0,0,0)·(0,0) ; (-0.45,0,0)·(+5.5,0) | 0.9208 / 0.9315 | 14943 / 3259 | 2.830 / 7.702 mm | 0.0497→0.9602 (+0.9105) | 0.9743 | 12.624 mm | 21.132 mm |

Front-wing coverage 0.9987–1.0000 at seed and 1.0000 final on all four. Every
reveal replay idempotent. Maps 26,392–26,943 points, all pure instance 151, with
6,789–9,672 surfels at support >=2. Support histograms
{1: 16720, 2: 9672}, {1: 16825, 2: 9567}, {1: 20154, 2: 6789}, {1: 20110, 2: 6809}.
Wall: runs 10.86 s, 11.03 s, 9.46 s, 9.44 s (loop 10.71/10.86/9.35/9.29 s, Blender
3.38–3.42 s); evals 4.15 s, 4.03 s, 4.30 s, 4.36 s; comparison under a second.

**Every gate passed on every trial except the final median.** Patch coverage
>=0.90 ✓ (0.9208–0.9358); reveal matches >=5,000 ✓ (14,923–19,058); overlap
median <=10 mm ✓ and P95 <=25 mm ✓; idempotent ✓; instance purity ✓; supported
surfels >=5,000 ✓; P95 <=30 mm ✓ (21.1–21.8); seed front >=80% ✓; seed return
<=5% ✓ (4.73–4.97%); final return >=80% ✓; return gain >=75 pp ✓; whole-object
>=90% ✓; visibility gates ✓.

### All FAIL lines, verbatim

```text
fold_right/1409:  final map median folded-surface error
fold_right/1453:  final map median folded-surface error
fold_left/1409:   final map median folded-surface error
fold_left/1453:   final map median folded-surface error
[fsg7a-compare] FSG7A_HEAD_MOTION_FEASIBILITY_FAIL
  fold_right/1409 moving-head run failed
  fold_right/1453 moving-head run failed
  fold_left/1409 moving-head run failed
  fold_left/1453 moving-head run failed
  trial_passes 0 | mean_final_coverage 0.947515 | mean_return_coverage 0.918624
```

### Diagnosis: a front-panel depth bias, not a head-motion or transport failure

Splitting the final map by which panel each surfel is nearest:

```text
fold_right/1409  overall median 12.941 mm
   nearest FRONT   n=23520 (89.1%)  median 13.808 mm  P95 22.325 mm
   nearest RETURN  n= 2872 (10.9%)  median  1.600 mm  P95 11.892 mm
   FRONT signed z offset from the z=-2.500 plane : median -13.741 mm (mean -13.607)
   RETURN signed x offset from the x=+0.180 plane: median  -0.983 mm (mean  -2.061)
fold_left/1409   overall median 12.683 mm
   nearest FRONT   n=23431 (87.0%)  median 13.686 mm  P95 21.864 mm
   nearest RETURN  n= 3512 (13.0%)  median  2.334 mm  P95 11.391 mm
   FRONT signed z offset: median -13.664 mm | RETURN signed x offset: median +1.435 mm
```

**The return wing — the surface FSG7a is about — is reconstructed accurately
(1.6–2.3 mm median).** The error is a uniform 13.7 mm depth offset on the front
panel, which carries 87–89% of the surfels and therefore sets the median.

That offset is the frozen instrument's known sub-pixel behaviour. With baseline
0.0630 m and f = 1217.8 px (256-px core over 12 degrees), the front panel at
Z = 2.50 m has nominal disparity 30.690 px, and a +13.74 mm depth offset implies a
disparity bias of **-0.1687 px** — within 7% of the **-0.1579 px SGBM bias FSG1
measured and recorded** in its step diagnostic. The fixture sits 0.40 m *beyond*
the prescribed 2.10 m vergence, further than any previous FSG target, so the same
fixed sub-pixel bias produces a larger metric offset than in earlier increments.

The return wing escapes it for a geometric reason that also confirms the account:
the front panel's normal is +z, so a depth offset moves points **off** it, while
the return wing's normal is ±x, so the same depth offset slides points **along**
it. `scene._rect_distance` reflects exactly that — front clips (x,y) and fixes z;
return clips (y,z) and fixes x.

Applying a **single global +13.74 mm z correction** to every surfel — as a
diagnostic only, not a change to any tool — brings the folded-surface error to
3.776 mm median / 11.333 mm P95 (`fold_right`) and 3.663 mm / 10.808 mm
(`fold_left`), both far inside the 10/30 mm gates.

**This is a specification/measurement result, not an implementation defect.** The
code faithfully implements the written experiment: the transport is exact to
1.5e-08, the scene stays fixed, the schedule and visibility gates all pass, and
the head motion does reveal the hidden return. Correcting the bias would mean
changing the frozen FSG1 instrument or the 2.10 m vergence, both of which this
handoff forbids. Nothing was tuned, nothing rerendered.

### Visuals and PLY

`growth.png` is a top-down (x,z) view and shows the result directly: at the H0
seed only a flat front panel, and after translation an **"L"** whose return leg
extends backward in z — surface that was absent one panel earlier.
`growth_truth.png` reports front 100.0% / return 87.5% for `fold_right`/1409.
`fold_left` mirrors it. Every `surface_map.ply` carries
`comment fixed initial head frame H0`, has **no `element face`** (no meshing), and
26,392–26,943 vertices.

### Code fixes

**None.** No source file was modified; this increment changed documentation only.

### Outcome

Per the prospective decision rule, FSG7a required 4/4. It is **0/4**, so the miss
is preserved and **FSG7a feasibility is not closed**. Active head-motion
selection remains not implemented and is untouched by this result.

What the run does establish, short of the gate: prescribed lateral head
translation reveals a genuinely binocularly self-occluded continuation
(0.0000 -> 1.0000 direct visibility, 4.7% -> 87–96% reconstructed coverage), and
exact-pose transport into H0 places those newly visible measurements into the
frozen 12 mm fusion coherently, at 2.5–2.8 mm median overlap with the seed map
and with idempotent replay — without ICP or any registration optimization. The
single failing gate is a front-panel depth bias inherited from the frozen stereo
instrument at a working distance 0.40 m beyond its prescribed vergence.
