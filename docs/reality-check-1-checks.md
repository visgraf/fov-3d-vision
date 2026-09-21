# Reality Check 1 — Chat-side checks

The package was syntax-checked in Chat's container.  Blender/Cycles and the workstation repository were not available there, so no scientific acquisition was performed.

Pure checks exercise the parts that do not require Blender:

- target angular extent is about 25.5° × 19.1°;
- target depth range is about 8.7 cm, so it is not a planar substitute;
- the target texture contains both a genuinely low-contrast region and a substantially more featureful region;
- the prediction runner imports the frozen `fsg6f_frontier` policy and does not import evaluator scene truth;
- FSG6f's six-look budget, stereo instrument and 12 mm fusion rule are inherited unchanged;
- evaluation explicitly remains descriptive rather than importing the previous calibration-quality gates.

Expected positive summary:

```text
[reality1-scene] PASS ...
[reality1-policy] PASS frozen_fsg6f=true quality_gated=false fixed_head=true static_scene=true
[reality1-check] SUMMARY passed=6 failed=0
```

Six deliberate negatives must each exit 1:

- `flat` — detects collapsing the target back to an almost planar surface;
- `uniformrich` — detects replacing the mixed texture with the old uniformly rich calibration style;
- `policycopy` — detects copying/reimplementing FSG6f;
- `truth` — detects evaluator truth entering prediction;
- `qualitygate` — detects turning the observational reality check into a post-hoc tuned PASS threshold;
- `budgetbump` — detects increasing the frozen FSG6f fixation budget.
