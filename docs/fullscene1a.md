# FullScene-1a — Scene State Snapshot

## Purpose

FullScene-1a is the formal starting point of the first bounded full-scene calibration. It freezes the exact post-MultiObject-3h state and asks one scene-level question without taking another look:

> What does the observer currently believe the scene contains, and which already-observed but uninstantiated object is next under the existing scene-selection rule?

This is the `S0` initial condition for FullScene-1.

## Why now

The MultiObject sequence established persistent multi-object geometry, scene-memory selection, epistemic audits, one global-to-local attention handoff, causal attentional reactivation, and two bounded post-handoff local actions. MultiObject-3h left another local action available but unexecuted. FullScene-1a deliberately defers that action and zooms out to the scene executive.

## Frozen experiment

FullScene-1a:

1. consumes the unique completed MultiObject-3h parent;
2. reads the live scene graph and verifies every persistent object map is pure and unchanged;
3. reconstructs the established scene-level observation scope from global steps 18 through the MultiObject-3h final step;
4. reports all positive observed instance ids and all ids that ever carried valid stereo depth;
5. excludes every currently instantiated object id;
6. reuses `multiobject3a_select.accumulate_candidate_support` and `select_next_object` unchanged;
7. writes a scene-state snapshot and a deterministic next-object selection;
8. executes no acquisition, fusion, growth, handoff, deferred local action or revisit.

The declared history intentionally preserves the earlier scene-selection scope beginning at step 18. It does not silently broaden the experiment backward into the older object-141 Reality/Cyclopean acquisition lineage.

## Scene inventory

For each live persistent object the snapshot records:

- object id;
- geometry type;
- current point count;
- current raw angular footprint-cell count;
- read-only snapshot status;
- prior epistemic status only where a still-current dedicated audit is reachable in the ancestry;
- for the currently active object, its current local-policy status, latest measurement status and deferred unexecuted gaze.

These are separate descriptive fields. FullScene-1a does not manufacture a single object-completeness score.

## Next-object rule

The candidate set is

\[
\mathcal C = \{\text{positive ids with valid-depth evidence in the declared history}\}
- \{\text{currently instantiated ids}\}.
\]

For each candidate, accumulated valid-depth support is summed over the saved observations. The next object is the largest support, with smaller integer id as the exact tie-break. This is the unchanged MultiObject-3a rule.

If a candidate is selected, the next increment is **FullScene-1b: one prescribed seed fixation for that selected object**. If no candidate remains, the first scene tour is frozen and evaluator truth may be opened only in a later evaluation increment.

## Not part of FullScene-1a

- no Blender/Cycles render or rerender;
- no new fixation;
- no surfel fusion;
- no local FSG6f action;
- no epistemic handoff;
- no revisit scheduler;
- no automatic scene scheduler;
- no semantic ranking or saliency score;
- no productivity, recovery, support or completeness threshold;
- no evaluator truth.

## Results

Run 2026-09-22 on the workstation, **host-side only**. `FULLSCENE1A_COMPLETE`,
`structural_fails: []`, no FAIL line anywhere; the comparator agrees and exits 0.

**S0 is established.** At the exact post-MultiObject-3h state the observer holds
**four persistent objects** — 141, 142, 143, 145 — has observed **five** positive
instance ids in the declared history, and **one** observed id remains
uninstantiated: **144**. Under the unchanged MultiObject-3a rule it is the next
object, on **2,436** accumulated valid-depth samples. It is the **only**
candidate, so there is **no runner-up and no margin**.

The MultiObject-3h deferred local gaze **(+13.700, −5.500)** remains
**unexecuted**, carried in the snapshot as a separate field rather than folded
into any completeness judgement.

### Provenance

Working tree clean at the start. The prospective package was applied and
committed at **`a094e2f`**, adding **exactly the six FullScene-1a files, all
`A`**; parent result **`15eedee`**.

