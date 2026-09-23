# Demo-Classroom-1 — Oracle-Attention Concept Demonstration

## Purpose

This is the second concept demonstration after Demo-Tabletop-1. Its goal is to show that the foveated binocular acquisition, established stereo front end, demo measurement validation, 12 mm persistent surface fusion, foreground/background decomposition, and scene export can operate on the realistic Blender Classroom.

It is **not** a controller-generalization experiment.

The live preflight exposed a real repository seam: the FSG6f local controller belongs to the procedural/rectified lineage, whereas Classroom uses the established foveated-warp `.blend` lineage. Rather than redesign a controller inside a demo, Classroom attention is therefore explicitly oracle-driven.

The demo claim is:

> Blender guides where to look and validates measurements; stereo plus persistent fusion builds metric foreground geometry.

## Attention contract

Every Classroom fixation is selected from Blender reference support.

- first fixation for an object: deterministic visible/deep-interior reference support;
- later fixations: deterministic deep/interior **uncovered** reference support after projecting the accumulated stereo map to the reference sphere;
- candidates that violate the established renderer's occupancy/precondition are skipped deterministically;
- no FSG6f action, cyclopean1a probe, or per-object belief.Policy action is used as the Classroom attention controller.

The run and report must say this plainly. `autonomous_controller_tested=false` and `fsg6f_generalization_tested=false` are required.

This choice does not weaken Demo-Tabletop-1, which already demonstrated established local FSG control. The two demos intentionally emphasize different things:

- **Tabletop:** active local control plus reconstruction;
- **Classroom:** realistic-scale foveated perception plus reconstruction.

## Hard geometry boundary

Reference truth may:

- define object/group masks;
- choose gaze targets;
- reject stereo samples whose depth is implausible;
- define the background scaffold and final evaluation products.

Reference truth may **not** insert xyz/depth into metric foreground maps.

Accepted foreground points must be literal rows from the established Classroom stereo output after target-instance and depth-validation filtering. The demo gate remains

`abs(z_stereo - z_ref) <= max(0.10 m, 0.05*z_ref)`.

The 12 mm surface association/fusion rule remains unchanged.

## Scene binding already established by preflight

The live preflight reported:

- `scenes/classroom/classroom_eye.blend`;
- metric scene, 178 renderable meshes;
- fixed `EYE` camera at the manifest pose;
- established `fixation_pairs.PairRenderer` opens/renders the blend;
- established `stereo_field.field_of_pair` produces usable stereo rows;
- stereo xyz conversion to head coordinates is known;
- reference equirectangular RGB/depth/position is viable in the same head convention;
- parent-root hierarchy is a deterministic partition: 178 meshes -> 98 structural entities, 86 reference-visible.

The adapter should re-verify these facts at execution time rather than treating this document as authoritative runtime state.

## Foreground/background decomposition

Use the scene-adaptive rule rather than named Classroom exceptions.

Preferred rule:

1. build the reference panorama and valid occupied depth distribution;
2. compute `d_near = q70` and `d_far = q90`;
3. define a smooth far/background weight over `[d_near,d_far]`;
4. compute each structural entity's visible support and depth/background statistics;
5. explicit foreground entities must have at least `MIN_FOREGROUND_SUPPORT_FRACTION` of occupied reference support and be sufficiently foreground-like under the single deterministic rule;
6. aggregate far/contextual support and visible support not assigned to explicit foreground entities into exactly one `__BACKGROUND__` object.

The ungrouped/non-mesh reference support noted by preflight must not disappear; assign it explicitly to the background aggregate unless a simpler truthful structural treatment is found.

The background may use reference RGB and soft reference-depth statistics plus trivial shell geometry. It is never counted as stereo-reconstructed foreground.

## Foreground object loop

For each planned foreground entity, in deterministic id order:

1. oracle chooses a visible seed gaze;
2. established Classroom foveated binocular pair is rendered;
3. established stereo runs;
4. reference instance/depth filters the target stereo samples;
5. accepted stereo xyz initializes/fuses through the existing 12 mm map;
6. oracle measures remaining target reference support and chooses the next uncovered gaze;
7. repeat until demo target coverage (0.85), no useful oracle support, 24 object fixations, or 256 total fixations.

Use the completed Tabletop demo's inherited empty-look floor, render precondition lesson, fixation ledger, point provenance checks, exports, report, and movie grammar where applicable.

## Required presentation

Keep four products visually and numerically distinct:

A. **STEREO FOREGROUND** — metric observer geometry from accepted stereo only;

B. **BACKGROUND SCAFFOLD** — one oracle/context object with rich texture and soft depth;

C. **REFERENCE TRUTH** — Blender evaluation/guidance products;

D. **DEMO COMPOSITE** — explicitly labelled oracle-assisted, not autonomous.

The timeline/movie should make the story visible:

`oracle gaze -> foveated binocular observation -> stereo -> validation -> fusion -> persistent scene accumulation`.

## What the demo may establish

- the realistic Classroom `.blend` can feed the foveated binocular/stereo pipeline;
- multiple dynamically grouped room entities can be reconstructed into persistent stereo-derived 3-D foreground maps;
- foreground/background layers can coexist with explicit provenance;
- a room-scale composite RGB-D representation and visual acquisition story can be generated.

## What it does not establish

- autonomous discovery;
- autonomous Classroom attention;
- FSG6f generalization to `.blend` mesh scenes;
- truth-free measurement validation;
- autonomous foreground/background decomposition;
- controller optimality;
- complete reconstruction of every mesh component.

The missing generic `.blend` -> FSG-controller bridge remains a real architectural capability gap to address later, not inside this demonstration.
