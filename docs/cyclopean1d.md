# Cyclopean-1d — observation versus measurement

## Question

Cyclopean-1c established that one fixation aimed from cyclopean boundary
structure can acquire a large amount of useful missing target surface. It also
exposed a more refined epistemic distinction: a small residual on the printed
emblem was **seen in the image** but frozen stereo produced little/no valid
depth there.

Cyclopean-1d asks only:

> Of the final shoreline cells that the existing Cyclopean-1b semantics still
> call `UNOBSERVED`, which were truly never imaged, and which were imaged as
> target but not measured in depth?

This is a read-only audit. It does not take another look.

## Why refine the entity

The old state `UNOBSERVED` meant only that no valid stereo target or non-target
3D evidence landed on that cyclopean shoreline cell. Cyclopean-1c showed that
this can conflate two different situations:

1. **absence of attention** — the region was never seen;
2. **failure of measurement** — the region was seen as target, but the stereo
   instrument did not return valid depth.

These should not force the controller to invent different heuristics later. The
representation should first say what actually happened.

## Frozen base semantics

Rebuild the final Cyclopean-1c support on the exact inherited chart and reuse
Cyclopean-1b's shoreline states unchanged. `PHYSICAL_DEPTH_BREAK` and
`AMBIGUOUS` are not redefined.

Only cells whose base shoreline state is `UNOBSERVED` are refined.

## Observation versus depth

For one such shoreline cell, Cyclopean-1b already provides a nearby target
range reference: `local_target_range_m`. Use that inherited value only to build
a **continuation test point** on the cell's cyclopean ray.

The point is not geometry and is never fused. It is a query into past images:
if the same putative continuation had existed there, what did the completed
foveal observations contain at its projected image location?

For every completed left rectified core, use the exact saved calibration,
rectification, crop, oracle instance mask, calibration support and stereo
`valid` mask. Observation and measurement are independent:

- target instance at a supported projected pixel -> target was **observed**;
- the same pixel also `valid == true` -> target depth was **measured**.

No RGB texture threshold is introduced here. The audit reads the instrument's
already-saved valid mask rather than reverse-engineering why it failed.

## Refined states

The base `UNOBSERVED` shoreline is split descriptively into:

- `NEVER_OBSERVED` — no completed supported projection carried image evidence;
- `OBSERVED_TARGET_NO_DEPTH` — target image evidence exists, but no projected
  target sample has valid stereo depth;
- `OBSERVED_TARGET_WITH_DEPTH` — target image evidence and valid depth both
  exist even though the cell remains outside final support; this is diagnostic;
- `OBSERVED_NONTARGET_ONLY` — only non-target image evidence exists under the
  continuation projection hypothesis;
- `MIXED_OBSERVATION` — target and non-target evidence both occur across views;
- `NO_RANGE_REFERENCE` — the inherited local target range is undefined, so no
  continuation projection is attempted.

No state selects a fixation in this step.

## Scope

Seed 2111 only, using the completed Cyclopean-1c record and all of its already
completed acquisition ancestry. No Blender invocation, no new fixation, no
FSG6f import, no stopping change, no mesh, no morphology, no normal cue, no
new depth or texture threshold, and no evaluator truth.

The intended readout is especially simple:

- does the tiny internal residue exposed by Cyclopean-1c become
  `OBSERVED_TARGET_NO_DEPTH` rather than `NEVER_OBSERVED`?
- how much of the remaining exterior-connected bay shoreline is still genuinely
  `NEVER_OBSERVED`?

Those are measurements, not gates.

## Results

Run 2026-09-21 on the workstation. **`CYCLOPEAN1D_COMPLETE`,
`structural_fails: []`.** The Cyclopean-1c record and its whole ancestry were
read **only**, and the four pinned parent files are byte-identical afterwards.
Structural only: **there is no quality gate here, no state is a PASS, and no
refined state selects a fixation or touches stopping.**

### Provenance

