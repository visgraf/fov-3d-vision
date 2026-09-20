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

## D-FSG1b - Audit the full-profile coverage miss on saved records (2026-09-19)
Authorize the additive read-only coverage audit on the existing small/64, full/256 and diagnostic-small/1024 seed-17 records; both FSG1 failures stand and no FSG2 work is authorized.
Why: frequent texture rejection identifies a gate, not whether rejected correspondences are correct; fixed pixel support, display clipping, quantization and genuinely weak evidence must be distinguished.
Preserve the estimator, all thresholds, fixtures, reference denominators, provenance, failed records and prior decisions; no new acquisition or automatic adoption follows from counterfactual statistics.
Overturned if: frozen source hashes, exact replay, gate reconstruction or reference metrics disagree; stop and return evidence before drawing a diagnostic conclusion.

## D-FSG1c - Test a fixed soft HDR encoding on saved FSG1 observations (2026-09-19)
Authorize one opt-in candidate: max(x,0)/(1+max(x,0)), then the existing sRGB transfer and uint8 quantization, shared by both eyes for SGBM and its texture score. Keep the original linear-RGB refiner and every numerical matching/acceptance/evaluation setting.
Why: FSG1b identifies post-render clipping in the old encoding, while its tilted counterexample does not justify deleting the texture veto. No fitted exposure or threshold sweep is authorized.
Compare on the existing small/64, full/256 and diagnostic-small/1024 seed-17 records, with exact legacy replay and unchanged fixed reference populations. Preserve all original files and failures; record the candidate separately. No new acquisition, default change, milestone promotion or FSG2 work.
A numerical miss on small does not block the prescribed full comparison: all three existing records are processed once. A source, provenance, replay or integrity exception stops execution immediately. A candidate numerical miss is reported, not tuned away.
The candidate is successful on the existing full record only if it satisfies the original per-case/per-instance 90% coverage, 1% median and 3% p95 range-error rules and identity checks. This is development-set evidence, not independent validation; the synthetic bright-full stress miss and the unexercised half-occlusion case remain explicit. Report any regression on other records.
Overturned if: frozen-source/replay checks fail, or the candidate cannot recover coverage without violating the fixed accuracy rules. Stop for Luiz/Chat; do not alter the mapping, windows, thresholds, fixtures or tests.

Outcome 2026-09-19 (evidence: `docs/fsg1-hdr-candidate.md` Results and `docs/log.md`).
Run once on the three saved records, exit 2. The full record is
`CANDIDATE_PASS_ON_EXISTING_RECORD` with no fails: step foreground coverage
79.319% -> 99.361%, pooled step 87.502% -> 99.445%, fronto 94.786% -> 99.019%,
tilted 98.433% -> 98.912%, every median and p95 still inside 1% and 3%, and 8
pixels lost on the failing instance. The newly accepted geometry is re-derived,
not resurrected, scoring 0.176%/0.867% with none over 3%. The exit-2 miss is the
small record's pre-existing background accuracy failure, unchanged because that
instance had no clipped pixels. Mechanism: the encoding lowers median scores
(4.508 -> 2.708) but collapses exactly-zero scores 14.243% -> 0.014% and removes
all-channel saturation, so coverage returns by deleting the dead zone rather than
by amplifying signal. NOT adopted and no default changed. Three limits stand: the
analytic bright-full stress still fails coverage under this same encoding; on
small/tilted all 29 old texture-only pixels are now accepted and measure
1.914%/4.084%, so the candidate admits weak evidence the veto used to catch
(n=29, an observation, not a population estimate); and half-occlusion is
NOT_EXERCISED in all nine case-records. This is development-set evidence on the
records that selected the candidate, not independent validation. The next step,
for Luiz and Chat, is a held-out geometry and seed plus an additive mirrored-step
or opposite-eye half-occlusion fixture BEFORE any fusion.

