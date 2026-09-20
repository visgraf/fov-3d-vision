# FSG6c / Increment 6 — candidate-aligned continuation for the 3D surface frontier

## Decision to record before acquisition

`D-FSG6c — Preserve the FSG6 3D surfel frontier and the FSG6b binocular repair; replace only the diagonal component-conjunction veto with candidate-aligned forward-perimeter continuation.`

FSG6a and FSG6b remain **formal FAILS** and their records/results must remain untouched. FSG6a established that the persistent 3D surfel frontier can drive genuinely two-dimensional gaze, but exposed a left-eye-only continuation asymmetry. FSG6b repaired that eye asymmetry with binocular `max(f_L,f_R)` evidence, but fresh validation exposed a second, independent defect: a diagonal candidate required BOTH component edges to show continuation. A rolled ribbon can leave the current foveal core through the forward perimeter (for example high on the right edge) without ever touching the top edge. The old `top AND right` rule therefore vetoed a geometrically valid up-right move and consumed the six-fixation budget on a detour.

The accepted one-token `z -> gaze` repair in `tools/fsg6_run.py` remains an implementation fix. The FSG6b eye-symmetric evidence remains accepted. FSG6c is additive; do not rewrite FSG6a or FSG6b.

The scientific question is:

> Does the unchanged truth-free 3D surfel frontier close Increment 6 when the segmentation-only physical-boundary veto is aligned with the proposed 2D candidate direction rather than decomposed into conjunctive axis tests?

## The only policy change

Per-eye directional edge fractions are computed exactly as in FSG6b and remain combined symmetrically:

`f(edge) = max(f_L(edge), f_R(edge))`.

For a candidate lattice direction `d=(dx,dy)`, define the forward-compatible perimeter edges from its nonzero components. Examples:

- right: `{right}`
- up: `{top}`
- up-right: `{right, top}`
- down-left: `{left, bottom}`

The candidate continuation evidence is

`f_cont(d) = max( f(edge) for edge in forward-compatible edges(d) )`

and the candidate is permitted iff

`f_cont(d) >= 0.15`.

The **0.15 threshold is unchanged**. Axis-aligned behavior is therefore identical to FSG6b. Only diagonal semantics change: continuation through either direction-compatible exit edge is sufficient. The retired FSG6a/FSG6b rule used `all(...)` over the two component edges.

The persistent 3D surfel map still creates and ranks frontier candidates. Segmentation cannot create or score a frontier; it remains only a physical-boundary veto. The rule remains exactly invariant to `L <-> R`.

## Design/runtime semantics are now shared

FSG6b's fixture construction check used a bare angular box and therefore certified a four-look diagonal path that its own runtime veto could later forbid. FSG6c removes that inconsistency.

`fsg6c_scene.py` contains an evaluator-only preflight that:

1. intersects the **continuous analytic cylinder** with the two frozen eye models;
2. sends the resulting raw oracle masks through the repository's actual stereo rectification maps and core crop;
3. computes the same calibration-derived support masks used by the runtime;
4. calls the exact `fsg6c_frontier.directional_continuation_evidence()` function used by the host policy.

The preflight does not prescribe the runtime trajectory. It only proves that the fresh construction is reachable under the actual continuation semantics before any Blender acquisition is run.

A deliberately load-bearing fresh control is frozen: on `corner_up_right` at gaze `(2,+3)` the intended `(+5,+5)` transition must have right-edge continuation above 0.15 while top-edge continuation remains below 0.15. The new candidate-aligned rule must permit the move, while the retired component conjunction must reject it. If that property drifts, checks fail before acquisition.

## Frozen pieces

Unchanged from FSG6b:

- `FSG1-HDR-SGBM-one-original-update-original-validity-v1`;
- existing `tools/fsg3_surface_map.py`, 12 mm association/hash and idempotent replay;
- fixed head frame H and exact eye/head geometry; no ICP;
- fixed 2.10 m vergence;
- full profile 256 spp, small profile 64 spp for smoke only;
- 25 mm frontier voxels, 65 mm neighbourhood, PCA tangent frontier, 0.18 asymmetry minimum, 0.12 m lookahead;
- eight neighbouring 5-degree yaw/pitch candidate moves;
- minimum 8 agreeing 3D frontier surfels;
- **0.15** edge-object continuation threshold;
- all FSG6b measurement, overlap, map-quality, coverage, pitch-span and radial-bias gates;
- no meshing, hole filling, learned policy or fitted surface model.