Working tree clean at `47b33f2`. The prospective package adds **exactly seven
files, all `A`** (`tools/cyclopean1d_{public,epistemic,audit,compare}.py`,
`tools/dev/check_cyclopean1d.py`, `docs/cyclopean1d.md`,
`docs/cyclopean1d-checks.md`). `git diff` against the Cyclopean-1c result commit
`b32ce44` over **44 frozen sources** - every FSG1/FSG3/FSG6f source, the
renderer, scene, rig, pin file, every Reality Check 1/2/2b source and **every
Cyclopean-1a, 1b and 1c source** - is **empty (0 lines)**, and all 44 sha256 are
SAME.

The parent was located **by manifest**: exactly one `Cyclopean1c-bay-probe-v1`
record exists, `previews/cyclopean1c/full-seed2111`, with `profile` full, `seed`
2111, `truth_opened` false, `fixed_head`/`static_scene` true, `added_fixations`
1 and `parent_fixations_rerendered` 0. Nothing to disambiguate. Its four pinned
files hash identically **before and after**:

| file | sha256 (before == after) |
|---|---|
| `prediction_manifest.json` | `fb4e250959288019…75945b12` |
| `surface_map.npz` | `66adebea5ece578f…ca54b7fb` |
| `probe_patch.npz` | `52f052d153e0c032…767b1b24` |
| `shoreline_after.png` | `f187ae296c30fc03…a133607c8` |

Ancestry was followed to its root, not assumed:

| step | record | contributes |
|---|---|---|
| Reality Check 1 | `previews/reality1/full-seed2111` | fixations **0-5** |
| Reality Check 2b | `previews/reality2b/full-seed2111` | fixations **6-12** (`parent_fixation_count` 6, 13 gazes) |
| Cyclopean-1a | `previews/cyclopean1a/full-seed2111` | **none** (`added_fixations` 0 - seed 2111 took no 1a probe) |
| Cyclopean-1b | `previews/cyclopean1b/full-seed2111` | **none** (read-only audit) |
| Cyclopean-1c | `previews/cyclopean1c/full-seed2111` | fixation **13** |

**14 completed fixations, `fix_00` … `fix_13`**, all replayed from saved
calibration, rectification, oracle instance mask, calibration support and frozen
stereo `valid` mask.

### Environment, and that nothing was acquired

Host `.venv/bin/python` 3.12.3 only; the audit is **Interactive at 2.6 s**.
**No Blender process ran**, verified three ways: no `subprocess`, `blender` or
`bpy` token appears in any Cyclopean-1d source; `pgrep blender` found nothing;
and the output directory contains **exactly three host artifacts** -
`observation_measurement_report.json`, `prediction_manifest.json`,
`epistemic_shoreline.png` - with no `acquisition/`, `.ply`, `.exr` or
`render.log` anywhere beneath it.

### Checks

`py_compile` clean on all five modules. The three prescribed positive lines
appeared verbatim:

```text
[cyclopean1d-epistemic] PASS never_observed=true seen_no_depth=true measured=true mixed=true projection=true
[cyclopean1d-policy] PASS parent=cyclopean1c read_only=true observation_separate_from_depth=true no_acquisition=true no_policy=true quality_gated=false
[cyclopean1d-check] SUMMARY passed=6 failed=0
```

All six deliberate negatives exit 1: `depthonly`, `acquire`, `truth`, `policy`,
`threshold`, `mutateparent`. Every prior suite is still green with its negative
set still firing: **cyclopean1c 6/6 (6/6)**, **cyclopean1b 6/6 (6/6)**,
**cyclopean1a 6/6 (6/6)**, **reality2b 7/7 (10/10)**, **reality1 6/6 (6/6)**,
**fsg6f 14/14 (15/15)**.

### The projection was validated before it was trusted

The shipped `epistemic` self-test exercises the classifier and a pinhole
projection, but it uses an **identity** `R_hc` and `R1`, so it cannot confirm the
head-to-camera convention on real data - and a wrong convention would silently
mislabel every cell. So the whole chain was checked by round-trip on saved
records, which the authorization explicitly allows: each observation's own
reconstructed head-frame points were pushed back through
`project_head_to_rectified_core` and compared with the pixels they came from.

