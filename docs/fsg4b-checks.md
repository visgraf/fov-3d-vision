# FSG4b Chat-side checks

These are software/orchestration checks only; no Blender/Cycles policy comparison was run here.

The FSG4a report established that repeated seeded OptiX rendering is not bit-reproducible at the float32 RGB level, so FSG4b preserves the original exact paired-observation requirement by reusing the already-rendered active acquisition artifact when the fixed scan visits the same yaw. There is no RGB tolerance and no change to `fsg4_public.py` or its scientific contract.

Chat-side checks performed on the supplied FSG4 source plus available frozen dependencies:

- `py_compile` passed for the modified `fsg4_run.py`, `fsg4_pair.py` and `check_fsg4.py`;
- `check_fsg4.py --self-test`: **7 passed, 0 failed**;
- exact-reuse test: source and cloned `observation.npz` bytes were identical, logical primary samples were preserved, newly rendered samples were zero, step-local metadata was rewritten, and the original exact shared-view verifier passed;
- the truth-free-host guard still verifies that `fsg4_run.py` imports no `fsg4_scene` and contains no `evaluation_only` access;
- all four negatives exit 1: frontier, scan, exact-pairing mutation, and no-AUC-advantage;
- no Blender or GPU execution was performed here.

The stopped FSG4a smoke and all earlier records must remain preserved. FSG4b uses new `previews/fsg4b/...` output paths.
