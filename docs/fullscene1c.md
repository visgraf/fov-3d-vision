# FullScene-1c — grow the S0-selected object

## Question

Can the same frozen selected-object growth machinery grow the entity seeded by FullScene-1b while every pre-existing persistent scene object remains separate and byte-identical, and while the prior object's deferred local action remains unexecuted?

This is the first ordinary local-growth stage inside the `fullscene-calibration-1` field-test branch. FullScene-1a established scene state S0; FullScene-1b consumed its next-object decision and instantiated exactly one new seed entity with one prescribed fixation. FullScene-1c now asks only what the already-established local controller does with that seed.

The target object id is consumed from the completed FullScene-1b parent. It is not hard-coded in FullScene-1c.

## Occam choice: reuse the frozen local machinery

FullScene-1c introduces no new growth policy. It reuses:

- `tools/multiobject2c_policy.py` unchanged as the generic scene-id-to-FSG6f target-label adapter;
- frozen `tools/fsg6f_frontier.py` and all of its numerical rules;
- the frozen 12 mm FSG3/FSG6f association rule;
- the inherited 5 degree local saccade lattice;
- Reality-2b empty-look semantics;
- generic `tools/scene_render_fix.py` acquisition.

The adapter changes only the label namespace presented to the frozen controller. The actual object surfel map always retains the real scene instance id.

## Parent and scene integrity

The completed FullScene-1b record is the only parent. Its one seed acquisition is replayed from disk, not rerendered, and its saved seed patch must match the reconstructed seed exactly.

Every object that was already persistent before FullScene-1b remains read-only. Only pixels carrying the parent-selected scene id may enter the active surfel map. The prior object's deferred local action remains unexecuted.

## Local history scope

The local FSG6f history begins at the FullScene-1b seed observation only.

The older FullScene S0 observations used to select the object and position the seed are scene-memory evidence; they are **not** replayed as local FSG6f growth history. This preserves the already-established separation between scene-level memory and object-local control.

## Empty looks

The inherited minimum target-point count is unchanged. If a newly rendered fixation reconstructs fewer than 100 selected-object points, that fixation is valid negative evidence:

- record the binocular observation;
- fuse nothing;
- leave the selected-object map unchanged;
- append the observation to local history;
- ask the frozen controller what to do next.

An empty look is not a runtime failure and does not automatically stop the object.

## Stop and watchdog

Scientific stop is unchanged: the frozen FSG6f policy returns `stop/no_frontier`.

A 24 selected-object-fixation watchdog, including the FullScene-1b seed look, remains an engineering guardrail only. If it fires while FSG6f still says `continue`, the run is structurally complete but has **not** reached a scientific stop.

No epistemic handoff is allowed in this stage. If local growth ends with unresolved epistemic residue, that belongs to the subsequent audit stage rather than to FullScene-1c.

## Progress diagnostics — measured separately

This field test deliberately records several kinds of progress without collapsing them into one score:

- **attention / measurement:** visible selected-object pixels, valid selected-object depth points, recovery fraction, empty looks;
- **geometry:** matched and new surfels, map point count, footprint changes;
- **control:** policy trace, candidate/frontier state carried by the frozen controller, termination reason, scientific stop versus watchdog.

These are diagnostics only. In particular, FullScene-1c introduces no productivity score, no novelty threshold, no quality gate, and no changed stopping rule.

The FullScene-1b seed-view recovery measurement is therefore context, not a prediction or gate. Growth is allowed to reveal whether the object is dense, sparse, repetitive, measurement-poor, or quickly exhausted under the same frozen mechanism used before.

## Outputs

The run writes:

- the grown selected-object surfel map and PLY;
- a growth visualization;
- per-look RGB previews;
- saved local patches and intermediate maps;
- the complete local FSG6f policy trace;
- updated shared cyclopean footprints;
- an updated five-entity scene graph;
- a manifest containing the structural invariants, per-look stereo diagnostics, fusion matched/new counts, stop reason and integrity hashes.

