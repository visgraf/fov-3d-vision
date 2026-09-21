# MultiObject-1a — Second Object Seed

## Purpose

Cyclopean-1g closes the current single-object branch for object 141.  The next step introduces exactly one new difficulty: **two foreground object entities in one fixed-head scene representation**.

Object 141 is inherited read-only from the completed Cyclopean-1g record.  Object 143 is declared in advance as the second object and receives exactly one new seed foveation.  No object-growth loop or automatic scene scheduler is introduced.

## Scientific question

> Can the completed object-141 representation coexist with a newly seeded object-143 entity in the same cyclopean scene record without cross-object contamination?

## Seed selection

This is not automatic object discovery.  Object id 143 is fixed by the experiment.  Its seed direction is determined only from object-143 samples that already appeared incidentally in completed prediction-side observations:

1. recompute completed saved stereo observations;
2. collect valid head-frame samples labelled 143;
3. quantize their directions on the inherited 0.1-degree full-profile grid;
4. take the spherical mean of occupied cells;
5. choose the occupied cell nearest that mean;
6. foveate exactly once there.

This gives object 143 a deterministic prescribed seed while avoiding scene/evaluator truth.

## Representation

The output scene contains two separate foreground entities:

- **141** — the inherited persistent surfel map, untouched;
- **143** — the new seed surfel patch from one fixation.

Both are registered on a shared 0.1-degree cyclopean chart for a first multi-object footprint visualization.  They are not merged into one surfel map.

## Deliberately not included

- no growth of object 143;
- no automatic search for a next object;
- no multi-object scheduler;
- no mesh or semantic relation inference;
- no evaluator truth;
- no quality threshold.

If this structural coexistence works, the next step can ask whether object 143 can be grown independently while object 141 remains stable.

## Results

Run 2026-09-21 on the workstation. **`MULTIOBJECT1A_COMPLETE`,
`structural_fails: []`.** Object 141 was inherited read-only and is
byte-identical afterwards; object 143 received exactly one prescribed seed
foveation. Structural only: **no target-point count, footprint size, overlap
figure or coverage number is a PASS gate.**

### Provenance

Working tree clean. Prospective commit **`1db6b9a`**; pre-package parent
**`aa5ac98`**. The package adds **exactly the seven expected files, all `A`**
(`tools/multiobject1a_{public,seed,run,compare}.py`,
`tools/dev/check_multiobject1a.py`, `docs/multiobject1a.md`,
`docs/multiobject1a-checks.md`). `git diff` against `aa5ac98` over **64 frozen
sources** - every FSG1/FSG3/FSG6f source, renderer, scene, rig, pin file, every
Reality Check 1/2/2b source and **every Cyclopean-1a through 1g source** - is
**empty (0 lines)**, and all 64 sha256 are SAME.

The parent was located **by manifest**, requiring
`schema == Cyclopean1g-recentered-measurement-v1`, `seed == 2111`,
`profile == full` and `truth_opened == false`: exactly one record matched,
`previews/cyclopean1g/full-seed2111`. Its two pinned files hash identically
**before and after**:

| file | sha256 (before == after) |
|---|---|
| `prediction_manifest.json` | `8d4c7b4de820221f…ef92000a` |
| `surface_map.npz` | `6ac98f6251b47337…f71e524a` |

### Environment

Blender 5.2.1 LTS headless, Cycles, **OPTIX** on an RTX 4090 (driver 595.84);
host analysis under `.venv/bin/python` 3.12.3. **Interactive at 11.9 s wall**,
including the single Blender launch.

### Checks

`py_compile` clean on all five modules. The three prescribed lines appeared
verbatim:

```text
[multiobject1a-scene] PASS object141_inherited=true object143_seeded=true separate_entities=true shared_cyclopean_chart=true
[multiobject1a-policy] PASS parent=cyclopean1g one_fixation_max=true prior_evidence_seed=true object_growth=false auto_discovery=false quality_gated=false
[multiobject1a-check] SUMMARY passed=6 failed=0
```

All six negatives are **genuine source-mutation controls**, each exiting **1**
because its mutation was actually detected, and each naming its detector. **None
exited 2**, so no mutation escaped:

| negative | rc | detected by |
|---|---|---|
| `sameid` | 1 | `two_declared_objects` |
| `multiprobe` | 1 | `one_second_object_seed` |
| `merge` | 1 | `separate_geometry` |
| `truth` | 1 | `no_truth_or_discovery` |
| `autodiscover` | 1 | `no_truth_or_discovery` |
| `grow` | 1 | `growth_deferred` |

