# Reality Check 2 — let the observer finish

## Question

Reality Check 1 produced coherent geometry on a moderately realistic mixed-texture target, but both full records ended only because the inherited six-fixation experiment limit was reached while frozen FSG6f still said `continue`.

Reality Check 2 asks the simplest follow-up:

> If those exact saved states are not interrupted at six looks, does the unchanged observer continue to useful new surface and eventually stop by its own `no_frontier` rule?

## One scientific change

The six-look interruption is removed.  Nothing else in perception changes.

The first six full observations are **not rerendered**.  For each seed, the runner loads the exact Reality Check 1 map, gaze history, completed binocular observation history, and the final FSG6f `continue` decision.  Acquisition resumes at the already-recorded `next_gaze_deg`.

Frozen:

- Reality Check 1 scene, target geometry, texture and clutter;
- seeds 2111 and 2179 and their exact first six records;
- fixed head, static scene, oracle target segmentation;
- FSG1 stereo, 2.10 m vergence and full 256 spp instrument;
- FSG3 12 mm fusion;
- FSG6f frontier/state/consensus/corridor/ranking policy.

Scientific stopping is exactly `no_frontier` from frozen FSG6f.

A 24-total-fixation watchdog exists only to bound an accidental non-terminating run.  Reaching it is reported, not turned into a quality or integrity FAIL.

## Interpretation

There is again no tuned numerical quality PASS threshold.  The useful questions are descriptive:

1. how much additional visible surface is acquired after look 6;
2. whether added views preserve geometric coherence;
3. whether FSG6f eventually reaches `no_frontier`;
4. whether the two stochastic trajectories become similarly complete even if their paths and fixation counts differ.

The exact Reality Check 1 coverage at look 6 is the baseline for each seed.  No alternate seeds, scene edits, policy changes, low-gain stops or rerenders are allowed in response to the result.

## Results

Run on the workstation 2026-09-21 (Blender 5.2.1 LTS headless, Cycles, OPTIX on
RTX 4090, driver 595.84; host-side scripts under `.venv/bin/python` 3.12.3 per
the working agreement).

**Status: `REALITY2_INTEGRITY_FAIL` under the prospective rule, because the two
full continuation records do not exist.  Read that token narrowly: no structural
integrity check failed anywhere.  The diagnostic smoke raised a RUNTIME
EXCEPTION, which by the authorization rule blocks full acquisition, so neither
full continuation was run.**

### Provenance and frozen-source audit

HEAD `e9ed914`, clean, on `main`.  **`7c1bfc7` (the Reality Check 1 result) is an
ancestor of HEAD**, confirmed by `git merge-base --is-ancestor`.
`git diff --name-status HEAD~1 HEAD` is exactly eight files, all `A`:
`docs/reality-check-2.md`, `docs/reality-check-2-checks.md`,
`tools/reality2_{public,render_fix,run,eval,compare}.py`,
`tools/dev/check_reality2.py`.

`git diff HEAD~1 HEAD` restricted to every FSG1/FSG3/FSG6f source,
`fsg_render.py`, `rig.py`, `bl_common.py` **and every Reality Check 1 source** is
**empty**, confirmed additionally by per-file sha256 against `7c1bfc7` - all
SAME: `fsg_stereo_supported` 683ae91eaca7b6af, `fsg_stereo_hdr`
67e2ec4667bcc179, `fsg_stereo` faebf0f1b3acbfde, `fsg_evaluate`
a5134b8d8537714d, `fsg_geometry` d9537d8ebc23b60c, `fsg3_surface_map`
1b9dbeb873105ec9, `fsg6f_public` c79f58c9b51f33d4, `fsg6f_frontier`
d636c9405d719916, `fsg_render` 681237fa8533b7cc, `reality1_public`
d2b00211021ff65d, `reality1_run` c0d4f18a682fd9fe, `reality1_eval`
91720f42932b463c, `reality1_scene` b4392230292bb51c, `reality1_render_fix`
bdc068ad931e1072, `check_reality1` b057b1d307aebfde.

### Parent-state audit - 32 of 32 conditions hold on each record

Both parents are intact and were never modified by anything below.

