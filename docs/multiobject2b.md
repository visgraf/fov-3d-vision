# MultiObject-2b — seed the scene-selected third object

## Motivation

MultiObject-2a performed the first scene-level next-object decision entirely from memory.  It selected one uninstantiated object by accumulated **valid-depth** support while leaving objects 141 and 143 unchanged.

MultiObject-2b turns that decision into action, but introduces only one new thing: **one prescribed fixation that instantiates the selected object as a third persistent entity**.

This is still not a growth experiment.

## Parent-selected object

The selected id is consumed from the completed MultiObject-2a parent.  It is not declared or hand-picked in this source step.  The current measured parent result is expected to select id 142, but the implementation validates and consumes whatever positive uninstantiated id the parent actually recorded.

## Seed-direction rule

Use exactly the saved observation scope that MultiObject-2a used for selection.

For the parent-selected id:

1. collect only samples for which the existing stereo front end produced valid depth and the saved oracle instance id equals the selected id;
2. convert their reconstructed head-frame xyz positions to yaw/pitch;
3. quantize directions on the inherited 0.1-degree scene grid;
4. compute the spherical mean of occupied cells;
5. choose the occupied cell nearest that mean, using the unchanged MultiObject-1a seed selector.

Quantizing before the mean prevents heavily sampled views from winning merely because they contributed more pixels.  Choosing an occupied cell anchors the fixation in already-supported evidence even if the spherical mean itself lies on an occluder or another object.

## Acquisition

Add exactly one fixation at

```text
max(MultiObject-2a evidence global steps) + 1
```

using `tools/scene_render_fix.py`.

Do not rerender any saved history.

## Scene representation

Objects 141 and 143 remain separate read-only `SURFEL_MAP` entities.  The selected object is added as a separate `SEED_SURFEL_PATCH` entity.

The shared cyclopean chart records raw angular footprints for all three objects and reports pairwise/triple overlap as **measurements only**.  Overlap is not a failure: future scene configurations may contain occlusion or shared angular support.

## Scope

There is no object growth, no fusion into an existing object, no revisit of object 143, no automatic scheduler, no semantic ranking and no quality threshold.

A zero or small seed-point count is a measurement, not a reason to silently change the rule.  The experiment asks whether the scene-level selection can be converted into one clean third entity under the current instrument.

## Next stage

If the seed record is structurally clean, grow the newly seeded object independently while keeping objects 141 and 143 stable.

## Results

Run 2026-09-22 on the workstation. **`MULTIOBJECT2B_COMPLETE`,
`structural_fails: []`.** The scene-level selection was converted into a third
persistent entity by **exactly one** new fixation. Objects 141 and 143 are
**byte-identical** afterwards and all 57 pinned inputs unchanged.

**Object 142 instantiated at global step 42 with 38,020 seed points, pure
`{142}`, and zero angular-footprint overlap with either existing object.**

### Provenance

Working tree clean. Prospective commit **`863f91b`**; parent result
**`a31cc77`**. The package adds **exactly the seven expected files, all `A`**.
`git diff` against `a31cc77` over **71 frozen sources** — every FSG1/FSG3/FSG6f
source, scene, rig, pin file, every Reality Check 1/2/2b source, **both
renderers**, every Cyclopean-1a..1g source and every MultiObject-1a/1b/1b2/1c/2a
source — is **empty (0 lines)**, all 71 sha256 SAME. The inherited seed selector
`multiobject1a_seed.py` is unchanged at `a5ad5ea0055c3974…`, the generic
renderer `scene_render_fix.py` at `6e70bbb78c1043ec…`, and the legacy
`reality2_render_fix.py` at `9f1433d189fbcbb5…`.

The parent was located **by manifest** and **all nine required conditions
hold**: schema `MultiObject2a-next-object-selection-v1`, seed 2111,
`truth_opened` false, `acquisitions_added` 0, `growth_iterations_added` 0,
`new_object_instantiated` false, `objects_141_143_read_only` true,
`selection_status = NEXT_OBJECT_SELECTED`, `structural_fails []`. Exactly one
record matched: `previews/multiobject2a/full-seed2111`.

The parent points to the completed MultiObject-1b2 scene history
(`previews/multiobject1b2-r2/full-seed2111`) and its MultiObject-1c audit
ancestry (`previews/multiobject1c/full-seed2111`), both confirmed.

### Read-only integrity

**57 inputs pinned before and re-hashed after — all byte-identical**:

| input | sha256 |
|---|---|
| 2a `prediction_manifest.json` | `66194272c1121475…` |
| 2a `next_object_selection.json` | `31a2de98dc187072…` |
| 1c `prediction_manifest.json` | `3ad6c63e761f0411…` |
| 1c `object_143_epistemic_report.json` | `7d3c7a2a29fa1ac2…` |
| 1b2 `prediction_manifest.json` | `74d5cc0f58a2c590…` |
| 1b2 `scene_graph.json` | `5df35f372460399…` |
| 1b2 `object_143_surface_map.npz` | `bbc4b856a07d2be5…` |
| object-141 source | `6ac98f6251b47337…f71e524a` |
| object-143 source | `bbc4b856a07d2be5…a39f234df` |
| all 24 calibration/observation pairs, steps 18–41 | byte-identical |

