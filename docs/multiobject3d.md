# MultiObject-3d — epistemic audit of the first frozen-policy stop

## Motivation

MultiObject-3c repeated the unchanged selected-object growth machinery on the fourth persistent scene entity.  On the current seed-2111 record the target grew from **3,662** to **6,426** pure surfels, while all prior object maps stayed byte-identical.  Its stereo recovery remained low (**1.3–9.6%**, median about **6.7%**), and the Reality-2b valid-empty-look path fired four times.

For the first time in this multi-object series, however, frozen FSG6f reached its own stop before the engineering watchdog:

```text
termination_reason = no_frontier
scientific_stop_reached = true
selected-object fixations = 13 / 24
```

The final trace still contained **30 OPEN frontier voxels out of 72**, but `candidates_before_consensus_count = 0`: no admissible next gaze existed under the unchanged controller.

That makes this an important distinction to audit rather than interpret by label alone.

## Central question

> Did `no_frontier` coincide with attention completion, or did the policy exhaust its admissible actions while genuinely unseen territory remained?

This is a **read-only stop audit**.  It does not rescue, extend, or modify the stopped policy.

## Method

1. Consume `selected_object_id` from the completed MultiObject-3c parent; do not hard-code a scene id.
2. Require the parent to be the declared `no_frontier` scientific stop reached before the 24-look engineering watchdog.
3. Load the selected-object surfel map read-only.
4. Replay only the saved selected-object observation history: the MultiObject-3b seed plus the MultiObject-3c growth looks.  No rendering or fusion occurs.
5. Rebuild the existing 0.1° cyclopean chart and reuse the angular footprint implied by the unchanged 12 mm association radius at this object's own range.
6. Reuse Cyclopean-1b shoreline states and refine only base `UNOBSERVED` cells with the unchanged Cyclopean-1d observation-versus-measurement states.
7. Reconstruct the **final frozen FSG6f decision exactly** from the saved final observation, saved gaze history, final map and saved binocular observation history.  Counts and stop fields must match the parent's policy trace before any interpretation is made.
8. Reconstruct the frozen final 3D frontier and angularly quantize each look-ahead target onto the unchanged 0.1° cyclopean chart.  Report which epistemic cell each `OPEN`, `MAP_RESOLVED`, and `BOUNDARY_RESOLVED` target coincides with.

The 3D-frontier/cyclopean relation is descriptive.  It introduces no distance threshold: it is simply the existing look-ahead target direction quantized by the existing chart rule.

## Stop interpretation

No fitted threshold is used.

- exterior `NEVER_OBSERVED > 0` at a genuine `no_frontier` stop -> `POLICY_EXHAUSTED_WITH_UNSEEN_TERRITORY`;
- otherwise, if target-no-depth remains -> `ATTENTION_COMPLETE_MEASUREMENT_PARTIAL_AT_POLICY_STOP`;
- otherwise -> `ATTENTION_COMPLETE_AT_POLICY_STOP`.

This interpretation describes the stopped object's state.  It does **not** change the scene-level disposition.

## Scene-progress principle

In every case:

```text
scene_disposition = MOVE_TO_NEXT_OBJECT
```

Unresolved territory remains persistent and can later participate in a revisit policy.  This increment does not create that policy.

## Deliberately deferred

- any rescue fixation after the frozen stop;
- watchdog extension;
- changes to FSG6f candidate generation, consensus, corridor rules, or lattice;
- alternate matcher, baseline, vergence, illumination, or active texture;
- interpolation, mesh completion, layered occlusion, or evaluator truth;
- object discovery, revisit scheduling, or scene scheduling.

## Expected output

The record contains:

- `object_<id>_epistemic_stop_report.json` — shoreline census, refined arcs, exact final-policy replay and 3D-frontier/cyclopean relation;
- `object_<id>_epistemic_stop_shoreline.png` — selected-object support and epistemic shoreline;
- `prediction_manifest.json` — integrity, stop interpretation, relation summary and unconditional scene disposition.

The experiment is successful structurally only if it remains read-only and reproduces the saved frozen-policy stop exactly.  The scientific result is whatever the saved evidence says about the residual state.

