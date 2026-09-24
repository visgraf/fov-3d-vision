# Classroom-Oracle-3 — eligibility audit result

Diagnostic, read-only. **No controller rule, threshold, ranking, corridor, consensus,
fusion radius, watchdog or domain was changed.** No acquisition, no fixation, no fusion, no
Blender launch.

## Branch / commits / checks

| item | value |
|---|---|
| branch | `classroom-oracle-3` |
| required ancestor | `20bce24` CLASSROOM_ORACLE2_COMPLETE (direct parent) |
| package | `d828b05` Add Classroom Oracle 3 eligibility audit |

```text
[classroom-oracle3-check] SUMMARY passed=12 failed=0
```

All four modules compile; `git diff --check` clean; tree clean.

**No mechanical repair was required.** The live API matched the package assumptions:
`multiobject2c_policy.choose_next` / `.history_entry`, `classroom_oracle1_matcher.compute`,
`classroom_oracle1_epistemic.{make_evidence, add_observation, audit, choose_next}` and
`fsg6f_frontier.{extract_frontier, classify_frontier_state, candidate_state_consensus,
candidate_continuation_evidence, choose_next}` all bound as delivered.

## Parent runs, verified from the files

**Oracle-1**: `control_complete=true`, `smoke=false`, 25 targets, **104** fixations summed
from the manifest, all 25 `attention_complete`, dense truth not opened during control, and
every target has `result.json`, saved acquisitions and `final_map.npz` (0 missing).

**Oracle-2**: `control_complete=true`, `smoke=false`, 25 targets, **159** fixations, dense
truth not opened during control, `evaluation.json` present. Independently confirmed rather
than trusting the flags: the target ID sets are identical, the seed gazes are identical
value-for-value, and Scope-A uses the identical Oracle-1 reachable sample count (29,288)
with a baseline coverage that matches Oracle-1's own evaluation to 1e-12.

## Read-only and truth-isolation audit

| check | result |
|---|---|
| controller replays | **25** |
| `all_final_fsg6f_replays_exact` | **true** (0 recorded mismatches) |
| independent replay compare (6 count fields per object) | **25/25 agree** |
| `truth_opened_during_controller_replay` | **false** (0/25 objects) |
| `truth_opened_only_after_controller_phase` | **true**, `controller_phase_complete=true` |
| `new_acquisitions` / `new_fixations` / `new_fusion` | **0 / 0 / 0** |
| acquisition dirs or `fix_*` under the audit tree | **none** |
| EXR / `raw_*` written by Oracle-3 | **none** |
| Blender launched | **none** (no process, no log) |
| parent trees modified | **no** — 1,480 `.json`/`.npz` files across both parent runs, aggregate sha256 identical before and after (`d1227d27589f5dfa…`) |
| policy source modified after the package commit | **none** |

Focus set is not hard-coded. The manifest records
`focus_selection: six largest Oracle-1 miss counts from Oracle-2 Scope-A evaluation`, and I
cross-checked it against that evaluation independently: the six largest `baseline_misses`
are **[178, 225, 210, 166, 115, 123]**, exactly the manifest's `focus_instance_ids`.

## Final FSG6f replay — all 25

| terminal stage | objects |
|---|---:|
| `CANDIDATES_REJECTED_BY_CONSENSUS` | **11** |
| `OPEN_BUT_NO_CANDIDATE` | **10** |
| `NO_OPEN_FRONTIER` | **4** |
| `STOP_OTHER` / `ACTIVE` | 0 |

Only 4 of 25 objects ran out of OPEN frontier. The other 21 still had open frontier cells at
the moment of `attention_complete` and were stopped downstream — at candidate formation or
at consensus.

## Focus six — rejection diagnosis

