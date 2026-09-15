# Step B1 — the second eye, verged fixation pairs, the foveae-on-target check

Written 2026-09-14 before the first workstation run; every number below is **predicted**
(geometry, from `tools/rig.py`) or **assumed** until the log records a measurement. The
sandbox that wrote this had no `bpy`; the writer was exercised through a stub Blender (`tools/dev/fake_blender_pairs.py`) with an
analytic ray caster over the calibration room's cards and walls, and the checker judged its
output. That tests the plumbing and the checks, not the OSL camera or Blender's matrix
composition — check (a) does that on the real run.

## The rig (D12)

`EYE` is unchanged: the head frame and the cyclopean point. The two eye centres sit on its
local X at ±ipd/2, 63 mm by default (`--ipd`), so the calib room's eyes are at
(∓0.0315, 0, 1.6) m. Each eye is the Phase A foveated camera rotated about its own centre:
`render_foveated.gaze_matrix` gained an `offset_local` and nothing else changed. D2 reads as
"fixed rig, eyes rotate"; D3 still holds (no head translation).

A pair fixates one world point P. With `--vergence on` (default) each eye's gaze is P − Cᵢ,
composed yaw-then-pitch in the head frame like every Phase A gaze; no torsion (assumed for
B1 — Listing's law is a later refinement that changes `rig.py`, not the record). With
`--vergence off` both eyes take the cyclopean gaze: parallel lines of sight, the control.

Fixation points for the calib room: cards at `eye + dir_world · distance`
(`make_calib_room.place_card`), wires at eye height on their azimuth. Predicted vergence
(63 mm): 1.80° for the ring cards at 2 m (36 full-profile samples, 18 small), 2.41° at the
wires' 1.5 m, 7.2° at the 0.5 m ladder — except that the ladders sit at azimuth 55–83°,
almost on the interocular axis, where vergence collapses: 0.17° at the 2.6 m ladder. They are
the geometric worst case for anything binocular in this scene.

## The record (D1 v2)

`--out/L/` and `--out/R/` are each a Phase A sequence (`f<NNN>/{fix.exr, samples.npz,
meta.json, columns.json}`, `sequence.json`) so per-eye tools run unchanged. `samples.npz`
adds `eye_id` (0 = L, 1 = R) and `pair_id`; `origin` is this eye's centre; `direction` stays in
the head frame for both eyes, so the two records share one frame and differ only in origin.
`meta.json` carries `schema: "D1v2"`, the eye centre and offset, the ipd, the fixation point,
the full camera pose (position, forward, right, up) and a timestamp. `--out/pairs.json` holds
the rig (head origin and rotation, ipd, both centres), and per pair the target, P, both gazes,
the vergence, the predicted central-ray distances and misses, render seconds, and the centre
pixels' Position and Depth as read in-session by `exr_lite` (reported; the host checker
re-measures with OpenEXR and judges).

Cost: a pair is two fixations, nothing more (predicted from A4: ~30 ms small, ~280 ms full);
50 pairs is interactive at small, batch at full. `--seed-pair` exists but is off: B1's checks
are geometric.

## Checks (`tools/check_pairs.py`, host side, no reference panorama)

- **reader** — `samples.npz` equals `fix.exr` at the stored raster indices (exact); `origin`
  equals the eye's centre in `pairs.json`; `eye_id`, `pair_id` columns.
- **(a) warp** — stored head-frame direction vs the Position pass seen from *this eye's*
  centre, p99.9 within 1 s₀. Phase A measured 0.018 reference px (0.0009°) with the eye at
  the head origin; with the eye 31.5 mm off it, a wrong offset would show as parallax:
  0.9° = 9 s₀ at 2 m (small).
- **(d) cap** — footprints sum to the cap within 1%.
- **(e) foveae on target** — the mean Position of the raster's centre pixels (the 2×2 block
  for even n) is within one sample spacing at the target's distance of P: tol = Dᵢ·s₀, i.e.
  3.5 mm at 2 m at the small profile, 1.7 mm at full, 0.9 mm at the 0.5 m ladder; the centre
  Depth equals Dᵢ to the same tolerance. Judged on the 42 cards; the 8 wires are thinner than
  a sample at the centre and are reported only.
