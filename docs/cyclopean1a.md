# Cyclopean-1a — spherical topology hole probe

## Question

Reality Check 2b showed that the fixed-head observer can continue beyond the old six-look budget, learn from empty looks, and terminate by its own `no_frontier` rule.  It also exposed the next missing abstraction: `no_frontier` can leave an enclosed unsampled region.  Seed 2111 ended with a large ring-like gap and seed 2179 with a much smaller one.

Cyclopean-1a asks the smallest next question:

> Can the persistent head/cyclopean spherical domain expose such internal sampling holes, distinguish them from an already-observed physical depth break, and place one foveation inside the largest unresolved hole without changing FSG6f?

This is the first concrete use of the cyclopean sphere as a 2-D perceptual organization layer over the metric surfel scene.

## Representation

For every target surfel `x_h`,

```
rho   = ||x_h||
yaw   = atan2(x, -z)
pitch = atan2(y, hypot(x,z))
```

The metric surfel map remains authoritative.  The chart is bookkeeping only.

The angular raster uses the already-declared D9 evaluation scale: `2*s0` (`0.2 deg` small, `0.1 deg` full).  A surfel occupies an angular disc whose radius is derived from the frozen FSG3 association radius:

```
alpha = atan(0.012 / median_range)
```

No new metric spatial tolerance is introduced.

An **internal hole** is a connected component of the complement of target support that does not touch the padded chart boundary.  The exterior component is therefore not a hole.

## Physical-hole cue

Topology alone does not imply that an internal loop should be filled.  A square-ring tabletop is the canonical counterexample.

Completed prediction-side stereo observations are projected into the same chart.  An internal hole is considered already resolved as a **physical depth break** when:

1. observed cells inside it are non-target-majority; and
2. their reconstructed range differs from the nearby target-boundary range by more than the already-frozen 12 mm association radius.

This is intentionally only a first geometric cue.  Surface-normal continuity is recorded as a future extension, not added here.  If a hole is unobserved or ambiguous, probing it is allowed: an empty/non-target result is itself useful perceptual evidence.

## Experiment

Inputs are the two completed **Reality Check 2b full records**, seeds 2111 and 2179.  Parent renders are never regenerated.

For each record:

1. load the final persistent target surfel map;
2. reconstruct completed prediction-side observation evidence from the saved acquisitions;
3. build the cyclopean support chart and enumerate internal holes;
4. mark any hole already supported as a physical depth break;
5. choose the largest remaining hole by angular area;
6. foveate its spherical centroid **once** (0.1-degree physical-view quantization);
7. fuse target stereo if the inherited Reality Check 2b `<100`-point rule says it is a target measurement; otherwise retain it as negative evidence and fuse nothing;
8. rebuild the same chart and report how the selected hole and map changed.

There is no loop of topology probes in Cyclopean-1a.  It is one probe only.  Integration with the active stopping rule is a later decision.

## Contract

Frozen:

- fixed head and static scene;
- Reality Check 2b scene, texture and seeds;
- FSG1 stereo instrument;
- FSG3 12 mm association/hash;
- FSG6f source and ranking;
- Reality Check 2b empty-look semantics;
- every saved parent fixation and map.

No evaluator truth, mesh reconstruction, hole filling, ICP, new stereo matcher, new frontier ranking, completeness percentage, or numerical quality PASS threshold is permitted.

Structural completion means that both parent records are processed faithfully and any new probe is serialized with pure target geometry and idempotent fusion.  The scientific outputs are descriptive: number/area/state of holes, selected gaze, target points found, map growth and hole-area change.

## Results

Run on the workstation 2026-09-21 (Blender 5.2.1 LTS headless, Cycles, OPTIX on
RTX 4090, driver 595.84; host-side scripts under `.venv/bin/python` 3.12.3 per
the working agreement).  One probe per parent record, run once each.

**Status: `CYCLOPEAN1A_COMPLETE`, `structural_fails: []`.  Both parent records
were processed faithfully; no parent view was rerendered; no FAIL line was
produced anywhere.  This is a structural statement only - no PASS is inferred
from coverage or from hole reduction.**

### Provenance and frozen-source audit

`git status --short` empty; HEAD `e7a33a3` on `main`.
`git diff --name-status HEAD~1 HEAD` is exactly seven files, all `A`:
`tools/cyclopean1a_{public,topology,probe,compare}.py`,
`tools/dev/check_cyclopean1a.py`, `docs/cyclopean1a.md`,
`docs/cyclopean1a-checks.md`.

