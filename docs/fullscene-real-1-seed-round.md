# FullScene-REAL-1S — one-round visible-seed recovery

Question: when a benchmark object's oracle centre direction is occluded, can one bounded prediction-side survey on the established 5-degree lattice recover a usable seed without evaluator geometry?

This experiment consumes the completed REAL-1 baseline only. It dynamically selects baseline rows with `NOT_VISIBLE_OR_NO_TARGET_SUPPORT`. For each such row it renders exactly the eight neighbors of the failed centre on a 5-degree Moore ring. All eight are rendered before selection. The winner is chosen by target valid-depth count, then target-visible pixels, then fixed ring order. If observer-side valid target depth exists, the same winning observation is reused with the established selected-object seed extraction/purity semantics.

There is no second ring, radius expansion, extra seed render, growth, audit, handoff, revisit, scheduler, or truth access. A failure after the ring is a valid experimental outcome.

The experiment does not test discovery: object identity and the original centre direction remain the same explicit REAL-1 oracle scaffold.

## Results

**COMPLETE 2026-09-23 on branch `fullscene-real-1`** (`[real1-seed-round] COMPLETE
{"targets": 1, "probes": 8}`; comparator prints
`FULLSCENE_REAL1_SEED_ROUND_COMPLETE structural_fails: []` and exits 0). Record:
`previews/fullscene-real1-seed-round1/full-seed2111`, seed 2111, profile `full`,
OPTIX, Blender 5.2.1 LTS. Baseline input `previews/fullscene-real1/full-seed2111`
at REAL-1 result commit `f49ec8e`.

**The headline is a negative result that the round's own criteria could not
see.** One ring did find the object and did produce a patch that passes every
established purity check — and every point in that patch is roughly 1.25 m
wrong.

### Target selected dynamically

Filtering the baseline status table for `NOT_VISIBLE_OR_NO_TARGET_SUPPORT`
returned **exactly one row: object 143, label `rc1_wall`**, whose failed
baseline seed gaze was **(0.000, 0.000)** — the object's own oracle centre,
which REAL-1 measured to be occluded by object 141. No scene id is written in
any seed-round source; the id arrives from the baseline row.

### All eight probes, rendered before any selection

Eight Moore-neighbour offsets on the established 5° lattice, global steps
**66..73** continuing the baseline's 0..65. Eight Blender launches for eight
probes, asserted equal in the manifest.

| ring | offset | gaze (yaw, pitch) | step | target visible px | target valid depth | frame valid |
|---:|---|---|---:|---:|---:|---:|
| 0 | (−5, −5) | (−5.00, −5.00) | 66 | 17,226 | 6,055 | 0.7286 |
| **1** | **(0, −5)** | **(0.00, −5.00)** | **67** | **13,758** | **6,169** | 0.7959 |
| 2 | (+5, −5) | (+5.00, −5.00) | 68 | 10,428 | 4,119 | 0.7730 |
| 3 | (−5, 0) | (−5.00, 0.00) | 69 | 1,025 | 27 | 0.8800 |
| 4 | (+5, 0) | (+5.00, 0.00) | 70 | **0** | **0** | 0.9131 |
| 5 | (−5, +5) | (−5.00, +5.00) | 71 | 6,996 | 70 | 0.7878 |
| 6 | (0, +5) | (0.00, +5.00) | 72 | 6,469 | 39 | 0.8373 |
| 7 | (+5, +5) | (+5.00, +5.00) | 73 | 9,167 | 122 | 0.7979 |

**Seven of eight probes saw the object at all** — a 5° step is enough to clear
the occluder from a centre that showed zero target pixels. Only (+5, 0)
remained fully occluded.

There is a sharp asymmetry the ring exposes: the three **downward** probes
recovered 4,119–6,169 valid points, while the three **upward** probes saw
comparable numbers of wall pixels (6,469–9,167) but recovered only **39–122**.
Below the cloth the wall is a narrow band bounded by the cloth edge and the
table; above it the wall is open, uniform expanse.

### Deterministic winner

