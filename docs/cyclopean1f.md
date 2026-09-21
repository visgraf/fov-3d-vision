# Cyclopean-1f — Iterate Epistemic Gaze

## Question

Cyclopean-1e established that one literal read-out of the refined perceptual field — `EXTERIOR + NEVER_OBSERVED -> deepest shoreline cell` — produced a useful fixation while ignoring `OBSERVED_TARGET_NO_DEPTH`.

Cyclopean-1f asks only:

> If exactly that rule is repeated without modification, does the observer reach a state with no eligible exterior `NEVER_OBSERVED` shoreline?

This is a convergence/fixed-point experiment for one seed, not a new controller design.

## Frozen mechanism

- parent: completed Cyclopean-1e, seed 2111;
- fixed head and static scene;
- same cyclopean chart and 0.1 degree grid;
- same support footprint derived from the frozen 12 mm FSG3 association radius;
- same Cyclopean-1d epistemic state definition;
- same Cyclopean-1e gaze selector;
- same Reality/FSG stereo path and 12 mm fusion;
- same Reality Check 2b empty-look semantics;
- no FSG6f ranking or stopping logic.

## Loop

At each iteration:

1. rebuild geometric and epistemic shoreline state from the cumulative map and completed observations;
2. select only `EXTERIOR` shoreline refined as `NEVER_OBSERVED`;
3. reuse the Cyclopean-1e deepest-border-distance selector unchanged;
4. acquire one fixation;
5. fuse target depth if available, otherwise retain the valid negative observation;
6. update the cyclopean field;
7. repeat.

Scientific stop:

`NO_ELIGIBLE_EXTERIOR_NEVER_OBSERVED`

The inherited total-24-fixation limit is reused only as an engineering watchdog. Reaching it is not scientific success.

## Deliberate exclusions

- `OBSERVED_TARGET_NO_DEPTH` never becomes an eligible gaze merely because geometry is missing there;
- no INTERNAL component is eligible;
- no minimum bay depth, area, gain, coverage, or accuracy threshold;
- no fixed number of scientific iterations;
- no mesh, morphology tuning, normal cue, texture threshold, new geometry tolerance, evaluator truth, or FSG6f modification.

## Interpretation

A successful scientific stop would establish only that this particular epistemic action rule reached its own fixed point on this record. It would not establish global object completeness, stereo accuracy, or convergence on other scenes/seeds.

## Results

Run 2026-09-21 on the workstation. **`CYCLOPEAN1F_COMPLETE`,
`structural_fails: []`, scientific stop
`NO_ELIGIBLE_EXTERIOR_NEVER_OBSERVED`.** The repeated Cyclopean-1e rule reached
its own fixed point in **two** added fixations - **17 total against the 24-look
watchdog**, so the watchdog was never approached. Structural only: **no coverage,
gain, depth or look-count number is a PASS gate, and none is proposed.**

### Provenance

Working tree clean. Prospective commit **`81fec0a`**; pre-1f parent **`8672bba`**.
The package adds **exactly seven files, all `A`**
(`tools/cyclopean1f_{public,loop,run,compare}.py`,
`tools/dev/check_cyclopean1f.py`, `docs/cyclopean1f.md`,
`docs/cyclopean1f-checks.md`). `git diff` against `8672bba` over **54 frozen
sources** - every FSG1/FSG3/FSG6f source, the renderer, scene, rig, pin file,
every Reality Check 1/2/2b source and **every Cyclopean-1a, 1b, 1c, 1d and 1e
source** - is **empty (0 lines)**, and all 54 sha256 are SAME. In particular the
Cyclopean-1e selector that 1f must reuse unchanged,
`tools/cyclopean1e_gaze.py`, is byte-identical at `a3599ea14fc00e60…`.

The parent was located **by manifest**: exactly one
`Cyclopean1e-epistemic-gaze-v1` record with seed 2111 and profile `full` exists,
`previews/cyclopean1e/full-seed2111`, carrying `truth_opened` false,
`fixed_head`/`static_scene` true, `added_fixations` 1 and
`parent_fixations_rerendered` 0. Its four pinned files hash identically **before
and after**:

| file | sha256 (before == after) |
|---|---|
| `prediction_manifest.json` | `d94c90ef97d173b0…a894df70` |
| `surface_map.npz` | `5dfef59dd8203cd3…062e492e` |
| `probe_patch.npz` | `eda539ae9a36684b…dd83515a` |
| `epistemic_after.png` | `16decefba9adb4a3…f99f978` |

