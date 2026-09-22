# MultiObject-3f — frontier reactivation audit

## Motivation

MultiObject-3e gave the first bounded hierarchical handoff.  Frozen FSG6f had stopped with `no_frontier`; the established cyclopean epistemic selector supplied one gaze outside the previously visited envelope; that gaze acquired useful selected-object depth and fused a small amount of new geometry; then one call to the unchanged local controller returned `continue` with a concrete next gaze.

The striking diagnostic was the local frontier jump:

```text
before handoff: frontier 72, OPEN 30, candidates before consensus 0
after handoff:  frontier 488, OPEN 391, candidates before consensus 4
```

while the persistent selected-object map itself changed only modestly.

Before treating that reactivation as mechanistically understood, one confound must be separated explicitly: **FSG6f frontier extraction is local to the current gaze**.  The handoff did not merely add geometry; it also moved the current gaze to a region the local controller had never reached.  Therefore `72 -> 488` cannot be attributed to the fused surfels from the raw counts alone.

This increment is the small diagnostic step that separates those effects.

## Central question

> What, exactly, changed inside the frozen local representation when the one epistemic handoff reactivated FSG6f?

More specifically:

1. How much of the frontier-count jump comes from moving the **current gaze/window** over geometry that already existed?
2. How much comes from the **map update** itself?
3. Among the final frontier sources, which are persistent, newly exposed, newly frontier-active on pre-existing map voxels, or supported by newly occupied map voxels?
4. Which frozen candidate-generation gate changed for each of the eight local lattice directions?
5. Are the reactivated candidates supported mostly by newly exposed frontier structure or by genuinely new geometry?

## Read-only 2x2 decomposition

The audit extracts the geometric frontier in four combinations, without acting on any of them:

```text
PRE_MAP_PRE_GAZE    actual state before the handoff
PRE_MAP_POST_GAZE   moved gaze/window, but no fused map update
POST_MAP_PRE_GAZE   fused map update, but old local gaze/window
POST_MAP_POST_GAZE  actual state after the handoff
```

This uses the same frozen `extract_frontier` function in every case.  It adds no threshold and makes no new policy decision.

Two policy-level counterfactuals are also recorded descriptively:

- **ATTENTION_ONLY_PRE_FUSION_MAP** — use the handoff gaze/current observation and updated observation history, but keep the pre-fusion map;
- **GEOMETRY_ONLY_OLD_ATTENTION_CONTEXT** — use the post-fusion map under the old current gaze/current observation and old history.

Their returned actions are diagnostics only and are never executed.

## Frontier identity

To avoid inventing a matching tolerance, frontier sources are matched only by the controller's own already-frozen voxel grid:

```text
source_voxel_key = floor(source_xyz_h / SURFACE_FRONTIER["voxel_m"])
```

This partitions the actual pre/post frontier into:

- persistent source voxels;
- appeared source voxels;
- disappeared source voxels.

For persistent voxels the audit reports `OPEN`, `MAP_RESOLVED`, and `BOUNDARY_RESOLVED` transitions plus continuous source/target displacement diagnostics.

For appeared post-handoff frontier voxels it distinguishes exactly:

- `EXPOSED_BY_POST_GAZE_ON_PRE_MAP` — already a frontier on the pre-map when viewed from the handoff gaze;
- `CREATED_BY_MAP_UPDATE_ON_PREEXISTING_VOXEL` — source map voxel existed before, but became frontier only after the map update;
- `FRONTIER_FROM_NEW_MAP_VOXEL` — frontier source belongs to a map voxel absent before the handoff.

Nearest distances to the saved handoff patch are reported continuously.  They gate nothing.

## Candidate-gate ledger

For each of the eight frozen 5-degree lattice directions, before and after the handoff, the audit records:

- policy bounds;
- previously visited status;
- raw aligned frontier support;
- `OPEN`, `MAP_RESOLVED`, and `BOUNDARY_RESOLVED` aligned support;
- the already-frozen minimum OPEN-support gate;
- the unchanged projected continuation-corridor result;
- the unchanged strict OPEN-majority state consensus;
- whether the direction reached `candidates_before_consensus`;
- whether it became admissible.

The ledger reuses the frozen FSG6f projection, continuation and consensus functions.  It is a diagnostic replay, not a replacement controller.

For post-handoff OPEN support it also reports the frontier-origin composition, so a reactivated direction can be traced back to persistent, gaze-exposed, map-update-created, or new-map-voxel frontier sources.

