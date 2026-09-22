# MultiObject-1b2 — resume object-143 growth past the legacy renderer ceiling

## Status of this revision

The first MultiObject-1b2 attempt stopped before global step 24 because its renderer-equivalence gate required bitwise equality of stored RGB arrays. Workstation evidence showed that this criterion is unsatisfiable on the current Blender/Cycles/OPTIX platform: the frozen legacy renderer, rerun at the same saved gaze with the same sample budget and configuration, also fails to reproduce its own saved RGB bit-for-bit, while calibration and both oracle instance masks remain exact.

This revision corrects **the equivalence specification only**. It is not a new scientific experiment and it does not change the perception/control mechanism.

The distinction is now explicit:

- **bit reproducibility** is required for quantities that this instrument reproduces deterministically;
- **instrument reproducibility** is established by exact configuration/provenance plus deterministic geometry/segmentation outputs;
- RGB re-render differences from Cycles/OPTIX are measured and recorded, but are not treated as an identity gate.

No RGB epsilon or post-hoc tolerance is introduced.

### Evidence from the blocked first attempt (`c588700`)

At the saved step-23 gaze, calibration and both 640x640 integer instance masks were bitwise identical between the generic renderer and the saved legacy acquisition. The RGB arrays differed at 47.408% (left) and 45.770% (right) of float32 elements, with maximum absolute difference `7.748604e-07`. Crucially, rerunning the **frozen legacy renderer itself** against its own saved acquisition produced essentially the same behavior: 47.458% / 45.669% differing RGB elements with maximum differences `7.15e-07` / `8.34e-07`, while the instance masks remained bitwise exact. This is the empirical reason the old RGB-byte gate is removed.

## Question

MultiObject-1b transferred the frozen FSG6f local grower to object 143 successfully for five new looks, but the experiment was truncated by `reality2_render_fix.py` at global step 24. The policy was still returning `continue`; the stop was infrastructural, not scientific.

The question remains unchanged:

> If the five successful MultiObject-1b looks are reused exactly and only the obsolete Reality-2 scheduling gate is removed from acquisition plumbing, does object 143 continue to the frozen policy's own stop or the genuine object-scoped watchdog?

## What changes

One generic acquisition entry point is used: `tools/scene_render_fix.py`.

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

## Corrected equivalence before flight

Before any new object-143 acquisition, the generic renderer is run once at the already-saved global step-23 gaze.

The following are blocking exact checks:

1. calibration JSON object equality;
2. exact selected acquisition-contract fields: source/backend identity, fixture, profile, gaze, SPP, left/right render seeds, Blender version, device, sample-budget fields, adaptive-sampling flag and segmentation contract;
3. identical observation keys, shapes and dtypes;
4. bitwise-identical left/right oracle instance masks.

RGB arrays are **not** required to be bitwise identical. Instead the run records, separately for `rgb_L` and `rgb_R`:

- whether they happen to be bitwise equal;
- number and fraction of differing elements;
- maximum absolute difference;
- mean absolute difference;
- RMS difference;
- p99 absolute difference.

Those RGB values are descriptive measurements only. There is no RGB tolerance, epsilon or quality threshold.

This is justified by the preceding blocked run, where the frozen legacy renderer itself differed from its own saved RGB by the same ~ulp-scale while calibration and instance masks reproduced exactly. Therefore RGB bit equality was measuring GPU accumulation determinism rather than instrument identity.

## Reuse, do not rerender

The blocked MultiObject-1b record is replayed from disk:

- seed map at global step 18;
- completed growth acquisitions/maps at steps 19–23.

The frozen policy is replayed through that history and must reproduce each saved gaze and each saved object-143 map exactly at saved float32 representation. Those five looks are **not rerendered**.

The first new scientific acquisition is global step 24. Global chronology is preserved; nothing is renumbered into an object-local step namespace.

## Scientific mechanism

Everything else is unchanged from MultiObject-1b:

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

MultiObject-1b2 remains the completion of the interrupted MultiObject-1b experiment. The specification correction removes an impossible reproducibility demand without adding a numerical tolerance and without changing any scientific control variable.

If the continuation reaches the frozen policy stop, the next scientific step is cyclopean completion for object 143. If the object-scoped watchdog is reached instead, that is recorded descriptively and interpreted separately; the watchdog is not success.

