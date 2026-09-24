# Classroom-FSG-1 — controlled tangent-stereo reconstruction

## Purpose

Return from the matcher micro-study to the actual Classroom scene and test the completed generic FSG bridge as a scene-construction instrument.

The attention variable is controlled by replaying the already sealed Demo-Classroom-1 fixation history. The old demo's foreground/background role assignments are **not** reused. For this experiment every positive instance id is an ordinary scene entity.

The loop is therefore:

```text
sealed gaze
  -> Blender tangent pair
  -> unchanged rectification + SGBM
  -> native valid metric patch
  -> per-instance persistent 12 mm fusion
```

Two scene reconstructions are accumulated in parallel:

1. **native** — unchanged FSG stereo validity only;
2. **guarded** — a pure row-subset of native stereo, with Blender truth allowed only to reject gross range errors after stereo.

The guarded stream is damage control for the concept demonstration. It is not a truth-free confidence model.

## Explicitly out of scope

For this round there is:

- no autonomous gaze/controller experiment;
- no foreground/background decomposition;
- no background panorama;
- no special background object or shell;
- no SGBM tuning;
- no replacement matcher;
- no truth-derived geometry insertion.

## Frozen attention

Source:

```text
previews/demo-classroom1/full-seed2111/fixation_history.json
```

The source must contain exactly 225 ordered fixations and be accompanied by the original `demo_manifest.json`. The new runner consumes only the gaze yaw/pitch and order. Historical target ids/action labels are carried as provenance only.

## Measurement instrument

Each gaze is reacquired with:

```text
tools/fsg_blend_bridge.py
profile small
64 spp
seed 2111
vergence 2.10 m
IPD 0.063 m
baseline_projected tangent frame
```

Then `tools/fsg_stereo.py` runs unchanged. Its native validity mask is the native stream.

## Damage-control guard

After stereo, evaluator-only Blender left-eye range is remapped through the same rectification into the stereo core. A native point survives the guarded stream iff

```text
|range_stereo - range_truth| <= max(0.10 m, 0.05 * range_truth)
```

This is exactly a rejection operation. `xyz_h` in the guarded patch is copied from the corresponding native stereo row. Blender `xyz_h` is never inserted or substituted.

## No foreground/background split

The generic bridge's deterministic evaluated-depsgraph parent-root ids provide instance identity. Every positive id is eligible for ordinary persistent geometry.

This means a fixation historically aimed at the floor may also contribute valid geometry for a chair, pipe, book, wall, or any other instance visible in the tangent core. Nothing is discarded because it was historically called background.

## Fusion

The established `fsg3_surface_map.initialize/fuse` and frozen 12 mm association rule are reused unchanged.

`fsg3_surface_map` stores patch provenance in a `uint64`, limiting one object map to 63 patch ids. Replaying 225 fixations could exceed that if every fixation contributed to the same object, so Classroom-FSG-1 uses a deterministic adapter: four contributing fixations per fusion packet. Thus at most `ceil(225/4)=57` packets can reach any object. This changes only provenance granularity; the fusion algorithm and 12 mm rule remain unchanged.

Packets still obey the inherited 100-point FSG3 minimum. Final leftovers below 100 points are reported, not force-fused.

## Primary outputs

```text
classroom_fsg1_manifest.json
classroom_fsg1_report.json
classroom_fsg1_report.md
replayed_fixations.json
instance_groups.json

native_scene_points.npz
native_scene_points.ply
native_objects.json
objects/native/object_<id>.npz/.ply

guarded_scene_points.npz
guarded_scene_points.ply
guarded_objects.json
objects/guarded/object_<id>.npz/.ply
```

Every fixation also retains its tangent observation, stereo result, native/guarded patches, evaluator-only truth, and `measurement_evaluation.json` beneath `fixations/fix_<step>/`.

## Interpretation

The decisive comparison is not whether guarded is more accurate — it must be, because its rejection gate uses truth. The useful comparison is:

- how much geometry current SGBM can construct natively in the fixed Classroom attention sequence;
- how much gross corruption the oracle gate must remove;
- whether the guarded scene demonstrates that the larger tangent-stereo + persistent-memory architecture is viable when matcher failures are suppressed;
- which objects/ranges remain poorly measured even under the completed bridge.