**Apply verification.** The four companion files (`FULLSCENE1A_APPLY.md`,
`_CHECKS.md`, `_CODE_PROMPT.md`, `_HANDOFF.md`) are delivered outside the
repository and are correctly absent from it; the repository check documentation
is `docs/fullscene1a-checks.md`, which is what was run. The applied package was
verified against the delivered ZIP
(`~/Downloads/fullscene1a-scene-state-snapshot.zip`): **6 entries, all 6
byte-identical**, 0 different, 0 missing.

Frozen audit at full scope: **every tracked non-documentation source present at
`15eedee` — 316 files** across `tools/`, `tools/dev/` and `scenes/`.
`git diff 15eedee HEAD` over that set is **empty (0 lines)** and all **316 sha256
are SAME**. Machinery reused unchanged: `multiobject3a_select.py`
`ee8fc80971d48a7a…`, `fsg6f_frontier.py` `d636c9405d719916…`,
`scene_render_fix.py` `6e70bbb78c1043ec…`, `multiobject3h_run.py`
`b568747c794fe345…`, `cyclopean1a_topology.py` `6ed00fca00907f33…`.

The parent was located **by manifest**: exactly one
`MultiObject3h-one-more-local-productivity-step-v1` record —
`previews/multiobject3h/full-seed2111`. **All four required gates hold:**
`truth_opened` **false**, `structural_fails` **[]**, `added_fixations` **1** (its
one bounded second post-handoff action), and
`subsequent_local_action_executed` **false**.

The ancestry resolves cleanly through 3g → 3f → 3e → 3d → 3c → 3b → 3a → 2d →
2c → 2b → 2a → 1c.

### Read-only execution

**No Blender process started** — `pgrep blender` 0 before and after. **9.7 s**,
host `.venv/bin/python` 3.12.3. The record contains no acquisition directory; the
manifest records no acquisition, fusion, growth, handoff, revisit or scheduler
activity, `new_object_instantiated` **false**, `truth_opened` **false**,
`automatic_scene_scheduler` **false**, `revisit_scheduler_used` **false**.

**All 10 pinned inputs byte-identical afterwards** — 6 MultiObject-3h artifacts
and all 4 persistent object geometry sources — and every object map is
**instance-id pure**.

### S0 scene inventory

Instantiated ids **[141, 142, 143, 145]**, read from the **live MultiObject-3h
scene graph**, not hard-coded; `scene_object_count` **4**.

| object | geometry | points | raw footprint cells | prior epistemic status (source) |
|---|---|---|---|---|
| 141 | `SURFEL_MAP` | 155,684 | 37,654 | *(none reachable in this ancestry)* |
| 142 | `SURFEL_MAP` | 310,884 | 62,784 | **`ATTENTION_INCOMPLETE_RETAIN_FOR_REVISIT`** (MultiObject-2d) |
| 143 | `SURFEL_MAP` | 42,988 | 17,947 | **`ATTENTION_INCOMPLETE_RETAIN_FOR_REVISIT`** (MultiObject-1c) |
| 145 | `SURFEL_MAP` | 6,762 | 2,125 | *(no current prior label — see below)* |

All four are `read_only_in_snapshot: true` and `persistent: true`.

**Status evidence is reported conservatively, and the omissions are deliberate.**
Object **141**'s dedicated audits (Cyclopean-1f/1g) lie outside the ancestry this
package resolves, so no label is claimed for it. Object **145** has a dedicated
audit — MultiObject-3d, `ATTENTION_INCOMPLETE_RETAIN_FOR_REVISIT` with
`POLICY_EXHAUSTED_WITH_UNSEEN_TERRITORY` — but that audit is **stale**: its
geometry has since changed from 6,426 to 6,762 points through the MultiObject-3e
handoff and the MultiObject-3g action. The snapshot therefore correctly omits a
prior label for 145 and instead carries its **current** state in separate fields:

- `current_local_control_status` **`LOCAL_EXPLORATION_CONTINUES`**
- `latest_measurement_status` **`VALID_NEGATIVE_EVIDENCE`**
- `deferred_local_action_deg` **(+13.700, −5.500)**, `deferred_local_action_executed` **false**

**No single object-completeness score was synthesized anywhere.**

### Declared history scope

**64 observations, global steps 18..81**, with **0 duplicates** and **globally
contiguous** — verified independently. Composed of four declared groups whose
sizes sum exactly to 64:

