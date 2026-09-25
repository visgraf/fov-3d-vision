# Classroom-Oracle-3b — gap anatomy result

Post-hoc and read-only. The controller was **not executed**. No acquisition, no fixation, no
fusion, no Blender, no rule changed.

## Branch / commits / checks

| item | value |
|---|---|
| branch | `classroom-oracle-3b` |
| required ancestor | `9c13905` CLASSROOM_ORACLE3_COMPLETE (direct parent) |
| package | `024ff7c` Add Classroom Oracle 3b gap anatomy |

```text
[classroom-oracle3b-check] SUMMARY passed=15 failed=0
```

All four modules compile; `git diff --check` clean; tree clean. **No mechanical repair was
required.**

## Input provenance and read-only verification

Verified from the files, not from the prompt.

**Oracle-3**: `controller_phase_complete=true`, `truth_phase_complete=true`,
`truth_opened_during_controller_replay=false`, `all_final_fsg6f_replays_exact=true`,
`controller_phase_replays=25`. All 25 object directories carry `controller_state.npz`,
`truth_misses.npz`, `control_audit.json` and `truth_audit.json` (0 missing). Aggregate
misses **3,670**; `COMPLEMENT_NONSHORELINE` **3,479**; `NOT_SHORELINE` **3,624**. Focus set
inherited: `[178, 225, 210, 166, 115, 123]`, exactly six.

**Oracle-1**: `bootstrap/evaluation_only/reachable_samples.npz` present, 29,288 samples;
lattice step independently inferred from the file as **0.25 deg**, against the Cyclopean
chart's 0.1 deg (401x501). The manifest records
`reference_lattice: {step_deg: 0.25, yaw0_deg: -25.0, pitch0_deg: -20.0}`, so components are
measured on the truth lattice and not spuriously fragmented on the finer raster.

**Source contract**, audited independently of the check suite: `classroom_oracle3b_audit.py`
contains zero references to `multiobject2c_policy`, `choose_next`, `bpy`, `subprocess`,
`render`, `fuse(` or `initialize(`. Its only `fsg6f` mention is the provenance guard
`if not a3.get("all_final_fsg6f_replays_exact")`, and its only `blender` mention is the
declared flag `"blender_launched": False`. Focus IDs are read from
`a3.get("focus_instance_ids")` with a hard requirement of six; truth is decoded from
Oracle-3's own `CYCLOPEAN_FIRST_REJECTION_REASONS` / `TRUTH_SUBTYPES` tables rather than
reclassified.

**Run flags**: `controller_executed=false`, `new_acquisitions=0`, `new_fixations=0`,
`new_fusion=0`, `blender_launched=false`, `posthoc_only=true`.

**Immutability**: 703 `.json`/`.npz` files across `classroom-oracle-3-audit` and
`classroom-oracle-1-full` have an identical aggregate sha256 before and after the run
(`24d7e6c343711acc…`). No EXR or render was written anywhere under the Oracle-3b tree.
`git diff 9c13905 HEAD` over `classroom_oracle1_*`, `classroom_oracle2_*`,
`classroom_oracle3_*`, `fsg6f*` and `multiobject2c_policy.py` is empty.

## Aggregate gap anatomy

| quantity | value |
|---|---:|
| COMPLEMENT_NONSHORELINE samples | **3,479** |
| fraction of all 3,670 Oracle-3 misses | **94.80%** |
| connected components (0.25 deg lattice, 8-connected) | **62** |
| support-ring depth: min / median / P90 / max | **2 / 52 / 116 / 324** |
| in degrees (x 0.1 deg per ring) | 0.2 / **5.2** / 11.6 / **32.4** |
| never-observed fraction | **98.16%** |
| target-seen fraction | **1.55%** |

Observation-state histogram over the detached misses:

| state | count | share |
|---|---:|---:|
| NEVER_OBSERVED | **3,415** | 98.16% |
| TARGET_SEEN_WITH_DEPTH | 29 | 0.83% |
| TARGET_SEEN_NO_DEPTH | 25 | 0.72% |
| NONTARGET_ONLY | 10 | 0.29% |