If the guarded scene is substantially better than native and qualitatively useful, the next engineering/scientific move is to keep the architecture fixed and swap only the stereo matcher.

## Results

**CLASSROOM_FSG1_GUARDED_GOOD 2026-09-24 on branch `classroom-fsg-1`.** All 225 sealed
gazes were replayed through the generic tangent bridge in 4748.55 s (79.1 min, ~21.1 s per
gaze, dominated by Blender re-acquisition; SGBM itself is ~0.03 s). Nothing in `tools/`
changed; the five established sources are byte-identical to `605fdfc` before, during and
after the run.

The architecture works. The matcher is the limitation, and the evidence separating the two
is unusually clean.

### Control and provenance

| control | value |
|---|---|
| fixations replayed / available | **225 / 225** |
| source history sha256 | `0ba7a0543b948f36...` |
| source manifest sha256 | `62c2472c7b3d15cc...` |
| instance grouping sha256 | `f35cf39e47a60035...` (206 groups, 854 mesh instances) |
| `attention_replayed_not_reselected` | **true** |
| foreground/background decomposition, panorama, shell, special bg object | **all false** |
| `historical_foreground_background_roles_ignored` | **true** |
| `guarded_is_subset_only` | **true** |
| `truth_inserted_or_substituted_geometry` | **false** |
| `truth_used_only_after_stereo_for_guard_and_evaluation` | **true** |
| `frozen_tools_unchanged_during_run` | **true** |

The sealed source carries `oracle_attention_for_all_fixations: true` and
`local_fsg_attention_actions: 0`. No controller was run and no gaze was reselected.

Spot-checked on 12 random fixations: truth-separation, boolean-subset and exact-alignment
flags correct 12/12, and the observation contract is exactly
`{rgb_L, rgb_R, instance_L, instance_R}` in all of them.

The smoke test established acquisition, unchanged SGBM, non-empty native patches, a strict
boolean row subset with **byte-identical** xyz, exact instance alignment, no truth xyz in
patch geometry, and fusion that is both deterministic and **idempotent** - re-fusing an
identical patch adds 0 surfels and is flagged `duplicate_patch`. No defect was found, so no
repair was needed.

One measured caveat: Blender acquisition is **not** bit-reproducible. Two identical
four-fixation runs gave native counts 1735/1740 on the same gaze, a drift below 0.1%.
That is a Cycles/OPTIX sampling property, not a fusion property.

### Measurement totals

| | native | guarded |
|---|---:|---:|
| accepted points | **942,402** | **666,999** |
| rejected by the oracle gate | - | 275,403 (**29.22%** of native) |
| depth error, median of fixation medians | **164.6 mm** | **44.6 mm** |
| depth error, median of fixation P95 | **1176.5 mm** | **94.0 mm** |

Per-fixation distributions (225 fixations):

| quantity | P10 | P50 | P90 | max |
|---|---:|---:|---:|---:|
| native valid fraction | 0.001 | 0.128 | 0.804 | 0.822 |
| native points | 10 | 2,090 | 13,172 | 13,471 |
| guarded points | 0 | 728 | 13,150 | 13,450 |
| native depth error median | 22.7 mm | 164.6 mm | **4441.5 mm** | **32,346.7 mm** |
| guarded depth error median | 22.5 mm | 44.6 mm | 58.2 mm | 104.7 mm |
| guard rejection fraction | 0.003 | 0.607 | 1.000 | 1.000 |

Empty and near-empty looks: **14 fixations produced no native geometry at all**, 33 gave
100 points or fewer; on the guarded side 69 fixations were emptied completely and 73 fell
to 100 or fewer. The rejection fraction has a median of 0.607 but a P90 of 1.000 - the
median fixation loses most of its points and a large minority lose all of them.

The distribution is strongly bimodal rather than uniformly mediocre: 35 fixations sit below
2% validity while 24 sit above 60%.

### Behaviour by range - the single clearest result