| group | steps | count |
|---|---|---|
| `scene_history_143` | 18..41 | 24 |
| `selected_object_142` | 42..65 | 24 |
| `selected_object_145_base` | 66..78 | 13 |
| `handoff_and_post_handoff` | 79..81 | 3 |

The scope deliberately begins at **global step 18**, preserving the earlier
scene-selection scope and **not** broadening backward into the older object-141
Reality/Cyclopean acquisition lineage. **No historical rerender occurred** — this
increment renders nothing at all.

### Observed ids and the candidate set

Recomputed from the raw saved observations across the declared history:

- **positive observed instance ids: {141, 142, 143, 144, 145}**
- **ids with valid stereo depth: {141, 142, 143, 144, 145}** — identical set
- **uninstantiated observed ids: {144}**

So every positive id the observer has ever seen in this scope has also, at some
point, carried valid stereo depth; and exactly one of them has not yet become a
persistent object.

### Candidate table and the deterministic next object

Reusing `multiobject3a_select.accumulate_candidate_support` and
`select_next_object` **unchanged** — valid depth decides, visibility is
diagnostic, and no threshold is applied:

| id | valid-depth support | visible samples | valid fraction | contributing steps |
|---|---|---|---|---|
| **144** | **2,436** | 66,237 | 3.68% | 21 (1,410), 22 (252), 47 (107), 48 (340), 49 (327) |

`selection_status` **`NEXT_OBJECT_SELECTED`**, `selected_object_id` **144**,
`selected_valid_depth_samples` **2,436**, `tie_break`
`largest_valid_depth_support_then_smaller_object_id` — **not exercised**, since
144 is the sole candidate. **There is no runner-up and therefore no margin.**

**Ordering comparison against the MultiObject-3a snapshot** (diagnostic only,
derived from saved records, and it altered nothing):

| | MultiObject-3a (history 18..65) | FullScene-1a S0 (history 18..81) |
|---|---|---|
| candidates | 145 (13,047), 144 (2,436) | 144 (2,436) |
| selected | **145** | **144** |

**The ordering did not change.** MultiObject-3a ranked 145 ahead of 144; 145 was
duly seeded and grown and is now instantiated; 144 is next, exactly as that
ordering predicted. Worth recording precisely: **object 144's support is
unchanged at 2,436** — the **16 looks added since MultiObject-3a (steps 66..81)
contributed zero new valid-depth samples for 144**, and its contributing steps
remain 21, 22, 47, 48, 49. All of the recent attention went to object 145.

### The deferred local action

`deferred_local_action`: object **145**, gaze **(+13.700, −5.500)**,
`policy_status` **`LOCAL_EXPLORATION_CONTINUES`**, `executed` **false**,
`disposition` **`DEFERRED_DURING_FULLSCENE_SNAPSHOT`**. The
`execute_deferred` negative exists to enforce this and fires.

### Checks

`py_compile` clean on all four modules. The four prescribed lines appeared
verbatim:

```text
[fullscene1a-snapshot] PASS parent_3h=true read_only=true history_through_3h=true
[fullscene1a-inventory] PASS live_scene_graph=true object_maps_read_only=true status_descriptive=true
[fullscene1a-selection] PASS valid_depth_only=true frozen_selector=true no_threshold=true
[fullscene1a-check] SUMMARY passed=9 failed=0
```

All **nine** negatives are genuine source-mutation controls, each exiting **1**
with a named detector; **none exited 0 or 2**:

| negative | rc | detected by |
|---|---|---|
| `acquire` | 1 | `no_acquisition_fusion_or_growth` |
| `hardcode` | 1 | `live_scene_ids_consumed_not_hardcoded` |
| `oldhistoryonly` | 1 | `complete_declared_history_through_3h` |
| `visibleonly` | 1 | `reuse_valid_depth_scene_selector` |
| `crossobject` | 1 | `persistent_scene_objects_read_only` |
| `execute_deferred` | 1 | `post_3h_parent_snapshot_no_deferred_action` |
| `scheduler` | 1 | `no_truth_scheduler_or_discovery` |
| `truth` | 1 | `no_truth_scheduler_or_discovery` |
| `threshold` | 1 | `selection_and_status_are_descriptive` |

