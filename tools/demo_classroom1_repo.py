"""Repository seam for Demo-Classroom-1.

This is Demo Mode: Blender truth may guide attention, grouping and rejection.
The one hard boundary remains that evaluator/reference xyz/depth must never be
inserted as metric foreground reconstruction.

Claude Code should bind these methods to the live repository while changing
only new Demo-Classroom-1 files unless a genuine blocker is reported first.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DemoObject:
    object_id: int
    label: str
    source_group: str


class RepositoryAdapter:
    def __init__(self, repo_root: Path, out: Path, seed: int):
        self.repo_root = Path(repo_root).resolve()
        self.out = Path(out).resolve()
        self.seed = int(seed)

    def preflight_scene(self) -> dict[str, Any]:
        """Inspect the live Classroom blend before any demo acquisition.

        Verify the manifest binding, file hash, metric units, EYE/head camera,
        pose/convention, render engine viability, and the object/group structure
        that can support deterministic reference instance masks. Return
        {ready: bool, ...}. No established source may be edited to pass preflight.
        """
        raise NotImplementedError

    def build_reference_and_guidance(self, preflight: dict[str, Any]) -> dict[str, Any]:
        """Create 2048x1024 RGB/depth/instance reference and guidance metadata.

        This is intentionally truth-side and may happen before control. Prefer
        the established Classroom preview360/foveated rig conventions. Object
        identities/groups must be created dynamically from the live .blend and
        the exact grouping rule must be recorded.
        """
        raise NotImplementedError

    def build_scene_plan(self, guidance: dict[str, Any]) -> dict[str, Any]:
        """Partition visible scene support into foreground entities + one background.

        Preferred default: derive a scene-adaptive soft background range from
        occupied reference-depth quantiles (q70..q90), combine it with reference
        angular support, keep sufficiently supported nearer groups as foreground,
        and aggregate far/background-like support into ONE special background
        object. Do not hand-pick Classroom object names. Record the actual rule.

        Return at least:
          foreground_objects: [{object_id,label,source_group}, ...]
          background: {... special-object metadata ...}
          decomposition: {... exact deterministic rule and counts ...}
        """
        raise NotImplementedError

    def choose_oracle_seed_gaze(self, obj: DemoObject, guidance: dict[str, Any]) -> tuple[float, float]:
        """Choose a deterministic visible seed gaze from the object's reference mask."""
        raise NotImplementedError

    def acquire_and_validate(self, obj: DemoObject, gaze_deg: tuple[float, float], global_step: int,
                             object_dir: Path, guidance: dict[str, Any]) -> dict[str, Any]:
        """Render one Classroom foveated stereo fixation and validate stereo with truth.

        Reuse the established Classroom pair renderer/rig and stereo front end;
        adapt their output to the existing FSG accepted-point representation.
        Required record includes target-visible support, raw stereo count,
        accepted/rejected counts, raw/accepted depth error, acquisition paths,
        and direct proof accepted xyz is a row-subset/filter of stereo xyz.
        """
        raise NotImplementedError

    def initialize_or_fuse(self, obj: DemoObject, measurement: dict[str, Any], object_dir: Path,
                           existing_map: Path | None) -> dict[str, Any]:
        """Use established surface-map initialization/fusion on accepted stereo xyz only."""
        raise NotImplementedError

    def local_next_action(self, obj: DemoObject, object_dir: Path, history: list[dict[str, Any]],
                          current_map: Path) -> dict[str, Any]:
        """Use/replay the established local FSG controller; do not invent a Classroom controller."""
        raise NotImplementedError

    def oracle_uncovered_support(self, obj: DemoObject, guidance: dict[str, Any], current_map: Path | None,
                                 history: list[dict[str, Any]]) -> dict[str, Any]:
        """Measure uncovered reference angular support and propose one deterministic redirect gaze."""
        raise NotImplementedError

    def finalize_foreground_object(self, obj: DemoObject, object_dir: Path, current_map: Path | None,
                                   history: list[dict[str, Any]], stop_reason: str) -> dict[str, Any]:
        raise NotImplementedError

    def build_background_scaffold(self, background_plan: dict[str, Any], guidance: dict[str, Any],
                                  out: Path) -> dict[str, Any]:
        """Export the ONE adaptive special background object.

        It may use Blender RGB/reference depth and trivial spherical/shell geometry.
        It must be separate from foreground point counts, depth errors and purity.
        """
        raise NotImplementedError

    def export_demo(self, object_rows: list[dict[str, Any]], background_row: dict[str, Any],
                    guidance: dict[str, Any], fixation_history: list[dict[str, Any]], out: Path) -> dict[str, Any]:
        """Export foreground, special background, provenance-preserving composite, timeline and movie."""
        raise NotImplementedError