| observation | valid points | reprojection error (px) |
|---|---|---|
| `fix_00` (Reality Check 1 branch) | 44,518 | median **0.0000**, p95 0.0000, max **0.0000** |
| `fix_09` (Reality Check 2b branch) | 25,268 | median **0.0000**, p95 0.0000, max **0.0000** |
| `fix_13` (Cyclopean-1c probe) | 53,894 | median **0.0000**, p95 0.0000, max **0.0000** |

100% within 0.5 px on all three branches, `crop_xywh` `[192, 192, 256, 256]`
against a 256x256 core. `R_hc`, `R1`, `P1` and the crop offset are exact.
**No projection defect was found and no empirical offset, dilation or tolerance
was introduced.**

### Base, unchanged

The final Cyclopean-1c support was rebuilt on the inherited chart - **263 x 199**
cells, grid **0.1 deg**, footprint **4 cells / 0.322236 deg**, map **137,734**
points - and Cyclopean-1b's shoreline states were reused unchanged.
`PHYSICAL_DEPTH_BREAK` (314 cells) and `AMBIGUOUS` (152 cells) were **not
redefined**. Of the **1,384** shoreline cells, **918** carry the base state
`UNOBSERVED`, and only those were refined.

### The refinement

| refined state | cells | exterior | internal | % of base |
|---|---|---|---|---|
| `NEVER_OBSERVED` | **388** | 388 | 0 | 42.27% |
| `OBSERVED_TARGET_NO_DEPTH` | **28** | 0 | **28** | 3.05% |
| `OBSERVED_TARGET_WITH_DEPTH` | **0** | 0 | 0 | 0.00% |
| `OBSERVED_NONTARGET_ONLY` | **398** | 398 | 0 | 43.36% |
| `MIXED_OBSERVATION` | **0** | 0 | 0 | 0.00% |
| `NO_RANGE_REFERENCE` | **104** | 100 | 4 | 11.33% |
| **sum** | **918** | 886 | 32 | 100% |

The partition is exact - the six states sum to the 918 base cells with nothing
left over. By arc: **141** refined arcs in total - `NEVER_OBSERVED` **1** arc /
388 cells, `OBSERVED_TARGET_NO_DEPTH` **2** arcs / 28 cells,
`OBSERVED_NONTARGET_ONLY` **44** arcs / 398 cells, `NO_RANGE_REFERENCE` **94**
arcs / 104 cells.

**The exterior/internal split is total and clean**: every internal cell is
`OBSERVED_TARGET_NO_DEPTH` or `NO_RANGE_REFERENCE`, and every exterior cell is
`NEVER_OBSERVED`, `OBSERVED_NONTARGET_ONLY` or `NO_RANGE_REFERENCE`. The two
families do not overlap in a single cell.

### The tiny internal residue: the Cyclopean-1c diagnosis is confirmed

Cyclopean-1c predicted that its residue was *seen but not measured*. It is.

| arc | component | state | cells | centroid | target seen | **target depth valid** | supported projections |
|---|---|---|---|---|---|---|---|
| 2 | 2 (31 cells) | `OBSERVED_TARGET_NO_DEPTH` | **27** | (+6.7926, -2.1519) | 27 | **0** | 27 |
| 139 | 2 | `NO_RANGE_REFERENCE` | 2 | (+6.7500, -2.1000) | 0 | 0 | 0 |
| 138 | 2 | `NO_RANGE_REFERENCE` | 1 | (+6.5000, -2.2000) | 0 | 0 | 0 |
| 140 | 2 | `NO_RANGE_REFERENCE` | 1 | (+7.1000, -2.1000) | 0 | 0 | 0 |
| 1 | 1 (1 cell) | `OBSERVED_TARGET_NO_DEPTH` | **1** | (+7.3000, -2.9000) | 1 | **0** | 1 |

Both centroids match the internal components Cyclopean-1c reported at
(+6.7903, -2.1484) and (+7.3000, -2.9000). **Every internal cell that has a range
reference is `OBSERVED_TARGET_NO_DEPTH` - 28 of 28 - with 28 supported
projections carrying target instance evidence and exactly zero valid stereo
depth.** Not a single cell is `NEVER_OBSERVED`.