- **(f) control** — on a `--vergence off` run, (e) must fail on every card by the amount
  `rig.py` predicts: (ipd/2)·√(1 − (right·ĝ)²), 31.5 mm on the midline, 18.1 mm at the 0.5 m
  ladder; where the parallel ray leaves the card (the 1° card at e = 0 is 35 mm wide) the miss
  is at least that. Where the prediction is itself below one spacing (the 2.6 m ladder at
  azimuth 83°: 3.8 mm against 4.6 mm at small) the control is not resolvable at that s₀ and is
  reported, not judged.
- **Reported** — measured vergence (angle at P between the two centre rays) against the
  predicted; wires' centre depth against 1.5 m.

`--sheet` writes `sheet.png`: the central ±2° of L | R for the first pairs, ×8, with a cross
at the raster centre. Verged, the target is on the cross in both eyes; control, it is off by
the predicted amount (0.9° at 2 m).

`rig.py --self-test` and `warp.py --self-test` are the pure-numpy identities (gaze composition
round trip, ±yaw/pitch signs, verged rays through P, control misses, raster orientation, cap,
s₀ round trip); each was shown to fail on a wrong sign or scale before it was kept.

## Commands (small profile; add `--profile full` for the reported numbers)

```bash
python tools/warp.py --self-test && python tools/rig.py --self-test
blender -b scenes/calib_room/calib_room.blend -P tools/fixation_pairs.py -- \
    --out previews/pairs/calib_room --profile small --targets scenes/calib_room/calib_room.targets.json
.venv/bin/python tools/check_pairs.py previews/pairs/calib_room --sheet
blender -b scenes/calib_room/calib_room.blend -P tools/fixation_pairs.py -- \
    --out previews/pairs/calib_room_control --profile small --targets scenes/calib_room/calib_room.targets.json --vergence off
.venv/bin/python tools/check_pairs.py previews/pairs/calib_room_control --sheet
```

## Results

First workstation run 2026-09-15 (Blender 5.2.1 LTS, RTX 4090 through OptiX, 50 pairs per
run, 42 cards judged, 8 wires reported). All numbers below are **measured**, from
`previews/pairs/<run>/check.json` (`summary` block) unless a file is named; the source of
each is `pairs.json` for timings. Every check passed on both profiles: `fails: []` in all
four check files.

| | small (s₀ 0.100°, 64 spp) | full (s₀ 0.050°, 256 spp) |
|---|---|---|
| samples per fixation | 12,492 | 50,269 |
| reader (npz vs exr, max abs diff) | 0 | 0 |
| (a) warp, worst p99.9 over 100 fixations | 0.016 s₀ | 0.017 s₀ |
| (d) cap ratio, all fixations | 1.0059 | 0.9998 |
| (e) verged miss on cards, median / max | 0.0025 / 0.0041 mm | 0.0012 / 0.0024 mm |
| (e) in spacings, max | 0.0010 | 0.0013 |
| (e) tolerance range (Dᵢ·s₀) | 0.83 – 4.60 mm | 0.41 – 2.29 mm |
| control (f): predicted miss range | 3.84 – 31.5 mm | 3.84 – 31.5 mm |
| control: judged fixations on-card / off-card | 72 / 12 | 72 / 12 |
| control: on-card miss median (range) | 30.98 mm (3.84 – 31.50) | 30.98 mm (3.84 – 31.50) |
| control: \|measured − predicted\| max, on-card | 0.0026 mm | 0.0014 mm |
| control: off-card miss | 3000 – 3175 mm (the wall) | same |
| control: unresolvable (pred. < 1 spacing) | p041 ladder_2.6m, L and R | none |
| vergence, \|measured − predicted\| max (verged run) | 2.1e-5° | 1.7e-5° |
| seconds per pair, median | 0.029 s | 0.271 s |
| seconds per fixation, median | 0.0147 s | 0.136 s |
| sequence wall (50 pairs) | 2.3 s (verged), 2.2 s (control) | 14.9 s, 14.8 s |
| whole command incl. Blender start | 2.9 s | 15.4 s |

