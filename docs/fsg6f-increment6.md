# FSG6f / Increment 6 — candidate-level frontier-state consensus

## Decision

FSG6a, FSG6b, FSG6c, FSG6d and FSG6e remain formal FAIL records. Preserve every result and preserve the accepted `z -> gaze` repair.

FSG6e established the three-way persistent surfel state we wanted: raw geometric frontier could remain high while `OPEN` support collapsed and `no_frontier` occurred on both `closure_down_left` trials. Its two `closure_up_right` failures exposed the remaining abstraction gap: candidate eligibility still meant merely “at least eight OPEN surfels exist in this direction”, even when most of the aligned persistent evidence was already resolved.

FSG6f changes only that candidate-level interpretation.

For an aligned candidate direction, let

- `N_OPEN` = OPEN frontier support,
- `N_MAP` = MAP_RESOLVED support,
- `N_BOUNDARY` = BOUNDARY_RESOLVED support,
- `N_RESOLVED = N_MAP + N_BOUNDARY`.

The candidate is exploration-open only when

```text
N_OPEN > N_RESOLVED
```

and it must independently satisfy the already-frozen

```text
N_OPEN >= 8
```

support gate. A tie is resolved, not open.

This is a state-consensus rule, not a fitted numerical threshold. No `0.5` tuning constant is introduced; OPEN must simply outnumber the two resolved states together.

The FSG6e surfel-state classifier, FSG6d projected-frontier corridor, candidate ranking, FSG1 instrument, FSG3/FSG4 12 mm fusion, 5-degree lattice, six-fixation budget and every numerical acceptance gate remain unchanged.

## Why this is the smallest correction

FSG6e development results already separate productive and pathological candidate state mixtures.

Productive `closure_up_right/1123` selected moves had:

```text
OPEN / raw
45/46
41/59
31/50
61/63
60/83
```

All are strict OPEN majorities.

The two pathological survivors were:

```text
closure_up_right/1123 final survivor: 11 OPEN, 3 MAP, 82 BOUNDARY -> 11/96
closure_up_right/1181 off-ribbon move: 8 OPEN, 1 MAP, 16 BOUNDARY -> 8/25
```

Both pass the old FSG6e `>=8 OPEN` rule but are overwhelmingly resolved by persistent evidence.

These preserved FSG6e numbers are development controls only. They are not counted as FSG6f validation.

## Candidate-level semantics

FSG6f preserves FSG6e's surfel classifier exactly:

1. `MAP_RESOLVED`: the existing 0.12 m look-ahead target is already represented within the frozen strict 12 mm map-association rule.
2. `BOUNDARY_RESOLVED`: the target is not mapped, but completed binocular history has valid support in both eyes and object evidence below the frozen 0.15 threshold around the projected target.
3. `OPEN`: neither resolved condition applies.

Candidate support is then aggregated. Only a strict OPEN-majority candidate can reach the unchanged FSG6d projected-frontier continuation corridor and ranking.

Thus the hierarchy is:

```text
raw 3D frontier
  -> persistent surfel state
  -> candidate state consensus
  -> projected-frontier binocular continuation corridor
  -> unchanged predicted-new-area / frontier-score ranking
  -> gaze
```

No truth coverage, recent gain, evaluator geometry, or hidden surface is used by the runtime controller.

## Fresh prospective validation

Fresh non-mirror curved fixtures and fresh renderer seeds are used. All FSG6a-e observations are development/regression evidence only.

- `consensus_up_right`: radius 0.75 m, centre-z -2.91 m, cylinder arc -59 to +58 degrees, height 0.252 m, roll +28 degrees; seed gaze `(-8,-7)` degrees.
- `consensus_down_left`: radius 0.71 m, centre-z -2.69 m, cylinder arc -52 to +65 degrees, height 0.250 m, roll +216 degrees; seed gaze `(+8,+7)` degrees.
- fresh seeds: `1237`, `1291`.

Analytic angular bounds are approximately:

- `consensus_up_right`: yaw [-13.948,+13.877], pitch [-9.115,+9.088] degrees;
- `consensus_down_left`: yaw [-13.959,+13.145], pitch [-11.153,+10.659] degrees.

A five-look horizontal-only ideal scan covers at most 0.450 of the fresh surface.

## Evaluator-only closed-loop preflight

Before Blender acquisition, `fsg6f_scene.py` performs a design/plumbing simulation using continuous analytic cylinder truth only on the evaluator side. It supplies ideal visible map samples and analytic binocular masks to the **actual runtime `fsg6f_frontier.choose_next()`**. The runtime policy itself still imports no fixture truth.

