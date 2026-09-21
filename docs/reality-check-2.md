# Reality Check 2 — let the observer finish

## Question

Reality Check 1 produced coherent geometry on a moderately realistic mixed-texture target, but both full records ended only because the inherited six-fixation experiment limit was reached while frozen FSG6f still said `continue`.

Reality Check 2 asks the simplest follow-up:

> If those exact saved states are not interrupted at six looks, does the unchanged observer continue to useful new surface and eventually stop by its own `no_frontier` rule?

## One scientific change

The six-look interruption is removed.  Nothing else in perception changes.

The first six full observations are **not rerendered**.  For each seed, the runner loads the exact Reality Check 1 map, gaze history, completed binocular observation history, and the final FSG6f `continue` decision.  Acquisition resumes at the already-recorded `next_gaze_deg`.

Frozen:

- Reality Check 1 scene, target geometry, texture and clutter;
- seeds 2111 and 2179 and their exact first six records;
- fixed head, static scene, oracle target segmentation;
- FSG1 stereo, 2.10 m vergence and full 256 spp instrument;
- FSG3 12 mm fusion;
- FSG6f frontier/state/consensus/corridor/ranking policy.

Scientific stopping is exactly `no_frontier` from frozen FSG6f.

A 24-total-fixation watchdog exists only to bound an accidental non-terminating run.  Reaching it is reported, not turned into a quality or integrity FAIL.

## Interpretation

There is again no tuned numerical quality PASS threshold.  The useful questions are descriptive:

1. how much additional visible surface is acquired after look 6;
2. whether added views preserve geometric coherence;
3. whether FSG6f eventually reaches `no_frontier`;
4. whether the two stochastic trajectories become similarly complete even if their paths and fixation counts differ.

The exact Reality Check 1 coverage at look 6 is the baseline for each seed.  No alternate seeds, scene edits, policy changes, low-gain stops or rerenders are allowed in response to the result.
