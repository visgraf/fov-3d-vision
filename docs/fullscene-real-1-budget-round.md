# FullScene-REAL-1W — one-round watchdog continuation

Question: when the 24-fixation engineering watchdog interrupts an object while frozen FSG6f still wants to continue, how much progress does one additional bounded block buy?

Dynamically select completed REAL-1 objects with `WATCHDOG_REACHED_RETAIN_FOR_REVISIT`. Resume each object's saved final map and local history, replay its last policy state exactly, and execute at most **6 fresh local fixations**: one additional quarter of the original 24-fixation guardrail. Stop earlier only if frozen FSG6f reaches its own scientific stop.

This six-look block is a diagnostic intervention, not a new budget rule. There is no second block, no re-seed, no handoff, no adaptive scaling, and no productivity gate. After the block, run the established read-only epistemic audit. Only after a continuation seal may a separate evaluator compare baseline vs continued geometry against the immutable REAL-1 reference products.

Report attention, geometry, coverage, depth error, and control changes separately. Do not fit a budget formula or synthesize a score from this one round.

## Results

**COMPLETE 2026-09-23 on branch `fullscene-real-1`** (`[real1-budget-round]
COMPLETE {"targets": 2, "fresh_fixations": 6}`; comparator prints
`FULLSCENE_REAL1_BUDGET_ROUND_COMPLETE structural_fails: []` and exits 0).
Record `previews/fullscene-real1-budget-round1/full-seed2111`, seed 2111,
profile `full`, OPTIX, Blender 5.2.1 LTS. Baseline input
`previews/fullscene-real1/full-seed2111` at REAL-1 result commit `f49ec8e`.
No data from the REAL-1S seed-recovery round entered this experiment; the seam
refuses such a path outright (verified live).

**The short answer: the watchdog had interrupted both objects only three looks
short of their own stopping point — and reaching that stopping point bought one
object a real coverage gain and the other almost nothing.**

### Targets selected dynamically

Filtering the baseline status table for `WATCHDOG_REACHED_RETAIN_FOR_REVISIT`
returned **two rows: 141 `rc1_cloth` and 142 `rc1_table`**. No scene id appears
in any budget-round source.

Both resumed from their **saved final REAL-1 map** (`objects/object_141.npz`,
`objects/object_142.npz`) with `reseeded: false` and
`historical_rerenders: 0`. Object-local history was rebuilt by **re-reading**
the 24 saved acquisitions each from disk — read-only, no render, and the map was
never re-fused from history.

### Saved final decision reproduced exactly, before any fresh render

Both saved decisions were `stop=false, reason=continue`: FSG6f genuinely still
wanted to continue when the guardrail fired. Each was reproduced through the
unchanged `multiobject3f_audit._exact_decision_replay` across all ten exact
fields plus the next gaze, **before a single new pixel was rendered**.

| | 141 | 142 |
|---|---|---|
| saved `stop` / `reason` | false / `continue` | false / `continue` |
| `frontier_voxel_count` | 2,443 | 28,845 |
| `frontier_count` / `raw` | 197 / 197 | 1,582 / 1,582 |
| `map_resolved` / `boundary_resolved` | 1 / 149 | 81 / 363 |
| **`frontier_open_count`** | **47** | **1,138** |
| candidates before consensus | 2 | 3 |
| consensus-rejected | 0 | 0 |
| saved next gaze | (+0.113, +6.076) | (−10.000, −14.769) |
| **replay exact** | **true** | **true** |

### The block: 3 of 6 looks each, then the policy's own stop

| object | fresh looks | steps | termination | scientific stop | block exhausted |
|---|---:|---|---|---|---|
| 141 | **3 / 6** | 66, 67, 68 | `no_frontier` | **true** | false |
| 142 | **3 / 6** | 69, 70, 71 | `no_frontier` | **true** | false |

6 Blender launches for 6 fresh fixations, asserted equal. No empty looks.

| object | step | gaze | target visible | valid depth | recovery | matched | **new** | map after |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| 141 | 66 | (+0.113, +6.076) | 53,128 | 49,374 | 0.929 | 49,329 | **45** | 151,491 |
| 141 | 67 | (+5.113, +6.076) | 50,394 | 46,719 | 0.927 | 42,408 | **4,311** | 155,802 |
| 141 | 68 | (+5.113, +1.076) | 65,536 | 59,929 | 0.914 | 59,752 | **177** | 155,979 |
| 142 | 69 | (−10.000, −14.769) | 60,223 | 42,134 | 0.700 | 39,675 | **2,459** | 361,510 |
| 142 | 70 | (−15.000, −14.769) | 61,856 | 42,274 | 0.683 | 39,289 | **2,985** | 364,495 |
| 142 | 71 | (−20.000, −14.769) | 64,236 | 44,033 | 0.685 | 41,349 | **2,684** | 367,179 |

