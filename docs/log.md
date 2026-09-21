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

## 2026-09-17 — C1 after the first run: smoothing from level 2, (p) pooled and one-sided; not yet re-run

Read Code's report (repo `main` at 22e4e76). (o), (q), (r) pass everywhere; negatives fail as
designed; (p) fails on 7 of 8 because (i) the wire pairs were pooled in (Code fixed the
`judged` collision) and (ii) the theta-smoothing costs level 0 on the renders — measured by
Code with the keyword patched: `calib_room_sp` level 0 0.39 -> 0.29 s0 without it, gross
14.6% -> 8.9%, pooled like-for-like 0.0250 vs the instrument's 0.0269 (7%); levels 3-4 lose
without it (0.40/0.23 -> 0.45/0.27 cells). The synthetic wall had predicted a gain at level 0
because its texture was oversampled there; the room's cards are at the cell scale. Changes:
`field_of_pair(smooth_from_level=2)` / `--smooth-from` (levels 0-1 are the instrument, 2-4 are
de-biased); (p) pools the level-0 LR-consistent inliers within 2 deg over the instrument's
judged pairs against the instrument's pooled RMS and fails only when worse by > 25% — at full
the field is 27% BETTER (LR consistency removes 5% of cells the instrument keeps), which the
old two-sided check called a failure. Stub: (p) -11%, all checks pass, `--eval-factor 4` fails
(p) at +61%, `--no-lr` fails (r) x10. Predicted for the re-run: (p) passes on all eight;
level-0 kappa near 3 and floor ~0.1 cell at small (Code's unsmoothed level 0), coarse levels
unchanged from the first run. C2 reads kappa and floor per level from the re-run's
`field.json`. Also: the apply block now uses the repo's real path and `sha256sum -c`.

## 2026-09-17 — C1 second run: every check passes on all eight runs; C1 done

All measured (`field.json` per run, `stereo.json` for the instrument), host side, nothing
rendered, no code changed. Self-test ok (0.2 s). (p) pooled, field vs instrument in deg:
calib_room_sp 0.0250 vs 0.0269 (-7%, 9148 cells); control 0.0523 vs 0.0535 (-2%); full 0.0158
vs 0.0208 (-24%, 40194 cells); e2_1 0.0187 vs 0.0270 (-31%); e2_2 = calib_room_sp; e2_4 0.0234 vs
0.0262 (-10%); emax_30 0.0262 vs 0.0293 (-11%); emax_60 0.0261 vs 0.0285 (-8%). (o) 0.984-0.990
(1.029 on E2 1), (q) and (r) pass at every level. Negatives: `--no-lr` fails (r) x10, exit 1,
(p) -2%; `--eval-factor 4` fails (p) at +206%, exit 1. Wall: sp 5.0 s, control 5.4 s, full
16.7 s, sweep 3.6-8.3 s. calib_room_sp per level: inlier RMS 0.14/0.25/0.39/0.40/0.23 cells
(0.29/1.00/3.10/6.44/7.42 s0), gross before -> after LR 8.9->5.7 / 23.3->20.0 / 17.0->16.7 /
0.5->0.2 / 0.3->0.2 %, kappa measured 4.58/4.26/5.34/6.28/5.35, floor
0.12/0.20/0.34/0.37/0.20 cells, z RMS 0.45/0.73/1.12/1.20/0.71, depth RMS 0.28 -> 5.6 m.
full: 0.16/0.22/0.26/0.33/0.34 cells, kappa 7.70/4.34/4.35/7.58/9.29, floor
0.14/0.11/0.13/0.29/0.31, z RMS 0.50/0.62/0.78/1.04/1.06, depth RMS 0.07 -> 3.8 m. Levels 2-4
identical to the first run (same code path); levels 0-1 are the unsmoothed matcher's; level-0
RMS/bound at small is 4.6, not the predicted ~3, because the bound halves without smoothing
(0.0121 -> 0.0063 deg) while the error falls less. README C1 row -> done. Sheet replaced.
C2 reads kappa and floor per level from these field.json files.

## 2026-09-17 — C1 closed (Code's second run, b7ab372); C2 written and run on the stub; not yet run on the workstation

C1: every check on all eight runs; (p) -7% small, -24% full (the LR test); level-0 RMS/bound
4.6 at small (the bound halves without the smoothing, the error less); floor 0.10-0.37 cells
per level. C2 reads kappa and floor per level from those runs.

C2, five files. `fixation_pairs.py` refactored into `PairRenderer` (setup once, `render_pair`
on demand, `seed_pass`, `finish`; `add_render_args`) — stub output identical modulo timings,
check_pairs passes. `belief.py`: SphereBelief on the epipolar grid at s_eval (898x1796 at
small), inverse-variance fusion with the measurement splatted over the belief cells it
covers; the variance split into a noise part that averages across pairs and a model floor
that does not (found on the stub: with one variance the periphery's sigma went to zero after
ten overlapping coarse measurements while its error did not); gating of a coarser
measurement that disagrees by 3 sigma; the visit map (owned cells, matchable or not) so the
policy tells unseen from unmeasurable; truth from the L eye's own ray distances; metrics
over the cap (coverage any/fine apart from error on measured cells by band, calibration z).
Policies targets, random, coverage, info (expected information with the running per-level
sigma_rho of the run's own fields, out to 14 deg), oracle; candidates every 2 deg in a 60 deg
cap; scored on a 1 deg grid (2969 candidates in 0.2 s). `active_loop.py` (Blender side): the
loop in one session; vergence from the belief within 2 deg of the target, else over the cap,
else z0; fixation 0 rendered twice to calibrate the noise per level; search range 6 deg.
`active_eval.py` (host): replay check (s), calibration (t), learning (u), not-twice (v);
bioeye's four panels per run; the comparison chart across runs. `stereo_field.py` now also
returns the owned cells (the visit map) and the two variance parts per row, and accepts a
per-level noise_rel. `check_pairs.py` and `stereo_truth.py` report instead of crashing on a
run with no judged card pairs (three empty-max sites). `tools/dev/fake_blender_loop.py`.
D18: the evaluation contract.

Stub, 20 fixations each, equal rays: median rho error info 0.0456 < coverage 0.0470 < oracle
0.0530 < random 0.0549 < targets 0.0959 /m; fine coverage coverage 0.190 > random 0.174 >
oracle 0.155 ~ info 0.154 > targets 0.078; z RMS 0.66-0.85; vergence error from the
periphery median 0.5-0.9 m at 2-4 m; (s)-(v) pass on all five. Per fixation 0.7 s on the
stub. Predicted for the workstation: ~1 s per fixation at small, a minute per run; the
spreading policies within 20% of each other on error and all well ahead of target order at
50 fixations; whether info beats coverage on the fine band is the open question, and the
render's textured walls (not the stub's noise texture) decide the coarse-band gross fraction.

## 2026-09-17 — C2 run on the workstation: the loop closes at 0.3-0.5 s per fixation; (t) and (v) fail on the model-driven policies, which lock onto an unmeasurable direction

All measured. Refactor check: calib_room_c2check re-rendered in 11.2 s; check_pairs, stereo_truth,
stereo_instrument ok, instrument summary = calib_room_sp to 1e-8 (0.0269 deg, 12604 cells).
Self-tests ok. Five runs x 50 fixations at small: targets 15.2 s, random 15.3, coverage 17.3, info
23.0, oracle 21.7 (render 0.08-0.11 s per pair, field 0.13-0.23 s, choose 0.09-0.14 s for the
scored policies). Eval: (s) exact and (u) pass on all five; (t) FAILS info 0.310, oracle 0.298
(band [0.4, 2.5]); (v) FAILS coverage, info, oracle at fine coverage 0.004 vs random 0.069. Final
at 8.0e7 rays: rho err median random 0.1641 < oracle 0.1741 < info 0.1894 < coverage 0.2052 <
targets 0.2101 /m; fine coverage targets 0.179 > random 0.069 > the three at 0.004; coverage any
0.961 / 0.955 / 0.563 / 0.853 / 0.887 (targets/random/coverage/info/oracle); gross 0.62-0.71;
coarse-band gross 0.67-0.82 (stub 0.35-0.40). Diagnosis: coverage fixates (-22, +56) deg 49
times (score bit-identical, 0.18876), info locks on (+58, -16) from k013, oracle on (+60, 0)
from k020; in the loop's own records no eccentric fixation of the three yields any consistent
level-0/1 row (only cards do: random p002 130+188, p019 153+200). Cause 1: the carried noise,
calibrated on fixation 0's seed pair, is 0.177/0.173/0.162/0.143/0.084 relative per level; the
host-side field on a copy of the info record judges 6545 level-0 cells (gross 4.6% -> 2.0%) at
--noise-rel 0.07 and 79 (gross 49%) at 0.177 — the walls are matchable finely, the thresholds
at the calibrated noise reject them. Cause 2: coverage scores best_level (measured) not visited;
the visit-map zero applies only to visited-and-never-measured cells, so cells a coarse level has
measured keep a floor-limited variance and info/oracle's gain to re-look never falls. Vergence
error median info 1.54 m, oracle 2.81 m (the locked fixation's own); --search-deg 8 diagnostic
(diag_info_s8, diag_oracle_s8): 1.56 / 1.07 m, fine 0.004, (t)(v) fail the same way. Hazard:
stereo_field.py on a loop run overwrites field/p*.npz (the loop's record); info run re-rendered
to restore it (final numbers identical to 1e-9), host-side field then run on a symlinked copy.
Phase B tools on calib_info: check_pairs ok (0 judged card pairs), stereo_truth ok, stereo_field
--noise-rel 0.07 ok ((p) skipped). info level_sigma_final 0.0199/0.0415/0.2166/0.2096/0.4410.
No code changed. README C2 row -> run, open. Figures copied to docs/reference. Decisions for
Chat: the noise carry, the gain model's use of the visit map, and whether the room's walls are
the scene to rank policies on.

## 2026-09-17 — C2 after the first run: per-cell noise in the field, the visit map in the policies; not yet re-run

Code's run (repo `main` at 6db42ed): the loop at 0.3-0.5 s per fixation, PairRenderer exact
to the eighth digit, (s) and (u) pass; coverage/info/oracle lock onto one edge direction (49
of 50 for coverage), (t) and (v) fail. Two causes, Code's diagnosis confirmed here: (i) the
carried noise 0.177 vs the manifest's 0.073 — the equivalence assumed 4 samples per level-0
cell, the wide map has 1.2 (measured on the stub), the walls became unmatchable at fine
levels; (ii) the gain model scored "not measured" not "not looked at", and the zero-gain rule
missed coarsely-measured cells. Fixes: `stereo_field.py` — sigma per CELL from the per-sample
relative RMS nr (measured from a seed pair as a robust median, else assumed) and the owning
sample count (`accumulate` now returns `_count`), for the bound, the texture gate and the
assumed path alike (stub: nr 0.0097-0.0101 at every level, one number as it should be);
`signal_information` carries no information where sigma is unknown; the host-side field on a
loop run writes `field_check/`. `belief.py` — coverage scores the visit map; info/oracle count
a cell only where measured at some level or where the look would be two levels finer than the
finest failed one; coverage's radius is the fine disc (6 deg). Self-test has the three cases.
Stub with blank walls (`FAKE_BLANK_WALLS=1`, new in the stub): info 27 distinct of 30, coverage
30 of 30, info's fine coverage 0.074 vs random's 0.058. Textured stub, 20 fixations: coverage
0.0442 < info 0.0459 < random 0.0536 < oracle 0.0542 < targets 0.0960 /m; (s)-(v) pass.
Predicted for the re-run: no lock, fine coverage above random's for the spreading policies, z
RMS in band. On Code's third question — the calib room is the test of the mechanism (only the
cards are richly textured); the classroom, textured everywhere, is where a ranking means
something, and C3 runs it.

## 2026-09-17 — C2 second run: per-cell noise holds C1's checks and fixes coverage; info still locks, oracle half so; (t) and (v) open

All measured, `previews/loop2/`. Self-tests ok. C1 with the per-cell noise: calib_room_sp all
pass, (p) -3% (0.0260 vs 0.0269 deg), level-0 RMS/bound 5.82 (bound 0.0051 deg), floor 0.13;
full all pass, (p) -24%, RMS/bound 9.76. noise_rel_equiv per level: sp p000
0.0705/0.0751/0.0793/0.0900/0.0893 (median over pairs 0.066-0.081; manifest 0.07), full p000
0.0340/0.0351/0.0380/0.0413/0.0419 (median 0.032-0.037; manifest 0.036): one number to 25%,
rising slightly with level. Loops carry 0.0704/0.0748/0.0801/0.0893/0.0893. Runs 16.2-23.3 s
(0.3-0.5 s per fixation). Final at 8.0e7 rays: rho err median coverage 0.1052 < random 0.1111 <
info 0.1126 < oracle 0.1386 < targets 0.1397 /m; fine coverage targets 0.201 > coverage 0.138 >
random 0.116 > oracle 0.039 > info 0.013; coverage any 0.94-0.996; z RMS 0.57/0.51/0.49/0.32/
0.42; distinct directions 50/49/50/14/25. (s), (u) pass on all five; (t) FAILS info 0.322
(level_sigma_final 0.0250/0.0637/0.1205/0.1573/0.3783); (v) FAILS info 0.013 and oracle 0.039
vs 0.5 x 0.116. Info locks on (-26, +56) deg from k013 (37 of 50) with z_hat 11.0 m from the
belief within 2 deg against 1.93 m (vergence median 9.07 m), fine cells constant, visited_fine_
unmeasured 0.0128 at the end; oracle repeats (36, 40) x10 and (-46, 36) x12 where its belief is
wrong (1.58 vs 2.69 m). Both directions were measured coarsely from afar, so the new rule holds
them "known measurable" while the fovea finds nothing there; the gain never falls. Stopped per
the prompt; the rule is Chat's. Coverage: 50 distinct, fine above random, lowest error, walls
yield fine cells (visited_fine_unmeasured 0.0046). Record check: field_check/ 50 files, field/
50 files untouched, single-run eval (s) ok. No code changed. README C2 row stays run, open.
Figures replaced in docs/reference.

## 2026-09-17 — C2 after the second run: fine-level measurability, the cap as the gain's domain, IOR for the oracle; not yet re-run

Code's second run (repo `main` at 943ba88): noise 0.07 at every level, C1 holds, coverage
50 distinct and best (0.1052 /m), info locked on the ceiling (14 distinct, belief 11 m vs 1.9
m), oracle 25 distinct; (t), (v) fail on those two. Cause, Code's: "measured at any level"
counted a coarsely mis-measured ceiling as measurable. `belief.py`: allowed = measured at
levels 0-1, or a look two levels finer than the finest failed one; gain masked to the field
of regard (edge candidates were scoring cells beyond the cap: info's first 13 fixations at
+-56-60 deg); explicit IOR 3 deg for the oracle only (`--ior-deg`, default 0 for policies);
fixation 0 enters the history. Self-test adds the coarse-plus-empty-fine case. Blank-walls
stub: info 30/30 distinct, oracle 30/30. Textured stub, 20 fixations: coverage 0.0464 < info
0.0482 < random 0.0536 < oracle 0.0713 < targets 0.0960; fine coverage coverage 0.204 ~ info
0.203. Predicted for the third run: info >= 40 distinct, (t) and (v) pass on all five.

## 2026-09-17 — C2 third run: oracle fixed, (t) passes everywhere; info locks a third way, on a finely-measurable wall; (v) open on info

All measured, `previews/loop2/` (info and oracle re-run; the other three from the second run).
Self-test ok. Banners IOR 0 (info), 3 deg (oracle). info: 24.1 s, 28 distinct of 50, cover any
0.989, fine 0.053, rho err median 0.1006 /m, z RMS 0.44, vergence median 0.51 m; oracle: 23.1 s,
50 distinct, cover any 0.993, fine 0.074, rho err 0.1462, z 0.50, vergence median 2.66 m. Eval:
(s) exact, (t) 0.44-0.57 and (u) pass on all five; (v) passes on four and FAILS on info (0.053 <
0.5 x 0.116). Rankings: rho err info 0.1006 < coverage 0.1052 < random 0.1111 < targets 0.1397 <
oracle 0.1462; fine coverage targets 0.201 > coverage 0.138 > random 0.116 > oracle 0.074 >
info 0.053; fine-band error targets 0.0149, coverage 0.0249 ~ info 0.0252 ~ random 0.0253. Info's
lock: 26 spread fixations (cap covered by k024), then (+48, -10) deg x23 from k026: z_hat
3.61-3.71 m vs centre 4.12 (vergence fine), field identical each time (1840 cells; consistent
rows 0/93/535/728/332 by level: no level-0, 93 level-1 on a weak-texture wall), fine coverage
constant, score 0.031-0.041 (0.51 at k001), visited_fine_unmeasured 0.0012 at the end. The
direction is finely measurable, so the new rule admits it; its 93 cells' variance is floor-
limited and does not fall with re-measurement, so once no unseen cell remains the gain
landscape is flat and its argmax a fixed point; the oracle escapes only by its IOR. Stopped per
the prompt; the gain model (noise-only variance in the gain, a minimum cell yield to retire a
direction, or an IOR for info) is Chat's. No code changed. README C2 row stays run, open.
Figures replaced.

## 2026-09-17 — C2 after the third run: info's gain is the expected reduction of the belief's own variance; not yet re-run

Code's third run (repo `main` at e18330f): oracle 50 distinct with IOR, (t) passes on all
five, info best on error (0.1006 /m) but locked on a finely-measurable wall from k026 (28
distinct; 93 level-1 cells, floor-limited). Cause, Code's: 1/2 log(1 + sigma^2 I) with sigma
all floor — the model's own variance cannot fall there, the gain never did. `belief.py`:
info's gain = 1/2 log(var_before / var_after) with var = 1/P_noise + floor^2, the noise part
averaged down by the level's noise precision and the floor replaced by the smaller floor;
`LevelSigma` tracks noise and floor medians per level (in loop.json too); the noise-precision
map masked to the cap as the variance map was (cells beyond the cap looked unseen — the edge
pull, found on the stub). Self-test adds the fixed-point case. Stub: blank walls info 30/30;
textured 40 fixations (the cap gets covered, which reproduced the lock at 12/40 before the
fix) info 37/40, coverage 0.0434 < info 0.0460 < random 0.0476 < targets 0.0673 < oracle
0.0729 /m, fine coverage coverage 0.407 > info 0.309 ~ random 0.306; (s)-(v) pass. Predicted
for the fourth run: info >= 40 distinct, (v) passes, C2 closes.

## 2026-09-17 — C2 fourth run: (s)-(v) pass on all five; info 45 distinct, one wall six times then released; closing left to Chat

All measured, `previews/loop2/` (info re-run only). Self-test ok. info: 26.3 s (choose 10.7 s
of it; 0.21 s per choice), 45 distinct of 50, cover any 0.999, fine 0.080, rho err median
0.1027 /m, gross 0.539, depth err median 0.769 m, z RMS 0.45, vergence median 0.59 m. Eval ok
(0 failures): (s) exact, (t) 0.45-0.57, (u), (v) all pass. Rankings: rho err info 0.1027 <
coverage 0.1052 < random 0.1111 < targets 0.1397 < oracle 0.1462; fine coverage targets 0.201
> coverage 0.138 > random 0.116 > info 0.080 > oracle 0.074. The prompt's repeat limit (five)
is exceeded once: (-56, +6) deg at k042-k047 (six), then k048 (+38, -12), k049 (-16, +34) —
the direction retired itself. There: z_hat 3.18 m vs centre 3.61; field rows by level
3/84/675/721/242; sigma parts at k042 noise 0.0045/0.0199/0.0352/0.0588/0.1146, floor
0.0177/0.0392/0.0741/0.1445/0.3441 /m. Final level_sigma_noise 0.0045/0.0219/0.0385/0.0610/
0.1208, floor 0.0177/0.0421/0.0763/0.1477/0.3596. Reported and stopped per the prompt; README
C2 row stays run, open with the reason (all checks pass; the six-repeat is Chat's call). No
code changed. Figures replaced.

## 2026-09-17 — C2 closed (Code's fourth run, f19a6a6); C3 written, not yet run

C2: (s)-(v) on all five, info 45 distinct (six looks at one wall, then released — the two-part
gain retiring a direction on its own, not a lock), error info 0.1027 < coverage 0.1052 <
random 0.1111 < targets 0.1397 < oracle 0.1462 /m; fine coverage targets 0.201 > coverage
0.138 > random 0.116 > info 0.080 > oracle 0.074. Four runs to close: the loop's mechanics
were right the first time (0.3-0.5 s per fixation, the record replays), and each run found
one hole in the model — the noise carry, the visit map, "measurable at any level", the
floor in the gain — each caught by the record, each fixed in the model, none by a threshold.
C3 (`docs/c3-closing.md`): the classroom at small with the four policies that need no target
list, one `full` run (info), then the summary and the README as the engine's front page. No
new code.

## 2026-09-17 — C3 run: the classroom at small and info at full; (s), (t), (v) pass, (u) fails on all five by its definition; info last on the textured scene

All measured, `previews/loop3/`. Classroom at small, 50 fixations: random 29.2 s, coverage 31.7,
info 37.9, oracle 36.4 (render 0.33-0.37 s per pair, the scene's call floor); info at full 78.6 s
(1.6 s per fixation; belief 1803x3606 cells, no memory issue), kappa 3.8. Distinct directions
49/50/50/50 and 50 (full): no lock. Final at 8.0e7 rays: rho err median random 0.0808 <
coverage 0.0852 < oracle 0.0940 < info 0.1006 /m; fine coverage coverage 0.066 > random 0.054
> oracle 0.046 > info 0.044; cover any 0.84-0.88; gross 0.49-0.55, coarse band 0.54-0.59; z
0.62-0.69; vergence medians 0.38-0.77 m, 7-9 fixations per run more than 2x off z_hat. Full:
rho err 0.0435 (fine 0.0186), depth err median 0.375 m (fine 0.140), cover any 0.920 fine
0.059, gross 0.355 (coarse 0.43), z 0.85, vergence median 0.71 m, level_sigma_final
0.0118/0.0216/0.0447/0.0922/0.1875. Noise per level calibrated: small 0.176/0.176/0.201/0.222/
0.231, full 0.083/0.082/0.096/0.101/0.105 — the manifest's 0.092 at 256 spp (0.18 at 64):
the classroom is 2.5x noisier than the calib room at the same spp, fields 760-1240 cells vs
~2000, and the fine band is 4-7% of the cap, smaller than the calib room's, not larger. Evals:
(s) exact, (t) in band on all five; (v) passes on the four small runs, not reported on full (no
random run in the call, as expected); (u) FAILS on all five: median rho err after fixation 0
0.0799 (full 0.0397) vs final 0.081-0.101 (full 0.0435) while coverage rose 0.34 -> 0.84-0.92.
The median is over measured cells, and the set grows from the middle of the room to the whole
cap, mostly coarse floor-limited cells; two medians over different sets. Reported, not changed;
whether (u) compares on fixation 0's cells or on the cap at the prior is Chat's. Finding: info
separates from coverage here, downward — last on error and fine coverage with no lock; random
is best on error; the spread among random/coverage/oracle (25%) is within the fine band's
+-30% noise between fixations. Phase B tools on class_info: check_pairs ok (0 card pairs),
stereo_truth ok. No code changed. README C3 row -> run. Three figures in docs/reference.

## 2026-09-17 — C3 after the run: (u) redefined on a fixed cell set; the classroom at small is noise-limited; four policies at full next

Code's run (repo `main` at 55fb184): five runs, no lock; classroom small — random 0.0808 <
coverage 0.0852 < oracle 0.0940 < info 0.1006 /m, fine coverage 4-7% of the cap, gross
49-55%, noise 0.18 relative (2.5x the calib room, as the manifest says); info full 0.0435 /m
(fine 0.0186), gross 0.355, 79 s. (u) failed on all five by its own definition (median over a
growing set); redefined in `active_eval.py`: the cells measured and judged after fixation 0,
the same cells at the end, may not get worse by more than 5% (stub: 0.114 -> 0.07 /m). No
loop re-run needed. Reading of the small runs: with half the measured cells gross, the
variance-driven policy optimises a model that is wrong where it matters and loses to the two
policies that do not consult it; the objective bought nothing where the model was right
(calib room) and costs where it is wrong. Next: random, coverage, oracle at full on the
classroom beside the info run, evals of the five with the new (u); then the summary and the
front page.

## 2026-09-17 — C3b: classroom at full, four policies; all thirteen runs pass under the new (u); info third at full, random first at both profiles

All measured, `previews/loop3/`. Random, coverage, oracle at full (kappa 3.8): 68.4 / 74.9 /
77.5 s (1.4-1.6 s per fixation), distinct 49/50/50; final at 1.287e9 rays: rho err median
random 0.0385 < coverage 0.0427 < info 0.0435 < oracle 0.0453 /m; fine coverage coverage 0.094
> random 0.078 > oracle 0.064 > info 0.059; fine-band error oracle 0.0139 < random 0.0155 <
coverage 0.0177 < info 0.0186; gross 0.31-0.37 (coarse 0.38-0.43); z 0.74-1.02; vergence
medians 0.33-0.71 m. Evals: (s), (t), (u), (v) pass on all thirteen runs (exit 0). (u)
fixation-0 cells: classroom full 27427 cells 0.0397 -> 0.0180-0.0195; classroom small 5627
cells 0.0799 -> 0.0412-0.0535; calib room 10820 cells 0.2160 -> 0.2009-0.2155 (0-7%; the
central cards' surround is gross at its depth edges and the coarse looks cannot lower it).
Small rankings unchanged (re-judged, not re-rendered). Reading: at full info recovers from
last to third, within 2% of coverage, still last on fine coverage; random first on error at
both profiles (by 10% at full), coverage first on fine coverage at both; spread 18% at full.
No code changed. README C3 row stays run. Figure c3_compare_classroom_full.png added.

## 2026-09-17 — Phase C closed: the summary, the front page, D19

Code's C3b (repo `main` at 81dff57): thirteen runs, every check under the redefined (u), the
fixation-0 cells improving on all; classroom at full random 0.0385 < coverage 0.0427 < info
0.0435 < oracle 0.0453 /m, fine coverage coverage 0.094 > random 0.078 > oracle 0.064 > info
0.059. `docs/phase-c-summary.md` written in the tradition of A and B (question, what was
built, the result table over three settings, eight lessons, what is open); the README
rewritten as the engine's front page (what it is, one command, the numbers at full, the
sequence of four repositories, a table of the tools; the phase tables kept as history); D19
closes the phase with coverage-first as the default policy and names what would overturn it.
The one reading added beyond Code's: the objective bought 2% where the variance model was
right and cost 3-20% where it was wrong, and a policy that does not consult the model cannot
be misled by it. Phase C: two days, three steps, eleven handoffs, thirteen loop runs of
20-80 s; the loop's mechanics unchanged from the first run, its model corrected four times by
its own record.

## 2026-09-17 — sphere_views.py: the scene as it is and as the engine saw it, two formats; not yet run on renders

`tools/sphere_views.py` (host side): from a loop run and, optionally, a preview360 panorama
rendered at the L eye (`--truth`), (RGB, depth) in equirectangular (preview360's convention)
and on the epipolar sphere (phi across, theta down: the baseline axis is the top and bottom
edge, the primary gaze the centre, every epipolar line a row), for two sources — the
panorama and its Depth pass; the loop's fixations integrated finest-owns with each sample
painted over its footprint (at s_eval the periphery is otherwise 18% filled) and the belief's
depth. Eight panels, four depth .npy, the scanpath, one sheet with a shared log depth scale.
Without --truth the L eye's own rays stand in for the scene, labelled so. Stub: 10 s, 58% of
the sphere seen, 52% with a depth. To run on the workstation: the classroom L-eye panorama
(preview360 --eye-offset -0.0315 0 0, B2's convention, a minute at small) and a loop run.

## 2026-09-17 — sphere_views on the renders: the picture; one loader fix; the full L-eye classroom panorama rendered (reference class)

Measured. Panoramas from the L eye (preview360 --eye-offset -0.0315 0 0): classroom small
70.1 s render; classroom full 2137.4 s (7200x3600 at 8192 spp — the prompt predicted a minute,
this is A2's reference class, 1940 s in the manifest for the R-eye-free one; kept as an asset,
md5 de47b7629026782015ede6cdaeaefb65, not in the manifest yet). Fix in sphere_views.py, one
flag: OpenEXR 3.4 groups RGBA into one 'ViewLayer.Combined' array, so the loader's suffix
search for 'Combined.R' failed; the file is now opened with separate_channels=True (as the
channel names in the file already are). Runs: class_coverage_full vs the full panorama —
2551239 shared cells, median |rho err| 0.0816 /m, median |depth err| 0.358 m (C3b: 0.351 m
over all measured cells), 58.6% of the sphere seen, 40.3% with a depth, 32.6 s; class_coverage
(small) vs the small panorama — 640534 cells, 0.1465 /m, 0.630 m, 60.6% / 42.1%, 8.8 s;
calib_info vs B2's small L reference — 878315 cells, 0.1257 /m, 0.869 m, 64.0% / 54.5%, 7.4 s.
Rows agree in orientation on both scenes (lamp, windows, near desks in the same places; the
engine's row sharp at the fixations, blurred in the periphery, dark outside the cap). Sheet
copied to docs/reference/views_classroom_full.png; "The picture" added to the Phase C summary.

## 2026-09-17 — the picture drawn by confidence; Phase D planned (D20); manifest entries for the L-eye panoramas

`sphere_views.py`: the engine's depth is now a precision-weighted 3x3 median of inverse depth
on the sphere (a wrong peak at a depth edge gives way to its neighbours), faded toward the
unknown grey by confidence — solid at sigma_rho <= the run's level-1 sigma, grey at >= its
level-3 sigma (`--conf-sigma` overrides; `--raw` is the first picture); the fine band alone
and the confidence map are panels of their own; sigma saved as .npy. Stub: solid on 3.7% of
the sphere, half-confident on 13.6%, 18 s. Not re-run on the renders yet. `docs/phase-d-plan.md`
and D20: coarse-to-fine in the field (D1) with the decision rule written before the run —
gross down by a third or error by 10% at full on the classroom, coverage-first, 50 fixations
— a gross-error term in the fusion only if needed (D2), the 500-fixation run to decide next
week (D3). `scenes/manifest.json`: `reference_full_L` for the classroom (md5
de47b7629026782015ede6cdaeaefb65, 2137 s) and `reference_small_L` (md5 to be filled by Code).

## 2026-09-17 — the picture by confidence on the renders; manifest md5s filled

Measured. sphere_views with the weighted median and the sigma fade: class_coverage_full vs the
full L panorama — 2589422 shared cells, median |rho err| 0.0822 /m, |depth err| 0.359 m; solid
on 1.1% of the sphere, half-confident or better on 5.5% (solid sigma <= 0.020, grey >= 0.089
/m); 58.6% seen, 40.9% with a depth; 35.0 s. class_coverage (small) — 650208 cells, 0.1458 /m,
0.629 m; solid 0.9%, half 5.1% (0.046 / 0.187); 9.5 s. calib_info — 887754 cells, 0.1247 /m,
0.862 m; solid 1.1%, half 8.0% (0.048 / 0.162); 8.1 s. The predicted "solid ~8-9%, the fine
band" mixed the cap and the sphere: the fine band is 9.4% of the 60-degree cap = 2.3% of the
sphere, and solid (1.1%) is half of it, half-confident (5.5%) 2.3x it. The speckle is gone:
solid colour only along the fixated desks, the far wall faint, the periphery grey. md5s:
reference_small_L/classroom pano 17bdfa4a8dab7260fd95926b9a61aa9e, backface
06038dd4afbc5a0c7be885e1d1e05fa7; reference_full_L/classroom backface
ac86e5f65f40d69d9b3658821ad79de8 — in the manifest. Figures replaced/added in docs/reference.
No code changed.

## 2026-09-18 — belief.py: the module docstring caught up with the code (a review observation)

The third-party reviewer noticed the docstring still gave info's gain as 1/2 log(1 + sigma^2 I)
while `_score` computes 1/2 log(var_before / var_after). Cause: the C2 third- and fourth-round
docstring edits were `str.replace` calls whose old text no longer matched, so they did
nothing while the code moved. The policies paragraph now states what runs: coverage on the
visit map; info on the two-part variance, fine-level measurability, the cap mask; oracle's
inhibition of return. No code change; self-test ok.

## 2026-09-18 — Phase D plan revised after a third-party review; the review filed

`docs/reviews/2026-09-18-phase-d-suggestions.md` with the reading. Changes to the plan: the
diagnosis of the gross errors comes first (distance to a depth edge, occlusion from the truth
sidecar, per level; prediction: the window's at levels 0-1, the search's at 3-4);
coarse-to-fine gets a safety valve (parent as proposal; full search on a boundary hit, weak
peak or LR failure) and P(child gross | parent gross); D2 is the window (3x3 at the fine
levels, photometrically weighted 5x5), D3 the inlier probability in the fusion (conditional,
then coverage vs information only), D4 the long run read at checkpoints. D20 stands as
written. Phase D starts in a new conversation.

## 2026-09-18 — D1a written: the gross-error diagnosis (no rendering, no matcher change)

`tools/gross_diagnosis.py` and `docs/d1-gross-diagnosis.md`. Rebuilds each saved pair's field
with the run's own settings and the truth carried through the accumulation; kinds per
LR-consistent cell: occluded / window / search / resolution / good; depth edges judged per
sample in the L raster; the parent oracle (what a +-2-cell search about the parent would cure
or put at risk). Found while writing it: the repository's two "gross" differ — a wrong peak
(> 1 cell, the field's) and rho beyond 25% (the belief's, the one in D20's rule) — and C1's
table already shows level 4 at 1.3% wrong peaks with an inlier RMS of 0.54 deg, so most of the
coarse band's 0.38-0.43 cannot be wrong peaks. The plan's prediction for levels 3-4 ("the
search's") is revised to "the resolution's" in the note, before the run. Stub only so far
(measured, sandbox): pairs run (y1) exact, loop run rebuilt = record on 100.000% of 44459 rows
once the samples are placed by the record's float32 directions as the loop placed them (by the
sidecar's analytic theta 0.26% of rows move: a cell border for a few samples); negatives
--search-deg and --edge-jump 10 exit 1; by area 90% of the stub's bad cells are resolution.

## 2026-09-18 — D1a run: the gross-error diagnosis on the four records; all checks pass

All measured, host side, nothing rendered. Self-test ok. field.json refreshed on both pairs
runs with the standard flags (C2's second-run numbers back: (p) -3% at sp, -24% at full).
stereo_truth on the loop runs ok (class_coverage 0.7 s, class_coverage_full 2.1 s; (h) reads
None on a loop run). Diagnoses: calib_room_sp 4.8 s, calib_room_full_sp 15.1 s,
class_coverage 6.0 s, class_coverage_full 20.4 s; (y1) 0.0000 / 0.0000 / 100.000% of 46692
rows / 99.999% of 213541 rows; (y2) passes on all four; negatives --search-deg 4 (worst
difference 0.0083) and --edge-jump 10 (no edge cells) exit 1. By area, resolution is
89.1 / 76.9 / 83.7 / 74.6% of the bad cells (bad area 67.3 / 48.6 / 64.9 / 41.5%): prediction 3
holds. Prediction 1 (levels 0-1 the window's) holds on the calib room (excess share 75-95%)
and fails on the classroom (46-54% at full; search 15.3 / 13.1% exceeds window 9.2 / 8.5% at
levels 0-1; far-from-edge wrong peaks at 18-22%). Prediction 2 holds in direction, fails the
50% clause (class_coverage_full level 4: resolution 37.2% of judged cells, 80% of the bad
ones; search 1.7%). Prediction 4: the oracle cures 6-25% of the wrong peaks at levels 0-2 on
the renders (33% at level 3 of calib_room_full_sp), the minority it predicted; at risk under
5% except calib_room_full_sp levels 1-2 (5.0%, 9.0%). Prediction 5 holds: removing the bias
moves P(beyond 25%) by at most -4.6% relative and raises it on 5 of 8 rows at levels 3-4.
The loop-run diagnoses print numpy RuntimeWarnings from stereo_instrument.py:244-262 (per-cell
noise zero on some cells); the rebuilt rows equal the record, nothing changed. No code
change. Figures in docs/reference (d1_diagnosis_classroom_full.png,
d1_diagnosis_calib_room_full.png). D20's rule and the order D1b/D2 not decided here.

## 2026-09-18 — D21: D1 closed as a diagnosis, coarse-to-fine not written; D2a written

After D1a's report (a80342f). D21 in DECISIONS.md; the plan has a new head section; D2a is
`docs/d2-wrong-or-right.md`. Code: `belief.metrics` splits gross = coarse + outlier (beyond
25% and beyond 3 sigma), with a known-answer control in the self-test (outlier 0.10, coarse
0.555 expected, measured 0.10 / in band); `active_eval.py` prints it from the replay;
`ncc_match(second=True)` returns the rival peak; `field_of_pair(features=True)` adds ncc_peak,
ncc_rival, lr_resid_cells (off in the loop, nothing else changes: (y1) on the stub loop run
still 100.000% of 44459 rows); `gross_diagnosis.py` adds the uncured breakdown, the
five-feature separation at 90% of the right peaks kept, `--tag` for what-ifs. Stub only
(measured, sandbox): gross 0.359 = coarse 0.298 + outlier 0.061; parent disagreement rejects
74-78% of wrong peaks at levels 0-1 (90% of search), peak and margin 40-50%, bound 4-6%; the
oracle's uncured are 54-65% "inside the interval" at levels 1-3; `--window 1` raises wrong
peaks at level 0 from 7% to 30% on the stub's noise texture.

## 2026-09-18 — D2a run: the split judge on the thirteen runs, the five features, the 3x3 what-if; all checks pass

All measured, host side, nothing rendered, no loop re-run. Four self-tests ok. The three
active_eval calls (47.1 / 16.8 / 23.3 s) exit 0, (s) replay ok on all thirteen runs, no other
FAIL; compare.json's scalars unchanged from C3b's files, four keys added; gross - coarse -
outlier <= 8e-17 everywhere. Outlier fraction: classroom full 0.098-0.104 of gross
0.314-0.374; by band fine 0.194-0.268 of 0.199-0.284 (the fine band's gross is its outlier
fraction), mid 0.14-0.15 of 0.21-0.23, coarse 0.06 of 0.38-0.43; classroom small 0.08-0.09 of
0.49-0.55; calib room 0.12-0.19 of 0.54-0.63. D21's "overturned if" does not fire. The four
standard diagnoses (4.8 / 15.7 / 6.1 / 20.9 s): (y1), (y2) ok, the level lines equal D1a's
exactly (string diff). Telling wrong from right at 90% of the right kept, class_coverage_full
levels 0-2: parent 33.9 / 44.5 / 39.7% (the best), margin 31.5 / 34.4 / 28.4%, bound 18.0 /
21.5 / 21.3%, peak 11.4 / 14.4 / 15.8% (AUC 0.45-0.51, a coin); no AUC above 0.71 there. On the
calib room the bound is the best at level 0 (68.4% sp, 52.6% full) and the LR residual at
level 2. The uncured wrong peaks are mostly "parent wrong too" or "no parent" at levels 0-2
on the classroom (inside the interval 14.6 / 20.6 / 33.0%), inside only at level 3 (60.8%).
The 3x3 what-ifs (10.3 / 15.5 s, exit 0, (y1) not judged, standard files untouched): on
class_coverage_full judged cells 4736 -> 1557 at level 0, wrong peaks 26.1 -> 45.7%, far rate
21.5 -> 45.2%, worse at every level; on calib_room_full_sp worse at every level too (level 0
wrong peaks 8.5 -> 9.2%, far 1.7 -> 5.0%, a quarter fewer cells). Predictions: 1 held, 2 held
(peak's 30-50% failed low at 11-14%), 3 held on the classroom and failed on the calib room at
levels 0 and 2 and in its "inside the interval" reason, 4 held and the window loses on the
calib room too. RuntimeWarnings from stereo_instrument.py on the loop runs as in D1a. No code
change. D2b not decided here.

## 2026-09-18 — D2b written: the neighbour test (after D2a's report, 374e211)

D2a supported none of its three options (no feature a test: best 44.5% at 90% kept, AUC <=
0.71; NCC peak below a coin at the fine levels; 3 x 3 loses everywhere); the judge split held
(outlier 0.098-0.104 of gross 0.31-0.37 at full; fine outlier ~ fine gross). My reason for the
parent's value was wrong (the uncured are "parent wrong too" and "no parent", not "inside the
interval"). Reading: the classroom's fine levels are the texture gate's margin. Sandbox,
measured: a wall of smooth shading plus noise — below the margin the gates reject every cell,
above it nothing is wrong, at it (0.1-1 c/m, noise 0.03, level 2) 59% of 78 matchable cells are
wrong and LR keeps 22 with 51% wrong. D2b: `neighbour_median` and
`field_of_pair(nb_tol_cells, nb_drop_isolated)` (off by default; record rebuilds exactly),
`active_loop.py --nb-tol`, the diagnostic's sixth feature `neighbours`, `combined` (logistic,
even pairs -> odd pairs), `--nb-tol` what-ifs, "outside the model" on the area line, loop.json's
nb settings read back. Stub only (measured): neighbours rejects 75-86% at levels 0-2 (AUC
0.88-0.92), combined 77-89%; what-if nb1 on the stub loop run: wrong peaks 7.2/4.9/2.6 ->
2.0/2.3/1.3% for 2-6% of the cells, outside-the-model area 6.2 -> 4.2%; stub loop with
--nb-tol 1 (15 fixations): outlier 0.061 -> 0.038, fine 0.087 -> 0.048, fine coverage 0.154 ->
0.150, (y1) 100.000% of 44445 rows; synthetic wall and card: drops 22.8% of 92 wrong (the
card's edge: coherent) and 0.3% of the right. Both rules (offline -> loop; loop win/lose) are
in the note before the run.

## 2026-09-18 — D2b run: the neighbour test; the offline rule not met by either what-if, the loop not run

All measured, host side, nothing rendered. Four self-tests ok. Standard diagnoses
(calib_room_full_sp 18.2 s, class_coverage_full 22.7 s): (y1) 0.0000 / 99.999%, (y2) ok; level,
right-peaks, oracle and uncured lines string-equal to D2a's; area line = D1a's + "outside the
model" 11.2% of 261183 deg2 / 10.5% of 162647 deg2. Telling wrong from right at 90% kept on
class_coverage_full: neighbours 49.0 / 50.4 / 43.6 / 40.0 / 52.7% at levels 0-4, the best
single feature at every level (AUC 0.72 / 0.75 / 0.71 / 0.70 / 0.78), search 62-81% vs window
22-30%; combined 39.9 / 56.0 / 52.0 / 41.4 / 52.6% (AUC 0.72-0.79); isolated 0.4% of the right,
3.3% of the wrong at level 0. What-ifs (20-24 s each, exit 0, (y1) not judged, standard files
untouched): nb1 on class_coverage_full wrong peaks 26.07 -> 17.62, 22.74 -> 15.38, 16.33 ->
12.55% (cuts 32.4 / 32.4 / 23.2%), right peaks kept 98.4 / 98.4 / 98.7%; nb1i 16.87 / 15.22 /
12.50% (cuts 35.3 / 33.1 / 23.4%), kept 98.0 / 98.2 / 98.6%; outside the model 10.5 -> 9.2% of
the judged area, both. Calib room: cuts 16-17% at levels 0-2, kept 96.5-99.4%. Offline rule
(a third at each of levels 0-2, 85% kept): not met by nb1, not met by nb1i (level 1 misses by
0.2 points, level 2 by 10). The loop was not run. Predictions: 1 held (level 2 at 43.6%, under
the 45-65%), 2 failed on the amount (0.4% isolated vs 10-35%), 3 held at levels 1-2 (+5.6,
+8.4 points) and failed at 0, 3, 4, 4 failed, 5 held (the test removes 18% of the window cells
at levels 0-1 and 54% of the search cells). No nanmedian warning; the known
stereo_instrument.py warnings on the loop run. No code change. D2 closes as the note's rule
says; what remains is D4.

## 2026-09-18 — D22: D2 closes; D4 written (the long run, a second look as the test)

After D2b's report (bc7c71d): the neighbour test missed its offline rule (cuts 32.4 / 32.4 /
23.2% at levels 0-2, rule a third; 98% of the right kept), the loop was not run; outside the
model 10.5 -> 9.2% of the judged area, occluded + window 8.2 of it. D22 closes D2; `--nb-tol`
stays, off. D4: `belief.looks` and coverage-first's second phase (least-looked: sum of area /
(1 + fine looks) once the best disc holds under 5% unvisited area) because the long run would
otherwise return candidate 0 for ever after K ~ 130 (self-test with its negative: six distinct
directions, one with the phase disabled); `rho_err_p90` in the metrics; the step records the
phase; `active_eval.py` prints checkpoints for runs over 60 fixations; `tools/second_look.py`
(fine looks per cell, repeatability, agreement, four fusions; (z1), (z2)). Stub only
(measured, sandbox, small, a 20-degree cap so it saturates): least-looked from k = 21, 52
distinct of 60, no lock; coarse 0.336 -> 0.156 and outlier 0.173 -> 0.228 from K = 10 to 70, z RMS
1.02 -> 1.60; second_look on 60 fixations: P(second bad | first bad) 53.5% vs 8.5%, bad-bad pairs
agree 67%, fine gross mean 26.1% / median 23.7% / consensus 17.9% with 4.3% undecided; (z1) 0
cells differ of 31176.

## 2026-09-18 — D4: the run to saturation scheduled (overnight class)

`class_coverage_full_500` (coverage-first, `full`, 500 fixations, κ 3.8, ~13 G rays, predicted
13–15 min) runs now because it is the one record every remaining Phase D step reads
(`second_look.py`, the checkpoint curve, a consensus fusion re-fused from it without rendering),
and it is backed up outside the checkout as a pinned asset.

## 2026-09-18 — D4 run: 500 fixations at full in 12 min; bad looks repeat, consensus beats the mean; (z1) fails on the gate

Measured. The render: 717.7 s wall (choose 88.7 / render 311.1 / infer 239.1 / judge 78.8 s;
medians per fixation 0.191 / 0.623 / 0.463 / 0.159 s), 1.287e10 rays, exit 0, no lock (469
distinct directions of 500, longest repeat 1), least-looked from k = 146; 14 GB, backed up to
/home/lvelho/data/loop4/class_coverage_full_500. Eval (2 min, ok): checkpoints K = 10 / 25 /
50 / 100 / 200 / 300 / 500 — fine coverage 0.021 / 0.048 / 0.094 / 0.171 / 0.230 / 0.266 /
0.295; rho err median 0.0515 / 0.0415 / 0.0423 / 0.0404 / 0.0391 / 0.0386 / 0.0387 (fine 0.0187
at 500); gross 0.384 / 0.332 / 0.345 / 0.344 / 0.337 / 0.336 / 0.336 = coarse 0.296 -> 0.200 +
outlier 0.088 -> 0.136; z RMS 0.77 -> 1.66 (inside (t)'s band); (u) 0.0397 -> 0.0160. (z0): the
50 directions identical to loop3's, the numbers differ in the third-fourth digit (rho err
0.0423 vs 0.0427, gross 0.345 vs 0.344): fixation 0's fix.exr and samples.npz differ in
checksum at the same seed and its field by <= 1e-5 deg in 4 cells — OptiX is not
bit-deterministic; the loop is. second_look (8.6 s, 0.7 GB): P(second bad | first bad) 61.8%
vs P(second bad | first good) 11.3% (at 100: 64.0 / 7.3; at 200: 63.8 / 9.2); agreement
good-good 98.3%, one bad 13.8%, bad-bad 64.4%; fine gross over all fine cells: first look
25.2%, mean 27.9%, median 23.2%, consensus 18.3% with 9.3% undecided (2+ looks: 26.9 -> 14.6%
with 11.5% undecided). (z1) FAIL: 1422 cells (0.4%) hold a fine look that belief.npz has at
best_level 2-3 — all one way, across the cap, cells fused ~200 times from coarse levels whose
single fine look the gate treats as the coarser measurement and drops when it disagrees;
best_level is set only for what passes the gate. Left as it is; the side to change is Chat's.
Views (3.7 min): median |rho err| 0.0919 /m on 3.35 M shared cells, solid on 4.3% of the
sphere, half-confident 9.4% (50 fixations: 1.1 / 5.5%); docs/reference/views_classroom_full_500.png.
Predictions: 1 held (k = 146, 469 distinct), 2 held (0.204 at the switch, 0.295 at 500), 3
failed on the number (0.0387, not 0.025-0.032; saturates above the fine band as said), 4
outlier held (0.136) coarse failed (0.200, not 0.10-0.15), 5 held (62 vs 11%), 6 held on all
looks (34% below the mean, 9.3% undecided). No code change.

## 2026-09-18 — D23, D5 written: the consensus belief (after D4's report, 3c65e49)

`belief.ConsensusBelief` (a subclass; SphereBelief untouched), `consensus_of` shared with
`second_look.py`, `active_loop.py --fusion`, `active_eval.py --refuse` with check (r),
`second_look.py`'s (z1) made one-directional (the gate's drops reported; the first definition
was wrong, as (p) and (u) were before it). Stub only (measured, sandbox, small, 20-degree cap,
70 fixations): re-fused consensus against recorded mean — outlier 0.228 -> 0.175, fine
coverage 0.993 -> 0.946 (undecided 4.7% of the cap), rho error 0.0416 -> 0.0414 (fine 0.0414 ->
0.0397), p90 0.172 -> 0.150, z RMS 1.60 -> 1.54 (not repaired: z is on inliers); (r) exact;
live `--fusion consensus` on the same stub: outlier 0.172, fine coverage 0.946, (s) replay ok;
the default path's 15-fixation stub run reproduces to the digit (0.154 / 0.0478 / 0.359).
Self-tests ok, each new one with a known answer.

## 2026-09-18 — D5 run: the consensus belief re-fused on D4's record; the rule lands in between; Phase D closes

Measured, host side, no render. Self-tests ok. second_look on class_coverage_full_500 exits 0
with the corrected (z1): fine cells here 355601, in belief.npz 354179, missing here 0, gate
dropped 1422 (reported); every other line as in D4. active_eval --refuse consensus on the
500-record (5 min 09 s, 1.73 GB; belief.npz and loop.json untouched; belief_consensus.npz,
refuse_consensus.json, loop_fig_consensus.png written; (r) 2.8e-16; (s)-(u) ok): recorded
checkpoints reproduce D4's; re-fused at K = 10 / 25 / 50 / 100 / 200 / 300 / 500 — fine
coverage 0.021 / 0.048 / 0.094 / 0.167 / 0.209 / 0.239 / 0.263, rho err 0.0517 / 0.0416 /
0.0420 / 0.0398 / 0.0379 / 0.0370 / 0.0365 (fine 0.0151 at 500), outlier 0.088 / 0.095 / 0.103
/ 0.115 / 0.120 / 0.127 / 0.126 (fine 0.212 -> 0.171; mid and coarse unchanged), z RMS 0.77 ->
1.27, undecided of cap 0 -> 0.0322. The 50-record re-fused (29 s): fine outlier 0.214, outlier
0.103, fine coverage 0.094, rho err 0.0424 (fine 0.0165), z 0.97. THE RULE at K = 500, exact:
fine outlier 0.1715 (<= 0.175 met), outlier 0.1257 (<= 0.125 missed by 0.0007), fine coverage
0.2625 (>= 0.265 missed by 0.0025), rho err -5.6% and fine -19% (met); nothing rises, coverage
above 0.250: IN BETWEEN. No live run; --fusion stays mean by default. Views from the
consensus belief (3.7 min): median |rho err| 0.0898 /m (mean's 0.0919), solid 3.6% / half
9.2% of the sphere (4.3 / 9.4); docs/reference/views_classroom_full_500_consensus.png.
Predictions: 1 fine outlier held (0.171), outlier failed by 0.0007; 2 fine coverage failed by
0.0025, undecided held (3.2% of cap, 10.9% of the fine cells); 3 failed on all three (median
-5.6%, fine -19%, p90 -0.3%); 4 failed downward (z RMS 1.66 -> 1.27); 5 failed (in between).
No code change. Phase D closes.

## 2026-09-18 — Phase D closed: the summary

`docs/phase-d-summary.md`, written after a5048b0 from the committed Results of D1a, D2a, D2b,
D4 and D5 and the log. D5's rule landed in between (outlier 0.1257 for 0.125, fine coverage
0.2625 for 0.265); the default fusion stays the mean and the question opens the next phase.
One code change with it: `active_eval.py --refuse` compares against the run's own fusion as
replayed, so a record older than the judge split no longer prints nan on the comparison line.
README's State paragraph rewritten.


<!-- FSG1_HANDOFF_20260919 -->
### 2026-09-19 - FSG1 implementation handoff (applied, not workstation-tested)

Applied to checkout HEAD `84ddf94ca18d71b113091797746549d722da7186`. Chat reviewed public-main interfaces via
web on 2026-09-19; git clone was unavailable in its execution sandbox, so no
upstream commit identity or Blender integration run was claimed there.

23 software checks passed in Chat (NumPy/OpenCV; no bpy). Synthetic small/full
calibration fixtures passed the fixed 90%/1%/3% interior targets after a bounded
photometric refinement addressed SGBM subpixel bias; these are NOT Cycles results.
Implementation and diagnostic history are in `docs/fsg1-single-patch.md`.

Agreed scope recorded from the conversation: oracle instance IDs; fixed head
reference at the eye midpoint; RGB-only inferred geometry; single-patch milestone
first. Defaults and code of Phases C/D are unchanged. Code runs
`docs/fsg1-code-prompt.md`, records measured results, commits and reports. No
surface-growing policy or multi-patch fusion is authorized in this handoff.


### 2026-09-19 - FSG1 small-profile run: passes fronto/tilted, FAILS the step background

Ran `docs/fsg1-code-prompt.md` on the workstation from HEAD `1fbe81c`. Blender
5.2.1 LTS, OPTIX on an RTX 4090; host Python 3.12.3, NumPy 2.2.6, Pillow 12.3.0,
OpenCV 4.13.0 installed fresh from `requirements-fsg.txt` (only OpenCV present,
no existing pin moved).

`[fsg-check] SUMMARY passed=24 failed=0 seconds=1.829 blender_executed=False`,
including the real repository rig integration check. Both deliberate negatives
exit 1 with their geometry FAIL lines (baseline 0.799 m, crop 2.371 m errors).

Real small suite in `previews/fsg1/small-seed17`, 39,321,600 primary samples,
2.1 s of Blender wall; every acquisition.json says `blender_cycles` / `OPTIX`
with `independent_blender_checks: true`, projection error <=8.19e-5 px and
ray-cast error <=7.22e-7 m against limits of 0.002 px and 20 um.

Interior: fronto 98.395% / 0.388% / 1.315%, tilted 99.823% / 0.463% / 1.680% -
both pass. step pools to 94.101% / 0.358% / 2.965%, which also passes, but the
per-instance rule catches the background: instance 2 at 3.4 m gives 99.751%
coverage, 1.136% median and 4.111% p95, missing the 1% and 3% targets. Instance 1
at 1.6 m is 90.361% / 0.187% / 0.792%. `evaluation.json:status` is `FAIL`.

Diagnosed before touching anything, by recomputing truth disparity on the same
core grid: the refinement removes SGBM's pixel-locking bias correctly everywhere
(|median| <= 0.022 px), but its scatter on instance 2 is 0.2185 px against only
11.28 px of disparity at 3.4 m, which is the 1.136%/4.111% arithmetic. A labelled
diagnostic re-render at 1024 spp (`previews/fsg1/diag-small-spp1024-seed17`)
halved that scatter to 0.1089 px and took the case to 0.618%/1.846%, i.e. a pass,
while SGBM's bias stayed at -0.1579 px exactly. Noise, then, not geometry;
texture is ample (instance 2 local std median 8.94, p5 4.05 vs a 0.5 cutoff).
Head-frame geometry independently checks out: step levels Z = -1.5991/-3.3937 m,
fronto -1.999 m, tilted plane normal 25.5 deg from gaze (specified 25).

So this is instrument resolution, not an implementable bug: `small` puts 11.28 px
of disparity on the farthest surface at 64 spp, and the relief - about 1218 px of
rectified focal and 256 spp - lives in the full profile. Per the execution prompt
the full run was NOT started, the matcher was not tuned, and no threshold,
fixture or margin was touched. No code changed. `singly_visible` is 0 reference
pixels in all cases: the foreground half-plane sits on the left, so the half
occlusion belongs to the right eye and is absent from a left-eye reference grid.

Open for Luiz/Chat per D-FSG1: whether `small` is expected to meet a gate written
for the reported configuration, or whether the full profile is the only
configuration the 90/1/3 targets are a statement about.


### 2026-09-19 - FSG1 full-profile follow-up: authorized, prospective entry (written before acquisition)

Per `docs/fsg1-full-profile-followup.md` and the D-FSG1a block appended to
DECISIONS.md just above this entry, one unchanged full-profile suite is authorized
and about to run. Written before the command, so the intent is on record whatever
the outcome:

    blender -b --python-exit-code 1 -P tools/fsg_render.py -- \
      --out previews/fsg1/full-seed17 --profile full --device OPTIX --seed 17 --save-blend
    .venv/bin/python tools/fsg_stereo.py previews/fsg1/full-seed17
    .venv/bin/python tools/fsg_evaluate.py previews/fsg1/full-seed17

Settings are frozen at the 03029a2 baseline: `git diff 03029a2` over the FSG1
executables, rig, bl_common and requirements-fsg.txt is empty. Default 256 spp,
seed 17, no `--spp`, no `--allow-synthetic`, no denoising or adaptive sampling.
Prescription to check against: 640x640 per eye, 256x256 accepted core, three
cases, 629,145,600 primary camera samples. Frozen gate: >=90% coverage, <=1%
median and <=3% p95 relative left-eye range error, per case and per adequately
supported instance, at the existing 8 px full-profile boundary margin.

The small/64-spp suite remains FAIL and its records under
`previews/fsg1/small-seed17` are preserved untouched, as is the 1024-spp
diagnostic. This is one acquisition, not attempts until a seed passes. Full may
fail; that is a reportable outcome and not permission to tune. Logs under
`previews/fsg1/full-followup-logs/`.

Measured outcome, appended after the run. The full suite also FAILS, on a
different criterion from small. `previews/fsg1/full-seed17`, 629,145,600 primary
samples, 640x640 per eye, 256x256 core, spp 256 = recorded default, every case
blender_cycles/OPTIX with complete run.json, projection max 1.577e-4 px and
ray-cast max 7.305e-7 m against 0.002 px and 20 um, IDs matching, 242 rays each.
Render L+R 0.96/0.90/0.99 s, oracle 0.18/0.18/0.27 s, total_wall 4.869 s, whole
process 5.403 s, stereo 0.16/0.12/0.13 s. Software checks reconfirmed first:
passed=24 failed=0; both negatives exit 1 with byte-identical FAIL lines.
`git diff 03029a2` over the FSG1 executables, rig, bl_common and
requirements-fsg.txt was empty, so this is the same estimator.

Interior: fronto 94.786%/0.285%/1.159% PASS, tilted 98.433%/0.318%/1.348% PASS,
step pooled 87.502%/0.268%/1.950%, step inst 1 (1.6 m) 79.319%/0.137%/0.595%,
step inst 2 (3.4 m) 99.819%/0.785%/2.497%. wrong_instance_accepted 0 everywhere.
Evaluator exit 1, status FAIL, full_profile_milestone_pass false:

    [fsg-eval] FAIL step: coverage=0.8750164128151261 fails min 0.9
    [fsg-eval] FAIL step: instance 1: coverage=0.7931872814685315 fails min 0.9

So the predicted effect did happen - instance 2 went 1.136%/4.111% to
0.785%/2.497% and passes, and every median and p95 in the suite is now inside the
gate - but the 1.6 m foreground's coverage, which cleared 90% by 0.36 points at
small, fell to 79.319%. Different instance, different criterion; neither result
supersedes the other.

Cause, measured from stored arrays only (no new code): 99.7% of step instance 1's
7,571 rejected interior pixels fail the fixed `left_gray_std < 0.5` textureless
test; 0.3% fail the 1 px LR residual; none lack raw support. Fronto 98.6% and
tilted 91.5% of rejections are likewise low-texture. The cutoff is absolute while
the texture is magnified: doubling linear resolution halves local contrast in the
fixed 5x5 window. Median std / fraction below cutoff, small -> full: fronto
9.460/1.60% -> 5.056/5.14%; tilted 9.399/0.18% -> 5.109/1.43%; step inst 1
8.325/9.64% -> 4.508/20.63%; step inst 2 8.930/0.00% -> 5.052/0.00%. Step
instance 1's p5 std is 0.000 at both profiles - the fixture's foreground has
genuinely flat patches, resolved as flat once magnified. Not a calibration or
integration defect: head-frame geometry is tighter at full than small (step Z
-1.6002/-3.4001, fronto -1.9995, tilted normal 25.288 deg from gaze vs spec 25).

Correction to the earlier noise reading, per the follow-up's instruction to keep
it qualified: full's accuracy gain is NOT reduced noise. Refined scatter in pixels
GREW at full on every surface (step inst 2 0.2185 -> 0.2920 px, fronto 0.1287 ->
0.2093), for the same weak-gradient reason coverage fell. The gain is geometric -
the rectified focal doubles to 1217.839 px, so the background carries 22.566 px of
disparity instead of 11.283. Equal-cost pair at 629,145,600 samples: the 1024-spp
small diagnostic gives step inst 1 coverage 90.284% and inst 2 0.618%/1.846%;
full gives 79.319% and 0.785%/2.497%. Samples cut scatter (0.2185 -> 0.1089 px)
and barely move the cutoff (9.64% -> 9.72%); resolution buys disparity but halves
per-pixel contrast and costs coverage. This cannot isolate resolution from noise,
support or acceptance, and no efficiency claim follows.

Boundary on step: 4,608 ref px, 51.259% coverage, median 0.605%, p95 3.266%,
5.843% over 3%. Reported, not gated; the interior gate does not validate it.
`singly_visible` is 0 reference pixels in all cases: half-occlusion rejection is
NOT EXERCISED, which is a test-coverage gap, not a pass. A mirrored step or an
opposite-eye reference is Chat's separate additive step before fusion. The suite
was not altered to close it here. Nothing tuned, no threshold/fixture/default
changed, documentation only. Stopped for Luiz/Chat; no fusion or surface growing.


### 2026-09-19 - FSG1b coverage audit: authorized, prospective entry (written before execution)

Per `docs/fsg1-coverage-audit.md` and D-FSG1b appended just above, a read-only
audit of the three already-saved seed-17 records is about to run. Written before
the command so the intent is on record whatever it finds:

    .venv/bin/python tools/fsg_coverage_audit.py \
      previews/fsg1/small-seed17 previews/fsg1/full-seed17 \
      previews/fsg1/diag-small-spp1024-seed17 \
      --out previews/fsg1/coverage-audit-seed17

Zero new primary camera samples: no render, no new seed, no sample-count change,
no matcher/acceptance/gate/fixture/mask change. `git diff 8ac6137` over the FSG1
executables, rig, bl_common and requirements-fsg.txt is empty; environment is
unchanged at Python 3.12.3 / NumPy 2.2.6 / OpenCV 4.13.0 / Pillow 12.3.0, the
same one that produced the records. All 167 files of the three records were
SHA-256 fingerprinted beforehand into
`previews/fsg1/coverage-audit-logs/00-records-before.sha256` so their
preservation can be verified independently of the tool's own checks.

The question: the earlier report's "99.7% fails texture" is not the same claim as
"99.7% fails ONLY texture". The audit splits each fixed reference population into
three disjoint, exhaustive groups - accepted, rejected solely by texture, rejected
for another reason - and scores the texture-only group's already-stored
hypotheses against the unchanged evaluation reference, alongside quantization,
clipping, linear-contrast and angle-matched-support diagnostics.

Expected `AUDIT_COMPLETE_NOT_A_MILESTONE`. Both FSG1 failures stand: small fails
background accuracy, full fails step coverage 87.502% and foreground 79.319%.
A counterfactual without the texture veto is labelled diagnostic and is not
accepted output; nothing is adopted, and no FSG2 work follows. Half-occlusion
stays NOT EXERCISED. Logs under `previews/fsg1/coverage-audit-logs/`.

Measured outcome, appended after the audit. `AUDIT_COMPLETE_NOT_A_MILESTONE`,
3 runs, 2.974 s, diagnostic_only true, fsg1_authorized_pass false,
new_primary_samples 0. FSG1 remains FAIL; both baseline failures are preserved
verbatim inside the audit output. Legacy checks 24/0, new audit checks 29/0, both
deliberate negatives exit 1 ("replay mismatch in valid; no counterfactual
analysis authorized" and "partition overlaps or misses reference pixels").
`replay_exact` true for all nine case-records, every partition exact, original
evaluator metrics reproduced. All 167 record files SHA-256 fingerprinted before
and after: byte-identical, independently of the tool's own inputs_unchanged flag.

The question was whether "99.7% fails texture" means "fails ONLY texture". It
does. full/step instance 1: reference 36,608, accepted 29,037, rejected 7,571, of
which 7,552 fail texture at all and 7,549 fail texture and nothing else; 22 fail
only lr_consistent. Scored against the unchanged reference, those 7,549 discarded
hypotheses are as accurate as the accepted ones - refined median 0.178%, p95
0.889%, none over 3%, against the accepted 0.137%/0.595%. Labelled counterfactual
with the texture veto absent and all other vetoes in force: coverage 79.319% ->
99.940%, median 0.137% -> 0.144%, p95 0.595% -> 0.653%; pooled step 87.502% ->
99.893%. Diagnostic arithmetic on stored hypotheses only - not accepted output,
not a coverage number, not a pass, nothing adopted.

Cause, and it revises the emphasis of the full-profile note: the fixture's
foreground is over-exposed. 100.000% of that cohort has at least one RGB channel
high-clipped and 92.489% has all three; the production conversion clips linear
RGB to [0,1] before quantizing, so saturated neighbourhoods score exactly 0.
Separating the two mechanisms: 51.835% of the cohort is already flat BEFORE
quantization (clipping) and quantization flattens 17.2 points more, to 69.029%.
The unclipped linear luminance score is never zero anywhere - 0.000% at every
record - so the radiance variation is always present and the display conversion
destroys it. Resolution is a real but secondary modulator: the saturated blobs
are a fixed angular size, so the fixed pixel window sits deeper inside them at
full and the zero-score share goes 59.932% -> 69.029% small to full on the same
instance. The earlier "texture halves with resolution" is the median-contrast
statement; true, but not the main mechanism.

Three cautions against reading this as "drop the veto". Raw SGBM on these cohorts
is often degenerate, median equal to p95 to four decimals (0.0992/0.0992 on step
instance 1 at all three records), i.e. one constant disparity propagated across
the saturated region by the smoothness term - correct only because the hidden
surface really is a fronto-parallel plane. About half the cohort (3,678 of 7,549)
has no contrast even in the 9x9 angle-matched window, and the contrast-bearing
half scores 0.162%/0.773% against the whole cohort's 0.178%/0.889%, barely
better - so the accuracy is propagation, not recovered local evidence. And the
veto earns its keep elsewhere: on small/tilted the texture-only hypotheses are
worse, median 1.406%, p95 4.084%, 34.483% of them over 3%, against raw SGBM's
0.127%/1.366%. Interpretations A and D hold, B is not excluded. A fix belongs in
the representation (exposure, or a score computed before the clip) as a separate
prospective experiment evaluated as a NEW candidate against both baselines.

singly_visible reference count is 0 in all nine case-records: NOT EXERCISED at
both profiles and in the diagnostic; a zero denominator is not a pass and the
mirrored/opposite-eye test stays a separate additive step before fusion. boundary
NOT EXERCISED for fronto/tilted, EXERCISED on step only (1,280/395 small,
4,608/2,362 full, 1,280/411 diag1024); still not validated by the interior gate.
Inspected diagnostic.png for full/step, full/fronto and small/step and audit.json
for all nine. No rejected hypothesis was exported, written back or filled. No
render, no new seed, no acceptance change, no code fix needed. Stopped for
Luiz/Chat; no fusion or surface growing.


### 2026-09-19 - FSG1c fixed HDR encoding candidate: authorized, prospective entry (written before execution)

Per `docs/fsg1-hdr-candidate.md` and D-FSG1c appended just above, one opt-in
candidate encoding is about to be compared against the legacy encoder on the
three already-saved seed-17 records. Written before the command:

    .venv/bin/python tools/fsg_hdr_compare.py \
      previews/fsg1/small-seed17 previews/fsg1/full-seed17 \
      previews/fsg1/diag-small-spp1024-seed17 \
      --out previews/fsg1/hdr-candidate-seed17

The candidate is exactly `uint8 = round(255 * sRGB(max(x,0)/(1+max(x,0))))`,
one fixed pointwise function, both eyes, every pixel, no histogram, percentile,
per-eye exposure, gain search or truth. Verified by reading the kernel: it calls
the frozen legacy `linear_to_u8` for the sRGB/quantization step, where that
function's clip is a no-op, so only the pre-transfer compression is new. SGBM and
the original 5x5 texture score see the encoded images; the bounded photometric
refiner still sees ORIGINAL scene-linear float RGB. The 0.5-code-unit cutoff,
windows, search bounds, instance guard, LR check, refinement iterations and every
evaluator rule are unchanged.

This is a NEW instrument candidate, not a cosmetic display edit: it changes the
evidence for initial correspondence as well as acceptance. Zero new primary
camera samples, no render, no seed or spp change, no default adopted.

Known BEFORE running, from `docs/fsg1-hdr-validation.md`: Chat's analytic
bright-full stress (`1.2 + 2*RGB` on both eyes) PASSES at small but FAILS full
coverage - fronto 79.097%, tilted 78.828%, step pooled 86.809%, foreground
85.760%, background 88.388% - with accepted errors inside the limits. The old
clipped encoder accepts zero points in that stress. So avoiding the hard clamp
does not guarantee an 8-bit fixed-window system retains every weak gradient, and
a pass here would still be development-set evidence on records that already
informed the diagnosis. Exit 0 means all requested gates passed, exit 2 a
candidate numerical miss (both valid outcomes), exit 1 an integrity exception
and a stop. Prior failures stand: small misses background accuracy, full misses
step coverage 87.502% / foreground 79.319%. Half-occlusion stays NOT EXERCISED.
All 167 record files fingerprinted beforehand into
`previews/fsg1/hdr-candidate-logs/00-records-before.sha256`.

Measured outcome, appended after the run. Process exit 2 - completed with one
candidate numerical miss, and the miss is the SMALL record's pre-existing
background accuracy failure, not a full-profile miss. Per run:
small CANDIDATE_FAIL_ON_EXISTING_RECORD, **full CANDIDATE_PASS_ON_EXISTING_RECORD
with no fails**, diag1024 CANDIDATE_PASS. Suite flags stay
full_profile_milestone_pass false, fusion_authorized false, adopted_default false,
status CANDIDATE_COMPARISON_COMPLETE_NOT_A_MILESTONE. 5.713 s, 0 new samples.

Integrity: legacy diff vs 64e02af empty before and after; four frozen hashes
pinned by the runtime; legacy_replay_exact and baseline_preserved true for all
nine case-records; input_sha256_before == input_sha256_after over 167 paths, and
I re-fingerprinted the same 167 files myself - byte-identical. Both baselines'
evaluation.json still read status FAIL with two fails each. Checks 24/0, 29/0,
34/0; the three deliberate negatives each exit 1.

full record, legacy -> candidate on the same fixed reference: fronto 94.786% ->
99.019%, tilted 98.433% -> 98.912%, step pooled 87.502% -> 99.445%, step
foreground 79.319% -> 99.361% (median 0.137% -> 0.142%, p95 0.595% -> 0.649%),
step background 99.819% -> 99.572% (0.785% -> 0.796%, 2.497% -> 2.572%).
wrong_instance_accepted 0 for both estimators in all nine. So the full coverage
miss is resolved with every accuracy criterion still met. The small background
miss is essentially unchanged (1.136% -> 1.138% median, 4.111% -> 4.065% p95),
which is correct: that instance had 0.000% clipped pixels, so the encoding has
nothing to recover and its angular-resolution limit stands.

Paired support on the failing instance: common 29,029, gained 7,345, lost 8,
neither 226; 7,335 of the 7,549 old texture-only pixels now accepted (97.2%).
The gain is not resurrection of the old diagnostic hypotheses - the newly
accepted pixels are re-derived from the encoded images and independently score
0.176% median / 0.867% p95 with none over 3%, against those hypotheses' 0.178% /
0.889%; on common support the candidate is marginally better (0.137% -> 0.135%).
Regressions are real and small: full/step background nets -60 pixels, full/tilted
loses 481 while gaining 795, scattered.

The FSG1b counterexample survives and is the sharpest caution. On small/tilted
all 29 old texture-only pixels are now ACCEPTED and as candidate geometry measure
1.914% median / 4.084% p95, far worse than that case's 0.457%/1.667%, consistent
with the audit's 10-of-29 over 3%. They pass only because 29 pixels among 16,384
cannot move an aggregate. n=29, a specific observation and not a population
estimate - direct evidence the candidate admits some weak evidence along with the
clipped-but-good evidence.

Mechanism, stated honestly: the candidate does NOT find more texture. Median
scores roughly HALVE under compression (full/step foreground 4.508 -> 2.708) -
the encoded image has less contrast. What changes is the dead zone: exactly-zero
scores collapse 14.243% -> 0.014% and nothing saturates to 255 in all channels
anywhere. Coverage is recovered by removing hard saturation, not by amplifying
signal. The halving is also the cost: with typical scores about half as large,
the unchanged 0.5 cutoff sits relatively closer to the bulk, and 0.6-0.9% of
full-profile reference pixels now fall below it against 0.000% at small. That is
the regime of Chat's analytic bright-full stress, which still FAILS coverage
under this same encoding (fronto 79.097%, tilted 78.828%, step pooled 86.809%,
foreground 85.760%, background 88.388%). That limitation travels with the result.

Boundary EXERCISED only on step and improves without being gated: full 2,362 ->
2,819 accepted, median 0.604% -> 0.484%, p95 3.266% -> 2.857%. singly_visible is
0 reference pixels in all nine for legacy and candidate alike: NOT_EXERCISED,
unchanged, not a pass. Inspected comparison.png for full/step, full/tilted,
full/fronto, small/tilted and comparison.json for all nine; candidate PLY for
full/step has 63,409 vertices (legacy 55,675), no faces, instance medians Z
-1.6002 and -3.4006 m in fixed H. Remaining holes shown as missing, never filled.

Nothing adopted, no default changed, the legacy encoder remains the instrument.
This is development-set evidence: these records produced the diagnosis and
selected the candidate. Next would be a held-out geometry and seed plus an
additive mirrored-step or opposite-eye half-occlusion fixture BEFORE fusion;
neither is authorized and neither was performed. Stopped for Luiz/Chat.


### 2026-09-19 - FSG1d prospective validation: authorized, prospective entry (written before acquisition)

Per `docs/fsg1-prospective-validation.md` and D-FSG1d appended just above. Two
NEW fixtures on the unchanged instrument, and the schedule is fixed in advance:

    blender -b --python-exit-code 1 -P tools/fsg_validation_render.py -- --out previews/fsg1/validation-small-seed31 --profile small --seed 31 --device OPTIX --save-blend
    .venv/bin/python tools/fsg_validation_eval.py previews/fsg1/validation-small-seed31 --mode smoke --out previews/fsg1/validation-small-evaluation
    blender -b --python-exit-code 1 -P tools/fsg_validation_render.py -- --out previews/fsg1/validation-full-seed31 --profile full --seed 31 --device OPTIX --save-blend
    blender -b --python-exit-code 1 -P tools/fsg_validation_render.py -- --out previews/fsg1/validation-full-seed73 --profile full --seed 73 --device OPTIX --save-blend
    .venv/bin/python tools/fsg_validation_eval.py previews/fsg1/validation-full-seed31 previews/fsg1/validation-full-seed73 --mode full --out previews/fsg1/validation-full-evaluation

Budget, calculated not measured: 26,214,400 + 419,430,400 + 419,430,400 =
865,075,200 primary camera samples. Each entry runs ONCE; no retry, no
replacement seed, no rerender for a favourable sample.

`FSG1c-fixed-soft-hdr-srgb-v1` is frozen. Verified before writing this: the diff
from `edfe1d2` over the fifteen original/audit/candidate modules, rig, bl_common
and requirements-fsg.txt is empty, and `fsg_validation_scene.check_frozen()`
confirms all eight pinned hashes against this checkout. Spec digest
c7f8c67b56c73321315c1b32750fcec36de86af267eaec51433fbfc1730a7299. Read the new
modules directly: Blender-side imports are numpy plus repo modules only (no cv2
or PIL), the CLI has no --spp or --case override, seeds are restricted to (31,73)
with small restricted to 31, and the fixtures match the frozen spec -
tilted_holdout gaze (-12,+8) deg, centre 2.6 m, tilt -32 deg, 3.2x3.2 m; and
step_right with the foreground on +X in [0,1.65] m at Z=-1.8 m against a
background at Z=-3.2 m, reversing the old step's occluding edge.

The question is narrow: does the fixed full-profile sensor keep its accuracy and
coverage on NEW textured planar geometry while refusing a surface only the left
eye can see. Gates are the original ones per case and per instance interior on
each seed: coverage >=90%, median <=1%, p95 <=3%. The new safety criterion is
zero accepted candidate points inside the ground-truth-selected eroded
singly-visible core (full: >=256 raw, >=128 core, 2 px erosion). An empty or
undersized reference is NOT_EXERCISED and is FATAL for step_right, never a pass;
tilted_holdout is expected to report NOT_EXERCISED for that subtest only.

Prior results stand unchanged and are not superseded by anything here: the small
seed-17 background accuracy failure, the full seed-17 baseline coverage failure,
FSG1b's diagnosis, and FSG1c's development-set-only pass together with its two
recorded limitations - the 29-pixel weak-evidence cohort now accepted at
1.914%/4.084%, and the analytic bright-full coverage failure, which these
fixtures' different radiometry does not cancel. Chat has not seen these Cycles
observations; its analytic numbers in
`docs/fsg1-prospective-validation-checks.md` are a software proxy, so this is
prospective simulator validation, not an independent real-world benchmark, and
two Monte Carlo seeds are not two geometries. Outcome unknown at writing; a pass
would be limited evidence for a later decision by Luiz/Chat, and authorizes no
default adoption, milestone closure or fusion here.

Measured outcome, appended after the run. **FROZEN_CANDIDATE_VALIDATION_FAIL.**
Renders exit 0, smoke evaluation exit 2, paired full validation exit 2 - numerical
misses, never an integrity exception. adopted_default, full_profile_milestone_pass,
fusion_authorized and prospective_blender_validation_pass all false.

Integrity: diff from edfe1d2 over the fifteen frozen modules empty before and
after; check_frozen() confirmed all eight pinned hashes; spec digest
c7f8c67b56c73321... echoed by every COMPLETE line and stored in each run.json;
inputs_unchanged true over 32 new paths; predictions_saved_before_truth and
original_interior_gates_unchanged true for all four full case-records; the 295
files of every prior seed-17 record re-hashed byte-identical. Checks 24/29/34/48
all zero failures, py_compile clean, three negatives exit 1 with their intended
wording. Independent Blender checks: projection <=2.353e-4 px, ray-cast
<=7.313e-7 m, 242 rays per case, IDs matching. Mesh, calibration and both
instance masks byte-identical across seeds; only RGB differs (mean |d| 0.000643
tilted, 0.002459 step) - two noise realisations of ONE geometry.

PASSED: tilted_holdout on both seeds, at a gaze (-12,+8), range 2.6 m and tilt
-32 deg the instrument had never seen - candidate 99.763%/0.251%/1.106% (s31) and
99.768%/0.251%/1.092% (s73). The sensor transfers to new planar geometry.
Also passed: step_right foreground at 1.8 m, where the HDR candidate reproduces
its FSG1c benefit PROSPECTIVELY - coverage 96.959% -> 99.868% (s31) and 96.939%
-> 99.904% (s73), gaining 747/758 pixels at 0.166%/0.621% and 0.177%/0.624% with
nothing over 3%; legacy zero-score 1.375% -> candidate 0.000%, median score
6.763 -> 3.382, so again dead-zone removal rather than added contrast.

FAILURE 1 - the 3.2 m background, both seeds, BOTH estimators within 0.006 points
of each other: legacy 1.053%/3.123%, candidate 1.053%/3.123% (s31) and
1.060%/3.127% vs 1.066%/3.127% (s73), with 10.471%/11.097% of accepted pixels over
3%. Not radiometric: that instance has 0.000% zero-score and nothing to unclip.
Not simply angular resolution either - the old full seed-17 background at 3.4 m
had 22.57 px of disparity and PASSED at 0.785%/2.497%, while this one at 3.2 m has
about 23.98 px and FAILS. The measurable difference is texture: median legacy
score 4.430 here against 5.052 there. An observation from two fixtures, not an
established cause; the fixture was not changed to test it.

FAILURE 2 - half-occlusion, which this fixture finally EXERCISES: 4,608 raw and
3,528 core pixels at full (2 px erosion), 1,280/1,008 at small, against required
256/128 and 64/32. tilted_holdout correctly NOT_EXERCISED for that subtest only.
Seed 73: candidate 0 raw / 0 core accepted, legacy 2 raw / 0 core - pass. Seed 31:
BOTH estimators accept 2 core pixels (0.0567%) - FAIL, limit is exactly zero.
Read from saved outputs, the truth there is the background at 3.20 m and the
estimates are geometrically impossible: candidate (83,145) and (84,145) at
Z=-1.8240 m, essentially ON the 1.8 m foreground plane, a 1.377 m (43%) error;
legacy (106,133) and (107,133) at Z=-2.5521/-2.5575 m, a nonexistent intermediate
depth, 0.648/0.643 m error. Every existing veto passed on all four: LR residual
0.148-0.359 px (limit 1.0), texture std 5.5-8.1 (cutoff 0.5), correct oracle
label. These live in the singly-visible population the interior reference
excludes, so no interior metric would ever have seen them - which is exactly why
the separate safety test exists. Two attributions: the leak is NOT the HDR
candidate's (legacy leaks the same two pixels on seed 31, and on seed 73 the
candidate is strictly safer), it is the shared matcher/acceptance; and it is
seed-dependent, so one passing seed would not have demonstrated safety.

Boundary EXERCISED only on step_right: 2,304 ref, 1,261 -> 1,263 accepted at s31
(median 0.318% -> 0.301%, p95 1.071% -> 1.034%), 1,260 -> 1,259 at s73. No
invented threshold; the interior gate does not validate it. wrong_instance 0
everywhere. Candidate PLYs head-frame, no faces: s31 tilted 65,381 (Z med
-2.5458), step 58,590 (26,318 at -1.8006; 32,272 at -3.2007); s73 65,384 and
58,593, same medians. Small record independently: foreground X [+0.010,+0.159],
background X [-0.387,-0.038], tilt 32.5 deg from gaze - built and recovered as
specified. Small seed 31 (a diagnostic, not a gate) also missed on its 3.2 m
background, 94.11%/1.364%/5.613%, and exercised occlusion with 0 core accepted.

Cost: calculated 26,214,400 + 419,430,400 + 419,430,400 = 865,075,200 primary
samples; recorded exactly that. Inference added 0. Blender wall 1.705 / 3.964 /
3.899 s, in-script 1.139 / 3.429 / 3.345 s, smoke evaluation 0.851 s, paired
validation 6.381 s. Batch throughout.

Nothing was tuned: no instrument, encoding, cutoff, window, reference, erosion,
fixture, spp or seed change, and no repeated acquisition. Prior FSG1c limitations
stand (29-pixel weak cohort; analytic bright-full coverage failure), as do all
earlier failures. No default adopted, FSG1 not closed, no fusion. Stopped for
Luiz/Chat.


### 2026-09-19 - FSG1e stage and visibility audit: authorized, prospective entry (written before execution)

Per `docs/fsg1-stage-visibility-audit.md` and D-FSG1e appended just above. A
read-only replay and instrumentation of EXISTING predictions. Zero new camera
samples, no render, no estimator change. The command, written before running it:

    .venv/bin/python -u tools/fsg_failure_audit.py \
      --development previews/fsg1/full-seed17 \
      --development-results previews/fsg1/hdr-candidate-seed17 \
      --validation previews/fsg1/validation-full-seed31 previews/fsg1/validation-full-seed73 \
      --validation-results previews/fsg1/validation-full-evaluation \
      --out previews/fsg1/stage-visibility-audit

The seven full-profile pairs, fourteen instrument-pair combinations: development
`full-seed17` fronto/tilted/step (legacy and HDR candidate), and validation
seeds 31 and 73, `tilted_holdout` and `step_right` (legacy and HDR candidate).

**These validation observations are now DIAGNOSTIC data.** Seeds 31 and 73 have
been inspected in detail here, so they are no longer a fresh holdout for any
future fix; a later candidate needs new validation geometry as well as these
preserved records.

Two open questions, neither assumed: (1) does the failing 3.2 m background have
usable discrete SGBM estimates that the bounded refinement then damages, and do
the error atoms sit on the +/-0.75 px cap - the arithmetic is suggestive, since
with d_true = 23.97619842464091 px an initialization of 24 capped to 23.25 gives
23.97619842464091/23.25 - 1 = 0.03123434084477 against the reported seed-31 p95 of
0.031234338696499123, and 24.75 gives about 3.12647%, but that is a CALCULATION
from calibration and a hypothetical initialization, not a measured cap
population; and (2) for each accepted half-occluded point, is the small LR
residual an average of incompatible right endpoints or a genuinely
self-consistent but wrong correspondence. Both are possibilities. The audit must
confirm or refute, and the regression on the original 3.4 m background matters:
success near an integer disparity cannot justify deleting refinement everywhere.

Preflight verified before writing this: clean main at 3ca52de with d274fac an
ancestor, the instrument diff over the nineteen pinned modules, rig, bl_common
and requirements-fsg.txt empty, all seven input pairs complete, and saved
prediction metadata NumPy 2.2.6 / OpenCV 4.13.0 matching this venv. Exit 0 means
the audit completed with equal replay - never that FSG1 passed. An integrity
exception stops immediately. Outputs without a final audit.json are INCOMPLETE.
All prior failures stand, including FSG1d's FROZEN_CANDIDATE_VALIDATION_FAIL,
the two seed-31 core leaks and the 3.2 m background miss. No default adoption,
milestone closure, gate change, new candidate or fusion follows. Logs under
`previews/fsg1/stage-visibility-logs/`.

Measured outcome, appended after the audit. `AUDIT_COMPLETE_NOT_A_MILESTONE`,
exit 0, 7 pairs / 14 combinations, exact_replay true, inputs_unchanged true,
15.948 s, zero new camera samples. Integrity: instrument diff from d274fac empty
before and after, 11 frozen source hashes verified by the tool, 268 input files
re-hashed byte-identical by me as well, exact_replay / no_acceptance_change /
trace_saved_before_truth true for all 14, prior gate results untouched
(full-seed17 FAIL, FSG1d FROZEN_CANDIDATE_VALIDATION_FAIL). Checks 24/29/34/48/37
with zero failures; three negatives exit 1 with their intended wording.

**Q1/Q2 - the cap explanation is CONFIRMED.** On the failing 3.2 m background the
RAW SGBM estimate is excellent: median 0.099%, p95 0.359%, well inside the gate.
Each refinement update makes it monotonically worse - 0.386/1.650, 0.741/2.886,
1.053/3.123 - and 3,482 of the 3,499 bad pixels were GOOD before refinement
(only 71 went the other way). The true phase is 0.976198, so d_true =
23.976198 px, and SGBM initialises at exactly integer 24 for 90.5% of accepted
background pixels. The top two final-disparity atoms are 23.25 px (1,631 px,
5.05%) and 24.75 px (1,240 px, 3.84%) - exactly 24 -/+ 0.75. The lower-cap
cohort's median relative range error is 0.031234340844770295 against the
predicted 0.03123434084477, the upper-cap cohort's 0.03126471011551888 against
the predicted ~3.12647%, and the reported seed-31 p95 was 0.031234338696499123.
The two caps are ~11% of accepted pixels and ~88% of every pixel over 3%.
Driver: iteration-1 gradient variance median 2.20e-05 with unbounded steps from
-42.19 to +15.86 px - ill-conditioned Gauss-Newton clipped to 0.5/iteration and
accumulating to the 0.75 bound. Tail pixels are 2.9-43x worse conditioned than
the rest of the same surface.

**Q5 - aggregate regularity, noise-selected membership.** Across seeds the
signed-error correlation on that background is only 0.045 (legacy) / 0.048 (hdr),
bad-pixel Jaccard 0.150 / 0.145, 910 of 6,083 union-bad pixels bad in both, and
per-pixel seed differences span -3.91% to +3.85%. The foreground correlates at
0.711 and tilted_holdout at 0.810. So the caps recur in near-identical proportion
but land on different pixels. Two seeds of one geometry prove no independence.

**Q3/Q6 - the regression that forbids simply deleting refinement.** On the
ORIGINAL 3.4 m background the true phase is 0.565833, near half-integer, so the
discrete peak cannot be nearly right: raw median 1.620% would FAIL the 1% gate
on its own, and refinement takes it to 0.785%, a pass, with tail shift median
+0.5232 px toward truth and only 21.78% of its bad pixels at a cap. Same
direction elsewhere: fronto 0.787% -> 0.285%, tilted 0.366% -> 0.318%,
tilted_holdout 0.472% -> 0.258%, step_right foreground 0.729% -> 0.195%.
Refinement helps wherever the true disparity is NOT near an integer and hurts
where it is. A bigger cap or no cap is not the indicated response.

**Q4 - six accepted half-occluded points, and they are NOT one mechanism.** Six
exist across all 14 combinations; every other CSV is empty (not proof of safety).
Four at seed 31 are inside the eroded core (2 legacy, 2 hdr); the two seed-73
legacy rows are raw-strip points outside the core, which is why FSG1d scored
seed 73 a pass. cycle_both_endpoints_pass is False in ALL six while the
interpolated check passes in all six. One is true cancellation - s31/hdr
(337,275): x0 +18.472 and x1 -1.074, NEITHER passing alone, cancelling to +0.148.
Four are endpoint masking: the near endpoint passes (|res| 0.125-0.938) at weight
0.81-0.94 while the far one is 6-18 px wrong. One - s31/legacy (325,299) - has
weight1_ideal 0.0, so the interpolated residual IS the single-endpoint residual
-0.25 px: a genuinely self-consistent cycle that is still wrong by 0.643 m.
Endpoint checking would have caught five of six and NOT the sixth, so it is
insufficient on its own. The ID check passes on all six because the match lands
on another part of the SAME background 6-18 px from the true projection
(right_x_predicted ~294.9 vs right_x_true_surface 300-313); ID-boundary distance
is 3-16 px; right-bin collision count is 1 with margin 0.0 on every row, so that
diagnostic would not have flagged them either. All six ALSO sit at exactly the
-0.75 px cap with unbounded steps -0.33 to -13.72 px - the cap did not cause the
leak, since SGBM's initial peak was already grossly wrong (42.8/30.8/29.9 vs
23.976), but the same conditioning symptom appears in both failures.

Visuals: stage_visibility.png for s31 step_right (legacy and hdr), s73
step_right, full-seed17/step and s31 tilted_holdout. On the new step the raw-error
panel is almost entirely black, update 1 speckles and update 3 is heavily white;
the cap panel is a dense speckle over the same region; accepted-in-core is black
but for one mark at seed 31; "cycle interpolation pass only" clusters along the
occlusion strip. full-seed17/step is the converse - uniformly mid-grey raw
background that update 1 visibly darkens, with an empty occlusion core.

Audit only. Nothing tuned, no candidate, no threshold selected, no script fixed,
no unexpected failure. All prior failures stand. No default adopted, no milestone
closed, no gate changed, no fusion. Seeds 31/73 are now diagnostic data, not a
fresh holdout. Stopped for Luiz/Chat.


### 2026-09-19 - FSG1f one-update supported-reciprocity candidate: authorized, prospective entry (written before execution)

Per `docs/fsg1-supported-candidate.md` and D-FSG1f appended just above. One
opt-in candidate plus TWO PREDEFINED ablation controls, on the seven existing
full-profile pairs. Zero new camera samples, no render. The command, written
before running it:

    .venv/bin/python -u tools/fsg_supported_compare.py \
      --development previews/fsg1/full-seed17 \
      --development-results previews/fsg1/hdr-candidate-seed17 \
      --validation previews/fsg1/validation-full-seed31 previews/fsg1/validation-full-seed73 \
      --validation-results previews/fsg1/validation-full-evaluation \
      --out previews/fsg1/supported-candidate-comparison

Five instruments reported in a fixed order: stored legacy baseline, stored HDR
baseline, fresh one_step_control, endpoint_control, and the named candidate. The
last three share the same new disparity arrays and their supports are nested, so
accuracy changes separate from rejection changes. **The named candidate is fixed
in advance; a control that happens to pass is NOT a fallback and must not be
selected afterwards.**

The candidate is: exactly one original photometric update (`range(3)` ->
`range(1)`, everything inside identical, structurally checked); plus separate
reciprocity at EVERY strictly-positive-weight right contributor (not their
weighted average, no coordinate rounding, exactly-zero-weight neighbours
ignored); plus full 5x5 reciprocal footprint support in the left image and at
every active right contributor. Verified by reading the module before running.
The old interpolated LR check is retained in the intersection - this is an extra
veto, not a relaxed replacement. Encoding, SGBM settings, calibration, the 0.5 px
per-update clip, texture cutoff, reference masks and all numerical gates are
unchanged.

Motivated by FSG1e's measurements: repeated updates damage a near-integer-phase
surface (raw 0.099%/0.359% degraded to 1.053%/3.123%, ~88% of bad pixels at a
cap), while the old 3.4 m background NEEDS refinement (raw 1.620% would fail the
1% gate, final 0.785% passes) - so the old background is a mandatory regression
case and no per-scene update count is permitted. Five of the six known leaks were
interpolation of incompatible endpoints; one was a valid single-endpoint cycle
that was still wrong, which this support rule is NOT guaranteed to catch.

Known before running, from `docs/fsg1-supported-checks.md`: on Chat's ANALYTIC
fixtures the candidate passes, but its seed-31/73 right-step background coverage
is already only ~94.9%, so the two-sided footprint rule's coverage cost is real
and could miss the 90% floor on the actual Cycles records. That cost is charged
against the UNCHANGED reference; reference masks must not shrink to accommodate
it. A coherent wrong disparity field can still pass the support rule - a software
test asserts that limitation deliberately, and zero leaks would be an observed
result, not a theorem.

Preflight verified: clean main at f3eb838 with 7073594 an ancestor, the frozen
diff over the twenty-one instrument modules, rig, bl_common and
requirements-fsg.txt empty, all five input roots and 14 saved predictions
present, environment Python 3.12.3 / NumPy 2.2.6 / OpenCV 4.13.0 / Pillow 12.3.0
matching the saved predictions, and all 268 input files fingerprinted beforehand.

Outcome unknown at writing. A pass on all seven is only
`CANDIDATE_PASS_ON_DIAGNOSTIC_RECORDS` - seeds 17/31/73 have all been inspected
and are development/diagnostic data, so this can never be relabelled prospective
validation; it would at most support proposing a fresh validation later. Exit 2
is a numerical miss (reported, retained); exit 1 is an integrity stop.
`full_profile_milestone_pass`, `adopted_default` and `fusion_authorized` stay
false either way. All prior failures stand. Logs under
`previews/fsg1/supported-candidate-logs/`.

Measured outcome, appended after the run. **CANDIDATE_PASS_ON_DIAGNOSTIC_RECORDS**,
exit 0, candidate_all_gates_pass true, inputs_unchanged true, 7 pairs, 16.625 s,
zero new camera samples. Flags full_profile_milestone_pass / adopted_default /
fusion_authorized all false, development_data_only true.

Integrity: frozen diff from 7073594 empty before and after, five files added and
none modified, environment matching the saved predictions,
exact_legacy_and_hdr_replay / predictions_saved_before_truth /
same_fixed_references true for all seven pairs, 268 input files re-hashed
byte-identical by me as well as by the tool. Checks 24/29/34/48/37/46 with zero
failures; the four negatives exit 1 with their stated causes. No script fixed, no
unexpected exception.

Every NUMERICAL_FAIL line emitted belongs to a stored BASELINE; the named
candidate has none on any pair or instance, and wrong_instance is 0 for all five
instruments everywhere. Candidate per instance (coverage/median/p95):
fronto 99.104/0.098/0.359; tilted 98.892/0.116/0.488; s17 step fg
99.399/0.055/0.220 and bg 99.737/0.333/1.176; s31 tilted_holdout
99.785/0.112/0.448; s31 step_right fg 99.904/0.103/0.293 and bg
94.555/0.383/1.606; s73 tilted_holdout 99.786/0.111/0.447; s73 step_right fg
99.908/0.101/0.293 and bg 94.665/0.382/1.632.

The two failing backgrounds move from 1.053%/3.123% and 1.066%/3.127% to
0.383%/1.606% and 0.382%/1.632%, with the over-3% fraction collapsing from
10.5-11.1% to 0.035% and 0.000%. On COMMON support (32,267 of 33,536 pixels at
seed 31) the median falls 1.053% -> 0.388% and >3% 10.466% -> 0.152%, so the gain
is on the same pixels rather than from a changed support; 3 pixels lost there had
median error 4.10%, the 293 gained sit at 1.03%. First-update shifts reach the
original +/-0.5 per-update clip and no further, so the old +/-0.75 total cap is
unreachable in one update.

**The mandatory regression case does not regress.** FSG1e warned that deleting
refinement would break the older 3.4 m background (near half-integer phase); one
update improves it too, 0.796% -> 0.333% median and 2.572% -> 1.176% p95 with
coverage 99.572% -> 99.737%. One update is the better stage for both the
near-integer and half-integer surface here; no per-scene update count was used.

Cost of the two extra vetoes, concentrated entirely on the occluded step
background: endpoints reject 34 (s31) and 28 (s73) pixels, the footprint rejects
816 and 757, total 2.611% and 2.413% of accepted interior, against 0.171% on
tilted and nothing elsewhere. Coverage there is 94.555% and 94.665%, clearing the
90% floor by about 4.5 points. Boundary is not gated but the reduction is larger
and real: accepted boundary goes 1,279 -> 762 of 2,304 on s31/step_right and
2,885 -> 1,381 of 4,608 on s17/step, i.e. roughly half the boundary population
rejected, while accuracy on what remains improves slightly.

Occlusion: fixed denominators unchanged (4,608 raw / 3,528 core per step_right
seed; NOT_EXERCISED on all three full-seed17 cases and both tilted_holdout
seeds). The candidate accepts 0 raw and 0 core on BOTH seeds, against the legacy
baseline's 2/2 at seed 31 and 2/0 at seed 73 and the HDR baseline's 2/2 at seed
31. occlusion_tracking.csv holds six rows - the union of all previously accepted
locations - and NO new leak appeared; all six are rejected. But the attribution
must stay honest: every row has one_step_valid=False, so the one-step original
validity ALREADY rejects all six before either new veto applies, and also
endpoint_left=False (max active endpoint residual 7.0-43.6 px vs a 1.0 px
tolerance) and footprint_left=False. The rejection is redundant three times over,
so these records do NOT demonstrate that the support rule is what prevents
leakage. Zero leaks is an observed result on two fixtures at two seeds, not a
theorem; the suite deliberately retains a test showing a coherent wrong
reciprocal field can pass the support rule.

Visuals: supported_comparison.png for s31/step_right and s17/step. Identical RGB
across instruments; the baseline's interior-error panel is almost entirely white
across the background while one_step/endpoint/candidate are progressively darker;
the candidate's validity band at the occlusion strip is visibly wider (the
counted footprint cost); the unsafe-accepted-core panel goes from one minute mark
to entirely black. Candidate PLYs head-frame, no faces, correct depths
(s31/step_right 57,536 pts at Z -1.8015 / -3.2007 against the frozen -1.8 / -3.2;
s17/step 62,025 at -1.6004 / -3.4047; fronto 64,949 at -1.9992; tilted_holdout
65,395/65,396 at -2.5464/-2.5460). Holes remain missing; nothing filled or fused.

This is NOT validation: seeds 17/31/73 have all been inspected, so a pass here
cannot be relabelled prospective and at most supports proposing a fresh
validation later. One step is chosen from FSG1e evidence, not proven optimal, and
still uses the ill-conditioned denominator. All prior failures stand unaltered,
including the small-profile misses, the analytic bright-full stress and FSG1d's
FROZEN_CANDIDATE_VALIDATION_FAIL on its own records. Nothing tuned, no control
selected (the named candidate passed, so the question did not arise), no default
adopted, no milestone closed, no fusion. Stopped for Luiz/Chat.


### 2026-09-19 - FSG1g final prospective validation: authorized, prospective entry (written before acquisition)

Per `docs/fsg1-final-validation.md` and D-FSG1g appended just above. The last
planned experiment of Increment 1, on FRESH fixtures and FRESH seeds. Commands,
written before running them:

    blender -b --python-exit-code 1 -P tools/fsg_final_render.py -- --out previews/fsg1/final-small-seed101 --profile small --seed 101 --device OPTIX --save-blend
    .venv/bin/python tools/fsg_final_eval.py previews/fsg1/final-small-seed101 --mode smoke --out previews/fsg1/final-small-evaluation
    blender -b --python-exit-code 1 -P tools/fsg_final_render.py -- --out previews/fsg1/final-full-seed101 --profile full --seed 101 --device OPTIX --save-blend
    blender -b --python-exit-code 1 -P tools/fsg_final_render.py -- --out previews/fsg1/final-full-seed149 --profile full --seed 149 --device OPTIX --save-blend
    .venv/bin/python tools/fsg_final_eval.py previews/fsg1/final-full-seed101 previews/fsg1/final-full-seed149 --mode full --out previews/fsg1/final-full-evaluation

**The frozen candidate is the SIMPLE one: FSG1c soft-HDR encoding, unchanged
SGBM, exactly ONE original photometric update, original validity predicate.
FSG1f's endpoint and footprint vetoes are deliberately NOT used.** Verified by
reading `tools/fsg_final_eval.py` before running: it calls
`fsg_stereo_supported.compute_once()`, never `compute_variants()`, and the
`--negative candidate` control fails if the FSG1f named supported candidate is
substituted. Rationale recorded in D-FSG1g: on the seven diagnostic pairs the
one-step validity already rejected every observed half-occlusion leak before the
extra vetoes acted, while the footprint rule cost ~2.5% interior support on the
occluded background and about half the accepted boundary population.

Six NEW fixtures, none reusing seed-17/31/73 textures: four frontoparallel planes
at target full-profile disparities 22.00, 22.25, 22.50 and 22.75 px - fractional
phases 0, .25, .50, .75, a direct stress of the pixel-locking/refinement phase
effect FSG1e identified - plus two MIRRORED finite-foreground occluders
(occluder_left: fg Z=-1.85 m over bg Z=-3.05 m, fg x in [-1.00,+0.35];
occluder_right: fg Z=-1.95 m over bg Z=-3.15 m, fg x in [-0.35,+1.00]), instances
21/22 and 23/24. The mirrored pair exercises left-reference half-occlusion from
both edge orientations rather than inferring safety from one.

Pass rule, applied separately to EVERY full seed and EVERY instance: interior
coverage >=0.90, median <=1%, p95 <=3%; zero accepted points in each prescribed
eroded singly-visible core; and on each occluder at least 100 accepted
jointly-visible boundary points with median <=1% and p95 <=3%. A zero or
too-small population is NOT_EXERCISED, never an invented pass. The boundary
accuracy gate is new; boundary COMPLETENESS is still not a target.

Calculated primary camera samples, not measured: smoke 6x2x320^2x64 =
78,643,200; each full seed 6x2x640^2x256 = 1,258,291,200; both fulls
2,516,582,400; total 2,595,225,600. Small seed 101 is a smoke/integration run
only - its numerical result is diagnostic and an exit 2 there does not block the
full run, while an exit 1 (provenance/geometry/fixture/software integrity) does.

**No rerender after a numerical miss, no alternative seed or spp, no parameter
search, threshold change, hole filling or estimator adaptation is authorized,
and no control or alternative candidate may be selected after seeing results.**
The two full seeds are two Monte-Carlo realisations of the same six geometries,
not twelve independent scenes.

Preflight verified before writing this: clean main at fd0bad9 with 837acfe an
ancestor; the frozen-instrument diff over the fifteen pinned modules, rig,
bl_common and requirements-fsg.txt empty; six files added by the handoff;
environment Python 3.12.3 / NumPy 2.2.6 / OpenCV 4.13.0 / Pillow 12.3.0 matching
the saved FSG1 records; Blender 5.2.1 LTS on an RTX 4090; all five output paths
absent. `[fsg-final-scene] PASS cases=6 phases=4 mirrored_occluders=2`,
`[fsg-final-check] SUMMARY passed=7 failed=0`, and the six regression suites at
24/29/34/48/37/46 with zero failures. The three negatives each exit 1: deliberate
phase mutation detected, deliberate bad boundary detected, deliberate candidate
substitution detected.

Outcome unknown at writing. If every prescribed full gate passes on both seeds,
Increment 1 / FSG1 closes, this one-update instrument is recorded as the FSG1
local RGB-D instrument, and Increment 2 (two overlapping patches in the fixed
head-centred map) is AUTHORIZED BUT NOT IMPLEMENTED in this run. If any full gate
misses, the failure is preserved and I stop for Luiz/Chat without inventing a new
candidate. A pass closes only the single local RGB-D patch instrument milestone
under controlled calibration conditions - it claims nothing about fusion,
exploration, complete boundaries, thin structure, arbitrary scenes or calibrated
uncertainty. Logs under `previews/fsg1/final-validation-logs/`.

Measured outcome, appended after the run. **STOPPED at the smoke stage with an
integrity failure; the two full acquisitions were NOT run. FSG1 / Increment 1 is
NOT closed and Increment 2 is NOT authorized.**

    [fsg-final] FAIL ValueError: half-occlusion NOT_EXERCISED: raw

Smoke evaluation exit 1. Per section 5.2 an exit 1 for fixture/geometry integrity
blocks the full run, and section 2 states that a fixture failing to create a
substantial singly-visible population is an integrity/test-design failure, not a
numerical pass. This is NOT a numerical miss by the candidate - the candidate was
never tested on half-occlusion, because the fixtures present none inside the
accepted measurement.

The defect, measured not assumed. Both occluders put their nearest foreground
edge outside the accepted core: occluder_left fg Z=-1.85 m with x in
[-1.00,+0.35], nearest edge |x|=0.35 m at **10.713 deg** off axis;
occluder_right fg Z=-1.95 m with x in [-0.35,+1.00], nearest edge **10.176 deg**.
The accepted core spans CORE_FOV_DEG=12, i.e. **+/-6.000 deg at BOTH profiles** -
atan(64/608.9193) = atan(128/1217.8387) = 6.0000 deg, since small and full differ
in resolution, not field. Core half-width at those depths is 0.1944 m and
0.2050 m against a 0.35 m edge. The rendered masks confirm it: the padded 320x320
raster does contain both instances (21:88,320 / 22:14,080 and 31:86,080 /
32:16,320) but the accepted 128x128 core contains ONLY foreground (21:16,384 and
31:16,384), so the edge lives entirely in the search/rectification margin. Truth
on the rectified core therefore has a single instance and singly_visible = 0 raw
/ 0 core, against a required 64/32 at small and 256/128 at full. The
occluder_left cloud written before the stop is 16,384 points, all instance 21,
median Z = -1.8526 m - the foreground alone.

Profile-independent, so the full run would reproduce it exactly: the two full
acquisitions would have spent 2,516,582,400 primary camera samples to re-derive a
known fixture defect. For contrast FSG1d's step_right worked (4,608 raw / 3,528
core at full) because its edge sat at x=0, on the optical axis; the FSG1g
occluders are finite rectangles with BOTH edges outside the core, so neither
orientation of the mirrored pair is exercised. Correcting this means moving a
fixture edge inside +/-6 deg of the gaze - a geometry change, which section 5.1
explicitly does not delegate. Nothing was altered: no scene, gate, seed, spp,
encoding, iteration count, matcher setting, erosion radius, reference mask or
candidate.

What the smoke did establish. Four of six fixtures are exactly as frozen -
measured truth disparities scaled to full are 22.00000 / 22.25000 / 22.50000 /
22.75000 px, phases 0.0000 / 0.2500 / 0.5000 / 0.7500. Their smoke interior
results (diagnostic, small profile): phase_00 100.000%/0.1663%/0.5604%, phase_25
100.000%/0.3211%/0.7792%, phase_50 100.000%/0.4676%/0.9948%, phase_75
100.000%/0.5912%/1.1996% - all inside the gates at full coverage, with error
rising monotonically with distance from an integer disparity, i.e. the FSG1e
phase mechanism reappearing in a fresh fixture under the one-update instrument at
a magnitude that stays well within targets. Caveat: at small the disparities are
halved, so these exercise phases 0/.125/.25/.375, NOT the frozen 0/.25/.50/.75 -
the intended phase stress only happens at full, which was not run. Point clouds
head-frame, no faces, no fill: median Z -3.4830 / -3.4377 / -3.3942 / -3.3526 m.

Everything else was clean. Frozen-instrument diff from 837acfe empty before and
after; six files added by the handoff, none modified; environment Python 3.12.3 /
NumPy 2.2.6 / OpenCV 4.13.0 / Pillow 12.3.0; Blender 5.2.1 LTS on OPTIX.
`[fsg-final-scene] PASS cases=6 phases=4 mirrored_occluders=2`,
`[fsg-final-check] SUMMARY passed=7 failed=0`, regression suites
24/29/34/48/37/46 with zero failures, and the three negatives each exit 1
(deliberate phase mutation / bad boundary / candidate substitution detected - the
last confirming the validator uses compute_once, not the FSG1f named candidate,
which I also verified by reading fsg_final_eval.py before running). The small
render itself succeeded: exit 0, six [fsg-render] lines, COMPLETE markers,
spec=cb9da6a2fc70..., 78,643,200 primary samples, 3.629 s Blender wall. Inspected
phase_50/validation.png (textured RGB, fully white validity, dark interior error,
correctly empty boundary/occlusion panels) and a direct occluder_left full-raster
mask vs accepted core comparison showing the background strip only at the raster
margin and an edgeless core. Only four validation.png exist; the two occluder
sheets were never written because of the stop.

No full-stage validation.json exists. FSG1 / Increment 1 remains OPEN, Increment
2 NOT authorized, no default adopted, no milestone closed, no fusion, no new
candidate invented. All earlier failures stand. The fixture correction is Chat's
and Luiz's call; the numbers above say exactly what must move and by how much.


### 2026-09-19 - FSG1h corrected final validation: authorized, prospective entry (written before acquisition)

Per `docs/fsg1h-final-validation.md` and D-FSG1h appended just above. FSG1g's
stereo instrument is UNCHANGED; only the two occluder foreground x extents are
corrected. Commands, written before running them:

    blender -b --python-exit-code 1 -P tools/fsg_finalh_render.py -- --out previews/fsg1/finalh-small-seed101 --profile small --seed 101 --device OPTIX --save-blend
    .venv/bin/python tools/fsg_finalh_eval.py previews/fsg1/finalh-small-seed101 --mode smoke --out previews/fsg1/finalh-small-evaluation
    blender -b --python-exit-code 1 -P tools/fsg_finalh_render.py -- --out previews/fsg1/finalh-full-seed101 --profile full --seed 101 --device OPTIX --save-blend
    blender -b --python-exit-code 1 -P tools/fsg_finalh_render.py -- --out previews/fsg1/finalh-full-seed149 --profile full --seed 149 --device OPTIX --save-blend
    .venv/bin/python tools/fsg_finalh_eval.py previews/fsg1/finalh-full-seed101 previews/fsg1/finalh-full-seed149 --mode full --out previews/fsg1/finalh-full-evaluation

**Candidate unchanged and verified by reading `tools/fsg_finalh_eval.py` before
running: it calls `fsg_stereo_supported.compute_once()`, never
`compute_variants()`.** FSG1c soft-HDR encoding, unchanged SGBM, exactly ONE
original photometric update, original validity predicate. No endpoint or
footprint support vetoes.

The correction, verified against FSG1g's module: occluder_left foreground x
[-1.00,+0.35] -> [-0.16,+0.10] m, occluder_right [-0.35,+1.00] -> [-0.10,+0.16] m.
All four corrected edges now lie 2.936-4.943 deg off the gaze axis, inside the
+/-6.000 deg accepted core (core half-width 0.1944 m at 1.85 m and 0.2050 m at
1.95 m). Foreground/background depths (-1.85/-3.05 and -1.95/-3.15 m), instance
IDs, phase targets (22.00/22.25/22.50/22.75 px), textures, seeds (101/149),
profile, spp and every gate are unchanged.

Pre-render fixture proof, computed with the evaluator's own `ground_reference`
and `eroded_core`: raw singly-visible 1024/1024/4096/3840 and boundary
1920/1792/6912/6656 and interiors 9600/3840, 9088/4480, 39424/15104, 37120/17920
for small-left/small-right/full-left/full-right - all matching the handoff table
EXACTLY. The eroded cores measure 756/756/3024/2772 against a handoff table
saying 768/768/3072/2816. **Diagnosed before rendering: the handoff's expected
core column was computed as (w-2r)*h, eroding only horizontally, while cv2.erode
erodes both axes giving (w-2r)*(h-2r); both formulas reproduce their respective
numbers exactly in all four rows.** The strips are 8x128 (small) and 16x256 /
15x256 (full). So the geometry is exactly as intended and only the document's
arithmetic for that one column is wrong; the actual cores exceed the required
minima (32 small, 128 full) by 21.7-23.6x, and the shipped check gates on those
minima and passes. Not a fixture-integrity failure; nothing was altered.

`[fsg-finalh-scene] PASS cases=6 phases=4 corrected_finite_occluders=2` and
`[fsg-finalh-check] SUMMARY passed=8 failed=0 occluder_reference_checks=4`. All
four negatives exit 1, including the FSG1g regression: "deliberate off-core
occluder detected: singly-visible reference is empty" - proving the new check
would have caught the original defect. Existing suites 24/29/34/48/37/46/7 with
zero failures. Environment Python 3.12.3 / NumPy 2.2.6 / OpenCV 4.13.0 / Pillow
12.3.0, Blender 5.2.1 LTS on an RTX 4090; frozen-instrument diff from 7408e03
empty; six files added; FSG1g records preserved and not overwritten.

Calculated primary camera samples, not measured: smoke 78,643,200; each full seed
1,258,291,200; total 2,595,225,600 if all stages run. No rerender after a
numerical miss, no alternative seed or spp, no tuning, no support veto, no
threshold change, no hole filling. Outcome unknown at writing. If every
prescribed full gate passes on both seeds, FSG1 / Increment 1 closes, the
one-update instrument is recorded as the FSG1 local RGB-D instrument, and
Increment 2 is AUTHORIZED BUT NOT IMPLEMENTED. Otherwise the failure is preserved
and I stop for Luiz/Chat. Logs under `previews/fsg1/finalh-logs/`.

Measured outcome, appended after the run. **FSG1H_FINAL_VALIDATION_PASS.** Every
prescribed full gate passes on both fresh seeds, no numerical FAIL line anywhere,
zero accepted half-occlusion core points, zero wrong-instance acceptances.
all_gates_pass / prospective_blender_validation_pass / full_profile_milestone_pass
/ increment1_complete / increment2_authorized / adopted_as_fsg1_instrument all
true. 2,516,582,400 acquisition primary samples, 0 added by inference, evaluation
8.197 s.

**FSG1 / Increment 1 is CLOSED. The candidate
FSG1-HDR-SGBM-one-original-update-original-validity-v1 is recorded as the FSG1
local RGB-D instrument. Increment 2 is AUTHORIZED BUT NOT IMPLEMENTED** - no
fusion, surface map, saccade policy or multi-patch code was written.

Fixture proof before rendering: raw 1024/1024/4096/3840, boundary
1920/1792/6912/6656 and interiors 9600/3840, 9088/4480, 39424/15104, 37120/17920
match the handoff table EXACTLY. Cores measured 756/756/3024/2772 against a table
saying 768/768/3072/2816 - diagnosed before rendering as the table computing
(w-2r)*h, eroding only horizontally, where cv2.erode does (w-2r)*(h-2r); both
formulas reproduce their numbers exactly on strips of 8x128 (small) and 16x256 /
15x256 (full). Geometry exactly as intended, only that documentation column
wrong, and the real cores exceed the required minima by 21.7-23.6x. Nothing
altered. All four negatives exit 1, including the FSG1g regression "deliberate
off-core occluder detected: singly-visible reference is empty", proving the new
check would have caught the original defect. Existing suites 24/29/34/48/37/46/7.

Phase planes, both seeds, with the fixture verified (measured truth disparities
22.00000/22.25000/22.50000/22.75000 px at phases 0/.25/.50/.75): seed 101
99.965%/0.0849%/0.2844%, 99.886%/0.0973%/0.3655%, 99.940%/0.2209%/0.9252%,
99.774%/0.1293%/0.4091%; seed 149 99.963%/0.0852%/0.2863%, 99.890%/0.0967%/
0.3607%, 99.936%/0.2255%/0.9587%, 99.765%/0.1297%/0.4128%. The half-integer phase
is hardest, as FSG1e predicted, but at about a fifth of the median budget.

Occluder interiors: foreground instances 100.000% coverage on every seed and both
orientations (0.1360-0.2411% median, 0.3819-0.5460% p95); occluded backgrounds
93.287% / 95.128% (seed 101) and 93.167% / 95.190% (seed 149) with medians
0.3549-0.4046% and p95 1.3736-1.6378%. Those backgrounds are the tightest margin
in the suite - 3-5 points of coverage headroom above the 90% floor.

Half-occlusion, the test FSG1d first exercised and FSG1g could not: raw reference
4096/3840 and core 3024/2772 per occluder per seed, and **0 accepted raw and 0
accepted core in all four occluder-seed combinations** - not one of 11,592 core
points. Boundary accuracy gate: 4,041 / 3,973 / 4,044 / 3,980 accepted points
(58.5-59.8% descriptive coverage) with medians 0.2222-0.3302% and p95
1.4432-2.0518%, all PASS against 100 points / 1% / 3%. About 40% of boundary
reference stays unaccepted and remains missing; no interpolation or fill.

Point clouds head-frame, no faces, no fill, on the frozen geometry:
occluder_left 57,555/57,540 points at Z -1.8460 (spec -1.85) and -3.0494/-3.0506
(spec -3.05); occluder_right 58,140/58,158 at -1.9476 (spec -1.95) and
-3.1490/-3.1488 (spec -3.15); phase planes 65,382-65,513 at -3.4888/-3.4468/
-3.4080/-3.3759 m. Inspected all six small sheets before the full stage and the
full occluder sheets after: both crops now show a finite foreground rectangle
with BOTH depth edges inside the core, mirrored between cases; occlusion-core
panels non-empty; unsafe-accepted-core panels entirely black; missing panels show
excluded strips rather than filling them.

Small smoke missed two gates diagnostically (occluder_left instance 22 coverage
87.031%, boundary p95 3.306%) - exit 2, which section 5.2 says does not block
full - and both cleared at full (93.287%, 2.045%), consistent with the resolution
dependence seen throughout FSG1. No rerender, seed change, spp change, tuning,
support veto, threshold change or hole filling at any point. Timings: small
render 3.637 s, full seed 101 10.101 s, full seed 149 10.056 s, full evaluation
8.313 s wall.

Scope of the close: one local RGB-D patch instrument validated prospectively on
fixtures and seeds it had never seen, against gates frozen before the data
existed - four disparity phases spanning the pixel-locking mode that broke FSG1d,
and two mirrored finite occluders exercising left-reference half-occlusion from
both orientations with zero unsafe acceptances. It remains a controlled opaque,
diffuse, planar suite with oracle instance segmentation, known fixed cameras and
two MC seeds of the same six geometries. It does NOT establish arbitrary-scene
stereo, complete boundary coverage, thin-structure performance, calibrated
uncertainty or multi-patch reconstruction. Earlier limitations stand: the
small-profile misses, the analytic bright-full stress, and the FSG1c/FSG1f
development-set caveats. Stopped for Luiz/Chat.


### 2026-09-19 - FSG2 Increment 2, two-patch fusion: authorized, prospective entry (written before acquisition)

Per `docs/fsg2-increment2.md` and D-FSG2a appended just above. The first step of
Increment 2, authorized by D-FSG1h's close of Increment 1. Commands, written
before running them:

    blender -b --python-exit-code 1 -P tools/fsg2_render.py -- --out previews/fsg2/two-patch-small-seed211 --profile small --seed 211 --device OPTIX --save-blend
    .venv/bin/python tools/fsg2_eval.py previews/fsg2/two-patch-small-seed211 --mode smoke --out previews/fsg2/two-patch-small-evaluation
    blender -b --python-exit-code 1 -P tools/fsg2_render.py -- --out previews/fsg2/two-patch-full-seed211 --profile full --seed 211 --device OPTIX --save-blend
    .venv/bin/python tools/fsg2_eval.py previews/fsg2/two-patch-full-seed211 --mode full --out previews/fsg2/two-patch-full-evaluation

**The FSG1 instrument is frozen and unchanged.** Verified by reading
`tools/fsg2_eval.py` before running: it imports `compute_once` and
`check_kernel_equivalence` from `fsg_stereo_supported`, never `compute_variants`.
The `git diff 4637961` over the fifteen pinned FSG1 modules, rig, bl_common and
requirements-fsg.txt is empty. This step adds only scene, fusion, render and
evaluation code; it changes no part of the validated instrument.

What is being tested, and only this: whether two independently reconstructed
local patches accumulate into ONE persistent surface in the fixed head frame.
No active frontier selection, ICP or any pose estimation (the calibrated
head/eye transforms are exact inputs), no learned fusion, no meshing, no hole
filling, no multi-object switching.

Frozen geometry and parameters, read from `fsg2_scene.SPEC`: two fixations at
yaw -3 deg (`fix_left`) and +3 deg (`fix_right`), pitch 0, default 2 m vergence;
one finite tilted object ID 61 centred at (0, 0, -2.05) m, 0.68 x 0.48 m, tilted
12 deg; background plane ID 62 at Z = -3.4 m; **only ID 61 enters the surface
map**; seed 211; spp 64 small / 256 full; association radius 12 mm, hash cell
12 mm, truth-cover radius 15 mm, truth grid 170 x 120.

Map model: patch A initializes one surfel per accepted object point; patch B
associates ONLY against the snapshot of A by same object ID and Euclidean
distance <= 12 mm; matched surfels average with their B observations and record
two-patch support; unmatched B observations extend the map; samples within B are
never collapsed with one another; replaying the same patch ID must leave the map
byte-identical. This is an engineering baseline, not a claim that Euclidean
nearest-neighbour fusion is a final surface model.

Prospective gates, all fixed before execution: per patch, eroded object-reference
coverage >= 90%. Overlap/fusion: >= 5,000 B points associated to A; >= 15% of B
points remain new; matched A/B distance median <= 10 mm and p95 <= 25 mm;
fused-map point-to-true-plane median <= 10 mm and p95 <= 30 mm; fixed
object-surface grid coverage after fusion >= 70%; fusion raises that grid
coverage by >= 12 percentage points over patch A alone; replaying patch B is
idempotent. The truth grid and plane are evaluation-only, and the RGB-derived
patches and fused map are written BEFORE those geometry metrics are computed.

Preflight verified before writing this: clean main at bd67270 with 4637961 an
ancestor; seven files added; environment Python 3.12.3 / NumPy 2.2.6 / OpenCV
4.13.0 / Pillow 12.3.0, Blender 5.2.1 LTS on an RTX 4090; `previews/fsg2` absent.
`[fsg2-scene] PASS cases=2 object=61 overlap_prescribed=true`,
`[fsg2-map] PASS matched=658 new=842 idempotent=true`,
`[fsg2-check] SUMMARY passed=4 failed=0`, and the three negatives each exit 1
(5 cm shift collapses overlap; wrong-instance patch detected; duplicate patch
refused to alter the map). All eight FSG1 regression suites pass:
24/29/34/48/37/46/7/8.

ONE full acquisition only, at seed 211. No rerender, seed change, spp change,
threshold change, association-radius change or instrument change after seeing a
numerical miss. A numerical miss at small is diagnostic and does not change the
full gates; an integrity failure, geometry mismatch, non-idempotence or wrong
instrument wiring stops the step. Outcome unknown at writing: a full pass
authorizes Increment 3 (automatic single-object frontier growth) but must NOT
implement it; any full miss is preserved and returned to Luiz/Chat. Logs under
`previews/fsg2/logs/`.

Measured outcome, appended after the run. **FSG2_INCREMENT2_PASS** on the single
prescribed full seed-211 acquisition, exit 0, empty fails list. **Increment 3
(automatic single-object frontier growth) is AUTHORIZED BUT NOT IMPLEMENTED** -
no frontier selection, policy, ICP, meshing or hole filling was written.

Integrity: FSG1 frozen-instrument diff from 4637961 empty; seven files added,
none modified; instrument wiring read before running (compute_once +
check_kernel_equivalence, never compute_variants) and both runs report
instrument FSG1-HDR-SGBM-one-original-update-original-validity-v1;
prediction_manifest truth_opened=false in both, so patches and the fused map were
written before any geometry metric. Scene/map/self-test PASS with
matched=658 new=842 idempotent=true and SUMMARY passed=4 failed=0; the three
negatives each exit 1 (5 cm shift collapses overlap, wrong-instance detected,
duplicate replay refused). All eight FSG1 regression suites pass: 24/29/34/48/
37/46/7/8.

Full seed 211, every gate: patch coverage fix_left 99.132% and fix_right
100.000% (>=90%); 32,222 B points matched (>=5,000); 50.833% of B remains new
(>=15%); matched A/B distance median 1.907 mm and p95 6.187 mm (<=10 / <=25);
fused point-to-true-plane median 3.548 mm and p95 9.740 mm (<=10 / <=30);
fixed-grid coverage 90.225% (>=70%); gain 30.485 pp over patch A alone (>=12);
idempotent replay true. Patch points 58,627 and 65,536. The fused map holds
91,941 surfels of which 16,860 carry two-look support and 75,081 one look -
consistent with 32,222 matches collapsing to 16,860 fused surfels plus 33,314 new
B points extending the surface. Fixed-grid coverage rises 59.740% -> 90.225%.
Only ID 61 in the map (91,941 points) and in both patch NPZs; background 62
absent. No numerical FAIL line at full.

Small smoke was FSG2_INCREMENT2_FAIL, exit 2, on exactly two gates - fused plane
error median 13.837 mm and p95 34.370 mm - with every other gate passing
(coverage 97.474%/100.000%, matched 7,950, new 51.477%, overlap 3.812/8.330 mm,
grid 85.005% with 30.363 pp gain, idempotent, no background ID). Per the handoff
a small miss is diagnostic and does not alter the full gates; integrity,
geometry, idempotence and wiring were sound, so full proceeded. Both cleared at
full (13.837 -> 3.548 mm, 34.370 -> 9.740 mm, about 3.9x and 3.5x), consistent
with the resolution dependence measured throughout FSG1. Nothing tuned,
rerendered or re-seeded; no code fix was needed.

Visuals: fusion.png at both profiles shows fix A covering the left of the object,
fix B the right, and a fused panel visibly wider than either with a distinctly
darker central band - the 16,860 two-look surfels - flanked by lighter one-look
wings. surface_map.ply carries "comment fixed head frame H", 91,941 vertices, no
faces, and a per-vertex support property with values exactly {1: 75,081,
2: 16,860}. Head-frame geometry matches the fixture: Z median -2.0497 m against
the prescribed -2.05, spans 0.621 x 0.444 m against a 0.68 x 0.48 m object.
Missing regions stay missing - no meshing, fill or interpolation, and no
registration was estimated.

Cost: smoke 26,214,400 and full 419,430,400 primary camera samples. Smoke render
1.717 s, full render 3.966 s (0.930 / 1.008 s per fixation), full evaluation
37.539 s wall.

Scope of the pass: two prescribed overlapping foveal RGB-D patches from the
frozen FSG1 instrument accumulate into one persistent surface in the fixed head
frame, extending coverage 59.7% -> 90.2% while holding plane accuracy at 3.5 mm
median, with exact calibrated poses and no registration. It is one finite planar
tilted object under oracle segmentation, two fixations 3 deg apart, one seed, and
a 12 mm Euclidean nearest-neighbour rule fixed in advance - an engineering
baseline, not a final surface model. Same-object folds and self-occlusions are
deferred, surfel normals unused, the proximity rule is not a calibrated
uncertainty model, and the completeness grid samples only this known finite
object. Nothing here speaks to active frontier selection, multi-object switching
or uncontrolled scenes. Stopped for Luiz/Chat.


### 2026-09-19 - FSG3 Increment 3, active frontier growth: authorized, prospective entry (written before acquisition)

Per `docs/fsg3-increment3.md` and D-FSG3a appended just above. Increment 3,
authorized by D-FSG2a's close of Increment 2. Commands, written before running:

    .venv/bin/python -u tools/fsg3_loop.py --repo . --out previews/fsg3/active-small-seed307 --profile small --seed 307 --device OPTIX
    .venv/bin/python tools/fsg3_eval.py previews/fsg3/active-small-seed307 --mode smoke --out previews/fsg3/active-small-evaluation
    .venv/bin/python -u tools/fsg3_loop.py --repo . --out previews/fsg3/active-full-seed307 --profile full --seed 307 --device OPTIX
    .venv/bin/python tools/fsg3_eval.py previews/fsg3/active-full-seed307 --mode full --out previews/fsg3/active-full-evaluation

**What changes in this increment is ONLY the choice and stopping of fixations.**
No policy comparison, no learned policy, no pose estimation, no ICP, no
meshing/filling, no object switching, no folds, no head motion, no vergence
control - vergence is fixed at the prescribed 2.10 m and only gaze direction is
active.

**The policy decides the trajectory; I do not.** After each fixation it measures
whether object ID 71 reaches the left/right edge band of the current core,
computes robust 1%/99% head-yaw extents from the RECONSTRUCTED map only,
considers just the two candidates at current yaw +/- 5 deg, requires an edge
where the object continues, >= 4 deg map overlap, yaw within the frozen
[-12,+18] range and no revisit, scores by predicted new angular support, and
stops when no candidate predicts >= 1 deg. The document's "approximately five
looks at -7, -2, +3, +8, +13 deg" is a design expectation and explicitly NOT an
execution gate; whatever trajectory the policy produces is what I report.

Frozen and unchanged: FSG1 instrument
`FSG1-HDR-SGBM-one-original-update-original-validity-v1`; oracle segmentation
with only ID 71 entering the map (background 72 excluded); fixed head frame H;
exact calibrated poses, no registration; 12 mm association radius and hash cell;
SPP 64 small / 256 full; master seed 307 with a deterministic distinct L/R Cycles
seed per step. Verified by reading the code before running: `fsg3_loop.py` and
`fsg3_policy.py` import NO fixture geometry and touch no `evaluation_only` asset
- only `fsg3_eval.py` does - and the loop calls `compute_once` with
`check_kernel_equivalence`, never `compute_variants`.

Prospective gates, all fixed in advance. Loop: 4-6 fixations including the seed;
termination reason must be `no_frontier`, not budget exhaustion; every saccade
nonzero and <= 5 deg; no repeat. Per patch: oracle-object measurement coverage
>= 90%. Every non-seed overlap: >= 5,000 points associate, median <= 10 mm,
p95 <= 25 mm, duplicate replay exactly idempotent. Extension: >= 15% of points
new on every NONTERMINAL added patch, >= 5% on the TERMINAL boundary-closing
patch - an asymmetric rule fixed prospectively because the last placement is
expected to re-see reconstructed surface plus only the remaining strip.
Persistent surface on the fixed evaluation-only grid: final coverage >= 90%;
>= 35 pp improvement over the seed patch; every nonterminal post-seed fixation
>= 10 pp; the terminal one >= 2 pp; no step may lose more than 0.5 pp; final
point-to-plane median <= 10 mm and p95 <= 30 mm; every map point ID 71.

Preflight verified: clean main at 8e4bcb2 with 7b8d39b an ancestor; the FSG1/FSG2
frozen diff over the nineteen pinned modules empty; ten files added; environment
Python 3.12.3 / NumPy 2.2.6 / OpenCV 4.13.0 / Pillow 12.3.0, Blender 5.2.1 LTS on
an RTX 4090; `previews/fsg3` absent.
`[fsg3-scene] PASS angular_span=[-10.075,15.190] seed=-7.0 five_looks_reach=true`,
`[fsg3-map] PASS B=552/648 C=504/696 idempotent=true`,
`[fsg3-policy] PASS map_state_changes_direction=true resolved_frontier_stops=true`,
`[fsg3-check] SUMMARY passed=5 failed=0`. All four negatives exit 1 (hard-coded
frontier direction, failure to stop at a resolved boundary, 5 cm registration
error, duplicate replay). All nine FSG1/FSG2 regression suites pass:
24/29/34/48/37/46/7/8/4.

ONE full active run only, seed 307. The number of rendered fixations is the
policy's decision, not mine after seeing results. No rerender, new seed,
threshold change, scene change, step change, association-radius change,
instrument change or manual gaze edit after a numerical miss. A small-profile
numerical miss is diagnostic; integrity failure, wrong instrument, truth leakage,
repeated fixation, renderer failure, invalid object ID, non-idempotent map or a
policy/runtime bug violating the written algorithm stops before full. Outcome
unknown at writing: a full pass closes Increment 3 and authorizes - but must NOT
implement - the next experiment, and establishes feasibility, NOT optimality,
since no competing gaze policy is evaluated. Logs under `previews/fsg3/logs/`.

Measured outcome, appended after the run. **FSG3_INCREMENT3_PASS** on the single
prescribed full seed-307 active run, exit 0, empty fails list, final surface
coverage **100.0%**. **Increment 3 is closed; the next experiment is AUTHORIZED
BUT NOT IMPLEMENTED** - no competing policy, learned policy, pose estimation,
ICP, meshing, hole filling, object switching, folds, head motion or vergence
control was written. Feasibility, not optimality: no competing gaze policy was
evaluated.

Integrity: FSG1/FSG2 frozen diff from 7b8d39b empty; ten files added, none
modified. Verified by reading the code before running - fsg3_loop.py and
fsg3_policy.py import no fixture geometry and touch no evaluation_only asset
(only fsg3_eval.py does), and the loop calls compute_once with
check_kernel_equivalence, never compute_variants. prediction_manifest records
truth_opened=false with policy_inputs limited to map xyz_h, current rectified
oracle mask, raw calibration support, calibration and fixation history; the
trajectory, five patches, five map snapshots and final map were all written
before the evaluator opened geometry. Scene/map/policy self-tests PASS
(angular_span=[-10.075,15.190] seed=-7.0 five_looks_reach=true; B=552/648
C=504/696 idempotent=true; map_state_changes_direction=true
resolved_frontier_stops=true), [fsg3-check] SUMMARY passed=5 failed=0, all four
negatives exit 1, and all nine FSG1/FSG2 suites pass 24/29/34/48/37/46/7/8/4.

**The policy chose the trajectory, not me**: 5 fixations at yaw -7, -2, +3, +8,
+13, every saccade exactly +5 deg and nonzero, no repeat, terminating on
no_frontier. The reasoning is genuinely frontier-driven at both ends. At the seed
the object does NOT reach the left edge (left_fraction 0.0) so only one candidate
exists; at each middle step both edges touch but the leftward candidate is
excluded as a revisit; at +13 the object no longer reaches the right edge
(right_fraction 0.0) so no candidate remains and the loop stops. Map yaw extent
grew [-9.709,-2.400] -> [-9.619,+2.873] -> [-9.534,+8.160] -> [-9.525,+13.272]
-> [-9.523,**+14.632**] against the fixture's analytic right boundary of +15.190,
so it stopped at the visible object boundary from segmentation and map evidence
alone.

Per-patch oracle-object coverage 94.050 / 96.564 / 96.603 / 96.723 / 94.756%
(gate >=90), point counts 28,405 / 45,134 / 45,962 / 46,580 / 31,819. Overlaps
(gate >=5,000 matched, median <=10 mm, p95 <=25 mm, idempotent): fix_01 25,720
matched / 43.014% new / 1.992 / 6.336 mm; fix_02 26,514 / 42.313% / 1.966 /
6.104; fix_03 26,608 / 42.877% / 1.823 / 5.455; fix_04 26,426 / **16.949%** /
1.924 / 5.695. All idempotent. Nonterminal new fractions >=15% and the terminal
16.949% clears its relaxed 5% rule by a wide margin, so the asymmetric allowance
was not actually needed.

Persistent surface: 92,632 surfels, support histogram {1: 39,551, 2: 47,660,
3: 5,421}, 15 distinct provenance masks, snapshots 28,405 -> 47,819 -> 67,267 ->
87,239 -> 92,632. Fixed-grid coverage 33.613 -> 54.601 -> 74.785 -> 94.758 ->
**100.000%**, gains +20.987 / +20.184 / +19.974 / +5.242 pp, improvement over the
seed 66.387 pp, no step losing any coverage. Final point-to-plane median
**4.219 mm** and p95 **13.587 mm** (gates 10 / 30). Object purity absolute: all
92,632 map points ID 71, every snapshot and every patch pure 71, background 72
never present.

Small smoke ran the same trajectory, exit 2, missing four gates - fix_00 and
fix_04 oracle coverage 89.513% and 89.547%, final plane median 11.884 mm and p95
31.972 mm. Diagnostic under the handoff, and none of the stop conditions applied,
so full proceeded; all four cleared at full (94.050%, 94.756%, 4.219 mm,
13.587 mm). Nothing tuned, rerendered or re-seeded; no code fix required.

Visuals: growth.png (truth-free, from the loop) shows a narrow strip at -7
widening rightward through -2, +3, +8, +13. growth_truth.png shows the same
against the fixed grid at 33.6 -> 54.6 -> 74.8 -> 94.8 -> 100.0%, final panel
fully covered. The five patch masks confirm the edge evidence directly: at fix_00
the object's left boundary sits inside the core while it runs off the right edge;
fix_01-fix_03 fill the width; at fix_04 background appears at the right edge -
the boundary that ends the loop. Final map Z median -2.0992 m, X [-0.385,+0.546],
Y [-0.157,+0.156]. Missing geometry stays missing - no meshing, filling,
interpolation or registration anywhere.

Cost: smoke 65,536,000 and full 1,048,576,000 primary camera samples. Small loop
8.234 s wall (2.623 s inside Blender), full loop 59.411 s, full evaluation
42.817 s.

Scope: a truth-free frontier policy, from one seed fixation, chose four further
5-deg saccades from the evolving map and its segmentation frontier, stopped
itself at the visible object boundary, and grew a coherent head-frame surface
from 33.6% to 100% of the visible object at 4.2 mm median plane accuracy, with
the FSG1 instrument frozen and no registration estimated. It is one opaque
diffuse textured planar tilted rectangle under oracle segmentation, horizontal
saccades only, fixed 2.10 m vergence, one seed, one policy and a 12 mm
association rule fixed in advance. No competing gaze policy was evaluated, so
nothing here speaks to optimality - the fixed-scan comparison was deliberately
deferred until the active loop worked, which it now does. Folds, self-occlusion,
multi-object switching, head motion, vergence control, calibrated uncertainty and
hidden-surface completeness remain open. Stopped for Luiz/Chat.


### 2026-09-19 - FSG4 Increment 4, active versus fixed scan: authorized, prospective entry (written before acquisition)

Per `docs/fsg4-increment4.md` and D-FSG4a appended just above. The question moves
from "can the loop work?" (FSG3, closed) to "does the feedback buy sampling
efficiency over a non-adaptive scan at equal budget?". Commands, written before
running them:

    .venv/bin/python -u tools/fsg4_pair.py --repo . --out previews/fsg4/smoke-case_a-seed401 --profile small --fixture case_a --seed 401 --mode smoke --device OPTIX
    .venv/bin/python -u tools/fsg4_pair.py --repo . --out previews/fsg4/full-case_a-seed401 --profile full --fixture case_a --seed 401 --mode full --device OPTIX
    .venv/bin/python -u tools/fsg4_pair.py --repo . --out previews/fsg4/full-case_a-seed443 --profile full --fixture case_a --seed 443 --mode full --device OPTIX
    .venv/bin/python -u tools/fsg4_pair.py --repo . --out previews/fsg4/full-case_b-seed401 --profile full --fixture case_b --seed 401 --mode full --device OPTIX
    .venv/bin/python -u tools/fsg4_pair.py --repo . --out previews/fsg4/full-case_b-seed443 --profile full --fixture case_b --seed 443 --mode full --device OPTIX
    .venv/bin/python tools/fsg4_compare.py previews/fsg4/full-case_a-seed401 previews/fsg4/full-case_a-seed443 previews/fsg4/full-case_b-seed401 previews/fsg4/full-case_b-seed443 --out previews/fsg4/full-comparison

**Everything scientific is frozen and was verified by reading the code before
running.** FSG1 instrument `FSG1-HDR-SGBM-one-original-update-original-validity-v1`
via `compute_once`, never `compute_variants`; FSG3 frontier rule in substance;
FSG3 multi-look map with 12 mm association/hash; vergence 2.10 m; 5-degree active
steps; five-fixation budget; **the non-adaptive control is the single frozen
sequence `SCAN_YAWS_DEG = (0.0, -5.0, 5.0, -10.0, 10.0)`**, identical for every
fixture and seed, consulting neither RGB, segmentation, map nor geometry. The
active host and policy import NO fixture geometry (`fsg4_run.py`,
`fsg4_policy.py`) - only the evaluator does - and the active code never branches
on the opaque fixture names.

Paired noise is the design's key control: `render_seed(fixture, seed, yaw_deg,
eye_id)` takes no policy or step argument, so whenever active and scan visit the
same yaw their RGB and oracle arrays must be EXACTLY identical. A mismatch is an
integrity failure, not a numerical result.

Design: two NEW mirrored placements of the same 0.95 x 0.32 m tilted rectangle at
z ~ -2.10 m with distinct textures - `case_a` frontier pointing left, `case_b`
its mirror pointing right - x two fresh MC seeds 401 and 443 = four paired
trials. Both policies start at yaw 0. Analytic design check (an estimate, NOT a
result and NOT an acceptance number): with ideal 12-degree intervals the fixed
scan would cover about 0.840 of case_a and 0.789 of case_b, measured spans
[-19.847,+4.189] and [-3.874,+21.329] degrees.

Gates, all fixed in advance. (A) Integrity, both policies every trial: final
point-to-plane median <=10 mm and p95 <=30 mm; only object ID 81 in the map;
idempotent duplicate replay; no coverage drop beyond 0.5 pp. **The scan is NOT
required to achieve high completeness - poor spatial allocation is the quantity
being measured, not an integrity failure.** (B) Active validity, every trial:
4-5 fixations; termination `no_frontier`, not budget exhaustion; saccades nonzero
and <=5 deg, no revisit; >=90% object measurement coverage per patch; >=5,000
matched per post-seed patch; overlap median <=10 mm and p95 <=25 mm; nonterminal
>=15% new and >=10 pp gain; terminal >=5% new and >=2 pp gain; final coverage
>=90%; gain over seed >=35 pp. (C) Comparison across the four pairs: active AUC
must win **4/4**; mean paired AUC advantage >=0.10; mean final-coverage advantage
>=0.10; active actual camera samples <= scan samples in every pair; all
shared-yaw observations exactly paired. AUC is the frozen normalized discrete
trapezoid over k=1..5 with early-stop coverage carried forward.

Preflight verified: clean main at 4166d0c with cf3601a an ancestor; the
FSG1/2/3 frozen diff over the twenty-one pinned modules empty; eleven files
added; environment Python 3.12.3 / NumPy 2.2.6 / OpenCV 4.13.0 / Pillow 12.3.0,
Blender 5.2.1 LTS on an RTX 4090; `previews/fsg4` absent.
`[fsg4-scene] PASS case_a=[-19.847,4.189] scan_ideal=0.840 case_b=[-3.874,21.329] scan_ideal=0.789`,
`[fsg4-policy] PASS mirrored_frontiers=true resolved_frontier_stops=true`,
`[fsg4-metrics] PASS known_auc_gain=0.220000 early_stop_padding=true`,
`[fsg4-check] SUMMARY passed=6 failed=0`. All four negatives exit 1 (hard-coded
frontier, fixture-favouring scan mutation, paired-noise mismatch, no-advantage
AUC curve). All ten FSG1/2/3 regression suites pass:
24/29/34/48/37/46/4/5/7/8.

All four predeclared full pairs run once each. **A completed numerical exit 2
from one pair does NOT authorize tuning and does NOT cancel the remaining
predeclared pairs; an integrity exception stops execution.** No alternate scan,
threshold, placement, seed or AUC definition may be selected after seeing
results, and no second baseline may be added. Outcome unknown at writing: a pass
closes Increment 4 and records that active frontier feedback improves sampling
efficiency over this fixed-scan control on this controlled mirrored planar
family - explicitly NOT optimality and NOT a population-level statistical result
- and authorizes but does not implement the next experiment. Logs under
`previews/fsg4/logs/`.

Measured outcome, appended after the run. **STOPPED at the small paired smoke on
an integrity failure. The four full paired trials and `fsg4_compare.py` were NOT
run. Increment 4 is NOT closed and no next experiment is authorized.** No
FSG4_INCREMENT4_PASS/FAIL status exists, because the comparison never executed.

    AssertionError: paired observation differs at shared yaw -10.0

`fsg4_pair.py` exit 1. Section 2 stops before full on an integrity/provenance/
runtime failure, and the handoff states a paired-observation mismatch is an
integrity failure, not a numerical policy result.

Diagnosis, measured not assumed. At all three shared yaws the Cycles seeds are
IDENTICAL and the oracle instance masks are BIT-EXACT; only RGB differs, by one
to two float32 ulp: yaw 0.0 seeds (40100050,40100051), 177,748/186,798 of 307,200
elements differing, max 5.96e-07; yaw -5.0 seeds (40100040,40100041), 175,544/
175,029, max 4.77e-07; yaw -10.0 seeds (40100030,40100031), 173,508/174,289, max
4.77e-07. A controlled reproducibility test settles the cause: rendering the
IDENTICAL command twice - same fixture, seed, yaw AND same step - gives the same
discrepancy (174,461/173,449 differing, max 4.768e-07) as two renders at
different steps (174,386/173,221, max 4.768e-07), with all three reporting
seeds_lr = [40100030, 40100031]. So the seed rule is confirmed step-independent
and the difference is NOT policy or step leakage: Cycles/OptiX floating-point
accumulation is non-associative under parallel scheduling and identical inputs
give last-ulp differences on this hardware.

The control's scientific purpose is satisfied in substance. At shared yaw -10.0
every reconstruction statistic is bit-identical between the two policies:
point_count and object_valid_count 10,911; object_reference_count 11,754;
object_measurement_fraction 0.9282797345584481; matched 6,069; new 4,842;
overlap median 0.003912357932249099 m.

I did NOT fix it. `fsg4_pair.py` uses np.array_equal, faithfully implementing the
written requirement that the arrays "must be exactly identical"; the
implementation is not defective, the specification's bit-exactness assumption is
unachievable for RGB on this renderer. That is a specification question, not the
"demonstrated implementation/orchestration defect" D-FSG4a delegates. Relaxing
the comparison would change gate C5 ("all shared-yaw observations must be exactly
paired") and blunt the --negative pairing control whose purpose is to prove this
check can fail, and no tolerance value is prescribed. `git diff` against the
handoff commit shows NO change under tools/; no scan, policy, geometry, texture,
seed, fusion radius, budget, threshold or gate was touched.

Diagnostic only, not a result: both smoke runs completed before the assertion and
both reported FSG4_..._RUN_FAIL on their own small-profile gates (plane error
median/p95 for both; fix_03 object coverage 89.76% for active). The active policy
chose 0, -5, -10, -15 deg, stopped on no_frontier after 4 fixations using
52,428,800 samples and reached 94.67% coverage; the fixed scan spent all five
fixations and 65,536,000 samples for 85.73%, its third look at +5 adding 2.33 pp
and its fifth at +10 landing essentially off-object (384 reference points, 58
valid, skipped_too_few_object_points true) adding 0.00 pp. That is the poor
spatial allocation the experiment exists to measure, and the handoff is explicit
it is not an integrity failure for the scan - but one small-profile pair is not
the four-pair full comparison and the AUC aggregation never ran, so it must not
be reported as the outcome.

Everything else was clean: FSG1/2/3 frozen diff from cf3601a empty; eleven files
added, none modified; fsg4_run.py and fsg4_policy.py import no fixture geometry
and open no evaluator-only asset; the loop calls compute_once with
check_kernel_equivalence, never compute_variants; SCAN_YAWS_DEG =
(0.0,-5.0,5.0,-10.0,10.0) is the single frozen control. Scene/policy/metrics
self-tests PASS (case_a=[-19.847,4.189] scan_ideal=0.840, case_b=[-3.874,21.329]
scan_ideal=0.789; mirrored_frontiers and resolved_frontier_stops true;
known_auc_gain=0.220000 early_stop_padding true), [fsg4-check] SUMMARY passed=6
failed=0, all four negatives exit 1, and all ten FSG1/2/3 suites pass
24/29/34/48/37/46/4/5/7/8.

Open for Luiz/Chat: whether "exactly identical" stays bit-exact - in which case
this comparison cannot run on this GPU as specified and needs a deterministic
rendering path - or is restated as bit-exact seeds and oracle masks plus an
explicit RGB tolerance, with a stated value and gate C5 reworded to match. The
four full pairs and the AUC aggregation remain unrun and unprejudiced; no
alternate scan, threshold, placement, seed or AUC definition has been seen or
selected. Increment 4 stays open. Stopped for Luiz/Chat.


### 2026-09-19 - FSG4b exact shared-view reuse: authorized, prospective entry (written before acquisition)

Per `docs/fsg4b-pairing-reuse.md` and D-FSG4b appended just above. Corrective
ORCHESTRATION only, after FSG4a stopped at the paired-noise gate with no
full-profile comparison. Commands, written before running them:

    .venv/bin/python -u tools/fsg4_pair.py --repo . --out previews/fsg4b/smoke-case_a-seed401 --profile small --fixture case_a --seed 401 --mode smoke --device OPTIX
    .venv/bin/python -u tools/fsg4_pair.py --repo . --out previews/fsg4b/full-case_a-seed401 --profile full --fixture case_a --seed 401 --mode full --device OPTIX
    .venv/bin/python -u tools/fsg4_pair.py --repo . --out previews/fsg4b/full-case_a-seed443 --profile full --fixture case_a --seed 443 --mode full --device OPTIX
    .venv/bin/python -u tools/fsg4_pair.py --repo . --out previews/fsg4b/full-case_b-seed401 --profile full --fixture case_b --seed 401 --mode full --device OPTIX
    .venv/bin/python -u tools/fsg4_pair.py --repo . --out previews/fsg4b/full-case_b-seed443 --profile full --fixture case_b --seed 443 --mode full --device OPTIX
    .venv/bin/python tools/fsg4_compare.py previews/fsg4b/full-case_a-seed401 previews/fsg4b/full-case_a-seed443 previews/fsg4b/full-case_b-seed401 previews/fsg4b/full-case_b-seed443 --out previews/fsg4b/full-comparison

**The exact pairing gate is NOT relaxed and no RGB tolerance is introduced.**
Verified by reading the code before running: `fsg4_pair.py` still uses
`np.array_equal`, and the gate is now STRICTER - it requires exact arrays AND
exact seeds AND a declared `paired_observation_reused` flag on every scan
shared-yaw record. The repaired `--negative pairing` control mutates one float in
an otherwise reused observation and still exits 1, which is the direct proof the
gate was not weakened.

Mechanism: active runs FIRST with no cache
(`ma=fsg4_run.execute(_ns(args,ar,"active"))`, no provider argument); its
completed acquisitions are indexed by yaw; the scan runs second with a provider
that clones the completed active acquisition at shared yaws, rewriting only
step-local metadata, and renders scan-only yaws normally with the frozen
yaw-keyed seed rule. The fixed scan is nonadaptive, so reuse cannot influence its
schedule, and active cannot inspect scan state.

**The scientific experiment is unchanged**, and I verified it rather than
assuming: `git diff d4104d9` over `fsg4_scene.py`, `fsg4_policy.py`,
`fsg4_metrics.py`, `fsg4_public.py`, `fsg4_eval.py`, `fsg4_compare.py`, the FSG1
stereo modules, `fsg3_surface_map.py`, rig, bl_common and requirements-fsg.txt is
EMPTY. Only three orchestration files differ from FSG4a:
`tools/dev/check_fsg4.py` (added 7th check, repaired pairing negative),
`tools/fsg4_pair.py` (reuse orchestration) and `tools/fsg4_run.py` (optional view
provider). `fsg4_run.py` remains truth-free: it imports no fixture geometry and
opens no `evaluation_only` asset.

Budget accounting: logical `primary_camera_samples` is charged in full per
fixation regardless of reuse - a reused shared view still costs the scan one
fixation - while `new_primary_camera_samples` records only what this execution
actually rendered. Confirmed in `fsg4_run.py`: `samples += primary_camera_samples`
unconditionally, `new_samples += new_primary_camera_samples`, and the clone sets
the latter to 0 while preserving the former.

Preflight verified: clean main at 83b6038 with d4104d9 an ancestor; D-FSG4b
absent; `previews/fsg4b` absent; the stopped FSG4a record preserved at
`previews/fsg4/smoke-case_a-seed401`; environment Python 3.12.3 / NumPy 2.2.6 /
OpenCV 4.13.0 / Pillow 12.3.0 with Blender 5.2.1 LTS.
`[fsg4-scene] PASS case_a=[-19.847,4.189] scan_ideal=0.840 case_b=[-3.874,21.329] scan_ideal=0.789`,
`[fsg4-policy] PASS mirrored_frontiers=true resolved_frontier_stops=true`,
`[fsg4-metrics] PASS known_auc_gain=0.220000 early_stop_padding=true`,
`[fsg4-check] SUMMARY passed=7 failed=0` including the new "exact shared-view
artifact reuse" check. All four negatives exit 1. All ten FSG1/2/3 regression
suites pass 24/29/34/48/37/46/4/5/7/8.

Gates are the unchanged FSG4a ones: (A) both policies every trial - final
point-to-plane median <=10 mm, p95 <=30 mm, only object ID 81, idempotent
duplicate replay, no coverage drop beyond 0.5 pp, with the scan NOT required to
achieve high completeness; (B) active validity - 4-5 fixations, termination
`no_frontier`, saccades nonzero <=5 deg without revisit, >=90% object coverage
per patch, >=5,000 matched per post-seed patch, overlap median <=10 mm and p95
<=25 mm, nonterminal >=15% new and >=10 pp gain, terminal >=5% new and >=2 pp
gain, final coverage >=90%, gain over seed >=35 pp; (C) comparison across four
pairs - active AUC wins 4/4, mean AUC advantage >=0.10, mean final-coverage
advantage >=0.10, active logical samples <= scan in every pair, all shared-yaw
observations exactly paired.

All four predeclared full pairs run once each. A completed pair's numerical exit
2 does NOT authorize tuning and does NOT cancel the remaining pairs; an integrity
exception stops execution. No tolerance, rerender after a miss, alternate scan,
threshold, seed, geometry, texture, policy, fusion radius or AUC change. No full
FSG4 pair has been observed yet, so the comparison remains unprejudiced. Outcome
unknown at writing: a pass closes Increment 4 with the limited claim that active
frontier feedback improves surface acquisition efficiency over this ONE frozen
nonadaptive scan on this controlled mirrored planar family - not optimality, not
a population-level statistical result - and authorizes but does not implement the
next experiment. Logs under `previews/fsg4b/logs/`.

Measured outcome, appended after the run. **FSG4_INCREMENT4_FAIL.** The pairing
repair worked and the full four-pair comparison ran for the first time. Every
comparison gate (C) passed emphatically, but the active-run validity contract (B)
failed on case_b at BOTH seeds, so **Increment 4 is NOT closed and no next
experiment is authorized.** All four pairs preserved; nothing tuned.

    fails: ["case_b/401 active run failed", "case_b/443 active run failed"]
    active fails, both case_b seeds: ["fix_04 too little new surface",
                                      "active fixation 4 added too little visible surface"]

The exact-pairing gate was preserved, not relaxed: fsg4_pair.py still uses
np.array_equal and the gate is STRICTER, requiring exact arrays AND exact seeds
AND a declared reuse flag. The repaired --negative pairing control mutates one
float in an otherwise reused observation and still exits 1. Only three
orchestration files differ from FSG4a (check_fsg4.py, fsg4_pair.py,
fsg4_run.py); the diff over fsg4_scene/policy/metrics/public/eval/compare, the
FSG1 stereo modules, fsg3_surface_map, rig, bl_common and requirements-fsg.txt is
empty. fsg4_run.py remains truth-free and truth_opened is false in all eight runs.
Checks 7/0 including the new exact shared-view reuse check, four negatives exit 1,
ten FSG1/2/3 suites pass 24/29/34/48/37/46/4/5/7/8.

Pairing: 3 shared yaws per pair, all arrays exact, all seeds exact, all reused;
active reuse count 0 in all four, and active newly-rendered equals active logical
in all four, independently confirming it received no cache. Budgets unchanged by
reuse: case_a active 838,860,800 vs scan 1,048,576,000; case_b both
1,048,576,000. The harness newly rendered 419,430,400 for each scan instead of
1,048,576,000, which is execution provenance only.

Curves and comparison. case_a/401 active 0.44112/0.65625/0.88629/0.99995/0.99995
AUC 0.815756 final 0.999947 vs scan 0.44112/0.65625/0.65625/0.88629/0.88629 AUC
0.715625 final 0.886292; case_a/443 nearly identical. case_b/401 active
0.37815/0.58183/0.78262/0.98724/1.00000 AUC 0.760189 final 1.0 vs scan
0.37815/0.37815/0.58183/0.58183/0.78262 AUC 0.530548 final 0.782616; case_b/443
nearly identical. Gate C ALL PASS: AUC wins 4/4, mean AUC advantage 0.164873
(>=0.10), mean final-coverage advantage 0.165546 (>=0.10), active logical <= scan
in 4/4, all shared yaws exactly paired.

Gate A ALL PASS both policies all pairs: active plane median 3.968-4.346 mm and
p95 12.833-14.144 mm; scan 3.813-4.201 mm and 12.258-13.245 mm; every map pure ID
81; every post-seed fusion idempotent; no coverage drop beyond 0.5 pp. The scan's
low completeness is not an integrity failure, as specified.

Gate B: case_a PASSES both seeds (4 fixations 0,-5,-10,-15, no_frontier, matched
24,741-26,880, overlap medians 1.998-2.088 mm p95 5.972-6.169 mm, final 99.995%,
gain over seed 55.88 pp). case_b FAILS both seeds on the TERMINAL patch only: new
fraction 0.03912/0.03970 against a >=0.05 rule and terminal coverage gain
1.276/1.282 pp against a >=2 pp rule. Everything else on case_b passes - 5
fixations 0,+5,+10,+15,+20, no_frontier, matched 24,942-26,073, overlap medians
1.874-2.013 mm, nonterminal gains 20.08-20.46 pp, final coverage 100.000%, gain
over seed 62.19 pp. Cause is legible: the policy is already at 98.72% after four
looks, so its fifth at +20 catches only the last sliver up to the object's right
boundary at +21.329 deg, yet it still reported frontier remaining.

Worth recording as a tension rather than smoothing over: the same case_b
trajectory that violates the terminal-patch rule also produces the largest
advantage in the experiment (AUC gain 0.2296, final gain 0.2173, 100% coverage).
The efficiency question and the inherited FSG3 terminal contract disagree here;
resolving that is a specification decision for Luiz/Chat, not Code's.

Visuals: coverage_vs_budget.png shows both curves starting at the identical seed
point in all four pairs with active above scan from k=2 onward, and the scan's
flat segments are the visible cost of nonadaptive allocation (case_a gains
nothing k=2->3; case_b nothing k=1->2 and k=3->4). growth_truth.png for
case_b/401 is the clearest view: active marches 0->+5->+10->+15->+20 with
coverage 37.8->58.2->78.3->98.7->100.0%, while the scan spends its -5 and -10
looks entirely off the object, unchanged at 37.8% and 58.2%, ending at 78.3%.

No tolerance introduced, no rerender after a miss, no alternate scan, threshold,
seed, geometry, texture, policy, fusion radius or AUC change; no code fix needed.
What the run establishes: on this controlled mirrored planar family with exactly
paired observations, the active policy beat the one frozen nonadaptive scan on
every pair by a wide margin. What it does not: the active run is not yet a valid
FSG3-contract run on case_b, so the increment's own pass rule is unmet.
Increment 4 stays OPEN. Stopped for Luiz/Chat.


### 2026-09-19 - FSG4c fresh efficiency validation: authorized, prospective entry (written before acquisition)

Per `docs/fsg4c-increment4.md` and D-FSG4c appended just above. **A FRESH
validation, not a reinterpretation of FSG4b.** The formal FSG4b FAIL and every
earlier record are preserved unchanged; FSG4b observations are
development/diagnostic data and are NOT reused in this comparison. Commands,
written before running them:

    .venv/bin/python -u tools/fsg4c_pair.py --out previews/fsg4c/smoke-case_c-seed503 --profile small --fixture case_c --seed 503 --mode smoke --device OPTIX
    .venv/bin/python -u tools/fsg4c_pair.py --out previews/fsg4c/full-case_c-seed503 --profile full --fixture case_c --seed 503 --mode full --device OPTIX
    .venv/bin/python -u tools/fsg4c_pair.py --out previews/fsg4c/full-case_c-seed557 --profile full --fixture case_c --seed 557 --mode full --device OPTIX
    .venv/bin/python -u tools/fsg4c_pair.py --out previews/fsg4c/full-case_d-seed503 --profile full --fixture case_d --seed 503 --mode full --device OPTIX
    .venv/bin/python -u tools/fsg4c_pair.py --out previews/fsg4c/full-case_d-seed557 --profile full --fixture case_d --seed 557 --mode full --device OPTIX
    .venv/bin/python -u tools/fsg4c_compare.py previews/fsg4c/full-case_c-seed503 previews/fsg4c/full-case_c-seed557 previews/fsg4c/full-case_d-seed503 previews/fsg4c/full-case_d-seed557 --out previews/fsg4c/full-comparison

**The only contract correction is conceptual**: per-fixation `new_fraction` and
incremental coverage gain become DESCRIPTIVE measurements rather than
run-failure gates, and **no replacement threshold is introduced**. The reason is
arithmetic: with coverage at 98.72% before the terminal fixation, at most 1.28 pp
remains, so a >=2 pp terminal-gain rule is unsatisfiable even by a view that
closes 100% of the residual. In an efficiency experiment a wasteful fixation
should be penalised through C(k) and AUC, not invalidate the trial. Residual
closure `gain/(1-C_previous)` will be reported where defined.

**Everything else is frozen and I verified it by reading the code, not
assuming**: `git diff 373d853` over `fsg4_policy.py`, `fsg4_public.py`,
`fsg4_metrics.py`, `fsg4_scene.py`, `fsg4_eval.py`, `fsg4_compare.py`,
`fsg4_pair.py`, `fsg4_run.py`, the FSG1 stereo modules, `fsg3_surface_map.py`,
rig, bl_common and requirements-fsg.txt is EMPTY - FSG4b and earlier are
untouched. `fsg4c_run.py` imports the EXISTING `fsg4_policy` unchanged, calls
`compute_once` with `check_kernel_equivalence` (never `compute_variants`),
imports no fixture geometry and opens no `evaluation_only` asset.
`fsg4c_public.SCAN_YAWS_DEG = (0.0,-5.0,5.0,-10.0,10.0)`,
`FIXTURES = ("case_c","case_d")`, `SEEDS = (503,557)`. `fsg4c_pair.py` still
compares with `np.array_equal` - exact pairing is unchanged and no tolerance
exists. `fsg4c_eval.py` declares `per_fixation_novelty_and_gain_gated: False`.

Fresh fixtures: `case_c` centre x=-0.38 m z=-2.18 m, 1.00 x 0.34 m, tilt 9 deg,
texture tag 7; `case_d` centre x=+0.34 m z=-2.05 m, 1.02 x 0.30 m, tilt 8 deg,
texture tag 11. Analytic design check (a calculation, NOT a result and NOT an
acceptance number): spans [-21.155,+3.100] and [-4.449,+23.122] deg with
fixed-scan ideal angular coverage 0.787 and 0.742.

Run validity gates, both policies: final map point-to-plane median <=10 mm and
p95 <=30 mm; only object ID 81; no coverage decrease >0.5 pp; every post-seed
fusion replay idempotent. Active additionally: 4-5 fixations; termination
`no_frontier`; local non-repeating <=5 deg saccades; >=100 oracle reference
pixels and >=90% object measurement coverage per patch; >=5,000 overlap matches
per post-seed patch; overlap median <=10 mm and p95 <=25 mm; final fixed-grid
coverage >=90%. Scan: exactly five prescribed yaws and `fixed_budget`
termination, with NO completeness gate. Aggregate pass needs all four active runs
valid, all four scan maps valid, exact reuse at every shared yaw, active logical
samples <= scan in all four, active AUC > scan AUC in 4/4, mean AUC advantage
>=0.10 and mean final-coverage advantage >=0.10.

Preflight verified: clean main at ee2698c with 373d853 an ancestor; D-FSG4c
absent; `previews/fsg4c` absent; FSG4b records preserved; environment Python
3.12.3 / NumPy 2.2.6 / OpenCV 4.13.0 / Pillow 12.3.0, Blender 5.2.1 LTS on an RTX
4090. All eight new Python files compile. `[fsg4c-check] SUMMARY passed=7
failed=0`, including "per-fixation novelty is descriptive only" and "frozen
policy responds to map/mask state". All five negatives exit 1 - the `novelty`
control detects reintroduction of the obsolete per-fixation gain gate and notes
residual closure would be 100%. All eleven FSG1/2/3/4 regression suites pass
24/29/34/48/37/46/4/5/7/7/8.

All four predeclared full pairs run exactly once and ALL FOUR are aggregated even
if a pair exits 2 numerically; only an integrity/provenance/runtime exception
stops early. No rerender after a numerical miss, no alternate policy, scan,
fixture geometry, texture, seed, SPP, stereo instrument, fusion radius, budget,
AUC, accuracy threshold, final-coverage threshold, aggregate threshold or pairing
change. Active receives no paired cache; only the later scan may reuse active
acquisitions at shared yaws, with arrays and seeds exactly equal. **A poor
individual fixation is allowed to be poor** - it is reported and penalised
through the curve, and no per-fixation utility gate will be reintroduced.

Outcome unknown at writing. If and only if the aggregate is
`FSG4C_INCREMENT4_PASS` do I close Increment 4 and authorize - but NOT implement
- the next experiment; the claim would be limited to frontier feedback improving
visible-surface acquisition efficiency over this ONE frozen nonadaptive scan on
this controlled fresh planar family, and is neither policy optimality nor a
population estimate. Otherwise I record `FSG4C_INCREMENT4_FAIL`, preserve every
full pair and stop for Luiz/Chat. Logs under `previews/fsg4c/logs/`.

Measured outcome, appended after the run. **FSG4C_INCREMENT4_PASS**, exit 0,
empty fails. **Increment 4 is CLOSED; the next experiment is AUTHORIZED BUT NOT
IMPLEMENTED** - no design or code for it was written. The formal FSG4b FAIL and
all earlier records are preserved; this was a fresh validation, not a
reinterpretation, and no FSG4b observation entered the comparison.

Integrity: diff from 373d853 over fsg4_policy/public/metrics/scene/eval/compare/
pair/run, the FSG1 stereo modules, fsg3_surface_map, rig, bl_common and
requirements-fsg.txt is EMPTY; ten files added, none modified. fsg4c_run.py
imports the EXISTING unchanged fsg4_policy, calls compute_once with
check_kernel_equivalence, imports no fixture geometry and opens no
evaluation_only asset; SCAN_YAWS_DEG=(0,-5,5,-10,10), FIXTURES=(case_c,case_d),
SEEDS=(503,557); fsg4c_pair.py still uses np.array_equal so exact pairing is
unchanged; fsg4c_eval.py declares per_fixation_novelty_and_gain_gated=False. All
eight new files compile. [fsg4c-check] SUMMARY passed=7 failed=0; all five
negatives exit 1 including the novelty control that detects reintroduction of the
obsolete per-fixation gain gate; all eleven FSG1/2/3/4 suites pass
24/29/34/48/37/46/4/5/7/7/8.

Pairing: 3 shared yaws per pair, 12/12 rows arrays-exact and seeds-exact and
reused; active reuse 0 with active newly-rendered equal to active logical in all
four, proving no cache; truth_opened false in all eight runs. Logical budgets
838,860,800 (case_c active) or 1,048,576,000 vs scan 1,048,576,000; active <=
scan in 4/4. Harness newly rendered 419,430,400 per scan, provenance only.

The policy found opposite directions on the mirrored placements without being
told: case_c 0,-5,-10,-15 (4 fixations) and case_d 0,+5,+10,+15,+20 (5), both
no_frontier. Curves: case_c active 0.390625/0.601423/0.823335/1.0/1.0 AUC
0.780018 vs scan 0.390625/0.601423/0.601423/0.823335/0.823335 AUC 0.658290;
case_d active 0.363002/0.546828/0.733073/0.917969/1.0 AUC 0.719843 vs scan
0.363002/0.363002/0.546828/0.546828/0.733073 AUC 0.501174; second seeds match to
~1e-4. Active reached 100.000% final coverage in all four.

Descriptive per-fixation measurements (never gated): case_c post-seed matched
25,445-27,555, new fractions 0.377-0.429, gains 17.66-22.20 pp, residual closure
34.59% -> 55.68% -> 100.000%; case_d matched 23,701-25,035, new fractions
0.272-0.451, gains 8.20-18.62 pp, residual closure 28.86% -> 41.10% -> 69.27% ->
100.000%. The terminal fixation closes 100.000% of the residual in all four
pairs. **Honest note: the contract correction was not load-bearing here** - the
terminal new fractions (0.377/0.272) and gains (17.66/8.20 pp) would have
satisfied the retired >=5% and >=2 pp rules anyway, so no run was rescued by
removing them. The correction remains right in principle but this PASS does not
depend on it.

Run validity, both policies all four pairs: plane medians 4.308-4.520 mm and p95
13.590-14.808 mm (gates 10/30); every map pure ID 81; every post-seed fusion
idempotent; no coverage decrease anywhere. Active: 4-5 fixations, no_frontier,
non-repeating 5 deg saccades, min object reference 34,730 px (gate >=100), min
object measurement coverage 93.844% (gate >=90%), post-seed matches
23,701-27,555 (gate >=5,000), overlap medians and p95 inside 10/25 mm, final
coverage 100% (gate >=90%). Every run reports an empty fails list. The scan has
no completeness gate and was not penalised for its low coverage.

Aggregate: all seven conditions pass - four valid active runs, four valid scan
maps, exact reuse at every shared yaw, active logical <= scan in 4/4, active AUC
wins **4/4**, mean AUC advantage **0.170182** (>=0.10), mean final-coverage
advantage **0.221831** (>=0.10). Per-pair AUC gains 0.121727/0.121704/0.218669/
0.218628; final gains 0.176665/0.176572/0.266927/0.267160. No numerical FAIL line
anywhere.

Visuals: coverage_vs_budget.png shows both curves starting at the identical seed
point with active above scan from k=2 onward in all four, and the scan's flat
segments are the visible cost of nonadaptive allocation. growth_truth.png for
case_d/503 shows active marching 0->+5->+10->+15->+20 with coverage
36.3->54.7->73.3->91.8->100.0% while the scan spends its -5 and -10 looks
entirely off the object, unchanged at 36.3% and 54.7%, finishing at 73.3%.

Cost: smoke 78,643,200 samples in 27.8 s; full pairs 2m42.0s, 2m39.9s, 3m0.8s,
3m1.0s; aggregation 0.1 s. No code fix was required or made. Nothing tuned - no
policy, scan, geometry, texture, seed, SPP, instrument, fusion radius, budget,
AUC, threshold or pairing change, no rerender after a miss, no per-fixation
utility gate reintroduced.

Scope of the closure: on this controlled fresh planar family, with exactly paired
observations and equal-or-lower logical budget, the frozen frontier policy
acquired visible surface more efficiently than the one frozen nonadaptive scan -
AUC wins 4/4 by a mean 0.170, reaching 100% final coverage against 73-82%. Two
opaque diffuse planar placements, two MC seeds, oracle segmentation, exact poses,
horizontal saccades only, fixed 2.10 m vergence, one policy and ONE comparison
scan. Not policy optimality, not a population estimate, and silent on folds,
self-occlusion, multi-object scenes, head motion, vergence control and calibrated
uncertainty. Stopped for Luiz/Chat.


### 2026-09-20 - FSG5 Increment 5, curved-surface growth: authorized, prospective entry (written before acquisition)

Per `docs/fsg5-increment5.md` and D-FSG5a appended just above. **A curvature
stress test, not a new-policy experiment**: geometry changes, intelligence does
not. Commands, written before running them:

    .venv/bin/python tools/fsg5_run.py  --out previews/fsg5/smoke-curve_right-seed601 --profile small --fixture curve_right --seed 601 --device OPTIX
    .venv/bin/python tools/fsg5_eval.py previews/fsg5/smoke-curve_right-seed601 --out previews/fsg5/smoke-curve_right-seed601-evaluation --mode smoke
    (then the four full trials curve_right/601, curve_right/647, curve_left/601, curve_left/647,
     each run + evaluated, then fsg5_compare.py over exactly those four metrics.json)

**Everything scientific is frozen and I verified it by reading the code, not
assuming**: `git diff 47ba474` over the FSG1 stereo modules
(`fsg_stereo_supported`, `fsg_stereo_hdr`, `fsg_stereo`, `fsg_evaluate`,
`fsg_geometry`), `fsg4_policy.py`, `fsg3_surface_map.py`, `fsg4_public.py`,
`rig.py`, `bl_common.py` and `requirements-fsg.txt` is EMPTY. `fsg5_run.py`
imports the EXISTING `fsg4_policy` and the EXISTING `fsg3_surface_map`, calls
`compute_once` with `check_kernel_equivalence` (never `compute_variants`),
imports no fixture geometry and opens no `evaluation_only` asset.
`fsg5_public` fixes association_radius_m = 0.012, hash_cell_m = 0.012,
VERGENCE_DISTANCE_M = 2.10, FIXTURES = (curve_right, curve_left),
SEEDS = (601, 647).

Fixtures: two opaque diffuse cylindrical ribbons, vertical axis, radius 0.75 m,
height 0.34 m, centre z = -2.80 m, 75 deg arc, 40 quad strips, mirrored with
distinct textures. Pre-render geometry check measured max chord error 0.100 mm
against the analytic cylinder (requirement < 0.2 mm) and visible spans
right=[-8.487,+14.866] and left=[-14.866,+8.487] deg - so each seed exposes only
one unresolved frontier. The design traces `-7,-2,+3,+8,+13` and
`+7,+2,-3,-8,-13` are sanity notes, NOT acceptance criteria; **the policy chooses
the actual trajectories from its own map and segmentation evidence.**

Gates, all four trials judged independently and all four required: 4-6 fixations;
termination `no_frontier`; every saccade exactly 5 deg with no repeat; >=100
oracle object reference pixels and >=90% valid object measurement coverage per
patch; per post-seed patch >=5,000 matched, overlap median <=10 mm and p95
<=25 mm, idempotent duplicate replay, no fixed-grid coverage drop beyond 0.5 pp.
Curved geometry on the final map: analytic finite-cylinder point-to-surface
median <=10 mm and p95 <=30 mm; final curved-surface coverage >=90% (a truth
sample on the fixed 256x84 (theta,y) grid counts as covered when a surfel lies
within 15 mm, so this is CURVED-SURFACE completeness, not image coverage);
coverage gain over the seed >=35 pp; only instance 81; >=5,000 surfels with
support from >=2 fixations; and for those, **absolute median signed radial error
<=7.5 mm** - the curvature-specific gate, since averaging across a curved surface
can contract the map inward even when association distances look small.

Preflight verified: clean main at 18cfd0a with 47ba474 an ancestor; D-FSG5a
absent; `previews/fsg5` absent; environment Python 3.12.3 / NumPy 2.2.6 / OpenCV
4.13.0 / Pillow 12.3.0, Blender 5.2.1 LTS on an RTX 4090. All seven new Python
files compile. `[fsg5-scene] PASS right=[-8.487,14.866] left=[-14.866,8.487]
chord_max_mm=0.100` and `[fsg5-check] SUMMARY passed=6 failed=0`. All five
negatives exit 1: hard-coded/wrong curved frontier, flat substitute for the
curved surface, 5 cm map shift, **15 mm fusion contraction**, and background
contamination. All twelve existing FSG1-FSG4c regression suites remain green:
24/29/34/48/37/46/4/5/7/7/7/8.

Anticipated failure modes, in the order the handoff ranks them, to be diagnosed
before any edit: (a) the current 12 mm Euclidean fusion losing overlap or
radially contracting the curved surface; (b) the existing image-edge/map-yaw
policy stopping early or failing to terminate on one mirror; (c) the FSG1 local
matcher losing coverage on strongly oblique cylinder strips; (d) only then
renderer/mesh integration.

All four full trials run exactly once. A completed numerical exit 2 does NOT
authorize tuning and does NOT cancel the remaining predeclared trials - it is
preserved and the schedule continues; only an integrity/provenance/runtime
exception stops early. No rerender after a numerical miss, no alternate radius,
curvature, seed, texture, policy, threshold or fixation schedule; no ICP,
normals-based registration, meshing, hole filling, new frontier logic or
competing policy. Outcome unknown at writing: a pass closes Increment 5 and
authorizes - but must NOT implement - the next experiment, with the claim limited
to this controlled convex cylindrical family; a miss is preserved and returned to
Luiz/Chat. Logs under `previews/fsg5/logs/`.

Measured outcome, appended after the run. **FSG5_INCREMENT5_PASS**, exit 0,
trial_passes 4, empty fails; all four full trials FSG5_CURVED_RUN_PASS with empty
fail lists. **Increment 5 is CLOSED; the next experiment is AUTHORIZED BUT NOT
IMPLEMENTED** - no design or code for it was written. The already validated
active loop grew a metrically correct curved surface with no new policy, no
registration step and no surface model.

Integrity: diff from 47ba474 over the FSG1 stereo modules, fsg4_policy.py,
fsg3_surface_map.py, fsg4_public.py, rig, bl_common and requirements-fsg.txt is
EMPTY; nine files added, none modified. fsg5_run.py imports the EXISTING
fsg4_policy and EXISTING fsg3_surface_map, calls compute_once with
check_kernel_equivalence, imports no fixture geometry and opens no
evaluation_only asset. Seven new files compile. [fsg5-scene] PASS
right=[-8.487,14.866] left=[-14.866,8.487] chord_max_mm=0.100; [fsg5-check]
SUMMARY passed=6 failed=0; all five negatives exit 1 (hard-coded curved frontier,
flat substitute, 5 cm shift, **15 mm fusion contraction**, background
contamination). All twelve FSG1-FSG4c suites green: 24/29/34/48/37/46/4/5/7/7/7/8.

Smoke (curve_right/601, small): run exit 0, eval exit 2 on four numerical gates -
surface median 12.225 mm, p95 30.546 mm, fix_00/fix_04 object coverage
87.756%/89.819%. Familiar small-profile gap; integrity sound so full proceeded.
The curvature gate already passed at small: signed radial median -4.295 mm on
12,146 multi-look surfels.

Four full trials, each 5 fixations terminating no_frontier with exactly 5 deg
non-repeating saccades. **The policy produced the mirrored trajectory on the
mirrored fixture unaided**: curve_right -7,-2,+3,+8,+13 and curve_left
+7,+2,-3,-8,-13. Coverage final 99.995% / 100.000% / 100.000% / 99.991%, gains
over seed 69.79 / 69.81 / 62.90 / 62.89 pp. Map points 90,675-91,723 with
54,526-55,383 multi-look surfels (gate >=5,000). Purity ID 81 only and every
post-seed replay idempotent in all four.

Curved geometry: surface median 3.647 / 3.654 / 3.362 / 3.363 mm (gate <=10) and
p95 11.263 / 11.309 / 10.769 / 10.797 mm (gate <=30) - clearing both by about
2.7x. **Signed radial median +1.335 / +1.335 / +1.251 / +1.252 mm** (gate
|.|<=7.5), i.e. POSITIVE - the map sits ~1.3 mm outward of the analytic cylinder,
so the anticipated failure mode (a), 12 mm Euclidean fusion radially contracting
a curved surface, DID NOT occur. Independent check on the exported clouds agrees:
reconstructed median radius 0.75075-0.75097 m against a true 0.750 m, y extent
[-0.168,+0.166] m against a 0.34 m ribbon.

Per-patch and overlap across all four: min oracle object reference 25,686 px
(gate >=100); min object measurement coverage 93.561% (gate >=90%); post-seed
matched 24,147-29,018 (gate >=5,000); overlap medians 1.800-2.014 mm (gate <=10);
p95 4.722-6.012 mm (gate <=25); largest coverage decrease 0.005 pp (tolerance
0.5 pp). Aggregate: mean final coverage 0.9999651; ranges surface median
3.362-3.654 mm, p95 10.769-11.309 mm, signed radial +1.251 to +1.335 mm.

Descriptive observation, not a failure: on curve_left the fifth fixation added
essentially nothing - new fraction 0.00066/0.00074, coverage gain +0.014 pp
(601) and -0.005 pp (647) - because coverage was already 99.99% after four looks.
Under the closed FSG4c contract these are descriptive, so the runs stay valid and
the tiny decrease is far inside tolerance. Same slight overshoot the policy showed
on FSG4b's case_b; recorded rather than smoothed away. curve_right used its fifth
fixation productively, gaining 5.86 pp.

Visuals: growth.png and growth_truth.png for all four show the mirrored fixtures
growing in mirror-image directions - curve_right seeds at -7 deg on the left edge
and grows rightward 30.2->50.4->70.3->94.1->100.0%, curve_left seeds at +7 deg on
the right edge and grows leftward 37.1->56.6->77.3->100.0->100.0%. The accumulated
surfaces are visibly curved ribbons wrapping the cylinder, not flat rectangles.
coverage_curved.png shows all four rising monotonically to 100.0% with per-trial
median/p95 at 3.4-3.7 / 10.8-11.3 mm. Each surface_map.ply carries "comment fixed
head frame H", no faces, a support property, 90,675-91,723 vertices, support
histograms ~35-37k single / 48-50k double / 5.7-6.2k triple. No meshing, filling
or registration anywhere.

Cost: smoke 65,536,000 samples; each full trial 1,048,576,000, so 4,194,304,000
across the four. Wall: smoke run 14.5 s, eval 9.3 s; full runs 1m16.6s, 1m17.0s,
1m18.2s, 1m17.1s; aggregation 0.09 s. **No code fix was required or made.**
Nothing tuned - no geometry, texture, seed, SPP, vergence, instrument, policy,
fusion radius, coverage radius or gate change; no rerender after the smoke miss;
no ICP, normals registration, meshing, hole filling, new frontier logic,
competing policy or extra seed.

Scope: the frozen FSG1 instrument, unchanged FSG4 policy and unchanged FSG3 12 mm
fusion grew a convex curved surface to ~100% completeness at 3.4-3.7 mm median
accuracy with no inward contraction, on both mirror orientations and both seeds.
Narrow: two mirrored opaque diffuse cylindrical ribbons of ONE fixed radius
(0.75 m) and arc (75 deg), two MC seeds, oracle segmentation, exact poses,
horizontal saccades, fixed 2.10 m vergence. NOT a result about general curvature,
varying radius, concave or saddle geometry, self-occlusion, folds, multi-object
scenes, head motion, vergence control or calibrated uncertainty. The policy
remains a 2D image-edge/map-yaw controller; a true 3D surface-frontier controller
is now a clean next question and was deliberately not built. Stopped for
Luiz/Chat.

### 2026-09-20 - FSG6 Increment 6, the reconstructed surface becomes the frontier: authorized, prospective entry (written before acquisition)

Per `docs/fsg6-increment6.md` and D-FSG6a appended just above. **The frontier
representation changes; the measurement instrument and the fusion do not.**
Commands, written before running them:

    .venv/bin/python tools/dev/check_fsg6.py
    for n in policy mapstate horizontal flat shift bias purity; do .venv/bin/python tools/dev/check_fsg6.py --negative "$n"; done
    (all existing FSG1-FSG5 regression checks, unchanged)
    .venv/bin/python tools/fsg6_run.py  --out previews/fsg6/smoke-diag_up_right-seed701 --profile small --fixture diag_up_right --seed 701 --device OPTIX
    .venv/bin/python tools/fsg6_eval.py previews/fsg6/smoke-diag_up_right-seed701 --out previews/fsg6/smoke-diag_up_right-seed701-evaluation --mode smoke
    (then the four full trials diag_up_right/701, diag_up_right/743, diag_down_left/701, diag_down_left/743,
     each run once and evaluated, then fsg6_compare.py over exactly those four metrics.json)

**What is frozen, verified by reading the code rather than assuming**:
`git diff 3d5125c` over the FSG1 stereo modules (`fsg_stereo_supported`,
`fsg_stereo_hdr`, `fsg_stereo`, `fsg_evaluate`, `fsg_geometry`),
`fsg3_surface_map.py`, `rig.py`, `bl_common.py` and `requirements-fsg.txt` is
EMPTY. `fsg6_run.py` imports the EXISTING `fsg3_surface_map` and calls
`compute_once` behind `check_kernel_equivalence` (never `compute_variants`);
neither `fsg6_run.py` nor `fsg6_frontier.py` imports `fsg6_scene` or opens any
`evaluation_only` asset - `fsg6_frontier` imports only numpy and `fsg6_public`.
`fsg6_run` additionally asserts at start-up that `fsg6_public.FUSION` equals the
frozen `fsg4_public.FUSION`, so the 12 mm association/hash cannot drift.
`fsg6_public` fixes VERGENCE_DISTANCE_M = 2.10, FIXTURES =
(diag_up_right, diag_down_left), SEEDS = (701, 743), spp 64/256, OBJECT_ID 91,
and the frontier constants: 25 mm voxel, 65 mm neighbourhood, >=6 neighbours,
tangent asymmetry >=0.18, 120 mm lookahead, alignment cos >=0.50, >=8 agreeing
frontier surfels per candidate, 5 deg component step, yaw [-25,+25], pitch
[-20,+20], 1% robust map extent quantile.

Fixtures: two finite cylindrical ribbons, radius 0.75 m, local centre
z = -2.80 m, 110 deg arc, 0.20 m width, 48 quad strips, rigidly rolled in the
head image plane by +35 deg (`diag_up_right`) and +215 deg (`diag_down_left`,
the exact 180 deg image-plane mirror), with distinct textures. Seed gazes are
(-8,-8) and (+8,+8) deg. The fixture family is deliberately asymmetric with
respect to controller class: a plausible four-look diagonal trace covers >97% of
the truth surface while even a five-look horizontal-only scan along the correct
yaw direction covers <65%. Those are fixture-construction estimates checked in
software, **not** experimental results and **not** trajectory acceptance
criteria; **the policy chooses the actual trajectories from its own 3D map plus
current segmentation evidence.**

Gates, all four trials judged independently and all four required: 4-6
fixations; termination `no_frontier`; no repeated fixation; every move exactly
one 5-degree lattice component in yaw and/or pitch with neither component
exceeding 5 deg; **total visited pitch span >=10 deg**, which a horizontal-only
controller cannot reach; >=100 oracle object reference pixels and >=90% valid
object measurement coverage per patch; at least eight agreeing 3D frontier
surfels behind every nonterminal selected gaze, as recorded in
`policy_trace.json`; per post-seed patch >=5,000 matched, overlap median <=10 mm
and p95 <=25 mm, idempotent duplicate replay, no truth-coverage drop beyond
0.5 pp. Final map: analytic finite-cylinder point-to-surface median <=10 mm and
p95 <=30 mm; final curved-surface coverage >=90% (a truth sample on the fixed
256x64 (theta,y) grid counts as covered when a surfel lies within 15 mm, so this
is CURVED-SURFACE completeness, not image coverage); coverage gain over the seed
>=35 pp; only instance 91; >=5,000 surfels with support from >=2 fixations; and
for those, absolute median signed radial error <=7.5 mm.

Cost class: the smoke is Interactive; each full trial is Batch (FSG5's
comparable full trials ran ~1m17s each), so the four fulls plus evaluations sit
inside Batch. Expected ~1,048,576,000 primary camera samples per full trial at
5 fixations, ~4.2e9 across the four if every trial takes five looks.

Likely failure modes, in the order I expect them: (a) the 3D frontier is
extracted from too sparse or too thin a ribbon - the 0.20 m width is only about
8 voxels of 25 mm across, so the 65 mm neighbourhood may see the ribbon's long
edges as the dominant asymmetry and push the gaze across the width rather than
along the arc; (b) the largest-new-area ranking prefers a diagonal purely for
its bounding-box geometry and the <=8-surfel support rule then terminates early,
giving fewer than 4 fixations or a pitch span below 10 deg; (c) the oracle
continuation veto blocks one diagonal component too soon on the rolled ribbon;
(d) only then suspect the renderer or the rolled-mesh integration. Diagnose
before editing. **I will not change the frontier algorithm or any constant, the
lattice, the instrument, the fusion radius, the geometry, textures, seeds, SPP,
vergence, coverage radius or any gate to obtain a pass, and I will not rerender
after a numerical miss.**

**Measured outcome, appended after the run (2026-09-20).**
**`FSG6_INCREMENT6_FAIL`, trial_passes 2/4.** The miss is preserved; Increment 6
is NOT closed and no next experiment is authorized.

`[fsg6-check] SUMMARY passed=7 failed=0`, plus
`[fsg6-scene] PASS up_right=[-13.309,13.309]x[-10.210,10.210] horizontal_ideal_max=0.412 chord_max_mm=0.150`
and `[fsg6-frontier] PASS map_state_changes_2d_direction=true resolved_boundary_stops=true`.
All seven negatives exited 1 with their intended FAIL lines. All thirteen
FSG1-FSG5 regression suites stayed green (24, 29, 34, 48, 37, 46, 7, 8, 4, 5, 7,
7, 6 passed / 0 failed). `git diff 3d5125c` over the FSG1 stereo modules,
`fsg3_surface_map.py`, `rig.py`, `bl_common.py` and `requirements-fsg.txt` is
empty; every manifest records `truth_opened: false`.

**One code fix, the only one in this increment.** `tools/fsg6_run.py` line 64
referenced an undefined name `z` in the loop's defensive revisit guard. `z` is
never assigned, never a parameter, never imported - confirmed by AST walk and by
the actual `NameError`. At step 0 `gazes` is empty so the generator
short-circuits; every step >=1 crashed, making the written 4-6 fixation algorithm
impossible to execute. The guard compares the gaze about to be acquired against
the history, and the variable holding it is `gaze`; changed `z` -> `gaze`, one
token. No constant, threshold, gate or scientific specification touched, and the
guard is strictly stricter afterwards than a crash. The crashed partial is kept
at `previews/fsg6/smoke-diag_up_right-seed701-crashed-nameerror-preserved`.

Smoke (`diag_up_right`/701/small) completed and exited 2 numerically: 6
fixations, `max_fixations`, coverage 87.57%, median 13.836 mm, p95 33.814 mm.
All its misses are resolution-scaled - overlap quality passed throughout (median
3.83-4.79 mm, p95 8.01-10.67 mm, every replay idempotent) and only the absolute
counts and the known FSG1 small-profile measurement fraction (0.796-0.863) fell
short. No exception, so full was not blocked.

Four full trials, each run once, 1,258,291,200 samples each (5,033,164,800
total). `diag_down_left` **passed on both seeds** with empty fail lists:
`(8,8) (3,3) (-2,-2) (-7,-7) (-2,-7) (-7,-2)`, `no_frontier`, final coverage
99.091/99.121%, median 4.643/4.639 mm, p95 14.436/14.446 mm, signed radial
+1.419/+1.431 mm. `diag_up_right` **failed on both seeds** with exactly two fails
each: `3D frontier policy did not terminate by resolving the frontier` and
`fix_04 object measurement coverage`. Its trajectory
`(-8,-8) (-3,-3) (2,2) (7,2) (12,7) (7,7)` still reached 99.139/99.207% coverage
at 4.041/4.055 mm median and 12.784/12.844 mm p95, signed radial +1.687/+1.645 mm.
Pitch span 15.0 deg on **all four** against the >=10 gate; every move one 5-degree
lattice component; no repeats; nonterminal frontier support 21-93 against >=8;
post-seed matched 13,322-25,927, overlap medians 1.76-2.59 mm, p95 5.35-8.20 mm,
all idempotent; largest coverage decrease 0.01 pp; every map pure instance 91
with 31,689-34,780 multi-look surfels.

**Root cause, measured not assumed: the mirror pair is not a monocular mirror.**
The fixtures are an exact 180-degree image-plane rotation as geometry - `up_right L`
and rotated `down_left R` disagree on **0 of 409,600 pixels, IoU 1.000000**, and
likewise `up_right R` vs rotated `down_left L`. But a 180-degree roll maps
(x,y,z) -> (-x,-y,z), which swaps the two eye centres at +/-0.0315 m along X, so
the mirror of the left eye's view is the RIGHT eye's view. The controller reads
only the left-eye oracle mask, so the "mirrored" fixtures differ by the full
binocular parallax - **37.4 px (1.76 deg) on a ribbon only 119 px (5.59 deg)
wide**, 31% of its width. `up_right L` vs rotated `down_left L` disagree on
16.43% of core pixels, IoU 0.732.

The continuation veto then amplifies that into a trajectory difference. Across
the three comparable mirrored fixations the mirrored edge fraction runs
systematically 0.136-0.143 lower on `up_right`, and at the third it crosses the
0.15 threshold: top=0.3914 vs bottom=0.5340, then 0.2391 vs 0.3820, then
**0.0703 vs 0.2066**. `raw_support_L` is 100% true in both bands, so the stereo
mask plays no part - the asymmetry is entirely in the oracle mask the veto
consults. Consequence: on `up_right` the (+5,+5) diagonal is removed at fixation
3, the controller is deflected onto the pure-yaw (+7,+2), then needs (+12,+7) and
(+7,+7); it reaches 99.1% but still has two eligible candidates at fixation 6, so
the budget ends it as `max_fixations`. The same deflection puts fixation 4 at
(+12,+7) where the fovea hangs off the ribbon end, giving measurement coverage
0.8940 - a 0.60 pp miss. Both FAIL lines are downstream of that one vetoed
diagonal. `down_left` keeps all four edges live at its third fixation, runs the
clean diagonal to (-7,-7), hits 99.07% by fixation 4 and stops `no_frontier`.

This is a fixture/rig design property, not an implementation defect and not a
numerical accident: it reproduced identically on both seeds with byte-identical
oracle reference counts, because the oracle mask is ray-traced and
seed-independent. Repairing it needs a change to the fixture design, the
reference eye, or `edge_object_fraction_min` - none of which this handoff
delegates to Code. So the miss stands.

Visuals: `growth.png` shows `up_right` growing lower-left to upper-right and
`down_left` upper-right to lower-left, the mirror direction found unaided.
`growth_truth.png` gives 37.4->55.7->74.9->93.3->99.1->99.1% and
39.8->59.0->80.7->99.1->99.1->99.1%, `down_left` saturating a fixation earlier;
`up_right` panels 4 and 5 are visually indistinguishable (last look +0.04 pp).
`coverage_3d_frontier.png` shows all four rising monotonically to ~99.1%. Each
`surface_map.ply` carries "comment fixed head frame H", has **no `element face`**,
and an independent read gives median cylinder radius **0.75110-0.75120 m against
a true 0.750 m** - ~1.1-1.2 mm outward, matching the signed radial medians and
reproducing FSG5's finding that 12 mm Euclidean fusion does not contract inward.

Cost: smoke run 17.4 s / eval 6.9 s; full runs 1m14.2s, 1m15.5s, 1m16.7s,
1m16.1s; full evaluations ~37 s each; aggregation under a second. Nothing was
tuned - no frontier constant, lattice, instrument, fusion radius, geometry,
texture, seed, SPP, vergence, coverage radius or gate changed, and no rerender
after the numerical miss.

What did hold, and is worth keeping: on all four trials the 3D surfel frontier
drove a genuinely two-dimensional trajectory (pitch span 15.0 deg) that grew a
rolled cylindrical ribbon to ~99.1% curved-surface completeness at 4.04-4.64 mm
median, which the software check confirms a five-look horizontal-only scan cannot
do on this fixture (ideal coverage 0.412). **The frontier representation works.**
What failed is the interaction between the oracle continuation veto and a mirror
pair that is not a mirror monocularly. Stopped for Luiz/Chat.

### 2026-09-20 - FSG6b Increment 6, binocular continuation for the 3D surface frontier: authorized, prospective entry (written before acquisition)

Per `docs/fsg6b-increment6.md` and D-FSG6b appended just above. **Exactly one
architectural element changes: the segmentation-only physical-boundary veto
becomes binocular and eye-swap invariant.** Commands, written before running
them:

    .venv/bin/python tools/dev/check_fsg6b.py
    for n in policy mapstate horizontal monocular flat shift bias purity; do .venv/bin/python tools/dev/check_fsg6b.py --negative "$n"; done
    (all existing FSG1-FSG6a regression checks, unchanged, including check_fsg6.py)
    .venv/bin/python tools/fsg6b_run.py  --out previews/fsg6b/smoke-fresh_up_right-seed809 --profile small --fixture fresh_up_right --seed 809 --device OPTIX
    .venv/bin/python tools/fsg6b_eval.py previews/fsg6b/smoke-fresh_up_right-seed809 --out previews/fsg6b/smoke-fresh_up_right-seed809-evaluation --mode smoke
    (then the four full trials fresh_up_right/809, fresh_up_right/853, fresh_down_left/809, fresh_down_left/853,
     each run once and evaluated, then fsg6b_compare.py over exactly those four metrics.json)

**FSG6a is preserved.** It remains a formal `FSG6_INCREMENT6_FAIL` (2/4); its
Results, log entry, D-FSG6a outcome, README row and all twelve
`previews/fsg6/...` artifact directories are untouched, and the accepted
one-token `z -> gaze` repair is still in place at `tools/fsg6_run.py:64`.
`git diff ea8e962` over the FSG1 stereo modules (`fsg_stereo_supported`,
`fsg_stereo_hdr`, `fsg_stereo`, `fsg_evaluate`, `fsg_geometry`),
`fsg3_surface_map.py`, ALL FSG6a modules (`fsg6_public`, `fsg6_frontier`,
`fsg6_run`, `fsg6_eval`, `fsg6_scene`), `rig.py`, `bl_common.py` and
`requirements-fsg.txt` is EMPTY.

**What I verified by reading the code rather than assuming.** A normalised diff
of `fsg6b_frontier.py` against `fsg6_frontier.py` shows the ONLY functional
change is the new `binocular_edge_evidence` and `choose_next` consuming both
eyes; `edge_evidence`, `_voxel_centroids`, `extract_frontier`,
`_candidate_edge_allowed`, `_new_box_area` and the candidate sort key are
byte-identical. `fsg6b_compare.py` and `fsg6b_render_fix.py` are identical to
their FSG6a counterparts modulo naming; `fsg6b_scene.py` differs only in the
fixture dictionary and its design assertions. `fsg6b_public.SURFACE_FRONTIER`
and `TARGETS` are compared for exact equality against `fsg6_public` by
`check_fsg6b.run_positive` check 1, so the 0.15 threshold and every gate cannot
drift silently. `fsg6b_run.py` imports the EXISTING `fsg3_surface_map`, calls
`compute_once` behind `check_kernel_equivalence` (never `compute_variants`),
imports no fixture geometry and opens no `evaluation_only` asset.

The right eye reaches the policy through outputs the FROZEN instrument already
produces and FSG6a simply discarded: `compute_once` returns a third `state`
value carrying `ids_left`/`ids_right`, and `fsg_stereo.support_mask(c, rec, "R")`
already exists. `fsg6b_run` slices both with the same `rec["crop_xywh"]`
convention the frozen code uses at `fsg_stereo.py:174`, and asserts
`rec["instance_id"] == state["ids_left"][sl]` as a replay check. **No change to
the stereo instrument was needed or made to obtain the second eye.**

Fixtures: two rolled cylindrical ribbons, 48 strips, deliberately NOT exact
mirror copies - `fresh_up_right` (centre z -2.85 m, radius 0.78 m, theta -58 to
+52 deg, height 0.24 m, roll +30 deg, seed gaze (-8,-7), texture tag 47) and
`fresh_down_left` (centre z -2.70 m, radius 0.70 m, theta -50 to +60 deg, height
0.23 m, roll +220 deg, seed gaze (+8,+7), texture tag 53). Object instance 101,
background 102. `fsg6b_scene.self_test` asserts they do NOT collapse to a mirror
pair, which is the whole point: FSG6a's miss was an artifact of a nominal mirror
that was not a monocular mirror, so the validation family must not rely on
mirror symmetry at all. Fresh seeds 809 and 853. The design traces
`(-8,-7)(-3,-2)(2,3)(7,8)` and `(8,7)(3,2)(-2,-3)(-7,-8)` are construction
sanity notes, NOT acceptance criteria; the policy chooses its own trajectories.

Gates, all four trials judged independently and all four required: 4-6
fixations; termination `no_frontier`; no repeated fixation; each move one
5-degree yaw/pitch lattice move; visited pitch span >=10 deg; >=100 oracle object
reference pixels and >=90% valid object measurement coverage per patch; >=8
agreeing 3D frontier surfels behind every nonterminal selected gaze, with the
trace recording both per-eye fractions AND the symmetric combined fraction; per
post-seed patch >=5,000 matched, overlap median <=10 mm, p95 <=25 mm, exact
idempotent replay, no truth-coverage drop beyond 0.5 pp. Final map: analytic
point-to-surface median <=10 mm, p95 <=30 mm, final coverage >=90%, gain over
seed >=35 pp, only instance 101, >=5,000 surfels with support >=2, and for those
absolute median signed radial error <=7.5 mm.

Cost class: smoke Interactive/Batch; each full trial Batch (FSG6a's comparable
full trials ran ~1m15s each), so the four fulls plus evaluations sit inside
Batch. Expected ~1,258,291,200 primary camera samples per full trial at six
fixations.

Likely failure modes, in the order I expect them: (a) the binocular veto is
strictly MORE permissive than the left-eye-only rule, so a candidate that should
have been vetoed at a genuinely resolved boundary may now survive and the run
overruns to `max_fixations` again - the `resolved_boundary_stops` case in
`fsg6b_frontier.self_test` is the existing guard and I will watch termination
closely; (b) the fresh ribbons are wider (0.23-0.24 m vs 0.20 m) and at different
depths/radii, so per-patch measurement coverage and the >=8 frontier support may
behave differently from FSG6a; (c) the non-mirror fixture pair may simply need
different trajectory lengths on the two fixtures, pushing one outside 4-6
fixations; (d) only then suspect the renderer or rolled-mesh integration.
Diagnose before editing. **I will not change the 0.15 threshold, any FSG6a
frontier constant, the instrument, the fusion radius or hash, the lattice, the
geometry, textures, seeds, SPP, vergence, coverage radius or any gate to obtain a
pass, and I will not rerender after a numerical miss.**

**Measured outcome, appended after the run (2026-09-20).**
**`FSG6B_INCREMENT6_FAIL`, trial_passes 2/4.** The miss is preserved; Increment 6
is NOT closed and no next experiment is authorized.

FSG6a is intact: still a formal `FSG6_INCREMENT6_FAIL` (2/4), records untouched,
`z -> gaze` still at `tools/fsg6_run.py:64`, and `git diff ea8e962` over the FSG1
stereo modules, `fsg3_surface_map.py`, all five FSG6a modules, `rig.py`,
`bl_common.py` and `requirements-fsg.txt` is EMPTY.

`[fsg6b-check] SUMMARY passed=8 failed=0`, with
`[fsg6b-scene] PASS up_right=[-14.559,14.033]x[-9.902,9.659] down_left=[-12.902,12.157]x[-11.340,10.770] horizontal_ideal_max=0.471 chord_max_mm=0.156`
and `[fsg6b-frontier] PASS map_state_changes_2d_direction=true eye_swap_invariant=true resolved_boundary_stops=true`.
All eight negatives exited 1, including
`deliberate retired left-eye-only continuation rule detected as eye-swap asymmetric`.
All fifteen FSG1-FSG6a suites green; FSG6a's seven negatives still all exit 1.
Contract equality confirmed directly: `fsg6b_public.SURFACE_FRONTIER ==
fsg6_public.SURFACE_FRONTIER` and `TARGETS == TARGETS` are both exactly True with
NO differing keys, `edge_object_fraction_min` 0.15 in both.

**The binocular repair works and is not what failed.** At fixation 0 of both
`fresh_up_right` trials the left edge measured f_L=0.0000, f_R=0.2414, so
max(f_L,f_R)=0.2414 >= 0.15 permitted a direction the retired left-eye-only rule
would have vetoed. Honest qualification: that rescue fired twice across the four
trials and in neither case did the SELECTED move depend on a rescued edge - the
rule broadened the candidate set but changed no trajectory here. FSG6a's
eye-asymmetry mode did not recur, and FSG6a's `fix_04 object measurement
coverage` miss is gone (every patch 0.9215-0.9485 vs >=0.90).

Four full trials, each run once, 1,258,291,200 samples each (5,033,164,800
total). `fresh_down_left` **passed on both seeds**, empty fail lists:
`(8,7)(3,2)(-2,-3)(-7,-8)(-2,-8)(-7,-3)`, `no_frontier`, coverage 99.225/99.225%,
median 4.260/4.269 mm, p95 14.395/14.411 mm, radial +0.988/+0.965 mm.
`fresh_up_right` **failed on both seeds with ONE fail line each** -
`3D frontier policy did not terminate by resolving the frontier` - while still
reaching 99.683/99.664% coverage at 3.369/3.352 mm median, 13.124/13.117 mm p95,
radial -0.300/-0.282 mm. Pitch span 15.0 deg on all four; nonterminal frontier
support 29-90 vs >=8; post-seed matched 17,172-27,465, overlap medians
1.95-2.57 mm, p95 5.14-8.39 mm, all idempotent; largest coverage decrease 0.00 pp;
maps 71,727-78,340 surfels, all pure instance 101, 36,490-37,288 multi-look.

**Root cause, measured: the conjunctive corner rule blocks a diagonal surface.**
A diagonal move needs BOTH corresponding edge bands to continue, but a narrow
ribbon rolled +30 deg leaves the fovea through a CORNER. At the deflecting
fixation, gaze (+2,+3) on `fresh_up_right`, read from the saved rectified masks:
top band L=0.0000 R=0.0035 (veto); right band L=0.6176 R=0.6004 (permit);
top-right corner L=0.0000 R=0.0900 (veto); **right band top half L=0.7883
R=0.9258**. The object occupies rows 25..255 of 256 and never reaches the top
row, so the `top` veto is CORRECT and both eyes agree - this is not an eye-swap
artifact. Yet 93% of the top half of the right band is object: the surface
plainly continues up-and-right, out of the corner. The (+5,+5) move is blocked,
the controller takes the pure-yaw (+7,+3), and spends an extra fixation
recovering the diagonal at (+12,+8). The cost is exactly the budget:
`fresh_up_right` still has TWO eligible candidates at fixation 6 - (+12,+3) with
90 frontier surfels and (+2,+8) with 63 - because the ribbon truly extends to yaw
+14.03 while the map reaches +12.44. The frontier is not exhausted when
MAX_BUDGET_FIXATIONS=6 ends the run. `fresh_down_left` stops properly: its final
`left` (0.0988) and `top` (0.1039) edges are genuinely resolved in both eyes and
every remaining permitted neighbour is already visited. The two fixtures
diverging is the non-mirror design working as intended.

Worth recording for the next handoff: the FSG6b construction estimate assumed a
four-look diagonal `(-8,-7)(-3,-2)(2,3)(7,8)`, whose fourth step is exactly the
(+5,+5) move the conjunctive rule forbids. `ideal_angular_coverage` models the
fovea as a plain 12x12 box with no veto, so the fixture design check and the veto
semantics disagree about whether that trajectory is even reachable.

This is a **specification question, not an implementation defect**: the
conjunctive requirement is written into the handoff, inherited unchanged from
FSG6a and explicitly frozen for FSG6b. Changing it, the 0.15 threshold, or the
6-fixation budget would alter the scientific specification. **No code fix was
required or made in FSG6b.** Nothing tuned - no threshold, frontier constant,
instrument, fusion radius or hash, lattice, geometry, texture, seed, SPP,
vergence, coverage radius or gate changed, and no rerender after the numerical
miss.

Visuals: growth.png / growth_truth.png show `fresh_up_right` growing lower-left
to upper-right (41.4->58.7->75.3->97.4->99.6->99.7%) and `fresh_down_left`
upper-right to lower-left (37.2->56.5->80.3->99.1->99.1->99.2%), the last two
panels of each visually indistinguishable since the surface is finished by
fixation 4. coverage_3d_frontier.png shows all four rising monotonically. Every
surface_map.ply carries "comment fixed head frame H" with NO `element face`;
independent reads give median radius 0.77914 m vs true 0.780 (`fresh_up_right`)
and 0.70120-0.70122 m vs true 0.700 (`fresh_down_left`) - within 0.9 mm inward
and 1.2 mm outward, no systematic contraction.

Cost: smoke run 17.6 s (loop 17.47 s, Blender 11.86 s) / eval 8.2 s; full runs
1m17.9s, 1m18.4s, 1m24.2s, 1m24.6s (loop 77.71/78.25/84.10/84.51 s, Blender
34.6-35.1 s each); aggregation under a second.

Scope of what holds: the truth-free 3D surfel frontier drove genuinely
two-dimensional gaze on all four trials (pitch span 15.0 deg) and reconstructed
both fresh, deliberately non-mirror ribbons to 99.2-99.7% completeness at
3.35-4.27 mm median, where a five-look horizontal-only controller reaches at most
0.471 ideal coverage. The eye-symmetry repair is proven by check and exercised on
real data. The remaining obstacle to closing Increment 6 is the conjunctive
corner rule in the auxiliary veto. Stopped for Luiz/Chat.

### 2026-09-20 - FSG6c Increment 6, candidate-aligned continuation for the 3D surface frontier: authorized, prospective entry (written before acquisition)

Per `docs/fsg6c-increment6.md` and D-FSG6c appended just above. **Exactly one
policy semantics changes: the diagonal component-conjunction veto becomes
candidate-aligned forward-perimeter continuation.** Commands, written before
running them:

    .venv/bin/python tools/dev/check_fsg6c.py
    for n in policy mapstate horizontal monocular conjunction flat shift bias purity; do .venv/bin/python tools/dev/check_fsg6c.py --negative "$n"; done
    (all existing FSG1-FSG6b regression checks, unchanged, including check_fsg6.py and check_fsg6b.py)
    .venv/bin/python tools/fsg6c_run.py  --out previews/fsg6c/smoke-corner_up_right-seed907 --profile small --fixture corner_up_right --seed 907 --device OPTIX
    .venv/bin/python tools/fsg6c_eval.py previews/fsg6c/smoke-corner_up_right-seed907 --out previews/fsg6c/smoke-corner_up_right-seed907-evaluation --mode smoke
    (then the four full trials corner_up_right/907, corner_up_right/953, corner_down_left/907, corner_down_left/953,
     each run once and evaluated, then fsg6c_compare.py over exactly those four metrics.json)

**FSG6a and FSG6b are preserved.** Both remain formal FAILS (2/4 each); their
Results, log entries, D-FSG6a/D-FSG6b outcomes, README rows and all
`previews/fsg6/...` and `previews/fsg6b/...` artifact directories are untouched.
The accepted `z -> gaze` repair is in place in all three runners
(`fsg6_run.py:64`, `fsg6b_run.py:65`, `fsg6c_run.py:65`) and an AST sweep
confirms no bare `z` load remains in any of them. `git diff 44794a3` over the
FSG1 stereo modules, `fsg3_surface_map.py`, **all five FSG6a modules and all five
FSG6b modules**, `rig.py`, `bl_common.py` and `requirements-fsg.txt` is EMPTY.

**Normalized FSG6b -> FSG6c policy comparison, read from the code.** A
naming-normalized diff of `fsg6c_frontier.py` against `fsg6b_frontier.py` shows
the ONLY functional change is: the new `directional_continuation_evidence()`
(max over direction-compatible edges, returning `compatible_edges`,
`edge_fractions`, `combined_fraction`, `threshold`, `allowed`, `rule`);
`_candidate_edge_allowed` delegating to it; `_retired_component_conjunction_allowed`
retained solely for fail-capable diagnostics; and `choose_next` recording the
`continuation` record on each candidate. **Unchanged and byte-identical**:
`edge_evidence`, `binocular_edge_evidence` (the accepted FSG6b eye-symmetric
per-edge evidence), `_voxel_centroids`, `extract_frontier`, `_new_box_area`, and
the candidate sort key. `fsg6c_run.py`, `fsg6c_eval.py`, `fsg6c_compare.py` and
`fsg6c_render_fix.py` are identical to their FSG6b counterparts modulo naming, so
orchestration, the FSG1 instrument call path and FSG3 fusion are untouched.
`check_fsg6c.run_positive` asserts `SURFACE_FRONTIER` and `TARGETS` exactly equal
`fsg6b_public`, and `source_isolation_control` asserts neither
`fsg6c_frontier.py` nor `fsg6c_run.py` mentions `fsg6c_scene` or
`evaluation_only`.

**The preflight is a real runtime-semantic check, not an angular box.**
`fsg6c_scene.analytic_rectified_oracles` intersects the **continuous analytic
cylinder** (quadratic solve with theta/height clipping) against the two frozen
eye models via `fsg_geometry.rays_h`, remaps through the repository's own
`fsg_stereo.rectification`/`remap` with `crop_xywh`, builds the same
`fsg_stereo.support_mask` the runtime uses, and then calls the exact
`fsg6c_frontier.binocular_edge_evidence` + `directional_continuation_evidence`
the host policy calls. `preflight_transition` reports both the new decision and
the retired conjunction's decision. The `ideal_angular_coverage` figure is kept
only as a geometry-only coverage number; **reachability is now decided by the
runtime semantics**, which is exactly the FSG6b design/runtime inconsistency I
reported and this fixes.

Fixtures: two rolled cylindrical ribbons, 48 strips, deliberately NOT exact
mirror copies - `corner_up_right` (centre z -2.90 m, radius 0.76 m, theta -60 to
+54 deg, height 0.245 m, roll +33 deg, seed gaze (-8,-7), texture tag 61) and
`corner_down_left` (centre z -2.75 m, radius 0.72 m, theta -52 to +62 deg, height
0.235 m, roll +216 deg, seed gaze (+8,+7), texture tag 67). Object instance 111,
background 112. Fresh seeds 907 and 953. The frozen load-bearing control: on
`corner_up_right` at gaze `(2,+3)` the `(+5,+5)` transition must have right-edge
continuation >=0.15 and top-edge continuation <0.15, so FSG6c permits it and the
retired conjunction rejects it. The construction traces are sanity notes, NOT
acceptance criteria; the policy chooses its own trajectories.

Gates, all four trials judged independently and all four required: 4-6
fixations; termination `no_frontier`; no repeated fixation; each move one
5-degree lattice move; visited pitch span >=10 deg; >=100 oracle object reference
pixels and >=90% valid object measurement coverage per patch; >=8 agreeing 3D
frontier surfels behind every nonterminal selected gaze, with the trace recording
per-eye fractions, the binocular per-edge combination AND the selected
candidate's `compatible_edges`/`combined_fraction`/`threshold`/`allowed`; per
post-seed patch >=5,000 matched, overlap median <=10 mm, p95 <=25 mm, exact
idempotent replay, no truth-coverage drop beyond 0.5 pp. Final map: analytic
point-to-surface median <=10 mm, p95 <=30 mm, final coverage >=90%, gain over
seed >=35 pp, only instance 111, >=5,000 surfels with support >=2, and for those
absolute median signed radial error <=7.5 mm.

Cost class: smoke Interactive/Batch; each full trial Batch (FSG6b's comparable
full trials ran ~1m18-1m25s each). Expected ~1,258,291,200 primary camera samples
per full trial at six fixations.

Likely failure modes, in the order I expect them: (a) the candidate-aligned rule
is strictly MORE permissive than the conjunction on diagonals, so a candidate at
a genuinely resolved corner may now survive and a run could again overrun to
`max_fixations` - the `resolved forward perimeter must veto a diagonal candidate`
case in `fsg6c_frontier.self_test` is the guard, and I will watch termination
first; (b) the extra permissiveness could let the controller step off the ribbon
end, costing per-patch measurement coverage as FSG6a's `fix_04` did; (c) the two
non-mirror fixtures may need different trajectory lengths, pushing one outside
4-6 fixations; (d) only then suspect the renderer or rolled-mesh integration.
Diagnose before editing. **I will not change the 0.15 threshold, any FSG6b
frontier constant or gate, the instrument, the fusion radius or hash, the
lattice, the six-fixation budget, the geometry, textures, seeds, SPP, vergence or
coverage radius to obtain a pass, and I will not rerender after a numerical
miss.**

**Measured outcome, appended after the run (2026-09-20).**
**`FSG6C_INCREMENT6_FAIL`.** The diagnostic smoke raised a RUNTIME EXCEPTION,
which per the handoff blocks the full schedule. **No full trial was run.** The
miss is preserved; Increment 6 is NOT closed and no next experiment is authorized.

FSG6a and FSG6b are intact: both still formal FAILS (2/4 each), records
untouched, `z -> gaze` present in all three runners (`fsg6_run.py:64`,
`fsg6b_run.py:65`, `fsg6c_run.py:65`) with no bare `z` load anywhere by AST
sweep. `git diff 44794a3` over the FSG1 stereo modules, `fsg3_surface_map.py`,
all five FSG6a and all five FSG6b modules, `rig.py`, `bl_common.py` and
`requirements-fsg.txt` is EMPTY.

Everything upstream of acquisition passed. `[fsg6c-check] SUMMARY passed=10
failed=0` with `[fsg6c-scene] PASS ... horizontal_ideal_max=0.480
chord_max_mm=0.163 runtime_preflight=true retired_conjunction_rejected_critical=true`
and `[fsg6c-frontier] PASS map_state_changes_2d_direction=true
eye_swap_invariant=true diagonal_corner_continuation=true
resolved_boundary_stops=true`. All nine negatives exited 1, including
`conjunction` and `monocular`. All sixteen FSG1-FSG6b suites green; FSG6a's seven
and FSG6b's eight negatives still all exit 1. `SURFACE_FRONTIER` and `TARGETS`
exactly equal FSG6b with NO differing keys.

The runtime-semantic preflight did its job on what it covered: the critical
`corner_up_right` (2.0,+3.0)->(7.0,+8.0) transition measures right=0.6219,
top=0.0797, combined 0.6219 >= 0.15, FSG6c allowed=True, retired conjunction
allowed=False. Every construction-trace transition is reachable under runtime
semantics (geometry-only ideal coverage 0.9962 / 0.9909). The FSG6b design/runtime
inconsistency I reported last increment is genuinely fixed.

**But the smoke walked off the fixture.** `corner_up_right`/907/small:
step 0 gaze (-8,-7) 7,005 object px; step 1 gaze (-3,**-12**) 1,486 px; step 2
gaze (-8,**-17**) **0 px** -> `ValueError: active FSG6c fixation has too few
object points`. The ribbon spans pitch [-10.188,+9.952].

**Root cause, measured: max() lets one component license the other.** Recomputed
with the runtime functions on the saved rectified masks at the seed gaze (-8,-7):
left=0.0766 veto, right=0.4203 PERMIT, top=0.5156 PERMIT, **bottom=0.0000 in BOTH
eyes**. The down-right direction (+1,-1) has compatible edges {right,bottom}, so
f_cont = max(0.4203, 0.0000) = 0.4203 >= 0.15 and FSG6c PERMITS it, while the
retired component conjunction REJECTS it. The bottom edge is exactly zero - a
provably resolved boundary - yet the move is allowed because max() substitutes
the other component's evidence. Step 1 repeats it with {left,bottom}:
max(0.3109, 0.0000) = 0.3109.

Not small-profile or seed specific. Through the analytic preflight at both
profiles and on both fixtures: corner_up_right small bottom=0.0000/right=0.4203
and full bottom=0.0000/right=0.4258; corner_down_left small top=0.0000/left=0.4609
and full top=0.0000/left=0.4641 - all ALLOWED by FSG6c, all rejected by the
retired rule. The oracle mask is ray-traced and seed-independent, so all four full
trials would have begun from exactly this state. The failure is geometric and
deterministic.

FSG6c is too permissive in precisely the dual way FSG6a/FSG6b were too strict.
The conjunction demanded continuation on EVERY component; max() demands it on
NONE in particular. Neither expresses "the surface leaves through the corner
region between these two edges".

**No code fix was made, and none was permitted.**
`directional_continuation_evidence()` implements the handoff's written rule
exactly - compatible edges from the nonzero components, f_cont = max over them,
permitted iff >= 0.15 - and (+1,-1) legitimately yields max(0.4203, 0.0000). Code
and specification agree, so this is NOT an implementation or orchestration
defect; any repair would change the continuation rule itself, which the handoff
forbids. Nothing was tuned: no threshold, frontier constant, gate, instrument,
fusion radius or hash, lattice, budget, geometry, texture, seed, SPP, vergence or
coverage radius changed, and nothing was rerun after the failure.

**A gap in the check suite, worth fixing in the next handoff.** The shipped
over-permissiveness guard in `fsg6c_frontier.self_test` resolves BOTH compatible
edges (top=0.0000 right=0.0000 -> combined 0.0000, correctly vetoed). The failing
case resolves only ONE: a synthetic mask with bottom=0.0000 and right=0.9062
gives combined 0.9062 and is ALLOWED (the retired rule rejects it). A control in
which one compatible edge is exactly zero while the other is strong would have
failed before any acquisition. The preflight likewise only validated the two
intended traces and the critical up-right transition - it never checked that
off-object directions are correctly REFUSED.

Not reached: no full trajectories, per-patch coverage, overlap statistics,
coverage curves, final map geometry, PLY, aggregate or coverage_3d_frontier.png.
`previews/fsg6c/full-*` does not exist. The only artifacts are the aborted
smoke's three acquisitions, two maps and three patches, preserved at
`previews/fsg6c/smoke-corner_up_right-seed907`.

Cost: smoke 7.9 s, 3 fixations x 13,107,200 = 39,321,600 samples before the
abort; checks and regressions under a minute total. Interactive class only; no
Batch work reached.

What still holds: the FSG6b eye-symmetry repair and the candidate-aligned
DIAGONAL permission both behave as designed where tested - the critical
transition that defeated FSG6b is now correctly permitted (0.6219 against a
0.0797 top edge) and the retired conjunction correctly detected. What fails is
the direction-compatible COMBINATION rule. Stopped for Luiz/Chat.

### 2026-09-20 - FSG6d Increment 6, projected 3D-frontier exit corridors: authorized, prospective entry (written before acquisition)

Per `docs/fsg6d-increment6.md` and D-FSG6d appended just above. **FSG6d changes
the spatial support of the continuation measurement, not its threshold.**
Commands, written before running them:

    .venv/bin/python tools/dev/check_fsg6d.py
    for n in policy mapstate horizontal monocular conjunction componentmax full_edge flat shift bias purity; do .venv/bin/python tools/dev/check_fsg6d.py --negative "$n"; done
    (all existing FSG1-FSG6c regression checks and their negatives, unchanged)
    .venv/bin/python tools/fsg6d_run.py  --out previews/fsg6d/smoke-corridor_up_right-seed1009 --profile small --fixture corridor_up_right --seed 1009 --device OPTIX
    .venv/bin/python tools/fsg6d_eval.py previews/fsg6d/smoke-corridor_up_right-seed1009 --out previews/fsg6d/smoke-corridor_up_right-seed1009-evaluation --mode smoke
    (then the four full trials corridor_up_right/1009, corridor_up_right/1061, corridor_down_left/1009, corridor_down_left/1061,
     each run once and evaluated, then fsg6d_compare.py over exactly those four metrics.json)

**FSG6a, FSG6b and FSG6c are preserved.** All three remain formal FAILS; their
Results, log entries, decision outcomes, README rows and all `previews/fsg6/`,
`previews/fsg6b/` and `previews/fsg6c/` artifacts are untouched. The accepted
`z -> gaze` repair is present in all four runners (`fsg6_run.py:64`,
`fsg6b_run.py:65`, `fsg6c_run.py:65`, `fsg6d_run.py:65`). `git diff fc35bc8` over
the FSG1 stereo modules, `fsg3_surface_map.py`, **all FSG6a, FSG6b and FSG6c
modules**, `rig.py`, `bl_common.py` and `requirements-fsg.txt` is EMPTY.

**Normalized FSG6c -> FSG6d policy comparison, read from the code.** A
naming-normalized diff shows the functional change is confined to the
physical-boundary veto: new `_project_rectified_core`, `_ray_exit`,
`_exit_corridor_mask`, `_corridor_eye_evidence`, `_project_frontier_pairs`,
`_candidate_continuation_from_projected` and `candidate_continuation_evidence`;
`_retired_component_max_allowed` added alongside
`_retired_component_conjunction_allowed` for fail-capable diagnostics; and in
`choose_next` the continuation test now runs AFTER the candidate's supporting
surfels are known, because the corridor is built from those very surfels.
**Verified unchanged**: the candidate sort key is byte-identical
(`-predicted_new_angular_area_deg2, -frontier_score, |dyaw|+|dpitch|, yaw,
pitch`); `alignment_cos_min` is used exactly once in both; the look-ahead point
`target = x + cfg["lookahead_m"] * missing` is computed identically at
`fsg6c_frontier.py:127` and `fsg6d_frontier.py:123` - FSG6d merely **returns** it
as `target_xyz_h` instead of discarding it, which is data plumbing, not a changed
frontier calculation. `_voxel_centroids`, the PCA/tangent asymmetry extraction
and `_new_box_area` are untouched. `fsg6d_eval.py`, `fsg6d_compare.py` and
`fsg6d_render_fix.py` are identical to their FSG6c counterparts modulo naming;
`fsg6d_run.py` differs from `fsg6c_run.py` in exactly one line, the policy label
string written into `policy_trace.json`.

**Constants audit, measured not assumed**: `SURFACE_FRONTIER` and `TARGETS` are
exactly equal to `fsg6c_public` with NO differing keys; `FUSION` equals
`fsg4_public.FUSION` = {0.012, 0.012}; `edge_object_fraction_min` 0.15;
`edge_band_fraction` 0.04; `component_step_deg` 5.0; budget 6; minimum frontier
support 8; `alignment_cos_min` 0.50; vergence 2.10; spp {small 64, full 256};
object 121. The corridor geometry is derived, introducing no new constant:
core 128 -> longitudinal band 5 px and transverse half-width 2 px; core 256 ->
10 px and 5 px.

**The check suite closes the gap I reported after FSG6c.**
`fsg6d_scene.self_test` now enumerates EVERY neighbour at EVERY construction
state and requires that any direction the corridor permits lands on a next view
with at least the frozen 100 oracle reference pixels IN EACH EYE - precisely the
control whose absence let FSG6c walk off the fixture unnoticed until acquisition.
`check_fsg6d.projection_control` verifies `_project_rectified_core` against
OpenCV `undistortPoints` to 1e-9. `historical_bracket_control` requires both
historical defects to stay fixed at once: the valid FSG6b-style corner
continuation must survive AND FSG6c-style one-component licensing must be
rejected. `source_isolation_control` asserts neither `fsg6d_frontier.py` nor
`fsg6d_run.py` mentions `fsg6d_scene` or `evaluation_only`.

Fixtures: two rolled cylindrical ribbons, 48 strips, deliberately NOT mirrors -
`corridor_up_right` (radius 0.74 m, centre z -2.86 m, arc -58 to +55 deg, height
0.252 m, roll +29 deg, seed gaze (-8,-7)) and `corridor_down_left` (radius 0.70 m,
centre z -2.70 m, arc -50 to +63 deg, height 0.246 m, roll +211 deg, seed gaze
(+8,+7)). Object 121, background 122. Fresh seeds 1009 and 1061. Construction
traces are fixture-design checks only; the policy chooses its own trajectories.

Gates, all four trials judged independently and all four required: 4-6 fixations;
termination `no_frontier`; no repeated fixation; each move one nonzero 5-degree
lattice step; pitch span >=10 deg; >=100 oracle object reference pixels and >=90%
object measurement coverage per patch; >=8 agreeing 3D frontier surfels behind
every nonterminal selected gaze; per post-seed patch >=5,000 matched, overlap
median <=10 mm, p95 <=25 mm, idempotent replay, no coverage drop beyond 0.5 pp;
final analytic median <=10 mm, p95 <=30 mm, coverage >=90%, gain >=35 pp, only
instance 121, >=5,000 multi-look surfels, |signed radial median| <=7.5 mm.

Cost class: smoke Interactive/Batch; each full trial Batch (FSG6b's comparable
fulls ran ~1m18-1m25s). Expected ~1,258,291,200 samples per full trial at six
fixations.

Likely failure modes, in the order I expect them: (a) the corridor is a much
smaller sample than a whole edge band - at small profile it is roughly 5 px long
and 5 px wide per ray - so its object fraction may be noisy or its support
denominator near zero, making the veto erratic rather than wrong; (b) requiring
exits in the candidate's own forward sector may over-restrict when the projected
frontier rays are nearly parallel to an edge, stopping early at `no_frontier`
below 4 fixations; (c) the corridor may be too permissive in a new way, letting
the controller step off the ribbon end and costing per-patch measurement
coverage; (d) only then suspect projection/rectification or the renderer.
Diagnose before editing. **I will not change the 0.15 threshold, the 0.04 band
fraction, any frontier constant, the ranking, the instrument, the fusion radius
or hash, the lattice, the six-fixation budget, the geometry, textures, seeds,
SPP, vergence, coverage radius or any gate to obtain a pass, and I will not
rerender after a numerical miss. If the code implements the written rule and the
rule fails, I will preserve that as a specification result and stop.**

**Measured outcome, appended after the run (2026-09-20).**
**`FSG6D_INCREMENT6_FAIL`, trial_passes 0/4.** Every trial fails on **exactly one
gate, the same one**: termination `max_fixations` instead of `no_frontier`. The
miss is preserved; Increment 6 is NOT closed and no next experiment is authorized.

FSG6a, FSG6b and FSG6c are intact: all three still formal FAILS, records
untouched, `z -> gaze` present in all four runners. `git diff fc35bc8` over the
FSG1 stereo modules, `fsg3_surface_map.py`, all FSG6a/FSG6b/FSG6c modules,
`rig.py`, `bl_common.py` and `requirements-fsg.txt` is EMPTY.

`[fsg6d-check] SUMMARY passed=11 failed=0` with
`[fsg6d-scene] PASS ... horizontal_ideal_max=0.460 chord_max_mm=0.156
corridor_preflight=true all_permitted_neighbours_population_checked=true` and
`[fsg6d-frontier] PASS map_state_changes_2d_direction=true eye_swap_invariant=true
projected_frontier_corridor=true one_component_cannot_license_other=true
resolved_boundary_stops=true`. All eleven negatives exited 1, including
`conjunction`, `componentmax` and `full_edge`. All seventeen FSG1-FSG6c suites
green; FSG6a's seven, FSG6b's eight and FSG6c's nine negatives all still exit 1.
`SURFACE_FRONTIER` and `TARGETS` exactly equal FSG6c with NO differing keys.

Corridor preflight: every construction transition reachable under the exact
runtime rasterizer (combined 0.7167-1.0000 over 24-36 projected rays, 113-141
support px). Enumerating ALL neighbours at ALL construction states, 24 and 23
directions are permitted and the worst destination still carries 2,151/2,269
oracle reference pixels against the >=100 gate - the control whose absence let
FSG6c walk off the fixture, now present and passing.

Four full trials, each once, 1,258,291,200 samples each (5,033,164,800 total).
`corridor_up_right` both seeds: `(-8,-7)(-3,-2)(2,3)(7,8)(12,8)(12,3)`, coverage
98.987/99.042%, median 3.476/3.463 mm, p95 12.691/12.657 mm, radial
+0.460/+0.445 mm. `corridor_down_left` both seeds:
`(8,7)(3,2)(-2,-3)(-7,-8)(-12,-8)(-12,-3)`, coverage 98.676/98.712%, median
3.933/3.938 mm, p95 13.371/13.359 mm, radial +0.718/+0.728 mm. **Every other gate
passes on every trial**: pitch span 15.0 deg, yaw span 20.0, one 5-deg step per
move, no repeats, frontier support 23-69 (>=8), per-patch measurement coverage
**0.9114-0.9503** (>=0.90), post-seed matched 11,387-20,222, overlap medians
1.97-3.20 mm, p95 4.77-9.90 mm, all idempotent, largest coverage decrease
0.00 pp, gain 60.40-63.53 pp, maps 76,259-78,092 surfels all pure instance 121,
32,441-33,215 multi-look.

**The corridor rule works and is not what failed.** At the third fixation of
every trial it permitted the diagonal the retired FSG6b conjunction would have
vetoed: up_right at (+2,+3) corridor 0.7031 allowed vs retired conjunction False
with full edges left=0.4445 right=0.6250 **top=0.0000** bottom=0.5629; down_left
at (-2,-3) corridor 0.7787 allowed vs False with **bottom=0.0535**. Coverage
jumps 74.47->96.97% and 75.52->98.44% at that step. The FSG6c defect also does
not recur: no trial ever steps off the ribbon, and the corridor veto is
demonstrably active, rejecting 4 of 8 neighbours at the final fixation of every
trial. Legacy full-edge evidence was computed for diagnosis only and never
entered selection.

**Root cause, measured: the 3D frontier never resolves on a thin ribbon.**
Frontier counts by step: up_right [207,214,206,189,157,164], down_left
[195,215,189,177,151,163], while coverage goes 38.6% -> 99.0%. The population
stays ~150-215 throughout. `extract_frontier` marks a voxel as frontier from
tangent asymmetry of its in-view neighbourhood, and these ribbons are only about
6-7 degrees wide across a 12-degree fovea, so every fixation sees long lateral
ribbon boundaries that read as frontier however complete the reconstruction is.
Termination can therefore only come from the candidate set emptying. Recomputed
exclusion breakdown at the final fixation: up_right/1009 at (+12,+3) - visited 2,
corridor_veto 4, **ELIGIBLE 2** ((+7,+3) sup=23 corridor=0.4909, (+7,-2) sup=9
corridor=0.2323); down_left/1009 at (-12,-3) - visited 2, support<8 1,
corridor_veto 4, **ELIGIBLE 1** ((-7,-3) sup=31 corridor=0.9208). The survivors
are INTERIOR lattice cells inside the already-swept region - (+7,+3) is the
centre of the square bounded by the visited (2,3),(7,8),(12,8),(12,3) - with
small predicted new area (22.1 and 7.7 deg^2) but genuine frontier support and a
permitted corridor. The policy is not wandering; it correctly reports that a
little unreconstructed surface remains. It simply never runs out within six
fixations. Note four fixations already suffice numerically: at step 3 coverage is
96.97-98.57% with gain 58.4-63.4 pp, inside every coverage gate.

**This is a specification result, not an implementation defect, and no code fix
was made.** The code implements the written FSG6d rule exactly and the rule did
what it promised - it fixed the diagonal-corner veto without reintroducing
one-component licensing. What fails is the interaction of the FROZEN
frontier-extraction termination behaviour with the FROZEN `no_frontier` gate and
the FROZEN six-fixation budget, none of which FSG6d was permitted to vary.
Nothing was tuned: no 0.15 threshold, 0.04 band fraction, frontier constant,
ranking, instrument, fusion radius or hash, lattice, budget, geometry, texture,
seed, SPP, vergence, coverage radius or gate changed; no rerender after the
numerical miss.

Visuals: growth.png / growth_truth.png show both fixtures growing along their
diagonals - up_right 38.6->57.0->74.5->97.0->98.2->99.0%, down_left
35.2->54.7->75.5->98.4->98.6->98.7% - the last two panels of each nearly
indistinguishable since the surface is essentially complete after four looks.
coverage_3d_frontier.png shows all four rising monotonically and saturating.
Every surface_map.ply carries "comment fixed head frame H" with NO `element
face`; independent reads give median radius **0.74001-0.74005 m vs true 0.740**
and **0.70095-0.70096 m vs true 0.700** - sub-millimetre, the best radial
agreement of any FSG6 increment.

Cost: smoke run 17.5 s (loop 17.27 s, Blender 11.89 s) / eval 8.3 s; full runs
1m8.5s, 1m8.5s, 1m12.6s, 1m13.1s (loop 68.42/68.38/72.44/72.96 s, Blender
34.7-35.0 s each); aggregation under a second.

Scope of what holds: the projected candidate-local corridor veto is the first of
the four FSG6 continuation rules that is simultaneously eye-symmetric, permissive
to a genuine corner exit, and restrictive against one-component licensing -
demonstrated by check AND on all four acquisitions. With it the 3D surfel
frontier produced clean diagonal trajectories reconstructing both fresh ribbons
to 98.7-99.0% at 3.46-3.94 mm median with sub-millimetre radial agreement. **The
open question is no longer the veto but termination**: how a frontier defined by
local tangent asymmetry should ever declare a thin ribbon finished. Stopped for
Luiz/Chat.

### 2026-09-20 - FSG6e Increment 6, persistent OPEN frontier state: authorized, prospective entry (written before acquisition)

Per `docs/fsg6e-increment6.md` and D-FSG6e appended just above. **FSG6e changes
the state of a raw frontier, not the FSG6d corridor and not any numerical gate.**
Commands, written before running them:

    .venv/bin/python tools/dev/check_fsg6e.py
    for n in policy mapstate horizontal monocular conjunction componentmax full_edge rawtermination forget_history stereo_hole flat shift bias purity; do .venv/bin/python tools/dev/check_fsg6e.py --negative "$n"; done
    (all existing FSG1-FSG6d regression checks and their negatives, unchanged)
    .venv/bin/python tools/fsg6e_run.py  --out previews/fsg6e/smoke-closure_up_right-seed1123 --profile small --fixture closure_up_right --seed 1123 --device OPTIX
    .venv/bin/python tools/fsg6e_eval.py previews/fsg6e/smoke-closure_up_right-seed1123 --out previews/fsg6e/smoke-closure_up_right-seed1123-evaluation --mode smoke
    (then the four full trials closure_up_right/1123, closure_up_right/1181, closure_down_left/1123, closure_down_left/1181,
     each run once and evaluated, then fsg6e_compare.py over exactly those four metrics.json)

**FSG6a-FSG6d are preserved.** All four remain formal FAILS; their Results, log
entries, decision outcomes, README rows and all `previews/fsg6/`,
`previews/fsg6b/`, `previews/fsg6c/` and `previews/fsg6d/` artifacts are
untouched. The accepted `z -> gaze` repair is present in all five runners
(`fsg6_run.py:64`, `fsg6b/c/d/e_run.py:65`). `git diff ab13eae` over the FSG1
stereo modules, `fsg3_surface_map.py`, **all FSG6a, FSG6b, FSG6c and FSG6d
modules**, `rig.py`, `bl_common.py` and `requirements-fsg.txt` is EMPTY.

**Normalized FSG6d -> FSG6e policy comparison, read from the code.** The
functional change is confined to the OPEN-state filter plus completed binocular
observation-history plumbing: new `_target_mapped_mask` (frozen 12 mm radius and
12 mm hash cell, strict `<`), `_target_patch_eye_evidence` (patch radius derived
from the already-frozen `edge_band_fraction`, exactly as the FSG6d corridor
derives its width) and `classify_frontier_state` (three-way); `choose_next` now
takes `observation_history` and computes `support = raw_support & open`, plus
descriptive raw/map-resolved/boundary-resolved counts. **Verified frozen by
`inspect.getsource` text-identity (modulo module naming)**: `extract_frontier`,
`_project_rectified_core`, `_ray_exit`, `_exit_corridor_mask`,
`_corridor_eye_evidence`, `_project_frontier_pairs`,
`_candidate_continuation_from_projected`, `_new_box_area`, `_voxel_centroids`,
`edge_evidence`, `binocular_edge_evidence` - all identical. The candidate sort
key is verbatim identical; `alignment_cos_min` is used exactly once in both; the
0.12 m look-ahead line is identical. `angular_coordinates` differs only in an
error-message string ("FSG6d policy" -> "FSG6e policy"). `fsg6e_compare.py` and
`fsg6e_render_fix.py` are identical to FSG6d modulo naming; `fsg6e_run.py`
differs only by accumulating `observation_history` (deep copies of both eyes'
rectified masks plus calibration), passing it to `choose_next`, and the policy
label/`policy_inputs` strings; `fsg6e_eval.py` differs only by adding the
descriptive `frontier_state_by_fixation` block - **the `fails` gate logic is
unchanged, so FSG6e adds no acceptance gate.**

**Constants audit, measured not assumed**: `SURFACE_FRONTIER` and `TARGETS` are
exactly equal to `fsg6d_public` with NO differing keys; `FUSION` equals
`fsg4_public.FUSION` = {0.012, 0.012} and is precisely what MAP_RESOLVED reuses;
`edge_object_fraction_min` 0.15; `edge_band_fraction` 0.04; `lookahead_m` 0.12;
step 5.0; budget 6; minimum support 8; `alignment_cos_min` 0.50; vergence 2.10;
object 131. BOUNDARY_RESOLVED patch radius is derived, not new: core 128 ->
band 5 px, radius 2 px; core 256 -> 10 px, 5 px.

**The evaluator-only closed-loop preflight makes the new state load-bearing.**
`fsg6e_scene.persistent_policy_preflight` builds an idealized map and history
from analytic cylinder truth on the evaluator side, then calls the **actual
runtime `choose_next`** for every next gaze. It must terminate in 4-6 fixations
with `no_frontier`, reach >=90% ideal coverage and >=10 degrees pitch span, and -
the load-bearing part - **removing completed binocular history from the same
final state must recreate at least one eligible raw-frontier candidate**, which
reproduces the FSG6d termination gap. The positive check asserts both `pf["stop"]`
and `not pf["without_history_stops"]`. Design-only numbers, not scientific
results: six-look traces with ideal coverage 0.9996 and 1.0000.

Fixtures: two rolled cylindrical ribbons, 48 strips, deliberately NOT mirrors -
`closure_up_right` (radius 0.77 m, centre z -2.88 m, arc -57 to +57 deg, height
0.250 m, roll +31 deg, seed gaze (-8,-7)) and `closure_down_left` (radius 0.69 m,
centre z -2.72 m, arc -51 to +64 deg, height 0.248 m, roll +214 deg, seed gaze
(+8,+7)). Object 131, background 132. Fresh seeds 1123 and 1181.

Gates, all four trials judged independently and all four required, all inherited
unchanged from FSG6d: 4-6 fixations; termination `no_frontier`; no repeated
fixation; each move one nonzero 5-degree lattice step; pitch span >=10 deg; >=100
oracle object reference pixels and >=90% object measurement coverage per patch;
**>=8 OPEN** 3D frontier surfels behind every nonterminal selected gaze; per
post-seed patch >=5,000 matched, overlap median <=10 mm, p95 <=25 mm, idempotent
replay, no coverage drop beyond 0.5 pp; final analytic median <=10 mm, p95
<=30 mm, coverage >=90%, gain >=35 pp, only instance 131, >=5,000 multi-look
surfels, |signed radial median| <=7.5 mm.

Cost class: smoke Interactive/Batch; each full trial Batch (FSG6d's fulls ran
~1m9-1m13s). Expected ~1,258,291,200 samples per full trial at six fixations,
fewer if the new rule terminates earlier - which is the point of the experiment.

Likely failure modes, in the order I expect them: (a) BOUNDARY_RESOLVED is too
eager on real Cycles data - a supported binocular patch just past the true ribbon
edge reads as background and resolves a frontier that is actually still open,
terminating below 4 fixations with coverage under 90%; (b) MAP_RESOLVED is too
eager because the 0.12 m look-ahead lands back inside the already-fused ribbon on
a strongly curved surface, collapsing OPEN support below 8 prematurely; (c) the
opposite - real stereo holes keep targets OPEN (correctly, per the stereo-hole
guard) and the run again exhausts the budget as FSG6d did; (d) history
accumulation over six fixations is slow or memory-heavy enough to perturb the
loop; (e) only then suspect projection or the renderer. Diagnose before editing.
**I will not change the 12 mm association radius or hash, the 0.15 threshold, the
0.04 scale, any frontier constant, the FSG6d corridor, the ranking, the
instrument, FSG3 fusion, the lattice, the six-fixation budget, the geometry,
textures, seeds, SPP, vergence, coverage radius or any gate to obtain a pass; I
will add no completeness-percentage stop, low-gain stop or budget extension; and
I will not rerender after a numerical miss. If the code faithfully implements the
written persistent-state rule and that rule fails, I will preserve the
specification result and stop.**

**Measured outcome, appended after the run (2026-09-20).**
**`FSG6E_INCREMENT6_FAIL`, trial_passes 2/4.** The miss is preserved; Increment 6
is NOT closed and no next experiment is authorized.

**But the central FSG6e claim is demonstrated on real acquisitions.** Both
`closure_down_left` trials terminated `no_frontier` with the raw
tangent-asymmetry frontier still at **169-170** surfels while OPEN had collapsed
to **6-9** and every candidate direction fell below the frozen minimum of eight.
So yes: **raw frontier count can remain nonzero and high while OPEN resolves and
`no_frontier` occurs** - precisely what FSG6d could not do.

FSG6a-FSG6d are intact: all four still formal FAILS, records untouched,
`z -> gaze` present in all five runners. `git diff ab13eae` over the FSG1 stereo
modules, `fsg3_surface_map.py`, all FSG6a/6b/6c/6d modules, `rig.py`,
`bl_common.py` and `requirements-fsg.txt` is EMPTY.

`[fsg6e-check] SUMMARY passed=13 failed=0` with
`[fsg6e-scene] PASS ... horizontal_ideal_max=0.452 chord_max_mm=0.165
corridor_preflight=true persistent_state_preflight=true
raw_frontier_termination_rejected=true traces={closure_up_right:6fix/0.9996,
closure_down_left:6fix/1.0000}` and `[fsg6e-frontier] PASS
map_state_changes_2d_direction=true persistent_state_three_way=true
historical_boundary_state=true stereo_hole_not_boundary=true
eye_swap_invariant=true projected_frontier_corridor=true
resolved_boundary_stops=true`. All fourteen negatives exited 1, including
`rawtermination`, `forget_history` and `stereo_hole`. All eighteen FSG1-FSG6d
suites green; FSG6a's 7, FSG6b's 8, FSG6c's 9 and FSG6d's 11 negatives all still
exit 1. `SURFACE_FRONTIER` and `TARGETS` exactly equal FSG6d with NO differing
keys, and `inspect.getsource` confirms all eleven settled FSG6d
corridor/extraction/ranking helpers are text-identical modulo module naming.

Closed-loop preflight (**design/plumbing only, not a scientific result**): raw
152,120,109,136,124,133 with OPEN 84,68,76,62,39,**2** on `closure_up_right` and
raw 128,117,105,148,131,135 with OPEN 68,70,75,65,34,**6** on
`closure_down_left`, both terminating `no_frontier` in six fixations at ideal
coverage 0.9996/1.0000; and the load-bearing control - removing completed history
from the same final state leaves 1 candidate and does not stop - reproducing the
FSG6d gap.

Smoke (`closure_up_right`/1123/small) completed, exit 2, numerical only: same
trajectory, `max_fixations`, coverage 90.73%, median 8.072 mm, p95 29.214 mm.
State raw 233-265 with OPEN 141,121,120,124,127,86 - **OPEN does not collapse at
small profile**, because measurement coverage is only 0.842-0.897 and the
hole-ridden map generates far more raw frontier. This is failure mode (c) from
the prospective entry, and it is resolution, not rule.

Four full trials, each once, 1,258,291,200 samples each (5,033,164,800 total).
`closure_down_left` **passed on both seeds** with empty fail lists:
`(8,7)(3,2)(-2,-3)(-7,-8)(-12,-8)(-12,-3)`, `no_frontier`, coverage
98.639/98.840%, median 4.506/4.507 mm, p95 14.714/14.835 mm, radial
-2.811/-2.842 mm. `closure_up_right` failed on both:
seed 1123 `(-8,-7)(-3,-2)(2,3)(7,8)(12,8)(12,3)` with ONE fail line (termination),
coverage 98.718%, median 3.808 mm; seed 1181
`(-8,-7)(-3,-2)(2,3)(7,8)(12,13)(17,13)` with five, coverage 95.923%.

Frontier state raw/map_res/bnd_res/OPEN/cands:
up_right/1123 (215,0,91,124,5)(205,2,111,92,7)(181,7,73,101,5)(208,9,105,94,3)(173,4,103,66,2)(187,4,167,16,1)
up_right/1181 (220,0,92,128,5)(208,8,102,98,7)(188,10,68,110,6)(210,11,107,92,4)(86,0,72,14,3)(43,0,27,16,1)
down_left/1123 (185,0,81,104,3)(228,9,79,140,5)(215,14,54,147,6)(192,3,102,87,3)(162,0,111,51,2)(170,0,161,9,0)
down_left/1181 (187,0,78,109,3)(227,15,73,139,5)(214,11,56,147,6)(191,2,105,84,3)(157,0,108,49,1)(169,0,163,6,0)

**How down_left terminates**, enumerated at the final fixation with the runtime
functions: at (-12,-3), raw=170, bnd_res=161, OPEN=9; per-direction raw support
is 8-100 but OPEN is 0-7 on every unvisited neighbour, all below the frozen 8, so
`no_frontier` fires. The mechanism is exactly as designed.

**Why up_right/1123 failed.** OPEN collapsed 124 -> 16 and candidates 5 -> 1, but
one survived: (12,-2) with 96 raw aligned surfels of which **82 BOUNDARY_RESOLVED
and 3 MAP_RESOLVED**, leaving **11 OPEN against the frozen minimum of 8**. The
filter removed 85 of 96; three more resolutions would have ended the run. Its
corridor was only 0.2252.

**Why up_right/1181 failed differently.** At fixation 3, gaze (7,8), the candidate
(12,13) was admitted and selected despite the weakest support of the four
(**8 OPEN, exactly the minimum**, from 25 raw) and the weakest corridor (0.3230),
because `predicted_new_angular_area` is the primary sort key and (12,13) scores
134.26 against 103.65, 73.04 and 15.09. (12,13) is above the fixture's +9.942 deg
pitch bound, so fixations 4 and 5 fell off the ribbon: measurement coverage
0.8268 and 0.6650, matched 3,879 and 404, coverage flat at 95.9%.

**The two seeds diverge on a knife edge.** Recomputed at the identical state, the
(12,13) corridor fraction is 0.1490 (seed 1123, L f=0.1490 obj=138 sup=926
rays=6, R f=0.0000) versus 0.3230 (seed 1181, L f=0.3230 obj=208 sup=644 rays=6,
R f=0.0000). Both have OPEN support >= 8 (10 and 8). The decisive quantity is a
corridor fraction computed from only **six** projected frontier rays, straddling
the frozen 0.15 threshold under a Monte-Carlo seed change, with the right eye
contributing exactly 0.0000 in both.

**This is a specification result, not an implementation defect, and no code fix
was made.** The code faithfully implements the written persistent-state rule; the
OPEN filter demonstrably works (25 -> 8 and 29 -> 10 on that very candidate, 170
-> 9 overall) and delivers clean truth-free `no_frontier` on both down_left
trials. What fails is the interaction of that correctly-implemented rule with
three FROZEN pieces FSG6e could not vary: the FSG6d corridor evaluated on a
six-ray sample, the `predicted_new_angular_area` primary sort key that rewards
the most extreme move, and the minimum support of exactly 8. Nothing was tuned -
no 12 mm radius or hash, 0.15 threshold, 0.04 scale, frontier constant, corridor,
ranking, instrument, FSG3 fusion, lattice, budget, geometry, texture, seed, SPP,
vergence, coverage radius or gate changed; no completeness-percentage stop,
low-gain stop or budget extension added; no rerender after a numerical miss.

Visuals: growth_truth.png shows down_left sweeping cleanly
(35.7->55.1->77.3->98.6->98.7->98.6%) and up_right/1181 visibly stalling after
fixation 3 (95.9% flat for three panels) as the gaze leaves the ribbon.
coverage_3d_frontier.png shows three curves saturating near 98.6-98.8% and the
1181 curve flat at 95.9%. Every surface_map.ply carries "comment fixed head frame
H" with NO `element face`; independent reads give median radius 0.77106 m vs true
0.770 and 0.68780-0.68782 m vs true 0.690 (+1.1 mm and -1.2 mm).

Cost: smoke run 17.5 s (loop 17.34 s, Blender 11.81 s) / eval 8.5 s; full runs
1m10.5s, 1m0.6s, 1m11.4s, 1m10.9s (loop 70.36/60.43/71.28/70.75 s, Blender
34.4-34.7 s each); aggregation under a second.

Scope of what holds: FSG6e answered its own question affirmatively on half the
prospectively fixed set, visibly in the diagnostics rather than by inference -
the observer terminated from its own persistent 3D memory and completed
binocular observations while the raw geometric frontier stood at 169-170. The
distinction between a geometric one-sided surface boundary and an unresolved
exploration frontier is representable with the frozen 12 mm association and the
frozen 0.15 threshold, with no new numerical constant. What is NOT established is
robustness: on `closure_up_right` the decision rides on a six-ray corridor sample
and a support count of exactly 8, and a seed change flips the trajectory off the
surface. Stopped for Luiz/Chat.

### 2026-09-20 - FSG6f Increment 6, candidate-level frontier-state consensus: authorized, prospective entry (written before acquisition)

Per `docs/fsg6f-increment6.md` and D-FSG6f appended just above. **FSG6f changes
exactly one scientific abstraction: candidate-level aggregation of the frozen
FSG6e persistent surfel states.** A candidate is exploration-open only when
`N_OPEN > N_MAP + N_BOUNDARY`, independently retaining the frozen `N_OPEN >= 8`
gate; ties are resolved, not open. Commands, written before running them:

    .venv/bin/python tools/dev/check_fsg6f.py
    for n in policy mapstate horizontal monocular conjunction componentmax full_edge rawtermination forget_history stereo_hole anyopen flat shift bias purity; do .venv/bin/python tools/dev/check_fsg6f.py --negative "$n"; done
    (all existing FSG1-FSG6e regression checks and their negatives, unchanged)
    .venv/bin/python tools/fsg6f_run.py  --out previews/fsg6f/smoke-consensus_up_right-seed1237 --profile small --fixture consensus_up_right --seed 1237 --device OPTIX
    .venv/bin/python tools/fsg6f_eval.py previews/fsg6f/smoke-consensus_up_right-seed1237 --out previews/fsg6f/smoke-consensus_up_right-seed1237-evaluation --mode smoke
    (then the four full trials consensus_up_right/1237, consensus_up_right/1291, consensus_down_left/1237, consensus_down_left/1291,
     each run once and evaluated, then fsg6f_compare.py over exactly those four metrics.json)

**FSG6a-FSG6e are preserved.** All five remain formal FAILS; their Results, log
entries, decision outcomes, README rows and all `previews/fsg6{,b,c,d,e}/`
artifacts are untouched. The accepted `z -> gaze` repair is present in all six
runners (`fsg6_run.py:64`, `fsg6b/c/d/e/f_run.py:65`). `git diff 62fab1d` over
the FSG1 stereo modules, `fsg3_surface_map.py`, **all FSG6a, FSG6b, FSG6c, FSG6d
and FSG6e modules**, `rig.py`, `bl_common.py` and `requirements-fsg.txt` is EMPTY.

**Normalized FSG6e -> FSG6f comparison, read from the code.** The functional
change is only candidate state consensus plus diagnostics: new
`candidate_state_consensus(n_open, n_map, n_boundary)` returning
`allowed = n_open > n_map + n_boundary`; `_retired_any_open_allowed` kept solely
as a diagnostic negative control; in `choose_next` an exhaustiveness assertion
that `raw == open + map_resolved + boundary_resolved`, the consensus gate, and
`consensus_rejected_candidates` / `consensus_rejected_candidate_count` /
`candidates_before_consensus_count` diagnostics. **Verified frozen by
`inspect.getsource` text-identity (modulo module naming), 14 helpers, none
drifted**: `extract_frontier`, `classify_frontier_state`, `_target_mapped_mask`,
`_target_patch_eye_evidence`, `_project_rectified_core`, `_ray_exit`,
`_exit_corridor_mask`, `_corridor_eye_evidence`, `_project_frontier_pairs`,
`_candidate_continuation_from_projected`, `_new_box_area`, `_voxel_centroids`,
`edge_evidence`, `binocular_edge_evidence`. The candidate sort key is literally
identical and `check_fsg6f.frozen_algorithm_control` asserts it by string match.
`fsg6f_compare.py` and `fsg6f_render_fix.py` are identical to FSG6e modulo
naming; `fsg6f_run.py` differs only in the policy label string; `fsg6f_eval.py`
adds the consensus diagnostics and exactly **one** new fail line, `policy
decision {i} lacks OPEN-majority candidate consensus`, which is the gate the
handoff itself prescribes.

**Ordering note, verified in source.** A candidate is accepted iff it passes
`N_OPEN >= 8` **and** the FSG6d corridor **and** consensus. The implementation
evaluates the corridor before recording the consensus rejection, so the accepted
set is exactly as specified, and `consensus_rejected_candidates` is precisely the
set FSG6e would have accepted - which makes the required "would have passed the
old rule" diagnostic exact rather than reconstructed.

**Constants audit, measured not assumed**: `SURFACE_FRONTIER` and `TARGETS`
exactly equal `fsg6e_public` with NO differing keys; `FUSION` equals
`fsg4_public.FUSION` = {0.012, 0.012}; 0.15 threshold; 0.04 scale; 0.12 m
look-ahead; step 5.0; budget 6; minimum OPEN support 8; `alignment_cos_min` 0.50;
vergence 2.10; object 141. The consensus source contains no `0.5` and the core
expression `bool(no > nr)` is present.

**The rule was validated against the preserved FSG6e record before acquisition.**
All five productive `closure_up_right/1123` moves remain eligible - (45,0,1),
(41,1,17), (31,5,14), (61,1,1), (60,3,20) - while both pathological survivors are
rejected: **(11,3,82) -> resolved 85 of 96 raw, allowed=False** and
**(8,1,16) -> resolved 17 of 25 raw, allowed=False**, each of which the retired
any-OPEN>=8 rule would still have admitted. Tie behaviour confirmed: (9,4,4)
allowed, (8,4,4) rejected. **These FSG6e numbers are development controls only
and are not FSG6f validation.**

Fixtures: two rolled cylindrical ribbons, 48 strips, deliberately NOT mirrors -
`consensus_up_right` (radius 0.75 m, centre z -2.91 m, arc -59 to +58 deg, height
0.252 m, roll +28 deg, seed gaze (-8,-7)) and `consensus_down_left` (radius
0.71 m, centre z -2.69 m, arc -52 to +65 deg, height 0.250 m, roll +216 deg, seed
gaze (+8,+7)). Object 141, background 142. Fresh seeds 1237 and 1291.

Gates, all four trials judged independently and all four required, all inherited
from FSG6e plus the one prescribed addition: 4-6 fixations; termination
`no_frontier`; no repeated fixation; one nonzero 5-degree lattice step per move;
pitch span >=10 deg; >=100 oracle object reference pixels and >=90% object
measurement coverage per patch; **>=8 OPEN** frontier surfels and **strict
OPEN-majority consensus** behind every nonterminal selected gaze; per post-seed
patch >=5,000 matched, overlap median <=10 mm, p95 <=25 mm, idempotent replay, no
coverage drop beyond 0.5 pp; final analytic median <=10 mm, p95 <=30 mm, coverage
>=90%, gain >=35 pp, only instance 141, >=5,000 multi-look surfels, |signed radial
median| <=7.5 mm.

Cost class: smoke Interactive/Batch; each full trial Batch (FSG6e's fulls ran
~1m0-1m11s). Expected ~1,258,291,200 samples per full trial at six fixations,
fewer if consensus terminates earlier - which is the point.

Likely failure modes, in the order I expect them: (a) the consensus rule is too
strict on real Cycles data, where BOUNDARY_RESOLVED accumulates quickly, so OPEN
loses the majority while genuine surface remains and the run stops below four
fixations or under 90% coverage; (b) it is too strict specifically at the seed
fixation, where the map is small and most look-ahead targets are unmapped but
also unobserved, giving few candidates and an immediate stop; (c) it is not
load-bearing on these fresh fixtures - every candidate that passes >=8 OPEN and
the corridor also happens to be an OPEN majority - so FSG6f neither helps nor
hurts and the FSG6e budget overrun simply recurs; (d) real stereo holes keep
enough targets OPEN that a mostly-resolved direction still wins; (e) only then
suspect projection, history accumulation or the renderer. Diagnose before
editing. **I will not change the 12 mm association or hash, the 0.15 threshold,
the 0.04 scale, the 0.12 m look-ahead, any frontier constant, the FSG6e
classifier, the FSG6d corridor, the ranking, the minimum support 8, the
instrument, FSG3 fusion, the lattice, the six-fixation budget, the geometry,
textures, seeds, SPP, vergence, coverage radius or any gate to obtain a pass; I
will add no completeness-percentage stop, low-gain stop, confidence threshold or
budget extension; and I will not rerender after a numerical miss. If the code
faithfully implements strict OPEN-majority candidate consensus and that rule
fails, I will preserve the specification result and stop.**

**Measured outcome, appended after the run (2026-09-20).**
**`FSG6F_INCREMENT6_PASS`, trial_passes 4/4, every fail list empty, aggregate
exit 0. Increment 6 is CLOSED and the next experiment is AUTHORIZED BUT NOT
IMPLEMENTED.**

FSG6a-FSG6e are intact: all five still formal FAILS, records untouched,
`z -> gaze` present in all six runners. `git diff 62fab1d` over the FSG1 stereo
modules, `fsg3_surface_map.py`, all FSG6a-FSG6e modules, `rig.py`,
`bl_common.py` and `requirements-fsg.txt` is EMPTY.

`[fsg6f-check] SUMMARY passed=14 failed=0` with
`[fsg6f-scene] PASS ... horizontal_ideal_max=0.450 chord_max_mm=0.170
corridor_preflight=true persistent_state_preflight=true
candidate_consensus_preflight=true traces={consensus_up_right:6fix/1.0000,
consensus_down_left:5fix/0.9991}` and `[fsg6f-frontier] PASS ...
candidate_state_consensus=true`. All fifteen negatives exited 1, including
`anyopen`. All nineteen FSG1-FSG6e suites green; FSG6a's 7, FSG6b's 8, FSG6c's 9,
FSG6d's 11 and FSG6e's 14 negatives all still exit 1. `SURFACE_FRONTIER` and
`TARGETS` exactly equal FSG6e with NO differing keys; `inspect.getsource`
confirms fourteen settled helpers text-identical including
`classify_frontier_state` and every FSG6d corridor helper; the candidate sort key
is asserted by literal string match. The consensus source contains no `0.5`.

Four full trials, each once. **`consensus_up_right` passed on both seeds**:
`(-8,-7)(-3,-2)(2,3)(7,8)(12,8)(12,3)`, six fixations, `no_frontier`, coverage
99.402/99.439%, median 4.324/4.309 mm, p95 15.598/15.534 mm, radial
+0.314/+0.309 mm. **`consensus_down_left` passed on both seeds in FIVE
fixations**: `(8,7)(3,2)(-2,-3)(-7,-8)(-12,-8)`, `no_frontier`, coverage
98.517/98.535%, median 4.382/4.386 mm, p95 14.224/14.235 mm, radial
-2.855/-2.885 mm. Every gate passed on every trial: pitch span 15.0 deg, yaw span
20.0, one 5-degree step per move, no repeats, per-patch measurement coverage
0.9053-0.9547, post-seed matched 11,034-20,223 with medians 1.81-3.51 mm and p95
5.74-10.54 mm, all idempotent, largest coverage decrease 0.00 pp, gain
60.91-62.21 pp, maps 76,326-82,703 surfels all pure instance 141 with
28,276-33,969 multi-look, and every nonterminal selected candidate carrying both
>=8 OPEN support and strict OPEN-majority consensus.

**Candidate consensus is load-bearing on real acquisitions, not cosmetic.**
Twenty consensus rejections across the four trials, and **every single one had
corridor allowed=True and OPEN >= 8 - so every one would have been ACCEPTED by
the retired FSG6e rule.** Three of the four trials terminate BECAUSE of
consensus: up_right/1291 had 2 candidates at the final step and both were
rejected; down_left/1237 and /1291 each had 1 and it was rejected. Only
up_right/1237 terminated on the FSG6e state alone.

The FSG6e pathology is caught explicitly on fresh data. up_right/1237 s1 (-3,-7)
with **OPEN 11 against resolved 85 of 96 raw** is the same shape as FSG6e's
`closure_up_right/1123` final survivor (11,3,82). down_left/1237 s3 (-7,-13) with
**OPEN 8 exactly at the frozen minimum, resolved 100 of 108, new-area 112.3** is
the same shape as FSG6e's `closure_up_right/1181` off-ribbon move (8,1,16) that
carried that trajectory off the surface. Both rejected before ranking; neither
fixture ever leaves the ribbon. down_left/1237 s4 (-12,-3) was an **exact 40/40
tie**, resolved rather than open by the prospectively specified tie rule, and
that rejection is what terminated the run.

Selected candidates were always large OPEN majorities (38:0 up to 76:7), so the
rule never blocked a productive move - the same separation the preserved FSG6e
development controls predicted, now reproduced prospectively on fresh fixtures
and fresh seeds.

Visuals: growth.png/growth_truth.png show both fixtures sweeping cleanly -
up_right 38.5->56.3->73.2->96.4->98.6->99.4%, down_left
36.3->54.2->75.1->98.3->98.5% in five looks - with no fixation leaving the
ribbon. coverage_3d_frontier.png shows all four rising monotonically and
saturating. Every surface_map.ply carries "comment fixed head frame H" with NO
`element face`; independent reads give median radius 0.75043-0.75044 m vs true
0.750 and 0.70797-0.70800 m vs true 0.710 (+0.4 mm and -2.0 mm).

Cost: smoke run 17.4 s (loop 17.25 s, Blender 11.84 s) / eval 6.8 s; full runs
1m5.5s, 1m6.2s, 1m4.4s, 1m5.1s; 1,258,291,200 samples per six-fixation up_right
trial and 1,048,576,000 per five-fixation down_left trial, **4,613,734,400
total** - less than the 5,033,164,800 a six-fixation set would have cost, because
consensus ended two trials a fixation early. **No code fix was required or made;
no source file was modified.** Nothing tuned - no 12 mm association or hash, 0.15
threshold, 0.04 scale, 0.12 m look-ahead, frontier constant, FSG6e classifier,
FSG6d corridor, ranking, minimum support 8, instrument, FSG3 fusion, lattice,
budget, geometry, texture, seed, SPP, vergence, coverage radius or gate changed;
no completeness-percentage stop, low-gain stop, confidence threshold or budget
extension added; no rerender after a numerical miss.

**Increment 6 is CLOSED; the next experiment is AUTHORIZED BUT NOT IMPLEMENTED.**
Scope, narrow: on fresh single convex visible curved surfaces with oracle
instance segmentation, persistent three-state 3D frontier memory can be
aggregated into candidate-level consensus strongly enough to reject
mostly-resolved actions while preserving useful active exploration and truth-free
`no_frontier` termination. NOT established: self-occlusion reasoning,
hidden-surface discovery, multiple objects, free head motion, learned gaze,
optimality or calibrated uncertainty. The six-increment route - FSG6a's
eye-asymmetric veto, FSG6b's conjunctive corner, FSG6c's one-component licensing,
FSG6d's non-terminating raw frontier, FSG6e's minority-OPEN survivors - is
preserved in full as five formal FAIL records.

### 2026-09-20 - FSG7a Increment 7, prescribed head motion reveals self-occluded surface: authorized, prospective entry (written before acquisition)

Per `docs/fsg7a-increment7.md` and D-FSG7a appended just above. Increment 6 is
CLOSED at FSG6f; **FSG7a is a new prospective experiment, not a repair of
FSG6f.** Commands, written before running them:

    python -m py_compile tools/fsg7a_{public,motion,scene,render_fix,run,eval,compare}.py tools/dev/check_fsg7a.py
    python tools/dev/check_fsg7a.py
    for n in no_motion moving_scene frame truth purity visibility; do python tools/dev/check_fsg7a.py --negative "$n"; done
    (the current FSG6f check and the standard prior suites from the FSG6f report)
    python tools/fsg7a_run.py  --out previews/fsg7a/smoke-fold_right-seed1409 --profile small --fixture fold_right --seed 1409 --device OPTIX
    python tools/fsg7a_eval.py previews/fsg7a/smoke-fold_right-seed1409 --out previews/fsg7a/smoke-fold_right-seed1409-eval --mode smoke
    (then the four full trials fold_right/1409, fold_right/1453, fold_left/1409, fold_left/1453,
     each run once and evaluated, then fsg7a_compare.py --root previews/fsg7a --out previews/fsg7a/full-comparison)

**Stated explicitly, because it is the reason Increment 7 exists: true
self-occlusion cannot be revealed by eye rotation at fixed centres.** Holding the
eye centres fixed and changing fixation changes which rays are sampled at high
resolution, not which world points are on a line of sight. A point behind a fold
stays hidden however the eyes rotate. Every increment through FSG6f rotated the
eyes about fixed centres, so none of them could have discovered hidden surface
even in principle; D3 set head motion aside as its own question. **FSG7a permits
prescribed lateral head translation, keeps H0 (the initial head frame) as the
persistent map frame, and does NOT yet implement an active motion policy** - the
two head positions and two gazes are constants in the public schedule and the
observer does not choose them.

**Preservation and frozen source.** `git diff 3fe2864` over the FSG1 stereo
modules (`fsg_stereo_supported`, `fsg_stereo_hdr`, `fsg_stereo`, `fsg_evaluate`,
`fsg_geometry`, `fsg_scene`, `fsg_validation_render`), `fsg3_surface_map.py`,
**all FSG6, FSG6b, FSG6c, FSG6d, FSG6e and FSG6f modules**, `rig.py`,
`bl_common.py` and `requirements-fsg.txt` is EMPTY. No prior decision block is
edited. `fsg7a_run.py` imports neither `fsg7a_scene` nor any `evaluation_only`
asset and calls `compute_once` behind `check_kernel_equivalence`.

**The transport, read from the code.** `fsg7a_run.patch_from_record` builds each
patch as `xyz_h0 = motion.points_ht_to_h0(rec["xyz_h"][mask], t)`, i.e.
`x_H0 = x_Ht + t_H0`, and fuses in H0; `check_fsg7a.source_control` asserts that
call is present, `world_fixed_control` asserts the rendered scene stays fixed in
H0 while the head moves, and `schedule_control` asserts the seed is at H0 and the
reveal translation is 0.45 m toward the correct side of each fold. The head
origin is moved through `fsg_geometry.make_calibration(..., head_origin_w=...)`,
a keyword that **already exists in the frozen module** and is already consumed by
the frozen render path - no instrument change was needed to move the head.

Design checks quoted from the handoff, not experimental results: at H0 direct
evaluator geometry gives 0.0000 return visibility in both eyes on both fixtures,
and after the prescribed +/-0.45 m translation gives 1.0000 in both eyes.

Gates, all four trials judged independently and all four required: per-patch
object measurement coverage >=90%; reveal patch >=5,000 fixed-H0 overlap matches,
overlap median <=10 mm, P95 <=25 mm, idempotent replay; final map only instance
151; >=5,000 surfels with support >=2; final folded-surface median <=10 mm and
P95 <=30 mm; seed front coverage >=80% and seed return coverage <=5%; final
return coverage >=80% with gain >=75 pp; final whole-object coverage >=90%; and
evaluator direct visibility confirming fixed-head return <=2% and moved-head
binocular return >=95%.

Cost class: checks Interactive; smoke Interactive/Batch (two acquisitions only);
each full trial Batch - two binocular acquisitions rather than five or six, so
these should be markedly cheaper than the FSG6 trials.

Likely failure modes, in the order I expect them: (a) the 0.45 m translation
moves the front panel far enough that the reveal patch loses fixed-H0 overlap
with the seed map, so matched drops below 5,000 even though the return wing is
visible; (b) the return wing is seen at a very oblique angle after translation,
costing object measurement coverage or inflating the folded-surface P95; (c) an
error in the Ht->H0 transport sign or in the head-origin world mapping would show
up as a bimodal map offset near 0.45 m - the `frame` negative is the guard; (d)
the fold's inner corner is genuinely grazing for one eye, so binocular stereo
fails exactly along the seam; (e) only then suspect the renderer or the scene
build. Diagnose before editing. **I will not change the 0.45 m translation, the
gazes, geometry, texture, seeds, SPP, the 2.10 m vergence, the stereo instrument,
the 12 mm fusion rule, the coverage radius or any gate to obtain a pass; I will
add no ICP, registration optimization, motion policy or extra views; and I will
not rerender a numerical miss.** If the comparison fails I preserve everything
and stop; if it passes I close FSG7a feasibility only, and active head-motion
selection remains not implemented.

**Measured outcome, appended after the run (2026-09-20).**
**`FSG7A_HEAD_MOTION_FEASIBILITY_FAIL`, trial_passes 0/4.** Every trial failed on
**exactly one gate, the same one in all four**: `final map median folded-surface
error`, 12.62-12.98 mm against a <=10 mm limit. The miss is preserved and FSG7a
feasibility is NOT closed.

**The head-motion mechanism worked on every trial.** Return-wing coverage went
from 4.73-4.97% at the H0 seed to **87.49-96.20%** after the prescribed lateral
translation - gain 82.75-91.36 pp - and the newly visible measurements landed in
persistent H0 memory at **2.545-2.830 mm median overlap** with the seed map, P95
7.037-7.741 mm, every replay idempotent. Direct evaluator visibility: return
**0.0000/0.0000** in both eyes at H0 and **1.0000/1.0000** after translation, on
both fixtures.

Preservation: `git diff 3fe2864` over the FSG1 stereo modules,
`fsg3_surface_map.py`, all FSG6-FSG6f modules, `rig.py`, `bl_common.py` and
`requirements-fsg.txt` is EMPTY; no prior decision block edited; every manifest
records `truth_opened: false`, `policy: none`, empty `policy_inputs`. The head
origin moves through `make_calibration(..., head_origin_w=...)`, a keyword that
**already existed in the frozen geometry module** and is already consumed by the
frozen render path - no instrument change was needed to move the head.

`[fsg7a-check] SUMMARY passed=7 failed=0` with
`[fsg7a-motion] PASS h0_ht_roundtrip=true moving_frame_negative_m=0.451` and
`[fsg7a-scene] PASS self_occlusion=true head_translation_reveals=true
fixed_head_gaze_cannot_reveal=true`. All six negatives exited 1. All twenty prior
suites green including `[fsg6f-check] passed=14 failed=0`.

Frame-transport integrity measured on the saved arrays: `x_H0 - x_Ht` equals the
prescribed translation to `max|delta-t| = 1.49e-08` (float32 storage of 0.45),
exactly zero at the seed. The seed map spans z [-2.623,-2.446]; after the reveal
it reaches z = -3.025 along a return wing running z = -2.50 to -3.15 - the motion
genuinely added surface absent from the seed map.

Smoke (`fold_right`/1409/small, 2.74 s run / 1.10 s eval) completed, exit 2,
numerical only: return 0.0000 -> 0.4776, overlap 5.368/11.074 mm idempotent, nine
resolution-scaled FAIL lines. No runtime, provenance, truth-leak, frame-transform,
scene-motion or orchestration blocker, so full ran.

Four full trials, each once, 419,430,400 samples each (1,677,721,600 total), two
acquisitions per trial. fold_right/1409 and /1453: patch coverage 0.9208/0.9357-8,
reveal matched 19,054-19,058 new 2,732, overlap 2.545-2.548/7.037-7.069 mm,
return 0.0473-0.0477 -> 0.8749-0.8774, whole 0.9193-0.9209, median
12.941-12.983 mm, P95 21.777-21.810 mm. fold_left/1409 and /1453: patch coverage
0.9208/0.9315-7, reveal matched 14,923-14,943 new 3,259-3,283, overlap
2.818-2.830/7.702-7.741 mm, return 0.0484-0.0497 -> 0.9602-0.9620, whole
0.9743-0.9755, median 12.624-12.683 mm, P95 21.132-21.253 mm. Maps 26,392-26,943
points, all pure instance 151, 6,789-9,672 surfels at support >=2. **Every gate
passed on every trial except the final median.**

**Root cause, measured: a front-panel depth bias inherited from the frozen
instrument, not a head-motion or transport failure.** Splitting the final map by
nearest panel: the **return wing is accurate at 1.600-2.334 mm median**, while
the **front panel carries a uniform -13.7 mm z offset** (median -13.741 mm on
fold_right, -13.664 mm on fold_left) and holds 87-89% of the surfels, so it sets
the median. With baseline 0.0630 m and f = 1217.8 px, the front panel at
Z = 2.50 m has nominal disparity 30.690 px, and +13.74 mm implies a disparity bias
of **-0.1687 px** - within 7% of the **-0.1579 px SGBM bias FSG1 measured and
recorded** in its step diagnostic. The fixture sits **0.40 m beyond the prescribed
2.10 m vergence**, further than any previous FSG target, so the same fixed
sub-pixel bias produces a larger metric offset than before. The return wing
escapes it geometrically: the front normal is +z so a depth offset moves points
OFF it, while the return normal is +/-x so the same offset slides points ALONG it.
A single global +13.74 mm z correction - computed as a diagnostic only, applied to
no tool - gives 3.776/11.333 mm and 3.663/10.808 mm, far inside the 10/30 gates.

**No code fix was made and no source file was modified.** The code faithfully
implements the written experiment; correcting the bias would mean changing the
frozen FSG1 instrument or the 2.10 m vergence, both forbidden. Nothing tuned,
nothing rerendered.

Visuals: growth.png is a top-down (x,z) view and shows it directly - a flat front
panel at the H0 seed, then an **"L"** whose return leg extends backward in z after
translation. growth_truth.png reports front 100.0% / return 87.5% for
fold_right/1409; fold_left mirrors it. Every surface_map.ply carries "comment
fixed initial head frame H0", has NO `element face`, 26,392-26,943 vertices.

Scope of what this does establish, short of the gate: prescribed lateral head
translation reveals a genuinely binocularly self-occluded continuation, and
exact-pose transport into H0 places the newly visible measurements into the
frozen 12 mm fusion coherently - 2.5-2.8 mm median overlap, idempotent, no ICP or
registration optimization. **Active head-motion selection remains not implemented
and is untouched by this result.** Stopped for Luiz/Chat.

### 2026-09-20 - Stage II / Scene-1a, seeded multi-object active reconstruction: authorized, prospective entry (written before acquisition)

Per `docs/scene1a-stage2.md` and D-SCENE1A appended just above. **FSG6f/Increment
6 is CLOSED/PASS and is the frozen per-object controller; FSG7a is preserved as
an exploratory moving-head FAIL and is DEFERRED - the moving-head branch is not
continued. Stage II returns to fixed head, static scene.** Commands, written
before running them:

    .venv/bin/python -m py_compile tools/scene1a_{public,scene,policy,render_fix,run,eval,compare}.py tools/dev/check_scene1a.py
    .venv/bin/python tools/dev/check_scene1a.py --self-test
    for n in hardcoded targetonly premature revisit truth copiedpolicy overlap; do .venv/bin/python tools/dev/check_scene1a.py --negative "$n"; done
    (all prior regression suites, including the FSG7a report set and at minimum FSG6f and FSG7a)
    .venv/bin/python tools/scene1a_run.py  --out previews/scene1a/smoke-triad_a-seed1601 --profile small --fixture triad_a --seed 1601 --device OPTIX
    .venv/bin/python tools/scene1a_eval.py previews/scene1a/smoke-triad_a-seed1601 --out previews/scene1a/smoke-triad_a-seed1601-eval --mode smoke
    (then the four full trials triad_a/1601, triad_a/1667, triad_b/1601, triad_b/1667,
     each run once and evaluated, then scene1a_compare.py over exactly those four metrics.json)

**Integrity audit, done before writing this entry.** HEAD `0997eae` on clean
`main`; `50eb782` confirmed an ancestor. `git diff --name-status 50eb782 HEAD`
shows exactly ten files, **all additions, no modifications**: the eight
`scene1a_*` tools plus `docs/scene1a-stage2.md` and `docs/scene1a-checks.md`. An
explicit `git diff 50eb782` over the FSG1 stereo modules, `fsg3_surface_map.py`,
**every FSG6/6b/6c/6d/6e/6f module**, every FSG7a module, `rig.py`,
`bl_common.py` and `requirements-fsg.txt` is EMPTY - in particular the FSG6f
modules are unchanged.

**FSG6f is reused by import, not copied.** `scene1a_policy.py` imports
`fsg6f_public` and `fsg6f_frontier as object_policy` and calls
`object_policy.choose_next(...)` at a single site; it contains no definition of
`extract_frontier`, `classify_frontier_state`, `candidate_state_consensus`, the
projected-corridor helpers, `_new_box_area`, or any `candidates.sort` ranking.
Neither `scene1a_run.py` nor `scene1a_policy.py` mentions `scene1a_scene` or
`evaluation_only`, and the runner calls `compute_once` behind
`check_kernel_equivalence`. The public contract carries `fixed_head: True`,
`static_scene: True` and `VERGENCE_DISTANCE_M = 2.10`.

The frozen contract, restated so it is on the record before any acquisition:
three known objects 201/202/203, one prescribed seed fixation each; after the
seeds every object asks the frozen FSG6f controller and the scene scheduler picks
**lexicographically by largest predicted new angular area, then largest frontier
score, then smaller instance ID as a deterministic final tie-break** - no weight,
learned utility or fitted scene constant. `scene_complete <=> every object
independently reports no_frontier`. Every fixation is processed for ALL known
object IDs, any non-target object contributing >=100 valid stereo points is fused
into its own map, and the completed binocular observation enters every object's
history. Physical gaze is globally no-revisit and the global history is supplied
to each object's controller. Fresh non-mirror scenes `triad_a` and `triad_b`,
fresh seeds 1601 and 1667, objects angularly disjoint (**object-object occlusion
is not part of Scene-1a**).

Gates as written in `docs/scene1a-stage2.md`: per object at least one autonomous
post-seed target fixation, targeted patch coverage >=90%, targeted post-seed
overlap >=5,000 matched with median <=10 mm and P95 <=25 mm, idempotent replay,
own-ID purity, >=5,000 multi-look surfels, final surface median <=10 mm and P95
<=30 mm, final coverage >=90% and gain >=25 pp; scene-level the first three
fixations exactly the prescribed seeds, all later selection autonomous, every
object receiving autonomous attention, >=2 post-seed attention switches, no
repeated physical fixation, no object over the six-target budget, total <=18
fixations, termination `scene_complete`, every final object state `no_frontier`.
All four trials must pass. Poor opportunistic visibility is descriptive only.

Cost class: checks Interactive; smoke Interactive/Batch; each full trial Batch -
up to 18 binocular fixations, so these should cost more than an FSG6 trial and
markedly more than FSG7a's two-view trials.

Likely failure modes, in the order I expect them: (a) the scheduler starves one
object - two objects keep out-bidding the third on predicted new area until the
18-look global budget ends the scene, so "every object receives autonomous
attention" or `scene_complete` fails; (b) opportunistic fusion contributes
essentially nothing because the three objects are angularly disjoint and a
12-degree fovea cannot see two of them at once, which would be honest but makes
that mechanism untested here; (c) a targeted patch that lands near an object's
edge misses the >=90% measurement fraction, exactly as FSG6/FSG7a smokes did at
small profile; (d) an object's own FSG6f run terminates at `no_frontier` before
reaching 90% coverage, which would be an inherited FSG6f property surfacing on
new geometry rather than a scheduler fault; (e) only then suspect the scheduler
implementation or the renderer. Diagnose before editing. **I will not change the
fixtures, geometry, instance IDs, textures, seeds, the three prescribed seeds,
the fixed-head/static-scene assumptions, the 2.10 m vergence, the FSG1
instrument, the FSG3 12 mm fusion or hash, any FSG6f code or constant, the
six-look or 18-look budgets, the scheduler ordering, global no-revisit, the
opportunistic rule, or any gate to obtain a pass; I will add no object discovery,
semantics, occlusion logic, head motion, ICP, meshing, filling, learned policy,
extra views or alternate seeds; and I will not rerender a numerical miss. A
faithfully implemented rule that fails is a specification result: I preserve it
and stop.**

**Measured outcome, appended after the run (2026-09-20).**
**`SCENE1A_STAGEII_FAIL`, trial_passes 0/4.** The miss is preserved; Scene-1a is
NOT closed and no next Stage-II experiment is authorized.

`[scene1a-check] SUMMARY passed=8 failed=0` with `[scene1a-scene] PASS
fixtures=triad_a,triad_b objects=[201, 202, 203] fixed_head=true
static_scene=true` and `[scene1a-policy] PASS frozen_fsg6f=true
scheduler=area_then_score opportunistic=true all_object_completion=true`. All
seven negatives exited 1. All twenty-one prior suites green, including
`[fsg6f-check] passed=14 failed=0` and `[fsg7a-check] passed=7 failed=0`, plus
FSG6f's fifteen and FSG7a's six negatives.

Smoke (`triad_a`/1601/small, run 59.3 s exit 0 / eval 6.8 s exit 2): 14
fixations, `object_budget_exhausted`, 41 numerical fails. Every integrity item
that would have blocked full PASSED - first three fixations exactly the
prescribed seeds, 14/14 unique gazes, per-object targets {201:4, 202:6, 203:4}
inside the six-look budget, 14 <= 18, all three objects got autonomous attention,
3 switches, `truth_opened: false`, opportunistic fired twice. No runtime
exception, provenance/truth leak, scene-motion error, scheduler integrity error
or broken FSG6f reuse, so full ran.

Four full trials, each once. **All four ended `object_budget_exhausted`, never
`scene_complete`.** triad_a/1601: 12 fixations, 4 switches, targets {201:5,
202:6, **203:1**}, 2,516,582,400 samples, loop 144.9 s. triad_a/1667: 13, 5
switches, {201:6, 202:6, **203:1**}, 2,726,297,600 samples, 161.9 s.
triad_b/1601 and /1667: 11 fixations each, 3 switches, {201:6, 202:2, 203:3},
2,306,867,200 samples, 141.9/141.6 s.

**What the substrate did do.** In every trial the first three fixations were
exactly the prescribed seeds, all later selection was autonomous, no physical
fixation repeated, no object exceeded six targets, totals stayed under 18, every
per-object map was pure in its own ID, and every fused patch replayed
idempotently. Targeted overlap medians 2.01-5.11 mm and P95 5.43-11.33 mm all
passed. Per-object surface accuracy passed everywhere: median 4.368-5.201 mm,
P95 13.153-18.249 mm across all twelve object-instances. **The lexicographic rule
was obeyed exactly: 39 autonomous decisions across the four trials, 39
rule-compliant, 0 violations.**

**Root cause, measured: a starvation loop in the scheduler's primary key.** The
rule ranks by largest `predicted_new_angular_area_deg2`. An object that is not
selected does not acquire, so its map does not change, so **its bid does not
change**. On triad_a object 203's proposal is frozen at **area 105.48 / score
18.12 for all ten decisions**, permanently below the 122-140 deg^2 that 201 and
202 keep offering, so it receives **zero autonomous post-seed attention** and its
map never leaves the seed state - coverage 0.4726 -> 0.4726, gain +0.0000, 23,197
points, support histogram {1: 23197}, **not one multi-look surfel**. The sharp
part: **203 carries the HIGHEST frontier score of the three at every decision**
(18.12 against 12.86 and 19.28->6.74). It would have won on the second key, but
the first key never ties so the second is never consulted. triad_b shows the same
dynamic redistributed - 202 frozen at 110.93 for seven consecutive decisions
before winning once and immediately reporting `no_frontier`; 203 frozen at 119.99,
two looks, then 104.40 and never selected again, with the final decision
separating 201 from 203 by **0.01 deg^2** (104.41 vs 104.40).

Final object policy states: only 2 of 12 object-instances reached `no_frontier`
(202 on both triad_b trials). The others ended `continue` with 21-98 OPEN
frontier surfels and 1-4 live candidates. No object reached the 90% coverage
gate; best was 0.7919.

**Opportunistic processing fired but rarely, reported honestly.** Non-target
objects were processed at every fixation (22-26 non-target patches per trial) but
only 1-2 per trial cleared the 100-valid-point threshold and fused: triad_a steps
6 and 7 (obj 202, 1360 and ~1367 points), triad_b step 7 (obj 202, 147 points).
Not dead, but on deliberately angularly disjoint base scenes a 12-degree fovea
rarely holds two objects, so it contributes little. That is a property of the
separated base case, not evidence the mechanism is wrong.

Visuals: `scene_map.png` shows the failure directly - objects 201 and 202 built
up across many numbered fixation markers while **object 203 carries a single seed
patch and the lone marker "2"**. `scene_surface_map.ply` carries "comment fixed
head frame H; Stage II Scene-1a", has NO `element face`, 99,107 vertices
(triad_a) and 91,598 (triad_b).

**No code fix was required or made and no source file was modified.** The
scheduler is faithfully implemented and fails, which the frozen contract defines
as a scientific/specification result. Nothing was tuned - no fixture, geometry,
instance ID, texture, seed, prescribed seed fixation, fixed-head/static-scene
assumption, 2.10 m vergence, FSG1 instrument, FSG3 12 mm fusion or hash, FSG6f
code or constant, six-look or 18-look budget, scheduler ordering, no-revisit
rule, opportunistic rule or gate changed; nothing rerendered.

Scope of what holds: three persistent object models were maintained
simultaneously with pure per-object identity and idempotent fusion; attention
switched autonomously 3-5 times per trial; per-object surface accuracy stayed
inside the gates everywhere; and the frozen FSG6f controller was driven
unmodified by import, with its full frontier-state, consensus and corridor record
preserved in every proposal. **What is unresolved is attention allocation**:
ranking by largest predicted new area is not stable under the fact that an
unselected object's bid cannot change, and it admits a starvation fixed point in
which the object most in need of looks is never selected at all. Stopped for
Luiz/Chat.

### 2026-09-20 - Stage II / Scene-1b, fair multi-object active reconstruction: authorized, prospective entry (written before acquisition)

Per `docs/scene1b-stage2.md` and D-SCENE1B appended just above. **FSG6f is
CLOSED/PASS and frozen; FSG7a is a preserved, deferred FAIL and is not reopened;
Scene-1a remains a formal FAIL in the record and is not edited.** Commands,
written before running them:

    .venv/bin/python -m py_compile tools/scene1b_{public,scene,policy,render_fix,run,eval,compare}.py tools/dev/check_scene1b.py
    .venv/bin/python tools/dev/check_scene1b.py --self-test
    for n in areaonly targetonly premature revisit truth copiedpolicy overlap underdesigned; do .venv/bin/python tools/dev/check_scene1b.py --negative "$n"; done
    (all prior regression suites from the Scene-1a report, including Scene-1a, FSG6f and FSG7a)
    .venv/bin/python tools/scene1b_run.py  --out previews/scene1b/smoke-fair_triad_c-seed1723 --profile small --fixture fair_triad_c --seed 1723 --device OPTIX
    .venv/bin/python tools/scene1b_eval.py previews/scene1b/smoke-fair_triad_c-seed1723 --out previews/scene1b/smoke-fair_triad_c-seed1723-eval --mode smoke
    (then the four full trials fair_triad_c/1723, fair_triad_c/1789, fair_triad_d/1723, fair_triad_d/1789,
     each run once and evaluated, then scene1b_compare.py over exactly those four metrics.json)

**Integrity audit, done before writing this entry.** HEAD `a49a28b` on clean
`main`; `9d03829` confirmed an ancestor. `git diff --name-status 9d03829 HEAD`
shows exactly ten files, **all additions, no modifications**: the eight
`scene1b_*` tools plus `docs/scene1b-stage2.md` and `docs/scene1b-checks.md`. An
explicit `git diff 9d03829` over the FSG1 stereo modules, `fsg3_surface_map.py`,
**every FSG6/6b/6c/6d/6e/6f module, every FSG7a module and every `scene1a_*`
module** (including `tools/dev/check_scene1a.py`), `rig.py`, `bl_common.py` and
`requirements-fsg.txt` is EMPTY.

**FSG6f reused by import, not copied.** `scene1b_policy.py` imports
`fsg6f_public` and `fsg6f_frontier as object_policy` and calls
`object_policy.choose_next(...)` at one site; it defines none of
`extract_frontier`, `classify_frontier_state`, `candidate_state_consensus`, the
corridor helpers, `_new_box_area` or any `candidates.sort`. **Prediction-side
truth isolation**: neither `scene1b_policy.py` nor `scene1b_run.py` mentions
`scene1b_scene`, `evaluation_only`, or any `witness`. The runner calls
`compute_once` behind `check_kernel_equivalence`.

**The frozen rule, restated before acquisition.** For each live object `i`, `n_i`
is the count of autonomous post-seed target fixations already allocated. Compute
`n_min = min n_i` over LIVE objects only; only objects at `n_i == n_min` are
eligible. Within that class the Scene-1a ordering is retained exactly: largest
`predicted_new_angular_area_deg2`, then largest `frontier_score`, then smaller
instance ID. A completed (`no_frontier`) object leaves the live set and stops
constraining the others. Read from the source, the implemented rule string is
`least_service_then_predicted_new_area_then_frontier_score_then_instance_id`.
**No weight, learned utility, confidence threshold, age bonus, starvation timer,
weighted sum or round-robin hard-coding** - fairness is structural eligibility,
the old utility is the within-class ranking.

Fixtures are fresh and deliberately easier, so this experiment isolates
scheduling from Scene-1a's harder geometry: `fair_triad_c` (upper-left plane,
lower-centre ribbon, upper-right ribbon, seeds 201@(-19,+8) 202@(-6,-9)
203@(+9,+8)) and `fair_triad_d` (lower-centre plane, upper-left ribbon,
upper-right ribbon, seeds 201@(-4,-9) 202@(-21,+9) 203@(+7,+9)), all near the
validated 2.10 m vergence, compact and angularly disjoint. Fresh seeds 1723 and
1789. Evaluator-only geometry carries a three-look design witness per object
covering >=98% of the analytic object under ideal 12-degree boxes using three of
six looks; **the witness is evaluator-side only, is not a prescribed path and is
not a policy prediction.**

Gates as written in `docs/scene1b-stage2.md`, unchanged from Scene-1a except one
addition: per object at least one autonomous post-seed target fixation, targeted
patch coverage >=90%, targeted post-seed overlap >=5,000 matched with median
<=10 mm and P95 <=25 mm, idempotent replay, own-ID purity, >=5,000 multi-look
surfels, final surface median <=10 mm and P95 <=30 mm, final coverage >=90%, gain
>=25 pp, **and final per-object policy state `no_frontier`**; scene-level the
first three fixations exactly the prescribed seeds, all later selection
autonomous, **every decision obeying least-service eligibility before the frozen
utility ordering**, every object receiving autonomous attention, >=2 switches, no
repeated physical fixation, no object over six targets, total <=18, termination
`scene_complete`. All four trials must pass.

Cost class: checks Interactive; smoke Interactive/Batch; each full trial Batch -
Scene-1a's comparable full trials ran 141-162 s each.

Likely failure modes, in the order I expect them: (a) fairness fixes starvation
but the 18-look global budget now binds earlier, because forcing service on a
low-utility object spends looks that Scene-1a would have given to a productive
one, so the scene ends `object_budget_exhausted` or `scene_budget_exhausted`
before every object reports `no_frontier`; (b) the easier fixtures make every
object complete in three or four looks and the fairness class is almost always
all three live objects, so the new rule is **decorative rather than load-bearing**
- I will measure this directly by counting decisions where the fair class is
strictly smaller than the live set, and by identifying any decision where
fairness rejected a strictly higher-area proposal; (c) a targeted patch near an
object edge misses the >=90% measurement fraction as in every prior smoke;
(d) an object's frozen FSG6f run reports `no_frontier` below 90% coverage,
an inherited property surfacing on new geometry rather than a scheduler fault;
(e) only then suspect the scheduler implementation or the renderer. Diagnose
before editing. **I will not change the fixtures, geometry, types, IDs, textures,
seeds, prescribed seed fixations, fixed-head/static-scene assumptions, the 2.10 m
vergence, the FSG1 instrument, the FSG3 12 mm fusion or hash, any FSG6f code or
constant, the six-look or 18-look budgets, the least-served-first rule, the
within-class area/score/ID ordering, global no-revisit, the opportunistic rule,
or any gate to obtain a pass; I will add no age bonus, starvation timer, weighted
sum, round-robin hard-coding, completeness or low-gain stop, object discovery,
semantics, occlusion logic, head motion, ICP, meshing, filling, learned policy,
extra views or alternate seeds; and I will not rerender a numerical miss. A
faithfully implemented rule that fails is a specification result: I preserve it
and stop.**

**Measured outcome, appended after the run (2026-09-20).**
**`SCENE1B_STAGEII_FAIL`, trial_passes 0/4.** The miss is preserved; Scene-1b is
NOT closed and no next Stage-II experiment is authorized. **But the abstraction
under test worked**: Scene-1a's starvation is gone completely, the rule is
demonstrably load-bearing, and reconstruction improved sharply.

`[scene1b-check] SUMMARY passed=9 failed=0` with `[scene1b-scene] PASS
fixtures=fair_triad_c,fair_triad_d objects=[201, 202, 203] fixed_head=true
static_scene=true witness_lt_budget=true` and `[scene1b-policy] PASS
frozen_fsg6f=true scheduler=least_service_then_area_then_score fairness=true
opportunistic=true all_object_completion=true`. All eight negatives exited 1
including `areaonly` and `underdesigned`. All twenty-two prior suites green -
Scene-1a (8), FSG6f (14), FSG7a (7) - and Scene-1a's seven, FSG6f's fifteen and
FSG7a's six negatives all still exit 1. `git diff 9d03829` over the FSG1 stereo
modules, `fsg3_surface_map.py`, all FSG6* / FSG7a / `scene1a_*` modules, `rig.py`,
`bl_common.py` and pins is EMPTY; Scene-1a remains a formal FAIL, unedited.

Design-only preflight (evaluator-side): seed ideal coverage 0.500-0.627 per
object; every three-look 5-degree witness reaches **1.0000** ideal coverage using
three of six looks on both fixtures. **The witness was not used by the
predictor** - prediction-side grep for `witness`, `scene1b_scene` and
`evaluation_only` in `scene1b_policy.py` / `scene1b_run.py` is False on all three.

Smoke (`fair_triad_c`/1723/small, run 78.4 s exit 0 / eval 9.4 s exit 2): 18
fixations, `max_scene_fixations`, service {5,5,5}, 14 switches, 43 numerical
fails, near-perfect round-robin target sequence. All blockers clear - scheduler
16/16 rule-compliant with 0 violations, fairness/service provenance present
(`fair_eligible_object_ids`, `minimum_autonomous_target_count`,
`fairness_restricted_decisions`=10), FSG6f payload intact, `truth_opened` false,
18/18 unique gazes, first three fixations exactly the prescribed seeds.

Four full trials, each once, 3,774,873,600 samples each (15,099,494,400 total),
runs 256.2/255.7/244.1/242.3 s. **All four ended `max_scene_fixations` at exactly
18 fixations with service counts {201:5, 202:5, 203:5}** and 13-14 attention
switches.

**Fair scheduler audit: 64 autonomous decisions, 64 rule-compliant, 0
violations.** In every decision the selected object was inside the least-served
live class AND ranked first within it by area, then frontier score, then ID.
**38 of 64 decisions had a fairness class strictly smaller than the live set, and
in 31 of 64 fairness rejected a proposal with strictly larger predicted new
area** - the rule is decisively load-bearing, not decorative. Worked example,
c/1723 after step 4: Scene-1a would have taken 201 at area 134.29; fairness forced
203 at 119.35 because 203 had been served once fewer. **Scene-1a's starvation
does not occur anywhere in Scene-1b.**

Per-object results: **every surface, purity, multi-look and idempotence gate
passed on all twelve object-instances** - median 3.834-5.339 mm, P95
15.519-16.900 mm, all maps pure in their own ID, 12,681-20,406 multi-look
surfels, every fused patch idempotent, every object >=1 autonomous look, gains
+0.3594 to +0.5451. **Three object-instances reached exactly 1.0000 coverage**;
ten of twelve passed the 90% gate (the exceptions are fair_triad_d object 202 at
0.8413/0.8427). Targeted overlap medians 2.02-2.94 mm, P95 4.63-9.41 mm.

**Why all four still failed - arithmetic, and structural rather than a defect.**
Three objects x six per-object looks = 18 = MAX_SCENE_FIXATIONS. Under
least-served-first the objects advance in lockstep, so by the time one could
complete, all three have consumed nearly the same number of looks and there is no
slack to redistribute. Every trial ends at exactly 18 with each object having
spent its full six-look allowance, and `scene_complete` needs ALL THREE to reach
`no_frontier` within six looks each. Only **5 of 12 object-instances** did (201
and 202 on c/1789; 201 on c/1723; 202 on both d trials). Scene-1a failed the
opposite way - it stopped at 11-13 fixations with budget unspent and objects
starved. **fair_triad_c/1789 came within TWO fail lines of passing.**

**Opportunistic non-target fused updates were 0 in all four full trials** (and 0
in the smoke), against 1-2 per trial in Scene-1a. Reported honestly: non-target
objects were still processed at every fixation but none cleared the
100-valid-point threshold, because the fair_triad objects are more widely
separated and fair round-robin makes consecutive fixations jump between distant
objects. The mechanism is exercised and inert here, not broken - Scene-1a already
showed it can fire.

Visuals: `scene_map.png` is the clearest contrast with Scene-1a - all three maps
substantially built up with numbered fixation markers spread evenly, six per
object, where Scene-1a's equivalent showed one object holding a lone seed patch
and a single marker. `scene_surface_map.ply` carries "comment fixed head frame H;
Stage II Scene-1b", has NO `element face`, 124,954 vertices (fair_triad_c) and
111,881 (fair_triad_d).

**No code fix was required or made and no source file was modified.** A
faithfully implemented rule that fails is a scientific/specification result.
Nothing tuned - no fixture, geometry, type, ID, texture, seed, prescribed seed
fixation, fixed-head/static-scene assumption, 2.10 m vergence, FSG1 instrument,
FSG3 12 mm fusion or hash, FSG6f code or constant, six-look or 18-look budget,
least-served rule, within-class ordering, no-revisit rule, opportunistic rule or
gate changed; no age bonus, starvation timer, weighted sum, round-robin
hard-coding, completeness or low-gain stop added; nothing rerendered.

Scope: **least-served-first eliminates the Scene-1a starvation fixed point
completely** while preserving the frozen utility ordering within the fairness
class and introducing no weight, timer or learned term. **What is unresolved is
budget sufficiency, not fairness**: with three objects, six looks each and an
18-look scene cap, perfectly fair service consumes the global budget precisely
when the per-object budgets are consumed, leaving no slack for an object needing
one more look. Any successor has to address the relationship between the
per-object budget, the scene budget and the number of objects - not the ordering
rule. Stopped for Luiz/Chat.

### 2026-09-20 - Stage II / Scene-1c, certified composition of active object reconstructions: authorized, prospective entry (written before acquisition)

Per `docs/scene1c-stage2.md` and D-SCENE1C appended just above. **FSG6f is
CLOSED/PASS and frozen; FSG7a is a preserved, deferred FAIL; Scene-1a and
Scene-1b remain preserved formal FAILs and are not edited or relabelled.**
Scene-1b settled the scheduler abstraction (least autonomous post-seed service
first, then area / frontier-score / instance-ID) with a 64/64 compliant audit and
starvation gone; Scene-1c asks whether three active object processes **compose**
when each actor is first prospectively certified solvable inside the unchanged
six-look budget. Commands, written before running them:

    .venv/bin/python -m py_compile tools/scene1c_{public,scene,policy,render_fix,certify_run,certify_eval,certify_compare,run,eval,compare}.py tools/dev/check_scene1c.py
    .venv/bin/python tools/dev/check_scene1c.py --self-test
    for n in incompletecert areaonly schedulercopy targetonly premature revisit truth overlap underdesigned budgetbump; do .venv/bin/python tools/dev/check_scene1c.py --negative "$n"; done
    (all prior regression suites from the Scene-1b report, including FSG6f, FSG7a, Scene-1a and Scene-1b)
    component smoke: scene1c_certify_run.py/-eval.py on cert_triad_e/1847/obj201 at --profile small
    twelve full component controls: {cert_triad_e,cert_triad_f} x {1847,1901} x {201,202,203}
    scene1c_certify_compare.py over all twelve -> must say SCENE1C_COMPONENT_CERTIFICATION_PASS with 12/12
    ONLY THEN: ensemble smoke, then four full ensembles, then scene1c_compare.py with --certification

**The authorization rule, on the record before any acquisition: full ensemble
acquisition is FORBIDDEN unless all twelve component controls certify.** If the
aggregate does not return exactly `SCENE1C_COMPONENT_CERTIFICATION_PASS` with
12/12, I stop with `SCENE1C_COMPONENT_CERTIFICATION_FAIL`, preserve every
control, and run no ensemble acquisition. A failed actor is not replaced,
resized, reseeded or tuned. Certification is an authorization condition only and
is never supplied to the scene policy as a runtime input.

**Integrity audit, done before writing this entry.** HEAD `7c59ac6` on clean
`main`; `3f4b490` confirmed an ancestor. `git diff --name-status 3f4b490 HEAD`
shows exactly **thirteen files, all additions, no modifications**. An explicit
`git diff 3f4b490` over the FSG1 stereo modules, `fsg3_surface_map.py`, every
FSG6/6b/6c/6d/6e/6f module, every FSG7a module, **every `scene1a_*` and
`scene1b_*` module** (including both dev checks), `rig.py`, `bl_common.py` and
`requirements-fsg.txt` is EMPTY.

Specific verifications required by the handoff, all measured: (1)
`scene1c_policy.py` imports `scene1b_policy as frozen_scene_scheduler`, has
**zero** direct `import fsg6f` lines, and aliases rather than reimplements every
scheduler symbol - `remap_instance`, `remap_observation`, `proposal_rank_key`,
`select_proposal`, `propose_for_object`, `choose_scene_action`,
`split_visible_object_masks`, `is_global_repeat`; (2) `scene1b_policy.py` still
imports `fsg6f_public` and `fsg6f_frontier` and shows no diff; (3)
`scene1c_certify_run.py:46` and `scene1c_run.py:70` both invoke
`tools/scene1c_render_fix.py`; (4) neither prediction runner nor the policy
mentions `scene1c_scene`, `evaluation_only` or any `witness`, and both runners
call `compute_once`; (5) constants equal Scene-1b exactly -
`PER_OBJECT_MAX_FIXATIONS` 6, `MAX_SCENE_FIXATIONS` 18, `FUSION`
{0.012, 0.012}, `TARGETS` identical with **no differing keys**, vergence 2.10,
objects (201,202,203), instrument ID identical;
`FROZEN_SCENE_SCHEDULER_ID = Scene1b-least-service-then-area-score-id-v1`,
`FROZEN_OBJECT_POLICY_ID = FSG6f-candidate-frontier-consensus-v1`.

The component protocol, restated: each control renders the **complete
three-object fixture** with the same renderer, geometry, textures, seed and
prescribed seed gaze the ensemble will use; reconstructs only the nominated
object; lets unchanged FSG6f choose its later gazes; allows at most six target
looks including the seed; sees no truth during prediction; and is judged by
exactly the Scene-1b per-object gates, terminating `no_frontier`. Fresh scenes
`cert_triad_e` / `cert_triad_f`, three compact convex ribbons each in angularly
disjoint regions, fresh seeds 1847 and 1901. The evaluator-only three-look
witness (>=98% ideal box coverage using three of six looks) is a **geometry
sanity check only - not a prediction path and not the certification**.

Cost class: checks Interactive; component smoke Interactive/Batch; **twelve full
component controls plus four full ensembles is the largest acquisition of the
project so far** - Scene-1b's four full trials alone ran ~250 s each, so the
component stage is Batch and the whole run is expected to be the longest yet.
Recorded here before it runs, per the Cost-classes rule.

Likely failure modes, in the order I expect them: (a) one or more component
controls fails to reach `no_frontier` within six looks, exactly as Scene-1b's
objects did, in which case certification fails and **no ensemble is run at all** -
this is the outcome the protocol is designed to detect cleanly; (b) all twelve
certify but the ensemble still cannot finish, because interleaving changes each
object's FSG6f history and hence its later state, which would be the genuinely
interesting composition failure; (c) the ensemble completes but a per-object
measurement or overlap gate misses on a patch near an object edge, as in every
prior Stage-II smoke; (d) opportunistic fusion stays at zero as in Scene-1b,
descriptive only; (e) only then suspect orchestration or the renderer. Diagnose
before editing. **I will not change either fixture, any geometry, ID, texture or
seed, the prescribed seeds, the fixed-head/static-scene assumptions, the 2.10 m
vergence, the FSG1 instrument, the FSG3 fusion or hash, any FSG6f or Scene-1b
code or constant, the six-look or 18-look budgets, no-revisit, the opportunistic
rule or any gate to obtain a pass; I will substitute no actor, add no look,
change no seed and relax no gate; and I will not rerender a numerical miss. A
faithfully implemented rule that fails is a specification result: I preserve it
and stop.**

**Measured outcome, appended after the run (2026-09-20).**
**`SCENE1C_COMPONENT_CERTIFICATION_FAIL`, control_passes 1/12.** Per the
prospective decision rule recorded before acquisition, **the ensemble stage was
NOT run**: no ensemble smoke, no full ensemble trials, no ensemble aggregate, no
composition diagnostic. All twelve controls are preserved. Scene-1c is not
closed.

`[scene1c-check] SUMMARY passed=10 failed=0` with `[scene1c-scene] PASS
fixtures=cert_triad_e,cert_triad_f objects=[201, 202, 203] fixed_head=true
static_scene=true witnesses_lt_budget=true` and `[scene1c-policy] PASS
frozen_fsg6f=true frozen_scene1b_scheduler=true fairness=true
component_certification=true opportunistic=true`. All ten negatives exited 1
including `incompletecert`, `schedulercopy` and `budgetbump`. All twenty-three
prior suites green - Scene-1a (8), Scene-1b (9), FSG6f (14), FSG7a (7) - and
Scene-1a's seven, Scene-1b's eight, FSG6f's fifteen and FSG7a's six negatives all
still exit 1. `git diff 3f4b490` over the FSG1 stereo modules,
`fsg3_surface_map.py`, all FSG6* / FSG7a / `scene1a_*` / `scene1b_*` modules,
`rig.py`, `bl_common.py` and pins is EMPTY; Scene-1a and Scene-1b remain
preserved formal FAILs, unedited.

Component smoke (cert_triad_e/1847/obj201/small, run 34.1 s exit 0 / eval 2.9 s
exit 2): 6 looks, `max_object_fixations`, coverage 0.4617 -> 0.9591. Integrity
clean - `truth_opened` false, fixed/static true,
`complete_three_object_scene_rendered` true, role
`component_certification_control`, 6/6 unique gazes, FSG6f reached only through
the frozen Scene-1b layer - so the full controls ran.

Twelve full component controls, 11,744,051,200 primary camera samples total.
**Only cert_triad_e/1847/obj203 certified** (4 looks, `no_frontier`, coverage
0.6153 -> 1.0000, median 5.169 mm, 12,935 multi-look surfels, zero fails).
Everything structural passed in every control: every map pure in its nominated
ID, every fused patch idempotent, no physical fixation repeated, no control over
six looks, and every surface median 5.169-6.616 mm with P95 16.252-18.092 mm
inside the 10/30 gates.

**Three distinct failure modes, separated cleanly by the protocol.**
(1) **Premature `no_frontier` after one unproductive autonomous look** - object
203 on e/1901, f/1847 and f/1901 took exactly one post-seed look and stopped with
**gain exactly +0.0000** and 4,185-4,472 multi-look surfels against the 5,000
gate. Against the recorded angular bounds (203 spans yaw [+6.180,+23.816] on e
and [+5.554,+22.389] on f, seeds at +11 and +10), the failing runs moved to
**(+6,+3)** and **(+5,+9)** - toward the near edge the seed already covers -
while the one certifying control moved to **(+16,+13)** then (+21,+13),(+21,+8)
into the unexplored far tail and reached 1.0000 in four looks. The e/1847 vs
e/1901 pair is the sharpest comparison in the record: **identical fixture,
identical prescribed seed gaze (+11,+8), different Monte-Carlo seed, opposite
first autonomous decision, opposite outcome** - the only recorded difference is
the renderer seed, so the divergence enters through stereo noise changing the
frozen controller's first post-seed choice.
(2) **`max_object_fixations` without `no_frontier`** - five controls
(e/1847/201, e/1901/201, e/1901/202, f/1847/202, f/1901/202) used all six looks
with the controller still reporting `continue`; three of them had already reached
1.0000, 1.0000 and 0.9999 coverage, so the reconstruction was finished but the
frontier was not declared resolved.
(3) **Per-look measurement coverage below 0.90** in eleven of twelve controls,
0.8669-0.8994 on the offending looks. Only e/1847/203 kept every look >=0.9036.
No claim is made about *why* the first autonomous choice is seed-sensitive on
this geometry; that is beyond what the recorded state supports.

Proof the controls exercised the real context: all twelve manifests record
`complete_three_object_scene_rendered: true`, and both runners invoke the
identical `tools/scene1c_render_fix.py` (certify_run.py:46, run.py:70). These
were not isolated single-object renders.

**No code fix was required or made and no source file was modified.** No actor
was replaced, resized, reseeded or tuned; no look added; no gate relaxed; FSG6f
untouched. Nothing rerendered.

What this establishes: **the certification protocol worked as designed and was
worth running.** It detected, before any ensemble acquisition, that eleven of
twelve actors are not solvable inside the unchanged six-look budget in the exact
complete-scene rendering context - including a mode Scene-1b could not have
isolated, where the frozen controller declares `no_frontier` after one
unproductive look with zero gain. Run ensemble-first, those actor-level failures
would have been confounded with scheduling and budget effects, exactly as
Scene-1b's budget-sufficiency question was confounded with component
solvability. **The composition question is not reached**: its premise
(individually solvable actors) does not hold on these fixtures. The open question
is now the frozen FSG6f controller's post-seed behaviour on this fixture family -
why its first autonomous choice is seed-sensitive at object 203's seed, and why
five controls exhaust six looks without resolving the frontier despite reaching
~1.0 coverage. Stopped for Luiz/Chat.

### 2026-09-21 - Reality Check 1, good enough on an ordinary static scene?: authorized, prospective entry (written before acquisition)

Per `docs/reality-check-1.md` and D-REALITY1 appended just above. **An
observational practical test, not another prospective metric benchmark.**
Commands, written before running them:

    .venv/bin/python -m py_compile tools/reality1_{public,scene,render_fix,run,eval,compare}.py tools/dev/check_reality1.py
    .venv/bin/python tools/dev/check_reality1.py
    for n in flat uniformrich policycopy truth qualitygate budgetbump; do .venv/bin/python tools/dev/check_reality1.py --negative "$n"; done
    (current FSG6f check suite and its negative set)
    .venv/bin/python tools/reality1_run.py  --out previews/reality1/smoke-seed2111 --profile small --seed 2111 --device OPTIX
    .venv/bin/python tools/reality1_eval.py previews/reality1/smoke-seed2111 --out previews/reality1/smoke-seed2111-eval
    (then full seed 2111 and full seed 2179, each exactly once, then reality1_compare.py --root previews/reality1)

Recorded before any data exists:
- **fixed head / static scene retained** - no head motion, FSG7a stays deferred;
- **frozen FSG1 stereo, FSG3 12 mm fusion and FSG6f object policy retained**,
  imported not copied;
- **the only experimental change is the less calibration-like scene/texture** -
  a shallow hanging cloth/poster-like target ~0.90 x 0.64 m at ~2.1 m, depth
  varying non-periodically by ~8 cm, 120 rendered triangles rather than a plane
  or constant-radius cylinder, with deliberately MIXED texture (broad
  low-contrast region, modest printed band/emblem, subtle fabric variation, small
  repetitive weave) plus table, wall and two unrelated side props;
- **seeds 2111/2179 and seed gaze (-6,-4) are fixed before data**;
- **there is intentionally NO numerical quality PASS threshold**;
- **after the two full runs I stop and return the report to Luiz/Chat.**

**Integrity audit, done before writing this entry.** HEAD `46d9699` on clean
`main`. `git diff --name-status HEAD~1 HEAD` shows exactly **nine files, all
additions**: the seven `reality1_*` tools plus `docs/reality-check-1.md` and
`docs/reality-check-1-checks.md`. `git diff HEAD~1` over the FSG1 stereo modules
(`fsg_stereo_supported`, `fsg_stereo_hdr`, `fsg_stereo`, `fsg_evaluate`,
`fsg_geometry`, `fsg_scene`, `fsg_validation_render`), `fsg3_surface_map.py`,
**every FSG6f module**, `rig.py`, `bl_common.py` and `requirements-fsg.txt` is
EMPTY, confirmed additionally by per-file sha256: `fsg_stereo_supported`
683ae91eaca7b6af, `fsg_stereo_hdr` 67e2ec4667bcc179, `fsg_stereo`
faebf0f1b3acbfde, `fsg_evaluate` a5134b8d8537714d, `fsg_geometry`
d9537d8ebc23b60c, `fsg3_surface_map` 1b9dbeb873105ec9, `fsg6f_public`
c79f58c9b51f33d4, `fsg6f_frontier` d636c9405d719916 - all identical to the
pre-install parent `ed851ef`.

`reality1_run.py` imports `fsg6f_frontier as policy` and calls
`policy.choose_next(...)`; it does **not** import `reality1_scene`, opens no
`evaluation_only` asset, and contains no copy of FSG6f's `extract_frontier`,
`classify_frontier_state`, `candidate_state_consensus`, corridor helpers or
candidate ranking. Contract: OBJECT_ID 141, backgrounds (142,143,144,145),
FIXTURE `tabletop_cloth`, SEEDS (2111,2179), SEED_GAZE_DEG (-6,-4),
MAX_FIXATIONS 6, VERGENCE 2.10, FUSION {0.012,0.012} - `FUSION`,
`MAX_FIXATIONS` and `INSTRUMENT_ID` all measurably equal to `fsg6f_public`.

Status-token note for the record: `reality1_eval.py` emits
`REALITY1_OBSERVATION_COMPLETE` per run (the token named in
`docs/reality-check-1.md`), and `reality1_compare.py` emits `REALITY1_COMPLETE`
for the two-run aggregate. Same decision rule at both levels - structural
integrity only.

Cost class: checks Interactive; smoke Interactive/Batch; the two full runs Batch
(FSG6f-scale single-object runs have been roughly 1-2 min each).

Likely outcomes, in the order I expect them, none of which changes anything:
(a) coverage well below the ~99% seen on the calibration-like cylinders, because
the broad low-contrast region gives the FSG1 matcher little to lock onto -
descriptive only; (b) the two seeds diverging in trajectory or termination, as
Scene-1c's object 203 did on a seed change - descriptive only; (c) a surface
median inflated by the non-periodic 8 cm depth variation relative to whatever
analytic reference the evaluator uses; (d) termination at `max_fixations` rather
than `no_frontier`, as five of Scene-1c's twelve controls did; (e) only then
suspect orchestration or the renderer. **None of (a)-(d) authorizes tuning or
rerendering.** I will not modify the scene, texture, seed, budget, policy,
vergence, fusion or any numerical constant in response to the smoke or either
full run, will not rerender after a numerical miss, and will not use an alternate
seed. I will fix only a demonstrable implementation defect, minimally, after
diagnosis. The raw result is preserved even if ugly.

**Measured outcome, appended after the run (2026-09-21).**
**`REALITY1_COMPLETE`.** Both full records are structurally valid;
`[reality1-compare] REALITY1_COMPLETE` with `integrity_fails: []` and
`quality_gated: false`. No FAIL line was produced anywhere in either run.
Each seed acquired **once** at `full`, 1,258,291,200 primary camera samples
each (2,516,582,400 total), Blender 5.2.1 LTS / Cycles / OPTIX on the RTX 4090,
host scripts under `.venv/bin/python` 3.12.3.

Checks first. `[reality1-scene] PASS depth_range_m 0.08711, target_triangles
120, low_panel_std 0.010764 vs feature_region_std 0.11710` - the target really
is non-planar, really is 120 triangles, and its texture really is mixed by an
order of magnitude in local contrast. `[reality1-policy] PASS frozen_fsg6f=true
quality_gated=false fixed_head=true static_scene=true`, `[reality1-check]
SUMMARY passed=6 failed=0`, all six negatives exit 1 for their own reasons, all
twenty-four prior suites green.

Smoke (seed 2111, `small`, once): `REALITY1_OBSERVATION_COMPLETE`, fails `[]`,
coverage 0.2565 -> 0.5276, median 17.597 mm / P95 46.199 mm, measurement
fraction min 0.8589, worst overlap median 5.96 mm, 5,609 multi-look surfels,
`max_fixations`. Its six gazes are identical to the full seed-2111 run's, so on
this seed the trajectory is profile-independent. Nothing was changed in response
to it.

Full seed **2111**: 6 fixations, `max_fixations`, gazes (-6,-4) (-1,-9) (4,-9)
(9,-9) (14,-4) (14,1); coverage 0.2603 -> **0.5345** (+0.2742) along
0.2603/0.3273/0.4000/0.4267/0.4764/0.5345; approximate surface median **6.188
mm**, P95 19.812 mm; measurement fraction min 0.8516 median 0.8740; worst
overlap median 3.025 mm P95 8.534 mm; 78,656 map points, 21,927 multi-look
surfels; 78.6 s run + 62.3 s eval.

Full seed **2179**: 6 fixations, `max_fixations`, gazes (-6,-4) (-1,1) (4,6)
(9,11) (14,11) (14,6); coverage 0.2604 -> **0.7329** (+0.4725) along
0.2604/0.5141/0.6745/0.7034/0.7034/0.7329; median **5.720 mm**, P95 18.106 mm;
measurement fraction min 0.8400 median 0.8750; worst overlap median 2.897 mm
P95 8.670 mm; 113,874 map points, 27,660 multi-look surfels; 84.0 s run + 94.0 s
eval.

Re-verified independently of the evaluator on both records: `truth_opened`
False, `fixed_head`/`static_scene` True, final map instance ids exactly {141},
every fused patch `idempotent_replay` True, 6 of 6 gazes unique, policy
`FSG6f-candidate-frontier-consensus-v1`, instrument
`FSG1-HDR-SGBM-one-original-update-original-validity-v1`, budget 6 and fusion
{0.012, 0.012} unchanged, and both manifests carrying the same
`public_spec_sha256` baa71ce4b0ae8e36bc0ccf80addad1c0e0e02ec76d7bc8369c37e4258c528f22.

Descriptive, gated by nothing. **Neither seed terminated `no_frontier`**; both
exhausted the six looks still reporting `continue` - the same mode five of
Scene-1c's twelve controls showed. **The two seeds diverge completely after the
prescribed seed fixation**: from the identical (-6,-4) start, 2111's first
autonomous move is (1,-1) and 2179's is (1,+1), and they never reconverge,
ending **19.8 coverage points apart** with nothing differing between the runs
but the Monte-Carlo render seed - the same seed sensitivity Scene-1c's object
203 showed, now on a single-object fixture. **Seed 2179's fifth fixation was
nearly wasted**: at (14,11) the target fills only the view's lower-left corner,
6,128 points, new-point fraction 0.001, coverage unchanged 0.7034 -> 0.7034.
**Measurement fraction never reached calibration-like values** (min
0.8400-0.8516, median 0.8740-0.8750), consistent with the deliberately broad
low-contrast panel. **Overlap consistency is millimetric** - worst per-fusion
overlap medians 2.897-3.025 mm across every fusion of both runs, better than on
the calibration fixtures. **The point-to-surface medians 5.72 and 6.19 mm sit
inside the 4.3-6.6 mm band every earlier FSG6/Scene increment produced**: the
non-periodic 8.4 cm target did not inflate them.

Visual reading, part of the report and not a criterion. `fix_00` is almost
featureless - cream cloth with faint fabric banding against a grey wall, exactly
the low-contrast region the fixture was built to contain; later looks bring in
the printed blue band, the red-orange emblem, the tabletop and a side prop. Both
runs build the map as six roughly rectangular foveal patches tiled edge to edge
with real overlap, not as scattered fragments: 2111 traces an **L** (a band
across the lower half, then a column up the right edge, leaving the upper-left
unvisited), 2179 a **diagonal staircase** from lower-left to upper-right. Sliced
into +/-12 mm horizontal bands against the exported truth mesh, the
reconstructed points **follow the true non-periodic undulation closely wherever
points exist**, a few millimetres of scatter about the curve and no band where
the cloud departs from the surface; the central 98% of reconstructed depths
(2.083-2.158 m and 2.083-2.167 m) coincides with the true span 2.083-2.166 m,
with a thin few-centimetre outlier tail beyond. Depth-coloured, 2179's map shows
coherent large-scale shape - a near region across the top, a far valley through
the middle - that reads as the cloth's fold, not as noise. Patch seams are
faintly visible; the measured disagreement across them is 2.4-3.0 mm. In plain
terms: **recognisable as the hanging cloth, coherent rather than fragmented, in
the right place at the right depth, with no gross wrong-depth region; its
visible deficiency is incompleteness - half to three-quarters of the visible
surface in six looks, the rest simply never visited.** Whether that is good
enough is Luiz/Chat's decision and is deliberately not encoded anywhere in this
record.

Three code fixes, all demonstrable implementation defects, each diagnosed before
being changed; no scientific or numerical behaviour, constant, fixture,
threshold or gate was touched. (1) `tools/dev/check_reality1.py` imported three
`tools/` modules without putting `tools/` on `sys.path` and never imported
`sys`, so the check crashed with `ModuleNotFoundError: No module named
'reality1_public'` - and **the six negatives were exiting 1 only because of that
crash**, false passes rather than controls; fixed with the `sys.path.insert`
every sibling check already has, after which `passed=6 failed=0` and each
negative fails for its own stated reason. (2) `tools/reality1_public.py`
`render_seed` returned `1_000_000 * seed + ...`, which under schedule seed
**2179** is at minimum 2,179,000,420 - above Blender's signed-32-bit Cycles seed
limit 2,147,483,647 - so **every** lattice gaze under 2179 raised `ValueError:
CyclesRenderSettings.seed value not in 'int' range` and seed 2179 crashed 2.5 s
into fixation 0 before rendering anything; fixed by folding into the
non-negative int32 range with `& 0x7FFF_FFFF`, verified to be **the identity
over the whole of seed 2111's domain** (max 2,111,550,421), so the
already-acquired seed-2111 record and the `public_spec_sha256` are unchanged.
Every previous experiment's schedule seeds were <= 1901 and never reached the
limit; 2179 is the first. (3) `tools/dev/check_reality1.py` gained the check
that would have caught (2) before acquisition, per "every tool ships a check
that can fail": every scheduled render seed must lie in [0, 2^31-1] with no
collisions - verified fail-capable, since restoring the pre-fix formula makes it
raise `render seed 2179050100 outside the Cycles signed-32-bit range`. The
crashed attempt is preserved at
`previews/reality1/full-seed2179-crashed-int32seed/` with its Blender log.
Nothing was rerendered after a numerical result, no alternate seed was used, and
the scene, texture, seeds, budget, policy, vergence and fusion are untouched.

What this establishes: on a deliberately less calibration-like static scene the
frozen FSG6f mechanism is **structurally sound and metrically sane** - pure
maps, idempotent fusion, no revisits, millimetric inter-look agreement, and a
recognisable surface at the right depth - while **completing only half to
three-quarters of the visible target in six looks and terminating on budget
rather than on frontier exhaustion, with a trajectory that is sensitive to the
render seed alone**. Preserved exactly as acquired. Stopped for Luiz/Chat, who
decide whether this is good enough and what the next practical step is.

### 2026-09-21 - Reality Check 2, let the observer finish: authorized, prospective entry (written before acquisition)

Per `docs/reality-check-2.md` and D-REALITY2 appended just above. **The literal
continuation of the two saved Reality Check 1 records, not a new experiment.**
Reality Check 1 stands preserved and unedited; nothing below reruns, relabels or
reinterprets it.

Provenance audited before anything was run. HEAD `e9ed914`, clean, on `main`;
**`7c1bfc7` (the Reality Check 1 result) is an ancestor of HEAD**, confirmed by
`git merge-base --is-ancestor`. `git diff --name-status HEAD~1 HEAD` is exactly
eight files, all `A`: `docs/reality-check-2.md`,
`docs/reality-check-2-checks.md`, `tools/reality2_{public,render_fix,run,eval,
compare}.py` and `tools/dev/check_reality2.py`. `git diff HEAD~1 HEAD`
restricted to every FSG1/FSG3/FSG6f source, `fsg_render.py`, `rig.py`,
`bl_common.py` **and every Reality Check 1 source** is EMPTY, confirmed
additionally by per-file sha256 against `7c1bfc7`: `fsg_stereo_supported`
683ae91eaca7b6af, `fsg_stereo_hdr` 67e2ec4667bcc179, `fsg_stereo`
faebf0f1b3acbfde, `fsg_evaluate` a5134b8d8537714d, `fsg_geometry`
d9537d8ebc23b60c, `fsg3_surface_map` 1b9dbeb873105ec9, `fsg6f_public`
c79f58c9b51f33d4, `fsg6f_frontier` d636c9405d719916, `fsg_render`
681237fa8533b7cc, `reality1_public` d2b00211021ff65d, `reality1_run`
c0d4f18a682fd9fe, `reality1_eval` 91720f42932b463c, `reality1_scene`
b4392230292bb51c, `reality1_render_fix` bdc068ad931e1072, `check_reality1`
b057b1d307aebfde - all SAME.

Parent-state audit, **32 of 32 conditions hold on each record**: manifest
present with exactly six unique gazes, `termination_reason` `max_fixations`,
`truth_opened` false, `fixed_head`/`static_scene` true, policy
`FSG6f-candidate-frontier-consensus-v1`, instrument
`FSG1-HDR-SGBM-one-original-update-original-validity-v1`, `public_spec_sha256`
equal to the current `reality1_public` digest
baa71ce4b0ae8e36bc0ccf80addad1c0e0e02ec76d7bc8369c37e4258c528f22, a six-entry
`policy_trace.json` whose final decision has `stop: false` with a
`next_gaze_deg`, and `surface_map.npz` plus `maps/00..05`, `patches/00..05` and
`acquisitions/00..05` all present.

- **seed 2111** gazes (-6,-4) (-1,-9) (4,-9) (9,-9) (14,-4) (14,1), continuation
  gaze **(14,6)**; sha256 `prediction_manifest.json` cd30b47ad26a5447,
  `policy_trace.json` 2bc2172ff0a237ad, `surface_map.npz` 8a77e0530202ddad.
- **seed 2179** gazes (-6,-4) (-1,1) (4,6) (9,11) (14,11) (14,6), continuation
  gaze **(14,1)**; sha256 `prediction_manifest.json` ed8d5d827e0c32c2,
  `policy_trace.json` 3da8322a35508dab, `surface_map.npz` 11520678e2725527.

Each seed's next move is the other seed's already-visited region, which is worth
noting before the data exists but decides nothing.

Checks, all before acquisition. `py_compile` clean on all six new modules.
`[reality2-scene] PASS` with the **same** fixture figures Reality Check 1
recorded (depth_range_m 0.08711, target_triangles 120, low_panel_std 0.010764,
feature_region_std 0.11710) - the scene is byte-identical, not merely similar.
`[reality2-policy] PASS exact_parent_continuation=true frozen_fsg6f=true
scientific_stop=no_frontier watchdog_total=24 quality_gated=false`,
`[reality2-check] SUMMARY passed=7 failed=0`, and all seven negatives exit 1
(`sixlimit`, `rerenderparent`, `scenechange`, `policycopy`, `truth`,
`qualitygate`, `watchdoggate`). The current Reality Check 1 suite is still green
(`passed=6 failed=0`, all six negatives exit 1) and so is FSG6f
(`[fsg6f-check] passed=14 failed=0`).

`reality2_public` digest dba8a00c7f140d14719c14289760af0c160c79770955cecfe27c308622b6362a;
`WATCHDOG_TOTAL_FIXATIONS` 24 = 4 x the retired six-look interruption.

Cost class: checks Interactive; the small continuation smoke and the two full
continuations **Batch** - Reality Check 1 spent about 9 s of Blender per look, so
a continuation that runs to the watchdog would add at most eighteen looks, and
the evaluator's cost grows with total fixation count. If any single command
exceeds five minutes it is reported as such, not split or shortened.

Likely outcomes, in the order I expect them, none of which changes anything:
(a) both seeds continue productively for several looks and then reach
`no_frontier`, the result the check was designed to test for; (b) one or both
run to the **24-fixation watchdog** still reporting `continue` - **an
observation, explicitly not a FAIL**, since Reality Check 1 already showed FSG6f
does not declare resolution on this fixture inside six looks; (c) later looks
returning near-zero new-point fractions, as seed 2179's fifth look already did
at 0.001 - descriptive only; (d) the two seeds converging to similar final
coverage despite their divergent paths, or failing to - either way descriptive;
(e) only then suspect orchestration, the parent loader or the renderer. **None
of (a)-(d) authorizes tuning or rerendering.** I will not modify the scene,
texture, policy, fusion, vergence, seeds, watchdog or any numerical constant in
response to the smoke or to either continuation, will not rerender any Reality
Check 1 view, will not rerender after a numerical disappointment, and will not
use an alternate seed. I will fix only a demonstrable implementation defect,
minimally, after diagnosis. The raw results are preserved even if ugly, and the
report goes back to Luiz/Chat, who interpret whether simply letting the observer
continue is good enough.

**Measured outcome, appended after the run (2026-09-21).**
**`REALITY2_INTEGRITY_FAIL`** under the prospective rule, **because the two full
continuation records do not exist** - not because anything failed an integrity
check. **No structural FAIL line was produced anywhere.** The diagnostic smoke
raised a RUNTIME EXCEPTION, which by the authorization rule blocks full
acquisition, so `previews/reality2/full-seed2111` and
`previews/reality2/full-seed2179` were never created and `reality2_compare.py`
was never run.

Everything upstream of acquisition passed. `py_compile` clean on all six new
modules. `[reality2-scene] PASS` with figures **identical** to Reality Check 1's
(depth_range_m 0.08711, target_triangles 120, low_panel_std 0.010764,
feature_region_std 0.11710) - the same fixture, not a similar one.
`[reality2-policy] PASS exact_parent_continuation=true frozen_fsg6f=true
scientific_stop=no_frontier watchdog_total=24 quality_gated=false`,
`[reality2-check] SUMMARY passed=7 failed=0`, all seven negatives exit 1
(`sixlimit`, `rerenderparent`, `scenechange`, `policycopy`, `truth`,
`qualitygate`, `watchdoggate`). Reality Check 1 still green (`passed=6 failed=0`,
six negatives exit 1) and FSG6f still green (`passed=14 failed=0`). Both parents
audited at **32 of 32 conditions** and untouched afterwards.

**The continuation mechanism itself worked.** The six parent maps were copied
byte-for-byte (verified), acquisition resumed at the recorded `(14,6)` without
rerendering a single Reality Check 1 view, and **seven further looks were
acquired, fused and replayed successfully**. Measured post-hoc, read-only, from
the saved maps: coverage **0.5276 at the Reality Check 1 stop -> 0.7904 seven
looks later, +26.3 points**, map 22,080 -> 33,775 points, 12,282 multi-look
surfels, approximate surface median/P95 16.701 / 46.167 mm (`small` profile,
against Reality Check 1's own smoke at 17.597 / 46.199 mm), map pure in {141},
all thirteen gazes unique, every fused patch replay-idempotent. Per-look
coverage: (+14,+6) +0.0166, (+14,+11) **+0.0012**, (+9,+11) +0.0600, (+4,+11)
+0.0671, (-1,+11) +0.0737, (-6,+11) +0.0442, (-11,+11) **+0.0000**. So removing
the six-look interruption is **not** futile on this fixture - that much is
answered.

**Then, at step 13, the frozen policy selected `(-16, +6)`.** The target spans
yaw **[-12.54, +12.93]**, so that gaze sits **3.5 degrees beyond its left edge**
and the foveal crop contains **zero** target pixels (`oracle_target_px` 0,
`support_on_target` 0, `valid_on_target` 0, against 2,495-6,255 points on each of
the seven preceding looks). The inherited guard `if len(p.xyz_h) < 100` -
**present verbatim in `reality1_run.py` and unchanged in `reality2_run.py`** -
aborted the run with `ValueError: Reality Check 2 fixation has too few target
points`.

Diagnosed before anything was changed, three read-only checks. (1) **The parent
state is reconstructed bit-exactly**: for parent steps 0 and 5 the calibration
loaded from `calibration.json` is key-for-key identical to what
`hdr.read_observation` returns live, and `instance_L`, `raw_support_L`,
`instance_R`, `raw_support_R` all reproduce exactly from the saved patches - the
loader is faithful. (2) **The decision replays deterministically offline**:
feeding frozen `fsg6f_frontier.choose_next` the saved `map_12.npz` (33,775
points), the thirteen-gaze history and the thirteen-entry observation history
returns `stop: False, next_gaze_deg: [-16.0, 6.0]`, with no renderer involved.
(3) **It is the specified ranking doing exactly what it specifies**: three
candidates, all consensus-allowed and all corridor-allowed - `(-16,+6)` area
**128.93 deg²**, score 29.85, OPEN 77, BOUNDARY 21, corridor fraction **0.327**;
`(-11,+6)` area 80.94, score 38.69, OPEN 95, BOUNDARY 0, corridor 0.898;
`(-6,+6)` area 32.94, score 24.84, OPEN 72, BOUNDARY 0, corridor 1.000. FSG6f's
frozen key is `(-area, -score, |dyaw|+|dpitch|, yaw, pitch)`, so **the largest
predicted new area wins outright** despite having the lowest corridor fraction,
the lowest frontier score and the only non-zero resolved-boundary count; the
strict OPEN-majority rule passes it because 77 > 0 + 21.

**No code fix was made and no source file was modified.** This is frozen-policy
behaviour, not an implementation defect: deciding what an off-object look should
mean in a continue-until-`no_frontier` regime - abort, skip, stop, or fuse
nothing and carry on - is a change to the experiment's stopping semantics, which
D-REALITY2 and the authorization explicitly reserve to Luiz/Chat. Nothing was
rerendered, no alternate seed was used, and the scene, texture, policy, fusion,
vergence, seeds, watchdog and every numerical constant are untouched. The
blocked smoke is preserved at `previews/reality2/smoke-seed2111/` with its eight
acquisitions, seven new maps and render logs.

What this establishes: the exact-continuation machinery is sound and **letting
the observer keep looking does produce substantial useful new surface** - seven
more looks, +26.3 coverage points, geometry and purity intact. **Whether frozen
FSG6f ever reaches `no_frontier` on this fixture remains unknown**, because
before it could stop it chose a look entirely off the target. The record now
holds **two independent demonstrations that FSG6f's area-first ranking can walk
off a fixture** - FSG6c's `max()` case at three looks, and this one at thirteen -
which is evidence about the object controller, not about the scheduler or the
scene. Stopped for Luiz/Chat, who decide what an off-object look means here and
whether simply letting the observer continue is good enough.

### 2026-09-21 - Reality Check 2b, learn from an empty look: authorized, prospective entry (written before acquisition)

Per `docs/reality-check-2b.md`, `docs/reality-check-2b-checks.md` and D-REALITY2b
appended just above. **One semantic change relative to Reality Check 2: a
completed fixation with fewer than 100 reconstructed target points is negative
perceptual evidence, not a runtime failure.** Reality Checks 1 and 2 stand
preserved and unedited.

Provenance audited before anything was run. `git status --short` empty; HEAD
**`e962ff6`** ("Add Reality Check 2b empty-look recovery") on `main`;
**`27cfcc2` (the Reality Check 2 result) is an ancestor of HEAD**, confirmed by
`git merge-base --is-ancestor`. `git diff --name-status HEAD~1 HEAD` is exactly
the seven authorized files, all `A`: `tools/reality2b_{public,run,eval,
compare}.py`, `tools/dev/check_reality2b.py`, `docs/reality-check-2b.md`,
`docs/reality-check-2b-checks.md`.

`git diff HEAD~1 HEAD` restricted to every FSG1/FSG3/FSG6f source, the renderer,
`fsg_scene.py`, `fsg_validation_render.py`, `rig.py`, `bl_common.py`,
`requirements-fsg.txt` **and every Reality Check 1 and Reality Check 2 source**
is EMPTY, confirmed additionally by per-file sha256 against `27cfcc2` - all
SAME: `fsg_stereo_supported` 683ae91eaca7b6af, `fsg_stereo_hdr`
67e2ec4667bcc179, `fsg_stereo` faebf0f1b3acbfde, `fsg_evaluate`
a5134b8d8537714d, `fsg_geometry` d9537d8ebc23b60c, `fsg3_surface_map`
1b9dbeb873105ec9, `fsg6f_public` c79f58c9b51f33d4, `fsg6f_frontier`
d636c9405d719916, `fsg6f_run` f2d4bdd54b8d395f, `fsg_render` 681237fa8533b7cc,
`fsg_scene` 1f410577c1103e01, `fsg_validation_render` f18883e1e2764dd7, `rig`
dff43ec0cd9d5047, `bl_common` aa7a56e8cd4988cb, `reality1_public`
d2b00211021ff65d, `reality1_run` c0d4f18a682fd9fe, `reality1_eval`
91720f42932b463c, `reality1_scene` b4392230292bb51c, `reality1_render_fix`
bdc068ad931e1072, `reality2_public` c7e7bd44d1a28de3, `reality2_run`
2b846a3413500dfc, `reality2_eval` ebfaa9e036db224b, `reality2_render_fix`
9f1433d189fbcbb5, `check_reality1` b057b1d307aebfde, `check_reality2`
ca832846a44b88bc.

Checks, all before acquisition. `py_compile` clean on all five new modules.
`[reality2b-policy] PASS exact_parent_continuation=true frozen_fsg6f=true
empty_look_is_evidence=true empty_fuses=false scientific_stop=no_frontier
watchdog_total=24 quality_gated=false`, `[reality2b-check] SUMMARY passed=7
failed=0`, and **all ten deliberate negatives exit 1** for their own named
reasons: `abortempty`, `skipempty`, `dropgaze`, `fuseempty`, `sixlimit`,
`rerenderparent`, `policycopy`, `truth`, `qualitygate`, `watchdoggate`. Prior
suites green and their negative sets still firing: `[reality1-check] passed=6
failed=0` with six negatives exit 1, `[reality2-check] passed=7 failed=0` with
seven negatives exit 1, `[fsg6f-check] passed=14 failed=0` with **15 of 15**
negatives exit 1.

Where the fail-capable map-invariance check lives, for the record: the runner
asserts the map is untouched around an empty look, but the load-bearing check is
evaluator-side - `reality2b_eval` reloads the saved `map_{step-1}` and
`map_{step}` from disk and fails the record if they differ, so a no-fusion step
that silently mutated the map could not pass.

Cost class: checks Interactive; the smoke and the two full continuations
**Batch**. Reality Check 2 spent about 9 s of Blender per look and its `small`
continuation ran 34 s for eight looks; a full continuation that runs to the
24-fixation watchdog adds at most eighteen looks, and the evaluator's cost grows
with total fixation count. If any single command exceeds five minutes it is
reported as such, not split or shortened.

Likely outcomes, in the order I expect them, none of which changes anything:
(a) the empty look at roughly (-16,+6) is recorded, resolves the false frontier
through FSG6f's existing BOUNDARY_RESOLVED mechanism, and the observer returns to
useful target surface - the result this check exists to test for; (b) recovery
happens but the run reaches the **24-fixation watchdog** still reporting
`continue` - an observation, explicitly not a FAIL; (c) repeated off-target
exploration, several empty looks in a row, because area-first ranking keeps
preferring the largest predicted new area - descriptive only; (d) the two seeds
ending at different fixation counts or different completeness - descriptive
either way; (e) only then suspect the new no-fusion path, zero-point patch
handling in visualization/serialization, history insertion order, or
parent-state provenance. **None of (a)-(d) authorizes tuning or rerendering.** I
will not alter FSG6f, the `<100` inherited condition, ranking, scene, texture,
seeds, vergence, fusion, parent views or the 24-look watchdog in response to any
result; I will not rerender a completed numerical result and will not use an
alternate seed. I will fix only a demonstrable implementation defect **in the new
Reality 2b files**, minimally, after diagnosis. All outcomes are preserved,
including watchdog termination, repeated off-target exploration and any crashed
attempt, and the report goes back to Luiz/Chat.

**Measured outcome, appended after the run (2026-09-21).**
**`REALITY2B_COMPLETE`.** Both full records are structurally valid,
`integrity_fails` empty in both per-run evaluations and in the aggregate, and
**no FAIL line was produced anywhere**. **Both terminated by the scientific rule,
`no_frontier`; neither reached the 24-look watchdog.** The Reality Check 2
blockage is resolved, and it was exactly what the diagnosis said: an artifact of
treating negative perception as a runtime error.

Checks first, all before acquisition. `py_compile` clean on all five new
modules. `[reality2b-policy] PASS exact_parent_continuation=true
frozen_fsg6f=true empty_look_is_evidence=true empty_fuses=false
scientific_stop=no_frontier watchdog_total=24 quality_gated=false`,
`[reality2b-check] SUMMARY passed=7 failed=0`, **all ten deliberate negatives
exit 1** for their own named reasons. Prior suites green with negative sets still
firing: reality1 6/6 (+6 negatives), reality2 7/7 (+7), fsg6f 14/14 (+**15/15**).
The installed package adds exactly the seven authorized files, all `A`, and the
diff over every FSG1/FSG3/FSG6f, renderer, rig, pin **and Reality Check 1/2**
source against `27cfcc2` is empty.

Smoke (`small` seed 2111, once): `REALITY2B_OBSERVATION_COMPLETE`, fails `[]`,
14 fixations (8 new), **one empty observation at step 13, termination
`no_frontier`**, coverage 0.5276 -> 0.7904, median/P95 16.705 / 46.167 mm,
12,286 multi-look surfels. Structurally clean, so full acquisition proceeded;
nothing was changed in response to it.

Full **seed 2111**: **13 fixations (7 new), `no_frontier`**, watchdog not
reached, 1 empty observation at step 12. Coverage **0.5345 -> 0.7984 (+0.2639)**;
median **5.878 mm**, P95 18.599 mm; measurement fraction min 0.8466 median
0.8740 over fused looks; worst overlap median 3.025 mm P95 8.534 mm; 117,567 map
points and **48,350 multi-look surfels (41.1%)**; 1,468,006,400 new samples;
94 s run + 176 s eval.

Full **seed 2179**: **16 fixations (10 new), `no_frontier`**, watchdog not
reached, 2 empty observations at steps 14 and 15. Coverage **0.7329 -> 0.8834
(+0.1505)**; median **5.812 mm**, P95 18.858 mm; measurement fraction median
0.8555 (min 0.0629 is itself an empty look); worst overlap median 2.897 mm P95
8.759 mm; 138,010 map points and **57,571 multi-look surfels (41.7%)**;
2,097,152,000 new samples; 135 s run + 296 s eval.

Every empty observation, in full. **seed 2111 step 12, gaze (-16,+6)**: 0 target
points from 0 reference pixels; map before/after bitwise identical (117,567 ->
117,567 points, support sum 173,427 -> 173,427 across `xyz_h`, `rgb`,
`instance_id`, `support_count`, `provenance_mask`), re-verified outside the
evaluator; the **immediate** policy response was `stop: True, reason:
no_frontier` with zero candidates offered. **seed 2179 step 14, gaze (-16,-4)**:
25 target points from 317 reference pixels (fraction 0.0789); map identical
(138,010 -> 138,010, support sum 214,527 -> 214,527); the immediate policy
response was **`stop: False, reason: continue, next_gaze_deg (-16,+1)`** with two
surviving candidates, `(-16,+1)` area 123.71 / score 10.19 / OPEN 23 / MAP 1 /
BND 3 and `(-11,+1)` area 63.71 / score 5.78 / OPEN 17 / MAP 1 / BND 0 - **this
is the recovery behaviour the experiment was built to test: the observer
incorporated a near-empty look and kept going instead of failing**. **seed 2179
step 15, gaze (-16,+1)**: 11 points from 175 reference pixels (0.0629); map
identical; `stop: True, reason: no_frontier`, zero candidates.

A precise note so a flag is not misread: the evaluator's
`recovered_after_first_empty` is `false` for both seeds, but it is defined as *a
later look that actually fused >= 100 target points*. Neither seed had one
because in both cases the empty looks fell at the very end. It does **not** mean
the policy failed to continue - seed 2179 demonstrably did.

Structure re-verified independently of the evaluator on both records: parent
`maps/map_00..05.npz` **byte-identical** to the Reality Check 1 source, **no
parent acquisition directory recreated** (not one of the twelve saved views was
rerendered), `truth_opened` False, fixed head and static scene True, map instance
ids exactly {141}, every *fused* patch `idempotent_replay` True (12/12 and
14/14) with the empty entries carrying `fused: false` and no idempotence claim,
all gazes unique (13/13 and 16/16), and frozen policy, instrument, fusion, the
`<100` limit and the watchdog unchanged.

Two-seed comparison. Both `no_frontier`; fixation counts differ by 3 (13 vs 16);
trajectories still completely different - 2111 sweeps the top row right-to-left,
2179 the right column then the bottom row. But **the final reconstructions are
far more comparable than Reality Check 1's**: the coverage gap **narrowed from
0.1984 at look 6 to 0.0850**, the surface medians differ by 0.066 mm and the
P95s by 0.26 mm, both maps are ~41% multi-look, and the seed that was behind
gained more (+0.2639 vs +0.1505). **Seed divergence became largely an efficiency
difference rather than a quality difference.**

Visual reading, descriptive and not a score. Empty looks are plainly visible and
exactly where the numbers say - seed 2111's `fix_12` shows grey wall and a blue
side prop with no cloth at all; seed 2179's `fix_14` is the blue prop and wall
with a sliver of cloth at the top edge. The added looks **fill rather than
wander**: seed 2111 climbs from the bottom band into the whole top row it had
never seen (y extent -0.319..0.261 at look 6 -> -0.319..**0.400**, against a true
span of -0.326..0.405) and seed 2179 wraps the right edge and the entire bottom
row. Sliced into +/-12 mm bands against the exported truth mesh, the points track
the true non-periodic undulation closely across every band including the new top
ones, with no band where the cloud departs from the surface, and multi-look
proportion roughly doubled (27.9% -> 41.1%, 24.3% -> 41.7%). **No gross
wrong-depth region appeared.** Termination is **sensible in mechanism but
premature in result**: both stopped by their own rule immediately after an empty
look resolved the frontier in that direction, yet seed 2111's final map is
visibly a **ring** - the observer swept the perimeter and declared `no_frontier`
with a large unvisited rectangular hole still in the middle of the cloth, which
is most of its missing 20%; seed 2179 ends far more complete with one small
square hole in the lower right. **`no_frontier` here means "no open frontier
reachable from the perimeter I walked", not "the surface is finished".**
Efficiency is also worth recording: **five of the seventeen new fused looks
returned under 1% new points**.

**No code fix was made and no source file was modified.** Every failure mode the
authorization listed was checked against the acquired records and none occurred:
the zero-point patch serialized, visualized and evaluated without incident; both
empty observations are present in the gaze list and the binocular history before
`choose_next`, proven by the policy trace carrying
`observation_was_empty_target: true`; every no-fusion step left the map bitwise
unchanged; the evaluator requires idempotence only of patches actually fused; and
parent provenance is exact.

What this establishes: **an empty look can be negative perceptual evidence, and
that single semantic change is enough for the unchanged observer to finish by its
own rule.** Both seeds now terminate `no_frontier` instead of being interrupted
or crashing, coverage rises to 0.798 and 0.883, geometry stays at ~5.8 mm median,
and the two stochastic trajectories converge to comparable quality. What it does
**not** establish is completeness: frozen FSG6f declares `no_frontier` while a
large interior hole remains on seed 2111, so the open question moves from "can
the observer continue?" to **"why does the frontier rule consider an enclosed
interior hole resolved?"** - which is about FSG6f's frontier/consensus rule, not
the scheduler, the scene or the stopping semantics. Stopped for Luiz/Chat.
