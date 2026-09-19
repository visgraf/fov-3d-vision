# FSG1h — corrected final prospective validation

Status at handoff: **instrument unchanged; FSG1g invalidated by fixture-integrity failure before the full run**. Read `CLAUDE.md` first.

FSG1g did not fail a stereo gate. Its finite occluder edges were outside the accepted ±6° core, so the half-occlusion population was empty and Code correctly stopped at smoke. FSG1h corrects **only that fixture geometry** and adds a pre-render check using the evaluator's actual reference construction. The local stereo candidate remains exactly:

```text
fixed soft-HDR encoding
→ unchanged SGBM
→ exactly ONE original photometric refinement update
→ unchanged original validity predicate
```

No endpoint or footprint-supported reciprocity is used.

## 1. Decision to record before any new acquisition

Check that `D-FSG1h` does not already exist. If it does, stop. Append this decision to `DECISIONS.md` and a prospective entry to `docs/log.md` before rendering:

```text
## D-FSG1h — correct the invalid FSG1g occluder fixture, instrument unchanged (2026-09-19)
FSG1g stopped at small smoke for an integrity failure: both prescribed finite-foreground edges were outside the accepted ±6° core, so the intended half-occlusion reference was empty. This was a Chat fixture-design error, not a numerical result about the stereo instrument.

Preserve the frozen FSG1g instrument, gates, profile, spp, texture construction, depths and seed schedule. Correct only the foreground x extents so finite occluding edges lie inside the accepted core: occluder_left [-0.16,+0.10] m at z=-1.85 m; occluder_right [-0.10,+0.16] m at z=-1.95 m. Backgrounds remain -3.05 m and -3.15 m.

Before Blender, require the evaluator's own analytic ground-reference construction to prove nonempty substantial half-occlusion cores, boundary populations, and >=100 interior reference pixels for both instances at both profiles. Recreate the FSG1g geometry as a negative control and require it to fail.

Run only corrected small seed 101 and corrected full seeds 101 and 149. Do not tune, change the candidate, change thresholds, change spp, add support vetoes, fill holes, or rerender after a numerical miss. If every prescribed full gate passes, close FSG1 / Increment 1 and authorize but do not implement Increment 2. Otherwise preserve the failure and stop for Luiz/Chat.
```

## 2. Exact correction

Only the occluder foreground x intervals differ from FSG1g:

| Case | FSG1g invalid interval | FSG1h corrected interval | Foreground Z | Background Z |
|---|---:|---:|---:|---:|
| `occluder_left` | [-1.00,+0.35] m | **[-0.16,+0.10] m** | -1.85 m | -3.05 m |
| `occluder_right` | [-0.35,+1.00] m | **[-0.10,+0.16] m** | -1.95 m | -3.15 m |

The corrected edges are finite and lie inside the accepted angular field. The rectangles are deliberately not large half-planes; missing geometry and both depth-discontinuity sides remain visible to the evaluator.

Everything else is frozen from FSG1g: four phase planes at full-profile disparities 22.00/22.25/22.50/22.75 px, textures, fixed head frame, oracle instance IDs, 63 mm baseline, full profile, 256 spp, seeds 101/149, one-update candidate, interior gates, boundary gates and zero accepted singly-visible core points.

## 3. Pre-render fixture proof

`tools/dev/check_fsg_finalh_validation.py` calls the same `fsg_evaluate.ground_reference()` logic used by evaluation on analytic triangles from the frozen fixture. Expected populations from the handoff build are:

| Profile / case | singly-visible raw | eroded core | jointly-visible boundary | foreground interior | background interior |
|---|---:|---:|---:|---:|---:|
| small / left | 1024 | 768 | 1920 | 9600 | 3840 |
| small / right | 1024 | 768 | 1792 | 9088 | 4480 |
| full / left | 4096 | 3072 | 6912 | 39424 | 15104 |
| full / right | 3840 | 2816 | 6656 | 37120 | 17920 |

These are deterministic geometry/reference counts, **not stereo results**. If Code gets different populations, stop and diagnose rather than rendering.

