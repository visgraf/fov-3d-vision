# MultiObject-1c — object-143 epistemic audit for scene progress

## Motivation

MultiObject-1b2 revision 2 transferred the frozen single-object grower to object 143 successfully: object 143 grew from 5,344 seed surfels to 42,988 surfels with pure id 143 and object 141 remained byte-identical.  But the run reached the **24-object-fixation engineering watchdog**, not the frozen policy's `no_frontier` stop.  At the final decision the policy still reported 696 open frontier voxels.

The same run also showed that object 143 is a large, smooth architectural surface on which stereo is frequently starved: some views contain tens of thousands of visible id-143 pixels while only roughly 1–3% yield valid depth.  Merely raising the watchdog would therefore mix two different causes of residual frontier:

1. territory that has not yet been looked at; and
2. territory that has been looked at but could not be measured by the current stereo instrument.

MultiObject-1c separates those causes **without taking another look**.

## Question

> What does the remaining object-143 cyclopean shoreline mean after the 24-look run: genuinely unseen territory, seen-but-unmeasured target surface, observed non-target/boundary evidence, or unresolved bookkeeping geometry?

This is an audit, not another completion loop.

## Method

The audit is read-only.

1. Load the completed MultiObject-1b2 object-143 surfel map.
2. Build the object-143 cyclopean chart at the already-established 0.1 degree grid.
3. Reuse the inherited footprint implied by the frozen 12 mm association radius.
4. Replay the **saved** object-143 observation history only as evidence; no rendering and no fusion occur.
5. Reuse the Cyclopean-1b shoreline semantics (`UNOBSERVED`, `PHYSICAL_DEPTH_BREAK`, `AMBIGUOUS`, etc.).
6. Refine only base `UNOBSERVED` shoreline cells with the Cyclopean-1d observation/measurement distinction:
   - `NEVER_OBSERVED`
   - `OBSERVED_TARGET_NO_DEPTH`
   - `OBSERVED_TARGET_WITH_DEPTH`
   - `OBSERVED_NONTARGET_ONLY`
   - `MIXED_OBSERVATION`
   - `NO_RANGE_REFERENCE`

No texture threshold, no new geometric tolerance, no interpolation and no layered occlusion model are introduced.

## Scene-progress principle

The audit records the status of object 143 but **does not gate scene progress**.

- If exterior `NEVER_OBSERVED` remains, object 143 is marked `ATTENTION_INCOMPLETE_RETAIN_FOR_REVISIT`.
- If exterior `NEVER_OBSERVED` is zero but target-no-depth residue remains, object 143 is marked `ATTENTION_COMPLETE_MEASUREMENT_PARTIAL`.
- If neither remains, it is marked `ATTENTION_COMPLETE_NO_TARGET_NO_DEPTH_RESIDUE`.

In all cases:

```text
scene_disposition = MOVE_TO_NEXT_OBJECT
```

This is deliberate.  A full-scene observer cannot require every object to be perfectly reconstructed before attending elsewhere.  Persistent object memory allows later revisit.

## Deliberately deferred

- watchdog extension;
- another object-143 growth look;
- alternate stereo matcher, baseline, active illumination or texture rescue;
- layered spherical depth for occlusion;
- automatic next-object discovery itself (that is the next stage);
- evaluator truth or accuracy claims.

## Expected output

The record contains:

- `object_143_epistemic_report.json` — state counts, arcs and chart statistics;
- `object_143_epistemic_shoreline.png` — support plus epistemic shoreline visualization;
- `prediction_manifest.json` — integrity and scene-progress disposition.

The scientific value is descriptive: it tells us **what kind of unfinished business object 143 carries forward while the scene-level process progresses**.

## Results

Run 2026-09-21 on the workstation. **`MULTIOBJECT1C_COMPLETE`,
`structural_fails: []`.** Read-only: **no Blender process, no acquisition, no
fusion**, and all 54 pinned inputs byte-identical afterwards.

- **`object_143_status = ATTENTION_INCOMPLETE_RETAIN_FOR_REVISIT`**
- **`scene_disposition = MOVE_TO_NEXT_OBJECT`**

The audit answers the question it was built for: **the residue object 143 carries
forward is overwhelmingly seen-but-unmeasured, not unexplored.**
`OBSERVED_TARGET_NO_DEPTH` **15,089** cells against `NEVER_OBSERVED` **830** — a
**18.2 : 1** ratio, **73.6%** versus **4.1%** of the refined shoreline. These are
measurements, not thresholds.