## D-FSG1d - frozen HDR prospective validation (2026-09-19)
Preserve all FSG1/FSG1a failures, FSG1b diagnostics and FSG1c development-set outcomes. Keep the FSG1c encoding, matcher and acceptance unchanged. Authorize only the FSG1d two-fixture schedule: small seed 31 once, full seeds 31 and 73 once each, at their default spp. Keep the existing per-instance interior accuracy/coverage gates. Add a nonempty left-eye singly visible reference and zero accepted points in its fixed eroded core. A numerical small miss does not block the predeclared full tests; integrity or unexercised-reference failures do. Analyze every prescribed full record irrespective of numerical misses; no retry, tuning, default adoption, milestone closure, or fusion is authorized. A candidate validation pass is limited evidence on these new opaque textured planar fixtures. What would overturn it: a failed full case/instance/seed, an unsafe core acceptance, invalid reference/provenance, or input/source mutation. Stop for Luiz/Chat after the report.

Outcome 2026-09-19 (evidence: `docs/fsg1-prospective-validation.md` Results and
`docs/log.md`). Executed exactly the authorized schedule: small seed 31 once, full
seeds 31 and 73 once each, 865,075,200 primary samples as calculated, nothing
repeated. Status `FROZEN_CANDIDATE_VALIDATION_FAIL`, with integrity intact
throughout (frozen diff empty, eight pinned hashes verified, inputs unchanged,
295 prior files byte-identical). Passed: `tilted_holdout` on both seeds at new
gaze/range/tilt (99.76%/0.25%/1.11%), and the 1.8 m foreground, where the HDR
candidate reproduced its coverage benefit prospectively (96.96% -> 99.87%, gained
pixels at 0.166%/0.621%). Failed on two counts, neither tunable here. First, the
3.2 m background misses median and p95 on both seeds for BOTH estimators
(1.053%/3.123%), so it is not radiometric; the old 3.4 m background passed with
less disparity, and the measurable difference is lower texture contrast - an
observation, not an established cause. Second, the half-occlusion test is finally
EXERCISED (4,608 raw / 3,528 core) and seed 31 leaks: both estimators accept 2
core pixels whose truth is the 3.20 m background, the candidate placing them at
1.824 m - on the foreground plane, a 1.377 m error - while every existing veto
passed. The leak is the shared matcher's, not the encoding's, and it is
seed-dependent, so one seed would not have shown it. Per this decision's overturn
clause, a failed full instance and an unsafe core acceptance both apply: no
limited adoption and no two-patch experiment follow. The next step is Luiz's and
Chat's, and would need an explicit occlusion-rejection mechanism and a decision
about the far-surface accuracy limit before any fusion.

## D-FSG1e - diagnose refinement and false cycles without changing the instrument (2026-09-19)
Keep FSG1d's validation FAIL, the HDR candidate, and all earlier results unchanged.
Replay seven existing full-profile pairs and audit raw SGBM, each of the three
frozen refinement updates, and every accepted singly-visible point; no new rays.
Why: the 3.1234% tail is numerically compatible with a refinement cap, and two
false matches pass all existing vetoes. Neither mechanism is established yet.
Overturned if: exact replay/provenance fails or the fixed support/reference cannot
be reproduced; stop rather than interpreting those diagnostics. No default
adoption, milestone closure, gate change, new candidate, or fusion is authorized.

Outcome 2026-09-19 (evidence: `docs/fsg1-stage-visibility-audit.md` Results and
`docs/log.md`). Audit completed with exact replay on all 14 combinations, inputs
byte-identical, zero new samples. CONFIRMED the cap explanation: on the failing
3.2 m background raw SGBM is 0.099%/0.359% median/p95, refinement degrades it
monotonically to 1.053%/3.123%, 3,482 of 3,499 bad pixels were good beforehand,
d_true = 23.976198 px with 90.5% of initialisations at integer 24, the top final
atoms are 23.25 px (1,631) and 24.75 px (1,240), and the cap cohorts' median
errors are 0.031234340844770295 and 0.03126471011551888 against the predicted
0.03123434084477 and ~3.12647%. The caps are ~11% of accepted and ~88% of all
>3% pixels, driven by an ill-conditioned gradient denominator (tail 2.9-43x worse
than safe). REFUTED any simple removal: on the ORIGINAL 3.4 m background, whose
true phase is 0.565833, raw median 1.620% would fail the gate and refinement
rescues it to 0.785%. The half-occlusion leaks are NOT one mechanism: all six
accepted points fail cycle_both_endpoints_pass while passing the interpolated
check, but one is true cancellation of two failing endpoints, four are masking by
a passing near endpoint, and one is a genuinely self-consistent wrong cycle at a
single right pixel - so endpoint checking alone would catch five of six. Matching
IDs, ID-boundary distance and right-bin collision counts would have flagged none.
Nothing was adopted, changed or swept; per this decision no gate change or fusion
follows, and the reused seeds 31/73 are now diagnostic data rather than a holdout.

