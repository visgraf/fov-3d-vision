# MultiObject-3c — grow the scene-selected fourth object

## Question

Can the same frozen selected-object growth machinery repeat on the object selected by MultiObject-3a and seeded by MultiObject-3b, while every previously instantiated scene object remains separate and byte-identical?

This is the second end-to-end scene-memory `select -> seed -> grow` cycle. The target id is consumed from the completed MultiObject-3b parent; it is not hard-coded in MultiObject-3c.

## Occam choice: reuse the existing adapter

MultiObject-2c already introduced a generic pure target-label adapter in `tools/multiobject2c_policy.py`. MultiObject-3c **reuses that file unchanged** rather than copying it under a new name. The adapter presents only the parent-selected scene id under FSG6f's historical target label and maps every other id to non-target for policy input only. Geometry always retains the real scene id.

This is deliberate: repeatability should reuse machinery, not reproduce it.

## Frozen science

- fixed head and static Reality fixture;
- existing stereo front end;
- generic `tools/scene_render_fix.py` acquisition entry point;
- unchanged `tools/multiobject2c_policy.py` label adapter;
- frozen FSG6f frontier/controller;
- frozen 12 mm FSG3/FSG6f association rule;
- inherited 5 degree local saccade lattice and all FSG6f numerical rules;
- Reality-2b empty-look semantics: fewer than 100 selected-object points is valid negative evidence, not a runtime failure;
- object-scoped 24-fixation watchdog including the MultiObject-3b seed, engineering only.

Every object already present in the MultiObject-3b scene graph remains read-only. Only pixels carrying the parent-selected scene id may enter the new object's surfel map.

## History

Active growth history begins at the saved MultiObject-3b seed observation. The earlier scene-memory observations that selected the object and positioned the seed are not replayed as growth-policy history. The seed acquisition is reused, never rerendered. The first new global fixation is the next chronological step after the seed.

## Measurement diagnostic

MultiObject-3b measured a low seed-view depth-recovery fraction for the selected object. MultiObject-3c does **not** react to that measurement. Each look simply records:

- visible selected-object pixels;
- valid selected-object depth points;
- recovered fraction `valid / visible`;
- frame-wide valid stereo fraction.

These values are descriptive only. They rank nothing, change no controller parameter, alter no stopping rule, and gate no outcome. The scientific value is the comparison with the earlier measurement regimes under the same instrument.

## Stop

Scientific stop remains the frozen FSG6f stop (`no_frontier`). The 24 selected-object-fixation watchdog is only an engineering guardrail. If the watchdog is reached while the policy still says `continue`, the run is structurally complete but the scientific stop was not reached.

## Outputs

The run writes the selected-object surfel map and PLY, growth image, per-look RGB previews, patches/maps, policy trace, updated scene graph, shared cyclopean footprints, and a manifest with per-look stereo-recovery diagnostics and integrity hashes.

No automatic discovery, revisit scheduler, scene scheduler, semantic ranking, mesh/interpolation, evaluator truth, or quality gate is introduced.

## Next

After growth, audit the selected object's epistemic remainder and continue scene progress. An unfinished object does not block the tour.

## Results

Run 2026-09-22 on the workstation. `MULTIOBJECT3C_COMPLETE`, `structural_fails:
[]`, no FAIL line anywhere; the comparator agrees and exits 0.

**This is the first scientific stop in the MultiObject series.**
`termination_reason: no_frontier`, `scientific_stop_reached: true`. The frozen
FSG6f policy returned `continue` twelve times and then **stopped on its own
condition** after **13 selected-object fixations — eleven short of the
24-fixation watchdog**, which was never reached.

Object 145 — the id consumed from MultiObject-3b, never declared here — grew
**3,662 -> 6,426** surfels (**1.75x**), pure `{145}` at every map, while objects
141, 142 and 143 stayed **byte-identical** and all six pairwise footprint
overlaps remained **0**.

Two firsts, both from identical machinery: **the frozen stop condition fired**,
and **the Reality-2b empty-look branch was exercised — 4 of 13 looks**, the first
time in the programme.

### Provenance

Working tree clean at the start. Package commit **`f4098dd`** adds **exactly the
six MultiObject-3c files, all `A`**; parent result **`627ff7a`**.

**There is no `multiobject3c_policy.py`** — confirmed absent on disk and absent
from the package commit. The adapter `tools/multiobject2c_policy.py`
(`f4d4a08b00981466…`) is **reused unchanged**, exactly as the Occam clause
requires, and the `copypolicy` negative exists to enforce it.

