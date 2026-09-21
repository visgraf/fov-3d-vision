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

## D-FSG5a - Curvature stress test with the existing active observer (2026-09-20)
Increment 4 closed the controlled planar efficiency question. Increment 5 changes **geometry, not intelligence**. Keep the closed FSG1 local RGB-D instrument, existing `tools/fsg4_policy.py` and its constants, existing `tools/fsg3_surface_map.py` with the fixed 12 mm Euclidean association and 12 mm spatial hash, oracle instance segmentation, exact calibrated head-frame poses, fixed 2.10 m vergence, 5-degree horizontal saccades, profile defaults, no ICP, no meshing and no hole filling. Replace the planar target by a finite convex cylindrical ribbon.

The question: can the already validated active loop grow a metrically correct curved visible surface without a new policy, registration step or surface model? The policy is deliberately NOT upgraded to a 3D frontier controller in this increment; that would confound curvature with a new controller.

Two mirrored opaque diffuse cylindrical ribbons (radius 0.75 m, height 0.34 m, centre z=-2.80 m, 75 deg arc, distinct textures) and fresh Monte-Carlo seeds 601 and 647 give four full trials, each judged independently and all four required to pass. Gates as written in `docs/fsg5-increment5.md`, including the curvature-specific rule that multi-look surfels (>=5,000 with support from >=2 fixations) must have absolute median signed radial error <=7.5 mm, recorded separately from unsigned point-to-surface error because averaging nearby samples on a curved surface can contract a map inward even when association distances are small. Per-fixation new fraction and coverage gain remain descriptive, not validity gates, following the closed FSG4c contract.

A full pass closes Increment 5 and authorizes - but does not implement - the next experiment. A miss is preserved and returned to Luiz/Chat. Code may fix only a demonstrated implementation/orchestration defect that violates the written algorithm; it may never change the stereo instrument, policy, fusion radius, geometry, texture, seeds, SPP, vergence, coverage radius or numerical gates to obtain a pass. No ICP, normals-based registration, meshing, hole filling, new frontier logic, competing policy, extra seed or rerender after a numerical miss.

Outcome 2026-09-20 (evidence: `docs/fsg5-increment5.md` Results and
`docs/log.md`). **FSG5_INCREMENT5_PASS**, trial_passes 4, empty fails; all four
full trials FSG5_CURVED_RUN_PASS with empty fail lists. The frozen FSG1
instrument, the unchanged `fsg4_policy` and the unchanged `fsg3_surface_map` with
its 12 mm Euclidean association grew a convex curved surface to ~100%
completeness at 3.362-3.654 mm median and 10.769-11.309 mm p95 point-to-surface
error, on both mirror orientations and both seeds, with no new policy,
registration step or surface model. The policy produced the mirrored trajectory
on the mirrored fixture unaided (curve_right -7,-2,+3,+8,+13; curve_left
+7,+2,-3,-8,-13), all terminating `no_frontier`. **The curvature-specific gate
passed with room to spare and in the safe direction**: signed radial median
+1.251 to +1.335 mm on 54,526-55,383 multi-look surfels against a +/-7.5 mm
limit - positive, i.e. slightly outward, so the anticipated inward contraction of
a curved surface under 12 mm Euclidean fusion did not occur; an independent check
of the exported clouds gives median radius 0.75075-0.75097 m against a true
0.750 m. Every map pure ID 81, every post-seed replay idempotent, largest
coverage decrease 0.005 pp. Descriptive and recorded rather than smoothed away:
on curve_left the fifth fixation added essentially nothing (new fraction 0.0007,
gain +0.014/-0.005 pp) because coverage was already 99.99% - valid under the
closed FSG4c contract. No code fix was required and nothing was tuned. Per this
decision: **Increment 5 is CLOSED and the next experiment is AUTHORIZED BUT NOT
IMPLEMENTED.** The claim is limited to two mirrored opaque diffuse cylindrical
ribbons of one fixed radius and arc, two MC seeds, oracle segmentation, exact
poses, horizontal saccades and fixed vergence - not general curvature, varying
radius, concave or saddle geometry, self-occlusion, folds, multi-object scenes,
head motion, vergence control or calibrated uncertainty. The policy remains a 2D
image-edge/map-yaw controller; a true 3D surface-frontier controller is now a
clean next question and was deliberately not built here.

## D-FSG6a - Replace the image-edge controller with a truth-free 3D surfel frontier (2026-09-20)
Increment 5 established that the closed FSG1 local RGB-D instrument and the existing 12 mm head-frame surfel fusion can grow a substantially curved convex surface without ICP, meshing or a surface model. Increment 6 changes **the frontier representation, not the measurement instrument or fusion**.

Keep the frozen FSG1 instrument `FSG1-HDR-SGBM-one-original-update-original-validity-v1` and the existing `tools/fsg3_surface_map.py` with its 12 mm Euclidean association and 12 mm spatial hash exactly unchanged. Replace the horizontal FSG4 image-edge/map-yaw controller by a truth-free controller whose candidate directions must be supported by boundary asymmetry in the persistent **3D surfel map**. Oracle segmentation remains available, but only as a current-view object-continuation veto: it may say that a surface frontier is actually a resolved object boundary; it may not create the frontier score or reveal fixture geometry. `fsg6_run.py` and `fsg6_frontier.py` must import no fixture geometry and open no `evaluation_only` asset.

The question: can a frontier extracted from the reconstructed 3D surface itself drive a two-dimensional gaze trajectory that grows a curved surface which a horizontal-only controller cannot cover? The frontier is extracted by downsampling the persistent surfels to 25 mm voxels, fitting a local covariance over 65 mm neighbourhoods, taking the smallest PCA eigenvector as the local normal, projecting the mean neighbour offset into the tangent plane, and calling the negative projected mean the missing surface direction. Candidate gazes are the eight neighbours of a 5-degree yaw/pitch lattice; each must stay inside the frozen limits, not revisit a fixation, be permitted by oracle segmentation on every nonzero movement component edge (a diagonal requires both), and be supported by at least eight 3D frontier surfels whose missing tangent directions agree with it. Selection maximizes the 12x12 degree foveal footprint area outside the robust yaw/pitch bounding box of the persistent map, with the 3D frontier score as tie-breaker.

Two fresh diagonal fixtures - finite cylindrical ribbons, radius 0.75 m, local centre z=-2.80 m, 110 deg arc, 0.20 m width, rigidly rolled in the head image plane by +35 deg (`diag_up_right`, seed gaze (-8,-8)) and +215 deg (`diag_down_left`, the exact image-plane mirror, seed gaze (+8,+8)) - and fresh Monte-Carlo seeds 701 and 743 give four full trials, each judged independently and all four required to pass. Gates as written in `docs/fsg6-increment6.md`, including the explicit 3D-gaze requirement that the visited pitch span be >=10 degrees, which a horizontal-only controller cannot satisfy, and the retained curvature-specific rule that multi-look surfels (>=5,000 with support from >=2 fixations) have absolute median signed radial error <=7.5 mm. Per-fixation novelty and coverage gain remain descriptive, not validity gates, following the closed FSG4c contract.

A full pass closes Increment 6 and authorizes - but does not implement - the next experiment. A miss is preserved and returned to Luiz/Chat. Code may fix only a demonstrated implementation/orchestration defect that violates the written algorithm; it may never change the stereo instrument, FSG3 fusion, frontier algorithm or constants, geometry, texture, seeds, SPP, vergence, coverage radius or numerical gates to obtain a pass. No ICP, meshing, hole filling, learned policy, self-occlusion extension or next-increment implementation.

Outcome 2026-09-20 (evidence: `docs/fsg6-increment6.md` Results and
`docs/log.md`). **FSG6_INCREMENT6_FAIL**, trial_passes 2/4. **The miss is
preserved; Increment 6 is NOT closed and the next experiment is NOT authorized.**

The frontier representation itself worked. On all four full trials the truth-free
3D surfel frontier drove a genuinely two-dimensional trajectory - **pitch span
15.0 degrees on every trial** against the >=10 degree gate - and grew a rolled
cylindrical ribbon to **~99.1% curved-surface completeness at 4.04-4.64 mm
median** and 12.78-14.45 mm p95, on both orientations and both seeds, with
nonterminal frontier support 21-93 surfels against a >=8 requirement, every map
pure instance 91, every replay idempotent, and signed radial median +1.42 to
+1.69 mm (outward, so no inward contraction, reproducing FSG5). The software
check confirms a five-look horizontal-only scan reaches only 0.412 ideal coverage
on this fixture, so the two-dimensional trajectory is doing real work.

`diag_down_left` passed on both seeds with empty fail lists, terminating
`no_frontier`. `diag_up_right` failed on both seeds with exactly two fails each:
`3D frontier policy did not terminate by resolving the frontier` and `fix_04
object measurement coverage` (0.8940 against >=0.90).

**Root cause, measured: the mirror pair is not a monocular mirror.** The two
fixtures are an exact 180-degree image-plane rotation as geometry - `up_right L`
and the rotated `down_left R` disagree on **0 of 409,600 pixels, IoU 1.000000**.
But a 180-degree roll maps (x,y,z) -> (-x,-y,z) and therefore **swaps the two eye
centres** at +/-0.0315 m along X, so the mirror of the left eye's view is the
*right* eye's view. The controller consults only the left-eye oracle mask, so the
"mirrored" fixtures differ by the full binocular parallax: **37.4 px (1.76 deg)
on a ribbon only 119 px (5.59 deg) wide**, 31% of its width; `up_right L` vs
rotated `down_left L` disagree on 16.43% of core pixels, IoU 0.732. The oracle
continuation veto, which thresholds the object fraction in a 10-row edge band at
0.15, converts that into a trajectory difference: the mirrored edge fraction runs
systematically 0.136-0.143 lower on `up_right` and at the third fixation crosses
the threshold (**0.0703 vs 0.2066**). The (+5,+5) diagonal is vetoed, the
controller is deflected onto a pure-yaw move, and both FAIL lines follow
mechanically - it still has eligible candidates when the 6-fixation budget ends,
and its fourth fixation lands half off the ribbon. `raw_support_L` is 100% true
in both bands, so the stereo instrument plays no part.

This is a fixture/rig design property, not an implementation defect: it
reproduced identically on both seeds with byte-identical oracle reference counts,
the oracle mask being ray-traced and seed-independent. Repairing it requires
changing the fixture design, the reference eye, or `edge_object_fraction_min` -
**a specification question this decision does not delegate to Code**, so nothing
was tuned and the miss stands for Luiz/Chat.

One code fix was required and made, the only one: `tools/fsg6_run.py` line 64
referenced an undefined name `z` in the loop's defensive revisit guard, so every
step after the seed raised `NameError` and the written 4-6 fixation algorithm
could not execute at all. Changed to `gaze`, the variable holding the gaze about
to be acquired - one token, no constant, threshold, gate or specification
touched. Nothing else was tuned: no frontier constant, lattice, instrument,
fusion radius, geometry, texture, seed, SPP, vergence, coverage radius or gate
changed, and no rerender after the numerical miss.

## D-FSG6b - Keep the FSG6 3D surfel frontier; make only the auxiliary continuation veto eye-symmetric (2026-09-20)
FSG6a remains a **formal FAIL** and its records, results and the accepted one-token `z -> gaze` implementation repair in `tools/fsg6_run.py` stay untouched. FSG6b is additive; it does not rewrite FSG6a.

FSG6a established that the truth-free 3D surfel frontier can drive genuinely two-dimensional gaze and reconstruct diagonal curved ribbons to about 99% completeness with millimetric geometry. Its formal miss was traced to the auxiliary continuation veto, which consulted only the rectified **left**-eye oracle mask. A 180-degree image-plane roll swaps the physical eye centres, so the nominal mirror pair was not a monocular mirror; binocular parallax changed the left-eye edge fraction enough to veto one diagonal move in exactly one fixture.

FSG6b changes **exactly one architectural element**: for each direction `d` the same edge-band object fraction is computed independently in both rectified eyes, and the continuation evidence becomes `f_cont(d) = max(f_L(d), f_R(d))`, permitted iff `f_cont(d) >= 0.15` using the **unchanged** FSG6a threshold. Either eye may supply evidence that the physical object continues. This rule is exactly invariant to `L <-> R`. Segmentation still cannot create a candidate: the persistent 3D surfel map alone creates and ranks frontier candidates, and the veto can only remove them.

Everything else is frozen and checked mechanically: the FSG1 instrument `FSG1-HDR-SGBM-one-original-update-original-validity-v1`; existing `tools/fsg3_surface_map.py` with 12 mm association/hash and idempotent replay; fixed head frame H and exact eye/head geometry; no ICP; fixed 2.10 m vergence; 256 spp full / 64 spp smoke; 25 mm frontier voxels, 65 mm neighbourhood, PCA tangent frontier, 0.18 asymmetry minimum, 0.12 m lookahead, 0.50 alignment cosine, minimum 8 agreeing frontier surfels; the eight-neighbour 5-degree yaw/pitch lattice; and every FSG6a measurement, overlap, map-quality, coverage, pitch-span and radial-bias gate. `check_fsg6b.py` compares `SURFACE_FRONTIER` and `TARGETS` for exact equality against `fsg6_public.py`, so any hidden threshold or gate drift fails before acquisition.

The scientific question: does the unchanged 3D surfel frontier close Increment 6 once its segmentation-only physical-boundary veto is invariant to swapping the two binocular eyes?

FSG6a's four full records are development evidence and are NOT reused as validation. Validation uses two fresh diagonal cylindrical ribbons that are deliberately **not** exact mirror copies - `fresh_up_right` (centre z -2.85 m, radius 0.78 m, theta -58 to +52 deg, height 0.24 m, roll +30 deg, seed gaze (-8,-7), texture tag 47) and `fresh_down_left` (centre z -2.70 m, radius 0.70 m, theta -50 to +60 deg, height 0.23 m, roll +220 deg, seed gaze (+8,+7), texture tag 53) - with fresh Monte-Carlo seeds **809** and **853**, giving four full trials judged independently and all four required to pass. Object instance is 101.

A full pass closes Increment 6 and authorizes - but does not implement - the next experiment. A miss is preserved and returned to Luiz/Chat. Code may fix only a demonstrated implementation/orchestration defect that prevents the written experiment from executing and does not alter the scientific specification; it may never change the 0.15 continuation threshold, any FSG6a frontier constant, the stereo instrument, FSG3 fusion radius or hash, the 5-degree lattice, geometry after acquisition starts, textures, seeds, SPP, vergence, truth coverage radius or any numerical gate to obtain a pass. No alternate fixture, extra seed, rerender after a numerical miss, ICP, meshing, hole filling, learned policy or next-increment implementation.

Outcome 2026-09-20 (evidence: `docs/fsg6b-increment6.md` Results and
`docs/log.md`). **FSG6B_INCREMENT6_FAIL**, trial_passes 2/4. **The miss is
preserved; Increment 6 is NOT closed and the next experiment is NOT authorized.**
FSG6a remains a formal FAIL with its records untouched and the `z -> gaze` repair
in place.

**The eye-symmetry repair works and is not what failed.** `check_fsg6b.py`
reports `passed=8 failed=0` with `eye_swap_invariant=true`, and the `monocular`
negative exits 1 proving the retired left-eye-only rule asymmetric. Contract
equality is exact: `SURFACE_FRONTIER` and `TARGETS` are identical to `fsg6_public`
with no differing keys, `edge_object_fraction_min` 0.15 in both. On real
acquisitions the rule fired: at fixation 0 of both `fresh_up_right` trials the
left edge measured f_L=0.0000, f_R=0.2414, so max(f_L,f_R) permitted a direction
the old rule would have vetoed. Honest qualification: this rescue occurred twice
across the four trials and no SELECTED move depended on it, so the repair
broadened the candidate set without changing a trajectory on this fixture family.
FSG6a's eye-asymmetry mode did not recur and its `fix_04` coverage miss is gone
(every patch 0.9215-0.9485 against >=0.90).

`fresh_down_left` passed on both seeds with empty fail lists, terminating
`no_frontier`. `fresh_up_right` failed on both seeds with **one fail line each** -
`3D frontier policy did not terminate by resolving the frontier` - while still
reaching 99.68/99.66% coverage at 3.37/3.35 mm median. All four trials held pitch
span 15.0 deg against the >=10 gate, frontier support 29-90 against >=8, every map
pure instance 101, every replay idempotent, and radial bias between -0.30 and
+0.99 mm.

**Root cause, measured: the conjunctive corner rule.** A diagonal move requires
BOTH corresponding edge bands to continue, but a narrow ribbon rolled +30 degrees
leaves the fovea through a CORNER. At the deflecting fixation, gaze (+2,+3) on
`fresh_up_right`: top band L=0.0000 R=0.0035 (veto), right band L=0.6176 R=0.6004
(permit), top-right corner L=0.0000 R=0.0900 (veto), but the **top half of the
right band is 0.7883/0.9258 object**. The object occupies rows 25..255 of 256 and
never reaches the top row, so the `top` veto is correct and both eyes agree - not
an eye-swap artifact. The surface nevertheless continues up-and-right out of the
corner. The (+5,+5) move is blocked, the controller takes the pure-yaw (+7,+3)
and spends an extra fixation recovering the diagonal, so it still has two
eligible candidates when the 6-fixation budget ends and terminates
`max_fixations`. `fresh_down_left` stops correctly because its remaining edges
are genuinely resolved in both eyes and its permitted neighbours are all visited.
The two fixtures diverging is the deliberately non-mirror design working.

Also recorded: the FSG6b construction estimate assumed a four-look diagonal whose
fourth step is exactly the (+5,+5) move the conjunctive rule forbids;
`ideal_angular_coverage` models the fovea as a plain 12x12 box with no veto, so
the fixture design check and the veto semantics disagree about reachability.

This is a **specification question, not an implementation defect**: the
conjunctive requirement is written into the handoff, inherited from FSG6a and
explicitly frozen for FSG6b. Changing it, the 0.15 threshold, or the 6-fixation
budget would alter the scientific specification, so nothing was tuned. **No code
fix was required or made in FSG6b.** Returned to Luiz/Chat.

## D-FSG6c - Preserve the FSG6 3D surfel frontier and the FSG6b binocular repair; replace only the diagonal component-conjunction veto with candidate-aligned forward-perimeter continuation (2026-09-20)
FSG6a and FSG6b remain **formal FAILS** and their records, results and artifacts stay untouched. The accepted one-token `z -> gaze` implementation repair remains in `tools/fsg6_run.py` (and is carried into the FSG6b/FSG6c runners). The FSG6b eye-symmetric binocular evidence `f(edge) = max(f_L(edge), f_R(edge))` is accepted and remains frozen. FSG6c is additive; it does not rewrite FSG6a or FSG6b.

FSG6a established that the persistent 3D surfel frontier can drive genuinely two-dimensional gaze, but exposed a left-eye-only continuation asymmetry: a 180-degree image-plane roll swaps the physical eye centres, so a nominal mirror pair was not a monocular mirror. FSG6b repaired that eye asymmetry and proved the repair by check and on real data, but fresh validation exposed a second, independent defect: a diagonal candidate required BOTH component edges to show continuation. A rolled ribbon can leave the current foveal core through the forward perimeter - for example high on the right edge - without ever touching the top edge. The retired `top AND right` rule therefore vetoed a geometrically valid up-right move and spent the six-fixation budget on a detour.

FSG6c changes **exactly one policy semantics**. Per-eye directional edge fractions are computed exactly as in FSG6b and remain combined symmetrically. For a candidate lattice direction `d=(dx,dy)`, the forward-compatible perimeter edges are named by its nonzero components (right -> {right}; up -> {top}; up-right -> {right,top}; down-left -> {left,bottom}). The candidate continuation evidence is `f_cont(d) = max(f(edge) for edge in compatible_edges(d))`, permitted iff `f_cont(d) >= 0.15` using the **unchanged** FSG6b threshold. Axis-aligned behaviour is therefore identical to FSG6b; only diagonal semantics change, from `all(...)` over the two component edges to `max(...)` over the direction-compatible edges. The persistent 3D surfel map still creates and ranks frontier candidates; segmentation cannot create or score a frontier and remains only a physical-boundary veto. The rule stays exactly invariant to `L <-> R`.

FSG6c also removes a design/runtime inconsistency this project found the hard way: FSG6b's fixture construction check used a bare angular box and therefore certified a four-look diagonal path that its own runtime veto could forbid. `fsg6c_scene.py` now carries an evaluator-only preflight that intersects the **continuous analytic cylinder** with the two frozen eye models, sends the raw oracle masks through the repository's actual rectification maps and core crop, computes the same calibration-derived support masks the runtime uses, and calls the exact `fsg6c_frontier.directional_continuation_evidence()` the host policy calls. It prescribes no trajectory; it only proves the fresh construction is reachable under the actual continuation semantics before any Blender acquisition. A load-bearing fresh control is frozen: on `corner_up_right` at gaze `(2,+3)` the intended `(+5,+5)` transition must have right-edge continuation above 0.15 while top-edge continuation stays below 0.15, so the candidate-aligned rule permits it and the retired conjunction rejects it; if that property drifts, checks fail before acquisition.

