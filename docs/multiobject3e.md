# MultiObject-3e — one bounded epistemic handoff

## Question

MultiObject-3d established a genuine, exactly reproducible frozen-FSG6f `no_frontier` stop while exterior `NEVER_OBSERVED` territory still remained. More importantly, the final OPEN 3D frontier targets did not point at that unseen territory.

MultiObject-3e tests one architectural seam only:

```text
local FSG6f stop
    -> cyclopean epistemic field supplies one unseen gaze
    -> acquire exactly one fixation
    -> update only the active object if measurable
    -> ask frozen FSG6f for exactly one new decision
    -> STOP
```

This is the project's **Bounded Boldness** principle: a bold architectural hypothesis tested by one bounded intervention.

## Frozen ingredients

- active object id comes from the completed MultiObject-3d parent;
- MultiObject-3d must say `POLICY_EXHAUSTED_WITH_UNSEEN_TERRITORY`;
- 0.1° cyclopean chart and the inherited 12 mm association scale;
- `cyclopean1e_gaze.select_epistemic_probe` unchanged;
- generic `tools/scene_render_fix.py`;
- frozen stereo front end;
- `<100` selected-object points = valid empty evidence, fuse nothing;
- frozen `tools/multiobject2c_policy.py` target-label adapter and FSG6f controller;
- selected-object policy history remains the seed-scoped history from MultiObject-3c, plus the one handoff look.

## What is new

Only the **control transfer** is new. The experiment composes already-established pieces:

1. reconstruct the MultiObject-3d epistemic field exactly enough to reproduce its exterior `NEVER_OBSERVED` count;
2. reuse the Cyclopean-1e selector to choose one unvisited exterior `NEVER_OBSERVED` cell;
3. render one new globally numbered fixation;
4. add that observation to epistemic evidence; fuse only valid active-object depth if the inherited empty-look contract permits;
5. call frozen FSG6f exactly once from the new gaze/history/map;
6. record whether the local policy reactivates, remains exhausted, or returns another stop;
7. do not execute the returned local action.

## Outcomes are measurements, not gates

Interesting possibilities include:

- `LOCAL_POLICY_REACTIVATED`: the global epistemic look makes the local controller produce another action;
- `LOCAL_POLICY_STILL_EXHAUSTED`: the handoff changes observation/map state but FSG6f still has no local action;
- an empty look: the handoff itself succeeds as attention but produces only negative evidence;
- the selected cell becomes support, target-seen/no-depth, non-target evidence, mixed evidence, or another inherited state.

None is a structural failure.

## Explicitly deferred

No second epistemic gaze, no execution of the returned FSG6f action, no automatic alternation, no scene scheduler, no revisit scheduler, no policy tuning, no matcher change, no new threshold, no mesh/interpolation, and no evaluator truth.

## Success criterion

Structural success means the experiment performs exactly one verified handoff with all inherited machinery frozen and returns exactly one FSG6f decision while preserving every pre-existing object source byte-for-byte. Scientific interpretation comes only after seeing the outcome.

## Results

Run 2026-09-22 on the workstation. `MULTIOBJECT3E_COMPLETE`, `structural_fails:
[]`, no FAIL line anywhere; the comparator agrees and exits 0.

**Both halves of the central question answer yes.**

The cyclopean epistemic field supplied **one useful action exactly where the
local 3D controller had none**: the unchanged Cyclopean-1e selector chose gaze
**(+23.700, −5.500)** — **outside** the previous visited-gaze envelope, **6.208
degrees** from the nearest previous fixation, precisely the region MultiObject-3d
showed the 3D frontier could not reach. One fixation there was **not empty**:
21,255 target pixels visible, **2,085 with valid depth (9.81% recovery, the best
single-look recovery this object has produced)**. Fusing once drove exterior
`NEVER_OBSERVED` from **20 to 0**, and turned the selected cell from
`NEVER_OBSERVED` into **`SUPPORT`**.

Control then handed back cleanly. Frozen FSG6f, asked exactly once through the
unchanged adapter, returned **`stop: false`, `reason: continue`, next gaze
(+18.700, −10.500)** — `candidates_before_consensus_count` went from **0 to 4**.
**`LOCAL_POLICY_REACTIVATED`.**

**The returned action was recorded and not executed.** `experiment_stop:
BOUNDED_AFTER_ONE_HANDOFF_AND_ONE_RETURN_DECISION`.

### Provenance and the parent chain