### Provenance

Working tree clean. Prospective commit **`3f3394b`**; parent result **`6b722d0`**.
The package adds **exactly seven files, all `A`**. `git diff` against `6b722d0`
over **63 frozen sources** — every FSG1/FSG3/FSG6f source, scene, rig, pin file,
every Reality Check 1/2/2b source, `scene_render_fix.py`, every Cyclopean-1a..1g
source and every MultiObject-1a/1b/1b2 source — is **empty (0 lines)**, all 63
sha256 SAME. The inherited epistemic machinery the audit reuses is untouched:
`cyclopean1b_boundary.py` `b34371ce8ffa86c7…`, `cyclopean1d_epistemic.py`
`559351701151a144…`, `cyclopean1d_audit.py` `2f9b92537bb1556b…`,
`cyclopean1a_topology.py` `6ed00fca00907f33…`.

The parent was located **by manifest** and **all ten required conditions hold**:
schema `MultiObject1b2-resume-object143-growth-v2`, seed 2111, profile `full`,
`truth_opened` false, `object_ids [141, 143]`, object-143 map pure `{143}`,
`object_2_fixations_total` 24, `termination_reason` `object2_watchdog`,
`scientific_stop_reached` false, `structural_fails` []. Exactly one record
matched: `previews/multiobject1b2-r2/full-seed2111`.

### Read-only integrity

**54 inputs pinned before and re-hashed after — all byte-identical**: the five
parent files (`prediction_manifest.json` `74d5cc0f58a2c590…`,
`object_143_surface_map.npz` `bbc4b856a07d2be5…`, `scene_graph.json`
`5df35f372460399…`, `scene_cyclopean_footprints.npz` `5ef4982532f8bde2…`,
`object_143_policy_trace.json` `c17589df1aa18b4c…`), the inherited object-141
source `6ac98f6251b47337…f71e524a`, and **all 24 object-143 calibration/observation
pairs for global steps 18–41**.

No Blender process ran, and this was verified three ways: no `subprocess`,
`blender` or `bpy` token appears in any MultiObject-1c source; `pgrep blender`
found nothing; and the output contains **exactly three host artifacts** —
`object_143_epistemic_report.json`, `object_143_epistemic_shoreline.png`,
`prediction_manifest.json` — with no acquisition directory, `.exr`, `.ply` or
render log anywhere beneath it. `acquisitions_added: 0`,
`object_1_read_only: true`, `truth_opened: false`. Object 141 remains **155,684**
points, ids exactly **{141}**.

### Environment and wall time

Host `.venv/bin/python` 3.12.3 only. **Interactive at 10.6 s.**

### Checks

`py_compile` clean on all five modules. The three prescribed lines appeared
verbatim:

```text
[multiobject1c-audit] PASS read_only=true object143_only=true observation_separate_from_depth=true no_watchdog_extension=true
[multiobject1c-progress] PASS descriptive_only=true scene_progress_unblocked=true next=next_object
[multiobject1c-check] SUMMARY passed=6 failed=0
```

All six negatives are **genuine source-mutation controls**, each exiting **1**
with the expected detector and **none exiting 2**:

| negative | rc | detected by |
|---|---|---|
| `acquire` | 1 | `read_only_no_acquisition` |
| `object1active` | 1 | `object143_only_object141_read_only` |
| `depthonly` | 1 | `observation_separate_from_depth` |
| `threshold` | 1 | `frozen_scale_no_new_threshold` |
| `watchdog` | 1 | `watchdog_not_extended_no_policy_loop` |
| `qualitygate` | 1 | `scene_progress_not_quality_gated` |

**No regression**: all 13 prior suites green and **92 prior negatives** still
firing — multiobject1b2 7/7, multiobject1b 6/6, multiobject1a 6/6,
cyclopean1g/1f/1e/1d/1c/1b/1a 6/6 each, reality2b 7/7 (10/10), reality1 6/6,
fsg6f 14/14 (15/15).

### Chart and inherited scale

| quantity | value |
|---|---|
| chart | **598 × 331** cells, grid **0.1 deg**, `yaw0 −31.10`, `pitch0 −10.20` |
| footprint | **2 cells / 0.19584847743640496 deg** |
| object-143 map points | **42,988** |
| observations replayed | **24**, global steps **18–41** |
| raw support / support | 17,947 / **65,971** |
| complement | 131,967 |
| shoreline | **20,799** |
| complement components | **489** — **1 EXTERIOR** (118,687 cells), **488 INTERNAL** (13,280 cells total, largest 1,407) |
| max exterior penetration depth | **288** cells |