`git diff HEAD~1 HEAD` restricted to every FSG1/FSG3/FSG6f source, the renderer,
`fsg_scene.py`, `fsg_validation_render.py`, `rig.py`, `bl_common.py`,
`requirements-fsg.txt` **and every Reality Check 1, 2 and 2b source** is
**empty**, confirmed additionally by per-file sha256 against `077850d` - all
SAME: `fsg_stereo_supported` 683ae91eaca7b6af, `fsg_stereo_hdr`
67e2ec4667bcc179, `fsg_stereo` faebf0f1b3acbfde, `fsg_evaluate`
a5134b8d8537714d, `fsg_geometry` d9537d8ebc23b60c, `fsg3_surface_map`
1b9dbeb873105ec9, `fsg6f_public` c79f58c9b51f33d4, `fsg6f_frontier`
d636c9405d719916, `fsg6f_run` f2d4bdd54b8d395f, `fsg_render` 681237fa8533b7cc,
`fsg_scene` 1f410577c1103e01, `fsg_validation_render` f18883e1e2764dd7, `rig`
dff43ec0cd9d5047, `bl_common` aa7a56e8cd4988cb, `reality1_public`
d2b00211021ff65d, `reality1_scene` b4392230292bb51c, `reality1_render_fix`
bdc068ad931e1072, `reality2_public` c7e7bd44d1a28de3, `reality2_render_fix`
9f1433d189fbcbb5, `reality2b_public` dfe1ca243c4c1543, `reality2b_run`
137bef448d5f1c42, `reality2b_eval` ee6d09abb33e24b7, `check_reality2b`
09d69165706764b2.

### Parents, located by manifest

A scan of every `prediction_manifest.json` under `previews/` found exactly three
`RealityCheck2b-prediction-v1` records and exactly one `full` record per seed, so
both parents resolved to the example paths **by manifest, not by assumption**.
Both pass every condition (23/23 and 26/26): schema, profile `full`, termination
**`no_frontier`**, `truth_opened` false, `fixed_head`/`static_scene` true, frozen
FSG6f policy and FSG1 instrument, and every map present.  Hashes pinned before
the probes and **re-verified unchanged afterwards**:

| | seed 2111 | seed 2179 |
|---|---|---|
| record | `previews/reality2b/full-seed2111` | `previews/reality2b/full-seed2179` |
| fixations / empty steps | 13 / [12] | 16 / [14, 15] |
| `prediction_manifest.json` | `45a8c524f50a2ea4…616e404f` | `0113296bec076f83…450fb533` |
| `policy_trace.json` | `abb7b3b292b837c6…8ae52013` | `c01103be845391ab…41be2550` |
| `surface_map.npz` | `c780d4345e6f74d3…9da1f6e1` | `1db5c6a87b9dd1f6…efccb24a` |

### Checks

`py_compile` clean on all five new modules.

```
[cyclopean1a-topology] PASS sampling_hole=true physical_hole_resolved=true exterior_not_hole=true
[cyclopean1a-policy] PASS cyclopean_domain=true topology=true physical_hole_depth_break=true one_probe_max=true no_mesh=true quality_gated=false
[cyclopean1a-check] SUMMARY passed=6 failed=0
```

All six negatives exit 1: `fillhole`, `physicalclose`, `exteriorhole`, `truth`,
`mesh`, `multiprobe`.  Prior suites green with their negative sets still firing:
`[reality2b-check] passed=7 failed=0` (**10/10** negatives exit 1),
`[reality1-check] passed=6 failed=0` (6/6), `[fsg6f-check] passed=14 failed=0`
(**15/15**).

### The chart, both records

Both charts use grid **0.1 deg** (`2*s0`, full profile) and a surfel footprint of
**4 cells** derived from the frozen 12 mm FSG3 radius at the measured median
range - `atan(0.012 / 2.1337) = 0.322236 deg` for seed 2111 and `0.322291 deg`
for seed 2179, so the dilation closes gaps narrower than **0.8 deg**.  No new
metric tolerance was introduced and nothing was tuned.

