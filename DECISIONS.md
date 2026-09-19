# Decisions

Append a block when something is settled. Keep it to four lines. Never edit an old
block — add a new one that supersedes it and say so. "Overturned if" is the point of
the exercise: a decision no one can imagine reversing was not a decision.

## D1 — Ray-value samples (2026-09-12)

What the downstream matcher consumes is records of (origin, direction, value, footprint),
not rectangular images.
Why: the warped raster is not a uniform lattice, and an image format would silently
impose one. Footprint has to travel with the value because peripheral samples average
over a larger solid angle.
Overturned if: the matcher turns out to need adjacency that the stored raster index
cannot supply.

## D2 — Fixed warp, eye rotates (2026-09-12)

The sampling pattern is a constant table of camera-frame directions and footprints,
computed once. A fixation is a rotation applied to it.
Why: it makes the pattern a property of the sensor rather than of the scene, and it
keeps every fixation comparable.
Overturned if: a content-dependent or anisotropic warp turns out to be needed before
Phase C.

## D3 — Fixed head (2026-09-12)

No translation anywhere in Phases A and B. The eye rotates about its own centre; in
the active loop this is saccades and fixations, and in Phase B also vergence.
Why: with a fixed centre of projection there is no parallax within one eye, so a single
panorama is ground truth for every fixation, and with two fixed centres the baseline is
fixed in the head frame and the epipolar geometry never changes.
Overturned if: head motion becomes part of the question, which would be a new phase,
not a change to these.

## D4 — One repository for Phases A–C (2026-09-12)

Phases A, B and C live here together, as roadmap sections rather than directories.
Why: Phase B adds an eye to Phase A's data structures rather than replacing them, and
splitting would duplicate the sample format and the scene tooling.
Overturned if: Phase C turns out to be a genuinely separate piece of work with its own
dependencies.

## D5 — This repository produces samples; it does not do stereo matching (2026-09-12)

The boundary with `active-stereo` is the sample record. This side generates it, and
anything consuming it lives elsewhere.
Why: keeps an engineering-paced project from inheriting a research-paced one's
governance, and vice versa.
Overturned if: the non-uniform-lattice matcher becomes the main line of work here.

## D6 — The repository is `visgraf/fov-3d-vision`, and the scene tooling lives in it (2026-09-12)

Phases A–C live in `fov-3d-vision`. The scene-gathering tools and manifest, first built in
the public `visgraf/w3d-scenes`, are folded in here rather than kept as a dependency.
Why: A1's manifest is the contract A2–A5 read, so two repositories would let the manifest
and the sample format drift apart, which is exactly the fragmentation this setup is meant
to avoid. Extracting a shared scene library later is cheaper than keeping two in sync now.
Supersedes the naming suggestion in D4; the one-repository substance of D4 stands.
Overturned if: the scene tooling is wanted by another project, in which case `w3d-scenes`
becomes its home and this repository depends on it.

## D7 — Reference noise at most a third of the fixation noise it is compared to; spp per scene (2026-09-13)

The reference panorama's relative noise, worst tile and median, must be at most one third of
the noise of the fixation renders it will be compared to; each scene picks its own spp.
Why: the reference exists to read fixation renders against, so its noise only needs to be
negligible relative to theirs; a fixed 1% worst-tile target was set by the darkest patch of
the Classroom and cost ten hours. Supersedes the one-spp-for-both rule and the 1% target.
Overturned if: a matcher turns out to be sensitive to reference noise below that ratio, or
fixation renders go above 1024 spp.

## D8 — Error is measured footprint-aware (2026-09-13)

Each integrated cell is compared to the reference box-filtered to that cell's effective
footprint, centred on the centroid of the samples that reached it, so error is measured at
the resolution the sampling provides there and where its samples are; the resampling floor
(per-sample nearest-pixel disagreement) is reported separately, never folded into the bound.
Why: a fixed-resolution metric would charge the periphery for resolution it was never asked
for and hide that the fovea's error is set by registration and noise, not by content.
Overturned if: the matcher needs a metric at a fixed resolution.

