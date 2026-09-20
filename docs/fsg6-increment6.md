# FSG6 / Increment 6 — the reconstructed surface becomes the frontier

## Decision to record before acquisition

`D-FSG6a — Replace the image-edge controller with a truth-free 3D surfel frontier.`

Increment 5 established that the closed FSG1 local RGB-D instrument and the
existing 12 mm head-frame surfel fusion can grow a substantially curved convex
surface without ICP, meshing or a surface model. Increment 6 changes **the
frontier representation, not the measurement instrument or fusion**.

Keep the frozen FSG1 instrument and existing `tools/fsg3_surface_map.py` exactly
unchanged. Replace the horizontal FSG4 image-edge/map-yaw controller by a
truth-free controller whose candidate directions must be supported by boundary
asymmetry in the persistent **3D surfel map**. Oracle segmentation is still
available, but only as a current-view object-continuation veto: it may say that a
surface frontier is actually a resolved object boundary; it may not create the
frontier score or reveal fixture geometry.

The scientific question is:

> Can a frontier extracted from the reconstructed 3D surface itself drive a
> two-dimensional gaze trajectory that grows a curved surface which a
> horizontal-only controller cannot cover?

A full pass closes Increment 6 and authorizes — but does not implement — the
next experiment. A miss is preserved and returned to Luiz/Chat. Code may fix
only a demonstrated implementation/orchestration defect; it may not change the
stereo instrument, FSG3 fusion, frontier algorithm/constants, geometry, texture,
seeds, SPP, vergence, coverage radius or numerical gates to obtain a pass.

## What remains frozen

- `FSG1-HDR-SGBM-one-original-update-original-validity-v1`.
- Existing `tools/fsg3_surface_map.py` and its 12 mm Euclidean association/hash.
- Fixed head/cyclopean map frame H; exact eye/head geometry; no ICP.
- Oracle object membership only; truth geometry remains post-hoc evaluator data.
- Fixed 2.10 m vergence.
- Full profile at repository-default 256 spp; small/64 spp for smoke only.
- No mesh reconstruction, hole fill, learned policy or surface fitting.
- Per-fixation novelty/coverage gain remains descriptive rather than gated.

`fsg6_run.py` and `fsg6_frontier.py` must not import `fsg6_scene` or open any
`evaluation_only` asset.

## The 3D frontier policy

The persistent surfels are downsampled to 25 mm voxels. Around each voxel
centroid, neighbours within 65 mm define a local covariance. The smallest PCA
eigenvector estimates the local normal. Mean neighbour offset is projected into
the tangent plane; an interior surfel is approximately balanced, while a
surface-boundary surfel has a one-sided tangent neighbourhood. The missing
surface direction is the negative projected mean.

Only frontier surfels currently near the foveal view participate in the next
local saccade. Candidate gazes occupy the eight neighbouring cells of a 5-degree
yaw/pitch lattice. A candidate must:

1. stay inside the frozen yaw/pitch limits and not revisit a fixation;
2. be permitted by current oracle segmentation on every nonzero movement
   component edge (a diagonal requires both corresponding edges to continue);
3. be supported by at least eight 3D frontier surfels whose missing tangent
   directions agree with that gaze direction.

Among eligible candidates, the controller selects the gaze whose 12-by-12 degree
foveal footprint adds the largest area outside the robust yaw/pitch bounding box
of the persistent 3D map; the 3D frontier score is the tie-breaker. Thus the
mask can veto a resolved physical edge, but **persistent reconstructed geometry
is what makes and ranks the frontier candidates**.

The software check gives the identical all-edge object mask to two different 3D
map states and requires opposite diagonal gaze decisions. A controller that
ignores the map cannot pass that check.

## Fresh diagonal curved fixtures

Both fixtures are finite cylindrical ribbons with radius 0.75 m, local cylinder
centre z=-2.80 m, 110 degrees of arc and 0.20 m width. The whole ribbon is rigidly
rolled in the head image plane:

- `diag_up_right`: +35 degrees roll; seed gaze yaw/pitch `(-8,-8)` degrees.
- `diag_down_left`: +215 degrees roll, the exact image-plane mirror; seed `(8,8)`.

Rendering uses 48 quad strips; the prospective chord-error check requires <0.2
mm against the continuous cylinder. Fresh seeds are **701** and **743**.

