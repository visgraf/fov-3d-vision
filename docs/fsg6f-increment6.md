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

Prospective section intentionally left blank for workstation execution.
