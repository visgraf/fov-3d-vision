# MultiObject-3d — epistemic audit of the first frozen-policy stop

## Motivation

MultiObject-3c repeated the unchanged selected-object growth machinery on the fourth persistent scene entity.  On the current seed-2111 record the target grew from **3,662** to **6,426** pure surfels, while all prior object maps stayed byte-identical.  Its stereo recovery remained low (**1.3–9.6%**, median about **6.7%**), and the Reality-2b valid-empty-look path fired four times.

For the first time in this multi-object series, however, frozen FSG6f reached its own stop before the engineering watchdog:

```text
termination_reason = no_frontier
scientific_stop_reached = true
selected-object fixations = 13 / 24
```

The final trace still contained **30 OPEN frontier voxels out of 72**, but `candidates_before_consensus_count = 0`: no admissible next gaze existed under the unchanged controller.

That makes this an important distinction to audit rather than interpret by label alone.

## Central question

> Did `no_frontier` coincide with attention completion, or did the policy exhaust its admissible actions while genuinely unseen territory remained?

This is a **read-only stop audit**.  It does not rescue, extend, or modify the stopped policy.

## Method

1. Consume `selected_object_id` from the completed MultiObject-3c parent; do not hard-code a scene id.
2. Require the parent to be the declared `no_frontier` scientific stop reached before the 24-look engineering watchdog.
3. Load the selected-object surfel map read-only.
4. Replay only the saved selected-object observation history: the MultiObject-3b seed plus the MultiObject-3c growth looks.  No rendering or fusion occurs.
5. Rebuild the existing 0.1° cyclopean chart and reuse the angular footprint implied by the unchanged 12 mm association radius at this object's own range.
6. Reuse Cyclopean-1b shoreline states and refine only base `UNOBSERVED` cells with the unchanged Cyclopean-1d observation-versus-measurement states.
7. Reconstruct the **final frozen FSG6f decision exactly** from the saved final observation, saved gaze history, final map and saved binocular observation history.  Counts and stop fields must match the parent's policy trace before any interpretation is made.
8. Reconstruct the frozen final 3D frontier and angularly quantize each look-ahead target onto the unchanged 0.1° cyclopean chart.  Report which epistemic cell each `OPEN`, `MAP_RESOLVED`, and `BOUNDARY_RESOLVED` target coincides with.

The 3D-frontier/cyclopean relation is descriptive.  It introduces no distance threshold: it is simply the existing look-ahead target direction quantized by the existing chart rule.

## Stop interpretation

No fitted threshold is used.

- exterior `NEVER_OBSERVED > 0` at a genuine `no_frontier` stop -> `POLICY_EXHAUSTED_WITH_UNSEEN_TERRITORY`;
- otherwise, if target-no-depth remains -> `ATTENTION_COMPLETE_MEASUREMENT_PARTIAL_AT_POLICY_STOP`;
- otherwise -> `ATTENTION_COMPLETE_AT_POLICY_STOP`.

This interpretation describes the stopped object's state.  It does **not** change the scene-level disposition.

## Scene-progress principle

In every case:

```text
scene_disposition = MOVE_TO_NEXT_OBJECT
```

Unresolved territory remains persistent and can later participate in a revisit policy.  This increment does not create that policy.

## Deliberately deferred

- any rescue fixation after the frozen stop;
- watchdog extension;
- changes to FSG6f candidate generation, consensus, corridor rules, or lattice;
- alternate matcher, baseline, vergence, illumination, or active texture;
- interpolation, mesh completion, layered occlusion, or evaluator truth;
- object discovery, revisit scheduling, or scene scheduling.

## Expected output

The record contains:

- `object_<id>_epistemic_stop_report.json` — shoreline census, refined arcs, exact final-policy replay and 3D-frontier/cyclopean relation;
- `object_<id>_epistemic_stop_shoreline.png` — selected-object support and epistemic shoreline;
- `prediction_manifest.json` — integrity, stop interpretation, relation summary and unconditional scene disposition.

The experiment is successful structurally only if it remains read-only and reproduces the saved frozen-policy stop exactly.  The scientific result is whatever the saved evidence says about the residual state.