A per-observation breakdown makes it sharper: of the 14 completed views,
**exactly one - `fix_13`, the Cyclopean-1c probe itself - contributed any
supported projection** (28 of 28 target-seen, 0 depth-valid). All thirteen
earlier views contributed **zero** supported projections there. The region was
imaged once, by the very fixation that filled the bay around it, and the frozen
instrument returned no depth.

This reproduces Cyclopean-1c's conclusion from a different and stronger source:
1c inferred it from an RGB texture proxy, while 1d reads the instrument's own
**saved `valid` mask**. No texture threshold was used here.

### The remaining exterior bay: genuinely unseen, and the rim is simply the edge

The residual bay is **one single `NEVER_OBSERVED` arc of 388 cells** - 42.27% of
all remaining unobserved shoreline - centroid **(-3.621, +2.306)**, reaching the
maximum exterior penetration depth **168**, with target seen 0, non-target seen 0
and **supported projections 0**.

That zero was checked rather than assumed, because "no supported projection"
could mean either *out of frame* or *in frame but outside calibration support* -
two quite different claims. Measured over all **5,432** projection attempts
(388 cells x 14 views): **5,432 (100.00%) fell entirely outside the rectified
core of every view**, and **zero** landed inside a core at all. So this is
absence of attention in the strongest available sense - never in frame, in any
completed fixation - not an artifact of calibration support.

The **398 `OBSERVED_NONTARGET_ONLY` cells across 44 arcs** are a different thing
entirely, and they sit on the **outer rim**: the largest are at (+5.500, +9.542)
71 cells, (+12.209, +8.309) 45, (-11.116, +9.789) 45, (-6.955, +10.580) 20, all
shallow (depth 4-22). There the continuation hypothesis *was* carried into
completed imagery and what it found was **non-target** - background, table or
room. Those cells are not unexplored; the object simply ends, and the boundary
stays open only because the inherited base state had no way to say so.

### `NO_RANGE_REFERENCE` is a deterministic artifact of the inherited radius

All **104** such cells were measured against the raster: the distance from each
to the nearest raw target support is **min 5.10, median 5.10, max 5.10 cells** -
every one strictly beyond the inherited local-range disk radius of
`footprint_cells + 1 = 5`. 5.10 is sqrt(26), the first lattice distance past 5.
These cells are not a defect and carry no epistemic content: the inherited
Cyclopean-1b local target range is simply undefined there, so by contract no
continuation point was built and no projection was attempted. **Nothing was
adjusted to reduce them** - widening that radius would be a new tolerance, which
this step forbids.

### Two states never occurred

`OBSERVED_TARGET_WITH_DEPTH` is **0** and `MIXED_OBSERVATION` is **0**. Both are
honest nulls and both were preserved rather than explained away. The first is the
state the contract calls *diagnostic* - a cell imaged as target, with valid
depth, yet still outside final support, which would have indicated fusion or
support-rasterization loss; it did not occur anywhere. The second would mean a
continuation point landing on target in one view and non-target in another; also
absent, consistent with the observed split in which target evidence appears only
on the internal residue and non-target evidence only on the outer rim. Four of
the six declared states carry all 918 cells; the vocabulary is wider than this
record needs.

### Aggregate

```text
[cyclopean1d-compare] CYCLOPEAN1D_COMPLETE {"records": [{"base_unobserved_shoreline_cells": 918, "exterior_refined": {"MIXED_OBSERVATION": 0, "NEVER_OBSERVED": 388, "NO_RANGE_REFERENCE": 100, "OBSERVED_NONTARGET_ONLY": 398, "OBSERVED_TARGET_NO_DEPTH": 0, "OBSERVED_TARGET_WITH_DEPTH": 0}, "internal_refined": {"MIXED_OBSERVATION": 0, "NEVER_OBSERVED": 0, "NO_RANGE_REFERENCE": 4, "OBSERVED_NONTARGET_ONLY": 0, "OBSERVED_TARGET_NO_DEPTH": 28, "OBSERVED_TARGET_WITH_DEPTH": 0}, "observation_count": 14, "refined": {"MIXED_OBSERVATION": 0, "NEVER_OBSERVED": 388, "NO_RANGE_REFERENCE": 104, "OBSERVED_NONTARGET_ONLY": 398, "OBSERVED_TARGET_NO_DEPTH": 28, "OBSERVED_TARGET_WITH_DEPTH": 0}, "seed": 2111}], "structural_fails": []}
```

