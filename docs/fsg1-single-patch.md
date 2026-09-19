# FSG1 - Single-patch foveal stereo instrument

Status: run on the workstation 2026-09-19, small and then full. Software checks
and both deliberate negatives pass. The small/64-spp suite FAILS the interior gate
on the `step` 3.4 m background (accuracy); the full/256-spp suite authorized by
D-FSG1a FAILS it on the `step` 1.6 m foreground (coverage), while every accuracy
target in the suite is met. No `MILESTONE_PASS`. Half-occlusion is NOT EXERCISED.
See the Workstation Results section; the Chat/synthetic record below it is as written.

## Question and scope

Can a directly acquired, locally uniform perspective stereo pair produce usable
metric geometry before we add a persistent surface map or a gaze policy?

This is increment 1 of Foveal Surface Growing, an opt-in experiment alongside the
Phase C/D engine. It does not replace that engine, its OSL camera, profiles,
records, matcher, belief, or policy. There is no multi-patch fusion, frontier
exploration, peripheral preview, object switching, or learned model yet.

### Agreed design

* Blender object IDs provide oracle instance segmentation only. A logical object
  can group several mesh objects by assigning them the same `pass_index`.
* The map frame H is FIXED to the head: origin at the midpoint of the eyes,
  +X right, +Y up, -Z initial gaze. Saccades do not rotate H.
* Blender world W is distinct. `head_R_wh` and `head_origin_w_m` implement
  `X_w = head_R_wh @ X_h + head_origin_w_m`.
* The eye centres are fixed at (+/-0.0315, 0, 0) metres in H. Per-eye camera
  orientations come from the existing `rig.py` zero-torsion vergence convention.
* All reconstructed geometry comes from RGB and calibration. No true depth,
  positions, normals, surface planes, or correspondences enter the estimator.
* The initial 2 m vergence distance is a prescribed acquisition setting, not a
  depth read from the scene. The depth-search interval is declared in advance.

The direct perspective renders are a deliberate hybrid-sensor approximation:
they test a movable high-quality foveal measurement, not information recovered
by magnifying low-resolution peripheral samples. No efficiency or biological
fidelity claim follows from this increment alone.

## Files

| File | Role / check |
| --- | --- |
| `tools/fsg_geometry.py` | NumPy frame, ray, projection and crop conventions; `--self-test` |
| `tools/fsg_scene.py` | Three procedural fixtures, texture and calibration-mesh intersector; `--self-test` |
| `tools/fsg_render.py` | Blender acquisition; independent camera-projection and ray-cast checks |
| `tools/fsg_stereo.py` | Host rectification, SGBM, bounded refinement, validity, head-frame points |
| `tools/fsg_evaluate.py` | Fixed-reference geometry evaluation; an explicit pass/fail gate |
| `tools/dev/fake_blender_fsg.py` | Synthetic backend for acquisition/file plumbing, NOT Blender emulation |
| `tools/dev/check_fsg.py` | Positive checks, negatives, ground-truth-removal and provenance checks |
| `requirements-fsg.txt` | Add-on OpenCV dependency, host interpreter only |
| `docs/fsg1-code-prompt.md` | Ordered workstation execution and reporting instructions |

The new tools use their own `FSG1-*` schemas; they do not claim compatibility with
Phase A-D sample records. NumPy, standard library, and Blender's own modules are
the only imports on the Blender side. OpenCV and Pillow belong to the host venv.

## Three independent observations

Each case rebuilds a small procedural scene in the same Blender session and
acquires ONE binocular pair. It is not a trajectory or a reconstruction loop.

| Case | Geometry and acquisition |
| --- | --- |
| `fronto` | 3 m square textured plane, 2 m in front of H; central fixation |
| `tilted` | Textured plane rotated 25 degrees relative to the local viewing direction; fixation yaw +14, pitch -7 degrees; tests noncentral vergence and coordinate transforms |
| `step` | Foreground half-plane at 1.6 m, background at 3.4 m, different IDs; tests discontinuity, masking, and half-occlusion |

Materials are opaque diffuse surfaces with repeatable aperiodic image textures;
lighting is a world background plus an area light. Depth of field, motion blur,
adaptive sampling, and denoising are disabled. RGB is linear float32 in the saved
observation; both eyes use the SAME fixed conversion for SGBM. Seeds are distinct
between eyes, and recorded. There are no downloaded assets.

The fixtures use ordinary Cycles light transport. Their simplicity is deliberate;
a successful calibration result is not a complex-scene reconstruction result.

## Acquisition settings and cost