The `--negative fixture` check reconstructs the original FSG1g off-core rectangle and must exit 1 because its singly-visible reference is empty.

## 4. Evaluation contract — unchanged

For every full seed and every instance with >=100 eligible interior points:

```text
coverage >= 0.90
median relative range error <= 0.01
p95 relative range error <= 0.03
```

For each corrected occluder and full seed:

```text
singly-visible raw/core populations must meet the prescribed minima
accepted singly-visible eroded-core points = 0
```

For jointly visible boundary points:

```text
accepted points >= 100
median relative range error <= 0.01
p95 relative range error <= 0.03
```

Boundary coverage itself is descriptive, not gated. Missing points stay missing. No interpolation or hole filling.

## 5. Execution order

### 5.1 Preflight — Interactive

```bash
git status --short
git merge-base --is-ancestor 7408e03 HEAD
.venv/bin/python -c "import sys,numpy,cv2,PIL; print(sys.version); print(numpy.__version__,cv2.__version__,PIL.__version__)"
.venv/bin/python tools/fsg_finalh_scene.py
.venv/bin/python tools/dev/check_fsg_finalh_validation.py
```

Run four negatives; every command must exit 1:

```bash
.venv/bin/python tools/dev/check_fsg_finalh_validation.py --negative phase
.venv/bin/python tools/dev/check_fsg_finalh_validation.py --negative boundary
.venv/bin/python tools/dev/check_fsg_finalh_validation.py --negative candidate
.venv/bin/python tools/dev/check_fsg_finalh_validation.py --negative fixture
```

Also run the existing FSG regression checks available in the checkout. An integrity/source/reference-population failure stops the experiment. Do not alter geometry or checks locally.

### 5.2 Corrected small smoke — Interactive

Use new output paths; do not overwrite FSG1g:

```bash
blender -b --python-exit-code 1 -P tools/fsg_finalh_render.py -- \
  --out previews/fsg1/finalh-small-seed101 --profile small --seed 101 --device OPTIX --save-blend

.venv/bin/python tools/fsg_finalh_eval.py previews/fsg1/finalh-small-seed101 \
  --mode smoke --out previews/fsg1/finalh-small-evaluation
```

A numerical exit 2 is diagnostic and does not block full. Exit 1 for provenance, fixture, geometry, source or software integrity blocks full.

Inspect all six validation images. For both occluders, confirm that the accepted crop visibly contains foreground/background boundaries and that `singly visible`, `occlusion core`, and `unsafe accepted core` panels are meaningful rather than empty by construction.

### 5.3 Full prospective validation — Batch

```bash
blender -b --python-exit-code 1 -P tools/fsg_finalh_render.py -- \
  --out previews/fsg1/finalh-full-seed101 --profile full --seed 101 --device OPTIX --save-blend

blender -b --python-exit-code 1 -P tools/fsg_finalh_render.py -- \
  --out previews/fsg1/finalh-full-seed149 --profile full --seed 149 --device OPTIX --save-blend

.venv/bin/python tools/fsg_finalh_eval.py \
  previews/fsg1/finalh-full-seed101 previews/fsg1/finalh-full-seed149 \
  --mode full --out previews/fsg1/finalh-full-evaluation
```

Do not rerun with a different seed or spp after a numerical miss.

The nominal primary-camera schedule is unchanged from FSG1g: 78,643,200 for smoke; 1,258,291,200 for each full seed; 2,595,225,600 total if all stages run. Report actual times separately.

## 6. Code report

Return one paste block with:

1. HEAD before/after, branch, commit/push, and proof D-FSG1h/log were recorded before acquisition.
2. Environment versions and GPU backend.
3. New fixture-reference counts from preflight, all software-check summaries, and all four expected negative FAIL lines.
4. Exact commands/output paths.
5. Every phase-plane metric and measured truth disparity/phase for both full seeds.
6. Every occluder instance metric separately for both full seeds.
7. Raw/core singly-visible reference and accepted counts, wrong-instance counts.
8. Boundary reference/accepted counts, descriptive coverage, median/P95 and gate result.
9. Visuals inspected and PLY/head-frame observations.
10. Sample counts and timings.
11. Every numerical FAIL and unexpected exception/fix verbatim.
12. Exact final status from `finalh-full-evaluation/validation.json`.