## D9 — The error-versus-budget curve is measured at a declared evaluation scale (2026-09-13)

The curve is measured at s_eval = 2 x s0 (0.2 deg small, 0.1 deg full): the representation is
reconstructed over the sphere at s_eval and compared to the reference filtered to s_eval, at
the targets and over the sphere, with the uncovered fraction beside. D8 remains the
per-sample validation check.
Why: D8 compares each cell at its own footprint, so a coarse uniform render is charged only
for its noise and never for its blur, which is how 2.3 deg pixels "won" at K = 1.
Overturned if: a matcher is shown to need a different scale.

## D10 — Check thresholds are set from measured noise and scene-bounded contrast, not fixed constants (2026-09-13)

The calibration point passes when the metric's score over the render's own seed-pair noise at
s_eval lies in 1.0 to 1.15; the 90 deg control must be at least 3x the largest-K target error;
the D8 validation bound per fixation is 1.5 sqrt(n^2 + (n/4)^2 + floor^2) with n the
fixation's seed-pair noise and floor its binned alignment floor, both measured.
Why: fixed constants were set at the wrong scale (0.073 was the per-pixel noise) or above what
a scene's contrast can deliver (5x on a room whose worst case is a wall against a star card).
Overturned if: a threshold set this way lets a known-wrong result pass a check.

## D11 — E2 = 2 deg and e_max = 45 deg stand, pending the objective (2026-09-13)

The A6 sweep at equal rays favours E2 = 4 for the fixated targets (0.103 against 0.155) and
E2 = 1 for the covered sphere (0.203 on 58% against 0.435 on 22%); e_max 45 wins the targets,
30 the sphere. The criteria disagree, so the profiles keep E2 = 2, e_max = 45 rather than
move on one of them.
Why: the choice is the objective's, and the objective (what the matcher needs: fovea,
coverage, or a budgeted mix) is Phase C's to set.
Overturned if: the objective is fixed to one criterion, in which case the sweep already names
the value, or a policy trades E2 against K.

## D12 — Two eyes on the EYE rig; the D1 record gains an origin per eye (2026-09-14)

