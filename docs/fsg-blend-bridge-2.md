# FSG Blend Bridge-2 — one structured Classroom fixation

## Question

Does the **unchanged native FSG tangent-plane stereo instrument** remain well behaved when the local Classroom core contains real scene structure rather than the near-ideal single textured floor plane of Bridge-1R?

Bridge-2 changes **only the gaze condition**. It does not introduce a controller, fusion, FSG6f, matcher tuning, truth gating, or a second measurement.

## Experimental control

Bridge-1R is the control condition:

- same scene: `scenes/classroom/classroom_eye.blend`;
- same `EYE`, IPD, vergence, `small` profile, 64 spp, seed 2111;
- same baseline-projected tangent frame;
- same `tools/fsg_stereo.py` without edits;
- one fixation;
- Blender truth used only after stereo for evaluation.

Bridge-2 differs only in selecting a core with multiple substantial instance regions and a real depth discontinuity.

## Gaze selection is sealed before stereo

Candidate gazes are a fixed 30-view grid:

- yaw: `[-180,-150,-120,-60,-30,0,30,60,120,150]` degrees;
- pitch: `[-30,0,30]` degrees.

Each candidate is acquired with the existing Bridge tangent renderer. **No SGBM is run on any candidate before selection.** The selector refuses any candidate directory that already contains `stereo/`.

Selection sees only:

- raw tangent RGB;
- raw Blender first-hit instance IDs;
- evaluator-only Blender first-hit range;
- calibration metadata.

Candidate acquisition may use 16 spp because these renders are only an oracle planning scaffold. The final selected fixation is reacquired at the control setting of 64 spp before stereo.

### Eligibility

The declared FSG core must have:

- truth hit fraction >= 0.95;
- a second instance occupying >= 0.10 of core pixels;
- reference range `P90-P10 >= 0.40 m`;
- median reference range jump across an instance boundary >= 0.20 m;
- fixed-transfer grayscale standard deviation >= 8 u8 levels.

These are **selection heuristics only**, not stereo-quality thresholds. If no candidate passes, Bridge-2 stops; the criteria are not relaxed after seeing data.

Among eligible candidates choose, in order: largest second-instance fraction, largest median boundary depth jump, largest texture standard deviation, largest robust depth span, smallest absolute pitch, then ascending wrapped yaw.

## Measurement

After `selection.json` is sealed, reacquire exactly the selected gaze at 64 spp and run the existing `tools/fsg_stereo.py` once. Then run the existing bridge evaluator. Do not retune or repair the matcher after seeing the result.

Report overall accuracy and, importantly, split diagnostics for:

- pixels whose 3x3 neighborhood is single-instance interior;
- pixels within a small image-space band of an instance boundary;
- each substantial reference instance in the core;
- error as a function of reference depth.

The split analysis is evaluator-only and must not alter validity or geometry.

## Stop

One final fixation only. No second gaze, no fusion, no controller, no FSG6f, and no Classroom demo continuation.

## Results

**BRIDGE2_COMPLETE 2026-09-24 on branch `fsg-blend-bridge-2`.** The unchanged
instrument ran end to end on a structured Classroom fixation and produced a
non-trivial metric patch. **No tool was modified during the experiment** —
`tools/` is byte-identical to the Bridge-2 package commit `fee9775`, and
`tools/fsg_geometry.py` / `tools/fsg_stereo.py` are byte-identical to
`7d53b5a`.

**Short answer to the scientific question: partially.** On the dominant near
surface the instrument stays control-grade. On the far surface behind it,
roughly half the accepted points are captured at the near surface's disparity —
classical foreground fattening — and the error tail explodes by a factor of 20.

### Preflight

Clean tree, branch `fsg-blend-bridge-2`, ancestor `7d53b5a`, package commit
`fee9775`, purely additive. `git diff 7d53b5a -- tools/fsg_geometry.py
tools/fsg_stereo.py` is empty. All five checks green:

```text
[fsg-geometry] self-test PASS
[fsg-tangent-frame] SUMMARY checked=92 failed=0
[fsg-blend-bridge-check] SUMMARY passed=13 failed=0
[fsg-bridge2-select] self-test PASS
[fsg-bridge2-check] SUMMARY passed=8 failed=0
```

