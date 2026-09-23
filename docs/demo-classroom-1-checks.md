# Demo-Classroom-1 checks — oracle-attention mode

Prospective source checks must establish:

1. Classroom is still bound to `scenes/classroom/classroom_eye.blend` and baseline `cafad30`.
2. Blender assistance is explicit and truth is allowed before/during control.
3. **All Classroom attention is oracle-driven** (`ORACLE_REFERENCE_SUPPORT`).
4. No `local_next_action`/FSG6f controller path is required by the demo.
5. Metric foreground xyz remains a filtered subset of established stereo xyz; reference depth may reject but never replace.
6. The real Classroom foveated-pair/stereo path is reused.
7. Preflight remains mandatory.
8. Foreground/background decomposition is adaptive and deterministic, with exactly one special background object.
9. The run is bounded by 24 fixations per foreground object and 256 total; these are engineering limits, not completion claims.
10. Discovery, autonomous attention, FSG6f mesh-scene generalization, and autonomous background decomposition are explicitly not claimed.
11. Foreground-only, background, reference, composite, timeline and movie/report products remain required.

Expected prospective output:

```text
[demo-classroom1-contract] PASS oracle_explicit=true oracle_all_attention=true foreground_truth_not_fused=true
[demo-classroom1-scene] PASS classroom_blend=true preflight=true adaptive_background=true single_background=true
[demo-classroom1-scope] PASS no_local_controller=true bounded_demo=true nonclaims=true
[demo-classroom1-check] SUMMARY passed=13 failed=0
```

All prescribed mutation controls must exit 1; an unknown mutation must exit 2.

For the live run, the report must additionally prove:

- accepted foreground points are row-subsets of stereo output;
- no reference xyz is fused;
- every fixation has action source `ORACLE_SEED` or `ORACLE_UNCOVERED_SUPPORT`;
- oracle-attention fixation count equals total fixation count;
- local FSG attention action count is zero;
- background points are excluded from foreground geometry/error counts;
- pre-Classroom source remains unchanged.
