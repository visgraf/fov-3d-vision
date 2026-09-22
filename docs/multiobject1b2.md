# MultiObject-1b2 — resume object-143 growth past the legacy renderer ceiling

## Question

MultiObject-1b transferred the frozen FSG6f local grower to object 143 successfully for five new looks, but the experiment was truncated by `reality2_render_fix.py` at global step 24.  The policy was still returning `continue`; the stop was infrastructural, not scientific.

The next question is deliberately narrow:

> If the five successful MultiObject-1b looks are reused exactly and only the obsolete Reality-2 scheduling gate is removed from acquisition plumbing, does object 143 continue to the frozen policy's own stop or the genuine object-scoped watchdog?

## What changes

One new generic acquisition entry point is introduced: `tools/scene_render_fix.py`.

It preserves the Reality physical instrument:

- same Reality-1 scene and texture;
- same fixed head;
- same camera calibration and vergence;
- same SPP profile;
- same `reality2_public.render_seed(...)` physical-view RNG function;
- same Cycles backend;
- same oracle first-hit instance masks.

It differs in one respect only: it does **not** encode Reality Check 2's experiment-specific admission interval `6 <= step < 24`.

The frozen `reality2_render_fix.py` remains untouched and historically correct.

## Equivalence before flight

Before any new object-143 acquisition, the new renderer is run once at the already-saved global step 23 gaze.  Its calibration and all stored RGB/instance arrays must match the saved legacy acquisition exactly.  Failure blocks the continuation.

This check makes the change an acquisition-plumbing extension rather than a silent instrument change.

## Reuse, do not rerender

The blocked MultiObject-1b record is replayed from disk:

- seed map at global step 18;
- completed growth acquisitions/maps at steps 19–23.

The frozen policy is replayed through that history and must reproduce each saved gaze and each saved object-143 map exactly (float arrays compared at their saved float32 representation).  Those five looks are **not rerendered**.

The first new scientific acquisition is global step 24.  Global chronology is preserved; nothing is renumbered into an object-local step namespace.

## Scientific mechanism

Everything else is MultiObject-1b:

- object 141 remains read-only and byte-identical;
- object 143 alone is fused;
- `multiobject1b_policy.py` is reused unchanged;
- frozen FSG6f is reused unchanged;
- frozen 12 mm association remains unchanged;
- `<100` reconstructed id-143 points remains valid negative evidence, not failure;
- scientific stop is frozen FSG6f `no_frontier`;
- 24 **object-143 fixations including the seed** is the engineering watchdog.

The object-scoped watchdog is explicitly independent of the global acquisition index.

## Deliberately deferred

- automatic discovery of object 142/144 or any other object;
- scene-level scheduling;
- cyclopean completion of object 143;
- layered/occlusion-aware spherical representation;
- interpolation, matcher changes or texture rescue;
- evaluator truth or accuracy gates.

## Interpretation

MultiObject-1b2 is not a new perception experiment.  It is the completion of the interrupted MultiObject-1b experiment after separating a generic scene-acquisition service from the old Reality-2 experimental schedule.

If the continuation reaches the frozen policy stop, the next scientific step is cyclopean completion for object 143.  If the object-scoped watchdog is reached instead, that is recorded descriptively and interpreted separately; the watchdog is not success.

## Results

Run attempted 2026-09-21 on the workstation. **`MULTIOBJECT1B2_BLOCKED` — the
renderer-equivalence gate is unsatisfiable on this platform.** The experiment did
**not** acquire a new scientific view and **no completion is claimed**. The
partial-reuse half of the design worked perfectly; the gate that guards it
cannot pass, and **the frozen legacy renderer cannot pass it either**.

Per the prospective contract — *"If renderer equivalence fails, stop. Do not
loosen exact equality or alter the instrument to force passage"* — the run stops
here and reports. Choosing a comparison tolerance is a scientific decision about
what "the same instrument" means, and it is reserved for Luiz/Chat.

### The replay half worked exactly

Before the gate, the runner replayed the blocked MultiObject-1b record through the
frozen policy and reproduced it **byte for byte**:

| replayed map | object-143 surfels | xyz equal | support equal | ids | byte-identical |
|---|---|---|---|---|---|
| `map_18` (1a seed) | 5,344 | true | true | `{143}` | **true** |
| `map_19` | 7,757 | true | true | `{143}` | **true** |
| `map_20` | 11,391 | true | true | `{143}` | **true** |
| `map_21` | 12,810 | true | true | `{143}` | **true** |
| `map_22` | 13,942 | true | true | `{143}` | **true** |
| `map_23` | 15,589 | true | true | `{143}` | **true** |

**All six maps reproduced exactly**, every one pure id 143, and the five
successful growth looks were **reused, not rerendered** — the partial record's
acquisitions `fix_19`…`fix_23` are untouched and no `fix_24` was created in it.
Global chronology was preserved; nothing was renumbered.

### The renderer-equivalence gate failed — and what actually differs

