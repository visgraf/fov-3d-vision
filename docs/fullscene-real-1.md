# FullScene-REAL-1 — End-to-End Frozen-System Benchmark

## Blocker repair: procedural fixture, not `.blend`

The first REAL-1 prospective package made one false interface assumption: it
required a `.blend` input. The established FullScene/Reality lineage does not
load one. `tools/scene_render_fix.py` renders the procedural Reality-1 fixture
named `tabletop_cloth`, built from the evaluator-side scene specification.

REAL-1 therefore binds to a **fixture name**, not a file path. Provenance is the
fixture name plus the established evaluator scene-spec `truth_digest()`. It must
never record a `.blend` hash for a file the renderer does not consume.

## Purpose

REAL-1 is the first deliberately end-to-end field run of the current foveal
stereo system on the established procedural test fixture. It begins from the
completed FullScene-1d calibration state but does **not** reuse the reconstructed
object maps as reconstruction input.

The benchmark asks:

> What geometric/RGB-D scene representation does the frozen current system
> produce when every benchmark object is attempted once, and where do attention,
> measurement, geometry and control debts remain?

## The pre-control enumeration oracle

REAL-1 is not an autonomous discovery benchmark. To guarantee that every
benchmark object is attempted, a **quarantined REAL-1-only helper** may inspect
the evaluator-side procedural scene specification before control.

This is an explicit declassification boundary. The helper may output only:

- `object_id`
- `seed_yaw_deg`
- `seed_pitch_deg`
- `label`

It may use exact procedural geometry internally to derive the seed direction,
but vertices, surfaces, depth, normals, range, masks, coverage, or object extent
must not cross into the observer process.

`tools/fullscene_real1_oracle_scaffold.py` is the only new REAL-1 module allowed
to import the evaluator-side scene specification before observer control.
`fullscene_real1_run.py` and `fullscene_real1_repo_adapter.py` consume only the
sanitized `enumeration_oracle.json`.

This makes the benchmark statement precise:

- object discovery is **not** tested;
- object identity and one seed direction are oracle scaffolding;
- stereo reconstruction, fusion, local growth, stopping, audit and handoff do
  not receive exact evaluator geometry/depth truth.

## What remains frozen

The benchmark continues to reuse unchanged:

- `tools/scene_render_fix.py` procedural acquisition path;
- current stereo front end;
- frozen FSG6f via `tools/multiobject2c_policy.py`;
- 12 mm surfel association;
- `<100` valid-target-point empty-look semantics;
- 24 selected-object-fixation watchdog including seed;
- established epistemic audit semantics;
- at most one already-demonstrated epistemic handoff when warranted.

No pre-REAL-1 source may be edited merely to make the benchmark run.

## Object loop

For each sanitized oracle row, sorted by positive instance id:

1. take one seed fixation at the oracle-supplied yaw/pitch using the unchanged
   generic renderer and stereo front end;
2. if usable selected-object geometry exists, grow with frozen local machinery
   until `no_frontier` or the object watchdog;
3. run the established read-only epistemic audit;
4. only for `no_frontier` + exterior `NEVER_OBSERVED > 0`, permit one bounded
   epistemic handoff and at most one returned local action;
5. freeze the object status and move on.

There is no recursive handoff scheduler and no revisit scheduler in REAL-1.

## Observer seal and evaluator phase

Before full evaluator truth is rendered/opened, export and seal the observer:
per-object geometry, combined point cloud, sparse observer depth/instance
panoramas, fixation history, status table and `observer_complete.json`.

Only after that seal may the evaluator phase generate reference RGB/depth/
instance panoramas and compute coverage/depth-error/purity/efficiency metrics.
Truth may evaluate the observer; it may not repair it.

## RGB-D naming discipline

If the current surfel representation carries no photometric RGB, do not invent
an observer RGB panorama. A reference RGB panorama is an evaluator product. If
Code can construct an RGB mosaic solely from acquired observer images, it may
export it as an explicitly named observer-acquisition mosaic; otherwise the
observer's primary panorama products remain sparse depth/instance/validity.

