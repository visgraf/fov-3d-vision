"""Repository seam for Demo-Classroom-1, oracle-attention mode.

This is deliberately a concept demo rather than a controller experiment.
Blender truth may guide object grouping, ALL gaze choices, and rejection.
The hard boundary is unchanged: evaluator/reference xyz/depth must never be
inserted as metric foreground reconstruction.

Only new Demo-Classroom-1 files may be changed to bind this seam unless a
new genuine blocker is reported first.
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
        """Verify the live Classroom binding and acquisition/reference paths.

        This includes the .blend hash, metric EYE convention, renderability,
        dynamic grouping support, established Classroom foveated-pair renderer,
        stereo-field conversion, and reference-panorama path.  The previously
        reported lack of an FSG6f/.blend controller bridge is NOT a blocker in
        this mode because Classroom attention is explicitly oracle-driven.
        """
        raise NotImplementedError

    def build_reference_and_guidance(self, preflight: dict[str, Any]) -> dict[str, Any]:
        """Build 2048x1024 reference RGB/depth/instance and oracle metadata.

        Truth is intentionally available before control in Demo Mode. Object
        identities/groups must be derived dynamically from the live .blend and
        the exact grouping rule must be recorded.
        """
        raise NotImplementedError

    def build_scene_plan(self, guidance: dict[str, Any]) -> dict[str, Any]:
        """Partition visible support into foreground entities + ONE background.

        Preferred rule: occupied reference-depth q70..q90 defines a soft far
        band; sufficiently supported nearer structural groups are explicit
        foreground targets; far/contextual support and otherwise-unassigned
        visible support are aggregated into __BACKGROUND__. Do not hand-pick
        Classroom object names.
        """
        raise NotImplementedError

    def choose_oracle_seed_gaze(self, obj: DemoObject, guidance: dict[str, Any]) -> tuple[float, float]:
        """Choose a deterministic visible/deep-interior seed from reference support."""
        raise NotImplementedError

    def acquire_and_validate(self, obj: DemoObject, gaze_deg: tuple[float, float], global_step: int,
                             object_dir: Path, guidance: dict[str, Any]) -> dict[str, Any]:
        """Render one Classroom foveated stereo fixation and validate with truth.

        Reuse the established Classroom PairRenderer/foveated warp and stereo
        field. Convert valid target stereo samples to the FSG Patch convention,
        then apply the demo reference-depth gate. The returned record must prove
        accepted xyz is a pure row-subset/filter of stereo xyz and that no
        reference xyz was substituted.
        """
        raise NotImplementedError

    def initialize_or_fuse(self, obj: DemoObject, measurement: dict[str, Any], object_dir: Path,
                           existing_map: Path | None) -> dict[str, Any]:
        """Use established 12 mm surface-map initialize/fuse on accepted stereo xyz only."""
        raise NotImplementedError

    def oracle_uncovered_support(self, obj: DemoObject, guidance: dict[str, Any], current_map: Path | None,
                                 history: list[dict[str, Any]]) -> dict[str, Any]:
        """Drive ALL post-seed Classroom attention from reference support.

        Compare the target's reference angular support with support represented
        by the current stereo map, report demo coverage, and choose the next
        deterministic deepest/interior uncovered gaze. Use the completed
        Tabletop gaze-precondition lesson to skip oracle candidates whose frame
        cannot satisfy the established renderer's scene-occupancy precondition.

        Return at least:
          demo_target_satisfied: bool
          reference_coverage: float
          next_gaze_deg: [yaw,pitch] or None
          candidate/source diagnostics sufficient to audit why the gaze was chosen
        """
        raise NotImplementedError

    def finalize_foreground_object(self, obj: DemoObject, object_dir: Path, current_map: Path | None,
                                   history: list[dict[str, Any]], stop_reason: str) -> dict[str, Any]:
        raise NotImplementedError

    def build_background_scaffold(self, background_plan: dict[str, Any], guidance: dict[str, Any],
                                  out: Path) -> dict[str, Any]:
        """Export the ONE adaptive special background object.

        It may use Blender RGB/reference depth and trivial spherical/shell
        geometry. It must remain separate from foreground point counts, stereo
        depth-error metrics, and any claim of observer-inferred geometry.
        """
        raise NotImplementedError

    def export_demo(self, object_rows: list[dict[str, Any]], background_row: dict[str, Any],
                    guidance: dict[str, Any], fixation_history: list[dict[str, Any]], out: Path) -> dict[str, Any]:
        """Export foreground, background, composite, provenance, timeline, movie and report."""
        raise NotImplementedError
