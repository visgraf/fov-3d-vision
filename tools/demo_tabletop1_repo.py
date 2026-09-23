"""Repository seam for Demo-Tabletop-1.

Unlike REAL-1 research runs, this DEMO seam is explicitly allowed to use evaluator
truth for guidance and rejection. It must still preserve one hard boundary:
reference depth/xyz may not be inserted as metric foreground reconstruction.

Claude Code should bind these methods to the live repository while changing only
new Demo-Tabletop-1 files unless a genuine blocker is reported first.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DemoObject:
    object_id: int
    label: str
    is_background: bool


class RepositoryAdapter:
    def __init__(self, repo_root: Path, out: Path, seed: int):
        self.repo_root = Path(repo_root).resolve()
        self.out = Path(out).resolve()
        self.seed = int(seed)

    def build_reference_and_guidance(self) -> dict[str, Any]:
        """Create reference RGB/depth/instance plus guidance metadata for tabletop_cloth.

        This is intentionally truth-side and happens before control in Demo Mode.
        The returned record must enumerate positive objects dynamically and expose
        enough information to choose visible seed/redirect gazes. Record provenance.
        """
        raise NotImplementedError

    def enumerate_objects(self, guidance: dict[str, Any]) -> list[DemoObject]:
        """Return deterministic positive objects; mark declared background labels."""
        raise NotImplementedError

    def choose_oracle_seed_gaze(self, obj: DemoObject, guidance: dict[str, Any]) -> tuple[float, float]:
        """Choose a visible seed direction from reference support, not object centre by fiat."""
        raise NotImplementedError

    def acquire_and_validate(self, obj: DemoObject, gaze_deg: tuple[float, float], global_step: int,
                             object_dir: Path, guidance: dict[str, Any]) -> dict[str, Any]:
        """Render one foveated binocular fixation, run established stereo, validate against truth.

        Required record: visible target pixels, raw valid stereo count, accepted/rejected
        counts, depth-error distribution for raw stereo, accepted geometry path, RGB paths,
        and proof that accepted xyz comes from stereo rather than reference depth.
        """
        raise NotImplementedError

    def initialize_or_fuse(self, obj: DemoObject, measurement: dict[str, Any], object_dir: Path,
                           existing_map: Path | None) -> dict[str, Any]:
        """Use established surface-map initialization/fusion on ACCEPTED stereo geometry only."""
        raise NotImplementedError

    def local_next_action(self, obj: DemoObject, object_dir: Path, history: list[dict[str, Any]],
                          current_map: Path) -> dict[str, Any]:
        """Replay/use established frozen local FSG policy; no new local controller here."""
        raise NotImplementedError

    def oracle_uncovered_support(self, obj: DemoObject, guidance: dict[str, Any], current_map: Path,
                                 history: list[dict[str, Any]]) -> dict[str, Any]:
        """Measure remaining reference angular support and propose one deterministic redirect gaze."""
        raise NotImplementedError

    def finalize_foreground_object(self, obj: DemoObject, object_dir: Path, current_map: Path | None,
                                   history: list[dict[str, Any]], stop_reason: str) -> dict[str, Any]:
        raise NotImplementedError

    def build_background_scaffold(self, obj: DemoObject, guidance: dict[str, Any], object_dir: Path) -> dict[str, Any]:
        """Build explicitly oracle-sourced visual background with soft depth metadata.

        It must be exported separately and must not enter foreground point counts or purity metrics.
        """
        raise NotImplementedError

    def export_demo(self, object_rows: list[dict[str, Any]], guidance: dict[str, Any],
                    fixation_history: list[dict[str, Any]], out: Path) -> dict[str, Any]:
        """Export observer foreground, oracle background, provenance-preserving composite and timeline."""
        raise NotImplementedError