The runner additionally asserts its own rebuild against the parent's published
fields before acquiring anything, and that guard passed: the reconstructed
initial state reproduces `exterior_never_observed_cells` **290** and
`max_exterior_never_observed_depth_cells` **142** exactly.

### Environment

Blender 5.2.1 LTS headless, Cycles, **OPTIX** on an RTX 4090 (driver 595.84);
host analysis under `.venv/bin/python` 3.12.3. The whole loop is **Interactive at
60.6 s wall**, including both Blender launches.

### Checks

`py_compile` clean on all five modules. The three prescribed lines appeared
verbatim:

```text
[cyclopean1f-loop] PASS repeated_rule=true never_observed_only=true exterior_only=true fixed_point=true watchdog_guardrail=true
[cyclopean1f-policy] PASS parent=cyclopean1e seed2111_only=true repeated_epistemic_gaze=true scientific_stop=no_eligible_never_observed watchdog_total=24 frozen_fsg6f=true quality_gated=false
[cyclopean1f-check] SUMMARY passed=6 failed=0
```

All six declared negatives exit 1: `nodepth`, `internal`, `threshold`, `quality`,
`fixedlooks`, `policy`. Every prior suite is green with its committed negative
set still firing, **61 prior negatives in total, none weakened**: cyclopean1e 6/6
(6/6), cyclopean1d 6/6 (6/6), cyclopean1c 6/6 (6/6), cyclopean1b 6/6 (6/6),
cyclopean1a 6/6 (6/6), reality2b 7/7 (10/10), reality1 6/6 (6/6), fsg6f 14/14
(15/15).

**One honest note about the strength of this step's controls, recorded because it
bears on how much the green line means.** The six `--negative` paths in
`tools/dev/check_cyclopean1f.py` print a FAIL line and exit 1 **unconditionally**
for any recognised name; they do not inject the named mutation into the real
selector or runner and then verify that the real code rejects it. That is weaker
than the negative sets in Cyclopean-1a through 1e, whose negatives genuinely
mutate behaviour and assert the production code detects it. The **positive**
checks, by contrast, were verified to be genuinely fail-capable: mutating a
scratch copy of the real sources made them fail, one condition at a time -
`"candidate_component_kind": "EXTERIOR"` → `"ANY"` gives
`[cyclopean1f-check] FAIL exterior_only`; replacing the imported selector gives
`FAIL iterates_same_rule`; rewriting the no-quality-gate clause gives
`FAIL no_quality_gate` - each exiting 1, with the unmutated copy returning to
`passed=6 failed=0`. So the invariants this step asserts are real and enforced on
the actual sources; the `--negative` flags are declarations rather than controls.
**Nothing was modified**, because this does not block the experiment and the
package is frozen by the prompt.

### The loop

Inherited chart **263 x 199**, grid **0.1 deg**, footprint **4 cells /
0.322236 deg**, starting map **146,996** surfels at **15** completed fixations.

**Step 15 - gaze (+1.3000, +4.2000)**

| | |
|---|---|
| selector | component **0**, kind **EXTERIOR**, state **NEVER_OBSERVED**, cell (y=130, x=142) |
| inherited border depth | **142** - the component maximum |
| eligible components / fallback rank | 1 / **0** |
| `observed_target_no_depth_eligible` | **false** |
| target points | **58,475** → **fused** |
| new / matched surfels | **3,298** / 55,177, `idempotent_replay` **true** |
| `NEVER_OBSERVED` | **290 → 142**, max depth **142 → 69** |
| support / complement / shoreline | 41,342 → 41,877 / 10,995 → 10,460 / 1,287 → 1,120 |
| `OBSERVED_TARGET_NO_DEPTH` | **28 → 28** |

**Step 16 - gaze (-6.0000, +4.2000)**

| | |
|---|---|
| selector | component **0**, kind **EXTERIOR**, state **NEVER_OBSERVED**, cell (y=130, x=69) |
| inherited border depth | **69** - again the component maximum |
| eligible components / fallback rank | 1 / **0** |
| `observed_target_no_depth_eligible` | **false** |
| target points | **50,010** → **fused** |
| new / matched surfels | **5,196** / 44,814, `idempotent_replay` **true** |
| `NEVER_OBSERVED` | **142 → 0**, max depth **69 → None** |
| support / complement / shoreline | 41,877 → 43,001 / 10,460 → 9,336 / 1,120 → 1,000 |
| `OBSERVED_TARGET_NO_DEPTH` | **28 → 28** |

