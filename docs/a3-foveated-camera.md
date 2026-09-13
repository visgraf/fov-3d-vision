# Step A3 — the foveated camera

Status: **done**. Verified on CPU, then on an RTX 4090 through OptiX. The custom camera runs
on the GPU; no fallback is needed and A4/A5 can use real renders rather than resampling.

## The warp

Sample spacing grows linearly with eccentricity, `s(e) = s0 * (1 + e/E2)`, which integrates
to a raster radius `w(e) = (E2/s0) * ln(1 + e/E2)`. Normalising by the rim value removes
`s0` from the shader:

    e(r) = E2 * ( (1 + e_max/E2)^r - 1 )        r in [0,1], centre to rim

`s0` is then whatever the resolution makes it: `N = 2 * (E2/s0) * ln(1 + e_max/E2)` pixels
across. `render_foveated.py` computes `N` from `--s0`, or takes `--n` and derives `s0`.

At `s0 = 0.05°`, `E2 = 2°`, `e_max = 45°` the raster is 253x253 and holds 50,269 samples
inside its disc, against 2,553,563 for uniform sampling at `s0` over the same field:
**50.8x fewer rays**, measured.

Where those samples go, at the same parameters:

| eccentricity | spacing there | raster radius r | share of samples inside |
|---|---|---|---|
| 2° | 0.10°/sample | 0.22 | 5% |
| 5° | 0.18° | 0.40 | 16% |
| 10° | 0.30° | 0.57 | 32% |
| 20° | 0.55° | 0.76 | 58% |
| 45° | 1.18° | 1.00 | 100% |

16% of the samples land inside 5°, which is 0.19% of the field.

Widening is cheap because the radius is logarithmic: 20° to 45° costs 1.7x in raster area,
45° to 80° a further 1.4x. So `e_max` is chosen for how much peripheral context each
fixation should carry, not for cost. `E2` is the knob that actually sets the budget and is
the one to sweep.

## Files

    tools/foveated_camera.osl    the camera shader
    tools/render_foveated.py     renders one fixation; --yaw / --pitch set the gaze
    tools/check_foveated.py      verifies a render, and compares two

## Verified on CPU (Blender 5.2.1, bpy module, calibration room)

* **Depth is still ray distance** through a custom camera: max error 5.8e-7 m against
  `|Position - centre|`. This was the main risk and it is answered.
* **The warp matches the formula**: p99.9 error 0.005°, rim lands at 44.995° against a 45°
  target, centre at 0.000°.
* **Clipping works**: outside the disc, zero throughput leaves the depth pass reading
  background for every pixel.
* **Gaze convention**: `--yaw` positive turns right, `--pitch` positive turns up, and the
  resulting elevation equals `--pitch` exactly. Verified at yaw 20°, pitch -5°.

Three things that cost time, recorded so they do not cost it again:

* `P` is a reserved global in OSL; a camera shader using it as a variable will not compile.
* `hypot` does not exist in OSL.
* Zero throughput suppresses radiance and leaves depth reading background, but **alpha stays
  1**, so alpha is not a valid mask. Rim pixels are partly covered and pick up some
  radiance. Mask with the analytic `r <= 1` test on the raster index, which the sample
  record stores anyway.

A note on the warp check: it is scored on the p99.9, not the max. The Position pass averages
across a pixel's footprint, which at the rim spans a whole degree, so a pixel straddling a
depth discontinuity reports a direction that is not its centre's. That inflates the max
(0.030° here) while the mapping itself is good to 0.005°.

## The OptiX question, answered

Measured on the calibration room at s0 = 0.02 (631x631 raster), 256 spp: OptiX 3.45 s against
CPU 16.1 s, a 4.66x speedup, with `rel_diff_median` 3.5e-6 and every check passing on the GPU
(depth 7.1e-7 m, warp p99.9 0.00033 deg, rim 44.9987 deg). Cycles selected OPTIX, and 4.66x is
far from the ~1.0 a silent fallback would produce.

Two readings worth keeping. First, 4.66x is a floor, not the asymptotic ratio: a foveated
render is small, so a fixed per-call cost (scene sync, BVH, OSL compile to PTX) is a large
share of 3.45 s. Second, `rel_diff` is *not* a noise measurement — both runs used seed 0 and
Cycles is deterministic across devices at a given seed, so the small tail (p99 0.7%) is most
likely sub-pixel direction differences flipping which side of a geometric edge a sample lands
on, not Monte Carlo variance.

The command that produced it:

```bash
cd fov-3d-vision
blender -b scenes/calib_room/calib_room.blend -P tools/render_foveated.py -- \
  --out previews/spike/cpu   --device CPU   --spp 256 --s0 0.02
blender -b scenes/calib_room/calib_room.blend -P tools/render_foveated.py -- \
  --out previews/spike/optix --device OPTIX --spp 256 --s0 0.02
.venv/bin/python tools/check_foveated.py previews/spike/optix --compare previews/spike/cpu
```

`--s0 0.02` gives a 632x632 raster, large enough that the timing difference is unambiguous.

`--s0 0.02` gives a 631x631 raster (not 632; `N` rounds down), large enough that the timing
difference cannot be ambiguous.

The warp error also fell from 0.005 deg at s0 = 0.05 to 0.00033 deg here, and the max
converged onto the p99.9 (0.00035 against 0.00033). That is the footprint explanation
confirmed from the other direction: rim pixels are 2.5x smaller at this s0, so there is much
less averaging across depth discontinuities inside a pixel.