| Setting | small | full |
| --- | ---: | ---: |
| Accepted central rectified core | 128 x 128 | 256 x 256 |
| Raw raster, per eye | 320 x 320 | 640 x 640 |
| Nominal core field | 12 degrees | 12 degrees |
| Raw field | about 29.4 degrees | about 29.4 degrees |
| Default spp from current `bl_common.PROFILES` | 64 | 256 |
| Primary camera samples per pair at those spp | 13,107,200 | 209,715,200 |
| Three-case suite at those spp | 39,321,600 | 629,145,600 |

Counts above are computed prescriptions, NOT measured timings. The extra pixels
are intentional search/rectification margins. Their full cost is counted even
though they are not inserted into the accepted core. This increment is an
accuracy instrument, not a padding or throughput optimization.

The default full spp follows the repository's working agreement (256), rather
than the earlier provisional 64-spp outline. `--spp` is an explicit recorded
override for a separately labelled diagnostic, never an invisible profile change.
`bl_common.PROFILES` and the original requirements file are not modified.

The exact post-rectification focal length and crop are stored. Do not assume the
accepted angular footprint is exactly the nominal value after rectification.
No peripheral discovery preview is acquired, so none is charged in this step.
Primary camera samples are not secondary path-ray counts. `render_seconds_lr`
measures render calls, `oracle_seconds` measures annotation, and `case_seconds`
and `run.json:total_wall_seconds` include setup and I/O within the Python entry.
Blender process startup is not included in that last counter.

## Stereo computation

1. Rectify both full padded RGB images using the known, converged camera poses.
   `cv2.stereoRectify` uses zero distortion, `CALIB_ZERO_DISPARITY`, and `alpha=-1`.
2. Match full images with SGBM_3WAY in both directions. Block size 5, uniqueness
   ratio 10, fixed P1/P2, and disparity bounds derived from rectified axial
   depth [0.75, 4.5] m. OpenCV's 1/16-pixel outputs are decoded explicitly.
3. Refine each selected disparity locally using float-luminance photometric
   alignment: three Gauss-Newton steps, <=0.5 pixel per step, <=0.75 pixel total
   departure from SGBM. This is evidence-based subpixel refinement, not a depth
   correction fitted to ground truth. It cannot recover a wrong matching peak.
4. Reject unsupported pixels, inconsistent disparities (>1 pixel left-right
   residual), object-ID mismatch, a narrow 3-pixel instance boundary guard,
   essentially textureless pixels (local std <0.5 in fixed-conversion uint8),
   nonpositive/out-of-range depth, and OpenCV's invalid disparity ROI.
5. Reproject with the full rectification Q, transform to H, THEN crop the core.
   Preserve both the SGBM disparity and the refined disparity for diagnosis.

RGB images are NOT blacked out outside object masks. Masks gate correspondences;
they do not make SGBM's internal regularization segmentation-aware. Texture and
left-right residual are diagnostic quantities, not calibrated probabilities.

### Three easy-to-miss geometry distinctions

* The rectifier produces geometric disparity. Vergence does NOT mean the returned
  disparity at fixation is automatically zero. No residual disparity is inserted
  into `Z=fB/d` without restoring its offset.
* Q refers to full image coordinates. `Q_core` includes the common crop, and
  `crop_q` also supports distinct horizontal crops with the correct disparity
  offset. Unequal vertical crops are explicitly rejected.
* `z_rect_m` is axial depth in the left RECTIFIED camera. `range_left_m` is distance
  from the physical left eye. `xyz_h` is position in the FIXED head frame. They
  are not interchangeable.

## Oracle segmentation and independent truth

For these opaque calibration fixtures, the oracle ID is the Blender object's
`pass_index` at the first pixel-centre ray intersection. It is not an RGB-derived
segmentation and is not antialiased. This implementation avoids a dependency on
version-specific multi-layer compositor interfaces.

The renderer exports triangles from Blender's EVALUATED mesh objects, transformed
to H. A small NumPy triangle intersector computes ID masks. Its hits and IDs are
cross-checked at 121 rays per eye against Blender `Scene.ray_cast` before rendering
proceeds. Blender `world_to_camera_view` independently checks the declared camera
intrinsics, pose, and pixel-centre convention at those sample locations.

Required in-session checks: maximum projection discrepancy <=0.002 pixel,
maximum hit-position discrepancy <=20 micrometres, matching IDs, and enough
actual hit rays. These tolerate Blender's float precision; they are calibration
checks, not stereo-error targets.

The evaluated triangles go under `evaluation_only/`. The sensor NPZ contains
EXACTLY RGB_L, RGB_R, instance_L and instance_R (keys use lower-case `rgb_`). The
estimator rejects unexpected keys, including accidentally supplied depth.