The **exit-2 escape branch was verified live**. **No regression**: **30/30**
prior suites green and **208/208** prior negatives still firing, **none
weakened**. The **Cyclopean-1f caveat stands and 1f was not edited**.

### Structural failures and the one code fix

**Structural failures: none.**

**One narrowly necessary code fix, in a new FullScene-1a file only.**
`tools/fullscene1a_run.py` read `retained_existing_object_states` from the
MultiObject-3a **manifest**, where that key does not exist — MultiObject-3a
records it inside its **selection report**, which is where its own comparator
reads it, the manifest carrying only the pointer. The lookup therefore resolved
to `{}` and **object 142 silently carried no prior epistemic status**, even
though its dedicated MultiObject-2d audit is reachable in the ancestry and its
geometry is unchanged at 310,884 points. This is the same class of defect as the
MultiObject-1a lookup corrected earlier in this programme.

The fix reads the report first and keeps the manifest as a fallback, so either
layout resolves (+8/−1 lines). **Corrected, not weakened**, and verified so:

- all nine negatives still exit 1 and the positive checker still reports
  `passed=9 failed=0`;
- the fix adds **only** the label the 3a report actually contains — `{'142':
  'ATTENTION_INCOMPLETE_RETAIN_FOR_REVISIT'}` — so object 141 and object 145
  remain correctly without a prior label;
- **the selection is completely unaffected**: 144 on 2,436 samples, identically,
  before and after.

The incomplete first record was deleted and the snapshot re-run once into the
same path rather than creating a duplicate; `previews/` is gitignored, so no
committed artifact was affected, and **exactly one FullScene-1a record exists**,
preserving the one-record-per-schema manifest scan later increments depend on.
No frozen prior source was modified.

### What this establishes, and what it does not

Established — this is the answer to the question asked.

**What the observer knows exists.** Across 64 saved observations spanning global
steps 18..81, **five** positive instance ids have been seen — **141, 142, 143,
144, 145** — and **all five** have at some point carried valid stereo depth.

**What has already become a persistent object.** **Four**: 141 (155,684 points,
37,654 footprint cells), 142 (310,884 / 62,784), 143 (42,988 / 17,947) and 145
(6,762 / 2,125). Two carry still-current audit labels, both
`ATTENTION_INCOMPLETE_RETAIN_FOR_REVISIT` — 142 from MultiObject-2d and 143 from
MultiObject-1c. Object 145's state is reported as *current* rather than
historical: `LOCAL_EXPLORATION_CONTINUES` with the latest measurement
`VALID_NEGATIVE_EVIDENCE` and one **unexecuted** deferred gaze. Object 141 is
carried without a status claim.

**Who is next.** **Object 144**, the single uninstantiated observed id, selected
deterministically by the unchanged rule on **2,436** accumulated valid-depth
samples from five historical looks (steps 21, 22, 47, 48, 49). It is the **only**
candidate, so the selection is forced rather than contested.

Not established. **This is an inventory, not an assessment.** **No accuracy
claim** — evaluator truth stayed closed, so every point count, footprint and
support figure describes the representation, not the scene. **No completeness
claim for any object** — the two retained labels are prior audits carried
forward, 141 carries none, 145's prior audit is stale by construction, and **no
completeness score was synthesized**. **No claim that 144 is well-measurable** —
its valid fraction is **3.68%**, lower than object 145's at selection time and
far below object 142's, so this selection may again pick a difficult target;
support measures how much the observer happened to measure, confounded with
fixations aimed at other objects. **No claim the scene contains only five
objects** — the declared scope begins at step 18 and excludes the object-141
Reality/Cyclopean lineage, and no discovery mechanism ran. **No trend claim from
144's unchanged support** — that the last 16 looks added nothing for it is a
measurement of where attention went, not evidence about 144 itself. And **nothing
was seeded, scheduled or executed**: the deferred gaze stands, and FullScene-1a
instantiates no object.

**Next: FullScene-1b — one prescribed seed fixation for object 144.**
