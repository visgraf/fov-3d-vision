# Cyclopean-1f checks

The pure checks enforce the intended minimal experiment:

- same Cyclopean-1e selection rule is reused;
- only EXTERIOR `NEVER_OBSERVED` is eligible;
- `OBSERVED_TARGET_NO_DEPTH` remains ineligible;
- scientific stop is absence of an eligible cell, not a quality threshold;
- total 24 fixations is an engineering watchdog only;
- no quality gate is introduced.

Expected positive lines:

```text
[cyclopean1f-loop] PASS repeated_rule=true never_observed_only=true exterior_only=true fixed_point=true watchdog_guardrail=true
[cyclopean1f-policy] PASS parent=cyclopean1e seed2111_only=true repeated_epistemic_gaze=true scientific_stop=no_eligible_never_observed watchdog_total=24 frozen_fsg6f=true quality_gated=false
[cyclopean1f-check] SUMMARY passed=6 failed=0
```

Deliberate negatives, each required to exit 1:

`nodepth`, `internal`, `threshold`, `quality`, `fixedlooks`, `policy`.
