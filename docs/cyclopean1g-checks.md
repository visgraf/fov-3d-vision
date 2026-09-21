# Cyclopean-1g checks

The pure structural suite must print:

```text
[cyclopean1g-measurement] PASS internal_no_depth_only=true centroid_recentering=true one_probe=true binary_outcome=true branch_closes=true
[cyclopean1g-policy] PASS parent=cyclopean1f seed2111_only=true frozen_stereo=true frozen_vergence=true quality_gated=false next=multi_object
[cyclopean1g-check] SUMMARY passed=6 failed=0
```

Six deliberate source-mutation negatives must each exit 1 because the mutation is actually detected:

- `external` — allow an exterior component instead of the internal no-depth residue;
- `unseen` — switch the candidate state back to `NEVER_OBSERVED`;
- `multiprobe` — allow two added fixations;
- `quality` — turn recovered depth into a numerical PASS gate;
- `rescueloop` — continue rescue measurements after this one probe;
- `truth` — permit evaluator truth.

These restore genuine mutation-based negative controls after the weaker declaration-only negatives observed in Cyclopean-1f.

Runtime structural expectations:

- exactly one completed Cyclopean-1f parent, seed 2111;
- parent reached `NO_ELIGIBLE_EXTERIOR_NEVER_OBSERVED`;
- final parent rebuild contains the established no-depth residue;
- selected cell belongs to `INTERNAL + OBSERVED_TARGET_NO_DEPTH` and is not a revisit;
- exactly one Blender fixation is added and no parent fixation rerendered;
- the outcome is one of `DEPTH_RECOVERED` or `DEPTH_STILL_ABSENT`;
- the experiment stops after that one look regardless of outcome;
- no evaluator truth is opened;
- parent hashes are unchanged;
- any fused target patch is target-pure and replay-idempotent.
