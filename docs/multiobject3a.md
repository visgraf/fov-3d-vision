# MultiObject-3a — next-object selection from updated scene memory

## Motivation

The scene now contains three persistent foreground entities.  MultiObject-2d
showed that the third object remains attention-incomplete, but scene progress is
explicitly unblocked.  The next move should therefore be a new scene-level
selection, not another forced completion attempt.

MultiObject-3a repeats the deliberately simple MultiObject-2a decision rule on a
larger memory: all saved observations from the earlier two-object stage plus the
third object's seed and growth history.

## Question

> Given everything the fixed-head observer has already seen, which observed but
> uninstantiated object currently has the largest accumulated usable depth evidence?

## Method

1. Consume the current instantiated object-id set from the completed scene graph;
   do not hard-code object ids in this increment.
2. Reuse the saved old scene history and the saved third-object seed/growth
   history.  No view is rerendered.
3. For every positive instance id that is **not already instantiated**, sum
   `valid & (instance_id == id)` over the complete saved history.
4. Record raw visibility only as a diagnostic.
5. Select the candidate with maximum accumulated valid-depth support; exact ties
   use the smaller integer id.
6. Stop.  The selected object's seed fixation belongs to the next increment.

No threshold, semantic ranking, saliency score, revisit priority or learned
scheduler is introduced.

## Why this is a new step

The rule is unchanged, but the memory is not.  The third object's 24-look
history may expose new objects or greatly change the evidence for candidates
already seen earlier.  This asks whether persistent scene memory can repeatedly
support the sequence

```text
explore current object -> retain unfinished state -> select another object
```

without requiring any existing object to be declared geometrically complete.

## Deliberately deferred

- the selected fourth object's seed fixation;
- growth of that object;
- revisit scheduling for objects retained as incomplete;
- semantic importance/saliency;
- layered occlusion handling;
- evaluator truth or accuracy claims.

## Expected outputs

- `next_object_selection.json` — instantiated ids, candidate table and selected id;
- `prediction_manifest.json` — read-only provenance, complete observation scope and next stage.