### Phase A — pre-stereo selection over the fixed 30-view grid

All 30 candidates acquired at 16 spp, 0 failures, **no `stereo/` in any
candidate directory**. Selection ran once on the completed grid.

```text
[fsg-bridge2-select] COMPLETE candidates=30 eligible=8
  winner=(30.000,-30.000) second=0.439 span=1.464m jump50=0.892m graystd=31.09
```

Thresholds (predeclared, none relaxed): hit ≥ 0.95, second instance ≥ 0.10,
range span ≥ 0.40 m, boundary jump median ≥ 0.20 m, grey std ≥ 8 u8.
**8 of 30 eligible.** Ranking is second-instance fraction, then boundary jump,
then texture; the winner led on the first key outright (0.4389 vs 0.3935 next).

| yaw | pitch | hit | 2nd frac | nInst | P10 | P50 | P90 | span | jump50 | jump90 | greystd | elig |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:--:|
| −180 | −30 | 1.0000 | 0.0000 | 1 | 2.106 | 2.404 | 2.824 | 0.717 | 0.000 | 0.000 | 23.25 | – |
| −150 | −30 | 1.0000 | 0.2720 | 4 | 0.708 | 0.814 | 2.768 | 2.060 | 1.405 | 1.714 | 26.79 | **YES** |
| −120 | −30 | 1.0000 | 0.1782 | 6 | 0.584 | 0.692 | 2.422 | 1.838 | 1.448 | 1.744 | 23.51 | **YES** |
| −60 | −30 | 1.0000 | 0.2920 | 4 | 0.707 | 2.246 | 2.407 | 1.700 | 0.004 | 1.614 | 23.97 | – |
| −30 | −30 | 1.0000 | 0.1830 | 7 | 0.698 | 0.747 | 0.819 | 0.122 | 0.030 | 1.071 | 28.38 | – |
| 0 | −30 | 1.0000 | 0.0000 | 1 | 2.106 | 2.404 | 2.824 | 0.717 | 0.000 | 0.000 | 20.38 | – |
| **+30** | **−30** | **1.0000** | **0.4389** | **6** | **1.304** | **1.738** | **2.768** | **1.464** | **0.892** | **1.229** | **31.09** | **WINNER** |
| +60 | −30 | 1.0000 | 0.1183 | 6 | 0.919 | 2.296 | 2.688 | 1.769 | 0.595 | 1.735 | 40.31 | **YES** |
| +120 | −30 | 1.0000 | 0.2308 | 13 | 0.708 | 0.986 | 2.437 | 1.729 | 0.853 | 1.675 | 45.19 | **YES** |
| +150 | −30 | 1.0000 | 0.2330 | 8 | 1.291 | 2.187 | 2.803 | 1.511 | 0.488 | 1.097 | 29.22 | **YES** |
| −180 | 0 | 1.0000 | 0.3281 | 3 | 3.583 | 3.601 | 3.618 | 0.034 | 0.008 | 0.012 | 27.35 | – |
| −150 | 0 | 1.0000 | 0.1531 | 7 | 2.845 | 3.960 | 4.348 | 1.503 | 0.180 | 1.030 | 33.64 | – |
| −120 | 0 | 1.0000 | 0.2589 | 4 | 2.002 | 2.093 | 2.214 | 0.212 | 0.005 | 0.015 | 28.67 | – |
| −60 | 0 | 1.0000 | 0.2589 | 3 | 2.002 | 2.093 | 2.210 | 0.208 | 0.003 | 0.005 | 23.00 | – |
| −30 | 0 | 1.0000 | 0.1843 | 7 | 3.063 | 4.444 | 5.173 | 2.110 | 0.026 | 2.012 | 30.88 | – |
| 0 | 0 | 1.0000 | 0.2183 | 28 | 3.834 | 4.176 | 4.295 | 0.461 | 0.031 | 0.330 | 35.98 | – |
| +30 | 0 | 1.0000 | 0.1413 | 6 | 4.743 | 4.963 | 5.253 | 0.510 | 0.015 | 0.064 | 42.86 | – |
| +60 | 0 | 1.0000 | 0.2158 | 12 | 4.686 | 4.905 | 5.298 | 0.612 | 0.145 | 0.210 | 68.22 | – |
| +120 | 0 | 1.0000 | 0.1907 | 13 | 4.676 | 4.968 | 5.254 | 0.578 | 0.161 | 0.190 | 85.65 | – |
| +150 | 0 | 1.0000 | 0.3334 | 4 | 3.988 | 4.171 | 4.410 | 0.422 | 0.013 | 0.947 | 32.14 | – |
| −180 | +30 | 1.0000 | 0.3935 | 3 | 1.929 | 3.300 | 3.951 | 2.022 | 1.024 | 1.329 | 86.54 | **YES** |
| −150 | +30 | 1.0000 | 0.0913 | 5 | 2.634 | 3.374 | 3.831 | 1.197 | 0.011 | 0.477 | 21.14 | – |
| −120 | +30 | 1.0000 | 0.0356 | 3 | 2.278 | 2.445 | 2.652 | 0.374 | 0.015 | 0.022 | 19.16 | – |
| −60 | +30 | 1.0000 | 0.0356 | 3 | 2.278 | 2.445 | 2.652 | 0.374 | 0.015 | 0.022 | 19.86 | – |
| −30 | +30 | 1.0000 | 0.0562 | 6 | 2.940 | 3.146 | 3.833 | 0.893 | 0.045 | 0.254 | 21.86 | – |
| 0 | +30 | 1.0000 | 0.1531 | 5 | 2.538 | 2.870 | 3.756 | 1.217 | 1.167 | 1.375 | 59.72 | **YES** |
| +30 | +30 | 1.0000 | 0.0000 | 1 | 2.990 | 3.188 | 3.999 | 1.010 | 0.000 | 0.000 | 19.79 | – |
| +60 | +30 | 1.0000 | 0.0069 | 2 | 3.010 | 3.441 | 4.026 | 1.017 | 0.018 | 0.032 | 23.80 | – |
| +120 | +30 | 1.0000 | 0.0038 | 5 | 3.008 | 3.357 | 3.796 | 0.788 | 0.027 | 0.546 | 25.93 | – |
| +150 | +30 | 1.0000 | 0.1409 | 2 | 2.940 | 3.384 | 3.997 | 1.057 | 0.021 | 0.043 | 21.86 | – |

