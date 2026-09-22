# FullScene-1d — read-only epistemic audit of the locally resolved object

## Why this stage exists

FullScene-1a established the field-test initial condition and selected the sole known uninstantiated object. FullScene-1b seeded that object with one prescribed fixation. FullScene-1c then grew the same dynamically selected object with the unchanged local machinery.

FullScene-1c reached a genuine frozen-policy `no_frontier` stop after only seven object fixations, well before the 24-fixation watchdog. The important detail is that this stop differs structurally from the earlier object-145 stop: its final trace has **zero OPEN frontier entries**. Every remaining local frontier entry is boundary-resolved under the controller's existing rules.

That makes the next question epistemic rather than geometric.

## Central question

> When the local 3D controller says that every remaining frontier is resolved, does the cyclopean evidence agree that attention/measurement is resolved, or has the controller merely enclosed the measurable subset of the object?

This is deliberately a **read-only audit**. It does not rescue the stopped controller.

## Method

1. Consume the selected object id and scene-object set from the completed FullScene-1c parent; do not hard-code an object id.
2. Require the parent to be the genuine FullScene-1c `no_frontier` scientific stop reached before its engineering watchdog.
3. Require the saved final policy trace to have `frontier_open_count == 0` and zero candidates before consensus.
4. Load the final selected-object surfel map and all scene-object geometry read-only.
5. Replay only the selected object's established local history: the saved FullScene-1b seed observation followed by the saved FullScene-1c growth observations. Do not rerender anything and do not broaden the audit with older S0 scene-memory observations in this increment.
6. Reuse the established MultiObject-3d / Cyclopean audit machinery unchanged:
   - 0.1 degree cyclopean chart;
   - current 12 mm association semantics;
   - Cyclopean-1b shoreline classification;
   - Cyclopean-1d observation-versus-measurement refinement;
   - exact frozen-policy replay and 3D-frontier-to-cyclopean relation.
7. Classify the residual shoreline and distinguish exterior from internal components.
8. Return to scene inventory after the audit regardless of the diagnostic result. No scheduler is created here.

## Epistemic states

The refined residue uses the already-established states:

- `NEVER_OBSERVED`
- `OBSERVED_TARGET_NO_DEPTH`
- `OBSERVED_TARGET_WITH_DEPTH`
- `OBSERVED_NONTARGET_ONLY`
- `MIXED_OBSERVATION`
- `NO_RANGE_REFERENCE`

Base shoreline states such as `PHYSICAL_DEPTH_BREAK` and `AMBIGUOUS` remain reported separately.

## Interpretation without a new threshold

The audit uses literal zero/non-zero states only.

- exterior `NEVER_OBSERVED > 0` means attention debt remains even though the local 3D frontier is fully resolved;
- otherwise, `OBSERVED_TARGET_NO_DEPTH > 0` means the audit is attention-complete under its local history but measurement-partial;
- otherwise the local frontier and epistemic audit are both resolved under the current representation.

None of these labels is object completeness or accuracy.

## Strong negative contract

FullScene-1d adds:

- no Blender launch;
- no fixation;
- no fusion;
- no map growth;
- no epistemic handoff;
- no execution of the prior object's deferred action;
- no scene/revisit scheduler;
- no discovery or semantic ranking;
- no evaluator truth;
- no new threshold or quality gate.

All scene geometry and all saved observations are pinned and re-hashed after the audit.

## Expected outputs

The output record contains:

- `object_<id>_fullscene1d_epistemic_audit.json` — shoreline census, refined arcs, exact final-policy replay, frontier/cyclopean relation and interpretation;
- `object_<id>_fullscene1d_epistemic_shoreline.png` — diagnostic support/shoreline visualization;
- `prediction_manifest.json` — provenance, read-only integrity and compact summary.

The next stage is **FullScene-1e: return to the scene inventory and recompute the set of known uninstantiated candidates using the updated observation history.**

## Results

Run 2026-09-22 on the workstation, on branch **`fullscene-calibration-1`**,
**host-side only**. `FULLSCENE1D_COMPLETE`, `structural_fails: []`, no FAIL line
anywhere; the comparator agrees and exits 0.
`final_policy_stop_replayed_exactly` **true**.

