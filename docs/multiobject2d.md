# MultiObject-2d — epistemic audit of the scene-selected third object

## Motivation

MultiObject-2c completed the full scene-memory -> selection -> seed -> growth chain for the third persistent object.  The selected object grew from **38,020** seed surfels to **310,884** surfels over 24 object fixations, remained pure, and left the two existing object maps byte-identical.  Its stereo regime was healthy: target depth recovery was **58.8–77.3%**, median **70.3%**, and the growth image showed filled interiors rather than the edge-lacework seen on the low-texture previous object.

But the frozen FSG6f policy still never returned `no_frontier`.  The run ended on the **24-object-fixation engineering watchdog**, with **650 of 679 frontier voxels still open**.  Good measurement therefore does not by itself imply local-policy termination.

Before spending more attention, MultiObject-2d asks what that remaining frontier means.

## Question

> After a well-measured scene object has grown densely but the frozen local policy still says `continue`, how much of its remaining cyclopean shoreline is genuinely unseen, how much is seen-but-unmeasured, and how much already carries boundary evidence?

This is a read-only audit, not another growth loop.

## Method

1. Consume `selected_object_id` from the completed MultiObject-2c parent; do not hand-pick the object id.
2. Load the selected-object surfel map read-only.
3. Build its cyclopean chart at the established 0.1 degree grid.
4. Reuse the angular footprint implied by the frozen 12 mm association radius at this object's own range.
5. Replay only the saved selected-object observation history: the MultiObject-2b seed and the MultiObject-2c growth looks.  No rendering and no fusion occur.
6. Reuse Cyclopean-1b shoreline states (`UNOBSERVED`, `PHYSICAL_DEPTH_BREAK`, `AMBIGUOUS`, ...).
7. Refine only base `UNOBSERVED` shoreline cells with the Cyclopean-1d observation/measurement states:
   - `NEVER_OBSERVED`
   - `OBSERVED_TARGET_NO_DEPTH`
   - `OBSERVED_TARGET_WITH_DEPTH`
   - `OBSERVED_NONTARGET_ONLY`
   - `MIXED_OBSERVATION`
   - `NO_RANGE_REFERENCE`

No texture threshold, completion interpolation, new geometric tolerance, matcher change or layered occlusion model is introduced.

## Scene-progress principle

The audit describes the selected object's unfinished business but **does not gate scene progress**.

- exterior `NEVER_OBSERVED` > 0 -> `ATTENTION_INCOMPLETE_RETAIN_FOR_REVISIT`
- no exterior `NEVER_OBSERVED`, but target-no-depth remains -> `ATTENTION_COMPLETE_MEASUREMENT_PARTIAL`
- neither remains -> `ATTENTION_COMPLETE_NO_TARGET_NO_DEPTH_RESIDUE`

In every case:

```text
scene_disposition = MOVE_TO_NEXT_OBJECT
```

The next stage is **next-object selection from updated scene memory**.  Any unfinished territory remains in persistent object memory for possible later revisit.

## Deliberately deferred

- watchdog extension or more growth looks;
- automatic scheduler/revisit policy;
- alternate stereo matcher, active illumination or texture rescue;
- completion interpolation or meshing;
- layered spherical depth for occlusion;
- evaluator truth or accuracy claims.

## Expected output

The record contains:

- `object_<id>_epistemic_report.json` — state counts, arcs and chart statistics;
- `object_<id>_epistemic_shoreline.png` — support plus epistemic shoreline visualization;
- `prediction_manifest.json` — integrity and scene-progress disposition.

The scientific question is descriptive: **is the remaining frontier mostly lack of attention, lack of measurement, or already-observed boundary structure?**  Whatever the answer, the scene tour continues.

## Results

Run 2026-09-22 on the workstation, **host-side only**. `MULTIOBJECT2D_COMPLETE`,
`structural_fails: []`, no FAIL line anywhere; the comparator agrees.

