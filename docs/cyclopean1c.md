# Cyclopean-1c — one deep-bay probe

## Question

Cyclopean-1a showed that the cyclopean chart can turn an enclosed sampling hole
into one useful foveation. Cyclopean-1b then showed why internal holes are not
the whole story: seed 2111 contains a large **exterior-connected bay** whose
shoreline is dominantly `UNOBSERVED`, and whose exterior penetration depth is
far larger than ordinary shoreline structure.

Cyclopean-1c asks one deliberately small action question:

> If we foveate **once** at the deepest point of that unresolved bay, does the
> existing stereo/fusion pipeline acquire useful target surface and reduce the
> bay, without changing FSG6f or the stopping policy?

This is not a new controller loop.

## Parent and scope

The only scheduled record is the completed Cyclopean-1b `full` audit for seed
2111. The parent is located by manifest, not by assumed path.

Cyclopean-1b itself is read-only, so Cyclopean-1c follows its `parent_record` to
the completed Cyclopean-1a record, reconstructs the exact inherited chart and
prediction-side evidence, and uses the final Cyclopean-1a `surface_map.npz` as
the map to extend.

Seed 2179 is intentionally not run. Its principal internal hole was already
probed in Cyclopean-1a and is not the question here.

## Bay selection

Reuse the exact Cyclopean-1b semantics and exterior-distance field.

An eligible bay component is an `EXTERIOR` complement component whose shoreline
contains at least one `UNOBSERVED` cell.

If more than one eligible exterior component exists, choose the one whose
`UNOBSERVED` shoreline reaches the greatest inherited border distance. Ties are
resolved by more unobserved shoreline cells, then component id. There is no
threshold saying how deep is deep enough.

Within that selected component, choose a complement cell at the greatest
8-connected shortest-path distance from the padded chart border:

\[
\omega_{probe}=\arg\max_{\omega\in B} d_{border}(\omega).
\]

If several cells share the maximum distance, choose the one nearest the raster
centroid of that maximum-depth plateau. If that exact angular gaze was already
visited, continue deterministically through the same depth ordering until the
first unvisited cell.

This is a one-off geometric readout of the representation, not a new ranking
family.

## Acquisition and fusion

Acquire exactly one binocular fixation with the existing Reality/FSG rendering
path. No parent fixation is rerendered.

The observation uses the same Reality Check 2b empty-look semantics:

- if the fixation contains enough target points under the inherited contract,
  fuse them with the frozen FSG3 12 mm association radius and hash cell;
- if it is empty/nearly empty, retain it as negative evidence and fuse nothing.

Any fused patch must be replay-idempotent and preserve target-map purity.

The before and after shoreline audits are rebuilt on the **same inherited
Cyclopean chart** so the structural change is directly comparable.

## Frozen / forbidden

Frozen: fixed head/static scene, seed 2111 parent acquisition history, FSG1
stereo instrument, FSG3 fusion scale, FSG6f, Reality Check semantics,
Cyclopean-1a chart scale and footprint, Cyclopean-1b boundary semantics.

Forbidden: a second probe, a repeated bay loop, stopping-rule change, FSG6f
ranking modification, evaluator truth, mesh reconstruction, hole filling,
morphology tuning, minimum-arc pruning, normal cue, new depth threshold,
coverage gate or reconstruction-quality PASS threshold.

## What to report

The experiment is observational. Report:

- selected component and deepest-cell gaze;
- whether a revisit fallback was needed;
- target points at the new fixation;
- map point gain and idempotence;
- before/after support, complement, internal/exterior components and maximum
  exterior penetration depth;
- visual reading of the before/after shoreline maps and the probe RGB.

Do not infer success from a tuned numerical threshold. The scientific question
is simply whether one representation-driven bay foveation acquires useful
missing surface and what it does to the spherical structure.

## Results

Run 2026-09-21 on the workstation. **`CYCLOPEAN1C_COMPLETE`,
`structural_fails: []`.** Exactly one new fixation was added, no parent fixation
was rerendered, and the Cyclopean-1b parent is byte-identical afterwards. That is
a structural statement only: **no numerical quality gate exists here and no PASS
is inferred** from target points, map growth or bay reduction.

### Provenance

Working tree clean at `ca9517b`. The prospective package adds **exactly seven
files, all `A`** (`tools/cyclopean1c_{public,bay,probe,compare}.py`,
`tools/dev/check_cyclopean1c.py`, `docs/cyclopean1c.md`,
`docs/cyclopean1c-checks.md`). One cosmetic note, recorded because the log should
match the repository: that commit's *message* reads "Add Cyclopean-1b spherical
shoreline audit", but its *content* is the Cyclopean-1c package. Git is
forward-only here, so the message was left as committed.