## Integrity

MultiObject-3f is strictly read-only:

- no Blender;
- no new fixation;
- no fusion;
- no watchdog extension;
- no controller or matcher change;
- no second local action;
- no scheduler;
- no evaluator truth.

Both the actual pre-handoff and post-handoff frozen policy decisions must replay exactly before any comparison is accepted.

## Expected output

The completed record contains:

- `object_<id>_frontier_reactivation_report.json` — exact policy replays, 2x2 map/gaze decomposition, counterfactual policy summaries, frontier lineage and candidate-gate tables;
- `frontier_reactivation.npz` — machine-readable pre/post frontier source keys, source/target geometry and state codes;
- `frontier_reactivation_details.json` — per-frontier persistent/appeared/disappeared details;
- `prediction_manifest.json` — integrity and compact summary.

## Deliberately deferred

- executing the returned local gaze;
- a second epistemic handoff;
- an automatic hierarchical loop;
- changing the FSG6f frontier extractor or candidate generator;
- tuning any threshold;
- revisiting other objects;
- scene scheduling.

The next step is chosen only after interpreting this audit.

## Results

Run 2026-09-22 on the workstation, **host-side only**. `MULTIOBJECT3F_COMPLETE`,
`structural_fails: []`, no FAIL line anywhere; the comparator agrees and exits 0.
Both required exact replays passed: `pre_policy_replayed_exactly` **true**,
`post_policy_replayed_exactly` **true**.

**The answer is not a single cause, but the causes are very unequal and the
counterfactuals separate them cleanly.**

The **2x2 decomposition is decisive**: moving the current gaze alone, with **no
fused geometry at all**, takes the frontier from **72 to 429** — while updating
the map alone, under the old gaze, leaves it at **exactly 72, unchanged**. The
remaining 59 entries (14.2% of the increase) are the interaction.

The **policy counterfactuals are sharper still**. With the handoff gaze and
updated history but the **pre-fusion map**, frozen FSG6f returns `continue` with
**4 candidates and the identical next gaze (+18.700, −10.500)**. With the
**post-fusion map** but the old gaze and history, it returns `no_frontier` with
**0 candidates** — bit-for-bit the pre-handoff outcome.

**So the fused geometry was neither necessary nor sufficient for the
reactivation. What restarted the controller was moving attention.** Geometry did
contribute — **20.0%** of the OPEN support behind the four reactivated directions
comes from genuinely new map voxels — but the directions clear every frozen gate
without it.

### Provenance

Working tree clean at the start. Package commit **`b5ee437`** adds **exactly the
seven MultiObject-3f files, all `A`**; parent result **`c4584ac`**.

Frozen audit at full scope: **every tracked non-documentation source present at
`c4584ac` — 301 files** across `tools/`, `tools/dev/` and `scenes/`.
`git diff c4584ac HEAD` over that set is **empty (0 lines)** and all **301 sha256
are SAME**. The complete changed-file list between parent result and HEAD is the
seven new 3f files and nothing else. The machinery this audit replays unchanged:
`fsg6f_frontier.py` `d636c9405d719916…`, `multiobject2c_policy.py`
`f4d4a08b00981466…`, `fsg6f_public.py` `c79f58c9b51f33d4…`,
`cyclopean1e_gaze.py` `a3599ea14fc00e60…`, `fsg3_surface_map.py`
`1b9dbeb873105ec9…`.

Parent located **by manifest**: exactly one
`MultiObject3e-one-epistemic-handoff-v1` record —
`previews/multiobject3e/full-seed2111`. **All six required 3e gates hold:**
`added_fixations` **1**, `returned_local_policy_decisions` **1**, `return_status`
**`LOCAL_POLICY_REACTIVATED`**, `returned_local_action_executed` **false**,
`automatic_handoff_loop` **false**, `structural_fails` **[]**.

Its manifest was followed to `previews/multiobject3c/full-seed2111`, where the
**genuine pre-handoff stop** is confirmed: `termination_reason` **`no_frontier`**,
`scientific_stop_reached` **true**, **13 of 24** fixations, and the **same
selected-object id 145**.

### Environment and wall time

Host `.venv/bin/python` 3.12.3. **No Blender, no Cycles, no GPU** — `pgrep
blender` 0 before and after. **2.9 s**. `acquisitions_added` **0**,
`fusion_iterations_added` **0**, `growth_iterations_added` **0**,
`watchdog_changed` **false**, `returned_local_action_executed` **false**,
`no_acquisition` **true**.

