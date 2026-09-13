> Audit of `tools/noise_floor.py` run on the workstation (Blender 5.2.1, OptiX,
> RTX 4090, calib room), 2026-09-12. Reproduced verbatim.

Audit complete. Everything below is from this machine: Blender 5.2.1 LTS, OptiX, RTX 4090, calib room. Nothing was changed.

**Interpreter tested against:** Blender's bundled CPython **3.13.13** at `/opt/blender-5.2/5.2/python/bin/python3.13`. The project venv is CPython **3.12.3**. Both measured.

## 1. Imports — clean, one leftover

I AST-scanned every import in all 10 files in [tools/](tools/), then tried each module name inside Blender's interpreter. Blender-side scripts (those importing `bpy`, run via `blender -b -P`) are `bl_common`, `make_calib_room`, `make_hdri_scene`, `noise_floor`, `place_eye`, `preview360`, `render_foveated`. Their combined imports are `__future__, addon_utils, argparse, bl_common, bpy, itertools, json, math, mathutils, numpy, os, sys, time, traceback` — **all present** (measured). No remaining Blender-side script imports anything Blender lacks.

The two files importing OpenEXR/PIL are [check_foveated.py:26-27](tools/check_foveated.py#L26-L27) and [inspect_preview.py:23-24](tools/inspect_preview.py#L23-L24); both are documented host-side (`python tools/...`) and neither imports `bpy` (measured). Blender's Python lacks OpenEXR and PIL; the venv has them but lacks `bpy` (both measured) — the split is real in both directions.

Loose end: [noise_floor.py:37](tools/noise_floor.py#L37) still imports `configure_multilayer_exr` and never uses it (grep: one occurrence). Harmless, but it is precisely the multilayer writer the rewrite exists to avoid.

## 2. read_rgb — assumptions hold; save_render is load-bearing

On a real tile (measured): `img.type` `'IMAGE'`, `img.size` **(127, 128)**, `img.channels` **4**, `is_float` True, `depth` 128, `alpha_mode` `'PREMUL'`, colorspace `'Linear Rec.709'`. `read_rgb` returns (128, 127, 3) float32 and agrees with the OpenEXR reader to **max|diff| = 0.000e+00**. Bottom-up rows confirmed.

Three caveats, all measured:
- Size is **127×128, not 128×128** — border rounding. `--tile-px` is not the tile you get. Handled downstream at [line 152](tools/noise_floor.py#L152).
- `'PREMUL'` is a no-op only because alpha is exactly 1.0 everywhere (min = max = 1.000000), which holds only because [line 113](tools/noise_floor.py#L113) forces `film_transparent = False`. Nothing asserts it.
- `img.pixels[:]` at [line 55](tools/noise_floor.py#L55) builds a Python list: 1.5 ms vs 0.1 ms for `foreach_get`, **22× slower**. Negligible at 128 px and outside the timer, but it scales with tile area.

**`save_render` does honour `scene.render.image_settings`, decisively** — so [lines 124-127](tools/noise_floor.py#L124-L127) are load-bearing, not decoration. Measured: with `color_depth="16"` the file's channels come back **float16** (one pixel moved 0.14521 → 0.14526, ~3.4e-4 relative); with `file_format="PNG"` it wrote **an actual PNG to a path named `.exr`** (magic `\x89PNG`, reloading as 8-bit sRGB). The extension does not pick the format. It is correct today, but a half-float file would put a ~3e-4 floor under σ — about 5% of the measured σ = 5.604e-03 at 512 spp — and nothing would report it.

## 3. Seeds — they work, but the estimator rests on an unguarded ordering invariant

**This is the most serious finding.** Seeds do decorrelate as written. Measured at the tool's own defaults, tile 0, OptiX:

| spp | σ = RMS(A−B)/√2 | rel | ratio vs previous |
|---|---|---|---|
| 16 | 3.501e-02 | 0.126 | — |
| 32 | 2.370e-02 | 0.085 | 1.477 |
| 64 | 1.661e-02 | 0.060 | 1.426 |
| 128 | 1.204e-02 | 0.043 | 1.380 |
| 256 | 8.020e-03 | 0.029 | 1.501 |
| 512 | 5.604e-03 | 0.020 | 1.431 |

Ratios cluster on the 1.414 expected for 1/√spp, and same-seed renders differ by at most 1.490116e-07 (float32 accumulation order on GPU; exactly 0.000e+00 on CPU). Seed 0 vs 1, 7, 12345 all differ by RMS ≈ 2.3e-2 at 64 spp.

But the correctness depends entirely on *when the file is read*, and that is written nowhere. The tool renders → saves → reads inside the seed loop at [lines 147-150](tools/noise_floor.py#L147-L150). Measured: with that ordering, max|A−B| = **2.499065e-01**. Issue both renders before the reads — two distinct paths, or a held `Render Result` reference — and both files come back with **identical pixels, max|A−B| = 1.490116e-07**. σ then collapses by six orders of magnitude, `rel_rms` reads ≈ 6e-8, and the tool would announce `chosen_spp = 16` with a confident projection.

I hit this by accident in my first probe and spent three runs proving it was my error and not the tool's. That is the point: the failure produces plausible numbers, not an exception, and there is no assertion defending the ordering.

## 4. Border with persistent data — no staleness found

Measured with `use_persistent_data = True`: tile 0 mean 0.277533, tile 3 mean 0.189443, **max|t0−t3| = 4.714382e-01**; returning to tile 0 reproduced it to 1.490116e-07. Borders take effect and are not cached.

## 5. The a + b·spp fit — the offset is not stable and the model is wrong at the low end

From running your exact command (11.9 s, 6 tiles × 8 spp):

| tile | a (s) | b (s/spp) | resid max | resid rms | worst rel resid |
|---|---|---|---|---|---|
| 0 | 0.0627 | 1.338e-04 | 0.0902 | 0.0370 | **63.3%** |
| 1 | 0.0363 | 1.528e-04 | 0.0149 | 0.0067 | 24.5% |
| 2 | 0.0299 | 1.605e-04 | 0.0039 | 0.0024 | 8.8% |
| 3 | 0.0294 | 1.517e-04 | 0.0029 | 0.0020 | 6.9% |
| 4 | 0.0382 | 1.437e-04 | 0.0116 | 0.0086 | 20.7% |
| 5 | 0.0279 | 1.570e-04 | 0.0030 | 0.0017 | 5.8% |

All measured. The intercept ranges 0.0279–0.0627 s — a spread of **105% of its own median**, while the reported `render_call_overhead_seconds` is a single number, 0.033 s. The slope is by contrast stable: 18% spread, median 1.523e-04 s/spp.

Two causes, both measured. Tile 0's first render took **0.155 s at 16 spp against 0.029–0.037 s for every other tile at the same spp** — one-time warm-up charged entirely to tile 0, giving it a *negative* low-end marginal cost of −7.125e-03 s/spp. And linearity genuinely fails below ~256 spp: times go 0.030 → 0.068 s for 16 → 256 spp (16× the samples for 2.3× the time), then 0.068 → 0.354 s for 256 → 2048 (8× for 5.2×). Per-tile marginal cost differs 2–8× between the low and high end. The data look like `time ≈ max(fixed, b·spp)`; fitting a straight line makes `a` absorb curvature rather than measure a fixed cost. That the warm-up is kernel/BVH build is assumed — measured is only that the first render is 4–5× slower.

Two smaller things feeding the same fit. `seconds` is rounded to 3 decimals at [line 164](tools/noise_floor.py#L164) before being fitted at [line 186](tools/noise_floor.py#L186) — a 3.4% quantum on the 0.029 s values that determine the intercept (measured). And tiles are not all the same size: the run produced both **16256 and 16384**-pixel tiles (measured), compared in the fit as if equal, with [line 195](tools/noise_floor.py#L195) taking a median for the projection.

## Additional findings

**The projection is absent for your command.** `chosen_spp` is `null` and `reference_projection` is `null`, because even 2048 spp gives `rel_rms_worst` 0.01941 against the default `--target 0.01` (measured). Reaching 0.01 needs ≈7700 spp by 1/√spp extrapolation (assumed). The tool says so plainly rather than guessing, which is right — but the headline cost answer isn't there.

**The projection ignores the fixed cost and assumes linearity in pixels** ([line 196](tools/noise_floor.py#L196)): `seconds_full = per_spp_s * chosen * (width*height)/tile_pixels`. That a 25.92 Mpx render costs 1594× a 16 kpx tile is assumed and untested at any intermediate size.

**σ and rel_p99 are different statistics** ([lines 156-157](tools/noise_floor.py#L156-L157)): `sigma` is an RMS, `per_px` is a mean absolute difference over channels. For Gaussian noise E|X| = σ√(2/π) ≈ 0.798σ, so the two are on scales differing by ~20% and `rel_p99` is not comparable to `rel_rms` (the Gaussian factor is assumed; that the formulas differ is measured).

Housekeeping that did work: the `finally` at [lines 168-170](tools/noise_floor.py#L168-L170) removed `_tile.exr`, and `noise.json` and `noise.csv` were both written.