## D-FSG1f - One update and footprint-supported reciprocity (2026-09-19)
Authorize one opt-in HDR candidate: exactly one original photometric update, separate checks on all positive-weight right disparity contributors, and full 5x5 reciprocal support around both matched endpoints. Encoding, matcher settings, geometric calibration, original vetoes, reference masks and numerical evaluation gates remain unchanged.
Why: FSG1e confirms damaging repeated updates and mixed interpolation failures, including one self-consistent wrong cycle. Report one-update-only and endpoint-only controls to separate geometry changes from support rejection; neither is an automatic fallback candidate.
Run the seven existing full-profile pairs once, replay both stored baselines exactly, persist RGB-only predictions before evaluation and preserve all historical failures. Seeds 17/31/73 are development/diagnostic data; no new rays, tuning, default, closure or fusion is authorized.
Overturned if: source/provenance/replay/reference integrity fails, or the named candidate fails any unchanged full per-instance interior gate or the existing zero-accepted-occlusion-core rule. Complete numerical comparisons, then return the results; never select whichever control happens to pass.

Outcome 2026-09-19 (evidence: `docs/fsg1-supported-candidate.md` Results and
`docs/log.md`). One comparison on the seven existing full pairs, zero new samples,
exact replay and inputs byte-identical. Status `CANDIDATE_PASS_ON_DIAGNOSTIC_RECORDS`:
the named candidate meets every unchanged interior gate on all seven pairs and
both instances, with no fail line anywhere - every NUMERICAL_FAIL emitted belongs
to a stored baseline. The two failing backgrounds move from 1.053%/3.123% and
1.066%/3.127% to 0.383%/1.606% and 0.382%/1.632%, the gain measured on common
support (median 1.053% -> 0.388%, >3% 10.466% -> 0.152%), and the mandatory 3.4 m
regression case IMPROVES rather than regressing (0.796% -> 0.333% median). The
candidate accepts 0 raw and 0 core singly-visible pixels on both seeds and no new
leak appeared. Attribution stays open: all six tracked locations have
one_step_valid=False, so the one-step validity already rejects them before either
new veto, and the endpoint and footprint rules reject them too - the records
cannot show which mechanism matters. Costs are real and charged: the footprint
rule removes 2.611% and 2.413% of accepted interior on the occluded background
(coverage 94.555%/94.665%, clearing 90% by ~4.5 points) and roughly half the
boundary population. Per this decision nothing is adopted: seeds 17/31/73 are
development/diagnostic data, so this is not validation and cannot be relabelled
prospective; no default, milestone closure or fusion follows, and neither control
was selected. The next step - whether to propose a fresh validation geometry and
seed for this candidate - belongs to Luiz and Chat.

## D-FSG1g - final prospective validation of the simple local stereo instrument (2026-09-19)
Freeze the FSG1 instrument for one final validation as: FSG1c fixed soft-HDR encoding, unchanged SGBM, exactly one original photometric refinement update, and the original validity predicate. Do not use FSG1f endpoint or footprint-supported reciprocity.

Why: on the seven diagnostic pairs, one update passed every unchanged interior gate and rejected every previously observed half-occlusion leak before the additional FSG1f vetoes acted. The footprint rule cost about 2.5% interior support on the occluded background and about half the accepted boundary population, so it is not justified by the present evidence.

Validate only on the new FSG1g fixtures and fresh seeds 101 and 149. The suite contains four frontoparallel planes whose full-profile disparities have fractional phases 0, .25, .50 and .75, plus two mirrored finite-foreground occluders. Use the unchanged full profile at 256 spp; small seed 101 is only a smoke/integration run. No parameter search, rerender after a numerical miss, threshold change, hole filling, or estimator adaptation is authorized.

