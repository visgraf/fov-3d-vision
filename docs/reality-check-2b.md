# Reality Check 2b — learn from an empty look

## Status

Measured. Both full continuations were acquired once each on the workstation on 2026-09-21;
see Results below. Final status `REALITY2B_COMPLETE`.

## Question

Reality Check 2 established that continuing beyond the old six-look interruption is useful: the saved small-profile continuation increased visible target coverage from about 0.528 to 0.790 before frozen FSG6f selected an off-target gaze and the inherited `<100 target points` guard raised a runtime exception.

Reality Check 2b asks one smaller question:

> If an exploratory fixation finds essentially no target surface, can the observer treat that completed binocular observation as negative evidence, recover, and continue until frozen FSG6f itself says `no_frontier`?

This is not a new ranking, a new frontier rule, or a new quality gate.

## Scientific change

Exactly one semantic change is authorized relative to Reality Check 2.

The condition that previously aborted the run,

```text
reconstructed target point count < 100
```

is retained unchanged but reinterpreted.

For such a fixation:

1. the physical gaze is recorded as visited;
2. the completed left/right instance masks and raw-support arrays are appended to the persistent observation history;
3. zero target points are fused and the persistent map must remain unchanged;
4. the unchanged FSG6f controller is called again using that new history.

This allows FSG6f's already-existing `BOUNDARY_RESOLVED` mechanism to learn from a place where the object was expected but not found. No evaluator truth enters the prediction path.

## Frozen pieces

- exact Reality Check 1 scene and texture;
- exact saved Reality Check 1 six-look parents, reused without rerender;
- seeds 2111 and 2179;
- fixed head and static scene;
- prescribed 2.10 m vergence;
- FSG1 stereo instrument;
- FSG3 12 mm fusion/hash;
- complete FSG6f frontier/state/consensus/corridor/ranking implementation;
- Reality Check 2's 24-total-fixation engineering watchdog;
- no numerical quality PASS threshold.

`tools/reality2_render_fix.py` is reused directly; no new renderer is introduced.

## Stopping semantics

Scientific stop:

```text
frozen FSG6f -> no_frontier
```

Engineering guard:

```text
24 total fixations
```

Reaching the watchdog is descriptive, not a tuned quality failure.

## Prospective schedule

Development smoke:

- exact saved Reality Check 1 `small` parent for seed 2111, if present;
- continue under the new empty-observation semantics;
- a genuine implementation/provenance/runtime defect blocks full acquisition;
- a poor numerical result does not.

Full observations, each once:

- exact saved Reality Check 1 `full-seed2111` parent;
- exact saved Reality Check 1 `full-seed2179` parent.

Do not replace a seed, alter a gaze, tune a threshold, change ranking, enlarge the watchdog, or rerender after a numerical disappointment.

## What to report

For each seed report the entire continuation trajectory, coverage by fixation, map size, support, metric surface statistics, termination reason, and all integrity checks.

For every empty target observation report:

- fixation step and gaze;
- reconstructed target-point count and target measurement fraction;
- confirmation that the map before/after the empty look is identical;
- the policy decision immediately after the empty look;
- whether a later fixation returned to useful target surface;
- subsequent coverage gain.

The central descriptive outcomes are:

1. whether an empty look can resolve the false frontier and allow recovery;
2. whether frozen FSG6f eventually reaches `no_frontier`;
3. whether the two stochastic trajectories end in comparably useful reconstructions;
4. whether geometry remains coherent as additional looks accumulate.

## Interpretation

A bad exploratory fixation is allowed. The experiment tests whether the observer can incorporate the negative observation and recover rather than requiring every saccade to be correct in advance.

## Results

Run on the workstation 2026-09-21 (Blender 5.2.1 LTS headless, Cycles, OPTIX on
RTX 4090, driver 595.84; host-side scripts under `.venv/bin/python` 3.12.3 per
the working agreement).  Each record acquired **once**.

**Status: `REALITY2B_COMPLETE`.  Both full records are structurally valid, every
`integrity_fails` list is empty, and no FAIL line was produced anywhere.  Both
terminated by the scientific rule, `no_frontier` - neither reached the watchdog.
The Reality Check 2 blockage is resolved: it was an artifact of treating negative
perception as a runtime error.**

### Provenance and frozen-source audit

`git status --short` empty; HEAD `e962ff6` on `main`; **`27cfcc2` (the Reality
Check 2 result) is an ancestor of HEAD**.  `git diff --name-status HEAD~1 HEAD`
is exactly the seven authorized files, all `A`: `tools/reality2b_{public,run,
eval,compare}.py`, `tools/dev/check_reality2b.py`, `docs/reality-check-2b.md`,
`docs/reality-check-2b-checks.md`.

