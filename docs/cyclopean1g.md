# Cyclopean-1g — Re-centered Measurement Probe

## Question

Cyclopean-1f reached attention completion on seed 2111: no exterior `NEVER_OBSERVED` shoreline remained.  The dominant unresolved geometry is now qualitatively different: an internal residue that has been imaged as target but for which frozen stereo returned no valid depth.

Cyclopean-1g asks one deliberately narrow question:

> If that dominant `OBSERVED_TARGET_NO_DEPTH` residue is placed at the foveal/tangent-chart centre for one new look, does the unchanged stereo instrument recover valid target depth there?

Whatever the outcome, this experiment stops after the one look.  A still-unmeasurable residue is recorded and deferred; it does not start a new rescue subproject.  The next project stage is multiple objects.

## Frozen mechanism

- parent: completed Cyclopean-1f, seed 2111;
- fixed head and static scene;
- same cyclopean chart and 0.1 degree grid;
- same support footprint derived from the frozen 12 mm FSG3 association radius;
- same Reality/FSG renderer, rectification, SGBM front end and render/vergence settings;
- same 12 mm surfel fusion;
- no FSG6f policy or stopping logic;
- no evaluator truth.

## One deliberate measurement change

The only intentional acquisition change is **re-centering**.

1. rebuild the final Cyclopean-1f epistemic shoreline;
2. select only `INTERNAL + OBSERVED_TARGET_NO_DEPTH`;
3. choose the component containing the most such cells;
4. choose the eligible cell nearest that component's no-depth-cell chart centroid;
5. if that exact gaze was already used, take the next cell in the same centroid-distance ordering;
6. acquire exactly one fixation there.

The stereo matcher, baseline, vergence/render settings and all geometric tolerances remain frozen.  This isolates whether a more favorable foveal placement alone can recover depth.

## Outcome

The pre-probe no-depth cells of the selected component are projected into the new saved observation using their already-existing local continuation range.

- `DEPTH_RECOVERED`: at least one selected residue cell is observed as target with valid stereo depth in the new look.
- `DEPTH_STILL_ABSENT`: none is.

This is a diagnostic label, not a PASS/FAIL gate.  The target patch from the new fixation is fused normally if valid depth exists elsewhere in the fovea, and all ordinary structural/idempotence/purity checks remain in force.

## Branch disposition

Cyclopean-1g stops after exactly this one look regardless of outcome.

- If depth is recovered, record that re-centering can rescue at least part of this measurement failure.
- If depth is still absent, record the residue as unresolved under the current fixed-head stereo instrument and defer the case.

In either case, the intended next research stage is **multiple objects**, progressing afterward toward the full cyclopean scene.

## Results

Run 2026-09-21 on the workstation. **`CYCLOPEAN1G_COMPLETE`,
`structural_fails: []`, measurement outcome **`DEPTH_STILL_ABSENT`**.** Exactly
one re-centered fixation was added, no parent fixation was rerendered, and the
Cyclopean-1f parent is byte-identical afterwards. This is a **diagnostic label,
not a PASS/FAIL**: no recovered-cell count is a gate, and the experiment stops
here either way.

### Provenance

Working tree clean. Prospective commit **`8944c17`**; pre-1g parent **`a4d9b7d`**.
The package adds **exactly the seven expected files, all `A`**
(`tools/cyclopean1g_{public,measurement,probe,compare}.py`,
`tools/dev/check_cyclopean1g.py`, `docs/cyclopean1g.md`,
`docs/cyclopean1g-checks.md`). `git diff` against `a4d9b7d` over **59 frozen
sources** - every FSG1/FSG3/FSG6f source, renderer, scene, rig, pin file, every
Reality Check 1/2/2b source and **every Cyclopean-1a through 1f source** - is
**empty (0 lines)**, and all 59 sha256 are SAME. In particular the acquisition
path this step must reuse unchanged, `tools/reality2_render_fix.py`, is
byte-identical at `9f1433d189fbcbb5…`, as is the stereo front end
`tools/fsg_stereo_supported.py` at `683ae91eaca7b6af…`.

