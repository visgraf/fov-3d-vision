# Step C2 — the loop: belief, policies, one Blender session, bioeye's four panels on the sphere

Written 2026-09-17 before the workstation run. Numbers are **predicted**, **assumed**, or from
the stub (plumbing and geometry, not content) until the log records a measurement.

## What C2 is

The perception–action cycle of the Phase A summary, run for real: observe a verged pair,
infer inverse depth everywhere the pair looked (C1), fuse it into a belief on the head sphere,
choose the next fixation from that belief, observe again — in one Blender session, in one
command. bioeye is the template: a per-cell Gaussian posterior, precision-weighted fusion, a
greedy policy, four panels. What is different from bioeye is the sensor: the periphery is
sampled coarsely and measured coarsely (C1's levels), so a fixation buys something, and the
policy has a periphery to guide it (bio-3d-vision's od-004).

## The belief (`tools/belief.py`)

A grid over the sphere in the epipolar frame (D13), cell s_eval (0.2° at small: 898 × 1796
cells; 0.1° at full), each cell a Gaussian over ρ = 1/|P − C_L|. The head is fixed (D3) and
directions are stored in the head frame, so a cell means the same direction in every pair
and fusion is inverse-variance averaging: a field measurement of cell c is splatted over the
belief cells it covers. Three things the fusion is not naive about, all from the record:

- **Two variances.** C1's σ has a noise part (κ × bound), which averages across pairs, and a
  model floor (β × cell), which does not — the coarse levels' error is the same window on the
  same edge every time. The belief keeps a noise-only precision and the smallest floor seen:
  σ² = 1/P_noise + floor². Without this the periphery looked sure after ten fixations it was
  not (stub: the σ panel went uniformly green).
- **Gating.** A measurement coarser than the belief that disagrees by more than 3σ is
  rejected; a finer one always enters and re-weights. bio-3d-vision's confident wrong match
  at a depth edge must not move a fovea's estimate. Gated counts are reported.
- **The visit map.** Every cell the field *owned* at some level, matchable or not, so the
  policy tells "not yet looked at" from "looked at finely and nothing to measure". This is
  the validity mask bio-3d-vision found worth 65:1 over the variance, and its lock-up on an
  unmeasurable pixel is what the map prevents.

Truth is the L eye's own ray distance (the D1 record's `distance`), accumulated on the same
grid as a footprint-weighted mean of 1/distance, so the belief is judged in the session,
without OpenEXR, on the cells the L eye has sampled. `stereo_truth.py` still runs on the
run's record for the parallax/visibility truth.

## The policies

All choose a direction ω within the field of regard (a cap of `--regard-deg` = 60° about the
primary gaze, 2969 candidates at 2°); the vergence distance ẑ is the belief's estimate within
2° of ω (else its estimate over the cap, else `--z0`; fixation 0 is always straight ahead at
z0). The target-order baseline takes the target's distance as Phase B did. The reviewer's
"where to look" and "at what depth to verge" are separated exactly here; the loop's fovea
search range is 6° so a vergence estimate from the periphery wrong by a factor of two still
lands inside it, and the vergence error |centre depth − ẑ| is reported per fixation.

- `targets` — the target list in order (Phase B's runs; the baseline).
- `random` — uniform over the cap.
- `coverage` — the candidate whose 6° disc holds the most cells not yet foveated (levels 0–1).
  "Not looking twice" and nothing else.
- `info` — expected information: Σ over the cells a pair would measure, out to 14° (levels
  0–2), of ½ log(1 + σ_c² I(e)), with I(e) the precision the field delivers at eccentricity e
  — the running median σ_ρ per level of this run's own fields, self-calibrating, starting from
  C1's numbers — and σ_c the belief's; unseen cells at the prior, visited-and-unmeasurable
  cells at zero. The reviewer's policy, with the visit map.
- `oracle` — the same sum with the belief's actual squared error in place of σ_c² where truth
  exists: "look where you are most wrong". The upper bracket, not a policy.

The policy scores on a 1° grid (block means of the belief's variance): 0.2 s per choice.

## The loop (`tools/active_loop.py`, Blender side)

`fixation_pairs.py` was refactored into `PairRenderer` (setup once, `render_pair` on demand,
`finish`) with `main()` unchanged in behaviour — the stub's `pairs.json` and records are
identical modulo timings, `check_pairs.py` passes. The loop renders pair k, builds the field
in memory (numpy only — no OpenEXR in Blender's Python), fuses, accumulates truth, judges
over the cap, chooses. Noise for the bound: fixation 0 is rendered twice (a seed pair) and
the per-level σ it measures is carried as an equivalent relative noise for the rest of the
run (labelled assumed thereafter). Everything `fixation_pairs.py` writes is written, so the
Phase B tools run on a loop run (`check_pairs.py` and `stereo_truth.py` now report, rather
than crash, with no judged card pairs — loop pairs are kind `policy`). Plus
`field/p<NNN>.npz`, `belief.npz`, `loop.json` with the per-fixation metrics and timings.

Per fixation on the stub: choose 0.2 s, render 0.06 s, infer 0.4 s, judge 0.06 s. Predicted
on the workstation at small: ~1 s per fixation (render 30 ms per eye plus EXR write/read),
a minute per 50-fixation run.

## Metrics, per fixation, over the cap

The decomposition bio-3d-vision needed: **coverage** as area fractions (any level; fine =
levels 0–1; visited) apart from **error** on the measured cells with truth — median |ρ error|
(all, and by band: fine / mid / coarse), inlier RMS (relative error ≤ 25%), gross fraction,
median |depth error| in metres, calibration z RMS on inliers. Cost is cumulative rays.
Unmeasured cells have no truth in the session, so there is no "whole cap at the prior"
number; coverage is that number's other half, reported beside it.

## `tools/active_eval.py` (host side)

Per run, bioeye's four panels on the sphere in a yaw/pitch equirect of the cap: posterior
depth with the scanpath | posterior σ_ρ | |depth error| | coverage and error against rays.
With several runs and `--out`: one chart of every run's curves, a table, `compare.json`, and
the ranking — the result of the experiment, reported, not judged.

Checks, each of which can fail (exit 1):
- **(s) replay** — the belief rebuilt host-side from `field/*.npz` and the L records, in order,
  reproduces `loop.json`'s final coverage and error to 1e-9: the record is complete and the
  figure is of the belief the loop had. Stub: ok on all five runs.
- **(t) calibration** — final z RMS on inliers in [0.4, 2.5] on every run. Stub: 0.66–0.85.
- **(u) learning** — coverage and error at the end no worse than after fixation 0.
- **(v) not twice** — with a random run present, every policy run's final fine coverage is at
  least half of random's: a policy that re-fixates fails here.

`belief.py --self-test`: gating, splatting, inverse-variance averaging, truth accumulation,
the info policy leaving a fixated direction, visited-unmeasured cells counting as no gain,
candidates inside the cap.

## Commands (workstation; each run about a minute at small)

```bash
.venv/bin/python tools/belief.py --self-test
B=scenes/calib_room/calib_room.blend; T=scenes/calib_room/calib_room.targets.json
blender -b $B -P tools/active_loop.py -- --out previews/loop/calib_targets --profile small --policy targets --fixations 50 --targets $T
for p in random coverage info oracle; do
  blender -b $B -P tools/active_loop.py -- --out previews/loop/calib_$p --profile small --policy $p --fixations 50
done
.venv/bin/python tools/active_eval.py previews/loop/calib_targets previews/loop/calib_random previews/loop/calib_coverage \
    previews/loop/calib_info previews/loop/calib_oracle --out previews/loop/calib_compare
# the record is a pairs run: the Phase B tools run on it (reported, no card pairs to judge)
.venv/bin/python tools/check_pairs.py previews/loop/calib_info
.venv/bin/python tools/stereo_truth.py previews/loop/calib_info
```

## Stub results (plumbing and geometry only; 20 fixations)

Ranking by median ρ error over measured cells: info 0.0456 < coverage 0.0470 < oracle 0.0530 <
random 0.0549 < targets 0.0959 /m; by fine coverage: coverage 0.190 > random 0.174 > oracle
0.155 ≈ info 0.154 > targets 0.078. Target order loses because the first twenty targets are
the central rings (six degrees of the cap); the four spreading policies are within 20% of each
other on error and the objective barely matters — bio-3d-vision's finding, on the stub, at
equal rays. Vergence from the periphery: median error 0.5–0.9 m at 2–4 m, inside the search
range. Coarse-band gross fractions are 35–40%: at 3° cells the periphery does not measure
depth to 25%; it says roughly how far, and the fovea has to come.

## Results

*(filled by Code from the workstation run)*

## What C2 leaves open

- The policies are one-step greedy over a 60° cap; there is no cost to a saccade's length
  and no head motion (D3).
- The cap has no truth outside what the L eye sampled; a policy that never looks somewhere
  is charged only in coverage.
- `info`'s gain model uses one σ per level; C1 measured the floor varying with the surface.
- E₂ and e_max stay at D16 until the policy exists on the renders (the reviewer's C5, the
  sensor as an action, is C3's if time allows).