`git diff` against the Cyclopean-1b result commit `695dbd9` over **38 frozen
sources** - every FSG1/FSG3/FSG6f source, the renderer, scene, rig, pin file,
every Reality Check 1/2/2b source and **every Cyclopean-1a and Cyclopean-1b
source** - is **empty (0 lines)**, and all 38 sha256 are SAME.

The parent was located **by manifest**: a scan of every
`prediction_manifest.json` found exactly two `Cyclopean1b-boundary-audit-v1`
records and **exactly one** for seed 2111 at `previews/cyclopean1b/full-seed2111`
(`truth_opened` false, `acquisitions_added` 0, `parent_files_modified` false), so
there was nothing to disambiguate. Its three pinned files hash identically
**before and after** the probe:

| file | sha256 (before == after) |
|---|---|
| `prediction_manifest.json` | `fc2c52ed3ad1e736…6bf48671` |
| `boundary_report.json` | `678985846eeee681…ac3b823e` |
| `shoreline.png` | `6544ba1a74c1b9ae…8cd1fdee` |

Ancestry was followed rather than assumed: 1b → **Cyclopean-1a**
`previews/cyclopean1a/full-seed2111` (`added_fixations` 0, no probe taken) →
**Reality Check 2b** `previews/reality2b/full-seed2111` (13 fixations). The
inherited map extended by this step is the Cyclopean-1a `surface_map.npz`,
sha256 `c780d4345e6f74d3…9da1f6e1`, **117,567 surfels** - still that exact hash
after the run, because Cyclopean-1c writes only into its own output directory.

### Environment

Blender 5.2.1 LTS headless, Cycles, **OPTIX** on an RTX 4090 (driver 595.84);
host analysis under `.venv/bin/python` 3.12.3. The whole increment is
**Interactive at 25.6 s wall**, including the single Blender launch.

### Checks

`py_compile` clean on all five modules. The three prescribed positive lines
appeared verbatim:

```text
[cyclopean1c-bay] PASS exterior_deepest=true physical_excluded=true revisit_fallback=true one_probe=true
[cyclopean1c-policy] PASS parent=cyclopean1b seed2111_only=true one_fixation_max=true frozen_fsg6f=true no_mesh=true quality_gated=false
[cyclopean1c-check] SUMMARY passed=6 failed=0
```

All six deliberate negatives exit 1: `internal`, `physical`, `centroid`,
`multiprobe`, `truth`, `policy`. Every prior suite is still green with its
negative set still firing: **cyclopean1b 6/6 (6/6)**, **cyclopean1a 6/6 (6/6)**,
**reality2b 7/7 (10/10)**, **reality1 6/6 (6/6)**, **fsg6f 14/14 (15/15)**.

### The selection, derived before rendering

The inherited chart was rebuilt from the Cyclopean-1a `map_before.npz`:
**263 x 199** cells, grid **0.1 deg**, footprint **4 cells / 0.322236 deg**. The
reconstruction reproduces the saved Cyclopean-1b report exactly - shoreline
**1,514** cells, **1** complement component, **213** arcs, max exterior depth
**209** - so the selector read the same structure 1b published.

**Nothing was hard-coded.** Both the 209-cell depth and the gaze were derived
from the record:

- eligible exterior components with `UNOBSERVED` shoreline: **exactly 1**
  (component 0, 18,116 cells, **1,059** `UNOBSERVED` shoreline cells reaching
  depth **209**);
- deepest complement cell in that component: **(y=109, x=209)** at depth
  **209**, equal to the component maximum; **3** cells tied at that depth, and
  the one nearest their raster centroid was taken;
- gaze **(8.0, 2.1) deg**, inside the parent gaze envelope
  (yaw [-16, 14], pitch [-9, 11]), **not** a revisit of any of the 13 parent
  gazes, so `revisit_fallback_rank` is **0** - the declared fallback was never
  needed;
- new step **`fix_13`**.

### The one probe

One Blender launch, one fixation, **`added_fixations: 1`,
`parent_fixations_rerendered: 0`**. The look returned **52,873 target points** -
far above the inherited Reality Check 2b `<100` limit - so it counted as a target
measurement and was fused:

| quantity | value |
|---|---|
| new surfels | **20,167** |
| matched surfels | **32,706** |
| map points | **117,567 → 137,734** |
| multi-look surfels | 48,350 → **53,412** |
| max support count | 4 → 5 |
| instance ids | **{141}** |
| `idempotent_replay` | **true** |

Re-verified independently of the runner: recomputing the patch from the saved
acquisition and refusing it onto `map_before.npz` reproduces the saved
`surface_map.npz` **bitwise** in xyz, support and provenance; replaying the same
patch onto the result returns `duplicate_patch: true` with **new 0, matched 0**
and the map bitwise unchanged. The observation itself has **53,894 of 65,536**
valid pixels (82.2%) and saw two instances - **{141: 52,873, 143: 1,021}** - with
the 1,021 non-target pixels excluded from the patch, so target purity is
preserved by construction rather than by luck.

### What it did to the spherical structure

Both audits are built on the **same inherited chart**, so the columns are
directly comparable.

| | before | after |
|---|---|---|
| raw support cells | 28,032 | 32,735 |
| support cells | 34,221 | **38,971** |
| complement cells | 18,116 | **13,366** |
| shoreline cells | 1,514 | 1,384 |
| EXTERIOR components | 1 | 1 |
| **INTERNAL components** | **0** | **2** |
| arcs | 213 | 222 |
| max exterior border distance | **209** | **168** |

Shoreline cells by state: `UNOBSERVED` **1,059 → 918**, `AMBIGUOUS` 152 → 152,
`PHYSICAL_DEPTH_BREAK` 303 → 314. Arc counts by state: `UNOBSERVED` 46 → 46,
`AMBIGUOUS` 86 → 92, `PHYSICAL_DEPTH_BREAK` 81 → 84. `TARGET_CONTINUATION`
remains **0**, as in Cyclopean-1b.

The bay itself shrank but **did not close**. Its deepest `UNOBSERVED` arc went
from arc 18 - **615 cells**, centroid (-1.078, +2.015), span 20.5 x 8.9 deg,
depth [5, **209**] - to arc 19 - **454 cells**, centroid (-4.245, +2.372), span
13.9 x 8.7 deg, depth [5, **168**]. The complement depth field moved with it:
median **16 → 9**, p95 **196 → 141**, max **209 → 168**; complement cells deeper
than 100 fell **6,795 → 2,013**, and cells deeper than 168 fell **2,918 → 0**.
These are reported as measurements; **no threshold is attached to any of them.**

**One structural change was not a reduction.** The record gained **two internal
components where it had none**: a **31-cell / 0.3100 deg²** hole at
**(+6.7903, -2.1484)** and a **1-cell / 0.0100 deg²** hole at
**(+7.3000, -2.9000)**, both with entirely `UNOBSERVED` shoreline. Filling the
bay from one viewpoint converted part of what had been open water into enclosed
lakes. That is an honest cost of the action, not a defect, and it is exactly the
kind of structure Cyclopean-1a was built to see.

### The residual hole is an instrument limit, not a sampling gap

The 31-cell residue was traced back into the probe image rather than guessed at.
Its centroid maps to pixel **(228, 111)** of `fix_13`, and that neighbourhood is
**10.4% valid against 82.2% frame-wide**, with local 5x5 luminance std
**0.00117 against a frame median of 0.00992** (8.5x less textured) and mean RGB
**[1.094, 0.263, 0.184]** against the frame's [0.629, 0.504, 0.414]. It is the
saturated, nearly untextured red-orange emblem printed on the cloth, where the
frozen SGBM instrument produces no valid disparity. The same mechanism shows up
frame-wide: invalid pixels have median local texture **0.00356** against
**0.01073** for valid ones.

So what the probe left behind at that spot is **not unsampled territory but a
region the stereo instrument cannot reconstruct**. This run gives no evidence
either way about whether some other viewpoint would fix it, and none was tried.

### The 3D map stays coherent

- The 20,167 new surfels lie **entirely inside the old range envelope** -
  [2.0815, 2.2134] m within [2.0667, 2.2372] m - with **zero** points outside
  it. Nothing landed at table or wall depth.
- Fusing the probe moved the **pre-existing** surfels by median **0.0000 mm**,
  p99 **1.72 mm**, max **5.94 mm**, all well inside the frozen 12 mm radius. The
  new look did not drag the existing surface.
- **32,706 of 52,873** probe points (**61.9%**) associated with existing surfels
  within that 12 mm radius, so where the new look overlapped known surface it
  agreed with it.