## Checkpoint / resume

Each completed object gets `object_complete.json`. `--resume` skips completed
objects without rerendering them and continues global step numbering. A sealed
observer must never silently resume into additional control actions.

## Branch discipline

All REAL-1 repair/integration/result work stays on `fullscene-real-1`. `main`
and `fullscene-calibration-1` remain untouched.

## Results

**COMPLETE 2026-09-22 on branch `fullscene-real-1`** (`[fullscene-real1] COMPLETE`,
`structural_fails: []`; `tools/fullscene_real1_compare.py` prints
`FULLSCENE_REAL1_COMPLETE` and exits 0). Record:
`previews/fullscene-real1/full-seed2111`, seed 2111, profile `full`, OPTIX on
RTX 4090, Blender 5.2.1 LTS, host Python 3.12.3.

### Binding and provenance

The repaired binding is what actually ran. REAL-1 took `--fixture
tabletop_cloth`; **no `.blend` path was accepted, claimed or hashed.**
Provenance is the fixture name plus the established evaluator scene-spec
digest `3ec18097659f82f7...` and the sanitized sidecar hash
`06c81abb5a85e773...`. Every one of the 66 acquisitions records
`fixture: tabletop_cloth` from the renderer's own `run.json`, and the adapter
re-checks that field against the requested fixture on every fixation.

### The enumeration oracle, and exactly what crossed the boundary

The quarantined helper found **5 positive instance ids dynamically** — none is
written in any REAL-1 source — and emitted one row each, carrying **only** the
four whitelisted fields:

| id | label | seed yaw (deg) | seed pitch (deg) |
|---:|---|---:|---:|
| 141 | `rc1_cloth` | +0.113122 | +1.076153 |
| 142 | `rc1_table` | +0.000000 | −14.769199 |
| 143 | `rc1_wall` | +0.000000 | +0.000000 |
| 144 | `rc1_book_left` | −20.353229 | −1.082907 |
| 145 | `rc1_box_right` | +20.409883 | +0.416263 |

