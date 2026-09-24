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
