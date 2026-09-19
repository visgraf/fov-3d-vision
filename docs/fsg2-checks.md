# FSG2 Increment-2 Chat-side checks

Chat prepared this handoff against the current repository interfaces visible on 2026-09-19. The repository could not be cloned in the Chat execution container because DNS/network access to GitHub was unavailable; relevant current source interfaces were inspected separately before authoring.

Executed locally on the handoff files:

- `python3 -m py_compile` on all five new Python files: PASS.
- `tools/dev/check_fsg2.py --self-test` with a minimal `fsg_scene` dependency stub: 4 passed, 0 failed.
- `tools/fsg2_surface_map.py` analytic overlap test: matched 658, new 842, duplicate replay idempotent.
- Negative `shift`: exit 1 as intended.
- Negative `instance`: exit 1 as intended.
- Negative `duplicate`: exit 1 as intended.

These are software checks, not Blender or scientific measurements. No Cycles render, current-checkout integration run, or real FSG1 stereo inference was possible in Chat's container. Code must run the repository regression suites and the prescribed workstation experiment.

Known deliberate limitations:
- The object is a single planar surface; same-object folds/self-occlusions are deferred.
- Fusion uses exact calibrated poses; no registration is estimated.
- Surfel normals are not yet used for association.
- The 12 mm proximity rule is a prospectively fixed engineering baseline, not a calibrated uncertainty model.
- The reported completeness grid samples only the known finite test object and is evaluation-only.
