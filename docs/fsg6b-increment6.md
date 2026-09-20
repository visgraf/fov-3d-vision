# FSG6b / Increment 6 — binocular continuation for the 3D surface frontier

## Decision to record before acquisition

`D-FSG6b — Keep the FSG6 3D surfel frontier; make only the auxiliary continuation veto eye-symmetric.`

FSG6a remains a **formal FAIL** and its records/results must remain untouched. It nevertheless established that the new 3D surfel frontier can drive genuinely two-dimensional gaze and reconstruct the diagonal curved ribbons to about 99% completeness with millimetric geometry. The formal miss was traced to the old auxiliary continuation veto: it consulted only the rectified left-eye oracle mask. A 180-degree image-plane roll swaps the physical eye centres, so the nominal mirror pair was not a monocular mirror. Binocular parallax then changed the left-eye edge fraction enough to veto one diagonal move in only one fixture.

The accepted one-token `z -> gaze` repair in `tools/fsg6_run.py` is an implementation fix and remains in the repository. FSG6b is additive; do not rewrite FSG6a.

The scientific question is:

> Does the unchanged truth-free 3D surfel frontier close Increment 6 when its segmentation-only physical-boundary veto is made invariant to swapping the two binocular eyes?

## The only policy change

The 3D frontier extraction, candidate lattice, candidate support test, ranking, 5-degree step, all thresholds and every numerical gate are unchanged from FSG6a.

For each direction `d`, compute the same edge-band object fraction independently in the two rectified eyes:

`f_L(d)` and `f_R(d)`.

The continuation evidence is now

`f_cont(d) = max(f_L(d), f_R(d))`,

and a movement component is permitted iff `f_cont(d) >= 0.15`, using the **unchanged** FSG6a threshold. Thus either eye may provide evidence that the physical object continues, while the persistent 3D map still creates and ranks the frontier. Segmentation cannot create a candidate.

This rule is exactly invariant to `L <-> R`. `check_fsg6b.py` supplies a synthetic case in which the retired left-eye-only rule changes under an eye swap; the binocular rule and selected gaze must not.

The host loop receives only the two rectified oracle instance masks, their calibration-derived raw support masks, calibration, persistent map and fixation history. It must not import `fsg6b_scene.py` or open `evaluation_only`.

## Frozen pieces

Unchanged from FSG6a:

- `FSG1-HDR-SGBM-one-original-update-original-validity-v1`;
- existing `tools/fsg3_surface_map.py`, 12 mm association/hash and idempotent replay;
- fixed head frame H and exact eye/head geometry; no ICP;
- fixed 2.10 m vergence;
- full profile 256 spp, small profile 64 spp for smoke only;
- 25 mm frontier voxels, 65 mm neighbourhood, PCA tangent frontier, 0.18 asymmetry minimum, 0.12 m lookahead;
- eight neighbouring 5-degree yaw/pitch candidate moves;
- minimum 8 agreeing 3D frontier surfels;
- 0.15 edge-object continuation threshold;
- all FSG6a measurement, overlap, map-quality, coverage, pitch-span and radial-bias gates;
- no meshing, hole filling, learned policy or fitted surface model.

`check_fsg6b.py` compares the FSG6b frontier constants and numerical targets byte-for-value with `fsg6_public.py`; any hidden threshold/gate drift fails before acquisition.

## Fresh, non-mirror validation fixtures

FSG6a's four full records are development evidence and are not reused as validation.

FSG6b uses two new diagonal cylindrical ribbons that are deliberately **not exact mirror copies** of each other:

- `fresh_up_right`: centre z = -2.85 m, radius 0.78 m, theta -58 to +52 degrees, height 0.24 m, roll +30 degrees, seed gaze `(-8,-7)` degrees, texture tag 47.
- `fresh_down_left`: centre z = -2.70 m, radius 0.70 m, theta -50 to +60 degrees, height 0.23 m, roll +220 degrees, seed gaze `(+8,+7)` degrees, texture tag 53.

Both render with 48 strips and are evaluated against the continuous analytic cylinders. The check requires max strip chord error <0.2 mm. Fresh Monte-Carlo seeds are **809** and **853**.

Analytic construction checks (not experimental results):

- `fresh_up_right` angular bounds are about yaw [-14.56,+14.03], pitch [-9.90,+9.66] degrees;
- `fresh_down_left` about yaw [-12.90,+12.16], pitch [-11.34,+10.77] degrees;
- a five-look horizontal-only controller covers at most about 47.1% of this fixture family;
- plausible four-look diagonal traces exceed 95% ideal angular coverage.

These estimates only establish that the fresh fixtures exercise two-dimensional gaze; no actual trajectory is prescribed.

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

Every nonterminal selected gaze has >=8 agreeing 3D frontier surfels. The policy trace must record both per-eye edge fractions and the symmetric combined fraction. Truth remains unavailable to the host loop.

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
- only object instance 101 in the map;
- >=5,000 surfels with support >=2;
- absolute median signed radial error on those surfels <=7.5 mm.

## Schedule

