# FSG Blend Bridge-2 — one structured Classroom fixation

## Question

Does the **unchanged native FSG tangent-plane stereo instrument** remain well behaved when the local Classroom core contains real scene structure rather than the near-ideal single textured floor plane of Bridge-1R?

Bridge-2 changes **only the gaze condition**. It does not introduce a controller, fusion, FSG6f, matcher tuning, truth gating, or a second measurement.

## Experimental control

Bridge-1R is the control condition:

- same scene: `scenes/classroom/classroom_eye.blend`;
- same `EYE`, IPD, vergence, `small` profile, 64 spp, seed 2111;
- same baseline-projected tangent frame;
- same `tools/fsg_stereo.py` without edits;
- one fixation;
- Blender truth used only after stereo for evaluation.

Bridge-2 differs only in selecting a core with multiple substantial instance regions and a real depth discontinuity.

## Gaze selection is sealed before stereo

Candidate gazes are a fixed 30-view grid:

- yaw: `[-180,-150,-120,-60,-30,0,30,60,120,150]` degrees;
- pitch: `[-30,0,30]` degrees.

Each candidate is acquired with the existing Bridge tangent renderer. **No SGBM is run on any candidate before selection.** The selector refuses any candidate directory that already contains `stereo/`.

Selection sees only:

- raw tangent RGB;
- raw Blender first-hit instance IDs;
- evaluator-only Blender first-hit range;
- calibration metadata.

Candidate acquisition may use 16 spp because these renders are only an oracle planning scaffold. The final selected fixation is reacquired at the control setting of 64 spp before stereo.

### Eligibility

The declared FSG core must have:

- truth hit fraction >= 0.95;
- a second instance occupying >= 0.10 of core pixels;
- reference range `P90-P10 >= 0.40 m`;
- median reference range jump across an instance boundary >= 0.20 m;
- fixed-transfer grayscale standard deviation >= 8 u8 levels.

These are **selection heuristics only**, not stereo-quality thresholds. If no candidate passes, Bridge-2 stops; the criteria are not relaxed after seeing data.

Among eligible candidates choose, in order: largest second-instance fraction, largest median boundary depth jump, largest texture standard deviation, largest robust depth span, smallest absolute pitch, then ascending wrapped yaw.

## Measurement

After `selection.json` is sealed, reacquire exactly the selected gaze at 64 spp and run the existing `tools/fsg_stereo.py` once. Then run the existing bridge evaluator. Do not retune or repair the matcher after seeing the result.

Report overall accuracy and, importantly, split diagnostics for:

- pixels whose 3x3 neighborhood is single-instance interior;
- pixels within a small image-space band of an instance boundary;
- each substantial reference instance in the core;
- error as a function of reference depth.

The split analysis is evaluator-only and must not alter validity or geometry.

## Stop

One final fixation only. No second gaze, no fusion, no controller, no FSG6f, and no Classroom demo continuation.
