# Cyclopean-1b — spherical shoreline audit

## Question

Cyclopean-1a established that the cyclopean chart can distinguish an enclosed
sampling hole from the exterior and can turn one genuine internal hole into one
useful foveation.  It also corrected the visual interpretation of seed 2111:
the conspicuous missing region is not a lake but a **bay**, connected to the
exterior through a left-side channel.

Cyclopean-1b asks the next smaller question:

> Can the same fixed-head cyclopean domain describe the *shoreline* of the
> sampled object, distinguish internal from exterior-connected complement, and
> say which boundary arcs are observed physical depth breaks versus continuation,
> unobserved, or ambiguous — without taking another fixation?

This is an audit, not a controller extension.

## Representation

The metric surfel map remains authoritative.  Cyclopean-1b reuses the exact
Cyclopean-1a angular chart: D9's `2*s0` grid and the support footprint derived
from the frozen FSG3 12 mm association radius.  No new geometric tolerance is
introduced.

A **shoreline cell** is a complement cell that is 8-adjacent to current target
support.  Every shoreline cell retains the identity of the complement component
it belongs to:

- `INTERNAL`: the component does not touch the padded chart border;
- `EXTERIOR`: the component does touch the padded chart border.

Border-touching therefore means only *topologically exterior*.  It does **not**
mean that the object has been observed to end there.

## Boundary semantics

Existing completed prediction-side observations are projected into the same
chart.  Each shoreline cell is labelled:

- `UNOBSERVED`: neither target nor non-target evidence was acquired there;
- `TARGET_CONTINUATION`: target-only evidence exists there;
- `PHYSICAL_DEPTH_BREAK`: non-target-only evidence exists and its range differs
  from the nearby target boundary by more than the already-frozen 12 mm FSG3
  association radius;
- `AMBIGUOUS`: all other observed cases.

Adjacent cells with the same state and complement-component identity form a
boundary arc.  No minimum arc length, smoothing rule or tuned morphology is
introduced.

For exterior complement only, the audit also reports the 8-connected shortest
path distance, in complement cells, from the padded chart border.  This is a
purely descriptive **exterior penetration depth**.  A deep bay can therefore be
reported without inventing a threshold that declares it important.

## Experiment

Inputs are the two completed **Cyclopean-1a full records**, seeds 2111 and 2179,
after the one-probe experiment.  They are located by manifest, not by assumed
path.

For each record:

1. load `map_before.npz` to reconstruct the exact Cyclopean-1a chart;
2. load the final `surface_map.npz` as current target geometry;
3. rebuild prediction-side evidence from the Reality Check 2b ancestry and, when
   present, the single Cyclopean-1a probe;
4. rasterize the final target support on the inherited chart;
5. enumerate internal/exterior complement components and their shoreline;
6. classify shoreline cells and connected same-state arcs;
7. report exterior penetration depth and write one diagnostic image.

There is **no Blender invocation, no new fixation, no map fusion and no stopping
rule** in Cyclopean-1b.

## Contract

Frozen:

- fixed head and static scene;
- all Reality Check 2b and Cyclopean-1a acquisitions and maps;
- FSG1 stereo instrument;
- FSG3 12 mm association scale;
- FSG6f;
- Cyclopean-1a grid and support footprint.

Forbidden: evaluator truth, mesh reconstruction, hole filling, boundary
smoothing/tuning, a minimum-arc filter, a new ranking policy, a probe selection,
new acquisition, completeness percentage, or numerical quality PASS threshold.

Structural completion means only that both parents are audited read-only and the
reported artifacts satisfy provenance/integrity checks.  The scientific outputs
are descriptive.

## Results

Run 2026-09-21 on the workstation. **`CYCLOPEAN1B_COMPLETE`,
`structural_fails: []`.** Both Cyclopean-1a records were audited **read only** and
both parents are byte-identical afterwards. That is a structural statement only:
**there is no numerical quality gate here and no PASS is inferred** from arc
counts, shoreline length or penetration depth.

### Provenance

Working tree clean at `5e01401`. The prospective package adds **exactly seven
files, all `A`** (`tools/cyclopean1b_{public,boundary,audit,compare}.py`,
`tools/dev/check_cyclopean1b.py`, `docs/cyclopean1b.md`,
`docs/cyclopean1b-checks.md`). `git diff` against the Cyclopean-1a result commit
`f7f3b05` over **33 frozen sources** - every FSG1/FSG3/FSG6f source, the
renderer, scene, rig, pin file, every Reality Check 1/2/2b source and **every
Cyclopean-1a source** - is **empty (0 lines)**, and all 33 sha256 are SAME.