EYE stays the head frame and the cyclopean point. The eye centres are at +-ipd/2 on its local
X (63 mm default), each eye a rotation of the same foveated camera about its own centre; a
verged pair fixates one world point, each eye's gaze P - C_i, yaw-then-pitch, no torsion. The
record is D1 with origin = this eye's centre plus eye_id and pair_id, directions still in the
head frame; per-eye folders L/ and R/ are Phase A sequences, pairs.json holds the rig.
Why: the scenes and every Phase A tool stay as they are; only the checker needs the centre.
Overturned if: torsion (Listing's law) is needed for rectification, which changes the gaze
composition in rig.py and not the record; or if a matcher needs the two eyes in one file.

## D13 — Ground truth is a derived sidecar; the epipolar frame is the head's X axis (2026-09-15)

Stereo truth (hit point, the other eye's direction to it, parallax, where it falls in the other
raster, visibility) is computed host-side from the Position and Depth passes and written as
truth.npz beside samples.npz; the D1 record stays what the renderer emitted. Epipolar
coordinates of a head-frame direction are theta from +X (the baseline) and phi about X.
Why: with both centres on X every epipolar plane contains X, so rectification is this one
change of coordinates and needs no re-render; a derived label that is regenerable in seconds
should not be baked into the record.
Overturned if: a matcher needs the truth interleaved with the samples in one file, or the eyes
leave the head's X axis (a tilted or asymmetric rig).

## D14 — Eye torsion is moot while the warp is isotropic (2026-09-15)

No torsion model (Listing's law or other) in Phases B and C. Closes B1's open item.
Why: the record stores directions in the head frame and the warp is radially symmetric about
the gaze (D2), so a torsion of the eye changes which raster pixel sampled which direction and
nothing a consumer of the record can see; epipolar geometry is set by the two centres alone.
Overturned if: D2 is overturned by an anisotropic warp, in which case torsion sets its
orientation and rig.py's gaze composition must model it.

## D15 — A reference matcher lives here as an instrument; D5 stands (2026-09-15)

`tools/stereo_instrument.py` is a block matcher (NCC, winner-take-all, Lucas-Kanade sub-cell
step) on the two foveal maps at s_eval in epipolar coordinates, plus the matcher-free bound
(Fisher information of disparity from gradient² over noise²). It exists so the E₂ sweep has a
number; it is not the research matcher and never sees the non-uniform lattice.
Why: D11's objective is a disparity error, and an error needs an estimate; waiting on
`active-stereo` couples closing E₂ to a research pace and to a matcher tuned to the warp it
would judge. The bound is reported beside the instrument so the ranking of E₂ can be read
without trusting the matcher.
Overturned if: the sweep's ranking differs between the instrument and the bound, in which case
the instrument is the suspect and the sweep waits on a better one; or D5 is overturned.

## D16 — E₂ = 2°, e_max = 45° stays, on evidence: the disparity objective is flat in E₂ (2026-09-15)

Closes D11. The B3 sweep at the small profile: the instrument's inlier RMS at the fixated
cards is 0.272 / 0.269 / 0.261 s₀ for E₂ = 1 / 2 / 4, the bound 0.121 / 0.085 / 0.088 s₀;
E₂ = 2 and 4 are within 3.5% of each other on both, E₂ = 1 is 40% worse on the bound; the
cost is 0.6M / 1.6M / 4.0M rays per pair, so per ray the cheaper setting wins on every column.
Why: at s_eval = 2 s₀ (D9) the fovea's cells are saturated at every E₂ (spacing at 2° is 3,
2 and 1.5 s₀), so the objective D11 named cannot separate E₂ = 2 from 4; E₂ = 1 fails the
cap check (A6, +1.03%) and e_max is Phase C's coverage question, not this objective's. The
standard setting is the middle of a flat optimum at 40% of E₂ = 4's cost.
Overturned if: a finer s_eval or the Classroom scene shows a slope in E₂ larger than the
3.5% measured here, or Phase C's gaze policy prices coverage into the objective.

## D17 — The active loop lives here: matcher, belief and gaze policy; supersedes D5 (2026-09-16)

Phase C builds the closed loop in this repository — a stereo matcher that works over the whole
field a pair covers (`tools/stereo_field.py`, the D15 instrument at the scale the samples
support, level by level), a belief on the head sphere fused across pairs, and the policy that
chooses the next fixation — and ends with a foveated stereo rendering engine for Blender that
runs that loop in one command. `active-stereo` is not a dependency and receives nothing;
bio-3d-vision's ledger of foreclosures is the prior for the policy (no revisiting first, the
objective second, coverage is the likely result).
Why: D5 kept a research-paced matcher out of an engineering-paced project. The matcher Phase C
needs is not that one: the instrument extended to every eccentricity is engineering, and it is
what the loop needs to close. Four repositories in, the loop that ran was the smallest one
(bioeye); the framework that was to receive the samples never ran its loop. The samples stay
the interface (D1), so a research matcher can still consume them from anywhere.
Overturned if: the field matcher cannot recover parallax where the fovea has not been, in which
case the loop has no periphery to guide it and the non-uniform-lattice matcher is back on the
line — as a step here, not a boundary.

## D18 — Phase C's evaluation contract: rays, the L eye's own rays as truth, coverage apart from error (2026-09-17)

