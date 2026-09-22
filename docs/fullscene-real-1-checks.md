# FullScene-REAL-1 repaired-binding checks

The repaired prospective checker verifies the blocker decision before any
scientific run:

1. REAL-1 takes `--fixture`, not `--scene`; no `.blend` input is claimed.
2. provenance records fixture name, evaluator scene-spec truth digest and the
   sanitized enumeration sidecar hash.
3. object IDs remain dynamic.
4. only `fullscene_real1_oracle_scaffold.py` may import the evaluator-side
   procedural scene specification before observer control.
5. the sidecar whitelist is exactly `object_id`, `seed_yaw_deg`,
   `seed_pitch_deg`, `label`.
6. fresh reconstruction, frozen local machinery, 12 mm association and the
   24-fixation object guard remain in force.
7. bounded one-handoff semantics remain in force.
8. observer state is sealed before full evaluator reference products.
9. observer/reference/evaluation outputs and resume remain required.
10. no single quality/completeness score is introduced.

Run:

```bash
python tools/dev/check_fullscene_real1.py
```

Mutation controls expected to exit 1:

`blend_input false_provenance hardcode oracle_import oracle_leak truth_early recursive reuse_maps touch_main score noresume noexports`

An unknown mutation must exit 2.
