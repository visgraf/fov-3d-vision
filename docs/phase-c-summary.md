# Phase C — summary

`visgraf/fov-3d-vision`, 2026-09-16 to 2026-09-17. State at `81dff57` plus this closing commit,
Phase C closed. Every number below was measured on the lab workstation (Blender 5.2.1 LTS,
OptiX, RTX 4090) unless marked assumed or predicted; the notes in `docs/` hold the commands.

## The question

Phases A and B built a foveated stereo sensor and measured it: a warp, a rig, a record, a
truth, an instrument, a bound. What none of them had was the loop — the thing that makes a
foveated sensor worth having. The predecessors' record was explicit about this. bioeye closed
an accumulation loop on a uniform sensor in 432 lines and worked; active-stereo built the
framework to hold that loop and never ran it; bio-3d-vision ran thirteen registered
experiments on a uniform sensor and found, consistently, that the gaze objective did not
matter once revisiting was controlled, that coverage was what a loop bought, and that a
foveal weighting laid over uniform samples was strictly lossy — and named the untested form:
a sensor whose periphery is genuinely sampled more coarsely than its fovea. That sensor is
this repository. Phase C's question was whether, on it, the loop closes and what the
predecessors' findings become.

The decisions taken at the start (D17): the loop lives here; a matcher that works lives here,
so D5's boundary with `active-stereo` goes; the policy is open-ended; close fast; end with an
engine. A third-party review proposed the shape (estimator, policy, judge as layers of one
experiment; expected information as the policy; the evaluation contract first) and it was
taken except for the order — the native-lattice matcher it put first was never needed.

## What was accomplished

