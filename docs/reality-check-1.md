# Reality Check 1 — good enough for an ordinary static scene?

## Question

After FSG6f and the failed Stage-II Scene-1a/1b/1c sequence, the immediate question is no longer whether another scheduler can be invented.  It is whether the existing single-object mechanism is already useful on geometry and texture that are less laboratory-like.

Reality Check 1 therefore asks one deliberately pragmatic question:

> Does the frozen FSG6f mechanism produce a recognisable, metrically sane active reconstruction of one moderately irregular, mixed-texture target in a small cluttered static scene?

This is a **reality check, not a benchmark**.  It is not adversarial and it does not attempt to establish worst-case robustness.

## Frozen assumptions

- fixed head;
- static scene;
- frozen FSG1 local stereo instrument;
- frozen FSG3 12 mm surface fusion;
- frozen FSG6f frontier/state/consensus/corridor/ranking policy, imported directly;
- frozen six-fixation object budget;
- oracle target-instance segmentation remains allowed;
- no head motion, object discovery, learned policy, ICP, meshing or hole filling.

## Scene

The target is a shallow hanging cloth/poster-like surface, approximately 0.90 m × 0.64 m at the validated ~2.1 m range.  Its depth varies non-periodically by about 8 cm across the visible surface.  It is represented by 120 rendered triangles rather than by a plane or a constant-radius cylinder.

The target texture is intentionally **mixed rather than uniformly rich**: a broad low-contrast region, a modest printed band/emblem, subtle fabric variation and a small repetitive weave region.  The surrounding scene contains a table, wall and two unrelated side props with their own textures.  The target is not deliberately occluded.

The scene remains opaque and diffuse because Reality Check 1 is meant to change as little as possible at once.  Specularity, strong shadows, thin structure and adversarial materials are later reality checks if this one is promising.

## Schedule

Two fresh stochastic seeds are frozen prospectively: 2111 and 2179.  Both begin from the same prescribed seed fixation `(-6°, -4°)` and then hand control entirely to the unchanged FSG6f policy for at most six physical fixations.

Develop on `small`; report each seed once at `full`.

## What is gated

Only structural integrity is gated:

- prediction never imports/open evaluator truth;
- map contains only the target instance;
- every fused patch replays idempotently;
- no physical fixation repeats;
- FSG6f is imported rather than copied/reimplemented;
- the six-look budget and 12 mm fusion rule remain unchanged.

## What is deliberately *not* gated

No new coverage, error, overlap, measurement-fraction or termination threshold decides PASS/FAIL.  The following are reported descriptively:

- visible-surface coverage by fixation;
- approximate point-to-surface median and P95 distance;
- overlap consistency;
- target measurement support;
- multi-look surfels;
- fixation trajectory and termination reason;
- variation between the two render seeds;
- RGB fixation previews, map growth and PLY.

The outcome is `REALITY1_OBSERVATION_COMPLETE` if the run is structurally valid.  Luiz/Chat then decide whether the behaviour is **good enough** to justify the next practical step.  Numerical misses are evidence, not an invitation to tune this record.

## Results

_To be filled by Code from the workstation run.  Preserve both full runs exactly as acquired._