Both objects were verified **pure before and after**: **141** 155,684 points ids
`{141}`; **143** 42,988 points ids `{143}`. The manifest records
`object_141_sha256_before == object_141_sha256_after` and likewise for 143,
`existing_objects_read_only: true`, `fusion_iterations_added: 0`,
`growth_iterations_added: 0`, `parent_fixations_rerendered: 0`,
`truth_opened: false`, `quality_gate_used: false`,
`automatic_scene_scheduler: false`.

### Environment and wall time

Blender 5.2.1 LTS headless, Cycles, **OPTIX** on an RTX 4090 (driver 595.84);
host `.venv/bin/python` 3.12.3. **Interactive at 14.3 s**, one Blender launch.

### Checks

`py_compile` clean on all five modules. The seed self-test and the three
prescribed structural lines appeared verbatim:

```text
[multiobject2b-seed] PASS parent_selected_object=true valid_depth_only=true occupied_cell_mean=true
[multiobject2b-seed] PASS parent_selected=true valid_depth_seed=true one_fixation=true separate_entity=true
[multiobject2b-progress] PASS existing_objects_read_only=true growth=false scheduler=false quality_gated=false
[multiobject2b-check] SUMMARY passed=6 failed=0
```

All six negatives are **genuine source-mutation controls**, each exiting **1**
with a distinct detector and **none exiting 2**:

| negative | rc | detected by |
|---|---|---|
| `handpick` | 1 | `parent_selection_consumed_not_handpicked` |
| `visibleonly` | 1 | `prior_valid_depth_seed_reuses_rule` |
| `multiprobe` | 1 | `one_new_global_fixation` |
| `legacyrenderer` | 1 | `generic_scene_renderer_not_legacy_cap` |
| `crossfuse` | 1 | `existing_objects_read_only_separate_seed` |
| `grow` | 1 | `growth_and_scheduler_deferred` |

**No regression**: all 15 prior suites green and **104 prior negatives** still
firing — multiobject2a 6/6, multiobject1c 6/6, multiobject1b2 7/7,
multiobject1b 6/6, multiobject1a 6/6, cyclopean1g/1f/1e/1d/1c/1b/1a 6/6 each,
reality2b 7/7 (10/10), reality1 6/6, fsg6f 14/14 (15/15).

### Parent selection reproduced, not assumed

The selected id was **consumed from the parent**, not declared here
(`selection_consumed_from_parent: true`; the runner reads
`pm["selected_object_id"]`). The implementation then **reproduced the parent's
measurement independently**: collecting saved valid-depth samples for that id
over the same 24-observation scope gives **151,133** evidence points, exactly
matching the parent's `selected_valid_depth_samples`, with the same per-step
contributions:

| global step | valid-depth samples |
|---|---|
| 18 | 15,513 |
| 38 | 19,555 |
| 39 | 41,752 |
| 40 | 38,724 |
| 41 | 35,589 |
| **total** | **151,133** |

Only **5** of the 24 observations contributed; the other 19 carry no valid-depth
id-142 evidence.

### Seed direction

Derived with the **unchanged MultiObject-1a occupied-cell spherical-mean
selector** on the 0.1-degree scene grid:

| quantity | value |
|---|---|
| valid-depth evidence points | **151,133** |
| occupied 0.1-deg cells | **22,035** |
| spherical mean | **(+13.97836249, −13.80151185) deg** |
| selected occupied cell | **[140, −138]** |
| dot-to-mean | **0.9999999218539822** |
| **prescribed gaze** | **(+13.99956999, −13.81094221) deg** |

Worth noting against the earlier case: for object 143 in MultiObject-1a the
spherical mean fell **7.392 deg** from the nearest occupied cell
(dot 0.991690), because that object's evidence wrapped around an occluder. Here
the dot is **0.99999992** — a separation of about **0.023 deg** — so object 142's
valid-depth evidence is angularly compact and the mean direction already lies
essentially inside its own occupied set. The occupied-cell rule was therefore
barely exercised on this object, whereas it was load-bearing on 143.

### The one fixation

`global_step: 42` = `max(evidence steps) + 1` = 41 + 1, continuing global
chronology. `added_fixations: 1`, `parent_fixations_rerendered: 0`,
`renderer_entrypoint: tools/scene_render_fix.py`. No reference to
`reality2_render_fix.py` appears anywhere in the MultiObject-2b sources.

New view `fix_42`, **65,536** pixels, **40,515** valid — a frame-wide valid
stereo rate of **61.8%**. Per positive instance id:

| id | visible | valid depth | recovered |
|---|---|---|---|
| 141 | 403 | 141 | 35.0% |
| **142** | **56,083** | **38,020** | **67.8%** |
| 143 | 9,050 | 2,354 | 26.0% |

