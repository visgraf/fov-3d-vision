# FullScene-REAL-1S checks

Run:

```bash
.venv/bin/python -m py_compile tools/fullscene_real1_seed_round_public.py tools/fullscene_real1_seed_round_repo.py tools/fullscene_real1_seed_round_run.py tools/fullscene_real1_seed_round_compare.py tools/dev/check_fullscene_real1_seed_round.py
.venv/bin/python tools/dev/check_fullscene_real1_seed_round.py
```

Expected:

```text
[real1-seed-round-contract] PASS dynamic_target=true one_ring=true eight_probes=true reuse_probe=true
[real1-seed-round-integrity] PASS baseline_read_only=true truth=false growth=false threshold=false
[real1-seed-round-check] SUMMARY passed=8 failed=0
```

Mutation controls: `hardcode secondring earlystop truth growth threshold baseline extraseed`; each must exit 1, never 0 or 2.
