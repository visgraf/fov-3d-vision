# Stage II / Scene-1c — Certified composition of active object reconstructions

## Question

Does active reconstruction compose across several objects under the already-settled fair scene scheduler?

More precisely: if each object placement is **prospectively certified** to be solvable by the frozen FSG6f controller within its unchanged six-look budget, in the exact complete three-object rendering context, can the unchanged Scene-1b fair scheduler interleave those object processes and complete the whole scene within the unchanged 18-look scene budget?

Scene-1a and Scene-1b remain preserved formal FAILs. Scene-1a established the multi-object memory/identity substrate but exposed starvation under unconstrained area-first scheduling. Scene-1b eliminated starvation decisively, but its three objects did not all independently reach `no_frontier` inside six looks, so budget sufficiency could not be separated cleanly from component solvability.

## Frozen substrate

Scene-1c introduces **no new runtime perception or scheduling mechanism**. Frozen:

- FSG1 stereo instrument: `FSG1-HDR-SGBM-one-original-update-original-validity-v1`;
- FSG3 12 mm surfel association / hash cell;
- all FSG6f frontier extraction, persistent OPEN/MAP_RESOLVED/BOUNDARY_RESOLVED state, candidate consensus, projected binocular corridor, ranking and 5-degree lattice;
- Scene-1b least-autonomous-service eligibility and its within-class area / frontier-score / instance-ID ordering;
- six target fixations maximum per object;
- 18 physical fixations maximum for three objects;
- fixed head, static scene, 2.10 m vergence;
- oracle instance segmentation;
- opportunistic all-known-object processing from every ensemble fixation;
- global physical no-revisit;
- scene completion only when every object independently reports `no_frontier`;
- every Scene-1b numerical per-object and scene-level acceptance gate.

`scene1c_policy.py` imports the frozen Scene-1b policy layer rather than reproducing it. Scene-1b in turn imports FSG6f.

## New experimental protocol: certify the actors before the ensemble

For every `(fixture, seed, object)` triple, run a full-profile **component certification control** before any Scene-1c ensemble acquisition.

A component control:

1. renders the **complete three-object fixture** with exactly the same renderer, geometry, textures, seed and target object's prescribed seed gaze used by the later ensemble;
2. reconstructs only the nominated object;
3. lets the unchanged FSG6f controller choose that object's subsequent gazes;
4. allows at most the unchanged six target looks including the seed;
5. sees no evaluator geometry or truth during prediction;
6. is evaluated afterward with exactly the Scene-1b per-object gates and must terminate `no_frontier`.

There are `2 fixtures x 2 Monte-Carlo seeds x 3 objects = 12` prospectively fixed full component controls. **All twelve must pass before the ensemble stage is allowed to run.** A failed actor is not replaced, resized, reseeded, or tuned. If certification fails, Scene-1c stops with `SCENE1C_COMPONENT_CERTIFICATION_FAIL` and no ensemble full acquisition is run.

The certification result is an experimental authorization condition only. It is not supplied to the scene policy as a runtime input.

## Fresh scenes

Two fresh non-mirror base scenes are used:

- `cert_triad_e`;
- `cert_triad_f`.

Each contains three compact convex cylindrical ribbons, instance IDs 201, 202 and 203, arranged in angularly disjoint regions. The shapes are intentionally in the already successful FSG6f qualitative family; Stage II is not asking a new geometry question here. Front surfaces remain near the validated 2.10 m working distance.

Fresh Monte-Carlo seeds: **1847, 1901**.

Each object has one prescribed partial seed. Evaluator-only geometry also carries a three-look 5-degree-lattice **box-coverage witness** beginning at that seed. Every witness reaches at least 98% ideal angular coverage while using only three of the six available object looks. This is only a prospective geometry sanity check; it is neither a policy prediction nor the component certification. The actual certification is the full rendered FSG6f control above.

## Prospective component-certification gates

For each of the twelve full controls:

- at least one autonomous post-seed target fixation;
- targeted patch object-measurement fraction >= 90%;
- targeted post-seed overlap matched points >= 5,000;
- targeted post-seed overlap median <= 10 mm, P95 <= 25 mm;
- idempotent fusion replay for every patch;
- final map contains only the nominated object's instance ID;
- >= 5,000 multi-look surfels;
- final analytic surface median <= 10 mm, P95 <= 30 mm;
- final truth coverage >= 90%;
- final coverage gain over the seed-state map >= 25 percentage points;
- no physical fixation repeats;
- <= 6 total target looks including the seed;
- final FSG6f state and termination are both `no_frontier`.

