# MultiObject-1b checks

The pure checker enforces six design invariants:

1. object 141 remains read-only;
2. only id 143 enters the growing object-143 map;
3. FSG6f is reused through a label adapter rather than copied or retuned;
4. active-growth history starts at the MultiObject-1a seed;
5. empty id-143 looks are valid negative evidence rather than runtime errors;
6. automatic discovery and numerical quality gates remain absent.

Expected positive output:

```text
[multiobject1b-growth] PASS object141_read_only=true object143_only=true frozen_fsg6f=true seed_scoped_history=true empty_evidence=true
[multiobject1b-policy] PASS parent=multiobject1a independent_growth=true auto_discovery=false quality_gated=false
[multiobject1b-check] SUMMARY passed=6 failed=0
```

The six negative controls are genuine source mutations and must exit 1 because the checker detects them:

```text
object1grow
crossfuse
copypolicy
priorhistory
emptyabort
autodiscover
```

Exit 2 means a mutation escaped detection and is a checker defect.