Every prior suite is green with its negative set still firing, **73 prior
negatives, none weakened**: cyclopean1g 6/6 (6/6), cyclopean1f 6/6 (6/6),
cyclopean1e 6/6 (6/6), cyclopean1d 6/6 (6/6), cyclopean1c 6/6 (6/6),
cyclopean1b 6/6 (6/6), cyclopean1a 6/6 (6/6), reality2b 7/7 (10/10),
reality1 6/6 (6/6), fsg6f 14/14 (15/15).

### Prior id-143 evidence, and the derived seed

The seed direction was taken **only** from id-143 samples that already appeared
incidentally in completed prediction-side observations. Every one of the **18**
completed fixations in the Cyclopean-1g ancestry carried some:

| step | id-143 valid points | record |
|---|---|---|
| 0-5 | 6,608 / 6,934 / 3,567 / 4,526 / 6,879 / 3,444 | `reality1/full-seed2111` |
| 6-12 | 1,854 / 784 / 695 / 670 / 756 / 757 / 988 | `reality2b/full-seed2111` |
| 13 | 1,021 | `cyclopean1c/full-seed2111` |
| 14 | 2,710 | `cyclopean1e/full-seed2111` |
| 15-16 | 39 / 78 | `cyclopean1f/full-seed2111` |
| 17 | 1,285 | `cyclopean1g/full-seed2111` |
| **total** | **43,595** | |

Those 43,595 samples quantize to **11,688** occupied 0.1-degree cells, whose
spherical mean direction is **(+2.4011, -0.6031) deg**. The occupied cell
nearest that mean is quantized cell **[15, -79]**, giving the prescribed seed
gaze **(+1.502902, -7.940374) deg** at dot-to-mean **0.991690**.

**That cell is 7.392 degrees away from the mean, and the reason is worth
recording.** The mean direction of object 143's own evidence falls **inside
object 141's footprint and outside object 143's** - measured directly on the
shared chart. Object 143's evidence wraps around and below the cloth rather than
centring on it, so its angular centroid lands on the occluding object. The
declared rule - *nearest occupied cell*, not the raw mean - therefore did exactly
what it exists for: it anchored the seed in a direction that actually carries
id-143 evidence instead of aiming at the cloth. **Nothing was hand-picked or
retuned after looking at the scene.**

### The one seed fixation

One Blender launch through the unchanged `reality2_render_fix.py` path,
`fix_18`. **`added_fixations: 1`, `parent_fixations_rerendered: 0`.**

The 256x256 observation is **48,820 of 65,536** valid (**74.5%**) and contains
**three** instances among valid pixels - **141: 27,963, 142: 15,513, 143:
5,344**. Object 143 contributed the **5,344** target points that became the seed
patch.

### The two entities

| | object 141 | object 143 |
|---|---|---|
| role | inherited read-only | new seed |
| geometry | `SURFEL_MAP` | `SEED_SURFEL_PATCH` |
| source | the Cyclopean-1g `surface_map.npz` | `object_143_seed_patch.npz` |
| points | **155,684** | **5,344** |
| instance ids present | **{141}** | **{143}** |
| pure | **true** | **true** |
| range m, min / med / max | 2.0659 / 2.1372 / 2.2372 | 1.8998 / 2.1684 / 3.6143 |

Verified independently of the runner: the inherited map still carries exactly
**{141}** and its file hash is unchanged; the seed patch carries exactly
**{143}**; and **the intersection of the two id sets is empty**. They live in
separate files as separate entities and were never fused. Object 143's median
range is **31.2 mm** farther than object 141's and its maximum reaches
**3.6143 m**, consistent with a surface receding behind and below the cloth.

### Shared cyclopean chart

Both entities were registered as raw angular footprints on one shared
0.1-degree chart, **263 x 215** cells at `yaw0 = -12.9`, `pitch0 = -10.4`:

| | cells | area |
|---|---|---|
| object 141 | **37,654** | 376.54 deg² |
| object 143 | **1,641** | 16.41 deg² |
| **overlap** | **0** | **0 deg²** |

Footprint extents: 141 spans yaw **[-12.40, +12.70]**, pitch **[-8.30, +10.40]**;
143 spans yaw **[-5.30, +6.80]**, pitch **[-9.80, -7.00]**.

**The zero overlap was checked rather than assumed**, because the two bounding
boxes *do* intersect in pitch. Over the **14** shared pitch rows
(**-8.30 to -7.00 deg**) object 141 holds **1,189** cells and object 143 holds
**447**, and **not one cell is claimed by both**: in every shared row the two are
disjoint in yaw, separated by a minimum gap of **19 to 45 cells (1.9 to 4.5
deg)**. The footprints **abut on the shared chart without interpenetrating**.

