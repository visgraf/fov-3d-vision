# MultiObject-2c — grow the scene-selected third object

## Question

Can the frozen single-object FSG6f growth mechanism grow the object selected by MultiObject-2a and seeded by MultiObject-2b, while the two pre-existing scene objects remain separate and byte-identical?

This is the first growth experiment whose target id is supplied by scene memory rather than declared by the experiment. The id is consumed from the completed MultiObject-2b parent; it is not hard-coded in MultiObject-2c.

## Frozen science

- fixed head and static Reality fixture;
- existing stereo front end;
- generic `tools/scene_render_fix.py` acquisition entry point;
- frozen FSG6f frontier/controller through a pure instance-label adapter;
- frozen 12 mm FSG3/FSG6f association rule;
- inherited 5 degree local saccade lattice and all FSG6f numerical rules;
- Reality-2b empty-look semantics: fewer than 100 selected-object points is valid negative evidence, not a runtime failure;
- object-scoped 24-fixation watchdog including the MultiObject-2b seed, engineering only.

Objects 141 and 143 remain read-only. Only pixels carrying the parent-selected scene id may enter the new object's surfel map.

## History

Active growth history begins at the saved MultiObject-2b seed observation. Earlier observations that selected the object and positioned the seed are not replayed as growth-policy history. The seed acquisition is reused, never rerendered. The first new global fixation is the next chronological step after the seed.

## Texture diagnostics

Because the selected object is strongly textured in its seed view, each look records:

- visible selected-object pixels in the rectified left field;
- valid selected-object depth points;
- recovered fraction `valid / visible`;
- frame-wide valid stereo fraction.

These values are descriptive only. They do not rank candidates, alter FSG6f, stop growth, or gate success. The purpose is to compare the measurement regime with the low-texture object-143 experience without changing the experiment.

## Stop

Scientific stop remains the frozen FSG6f stop (`no_frontier`). The 24 selected-object-fixation watchdog is only an engineering guardrail. If the watchdog is reached while the policy still says `continue`, the run is structurally complete but the scientific stop was not reached.

## Outputs

The run writes the selected-object surfel map and PLY, growth image, per-look RGB previews, patches/maps, policy trace, three-object scene graph, shared cyclopean footprints, and a manifest with per-look stereo-recovery diagnostics and integrity hashes.

No automatic discovery, scene scheduler, semantic ranking, mesh/interpolation, evaluator truth, or quality gate is introduced.

## Results

Run 2026-09-22 on the workstation. **`MULTIOBJECT2C_COMPLETE` structurally,
`structural_fails: []` — but `termination_reason: object3_watchdog` with
`scientific_stop_reached: false`. The watchdog is not scientific success.** The
frozen policy returned `continue` at **all 24** of its decisions and never
reached `no_frontier`.

Object 142 — the id supplied by scene memory, not declared here — grew from
**38,020** seed points to **310,884** surfels (**8.2×**) over 23 added fixations,
pure `{142}` at every map, while objects 141 and 143 remained **byte-identical**.

### Provenance

Working tree clean. Package commit **`b623dea`**; parent result **`97ba8cf`**. The
commit adds **exactly the seven MultiObject-2c files, all `A`**. `git diff`
against `97ba8cf` over **75 frozen sources** — every FSG1/FSG3/FSG6f source,
scene, rig, pin file, every Reality Check 1/2/2b source, **both renderers**,
every Cyclopean-1a..1g source and every MultiObject-1a/1b/1b2/1c/2a/2b source —
is **empty (0 lines)**, all 75 sha256 SAME. The sources 2c must reuse unchanged
are verified: `fsg6f_frontier.py` `d636c9405d719916…`,
`multiobject1b_policy.py` `4068b3a4ecd7d645…`, `scene_render_fix.py`
`6e70bbb78c1043ec…`, `fsg3_surface_map.py` `1b9dbeb873105ec9…`,
`reality2b_public.py` `dfe1ca243c4c1543…`.