Everything else is frozen and checked mechanically: the FSG1 instrument; existing `tools/fsg3_surface_map.py` with 12 mm association/hash and idempotent replay; fixed head frame H and exact eye/head geometry; no ICP; fixed 2.10 m vergence; 256 spp full / 64 spp smoke; 25 mm frontier voxels, 65 mm neighbourhood, PCA tangent frontier, 0.18 asymmetry minimum, 0.12 m lookahead, 0.50 alignment cosine, minimum 8 agreeing frontier surfels; the eight-neighbour 5-degree lattice; the six-fixation budget; and every FSG6b measurement, overlap, map-quality, coverage, pitch-span and radial-bias gate. `check_fsg6c.py` requires exact equality of `SURFACE_FRONTIER` and `TARGETS` with `fsg6b_public.py`, so any hidden threshold or gate drift fails before acquisition.

The scientific question: does the unchanged truth-free 3D surfel frontier close Increment 6 when the segmentation-only physical-boundary veto is aligned with the proposed 2D candidate direction rather than decomposed into conjunctive axis tests?

FSG6a/FSG6b full records are development evidence and are NOT reused as validation. Validation uses two fresh diagonal cylindrical ribbons, deliberately not exact mirror copies - `corner_up_right` (centre z -2.90 m, radius 0.76 m, theta -60 to +54 deg, height 0.245 m, roll +33 deg, seed gaze (-8,-7), texture tag 61) and `corner_down_left` (centre z -2.75 m, radius 0.72 m, theta -52 to +62 deg, height 0.235 m, roll +216 deg, seed gaze (+8,+7), texture tag 67) - with fresh Monte-Carlo seeds **907** and **953**, giving four full trials judged independently and all four required to pass. Object instance is 111.

A full pass closes Increment 6 and authorizes - but does not implement - the next experiment. A miss is preserved and returned to Luiz/Chat. Code may fix only a demonstrated implementation/orchestration defect that prevents the written experiment from executing and does not alter the scientific specification; it may never change the 0.15 threshold, any FSG6b frontier constant or numerical gate, the stereo instrument, FSG3 fusion radius or hash, the 5-degree lattice, the six-fixation budget, the fresh geometry after acquisition starts, textures, seeds, SPP, vergence or truth coverage radius to obtain a pass. No alternate fixture, extra seed, rerender after a numerical miss, ICP, meshing, hole filling, learned policy or next-increment implementation.

Outcome 2026-09-20 (evidence: `docs/fsg6c-increment6.md` Results and
`docs/log.md`). **FSG6C_INCREMENT6_FAIL.** The diagnostic smoke raised a RUNTIME
EXCEPTION, which blocks the full schedule; **no full trial was run**. The miss is
preserved; Increment 6 is NOT closed and the next experiment is NOT authorized.
FSG6a and FSG6b remain formal FAILS with records untouched and the `z -> gaze`
repair in place in all three runners.

**Everything upstream of acquisition passed.** `[fsg6c-check] SUMMARY passed=10
failed=0`; all nine negatives exit 1, including `conjunction` and `monocular`;
all sixteen FSG1-FSG6b suites green; `SURFACE_FRONTIER` and `TARGETS` exactly
equal FSG6b with no differing keys. The runtime-semantic preflight verified the
load-bearing control against real rectified masks: on `corner_up_right` at gaze
(2,+3) the (+5,+5) transition measures right=0.6219 and top=0.0797, combined
0.6219 >= 0.15, permitted by FSG6c and rejected by the retired conjunction. The
FSG6b design/runtime inconsistency is genuinely fixed.

**But the policy walked off the fixture.** `corner_up_right`/907/small went
(-8,-7) -> (-3,-12) -> (-8,-17) with 7,005 then 1,486 then **0** object pixels in
core, against a ribbon spanning pitch [-10.188,+9.952], raising `ValueError:
active FSG6c fixation has too few object points`.

**Root cause, measured: `max()` lets one component license the other.** At the
seed gaze (-8,-7) the binocular edges are left=0.0766 (veto), right=0.4203
(permit), top=0.5156 (permit) and **bottom=0.0000 in BOTH eyes**. The down-right
direction (+1,-1) has compatible edges {right,bottom}, so
`f_cont = max(0.4203, 0.0000) = 0.4203 >= 0.15` and FSG6c permits it while the
retired conjunction rejects it. The bottom edge is exactly zero - a provably
resolved boundary - yet the move is allowed because `max()` substitutes the other
component's evidence. Through the analytic preflight this reproduces at BOTH
profiles and on BOTH fixtures (corner_down_left: top=0.0000, left=0.4609/0.4641,
allowed). The oracle mask is ray-traced and seed-independent, so all four full
trials would have begun from exactly this state; the failure is geometric and
deterministic, not a Monte-Carlo accident.

FSG6c is too permissive in precisely the dual way FSG6a/FSG6b were too strict.
The conjunction demanded continuation on EVERY component; `max()` demands it on
NONE in particular. Neither rule expresses "the surface leaves through the corner
region between these two edges".

**No code fix was made, and none was permitted.**
`directional_continuation_evidence()` implements this decision's written rule
exactly, and (+1,-1) legitimately yields `max(0.4203, 0.0000)`. Code and
specification agree, so this is not an implementation or orchestration defect;
any repair would change the continuation rule itself, which this decision
forbids. Nothing was tuned and nothing was rerun after the failure.

Recorded for the next handoff: the shipped over-permissiveness guard in
`fsg6c_frontier.self_test` resolves BOTH compatible edges and is correctly
vetoed; the failing case resolves only ONE (synthetic bottom=0.0000,
right=0.9062 -> combined 0.9062, allowed). A control with one compatible edge
exactly zero and the other strong would have failed before acquisition, and the
preflight never checked that off-object directions are correctly REFUSED - it
only validated the two intended traces and the critical up-right transition.

## D-FSG6d - Make the continuation veto local to the projected 3D frontier and the candidate's own forward image sector (2026-09-20)
FSG6a, FSG6b and FSG6c remain **formal FAILS** and their records, results and artifacts stay untouched. The accepted one-token `z -> gaze` implementation repair remains in place in all four runners. FSG6d is additive; it does not rewrite any earlier increment.

The three earlier attempts bracket the problem. FSG6a showed the 3D surfel frontier can drive genuinely two-dimensional gaze but used a left-eye-only veto that a 180-degree roll made asymmetric. FSG6b repaired eye symmetry with `max(f_L,f_R)` and exposed the diagonal component-conjunction defect: requiring BOTH component edges vetoed a valid up-right move on a ribbon that exits through a corner. FSG6c replaced `all()` with `max()` over the compatible edges and hit the exact dual defect: at the seed gaze the bottom edge was **0.0000 in both eyes** yet `max(right 0.4203, bottom 0.0000)` licensed a down-right step across a provably resolved boundary, and the controller walked off the fixture. Neither Boolean combination of two whole-edge-band statistics can express "the surface leaves through the corner region between these two edges".

FSG6d therefore changes **the spatial support of the continuation measurement, not its numerical threshold**. For each candidate direction the existing 3D frontier supplies the supporting surfels and their existing 3D look-ahead targets. For each rectified eye independently, FSG6d projects each supporting surfel and its look-ahead target into the current rectified/cropped foveal core using the repository calibration and rectification, extends that projected frontier ray to the core boundary, keeps only exits lying in the candidate's own forward image sector (+yaw right, +pitch up, with image v growing downward), rasterizes only the terminal corridor around those exits, and measures object fraction over calibration-valid support inside that corridor. Corridor longitudinal length and transverse half-width are both derived from the already-frozen `edge_band_fraction = 0.04`, so **FSG6d introduces no new numerical policy constant**. The two eyes are combined with the accepted FSG6b symmetry `f_cont = max(f_L, f_R)` and the candidate is permitted iff `f_cont >= 0.15`, the **unchanged** threshold.

A strong full right edge therefore cannot by itself justify a down-right move when the supporting 3D frontier exits elsewhere in the image, and a legitimate up-right frontier leaving through the high-right boundary does not need to touch the whole top edge. The persistent 3D map still creates and ranks the candidates; segmentation can only veto them. Exposing `target_xyz_h` from the already-computed look-ahead point is data plumbing for this veto, not a changed frontier calculation.

Everything else is frozen and checked mechanically: the FSG1 instrument; existing `tools/fsg3_surface_map.py` with 12 mm association/hash and idempotent replay; fixed head frame H and exact acquisition poses; no ICP; fixed 2.10 m vergence; 256 spp full / 64 spp smoke; the PCA/tangent-asymmetry frontier extraction constants; the frontier/candidate alignment threshold and minimum support of 8; the candidate ranking and sort key; the eight-neighbour 5-degree lattice; the six-fixation budget; and every measurement, overlap, map-accuracy, purity, idempotence, curvature-bias, coverage and pitch-span gate. `check_fsg6d.py` requires exact equality of `SURFACE_FRONTIER` and `TARGETS` with `fsg6c_public.py`.

The check suite also closes the gap I reported after FSG6c. `fsg6d_scene.self_test` now enumerates **every** neighbour at **every** construction state and requires that any direction the corridor permits lands on a next view carrying at least the already-frozen 100 oracle reference pixels **in each eye** - a control that would have caught FSG6c's walk-off before acquisition. `check_fsg6d.projection_control` independently verifies the rectified-core projection against OpenCV `undistortPoints`, and `historical_bracket_control` requires both historical defects to stay fixed simultaneously: the valid FSG6b-style corner continuation survives while FSG6c-style one-component licensing is rejected. Eleven deliberate negatives must exit 1, including `conjunction` (against reverting to FSG6b), `componentmax` (against reverting to FSG6c) and `full_edge` (against replacing the local corridor by a whole-edge statistic).

The scientific question: can a truth-free persistent 3D surfel frontier drive the next foveal fixation when the oracle segmentation veto is made local to the same projected frontier and the same candidate direction, rather than a Boolean combination of whole image-edge bands?

Earlier full records are development evidence and are NOT reused as validation. Validation uses two fresh, deliberately non-mirror rolled cylindrical ribbons - `corridor_up_right` (radius 0.74 m, centre z -2.86 m, arc -58 to +55 deg, height 0.252 m, roll +29 deg, seed gaze (-8,-7)) and `corridor_down_left` (radius 0.70 m, centre z -2.70 m, arc -50 to +63 deg, height 0.246 m, roll +211 deg, seed gaze (+8,+7)) - with fresh Monte-Carlo seeds **1009** and **1061**, giving four full trials judged independently and all four required to pass. Object instance is 121.

A full pass closes Increment 6 and authorizes - but does not implement - the next experiment. A miss is preserved and returned to Luiz/Chat. Code may fix only a demonstrated implementation/orchestration defect that prevents the written experiment from executing and does not alter the scientific specification; **if the code implements the written rule and the rule fails, that is a specification result to be preserved, not repaired.** Never change the 0.15 threshold, the 0.04 band fraction, any frontier constant, the candidate ranking, the FSG1 instrument, the FSG3 fusion radius or hash, the 5-degree lattice, the six-fixation budget, the fresh geometry after acquisition starts, textures, seeds, SPP, vergence, truth coverage radius or any numerical gate to obtain a pass. No alternate fixture, extra seed, rerender after a numerical miss, ICP, meshing, hole filling, learned policy, self-occlusion extension or next-increment implementation.

Outcome 2026-09-20 (evidence: `docs/fsg6d-increment6.md` Results and
`docs/log.md`). **FSG6D_INCREMENT6_FAIL**, trial_passes 0/4. Every trial fails on
**exactly one gate, the same one**: termination `max_fixations` instead of
`no_frontier`. The miss is preserved; Increment 6 is NOT closed and the next
experiment is NOT authorized. FSG6a, FSG6b and FSG6c remain formal FAILS with
records untouched and the `z -> gaze` repair in place in all four runners.

**The corridor rule works and is not what failed.** `[fsg6d-check] SUMMARY
passed=11 failed=0`; all eleven negatives exit 1 including `conjunction`,
`componentmax` and `full_edge`; all seventeen prior suites green;
`SURFACE_FRONTIER`/`TARGETS` exactly equal FSG6c. On real acquisitions the veto
did precisely what it was designed to do: at the third fixation of **every**
trial it permitted the diagonal the retired FSG6b conjunction would have vetoed
(up_right corridor 0.7031 with full-edge **top=0.0000**; down_left corridor
0.7787 with **bottom=0.0535**), and coverage jumped 74.47->96.97% and
75.52->98.44% at that step. The FSG6c defect did not recur: no trial ever stepped
off the ribbon, and the veto stayed active, rejecting 4 of 8 neighbours at the
final fixation of every trial. It is the first FSG6 continuation rule that is
simultaneously eye-symmetric, permissive to a genuine corner exit and
restrictive against one-component licensing.

Every other gate passed on every trial: pitch span 15.0 deg, yaw span 20.0, one
5-degree step per move, no repeats, frontier support 23-69, per-patch measurement
coverage 0.9114-0.9503, post-seed matched 11,387-20,222 with medians 1.97-3.20 mm
and p95 4.77-9.90 mm, all idempotent, gain 60.40-63.53 pp, maps pure instance 121
with 32,441-33,215 multi-look surfels, final coverage 98.676-99.042% at
3.463-3.938 mm median and 12.657-13.371 mm p95, radial bias +0.445 to +0.728 mm,
and exported-cloud median radius 0.74001-0.74005 m against a true 0.740 and
0.70095-0.70096 m against 0.700 - sub-millimetre, the best radial agreement of
any FSG6 increment.

**Root cause, measured: the 3D frontier never resolves on a thin ribbon.**
Frontier counts by step are [207,214,206,189,157,164] and [195,215,189,177,151,163]
while coverage goes 38.6% -> 99.0%; the population never decays. `extract_frontier`
marks a voxel as frontier from tangent asymmetry of its in-view neighbourhood,
and these ribbons are only ~6-7 degrees wide across a 12-degree fovea, so every
fixation sees long lateral ribbon boundaries that read as frontier however
complete the reconstruction is. Termination can therefore only arise from the
candidate set emptying. At the final fixation the surviving candidates are
**interior** lattice cells inside the already-swept region - (+7,+3) is the
centre of the square bounded by the visited (2,3),(7,8),(12,8),(12,3) - with small
predicted new area but genuine frontier support and a permitted corridor. Four
fixations already suffice numerically (96.97-98.57% coverage, 58.4-63.4 pp gain),
but the policy has no signal telling it to stop.

**This is a specification result, not an implementation defect, and no code fix
was made.** The code implements the written FSG6d rule exactly. What fails is the
interaction of the FROZEN frontier-extraction termination behaviour with the
FROZEN `no_frontier` gate and the FROZEN six-fixation budget, none of which this
decision permitted FSG6d to vary. Nothing was tuned and nothing rerun.

Recorded for the next handoff: **the open question is no longer the continuation
veto but termination** - how a frontier defined by local tangent asymmetry should
declare a thin ribbon finished. The veto itself should now be treated as settled.

## D-FSG6e - Give a raw frontier a persistent state; terminate on OPEN exhaustion rather than on raw-frontier disappearance (2026-09-20)
FSG6a, FSG6b, FSG6c and FSG6d remain **formal FAILS** and their records, results and artifacts stay untouched. The accepted one-token `z -> gaze` implementation repair remains in place in all five runners. **FSG6d's projected candidate-local binocular continuation corridor is now accepted and frozen**; FSG6e is additive and does not rewrite any earlier increment.

FSG6d settled the continuation-veto question. Its projected, candidate-local binocular corridor rescued the FSG6b corner-exit failure, avoided the FSG6c one-component walk-off, and all four full trials passed every measurement, geometry, purity, overlap, curvature and 2D-gaze gate, reaching 98.7-99.0% coverage at 3.46-3.94 mm median with sub-millimetre radial agreement. Its sole failure was **termination**: raw tangent-asymmetry frontier counts stayed at ~150-215 even after 99% reconstruction, because a ~6-7 degree ribbon inside a 12-degree fovea always presents long lateral boundaries. `no_frontier` was therefore unreachable and every trial exhausted the six-fixation budget with interior already-swept lattice cells still eligible.

FSG6e changes **the state of a raw frontier**, not the corridor and not any numerical gate. For every raw frontier surfel the unchanged extractor already produces the look-ahead target `t_i = x_i + 0.12 m * missing_i`. FSG6e classifies that hypothesis into exactly one of three states. **MAP_RESOLVED**: `t_i` lies within the frozen FSG3/FSG4 association radius of a surfel already in persistent memory, `min_s ||t_i - s|| < 0.012 m`, using the strict `<` test and the 0.012 m spatial-hash cell - exactly the frozen fusion semantics, introducing no new distance threshold. **BOUNDARY_RESOLVED**: `t_i` is not map-resolved, and in at least one completed fixation of the observer's binocular history the target projected into calibration-supported local patches in **both** rectified eyes with `max(f_L, f_R) < 0.15`, the unchanged continuation threshold; the patch radius derives from the already-frozen `edge_band_fraction = 0.04` exactly as the FSG6d corridor width does. **OPEN**: neither. Only OPEN frontiers contribute to the unchanged candidate support count and frontier score, with the frozen minimum of eight; the unchanged FSG6d corridor then performs the current-view veto and ranking is unchanged.

Two properties are deliberate. An eye swap cannot change the state, because the historical test is `max(f_L, f_R)` over both eyes. And a target that was *looked at* but whose stereo reconstruction is merely missing is **not** declared empty while oracle object segmentation still supports it - the stereo-hole guard. The intended meaning of termination becomes `no_frontier` = no candidate direction has enough OPEN frontier support after the settled FSG6d veto; it explicitly does **not** mean that raw tangent-asymmetry frontiers vanish.

Scope is deliberately narrow: a single convex visible object surface with oracle instance segmentation, where a supported binocular observation of the 3D target with no target-object evidence is a valid physical-boundary resolution. This is **not** a hidden-surface or occlusion state machine. A future self-occlusion case that projects the target onto target-object pixels stays OPEN rather than being prematurely completed; explicit OCCLUDED/UNSEEN reasoning is deferred.

Everything else is frozen and checked mechanically: the FSG1 instrument; `tools/fsg3_surface_map.py` with 12 mm association/hash and idempotent replay; fixed head frame H and exact poses; no ICP; vergence 2.10 m; 256 spp full / 64 spp smoke; the PCA/tangent-asymmetry raw extraction including the 0.12 m look-ahead; the alignment threshold and minimum support of 8; the candidate ranking and sort key; the FSG6d projected corridor; threshold 0.15 and band fraction 0.04; the eight-neighbour 5-degree lattice; the six-fixation budget; and every measurement, overlap, map-accuracy, purity, idempotence, curvature-bias, coverage and pitch-span gate. `check_fsg6e.py` requires exact equality of `SURFACE_FRONTIER` and `TARGETS` with `fsg6d_public.py` **and** text-identity of the settled FSG6d corridor/ranking helpers via `inspect.getsource`. Raw/map-resolved/boundary-resolved/open counts are descriptive diagnostics only; **FSG6e introduces no new numerical acceptance gate.**

The scientific question: can the observer decide that exploration is complete from its own persistent 3D memory and completed binocular observations, rather than requiring the raw geometric frontier population itself to disappear? Equivalently, can FSG6 distinguish a geometric one-sided surface boundary from an unresolved exploration frontier?

Earlier full records are development evidence and are NOT reused as validation. Validation uses two fresh, deliberately non-mirror rolled cylindrical ribbons - `closure_up_right` (radius 0.77 m, centre z -2.88 m, arc -57 to +57 deg, height 0.250 m, roll +31 deg, seed gaze (-8,-7)) and `closure_down_left` (radius 0.69 m, centre z -2.72 m, arc -51 to +64 deg, height 0.248 m, roll +214 deg, seed gaze (+8,+7)) - with fresh Monte-Carlo seeds **1123** and **1181**, giving four full trials judged independently and all four required to pass. Object instance is 131.