Pass rule, evaluated separately for every full seed and every instance: interior coverage >= 0.90, median relative range error <= 0.01, p95 <= 0.03; zero accepted points in each prescribed eroded singly-visible core; and on each occluder, at least 100 accepted jointly-visible boundary points with median <= 0.01 and p95 <= 0.03. A zero/too-small population is NOT_EXERCISED, not a pass.

If every prescribed full gate passes on both seeds, close FSG1 / Increment 1, record this one-update instrument as the FSG1 local RGB-D instrument, and authorize (but do not implement in this run) Increment 2: two overlapping patches in the fixed head-centred map. If any full gate misses, preserve the failure and stop for Luiz/Chat. No control or alternative candidate is selected after seeing results.

Outcome 2026-09-19 (evidence: `docs/fsg1-final-validation.md` Results and
`docs/log.md`). STOPPED at the smoke stage on an integrity failure; the two full
acquisitions were NOT run, so this decision's pass rule was never reached.
`[fsg-final] FAIL ValueError: half-occlusion NOT_EXERCISED: raw`, smoke exit 1.
Cause, measured: both occluders place their nearest foreground edge at 10.713 and
10.176 degrees off the gaze axis while the accepted core spans only +/-6.000
degrees at BOTH profiles, so the occluding edge never enters the measurement. The
padded raster holds both instances but the accepted core holds only foreground
(21:16,384 and 31:16,384), giving 0 raw and 0 core singly-visible reference
against a required 64/32 at small and 256/128 at full. This is profile
independent and would reproduce identically at full, so 2,516,582,400 primary
camera samples were not spent re-deriving it. The four phase planes are correct -
measured full-profile disparities 22.00000/22.25000/22.50000/22.75000 px at phases
0/.25/.50/.75 - and passed their smoke interior gates at 100% coverage. Repairing
the occluders requires moving a fixture edge inside +/-6 degrees of the gaze, a
geometry change this handoff does not delegate, so nothing was altered and no
alternative candidate was introduced. Under this decision's terms the failure is
preserved and stopped for Luiz/Chat: **FSG1 / Increment 1 is NOT closed, the
one-update instrument is NOT recorded as the FSG1 local RGB-D instrument, and
Increment 2 is NOT authorized.**

## D-FSG1h - correct the invalid FSG1g occluder fixture, instrument unchanged (2026-09-19)
FSG1g stopped at small smoke for an integrity failure: both prescribed finite-foreground edges were outside the accepted +/-6 deg core, so the intended half-occlusion reference was empty. This was a Chat fixture-design error, not a numerical result about the stereo instrument.

Preserve the frozen FSG1g instrument, gates, profile, spp, texture construction, depths and seed schedule. Correct only the foreground x extents so finite occluding edges lie inside the accepted core: occluder_left [-0.16,+0.10] m at z=-1.85 m; occluder_right [-0.10,+0.16] m at z=-1.95 m. Backgrounds remain -3.05 m and -3.15 m.

Before Blender, require the evaluator's own analytic ground-reference construction to prove nonempty substantial half-occlusion cores, boundary populations, and >=100 interior reference pixels for both instances at both profiles. Recreate the FSG1g geometry as a negative control and require it to fail.

Run only corrected small seed 101 and corrected full seeds 101 and 149. Do not tune, change the candidate, change thresholds, change spp, add support vetoes, fill holes, or rerender after a numerical miss. If every prescribed full gate passes, close FSG1 / Increment 1 and authorize but do not implement Increment 2. Otherwise preserve the failure and stop for Luiz/Chat.

