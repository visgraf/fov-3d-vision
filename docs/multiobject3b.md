# MultiObject-3b — seed the scene-selected fourth object

## Motivation

MultiObject-3a repeated the scene-level next-object decision on the updated saved memory and selected one uninstantiated object by accumulated **valid-depth** support. Existing unfinished objects remained persistent and did not block progress.

MultiObject-3b turns that decision into exactly one action: **one prescribed fixation that instantiates the selected object as a fourth persistent scene entity**.

Small is beautiful: this is still not a growth experiment.

## Parent-selected object

The selected id is consumed from the completed MultiObject-3a parent. It is not declared or hand-picked in this step. The already-instantiated object-id set is likewise consumed from the current scene memory rather than hard-coded.

The current measured parent result selects object 145, but the implementation validates and consumes whatever positive uninstantiated id the parent actually recorded.

## Evidence scope and seed direction

Use exactly the complete saved observation scope that MultiObject-3a used for its decision: the older MultiObject-1b2 scene history plus the MultiObject-2b/2c third-object history.

For the parent-selected id:

1. collect only samples for which the existing stereo front end produced valid depth and the saved oracle instance id equals the selected id;
2. convert their reconstructed head-frame xyz positions to yaw/pitch;
3. quantize directions on the inherited 0.1-degree scene grid;
4. compute the spherical mean of occupied cells;
5. choose the occupied cell nearest that mean, using the unchanged MultiObject-1a seed selector.

Quantizing before the mean prevents repeated pixels or views from winning merely by sample density. Choosing an occupied cell anchors the new fixation in already-supported evidence even when the spherical mean falls on an occluder or another object.

## Acquisition

Add exactly one fixation at

```text
max(MultiObject-3a evidence global steps) + 1
```

using `tools/scene_render_fix.py`.

Do not rerender any saved history.

## Scene representation

Every previously instantiated object remains a separate read-only `SURFEL_MAP` entity. The newly selected object is added as a separate `SEED_SURFEL_PATCH` entity.

The shared cyclopean chart records raw angular footprints for all objects. Pairwise and all-object overlaps are **measurements only**, never integrity failures: later scenes may contain occlusion or shared angular support.

## Scope

There is no object growth, no fusion into an existing object, no revisit of retained unfinished objects, no semantic ranking, no saliency model, no quality threshold and no scene scheduler.

Seed point count and seed-view depth recovery are measurements. They do not alter the rule.

## Next stage

If the seed record is structurally clean, grow the newly seeded fourth object independently while every existing object remains stable.

## Results

Run 2026-09-22 on the workstation. `MULTIOBJECT3B_COMPLETE`, `structural_fails:
[]`, no FAIL line anywhere; the comparator agrees and exits 0.

**Object 145 — the id consumed from MultiObject-3a, never declared here — was
instantiated as a fourth persistent entity by exactly one new fixation at global
step 66**, gaze **(+20.822184, +0.000711)**, yielding a **3,662-point
`SEED_SURFEL_PATCH`, pure `{145}`**. Objects 141, 142 and 143 remained
**byte-identical**, and all six pairwise footprint overlaps plus the all-object
overlap are **0**.

The measured regime is the one MultiObject-3a's diagnostics warned about:
**depth recovery 6.68%** on a near-textureless surface. Recorded as a
measurement; it gated nothing.

### Provenance

Working tree clean at the start. Package commit **`532113f`** adds **exactly the
seven MultiObject-3b files, all `A`**; parent result **`16ccbb9`**.

Frozen audit at full scope, not a curated subset: **every tracked
non-documentation source present at `16ccbb9` — 282 files** across `tools/`,
`tools/dev/` and `scenes/`. `git diff 16ccbb9 HEAD` over that set is **empty (0
lines)** and all **282 sha256 are SAME**. The complete changed-file list between
parent result and HEAD is the seven new 3b files and nothing else. Key frozen
sources: `scene_render_fix.py` `6e70bbb78c1043ec…`, `reality2_render_fix.py`
`9f1433d189fbcbb5…` (present, unchanged, **never invoked**),
`fsg3_surface_map.py` `1b9dbeb873105ec9…`, `fsg6f_frontier.py`
`d636c9405d719916…`, `cyclopean1a_topology.py` `6ed00fca00907f33…`,
`multiobject1a_run.py` `8bf828e42239123c…`, `multiobject2b_run.py`
`4d293a3e14791f5f…`, `multiobject3a_run.py` `4f64b834be7e0041…`,
`multiobject3a_select.py` `ee8fc80971d48a7a…`, `fsg_stereo_supported.py`
`683ae91eaca7b6af…`.

