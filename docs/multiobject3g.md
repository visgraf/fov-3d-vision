# MultiObject-3g — execute one returned local action

## Motivation

MultiObject-3e demonstrated one bounded cyclopean-to-local handoff. MultiObject-3f then isolated the cause of the returned FSG6f reactivation: **attention was sufficient**, while the fused geometry alone was not. With the pre-fusion map but the handoff gaze/history, the frozen policy returned the same four candidates and the same next gaze. With the post-fusion map under the old gaze/history, it remained at `no_frontier`.

The returned local gaze has still never been executed. MultiObject-3g asks the remaining bounded question:

> **Does executing exactly the local action produced by attentional reactivation actually resume useful local exploration?**

## One action, one return, stop

The experiment performs exactly this sequence:

```text
completed MultiObject-3f causal audit
        |
        v
consume the already-returned local gaze
        |
        v
replay the MultiObject-3e returned decision exactly
        |
        v
execute ONE new fixation through scene_render_fix.py
        |
        v
process frozen stereo
        |
        +-- <100 target points --> valid negative evidence, no fusion
        |
        `-- otherwise ---------> selected-object-only 12 mm fusion
        |
        v
ask frozen FSG6f for ONE subsequent decision
        |
        v
record that decision and STOP
```

The subsequent action is not executed.

## Action source

The gaze is not selected again and is not hand-picked. It is consumed from:

```text
MultiObject-3f returned_next_gaze_deg
```

and must agree exactly with the unexecuted `MultiObject-3e returned_local_policy_decision.next_gaze_deg` after an exact frozen-policy replay.

This matters because 3g is testing **execution of an already-justified action**, not introducing another policy choice.

## Frozen machinery

Unchanged:

- generic `tools/scene_render_fix.py` renderer;
- existing stereo path;
- `tools/multiobject2c_policy.py` target-label adapter;
- frozen FSG6f controller;
- 12 mm association rule;
- `<100` selected-object points = valid empty evidence and no fusion;
- selected-object seed-scoped policy history;
- all previously instantiated scene objects.

No watchdog, threshold, matcher, semantics, scheduler, interpolation or truth access is added.

## Outcomes are descriptive

The executed look records:

- target visible pixels;
- valid selected-object depth points and recovery fraction;
- empty/non-empty status;
- matched/new surfels;
- map size before/after;
- idempotence and purity;
- the one subsequent FSG6f decision.

The existing `<100` empty-look rule is inherited instrument semantics, not a new MultiObject-3g quality threshold. No measured recovery, map gain or next-policy state is used as a pass gate.

Descriptive measurement outcomes are reported as one of:

```text
VALID_NEGATIVE_EVIDENCE
LOCAL_ACTION_ADDED_GEOMETRY
LOCAL_ACTION_REMEASURED_EXISTING_GEOMETRY
LOCAL_ACTION_MEASURED_NO_ASSOCIATION
```

The subsequent local-policy state is reported as one of:

```text
LOCAL_EXPLORATION_CONTINUES
LOCAL_POLICY_RESTOPS_NO_FRONTIER
LOCAL_POLICY_RETURNS_OTHER_STOP
```

## Integrity

MultiObject-3g must preserve:

- the complete MultiObject-3f audit record;
- the complete MultiObject-3e execution state;
- all selected-object historical observations through the epistemic handoff;
- all pre-existing scene-object sources.

The only new observation is the single globally next fixation. Only valid points belonging to the active selected object may be fused.

## Expected outputs

A completed record contains at least:

- `prediction_manifest.json`;
- `returned_action_report.json`;
- `returned_action_patch.npz`;
- `returned_action_rgb.png`;
- updated `object_<id>_surface_map.npz` and `.ply`;
- updated `object_<id>_policy_trace.json`;
- `scene_graph.json`;
- `scene_cyclopean_footprints.npz` and `.png`;
- one acquisition directory containing only the newly executed returned action;
- `render.log`.

## Deliberately deferred

- executing the new subsequent FSG6f action;
- a second epistemic handoff;
- automatic local/global alternation;
- revisiting other unfinished objects;
- scene scheduling;
- modifying the local controller or cyclopean selector.

The experiment stops after one executed returned action and one subsequent local-policy decision.

## Results

Run 2026-09-22 on the workstation. `MULTIOBJECT3G_COMPLETE`, `structural_fails:
[]`, no FAIL line anywhere; the comparator agrees and exits 0.
`pre_action_policy_replayed_exactly` **true**.

**The bounded answer is yes on both halves, but the geometric yield is small and
should not be overstated.**

Executing exactly the already-returned gaze **(+18.700, −10.500)** produced
**useful local evidence** — **648** valid selected-object depth points, well above
the inherited 100-point limit, so **not** an empty look — and frozen FSG6f then
returned `continue` with a concrete next gaze **(+13.700, −10.500)** and **4
candidates**: `LOCAL_EXPLORATION_CONTINUES`.

But of those 648 points, **607 matched existing surfels and only 41 were new**.
The map grew **6,721 → 6,762 (+41, +0.6%)** and the footprint **2,107 → 2,125
cells (+18)**. The packaged classifier reports
**`LOCAL_ACTION_ADDED_GEOMETRY`** because new > 0, which is literally true — but
**93.7% of the measured points re-measured surface the map already held.**

The subsequent action was **recorded and not executed**;
`experiment_stop: BOUNDED_AFTER_ONE_EXECUTED_RETURNED_ACTION_AND_ONE_NEXT_DECISION`.

### Provenance

Working tree clean at the start. Package commit **`c955696`** adds **exactly the
seven MultiObject-3g files, all `A`**; parent result **`1d18de9`**.

Frozen audit at full scope: **every tracked non-documentation source present at
`1d18de9` — 306 files** across `tools/`, `tools/dev/` and `scenes/`.
`git diff 1d18de9 HEAD` over that set is **empty (0 lines)** and all **306 sha256
are SAME**. The complete changed-file list between parent result and HEAD is the
seven new 3g files and nothing else. The machinery reused unchanged:
`fsg6f_frontier.py` `d636c9405d719916…`, `multiobject2c_policy.py`
`f4d4a08b00981466…`, `scene_render_fix.py` `6e70bbb78c1043ec…`,
`reality2_render_fix.py` `9f1433d189fbcbb5…` (unchanged, **never invoked**),
`fsg3_surface_map.py` `1b9dbeb873105ec9…`, `cyclopean1e_gaze.py`
`a3599ea14fc00e60…`.

Note on the prompt's apply step: `MULTIOBJECT3G_APPLY.md` and
`MULTIOBJECT3G_CHECKS.md` are **not present in the repository** — the package was
already applied at `c955696`, and its checks live at
`docs/multiobject3g-checks.md`. I ran those, exactly as written.

### Parent-chain provenance

Parent located **by manifest**: exactly one
`MultiObject3f-frontier-reactivation-audit-v1` record —
`previews/multiobject3f/full-seed2111` — with `truth_opened` **false**,
`acquisitions_added` **0**, `fusion_iterations_added` **0**,
`returned_local_action_executed` **false**, `pre_policy_replayed_exactly` and
`post_policy_replayed_exactly` both **true**, `reactivation_status`
`LOCAL_POLICY_REACTIVATION_REPRODUCED`, `structural_fails` **[]**. Its causal
result is carried forward intact: `geometric_frontier_factorial`
`{PRE_MAP_PRE_GAZE 72, PRE_MAP_POST_GAZE 429, POST_MAP_PRE_GAZE 72,
POST_MAP_POST_GAZE 488}` with both counterfactuals recorded.

It resolves to `previews/multiobject3e/full-seed2111` (the execution state:
handoff at global step **79**, gaze (+23.700, −5.500), map 6,721 points, 14
selected-object fixations, `returned_local_action_executed` **false**) and to
`previews/multiobject3c/full-seed2111` (the seed-scoped history, steps 66..78).

**Both the object and the action were consumed, never hand-picked:**

| quantity | value | source |
|---|---|---|
| `selected_object_id` | **145** | the 3f manifest |
| action gaze | **(+18.700, −10.500)** | 3f `returned_next_gaze_deg` |
| cross-check | **identical** | 3e `returned_local_policy_decision.next_gaze_deg` |

`action_source` in the record reads *"MultiObject-3f returned_next_gaze_deg,
cross-checked to exact MultiObject-3e replay"*.

### Exact pre-action replay, and the executed gaze

The MultiObject-3e returned decision was replayed **before any render** and
matched: `stop` **False**, `reason` **`continue`**, `next_gaze_deg` **(+18.700,
−10.500)**, `current_gaze_deg` (+23.700, −5.500), frontier **488**, OPEN **391**,
map-resolved 24, boundary-resolved 73, voxels **1,467**,
`candidates_before_consensus_count` **4**, rejected **0**.
`pre_action_policy_replayed_exactly: true`.

**`executed_gaze_deg` == `pre_action_policy_decision.next_gaze_deg` — verified
True.** The experiment executed the recorded parent action, not a new choice.

### One new global step, and no history rerendered

Exactly one fixation at **global step 80** = 79 + 1, through the generic
`tools/scene_render_fix.py`.

- the record's `acquisition/` holds **exactly one entry, `fix_80`**;
- **none** of the fourteen prior steps (66..79) appears in it;
- `added_fixations` **1**, `parent_fixations_rerendered` **0**;
- all **26** saved history files and the **handoff acquisition pair** are
  byte-identical afterwards.

### The executed look

| quantity | value |
|---|---|
| target visible pixels | **10,007** (15.3% of frame) |
| target valid depth points | **648** |
| **target depth recovery fraction** | **6.48%** |
| whole-frame valid | 32,131 of 65,536 (**49.0%**) |
| `empty_look` | **false** (648 ≥ the inherited 100 limit) |
| `measurement_status` | **`LOCAL_ACTION_ADDED_GEOMETRY`** |

The recovery of 6.48% sits back in object 145's usual band — below the handoff
look's 9.81% and close to its 6.68% seed. The frame-wide valid fraction is the
highest yet at 49.0%, but that is the **wood floor**, not the target: the image
shows the fovea dominated by floor with the terracotta panel and cream stripe
reduced to a thin band along the top edge. Looking down at −10.5° put most of the
object out of view.

### Association, purity, idempotence

Fused **once** with the unchanged 12 mm rule, selected-object valid points only:

| quantity | value |
|---|---|
| input points | 648 |
| **matched** | **607 (93.7%)** |
| **new** | **41 (6.3%)** |
| map points before → after | **6,721 → 6,762 (+41, +0.6%)** |
| `idempotent_replay` | **true** |
| `selected_object_map_pure` | **true**, ids exactly `{145}` |
| multi-look surfels | 4,086 (max support 6) |
| range min/med/max | 2.5265 / 2.7625 / 3.0033 m — **unchanged** from 3e |

`object_145_surface_map.ply` carries **6,762** vertices. The map's range envelope
did not move at all, consistent with an action that mostly re-measured the same
surface.

### The subsequent FSG6f decision — recorded, not executed

| field | pre-action (3e returned) | subsequent (3g) |
|---|---|---|
| `stop` | False | **False** |
| `reason` | `continue` | **`continue`** |
| `next_gaze_deg` | (+18.700, −10.500) | **(+13.700, −10.500)** |
| `current_gaze_deg` | (+23.700, −5.500) | (+18.700, −10.500) |
| `frontier_voxel_count` | 1,467 | 1,487 |
| `frontier_count` / `raw_count` | 488 | **278** |
| `frontier_open_count` | 391 | **167** |
| `frontier_map_resolved_count` | 24 | 6 |
| `frontier_boundary_resolved_count` | 73 | **105** |
| `candidates_before_consensus_count` | 4 | **4** |
| `consensus_rejected_candidate_count` | 0 | 0 |

Selected candidate: delta **(−5.0, 0.0)** on the frozen lattice, frontier score
**20.25**, support 63 (raw 95), map-resolved support 1, predicted new angular area
**135.71 deg²**, continuation corridor **allowed** at combined fraction **0.463**
(threshold 0.15), consensus **allowed** with open 63 against resolved 32.
`frontier_state_radius_m` **0.012**.

**The frontier count fell 488 → 278 while the candidate count stayed at 4.** That
is exactly what MultiObject-3f's decomposition predicts: the frontier total tracks
the current-gaze extraction window, and the window moved back over territory the
object had already visited. It is recorded as consistent with that finding, not as
independent confirmation of it.

**`subsequent_local_action_executed: false`.** The written policy trace carries
**15** entries with `last_action_executed: false`.

### Boundedness and integrity

`added_fixations` **1**, `parent_fixations_rerendered` **0**,
`fusion_iterations_added` **1**, `growth_loop_iterations_added` **0**,
`subsequent_local_action_executed` **false**, `automatic_scene_scheduler`
**false**, `revisit_scheduler_used` **false**, `watchdog_changed` **false**,
`quality_gate_used` **false**, `policy_source_modified` **false**,
`truth_opened` **false**, `renderer_entrypoint` `tools/scene_render_fix.py`,
`policy_adapter_source` `tools/multiobject2c_policy.py`,
`empty_look_min_target_points` **100**, `fusion_rule` {0.012, 0.012}.

**All 51 pinned inputs byte-identical afterwards** — 4 MultiObject-3f artifacts,
11 MultiObject-3e artifacts, 4 MultiObject-3c artifacts, 4 scene-object geometry
sources, all 26 saved selected-object history files, and the MultiObject-3e
handoff acquisition pair.

**The active object's 3e source was not modified in place**:
`previews/multiobject3e/.../object_145_surface_map.npz` is still
`b085e591f0b50b0e…`; the updated map is written separately into the 3g record as
`ac46e7fc815d103c…`.

| object | sha256 | points | ids |
|---|---|---|---|
| 141 | `6ac98f6251b47337…` | 155,684 | `{141}` |
| 142 | `6f90d985f8078a7d…` | 310,884 | `{142}` |
| 143 | `bbc4b856a07d2be5…` | 42,988 | `{143}` |
| 145 (3e source) | `b085e591f0b50b0e…` | 6,721 | `{145}` |

### Scene and footprint relations

`selected_object_fixations_total` **15**, `last_global_step` **80**.

| object | points | footprint cells | area | vs 3e |
|---|---|---|---|---|
| 141 | 155,684 | 37,654 | 376.54 deg² | unchanged |
| 142 | 310,884 | 62,784 | 627.84 deg² | unchanged |
| 143 | 42,988 | 17,947 | 179.47 deg² | unchanged |
| **145** | **6,762** | **2,125** | **21.25 deg²** | 2,107 → 2,125 (+18) |

**All six pairwise overlaps and the all-object overlap remain 0.**

### Environment and wall time

Blender 5.2.1 LTS headless, Cycles, **OPTIX** on an RTX 4090 (driver 595.84);
host `.venv/bin/python` 3.12.3. **11.2 s** — one Blender launch plus the
history replay.

### Checks

`py_compile` clean on all five modules. The four prescribed lines appeared
verbatim:

```text
[multiobject3g-progress] PASS threshold_free=true one_action=true one_next_decision=true auto_loop=false
[multiobject3g-action] PASS parent_action_consumed=true one_fixation=true generic_renderer=true selected_only=true
[multiobject3g-return] PASS pre_action_replay=true one_next_decision=true next_action_executed=false auto_loop=false
[multiobject3g-check] SUMMARY passed=9 failed=0
```

All **ten** negatives are genuine source-mutation controls, each exiting **1**
with a named detector; **none exited 2**:

| negative | rc | detected by |
|---|---|---|
| `handpick` | 1 | `parent_reactivation_action_consumed_not_handpicked` |
| `ignorecausal` | 1 | `attention_causal_parent_required` |
| `skipreplay` | 1 | `exact_pre_action_policy_replay` |
| `multiprobe` | 1 | `one_returned_action_generic_renderer_no_history_rerender` |
| `legacyrenderer` | 1 | `one_returned_action_generic_renderer_no_history_rerender` |
| `crossfuse` | 1 | `selected_only_fusion_existing_objects_read_only` |
| `skipempty` | 1 | `inherited_empty_look_and_fusion_rule` |
| `executeagain` | 1 | `single_subsequent_frozen_policy_decision_unexecuted` |
| `autoloop` | 1 | `bounded_no_scheduler_threshold_or_auto_loop` |
| `qualitygate` | 1 | `bounded_no_scheduler_threshold_or_auto_loop` |

The **exit-2 escape branch was verified live**. **No regression**: **28/28** prior
suites green and **188/188** prior negatives still firing, **none weakened**. The
**Cyclopean-1f caveat stands and 1f was not edited**.

### Structural failures and code fixes

**Structural failures: none.** **Code fixes: none** — no MultiObject-3g file
needed repair and no frozen prior source was modified. The package ran as
applied, first time.

### What this establishes, and what it does not

Established, within one bounded cycle. **The action returned by attentional
reactivation was executable and did not collapse.** It was **consumed, not
chosen** — the gaze came from the 3f manifest and matched the 3e returned
decision after an exact replay — it produced **useful local evidence** (648 valid
target points, comfortably non-empty), it **fused cleanly** (idempotent, pure
`{145}`, selected-object points only), and frozen FSG6f then returned
`continue` with **4 candidates** and a concrete next gaze at
**(+13.700, −10.500)**: `LOCAL_EXPLORATION_CONTINUES`. So the full bounded loop
— attention supplies a look, the local controller reactivates, its action is
executed, and the controller is still able to continue — closed once, with every
piece of machinery frozen and every pre-existing object byte-identical.

Established, and stated plainly because it qualifies the above. **The geometric
yield was small.** **607 of 648 points (93.7%) matched existing surfels; only 41
(6.3%) were new.** The map grew **+0.6%**, the footprint by **18 cells**, and the
range envelope **did not move at all**. Recovery was **6.48%**, back in this
object's ordinary band rather than the handoff look's 9.81%, and the image shows
why: at pitch −10.5° the fovea is mostly floor, with the target reduced to a band
at the top. The packaged label `LOCAL_ACTION_ADDED_GEOMETRY` is literally correct
and also the weakest of its positive categories; **this was much closer to a
re-measurement than to an expansion.**

Not established. **One executed action, one object, one seed** — nothing here
shows the cycle repeats, converges, or remains productive; **no second action was
taken, by design**, and the subsequent gaze at (+13.700, −10.500) is
**untested**. **Not evidence that alternation is a good policy** — a single
continuing decision is not a trajectory, and the small geometric yield of this
step is a reason for caution rather than confidence. **The frontier fall 488 →
278 is not independent evidence for anything** — it is consistent with
MultiObject-3f's finding that the count tracks the gaze window, and this run
neither re-derives nor tests that. **No accuracy claim** — evaluator truth stayed
closed; 6,762 points describe the representation. **No object completeness** —
the seen-but-unmeasured residue was not re-audited here and nothing suggests it
shrank. **No claim that the low recovery is irreducible** — no matcher, baseline,
vergence or illumination was changed. And **no scheduler, no automatic loop, no
second handoff, no watchdog or threshold change** was introduced.

**Next: interpret this one bounded cycle before taking another action.**
