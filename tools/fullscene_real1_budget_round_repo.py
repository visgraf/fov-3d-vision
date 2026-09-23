"""Live-repository seam for one extra watchdog-continuation round.

Claude Code may complete this NEW file only. The completed REAL-1 baseline and
all established mechanisms remain frozen/read-only.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
class BudgetRoundRepository:
    def __init__(self, repo:Path, baseline_out:Path, out:Path, seed:int):
        self.repo=Path(repo).resolve(); self.baseline_out=Path(baseline_out).resolve(); self.out=Path(out).resolve(); self.seed=int(seed)
    def load_baseline(self)->dict[str,Any]:
        raise NotImplementedError
    def replay_and_continue(self, target_row:dict[str,Any], max_fresh_fixations:int, first_global_step:int, object_dir:Path)->dict[str,Any]:
        """Replay saved final policy exactly, then execute at most max_fresh_fixations frozen local actions.

        Stop early only if frozen FSG6f reaches its own scientific stop. No handoff,
        no new threshold, no re-seed, and no reference/evaluator access.
        """
        raise NotImplementedError
    def audit_after_round(self, target_row:dict[str,Any], continuation:dict[str,Any], object_dir:Path)->dict[str,Any]:
        """Run established read-only epistemic audit after the continuation block."""
        raise NotImplementedError
    def evaluate_after_seal(self, results:list[dict[str,Any]], seal_path:Path, eval_dir:Path)->dict[str,Any]:
        """After seal only, compare baseline-vs-continued observer products to immutable REAL-1 reference arrays."""
        raise NotImplementedError
