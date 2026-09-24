# Classroom-Oracle-1 smoke-gate repair

## Why the original gate failed

The first Classroom-Oracle-1 smoke run was mechanically healthy but the gate required exactly two objects and exactly four looks. The fixed seed scan selected instances 107 and 108. Instance 107 legitimately terminated as `seed_uninitializable`; instance 108 legitimately terminated as `attention_complete` after FSG6f and the Cyclopean audit found no remaining eligible frontier. Therefore neither object could legally produce a controller-selected second fixation.

The fixed four-look assertion was inconsistent with the experiment's preserved empty/seed termination semantics. Forcing a second look would have changed the controller rather than tested it.

## Repaired smoke contract

The smoke test is an integration gate, not a scientific subset of the Classroom result.

1. Always retain and run the first two oracle-visible instances in ascending instance-id order.
2. A legitimate one-look termination at the seed is accepted. In particular, `seed_uninitializable` and `attention_complete` are not failures.
3. If neither of the first two objects requests a second look, continue deterministically through the remaining oracle-visible instances in the same ascending instance-id order.
4. Stop the smoke probe as soon as at least two objects have been retained **and** one real controller-selected second fixation has been acquired.
5. Every post-seed look must have `action_source` equal to `fsg6f` or `cyclopean_epistemic`. Blender/oracle may never select a post-seed gaze.
6. If the entire visible set is exhausted and every object legitimately terminates at its seed, the smoke test records `PASS_NO_CONTROLLER_TRANSITION_REQUESTED` instead of inventing a fixation. This is a scene/controller outcome, not an implementation failure.
7. The full experiment remains unchanged: it attempts every oracle-visible instance with the inherited 24-fixation watchdog and the same FSG6f/Cyclopean controller.

The runner records the decision in `manifest.json` under `smoke_gate`, including the first two primary instance IDs, number of objects examined, whether a controller transition was actually exercised, and the final smoke status.

## What this repair does not change

This patch does **not** change the oracle matcher, binocular same-instance visibility rule, object set, seed scan, 12 mm fusion rule, FSG6f/Cyclopean decision rules, 24-look watchdog, SGBM range behavior, or the no-foreground/background-decomposition contract.
