# MultiObject-2a — next-object selection from saved scene evidence

## Motivation

MultiObject-1c established a scene-progress principle: an object may remain partially measured or even slightly attention-incomplete without blocking exploration of the rest of the scene. Object 143 is therefore retained for possible revisit while the scene moves on.

The next new problem is no longer local surface growth. It is a scene-level question:

> Which object should receive attention next?

MultiObject-2a answers only that question. It is deliberately read-only and takes no new fixation.

## Candidate set

The current scene already contains oracle instance ids visible incidentally in saved observations that have not been instantiated as persistent foreground objects. MultiObject-2a forms candidates from:

1. the saved scene-history observations used by the MultiObject-1c ancestry;
2. positive integer instance ids with **valid stereo depth** in those observations;
3. excluding already-instantiated objects 141 and 143.

Visibility by itself is not selection support. A candidate receives support only where the existing stereo front end produced valid depth.

## Selection rule

For each uninstantiated candidate object id, sum its number of valid-depth samples over the saved observation history.

Select the object with the largest accumulated valid-depth support. If two candidates have exactly the same support, choose the smaller integer id.

There is:

- no minimum-support threshold;
- no semantic preference;
- no saliency model;
- no learned ranking;
- no hand-picked next id;
- no new scene scheduler beyond this one deterministic decision.

## Scope

This step does **not** seed the selected object. It does not render, fuse, grow, revisit or change either existing object.

Outputs:

- `next_object_selection.json` — candidate support table and deterministic selection;
- `prediction_manifest.json` — integrity/provenance and next-stage declaration.

The next stage is one prescribed seed fixation for the selected object.

## Interpretation

MultiObject-2a marks the first transition from object-local control to scene-level attention management. The decision is intentionally simple: use evidence already in memory and choose the uninstantiated object for which the current instrument already possesses the greatest valid geometric support.

## Results

Run 2026-09-22 on the workstation. **`MULTIOBJECT2A_COMPLETE`,
`structural_fails: []`.** Read-only: **no Blender process, no acquisition, no
fusion, no object instantiated**, and all 57 pinned inputs byte-identical
afterwards.

**Selected next object: id 142**, with **151,133** accumulated valid-depth
samples — the deterministic argmax over uninstantiated candidates, with no
threshold, no semantic ranking, no saliency model and no hand-picked id.

### Provenance

Working tree clean. Prospective commit **`16fadac`**; parent result **`fa65de8`**
(the restored MultiObject-1c documentation commit, a bookkeeping descendant of
`e5336fb`). The package adds **exactly seven files, all `A`**. `git diff` over
**67 frozen sources** — every FSG1/FSG3/FSG6f source, scene, rig, pin file, every
Reality Check 1/2/2b source, `scene_render_fix.py`, every Cyclopean-1a..1g source
and every MultiObject-1a/1b/1b2/1c source — is **empty (0 lines)** against both
`fa65de8` and `e5336fb`, all 67 sha256 SAME.

The parent was located **by manifest** and **all eight required conditions
hold**: schema `MultiObject1c-object143-epistemic-audit-v1`, seed 2111,
`truth_opened` false, `acquisitions_added` 0, `growth_iterations_added` 0,
`object_1_read_only` and `object_2_read_only` true,
`summary.scene_disposition = MOVE_TO_NEXT_OBJECT`, `structural_fails []`.
Exactly one record matched: `previews/multiobject1c/full-seed2111`.

### Read-only integrity

**57 inputs pinned before and re-hashed after — all byte-identical**:

| input | sha256 |
|---|---|
| 1c `prediction_manifest.json` | `3ad6c63e761f0411…` |
| 1c `object_143_epistemic_report.json` | `7d3c7a2a29fa1ac2…` |
| 1c `object_143_epistemic_shoreline.png` | `88b85071cb133a81…` |
| 1b2 `prediction_manifest.json` | `74d5cc0f58a2c590…` |
| 1b2 `scene_graph.json` | `5df35f372460399…` |
| 1b2 `object_143_surface_map.npz` | `bbc4b856a07d2be5…` |
| 1b2 `scene_cyclopean_footprints.npz` | `5ef4982532f8bde2…` |
| 1b2 `object_143_policy_trace.json` | `c17589df1aa18b4c…` |
| object-141 source | `6ac98f6251b47337…f71e524a` |
| all 24 calibration/observation pairs, global steps 18–41 | byte-identical |