If the full status is `FSG1H_FINAL_VALIDATION_PASS`, update README, this document's Results section, `docs/log.md`, and `DECISIONS.md`; record the one-update instrument as the FSG1 local RGB-D instrument, mark Increment 1 complete, and state **Increment 2 authorized but not implemented**. On any full numerical miss, preserve it and stop.

## 7. Scope

A pass qualifies one local RGB-D patch under controlled opaque, diffuse, calibrated conditions with oracle instance segmentation and known fixed cameras. It does not claim arbitrary-scene stereo, complete boundary coverage, calibrated uncertainty, or multi-patch reconstruction.

## Results

Run 2026-09-19 on the workstation by Code. Every number is read from files under
`previews/fsg1/finalh-*`.

**`FSG1H_FINAL_VALIDATION_PASS`.** Every prescribed full gate passes on both
fresh seeds, with no numerical FAIL line anywhere, zero accepted half-occlusion
core points and zero wrong-instance acceptances. `all_gates_pass: true`,
`prospective_blender_validation_pass: true`, `full_profile_milestone_pass: true`,
`increment1_complete: true`, `increment2_authorized: true`,
`adopted_as_fsg1_instrument: true`. 2,516,582,400 acquisition primary camera
samples; 0 added by inference; evaluation 8.197 s.

**FSG1 / Increment 1 is CLOSED.** The candidate
`FSG1-HDR-SGBM-one-original-update-original-validity-v1` is recorded as the FSG1
local RGB-D instrument. **Increment 2 is AUTHORIZED BUT NOT IMPLEMENTED** - no
fusion, surface map, saccade policy or multi-patch work was written in this run.

### Integrity and the fixture correction

HEAD `f1d71c98504dc9bc3679b19c0b6ee918f417d838` on clean `main`, `7408e03` an
ancestor. The frozen-instrument diff over the fifteen pinned modules, `rig.py`,
`bl_common.py` and `requirements-fsg.txt` is EMPTY; six files added by the
handoff and none modified. Python 3.12.3, NumPy 2.2.6, OpenCV 4.13.0, Pillow
12.3.0; Blender 5.2.1 LTS, OPTIX on an RTX 4090. D-FSG1h and a prospective
`docs/log.md` entry were recorded BEFORE any acquisition. FSG1g's records were
preserved, not overwritten.

The candidate is unchanged from FSG1g and was verified by reading
`tools/fsg_finalh_eval.py` before running: it calls
`fsg_stereo_supported.compute_once()`, never `compute_variants()`. No endpoint or
footprint support veto is used.

Only the two occluder foreground x extents changed. Measured against the FSG1g
module: `occluder_left` [-1.00,+0.35] -> [-0.16,+0.10] m and `occluder_right`
[-0.35,+1.00] -> [-0.10,+0.16] m, putting all four edges 2.936-4.943 degrees off
the gaze axis, inside the +/-6.000 degree accepted core (core half-width 0.1944 m
at 1.85 m, 0.2050 m at 1.95 m). Depths (-1.85/-3.05 and -1.95/-3.15 m), instance
IDs, phase targets, textures, seeds, profile, spp and every gate are unchanged.

### Pre-render fixture proof, and one documentation discrepancy

Computed with the evaluator's own `ground_reference` and `eroded_core`:

| profile / case | raw | core | boundary | fg interior | bg interior |
| --- | ---: | ---: | ---: | ---: | ---: |
| small / left | 1024 | **756** | 1920 | 9600 | 3840 |
| small / right | 1024 | **756** | 1792 | 9088 | 4480 |
| full / left | 4096 | **3024** | 6912 | 39424 | 15104 |
| full / right | 3840 | **2772** | 6656 | 37120 | 17920 |

