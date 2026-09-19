# FSG1g — final prospective validation of the simple one-update instrument

Status at handoff: **unmeasured on fresh Cycles observations**. Read `CLAUDE.md` first.

This is the last planned experiment in Increment 1. It tests the simplest instrument supported by FSG1f:

```text
fixed soft-HDR encoding
→ unchanged SGBM
→ exactly ONE original photometric refinement update
→ unchanged original validity predicate
```

It deliberately does **not** use FSG1f's endpoint or 5×5 footprint support vetoes. FSG1f showed that all known half-occlusion leaks were already rejected by the one-step validity, while the footprint veto removed about half the accepted boundary population on the step fixtures. The old records are development data and have no validation role here.

## 1. Decision to record BEFORE any acquisition

Check that `D-FSG1g` does not already exist. If it does, stop rather than duplicating it. Append the following to `DECISIONS.md`, and append a prospective entry to `docs/log.md` before running any render:

```text
## D-FSG1g — final prospective validation of the simple local stereo instrument (2026-09-19)
Freeze the FSG1 instrument for one final validation as: FSG1c fixed soft-HDR encoding, unchanged SGBM, exactly one original photometric refinement update, and the original validity predicate. Do not use FSG1f endpoint or footprint-supported reciprocity.

Why: on the seven diagnostic pairs, one update passed every unchanged interior gate and rejected every previously observed half-occlusion leak before the additional FSG1f vetoes acted. The footprint rule cost about 2.5% interior support on the occluded background and about half the accepted boundary population, so it is not justified by the present evidence.

Validate only on the new FSG1g fixtures and fresh seeds 101 and 149. The suite contains four frontoparallel planes whose full-profile disparities have fractional phases 0, .25, .50 and .75, plus two mirrored finite-foreground occluders. Use the unchanged full profile at 256 spp; small seed 101 is only a smoke/integration run. No parameter search, rerender after a numerical miss, threshold change, hole filling, or estimator adaptation is authorized.

Pass rule, evaluated separately for every full seed and every instance: interior coverage >= 0.90, median relative range error <= 0.01, p95 <= 0.03; zero accepted points in each prescribed eroded singly-visible core; and on each occluder, at least 100 accepted jointly-visible boundary points with median <= 0.01 and p95 <= 0.03. A zero/too-small population is NOT_EXERCISED, not a pass.

If every prescribed full gate passes on both seeds, close FSG1 / Increment 1, record this one-update instrument as the FSG1 local RGB-D instrument, and authorize (but do not implement in this run) Increment 2: two overlapping patches in the fixed head-centred map. If any full gate misses, preserve the failure and stop for Luiz/Chat. No control or alternative candidate is selected after seeing results.
```

## 2. Fresh fixtures

`tools/fsg_final_scene.py` fixes the geometry before rendering.

### Phase planes

Four separate single-plane cases have target full-profile disparities:

```text
phase_00 : 22.00 px
phase_25 : 22.25 px
phase_50 : 22.50 px
phase_75 : 22.75 px
```

Their physical depths are derived from the fixed full-profile focal length and 63 mm baseline before acquisition. These are a numerical stress test for pixel-locking/refinement phase, not a biological claim.

Each plane has a different oracle instance ID, hence a different new procedural texture. None of the seed-17/31/73 textures are reused.

### Mirrored finite occluders

`occluder_left` and `occluder_right` use finite foreground rectangles against different farther backgrounds, with new ranges and textures. The mirrored geometry is intended to exercise left-reference half-occlusion rather than infer safety from one edge orientation.

The evaluator requires a substantial singly-visible population. If the fixture fails to create it, this is an integrity/test-design failure (exit 1), not a numerical pass.

## 3. Frozen candidate

Inference calls `fsg_stereo_supported.compute_once()` directly. This is the FSG1f one-step control:

- FSG1c `hdr_to_u8` encoding;
- original SGBM calls and settings;
- one and only one original Gauss–Newton update in each eye;
- original interpolated LR check, texture cutoff, instance guard, depth bounds and valid-disparity ROI;
- no endpoint contributor veto;
- no footprint erosion/support veto;
- no truth access during inference.

`tools/dev/check_fsg_final_validation.py` fails if the final validator selects the FSG1f named supported candidate instead of `compute_once`.

## 4. Evaluation contract

The original interior thresholds remain unchanged and are applied to the pooled interior and every instance with >=100 independently eligible pixels:

```text
coverage >= 0.90
median relative range error <= 0.01
p95 relative range error <= 0.03
```

For each occluder, the fixed eroded singly-visible core must have **zero accepted predictions**. All raw singly-visible pixels are also reported.

Boundary completeness is *not* a percentage target in FSG1. But an accuracy gate is now exercised: each full occluder must have at least 100 accepted jointly-visible boundary points, and those accepted points must have median relative range error <=1% and p95 <=3%. Missing boundary points remain missing; there is no interpolation or fill.

A pass therefore means that accepted local geometry is accurate enough for a persistent-map experiment. It does not claim complete boundaries, arbitrary-scene stereo, thin-structure performance, or calibrated uncertainty.

## 5. Workstation execution order

### 5.1 Preflight — Interactive

Require clean `main` descended from the FSG1f report commit, then read this document and the working agreement.

