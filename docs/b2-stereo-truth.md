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

Not yet run. To be filled from the four `truth.json` summaries and the two `check.json`: (i),
(j), (k) worst values in s₀; (h) truth error vs the hit and vs the target, max, in m and in
quanta; the naive estimator on the verged run (error) and on the control (inf); visibility
fractions; the per-eye reference render seconds and md5s (pinned in `scenes/manifest.json` as
`reference_small_L` / `_R`); per-eye `check_sequence` outcomes.

## What B2 leaves open

- The truth is per pair. A correspondence across pairs (a point seen in fixation 3 of L and
  fixation 7 of R) is the same computation on the integrated spherical maps; not needed until a
  matcher works across fixations.
- Full-profile per-eye references (overnight, two) when a full D9 per eye is wanted.
- B3: the objective. A reference matcher on the two s_eval maps in (θ, φ) as an instrument,
  with the matcher-free bound — the Fisher information of disparity from gradient² over noise²
  along the epipolar direction — beside it; D15 to say the matcher is not the research one.
