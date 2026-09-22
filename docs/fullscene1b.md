# FullScene-1b — seed the S0-selected next object

## Motivation

FullScene-1a established the formal first-tour initial condition `S0`: four persistent scene objects, one remaining observed-but-uninstantiated object, and one deterministic next-object decision under the already-established valid-depth scene-memory rule.

FullScene-1b turns that scene-level decision into exactly one physical action: **one prescribed fixation that instantiates the selected object as a separate seed entity**.

This is the first action of the full-scene field test. It is intentionally not a scheduler and not a growth experiment.

## Parent selection

Consume the selected object id and instantiated-object set from the completed FullScene-1a S0 record. Do not declare either in FullScene-1b source.

The currently measured S0 result has one sole candidate, object 144 with 2,436 accumulated valid-depth samples. That is an observed parent result, not a hard-coded contract: the implementation must consume whatever valid FullScene-1a parent it is given.

The deferred local action belonging to the prior active object remains **unexecuted**. FullScene-1b follows the scene executive's S0 selection instead.

## Evidence and prescribed gaze

Reconstruct exactly the same saved observation scope declared by FullScene-1a, through the final MultiObject-3h observation. Do not rerender history and do not broaden backward into older object-141 acquisitions.

For the S0-selected object:

1. collect only saved samples having valid stereo depth and the selected instance id;
2. reuse `multiobject3b_seed.select_seed_from_saved_evidence` unchanged;
3. therefore reuse the established occupied-cell spherical-mean rule on the inherited 0.1-degree grid;
4. require the evidence count to reproduce FullScene-1a's selected valid-depth support exactly.

The historical valid-depth fraction is diagnostic only. No low-texture or measurability gate is introduced.

## One acquisition

Add exactly one fixation at

```text
max(S0 observation steps) + 1
```

through `tools/scene_render_fix.py` with the same fixed-head scene/render contract.

No saved fixation is rerendered.

## Scene representation

Every S0 object remains a separate read-only `SURFEL_MAP`. The newly selected object is appended as one separate `SEED_SURFEL_PATCH`.

The shared cyclopean chart and raw footprint overlaps are measurements only. Zero overlap is not required.

## Scope

No local growth, fusion into an existing object, epistemic handoff, revisit, semantic ranking, object discovery, quality threshold, productivity gate, or automatic scene scheduler is introduced.

Evaluator truth remains closed.

## Next stage

If the seed record is structurally clean, FullScene-1c grows the newly seeded scene-selected object with the frozen local machinery while all pre-existing objects remain stable.

## Results

Run 2026-09-22 on the workstation, on branch **`fullscene-calibration-1`**.
`FULLSCENE1B_COMPLETE`, `structural_fails: []`, no FAIL line anywhere; the
comparator agrees and exits 0.

**The first physical action of the FullScene-1 field test succeeded.** The S0
decision — **object 144**, consumed from the parent and never declared here —
became one prescribed fixation at **global step 82**, gaze **(−19.520574,
−2.005759)**, instantiating a **3,057-point `SEED_SURFEL_PATCH` pure in `{144}`**.
All four pre-existing objects stayed **byte-identical**, and all **ten** pairwise
footprint overlaps plus the all-object overlap are **0**.

The historical low-measurability concern was **not** borne out at the seed: S0's
evidence gave 144 a valid fraction of **3.68%**, but the prescribed view returned
**6.46%** — comparable to object 145's seed (6.68%) and to a normal look for this
scene. **This is reported as measured; no gate was applied either way.**

The prior object's deferred local action **remains unexecuted**.

### Branch and provenance

Branch **`fullscene-calibration-1`**, clean throughout. Prospective package
commit **`004d93c`** adds **exactly the six FullScene-1b files, all `A`**; its
parent is the FullScene-1a result **`206ac58`**. `main` and `origin/main` remain
at **`15eedee`**, the frozen MultiObject-3h lineage — untouched.

**Apply note.** `FULLSCENE1B_APPLY.md`, `_CHECKS.md`, `_CODE_PROMPT.md` and
`_HANDOFF.md` are companion files outside the repository and were correctly not
looked for in it; the repository check documentation is
`docs/fullscene1b-checks.md`, which is what was run.