1. Record `D-FSG6b` and a prospective `docs/log.md` entry before acquisition. Preserve FSG6a FAIL and its records.
2. Run the FSG6b positive checks and all eight expected-failing negatives.
3. Run the existing FSG1–FSG6a regression checks unchanged.
4. Run one diagnostic small trial: `fresh_up_right`, seed 809. Numerical exit 2 is diagnostic; integrity/provenance/runtime failure stops the experiment.
5. If integrity is sound, run exactly once all four full trials: both fixtures x seeds 809/853.
6. Evaluate each and aggregate exactly those four with `fsg6b_compare.py`.
7. Inspect `growth.png`, `growth_truth.png`, every `surface_map.ply`, policy traces and aggregate `coverage_3d_frontier.png`.
8. No rerender after a numerical miss and no threshold, fixture, seed, SPP, vergence, fusion, frontier or gate change.

A completed full run may exit 2 numerically; preserve it and continue the other predeclared full trials. Stop early only on integrity/provenance/runtime failure.

## Exact FSG6b commands

```bash
.venv/bin/python tools/dev/check_fsg6b.py
for n in policy mapstate horizontal monocular flat shift bias purity; do
  .venv/bin/python tools/dev/check_fsg6b.py --negative "$n"; test $? -eq 1 || exit 1
done
```

Run the existing regression checks exactly as recorded in `docs/log.md`, including `check_fsg6.py`; every prior summary must remain green.

Smoke:

```bash
.venv/bin/python tools/fsg6b_run.py --out previews/fsg6b/smoke-fresh_up_right-seed809 --profile small --fixture fresh_up_right --seed 809 --device OPTIX
.venv/bin/python tools/fsg6b_eval.py previews/fsg6b/smoke-fresh_up_right-seed809 --out previews/fsg6b/smoke-fresh_up_right-seed809-evaluation --mode smoke
```

Full:

```bash
.venv/bin/python tools/fsg6b_run.py --out previews/fsg6b/full-fresh_up_right-seed809 --profile full --fixture fresh_up_right --seed 809 --device OPTIX
.venv/bin/python tools/fsg6b_eval.py previews/fsg6b/full-fresh_up_right-seed809 --out previews/fsg6b/full-fresh_up_right-seed809-evaluation --mode full
.venv/bin/python tools/fsg6b_run.py --out previews/fsg6b/full-fresh_up_right-seed853 --profile full --fixture fresh_up_right --seed 853 --device OPTIX
.venv/bin/python tools/fsg6b_eval.py previews/fsg6b/full-fresh_up_right-seed853 --out previews/fsg6b/full-fresh_up_right-seed853-evaluation --mode full
.venv/bin/python tools/fsg6b_run.py --out previews/fsg6b/full-fresh_down_left-seed809 --profile full --fixture fresh_down_left --seed 809 --device OPTIX
.venv/bin/python tools/fsg6b_eval.py previews/fsg6b/full-fresh_down_left-seed809 --out previews/fsg6b/full-fresh_down_left-seed809-evaluation --mode full
.venv/bin/python tools/fsg6b_run.py --out previews/fsg6b/full-fresh_down_left-seed853 --profile full --fixture fresh_down_left --seed 853 --device OPTIX
.venv/bin/python tools/fsg6b_eval.py previews/fsg6b/full-fresh_down_left-seed853 --out previews/fsg6b/full-fresh_down_left-seed853-evaluation --mode full
.venv/bin/python tools/fsg6b_compare.py \
  previews/fsg6b/full-fresh_up_right-seed809-evaluation/metrics.json \
  previews/fsg6b/full-fresh_up_right-seed853-evaluation/metrics.json \
  previews/fsg6b/full-fresh_down_left-seed809-evaluation/metrics.json \
  previews/fsg6b/full-fresh_down_left-seed853-evaluation/metrics.json \
  --out previews/fsg6b/full-comparison
```

## What Code must report

Return one paste-ready block with:

- HEAD before/after, branch/push, and proof `ea8e962` is an ancestor;
- explicit preservation of FSG6a FAIL and the accepted `z -> gaze` repair;
- frozen-source diff for FSG1 stereo, FSG3 surface map, FSG6a frontier constants/targets, rig, `bl_common.py` and pins;
- environment and GPU backend;
- FSG6b positive summary, all eight negative FAIL lines, and all earlier regression summaries;
- smoke status and every FAIL line;
- each full trajectory, termination, every selected frontier support count/new-area score;
- for every policy decision, per-eye L/R directional edge fractions plus symmetric combined evidence for the selected direction;
- per-patch object measurement coverage;
- overlap matched/median/P95/idempotence;
- coverage curves and gain over seed;
- final map count/support histogram, curved-surface median/P95, supported radial median, purity, yaw/pitch span;
- all full FAIL lines verbatim;
- visuals/PLY observations, samples and wall times;
- aggregate status/ranges;
- any code fix, or explicitly none;
- final status exactly `FSG6B_INCREMENT6_PASS` or `FSG6B_INCREMENT6_FAIL`.

If PASS, close Increment 6 and authorize — but do not implement — the next experiment. If FAIL, preserve the miss and stop for Luiz/Chat.
