# MultiObject-3h — one more local productivity step

## Motivation

MultiObject-3e/3f established that the cyclopean handoff reactivated frozen FSG6f primarily by **moving attention**, not by the small amount of newly fused geometry. MultiObject-3g then executed the first local action returned by that reactivation. The controller remained live, but the step was geometrically modest: 607 of 648 associated target points matched existing surfels and only 41 were new.

MultiObject-3h asks one remaining local question before the planned FullScene-1 detour:

> **Was that low novelty merely one transitional step, or does the next already-returned local action again behave mainly as re-measurement?**

This is a measurement question, not a new stopping rule.

## One more action, one return, stop

```text
completed MultiObject-3g record
        |
        v
consume its already-returned subsequent local gaze
        |
        v
replay that frozen FSG6f decision exactly
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
measure novelty and compare with the 3g local step
        |
        v
ask frozen FSG6f for ONE subsequent decision
        |
        v
record the decision and STOP
```

The newly returned action is not executed.

## Action source

The gaze is neither selected again nor hard-coded. It is consumed from:

```text
MultiObject-3g subsequent_local_policy_decision.next_gaze_deg
```

and the complete frozen policy state is reconstructed from the seed-scoped history through the epistemic handoff and first returned local action. The saved 3g decision must replay exactly before the gaze is rendered.

On the currently measured lineage this is expected to be the next global fixation after step 80, but the implementation derives the step number from the parent record rather than encoding it.

## Productivity is a readout, not a gate

For the new look the experiment records:

- target-visible pixels and valid target-depth points;
- target-depth recovery fraction;
- matched and new surfels;
- novelty fraction `new / (new + matched)` when defined;
- map-point change;
- raw angular-footprint cell change;
- range min/median/max before and after;
- the corresponding measured quantities from the first post-handoff local action in MultiObject-3g;
- the one subsequent FSG6f decision.

No value is compared with a new productivity threshold. A second low-novelty result is evidence to interpret after the run, not a reason for the runner to stop, retry, tune or choose another gaze.

## Frozen machinery

Unchanged:

- generic `tools/scene_render_fix.py` renderer;
- existing stereo path;
- `tools/multiobject2c_policy.py` target-label adapter;
- frozen FSG6f controller;
- 12 mm association rule;
- `<100` selected-object points = valid empty evidence and no fusion;
- selected-object seed-scoped policy history;
- every previously instantiated scene object.

No watchdog, matcher, semantics, scheduler, interpolation, truth access, novelty threshold or automatic loop is added.

## Expected outputs

A completed record contains at least:

- `prediction_manifest.json`;
- `local_productivity_report.json`;
- `local_productivity_patch.npz`;
- `local_productivity_rgb.png`;
- updated `object_<id>_surface_map.npz` and `.ply`;
- updated `object_<id>_policy_trace.json`;
- `scene_graph.json`;
- `scene_cyclopean_footprints.npz` and `.png`;
- one acquisition directory containing only the newly executed action;
- `render.log`.

## Deliberately deferred

- executing the newly returned FSG6f action;
- a second epistemic handoff;
- automatic local/global alternation;
- revisiting other unfinished objects;
- scene scheduling;
- any definition of “productive enough”.

After this bounded step, interpret the two consecutive post-handoff local actions. The planned next project-scale move is the **FullScene-1 bounded full-scene calibration** detour.

## Results

Run 2026-09-22 on the workstation. `MULTIOBJECT3H_COMPLETE`, `structural_fails:
[]`, no FAIL line anywhere; the comparator agrees and exits 0.
`pre_action_policy_replayed_exactly` **true**.

**The second post-handoff local action produced no geometry at all.**

Executing exactly the gaze MultiObject-3g returned — **(+13.700, −10.500)** —
yielded **65** valid selected-object depth points, **below the inherited
100-point limit**. Under the unchanged Reality-2b rule this is
**`VALID_NEGATIVE_EVIDENCE`**: the observation was kept, **nothing was fused**,
and the map, footprint and range envelope are **all byte-identically unchanged**
(6,762 points, 2,125 cells, 2.5265 / 2.7625 / 3.0033 m).