Frozen audit at full scope: **every tracked non-documentation source present at
`206ac58` — 320 files** across `tools/`, `tools/dev/` and `scenes/`. The diff
over that set is **empty (0 lines)** both before and after execution. Machinery
reused unchanged: `multiobject3b_seed.py` `86c3b4fdccbbceab…`,
`multiobject1a_seed.py` `a5ad5ea0055c3974…`, `scene_render_fix.py`
`6e70bbb78c1043ec…`, `reality2_render_fix.py` `9f1433d189fbcbb5…` (present,
unchanged, **never invoked**), `fullscene1a_run.py` `efc595950d894cc0…`.

### Parent S0 and the pre-render invariants

Parent located **by manifest**, not by a guessed path: exactly one
`FullScene1a-scene-state-snapshot-v1` record — `previews/fullscene1a/full-seed2111`.
**Every required invariant holds**, reported as what the parent actually
contains:

| invariant | value |
|---|---|
| `truth_opened == false` | **false** |
| `snapshot_id == S0` | **S0** |
| `fullscene_initial_condition == true` | **true** |
| selection status | **`NEXT_OBJECT_SELECTED`** |
| selected id positive | **144** |
| selected id not already instantiated | instantiated `[141, 142, 143, 145]` |
| support agrees, manifest vs snapshot | **2,436 = 2,436** |
| deferred prior-object action unexecuted | **false** |
| no scheduler in parent | `automatic_scene_scheduler` / `revisit_scheduler_used` **false** |
| no quality gate in parent | **false** |
| `structural_fails` | **[]** |

The **live scene graph ids `[141, 142, 143, 145]` equal the parent's instantiated
set** exactly. The declared S0 scope is **64 observations, steps 18..81**, and
all **64** calibration/observation pairs were located.

### Independently reproduced seed decision — before rendering

Rebuilt the declared S0 scope from scratch and reimplemented the documented
occupied-cell spherical-mean rule independently, then compared against the
production path (`multiobject3b_seed.select_seed_from_saved_evidence`):

| quantity | independent | production | agreement |
|---|---|---|---|
| valid-depth evidence points | **2,436** | 2,436 | **match** |
| contributing steps | 21 (1,410), 22 (252), 47 (107), 48 (340), 49 (327) | same | **match** |
| occupied 0.1-degree cells | **987** | 987 | **match** |
| spherical mean of occupied cells | (−19.333766896635, −1.798502446227) | same | **0.000e+00 deg** |
| chosen cell `[yaw_i, pitch_i]` | **[−195, −20]** | [−195, −20] | **match** |
| cell dot to mean | 0.9999881483226 | 0.9999881483226116 | **match** |
| **prescribed gaze** | **(−19.520574420428, −2.005758596173)** | same | **0.000e+00 deg** |

The evidence count reproduces FullScene-1a's `selected_valid_depth_samples`
**2,436** exactly, and the runner's own guard enforces that equality before
rendering. **Raw visibility was not used to choose the seed** — it is recorded
only as a diagnostic (66,237 visible against 2,436 valid, **3.68%**), and the
`visibleonly` negative exists to enforce that.

### One acquisition

Exactly **one** Blender launch and **one** new acquisition directory entry:
**`fix_82`** = max(S0 steps 18..81) + 1, through the generic
`tools/scene_render_fix.py`. `added_fixations` **1**,
`parent_fixations_rerendered` **0**; **no historical step was rerendered**, and
all **128** pinned history files are byte-identical afterwards. The legacy
Reality-2 capped renderer was never used.

| quantity | value |
|---|---|
| global step | **82** |
| gaze | **(−19.520574, −2.005759)** |
| object-144 visible pixels | **47,332** (72.2% of frame) |
| object-144 valid-depth points | **3,057** |
| **depth recovery fraction** | **6.46%** |
| whole-frame valid | 3,818 of 65,536 (**5.8%**) |
| valid points by positive instance id in the seed view | **144: 3,057; 143: 761** |

### Seed patch and scene integrity

`object_144_seed_patch.npz` — **3,057 points**, **3,057 finite xyz** (all of
them), `instance_id` exactly **{144}**, `selected_object_patch_pure` **true**.
Range **2.5146 / 2.6458 / 2.8056 m** — a spread of only **0.29 m**, consistent
with a flat surface seen close to frontally, and the nearest object in the scene.

**All 135 pinned inputs byte-identical afterwards** — the 2 FullScene-1a
artifacts, the parent live scene graph, all 4 persistent object geometry sources,
and all **128** S0 evidence files.

