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