Most of the continuation's measurement effort was **re-measurement**: across the
block 141 fused 4,533 new against 151,489 matched (**2.9% new**) and 142 fused
8,128 new against 120,313 matched (**6.3% new**). Look 66 is the extreme case —
49,374 valid target points producing **45 new surfels**.

### Both stops say `no_frontier`. They are not the same stop.

| | 141 | 142 |
|---|---:|---:|
| `frontier_open_count` before → after | 47 → **122** | 1,138 → **1,048** |
| candidates before consensus | 2 → **3** | 3 → **0** |
| consensus-rejected | 0 → **3** | 0 → **0** |

**Object 141 stopped with its open frontier having grown 2.6×, because all
three candidates it generated were rejected by the OPEN-majority consensus
rule. Object 142 stopped because it generated no candidates at all.** Same
label, two different mechanisms, and in neither case does `no_frontier` mean the
frontier is empty — 141 ended with 122 open entries and 142 with 1,048.

This reproduces at scene scale the distinction MultiObject-3d and FullScene-1d
drew for single objects, now under a budget intervention rather than a natural
stop.

### Post-round epistemic audit (read-only; `audit_triggered_action: false`)

27 observations each (24 baseline + 3 fresh).

| | 141 | 142 |
|---|---|---|
| chart | 263×199 @ 0.1°, footprint 4 — **identical to baseline** | 666×183 fp 4 → **664×181 fp 3 — changed** |
| raw support cells | 36,499 → 37,726 (**+1,227**) | 75,537 → 75,793 (**+256**) |
| support cells | 42,158 → 42,951 (**+793**) | 100,122 → 98,180 (**−1,942**) |
| shoreline cells | 1,017 | 2,438 |
| **attention residue** (ext. `NEVER_OBSERVED`) | 0 → 0 (**+0**) | 1,158 → 1,033 (**−125**) |
| **measurement residue** (`OBSERVED_TARGET_NO_DEPTH`) | 31 → 32 (**+1**) | 74 → 284 (**+210**) |

**Object 142's support-cell decrease is not a loss of measured surface and must
not be read as one.** The audit chart is rebuilt from the map's own angular
extent, and 142's footprint radius fell from 4 cells to 3 because the footprint
is `atan(0.012 / median_range)` and the median range moved. Each surfel
therefore paints a smaller disk on a slightly different grid. For 142 the
like-for-like measures are `raw_support_cells` (+256) and the fixed-grid
panorama coverage below; for 141 the chart is bit-identical, so its +793 is a
clean like-for-like gain.

The shoreline images show the two situations plainly. **141 is near-solid grey
with a teal rim, no red anywhere** (attention residue 0) and a single small
orange arc — the flat emblem REAL-1 already identified as zero-contrast, still
unmeasured after three more looks. **142 retains a red border along its left,
right and bottom edges** — the 1,033 never-observed cells the policy declined to
act on — with orange measurement speckle across the slab.

### Post-seal evaluation against the immutable REAL-1 reference

The continuation seal was written first (`truth_opened_before_seal: false`);
only then were the reference arrays read. The evaluator refuses to run without a
truth-closed seal (verified live). Panoramas were rebuilt twice on the fixed
2048×1024 grid — baseline maps throughout, and continued maps substituted only
for the two targets — and `non_target_objects_unchanged: true`.

| object | ref px | observer px | correct px | coverage | purity | contam. | depth median | depth p95 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 141 baseline | 13,257 | 12,446 | 12,446 | 0.9388 | 1.0000 | 0.0000 | 9.54 mm | 21.15 mm |
| **141 continued** | 13,257 | 12,854 | 12,854 | **0.9696** | 1.0000 | 0.0000 | 9.78 mm | 22.10 mm |
| delta | — | +408 | +408 | **+0.0308** | +0.0000 | — | **+0.24 mm** | **+0.94 mm** |
| 142 baseline | 46,600 | 27,487 | 27,487 | 0.5898 | 1.0000 | 0.0000 | 26.02 mm | 196.19 mm |
| **142 continued** | 46,600 | 27,527 | 27,527 | **0.5907** | 1.0000 | 0.0000 | 26.93 mm | 203.96 mm |
| delta | — | +40 | +40 | **+0.0009** | +0.0000 | — | **+0.91 mm** | **+7.76 mm** |

Three things stand out, and they are reported separately by design:

1. **The same three-look intervention bought wildly different coverage.** 141
   gained **3.08 coverage points**; 142 gained **0.09** — and 142 did so while
   adding *more* surfels (8,128 vs 4,533). Geometric growth and coverage growth
   are not the same quantity: 142's 8,128 new surfels produced **+40** correct
   panorama pixels.
