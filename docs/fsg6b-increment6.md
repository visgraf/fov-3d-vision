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

## Results

Run 2026-09-20 on the workstation. HEAD before `32e3f1f`, working tree clean,
`ea8e962` confirmed an ancestor (`git merge-base --is-ancestor` exit 0).

**Final status: `FSG6B_INCREMENT6_FAIL` — 2 of 4 full trials passed.** The miss is
preserved. Increment 6 is NOT closed and no next experiment is authorized.

### FSG6a preserved

FSG6a remains a formal `FSG6_INCREMENT6_FAIL` (2/4). Its Results, `docs/log.md`
entry, `D-FSG6a` outcome, README row and all twelve `previews/fsg6/...` artifact
directories are untouched, and the accepted one-token `z -> gaze` repair is still
in place at `tools/fsg6_run.py:64`. `git diff ea8e962` over the FSG1 stereo
modules, `fsg3_surface_map.py`, **all five FSG6a modules**, `rig.py`,
`bl_common.py` and `requirements-fsg.txt` is empty.

### Frozen constants, verified mechanically

`fsg6b_public.SURFACE_FRONTIER == fsg6_public.SURFACE_FRONTIER` and
`fsg6b_public.TARGETS == fsg6_public.TARGETS` are both **exactly True**, with no
differing keys; `edge_object_fraction_min` is 0.15 in both; `FUSION` equals the
frozen FSG4 12 mm rule. A normalised diff of `fsg6b_frontier.py` against
`fsg6_frontier.py` shows the only functional change is the new
`binocular_edge_evidence` plus `choose_next` consuming both eyes —
`edge_evidence`, `_voxel_centroids`, `extract_frontier`,
`_candidate_edge_allowed`, `_new_box_area` and the candidate sort key are
byte-identical. `fsg6b_compare.py` and `fsg6b_render_fix.py` are identical to
their FSG6a counterparts modulo naming.

The right eye reaches the policy through outputs the **frozen** instrument
already produced and FSG6a discarded: `compute_once` returns a third `state`
carrying `ids_left`/`ids_right`, and `fsg_stereo.support_mask(c, rec, "R")`
already exists. No change to the stereo instrument was needed or made.

Python 3.12.3, NumPy 2.2.6, OpenCV 4.13.0, Pillow 12.3.0, Blender 5.2.1 LTS,
Cycles OPTIX on an NVIDIA GeForce RTX 4090.

### Checks

```text
[fsg6b-scene] PASS up_right=[-14.559,14.033]x[-9.902,9.659] down_left=[-12.902,12.157]x[-11.340,10.770] horizontal_ideal_max=0.471 chord_max_mm=0.156
[fsg6b-frontier] PASS map_state_changes_2d_direction=true eye_swap_invariant=true resolved_boundary_stops=true
[fsg6b-check] SUMMARY passed=8 failed=0
```

All eight negatives exited 1, including the one that matters most here:

```text
[monocular] [fsg6b-check] FAIL AssertionError deliberate retired left-eye-only continuation rule detected as eye-swap asymmetric
```

All fifteen FSG1–FSG6a regression suites stayed green (23/24, 29, 34, 48, 37, 46,
7, 8, 4, 5, 7, 7, 6, 7 passed, 0 failed), and FSG6a's own seven negatives still
all exit 1.

### The binocular repair works, and is not what failed

The new rule is live on real acquisitions. At fixation 0 of both `fresh_up_right`
trials the left edge measured **f_L = 0.0000, f_R = 0.2414**, so
`max(f_L,f_R) = 0.2414 >= 0.15` **permitted a direction the retired left-eye-only
rule would have vetoed**. Reported honestly: across all four trials this rescue
fired twice, and in neither case did the *selected* move depend on a rescued
edge — the rule broadened the candidate set but changed no trajectory on this
fixture family. FSG6a's eye-asymmetry failure mode did not recur, and FSG6a's
`fix_04 object measurement coverage` miss is gone: every patch here scores
0.9215–0.9485 against the >=0.90 gate.

### The four full trials

Each run exactly once at `--profile full`, 1,258,291,200 samples each
(5,033,164,800 total).

| Trial | Trajectory (yaw,pitch) | Termination | Final cov. | Median | P95 | Radial | Status |
|---|---|---|---:|---:|---:|---:|---|
| up_right/809 | (-8,-7)(-3,-2)(2,3)(7,3)(12,8)(7,8) | `max_fixations` | 99.683% | 3.369 mm | 13.124 mm | -0.300 mm | **FAIL** |
| up_right/853 | (-8,-7)(-3,-2)(2,3)(7,3)(12,8)(7,8) | `max_fixations` | 99.664% | 3.352 mm | 13.117 mm | -0.282 mm | **FAIL** |
| down_left/809 | (8,7)(3,2)(-2,-3)(-7,-8)(-2,-8)(-7,-3) | `no_frontier` | 99.225% | 4.260 mm | 14.395 mm | +0.988 mm | PASS |
| down_left/853 | (8,7)(3,2)(-2,-3)(-7,-8)(-2,-8)(-7,-3) | `no_frontier` | 99.225% | 4.269 mm | 14.411 mm | +0.965 mm | PASS |

Pitch span **15.0° on all four** against the >=10° gate; yaw span 20° / 15°.
Every move one 5-degree lattice component; no repeats. Nonterminal selected
frontier support 29–90 against >=8. Coverage gain 58.3–62.0 pp (gate >=35).
Post-seed overlap 17,172–27,465 matched (>=5,000), median 1.95–2.57 mm (<=10),
p95 5.14–8.39 mm (<=25), every replay idempotent, largest coverage decrease
0.00 pp. Maps 71,727–78,340 surfels, all pure instance 101, 36,490–37,288
multi-look (>=5,000).