## Results

Run 2026-09-22 on the workstation, **host-side only**. `MULTIOBJECT3D_COMPLETE`,
`structural_fails: []`, no FAIL line anywhere; the comparator agrees and exits 0.

**The answer to the central question is unambiguous:
`POLICY_EXHAUSTED_WITH_UNSEEN_TERRITORY`.** The first `no_frontier` stop did
**not** mean attention completion. **20 exterior `NEVER_OBSERVED` cells remain**,
in **two arcs**, both with **zero supported projections** across all 13 completed
views — and both lying **outside** the rectangular envelope of visited gazes,
**0.98 to 3.98 degrees beyond the rightmost gaze**.

The sharpest finding is the relation, not the count. **All 30 final OPEN 3D
frontier targets lie inside the visited gaze envelope — none outside — and not
one of them lands on a `NEVER_OBSERVED` cell.** Seventeen of the thirty quantize
onto cells that are **already mapped support**. The frontier the policy consults
was not pointing at the unseen territory at all.

`object_status: ATTENTION_INCOMPLETE_RETAIN_FOR_REVISIT`,
`scene_disposition: MOVE_TO_NEXT_OBJECT`.

### Provenance

Working tree clean at the start. Package commit **`6e5a1c7`** adds **exactly the
seven MultiObject-3d files, all `A`**; parent result **`b3c2186`**.

Frozen audit at full scope: **every tracked non-documentation source present at
`b3c2186` — 291 files** across `tools/`, `tools/dev/` and `scenes/`.
`git diff b3c2186 HEAD` over that set is **empty (0 lines)** and all **291 sha256
are SAME**. The complete changed-file list between parent result and HEAD is the
seven new 3d files and nothing else. Key frozen sources:
`multiobject2c_policy.py` `f4d4a08b00981466…` (the adapter the replay runs
through), `fsg6f_frontier.py` `d636c9405d719916…`, `cyclopean1a_topology.py`
`6ed00fca00907f33…`, `cyclopean1b_boundary.py` `b34371ce8ffa86c7…`,
`cyclopean1d_epistemic.py` `559351701151a144…`, `fsg3_surface_map.py`
`1b9dbeb873105ec9…`, `scene_render_fix.py` `6e70bbb78c1043ec…`,
`reality2_render_fix.py` `9f1433d189fbcbb5…`, `multiobject3c_run.py`
`553cadd6b33a6ec8…`.

The parent was located **by manifest**: exactly one
`MultiObject3c-grow-selected-object-v1` record —
`previews/multiobject3c/full-seed2111` — seed **2111**, `truth_opened` **false**.
**All three required stop conditions hold:** `termination_reason`
**`no_frontier`**, `scientific_stop_reached` **true**, and
`selected_object_fixations_total` **13** strictly below
`watchdog_selected_object_fixations` **24**. The audit's own guard enforces each
one and would have stopped otherwise.

### The object id is consumed, not hard-coded

`multiobject3d_audit.py:56` reads `int(m.get("selected_object_id", -1))` from the
parent manifest. **The literal `145` appears zero times in all five
MultiObject-3d sources — including the checker**, which enforces the invariant
structurally without naming the value.

### Read-only, and no acquisition

`grep -cil "subprocess|blender|bpy|cycles"` over `multiobject3d_audit.py` returns
**0**. No Blender process existed before or after (`pgrep` 0 both times). **No
acquisition, no fusion, no watchdog change and no growth-policy action** — the
record contains no acquisition directory, and the manifest records
`acquisitions_added` **0**, `growth_iterations_added` **0**, `watchdog_changed`
**false**, `parent_files_modified` **false**.

**All 35 pinned inputs byte-identical afterwards** — 5 parent files
(`prediction_manifest.json` `3b44f9c87eebdaac…`, `object_145_surface_map.npz`
`8c9e7ffada6fb6a7…`, `scene_graph.json` `55039411671c52b5…`,
`scene_cyclopean_footprints.npz` `c9dc9a3de8f871fa…`,
`object_145_policy_trace.json` `a7414fd6b6f0c41f…`), **4 scene-object geometry
sources**, and **all 26 saved selected-object calibration/observation files**
(13 looks x 2). The audit's own three internal guards assert the same, and all
passed.