Ranked by target valid-depth count, then target-visible pixels, then ring
order: **ring 1, gaze (0.000, −5.000), 6,169 valid of 13,758 visible (44.8%
recovery)**. No tie-break was needed. The ranking used only observer-side
instance support and stereo validity; no reference panorama, evaluator geometry
or depth was read — the seed-round process closure reaches 14 repository
modules and no evaluator-side module, and no `reference_*` artifact is named
anywhere in its sources.

### A pure seed was materialized — and it is metrically false

The winning observation was **reused, not re-rendered**
(`rendered_new_fixation: false`, `extra_seed_renders: 0`, exactly 8
acquisitions on disk). Applying the FullScene-1b extraction verbatim gave
**6,169 points, `seed_patch_pure: true`**, range 2.025 / 2.141 / 2.431 m
(min/median/max). It satisfies the frozen 100-point `initialize()` minimum,
which is **reported as a fact and not applied as a gate**; no map was
initialized and no growth started.

**Observer-side evidence alone says something is wrong.** The recovered wall
points sit at median **2.141 m**. The baseline's own object-141 map — the
cloth that occludes the wall — has median range **2.136 m**. The wall must be
*behind* the cloth, yet the recovered wall is at the cloth's depth. Worse, the
instrument's own vergence distance is **2.1 m**, a known setting and not truth:
the recovered median is **41 mm from the vergence plane**, and **89.5% of the
recovered points lie within ±150 mm of it**.

A post-hoc check against the REAL-1 sealed reference — run after the round was
written to disk, influencing nothing — confirms it:

- **all 6,169 points are directionally correct**: along every one of their
  directions the wall genuinely is the first hit;
- the true range along those directions is **3.380 / 3.393 / 3.421 m**;
- **median absolute error 1,251 mm, p95 1,326 mm**;
- **0 of 6,169 points — 0.00% — lie within 50 mm of the true surface.**

The mechanism is visible in the probe image: between the cloth and the table
the wall is a **completely featureless grey band** (the Reality-1 "quiet wall",
0.60 + 0.012·noise). With nothing to match, the stereo front end returns
disparities at the vergence plane; the oracle first-hit mask then labels those
pixels 143 because the left eye's first hit really is the wall. The result is a
dense, confident-looking, label-pure, metrically false patch.

### Quantity was anti-correlated with correctness

Post-hoc, per probe (again: did not influence the round):

| ring | gaze | valid pts | observer median | true median | median abs err | within 50 mm |
|---:|---|---:|---:|---:|---:|---|
| 0 | (−5, −5) | 6,055 | 2.173 m | 3.406 m | 1,234.7 mm | 0 (0.00%) |
| **1 (winner)** | **(0, −5)** | **6,169** | **2.141 m** | **3.393 m** | **1,251.0 mm** | **0 (0.00%)** |
| 2 | (+5, −5) | 4,119 | 2.156 m | 3.396 m | 1,243.0 mm | 32 (0.78%) |
| 3 | (−5, 0) | 27 | 2.163 m | 3.433 m | 1,265.2 mm | 0 (0.00%) |
| 5 | (−5, +5) | 70 | 2.177 m | 3.423 m | 1,262.0 mm | 4 (5.71%) |
| 6 | (0, +5) | 39 | 2.164 m | 3.411 m | 1,242.3 mm | 0 (0.00%) |
| 7 | (+5, +5) | **122** | **3.083 m** | 3.432 m | **322.3 mm** | **14 (11.48%)** |

**The prescribed quantity-first rule selected the worst probe available.** Ring
7 has 50× fewer points than the winner but a **4× smaller error** and the only
non-trivial fraction near the true surface. Its 122 points lie in a thin wall
sliver at the cloth's upper edge, where a real depth discontinuity gives the
matcher something to lock onto. Where the wall abuts structure it is measured;
in open uniform expanse it is invented at the vergence plane.

### Integrity

- Branch `fullscene-real-1` clean throughout; `main` `15eedee` and
  `fullscene-calibration-1` `651a6cb` untouched and matching their remotes.
