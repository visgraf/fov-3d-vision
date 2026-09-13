# Step A4 — a fixation sequence

State on 2026-09-13: `tools/fixation_sequence.py` renders a list of gazes in one Blender
session and writes a D1 sample record per fixation; `tools/check_sequence.py` verifies the
record against the scene's reference panorama. Run on both mesh scenes at `--profile small`.
Everything here was measured on the workstation (Blender 5.2.1 LTS, OptiX, RTX 4090) unless
marked assumed.

## Commands

```bash
# Step 0 of this pass: small references (about a minute each), pinned in scenes/manifest.json
blender -b scenes/calib_room/calib_room.blend -P tools/preview360.py -- --out previews/reference_small/calib_room --profile small
blender -b scenes/classroom/classroom_eye.blend -P tools/preview360.py -- --out previews/reference_small/classroom --profile small

# the sequence: 50 calibration targets, and 10 gazes in the Classroom
blender -b scenes/calib_room/calib_room.blend -P tools/fixation_sequence.py -- \
    --out previews/sequence/calib_room --profile small --targets scenes/calib_room/calib_room.targets.json
blender -b scenes/classroom/classroom_eye.blend -P tools/fixation_sequence.py -- \
    --out previews/sequence/classroom --profile small --gazes "0,0;30,0;-30,0;60,0;-60,0;0,20;0,-20;120,0;-120,0;180,0"

# the checks (venv; noise figures are A2's median-tile rel_rms at 64 and 1024 spp)
.venv/bin/python tools/check_sequence.py previews/sequence/calib_room --reference previews/reference_small/calib_room --noise-fix 0.0733 --noise-ref 0.0176
.venv/bin/python tools/check_sequence.py previews/sequence/classroom  --reference previews/reference_small/classroom  --noise-fix 0.1914 --noise-ref 0.0442
```

## The record

Per fixation, `f<NNN>/samples.npz` with a `columns.json` sidecar: `origin` (3,), `direction`
(N,3) unit vectors in the EYE frame from the analytic warp composed with the gaze, `value`
(N,3) linear RGB, `footprint` (N,) steradians, `distance` (N,) metres from the Depth pass,
`fixation_id` (N,), `raster_index` (N,2). Only samples inside the disc (r <= 1). Alongside,
`fix.exr` (all four passes, uncompressed) and `meta.json`; `sequence.json` at the top holds
the gaze list, timings and the timing fit.

Gazes from `--targets` are the target directions turned into (yaw, pitch) in the EYE frame;
wire targets carry only an azimuth and are taken as horizontal at eye height, as the ladders'
`dir_world` shows. The footprint is |d_x x d_y| of the raster-to-sphere map by central
differences over one pixel, evaluated on the analytic warp.

Two Blender facts shaped the tool. Blender's Python cannot read a multilayer EXR back and the
Render Result has no pixel access in background mode, so `fix.exr` is written with
`exr_codec = "NONE"` and parsed by `tools/exr_lite.py` (numpy only); the checker compares it
with the OpenEXR reader on every fixation, and it agrees to the bit. And with persistent data
Cycles re-reads the sample count only when the scene is tagged for update: a change of
`cycles.samples` alone was ignored (16, 256 and 4096 spp all took 16 ms), a seed change or
`scene.update_tag()` made it take. `render_fixation` now tags the scene whenever spp or seed
change, and the sweep renders a seed pair at each level whose noise must fall as 1/sqrt(spp),
which is the check that caught this. `noise_floor.py` and A3 alternated seeds and were not
affected.

## Numbers, small profile (raster 126x126, s0 0.1002 deg, E2 2, e_max 45, 64 spp)

