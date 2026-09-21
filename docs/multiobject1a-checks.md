# MultiObject-1a checks

The package checks only the new structural claim:

- two distinct declared ids, 141 and 143;
- object 141 inherited read-only;
- one new seed fixation maximum for object 143;
- second-object seed derived from already acquired id-143 prediction evidence;
- separate geometry entities rather than cross-object fusion;
- no evaluator truth, automatic object discovery, or object-growth loop.

Expected positive output:

```text
[multiobject1a-scene] PASS object141_inherited=true object143_seeded=true separate_entities=true shared_cyclopean_chart=true
[multiobject1a-policy] PASS parent=cyclopean1g one_fixation_max=true prior_evidence_seed=true object_growth=false auto_discovery=false quality_gated=false
[multiobject1a-check] SUMMARY passed=6 failed=0
```

Genuine source-mutation negatives:

```text
sameid multiprobe merge truth autodiscover grow
```

Each must exit 1 because its mutation is detected.  Exit 2 means a mutation escaped detection and is a check failure.