### Halo-reach curve

Cumulative fraction of detached misses that would become adjacent to support after k
successive 8-connected support dilations:

| rings | degrees | samples reached | cumulative |
|---:|---:|---:|---:|
| 1 | 0.1 | 0 | **0.00%** |
| 2 | 0.2 | 42 | 1.21% |
| 3 | 0.3 | 80 | 2.30% |
| 5 | 0.5 | 155 | 4.46% |
| 10 | 1.0 | 353 | 10.15% |
| 15 | 1.5 | 541 | 15.55% |
| **20** | **2.0** | **732** | **21.04%** |
| 324 | 32.4 | 3,479 | 100.00% |

The curve is shallow and close to linear over its first twenty rings: each additional
0.1-degree ring recovers roughly one further percent. Twenty rings — a twentyfold widening
of the one-ring halo — still leaves **79%** of the detached surface unreached. The JSON
samples the curve at rings 1-20 and then at the maximum; the percentile summary
(median 52, P90 116) is the authoritative description beyond ring 20.

## Focus six

| id | name | gap / object misses | frac | comps | ring med | ring P90 | ring max | support dist med | never obs | target seen |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 178 | sol | 1,022 / 1,043 | 98.0% | 5 | 57 | 100 | 110 | 5.75 deg | 96.6% | 2.9% |
| 225 | woodBaseboard | 623 / 634 | 98.3% | 5 | 80 | 153 | 169 | 8.10 deg | **100.0%** | 0.0% |
| 210 | wall.008 | 337 / 404 | 83.4% | 3 | **17** | 52 | 80 | 1.88 deg | 96.1% | 2.4% |
| 166 | lettersPlank | 378 / 382 | 99.0% | **1** | 54 | 96 | 106 | 5.50 deg | 99.5% | 0.5% |
| 115 | boardFrame | 338 / 342 | 98.8% | 2 | 65 | 122 | 134 | 6.55 deg | 97.9% | 2.1% |
| 123 | ceilingMoulding | 301 / 306 | 98.4% | 2 | 75 | 309 | **324** | 7.60 deg | 99.7% | 0.3% |

### Largest components

| id | name | n | ring min | ring med | ring max | support dist med | nearest completed fixation | yaw span | never obs |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|
| 178 | sol | **935** | 2 | 58 | 110 | 6.00 deg | **12.25 deg** | [14.0, 25.0] | 98.4% |
| 225 | woodBaseboard | 393 | 3 | 80 | 158 | 8.10 deg | 14.16 deg | [9.5, 25.0] | 100.0% |
| 166 | lettersPlank | 378 | 2 | 54 | 106 | 5.50 deg | 11.73 deg | [14.5, 25.0] | 99.5% |
| 210 | wall.008 | 236 | 2 | 14 | 29 | 1.56 deg | 8.32 deg | [-21.8, -19.0] | 97.9% |
| 123 | ceilingMoulding | 199 | 2 | 49 | 102 | 5.00 deg | 11.49 deg | [-24.5, -14.5] | 99.5% |
| 115 | boardFrame | 174 | 2 | 64 | 134 | 6.46 deg | 12.62 deg | [11.8, 25.0] | 97.7% |
| 174 | plank | 167 | 3 | 38 | 76 | 3.80 deg | 10.01 deg | [-25.0, -18.0] | 100.0% |
| 115 | boardFrame | 164 | 2 | 66 | 134 | 6.62 deg | 12.98 deg | [11.8, 25.0] | 98.2% |
| 123 | ceilingMoulding | **102** | **229** | **295** | **324** | 29.50 deg | **29.37 deg** | [15.5, 25.0] | **100.0%** |

Nine components hold 100 or more samples and together carry 2,748 of 3,479 (79.0%).

Smaller components tell the other half of the story. `sol` component 3 (9 samples, ring
median 6, 2.11 deg from a completed fixation) is **0% never observed** — 6 samples
TARGET_SEEN_NO_DEPTH, 3 NONTARGET_ONLY. `wall.008` component 3 (5 samples, ring median 5) is
likewise 0% never observed. These are the representational cases, and they are small.