The parent was located **by manifest**: exactly one
`Cyclopean1f-epistemic-loop-v1` record with seed 2111 and profile `full` exists,
`previews/cyclopean1f/full-seed2111`. Its required conditions hold -
`scientific_stop_reached` **true**, `stop_reason`
**`NO_ELIGIBLE_EXTERIOR_NEVER_OBSERVED`**, `exterior_never_observed_cells`
**0**, `truth_opened` false, fixed head and static scene true - and it carries
the established **28**-cell `OBSERVED_TARGET_NO_DEPTH` residue. Its three pinned
files hash identically **before and after**:

| file | sha256 (before == after) |
|---|---|
| `prediction_manifest.json` | `fee393ec99d0c81d…5fe9b647` |
| `surface_map.npz` | `7bc4e94a9c24fea4…1bcf2cf6` |
| `epistemic_final.png` | `200b6dd6f9a944eb…6380eea6` |

The runner additionally re-derives the parent's final state and asserts it
against the published fields before acquiring anything; that guard passed.

### Environment

Blender 5.2.1 LTS headless, Cycles, **OPTIX** on an RTX 4090 (driver 595.84);
host analysis under `.venv/bin/python` 3.12.3. **Interactive at 36.0 s wall**,
including the single Blender launch.

### Checks

`py_compile` clean on all five modules. The three prescribed lines appeared
verbatim:

```text
[cyclopean1g-measurement] PASS internal_no_depth_only=true centroid_recentering=true one_probe=true binary_outcome=true branch_closes=true
[cyclopean1g-policy] PASS parent=cyclopean1f seed2111_only=true frozen_stereo=true frozen_vergence=true quality_gated=false next=multi_object
[cyclopean1g-check] SUMMARY passed=6 failed=0
```

**The six 1g negatives are genuine source-mutation controls, and this was
verified rather than taken on trust.** Each applies a real mutation to the
actual source text, re-evaluates the structural checks, and exits 1 **only if a
previously-passing check now fails**; each one named the check that caught it:

| negative | detected by |
|---|---|
| `external` | `internal_no_depth_only` |
| `unseen` | `internal_no_depth_only` |
| `multiprobe` | `one_probe` |
| `quality` | `binary_outcome_no_gate` |
| `rescueloop` | `no_truth_or_rescue_loop` |
| `truth` | `no_truth_or_rescue_loop` |

The escape path was exercised too: a deliberately inert mutation added to a
scratch copy produced `[cyclopean1g-negative] ERROR noop mutation escaped
detection` and **exit 2**, not a silent exit 1. So these are controls that can
distinguish detection from non-detection - **restoring the property Cyclopean-1f
lacked**. The known Cyclopean-1f caveat stands recorded and **1f was not edited
in this step**; its six named flags remain declaration-only.

All prior suites green with their negative sets still firing, **67 prior
negatives, none weakened**: cyclopean1f 6/6 (6/6), cyclopean1e 6/6 (6/6),
cyclopean1d 6/6 (6/6), cyclopean1c 6/6 (6/6), cyclopean1b 6/6 (6/6),
cyclopean1a 6/6 (6/6), reality2b 7/7 (10/10), reality1 6/6 (6/6),
fsg6f 14/14 (15/15).

### The selection

Rebuilt on the inherited chart - **263 x 199**, grid **0.1 deg**, footprint
**4 cells** - from the parent's final map of **155,490** surfels at **17**
completed fixations, so the new step is **`fix_17`**.

- eligible **INTERNAL** components carrying `OBSERVED_TARGET_NO_DEPTH`: **2**;
- chosen component **2**, **27** no-depth cells of **31** total cells - the
  dominant residue;
- its no-depth centroid is cell **(66.481, 196.926)**; the nearest eligible cell
  is **(y=66, x=197)** at squared distance **0.2373** cells;
- gaze **(+6.8000, -2.2000) deg**, `revisit_fallback_rank` **0** - the declared
  fallback was not needed;
- `refined_state` **`OBSERVED_TARGET_NO_DEPTH`**, `component_kind`
  **`INTERNAL`**, `never_observed_eligible` **false**;