The twelve-control aggregate must return `SCENE1C_COMPONENT_CERTIFICATION_PASS` before the ensemble proceeds.

## Prospective ensemble gates

Unchanged from Scene-1b:

- the first three fixations are exactly the prescribed seeds, one per object;
- every later target/gaze decision is autonomous;
- every decision obeys the frozen least-service-first Scene-1b scheduler;
- every object receives autonomous post-seed attention;
- at least two post-seed attention switches occur;
- every fused patch replays idempotently and every final object map is pure;
- the same per-object measurement, overlap, support, surface-error, coverage and coverage-gain gates listed above hold;
- no physical fixation repeats;
- no object exceeds six target looks;
- total scene fixations <= 18;
- every final object policy state is `no_frontier`;
- final scene termination is `scene_complete`;
- all four fresh full ensemble trials pass.

Opportunistic non-target fusion remains part of the Scene-1b substrate but is descriptive rather than a gate.

## Composition diagnostic

For each `(fixture, seed, object)`, compare the object's target-gaze sequence in the certified single-object control with that object's target subsequence inside the ensemble. Exact equality is **not** a gate: interleaved observations enter all object histories by design and can legitimately alter later FSG6f state. Report the common prefix and first divergence, if any. This diagnostic distinguishes simple temporal interleaving from a genuinely scene-induced interaction.

## Decision rule

Three outcomes are possible and fixed prospectively:

1. If any of the twelve component controls fails, report `SCENE1C_COMPONENT_CERTIFICATION_FAIL`, preserve the controls, do not run the full ensemble, and stop for Luiz/Chat.
2. If all components certify but any of the four ensemble trials fails, report `SCENE1C_STAGEII_FAIL`. This is evidence that individually solvable active object processes did not compose under the frozen scene substrate.
3. Only if all twelve component controls and all four ensemble trials pass may the aggregate report `SCENE1C_STAGEII_PASS` and Scene-1c close.

Do not increase either budget, change an actor after certification, alter the scheduler, retune FSG6f, change a fixture/seed/gate, or rerender after a numerical miss.

## Deferred

Object discovery, object-object occlusion, semantic reasoning, moving objects and moving observers remain later Stage-II/future-stage questions.

## Results

Run 2026-09-20 on the workstation. HEAD before `7c59ac6`, clean `main`,
`3f4b490` confirmed an ancestor.

**Final status: `SCENE1C_COMPONENT_CERTIFICATION_FAIL` — 1 of 12 component
controls certified. Per the prospective decision rule, the ensemble stage was
NOT run: no ensemble smoke, no full ensemble trials, no ensemble aggregate.** All
twelve controls are preserved. Scene-1c is not closed.

### Preservation and frozen source

`git diff --name-status 3f4b490 HEAD` shows exactly **thirteen files, all
additions**. `git diff 3f4b490` over the FSG1 stereo modules,
`fsg3_surface_map.py`, every FSG6/6b/6c/6d/6e/6f module, every FSG7a module,
**every `scene1a_*` and `scene1b_*` module** (including both dev checks),
`rig.py`, `bl_common.py` and `requirements-fsg.txt` is **empty**. Scene-1a and
Scene-1b remain preserved formal FAILs, unedited and unrelabelled.

All five required verifications, measured:

1. `scene1c_policy.py` imports `scene1b_policy as frozen_scene_scheduler`, has
   **zero** direct `import fsg6f` lines, and **aliases rather than reimplements**
   every scheduler symbol — `remap_instance`, `remap_observation`,
   `proposal_rank_key`, `select_proposal`, `propose_for_object`,
   `choose_scene_action`, `split_visible_object_masks`, `is_global_repeat`.
2. `scene1b_policy.py` still imports `fsg6f_public` and `fsg6f_frontier`, and
   shows no diff.
3. `scene1c_certify_run.py:46` and `scene1c_run.py:70` both invoke
   `tools/scene1c_render_fix.py`.
4. Neither prediction runner nor the policy mentions `scene1c_scene`,
   `evaluation_only` or any `witness`; both runners call `compute_once`.