**The answer to the central question is an inversion of the previous object's.**
Of object 142's 2,055 shoreline cells, **986 (48.0%) are `NEVER_OBSERVED`** — all
of them exterior — against **125 (6.1%) `OBSERVED_TARGET_NO_DEPTH`**. The
remaining frontier is **primarily unobserved territory, 7.9x more unseen than
seen-but-unmeasured**, with a further **628 cells (30.6%) of already-resolved
boundary structure**. Object 143 measured the opposite way round: **18.2x more
seen-but-unmeasured than unseen**.

`object_status: ATTENTION_INCOMPLETE_RETAIN_FOR_REVISIT`,
`scene_disposition: MOVE_TO_NEXT_OBJECT`.

### Provenance

Working tree clean at the start. Package commit **`8ad0b50`** adds **exactly the
seven MultiObject-2d files, all `A`**; parent result **`9d96330`**.

Frozen audit at full scope: **every tracked non-documentation source present at
`9d96330` — 272 files** across `tools/`, `tools/dev/` and `scenes/` — was
compared. `git diff 9d96330 HEAD` over that set is **empty (0 lines)** and all
**272 sha256 are SAME**. The complete changed-file list between parent result and
HEAD is the seven new 2d files and nothing else. Key frozen sources:
`fsg6f_frontier.py` `d636c9405d719916…`, `scene_render_fix.py`
`6e70bbb78c1043ec…`, `reality2_render_fix.py` `9f1433d189fbcbb5…`,
`fsg3_surface_map.py` `1b9dbeb873105ec9…`, `cyclopean1a_topology.py`
`6ed00fca00907f33…`, `cyclopean1b_boundary.py` `b34371ce8ffa86c7…`,
`cyclopean1d_epistemic.py` `559351701151a144…`, `multiobject2c_run.py`
`e12b118e8ea08048…`.

The parent was located **by manifest**, not by assumed path: exactly one
`MultiObject2c-grow-selected-object-v1` record at seed 2111 with `truth_opened`
false — `previews/multiobject2c/full-seed2111` — carrying `selected_object_id`
**142**, `preexisting_object_ids` [141, 143], `selected_object_fixations_total`
**24**, steps **42..65**, `termination_reason` `object3_watchdog` and
`structural_fails []`.

### The object id is consumed, not hard-coded