`git diff HEAD~1 HEAD` restricted to every FSG1/FSG3/FSG6f source, the renderer,
`fsg_scene.py`, `fsg_validation_render.py`, `rig.py`, `bl_common.py`,
`requirements-fsg.txt` **and every Reality Check 1 and Reality Check 2 source**
is **empty**, confirmed additionally by per-file sha256 against `27cfcc2` - all
SAME: `fsg_stereo_supported` 683ae91eaca7b6af, `fsg_stereo_hdr`
67e2ec4667bcc179, `fsg_stereo` faebf0f1b3acbfde, `fsg_evaluate`
a5134b8d8537714d, `fsg_geometry` d9537d8ebc23b60c, `fsg3_surface_map`
1b9dbeb873105ec9, `fsg6f_public` c79f58c9b51f33d4, `fsg6f_frontier`
d636c9405d719916, `fsg6f_run` f2d4bdd54b8d395f, `fsg_render` 681237fa8533b7cc,
`fsg_scene` 1f410577c1103e01, `fsg_validation_render` f18883e1e2764dd7, `rig`
dff43ec0cd9d5047, `bl_common` aa7a56e8cd4988cb, `reality1_public`
d2b00211021ff65d, `reality1_run` c0d4f18a682fd9fe, `reality1_eval`
91720f42932b463c, `reality1_scene` b4392230292bb51c, `reality1_render_fix`
bdc068ad931e1072, `reality2_public` c7e7bd44d1a28de3, `reality2_run`
2b846a3413500dfc, `reality2_eval` ebfaa9e036db224b, `reality2_render_fix`
9f1433d189fbcbb5, `check_reality1` b057b1d307aebfde, `check_reality2`
ca832846a44b88bc.

### Checks - all before acquisition

`py_compile` clean on all five new modules.

```
[reality2b-policy] PASS exact_parent_continuation=true frozen_fsg6f=true empty_look_is_evidence=true empty_fuses=false scientific_stop=no_frontier watchdog_total=24 quality_gated=false
[reality2b-check] SUMMARY passed=7 failed=0
```

All ten deliberate negatives exit 1 for their own named reasons: `abortempty`,
`skipempty`, `dropgaze`, `fuseempty`, `sixlimit`, `rerenderparent`,
`policycopy`, `truth`, `qualitygate`, `watchdoggate`.  Prior suites green with
their negative sets still firing: `[reality1-check] passed=6 failed=0` (6/6
negatives exit 1), `[reality2-check] passed=7 failed=0` (7/7), `[fsg6f-check]
passed=14 failed=0` (**15/15** negatives exit 1).

### Smoke - `small` seed 2111, run once

`REALITY2B_OBSERVATION_COMPLETE`, `integrity_fails: []`, 33 s run + 47 s eval,
104,857,600 new samples.  **14 total fixations (8 new), one empty observation at
step 13, termination `no_frontier`.**  Coverage 0.5276 -> 0.7904 (+0.2627),
median/P95 16.705 / 46.167 mm, 12,286 multi-look surfels, worst overlap median
5.96 mm, map pure in {141}, 14/14 unique gazes, every fused patch idempotent.
Structurally clean, so full acquisition was authorized.  **Nothing was changed
in response to it.**

### The two full continuations, each acquired once

| | seed 2111 | seed 2179 |
|---|---|---|
| status | `REALITY2B_OBSERVATION_COMPLETE` | `REALITY2B_OBSERVATION_COMPLETE` |
| `integrity_fails` | `[]` | `[]` |
| total fixations / newly acquired | **13** / 7 | **16** / 10 |
| termination | **`no_frontier`** | **`no_frontier`** |
| watchdog reached | False | False |
| empty observations | 1 (step 12) | 2 (steps 14, 15) |
| parent gazes (unchanged, not rerendered) | (-6,-4) (-1,-9) (4,-9) (9,-9) (14,-4) (14,1) | (-6,-4) (-1,1) (4,6) (9,11) (14,11) (14,6) |
| continuation gazes | (14,6) (9,11) (4,11) (-1,11) (-6,11) (-11,11) **(-16,6)** | (14,1) (14,-4) (14,-9) (9,-9) (4,-9) (-1,-9) (-6,-9) (-11,-9) **(-16,-4)** **(-16,1)** |
| coverage at look 6 -> final | **0.5345 -> 0.7984** | **0.7329 -> 0.8834** |
| gain after look 6 | **+0.2639** | **+0.1505** |
| approx surface median / P95 | **5.878 mm** / 18.599 mm | **5.812 mm** / 18.858 mm |
| measurement fraction min / median | 0.8466 / 0.8740 (fused looks) | 0.0629 / 0.8555 (min is an empty look) |
| worst overlap median / P95 | 3.025 mm / 8.534 mm | 2.897 mm / 8.759 mm |
| map points | 117,567 | 138,010 |
| multi-look surfels (support >= 2) | **48,350** (41.1%) | **57,571** (41.7%) |
| new samples / total | 1,468,006,400 / 2,726,297,600 | 2,097,152,000 / 3,355,443,200 |
| wall: run / eval (Blender part) | 94 s / 176 s (59.8 s) | 135 s / 296 s (86.8 s) |

