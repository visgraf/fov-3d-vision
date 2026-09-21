# Cyclopean-1e — Epistemic Gaze

## Question

Cyclopean-1d split the old `UNOBSERVED` shoreline into distinct epistemic causes.  On seed 2111, the residual internal cells with a usable range reference were all `OBSERVED_TARGET_NO_DEPTH`, while the remaining deep exterior slot was one `NEVER_OBSERVED` arc.  Cyclopean-1e asks one deliberately small question:

> If the refined state is allowed to choose exactly one new fixation from genuinely `NEVER_OBSERVED` exterior shoreline, does it aim a useful look while ignoring the already-seen/no-depth residue?

## Frozen context

The experiment uses seed 2111 only.  Scene, fixed head, stereo path, fusion, chart, 0.1 degree full-profile grid, 12 mm association radius, object id, empty-look semantics, and every FSG6f source remain frozen.  Cyclopean-1d is the direct parent and is read only.

## Candidate entity

Only cells satisfying all three conditions are eligible:

1. they lie on the current shoreline;
2. their complement component is `EXTERIOR`;
3. Cyclopean-1d refines them as `NEVER_OBSERVED`.

In particular, `OBSERVED_TARGET_NO_DEPTH` is not a candidate for an identical blind repeat.

## Selection

No threshold or learned/tuned score is added.  Among eligible exterior components, choose the one whose `NEVER_OBSERVED` shoreline reaches the greatest inherited exterior border distance.  Within it, select the deepest `NEVER_OBSERVED` shoreline cell.  Ties use distance to the tied plateau centroid and then raster order.  A previously visited gaze is skipped using that same deterministic ordering.

Thus the action is the literal read-out

`refined epistemic state -> deepest genuinely unseen exterior shoreline -> one foveation`.

## Acquisition

Exactly one fixation may be added.  It is rendered through the existing Reality Check fixation path and processed by the frozen stereo pipeline.  Target depth is fused through the frozen 12 mm FSG3 association rule.  If the fixation contains fewer than the inherited minimum target points, it remains a valid empty/negative observation under the Reality Check 2b contract and fuses nothing.

The new observation is then added to the spherical evidence, the geometric shoreline is rebuilt, and the Cyclopean-1d observation-versus-measurement refinement is recomputed on the updated map.

## What is measured

The report records, without a quality gate:

- selected gaze and inherited border depth;
- whether the look contains target points;
- new and matched surfels;
- idempotent replay;
- map point count before/after;
- complement/support/shoreline structure;
- refined state counts before/after;
- number and maximum depth of exterior `NEVER_OBSERVED` shoreline cells.

No evaluator truth is opened, so internal coherence is not an accuracy claim.

## Non-goals

Cyclopean-1e does not change stopping, does not call FSG6f, does not introduce a repeated epistemic loop, does not solve low-texture stereo, and does not decide what alternate instrument action should follow `OBSERVED_TARGET_NO_DEPTH`.  It tests exactly one consequence of refined entities: whether they can simplify the next action.

## Results

Run 2026-09-21 on the workstation. **`CYCLOPEAN1E_COMPLETE`,
`structural_fails: []`.** Exactly one fixation was added, no parent fixation was
rerendered, and the Cyclopean-1d parent is byte-identical afterwards. Structural
only: **no surfel gain, coverage figure or depth change is a PASS threshold, and
none is proposed.**

### Provenance

Working tree clean. Prospective commit **`7d932d8`**; the pre-1e parent is
**`23b36d6`**. The package adds **exactly seven files, all `A`**
(`tools/cyclopean1e_{public,gaze,probe,compare}.py`,
`tools/dev/check_cyclopean1e.py`, `docs/cyclopean1e.md`,
`docs/cyclopean1e-checks.md`). `git diff` against `23b36d6` over **49 frozen
sources** - every FSG1/FSG3/FSG6f source, the renderer, scene, rig, pin file,
every Reality Check 1/2/2b source and **every Cyclopean-1a, 1b, 1c and 1d
source** - is **empty (0 lines)**, and all 49 sha256 are SAME.

The parent was located **by schema**, not by remembered path: exactly one
`Cyclopean1d-observation-measurement-audit-v1` record with seed 2111 and profile
`full` exists, `previews/cyclopean1d/full-seed2111`, carrying `truth_opened`
false, `fixed_head`/`static_scene` true, `acquisitions_added` 0,
`parent_files_modified` false and `observation_count` 14. Its three pinned files
hash identically **before and after**:

| file | sha256 (before == after) |
|---|---|
| `prediction_manifest.json` | `4ce0c102f9952595…c33bbdf5` |
| `observation_measurement_report.json` | `d4332b7b002a94fc…6148f7bd` |
| `epistemic_shoreline.png` | `dfd3acb622c740b0…308ef827` |

The Cyclopean-1c ancestor is also unchanged: `surface_map.npz`
`66adebea5ece578f…`, `prediction_manifest.json` `fb4e250959288019…`.

### Environment

Blender 5.2.1 LTS headless, Cycles, **OPTIX** on an RTX 4090 (driver 595.84);
host analysis under `.venv/bin/python` 3.12.3. The whole increment is
**Interactive at 33.2 s wall**, including the single Blender launch.

### Checks

`py_compile` clean on all five modules. The three prescribed lines appeared
verbatim:

```text
[cyclopean1e-gaze] PASS never_observed_only=true internal_excluded=true no_depth_excluded=true exterior_deepest=true revisit_fallback=true one_probe=true
[cyclopean1e-policy] PASS parent=cyclopean1d seed2111_only=true never_observed_only=true seen_no_depth_excluded=true one_fixation_max=true frozen_fsg6f=true quality_gated=false
[cyclopean1e-check] SUMMARY passed=6 failed=0
```

All six deliberate negatives exit 1: `nodepth`, `internal`, `centroid`,
`multiprobe`, `truth`, `policy`. Every prior suite is green with its committed
negative set still firing, **55 prior negatives in total, none weakened**:
cyclopean1d 6/6 (6/6), cyclopean1c 6/6 (6/6), cyclopean1b 6/6 (6/6),
cyclopean1a 6/6 (6/6), reality2b 7/7 (10/10), reality1 6/6 (6/6),
fsg6f 14/14 (15/15).

### The selection, derived before rendering

The inherited chart was rebuilt from the Cyclopean-1c map: **263 x 199** cells,
grid **0.1 deg**, footprint **4 cells**, map **137,734** surfels, **14**
observations in history, so the new step is **`fix_14`**.

The eligibility census over the 1,384 shoreline cells reproduces the Cyclopean-1d
record exactly - and the manifest's `epistemic_before` block matches the parent's
published counts **field for field**, which independently validates the rebuild:

| refined state | total | exterior | internal |
|---|---|---|---|
| `NEVER_OBSERVED` | 388 | **388** | 0 |
| `OBSERVED_TARGET_NO_DEPTH` | 28 | **0** | **28** |
| `OBSERVED_TARGET_WITH_DEPTH` | 0 | 0 | 0 |
| `OBSERVED_NONTARGET_ONLY` | 398 | 398 | 0 |
| `MIXED_OBSERVATION` | 0 | 0 | 0 |
| `NO_RANGE_REFERENCE` | 104 | 100 | 4 |

**Eligible exterior components: exactly 1** - component 0, with **388**
`NEVER_OBSERVED` shoreline cells spanning depths 9 to **168**.

**The already-seen residue is ineligible twice over, and this was measured rather
than assumed.** All **28** `OBSERVED_TARGET_NO_DEPTH` cells carry
`exterior_distance = -1` (min and max both -1) and belong to components **1 and
2, both `INTERNAL`**. They therefore fail the state test *and* the
exterior-component test independently. `selected.observed_target_no_depth_eligible`
is recorded as `false`.

Selected, with nothing hard-coded - neither the depth 168 nor any gaze:

- cell **(y=62, x=127)**, border distance **168**, equal to the component maximum;
- **2** cells tied at that depth; the one nearer the tied plateau centroid taken;
- gaze **(-0.2, -2.6) deg**, inside the prior gaze envelope (yaw [-16, 14],
  pitch [-9, 11]), **not** a revisit of any of the 14 prior gazes, so
  `revisit_fallback_rank` is **0**;
- verified directly on the chart: the cell is on the shoreline, its refined code
  is `NEVER_OBSERVED`, and its component 0 is `EXTERIOR`.

### The one fixation

