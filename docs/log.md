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

## 2026-09-13 — noise_floor.py fix pass, checked host-side; Blender path not run here

Rewrote `tools/noise_floor.py` against the audit's list. Every item landed:
- The ordering invariant is now guarded: a seed pair with rel_rms below 1e-5 fails the run
  (same-seed differs by <= 1.5e-7 absolute, different seeds by >= 1e-2 relative, both
  measured 2026-09-12). `--control late-read` reproduces the read-after-both-renders bug on
  purpose and passes only if the guard fires; `--control same-seed` reports how close
  "identical" is on the device.
- One warm-up render, timed and discarded, before any tile is measured.
- The `a + b*spp` fit is gone. Timing is reported as a call floor (time at the smallest
  spp) and a slope fitted only on spp >= `--fit-min-spp` (default 256), converted to
  ns per pixel-sample with each tile's own pixel count, each as median plus range over
  tiles. Seconds are no longer rounded before fitting; `time.perf_counter` replaces `time.time`.
- `read_rgb` asserts float, 4 channels, depth 128 (float32) and alpha exactly 1, and uses
  `foreach_get` (22x faster than `pixels[:]`, measured in the audit).
- `rel_p99` is now the 99th percentile of the per-pixel RMS, on the same scale as sigma.
- When no measured spp meets the target, the spp that would is extrapolated by 1/sqrt(spp)
  and labelled assumed; the projection uses it and adds the call floor. A normalised
  1/sqrt(spp) scaling check is reported per run. Default `--spp` now reaches 8192.
- Unused `configure_multilayer_exr` import dropped. `run()` is behind `__name__ ==
  "__main__"` so the analysis functions can be imported.

Measured, in the Chat sandbox: `tools/check_noise_floor_stats.py` passes 13 checks on
synthetic data — sigma to 0.3% of a known value, p99/rms 1.969 against 1.945 expected for
Gaussian noise (the old mean-absolute statistic gave 1.738), slope recovered to 1.2% from
max(floor, b*spp) data where the old straight-line intercept was 60% off, guard fires on an
identical pair and not on a real one, extrapolation lands on the target exactly.

Not measured: anything involving Blender. The sandbox today has no `bpy` (the wheel is not
on PyPI for its Python 3.12, and download.blender.org is not reachable), which contradicts
what CLAUDE.md says about the sandbox. The Blender-side control flow was driven end to end
with a stub `bpy` whose Render Result buffer is live like the real one — normal run, both
controls, exit codes — but that proves the script's logic, not the Blender API calls
(`img.depth == 128`, `pixels.foreach_get`, `save_render` under border render). Those are
what the two `--control` runs and one real run on the workstation must confirm.

## 2026-09-13 — A2 noise floor measured on both scenes; the guard caught a real bug; no reference rendered

All on the workstation (Blender 5.2.1, OptiX, RTX 4090). Step 0 first: `check_noise_floor_stats.py`
13 checks pass; `--control same-seed` max|A-B| 1.192e-07, rel_rms 5.8e-08, PASSED; `--control
late-read` guard fired, PASSED; both exit 0. A nonexistent `--blend` prints FAILED and exits 1.
The assumed API details (depth 128, foreach_get, save_render under border) all held.

First real Classroom run: FAILED at tile 0, 16 spp, seeds (0, 1) identical, rel_rms 4.97e-08.
Not the late-read bug: the Classroom's scene action keyframes `cycles.seed` (frame 1, value
144, GENERATOR modifier), and every render re-evaluates the frame, so `c.seed = 1` was
overwritten before the render; it read back as 1 both times. Calib room has no such key, which
is why the audit never saw it. Added `bl_common.pin_seed` (removes F-curves and drivers on
`cycles.seed`, Blender 5.2 layered-action API) and an assertion in `render()` that seed and
samples still hold after the render. `preview360.py` calls it too; `render_foveated.py` not yet.
Calib room re-run after the fix reproduces the earlier numbers (worst 0.00956 at 8192 both times).

Noise, worst tile: calib room 0.2662 at 16 spp down to 0.00956 at 8192; Classroom 1.148 down to
0.0336. 1/sqrt(spp) check medians 1.006 and 1.022, both ok. Timing: call floor 0.060 s / 0.158 s
median; 9.92 / 10.43 ns per pixel-sample median, ranges 9.41-10.08 / 8.70-10.89, worst fit
residual 0.117 / 0.077.

spp: calib room 8192 meets 0.01 (measured); Classroom needs ~92,600, rounded to 131072
(assumed, 1/sqrt extrapolation). One spp for both, so 131072: projected 561 min and 591 min.
Both over the 90-minute cap, so nothing rendered. At 8192 spp both would project to ~35-37 min.
The Classroom's worst tile is its darkest (level 0.042 vs 0.568); its brightest tile reaches
0.0077 at 8192. Full write-up in `docs/a2-reference-and-noise-floor.md`.

## 2026-09-13 — A2 references rendered at 8192 spp; adaptive sampling caught by the projection

Rule changed (D7): reference noise at most a third of the fixation noise it is compared to,
spp per scene. At 8192 vs 1024 spp the Classroom's ratios are 0.266 (worst) / 0.328 (median);
the calib room's are 0.341 / 0.350, over the bound by 2-5% (pure 1/sqrt gives 0.354 for 8x).
Rendered 8192 for both as instructed; calib room flagged, 16384 would give 0.24 (assumed).

Scale test first (calib room, 7200x3600, 256 spp): 58.2 s vs 65.9 s projected, ratio 0.883,
so proceed. Then the calib room reference at "8192 spp" took 135 s against 35 min projected.
Cause: calib_room.blend ships with use_adaptive_sampling on (threshold 0.01); noise_floor.py
turns it off, preview360.py did not. The Classroom blend has it off, so its reference, already
rendering, stayed valid. preview360.py now forces adaptive off and time_limit 0, asserts seed,
samples, adaptive and time_limit after the render, records them in meta.json, and got the
loud-failure wrapper (exit 1 on a raise; render_foveated.py too, both verified on a bad
--blend). Also added --time-write: re-saves Render Result to a scratch path, times it, and
asserts the byte size equals pano.exr. Deleted the adaptive-on reference, re-ran.