Coverage curves - seed 2111: 0.2603, 0.3273, 0.4000, 0.4267, 0.4764, **0.5345**,
0.5507, 0.6125, 0.6797, 0.7537, 0.7984, 0.7984, 0.7984; seed 2179: 0.2604,
0.5141, 0.6745, 0.7034, 0.7034, **0.7329**, 0.7811, 0.8092, 0.8101, 0.8675,
0.8834, 0.8834, 0.8834, 0.8834, 0.8834, 0.8834.  (Bold is the Reality Check 1
stop.)

Per-new-look new-point fraction - seed 2111: 0.154, 0.598, 0.442, 0.433, 0.314,
**0.005**, then the empty look; seed 2179: 0.373, 0.268, **0.007**, 0.521,
0.143, **0.006**, **0.007**, **0.003**, then two empty looks.  **Five of the
seventeen new fused looks returned under 1% new points** - the observer keeps
paying full render cost for re-measurement near the end of each sweep.  That is
reported, not gated.

Aggregate, `previews/reality2b/full-comparison/comparison.json`:
**`[reality2b-compare] REALITY2B_COMPLETE`**, `structural_fails: []`,
`quality_gated: false`, terminations `["no_frontier", "no_frontier"]`, fixation
counts [13, 16], empty counts [1, 2], final coverage range
[0.7984, 0.8834] with an absolute seed difference of **0.0850**, surface median
range [5.812, 5.878] mm, P95 range [18.599, 18.858] mm.

### Every empty observation, in full

**seed 2111, step 12, gaze (-16.0, +6.0)** - 0 reconstructed target points, 0
oracle reference pixels, 0 valid (measurement fraction undefined, not merely
low).  Map before/after **identical**: 117,567 -> 117,567 points, support sum
173,427 -> 173,427, and `xyz_h`, `rgb`, `instance_id`, `support_count` and
`provenance_mask` all bitwise equal, re-verified independently of the evaluator.
Association record `fused: false, empty_target_observation: true, new: 0,
matched: 0`.  **Immediate policy response: `stop: True, reason: no_frontier`,
zero candidates offered**, with the observation retained
(`observation_was_empty_target: true`).  No later fixation, so no subsequent
gain.

**seed 2179, step 14, gaze (-16.0, -4.0)** - 25 target points from 317 reference
pixels (measurement fraction 0.0789).  Map identical: 138,010 -> 138,010 points,
support sum 214,527 -> 214,527.  **Immediate policy response: `stop: False,
reason: continue, next_gaze_deg: (-16.0, +1.0)`** - two candidates survived
consensus and corridor, `(-16,+1)` area 123.71 / score 10.19 / OPEN 23 / MAP 1 /
BND 3, and `(-11,+1)` area 63.71 / score 5.78 / OPEN 17 / MAP 1 / BND 0.  **This
is the recovery behaviour the experiment was built to test: the observer
incorporated a near-empty look and kept going rather than failing.**

**seed 2179, step 15, gaze (-16.0, +1.0)** - 11 target points from 175 reference
pixels (0.0629).  Map identical again, same counts.  **Immediate policy
response: `stop: True, reason: no_frontier`, zero candidates.**

A precise note on the evaluator's `recovered_after_first_empty` flag, which
reads `false` for both seeds: it is defined as *a later look that actually fused
>= 100 target points*.  Neither seed had one, because in both cases the empty
looks came at the very end of the trajectory.  It does **not** mean the policy
failed to continue - seed 2179 demonstrably did continue after its first empty
look.  Reported both ways here so the flag is not misread.

### Structural integrity, re-verified independently of the evaluator

Both records: parent `maps/map_00..05.npz` **byte-identical** to the saved
Reality Check 1 source; **no parent acquisition directory recreated** - not one
of the twelve Reality Check 1 views was rerendered; `truth_opened` **False**;
`fixed_head` and `static_scene` **True**; final map instance ids exactly
**{141}**; **every fused patch `idempotent_replay` True** (12 of 12 for seed
2111, 14 of 14 for seed 2179) with the empty entries correctly carrying
`fused: false` and no idempotence claim; **all gazes unique** (13/13 and 16/16);
frozen policy `FSG6f-candidate-frontier-consensus-v1` and instrument
`FSG1-HDR-SGBM-one-original-update-original-validity-v1`; fusion
{0.012, 0.012}, the `<100` limit and the 24-look watchdog unchanged.