| object | sha256 before | after | same |
|---|---|---|---|
| 141 | `6ac98f6251b47337…` | `6ac98f6251b47337…` | **yes** |
| 142 | `6f90d985f8078a7d…` | `6f90d985f8078a7d…` | **yes** |
| 143 | `bbc4b856a07d2be5…` | `bbc4b856a07d2be5…` | **yes** |
| 145 | `ac46e7fc815d103c…` | `ac46e7fc815d103c…` | **yes** |

Flags: `truth_opened` **false**, `fusion_iterations_added` **0**,
`growth_iterations_added` **0**, `new_object_instantiated` **true**,
`existing_objects_read_only` **true**,
**`deferred_prior_object_action_executed` false**, `quality_gate_used` **false**,
`automatic_scene_scheduler` / `revisit_scheduler_used` /
`automatic_object_discovery` / `semantic_ranking_used` all **false**,
`renderer_entrypoint` `tools/scene_render_fix.py`.

### Five-object scene and footprints — diagnostics only

`object_ids_after` **[141, 142, 143, 145, 144]**. Shared chart **624 × 488** at
0.1 deg.

| object | geometry | points | footprint cells | area |
|---|---|---|---|---|
| 141 | `SURFEL_MAP` (read-only) | 155,684 | 37,654 | 376.54 deg² |
| 142 | `SURFEL_MAP` (read-only) | 310,884 | 62,784 | 627.84 deg² |
| 143 | `SURFEL_MAP` (read-only) | 42,988 | 17,947 | 179.47 deg² |
| 145 | `SURFEL_MAP` (read-only) | 6,762 | 2,125 | 21.25 deg² |
| **144** | **`SEED_SURFEL_PATCH`** | **3,057** | **1,098** | **10.98 deg²** |

**All ten pairwise overlaps and the all-object overlap are 0.** Recorded as what
this configuration produced; **zero overlap is not required** by the contract.

Object 144 is the **smallest footprint in the scene** at 10.98 deg², from a seed
that is nonetheless larger than object 145's was (3,057 against 3,662 points, on
a similar single look).

### Visual reading, descriptive

`object_144_seed_rgb.png`: the fovea is dominated by a large flat **blue-grey
panel** with a **pale cream rectangle inset** in the upper middle and a grey band
down the left edge. The surface is largely untextured — consistent with 6.46%
recovery — with the inset rectangle's borders supplying the edges a stereo
matcher can use. The 761 valid points attributed to object 143 in this view come
from that left-hand band; they were **not** fused, since only points carrying the
selected id enter the seed patch.

### Checks

`py_compile` clean on all four modules. The four prescribed lines appeared
verbatim:

```text
[fullscene1b-seed] PASS parent_s0=true selected_from_parent=true one_fixation=true
[fullscene1b-history] PASS full_s0_history=true valid_depth_seed=true no_rerender=true
[fullscene1b-progress] PASS existing_read_only=true deferred_action=false growth=false scheduler=false
[fullscene1b-check] SUMMARY passed=8 failed=0
```

All **ten** negatives are genuine source-mutation controls, each exiting **1**
with a named detector. **None exited 0 or 2.**

| negative | rc | detected by |
|---|---|---|
| `handpick` | 1 | `s0_selection_consumed_not_handpicked` |
| `oldhistoryonly` | 1 | `complete_s0_history_reused` |
| `visibleonly` | 1 | `valid_depth_occupied_cell_seed_rule_reused` |
| `multiprobe` | 1 | `one_fresh_fixation_generic_renderer` |
| `legacyrenderer` | 1 | `one_fresh_fixation_generic_renderer` |
| `crossfuse` | 1 | `persistent_objects_read_only_separate_seed` |
| `execute_deferred` | 1 | `deferred_prior_action_stays_deferred` |
| `grow` | 1 | `growth_handoff_scheduler_deferred` |
| `scheduler` | 1 | `growth_handoff_scheduler_deferred` |
| `truth` | 1 | `no_truth_quality_or_new_threshold` |

The **exit-2 escape branch was verified live** with an inert scratch mutation.
**No regression**: **31/31** prior suites green and **217/217** prior negatives
still firing, **none weakened**. The **Cyclopean-1f caveat stands and 1f was not
edited**.

### Environment and wall time