Current local design sanity gives:

```text
consensus_up_right:
  (-8,-7) -> (-3,-2) -> (+2,+3) -> (+7,+8) -> (+12,+8) -> (+12,+3)
  STOP no_frontier, ideal coverage 1.0000, pitch span 15 deg
  candidate-consensus rejections exercised: 2

consensus_down_left:
  (+8,+7) -> (+3,+2) -> (-2,-3) -> (-7,-8) -> (-12,-8)
  STOP no_frontier, ideal coverage 0.9991, pitch span 15 deg
  final state contains one candidate that passes the old FSG6e >=8-OPEN + corridor rule
  but is rejected by resolved-majority consensus.
```

The preflight therefore exercises the new rule, and on one fresh fixture the new rule is explicitly load-bearing for termination. These are design/software checks, not scientific results.

## Pre-acquisition checks

`tools/dev/check_fsg6f.py` must report:

```text
[fsg6f-check] SUMMARY passed=14 failed=0
```

The positive suite includes:

- exact equality of FSG6e frontier constants and numerical gates;
- exact reuse of frozen FSG4 fusion;
- source identity of the FSG6e MAP/BOUNDARY/OPEN classifier;
- source identity of raw frontier extraction and settled FSG6d projection/corridor helpers;
- unchanged candidate sort key;
- strict candidate state consensus and tie resolution;
- preserved productive FSG6e development controls and rejection of both pathological FSG6e survivors;
- map-state-dependent gaze direction;
- stereo-hole protection and historical binocular boundary state;
- eye-swap invariance;
- FSG6b/FSG6c/FSG6d continuation regression bracket;
- projection agreement with OpenCV rectification;
- source isolation from fixture/evaluator truth;
- fresh scene curvature/flat/shift/bias/horizontal controls;
- evaluator-only closed-loop preflight in which candidate consensus is exercised and is load-bearing for termination on at least one fresh fixture.

All fifteen deliberate negatives must exit 1:

```text
policy mapstate horizontal monocular conjunction componentmax full_edge
rawtermination forget_history stereo_hole anyopen flat shift bias purity
```

`anyopen` specifically detects a return to FSG6e's rule that any candidate with at least eight OPEN supporters is exploration-open even when resolved support is the majority.

## Runtime schedule

1. Read `CLAUDE.md`, verify clean `main`, and verify `62fab1d` is an ancestor.
2. Record `D-FSG6f` and the prospective `docs/log.md` entry **before acquisition**.
3. Run FSG6f checks, all fifteen negatives, and every prior regression through FSG6e including their negatives.
4. Run one small `consensus_up_right / 1237` diagnostic smoke.
5. A completed small numerical exit 2 may proceed to full if integrity/provenance/runtime remains sound. Any integrity/provenance/runtime/truth-isolation failure blocks full.
6. Run exactly four full trials once each: both fresh fixtures x both fresh seeds.
7. Evaluate all four and aggregate exactly the prospectively fixed set.
8. Preserve every result. No tuning or alternate trials after acquisition begins.

## Full-trial gates

All inherited FSG6e gates remain unchanged:

- fixation count 4..6 and terminal reason `no_frontier`;
- pitch span >=10 degrees;
- each move is one nonzero 5-degree lattice step and no gaze repeats;
- object measurement fraction >=0.90 at every patch;
- >=5000 post-seed matched points;
- overlap median <=10 mm and P95 <=25 mm;
- replay idempotent and no material coverage decrease;
- final curved-surface median <=10 mm and P95 <=30 mm;
- >=5000 multi-look surfels;
- absolute supported signed radial median <=7.5 mm;
- object-pure map;
- final truth coverage >=0.90 and gain over seed >=35 percentage points;
- every nonterminal selected candidate has >=8 OPEN frontier surfels;
- every nonterminal selected candidate has strict OPEN-majority state consensus.

Raw/MAP_RESOLVED/BOUNDARY_RESOLVED/OPEN counts, candidate resolved/open counts, consensus rejections, corridor evidence, per-fixation gain and residual closure are descriptive diagnostics.

## Frozen items

Do not change after this prospective handoff:

- 12 mm association/hash;
- 0.15 object threshold;
- 0.04 corridor/patch scale;
- raw frontier constants or 0.12 m look-ahead;
- FSG6e state classifier;
- FSG6d projected corridor;
- candidate sort key;
- minimum support 8;
- FSG1 instrument;
- FSG3 fusion;
- 5-degree lattice;
- six-fixation budget;
- SPP, vergence, truth coverage radius or numerical gates.

Do not introduce a completeness-percentage stop, low-gain stop, budget extension, confidence threshold, learned policy, ICP, meshing, filling or self-occlusion state in this increment.

## Outcome rule

If all four prospectively fixed full trials pass, status is `FSG6F_INCREMENT6_PASS`: close Increment 6 and authorize, but do not implement, the next experiment.

If any full trial fails, status is `FSG6F_INCREMENT6_FAIL`: preserve the miss, keep Increment 6 open, and stop for Luiz/Chat. Do not tune around the outcome.

## Interpretation discipline

A PASS supports only the narrow claim that on fresh single convex visible curved surfaces, persistent three-state 3D frontier memory can be aggregated into candidate-level consensus strongly enough to reject mostly-resolved actions while preserving useful active exploration and truth-free `no_frontier` termination.

It does not establish self-occlusion reasoning, hidden-surface discovery, multiple objects, free head motion, learned gaze, optimality or calibrated uncertainty.

## Results

Run 2026-09-20 on the workstation. HEAD before `c521445`, working tree clean,
`62fab1d` confirmed an ancestor (`git merge-base --is-ancestor` exit 0).

**Final status: `FSG6F_INCREMENT6_PASS` — 4 of 4 full trials passed, every fail
list empty, aggregate exit 0. Increment 6 is CLOSED and the next experiment is
AUTHORIZED BUT NOT IMPLEMENTED.**

### FSG6a–FSG6e preserved

All five remain formal FAILS with Results, log entries, decision outcomes, README
rows and all `previews/fsg6{,b,c,d,e}/` artifacts untouched. The accepted
`z -> gaze` repair is present in all six runners (`fsg6_run.py:64`,
`fsg6b/c/d/e/f_run.py:65`). `git diff 62fab1d` over the FSG1 stereo modules,
`fsg3_surface_map.py`, **all FSG6a–FSG6e modules**, `rig.py`, `bl_common.py` and
`requirements-fsg.txt` is empty.

### Constants and normalized policy comparison

`SURFACE_FRONTIER` and `TARGETS` are **exactly equal** to `fsg6e_public` with no
differing keys; `FUSION == fsg4_public.FUSION = {0.012, 0.012}`; 0.15 threshold;
0.04 scale; 0.12 m look-ahead; step 5.0; budget 6; minimum OPEN support 8;
`alignment_cos_min` 0.50; vergence 2.10; object 141.

Fourteen settled helpers verified **text-identical** by `inspect.getsource`
(modulo module naming), none drifted: `extract_frontier`,
`classify_frontier_state`, `_target_mapped_mask`, `_target_patch_eye_evidence`,
`_project_rectified_core`, `_ray_exit`, `_exit_corridor_mask`,
`_corridor_eye_evidence`, `_project_frontier_pairs`,
`_candidate_continuation_from_projected`, `_new_box_area`, `_voxel_centroids`,
`edge_evidence`, `binocular_edge_evidence`. The candidate sort key is literally
identical and asserted by string match in `frozen_algorithm_control`.

The functional change is only candidate state consensus plus diagnostics:
`candidate_state_consensus(n_open, n_map, n_boundary)` returning
`allowed = n_open > n_map + n_boundary`, `_retired_any_open_allowed` as a
diagnostic control, an exhaustiveness assertion that
`raw == open + map_resolved + boundary_resolved`, and the
`consensus_rejected_candidates` / `candidates_before_consensus_count`
diagnostics. The consensus source contains **no `0.5`** and the core expression
`bool(no > nr)` is present — asserted by the check suite. `fsg6f_eval.py` adds
exactly the one prescribed gate, `policy decision {i} lacks OPEN-majority
candidate consensus`.

A candidate is accepted iff `N_OPEN >= 8` **and** the FSG6d corridor **and**
consensus. The implementation evaluates the corridor before recording a consensus
rejection, so `consensus_rejected_candidates` is *precisely* the set the retired
FSG6e rule would have accepted — making the required comparison exact rather than
reconstructed.

Python 3.12.3, NumPy 2.2.6, OpenCV 4.13.0, Pillow 12.3.0, Blender 5.2.1 LTS,
Cycles OPTIX on an NVIDIA GeForce RTX 4090.

### Checks