### Checks

`py_compile` clean on all five modules. The four prescribed lines appeared
verbatim:

```text
[multiobject3f-progress] PASS threshold_free=true pre_post_reactivation=true no_action=true
[multiobject3f-audit] PASS read_only=true pre_post_replay=true frozen_voxel_identity=true frontier_lineage=true
[multiobject3f-candidates] PASS frozen_gate_ledger=true action_executed=false threshold_added=false
[multiobject3f-check] SUMMARY passed=10 failed=0
```

All **ten** negatives are genuine source-mutation controls, each exiting **1**
with exactly the detector the contract names; **none exited 2**:

| negative | rc | detected by |
|---|---|---|
| `acquire` | 1 | `read_only_no_acquisition_or_fusion` |
| `handpick` | 1 | `parent_reactivated_target_consumed_not_handpicked` |
| `prereplay` | 1 | `exact_pre_post_frozen_policy_replay` |
| `voxelid` | 1 | `frozen_voxel_identity_no_matching_tolerance` |
| `counterfactual` | 1 | `gaze_window_and_map_counterfactual_decomposition` |
| `lineage` | 1 | `frontier_lineage_and_map_voxel_decomposition` |
| `candidateledger` | 1 | `candidate_gate_ledger_reuses_frozen_rules` |
| `crossobject` | 1 | `scene_objects_and_parent_records_read_only` |
| `threshold` | 1 | `frozen_voxel_identity_no_matching_tolerance` |
| `act` | 1 | `descriptive_no_quality_gate_scheduler_or_action` |

The **exit-2 escape branch was verified live**. **No regression**: **27/27** prior
suites green and **178/178** prior negatives still firing, **none weakened**. The
**Cyclopean-1f caveat stands and 1f was not edited**.

### Exact pre/post policy replay — the precondition

Both replays reproduced the saved decisions before any comparison was accepted.

| field | PRE (replayed = saved) | POST (replayed = saved) |
|---|---|---|
| `stop` | True | **False** |
| `reason` | `no_frontier` | **`continue`** |
| `next_gaze_deg` | null | **(+18.700, −10.500)** |
| `current_gaze_deg` | (+10.822, −9.999) | **(+23.700, −5.500)** |
| `frontier_voxel_count` | 1,368 | 1,467 |
| `frontier_count` / `raw_count` | 72 | **488** |
| `frontier_open_count` | 30 | **391** |
| `frontier_map_resolved_count` | 1 | 24 |
| `frontier_boundary_resolved_count` | 41 | 73 |
| **`candidates_before_consensus_count`** | **0** | **4** |
| `consensus_rejected_candidate_count` | 0 | 0 |

`reactivation_status: LOCAL_POLICY_REACTIVATION_REPRODUCED`.

### Map-voxel change on the frozen grid

Frozen `SURFACE_FRONTIER["voxel_m"]` = **0.025 m**; occupied-voxel counts
reproduce the saved `frontier_voxel_count` values **1,368 → 1,467** exactly.

| quantity | value |
|---|---|
| pre-occupied voxels | 1,368 |
| post-occupied voxels | 1,467 |
| persistent | 1,359 |
| **added** | **108** |
| removed | 9 |
| handoff-patch occupied voxels | 256 |
| **added voxels directly present in the handoff patch** | **107 of 108** |

Map points 6,426 → 6,721 (+295) from a 2,085-point patch. So the handoff added
**108 new voxels, 107 of them straight from the patch** — a real but small
geometric change against a 1,368-voxel baseline (**+7.9%**).

### The four-way map/gaze frontier decomposition — the key control

Same frozen `extract_frontier` in every cell; no threshold, no policy decision.

| | **PRE gaze** (+10.822, −9.999) | **POST gaze** (+23.700, −5.500) |
|---|---|---|
| **PRE map** (6,426 pts) | **72** (actual before) | **429** |
| **POST map** (6,721 pts) | **72** | **488** (actual after) |

Reading the table:

- **Map update alone contributes exactly nothing**: `POST_MAP_PRE_GAZE` = **72**,
  identical to `PRE_MAP_PRE_GAZE`. From the old gaze, the 108 new voxels produce
  **zero** additional frontier entries.
