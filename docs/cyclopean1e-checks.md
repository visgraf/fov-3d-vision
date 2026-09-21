# Cyclopean-1e checks

Run:

```bash
.venv/bin/python -m py_compile tools/cyclopean1e_public.py tools/cyclopean1e_gaze.py tools/cyclopean1e_probe.py tools/cyclopean1e_compare.py tools/dev/check_cyclopean1e.py
.venv/bin/python tools/dev/check_cyclopean1e.py
```

Expected pure lines:

```text
[cyclopean1e-gaze] PASS never_observed_only=true internal_excluded=true no_depth_excluded=true exterior_deepest=true revisit_fallback=true one_probe=true
[cyclopean1e-policy] PASS parent=cyclopean1d seed2111_only=true never_observed_only=true seen_no_depth_excluded=true one_fixation_max=true frozen_fsg6f=true quality_gated=false
[cyclopean1e-check] SUMMARY passed=6 failed=0
```

Every deliberate negative must exit 1:

```bash
for k in nodepth internal centroid multiprobe truth policy; do
  .venv/bin/python tools/dev/check_cyclopean1e.py --negative "$k"
done
```

The controls mean:

- `nodepth`: seen-target/no-depth shoreline must not become a gaze candidate;
- `internal`: an internal `NEVER_OBSERVED` cell is not this experiment's exterior-attention candidate;
- `centroid`: the selector is depth-driven, not a generic arc centroid rule;
- `multiprobe`: the public contract allows at most one new fixation;
- `truth`: evaluator truth is forbidden;
- `policy`: FSG6f policy/stopping machinery is forbidden.

Workstation execution is expected to run exactly one Blender fixation if an eligible exterior `NEVER_OBSERVED` cell exists.  The experiment is structural: no surfel gain, coverage or depth-change value is a PASS threshold.