Frozen audit at full scope: **every tracked non-documentation source present at
`627ff7a` — 287 files** across `tools/`, `tools/dev/` and `scenes/`.
`git diff 627ff7a HEAD` over that set is **empty (0 lines)** and all **287 sha256
are SAME**. The complete changed-file list between parent result and HEAD is the
six new 3c files and nothing else. The sources 3c must reuse unchanged:

| source | sha256 |
|---|---|
| `multiobject2c_policy.py` | `f4d4a08b00981466…` |
| `fsg6f_frontier.py` | `d636c9405d719916…` |
| `multiobject1b_policy.py` | `4068b3a4ecd7d645…` |
| `scene_render_fix.py` | `6e70bbb78c1043ec…` |
| `reality2_render_fix.py` | `9f1433d189fbcbb5…` (unchanged, **never invoked**) |
| `fsg3_surface_map.py` | `1b9dbeb873105ec9…` |
| `reality2b_public.py` | `dfe1ca243c4c1543…` |
| `multiobject3b_run.py` | `6521d43f53fcaa94…` |

The parent was located **by manifest**, not by assumed path: exactly one
`MultiObject3b-seed-selected-object-v1` record —
`previews/multiobject3b/full-seed2111` — seed **2111**, `truth_opened` **false**,
`added_fixations` **1**, `fusion_iterations_added` / `growth_iterations_added`
**0**, `new_object_instantiated` **true**, `existing_objects_read_only` **true**,
`structural_fails` **[]**.

### Consumed ids and seed reproduction

| quantity | value | source |
|---|---|---|
| `selected_object_id` | **145** | `multiobject3c_run.py:58`, from the 3b manifest |
| `existing_object_ids_before` | **[141, 142, 143]** | `multiobject3c_run.py:59`, from the 3b manifest |
| 3b scene graph | 141/142/143 read-only `SURFEL_MAP`, 145 `SEED_SURFEL_PATCH` | validated by the runner |

**The literal `145` appears zero times in all three MultiObject-3c sources**; it
appears three times only in the checker, as the `handpick` mutation string and
the two assertions that it is absent from the real sources. The runner also
asserts the target is positive, not already instantiated, that the 3b object set
is consistent, that each pre-existing object is a **read-only `SURFEL_MAP`**, and
that the target is a **`SEED_SURFEL_PATCH`**.

**Seed recomputed, not trusted.** Re-running `compute_once` on the saved `fix_66`
acquisition and selecting `valid & (instance_id == 145)` gives **3,662** points,
**`xyz` byte-identical at stored float32 precision** to
`object_145_seed_patch.npz`, **ids byte-identical**, ids exactly `{145}`. The
runner performs the same comparison itself before initializing the map. Verified
independently **before** the run as well.

### History scope, and no rerender

Growth history begins at the **3b seed, global step 66**. The first new fixation
is **67** — the next chronological step — and the last is **78**.

- the record's `acquisitions/` directory holds **fix_67 … fix_78, twelve
  entries**; **`fix_66` is absent**, so the seed was reused and never rerendered;
- `parent_fixations_rerendered` **0**, `added_fixations` **12**;
- the pre-seed scene-memory observations (steps 18..65) were **not** replayed as
  growth-policy history — the `priorhistory` negative enforces that clause and
  fires.

### Environment and wall time

Blender 5.2.1 LTS headless, Cycles, **OPTIX** on an RTX 4090 (driver 595.84);
host `.venv/bin/python` 3.12.3. **105.5 s total**, growth loop **105.1 s**, **12
Blender launches**.

### Checks

`py_compile` clean on all four modules. The three prescribed lines appeared
verbatim:

```text
[multiobject3c-growth] PASS parent_selected=true preexisting_read_only=true selected_only=true reused_frozen_adapter=true seed_scoped_history=true
[multiobject3c-instrument] PASS generic_renderer=true object_scoped_watchdog=true empty_evidence=true texture_diagnostic=true scheduler=false
[multiobject3c-check] SUMMARY passed=6 failed=0
```

All **seven** negatives are genuine source-mutation controls, each exiting **1**
with a named detector; **none exited 2**:

| negative | rc | detected by |
|---|---|---|
| `handpick` | 1 | `parent_selected_target_and_scene_ids_not_handpicked` |
| `crossfuse` | 1 | `preexisting_read_only_selected_only_growth` |
| `copypolicy` | 1 | `reuse_existing_frozen_adapter` |
| `priorhistory` | 1 | `seed_scoped_history` |
| `legacyrenderer` | 1 | `generic_renderer_object_scoped_watchdog` |
| `globalwatchdog` | 1 | `generic_renderer_object_scoped_watchdog` |
| `texturegate` | 1 | `empty_evidence_texture_diagnostic_no_scheduler_gate` |

The **exit-2 escape branch was verified live**: an inert mutation on a scratch
copy of the runner was detected by **no** check, exactly the condition under
which the checker prints `ERROR ... mutation escaped detection` and exits 2.

**No regression**: **24/24** prior suites green and **155/155** prior negatives
still firing, **none weakened**. The **Cyclopean-1f caveat stands as a standing
caveat and 1f was not edited**.

### Full fixation table

History begins at the 3b seed (global step 66). Gazes move on the frozen 5-degree
lattice.

| g.step | obj # | src | gaze (yaw, pitch) | tgt visible | valid depth | recovery | frame valid | in | new | matched | empty | idem |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 66 | 0 | seed | (+20.822, +0.001) | 54,784 | 3,662 | 6.7% | 5.6% | 3,662 | 3,662 | 0 | false | true |
| 67 | 1 | grow | (+15.822, −4.999) | 25,453 | 2,404 | 9.4% | 27.5% | 2,404 | 720 | 1,684 | false | true |
| 68 | 2 | grow | (+10.822, +0.001) | 7,168 | 119 | 1.7% | 58.1% | 119 | 103 | 16 | false | true |
| 69 | 3 | grow | (+10.822, +5.001) | 5,241 | **94** | 1.8% | 49.5% | 94 | 0 | 0 | **true** | true |
| 70 | 4 | grow | (+10.822, +10.001) | 2,108 | **34** | 1.6% | 25.3% | 34 | 0 | 0 | **true** | true |
| 71 | 5 | grow | (+15.822, +10.001) | 11,530 | 1,107 | 9.6% | 9.5% | 1,107 | 700 | 407 | false | true |
| 72 | 6 | grow | (+20.822, +10.001) | 16,126 | 1,081 | 6.7% | 3.8% | 1,081 | 246 | 835 | false | true |
| 73 | 7 | grow | (+15.822, +5.001) | 28,235 | 2,685 | 9.5% | 18.8% | 2,685 | 365 | 2,320 | false | true |
| 74 | 8 | grow | (+20.822, +5.001) | 40,286 | 2,739 | 6.8% | 5.3% | 2,739 | 249 | 2,490 | false | true |
| 75 | 9 | grow | (+15.822, +0.001) | 38,144 | 3,538 | 9.3% | 22.0% | 3,538 | 226 | 3,312 | false | true |
| 76 | 10 | grow | (+10.822, −4.999) | 4,687 | **70** | 1.5% | 54.9% | 70 | 0 | 0 | **true** | true |
| 77 | 11 | grow | (+15.822, −9.999) | 8,835 | 836 | 9.5% | 54.1% | 836 | 155 | 681 | false | true |
| 78 | 12 | grow | (+10.822, −9.999) | 1,604 | **21** | 1.3% | 59.4% | 21 | 0 | 0 | **true** | true |

### Growth and recovery diagnostics

**Growth.** **3,662 -> 6,426** points (**1.75x**) over 13 object fixations.
**Pure `{145}` at all 13 saved maps** — never admitting 141, 142, 143 or 144 —
and **all 13 replay-idempotent**. Final map range **2.5265 / 2.7627 / 3.0033 m**,
multi-look surfels **3,761**, max support **6**;
`object_145_surface_map.ply` carries **6,426** vertices, matching the map.

**The empty-look branch fired, for the first time in the programme.**
`empty_steps: [69, 70, 76, 78]` — **4 of 13 looks** returned fewer than 100
selected-object points (94, 34, 70, 21). Each was recorded as **valid negative
evidence**: the binocular observation entered policy history, **nothing was
fused**, the map was left unchanged, and the loop continued. No error, no retry,
no special case. The Reality-2b semantics inherited since Reality Check 2b had
never previously been exercised; here they carried a quarter of the run.