The parent was located **by manifest**, not by assumed path: exactly one
`MultiObject2b-seed-selected-object-v1` record at seed 2111 with `truth_opened`
false — `previews/multiobject2b/full-seed2111` — carrying `selected_object_id`
**142**, `selected_object_seed_points` **38,020**, seed at `global_step` **42**,
`parent_fixations_rerendered` 0, `existing_objects_read_only` true,
`growth_iterations_added` 0, `structural_fails []`.

### The target id is consumed, not hard-coded

`multiobject2c_run.py:55` reads `int(m.get("selected_object_id", -1))` from the
parent manifest, and **the literal `142` appears nowhere in any MultiObject-2c
source**. The public contract states the rule explicitly: *"consume
MultiObject-2b selected_object_id; do not hand-pick or hard-code the scene id in
this step."*

### Seed reproduction

The saved MultiObject-2b seed acquisition was recomputed rather than trusted:
re-running `compute_once` on `fix_42` and selecting `valid & (instance_id == 142)`
yields **38,020** points, matching the saved patch count exactly, with
**`xyz` byte-identical** to `object_142_seed_patch.npz` and ids exactly `{142}`.
The seed acquisition was **reused, never rerendered** — `fix_42` does not appear
in the 2c output, and `parent_fixations_rerendered: 0`.

### Read-only integrity

**All 9 pinned inputs byte-identical after the run**: 2b `prediction_manifest.json`
`57f0162188609bb7…`, `scene_graph.json` `70b82a48b8477634…`,
`object_142_seed_patch.npz` `f64c9e1c5d718602…`, `object_142_seed_rgb.png`
`cde5d441a3f52136…`, `scene_cyclopean_footprints.npz` `dc6b3e39540dcb04…`, the
object-141 source `6ac98f6251b47337…f71e524a`, the object-143 source
`bbc4b856a07d2be5…a39f234df`, and the seed acquisition pair
(`43708ebc08800e6d…`, `44a10d8ddfa3c7ef…`).

Objects verified pure **before and after**: **141** 155,684 points ids `{141}`;
**143** 42,988 points ids `{143}`. Manifest records
`preexisting_objects_read_only: true`, `policy_source_modified: false`,
`truth_opened: false`, `quality_gate_used: false`,
`automatic_scene_scheduler: false`, `automatic_object_discovery: false`,
`renderer_entrypoint: tools/scene_render_fix.py`, adapter
`parent_selected_id_to_frozen_fsg6f_target_label`. No reference to
`reality2_render_fix.py` exists in the 2c sources.

### Environment and wall time

Blender 5.2.1 LTS headless, Cycles, **OPTIX** on an RTX 4090 (driver 595.84);
host `.venv/bin/python` 3.12.3. **4 m 21 s total**, of which **260.0 s** was the
growth loop — 23 Blender launches.

### Checks

`py_compile` clean on all five modules. The three prescribed lines appeared
verbatim:

```text
[multiobject2c-growth] PASS parent_selected=true preexisting_read_only=true selected_only=true frozen_fsg6f=true seed_scoped_history=true
[multiobject2c-instrument] PASS generic_renderer=true object_scoped_watchdog=true empty_evidence=true texture_diagnostic=true scheduler=false
[multiobject2c-check] SUMMARY passed=6 failed=0
```

All **seven** negatives are genuine source-mutation controls, each exiting **1**
with a named detector and **none exiting 2**:

| negative | rc | detected by |
|---|---|---|
| `handpick` | 1 | `parent_selected_target_not_handpicked` |
| `crossfuse` | 1 | `preexisting_read_only_selected_only_growth` |
| `copypolicy` | 1 | `frozen_fsg6f_adapter` |
| `priorhistory` | 1 | `seed_scoped_history` |
| `legacyrenderer` | 1 | `generic_renderer_object_scoped_watchdog` |
| `globalwatchdog` | 1 | `generic_renderer_object_scoped_watchdog` |
| `texturegate` | 1 | `empty_evidence_texture_diagnostic_no_scheduler_gate` |