The evaluator casts independent centre rays on a fixed rectified-left grid and
checks visibility from the right eye. Its reference includes ALL eligible pixels,
not just the points the stereo estimator happens to return. The reference is
therefore not improved by rejecting difficult estimates. Boundary and singly
visible regions are reported separately; they are never filled with invented
intermediate depths. Per-instance interior results prevent the background from
concealing poor foreground reconstruction.

These truths describe first-hit opaque geometry. Extending them to transparency,
volumetrics, motion blur, or mixed-depth pixel footprints is outside FSG1.

## Prospective acceptance rule

On each case, and each instance with at least 100 eligible interior pixels:

* accepted coverage >=90%;
* median absolute relative LEFT-EYE RANGE error <=1%;
* 95th-percentile absolute relative LEFT-EYE RANGE error <=3%.

The interior excludes a fixed band around GT instance/depth boundaries: radius
4 pixels at small, 8 at full (the same nominal angular margin). Boundary errors,
coverage, incorrect object labels, and singly-visible acceptance are reported
but have no invented pass threshold in this first milestone.

Empty reconstructions, stale input fingerprints, missing cases, and synthetic
provenance cannot pass the production gate. `SMALL_PROFILE_PASS` is not a full
milestone pass. Only a real full-profile suite with independent Blender checks
at its default sample count can produce `MILESTONE_PASS`. A sample-count override
can at most produce `DIAGNOSTIC_PASS_NONDEFAULT_SPP`, not a standard milestone pass.

The original user targets remain unchanged. If actual workstation measurements
miss them, stop: do not lower the targets, enlarge the boundary exclusion, shrink
the reference denominator, substitute truth, or change the fixtures to manufacture
a pass. Diagnose a genuine implementation bug separately from an algorithm limit.

## Record layout

```
previews/fsg1/<profile>-seed17/
    run.json                      # written last; complete acquisition marker
    fronto/                       # also tilted/, step/
        calibration.json          # sensor geometry and prescribed settings only
        observation.npz           # RGB + oracle IDs, no geometric truth
        acquisition.json          # provenance, timings, costs, independent checks
        L.exr, R.exr               # real Blender runs; linear single-layer RGB
        fixture.blend             # when --save-blend is requested
        evaluation_only/mesh.npz   # evaluated Blender triangles; evaluator only
        stereo/
            result.npz            # points, ranges, validity, disparity, full Q/maps
            summary.json          # parameters, input SHA-256, time, acceptance count
            points_head.ply       # head-frame positions, RGB, object IDs
            rectified_L.png, rectified_R.png
            disparity.png, range_left.png, validity.png
        evaluation/
            metrics.json
            truth_range_left.png, relative_range_error.png
            reference_interior.png, reference_boundary.png
    evaluation.json               # complete suite report, including every FAIL
```

Grayscale depth/disparity previews use black for invalid and a fixed documented
range for valid values; they are diagnostics, not normalized-to-look-good images.
Range uses [0.75,4.5] m, error uses [0,5%], disparity uses the declared search.
The floating-point NPZ is authoritative. PLY is an unmeshed colored point cloud,
not a surfel map or an object-completion result.

All these generated artifacts stay under gitignored `previews/`. Only scripts,
this note, the measured Results write-up and project log/decision entries are
committed.

## Checks run in Chat (2026-09-19)

Environment actually used: Python 3.13.5, NumPy 2.3.5, OpenCV 4.13.0, Pillow 12.3.0.
This is NOT the repository's pinned NumPy 2.2.6 workstation environment.
No Blender or bpy was installed. Direct git clone failed due network/DNS;
relevant public `main` source files were read through the web tool instead.
No upstream commit hash or successful full-checkout integration is claimed.
The additive installer records the destination checkout's HEAD when applied;
Code must run the real repository-rig check there.

Measured software result: 23 checks passed, zero failed, about 2.7 seconds in
this sandbox. Included exact off-axis/crop triangulation, deliberate baseline
and crop faults, empty/blank input, stale records, failed-run completion markers,
synthetic provenance rejection, and identical reconstructed arrays after truth
removal for every fixture. A synthetic backend executes the production acquisition
orchestrator; it does NOT test BlenderBackend's bpy calls or Cycles pixels.

Measured SYNTHETIC interior results (source `synthetic_stub`; 0 actual Cycles rays):

