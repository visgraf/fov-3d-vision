# Classroom-Oracle-3: Eligibility Audit

## Question

Classroom-Oracle-1 showed that the perfect-measurement controller reconstructs most of the reachable Classroom surface, but leaves a structured residue. Classroom-Oracle-2 widened the controller domain by ten degrees in every direction and falsified the hypothesis that the original residue was primarily caused by angular extent: five of the six largest-deficit objects followed byte-identical trajectories and did not use the extra domain.

Oracle-3 therefore asks a narrower question:

> **At the moment the controller declares attention complete, why is the still-reachable surface no longer represented as an actionable next fixation?**

## Scientific contract

Oracle-3 is a read-only audit. It performs:

- zero new Blender acquisitions;
- zero new fixations;
- zero fusion operations;
- zero changes to FSG6f;
- zero changes to the Cyclopean selector;
- zero changes to the 12 mm rule, watchdog, domain, scene, seeds, or matcher;
- no numerical quality PASS threshold.

The audit is explicitly two-phase.

### Phase 1: controller replay, truth closed

For every Oracle-1 target, reconstruct the completed observation history and final metric map, replay the frozen final FSG6f decision, and reconstruct the Cyclopean support/shoreline/epistemic chart. The replay must reproduce the saved final decision exactly on the fields needed for eligibility diagnosis.

FSG6f termination is summarized as one of:

1. `NO_OPEN_FRONTIER`;
2. `OPEN_BUT_NO_CANDIDATE`;
3. `CANDIDATES_REJECTED_BY_CONSENSUS`;
4. `STOP_OTHER`;
5. `ACTIVE`.

The audit also wraps the already-existing helper calls when reachable through the live policy path, recording corridor and consensus calls without replacing their behavior.

### Phase 2: post-hoc truth diagnosis

Only after all controller replays have completed successfully may the program open Oracle-1 dense reachable-surface truth.

Every reachable sample that is more than 12 mm from the final object map is projected to the frozen Cyclopean chart and classified by the first Cyclopean eligibility rule that excludes it:

1. `NOT_SHORELINE`;
2. `INTERNAL_COMPONENT`;
3. `ALREADY_OBSERVED`;
4. `PREVIOUSLY_FIXATED_CELL`;
5. `ELIGIBLE_NEVER_OBSERVED_EXTERIOR`;
6. `OUT_OF_CHART`.

A second label records a more descriptive subtype such as angular support but 3-D uncovered, internal target-with-no-depth, exterior target-with-no-depth, or never-observed exterior.

The six focus objects are selected deterministically from the already-completed Oracle-2 Scope-A evaluation: the six objects with the largest Oracle-1 miss counts. This is not a new favorable subset chosen by hand.

## Expected outputs

```text
previews/classroom-oracle-3-audit/
  manifest.json
  audit.json
  objects/instance_XXXX/
    control_audit.json
    controller_state.npz
    truth_audit.json
    truth_misses.npz
  demo/
    Demo.md
    overview.png
    objects/instance_XXXX_final.png
    frames/frame_XXXX.png
    classroom-oracle-3-demo.mp4   # when local codec support is available
```

The demo is post-hoc. Its four synchronized panels show trajectory/reference, saved binocular observation, evolving Cyclopean state, and final truth misses colored by first rejection rule.

## Interpretation

Oracle-3 does not repair the controller. Its purpose is to identify which stage makes the remaining reachable surface disappear from the action space. A subsequent Oracle-4 may change exactly one implicated rule and test that causal hypothesis.