Working tree clean at the start. Package commit **`076731f`** adds **exactly the
seven MultiObject-3e files, all `A`**; parent result **`6a7cc7b`**.

Frozen audit at full scope: **every tracked non-documentation source present at
`6a7cc7b` — 296 files** across `tools/`, `tools/dev/` and `scenes/`.
`git diff 6a7cc7b HEAD` over that set is **empty (0 lines)** and all **296 sha256
are SAME**. The complete changed-file list between parent result and HEAD is the
seven new 3e files and nothing else. The machinery this experiment must not
touch: `cyclopean1e_gaze.py` **`a3599ea14fc00e60…`** — the same hash recorded
since Cyclopean-1f — `multiobject2c_policy.py` `f4d4a08b00981466…`,
`fsg6f_frontier.py` `d636c9405d719916…`, `scene_render_fix.py`
`6e70bbb78c1043ec…`, `reality2_render_fix.py` `9f1433d189fbcbb5…` (unchanged,
**never invoked**), `fsg3_surface_map.py` `1b9dbeb873105ec9…`.

Parent located **by manifest**: exactly one
`MultiObject3d-selected-object-epistemic-stop-audit-v1` record —
`previews/multiobject3d/full-seed2111`. **All three required 3d gates hold:**
`stop_interpretation` **`POLICY_EXHAUSTED_WITH_UNSEEN_TERRITORY`**,
`object_status` **`ATTENTION_INCOMPLETE_RETAIN_FOR_REVISIT`**,
`final_policy_stop_replayed_exactly` **true** — with 20 exterior
`NEVER_OBSERVED` cells available to hand off.

Its manifest was followed to the scene record
`previews/multiobject3c/full-seed2111`, where **both required 3c gates hold**:
`termination_reason` **`no_frontier`** with `scientific_stop_reached` **true**,
and **13 selected-object fixations strictly below the 24-fixation watchdog** — a
genuine pre-watchdog stop. Each gate is enforced by the runner's own guard.

### The active object id is consumed, not hard-coded

`multiobject3e_run.py:61` reads `int(m3d.get("selected_object_id", -1))` from the
3d manifest, and the runner cross-checks it against the 3c record's own selected
id. **The literal `145` appears zero times in all five MultiObject-3e sources,
including the checker.** `preexisting_object_ids` **[141, 142, 143]** likewise
come from the parent.

### Read-only integrity

**All 39 pinned inputs byte-identical afterwards** — 3 MultiObject-3d artifacts
(`prediction_manifest.json` `53a7a2f0f619c83c…`, the epistemic report
`0b5e298c9f85d24e…`, its visual `75acb2318c2eb8d9…`), 6 MultiObject-3c artifacts
(manifest `3b44f9c87eebdaac…`, `scene_graph.json` `55039411671c52b5…`,
`object_145_surface_map.npz` `8c9e7ffada6fb6a7…`, policy trace
`a7414fd6b6f0c41f…`, footprints `c9dc9a3de8f871fa…`, PLY `abde346b5f16b5ec…`),
**4 scene-object geometry sources**, and **all 26 saved selected-object
calibration/observation files** (13 looks x 2). The runner's own four guards
assert the same and all passed.

| object | sha256 before | after | points | ids |
|---|---|---|---|---|
| 141 | `6ac98f6251b47337…` | same | 155,684 | `{141}` |
| 142 | `6f90d985f8078a7d…` | same | 310,884 | `{142}` |
| 143 | `bbc4b856a07d2be5…` | same | 42,988 | `{143}` |
| 145 (3c source) | `8c9e7ffada6fb6a7…` | same | 6,426 | `{145}` |

The active object's **updated** map is written into the new 3e record; the 3c map
it grew from is untouched.

### Environment and wall time

Blender 5.2.1 LTS headless, Cycles, **OPTIX** on an RTX 4090 (driver 595.84);
host `.venv/bin/python` 3.12.3. **11.7 s** — one Blender launch plus the 13-look
epistemic reconstruction.

### Checks

`py_compile` clean on all five modules. `tools/multiobject3e_progress.py` and the
positive checker printed the four prescribed lines verbatim:

```text
[multiobject3e-progress] PASS threshold_free=true one_return_decision=true auto_loop=false
[multiobject3e-handoff] PASS parent_policy_exhausted=true epistemic_selector_reused=true one_fixation=true
[multiobject3e-return] PASS frozen_local_policy=true one_decision=true returned_action_executed=false auto_loop=false
[multiobject3e-check] SUMMARY passed=8 failed=0
```