- the 27 cells' inherited local range references span **2.1177 / 2.1474 /
  2.1800 m** (min / median / max), all finite, so every continuation test point
  was well defined.

`NEVER_OBSERVED` was ineligible by construction and, at this parent, empty
anyway (0 cells). No exterior component was eligible.

### The one look, and the diagnostic

One Blender launch through the unchanged `reality2_render_fix.py` path, frozen
stereo, vergence and render settings; the **only** deliberate change is where the
fovea points. **`added_fixations: 1`, `parent_fixations_rerendered: 0`.**

The pre-probe residue cells were evaluated in the saved new observation using
their existing continuation-test points and the saved oracle instance and stereo
`valid` masks:

| quantity | value |
|---|---|
| selected residue cells | **27** |
| target-seen cells | **27** |
| **recovered valid-target-depth cells** | **0** |
| non-target-seen cells | **0** |
| unsupported cells | **0** |
| **outcome** | **`DEPTH_STILL_ABSENT`** |

This is the cleanest form the negative result could take. **The re-centering
worked as an acquisition change**: all 27 cells had a supported projection, and
all 27 were imaged as target - none fell outside the core, none landed on
background. **The instrument still returned no valid depth for a single one of
them.** The failure is therefore not about where the observer looked.

The re-centering is independently visible in the observation itself. With the
residue at the fovea centre, the central **32x32** window is only **23.0%**
valid against **86.7%** frame-wide (60.9% at 64x64, 76.1% at 96x96, rising with
distance from the centre), and the central 64x64 mean RGB is
**[0.9514, 0.4590, 0.3305]** against a frame mean of [0.6358, 0.5021, 0.4057] -
the saturated emblem, now squarely in the fovea. Frame-wide, valid pixels carry
median local texture **0.01031** against **0.00501** for invalid ones.

### Fusion, and the ordinary structural checks

The fixation returned **55,567 target points** and was fused under the unchanged
12 mm FSG3 contract:

| quantity | value |
|---|---|
| new / matched surfels | **194** / **55,373** |
| map points | **155,490 → 155,684** (+194, +0.12%) |
| multi-look surfels | 89,740 → **97,825** |
| max support count | 5 → **6** |
| instance ids | **{141}** |
| `idempotent_replay` | **true** |

Verified independently of the runner: `map_before.npz` equals the Cyclopean-1f
`surface_map.npz` bitwise; recomputing the patch and refusing it reproduces the
saved map **exactly - xyz maximum difference 0.00 nm**, with `support_count`,
`provenance_mask` and `instance_id` all identical; replaying returns
`duplicate_patch: true` with **new 0, matched 0**. The observation has
**56,852 of 65,536** valid pixels (**86.7%**) and saw **{141: 55,567,
143: 1,285}**, the non-target pixels excluded from the patch.

**Only 194 of 55,567 points were new - 99.7% matched existing surfels within
12 mm.** That is expected and is itself informative: the re-centered fovea was
looking almost entirely at surface the map already had, because the one thing it
was aimed at is the one thing it cannot measure.

### The residue after the look

`OBSERVED_TARGET_NO_DEPTH` moved **28 → 22**, and that movement is **not depth
recovery**. Traced cell by cell: **21 kept, 7 disappeared, 1 newly appeared**.
All **7** that disappeared **became support** - the 194 newly fused surfels, all
from the textured cloth *around* the emblem, brought their 12 mm footprints over
those rim cells. Not one cell left the state by being measured.

At the fixed point after this look: shoreline **1,000 → 990**, support
**43,001 → 43,011**, complement **9,336 → 9,326**, and the refined census is
`NEVER_OBSERVED` **0**, `OBSERVED_TARGET_NO_DEPTH` **22**,
`OBSERVED_TARGET_WITH_DEPTH` **0**, `OBSERVED_NONTARGET_ONLY` **421**,
`MIXED_OBSERVATION` **0**, `NO_RANGE_REFERENCE` **74**. The internal residue
persists as two components, **23** cells at **(+6.6609, -2.1391)** and **2**
cells at **(+7.4500, -2.1000)**, carrying only `OBSERVED_TARGET_NO_DEPTH` and
`NO_RANGE_REFERENCE` shoreline.