5. Constants equal Scene-1b exactly: `PER_OBJECT_MAX_FIXATIONS` 6,
   `MAX_SCENE_FIXATIONS` 18, `FUSION` {0.012, 0.012}, `TARGETS` identical with
   **no differing keys**, vergence 2.10, objects (201,202,203), instrument ID
   identical. `FROZEN_SCENE_SCHEDULER_ID = Scene1b-least-service-then-area-score-id-v1`,
   `FROZEN_OBJECT_POLICY_ID = FSG6f-candidate-frontier-consensus-v1`.

Environment: `.venv/bin/python` — Python 3.12.3, NumPy 2.2.6, OpenCV 4.13.0,
Pillow 12.3.0; Blender 5.2.1 LTS; NVIDIA GeForce RTX 4090 driver 595.84, OPTIX.

### Checks

```text
[scene1c-scene] PASS fixtures=cert_triad_e,cert_triad_f objects=[201, 202, 203] fixed_head=true static_scene=true witnesses_lt_budget=true
[scene1c-policy] PASS frozen_fsg6f=true frozen_scene1b_scheduler=true fairness=true component_certification=true opportunistic=true
[scene1c-check] SUMMARY passed=10 failed=0
```

All ten negatives exited 1, including `incompletecert`, `schedulercopy` and
`budgetbump`. All twenty-three prior suites stayed green — Scene-1a (8),
Scene-1b (9), FSG6f (14), FSG7a (7) among them — and Scene-1a's seven,
Scene-1b's eight, FSG6f's fifteen and FSG7a's six negatives all still exit 1.

### Design-only preflight — geometry sanity check, NOT a prediction path and NOT the certification

```text
cert_triad_e   bounds yaw x pitch                        seed ideal   3-look witness -> ideal
  201  [-24.052,-5.985] x [+4.092,+11.746]                0.6070      (-19,8)(-14,8)(-9,8)   -> 1.0000
  202  [ -8.604,+8.574] x [-12.938,-4.906]                0.6148      (-4,-9)(1,-9)(6,-9)    -> 1.0000
  203  [ +6.180,+23.816] x [+3.491,+12.370]               0.6131      (11,8)(16,8)(21,8)     -> 1.0000
cert_triad_f
  201  [ -8.681,+8.694] x [-12.231,-3.633]                0.6148      (-4,-8)(1,-8)(6,-8)    -> 1.0000
  202  [-23.712,-6.245] x [+5.147,+12.685]                0.6119      (-19,9)(-14,9)(-9,9)   -> 1.0000
  203  [ +5.554,+22.389] x [+5.448,+12.390]               ~0.61       (10,9)(15,9)(20,9)     -> 1.0000
```

Every witness reaches 1.0000 ideal box coverage using three of six looks. **These
are neither prediction paths nor certification results** — the prediction side
contains no witness reference, asserted by `check_scene1c.py`.

### Component-pipeline smoke

`cert_triad_e` / 1847 / obj201 / small, run 34.1 s exit 0, eval 2.9 s exit 2.
6 looks, `max_object_fixations`, coverage 0.4617 → 0.9591, median 14.840 mm,
P95 40.673 mm, 3,580 multi-look surfels. Integrity all clear —
`truth_opened: false`, `fixed_head: true`, `static_scene: true`,
`complete_three_object_scene_rendered: true`, role
`component_certification_control`, 6/6 unique gazes within the six-look budget,
FSG6f reached only through the frozen Scene-1b layer. Numerical small-profile
exit 2, so the full controls were allowed.

### Twelve full component controls

11,744,051,200 primary camera samples total. **control_passes = 1 / 12.**

