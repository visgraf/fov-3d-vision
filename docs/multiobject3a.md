# MultiObject-3a — next-object selection from updated scene memory

## Motivation

The scene now contains three persistent foreground entities.  MultiObject-2d
showed that the third object remains attention-incomplete, but scene progress is
explicitly unblocked.  The next move should therefore be a new scene-level
selection, not another forced completion attempt.

MultiObject-3a repeats the deliberately simple MultiObject-2a decision rule on a
larger memory: all saved observations from the earlier two-object stage plus the
third object's seed and growth history.

## Question

> Given everything the fixed-head observer has already seen, which observed but
> uninstantiated object currently has the largest accumulated usable depth evidence?

## Method

1. Consume the current instantiated object-id set from the completed scene graph;
   do not hard-code object ids in this increment.
2. Reuse the saved old scene history and the saved third-object seed/growth
   history.  No view is rerendered.
3. For every positive instance id that is **not already instantiated**, sum
   `valid & (instance_id == id)` over the complete saved history.
4. Record raw visibility only as a diagnostic.
5. Select the candidate with maximum accumulated valid-depth support; exact ties
   use the smaller integer id.
6. Stop.  The selected object's seed fixation belongs to the next increment.

No threshold, semantic ranking, saliency score, revisit priority or learned
scheduler is introduced.

## Why this is a new step

The rule is unchanged, but the memory is not.  The third object's 24-look
history may expose new objects or greatly change the evidence for candidates
already seen earlier.  This asks whether persistent scene memory can repeatedly
support the sequence

```text
explore current object -> retain unfinished state -> select another object
```

without requiring any existing object to be declared geometrically complete.

## Deliberately deferred

- the selected fourth object's seed fixation;
- growth of that object;
- revisit scheduling for objects retained as incomplete;
- semantic importance/saliency;
- layered occlusion handling;
- evaluator truth or accuracy claims.

## Expected outputs

- `next_object_selection.json` — instantiated ids, candidate table and selected id;
- `prediction_manifest.json` — read-only provenance, complete observation scope and next stage.

## Results

Run 2026-09-22 on the workstation, **host-side only**. `MULTIOBJECT3A_COMPLETE`,
`structural_fails: []`, no FAIL line anywhere; the comparator agrees and exits 0.

**Object 145 is the next object**, on **13,047** accumulated valid-depth samples
against runner-up 144's **2,436** — a margin of **10,611 samples, 5.36x**. The
decision was recomputed independently from the raw observations and matches
exactly. **No seed fixation was taken; the run stops at the selection.**

The honest headline for *why this is a new step*: the larger memory **did not
change the answer**. It exposed **no new object**, and object 145 was already the
argmax on the old history alone.

### Provenance

Working tree clean at the start. Package commit **`69c1a49`** adds **exactly the
seven MultiObject-3a files, all `A`**; parent result **`a2d8b5e`**.

Frozen audit at full scope, not a curated subset: **every tracked
non-documentation source present at `a2d8b5e` — 277 files** across `tools/`,
`tools/dev/` and `scenes/`. `git diff a2d8b5e HEAD` over that set is **empty
(0 lines)** and all **277 sha256 are SAME**. The complete changed-file list
between parent result and HEAD is the seven new 3a files and nothing else.
Key frozen sources: `fsg6f_frontier.py` `d636c9405d719916…`,
`scene_render_fix.py` `6e70bbb78c1043ec…`, `reality2_render_fix.py`
`9f1433d189fbcbb5…`, `fsg3_surface_map.py` `1b9dbeb873105ec9…`,
`cyclopean1a_topology.py` `6ed00fca00907f33…`, `multiobject2a_select.py`
`d53cc6db6397eec9…`, `multiobject2d_audit.py` `c653b63c80bcb745…`,
`fsg_stereo_supported.py` `683ae91eaca7b6af…`.

The parent was located **by manifest**, not by assumed path: exactly one
`MultiObject2d-selected-object-epistemic-audit-v1` record —
`previews/multiobject2d/full-seed2111` — with every required invariant satisfied:
`scene_disposition` **`MOVE_TO_NEXT_OBJECT`**, `truth_opened` **false**,
`acquisitions_added` **0**, `growth_iterations_added` **0**,
`scene_objects_read_only` and `selected_object_read_only` **true**,
`structural_fails` **[]**, `object_status`
`ATTENTION_INCOMPLETE_RETAIN_FOR_REVISIT`.

