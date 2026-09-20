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

## Results

Run 2026-09-20 on the workstation. HEAD before `6fea139`, working tree clean,
`44794a3` confirmed an ancestor (`git merge-base --is-ancestor` exit 0).

**Final status: `FSG6C_INCREMENT6_FAIL`.** The diagnostic smoke raised a **runtime
exception**, which per §Schedule blocks the full schedule. **No full trial was
run.** The miss is preserved. Increment 6 is NOT closed and no next experiment is
authorized.

### FSG6a and FSG6b preserved

Both remain formal FAILS (2/4 each) with Results, log entries, `D-FSG6a`/`D-FSG6b`
outcomes, README rows and all `previews/fsg6/...` and `previews/fsg6b/...`
artifacts untouched. The accepted `z -> gaze` repair is in place in all three
runners (`fsg6_run.py:64`, `fsg6b_run.py:65`, `fsg6c_run.py:65`); an AST sweep
confirms no bare `z` load remains in any of them. `git diff 44794a3` over the FSG1
stereo modules, `fsg3_surface_map.py`, **all five FSG6a and all five FSG6b
modules**, `rig.py`, `bl_common.py` and `requirements-fsg.txt` is empty.

### Normalized FSG6b -> FSG6c policy comparison

Naming-normalized diff of `fsg6c_frontier.py` against `fsg6b_frontier.py`: the
only functional change is the new `directional_continuation_evidence()`,
`_candidate_edge_allowed` delegating to it, `_retired_component_conjunction_allowed`
kept for diagnostics, and `choose_next` recording the `continuation` record.
**Byte-identical**: `edge_evidence`, `binocular_edge_evidence` (the accepted FSG6b
eye-symmetric evidence), `_voxel_centroids`, `extract_frontier`, `_new_box_area`,
and the candidate sort key. `fsg6c_run.py`, `fsg6c_eval.py`, `fsg6c_compare.py`
and `fsg6c_render_fix.py` are identical to their FSG6b counterparts modulo
naming. `SURFACE_FRONTIER` and `TARGETS` are **exactly equal** to FSG6b with no
differing keys; `edge_object_fraction_min` is 0.15 in both; `FUSION` equals the
frozen FSG4 12 mm rule.

Python 3.12.3, NumPy 2.2.6, OpenCV 4.13.0, Pillow 12.3.0, Blender 5.2.1 LTS,
Cycles OPTIX on an NVIDIA GeForce RTX 4090.

### Checks — all passed before acquisition

```text
[fsg6c-scene] PASS up_right=[-13.794,13.354]x[-10.188,9.952] down_left=[-13.597,12.894]x[-10.819,10.381] horizontal_ideal_max=0.480 chord_max_mm=0.163 runtime_preflight=true retired_conjunction_rejected_critical=true
[fsg6c-frontier] PASS map_state_changes_2d_direction=true eye_swap_invariant=true diagonal_corner_continuation=true resolved_boundary_stops=true
[fsg6c-check] SUMMARY passed=10 failed=0
```

All nine negatives exited 1, including `conjunction`:
`deliberate retired FSG6b diagonal component-conjunction rule detected`, and
`monocular`, preserving the FSG6b eye-symmetry protection. All sixteen FSG1–FSG6b
regression suites stayed green, and FSG6a's seven and FSG6b's eight negatives all
still exit 1.

### The analytic runtime-semantic preflight

The critical control passed exactly as specified, measured through the continuous
analytic cylinder, the repository's own rectification/crop/support masks, and the
exact runtime continuation function:

```text
corner_up_right  (2.0,+3.0) -> (7.0,+8.0)  direction [1, 1]
  binocular edges: left=0.4266 right=0.6219 top=0.0797 bottom=0.5406
  compatible_edges ['right','top']   fractions {'right': 0.6219, 'top': 0.0797}
  combined_fraction 0.6219 >= 0.15   rule max_over_direction_compatible_edges
  FSG6c allowed             : True
  retired conjunction allowed: False
```

Every transition of both construction traces is reachable under runtime
semantics (geometry-only ideal coverage 0.9962 and 0.9909). The FSG6b
design/runtime inconsistency is genuinely fixed.

### Smoke — RUNTIME EXCEPTION, blocks full

`corner_up_right` / 907 / small:

```text
ValueError: active FSG6c fixation has too few object points
  tools/fsg6c_run.py line 72, in execute
```

Three fixations were acquired before the abort. The policy walked **off the
fixture**:

```text
step 0  gaze (-8,-7)   object px in core 7005   map points 5936
step 1  gaze (-3,-12)  object px in core 1486   map points 1147
step 2  gaze (-8,-17)  object px in core    0   map points    0   -> exception
```