The parent was located **by manifest**, not by assumed path: exactly one
`MultiObject3a-next-object-selection-v1` record —
`previews/multiobject3a/full-seed2111` — with every required invariant:
`selection_status` **`NEXT_OBJECT_SELECTED`**, `truth_opened` **false**,
`acquisitions_added` **0**, `fusion_iterations_added` **0**,
`growth_iterations_added` **0**, `new_object_instantiated` **false**,
`scene_objects_read_only` **true**, `quality_gate_used` /
`revisit_scheduler_used` / `semantic_ranking_used` all **false**,
`structural_fails` **[]**.

### Ids consumed from the live scene record

| quantity | value | where it came from |
|---|---|---|
| `selected_object_id` | **145** | `multiobject3b_run.py:222`, from the 3a manifest |
| `instantiated_object_ids` | **[141, 142, 143]** | `multiobject3b_run.py:221`, from the 3a manifest |
| live scene graph ids | **[141, 142, 143]** | MultiObject-2c `scene_graph.json` |

The runner cross-checks all three: it asserts the live graph ids **equal** the
parent's instantiated set, that the selected id is **positive and not already
instantiated**, and that the 3a manifest and its selection report agree on both
the selected id and its support. **The literal `145` appears zero times in all
four MultiObject-3b sources**; it appears twice only inside
`check_multiobject3b.py`, as the `handpick` mutation string and the assertion
that the string is absent from the real sources.

### Evidence scope, and proof no history was rerendered

**48 looks, global steps 18..65** — exactly the scope MultiObject-3a used. The
runner re-derives the case list and asserts it is **identical** to the parent's
recorded `observation_steps` and `observation_count`; both checks passed.

**No historical rerender, three independent ways:**

- the 3b record's acquisition directory contains **exactly one** entry,
  **`fix_66`**;
- **none** of the 48 evidence steps appears in it;
- `added_fixations` **1**, `parent_fixations_rerendered` **0**, and all **96**
  saved calibration/observation files are byte-identical afterwards.

`global_step` = **max(65) + 1 = 66**, which the comparator re-derives
independently.

### Recomputed selected valid-depth evidence

Recomputed from the raw observations with paths rebuilt by hand from manifest
keys and the aggregation written fresh:

**13,047 valid-depth samples for object 145 over 8 of the 48 steps** — steps
**34 (333), 35 (2,049), 36 (3,726), 37 (3,118), 38 (1,441), 58 (114), 59
(1,228), 60 (1,038)**. This matches MultiObject-3a's
`selected_valid_depth_samples` **13,047** exactly, and the runner's own guard
(`seed evidence does not reproduce MultiObject-3a selected support`) enforces the
same equality before rendering anything.

**Valid depth, not raw visibility, drove the seed**: the mask is
`valid & (instance_id == 145)`, and the `visibleonly` negative — which deletes
the `valid &` term — is detected and exits 1.

### Seed direction

The unchanged MultiObject-1a occupied-cell spherical-mean selector was reused
(`select_prescribed_seed`, in frozen `multiobject1a_seed.py`):

| quantity | value |
|---|---|
| valid-depth evidence points | **13,047** |
| occupied 0.1-degree cells | **2,035** |
| spherical mean of occupied cells | **(+20.636381, +0.041449)** |
| selected occupied cell `[yaw_i, pitch_i]` | **[208, 0]** |
| cell dot-product to mean | **0.9999944891** |
| **prescribed gaze** | **(+20.822184, +0.000711)** |

Quantizing before averaging is what stops a repeatedly-observed sliver winning on
pixel count alone: 13,047 samples collapse to **2,035** cells, and the mean is
taken over cells.

**Independently reproduced to the last digit.** Reimplementing the documented
rule from scratch — per-cell mean sample directions, then the mean of those, then
the nearest cell — gives spherical mean, selected cell, dot product and gaze all
matching the record with **difference 0.000e+00**.

One methodological note worth recording. A first independent attempt used **cell
centres** as each cell's representative instead of the **mean of the samples
inside the cell**; it selected the **same cell [208, 0]** but reported a gaze
2.2e-02 deg away — sub-cell, under a quarter of one 0.1-degree cell. The frozen
selector's docstring is explicit that "the returned gaze is the mean direction of
one actually occupied cell", so the second reimplementation is the faithful one.
**The decision — which cell — is robust to that variation; only the sub-cell
aiming point is not.**