At the saved global step 23 gaze **(−23.4970979736, +12.0596257012)** the generic
`tools/scene_render_fix.py` was run once and compared with the saved legacy
acquisition:

```text
AssertionError: generic scene renderer failed exact legacy-equivalence check:
calibration=True arrays=False
```

Broken down by array:

| array | shape / dtype | result |
|---|---|---|
| `calibration.json` | — | **exactly equal** |
| `instance_L` | (640, 640) int32 | **bitwise equal** |
| `instance_R` | (640, 640) int32 | **bitwise equal** |
| `rgb_L` | (640, 640, 3) float32 | differs on 582,550 / 1,228,800 (**47.408%**), max &#124;delta&#124; **7.748604e-07** |
| `rgb_R` | (640, 640, 3) float32 | differs on 562,419 / 1,228,800 (**45.770%**), max &#124;delta&#124; **7.748604e-07** |

Both renderers reported the same sample budget, **209,715,200 samples**. The
observation key sets are identical. **Everything deterministic matches exactly** —
calibration, and both oracle first-hit instance masks, which carry the geometry
and the segmentation the experiment actually depends on. The only disagreement is
radiance, at **7.75e-07**, which is **6.5 float32 ulp at 1.0** (ulp at 1.0 is
1.192e-07; at 0.5 it is 5.96e-08).

### The gate cannot be satisfied by any renderer, including the frozen one

That magnitude invited a decisive test, so rather than assume the generic renderer
was at fault the **frozen** `reality2_render_fix.py` was re-run at the same step 23
and the same gaze — written only into the session scratchpad, leaving the record
untouched — and compared against **its own saved output**:

| comparison | `rgb_L` differing | `rgb_R` differing | max &#124;delta&#124; | `instance_L/R` |
|---|---|---|---|---|
| saved legacy vs **generic** | 47.408% | 45.770% | 7.748604e-07 | **bitwise equal** |
| saved legacy vs **legacy re-render** | **47.458%** | **45.669%** | 7.152557e-07 / 8.344650e-07 | **bitwise equal** |
| generic vs legacy re-render | 47.212% | 45.563% | 8.344650e-07 | **bitwise equal** |

**The frozen renderer does not reproduce its own saved RGB bit-exactly**, and it
misses by the same fraction of pixels and the same ~6–8 ulp magnitude as the
generic renderer does. Its calibration re-matched exactly, and its instance masks
were bitwise identical in every pairing.

So Cycles/OPTIX radiance accumulation on this platform is **not bit-deterministic
across processes** at the ~6–8 ulp level, presumably from GPU accumulation or
scheduling order. The gate as written compares all observation arrays with
`np.array_equal`, so **it is testing GPU bit-determinism rather than renderer
equivalence**, and no renderer can pass it — not the new one, and not the frozen
one it is meant to be validated against.

**This is a defect in the gate's exactness criterion, not evidence that the
instrument changed.** On every quantity that is reproducible at all, the two
renderers agree exactly.

### Why nothing was changed

The contract forbids exactly the move that would make this pass, and the
alternatives are all decisions rather than defect repairs:

