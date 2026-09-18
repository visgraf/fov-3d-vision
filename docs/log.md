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