No Blender process ran; no `subprocess`, `blender`, `bpy` or fusion call appears
in any MultiObject-2a source; the output contains **exactly two host artifacts**
— `next_object_selection.json` and `prediction_manifest.json` — with no
acquisition directory, `.exr`, `.ply`, `.npz` or render log. Manifest records
`acquisitions_added: 0`, `fusion_iterations_added: 0`,
`growth_iterations_added: 0`, `new_object_instantiated: false`,
`objects_141_143_read_only: true`, `truth_opened: false`,
`quality_gate_used: false`, `semantic_ranking_used: false`.

Objects unchanged: **141** still 155,684 points ids `{141}`; **143** still 42,988
points ids `{143}`.

### Environment and wall time

Host `.venv/bin/python` 3.12.3 only. **Interactive at 3.8 s.**

### Checks

`py_compile` clean on all five modules. The selector self-test and the three
prescribed structural lines appeared verbatim:

```text
[multiobject2a-select] PASS valid_depth_only=true deterministic_argmax=true no_threshold=true
[multiobject2a-selection] PASS read_only=true uninstantiated_only=true valid_depth_support=true deterministic_argmax=true
[multiobject2a-progress] PASS handpicked=false seed_deferred=true scheduler=false quality_gated=false
[multiobject2a-check] SUMMARY passed=6 failed=0
```

All six negatives are **genuine source-mutation controls**, each exiting **1**
with a distinct detector and **none exiting 2**:

| negative | rc | detected by |
|---|---|---|
| `acquire` | 1 | `read_only_no_acquisition` |
| `instantiated` | 1 | `uninstantiated_candidates_only` |
| `visibleonly` | 1 | `valid_depth_support_only` |
| `threshold` | 1 | `deterministic_argmax_no_threshold` |
| `handpick` | 1 | `selection_not_handpicked` |
| `grow` | 1 | `seed_deferred_no_scheduler` |

**No regression**: all 14 prior suites green and **98 prior negatives** still
firing — multiobject1c 6/6, multiobject1b2 7/7, multiobject1b 6/6,
multiobject1a 6/6, cyclopean1g/1f/1e/1d/1c/1b/1a 6/6 each, reality2b 7/7 (10/10),
reality1 6/6, fsg6f 14/14 (15/15).

### Scene history and candidate set

Evidence scope: the **24** saved scene-history observations at global steps
**18–41**, the same history MultiObject-1c audited. Already-instantiated ids
**{141, 143}** were excluded by the candidate rule.

**Three uninstantiated candidates carry valid-depth evidence**: **142, 145, 144**.

| object id | valid-depth samples | visible samples | depth recovered | steps with depth |
|---|---|---|---|---|
| **142** | **151,133** | 203,851 | **74.1%** | 5 — steps 18, 38, 39, 40, 41 |
| 145 | 10,667 | 144,994 | **7.4%** | 5 — steps 34, 35, 36, 37, 38 |
| 144 | 1,662 | 35,038 | **4.7%** | 2 — steps 21, 22 |
| **total** | **163,462** | 383,883 | | |

Visible-sample counts are recorded **as diagnostics only** and contribute nothing
to the ordering.

Per-step valid-depth support for the winner: step 18 **15,513**, step 38
**19,555**, step 39 **41,752**, step 40 **38,724**, step 41 **35,589** — total
**151,133** across 5 of the 24 observations.

### Selection

`selection_status = NEXT_OBJECT_SELECTED`, `selected_object_id = 142`,
`selected_valid_depth_samples = 151133`,
`tie_break = largest_valid_depth_support_then_smaller_object_id`.

