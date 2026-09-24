# Classroom-Oracle-1

## Scientific question

**If local stereo measurement were essentially perfect, does the active foveal control architecture know where to look?**

This experiment separates measurement from control. Blender replaces only the current local stereo matcher. The active loop, persistent metric memory, FSG6f surface-growth policy, Cyclopean epistemic handoff, and fixation budget remain real.

## Oracle boundary

For the current binocular tangent observation Blender may provide exact RGB, Object Index, and Position passes. A left truth point is accepted only when its reprojection is inside supported right-eye tangent data and the right eye sees the same instance. True half-occlusions therefore remain unmeasured. The oracle has no SGBM `0.75-4.5 m` range limit.

Blender must not select autonomous fixations, reveal unobserved/future geometry to the controller, declare completion, or fill holes. There is no foreground/background decomposition: floor, walls, chairs, ceiling, pipes, and other scene surfaces remain ordinary instances.

The one deliberate bootstrap exception is scene seeding: within the frozen FSG6f angular domain Blender enumerates visible instances and supplies one seed direction for each. Automatic scene discovery is therefore **not** claimed by Classroom-Oracle-1. After each seed, the controller owns the eyes.

## Control loop

For every visible instance:

1. use its single oracle seed;
2. render the current binocular tangent pair;
3. measure a perfect local stereo patch with the same-instance binocular rule;
4. initialize/fuse the inherited persistent surface map with the unchanged 12 mm association/hash rule;
5. record the completed binocular observation even when fewer than 100 target-depth points are recovered; such an empty look fuses zero geometry;
6. ask the frozen FSG6f policy for the next fixation;
7. when FSG6f returns `no_frontier`, run the inherited Cyclopean audit and, if available, fixate a `NEVER_OBSERVED + EXTERIOR` shoreline cell using deepest border-distance first;
8. repeat until attention completion or the inherited 24-fixation engineering watchdog.

A seed with fewer than the inherited 100 target points cannot initialize the metric map. It is preserved as `seed_uninitializable`; the object is not silently dropped.

## Fixed benchmark

Every controller-selected look preserves:

- left/right raw multilayer EXRs;
- the rectified tangent RGB pair;
- the oracle metric patch;
- gaze and action source;
- fusion and controller decisions.

The resulting trajectory \(G^*=(g_0,\ldots,g_N)\) is the open-loop benchmark for later SGBM, RAFT-Stereo, IGEV, CREStereo, or other matcher comparisons on exactly the same gazes and images.

## Evaluation

Depth error is not the principal metric because depth is oracle truth. The offline evaluator measures control behavior: fixation count, per-instance and aggregate reachable-surface coverage, zero-new-surface looks, remaining uncovered territory, incidental instance observations, and termination reason.

`reachable surface` has an explicit operational definition here: dense 0.25-degree Cyclopean first-hit samples inside the frozen controller angular domain, from the fixed head. It does not mean hidden/back-facing surface that no fixation from the fixed head can see.

The dense reference geometry is stored under the bootstrap evaluation-only directory. The control runner never opens it. Evaluation refuses to run before `control_complete: true`.

There is intentionally no scientific PASS/FAIL threshold. A successful oracle reconstruction supports the control architecture and points back to measurement as the bottleneck; a systematic oracle failure exposes a control/coverage problem. The measured result must be preserved without retuning.

## Acceptance check

From the repository root:

```bash
.venv/bin/python tools/dev/check_classroom_oracle1.py
```

Expected package acceptance line:

```text
[classroom-oracle1-check] SUMMARY passed=12 failed=0
```

## Integration smoke test

Use a new output directory. The smoke test takes the first two oracle-visible instances and requires exactly two observations per object (four looks total). The second look must come from the controller, not Blender.

```bash
.venv/bin/python tools/classroom_oracle1_run.py \
  --repo . \
  --out previews/classroom-oracle-1-smoke \
  --profile small \
  --device OPTIX \
  --smoke
```

