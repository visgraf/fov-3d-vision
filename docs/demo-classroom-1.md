# Demo-Classroom-1 — Oracle-Attention Concept Demonstration

## Purpose

This is the second concept demonstration after Demo-Tabletop-1. Its goal is to show that the foveated binocular acquisition, established stereo front end, demo measurement validation, 12 mm persistent surface fusion, foreground/background decomposition, and scene export can operate on the realistic Blender Classroom.

It is **not** a controller-generalization experiment.

The live preflight exposed a real repository seam: the FSG6f local controller belongs to the procedural/rectified lineage, whereas Classroom uses the established foveated-warp `.blend` lineage. Rather than redesign a controller inside a demo, Classroom attention is therefore explicitly oracle-driven.

The demo claim is:

> Blender guides where to look and validates measurements; stereo plus persistent fusion builds metric foreground geometry.

## Attention contract

Every Classroom fixation is selected from Blender reference support.

- first fixation for an object: deterministic visible/deep-interior reference support;
- later fixations: deterministic deep/interior **uncovered** reference support after projecting the accumulated stereo map to the reference sphere;
- candidates that violate the established renderer's occupancy/precondition are skipped deterministically;
- no FSG6f action, cyclopean1a probe, or per-object belief.Policy action is used as the Classroom attention controller.

The run and report must say this plainly. `autonomous_controller_tested=false` and `fsg6f_generalization_tested=false` are required.

This choice does not weaken Demo-Tabletop-1, which already demonstrated established local FSG control. The two demos intentionally emphasize different things:

- **Tabletop:** active local control plus reconstruction;
- **Classroom:** realistic-scale foveated perception plus reconstruction.

## Hard geometry boundary

Reference truth may:

- define object/group masks;
- choose gaze targets;
- reject stereo samples whose depth is implausible;
- define the background scaffold and final evaluation products.

Reference truth may **not** insert xyz/depth into metric foreground maps.

Accepted foreground points must be literal rows from the established Classroom stereo output after target-instance and depth-validation filtering. The demo gate remains

`abs(z_stereo - z_ref) <= max(0.10 m, 0.05*z_ref)`.

The 12 mm surface association/fusion rule remains unchanged.

## Scene binding already established by preflight

The live preflight reported:

- `scenes/classroom/classroom_eye.blend`;
- metric scene, 178 renderable meshes;
- fixed `EYE` camera at the manifest pose;
- established `fixation_pairs.PairRenderer` opens/renders the blend;
- established `stereo_field.field_of_pair` produces usable stereo rows;
- stereo xyz conversion to head coordinates is known;
- reference equirectangular RGB/depth/position is viable in the same head convention;
- parent-root hierarchy is a deterministic partition: 178 meshes -> 98 structural entities, 86 reference-visible.

The adapter should re-verify these facts at execution time rather than treating this document as authoritative runtime state.

## Foreground/background decomposition

Use the scene-adaptive rule rather than named Classroom exceptions.

Preferred rule:

1. build the reference panorama and valid occupied depth distribution;
2. compute `d_near = q70` and `d_far = q90`;
3. define a smooth far/background weight over `[d_near,d_far]`;
4. compute each structural entity's visible support and depth/background statistics;
5. explicit foreground entities must have at least `MIN_FOREGROUND_SUPPORT_FRACTION` of occupied reference support and be sufficiently foreground-like under the single deterministic rule;
6. aggregate far/contextual support and visible support not assigned to explicit foreground entities into exactly one `__BACKGROUND__` object.

The ungrouped/non-mesh reference support noted by preflight must not disappear; assign it explicitly to the background aggregate unless a simpler truthful structural treatment is found.

The background may use reference RGB and soft reference-depth statistics plus trivial shell geometry. It is never counted as stereo-reconstructed foreground.

## Foreground object loop

For each planned foreground entity, in deterministic id order:

1. oracle chooses a visible seed gaze;
2. established Classroom foveated binocular pair is rendered;
3. established stereo runs;
4. reference instance/depth filters the target stereo samples;
5. accepted stereo xyz initializes/fuses through the existing 12 mm map;
6. oracle measures remaining target reference support and chooses the next uncovered gaze;
7. repeat until demo target coverage (0.85), no useful oracle support, 24 object fixations, or 256 total fixations.

Use the completed Tabletop demo's inherited empty-look floor, render precondition lesson, fixation ledger, point provenance checks, exports, report, and movie grammar where applicable.

## Required presentation

