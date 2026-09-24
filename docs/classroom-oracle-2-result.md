# Classroom-Oracle-2 — boundary ablation result

## Branch and commits

| item | value |
|---|---|
| branch | `classroom-oracle-2` |
| baseline / required ancestor | `f9fb196` CLASSROOM_ORACLE1_COMPLETE (direct parent) |
| package | `f303f24` Add Classroom Oracle 2 boundary ablation |
| result commit | this document |

`git diff --check` clean, tree clean, `f9fb196` verified as an ancestor with nothing
interposed.

## Acceptance

```text
[classroom-oracle2-check] SUMMARY passed=15 failed=0
```

All six Oracle-2 modules compile. **No mechanical repair was required in this session** —
the package ran as delivered.

### Domain-override audit (the one thing that could have silently broken)

Several inherited `*_public.py` modules take an **import-time copy**
(`SURFACE_FRONTIER = dict(frozen.SURFACE_FRONTIER)`), including `multiobject2c_public`,
which is on the live controller path. A copy taken before the override would have left the
policy reading +-25/+-20 while the manifest claimed +-35/+-30.

I tested this empirically rather than reasoning about it. `apply_wide_domain()` mutates
`fsg6f_public.SURFACE_FRONTIER` **in place** and runs before `import classroom_oracle1_run`,
which is what triggers the `multiobject2c_public` import; the copy is therefore made from
the already-widened dict. Measured after the live import order:

```text
fsg6f_public         yawmin=-35.0 yawmax=+35.0 pitchmin=-30.0 pitchmax=+30.0
multiobject2c_public yawmin=-35.0 yawmax=+35.0 pitchmin=-30.0 pitchmax=+30.0
```

`classroom_oracle1_epistemic` (Cyclopean) and `fsg6f_frontier` both read the config at call
time, so they see it too. The override's own audit reports `changed_keys` equal to exactly
the four bounds and `only_domain_extent_changed: true`. Grid spacing, frontier ranking,
corridor rules, thresholds, consensus rules and fusion are untouched.

## Baseline verification

Read from the Oracle-1 files, not from the prompt: `control_complete=true`, `smoke=false`,
25 objects attempted, 104 fixations summed from the manifest,
`dense_evaluation_truth_opened_during_control=false`, seed domain yaw [-25, 25] /
pitch [-20, 20], and 25 `final_map.npz` present.

## Smoke — `previews/classroom-oracle-2-smoke`

```text
[classroom-oracle2] COMPLETE {"fixations": 5, "looks_outside_original_domain": 0,
  "objects": 4, "post_seed_looks": 1, "smoke": true,
  "terminations": {"attention_complete": 3, "smoke_budget": 1}}
```

`smoke_gate.status = PASS_CONTROLLER_TRANSITION_EXERCISED`, primaries [107, 108] retained,
4 objects examined, instance **110 `beams`** exercising the controller transition
(`action_source=fsg6f`). All seven required conditions were verified independently of the
manifest flags: 25 targets; **seed gazes value-for-value identical to Oracle-1 with zero
differences**; active domain +-35/+-30; post-seed sources `{fsg6f: 1}` and no
Blender-selected gaze; dense truth unopened; no foreground/background decomposition; and all
5 fixations inside the widened domain.

## Full ablation — `previews/classroom-oracle-2-full`

```text
[classroom-oracle2] COMPLETE {"fixations": 159, "looks_outside_original_domain": 52,
  "objects": 25, "post_seed_looks": 134, "smoke": false,
  "terminations": {"attention_complete": 22, "watchdog_24": 3}}
```

| quantity | Oracle-1 | Oracle-2 |
|---|---:|---:|
| target instances | 25 | 25 (identical IDs and seeds) |
| total fixations | 104 | **159** |
| oracle_seed / fsg6f / cyclopean_epistemic | 25 / 53 / 26 | 25 / **94** / **40** |
| post-seed looks, all controller-selected | 79 | **134** |
| looks outside the old +-25/+-20 domain | n/a | **52** |
| `attention_complete` | 25 | 22 |
| `watchdog_24` | **0** | **3** (`sol`, `wall.008`, `woodBase`) |