The history chain was walked by manifest at every hop, never guessed:
2d -> 2c (`previews/multiobject2c/full-seed2111`, object 142, steps 42..65)
-> 2b (`previews/multiobject2b/full-seed2111`)
-> 1b2-r2 (`previews/multiobject1b2-r2/full-seed2111`, the old scene history).

### Environment and wall time

Host `.venv/bin/python` 3.12.3. **No Blender, no Cycles, no GPU.** `pgrep blender`
returned **0 before and after**. The selection took **7.2 s**, replaying 48 saved
looks through the frozen stereo front end. The output record contains **no
acquisition directory**.

### Checks

`py_compile` clean on all five modules. Selector self-test:

```text
[multiobject3a-select] PASS valid_depth_only=true deterministic_argmax=true no_threshold=true
```

Normal checker, three lines verbatim:

```text
[multiobject3a-selection] PASS read_only=true updated_history=true uninstantiated_only=true valid_depth_support=true
[multiobject3a-progress] PASS handpicked=false seed_deferred=true revisit_scheduler=false quality_gated=false
[multiobject3a-check] SUMMARY passed=6 failed=0
```

All **six** negatives are genuine source-mutation controls, each exiting **1**
because a real invariant was detected. **None exited 2 — there is no blocker.**

| negative | rc | detected by |
|---|---|---|
| `acquire` | 1 | `read_only_no_acquisition` |
| `hardcode` | 1 | `instantiated_ids_consumed_not_hardcoded` |
| `oldhistoryonly` | 1 | `updated_history_combined` |
| `visibleonly` | 1 | `valid_depth_support_only` |
| `threshold` | 1 | `deterministic_argmax_no_threshold` |
| `scheduler` | 1 | `progress_without_revisit_scheduler` |

The **exit-2 escape branch was verified live**: an inert mutation applied to a
scratch copy of the runner was detected by **no** check, which is exactly the
condition under which the checker prints `ERROR ... mutation escaped detection`
and exits 2.

One precise note on the `hardcode` control. Its mutation injects the literal
`selected_object_id = 145`, and 145 happens to be the id the rule actually
selects. **The control is structural, not outcome-based**: it asserts the string
is absent from the sources, so it detects hard-coding regardless of value. It
does not, and is not meant to, demonstrate that a hard-coded id would have
produced a different answer.

**No regression, and no previous negative was weakened**: **22/22** prior suites
green and **142/142** prior negatives still firing — multiobject2d, 2c 6/6 (7 neg
each), 2b, 2a, 1c, 1a 6/6 (6 neg each), 1b2 6/6 (7 neg), 1b 6/6 (6 neg),
cyclopean1g..1a 6/6 (6 neg each), reality2b 7/7 (10 neg), reality2 7/7 (7 neg),
reality1 6/6 (6 neg), fsg6f 14/14 (15 neg), fsg3 5/5 (4 neg), fsg_supported 46/46
(4 neg), fsg_hdr 34/34 (3 neg). The **Cyclopean-1f caveat stands as a standing
caveat and 1f was not edited**: its six negatives print and exit 1
unconditionally rather than injecting a mutation.

### Combined observation scope

**48 looks, global steps 18..65**, with **0 duplicate steps** and **globally
contiguous** — the runner's own guard asserts both.

| source | looks | steps |
|---|---|---|
| old scene history (MultiObject-1b2-r2) | 24 | 18..41 |
| third-object history (MultiObject-2b seed + 2c growth) | 24 | 42..65 |
| **combined** | **48** | **18..65** |

The old half is itself assembled by manifest: the MultiObject-1a seed at step 18,
six reused steps (18..23) from the MultiObject-1b partial record, and 18 new
steps (24..41) from 1b2-r2 itself.

**Scope boundary, stated precisely.** "Complete saved history" here means what the
contract's `evidence_scope` declares — the 1b2 scene history plus the 2b/2c
third-object history — which begins at the MultiObject-1a seed, **global step
18**. Views from the object-141 Cyclopean/Reality lineage are **not** included;
exactly one such acquisition, `fix_17`, is reachable in the ancestry (in the
Cyclopean-1g record). That is the declared scope, not an omission by this run,
but it does bound what the counts below mean.

