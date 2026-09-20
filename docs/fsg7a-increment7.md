# FSG7a — prescribed head motion reveals self-occluded surface

## Status before acquisition

**Prospective. No scientific acquisition has been run by Chat.** Increment 6 is closed at FSG6f. FSG7a opens Increment 7 with one deliberately narrow question.

## Physics first

A true self-occluded surface cannot become visible merely because the eyes rotate. With a fixed pair of eye centres, changing fixation changes which rays receive high-resolution sampling but does not change line-of-sight visibility of a world point. Repository decision D3 anticipated this explicitly: head motion is a new phase/question.

Therefore FSG7a changes one physical assumption only: the binocular rig translates laterally while its orientation stays fixed. The surface map remains in the **initial head frame H0**. The head motion is prescribed; there is no new motion policy yet.

## Research question

> Can the frozen FSG1 local stereo instrument, followed by exact-pose transport into H0 and the frozen 12 mm FSG3/FSG4 fusion rule, reconstruct a surface continuation that is binocularly self-occluded at H0 and becomes visible only after a prescribed lateral head translation?

A PASS establishes the measurement and mapping substrate needed for active hidden-surface discovery. It does **not** establish that the observer can choose the head motion. That is the next question.

## Frozen components

- FSG1 instrument: `FSG1-HDR-SGBM-one-original-update-original-validity-v1`.
- FSG3/FSG4 fusion: 12 mm association radius and 12 mm hash cell.
- IPD, profile, SPP and 2.10 m prescribed vergence.
- Oracle instance segmentation remains object identity only.
- No ICP, mesh reconstruction, hole filling or registration optimization.

## New component

Two acquisition head frames Ht have the same orientation as H0 but different origins. Stereo reconstruction is produced in the local Ht frame by the unchanged instrument and transported exactly to H0 before fusion:

\[
\mathbf x_{H0}=\mathbf x_{Ht}+\mathbf t_{H0}.
\]

The rendered world does **not** move with the head.

## Fixtures

Two fresh connected folded ribbons use one public object instance ID:

- `fold_right`: a front panel at z = -2.50 m with a return wing folding backward from its right edge;
- `fold_left`: the mirrored physical fold on the left.

The front panel is 0.36 m wide by 0.30 m high. The return wing is 0.65 m deep by 0.30 m high. Both panels share the same rendered instance ID; evaluator-only part labels distinguish front versus return for measurement.

At H0, direct evaluator geometry gives **0.0000 return visibility in both eyes** on both fixtures. After the prescribed ±0.45 m lateral head translation, direct geometry gives **1.0000 visibility in both eyes**. These are design checks, not experimental results.

## Prescribed views

Each trial has exactly two binocular acquisitions:

- step 0: H0, gaze (0°, 0°), front seed;
- step 1: translate +0.45 m for `fold_right` / -0.45 m for `fold_left`, gaze ∓5.5° yaw, 0° pitch, revealing the return wing.

Fresh seeds: 1409 and 1453. Four full trials total.

## Prospective decision rule

A full trial passes only if all of the following pass:

- each patch object measurement coverage >= 90%;
- reveal patch has >= 5,000 fixed-H0 overlap matches;
- reveal overlap median <= 10 mm and P95 <= 25 mm;
- reveal replay is idempotent;
- final map contains only object instance 151;
- >= 5,000 final surfels have support >= 2;
- final folded-surface median error <= 10 mm and P95 <= 30 mm;
- seed front-wing coverage >= 80%;
- seed return-wing coverage <= 5%;
- final return-wing coverage >= 80%;
- return-wing coverage gain >= 75 percentage points;
- final whole-object coverage >= 90%;
- evaluator direct visibility confirms fixed-head return visibility <= 2% and moved-head binocular visibility >= 95%.

FSG7a passes only if all **4/4** fresh full trials pass. If not, preserve the failure and stop.

## What a PASS means

A PASS supports only this claim:

> Exact known head translation can reveal a genuinely self-occluded continuation and the existing local stereo/fusion stack can place the newly visible measurements coherently into persistent H0 memory without ICP.

It does not yet support active head-motion selection, occlusion classification by the controller, learned gaze, multiple objects, or free six-degree-of-freedom motion.