Uniform scale test: 63.1 s, ratio 0.958; EXR write 0.38 s; 502 MB on disk. inspect_preview
handles 7200x3600 in 14 s.

References, measured: calib room 1939.8 s (32.3 min, ratio 0.921 to the 35.1 projected),
Classroom 2147.4 s (35.8 min, ratio 0.970 to 36.9). EXR writes 0.38 s / 1.6 s inside those.
Files 501 MB / 2.00 GB (ZIP; the 1.14 GB in the previous entry was uncompressed arithmetic).
inspect_preview on both matches A1: holes 0 / 0.0208, backfaces 0 / 0.0038, nadir 1.6002 /
1.2001 m, zenith 1.6002 / 1.6967 m. These render times are the uniform-cost baseline at s0.

render_foveated.py now calls pin_seed (smoke-tested on the Classroom at 128 px: key removed,
exit 0), since A4 renders many fixations in one session. Write-up in
`docs/a2-reference-and-noise-floor.md`.

## 2026-09-13 — cost classes, profiles, references as pinned assets

After A2's two 35-minute renders: those are the uniform baseline, rendered once, and the loop
must never wait on anything like them. CLAUDE.md gains a "Cost classes" section (interactive
< 10 s, batch < 5 min, overnight with a logged justification) and two habits: build on
`--profile small`, and treat references as md5-pinned assets kept outside the checkout.

`bl_common.PROFILES` defines `small` (s0 0.1 deg, reference 3600x1800 at 1024 spp,
fixations 64 spp) and `full` (s0 0.05 deg, 7200x3600 at 8192 spp, fixations 256 spp).
`add_profile` puts `--profile` on `preview360.py`, `render_foveated.py` and
`noise_floor.py`; a profile only replaces defaults, so explicit flags still win, and
`meta.json` records which profile was used. Parsing behaviour checked host-side (no profile
keeps the old defaults; profile sets them; an explicit flag wins in either order) and the
noise-floor control flow re-driven with the stub bpy. Not run in Blender: the workstation
verifies `preview360.py --profile small` on the calib room, which also produces the small
reference A4 develops against.

Fixation spp is at most a sixteenth of the reference spp in both profiles so D7 holds by
construction: 1/sqrt(16) = 0.25 for small, 1/sqrt(32) = 0.18 for full, both under a third.

## 2026-09-13 — A4: fixation sequence tool, sample record, and its checks; stale sample count caught

Step 0: md5 of the four full reference files pinned in the manifest; D7 on the calib room
closed against the full profile's 256 spp fixations (0.162 / 0.174 from the noise table).
Small references rendered and pinned: calib room 62.6 s, Classroom 71.5 s, 3600x1800 at
1024 spp, BOX, adaptive off, inspect matches A1 to 4 digits. `render_foveated.py --profile
small`: raster 126, s0 0.1002 (from the rounded raster, not 0.1 exactly), 64 spp, check passes.

`render_foveated.py` refactored into setup_foveated_camera / set_gaze / render_fixation /
save_render_result / fixation_meta; CLI output re-checked at yaw 20 pitch -5. New:
`tools/exr_lite.py` (numpy reader for uncompressed single-part EXR, bit-identical to OpenEXR
on all 11 channels; Blender cannot read multilayer back and Render Result has no pixels in
background mode), `tools/fixation_sequence.py`, `tools/check_sequence.py`.

Caught by the tool's own sweep: with persistent data Cycles ignored a change of
cycles.samples alone (16/256/4096 spp all 16 ms). A seed change or scene.update_tag() makes
it take; render_fixation now tags on any spp or seed change, and each sweep level renders a
seed pair whose noise must fall as 1/sqrt(spp). noise_floor.py and A3 alternated seeds, so
their numbers stand.

Measured, small profile: calib room 50 targets, 12,492 samples each, 15.2 ms per fixation
median (14.4-16.3), warm-up 0.309 s, floor 8.6 ms, 10.06 ns per sample (9.50-10.56), floor
57% of a 64 spp render; Classroom 10 gazes, 28.4 ms (25.6-32.3), warm-up 0.750 s, floor
21.8 ms, 11.21 ns per sample (8.98-12.07), floor 77%. The fit on spp >= 64 is two points.

Checks: (a) directions vs Position pass 0.018 px p99.9 median, max 0.091 px, all pass;
(d) footprints sum to the 45 deg cap 0.59% low, all pass; reader exact. (b) foveal agreement
passes 13/50 on the calib room and 9/10 on the Classroom; the failures track a measured
alignment floor (reference vs itself half a pixel away: 0.08-0.19 on the resolved Siemens-star
cards) with no brightness bias (0.996-1.013), so on those targets (b) measures edge alignment,
not noise. Left as specified. (c) fails as required on 49/50 and 10/10; the exception is a
wire target whose 90 deg rotation lands on similar wall. Full profile untested. Write-up in
`docs/a4-fixation-sequence.md`.

## 2026-09-13 — check (b) reformulated and still registration-limited; A5 integration and curve; uniform wins on the calib room

