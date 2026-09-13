# Step A2 — noise floor and reference render

State on 2026-09-13: the noise floor is measured on both mesh scenes and both reference
panoramas are rendered at 8192 spp. Their render times are the uniform-cost baseline at
s0 = 0.05 deg/px. Everything here was run on the workstation (Blender 5.2.1 LTS, OptiX,
RTX 4090) unless marked assumed. See `../README.md` for the project and `../DECISIONS.md`
(D7) for the criterion.

## Criterion (D7)

The reference's relative noise, worst tile and median, must be at most one third of the noise
of the fixation renders it will be compared to, and each scene picks its own spp. Fixation
renders are taken as 1024 spp. From the noise table below, at 8192 spp:

| | reference worst / median | 1024 spp fixation worst / median | ratio worst / median |
|---|---|---|---|
| calib room | 0.0096 / 0.0062 | 0.0281 / 0.0176 | 0.341 / 0.350 |
| Classroom | 0.0336 / 0.0145 | 0.1265 / 0.0442 | 0.266 / 0.328 |

The Classroom meets the bound. The calib room misses it by 2 to 5%: by 1/sqrt(spp) alone,
8x the samples gives a ratio of 0.354, so one third needs a departure from 1/sqrt(spp) in
the right direction, which the Classroom's sqrt2 ratios (1.02 per doubling) supply and the
calib room's (1.006) do not. 8192 spp was rendered for both as instructed; the calib room
would meet D7 at 16384 spp (ratio 0.24, about 65 min: assumed, by 1/sqrt(spp) from the
measured 32 min). Not rendered; this is flagged, not resolved.

The 1% worst-tile target and the one-spp-for-both rule used on the first pass are withdrawn.

## Commands

```bash
python3 tools/check_noise_floor_stats.py                        # host side, numpy only: 13 checks
blender -b scenes/calib_room/calib_room.blend -P tools/noise_floor.py -- --out /tmp/nf --control same-seed
blender -b scenes/calib_room/calib_room.blend -P tools/noise_floor.py -- --out /tmp/nf --control late-read
blender -b scenes/calib_room/calib_room.blend -P tools/noise_floor.py -- --out previews/noise/calib_room
blender -b scenes/classroom/classroom_eye.blend -P tools/noise_floor.py -- --out previews/noise/classroom
# scale test, then the references; --time-write splits the EXR write out of render_seconds
blender -b scenes/calib_room/calib_room.blend -P tools/preview360.py -- --out previews/scale_test --width 7200 --spp 256 --filter BOX --time-write
blender -b scenes/calib_room/calib_room.blend -P tools/preview360.py -- --out previews/reference/calib_room --width 7200 --spp 8192 --filter BOX --time-write
blender -b scenes/classroom/classroom_eye.blend -P tools/preview360.py -- --out previews/reference/classroom --width 7200 --spp 8192 --filter BOX --time-write
.venv/bin/python tools/inspect_preview.py previews/reference/calib_room
.venv/bin/python tools/inspect_preview.py previews/reference/classroom
```
Noise-floor defaults: s0 0.05 deg/px (reference 7200x3600), 6 tiles of 128 px, spp 16..8192
doubling, box filter, no adaptive sampling, no denoising. `previews/noise/<scene>/noise.json`
and `previews/reference/<scene>/{pano.exr,backface.exr,meta.json,report.json}` hold every
number below; they are regenerable and not committed.

## Checks (all measured, 2026-09-13)

| Check | Result |
|---|---|
| `check_noise_floor_stats.py` | 13 checks, `all checks passed`, exit 0 |
| `--control same-seed` (calib room) | max abs A-B 1.192e-07, rel_rms 5.8e-08, threshold 1e-05: PASSED, exit 0 |
| `--control late-read` (calib room) | guard fired (rel_rms 0, max abs A-B 0): PASSED, exit 0 |
| nonexistent `--blend`, all three render tools | `FAILED` line, exit 1 |
| `--time-write` re-save | byte size equal to pano.exr on every run (asserted in the tool) |
| inspect_preview on each reference | hole, backface, nadir and zenith match A1's manifest values (table below) |

## Two things the checks caught

**The seed did not take on the Classroom.** The guard fired on the first Classroom run: seeds
0 and 1 gave the same pixels (rel_rms 4.97e-08). The scene action keyframes `cycles.seed` (one
key at frame 1, value 144, GENERATOR modifier) and every render evaluates the frame, so the
keyframe overwrote the seed the script had just set. `bl_common.pin_seed` now removes any
F-curve or driver on `cycles.seed`; `noise_floor.py`, `preview360.py` and `render_foveated.py`
all call it, and the first two assert after each render that the sampling settings still hold.