Keep four products visually and numerically distinct:

A. **STEREO FOREGROUND** — metric observer geometry from accepted stereo only;

B. **BACKGROUND SCAFFOLD** — one oracle/context object with rich texture and soft depth;

C. **REFERENCE TRUTH** — Blender evaluation/guidance products;

D. **DEMO COMPOSITE** — explicitly labelled oracle-assisted, not autonomous.

The timeline/movie should make the story visible:

`oracle gaze -> foveated binocular observation -> stereo -> validation -> fusion -> persistent scene accumulation`.

## What the demo may establish

- the realistic Classroom `.blend` can feed the foveated binocular/stereo pipeline;
- multiple dynamically grouped room entities can be reconstructed into persistent stereo-derived 3-D foreground maps;
- foreground/background layers can coexist with explicit provenance;
- a room-scale composite RGB-D representation and visual acquisition story can be generated.

## What it does not establish

- autonomous discovery;
- autonomous Classroom attention;
- FSG6f generalization to `.blend` mesh scenes;
- truth-free measurement validation;
- autonomous foreground/background decomposition;
- controller optimality;
- complete reconstruction of every mesh component.

The missing generic `.blend` -> FSG-controller bridge remains a real architectural capability gap to address later, not inside this demonstration.

## Results (O3 oracle attention)

**COMPLETE 2026-09-23 on branch `demo-classroom-1`**
(`DEMO_CLASSROOM1_COMPLETE foreground=10/10 fixations=225 attention=oracle
global_guard=False`; comparator `structural_fails: []` exits 0). Record
`previews/demo-classroom1/full-seed2111`, seed 2111, profile `full`, OPTIX,
227 Blender launches, 661 s in Blender.

**Attention here is entirely oracle scaffolding.** Per the O3 ruling every
fixation was chosen from Blender reference support; the local FSG controller
was never invoked. The blocker that prompted the ruling is preserved, not
solved: no `.blend` → FSG6f bridge was built, `cyclopean1a select_probe` was
not relaxed, and `belief.Policy` was not repurposed.

### Revalidated preflight

| fact | value |
|---|---|
| blend | `scenes/classroom/classroom_eye.blend`, 30.6 MB |
| sha256 | `dca66a3257b909ae…` |
| manifest | id `classroom`, tier 3, kind mesh, CC0 |
| Blender / engine / device | 5.2.1 LTS / CYCLES / OPTIX |
| scene | `_mainScene`, unit scale **1.0**, METRIC |
| EYE | exists at **[−0.6, −1.0, 1.2]**, euler [90,0,0], matches manifest; **not** the active camera (`renderCam` is), resolved by `bl_common.find_eye` |
| renderable meshes | 178 |

The established Classroom acquisition (`fixation_pairs.PairRenderer`, foveated
warp, raster 253, 50,269 samples/fixation, 256 spp) and the established stereo
front end (`stereo_field.field_of_pair`) were both exercised live before the
run. Stereo rows convert to head-frame xyz as
`eye_offset_L + dir · (1/rho)`, since `rho` is inverse distance from the left
eye centre. Fusion is the established 12 mm surface map, unchanged.

The reference panorama is read back through its **world Position pass** and
re-binned on the demo's own spherical grid, so no equirect pixel-to-direction
convention is assumed anywhere. That conversion reproduces the manifest's own
checks: nadir range **1.2000 m** against an eye height of 1.2, zenith
**1.6965 m** against the manifest's 1.69665, and `|Z pass − ‖head xyz‖|`
median **1e-07 m**.

### Grouping rule and inventory

Inspected in order: `pass_index` is **unusable** (162 of 178 meshes are 0);
custom properties carry nothing usable; collections **overlap** (171/171/143/
32/2/1 over 178 meshes) so they are not a partition. **Parent roots are a clean
partition** — every mesh has exactly one root by walking `.parent`.

Chosen rule: **parent-root partition, ids 1..N over sorted root names.**
No Classroom object name appears in any Demo source.

- 178 renderable mesh components → **98 structural entities**
- **87 visible** in the reference panorama
- occupied reference cells **2,069,089 of 2,097,152 (98.66%)**
- visible support carrying no grouped mesh id (index 0) is **not dropped**: it
  is aggregated into the single background object

### Scene-adaptive decomposition (measured)

