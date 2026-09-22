# MultiObject-1c — object-143 epistemic audit for scene progress

## Motivation

MultiObject-1b2 revision 2 transferred the frozen single-object grower to object 143 successfully: object 143 grew from 5,344 seed surfels to 42,988 surfels with pure id 143 and object 141 remained byte-identical.  But the run reached the **24-object-fixation engineering watchdog**, not the frozen policy's `no_frontier` stop.  At the final decision the policy still reported 696 open frontier voxels.

The same run also showed that object 143 is a large, smooth architectural surface on which stereo is frequently starved: some views contain tens of thousands of visible id-143 pixels while only roughly 1–3% yield valid depth.  Merely raising the watchdog would therefore mix two different causes of residual frontier:

1. territory that has not yet been looked at; and
2. territory that has been looked at but could not be measured by the current stereo instrument.

MultiObject-1c separates those causes **without taking another look**.

## Question

> What does the remaining object-143 cyclopean shoreline mean after the 24-look run: genuinely unseen territory, seen-but-unmeasured target surface, observed non-target/boundary evidence, or unresolved bookkeeping geometry?

This is an audit, not another completion loop.

## Method

The audit is read-only.

1. Load the completed MultiObject-1b2 object-143 surfel map.
2. Build the object-143 cyclopean chart at the already-established 0.1 degree grid.
3. Reuse the inherited footprint implied by the frozen 12 mm association radius.
4. Replay the **saved** object-143 observation history only as evidence; no rendering and no fusion occur.
5. Reuse the Cyclopean-1b shoreline semantics (`UNOBSERVED`, `PHYSICAL_DEPTH_BREAK`, `AMBIGUOUS`, etc.).
6. Refine only base `UNOBSERVED` shoreline cells with the Cyclopean-1d observation/measurement distinction:
   - `NEVER_OBSERVED`
   - `OBSERVED_TARGET_NO_DEPTH`
   - `OBSERVED_TARGET_WITH_DEPTH`
   - `OBSERVED_NONTARGET_ONLY`
   - `MIXED_OBSERVATION`
   - `NO_RANGE_REFERENCE`

No texture threshold, no new geometric tolerance, no interpolation and no layered occlusion model are introduced.

## Scene-progress principle

The audit records the status of object 143 but **does not gate scene progress**.

- If exterior `NEVER_OBSERVED` remains, object 143 is marked `ATTENTION_INCOMPLETE_RETAIN_FOR_REVISIT`.
- If exterior `NEVER_OBSERVED` is zero but target-no-depth residue remains, object 143 is marked `ATTENTION_COMPLETE_MEASUREMENT_PARTIAL`.
- If neither remains, it is marked `ATTENTION_COMPLETE_NO_TARGET_NO_DEPTH_RESIDUE`.

In all cases:

```text
scene_disposition = MOVE_TO_NEXT_OBJECT
```

This is deliberate.  A full-scene observer cannot require every object to be perfectly reconstructed before attending elsewhere.  Persistent object memory allows later revisit.

## Deliberately deferred

- watchdog extension;
- another object-143 growth look;
- alternate stereo matcher, baseline, active illumination or texture rescue;
- layered spherical depth for occlusion;
- automatic next-object discovery itself (that is the next stage);
- evaluator truth or accuracy claims.

## Expected output

The record contains:

- `object_143_epistemic_report.json` — state counts, arcs and chart statistics;
- `object_143_epistemic_shoreline.png` — support plus epistemic shoreline visualization;
- `prediction_manifest.json` — integrity and scene-progress disposition.

The scientific value is descriptive: it tells us **what kind of unfinished business object 143 carries forward while the scene-level process progresses**.
