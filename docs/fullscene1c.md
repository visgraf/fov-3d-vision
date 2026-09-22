# FullScene-1c — grow the S0-selected object

## Question

Can the same frozen selected-object growth machinery grow the entity seeded by FullScene-1b while every pre-existing persistent scene object remains separate and byte-identical, and while the prior object's deferred local action remains unexecuted?

This is the first ordinary local-growth stage inside the `fullscene-calibration-1` field-test branch. FullScene-1a established scene state S0; FullScene-1b consumed its next-object decision and instantiated exactly one new seed entity with one prescribed fixation. FullScene-1c now asks only what the already-established local controller does with that seed.

The target object id is consumed from the completed FullScene-1b parent. It is not hard-coded in FullScene-1c.

## Occam choice: reuse the frozen local machinery

FullScene-1c introduces no new growth policy. It reuses:

- `tools/multiobject2c_policy.py` unchanged as the generic scene-id-to-FSG6f target-label adapter;
- frozen `tools/fsg6f_frontier.py` and all of its numerical rules;
- the frozen 12 mm FSG3/FSG6f association rule;
- the inherited 5 degree local saccade lattice;
- Reality-2b empty-look semantics;
- generic `tools/scene_render_fix.py` acquisition.

The adapter changes only the label namespace presented to the frozen controller. The actual object surfel map always retains the real scene instance id.

## Parent and scene integrity

The completed FullScene-1b record is the only parent. Its one seed acquisition is replayed from disk, not rerendered, and its saved seed patch must match the reconstructed seed exactly.

Every object that was already persistent before FullScene-1b remains read-only. Only pixels carrying the parent-selected scene id may enter the active surfel map. The prior object's deferred local action remains unexecuted.

## Local history scope

The local FSG6f history begins at the FullScene-1b seed observation only.

The older FullScene S0 observations used to select the object and position the seed are scene-memory evidence; they are **not** replayed as local FSG6f growth history. This preserves the already-established separation between scene-level memory and object-local control.

## Empty looks

The inherited minimum target-point count is unchanged. If a newly rendered fixation reconstructs fewer than 100 selected-object points, that fixation is valid negative evidence:

- record the binocular observation;
- fuse nothing;
- leave the selected-object map unchanged;
- append the observation to local history;
- ask the frozen controller what to do next.

An empty look is not a runtime failure and does not automatically stop the object.

## Stop and watchdog

Scientific stop is unchanged: the frozen FSG6f policy returns `stop/no_frontier`.

A 24 selected-object-fixation watchdog, including the FullScene-1b seed look, remains an engineering guardrail only. If it fires while FSG6f still says `continue`, the run is structurally complete but has **not** reached a scientific stop.

No epistemic handoff is allowed in this stage. If local growth ends with unresolved epistemic residue, that belongs to the subsequent audit stage rather than to FullScene-1c.

## Progress diagnostics — measured separately

This field test deliberately records several kinds of progress without collapsing them into one score:

- **attention / measurement:** visible selected-object pixels, valid selected-object depth points, recovery fraction, empty looks;
- **geometry:** matched and new surfels, map point count, footprint changes;
- **control:** policy trace, candidate/frontier state carried by the frozen controller, termination reason, scientific stop versus watchdog.

These are diagnostics only. In particular, FullScene-1c introduces no productivity score, no novelty threshold, no quality gate, and no changed stopping rule.

The FullScene-1b seed-view recovery measurement is therefore context, not a prediction or gate. Growth is allowed to reveal whether the object is dense, sparse, repetitive, measurement-poor, or quickly exhausted under the same frozen mechanism used before.

## Outputs

The run writes:

- the grown selected-object surfel map and PLY;
- a growth visualization;
- per-look RGB previews;
- saved local patches and intermediate maps;
- the complete local FSG6f policy trace;
- updated shared cyclopean footprints;
- an updated five-entity scene graph;
- a manifest containing the structural invariants, per-look stereo diagnostics, fusion matched/new counts, stop reason and integrity hashes.

No evaluator truth, automatic discovery, scene scheduler, revisit scheduler, semantic ranking, mesh/interpolation, handoff, productivity threshold or quality gate is introduced.

## Next

If FullScene-1c completes structurally, the next bounded step is **FullScene-1d**: read-only epistemic audit of the grown object before returning to the scene-level inventory.

An unfinished object still does not block the scene tour.