One Blender launch, one fixation, **`added_fixations: 1`,
`parent_fixations_rerendered: 0`**. It returned **54,623 target points** - far
above the inherited Reality Check 2b `<100` limit - so it counted as a target
measurement and was fused:

| quantity | value |
|---|---|
| new surfels | **9,262** |
| matched surfels | **45,361** |
| map points | **137,734 → 146,996** (+6.72%) |
| multi-look surfels | 53,412 → **67,496** |
| max support count | 5 → 5 |
| instance ids | **{141}** |
| `idempotent_replay` | **true** |

Verified independently of the runner: `map_before.npz` equals the Cyclopean-1c
`surface_map.npz` bitwise; recomputing the patch from the saved acquisition and
refusing it onto that map reproduces the saved `surface_map.npz` **bitwise** in
xyz, support and provenance; replaying the same patch onto the result returns
`duplicate_patch: true` with **new 0, matched 0** and the map bitwise unchanged.
The observation has **57,333 of 65,536** valid pixels (**87.5%**) and saw two
instances - **{141: 54,623, 143: 2,710}** - with the 2,710 non-target pixels
excluded from the patch, so target purity holds by construction.

### Epistemic state, before and after

Both audits sit on the same inherited chart.

| | before | after |
|---|---|---|
| support cells | 38,971 | **41,342** |
| complement cells | 13,366 | **10,995** |
| shoreline cells | 1,384 | **1,287** |
| exterior components | 1 | 1 |
| internal components | 2 | 2 |
| **exterior `NEVER_OBSERVED` cells** | **388** | **290** |
| **max exterior `NEVER_OBSERVED` depth** | **168** | **142** |

| refined state | before | after | change |
|---|---|---|---|
| `NEVER_OBSERVED` | 388 | **290** | **-98** |
| `OBSERVED_TARGET_NO_DEPTH` | 28 | **28** | **0** |
| `OBSERVED_TARGET_WITH_DEPTH` | 0 | 0 | 0 |
| `OBSERVED_NONTARGET_ONLY` | 398 | 396 | -2 |
| `MIXED_OBSERVATION` | 0 | 0 | 0 |
| `NO_RANGE_REFERENCE` | 104 | 102 | -2 |
| **sum** | **918** | **816** | -102 |

The inherited Cyclopean-1b base states after the look are `UNOBSERVED` 816,
`TARGET_CONTINUATION` 0, `PHYSICAL_DEPTH_BREAK` 310, `AMBIGUOUS` 161, summing to
the 1,287 shoreline cells.

**The action semantics came out as designed.** The gaze addressed genuinely
unseen territory: `NEVER_OBSERVED` fell **388 → 290** and its maximum penetration
depth **168 → 142**. Meanwhile **`OBSERVED_TARGET_NO_DEPTH` is unchanged at 28**,
and the two internal components are bitwise the same objects as before - 1 cell
at **(+7.3000, -2.9000)** and 31 cells at **(+6.7903, -2.1484)**, the identical
centroids Cyclopean-1c and Cyclopean-1d reported. The known seen-but-unmeasured
emblem residue was **not** re-probed, which is the point of the experiment.

### Geometry coherence, which is not accuracy

No evaluator truth was opened, so nothing here is an accuracy claim. What can be
measured internally:

- the 9,262 new surfels lie **entirely inside the old range envelope** -
  [2.0772, 2.2023] m within [2.0667, 2.2372] m - with **zero** points outside it.
  Nothing landed at table or wall depth;
- fusing the probe moved the **pre-existing** surfels by median **0.0000 mm**,
  p99 **2.15 mm**, max **5.99 mm**, all well inside the frozen 12 mm radius, so
  the new look did not drag the existing surface;
- **45,361 of 54,623** probe points (**83.0%**) associated with existing surfels
  within that 12 mm radius, so where the new look overlapped known surface it
  agreed with it;
- the new patch sits at essentially the depth of its neighbours - new surfel
  median range **2.1293 m** against the old map's **2.1380 m**, only **8.7 mm**
  nearer. Across the 16 seam cells the new range minus the local old median is
  median **+15.4 mm**, max **36.7 mm**, with **none** beyond 50 mm, against a
  cloth relief of **145.2 mm**. For comparison, Cyclopean-1c's patch sat 28.6 mm
  *farther* than the old median; this one joins more smoothly.