**The answer is: partly.** The zero-OPEN local stop **does** correspond to
attention resolution — **exterior `NEVER_OBSERVED` is 0**, there is no unseen
territory left under the declared object-scoped history — but it does **not**
correspond to measurement resolution. **1,211 shoreline cells (59.9%) are
`OBSERVED_TARGET_NO_DEPTH`**: imaged as target across the seven looks, with
**3,107 supported projections, every one target-seen and none carrying valid
depth**.

`stop_interpretation`: **`LOCAL_FRONTIER_RESOLVED_ATTENTION_COMPLETE_MEASUREMENT_PARTIAL`**.
`object_status`: **`ATTENTION_COMPLETE_MEASUREMENT_PARTIAL`**.
`scene_disposition`: **`RETURN_TO_SCENE_INVENTORY`**.

This is a different outcome from object 145's MultiObject-3d audit, which found
`POLICY_EXHAUSTED_WITH_UNSEEN_TERRITORY` with 20 unseen cells. The two stops wore
the same `no_frontier` label; the audits separate them.

### A. Provenance and integrity

Branch **`fullscene-calibration-1`**, clean before and after. Prospective package
commit **`b0cfdf2`** adds **exactly the six FullScene-1d files, all `A`**
(`docs/fullscene1d.md`, `docs/fullscene1d-checks.md`,
`tools/dev/check_fullscene1d.py`, `tools/fullscene1d_compare.py`,
`tools/fullscene1d_public.py`, `tools/fullscene1d_run.py`). Parent result
**`f2a4dda`** (FullScene-1c).

Lineage linear, **0 merges**, 7 commits ahead of `main`. `main` and `origin/main`
remain at **`15eedee`** — untouched.

**Apply note.** `FULLSCENE1D_APPLY.md`, `_CHECKS.md`, `_CODE_PROMPT.md` and
`_HANDOFF.md` are companion files outside the repository and were not looked for
inside it; the repository documentation is `docs/fullscene1d*.md`.

**No code fix was required** — the package ran as applied, first time.

**Source freeze.** Every tracked non-documentation source present at `f2a4dda` —
**328 files** — diffs to **0 lines** against HEAD, **before and after
execution**; `git status` is empty after the run. Inherited sources pinned and
unmodified:

| source | sha256 |
|---|---|
| `multiobject3d_audit.py` | `fc50c81dccb3d29e…` |
| `cyclopean1a_topology.py` | `6ed00fca00907f33…` |
| `cyclopean1b_boundary.py` | `b34371ce8ffa86c7…` |
| `cyclopean1d_epistemic.py` | `559351701151a144…` |
| `multiobject2c_policy.py` | `f4d4a08b00981466…` |
| `fsg6f_frontier.py` | `d636c9405d719916…` |
| `fullscene1a_run.py` / `1b` / `1c` | `efc595950d894cc0…` / `db987883731c4a47…` / `4d603727ea34d44b…` |

**Input freeze.** **All 24 pinned inputs byte-identical afterwards** — the 5
FullScene-1c artifacts (manifest `9360f4d2c409f6ae…`, scene graph
`3f05a50342255ee3…`, footprints `97e4c5c6943570bd…`, surface map
`70a4bac299d73775…`, policy trace `21ca485269a925bf…`), **all 5 scene-object
geometry sources**, and **all 14 replayed calibration/observation files** (the
FullScene-1b seed plus the six FullScene-1c growth looks).

**Parent validation — all 17 gates hold.** Unique manifest match for
`FullScene1c-grow-seeded-selected-object-v1`: `previews/fullscene1c/full-seed2111`.
Schema and public digest; truth closed; fixed head/static scene;
`structural_fails []`; selected id and object set consistent with the live scene
graph (`[141, 142, 143, 144, 145]`); `termination_reason` **`no_frontier`** with
`scientific_stop_reached` **true**; stop at **7 of 24** fixations, before the
watchdog; final saved decision with `frontier_open_count` **0** and
`candidates_before_consensus_count` **0**; selected-object map pure; pre-existing
objects read-only; deferred prior action unexecuted; no handoff, scheduler or
quality threshold in 1c.