**Sealed winner (yaw +30.0, pitch −30.0)**: hit fraction 1.0000, 6 instances,
738 boundary pairs, reference range P10/P50/P90 **1.304 / 1.738 / 2.768 m**
(span **1.464 m**), boundary jump median **0.892 m** / P90 1.229 m, grey std
**31.09**. Substantial instances:

| id | root | px | fraction |
|---:|---|---:|---:|
| 159 | `sol` (carpet floor) | 8,035 | 49.04% |
| 7 | `Box297.002` (chair seat) | 7,191 | 43.89% |
| 47 | `Cylinder813.003` | 930 | 5.68% |
| 46 | `Cylinder813.001` | 193 | 1.18% |
| 92/93 | `Sphere140.003/004` | 35 | 0.22% |

The view is a wooden chair seat at ≈1.37 m suspended over carpet at ≈2.22 m,
with thin chrome tube legs and a slung cable — occlusion boundary, thin
geometry and a large depth step together.

### Phase B — final measurement at 64 spp

Fresh directory; the 16-spp candidate was **not** reused. Blender 5.2.1 LTS /
OPTIX, `small` / 64 spp / seed 2111, vergence 2.10 m, IPD 0.063 m,
`tangent_frame_mode: baseline_projected`, projection error **7.086e-05 px**,
hit fraction 1.0000 both eyes.

### Rectification

| quantity | value |
|---|---|
| `P2[0,3]` | **−38.36192** |
| `P2[1,3]` | **0.0** — horizontal, positive L−R |
| padded raster / rectified core | 320×320 / **128×128**, crop `[96, 96, 128, 128]` |
| rectified focal | 608.919 px |
| accepted disparity | min 8.71, **median 31.56**, max 50.12 px, window `[0, 64)` |