The analytic design check is intentionally asymmetric with respect to controller
class: a plausible four-look diagonal trace covers >97% of the truth surface,
whereas even a five-look horizontal-only scan along the correct yaw direction
covers <65%. These are fixture-construction estimates, not experimental results
and not trajectory acceptance criteria.

## Prospective gates

Every one of the four full fixture/seed trials must pass independently.

### Acquisition and 3D gaze

- 4–6 fixations;
- termination reason `no_frontier`;
- no repeated fixation;
- every move changes yaw and/or pitch by exactly one 5-degree lattice component,
  with neither component exceeding 5 degrees;
- total visited pitch span >=10 degrees (a horizontal-only controller fails);
- every patch has >=100 oracle object reference pixels and >=90% valid object
  measurement coverage.

### 3D frontier provenance

Every nonterminal selected gaze must have at least eight agreeing 3D frontier
surfels, as recorded in `policy_trace.json`. Truth geometry is not available to
the host loop.

### Overlap and persistent map

For every post-seed patch:

- >=5,000 matched measurements;
- overlap median <=10 mm;
- overlap P95 <=25 mm;
- duplicate replay exactly idempotent;
- truth coverage may not drop by >0.5 percentage points.

### Final curved geometry

- analytic finite-cylinder point-to-surface median <=10 mm;
- P95 <=30 mm;
- final curved-surface coverage >=90%;
- coverage gain over seed >=35 percentage points;
- map contains only object instance 91;
- >=5,000 surfels have support from >=2 distinct fixations;
- absolute median signed radial error on those multi-look surfels <=7.5 mm.

## Schedule

1. Record `D-FSG6a` and a prospective `docs/log.md` entry.
2. Run the FSG6 positive checks and seven expected-failing negatives.
3. Run all existing FSG1–FSG5 regression checks unchanged.
4. Run one diagnostic small trial: `diag_up_right`, seed 701. Numerical exit 2
   is diagnostic; integrity/provenance/runtime failure stops the experiment.
5. If integrity is sound, run exactly once all four full trials:
   - `diag_up_right` / 701
   - `diag_up_right` / 743
   - `diag_down_left` / 701
   - `diag_down_left` / 743
6. Evaluate each and aggregate exactly those four with `fsg6_compare.py`.
7. Inspect each `growth.png`, `growth_truth.png`, `surface_map.ply`, policy trace,
   and aggregate `coverage_3d_frontier.png`.
8. No rerender after a numerical miss and no alternate frontier threshold,
   neighbourhood, step, fixture, seed, radius, vergence or gate.

Suggested roots are under `previews/fsg6/` with `smoke-...`, `full-...`, and
`full-comparison` names matching the commands below.

## Exact new commands

```bash
.venv/bin/python tools/dev/check_fsg6.py
for n in policy mapstate horizontal flat shift bias purity; do
  .venv/bin/python tools/dev/check_fsg6.py --negative "$n"; test $? -eq 1 || exit 1
done
```

Run all existing FSG1–FSG5 regression checks exactly as recorded in
`docs/log.md`; every existing summary must remain green.

Smoke:

```bash
.venv/bin/python tools/fsg6_run.py --out previews/fsg6/smoke-diag_up_right-seed701 --profile small --fixture diag_up_right --seed 701 --device OPTIX
.venv/bin/python tools/fsg6_eval.py previews/fsg6/smoke-diag_up_right-seed701 --out previews/fsg6/smoke-diag_up_right-seed701-evaluation --mode smoke
```

Full:

```bash
.venv/bin/python tools/fsg6_run.py --out previews/fsg6/full-diag_up_right-seed701 --profile full --fixture diag_up_right --seed 701 --device OPTIX
.venv/bin/python tools/fsg6_eval.py previews/fsg6/full-diag_up_right-seed701 --out previews/fsg6/full-diag_up_right-seed701-evaluation --mode full
.venv/bin/python tools/fsg6_run.py --out previews/fsg6/full-diag_up_right-seed743 --profile full --fixture diag_up_right --seed 743 --device OPTIX
.venv/bin/python tools/fsg6_eval.py previews/fsg6/full-diag_up_right-seed743 --out previews/fsg6/full-diag_up_right-seed743-evaluation --mode full
.venv/bin/python tools/fsg6_run.py --out previews/fsg6/full-diag_down_left-seed701 --profile full --fixture diag_down_left --seed 701 --device OPTIX
.venv/bin/python tools/fsg6_eval.py previews/fsg6/full-diag_down_left-seed701 --out previews/fsg6/full-diag_down_left-seed701-evaluation --mode full
.venv/bin/python tools/fsg6_run.py --out previews/fsg6/full-diag_down_left-seed743 --profile full --fixture diag_down_left --seed 743 --device OPTIX
.venv/bin/python tools/fsg6_eval.py previews/fsg6/full-diag_down_left-seed743 --out previews/fsg6/full-diag_down_left-seed743-evaluation --mode full
.venv/bin/python tools/fsg6_compare.py \
  previews/fsg6/full-diag_up_right-seed701-evaluation/metrics.json \
  previews/fsg6/full-diag_up_right-seed743-evaluation/metrics.json \
  previews/fsg6/full-diag_down_left-seed701-evaluation/metrics.json \
  previews/fsg6/full-diag_down_left-seed743-evaluation/metrics.json \
  --out previews/fsg6/full-comparison
```

A completed full run may exit 2 numerically; preserve it and continue the other
predeclared full runs. Stop early only on an integrity/provenance/runtime error.

## What Code must report

Return one paste block containing:

- HEAD before/after, branch/push and proof `3d5125c` is an ancestor;
- frozen-source diff for the FSG1 instrument, `fsg3_surface_map.py`, rig,
  `bl_common.py` and pins;
- Python/NumPy/OpenCV/Pillow, Blender and GPU backend;
- FSG6 check summary, all seven negative FAIL lines and all prior regression
  summaries;
- small smoke status and every FAIL line;
- each full trajectory as `(yaw,pitch)`, every policy decision's 3D frontier
  count / selected support / predicted new angular area and termination reason;
- per-patch measurement coverage; every overlap matched count/median/P95 and
  idempotence; coverage curve and gain over seed;
- final map points/support histogram, analytic curved-surface median/P95,
  multi-look signed radial median, purity, yaw span and pitch span;
- all full FAIL lines verbatim;
- visual and PLY observations; samples and wall times;
- aggregate comparison status/ranges;
- every code fix, or explicitly none;
- final status exactly `FSG6_INCREMENT6_PASS` or `FSG6_INCREMENT6_FAIL`.

If PASS: close Increment 6 and authorize, but do not implement, the next
experiment. If FAIL: preserve the miss and stop for Luiz/Chat.

## Results

Run 2026-09-20 on the workstation. HEAD before `6b7190d`, working tree clean,
`3d5125c` confirmed an ancestor (`git merge-base --is-ancestor` exit 0).

**Final status: `FSG6_INCREMENT6_FAIL` — 2 of 4 full trials passed.** The miss is
preserved. Increment 6 is NOT closed and no next experiment is authorized.

### Frozen source and environment

`git diff 3d5125c` over `fsg_stereo_supported.py`, `fsg_stereo_hdr.py`,
`fsg_stereo.py`, `fsg_evaluate.py`, `fsg_geometry.py`, `fsg3_surface_map.py`,
`rig.py`, `bl_common.py` and `requirements-fsg.txt` is **empty**. `fsg6_run.py`
imports the existing `fsg3_surface_map` and calls `compute_once` behind
`check_kernel_equivalence`; neither `fsg6_run.py` nor `fsg6_frontier.py` imports
`fsg6_scene` or opens any `evaluation_only` asset. Every
`prediction_manifest.json` records `truth_opened: false`.

Python 3.12.3, NumPy 2.2.6, OpenCV 4.13.0, Pillow 12.3.0, Blender 5.2.1 LTS,
Cycles OPTIX on an NVIDIA GeForce RTX 4090.

### Checks

`[fsg6-check] SUMMARY passed=7 failed=0`, with
`[fsg6-scene] PASS up_right=[-13.309,13.309]x[-10.210,10.210] horizontal_ideal_max=0.412 chord_max_mm=0.150`
and `[fsg6-frontier] PASS map_state_changes_2d_direction=true resolved_boundary_stops=true`.
All seven negatives exited 1 with their intended FAIL lines. All thirteen
FSG1–FSG5 regression suites remained green (24, 29, 34, 48, 37, 46, 7, 8, 4, 5,
7, 7, 6 passed, 0 failed).

### One code fix

