# FullScene-REAL-1 checks

## Prospective package checks

From the repository root after applying the package:

```bash
python tools/dev/check_fullscene_real1.py
```

Expected:

```text
[fullscene-real1-contract] PASS dynamic_ids=true fresh_run=true frozen_local=true bounded_handoff=true
[fullscene-real1-truth] PASS observer_sealed_before_evaluator=true separate_metrics=true
[fullscene-real1-products] PASS scene_geometry=true sparse_rgbd_depth=true reference=true evaluation=true resume=true
[fullscene-real1-check] SUMMARY passed=10 failed=0
```

Mutation controls — every command must exit `1`:

```bash
for m in hardcode truth_early recursive reuse_maps touch_main score noresume noexports; do
  python tools/dev/check_fullscene_real1.py --mutation "$m"
  test $? -eq 1 || exit 1
done
```

`py_compile` all new Python files before execution.

## Workstation integration checks

Before the real run, Code must verify:

1. current branch is exactly `fullscene-real-1`;
2. branch descends from `651a6cb`;
3. `main` and `fullscene-calibration-1` have not moved as a consequence of the
   REAL-1 work;
4. all pre-REAL-1 tracked non-documentation sources are byte-identical to the
   parent state;
5. all repository-specific implementation is confined to new
   `fullscene_real1_*` files;
6. object enumeration is dynamic — no literal scene object IDs such as
   `141..145` in REAL-1 source;
7. object order is deterministic and reported;
8. evaluator depth/geometry is not reachable from seed/growth/audit/handoff
   code paths;
9. the observer seal is written before reference/evaluation files are created;
10. resume skips completed objects without rerendering them.

## Runtime acceptance checks

A completed run must satisfy:

```bash
python tools/fullscene_real1_compare.py <REAL1_OUTPUT_DIRECTORY>
```

with exit code `0` and status `FULLSCENE_REAL1_COMPLETE`.

The comparator requires that every enumerated positive instance ID was
attempted and carries a final status, and that the observer/reference/evaluation
products exist.

## Scientific non-claims

Passing REAL-1 does **not** establish:

- autonomous object discovery;
- physical completeness of any object;
- scene completeness beyond the fixed-head visible benchmark inventory;
- that measurement residue is recoverable by another sensor action;
- that the chosen deterministic object order is optimal;
- a single scalar quality score for the scene.