### Unchanged SGBM

```text
[fsg-stereo] classroom-structured-seed2111 valid=5687/16384 fraction=0.3471 ndisp=64 seconds=0.0741
```

**5,687 accepted of 16,384 (34.71%)**, against the control's 80.66%.
Rejections are overwhelmingly left–right consistency, not texture:

| diagnostic | valid median | invalid median | threshold |
|---|---:|---:|---|
| `lr_error_px` | 0.263 | **18.520** | 1.0 |
| `left_gray_std` | 7.849 | 9.866 | 0.5 |
| `raw_support_L` | 1.0000 | 1.0000 | — |

**76.21%** of rejected pixels fail the LR tolerance; **0.00%** fail the texture
floor — invalid pixels are in fact slightly *more* textured than valid ones.
The matcher is discarding geometry it cannot verify, which is the correct
behaviour.

### Overall accuracy

| statistic | value |
|---|---:|
| median | **27.258 mm** |
| P75 | 56.782 mm |
| P90 | 645.124 mm |
| **P95** | **1014.652 mm** |
| within 25 mm | 46.54% |
| within 50 mm | 72.67% |
| within 100 mm | 80.36% |
| wrong instance | **0** |

The median barely moves from the control (22.673 → 27.258 mm) while **P95
explodes 20× (50.605 → 1014.652 mm)**. The damage is entirely in the tail.

### Interior versus boundary — the band is empty

`instance_boundary_3x3_band.count = 0`, `boundary_fraction_of_compared = 0.0`.
Every accepted point is 3×3 single-instance interior, so the interior split is
numerically identical to the overall figures and the boundary split has no
samples. The 3-px instance guard plus LR consistency removed the entire
boundary band.

**That is the key structural finding: the tail is not at the boundary.** The
guard cleaned the boundary and the error appeared anyway, several pixels away.

### Per instance, and by reference depth

| instance | n | ref range median | median | P90 | P95 | ≤100 mm |
|---|---:|---:|---:|---:|---:|---:|
| 7 `Box297.002` (near seat) | 4,698 | 1.368 m | **22.636 mm** | 70.828 mm | 421.961 mm | **91.93%** |
| 159 `sol` (far floor) | 950 | 2.221 m | **807.593 mm** | 1159.484 mm | 1229.051 mm | **22.32%** |

| reference depth quartile | n | median | P95 | ≤100 mm |
|---|---:|---:|---:|---:|
| 1.225–1.316 m | 1,422 | 18.096 mm | 42.389 mm | **100.00%** |
| 1.316–1.395 m | 1,420 | 19.144 mm | 59.388 mm | 99.01% |
| 1.395–1.514 m | 1,423 | 26.522 mm | 211.082 mm | 93.25% |
| **1.514–3.019 m** | 1,422 | **436.178 mm** | 1199.542 mm | **29.18%** |

Below ≈1.5 m the instrument matches the Bridge-1R control exactly (18–27 mm
median). Above it, accuracy collapses. The split is by *depth*, not by image
position.

### Mechanism: foreground fattening, measured

The floor error is strongly bimodal — signed P25 **−1016 mm**, P50 −137 mm,
P75 +115 mm — so its 807 mm *absolute* median hides two populations:

- **48.00%** of floor points have error < −500 mm (estimated far too near);
- 22.32% are within 100 mm (correct);
- 6.84% are > +500 mm too far.

Isolating the 521 badly-near floor points:

| quantity | value |
|---|---:|
| their true range median | 2.2985 m |
| their **estimated** range median | **1.3363 m** |
| the seat's true range median | 1.3683 m |
| \|estimate − seat truth\| | **0.0320 m** |
| their disparity median | **31.69 px** |
| the seat's disparity median | 31.88 px |

They were matched at the **seat's** disparity. This is textbook foreground
fattening: the strongly textured near surface captures correspondence in a
neighbourhood far wider than the 3-px instance guard, and the far surface
inherits the near disparity.