### Visual reading, descriptive

`second_object_seed_rgb.png` shows the cloth filling the upper portion - cream
weave with the printed blue band and a sliver of the red emblem at the top right
- a light grey band running diagonally across the middle, and brown wood across
the bottom. Read against the saved instance mask rather than by eye: the **grey
middle band is object 143**, the cloth above is **141**, and the brown wood below
is a **third object, id 142**.

**The seed is visually centred on object 143.** The exact centre pixel (128, 128)
is instance **143**; the central 32x32 window is **67.6%** id-143 against 32.4%
id-141, and rows 128-159 are **96.1%** id-143. **Object 141 does appear in the
seed view**, occupying **31,144** pixels (47.5% of the frame, 27,963 of them
valid) in the upper region. Of the **12,649** id-143 pixels visible, **5,344**
(**42.2%**) carried valid stereo depth - the band is bright along its textured
upper edge and patchy through its smoother middle.

`scene_cyclopean_footprints.png` is the first two-object picture in this series:
object 141's large quadrilateral in mid-grey, with its panel seams and the black
emblem ellipse that Cyclopean-1g left unmeasured, and object 143's thin, sparse
bright band below it. The image uses its brightest level only for cells claimed
by both objects, and **no such pixel exists** - zero overlap, confirmed visually
as well as numerically.

### A third object is present and was deliberately not instantiated

The seed view contains **15,513 valid pixels of object 142**, more than object
143's 5,344. It was **not** turned into an entity, because the contract declares
exactly two object ids in advance and defers automatic next-object discovery.
This is the contract working as intended rather than an omission, and it is
recorded here so the deferral is visible in the measurements rather than only in
the prose.

### Structural FAIL lines

**None.** `structural_fails: []` in both the manifest and the comparator.

### Code fixes

**One, in a new MultiObject-1a file only, after diagnosis.**

`tools/multiobject1a_run.py:42` read the Cyclopean-1g diagnostic label as
`m.get("measurement_outcome")` at the manifest top level, but Cyclopean-1g
records it **only inside `probe_result`** - there is no top-level copy, and
Cyclopean-1g's own comparator correctly reads it as
`pr.get("measurement_outcome")`. The top-level lookup therefore returned `None`
for **any** valid Cyclopean-1g record, and parent validation aborted before the
run with "Cyclopean-1g did not complete its declared one-look diagnostic". The
fix reads the field where it is written, matching the parent's own reader.

**The check was corrected, not weakened**, and that was verified: with the fix in
place the guard still **rejects** a parent whose `measurement_outcome` is
removed, set to a bogus label, or whose `probe_result` is absent entirely, and
still rejects a flipped `truth_opened` or a changed seed, while **accepting** the
real record. No frozen source and no scientific parameter was touched.

### What this establishes, and what it does not

Established. **Two foreground object entities coexist in one fixed-head scene
record without cross-object contamination.** Object 141 was inherited read-only
and is byte-identical afterwards, still exactly **{141}** and 155,684 points;
object 143 was seeded from one prescribed fixation into a separate
`SEED_SURFEL_PATCH` of 5,344 points, exactly **{143}**; the two id sets do not
intersect, the two geometries are separate files, and on the shared 0.1-degree
chart their footprints have **zero** overlapping cells even where their bounding
boxes cross. **The seed came only from already-acquired evidence** - 43,595
incidental id-143 samples across all 18 completed fixations - by a deterministic
rule, with no hand-picking and no post-hoc tuning.

Not established. **This is coexistence, not multi-object reconstruction.**
Object 143 has **one** seed patch from **one** look and was not grown; 42.2% of
its visible pixels yielded depth and the rest did not, which is recorded and not
addressed. **No scheduler, no automatic discovery, no growth loop** was
introduced, and the third object visible in the very same frame (id 142, 15,513
valid pixels) was deliberately left uninstantiated. **No accuracy claim is made**:
evaluator truth stayed closed, so point counts, footprint areas and the zero
overlap are structural facts about the representation, not statements about the
scene's true geometry. And **zero footprint overlap is a property of this
configuration**, not a demonstrated invariant - these two objects happen to be
angularly disjoint from this fixed head, and nothing here shows what the
representation would do if they were not.

**Next stage**, as declared: grow object 143 independently while object 141
remains stable. Automatic next-object discovery remains deferred.
