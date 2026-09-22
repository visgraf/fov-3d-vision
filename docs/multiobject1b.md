# MultiObject-1b — independent growth of object 143

## Question

Can the already-established local FSG6f single-object growth mechanism be transferred to the second foreground entity introduced by MultiObject-1a, while object 141 remains a separate byte-identical entity?

This step adds **growth**, and nothing else.

## Parent

MultiObject-1a introduced two scene entities:

- object 141 — inherited completed surfel map, read-only;
- object 143 — one separate seed surfel patch from one prescribed fixation.

Automatic object discovery, scene scheduling, and second-object completion were all deferred.

## Mechanism

Object 143 is initialized from the saved MultiObject-1a seed acquisition.  Growth then uses `tools/fsg6f_frontier.py` **unchanged**.

FSG6f historically names its target object `141`, so MultiObject-1b uses a pure label adapter for policy input only:

- scene id 143 → frozen FSG6f target label 141;
- every other scene id → non-target.

No geometry or support map is transformed.  The object-143 surfel map itself always contains the real instance id 143.

The adapter lets us reuse the frozen FSG6f frontier extraction, persistent frontier states, strict candidate consensus, projected corridor, 5-degree local saccades, and all numerical constants without copying or retuning the controller.

## History scope

This is deliberately a transfer test, not a retrospective scene-reasoning test.  The object-143 active-growth history starts at its prescribed MultiObject-1a seed observation.  Earlier incidental id-143 observations were used only to choose that seed in 1a; they are not replayed as active-growth history here.

## Empty looks

Reality Check 2b semantics are retained.  A fixation with fewer than 100 reconstructed id-143 points is a valid negative observation:

1. record the binocular observation;
2. fuse no target surface;
3. leave the object-143 map unchanged;
4. let frozen FSG6f decide again.

## Stop

The scientific stop is the frozen policy's own stop (`no_frontier` when that is what it returns).  A 24-object-fixation watchdog, including the 1a seed, is engineering protection only and is not success.

## Scene output

The result remains a two-object scene record:

- object 141 references exactly the inherited read-only surfel source;
- object 143 references the newly grown separate surfel map;
- both are projected onto one shared cyclopean chart.

Footprint overlap is measured, not forbidden.  MultiObject-1a happened to have zero overlap; this experiment does not promote that observation to an invariant.

## Deliberately deferred

- automatic discovery of object 142 or any other object;
- scene-level scheduling;
- cyclopean completion of object 143 after local FSG6f growth;
- layered/occlusion-aware spherical representation;
- mesh reconstruction or interpolation;
- evaluator truth or accuracy gates.

## Interpretation

This experiment is structural.  It asks whether the mature local object-growth mechanism can be reused on a second entity without damaging the first.  Point gain, fixation count, coverage, and geometry statistics are measurements, not PASS thresholds.

## Results

Run attempted 2026-09-21 on the workstation. **`MULTIOBJECT1B_BLOCKED`.** The
experiment did **not** complete and **no status of completion is claimed**. Five
object-143 growth fixations executed faithfully and then the run stopped on a
`RuntimeError` when the **frozen** `reality2_render_fix.py` refused global step
24. **Object 141 and the MultiObject-1a parent are byte-identical afterwards.**

The blocking condition is a **contract-level collision with a frozen dependency,
not an implementation defect**, so under CLAUDE.md - *"Code does not take
decisions the prompt did not delegate: when a decision rule is not met, it stops
and says so"* - it is reported rather than repaired.

### The blocking condition, measured

`tools/reality2_render_fix.py` is a frozen Reality Check 2 source. It admits a
fixation only when

```text
PARENT_FIXATIONS <= step < WATCHDOG_TOTAL_FIXATIONS
```

and `reality2_public` fixes `PARENT_FIXATIONS = 6`,
`WATCHDOG_TOTAL_FIXATIONS = 4 * 6 = 24`. **The renderer therefore accepts global
fixation indices 6 through 23 and nothing else.**

The programme has already consumed global steps **0-18**: Reality Check 1 steps
0-5, Reality Check 2b 6-12, Cyclopean-1c 13, Cyclopean-1e 14, Cyclopean-1f
15-16, Cyclopean-1g 17, MultiObject-1a 18.

MultiObject-1b renders at `global_step = seed_step + len(gazes)` with
`seed_step = 18`, so the only renderable growth steps are **19, 20, 21, 22,
23 - exactly five**. Its own guardrail, `OBJECT2_WATCHDOG_FIXATIONS = 24`, counts
**object-143** fixations including the 1a seed, so the maximum object-143
fixation count physically reachable is **1 + 5 = 6 against a watchdog of 24**.
**The object-scoped watchdog can never be reached**, and the run hits a hard
`ValueError` from the frozen renderer instead of any declared stop.