### Instantiated ids, consumed from scene memory

`instantiated_object_ids` **[141, 142, 143]**, read at
[multiobject3a_run.py:106](tools/multiobject3a_run.py#L106) as
`tuple(sorted(objects))` where `objects` comes from the **current MultiObject-2c
`scene_graph.json`**, reached through the 2d parent. The runner additionally
asserts `len(objects) >= 3` and that the 2c selected id is present in the graph.
**No scene id is declared in any 3a source**; the `hardcode` negative enforces
that and fires.

Across all 48 looks the only positive instance ids present anywhere are **141,
142, 143, 144, 145**. Three are instantiated, so the candidate set is exactly
**{144, 145}**.

### Candidate table

Valid-depth support decides; visibility is a diagnostic only.

| id | valid-depth support | visible samples | valid fraction | steps with depth | steps visible |
|---|---|---|---|---|---|
| **145** | **13,047** | 183,164 | 7.1% | **8** | 9 |
| 144 | 2,436 | 66,237 | 3.7% | 5 | 5 |

Contributing steps:

- **145** — valid depth at **34, 35, 36, 37, 38, 58, 59, 60**; visible also at 41
  (seen, no usable depth). Largest per-step contributions: step 36 **3,726**,
  step 37 **3,118**, step 35 **2,049**, step 38 **1,441**, step 59 **1,228**,
  step 60 **1,038**.
- **144** — valid depth at **21, 22, 47, 48, 49**, visible at the same five.
  Largest: step 21 **1,410**, step 48 **340**, step 49 **327**, step 22 **252**,
  step 47 **107**.

Both candidates have a **low valid fraction** (7.1% and 3.7%): they are seen far
more often than they are measured. **Recorded as a diagnostic; it gated nothing**
— no minimum support, no visibility ratio and no threshold of any kind enters
the rule.

### Selection

`selection_status` **`NEXT_OBJECT_SELECTED`**, `selected_object_id` **145**,
`selected_valid_depth_samples` **13,047**, `tie_break`
`largest_valid_depth_support_then_smaller_object_id` (not exercised — no tie).

**Margin over runner-up 144: 10,611 samples, 5.36x.** The ordering is
unambiguous; no tie-break was needed and none of the supporting numbers is near a
boundary, because there is no boundary.

### Independent recomputation

The selection was recomputed **without using the package's selector or its
case-resolution helpers**: acquisition paths were rebuilt by hand from the
manifest keys (`reused_global_steps`, `new_global_steps`, `partial_record`,
`global_step_seed`, `last_global_step`), the instantiated set was re-read
directly from `scene_graph.json`, and the aggregation
`valid & (instance_id == id)` was written fresh.

| check | result |
|---|---|
| resolved 48 cases, steps 18..65 | matches |
| instantiated ids {141,142,143} | matches |
| selected id 145 | **matches** |
| selected support 13,047 | **matches** |
| candidate ordering [145, 144] | **matches** |
| full table, valid **and** visible counts | **matches** |

**All four comparisons match exactly.**

**Counterfactual split, measured.** Object 145 wins on **either half of the
memory alone**:

| evidence | 145 | 144 | argmax | margin |
|---|---|---|---|---|
| old scene history only (18..41) | 10,667 | 1,662 | **145** | 6.42x |
| third-object history only (42..65) | 2,380 | 774 | **145** | 3.07x |
| combined (18..65) | **13,047** | 2,436 | **145** | 5.36x |

So the updated memory **reinforced rather than changed** the decision. The new
24 looks contributed **18.2%** of 145's support and **31.8%** of 144's, which
**narrowed** the margin from 6.42x to 5.36x without reordering anything. **The
contract's stated hope — that the third object's history "may expose new objects
or greatly change the evidence" — did not materialise here, and is reported as
measured rather than as anticipated.**

### Read-only integrity

**All 105 pinned inputs byte-identical afterwards** — 3 MultiObject-2d files, 3
MultiObject-2c files, 3 scene-object geometry sources, and **all 96 saved
calibration/observation files** (48 looks x 2). The runner's own four guards
assert the same and all four passed.

Object geometry unchanged and pure:

| object | sha256 | points | ids |
|---|---|---|---|
| 141 | `6ac98f6251b47337…` | 155,684 | `{141}` |
| 142 | `6f90d985f8078a7d…` | 310,884 | `{142}` |
| 143 | `bbc4b856a07d2be5…` | 42,988 | `{143}` |

Manifest flags: `truth_opened` false, `acquisitions_added` 0,
`fusion_iterations_added` 0, `growth_iterations_added` 0,
`new_object_instantiated` **false**, `scene_objects_read_only` true,
`semantic_ranking_used` false, `quality_gate_used` false,
`revisit_scheduler_used` false, `automatic_candidate_selection` true,
`structural_fails` **[]**. `retained_existing_object_states` records object 142
as `ATTENTION_INCOMPLETE_RETAIN_FOR_REVISIT` — **carried forward as a fact, and
it did not block the selection.**

`tools/multiobject3a_compare.py` on the completed record printed
**`MULTIOBJECT3A_COMPLETE`** with `"structural_fails": []` and exited **0**,
independently re-deriving the argmax from the candidate table and confirming the
selected id is not already instantiated.

### Structural failures and code fixes

**Structural failures: none.** No FAIL line was produced anywhere.

**Code fixes: none.** No MultiObject-3a file needed repair and no frozen prior
source was modified. The package ran as applied, first time.

The inherited NaN->int64 cast `RuntimeWarning` from
[cyclopean1a_topology.py:117-118](tools/cyclopean1a_topology.py#L117-L118)
appears in the console during observation replay, as in every increment since
Cyclopean-1a; it is raised where `_indices` then discards those lanes through an
explicit `np.isfinite` term, was re-proved harmless by measurement in
MultiObject-2d, and **the parent was not edited**.

### What this establishes, and what it does not

Established. **The scene-level loop closes.** Persistent scene memory supported
`explore current object -> retain it as unfinished -> select another object`
**without any object being declared geometrically complete**: object 142 carried
`ATTENTION_INCOMPLETE_RETAIN_FOR_REVISIT` into this step and the selection
proceeded anyway. The decision was **one deterministic scene-level choice** taken
from memory with **no new view, no seed, no fusion, no growth, no threshold and
no scheduler** — and **object 145 was selected on 13,047 valid-depth samples
against 2,436, a 5.36x margin**, reproduced **exactly** by an independent
recomputation that shared none of the package's aggregation or path-resolution
code. The instantiated set came from the live scene graph, the candidate set fell
out of it as exactly `{144, 145}`, and every one of the 105 pinned inputs was
byte-identical afterwards.

Established as a **negative** result, worth as much as the positive one. **The
larger memory did not change the answer.** Only five positive ids exist anywhere
in the 48 looks, so the third object's 24-look history **exposed no new object**;
and object 145 was already the argmax on the old history alone (10,667 vs 1,662).
The new looks **narrowed** the margin from 6.42x to 5.36x rather than reordering
anything. The rule's stability across a doubled memory is a real observation —
but it is stability, not discovery.

Not established. **No accuracy claim** — evaluator truth stayed closed; 13,047 is
a count of usable stereo samples in saved views, not evidence that object 145 is
well reconstructed, large, near, or important. **Not a saliency or importance
ranking** — accumulated valid-depth support measures *how much the observer
happened to measure*, which is confounded with how often each object fell inside
the fixations chosen for **other** objects: 145's support comes entirely from
steps 34-38 and 58-60, gazes aimed at objects 143 and 142. **Not a claim that 145
is measurable** — its valid fraction is **7.1%**, closer to object 143's
difficult regime (1.4-2.5%) than to object 142's (58.8-77.3%), so this selection
may well pick a hard target; MultiObject-2a's selection of 142 preceded a healthy
stereo regime, and **one prior case is not a pattern**. **Not exhaustive over the
programme's history** — the declared evidence scope begins at global step 18, so
the object-141 Cyclopean/Reality lineage is excluded by contract. **No revisit
schedule** — object 142 remains retained, and nothing here says when or whether it
is revisited. **No seed taken**: the fourth object's first fixation is deferred.

**Next: seed the selected object 145 with one prescribed fixation.** Stopped
after selection, as instructed.