Outcome 2026-09-19 (evidence: `docs/fsg1h-final-validation.md` Results and
`docs/log.md`). **FSG1H_FINAL_VALIDATION_PASS.** The corrected fixture exercised
the intended geometry - raw/boundary/interior populations matched the handoff
exactly, and the eroded-core difference was diagnosed before rendering as a
documentation arithmetic slip ((w-2r)*h instead of (w-2r)*(h-2r)), with the real
cores exceeding their minima by 21.7-23.6x. All four negatives failed as
designed, including the FSG1g off-core regression. Every prescribed full gate
passed on both fresh seeds with no numerical FAIL line: phase planes 99.765-99.965%
coverage at 0.0849-0.2255% median and 0.2844-0.9587% p95 across all four frozen
phases; occluder foregrounds at 100.000% coverage; occluded backgrounds at
93.167-95.190%, the tightest margin in the suite; boundary accuracy gates passed
with 3,973-4,044 accepted points at 0.2222-0.3302% median and 1.4432-2.0518% p95;
and **0 accepted points in all 11,592 singly-visible core pixels** across four
occluder-seed combinations, with 0 wrong-instance acceptances. Per this decision:
**FSG1 / Increment 1 is CLOSED, the one-update instrument
(FSG1-HDR-SGBM-one-original-update-original-validity-v1) is recorded as the FSG1
local RGB-D instrument, and Increment 2 - two overlapping patches in the fixed
head-centred map - is AUTHORIZED BUT NOT IMPLEMENTED.** Nothing was tuned, no
support veto added, no threshold changed, and no rerender followed the
diagnostic small-profile miss. The pass covers one local patch under controlled
opaque, diffuse, planar, calibrated conditions with oracle segmentation; it makes
no claim about arbitrary scenes, complete boundaries, thin structure, calibrated
uncertainty or multi-patch reconstruction.

## D-FSG2a - Minimal two-patch fusion (2026-09-19)
Test whether two prescribed, overlapping foveal RGB-D observations from the frozen FSG1 instrument can extend and fuse one segmented object surface in the fixed head frame without registration or hole filling. Use the prospectively fixed geometry, seed 211, fusion radius 12 mm, and gates in `docs/fsg2-increment2.md`. A full-profile pass authorizes Increment 3 (automatic single-object frontier growth) but does not implement it. A miss is preserved and returned to Luiz/Chat; Code may fix only demonstrated orchestration/implementation bugs, never the checks, fixture, thresholds, seed, instrument, or fusion parameters to obtain a pass.

Outcome 2026-09-19 (evidence: `docs/fsg2-increment2.md` Results and
`docs/log.md`). **FSG2_INCREMENT2_PASS** on the single prescribed full seed-211
acquisition, empty fails list. Every gate met: patch coverage 99.132% / 100.000%;
32,222 B points matched; 50.833% of B new; matched A/B distance median 1.907 mm
and p95 6.187 mm; fused point-to-true-plane median 3.548 mm and p95 9.740 mm;
fixed-grid coverage 90.225% with a 30.485 pp gain over patch A alone; idempotent
replay true. The fused map holds 91,941 surfels, 16,860 with two-look support,
containing only object ID 61 with background 62 absent. The small smoke missed
only the two plane-error gates (13.837 mm / 34.370 mm) - diagnostic under the
handoff - and both cleared at full. Nothing was tuned, rerendered or re-seeded,
and no code fix was required. Per this decision, **Increment 3 (automatic
single-object frontier growth) is AUTHORIZED BUT NOT IMPLEMENTED.** The pass
covers one finite planar tilted object under oracle segmentation, two fixations
3 deg apart, one seed, exact calibrated poses and a prospectively fixed 12 mm
Euclidean association rule; it makes no claim about folds, self-occlusion,
calibrated uncertainty, active frontier selection, multi-object switching or
uncontrolled scenes.

## D-FSG3a - Automatic single-object frontier growth (2026-09-19)
Starting from the frozen seed fixation, test whether the evolving persistent RGB-D map plus oracle segmentation can choose nearby horizontal 5-degree saccades, stop when the segmented surface frontier is resolved, and grow one visible object surface under the fixed FSG1 instrument and FSG2 head-frame fusion principle. Use seed 307, the frozen geometry/policy/fusion parameters and the prospective gates in `docs/fsg3-increment3.md`. A full pass closes Increment 3 and authorizes - but does not implement - the next experiment. It does not establish policy optimality because no competing gaze policy is evaluated here.

A miss is preserved and returned to Luiz/Chat. Code may fix only demonstrated implementation/orchestration defects that violate this written algorithm, never the checks, geometry, seed, policy parameters, SPP, instrument, fusion radius or numerical gates to obtain a pass.