### The one new fixation

One Blender launch through the **generic `tools/scene_render_fix.py`**, OPTIX. The
legacy `reality2_render_fix.py` is byte-identical and **never referenced** by any
3b source; the `legacyrenderer` negative enforces that and fires.

| quantity | value |
|---|---|
| global step | **66** |
| gaze | **(+20.822184, +0.000711)** |
| object-145 visible pixels | **54,784** of 65,536 (**83.6%** of frame) |
| object-145 valid-depth points | **3,662** |
| **depth recovery fraction** | **6.68%** |
| whole-frame valid | **3,690** of 65,536 (**5.6%**) |
| valid points by instance in the seed view | **145: 3,662; 143: 28** |

Object 145 filled **five sixths of the fovea** and returned depth on **one
fifteenth** of it. Nothing else meaningful was measured in the view — the only
other instance with any valid depth was 143, at 28 points.

### Seed patch

`object_145_seed_patch.npz` — **3,662 points**, `instance_id` exactly **{145}**
(`selected_object_patch_pure: true`), all 3,662 xyz finite.

**Range min / median / max = 2.5517 / 2.7645 / 2.8809 m** — a spread of only
**0.33 m** across the whole patch, consistent with a flat surface seen close to
frontally, and more distant than object 141 (2.13 m) though nearer than object
143 (3.51 m).

The patch is a **separate entity**, never fused: `fusion_iterations_added` **0**,
`growth_iterations_added` **0**, `new_object_instantiated` **true**,
`existing_objects_read_only` **true**.

### Pre-existing objects, before and after

**All 103 pinned inputs byte-identical afterwards** — 2 MultiObject-3a files, 2
MultiObject-2c files, 3 object geometry sources, and all **96** saved
calibration/observation files. Verified twice: by my own external pinning, and by
the runner's own four guards.

| object | sha256 before | sha256 after | points | ids |
|---|---|---|---|---|
| 141 | `6ac98f6251b47337…` | `6ac98f6251b47337…` | 155,684 | `{141}` |
| 142 | `6f90d985f8078a7d…` | `6f90d985f8078a7d…` | 310,884 | `{142}` |
| 143 | `bbc4b856a07d2be5…` | `bbc4b856a07d2be5…` | 42,988 | `{143}` |

### Four-object scene and footprints

`object_ids_after` **[141, 142, 143, 145]**. Shared cyclopean chart **624 x 488**,
grid **0.1 deg**, `yaw0` -31.30, `pitch0` -25.70.

| object | geometry | points | raw footprint cells | area |
|---|---|---|---|---|
| 141 | `SURFEL_MAP` (read-only) | 155,684 | 37,654 | 376.54 deg² |
| 142 | `SURFEL_MAP` (read-only) | 310,884 | 62,784 | 627.84 deg² |
| 143 | `SURFEL_MAP` (read-only) | 42,988 | 17,947 | 179.47 deg² |
| **145** | **`SEED_SURFEL_PATCH`** | **3,662** | **1,165** | **11.65 deg²** |

**Overlaps — measurements, never integrity failures:**

| pair | cells |
|---|---|
| 141 ∩ 142, 141 ∩ 143, 141 ∩ 145 | **0, 0, 0** |
| 142 ∩ 143, 142 ∩ 145 | **0, 0** |
| 143 ∩ 145 | **0** |
| all four | **0** |

Object 145 spans yaw **[+16.30, +25.00]**, pitch **[-5.60, +5.70]** — a compact
region to the right of and above object 142's territory, with the seed gaze
inside it. It is the **smallest footprint in the scene**, 11.65 deg² against
142's 627.84. These are **raw occupied cells**, not footprint-dilated support.

### Visual reading, descriptive

`object_145_seed_rgb.png` is the clearest explanation of the 6.68% recovery in
the record: the fovea is **three flat vertical bands** — a broad matte
terracotta-brown field on the left and centre, a narrow pale cream stripe
between them, and a grey band on the right — with **essentially no texture
anywhere**. There is almost nothing for a stereo matcher to correspond, and the
numbers agree.

`scene_cyclopean_footprints.png` is the first **four-object** chart. A pixel
census reproduces the scene graph exactly — 37,654 / 62,784 / 17,947 / 1,165
cells at the four grey levels, **zero pixels at the overlap marker level 255**,
consistent with all overlaps being 0. Object 141's cloth quadrilateral (darkest)
sits at centre with its panel seams and the black emblem ellipse still visible;
object 143's architectural frame surrounds it above and to the sides; object 142
fills the lower half as a broad wood-grain expanse; and **object 145 appears as a
narrow bright vertical double-stripe on the right**, disjoint from all three.