| Profile / case | Accepted coverage | Median relative range error | P95 relative range error |
| --- | ---: | ---: | ---: |
| small / fronto | 100.000% | 0.312% | 1.004% |
| small / tilted | 99.994% | 0.400% | 1.481% |
| small / step | 99.987% | 0.296% | 1.371% |
| full / fronto | 99.908% | 0.318% | 1.161% |
| full / tilted | 99.768% | 0.347% | 1.383% |
| full / step | 99.939% | 0.234% | 1.262% |

All per-instance synthetic gates passed too. These figures are software-fixture
results, NOT evidence that photorealistic Blender stereo meets the target.
Raw check reports and synthetic example images are in the handoff's validation
folder, outside the repository payload, so they are not committed as assets.

### Engineering diagnosis before handoff

The initial SGBM-only fixture missed the 1% background median target (about 1.42%
small and 1.62% full). Its arbitrary 2/255 texture cutoff also rejected about
10.6% of the full fronto/tilted core despite correct correspondences. The fix was
to improve the estimator, not its evaluator: retain almost-flat rejection at
0.5/255 and add bounded float-photometric subpixel refinement. The evaluator's
90% / 1% / 3% targets and reference construction were not changed. Both disparity
versions are saved so the workstation can inspect that engineering choice.

This is a development-fixture check, not a held-out algorithm benchmark.

## Workstation Results - small profile RUN and FAILED; full profile NOT RUN

Run 2026-09-19 on the workstation by Code. Every number below is read from a file
under `previews/fsg1/`; the Chat/synthetic record above is unchanged. The small
profile missed the gate on one instance, so under `docs/fsg1-code-prompt.md` step 5
the full-profile suite was NOT run and there is no `MILESTONE_PASS`.

* Checkout HEAD before/after: `1fbe81ce5f7603d4c706cf26ebc32972a54a8442` before;
  this write-up is the only change after. Working tree was clean at preflight.
* Blender version, GPU/backend, Python, NumPy, OpenCV: Blender 5.2.1 LTS
  (hash 9e2066aef7ef, build 2026-08-25), device `OPTIX` on an NVIDIA GeForce
  RTX 4090 (driver 595.84); host Python 3.12.3, NumPy 2.2.6, Pillow 12.3.0,
  OpenCV 4.13.0 (`opencv-python-headless==4.13.0.92`, newly installed from
  `requirements-fsg.txt`; it was the only OpenCV in the venv and no existing pin
  moved). NumPy is the repository's pinned 2.2.6, not the sandbox's 2.3.5.
* Exact commands and output directories:
  `tools/rig.py --self-test`, `tools/fsg_geometry.py --self-test`,
  `tools/fsg_scene.py --self-test`,
  `tools/dev/check_fsg.py --self-test --repo-check --report previews/fsg1/software-checks.json`,
  `tools/dev/check_fsg.py --negative baseline`, `--negative crop`;
  `blender -b --python-exit-code 1 -P tools/fsg_render.py -- --out previews/fsg1/small-seed17 --profile small --device OPTIX --seed 17 --save-blend`;
  `tools/fsg_stereo.py previews/fsg1/small-seed17`; `tools/fsg_evaluate.py previews/fsg1/small-seed17`.
  Labelled diagnostic only: the same acquisition with `--spp 1024` into
  `previews/fsg1/diag-small-spp1024-seed17`, plus its stereo pass. No full profile.
* Repo-rig / software summary lines: `[rig] self-test ok`,
  `[fsg-geometry] self-test PASS`, `[fsg-scene] self-test PASS`, and
  `[fsg-check] SUMMARY passed=24 failed=0 seconds=1.829 blender_executed=False`.
  The 24th is `PASS current repository rig integration` against this checkout's
  `tools/rig.py`; `blender_executed=False` is correct, the suite claims no render.
* Deliberate-negative exit codes and verbatim FAIL lines: both exit 1, both a
  geometry failure rather than an import error.
  `[fsg-check] FAIL deliberate baseline mutation: max known-point 3D error=0.798831399 m; limit=1e-7 m`
  `[fsg-check] FAIL deliberate crop mutation: max known-point 3D error=2.37076271 m; limit=1e-7 m`
* Per-eye projection/ray-cast checks from `acquisition.json` (limits 0.002 px and
  20 um; 242 rays checked per case, 121 per eye, all IDs matching):

  | case | projection_max_error_px | raycast_max_error_m |
  | --- | ---: | ---: |
  | fronto | 3.774e-05 | 3.667e-07 |
  | tilted | 8.189e-05 | 5.797e-07 |
  | step | 3.774e-05 | 7.219e-07 |

  Every `acquisition.json` reads `source: blender_cycles`, `device: OPTIX`,
  `blender_version: 5.2.1 LTS`, `adaptive_sampling: false`, distinct L/R seeds,
  and `independent_blender_checks: true`. No `synthetic_stub` anywhere.