The footprint deserves a note because it differs from object 141's. It is the
**same frozen 12 mm FSG3 rule**, applied at object 143's own median range:
`atan(0.012 / 3.510605 m) = 0.19584847743640496 deg`, reproduced to 1e-12, giving
**2 cells** where object 141 at 2.13 m gave 4 cells / 0.322236 deg. **The metric
scale is unchanged; only the angular subtense is smaller because the object is
farther.** No new tolerance was introduced.

### Base boundary states (Cyclopean-1b, reused unchanged)

| state | cells |
|---|---|
| `UNOBSERVED` | **20,489** |
| `PHYSICAL_DEPTH_BREAK` | 201 |
| `AMBIGUOUS` | 109 |
| `TARGET_CONTINUATION` | 0 |
| **sum** | **20,799** = shoreline cells |

Only the 20,489 base-`UNOBSERVED` cells were refined, exactly as specified.

### Refined states (Cyclopean-1d, reused unchanged)

| refined state | total | exterior | internal | arcs |
|---|---|---|---|---|
| `NEVER_OBSERVED` | **830** | **830** | 0 | **73** |
| `OBSERVED_TARGET_NO_DEPTH` | **15,089** | 7,274 | **7,815** | **687** |
| `OBSERVED_TARGET_WITH_DEPTH` | **1** | 1 | 0 | 1 |
| `OBSERVED_NONTARGET_ONLY` | **816** | 816 | 0 | 195 |
| `MIXED_OBSERVATION` | **88** | 88 | 0 | 66 |
| `NO_RANGE_REFERENCE` | **3,665** | 2,363 | 1,302 | 3,088 |
| **sum** | **20,489** | **11,372** | **9,117** | **4,110** |

The partition is exact: the six refined states sum to the 20,489 base-`UNOBSERVED`
cells, and exterior + internal sum to the same total.

**Exterior `NEVER_OBSERVED`**: **830** cells in **73** arcs, deepest inherited
border distance **226** cells; the largest such arc is only **125** cells at
centroid **(−10.753, −8.982)** with its own maximum depth **23**. So the genuinely
unseen residue is not one deep pocket but 73 shallow scraps around the rim.

**`OBSERVED_TARGET_NO_DEPTH`** is the dominant state at **15,089** cells in
**687** arcs, and it is the only state with substantial **internal** presence
(**7,815** cells) — consistent with the 488 internal complement components, which
are interior holes inside territory the observer has already looked at.

`OBSERVED_TARGET_WITH_DEPTH` occurred exactly **once** — a single cell. It is the
diagnostic state (imaged, measured, yet outside support), and one cell out of
20,489 is recorded as an honest near-null rather than explained away.

### Inherited final FSG6f decision

From the parent's `object_143_policy_trace.json`, at global step **41** /
object-fixation **23**: `stop: false`, `reason: 'continue'`, `next_gaze_deg`
**(+6.5029, −12.9404)**, `frontier_count` **991**, **`frontier_open_count` 696**,
`frontier_map_resolved_count` 43, `frontier_boundary_resolved_count` 252,
`frontier_voxel_count` 18,125, 4 candidates before consensus, **0 rejected**. The
parent's `termination_reason` was `object2_watchdog` with
`scientific_stop_reached: false`.

**This audit explains that open frontier.** The policy correctly kept saying
`continue` because 696 frontier voxels remained open — but the shoreline shows
that the territory behind them is largely surface the instrument has already
looked at and could not measure, not surface it has yet to visit.

### Visual reading, descriptive

`object_143_epistemic_shoreline.png` shows object 143's support as a **frame**: a
broad marbled band across the top, vertical bands down both sides, and a band
along the bottom, surrounding a large white interior region that is object 141's
territory and correctly not object 143's.

The shoreline is overwhelmingly **orange — `OBSERVED_TARGET_NO_DEPTH`** — and it
lies *inside* the support, lacing through the marbled top band and outlining
hundreds of small interior holes. **Red — `NEVER_OBSERVED`** appears only as a
thin trace on the **outer** rim: along the far left edge, the bottom-left, the
bottom, and the outer right edge. **Cyan — `OBSERVED_NONTARGET_ONLY`** appears in
places along that same outer boundary.

The picture states the measurement plainly: **object 143's outer extent is
essentially delimited; what is missing is depth *within* what it has already
seen.** The unfinished business is interior lacework, not an unexplored frontier.