`check_fsg6c.py` requires exact equality of FSG6c `SURFACE_FRONTIER` constants and `TARGETS` with FSG6b; any hidden threshold/gate drift fails before acquisition.

## Fresh, non-mirror validation fixtures

FSG6a/FSG6b full records are development evidence and are not reused as validation.

FSG6c uses two new diagonal cylindrical ribbons that are deliberately not exact mirror copies:

- `corner_up_right`: centre z = -2.90 m, radius 0.76 m, theta -60 to +54 degrees, height 0.245 m, roll +33 degrees, seed gaze `(-8,-7)` degrees, texture tag 61.
- `corner_down_left`: centre z = -2.75 m, radius 0.72 m, theta -52 to +62 degrees, height 0.235 m, roll +216 degrees, seed gaze `(+8,+7)` degrees, texture tag 67.

Both render with 48 strips and are evaluated against continuous analytic cylinders. The check requires max strip chord error <0.2 mm. Fresh Monte-Carlo seeds are **907** and **953**.

Construction checks (not experimental results):

- `corner_up_right` angular bounds are about yaw [-13.79,+13.35], pitch [-10.19,+9.95] degrees;
- `corner_down_left` about yaw [-13.60,+12.89], pitch [-10.82,+10.38] degrees;
- a five-look horizontal-only controller covers at most about 48.0% of this fixture family;
- geometry-only four-look diagonal traces cover about 99.6% and 99.1%;
- every transition in those construction traces is also permitted by the exact runtime continuation semantics in the analytic rectified-mask preflight;
- the `corner_up_right` critical diagonal is specifically permitted by FSG6c and rejected by the retired FSG6b conjunction.

No actual trajectory is prescribed. The measured policy may choose any valid 3D-frontier path.

## Prospective gates

Every one of the four full fixture/seed trials must pass independently.

### Acquisition and 3D gaze

- 4–6 fixations;
- termination reason `no_frontier`;
- no repeated fixation;
- each move is one 5-degree yaw/pitch lattice move;
- visited pitch span >=10 degrees;
- every patch has >=100 oracle object reference pixels and >=90% valid object measurement coverage.

### 3D frontier provenance

Every nonterminal selected gaze has >=8 agreeing 3D frontier surfels. The policy trace must record both per-eye directional edge fractions, the binocular per-edge combination, and the selected candidate's candidate-aligned continuation record (`compatible_edges`, per-edge fractions, combined fraction, threshold, allowed). Truth remains unavailable to the host loop.

### Overlap and persistent map

Each post-seed patch:

- >=5,000 matched measurements;
- overlap median <=10 mm;
- overlap P95 <=25 mm;
- exact duplicate replay idempotence;
- truth coverage may not drop by more than 0.5 percentage points.

### Final curved geometry

- analytic point-to-surface median <=10 mm;
- P95 <=30 mm;
- final coverage >=90%;
- coverage gain over seed >=35 percentage points;
- only object instance 111 in the map;
- >=5,000 surfels with support >=2;
- absolute median signed radial error on those surfels <=7.5 mm.

## Schedule

1. Record `D-FSG6c` and a prospective `docs/log.md` entry **before acquisition**. Preserve both earlier FAIL records and results.
2. Run the FSG6c positive checks and all nine expected-failing negatives.
3. Run the existing FSG1 through FSG6b regression checks unchanged.
4. Run one diagnostic small trial: `corner_up_right`, seed 907. Numerical exit 2 is diagnostic; integrity/provenance/runtime failure stops the experiment.
5. If integrity is sound, run exactly once all four full trials: both fixtures x seeds 907/953.
6. Evaluate each and aggregate exactly those four with `fsg6c_compare.py`.
7. Inspect `growth.png`, `growth_truth.png`, every `surface_map.ply`, policy traces and aggregate `coverage_3d_frontier.png`.
8. No rerender after a numerical miss and no threshold, fixture, seed, SPP, vergence, fusion, frontier or gate change.

A completed full run may exit 2 numerically; preserve it and continue the other predeclared full trials. Stop early only on integrity/provenance/runtime failure.

## Exact FSG6c commands

```bash
.venv/bin/python tools/dev/check_fsg6c.py
for n in policy mapstate horizontal monocular conjunction flat shift bias purity; do
  .venv/bin/python tools/dev/check_fsg6c.py --negative "$n"; test $? -eq 1 || exit 1
done
```

