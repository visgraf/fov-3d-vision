# FSG4 Chat-side checks

These checks are software/design checks performed before workstation Blender execution. They are not FSG4 scientific results.

The handoff adds a paired active-versus-fixed-scan experiment while leaving the closed FSG1/FSG2/FSG3 implementation untouched. The active host and policy contain no import of `fsg4_scene` and no `evaluation_only` access. The fixed scan is one public schedule shared by both opaque fixtures. Render seeds are keyed by fixture, MC seed, yaw and eye, deliberately excluding policy and step.

The new self-test is expected to report six passes: fixture geometry/design, mirrored frontier policy behavior, paired yaw-keyed rendering seeds, frozen scan/truth-free host, AUC arithmetic including early-stop padding, and the public comparison contract.

Four negative modes must exit 1: `frontier`, `scan`, `pairing`, and `auc`. They are designed to show that each new invariant is actually capable of failing.

The analytic fixture self-test computes angular interval coverage only to catch a broken or degenerate experimental design before rendering. Those numbers are estimates and must not be reported as measured Blender performance.