**No regression**: all 16 prior suites green and **110 prior negatives** still
firing — multiobject2b 6/6, multiobject2a 6/6, multiobject1c 6/6,
multiobject1b2 7/7, multiobject1b 6/6, multiobject1a 6/6,
cyclopean1g/1f/1e/1d/1c/1b/1a 6/6 each, reality2b 7/7 (10/10), reality1 6/6,
fsg6f 14/14 (15/15).

### The full object-142 fixation table

Growth history begins at the 2b seed (global step 42); the first new fixation is
**43** and the last **65**. Gazes move on the frozen 5-degree lattice.

| g.step | obj # | src | gaze (yaw, pitch) | target visible | valid depth | recovery | frame valid | new | matched | idem |
|---|---|---|---|---|---|---|---|---|---|---|
| 42 | 0 | seed | (+14.000, −13.811) | 56,083 | 38,020 | 67.8% | 61.8% | 38,020 | 0 | true |
| 43 | 1 | grow | (+9.000, −8.811) | 27,094 | 19,134 | 70.6% | 64.2% | 12,196 | 6,938 | true |
| 44 | 2 | grow | (+4.000, −8.811) | 26,590 | 17,735 | 66.7% | 72.6% | 11,139 | 6,596 | true |
| 45 | 3 | grow | (−1.000, −8.811) | 26,368 | 19,185 | 72.8% | 74.9% | 13,330 | 5,855 | true |
| 46 | 4 | grow | (−6.000, −8.811) | 26,747 | 19,755 | 73.9% | 63.4% | 12,721 | 7,034 | true |
| 47 | 5 | grow | (−11.000, −8.811) | 27,421 | 19,181 | 70.0% | 49.5% | 11,527 | 7,654 | true |
| 48 | 6 | grow | (−16.000, −8.811) | 28,505 | 18,998 | 66.6% | 36.7% | 12,291 | 6,707 | true |
| 49 | 7 | grow | (−21.000, −8.811) | 30,010 | 21,756 | 72.5% | 40.3% | 15,086 | 6,670 | true |
| 50 | 8 | grow | (−21.000, −13.811) | 59,217 | 42,823 | 72.3% | 68.0% | 24,215 | 18,608 | true |
| 51 | 9 | grow | (−21.000, −18.811) | 65,536 | 38,525 | 58.8% | 58.8% | 15,158 | 23,367 | true |
| 52 | 10 | grow | (−16.000, −13.811) | 56,826 | 38,360 | 67.5% | 61.6% | 10,934 | 27,426 | true |
| 53 | 11 | grow | (−11.000, −13.811) | 55,147 | 40,173 | 72.8% | 64.3% | 11,568 | 28,605 | true |
| 54 | 12 | grow | (−6.000, −13.811) | 54,136 | 37,062 | 68.5% | 61.2% | 11,526 | 25,536 | true |
| 55 | 13 | grow | (−1.000, −13.811) | 53,760 | 38,855 | 72.3% | 67.4% | 10,996 | 27,859 | true |
| 56 | 14 | grow | (+4.000, −13.811) | 53,895 | 36,344 | 67.4% | 64.4% | 8,238 | 28,106 | true |
| 57 | 15 | grow | (+9.000, −13.811) | 54,668 | 36,603 | 67.0% | 63.1% | 4,081 | 32,522 | true |
| 58 | 16 | grow | (+14.000, −8.811) | 28,024 | 20,160 | 71.9% | 50.4% | 4,517 | 15,643 | true |
| 59 | 17 | grow | (+19.000, −8.811) | 29,389 | 22,168 | 75.4% | 41.3% | 13,216 | 8,952 | true |
| 60 | 18 | grow | (+24.000, −8.811) | 30,274 | 23,407 | 77.3% | 41.9% | 15,034 | 8,373 | true |
| 61 | 19 | grow | (+24.000, −13.811) | 60,343 | 43,030 | 71.3% | 67.8% | 20,849 | 22,181 | true |
| 62 | 20 | grow | (+24.000, −18.811) | 65,536 | 40,591 | 61.9% | 61.9% | 16,550 | 24,041 | true |
| 63 | 21 | grow | (+19.000, −13.811) | 58,175 | 42,198 | 72.5% | 68.6% | 2,727 | 39,471 | true |
| 64 | 22 | grow | (+19.000, −18.811) | 65,536 | 40,345 | 61.6% | 61.6% | 7,814 | 32,531 | true |
| 65 | 23 | grow | (+14.000, −18.811) | 65,536 | 41,363 | 63.1% | 63.1% | 7,151 | 34,212 | true |