The controller used the extra room: 52 of 134 post-seed looks went outside the old domain,
and the effort rose 53%. Three objects that previously self-terminated now exhausted the
inherited 24-look budget.

## Scope A — the controlled comparison, identical +-25/+-20 samples

| quantity | value |
|---|---:|
| reachable samples | 29,288 |
| Oracle-1 coverage | 0.874693 (25,618) |
| **Oracle-2 coverage** | **0.875239 (25,634)** |
| change | **+0.000546 fraction points** |
| Oracle-1 misses | 3,670 |
| **misses recovered** | **61 = 1.66%** |
| baseline hits regressed | 45 |
| net | **+16 samples** |

Uncovered fraction by distance to the **old** edge, on the identical samples:

| band | Oracle-1 | Oracle-2 |
|---|---:|---:|
| 0-1 deg | 0.2610 | **0.2685** |
| 1-2 deg | 0.2044 | 0.2077 |
| 2-4 deg | 0.2007 | 0.1905 |
| 4-6 deg | 0.1896 | 0.1897 |
| 6-10 deg | 0.0896 | **0.0896** |
| >10 deg | 0.0313 | **0.0313** |

Interior (>6 deg of the old edge): 0.9437 -> 0.9501. Within 6 deg of the old edge:
0.7906 -> **0.7900**.

**The old boundary gradient did not flatten.** The band within one degree of the old edge —
now a full 10 degrees inside the widened domain — is still 26.9% uncovered, marginally worse
than before. The outer bins are identical to four decimal places.

## Scope B — widened +-35/+-30 samples, same 25 targets

| quantity | value |
|---|---:|
| reachable target samples | 54,831 |
| coverage | **0.715599** (39,237 covered, 15,594 uncovered) |
| interior (>6 deg of the **new** edge) | 0.8110 |
| within 6 deg of the new edge | **0.4820** |

| band from new edge | samples | uncovered fraction |
|---|---:|---:|
| 0-1 deg | 2,643 | **0.5199** |
| 1-2 deg | 2,697 | 0.4972 |
| 2-4 deg | 5,107 | 0.5463 |
| 4-6 deg | 4,856 | 0.5049 |
| 6-10 deg | 10,240 | 0.3890 |
| >10 deg | 29,288 | **0.1248** |

A fresh boundary gradient appears at the new edge, steeper than the old one. The widened
domain also exposed 42 visible instances in total, 17 of them non-target; those were treated
as evaluation context and never added to the target list.

## Per-object