**C1 — the stereo field.** B3's instrument matched a ±2° map about the gaze. C1 runs it over
the whole disc a pair covers, level by level at the scale the samples support: level l has
cell 2^l × s_eval and owns the eccentricity band where a cell holds at least one sample
spacing — 2, 6, 14, 30 and 62° at the standard warp, five grids of a few hundred to a
thousand cells each, because a log-polar warp has about the same number of cells per octave.
Per cell it returns inverse depth ρ = 1/|P − C_L| by the sine rule with the exact Jacobian, a
left–right consistency flag, and a variance in two parts: the noise part (κ × B3's bound) and
a model floor (β × cell) that the coarse levels' error is made of. Level 0 is the instrument
and better than it — 7% at `small`, 24% at `full` — because the LR test removes cells the
instrument keeps. The periphery does not measure depth at 3° cells (depth RMS 5.6 m at
level 4); it says roughly how far, which is what vergence and coverage need. ~2000 consistent
cells per pair in 0.1 s. Numpy only, so it runs inside Blender.

**C2 — the loop.** One Blender session, one command: render a verged pair, build its field,
fuse it into a belief on the head sphere, accumulate the L eye's own ray distances as truth,
judge over a 60° field of regard, choose the next fixation, repeat. `fixation_pairs.py`
became `PairRenderer` without changing a byte of its output. The belief is a Gaussian over ρ
per 0.2° cell (0.1° at `full`) in the epipolar frame — fixed head, so a cell means the same
direction in every pair and fusion is inverse-variance averaging — with three things learned
from the record: the noise part of the variance averages across pairs and the floor does
not; a coarser measurement that disagrees by 3σ is gated; and a visit map records every cell
the field *owned*, matchable or not. Five policies: target order, random, coverage-first
(the disc with the most cells not yet looked at finely), expected information (the belief's
own predicted variance reduction from one more look, out to 14°), and an oracle that looks
where the belief is most wrong. Vergence comes from the belief, not the truth. 0.3–0.5 s per
fixation at `small`, 1.6 s at `full`; a 50-fixation run in 20–80 s. bioeye's four panels per
run and one comparison chart across policies; four checks that can fail — the record replays
the belief exactly, the σ the belief carries is the error it makes within a factor, the cells
fixation 0 measured are not made worse by later ones, and no policy re-fixates.

**C3 — the classroom and the closing.** The loop on Phase A's realistic interior at both
profiles, and the writing.

## The result

At equal rays, 50 fixations, over the field of regard, median inverse-depth error on the
measured cells (1/m):

| | targets | random | coverage | info | oracle |
|---|---|---|---|---|---|
| calib room, `small` | 0.140 | 0.111 | 0.105 | **0.103** | 0.146 |
| classroom, `small` | — | **0.081** | 0.085 | 0.101 | 0.094 |
| classroom, `full` | — | **0.0385** | 0.0427 | 0.0435 | 0.0453 |

Fine coverage (levels 0–1, fraction of the cap): target order first on the calib room because
the cards are where it looks (0.20); coverage-first first everywhere else (0.14, 0.066,
0.094); expected information last on the classroom at both profiles. Every run improves the
cells its first fixation measured — by half on the classroom, by 0–7% on the calib room,
whose central cards sit in gross-error surround at their depth edges that coarse looks cannot
lower.

Read plainly: **spreading buys error at equal rays and the objective does not.** Target order
loses to every spreading policy where it can be compared (0.140 against 0.103–0.111);
random, coverage-first and expected information are within 8% of each other on the calib
room and 12% on the classroom at `full`; the oracle brackets nothing. This is bio-3d-vision's
finding — the gaze objective does not matter once revisiting is controlled; coverage is what
a loop buys — reproduced on the sensor it said it needed, and it now has a mechanism. The
variance model behind expected information does not contain gross errors, and on the
classroom at `small` half of the measured cells are gross (depth edges everywhere, at a
noise level 2.5× the calib room's), so the model is wrong where it matters and the policy
that trusts it comes last; at `full`, with gross down to a third, it recovers to within 2% of
coverage-first and still does not lead. Coverage-first and random never consult the model.

The engine's numbers, classroom at `full`: 50 fixations, 1.3 G rays, 68–79 s, 92% of the cap
measured, 8–9% at foveal quality, 0.04 /m median error overall and 0.015–0.019 /m on the fine
band — 10–14 cm at 2.7 m — with vergence from the periphery landing within 0.4 m of the
surface at the median.

## What we learned

1. **The loop's mechanics were right the first time; the model took four runs.** The
   session, the record, the replay, the timings — none changed after the first run. Each of
   the four C2 runs found one hole in the model: the noise carried from fixation 0 assumed
   four samples per cell where there was one; the gain scored "not measured" instead of "not
   looked at"; "measurable at any level" let a wrongly measured ceiling stay eligible; the
   gain ½ log(1 + σ²I) promised a reduction the belief's own floor could not deliver. Each
   showed as a lock, each was caught by the record (distinct directions, the field at the
   locked direction, the σ parts), each was fixed in the model, none by a threshold. The
   fourth fix — ask the belief what a measurement would do to its own variance — is the one
   the reviewer's policy needed all along.

2. **The stub caught plumbing and, once long enough, one model error.** Blank walls
   reproduced the visit-map lock; the textured stub at 40 fixations, long enough to cover
   the cap, reproduced the floor fixed point (12 distinct of 40) before the fix. The noise
   carry and the coarse-measurement lock it could not show, because its walls are noise
   texture that fails at every level or none. Phase B's lesson again: a stub's texture
   decides what a matcher can do with it.

3. **A check is a definition, and definitions have bugs.** (p) compared a per-pair
   aggregate with a pooled number (15%) and pooled pairs the instrument never judged; (u)
   compared medians over two different sets and failed on all five classroom runs while
   every measured cell improved. Both were found by Code reading the failure rather than
   forcing it, and both fixes are one sentence in the check's docstring.

4. **The noise limit is a property of the scene, and the manifest knew.** The classroom's
   per-pixel noise at 64 spp is 0.18 relative, 2.5× the calib room's, and the manifest has
   carried that number since Phase A. At `small` the fovea barely resolves its texture; the
   fine band is 4–7% of the cap and half the measured cells are gross. `full` is that scene's
   profile. The prediction of a larger fine band on a textured scene was wrong for a reason
   already on file.

5. **Two variances, not one.** Fusing C1's single σ made the periphery look sure after ten
   overlapping coarse measurements while its error stood still. The floor is the same window
   on the same edge every time; it does not average. Keeping the noise precision and the
   smallest floor apart was needed for the σ panel to mean anything, and it is what made the
   expected-information gain computable honestly in the end.

6. **The oracle is a bracket only with an inhibition of return.** "Look where you are most
   wrong" at a depth edge the fovea cannot resolve has nowhere else to go; with a 3° IOR it
   spreads and still comes last, because being wrong there is not something looking fixes.

7. **Four repositories in, the smallest form of the loop is the one that ran.** The engine
   is `active_loop.py` on top of Phase B's tools: about 1200 lines across `belief.py`,
   `active_loop.py`, `active_eval.py` and the field, numpy inside Blender, no framework. It
   was written in two days and closed in four runs of twenty seconds each.

## Why it matters

The project set out to build a foveated stereo rendering engine and to keep the active-vision
framing in view: what counts is the foveated region and how it supplies data to a dynamic
loop, with the periphery guiding a multi-scale scheme. That is now literally what runs. The
periphery measures roughly how far (levels 2–4), supplies the vergence for the next fixation
and tells the policy what has been looked at; the fovea measures depth (levels 0–1, 10–14 cm
at 2.7 m); and the loop closes in one command on a stock Blender scene. The finding on
policies is the useful kind for an engine: the cheapest policy that does not look twice is
as good as the principled one, so the default is coverage-first and expected information is
an option, not a requirement.

## What it leaves open

- **Gross errors are outside the model.** Half the measured cells at `small` on the
  classroom, a third at `full`, are wrong by more than 25% at depth edges, and no variance
  carries that. A mixture or an edge-aware floor would let expected information score what
  it is actually wrong about; whether it would then beat coverage-first is the one open
  question a next step could answer cheaply.
- **The sensor as an action.** E₂ and e_max were held at D16 throughout; the reviewer's
  "45° few or 30° many" is unrun, and the loop makes it a one-flag experiment.
- **Head fixed (D3), cap of 60°, one-step greedy.** No saccade cost, no head motion, no
  lookahead. The scenes' targets sit inside the cap; a room is not.
- **Truth outside what the L eye sampled.** Coverage is reported beside error because the
  session has no truth for cells never seen; a whole-cap error at the prior would need the
  references from Phase A, and would be the number to publish if this were to be published.

## Deliverables

- `tools/stereo_field.py` — the multi-level field with LR consistency and the two-part
  variance; `tools/belief.py` — the belief and the five policies; `tools/active_loop.py` — the
  loop, Blender side; `tools/active_eval.py` — replay, checks, figures, comparison;
  `tools/fixation_pairs.py` — `PairRenderer`; `tools/dev/fake_blender_loop.py` and the
  blank-walls stub.
- `docs/c1-stereo-field.md`, `docs/c2-active-loop.md`, `docs/c3-closing.md` — the notes with
  their Results as Code wrote them, run by run; `docs/reviews/2026-09-16-phase-c-suggestions.md`
  — the review with its reading; D17, D18, D19.
- `docs/reference/c1_field_calib_room_small.png`, `c2_compare_calib_small.png`,
  `c2_loop_info_calib_small.png`, `c3_compare_classroom_small.png`, `c3_compare_classroom_full.png`,
  `c3_loop_info_classroom_small.png`, `c3_loop_info_classroom_full.png`.
- Runs on the workstation under `previews/loop2/` (calib room) and `previews/loop3/`
  (classroom), each a Phase B record plus `field/`, `belief.npz`, `loop.json`, `loop_fig.png`.

## The picture

`tools/sphere_views.py` puts the scene as it is beside the scene as the engine saw it, in two
formats each: equirectangular, and on the epipolar sphere (φ across, θ down, every epipolar
line a row), RGB and depth, with the scanpath drawn over the engine's RGB and one shared log
depth scale taken from the panorama. `docs/reference/views_classroom_full.png` is the
coverage-first run at `full` on the classroom (50 fixations) against the L-eye panorama
rendered at the full profile (`previews/reference_full_L/classroom`, 7200 × 3600 at 8192 spp,
2137.4 s on the RTX 4090, md5 de47b7629026782015ede6cdaeaefb65; the `small` one 70.1 s). The
engine's RGB is sharp where the fovea has been and blurred in the periphery, dark outside the
field of regard; its depth shows the room where the belief has it and dark grey elsewhere;
the two rows agree in orientation on both scenes. The script's two lines for that run,
measured:

    [views] engine vs truth on 2551239 shared cells: median |rho err| 0.0816 /m, median |depth err| 0.358 m
    [views] sphere at 0.0998261 deg: 58.6% of it seen by the L eye, 40.3% with a depth from the belief; white 1.922, depth scale 0.54-4.98 m

The 0.358 m is C3b's number for the same run (0.351 m over all measured cells) judged against
the panorama instead of the L eye's own rays. At `small` the same policy gives 0.630 m on
640 534 cells (60.6% of the sphere seen, 42.1% with a depth); the calib room's info run 0.869 m
on 878 315 cells (64.0% seen, 54.5% with a depth).

Drawn by confidence (a precision-weighted 3×3 median faded toward grey by σ_ρ), the engine's
depth at `full` is solid on 1.1% of the sphere and at half confidence or better on 5.5% (solid at
σ ≤ 0.020, grey at ≥ 0.089 /m); the fine band alone is `docs/reference/views_classroom_full_fine.png`.
At `small` 0.9% / 5.1%; the calib room's info run 1.1% / 8.0%. Measured, 2026-09-17.