`multiobject2d_audit.py:52` reads `int(m.get("selected_object_id", -1))` from the
parent manifest. **The literal `142` appears zero times in all five
MultiObject-2d sources.** The only textual matches for a hard-coded assignment
are inside the checker's own mutation strings at
[check_multiobject2d.py:34](tools/dev/check_multiobject2d.py#L34) and
[:72](tools/dev/check_multiobject2d.py#L72) — that is the `handpick` control, not
a code path.

### Read-only, and no acquisition

`grep -ci "blender|subprocess|bpy|cycles"` over `multiobject2d_audit.py` returns
**0**. No Blender process existed before or after the run (`pgrep` 0 both times);
**no acquisition, no fusion and no FSG6f policy loop ran**. The record contains
no acquisition directory.

**All 56 pinned inputs byte-identical afterwards** — 5 parent files
(`prediction_manifest.json` `e9aa28e9c5b0c10d…`, `object_142_surface_map.npz`
`6f90d985f8078a7d…`, `scene_graph.json` `725a101c12f78a9f…`,
`scene_cyclopean_footprints.npz` `5dc5afa23f929bcf…`,
`object_142_policy_trace.json` `11033cbccd005f0f…`), **3 scene-object geometry
sources**, and **all 48 saved selected-object calibration/observation files**
(24 looks x 2). The audit's own internal guards assert the same thing three
times over, and all three passed.

Objects verified pure: **141** 155,684 ids `{141}`, **143** 42,988 ids `{143}`,
**142** 310,884 ids `{142}` — all `SURFEL_MAP`, all unchanged. Manifest records
`acquisitions_added: 0`, `growth_iterations_added: 0`, `watchdog_changed: false`,
`parent_files_modified: false`, `scene_objects_read_only: true`,
`selected_object_read_only: true`, `truth_opened: false`,
`quality_gate_used: false`, `automatic_scene_scheduler: false`,
`automatic_object_discovery: false`.

### Environment and wall time

Host `.venv/bin/python` 3.12.3 on the workstation. **No Blender, no Cycles, no
GPU** — this step is pure host computation. The audit itself took **4.5 s**,
replaying 24 saved looks through `compute_once`.

### Checks

`py_compile` clean on all five modules; `multiobject2d_progress.py --self-test`
passes. The three prescribed lines appeared verbatim:

```text
[multiobject2d-audit] PASS read_only=true parent_selected_object=true observation_separate_from_depth=true no_watchdog_extension=true
[multiobject2d-progress] PASS descriptive_only=true scene_progress_unblocked=true next=next_object_selection
[multiobject2d-check] SUMMARY passed=6 failed=0
```

All **seven** negatives are genuine source-mutation controls, each exiting **1**
with exactly the detector the contract names, **none exiting 2**:

| negative | rc | detected by |
|---|---|---|
| `acquire` | 1 | `read_only_no_acquisition` |
| `handpick` | 1 | `parent_selected_object_not_handpicked` |
| `crossobject` | 1 | `scene_objects_read_only_selected_only_audit` |
| `depthonly` | 1 | `observation_separate_from_depth` |
| `threshold` | 1 | `frozen_scale_no_new_threshold` |
| `watchdog` | 1 | `watchdog_not_extended_scene_progress_unblocked` |
| `qualitygate` | 1 | `watchdog_not_extended_scene_progress_unblocked` |

The **exit-2 escape branch was verified live**, not assumed: an inert mutation
applied to a scratch copy of the audit source was detected by **no** check, which
is precisely the condition under which the checker prints
`ERROR ... mutation escaped detection` and exits 2.

**No regression**: **21/21** prior suites green and **135/135** prior negatives
still firing — multiobject2c 6/6 (7 neg), 2b, 2a, 1c, 1a 6/6 (6 neg each),
1b2 6/6 (7 neg), 1b 6/6 (6 neg), cyclopean1g..1a 6/6 (6 neg each),
reality2b 7/7 (10 neg), reality2 7/7 (7 neg), reality1 6/6 (6 neg),
fsg6f 14/14 (15 neg), fsg3 5/5 (4 neg), fsg_supported 46/46 (4 neg),
fsg_hdr 34/34 (3 neg). The **cyclopean1f caveat still stands unchanged**: its six
negatives print and exit 1 unconditionally, as recorded since 1f; they were run
and they exit 1, but they remain the one suite whose negatives are not
mutation-driven.

### Scope: the selected object, its own history, nothing else

`observation_count` **24**, `observation_steps` **42..65** — the MultiObject-2b
seed at global step 42 plus the 24-1 MultiObject-2c growth looks, contiguous with
no gap. The audit's own guard rejects a non-contiguous or miscounted history. The
two pre-existing objects were opened only to verify purity and hash, never
analysed as the active target.

### Chart and inherited scale — no new tolerance

Object-scoped cyclopean chart **612 x 171** cells, grid **0.1 deg**, `yaw0`
**-30.20**, `pitch0` **-25.60**; total 104,652 cells.

The footprint is derived from the **unchanged 12 mm association radius** at this
object's own range, exactly as inherited:

```text
association_radius_m = 0.012          (frozen, = parent FUSION, = policy frontier_state_radius_m)
object 142 range min/median/max = 1.3565 / 2.4113 / 4.0649 m
atan(0.012 / 2.4113) = 0.2851310 deg  ->  / 0.1 deg = 2.85 cells  ->  3 cells
report footprint_radius_deg = 0.2851309 deg, footprint_cells = 3
```

The recomputed and reported angles differ by **1.7e-8 deg**, far below one grid
cell, and both round to the same 3 cells. **No new threshold, tolerance, texture
gate, interpolation or occlusion model was introduced**; the `threshold` negative
exists to enforce that and fires.

Support: map **310,884** points -> raw support **62,784** cells (identical to the
footprint cell count MultiObject-2c published, an independent cross-check) ->
support after footprint dilation **79,416**, complement **25,236**, shoreline
**2,055**.

### Base shoreline states (Cyclopean-1b, unchanged)

| state | cells | share |
|---|---|---|
| `UNOBSERVED` | 1,427 | 69.4% |
| `PHYSICAL_DEPTH_BREAK` | 537 | 26.1% |
| `AMBIGUOUS` | 91 | 4.4% |
| `TARGET_CONTINUATION` | 0 | 0.0% |
| **total** | **2,055** | |

**`TARGET_CONTINUATION` is empty.** Nowhere on this object's shoreline does the
evidence say the target simply continues past the mapped edge — a first
difference from the cloth object.

### Refined states (Cyclopean-1d, unchanged), split exterior / internal

Applied only to the 1,427 base-`UNOBSERVED` cells, as the contract requires.

| refined state | all | exterior | internal |
|---|---|---|---|
| `NEVER_OBSERVED` | **986** | **986** | 0 |
| `NO_RANGE_REFERENCE` | 291 | 284 | 7 |
| `OBSERVED_TARGET_NO_DEPTH` | 125 | 26 | **99** |
| `OBSERVED_NONTARGET_ONLY` | 25 | 25 | 0 |
| `OBSERVED_TARGET_WITH_DEPTH` | 0 | 0 | 0 |
| `MIXED_OBSERVATION` | 0 | 0 | 0 |
| **total** | **1,427** | **1,321** | **106** |

Two clean zeros: **no cell is `OBSERVED_TARGET_WITH_DEPTH`** (nothing was
measured and then left outside support) and **no cell is `MIXED_OBSERVATION`**
(no shoreline cell saw both target and non-target evidence). The internal
remainder is almost entirely **seen-but-unmeasured**: 99 of 106 internal cells.

Components: **25** — one `EXTERIOR` of 25,129 cells with maximum border depth
**59** cells, and **24 `INTERNAL`** holes of 1 to 34 cells each (median 2).

### Arcs, and the inherited exterior border-depth structure

**316 arcs** in total.

| kind | state | arcs | cells |
|---|---|---|---|
| EXTERIOR | `NEVER_OBSERVED` | **6** | **986** |
| EXTERIOR | `NO_RANGE_REFERENCE` | 258 | 284 |
| EXTERIOR | `OBSERVED_TARGET_NO_DEPTH` | 6 | 26 |
| EXTERIOR | `OBSERVED_NONTARGET_ONLY` | 18 | 25 |
| INTERNAL | `OBSERVED_TARGET_NO_DEPTH` | 24 | 99 |
| INTERNAL | `NO_RANGE_REFERENCE` | 4 | 7 |

**The unobserved frontier is six large arcs, not scattered slivers.** Sizes
**3 / 181.5 / 339** (min / median / max), mean 164.3; four arcs carry 978 of the
986 cells.

| cells | border depth | centroid yaw | centroid pitch | yaw span | pitch span | supported projections |
|---|---|---|---|---|---|---|
| 339 | **59** | -4.59 | -20.59 | 26.2 deg | 5.2 deg | 0 |
| 276 | 21 | -26.59 | -20.00 | 12.0 deg | 16.4 deg | 0 |
| 239 | 16 | +28.64 | -19.76 | 9.9 deg | 15.7 deg | 0 |
| 124 | 7 | +14.94 | -25.26 | 11.7 deg | 0.8 deg | 0 |
| 5 | 25 | -18.48 | -23.30 | 0.2 deg | 0.5 deg | 0 |
| 3 | 4 | +8.20 | -25.20 | 0.3 deg | 0.1 deg | 0 |

Inherited exterior border depth over these arcs: min **4**, median **18.5**, max
**59** — and **59 is the chart-wide maximum**, so the deepest unobserved arc sits
at the deepest point of the exterior complement. Cell-weighted mean depth
**31.1** cells. **Every one of the six has `supported_projection_samples` = 0**:
across all 24 completed views, no supported projection ever landed on any of
these cells. That is the state's definition satisfied at its strongest — not
"observed and ambiguous" but never reached at all.

Evidence totals by state confirm the separation of observation from measurement:
`OBSERVED_TARGET_NO_DEPTH` has **156 supported projections, 156 target-seen, 0
with valid depth**; `OBSERVED_NONTARGET_ONLY` has 71 supported projections all
non-target; `NEVER_OBSERVED` and `NO_RANGE_REFERENCE` have 0.

**Where the unobserved territory lies is structural, and measurable.** The 2c
gaze lattice actually visited yaw **[-21.000, +24.000]**, pitch **[-18.811,
-8.811]**, while the object's chart spans yaw [-30.20, +31.00], pitch [-25.60,
-8.50]. **All six arcs lie below the lowest gaze row**, and two of them also
beyond the leftmost and rightmost gaze — **986 of 986 cells (100%)** sit in arcs
whose centroid is outside the span the lattice reached. The frozen policy
proposed only three distinct pitches across its 24 decisions — **-8.811 (10x),
-13.811 (9x), -18.811 (5x)** — and **never proposed a row below -18.811**, with
`delta_pitch_deg` 0.0 at 15 of 24 decisions. Recorded as an observation about
where this run's attention went; **nothing was changed in response.**

### Inherited final policy decision (context only)

From the parent's own trace, unmodified: at `global_step` **65**,
`object_fixation_index` **23**, `reason` **`continue`**, `stop` **false**.
Frontier **679** = **650 open** + 16 map-resolved + 13 boundary-resolved;
`next_gaze_deg` **(+8.9996, -18.8109)**; selected candidate `delta_yaw_deg` -5.0,
`delta_pitch_deg` **0.0**, `frontier_score` 45.79, predicted new angular area
7.20 deg^2, continuation corridor fraction **1.0** binocular;
`frontier_state_radius_m` **0.012** — the same 12 mm this audit reuses. The
policy returned `continue` at **all 24** decisions and never `no_frontier`.

**This audit explains that `continue` without endorsing it**: 650 voxels stayed
open, and 986 shoreline cells were never observed, all of them outside the rows
and columns the lattice actually visited. The policy was not wrong that work
remained.

### Visual reading, descriptive

`object_142_epistemic_shoreline.png` (612 x 171, upscaled 3x). A pixel census of
the rendered image reproduces the report exactly — 79,416 support, 986
`NEVER_OBSERVED`, 537 `PHYSICAL_DEPTH_BREAK`, 291 `NO_RANGE_REFERENCE`, 125
`OBSERVED_TARGET_NO_DEPTH`, 91 `AMBIGUOUS`, 25 `OBSERVED_NONTARGET_ONLY`, 23,181
background, summing to all 104,652 chart cells — an independent cross-check of
the numbers against the picture.

The picture reads plainly. A broad solid grey slab of mapped surface fills most
of the frame. Along the **entire top edge** runs a thin continuous **blue** line:
`PHYSICAL_DEPTH_BREAK`, the object's far edge resolved against the background —
**already-observed boundary structure, not missing attention**. The **left,
right and bottom** edges are a continuous **red** rim of `NEVER_OBSERVED`, with a
large white notch at bottom-centre where support has not closed between the two
lower lobes. The interior is essentially solid, carrying only **orange speckle**
— the 125 `OBSERVED_TARGET_NO_DEPTH` cells as isolated pinholes, nothing
structural. **750 of the 986 unobserved cells (76%) lie in the bottom third of
the picture.**

So the epistemic picture matches the growth picture MultiObject-2c produced:
filled interior, thin rim, and the unfinished business pushed to the margin.

### Status and disposition

`multiobject2d_progress.object_status` applied its literal, threshold-free rule:
exterior `NEVER_OBSERVED` = 986 > 0, therefore
**`ATTENTION_INCOMPLETE_RETAIN_FOR_REVISIT`**. No count was compared against any
threshold; the rule reads only "greater than zero", and `quality_gate_used` is
false.

**`scene_disposition = MOVE_TO_NEXT_OBJECT`**, unconditionally, as the contract
requires. `next_stage: next-object selection from updated scene memory`. The
comparator independently re-asserts that scene progress was not blocked.

`tools/multiobject2d_compare.py` on the completed record printed
**`MULTIOBJECT2D_COMPLETE`** with `"structural_fails": []` and exited **0**.

### Structural failures and code fixes

**Structural failures: none.** `structural_fails: []` in both the manifest and
the comparator; all 56 pinned inputs byte-identical; all three scene objects pure
and unchanged; zero acquisitions; watchdog untouched; truth closed.

**Code fixes: none.** No MultiObject-2d file needed repair and no frozen prior
source was modified. The package ran as applied.

One inherited artifact, unchanged and re-proved harmless: the NaN->int64 cast
`RuntimeWarning` at
[cyclopean1a_topology.py:117-118](tools/cyclopean1a_topology.py#L117-L118)
appeared twice in the console (Python's default per-location deduplication; 48
occurrences with `simplefilter("always")`, two per look across 24 looks), raised
because **40.47%** of observation pixels carry non-finite `xyz`. Harmless by
inspection — `_indices` discards those lanes through an explicit
`np.isfinite(yaw) & np.isfinite(pitch)` term — and by measurement: a
NaN-prefiltered rebuild produced **bitwise-identical** `seen_target`,
`seen_nontarget`, `target_range_m` and `nontarget_range_m`. **The parent was not
edited.**

### What this establishes, and what it does not

Established, descriptively. **After dense, well-measured growth, object 142's
remaining frontier is primarily unobserved territory.** Of 2,055 shoreline cells,
**986 (48.0%) were never observed at all** — zero supported projections across all
24 completed views — **628 (30.6%) are already-resolved boundary structure**
(`PHYSICAL_DEPTH_BREAK` 537 + `AMBIGUOUS` 91), and only **125 (6.1%) are
seen-but-unmeasured**. **7.9x more unseen than seen-but-unmeasured.**

**This is the inverse of the previous object.** On object 143 the same audit
found **830 `NEVER_OBSERVED` against 15,089 `OBSERVED_TARGET_NO_DEPTH` — 18.2x
more seen-but-unmeasured than unseen** — and on object 141, Cyclopean-1f drove
exterior `NEVER_OBSERVED` to **zero**, leaving only a seen-but-unmeasured emblem.
Three objects, three different remainders, under one unchanged vocabulary: **the
epistemic bottleneck is a property of the object and the attention it received,
not of the instrument.** The shoreline sizes say the same thing — object 143's
shoreline (20,799 cells) **exceeded** its own mapped footprint (17,947), the
signature of lacework; object 142's shoreline (2,055) is **3.3%** of its
footprint (62,784), the signature of a filled region with a thin rim.

Established structurally. **The unobserved remainder is where the gaze lattice
did not go**: six large contiguous arcs, all below the lowest visited pitch row
and two beyond the visited yaw extremes, **100% of unobserved cells** outside the
lattice span, with the deepest arc at the chart-wide maximum border depth of 59
cells. The frozen policy never proposed a row below -18.811 deg.

Not established. **This is descriptive, not a diagnosis**: it does not show
*why* the lattice stopped short, whether more looks would reach those arcs, or
that the policy is deficient — no counterfactual was run and **nothing was
tuned**. **No accuracy claim** — evaluator truth stayed closed; these are counts
of the representation, not of the scene. **No object completeness** — 986
unobserved cells bound attention, not geometry. **No claim that the 125
seen-but-unmeasured cells are irreducible** — Cyclopean-1g showed re-centering did
not recover such a residue on object 141, but no alternate matcher, baseline,
vergence or illumination was tried here either, **by design**. **`NO_RANGE_REFERENCE`
(291 cells, 258 of them single-cell exterior arcs) is a bookkeeping state, not a
finding** — it marks where the inherited local target-boundary range is undefined.
And **the counts gated nothing**: `object_status` came from a literal
zero-comparison and `scene_disposition` is `MOVE_TO_NEXT_OBJECT` regardless.

**Next: next-object selection from updated scene memory.** Object 142 stays in
persistent memory as `ATTENTION_INCOMPLETE_RETAIN_FOR_REVISIT`; whether to revisit
it, and whether the lattice's pitch reach deserves attention, is a judgement for
Luiz/Chat. The scene tour proceeds.