Run the existing regression checks exactly as recorded in `docs/log.md`, including `check_fsg6.py` and `check_fsg6b.py`; every prior summary must remain green.

Smoke:

```bash
.venv/bin/python tools/fsg6c_run.py --out previews/fsg6c/smoke-corner_up_right-seed907 --profile small --fixture corner_up_right --seed 907 --device OPTIX
.venv/bin/python tools/fsg6c_eval.py previews/fsg6c/smoke-corner_up_right-seed907 --out previews/fsg6c/smoke-corner_up_right-seed907-evaluation --mode smoke
```

Full:

```bash
.venv/bin/python tools/fsg6c_run.py --out previews/fsg6c/full-corner_up_right-seed907 --profile full --fixture corner_up_right --seed 907 --device OPTIX
.venv/bin/python tools/fsg6c_eval.py previews/fsg6c/full-corner_up_right-seed907 --out previews/fsg6c/full-corner_up_right-seed907-evaluation --mode full
.venv/bin/python tools/fsg6c_run.py --out previews/fsg6c/full-corner_up_right-seed953 --profile full --fixture corner_up_right --seed 953 --device OPTIX
.venv/bin/python tools/fsg6c_eval.py previews/fsg6c/full-corner_up_right-seed953 --out previews/fsg6c/full-corner_up_right-seed953-evaluation --mode full
.venv/bin/python tools/fsg6c_run.py --out previews/fsg6c/full-corner_down_left-seed907 --profile full --fixture corner_down_left --seed 907 --device OPTIX
.venv/bin/python tools/fsg6c_eval.py previews/fsg6c/full-corner_down_left-seed907 --out previews/fsg6c/full-corner_down_left-seed907-evaluation --mode full
.venv/bin/python tools/fsg6c_run.py --out previews/fsg6c/full-corner_down_left-seed953 --profile full --fixture corner_down_left --seed 953 --device OPTIX
.venv/bin/python tools/fsg6c_eval.py previews/fsg6c/full-corner_down_left-seed953 --out previews/fsg6c/full-corner_down_left-seed953-evaluation --mode full
.venv/bin/python tools/fsg6c_compare.py \
  previews/fsg6c/full-corner_up_right-seed907-evaluation/metrics.json \
  previews/fsg6c/full-corner_up_right-seed953-evaluation/metrics.json \
  previews/fsg6c/full-corner_down_left-seed907-evaluation/metrics.json \
  previews/fsg6c/full-corner_down_left-seed953-evaluation/metrics.json \
  --out previews/fsg6c/full-comparison
```

## What Code must report

Return one paste-ready block with:

- HEAD before/after, branch/push, and proof `44794a3` is an ancestor;
- explicit preservation of FSG6a and FSG6b FAIL records and the accepted `z -> gaze` repair;
- frozen-source diff for FSG1 stereo, FSG3 surface map, FSG6b frontier constants/targets, rig, `bl_common.py` and pins;
- explicit normalized comparison showing the FSG6c policy change is the candidate continuation semantics, while FSG6b binocular per-edge evidence and 3D frontier extraction/ranking remain unchanged;
- environment and GPU backend;
- FSG6c positive summary, all nine negative FAIL lines, and all earlier regression summaries;
- the analytic runtime-semantic preflight, including the critical fresh `corner_up_right` transition's top/right fractions, new decision and retired-conjunction decision;
- smoke status and every FAIL line;
- each full trajectory, termination, every selected frontier support count/new-area score;
- for every selected decision: per-eye L/R edge fractions, binocular per-edge evidence, compatible edges, selected candidate continuation combined fraction and threshold;
- per-patch object measurement coverage;
- overlap matched/median/P95/idempotence;
- coverage curves and gain over seed;
- final map count/support histogram, curved-surface median/P95, supported radial median, purity, yaw/pitch span;
- all full FAIL lines verbatim;
- visuals/PLY observations, samples/timings and aggregate;
- code fixes, if any, with the demonstrated defect and why the fix does not alter the scientific specification;
- final status exactly `FSG6C_INCREMENT6_PASS` or `FSG6C_INCREMENT6_FAIL`.

If PASS: close Increment 6 and authorize, but do not implement, the next experiment. If FAIL: preserve the miss and stop.