- **Gaze move alone contributes 357 of the 416 total increase (85.8%)**:
  72 → 429 with the map untouched.
- **The interaction contributes 59 (14.2%)**: 488 − 429, frontier that exists
  only when both the new geometry and the new viewing window are present.

### The two policy counterfactuals — neither executed

| | ATTENTION_ONLY_PRE_FUSION_MAP | GEOMETRY_ONLY_OLD_ATTENTION_CONTEXT |
|---|---|---|
| inputs | handoff gaze + updated history + **pre-fusion map** | **post-fusion map** + old gaze + old history |
| `stop` | **False** | True |
| `reason` | **`continue`** | `no_frontier` |
| `frontier_count` | 429 | 72 |
| `frontier_open_count` | 354 | 30 |
| `frontier_map_resolved_count` | 21 | 1 |
| `frontier_boundary_resolved_count` | 54 | 41 |
| **`candidates_before_consensus_count`** | **4** | **0** |
| `consensus_rejected_candidate_count` | 0 | 0 |
| `next_gaze_deg` | **(+18.700, −10.500)** | null |

**Attention alone reproduces the actual decision exactly** — same candidate count,
**same next gaze**. **Geometry alone reproduces the stop exactly.** Both returned
actions are diagnostics; `returned_local_action_executed: false`.

### Frontier lineage — matched only by the frozen voxel key

`identity_rule: exact frozen source voxel key floor(source_xyz_h / voxel_m); no
tolerance`, `voxel_m` 0.025.

| partition | count |
|---|---|
| persistent source voxels | **24** |
| appeared | **464** |
| disappeared | **48** |

**Persistent frontier is bitwise stationary and bitwise unchanged in state.**
`persistent_state_changed_count` **0** — OPEN→OPEN 16, MAP_RESOLVED→MAP_RESOLVED
1, BOUNDARY_RESOLVED→BOUNDARY_RESOLVED 7, with **zero** off-diagonal. Persistent
source shift and target shift are **exactly 0.0 m** (min/median/max/mean), and
the maximum angular target shift is **1.21e-06 deg**.

**Appeared-source cause partition:**

| origin class | count | share |
|---|---|---|
| **`EXPOSED_BY_POST_GAZE_ON_PRE_MAP`** | **359** | **77.4%** |
| `FRONTIER_FROM_NEW_MAP_VOXEL` | 93 | 20.0% |
| `CREATED_BY_MAP_UPDATE_ON_PREEXISTING_VOXEL` | 12 | 2.6% |

(359 + 12 = 371 on pre-existing map voxels, plus 93 on new voxels.)

**More than three quarters of the appeared frontier was already frontier on the
pre-handoff map — it had simply never been in view.**

Appeared states: OPEN **375**, MAP_RESOLVED 23, BOUNDARY_RESOLVED 66.
Disappeared states: OPEN 14, BOUNDARY_RESOLVED 34, MAP_RESOLVED 0.
169 appeared sources share a voxel with the handoff patch.

Continuous diagnostics, gating nothing — appeared-source nearest distance to the
handoff patch: min **0.0**, median **0.0216 m**, max **0.174 m**; appeared-target
nearest: min **0.0035 m**, median **0.0934 m**, max **0.219 m**.

### Candidate-gate ledger — the eight frozen lattice directions

Diagnostic replay of the frozen projection, continuation and consensus functions.
No action was selected or executed.

**BEFORE** — 0 reaching before-consensus, 0 admissible:

| dir | candidate gaze | visited | raw | OPEN | MAPR | BNDR | min-sup (req 8) | corridor | consensus | first blocker |
|---|---|---|---|---|---|---|---|---|---|---|
| (−1,−1) | (+5.822, −14.999) | no | 36 | 8 | 1 | 27 | pass | **0.000** | no | `CONTINUATION_CORRIDOR` |
| (−1, 0) | (+5.822, −9.999) | no | 28 | **7** | 0 | 21 | **fail** | — | no | `MINIMUM_OPEN_SUPPORT` |
| (−1, 1) | (+5.822, −4.999) | no | 21 | 9 | 0 | 12 | pass | **0.000** | no | `CONTINUATION_CORRIDOR` |
| ( 0,−1) | (+10.822, −14.999) | no | 39 | 11 | 1 | 27 | pass | **0.000** | no | `CONTINUATION_CORRIDOR` |
| ( 0, 1) | (+10.822, −4.999) | **yes** | 0 | 0 | 0 | 0 | — | — | — | `ALREADY_VISITED` |
| ( 1,−1) | (+15.822, −14.999) | no | 33 | 14 | 1 | 18 | pass | **0.000** | no | `CONTINUATION_CORRIDOR` |
| ( 1, 0) | (+15.822, −9.999) | **yes** | 0 | 0 | 0 | 0 | — | — | — | `ALREADY_VISITED` |
| ( 1, 1) | (+15.822, −4.999) | **yes** | 0 | 0 | 0 | 0 | — | — | — | `ALREADY_VISITED` |