**Checks.** `py_compile` clean on all four modules; the four prescribed lines
verbatim; `SUMMARY passed=9 failed=0`. **All eleven negatives exit 1** with a
named detector — `acquire`, `handpick`, `openfrontier`, `copyaudit`,
`oldhistory`, `depthonly`, `crossobject`, `execute_deferred`, `threshold`,
`scheduler`, `truth` — **none exited 0 or 2**, and the exit-2 escape branch was
verified live. **No regression**: **33/33** prior suites green, **239/239** prior
negatives firing, **none weakened**; the Cyclopean-1f caveat stands and 1f was
not edited.

Environment: host `.venv/bin/python` 3.12.3, **no Blender, no Cycles, no GPU**
(`pgrep blender` 0 before and after). **1.6 s**.

### B. Parent stop reproduction

Consumed dynamically from the parent, never hand-picked:

| quantity | value |
|---|---|
| selected object id | **144** |
| selected-object map points | **3,859** |
| observation steps | **82..88** (7 looks) |
| visited gaze envelope | yaw **[−19.521, −9.521]**, pitch **[−7.006, +7.994]** |
| parent fixations vs watchdog | **7 of 24** |

**The final frozen decision replayed exactly — all eleven fields:**

| field | saved | replayed | match |
|---|---|---|---|
| `stop` | True | True | ✓ |
| `reason` | `no_frontier` | `no_frontier` | ✓ |
| `next_gaze_deg` | null | null | ✓ |
| `frontier_voxel_count` | 810 | 810 | ✓ |
| `frontier_count` / `raw_count` | 25 | 25 | ✓ |
| **`frontier_open_count`** | **0** | **0** | ✓ |
| `frontier_map_resolved_count` | 0 | 0 | ✓ |
| **`frontier_boundary_resolved_count`** | **25** | **25** | ✓ |
| `candidates_before_consensus_count` | 0 | 0 | ✓ |
| `consensus_rejected_candidate_count` | 0 | 0 | ✓ |

Saved `current_gaze_deg` **(−9.520574, +2.994241)**.
**`frontier_open_count == 0` is confirmed in both the saved and the replayed
decision**, and the OPEN / MAP_RESOLVED / BOUNDARY_RESOLVED partition is
**0 / 0 / 25**.

### C. Epistemic census

Object-scoped chart **92 × 122** cells (11,224 total), grid **0.1 deg**, `yaw0`
−24.80, `pitch0` −7.20. Footprint **3 cells** / **0.2605 deg**, from the
unchanged 12 mm association radius at this object's own range.

Support chain: raw support **1,413** → support after footprint dilation
**6,203**, complement **5,021**, **shoreline 2,022**, maximum exterior border
distance **69** cells.

**Base shoreline states (Cyclopean-1b, unchanged):**

| state | cells | share |
|---|---|---|
| `UNOBSERVED` | 1,953 | 96.6% |
| `PHYSICAL_DEPTH_BREAK` | 36 | 1.8% |
| `AMBIGUOUS` | 33 | 1.6% |
| `TARGET_CONTINUATION` | 0 | 0.0% |

**Refined states (Cyclopean-1d, unchanged), exterior / internal:**

| refined state | all | exterior | internal |
|---|---|---|---|
| **`OBSERVED_TARGET_NO_DEPTH`** | **1,211** | **1,031** | **180** |
| `NO_RANGE_REFERENCE` | 578 | 522 | 56 |
| `OBSERVED_NONTARGET_ONLY` | 157 | 157 | 0 |
| `MIXED_OBSERVATION` | 7 | 7 | 0 |
| **`NEVER_OBSERVED`** | **0** | **0** | **0** |
| `OBSERVED_TARGET_WITH_DEPTH` | 0 | 0 | 0 |
| **total** | **1,953** | **1,717** | **236** |

Components: **6** — one `EXTERIOR` of 4,609 cells at max border depth **69**, and
**5 `INTERNAL`** holes of 1, 35, 36, 94 and 246 cells.