| id | name | O1 misses | O1 fix | FSG terminal stage | OPEN/MAP/BOUND | cand/rej | Cyclopean first-rejection | dominant | O1==O2 traj |
|---|---|---:|---:|---|---|---|---|---|---|
| 178 | sol | 1,043 | 6 | CANDIDATES_REJECTED_BY_CONSENSUS | 87/105/134 | 3/3 | NOT_SHORELINE 1029 (98.7%), ALREADY_OBSERVED 14 (1.3%) | **NOT_SHORELINE** | **False** |
| 225 | woodBaseboard | 634 | 2 | CANDIDATES_REJECTED_BY_CONSENSUS | 30/8/173 | 4/4 | NOT_SHORELINE 628 (99.1%), ALREADY_OBSERVED 6 (0.9%) | **NOT_SHORELINE** | True |
| 210 | wall.008 | 404 | 19 | CANDIDATES_REJECTED_BY_CONSENSUS | 42/97/317 | 2/2 | NOT_SHORELINE 391 (96.8%), ALREADY_OBSERVED 13 (3.2%) | **NOT_SHORELINE** | **False** |
| 166 | lettersPlank | 382 | 4 | CANDIDATES_REJECTED_BY_CONSENSUS | 21/0/103 | 2/2 | NOT_SHORELINE 380 (99.5%), ALREADY_OBSERVED 2 (0.5%) | **NOT_SHORELINE** | True |
| 115 | boardFrame | 342 | 3 | OPEN_BUT_NO_CANDIDATE | 7/0/177 | 0/0 | NOT_SHORELINE 342 (100.0%) | **NOT_SHORELINE** | True |
| 123 | ceilingMoulding | 306 | 1 | CANDIDATES_REJECTED_BY_CONSENSUS | 44/4/200 | 4/4 | NOT_SHORELINE 306 (100.0%) | **NOT_SHORELINE** | True |

Every focus object still had OPEN frontier (7 to 87 cells) at its terminal decision, and
every one has `cyclopean_eligible_cells_final = 0`.

Truth subtype per focus object is dominated by `COMPLEMENT_NONSHORELINE` throughout:
sol 1022/1043, woodBaseboard 623/634, wall.008 337/404, lettersPlank 378/382,
boardFrame 338/342, ceilingMoulding 301/306. `wall.008` carries the largest
`ANGULAR_SUPPORT_BUT_3D_UNCOVERED` share (54), i.e. cells angularly inside the map's support
but still more than 12 mm from any surfel.

## Aggregate — all 25 objects, 3,670 missed samples

Cyclopean first-rejection rule:

| rule | count | share |
|---|---:|---:|
| **NOT_SHORELINE** | **3,624** | **98.75%** |
| ALREADY_OBSERVED | 46 | 1.25% |
| INTERNAL_COMPONENT | 0 | never fired |
| PREVIOUSLY_FIXATED_CELL | 0 | never fired |
| ELIGIBLE_NEVER_OBSERVED_EXTERIOR | **0** | never fired |
| OUT_OF_CHART | 0 | never fired |

Descriptive subtype:

| subtype | count | share |
|---|---:|---:|
| COMPLEMENT_NONSHORELINE | 3,479 | 94.80% |
| ANGULAR_SUPPORT_BUT_3D_UNCOVERED | 145 | 3.95% |
| EXTERIOR_TARGET_NO_DEPTH | 23 | 0.63% |
| EXTERIOR_TARGET_WITH_DEPTH | 21 | 0.57% |
| EXTERIOR_NONTARGET_ONLY | 2 | 0.05% |

### Consistency check — passes

No object that ended `attention_complete` has a post-hoc miss landing on a cell its own
reconstructed final Cyclopean state still calls eligible: `ELIGIBLE_NEVER_OBSERVED_EXTERIOR`
is **0** across all 25, and `cyclopean_eligible_cells_final` is **0** for every object. The
replay and the saved run agree about what was actionable.

### The shoreline exists; it is simply already observed

From the reconstructed final states, e.g. `sol`: `shoreline_cells` 850,
`exterior_shoreline_cells` 827, `eligible_never_observed_exterior_shoreline_cells` **0** —
the object has a large exterior shoreline, but every cell on it has already been observed.
`boardFrame` is the same shape: 634 exterior shoreline cells, 0 eligible. Meanwhile 98.75%
of the missed truth is not on the shoreline at all.