Objects verified pure: **141** 155,684 `{141}`, **142** 310,884 `{142}`, **143**
42,988 `{143}`, **145** 6,426 `{145}`.

### Environment and wall time

Host `.venv/bin/python` 3.12.3. **No Blender, no Cycles, no GPU.** The audit took
**2.7 s**, replaying 13 saved looks and reconstructing the final policy decision.

### Checks

`py_compile` clean on all five modules; the progress self-test passes. The three
prescribed lines appeared verbatim:

```text
[multiobject3d-audit] PASS read_only=true parent_policy_stop=true observation_separate_from_depth=true stop_replay=true
[multiobject3d-progress] PASS descriptive_only=true scene_progress_unblocked=true next=next_object_selection
[multiobject3d-check] SUMMARY passed=7 failed=0
```

All **eight** negatives are genuine source-mutation controls, each exiting **1**
with exactly the detector the contract names; **none exited 2**:

| negative | rc | detected by |
|---|---|---|
| `acquire` | 1 | `read_only_no_acquisition` |
| `handpick` | 1 | `parent_selected_policy_stop_not_handpicked` |
| `crossobject` | 1 | `scene_objects_read_only_selected_only_audit` |
| `depthonly` | 1 | `observation_separate_from_depth` |
| `stopreplay` | 1 | `final_policy_stop_replayed_and_related` |
| `threshold` | 1 | `frozen_scale_no_new_threshold` |
| `watchdog` | 1 | `watchdog_not_extended_scene_progress_unblocked` |
| `qualitygate` | 1 | `watchdog_not_extended_scene_progress_unblocked` |

The **exit-2 escape branch was verified live**: an inert mutation on a scratch
copy of the audit source was detected by **no** check — exactly the condition
under which the checker prints `ERROR ... mutation escaped detection` and exits 2.

**No regression**: **25/25** prior suites green and **162/162** prior negatives
still firing, **none weakened**. The **Cyclopean-1f caveat stands as a standing
caveat and 1f was not edited**.

### Scope: the selected object, its own history

`observation_count` **13**, `observation_steps` **66..78** — the MultiObject-3b
seed at step 66 plus the twelve MultiObject-3c growth looks, contiguous. The
audit's guard rejects a non-contiguous or miscounted history. The three
pre-existing objects were opened only to verify purity and hash.

### Chart and inherited scale — no new tolerance

Object-scoped cyclopean chart **104 x 154** cells, grid **0.1 deg**, `yaw0`
**+15.10**, `pitch0` **−7.20**; 16,016 cells total.

Footprint from the **unchanged 12 mm association radius** at this object's own
range:

```text
association_radius_m = 0.012   (= parent FUSION = policy frontier_state_radius_m)
object 145 median range = 2.7627 m
atan(0.012 / 2.7627) = 0.2488695 deg  ->  / 0.1 = 2.49 cells  ->  3 cells
report footprint_radius_deg = 0.2488695386, footprint_cells = 3
```

**No new threshold, tolerance, texture gate, interpolation or occlusion model was
introduced**; the `threshold` negative enforces that and fires.

Support: map **6,426** points -> raw support **2,041** cells (identical to the
footprint cell count MultiObject-3c published) -> support after footprint
dilation **9,198**, complement **6,818**, shoreline **2,516**.

### Exact final FSG6f stop replay

Reconstructed from the final map, the final saved observation, the complete
13-gaze list and the saved binocular history, through the **unchanged**
`multiobject2c_policy.py` adapter. **All eleven compared fields matched exactly**:

| field | saved | replayed | match |
|---|---|---|---|
| `stop` | True | True | ✓ |
| `reason` | `no_frontier` | `no_frontier` | ✓ |
| `frontier_voxel_count` | 1368 | 1368 | ✓ |
| `frontier_count` | 72 | 72 | ✓ |
| `frontier_raw_count` | 72 | 72 | ✓ |
| `frontier_map_resolved_count` | 1 | 1 | ✓ |
| `frontier_boundary_resolved_count` | 41 | 41 | ✓ |
| `frontier_open_count` | 30 | 30 | ✓ |
| `candidates_before_consensus_count` | **0** | **0** | ✓ |
| `consensus_rejected_candidate_count` | 0 | 0 | ✓ |
| `next_gaze_deg` | null | null | ✓ |

