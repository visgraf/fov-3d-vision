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

Pending workstation execution.