First-blocker counts: `ALREADY_VISITED` 3, `CONTINUATION_CORRIDOR` 4,
`MINIMUM_OPEN_SUPPORT` 1.

**AFTER** — 4 reaching before-consensus, **4 admissible**, 0 consensus-rejected:

| dir | candidate gaze | visited | raw | OPEN | MAPR | BNDR | min-sup | corridor | consensus | first blocker |
|---|---|---|---|---|---|---|---|---|---|---|
| **(−1,−1)** | (+18.700, −10.500) | no | 143 | **104** | 9 | 30 | pass | **0.396** | **yes** | **none — admissible** |
| **(−1, 0)** | (+18.700, −5.500) | no | 141 | **119** | 9 | 13 | pass | **0.961** | **yes** | **none — admissible** |
| **(−1, 1)** | (+18.700, −0.500) | no | 117 | **107** | 10 | 0 | pass | **1.000** | **yes** | **none — admissible** |
| ( 0,−1) | (+23.700, −10.500) | no | 118 | 58 | 2 | 58 | pass | 0.100 | no | `CONTINUATION_CORRIDOR` |
| **( 0, 1)** | (+23.700, −0.500) | no | 92 | **79** | 4 | 9 | pass | **0.729** | **yes** | **none — admissible** |
| ( 1,−1) | (+28.700, −10.500) | — | 0 | 0 | 0 | 0 | — | — | — | `POLICY_BOUNDS` |
| ( 1, 0) | (+28.700, −5.500) | — | 0 | 0 | 0 | 0 | — | — | — | `POLICY_BOUNDS` |
| ( 1, 1) | (+28.700, −0.500) | — | 0 | 0 | 0 | 0 | — | — | — | `POLICY_BOUNDS` |

First-blocker counts: `POLICY_BOUNDS` 3, `CONTINUATION_CORRIDOR` 1, none 4.

`directions_newly_reaching_before_consensus` and `directions_newly_admissible`
are the same four: **(−1,−1), (−1,0), (−1,1), (0,1)**.

**The decisive gate is the projected binocular continuation corridor.** Before,
*every* unvisited direction had combined corridor fraction **exactly 0.000**;
after, the four admissible ones have **0.396 / 0.961 / 1.000 / 0.729**. That
corridor is projected **from the current gaze**, so it is an attention-frame
quantity — which is why moving the window, not adding surfels, is what opened it.

A second, purely attentional effect is visible in the table: because the 5-degree
lattice is **relative to the current gaze**, three directions that were
`ALREADY_VISITED` before are unvisited after (the lattice moved with the gaze),
and three that were in bounds before are now outside `POLICY_BOUNDS` at yaw
+28.700. **Neither of those has anything to do with the fused geometry.**

### Support-origin decomposition for the reactivated directions

| dir | OPEN | PERSISTENT | EXPOSED by post-gaze | NEW map voxel | created by map update |
|---|---|---|---|---|---|
| (−1,−1) | 104 | 5 (4.8%) | **77 (74.0%)** | 19 (18.3%) | 3 (2.9%) |
| (−1, 0) | 119 | 4 (3.4%) | **90 (75.6%)** | 22 (18.5%) | 3 (2.5%) |
| (−1, 1) | 107 | 4 (3.7%) | **80 (74.8%)** | 19 (17.8%) | 4 (3.7%) |
| ( 0, 1) | 79 | 4 (5.1%) | **52 (65.8%)** | 22 (27.8%) | 1 (1.3%) |
| **all four** | **409** | **17 (4.2%)** | **299 (73.1%)** | **82 (20.0%)** | **11 (2.7%)** |

(The blocked direction (0,−1) reads the same way: 58 OPEN — 4 persistent, 40
exposed, 12 new voxel, 2 map-update.)