1. **loosen the comparison to a tolerance** — explicitly forbidden ("do not
   loosen exact equality"), and the tolerance would be a new numerical constant
   defining instrument identity;
2. **compare only the deterministic arrays** (calibration + instance masks, which
   already match bitwise) — a narrower and defensible gate, but it redefines what
   the equivalence check asserts;
3. **force determinism** (CPU backend, fixed tile/thread scheduling, different
   sample accumulation) — alters the instrument, forbidden;
4. **re-render steps 19–23 with the generic renderer** so the comparison is
   self-consistent — forbidden, and it would discard the reuse the experiment
   exists to demonstrate.

**None was taken. No file was modified**; the working tree carries no change to
any source, frozen or new.

### Provenance

Working tree clean. Prospective commit **`c0d2fc2`**; pre-package parent
**`ea873ed`** (the blocked MultiObject-1b documentation commit). The package adds
**exactly the seven expected files, all `A`**, including the explicitly authorized
new entry point `tools/scene_render_fix.py`. `git diff` against `ea873ed` over
**58 frozen sources** — every FSG1/FSG3/FSG6f source, scene, rig, pin file, every
Reality Check 1/2/2b source, every Cyclopean-1a..1g source and every
MultiObject-1a/1b source — is **empty (0 lines)**, all 58 sha256 SAME. **The
frozen `reality2_render_fix.py` is untouched at `9f1433d189fbcbb5…`.**

The new renderer's instrument delegation was inspected rather than assumed: it
takes `VERGENCE_DISTANCE_M`, `DEFAULT_SPP`, `SEEDS` and the physical-view RNG
`render_seed(...)` from `reality2_public`, the scene and texture from
`reality1_scene`, and calls the same `make_calibration(...)` and
`base.check_renderer_equivalence()`. Its only substantive difference is that
`step` is required to be non-negative instead of lying in `6 <= step < 24`.

Inputs located **by manifest**: exactly one `MultiObject1a-second-object-seed-v1`
record at seed 2111, profile `full`, `truth_opened` false. The blocked partial
record was verified to be the reported one — **no completed
`prediction_manifest.json`**, maps **18–23 contiguous** with no later map,
completed acquisitions **19–23** with **no acquisition 24**, all maps pure id 143,
and the diagnostic step-24 render log present.

**All 15 pinned inputs are byte-identical after the failed run** — the three 1a
files, the six partial maps, the five partial patches, and the object-141 source
`6ac98f6251b47337…f71e524a`. **Object 141 did not change by a single byte.**

### Environment

Blender 5.2.1 LTS headless, Cycles, **OPTIX** on an RTX 4090 (driver 595.84);
host `.venv/bin/python` 3.12.3. **9.9 s wall** to the gate failure (one generic
render), plus one scratchpad diagnostic re-render with the frozen renderer.

### Checks

`py_compile` clean on all five modules. The three prescribed lines appeared
verbatim:

```text
[multiobject1b2-resume] PASS partial_reuse=true renderer_equivalence=true global_history_preserved=true object143_only=true
[multiobject1b2-policy] PASS frozen_fsg6f=true object_scoped_watchdog=true auto_discovery=false quality_gated=false
[multiobject1b2-check] SUMMARY passed=6 failed=0
```

All six negatives are **genuine source-mutation controls**, each exiting **1**
with its detector named and **none exiting 2**: `globalcap` →
`generic_renderer_no_global_cap`, `instrument` → `physical_instrument_frozen`,
`rerenderpartial` → `partial_history_reused_not_rerendered`, `noequivalence` →
`renderer_equivalence_required`, `crossfuse` →
`object141_read_only_object143_only`, `globalwatchdog` →
`object_scoped_watchdog_no_discovery`.

**No regression**: all 12 prior suites green and **85 prior negatives** still
firing — multiobject1b 6/6, multiobject1a 6/6, cyclopean1g/1f/1e/1d/1c/1b/1a 6/6
each, reality2b 7/7 (10/10), reality1 6/6, fsg6f 14/14 (15/15).

### What was not reached

Because the gate blocks before any new acquisition, none of the following
happened and none is reported as a measurement: **the first new global step 24 was
never acquired**; object 143 remains at its resumed **15,589** surfels; there is
no new fixation sequence, no termination reason, no empty look, no per-new-look
fusion or idempotence figure, and no new scene footprint or growth visual. The
frozen policy's own stop and the 24-object-fixation watchdog were both untested.
`multiobject1b2_compare.py` has no completed record to aggregate and was not run.

The object-143 state carried into the blocked run is unchanged from
MultiObject-1b: **15,589 surfels, pure `{143}`**, with the policy last known to
return `continue` and 1,193 open frontier voxels of 1,264 — still far from
`no_frontier`, and still at **6 of 24** object-scoped fixations.

### Structural failures

One, and it is the blocking one: the renderer-equivalence `AssertionError` above.
**No integrity failure**: all 15 pinned inputs byte-identical, object 141
unchanged, no `fix_24` created anywhere, the partial record's acquisitions
untouched, all replayed maps pure id 143, and no evaluator truth opened.

### Code fixes

**None.** No file was modified.

### What this establishes, and what it does not

Established. **The reuse mechanism is exact.** Replaying the blocked
MultiObject-1b record through the frozen policy reproduced all six object-143
maps **byte-identically**, ids pure `{143}` throughout, with the five successful
looks reused rather than rerendered and global chronology preserved. That half of
the design needs nothing further.

Also established, and this is the substantive finding: **the two renderers are
equivalent on every quantity this platform reproduces at all** — calibration
exactly equal, both oracle first-hit instance masks bitwise equal, same
209,715,200-sample budget — while **radiance is not bit-reproducible even by the
frozen renderer against its own saved output**, missing by ~6–8 ulp on ~46–47% of
float32 values in every pairing tested. The equivalence gate therefore measures
GPU bit-determinism rather than instrument identity, and **cannot be satisfied by
any renderer, including the one it validates against**.

Not established. **Nothing about object-143 growth past step 23.** The experiment
acquired no new view, so it says nothing about whether object 143 reaches
`no_frontier`, whether it hits the object-scoped watchdog, how the low-texture
surface behaves under continued growth, or whether measurement deficit appears —
all of which were the actual scientific questions. **No accuracy claim** is made;
no truth was opened, and internal coherence is not evaluator accuracy. And
**nothing here licenses a tolerance**: that the frozen renderer also fails the
exact test shows the criterion is wrong, not what the right criterion is.

**Resolution is a design decision for Luiz/Chat** — narrow the gate to the
deterministic arrays that already match bitwise, adopt an explicit and justified
radiance tolerance, or require a deterministic render configuration. The
continuation is otherwise ready: the reuse path is proven exact and the only
obstacle is how instrument identity should be tested.