Object 142 fills **86%** of the frame and recovers **67.8%** of it — in the same
class as object 141's textured cloth and far above object 143's 1.4–2.5%.

### The seed patch

| quantity | value |
|---|---|
| seed points | **38,020** |
| instance ids | **{142}** — pure |
| range min / median / max | **1.6754 / 2.2982 / 4.0324 m** |

Verified independently of the runner: recomputing `valid & (instance_id == 142)`
over the saved observation gives **38,020** points, matching the patch exactly,
with ids exactly `{142}`.

### Three-object scene representation

| object | geometry | points | read-only |
|---|---|---|---|
| 141 | `SURFEL_MAP` | 155,684 | true |
| 143 | `SURFEL_MAP` | 42,988 | true |
| **142** | **`SEED_SURFEL_PATCH`** | **38,020** | false |

Shared cyclopean chart **602 × 437**, grid **0.1 deg**, `yaw0 −31.30`,
`pitch0 −20.60`:

| object | cells | area | yaw extent | pitch extent |
|---|---|---|---|---|
| 141 | 37,654 | 376.54 deg² | [−12.40, +12.70] | [−8.30, +10.40] |
| 143 | 17,947 | 179.47 deg² | [−30.70, +28.20] | [−9.80, +22.50] |
| **142** | **9,624** | **96.24 deg²** | **[+8.20, +20.10]** | **[−20.00, −9.60]** |

**Overlap — measurements, not gates:**

| pair | overlapping cells |
|---|---|
| 141 ∩ 142 | **0** |
| 141 ∩ 143 | **0** |
| 142 ∩ 143 | **0** |
| all three | **0** |

Confirmed in the image as well: the PNG codes 141 at intensity 70, 142 at 140
and 143 at 210, and **no pixel carries a blended overlap value**. Zero overlap
is recorded as what happened in this configuration, not as a property the
representation requires — the contract explicitly allows occlusion and shared
angular support in future scenes.

### Visual reading, descriptive

`object_142_seed_rgb.png` shows the fovea filled almost entirely by a **brown
wood-grain surface** — the table or floor — with a thin grey band and a sliver of
cream cloth at the very top. The grain carries genuine swirling texture, which
is consistent with the 67.8% depth recovery.

`scene_cyclopean_footprints.png` is the first **three-object** picture in the
series. Object 141's cloth quadrilateral sits in the centre in the darkest grey,
its panel seams and the black emblem ellipse — the residue Cyclopean-1g could not
measure — still visible. Object 143's architectural frame surrounds it, marbled
band above and vertical bands at both sides. Object 142 appears as a new medium
grey block **below and to the right**, showing streaky wood-grain structure. The
three occupy visibly disjoint angular territory.

### Structural failures and code fixes

**No structural FAIL line**: `structural_fails: []` in both the manifest and the
comparator, `parent_fixations_rerendered: 0`, `fusion_iterations_added: 0`,
`growth_iterations_added: 0`, all 57 pinned inputs byte-identical, objects 141
and 143 unchanged and pure, seed patch pure, no evaluator truth opened.

**Code fixes: none.** No file was modified by this run.

### What this establishes, and what it does not

Established. **The scene-level decision became a scene-level action, cleanly.**
The id was consumed from MultiObject-2a rather than declared, its 151,133-sample
valid-depth support was **reproduced independently** from the saved
observations, the gaze was derived by the **unchanged** MultiObject-1a selector,
and **exactly one** fixation at global step **42** — through the generic
renderer, with **zero** historical rerenders — instantiated object 142 as a
**third separate entity** of 38,020 points, pure `{142}`. **Objects 141 and 143
are byte-identical**, and the three footprints are **mutually disjoint** on the
shared chart. The scene now carries three persistent objects with no
cross-object contamination.

Also worth recording: **the selection picked a well-measurable object.** Object
142 recovered **67.8%** of its visible pixels in the seed view, against object
143's 1.4–2.5% in comparable looks — consistent with MultiObject-2a's valid-depth
support ordering, though one look is not a demonstration that the ordering
predicts measurability in general.

Not established. **No object completeness** — object 142 has one seed patch from
one look and nothing more. **No growth or termination** — no growth loop ran, and
whether the frozen grower will extend 142 to `no_frontier` or hit a watchdog is
untested. **No accuracy claim** — evaluator truth stayed closed, so 38,020 points
and the range span describe the representation, not the scene. **No semantic
importance** — 142 was chosen for accumulated valid-depth support, nothing more.
**No general rule about footprint overlap or occlusion** — all three overlaps
happen to be zero in this configuration, and the contract deliberately declines
to make that an invariant. **No automatic scheduling** beyond the single
already-completed 2a selection: `automatic_scene_scheduler: false`. And **object
143 remains retained for revisit** under MultiObject-1c's disposition.

**Next stage**: grow the newly seeded object 142 independently while keeping
objects 141 and 143 stable.
