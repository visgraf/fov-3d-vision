# Scene-1a checks

Chat-side pure checks before workstation acquisition:

- public contract derives the 18-look scene budget from 3 objects x frozen 6-look FSG6f budget;
- fixed-head/static-scene and 12 mm fusion constants are explicit;
- evaluator geometry contains three angularly disjoint objects inside the frozen FSG6f gaze domain;
- each prescribed seed is partial and admits an improving neighbouring gaze;
- scheduler is area-first, frontier-score-second, instance-ID-only-as-final-tie-break;
- scene completion requires all three object controllers to stop;
- observation splitter exposes every visible known instance for opportunistic fusion;
- global physical no-revisit helper is active;
- `scene1a_policy.py` imports `fsg6f_frontier` rather than reimplementing its frontier/controller;
- prediction runner and scene policy do not import evaluator truth.

Expected summary:

`[scene1a-check] SUMMARY passed=8 failed=0`

Seven deliberate negatives must each exit 1:

- `hardcoded` — hard-coded object priority;
- `targetonly` — only the nominal target is updated;
- `premature` — scene stops while one object remains incomplete;
- `revisit` — repeated physical fixation;
- `truth` — evaluator truth imported by prediction runner;
- `copiedpolicy` — FSG6f controller copied/reimplemented instead of imported;
- `overlap` — substitute an object-overlap case into this explicitly non-occluding base experiment.

No Blender/Cycles scientific result is produced by these Chat-side checks.