The loop is judged at equal cumulative rays (the budget, as in Phase A) over a field of
regard (a 60 deg cap about the primary gaze). Truth is the L eye's own ray distance from the
D1 record, on the cells the L eye has sampled; the belief's error is reported on those cells
(median inverse-depth error, by level band, with a calibration z) and its coverage (any
level, fine) is reported apart from it — the decomposition bio-3d-vision needed to read its
own result. Policies are compared against target order and random; the oracle brackets from
above. The sensor stays at D16 (E2 = 2, e_max = 45) until the policy exists on the renders.
The vergence distance comes from the belief, not the truth, for every policy but target
order, so "where to look" and "at what depth to verge" are separate and the vergence error is
a number of its own.
Why: the reviewer's C0 asked for this contract first; it is written now that the loop exists
and the numbers it contains are the loop's own. Whole-cap error with unmeasured cells at a
prior would need truth the session does not have; coverage beside error says the same thing
honestly.
Overturned if: the ranking of the policies changes with the cap's size or with the budget in
a way the coverage/error split cannot explain.

## D19 — Phase C closed: the engine, and coverage-first as its default policy (2026-09-17)

The repository is a foveated stereo rendering engine for Blender with an active loop on top,
and Phase C is closed with it. The default policy is coverage-first: the fixation whose
foveal disc holds the most cells not yet looked at finely. Expected information stays as an
option; target order and random as baselines; the oracle as a bracket.
Why: at equal rays, on two scenes and two profiles, random, coverage-first and expected
information end within 12% of each other on median inverse-depth error and target order 30%
behind; expected information leads by 2% on the calib room and trails on the classroom at
both profiles, because its variance model does not contain the gross errors that are half
the measured cells at the classroom's noise limit. The policy that does not consult the
model is as good as the one that does and cannot be misled by it — bio-3d-vision's finding
on a uniform sensor, reproduced on the foveated one with a mechanism. D16's warp stood
throughout.
Overturned if: a variance model that carries gross errors (a mixture, an edge-aware floor)
lets expected information beat coverage-first by more than the fixation-to-fixation spread
on the classroom at `full`; or a scene where the field of regard is not fully coverable in
the budget, where the objective has room to matter.

## D20 — Phase D opened: coarse-to-fine in the field, the gross fraction as its number (2026-09-17)

Phase D asks one question the picture put plainly: whether initialising each level's search
from the level above it cuts the gross fraction at every level and improves the loop's depth
at equal rays. Its plan is `docs/phase-d-plan.md`; its decision rule is written there before
the run; its scope is the matcher (D1), a gross-error term in the fusion only if D1 leaves
gross above 20% (D2), and a long run to see saturation, to be decided next week (D3).
Why: at `full` a third of the measured cells are wrong by more than 25%, all at depth edges,
all from a block matcher searching ±3-6 deg on every level independently while the levels
above it already know the answer to a cell. That is engineering with a known remedy and a
number to move; D19's default policy stands until D2 gives expected information a model
that contains what it is wrong about.
Overturned if: D1 does not move the gross fraction at `full` by a third or the error by the
run-to-run spread — then the edges are the window's, not the search's, and the next step is a
smaller window or an edge-aware one, not a deeper pyramid.

## D21 — D1 closes as a diagnosis; coarse-to-fine is not written; D20's rule withdrawn (2026-09-18)

D1a (`docs/d1-gross-diagnosis.md`, measured, four records) found that the repository's two
"gross" are different things and that D20's number is mostly the wrong one. On
`class_coverage_full`, by area, 41.5% of the fused cells are wrong or beyond 25% in rho, and
74.6% of that is *resolution*: right peaks at levels 3-4 whose honest 0.3-cell error exceeds a
quarter of the parallax. Those cells are inside the variance model. What is outside it —
window 11.3%, occluded 9.2%, search 4.9% of the bad area — is about a tenth of the judged
area, not a third. Curing every wrong peak would move the 25% number by a sixth; D20 asked for
a third of it from a matcher. The rule is withdrawn as unreachable by construction, not failed.

