# Log

Newest last. A few lines per entry: what was run, what came out, what it changed.
Numbers get a "measured" or "assumed" label.

## 2026-09-12 — step 1 tooling written and exercised on CPU

Wrote `tools/` (calibration-room generator, HDRI scene wrapper, 360° preview, inspector,
Poly Haven fetcher). All of it ran in the Chat sandbox against Blender 5.2.1 as a Python
module, CPU only.

Measured, in that sandbox:
- Calibration room preview at 1024×512, 24 spp: 64 s; hole fraction 0, backface fraction 0;
  nadir and zenith depth both 1.600 m, which matches the 1.6 m eye height and the 3.2 m ceiling.
- HDRI path against a synthetic panorama: column shift 0 px, median relative error 0.34 %.
  Negative control, eye rotated 90°: shift 128 px = W/4, as expected.
- Backface detector positive control, one wall's normals flipped: 11.0 % of the sphere.

Learned about Blender 5.2, all measured:
- Multilayer EXR writes one part per pass by default; a reader that looks only at part 0
  sees just Combined. `use_exr_interleave = True` puts them back in one part.
- The equirect camera's depth pass is ray distance from the eye centre, matching |P − c|
  to 3e-7 m. Background reads 1e10.
- The Normal pass flips back-facing normals toward the camera, so it cannot detect
  back-faces. A Backfacing-emission override pass can.

Not tested: the OptiX path, the live Poly Haven API, any real demo file.

## 2026-09-12 — step A1 completed on the GPU (Claude Code, `w3d-scenes`)

All three tiers run on an RTX 4090 through OptiX at 2048x1024, 1.3-5.2 s each. Full numbers
in `scenes/manifest.json`; the three open items from the handover are now closed.

Measured:
- Calibration room: hole fraction 0, backface fraction 0, nadir and zenith 1.60019 m. The
  contact sheet matches the CPU reference structurally, and re-running reproduces
  `report.json` field for field.
- HDRI `workshop` (Poly Haven, CC0, 8k, md5 verified on download): column shift 0,
  rel_err_median 0.0152. Negative control on this machine: 512 px = W/4.
- Classroom (CC0, Christophe Seux): hole fraction 0.0208 (window panes only), backface
  fraction 0.0038, nadir 1.20014 m against a chosen 1.2 m eye height. From the file's own
  shot camera instead, backface fraction was 0.136 - the camera sits 0.46 m off the rear
  wall and sees its back side. Moving the eye into the room is a 36x reduction.

Two findings worth keeping:
- `rel_err_median` has a floor set by the reconstruction filter, not by the mapping or by
  sample count: 16 -> 512 spp moves it 0.0152 -> 0.0154, while a box filter gives 0.0032.
  This matters beyond the identity check, because the footprint omega that travels with each
  sample only means "the average over this solid angle" under a box filter.
- `rotation_euler` does not reach `matrix_world` until the depsgraph runs. Anything that
  repositions the eye must call `bpy.context.view_layer.update()` first, or the old pose is
  silently rendered.

## 2026-09-12 — merged into `fov-3d-vision`

`w3d-scenes` folded in as step A1 (D6). The six handover tools came back byte-identical, so
the only new code was `tools/place_eye.py`. Two changes made while merging, both from the
findings above and both re-run on CPU in the sandbox:
- `preview360.py` gained `--filter` / `--filter-width`, defaulting to Cycles' own filter and
  to width 1.0 for BOX, and records both in `meta.json`. Measured on the synthetic panorama:
  rel_err_median 0.0034 with the default filter, 0.0018 with `--filter BOX`.
- `preview360.py` calls `view_layer.update()` before reading the eye pose.

## 2026-09-12 — A3 spike: the foveated OSL camera works on CPU

Built `tools/foveated_camera.osl`, `tools/render_foveated.py`, `tools/check_foveated.py` and
ran them on the calibration room in the sandbox, Blender 5.2.1, CPU. Details and the warp
table in `docs/a3-foveated-camera.md`.

Measured, at s0 = 0.05 deg, E2 = 2 deg, e_max = 45 deg, raster 253x253:
- Depth through a custom camera is still ray distance: max error 5.8e-7 m.
- Warp matches the formula to 0.005 deg at p99.9; rim 44.995 deg against a 45 deg target.
- 50,269 samples inside the disc against 2,553,563 uniform at s0 over the same field: 50.8x.
- Clipping: zero throughput leaves depth reading background for every pixel outside the disc.
- Gaze: +yaw right, +pitch up, elevation equals --pitch exactly (checked at 20 / -5).

Two defects the checker caught while being written, both fixed:
- Yaw came out mirrored and pitch was off by a factor cos(yaw), because the Euler order
  applied pitch before yaw. Now an explicit intrinsic yaw-then-pitch composition.
- `--compare` happily compared two different gazes. It now fails if the warp parameters,
  gaze, spp or source file differ.

Assumed, not measured: that a custom camera runs on OptiX rather than silently falling back
to CPU. That is the one open item and needs the GPU.

## 2026-09-12 — A3 spike passed on the GPU

Calibration room, s0 = 0.02 (631x631), 256 spp, on the RTX 4090. Measured: OptiX 3.454 s
against CPU 16.1 s, speedup 4.66; depth max error 7.1e-7 m; warp p99.9 0.00033 deg, max
0.00035 deg, rim 44.9987 deg; 312,745 samples inside the disc against 15,884,163 uniform at
s0, 50.8x; clipping clean; no checks failed. A3 is done and the custom camera is usable.

