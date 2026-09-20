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