A full pass closes Increment 6 and authorizes - but does not implement - the next experiment. A miss is preserved and returned to Luiz/Chat. Code may fix only a demonstrated implementation/orchestration defect that prevents the written experiment from executing and does not alter the scientific specification; **if the code faithfully implements the written persistent-state rule and that rule fails, the specification result is preserved and I stop.** Never change the 12 mm association radius or hash, the 0.15 object threshold, the 0.04 patch/corridor scale, any frontier constant, the FSG6d corridor, the candidate ranking, the FSG1 instrument, FSG3 fusion, the 5-degree lattice, the six-fixation budget, the fresh geometry after acquisition starts, textures, seeds, SPP, vergence, truth coverage radius or any numerical gate to obtain a pass. Add no completeness-percentage stop, low-gain stop or budget extension. No alternate fixture, extra seed, rerender after a numerical miss, ICP, meshing, hole filling, learned policy, self-occlusion extension or next-increment implementation.

Outcome 2026-09-20 (evidence: `docs/fsg6e-increment6.md` Results and
`docs/log.md`). **FSG6E_INCREMENT6_FAIL**, trial_passes 2/4. The miss is
preserved; Increment 6 is NOT closed and the next experiment is NOT authorized.
FSG6a-FSG6d remain formal FAILS with records untouched and the `z -> gaze` repair
in place in all five runners.

**The central claim of this decision is nevertheless demonstrated on real
acquisitions.** Both `closure_down_left` trials terminated **`no_frontier` with
the raw tangent-asymmetry frontier still at 169-170 surfels** while OPEN had
collapsed to 6-9 and every unvisited direction fell below the frozen minimum of
eight (per-direction raw support 8-100, OPEN 0-7). The observer decided
exploration was complete from its own persistent 3D memory and completed
binocular observations, without the raw geometric frontier disappearing - exactly
what FSG6d could not do, and with no new numerical constant, no
completeness-percentage stop and no low-gain stop.

`[fsg6e-check] SUMMARY passed=13 failed=0`; all fourteen negatives exit 1
including `rawtermination`, `forget_history` and `stereo_hole`; all eighteen
prior suites green; `SURFACE_FRONTIER`/`TARGETS` exactly equal FSG6d, and
`inspect.getsource` confirms all eleven settled FSG6d corridor/extraction/ranking
helpers text-identical. The evaluator-only closed-loop preflight terminated both
fixtures in six fixations at ideal coverage 0.9996/1.0000, and its load-bearing
control - removing completed history from the same final state leaves a candidate
and does not stop - confirms the new state is not cosmetic.

`closure_down_left` passed on both seeds with empty fail lists (coverage
98.639/98.840%, median 4.506/4.507 mm, radial -2.811/-2.842 mm).
`closure_up_right` failed on both, for two different proximate reasons.
Seed 1123 produced **one** fail line, termination: OPEN collapsed 124 -> 16 and
candidates 5 -> 1, but `(12,-2)` survived with 96 raw aligned surfels of which 82
were BOUNDARY_RESOLVED and 3 MAP_RESOLVED, leaving **11 OPEN against a frozen
minimum of 8** - three more resolutions would have ended the run. Seed 1181
diverged at fixation 3: `(12,13)` was selected despite the weakest support of the
four (**8 OPEN, exactly the minimum**, from 25 raw) and the weakest corridor
(0.3230), because `predicted_new_angular_area` is the primary sort key and it
scored 134.26 against 103.65/73.04/15.09; `(12,13)` lies above the fixture's
+9.942 degree pitch bound, so fixations 4-5 fell off the ribbon (measurement
coverage 0.8268/0.6650, matched 3,879/404).

**The two seeds diverge on a knife edge**: recomputed at the identical state the
`(12,13)` corridor fraction is 0.1490 versus 0.3230, straddling the frozen 0.15
threshold, computed from only **six** projected frontier rays with the right eye
contributing exactly 0.0000 in both.

**This is a specification result, not an implementation defect, and no code fix
was made.** The code faithfully implements the written persistent-state rule and
the OPEN filter demonstrably works (170 -> 9 overall; 25 -> 8 and 29 -> 10 on the
decisive candidate). What fails is its interaction with three pieces this
decision froze: the FSG6d corridor evaluated on a six-ray sample, the
`predicted_new_angular_area` primary sort key that rewards the most extreme move,
and the minimum support of exactly 8. Nothing was tuned and nothing rerun.

Recorded for the next handoff: **the termination mechanism is sound; what is
unestablished is robustness.** The remaining fragility is not in the OPEN state
but in how thin the evidence behind a marginal candidate is allowed to be - a
six-ray corridor sample and a support count sitting exactly on the threshold.

## D-FSG6f - Aggregate the frozen persistent surfel states into candidate-level consensus: OPEN must strictly outnumber resolved (2026-09-20)
FSG6a, FSG6b, FSG6c, FSG6d and FSG6e remain **formal FAILS** and their records, results and artifacts stay untouched. The accepted one-token `z -> gaze` implementation repair remains in place in all six runners. FSG6f is additive and does not rewrite any earlier increment.

FSG6e established the three-way persistent surfel state we wanted, and proved it on real acquisitions: on both `closure_down_left` trials the raw tangent-asymmetry frontier stayed at 169-170 surfels while OPEN collapsed to 6-9 and `no_frontier` fired truth-free. Its two `closure_up_right` failures exposed the remaining abstraction gap. Candidate eligibility still meant only "at least eight OPEN surfels exist in this direction", even when the overwhelming majority of the aligned persistent evidence was already resolved. The two pathological survivors were **11 OPEN against 3 MAP + 82 BOUNDARY (11 of 96 raw)** and **8 OPEN against 1 MAP + 16 BOUNDARY (8 of 25 raw)**; the second, sitting exactly on the frozen minimum of 8, carried the trajectory off the ribbon.

FSG6f changes **exactly one scientific abstraction**: candidate-level aggregation of the already-frozen FSG6e states. For an aligned candidate let `N_OPEN`, `N_MAP` and `N_BOUNDARY` be the support counts and `N_RESOLVED = N_MAP + N_BOUNDARY`. The candidate is exploration-open only when

    N_OPEN > N_RESOLVED

and it must **independently** still satisfy the already-frozen `N_OPEN >= 8` support gate. **A tie is resolved, not open.** This is a state-consensus rule, not a fitted numerical threshold: no `0.5` or other majority constant is introduced, and the check suite asserts on the source that none appears. The hierarchy becomes raw 3D frontier -> persistent surfel state -> candidate state consensus -> projected-frontier binocular continuation corridor -> unchanged predicted-new-area / frontier-score ranking -> gaze.

Everything else is frozen and checked mechanically: the FSG6e MAP/BOUNDARY/OPEN classifier; the FSG6d projected-frontier corridor; the candidate ranking and sort key; the FSG1 instrument; FSG3/FSG4 12 mm association and hash; the raw frontier constants and 0.12 m look-ahead; the 0.15 continuation threshold; the 0.04 corridor/patch scale; the minimum OPEN support of 8; the 5-degree lattice; the six-fixation budget; SPP, vergence, truth coverage radius and every numerical acceptance gate. `check_fsg6f.py` requires exact equality of `SURFACE_FRONTIER` and `TARGETS` with `fsg6e_public.py`, `inspect.getsource` text-identity of the FSG6e state classifier and all settled FSG6d corridor/extraction helpers, and a literal match of the candidate sort key.

The rule is validated against the preserved FSG6e development record before any acquisition: all five productive `closure_up_right/1123` selected moves (45/46, 41/59, 31/50, 61/63, 60/83 OPEN-of-raw) are strict OPEN majorities and remain eligible, while both pathological survivors are rejected, and the `anyopen` negative detects any return to the retired any-OPEN rule. **Those FSG6e numbers are development controls only and are not counted as FSG6f validation.**

The scientific question: can persistent three-state 3D frontier memory be aggregated into candidate-level consensus strongly enough to reject mostly-resolved actions while preserving useful active exploration and truth-free `no_frontier` termination?

All FSG6a-e observations are development/regression evidence and are NOT reused as validation. Validation uses two fresh, deliberately non-mirror rolled cylindrical ribbons - `consensus_up_right` (radius 0.75 m, centre z -2.91 m, arc -59 to +58 deg, height 0.252 m, roll +28 deg, seed gaze (-8,-7)) and `consensus_down_left` (radius 0.71 m, centre z -2.69 m, arc -52 to +65 deg, height 0.250 m, roll +216 deg, seed gaze (+8,+7)) - with fresh Monte-Carlo seeds **1237** and **1291**, giving four full trials judged independently and all four required to pass. Object instance is 141. One acceptance gate is added, exactly as the handoff prescribes: every nonterminal selected candidate must have strict OPEN-majority state consensus.

A full pass closes Increment 6 and authorizes - but does not implement - the next experiment. A miss is preserved and returned to Luiz/Chat. Code may fix only a demonstrated implementation/orchestration defect that prevents the written experiment from executing and does not alter the scientific specification; **if the code faithfully implements strict OPEN-majority candidate consensus and that rule fails, the specification result is preserved and I stop.** Never change the 12 mm association or hash, the 0.15 threshold, the 0.04 scale, the 0.12 m look-ahead, any frontier constant, the FSG6e state classifier, the FSG6d corridor, the candidate ranking, the minimum OPEN support of 8, the FSG1 instrument, FSG3 fusion, the 5-degree lattice, the six-fixation budget, the geometry after acquisition starts, textures, seeds, SPP, vergence, coverage radius or any numerical gate to obtain a pass. Add no completeness-percentage stop, low-gain stop, confidence threshold or budget extension. No alternate fixture, extra seed, rerender after a numerical miss, ICP, meshing, hole filling, learned policy, self-occlusion extension or next-increment implementation.

Outcome 2026-09-20 (evidence: `docs/fsg6f-increment6.md` Results and
`docs/log.md`). **FSG6F_INCREMENT6_PASS**, trial_passes 4/4, every fail list
empty, aggregate exit 0. Per this decision, **Increment 6 is CLOSED and the next
experiment is AUTHORIZED BUT NOT IMPLEMENTED.** FSG6a-FSG6e remain formal FAILS
with records untouched and the `z -> gaze` repair in place in all six runners.

`[fsg6f-check] SUMMARY passed=14 failed=0`; all fifteen negatives exit 1
including `anyopen`; all nineteen prior suites green and every prior negative set
still fires. `SURFACE_FRONTIER`/`TARGETS` exactly equal FSG6e with no differing
keys; `inspect.getsource` confirms fourteen settled helpers text-identical,
including the whole FSG6e state classifier and every FSG6d corridor helper; the
candidate sort key is asserted by literal string match; the consensus source
contains no `0.5`.

All four trials passed. `consensus_up_right` on both seeds: six fixations,
`no_frontier`, coverage 99.402/99.439%, median 4.324/4.309 mm, radial
+0.314/+0.309 mm. `consensus_down_left` on both seeds: **five** fixations,
`no_frontier`, coverage 98.517/98.535%, median 4.382/4.386 mm, radial
-2.855/-2.885 mm. Pitch span 15.0 deg and yaw span 20.0 everywhere; per-patch
measurement coverage 0.9053-0.9547; post-seed matched 11,034-20,223 at 1.81-3.51
mm median and 5.74-10.54 mm p95, all idempotent; gain 60.91-62.21 pp; every map
pure instance 141 with 28,276-33,969 multi-look surfels; every nonterminal
selected candidate carrying both >=8 OPEN support and strict OPEN-majority
consensus.

**Candidate consensus is load-bearing on real acquisitions.** Twenty rejections
across the four trials, and **every one had corridor allowed=True and OPEN >= 8 -
every one would have been accepted by the retired FSG6e rule.** Three of four
trials terminate because of consensus (up_right/1291 rejected both remaining
candidates; down_left/1237 and /1291 each rejected their last one); only
up_right/1237 stopped on the FSG6e state alone. The FSG6e pathology is caught on
fresh data: `(-3,-7)` at OPEN 11 vs resolved 85 of 96 reproduces the
`closure_up_right/1123` survivor (11,3,82), and `(-7,-13)` at OPEN 8 - exactly the
frozen minimum - vs resolved 100 of 108 with the second-largest new-area on offer
reproduces the `closure_up_right/1181` off-ribbon move (8,1,16). Both rejected
before ranking; neither fixture ever left the ribbon. One termination was decided
by an **exact 40/40 tie** resolved rather than open, exercising the prospectively
specified tie rule on real data. Selected candidates were always large OPEN
majorities (38:0 to 76:7), so the rule never blocked a productive move.

**No code fix was required or made and no source file was modified**; the
increment changed documentation only. Nothing was tuned and nothing rerun. Cost
4,613,734,400 primary camera samples, below the 5,033,164,800 a six-fixation set
would have needed, because consensus ended two trials a fixation early.

Scope, narrowly: on fresh single convex visible curved surfaces with oracle
instance segmentation, persistent three-state 3D frontier memory can be
aggregated into candidate-level consensus strongly enough to reject
mostly-resolved actions while preserving useful active exploration and truth-free
`no_frontier` termination. This does NOT establish self-occlusion reasoning,
hidden-surface discovery, multiple objects, free head motion, learned gaze,
optimality or calibrated uncertainty. The route here is preserved in full as five
formal FAIL records - FSG6a's eye-asymmetric veto, FSG6b's conjunctive corner,
FSG6c's one-component licensing, FSG6d's non-terminating raw frontier and FSG6e's
minority-OPEN survivors - and each fixed exactly one abstraction without tuning a
constant.

## D-FSG7a - Prescribed lateral head translation to reveal genuinely self-occluded surface (2026-09-20)
Increment 6 is **closed** at FSG6f. FSG7a opens Increment 7 as a **new prospective experiment, not a repair of FSG6f**. All FSG6a-FSG6e FAIL records and the FSG6f PASS stand unchanged, as does the accepted `z -> gaze` implementation repair; no prior decision block is edited.

**The physics, stated first because it is the whole reason this increment exists. True self-occlusion cannot be revealed by eye rotation at fixed centres.** With the eye centres held in one place, changing fixation changes which rays are sampled at high resolution but does not change the line-of-sight visibility of any world point: a point hidden behind a fold stays hidden no matter where the eyes look. Every increment through FSG6f rotated the eyes about fixed centres, so none of them could have discovered hidden surface even in principle. Repository decision D3 anticipated this and set head motion aside as a separate question. FSG7a therefore changes **exactly one physical assumption**: the binocular rig may **translate laterally** while its orientation stays fixed.

Two consequences are deliberate and are checked. First, **H0 - the initial head frame - remains the persistent map frame.** Stereo is reconstructed by the unchanged FSG1 instrument in the local acquisition frame Ht and transported exactly into H0 by `x_H0 = x_Ht + t_H0` before fusion; the runner performs that transport and the check suite asserts the call is present. Second, **the rendered world does not move with the head** - moving the scene with the observer would cancel the parallax and reveal nothing, so it is an explicit negative control.

**FSG7a does not implement an active motion policy.** The two head positions and two gazes are prescribed constants in the public schedule. The observer does not choose where to move. Selecting head motion is the next question, and a PASS here does not touch it.

The research question: can the frozen FSG1 local stereo instrument, followed by exact-pose transport into H0 and the frozen 12 mm FSG3/FSG4 fusion rule, reconstruct a surface continuation that is binocularly self-occluded at H0 and becomes visible only after a prescribed lateral head translation?

Frozen: the FSG1 instrument `FSG1-HDR-SGBM-one-original-update-original-validity-v1`; FSG3/FSG4 fusion at 12 mm association radius and 12 mm hash cell; IPD, profile, SPP and the 2.10 m prescribed vergence; oracle instance segmentation as object identity only; no ICP, mesh reconstruction, hole filling or registration optimization. The head-origin keyword FSG7a uses already exists in the frozen `fsg_geometry.make_calibration` and is already consumed by the frozen render path, so no instrument change was needed to move the head.

Fixtures are two fresh connected folded ribbons sharing one rendered instance ID 151 - `fold_right` (front panel at z = -2.50 m, 0.36 m wide by 0.30 m high, with a 0.65 m deep return wing folding backward from its right edge) and `fold_left` (the mirrored fold) - with evaluator-only part labels distinguishing front from return. Each trial has exactly two binocular acquisitions: step 0 at H0 with gaze (0,0) seeding the front, and step 1 after +0.45 m (`fold_right`) or -0.45 m (`fold_left`) lateral translation with gaze -5.5/+5.5 degrees yaw, revealing the return wing. Fresh seeds 1409 and 1453 give four full trials.

A full trial passes only if every gate in `docs/fsg7a-increment7.md` passes: per-patch object measurement coverage >=90%; reveal patch >=5,000 fixed-H0 overlap matches with overlap median <=10 mm and P95 <=25 mm; idempotent reveal replay; final map containing only instance 151; >=5,000 final surfels with support >=2; final folded-surface median <=10 mm and P95 <=30 mm; seed front-wing coverage >=80% and seed return-wing coverage <=5%; final return-wing coverage >=80% with gain >=75 percentage points; final whole-object coverage >=90%; and evaluator direct visibility confirming fixed-head return visibility <=2% with moved-head binocular visibility >=95%. **FSG7a passes only if all 4/4 fresh full trials pass.**

A PASS establishes the measurement and mapping substrate for active hidden-surface discovery and nothing more: exact known head translation can reveal a genuinely self-occluded continuation, and the existing local stereo/fusion stack can place the newly visible measurements coherently into persistent H0 memory without ICP. It does **not** establish active head-motion selection, occlusion classification by the controller, learned gaze, multiple objects or free six-degree-of-freedom motion. A miss is preserved and returned to Luiz/Chat.

Code may fix only a demonstrable implementation/orchestration defect, after diagnosis, outside the checks, reported precisely. Never change the 0.45 m translation, the prescribed gazes, geometry, texture, seeds, SPP, the 2.10 m vergence, the stereo instrument, the 12 mm fusion rule, the coverage radius or any gate to obtain a pass. Do not rerender a numerical miss. Add no ICP, registration optimization, motion policy or extra views.

Outcome 2026-09-20 (evidence: `docs/fsg7a-increment7.md` Results and
`docs/log.md`). **FSG7A_HEAD_MOTION_FEASIBILITY_FAIL**, trial_passes 0/4. Every
trial failed on **exactly one gate, the same one in all four**: `final map median
folded-surface error`, 12.62-12.98 mm against a <=10 mm limit. The miss is
preserved; **FSG7a feasibility is NOT closed** and active head-motion selection
remains not implemented.

**The head-motion mechanism worked on every trial.** Direct evaluator visibility
gave return **0.0000/0.0000** in both eyes at H0 and **1.0000/1.0000** after the
prescribed translation on both fixtures; reconstructed return-wing coverage went
**4.73-4.97% -> 87.49-96.20%** (gain 82.75-91.36 pp); and the newly visible
measurements landed in persistent H0 memory at **2.545-2.830 mm median overlap**
with the seed map (P95 7.037-7.741 mm), every replay idempotent, with no ICP or
registration optimization. Frame transport measured exact to 1.49e-08. All other
gates passed on all four trials: patch coverage 0.9208-0.9358, reveal matches
14,923-19,058, overlap medians and P95s inside limits, instance purity 151,
6,789-9,672 surfels at support >=2, surface P95 21.1-21.8 mm, whole-object
coverage 0.9193-0.9755. `[fsg7a-check] passed=7 failed=0`, all six negatives exit
1, all twenty prior suites green including FSG6f.

**Root cause, measured: a front-panel depth bias inherited from the frozen
instrument, not a head-motion or transport failure.** Split by nearest panel, the
**return wing is accurate at 1.600-2.334 mm median** while the **front panel
carries a uniform -13.7 mm z offset** and holds 87-89% of the surfels, so it sets
the median. At Z = 2.50 m with baseline 0.0630 m and f = 1217.8 px, +13.74 mm
implies a disparity bias of **-0.1687 px**, within 7% of the **-0.1579 px SGBM
bias FSG1 measured and recorded** in its step diagnostic. The fixture sits
**0.40 m beyond the prescribed 2.10 m vergence** - further than any previous FSG
target - so the same fixed sub-pixel bias yields a larger metric offset. The
return wing escapes it geometrically: its normal is +/-x, so a depth offset slides
points along it rather than off it. A single global +13.74 mm z correction,
computed as a diagnostic only and applied to no tool, gives 3.663-3.776 mm median
and 10.808-11.333 mm P95, far inside the gates.

**This is a measurement/specification result, not an implementation defect. No
code fix was made and no source file was modified.** The code faithfully
implements the written experiment; correcting the bias would require changing the
frozen FSG1 instrument or the 2.10 m vergence, both of which this decision
forbids. Nothing was tuned and nothing rerendered.

Recorded for the next handoff: the substrate claim this increment set out to test
is supported everywhere except the inherited depth bias - exact known head
translation does reveal genuinely self-occluded surface and the existing
stereo/fusion stack does place it coherently in H0 without ICP. What stands
between that and a PASS is the FSG1 sub-pixel bias at a working distance beyond
its prescribed vergence, which is a question about the instrument or the fixture
distance, not about head motion.