The two counters are simply different quantities - a **global** acquisition index
versus an **object-scoped** fixation budget - and nothing in the 1b package
reconciles them.

### The scientific stop was far away when the ceiling was hit

This matters for how the truncation should be read, so it was measured rather
than assumed. Replaying the frozen policy read-only against the saved state at
the blocked step returns:

```text
stop = False
reason = 'continue'
next_gaze_deg = [-23.4970979736, 17.059625701199998]
```

with **1,193 open frontier voxels of 1,264** (54 map-resolved, 17
boundary-resolved), 4 candidates before consensus and 0 rejected. **The policy
was still growing normally**; it was nowhere near `no_frontier`, and object 143
had used **6** of its 24-fixation budget. **The run was truncated entirely by the
renderer's global ceiling, not by anything scientific.**

### Why this was not repaired here

Every available remedy is a decision, not a defect repair:

1. **widen the frozen renderer's step range** - forbidden; it is a frozen
   scientific source encoding Reality Check 2's own schedule;
2. **renumber 1b's renders into an object-scoped step space** - changes the
   acquisition-record naming convention the entire ancestry relies on, and would
   make 1b's records non-comparable with every earlier record;
3. **lower `OBJECT2_WATCHDOG_FIXATIONS` to 6** - tuning a policy constant to fit
   the tooling, explicitly forbidden, and it would dress a renderer limit up as a
   scientific budget.

**None was taken.** No frozen source, policy constant, fusion radius, threshold,
scene or matcher was modified; the working tree carries no change to any
scientific source.

### Provenance

Working tree clean. Prospective commit **`2236998`**; pre-package parent
**`267c579`**. The package adds **exactly the seven expected files, all `A`**.
`git diff` against `267c579` over **69 frozen sources** - every FSG1/FSG3/FSG6f
source, renderer, scene, rig, pin file, every Reality Check 1/2/2b source, every
Cyclopean-1a through 1g source and **every MultiObject-1a source** - is **empty
(0 lines)**, all 69 sha256 SAME.

Parent located **by manifest** (`MultiObject1a-second-object-seed-v1`, seed 2111,
profile `full`, `truth_opened` false): exactly one match,
`previews/multiobject1a/full-seed2111`. Pinned before and **re-verified
byte-identical after the failed run**:

| file | sha256 (before == after) |
|---|---|
| 1a `prediction_manifest.json` | `30acca954af1914d…98cb1a4e` |
| 1a `object_143_seed_patch.npz` | `e7e40c16a185a2f9…5f8a7d8c` |
| 1a `scene_graph.json` | `79817b6d2647f45b…890a2376` |
| object-141 source (`cyclopean1g/.../surface_map.npz`) | `6ac98f6251b47337…f71e524a` |

**Object 141 did not change by a single byte, including through the crash.**

### Environment

Blender 5.2.1 LTS headless, Cycles, **OPTIX** on an RTX 4090 (driver 595.84);
host `.venv/bin/python` 3.12.3. **44.2 s wall** to the point of failure, five
Blender launches completed and the sixth refused.

### Checks

`py_compile` clean on all five modules. The three prescribed lines appeared
verbatim:

```text
[multiobject1b-growth] PASS object141_read_only=true object143_only=true frozen_fsg6f=true seed_scoped_history=true empty_evidence=true
[multiobject1b-policy] PASS parent=multiobject1a independent_growth=true auto_discovery=false quality_gated=false
[multiobject1b-check] SUMMARY passed=6 failed=0
```

All six negatives are **genuine source-mutation controls**, each exiting **1**
because the mutation was detected, none exiting 2: `object1grow` →
`object141_read_only`, `crossfuse` → `object143_only_growth`, `copypolicy` →
`frozen_fsg6f_adapter`, `priorhistory` → `seed_scoped_history`, `emptyabort` →
`empty_look_is_evidence`, `autodiscover` → `no_discovery_or_quality_gate`.

**No regression**: all 11 prior suites green and **79 prior negatives** still
firing - multiobject1a 6/6, cyclopean1g/1f/1e/1d/1c/1b/1a 6/6 each, reality2b
7/7 (10/10), reality1 6/6, fsg6f 14/14 (15/15).

### What the five completed growth looks did show

These are **partial measurements from a truncated run**, recorded because they
are informative, not because they complete anything.

| global step | object fixation | gaze (deg) | id-143 points | new surfels | map after |
|---|---|---|---|---|---|
| 18 | 0 (1a seed) | (+1.5029, -7.9404) | 5,344 | - | 5,344 |
| 19 | 1 | (-3.4971, -2.9404) | 4,076 | +2,413 | 7,757 |
| 20 | 2 | (-8.4971, -2.9404) | 5,033 | +3,634 | 11,391 |
| 21 | 3 | (-13.4971, +2.0596) | 1,547 | +1,419 | 12,810 |
| 22 | 4 | (-18.4971, +7.0596) | 1,197 | +1,132 | 13,942 |
| 23 | 5 | (-23.4971, +12.0596) | 1,721 | +1,647 | 15,589 |