| median range | fixations | native pts | guarded pts | rejected | native err median | guarded err median |
|---|---:|---:|---:|---:|---:|---:|
| 0.0-1.5 m | 41 | 320,386 | 319,543 | **0.3%** | **22.7 mm** | 22.3 mm |
| 1.5-2.0 m | 53 | 285,371 | 205,181 | 28.1% | 61.4 mm | 43.1 mm |
| 2.0-2.5 m | 68 | 257,513 | 132,033 | 48.7% | 100.3 mm | 49.7 mm |
| 2.5-3.0 m | 5 | 13,343 | 3,468 | 74.0% | 905.3 mm | 58.6 mm |
| 3.0-4.0 m | 3 | 4,371 | 1,092 | 75.0% | 1784.4 mm | 77.2 mm |
| 4.0-6.0 m | 14 | 28,282 | 5,682 | 79.9% | 2329.3 mm | 97.2 mm |
| **> 6.0 m** | 27 | 33,136 | **0** | **100.0%** | **4838.8 mm** | - |

Inside 1.5 m the unchanged instrument is **already correct**: 0.3% rejection and a 22.7 mm
median, reproducing the sealed Bridge-1R control number exactly. Accuracy then decays
monotonically, and beyond 6 m every one of 33,136 native points is wrong - unsurprising,
since the frozen depth bound is `z_rect [0.75, 4.5] m` and those ranges cannot be
represented at all. The native stream nonetheless emits them.

The extremes agree: the five best fixations (validity 0.820-0.822, 13,441-13,471 points,
22-23 mm, rejection 0.1-0.2%) are all at pitch ~ -89.8 deg, looking straight **down** at the
close floor. The five worst by validity produced **zero** valid pixels and are all at pitch
+74 deg, looking **up** at the ceiling. The worst by error is `fix_177` at
yaw -98.5, pitch -16.8 - a horizontal gaze into room depth - with a **32.3 m** median error
on 109 points.

Inspecting the images explains it: the best fixations show dense textured carpet grain,
while `fix_128` (8.0 m error) is a nearly featureless blurred brown gradient with almost no
matchable detail. This is Bridge-5's conclusion appearing in the real scene - the limiting
variable is absolute match strength, not contrast, gap, or slant.

### Persistent scene construction

| | native | guarded |
|---|---:|---:|
| distinct instance ids observed | 16 | 14 |
| instantiated into persistent maps | 14 | 12 |
| total surfels | **355,830** | **171,361** |
| source points | 942,402 | 666,999 |
| fusion packets | 85 | 67 |
| leftover unfused points below the 100-point floor | 34 | 26 |

Only 16 of the 206 available instance groups were ever seen, because the sealed attention
sequence concentrates on a handful of entities. Every positive id was treated as an ordinary
entity; no role assignment was used.

Resource limits: the busiest object used **17** packets of the 57 available (FSG3's uint64
provenance ceiling is 63), from up to 75 contributing fixations. **No object hit any
provenance or resource limit**, as expected. Two objects fell below the inherited 100-point
FSG3 floor and were reported rather than force-fused: `Plane.004` (8 points) and
`ceiling_pipeHang.002` (26 native / 18 guarded).

Per-object support, sorted by native surfels:

| id | label | native surfels | guarded surfels | kept | native src | rejected |
|---|---|---:|---:|---:|---:|---:|
| 195 | woodBase | 101,063 | 45,093 | 45% | 200,468 | 44.6% |
| 159 | sol (floor) | 60,431 | 56,441 | **93%** | 326,571 | **1.3%** |
| 97 | beams | 43,125 | 14,600 | 34% | 69,943 | 62.0% |
| 173 | wall | 33,224 | 3,667 | **11%** | 43,592 | 88.1% |
| 107 | ceilingAirVent.002 | 33,045 | 21,460 | 65% | 162,333 | 24.3% |
| 130 | corkboard | 27,213 | 4,708 | **17%** | 27,400 | 82.8% |
| 153 | pipe | 26,118 | 22,379 | **86%** | 77,065 | 10.3% |
| 155 | **plank** | 26,010 | **0** | **0%** | 26,759 | **100.0%** |
| 196 | woodBaseboard | 3,169 | 1,603 | 51% | 5,805 | 35.8% |
| 116/115/113 | ceiling_pipeHang | 1,036/679/232 | 698/441/162 | ~67% | - | ~32% |
| 78 | Plane.003 | 268 | 109 | 41% | 268 | 59.3% |
| 4 | **Box280.002** | 217 | **0** | **0%** | 217 | **100.0%** |

