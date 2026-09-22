# MultiObject-3c — grow the scene-selected fourth object

## Question

Can the same frozen selected-object growth machinery repeat on the object selected by MultiObject-3a and seeded by MultiObject-3b, while every previously instantiated scene object remains separate and byte-identical?

This is the second end-to-end scene-memory `select -> seed -> grow` cycle. The target id is consumed from the completed MultiObject-3b parent; it is not hard-coded in MultiObject-3c.

## Occam choice: reuse the existing adapter

MultiObject-2c already introduced a generic pure target-label adapter in `tools/multiobject2c_policy.py`. MultiObject-3c **reuses that file unchanged** rather than copying it under a new name. The adapter presents only the parent-selected scene id under FSG6f's historical target label and maps every other id to non-target for policy input only. Geometry always retains the real scene id.

This is deliberate: repeatability should reuse machinery, not reproduce it.

## Frozen science

- fixed head and static Reality fixture;
- existing stereo front end;
- generic `tools/scene_render_fix.py` acquisition entry point;
- unchanged `tools/multiobject2c_policy.py` label adapter;
- frozen FSG6f frontier/controller;
- frozen 12 mm FSG3/FSG6f association rule;
- inherited 5 degree local saccade lattice and all FSG6f numerical rules;
- Reality-2b empty-look semantics: fewer than 100 selected-object points is valid negative evidence, not a runtime failure;
- object-scoped 24-fixation watchdog including the MultiObject-3b seed, engineering only.

Every object already present in the MultiObject-3b scene graph remains read-only. Only pixels carrying the parent-selected scene id may enter the new object's surfel map.

## History

Active growth history begins at the saved MultiObject-3b seed observation. The earlier scene-memory observations that selected the object and positioned the seed are not replayed as growth-policy history. The seed acquisition is reused, never rerendered. The first new global fixation is the next chronological step after the seed.

## Measurement diagnostic

MultiObject-3b measured a low seed-view depth-recovery fraction for the selected object. MultiObject-3c does **not** react to that measurement. Each look simply records:

- visible selected-object pixels;
- valid selected-object depth points;
- recovered fraction `valid / visible`;
- frame-wide valid stereo fraction.

These values are descriptive only. They rank nothing, change no controller parameter, alter no stopping rule, and gate no outcome. The scientific value is the comparison with the earlier measurement regimes under the same instrument.

## Stop

Scientific stop remains the frozen FSG6f stop (`no_frontier`). The 24 selected-object-fixation watchdog is only an engineering guardrail. If the watchdog is reached while the policy still says `continue`, the run is structurally complete but the scientific stop was not reached.

## Outputs

The run writes the selected-object surfel map and PLY, growth image, per-look RGB previews, patches/maps, policy trace, updated scene graph, shared cyclopean footprints, and a manifest with per-look stereo-recovery diagnostics and integrity hashes.

No automatic discovery, revisit scheduler, scene scheduler, semantic ranking, mesh/interpolation, evaluator truth, or quality gate is introduced.

## Next

After growth, audit the selected object's epistemic remainder and continue scene progress. An unfinished object does not block the tour.