* Small per-case and per-instance metrics from `metrics.json` (interior; targets
  >=90% coverage, <=1% median, <=3% p95):

  | case / instance | coverage | median rel. range | p95 rel. range | ref px |
  | --- | ---: | ---: | ---: | ---: |
  | fronto | 98.395% | 0.388% | 1.315% | 16384 |
  | tilted | 99.823% | 0.463% | 1.680% | 16384 |
  | step (pooled) | 94.101% | 0.358% | 2.965% | 15104 |
  | step instance 1 (1.6 m) | 90.361% | 0.187% | 0.792% | 9088 |
  | step instance 2 (3.4 m) | 99.751% | **1.136%** | **4.111%** | 6016 |

  `fronto` and `tilted` pass on every criterion. The pooled `step` figures also
  pass; the per-instance split is what catches the background, which is exactly
  what the per-object rule in D-FSG1 exists to prevent being hidden.
  `wrong_instance_accepted_count` is 0 in all three cases.
  Full profile: not run, so no numbers are claimed.
* Boundary and singly-visible diagnostics: only `step` has any boundary reference
  pixels (1280): coverage 30.859%, median 0.900%, p95 7.456%, and 31.139% of
  accepted boundary pixels exceed 3% relative error. That is the expected cost of
  SGBM regularisation across an 1.8 m discontinuity and has no pass threshold in
  FSG1. `singly_visible` has 0 reference pixels in all three cases, including
  `step`. This is geometry, not a missing test: the foreground half-plane lies on
  the left of the frame, so the background the left eye can see is never the part
  the foreground hides from the right eye. The half-occluded strip belongs to the
  right eye and so is absent from a left-eye reference grid. A fixture with the
  step mirrored would be needed to exercise a left-eye half-occlusion.
* Primary samples, render/stereo/annotation/process times: 13,107,200 primary
  camera samples per case and 39,321,600 for the suite, matching the prescription
  in this note. Per case, render (L+R) / oracle annotation / case seconds:
  fronto 0.2666 / 0.0469 / 0.6122; tilted 0.2125 / 0.0406 / 0.4870;
  step 0.2122 / 0.0586 / 0.5070. `run.json:total_wall_seconds` 1.6064; the whole
  Blender process took 2.149 s wall. Stereo: fronto 0.0503 s, tilted 0.0343 s,
  step 0.0283 s. These are Interactive-class, well inside the estimate.
* Files viewed (RGB, validity, predicted/truth depth, error, point cloud): the
  rectified L/R pair, `disparity.png`, `range_left.png`, `validity.png`,
  `truth_range_left.png`, `relative_range_error.png`, `reference_interior.png`
  and `reference_boundary.png` for all three cases, as one contact sheet.
  `fronto` is a flat mid-grey disparity field; `tilted` shows a monotonic gradient
  whose sign agrees with its truth range map, which rules out a vertical flip;
  `step` shows the near half bright in disparity and dark in range, with the
  interior/boundary masks complementary across a vertical band at the edge, and
  visibly noisier relative error on the far half - the failing instance is visible
  in the image, not only in the metric. Independent of the images, the head-frame
  point geometry is right: `step` instance medians Z = -1.5991 m and -3.3937 m
  against -1.6 and -3.4; `fronto` Z = -1.999 m; and the `tilted` plane normal fits
  at 25.5 degrees from the gaze direction (specified 25) while sitting 13.2 degrees
  from head -Z, so the fixed head frame is not being confused with Blender world.
  `points_head.ply` parses as 14,608 vertices, no faces, the head-frame comment,
  and the two depth levels above.
* Fixes, with diagnosis and affected file: none. No repository file was changed
  other than this note, `docs/log.md`, `README.md` and `DECISIONS.md`. No check,
  threshold, fixture, margin or matcher parameter was touched.
* Every unexpected FAIL line: none unexpected. The two expected negatives are
  quoted above. The two real gate failures are:
  `[fsg-eval] FAIL step: instance 2: median_relative_range_error=0.011358246628436037 fails max 0.01`
  `[fsg-eval] FAIL step: instance 2: p95_relative_range_error=0.04111456787779029 fails max 0.03`
* Gate status and whether further work is authorized: `[fsg-eval] FAIL`, and
  `evaluation.json:status` is `FAIL` with `full_profile_milestone_pass: false`.
  Stop after this report; no fusion, surface growing or policy work begun.

### Diagnosis of the step instance-2 miss