Both parents were located **by manifest**, not by assumed path: a scan of every
`prediction_manifest.json` under `previews/` found **exactly two**
`Cyclopean1a-probe-v1` records, exactly one `full` per seed, so there was nothing
to disambiguate. Both carry `public_spec_sha256`
`76c32103a04e500eb81d35ff69514a5fef6a6483bbce3870282fc8a713da44a1`,
`truth_opened` false, `fixed_head`/`static_scene` true,
`parent_fixations_rerendered` 0, and `added_fixations` 0 and 1.

The three pinned files per parent hash identically **before and after** both
audits:

| seed | `prediction_manifest.json` | `map_before.npz` | `surface_map.npz` |
|---|---|---|---|
| 2111 | `aed7700ecfe0de3a...a24b52f4` | `c780d4345e6f74d3...9da1f6e1` | `c780d4345e6f74d3...9da1f6e1` |
| 2179 | `d87ae3efa0762dca...a126fcb3` | `1db5c6a87b9dd1f6...efccb24a` | `1604fce3c7b527cb...c851c18e` |

Seed 2111's `map_before.npz` and `surface_map.npz` carry the **same** sha256,
which independently reconfirms the Cyclopean-1a finding that no probe was taken
and that map was left bitwise unchanged.

### Environment, and that nothing was acquired

Host `.venv/bin/python` 3.12.3 only. **No Blender process ran**: the Cyclopean-1b
sources contain no reference to `subprocess`, `blender`, `bpy` or a render fix,
`pgrep blender` found nothing, and each audit is Interactive - **2.3 s** and
**2.9 s** wall. No `acquisition/` directory, `.ply` or `render.log` exists
anywhere under `previews/cyclopean1b/`; each output is exactly
`boundary_report.json`, `prediction_manifest.json`, `shoreline.png`.

### Checks

`py_compile` clean on all five modules. The three prescribed positive lines
appeared verbatim:

```text
[cyclopean1b-boundary] PASS exterior_bay=true internal_distinct=true continuation=true physical_depth_break=true
[cyclopean1b-policy] PASS parent=cyclopean1a read_only=true acquisition=false boundary_arcs=true no_mesh=true quality_gated=false
[cyclopean1b-check] SUMMARY passed=6 failed=0
```

All six deliberate negatives exit 1: `holeonly`, `exteriorresolved`,
`depthblind`, `truth`, `mesh`, `acquire`. Every prior suite is still green with
its negative set still firing: **cyclopean1a 6/6 (6/6 negatives)**, **reality2b
7/7 (10/10)**, **reality1 6/6 (6/6)**, **fsg6f 14/14 (15/15)**.

### The chart, inherited unchanged

Both audits rebuild the Cyclopean-1a chart from `map_before.npz` and assert the
reconstruction matches the parent manifest. Grid **0.1 deg** (D9's `2*s0` at
full), footprint **4 cells** from the frozen FSG3 12 mm radius - **0.322236 deg**
(2111) and **0.322291 deg** (2179). **No new geometric tolerance was introduced
and no raster rule was touched.**

### Seed 2111 - the bay is one deep unobserved arc

| quantity | value |
|---|---|
| chart | 263 x 199 cells |
| map points | 117,567 |
| raw support / support / complement | 28,032 / 34,221 / 18,116 |
| shoreline cells | 1,514 |
| complement components | **1 EXTERIOR, 0 INTERNAL** |
| arcs | **213**, all EXTERIOR |

Arcs by state: **UNOBSERVED 46, TARGET_CONTINUATION 0, PHYSICAL_DEPTH_BREAK 81,
AMBIGUOUS 86.** By shoreline cell: UNOBSERVED **1,059**, PHYSICAL_DEPTH_BREAK
**303**, AMBIGUOUS **152** (sum 1,514).

**The bay is arc 18**: a single connected `UNOBSERVED` arc of **615 cells** -
**40.6%** of the entire shoreline - centroid **(-1.078, +2.015)**, spanning
**20.5 deg x 8.9 deg**, with `seen_target_cells` 0 and `seen_nontarget_cells` 0.
Its exterior penetration depth runs **[min 5, median 132, max 209] cells**, that
is up to **20.9 deg** of complement path from the padded chart border.

The separation from ordinary outer shoreline is not close. Over the 213 exterior
arcs the per-arc maximum depth has **min 0, median 8, mean 10.4, max 209**: the
**second**-deepest arc reaches only **22** cells, so the bay is **9.5x** deeper
than anything else in the record. Of 1,514 shoreline cells, **546** lie deeper
than 22 cells and **383** deeper than 100. **No threshold was applied to obtain
this** - the depth is simply reported, and the bay separates itself.

### Seed 2179 - a shallow exterior notch plus the residual internal hole

| quantity | value |
|---|---|
| chart | 263 x 192 cells |
| map points | 141,184 |
| raw support / support / complement | 33,752 / 38,608 / 11,888 |
| shoreline cells | 989 |
| complement components | **1 EXTERIOR (11,853 cells, shoreline 956, max depth 45), 1 INTERNAL (35 cells, shoreline 33)** |
| arcs | **195** (194 EXTERIOR, 1 INTERNAL) |

