# MultiObject-2b checks

## Positive structural contract

The package checks six invariants:

1. the selected object id is consumed from the MultiObject-2a parent rather than hard-coded;
2. seed evidence uses saved **valid-depth** samples and the unchanged MultiObject-1a occupied-cell spherical-mean selector;
3. exactly one new globally numbered fixation is added and no history is rerendered;
4. the generic `scene_render_fix.py` entry point is used rather than the legacy Reality-2 global-step-limited renderer;
5. objects 141 and 143 remain read-only while the selected object receives a separate seed patch only;
6. growth and scene scheduling remain deferred.

Expected pure-check lines:

```text
[multiobject2b-seed] PASS parent_selected=true valid_depth_seed=true one_fixation=true separate_entity=true
[multiobject2b-progress] PASS existing_objects_read_only=true growth=false scheduler=false quality_gated=false
[multiobject2b-check] SUMMARY passed=6 failed=0
```

## Genuine mutation negatives

Each negative mutates the real source text and must be detected with exit code 1:

- `handpick` — replace parent-selected id consumption with hard-coded 142;
- `visibleonly` — drop the valid-depth requirement from seed evidence;
- `multiprobe` — allow two added fixations;
- `legacyrenderer` — switch back to the Reality-2 renderer;
- `crossfuse` — claim a fusion iteration in the seed step;
- `grow` — enable growth in this step.

Exit code 2 means the mutation escaped detection and is itself a check failure.