The captured helper traces show the upstream gate directly. For `boardFrame`,
`candidate_state_consensus` was called 8 times and returned `allowed=False` every time —
one recorded call is `open_support_count=1, map_resolved=0, boundary_resolved=79,
raw_support=80` under `strict_open_majority_over_resolved_state`, which is why zero
candidates ever reached the "before consensus" count. For `sol`,
`_candidate_continuation_from_projected` was called 4 times, 3 allowed and 1 not.

## Oracle-1 vs Oracle-2 trajectory cross-check

Verified from the raw `result.json` files, not from the audit: **17 of 25 objects have
byte-identical trajectories**; 8 differ (110 beams, 111 blackBoard, 116 ceiling, 172 pipe,
178 sol, 202 wall, 210 wall.008, 224 woodBase).

Within the file-authoritative focus six: **4 of 6 identical** (225, 166, 115, 123), with 178
`sol` and 210 `wall.008` differing.

This reconciles with the Oracle-2 report's "five of six", which used the *named* deficit list
including `plank` (174) rather than `wall.008` (210). `plank` is confirmed identical here,
and it is the 7th-largest miss count (259) behind `wall.008` (404). Both statements are
correct for their respective sets; the six-largest-by-count set is the one this audit uses.

## Demo

```text
previews/classroom-oracle-3-audit/demo/Demo.md
previews/classroom-oracle-3-audit/demo/overview.png
previews/classroom-oracle-3-audit/demo/objects/instance_{0115,0123,0166,0178,0210,0225}_final.png
previews/classroom-oracle-3-audit/demo/frames/frame_0000..0034.png      (35 frames)
previews/classroom-oracle-3-audit/demo/classroom-oracle-3-demo.mp4      (1280x780 @ 4 fps, 35 frames)
```

MP4 encoding was available and the video was written. The 35 frames equal the sum of the
focus six's Oracle-1 fixation counts (6+2+19+4+3+1), so the sequence is complete.

`Demo.md` states explicitly that panel 4 "is deliberately post-hoc and diagnostic. It never
participated in gaze selection," and the panel is titled *final truth misses by first
rejection rule*.

Inspected: `frame_0000` (sol fixation 1/6), the final frame of every focus object, and
`overview.png`. The images show the diagnosis directly — in panel 3 the map's angular
support (gray) with its shoreline (orange) hugging it, and in panel 4 the missed truth (red,
not-shoreline) lying in territory disconnected from that support. `boardFrame` is the
clearest single case: the gray support forms three sides of a rectangular frame and the red
misses are exactly the missing fourth side, angularly separated from the support and
therefore never on the shoreline.

Presentation limitation, not scientific: in some frames panels 3 and 4 clip the chart at the
bottom edge of the panel. The underlying measurements are unaffected.

## Interpretation

**Measured.** 98.75% of all 3,670 reachable-but-uncovered samples are excluded by the very
first Cyclopean test, `NOT_SHORELINE` — they are in the complement of the map's angular
support but not adjacent to it. `INTERNAL_COMPONENT`, `PREVIOUSLY_FIXATED_CELL` and
`OUT_OF_CHART` never fired at all, and `ELIGIBLE_NEVER_OBSERVED_EXTERIOR` is zero, so the
exterior-only topology rule and the never-observed restriction are not where the loss
happens. On the FSG6f side, 21 of 25 objects still had OPEN frontier at termination and were
stopped at candidate formation or by `strict_open_majority_over_resolved_state`.

**Interpretation, clearly labelled as such.** These two facts are consistent with a single
mechanism: the Cyclopean handoff can only grow outward one ring from existing support, so
target surface that is angularly *disconnected* from what the map already holds is
permanently invisible to the selector, no matter how much of it remains. That also explains
Oracle-2: widening the domain adds territory but does not connect a disconnected component,
which is why five (by the named set) of the deficit objects re-ran byte-identically. It is
an inference from the histograms and the traces, not a separately tested claim.

No numerical outcome here is a PASS/FAIL threshold, and no threshold is proposed.

## Next decision — not taken here

The audit isolates one dominant clause: the shoreline-adjacency precondition in the
Cyclopean eligibility test. A causal test would modify exactly that one rule and re-run the
identical 25 targets and seeds — Oracle-4. That changes controller behaviour, so it is
Luiz/Chat's call, and nothing was changed in Oracle-3.