`tools/fsg6_run.py` line 64 referenced an undefined name `z` in the loop's
defensive revisit guard (`np.allclose(g,z,...)`). `z` is never assigned, never a
parameter and never imported; the guard compares the gaze **about to be
acquired** against the history, and the variable holding it is `gaze`. At step 0
`gazes` is empty so the generator short-circuits, but every step ≥ 1 raised
`NameError`, which made the written 4–6 fixation algorithm impossible to run.
Changed `z` → `gaze`, one token. No constant, threshold, gate or specification
changed; the guard becomes functional rather than crashing, and is strictly
stricter afterwards. The crashed partial smoke is preserved at
`previews/fsg6/smoke-diag_up_right-seed701-crashed-nameerror-preserved`.

### Small smoke (diagnostic, exit 2)

`diag_up_right` / 701 / small: 6 fixations
`(-8,-8) (-3,-3) (2,2) (7,2) (12,7) (7,7)`, `max_fixations`, final curved-surface
coverage 87.57%, median 13.836 mm, p95 33.814 mm, signed radial −4.821 mm.
FAILs: final median, final p95, termination, object measurement coverage on all
six patches (0.796–0.863 against ≥0.90), too few overlap matches on fix_01–04
(2,795–5,532 against ≥5,000), final coverage. Every miss is resolution-scaled —
overlap **quality** passed throughout (median 3.83–4.79 mm, p95 8.01–10.67 mm)
and every replay was idempotent. No exception, so full was not blocked.

### The four full trials

Each run exactly once at `--profile full`, 1,258,291,200 primary camera samples
each (5,033,164,800 total).

| Trial | Trajectory (yaw,pitch) | Termination | Final cov. | Median | P95 | Signed radial | Status |
|---|---|---|---:|---:|---:|---:|---|
| up_right/701 | (-8,-8) (-3,-3) (2,2) (7,2) (12,7) (7,7) | `max_fixations` | 99.139% | 4.041 mm | 12.784 mm | +1.687 mm | **FAIL** |
| up_right/743 | (-8,-8) (-3,-3) (2,2) (7,2) (12,7) (7,7) | `max_fixations` | 99.207% | 4.055 mm | 12.844 mm | +1.645 mm | **FAIL** |
| down_left/701 | (8,8) (3,3) (-2,-2) (-7,-7) (-2,-7) (-7,-2) | `no_frontier` | 99.091% | 4.643 mm | 14.436 mm | +1.419 mm | PASS |
| down_left/743 | (8,8) (3,3) (-2,-2) (-7,-7) (-2,-7) (-7,-2) | `no_frontier` | 99.121% | 4.639 mm | 14.446 mm | +1.431 mm | PASS |

Yaw span 20° (up_right) and 15° (down_left); **pitch span 15.0° in all four**
against the ≥10° gate, so the 3D controller did move in two dimensions on every
trial. Every move was exactly one 5-degree lattice component; no fixation was
repeated. Nonterminal selected 3D frontier support 21–93 surfels against the ≥8
gate, never close to the limit. Coverage gain over seed 59.3–61.8 pp (gate ≥35).
Post-seed overlap: 13,322–25,927 matched (gate ≥5,000), median 1.76–2.59 mm
(≤10), p95 5.35–8.20 mm (≤25), every replay idempotent, largest coverage
decrease 0.01 pp (tolerance 0.5 pp). Maps 62,334–63,758 surfels, all pure
instance 91, 31,689–34,780 with multi-look support (gate ≥5,000).

### All full FAIL lines, verbatim

```text
diag_up_right/701: 3D frontier policy did not terminate by resolving the frontier
diag_up_right/701: fix_04 object measurement coverage
diag_up_right/743: 3D frontier policy did not terminate by resolving the frontier
diag_up_right/743: fix_04 object measurement coverage
[fsg6-compare] FSG6_INCREMENT6_FAIL
  diag_up_right/701 3D-frontier run failed
  diag_up_right/743 3D-frontier run failed
```

### Diagnosis: the mirror pair is not a monocular mirror

