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

## D7 — Reference noise at most a third of the fixation noise it is compared to; spp per scene (2026-09-13)

The reference panorama's relative noise, worst tile and median, must be at most one third of
the noise of the fixation renders it will be compared to; each scene picks its own spp.
Why: the reference exists to read fixation renders against, so its noise only needs to be
negligible relative to theirs; a fixed 1% worst-tile target was set by the darkest patch of
the Classroom and cost ten hours. Supersedes the one-spp-for-both rule and the 1% target.
Overturned if: a matcher turns out to be sensitive to reference noise below that ratio, or
fixation renders go above 1024 spp.

## D8 — Error is measured footprint-aware (2026-09-13)

Each integrated cell is compared to the reference box-filtered to that cell's effective
footprint, centred on the centroid of the samples that reached it, so error is measured at
the resolution the sampling provides there and where its samples are; the resampling floor
(per-sample nearest-pixel disagreement) is reported separately, never folded into the bound.
Why: a fixed-resolution metric would charge the periphery for resolution it was never asked
for and hide that the fovea's error is set by registration and noise, not by content.
Overturned if: the matcher needs a metric at a fixed resolution.

## D9 — The error-versus-budget curve is measured at a declared evaluation scale (2026-09-13)

The curve is measured at s_eval = 2 x s0 (0.2 deg small, 0.1 deg full): the representation is
reconstructed over the sphere at s_eval and compared to the reference filtered to s_eval, at
the targets and over the sphere, with the uncovered fraction beside. D8 remains the
per-sample validation check.
Why: D8 compares each cell at its own footprint, so a coarse uniform render is charged only
for its noise and never for its blur, which is how 2.3 deg pixels "won" at K = 1.
Overturned if: a matcher is shown to need a different scale.

## D10 — Check thresholds are set from measured noise and scene-bounded contrast, not fixed constants (2026-09-13)

The calibration point passes when the metric's score over the render's own seed-pair noise at
s_eval lies in 1.0 to 1.15; the 90 deg control must be at least 3x the largest-K target error;
the D8 validation bound per fixation is 1.5 sqrt(n^2 + (n/4)^2 + floor^2) with n the
fixation's seed-pair noise and floor its binned alignment floor, both measured.
Why: fixed constants were set at the wrong scale (0.073 was the per-pixel noise) or above what
a scene's contrast can deliver (5x on a room whose worst case is a wall against a star card).
Overturned if: a threshold set this way lets a known-wrong result pass a check.

## D11 — E2 = 2 deg and e_max = 45 deg stand, pending the objective (2026-09-13)

The A6 sweep at equal rays favours E2 = 4 for the fixated targets (0.103 against 0.155) and
E2 = 1 for the covered sphere (0.203 on 58% against 0.435 on 22%); e_max 45 wins the targets,
30 the sphere. The criteria disagree, so the profiles keep E2 = 2, e_max = 45 rather than
move on one of them.
Why: the choice is the objective's, and the objective (what the matcher needs: fovea,
coverage, or a budgeted mix) is Phase C's to set.
Overturned if: the objective is fixed to one criterion, in which case the sweep already names
the value, or a policy trades E2 against K.

## D12 — Two eyes on the EYE rig; the D1 record gains an origin per eye (2026-09-14)

EYE stays the head frame and the cyclopean point. The eye centres are at +-ipd/2 on its local
X (63 mm default), each eye a rotation of the same foveated camera about its own centre; a
verged pair fixates one world point, each eye's gaze P - C_i, yaw-then-pitch, no torsion. The
record is D1 with origin = this eye's centre plus eye_id and pair_id, directions still in the
head frame; per-eye folders L/ and R/ are Phase A sequences, pairs.json holds the rig.
Why: the scenes and every Phase A tool stay as they are; only the checker needs the centre.
Overturned if: torsion (Listing's law) is needed for rectification, which changes the gaze
composition in rig.py and not the record; or if a matcher needs the two eyes in one file.

## D13 — Ground truth is a derived sidecar; the epipolar frame is the head's X axis (2026-09-15)

Stereo truth (hit point, the other eye's direction to it, parallax, where it falls in the other
raster, visibility) is computed host-side from the Position and Depth passes and written as
truth.npz beside samples.npz; the D1 record stays what the renderer emitted. Epipolar
coordinates of a head-frame direction are theta from +X (the baseline) and phi about X.
Why: with both centres on X every epipolar plane contains X, so rectification is this one
change of coordinates and needs no re-render; a derived label that is regenerable in seconds
should not be baked into the record.
Overturned if: a matcher needs the truth interleaved with the samples in one file, or the eyes
leave the head's X axis (a tilted or asymmetric rig).

## D14 — Eye torsion is moot while the warp is isotropic (2026-09-15)

No torsion model (Listing's law or other) in Phases B and C. Closes B1's open item.
Why: the record stores directions in the head frame and the warp is radially symmetric about
the gaze (D2), so a torsion of the eye changes which raster pixel sampled which direction and
nothing a consumer of the record can see; epipolar geometry is set by the two centres alone.
Overturned if: D2 is overturned by an anisotropic warp, in which case torsion sets its
orientation and rig.py's gaze composition must model it.
