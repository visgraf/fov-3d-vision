# Scene-1c checks

Chat-side pure checks before workstation acquisition:

- fixed head, static scene, 2.10 m vergence, 12 mm fusion, six-look per-object budget and 18-look global budget remain unchanged from Scene-1b;
- every Scene-1b numerical target gate is unchanged;
- the component-certification matrix is exactly 2 fixtures x 2 seeds x 3 objects = 12 controls;
- the two fresh fixtures contain three angularly disjoint compact convex ribbons inside the frozen FSG6f gaze domain;
- each seed is a controlled partial view and each evaluator-only three-look geometric witness reaches >=98% ideal box coverage with budget slack;
- `scene1c_policy.py` imports the frozen Scene-1b scheduler instead of copying it, and Scene-1b still imports FSG6f;
- the frozen least-service fairness semantics remain load-bearing;
- component and ensemble prediction use the same `scene1c_render_fix.py` complete-scene renderer;
- neither component nor ensemble prediction imports evaluator scene truth or design witnesses;
- `scene1c_certify_compare.py` requires the exact twelve-control prospective set;
- the final Scene-1c aggregate requires a passed component-certification artifact;
- opportunistic all-object observation splitting, all-object completion and global no-revisit remain active.

Expected summary:

`[scene1c-check] SUMMARY passed=10 failed=0`

Ten deliberate negatives must each exit 1:

- `incompletecert` — one prospective actor control is missing;
- `areaonly` — retire fairness and return to Scene-1a's area-only scheduler;
- `schedulercopy` — copy/reimplement Scene-1b scheduling instead of importing it;
- `targetonly` — only the nominal target is processed;
- `premature` — scene stops while an object remains incomplete;
- `revisit` — repeated physical fixation;
- `truth` — evaluator truth imported by component or ensemble prediction;
- `overlap` — substitute an angularly overlapping scene into this explicit non-occluding composition base case;
- `underdesigned` — substitute a one-look object with no controlled active span;
- `budgetbump` — increase the six-look or 18-look budget after Scene-1b.

The local checks do not run Blender/Cycles and do not constitute component certification or a scientific Scene-1c result.
