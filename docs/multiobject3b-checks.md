# MultiObject-3b checks

## Positive structural contract

The package checks six invariants:

1. both the selected id and already-instantiated id set are consumed from the MultiObject-3a parent/current scene rather than hard-coded;
2. seed evidence uses the **complete updated** MultiObject-3a saved history, valid-depth samples only, and the unchanged MultiObject-1a occupied-cell spherical-mean selector;
3. exactly one new globally numbered fixation is added and no saved history is rerendered;
4. the generic `scene_render_fix.py` entry point is used rather than the legacy Reality-2 global-step-limited renderer;
5. every existing object remains read-only while the selected object receives a separate seed patch only;
6. growth, revisit scheduling and scene scheduling remain deferred.

Expected pure-check lines:

```text
[multiobject3b-seed] PASS parent_selected=true updated_valid_depth_seed=true one_fixation=true separate_entity=true
[multiobject3b-progress] PASS existing_objects_read_only=true growth=false revisit=false scheduler=false
[multiobject3b-check] SUMMARY passed=6 failed=0
```

## Genuine mutation negatives

Each negative mutates the real source text and must be detected with exit code 1:

- `handpick` — replace parent-selected id consumption with a hard-coded id;
- `oldhistoryonly` — discard the new half of the updated scene history;
- `visibleonly` — drop the valid-depth requirement from seed evidence;
- `multiprobe` — allow two added fixations;
- `legacyrenderer` — switch back to the Reality-2 renderer;
- `crossfuse` — claim a fusion iteration in the seed step;
- `grow` — enable growth in this step.

Exit code 2 means the mutation escaped detection and is itself a check failure.