Outcome 2026-09-19 (evidence: `docs/fsg3-increment3.md` Results and
`docs/log.md`). **FSG3_INCREMENT3_PASS** on the single prescribed full seed-307
active run, empty fails list. The POLICY chose the trajectory: 5 fixations at yaw
-7, -2, +3, +8, +13, every saccade exactly +5 deg, no repeat, terminating on
`no_frontier` - at the seed the object does not reach the left edge so only one
candidate exists, and at +13 it no longer reaches the right edge so none does.
The map's right extent finished at +14.632 deg against the fixture's analytic
+15.190, i.e. it stopped at the visible object boundary from segmentation and map
evidence alone, with the loop and policy verified to import no fixture geometry
and open no evaluation_only asset. Every gate met: per-patch oracle coverage
94.050-96.723%; overlaps 25,720-26,608 matched with medians 1.823-1.992 mm and
p95 5.455-6.336 mm, all idempotent; nonterminal new fractions 42.3-43.0% and the
terminal 16.949%; fixed-grid coverage 33.613% -> **100.000%** with gains
+20.987/+20.184/+19.974/+5.242 pp and no step losing coverage; final
point-to-plane median 4.219 mm and p95 13.587 mm; all 92,632 map points ID 71
with background 72 never present. The small smoke missed four gates
diagnostically and all four cleared at full; nothing was tuned, rerendered or
re-seeded and no code fix was required. Per this decision, **Increment 3 is
CLOSED and the next experiment is AUTHORIZED BUT NOT IMPLEMENTED.** The result is
feasibility, not optimality - no competing gaze policy was evaluated - on one
opaque diffuse planar tilted rectangle under oracle segmentation, horizontal
saccades only, fixed 2.10 m vergence, one seed and a prospectively fixed 12 mm
association rule. Folds, self-occlusion, multi-object switching, head motion,
vergence control, calibrated uncertainty and hidden-surface completeness remain
open.

## D-FSG4a - Compare active frontier growth with one fixed symmetric scan (2026-09-19)
Keep the closed FSG1 instrument, FSG3 frontier policy in substance, FSG3 multi-look head-frame fusion and all metric-geometry gates. On two new mirrored planar placements with distinct textures and fresh seeds 401/443, compare the active policy against the single frozen non-adaptive scan `0,-5,+5,-10,+10` at a five-fixation camera budget. Pair rendering noise by fixture/seed/yaw/eye. The primary number is truth-grid surface coverage versus budget and its fixed normalized AUC. A pass requires all four active runs to remain valid, all four scan maps to remain metrically valid, exact same-yaw pairing, active AUC wins in 4/4 pairs, mean AUC advantage >=0.10 and mean final-coverage advantage >=0.10. No alternative scan or threshold may be selected after results.

If the full comparison passes, close Increment 4 and record that active frontier feedback improves sampling efficiency over this fixed-scan control on the controlled mirrored planar family. Authorize, but do not implement, the next experiment. If it misses, preserve all pairs and stop for Luiz/Chat. Code may fix only demonstrated implementation/orchestration defects that violate this written experiment; never change the instrument, policy, scan, geometry, texture, seed, fusion radius, budget or gates to obtain a pass.