| Control | Gazes | Fix | Termination | Cov seed→final (gain) | Median | P95 | sup>=2 | Pure | Status |
|---|---|---:|---|---|---:|---:|---:|---|---|
| e/1847/201 | (-19,8)(-14,13)(-9,13)(-4,13)(-4,8)(-9,3) | 6 | `max_object_fixations` | 0.4843→1.0000 (+0.5157) | 6.494 | 18.092 | 14,760 | ✓ | FAIL |
| e/1847/202 | (-4,-9)(1,-14)(6,-14)(11,-14)(11,-9)(6,-4) | 6 | `no_frontier` | 0.5753→1.0000 (+0.4247) | 5.231 | 16.252 | 12,872 | ✓ | FAIL |
| **e/1847/203** | **(11,8)(16,13)(21,13)(21,8)** | **4** | **`no_frontier`** | **0.6153→1.0000 (+0.3847)** | **5.169** | **16.921** | **12,935** | ✓ | **PASS** |
| e/1901/201 | (-19,8)(-14,3)(-9,3)(-4,3)(-4,8)(-4,13) | 6 | `max_object_fixations` | 0.4843→0.9363 (+0.4519) | 6.616 | 17.718 | 14,090 | ✓ | FAIL |
| e/1901/202 | (-4,-9)(1,-4)(6,-4)(11,-9)(11,-14)(6,-14) | 6 | `max_object_fixations` | 0.5753→1.0000 (+0.4247) | 5.597 | 17.017 | 12,763 | ✓ | FAIL |
| e/1901/203 | (11,8)(6,3) | 2 | `no_frontier` | 0.6153→0.6153 (**+0.0000**) | 5.360 | 17.116 | 4,472 | ✓ | FAIL |
| f/1847/201 | (-4,-8)(1,-3)(6,-3)(11,-8)(6,-13) | 5 | `no_frontier` | 0.5740→1.0000 (+0.4260) | 5.629 | 16.557 | 12,023 | ✓ | FAIL |
| f/1847/202 | (-19,9)(-14,14)(-9,14)(-4,14)(-4,9)(-4,4) | 6 | `max_object_fixations` | 0.4844→0.9348 (+0.4504) | 6.184 | 16.821 | 13,461 | ✓ | FAIL |
| f/1847/203 | (10,9)(5,9) | 2 | `no_frontier` | 0.6160→0.6160 (**+0.0000**) | 5.327 | 17.697 | 4,185 | ✓ | FAIL |
| f/1901/201 | (-4,-8)(1,-3)(6,-3)(11,-8)(6,-13) | 5 | `no_frontier` | 0.5740→1.0000 (+0.4260) | 5.637 | 16.590 | 11,970 | ✓ | FAIL |
| f/1901/202 | (-19,9)(-14,4)(-9,4)(-4,9)(-9,14)(-14,14) | 6 | `max_object_fixations` | 0.4846→0.9999 (+0.5154) | 6.288 | 17.770 | 17,609 | ✓ | FAIL |
| f/1901/203 | (10,9)(5,9) | 2 | `no_frontier` | 0.6160→0.6160 (**+0.0000**) | 5.344 | 17.619 | 4,221 | ✓ | FAIL |

**What passed everywhere**: every map pure in its nominated instance ID; every
fused patch idempotent; no physical fixation repeated in any control; no control
exceeded six looks; every surface median (5.169–6.616 mm) and P95
(16.252–18.092 mm) inside the 10/30 mm gates.

**Every FAIL line, verbatim**

```text
e/1847/201 (2): component fix_04 measurement coverage
                component did not independently terminate no_frontier
e/1847/202 (2): component fix_03 measurement coverage
                component fix_04 measurement coverage
e/1847/203 (0): (none)
e/1901/201 (3): component fix_04 measurement coverage
                component fix_03 too few overlap matches
                component did not independently terminate no_frontier
e/1901/202 (4): component fix_03 measurement coverage
                component fix_04 measurement coverage
                component fix_03 too few overlap matches
                component did not independently terminate no_frontier
e/1901/203 (4): component too few multi-look surfels
                component final coverage
                component coverage gain over seed
                component fix_01 measurement coverage
f/1847/201 (1): component fix_03 measurement coverage
f/1847/202 (5): component fix_03 measurement coverage
                component fix_04 measurement coverage
                component fix_03 too few overlap matches
                component fix_04 too few overlap matches
                component did not independently terminate no_frontier
f/1847/203 (4): component too few multi-look surfels
                component final coverage
                component coverage gain over seed
                component fix_01 measurement coverage
f/1901/201 (1): component fix_03 measurement coverage
f/1901/202 (2): component fix_03 measurement coverage
                component did not independently terminate no_frontier
f/1901/203 (4): component too few multi-look surfels
                component final coverage
                component coverage gain over seed
                component fix_01 measurement coverage
```

### Proof the controls rendered the complete three-object scene

Every one of the twelve manifests records
`complete_three_object_scene_rendered: true`, `role:
component_certification_control`, `truth_opened: false`, `fixed_head: true` and
`static_scene: true`. Both runners invoke the identical render script —
`tools/scene1c_render_fix.py` at `scene1c_certify_run.py:46` and
`scene1c_run.py:70`. So the controls are not isolated single-object renders:
each object was certified in the exact complete-scene rendering context the
ensemble would have used.