**Arcs: 498 in total.** There are **zero `NEVER_OBSERVED` arcs**, so there is no
unseen territory to characterise — the question of arc number, size and location
for unseen regions has an empty answer here, which is itself the finding.

| kind | state | arcs | cells |
|---|---|---|---|
| EXTERIOR | `OBSERVED_TARGET_NO_DEPTH` | 19 | 1,031 |
| EXTERIOR | `NO_RANGE_REFERENCE` | 386 | 522 |
| EXTERIOR | `OBSERVED_NONTARGET_ONLY` | 35 | 157 |
| EXTERIOR | `MIXED_OBSERVATION` | 7 | 7 |
| INTERNAL | `OBSERVED_TARGET_NO_DEPTH` | 5 | 180 |
| INTERNAL | `NO_RANGE_REFERENCE` | 46 | 56 |

**Meaningful arcs (≥ 20 cells): 18 of 498**, every one of them
`OBSERVED_TARGET_NO_DEPTH`. The largest:

| cells | kind | border depth | centroid yaw | centroid pitch | inside envelope | nearest gaze |
|---|---|---|---|---|---|---|
| 166 | EXTERIOR | 38 | −19.75 | +1.86 | false | 3.872 deg |
| 161 | EXTERIOR | 36 | −20.65 | −4.90 | false | 3.109 deg |
| 141 | EXTERIOR | **69** | −19.18 | −4.20 | **true** | 2.218 deg |
| 111 | EXTERIOR | 22 | −22.83 | −5.38 | false | 4.729 deg |
| 97 | EXTERIOR | 43 | −22.80 | +2.13 | false | 5.279 deg |
| 88 | INTERNAL | — | −20.06 | −1.04 | false | 1.109 deg |
| 73 | EXTERIOR | 40 | −17.88 | −3.29 | **true** | 2.083 deg |
| 60 | EXTERIOR | 27 | −18.80 | +2.58 | **true** | 4.302 deg |

Of the 18 meaningful arcs, **8 centroids lie inside the visited gaze envelope and
10 outside**, at nearest-gaze distances of **1.1 to 5.3 degrees**. Unlike object
145's case, these are **not** unseen: every one was imaged as target and returned
no depth.

Evidence totals confirm the observation/measurement separation:
`OBSERVED_TARGET_NO_DEPTH` carries **3,107 supported projections, 3,107
target-seen, 0 with valid depth**; `OBSERVED_NONTARGET_ONLY` 311 supported
projections all non-target; `MIXED_OBSERVATION` 9 target-seen and 10 non-target;
`NO_RANGE_REFERENCE` **0** supported projections; `NEVER_OBSERVED` has no arcs at
all.

### D. Local-stop interpretation

**The measured case is `LOCAL_FRONTIER_RESOLVED_ATTENTION_COMPLETE_MEASUREMENT_PARTIAL`** —
no exterior unseen cells remain (`NEVER_OBSERVED` exterior = **0**), but
target-no-depth residue exists (**1,211** cells). The runner's own literal rule
selected it; no threshold was consulted.

`local_stop_subtype`: **`ZERO_OPEN_FRONTIER_BOUNDARY_RESOLVED_STOP`**.

**Frozen frontier-to-cyclopean relation, all states** — each frozen look-ahead
target angularly quantized onto the unchanged 0.1-degree chart, descriptive only:

| frontier state | total | cyclopean cell class |
|---|---|---|
| `OPEN` | **0** | — |
| `MAP_RESOLVED` | **0** | — |
| **`BOUNDARY_RESOLVED`** | **25** | **`OUT_OF_CHART` 25** |

The boundary-resolved count **reproduces the parent's 25 exactly**, and **all 25
project outside the object's own chart** — they point beyond the angular extent
object 144's map occupies. With zero OPEN targets, the
inside/outside-gaze-envelope counts for OPEN are both **0**.

### E. Scene invariants

- **No Blender, no fixation, no fusion, no growth** — `pgrep blender` 0 before
  and after; the record contains no acquisition directory; `NO_ACQUISITION` is
  declared in the public contract and the `acquire` negative enforces it.
