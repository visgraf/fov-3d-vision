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

## After the first run (2026-09-17)

The loop closed at 0.3–0.5 s per fixation, the refactor was exact and the record replayed;
coverage, info and oracle locked onto one direction at the cap's edge (coverage: the same
direction 49 times) and (t), (v) failed on them. Code's two diagnoses were right and both fixes
are in the model, not the thresholds:

1. **The noise carried from fixation 0 was 2.4× too high** (0.177 relative at level 0 against
   the manifest's 0.073), which made the walls unmatchable at the fine levels — the same
   records judged host-side at 0.07 found thousands of fine cells at 2% gross. Cause, measured
   on the stub: the equivalence assumed four samples per level-0 cell; the wide level-0 map
   holds 1.2 on average and the owned band 1–4. The field now works per cell: the constant is
   the per-sample relative RMS (the Monte Carlo noise per pixel, the manifest's quantity),
   measured from the seed pair as a robust median over cells, and σ_cell = nr × mean_cell /
   √count_cell — for the bound, for the texture gate, in the assumed path too. On the stub
   nr comes out 0.0097–0.0101 at every level (it should be one number; the old equivalence
   gave 0.0185 → 0.0073 across levels, the artefact).
2. **The gain model never learned that a surface is unmeasurable.** `coverage` scored "not
   yet measured", so an unmeasurable direction stayed uncovered; `info`'s zero-gain rule fired
   only on never-measured cells, so a cell measured coarsely from afar and then foveated
   without result kept its coarse σ and its large gain. Now `coverage` scores the visit map
   (not yet *looked at* finely), and for `info`/`oracle` a look counts only where the cell is
   known measurable (measured at any level) or where the fixation would look at it at least
   two levels finer than the finest look that found nothing (levels 0 and 1 are one class: a
   blank wall fails both). The self-test has the three cases; a blank-walls stub
   (`FAKE_BLANK_WALLS=1`, only the cards matchable — the lock scenario) gives info 27 distinct
   directions of 30 and coverage 30 of 30, with info finding the cards (fine coverage 0.074
   against random's 0.058).

Also: `stereo_field.py` on a loop run now writes to `field_check/`, not the record's `field/`
(Code's hazard). Predicted for the re-run: no lock; fine coverage of the spreading policies
above random's on the room's walls; z RMS back inside the band as σ falls with the noise;
`info` and `coverage` within 20% of each other and ahead of target order on median ρ error,
as on the stub. The first run's record follows as Code wrote it.

## Results

Run 2026-09-17 on the workstation (RTX 4090, Blender 5.2.1), calibration room at `small`, 50
fixations per policy, one Blender session per run. All numbers measured (`loop.json`,
`compare.json`, the eval's lines) unless marked assumed. Figures:
`docs/reference/c2_compare_calib_small.png` (the four curves, five runs) and
`docs/reference/c2_loop_info_calib_small.png` (the info run's four panels).

**Refactor check.** `calib_room_c2check` re-rendered in 11.2 s (0.091 s per pair); `check_pairs`,
`stereo_truth` and `stereo_instrument` pass, and the instrument's summary is `calib_room_sp`'s to
the eighth digit (inlier RMS 0.0269°, 37 pairs, 12604 cells, gross 6.2%, bias +0.0107, bound
0.0085, RMS/bound 2.54, info/ray 0.3466): `PairRenderer` is behaviour-preserving.

**Self-tests** (`belief`, `stereo_field`): ok, 0.2 s each.

**The runs.** Every run completed in 15–24 s, 0.3–0.5 s per fixation — three times faster than
the ~1 s predicted (the render is 0.08–0.11 s per pair, the field 0.13–0.23 s).

| policy | rays | wall | cover any / fine | ρ err median all / fine (1/m) | depth err median all / fine (m) | gross | z RMS | vergence err median (m) | gated |
|---|---|---|---|---|---|---|---|---|---|
| targets | 7.995e7 | 15.2 s | 0.961 / 0.179 | 0.2101 / 0.0118 | 1.665 / 0.047 | 0.666 | 0.52 | 0.01 | 1764 |
| random | 7.995e7 | 15.3 s | 0.955 / 0.069 | 0.1641 / 0.0167 | 1.228 / 0.067 | 0.616 | 0.42 | 0.69 | 13030 |
| coverage | 7.995e7 | 17.3 s | 0.563 / 0.004 | 0.2052 / 0.1691 | 1.497 / 1.896 | 0.714 | 0.43 | 0.04 | 5567 |
| info | 7.995e7 | 23.0 s | 0.853 / 0.004 | 0.1894 / 0.1691 | 1.399 / 1.896 | 0.673 | 0.31 | 1.54 | 3680 |
| oracle | 7.995e7 | 21.7 s | 0.887 / 0.004 | 0.1741 / 0.1691 | 1.386 / 1.896 | 0.658 | 0.30 | 2.81 | 2310 |

Per-fixation timings, medians (choose + render + infer + judge, s): targets 0.000 + 0.113 +
0.143 + 0.030; random 0.006 + 0.096 + 0.147 + 0.035; coverage 0.088 + 0.094 + 0.134 + 0.022; info
0.124 + 0.093 + 0.229 + 0.029; oracle 0.141 + 0.077 + 0.178 + 0.030.

Rankings (the eval's, reported not judged): by median ρ error over measured cells, **random
0.1641 < oracle 0.1741 < info 0.1894 < coverage 0.2052 < targets 0.2101**; by fine coverage,
**targets 0.179 > random 0.069 > coverage 0.004 = info 0.004 = oracle 0.004**.

**Checks.** (s) replay ok on all five (exact); (u) passes on all five. **(t) fails** on info
(z RMS 0.310) and oracle (0.298), below 0.4: the belief's σ is conservative by ~3× there
(random 0.42, coverage 0.43, targets 0.52 pass). **(v) fails** on coverage, info and oracle:
fine coverage 0.004 against random's 0.069, i.e. no fixation after the first added a fine cell
in any of the three. Not widened, not changed. The eval exits 1 with 5 failures.

**Diagnosis of (v), measured.** The three policies lock onto one direction at the cap's edge
and re-fixate it: `coverage` fixates (yaw −22°, pitch +56°) at every fixation from k001 to k049
(2 distinct directions in 50; its score is bit-identical at every step, 0.18876); `info` visits
13 distinct directions, then (+58°, −16°) from k013 on; `oracle` 19, then (+60°, 0°) from k020 on.
Two mechanisms, both in the record:

1. *No fine cells away from the cards.* In the loop's own field records, no eccentric fixation of
   the three runs produced a single LR-consistent level-0 or level-1 row (oracle p002, p003,
   p007, p019: 0 and 0; coverage p001: 0 and 0; random's fixations that landed on cards did:
   p002 130 + 188, p019 153 + 200). The belief's fine cells stay fixation 0's 908 (593 with
   truth) in all three runs. The cause is the noise the loop carries: fixation 0's seed pair
   calibrates `noise_rel_per_level` = 0.177 / 0.173 / 0.162 / 0.143 / 0.084 (relative, per
   level), 2.5× the 0.07 this prompt assumed for the host-side check. Run host-side on a copy of
   the info run's record, `stereo_field.py --noise-rel 0.07` judges 6545 level-0 cells over 50
   pairs with gross 4.6% → 2.0% after LR (the walls *are* matchable at the fine scale), while
   `--noise-rel 0.177` judges 79 with gross 49%: the texture and bound thresholds at the
   calibrated noise reject the walls' texture, and only the cards pass. Whether 0.177 is the
   render's noise or an overestimate of the seed pair's σ (measured over the wide map, then
   made relative) is for Chat; the fix, if one is wanted, belongs in the loop's noise carry
   (`active_loop.py`, `noise_rel_equiv`), not in the thresholds.
2. *The gain model does not learn that a surface is unmeasurable.* `coverage` scores
   `best_level > 1` (not yet *measured* finely), not `visited > 1` (not yet *looked at*), so a
   fine look that measures nothing leaves its gain unchanged: at the locked direction 2698 of
   the 2879 belief cells within 6° are visited at level ≤ 1 and 0 are measured at level ≤ 1. The
   visit-map rule in `_gain_field` (zero gain where visited finely and never measured) is
   applied after `coverage` has already returned, and for `info`/`oracle` it does not fire on
   cells a coarse level has measured (P > 0), which is every cell at the cap's edge after a few
   fixations; their variance then sits at the coarse floor, which does not average down, so the
   expected gain of re-looking never falls. This is the lock-up bio-3d-vision described; the
   decision on the gain model is Chat's, per the prompt.

**Vergence.** Median vergence error exceeds 1 m on info (1.54 m) and oracle (2.81 m): both are the
locked fixation's own error (info: ẑ 2.19 m from the belief over the cap against a wall at
3.70 m; oracle: ẑ 0.64 m from a wrong fine estimate against 3.45 m). The prescribed diagnostic
re-run with `--search-deg 8` (`previews/loop/diag_info_s8`, `diag_oracle_s8`) changes nothing
that matters: vergence medians 1.56 m and 1.07 m, fine coverage 0.004, (t) and (v) fail the same
way — the search range is not what is missing.

**What the render decided that the stub could not.** Coarse-band gross fractions are 0.67–0.82
(stub: 0.35–0.40): at 1.6–3.2° cells on the room's walls, the periphery says which side of the
room, not the depth. `info` does not beat `coverage` on the fine band; neither measured it.
The four spreading policies are not within 20% of each other on error (random 0.164 to coverage
0.205), and random is the best of the five: it is the only spreading policy that keeps landing
on cards. Target order wins fine coverage (0.179) because the cards are the only fine-measurable
surfaces and it visits all of them.

**Record hazard (found, not fixed).** `stereo_field.py <loop run>` writes `field/p<NNN>.npz`
into the same directory the loop's own record uses and overwrote the info run's fields (the eval
had already passed (s) on the originals). The run was re-rendered to restore it (identical to
1e-9: final ρ error 0.1894, z 0.3097602631 vs 0.3097602658; one per-fixation line differs in
the fourth decimal) and the host-side field was then run on a symlinked copy. The Phase B tools
on the info run: `check_pairs` ok (0 judged card pairs, reported), `stereo_truth` ok (visible
96.7%, (i) 0.014 s₀, (j) 100%), `stereo_field --noise-rel 0.07` ok (levels 0–4 judged
6545 / 21888 / 34974 / 39827 / 12541 cells; (p) skipped, no stereo.json).

**Per-level σ_ρ at the end of the info run** (`level_sigma_final`, 1/m): 0.0199 / 0.0415 /
0.2166 / 0.2096 / 0.4410; noise note: "calibrated on fixation 0 (seed pair), then carried".

No code was changed in this step.

## What C2 leaves open

- The policies are one-step greedy over a 60° cap; there is no cost to a saccade's length
  and no head motion (D3).
- The cap has no truth outside what the L eye sampled; a policy that never looks somewhere
  is charged only in coverage.
- `info`'s gain model uses one σ per level; C1 measured the floor varying with the surface.
- E₂ and e_max stay at D16 until the policy exists on the renders (the reviewer's C5, the
  sensor as an action, is C3's if time allows).