Cost class as measured: small is interactive (2.9 s per sequence), full is batch by the
README's classes but only just (15 s); both match the A4-based prediction (30 ms / 280 ms
per pair predicted, 29 / 271 measured).

The verged misses are a few µm at 2 m, three orders below the tolerance, so they are the
render's own precision rather than a geometric residual. Their origin is assumed, not
separated: the OSL camera reads the jittered per-sample raster position under a box filter of
width 1, so the mean of the symmetric 2×2 centre block converges to P up to the stratified
jitter's residual and float32 Position. Check (a) at 0.016 s₀ with the eye 31.5 mm
off the head origin says Blender composes the offset as `rig.camera_pose` does; a wrong
offset would have shown as 9 s₀ at small.

**Control, off-card.** Twelve of the 84 judged control fixations (six pairs, both eyes) leave
the card entirely: the 1° card at e = 0 (35 mm wide, half-width 17.5 mm), the four 1.6° cards
at e = 2.5° (57 mm, half-width 28 mm), both against a 31.5 mm predicted miss, and the 3° card
of the 0.5 m ladder (26 mm, half-width 13 mm against 18.1 mm). Sizes from
`make_calib_room.place_card`, geometry not measured here. Their centre ray
lands on the wall 3.0–3.2 m away, so the miss is 3000–3175 mm, at least the prediction as the
check requires; the 72 on-card fixations match the prediction to 3 µm. The small-profile
control cannot resolve the 2.6 m ladder (3.84 mm predicted against 4.60 mm tolerance) and
`check_pairs.py` lists it as such; at full the same pair is 1.7 spacings and is judged.

**Wires (reported only).** Fixation points sit on the wire axis, so the verged centre ray
stops at the cylinder surface one radius short: at full the miss equals the radius for all
eight (0.49, 0.74, 0.99, 1.50, 1.98, 2.95, 3.92, 5.90 mm for radii 0.5–6 mm; centre depth
1.4628 m against 1.4687 m predicted for the 6 mm wire, i.e. 5.9 mm short). At small the even
raster's four centre pixels sit ±0.5 spacing (±1.3 mm at 1.5 m) off the axis, so the three
wires thinner than that (0.5, 0.75, 1 mm) are missed altogether and the centre ray reaches the
back wall (miss 1.86–2.18 m, depth 3.3–3.7 m); the 1.5–6 mm wires give 0.6–5.8 mm, a little
under one radius because the block averages oblique hits. In the control all wires but the
6 mm one are missed at both profiles (miss 1.55–2.18 m). None of this is a rig error; a line
target needs its own check (open item below).

Sheets: `previews/pairs/{calib_room,calib_room_control,calib_room_full,calib_room_control_full}/sheet.png`
(regenerable; not pinned). Verged: the cross on the card centre in both eyes. Control: the
card displaced to the right in L and to the left in R by ~0.9° at 2 m, as predicted.

Nothing was changed in code to make a check pass; no thresholds moved.

## What B1 leaves open

- **Per-eye references.** Phase A's reference is from the cyclopean point. The radiometric
  checks ((b), D8, D9) on a per-eye sequence need a reference from that eye's centre: small
  ones are ~1 min each (batch), full ones two overnight renders. `check_sequence.py` now says
  so instead of failing (a) by parallax. Decide at B2, when disparity needs radiometry.
- **Torsion.** None in B1. The earlier binocular work found a Listing coefficient of 1/2
  optimal for plane-of-regard alignment; whether B2's rectification needs it is B2's question.
- **Wires** as binocular targets: sub-sample at the centre; a line target needs its own check.