```bash
git status --short
git merge-base --is-ancestor 837acfe HEAD
.venv/bin/python -c "import sys,numpy,cv2,PIL; print(sys.version); print(numpy.__version__,cv2.__version__,PIL.__version__)"
.venv/bin/python tools/fsg_final_scene.py
.venv/bin/python tools/dev/check_fsg_final_validation.py
```

Expected environment from the saved FSG1 records: Python 3.12.3, NumPy 2.2.6, OpenCV 4.13.0, Pillow 12.3.0. Do not upgrade packages to make a result change.

Run the three negative controls; each must exit 1:

```bash
.venv/bin/python tools/dev/check_fsg_final_validation.py --negative phase
.venv/bin/python tools/dev/check_fsg_final_validation.py --negative boundary
.venv/bin/python tools/dev/check_fsg_final_validation.py --negative candidate
```

Likely integrity failures, in order: a current repository calibration/API drift; an inherited validation-renderer equivalence guard; an empty half-occlusion reference caused by unexpected geometry. Diagnose these before any edit. Do not change a gate, scene, seed, spp, encoding, iteration count, matcher setting, erosion radius or reference mask to make the check pass.

A small orchestration/API compatibility fix is delegated only if it preserves the frozen semantics above, is outside the checks, and is described exactly in the report. Any change that can affect geometry, RGB, disparity, validity or evaluation requires stopping for Luiz/Chat instead.

### 5.2 Small smoke — Interactive

Fresh output paths only:

```bash
blender -b --python-exit-code 1 -P tools/fsg_final_render.py -- \
  --out previews/fsg1/final-small-seed101 --profile small --seed 101 --device OPTIX --save-blend

.venv/bin/python tools/fsg_final_eval.py previews/fsg1/final-small-seed101 \
  --mode smoke --out previews/fsg1/final-small-evaluation
```

The small numerical result is diagnostic. Exit 2 for a numerical miss does not block the prescribed full run. Exit 1 for provenance, geometry, source, fixture or software integrity does block it.

Inspect all six `validation.png` images. In particular, verify that the two occluders visibly contain finite foreground rectangles, missing predictions are not filled, and the phase planes do not show a coordinate/orientation mistake.

### 5.3 Full prospective run — Batch

Run exactly the two predeclared fresh seeds, once each:

```bash
blender -b --python-exit-code 1 -P tools/fsg_final_render.py -- \
  --out previews/fsg1/final-full-seed101 --profile full --seed 101 --device OPTIX --save-blend

blender -b --python-exit-code 1 -P tools/fsg_final_render.py -- \
  --out previews/fsg1/final-full-seed149 --profile full --seed 149 --device OPTIX --save-blend

.venv/bin/python tools/fsg_final_eval.py \
  previews/fsg1/final-full-seed101 previews/fsg1/final-full-seed149 \
  --mode full --out previews/fsg1/final-full-evaluation
```

Do not rerun with another seed or spp after seeing a numerical miss. The two seeds are two Monte-Carlo realizations of the same six geometries, not twelve independent scenes.

Nominal primary-camera cost from the fixed schedule is calculated, not measured:

- small smoke: 6 cases × 2 eyes × 320² × 64 = **78,643,200** samples;
- each full seed: 6 × 2 × 640² × 256 = **1,258,291,200** samples;
- both full seeds: **2,516,582,400** samples;
- total including smoke: **2,595,225,600** primary camera samples.

Report actual Blender/render/evaluation wall times separately. These counts are primary camera samples, not all secondary path rays.

## 6. What Code must report

Return one paste block containing:

1. HEAD before/after, branch, commit/push result, and confirmation that D-FSG1g/log entry were written before acquisition.
2. Python/NumPy/OpenCV/Pillow, Blender version, GPU backend, and unchanged pins.
3. All software-check summary lines and all three expected negative FAIL lines/exits.
4. Exact render/evaluation commands and output paths.
5. For every phase plane and full seed: reference count, coverage, median, p95, >3% fraction; also report the measured truth-disparity median/fractional phase so the fixture is checked rather than assumed.
6. For every occluder instance and seed: the same interior metrics separately; no pooled result may substitute for an instance failure.
7. For each occluder/seed: raw/core singly-visible reference counts, accepted raw/core counts, wrong-instance count.
8. For each occluder/seed: jointly-visible boundary reference and accepted counts, coverage (descriptive only), median and p95, and boundary gate result.
9. Visuals actually inspected and what was seen; PLY point counts and head-frame range medians.
10. Calculated primary sample counts and measured timings.
11. Every numerical FAIL line verbatim and every unexpected exception/fix.
12. Final exact status from `final-full-evaluation/validation.json`.

If `FSG1_FINAL_VALIDATION_PASS`, update README / `docs/fsg1-final-validation.md` Results / `docs/log.md` / DECISIONS with measured results, mark Increment 1 complete, and state **Increment 2 authorized but not implemented**. If `FSG1_FINAL_VALIDATION_FAIL`, preserve the failure and stop without inventing a new candidate.

## 7. Scope boundary

No multi-patch fusion, surface map, saccade policy or object exploration is implemented in FSG1g. A pass closes only the **single local RGB-D patch instrument** milestone under controlled calibration conditions.