### Two-seed comparison

Both reach `no_frontier`; neither reaches the watchdog.  The fixation counts
differ by **3** (13 vs 16) and the trajectories are still completely different -
seed 2111 sweeps the top row right-to-left, seed 2179 sweeps the right column
down then the bottom row right-to-left - yet **the final reconstructions are
much more comparable than Reality Check 1's were**.  The final coverage gap
**narrowed from 0.1984 at look 6 to 0.0850**, the surface medians differ by
0.066 mm (5.812 vs 5.878) and the P95s by 0.26 mm, and both maps are ~41%
multi-look.  The seed that was behind gained more (+0.2639 against +0.1505).
**Seed divergence became largely an efficiency difference rather than a quality
difference** - that is the descriptive answer, with no threshold attached.

### Visual reading (descriptive; not a quality score)

**Empty and off-target looks are plainly visible and are exactly where the
numbers say.**  Seed 2111's `fix_12` at (-16,+6) shows grey wall and a blue side
prop with no cloth anywhere in frame.  Seed 2179's `fix_14` at (-16,-4) is
dominated by the blue prop and wall with only a sliver of cloth at the top edge -
the visual counterpart of 25 target points out of 317 reference pixels.  Its
`fix_13` at (-11,-9), the last productive look, catches the cloth's bottom-left
corner over the brown tabletop and returned 0.26% new points.

**Does the observer return to the target afterwards?**  Seed 2179 did: after the
near-empty `fix_14` the policy chose another gaze and looked again.  It did not
land back on useful surface - the next look was also near-empty - and then
frozen FSG6f declared `no_frontier`.  Seed 2111 never had the chance; its single
empty look immediately resolved the frontier.

**Do the added looks fill meaningful holes or merely wander?**  They fill.  Both
growth sequences show the map extending into genuinely unvisited cloth on every
fused look, not re-covering old ground: seed 2111 climbs from the bottom band
into the whole top row it had never seen (y extent -0.319..0.261 at look 6 ->
-0.319..**0.400** at the end, against a true target span of -0.326..0.405), and
seed 2179 wraps the right edge and the entire bottom row.  The wandering, where
it exists, is at the end - the five sub-1% looks and then the empty ones.

**Is geometry coherent?**  Yes, and it improved.  Sliced into +/-12 mm horizontal
bands against the exported truth mesh, the points track the true non-periodic
undulation closely across every band, including the top bands neither record
reached in Reality Check 1, with a few millimetres of scatter and **no band
where the cloud departs from the surface**.  Multi-look coverage roughly doubled
in proportion (27.9% -> 41.1% for seed 2111, 24.3% -> 41.7% for 2179), which is
visible as the denser blue in the band plots.  Depth-coloured, seed 2179's final
map reads as one continuous cloth with a near region across the top and a far
valley through the middle.  **No gross wrong-depth region appeared** in either
record; the central 98% of reconstructed depths stays inside the true
2.083-2.166 m span.

**Does termination look sensible?**  Sensible in mechanism, **premature in
result**.  Both stopped by their own rule rather than by exhaustion, and both
stopped immediately after an empty look resolved the frontier in that direction -
that is the mechanism working.  But seed 2111's final map is visibly a **ring**:
the observer swept the perimeter and declared `no_frontier` with a large
unvisited rectangular hole still in the middle of the cloth, which is most of the
missing 20%.  Seed 2179 ends far more complete, with one small square hole in the
lower right.  So `no_frontier` here means "no open frontier reachable from the
perimeter I walked", not "the surface is finished".  That is an observation about
the frozen frontier/consensus rule, and it is deliberately not turned into a
PASS/FAIL.

### Structural FAIL lines

**None.**  No FAIL line was produced by `[reality2b-check]`, `[reality1-check]`,
`[reality2-check]`, `[fsg6f-check]`, either evaluator, the comparator, or any
inline runtime assertion.

### Code fixes

**None.**  No implementation defect was found.  Every failure mode the
authorization listed was checked against the acquired records and none occurred:
the zero-point patch at seed 2111 step 12 serialized, visualized and was
evaluated without incident; both empty observations are present in the gaze list
and in the binocular observation history before `choose_next` was called, proven
by the policy trace carrying `observation_was_empty_target: true` at those steps;
every no-fusion step left the persistent map bitwise unchanged, re-verified
outside the evaluator; the evaluator correctly requires idempotence only of
patches that were actually fused; and the parent-state provenance is exact, with
byte-identical parent maps and no rerendered parent view.  No source file was
modified.