Coarse-to-fine is not written. The parent oracle is its ceiling with a perfect safety valve:
16% of the wrong peaks at levels 0-3 cured on the classroom at `full`, 1504 right peaks put at
risk for 3044 cured; net harmful at levels 1-2 on `calib_room_full_sp` (2780 cured, 8327 at
risk at level 2). D20's "overturned if" fires on the oracle, without the run.

Phase D's numbers from here: in the loop, the **outlier fraction** — beyond 25% *and* beyond
3 sigma of the belief's own sigma (`belief.metrics`: gross = coarse + outlier, exactly); in the
field, the **wrong-peak fraction per level** on the saved pairs, by kind. The 25% gross stays
reported, by band. D19's mechanism is restated: the variance model misses about a tenth of
the cells, not a third; that expected information trails coverage-first all the same is left
standing, and is now a smaller claim.
Why: a threshold relative to rho calls a coarse measurement gross for being coarse; a
decision rule on that number rewards nothing a matcher can do.
Overturned if: the re-judged runs put the outlier fraction near the gross fraction (the
belief's sigma then does not cover its coarse cells and (t) has been passing on inliers only).

## D22 — D2 closes: at one look the field's outliers are the scene's; the neighbour test stays an option (2026-09-18)

D2a and D2b (`docs/d2-wrong-or-right.md`, `docs/d2b-neighbour-test.md`; measured, offline, on
`class_coverage_full` and `calib_room_full_sp`). Tried against the wrong peaks, in order: the
parent as a prior (the oracle: 16% cured, net harmful on the calib room), a 3 x 3 window
(loses at every level on both scenes), five truth-free features (best 44.5% rejected at 90% of
the right kept; the NCC peak below a coin), agreement with the neighbours (the best feature at
every level on the classroom, 44-50% at levels 0-2; as a one-cell test it cuts wrong peaks by
32 / 32 / 23% for 2% of the right ones), a cross-validated logistic score of all six (AUC
0.72-0.79). The neighbour test's offline rule — a third at each of levels 0-2 — was missed by
one point at two levels and ten at the third, so by the rule written before the run the loop
was not run with it. It would not have changed the account: outside-the-model area goes from
10.5% to 9.2% of the judged area, and of that 9.2%, occluded and window are 8.2. The test
removes half of the search kind and a sixth of the window kind; what is left is depth edges
and half-occlusions, which agree with their neighbours along the edge and with their parents
across scales.
Decision: `--nb-tol` stays in the field and the loop, off by default; no default changes
without a loop result. D2 closes. The remaining remedy inside Phase D's scope is not in the
matcher: a loop can look again. D4 runs to saturation and its record says whether a second
look is a test (`tools/second_look.py`).
Why: four remedies and six features, each judged offline in under a minute against a rule
written first, all say the same thing about the same 8% of the area.
Overturned if: the long run shows the bad looks are not repeatable across fixations
(P(second bad | first bad) near the base rate) — then the outliers were the matcher's after
all, and a consensus fusion removes them.

## D23 — A consensus among the fine looks, judged by re-fusing D4's record; the default follows the rule (2026-09-18)

D4 (`docs/d4-long-run.md`, measured): the budget curve is flat after the cap is covered
(median rho error 0.0423 at 50 fixations, 0.0387 at 500); bad looks repeat (61.8% against
11.3%), so D22 stands; and the belief's inverse-variance mean is worse than a cell's first look
at every multiplicity (27.9% against 25.2% of the fine cells beyond 25%), because a confident
wrong peak, once averaged in, never leaves. Two looks are a test where one is not: a pair that
disagrees holds a bad look 94% of the time, a pair that agrees 14%.
Decision: `belief.ConsensusBelief` — the fine looks of a cell (levels 0-1, one per fixation,
up to six) are kept, the cell's fine verdict is the fusion of the largest set of mutually
agreeing looks when that set is a strict majority, a cell without a majority is *undecided*
and falls back to its coarse stream; verdict and coarse stream are summed when they agree and
the surer stands when they do not. `--fusion consensus` in the loop; `active_eval.py --refuse
consensus` re-fuses a recorded run without rendering. It becomes the loop's default only if
the rule in `docs/d5-consensus.md`, written before the run, is met on D4's record, and one
live 50-fixation run confirms the Blender-side path. Phase D closes after it either way.
Not claimed: that it repairs the belief's overconfidence. z RMS is computed on inliers, so its
climb (0.77 to 1.66 over 500 fixations) is not the wrong peaks'; it is the noise part of the
variance averaging down over looks whose errors are correlated. That is left open, by name.
Why: the one remedy for outliers that this sensor has and a matcher does not is another look,
and the record to judge it on already exists.
Overturned if: the undecided cells, given a third look, do not resolve (a loop that looks
where its looks disagree and stays undecided has found the scene's 8%, not a test).



<!-- FSG1_HANDOFF_20260919 -->
## D-FSG1 - A local stereo measurement before surface growing

Agreed experimental scope, not a measured Blender result: use per-eye Blender
`pass_index` masks as oracle instance segmentation only; infer geometry from RGB
and calibration; store positions in the fixed head frame with its origin at the
midpoint of the eyes. Blender world and the rotating fixation frames are distinct.

Acquire padded perspective pairs for fronto, tilted and depth-step fixtures. Use
SGBM plus bounded RGB-only subpixel refinement, then retain only the central core.
Truth is exported separately for evaluation. Keep all Phase C/D code and defaults.
No fusion, frontier policy, peripheral preview or object switching in FSG1.

Prospective interior gate per case/per adequately supported instance: >=90%
coverage, <=1% median and <=3% p95 relative left-eye range error. The full profile
at its declared default spp is the reported instrument result. Boundary and
singly-visible regions are separately reported, never silently filled.

What would change the next step: a real full-profile miss without a demonstrated
implementation bug requires a decision from Luiz/Chat before surface fusion.

Outcome 2026-09-19 (small profile only; evidence in `docs/fsg1-single-patch.md`
Workstation Results and `docs/log.md`): the real `small` suite passes `fronto`
and `tilted` on every criterion and fails `step` instance 2, the 3.4 m
background, at 1.136% median and 4.111% p95 against the 1% and 3% targets. The
per-instance rule in this decision is what caught it; the pooled `step` figures
passed. Measured diagnosis: bounded refinement removes SGBM's subpixel bias
everywhere (|median| <= 0.022 px) but scatters 0.2185 px on an 11.28 px
disparity; a 1024 spp diagnostic re-render halves the scatter to a pass while
SGBM's bias is unchanged, so it is render noise at the small profile's angular
resolution, not a geometry, orientation, indexing or calibration fault. No code,
threshold, fixture or matcher parameter was changed, and the full profile was not
run. The gate itself is not challenged; what is open is whether `small` was ever
in its scope, since the decision names the full profile at its default spp as the
reported instrument result. Nothing here yet speaks to a full-profile miss, which
is the case this decision's rule above was written for.
Passing these controlled fixtures justifies considering two overlapping patches;
it does not demonstrate complex-scene or complete-object reconstruction.

Details, validation limits and Results: `docs/fsg1-single-patch.md`.

## D-FSG1a - Assess the unchanged full profile after the small-profile miss (2026-09-19)
Authorize one default full/256-spp FSG1 suite at seed 17; small/64-spp remains FAIL, and no FSG2 work is authorized.
Why: software/calibration checks passed; the remaining small-profile miss warrants measuring the already-declared reporting configuration, not retuning it.
Supersedes only the small-pass prerequisite in sections 4-5 of fsg1-code-prompt.md; preserve every threshold, fixture, estimator setting, failed record and per-instance gate.
Overturned if: calibration/provenance fails or full misses its gate; stop and return the evidence to Luiz/Chat without tuning or beginning fusion.
