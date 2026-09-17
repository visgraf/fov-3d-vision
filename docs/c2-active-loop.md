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

## After the second run (2026-09-17)

The noise is now one number across levels at the manifest's value (0.07 small, 0.035 full),
C1's checks hold with the per-cell σ, the walls yield fine cells, and coverage-first spreads
over the cap (50 distinct directions) with the lowest error of the five. `info` still locked
(14 distinct; 37 fixations at (−26°, +56°), the ceiling, where a coarse measurement from afar
said 11 m and the surface is at 1.9 m), `oracle` half so. Code's reading is right: "known
measurable" meant measured at *any* level, so a ceiling measured coarsely — and wrongly — from
afar counted as measurable, the fovea found nothing there, and the gain never fell. Three
changes in `belief.py`: (1) known measurable means measured at the fine levels (0–1); a fine
look that finds nothing retires the direction for `info` and `oracle` as it already did for
`coverage` (self-test: a coarse measurement plus an empty fine visit scores below an unseen
direction); (2) cells outside the field of regard count for nothing — they were pulling every
edge candidate, which is why `info`'s first thirteen fixations all sat at ±56–60°; (3) the
oracle gets an explicit inhibition of return (3°), because "look where you are most wrong" at
a depth edge the fovea cannot resolve has nowhere else to go; the policies keep none — the
gain model has to retire a direction on its own, and the record says whether it does. Blank-
walls stub: info 30 of 30 distinct, oracle 30 of 30. Predicted for the third run: `info` with
≥ 40 distinct directions and fine coverage near coverage-first's; the ranking coverage ≈ info
< random < oracle ≈ targets on median ρ error, as on the stub.

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

### Second run (2026-09-17, after `cac7712`: per-cell noise, the visit map in the policies)

Same five runs in fresh directories (`previews/loop2/`), all measured. Self-tests ok. **C1's
checks hold with the per-cell noise**: `calib_room_sp` all pass, (p) 0.0260 vs 0.0269° (−3%,
9614 cells), level 0 RMS 0.30 s₀, RMS/bound 5.82 (was 4.58: the bound fell from 0.0063 to
0.0051° with the per-cell σ), floor 0.13; `calib_room_full_sp` all pass, (p) 0.0159 vs 0.0208°
(−24%), level-0 RMS/bound 9.76 (was 7.70). `noise_rel_equiv` per level is now one number to
within 25%, rising slightly with level: `sp` p000 0.0705 / 0.0751 / 0.0793 / 0.0900 / 0.0893
(median over pairs 0.066–0.081), the manifest's 0.07 at 64 spp; `full` p000 0.0340 / 0.0351 /
0.0380 / 0.0413 / 0.0419 (median 0.032–0.037), the manifest's 0.036 at 256 spp. The loops carry
0.0704 / 0.0748 / 0.0801 / 0.0893 / 0.0893 (was 0.177 → 0.084).

| policy | rays | wall | distinct dirs | cover any / fine | ρ err median all / fine (1/m) | depth err median all / fine (m) | gross | z RMS | vergence err median (m) | gated |
|---|---|---|---|---|---|---|---|---|---|---|
| targets | 7.995e7 | 16.7 s | 50 | 0.993 / 0.201 | 0.1397 / 0.0149 | 1.128 / 0.059 | 0.609 | 0.57 | 0.01 | 28939 |
| random | 7.995e7 | 16.2 s | 49 | 0.996 / 0.116 | 0.1111 / 0.0253 | 0.864 / 0.153 | 0.555 | 0.51 | 0.39 | 34582 |
| coverage | 7.995e7 | 18.9 s | 50 | 0.994 / 0.138 | 0.1052 / 0.0249 | 0.836 / 0.127 | 0.557 | 0.49 | 0.51 | 41465 |
| info | 7.995e7 | 21.4 s | 14 | 0.942 / 0.013 | 0.1126 / 0.0305 | 0.900 / 0.318 | 0.553 | 0.32 | 9.07 | 25073 |
| oracle | 7.995e7 | 23.3 s | 25 | 0.983 / 0.039 | 0.1386 / 0.0333 | 1.031 / 0.195 | 0.595 | 0.42 | 1.16 | 59530 |