| id | name | O1 fix | O2 fix | outside | O1 cov | O2 cov | misses | recovered | regressed | termination |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 224 | woodBase | 19 | 24 | 8 | 99.95% | 99.27% | 3 | 0 | **45** | watchdog_24 |
| 210 | wall.008 | 19 | 24 | 5 | 93.14% | 93.14% | 404 | 0 | 0 | watchdog_24 |
| 111 | blackBoard | 12 | 18 | 6 | 100.00% | 100.00% | 0 | 0 | 0 | attention_complete |
| 234 | worldMap | 7 | 7 | 0 | 100.00% | 100.00% | 0 | 0 | 0 | attention_complete |
| **178** | **sol** | 6 | **24** | **17** | 59.68% | **62.04%** | 1,043 | **61 (5.85%)** | 0 | watchdog_24 |
| 166 | lettersPlank | 4 | 4 | 0 | 68.84% | 68.84% | 382 | **0** | 0 | attention_complete |
| 225 | woodBaseboard | 2 | 2 | 0 | 39.04% | 39.04% | 634 | **0** | 0 | attention_complete |
| 202 | wall | 5 | 11 | 5 | 99.30% | 99.30% | 7 | 0 | 0 | attention_complete |
| 115 | boardFrame | 3 | 3 | 0 | 55.58% | 55.58% | 342 | **0** | 0 | attention_complete |
| 201 | verticalPipe | 6 | 6 | 0 | 97.29% | 97.29% | 17 | 0 | 0 | attention_complete |
| 174 | plank | 2 | 2 | 0 | 56.76% | 56.76% | 259 | **0** | 0 | attention_complete |
| 140 | coat 1 | 2 | 2 | 0 | 87.65% | 87.65% | 50 | 0 | 0 | attention_complete |
| 123 | ceilingMoulding | 1 | 1 | 0 | 17.07% | 17.07% | 306 | **0** | 0 | attention_complete |
| 112 | blackBoardLamp | 3 | 3 | 0 | 76.98% | 76.98% | 61 | 0 | 0 | attention_complete |
| 110 | beams | 3 | 16 | 9 | 100.00% | 100.00% | 0 | 0 | 0 | attention_complete |
| 113 | blackBoard_upPart | 1 | 1 | 0 | 46.48% | 46.48% | 76 | 0 | 0 | attention_complete |
| 109 | alphabet | 1 | 1 | 0 | 32.93% | 32.93% | 55 | 0 | 0 | attention_complete |
| 114 | blackboardLamp | 1 | 1 | 0 | 41.51% | 41.51% | 31 | 0 | 0 | attention_complete |
| 167/168/216/116/172/107/108 | (small) | 1 | 1-2 | 0-1 | 100.00% | 100.00% | 0 | 0 | 0 | attention_complete |

### The decisive observation

**Nine objects have byte-identical trajectories between Oracle-1 and Oracle-2** — same
gazes, same action sources, same termination — including **five of the six principal
Oracle-1 deficit objects**: `woodBaseboard`, `ceilingMoulding`, `lettersPlank`,
`boardFrame`, `plank` (and also `alphabet`, `blackBoard_upPart`, `blackboardLamp`,
`blackBoardLamp`). They did not take a single look outside the old domain. Given ten more
degrees in every direction, the controller **did not want them**: its frontier and shoreline
tests were already empty inside the old domain, and it declared `attention_complete` at
exactly the same point with exactly the same territory unseen.

`sol` is the sole deficit object that behaved differently, and it is instructive. Its first
six looks are identical to Oracle-1 — (7.5, -18.0) seed, four FSG6f looks, then the
Cyclopean handoff to (-0.1, -19.2). In Oracle-2 it then continues past the old boundary:
(-0.1, -24.2), (-5.1, -29.2), (-10.1, -29.2), (-15.1, -29.2), (-20.1, -29.2), (-25.1, -29.2)
— marching along the new pitch floor. It spent 18 extra looks, hit the 24-look watchdog, and
more than doubled its map (82,472 -> 195,218 surfels) — yet recovered only **61 of 1,043**
old-domain misses. The extra budget went into **new** territory, not into closing the
interior holes.

`woodBase` is the only regression of note: given more room it also ran to the watchdog and
lost 45 previously covered samples (99.95% -> 99.27%), the entire regression count of the
experiment.

## Interpretation

Of the four possibilities set out in the prompt, the result is **mixed, with one component
clearly dominant**:

1. **"Old holes recovered — the field was too tight." REJECTED.** 1.66% recovery, +0.0005
   coverage, and five of six deficit objects with byte-identical trajectories. The
   +-25/+-20 field was not the cause of the Oracle-1 deficit.
2. **"Old holes persist even though now interior." CONFIRMED, and this is the decisive
   finding.** The band within one degree of the old edge is now 10 degrees interior and is
   still 26.9% uncovered; the 6-10 deg and >10 deg bins are identical to four decimals. The
   limiter is the frontier/shoreline **eligibility** rule, not the domain extent.
3. **"Misses migrate to the new boundary." ALSO PRESENT.** A fresh and steeper gradient
   appears at +-35/+-30: 0.52 uncovered in the first degree against 0.125 beyond ten. A
   generic finite-domain boundary effect is real — but it is an additional phenomenon, not
   an explanation of the original deficit, because the original region did not improve when
   it stopped being a boundary.