No evaluator truth, automatic discovery, scene scheduler, revisit scheduler, semantic ranking, mesh/interpolation, handoff, productivity threshold or quality gate is introduced.

## Next

If FullScene-1c completes structurally, the next bounded step is **FullScene-1d**: read-only epistemic audit of the grown object before returning to the scene-level inventory.

An unfinished object still does not block the scene tour.

## Results

Run 2026-09-22 on the workstation, on branch **`fullscene-calibration-1`**.
`FULLSCENE1C_COMPLETE`, `structural_fails: []`, no FAIL line anywhere; the
comparator agrees and exits 0.

**The answer to the question asked is yes.** The frozen selected-object local
machinery grew the FullScene-1b seed — object **144**, consumed from the parent
— from **3,057 to 3,859** surfels over **7** object fixations, **pure `{144}` at
every saved map**, while **all four earlier persistent objects stayed
byte-identical** and the prior object's deferred local action **remained
unexecuted**.

Termination was **`no_frontier`** with `scientific_stop_reached` **true**, after
7 fixations against a 24-fixation watchdog that was **never approached**. The
three ledgers are kept separate below and point in different directions:
**control** stopped cleanly and early, **attention** covered a small angular
region, and **geometric** gain was modest (**1.262×**).

### A. Provenance and integrity

Branch **`fullscene-calibration-1`**, clean before and after. Prospective package
commit **`15ec8ff`** adds **exactly the six FullScene-1c files, all `A`**
(`docs/fullscene1c.md`, `docs/fullscene1c-checks.md`,
`tools/dev/check_fullscene1c.py`, `tools/fullscene1c_compare.py`,
`tools/fullscene1c_public.py`, `tools/fullscene1c_run.py`). Parent result
**`dd4df82`** (FullScene-1b).

Lineage: 5 commits ahead of `main`, **0 merges**, linear
`15eedee → a094e2f → 206ac58 → 004d93c → dd4df82 → 15ec8ff`.
`main` and `origin/main` remain at **`15eedee`**, the completed MultiObject-3h
developmental state — **untouched**.

**Apply note.** `FULLSCENE1C_APPLY.md`, `_CHECKS.md`, `_CODE_PROMPT.md` and
`_HANDOFF.md` are companion files outside the repository and were not looked for
inside it; the repository documentation is `docs/fullscene1c*.md`.

**Source freeze.** Every tracked non-documentation source present at `dd4df82` —
**324 files** — diffs to **0 lines** against HEAD, **both before and after
execution**, and `git status` is empty after the run. Required-reuse sources:

| source | sha256 |
|---|---|
| `multiobject2c_policy.py` | `f4d4a08b00981466…` |
| `fsg6f_frontier.py` | `d636c9405d719916…` |
| `fsg6f_public.py` | `c79f58c9b51f33d4…` |
| `fsg3_surface_map.py` | `1b9dbeb873105ec9…` |
| `scene_render_fix.py` | `6e70bbb78c1043ec…` |
| `reality2_render_fix.py` | `9f1433d189fbcbb5…` (unchanged, **never invoked**) |
| `fsg_stereo.py` / `fsg_stereo_supported.py` | `faebf0f1b3acbfde…` / `683ae91eaca7b6af…` |
| `fullscene1a_run.py` / `fullscene1b_run.py` | `efc595950d894cc0…` / `db987883731c4a47…` |

**Input freeze.** All **11 pinned inputs byte-identical afterwards** — the 5
FullScene-1b artifacts (manifest `275cbcbdf0f80f03…`, scene graph
`eca6c91944ea7d55…`, seed patch `c21806a940df5aa9…`, seed RGB, footprints), the
**2 seed-acquisition files** (`c4ab7eade895064f…`, `7a102cfd8cbf8099…`), and all
**4 pre-existing object geometry sources**.

**No code fix was required.** The package ran as applied, first time.