Two things that change what comes next:
- 4.66x is a floor, not the asymptotic speedup. A foveated render is small, so fixed per-call
  cost is a large share of 3.45 s. A4 must therefore measure the *marginal* cost of a
  fixation inside one Blender session with persistent data, not total time divided by N, or
  the budget will measure scene setup.
- `rel_diff_median` 3.5e-6 is not a noise estimate: both runs used seed 0 and Cycles is
  deterministic across devices at a fixed seed. The A2 noise floor must vary the seed
  explicitly. The p99 tail of 0.7% is most likely sub-pixel direction differences between
  backends flipping which side of an edge a sample lands on.

## 2026-09-12 — A2 noise-floor tool written, smoke-tested on CPU

`tools/noise_floor.py` renders tiles of the full-resolution reference panorama via Cycles'
border render, so each tile has the reference pixel scale at a tile's cost, and renders each
twice with different seeds. sigma = RMS(A-B)/sqrt(2) estimates one render's noise without
needing a converged reference, so no bias from one is smuggled into the measurement.

Smoke test (calib room, 2 tiles of 48 px, CPU): rel_rms 0.1515 / 0.1087 / 0.0733 at 8 / 16 /
32 spp. Ratios 1.39 and 1.48 against the 1.41 expected for 1/sqrt(spp), so the estimator
behaves. Fixed cost per render call with persistent data on: 0.023 s.

## 2026-09-12 — noise_floor.py failed on the workstation; sandbox parity rule added

The tool imported OpenEXR, which does not exist in Blender's bundled Python. It ran fine in
the Chat sandbox because there bpy and OpenEXR sit in one interpreter, so the sandbox is
structurally blind to this class of bug. Diagnosed by Code against the real environment.

The import was deferred inside a function, so the script got through argument parsing, camera
setup and a whole tile render before failing — and `blender -b -P` exited 0 regardless, so
the command reported success while writing no noise.json.

Fixed, each verified rather than assumed:
- Reads tiles back through `bpy.data.images.load` on single-layer EXR instead of OpenEXR.
  Checked against the OpenEXR reader on a real 96 px tile: max difference exactly 0.0. The
  `[::-1]` row flip is load-bearing (without it, 1.33). Multilayer cannot be read this way at
  all: Blender loads it as type MULTILAYER, size (0,0), no pixels.
- Failure now exits 1 and prints a FAILED line. Confirmed: exit code 1 on a bad --blend.
- The scratch tile is removed in a `finally`, so a crash no longer leaves it behind.
- File I/O moved outside the timer, so the a + b*spp fit measures rendering only.
- Tile pixel count now measured from the returned array. Border rounding gave 95x96 for a
  requested 96, so the old `tile_px**2` would have skewed the reference-cost projection.

Re-run after the fix reproduces the earlier rel_rms values exactly (0.15150 / 0.10867 /
0.07335 at 8 / 16 / 32 spp), which is the check that the new reader changed nothing.

CLAUDE.md now states the two-interpreter rule, since the sandbox cannot catch it.

## 2026-09-12 — A2 paused: noise_floor.py audited, not yet trustworthy

Full audit in `docs/reviews/2026-09-12-noise-floor.md`, run on the workstation.
`tools/noise_floor.py` should not be trusted until the fix pass lands.

The serious finding is an unguarded ordering invariant. `Render Result` is a live shared
buffer, so the estimator is only correct because each render is read before the next is
issued. Render both seeds and then read both, and the two files come back with identical
pixels: measured max|A-B| 2.499e-01 with the current ordering against 1.490116e-07 with
both-then-read. sigma collapses by six orders of magnitude and the tool reports
`chosen_spp = 16` with a confident projection. Plausible numbers, no exception, nothing
asserting the invariant.

Measured, and good: seeds do decorrelate. sigma ratios across 16 to 512 spp cluster on the
1.414 expected for 1/sqrt(spp); same-seed renders differ by at most 1.490116e-07 on OptiX
and exactly 0 on CPU. Border rendering with persistent data is not cached. `save_render`
does honour `scene.render.image_settings` — `color_depth="16"` produced a float16 file, and
`file_format="PNG"` wrote an actual PNG to a path named .exr — so those settings are
load-bearing, not decoration.

Measured, and wrong: the `a + b*spp` fit measures curvature, not overhead. The intercept
ranges 0.0279 to 0.0627 s, a spread of 105% of its own median, while a single number is
reported. Tile 0 absorbs a one-time warm-up (first render 0.155 s against 0.029 to 0.037 s
for the same spp elsewhere) and gets a negative low-end marginal cost. Linearity fails
below about 256 spp; the data look like max(fixed, b*spp). The slope is sound: 18% spread,
median 1.523e-04 s/spp.

The projection is absent at the default target: 2048 spp gives rel_rms_worst 0.01941
against `--target 0.01`. Reaching 1% needs about 7700 spp (assumed, by 1/sqrt(spp)
extrapolation).

Assumed, from the stable slope: 1.523e-04 s/spp over ~16.3k pixels is 9.3 ns per
pixel-sample, so the full 25.92 Mpx reference projects to roughly 2 minutes at 512 spp and
half an hour at 7700 spp. Tiling the reference is therefore unnecessary for time; the only
size constraint is the 1.14 GB EXR.

Fix pass pending: assert that the two seed renders actually differ, so the worst failure
mode becomes loud; discard a warm-up render before timing; fit only the linear regime and
report per-tile spread instead of a single median; assert float32 and alpha == 1; stop
rounding `seconds` before fitting; drop the unused `configure_multilayer_exr` import; put
sigma and rel_p99 on the same scale (one is an RMS, the other a mean absolute difference,
so they differ by ~20% for Gaussian noise).