## D-SCENE1A - Stage II opens: seeded multi-object active reconstruction with a scene scheduler (2026-09-20)
FSG6f / Increment 6 is **CLOSED/PASS** and is the frozen per-object active controller. FSG7a is preserved as an exploratory moving-head feasibility **FAIL** and is **deferred - the moving-head branch is not continued here**. Every earlier FSG record stands unedited, as does the accepted `z -> gaze` implementation repair; no prior decision block is modified.

**Stage II returns to the project's base assumptions: fixed head, static scene.** Scene-1a is the first Stage II experiment and asks one question: can the fixed-head, static-scene observer maintain several persistent object models, allocate attention among them using their own unresolved state, return to objects when useful, and stop only when every object is independently complete?

**Scene-1a imports the existing FSG6f controller; it does not copy or modify it.** The frontier extraction, the persistent OPEN/MAP_RESOLVED/BOUNDARY_RESOLVED surfel state, the candidate consensus, the projected binocular continuation corridor, the ranking and sort key, the 5-degree lattice and the per-object six-fixation budget are all reused by import. Verified before acquisition: `scene1a_policy.py` imports `fsg6f_frontier` and calls `object_policy.choose_next(...)` at a single site, and contains no copy of `extract_frontier`, `classify_frontier_state`, `candidate_state_consensus`, the corridor helpers, `_new_box_area` or the candidate sort. Also frozen: the FSG1 instrument `FSG1-HDR-SGBM-one-original-update-original-validity-v1`; FSG3 12 mm association and hash; fixed head and static scene; prescribed vergence 2.10 m; oracle instance segmentation as object identity only; no ICP, meshing, hole filling or learned policy.

**The one new abstraction is a scene scheduler.** Three known objects carry instance IDs 201, 202 and 203, each with one prescribed seed fixation. Once all three seeds exist, every object asks the frozen FSG6f controller for its next action; FSG6f either reports `no_frontier` or returns its already-defined selected candidate with `predicted_new_angular_area_deg2`, `frontier_score` and a next yaw/pitch. The scheduler chooses **lexicographically: largest predicted new angular area, then largest frontier score, then smaller instance ID purely as a deterministic final tie-break.** No weight, learned utility or fitted scene-level constant is introduced. Scene completion is exactly `scene_complete <=> every object independently reports no_frontier`.

**Opportunistic perception.** A physical fixation has one nominal attention target, but the stereo observation is processed for all known object IDs: any non-target object contributing at least 100 valid stereo points is fused into its own persistent map, and the completed binocular observation enters every object's history so later boundary resolution can profit from looks taken while attention was elsewhere. Physical gaze is **globally no-revisit**, and the global fixation history is supplied to each object's frozen FSG6f controller.

Two fresh non-mirror scenes are used - `triad_a` (left-upper plane, centre-lower convex ribbon, right-upper convex ribbon) and `triad_b` (right-upper plane, left-upper convex ribbon, centre-lower convex ribbon) - with fresh Monte-Carlo seeds **1601** and **1667**, giving four full trials judged independently. The objects are angularly disjoint: **object-object occlusion is not part of Scene-1a.** All geometry lies inside the frozen FSG6f yaw/pitch domain. Each prescribed seed is analytically partial (about 29-53% ideal 12-degree box coverage) with at least one neighbouring 5-degree gaze that improves it; those are design checks, not results.

Per-object gates: at least one autonomous post-seed target fixation; targeted patch object-measurement fraction >=90%; targeted post-seed overlap >=5,000 matched with median <=10 mm and P95 <=25 mm; idempotent replay for every fused patch; final map containing only the object's own instance ID; >=5,000 multi-look surfels; final analytic surface median <=10 mm and P95 <=30 mm; final truth coverage >=90%; final coverage gain over the object's seed-state map >=25 percentage points. Scene-level gates: the first three fixations are exactly the prescribed seeds; all later gaze selection is autonomous; every object receives autonomous post-seed attention; at least two post-seed attention switches; no physical fixation repeats; no object exceeds the frozen six-target budget; total scene budget <=18 physical fixations; final termination `scene_complete`; every final object policy state `no_frontier`. **Scene-1a passes only if all four fresh full trials pass.** Poor opportunistic visibility is descriptive, not a per-patch gate - only nominal target patches carry the inherited FSG measurement and overlap gates.

Scene-1a does **not** address object discovery, object-object occlusion, semantics, moving objects or head motion; those are separate scene-stage questions once the scheduling/memory substrate works.

Code may fix only a demonstrable implementation/runtime defect (undefined name, wrong path, schema mismatch), diagnosed first and repaired minimally. Never change the fixtures, object geometry, instance IDs, textures or fresh seeds; the three prescribed seed fixations; the fixed-head/static-scene assumptions; the 2.10 m vergence; the FSG1 instrument; the FSG3 12 mm fusion or hash; any FSG6f code, constant, frontier state, consensus, corridor, ranking or lattice; the per-object six-look or global 18-look budget; the scheduler ordering; the global no-revisit rule; the opportunistic all-known-object fusion and history; or any prospective gate. Add no object discovery, semantics, object-object occlusion logic, head motion, ICP, meshing, filling, learned policy, extra views, alternate seeds or rerenders after a numerical miss. **A faithfully implemented rule that fails is a scientific/specification result: preserve it and stop for Luiz/Chat.**

Outcome 2026-09-20 (evidence: `docs/scene1a-stage2.md` Results and
`docs/log.md`). **SCENE1A_STAGEII_FAIL**, trial_passes 0/4. The miss is
preserved; **Scene-1a is NOT closed** and no next Stage-II experiment is
authorized. FSG6f remains CLOSED/PASS and unmodified; FSG7a remains a preserved,
deferred FAIL.

`[scene1a-check] SUMMARY passed=8 failed=0`; all seven negatives exit 1; all
twenty-one prior suites green including FSG6f (14) and FSG7a (7) with their full
negative sets. The applied commit added exactly ten files, all additions, and an
explicit diff over every FSG1-FSG7a source is empty.

**The scheduler mechanics are correct and the failure is in the rule itself.** In
every trial the first three fixations were exactly the prescribed seeds, all
later selection was autonomous, no physical fixation repeated, no object exceeded
six targets, totals stayed under 18, each per-object map was pure in its own ID,
every fused patch replayed idempotently, targeted overlap medians ran 2.01-5.11
mm with P95 5.43-11.33 mm, and per-object surface accuracy passed everywhere
(median 4.368-5.201 mm, P95 13.153-18.249 mm across twelve object-instances).
**The lexicographic ordering was obeyed at all 39 autonomous decisions with zero
violations.**

**Root cause, measured: a starvation fixed point in the primary key.** Ranking by
largest `predicted_new_angular_area_deg2` is not stable, because an object that
is not selected does not acquire, so its map does not change, so its bid does not
change. On `triad_a` object 203's proposal is frozen at **area 105.48 / score
18.12 for all ten decisions**, permanently below the 122-140 deg^2 the other two
keep offering; it receives **zero autonomous post-seed attention** and ends at
coverage 0.4726 -> 0.4726, gain +0.0000, support histogram {1: 23197} - **not one
multi-look surfel**. Decisively, **203 carried the HIGHEST frontier score of the
three at every decision** (18.12 vs 12.86 and 19.28->6.74): it would have won on
the second key, but the first key never ties so the second is never consulted.
`triad_b` redistributes the same dynamic - 202 frozen at 110.93 for seven
consecutive decisions, 203 frozen at 119.99 then dropping to 104.40 and never
selected again, with one decision separated by 0.01 deg^2. All four trials ended
`object_budget_exhausted`, never `scene_complete`; only 2 of 12 object-instances
reached `no_frontier`; no object reached the 90% coverage gate (best 0.7919).

Opportunistic processing fired but rarely and is reported as such: 22-26
non-target patches processed per trial, of which only 1-2 cleared the
100-valid-point threshold and fused. On deliberately angularly disjoint base
scenes a 12-degree fovea rarely holds two objects, so the mechanism is exercised
but contributes little - a property of the separated base case, not evidence
against the mechanism.

**No code fix was required or made and no source file was modified.** A
faithfully implemented rule that fails is a scientific/specification result under
this decision, preserved rather than repaired. Nothing was tuned and nothing
rerendered.

Recorded for the next handoff: the memory and identity substrate works - three
persistent object models maintained simultaneously, pure per-object identity,
idempotent fusion, autonomous attention switching 3-5 times per trial, per-object
accuracy inside the gates, and the frozen FSG6f controller driven unmodified by
import. **What is unresolved is attention allocation.** Any successor rule has to
break the fixed point in which an unselected object's bid cannot improve; the
diagnostic to keep is that the starved object was the one with the highest
frontier score at every decision.

## D-SCENE1B - Fairness before utility: least-served-first scene scheduling (2026-09-20)
FSG6f / Increment 6 is **CLOSED/PASS** and remains the frozen per-object controller. FSG7a is a **preserved, deferred moving-head FAIL** and is not reopened. **Scene-1a remains a formal FAIL in the record and is not edited**; its multi-object memory, identity and fusion substrate worked, but its unconstrained area-first scheduler admitted a starvation fixed point - a live object could stay unvisited because its bid did not change while other objects kept winning the primary key. On `triad_a` object 203 was frozen at area 105.48 / score 18.12 for all ten decisions, took zero autonomous looks and ended with not one multi-look surfel, while carrying the highest frontier score of the three at every decision.

**Scene-1b changes exactly one abstraction: the scene scheduler.** For each live object `i` let `n_i` be the number of autonomous post-seed target fixations already allocated to it. Compute `n_min = min_i n_i` over **live objects only**. Only objects with `n_i == n_min` are eligible for the next scene action. Within that fairness class the Scene-1a utility ordering is retained **exactly**: largest FSG6f `predicted_new_angular_area_deg2`, then largest FSG6f `frontier_score`, then smaller instance ID as a deterministic final tie-break. A completed object (`no_frontier`) leaves the live set and does not constrain the service count of the remaining objects. **No fitted weight, learned utility, confidence threshold, age bonus, starvation timeout, weighted sum or round-robin hard-coding is introduced** - fairness is a structural eligibility constraint and the old utility is preserved as the within-class ranking.

**Scene-1b does not repair or alter the object controller.** It imports the existing FSG6f controller unchanged; verified before acquisition that `scene1b_policy.py` imports `fsg6f_frontier` and calls `object_policy.choose_next(...)` at a single site, defining none of FSG6f's frontier extraction, persistent state classifier, candidate consensus, projected corridor, `_new_box_area` or candidate ranking. Also frozen: the FSG1 instrument; FSG3 12 mm association and hash; fixed head, static scene, 2.10 m vergence; oracle instance segmentation; the six-target-per-object and 18-look global budgets; opportunistic all-known-object processing from every physical fixation; global physical no-revisit; and scene completion only when every object independently reports `no_frontier`. No ICP, meshing, hole filling, object discovery, learned policy, semantics, head motion or object-object occlusion logic.

**Scene-1b also uses fresh, deliberately easier base fixtures so this experiment isolates scheduling from Scene-1a's harder geometry** - `fair_triad_c` (upper-left plane, lower-centre convex ribbon, upper-right convex ribbon) and `fair_triad_d` (lower-centre plane, upper-left convex ribbon, upper-right convex ribbon), with all front surfaces near the validated 2.10 m vergence regime and objects compact and angularly disjoint. Fresh Monte-Carlo seeds **1723** and **1789**. Each object has one prescribed partial seed. Evaluator-only geometry carries a three-look 5-degree-lattice **design witness** from each seed covering at least 98% of the analytic object under ideal 12-degree boxes using only three of the six available looks; **the witness is not exposed to the prediction loop, is not a prescribed path and is not a policy prediction** - it is a prospective scene-design reachability check only, and the check suite asserts the prediction side contains no witness reference.

Per-object gates, unchanged from Scene-1a plus one addition: at least one autonomous post-seed target fixation; targeted patch object-measurement fraction >=90%; targeted post-seed overlap >=5,000 matched with median <=10 mm and P95 <=25 mm; idempotent replay for every fused patch; final map containing only the object's own instance ID; >=5,000 multi-look surfels; final analytic surface median <=10 mm and P95 <=30 mm; final truth coverage >=90%; final coverage gain over the object's seed-state map >=25 percentage points; **and final per-object policy state `no_frontier`**. Scene-level: the first three fixations are exactly the prescribed seeds; all later selection autonomous; **every scheduler decision obeys least-service eligibility before the frozen area/score/ID ordering**; every object receives autonomous post-seed attention; at least two post-seed attention switches; no physical fixation repeats; no object over six targets; total <=18; final termination `scene_complete`. **Scene-1b passes only if all four fresh full trials pass and the aggregate returns `SCENE1B_STAGEII_PASS`.** Poor opportunistic visibility remains descriptive, not a per-patch gate.

Code may fix only a demonstrable implementation/runtime defect, diagnosed first and repaired minimally. Never change the fixtures, object geometry, types, IDs, textures or fresh seeds; the three prescribed seed fixations; the fixed-head/static-scene assumptions; the 2.10 m vergence; the FSG1 instrument; the FSG3 12 mm fusion or hash; any FSG6f code, constant, frontier state, consensus, corridor, ranking or lattice; the six-look or 18-look budgets; the least-served-first eligibility rule; the within-class area/score/ID ordering; global no-revisit; the opportunistic rule; or any prospective gate. Add no age bonuses, starvation timers, weighted sums, round-robin hard-coding, completeness-percentage stops, low-gain stops, object discovery, semantics, occlusion logic, head motion, ICP, meshing, filling, learned policy, extra views, alternate seeds or rerenders after a numerical miss. **A faithfully implemented rule that fails is a scientific/specification result: preserve it and stop for Luiz/Chat.**

Outcome 2026-09-20 (evidence: `docs/scene1b-stage2.md` Results and
`docs/log.md`). **SCENE1B_STAGEII_FAIL**, trial_passes 0/4. The miss is
preserved; **Scene-1b is NOT closed** and no next Stage-II experiment is
authorized. FSG6f remains CLOSED/PASS and unmodified; FSG7a remains a preserved,
deferred FAIL; **Scene-1a remains a formal FAIL and was not edited**.

**The abstraction under test worked.** `[scene1b-check] passed=9 failed=0`; all
eight negatives exit 1 including `areaonly`; all twenty-two prior suites green.
**Fair scheduler audit: 64 autonomous decisions across four trials, 64
rule-compliant, 0 violations** - in every decision the selected object was inside
the least-served live class and ranked first within it by area, then frontier
score, then instance ID. **38 of 64 decisions had a fairness class strictly
smaller than the live set, and in 31 of 64 fairness rejected a strictly
higher-area proposal**, so the rule is decisively load-bearing rather than
decorative. Service counts finished **perfectly equal at {201:5, 202:5, 203:5} in
all four trials** with 13-14 attention switches. **Scene-1a's starvation fixed
point does not occur anywhere in Scene-1b.**

Reconstruction improved sharply. **Every per-object surface, purity, multi-look
and idempotence gate passed on all twelve object-instances**: median 3.834-5.339
mm, P95 15.519-16.900 mm, all maps pure in their own ID, 12,681-20,406 multi-look
surfels, every fused patch idempotent, gains +0.3594 to +0.5451. **Three
object-instances reached exactly 1.0000 coverage** and ten of twelve passed the
90% gate. `fair_triad_c/1789` came within **two** fail lines of passing.

**Why it still failed - arithmetic, and structural rather than a defect.** Three
objects x six per-object looks = 18 = the global scene cap. Under
least-served-first the objects advance in lockstep, so by the time one could
complete, all three have consumed nearly the same number of looks and there is no
slack to redistribute. Every trial ended at exactly 18 fixations with each object
having spent its full allowance, and `scene_complete` requires all three to reach
`no_frontier` within six looks each; only **5 of 12 object-instances** did.
Scene-1a failed the opposite way - it stopped early with budget unspent and
objects starved.

Opportunistic non-target fused updates were **0 in all four full trials**,
against 1-2 per trial in Scene-1a. Reported honestly: the `fair_triad` objects
are more widely separated and fair round-robin makes consecutive fixations jump
between distant objects, so nothing cleared the 100-valid-point threshold. The
mechanism is exercised and inert here, not broken.

**No code fix was required or made and no source file was modified.** A
faithfully implemented rule that fails is a scientific/specification result,
preserved rather than repaired. Nothing was tuned and nothing rerendered.

Recorded for the next handoff: **fairness is settled; budget sufficiency is
not.** Least-served-first removes starvation while preserving the frozen utility
ordering and introducing no weight, timer or learned term. What remains is the
relationship between the per-object budget, the scene budget and the number of
objects - with three objects at six looks each and an 18-look cap, perfectly fair
service exhausts the global budget exactly when the per-object budgets are
exhausted, leaving no slack for an object that needs one more look. A successor
should address that relationship, not the ordering rule.

## D-SCENE1C - Certify the actors before the ensemble: composition of active object reconstructions (2026-09-20)
FSG6f is **CLOSED/PASS** and remains the frozen object controller. FSG7a is a **preserved, deferred moving-head FAIL**. **Scene-1a and Scene-1b remain preserved formal FAILs; they are not edited or relabelled.** Scene-1a established the multi-object memory/identity substrate but exposed starvation under unconstrained area-first scheduling. **Scene-1b nevertheless settled the scheduler abstraction** - least autonomous post-seed service first, then the unchanged area / frontier-score / instance-ID ordering - with a 64/64 compliant audit and starvation eliminated; what it could not separate was budget sufficiency from component solvability, because its three objects did not all reach `no_frontier` inside six looks.

**Scene-1c introduces no new runtime perception or scheduling mechanism.** `scene1c_policy.py` imports the frozen Scene-1b policy layer rather than reproducing it, and Scene-1b in turn imports FSG6f; verified before acquisition that `scene1c_policy.py` imports `scene1b_policy as frozen_scene_scheduler`, makes **no direct FSG6f import**, and aliases rather than reimplements every scheduler symbol (`remap_instance`, `remap_observation`, `proposal_rank_key`, `select_proposal`, `propose_for_object`, `choose_scene_action`, `split_visible_object_masks`, `is_global_repeat`). Everything else is frozen: the FSG1 instrument; FSG3 12 mm association/hash; all FSG6f frontier extraction, persistent state, consensus, corridor, ranking and 5-degree lattice; the Scene-1b least-service eligibility and within-class ordering; six target looks per object; 18 physical fixations per scene; fixed head, static scene, 2.10 m vergence; oracle instance segmentation; opportunistic all-known-object processing; global no-revisit; scene completion only when every object independently reports `no_frontier`; and every Scene-1b numerical gate. Measured equality against Scene-1b before acquisition: `PER_OBJECT_MAX_FIXATIONS` 6, `MAX_SCENE_FIXATIONS` 18, `FUSION` {0.012, 0.012}, `TARGETS` identical with no differing keys, vergence 2.10, object IDs (201,202,203), instrument ID identical.

**The new element is an experimental protocol, not a policy: certify the actors before the ensemble.** For every `(fixture, seed, object)` triple a full-profile component control is run *before* any ensemble acquisition. Each control renders the **complete three-object fixture** with exactly the same renderer, geometry, textures, seed and prescribed seed gaze the ensemble will use; reconstructs only the nominated object; lets the unchanged FSG6f controller choose that object's later gazes; allows at most the unchanged six target looks including the seed; sees no evaluator geometry or truth during prediction; and is judged afterwards by exactly the Scene-1b per-object gates, and must terminate `no_frontier`. Both runners invoke the same `tools/scene1c_render_fix.py`, verified by inspection. There are 2 fixtures x 2 seeds x 3 objects = **twelve prospectively fixed full component controls.**

**The authorization rule, stated before acquisition: full ensemble acquisition is FORBIDDEN unless all twelve component controls certify.** If the twelve-control aggregate does not return exactly `SCENE1C_COMPONENT_CERTIFICATION_PASS` with 12/12, Scene-1c stops with `SCENE1C_COMPONENT_CERTIFICATION_FAIL`, every control is preserved, and **no ensemble full acquisition is run**. A failed actor is not replaced, resized, reseeded or tuned. The certification result is an experimental authorization condition only and is **not supplied to the scene policy as a runtime input**.

Fresh scenes `cert_triad_e` and `cert_triad_f`, each three compact convex cylindrical ribbons with IDs 201/202/203 in angularly disjoint regions, deliberately in the already successful FSG6f qualitative family with front surfaces near the validated 2.10 m distance. Fresh Monte-Carlo seeds **1847** and **1901**. Each object has one prescribed partial seed; evaluator-only geometry also carries a three-look 5-degree-lattice box-coverage witness reaching at least 98% ideal angular coverage using three of six looks. **The witness is a prospective geometry sanity check only - neither a policy prediction nor the certification**; the actual certification is the rendered FSG6f control.