Plus an independent re-extraction of the frontier itself: `extract_frontier` and
`classify_frontier_state` reproduced **72** frontier entries partitioned **30
open / 1 map-resolved / 41 boundary-resolved**, matching the replayed decision.
Saved `current_gaze_deg` **(+10.822, −9.999)** agrees with the last gaze in the
history; final `global_step` **78**, `object_fixation_index` **12**,
`frontier_state_radius_m` **0.012**.

**The stop is genuine and reproducible.** `candidates_before_consensus_count = 0`
means the controller generated **no candidate at all** — not that candidates were
generated and rejected (`consensus_rejected_candidate_count` is also 0).

### Base shoreline states (Cyclopean-1b, unchanged)

| state | cells | share |
|---|---|---|
| `UNOBSERVED` | 2,416 | 96.0% |
| `PHYSICAL_DEPTH_BREAK` | 55 | 2.2% |
| `AMBIGUOUS` | 45 | 1.8% |
| `TARGET_CONTINUATION` | 0 | 0.0% |
| **total** | **2,516** | |

### Refined states (Cyclopean-1d, unchanged), exterior / internal

Applied only to the 2,416 base-`UNOBSERVED` cells.

| refined state | all | exterior | internal |
|---|---|---|---|
| `OBSERVED_TARGET_NO_DEPTH` | **1,514** | 1,043 | 471 |
| `NO_RANGE_REFERENCE` | 720 | 561 | 159 |
| `OBSERVED_NONTARGET_ONLY` | 142 | 142 | 0 |
| **`NEVER_OBSERVED`** | **20** | **20** | 0 |
| `MIXED_OBSERVATION` | 20 | 20 | 0 |
| `OBSERVED_TARGET_WITH_DEPTH` | 0 | 0 | 0 |
| **total** | **2,416** | **1,786** | **630** |

Whole-shoreline composition: **`OBSERVED_TARGET_NO_DEPTH` 60.2%**,
`NO_RANGE_REFERENCE` 28.6%, `OBSERVED_NONTARGET_ONLY` 5.6%, observed boundary
structure (`PHYSICAL_DEPTH_BREAK` + `AMBIGUOUS`) 4.0%, **`NEVER_OBSERVED` 0.8%**,
`MIXED_OBSERVATION` 0.8%.

**Seen-but-unmeasured outnumbers unseen 75.7 to 1** — the most extreme ratio in
the programme so far. Evidence totals confirm the separation:
`OBSERVED_TARGET_NO_DEPTH` carries **4,633 supported projections, all
target-seen, 0 with valid depth**; `NEVER_OBSERVED` and `NO_RANGE_REFERENCE`
carry **0** supported projections.

Components: **16** — one `EXTERIOR` of 5,618 cells with maximum border depth
**47**, and **15 `INTERNAL`** holes with sizes 1, 1, 1, 1, 2, 2, 2, 3, 8, **154,
180, 190, 203, 221, 231** — the six large internal components are the gaps
between the fronds of the structure.

### Arcs, and the exterior `NEVER_OBSERVED` territory

**613 arcs** in total.

| kind | state | arcs | cells |
|---|---|---|---|
| EXTERIOR | `OBSERVED_TARGET_NO_DEPTH` | 28 | 1,043 |
| EXTERIOR | `NO_RANGE_REFERENCE` | 402 | 561 |
| EXTERIOR | `OBSERVED_NONTARGET_ONLY` | 43 | 142 |
| EXTERIOR | **`NEVER_OBSERVED`** | **2** | **20** |
| EXTERIOR | `MIXED_OBSERVATION` | 16 | 20 |
| INTERNAL | `OBSERVED_TARGET_NO_DEPTH` | 15 | 471 |
| INTERNAL | `NO_RANGE_REFERENCE` | 107 | 159 |

**The unseen territory is two small, compact arcs:**