Do not continue to the full experiment if the smoke test fails. Diagnose implementation defects; do not retune the controller.

## Full experiment

```bash
.venv/bin/python tools/classroom_oracle1_run.py \
  --repo . \
  --out previews/classroom-oracle-1-full \
  --profile full \
  --device OPTIX

.venv/bin/python tools/classroom_oracle1_eval.py \
  --run previews/classroom-oracle-1-full
```

The full run must attempt every oracle-visible Classroom instance. Do not drop inconvenient objects, tighten the visibility set after seeing results, alter the 12 mm fusion rule, or tune FSG6f/Cyclopean constants.

## Result record

After execution, append the actual smoke/full outcomes here: number of oracle-visible instances, total fixations, termination counts, per-object and aggregate coverage, zero-new looks, object failures, and paths to the retained benchmark artifacts. The result—good or bad—is the result of Classroom-Oracle-1.

## Execution notes — 2026-09-24, branch `classroom-oracle-1`

Acceptance passed on the first attempt: `[classroom-oracle1-check] SUMMARY passed=12 failed=0`.
Four implementation defects then surfaced in sequence during the smoke test. All four are
mechanical — a typo, a missing call to an existing repository helper, a wrong pass-channel
literal, and a constructor-argument mismatch against the real inherited API. None touched
the scientific contract, the FSG6f/Cyclopean decision rules, the 12 mm fusion rule, the
24-look watchdog, oracle visibility semantics, or the object set. The 12-check suite was
rerun green after each.

### Repair 1 — `_json_write` NameError (bootstrap seed scan)

`tools/classroom_oracle1_render.py:41` defined `__json_write` while all five call sites used
`_json_write`. Renamed the definition to match the call sites. Pure typo; no behaviour change.

### Repair 2 — Cycles seed not pinned (fixation render)

`render_foveated.render_fixation` asserts the sampling settings survived the render and
raised: `expected (64, 11206003, ...)`, got `(64, 1, ...)`. Reproduced directly: the seed
reverts to **1** across a render while `samples` persists, independently of
`use_persistent_data`.

Cause: the Classroom `.blend` **keyframes `cycles.seed` at frame 1**, so frame evaluation
during the render overwrites any script-set seed. The repository already carries the fix —
`bl_common.pin_seed()`, whose docstring documents this exact scene and this exact symptom —
and `fsg_blend_bridge.py` calls it in `configure_scene`. `_prepare_perspective_pair` omitted
the call. Added `pin_seed(scene)` there. Verified by running a real
`fsg_blend_bridge.py` fixation, whose identical post-render assert passes.

The seed affects render noise only, never geometry or instance selection.

### Repair 3 — wrong Object Index channel literal

`_extract_exr` requested `IndexOB.X`; the multilayer EXR written by this scene carries
`interior.Object Index.X`. Changed the literal to `Object Index.X`, matching the existing
repository convention in `demo_classroom1_scene_blender.py` (`"Object Index.X"`) and
`demo_classroom1_repo.py`. `Combined.*` and `Position.*` already matched and were untouched.

### Repair 4 — `fsg3_surface_map.Patch` constructor mismatch

Fusion raised `cannot reshape array of size 16384 into shape (3)`. The real signature is
`Patch(patch_id: str, xyz_h, rgb, instance_id)` — `patch_id` comes **first** and was absent
from the runner's binding table, so the keyword path reported it missing and the positional
fallback shifted every argument (xyz became `patch_id`, `instance_id` became `rgb`). Added a
`patch_id` entry (`fix_NN`, unique per look within an object's map, as fsg3 requires for
duplicate detection and its 63-bit provenance mask) and put the correct 4-tuple first in the
positional fallback.

### Smoke test outcome — integration verified, harness contract unreachable

After the four repairs the smoke test runs end to end and every integration property holds:

| property | observed |
|---|---|
| oracle-visible instances in the frozen domain | **25** (yaw +-25 deg, pitch +-20 deg, 0.25 deg scan) |
| attempted in smoke | 2 (`107 Text`, `108 Text.001`) |
| oracle valid core fraction | **0.8099 / 0.8475** (13,269 and 13,886 points of 16,384) |
| `sgbm_called` | false; `depth_search_bound_applied` false |
| `dense_evaluation_truth_opened_during_control` | **false** |
| artifacts per look | raw_L/R.exr, calibration, acquisition, oracle_observation.npz, benchmark PNG pair, patch, map snapshot |
| foreground/background decomposition | false |

For comparison, the same instrument under SGBM in Classroom-FSG-1 had a **0.128** median
valid fraction. Measurement is now essentially perfect, which is the point of the experiment.

Both objects reached legitimate, documented terminations after their seed:

- **107 `Text`** — `seed_uninitializable`: fewer than the inherited 100 target-depth points,
  preserved rather than dropped, 0 surfels.
- **108 `Text.001`** — `attention_complete` with 116 surfels. The chain is fully recorded:
  FSG6f found 37 frontier cells, 35 boundary-resolved and 2 map-resolved, **0 open**, so it
  returned no candidates; the Cyclopean audit then found **0** eligible
  `NEVER_OBSERVED + EXTERIOR` shoreline cells and returned `attention_complete`.

**The smoke test nonetheless fails its own harness assertion** — `objects=2, looks=2` against
a required four — and this is not an implementation defect:

- both objects are tiny blackboard text labels; the benchmark pair shows `Text.001` is the
  digits "678910" on a blackboard, occupying ~116 of 13,886 valid core points, the rest
  belonging to eight incidental instances;
- the harness selects **the first two oracle-visible instances by id**, and ids 107/108 are
  the two smallest objects in the visible set of 25, which also contains `beams`,
  `blackBoard`, `ceiling`, `sol`, `wall`, `woodBase` and `worldMap`;
- more fundamentally, a `seed_uninitializable` object **can never** have a controller-selected
  second look, because no metric map exists for FSG6f to grow from. The assertion "exactly
  two observations per object" therefore contradicts the experiment's own preserved
  Reality-Check-2b semantics for that class of object.