| | `full-seed2111` | `full-seed2179` |
|---|---|---|
| gazes (exactly six, unique) | (-6,-4) (-1,-9) (4,-9) (9,-9) (14,-4) (14,1) | (-6,-4) (-1,1) (4,6) (9,11) (14,11) (14,6) |
| termination | `max_fixations` | `max_fixations` |
| `truth_opened` / `fixed_head` / `static_scene` | False / True / True | False / True / True |
| policy / instrument | frozen FSG6f / frozen FSG1 | frozen FSG6f / frozen FSG1 |
| `public_spec_sha256` | baa71ce4…c528f22 | baa71ce4…c528f22 |
| final decision | `stop: false`, `next_gaze_deg` **(14,6)** | `stop: false`, `next_gaze_deg` **(14,1)** |
| sha256 `prediction_manifest.json` | cd30b47ad26a5447 | ed8d5d827e0c32c2 |
| sha256 `policy_trace.json` | 2bc2172ff0a237ad | 3da8322a35508dab |
| sha256 `surface_map.npz` | 8a77e0530202ddad | 11520678e2725527 |

`surface_map.npz`, `maps/00..05`, `patches/00..05` and `acquisitions/00..05` are
all present on both.  The saved `small` seed-2111 parent is also present, so the
smoke was run rather than skipped.

### Checks - all before acquisition

`py_compile` clean on all six new modules.

```
[reality2-scene]  PASS {"bounds_deg": [-12.5409329600209, 12.927836122861482, -8.480785357044672, 10.639688570109426], "depth_range_m": 0.08710801971695359, "target_triangles": 120, "texture": {"dynamic_range": 0.3474660813808441, "feature_region_std": 0.11709735542535782, "low_panel_std": 0.010763664729893208, "whole_std": 0.07815825194120407}}
[reality2-policy] PASS exact_parent_continuation=true frozen_fsg6f=true scientific_stop=no_frontier watchdog_total=24 quality_gated=false
[reality2-check]  SUMMARY passed=7 failed=0
```

The scene figures are **identical** to the ones Reality Check 1 recorded, so the
fixture is the same fixture, not merely a similar one.  All seven negatives exit
1: `sixlimit`, `rerenderparent`, `scenechange`, `policycopy`, `truth`,
`qualitygate`, `watchdoggate`.  The current Reality Check 1 suite is still green
(`[reality1-check] SUMMARY passed=6 failed=0`, all six negatives exit 1) and so
is FSG6f (`[fsg6f-check] SUMMARY passed=14 failed=0`).
`reality2_public` digest dba8a00c7f140d14719c14289760af0c160c79770955cecfe27c308622b6362a;
watchdog 24 = 4 x the retired six-look interruption.

### Smoke - the blocking event

```
.venv/bin/python tools/reality2_run.py --parent previews/reality1/smoke-seed2111 --out previews/reality2/smoke-seed2111 --device OPTIX
ValueError: Reality Check 2 fixation has too few target points
RUN_EXIT=1 wall=34s
```

**The continuation mechanism itself worked.**  The parent's six maps were copied
byte-for-byte (verified), acquisition resumed at the recorded `(14,6)`, and
**seven further looks were acquired, fused and replayed successfully** before the
exception.  Measured post-hoc from the saved maps, read-only:

| step | gaze | map points | coverage | Δ coverage | source |
|---|---|---|---|---|---|
| 0-5 | the six parent looks | 10,136 → 22,080 | 0.2565 → **0.5276** | | exact parent copies |
| 6 | (+14,+6) | 23,002 | 0.5442 | +0.0166 | new |
| 7 | (+14,+11) | 23,121 | 0.5454 | **+0.0012** | new |
| 8 | (+9,+11) | 25,553 | 0.6054 | +0.0600 | new |
| 9 | (+4,+11) | 28,371 | 0.6725 | +0.0671 | new |
| 10 | (-1,+11) | 31,500 | 0.7462 | +0.0737 | new |
| 11 | (-6,+11) | 33,544 | 0.7904 | +0.0442 | new |
| 12 | (-11,+11) | 33,775 | 0.7904 | **+0.0000** | new |
| 13 | **(-16,+6)** | — | — | — | **0 target points; run aborted** |