Then the selector found no eligible cell and the loop stopped on
**`NO_ELIGIBLE_EXTERIOR_NEVER_OBSERVED`**. Neither look was empty, so the
Reality Check 2b negative-evidence branch was never exercised in this run - it
remains available and untested here.

Both fixations landed on chart row **y=130** at different yaw, which is what the
remaining structure was: a thin horizontal band rather than a deep pocket.

### Final state

| | initial | final |
|---|---|---|
| map points | 146,996 | **155,490** (+8,494, +5.78%) |
| multi-look surfels | 67,496 | **89,740** |
| support / complement | 41,342 / 10,995 | **43,001 / 9,336** |
| shoreline cells | 1,287 | **1,000** |
| exterior / internal components | 1 / 2 | 1 / 2 |
| **exterior `NEVER_OBSERVED`** | **290** | **0** |
| **max exterior `NEVER_OBSERVED` depth** | **142** | **None** |
| max exterior component depth | 142 | **22** |

Final refined census over the 527 base-`UNOBSERVED` shoreline cells:

| refined state | cells | exterior | internal |
|---|---|---|---|
| `NEVER_OBSERVED` | **0** | 0 | 0 |
| `OBSERVED_TARGET_NO_DEPTH` | **28** | 0 | **28** |
| `OBSERVED_TARGET_WITH_DEPTH` | 0 | 0 | 0 |
| `OBSERVED_NONTARGET_ONLY` | **423** | 423 | 0 |
| `MIXED_OBSERVATION` | 0 | 0 | 0 |
| `NO_RANGE_REFERENCE` | **76** | 72 | 4 |

Inherited base states at the fixed point: `UNOBSERVED` 527,
`TARGET_CONTINUATION` 0, `PHYSICAL_DEPTH_BREAK` 311, `AMBIGUOUS` 162, summing to
the 1,000 shoreline cells.

### The residual, described rather than fixed

At the fixed point nothing remains that this rule can act on, and the three
things that do remain are each non-actionable for a different reason:

- **`OBSERVED_TARGET_NO_DEPTH`, 28 cells, all internal** - the emblem residue,
  **unchanged through both iterations** and still the same two components,
  1 cell at **(+7.3000, -2.9000)** and 31 cells at **(+6.7903, -2.1484)**, the
  identical centroids Cyclopean-1c, 1d and 1e reported. It was excluded by
  construction and the loop never touched it;
- **`OBSERVED_NONTARGET_ONLY`, 423 cells, all exterior** - the object's own edge:
  imaged, with background beyond. Their exterior depth is shallow and ordinary,
  min 0, median 9, max 22, and the maximum depth of the whole exterior component
  fell from **142 to 22**, so no deep pocket survives anywhere;
- **`NO_RANGE_REFERENCE`, 76 cells** - all at distance **5.10 cells** (min =
  median = max) from the nearest raw target support, strictly beyond the
  inherited local-range disk radius `footprint_cells + 1 = 5`. The same
  deterministic artifact Cyclopean-1d measured, unchanged in character and
  **left unadjusted**, since widening that radius would be a new tolerance.

**No fix is proposed inside this run for any of them.**

### Geometry coherence, which is not accuracy

Evaluator truth stayed closed - no 1f source references `evaluation_only`,
`reality2b_eval` or a truth file - so nothing here is an accuracy claim.

- Both fixations were re-fused from their saved acquisitions at runner precision
  and reproduce the manifest exactly: target points **58,475** and **50,010**,
  new **3,298** and **5,196**, matched **55,177** and **44,814**, and
  `idempotent_replay` **true** for each, with the replayed cumulative total
  **8,494** equalling the map gain exactly;
- the replayed final map matches the saved one **exactly** in `support_count`,
  `provenance_mask` and `instance_id`; its `xyz_h` differs on 18,563 of 155,490
  rows by at most **121 nanometres**, which is **below one float32 ulp at 2.1 m
  (238 nm)** and within 4 ulp everywhere - accumulation-order rounding in the
  running average, not a semantic difference;
- target purity holds: final instance ids exactly **{141}**, and the non-target
  pixels each look saw (**39** and **78**, instance 143) were excluded from the
  patches by construction;
- fusing moved the **pre-existing** surfels by median **0.0000 mm**, p99
  **2.49 mm**, max **6.83 mm** - all well inside the frozen 12 mm radius, so two
  further looks did not drag the established surface;