The two fixtures are an exact 180-degree image-plane rotation of one another as
**geometry** — `up_right L` and the 180-degree rotation of `down_left R` agree on
**0 of 409,600 pixels disagreeing, IoU 1.000000**, and so do `up_right R` against
rotated `down_left L`. But a 180-degree roll about the gaze axis maps the head
frame by (x,y,z) → (−x,−y,z), which **swaps the two eye centres** (±0.0315 m
along X). The mirror of the left eye's view is therefore the *right* eye's view,
not the left one's. The FSG6 controller reads only the left-eye oracle mask, so
the two "mirrored" fixtures present it with genuinely different images, differing
by the full binocular parallax: **37.4 px (1.76°) on a ribbon only 119 px (5.59°)
wide**, a 31% shift of the ribbon's width. Measured directly, `up_right L` vs
rotated `down_left L` disagree on 16.43% of core pixels, IoU 0.732.

That difference is amplified by the continuation veto, which thresholds the
object fraction in a 10-row edge band at 0.15. Across the three comparable
mirrored fixations the mirrored edge fraction is systematically **0.136–0.143
lower** on `up_right`, and at the third fixation it crosses the threshold:

```text
step 0  up_right@(-8,-8) top=0.3914  vs  down_left@(+8,+8) bottom=0.5340  delta=-0.1426
step 1  up_right@(-3,-3) top=0.2391  vs  down_left@(+3,+3) bottom=0.3820  delta=-0.1430
step 2  up_right@(+2,+2) top=0.0703  vs  down_left@(-2,-2) bottom=0.2066  delta=-0.1363
                         ^ < 0.15, vetoed                  ^ >= 0.15, permitted
```

`raw_support_L` is 100% true in both bands, so the stereo support mask plays no
part; the asymmetry is entirely in the oracle mask the veto consults. The
consequence is mechanical: on `up_right` the (+5,+5) diagonal is removed from the
candidate set at fixation 3, the controller is deflected onto the pure-yaw
(+7,+2), and it then needs (+12,+7) and (+7,+7) to finish. It reaches 99.1%
coverage but still has two eligible candidates at fixation 6, so the budget
ends the run as `max_fixations` instead of `no_frontier`. The same deflection
places fixation 4 at (+12,+7), where the fovea hangs off the ribbon end and
object measurement coverage is 0.8940 — a 0.60 pp miss of the ≥0.90 gate. Both
`up_right` FAIL lines are downstream of that single vetoed diagonal.
`down_left` keeps all four edges live at its third fixation, runs the clean
diagonal to (−7,−7), reaches 99.07% by fixation 4 and terminates `no_frontier`.

This is a **fixture/rig design property, not an implementation defect and not a
numerical accident**: it reproduced identically on both seeds, with byte-identical
oracle reference counts, because the oracle mask is ray-traced and seed-independent.
Repairing it would require changing the fixture design, the reference eye, or the
`edge_object_fraction_min` constant — none of which §5 delegates to Code — so the
miss is preserved and returned to Luiz/Chat.

### Visuals and PLY

`growth.png` for `up_right` shows a diagonal ribbon growing from lower-left to
upper-right; `down_left` grows upper-right to lower-left, the mirror direction,
confirming the controller found opposite directions unaided. `growth_truth.png`
gives 37.4 → 55.7 → 74.9 → 93.3 → 99.1 → 99.1% for `up_right` (panels 4 and 5
visually indistinguishable — the last look adds 0.04 pp) and 39.8 → 59.0 → 80.7 →
99.1 → 99.1 → 99.1% for `down_left`, saturating a fixation earlier.
`coverage_3d_frontier.png` shows all four curves rising monotonically to ~99.1%.
Each `surface_map.ply` carries `comment fixed head frame H`, has **no `element
face`** — no meshing anywhere — and an independent read of the exported clouds
gives median cylinder radius **0.75110–0.75120 m against a true 0.750 m**, i.e.
~1.1–1.2 mm outward, matching the signed radial medians and reproducing FSG5's
finding that 12 mm Euclidean fusion does not contract a curved surface inward.

### Cost

Smoke run 17.4 s / eval 6.9 s; full runs 1m14.2s, 1m15.5s, 1m16.7s, 1m16.1s;
full evaluations ~37 s each; aggregation under a second. Batch class throughout.

### Scope of what did hold

On all four trials the 3D surfel frontier drove a genuinely two-dimensional
trajectory (pitch span 15.0°) that grew a rolled cylindrical ribbon to ~99.1%
curved-surface completeness at 4.04–4.64 mm median error, which the software
check confirms a five-look horizontal-only scan cannot do on this fixture
(ideal coverage 0.412). The frontier representation works. What failed is the
interaction between the oracle continuation veto and a mirror pair that is not a
mirror monocularly.