Frozen FSG6f nevertheless returned `continue` again, with next gaze
**(+13.700, −5.500)** and **2** candidates: `LOCAL_EXPLORATION_CONTINUES`. That
action was **recorded and not executed**.

**Answering the question asked, without a threshold: the two measurements point
in the same qualitative direction, and the second strengthens rather than
changes the first.** Step 1 was 93.7% re-measurement with 41 new surfels from 648
valid points; step 2 added **zero** from 65. Across both post-handoff local
steps, **713 valid target points produced 41 new surfels in total**, all of them
in the first step. Local productivity did not recover — it fell to nothing.

### Provenance

Working tree clean at the start. The prospective package was applied and
committed at **`fcb7180`**, adding **exactly the seven MultiObject-3h files, all
`A`**; parent result **`8633eb4`**.

**Apply verification.** The four companion files (`MULTIOBJECT3H_APPLY.md`,
`_CHECKS.md`, `_CODE_PROMPT.md`, `_HANDOFF.md`) are delivered outside the
repository and are correctly absent from it; the repository check documentation
is `docs/multiobject3h-checks.md`, which is what was run. The applied package was
verified against the delivered ZIP
(`~/Downloads/multiobject3h-one-more-local-productivity-step.zip`): **7 entries,
all 7 byte-identical** to the committed files, 0 different, 0 missing.

Frozen audit at full scope: **every tracked non-documentation source present at
`8633eb4` — 311 files** across `tools/`, `tools/dev/` and `scenes/`.
`git diff 8633eb4 HEAD` over that set is **empty (0 lines)** and all **311 sha256
are SAME**. The complete changed-file list between parent result and HEAD is the
seven new 3h files and nothing else. Machinery reused unchanged:
`fsg6f_frontier.py` `d636c9405d719916…`, `multiobject2c_policy.py`
`f4d4a08b00981466…`, `scene_render_fix.py` `6e70bbb78c1043ec…`,
`reality2_render_fix.py` `9f1433d189fbcbb5…` (unchanged, **never invoked**),
`fsg3_surface_map.py` `1b9dbeb873105ec9…`, `multiobject3g_run.py`
`0eb7382b836e0771…`.

### Parent provenance and consumed action

Parent located **by manifest**, not by assumed path: exactly one
`MultiObject3g-one-returned-local-action-v1` record —
`previews/multiobject3g/full-seed2111`. **All five required gates hold:**

| gate | value |
|---|---|
| clean structural status | `structural_fails: []` |
| truth closed | `truth_opened: false` |
| exactly one executed 3g action | `added_fixations: 1` |
| subsequent decision unexecuted | `subsequent_local_action_executed: false` |
| `subsequent_policy_status` | **`LOCAL_EXPLORATION_CONTINUES`** |

**Both the object and the gaze were consumed, never hand-picked:**

| quantity | value | source |
|---|---|---|
| `selected_object_id` | **145** | the 3g manifest |
| action gaze | **(+13.700, −10.500)** | 3g `subsequent_local_policy_decision.next_gaze_deg` |

`action_source` reads *"MultiObject-3g subsequent_local_policy_decision.next_gaze_deg
after exact replay"*.

### Exact pre-action replay

The saved MultiObject-3g subsequent decision was reconstructed from the full
seed-scoped history and **reproduced exactly before any render**: `stop`
**False**, `reason` **`continue`**, `next_gaze_deg` **(+13.700, −10.500)**,
`current_gaze_deg` (+18.700, −10.500), frontier **278**, OPEN **167**,
map-resolved 6, boundary-resolved 105, voxels **1,487**,
`candidates_before_consensus_count` **4**, rejected **0**.
`pre_action_policy_replayed_exactly: true`.