| | seed 2111 | seed 2179 |
|---|---|---|
| map surfels | 117,567 | 138,010 |
| chart (cells) | 263 x 199 | 263 x 192 |
| chart extent yaw / pitch (deg) | -12.90..13.30 / -8.80..11.00 | -12.90..13.30 / -8.80..10.30 |
| median range (m) | 2.1337 | 2.1333 |
| footprint radius (deg) -> cells | 0.322236 -> 4 | 0.322291 -> 4 |
| raw occupied cells | 28,032 | 32,906 |
| support cells after dilation | 34,221 (65.4% of chart) | 37,873 (75.0%) |
| complement cells | 18,116 | 12,623 |
| complement components | **1**, border-touching | **2** (1 border-touching of 11,851 cells, **1 internal**) |
| **internal holes** | **0** | **1** |

### Discretization holes - reported in full before any raster rule was touched

Against the **undilated** raw support, both charts are riddled with single-surfel
gaps, exactly the failure mode the authorization named first:

- **seed 2111**: 331 raw complement components, **330 internal**.  Largest 42
  cells / **0.4168 deg2** at centroid (+8.25, +7.03); then 29 / 0.2898 at
  (+9.21, +1.92), 24 / 0.2383 at (-8.09, +6.88), 22 / 0.2197 at (+9.38, -2.98),
  20 / 0.1993 at (-9.63, -4.84).
- **seed 2179**: 411 raw components, **410 internal**.  Largest 1,389 cells /
  **13.8825 deg2** at (+6.23, -1.47) - this is the real hole, not noise - and the
  next largest is 36 cells / **0.3572 deg2** at (+0.14, +7.16), then 23 / 0.2291,
  22 / 0.2198, 17 / 0.1688.

The frozen 12 mm footprint removes **every** one of these below ~0.5 deg2 while
leaving seed 2179's genuine 13.88 deg2 component standing as a 7.72 deg2 hole.
**No raster rule was changed** - this is reported as evidence that the inherited
footprint is already doing the job it was specified to do.

### Seed 2111 - no internal hole, no probe, nothing rendered

The complement of the dilated support is **a single connected component of 18,116
cells that touches the padded chart border**.  By the stated rule the exterior
component is not a hole, so there is **no internal hole and no probe candidate**.
The probe was not taken, `added_fixations: 0`, `parent_fixations_rerendered: 0`,
and the map is **bitwise unchanged** at 117,567 points and 48,350 multi-look
surfels.  No acquisition directory was created and nothing was rendered.  Per the
contract this is a valid observational result.

**This corrects a reading in the Reality Check 2b report.**  There the seed-2111
gap was described, from an (x, y) scatter of the surfels, as "a large unvisited
rectangular hole in the middle of the cloth".  The cyclopean chart - which is the
actual topological representation - shows it is **not enclosed**: the unsampled
region runs continuously from the interior out through a channel on the **left**
side of the chart to the exterior.  It is a bay, not a lake.  The Reality Check
2b numbers are unaffected; only that topological characterisation was wrong, and
exposing it is precisely what this representation was built to do.

### Seed 2179 - one internal hole, one probe

**Hole before**, the only internal component: **772 cells, 7.7165 deg2**,
centroid **(+6.2780, -1.5873)**, state **`UNOBSERVED_HOLE`**.  Inside it,
`target_observed_cells = 0` and `nontarget_observed_cells = 0` - no completed
stereo observation covers it at all - so the physical-depth-break test could not
fire: the boundary target range is 2.1361 m, there is no interior non-target
range, `range_gap_m` is `None`, and the hole is **not** resolved as a depth
break.  `probe_candidate: true`.

**Probe**: centroid snapped to the 0.1-degree physical-view lattice at
**(6.3, -1.6)** from the unsnapped (6.27796, -1.58728).  That gaze is inside the
allowed domain and is **not** a revisit of any of the sixteen parent gazes, so no
fallback rule was invoked.  One fixation, `fix_16`, was rendered -
`added_fixations: 1`, `parent_fixations_rerendered: 0`.

**Result**: **58,721 target points** - comfortably over the inherited Reality
Check 2b `<100` limit, so it counted as a target measurement and was fused:
**3,174 new surfels**, 55,547 matched, **`idempotent_replay: true`**, map
**138,010 -> 141,184** points and multi-look surfels **57,571 -> 70,136**, final
map instance ids exactly **{141}**.

**Hole after**: still one internal component, now **35 cells / 0.3498 deg2** at
centroid (+6.85, -2.13), state `UNOBSERVED_HOLE`.  The selected hole's angular
area went from 7.7165 to 0.3498 deg2.  That number is reported as a measurement
of what the one probe did; **it is not a PASS criterion and no threshold is
attached to it.**  The residue is the same size class as the discretization
components listed above, which is worth noting and is not interpreted further.

