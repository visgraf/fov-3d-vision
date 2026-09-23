# Demo-Tabletop-1 — Oracle-assisted concept demonstration

## Purpose

This is deliberately **not** another controller experiment. It is the first polished concept demonstration of the whole active foveal-stereo scene-construction idea on the established procedural `tabletop_cloth` fixture.

The demo is allowed to use Blender evaluator information as supervisory scaffolding. The purpose is to show the architecture working end-to-end, not to claim autonomous discovery or a truth-free controller.

## The one hard boundary

Blender may tell the demo **what object is visible, where to look, and whether a stereo depth is plausible**. It may not silently replace foreground stereo geometry with evaluator geometry.

Foreground metric points therefore have this provenance:

`foveated binocular render -> established stereo -> oracle validity gate -> established fusion -> persistent foreground geometry`

A reference point may reject a stereo sample; it does not become the accepted sample.

## Background

For the Tabletop demonstration, `rc1_wall` is explicitly declared a special background object. It is exported as a separate visual layer with trivial/soft-depth support and reference texture. It is not counted as stereo-reconstructed foreground geometry.

This is a demonstration scaffold and an initial concrete use of the foreground/background idea. The future research problem is to infer this decomposition and its soft depth regime rather than declare it.

## Attention

Normal local FSG control is reused whenever it produces an action. When it stalls while Blender says relevant target support remains, Demo Mode may issue a bounded oracle redirect. This is intentionally called **oracle attention assistance**, not a new general controller.

## Measurement validation

The demo records raw stereo and oracle-accepted stereo separately. The default demo gate is:

`abs(z_stereo - z_reference) <= max(0.10 m, 0.05 * z_reference)`

This is an engineering aid for the concept demo, not a scientific estimate of stereo confidence.

## Deliverables

The run exports:

- stereo-derived foreground point clouds and spherical depth/instance products;
- a separate oracle background visual layer;
- a provenance-preserving composite RGB-D demonstration product;
- the Blender reference products;
- a fixation timeline, and an MP4 when `ffmpeg` is available;
- a manifest/report that labels every layer and every use of truth.

The visual story should make the cycle legible: **look -> stereo -> validate -> fuse -> remember -> redirect attention -> build scene**.

## Results

**COMPLETE 2026-09-23 on branch `demo-tabletop-1`** (`DEMO_TABLETOP1_COMPLETE
objects=5 fixations=72`; comparator `DEMO_TABLETOP1_COMPLETE structural_fails:
[]` exits 0). Record `previews/demo-tabletop1/full-seed2111`, seed 2111,
profile `full`, OPTIX, Blender 5.2.1 LTS, 72 Blender launches, 587 s rendering.

### Oracle aids actually used

| aid | used | note |
|---|---|---|
| object identity / instance masks | **yes** | dynamic enumeration from the live scene spec |
| seed-gaze guidance from reference support | **yes** | 4 seeds |
| redirect gaze when local control stalls | **yes** | 8 redirects |
| reference depth for measurement validation | **yes** | rejected 4.88% of raw stereo |
| reference RGB for background texture | **yes** | declared background layer only |
| **reference depth inserted into metric foreground** | **NO** | the hard boundary, verified per fixation |

### The hard boundary held, and was verified rather than asserted

Across all **69 rendered fixations**:

- the accepted set is a **bitwise row-subset of the stereo xyz array** — 69/69;
- it is a pure boolean filter of that array — 68/68 where samples existed (the
  69th had 0 valid stereo samples and takes the zero-sample path);
- **0 fixations** had reference depth supply a foreground value;
- **1,210,308 of 1,210,308 accepted rows (100.00%)** differ bitwise from the
  reference-derived position along the same direction — the reference point was
  computed only to record that it was *not* adopted.

Rejections break down as **62,139 gate rejections, 0 wrong-instance, 0
no-reference-hit**.

### Objects