Blender 5.2.1 LTS headless, Cycles, **OPTIX** on an RTX 4090 (driver 595.84);
host `.venv/bin/python` 3.12.3. **27.3 s** — one Blender launch plus the 64-look
S0 evidence replay.

### Structural failures and the one code fix

**Structural failures: none.**

**One narrowly necessary code fix, inside a new FullScene-1b file only.** The
first execution attempt aborted before any render with
`KeyError: 'xyz_h'` raised from the **frozen**
`multiobject3b_seed.collect_selected_object_evidence`.

Diagnosis: FullScene-1b reuses `fullscene1a_run._history` to rebuild the declared
S0 scope. That builder deliberately projects every observation down to `step`,
`instance_id` and `valid` — which was exactly right for FullScene-1a, whose
snapshot only ever counted ids and valid masks and never needed geometry. The
frozen seed rule additionally requires the reconstructed `xyz_h`, so the reused
observations were missing the one field the seed needs.

**The frozen source is not broken** — the readers it draws on
(`multiobject1c_audit`, `multiobject2d_audit`, `multiobject3d_audit`) all return
`xyz_h`, and my independent reproduction using them succeeded. The defect is in
the new FullScene-1b runner's reuse of a deliberately narrower builder.

The fix, in `tools/fullscene1b_run.py` only (+16/−0 lines): after
`fs1a_run._history(...)` returns, re-read **exactly the same declared cases**
through the unchanged stereo front end and attach `xyz_h`, asserting that the
re-read `instance_id` and `valid` arrays are **bitwise equal** to what
FullScene-1a produced before accepting the geometry. **The scope is not widened**
— the cases, their order and their count are the ones `_history` already returned
and validated against the parent's `observation_steps` and `observation_count`.

**Corrected, not weakened**, and verified so: all ten negatives still exit 1, the
checker still reports `passed=8 failed=0`, and the two call sites the checks
assert verbatim — `fs1a_run._history(parent3h, m3h, chain)` and
`select_seed_from_saved_evidence(observations, selected_id, public.GRID_DEG)` —
are untouched. **No frozen pre-FS1b source was modified**; the frozen-set diff
against `206ac58` is **0 lines** after the fix. The seed the fix enables
reproduces the independent calculation to **0.000e+00 deg**.

### What this establishes, and what it does not

Established. **The scene executive's S0 decision became a physical scene entity
in one action.** The object id and the instantiated set were **consumed from the
parent** — neither is declared in FullScene-1b source, and the `handpick`
negative enforces that. The prescribed gaze was derived by the **unchanged**
occupied-cell spherical-mean rule from **valid-depth evidence only**, reproduced
**independently to 0.000e+00 deg**, and its evidence count reproduced
FullScene-1a's support **exactly**. **Exactly one** new globally numbered
fixation at step 82 through the **generic renderer**, with **zero** historical
rerenders, produced a **3,057-point patch pure in `{144}`** with all xyz finite
and a 0.29 m range spread. All four pre-existing objects stayed **byte-identical**
and read-only, all **135** pinned inputs unchanged, the deferred prior-object
action **unexecuted**, and the five footprints **mutually disjoint**. The scene
now holds **five** entities.

Established as a diagnostic, and it cuts against the prior expectation.
**Object 144's seed view measured better than its history predicted** — **6.46%**
recovery against the **3.68%** valid fraction its S0 evidence carried, and a seed
of 3,057 points from a single look. That is a normal seed for this scene, not a
weak one. **It gated nothing**, and a single look is not a measurability claim.

Not established. **This is a seed, not an object** — 3,057 points from one
fixation; whether 144 grows, stalls, or terminates is **untested**, and no growth
loop ran. **No accuracy claim** — evaluator truth stayed closed, so every count
describes the representation, not the scene. **No object completeness** and **no
measurability claim** — one look cannot establish either, and 144's historical
3.68% remains the only multi-look figure available for it. **Zero overlap is
still not an invariant** — it now survives five objects in this configuration and
nothing more. **Nothing about the prior object** — 145's deferred action stands
unexecuted and its state is unchanged. And **no scheduler, discovery, revisit,
semantic ranking, threshold or handoff** was introduced.

**Next stage, structurally warranted: FullScene-1c — grow the newly seeded object
144 with the frozen local machinery while all pre-existing objects remain
stable.**