**Adaptive sampling was on in calib_room.blend.** The first calib room reference at "8192 spp"
finished in 135 s against 35 min projected: the blend ships with `use_adaptive_sampling` on
(threshold 0.01), `noise_floor.py` turns it off but `preview360.py` did not, so most pixels
stopped early and the file was neither uniform nor at the table's noise. Caught by the
measured/projected ratio, not by the tool. `preview360.py` now forces adaptive sampling off
and `time_limit` 0, asserts both after the render, and records them in meta.json. The
Classroom blend has adaptive sampling off, so its reference was valid on the first run. The
adaptive-on calib room file was deleted and re-rendered. A1's previews were rendered before
this fix; their checks are geometric and do not depend on it.

## Noise floor

rel_rms is sigma/level where sigma = RMS(A-B)/sqrt(2) over the tile and level is the tile's
mean value; "worst" is the maximum over the six tiles, "median" the median over them.

| spp | calib room median | calib room worst | Classroom median | Classroom worst |
|---|---|---|---|---|
| 16 | 0.1532 | 0.2662 | 0.4063 | 1.1481 |
| 32 | 0.1046 | 0.1785 | 0.2768 | 0.7978 |
| 64 | 0.0733 | 0.1266 | 0.1914 | 0.5573 |
| 128 | 0.0521 | 0.0865 | 0.1322 | 0.3852 |
| 256 | 0.0356 | 0.0591 | 0.0922 | 0.2676 |
| 512 | 0.0251 | 0.0403 | 0.0638 | 0.1861 |
| 1024 | 0.0176 | 0.0281 | 0.0442 | 0.1265 |
| 2048 | 0.0124 | 0.0196 | 0.0307 | 0.0818 |
| 4096 | 0.0087 | 0.0136 | 0.0211 | 0.0518 |
| 8192 | 0.0062 | 0.0096 | 0.0145 | 0.0336 |

1/sqrt(spp) check (observed ratio between consecutive spp divided by sqrt 2; expect 1.0):
calib room median 1.006, range 0.993 to 1.035; Classroom median 1.022, range 1.014 to 1.038.

The Classroom's worst tile is its darkest: tile 1 (lon 0, lat -18 deg, under the desks) has
level 0.042 against 0.568 for the brightest tile, which alone reaches 0.0077 at 8192 spp.

Timing from the tiles: call floor 0.060 s / 0.158 s median (calib room / Classroom);
9.92 / 10.43 ns per pixel-sample median, ranges 9.41 to 10.08 / 8.70 to 10.89, fit on
spp >= 256, worst relative residual 0.117 / 0.077.

## Scale test

Calib room at 7200x3600, 256 spp, uniform sampling. Projection from the tiles:
9.92 ns x 25.92 Mpx x 256 + 0.06 s = 65.9 s.

| | measured |
|---|---|
| render_seconds (includes the EXR write) | 63.1 s |
| EXR write alone (re-save of Render Result, same byte size) | 0.38 s |
| measured / projected | 0.958 |
| pano.exr on disk (4 passes, 32-bit, ZIP) | 502 MB |
| inspect_preview.py at 7200x3600 | runs, 14 s; holes 0, backfaces 0, nadir 1.6002 m, zenith 1.6002 m |

The inspect timing and values are from the first scale test, which had adaptive sampling on
(58.2 s, ratio 0.883); the geometry passes do not depend on sampling. The 1.14 GB figure in
the earlier version of this note was the uncompressed size; ZIP brings the calib room to
0.50 GB and the Classroom to 2.0 GB (the Classroom compresses worse).

## References

| | calib room | Classroom |
|---|---|---|
| spp, filter | 8192, BOX 1.0 | 8192, BOX 1.0 |
| render_seconds (includes the EXR write) | 1939.8 s = 32.3 min | 2147.4 s = 35.8 min |
| projected from tiles | 35.1 min | 36.9 min |
| measured / projected | 0.921 | 0.970 |
| EXR write alone | 0.38 s | 1.6 s |
| backface pass (4 spp) | 1.5 s | 10.5 s |
| pano.exr on disk | 501 MB | 2.00 GB |
| hole_fraction (A1) | 0.0 (0.0) | 0.0208 (0.02079) |
| backface_fraction (A1) | 0.0 (0.0) | 0.0038 (0.0038) |
| nadir_depth_m (A1) | 1.6002 (1.60019) | 1.2001 (1.20014) |
| zenith_depth_m (A1) | 1.6002 (1.60019) | 1.6967 (1.69665) |

These render_seconds are the uniform-cost baseline at s0 = 0.05: 32.3 min and 35.8 min for
25.92 Mpx at 8192 spp, each with about a second of file writing inside the timer.

## What is still untested

- The reference's own noise: the table is from six 128 px tiles away from the poles; the
  full panorama is one render, so its noise is inferred from the tiles, not measured. A
  second-seed render of each reference (another 32 to 36 min each) would measure it.
- D7 on the calib room: ratio 0.34 / 0.35 against the one-third bound, see above.
- The 16384 spp figure for the calib room is extrapolated.
- Cost linearity in pixel count is now measured at 256 and 8192 spp (ratios 0.96, 0.92,
  0.97 against the tile projection), so the earlier "assumed" on it is retired within 8%.