**Verified independently of the tooling**: recomputing candidate support directly
from the 24 raw saved observations — re-running `compute_once` and counting
`(instance_id == oid) & valid` per id — reproduces **142 / 151,133** exactly, and
the recomputed ordering by `(−support, +id)` is **[142, 145, 144]**, matching the
record. **No tie occurred at the top**; the margin over the runner-up is
**140,466 samples, a factor of 14.2**, so the smaller-id tie-break was not
exercised.

`quality_gate_used: false`, `semantic_ranking_used: false`,
`new_object_instantiated: false`. The declared rules are recorded verbatim in the
manifest: candidates are *"positive integer instance ids present in saved
scene-history observations with valid stereo depth, excluding all
already-instantiated object ids"*, and the selection is *"sum valid-depth sample
support over the saved scene-history observations for each candidate; select the
largest accumulated support, breaking an exact tie by smaller integer object
id"*.

**Next stage**: `seed the selected next object with one prescribed fixation`. No
seeding, rendering, fusion, growth or revisit occurred in this step.

### What the valid-depth rule actually changed here

Worth recording precisely, because it is easy to over-claim. On this record,
ranking by **raw visibility** would have produced the **same winner**: by visible
samples the order is also 142 (203,851) > 145 (144,994) > 144 (35,038).

What the valid-depth rule changed is the **margin and the interpretation**. By
visibility, object 142 leads object 145 by only **1.4×**; by valid-depth support
it leads by **14.2×**. The rule correctly demotes object 145, which is nearly as
visible as 142 but yields depth on only **7.4%** of the pixels where it appears —
the same low-texture starvation documented for object 143, whose own looks
recovered 1.4–2.5%. Object 142, by contrast, recovers **74.1%**.

So: **the rule is vindicated in margin and in what it reveals, not in outcome, on
this particular record.** A record where a highly visible but unmeasurable object
outranked a well-measured one would separate the two rules by winner as well;
this one does not, and that is reported rather than glossed.

### Structural failures and code fixes

**No structural FAIL line**: `structural_fails: []` in both the selection report
and the comparator, `acquisitions_added: 0`, all 57 pinned inputs byte-identical,
objects 141 and 143 unchanged and pure, no evaluator truth opened.

**Code fixes: none.** No file was modified by this run.

### What this selection establishes, and what it does not

Established. **The scene can now make a next-object decision from memory alone.**
Using only evidence already saved in the 24-observation scene history, with no
new fixation and no change to either existing object, MultiObject-2a formed a
candidate set of three uninstantiated ids and selected **object 142** as the
deterministic argmax of accumulated valid-depth support, reproduced exactly by an
independent recomputation from the raw observations. The decision is **fully
determined by the declared rule**: no threshold, no semantic preference, no
saliency, no learned ranking, no hand-picked id, and no scheduler beyond this one
ordering. **Support is measured as valid depth, not visibility**, and the
difference is substantive — it separates a 74.1%-recoverable object from a
7.4%-recoverable one that is almost as visible.

Not established. **This is not a claim that object 142 is globally most
important or semantically salient.** It means only what the contract says: among
already-observed uninstantiated ids in the saved scene history, object 142
currently has the largest accumulated valid-depth support. **No accuracy claim** —
evaluator truth stayed closed, and the counts describe what the instrument
recorded, not the scene. **No threshold is implied**: 151,133 and 14.2× are
measurements, and nothing here says how much support an object needs to deserve
attention. **The candidate set is not the scene's object set** — it is only ids
that happened to appear *with valid depth* in the 24 saved observations, so an
object never looked at, or looked at and never measured, would not appear at all;
objects 144 and 145 are in the set precisely because they were incidentally
measured, and any other object in the room is not represented. **Nothing is
seeded**: object 142 has no map, no patch and no persistent entity, and whether a
prescribed seed fixation will actually yield useful surface is untested. And
**object 143 remains retained for revisit** under MultiObject-1c's disposition;
moving on is not abandoning it.