Component gates per control: >=1 autonomous post-seed target fixation; targeted patch object-measurement fraction >=90%; targeted post-seed overlap >=5,000 matched with median <=10 mm and P95 <=25 mm; idempotent replay for every patch; final map containing only the nominated object's ID; >=5,000 multi-look surfels; final analytic surface median <=10 mm and P95 <=30 mm; final truth coverage >=90%; final coverage gain over the seed-state map >=25 pp; no repeated physical fixation; <=6 total target looks including the seed; and final FSG6f state and termination both `no_frontier`. Ensemble gates are unchanged from Scene-1b, plus every final object policy state `no_frontier` and final termination `scene_complete`; all four fresh full ensemble trials must pass.

Three outcomes are fixed prospectively: (1) any component control fails -> `SCENE1C_COMPONENT_CERTIFICATION_FAIL`, preserve, do not run the ensemble, stop; (2) all components certify but any ensemble trial fails -> `SCENE1C_STAGEII_FAIL`, which is evidence that individually solvable active object processes did not compose under the frozen scene substrate; (3) only if all twelve controls and all four ensembles pass may the aggregate report `SCENE1C_STAGEII_PASS` and Scene-1c close.

A composition diagnostic is required but is explicitly **not** a gate: for each `(fixture, seed, object)` compare the certified control's target-gaze sequence with that object's target subsequence in the ensemble, reporting common prefix and first divergence. Interleaved observations enter all object histories by design and can legitimately alter later FSG6f state; the diagnostic separates simple temporal interleaving from a genuinely scene-induced interaction, and must be explained only from recorded state.

Code may fix only a demonstrable implementation/runtime defect, diagnosed first and repaired minimally. Never change either fixture, any object geometry, ID or texture, seeds 1847/1901, the prescribed ensemble or component seeds, the fixed-head/static-scene assumptions, the 2.10 m vergence, the FSG1 instrument, the FSG3 12 mm fusion or hash, any FSG6f code/constant/state/consensus/corridor/ranking/lattice, any Scene-1b scheduler code or its ordering, the six-look or 18-look budgets, global no-revisit, opportunistic all-object processing, or any component or ensemble gate. Add no age bonuses, timers, weighted sums, completeness or low-gain stops, object discovery, semantics, occlusion logic, head motion, ICP, meshing, filling, learned policy, extra views, alternate seeds, actor substitution or rerenders after a numerical miss. **A faithfully implemented rule that fails is a scientific/specification result: preserve it and stop for Luiz/Chat.**

Outcome 2026-09-20 (evidence: `docs/scene1c-stage2.md` Results and
`docs/log.md`). **SCENE1C_COMPONENT_CERTIFICATION_FAIL**, control_passes 1/12.
**Per the authorization rule recorded above, the ensemble stage was NOT run** -
no ensemble smoke, no full ensemble trials, no ensemble aggregate, no composition
diagnostic. All twelve controls are preserved; Scene-1c is not closed. FSG6f
remains CLOSED/PASS and unmodified; FSG7a, Scene-1a and Scene-1b remain preserved
formal FAILs, unedited and unrelabelled.

`[scene1c-check] passed=10 failed=0`; all ten negatives exit 1 including
`incompletecert`, `schedulercopy` and `budgetbump`; all twenty-three prior suites
green with every prior negative set still firing. `git diff 3f4b490` over every
FSG1-FSG7a, `scene1a_*` and `scene1b_*` source is empty, and all five required
verifications passed - delegation to `scene1b_policy` with no direct FSG6f
import, `scene1b_policy` unchanged and still importing `fsg6f_frontier`, both
runners invoking the same `scene1c_render_fix.py`, no truth/witness reference in
either prediction runner, and budgets/fusion/targets identical to Scene-1b.

**Only `cert_triad_e/1847/obj203` certified** - 4 looks, `no_frontier`, coverage
0.6153 -> 1.0000, median 5.169 mm, 12,935 multi-look surfels, zero fails.
Everything structural passed in all twelve: pure per-object maps, idempotent
replay, no repeated fixation, no control over six looks, surface medians
5.169-6.616 mm and P95 16.252-18.092 mm inside the gates.

**Three failure modes, separated cleanly by the protocol.** (1) Object 203 on
e/1901, f/1847 and f/1901 took exactly one autonomous look and stopped
`no_frontier` with **gain +0.0000** and 4,185-4,472 multi-look surfels: against
the recorded bounds those runs moved toward the near edge the seed already covers
- (+6,+3) and (+5,+9) - while the certifying control moved into the unexplored
far tail, (+16,+13) then (+21,+13),(+21,+8). The e/1847 vs e/1901 pair is
decisive in the record: **identical fixture and prescribed seed gaze (+11,+8),
different Monte-Carlo seed, opposite first autonomous decision, opposite
outcome**, with the renderer seed the only recorded difference. (2) Five controls
hit `max_object_fixations` still reporting `continue`, three of them after
already reaching 1.0000/1.0000/0.9999 coverage. (3) Per-look measurement coverage
fell to 0.8669-0.8994 in eleven of twelve controls.

**No code fix was required or made and no source file was modified.** No actor
was replaced, resized, reseeded or tuned; no look added; no gate relaxed; FSG6f
untouched; nothing rerendered.

Recorded for the next handoff: **the certification protocol worked as designed
and was worth running.** It detected before any ensemble acquisition that eleven
of twelve actors are not solvable inside the unchanged six-look budget in the
exact complete-scene rendering context - including a mode Scene-1b could not have
isolated, where the frozen controller declares `no_frontier` after one
unproductive look with zero gain. **The composition question is not reached**,
because its premise does not hold on these fixtures. What now needs understanding
is the frozen FSG6f controller's post-seed behaviour on this fixture family: why
its first autonomous choice is seed-sensitive at object 203's seed, and why five
controls exhaust six looks without resolving the frontier despite reaching ~1.0
coverage. That is an object-controller question, not a scheduler or composition
question.

## D-REALITY1 - Reality Check 1: is the frozen mechanism already good enough on a less calibration-like scene? (2026-09-21)
FSG6f remains **CLOSED/PASS** and is the frozen object policy. FSG7a, Scene-1a, Scene-1b and Scene-1c remain preserved records and are **not edited**. After the failed Stage-II Scene-1a/1b/1c sequence the immediate question is no longer whether another scheduler can be invented; Scene-1c's certification showed eleven of twelve actors were not solvable inside six looks, so the open question moved onto the object controller itself. Reality Check 1 asks the pragmatic version of that: **does the frozen FSG6f mechanism produce a recognisable, metrically sane active reconstruction of one moderately irregular, mixed-texture target in a small cluttered static scene?**

**This is an observational practical test, not another prospective metric benchmark.** Recorded before acquisition:

- **Fixed head and static scene are retained.** No head motion; the FSG7a moving-head branch stays deferred.
- **The frozen FSG1 stereo instrument, FSG3 12 mm fusion and FSG6f object policy are retained**, imported rather than copied. Verified before acquisition: `reality1_run.py` imports `fsg6f_frontier as policy` and calls `policy.choose_next(...)`; it does **not** import `reality1_scene`, opens no `evaluation_only` asset, and defines none of FSG6f's frontier extraction, state classifier, consensus, corridor or ranking. `FUSION`, `MAX_FIXATIONS` (6) and `INSTRUMENT_ID` are measurably equal to `fsg6f_public`.
- **The only experimental change is the less calibration-like scene and texture.** The target is a shallow hanging cloth/poster-like surface about 0.90 m x 0.64 m at the validated ~2.1 m range, depth varying non-periodically by about 8 cm, represented by 120 rendered triangles rather than a plane or constant-radius cylinder. Its texture is deliberately **mixed rather than uniformly rich** - a broad low-contrast region, a modest printed band/emblem, subtle fabric variation and a small repetitive weave region - and the surrounding scene adds a table, wall and two unrelated side props. The target is not deliberately occluded; the scene stays opaque and diffuse, because Reality Check 1 changes as little as possible at once. Specularity, strong shadows, thin structure and adversarial materials are later reality checks if this one is promising.
- **Seeds 2111 and 2179 and the prescribed seed gaze (-6,-4) are fixed before any data exists.** Both runs hand control entirely to the unchanged FSG6f policy after that seed, for at most six physical fixations.
- **There is intentionally NO numerical quality PASS threshold.** No coverage, error, overlap, measurement-fraction or termination gate decides the outcome. Those are reported descriptively only.

**The only automated FAIL condition is structural integrity**: prediction never imports or opens evaluator truth; the map contains only the target instance 141; every fused patch replays idempotently; no physical fixation repeats; FSG6f is imported rather than copied; and the six-look budget and 12 mm fusion rule are unchanged. The per-run evaluator reports `REALITY1_OBSERVATION_COMPLETE` and the two-run aggregate reports `REALITY1_COMPLETE` when those hold, or `REALITY1_INTEGRITY_FAIL` otherwise.

**Numerical quality may be poor and that does not authorize tuning or rerendering.** Poor coverage, poor error, low measurement fraction, odd termination or seed sensitivity are precisely what this check exists to expose. Nothing about the scene, texture, seed, budget, policy, vergence, fusion or any numerical constant may be changed in response to the smoke or to either full run, and there is no rerender after a numerical miss and no alternate seed. A demonstrable implementation defect may be repaired minimally after diagnosis; scientific or numerical behaviour may not.

**After the two full runs, stop and return the report to Luiz/Chat.** They decide whether the behaviour is good enough to justify the next practical step. The visual reading of the RGB sequence, growth image and PLY is part of that report but is explicitly not upgraded into a formal PASS criterion.

Outcome 2026-09-21 (evidence: `docs/reality-check-1.md` Results and
`docs/log.md`). **REALITY1_COMPLETE** - both full records have structural
integrity; `integrity_fails` is empty in both per-run evaluations and in the
aggregate, and no FAIL line was produced anywhere. Per the rule recorded above
this is an **observation, not a PASS or a FAIL**: nothing here closes or reopens
anything. FSG6f remains CLOSED/PASS and unmodified; FSG7a, Scene-1a, Scene-1b
and Scene-1c remain preserved records, unedited and unrelabelled. No prior
decision is edited.

`[reality1-check] passed=6 failed=0`; all six negatives exit 1 for their own
stated reasons; all twenty-four prior suites green. `[reality1-scene] PASS`
confirms the fixture is what was promised - depth range 0.08711 m, 120
triangles, low-contrast panel std 0.010764 against feature-region std 0.11710.
Both prediction manifests carry the same `public_spec_sha256`
baa71ce4b0ae8e36bc0ccf80addad1c0e0e02ec76d7bc8369c37e4258c528f22, and the
independently re-verified structural conditions hold on both: truth never
opened, fixed head, static scene, map instance ids exactly {141}, every fused
patch idempotent, 6 of 6 gazes unique, policy and instrument the frozen ones,
budget 6 and fusion {0.012, 0.012} unchanged.

Measured, each seed acquired once at `full` (1,258,291,200 primary camera
samples each). Seed **2111**: 6 looks, `max_fixations`, coverage 0.2603 ->
**0.5345**, surface median **6.188 mm** / P95 19.812 mm, measurement fraction
min 0.8516, worst overlap median 3.025 mm, 21,927 multi-look surfels. Seed
**2179**: 6 looks, `max_fixations`, coverage 0.2604 -> **0.7329**, median
**5.720 mm** / P95 18.106 mm, measurement fraction min 0.8400, worst overlap
median 2.897 mm, 27,660 multi-look surfels.

Descriptive and deliberately ungated: **neither seed terminated `no_frontier`**;
**the two seeds diverge completely after the prescribed seed fixation** - first
autonomous moves (1,-1) versus (1,+1) from an identical start, never
reconverging, ending 19.8 coverage points apart with nothing differing but the
Monte-Carlo render seed; seed 2179's fifth look returned a new-point fraction of
0.001 and zero coverage gain; measurement fraction stayed at 0.84-0.88 rather
than the calibration-like values. The surface medians nonetheless sit inside the
4.3-6.6 mm band every earlier FSG6/Scene increment produced. Visually the map is
**recognisable as the hanging cloth, coherent rather than fragmented, at the
right depth (central 98% of reconstructed depths 2.083-2.167 m against a true
span of 2.083-2.166 m), with no gross wrong-depth region**; its visible
deficiency is incompleteness, not misplacement. That reading is reported, not
promoted to a criterion.

Three code fixes, all demonstrable implementation defects diagnosed before being
changed, none touching scientific or numerical behaviour: the check module's
missing `sys.path` entry, which had been making all six negatives crash-pass
rather than control; `render_seed` overflowing Blender's signed-32-bit Cycles
seed for **every** gaze under schedule seed 2179 (2,179,000,420 minimum against
a 2,147,483,647 limit), fixed by folding into int32 range, which is the identity
over the whole of seed 2111's domain and leaves the already-acquired 2111 record
and this spec's digest unchanged; and the range/collision check that would have
caught it before acquisition, verified fail-capable. The crashed attempt is
preserved at `previews/reality1/full-seed2179-crashed-int32seed/`. No scene,
texture, seed, budget, policy, vergence, fusion or numerical constant was
changed; nothing was rerendered after a numerical result; no alternate seed was
used.

What would overturn or extend this: it is an observation on **one** fixture
family with oracle segmentation, a fixed head and a static scene, so it does not
generalise to specular, shadowed, thin or adversarial material, to occlusion, to
object discovery, or to more than six looks. The two open behaviours it
documents - termination on budget rather than on frontier exhaustion, and a
trajectory sensitive to the render seed alone - are the same two Scene-1c
surfaced, now isolated on a single object, which is evidence that they belong to
the frozen FSG6f controller rather than to any scheduler. **Luiz/Chat decide
whether this is good enough and what the next practical step is.**

## D-REALITY2 - Reality Check 2: let the observer finish (2026-09-21)

Reality Check 1 is **preserved exactly as acquired and is not edited, relabelled
or rerun**; its `REALITY1_COMPLETE` observation stands, as do FSG6f
(CLOSED/PASS), FSG7a, Scene-1a, Scene-1b and Scene-1c. No prior decision is
edited by this block.

Reality Check 1 ended both full records on the **inherited six-fixation
experimental limit while frozen FSG6f still said `continue`** - `max_fixations`
on both seeds, with a live `next_gaze_deg` still on the table. Reality Check 2
asks the literal follow-up: **if those exact saved states are not interrupted at
six looks, does the unchanged observer continue to useful new surface and
eventually stop by its own `no_frontier` rule?**

**One scientific change: the six-look interruption is removed. Nothing else in
perception changes.** Recorded before acquisition:

- **The two saved Reality Check 1 full records are the parent states** -
  `previews/reality1/full-seed2111` and `previews/reality1/full-seed2179`, seeds
  **2111** and **2179**, each already holding exactly six looks, termination
  `max_fixations`, `truth_opened` false, fixed head and static scene true, and a
  final policy decision with `stop: false` and a recorded `next_gaze_deg`
  ((14,6) for 2111, (14,1) for 2179). Audited before anything was run: 32 of 32
  parent conditions hold on each, and the runner pins them by sha256
  (`prediction_manifest.json`, `policy_trace.json`, `surface_map.npz`) so a
  parent that changes after continuation is a structural FAIL.
- **The first six views are NOT rerendered.** Each continuation loads the exact
  saved map, gaze history, completed binocular observation history and final
  FSG6f `continue` decision, copies `maps/map_00..05.npz` byte-for-byte, and
  resumes acquisition at the already-recorded `next_gaze_deg`. The renderer
  refuses any step below the parent count, and the evaluator fails the record if
  any parent acquisition directory reappears or any copied parent map differs
  from its source by sha256. If a parent were missing or incompatibly changed,
  the run stops - it is never recreated by rerendering.
- **Scene, target geometry, texture and clutter, fixed head, static scene, the
  FSG1 stereo instrument at 256 spp, the 2.10 m prescribed vergence, FSG3's 12 mm
  fusion, oracle target segmentation and the FSG6f frontier/state/consensus/
  corridor/ranking policy are all unchanged**, imported rather than copied.
  Verified before acquisition: `reality2_run.py` imports `fsg6f_frontier as
  policy`, does not import `reality1_scene`, and defines none of FSG6f's frontier
  extraction, state classifier, consensus or ranking; `INSTRUMENT_ID`,
  `FROZEN_POLICY_ID`, `OBJECT_ID`, `FIXTURE`, `SEEDS`, `SEED_GAZE_DEG`,
  `VERGENCE_DISTANCE_M` and `FUSION` are measurably equal to `reality1_public`.
- **Scientific stopping is exactly `no_frontier` from frozen FSG6f.** No
  low-gain stop, no coverage target, no convergence heuristic and no operator
  judgement may end a run.
- **24 total fixations is an engineering watchdog only, not a quality gate.** It
  exists solely to bound an accidental non-terminating run. Reaching it is
  **reported descriptively and is not a scientific or integrity FAIL**; the
  evaluator records `watchdog_reached` as an observation alongside
  `terminated_by_no_frontier`.
- **There is still NO numerical quality PASS threshold.** Coverage, gain after
  look 6, point-to-surface error, overlap, measurement fraction, fixation count
  and efficiency are all descriptive. The only automated FAIL condition remains
  structural integrity: exact parent reuse without rerender, truth never opened,
  map containing only instance 141, every newly fused patch replay-idempotent, no
  repeated physical fixation, and FSG6f imported rather than copied.
- **After the two continuations, stop and return the report to Luiz/Chat.** They
  interpret whether simply letting the observer continue is good enough. Poor
  geometry, low coverage, watchdog termination, an odd trajectory or zero-gain
  views authorize **no** tuning: nothing about the scene, texture, policy,
  fusion, vergence, seeds, watchdog or any numerical constant may change in
  response, there is no rerender after a numerical disappointment and no
  alternate seed. A demonstrable implementation defect may be repaired minimally
  after diagnosis; scientific behaviour may not.

The per-run evaluator reports `REALITY2_OBSERVATION_COMPLETE` and the two-run
aggregate `REALITY2_COMPLETE` when structural integrity holds - **even if one or
both reach the watchdog** - or `REALITY2_INTEGRITY_FAIL` otherwise.

Outcome 2026-09-21 (evidence: `docs/reality-check-2.md` Results and
`docs/log.md`). **REALITY2_INTEGRITY_FAIL** - **solely because the two full
continuation records do not exist.** No structural integrity check failed
anywhere and no FAIL line was produced. The diagnostic smoke raised a runtime
exception, which by the authorization rule recorded above blocks full
acquisition, so neither full continuation was run and no comparison was
produced. Reality Check 1 remains preserved and unedited; FSG6f remains
CLOSED/PASS and unmodified; FSG7a, Scene-1a, Scene-1b and Scene-1c remain
preserved records. No prior decision is edited.

Everything upstream passed: `[reality2-check] passed=7 failed=0`, all seven
negatives exit 1, `[reality1-check] passed=6 failed=0` with all six negatives
exiting 1, `[fsg6f-check] passed=14 failed=0`, the diff over every FSG1/FSG3/
FSG6f and Reality Check 1 source empty against `7c1bfc7`, and **32 of 32
parent conditions holding on each saved record**, unchanged afterwards.

**The exact-continuation machinery works.** Six parent maps copied byte-for-byte,
resumption at the recorded `(14,6)` with no Reality Check 1 view rerendered, and
seven further looks acquired, fused and replayed successfully: coverage
**0.5276 -> 0.7904 (+26.3 points)**, 22,080 -> 33,775 map points, 12,282
multi-look surfels, median/P95 16.701 / 46.167 mm on `small`, map pure in {141},
thirteen unique gazes, every patch idempotent. **Removing the six-look
interruption is not futile on this fixture** - that part of the question is
answered affirmatively and descriptively.

**What blocked it**: at step 13 frozen FSG6f selected `(-16, +6)`, **3.5 degrees
beyond the target's left edge** (target yaw span [-12.54, +12.93]), giving zero
target pixels, and the guard `if len(p.xyz_h) < 100` - **verbatim inherited from
`reality1_run.py`** - aborted the run. Diagnosed read-only and three ways: the
parent state reconstructs bit-exactly; the decision replays deterministically
offline from the saved map and history alone; and it is the specified ranking
behaving as specified - `(-16,+6)` won on predicted new area **128.93 deg²**
despite the lowest corridor fraction (0.327 against 0.898 and 1.000), the lowest
frontier score and the only non-zero resolved-boundary count, because FSG6f's
frozen key is `(-area, -score, |dyaw|+|dpitch|, yaw, pitch)` and strict
OPEN-majority passes 77 > 0 + 21.