Per-fixation timings, medians (choose + render + infer + judge, s): targets 0.000 + 0.133 +
0.145 + 0.029; random 0.006 + 0.105 + 0.153 + 0.037; coverage 0.067 + 0.100 + 0.159 + 0.034;
info 0.151 + 0.091 + 0.137 + 0.028; oracle 0.172 + 0.079 + 0.169 + 0.031.

Rankings (reported, not judged): by median ρ error, **coverage 0.1052 < random 0.1111 < info
0.1126 < oracle 0.1386 < targets 0.1397**; by fine coverage, **targets 0.201 > coverage 0.138 >
random 0.116 > oracle 0.039 > info 0.013**. On the fine band's own error targets wins (0.0149),
then coverage 0.0249 ≈ random 0.0253. Coverage and info are within 7% of each other on error
and both ahead of target order, as predicted; random is not behind but between them.

**Checks.** (s) exact and (u) pass on all five; (t) and (v) pass on targets, random and
coverage. **(t) fails on info** (z RMS 0.322; `level_sigma_final` 0.0250 / 0.0637 / 0.1205 /
0.1573 / 0.3783; noise per level as above). **(v) fails on info** (fine 0.013) **and oracle**
(0.039) against half of random's 0.116. Eval exits 1 with 3 failures. The record check: the
host-side field on `calib_info` wrote `field_check/` (50 files) and left `field/` (50 files)
untouched; the single-run eval replays (s) ok afterwards.

**Coverage is fixed.** 50 distinct directions, fine coverage above random's, the lowest error
of the five, and the walls now yield fine cells off the cards (fine coverage grows at almost
every fixation; `visited_fine_unmeasured` 0.0046 of the cap at the end).

**Info still locks, oracle half so; reported and stopped, per the prompt.** Info visits 13
distinct directions, then (yaw −26°, pitch +56°) 37 times from k013 on, with ẑ = 11.0 m from
the belief within 2° against a surface at 1.93 m (hence the 9 m vergence median); the fine look
there yields no fine cells (cells 508 at every repeat, fine coverage constant at 0.013) and
the belief is not corrected. Its `visited_fine_unmeasured` at the end is 0.0128 of the cap,
about the fine disc of that one direction. Oracle repeats (+36°, +40°) 10 times and (−46°,
+36°) 12 times, where its belief is wrong (ẑ 1.58 m against 2.69 m) and the fine look does not
fix it. Both directions were measured coarsely from afar, so the new rule counts them as
"known measurable"; measurable at a coarse level is not measurable finely, and the gain to
re-look never falls. The decision on the rule is Chat's. Scanpaths:

- info: (0,0) (−22,56) (−58,−14) (28,−54) (56,26) (58,−16) (−56,24) (34,52) (−46,−42) (60,0)
  (−56,22) (−56,26) (−22,52) then (−26,56) ×37.
- oracle: (0,0) (−22,56) (−58,−14) (28,−54) (56,26) (58,−16) (−56,24) (34,52) (−46,−42) (60,0)
  (−60,0) (−36,46) (−54,30) (36,44) (−22,52) (28,−54) (36,−14) (36,40) (−22,52) (36,40)
  (−34,−10) (36,40) ×2 (60,0) (36,40) ×5 (60,0) (36,40) (30,−8) (−36,28) (−32,−14) (−26,0)
  (−22,52) (−26,−6) (−16,16) then (−46,36) ×12.

No code was changed in this step. Figures replaced.


### Third run (2026-09-17, after `e157d32`: fine-level measurability, gain masked to the cap, IOR 3° for the oracle)

`info` and `oracle` re-run into `previews/loop2/`; `targets`, `random`, `coverage` are the second
run's (repeated below so the table stands alone). Banner: `IOR 0 deg` for info, `IOR 3 deg` for
oracle. `belief.py --self-test` ok. All measured.

