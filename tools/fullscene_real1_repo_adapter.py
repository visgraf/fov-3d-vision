"""Live-repository adapter for FullScene-REAL-1.

This file is the ONLY intentionally repository-specific seam in REAL-1.
Claude Code is expected to complete/adjust these methods against the live
repository while leaving all pre-REAL-1 sources frozen.

The orchestration contract lives in fullscene_real1_run.py; policy, stereo,
fusion, audit, and handoff semantics must be imported/reused from established
modules rather than reimplemented here.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class BenchmarkObject:
    object_id: int
    seed_yaw_deg: float
    seed_pitch_deg: float
    label: str = ""
    oracle_visible: bool | None = None


class RepositoryAdapter:
    """Narrow adapter from the generic REAL-1 state machine to this repository.

    Implementation rules:
    - dynamically inspect the supplied Blender scene; never hard-code scene ids;
    - reuse existing scene_render_fix.py, stereo, surface-map, FSG6f adapter,
      epistemic-audit and handoff helpers unchanged;
    - evaluator depth/geometry truth is unavailable to control methods;
    - checkpoints/results are written only below the REAL-1 output directory.
    """

    def __init__(self, repo_root: Path, scene: Path, out: Path, seed: int):
        self.repo_root = Path(repo_root).resolve()
        self.scene = Path(scene).resolve()
        self.out = Path(out).resolve()
        self.seed = int(seed)

    # ---------- benchmark enumeration / seed scaffolding ----------

    def enumerate_benchmark_objects(self) -> list[BenchmarkObject]:
        """Return every positive benchmark instance object in deterministic order.

        Allowed oracle use: Blender instance/pass-index identity and object/bounds
        direction may be used so REAL-1 attempts every benchmark object.  Do not
        expose evaluator depth, exact surface geometry, normals, or coverage to the
        observer/control loop.
        """
        raise NotImplementedError("Complete against the live Blender scene/repository")

    # ---------- existing observer machinery ----------

    def seed_object(self, obj: BenchmarkObject, global_step: int, object_dir: Path) -> dict[str, Any]:
        """Take exactly one seed fixation and create a pure selected-object patch.

        Must use the existing generic renderer/stereo front end and existing seed
        semantics. Return a JSON-serializable record including visible target
        pixels, valid target depth count, recovery fraction, empty/usable status,
        saved acquisition paths, and seed geometry path(s).
        """
        raise NotImplementedError

    def grow_object(self, obj: BenchmarkObject, seed_record: dict[str, Any], global_step: int,
                    object_dir: Path) -> dict[str, Any]:
        """Run frozen local growth from the seed until no_frontier or object watchdog.

        Reuse multiobject2c_policy/FSG6f, 12 mm association, generic renderer,
        object-scoped 24-fixation watchdog, and inherited empty-look semantics.
        Return final map path, policy trace, fixation records, termination reason,
        final global step and all ledgers needed for later analysis.
        """
        raise NotImplementedError

    def audit_object(self, obj: BenchmarkObject, object_record: dict[str, Any],
                     object_dir: Path) -> dict[str, Any]:
        """Run the established read-only epistemic audit on this object's own history."""
        raise NotImplementedError

    def maybe_one_handoff(self, obj: BenchmarkObject, object_record: dict[str, Any],
                          audit_record: dict[str, Any], global_step: int,
                          object_dir: Path) -> dict[str, Any] | None:
        """Optionally execute the one established bounded epistemic handoff.

        It is permitted only when:
          termination == no_frontier AND exterior NEVER_OBSERVED > 0.
        At most one cyclopean handoff fixation and at most one returned local action
        may execute. No recursive handoff scheduling and no revisit loop.
        Return None when the condition does not hold.
        """
        raise NotImplementedError

    def finalize_object(self, obj: BenchmarkObject, object_record: dict[str, Any],
                        audit_record: dict[str, Any], handoff_record: dict[str, Any] | None,
                        object_dir: Path) -> dict[str, Any]:
        """Freeze final object map/status and return one scene-inventory row."""
        raise NotImplementedError

    # ---------- exports from observer state (truth still quarantined) ----------

    def export_observer_scene(self, object_rows: list[dict[str, Any]], scene_dir: Path) -> dict[str, Any]:
        """Export combined NPZ/PLY and sparse spherical depth/instance panoramas.

        Projection must be documented and use a nearest-range z-buffer. Reference
        RGB/depth are not allowed here. If surfel RGB is unavailable, do not invent
        photometric color; instance-colored visualization may be emitted separately.
        """
        raise NotImplementedError

    # ---------- evaluator-only phase; called strictly after observer seal ----------

    def render_reference_after_control(self, scene_dir: Path) -> dict[str, Any]:
        """Render evaluator RGB/depth/instance panorama after observer_complete seal."""
        raise NotImplementedError

    def evaluate_against_reference(self, object_rows: list[dict[str, Any]],
                                   observer_exports: dict[str, Any],
                                   reference_exports: dict[str, Any],
                                   scene_dir: Path) -> dict[str, Any]:
        """Compute inventory, coverage, depth-error, purity and efficiency metrics."""
        raise NotImplementedError
