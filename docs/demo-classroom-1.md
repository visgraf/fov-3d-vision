# Demo-Classroom-1 — Oracle-assisted concept demonstration in a realistic room

## Purpose

This is the second concept demonstration, following the completed Tabletop demo. The goal is to carry the same active foveal-stereo organism into the repository's realistic Blender Classroom scene without turning the exercise into another controller-research round.

Blender truth is intentionally allowed to scaffold scene grouping, masks, visible seeds, rescue gaze directions, measurement validation, and a special visual background object. The demonstration does **not** claim autonomous discovery, autonomous control, autonomous foreground/background inference, or truth-free stereo confidence.

## Scene binding

The intended live scene is `scenes/classroom/classroom_eye.blend`. The demo must first preflight the actual repository and record the scene hash, metric units, the `EYE`/head camera convention, pose, renderability, and the object/group structure used for reference instance masks. If that binding cannot be established without modifying established source, stop and report a blocker rather than silently switching scenes.

## The hard boundary

Foreground metric geometry must still originate from foveated stereo:

`Classroom foveated binocular acquisition -> established stereo -> oracle validity gate -> established 12 mm fusion -> persistent foreground geometry`

Reference depth may reject a foreground stereo sample. It may not replace the stereo xyz/depth.

The default demo validation gate remains:

`abs(z_stereo - z_reference) <= max(0.10 m, 0.05 * z_reference)`

This is an engineering safety net for the concept demo, not a scientific confidence model.

## Foreground / background

The Classroom is the first demo where the foreground/background idea is used in a scene-adaptive form.

The preferred decomposition is based on the occupied reference-depth distribution. Let `d_near = q70` and `d_far = q90`; pixels transition softly from foreground-like to background-like across that range. Object/group support and angular extent then decide which sufficiently visible nearer groups are reconstructed as stereo foreground. Distant/background-like support is aggregated into **one special background object**.

That special object has deliberately asymmetric responsibilities:

- trivial spherical/shell geometry;
- rich reference RGB texture;
- scene-dependent soft-depth statistics/range;
- no contribution to foreground surfel counts, purity, or stereo depth-error claims.

If the live Blender organization requires an equivalent deterministic decomposition, record the exact rule. Do not hand-pick individual Classroom object names just to make the demo work.

## Attention and control

Use the established local FSG controller when it has an action. When it stalls while Blender reference support says a foreground target remains under-covered, Demo Mode may issue a bounded oracle redirect. This is supervisory scaffolding, not a new general controller.

Engineering guardrails are 24 fixations per foreground object, 6 oracle redirects per object, and 256 total fixations. They are not completeness definitions.

## Deliverables

The run should produce:

- `scene_preflight.json` and `scene_plan.json`;
- stereo-derived foreground point clouds and spherical depth/instance/valid products;
- per-object foreground maps;
- a single adaptive background mask/RGB/soft-depth/shell object;
- a provenance-preserving composite RGB-D scene;
- Blender reference RGB/depth/instance panoramas;
- fixation history, timeline frames, and `demo.mp4` when ffmpeg is available;
- a report that clearly distinguishes foreground reconstruction, background scaffold, reference truth, and the demo composite.

The intended visual story remains:

**look -> stereo -> validate -> fuse -> remember -> redirect attention -> build the room**.