Step 1. `fixation_sequence.py --seed-pair` (default on) renders every fixation again at seed 1
in a second pass (so the seed change's scene re-sync is not inside the timed renders):
fix_b.exr, samples_b.npz, not part of the record. `check_sequence.py` (b) is now binned at
0.5 deg within 2 deg of the fovea, footprint-weighted means against the reference's box means,
bound per fixation 1.5*sqrt(n^2 + (n/4)^2) from the seed pair. Calib room 17/50 pass, bounds
0.012-0.043 (median 0.026), binned alignment floor median 0.023 (max 0.137); Classroom 8/10,
bounds 0.043-0.222 (median 0.061), floor 0.017. (c) 50/50 and 10/10. Measured why 33 still
fail: a 1 px (0.1 deg) shift of the reference alone exceeds the bound on 39/50, a half-pixel
on 23/50; cells are 2.5-5 samples wide on cards whose spoke edges recur every 2 px. A
footprint-matched variant was worse (0.050). Bound untouched. Old statistic kept as
resampling_floor (0.098 / 0.116). (d) is +0.59%, not -0.59% as the A4 note said (fixed): the
footprint integrates to the cap to 0.001% over the exact disc; the rim ring of straddling
pixel squares adds 1.48% outside and misses 0.87% inside, net +0.61%.

Step 2. `tools/integrate_sphere.py`: disc splat with 1/footprint weights onto the reference
grid, centroid per cell, D8 metric with the reference box at the centroid (cell-centre box
reported too, 0.02-0.03 worse). Identity check exact (2e-16) to lat 70 deg, 0.11-0.14 beyond
because a polar pixel's disc spans its longitude neighbours; mass check +0.02-0.09%. One
fixation covers 0.118 of the sphere (81% of its cap: disc corner gaps); 50 cover 0.578.
Calib room, 40 M rays at K=50: foveated targets 0.354 RMS (median 0.176), sphere 0.186;
uniform W=1118 targets 0.125, sphere 0.077. Uniform wins at every K on this scene, and the
foveated target error rises with K (0.159 -> 0.354). Measured causes: the uniform is
grid-registered and shows only its 64 spp noise (0.077, A2 says 0.073); the foveated pays the
resampling floor at 0.1 deg on the stars; and 1/footprint leaks blur: coarse-sample share of
the weight at the targets 0.50 at K=50 (finest-only or 1/fp^2 variants: 0.259 / 0.274, still
above uniform). Checks (2) 0.354 vs bound 0.026 and (3) control 1.46x both fail, recorded.
Classroom, K=10, 8 M rays: foveated targets 0.223 vs uniform 0.297, sphere 0.276 vs 0.240;
control 5.3x passes, (2) fails (0.223 vs 0.061). Binned-to-0.5-deg target error 0.067 / 0.073.
Full profile untested for A4 and A5. Write-up in `docs/a5-spherical-integration.md`; D8 added.
No new pinned asset: the uniform renders and integrations are regenerable in seconds.

## 2026-09-13 — D9: the curve at a declared scale; finest-owns integration; foveation wins at the targets

D8 charged a coarse uniform render only for its noise, never its blur, so 2.3 deg pixels "won"
at K=1. D9 added: the curve is measured at s_eval = 2 s0 (0.2 deg small), reconstruction vs
reference both at s_eval; uniform nearest-upsampled to the reference grid then filtered the
same way. `integrate_sphere.py` rewritten: finest-owns layering (samples within 1.5x the
cell's finest footprint own it; coarser ones fill only where nothing finer covers), s_eval
reconstruction with the uncovered fraction always beside the sphere error, resampling floor
at s_eval, PIL chart, and the D8 per-cell comparison kept as a check. `preview360.py --seed`
added for the calibration point.

Calib room at s_eval 0.2 deg: targets F/U 0.292/0.347 at K=1 ... 0.161/0.294 at K=50 (F wins
at every K, 1.8x at 50); sphere F/U 0.546/0.296 at K=1 (F uncovered 0.868) ... 0.140/0.151 at
K=50 (uncovered 0.416): uniform wins the sphere at every K below 50, level at 50. Floor at
s_eval 0.217 targets / 0.089 sphere. Classroom K=10: targets 0.152 vs 0.759 (5x), sphere 0.520
vs 0.516 with 0.314 uncovered; control 8.8x passes. Calib room control 3.7x fails (wall vs
star card bounds the wrong-content error at 0.59; right-content residual 0.16 is registration
plus 0.03 noise). Identity of the reconstruction path 2.2e-16 / 4.4e-16 within lat 60.

Calibration point: uniform 3600x1800 at 64 spp (5.0 s) scores 0.0332 over the sphere; its own
noise at s_eval from a seed pair is 0.0323, so the metric charges noise x 1.03. It fails the
specified 0.073 +- 0.01, which is the per-pixel figure at 0.1 deg; at 0.2 deg the 2x2 box
halves it (0.037 assumed, 0.032 measured). Left as specified and recorded. D8 validation at
the 0.5 deg bin still fails (0.067 vs 0.026, 0.072 vs 0.061). Charts committed under
docs/reference/. Full profile untested.

## 2026-09-13 — overnight-class justification: two full-profile shifted references

Two renders of about 4.5 min each (projected from A2's 9.92 and 10.43 ns per pixel-sample at
1024 spp over 25.92 Mpx): the full references re-rendered half a pixel of yaw off-grid, so the
resampling floor at s_eval is measured from a true off-grid render rather than a bilinear
shift. Rendered once, pinned by md5 as assets, seed 1 so their noise is independent of the
references'.

## 2026-09-13 — D10 thresholds, off-grid floor, full profile on both scenes; Phase A result written

Thresholds (D10): calibration passes on score / own seed-pair noise at s_eval in 1.0-1.15
(1.029 small, 1.013 full; the earlier 0.073 expectation was the per-pixel noise at the wrong
scale); control 3x (3.7x / 4.2x calib room, 8.8x / 11.5x Classroom); (b) bound carries the
fixation's binned alignment floor in quadrature (small: 40/50 and 8/10 pass, bound medians
0.043 / 0.073; full: 12/50 and 7/10, 0.024 / 0.022, noise 0.003-0.008 so the floor sets it);
(c) still fails on every fixation. D8 validation at the 0.5 deg bin: 0.067 vs 0.043, 0.072 vs
0.073 (pass), 0.025 vs 0.024, 0.051 vs 0.022.

Off-grid floor: preview360.py --yaw-offset-px; four shifted references rendered (seed 1,
1024 spp, 0.5 px: small 62.8 / 71.3 s, full 246 / 278 s), pinned by md5. Floor at s_eval,
targets / sphere: calib 0.175 / 0.065 small, 0.226 / 0.051 full; Classroom 0.375 / 0.131,
0.257 / 0.107; the bilinear version overstated the sphere floors by up to 2x.

Full profile: fixations 140 ms (calib, floor 16 ms, 10.14 ns/sample) and 169 ms (Classroom,
34 ms, 11.03); warp 0.018 px; cap -0.02%. Curve at s_eval 0.1 deg, calib K=50, 643 M rays:
targets F 0.183 vs U 0.351, sphere 0.100 (42% uncovered) vs 0.092; Classroom K=10: 0.134 vs
0.363, sphere 0.514 (32% uncovered) vs 0.409. Foveation wins at the targets at every K on both
scenes and profiles; uniform wins the sphere below the largest K. Longest commands: shifted
Classroom reference 278 s, calib integration 264 s. docs/phase-a-result.md written; A4 and A5
notes updated; charts in docs/reference/.

## 2026-09-13 — fixated-targets column; (b) judged on plain content; E2 / e_max sweep

Step 1: `targets_fixated` in the D9 curve (targets whose fixation is among the first K).
Full profile, calib room: 0.146 F vs 0.365 U at K=1, 0.183 vs 0.351 at K=50; Classroom 0.075
vs 0.228 at K=5. All four integrations re-run; other numbers unchanged.

Step 2: `check_sequence.py --plain kind=wire | floor=0.03`. Small: wires 8/8, Classroom 5/7
(desk floor; window gaze). Full: wires 0/8 at 0.006-0.013 vs bounds 0.004-0.009, measured as
not radiometric (brightness 0.998-1.003; seed 1 scores the same as seed 0 vs the reference
while the pair noise is 0.003; a 1 px shift gives 0.003-0.030): sub-pixel lattice vs the
0.5 deg cells. D8 validation closed on the calibration ratio, the brightness ratio and (a).

Step 3: sweep, five settings, 50 targets each, ~4-11 s per sequence, ~1 min per curve.
Rasters 77 / 126 / 200 / 111 / 137, samples 4,669 / 12,492 / 31,428 / 9,689 / 14,745. At equal
rays (14.9 M, E2 1's K=50; others interpolated log-log along K): fixated 0.227 / 0.155 / 0.103
/ 0.168 / 0.168; sphere 0.203 (0.42 uncov) / 0.435 (0.78) / 0.395 (0.83) / 0.371 (0.82) / 0.378
(0.68). E2 4 wins the targets, E2 1 the sphere; e_max 45 the targets, 30 the sphere. Choice
differs from the profiles' E2 = 2, e_max = 45 and the criteria disagree: profiles NOT
changed, stopped, recorded as D11 pending the objective. E2 1 fails the cap check (+1.03%,
raster 77) and the control (2.6x). `docs/a6-warp-sweep.md`.

## 2026-09-13 — Phase A summary

`docs/phase-a-summary.md` written by Luiz: the question, what was accomplished (A1-A6), the
result, eight things learned, why it matters, what carries into Phase B, deliverables. The
README's layout and State now point to it.

## 2026-09-14 — B1 written: the second eye, verged pairs, foveae-on-target; not yet run

Reviewed the third-party suggestions for Phase B: adopted the binocular schema (D12, minimal:
origin per eye, eye_id, pair_id, schema tag, pose and timestamp in meta, rig in pairs.json),
split only the pure-numpy geometry out of `fixation_sequence.py` / `render_foveated.py` into
`tools/warp.py` and `tools/rig.py` (host-side checkers need them; `integrate_sphere.py` untouched
until B2 needs it per eye); test vectors are check (a), kept; objective-before-E2 is D11; rays
as the budget with timing separate is already the practice; CI deferred until self-tests exist
(they do now: `warp.py --self-test`, `rig.py --self-test`, each shown to fail on a wrong sign).

`render_foveated.gaze_matrix` / `set_gaze` gained `offset_local` (eye centre in the head frame,
default 0: Phase A unchanged). `tools/fixation_pairs.py` renders verged pairs on the rig
(ipd 63 mm default, `--vergence on|off`), writing L/ and R/ Phase A sequences plus pairs.json;
`tools/check_pairs.py` judges reader, (a) against this eye's centre, (d), (e) centre pixels on
P within one spacing at the target's distance, (f) the control's predicted miss, and draws a
sheet. `check_sequence.py`'s origin failure now points at check_pairs (a per-eye sequence
against the cyclopean reference is off by parallax, 0.9 deg at 2 m).

This sandbox had no bpy (Python 3.12, no wheel). Pure-numpy parts ran here; the writer and
checker were exercised end to end through a stub Blender (`tools/dev/fake_blender_pairs.py`: analytic ray caster over the calib
room's cards and walls, real uncompressed EXRs written with OpenEXR and read back by exr_lite:
reader diff 0): verged run 42/42 cards pass (e), control run fails (e) on every resolvable card
by the predicted amount; a 1 cm error injected into one fixation point fails (e) on both eyes.
Those are plumbing results, not measurements. Predicted for the workstation: 1.80 deg vergence
on the 2 m ring, 7.2 deg at the 0.5 m ladder, 0.17 deg at the 2.6 m ladder (azimuth 83 deg,
almost on the baseline: the control is unresolvable there at small s0, 3.8 mm vs 4.6 mm tol);
about 30 ms per pair small, 280 ms full (from A4). CLAUDE.md notes the bpy-less case.
Write-up in `docs/b1-verged-pairs.md`, Results empty until the run.

## 2026-09-15 — B1 first workstation run: verged pairs and control, both profiles, all checks pass

Step 0: `warp.py --self-test`, `rig.py --self-test` pass in `.venv`; both import and pass under
Blender 5.2.1's bundled Python (no fix needed). Step 1-2, small (OptiX, RTX 4090): verged 50
pairs 2.9 s wall incl. Blender start (29 ms median per pair, 14.7 ms per fixation, 12,492
samples), control the same; interactive class as predicted (30 ms). check_pairs: reader diff 0,
(a) 0.016 s0 with the eye 31.5 mm off the head origin (a wrong offset would read 9 s0), cap
1.0059, (e) verged miss median 0.0025 mm / max 0.0041 mm (0.001 spacings) on 42/42 cards;
control on-card miss median 30.98 mm within 3 µm of rig.py's prediction on 72 fixations, 12
off-card (the 35 mm cards at e <= 2.5 deg and the 0.5 m ladder: ray lands on the wall,
3.0-3.2 m), 2.6 m ladder unresolvable at small (3.84 vs 4.60 mm tol) as predicted; vergence
measured minus predicted 2e-5 deg. Step 3, full: 271 ms per pair, 136 ms per fixation
(50,269 samples), 14.9 s per sequence, 15.4 s the whole command (batch, predicted 280 ms /
15 s); (a) 0.017 s0, cap 0.9998, (e) 0.0012 / 0.0024 mm, control on-card within 1.4 µm of
prediction, 2.6 m ladder resolved (1.7 spacings). Four check.json files, `fails: []` in all.
Wires (reported only): verged centre miss equals the wire radius at full (P is on the axis,
the ray stops at the surface); at small the 2x2 centre block sits +-1.3 mm off-axis at 1.5 m
so the three wires under 1.3 mm radius are missed to the wall. Nothing changed in code,
thresholds, warp or record. Results in `docs/b1-verged-pairs.md`; previews regenerable, nothing
pinned.

## 2026-09-15 — B2 written: stereo truth sidecar, epipolar frame, triangulation check; per-eye references; not yet run

Decided with Luiz after B1: B2 as ground truth from the Position pass (no rendering), the
triangulation check with a naive-estimator control, epipolar coordinates on the sphere, and
per-eye references; B3's objective will be a reference matcher as an instrument plus the
matcher-free Fisher-information bound (D15 when written). D13 (truth is a sidecar, epipolar
frame is the head X axis) and D14 (torsion moot while the warp is isotropic) added.

`warp.py` gained the inverse warp (direction -> continuous raster coordinates; self-test:
exact round trip on every inside pixel, fails on a flipped row). `rig.py` gained
to_camera_frame, epipolar, phi_distance_deg, triangulate (sine rule), depth_quantum_m;
self-tests: random points share phi and triangulate back to 1e-9, parallax at the fixated
midline point equals the vergence, parallel rays give inf, quantum at 2 m / s0 0.1 is 0.111 m;
fails on a wrong axis or a swapped sine-rule term. `tools/stereo_truth.py` (host side) writes
truth.npz per fixation and truth.json per run, checks (i) epipolar, (j) round trip, (k)
triangulation identity, (h) depth at the cards with the naive control. `preview360.py
--eye-offset` for per-eye references, meta.json's eye.position_m is then the offset centre.

Sandbox (no bpy): the tool ran on the B1 stub runs. Verged: (i) 0.000 s0, (k) 0.000 s0, (j)
100%, (h) truth error 0 vs hit and target, naive passes; visible 93.8% / occluded 4.2% (cards
in front of walls) / outside 0.6% / inconsistent 1.4% (nearest other-eye pixel looking past a
card edge). Control: truth passes vs the hit (max 0.2 mm), naive gives inf on every card as
required; 7214 samples within 5 deg of the axis excluded per run (the ladders at azimuth 83).
Negatives: ipd 0.070 in pairs.json fails (h) at 2.22 m vs 2.00; swapped centres fail with inf.
Stub numbers, not measurements. Write-up `docs/b2-stereo-truth.md`, Results empty.

## 2026-09-15 — B2 first workstation run: truth on the four B1 runs, per-eye references, per-eye (b)

Step 0: self-tests pass in .venv and under Blender's bundled Python. Step 1, `stereo_truth.py`
on the four B1 runs (interactive: 0.6 s small, 1.9 s full): small runs clean; both full runs
FAILED first pass, 2 and 1 samples with non-positive parallax, all within 0.02 deg of the
baseline axis (left wall at x = -3 m through the wire fixations' periphery). Diagnosed, not
tolerated: `rig.epipolar` computed theta = arccos(d_x) on the float32 direction, whose x is
quantised at -0.99999994 next to the axis, 0.02 deg of theta error against a geometric parallax
of 2e-5 to 5e-4 deg there. Fixed to atan2(hypot(y, z), x) (same function, well conditioned);
self-tests unchanged, re-run from step 0. One sample remained (full control, L f048, 0.0008 deg
off-axis): geometric parallax 2.0e-5 deg against a 1.6e-4 deg residual between its analytic ray
and its Position-pass hit (check (a)'s residual), so its sign is unmeasurable; `stereo_truth.py`
now counts the sign on the off-axis mask (i) and (k) already use and reports the near-axis count.
That is a checker change made after the diagnosis. After both: all four pass, (i) 0.015 s0 p99.9
(max 0.017), (k) 0.015 s0, (j) 100.000%, (h) truth within 0.0009 m (0.005 quanta) small and
0.0005 m (0.006 q) full of the hit and of the target on verged runs, naive exact on verged and
inf on 42/42 cards of both controls; visible 93.0 / 91.1 / 94.9 / 94.7%, occluded 4.7 / 5.6 /
3.9 / 4.0%, inconsistent 1.70 / 2.85 / 0.72 / 0.89%; axis-excluded 7,214 (small) and 29,057
(full) per run. B1's check_pairs re-run after the rig.py change: identical.

Step 2, per-eye small references (batch; justified: the per-eye (b) cannot be read against the
cyclopean reference, parallax 0.9 deg at 2 m): L 60.55 s, R 61.08 s, OptiX; meta.json eye
(-/+0.0315, 0, 1.6), head (0, 0, 1.6); inspect: no holes, no backface, nadir 1.6002 m. Pinned as
reference_small_L (md5 fdcbe57f7f0d575b532984dc1a8183e4) and reference_small_R
(5e268d470f70aa34f57625465daca306) with backface md5s; copied to
/home/lvelho/data/reference/reference_small_{L,R}/calib_room, md5 verified (that tree held only
the two full references; the small cyclopean ones and the shifts are not in it). Card centroids
from each pano's Depth pass land within 0.5 px of the offset centre's prediction, e = 0 card at
1808.8 / 1790.6 vs 1800.3 cyclopean (the 9 px parallax).

Step 3, check_sequence L and R against their references: on the B1 run (no seed pair) origin,
(a) 0.018 px, (c), (d) pass, (b) unjudged as the checker says. Re-rendered verged small with
--seed-pair as previews/pairs/calib_room_sp (4.5 s; check_pairs and truth identical to
calib_room); against the per-eye references: (b) 36/50 L, 35/50 R (Phase A cyclopean 40/50),
cards 30/42 both (32/42), wires 6/8 L, 5/8 R (8/8), bound median 0.046 (0.043), control 50/50
fails as required. Wire failures by 3-43% (scores 0.015-0.030 vs bounds 0.014-0.025); Phase A's
wire passes had 1.5-3% margins and its full-profile note showed the wire score moving
0.003-0.030 under a 1 px shift, so read as sub-pixel lattice phase from a different centre, not a
reference error (centres verified above). No tolerance changed. Full per-eye references not
rendered (overnight, unscheduled). Results in `docs/b2-stereo-truth.md`.

## 2026-09-15 — B3 written: the stereo instrument, the bound, the sweep; not yet run

D15: a reference matcher lives here as an instrument; D5 stands. `tools/stereo_instrument.py`:
foveal epipolar maps at s_eval (finest-owns, R map wider by the search range), NCC block
matcher with two Lucas-Kanade sub-cell steps, the Fisher-information bound with the noise's
own gradient removed, information per ray, checks (l) self-shift, (m) recovery on the fixated
surface, (n) bound below the error, a sheet (L | R | truth | estimate | error), `--self-test`
on synthetic shifted textures. `tools/stereo_sweep.py` collects settings into a table, CSV
and chart. `docs/b3-stereo-instrument.md`; README B3 row.

Found while building, all on the stub (`tools/dev/fake_blender_pairs.py`, itself changed):
a 3-point parabola on the NCC peak locks to the integer by up to 0.25 cell on an exact
peak, replaced by LK steps (self-test RMS/bound 4-5x -> under 3x); the LK gather lacked the
column index (caught by the self-test: median 0.9 cell at every shift); windows at the map
edge lost their true shift to the valid-count rule (now relative to the window's own valid
cells, R map padded by S); noise gradients counted as information on a flat card (half-cell
bound from noise alone; now only gradients above 2 sigma, noise variance subtracted); a
striped card with no gradient along theta was "matchable" by texture alone (now the bound
must be below one cell); (m) on a 5x5 centre block failed on cards whose block straddles a
depth edge (now over the fixated surface's edge-free cells). The stub itself: a periodic
checker (every matcher ambiguous), then sub-cell texture (aliasing), then noise seeded
identically for both eyes (the matcher matched the noise pattern) — each replaced. Stub
results, plumbing only: verged 41 judged pairs, inlier RMS 0.27 cell, gross 17% (8% edge-free),
RMS/bound 5.8, (l) 100%, (m) 38/42 judged and passing; control (`--search 24`) (m) 42/42
recovering ~9 cells; negatives: a lazy matcher fails (m) on the control and (l); sigma x3 fails
(n); sigma x10 leaves nothing matchable and fails on that. Predicted for the workstation: E2 4
lowest error per pair at 2.5x the rays; information per ray undecided.

## 2026-09-15 — B3 first workstation run: instrument, bound, sweep; rankings disagree, D11 stands

Step 0: warp, rig and stereo_instrument self-tests pass (0.1 s). Step 1 first pass: verged
`calib_room_sp` FAILED (n) on 10/37 cards, inlier RMS below the bound by up to 4x (p006
0.0055 vs 0.0209 deg); control (rendered with --seed-pair, 4.5 s) clean, (m) 36/36 recovering
~9 cells, RMS/bound 3.15. Diagnosed: both eyes rendered at seed 0 on the same raster; on a
verged fronto-parallel card L(i,j) and R(i,j) see the same point with the same random numbers.
Measured on the centre pixels: corr(L - L_seed1, R - R_seed1) 0.95-0.98 on cards and ladders,
RMS(L - R) a quarter of the seed-pair noise; control 0.04. Fixed in `fixation_pairs.py`: R eye at
seeds (2, 3), L at (0, 1), recorded in pairs.json / meta.json (a fix outside the checks;
re-run from step 0). After: corr 0.004; verged (n) fails on 3/37 (ratios 0.75-0.95), (l) 100%,
(m) 37/37, inlier RMS 0.27 s0 (0.13 cells), gross 6.3% (edge-free 0%), RMS/bound 1.62,
info/ray 0.101; control unchanged. B2's per-eye (b) on the re-rendered R: 34/50, 29/42, wires 5/8
(was 35, 30, 5); L unchanged.

The remaining (n) failures (3-14 cards per setting at small, all Siemens-star rings, none at
full): edge-free RMS half the bound with 0% gross. Ruled out by measurement: sigma too high at
the card (it is higher there, 0.039-0.045 vs 0.030-0.039, spoke aliasing under jitter); LK
shrinkage (raw/signal gradient power 1.02-1.05). Cause: the bound's central-difference gradient
cancels on sub-cell spokes where one-sided slopes alternate sign; one-sided power is 4-9x the
central on those cards and a one-sided bound puts all of them at 1.3-2.0x; at full the factor is
1.6-2.0 and (n) passes. Bound NOT changed (working rule); reported as the bound's model error,
Luiz's call.

Step 2, sweep (each render 10-12 s interactive with the seed pass; truth + instrument ~1 s):
inlier RMS s0 0.282 / 0.294 / 0.269 / 0.284 / 0.261 (E2 1, e_max 30, E2 2, e_max 60, E2 4);
bound s0 0.193 / 0.150 / 0.141 / 0.145 / 0.130; info/ray 0.108 / 0.132 / 0.101 / 0.078 / 0.051;
(n) fails 14 / 11 / 3 / 5 / 3; (l), (m), truth pass on all. `[sweep]`: lowest error E2 4,
most information per ray e_max 30; they disagree. Per pair the bound ranks E2 like the
instrument (4 < 2 < 1); per ray it reverses (E2 4 buys 26% more information for 2.5x rays). No
D16; D11 stands. Step 3, full verged with seed pair (33 s batch): (l) 100%, (m) 42/42, (n)
passes, RMS 0.42 s0 = 0.21 cells, gross 12.1% (edge-free 4.3%), RMS/bound 2.68, info/ray 0.83.
Chart copied to docs/reference/b3_sweep_calib_room_small.png. Results in
`docs/b3-stereo-instrument.md`. Nothing pinned.

## 2026-09-15 — B3 follow-up written: the bound's gradient model; not yet re-run

Code's first run found (n) failing on 14 of 37 cards at E2 1 (3-11 elsewhere at small, none at
full), the bound sitting above the instrument's inlier RMS by up to 2x on Siemens-star cards
with 0% gross — a bound that is not a bound. Diagnosis in the run's write-up, confirmed here
by reading it: the bound took its gradient from a central difference, which has a null at the
grid's Nyquist frequency and reports no gradient on content with a two-cell period, which the
spokes near a star centre have at s_eval. `gradient_power_theta` now uses the mean of the
forward and backward squared differences (no null; still below the continuous derivative's
power, so what it gives stays a lower bound), and the noise correction changed with it (a
one-sided difference of white noise has variance 2 sigma^2 / cell^2, four times the central
one). Self-test: a fourth texture with flat power up to 0.45 cycles per cell, bound side only;
the matcher-side factor loosened from 3x to 4x because the tighter bound raises the ratio
(3.04 measured on the smooth texture). On synthetic textures the old model did not violate the
bound, so the evidence for the change is the workstation measurement, not the self-test.
The seed change Code made (L 0/1, R 2/3) is the same fault the stub had on 2026-09-15
(identically seeded noise in both eyes matched by the matcher); it should have been carried
into fixation_pairs.py then. Stub after the change: RMS/bound 8.2 (was 5.8), (l), (m), (n) pass.
No render needed: the instrument re-runs on the eight existing runs in seconds.

## 2026-09-15 — B3 re-run under the one-sided bound: (n) passes on 7 of 8 runs; bound ranking moved; no D16

Instrument only, no rendering (0.5-1.0 s per run). Self-test ok. Standard setting: small verged
(l) 100%, (m) 37/37, (n) passes (was 3 fails), bound RMS 0.0085 deg (was 0.0141), RMS/bound
2.54 (1.62), info/ray 0.347 (0.101); control (n) passes, bound 0.0094, RMS/bound 5.63, info/ray
0.315; full (n) passes, bound 0.0045, RMS/bound 3.84, info/ray 1.63. Instrument numbers
unchanged except through the matchable set: E2 1 judged cells 10,948 -> 10,608 and inlier RMS
0.282 -> 0.272 s0; others within 0.1%. Sweep: bound s0 0.121 / 0.095 / 0.085 / 0.088 / 0.088
(E2 1, e_max 30, E2 2, e_max 60, E2 4), info/ray 0.423 / 0.444 / 0.347 / 0.266 / 0.178, (n)
fails 0 / 1 / 0 / 0 / 0. The one failure: e_max 30 p007 ring_e6_m90 at 0.97 (bound 0.01253 vs
RMS 0.01218 deg, 85% edge cells); reported, bound not touched. `[sweep]`: lowest error E2 4
(0.261 s0), most information per ray e_max 30 (0.444); they disagree. Per pair the bound now
ranks E2 2 (0.085) < E2 4 (0.088) < E2 1 (0.121), i.e. the 2/4 order flipped by 3.5% relative
to the first run; the instrument keeps 4 < 2 < 1 (0.261 / 0.269 / 0.272). Per the rule set for
this re-run (D16 only if the per-pair order was 4 < 2 < 1 on both), no D16: the objective is
flat in E2 to 4% on the instrument and to 3.5% between E2 2 and 4 on the bound, with E2 1 40%
above on the bound; per ray the cheaper settings win. Chart re-copied to docs/reference. README
B3 row -> done with D11 standing. Nothing rendered, nothing pinned, no code changed by Code.

## 2026-09-15 — D16: D11 closed after the bound re-run

The literal condition set for Code (4 < 2 < 1 on both instrument and bound) failed by 3.5%
under the one-sided bound (bound 0.085 for E₂ 2 against 0.088 for E₂ 4), so Code correctly
left the decision open. Read for substance the result is stronger than the condition asked
for: E₂ = 2 and 4 are indistinguishable on both columns (3.5% and 3%), E₂ = 1 is 40% worse on
the bound, and the cost spans 7x. D16 keeps E₂ = 2, e_max = 45 as the middle of a flat
optimum, with a finer s_eval or the Classroom as what could overturn it. The one remaining
(n) failure (emax_30 p007, ratio 0.97, 85% edge cells) is within the label fuzz at a card
whose fovea is mostly depth edge; recorded, not acted on. Phase B's three steps are done.

## 2026-09-16 — Phase C opened: D17, the review filed, C1 written and checked on the stub; not yet run

Phase C starts from a third-party review (`docs/reviews/2026-09-16-phase-c-suggestions.md`,
with the reading) and Luiz's three decisions: the loop lives here, a matcher that works lives
here (no D5 boundary), the policy is open-ended; close fast, end with a practical engine. D17
supersedes D5. Read for context: bioeye (the loop that ran, 432 lines), active-stereo (the
framework whose loop never ran), bio-3d-vision (thirteen foreclosures on a uniform sensor;
od-004 named the variable-resolution sensor as the untested form — this project). The prior
those give the policy: not looking twice beats the objective; coverage is the gain.

C1: `tools/stereo_field.py`, numpy-only (imports rig, stereo_instrument; PIL only for the
sheet), so C2 can call `field_of_pair` inside the Blender session. Levels l = 0..4 with cell
2^l s_eval owning eccentricity (E2 (2 2^(l-1) - 1), E2 (2 2^l - 1)]: 2, 6, 14, 30, 62 deg at the
standard warp; per level B3's maps, NCC + LK, plus the R->L match for left-right consistency,
the bound, and a variance sigma_p^2 = (kappa bound)^2 + (floor cell)^2; inverse depth by the
sine rule with the exact Jacobian; record per pair `field/p<NNN>.npz`, `field.json`, `--sheet`.
Checks (o) ownership, (p) level 0 = the instrument to 25%, (q) bound below the error per
level, (r) LR consistency rejects and lowers gross; `--self-test` with a synthetic verged
pair on a textured wall at 2 m and a card at 1 m.

Found while building, on the synthetic pair (numbers measured there, not on renders): a
periodic synthetic texture gave 75% gross at level 0 (a stimulus is an instrument — replaced
by 60 random sinusoids); at the coarse levels the LK step recovered about half of a
fractional shift (bias +0.09 cells at level 4 for true shifts of -0.16, none at a 20 m wall
where the shift is ~0; not the warp: the same on uniform sampling; not the window model: a
2-parameter shift-plus-gradient LK did not change it) — one pass of [1,2,1]/4 along theta
halves it and improves level 0 from 0.14 to 0.06 cells RMS; a floor in the variance was needed
because the coarse levels' error (0.32-0.39 cells at levels 1-4 on the stub) is 15-30x the
bound. Stub (`fake_blender_pairs.py`, plumbing and geometry only): 50 pairs in 8.3 s, ~2950
cells per pair (2640 consistent), owned/covered 0.986, level 0 inlier RMS 0.0512 deg vs the
instrument's 0.0510 (0%), gross 13.6% -> 6.2% after LR at level 0; control run (`--search-deg
4`): (p) 11%, all checks pass. Negatives: `--no-lr` fails (r) on every level; `--eval-factor
4` fails (p) at 134%. Predicted for the workstation: level 0 within 10% of B3's 0.269 s0 on
`calib_room_sp`; floor per level 0.2-0.4 cells on the room's walls; kappa near B3's 2.5 at
level 0 and above it at the coarse levels.

## 2026-09-17 — C1 run on the workstation: (o), (q), (r) pass everywhere, (p) fails on 7 of 8 runs; the smoothing costs level 0

All measured (`field.json` per run; `stereo.json` for the instrument), host side, nothing rendered.
Self-test ok (0.2 s). Runs: calib_room_sp 5.0 s, control 5.4 s, full 16.5 s, sweep 3.6–8.4 s;
cells/pair median 2100 (consistent 2002) at small, 9848 (8536) at full; owned/covered 0.984–0.990
(1.029 on E2 1). Negatives: `--no-lr` fails (r) on all five levels, `--eval-factor 4` fails (p) at
428%; both exit 1. (p) as shipped: 0.0505 vs 0.0269 deg (87%) on calib_room_sp, field worse.
Found: `main()` overwrote the per-pair `judged` flag with the judged-cell count, so the 8 wire
pairs the instrument does not judge entered (p); fixed (count now `judged_cells`), the only code
change. After it, (p) field vs instrument in deg: calib_room_sp 0.0460 vs 0.0269 (71%, FAIL);
control 0.0652 vs 0.0535 (22%, pass); full 0.0152 vs 0.0208 (27%, FAIL, field better); e2_1
0.0396 vs 0.0270 (46%); e2_4 0.0456 vs 0.0262 (74%); emax_30 0.0406 vs 0.0293 (38%); emax_60
0.0425 vs 0.0285 (49%), all FAIL. Diagnosed with `field_of_pair(smooth=False)` from a scratch
harness, nothing else changed: calib_room_sp level 0 0.0394 -> 0.0291 deg (0.39 -> 0.29 s0 vs
the instrument's 0.269), gross before LR 14.6 -> 8.9%, pooled like-for-like 0.0250 vs 0.0269 (7%),
(p) 0.0278 (3%, would pass); control (p) 7%; full unchanged (level 0 0.0156 vs 0.0160 deg, (p)
28%). Coarse levels without smoothing: levels 3-4 RMS 0.40/0.23 -> 0.45/0.27 cells, bias
+0.42/+0.48 -> +0.51/+0.61 deg. The wider level-0 grid is not the cause (margin 0: same to
0.0001 deg). Also: (p) compares an RMS of per-pair RMS against the instrument's pooled RMS; the
instrument's own per-pair aggregate is 0.0308 vs its pooled 0.0269 (15%). Per level on
calib_room_sp: inlier RMS 0.20/0.26/0.39/0.40/0.23 cells, kappa measured 3.25/3.75/5.34/6.28/5.35,
floor 0.13/0.20/0.34/0.37/0.20 cells, z RMS 0.57/0.73/1.12/1.20/0.71, depth RMS 0.35 -> 5.6 m;
full: 0.16/0.23/0.26/0.33/0.34 cells, kappa 7.21/4.22/4.35/7.58/9.29, floor
0.13/0.10/0.13/0.29/0.31, depth RMS 0.08 -> 3.8 m. Coarse levels carry a positive bias
(+0.15 deg at level 2, +0.4-0.5 at 3-4), red over the cards on the sheet. Left for Chat: the
smoothing at level 0, (p)'s aggregation and tolerance; C2 should not take level-0 kappa/floor
until then. README C1 row -> run, (p) open. Sheet copied to docs/reference.
