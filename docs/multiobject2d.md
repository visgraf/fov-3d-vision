# MultiObject-2d — epistemic audit of the scene-selected third object

## Motivation

MultiObject-2c completed the full scene-memory -> selection -> seed -> growth chain for the third persistent object.  The selected object grew from **38,020** seed surfels to **310,884** surfels over 24 object fixations, remained pure, and left the two existing object maps byte-identical.  Its stereo regime was healthy: target depth recovery was **58.8–77.3%**, median **70.3%**, and the growth image showed filled interiors rather than the edge-lacework seen on the low-texture previous object.

But the frozen FSG6f policy still never returned `no_frontier`.  The run ended on the **24-object-fixation engineering watchdog**, with **650 of 679 frontier voxels still open**.  Good measurement therefore does not by itself imply local-policy termination.

Before spending more attention, MultiObject-2d asks what that remaining frontier means.

## Question

> After a well-measured scene object has grown densely but the frozen local policy still says `continue`, how much of its remaining cyclopean shoreline is genuinely unseen, how much is seen-but-unmeasured, and how much already carries boundary evidence?

This is a read-only audit, not another growth loop.

## Method

1. Consume `selected_object_id` from the completed MultiObject-2c parent; do not hand-pick the object id.
2. Load the selected-object surfel map read-only.
3. Build its cyclopean chart at the established 0.1 degree grid.
4. Reuse the angular footprint implied by the frozen 12 mm association radius at this object's own range.
5. Replay only the saved selected-object observation history: the MultiObject-2b seed and the MultiObject-2c growth looks.  No rendering and no fusion occur.
6. Reuse Cyclopean-1b shoreline states (`UNOBSERVED`, `PHYSICAL_DEPTH_BREAK`, `AMBIGUOUS`, ...).
7. Refine only base `UNOBSERVED` shoreline cells with the Cyclopean-1d observation/measurement states:
   - `NEVER_OBSERVED`
   - `OBSERVED_TARGET_NO_DEPTH`
   - `OBSERVED_TARGET_WITH_DEPTH`
   - `OBSERVED_NONTARGET_ONLY`
   - `MIXED_OBSERVATION`
   - `NO_RANGE_REFERENCE`

No texture threshold, completion interpolation, new geometric tolerance, matcher change or layered occlusion model is introduced.

## Scene-progress principle

The audit describes the selected object's unfinished business but **does not gate scene progress**.

- exterior `NEVER_OBSERVED` > 0 -> `ATTENTION_INCOMPLETE_RETAIN_FOR_REVISIT`
- no exterior `NEVER_OBSERVED`, but target-no-depth remains -> `ATTENTION_COMPLETE_MEASUREMENT_PARTIAL`
- neither remains -> `ATTENTION_COMPLETE_NO_TARGET_NO_DEPTH_RESIDUE`

In every case:

```text
scene_disposition = MOVE_TO_NEXT_OBJECT
```

The next stage is **next-object selection from updated scene memory**.  Any unfinished territory remains in persistent object memory for possible later revisit.

## Deliberately deferred

- watchdog extension or more growth looks;
- automatic scheduler/revisit policy;
- alternate stereo matcher, active illumination or texture rescue;
- completion interpolation or meshing;
- layered spherical depth for occlusion;
- evaluator truth or accuracy claims.

## Expected output

The record contains:

- `object_<id>_epistemic_report.json` — state counts, arcs and chart statistics;
- `object_<id>_epistemic_shoreline.png` — support plus epistemic shoreline visualization;
- `prediction_manifest.json` — integrity and scene-progress disposition.

The scientific question is descriptive: **is the remaining frontier mostly lack of attention, lack of measurement, or already-observed boundary structure?**  Whatever the answer, the scene tour continues.