Raw, boundary and both interiors match the handoff table **exactly**. The eroded
core differs from its stated 768/768/3072/2816, and I diagnosed that before
rendering rather than proceeding on trust: the handoff computed the core as
`(w-2r)*h`, eroding only horizontally, while `cv2.erode` erodes both axes giving
`(w-2r)*(h-2r)`. Both formulas reproduce their respective numbers exactly in all
four rows, on strips measured at 8x128 (small) and 16x256 / 15x256 (full). So the
fixture geometry is exactly as intended and only that one documentation column is
arithmetically wrong. The actual cores exceed the required minima (32 small, 128
full) by 21.7-23.6x, and the shipped check gates on those minima. Nothing was
altered.

`[fsg-finalh-scene] PASS cases=6 phases=4 corrected_finite_occluders=2` and
`[fsg-finalh-check] SUMMARY passed=8 failed=0 occluder_reference_checks=4`.
Existing suites: 24 / 29 / 34 / 48 / 37 / 46 / 7, zero failures. All four
negatives exit 1, including the FSG1g regression that proves this check would
have caught the original defect:

    [fsg-finalh-check] FAIL AssertionError: deliberate phase mutation detected
    [fsg-finalh-check] FAIL AssertionError: deliberate bad boundary detected: boundary median_relative_range_error=0.02 fails max 0.01; boundary p95_relative_range_error=0.04 fails max 0.03
    [fsg-finalh-check] FAIL AssertionError: deliberate candidate substitution detected
    [fsg-finalh-check] FAIL AssertionError: deliberate off-core occluder detected: singly-visible reference is empty

### Full results, both seeds (gates: coverage >=90%, median <=1%, p95 <=3%)

Phase planes, with the fixture verified rather than assumed - measured truth
disparities are 22.00000 / 22.25000 / 22.50000 / 22.75000 px at fractional phases
0.0000 / 0.2500 / 0.5000 / 0.7500:

| seed / case | ref | coverage | median | p95 | >3% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 101 / phase_00 | 65536 | 99.965% | 0.0849% | 0.2844% | 0.000% |
| 101 / phase_25 | 65536 | 99.886% | 0.0973% | 0.3655% | 0.000% |
| 101 / phase_50 | 65536 | 99.940% | 0.2209% | 0.9252% | 0.014% |
| 101 / phase_75 | 65536 | 99.774% | 0.1293% | 0.4091% | 0.000% |
| 149 / phase_00 | 65536 | 99.963% | 0.0852% | 0.2863% | 0.000% |
| 149 / phase_25 | 65536 | 99.890% | 0.0967% | 0.3607% | 0.000% |
| 149 / phase_50 | 65536 | 99.936% | 0.2255% | 0.9587% | 0.003% |
| 149 / phase_75 | 65536 | 99.765% | 0.1297% | 0.4128% | 0.000% |

The half-integer phase is the hardest, as FSG1e predicted, but at roughly a fifth
of the median budget rather than a failure. Occluder interiors, per instance:

| seed / case / instance | ref | coverage | median | p95 | >3% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 101 / left / 21 (fg 1.85 m) | 39424 | 100.000% | 0.2399% | 0.5460% | 0.000% |
| 101 / left / 22 (bg 3.05 m) | 15104 | 93.287% | 0.4046% | 1.6378% | 0.312% |
| 101 / right / 31 (fg 1.95 m) | 37120 | 100.000% | 0.1360% | 0.3819% | 0.000% |
| 101 / right / 32 (bg 3.15 m) | 17920 | 95.128% | 0.3774% | 1.3736% | 0.563% |
| 149 / left / 21 | 39424 | 100.000% | 0.2411% | 0.5440% | 0.000% |
| 149 / left / 22 | 15104 | 93.167% | 0.3904% | 1.6378% | 0.320% |
| 149 / right / 31 | 37120 | 100.000% | 0.1383% | 0.3839% | 0.000% |
| 149 / right / 32 | 17920 | 95.190% | 0.3549% | 1.3991% | 0.621% |

The occluded backgrounds are the tightest margin at 93.2-95.2% coverage against
the 90% floor - about 3-5 points of headroom, the smallest anywhere in the suite.

### Half-occlusion safety and boundary accuracy

The mirrored fixture is genuinely exercised on both seeds and both orientations:

| seed / case | raw ref | core ref | accepted raw | accepted core | wrong-instance |
| --- | ---: | ---: | ---: | ---: | ---: |
| 101 / occluder_left | 4096 | 3024 | 0 | **0** | 0 |
| 101 / occluder_right | 3840 | 2772 | 0 | **0** | 0 |
| 149 / occluder_left | 4096 | 3024 | 0 | **0** | 0 |
| 149 / occluder_right | 3840 | 2772 | 0 | **0** | 0 |

Not one of the 11,592 core points across the four occluder-seed combinations was
accepted, and not a single raw singly-visible point either. Boundary accuracy,
gated on accepted points with coverage reported descriptively only:

| seed / case | boundary ref | accepted | coverage | median | p95 | gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 101 / left | 6912 | 4041 | 58.464% | 0.3302% | 2.0450% | PASS |
| 101 / right | 6656 | 3973 | 59.691% | 0.2230% | 1.4432% | PASS |
| 149 / left | 6912 | 4044 | 58.507% | 0.3174% | 2.0518% | PASS |
| 149 / right | 6656 | 3980 | 59.796% | 0.2222% | 1.4866% | PASS |

All far above the 100-point exercise minimum. Roughly 40% of boundary reference
points remain unaccepted; they stay missing, with no interpolation or fill.

### Visuals and point clouds

All six small validation sheets were inspected before the full stage, and the
full occluder sheets afterwards. Both occluder crops now visibly contain a finite
foreground rectangle with BOTH depth edges inside the accepted core - background,
bright foreground, background - mirrored between the two cases. Validity is
near-solid with two excluded bands at the edges; the occlusion-core panel is a
clear non-empty strip; the unsafe-accepted-core panel is entirely black; the
missing panel shows the excluded strips rather than filling them. The four phase
sheets show full validity and interior-error panels that brighten from phase_00
to phase_50, matching the measured medians.

Candidate point clouds are head-frame, no faces, no fill, and land on the frozen
geometry: `occluder_left` 57,555 / 57,540 points with instance medians
Z = -1.8460 m (spec -1.85) and -3.0494 / -3.0506 m (spec -3.05); `occluder_right`
58,140 / 58,158 at -1.9476 (spec -1.95) and -3.1490 / -3.1488 (spec -3.15);
phase planes 65,382-65,513 points at -3.4888 / -3.4468 / -3.4080 / -3.3759 m,
matching f*B/d for the four target disparities.

### Cost

Calculated: smoke 78,643,200; each full seed 1,258,291,200; 2,595,225,600 total
across all three stages, all of which ran. Measured: small render 3.637 s Blender
wall (6 cases, 0.215-0.263 s each); full seed 101 10.101 s; full seed 149
10.056 s; smoke evaluation exit 2 (diagnostic, did not block); full evaluation
8.313 s wall / 8.197 s internal. Batch class throughout.

The small smoke missed two gates diagnostically - `occluder_left` instance 22
coverage 87.031% and boundary p95 3.306% - which under section 5.2 is exit 2 and
does not block the full run. Both cleared comfortably at the full profile
(93.287% and 2.045%), consistent with the resolution dependence seen throughout
FSG1. No rerender, seed change, spp change or tuning was performed at any point.

### What this does and does not establish

One local RGB-D patch instrument is validated prospectively, on fixtures and
seeds it had never seen, against gates frozen before the data existed: four
disparity phases spanning the pixel-locking failure mode that broke FSG1d, and
two mirrored finite occluders that exercise left-reference half-occlusion from
both edge orientations with zero unsafe acceptances.

It remains a controlled opaque, diffuse, planar calibration suite with oracle
instance segmentation, known fixed camera poses, and two Monte-Carlo seeds of the
same six geometries. It does not establish arbitrary-scene stereo, complete
boundary coverage - about 40% of boundary reference points are not accepted -
thin-structure performance, calibrated uncertainty, or anything about multi-patch
reconstruction. Earlier recorded limitations stand unchanged: the small-profile
misses, the analytic bright-full stress, and the FSG1c/FSG1f development-set
caveats.

Increment 1 is closed on that basis and Increment 2 is authorized, not
implemented. Stopped for Luiz and Chat.