- The newly filled patch does sit at the far end of the cloth's depth range - new
  surfel median range **2.1623 m** against the old map's **2.1337 m** - and abuts
  a nearer region, so there is a visible depth step at the seam (median **+22
  mm**, max **41 mm** over the 15 seam cells). The cloth already shows
  panel-to-panel steps of that size across its whole extent and its total relief
  is 170 mm, so this reads as the scene's own fold structure rather than a
  misplaced slab.

One statistic was computed and then **discarded as uninformative**: "new surfels
disagree with old cells by more than 12 mm" is **definitionally forced**, since a
point within 12 mm of an existing surfel would have *matched* instead of becoming
new. It is recorded here only so it is not mistaken for evidence later.

### Aggregate

```text
[cyclopean1c-compare] CYCLOPEAN1C_COMPLETE {"records": [{"internal_components_after": 2, "internal_components_before": 0, "map_point_gain": 20167, "max_exterior_depth_after": 168, "max_exterior_depth_before": 209, "probe_gaze_deg": [8.000000000000002, 2.0999999999999996], "probe_target_points": 52873, "seed": 2111}], "structural_fails": []}
```

### Visual reading, descriptive

`shoreline_before.png` is the Cyclopean-1b picture: a white complement channel
enters from the **left edge**, runs between an upper slab and a lower-left slab,
and opens into a wide rectangular basin in the middle right.

`shoreline_after.png` shows the **basin filled**. What remains is a narrow
L-shaped slot along the left - the former entrance channel, still reaching the
chart border, which is why the record still has exactly one exterior component
and a depth of 168 - plus one small red crescent in the middle right, the 31-cell
internal hole. So the bay became **much smaller and much shallower, stayed
exterior-connected, and fragmented** by shedding two internal lakes.

`probe_rgb.png` explains the yield: the gaze landed on fully textured cloth - the
printed blue band at the left, cream weave, the red-orange emblem near the bottom
- with a narrow strip of a second object at the right edge, which is the 1,021
non-target pixels.

A depth-coloured before/after view of the surfel map itself shows the same event
in 3D: the rectangular void in the cloth is replaced by a coherent textured
patch, at the far end of the cloth's own depth range, carrying a small elliptical
gap where the emblem is.

### Structural FAIL lines, and code fixes

**No structural FAIL line was produced anywhere**, and **no code fix was made**;
no source file was modified.

The inherited `RuntimeWarning: invalid value encountered in cast` from
`cyclopean1a_topology.py:117-118` appears again - **2** occurrences in the
Cyclopean-1c rasterization path - and is recorded again as harmless, proved the
same two ways as in Cyclopean-1b. By inspection, `_indices` builds its `good`
mask with an **explicit** `np.isfinite(yaw) & np.isfinite(pitch)` term, so the
cast's output for a non-finite input is never used. By measurement, rebuilding
the 1c evidence and support with a NaN-prefiltered `_indices` raises **0**
warnings and yields **bitwise identical** `seen_target`, `seen_nontarget`,
`target_range_m`, `nontarget_range_m`, `raw_support`, `support` and target range
raster. The 11,642 non-finite angle pairs at `fix_13` are exactly its 11,642
invalid pixels, all correctly excluded. It changes no Cyclopean-1c number, so the
parent scientific source was correctly left alone.

### What this one probe establishes, and what it does not

Established. **A boundary structure read off the cyclopean chart was enough to
aim one useful fixation.** The deepest cell of the bay - chosen with no
threshold, no tuned score and no FSG6f involvement - returned **52,873 target
points** and **20,167 new surfels**, a **17.2%** growth of a map that
`no_frontier` had already declared finished, with replay idempotence and target
purity intact. **The bay is measurably reduced**: max penetration depth 209 →
168, complement 18,116 → 13,366, cells deeper than 168 down to zero. And **one
probe did not finish the job**: the bay stayed exterior-connected through its
narrow entrance channel, and the action *created* two internal lakes where there
had been none.

Not established. **No stopping rule changed, and none is proposed** - FSG6f is
untouched and was never consulted. **Nothing here says one probe is enough, or
that more probes would converge**; a single action on a single seed cannot show
that, and a second probe was forbidden by construction. **No quality claim is
made**: 20,167 new surfels is a count, not an accuracy statement, and this step
opened no evaluator truth, so the *correctness* of the new surface is unmeasured
here. **The residue is not a gap this method can close** - it is a texture-limited
stereo failure, which means bay depth alone would keep proposing looks at a spot
the instrument cannot resolve. That is the sharpest thing this run says about
using topology to drive stopping, and it is a caution, not a result.