The ribbon spans pitch [-10.188,+9.952]. Fixation 2 at pitch -17 sees no object
at all.

### Diagnosis: `max()` lets one component license the other

Recomputed with the runtime functions on the saved rectified masks, at the seed
gaze (-8,-7):

```text
left   L=0.0000 R=0.0766  binocular=0.0766  veto
right  L=0.4203 R=0.3406  binocular=0.4203  PERMIT
top    L=0.3844 R=0.5156  binocular=0.5156  PERMIT
bottom L=0.0000 R=0.0000  binocular=0.0000  veto        <-- object does NOT continue downward
```

The down-right direction `(+1,-1)` has compatible edges `{right, bottom}`:

```text
f_cont = max(right 0.4203, bottom 0.0000) = 0.4203 >= 0.15  -> FSG6c PERMITS
retired component conjunction: right PERMIT and bottom veto -> REJECTS
```

The bottom edge is **exactly 0.0000 in both eyes** — a provably resolved
boundary — yet the move is permitted because `max()` substitutes the *other*
component's evidence. At step 1 the same thing happens with `{left, bottom}`:
`max(0.3109, 0.0000) = 0.3109`, and the controller leaves the object entirely.

This is **not** small-profile or seed specific. Through the analytic preflight at
both profiles and on both fixtures:

```text
corner_up_right  small core=128 seed(-8,-7)  bottom=0.0000 right=0.4203 -> combined 0.4203 ALLOWED (retired: False)
corner_up_right  full  core=256 seed(-8,-7)  bottom=0.0000 right=0.4258 -> combined 0.4258 ALLOWED (retired: False)
corner_down_left small core=128 seed(+8,+7)  top=0.0000 left=0.4609 -> combined 0.4609 ALLOWED (retired: False)
corner_down_left full  core=256 seed(+8,+7)  top=0.0000 left=0.4641 -> combined 0.4641 ALLOWED (retired: False)
```

The oracle mask is ray-traced and seed-independent, so all four full trials would
begin from exactly this state. **The failure is geometric and deterministic.**

FSG6c is therefore too permissive in precisely the dual way FSG6a/FSG6b were too
strict. The conjunction demanded continuation on *every* component; `max()`
demands it on *none in particular*. Neither expresses "the surface leaves through
the corner region between these two edges".

### Why no code fix was made

`directional_continuation_evidence()` implements the handoff's §"The only policy
change" exactly: compatible edges from the nonzero components,
`f_cont(d) = max(f(edge) for edge in compatible_edges(d))`, permitted iff
`>= 0.15`. Down-right from `(+1,-1)` gives `{right, bottom}` and
`max(0.4203, 0.0000) = 0.4203 >= 0.15`. The code and the specification agree.

The exception therefore arises from the **specified semantics**, not from an
implementation or orchestration defect. Per §Schedule a code fix is permitted
only for a defect that "does not alter the scientific specification"; any repair
here changes the continuation rule itself. Nothing was changed and the miss is
returned to Luiz/Chat.

### A gap in the check suite

The shipped over-permissiveness guard in `fsg6c_frontier.self_test` resolves
**both** compatible edges and is correctly vetoed. The failing case resolves only
**one**:

```text
shipped control (top AND right resolved): top=0.0000 right=0.0000 -> combined 0.0000 allowed=False   correctly vetoed
UNTESTED case   (bottom resolved, right strong): bottom=0.0000 right=0.9062 -> combined 0.9062 allowed=True   (retired rule: False)
```

A control in which one compatible edge is exactly zero while the other is strong
would have failed before any acquisition. The suite has no such case, and the
preflight only validated the two intended traces and the critical up-right
transition — never that off-object directions are correctly refused.

### Not reached

No full trial was run, so there are no full trajectories, per-patch coverages,
overlap statistics, coverage curves, final map geometry, PLY files, aggregate
comparison or `coverage_3d_frontier.png`. `previews/fsg6c/full-*` does not exist.
The only FSG6c artifacts are the aborted smoke's three acquisitions, two maps and
three patches, preserved at
`previews/fsg6c/smoke-corner_up_right-seed907`.

### Cost

Smoke 7.9 s wall, 3 fixations x 13,107,200 = 39,321,600 primary camera samples
before the abort. Checks and regressions under a minute in total. Interactive
class throughout; no Batch work was reached.

### What still holds

The eye-symmetry repair (FSG6b) and the candidate-aligned *diagonal* permission
both behave as designed where they were tested: the critical `corner_up_right`
transition that defeated FSG6b is now correctly permitted (0.6219 vs a 0.0797 top
edge), and the retired conjunction is correctly detected as rejecting it. The 3D
surfel frontier, FSG1 instrument and FSG3 fusion were never reached in anger this
increment. What fails is the direction-compatible **combination rule**, measured
above.