- **no empty looks** — `empty_steps: []`; every look far exceeded the inherited
  `<100` limit, so the Reality-2b negative-evidence branch was **not exercised**;
- **`idempotent_replay` true on all 24** looks;
- **purity verified independently at all 24 saved maps**: exactly `{142}`, never
  admitting 141, 143, 144 or 145;
- final map **310,884** points, range **1.3565 / 2.4113 / 4.0649 m**, multi-look
  surfels **130,949**, max support **8**;
- `object_142_surface_map.ply` carries **310,884** vertices.

### Texture-recovery diagnostics — descriptive only

`texture_diagnostics_are_gates: false`. Across the 24 looks the target
depth-recovery fraction is **min 58.8%, median 70.3%, max 77.3%** — a narrow,
consistently high band.

The contrast the contract asked for is stark. Object 143, on its low-texture
architectural surface, recovered **1.4–2.5%** per look and its frame-wide valid
rate fell to **1.4%**. Object 142 recovers **~70%** with frame-wide validity
mostly 40–75%. **These numbers ranked nothing, stopped nothing and gated
nothing** — they are recorded to characterise the measurement regime, exactly as
specified.

### Termination — watchdog, not scientific stop

`termination_reason: object3_watchdog`,
`selected_object_fixations_total: 24` = `watchdog_selected_object_fixations: 24`,
`scientific_stop_reached: false`.

**The frozen policy returned `continue` at all 24 decisions and never once
returned `no_frontier`.** At the final decision (global step 65) it wanted gaze
**(+8.9996, −18.8109)** with **650 open frontier voxels of 679** (16
map-resolved, 13 boundary-resolved). Proportionally that is **95.7% of the
frontier still open** — compared with object 143's 696 of 991 (70.2%) at its own
watchdog. **Object 142 is nowhere near exhausted**, and this run establishes
nothing about where its growth would terminate.

### Three-object scene representation

| object | geometry | points | footprint cells | area |
|---|---|---|---|---|
| 141 | `SURFEL_MAP` (read-only) | 155,684 | 37,654 | 376.54 deg² |
| 143 | `SURFEL_MAP` (read-only) | 42,988 | 17,947 | 179.47 deg² |
| **142** | **`SURFEL_MAP`** (grown) | **310,884** | **62,784** | **627.84 deg²** |

Shared chart **624 × 488**, grid **0.1 deg**, `yaw0 −31.30`, `pitch0 −25.70`.
Extents: 141 yaw [−12.40, +12.70] pitch [−8.30, +10.40]; 143 yaw [−30.70, +28.20]
pitch [−9.80, +22.50]; **142 yaw [−29.80, +30.50] pitch [−25.20, −9.00]**.

**Footprint relations — measurements, never gates:**

| pair | overlapping cells |
|---|---|
| 141 ∩ 142 | **0** |
| 141 ∩ 143 | **0** |
| 142 ∩ 143 | **0** |
| all three | **0** |