```text
[fsg6f-scene] PASS up_right=[-13.948,13.877]x[-9.115,9.088] down_left=[-13.959,13.145]x[-11.153,10.659] horizontal_ideal_max=0.450 chord_max_mm=0.170 corridor_preflight=true persistent_state_preflight=true candidate_consensus_preflight=true traces={consensus_up_right:6fix/1.0000, consensus_down_left:5fix/0.9991}
[fsg6f-frontier] PASS map_state_changes_2d_direction=true persistent_state_three_way=true historical_boundary_state=true stereo_hole_not_boundary=true eye_swap_invariant=true projected_frontier_corridor=true resolved_boundary_stops=true candidate_state_consensus=true
[fsg6f-check] SUMMARY passed=14 failed=0
```

All fifteen negatives exited 1, including `anyopen`:
`deliberate retired FSG6e any-OPEN candidate rule detected`. All nineteen
FSG1–FSG6e regression suites stayed green, and FSG6a's seven, FSG6b's eight,
FSG6c's nine, FSG6d's eleven and FSG6e's fourteen negatives all still exit 1.

Rule behaviour against the preserved FSG6e **development controls** (not
validation): all five productive moves remain eligible — (45,0,1), (41,1,17),
(31,5,14), (61,1,1), (60,3,20) — and both pathological survivors are rejected,
**(11,3,82) resolved 85 of 96 raw** and **(8,1,16) resolved 17 of 25 raw**, each
of which the retired any-OPEN rule would still have admitted. Ties: (9,4,4)
allowed, (8,4,4) rejected.

### Closed-loop preflight — DESIGN/PLUMBING ONLY, NOT A SCIENTIFIC RESULT

```text
consensus_up_right  (-8,-7)(-3,-2)(+2,+3)(+7,+8)(+12,+8)(+12,+3)  STOP no_frontier
  raw 149,121,109,130,117,128 | OPEN 84,59,66,57,43,7 | cands 5,3,4,3,2,0
  ideal coverage 1.0000, pitch span 15.0, consensus rejections 2 (final state 0)
consensus_down_left (+8,+7)(+3,+2)(-2,-3)(-7,-8)(-12,-8)          STOP no_frontier
  raw 138,111,111,154,139 | OPEN 75,78,86,72,27 | cands 3,3,5,3,0
  ideal coverage 0.9991, pitch span 15.0, consensus rejections 1 (final state 1 — load-bearing)
horizontal-only ideal max 0.4503 | max strip chord error 0.1697 mm
```

### Smoke — COMPLETED, exit 2 (numerical only)

`consensus_up_right` / 1237 / small: 6 fixations, `max_fixations`, coverage
88.05%, median 13.862 mm, p95 34.420 mm. State raw 288–312 with OPEN 192→104 and
consensus rejections 0,2,1,1,0,2 — **the new rule already fires on real data at
small profile**. FAIL lines: final median, final p95, termination, `fix_00`–
`fix_05` object measurement coverage (0.826–0.897), `fix_01`–`fix_05` too few
overlap matches, final coverage. All resolution-scaled. No exception, so full was
not blocked.

### The four full trials — ALL PASS

| Trial | Trajectory | Fix | Term | Final cov. | Median | P95 | Radial | Status |
|---|---|---:|---|---:|---:|---:|---:|---|
| up_right/1237 | (-8,-7)(-3,-2)(2,3)(7,8)(12,8)(12,3) | 6 | `no_frontier` | 99.402% | 4.324 mm | 15.598 mm | +0.314 mm | **PASS** |
| up_right/1291 | (-8,-7)(-3,-2)(2,3)(7,8)(12,8)(12,3) | 6 | `no_frontier` | 99.439% | 4.309 mm | 15.534 mm | +0.309 mm | **PASS** |
| down_left/1237 | (8,7)(3,2)(-2,-3)(-7,-8)(-12,-8) | 5 | `no_frontier` | 98.517% | 4.382 mm | 14.224 mm | -2.855 mm | **PASS** |
| down_left/1291 | (8,7)(3,2)(-2,-3)(-7,-8)(-12,-8) | 5 | `no_frontier` | 98.535% | 4.386 mm | 14.235 mm | -2.885 mm | **PASS** |