One statistic was computed and **discarded as uninformative**: "new surfels
disagree with old cells by more than 12 mm" is **definitionally forced**, because
a point within 12 mm of an existing surfel would have *matched* rather than
become new. It is recorded only so it is not mistaken for evidence later.

### Visual reading, descriptive

`epistemic_before.png` shows the inherited picture: an **L-shaped white slot**
cut into the grey support - a vertical arm descending from the top edge plus a
horizontal notch - outlined entirely in **red `NEVER_OBSERVED`**, with the outer
rim **cyan `OBSERVED_NONTARGET_ONLY`**, the bottom edge **blue
`PHYSICAL_DEPTH_BREAK`**, and a small **orange crescent** middle-right, the
`OBSERVED_TARGET_NO_DEPTH` emblem residue.

`epistemic_after.png` shows the **vertical arm of the slot filled**. What remains
is a thin horizontal red seam where the slot used to be, plus a small step at the
left - the complement narrowed from 13,366 to 10,995 cells but did not close, so
the shoreline persists as a line rather than as the boundary of a visible white
region. **The orange crescent is unchanged and still present**, in exactly the
same place: the experiment looked past it, as designed.

`probe_rgb.png` explains the 87.5% stereo validity: the gaze landed on fully
textured cloth - cream weave with visible panel seams and the printed blue band
at the right - with a strip of a second object along the bottom, the 2,710
non-target pixels.

A depth-coloured before/after view of the surfel map shows the same event in 3D:
the L-shaped void is replaced by a coherent patch whose colour matches the
adjacent region rather than contrasting with it, and the small elliptical emblem
hole is still open at the right.

### Structural FAIL lines, and code fixes

**No structural FAIL line was produced anywhere**, and **no code fix was made**;
no file outside the seven Cyclopean-1e sources and docs was modified.

The inherited `RuntimeWarning: invalid value encountered in cast` from
`cyclopean1a_topology.py:117-118` appears again - **30** occurrences - and is
recorded again as harmless, tested against the 1e evidence itself. By inspection,
`_indices` builds its `good` mask with an **explicit**
`np.isfinite(yaw) & np.isfinite(pitch)` term, so the cast's output for a
non-finite input is never used. By measurement, rebuilding the whole post-probe
evidence with a NaN-prefiltered `_indices` raises **0** warnings and yields
**bitwise identical** `seen_target`, `seen_nontarget`, `target_range_m`,
`nontarget_range_m`, `raw_support`, `support` and target range raster. The
**8,203** non-finite angle pairs at `fix_14` are exactly its 8,203 invalid pixels.
It changes no Cyclopean-1e number, so the parent source was correctly left alone.

### What this one fixation establishes, and what it does not

Established. **A refined epistemic state can drive an action directly, with no
new machinery between the representation and the gaze.** The rule was the literal
read-out `NEVER_OBSERVED + EXTERIOR -> deepest inherited border distance -> one
foveation`, with no threshold and no tuned score, and it produced a legal,
unvisited gaze on the first try. **It aimed at genuinely unseen territory and
moved it**: `NEVER_OBSERVED` 388 → 290, maximum depth 168 → 142, complement
13,366 → 10,995, with **54,623** target points and **9,262** new surfels fused
replay-idempotently into a map that `no_frontier` had declared finished two
increments ago. **And it ignored the residue it was supposed to ignore**:
`OBSERVED_TARGET_NO_DEPTH` is unchanged at 28, both internal components bitwise
the same. That is the whole claim - refined entities simplified the next action
instead of requiring a new heuristic.

Not established. **No stopping rule changed and none is proposed**; FSG6f was
never imported or consulted. **One fixation on one seed shows nothing about
convergence** - the slot did not close, 290 `NEVER_OBSERVED` cells remain at depth
142, and a second epistemic gaze was forbidden by construction, so whether this
iterates is untested. **No quality claim is made**: 9,262 surfels is a count, and
with evaluator truth closed the *correctness* of the new surface is unmeasured -
internal coherence is not accuracy. **Nothing was learned about what to do with
`OBSERVED_TARGET_NO_DEPTH`**; the experiment deliberately stepped around it, so
the question of what alternate instrument action should follow a
seen-but-unmeasurable region is exactly as open as Cyclopean-1d left it.
