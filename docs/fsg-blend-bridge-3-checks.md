# FSG Blend Bridge-3 checks

Prospective checks for the analysis-only foreground-fattening audit.

Expected before execution:

```text
[fsg-bridge3-fattening] self-test PASS
[fsg-bridge3-check] SUMMARY passed=7 failed=0
```

The package is additive. It must not modify `tools/fsg_geometry.py`, `tools/fsg_stereo.py`, Bridge-2 outputs, or any controller/fusion source.

Runtime invariants:

- use the sealed Bridge-2 run `previews/fsg-bridge2/classroom-structured-seed2111/`;
- no new Blender acquisition;
- no new `tools/fsg_stereo.py` execution;
- truth remains evaluator-only;
- estimator geometry/validity remains byte-for-byte as already produced;
- `alpha >= 0.5` is a descriptive midpoint classification, not an estimator threshold.

The self-test builds a synthetic two-plane disparity map with a five-pixel foreground invasion and verifies that the audit recognizes capture extending beyond the old three-pixel guard.