### Aggregate

```
[cyclopean1a-compare] CYCLOPEAN1A_COMPLETE {"records": [{"candidate_holes_after": 0, "candidate_holes_before": 0, "largest_after_deg2": 0.0, "largest_before_deg2": 0.0, "map_point_gain": 0, "probe_taken": false, "probe_target_points": null, "seed": 2111}, {"candidate_holes_after": 1, "candidate_holes_before": 1, "largest_after_deg2": 0.3497566848117508, "largest_before_deg2": 7.716529889378285, "map_point_gain": 3174, "probe_taken": true, "probe_target_points": 58721, "seed": 2179}], "structural_fails": []}
```

### Structural integrity, re-verified independently of the tooling

Both records: `map_before.npz` equals the saved Reality Check 2b parent map
exactly; both parents' `prediction_manifest.json`, `policy_trace.json` and
`surface_map.npz` sha256 are **unchanged after the probes**; `truth_opened`
False; `fixed_head` and `static_scene` True; `parent_fixations_rerendered` 0;
`added_fixations` 0 and 1, never more; final map instance ids exactly **{141}**;
the one fused probe is **replay-idempotent**; and seed 2111's map is bitwise
identical before and after.  Both manifests carry
`public_spec_sha256 76c32103a04e500eb81d35ff69514a5fef6a6483bbce3870282fc8a713da44a1`.

### Visual reading (descriptive; no PASS inferred)

`full-seed2111/cyclopean_before.png` shows the point plainly: the unsampled white
region is one continuous area that reaches the left edge of the chart.  There is
no enclosed red region because there is no internal hole.  Nothing else was
rendered for this seed.

`full-seed2179/cyclopean_before.png` shows one compact red rectangle sitting well
inside the grey support, with the selected centroid marked.
`cyclopean_after.png` shows the same chart after the single fused probe: the red
rectangle is gone, replaced by a thin red crescent along what was its lower edge.

`full-seed2179/probe_rgb.png` shows why the probe returned so much: the gaze
landed on fully textured cloth - the printed blue band on the left and the
red-orange emblem in the centre - with no wall, table or prop in frame.  58,721
target points is the largest single-look count anywhere in this series, and the
hole was unobserved rather than a depth break precisely because no earlier
fixation had ever pointed there.

### Structural FAIL lines

**None.**  No FAIL line was produced by `[cyclopean1a-check]`,
`[reality2b-check]`, `[reality1-check]`, `[fsg6f-check]`, either probe, or the
comparator.

### Code fixes

**None.**  No source file was modified.

One diagnosed and deliberately unfixed observation, recorded because it is
visible in the console: both probes emit
`RuntimeWarning: invalid value encountered in cast` from
`cyclopean1a_topology.py:117-118`, where `_indices` casts yaw/pitch to `int64`
before filtering.  **Measured, not assumed**: each saved observation's rectified
grid carries 43,689 non-finite cells out of 65,536 (ordinary stereo holes); on
this platform every NaN/inf casts to `INT64_MIN`, which fails the subsequent
`x >= 0` test, and a direct test confirms **zero** non-finite entries are
admitted by `good`.  The warning therefore changes no reported number.  It is a
robustness and noise issue, not a demonstrable defect producing a wrong result,
so under the authorization it was left alone and reported rather than edited.

### What the representation actually exposed

Three things, none of which is a quality verdict:

1. **The cyclopean chart discriminates.**  On the same fixture, same grid and
   same frozen footprint, it returned **zero** internal holes for one record and
   **exactly one** for the other, and in the seed-2179 case the internal hole it
   found is the one a human would point at.
2. **It overturned a description that came from looking at a point cloud.**
   Seed 2111's gap is topologically open to the exterior.  A representation that
   can contradict an eyeball reading of the same data is doing work.
3. **The physical-depth-break cue was never exercised.**  The only hole found was
   `UNOBSERVED_HOLE` with zero observed cells of either kind inside it, so the
   range-gap test returned `None` and was never the reason for anything.  The cue
   is implemented and passes its synthetic control (`physicalclose`), but **this
   run provides no field evidence about it.**  That is a gap in the evidence, not
   a result.

What this does **not** settle: whether topology should inform stopping.
Cyclopean-1a is one probe, by construction, and integration with the active
stopping rule is a later decision.  Seed 2111 in particular shows that
`no_frontier` plus an open bay is not something this chart alone would have
caught, because an open bay is not a hole by the stated rule.