So on the `small` profile, **letting the observer continue took coverage from
0.5276 at the Reality Check 1 stop to 0.7904 seven looks later, +26.3 points**,
with the map still pure in instance {141}, all thirteen gazes unique, every
fused patch replay-idempotent, 12,282 multi-look surfels and approximate surface
median/P95 16.701 / 46.167 mm (`small`-profile figures, comparable to Reality
Check 1's own smoke at 17.597 / 46.199 mm).  That is the useful part of the
answer, and it is descriptive only.

### Diagnosis - frozen-policy behaviour, not an implementation defect

At step 13 the frozen policy selected **(-16°, +6°)**.  The target spans yaw
**[-12.54°, +12.93°]** (from the evaluator's own scene self-test), so that gaze
sits **3.5° beyond the target's left edge** and the foveal crop contains **zero
target pixels** - `oracle_target_px = 0`, `support_on_target = 0`,
`valid_on_target = 0`, against 2,495-6,255 points on each of the seven preceding
looks.  The inherited guard `if len(p.xyz_h) < 100` - **present verbatim in
`reality1_run.py` and unchanged in `reality2_run.py`** - then aborted the run.

Three things were checked before concluding, all read-only:

1. **The parent state is reconstructed bit-exactly.**  For parent steps 0 and 5,
   the calibration loaded from `calibration.json` is key-for-key identical to the
   one `hdr.read_observation` returns live, and `instance_L`, `raw_support_L`,
   `instance_R` and `raw_support_R` all reproduce **exactly** from the saved
   patches.  The six parent maps copy byte-for-byte.  The loader is faithful.
2. **The decision replays deterministically from saved state alone.**  Feeding
   the frozen `fsg6f_frontier.choose_next` the saved map (`map_12.npz`, 33,775
   points), the thirteen-gaze history and the thirteen-entry observation history
   returns `stop: False, next_gaze_deg: [-16.0, 6.0]` - the same choice, offline,
   with no renderer involved.
3. **It is the specified ranking doing exactly what it specifies.**  Three
   candidates were offered, all consensus-allowed and all corridor-allowed:

   | direction | gaze | predicted new area (deg²) | frontier score | OPEN | BOUNDARY | corridor fraction |
   |---|---|---|---|---|---|---|
   | (-1,-1) | **(-16,+6)** | **128.93** | 29.85 | 77 | 21 | **0.327** |
   | (0,-1) | (-11,+6) | 80.94 | 38.69 | 95 | 0 | 0.898 |
   | (+1,-1) | (-6,+6) | 32.94 | 24.84 | 72 | 0 | 1.000 |

   FSG6f's frozen key is `(-area, -score, |dyaw|+|dpitch|, yaw, pitch)`, so the
   **largest predicted new area wins outright** - even though it has the lowest
   corridor fraction, the only non-zero resolved-boundary count, and the lowest
   frontier score of the three.  The strict OPEN-majority rule passes it because
   77 > 0 + 21.

**No code fix was made and no source file was modified.**  Deciding what an
off-object look should mean in a continue-until-`no_frontier` regime - abort,
skip, stop, or fuse nothing and carry on - is a change to the experiment's
stopping semantics, which D-REALITY2 and the authorization explicitly reserve.
Per the authorization rule, the runtime exception blocks full acquisition, so
**`previews/reality2/full-seed2111` and `previews/reality2/full-seed2179` were
never created and `reality2_compare.py` was never run.**  Nothing was rerendered,
no alternate seed was used, and the scene, texture, policy, fusion, vergence,
seeds, watchdog and every numerical constant are untouched.

### Structural FAIL lines

**None.**  No integrity check produced a FAIL line anywhere - not in
`[reality2-check]`, not in `[reality1-check]`, not in `[fsg6f-check]`, and not in
the smoke's own inline assertions (left-rectified ID replay, idempotent replay,
no repeated fixation, pure instance map).  The only failure was the runtime
exception above.

### What this leaves open for Luiz/Chat

The question Reality Check 2 asked is **partly answered and partly blocked**.
Partly answered: on the `small` parent, removing the six-look interruption
**does** produce substantial useful new surface - seven more looks, +26.3
coverage points, geometry and purity intact - so continuing is not futile.
Blocked: **whether frozen FSG6f ever reaches `no_frontier` on this fixture is
still unknown**, because before it could stop it selected a look entirely off the
target and the inherited guard ended the run.  The record now contains two
independent demonstrations that FSG6f's area-first ranking can walk off a
fixture - FSG6c's `max()` case at three looks, and this one at thirteen - which
is evidence about the controller, not about the scheduler or the scene.

The decision that is not Code's to take: what an off-object look means here.