All **eight** negatives are genuine source-mutation controls, each exiting **1**
with a named detector; **none exited 2**:

| negative | rc | detected by |
|---|---|---|
| `handpick` | 1 | `parent_policy_exhausted_target_consumed_not_handpicked` |
| `newselector` | 1 | `reuse_established_epistemic_selector` |
| `multiprobe` | 1 | `bounded_one_fixation_one_return_decision` |
| `legacyrenderer` | 1 | `generic_renderer_no_history_rerender` |
| `crossfuse` | 1 | `selected_only_fusion_existing_objects_read_only` |
| `skipempty` | 1 | `inherited_empty_look_and_fusion_rule` |
| `autoloop` | 1 | `bounded_one_fixation_one_return_decision` |
| `qualitygate` | 1 | `no_threshold_quality_gate_or_scheduler` |

The **exit-2 escape branch was verified live**. Structurally confirmed
independently: `policy.choose_next(` appears **exactly once** in the runner, and
`reality2_render_fix` appears **zero** times.

**No regression**: **26/26** prior suites green and **170/170** prior negatives
still firing, **none weakened**. The **Cyclopean-1f caveat stands and 1f was not
edited**.

### Active-object and history scope

Seed-scoped history **13 looks, global steps 66..78** — the MultiObject-3b seed
plus the twelve MultiObject-3c growth looks, reconstructed through the frozen
3d audit helpers. **No earlier scene-memory observation was imported**; the
`priorhistory`-style clause is inherited from 3c and the seed-scoped reconstruction
is what the runner replays.

### Reconstructed pre-handoff state — the required blocker check

Rebuilt on the inherited **0.1-degree** chart at the **12 mm** scale from the 3c
final map plus its seed-scoped observations. **Exterior `NEVER_OBSERVED`
reproduced as 20**, matching both the MultiObject-3d manifest summary and its
report. The runner raises `reconstructed pre-handoff epistemic field disagrees
with MultiObject-3d` otherwise; it did not.

Pre-handoff refined census (all / exterior / internal): `OBSERVED_TARGET_NO_DEPTH`
**1,514 / 1,043 / 471**; `NO_RANGE_REFERENCE` 720 / 561 / 159;
`OBSERVED_NONTARGET_ONLY` 142 / 142 / 0; **`NEVER_OBSERVED` 20 / 20 / 0**;
`MIXED_OBSERVATION` 20 / 20 / 0; `OBSERVED_TARGET_WITH_DEPTH` 0 — identical to
what MultiObject-3d published.

### The selected epistemic gaze

From `cyclopean1e_gaze.select_epistemic_probe` **unchanged**, no new score and no
threshold:

| field | value |
|---|---|
| eligible components | **1** |
| never-observed shoreline cells | 20 |
| component max exterior depth | 17 |
| **probe cell (y, x)** | **(17, 86)** |
| **probe border distance** | **17** — the deepest available |
| `revisit_fallback_rank` | **0** |
| **handoff gaze** | **(+23.700, −5.500)** |

Diagnostics, recorded and gating nothing: the gaze is **outside** the previous
visited-gaze envelope (yaw [+10.822, +20.822], pitch [−9.999, +10.001]) and
**6.208 degrees** from the nearest previous fixation. The runner independently
re-verified that the chosen cell was `NEVER_OBSERVED` and `EXTERIOR` before
rendering, and that it had not been visited.

### One acquisition, and the measurement

Exactly one new globally numbered fixation at **global step 79** = 78 + 1,
through the generic `tools/scene_render_fix.py`, same profile/seed/device
contract. The record's `acquisition/` holds **only `fix_79`**;
`parent_fixations_rerendered` **0**.

| quantity | value |
|---|---|
| target visible pixels | **21,255** |
| target valid depth points | **2,085** |
| **depth recovery fraction** | **9.81%** |
| whole-frame valid | 14,041 of 65,536 (21.4%) |
| `empty_look` | **false** (2,085 ≥ the inherited 100-point limit) |

**9.81% is the highest single-look recovery object 145 has produced** — above the
9.6% maximum across all thirteen MultiObject-3c looks, and well above the 6.68%
of its seed. The image shows why: unlike the flat three-band seed view, this look
catches the **right-hand edge of the terracotta panel** against the grey wall,
with the cream vertical stripe beside it — a genuine depth boundary rather than
untextured interior.

### Fusion, idempotence, purity