Over occupied reference depth: median **1.888 m**,
**d_near = q70 = 2.374 m**, **d_far = q90 = 4.041 m**, with a smoothstep
background weight `t·t·(3−2t)` across the band. A group becomes an explicit
foreground target when its visible fraction reaches
`MIN_FOREGROUND_SUPPORT_FRACTION = 0.0025` **and** its mean band weight is
below 0.5; everything else, including index-0 support, aggregates into
`__BACKGROUND__`.

**87 groups considered → 10 foreground, 77 background.**

This is a real and reportable property of the rule at room scale: from an eye
inside the room, the large near solid angles belong to the **architecture**
(beams 31.9%, floor 28.3%, walls, corkboard), while each individual desk or
chair is far too small in solid angle to clear 0.0025 and therefore lands in
the background aggregate. The rule was **not** retuned to move furniture into
the foreground.

### Foreground objects

| id | group | fixations | stop | surfels | ref. cells | coverage |
|---:|---|---:|---|---:|---:|---:|
| 2 | `beams` | 24 | `DEMO_OBJECT_GUARDRAIL` | **0** | 659,707 | 0.0000 |
| 10 | `ceilingAirVent.001` | 24 | `DEMO_OBJECT_GUARDRAIL` | 822 | 34,140 | 0.2512 |
| 11 | `ceilingAirVent.002` | 24 | `DEMO_OBJECT_GUARDRAIL` | 2,631 | 8,750 | 0.6977 |
| 33 | `corkboard` | 24 | `DEMO_OBJECT_GUARDRAIL` | 10,101 | 63,196 | 0.7583 |
| 46 | `pipe` | **9** | **`DEMO_TARGET_SATISFIED`** | 5,977 | 23,796 | **0.9048** |
| 48 | `plank` | 24 | `DEMO_OBJECT_GUARDRAIL` | **0** | 16,620 | 0.0000 |
| 52 | `sol` (floor) | 24 | `DEMO_OBJECT_GUARDRAIL` | 10,535 | 584,560 | 0.1893 |
| 66 | `wall` | 24 | `DEMO_OBJECT_GUARDRAIL` | 5,589 | 68,474 | 0.2254 |
| 88 | `woodBase` | 24 | `DEMO_OBJECT_GUARDRAIL` | 5,614 | 129,692 | 0.2077 |
| 89 | `woodBaseboard` | 24 | `DEMO_OBJECT_GUARDRAIL` | 3,861 | 14,317 | 0.6101 |

**One object of ten reached the demo coverage condition.** Eight hit the
24-fixation engineering guardrail, which is not a completion claim.

**Two objects produced zero surfels despite 24 fixations each.** `beams`
accepted 1,427 points over 24 looks and `plank` 1,065 — but spread across
looks, *every single fixation* fell below the inherited 100-point fusion floor,
so nothing was ever fused. These are thin structures seen mostly edge-on: they
yield validated stereo, just never enough in one look. That is the inherited
empty-look rule behaving exactly as designed, and it is reported rather than
weakened.

### Measurement and the hard boundary

Over 225 fixations: **587,483 raw valid stereo rows, 118,433 accepted
(20.16%), 469,050 oracle-rejected (79.84%)** — 370,290 wrong instance
(63.03%), 98,718 depth gate (16.80%), 42 with no reference.

| | raw | accepted |
|---|---:|---:|
| depth error median | **218.34 mm** | **43.62 mm** |
| depth error p95 | **1664.48 mm** | **101.10 mm** |

The gate does far more work here than on the Tabletop, where it rejected only
4.88%. A real room with occlusion, thin structure and long range is simply a
harder scene for this stereo front end, and the demo shows that honestly.

The hard boundary held and was verified per fixation, not asserted:

- accepted set is a **bitwise row-subset** of the stereo array — **225/225**;
- accepted set is a pure boolean filter of it — **225/225**;
- fixations where reference depth supplied a foreground value — **0**;
- **118,433 of 118,433 accepted rows (100.00%)** differ bitwise from the
  reference-derived position along the same direction; that position is
  computed solely to record that it was never adopted.

50 of 225 fixations were empty looks under the inherited <100-point floor.

### Attention

| source | fixations |
|---|---:|
| `ORACLE_SEED` | 10 |
| `ORACLE_UNCOVERED_SUPPORT` | 215 |
| **`LOCAL_FSG`** | **0** |

`oracle_attention_fixation_count` = `fixation_count` = **225**.
`local_fsg_attention_actions` = **0**.

### Layers

