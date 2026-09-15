# Step B2 — ground-truth correspondence, the epipolar frame, the triangulation check, per-eye references

Written 2026-09-15 before the workstation run. Numbers are **predicted** (geometry) or
**assumed** until the log records a measurement. The tool ran end to end in the sandbox on
the B1 stub runs (`tools/dev/fake_blender_pairs.py`) and its negatives were checked; those are
plumbing results, listed in the log.

## What B2 is

B1 produced two D1 v2 sequences per run and the Position pass in every `fix.exr`. Everything a
matcher will be measured against follows from that with no rendering: for each sample of one
eye, the world point its ray hit, where that point is seen from the other eye, and whether the
other eye can see it at all. `tools/stereo_truth.py` writes that as a sidecar `truth.npz` next
to each `samples.npz` (D13: the record stays what the renderer emitted; derived labels are
sidecars) and judges it with checks that can fail.

### The epipolar frame (D13)

Both centres lie on the head's X axis, so every epipolar plane contains that axis and the
change of coordinates the README promised is one function, `rig.epipolar`: a head-frame
direction d is (θ, φ) with θ the angle from +X (the baseline) and φ = atan2(d_y, −d_z) the
plane's rotation about X (0 forward-horizontal, +90° up, 180° backward). Corresponding
directions share φ and differ in θ; the parallax θ_R − θ_L is positive for every finite point
and equals the vergence at the fixated point. The sine rule in the triangle C_L C_R P gives
`rig.triangulate`: |P − C_L| = ipd·sin θ_R / sin(θ_R − θ_L), and its derivative gives the depth
quantum, one sample spacing of parallax at distance D: D·s₀/tan γ ≈ D²s₀/ipd, which is
0.111 m at 2 m and 7 mm at 0.5 m at the small profile, half that at full. That quantum is the
tolerance of the depth check, not a constant.

Torsion closed (D14): directions are stored in the head frame and the warp is radially
symmetric about the gaze, so an eye's torsion changes which raster pixel sampled which
direction and nothing else. Listing's law does not enter unless D2 is overturned.

### The sidecar

`truth.npz` per fixation: `hit_world`, own (θ, φ), the other eye's (θ, φ) and unit direction
to the hit point, `parallax`, `other_raster` — the continuous (row, col) where the point falls
in the other eye's raster of the same pair, from the inverse warp `warp.raster_of_direction`
— and `other_visible` (1 visible, 0 occluded, −1 outside the other disc, 2 inconsistent).
Visibility compares the other eye's Depth at that pixel with the point's distance from that
eye, within 2% (assumed): occluded if the other eye sees something nearer, inconsistent if it
sees something farther, which happens at depth edges where the nearest pixel's ray passes the
edge, and which is reported so the label's fuzz is a number. `truth_columns.json` beside it.

## Checks (`tools/stereo_truth.py`)

- **(i) epipolar** — φ of the own analytic direction and φ of the hit seen from the other
  eye agree, as a great-circle distance across epipolar lines (Δφ·sin θ), within 1 s₀ at
  p99.9. Inherits check (a)'s residual (0.017 s₀ measured in B1); a wrong axis fails it.
  Samples within 5° of the baseline axis are excluded (φ is ill-conditioned there) and
  counted; the ladders at azimuth 83° contribute most of them.
- **(j) inverse warp** — each eye's own hit points, sent back through the inverse warp with
  its own gaze, land on their own raster pixel for ≥ 99% of samples (rim pixels may flip).
- **(k) triangulation identity** — `triangulate(θ, θ_other)` reproduces the Position pass's
  ray distance for every hit; the implied angular error |ΔD|/D·tan γ is within 1 s₀ at p99.9.
  Fails on a wrong ipd or swapped centres (shown on the stub).