**No code fix was made and no source file was modified.** Choosing what an
off-object look means in a continue-until-`no_frontier` regime is a change to the
experiment's stopping semantics, which this decision explicitly reserves.

What would overturn or extend this: the blocking event is `small`-profile
evidence at one seed, so it does not establish that the `full` continuations
would abort at the same step, or at all - that is exactly what was not run. What
it does establish is that **whether frozen FSG6f ever reaches `no_frontier` on
this fixture is still unknown**, and that the record now holds **two independent
demonstrations that FSG6f's area-first ranking can walk off a fixture** - FSG6c's
`max()` case at three looks and this one at thirteen. That is evidence about the
object controller, not about the scheduler or the scene. **Luiz/Chat decide what
an off-object look means here and whether letting the observer simply continue is
good enough.**

## D-REALITY2b - Reality Check 2b: learn from an empty look (2026-09-21)

Reality Check 1 and Reality Check 2 are **preserved exactly as acquired and are
not edited, relabelled or rerun**; FSG6f remains CLOSED/PASS and unmodified, and
FSG7a, Scene-1a, Scene-1b and Scene-1c remain preserved records. No prior
decision is edited by this block.

Reality Check 2 established that continuing past the retired six-look
interruption is useful - its `small` continuation took visible coverage from
0.5276 to 0.7904 in seven further looks - and then aborted when frozen FSG6f
selected an off-target gaze whose stereo patch held fewer than 100 reconstructed
target points. Reality Check 2b asks the smaller follow-up: **if an exploratory
fixation finds essentially no target surface, can the observer treat that
completed binocular observation as negative evidence, recover, and continue until
frozen FSG6f itself says `no_frontier`?**

**Exactly one semantic change relative to Reality Check 2.** The inherited
condition `reconstructed target point count < 100` is **retained unchanged** and
reinterpreted: such a fixation (1) records its physical gaze as visited, (2)
appends its completed left/right instance masks and raw-support arrays to the
persistent observation history, (3) fuses **zero** target points and leaves the
persistent map unchanged, and (4) is followed by another call to the unchanged
FSG6f controller. This lets FSG6f's already-existing `BOUNDARY_RESOLVED`
mechanism learn from a place where the object was expected but not found. No
evaluator truth enters the prediction path.

Recorded before acquisition:

- **The two saved Reality Check 1 full records remain the parent states** and
  their first six views are **not rerendered**; `tools/reality2_render_fix.py` is
  reused directly and no new renderer is introduced.
- **Nothing else changes.** FSG6f ranking, every FSG6f constant, the scene and
  texture, the FSG1 stereo instrument at 256 spp, the 2.10 m prescribed
  vergence, FSG3's 12 mm fusion/hash, seeds 2111 and 2179, oracle target
  segmentation, fixed head, static scene and Reality Check 2's 24-total-fixation
  watchdog are all frozen. Verified before acquisition: the installed package
  adds exactly seven files, all `A`, and `git diff` over every FSG1/FSG3/FSG6f,
  renderer, rig, pin **and Reality Check 1/2** source against `27cfcc2` is empty.
- **The `<100` limit is not a tuned quality threshold** and will not be changed
  after seeing outcomes. It is exactly the retired Reality Check 2 abort guard,
  given semantics instead of being moved.
- **Scientific stopping is exactly `no_frontier` from frozen FSG6f.** The
  24-fixation watchdog remains an engineering guard only; **reaching it is
  descriptive, not a scientific or integrity FAIL.**
- **There is still NO numerical quality PASS threshold.** Coverage, recovery
  after an empty look, error, overlap, measurement fraction, fixation count and
  efficiency are all descriptive.
- **The only automated FAIL condition remains structural integrity**: exact
  parent reuse without rerender, truth never opened, map containing only instance
  141, every *fused* patch replay-idempotent, **every empty observation retained
  in gaze and binocular history while leaving the persistent map provably
  unchanged**, no repeated physical fixation, and FSG6f imported rather than
  copied.
- **The previously observed off-target direction near (-16,+6) is not
  hard-coded, forced or avoided.** Frozen FSG6f either reproduces it or does
  not; either is an observation.
- **After the two continuations, stop and return the report to Luiz/Chat.** A
  poor numerical result, repeated off-target exploration or watchdog termination
  authorize **no** tuning: no seed replacement, no gaze edit, no threshold move,
  no ranking change, no watchdog enlargement and no rerender after a numerical
  disappointment. A demonstrable implementation defect **in the new Reality 2b
  files only** may be repaired minimally after diagnosis; FSG6f, the `<100`
  condition, ranking, scene, seeds, watchdog and numerical outcomes may not.

The per-run evaluator reports `REALITY2B_OBSERVATION_COMPLETE` and the two-run
aggregate `REALITY2B_COMPLETE` when structural integrity holds - **even if one or
both reach the watchdog** - or `REALITY2B_INTEGRITY_FAIL` otherwise.

**What this decision would resolve.** If an empty look lets the observer recover
and frozen FSG6f then reaches `no_frontier`, the Reality Check 2 blockage was an
artifact of treating negative perception as a runtime error, and the open
question returns to reconstruction quality. If the observer keeps selecting
off-target gazes or reaches the watchdog still saying `continue`, then FSG6f's
area-first ranking - already shown to walk off a fixture twice, in FSG6c at three
looks and Reality Check 2 at thirteen - is implicated directly, and no amount of
extra looking fixes it.

Outcome 2026-09-21 (evidence: `docs/reality-check-2b.md` Results and
`docs/log.md`). **REALITY2B_COMPLETE** - both full records are structurally
valid, every `integrity_fails` list is empty, no FAIL line was produced
anywhere, and **both terminated by the scientific rule, `no_frontier`; neither
reached the watchdog.** Reality Checks 1 and 2 remain preserved and unedited;
FSG6f remains CLOSED/PASS and unmodified; FSG7a, Scene-1a, Scene-1b and Scene-1c
remain preserved records. No prior decision is edited.

**The prewritten rule resolves on its first branch.** This block recorded before
acquisition that if an empty look lets the observer recover and frozen FSG6f then
reaches `no_frontier`, the Reality Check 2 blockage was an artifact of treating
negative perception as a runtime error. It was. Seed 2111 finished in **13
fixations** and seed 2179 in **16**, both `no_frontier`, with coverage rising
**0.5345 -> 0.7984** and **0.7329 -> 0.8834** and surface medians of **5.878 mm**
and **5.812 mm**. The one semantic change - record the gaze, keep the binocular
observation, fuse nothing, leave the map unchanged, ask the unchanged policy
again - was sufficient on its own. **No code fix was made and no source file was
modified**; FSG6f, the `<100` condition, ranking, scene, texture, seeds,
vergence, fusion, parent views and the 24-look watchdog are untouched, and not
one of the twelve saved Reality Check 1 views was rerendered.

The recovery behaviour is directly evidenced, not inferred. At seed 2179 step 14,
gaze (-16,-4), a look returning **25 target points from 317 reference pixels**
left the map bitwise identical and the **immediate** frozen-FSG6f response was
`continue` with a new gaze and two surviving candidates. The observer
incorporated a near-empty look and kept going. Its next look was also near-empty
(11 points from 175) and then the frontier resolved. Seed 2111's single empty
look, 0 points from 0 reference pixels, resolved the frontier immediately.

Seed divergence largely stopped being a quality question: the two-seed coverage
gap **narrowed from 0.1984 at look 6 to 0.0850**, medians differ by 0.066 mm,
P95s by 0.26 mm, and both maps are ~41% multi-look, while the trajectories remain
entirely different and the fixation counts differ by three. It is now mainly an
efficiency difference.

What this does **not** resolve, and what it opens instead. `no_frontier` here
means "no open frontier reachable from the perimeter I walked", **not** "the
surface is finished": seed 2111 stops with a large unvisited rectangular hole in
the middle of the cloth, which is most of its missing 20%, and **five of the
seventeen new fused looks returned under 1% new points**. So the open question
moves off stopping semantics and onto the frozen controller again - **why does
FSG6f's frontier/consensus rule consider an enclosed interior hole resolved, and
why does area-first ranking keep spending full-cost looks on sub-1% returns?**
That is about FSG6f, not about the scheduler, the scene or the continuation
machinery. What would overturn or extend this: it is two seeds on one fixture
family with oracle segmentation, a fixed head and a static scene, so it says
nothing about specular, shadowed, thin or adversarial material, occlusion, object
discovery, or a target whose interior is not enclosed by its own perimeter.
**Luiz/Chat decide what to ask next.**

## D-CYCLOPEAN1A - Cyclopean-1a: spherical topology hole probe (2026-09-21)

Reality Checks 1, 2 and 2b are **preserved exactly as acquired and are not
edited, relabelled or rerun**; FSG6f remains CLOSED/PASS and unmodified, and
FSG7a, Scene-1a, Scene-1b and Scene-1c remain preserved records. No prior
decision is edited by this block.

Reality Check 2b closed its own question - the observer continues past six
looks, learns from empty looks, and terminates by `no_frontier` - and exposed the
next missing abstraction in doing so: **`no_frontier` can leave an enclosed
unsampled region.** Seed 2111 ended with a large ring-like interior gap and seed
2179 with a much smaller one. Cyclopean-1a asks the smallest next question:

> Can the persistent head/cyclopean spherical domain expose such internal
> sampling holes, distinguish them from an already-observed physical depth break,
> and place one foveation inside the largest unresolved hole without changing
> FSG6f?

This is the first concrete use of the cyclopean sphere as a 2-D perceptual
organization layer over the metric surfel scene. **The metric surfel map remains
authoritative; the chart is bookkeeping only.**

Recorded before acquisition:

- **The two completed Reality Check 2b full records are the parents**, located
  by manifest rather than by assumed path: `previews/reality2b/full-seed2111`
  (13 fixations, empty step 12) and `previews/reality2b/full-seed2179` (16
  fixations, empty steps 14, 15). Both audited before anything was run - schema
  `RealityCheck2b-prediction-v1`, profile `full`, termination **`no_frontier`**,
  `truth_opened` false, `fixed_head`/`static_scene` true, frozen FSG6f policy and
  FSG1 instrument, every map present - 23 of 23 and 26 of 26 conditions holding.
  Their manifest, policy-trace and final-map sha256 are pinned in the log entry
  below. **No parent view is ever regenerated**; if a parent were missing or
  changed, the run stops rather than recreating it.
- **Nothing in perception changes.** Fixed head, static scene, the Reality Check
  2b scene, texture and seeds, the FSG1 stereo instrument, FSG3's 12 mm
  association/hash, the FSG6f source and ranking, and Reality Check 2b's
  empty-look semantics are all frozen. Verified before acquisition: the installed
  package adds exactly seven files, all `A`, and `git diff` over every
  FSG1/FSG3/FSG6f, renderer, rig, pin and Reality Check 1/2/2b source against
  `077850d` is empty.
- **No new metric tolerance is introduced.** The angular raster reuses D9's
  already-declared evaluation scale `2*s0` (0.2 deg small, 0.1 deg full), and a
  surfel's angular footprint is derived from the frozen FSG3 radius as
  `alpha = atan(0.012 / median_range)`. Grid scale, the 12 mm footprint and the
  depth-break rule are fixed before data and may not be changed after it.
- **An internal hole is topological**: a connected component of the complement
  of rasterized target support that does **not** touch the padded chart border.
  The exterior component is therefore not a hole - a square-ring tabletop is the
  canonical counterexample the rule must respect.
- **A hole counts as an already-resolved physical depth break** when completed
  prediction-side observations inside it are non-target-majority **and** their
  reconstructed range differs from the nearby target-boundary range by more than
  the frozen 12 mm association radius. This is explicitly only a first geometric
  cue; surface-normal continuity is recorded as a future extension and is **not**
  added here. An unobserved or ambiguous hole may be probed, because an
  empty/non-target result is itself useful perceptual evidence.
- **One probe only, per parent record.** The largest remaining hole is selected
  by angular area, its spherical centroid is foveated **once** at 0.1-degree
  physical-view quantization, and target stereo is fused only if the inherited
  Reality Check 2b `<100`-point rule says it is a target measurement; otherwise
  it is retained as negative evidence and fuses nothing. **There is no loop of
  topology probes.** Integration with the active stopping rule is a later
  decision, not this one.
- **A record with no unresolved internal hole is still a valid observational
  result** and renders nothing. That is an outcome, not a failure.
- **There is NO numerical quality PASS threshold, and none may be added after
  seeing results.** Hole count, hole area, selected gaze, target points found,
  map growth and hole-area change are all descriptive. **A PASS may not be
  inferred from coverage or from hole reduction.** No evaluator truth, mesh
  reconstruction, hole filling, ICP, new stereo matcher, new frontier ranking or
  completeness percentage is permitted.
- **The only automated FAIL condition is structural**: the saved parent is read
  only and no parent view rerendered; no evaluator truth opened by the topology
  or probe path; topology built only from persistent surfels plus completed
  prediction-side stereo/instance observations; no mesh or hole filling; FSG6f
  neither modified nor copied; at most one new physical fixation per record; an
  empty probe retained as negative evidence fusing nothing; and a fused probe
  replay-idempotent with target-map purity preserved.
- **After the two probes, stop and return the report to Luiz/Chat.** A
  disappointing result authorizes no tuning: no grid-scale change, no footprint
  change, no depth-break-rule change, no scene or seed substitution, no FSG6f
  edit, no second probe and no post-hoc gate. A demonstrable implementation
  defect **in the new Cyclopean-1a files only** may be repaired minimally after
  diagnosis.

Diagnosis order fixed in advance, so that a surprising raster result cannot be
rationalised after the fact: if the local support raster produces small
discretization holes, **all holes and the largest are reported before any raster
rule is touched**; a parent path that differs from the example is resolved by
manifest, never by substituting data; a shape/schema mismatch when recomputing
observation evidence is diagnosed against saved `compute_once` output before any
code change; a selected centroid outside the allowed gaze domain or revisiting a
prior gaze is **reported and stopped on**, not patched with an invented action
rule; and a probe returning fewer than 100 target points is **valid Reality Check
2b negative evidence** - not an exception, and not a reason for another probe.

The aggregate reports `CYCLOPEAN1A_COMPLETE` when both parent records are
processed faithfully and any new probe is serialized with pure target geometry
and idempotent fusion, or `CYCLOPEAN1A_INTEGRITY_FAIL` otherwise.

**What this decision would resolve.** If the chart exposes the interior gaps that
Reality Check 2b left, separates them from genuine depth breaks, and places a
legal foveation inside the largest one, then the cyclopean sphere is a usable
perceptual organization layer and the next question is whether to let it inform
stopping. If it exposes nothing, or only discretization noise, or selects an
illegal gaze, then the representation is not yet carrying the structure that
`no_frontier` is missing, and the gap stays inside FSG6f's frontier rule.

Outcome 2026-09-21 (evidence: `docs/cyclopean1a.md` Results and `docs/log.md`).
**CYCLOPEAN1A_COMPLETE**, `structural_fails: []` - both parent records processed
faithfully, no parent view rerendered, no FAIL line anywhere. **Structural only;
no PASS is inferred from coverage or hole reduction.** Reality Checks 1, 2 and 2b
remain preserved and unedited; FSG6f remains CLOSED/PASS and unmodified. No prior
decision is edited. **No code fix was made and no source file was modified.**

**The prewritten rule resolves on its first branch, partially.** This block
recorded that if the chart exposes the interior gaps Reality Check 2b left,
separates them from genuine depth breaks, and places a legal foveation inside the
largest one, the cyclopean sphere is a usable perceptual organization layer. It
exposed and probed one such hole; it did **not** get the chance to separate a
depth break, because none arose.

Measured. Both charts: grid **0.1 deg**, footprint **4 cells** from the frozen
12 mm radius at the measured median range (0.322236 and 0.322291 deg), closing
gaps below **0.8 deg**; nothing tuned. **Seed 2111** - 117,567 surfels, complement
in **exactly one border-touching component**, therefore **zero internal holes, no
probe**, map bitwise unchanged, nothing rendered. **Seed 2179** - 138,010
surfels, **one internal hole of 772 cells / 7.7165 deg2** at (+6.2780, -1.5873),
state `UNOBSERVED_HOLE` with zero observed cells of either kind inside; centroid
snapped to **(6.3, -1.6)**, inside the domain and not a revisit; one fixation
returned **58,721 target points**, fused **3,174 new surfels**, replay-idempotent,
map 138,010 -> 141,184, multi-look 57,571 -> 70,136, instance ids {141}; selected
hole 7.7165 -> **0.3498 deg2**, no threshold attached.

**A Reality Check 2b description is corrected, and the numbers are not.** Seed
2111's gap was described there, from an (x,y) surfel scatter, as an enclosed
interior hole. The chart shows it is **open to the exterior** through a channel on
the left - a bay, not a lake. Every Reality Check 2b measurement stands; only that
topological characterisation was wrong, and catching it is what this layer is for.

What would overturn or extend this. **The physical-depth-break cue was never
exercised in the field**: the only hole found was unobserved, so the range-gap
test returned `None` and decided nothing. It passes its synthetic control
(`physicalclose`) and nothing more can be claimed for it from this run. The
discretization evidence is strong in the other direction - 330 and 410 internal
raw-complement components, the largest spurious one 0.4168 deg2, all removed by
the inherited footprint while seed 2179's genuine 13.88 deg2 component survived -
so the frozen 12 mm footprint is doing its job and needs no change. **This does
not settle whether topology should inform stopping**; Cyclopean-1a is one probe
by construction. Seed 2111 is the pointed case: an open bay left behind by
`no_frontier` is **not** something this chart alone would catch, because an open
bay is not a hole by the stated rule. If that matters, the next question is about
the boundary between `no_frontier` and chart topology, not about either alone.
**Luiz/Chat decide what to ask next.**

## D-CYCLOPEAN1B - Cyclopean-1b: spherical shoreline audit (2026-09-21)

Reality Checks 1, 2 and 2b and **Cyclopean-1a** are preserved exactly as acquired
and are **not edited, relabelled or rerun**; FSG6f remains CLOSED/PASS and
unmodified. No prior decision is edited by this block.

Cyclopean-1a answered its own question and, in doing so, corrected one of its
parent's descriptions: seed 2111's conspicuous missing region is not an enclosed
lake but a **bay**, connected to the exterior through a left-side channel. That
left a specific hole in the vocabulary. An internal hole is nameable and
probeable; **a bay is neither, because by the stated rule it is not a hole at
all** - yet it is exactly the kind of thing `no_frontier` leaves behind.
Cyclopean-1b asks the smallest next question:

> Can the same fixed-head cyclopean domain describe the *shoreline* of the
> sampled object, distinguish internal from exterior-connected complement, and
> say which boundary arcs are observed physical depth breaks versus continuation,
> unobserved or ambiguous - **without taking another fixation**?

This is an audit, not a controller extension. **The metric surfel map remains
authoritative; the chart is bookkeeping only.**

Recorded for this step:

- **The two completed Cyclopean-1a full records are the parents**, located by
  manifest rather than by assumed path, and are **read only**. Schema
  `Cyclopean1a-probe-v1`, profile `full`, `truth_opened` false,
  `fixed_head`/`static_scene` true, `parent_fixations_rerendered` 0,
  `added_fixations` in {0, 1}. Their manifest, `map_before` and `surface_map`
  sha256 are pinned before the audit and **re-verified byte-identical after it**.
- **Nothing is acquired.** No Blender process, no fixation, no fusion, no write
  into any parent. This is the first increment in the series whose entire cost is
  host-side analysis, and therefore the first with no prospective
  before-acquisition record to make - there is nothing irreversible to precede.
- **No new geometric tolerance is introduced.** The audit reuses the exact
  Cyclopean-1a chart - D9's `2*s0` grid and the support footprint derived from
  the frozen FSG3 12 mm association radius - and asserts the reconstruction
  against the parent manifest rather than recomputing a fresh scale.
- **A shoreline cell** is a complement cell 8-adjacent to current target support,
  and it **retains the identity of its complement component**: `INTERNAL` when
  that component does not touch the padded border, `EXTERIOR` when it does.
  **Border-touching means only topologically exterior. It does not mean the
  object has been observed to end there** - that conflation is the specific error
  this step exists to prevent, and a deliberate negative (`exteriorresolved`)
  fails if it is ever made.
- **Four boundary states, from completed prediction-side evidence only**:
  `UNOBSERVED` (no evidence), `TARGET_CONTINUATION` (target-only),
  `PHYSICAL_DEPTH_BREAK` (non-target-only whose range differs from the nearby
  target boundary by more than the frozen 12 mm radius), `AMBIGUOUS` (everything
  else observed). Adjacent same-state cells of the same component form an arc,
  with **no minimum arc length, no smoothing and no tuned morphology**.