| policy | rays | wall | distinct dirs | cover any / fine | ρ err median all / fine (1/m) | depth err median all / fine (m) | gross | z RMS | vergence err median (m) | gated |
|---|---|---|---|---|---|---|---|---|---|---|
| targets | 7.995e7 | 16.7 s | 50 | 0.993 / 0.201 | 0.1397 / 0.0149 | 1.128 / 0.059 | 0.609 | 0.57 | 0.01 | 28939 |
| random | 7.995e7 | 16.2 s | 49 | 0.996 / 0.116 | 0.1111 / 0.0253 | 0.864 / 0.153 | 0.555 | 0.51 | 0.39 | 34582 |
| coverage | 7.995e7 | 18.9 s | 50 | 0.994 / 0.138 | 0.1052 / 0.0249 | 0.836 / 0.127 | 0.557 | 0.49 | 0.51 | 41465 |
| info | 7.995e7 | 24.1 s | 28 | 0.989 / 0.053 | 0.1006 / 0.0252 | 0.774 / 0.239 | 0.531 | 0.44 | 0.51 | 48162 |
| oracle | 7.995e7 | 23.1 s | 50 | 0.993 / 0.074 | 0.1462 / 0.0882 | 1.201 / 0.789 | 0.628 | 0.50 | 2.66 | 25433 |

Per-fixation timings, medians (choose + render + infer + judge, s): info 0.156 + 0.082 + 0.225 +
0.036; oracle 0.175 + 0.083 + 0.147 + 0.037 (the other three as in the second run).

Rankings (reported, not judged): by median ρ error, **info 0.1006 < coverage 0.1052 < random
0.1111 < targets 0.1397 < oracle 0.1462**; by fine coverage, **targets 0.201 > coverage 0.138 >
random 0.116 > oracle 0.074 > info 0.053**. On the fine band's own error targets 0.0149, then
coverage 0.0249 ≈ info 0.0252 ≈ random 0.0253, as predicted.

**Checks.** (s) exact, (t) and (u) pass on all five; (v) passes on targets, random, coverage and
now oracle (50 distinct directions, IOR 3°). **(v) fails on info** (fine coverage 0.053 against
half of random's 0.116). Eval exits 1 with 1 failure. Reported and stopped, per the prompt.

**Info's third lock, measured.** 28 distinct directions: the first 26 spread over the cap (only
4 of the first ten at ≥ 50° from forward; cover any 0.989 by k024), then (yaw +48°, pitch −10°)
23 times from k026 on. At that direction ẑ is 3.61–3.71 m from the belief within 2° and the
surface is at 4.12 m (vergence error 0.4–0.5 m, inside the search range); the field there is
the same every time (1840 cells; consistent rows by level 0 / 93 / 535 / 728 / 332 — no
level-0 cells, 93 level-1 cells on a weakly textured wall), fine coverage stays at 0.053, and the
score is 0.031–0.041 (it was 0.51 at k001). `visited_fine_unmeasured` at the end is 0.0012 of
the cap. This is not the earlier lock: the direction *is* finely measurable (level 1), so the
new rule admits it, and the fovea keeps re-measuring the same 93 cells. Their variance is
floor-limited (1/P_noise + β²·cell², the floor does not average down), so the expected gain of
looking again, ½ log(1 + σ²I), never falls below that of any other direction once the cap has
no unseen cells left — the argmax is a fixed point. The oracle escapes it only by its IOR. The
decision is Chat's: whether info's gain should count only the reducible (noise) part of the
variance, or retire a direction whose fine look yielded fewer cells than some count, or carry
an IOR as the oracle does.

Scanpath (yaw, pitch): (0,0) (−46,2) (48,2) (−12,−46) (4,48) (34,−36) (−32,44) (38,42)
(−50,−18) (50,−18) (−48,28) (50,24) (−30,−12) (30,−12) (16,30) (−28,14) (−12,30) (32,14)
(−40,−40) (18,−52) (12,−28) (−10,−24) (−44,−12) (−46,−6) (12,10) (42,−14) then (48,−10) ×22
with one (48,−12).

No code was changed in this step. Figures replaced.


## What C2 leaves open

- The policies are one-step greedy over a 60° cap; there is no cost to a saccade's length
  and no head motion (D3).
- The cap has no truth outside what the L eye sampled; a policy that never looks somewhere
  is charged only in coverage.
- `info`'s gain model uses one σ per level; C1 measured the floor varying with the surface.
- E₂ and e_max stay at D16 until the policy exists on the renders (the reviewer's C5, the
  sensor as an action, is C3's if time allows).