| id | label | role | fixations | redirects | stop | foreground surfels | reference coverage |
|---:|---|---|---:|---:|---|---:|---:|
| 141 | `rc1_cloth` | STEREO_FOREGROUND | 20 | 1 | `DEMO_TARGET_SATISFIED` | 146,548 | 0.9510 |
| 142 | `rc1_table` | STEREO_FOREGROUND | 32 | 7 | `DEMO_OBJECT_GUARDRAIL` | 368,295 | 0.7491 |
| 143 | `rc1_wall` | **BACKGROUND_SCAFFOLD** | 0 | 0 | `DECLARED_BACKGROUND_NO_CONTROL` | **0** | — |
| 144 | `rc1_book_left` | STEREO_FOREGROUND | 11 | 1 | `DEMO_TARGET_SATISFIED` | 4,123 | 0.9082 |
| 145 | `rc1_box_right` | STEREO_FOREGROUND | 9 | 0 | `DEMO_TARGET_SATISFIED` | 6,779 | 0.9228 |

Three of four foreground objects reached the demo coverage condition; the table
hit the 32-fixation engineering guardrail at 74.9%, which is **not** a
completion claim. Object 143 is the declared background and contributes
**0 foreground surfels**.

### Attention: the local controller did most of the work

| source | fixations |
|---|---:|
| `LOCAL_FSG` (established frozen policy) | **60** |
| `ORACLE_REDIRECT` | 8 |
| `ORACLE_SEED` | 4 |

The oracle supplied one seed per foreground object and eight rescue redirects;
**83% of fixations came from the unchanged local FSG policy**. Also recorded:
**3 renderer precondition refusals** and **4 empty looks** under the inherited
<100-point rule.

### Raw versus oracle-accepted measurement

| object | looks | raw median | accepted median | raw p95 | accepted p95 | rejected |
|---|---:|---:|---:|---:|---:|---:|
| 141 `rc1_cloth` | 19 | 5.22 mm | 5.22 mm | 15.81 mm | 15.81 mm | **0.00%** |
| 142 `rc1_table` | 29 | 33.95 mm | 29.71 mm | **151.86 mm** | **99.83 mm** | **6.60%** |
| 144 `rc1_book_left` | 11 | 31.97 mm | 31.53 mm | 69.52 mm | 64.22 mm | 0.19% |
| 145 `rc1_box_right` | 9 | 15.04 mm | 15.03 mm | 61.88 mm | 61.56 mm | 0.09% |

**The validation gate is essentially only active on the table**, where it cuts
p95 error from 151.9 mm to 99.8 mm. On the cloth it rejects nothing at all: that
object sits near the 2.1 m vergence plane and is well textured. This is a
faithful picture of where stereo is and is not trustworthy on this fixture, and
it matches what REAL-1 measured independently.

### Layers, kept separate and inspectable

| layer | metric geometry from | extent |
|---|---|---|
| **A** stereo foreground | foveated render → stereo → oracle gate → 12 mm fusion | 525,745 surfels, 42,837 px |
| **B** oracle background scaffold | reference soft depth, **not** stereo | 41,453 px, median 3.623 m |
| **C** reference truth | evaluator scene, rendered before control | 2048×1024 |
| **D** demo composite | A where present, else B | per-pixel provenance in `demo_layer.npy` |

`background_surfels_counted_in_foreground: 0`,
`composite_is_autonomous_reconstruction: false`. Comparing
`foreground_rgb_mosaic.png` with `demo_rgb.png` shows the difference directly:
the grey wall is the only thing layer B adds, and the foreground is visibly
sparse and banded while the background is smooth reference texture.

Background soft depth is computed as robust quantiles of the reference range
over every panorama cell whose reference instance is `rc1_wall`: p5/p25/p50/p75/p95
plus median, mean, std, min and max, recorded with the method in
`background_soft_depth.json`. The visualization shell is a constant-range
spherical shell at the median.

### Story