### Coherence, which is not accuracy

Evaluator truth stayed closed - no Cyclopean-1g source references
`evaluation_only`, `reality2b_eval` or a truth file - so every number here is
internal consistency and **no accuracy claim is made**.

- overlap agreement is the highest in the series: **55,373 of 55,567**
  (**99.7%**) of probe points associated with existing surfels within 12 mm;
- fusing moved the **pre-existing** surfels by median **0.0000 mm**, p99
  **1.72 mm**, max **5.87 mm** - well inside the frozen 12 mm radius;
- the 194 new surfels span [2.0855, 2.2139] m inside an old envelope of
  [2.0659, 2.2372] m, with **zero** outside it. No gross wrong-depth patch;
- target purity holds: final instance ids exactly **{141}**, with the 1,285
  non-target pixels excluded by construction.

### Visual reading, descriptive

`probe_rgb.png` shows the re-centering plainly: the red-orange emblem sits at the
centre of the fovea, a flat and almost perfectly uniform ellipse, with the
printed blue band to its left and cream weave around it. There is no internal
detail in the ellipse for a correspondence matcher to lock onto.

`epistemic_before.png` and `epistemic_after.png` are almost indistinguishable: a
solid grey support with a cyan and blue rim, and the small **orange
`OBSERVED_TARGET_NO_DEPTH` crescent** in the middle right. In the after image the
crescent is marginally thinner and slightly broken - the 7 rim cells that became
support - but it is unmistakably still there. **One re-centered look changed
essentially nothing about the residue**, and the picture says so.

### Structural FAIL lines, and code fixes

**No structural FAIL line was produced anywhere**, and **no code fix was made**;
nothing outside the seven Cyclopean-1g files was modified.

The inherited `RuntimeWarning: invalid value encountered in cast` from
`cyclopean1a_topology.py:117-118` appears again - **36** occurrences - and is
recorded again as harmless: `_indices` builds its `good` mask with an **explicit**
`np.isfinite(yaw) & np.isfinite(pitch)` term, and a NaN-prefiltered rebuild of
the 1g evidence raises **0** warnings with **bitwise identical** `seen_target`,
`seen_nontarget`, `target_range_m` and `nontarget_range_m`. The **8,684**
non-finite angle pairs at `fix_17` are exactly its 8,684 invalid pixels.

### What this establishes, and what it does not

Established. **Foveal re-centering alone does not rescue this measurement
failure.** The residue was placed at the centre of the fovea, all **27** of its
cells were re-imaged as target with supported projections, and **zero** recovered
valid stereo depth. Because every other acquisition variable was frozen - matcher,
baseline, vergence, render settings, chart, footprint, fusion, every tolerance -
the experiment isolates placement, and placement is not the cause. The visible
reason is consistent: the emblem is a saturated, near-uniform ellipse, and stereo
validity collapses to **23.0%** at the fovea centre against 86.7% frame-wide,
with invalid pixels carrying half the local texture of valid ones.

Also established, more narrowly: **the 28 → 22 change is bookkeeping, not
progress.** All seven cells that left the state did so because neighbouring
fused surfels grew over them, and **the experiment says so explicitly rather than
reporting the drop as improvement**.

Not established. **This is one look, one residue, one seed**, and it says nothing
about whether *some other* instrument change - a different matcher, baseline,
vergence, illumination or active pattern - would recover the depth; **none was
tried, by design**. It is **not an accuracy claim**: truth stayed closed, so the
194 new surfels and the 99.7% overlap are internal consistency only. And
`DEPTH_STILL_ABSENT` is **not a failure of the experiment** - it is the
measurement the experiment was built to take.

**Branch disposition, as declared before the run:** Cyclopean-1g stops after this
one look regardless of outcome. The residue is recorded as **unresolved under the
current fixed-head stereo instrument and deferred**. No second view, alternate
matcher, interpolation, texture rescue or normal cue was attempted, and none is
proposed here.

**The intended next research stage is multiple objects, and that is unchanged by
this outcome** - it was the declared next step whether depth had been recovered
or not - progressing afterward toward the full cyclopean scene.
