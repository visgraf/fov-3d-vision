"""Live-repository seam for the one-round visible-seed recovery experiment.

Claude Code may complete this NEW file against the live repository. Existing
renderer, stereo, seed, fusion, FSG, audit, REAL-1 baseline, and evaluator
sources remain frozen.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any

class SeedRoundRepository:
    def __init__(self, repo: Path, baseline_out: Path, out: Path, seed: int):
        self.repo = Path(repo).resolve()
        self.baseline_out = Path(baseline_out).resolve()
        self.out = Path(out).resolve()
        self.seed = int(seed)

    def load_baseline(self) -> dict[str, Any]:
        """Return sealed REAL-1 manifest/status/fixation data; never mutate baseline files."""
        raise NotImplementedError

    def acquire_probe(self, target_row: dict[str, Any], gaze_deg: tuple[float, float],
                      global_step: int, probe_dir: Path) -> dict[str, Any]:
        """Render exactly one generic fixation and run the unchanged stereo front end.

        Return observer-side target visible-pixel and valid-depth counts plus
        enough saved evidence to materialize a selected-object seed from this
        SAME observation. Evaluator truth/reference data must not be read here.
        """
        raise NotImplementedError

    def materialize_seed_from_probe(self, target_row: dict[str, Any], probe: dict[str, Any],
                                    object_dir: Path) -> dict[str, Any]:
        """Apply established selected-object seed extraction/purity semantics to the winning probe."""
        raise NotImplementedError