Every fail list empty. Fixation count 5–6 (gate 4–6); every termination
`no_frontier`; pitch span 15.0° and yaw span 20.0° on all four; every move one
5-degree lattice step; no repeats. Per-patch object measurement coverage
**0.9053–0.9547** (gate >=0.90). Post-seed overlap 11,034–20,223 matched
(>=5,000), median 1.81–3.51 mm (<=10), p95 5.74–10.54 mm (<=25), every replay
idempotent, largest coverage decrease 0.00 pp. Coverage gain 60.91–62.21 pp
(>=35). Maps 76,326–82,703 surfels, all pure instance 141, 28,276–33,969
multi-look (>=5,000). Every nonterminal selected candidate had >=8 OPEN support
**and** strict OPEN-majority consensus.

Frontier state per fixation (raw / MAP / BOUNDARY / OPEN / accepted candidates /
before consensus / consensus-rejected):

```text
up_right/1237  (229,0,90,139,5,5,0) (214,3,112,99,4,6,2) (241,15,101,125,4,6,2) (217,5,116,96,3,3,0) (178,1,102,75,2,2,0) (187,1,169,17,0,0,0)
up_right/1291  (228,0,90,138,5,5,0) (227,1,116,110,5,7,2) (245,18,102,125,4,6,2) (214,5,113,96,3,3,0) (177,2,99,76,2,2,0) (189,1,170,18,0,2,2)
down_left/1237 (182,0,77,105,3,3,0) (214,26,60,128,4,5,1) (225,30,45,150,5,6,1) (211,9,108,94,3,5,2) (167,2,121,44,0,1,1)
down_left/1291 (180,0,78,102,3,3,0) (218,27,62,129,4,6,2) (231,33,51,147,5,6,1) (211,9,108,94,3,4,1) (165,0,120,45,0,1,1)
```

### Selected candidates

```text
up_right/1237  s0 (-3,-2)  OPEN 51 raw 51 MAP 0 BND 0  res 0  51>0  score 18.443 area 106.326 corridor 1.0000
               s1 (+2,+3)  OPEN 43 raw 53 MAP 1 BND 9  res 10 43>10 score 16.667 area 106.724 corridor 0.9966
               s2 (+7,+8)  OPEN 55 raw 73 MAP 4 BND 14 res 18 55>18 score 16.122 area 119.140 corridor 0.6628
               s3 (+12,+8) OPEN 60 raw 66 MAP 1 BND 5  res 6  60>6  score 16.705 area 108.694 corridor 0.7257
               s4 (+12,+3) OPEN 68 raw 81 MAP 1 BND 12 res 13 68>13 score 23.990 area  75.138 corridor 0.5642
down_left/1237 s0 (+3,+2)  OPEN 38 raw 38 MAP 0 BND 0  res 0  38>0  score 13.885 area  94.789 corridor 1.0000
               s1 (-2,-3)  OPEN 50 raw 62 MAP 9 BND 3  res 12 50>12 score 16.922 area  93.472 corridor 1.0000
               s2 (-7,-8)  OPEN 37 raw 52 MAP 10 BND 5 res 15 37>15 score 11.906 area  95.402 corridor 0.8562
               s3 (-12,-8) OPEN 76 raw 83 MAP 0 BND 7  res 7  76>7  score 20.675 area  93.627 corridor 0.4126
```

Every selected candidate is a large OPEN majority (38:0 to 76:7). The consensus
rule never blocked a productive move.

### Candidate consensus is load-bearing on real acquisitions

**20 consensus rejections across the four trials. Every one had corridor
`allowed=True` and `OPEN >= 8`, i.e. every one would have been ACCEPTED by the
retired FSG6e rule.** Three of the four trials terminate *because of* consensus:

```text
up_right/1237  rejections 4 | final step: before 0, rejected 0  -> terminated by FSG6e state alone
up_right/1291  rejections 6 | final step: before 2, rejected 2  -> TERMINATION CAUSED BY CONSENSUS
down_left/1237 rejections 5 | final step: before 1, rejected 1  -> TERMINATION CAUSED BY CONSENSUS
down_left/1291 rejections 5 | final step: before 1, rejected 1  -> TERMINATION CAUSED BY CONSENSUS
```

The FSG6e pathology pattern is caught explicitly on fresh data:

```text
up_right/1237  s1 (-3,-7)   OPEN 11 resolved 85 of 96 raw   corridor 0.4464 allowed  -> REJECTED
up_right/1291  s1 (-3,-7)   OPEN 10 resolved 90 of 100 raw  corridor 0.3900 allowed  -> REJECTED
up_right/1291  s5 (+7,-2)   OPEN  8 resolved 15 of 23 raw   corridor 0.4944 allowed  -> REJECTED  [OPEN exactly at the frozen minimum 8]
down_left/1237 s3 (-7,-13)  OPEN  8 resolved 100 of 108 raw corridor 0.2243 allowed  -> REJECTED  [OPEN exactly 8, new-area 112.3 — the FSG6e off-ribbon shape]
down_left/1237 s3 (-12,-13) OPEN  9 resolved 18 of 27 raw   corridor 0.4585 allowed  -> REJECTED  [new-area 126.1, the largest on offer]
down_left/1237 s4 (-12,-3)  OPEN 40 resolved 40 of 80 raw   corridor 0.3648 allowed  -> REJECTED  [EXACT TIE — resolved, not open; this rejection terminates the run]
```

`up_right/1237 s1 (-3,-7)` at **11 OPEN against 85 resolved** is the same shape as
FSG6e's `closure_up_right/1123` final survivor (11,3,82). `down_left/1237 s3
(-7,-13)` at **8 OPEN, 100 resolved, new-area 112.3** is the same shape as
FSG6e's `closure_up_right/1181` off-ribbon move (8,1,16) that carried that
trajectory off the surface. Both are now rejected before ranking, and neither
fixture ever leaves the ribbon.

The exact-tie rejection at `down_left/1237 s4` (40 OPEN vs 40 resolved) is the
prospectively specified tie rule deciding a real termination.

### All FAIL lines, verbatim

```text
consensus_up_right/1237:  (none)
consensus_up_right/1291:  (none)
consensus_down_left/1237: (none)
consensus_down_left/1291: (none)
[fsg6f-compare] FSG6F_INCREMENT6_PASS   trial_passes 4/4, fails (none), exit 0
```

### Aggregate

```text
status FSG6F_INCREMENT6_PASS | trial_passes 4/4 | mean_final_coverage 0.989731
pitch_span_range 15.0-15.0 deg | surface median 4.309-4.386 mm
p95 14.224-15.598 mm | signed radial -2.885 to +0.314 mm
```

### Visuals and PLY

`growth.png` and `growth_truth.png` show both fixtures sweeping their diagonals
cleanly — `consensus_up_right` 38.5 -> 56.3 -> 73.2 -> 96.4 -> 98.6 -> 99.4% and
`consensus_down_left` 36.3 -> 54.2 -> 75.1 -> 98.3 -> 98.5% in five looks — with
no fixation leaving the ribbon. `coverage_3d_frontier.png` shows all four curves
rising monotonically and saturating. Every `surface_map.ply` carries
`comment fixed head frame H`, has **no `element face`** (no meshing),
76,326–82,703 vertices, and independent reads give median cylinder radius
**0.75043–0.75044 m against a true 0.750** and **0.70797–0.70800 m against a true
0.710** — +0.4 mm and −2.0 mm.

### Cost

Smoke run 17.4 s (loop 17.25 s, Blender 11.84 s) / eval 6.8 s, 78,643,200
samples. Full runs 1m5.5s, 1m6.2s, 1m4.4s, 1m5.1s (loop 65.37/66.04/64.33/64.95 s,
Blender 29.0–35.1 s each); 1,258,291,200 samples for each six-fixation
`consensus_up_right` trial and 1,048,576,000 for each five-fixation
`consensus_down_left` trial, **4,613,734,400 total** — under the 5,033,164,800 a
six-fixation set would have cost, because consensus ended two trials a fixation
early. Aggregation under a second. Batch class throughout.

### Code fixes

**None.** No source file was modified; the increment changed documentation only.

### Outcome

Per §Outcome rule, **Increment 6 is CLOSED** and the next experiment is
**AUTHORIZED BUT NOT IMPLEMENTED**.

Scope, stated narrowly as §Interpretation discipline requires: on fresh single
convex visible curved surfaces with oracle instance segmentation, persistent
three-state 3D frontier memory can be aggregated into candidate-level consensus
strongly enough to reject mostly-resolved actions while preserving useful active
exploration and truth-free `no_frontier` termination. It does **not** establish
self-occlusion reasoning, hidden-surface discovery, multiple objects, free head
motion, learned gaze, optimality or calibrated uncertainty. The six-increment
route to this result — FSG6a's eye-asymmetric veto, FSG6b's conjunctive corner,
FSG6c's one-component licensing, FSG6d's non-terminating raw frontier and
FSG6e's minority-OPEN survivors — is preserved in full as five formal FAIL
records.
