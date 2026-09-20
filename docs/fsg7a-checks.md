# FSG7a checks

`python tools/dev/check_fsg7a.py` must print `passed=7 failed=0` before acquisition.

The check suite verifies the H0/Ht transport, exact fixed-world scene transform, genuine binocular self-occlusion at H0, binocular reveal after translation, frozen instrument/fusion IDs, evaluator-truth isolation from the prediction runner, and fail-capable part/surface metrics.

Six deliberate negatives must each exit 1:

- `no_motion` — a fixed-head substitute cannot reveal the return wing;
- `moving_scene` — moving the world with the head cancels parallax;
- `frame` — omitting Ht→H0 transport produces a 45 cm map error;
- `truth` — evaluator truth in the runner is forbidden;
- `purity` — background contamination is detectable;
- `visibility` — falsely claiming the translated view remains occluded is detectable.

Chat-side design checks are not Blender evidence. Only Code's fresh full runs may close FSG7a.
