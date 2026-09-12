# Decisions

Append a block when something is settled. Keep it to four lines. Never edit an old
block — add a new one that supersedes it and say so. "Overturned if" is the point of
the exercise: a decision no one can imagine reversing was not a decision.

## D1 — Ray-value samples (2026-09-12)

What the downstream matcher consumes is records of (origin, direction, value, footprint),
not rectangular images.
Why: the warped raster is not a uniform lattice, and an image format would silently
impose one. Footprint has to travel with the value because peripheral samples average
over a larger solid angle.
Overturned if: the matcher turns out to need adjacency that the stored raster index
cannot supply.

## D2 — Fixed warp, eye rotates (2026-09-12)

The sampling pattern is a constant table of camera-frame directions and footprints,
computed once. A fixation is a rotation applied to it.
Why: it makes the pattern a property of the sensor rather than of the scene, and it
keeps every fixation comparable.
Overturned if: a content-dependent or anisotropic warp turns out to be needed before
Phase C.

## D3 — Fixed head (2026-09-12)

No translation anywhere in Phases A and B. The eye rotates about its own centre; in
the active loop this is saccades and fixations, and in Phase B also vergence.
Why: with a fixed centre of projection there is no parallax within one eye, so a single
panorama is ground truth for every fixation, and with two fixed centres the baseline is
fixed in the head frame and the epipolar geometry never changes.
Overturned if: head motion becomes part of the question, which would be a new phase,
not a change to these.

## D4 — One repository for Phases A–C (2026-09-12)

Phases A, B and C live here together, as roadmap sections rather than directories.
Why: Phase B adds an eye to Phase A's data structures rather than replacing them, and
splitting would duplicate the sample format and the scene tooling.
Overturned if: Phase C turns out to be a genuinely separate piece of work with its own
dependencies.

## D5 — This repository produces samples; it does not do stereo matching (2026-09-12)

The boundary with `active-stereo` is the sample record. This side generates it, and
anything consuming it lives elsewhere.
Why: keeps an engineering-paced project from inheriting a research-paced one's
governance, and vice versa.
Overturned if: the non-uniform-lattice matcher becomes the main line of work here.

## D6 — The repository is `visgraf/fov-3d-vision`, and the scene tooling lives in it (2026-09-12)

Phases A–C live in `fov-3d-vision`. The scene-gathering tools and manifest, first built in
the public `visgraf/w3d-scenes`, are folded in here rather than kept as a dependency.
Why: A1's manifest is the contract A2–A5 read, so two repositories would let the manifest
and the sample format drift apart, which is exactly the fragmentation this setup is meant
to avoid. Extracting a shared scene library later is cheaper than keeping two in sync now.
Supersedes the naming suggestion in D4; the one-repository substance of D4 stands.
Overturned if: the scene tooling is wanted by another project, in which case `w3d-scenes`
becomes its home and this repository depends on it.