### Structural failures and code fixes

**Structural failures: none.** `structural_fails: []` in both the manifest and
the comparator; no FAIL line was produced anywhere.

**Code fixes: none.** No MultiObject-3b file needed repair and no frozen prior
source was modified. The package ran as applied, first time.

### Checks

`py_compile` clean on all five modules. Seed self-test:

```text
[multiobject3b-seed] PASS parent_selected_object=true updated_valid_depth_only=true occupied_cell_mean=true
```

Normal checker, verbatim:

```text
[multiobject3b-seed] PASS parent_selected=true updated_valid_depth_seed=true one_fixation=true separate_entity=true
[multiobject3b-progress] PASS existing_objects_read_only=true growth=false revisit=false scheduler=false
[multiobject3b-check] SUMMARY passed=6 failed=0
```

All **seven** negatives are genuine source-mutation controls, each exiting **1**
because a real invariant was detected. **None exited 2 — there is no blocker.**

| negative | rc | detected by |
|---|---|---|
| `handpick` | 1 | `parent_selection_and_scene_ids_consumed_not_handpicked` |
| `oldhistoryonly` | 1 | `complete_updated_valid_depth_seed_reuses_rule` |
| `visibleonly` | 1 | `complete_updated_valid_depth_seed_reuses_rule` |
| `multiprobe` | 1 | `one_new_global_fixation` |
| `legacyrenderer` | 1 | `generic_scene_renderer_not_legacy_cap` |
| `crossfuse` | 1 | `existing_objects_read_only_separate_seed` |
| `grow` | 1 | `growth_revisit_and_scheduler_deferred` |

The **exit-2 escape branch was verified live**: an inert mutation on a scratch
copy of the runner was detected by **no** check, exactly the condition under
which the checker prints `ERROR ... mutation escaped detection` and exits 2.

**No regression, and no previous negative was weakened**: **23/23** prior suites
green and **148/148** prior negatives still firing. The **Cyclopean-1f caveat
stands as a standing caveat and 1f was not edited**.

### Environment and wall time

Blender 5.2.1 LTS headless, Cycles, **OPTIX** on an RTX 4090 (driver 595.84);
host `.venv/bin/python` 3.12.3. **16.0 s total** — one Blender launch plus the
48-look evidence replay.

### What this establishes, and what it does not

Established. **A scene-level decision became a fourth persistent entity in one
action.** The id and the instantiated set were both **consumed from the live
scene record** (the literal never appears in any 3b source), the **13,047-sample
support was reproduced independently** before anything was rendered, the seed
direction came from the **unchanged MultiObject-1a rule** and was reproduced **to
the last digit**, and **exactly one** new globally numbered fixation at step 66 —
through the **generic renderer**, with **zero** historical rerenders — produced a
**3,662-point patch pure in `{145}`**. All three pre-existing objects stayed
**byte-identical**, all **103** pinned inputs unchanged, and the four footprints
are **mutually disjoint**. The selection -> seed chain now runs a second time,
from a memory the programme itself built.

Established as a **diagnostic**: MultiObject-3a's caution was warranted. Object
145 recovers **6.68%** of its visible pixels as depth — far from object 142's
58.8-77.3% and much closer to object 143's 1.4-2.5% — and the seed image shows
why: a nearly textureless three-band surface. **This gated nothing**, and it is
exactly the kind of prediction the 3a report declined to make with confidence.

Not established. **Nothing about growth** — 3,662 points from one look is a seed,
not an object; whether 145 grows, stalls at low recovery like 143, or terminates
scientifically is **untested**, and no growth loop ran. **No accuracy claim** —
evaluator truth stayed closed; 3,662 points and a 0.33 m range spread describe
the representation, not the scene. **No object completeness** and **no semantic
importance** — 11.65 deg² is the smallest footprint in the scene and means only
what it says. **Zero overlap remains a property of this configuration, not an
invariant** — it now survives four objects, and the contract still declines to
make it a requirement. **The low recovery is not shown to be irreducible** — no
alternate matcher, baseline, vergence or illumination was tried, by design. And
**no revisit scheduler** — objects 142 and 143 remain retained as unfinished, and
nothing here schedules them.

**Next: grow the newly seeded fourth object independently while every existing
object stays stable.** Stopped after the seed fixation, as instructed.
