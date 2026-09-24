# FSG Blend Bridge-5 — controlled texture × slant factorial

## Question

Bridge-4 rejected the simple hypothesis that disparity separation alone produces the detached foreground-disparity capture seen in the Classroom. At a matched gap, two measured differences remained: the Classroom foreground had about twice the local texture evidence of the background, and the background was a vertically slanted disparity surface (~0.0478 px/px) rather than fronto-parallel.

Bridge-5 asks, with the native FSG matcher frozen:

> Are background slant and/or foreground/background texture-strength asymmetry sufficient to trigger the detached epipolar foreground-disparity capture?

## Design

A predeclared 2×2 factorial, repeated for texture seeds 2111, 2112, 2113:

| Cell | Far geometry | Far texture gain | Purpose |
|---|---|---:|---|
| A | flat (`k=0`) | 1.0 | Bridge-4-like control |
| B | flat | 0.44 | texture asymmetry only |
| C | slanted (`k=1.8`) | 1.0 | slant only |
| D | slanted | 0.44 | slant + texture asymmetry |

Everything else is fixed: small profile, yaw/pitch 0/0, vergence 2.10 m, IPD 63 mm, baseline-projected tangent frame, near plane 1.40 m, far base depth 2.40 m, near silhouette, near texture, and unchanged `tools/fsg_stereo.py`.

The far base depth 2.40 m gives approximately the Bridge-4 11.4 px gap, close to the sealed Classroom ~12.2 px case. `k=1.8` was selected prospectively from camera geometry because it yields approximately 0.047 px/px vertical true-disparity slant, close to the sealed Classroom ~0.0478 px/px. The far texture gain 0.44 targets the sealed Classroom near/far local-texture ratio near 2:1; the analyzer reports the measured ratio rather than assuming it.

## Measurement

Capture uses the unchanged Bridges 3/4 definition:

`alpha = (d_est - d_true) / (d_near - d_true)`

`alpha >= 0.5` means the estimate is closer to the foreground disparity plateau than to its own far-surface truth.

Per condition the evaluator reports measured true disparity gap/slant, local 5×5 texture evidence, far acceptance, capture fraction/count, capture reach, and same-row versus no-near-row behavior. The aggregate reports all four factorial cells and descriptive contrasts B−A, C−A, D−C, D−B, and the interaction `D-C-B+A`.

## Boundaries

This experiment does not tune or repair SGBM. It does not change block size, mode, P1/P2, LR tolerance, the 3-px instance guard, depth bounds, or texture threshold. It does not launch Blender, use the Classroom fixation, run a controller, or fuse observations. Analytic truth remains under `evaluation_only/` and is used only after stereo.