**`wrong_instance = 0` does not contradict this.** That statistic compares the
left-eye oracle label with left-eye truth, so a floor pixel keeps id 159 even
when its right-eye correspondence landed on the seat. It certifies labelling,
not matching.

### Visual inspection

- **Raw tangent L/R** (320×320): a wooden chair seat centre-right over carpet,
  chrome tube legs, a slung dark cable, strong shadow and a sunlit carpet
  patch. L and R are visibly displaced horizontally.
- **`rectified_L/R.png`**: the seat as a bright angled quadrilateral with two
  small bright fixings, over dark carpet. The seat edge and fixings shift
  horizontally and not vertically between views.
- **Epipolar behaviour is horizontal**: NCC between the rectified pair peaks at
  **32 px (+0.6004)** — matching SGBM's 31.56 px accepted median — and the
  vertical residual at that shift peaks **exactly at dv = 0**, falling
  symmetrically (0.482 at ∓3 px).
- **`disparity.png`**: a coherent mid-grey wedge on the seat against a darker,
  heavily holed carpet field.
- **`validity.png`**: a dense bright wedge exactly on the seat; the carpet is
  largely black with scattered speckle. Invalid pixels concentrate on the far
  surface and around the legs and cable, i.e. at occlusion and thin geometry —
  though not in a thin rim at the seat edge, because that rim was removed
  wholesale by the guard.
- **`points_head.ply`** (5,687 pts): **genuinely bimodal, not a smeared
  bridge.** A dominant lobe at 1.18–1.52 m (the seat, truth median 1.42 m), a
  distinct second lobe at 1.96–2.40 m (the floor, truth median 2.26 m), and a
  deep trough between (45 points in 1.61–1.88 m). The two surfaces are
  separated — but the far lobe is under-populated because roughly half its
  points were pulled into the near lobe.

### Provenance

`observation.npz` holds exactly `rgb_L`, `rgb_R`, `instance_L`, `instance_R`,
and its on-disk sha256 matches the estimator's recorded input hash. Blender
range/XYZ exist only under `evaluation_only/` and were read only after stereo
was sealed. `z_rect_m` reproduces `f·B/disparity` to **2.29e-07 m** over every
accepted pixel, so geometry is triangulated, not copied; reconstruction is on
the 128×128 rectified core while truth is on the 320×320 raw tangent raster.
`foreground_warp_used` and `stereo_field_used` are both false.

### Comparison with the Bridge-1R control (descriptive; control not rerun)

| | Bridge-1R control (flat floor) | Bridge-2 (structured) |
|---|---:|---:|
| accepted | 80.66% | **34.71%** |
| median abs error | 22.673 mm | 27.258 mm |
| P95 abs error | 50.605 mm | **1014.652 mm** |
| within 50 mm | 94.59% | 72.67% |
| wrong ID | 0 | 0 |

The control is near-ideal planar geometry and Bridge-2 deliberately adds
structure, so this is not a target to beat. The informative pattern is that the
**median is nearly preserved while acceptance halves and the tail grows 20×** —
the instrument does not degrade gracefully everywhere at once; it stays
control-grade on the near surface and fails specifically on the far one.

### What this establishes

The unchanged native FSG instrument runs on genuine local Classroom depth
structure and returns a non-trivial, bimodal, metric patch. Rectification stays
horizontal, the estimator's own LR test removes most bad matches, the 3-px
instance guard clears the boundary band completely, and the near surface is
measured at control accuracy (22.6 mm median, 91.9% within 100 mm).

### What this does NOT establish

One fixation, one gaze, one profile. The failure mode is identified but not
characterised across scenes, baselines, vergences or textures. Nothing here
says the 3-px guard, the 1.0-px LR tolerance or the `[0.75, 4.5] m` search band
are right or wrong in general — only that at this geometry the fattening
extends beyond the guard. No fusion, no controller, no FSG6f, no attention, no
foreground/background claim, no Classroom reconstruction. No parameter was
tuned and no threshold was relaxed; the selection ran entirely before stereo.