- **All five scene-object geometry sources byte-identical**: 141
  `6ac98f6251b47337…`, 142 `6f90d985f8078a7d…`, 143 `bbc4b856a07d2be5…`, 144
  `70a4bac299d73775…`, 145 `ac46e7fc815d103c…`.
- **The prior deferred object-145 action remains unexecuted.**
- **No epistemic handoff**, and no scheduler, revisit, automatic discovery or
  semantic ranking occurred.
- **Evaluator truth closed.**
- **Older S0 history was not added**: the audit replayed **only** the
  FullScene-1b seed (step 82) and the six FullScene-1c growth looks (83..88) —
  7 observations, steps 82..88. The `oldhistory` negative enforces this.

### Visual reading, descriptive

`object_144_fullscene1d_epistemic_shoreline.png` (92 × 122, 3× upscale). A pixel
census reproduces the report **exactly on all eight classes** — 6,203 support,
1,211 `OBSERVED_TARGET_NO_DEPTH`, 578 `NO_RANGE_REFERENCE`, 157
`OBSERVED_NONTARGET_ONLY`, 36 `PHYSICAL_DEPTH_BREAK`, 33 `AMBIGUOUS`, 7
`MIXED_OBSERVATION`, **0 `NEVER_OBSERVED`**, 2,999 background — summing to all
11,224 chart cells.

The picture shows the support as a set of **wavy horizontal grey bands** — the
striations the FullScene-1c growth strip built — and **every band edge traced in
orange**. Teal `OBSERVED_NONTARGET_ONLY` speckle rims the outer boundary; blue
and purple appear only as small marks. **There is no red anywhere**, confirming
visually what the census says: **no unseen territory remains**.

### F. Established / not established

Established — measured facts.

**The zero-OPEN local stop coincides with attention resolution but not with
measurement resolution.** Under the declared object-scoped history, exterior
`NEVER_OBSERVED` is **0** and there are **zero unseen arcs**; at the same time
**1,211 of 2,022 shoreline cells (59.9%)** are `OBSERVED_TARGET_NO_DEPTH`, in 24
arcs carrying **3,107 supported projections, all target-seen, none with valid
depth**. The measured case is
**`LOCAL_FRONTIER_RESOLVED_ATTENTION_COMPLETE_MEASUREMENT_PARTIAL`**.

**The parent stop reproduced exactly** — all eleven fields, with
`frontier_open_count` **0** in both saved and replayed decisions and the
partition **0 OPEN / 0 MAP_RESOLVED / 25 BOUNDARY_RESOLVED**; all 25
boundary-resolved targets quantize **out of the object's chart**.

**The audit was strictly read-only**: no acquisition, no fusion, no growth, no
handoff; all 24 pinned inputs and all five object sources byte-identical; the
deferred object-145 action untouched; truth closed; only the seed-plus-growth
history replayed.

Not established.

**`frontier_open_count == 0` means local frontier resolution under frozen FSG6f,
not physical object completeness.** The controller's frontier is built from
measured surfels and extracted relative to the current gaze; it cannot extend
into surface the stereo front end never recovers. Its exhaustion says where the
controller can still act, not where the object ends.

**`OBSERVED_TARGET_NO_DEPTH` is measurement residue, not proof that new sensing
could recover it.** These 1,211 cells were imaged as target and returned no
depth under this matcher, baseline, vergence and illumination — **none of which
was changed or tested here**. Whether a different instrument would measure them
is untested.

**`NEVER_OBSERVED = 0` is attention debt discharged under the declared local
history, not a scene-discovery claim.** It is scoped to the seven
seed-plus-growth observations of this object; it says nothing about the wider
scene, and no discovery mechanism ran.

**No accuracy claim and no full-scene completeness claim.** Evaluator truth
stayed closed, so 3,859 points and every cell count describe the representation,
not the scene; and that every currently known id is instantiated implies nothing
about how many objects the scene contains.

**Next stage: FullScene-1e — return to scene inventory and recompute the
known-uninstantiated candidate set from the updated field-test history.**
