# Phase A — summary

`visgraf/fov-3d-vision`, 2026-09-12 to 2026-09-13. State at `d808769`, Phase A closed. Every number
below was measured on the lab workstation (Blender 5.2.1 LTS, OptiX, RTX 4090) unless
marked assumed; the notes in `docs/` hold the commands that produced each one.

## The question

Context.txt posed it: the retina is a variable-resolution sensor, so foveation is a
bandwidth decision before it is an attention mechanism, and active vision is a controlled
sampling problem. The engineering claim that follows is *the same posterior for less
computation*, which is only a claim once there is a declared computational budget and a
declared error. Phase A's job was to build the sensor, declare both, and measure the claim
on real scenes.

## What was accomplished

**A1 — scenes.** Three tiers, each verified on the GPU: a generated calibration room with
50 targets of known geometry (Siemens-star cards at 1 to 11 degrees, wire targets against
plain wall); the Poly Haven `workshop` HDRI, which is its own reference; and Blender's
Classroom with an `EYE` placed into it. Checked for holes, back-faces and metric scale.

**A2 — reference and noise floor.** A noise-floor tool that estimates one render's noise
from two seeds, σ = RMS(A−B)/√2, with no converged reference and no bias from one. It gave
the spp for the references (8192, per scene, under D7), the call floor and the marginal cost
of a render (9.9 to 10.4 ns per pixel-sample), and projections that the later renders
matched to within 8%. Two full references at foveal spacing s₀ = 0.05° (7200×3600, box
filter, uniform sampling): 32.3 min for the calibration room, 35.8 min for the Classroom.
Those two times *are* the uniform-cost baseline — the cost of the render that foveation
replaces. Small references (s₀ = 0.1°, 1024 spp, about a minute) for development. All
pinned by md5 in `scenes/manifest.json`.

**A3 — the foveated camera.** The warp s(e) = s₀(1 + e/E₂) as a Cycles OSL custom camera,
first in numpy, then verified on the GPU against the CPU. One fixation of a 45° half-field at
s₀ = 0.05° costs 50,269 samples against 2.55 M for uniform sampling of the same field —
50.8× fewer rays, measured.

**A4 — fixation sequences.** A gaze list rendered in one Blender session, writing the D1
sample record per fixation: origin, direction, value, footprint in steradians, ray
distance, fixation id, raster index. 15 ms per fixation at the small profile, 140 ms at
the full one. The marginal cost per sample is 10.1 to 11.0 ns — the same as the uniform
camera's — so foveation saves by taking fewer samples, not cheaper ones. Checks: the
analytic warp composed with the gaze agrees with the renderer's own Position pass to
0.018 reference pixels (p99.9); footprints sum to the solid angle of the cap to 0.02%.

**A5 — integration and the curve.** The samples of a sequence integrated into a spherical
map (finest-owns: the finest sample covering a cell owns it, coarser samples fill only
gaps), reconstructed at a declared evaluation scale and compared to the reference at that
scale (D9). The error-versus-budget curve for K = 1 to 50 fixations, with a uniform
render at the *same number of rays* beside every point, on both scenes and both profiles.

**A6 — the warp sweep.** E₂ of 1, 2 and 4° and e_max of 30, 45 and 60° on the calibration
room at the small profile, compared at equal rays. The two Phase A criteria disagree:
E₂ = 4 gives the lowest fixated-target error (0.103 against 0.155 at E₂ = 2), E₂ = 1 the
lowest covered-sphere error, because a larger E₂ buys denser sampling around the fovea at
the price of fewer fixations per budget. D11 keeps E₂ = 2, e_max = 45 standing and names
the objective that will decide: Phase B's disparity error at fixated targets, per ray.

**The result.** At the targets, foveation reaches a lower error than uniform sampling at
equal rays at every budget, on both scenes and both profiles. Over all 50 targets at the
full profile: 1.9× lower on the calibration room and 2.7× on the Classroom. At the targets
the observer actually fixated — the number a fixation buys — 2.5× on the calibration room
(0.146 vs 0.365 at K = 1) and 3.0× on the Classroom (0.075 vs 0.228 at K = 5). Over the sphere, uniform
wins at every budget below the largest, where the two are level on the covered part. The
mechanism is measured, not argued: uniform saturates at the targets because at these
budgets its pixels are coarser than the content and, once fine enough, pay the registration
floor; foveation places four s₀ samples per evaluation cell exactly where it looked. And
foveation does not cover the sphere — 58% after fifty fixations — with the covered periphery
charged for its 0.5 to 1.2° footprints.

**The apparatus.** Eleven decisions (D1–D11) with what would overturn each; a working agreement
(`CLAUDE.md`) with two hard rules — every number is measured or assumed, never in between,
and every tool ships a check that can fail — plus cost classes (interactive < 10 s,
batch < 5 min, overnight with a logged justification) and two profiles one flag apart.

## What we learned

1. **Per-sample cost is invariant.** The foveated camera pays 10 ns per sample, the
   uniform one 10 ns per pixel-sample, and a fixation sequence at N rays takes the same
   seconds as a uniform render at N rays (0.78 s vs 0.71 s at 40 M). So *rays* is an honest
   budget and the x-axis of the curve is time.

2. **The metric decides the answer more than the sampling does.** Under D8 — compare each
   sample to the reference at the sample's own footprint — uniform won at every budget,
   because a 2.3° pixel that correctly averages 2.3° of sky is charged only for its noise.
   Under D9 — reconstruct at a fixed evaluation scale and compare there — the same data
   gave the result above. D8 answers "is each sample right at its own scale", a validation
   question; D9 answers "how much of the scene does the representation know at the scale
   the task needs". The project's claim is the second. Phase B's matching error will be
   read against D9 and its floors, not against pixel counts.