| cells | border depth | centroid yaw | centroid pitch | yaw span | pitch span | supported projections | inside gaze envelope | nearest visited gaze |
|---|---|---|---|---|---|---|---|---|
| 13 | 17 | **+24.22** | −5.69 | 1.2 deg | 0.5 deg | **0** | **false** | **6.628 deg** |
| 7 | 16 | **+22.10** | −5.74 | 0.7 deg | 0.4 deg | **0** | **false** | **5.884 deg** |

Inherited exterior border depth **16–17** (cell-weighted mean 16.65) against a
chart-wide maximum of **47** — so these are *not* the deepest pockets of the
exterior complement. Both have **zero supported projections**: across all 13
completed views, no supported projection ever landed on them.

**Both arcs lie outside the visited gaze envelope.** The envelope is yaw
**[+10.822, +20.822]**, pitch **[−9.999, +10.001]**; the unseen cells occupy yaw
**[+21.80, +24.80]**, pitch **[−5.90, −5.50]** — **0.98 to 3.98 degrees beyond
the rightmost gaze**, at L2 distances of **5.88** and **6.63** degrees from the
nearest completed fixation.

### The 3D frontier / cyclopean relation — the decisive measurement

Each frozen look-ahead target was angularly quantized onto the unchanged
0.1-degree chart. No distance threshold was introduced.

| frontier state | total | cyclopean cell class |
|---|---|---|
| **OPEN** | **30** | **`SUPPORT` 17**, `COMPLEMENT_NONSHORELINE` 6, `OBSERVED_TARGET_NO_DEPTH` 5, `OBSERVED_NONTARGET_ONLY` 1, `NO_RANGE_REFERENCE` 1 |
| `MAP_RESOLVED` | 1 | `SUPPORT` 1 |
| `BOUNDARY_RESOLVED` | 41 | `OUT_OF_CHART` 38, `COMPLEMENT_NONSHORELINE` 3 |

**Gaze-envelope relation: 30 of 30 OPEN targets fall inside the visited gaze
envelope; 0 fall outside.** Their distance to the nearest completed gaze is
**min 0.620, median 2.112, max 4.365 degrees** — every one of them is well within
the region already looked at.

**Not one OPEN target lands on a `NEVER_OBSERVED` cell.** Seventeen land on cells
that are **already mapped support**; six on complement cells that are not even on
the shoreline; five on `OBSERVED_TARGET_NO_DEPTH`; one each on
`OBSERVED_NONTARGET_ONLY` and `NO_RANGE_REFERENCE`.

That is the mechanism-level answer. The unseen arcs sit ~6 degrees to the right
of everywhere the observer looked, while the 3D frontier's remaining OPEN voxels
cluster **inside** the visited region and mostly point at surface the map already
holds. **The policy did not decline to go to the unseen territory — it had no
representation of it to act on.**

### Stop interpretation, status and disposition

`multiobject3d_progress.stop_interpretation` applied its literal zero/non-zero
rule: the parent is the declared `no_frontier` stop, and exterior
`NEVER_OBSERVED` = 20 > 0, therefore
**`POLICY_EXHAUSTED_WITH_UNSEEN_TERRITORY`**.

`object_status` from the same literal rule: 20 > 0, therefore
**`ATTENTION_INCOMPLETE_RETAIN_FOR_REVISIT`**. **No count was compared against
any threshold**; `quality_gate_used` is false.

**`scene_disposition = MOVE_TO_NEXT_OBJECT`**, unconditionally, as the contract
requires. `next_stage: next-object selection from updated scene memory`. The
comparator independently re-asserts that scene progress was not blocked, that the
parent stop was `no_frontier`, and that
`final_policy_stop_replayed_exactly` is true.

`tools/multiobject3d_compare.py` printed **`MULTIOBJECT3D_COMPLETE`** with
`"structural_fails": []` and exited **0**.

### Visual reading, descriptive

`object_145_epistemic_stop_shoreline.png` (104 x 154, 3x). A pixel census
reproduces the report **exactly on all eight classes** — 9,198 support, 1,514
`OBSERVED_TARGET_NO_DEPTH`, 720 `NO_RANGE_REFERENCE`, 142
`OBSERVED_NONTARGET_ONLY`, 55 `PHYSICAL_DEPTH_BREAK`, 45 `AMBIGUOUS`, 20
`MIXED_OBSERVATION`, 20 `NEVER_OBSERVED`, 4,302 background, summing to all
16,016 chart cells.