Arcs by state: **UNOBSERVED 33 (32 exterior + 1 internal), TARGET_CONTINUATION 0,
PHYSICAL_DEPTH_BREAK 61, AMBIGUOUS 101.** By cell: UNOBSERVED **494**,
PHYSICAL_DEPTH_BREAK **336**, AMBIGUOUS **159**.

The **residual internal component** left by the one Cyclopean-1a probe survives
into this audit as a single `INTERNAL` / `UNOBSERVED` arc - **arc 194, 33 cells,
centroid (+6.852, -2.136), span 1.5 deg x 0.4 deg**, zero target and zero
non-target evidence, `border_distance_cells_*` **null** because an internal
component is by construction unreachable from the border. Its centroid matches
the 35-cell / 0.3498 deg2 residue Cyclopean-1a reported at (+6.85, -2.13).

Seed 2179's deepest exterior arc is also `UNOBSERVED` - **arc 18, 215 cells,
centroid (-6.971, +5.908), span 11.4 x 9.5 deg, depth [1, 28, 45]** - but at
**45** cells (4.5 deg) it is a shallow staircase notch, not seed 2111's deep
basin. Exterior per-arc depth: **min 0, median 8, mean 8.6, max 45**; **138** of
989 shoreline cells lie deeper than 22 cells.

### The depth-break cue, exercised in the field for the first time

Cyclopean-1a recorded that its physical-depth-break cue was **never exercised**,
because the only hole it found was unobserved. Cyclopean-1b exercises it on real
data, and the inherited 12 mm scale separates the two observed populations
**without overlap**:

| | `PHYSICAL_DEPTH_BREAK` arc range gap (m) | `AMBIGUOUS` arc range gap (m) |
|---|---|---|
| seed 2111 | min **0.0121**, median 0.0315, max 1.5882 | min 0.0001, median 0.0073, max **0.0118** |
| seed 2179 | min **0.0132**, median 0.0365, max 1.7380 | min 0.0006, median 0.0068, max **0.0114** |

Every arc classed physical has a median gap **above** the frozen 0.012 m radius
and every ambiguous arc with a defined gap is **below** it. The frozen FSG3
association radius, which was never chosen for this purpose, lands in the empty
interval between two populations. The largest gaps - **1.59 m** and **1.74 m** -
are the room behind the table.

The two states also separate spatially, again without any rule that says so.
Cell-weighted centroid pitch of `PHYSICAL_DEPTH_BREAK` is **-3.864 deg** (2111)
and **-5.396 deg** (2179), against **+3.634** and **+5.566** for `UNOBSERVED`;
**63.0%** and **68.2%** of physical shoreline cells lie below pitch -6.0 deg,
against **3.5%** and **3.2%** of unobserved cells. The observer has seen past the
lower edge of the cloth onto the table and the room, and has simply never looked
above and to the left.

### Two states of the four did not occur, and why

`AMBIGUOUS` is entirely the **sub-12 mm tail**, not a mixture: measured over
every shoreline cell, **zero** cells carry both target and non-target evidence.
The 152 (2111) and 159 (2179) ambiguous cells are non-target-only, split
**65 + 87** and **76 + 83** between "no local target reference within the
inherited radius, so the gap is undefined" and "gap defined but not larger than
12 mm".

`TARGET_CONTINUATION` is **0 arcs on both records, and this is structural rather
than a defect.** Measured: of 28,835 (2111) and 34,880 (2179) chart cells
carrying target evidence, **100.00%** fall inside the dilated support and
**zero** fall outside it, so **no target-evidence cell can ever be a shoreline
cell**. The reason is the representation itself - a target observation that was
fused becomes a surfel, and the surfel's 12 mm footprint dilation covers the very
cell the observation projected to. On this fixture the state is unreachable by
construction. **Nothing was changed to make it occur**; doing so would require
altering the inherited footprint or raster rule, which this step forbids.

### Aggregate