- overlap agreement is high: **55,177 of 58,475** (**94.4%**) and **44,814 of
  50,010** (**89.6%**) of probe points associated with existing surfels within
  12 mm, so where the new looks overlapped known surface they agreed with it;
- the 8,494 new surfels span [2.0659, 2.2035] m against an old envelope of
  [2.0667, 2.2372] m. **Two** surfels fall outside it, by **0.73 mm** and
  **0.57 mm** below the old minimum - 0.5% of the cloth's 145.2 mm relief and far
  under the 12 mm association scale. There is no gross wrong-depth patch.

### Visual reading, descriptive

`epistemic_initial.png` shows the inherited state: a thin horizontal slot and a
step cut into the grey support, outlined in **red `NEVER_OBSERVED`**, with the
outer rim **cyan `OBSERVED_NONTARGET_ONLY`**, the lower edge **blue
`PHYSICAL_DEPTH_BREAK`**, and a small **orange crescent** middle-right.

`epistemic_final.png` is the picture of the fixed point: **all red is gone**. The
support is a single solid quadrilateral whose entire boundary is cyan and blue -
imaged edge and observed depth break - and **the orange crescent is still there,
unchanged and in exactly the same place**. The only thing left inside the object
is the one thing the rule was forbidden to chase.

`probe_rgb_fix_15.png` shows textured cloth with the printed blue band and a
sliver of the red emblem at the bottom (89.3% stereo validity);
`probe_rgb_fix_16.png` shows plainer cream weave with a grey band at the left
(76.4% validity, consistent with less texture). Both are genuine cloth.

A depth-coloured before/after view of the surfel map shows the same event in 3D:
the horizontal gap between the upper band and the lower body is replaced by a
continuous band whose depth colouring blends with the panels on either side, and
the small elliptical emblem hole stays open.

### Structural FAIL lines, and code fixes

**No structural FAIL line was produced anywhere**, and **no code fix was made**;
nothing outside the seven Cyclopean-1f files was modified.

The inherited `RuntimeWarning: invalid value encountered in cast` from
`cyclopean1a_topology.py:117-118` appears again - **34** occurrences when
rebuilding the cumulative evidence - and is recorded again as harmless. By
inspection `_indices` builds its `good` mask with an **explicit**
`np.isfinite(yaw) & np.isfinite(pitch)` term, so the cast's output for a
non-finite input is never used; by measurement, rebuilding the whole 1f evidence
with a NaN-prefiltered `_indices` raises **0** warnings and yields **bitwise
identical** `seen_target`, `seen_nontarget`, `target_range_m` and
`nontarget_range_m`. The non-finite angle pairs at the two new looks, **7,022**
and **15,448**, are exactly their invalid-pixel counts. It changes no
Cyclopean-1f number, so the parent source was correctly left alone.

### What this establishes, and what it does not

Established. **The repeated Cyclopean-1e rule terminates on its own condition.**
Applied unchanged, with no threshold, no tuned score and no FSG6f involvement, it
consumed the remaining eligible field in **two** looks and stopped because
`EXTERIOR NEVER_OBSERVED` was **empty**, not because a guardrail fired - 17 total
fixations against a 24 watchdog. **The exclusion held for the whole loop**:
`OBSERVED_TARGET_NO_DEPTH` stayed at 28 at every iteration and both internal
components are the same objects at the same centroids. **The deep structure is
gone**: maximum exterior penetration depth fell 142 → 22, and what remains is
ordinary rim. And the two looks were productive - 58,475 and 50,010 target
points, 8,494 new surfels, replay-idempotent, purity intact.

Not established. **This is one rule on one seed**, and the contract says so: a
scientific stop shows only that *this* epistemic action rule reached *its own*
fixed point on *this* record. **It is not object completeness** - 527 shoreline
cells remain base-`UNOBSERVED`, 423 of them imaged-with-background and 28
seen-but-unmeasurable. **It is not accuracy**: evaluator truth stayed closed, so
coherence diagnostics are internal consistency and nothing more. **It says
nothing about other seeds or scenes**, and nothing about whether the rule would
terminate where the geometry is less benign. **The empty-look branch was never
exercised**, since both fixations were rich. And **`OBSERVED_TARGET_NO_DEPTH`
remains exactly where Cyclopean-1d left it** - the loop's success is precisely a
success at avoiding it, so the question of what action, if any, belongs to a
region the instrument cannot measure is untouched by this run.