The picture explains the structure at a glance. The mapped support is **not a
blob but a comb**: a solid vertical spine with a dozen rib-like fronds curving
off to each side, like a pleated drapery seen edge-on — precisely the textured
seams that a stereo matcher can lock onto in an otherwise flat surface. **Every
frond edge is traced in orange**, `OBSERVED_TARGET_NO_DEPTH`: the object was
imaged there and returned no depth, everywhere, which is why the residue is 60%
seen-but-unmeasured. Blue `PHYSICAL_DEPTH_BREAK` and purple `AMBIGUOUS` appear
only as small specks along the left edge. The **20 `NEVER_OBSERVED` cells are a
single small red patch at the lower right** — visually tiny, and exactly where
the numbers put it: past the right edge of everything the observer looked at.

### Structural failures and code fixes

**Structural failures: none.** `structural_fails: []` in both the manifest and
the comparator; all 35 pinned inputs byte-identical; all four scene objects pure
and unchanged; zero acquisitions; watchdog untouched; truth closed; the final
policy stop replayed exactly.

**Code fixes: none.** No MultiObject-3d file needed repair and no frozen prior
source was modified. The package ran as applied, first time.

### What this establishes, and what it does not

Established, and it answers the question asked. **The first `no_frontier` stop
was policy exhaustion, not attention completion.** The stop itself is genuine and
**exactly reproducible** — eleven fields plus an independent frontier
re-extraction all matched, with `candidates_before_consensus_count = 0` and
`consensus_rejected_candidate_count = 0`, so the controller generated no
candidate rather than generating and rejecting one. But **20 exterior cells were
never observed at all**, in two compact arcs with **zero supported projections**,
sitting **0.98–3.98 degrees beyond the rightmost gaze** and **5.9–6.6 degrees**
from the nearest fixation.

Established, and mechanistically sharper than the counts alone. **The 3D frontier
was not pointing at the unseen territory.** All **30** remaining OPEN look-ahead
targets quantize **inside** the visited gaze envelope (**0** outside), at 0.62 to
4.37 degrees from a completed gaze, and **none** lands on a `NEVER_OBSERVED`
cell — **17 of 30 land on already-mapped support**. The two representations
disagree about where the unfinished business is, and this audit measures that
disagreement without changing either.

Established as a diagnostic. **The dominant residue is seen-but-unmeasured**:
1,514 cells, **60.2%** of the shoreline, **75.7x** the unseen count — the most
extreme such ratio in the programme (object 143 was 18.2x, object 142 inverted at
7.9x unseen). Its 4,633 supported projections are **all** target-seen with **0**
valid depth, the low-texture signature MultiObject-3b first measured at 6.68%.

Not established. **Not a defect claim against FSG6f** — the controller behaved
exactly as specified, and this audit did not test whether a different candidate
generator, corridor rule or lattice would have reached the arcs; **nothing was
tuned, extended or rescued**. **No accuracy claim** — evaluator truth stayed
closed; these are counts of the representation. **No object completeness** — 20
unseen cells bound attention, not geometry, and the 1,514 unmeasured cells bound
nothing at all about the surface behind them. **No claim the unmeasured residue
is irreducible** — no alternate matcher, baseline, vergence or illumination was
tried, by design. **`NO_RANGE_REFERENCE` (720 cells, 402 exterior arcs averaging
1.4 cells) remains bookkeeping, not a finding.** And **the counts gated nothing**:
both labels came from literal zero/non-zero comparisons, and
`scene_disposition` is `MOVE_TO_NEXT_OBJECT` regardless.

**Next: next-object selection from updated scene memory.** Object 145 stays in
persistent memory as `ATTENTION_INCOMPLETE_RETAIN_FOR_REVISIT`; whether the gap
between the 3D frontier and the cyclopean field deserves attention is a judgement
for Luiz/Chat. The scene tour proceeds.
