# Step A6 — the E2 and e_max sweep

Calibration room, small profile, 50 targets in target order, seed pairs on, 64 spp, D9 metric
at s_eval 0.2 deg, uniform baselines at equal rays. Five settings, each one
`fixation_sequence.py` run plus one `integrate_sphere.py` curve (identity check skipped: same
grid as A5). Everything measured on the workstation on 2026-09-13 unless marked assumed.
The raster follows from the warp, N = 2 (E2/s0) ln(1 + e_max/E2), so samples per fixation
and rays differ across settings.

```bash
blender -b scenes/calib_room/calib_room.blend -P tools/fixation_sequence.py -- --out previews/sweep/e2_1/sequence --profile small \
    --targets scenes/calib_room/calib_room.targets.json --e2 1 --emax 45        # and --e2 4; --emax 30; --emax 60
.venv/bin/python tools/check_sequence.py previews/sweep/e2_1/sequence --reference previews/reference_small/calib_room --plain kind=wire
.venv/bin/python tools/integrate_sphere.py previews/sweep/e2_1/sequence --reference previews/reference_small/calib_room \
    --out previews/sweep/e2_1/integrated --uniform previews/uniform/calib_room --bound <median (b) bound> \
    --calibration previews/uniform/calib_room/w3600_seed0 --calibration-b previews/uniform/calib_room/w3600_seed1 \
    --shifted previews/reference_small_shift/calib_room --shift-noise 0.0176 --skip-identity
```

## Per setting, K = 10 and K = 50

F = foveated, U = uniform at the same rays. Seconds are the seed-0 render calls.

| setting | raster | samples | K | rays | F s | fixated F / U | all tgt F / U | sphere F (uncov) / U |
|---|---|---|---|---|---|---|---|---|
| E2 1, e_max 45 | 77 | 4,669 | 10 | 2.99 M | 0.10 | 0.207 / 0.314 | 0.283 / 0.316 | 0.547 (0.82) / 0.261 |
| | | | 50 | 14.9 M | 0.50 | 0.227 / 0.300 | 0.227 / 0.300 | 0.203 (0.42) / 0.193 |
| E2 2, e_max 45 | 126 | 12,492 | 10 | 7.99 M | 0.16 | 0.143 / 0.282 | 0.261 / 0.300 | 0.503 (0.82) / 0.227 |
| | | | 50 | 40.0 M | 0.78 | 0.161 / 0.294 | 0.161 / 0.294 | 0.140 (0.42) / 0.151 |
| E2 4, e_max 45 | 200 | 31,428 | 10 | 20.1 M | 0.29 | 0.120 / 0.267 | 0.248 / 0.297 | 0.385 (0.82) / 0.179 |
| | | | 50 | 100.6 M | 1.45 | 0.140 / 0.270 | 0.140 / 0.270 | 0.101 (0.41) / 0.118 |
| E2 2, e_max 30 | 111 | 9,689 | 10 | 6.20 M | 0.14 | 0.159 / 0.276 | 0.257 / 0.302 | 0.440 (0.91) / 0.234 |
| | | | 50 | 31.0 M | 0.68 | 0.174 / 0.289 | 0.174 / 0.289 | 0.146 (0.58) / 0.161 |
| E2 2, e_max 60 | 137 | 14,745 | 10 | 9.44 M | 0.17 | 0.163 / 0.283 | 0.272 / 0.302 | 0.415 (0.71) / 0.214 |
| | | | 50 | 47.2 M | 0.89 | 0.177 / 0.299 | 0.177 / 0.299 | 0.140 (0.27) / 0.145 |

Per-fixation cost: 10.1, 15.5, 28.7, 13.7, 17.2 ms (floor 7.3 to 13.2 ms, 10.2 to 10.9 ns
per sample); warm-up 0.30 to 0.38 s. Checks per setting: (a) p99.9 0.009 to 0.034 px; the
calibration ratio 1.029 (same render); the control 2.6x (E2 1, fails the 3x threshold), 3.4x,
3.4x, 3.7x, 4.3x; (d) cap +1.03% at raster 77 (E2 1, fails the 1% tolerance: the rim-ring
excess of straddling pixel squares, measured in the A4 note, grows as the raster shrinks),
+0.38%, +0.59%, +0.09%, +0.10%; wires (b) 1, 8, 7, 2, 1 of 8, which moves with raster size
alone (the sub-pixel lattice effect established at the full profile). The D8 validation
fails on every setting, as on the baseline.

## At equal rays

The largest budget every setting reaches is 14.94 M rays (E2 1 at K = 50). Every other
setting is interpolated log-log along its own K axis between the bracketing measured points
(K 10 to 20 for E2 2 e_max 45 and e_max 60, 5 to 10 for E2 4, 20 to 50 for e_max 30);
the K column says where. Sphere errors are over each setting's covered part, whose fraction
differs, so they are not like-for-like; the uncovered fraction stands beside them.

| setting | K at 14.9 M | fixated | all targets | sphere (uncov) |
|---|---|---|---|---|
| E2 1, e_max 45 | 50.0 | 0.227 | 0.227 | 0.203 (0.42) |
| E2 2, e_max 45 | 19.0 | 0.155 | 0.242 | 0.435 (0.78) |
| E2 4, e_max 45 | 7.9 | **0.103** | 0.251 | 0.395 (0.83) |
| E2 2, e_max 30 | 26.1 | 0.168 | 0.224 | 0.371 (0.82) |
| E2 2, e_max 60 | 16.6 | 0.168 | 0.256 | 0.378 (0.68) |

Lowest fixated-target error at equal rays: **E2 4** (0.103 against 0.155 at E2 2 and 0.227 at
E2 1) and **e_max 45** (0.155 against 0.168 at 30 and 60). Lowest covered-sphere error: **E2 1**
(0.203, but on 58% covered against 17 to 22% for the others, and with two tool checks
failing) and **e_max 30** (0.371 against 0.435 and 0.378).

The two criteria disagree, and on the fixated-target criterion the answer is not the
profiles' E2 = 2. Per the instruction the profiles are not changed; the sweep stops here and
the choice is recorded as pending in D11. What the sweep does say without ambiguity: a
larger E2 buys foveal accuracy per ray (E2 4 puts 2.5x the samples of E2 2 into a fixation
and reaches the fixated targets at 0.103 with eight fixations), a smaller E2 buys coverage
(E2 1 covers 58% of the sphere for the rays E2 2 needs to cover 22%), and e_max is a
second-order knob at 45 against 30 and 60.

## Assumed

- Log-log interpolation along K between measured points, at most one bracket apart.
- E2 1's numbers carry a failed cap check (+1.03%) and a control at 2.6x.

## Untested

- Any E2 between the three values, e_max outside 30 to 60, and the full profile.
- Gaze orders other than target order; a policy that trades E2 against K is Phase C.
