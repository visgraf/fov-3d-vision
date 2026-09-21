# Scene-1b checks

Chat-side pure checks before workstation acquisition:

- public contract derives the 18-look scene budget from 3 objects x frozen 6-look FSG6f budget;
- fixed-head/static-scene and 12 mm fusion constants are explicit;
- scheduler contract is least-autonomous-service first, then the unchanged Scene-1a area/score/ID ordering;
- a deliberately high-utility but more-served object is excluded while a less-served live object exists;
- repeated static bids cannot starve any live object;
- evaluator geometry contains three angularly disjoint objects inside the frozen FSG6f gaze domain;
- every prescribed seed is a controlled partial view and every evaluator-only three-look design witness reaches >=98% ideal coverage while leaving per-object budget slack;
- `scene1b_policy.py` imports `fsg6f_frontier` rather than reimplementing FSG6f;
- the evaluator-only design witness is absent from the prediction policy and runner;
- prediction runner and scene policy do not import evaluator truth;
- observation splitter exposes every visible known instance for opportunistic fusion;
- scene completion requires all live object controllers to stop;
- global physical no-revisit helper is active.

Expected summary:

`[scene1b-check] SUMMARY passed=9 failed=0`

Eight deliberate negatives must each exit 1:

- `areaonly` — retired Scene-1a area-only scheduler ignores least-service fairness;
- `targetonly` — only the nominal target is updated;
- `premature` — scene stops while one object remains incomplete;
- `revisit` — repeated physical fixation;
- `truth` — evaluator truth imported by prediction runner;
- `copiedpolicy` — FSG6f controller copied/reimplemented instead of imported;
- `overlap` — substitute an object-overlap case into this explicitly non-occluding base experiment;
- `underdesigned` — substitute a one-look fixture that has no short active-coverage witness.

No Blender/Cycles scientific result is produced by these Chat-side checks.