Fused **once** with the frozen 12 mm rule: **295 new** surfels, **1,790 matched**.
Replay was **idempotent** (duplicate detected, `xyz_h`, `support_count` and
`provenance_mask` all bitwise equal), and the map stayed **pure `{145}`**.

Map **6,426 → 6,721** points (+295); multi-look surfels **4,005**, max support
**6**; range **2.5265 / 2.7625 / 3.0033 m**, essentially unchanged from 3c's
2.5265 / 2.7627 / 3.0033. `object_145_surface_map.ply` carries **6,721** vertices.

### Epistemic before and after

**Exterior `NEVER_OBSERVED` 20 → 0.** The selected cell went from
`NEVER_OBSERVED` (EXTERIOR) to **`SUPPORT`** — not merely observed, but mapped.

| state | all before | all after | ext before | ext after | int before | int after |
|---|---|---|---|---|---|---|
| **`NEVER_OBSERVED`** | **20** | **0** | **20** | **0** | 0 | 0 |
| `OBSERVED_TARGET_NO_DEPTH` | 1,514 | 1,584 | 1,043 | 1,114 | 471 | 470 |
| `NO_RANGE_REFERENCE` | 720 | 760 | 561 | 600 | 159 | 160 |
| `OBSERVED_NONTARGET_ONLY` | 142 | 174 | 142 | 174 | 0 | 0 |
| `MIXED_OBSERVATION` | 20 | 20 | 20 | 20 | 0 | 0 |
| `OBSERVED_TARGET_WITH_DEPTH` | 0 | 0 | 0 | 0 | 0 | 0 |

The other states **grew** because the map grew: a pixel census of the two visuals
gives support **9,198 → 9,537 (+339)**, background **4,302 → 3,816 (−486)**,
`OBSERVED_TARGET_NO_DEPTH` **+70**, `NO_RANGE_REFERENCE` **+40**,
`OBSERVED_NONTARGET_ONLY` **+32**, `PHYSICAL_DEPTH_BREAK` **+15**, `AMBIGUOUS`
**+10** — both totalling all 16,016 chart cells. **No quality gate was applied to
the amount of change**; these are recorded as they fell.

### Exactly one returned FSG6f decision

The one handoff gaze and observation were appended to the seed-scoped history and
the **unchanged** `multiobject2c_policy.py` / frozen FSG6f machinery was called
**once**:

| field | before (3c final) | after handoff |
|---|---|---|
| `stop` | True | **False** |
| `reason` | `no_frontier` | **`continue`** |
| `next_gaze_deg` | null | **(+18.700, −10.500)** |
| **`candidates_before_consensus_count`** | **0** | **4** |
| `consensus_rejected_candidate_count` | 0 | 0 |
| `frontier_count` / `raw_count` | 72 | **488** |
| `frontier_open_count` | 30 | **391** |
| `frontier_map_resolved_count` | 1 | 24 |
| `frontier_boundary_resolved_count` | 41 | 73 |
| `frontier_voxel_count` | 1,368 | 1,467 |
| `frontier_state_radius_m` | 0.012 | 0.012 |

The selected candidate: delta **(−5.0, −5.0)** on the frozen lattice, frontier
score **30.46**, support 104, predicted new angular area **125.90 deg²**,
continuation corridor **allowed** at combined fraction 0.396, consensus
**allowed** under the unchanged `strict_open_majority_over_resolved_state` rule
with open 104 against resolved 39.

**Recorded honestly as measured, not explained**: 295 new surfels on a
6,426-point map grew the frontier from 72 to 488 entries — a 6.8x jump — while
the map's own angular extent barely moved (yaw 15.679→15.684, 24.420→24.524;
pitch −6.538→−6.547, 7.350→7.346). That is the frozen extractor's own response to
the new geometry, and **this single observation does not explain the mechanism.**

`multiobject3e_progress.classify_return` applied its threshold-free rule —
`stop` is False and `next_gaze_deg` is not None — giving
**`LOCAL_POLICY_REACTIVATED`**.

### Boundedness

`returned_local_action_executed` **false**. `added_fixations` **1**,
`returned_local_policy_decisions` **1**, `automatic_handoff_loop` **false**,
`automatic_scene_scheduler` **false**, `revisit_scheduler_used` **false**,
`watchdog_changed` **false**, `quality_gate_used` **false**,
`growth_loop_iterations_added` **0**, `policy_source_modified` **false**,
`epistemic_selector_reused_unchanged` **true**, `truth_opened` **false**. The
written policy trace carries 14 entries — the 13 inherited from 3c plus the one
returned decision — with `last_action_executed: false` and
`bounded_handoff: true`. **The experiment stopped after observing the decision.**