**`executed_gaze_deg` == `pre_action_policy_decision.next_gaze_deg` — verified
True.** The run executed the recorded parent action, not a new choice.

### One new global step, and no history rerendered

Exactly one fixation at **global step 81** = 80 + 1, through the generic
`tools/scene_render_fix.py`, OPTIX.

- the record's `acquisition/` holds **exactly one entry, `fix_81`**;
- **none** of the fifteen prior steps (66..80) appears in it;
- `added_fixations` **1**, `parent_fixations_rerendered` **0**;
- all **30** history calibration/observation files are byte-identical afterwards.

Environment: Blender 5.2.1 LTS headless, Cycles, **OPTIX** on an RTX 4090 (driver
595.84); host `.venv/bin/python` 3.12.3. **11.4 s** — one Blender launch plus the
15-look history replay.

### The new look, and fusion association

| quantity | value |
|---|---|
| target visible pixels | **4,831** (7.4% of frame) |
| target valid depth points | **65** |
| **target depth recovery fraction** | **1.35%** |
| whole-frame valid | 36,740 of 65,536 (**56.1%**) |
| `empty_look` | **true** (65 < the inherited 100 limit) |
| `fused` | **false** |
| matched surfels | **0** |
| new surfels | **0** |
| `novelty_fraction` | **null** (undefined — nothing was fused) |
| `idempotent_replay` | true |
| `selected_object_map_pure` | **true**, ids exactly `{145}` |

The inherited `<100` rule fired exactly as specified: the binocular observation
entered policy history, **nothing was fused**, the map was left unchanged, and
the experiment continued to its one policy call. That rule is inherited
instrument semantics, not a MultiObject-3h threshold, and the `skipempty`
negative exists to enforce it.

The image shows why the look measured so little: the fovea is dominated by the
**wood floor** across its lower half, a grey wall band above it, and object 145
reduced to a **sliver at the top-right corner** — a cream panel edge at the left
and the terracotta panel at the right. The 56.1% frame-wide validity is the
floor, not the target.

### Side-by-side: the two post-handoff local steps

| quantity | **3g** (step 80) | **3h** (step 81) |
|---|---|---|
| gaze | (+18.700, −10.500) | **(+13.700, −10.500)** |
| target visible pixels | 10,007 (15.3%) | **4,831 (7.4%)** |
| target valid depth points | 648 | **65** |
| recovery fraction | 6.48% | **1.35%** |
| empty look | false | **true** |
| matched surfels | 607 | **0** |
| new surfels | **41** | **0** |
| novelty fraction | **0.0633** | **null (nothing fused)** |
| map points | 6,721 → 6,762 (**+41**) | 6,762 → 6,762 (**0**) |
| raw footprint cells | 2,107 → 2,125 (**+18**) | 2,125 → 2,125 (**0**) |
| range envelope | unmoved | **unmoved** |
| measurement status | `LOCAL_ACTION_ADDED_GEOMETRY` | **`VALID_NEGATIVE_EVIDENCE`** |
| subsequent policy | `LOCAL_EXPLORATION_CONTINUES` | **`LOCAL_EXPLORATION_CONTINUES`** |

**Two-step totals: 713 valid target points → 41 new surfels, 607 matched.** All
of the novelty is in the first step.

The wider trajectory of the recovery fraction across this object's life is
**6.68%** (3b seed) → **9.81%** (3e handoff look) → **6.48%** (3g) → **1.35%**
(3h), and target visibility fell 15.3% → 7.4% of frame between the two local
steps. The policy is walking the gaze progressively off the object. **Recorded as
measured; no threshold or gate was introduced anywhere.**

### The newly returned FSG6f decision — recorded, not executed

