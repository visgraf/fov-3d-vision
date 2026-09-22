"""Live-repository adapter for FullScene-REAL-1.

This file is the ONLY prediction/control repository-specific seam in REAL-1.
It must NOT import evaluator-side reality1_scene. A separate quarantined
subprocess, fullscene_real1_oracle_scaffold.py, is the sole pre-control module
allowed to inspect that truth-side scene specification, and it may emit only a
strict four-field enumeration sidecar.

Claude Code is expected to complete/adjust the observer methods against the live
repository while leaving all pre-REAL-1 sources frozen.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


@dataclass(frozen=True)
class BenchmarkObject:
    object_id: int
    seed_yaw_deg: float
    seed_pitch_deg: float
    label: str = ""


class RepositoryAdapter:
    """Narrow adapter from the generic REAL-1 state machine to this repository.

    Implementation rules:
    - acquisition is the established procedural fixture via scene_render_fix.py;
    - never load/claim an unrelated .blend scene;
    - never import evaluator-side reality1_scene in this observer process;
    - consume only the sanitized enumeration oracle for id + seed direction;
    - reuse existing renderer/stereo/surface-map/FSG6f/audit/handoff unchanged;
    - evaluator depth/geometry truth is unavailable to control methods;
    - checkpoints/results are written only below the REAL-1 output directory.
    """

    ORACLE_OBJECT_FIELDS = {"object_id", "seed_yaw_deg", "seed_pitch_deg", "label"}

    def __init__(self, repo_root: Path, fixture: str, out: Path, seed: int):
        self.repo_root = Path(repo_root).resolve()
        self.fixture = str(fixture)
        self.out = Path(out).resolve()
        self.seed = int(seed)

    # ---------- quarantined benchmark enumeration ----------

    def enumeration_scaffold(self) -> dict[str, Any]:
        """Run the truth-side sanitizer in a separate process and return its JSON.

        The helper may inspect exact procedural geometry internally, but this
        method accepts only the declared four object fields. Anything else is a
        structural failure before observer control begins.
        """
        sidecar = self.out / "preflight" / "enumeration_oracle.json"
        helper = self.repo_root / "tools" / "fullscene_real1_oracle_scaffold.py"
        subprocess.run(
            [
                sys.executable,
                str(helper),
                "--repo",
                str(self.repo_root),
                "--fixture",
                self.fixture,
                "--out",
                str(sidecar),
            ],
            cwd=self.repo_root,
            check=True,
        )
        rec = json.loads(sidecar.read_text())
        if rec.get("fixture") != self.fixture:
            raise AssertionError("enumeration oracle fixture mismatch")
        if set(rec.get("fields_exposed", [])) != self.ORACLE_OBJECT_FIELDS:
            raise AssertionError("enumeration oracle exposed-fields mismatch")
        rows = rec.get("objects")
        if not isinstance(rows, list) or not rows:
            raise AssertionError("enumeration oracle returned no objects")
        for row in rows:
            if not isinstance(row, dict) or set(row) != self.ORACLE_OBJECT_FIELDS:
                raise AssertionError(f"enumeration oracle row crossed whitelist: {row!r}")
        return rec

    @staticmethod
    def objects_from_scaffold(scaffold: dict[str, Any]) -> list[BenchmarkObject]:
        return [
            BenchmarkObject(
                object_id=int(r["object_id"]),
                seed_yaw_deg=float(r["seed_yaw_deg"]),
                seed_pitch_deg=float(r["seed_pitch_deg"]),
                label=str(r["label"]),
            )
            for r in scaffold["objects"]
        ]

    # ---------- existing observer machinery ----------

    def seed_object(self, obj: BenchmarkObject, global_step: int, object_dir: Path) -> dict[str, Any]:
        """Take exactly one seed fixation using obj's whitelisted oracle direction.

        Must use existing generic renderer/stereo and selected-object seed semantics.
        The renderer already binds to the procedural fixture; do not add a scene path.
        """
        raise NotImplementedError

    def grow_object(self, obj: BenchmarkObject, seed_record: dict[str, Any], global_step: int,
                    object_dir: Path) -> dict[str, Any]:
        """Run frozen local growth until no_frontier or object watchdog."""
        raise NotImplementedError

    def audit_object(self, obj: BenchmarkObject, object_record: dict[str, Any],
                     object_dir: Path) -> dict[str, Any]:
        """Run the established read-only epistemic audit on this object's own history."""
        raise NotImplementedError

    def maybe_one_handoff(self, obj: BenchmarkObject, object_record: dict[str, Any],
                          audit_record: dict[str, Any], global_step: int,
                          object_dir: Path) -> dict[str, Any] | None:
        """Optionally execute the one established bounded epistemic handoff.

        Only when termination==no_frontier and exterior NEVER_OBSERVED>0.
        At most one handoff fixation and at most one returned local action. No recursive handoff.
        """
        raise NotImplementedError

    def finalize_object(self, obj: BenchmarkObject, object_record: dict[str, Any],
                        audit_record: dict[str, Any], handoff_record: dict[str, Any] | None,
                        object_dir: Path) -> dict[str, Any]:
        """Freeze final object map/status and return one scene-inventory row."""
        raise NotImplementedError

    # ---------- exports from observer state (truth still quarantined) ----------

    def export_observer_scene(self, object_rows: list[dict[str, Any]], scene_dir: Path) -> dict[str, Any]:
        """Export combined NPZ/PLY and sparse spherical depth/instance panoramas."""
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