## Results — corrected run (revision 2)

Run 2026-09-21 on the workstation into `previews/multiobject1b2-r2/full-seed2111`.
**`MULTIOBJECT1B2_COMPLETE` structurally, `structural_fails: []` — but the
termination is `object2_watchdog` with `scientific_stop_reached: false`.** The
corrected equivalence gate passed, the interrupted experiment resumed exactly,
and object 143 grew through 18 new looks to the 24-object-fixation guardrail.
**The watchdog is not success**: the frozen policy returned `continue` at every
one of its 24 decisions and never reached `no_frontier`.

The **first blocked run is preserved untouched** at
`previews/multiobject1b2/full-seed2111` (14 files, equivalence observation
byte-identical), and its evidence remains in the `docs/log.md` entry for
`c588700`.

### Provenance

Working tree clean. Correction commit **`9bbfbff`**; the prior blocked result is
**`c588700`**. The correction modifies only the five MultiObject-1b2 files plus
its two docs, and **does not touch `tools/scene_render_fix.py`**, which is
unchanged at `6e70bbb78c1043ec…`. `git diff` against `c588700` over **59 frozen
sources** — every FSG1/FSG3/FSG6f source, scene, rig, pin file, every Reality
Check 1/2/2b source, every Cyclopean-1a..1g source, every MultiObject-1a/1b
source **and the generic renderer** — is **empty (0 lines)**, all 59 sha256 SAME.
The frozen `reality2_render_fix.py` remains at `9f1433d189fbcbb5…`.

Inputs located **by manifest**: exactly one
`MultiObject1a-second-object-seed-v1` record at seed 2111, profile `full`,
`truth_opened` false. The blocked MultiObject-1b partial was re-audited as the
reported one — no completed `prediction_manifest.json`, maps **18–23
contiguous**, acquisitions **19–23**, **no acquisition 24**, all maps pure id 143.

**All 16 pinned items are byte-identical after the run** — the three 1a files,
six partial maps, five partial patches, the object-141 source
`6ac98f6251b47337…f71e524a`, and the first blocked 1b2 equivalence observation.
**Object 141 did not change by a single byte** (`object_1_sha256_before` ==
`object_1_sha256_after`).

### Environment and wall time

Blender 5.2.1 LTS headless, Cycles, **OPTIX** on an RTX 4090 (driver 595.84);
host `.venv/bin/python` 3.12.3. **2 m 44 s total**, of which **154.3 s** was the
growth loop after resume — 19 Blender launches (one equivalence re-render plus 18
new fixations).

### Checks

`py_compile` clean on all five modules. The three prescribed lines appeared
verbatim:

```text
[multiobject1b2-resume] PASS partial_reuse=true renderer_equivalence=true global_history_preserved=true object143_only=true
[multiobject1b2-policy] PASS frozen_fsg6f=true object_scoped_watchdog=true auto_discovery=false quality_gated=false
[multiobject1b2-check] SUMMARY passed=6 failed=0
```

All **seven** negatives are genuine source-mutation controls, each exiting **1**
with its detector named and **none exiting 2** — including the new `rgbgate`
control, which fails if an RGB tolerance is reintroduced:

| negative | rc | detected by |
|---|---|---|
| `globalcap` | 1 | `generic_renderer_no_global_cap` |
| `instrument` | 1 | `physical_instrument_frozen` |
| `rerenderpartial` | 1 | `partial_history_reused_not_rerendered` |
| `noequivalence` | 1 | `renderer_equivalence_required` |
| **`rgbgate`** | 1 | `renderer_equivalence_required` |
| `crossfuse` | 1 | `object141_read_only_object143_only` |
| `globalwatchdog` | 1 | `object_scoped_watchdog_no_discovery` |

**No regression**: all 12 prior suites green and **85 prior negatives** still
firing — multiobject1b 6/6, multiobject1a 6/6, cyclopean1g/1f/1e/1d/1c/1b/1a 6/6
each, reality2b 7/7 (10/10), reality1 6/6, fsg6f 14/14 (15/15).

### Corrected renderer equivalence at step 23

Criterion revision `deterministic-instrument-contract-v2`, at the saved gaze
**(−23.4970979736, +12.0596257012)**. **All five blocking deterministic checks
passed exactly:**