### Scene state and footprints

`selected_object_fixations_total` **14**. Shared chart **624 x 488** at 0.1 deg.

| object | points | footprint cells | area | vs 3c |
|---|---|---|---|---|
| 141 | 155,684 | 37,654 | 376.54 deg² | unchanged |
| 142 | 310,884 | 62,784 | 627.84 deg² | unchanged |
| 143 | 42,988 | 17,947 | 179.47 deg² | unchanged |
| **145** | **6,721** | **2,107** | **21.07 deg²** | 2,041 → 2,107 (+66) |

**All six pairwise overlaps and the all-object overlap remain 0.**

### Visual reading

`handoff_rgb.png` — the handoff look: a terracotta panel with a cream vertical
stripe along its left edge, seen at an angle against a flat grey wall, with wood
floor below. Crucially the **panel's right-hand edge is in view**: a real
occluding boundary, which is what a stereo matcher can measure, and what the
previous thirteen looks never reached.

`epistemic_before.png` / `epistemic_after.png` — the same comb-shaped support (a
vertical spine with rib-like fronds) in both, with every frond edge traced orange
as seen-but-unmeasured. The difference is at the lower right: **the small red
`NEVER_OBSERVED` patch present in the before image is absent from the after
image**, replaced by support and shoreline. Pixel censuses of both reproduce the
report exactly and both total 16,016 cells.

`scene_cyclopean_footprints.png` — the four-object chart, with object 145's bright
narrow vertical feature slightly larger than at 3c and still disjoint from the
other three.

### Structural failures and code fixes

**Structural failures: none.** `structural_fails: []` in both the manifest and
the comparator; all 39 pinned inputs byte-identical; all four object sources pure
and unchanged; one acquisition; no rerender; truth closed; the active map pure.

**Code fixes: none.** No MultiObject-3e file needed repair and no frozen prior
source was modified. The package ran as applied, first time.

### What this establishes, and what it does not

Established — and it answers both halves of the question. **The global cyclopean
epistemic field supplied one useful action exactly where the local 3D controller
had none.** MultiObject-3d had shown the final OPEN frontier targets all lay
inside the already-visited envelope with none on unseen territory; the unchanged
Cyclopean-1e selector picked a gaze **6.208 degrees outside that envelope**, at
the **deepest** of the 20 unseen cells, and that single look was **not empty** —
**2,085 valid target points at 9.81% recovery**, the object's best single-look
figure. It drove exterior `NEVER_OBSERVED` from **20 to 0** and converted the
selected cell to **`SUPPORT`**.

Established — **control was handed back without changing either mechanism.**
Frozen FSG6f, called exactly once through the unchanged adapter with the
seed-scoped history plus one entry, moved from `no_frontier` with **0 candidates**
to `continue` with **4 candidates** and a concrete next gaze. Every ingredient was
byte-identical: the selector, the adapter, the controller, the renderer, the 12 mm
rule, the empty-look semantics. **`LOCAL_POLICY_REACTIVATED`**, and the returned
action was **recorded, not executed** — the boundedness the contract requires and
the checks enforce.

Not established. **One handoff on one object at one seed.** Nothing here shows the
transfer generalises, that it would work from a different unseen cell, or that a
second handoff would behave the same — **no second epistemic gaze was taken, by
design**. **Not a demonstration that alternation is a good policy**: the returned
action was never executed, so whether FSG6f would have made progress from
(+18.700, −10.500) is **untested**. **No mechanism for the frontier jump** — 72 to
488 entries from 295 surfels is recorded as measured and **not explained**; this
run cannot separate "the new geometry genuinely opened the frontier" from
properties of the frozen extractor. **No accuracy claim** — evaluator truth stayed
closed; 6,721 points describe the representation. **No object completeness** —
exterior `NEVER_OBSERVED` reaching 0 is attention, not geometry, and **1,584 cells
remain seen-but-unmeasured**, more than before. **No claim the unmeasured residue
is reducible** — no matcher, baseline, vergence or illumination was changed. And
**no scheduler, no revisit policy, no automatic loop** was introduced.

**Next: interpret this single handoff outcome before any second action.** The
experiment stopped after observing the returned decision, as the contract
requires.