### The shape: near tips, far bodies

**13 of 62 components — carrying 2,279 of 3,479 samples (65.5%) — have their nearest
detached sample at ring 2**, i.e. exactly one step beyond the current one-ring shoreline,
with a minimum support distance of 0.20 deg. Five more start at ring 3 and two at ring 4.
Yet the same components' bodies run to a median ring depth of 43 (P10 8, P90 97, max 295)
and a maximum of 324.

So the typical large component is an elongated strip whose tip almost touches the shoreline
and whose body extends five to thirty degrees away, usually running to the domain edge
(eight of the nine largest span to yaw +25.0 or -25.0).

One component has no near tip at all: `ceilingMoulding` component 2, 102 samples, ring
minimum **229**, 29.37 deg from the nearest completed fixation, 100% never observed. That
one is genuinely remote by any reading.

## Demo

```text
previews/classroom-oracle-3b-gap-anatomy/demo/Demo.md
previews/classroom-oracle-3b-gap-anatomy/demo/overview.png
previews/classroom-oracle-3b-gap-anatomy/demo/objects/instance_{0115,0123,0166,0178,0210,0225}_gap_anatomy.png
previews/classroom-oracle-3b-gap-anatomy/demo/frames/frame_0000..0005.png   (6 frames)
previews/classroom-oracle-3b-gap-anatomy/demo/classroom-oracle-3b-demo.mp4  (1280x838 @ 1 fps, 6 frames)
```

MP4 encoding was available and the video was written. `Demo.md` states: "This is a post-hoc
diagnostic visualization. No panel participated in gaze selection." Panel 4 is titled
*saved observation state (post-hoc)*.

Inspected `overview.png` and all six focus frames. `boardFrame` is the clearest single
image: the gray support forms a "C" — three sides of the picture frame — with the orange
one-ring shoreline hugging it, and the two detached components are horizontal dotted strips
running from the open end of the C out to the domain edge. Panel 2 shows the C as the
dark-blue ring-depth core with the strips beginning at its cyan fringe and extending into
progressively distant territory; panel 4 shows them as never-observed.

Presentation limitation, recorded separately from the measurements: in panel 2 the
ring-depth colormap is scaled to the full chart, so the far side of the domain saturates red
and visually dominates the informative near-support structure. The underlying ring values
are unaffected.

## Interpretation — labelled as interpretation, not measured fact

**Measured**, and not in dispute: the detached surface is 94.80% of all residual misses;
it forms 62 components; its median ring depth is 52 (5.2 deg) with a maximum of 324
(32.4 deg); a twenty-ring halo would reach only 21.04% of it; and 98.16% of it was never
observed by either eye.

**Interpretation.** Of the two possibilities Oracle-3b was built to separate, the evidence
favours the second. The detached surface is not a thin halo: widening the one-ring shoreline
to twenty rings still misses four fifths of it, and the large components sit five to thirty
degrees from anything the controller ever fixated. Equally, the gap is **attentional rather
than representational** — at 98.16% never observed, the eyes did not image this surface and
fail to record it; they never looked. The representational cases exist but are a rounding
error (1.55% target-seen, concentrated in components of five to nine samples).

A further reading, more speculative and resting on the near-tip statistic: because 65.5% of
the detached samples belong to components whose nearest tip is at ring 2 — one step beyond
the shoreline — the failure at the near end is marginal, while the failure at the far end is
not. That is consistent with a selector that cannot make the first step onto a strip, after
which the strip would have been walkable. But Oracle-3b did not test that, and nothing here
establishes that a larger halo would in fact walk the strip rather than stall again.

No numerical value in this document is a PASS/FAIL threshold, and none is proposed as one.

## Next decision — not taken here

Oracle-3b ends with diagnosis. The measurements distinguish a local-halo repair from a
global re-find mechanism and favour the latter, but choosing, sizing or implementing either
changes controller behaviour and is Luiz/Chat's call. No shoreline was enlarged, no global
search invented, no ranking modified.