The sidecar's top-level keys are exactly `{schema, fixture,
fixture_truth_digest, fields_exposed, objects}` and every row's keys are exactly
the four; the run driver and the adapter each re-validate this independently and
abort otherwise. **No vertex, surface, depth, normal, range, mask, coverage or
extent value appears anywhere in the sidecar.**

The barrier was also checked structurally, not just by declaration: the
**transitive import closure of the observer process reaches 52 repository
modules and not one evaluator-side module** (`reality1_scene`, `reality1_eval`,
`reality2_eval`, `reality2b_eval` are all unreachable from
`fullscene_real1_run.py` and `fullscene_real1_repo_adapter.py`).

### Every object attempted, once

66 fixations, global steps **0..65, unique and contiguous** — no step repeated,
none rerendered, 66 Blender launches for 66 fixations.

| id | label | seed visible px | seed valid depth | fixations (steps) | termination | surfels | status |
|---:|---|---:|---:|---|---|---:|---|
| 141 | `rc1_cloth` | 65,536 | 62,203 (94.9%) | 24 (0..23) | `object_watchdog` | 151,446 | `WATCHDOG_REACHED_RETAIN_FOR_REVISIT` |
| 142 | `rc1_table` | 58,904 | 39,719 (67.4%) | 24 (24..47) | `object_watchdog` | 359,051 | `WATCHDOG_REACHED_RETAIN_FOR_REVISIT` |
| 143 | `rc1_wall` | **0** | **0** | 1 (48) | `seed_measurement_failed` | 0 | `NOT_VISIBLE_OR_NO_TARGET_SUPPORT` |
| 144 | `rc1_book_left` | 45,966 | 2,894 (6.3%) | 10 (49..58) | `no_frontier` | 4,317 | `ATTENTION_COMPLETE_MEASUREMENT_PARTIAL` |
| 145 | `rc1_box_right` | 57,700 | 3,859 (6.7%) | 7 (59..65) | `no_frontier` | 5,334 | `POLICY_EXHAUSTED_WITH_UNSEEN_TERRITORY` |

Two objects reached the 24-fixation watchdog. **The watchdog is an engineering
guardrail and reaching it is not a scientific stop** — both rows are marked
`scientific_stop_reached: false`, and 141/142 are explicitly retained for
revisit, not completed. Only 144 and 145 reached the frozen policy's own
`no_frontier` stop.

Empty looks behaved as inherited: 144 at steps 51–52 and 145 at steps 61–63
returned fewer than 100 target points, fused nothing, retained the observation
and continued.

### Object 143: a scaffold limitation, not a system failure

The wall's seed direction is its own centre, and **its own centre is occluded by
object 141**. This was measured before the run and reproduced by it: at gaze
(0.000, 0.000) the frame recovered depth on **94.0% of its pixels** — the stereo
front end worked normally — but **zero of those pixels belonged to 143**, so the
object had no support to seed from and was never instantiated. Meanwhile 143 is
the **largest object in the reference panorama at 41,453 pixels**, 38% of all
occupied reference pixels.

This is a property of the prescribed centre-direction seed rule, not of the
renderer, the stereo front end, FSG6f or fusion. It is recorded rather than
repaired: choosing a visible direction instead would require a new visibility
policy and fallback search that the contract does not define.

### The bounded handoff, twice, with different outcomes

Both `no_frontier` stops had exterior `NEVER_OBSERVED > 0`, so both took exactly
one epistemic handoff through the unchanged
`cyclopean1e_gaze.select_epistemic_probe`, then executed exactly one returned
local action. **Neither recursed** (`recursive_handoff: false`).

| | 144 | 145 |
|---|---|---|
| eligible exterior components | 1 | 1 |
| NEVER_OBSERVED shoreline cells | 6 | 86 |
| probe border depth (cells) | 5 | 20 |
| handoff gaze | (−24.1, −6.6) | (+21.7, +6.0) |
| handoff target points / new / matched | 572 / 119 / 453 | 2,417 / 418 / 1,999 |
| returned action gaze | (−19.1, −6.6) | (+16.7, +11.0) |
| action target points / new / matched | 1,733 / 152 / 1,581 | 785 / 70 / 715 |
| exterior NEVER_OBSERVED before → after | **6 → 0** | **86 → 61** |
| status before → after | `POLICY_EXHAUSTED_WITH_UNSEEN_TERRITORY` → `ATTENTION_COMPLETE_MEASUREMENT_PARTIAL` | unchanged |

**One bounded handoff fully discharged a small attention debt and only partly
discharged a larger one** (25 of 86 cells). That is the measured behaviour of
boundedness, not a threshold: nothing in the policy scales the number of actions
to the size of the debt, so the same single action closes 6 cells completely and
86 cells partially.

### Observer products, sealed before truth

`observer_complete.json` was written at 18:59:49 with `evaluator_truth_opened:
false`; the first evaluator product is dated 18:59:57. **The seal precedes every
reference product by 8 s**, and the post-seal reference tool refuses to run at
all without a sealed, truth-closed record (both refusals verified live, exit 1).

Combined observer geometry: **520,148 surfels** (141: 151,446; 142: 359,051;
143: 0; 144: 4,317; 145: 5,334) exported as `scene_points.npz` (5.3 MB) and
`scene_points.ply` (25.9 MB), plus per-object `objects/object_<id>.npz/.ply`
— including a genuinely empty, still-loadable map for 143 so the hole is
preserved rather than omitted.

Sparse spherical products at 2048×1024: `observer_depth.npy`,
`observer_instance.npy`, `observer_valid.png`, `observer_depth_preview.png`,
occupying **41,599 of 2,097,152 panorama pixels**.

Because the surfels carry the acquired left-eye linear RGB of the pixels they
came from, an RGB mosaic **is** genuinely constructible from images the observer
actually took, and is exported as `observer_acquisition_rgb_mosaic.png` with
`observer_rgb_reconstruction_claimed: false`. **It is an acquisition mosaic, not
an observer RGB reconstruction**, and it is exactly as sparse as the point cloud.

### Evaluator phase

`reference_rgb.png`, `reference_depth.npy`, `reference_instance.npy` at
2048×1024, 108,904 occupied pixels, all five instance ids present. Per object,
on the sparse spherical z-buffer:

| id | ref px | observer px | correct | coverage | purity | contamination | depth median | depth p95 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 141 | 13,257 | 12,446 | 12,446 | 0.9388 | **1.0000** | **0.0000** | 9.54 mm | 21.15 mm |
| 142 | 46,600 | 27,487 | 27,487 | 0.5898 | **1.0000** | **0.0000** | 26.02 mm | 196.19 mm |
| 143 | 41,453 | 0 | 0 | 0.0000 | — | — | — | — |
| 144 | 3,060 | 799 | 799 | 0.2611 | **1.0000** | **0.0000** | 43.87 mm | 82.87 mm |
| 145 | 4,534 | 867 | 867 | 0.1912 | **1.0000** | **0.0000** | 29.40 mm | 83.82 mm |

**Every instantiated object is perfectly pure: 1.0000 purity, 0.0000
contamination, zero mislabelled pixels anywhere.** The coverage preview shows
this directly — **no red and no yellow pixel exists in the image**, only green
agreement and grey reference-only.

Coverage here is a **sparse point-cloud z-buffer measure at 0.1°-scale panorama
resolution, not surface completeness**, and it is reported beside — never merged
with — the audit's own footprint counts and residues:

| id | support cells | raw support cells | attention residue (ext. NEVER_OBSERVED) | measurement residue (OBSERVED_TARGET_NO_DEPTH) |
|---:|---:|---:|---:|---:|
| 141 | 42,158 | 36,499 | 0 | 31 |
| 142 | 100,122 | 75,537 | 1,158 | 74 |
| 144 | 6,415 | 1,524 | 0 | 1,192 |
| 145 | 8,015 | 1,599 | 61 | 1,562 |

### Where the holes are, and why — three mechanisms, not one

Object 141 missed **811 of 13,257 reference pixels (6.12%)** in 97 components,
of which the two largest hold 61.4%. Measuring 5×5 luminance contrast on the
reference panorama separates them into genuinely different failures:

- **hole #2, 89 px, median contrast 0.000** — the flat red emblem disk. Nothing
  to match; a pure texture-starvation failure.
- **hole #1, 409 px, median contrast 1.170** against a covered-region median of
  **1.298** — essentially the same contrast as the surface that *was* recovered.
  **Local reference contrast does not explain this hole.** The mechanism is left
  open rather than assigned.
- **all remaining 313 px, median contrast 8.319** — far *above* the covered
  median. These are high-contrast edge pixels, the opposite regime from the
  emblem.

The other objects fail in a different shape entirely. 142 misses 41.0% across
**400 components** (largest 6,061 / 5,426 / 5,167) — distributed, consistent
with a watchdog stop part-way through coverage. 144 and 145 miss 73.9% and 80.9%
but in only **5 components each, one dominant** (1,729 and 3,588) — a single
contiguous unvisited region, i.e. attention/coverage debt, not scattered
measurement failure. Object 145's shoreline image shows exactly that: a fixation
spine with ribs, the gaps between ribs **orange-rimmed** (seen but unmeasured)
and only a thin red border (never observed).

For 142, coverage rises with reference contrast (0.3976 in the lowest quartile
to 0.6442 in the highest) and depth error rises steeply with range:

| range | n | median | p95 |
|---|---:|---:|---:|
| < 2.0 m | 12,939 | 15.19 mm | 41.73 mm |
| 2.0–2.5 m | 6,998 | 35.03 mm | 94.45 mm |
| 2.5–3.0 m | 4,668 | 74.90 mm | 212.03 mm |
| 3.0–4.0 m | 2,882 | 154.78 mm | 335.14 mm |

That range dependence is what the single 196 mm p95 figure for 142 is made of;
the table is a large surface viewed at a grazing angle, and its far end is the
worst-conditioned geometry in the scene. These are **diagnostics, separate and
uncombined** — `single_quality_score_synthesized: false`.

### Integrity

- `[fullscene-real1-check] SUMMARY passed=13 failed=0`, rc 0.
- **All twelve documented mutations exit 1** (`blend_input false_provenance
  hardcode oracle_import oracle_leak truth_early recursive reuse_maps touch_main
  score noresume noexports`); an unknown mutation exits 2.
- Two **live** seal negatives: the reference tool refuses a missing seal and a
  seal that is not truth-closed, both exit 1.
- **Every checker in the repository: 53/53 suites green, 331/331 prior negatives
  firing, none weakened.**
- **Frozen-source audit: all 329 tracked source files present at baseline
  `651a6cb` are byte-identical — 0 differing files, 0 diff lines.** The only
  changes are the three REAL-1 modules and the REAL-1 checker.
- `main` at `15eedee` and `fullscene-calibration-1` at `651a6cb` are untouched
  and match their remotes.

One inherited `RuntimeWarning` (NaN→int64 cast at
`cyclopean1a_topology.py:117-118`) appears during the audits. It was proved
harmless in earlier increments — `_indices` filters on an explicit `np.isfinite`
term — and the parent was not edited.

### ESTABLISHED

- REAL-1 runs end to end against the **live procedural fixture** with truthful
  provenance and no `.blend` claim.
- **All 5 benchmark objects were enumerated dynamically and attempted exactly
  once**, in ascending id order, with contiguous global steps and no rerender.
- The declassification boundary held: **only the four whitelisted fields
  crossed**, and no evaluator-side module is reachable from the observer process.
- The observer was **sealed before any evaluator truth was opened**, verified by
  ordering, by the seal's own `evaluator_truth_opened: false`, and by a live
  refusal when the seal is absent or not truth-closed.
- **Zero cross-object contamination**: purity 1.0000 and contamination 0.0000 on
  all four instantiated objects, with no red or yellow pixel in the coverage map.
- The **bounded handoff works and is genuinely bounded**: one probe, at most one
  returned action, no recursion — closing 6/6 cells for 144 and 25/86 for 145.
- **Depth agrees with truth at the 10–44 mm median level** on the four
  instantiated objects where both are valid, with a measured range dependence.
- Frozen machinery stayed frozen: **329 baseline sources, 0 diff lines**;
  53/53 suites and 331/331 negatives unchanged.

### NOT ESTABLISHED

- **No discovery claim.** Object identity and one seed direction are explicit
  oracle scaffolding. The benchmark does not test whether this system can find
  objects; `discovery_tested: false` is recorded in the manifest.
- **The watchdog is not success.** 141 and 142 stopped because they ran out of
  budget, not because the policy resolved them. Their 151,446 and 359,051
  surfels say nothing about whether those objects are complete.
- **Coverage is not completeness.** It is a sparse z-buffer pixel ratio at one
  panorama resolution; a denser panorama or a different footprint would move it.
  It is not a surface-completeness or accuracy claim.
- **Purity 1.0000 is not an accuracy claim.** It says the observer never
  attached a pixel to the wrong object, on the pixels it produced at all. It
  says nothing about the 59% of the reference the observer never covered.
- **Object 143's failure is scaffold, not system.** It does not show the system
  cannot reconstruct a wall; it shows the centre-direction seed rule can point
  at an occluder. Nothing here measures what the system would do from a visible
  wall direction.
- **The three hole mechanisms are described, not explained.** The 409-px hole is
  explicitly *not* accounted for by local reference contrast, and no single
  cause is assigned. No matcher, baseline, vergence or illumination was changed
  or tested.
- **One run, one seed, one fixture, fixed head, static scene.** Seed 2179 was not
  run; nothing here is a variance estimate.
- **No single score.** Coverage, purity, depth error, attention residue and
  measurement residue are kept separate deliberately and must not be combined.