- Baseline sealed and verified before use (`observer_sealed: true`,
  `observer_sealed_before_truth: true`, `structural_fails: []`, seed 2111).
- **Baseline immutable: all 767 files in the baseline record re-hashed after the
  round are byte-identical**, digest-of-digests
  `76ad8b411a9e48ab...` before and after. The run's own in-process check pinned
  18 artifacts including every per-object map and reported
  `baseline_files_changed: 0`. The four `reference_*` products and
  `observer_complete.json` are inside that 767 and unchanged.
- `py_compile` clean on all five seed-round modules.
- `[real1-seed-round-check] SUMMARY passed=8 failed=0`, rc 0.
- **All eight mutations exit 1** with named detectors: `hardcode`→
  `dynamic_target`, `secondring`/`earlystop`→`bounded_round`, `truth`→
  `truth_quarantine`, `growth`→`no_growth`, `threshold`→`no_threshold`,
  `baseline`→`baseline_readonly`, `extraseed`→`reuse_probe`. An unknown
  mutation exits 2.
- REAL-1's own checker still `passed=13 failed=0` and all twelve of its
  mutations still exit 1; the REAL-1 comparator on the baseline still exits 0.
- **54/54 suites green, 331/331 prior negatives firing, none weakened.**
- **Frozen-source audit: 337 tracked sources at `f49ec8e` and 329 at `651a6cb`
  are byte-identical — 0 differing.** Only the two new seed-round seam files
  were completed.
- No growth, audit, handoff, second ring, radius expansion, revisit, scheduler
  or scene update: `growth_actions: 0`, `audit_actions: 0`,
  `handoff_actions: 0`, `truth_opened: false`, and the output tree contains
  **zero** map/growth/audit/handoff/reference artifacts.

### ESTABLISHED

- **One 5° ring is enough to clear this occluder geometrically.** Seven of eight
  neighbours saw a centre-occluded object that showed zero target pixels at its
  own centre; only one remained fully occluded.
- The round is **bounded exactly as specified**: 8 probes, all rendered before
  selection, one deterministic winner, the same observation reused as the seed,
  no ninth render, and nothing after it.
- **The baseline was pure input**: 767 files byte-identical, verified twice.
- The declassification discipline held: selection used only observer-side
  instance support and stereo validity, with no evaluator module reachable.
- **A visible direction is not a usable seed.** The winner produced 6,169
  label-pure points of which **0.00% are within 50 mm of the true surface**,
  median error **1,251 mm**.
- **An observer-side red flag existed and the prescribed rule ignored it**: the
  recovered depth piles up at the instrument's own 2.1 m vergence plane (median
  41 mm from it, 89.5% within ±150 mm) and coincides with the occluder's
  measured depth — both knowable without truth.
- **Ranking by valid-depth count is anti-correlated with correctness here.** The
  probe with 50× fewer points had 4× lower error and the only meaningful
  near-surface fraction.

### NOT ESTABLISHED

- **This is not a recovery success.** `recovery_status: RECOVERED_SEED` is
  correct under the round's own truth-free criteria and wrong as physics. The
  round's criteria cannot distinguish the two.
- **No claim that a vergence-plane guard would fix it.** The pile-up is
  measured; no such test was implemented, tuned or validated, and inventing one
  is outside this round's contract.
- **No claim about the general occluded-seed case.** One object, one occluder,
  one ring radius, one lattice step, one seed, one fixture, fixed head. Whether
  a 5° ring generally clears occluders is not tested by n = 1.
- **No claim that the wall is unreconstructable.** Ring 7 recovered 11.48% of
  its points within 50 mm, so structure-adjacent wall *is* measurable; nothing
  here tests a matcher, baseline, vergence or illumination change.
- **No discovery claim.** Object identity and the original centre direction
  remain the same explicit REAL-1 oracle scaffold.
- **The seed was not used.** No map initialized, no growth, no audit, no
  handoff, and the REAL-1 scene inventory still records 143 as
  `NOT_VISIBLE_OR_NO_TARGET_SUPPORT`.