### Visual reading, descriptive

`epistemic_shoreline.png` separates three different reasons a boundary stays open,
and they are visually distinct at a glance:

- the **residual L-shaped bay slot** in the centre-left is outlined entirely in
  **red, `NEVER_OBSERVED`** - the single 388-cell arc;
- the **outer rim** of the cloth - top edge, right edge, upper left - is
  **cyan, `OBSERVED_NONTARGET_ONLY`**: looked at, and the object ends;
- the **small orange crescent** in the middle right is
  **`OBSERVED_TARGET_NO_DEPTH`** - the emblem residue, seen but unmeasured;
- the **bottom edge** remains **blue, `PHYSICAL_DEPTH_BREAK`**, with small purple
  `AMBIGUOUS` fragments, both inherited from Cyclopean-1b and untouched.

No yellow (`OBSERVED_TARGET_WITH_DEPTH`) and no magenta (`MIXED_OBSERVATION`)
appear anywhere in the image. The rendering was verified against the report
rather than read by eye: counting pixels of each legend colour and dividing by
the 3x upscale gives exactly **388 / 398 / 28 / 104 / 314 / 152** cells and
**38,971** support cells, matching the JSON figure for figure.

### Structural FAIL lines, and code fixes

**No structural FAIL line was produced anywhere**, and **no code fix was made**;
no source file was modified.

The inherited `RuntimeWarning: invalid value encountered in cast` from
`cyclopean1a_topology.py:117-118` appears again - **28** occurrences while
rebuilding the final boundary - and is recorded again as harmless, now tested
against the 1d output itself. By inspection, `_indices` builds its `good` mask
with an **explicit** `np.isfinite(yaw) & np.isfinite(pitch)` term, so the cast's
output for a non-finite input is never used. By measurement, rebuilding the whole
audit with a NaN-prefiltered `_indices` raises **0** warnings and yields
**bitwise identical** `raw_support`, `support`, `shoreline`, base `state_code`,
`local_target_range_m`, `component_labels` **and the refined state array itself**,
with all six refined counts unchanged. It changes no Cyclopean-1d number, so the
parent scientific source was correctly left alone.

### What the refined entities establish, and what they do not

Established. **The old `UNOBSERVED` state really was conflating two different
things, and separating them costs nothing but bookkeeping.** On this record it
splits cleanly and along an anatomical line: **every internal cell is
seen-but-unmeasured, every deep exterior cell is never-seen, and 398 rim cells
are neither** - they were imaged and the object simply ends there. **The
Cyclopean-1c emblem diagnosis is confirmed from the instrument's own saved valid
mask** rather than from a texture proxy: 28 of 28 internal cells with a range
reference carry target evidence and **zero** valid depth, contributed by exactly
one view. And **the deep bay remnant is genuinely unseen** - 5,432 of 5,432
projection attempts fell outside every completed view's core.

Not established. **Nothing here changes any controller**: no gaze was proposed,
no ranking touched, no stopping rule consulted, and FSG6f was never imported.
**No completeness claim is made** - 42.27% and 43.36% describe a shoreline, not
an object, and none of them is a threshold. **The continuation test point is a
projection hypothesis, never geometry**: `OBSERVED_NONTARGET_ONLY` means the
hypothesis found non-target at *that assumed range*, which is evidence about the
hypothesis and not proof that the surface ends - a different continuation range
could read differently, and none was tried. **`NO_RANGE_REFERENCE` leaves 104
cells unclassified** by construction, and this step deliberately did not widen
the inherited radius to reduce them. **Two of the six states never fired**, so
this record does not exercise the full vocabulary. And the obvious next question
- what a controller should do differently for *never seen* versus *seen but
unmeasurable* - is exactly what 1d refuses to answer.