69 timeline frames (`timeline/fix_<step>.png`, left = the fixation, right = the
scene accumulated so far) and `demo.mp4`, 1040×334, 69 frames, 34.5 s. Three
fixations produced no frame because the renderer refused them.

### Code fixes, all in new Demo files

Four defects were found by running, each diagnosed before any change:

1. **Renderer precondition.** Run 1 died on object 142 fixation 49 with the
   established `fsg_render.check_geometry` raising *"Blender truth check FAIL:
   max 5.1974e-07 m; hits 70"*. `max_hit` was far inside the 2e-5 tolerance, so
   the failing clause was `count < 100`: that check samples 121 random pixels
   per eye and needs ≥100 hits. The demo's redirect had chosen a gaze whose
   foveal frame was mostly empty space past the table edge. Fixed demo-side with
   one `_pick_gaze()` rule shared by seeds and redirects that skips candidates
   whose frame contains less than 0.50 scene occupancy — calibrated against
   measurement (the renderer's own ratio is 100/242 = 0.413; every gaze that
   actually rendered measured ≥ 0.847; the refused one ≈ 0.29).
2. **Fuse precondition.** Run 2 died on object 144 fixation 58 with frozen
   `fsg3_surface_map.fuse` raising *"too few object points in patch"*. `fuse()`
   enforces the same 100-point floor as `initialize()`, and that fixation
   accepted 92 points. The inherited Reality-2b empty-look rule already covers
   this; it was being applied only on the initialize path and is now applied on
   both.
3. **No per-fixation ledger was persisted.** Added `fixation_history.json` plus
   `action_source` and fusion counts per fixation.
4. **`demo_report.json`/`.md` were never generated, and `demo.mp4` held 49 of 69
   frames** because the refused fixations leave gaps and ffmpeg's `%03d` pattern
   stops at the first one. Added the report writer; switched to
   `-pattern_type glob`.

**No pre-Demo source was modified: all 347 tracked sources at baseline
`0e09f5b` are byte-identical.** The branch is purely additive.

### Integrity

- `py_compile` clean on all six Demo modules; reference-helper self-test green.
- `[demo-tabletop1-check] SUMMARY passed=9 failed=0`; all five mutations
  (`truthfill hideoracle nobackground unbounded autonomyclaim`) exit 1.
- Runtime comparator `structural_fails: []`, exit 0.
- **56/56 suites green, 331/331 prior negatives firing, none weakened.**
- Every required output in `demo_tabletop1_public.py` is present.
- `main` `15eedee`, `fullscene-calibration-1` `651a6cb`, `fullscene-real-1`
  `0e09f5b` — all unmoved and matching their remotes.

### What this demonstrates

- The **full architecture runs end to end** on the Tabletop fixture: look →
  foveated binocular render → established stereo → validation → 12 mm fusion →
  persistent per-object geometry → attention redirect → scene accumulation, with
  a legible visual story.
- **Metric foreground geometry is stereo throughout**, verified per fixation by
  bitwise subset, array hash and a 100% differ-from-reference check.
- **Foreground and declared background stay separate** in every product and in
  the point totals.
- The **established local FSG policy drove 83% of fixations** with the oracle as
  scaffolding, not as the controller.

### What this does NOT establish

- **No autonomous discovery.** Object identity and masks came from truth.
- **No autonomous gaze policy.** Seeds and 8 rescue redirects came from truth;
  the demo coverage condition is itself measured against reference support.
- **No truth-free measurement validation.** The gate *is* the reference.
- **No controller optimality.** The 32-fixation and 8-redirect limits are
  engineering guardrails; the table hit one at 74.9% coverage.
- **Background geometry was not inferred.** `rc1_wall` is declared, textured and
  soft-depthed from truth. Inferring that decomposition is the future research
  problem, not something shown here.
- **The composite is not a fully autonomous reconstruction** and is labelled so
  in `demo_layer_provenance.json` and the report.
- **Coverage is a demo presentation condition, not a completeness claim**, and
  is measured against reference angular support.
