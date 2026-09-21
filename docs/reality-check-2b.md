# Reality Check 2b — learn from an empty look

## Status

Prospective. No workstation acquisition has been run from this package.

## Question

Reality Check 2 established that continuing beyond the old six-look interruption is useful: the saved small-profile continuation increased visible target coverage from about 0.528 to 0.790 before frozen FSG6f selected an off-target gaze and the inherited `<100 target points` guard raised a runtime exception.

Reality Check 2b asks one smaller question:

> If an exploratory fixation finds essentially no target surface, can the observer treat that completed binocular observation as negative evidence, recover, and continue until frozen FSG6f itself says `no_frontier`?

This is not a new ranking, a new frontier rule, or a new quality gate.

## Scientific change

Exactly one semantic change is authorized relative to Reality Check 2.

The condition that previously aborted the run,

```text
reconstructed target point count < 100
```

is retained unchanged but reinterpreted.

For such a fixation:

1. the physical gaze is recorded as visited;
2. the completed left/right instance masks and raw-support arrays are appended to the persistent observation history;
3. zero target points are fused and the persistent map must remain unchanged;
4. the unchanged FSG6f controller is called again using that new history.

This allows FSG6f's already-existing `BOUNDARY_RESOLVED` mechanism to learn from a place where the object was expected but not found. No evaluator truth enters the prediction path.

## Frozen pieces

- exact Reality Check 1 scene and texture;
- exact saved Reality Check 1 six-look parents, reused without rerender;
- seeds 2111 and 2179;
- fixed head and static scene;
- prescribed 2.10 m vergence;
- FSG1 stereo instrument;
- FSG3 12 mm fusion/hash;
- complete FSG6f frontier/state/consensus/corridor/ranking implementation;
- Reality Check 2's 24-total-fixation engineering watchdog;
- no numerical quality PASS threshold.

`tools/reality2_render_fix.py` is reused directly; no new renderer is introduced.

## Stopping semantics

Scientific stop:

```text
frozen FSG6f -> no_frontier
```

Engineering guard:

```text
24 total fixations
```

Reaching the watchdog is descriptive, not a tuned quality failure.

## Prospective schedule

Development smoke:

- exact saved Reality Check 1 `small` parent for seed 2111, if present;
- continue under the new empty-observation semantics;
- a genuine implementation/provenance/runtime defect blocks full acquisition;
- a poor numerical result does not.

Full observations, each once:

- exact saved Reality Check 1 `full-seed2111` parent;
- exact saved Reality Check 1 `full-seed2179` parent.

Do not replace a seed, alter a gaze, tune a threshold, change ranking, enlarge the watchdog, or rerender after a numerical disappointment.

## What to report

For each seed report the entire continuation trajectory, coverage by fixation, map size, support, metric surface statistics, termination reason, and all integrity checks.

For every empty target observation report:

- fixation step and gaze;
- reconstructed target-point count and target measurement fraction;
- confirmation that the map before/after the empty look is identical;
- the policy decision immediately after the empty look;
- whether a later fixation returned to useful target surface;
- subsequent coverage gain.

The central descriptive outcomes are:

1. whether an empty look can resolve the false frontier and allow recovery;
2. whether frozen FSG6f eventually reaches `no_frontier`;
3. whether the two stochastic trajectories end in comparably useful reconstructions;
4. whether geometry remains coherent as additional looks accumulate.

## Interpretation

A bad exploratory fixation is allowed. The experiment tests whether the observer can incorporate the negative observation and recover rather than requiring every saccade to be correct in advance.

## Results

_To be filled by Code from measured workstation records. Preserve all outcomes, including watchdog termination or repeated off-target exploration._