### Status and disposition

`object_143_status = ATTENTION_INCOMPLETE_RETAIN_FOR_REVISIT`, because exterior
`NEVER_OBSERVED` is **830 > 0** — the literal rule, applied without a threshold.

`scene_disposition = MOVE_TO_NEXT_OBJECT`, `next_stage = 'next-object
discovery/selection'`. The comparator reports this **regardless** of the
descriptive status, as designed: a full-scene observer cannot require every
object to be perfectly reconstructed before attending elsewhere, and persistent
object memory allows later revisit.

Worth stating precisely, because the label alone could mislead: **the status is
"attention incomplete" on a literal reading of 830 remaining unseen cells, while
the residue is 18.2 times more seen-but-unmeasured than unseen.** Both facts are
recorded; neither is turned into a gate.

### Structural failures and code fixes

**No structural FAIL line**: `structural_fails: []` in both the report and the
comparator, `acquisitions_added: 0`, `object_1_read_only: true`,
`truth_opened: false`, all 54 pinned inputs byte-identical, object 141 unchanged
and pure.

**Code fixes: none.** No file was modified by this run.

One note on my own tooling, recorded for honesty rather than because it affected
any result: my first integrity-verification script mis-resolved the `fix_18` seed
acquisition, because MultiObject-1a stores its case as `acquisition/fix_18`
directly while MultiObject-1b/1b2 use `acquisitions/fix_NN/fix_NN`. That was a
defect in my scratchpad checker, not in the audit or the data; it was corrected to
handle both layouts, after which all 54 inputs verified byte-identical. No
repository file was involved.

### What this audit establishes, and what it does not

Established. **The two causes of residual frontier are now separated, and they
are not equally responsible.** After 24 looks, object 143's remaining shoreline
is **73.6% seen-but-unmeasured** (15,089 cells, 687 arcs) against **4.1%
genuinely unseen** (830 cells, 73 arcs, largest only 125 cells) — an **18.2 : 1**
ratio. **Raising the watchdog would therefore mostly buy more looks at surface
the instrument has already failed to measure**, which is precisely the conflation
the audit existed to prevent. The dominant residue is also **internal** (7,815
no-depth cells across 488 interior components), i.e. holes inside already-visited
territory rather than an outward frontier. And the audit did all of this
**read-only**: no acquisition, no fusion, object 141 and all 24 saved observations
byte-identical.

Not established. **No accuracy claim** — evaluator truth stayed closed, so every
number describes the representation, not the scene. **No threshold** — 830, 15,089
and 18.2 : 1 are measurements; nothing here says how much residue is acceptable,
and the disposition is deliberately independent of them. **Why stereo fails is not
explained here** — the audit reads the instrument's saved validity and introduces
no texture measure, matcher change, illumination change or layered occlusion
model. **The 830 unseen cells are not shown to be reachable**; whether another
look would resolve them is untested by construction. **`NO_RANGE_REFERENCE`
(3,665 cells) remains unclassified** by the inherited local-range rule.
`OBSERVED_TARGET_WITH_DEPTH` fired **once**, so that state is effectively
unexercised. And **nothing about objects 141, 142, 144 or 145 is established** —
discovery remains deferred, which is the next stage.

### Reproduction note (2026-09-22)

The prospective package was re-applied as `c29bcff`, which restored this document
to its pre-run state and removed the Results section below; the measured record
and the `docs/log.md` entry were untouched. The audit was therefore re-run from
the same unique parent into a fresh output on 2026-09-22 with the five
MultiObject-1c tool sources **byte-identical** to the original run
(`multiobject1c_public.py` `cf5ab2a1a0bca72a`, `_progress.py` `598d5d4d4987e0f0`,
`_audit.py` `c96944d7d2d244a7`, `_compare.py` `d6659e576e9ea8bd`,
`check_multiobject1c.py` `99e9eccb7a16fff1`) and every frozen source unchanged.

**The re-run reproduced the record exactly**: `object_143_epistemic_report.json`
and `object_143_epistemic_shoreline.png` are **byte-identical** to the originals
and the manifest matches on every path-independent field, with all **54** pinned
inputs again byte-identical and no Blender process. All checks and the six
mutation negatives passed again, with 13/13 prior suites green and 92/92 prior
negatives firing. The duplicate re-run directory was then removed so exactly one
`MultiObject1c-object143-epistemic-audit-v1` record exists, preserving the
"exactly one record" invariant a later step would scan for. The Results below are
the restored original text and remain correct as measured.

