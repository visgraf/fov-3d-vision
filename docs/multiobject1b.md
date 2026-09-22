# MultiObject-1b — independent growth of object 143

## Question

Can the already-established local FSG6f single-object growth mechanism be transferred to the second foreground entity introduced by MultiObject-1a, while object 141 remains a separate byte-identical entity?

This step adds **growth**, and nothing else.

## Parent

MultiObject-1a introduced two scene entities:

- object 141 — inherited completed surfel map, read-only;
- object 143 — one separate seed surfel patch from one prescribed fixation.

Automatic object discovery, scene scheduling, and second-object completion were all deferred.

## Mechanism

Object 143 is initialized from the saved MultiObject-1a seed acquisition.  Growth then uses `tools/fsg6f_frontier.py` **unchanged**.

FSG6f historically names its target object `141`, so MultiObject-1b uses a pure label adapter for policy input only:

- scene id 143 → frozen FSG6f target label 141;
- every other scene id → non-target.

No geometry or support map is transformed.  The object-143 surfel map itself always contains the real instance id 143.

The adapter lets us reuse the frozen FSG6f frontier extraction, persistent frontier states, strict candidate consensus, projected corridor, 5-degree local saccades, and all numerical constants without copying or retuning the controller.

## History scope

This is deliberately a transfer test, not a retrospective scene-reasoning test.  The object-143 active-growth history starts at its prescribed MultiObject-1a seed observation.  Earlier incidental id-143 observations were used only to choose that seed in 1a; they are not replayed as active-growth history here.

## Empty looks

Reality Check 2b semantics are retained.  A fixation with fewer than 100 reconstructed id-143 points is a valid negative observation:

1. record the binocular observation;
2. fuse no target surface;
3. leave the object-143 map unchanged;
4. let frozen FSG6f decide again.

## Stop

The scientific stop is the frozen policy's own stop (`no_frontier` when that is what it returns).  A 24-object-fixation watchdog, including the 1a seed, is engineering protection only and is not success.

## Scene output

The result remains a two-object scene record:

- object 141 references exactly the inherited read-only surfel source;
- object 143 references the newly grown separate surfel map;
- both are projected onto one shared cyclopean chart.

Footprint overlap is measured, not forbidden.  MultiObject-1a happened to have zero overlap; this experiment does not promote that observation to an invariant.

## Deliberately deferred

- automatic discovery of object 142 or any other object;
- scene-level scheduling;
- cyclopean completion of object 143 after local FSG6f growth;
- layered/occlusion-aware spherical representation;
- mesh reconstruction or interpolation;
- evaluator truth or accuracy gates.

## Interpretation

This experiment is structural.  It asks whether the mature local object-growth mechanism can be reused on a second entity without damaging the first.  Point gain, fixation count, coverage, and geometry statistics are measurements, not PASS thresholds.