Outcome 2026-09-19 (evidence: `docs/fsg4-increment4.md` Results and
`docs/log.md`). **STOPPED at the small paired smoke on an integrity failure; the
four full paired trials and `fsg4_compare.py` were NOT run, so this decision's
comparison gates were never reached and no FSG4_INCREMENT4_PASS/FAIL status
exists.** `AssertionError: paired observation differs at shared yaw -10.0`,
`fsg4_pair.py` exit 1. Diagnosis: at every shared yaw the Cycles seeds are
identical and the oracle masks bit-exact; only RGB differs by one to two float32
ulp (max 5.96e-07). Rendering the identical command twice - same fixture, seed,
yaw and step - reproduces the same discrepancy as two renders at different steps,
with identical seeds in all three, so the paired-seed rule is confirmed
step-independent and the cause is non-associative GPU floating-point
accumulation, not policy or step leakage. The control's purpose is met in
substance: at the shared yaw every reconstruction statistic is bit-identical
between policies. I did not fix it - `fsg4_pair.py` faithfully implements the
written "exactly identical" requirement, so the issue is the specification's
bit-exactness assumption, not a delegated implementation defect, and relaxing it
would change gate C5 and blunt the `--negative pairing` control. Nothing was
altered: no change under `tools/`, and no scan, policy, geometry, texture, seed,
fusion radius, budget, threshold or gate touched. **Increment 4 remains OPEN and
no next experiment is authorized.** The decision for Luiz/Chat is whether
"exactly identical" stays bit-exact - requiring a deterministic rendering path -
or is restated as bit-exact seeds and oracle masks plus an explicit RGB tolerance
with gate C5 reworded. The four pairs and the AUC aggregation remain unrun and
unprejudiced.

## D-FSG4b - preserve exact FSG4 pairing by reusing the observation artifact (2026-09-19)
FSG4a stopped at the small paired-noise integrity gate and produced no full-profile comparison: two independent OptiX executions of the same seeded view are not bit-reproducible (seeds and oracle masks exact, scene-linear float32 RGB differing by one to two ulp, max 5.96e-7, reproduced by repeating the identical command). That is an execution-property mismatch, not a policy result.

Do NOT weaken Gate C5 and do NOT introduce an RGB tolerance. Instead make the paired condition true by construction: run the active policy first with no cache, index its completed acquisitions by yaw, then run the fixed scan, cloning the completed active acquisition at any shared yaw (rewriting only step-local metadata) and rendering scan-only yaws normally with the frozen yaw-keyed seed rule. After both runs, require exact equality of every saved array, exact seed equality, and a declared reuse flag on every scan shared-yaw record.

The scientific experiment is unchanged: same frontier policy, fixed scan 0,-5,+5,-10,+10, fixtures case_a/case_b, seeds 401/443, FSG1 instrument, FSG3 fusion with 12 mm association, five-fixation budget, AUC definition, geometry gates and pass thresholds. The budget remains logical camera samples consumed per policy - a reused shared view is still charged to the scan as one fixation - while new_primary_camera_samples records execution provenance only and never reduces the policy budget.

Code may fix only a demonstrated implementation/orchestration defect in this handoff, and may not change the policy, scan, geometry, texture, seed, stereo instrument, fusion radius, camera budget, metric, thresholds, exact-pairing requirement or pass rule. If the four-pair full comparison passes the unchanged FSG4a gates, close Increment 4 and record the limited claim that active frontier feedback improves surface acquisition efficiency over this one frozen nonadaptive scan on the controlled mirrored planar family. If it misses, preserve all four pairs and stop for Luiz/Chat. No next-increment implementation is delegated.

Outcome 2026-09-19 (evidence: `docs/fsg4b-pairing-reuse.md` Results and
`docs/log.md`). **FSG4_INCREMENT4_FAIL.** The pairing repair worked - 3 shared
yaws per pair, all arrays and seeds exact, all reused, active reuse count 0 and
active newly-rendered equal to active logical in all four pairs - and the full
four-pair comparison ran for the first time. The exact gate was preserved, not
relaxed: `np.array_equal` unchanged, the gate additionally requires a declared
reuse flag, and the repaired `--negative pairing` control still exits 1 on a
single mutated float. Gate C ALL PASS: AUC wins 4/4, mean AUC advantage 0.164873,
mean final-coverage advantage 0.165546, active logical samples <= scan in 4/4.
Gate A ALL PASS: plane medians 3.968-4.346 mm active and 3.813-4.201 mm scan, p95
12.258-14.144 mm, every map pure ID 81, every fusion idempotent. **Gate B fails
on `case_b` at both seeds, on the terminal patch only**: new fraction
0.03912/0.03970 against >=0.05 and terminal coverage gain 1.276/1.282 pp against
>=2 pp, because the policy is already at 98.72% after four looks and its fifth at
+20 catches only the sliver up to the object's right boundary at +21.329 deg.
`case_a` passes fully at both seeds. Per this decision the miss is preserved and
returned: **Increment 4 remains OPEN, nothing is adopted, and no next experiment
is authorized.** Nothing was tuned - no tolerance, rerender, alternate scan,
threshold, seed, geometry, texture, policy, fusion radius or AUC change, and no
code fix was required. A tension for Luiz/Chat to resolve: the same `case_b`
trajectory that violates the inherited FSG3 terminal-patch contract also produces
the largest efficiency advantage in the experiment (AUC gain 0.2296, final gain
0.2173, 100% coverage).

