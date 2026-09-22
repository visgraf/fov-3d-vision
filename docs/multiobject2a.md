# MultiObject-2a — next-object selection from saved scene evidence

## Motivation

MultiObject-1c established a scene-progress principle: an object may remain partially measured or even slightly attention-incomplete without blocking exploration of the rest of the scene. Object 143 is therefore retained for possible revisit while the scene moves on.

The next new problem is no longer local surface growth. It is a scene-level question:

> Which object should receive attention next?

MultiObject-2a answers only that question. It is deliberately read-only and takes no new fixation.

## Candidate set

The current scene already contains oracle instance ids visible incidentally in saved observations that have not been instantiated as persistent foreground objects. MultiObject-2a forms candidates from:

1. the saved scene-history observations used by the MultiObject-1c ancestry;
2. positive integer instance ids with **valid stereo depth** in those observations;
3. excluding already-instantiated objects 141 and 143.

Visibility by itself is not selection support. A candidate receives support only where the existing stereo front end produced valid depth.

## Selection rule

For each uninstantiated candidate object id, sum its number of valid-depth samples over the saved observation history.

Select the object with the largest accumulated valid-depth support. If two candidates have exactly the same support, choose the smaller integer id.

There is:

- no minimum-support threshold;
- no semantic preference;
- no saliency model;
- no learned ranking;
- no hand-picked next id;
- no new scene scheduler beyond this one deterministic decision.

## Scope

This step does **not** seed the selected object. It does not render, fuse, grow, revisit or change either existing object.

Outputs:

- `next_object_selection.json` — candidate support table and deterministic selection;
- `prediction_manifest.json` — integrity/provenance and next-stage declaration.

The next stage is one prescribed seed fixation for the selected object.

## Interpretation

MultiObject-2a marks the first transition from object-local control to scene-level attention management. The decision is intentionally simple: use evidence already in memory and choose the uninstantiated object for which the current instrument already possesses the greatest valid geometric support.
