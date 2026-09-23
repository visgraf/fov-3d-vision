# Demo-Tabletop-1 — Oracle-assisted concept demonstration

## Purpose

This is deliberately **not** another controller experiment. It is the first polished concept demonstration of the whole active foveal-stereo scene-construction idea on the established procedural `tabletop_cloth` fixture.

The demo is allowed to use Blender evaluator information as supervisory scaffolding. The purpose is to show the architecture working end-to-end, not to claim autonomous discovery or a truth-free controller.

## The one hard boundary

Blender may tell the demo **what object is visible, where to look, and whether a stereo depth is plausible**. It may not silently replace foreground stereo geometry with evaluator geometry.

Foreground metric points therefore have this provenance:

`foveated binocular render -> established stereo -> oracle validity gate -> established fusion -> persistent foreground geometry`

A reference point may reject a stereo sample; it does not become the accepted sample.

## Background

For the Tabletop demonstration, `rc1_wall` is explicitly declared a special background object. It is exported as a separate visual layer with trivial/soft-depth support and reference texture. It is not counted as stereo-reconstructed foreground geometry.

This is a demonstration scaffold and an initial concrete use of the foreground/background idea. The future research problem is to infer this decomposition and its soft depth regime rather than declare it.

## Attention

Normal local FSG control is reused whenever it produces an action. When it stalls while Blender says relevant target support remains, Demo Mode may issue a bounded oracle redirect. This is intentionally called **oracle attention assistance**, not a new general controller.

## Measurement validation

The demo records raw stereo and oracle-accepted stereo separately. The default demo gate is:

`abs(z_stereo - z_reference) <= max(0.10 m, 0.05 * z_reference)`

This is an engineering aid for the concept demo, not a scientific estimate of stereo confidence.

## Deliverables

The run exports:

- stereo-derived foreground point clouds and spherical depth/instance products;
- a separate oracle background visual layer;
- a provenance-preserving composite RGB-D demonstration product;
- the Blender reference products;
- a fixation timeline, and an MP4 when `ffmpeg` is available;
- a manifest/report that labels every layer and every use of truth.

The visual story should make the cycle legible: **look -> stereo -> validate -> fuse -> remember -> redirect attention -> build scene**.