## D-FSG4c - Fresh validation of the efficiency question (2026-09-19)
FSG4c removes the FSG3 per-fixation novelty/new-fraction and minimum coverage-gain conditions from the FSG4 *validity* contract. Those quantities remain measured and reported. No numerical replacement threshold is introduced. All other scientific elements remain frozen: FSG1 instrument, FSG3/FSG4 frontier policy and parameters, fixed scan `0,-5,+5,-10,+10`, 12 mm fusion, exact shared-view artifact reuse, five-fixation logical camera budget, normalized AUC definition, map accuracy/purity gates, active final coverage >=90%, and aggregate comparison thresholds (4/4 AUC wins, mean AUC gain >=0.10, mean final-coverage gain >=0.10).

Why: once coverage before the terminal fixation is 98.72%, at most 1.28 pp remains, so a `>=2 pp` terminal-gain requirement is impossible even for a view that closes 100% of the residual surface. In an efficiency experiment a wasteful fixation should hurt the coverage-vs-budget curve and its AUC; it should not invalidate the trial through a second, per-fixation utility gate.

FSG4b observations are development/diagnostic data and are not reused. Validate on fresh opaque fixtures `case_c`, `case_d` and fresh Monte-Carlo seeds 503 and 557. Run small `case_c`/503 only as smoke. Then run all four full pairs exactly once and aggregate all four regardless of numerical exit-2 misses; stop early only for an integrity/provenance/runtime exception.

Overturned if: exact pairing/reuse/provenance fails, the frozen policy or scan changes, or the fresh full comparison misses the prospective FSG4c aggregate/map-quality gates. Never tune fixture, policy, scan, seed, SPP, fusion radius, AUC, or thresholds after seeing results. The formal FSG4b FAIL and all earlier records are preserved; this is a fresh validation, not a reinterpretation.

Outcome 2026-09-19 (evidence: `docs/fsg4c-increment4.md` Results and
`docs/log.md`). **FSG4C_INCREMENT4_PASS**, empty fails. All seven aggregate
conditions met: four valid active runs, four valid scan maps, exact reuse at
every shared yaw (12/12 rows arrays- and seeds-exact), active logical samples <=
scan in 4/4, active AUC wins **4/4**, mean AUC advantage **0.170182**, mean
final-coverage advantage **0.221831**. The policy found opposite directions on
the mirrored placements unaided - case_c 0,-5,-10,-15 and case_d
0,+5,+10,+15,+20, both `no_frontier` - and reached 100.000% final coverage in all
four against the scan's 73.3-82.3%. Map quality holds for both policies (plane
medians 4.308-4.520 mm, p95 13.590-14.808 mm, every map pure ID 81, every fusion
idempotent). Active received no cache, proven by newly-rendered equalling logical
samples in every pair. **Honest qualification: the contract correction was not
load-bearing** - the terminal new fractions (0.377/0.272) and gains (17.66/8.20
pp) would have satisfied the retired >=5% and >=2 pp rules anyway, so no run was
rescued by removing them; residual closure was 100.000% at the terminal fixation
in all four pairs. Nothing was tuned and no code fix was needed. Per this
decision: **Increment 4 is CLOSED and the next experiment is AUTHORIZED BUT NOT
IMPLEMENTED.** The claim is limited to frontier feedback improving
visible-surface acquisition efficiency over this ONE frozen nonadaptive scan on
this controlled fresh planar family - two opaque diffuse planar placements, two
MC seeds, oracle segmentation, exact poses, horizontal saccades, fixed 2.10 m
vergence - and is neither policy optimality nor a population estimate. The
formal FSG4b FAIL and all earlier records are preserved.