### All full FAIL lines, verbatim

```text
fresh_up_right/809: 3D frontier policy did not terminate by resolving the frontier
fresh_up_right/853: 3D frontier policy did not terminate by resolving the frontier
fresh_down_left/809: (none)
fresh_down_left/853: (none)
[fsg6b-compare] FSG6B_INCREMENT6_FAIL
  fresh_up_right/809 3D-frontier run failed
  fresh_up_right/853 3D-frontier run failed
```

Each failing trial fails on **one gate only**, and it is the same gate.

### Diagnosis: the conjunctive corner rule blocks a diagonal surface

This is a *different* defect from FSG6a's, now isolated because the eye
asymmetry is gone.

The veto requires, for a diagonal move, that **both** corresponding edge bands
continue (`dx>0 and dy>0` needs `touch_right` AND `touch_top`). But a narrow
ribbon rolled +30° leaves the fovea through a **corner**, not through two full
edge bands. Measured at the deflecting fixation, gaze (+2,+3) on
`fresh_up_right`, from the saved rectified masks:

```text
top band            L=0.0000  R=0.0035  max=0.0035  veto
right band          L=0.6176  R=0.6004  max=0.6176  PERMIT
top-right corner    L=0.0000  R=0.0900  max=0.0900  veto
right band, top half L=0.7883  R=0.9258  max=0.9258  PERMIT
object extent in the core: rows 25..255 of 256, cols 0..255 of 256
object touches top row: False | right col: True
```

The object does not reach the top image row at all — the `top` veto is
**correct**, and both eyes agree, so this is not an eye-swap artifact. Yet the
surface plainly continues up-and-right: 93% of the top half of the right band is
object. The conjunctive rule reads "no object at the top edge" as "the object
does not continue upward", when in fact it continues diagonally out of the
corner. The `(+5,+5)` move is therefore blocked, the controller takes the
pure-yaw `(+7,+3)` instead, and it spends an extra fixation recovering the
diagonal at `(+12,+8)`.

The cost is exactly the budget. `fresh_up_right` reaches 99.68% coverage but
still has **two eligible candidates** at fixation 6 — `(+12,+3)` with 90 frontier
surfels and `(+2,+8)` with 63 — because the ribbon truly extends to yaw +14.03
while the map reaches +12.44. The frontier is not exhausted when
`MAX_BUDGET_FIXATIONS = 6` ends the run, so it terminates `max_fixations`.
`fresh_down_left` stops properly at `no_frontier`: at its final fixation its
`left` (0.0988) and `top` (0.1039) edges are genuinely resolved in both eyes and
every remaining permitted neighbour is already visited.

That the two fixtures diverge is the non-mirror design working as intended: the
+30° ribbon exits through a corner, the +220° one does not.

Note the handoff's own construction estimate assumed a four-look diagonal
`(-8,-7)(-3,-2)(2,3)(7,8)`. Its fourth step is exactly the `(+5,+5)` move the
conjunctive rule forbids, so `ideal_angular_coverage` — which models the fovea as
a plain 12x12 box with no veto — and the veto semantics disagree about whether
that trajectory is reachable.

**This is a specification question, not an implementation defect.** The
conjunctive requirement is written into the handoff ("a diagonal requires both
corresponding edges to continue"), inherited unchanged from FSG6a and explicitly
frozen for FSG6b. Changing it, or the 0.15 threshold, or the 6-fixation budget,
would alter the scientific specification, so nothing was tuned and the miss is
returned to Luiz/Chat.

### Visuals and PLY

`growth.png` and `growth_truth.png` show `fresh_up_right` growing lower-left to
upper-right (41.4 → 58.7 → 75.3 → 97.4 → 99.6 → 99.7%) and `fresh_down_left`
upper-right to lower-left (37.2 → 56.5 → 80.3 → 99.1 → 99.1 → 99.2%); the last
two panels of each are visually indistinguishable, the surface being finished by
fixation 4. `coverage_3d_frontier.png` shows all four rising monotonically to
~99.2–99.7%. Every `surface_map.ply` carries `comment fixed head frame H` and has
**no `element face`** — no meshing. An independent read of the exported clouds
gives median cylinder radius **0.77914 m against a true 0.780** (`fresh_up_right`)
and **0.70120–0.70122 m against a true 0.700** (`fresh_down_left`), i.e. within
0.9 mm inward and 1.2 mm outward respectively — no systematic contraction.

### Cost

Smoke run 17.6 s (loop 17.47 s recorded, Blender 11.86 s) / eval 8.2 s. Full runs
1m17.9s, 1m18.4s, 1m24.2s, 1m24.6s (recorded loop 77.71/78.25/84.10/84.51 s,
Blender 34.6–35.1 s each). Aggregation under a second. Batch class throughout.

### What holds

The truth-free 3D surfel frontier drove a genuinely two-dimensional trajectory on
all four trials (pitch span 15.0°) and reconstructed both fresh ribbons to
99.2–99.7% curved-surface completeness at 3.35–4.27 mm median, where a five-look
horizontal-only controller reaches at most 0.471 ideal coverage. The eye-symmetry
repair is proven correct by check and exercised on real data. The remaining
obstacle to closing Increment 6 is the conjunctive corner rule in the auxiliary
veto, measured above and left for a specification decision.
