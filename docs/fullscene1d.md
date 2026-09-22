# FullScene-1d — read-only epistemic audit of the locally resolved object

## Why this stage exists

FullScene-1a established the field-test initial condition and selected the sole known uninstantiated object. FullScene-1b seeded that object with one prescribed fixation. FullScene-1c then grew the same dynamically selected object with the unchanged local machinery.

FullScene-1c reached a genuine frozen-policy `no_frontier` stop after only seven object fixations, well before the 24-fixation watchdog. The important detail is that this stop differs structurally from the earlier object-145 stop: its final trace has **zero OPEN frontier entries**. Every remaining local frontier entry is boundary-resolved under the controller's existing rules.

That makes the next question epistemic rather than geometric.

## Central question

> When the local 3D controller says that every remaining frontier is resolved, does the cyclopean evidence agree that attention/measurement is resolved, or has the controller merely enclosed the measurable subset of the object?

This is deliberately a **read-only audit**. It does not rescue the stopped controller.

## Method

1. Consume the selected object id and scene-object set from the completed FullScene-1c parent; do not hard-code an object id.
2. Require the parent to be the genuine FullScene-1c `no_frontier` scientific stop reached before its engineering watchdog.
3. Require the saved final policy trace to have `frontier_open_count == 0` and zero candidates before consensus.
4. Load the final selected-object surfel map and all scene-object geometry read-only.
5. Replay only the selected object's established local history: the saved FullScene-1b seed observation followed by the saved FullScene-1c growth observations. Do not rerender anything and do not broaden the audit with older S0 scene-memory observations in this increment.
6. Reuse the established MultiObject-3d / Cyclopean audit machinery unchanged:
   - 0.1 degree cyclopean chart;
   - current 12 mm association semantics;
   - Cyclopean-1b shoreline classification;
   - Cyclopean-1d observation-versus-measurement refinement;
   - exact frozen-policy replay and 3D-frontier-to-cyclopean relation.
7. Classify the residual shoreline and distinguish exterior from internal components.
8. Return to scene inventory after the audit regardless of the diagnostic result. No scheduler is created here.

## Epistemic states

The refined residue uses the already-established states:

- `NEVER_OBSERVED`
- `OBSERVED_TARGET_NO_DEPTH`
- `OBSERVED_TARGET_WITH_DEPTH`
- `OBSERVED_NONTARGET_ONLY`
- `MIXED_OBSERVATION`
- `NO_RANGE_REFERENCE`

Base shoreline states such as `PHYSICAL_DEPTH_BREAK` and `AMBIGUOUS` remain reported separately.

## Interpretation without a new threshold

The audit uses literal zero/non-zero states only.

- exterior `NEVER_OBSERVED > 0` means attention debt remains even though the local 3D frontier is fully resolved;
- otherwise, `OBSERVED_TARGET_NO_DEPTH > 0` means the audit is attention-complete under its local history but measurement-partial;
- otherwise the local frontier and epistemic audit are both resolved under the current representation.

None of these labels is object completeness or accuracy.

## Strong negative contract

FullScene-1d adds:

- no Blender launch;
- no fixation;
- no fusion;
- no map growth;
- no epistemic handoff;
- no execution of the prior object's deferred action;
- no scene/revisit scheduler;
- no discovery or semantic ranking;
- no evaluator truth;
- no new threshold or quality gate.

All scene geometry and all saved observations are pinned and re-hashed after the audit.

## Expected outputs

The output record contains:

- `object_<id>_fullscene1d_epistemic_audit.json` — shoreline census, refined arcs, exact final-policy replay, frontier/cyclopean relation and interpretation;
- `object_<id>_fullscene1d_epistemic_shoreline.png` — diagnostic support/shoreline visualization;
- `prediction_manifest.json` — provenance, read-only integrity and compact summary.

The next stage is **FullScene-1e: return to the scene inventory and recompute the set of known uninstantiated candidates using the updated observation history.**