**Parent validation — all 16 gates hold.** Located by manifest scan: exactly one
`FullScene1b-seed-snapshot-selected-object-v1` record,
`previews/fullscene1b/full-seed2111`. Schema and public digest match; truth
closed; fixed head and static scene; **exactly one** seed fixation with **zero**
historical rerenders; **no** fusion, growth or handoff in 1b; new object
instantiated and seed patch pure; earlier objects read-only; deferred prior
action unexecuted; no scene or revisit scheduler; no quality gate;
`structural_fails []`.

**Checks.** `py_compile` clean on all four modules; the four prescribed lines
verbatim; `SUMMARY passed=9 failed=0`. **All twelve negatives exit 1** with a
named detector — `handpick`, `crossfuse`, `copypolicy`, `priorhistory`,
`legacyrenderer`, `globalwatchdog`, `emptyabort`, `execute_deferred`, `handoff`,
`productivitygate`, `scheduler`, `truth` — **none exited 0 or 2**, and the exit-2
escape branch was verified live with an inert scratch mutation. **No
regression**: **32/32** prior suites green, **227/227** prior negatives firing,
**none weakened**; the Cyclopean-1f caveat stands and 1f was not edited.

**Environment.** Blender 5.2.1 LTS headless, Cycles, **OPTIX** on an RTX 4090
(driver 595.84); host `.venv/bin/python` 3.12.3. **52.9 s**, 6 Blender launches.

### B. Parent seed and the first local decision

Consumed dynamically from the parent, never hand-picked:

| quantity | value |
|---|---|
| selected object id | **144** |
| pre-existing object ids | **[141, 142, 143, 145]** |
| seed global step | **82** |
| seed gaze | **(−19.520574, −2.005759)** |
| seed point count | **3,057** |
| seed recovery diagnostic | **6.46%** |

The saved seed acquisition was **reconstructed and verified against the saved
seed patch**, then used to initialize the active map. **It was not rerendered** —
`fix_82` does not appear in this record and `parent_fixations_rerendered` is 0.

**First FSG6f decision from the seed**: `stop` **false**, `reason` **`continue`**,
**7** candidates before consensus (0 rejected), next gaze **(−14.520574,
−7.005759)**, frontier **419** with **394 open**.

### C. Attention / measurement ledger

Diagnostics only. No stopping rule, ranking or gate depends on any of these.

| g.step | obj # | src | gaze (yaw, pitch) | target visible | valid depth | recovery | frame valid | empty |
|---|---|---|---|---|---|---|---|---|
| 82 | 0 | seed | (−19.521, −2.006) | 47,332 | 3,057 | 6.46% | 5.8% | false |
| 83 | 1 | grow | (−14.521, −7.006) | 16,464 | 1,008 | 6.12% | 32.8% | false |
| 84 | 2 | grow | (−14.521, −2.006) | 31,516 | 1,905 | 6.04% | 16.1% | false |
| 85 | 3 | grow | (−14.521, +2.994) | 21,983 | 1,759 | **8.00%** | 11.8% | false |
| 86 | 4 | grow | (−19.521, +7.994) | 10,298 | 143 | 1.39% | 2.3% | false |
| 87 | 5 | grow | (−14.521, +7.994) | 7,104 | 100 | 1.41% | 5.0% | false |
| 88 | 6 | grow | (−9.521, +2.994) | 2,156 | **29** | **1.35%** | 50.8% | **true** |

Recovery **min 1.35% / median 6.04% / max 8.00%**. **One empty look**, step 88
(29 target points, below the inherited 100-point limit). Gazes moved on the
frozen 5-degree lattice over yaw −19.5…−9.5 and pitch −7.0…+8.0.

The inherited Reality-2b semantics applied unchanged at step 88: the binocular
observation was **retained in history**, **nothing was fused**, the map was left
unchanged, and the run **continued** to its policy call. The `emptyabort`
negative exists to enforce that and fires.

### D. Geometric ledger

| g.step | input | matched | new | empty | idempotent |
|---|---|---|---|---|---|
| 82 (seed) | 3,057 | 0 | 3,057 | false | true |
| 83 | 1,008 | 798 | 210 | false | true |
| 84 | 1,905 | 1,660 | 245 | false | true |
| 85 | 1,759 | 1,529 | 230 | false | true |
| 86 | 143 | 59 | 84 | false | true |
| 87 | 100 | 67 | 33 | false | true |
| 88 | 29 | 0 | **0** | **true** | true |