### Component aggregate

```text
[scene1c-certify-compare] SCENE1C_COMPONENT_CERTIFICATION_FAIL
  control_count 12 | expected_control_count 12 | control_passes 1
  fails: cert_triad_e/1847/201, cert_triad_e/1847/202, cert_triad_e/1901/201,
         cert_triad_e/1901/202, cert_triad_e/1901/203, cert_triad_f/1847/201,
         cert_triad_f/1847/202, cert_triad_f/1847/203, cert_triad_f/1901/201,
         cert_triad_f/1901/202, cert_triad_f/1901/203   (11 of 12)
```

### Diagnosis, from recorded state only

Three distinct failure modes appear, and the protocol separated them cleanly.

**1. Premature `no_frontier` after a single unproductive autonomous look — object
203, three of four (fixture, seed) combinations.** On `e/1901`, `f/1847` and
`f/1901` object 203 took exactly one autonomous look and stopped with **gain
exactly +0.0000** and 4,185–4,472 multi-look surfels against the 5,000 gate.
Reading the recorded gazes against the recorded angular bounds: 203's yaw range
is [+6.180,+23.816] on `e` and [+5.554,+22.389] on `f`, with the seed at +11 and
+10 respectively. The failing runs moved to **(+6,+3)** and **(+5,+9)** — toward
the near edge, which the seed already covers — whereas the one control that
certified, `e/1847/203`, moved to **(+16,+13)** and then (+21,+13), (+21,+8),
into the unexplored far tail, reaching 1.0000 in four looks.

The `e/1847` and `e/1901` pair is the sharpest comparison available: **identical
fixture, identical prescribed seed gaze (+11,+8), different Monte-Carlo seed,
opposite first autonomous decision** — (+16,+13) versus (+6,+3) — and opposite
outcome. The only difference between those two runs in the record is the renderer
seed, so the divergence enters through stereo noise changing the frozen FSG6f
controller's first post-seed choice.

**2. `max_object_fixations` without reaching `no_frontier` — five controls.**
`e/1847/201`, `e/1901/201`, `e/1901/202`, `f/1847/202`, `f/1901/202` each used all
six looks with the controller still reporting `continue`. Notably three of these
had already reached 1.0000, 1.0000 and 0.9999 coverage — the reconstruction was
finished but the frontier was not declared resolved.

**3. Per-look measurement coverage below 0.90 — eleven of twelve controls.**
Values ran 0.8669–0.8994 on the offending looks (`fix_03`/`fix_04` most often),
against the inherited >=0.90 gate. Only `e/1847/203` kept every look at or above
0.9036.

No claim is made here about why FSG6f's first autonomous choice is seed-sensitive
on this geometry; that is beyond what the recorded state supports.

### Consequence for the experiment

The prospective decision rule fixed three outcomes before acquisition. Outcome
(1) applies: **any component control failing means report
`SCENE1C_COMPONENT_CERTIFICATION_FAIL`, preserve the controls, do not run the
full ensemble, and stop.** That is what was done. No ensemble smoke, no full
ensemble trials, no ensemble aggregate, no composition diagnostic — the
composition question is simply not reached, because the premise it depends on
(individually solvable actors) does not hold on these fixtures.

No actor was replaced, resized, reseeded or tuned; no look was added; no gate was
relaxed; FSG6f was not modified.

### Code fixes

**NONE.** No source file was modified; this run changed documentation only.

### What this does establish

The certification protocol itself worked exactly as designed, and it was worth
running. It detected before any ensemble acquisition that eleven of twelve actors
are not solvable within the unchanged six-look budget in the exact complete-scene
rendering context — including a failure mode Scene-1b could not have isolated,
where the frozen controller declares `no_frontier` after one unproductive look
with zero coverage gain. Had the ensemble been run first, those actor-level
failures would have been confounded with scheduling and budget effects, exactly
as Scene-1b's budget-sufficiency question was confounded with component
solvability.

The open question moves accordingly: **before composition can be tested, the
frozen FSG6f controller's post-seed behaviour on this fixture family needs to be
understood** — specifically why its first autonomous choice is seed-sensitive at
object 203's seed, and why five controls exhaust six looks without resolving the
frontier despite reaching ~1.0 coverage.