Object 142 grew from **9,624** cells at seed to **62,784** — it is now the
**largest** footprint in the scene, larger than 141 and 143 combined — and the
three objects remain **mutually disjoint**. Zero overlap is recorded as what this
configuration produced, not as a property the representation requires.

### Visual reading, descriptive

`object_142_growth.png` (24 panels) shows genuine **area-filling** growth: the
seed is a compact block at the lower right; by look 5 a horizontal band has
extended leftward across most of the width; by look 11 the band has thickened
downward with a notch still open at bottom-centre; by look 17 it is a solid
filled band; and the final panel is a continuous, densely filled expanse spanning
the full width. **Region interiors are filled solid, not hollow.**

That is the visible counterpart of the recovery diagnostics, and the sharpest
contrast with object 143, whose growth under 1.4–2.5% recovery was
edge-concentrated lacework with unfilled interiors.

`scene_cyclopean_footprints.png` is the three-object picture after growth:
object 141's cloth quadrilateral in the darkest grey at centre, with its panel
seams and the black emblem ellipse — the residue Cyclopean-1g could not measure —
still visible; object 143's bright architectural frame surrounding it; and
**object 142 now a broad medium-grey wood-grain expanse filling the entire lower
half**, disjoint from both.

Twenty-four per-look RGB previews were written alongside the growth strip.

### Structural failures and code fixes

**No structural FAIL line**: `structural_fails: []` in both the manifest and the
comparator, `parent_fixations_rerendered: 0`, purity at all 24 maps, objects 141
and 143 byte-identical, all 9 pinned inputs unchanged, no evaluator truth opened.

**Code fixes: none.** No file was modified by this run — no implementation defect
blocked execution, and no frozen source was touched.

### What this establishes, and what it does not

Established. **The frozen single-object growth mechanism works on a target chosen
by scene memory.** The id was **consumed from the MultiObject-2b parent** — the
literal never appears in 2c source — the seed was **reproduced byte-identically**
and reused without rerendering, and the frozen FSG6f controller, reached only
through a pure label adapter with `policy_source_modified: false`, drove 23
further fixations on the frozen 5-degree lattice. Object 142 grew **38,020 →
310,884** surfels (**8.2×**), **pure `{142}` at every one of 24 maps**, all
replay-idempotent, while **objects 141 and 143 stayed byte-identical** and all
three footprints remained **mutually disjoint**. The complete
selection → seed → growth chain now runs end to end without cross-object
contamination.

Also established, as a diagnostic contrast: **the measurement regime differs
enormously between objects.** Object 142 recovers **58.8–77.3%** (median 70.3%)
where object 143 recovered **1.4–2.5%**, and the growth images show the
consequence — filled interiors versus edge lacework. **These numbers gated
nothing.**

Not established. **The scientific question is open**: termination was the
**object-scoped watchdog**, not `no_frontier`; the policy said `continue` 24
times out of 24 with **650 of 679** frontier voxels still open — proportionally
*more* open than object 143 at its watchdog — so this shows only that growth does
not terminate within 24 looks, not where it would end. **The watchdog is not
scientific success.** **No object completeness** — 627.84 deg² of footprint says
nothing about how much of object 142 exists. **No accuracy claim** — evaluator
truth stayed closed, so 310,884 points describe the representation, not the
scene. **The empty-look branch remains untested**, since no look came near the
`<100` limit. **Zero footprint overlap is still not an invariant** — it survived a
6.5× footprint expansion in this configuration and nothing more; the contract
explicitly allows occlusion and shared angular support. And **no discovery,
scheduler, semantic ranking, mesh or interpolation** was introduced; object 143
remains retained for revisit under MultiObject-1c's disposition.

**Next**: because the scientific stop was not reached, whether to raise the
object-scoped watchdog for object 142, accept the current coverage, or proceed to
another scene-level decision is a judgement for Luiz/Chat.