- seed map **3,057 → 3,859** points, growth factor **1.262×**;
- totals after the seed: **matched 4,113, new 802**;
- looks after the seed that changed **no** geometry: **1** (step 88, the empty
  look);
- **all 7 saved maps pure `{144}`** — never admitting 141, 142, 143 or 145 — and
  **all 7 fusions replay-idempotent**;
- final map range **2.3344 / 2.6391 / 2.8113 m** against the seed patch's
  2.5146 / 2.6458 / 2.8056 — the envelope widened by about 18 cm at the near
  end; multi-look surfels **1,306**, max support **5**;
  `object_144_surface_map.ply` carries **3,859** vertices;
- raw footprint **1,098 → 1,413 cells** (10.98 → **14.13 deg²**), a **1.287×**
  angular gain.

Five-object footprints and **all** overlap diagnostics:

| object | geometry | points | footprint cells | area | vs FS1b |
|---|---|---|---|---|---|
| 141 | `SURFEL_MAP` (read-only) | 155,684 | 37,654 | 376.54 deg² | unchanged |
| 142 | `SURFEL_MAP` (read-only) | 310,884 | 62,784 | 627.84 deg² | unchanged |
| 143 | `SURFEL_MAP` (read-only) | 42,988 | 17,947 | 179.47 deg² | unchanged |
| 145 | `SURFEL_MAP` (read-only) | 6,762 | 2,125 | 21.25 deg² | unchanged |
| **144** | **`SURFEL_MAP`** (grown) | **3,859** | **1,413** | **14.13 deg²** | 1,098 → 1,413 |

**All ten pairwise overlaps and the all-object overlap are 0.** Recorded as
measurements; zero overlap is not required.

**These numbers are not combined into any productivity or novelty score**, and no
stopping rule consulted them. The `productivitygate` negative enforces that.

### E. Control ledger

| quantity | value |
|---|---|
| selected-object fixations total (incl. seed) | **7** |
| fresh FullScene-1c fixations | **6** (global steps **83..88**) |
| object watchdog | **24** — never approached |
| termination reason | **`no_frontier`** |
| `scientific_stop_reached` | **true** |
| policy decisions | 7 — `continue` ×6, `stop` ×1 |

**The final decision, stated exactly rather than interpreted.** At global step
88, object fixation index 6, the frozen controller returned `stop` **true**,
`reason` **`no_frontier`**, `next_gaze_deg` **null**, with
`candidates_before_consensus_count` **0** and
`consensus_rejected_candidate_count` **0**. Its frontier accounting was:

```text
frontier_voxel_count              810
frontier_count                     25
frontier_open_count                 0
frontier_map_resolved_count         0
frontier_boundary_resolved_count   25
```

**Every one of the 25 frontier entries was BOUNDARY_RESOLVED; none was open and
none map-resolved.** That is a different state from object 145's `no_frontier`
stop in MultiObject-3c, which ended with **30 of 72 voxels still open** and no
admissible candidate. Here the controller's frontier is **fully resolved under
its own 12 mm rules**, not merely lacking admissible moves. **This is reported as
the controller's state; it is not a completeness claim about object 144** — see
the Not-established section.

The adapter and renderer were the required frozen ones —
`policy_adapter_source` `tools/multiobject2c_policy.py`, `policy_source_modified`
**false**, `renderer_entrypoint` `tools/scene_render_fix.py` — and the local
history began at the FullScene-1b seed, with no older S0 scene-memory
observations fed to FSG6f (`priorhistory` negative enforces this).

### F. Scene invariants

- **All four pre-existing persistent objects byte-identical**: 141
  `6ac98f6251b4…`, 142 `6f90d985f807…`, 143 `bbc4b856a07d…`, 145
  `ac46e7fc815d…`, before **and** after, with
  `preexisting_objects_read_only` **true**.