| blocking check | result |
|---|---|
| `calibration_exact` | **true** |
| `acquisition_contract_exact` | **true** |
| `observation_keys_exact` | **true** |
| `observation_shape_dtype_exact` | **true** |
| `instance_arrays_exact` (`instance_L`, `instance_R`) | **true / true** |

RGB was recorded as a **diagnostic, never a gate** —
`rgb_is_diagnostic_not_gate: true`, `rgb_tolerance_used: false`:

| eye | bitwise equal | differing elements | fraction | max abs | mean abs | rms | p99 abs |
|---|---|---|---|---|---|---|---|
| `rgb_L` | false | 582,747 / 1,228,800 | 47.424% | 7.152557e-07 | 4.431207e-08 | 7.689193e-08 | 2.384186e-07 |
| `rgb_R` | false | 562,015 / 1,228,800 | 45.737% | 7.152557e-07 | 4.265641e-08 | 7.552280e-08 | 2.384186e-07 |

`passed: true`. The magnitudes confirm the prior diagnosis quantitatively: **mean
absolute difference 4.43e-08 is below one float32 ulp at 1.0** (1.192e-07), and
p99 is exactly **2 ulp**. This is accumulation noise, not a different image —
and the previous run established that the frozen renderer misses its own saved
RGB by the same order while its instance masks reproduce bitwise.

### Partial replay of steps 18–23

`partial_fixations_rerendered: 0`, `global_history_renumbered: false`,
`reused_partial_fixations_total: 6`, `reused_global_steps: [18,19,20,21,22,23]`.
The five successful MultiObject-1b looks and the 1a seed were **reused, not
rerendered**; the partial record's `fix_19`…`fix_23` are untouched and no
`fix_24` was created in it. Replay through the frozen policy reproduced each
saved map, and every one of maps 18–23 in this record is pure id 143.

### The full object-143 fixation sequence

`first new global step = 24`, exactly as required. Twenty-four object-143
fixations: **6 reused** (global 18–23) and **18 new** (global **24–41**).

| g.step | obj # | source | gaze (yaw, pitch) | id-143 pts | new | matched | idem | map |
|---|---|---|---|---|---|---|---|---|
| 18 | 0 | 1a seed | (+1.5029, −7.9404) | 5,344 | 5,344 | 0 | true | 5,344 |
| 19 | 1 | reused | (−3.4971, −2.9404) | 4,076 | 2,413 | 1,663 | true | 7,757 |
| 20 | 2 | reused | (−8.4971, −2.9404) | 5,033 | 3,634 | 1,399 | true | 11,391 |
| 21 | 3 | reused | (−13.4971, +2.0596) | 1,547 | 1,419 | 128 | true | 12,810 |
| 22 | 4 | reused | (−18.4971, +7.0596) | 1,197 | 1,132 | 65 | true | 13,942 |
| 23 | 5 | reused | (−23.4971, +12.0596) | 1,721 | 1,647 | 74 | true | 15,589 |
| 24 | 6 | generic | (−23.4971, +17.0596) | 1,360 | 1,202 | 158 | true | 16,791 |
| 25 | 7 | generic | (−18.4971, +17.0596) | 1,231 | 1,080 | 151 | true | 17,871 |
| 26 | 8 | generic | (−13.4971, +17.0596) | 964 | 914 | 50 | true | 18,785 |
| 27 | 9 | generic | (−8.4971, +17.0596) | 932 | 889 | 43 | true | 19,674 |
| 28 | 10 | generic | (−3.4971, +17.0596) | 935 | 889 | 46 | true | 20,563 |
| 29 | 11 | generic | (+1.5029, +17.0596) | 933 | 892 | 41 | true | 21,455 |
| 30 | 12 | generic | (+6.5029, +17.0596) | 911 | 878 | 33 | true | 22,333 |
| 31 | 13 | generic | (+11.5029, +17.0596) | 970 | 917 | 53 | true | 23,250 |
| 32 | 14 | generic | (+16.5029, +17.0596) | 1,038 | 975 | 63 | true | 24,225 |
| 33 | 15 | generic | (+21.5029, +17.0596) | 1,228 | 1,168 | 60 | true | 25,393 |
| 34 | 16 | generic | (+21.5029, +12.0596) | 1,852 | 1,662 | 190 | true | 27,055 |
| 35 | 17 | generic | (+21.5029, +7.0596) | 1,169 | 983 | 186 | true | 28,038 |
| 36 | 18 | generic | (+21.5029, +2.0596) | 229 | 222 | 7 | true | 28,260 |
| 37 | 19 | generic | (+21.5029, −2.9404) | 3,122 | 3,092 | 30 | true | 31,352 |
| 38 | 20 | generic | (+21.5029, −7.9404) | 5,608 | 4,958 | 650 | true | 36,310 |
| 39 | 21 | generic | (+21.5029, −12.9404) | 3,469 | 2,426 | 1,043 | true | 38,736 |
| 40 | 22 | generic | (+16.5029, −12.9404) | 3,084 | 2,799 | 285 | true | 41,535 |
| 41 | 23 | generic | (+11.5029, −12.9404) | 2,147 | 1,453 | 694 | true | 42,988 |

