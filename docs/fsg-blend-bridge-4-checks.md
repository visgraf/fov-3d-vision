# FSG Blend Bridge-4 checks

Prospective package checks:

```text
[fsg-bridge4-synthetic] self-test PASS
[fsg-bridge4-analyze] self-test PASS
[fsg-bridge4-check] SUMMARY passed=16 failed=0
```

The checker verifies:

- analytic two-plane acquisition, no Blender;
- near depth fixed at 1.40 m;
- seven predeclared far depths;
- three fixed texture repeats;
- baseline-projected tangent frame;
- evaluator truth quarantined;
- no SGBM implementation in Bridge-4 tools;
- geometric midpoint capture definition (`alpha >= 0.5`);
- explicit same-row/no-near-row probe;
- established FSG matcher constants remain `blockSize=5`, LR tolerance `1.0 px`, instance guard `3 px`, and `SGBM_3WAY`;
- no subprocess/shell path hidden inside the analysis tools.

Runtime controls required by the Code prompt:

- branch descends from `fd14943` (`BRIDGE3_COMPLETE`);
- established FSG/Bridge-1R/2/3 source unchanged from that ancestor;
- generated instance-mask hashes identical across all 21 conditions;
- no `stereo/` directory exists before the frozen matcher loop;
- truth is never placed in `observation.npz`;
- all 21 conditions run the same unchanged `tools/fsg_stereo.py`;
- analysis runs only after all stereo results are sealed;
- no estimator output is modified by the analyzer.