So the Oracle-1 boundary correlation was largely **coincidental**: the surfaces that ran out
of the domain are the same extended, thin, grazing surfaces (`sol`, `woodBaseboard`,
`ceilingMoulding`, `plank`, `boardFrame`, `lettersPlank`) on which the frontier and
shoreline tests go empty early. Widening the domain separates the two and shows the
eligibility rule, not the extent, carries the deficit.

A second, quieter result: more domain is not free. Fixations rose 53%, three objects
converted from self-termination to watchdog exhaustion, and one object regressed. Where the
controller did use the extra room it extended outward rather than completing what it had.

## Next decision — not taken here

The indicated next probe is the frontier/shoreline eligibility rule itself: why FSG6f
reports zero open frontier cells and the Cyclopean audit zero eligible
`NEVER_OBSERVED + EXTERIOR` shoreline cells while substantial contiguous target surface
remains unobserved on exactly these extended surfaces. That requires changing a decision
rule, so it is Luiz/Chat's call and nothing was changed here.

## Demo

Produced by `tools/classroom_oracle2_demo.py` after control, post hoc, with no demo product
fed back to the controller. Panel 1 uses a real Blender RGB panorama rendered with the
established `tools/preview360.py` at the fixed head (`--width 2048 --spp 64 --device OPTIX
--denoise`); that render independently reconfirmed the Oracle-1 seed diagnosis, logging
`removed fcurve on cycles.seed in action 'SceneAction'`.

```text
previews/classroom-oracle-2-full/demo/Demo.md
previews/classroom-oracle-2-full/demo/overview.png
previews/classroom-oracle-2-full/demo/panoramas/{rgb_observed,depth_reference,instance_reference,coverage_comparison}.png
previews/classroom-oracle-2-full/demo/pointclouds/scene_final.ply        (1,340,050 points)
previews/classroom-oracle-2-full/demo/pointclouds/instance_XXXX.ply      (25 files)
previews/classroom-oracle-2-full/demo/frames/frame_0000..0158.png        (159 frames)
previews/classroom-oracle-2-full/demo/classroom-oracle-2-demo.mp4        (1280x754 @ 4 fps, 159 frames)
```

MP4 encoding **was** available and the video was written. Frames inspected at the beginning
(`frame_0002`, object 109 `alphabet` seed), middle (`frame_0080`, object 178 `sol` look 20,
`fsg6f`, gaze (-19.40, -20.70)) and end (`frame_0157`, object 234 `worldMap`,
`cyclopean_epistemic`). All four panels render correctly: the Blender reference panorama,
the left/right tangent pair with visible horizontal parallax, the Cyclopean angular state
with the white rectangle marking the old domain inside the widened one, and the accumulating
3-D reconstruction, which by the final frames is a coherent room-scale cloud.

`frame_0080` is the single clearest image of the result: `sol`'s gaze trajectory is drawn
marching out of the white old-domain rectangle to (-19.40, -20.70) while red uncovered
territory persists both inside and outside it. `panoramas/coverage_comparison.png` shows
Scope A directly — overwhelmingly gray (covered by both) with substantial red (missed by
both) and almost no green (recovered).

## Artifact paths

```text
previews/classroom-oracle-2-full/manifest.json
previews/classroom-oracle-2-full/evaluation.json
previews/classroom-oracle-2-full/bootstrap/seeds.json
previews/classroom-oracle-2-full/objects/instance_XXXX/result.json
previews/classroom-oracle-2-full/objects/instance_XXXX/acquisitions/fix_NN/{raw_L,raw_R}.exr
previews/classroom-oracle-2-full/objects/instance_XXXX/benchmark/fix_NN_{L,R}.png
previews/classroom-oracle-2-smoke/                 (integration gate)
previews/classroom-oracle-1-full/                  (baseline, untouched)
```

All of `previews/` remains gitignored.