Three entities account for 62.5% of all rejected geometry: woodBase 32.5%, beams 15.7%,
ceilingAirVent 14.3%.

**Strongest entities:** the floor `sol` (1.3% rejected, 56,441 guarded surfels) and the
`pipe` (10.3% rejected) - both close and textured. The guarded floor is geometrically
correct: its Y extent is only 0.2 m across 4.3 m of X-Z, a genuinely flat horizontal plane
1.2 m below the eye. Notably the **thin** pipe survives well, because it is close (~2 m).

**Weakest entities:** `plank` and `Box280.002` are **entirely spurious** - 26,010 and 217
native surfels, none of which survive the gate. The native plank spans 14.3 m and reaches
20.2 m of range, a diagonal smear in a classroom. `wall` keeps 11% and `corkboard` 17%.

### Native versus guarded - what the clouds actually look like

**Native (355,830 points, range P50 2.14 m, max 35.42 m, X extent -35.1 to 2.6 m).** The
orthographic views show a **radial starburst**: long spikes emanating from the head origin
in every direction, extending to 35 m. This is the signature of disparity error sliding a
point along its own viewing ray. Correct geometry exists as a dense core near the origin
but is completely swamped. **Yes - native contains gross wrong-depth structure**, and it is
not subtle.

**Guarded (171,361 points, range P50 1.96 m, max 5.20 m, X extent -1.9 to 2.6 m).** The
same views show discrete, compact, **planar slabs** at coherent relative positions, with no
radial structure whatsoever. Individual entities are clean: the guarded `wall` occupies an
X span of 0.1 m - a flat vertical plane - where its native counterpart smears from 1.3 to
7.6 m of range.

So the guarded stream is a **coherent room-scale partial scene**: locally clean, metrically
plausible, correctly arranged - and visibly incomplete, a set of disconnected fragments
rather than a continuous room. That is the honest description.

### Interpretation

Splitting architecture from matcher, the evidence is one-sided.

Working, on the architecture side: the generic evaluated-depsgraph bridge produced a valid
tangent pair for all 225 sealed gazes including yaw 118-129 deg, which Bridge-1 could not
rectify at all before the Bridge-1R tangent-frame canonicalisation. Per-instance 12 mm
fusion ran over 85 packets with zero limit hits, correct floor handling, and verified
idempotence. Truth never entered geometry. No foreground/background decomposition was
needed anywhere, and dropping it cost nothing.

Failing, on the matcher side: 29.2% of points and 52% of fixations' entire yield are
gross-wrong; two whole entities are fabrications; the native cloud is a starburst reaching
eight times the room's size. The failure is systematically organised by **range and surface
texture** - excellent inside 1.5 m, unusable past 6 m, zero on the ceiling - exactly the
weak-match-strength regime Bridge-5 isolated.

The guarded stream is **not** an estimator result and must not be reported as one. It uses
Blender truth to reject, so its 44.6 mm median is an upper bound on what a better matcher
could deliver on this attention sequence, not a measurement of any autonomous system. Its
only purpose is to show that when the bad rows are removed, what remains is a usable scene -
which is evidence about the architecture, not about the matcher.

### What this does not establish

One scene, one sealed attention sequence, one profile, one seed. Nothing about autonomous
attention, discovery, controller behaviour, FSG6f generalisation, or fusion quality beyond
what these 16 entities exercise. 190 of the 206 instance groups were never looked at, so
nothing is claimed about scene completeness. The guarded stream cannot be produced without
truth and is therefore not a deliverable capability. And no threshold here was chosen after
seeing results: the 100 mm gate, the 100-point floor and the 12 mm radius are all inherited.

Nothing was tuned, no matcher parameter touched, no fixation reselected, no repair attempted.