- **Exterior penetration depth** - the 8-connected shortest complement-path
  distance from the padded border - is reported for exterior complement only, and
  is **purely descriptive**. It exists so that a deep bay can be *described*
  without inventing a threshold that declares it important.
- **There is NO numerical quality PASS threshold, and none may be added after
  seeing results.** Arc counts, shoreline length, component sizes and penetration
  depth are all descriptive. **No completeness percentage, no probe selection, no
  ranking rule and no stopping-policy change.** Forbidden outright: evaluator
  truth, mesh reconstruction, hole filling, boundary smoothing, a minimum-arc
  filter and any new acquisition.
- **The only automated FAIL condition is structural**: both parents read only and
  byte-identical afterwards; no acquisition launched; no evaluator truth opened;
  the inherited chart and footprint reused unchanged; internal and exterior
  complement kept distinct; and each output serialized with its parent hashes.
- **If the real shoreline is fragmented or visually messy, it is reported, not
  tuned.** A disappointing picture authorizes no morphology change after the
  fact. A demonstrable implementation defect **in the new Cyclopean-1b files
  only** may be repaired minimally after diagnosis; the inherited NaN-cast
  warning is explicitly **not** authorization to modify a Cyclopean-1a source,
  and if it ever demonstrably changed a 1b result the run stops for Luiz/Chat.

The aggregate reports `CYCLOPEAN1B_COMPLETE` when both parents are audited
read-only and both manifests satisfy the integrity fields, or
`CYCLOPEAN1B_INTEGRITY_FAIL` otherwise.

**What this decision would resolve.** If the chart can name a bay as an
unresolved boundary arc and separate it from boundary the observer has actually
seen past, then the cyclopean layer carries the structure `no_frontier` is
missing, and the open question becomes whether that structure should inform
stopping. If every arc looks alike, or exterior-connected boundary cannot be told
from a resolved physical edge, then the representation is still only a hole
detector and the gap stays inside FSG6f's frontier rule.

Outcome 2026-09-21 (evidence: `docs/cyclopean1b.md` Results and `docs/log.md`).
**CYCLOPEAN1B_COMPLETE**, `structural_fails: []` - both parents audited read-only
and byte-identical afterwards, no Blender process, no fixation, no FAIL line
anywhere. **Structural only; no PASS is inferred** from arc counts, shoreline
length or penetration depth. Cyclopean-1a, the Reality Checks and FSG6f remain
preserved and unedited. No prior decision is edited. **No code fix was made and
no source file was modified.**

**The prewritten rule resolves on its first branch.** The chart named the bay
without being asked to look for one. Seed 2111's bay is a **single connected
`UNOBSERVED` arc of 615 cells - 40.6% of the entire shoreline** - centroid
(-1.078, +2.015), span 20.5 x 8.9 deg, with exterior penetration depth
**[5, 132, 209] cells (up to 20.9 deg)** while the **second**-deepest of 213
exterior arcs reaches only **22**: a **9.5x** separation that no threshold
produced. **A bay is therefore describable even though it is not a hole** -
exactly the case Cyclopean-1a could not catch. Lakes and bays stay distinct: seed
2179's 35-cell residue from the 1a probe survives as the lone `INTERNAL` arc
(33 cells at (+6.852, -2.136)) while its staircase notch stays `EXTERIOR` at
depth 45.

**And the depth-break cue, which D-CYCLOPEAN1A recorded as never exercised in the
field, is exercised here.** `PHYSICAL_DEPTH_BREAK` arcs carry range gaps of
median 0.0315 / 0.0365 m up to **1.59** and **1.74** m (the room behind the
table), while every `AMBIGUOUS` arc with a defined gap sits **below** the frozen
radius at max 0.0118 / 0.0114 m: the inherited FSG3 12 mm scale, never chosen for
this purpose, **falls in the empty interval between two measured populations**.
The states separate spatially too, unforced - 63.0% and 68.2% of physical
shoreline cells lie below pitch -6.0 deg against 3.5% and 3.2% of unobserved
cells.

**Two of the four states did not occur, and that is recorded rather than
repaired.** `AMBIGUOUS` is entirely the sub-12 mm tail - zero cells carry both
kinds of evidence. `TARGET_CONTINUATION` is **0 arcs on both records and is
structurally unreachable**: **100.00%** of the 28,835 and 34,880 target-evidence
cells fall inside the dilated support, so none can ever be a shoreline cell,
because a fused target observation becomes a surfel whose 12 mm footprint covers
the cell it projected to. The four-state vocabulary is really a **three-state**
vocabulary on this fixture. Making the fourth occur would require changing the
inherited footprint or raster rule, which this block forbids.

What would overturn or extend this. The audit is **descriptive and changes no
policy**: no probe was selected, no gaze proposed, no stopping rule touched, and
**no completeness claim is made** - 40.6% describes the shoreline, not the
object, and `no_frontier` is not being called wrong. The shoreline is genuinely
**fragmented** (213 and 195 arcs, median arc 2 and 1 cells) because a minimum-arc
filter is forbidden; that is a measured property, and **nothing was smoothed
after seeing it**. The open question is unchanged in shape but now better posed:
**whether a deep unresolved arc should ever become a fixation**, and if so
whether that belongs in FSG6f's frontier rule or beside it. **Luiz/Chat decide
what to ask next.**

## D-CYCLOPEAN1C - Cyclopean-1c: one deep-bay probe (2026-09-21)

Reality Checks 1, 2 and 2b, **Cyclopean-1a and Cyclopean-1b** are preserved
exactly as acquired and are **not edited, relabelled or rerun**; FSG6f remains
CLOSED/PASS and unmodified. No prior decision is edited by this block.

Cyclopean-1b established that seed 2111's conspicuous missing region is a deep
**exterior-connected bay** whose shoreline is dominantly `UNOBSERVED`, and that
the chart can say so without any new machinery. It deliberately stopped there:
describing a bay is not acting on one. Cyclopean-1c asks the one small action
question that follows:

> If we foveate **once** at the deepest cell of that unresolved bay, does the
> existing stereo/fusion pipeline acquire useful target surface and reduce the
> bay, **without changing FSG6f or the stopping policy**?

This is one action, not a controller loop. **The metric surfel map remains
authoritative; the chart only chooses where to look.**

Recorded before acquisition:

- **The completed Cyclopean-1b seed-2111 audit is the parent**, located by
  manifest and read only, and its Cyclopean-1a and Reality Check 2b ancestry is
  read only as well. The map extended is the Cyclopean-1a `surface_map.npz`. All
  parent hashes are pinned before the probe and **re-verified byte-identical
  after it**.
- **Seed 2179 is deliberately not run.** Its principal internal hole was already
  probed in Cyclopean-1a; repeating that is not the question.
- **Nothing in perception changes.** Fixed head, static scene, the seed-2111
  acquisition history, the FSG1 stereo instrument, FSG3's 12 mm
  association/hash, FSG6f, Reality Check empty-look semantics, the Cyclopean-1a
  chart scale and footprint and the Cyclopean-1b boundary semantics are all
  frozen. **No new geometric tolerance is introduced.**
- **The bay rule is topological and threshold-free.** An eligible bay is an
  `EXTERIOR` complement component with at least one `UNOBSERVED` shoreline cell;
  among eligible components the one whose unobserved shoreline reaches the
  greatest inherited border distance is chosen, ties by more unobserved cells
  then smaller id. **There is no threshold saying how deep is deep enough**, and
  an exterior shoreline made entirely physical by observed deep non-target
  evidence yields **no** probe at all.
- **The probe is the deepest complement cell of that component**, ties resolved
  by nearness to the maximum-depth plateau's raster centroid, and a gaze already
  visited walks the same deterministic ordering to the first unvisited cell.
  **The deepest-cell rule and the gaze must be derived from the record**, never
  restated from a previously measured number.
- **Exactly one physical fixation, and only for seed 2111.** Inherited Reality
  Check 2b semantics apply unchanged: enough target points and the patch is
  fused at the frozen scale; empty or nearly empty and it is retained as negative
  evidence fusing nothing. A fused patch must be **replay-idempotent** and
  preserve **target-map purity**.
- **The before and after audits are rebuilt on the same inherited chart**, so the
  structural change is directly comparable rather than re-derived.
- **There is NO numerical quality PASS threshold, and none may be added after
  seeing results.** Target points, map growth, complement size, component counts
  and penetration depth are all descriptive. Forbidden outright: a second probe,
  a repeated bay loop, a stopping-rule change, FSG6f ranking modification,
  evaluator truth, mesh reconstruction, hole filling, morphology tuning,
  minimum-arc pruning, a normal cue, a new depth threshold and any coverage or
  reconstruction-quality gate.
- **The only automated FAIL condition is structural**: parents read only and
  byte-identical afterwards; no parent fixation rerendered; at most one added
  fixation; no evaluator truth opened; inherited chart, footprint and fusion
  scale reused; fused patch idempotent with target purity preserved.
- **If the one probe lands somewhere surprising but obeys the declared rule, the
  selector is not tuned afterwards.** A messy or disappointing result is
  preserved. A demonstrable implementation defect **in the new Cyclopean-1c files
  only** may be repaired minimally after diagnosis; the inherited NaN-cast
  warning is explicitly **not** authorization to modify a Cyclopean-1a source,
  and if it ever demonstrably changed a 1c result the run stops for Luiz/Chat.

**What this decision would resolve.** If one chart-chosen foveation at the
deepest unresolved bay cell returns real target surface and measurably reduces
the bay, then the cyclopean layer can not only describe what `no_frontier` left
but aim at it, and the open question becomes whether that should inform stopping.
If it returns nothing, lands illegally, or leaves the structure unchanged, then
the representation describes but cannot act, and topology stays a diagnostic.

Outcome 2026-09-21 (evidence: `docs/cyclopean1c.md` Results and `docs/log.md`).
**CYCLOPEAN1C_COMPLETE**, `structural_fails: []` - exactly one added fixation, no
parent fixation rerendered, the Cyclopean-1b parent byte-identical afterwards, no
FAIL line anywhere. **Structural only; no PASS is inferred** from target points,
map growth or bay reduction. Cyclopean-1a/1b, the Reality Checks and FSG6f remain
preserved and unedited. No prior decision is edited. **No code fix was made and
no source file was modified.**

**The prewritten rule resolves on its first branch, with a cost the branch did
not anticipate.** The selector derived everything from the record - one eligible
exterior component (18,116 cells, **1,059** unobserved shoreline cells reaching
depth **209**), deepest cell **(y=109, x=209)** at depth 209 with 3 cells tied,
gaze **(8.0, 2.1) deg**, **no revisit fallback needed**, step `fix_13`. That one
look returned **52,873 target points** and fused **20,167 new surfels** -
a **17.15%** gain on a map `no_frontier` had already declared finished -
replay-idempotent, ids **{141}**, map **117,567 -> 137,734**. **The bay is
measurably reduced**: max penetration depth **209 -> 168**, complement
**18,116 -> 13,366**, unobserved shoreline **1,059 -> 918**, cells deeper than
168 down to **zero**.

**But one probe did not finish the job, and it created structure of its own.**
The bay stayed **exterior-connected** through its narrow entrance channel, and
the record gained **two internal components where it had none** - 31 cells at
(+6.7903, -2.1484) and 1 cell at (+7.3000, -2.9000). Filling a bay from a single
viewpoint converts part of open water into enclosed lakes.

**And the residue is an instrument limit, not a sampling gap.** The 31-cell hole
was traced into the probe image: its centroid maps to pixel (228, 111), whose
neighbourhood is **10.4% valid against 82.2% frame-wide**, with local texture
**0.00117 against a frame median of 0.00992** and mean RGB [1.094, 0.263, 0.184].
It is the saturated, nearly untextured emblem printed on the cloth, where the
frozen SGBM instrument yields no disparity. **Bay depth alone would keep
proposing looks at a spot the instrument cannot resolve.**

What would overturn or extend this. **No stopping rule changed and none is
proposed**; FSG6f was never consulted. **Nothing here shows one probe is enough
or that more would converge** - a single action on a single seed cannot, and a
second probe was forbidden by construction. **No quality claim is made**: 20,167
surfels is a count, no evaluator truth was opened, so the correctness of the new
surface is unmeasured. The 3D map is coherent by the checks available - new
surfels entirely inside the old range envelope, pre-existing surfels moved by at
most **5.94 mm**, and **61.9%** of probe points associating with existing surfels
within the frozen 12 mm radius - but coherent is not accurate. The sharpest
question this run raises is not whether topology can aim a look, which it did,
but **what a topology-driven controller should do when the thing it can see is
something the instrument cannot measure**. **Luiz/Chat decide what to ask next.**

## D-CYCLOPEAN1D - Cyclopean-1d: observation versus measurement (2026-09-21)

Reality Checks 1, 2 and 2b and **Cyclopean-1a, 1b and 1c** are preserved exactly
as acquired and are **not edited, relabelled or rerun**; FSG6f remains CLOSED/PASS
and unmodified. No prior decision is edited by this block.

Cyclopean-1c filled a bay with one chart-chosen fixation and left a tiny residue
that its own diagnosis called **seen but not measured** - image evidence existed
where frozen stereo returned no valid depth. That exposed a flaw in the
vocabulary rather than in the instrument: the Cyclopean-1b state `UNOBSERVED`
means only "no valid 3D evidence landed here", which silently merges two
different situations. Cyclopean-1d asks only:

> Of the final shoreline cells that the frozen Cyclopean-1b semantics still call
> `UNOBSERVED`, which were **truly never imaged**, and which were **imaged as
> target but not measured in depth**?

Read-only. It takes no look. **The representation should first say what actually
happened, so no controller has to invent a heuristic for it later.**

Recorded for this step:

- **The completed Cyclopean-1c seed-2111 record is the parent**, located by
  manifest, and its whole ancestry - Cyclopean-1b, Cyclopean-1a, Reality Check 2b
  and Reality Check 1 - is **read only**. All pinned hashes are verified
  byte-identical after the audit.
- **Nothing is acquired.** No Blender process, no fixation, no fusion, no write
  into any parent. Only already-saved calibration, rectification, crop, oracle
  instance masks, calibration support and the frozen stereo `valid` mask are read.
- **The base semantics are not redefined.** The final Cyclopean-1c support is
  rebuilt on the exact inherited chart and Cyclopean-1b's shoreline states are
  reused unchanged; `PHYSICAL_DEPTH_BREAK` and `AMBIGUOUS` are untouched, and
  **only** base-`UNOBSERVED` cells are refined.
- **Observation and measurement are independent fields.** Target instance at a
  calibration-supported projected pixel means the target was **observed**; that
  same pixel also satisfying the saved `valid` mask means depth was **measured**.
  Collapsing the two is a deliberate negative (`depthonly`) that must fail.
- **The continuation test point is a projection hypothesis and never geometry.**
  It uses only the inherited Cyclopean-1b `local_target_range_m` on the cell's
  cyclopean ray, to ask what completed images contained at its projected
  location. **It is never fused and never treated as measured surface.**
- **No texture or quality threshold is introduced.** The audit reads the
  instrument's already-saved validity rather than reverse-engineering why stereo
  failed. Cyclopean-1c's texture statistics were a diagnosis, not a rule.
- **Six refined states, all descriptive**: `NEVER_OBSERVED`,
  `OBSERVED_TARGET_NO_DEPTH`, `OBSERVED_TARGET_WITH_DEPTH` (diagnostic - imaged,
  measured, yet still outside support), `OBSERVED_NONTARGET_ONLY`,
  `MIXED_OBSERVATION`, and `NO_RANGE_REFERENCE` for cells where the inherited
  local range is undefined so no projection is attempted.
- **No state selects a fixation.** No gaze policy, no ranking, no stopping change,
  no FSG6f import, no mesh, no morphology, no minimum-arc pruning, no normal cue,
  no evaluator truth, and **no percentage becomes a completeness gate**.
- **The only automated FAIL condition is structural**: parent and ancestry read
  only and byte-identical afterwards; no acquisition launched; no evaluator truth
  opened; inherited chart, footprint and boundary scale reused; observation kept
  separate from depth.
- **A projection defect may be repaired from camera geometry and round-trip or
  known-point checks only.** An empirical pixel offset, dilation, tolerance or
  texture threshold introduced **after seeing the result** is forbidden; if the
  declared continuation projection were intrinsically too ambiguous to support the
  audit, the run stops for Luiz/Chat rather than being tuned. The inherited
  NaN-cast warning remains outside this step.

**What this decision would resolve.** If the refinement separates the residue that
Cyclopean-1c called seen-but-unmeasured from boundary that was genuinely never
imaged, then the representation can state *why* a boundary is still open, and the
open question becomes what a controller should do differently for each cause. If
every cell looks alike, the distinction is not carried by the saved record and
the conflation stays.

Outcome 2026-09-21 (evidence: `docs/cyclopean1d.md` Results and `docs/log.md`).
**CYCLOPEAN1D_COMPLETE**, `structural_fails: []` - read-only, parent and ancestry
byte-identical afterwards, no Blender process, no FAIL line anywhere. **Structural
only; no state is a PASS and none selects a fixation.** Cyclopean-1a/1b/1c, the
Reality Checks and FSG6f remain preserved and unedited. No prior decision is
edited. **No code fix was made and no source file was modified.**

**The prewritten rule resolves on its first branch, and more sharply than it
asked.** Replaying **14 completed fixations** (`fix_00`..`fix_13`) split the
**918** base-`UNOBSERVED` cells exactly, with nothing left over, and the split
follows an anatomical line:

- **`OBSERVED_TARGET_NO_DEPTH` 28 cells - every one of them internal.** Component
  2 gives 27 cells at (+6.7926, -2.1519) with **27 target-seen and 0 depth-valid**
  over 27 supported projections; component 1 gives 1 cell at (+7.3000, -2.9000).
  Both centroids match the residue Cyclopean-1c reported. **Every internal cell
  with a range reference is seen-but-unmeasured, 28 of 28, and not one is
  `NEVER_OBSERVED`.** Of the 14 views, **exactly one - `fix_13`, the 1c probe
  itself - contributed any supported projection there.** This confirms
  Cyclopean-1c's emblem diagnosis **from the instrument's own saved `valid` mask**
  rather than from the RGB texture proxy 1c had to use.
- **`NEVER_OBSERVED` 388 cells in one single arc**, centroid (-3.621, +2.306), at
  the maximum penetration depth **168** - the deep bay remnant. All **5,432**
  projection attempts (388 cells x 14 views) fell **entirely outside the rectified
  core of every view**; zero landed inside a core at all. Absence of attention in
  the strongest available sense, and checked rather than assumed.
- **`OBSERVED_NONTARGET_ONLY` 398 cells on the outer rim** - imaged, with the
  continuation hypothesis finding background rather than target. Not unexplored:
  the object ends, and the boundary stayed open only because the inherited state
  had no way to say so.
- **`NO_RANGE_REFERENCE` 104 cells**, all at distance **5.10 cells** from the
  nearest raw support, strictly beyond the inherited 5-cell disk - a deterministic
  artifact of the inherited radius, left unadjusted because widening it would be a
  new tolerance.

**Two of the six states never fired**: `OBSERVED_TARGET_WITH_DEPTH` and
`MIXED_OBSERVATION` are both **0**. Preserved as honest nulls; the diagnostic
state finding nothing means no fusion or support-rasterization loss showed up.

**The projection was validated before it was trusted**, because the shipped
self-test uses an identity `R_hc` and cannot confirm the convention on real data:
round-tripping each observation's own reconstructed points gave **0.0000 px**
median, p95 **and max** reprojection error on all three ancestry branches. No
defect, and no empirical offset was introduced.

What would overturn or extend this. **Nothing here changes any controller** - no
gaze proposed, no ranking touched, no stopping rule consulted, FSG6f never
imported - and **no completeness claim is made**: 42.27% and 43.36% describe a
shoreline, not an object. **The continuation test point remains a hypothesis**, so
`OBSERVED_NONTARGET_ONLY` is evidence about that hypothesis at that assumed range,
not proof the surface ends; a different continuation range could read differently
and none was tried. **104 cells stay unclassified by construction.** The sharp
question this run hands forward is the one it deliberately refuses: **what should
a controller do differently for boundary that was never seen versus boundary the
instrument cannot measure** - the first is answerable by looking, the second is
not. **Luiz/Chat decide what to ask next.**

## D-CYCLOPEAN1E - Cyclopean-1e: epistemic gaze (2026-09-21)

Reality Checks 1, 2 and 2b and **Cyclopean-1a, 1b, 1c and 1d** are preserved
exactly as acquired and are **not edited, relabelled or rerun**; FSG6f remains
CLOSED/PASS and unmodified. No prior decision is edited by this block.