| | calib room, 50 targets | Classroom, 10 gazes |
|---|---|---|
| samples per fixation (in the disc) | 12,492 | 12,492 |
| warm-up render, discarded | 0.309 s | 0.750 s |
| render per fixation, median (range) | 15.2 ms (14.4 to 16.3) | 28.4 ms (25.6 to 32.3) |
| file I/O per fixation, median | 2.9 ms | 6.4 ms |
| render sum / sequence wall (with sweep) | 0.76 s / 5.0 s | 0.29 s / 3.9 s |
| sweep median at 16 / 64 / 256 spp | 8.6 / 15.1 / 39.3 ms | 21.8 / 28.6 / 56.1 ms |
| call floor (time at 16 spp), median (range) | 8.6 ms (7.9 to 9.8) | 21.8 ms (19.6 to 22.8) |
| marginal cost, ns per sample, median (range) | 10.06 (9.50 to 10.56) | 11.21 (8.98 to 12.07) |
| floor as a share of a 64 spp render | 57% | 77% |
| seed-pair rel_rms at 16 / 64 / 256 spp | 0.234 / 0.104 / 0.050 | 0.618 / 0.268 / 0.130 |
| normalised 1/sqrt(spp) ratios | 1.12, 1.05 | 1.15, 1.03 |

The fit is `seconds = floor + slope * samples * spp` on spp >= 64, which with the sweep
16/64/256 is a line through two points (64 and 256); the zero residual is therefore not
evidence. The marginal 10 to 11 ns per sample matches A2's 9.9 and 10.4 ns per pixel-sample
from 128 px tiles, so the per-sample cost of the foveated camera is the same as the uniform
one's, measured. At 64 spp a fixation is dominated by the call floor.

## Checks (all measured)

| | calib room | Classroom |
|---|---|---|
| reader: samples.npz vs fix.exr | exact, all 50 | exact, all 10 |
| (a) warp + gaze vs Position pass, reference px, p99.9 median (worst fixation) | 0.018 (0.064) | 0.018 (0.024) |
| (a) max over all samples | 0.091 px | 0.025 px |
| (b) foveal median rel diff < bound; bound | 13 of 50 pass; 0.0754 | 9 of 10 pass; 0.196 |
| (c) control at 90 deg yaw fails as required | 49 of 50 | 10 of 10 |
| (d) footprints sum to 1.8403 sr | 0.59% low, every fixation | 0.59% low, every fixation |

(a) and (d) pass everywhere; the record's geometry is right. The bound in (b) is
sqrt(noise_fix^2 + noise_ref^2) with A2's median-tile rel_rms at the two spp, combined in
quadrature because the fixation and the reference are independent renders (assumed: that
the tile medians describe the foveal region).

**(b) fails as specified on 37 calibration targets, and the cause is measured.** The checker
also reports an alignment floor: the reference's median relative disagreement with itself
half a pixel away at the same directions. On the 1 to 1.6 deg cards (e 0 and 2.5) it is
0.014 to 0.017 and (b) passes at 0.05 to 0.06; on the wire targets, plain wall behind, it
is 0.008 and (b) passes at 0.03 to 0.04; on the 4 to 11 deg cards the Siemens-star spokes are
resolved at 0.1 deg, the floor is 0.08 to 0.19, and the foveal median is 0.08 to 0.16, tracking
the floor. There is no brightness bias: mean fixation value over mean reference value is
0.996 to 1.013 on every fixation checked. So on those targets (b) measures sub-pixel
alignment on texture edges, not noise, and its bound does not include that. The check is
left as specified; changing its formulation is a decision.

(c) fails to fail on one target, `wire_2mm`: rotated 90 deg the fovea lands on a stretch of
wall like the one behind the wire, median 0.059 against a bound of 0.075.

Classroom: (b) fails on gaze (0, -20), the floor under the desks, at 0.414 with an alignment
floor of 0.127; A2's worst tile was that region (level 0.042 against 0.568 elsewhere) and
its relative noise is far above the median-tile figure the bound uses. Two gazes look through
windows (9,626 and 9,940 hits of 12,492); those samples carry distance 1e10 and are excluded
from (a) and (b).

## Assumed

- The noise bound for (b): tile medians from A2 stand in for the foveal region.
- Cost linearity in samples between 64 and 256 spp (two fit points).
- Wire target directions (horizontal at eye height).

## Untested

- **The full profile.** Nothing here has run at `--profile full` (raster 253, 50,269 samples,
  256 spp). Projected from the small-profile fit: 9 ms + 10 ns x 50,269 x 256 = 0.14 s per
  fixation on the calib room (assumed), 50 fixations in about 7 s plus warm-up; the checks
  against the 500 MB and 2 GB full references have not been run.
- A gaze list longer than 50, and whether the call floor drifts over a long session.
- The record has not been consumed by anything downstream yet; D1's adjacency question
  (raster index as the only neighbourhood) is open.