2. **Depth error got slightly worse for both**, in median and p95. The surface
   added late sits at the periphery, at grazing angles and longer range — the
   regime REAL-1 already measured as the worst-conditioned.
3. **Purity stayed exactly 1.0000 and contamination exactly 0.0000** for both.
   The extra budget bought no contamination.

No score was synthesized and no budget formula was fitted
(`score_synthesized: false`, `budget_formula_fitted: false`).

### Integrity

- Branch `fullscene-real-1` clean throughout; `main` `15eedee` and
  `fullscene-calibration-1` `651a6cb` untouched and matching their remotes.
- **Baseline immutable: all 767 files re-hashed after the round are
  byte-identical** (digest-of-digests `76ad8b411a9e48ab...` before and after).
  The run's own pin covered 28 artifacts — every per-object map, every object
  checkpoint and the four `reference_*` products — with
  `baseline_files_changed: 0`.
- **REAL-1S data excluded**: `load_baseline()` refuses any path containing a
  seed-round or budget-round marker; verified live against the actual REAL-1S
  output directory.
- `py_compile` clean on all five budget-round modules.
- `[real1-budget-round-check] SUMMARY passed=9 failed=0`, rc 0.
- **All nine mutations exit 1** with named detectors: `hardcode`→
  `dynamic_targets`, `twelve`→`quarter_round`, `secondblock`→`one_block`,
  `policy`→`frozen_control`, `handoff`→`no_handoff`, `auditaction`→
  `audit_readonly`, `truth`→`truth_barrier`, `score`→`no_score_formula`,
  `baseline`→`baseline_readonly`. Unknown exits 2.
- Two live seal negatives exit as refusals: evaluator products before the seal
  exists, and with a seal that is not truth-closed.
- **55/55 suites green, 331/331 prior negatives firing, none weakened.**
- **Frozen-source audit: 337 tracked sources at `f49ec8e` and 342 at `f1a2ae7`
  are byte-identical — 0 differing.** Only the two new budget-round seam files
  were completed.
- `handoff_actions: 0`, `returned_handoff_actions: 0`, `second_block: false`,
  `adaptive_budget_rule_used: false`, `reseeded: false`,
  `historical_rerenders: 0`, `truth_opened_before_seal: false`,
  `blender_launches: 6`.

### ESTABLISHED

- **The watchdog fired three looks early for both objects.** Each reached frozen
  FSG6f's own `no_frontier` stop after 3 of the 6 allotted fresh fixations; the
  block was never exhausted.
- **The saved final decision reproduced exactly** for both objects across all
  ten exact fields and the next gaze, before any fresh render, from the saved
  map and re-read history alone.
- **`no_frontier` is still not one state.** 141 stopped with its open count
  *risen* 47→122 and all three candidates consensus-rejected; 142 stopped with
  1,048 open and zero candidates generated.
- **Continuation is dominated by re-measurement**: 2.9% and 6.3% of fused points
  were new, with one look producing 45 new surfels from 49,374 valid points.
- **Geometric growth and coverage growth are different quantities.** 142 added
  nearly twice as many surfels as 141 and gained 34× less coverage.
- **The extra budget cost a little depth accuracy** — both objects' median and
  p95 error rose — while **purity stayed exactly 1.0000 and contamination
  exactly 0.0000**.
- The round is bounded exactly as specified and the baseline was pure input.

### NOT ESTABLISHED

- **No budget rule.** One block, one size, two objects, one seed, one fixture.
  Nothing here licenses "24 should have been 27", and no formula was fitted.
- **`no_frontier` after continuation is not completeness.** 141 ended with 122
  open frontier entries and 32 unmeasured shoreline cells; 142 ended with 1,048
  open and **1,033 never-observed** cells. Both still carry debt.
- **142's support-cell decrease is not surface loss** — its chart origin,
  extent and footprint radius all changed, so that delta is not like-for-like.
  Only `raw_support_cells` and the fixed-grid coverage are comparable for it.
- **The slightly worse depth error is an observation, not a law.** It is
  consistent with late surface being peripheral, but no test isolated that
  cause, and n = 2.
- **Nothing about why the consensus rule rejected 141's candidates**, or why 142
  generated none. The counts are recorded; the mechanism was not opened.
- **No claim that more looks would help either object.** 141's remaining hole is
  the zero-contrast emblem, a measurement limit budget cannot address; 142's is
  a large attention debt the policy declined to act on.
- **No score, no productivity metric, no combined figure.** Attention,
  measurement, geometry, coverage, depth error and control state stay separate.