| field | pre-action (3g returned) | subsequent (3h) |
|---|---|---|
| `stop` | False | **False** |
| `reason` | `continue` | **`continue`** |
| `next_gaze_deg` | (+13.700, −10.500) | **(+13.700, −5.500)** |
| `current_gaze_deg` | (+18.700, −10.500) | (+13.700, −10.500) |
| `frontier_voxel_count` | 1,487 | 1,487 |
| `frontier_count` / `raw_count` | 278 | **165** |
| `frontier_open_count` | 167 | **100** |
| `frontier_map_resolved_count` | 6 | 3 |
| `frontier_boundary_resolved_count` | 105 | 62 |
| **`candidates_before_consensus_count`** | 4 | **2** |
| `consensus_rejected_candidate_count` | 0 | 0 |

Selected candidate: delta **(0.0, +5.0)** on the frozen lattice, frontier score
**6.42** (down from 20.25 at 3g), support **23** (raw 29), map-resolved support
1, predicted new angular area **115.64 deg²**, continuation corridor **allowed**
at combined fraction **1.000**, consensus **allowed** with open 23 against
resolved 6. `frontier_state_radius_m` **0.012**.

`frontier_voxel_count` is **unchanged at 1,487** — as it must be, since nothing
was fused. The frontier total fell 278 → 165 and the candidate count 4 → 2; the
selected candidate's frontier score fell roughly threefold. **Recorded as
measured.**

**`subsequent_local_action_executed: false`.** The written policy trace carries
**16** entries with `last_action_executed: false`.

### Integrity

**All 52 pinned inputs byte-identical afterwards** — 9 MultiObject-3g artifacts,
2 MultiObject-3f artifacts, 4 MultiObject-3e artifacts, 3 MultiObject-3c
artifacts, 4 scene-object geometry sources, and all **30** history
calibration/observation files spanning steps 66..80.

**The active object's 3g source was not modified in place**:
`previews/multiobject3g/.../object_145_surface_map.npz` is still
`ac46e7fc815d103c…`. Because this look was empty and nothing fused, the map
written into the 3h record is byte-identical to it — which is the correct
outcome, not a copy error: `fusion_iterations_added` is **0**.

| object | sha256 | points | ids |
|---|---|---|---|
| 141 | `6ac98f6251b47337…` | 155,684 | `{141}` |
| 142 | `6f90d985f8078a7d…` | 310,884 | `{142}` |
| 143 | `bbc4b856a07d2be5…` | 42,988 | `{143}` |
| 145 (3g source) | `ac46e7fc815d103c…` | 6,762 | `{145}` |

Flags: `added_fixations` 1, `parent_fixations_rerendered` 0,
`fusion_iterations_added` **0**, `growth_loop_iterations_added` 0,
`subsequent_local_action_executed` false, `automatic_scene_scheduler` false,
`revisit_scheduler_used` false, `watchdog_changed` false, `quality_gate_used`
false, `policy_source_modified` false, `truth_opened` false,
`renderer_entrypoint` `tools/scene_render_fix.py`, `policy_adapter_source`
`tools/multiobject2c_policy.py`, `empty_look_min_target_points` **100**,
`fusion_rule` {0.012, 0.012}.

Scene after: `selected_object_fixations_total` **16**, `last_global_step` **81**.
Footprints 141 **37,654**, 142 **62,784**, 143 **17,947**, 145 **2,125** cells —
**all unchanged from 3g**, and **all six pairwise overlaps and the all-object
overlap remain 0**.

### Checks

`py_compile` clean on all five modules. The five prescribed lines appeared
verbatim:

```text
[multiobject3h-progress] PASS threshold_free=true one_action=true productivity_diagnostic=true auto_loop=false
[multiobject3h-action] PASS parent_action_consumed=true one_fixation=true generic_renderer=true selected_only=true
[multiobject3h-productivity] PASS descriptive=true parent_comparison=true threshold=false
[multiobject3h-return] PASS pre_action_replay=true one_next_decision=true next_action_executed=false auto_loop=false
[multiobject3h-check] SUMMARY passed=9 failed=0
```

All **ten** negatives are genuine source-mutation controls, each exiting **1**
with a named detector; **none exited 2**:

| negative | rc | detected by |
|---|---|---|
| `handpick` | 1 | `parent_continuing_action_consumed_not_handpicked` |
| `skipreplay` | 1 | `exact_parent_action_policy_replay` |
| `multiprobe` | 1 | `one_local_action_generic_renderer_no_history_rerender` |
| `legacyrenderer` | 1 | `one_local_action_generic_renderer_no_history_rerender` |
| `crossfuse` | 1 | `selected_only_fusion_existing_objects_read_only` |
| `skipempty` | 1 | `inherited_empty_look_and_fusion_rule` |
| `executeagain` | 1 | `one_new_subsequent_decision_not_executed` |
| `autoloop` | 1 | `bounded_no_scheduler_threshold_or_auto_loop` |
| `productivitygate` | 1 | `productivity_is_descriptive_not_gate` |
| `qualitygate` | 1 | `bounded_no_scheduler_threshold_or_auto_loop` |

The **exit-2 escape branch was verified live**. **No regression**: **29/29**
prior suites green and **198/198** prior negatives still firing, **none
weakened**. The **Cyclopean-1f caveat stands and 1f was not edited**.

### Structural failures and code fixes

**Structural failures: none.** **Code fixes: none** — no MultiObject-3h file
needed repair and no frozen prior source was modified. The package ran as
applied, first time.

### What this establishes, and what it does not

Established, mechanically. **The second post-handoff local action executed
cleanly and the bounded contract held.** The gaze was **consumed** from the 3g
record and the parent decision **replayed exactly** before rendering; **exactly
one** new globally numbered fixation was taken at step 81 through the generic
renderer with **zero** historical rerenders; the inherited `<100` empty-look rule
was applied unchanged; the map stayed **pure `{145}`**; every one of the **52**
pinned inputs and all three other persistent objects stayed **byte-identical**;
and the one newly returned FSG6f decision was **recorded and not executed**.

Established, measured. **The second step added no geometry.** 65 valid target
points at **1.35%** recovery, below the inherited limit; `VALID_NEGATIVE_EVIDENCE`;
**0 matched, 0 new, novelty undefined**; map, footprint and range envelope
**unchanged**. The local controller nevertheless returned `continue` with
**2** candidates and a next gaze at (+13.700, −5.500).

**Answering the question directly: the second measurement does not change the
interpretation of the first — it points the same way, more sharply.** Step 1 was
already dominated by re-measurement (93.7% matched, 6.3% novelty); step 2
produced nothing at all. Across both, **713 valid target points yielded 41 new
surfels, every one of them in step 1**. Alongside that, target visibility halved
(15.3% → 7.4% of frame), recovery fell 6.48% → 1.35%, the frontier total fell
278 → 165, the candidate count 4 → 2 and the leading frontier score 20.25 → 6.42.
**Every one of these is a descriptive measurement; no threshold, gate or ranking
was introduced, and the `productivitygate` negative exists to keep it that way.**

Not established. **Two steps are not a trend** — two consecutive observations on
one object at one seed cannot establish a rate, a limit, or that a third step
would also be empty; **no third action was taken, by design**, so (+13.700,
−5.500) is **untested**. **Not a claim that the local controller is failing** —
it behaved exactly as specified, returned admissible candidates both times, and
**nothing was tuned, extended or replaced**. **Not an explanation** — this run
measures *that* productivity fell, not *why*; the co-occurrence with the gaze
walking off the object is an observation, and this experiment ran no
counterfactual to test it. **No accuracy claim** — evaluator truth stayed closed;
6,762 points describe the representation, not the scene. **No object
completeness** — the seen-but-unmeasured residue was not re-audited and nothing
here suggests it changed. **No claim the low recovery is irreducible** — no
matcher, baseline, vergence or illumination was altered. And **no scheduler, no
automatic loop, no second handoff, no watchdog or threshold change**.

**Next: FullScene-1 is deliberately deferred until Chat/Luiz interprets this
result.**