Measured, by comparing the stored disparities against a truth disparity recomputed
from `evaluation_only/mesh.npz` on the same rectified core grid (rectified focal
608.919 px, baseline 0.063000 m, so 11.28 px of disparity at 3.4 m against 23.98 px
at 1.6 m):

| case / instance | SGBM median err | SGBM std | refined median err | refined std |
| --- | ---: | ---: | ---: | ---: |
| fronto | -0.1185 px | 0.0303 | +0.0100 px | 0.1287 |
| tilted | +0.0747 px | 0.1528 | -0.0019 px | 0.1615 |
| step inst 1 | +0.0238 px | 0.0116 | +0.0127 px | 0.0939 |
| step inst 2 | -0.1579 px | 0.0370 | +0.0216 px | 0.2185 |

The refinement is doing its declared job and doing it correctly: it removes SGBM's
sub-pixel pixel-locking bias everywhere (|median| <= 0.022 px on all four), which
also confirms its Gauss-Newton sign. What limits the result is its scatter. At
3.4 m a 0.2185 px scatter on an 11.28 px disparity is a 1.9% one-sigma range error,
and the 1.136% median and 4.111% p95 follow arithmetically from it.

That scatter is stochastic render noise, not a geometry error. Re-rendering the
identical fixture at 1024 spp (16x the samples) and re-running only the estimator
halved the instance-2 refinement scatter, 0.2185 -> 0.1089 px, and carried the case
to median 0.618% and p95 1.846%, which would pass; instance 1 went 0.187% ->
0.104%. Over the same change SGBM's bias was unmoved, -0.1579 -> -0.1579 px, which
is what a deterministic interpolation bias should do and what a geometry,
orientation, indexing or calibration fault could not do. Texture is not the
constraint either: instance 2's local luminance std is a median 8.94 and a 5th
percentile 4.05 in the fixed uint8 conversion, far above the 0.5 rejection cutoff,
and its coverage is 99.751%. The residual ~0.10 px floor at 1024 spp is the
bilinear remap, the 5x5 window and the linear-gradient approximation, not noise.

So this is an instrument-resolution result, not an implementation bug. The small
profile puts only 11.28 px of disparity on the farthest surface at 64 spp; the two
terms that would relieve it both belong to the full profile, which doubles the
rectified focal length to about 1218 px, and so the disparity at 3.4 m to about
22.6 px, and quadruples the samples to 256. Neither is available by fixing code.

Because the miss is a genuine algorithm/resolution limit and not one of the
plainly identified bug classes the execution prompt allows to be fixed in place,
the matcher was not tuned, the thresholds and fixtures were not touched, and the
full run was not used to bury a small-profile failure. Per D-FSG1 this is the
point at which the next step is Luiz's and Chat's decision, not Code's. The open
question for that decision is whether `small` should be expected to meet a gate
written for the reported configuration, or whether the gate is a full-profile
statement that `small` is simply too coarse to satisfy at 3.4 m.

### Full-profile follow-up under D-FSG1a (2026-09-19) - also FAILS, on a different criterion

Run under `docs/fsg1-full-profile-followup.md`, which authorized exactly one
unchanged full/256-spp suite at seed 17 and superseded only the small-pass
prerequisite in sections 4-5 of the execution prompt. D-FSG1a was appended to
DECISIONS.md and a prospective entry written to `docs/log.md` BEFORE acquisition.
The small/64-spp FAIL above stands unedited, and `previews/fsg1/small-seed17` and
the 1024-spp diagnostic directory are preserved untouched.

Preflight: branch `main`, HEAD `6fd8a78b116144ba3ae0169af5235784eee9f60e`, clean
tree. `git diff 03029a2` over `fsg_geometry.py`, `fsg_scene.py`, `fsg_render.py`,
`fsg_stereo.py`, `fsg_evaluate.py`, `dev/check_fsg.py`, `dev/fake_blender_fsg.py`,
`rig.py`, `bl_common.py` and `requirements-fsg.txt` is EMPTY, so this is the same
estimator that produced the small result. Same environment as above. Logs and
reports under the new `previews/fsg1/full-followup-logs/`.

Software checks reconfirmed on the unchanged implementation:
`[fsg-check] SUMMARY passed=24 failed=0 seconds=1.847 blender_executed=False`,
and both deliberate negatives again exit 1 with byte-identical FAIL lines
(baseline 0.798831399 m, crop 2.37076271 m).