**Recovery diagnostics — descriptive only** (`texture_diagnostics_are_gates:
false`, `quality_gate_used: false`). Per-look target depth recovery **min 1.3%,
median 6.7%, max 9.6%**.

The comparison across the four objects under one unchanged instrument:

| object | per-look recovery | seed -> final | fixations | termination |
|---|---|---|---|---|
| 142 | 58.8–77.3% (med 70.3%) | 38,020 -> 310,884 (8.2x) | 24 | `object3_watchdog` |
| 143 | 1.4–2.5% | 5,344 -> 42,988 (8.0x) | 24 | `object2_watchdog` |
| **145** | **1.3–9.6% (med 6.7%)** | **3,662 -> 6,426 (1.75x)** | **13** | **`no_frontier`** |

The low recovery **changed nothing in the machinery**: no threshold was added, no
constant retuned, no look skipped or retried because of it. It is recorded, and
the policy behaved as it always does.

### Termination — a scientific stop, precisely stated

`termination_reason` **`no_frontier`**, `scientific_stop_reached` **true**,
`selected_object_fixations_total` **13** against a watchdog of **24**. The policy
returned `continue` at **12** decisions and `stop` at the **13th**.

At the final decision (global step 78, object fixation 12) the frozen controller
reported `candidates_before_consensus_count` **0** — **no candidate gaze was
generated at all**, which is the controller's own `no_frontier` condition —
with `next_gaze_deg` **null**. Frontier accounting at that moment: **72** voxels
= **30 open** + 1 map-resolved + **41 boundary-resolved**, of 1,368 frontier
voxels total; `frontier_state_radius_m` **0.012**, the same 12 mm. Map extent
yaw **[+15.68, +24.42]**, pitch **[−6.54, +7.35]**.

**Stated precisely: the frozen rule reached its own stop, and that is not the
same as the object being complete.** Thirty frontier voxels were still labelled
open; what ended the run is that the controller's candidate generator produced
**nothing admissible** under its unchanged consensus and exit-corridor rules.
This is the scientific stop the contract names — but it bounds the *policy*, not
the *geometry*.

### Purity and read-only integrity

**All 10 pinned inputs byte-identical afterwards** — the five 3b files
(`prediction_manifest.json` `a0716d9c544d0421…`, `scene_graph.json`
`33ee596270e58892…`, `object_145_seed_patch.npz` `968c5e30206ec401…`,
`object_145_seed_rgb.png` `52479b5b9cb6baf4…`,
`scene_cyclopean_footprints.npz` `0a02841357ff7440…`), the three object geometry
sources, and the two seed-acquisition files (`calibration.json`
`f972005da611ab67…`, `observation.npz` `becf00c87e60bc3f…`).

| object | sha256 before | after | points | ids |
|---|---|---|---|---|
| 141 | `6ac98f6251b47337…` | same | 155,684 | `{141}` |
| 142 | `6f90d985f8078a7d…` | same | 310,884 | `{142}` |
| 143 | `bbc4b856a07d2be5…` | same | 42,988 | `{143}` |

Manifest: `preexisting_objects_read_only` **true**, `selected_object_map_pure`
**true**, `policy_source_modified` **false**, `truth_opened` **false**,
`automatic_object_discovery` / `automatic_scene_scheduler` /
`revisit_scheduler_used` / `quality_gate_used` all **false**,
`renderer_entrypoint` **`tools/scene_render_fix.py`**, `fusion_rule`
**{0.012, 0.012}**, `policy_adapter_source` **`tools/multiobject2c_policy.py`**.

### Footprint relations — measurements, never gates

| object | geometry | points | footprint cells | area |
|---|---|---|---|---|
| 141 | `SURFEL_MAP` (read-only) | 155,684 | 37,654 | 376.54 deg² |
| 142 | `SURFEL_MAP` (read-only) | 310,884 | 62,784 | 627.84 deg² |
| 143 | `SURFEL_MAP` (read-only) | 42,988 | 17,947 | 179.47 deg² |
| **145** | **`SURFEL_MAP`** (grown) | **6,426** | **2,041** | **20.41 deg²** |

Shared chart **624 x 488**, grid 0.1 deg. Object 145 grew **1,165 -> 2,041**
cells (**1.75x**, the same factor as its point count) and now spans yaw
**[+15.50, +25.00]**, pitch **[−6.80, +7.60]** — widened from the seed's
[+16.30, +25.00] x [−5.60, +5.70]. It remains the **smallest footprint in the
scene**, 20.41 deg² against 142's 627.84.