```text
[cyclopean1b-compare] CYCLOPEAN1B_COMPLETE {"records": [{"arc_count": 213, "arcs_by_state": {"AMBIGUOUS": 86, "PHYSICAL_DEPTH_BREAK": 81, "TARGET_CONTINUATION": 0, "UNOBSERVED": 46}, "exterior_arcs_by_state": {"AMBIGUOUS": 86, "PHYSICAL_DEPTH_BREAK": 81, "TARGET_CONTINUATION": 0, "UNOBSERVED": 46}, "internal_arcs_by_state": {"AMBIGUOUS": 0, "PHYSICAL_DEPTH_BREAK": 0, "TARGET_CONTINUATION": 0, "UNOBSERVED": 0}, "max_exterior_border_distance_cells": 209, "seed": 2111}, {"arc_count": 195, "arcs_by_state": {"AMBIGUOUS": 101, "PHYSICAL_DEPTH_BREAK": 61, "TARGET_CONTINUATION": 0, "UNOBSERVED": 33}, "exterior_arcs_by_state": {"AMBIGUOUS": 101, "PHYSICAL_DEPTH_BREAK": 61, "TARGET_CONTINUATION": 0, "UNOBSERVED": 32}, "internal_arcs_by_state": {"AMBIGUOUS": 0, "PHYSICAL_DEPTH_BREAK": 0, "TARGET_CONTINUATION": 0, "UNOBSERVED": 1}, "max_exterior_border_distance_cells": 45, "seed": 2179}], "structural_fails": []}
```

### Visual reading, descriptive

`full-seed2111/shoreline.png` makes the bay legible with **no post-hoc
smoothing**: the grey support is a large quadrilateral, and a white complement
channel enters from the **left edge**, runs horizontally between an upper slab
and a lower-left slab, and opens into a wide rectangular basin in the middle
right. The basin and its channel are one continuous white region reaching the
chart border - a bay. Its entire perimeter is drawn red, `UNOBSERVED`; there is
**no** salmon interior tint anywhere, because there is no internal component.
Blue `PHYSICAL_DEPTH_BREAK` appears only along the lower-right outer edge, with
small purple `AMBIGUOUS` fragments beside it.

`full-seed2179/shoreline.png` shows a nearly solid support with a stepped
staircase notch cut out of the upper left - that is the 215-cell exterior arc -
and a single small red crescent in the middle right, which is the residual
internal hole. The lower edge is a long continuous blue `PHYSICAL_DEPTH_BREAK`
run; the upper and left edges are red `UNOBSERVED`. The picture states the same
thing the numbers do: this record ends where it has seen the table below, and
stops where it never looked above.

The shoreline is genuinely **fragmented** - 213 and 195 arcs for 1,514 and 989
cells, a **median arc of 2 and 1 cells** against maxima of 615 and 215 - and that
is reported as measured.
It is a consequence of forbidding a minimum-arc filter and any morphology
tuning, and **nothing was smoothed after seeing it**.

### Structural FAIL lines, and code fixes

**No structural FAIL line was produced anywhere**, and **no code fix was made**;
no source file was modified.

The inherited `RuntimeWarning: invalid value encountered in cast` from
`cyclopean1a_topology.py:117-118` appears again - **26** and **34** occurrences
while rebuilding parent evidence - and is recorded again as harmless, now with a
stronger argument than in Cyclopean-1a. First by inspection: `_indices` builds
its `good` mask with an **explicit** `np.isfinite(yaw) & np.isfinite(pitch)`
term, so the value the cast produced for a non-finite input is never relied on.
Second by measurement: rebuilding the complete Cyclopean-1b evidence with a
NaN-prefiltered `_indices` raises **0** warnings and yields **bitwise identical**
`seen_target`, `seen_nontarget`, `target_range_m`, `nontarget_range_m`,
`raw_support`, `support` and the target range raster on **both** seeds. It
changes no Cyclopean-1b number, so the parent scientific source was correctly
left alone.

One implementation detail was checked rather than assumed: `_exterior_distance`
leaves unreachable complement cells at the sentinel **-1**, which is exactly the
internal component. That sentinel **never reaches the report** - all
`border_distance_cells_*` fields are `null` for internal arcs and non-negative
for all 194 + 213 exterior arcs, verified directly against both JSON files.

### What this establishes, and what it does not

Established. **The existing representation already carries boundary semantics -
no new machinery was needed to read them out.** It represents seed 2111's bay as
a single, unmistakable `UNOBSERVED` arc that is 40.6% of the shoreline and 9.5
times deeper than any other arc, so **a bay is describable even though it is not
a hole**, which is precisely the case Cyclopean-1a could not catch. It keeps
lakes and bays distinct: seed 2179's 35-cell residue stays `INTERNAL` while its
staircase notch stays `EXTERIOR`. And it distinguishes *unresolved* boundary from
*observed* physical boundary on real data, with the frozen 12 mm scale falling in
the empty interval between the two measured gap populations.

Not established. **This is an audit and it changes no policy**: no probe was
selected, no gaze proposed, no stopping rule touched. **No completeness claim is
made** - "40.6% of the shoreline" describes the boundary, not the object, and
`no_frontier` is not being called wrong. `TARGET_CONTINUATION` never occurred, so
that quarter of the state space has **no field evidence** at all; the reason is
understood and structural, but it means the four-state vocabulary is really a
three-state vocabulary on this fixture. Arc fragmentation is measured, not
judged. Whether a deep unobserved arc should ever become a fixation is exactly
the question left open, and **1b deliberately does not answer it**.