Acquisition `previews/fsg1/full-seed17`: every case `source: blender_cycles`,
`device: OPTIX`, Blender 5.2.1 LTS, `profile: full`, `spp: 256` equal to the
recorded `profile_default_spp`, `adaptive_sampling: false`, distinct L/R seeds
(170000/170001, 170100/170101, 170200/170201), `run.json` complete, 640x640 raw
per eye and a 256x256 accepted core, 209,715,200 primary samples per case and
629,145,600 for the suite - the prescription exactly. In-session checks against
limits of 0.002 px and 20 um: projection max 8.609e-05 / 1.577e-04 / 8.609e-05 px
and ray-cast max 3.755e-07 / 5.085e-07 / 7.305e-07 m for fronto / tilted / step,
242 rays each, all object IDs matching. Times: render L+R 0.9633 / 0.9025 / 0.9874 s,
oracle 0.1826 / 0.1756 / 0.2654 s, case 1.6220 / 1.5335 / 1.7133 s,
`total_wall_seconds` 4.8691, whole Blender process 5.403 s; stereo 0.1612 /
0.1244 / 0.1275 s. Batch-class as estimated, nowhere near the 5-minute stop rule.

Interior results (`previews/fsg1/full-seed17/<case>/evaluation/metrics.json`),
frozen gate 90% / 1% / 3% at the existing 8 px full-profile boundary margin:

| case / instance | coverage | median rel. range | p95 rel. range | ref px |
| --- | ---: | ---: | ---: | ---: |
| fronto | 94.786% | 0.285% | 1.159% | 65536 |
| tilted | 98.433% | 0.318% | 1.348% | 65536 |
| step (pooled) | **87.502%** | 0.268% | 1.950% | 60928 |
| step instance 1 (1.6 m) | **79.319%** | 0.137% | 0.595% | 36608 |
| step instance 2 (3.4 m) | 99.819% | 0.785% | 2.497% | 24320 |

`wrong_instance_accepted_count` is 0 in all three cases. Evaluator exit code 1,
`[fsg-eval] FAIL`, `evaluation.json:status` `FAIL`,
`full_profile_milestone_pass: false`. No `MILESTONE_PASS` was emitted.

Verbatim accuracy FAIL lines, both of which are coverage, not error:

    [fsg-eval] FAIL step: coverage=0.8750164128151261 fails min 0.9
    [fsg-eval] FAIL step: instance 1: coverage=0.7931872814685315 fails min 0.9

The predicted effect did occur. Step instance 2, the 3.4 m background that failed
at small with 1.136% median and 4.111% p95, now measures 0.785% and 2.497% and
passes every criterion. Every median and p95 in the suite is now inside the gate.
What fails is a criterion that passed before: the 1.6 m foreground's coverage,
which was 90.361% at small - clearing the 90% floor by 0.36 points - and is
79.319% here. The small and full failures are different instances failing
different criteria, so neither result supersedes the other.

#### Why coverage fell, measured from the stored arrays

Diagnosis is evaluation-side and uses only quantities the existing tools already
store (`left_gray_std`, `lr_error_px`, `raw_support_L`, `valid` in `result.npz`,
against the evaluator's own interior reference). No production code was written.

Of the 7,571 rejected interior pixels on step instance 1, **99.7% fail the fixed
textureless test** `left_gray_std < 0.5` in the fixed uint8 conversion; 0.3% fail
the 1-pixel left-right residual and none lack raw support. The same holds for
fronto (98.6% of rejections low-texture) and tilted (91.5%). Only step instance 2,
which loses just 44 pixels, is dominated by the left-right test.

The cause is that the cutoff is a fixed absolute number while the texture is
magnified. Doubling the linear resolution spreads the same painted texture over
twice as many pixels, so local contrast in the fixed 5x5 window roughly halves,
and the low tail crosses a threshold that does not move with it:

| interior reference | small: median std / frac <0.5 | full: median std / frac <0.5 |
| --- | ---: | ---: |
| fronto | 9.460 / 1.60% | 5.056 / 5.14% |
| tilted | 9.399 / 0.18% | 5.109 / 1.43% |
| step instance 1 | 8.325 / 9.64% | 4.508 / 20.63% |
| step instance 2 | 8.930 / 0.00% | 5.052 / 0.00% |

Step instance 1 was already the suite's weakest surface at small, with 9.64% of
its interior below the cutoff, and that share doubles to 20.63% at full. Its 5th
percentile local std is 0.000 at both profiles: this fixture's foreground really
does contain flat patches, and they are simply resolved as flat once magnified.
The contact sheet shows the same thing - the full rectified RGB is visibly
smoother than the small one, and the black holes in `validity.png` sit exactly on
the low-contrast patches, clustered in the left/foreground half of `step` while
the background half is nearly solid white.

This is a property of the fixture and the fixed cutoff together, not a geometry,
calibration or integration defect. The independent Blender checks passed by three
to four orders of magnitude, and the recovered head-frame geometry is tighter at
full than at small: step instance medians Z = -1.6002 and -3.4001 m against -1.6
and -3.4, fronto Z = -1.9995 m, and the tilted plane normal 25.288 degrees from
the gaze direction against a specified 25. Per D-FSG1a this is a miss to return
to Luiz and Chat with the evidence, not something to tune, so the cutoff, the
window, the fixture and every threshold are untouched.

#### Disparity bias and scatter, and a correction to the noise reading

On accepted interior pixels only - a different support at each profile, so these
compare estimators on what each accepted, not on a common pixel set:

| case / instance | d_truth | SGBM median | SGBM std | refined median | refined std |
| --- | ---: | ---: | ---: | ---: | ---: |
| full fronto | 38.362 px | -0.2994 | 0.0386 | +0.0089 | 0.2093 |
| full tilted | 39.499 px | +0.0102 | 0.1587 | +0.0011 | 0.2429 |
| full step inst 1 | 47.952 px | +0.0476 | 0.0067 | -0.0075 | 0.1399 |
| full step inst 2 | 22.566 px | +0.3717 | 0.0834 | +0.0012 | 0.2920 |

The refinement again removes SGBM's pixel-locking bias everywhere (|median|
<= 0.009 px at full). But the earlier note's reading needs qualifying, and the
follow-up handoff asked for exactly this care. Full's accuracy gain is NOT reduced
noise. Refined scatter in pixels actually grew at full on every surface - step
instance 2 goes 0.2185 -> 0.2920 px, fronto 0.1287 -> 0.2093 - for the same reason
coverage fell, since weaker per-pixel gradients make photometric alignment noisier.
The gain is purely geometric: the rectified focal length doubles to 1217.839 px,
so the 3.4 m background carries 22.566 px of disparity instead of 11.283, and
0.2920/22.566 = 1.29% beats 0.2185/11.283 = 1.94% despite the worse pixel scatter.