3. **How samples are combined matters as much as how they are taken.** Weighting by
   1/footprint let the periphery of one fixation blur the fovea of another: half the weight
   in target cells came from samples coarser than twice the finest, and the target error
   *rose* with the number of fixations. Finest-owns fixed it.

4. **Comparing off-grid samples to a grid reference has a floor, and it is measurable.**
   On content at the resolution limit, two grids half a pixel apart disagree by 0.17 to
   0.38 (relative RMS, at the targets). The floor was measured with a second reference
   rendered half a pixel off — a true off-grid sample of the same scene, no interpolation
   — and every result is stated against it. A bilinear shift overstates it, because a
   bilinear shift is also a blur.

5. **A reference only needs to be a few times cleaner than what it is compared to.** A
   fixed 1% noise target, set by the darkest patch of the Classroom, demanded 131,072 spp
   and ten hours per scene. The right criterion (D7) — reference noise at most a third of
   the fixation noise, so it adds about 5% to the error budget — is met at 8192 spp.

6. **Projection against measurement is a bug detector.** Four silent failures were caught
   by a number disagreeing with its prediction or by a check that could fail: the Render
   Result buffer read after the next render (two "different-seed" renders identical to
   1.5e-7); the Classroom's keyframed Cycles seed overwriting the one the script set;
   persistent data ignoring a bare change of sample count (16, 256 and 4096 spp all in
   16 ms); adaptive sampling shipped on in the calibration blend (a "35-minute" render in
   135 s). None raised an exception. All are now guarded.

7. **The only slow thing is the baseline.** A fixation is 15 to 140 ms; the noise floor is a
   minute; the whole full-profile curve is batch class. The 35-minute renders are the
   uniform-at-foveal-spacing baseline, rendered once per scene and kept as pinned assets.
   Nothing in the iteration loop should ever wait on anything like them.

8. **The calibration room is a hard case by construction.** Its spokes recur every two
   pixels at the small profile's s₀; it isolates the registration floor and exercises the
   metric, but it is not representative of scene content. The Classroom, with texture at
   many scales and a plain-walled periphery, shows the larger gap (2.7×) and is the better
   guide to what a matcher will see.

## Why it matters

Before Phase A the foveation claim was an argument from physiology. Now it is a curve with
a declared budget, a declared error scale, a measured floor, and a uniform baseline at
equal cost beside every point — reproducible from a repository by two commands. The
result cuts both ways, which is what makes it credible: foveation wins where the observer
looked and loses on coverage, and the size of each is a number. That is also the shape the
active-vision thesis needs: the value of a fixation is measured at the fixated target, and
the coverage cost is what a gaze policy exists to manage.

## How it carries into Phase B

Phase B is binocular: a second `EYE` at a fixed interocular offset, fixation pairs verged
on the same target, and the disparity between the two per-eye maps read against the
Depth pass. Phase A hands it:

- **The data structure.** Per-eye spherical maps built from D1 sample records that carry
  the footprint with the value. With both eye centres fixed in the head (D3), the baseline
  is fixed and the epipolar geometry is constant; rectification is one change of
  coordinates on the sphere.
- **A stated error.** Any matching error can be decomposed into the two eyes' D9 errors,
  the registration floor and the matcher's own contribution, because the first three are
  measured.
- **The budget and its cost.** 10 ns per sample, 140 ms per full-profile fixation, and
  the knowledge that a fixation pair costs two fixations, not more.
- **The check that can fail first.** Recovered depth at a fixated calibration target must
  match the manifest's ground truth to within the s₀ angular quantisation.
- **What is still open.** E₂ and e_max are standing, not chosen (D11): the sweep tool
  exists, is batch class, and is re-run with the disparity error as its objective once
  Phase B can measure one. Any gaze order other than target order, and any gaze policy
  (Phase C); error on distance, since only radiance has been compared; budgets beyond
  fifty fixations.

## Deliverables

All in `github.com/visgraf/fov-3d-vision`, `main` at `d808769`.

| Kind | What |
|---|---|
| Tools | `make_calib_room.py`, `make_hdri_scene.py`, `fetch_hdris.py`, `place_eye.py`, `preview360.py`, `inspect_preview.py`, `noise_floor.py`, `foveated_camera.osl` + `render_foveated.py`, `fixation_sequence.py`, `integrate_sphere.py`, `exr_lite.py`; checks `check_noise_floor_stats.py`, `check_foveated.py`, `check_sequence.py` |
| Scenes | Three tiers in `scenes/`, with `calib_room.targets.json` (50 targets, ground truth) and `manifest.json` recording every reference with spp, render time, noise and md5 |
| Assets (pinned, kept outside the checkout) | Full references at s₀ = 0.05°, 8192 spp, both mesh scenes; small references at s₀ = 0.1°; off-grid shifted references at both profiles |
| Record format | D1 sample record: `samples.npz` + `columns.json` per fixation, `sequence.json` per sequence |
| Result | `docs/phase-a-result.md` with the D9 curves at both profiles, all-targets and fixated-targets columns, `curve.json` / `curve.csv`, four charts in `docs/reference/`; `docs/a6-warp-sweep.md` |
| Notes | `docs/a1` … `a6`, `docs/reviews/2026-09-12-noise-floor.md`, `docs/log.md` (dated, measured-or-assumed) |
| Decisions | `DECISIONS.md`, D1–D11, each with its overturn condition |
| Working agreement | `CLAUDE.md`: hard rules, cost classes, profiles, references as assets, Chat / Code roles |