The gazes trace a **perimeter circumnavigation** on the frozen 5-degree lattice:
left along pitch −2.94, up to +17.06, right across the top to +21.50, down the
right side to −12.94, then back left.

- object 143: **5,344** (seed) → **15,589** (resume) → **42,988** surfels;
- **no empty looks** — `empty_steps: []`; every look exceeded the inherited
  `<100` limit, so the Reality-2b negative-evidence branch stayed untested;
- **`idempotent_replay` true on all 24** looks;
- **purity verified independently at all 24 maps**: exactly `{143}`, never
  admitting 141, 142, 144 or 145;
- resume surfels displaced by median **0.0000 mm**, p99 **2.76 mm**, max
  **8.66 mm** — inside the frozen 12 mm radius;
- final multi-look surfels **3,598**, max support **3**;
- range at resume 1.8998 / 2.2121 / 4.6621 m → final 1.8998 / **3.5106** /
  4.6958 m, so growth moved the mass of the object substantially farther.

### Termination: the object-scoped watchdog, not the scientific stop

`termination_reason: object2_watchdog`, `object_2_fixations_total: 24`,
`watchdog_object2_fixations: 24`, `scientific_stop_reached: false`.

**The frozen policy returned `continue` at all 24 decisions and never once
returned `no_frontier`.** At the final decision it wanted gaze
**(+6.5029, −12.9404)** with **696 open frontier voxels of 991** (43
map-resolved, 252 boundary-resolved).

The frontier is nonetheless converging: comparing the blocked MultiObject-1b
state with this one, open frontier fell **1,193 → 696** (−42%) while
boundary-resolved rose **17 → 252** (×15). **Object 143 is being resolved, just
not within 24 looks.** That is a measurement, not a threshold.

### Scene representation

Both entities remain separate. `object_1_read_only: true`,
`automatic_object_discovery: false`, `truth_opened: false`,
`policy_source_modified: false`, adapter
`id143_to_frozen_fsg6f_target_label`, renderer entry point
`tools/scene_render_fix.py`.

Shared 0.1-degree chart **602 × 335** at `yaw0 = −31.30`, `pitch0 = −10.40`:

| | cells | area |
|---|---|---|
| object 141 | **37,654** | 376.54 deg² |
| object 143 | **17,947** | 179.47 deg² (from the seed's 1,670) |
| **overlap** | **0** | **0 deg²** |

Object 141 spans yaw **[−12.40, +12.70]**, pitch **[−8.30, +10.40]**; object 143
now spans yaw **[−30.70, +28.20]**, pitch **[−9.80, +22.50]**. Zero overlap was
confirmed both numerically and in the image, which reserves its brightest level
for cells claimed by both and contains **no such pixel**.

### Visual reading, descriptive

`object_143_growth.png` (24 panels) shows object 143 revealed as a large
**architectural corner structure**, not a compact object: the seed is a thin
horizontal ledge sliver; by the end of the reused looks a vertical wall segment
and an upper band have appeared; the new looks extend the upper band right across
the full width, add a right-hand vertical edge, and close a bottom band. **The
growth is edge-concentrated — region interiors stay unsampled throughout.**

`scene_cyclopean_footprints.png` shows object 143 **framing** object 141: a broad
band above, vertical bands down both sides, a band below, with the cloth
quadrilateral and its black emblem ellipse — the residue Cyclopean-1g could not
measure — in the centre. This is the same enclosure relation MultiObject-1a
inferred indirectly when the 1a seed's spherical mean landed inside object 141's
footprint; it is now visible directly.

`object_143_surface_map.ply` carries **42,988** vertices in the fixed head frame.

**Newly visible objects, all correctly not instantiated**: id **144** at global
steps 21–22 and id **145** at step 36 (3,726 valid pixels), alongside 141 and 142.
Automatic discovery remains deferred and the deferral is visible in the
measurements.

### The low-texture surface does produce measurement deficit

This was the sharpest question, and the answer is unambiguous.

Yield per new look: **min 229, median 1,198, mean 1,732, max 5,608** target
points. A typical object-141 look in this programme returned ~**55,000**. The
best object-143 look is **10.1%** of that and the median is **2.2%**.

Sampled stereo validity on the new looks tells the same story from the instrument
side:

| look | frame valid | id-143 visible | id-143 measured | recovered |
|---|---|---|---|---|
| `fix_24` | **2.1%** | 54,801 | 1,360 | **2.5%** |
| `fix_30` | **1.4%** | 62,839 | 911 | **1.4%** |
| `fix_36` | **6.0%** | 15,799 | 229 | **1.4%** |
| `fix_41` | **61.4%** | 11,752 | 2,147 | 18.3% |

**Object 143 fills most of the frame and the instrument recovers 1.4–2.5% of
it.** Frame validity falls to **1.4%**: the observer can see the surface and
cannot measure it. Validity recovers to 61.4% only at `fix_41`, back near the
textured cloth region.

This is the Cyclopean-1g emblem problem at architectural scale, and it explains
the watchdog termination: each look resolves a little of the frontier, so the
policy correctly keeps going, but the yield is too low to exhaust a surface this
large in 24 looks.

One subtlety worth recording: **no empty look occurred even so**, because 1.4% of
~60,000 visible pixels is still ~900 points, far above the inherited `<100`
threshold. The empty-look contract is calibrated well below what even a
barely-measurable large surface returns, so that branch stayed untested.

**Internal coherence is not evaluator accuracy.** No truth was opened; every
number here describes the representation.

### Structural failures and code fixes

**No structural FAIL line**: `structural_fails: []` in both the manifest and the
comparator, `partial_fixations_rerendered: 0`, `global_history_renumbered:
false`, purity at all 24 maps, object 141 byte-identical, all 16 pinned items
unchanged, the first blocked record preserved, and no evaluator truth opened.

**Code fixes: none.** No file was modified by this run.

### What this establishes, and what it does not

Established. **The corrected equivalence criterion is the right shape and it
passes.** Gating on calibration, the acquisition contract, observation
keys/shapes/dtypes and both oracle instance masks — all exact — while recording
RGB descriptively with **no tolerance** separates instrument identity from GPU
accumulation determinism, and the new `rgbgate` control keeps a tolerance from
creeping back. **The interrupted experiment resumed exactly**: six looks reused
with zero rerenders, no renumbering, first new step 24. **The FSG6f transfer
holds over a long run** — 18 further looks, purity exactly `{143}` at every map,
all 24 replay-idempotent, resume surfels moved at most 8.66 mm, and **object 141
byte-identical throughout**, with **zero** shared-chart overlap. And **the
low-texture surface demonstrably starves the instrument**: 1.4–2.5% depth
recovery, median yield 2.2% of a cloth look.

Not established. **The scientific question is still open.** Termination was the
**object-scoped watchdog**, not `no_frontier`; the policy said `continue` 24
times out of 24 and still had 696 open frontier voxels, so this run does **not**
show whether object-143 growth terminates — only that it does not terminate
within 24 looks on this surface. **The watchdog is not success**, and the
frontier trend (open 1,193 → 696, boundary-resolved 17 → 252) is a measurement
that suggests convergence without demonstrating it. **No accuracy claim**: truth
stayed closed, so nothing here speaks to whether the 42,988 surfels are correct.
**The empty-look branch remains untested.** **Zero footprint overlap is still not
an invariant** — it survived a fourfold growth of object 143 on this
configuration and nothing more. And **objects 142, 144 and 145 remain
uninstantiated by design**, so nothing is established about discovery or
scene-level scheduling.

**Next**, per the contract: because the scientific stop was not reached, whether
to raise the object-scoped watchdog, accept edge-concentrated coverage as the
practical outcome for low-texture architecture, or move to cyclopean completion
for object 143 is a decision for Luiz/Chat.