The two knobs therefore act on different failure modes, which the equal-cost pair
shows directly. The 1024-spp small diagnostic and this full suite have the same
629,145,600 nominal primary samples. On step, the diagnostic gives instance 1
coverage 90.284% and instance 2 0.618% / 1.846%; full gives 79.319% and
0.785% / 2.497%. More samples cut refinement scatter (0.2185 -> 0.1089 px) while
leaving the texture cutoff almost untouched (9.64% -> 9.72% below it); more
resolution buys disparity but halves per-pixel contrast, costing coverage. As the
handoff states, this equal-count comparison cannot isolate resolution from noise,
support size or acceptance differences, and no end-to-end efficiency claim follows
from it. It is a calibration observation about two fixtures at one seed.

#### Boundary, half-occlusion and what is NOT established

Boundary on step: 4,608 reference pixels, 51.259% coverage, median 0.605%, p95
3.266%, and 5.843% of accepted boundary pixels over 3% relative error. Boundary
has no FSG1 threshold and is reported, not gated. The interior gate says nothing
about boundary accuracy and must not be read as validating it.

`singly_visible` has 0 reference pixels in all three cases at full, as at small.
**Half-occlusion rejection is NOT EXERCISED by this suite.** A zero denominator is
not a pass. The foreground half-plane lies on the left of the frame, so the
background the left eye can see is never the part the foreground hides from the
right eye; the half-occluded strip belongs to the right eye and cannot appear in a
left-eye reference grid. Repairing that coverage gap needs a mirrored depth step
or an explicitly opposite-eye reference, which the follow-up assigns to Chat as a
separate additive step before surface fusion is authorized. The existing three-case
suite was deliberately not altered here to close it.

A pass on these fixtures would in any case have applied only to controlled opaque
textured planes at this configuration and seed. There was no pass, and FSG2 is not
authorized. Stopped here for Luiz and Chat.

## Source interfaces reviewed

Repository public main: `CLAUDE.md`, `tools/rig.py`, `tools/bl_common.py`,
`tools/fixation_pairs.py`, `tools/render_foveated.py`,
`tools/dev/fake_blender_pairs.py`, and `requirements.txt`.

API references used for the implementation:

* OpenCV calibration, stereo rectification, projection and disparity conventions:
  https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html
* Blender ImageFormatSettings (`media_type=IMAGE`, single-layer EXR):
  https://docs.blender.org/api/current/bpy.types.ImageFormatSettings.html
* Blender scene ray casts on evaluated geometry:
  https://docs.blender.org/api/current/bpy.types.Scene.html
* Blender camera perspective and sensor settings:
  https://docs.blender.org/api/current/bpy.types.Camera.html