- **The prior object's deferred local action remained unexecuted**:
  `deferred_prior_object_action_executed` **false**.
- **No epistemic handoff occurred** — none is reachable from this runner, and the
  `handoff` negative fires.
- **No scheduler, revisit, automatic discovery or semantic ranking occurred**:
  `automatic_scene_scheduler`, `revisit_scheduler_used`,
  `automatic_object_discovery`, `semantic_ranking_used` all **false**.
- **Truth remained closed**: `truth_opened` **false**; `quality_gate_used`
  **false**.

Outputs written: the surfel map and PLY, growth image, 7 per-look RGB previews, 6
patches, 7 maps, 6 render logs, policy trace, updated scene graph and shared
cyclopean footprints.

### Visual reading, descriptive

`object_144_growth.png` (7 panels) shows a **compact, sparse structure**: a small
rectangular outline with hatched striations along its left side. Across the
panels it extends modestly upward and downward and thickens slightly, but never
fills an area. That matches the seed image, where object 144 presented as a large
flat **blue-grey panel with a pale cream rectangle inset** — the rectangle's
border and the nearby striations are the only features carrying matchable
texture, and they are what the map consists of. The flat panel interior never
produced depth.

### G. Established / not established

Established — measured facts.

**The frozen local machinery grew the FullScene-1b seed under full scene
invariance.** The target id and pre-existing set were **consumed from the
parent**; the seed acquisition was **reconstructed, verified against the saved
patch and reused without rerendering**; frozen FSG6f — reached only through the
unchanged `multiobject2c_policy.py` adapter — chose **6** fresh actions on the
inherited 5-degree lattice through the generic renderer; the map grew **3,057 →
3,859** points (**1.262×**) and **1,098 → 1,413** footprint cells, **pure `{144}`
at all 7 maps** with **all 7 fusions replay-idempotent**. All four earlier
objects stayed **byte-identical**, all 11 pinned inputs unchanged, the deferred
prior action **unexecuted**, and the five footprints **mutually disjoint**.

**The inherited empty-look contract was exercised once and behaved exactly as
specified** (step 88: 29 points, nothing fused, observation retained, run
continued).

**The controller reached its own stop early and cleanly.** `no_frontier` at 7
fixations against a 24 watchdog, with **0 open** and **0 map-resolved** frontier
entries and **0 candidates** — a fully resolved frontier, distinct in kind from
object 145's stop.

Not established.

**This is not an accuracy claim.** Evaluator truth stayed closed; 3,859 points
and 14.13 deg² describe the representation, not the scene.

**This is not object completeness.** `no_frontier` with `frontier_open_count` 0
means the controller's frontier is exhausted **under its own 12 mm rules and its
own gaze-local extraction**, not that object 144 has been fully measured. The
seed image shows a large flat panel whose interior yields no depth at all; a
frontier built only from measured surfels cannot extend into surface the stereo
front end never recovers. **That the two coincide here is an observation, not a
demonstrated mechanism** — no counterfactual was run, and FullScene-1d is the
separate read-only audit that would examine it.

**No productivity trend may be inferred.** Six growth looks with per-look new
counts 210, 245, 230, 84, 33, 0 is too few to establish a rate or a decay, and
these numbers **gated nothing** — no score, threshold or ranking was formed from
them. The apparent decline co-occurs with recovery falling from ~6–8% to ~1.4%
and with the gaze moving off the textured rectangle, but this run tested no
causal claim about that.

**The watchdog was not the terminator and is not being called a scientific
stop** — it was never approached; the stop is the controller's own, reported with
its exact reason and candidate state above.

**No scene completeness may be inferred.** Every id currently known to the
observer is now instantiated, but the declared S0 scope begins at global step 18,
no discovery mechanism has ever run, and truth remains closed — so nothing here
says the scene contains only these five objects.

**Nothing about object 145** — its deferred local action stands unexecuted and
its state is unchanged.

**Next structurally warranted stage: FullScene-1d — a separate read-only
epistemic audit of the grown object 144.**