Cyclopean-1d showed that the single word `UNOBSERVED` had been hiding different
situations, and split seed 2111's remaining shoreline into distinct causes: the
deep exterior slot was genuinely `NEVER_OBSERVED`, while the tiny internal emblem
residue was `OBSERVED_TARGET_NO_DEPTH` - imaged once, and returned no depth the
frozen instrument could produce. 1d deliberately refused to act on that. This
block asks the one question that follows:

> If the refined state is allowed to choose exactly one new fixation from
> genuinely `NEVER_OBSERVED` exterior shoreline, does it aim a useful look while
> **ignoring** the already-seen/no-depth residue?

One action, not a loop. **The metric surfel map remains authoritative; the
refined chart only chooses where to look.**

Recorded for this step:

- **The completed Cyclopean-1d seed-2111 record is the parent**, located by
  schema rather than by remembered path, and it and every ancestor are **read
  only**, with pinned hashes verified byte-identical afterwards.
- **Seed 2111 only, and at most one added fixation** - zero is a legitimate
  outcome if no eligible cell exists.
- **The candidate entity is narrow and stated in advance**: a cell must lie on
  the current shoreline, belong to an **`EXTERIOR`** complement component, and be
  refined **`NEVER_OBSERVED`**. **`OBSERVED_TARGET_NO_DEPTH` is explicitly not a
  candidate** - re-looking at a region the instrument already failed to measure
  would be an identical blind repeat, and a deliberate negative (`nodepth`) fails
  if it ever becomes eligible.
- **The selection rule is the inherited depth field, with no new threshold or
  tuned score**: among eligible exterior components take the one whose
  `NEVER_OBSERVED` shoreline reaches the greatest inherited exterior border
  distance, then the deepest such cell, ties by distance to the tied plateau
  centroid and then raster order, with visited gazes skipped in that same
  deterministic order. **The depth value and the gaze must be derived from the
  record**, never restated from a previously measured number.
- **Nothing in perception changes.** Fixed head, static scene, the seed-2111
  acquisition history, the FSG1 stereo instrument, FSG3's 12 mm
  association/hash, the inherited chart and footprint, Cyclopean-1b boundary
  semantics, Cyclopean-1d refinement and the Reality Check 2b empty-look contract
  are all frozen. A fixation below the inherited minimum stays a valid negative
  observation and fuses nothing.
- **There is NO numerical quality PASS threshold, and none may be added after
  seeing results.** Target points, surfel gain, coverage, complement size and
  depth reduction are all descriptive. Forbidden outright: a second epistemic
  gaze, a repeated loop, a stopping-rule change, FSG6f import or modification,
  evaluator truth, mesh, morphology tuning, normals, a texture threshold and any
  new geometric tolerance.
- **The only automated FAIL condition is structural**: parent and ancestry read
  only and byte-identical afterwards; no parent fixation rerendered; at most one
  added fixation; no evaluator truth opened; inherited scales reused; a fused
  patch replay-idempotent with target-map purity preserved.
- **A surprising but rule-obeying landing is not tuned away.** Only a
  demonstrable implementation defect in the new Cyclopean-1e files may be
  repaired, and **no check may be weakened to obtain green output**; any change
  outside the seven 1e files requires explicit justification.

**What this decision would resolve.** If the refined state can name one action
directly - aiming at genuinely unseen boundary and leaving the unmeasurable
residue alone - then refining the entity simplified the next action instead of
requiring a new heuristic, and the open question becomes what a controller should
do about the residue. If the refined state cannot pick a legal gaze, or picks the
residue, then the refinement is descriptive only and the action problem stays
where Cyclopean-1c left it.

Outcome 2026-09-21 (evidence: `docs/cyclopean1e.md` Results and `docs/log.md`).
**CYCLOPEAN1E_COMPLETE**, `structural_fails: []` - exactly one added fixation, no
parent rerender, parent byte-identical afterwards, no FAIL line anywhere.
**Structural only; no PASS is inferred** from surfel gain, coverage or depth
reduction. Cyclopean-1a/1b/1c/1d, the Reality Checks and FSG6f remain preserved
and unedited. No prior decision is edited. **No code fix was made and nothing
outside the seven Cyclopean-1e files was modified.**

**The prewritten rule resolves on its first branch.** The selector derived
everything from the record: **exactly one** eligible exterior component with
**388** `NEVER_OBSERVED` shoreline cells spanning depths 9 to **168**, deepest
cell **(y=62, x=127)** at depth **168** with 2 cells tied, gaze **(-0.2, -2.6)
deg**, **not** a revisit, `revisit_fallback_rank` **0**, step `fix_14` - a legal
unvisited gaze on the first try, with no threshold and no tuned score between the
representation and the action.

**And the exclusion held, measured rather than assumed.** All **28**
`OBSERVED_TARGET_NO_DEPTH` cells carry `exterior_distance = -1` and sit in
components **1 and 2, both `INTERNAL`**, so they fail the state test *and* the
exterior test independently. After the look they are **unchanged at 28**, and
both internal components are bitwise the same objects - 1 cell at
(+7.3000, -2.9000) and 31 cells at (+6.7903, -2.1484), the identical centroids
Cyclopean-1c and 1d reported. The experiment looked **past** the region it could
not use.

Measured. The fixation returned **54,623 target points** and fused **9,262 new
surfels** (45,361 matched), map **137,734 -> 146,996** (+6.72%),
replay-idempotent, ids **{141}**, reproduced bitwise independently of the runner.
**`NEVER_OBSERVED` fell 388 -> 290** and its maximum penetration depth
**168 -> 142**; complement **13,366 -> 10,995**, support **38,971 -> 41,342**,
shoreline **1,384 -> 1,287**. Coherence without truth: new surfels **entirely
inside** the old range envelope with zero outliers, pre-existing surfels moved by
at most **5.99 mm**, **83.0%** of probe points associating within the frozen 12 mm
radius, and the new patch sitting only **8.7 mm** from its neighbours' median
range - a smoother join than Cyclopean-1c's.

What would overturn or extend this. **No stopping rule changed and none is
proposed**; FSG6f was never imported or consulted. **One fixation on one seed
shows nothing about convergence** - the slot did **not** close, **290**
`NEVER_OBSERVED` cells remain at depth **142**, and a second epistemic gaze was
forbidden by construction, so whether this iterates to a fixed point is untested.
**No quality claim is made**: 9,262 surfels is a count, evaluator truth stayed
closed, and internal coherence is **not** accuracy. **Nothing was learned about
what to do with `OBSERVED_TARGET_NO_DEPTH`** - the step deliberately walked around
it. The question this hands forward is therefore unchanged in shape but now
sharper: **a topology-driven action works where looking helps, so what action, if
any, belongs to a region the instrument cannot measure from any viewpoint?**
**Luiz/Chat decide what to ask next.**

## D-CYCLOPEAN1F - Cyclopean-1f: iterate epistemic gaze to a fixed point (2026-09-21)

Reality Checks 1, 2 and 2b and **Cyclopean-1a, 1b, 1c, 1d and 1e** are preserved
exactly as acquired and are **not edited, relabelled or rerun**; FSG6f remains
CLOSED/PASS and unmodified. No prior decision is edited by this block.

Cyclopean-1e showed that one literal read-out of the refined perceptual field -
`EXTERIOR + NEVER_OBSERVED -> deepest inherited border distance -> one foveation`
- aimed a useful look while ignoring `OBSERVED_TARGET_NO_DEPTH`. It was one
action by construction, so it could say nothing about where repetition leads.
This block asks only:

> If exactly that rule is repeated **without modification**, does the observer
> reach a state with no eligible exterior `NEVER_OBSERVED` shoreline?

This is a convergence/fixed-point experiment for one seed, **not a new controller
design**.

Recorded for this step:

- **The completed Cyclopean-1e seed-2111 record is the parent**, located by
  manifest, and it and every ancestor are **read only**, with pinned hashes
  verified byte-identical afterwards. The runner additionally asserts that its own
  rebuild reproduces the parent's published epistemic fields **before** acquiring
  anything.
- **The mechanism is frozen end to end**: fixed head, static scene, the same
  cyclopean chart and 0.1 degree grid, the same footprint from the frozen 12 mm
  FSG3 radius, the same Cyclopean-1d epistemic state definition, **the same
  Cyclopean-1e gaze selector reused unchanged at every iteration**, the same
  Reality/FSG stereo path and 12 mm fusion, and the same Reality Check 2b
  empty-look semantics. **No FSG6f ranking or stopping logic is imported.**
- **The candidate entity does not widen with iteration.** Only `EXTERIOR`
  shoreline refined `NEVER_OBSERVED` is eligible. **`OBSERVED_TARGET_NO_DEPTH`
  never becomes eligible merely because geometry is still missing there**, and no
  `INTERNAL` component is eligible. An empty look remains valid negative evidence
  and fuses nothing.
- **The scientific stop is the absence of an eligible cell**,
  `NO_ELIGIBLE_EXTERIOR_NEVER_OBSERVED`, and nothing else. **The inherited
  total-24-fixation limit is an engineering watchdog only; reaching it is not
  scientific success** and must be reported plainly as a guardrail stop.
- **There is NO numerical quality PASS threshold, and none may be added after
  seeing results.** No minimum bay depth, area, gain, coverage or accuracy; no
  fixed number of scientific iterations; no mesh, morphology tuning, normal cue,
  texture threshold, new geometric tolerance or evaluator truth.
- **The only automated FAIL condition is structural**: parent and ancestry read
  only and byte-identical afterwards; no parent fixation rerendered; no evaluator
  truth opened; inherited scales reused; each fused patch replay-idempotent with
  target-map purity preserved.
- **A disappointing trajectory authorizes no rescue.** No retargeting after
  seeing a low-yield look, no threshold introduced to force termination, and no
  check weakened to obtain green output. Only a demonstrable implementation
  defect in the new Cyclopean-1f files may be repaired.

**What this decision would resolve.** If the unchanged rule exhausts its own
eligible field and stops on its own condition, then this epistemic action rule
has a fixed point on this record and the remaining boundary can be described by
what is left rather than by what was tried. If it reaches the watchdog, or
oscillates, or starts selecting the excluded residue, then the rule does not
terminate by itself and iteration is not yet the right frame.

Outcome 2026-09-21 (evidence: `docs/cyclopean1f.md` Results and `docs/log.md`).
**CYCLOPEAN1F_COMPLETE**, `structural_fails: []`, stop reason
**`NO_ELIGIBLE_EXTERIOR_NEVER_OBSERVED`** - the **scientific** stop, not the
watchdog. **Structural only; no PASS is inferred** from coverage, gain, depth or
look count. Cyclopean-1a..1e, the Reality Checks and FSG6f remain preserved and
unedited. No prior decision is edited. **No code fix was made and nothing outside
the seven Cyclopean-1f files was modified.**

**The prewritten rule resolves on its first branch.** Repeated unchanged, the
selector consumed the remaining eligible field in **two** fixations - **17 total
against the 24-look watchdog**, so the guardrail was never approached. **Step
15**, gaze **(+1.3000, +4.2000)**, cell (y=130, x=142) at depth **142** = the
component maximum, returned **58,475 target points** and fused **3,298** new
surfels; `NEVER_OBSERVED` **290 -> 142**, max depth **142 -> 69**. **Step 16**,
gaze **(-6.0000, +4.2000)**, cell (y=130, x=69) at depth **69** = again the
maximum, returned **50,010 target points** and fused **5,196**;
`NEVER_OBSERVED` **142 -> 0**, max depth **69 -> None**. Both replay-idempotent,
ids **{141}**, map **146,996 -> 155,490**, and **the maximum depth of the whole
exterior component fell 142 -> 22**, so no deep pocket survives anywhere.

**The exclusion held for the whole loop, not just the first step.**
`OBSERVED_TARGET_NO_DEPTH` was **28 at every iteration**, and both internal
components are bitwise the same objects at the same centroids -
**(+7.3000, -2.9000)** and **(+6.7903, -2.1484)** - that Cyclopean-1c, 1d and 1e
each reported. The loop's termination is therefore precisely a success at
**avoiding** the region it could not use.

**The residual is described, not repaired.** At the fixed point 527 shoreline
cells remain base-`UNOBSERVED`: **423** `OBSERVED_NONTARGET_ONLY` on the outer
rim at shallow ordinary depth (min 0, median 9, max 22) - the object's own edge,
imaged with background beyond; **28** `OBSERVED_TARGET_NO_DEPTH`, the untouched
emblem; and **76** `NO_RANGE_REFERENCE`, all at **5.10 cells** from raw support,
just past the inherited 5-cell disk - the same deterministic artifact
Cyclopean-1d measured, **left unadjusted** because widening that radius would be
a new tolerance.

**One weakness in this step's own controls is recorded rather than patched.** The
six `--negative` paths in `check_cyclopean1f.py` print a FAIL line and exit 1
**unconditionally** for any recognised name; they do not inject the named
mutation into the real selector and verify the production code rejects it, which
is weaker than the negative sets of Cyclopean-1a through 1e. The **positive**
checks were verified genuinely fail-capable against mutated scratch copies of the
real sources - three independent invariants each produced their own FAIL and
exit 1 - so what this step asserts is enforced, but the `--negative` flags are
declarations rather than controls. Nothing was modified, since this does not
block the experiment; **if these checks are to be relied on later as controls,
they need rewriting to mutate and detect.**

What would overturn or extend this. **This is one rule on one seed**, and the
contract says so: a scientific stop shows only that *this* epistemic action rule
reached *its own* fixed point on *this* record. **It is not object completeness** -
527 shoreline cells remain, 423 of them imaged-with-background and 28
seen-but-unmeasurable. **It is not accuracy**: evaluator truth stayed closed, so
every coherence number is internal consistency and nothing more. **It says
nothing about other seeds or scenes**, or about whether the rule terminates where
the geometry is less benign. **The empty-look branch was never exercised**, since
both fixations were rich, so the negative-evidence path remains untested inside
this loop. And **`OBSERVED_TARGET_NO_DEPTH` is exactly where Cyclopean-1d left
it**: the question of what action, if any, belongs to a region the instrument
cannot measure is untouched by a loop whose success consisted of stepping around
it. **Luiz/Chat decide what to ask next.**

## D-CYCLOPEAN1G - Cyclopean-1g: re-centered measurement probe (2026-09-21)

Reality Checks 1, 2 and 2b and **Cyclopean-1a through 1f** are preserved exactly
as acquired and are **not edited, relabelled or rerun**; FSG6f remains CLOSED/PASS
and unmodified. No prior decision is edited by this block.

Cyclopean-1f reached **attention completion** on seed 2111: no exterior
`NEVER_OBSERVED` shoreline remained, and the loop stopped on its own condition.
What survives is qualitatively different from everything the series has chased so
far - an internal residue **imaged as target** for which the frozen stereo
instrument returned **no valid depth**. Looking harder is not obviously the
answer, because the observer has already looked. This block asks one narrow
question:

> If that dominant `OBSERVED_TARGET_NO_DEPTH` residue is placed at the foveal
> centre for **one** new look, does the **unchanged** stereo instrument recover
> valid target depth there?

Recorded for this step:

- **The completed Cyclopean-1f seed-2111 record is the parent**, located by
  manifest and read only, and its required conditions are asserted before
  anything runs: `scientific_stop_reached` true, `stop_reason`
  `NO_ELIGIBLE_EXTERIOR_NEVER_OBSERVED`, `exterior_never_observed_cells` **0**,
  and the established 28-cell residue present. Pinned hashes are verified
  byte-identical afterwards.
- **The candidate entity is the inverse of every earlier step.** Only
  **`INTERNAL` + `OBSERVED_TARGET_NO_DEPTH`** is eligible - specifically the
  component with the most such cells, and within it the eligible cell nearest
  that residue's chart centroid, with a revisit falling through to the next cell
  in the same centroid-distance ordering. **`NEVER_OBSERVED` and exterior
  components are ineligible**, which reverses Cyclopean-1e/1f exactly.
- **The only deliberate measurement change is re-centering.** The Reality/FSG
  renderer, rectification, SGBM front end, baseline, vergence and render
  settings, the chart, the footprint, the 12 mm fusion scale and every geometric
  tolerance stay frozen. **This isolates foveal placement as the single
  variable**, so a negative result means placement is not the cause.
- **The outcome is binary and diagnostic, never a gate.** `DEPTH_RECOVERED` if
  at least one pre-probe residue cell is observed as target *with* valid stereo
  depth in the new look; `DEPTH_STILL_ABSENT` otherwise. **No recovered-cell
  count, coverage figure or surfel gain is a PASS threshold**, and none may be
  added after seeing the result.
- **Exactly one added fixation, and the branch closes regardless of outcome.**
  No second view, alternate matcher, interpolation, texture rescue, normal cue or
  any new mechanism. A still-unmeasurable residue is **recorded and deferred, not
  turned into a rescue subproject**.
- **The only automated FAIL condition is structural**: parent and ancestry read
  only and byte-identical afterwards; no parent fixation rerendered; exactly one
  added fixation; no evaluator truth opened; inherited scales reused; any fused
  patch target-pure and replay-idempotent.
- **The deliberate negatives are restored to genuine source-mutation controls.**
  Cyclopean-1f's named flags were declaration-only - they printed and exited 1
  regardless of the code - and that weakness was recorded rather than patched.
  Here each negative mutates the real source, re-evaluates the checks, and exits
  1 **only if a previously-passing check now fails**, with an escaped mutation
  reported as an error instead of a pass.

**What this decision would resolve.** If re-centering recovers depth, then part
of this measurement failure is a placement artifact and the instrument is less
limited than it appeared. If depth is still absent with every other variable
frozen, then the residue is a genuine limit of the current fixed-head stereo
instrument on this material, and the case is closed and deferred rather than
chased.

Outcome 2026-09-21 (evidence: `docs/cyclopean1g.md` Results and `docs/log.md`).
**CYCLOPEAN1G_COMPLETE**, `structural_fails: []`, measurement outcome
**`DEPTH_STILL_ABSENT`**. One added fixation, no parent rerender, parent
byte-identical afterwards, no FAIL line anywhere. **Diagnostic only; no gate.**
Cyclopean-1a..1f, the Reality Checks and FSG6f remain preserved and unedited. No
prior decision is edited. **No code fix was made and nothing outside the seven
Cyclopean-1g files was modified.**

**The prewritten rule resolves on its second branch, as cleanly as it could.**
The selector chose component **2** - **27** no-depth cells of 31, the dominant
residue - and its centroid-nearest cell **(y=66, x=197)**, gaze
**(+6.8000, -2.2000) deg**, `revisit_fallback_rank` **0**. In the new look **all
27** residue cells had a **supported projection** and **all 27 were imaged as
target**; **zero** recovered valid stereo depth, and **zero** saw non-target.
**The re-centering worked as an acquisition change and the instrument still
returned nothing.** Placement is not the cause.

The re-centering is independently visible in the observation: with the residue at
the fovea centre, the central **32x32** window is **23.0%** valid against
**86.7%** frame-wide, and its mean RGB **[0.9514, 0.4590, 0.3305]** against a
frame mean of [0.6358, 0.5021, 0.4057] - the saturated, near-uniform emblem,
squarely in the fovea, with no internal detail for a correspondence matcher.

**The residue count moved 28 -> 22, and this block records that as bookkeeping
rather than progress.** Traced cell by cell: 21 kept, **7 disappeared, 1 newly
appeared**, and **all 7 that disappeared became support** because the 194 newly
fused surfels - all from the textured cloth *around* the emblem - brought their
12 mm footprints over those rim cells. **Not one cell left the state by being
measured.** Ordinary structural checks held: 55,567 target points, 194 new /
55,373 matched (**99.7%** overlap within 12 mm), map 155,490 -> 155,684,
replay-idempotent, ids exactly **{141}**, and the fusion reproduced **bitwise**
independently of the runner.

What would overturn or extend this. **One look, one residue, one seed.** It says
nothing about whether some *other* instrument change - a different matcher,
baseline, vergence, illumination or an active pattern - would recover the depth;
**none was tried, by design**, and that is the deferred case. It is **not an
accuracy claim**: evaluator truth stayed closed, so the 194 new surfels and the
99.7% overlap are internal consistency only. And `DEPTH_STILL_ABSENT` is **not a
failure of the experiment** - it is the measurement the experiment was built to
take, and it closes the branch honestly rather than leaving an open rescue thread.

**Disposition.** The residue is recorded as **unresolved under the current
fixed-head stereo instrument and deferred**. **The intended next research stage
is multiple objects** - declared before the run and unchanged by this outcome -
progressing afterward toward the full cyclopean scene. **Luiz/Chat decide what to
ask next.**