- object 143 grew **5,344 → 15,589** surfels (**+10,245, +191.7%**);
- **no empty looks** - every fixation exceeded the inherited 100-point limit, so
  the Reality-2b negative-evidence branch was not exercised;
- **all six gazes distinct**, moving on the frozen 5-degree FSG6f lattice in a
  coherent leftward-and-upward traverse;
- **final instance-id purity is exactly `{143}`** at every saved map from
  `map_18` through `map_23`; the growing map never admitted 141, 142 or 144;
- seed surfels moved by at most **6.32 mm** (median 0.0000, p99 4.85) when later
  looks fused over them - inside the frozen 12 mm radius, so growth did not drag
  the seed;
- final multi-look surfels **1,312**, max support count **3**.

Shared 0.1-degree chart after the five looks: object 141 **37,601** cells
(376.01 deg²), object 143 **6,478** cells (64.78 deg², up from the seed's
**1,670**), **overlap 0**. Object 143 now spans yaw **[-30.72, +6.88]** and pitch
**[-9.80, +17.90]**, wrapping well outside object 141's **[-12.42, +12.68]** x
**[-8.30, +10.40]** - so the zero overlap persisted through growth on this
configuration, though MultiObject-1a's contract already declined to treat that as
an invariant and this run does not either.

### Visual reading, descriptive

The run crashed before writing `object_143_growth.png`, the final PLY and the
scene footprint image, so only the per-fixation previews exist. Across
`rgb/fix_18..23.png` the fovea starts on the seed view - cloth above, the grey
band of object 143 across the middle, brown wood below - and then walks left and
up across a **large, smooth, largely untextured grey surface**. By `fix_22` and
`fix_23` object 141 has left the frame entirely and the view is nearly
featureless grey with a single flat blue panel.

That is visible in the stereo yield: valid pixels collapse
**52,622 → 35,666 → 13,928 → 1,449 → 1,721** across the five looks. **Object 143
looks coherent rather than merely larger** - it is one continuous surface, the
saccades are orderly, and fusion is well behaved - but the frontier is marching
onto texture-free area of exactly the kind Cyclopean-1g documented for the
emblem, at much larger scale.

Two further objects were visible and, correctly, **not instantiated**: **144**
appears at `fix_21` (1,410 valid px) and `fix_22` (252 px), and **142** was
already present in the 1a seed view. Automatic discovery remains deferred, and
the deferral is visible in the measurements.

**Internal coherence is not evaluator accuracy.** No truth was opened, so every
number above describes the representation, not the scene.

### Structural failures

One, and it is the blocking one: **`RuntimeError: MultiObject-1b Blender
fixation 24 failed`**, caused by the frozen renderer raising
`ValueError: Reality Check 2 renders continuation steps only`. No manifest was
written, so `multiobject1b_compare.py` has no record to aggregate and was not
run.

No integrity failure occurred: parent, ancestry and object-141 source are all
byte-identical, purity held at every step, and no evaluator truth was opened.

### Code fixes

**None.** No file was modified. The blocking condition is a contract-level
collision, not a demonstrable implementation defect, and every remedy is a
decision reserved for Luiz/Chat.

### What this establishes, and what it does not

Established, within five looks. **The transfer mechanism itself works.** The
frozen FSG6f controller, reached only through a pure label adapter, drove object
143 from its 1a seed through five orderly 5-degree saccades and **191.7%** surfel
growth, with **exact `{143}` purity at every step**, seed surfels undisturbed
within the frozen radius, and **object 141 byte-identical throughout**. Nothing
in the mechanism resisted being pointed at a second entity.

Not established - and this is the larger part. **The experiment did not run to
its own stop**, so it shows nothing about whether object-143 growth terminates,
converges, or how large the object is; the policy was still returning `continue`
with 1,193 open frontier voxels when the renderer refused. **No empty look
occurred**, so the Reality-2b negative-evidence path is untested here. **No
accuracy claim** is made. **The zero footprint overlap is still not an
invariant** - it survived this truncated growth on this configuration and nothing
more. And the run surfaced a structural fact the contract had not accounted for:
**the frozen Reality-2 renderer caps the whole programme at 24 global fixations,
of which 19 were already spent, so any future multi-object growth experiment has
at most 5 renders left under this acquisition path.** That ceiling, not object
143, is what stopped this run, and resolving it is a design decision for
Luiz/Chat.
