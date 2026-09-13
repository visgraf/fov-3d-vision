# Step A2 — noise floor and reference render

State on 2026-09-13: the noise floor is measured on both mesh scenes; no reference panorama
has been rendered, because at the spp the rule below selects both would take about ten hours.
Everything here was run on the workstation (Blender 5.2.1 LTS, OptiX, RTX 4090) unless marked
assumed. See `../README.md` for the project and `../DECISIONS.md` for the standing decisions.

## Commands

```bash
python3 tools/check_noise_floor_stats.py                        # host side, numpy only: 13 checks
blender -b scenes/calib_room/calib_room.blend -P tools/noise_floor.py -- --out /tmp/nf --control same-seed
blender -b scenes/calib_room/calib_room.blend -P tools/noise_floor.py -- --out /tmp/nf --control late-read
blender -b scenes/calib_room/calib_room.blend -P tools/noise_floor.py -- --out previews/noise/calib_room
blender -b scenes/classroom/classroom_eye.blend -P tools/noise_floor.py -- --out previews/noise/classroom
```
Defaults: s0 0.05 deg/px (reference 7200x3600), 6 tiles of 128 px, spp 16..8192 doubling,
target rel_rms 0.01 on the worst tile, box filter, no adaptive sampling, no denoising.
`previews/noise/<scene>/noise.json` and `noise.csv` hold every number below; they are
regenerable and not committed.

## Checks (all measured, 2026-09-13)

| Check | Result |
|---|---|
| `check_noise_floor_stats.py` | 13 checks, `all checks passed`, exit 0 |
| `--control same-seed` (calib room) | max abs A-B 1.192e-07, rel_rms 5.8e-08, threshold 1e-05: PASSED, exit 0 |
| `--control late-read` (calib room) | guard fired (rel_rms 0, max abs A-B 0): PASSED, exit 0 |
| nonexistent `--blend` | prints `FAILED: no noise.json was written`, exit 1 |

## What the first Classroom run caught

The guard fired on the Classroom at tile 0, 16 spp: seeds 0 and 1 gave the same pixels
(rel_rms 4.97e-08). Cause: the Classroom's scene action keyframes `cycles.seed` (one key at
frame 1, value 144, with a GENERATOR modifier), and every render evaluates the frame, so the
keyframe overwrote the seed the script had just set; `c.seed` read back as 1 after each render.
Fix: `bl_common.pin_seed` removes any F-curve or driver on `cycles.seed`, `noise_floor.py`
calls it and additionally asserts after every render that seed and sample count still hold
the requested values. `preview360.py` also calls it, so a reference renders with the seed its
command states. `render_foveated.py` does not yet; A3's claims do not depend on the seed value.
The calibration room has no such keyframe: its numbers before and after the fix agree.

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
Both ok. The estimator is behaving on both scenes.

The Classroom's worst tile is its darkest: tile 1 (lon 0, lat -18 deg, under the desks) has
level 0.042 against 0.568 for the brightest tile, which alone reaches 0.0077 at 8192 spp. A
relative criterion on the worst tile is a criterion on the darkest tile.

## Timing

| | calib room | Classroom |
|---|---|---|
| warm-up render, discarded | 0.276 s | 0.631 s |
| call floor (time at 16 spp), median | 0.060 s | 0.158 s |
| call floor, range over tiles | 0.035 to 0.064 s | 0.113 to 0.180 s |
| ns per pixel-sample, median (fit on spp >= 256) | 9.92 | 10.43 |
| ns per pixel-sample, range over tiles | 9.41 to 10.08 | 8.70 to 10.89 |
| worst relative fit residual | 0.117 | 0.077 |

## spp choice and projection

| | calib room | Classroom |
|---|---|---|
| spp meeting worst-tile rel_rms <= 0.01 | 8192, measured (0.00956) | none measured; 92,600 unrounded, 131072 as a power of two: assumed, 1/sqrt(spp) extrapolation from 8192 |
| projected full reference at 8192 spp | 35.1 min | 36.9 min |
| projected full reference at 131072 spp | 561 min | 591 min |

The rule for A2 is one spp for both scenes: the smallest measured spp meeting the target on
both, else the larger extrapolated value. That is 131072 spp, assumed. At that spp both
projections exceed the 90-minute cap, so neither reference was rendered. The projection is
ns-per-pixel-sample times 25.92 Mpx times spp plus the call floor, and assumes cost is
linear in pixel count (measured only at tile size) and that 1/sqrt(spp) holds 16x beyond the
largest measured spp.

The EXR at 7200x3600 with four 32-bit passes is 1.14 GB per scene (arithmetic, not measured).

## What is still untested

- `preview360.py` at 7200 px: never run at that width, so neither the 1.14 GB multilayer
  write nor `inspect_preview.py` on an image that size has been exercised.
- `pin_seed` in `preview360.py` has run on the Classroom only at 256 px, 4 spp (smoke test: it
  removed the key and exited 0), not at reference size.
- Cost linearity in pixel count between a 128 px tile and the full 25.92 Mpx panorama.
- The extrapolation from 8192 to 131072 spp.

## What would change the picture

Not done here, because the target was set before the run: a criterion on the median tile
instead of the worst would need about 8192 spp for the calib room (measured) and about 17,000
spp for the Classroom (assumed, extrapolated from its median 0.0145 at 8192), both around
40 to 80 minutes; a target of 0.02 on the worst tile would be met at 2048 spp on the calib
room (measured) and about 23,000 spp on the Classroom (assumed). Whether the Classroom's dark
regions should set the reference's cost is a decision, not a measurement.