Making it pass would require either selecting different objects or relaxing the assertion.
Both are excluded by the handoff ("do not force a gaze, remove an object, or tune the policy
merely to make the smoke test pass"), and the choice changes what the smoke test certifies.
Under the working agreement this is a decision the prompt did not delegate, so execution
**stopped here** and the full 25-instance run was not launched.

Nothing was cherry-picked, no gaze forced, no policy constant touched, no object dropped.

**CLASSROOM_ORACLE1_STOPPED — smoke harness contract unreachable on the first two visible
instances. Awaiting Luiz/Chat.**

## Result — 2026-09-24, repaired smoke gate and full run

The execution notes above are preserved as the historical record of the stopped first attempt
(`f850946`). The smoke-gate repair is `ee578d5`; it changed only the integration gate. The
four mechanical repairs from `f850946` survive it unchanged — Chat renamed the local `pid`
to `patch_id`, but `patch_id` remains bound in the binding table and first in the positional
fallback. `[classroom-oracle1-check] SUMMARY passed=12 failed=0`, `py_compile` clean,
`git diff --check` clean. **No further repair was needed in this session.**

### Repaired smoke test — `previews/classroom-oracle-1-smoke-2`

```text
[classroom-oracle1] COMPLETE {"fixations": 5, "objects": 4, "smoke": true,
  "terminations": {"attention_complete": 2, "seed_uninitializable": 1, "smoke_budget": 1}}
```

`smoke_gate` is internally consistent and reports the preferred status:

| field | value |
|---|---|
| status | **PASS_CONTROLLER_TRANSITION_EXERCISED** |
| primary_instance_ids | [107, 108] (retained, as required) |
| objects_examined | 4 (probe continued deterministically to 109, 110) |
| controller_transition_exercised | true |
| all_post_seed_looks_controller_selected | true |
| exhausted_visible_set | false |
| dense_evaluation_truth_opened_during_control | **false** |

Instance **110 `beams`** first exercised a controller-selected second look:
`action_source=fsg6f`, gaze (-22.00, 20.00) -> (-17.00, 15.00), fusing 251 input points as
114 matched + 137 new and growing the map 4,868 -> 5,005 surfels. Instances 107 and 108
terminated legally at their seed (`seed_uninitializable`, `attention_complete`), which the
repaired gate now accepts. Oracle valid core fraction ran 0.810-0.910 over the four objects.
Raw EXR pairs, benchmark PNG pairs, oracle patches and map snapshots were retained per look.

### Full experiment — `previews/classroom-oracle-1-full`, profile `full`

```text
[classroom-oracle1] COMPLETE {"fixations": 104, "objects": 25, "smoke": false,
  "terminations": {"attention_complete": 25}}
[classroom-oracle1-eval] COMPLETE {"coverage": 0.8746927069106801, "fixations": 104,
  "instances": 25, "terminations": {"attention_complete": 25}}
```

| quantity | value |
|---|---|
| oracle-visible instances | **25** |
| attempted instances | **25** (none dropped; `unexpected_attempted_instance_ids` empty) |
| total fixations | **104** |
| termination histogram | **`attention_complete`: 25** — and nothing else |
| seed_uninitializable / runtime-failed / watchdog hits | **0 / 0 / 0** |
| `control_complete` | true |
| `dense_evaluation_truth_opened_during_control` | **false** |
| foreground/background decomposition | false |

**Action sources across all 104 looks: 25 `oracle_seed`, 53 `fsg6f`, 26
`cyclopean_epistemic`.** All 79 post-seed looks were controller-selected and **zero** gazes
after a seed came from Blender. The Cyclopean epistemic handoff is not vestigial: it fired
26 times across 8 of the 25 objects (111, 115, 178, 201, 202, 210, 224, 234).

At profile `full` no object was `seed_uninitializable`. Instance 107 `Text`, which was
uninitializable at `small`, initialized here: the larger core (256 vs 128) clears the
inherited 100-point floor. That is a profile consequence, not a policy change.

### Coverage

Scope is the declared one: dense 0.25-degree Cyclopean first-hit samples inside the frozen
fixed-head controller domain (yaw +-25 deg, pitch +-20 deg), covered iff within 12 mm of a
final surfel. It is **not** coverage of hidden or back-facing global surface.

| aggregate | value |
|---|---|
| reachable samples | 29,288 |
| covered samples | 25,618 |
| **micro coverage** | **0.8747** |
| macro (unweighted mean over 25 objects) | 0.7889 |
| median per-object coverage | 0.9729 |
| objects at exactly 100% | **10 / 25** |
| zero-new-surfel looks | **4** of 79 post-seed looks (94.9% of controller looks added geometry) |

I recomputed coverage independently from the retained maps and the dense reference and
reproduced the evaluator exactly: 25,618 / 29,288.

Per object, sorted by reachable surface:

| id | name | fix | surfels | reachable | coverage | uncovered |
|---|---|---:|---:|---:|---:|---:|
| 224 | woodBase | 19 | 230,021 | 6,614 | **99.95%** | 3 |
| 210 | wall.008 | 19 | 170,083 | 5,892 | **93.14%** | 404 |
| 111 | blackBoard | 12 | 159,935 | 4,623 | **100.00%** | 0 |
| 234 | worldMap | 7 | 79,351 | 2,645 | **100.00%** | 0 |
| 178 | sol | 6 | 82,472 | 2,587 | **59.68%** | 1,043 |
| 166 | lettersPlank | 4 | 22,082 | 1,226 | 68.84% | 382 |
| 225 | woodBaseboard | 2 | 10,781 | 1,040 | 39.04% | 634 |
| 202 | wall | 5 | 67,335 | 1,007 | **99.30%** | 7 |
| 115 | boardFrame | 3 | 12,056 | 770 | 55.58% | 342 |
| 201 | verticalPipe | 6 | 17,930 | 627 | **97.29%** | 17 |
| 174 | plank | 2 | 8,871 | 599 | 56.76% | 259 |
| 140 | coat 1 | 2 | 12,489 | 405 | 87.65% | 50 |
| 123 | ceilingMoulding | 1 | 5,647 | 369 | 17.07% | 306 |
| 112 | blackBoardLamp | 3 | 5,860 | 265 | 76.98% | 61 |
| 167 | lettersPlank.001 | 1 | 5,071 | 177 | 100.00% | 0 |
| 113 | blackBoard_upPart | 1 | 1,820 | 142 | 46.48% | 76 |
| 109 | alphabet | 1 | 822 | 82 | 32.93% | 55 |
| 114 | blackboardLamp | 1 | 661 | 53 | 41.51% | 31 |
| 168 | lettersPlank.002 | 1 | 5,601 | 43 | 100.00% | 0 |
| 216 | wallPlug.001 | 1 | 1,110 | 37 | 100.00% | 0 |
| 116 | ceiling | 1 | 1,783 | 34 | 100.00% | 0 |
| 172 | pipe | 1 | 6,094 | 24 | 100.00% | 0 |
| 107 | Text | 1 | 403 | 19 | 100.00% | 0 |
| 108 | Text.001 | 1 | 485 | 5 | 100.00% | 0 |
| 110 | beams | 3 | 36,317 | 3 | 100.00% | 0 |

A caution on the last rows: objects such as `beams` (36,317 surfels, 3 reachable samples)
and `pipe` have tiny reachable counts because most of their surface lies **outside** the
+-25/+-20 controller domain. Their 100% is real but nearly vacuous; the informative rows are
the ones with large reachable counts.

### The deficit is at the controller's own domain boundary

Every systematic miss has its uncovered territory pressed against a domain edge:

| object | uncovered yaw span | uncovered pitch span |
|---|---|---|
| sol | [-25.00, 25.00] (full width) | [-20.00, -14.00] (bottom edge) |
| woodBaseboard | [-25.00, 25.00] (full width) | [-15.50, -12.50] |
| ceilingMoulding | [-24.50, 25.00] (full width) | [18.25, 20.00] (top edge) |
| lettersPlank | [14.25, 25.00] (right edge) | [11.50, 14.50] |
| boardFrame | [9.75, 25.00] (right edge) | [-6.50, 9.75] |
| plank | [-25.00, 4.25] (left edge) | [-1.50, -0.25] |

Measured against distance to the nearest domain edge:

| distance to edge | samples | uncovered | uncovered rate |
|---|---:|---:|---:|
| 0-1 deg | 2,510 | 655 | **26.1%** |
| 1-2 deg | 2,378 | 486 | 20.4% |
| 2-4 deg | 4,216 | 846 | 20.1% |
| 4-6 deg | 4,097 | 777 | 19.0% |
| 6-10 deg | 6,898 | 618 | 9.0% |
| >10 deg | 9,189 | 288 | **3.1%** |

**Coverage in the domain interior (>6 deg from any edge) is 0.9437; within 6 deg of an edge
it is 0.7906.** 75.3% of all uncovered samples lie within 6 deg of an edge, against 45.1% of
all samples — so the residual is concentrated at the boundary, not spread through the scene.

The `sol` trajectory shows the mechanism with no ambiguity, and shows the architecture
working rather than failing: seed at pitch -18, then four FSG6f looks growing the map
41,246 -> 68,209 surfels; at look 4 FSG6f returned **0 candidates**, the Cyclopean audit
took over with 37 eligible `NEVER_OBSERVED + EXTERIOR` shoreline cells and fired an
`epistemic_fixation` to pitch **-19.20**, essentially the domain floor, gaining a further
14,263 surfels; then FSG6f again returned 0 candidates and the shoreline audit found **0**
eligible cells, so it stopped. The controller pushed to its own boundary and halted when its
own frontier and shoreline tests were both empty.

### Incidental observation

34 distinct instances were seen incidentally, a mean of 9.7 per object — the fixed-head
tangent core routinely contains many entities besides the target. The most frequently
incidental were 210 `wall.008` (21 objects), 109 `alphabet` and 166 `lettersPlank` (16 each).
This is recorded, not exploited: no cross-object fusion or role assignment was used.

### Retained benchmark

Every look retained its left/right raw multilayer EXR, rectified tangent PNG pair, oracle
metric patch, map snapshot, calibration, acquisition record, gaze and action source. The
104-fixation trajectory is the fixed open-loop benchmark for later SGBM / RAFT-Stereo /
IGEV / CREStereo comparison on exactly these gazes and images.

```text
previews/classroom-oracle-1-full/manifest.json
previews/classroom-oracle-1-full/evaluation.json
previews/classroom-oracle-1-full/bootstrap/seeds.json
previews/classroom-oracle-1-full/bootstrap/evaluation_only/reachable_samples.npz   (eval only)
previews/classroom-oracle-1-full/objects/instance_XXXX/result.json                 (trajectory)
previews/classroom-oracle-1-full/objects/instance_XXXX/benchmark/fix_NN_{L,R}.png
previews/classroom-oracle-1-full/objects/instance_XXXX/acquisitions/fix_NN/raw_{L,R}.exr
previews/classroom-oracle-1-full/objects/instance_XXXX/acquisitions/fix_NN/oracle_observation.npz
previews/classroom-oracle-1-full/objects/instance_XXXX/patches/fix_NN.npz
previews/classroom-oracle-1-full/objects/instance_XXXX/maps/fix_NN.npz
previews/classroom-oracle-1-smoke/    (stopped first attempt, preserved as evidence)
previews/classroom-oracle-1-smoke-2/  (repaired gate)
```

### What this establishes

**Oracle measurement behaviour.** Essentially perfect, as intended: valid core fraction
0.810-0.910, against the 0.128 median the same instrument produced under SGBM in
Classroom-FSG-1. `sgbm_called` false and `depth_search_bound_applied` false throughout, so
no 0.75-4.5 m bound was imposed. Half-occlusions were preserved by the same-instance
right-eye reprojection rule.

**Autonomous control behaviour.** The controller owned the eyes after every seed: 79 of 79
post-seed looks were `fsg6f` or `cyclopean_epistemic`, none from Blender. All 25 objects
terminated by the controller's own `attention_complete`; the 24-look watchdog never fired,
so no termination was an engineering cutoff. 94.9% of controller-selected looks added new
geometry. The FSG6f -> Cyclopean handoff is genuinely load-bearing, firing on 8 objects.

**Scene coverage.** 87.47% of reachable surface overall, 94.37% in the domain interior,
10 of 25 objects complete, median per-object coverage 97.29%.

**Engineering failures.** None in this session. No repair was required; no object was
dropped, renamed, or substituted; no controller constant was touched.

**Scientific observation that survives correct implementation.** The residual 12.5% is not
random: it is pressed against the edges of the controller's own angular domain, where the
uncovered rate rises from 3.1% deep in the interior to 26.1% in the last degree. Five
substantial objects — `sol`, `woodBaseboard`, `boardFrame`, `plank`, `lettersPlank` — are
extended surfaces that run out of the +-25/+-20 domain, and each declares
`attention_complete` with a boundary-hugging band unseen. Whether that is a domain choice,
a frontier-eligibility rule at the boundary, or a real limit of the shoreline test is the
open question this experiment hands back; it is not resolvable without changing something,
and nothing was changed.