**All six pairwise overlaps and the all-object overlap are 0.** Recorded as what
this configuration produced; the contract still declines to make disjointness a
requirement.

### Visuals

`object_145_growth.png` (13 panels) shows growth quite unlike object 142's
area-filling: the map is a **narrow vertical wisp of thread-like strands** that
thickens and extends slightly upward and downward across the panels, never
filling an area. That is the visible counterpart of 1.3–9.6% recovery — only the
textured seams and edges between the flat bands ever match.

`scene_cyclopean_footprints.png`, the four-object chart: object 141's cloth
quadrilateral with panel seams and the black emblem ellipse at centre, 143's
architectural frame around it, 142's broad wood-grain expanse filling the lower
half, and **object 145 as a bright narrow vertical double-stripe on the right**,
now taller than at the seed and carrying a faint drapery-like structure. A pixel
census reproduces the scene graph exactly (37,654 / 62,784 / 17,947 / 2,041
cells) with **zero pixels at the overlap-marker level**, consistent with all
overlaps being 0.

An empty look is visible for what it is: `rgb/fix_70.png` is mostly flat grey
wall with a cream panel at lower left and a terracotta strip at the right edge —
object 145 occupies a thin slice and returns 34 depth points, below the inherited
100-point limit.

Twelve per-look RGB previews, twelve patches, thirteen maps and twelve render
logs were written alongside.

### Structural failures and code fixes

**Structural failures: none.** `structural_fails: []` in both the manifest and
the comparator; purity at all 13 maps; three pre-existing objects byte-identical;
all 10 pinned inputs unchanged; `parent_fixations_rerendered` 0; truth closed.

**Code fixes: none.** No MultiObject-3c file needed repair and no frozen prior
source was modified. The package ran as applied, first time.

One note on the comparator, recorded rather than changed: it prints the literal
string `MULTIOBJECT3C_COMPLETE` **before** its failure list and signals failure
only through exit code 1 and a non-empty `structural_fails`. Here it exited **0**
with `structural_fails: []`, so the label is accurate — but on a failing record
the prefix would be misleading, and a reader must check the exit code and the
list, not the word.

### What this establishes, and what it does not

Established. **The scene-level machinery repeats without special treatment.** The
target id and the pre-existing set were **consumed from the 3b parent** (the
literal never appears in 3c source), the seed was **reproduced byte-identically**
and reused without rerendering, the **already-frozen MultiObject-2c adapter was
reused unchanged** rather than copied — no `multiobject3c_policy.py` exists — and
frozen FSG6f, the 12 mm rule, the 5-degree lattice and the generic renderer all
ran untouched. Objects 141, 142 and 143 stayed **byte-identical**, the new map
stayed **pure `{145}` at all 13 saves**, every fusion was **replay-idempotent**,
and the four footprints remain **mutually disjoint**.

Established, and new. **The frozen policy reached its own scientific stop for the
first time in this series** — `no_frontier` after 13 fixations, **eleven short of
the watchdog** — where objects 142 and 143 both exhausted their 24-fixation
guardrail with the policy still saying `continue`. And **the Reality-2b
empty-look branch was exercised for the first time**, on 4 of 13 looks, behaving
exactly as specified: negative evidence recorded, nothing fused, loop continued.
Both outcomes came from **identical, unmodified machinery**; the difference is
the object, not the instrument.

Not established. **A scientific stop is not object completeness.** The controller
stopped because it generated **no admissible candidate**, with **30 frontier
voxels still open** — it bounds the policy's reach, not the object's geometry,
and 6,426 points at 1.75x is a small map by any comparison in this scene. **No
accuracy claim** — evaluator truth stayed closed. **No claim that the low
recovery is irreducible** — no alternate matcher, baseline, vergence or
illumination was tried, by design, and the 1.3–9.6% band is a measurement of this
instrument on this surface. **No explanation of *why* the stop came early** — that
`no_frontier` and low texture co-occur here is an observation, not a demonstrated
mechanism, and **nothing was tuned to test it**. **Zero overlap is still not an
invariant** — it now survives four objects and nothing more. And **no discovery,
revisit scheduler, scene scheduler, semantic ranking, mesh or interpolation** was
introduced; objects 142 and 143 remain retained as unfinished.

**Next: audit the selected object's residual epistemic state and continue scene
progress.** An unfinished object does not block the tour.
