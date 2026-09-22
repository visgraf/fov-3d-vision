# FullScene-1b — seed the S0-selected next object

## Motivation

FullScene-1a established the formal first-tour initial condition `S0`: four persistent scene objects, one remaining observed-but-uninstantiated object, and one deterministic next-object decision under the already-established valid-depth scene-memory rule.

FullScene-1b turns that scene-level decision into exactly one physical action: **one prescribed fixation that instantiates the selected object as a separate seed entity**.

This is the first action of the full-scene field test. It is intentionally not a scheduler and not a growth experiment.

## Parent selection

Consume the selected object id and instantiated-object set from the completed FullScene-1a S0 record. Do not declare either in FullScene-1b source.

The currently measured S0 result has one sole candidate, object 144 with 2,436 accumulated valid-depth samples. That is an observed parent result, not a hard-coded contract: the implementation must consume whatever valid FullScene-1a parent it is given.

The deferred local action belonging to the prior active object remains **unexecuted**. FullScene-1b follows the scene executive's S0 selection instead.

## Evidence and prescribed gaze

Reconstruct exactly the same saved observation scope declared by FullScene-1a, through the final MultiObject-3h observation. Do not rerender history and do not broaden backward into older object-141 acquisitions.

For the S0-selected object:

1. collect only saved samples having valid stereo depth and the selected instance id;
2. reuse `multiobject3b_seed.select_seed_from_saved_evidence` unchanged;
3. therefore reuse the established occupied-cell spherical-mean rule on the inherited 0.1-degree grid;
4. require the evidence count to reproduce FullScene-1a's selected valid-depth support exactly.

The historical valid-depth fraction is diagnostic only. No low-texture or measurability gate is introduced.

## One acquisition

Add exactly one fixation at

```text
max(S0 observation steps) + 1
```

through `tools/scene_render_fix.py` with the same fixed-head scene/render contract.

No saved fixation is rerendered.

## Scene representation

Every S0 object remains a separate read-only `SURFEL_MAP`. The newly selected object is appended as one separate `SEED_SURFEL_PATCH`.

The shared cyclopean chart and raw footprint overlaps are measurements only. Zero overlap is not required.

## Scope

No local growth, fusion into an existing object, epistemic handoff, revisit, semantic ranking, object discovery, quality threshold, productivity gate, or automatic scene scheduler is introduced.

Evaluator truth remains closed.

## Next stage

If the seed record is structurally clean, FullScene-1c grows the newly seeded scene-selected object with the frozen local machinery while all pre-existing objects remain stable.
