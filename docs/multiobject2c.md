# MultiObject-2c — grow the scene-selected third object

## Question

Can the frozen single-object FSG6f growth mechanism grow the object selected by MultiObject-2a and seeded by MultiObject-2b, while the two pre-existing scene objects remain separate and byte-identical?

This is the first growth experiment whose target id is supplied by scene memory rather than declared by the experiment. The id is consumed from the completed MultiObject-2b parent; it is not hard-coded in MultiObject-2c.

## Frozen science

- fixed head and static Reality fixture;
- existing stereo front end;
- generic `tools/scene_render_fix.py` acquisition entry point;
- frozen FSG6f frontier/controller through a pure instance-label adapter;
- frozen 12 mm FSG3/FSG6f association rule;
- inherited 5 degree local saccade lattice and all FSG6f numerical rules;
- Reality-2b empty-look semantics: fewer than 100 selected-object points is valid negative evidence, not a runtime failure;
- object-scoped 24-fixation watchdog including the MultiObject-2b seed, engineering only.

Objects 141 and 143 remain read-only. Only pixels carrying the parent-selected scene id may enter the new object's surfel map.

## History

Active growth history begins at the saved MultiObject-2b seed observation. Earlier observations that selected the object and positioned the seed are not replayed as growth-policy history. The seed acquisition is reused, never rerendered. The first new global fixation is the next chronological step after the seed.

## Texture diagnostics

Because the selected object is strongly textured in its seed view, each look records:

- visible selected-object pixels in the rectified left field;
- valid selected-object depth points;
- recovered fraction `valid / visible`;
- frame-wide valid stereo fraction.

These values are descriptive only. They do not rank candidates, alter FSG6f, stop growth, or gate success. The purpose is to compare the measurement regime with the low-texture object-143 experience without changing the experiment.

## Stop

Scientific stop remains the frozen FSG6f stop (`no_frontier`). The 24 selected-object-fixation watchdog is only an engineering guardrail. If the watchdog is reached while the policy still says `continue`, the run is structurally complete but the scientific stop was not reached.

## Outputs

The run writes the selected-object surfel map and PLY, growth image, per-look RGB previews, patches/maps, policy trace, three-object scene graph, shared cyclopean footprints, and a manifest with per-look stereo-recovery diagnostics and integrity hashes.

No automatic discovery, scene scheduler, semantic ranking, mesh/interpolation, evaluator truth, or quality gate is introduced.