**The reactivation mechanism is inspectable, not inferred**: roughly three
quarters of the support behind every reactivated direction is frontier structure
that already existed and was merely brought into view, one fifth is genuinely new
geometry, and persistent frontier contributes about 4%.

### Integrity

**All 46 pinned inputs byte-identical afterwards** — 10 MultiObject-3e artifacts,
4 MultiObject-3c artifacts, 4 scene-object geometry sources, all 26 saved
selected-object calibration/observation files, and the **single handoff
calibration/observation pair** (`c98b3c552dff13be…`, `f06e04c46e77db14…`).

Objects 141 `6ac98f6251b47337…`, 142 `6f90d985f8078a7d…`, 143
`bbc4b856a07d2be5…`, 145 (3c source) `8c9e7ffada6fb6a7…` — all unchanged.
`preexisting_objects_read_only` **true**, `selected_object_read_only` **true**,
`truth_opened` **false**, `quality_gate_used` **false**, `new_threshold_added`
**false**, `automatic_scene_scheduler` / `revisit_scheduler_used` /
`automatic_handoff_loop` all **false**.

Outputs written: the report, `frontier_reactivation.npz` (pre/post source voxel
keys, source and target geometry, state codes — 72 and 488 rows),
`frontier_reactivation_details.json`, and the manifest.
`tools/multiobject3f_compare.py` printed **`MULTIOBJECT3F_COMPLETE`** with
`"structural_fails": []` and exited **0**.

### Structural failures and code fixes

**Structural failures: none.** **Code fixes: none** — no MultiObject-3f file
needed repair and no frozen prior source was modified. The package ran as
applied, first time.

### What this establishes, and what it does not

Established, and it answers the central question **without forcing a single
cause**. **The reactivation was driven primarily by moving the attention window,
not by the fused geometry** — but geometry contributes measurably, and there is a
real interaction term.

- **Attention is sufficient.** With the **pre-fusion map** but the handoff gaze
  and updated history, frozen FSG6f returns `continue` with **4 candidates and
  the identical next gaze**. Not one fused surfel is required to reproduce the
  decision.
- **Geometry is not sufficient.** With the **post-fusion map** but the old gaze
  and history, it returns `no_frontier` with **0 candidates** — exactly the
  pre-handoff outcome. From the old gaze the 108 new voxels yield **zero**
  additional frontier entries.
- **The magnitudes are unequal but both non-zero.** Gaze alone accounts for
  **357 of the 416** frontier increase (**85.8%**), the map-only effect is
  **exactly 0**, and the interaction is **59 (14.2%)**. Among OPEN support behind
  the four reactivated directions, **73.1% was already frontier merely brought
  into view**, **20.0% comes from new map voxels**, 2.7% from the map update on
  pre-existing voxels, 4.2% persistent.
- **The decisive gate is identified.** Every unvisited direction had a projected
  continuation-corridor fraction of **exactly 0.000** before and **0.396–1.000**
  after; the corridor is computed **from the current gaze**. Two further purely
  attentional effects appear in the ledger: the relative 5-degree lattice moved
  three directions out of `ALREADY_VISITED` and three others out of
  `POLICY_BOUNDS`.
- **The persistent frontier did not move or change state at all** —
  `persistent_state_changed_count` 0, source and target shift exactly 0.0 m.

This refines, and partly deflates, the MultiObject-3e headline. The handoff's
value was real, but it was **attentional**: the cyclopean field supplied the
*look*, and the look is what restarted the controller. The 295 fused surfels were
a by-product, not the cause.

Not established. **One handoff, one object, one seed, one gaze** — nothing shows
this decomposition holds for a different unseen cell, object or scene. **Not a
claim that the fused geometry is useless** — it supplied 20% of the reactivating
OPEN support and 14.2% of the frontier increase, and a map has value beyond
restarting a controller. **No claim about what would happen if the returned
action were executed** — it was not, by design, so whether FSG6f makes progress
from (+18.700, −10.500) remains **untested**. **Not a defect claim against
FSG6f** — the gaze-local frontier extraction is the controller's documented
design, and nothing was tuned, extended or replaced. **No accuracy claim** —
evaluator truth stayed closed. **No general statement about the corridor gate** —
that it read 0.000 in every unvisited direction before is a measurement at this
one gaze, not a characterisation of the rule. And **no scheduler, no second
action, no automatic loop** was introduced.

**Next: interpret this audit before any second action.**