- **(h) depth at the fixated cards** — the L centre pixels' hit point, triangulated from L's
  gaze θ and the point's θ seen from R, gives the cyclopean distance the Position pass reports
  for it within one depth quantum, on any run; on a verged run it must also match the card's
  `distance_m` — the check the Phase A summary named as Phase B's first. The **control** is a
  second estimator, *naive*, which assumes zero parallax at the centre (θ_R from R's own gaze):
  it must pass against the target on the verged run and fail on the `--vergence off` run, where
  parallel rays triangulate to infinity. Cards judged; wires reported (their centre hit is one
  radius short of the axis at full, B1).
- **Reported** — parallax at the centre against the vergence; visibility fractions per eye
  and per run; θ range; samples excluded near the axis.

## Per-eye references

Phase A's references are from the cyclopean point; a per-eye sequence read against them is off
by parallax (0.9° at 2 m). `preview360.py --eye-offset X Y Z` renders from an offset of the
EYE centre in the head frame and records that centre as `eye.position_m` in its `meta.json`
(the head's own record moves to `head`), so `check_sequence.py` (b) and `integrate_sphere.py`
run on `L/` or `R/` against the matching reference unchanged. Small references are two batch
renders (~63 s each measured in A2 for the cyclopean one; the same assumed here). Full ones
are two overnight renders (~32 min each by A2) and are not scheduled by this step: they are
needed only for the full-profile D9 error per eye, which B3's objective does not use.

## Commands (small profile)

```bash
.venv/bin/python tools/warp.py --self-test && .venv/bin/python tools/rig.py --self-test
.venv/bin/python tools/stereo_truth.py previews/pairs/calib_room
.venv/bin/python tools/stereo_truth.py previews/pairs/calib_room_control
.venv/bin/python tools/stereo_truth.py previews/pairs/calib_room_full
.venv/bin/python tools/stereo_truth.py previews/pairs/calib_room_control_full
blender -b scenes/calib_room/calib_room.blend -P tools/preview360.py -- --out previews/reference_small_L/calib_room \
    --profile small --eye-offset -0.0315 0 0
blender -b scenes/calib_room/calib_room.blend -P tools/preview360.py -- --out previews/reference_small_R/calib_room \
    --profile small --eye-offset 0.0315 0 0
.venv/bin/python tools/inspect_preview.py previews/reference_small_L/calib_room
.venv/bin/python tools/check_sequence.py previews/pairs/calib_room/L --reference previews/reference_small_L/calib_room --plain kind=wire
.venv/bin/python tools/check_sequence.py previews/pairs/calib_room/R --reference previews/reference_small_R/calib_room --plain kind=wire
```

The last two are the B1 per-eye radiometric validation that could not run before: (a) against
the eye's own reference, (b) on the wires, (c) and (d). Both eyes should look like Phase A's
small-profile `check_sequence` results (40/50 (b) unjudged as registration-limited, wires 8/8).

## Results

First workstation run 2026-09-15 (Blender 5.2.1 LTS, RTX 4090 through OptiX for the two
reference renders; everything else host-side in `.venv`). Every number is **measured** and
comes from `previews/pairs/<run>/truth.json` (`summary`) unless another file is named. Cost
class as measured: `stereo_truth.py` is interactive (0.6 s small, 1.9 s full per run, 50 pairs);
each per-eye reference is batch (60.6 s and 61.1 s render); the seed-pair re-render of the
verged small run is interactive (4.5 s including Blender start); `check_sequence.py` is 4 s per eye.

### Truth checks, four B1 runs

| | small verged | small control | full verged | full control |
|---|---|---|---|---|
| (i) epipolar, p99.9 (max) | 0.015 (0.016) s₀ | 0.015 (0.017) s₀ | 0.015 (0.017) s₀ | 0.015 (0.017) s₀ |
| (k) triangulation identity, p99.9 (max) | 0.015 (0.016) s₀ | 0.015 (0.016) s₀ | 0.015 (0.017) s₀ | 0.015 (0.017) s₀ |
| (j) inverse-warp round trip | 100.000% | 100.000% | 100.000% | 100.000% |
| samples within 5° of the axis, excluded | 7,214 of 1,249,200 | 7,204 | 29,057 of 5,026,900 | 29,006 |
| non-positive parallax, judged off-axis | 0 | 0 | 0 | 0 |
| non-positive parallax, near-axis (reported) | 0 | 0 | 0 | 1 |
| (h) truth vs the hit, max | 0.0009 m, 0.005 quanta | 0.0009 m, 0.005 q | 0.0005 m, 0.006 q | 0.0005 m, 0.005 q |
| (h) truth vs the target, max | 0.0009 m, 0.005 quanta | 3.175 m (wall; not required) | 0.0005 m, 0.006 q | 3.175 m |
| (h) naive vs the target, max | 0.0000 m | inf on 42/42 cards | 0.0000 m | inf on 42/42 |
| target quantum range | 0.007 – 0.188 m | same | 0.003 – 0.093 m | same |
| centre parallax − vergence, max | 8e-5° | – | 5e-5° | – |
| visible / occluded / outside / inconsistent | 93.0 / 4.7 / 0.6 / 1.70% | 91.1 / 5.6 / 0.5 / 2.85% | 94.9 / 3.9 / 0.5 / 0.72% | 94.7 / 4.0 / 0.4 / 0.89% |
| fails | none | none | none | none |

(i) and (k) sit at check (a)'s residual (0.016–0.017 s₀ in B1), as predicted: the truth inherits
the direction error of the render and nothing else. The naive estimator reproduces the target
exactly on the verged runs because both gazes point at P by construction, and gives infinity
on every card of the controls; the truth estimator gives the Position pass's distance on all
four (on the controls the L centre ray is on the wall at 3–5 m, so "vs the target" is 3.2 m
there, as it must be). The seed-pair re-render `calib_room_sp` gives the same truth summary as
`calib_room` to every printed digit.

**The one thing that failed, and what was changed.** The first pass failed on both full runs
with 2 and 1 samples of non-positive parallax (−0.0009° and −0.013°). All three are within
0.02° of the baseline axis (gaze near azimuth −75°, the raster reaching −90°, the hit on the left
wall at x = −3 m), where the geometric parallax ipd·sin θ/D is 2e-5 to 5e-4 degrees. Two
causes, both measured on those samples: (1) `rig.epipolar` took θ = arccos(dₓ) of the float32
stored direction, whose x is quantised at −0.99999994 next to −1, so θ was off by 0.02° there
(arccos is ill-conditioned at ±1); changed to θ = atan2(hypot(d_y, d_z), dₓ), the same function
computed from the small components, which the self-tests and both interpreters pass unchanged
and which removes two of the three. (2) The third (full control, L f048 raster (126, 51),
0.0008° off the axis) has a geometric parallax of 2.0e-5° against a direction residual of
1.6e-4° between its analytic ray and its Position-pass hit — check (a)'s residual — so its sign
is not measurable at all. `stereo_truth.py` now judges the sign count on the same off-axis mask
(i) and (k) already use and reports the near-axis count beside it; that is a change inside the
checker, made after the diagnosis, and it is the only such change. B1's `check_pairs` re-run
after the `rig.py` change is unchanged to every digit.

### Per-eye references (pinned, `scenes/manifest.json` → `reference_small_L`, `_R`)

| | L | R |
|---|---|---|
| eye.position_m / head.position_m (meta.json) | (−0.0315, 0, 1.6) / (0, 0, 1.6) | (0.0315, 0, 1.6) / (0, 0, 1.6) |
| render seconds (incl. EXR write) | 60.55 | 61.08 |
| pano.exr md5 | fdcbe57f7f0d575b532984dc1a8183e4 | 5e268d470f70aa34f57625465daca306 |
| backface.exr md5 | 4286c3ad5ecbde34d43edaa75c905885 | 2a33408bc9efc9befefb73c179a145a5 |
| inspect: holes / backface / nadir / depth min | 0 / 0 / 1.6002 m / 0.526 m | 0 / 0 / 1.6002 m / 0.474 m |

3600×1800, 1024 spp, seed 0, box filter; backed up at `/home/lvelho/data/reference/reference_small_{L,R}/calib_room`,
md5 verified. Centre and yaw checked directly: the centroid of each card's pixels in the Depth
pass lands within 0.5 px (0.05°) of where the offset eye centre predicts it, including the ±9 px
parallax shift of the e = 0 card (1808.8 / 1790.6 against 1800.3 cyclopean; script in the log
entry's session, not kept). Full-profile per-eye references were not rendered (overnight, not scheduled).

### Per-eye radiometric validation (`check_sequence.py`, small, wires plain)

The B1 verged run has no seed pair, so against the per-eye references it gives: origin check
passes, (a) 0.018 px median p99.9 (max 0.064, both eyes; A4 level), (d) cap +0.59%, reader diff
0, and (b) unjudged ("no seed pair, (b) has no bound", exit 1 by design). To judge (b) the verged
small run was re-rendered with `--seed-pair` into `previews/pairs/calib_room_sp` (4.5 s; its
check_pairs and truth summaries are identical to `calib_room`'s), and that is what the table reports,
beside Phase A's cyclopean small run on the same scene:

| | Phase A cyclopean | B2 L | B2 R |
|---|---|---|---|
| (a) warp p99.9, median / max | 0.018 / 0.064 px | 0.018 / 0.064 px | 0.018 / 0.065 px |
| (b) bound median (noise median) | 0.043 (0.017) | 0.046 (0.017) | 0.046 (0.017) |
| (b) foveal score median | 0.038 | 0.040 | 0.037 |
| (b) pass, all 50 | 40 | 36 | 35 |
| registration-limited (42 cards) pass | 32 | 30 | 30 |
| plain (8 wires) pass | 8 | 6 | 5 |
| (c) control fails, as required | 50 / 50 | 50 / 50 | 50 / 50 |
| (d) cap | +0.59% | +0.59% | +0.59% |

Failures listed by the checker, all wires: L 0.75 mm 0.0150 vs bound 0.0136, 6 mm 0.0240 vs
0.0233; R 0.5 mm 0.0186 vs 0.0172, 1 mm 0.0302 vs 0.0250, 1.5 mm 0.0250 vs 0.0175. Phase A's
8/8 included passes with 1.5% and 3% margin (0.75 mm 0.0139 vs 0.0141, 6 mm 0.0188 vs 0.0194),
and its full-profile note measured the wire score as non-radiometric, moving 0.003–0.030 under a
1 px shift. The per-eye scores (0.011–0.030) lie in that range, the noise and bounds are the
same as Phase A's, and the references' centres are verified above, so these are the wires'
sub-pixel lattice phase seen from a different centre, not a rig or reference error; the
checker's verdict stands as written (5 of 16 wire fixations fail) and no tolerance was moved.
The ring cards behave as in Phase A (30/42 against 32/42 registration-limited).

## What B2 leaves open

- The truth is per pair. A correspondence across pairs (a point seen in fixation 3 of L and
  fixation 7 of R) is the same computation on the integrated spherical maps; not needed until a
  matcher works across fixations.
- Full-profile per-eye references (overnight, two) when a full D9 per eye is wanted.
- B3: the objective. A reference matcher on the two s_eval maps in (θ, φ) as an instrument,
  with the matcher-free bound — the Fisher information of disparity from gradient² over noise²
  along the epipolar direction — beside it; D15 to say the matcher is not the research one.