| layer | metric geometry from | extent |
|---|---|---|
| **A** stereo foreground | oracle gaze → established Classroom foveated stereo → gate → 12 mm fusion | **45,130 surfels**, 34,695 px |
| **B** background scaffold | reference soft depth, **not** stereo | 465,837 px, 77 groups, median **2.002 m**, 42,349 shell points |
| **C** reference truth | evaluator render before control | 2048×1024 |
| **D** demo composite | A where present, else B | per-pixel provenance in `demo_layer.npy` |

`background_surfels_counted_in_foreground: 0`,
`composite_is_autonomous_reconstruction: false`,
`attention_is_oracle_scaffolding: true`.

Comparing `foreground_rgb_mosaic.png` with `demo_rgb.png` makes the split
directly inspectable: layer A is visibly sparse dotted geometry on the beams,
air vents, corkboard, walls and floor, while every desk, chair, window and the
blackboard come from layer B.

### Outputs

Preflight `scene_preflight.json`, `scene_plan.json`, `oracle_guidance.json`;
foreground `foreground_scene_points.npz/.ply`, `objects/object_<id>.npz/.ply`
(10 each), `foreground_depth.npy`, `foreground_instance.npy`,
`foreground_valid.png`, `foreground_depth_preview.png`,
`foreground_rgb_mosaic.png`; background `background_mask.png`,
`background_rgb.png`, `background_soft_depth.json`, `background_shell.ply`;
composite `demo_rgb.png`, `demo_depth.npy`, `demo_depth_preview.png`,
`demo_instance.npy`, `demo_layer.npy`, `demo_layer_provenance.json`;
reference `reference_rgb.png`, `reference_depth.npy`,
`reference_instance.npy`; story `fixation_history.json`,
`demo_manifest.json`, `demo_report.json`, `demo_report.md`, 225 timeline PNGs
and **`demo.mp4`** (3084×1024, 225 frames, 112.5 s).

### Integrity

- `py_compile` clean on all six Demo-Classroom modules.
- `[demo-classroom1-check] SUMMARY passed=13 failed=0`; **all ten mutations
  exit 1**; unknown exits 2.
- Comparator `structural_fails: []`, exit 0; Demo-Tabletop checker 9/9 and its
  comparator still exit 0.
- **57/57 suites green, 331/331 prior negatives firing, none weakened.**
- **All 353 tracked pre-Classroom sources at `cafad30` are byte-identical.**
  The branch is purely additive.
- `main` `15eedee`, `demo-tabletop-1` `cafad30`, `fullscene-real-1` `0e09f5b`,
  `fullscene-calibration-1` `651a6cb` — all unmoved.

### What this establishes

- The **acquisition/measurement half of the architecture runs end to end in a
  real, cluttered, room-scale Blender scene**: oracle gaze → established
  foveated binocular render → established stereo → validation → 12 mm fusion →
  persistent per-entity geometry, with a 225-frame visual story.
- **Metric foreground geometry is stereo-derived throughout**, verified per
  fixation by bitwise row-subset, array hash and a 100% differ-from-reference
  check.
- A **scene-adaptive foreground/background split** can be computed from
  reference depth quantiles without naming a single object, and the single
  background object supplies context without touching foreground metrics.
- The **structural grouping problem has a clean deterministic answer** in this
  scene: parent roots, 178 components → 98 entities.
- The inherited empty-look floor and gate preconditions **transfer unchanged**
  to a scene the FSG lineage was never built for.

### What this does NOT establish

- **No autonomous discovery or semantic segmentation.** Identity and grouping
  came from the Blender hierarchy.
- **No autonomous gaze policy.** All 225 fixations were oracle-chosen; this
  demo tests nothing about attention. `local_fsg_attention_actions: 0`.
- **No generalization of FSG6f to `.blend` scenes.** The bridge was not built
  and FSG6f was never invoked; the blocker stands.
- **No truth-free measurement validation.** The gate *is* the reference, and
  it rejected 79.84% of raw stereo.
- **No controller optimality.** Eight of ten objects hit an engineering
  guardrail.
- **No autonomous foreground/background decomposition.** The q70/q90 rule reads
  reference depth directly.
- **Background geometry was not inferred.** It is reference RGB over a
  constant-range shell.
- **No complete reconstruction of every Blender mesh component.** 45,130
  surfels over 10 of 98 entities, with two of those at zero, is a
  demonstration — not a reconstruction of the room.
- **The composite is not an autonomous reconstruction** and is labelled so in
  `demo_layer_provenance.json`, the report and the manifest.
