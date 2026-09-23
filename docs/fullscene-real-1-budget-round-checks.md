# FullScene-REAL-1W checks

Run:

```bash
.venv/bin/python -m py_compile tools/fullscene_real1_budget_round_public.py tools/fullscene_real1_budget_round_repo.py tools/fullscene_real1_budget_round_run.py tools/fullscene_real1_budget_round_compare.py tools/dev/check_fullscene_real1_budget_round.py
.venv/bin/python tools/dev/check_fullscene_real1_budget_round.py
```

Expected:

```text
[real1-budget-round-contract] PASS dynamic_targets=true six_fixations=true one_block=true frozen_control=true
[real1-budget-round-integrity] PASS baseline_read_only=true handoff=false truth_after_seal=true score=false
[real1-budget-round-check] SUMMARY passed=9 failed=0
```

Mutation controls: `hardcode twelve secondblock policy handoff auditaction truth score baseline`; each must exit 1, never 0 or 2.
