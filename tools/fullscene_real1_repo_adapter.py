"""Live-repository adapter for FullScene-REAL-1.

This file is the ONLY prediction/control repository-specific seam in REAL-1.
It must NOT import evaluator-side reality1_scene. A separate quarantined
subprocess, fullscene_real1_oracle_scaffold.py, is the sole pre-control module
allowed to inspect that truth-side scene specification, and it may emit only a
strict four-field enumeration sidecar.

Every observer mechanism below is composed from already-established sources and
none of them is modified here: the generic procedural acquisition renderer
(scene_render_fix.py), the current stereo front end (fsg_stereo_supported),
frozen FSG6f through the unchanged MultiObject-2c target-label adapter, the
frozen 12 mm FSG3 association, the established MultiObject-3d cyclopean audit
helpers, and the established Cyclopean-1e bounded epistemic probe.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

import numpy as np
from PIL import Image

import cyclopean1a_topology as topo1a
import cyclopean1b_boundary as boundary
import cyclopean1d_epistemic as epi
import cyclopean1e_gaze as epistemic_gaze
import fsg6f_public as frozen_public
import fsg6f_run as fsg6run
import fsg_stereo_hdr as hdr
import fullscene1d_run as inherited_status
import fullscene_real1_export as export
import fullscene_real1_public as public
import multiobject2c_policy as policy
import multiobject3d_audit as inherited_audit
from fsg3_surface_map import Patch, SurfaceMap, fuse, initialize, load_map, save_map
from fsg_stereo import support_mask
from fsg_stereo_supported import check_kernel_equivalence, compute_once
from reality1_run import _tone_preview

# The established lineage (FullScene-1b/1c and every Reality/MultiObject record)
# reports on the "full" profile; geometry and every check are identical between
# profiles, only spp and s0 differ.
PROFILE = "full"
RENDERER = "tools/scene_render_fix.py"
REFERENCE_TOOL = "tools/fullscene_real1_reference.py"


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
        self.blender = "blender"
        self.device = "OPTIX"
        self.blender_launches = 0
        self.render_seconds = 0.0
        self._live: dict[int, dict[str, Any]] = {}
        self._kernel_checked = False
        # Reuse the frozen rule itself rather than a REAL-1 copy of its numbers.
        self.fusion = dict(frozen_public.FUSION)
        if abs(float(self.fusion["association_radius_m"]) - float(public.ASSOCIATION_RADIUS_M)) > 1e-12:
            raise AssertionError("REAL-1 association radius disagrees with the frozen 12 mm rule")

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

    # ---------- shared acquisition plumbing ----------

    def _ensure_kernel(self) -> None:
        if not self._kernel_checked:
            check_kernel_equivalence()
            self._kernel_checked = True

    def _render(self, step: int, gaze: tuple[float, float], object_dir: Path) -> Path:
        """One physical fixation through the unchanged generic scene renderer.

        The renderer binds to the procedural fixture itself; REAL-1 passes no
        scene path and adds no renderer argument.
        """
        out = object_dir / "acquisition" / f"fix_{step:02d}"
        logs = object_dir / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        yaw, pitch = float(gaze[0]), float(gaze[1])
        cmd = [
            self.blender, "-b", "--python-exit-code", "1", "-P", RENDERER, "--",
            "--out", str(out), "--profile", PROFILE, "--seed", str(self.seed),
            "--step", str(step), "--yaw", f"{yaw:.12g}", "--pitch", f"{pitch:.12g}",
            "--device", self.device,
        ]
        t0 = time.perf_counter()
        p = subprocess.run(cmd, cwd=self.repo_root, text=True, capture_output=True)
        self.blender_launches += 1
        self.render_seconds += time.perf_counter() - t0
        (logs / f"render_{step:02d}.log").write_text(p.stdout + "\n--- STDERR ---\n" + p.stderr)
        if p.returncode != 0:
            raise RuntimeError(f"REAL-1 Blender fixation {step} failed; see {logs / f'render_{step:02d}.log'}")
        rr = json.loads((out / "run.json").read_text())
        if not rr.get("complete") or int(rr.get("seed", -1)) != self.seed or int(rr.get("step", -1)) != step:
            raise RuntimeError("incomplete or wrong REAL-1 Blender acquisition record")
        if rr.get("fixture") != self.fixture:
            raise RuntimeError(
                f"renderer fixture {rr.get('fixture')!r} is not the requested REAL-1 fixture {self.fixture!r}"
            )
        if abs(float(rr["yaw_deg"]) - yaw) > 1e-8 or abs(float(rr["pitch_deg"]) - pitch) > 1e-8:
            raise RuntimeError("Blender record gaze mismatch")
        return out / f"fix_{step:02d}"

    @staticmethod
    def _right_state(c: dict, rec: dict, state: dict) -> tuple[np.ndarray, np.ndarray]:
        x, y, cw, ch = map(int, rec["crop_xywh"])
        sl = np.s_[y:y + ch, x:x + cw]
        ids_R = np.asarray(state["ids_right"])[sl]
        raw_R = np.asarray(support_mask(c, rec, "R"), bool)[sl]
        if not np.array_equal(np.asarray(rec["instance_id"]), np.asarray(state["ids_left"])[sl]):
            raise AssertionError("left rectified ID replay mismatch")
        return ids_R, raw_R

    @staticmethod
    def _patch(pid: str, rec: dict, target_id: int) -> Patch:
        mask = np.asarray(rec["valid"], bool) & (np.asarray(rec["instance_id"]) == int(target_id))
        return Patch(
            pid,
            np.asarray(rec["xyz_h"])[mask],
            np.asarray(rec["rgb_left"])[mask],
            np.asarray(rec["instance_id"])[mask],
        )

    @staticmethod
    def _look_stats(rec: dict, target_id: int) -> dict[str, Any]:
        ids = np.asarray(rec["instance_id"])
        valid = np.asarray(rec["valid"], bool)
        visible = int((ids == int(target_id)).sum())
        measured = int((valid & (ids == int(target_id))).sum())
        return {
            "target_visible_pixels": visible,
            "target_valid_depth_points": measured,
            "target_depth_recovery_fraction": (float(measured / visible) if visible else None),
            "frame_valid_pixels": int(valid.sum()),
            "frame_pixels": int(valid.size),
            "frame_valid_fraction": float(valid.mean()),
        }

    def _acquire(self, target_id: int, step: int, gaze: tuple[float, float],
                 object_dir: Path, pid: str) -> tuple[Path, dict, Patch, dict]:
        case = self._render(step, gaze, object_dir)
        c, obs = hdr.read_observation(case)
        rec, _meta, state = compute_once(c, obs)
        ids_R, raw_R = self._right_state(c, rec, state)
        patch = self._patch(pid, rec, target_id)
        if len(patch.instance_id) and set(np.unique(patch.instance_id).tolist()) != {int(target_id)}:
            raise AssertionError("acquisition patch is not pure for the benchmark object")
        rgb_dir = object_dir / "rgb"
        rgb_dir.mkdir(parents=True, exist_ok=True)
        Image.fromarray(_tone_preview(rec["rgb_left"])).save(rgb_dir / f"{pid}.png")
        ctx = {"calibration": c, "rec": rec, "ids_R": ids_R, "raw_R": raw_R, "case": case}
        return case, ctx, patch, self._look_stats(rec, target_id)

    @staticmethod
    def _fixation_record(target_id: int, step: int, index: int, phase: str,
                         gaze: tuple[float, float], stats: dict, points: int,
                         empty: bool, fused: bool) -> dict[str, Any]:
        return {
            "object_id": int(target_id),
            "global_step": int(step),
            "object_fixation_index": int(index),
            "phase": phase,
            "yaw_deg": float(gaze[0]),
            "pitch_deg": float(gaze[1]),
            "target_points": int(points),
            "empty_look": bool(empty),
            "fused": bool(fused),
            **stats,
        }

    # ---------- existing observer machinery ----------

    def seed_object(self, obj: BenchmarkObject, global_step: int, object_dir: Path) -> dict[str, Any]:
        """Take exactly one seed fixation using obj's whitelisted oracle direction.

        Must use existing generic renderer/stereo and selected-object seed semantics.
        The renderer already binds to the procedural fixture; do not add a scene path.
        """
        self._ensure_kernel()
        oid = int(obj.object_id)
        step = int(global_step)
        gaze = (float(obj.seed_yaw_deg), float(obj.seed_pitch_deg))
        pid = f"fix_{step:02d}"
        _case, ctx, patch, stats = self._acquire(oid, step, gaze, object_dir, pid)

        points = int(len(patch.xyz_h))
        # The frozen FSG3 initialize() itself refuses fewer than 100 object
        # points, which is the same limit as the inherited empty-look rule. No
        # new threshold is introduced here.
        usable = bool(points >= int(public.EMPTY_TARGET_VALID_LIMIT))

        patches = object_dir / "patches"
        patches.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            patches / f"{pid}.npz",
            xyz_h=np.asarray(patch.xyz_h, np.float32),
            rgb=np.asarray(patch.rgb, np.float32),
            instance_id=np.asarray(patch.instance_id),
            valid=np.asarray(ctx["rec"]["valid"], bool),
            oracle_instance_id=np.asarray(ctx["rec"]["instance_id"]),
            raw_support_L=np.asarray(ctx["rec"]["raw_support_L"], bool),
            oracle_instance_id_R=np.asarray(ctx["ids_R"]),
            raw_support_R=np.asarray(ctx["raw_R"], bool),
        )

        live: dict[str, Any] = {
            "object_id": oid,
            "gazes": [gaze],
            "steps": [step],
            "cases": [Path(ctx["case"])],
            "last_ctx": ctx,
            "map": None,
            "object_dir": object_dir,
        }
        if usable:
            live["map"] = initialize(patch, oid)
        self._live[oid] = live

        return {
            "object_id": oid,
            "label": str(obj.label),
            "global_step": step,
            "next_global_step": step + 1,
            "gaze_deg": [gaze[0], gaze[1]],
            "seed_usable": usable,
            "valid_target_points": points,
            "seed_map_points": int(len(live["map"].xyz_h)) if usable else 0,
            "patch_pure": True,
            "min_seed_points_rule": int(public.EMPTY_TARGET_VALID_LIMIT),
            "case": str(Path(ctx["case"]).relative_to(self.out)) if str(ctx["case"]).startswith(str(self.out)) else str(ctx["case"]),
            **stats,
            "fixation_records": [
                self._fixation_record(oid, step, 0, "seed", gaze, stats, points, not usable, usable)
            ],
        }

    def grow_object(self, obj: BenchmarkObject, seed_record: dict[str, Any], global_step: int,
                    object_dir: Path) -> dict[str, Any]:
        """Run frozen local growth until no_frontier or object watchdog."""
        self._ensure_kernel()
        oid = int(obj.object_id)
        live = self._live[oid]
        sm = live["map"]
        if sm is None:
            raise AssertionError("grow_object called without a usable seed map")
        gazes: list[tuple[float, float]] = live["gazes"]
        ctx = live["last_ctx"]
        c, rec, ids_R, raw_R = ctx["calibration"], ctx["rec"], ctx["ids_R"], ctx["raw_R"]

        maps_dir = object_dir / "maps"
        maps_dir.mkdir(parents=True, exist_ok=True)
        save_map(maps_dir / f"map_{live['steps'][0]:02d}.npz", sm)

        history = [policy.history_entry(c, rec["instance_id"], rec["raw_support_L"], ids_R, raw_R, oid)]
        snapshots = [sm.xyz_h.copy()]
        supports = [sm.support_count.copy()]
        association_stats: list[dict[str, Any]] = [{
            "global_step": int(live["steps"][0]),
            "object_fixation_index": 0,
            "input_points": int(len(sm.xyz_h)),
            "matched": 0,
            "new": int(len(sm.xyz_h)),
            "empty_look": False,
            "idempotent_replay": True,
        }]
        fixations: list[dict[str, Any]] = []
        empty_steps: list[int] = []
        policy_trace: list[dict[str, Any]] = []

        decision = policy.choose_next(
            gazes[-1][0], gazes[-1][1], c,
            rec["instance_id"], rec["raw_support_L"], ids_R, raw_R,
            sm.xyz_h, gazes, history, oid,
        )
        decision["object_fixation_index"] = 0
        decision["global_step"] = int(live["steps"][0])
        policy_trace.append(decision)

        step = int(global_step)
        termination: str | None = None
        t0 = time.perf_counter()
        while True:
            if decision.get("stop"):
                termination = str(decision.get("reason", "policy_stop"))
                break
            if len(gazes) >= int(public.OBJECT_WATCHDOG_FIXATIONS):
                termination = "object_watchdog"
                break
            gaze = tuple(map(float, decision["next_gaze_deg"]))
            if any(np.allclose(np.asarray(g), np.asarray(gaze), atol=1e-9) for g in gazes):
                raise AssertionError("local policy revisited an existing fixation")
            pid = f"fix_{step:02d}"
            _case, ctx, patch, stats = self._acquire(oid, step, gaze, object_dir, pid)
            c, rec, ids_R, raw_R = ctx["calibration"], ctx["rec"], ctx["ids_R"], ctx["raw_R"]
            np.savez_compressed(
                object_dir / "patches" / f"{pid}.npz",
                xyz_h=np.asarray(patch.xyz_h, np.float32),
                rgb=np.asarray(patch.rgb, np.float32),
                instance_id=np.asarray(patch.instance_id),
                valid=np.asarray(rec["valid"], bool),
                oracle_instance_id=np.asarray(rec["instance_id"]),
                raw_support_L=np.asarray(rec["raw_support_L"], bool),
                oracle_instance_id_R=np.asarray(ids_R),
                raw_support_R=np.asarray(raw_R, bool),
            )
            sm, assoc, empty, idem = self._fuse_look(sm, patch, oid)
            if empty:
                empty_steps.append(step)
            save_map(maps_dir / f"map_{step:02d}.npz", sm)

            gazes.append(gaze)
            live["steps"].append(step)
            live["cases"].append(Path(ctx["case"]))
            snapshots.append(sm.xyz_h.copy())
            supports.append(sm.support_count.copy())
            history.append(policy.history_entry(c, rec["instance_id"], rec["raw_support_L"], ids_R, raw_R, oid))
            dist = np.asarray(assoc.get("distances_m", np.empty(0)))
            association_stats.append({
                "global_step": step,
                "object_fixation_index": len(gazes) - 1,
                "input_points": int(len(patch.xyz_h)),
                "matched": int(assoc.get("matched", 0)),
                "new": int(assoc.get("new", 0)),
                "empty_look": bool(empty),
                "overlap_median_distance_m": float(np.median(dist)) if len(dist) else None,
                "overlap_p95_distance_m": float(np.percentile(dist, 95)) if len(dist) else None,
                "idempotent_replay": bool(idem),
            })
            fixations.append(self._fixation_record(
                oid, step, len(gazes) - 1, "growth", gaze, stats, int(len(patch.xyz_h)), empty, not empty
            ))
            decision = policy.choose_next(
                gaze[0], gaze[1], c,
                rec["instance_id"], rec["raw_support_L"], ids_R, raw_R,
                sm.xyz_h, gazes, history, oid,
            )
            decision["object_fixation_index"] = len(gazes) - 1
            decision["global_step"] = step
            policy_trace.append(decision)
            step += 1

        live["map"] = sm
        live["last_ctx"] = ctx
        live["history"] = history
        live["policy_trace"] = policy_trace
        if len(sm.instance_id) and set(np.unique(sm.instance_id).tolist()) != {oid}:
            raise AssertionError("final local map is not pure for the benchmark object")
        fsg6run.write_growth(object_dir / f"object_{oid}_growth.png", snapshots, supports, gazes)

        return {
            "object_id": oid,
            "termination_reason": termination,
            "scientific_stop_reached": bool(termination != "object_watchdog" and policy_trace[-1].get("stop")),
            "watchdog_object_fixations": int(public.OBJECT_WATCHDOG_FIXATIONS),
            "object_fixations_total": int(len(gazes)),
            "added_fixations": int(len(gazes) - 1),
            "map_points": int(len(sm.xyz_h)),
            "empty_steps": empty_steps,
            "gazes_deg": [[float(g[0]), float(g[1])] for g in gazes],
            "association_stats": association_stats,
            "policy_trace": policy_trace,
            "final_policy_decision": policy_trace[-1],
            "fusion_matched_total": int(sum(int(r.get("matched", 0)) for r in association_stats[1:])),
            "fusion_new_total": int(sum(int(r.get("new", 0)) for r in association_stats[1:])),
            "next_global_step": step,
            "loop_wall_seconds": float(time.perf_counter() - t0),
            "fixation_records": fixations,
        }

    def _fuse_look(self, sm, patch, target_id: int):
        """Inherited empty-look semantics plus the frozen 12 mm idempotent fusion."""
        empty = len(patch.xyz_h) < int(public.EMPTY_TARGET_VALID_LIMIT)
        if empty:
            return sm, {
                "input_points": int(len(patch.xyz_h)), "matched": 0, "new": 0,
                "affected_surfels": 0, "distances_m": np.empty(0), "duplicate_patch": False,
            }, True, True
        after, assoc = fuse(
            sm, patch, int(target_id),
            self.fusion["association_radius_m"], self.fusion["hash_cell_m"],
        )
        replay, dup = fuse(
            after, patch, int(target_id),
            self.fusion["association_radius_m"], self.fusion["hash_cell_m"],
        )
        idem = bool(
            dup["duplicate_patch"]
            and np.array_equal(after.xyz_h, replay.xyz_h)
            and np.array_equal(after.support_count, replay.support_count)
            and np.array_equal(after.provenance_mask, replay.provenance_mask)
        )
        if not idem:
            raise AssertionError("patch replay is not idempotent")
        if len(after.instance_id) and set(np.unique(after.instance_id).tolist()) != {int(target_id)}:
            raise AssertionError("cross-object contamination entered the local map")
        return after, assoc, False, True

    def audit_object(self, obj: BenchmarkObject, object_record: dict[str, Any],
                     object_dir: Path) -> dict[str, Any]:
        """Run the established read-only epistemic audit on this object's own history."""
        oid = int(obj.object_id)
        live = self._live.get(oid) or {}
        sm = live.get("map")
        if sm is None or not len(sm.xyz_h):
            seed = object_record.get("seed", {}) or {}
            visible = int(seed.get("target_visible_pixels", 0))
            return {
                "object_id": oid,
                "auditable": False,
                "reason": "no instantiated surfel map to audit",
                "object_status": (
                    "NOT_VISIBLE_OR_NO_TARGET_SUPPORT" if visible == 0 else "SEED_MEASUREMENT_FAILED"
                ),
                "seed_target_visible_pixels": visible,
                "seed_target_valid_depth_points": int(seed.get("valid_target_points", 0)),
                "exterior_refined_cells_by_state": {},
                "refined_cells_by_state": {},
                "base_cells_by_state": {},
            }

        chart, footprint_cells, footprint_deg = topo1a.build_chart(sm.xyz_h, PROFILE)
        if abs(float(chart.grid_deg) - float(public.GRID_DEG)) > 1e-12:
            raise AssertionError("local cyclopean grid changed from the established 0.1 degree scale")
        raw, support, target_range = topo1a.rasterize_target(sm.xyz_h, chart, footprint_cells)
        evidence = topo1a.empty_evidence(chart)
        observations = [
            inherited_audit._saved_observation(int(step), Path(case))
            for step, case in zip(live["steps"], live["cases"])
        ]
        for ob in observations:
            topo1a.add_observation(evidence, chart, ob["xyz_h"], ob["instance_id"], ob["valid"], oid)

        ev = boundary.EvidenceArrays(
            evidence.seen_target, evidence.seen_nontarget,
            evidence.target_range_m, evidence.nontarget_range_m,
        )
        audit = boundary.analyze_boundary(
            raw_support=raw, support=support, target_range_m=target_range, evidence=ev,
            grid_deg=chart.grid_deg, yaw0_deg=chart.yaw0_deg, pitch0_deg=chart.pitch0_deg,
            footprint_cells=footprint_cells,
            association_radius_m=float(public.ASSOCIATION_RADIUS_M),
        )
        refined, cell_ev = inherited_audit._refine_unobserved(chart, audit, observations, oid)
        arcs = inherited_audit._refined_arcs(chart, audit, refined, cell_ev)

        refined_counts = {name: int((refined == code).sum()) for name, code in epi.STATE_CODE.items()}
        exterior = {name: 0 for name in epi.STATE_CODE}
        internal = {name: 0 for name in epi.STATE_CODE}
        for row in arcs:
            (exterior if row["component_kind"] == "EXTERIOR" else internal)[row["state"]] += int(row["cell_count"])
        base_counts = {name: int((audit.state_code == code).sum()) for name, code in boundary.STATE_CODE.items()}

        live["audit_arrays"] = {
            "chart": chart, "audit": audit, "refined": refined,
            "support": support, "footprint_cells": footprint_cells,
            "observations": observations,
        }
        inherited_audit._write_visual(
            object_dir / f"object_{oid}_epistemic_shoreline.png", support, audit, refined
        )

        final = (object_record.get("growth") or {}).get("final_policy_decision", {}) or {}
        termination = object_record.get("termination_reason")
        return {
            "object_id": oid,
            "auditable": True,
            "object_status": self._status(termination, exterior, refined_counts),
            "inherited_object_status": inherited_status._object_status(exterior, refined_counts),
            "inherited_stop_interpretation": inherited_status._stop_interpretation(exterior, refined_counts, final),
            "termination_reason": termination,
            "observation_count": len(observations),
            "observation_steps": [int(o["step"]) for o in observations],
            "chart": {
                "yaw0_deg": chart.yaw0_deg, "pitch0_deg": chart.pitch0_deg,
                "grid_deg": chart.grid_deg, "width": chart.width, "height": chart.height,
            },
            "footprint_cells": int(footprint_cells),
            "footprint_radius_deg": float(footprint_deg),
            "map_points": int(len(sm.xyz_h)),
            "raw_support_cells": int(raw.sum()),
            "support_cells": int(support.sum()),
            "shoreline_cells": int(audit.shoreline.sum()),
            "base_cells_by_state": base_counts,
            "refined_cells_by_state": refined_counts,
            "exterior_refined_cells_by_state": exterior,
            "internal_refined_cells_by_state": internal,
            "attention_residue_exterior_never_observed_cells": int(exterior.get("NEVER_OBSERVED", 0)),
            "measurement_residue_observed_target_no_depth_cells": int(
                refined_counts.get("OBSERVED_TARGET_NO_DEPTH", 0)
            ),
            "refined_arc_count": len(arcs),
            "visual": f"object_{oid}_epistemic_shoreline.png",
        }

    @staticmethod
    def _status(termination: Any, exterior: dict[str, int], refined: dict[str, int]) -> str:
        """Map the established audit variables onto the declared REAL-1 vocabulary.

        Same decision variables as the FullScene-1d interpretation (policy stop
        reason, exterior NEVER_OBSERVED, OBSERVED_TARGET_NO_DEPTH); no new
        threshold or tuned quantity is introduced.
        """
        if termination == "object_watchdog":
            return "WATCHDOG_REACHED_RETAIN_FOR_REVISIT"
        if termination == "seed_measurement_failed":
            return "SEED_MEASUREMENT_FAILED"
        if termination == "no_frontier":
            if int(exterior.get("NEVER_OBSERVED", 0)) > 0:
                return "POLICY_EXHAUSTED_WITH_UNSEEN_TERRITORY"
            if int(refined.get("OBSERVED_TARGET_NO_DEPTH", 0)) > 0:
                return "ATTENTION_COMPLETE_MEASUREMENT_PARTIAL"
            return "LOCAL_FRONTIER_AND_ATTENTION_RESOLVED_UNDER_CURRENT_REPRESENTATION"
        return "LOCAL_GROWTH_STOPPED_OTHER"

    def maybe_one_handoff(self, obj: BenchmarkObject, object_record: dict[str, Any],
                          audit_record: dict[str, Any], global_step: int,
                          object_dir: Path) -> dict[str, Any] | None:
        """Optionally execute the one established bounded epistemic handoff.

        Only when termination==no_frontier and exterior NEVER_OBSERVED>0.
        At most one handoff fixation and at most one returned local action. No recursive handoff.
        """
        oid = int(obj.object_id)
        live = self._live[oid]
        arrays = live.get("audit_arrays")
        if arrays is None:
            return None
        chart, audit, refined = arrays["chart"], arrays["audit"], arrays["refined"]
        gazes: list[tuple[float, float]] = live["gazes"]

        selected = epistemic_gaze.select_epistemic_probe(
            shoreline=audit.shoreline,
            component_labels=audit.component_labels,
            components=audit.components,
            exterior_distance_cells=audit.exterior_distance_cells,
            refined_state=refined,
            never_observed_code=epi.STATE_CODE["NEVER_OBSERVED"],
            chart=chart,
            existing_gazes=gazes,
        )
        if selected is None:
            return {
                "object_id": oid,
                "handoff_executed": False,
                "reason": "no eligible exterior NEVER_OBSERVED gaze remained",
                "next_global_step": int(global_step),
                "fixation_records": [],
            }

        step = int(global_step)
        gaze = (float(selected["probe_gaze_deg"][0]), float(selected["probe_gaze_deg"][1]))
        pid = f"fix_{step:02d}"
        _case, ctx, patch, stats = self._acquire(oid, step, gaze, object_dir, pid)
        sm, assoc, empty, _idem = self._fuse_look(live["map"], patch, oid)
        live["map"] = sm
        live["gazes"].append(gaze)
        live["steps"].append(step)
        live["cases"].append(Path(ctx["case"]))
        records = [self._fixation_record(
            oid, step, len(live["gazes"]) - 1, "epistemic_handoff", gaze, stats,
            int(len(patch.xyz_h)), empty, not empty
        )]
        save_map(object_dir / "maps" / f"map_{step:02d}.npz", sm)

        c, rec, ids_R, raw_R = ctx["calibration"], ctx["rec"], ctx["ids_R"], ctx["raw_R"]
        history = inherited_audit._policy_history(arrays["observations"], oid)
        history.append(policy.history_entry(c, rec["instance_id"], rec["raw_support_L"], ids_R, raw_R, oid))
        returned = policy.choose_next(
            gaze[0], gaze[1], c, rec["instance_id"], rec["raw_support_L"], ids_R, raw_R,
            sm.xyz_h, live["gazes"], history, oid,
        )

        action: dict[str, Any] | None = None
        if not returned.get("stop") and returned.get("next_gaze_deg") is not None:
            action_gaze = tuple(map(float, returned["next_gaze_deg"]))
            if any(np.allclose(np.asarray(g), np.asarray(action_gaze), atol=1e-9) for g in live["gazes"]):
                action = {"executed": False, "reason": "returned action is an already visited gaze"}
            else:
                step += 1
                apid = f"fix_{step:02d}"
                _c2, ctx2, patch2, stats2 = self._acquire(oid, step, action_gaze, object_dir, apid)
                sm, assoc2, empty2, _i2 = self._fuse_look(sm, patch2, oid)
                live["map"] = sm
                live["gazes"].append(action_gaze)
                live["steps"].append(step)
                live["cases"].append(Path(ctx2["case"]))
                save_map(object_dir / "maps" / f"map_{step:02d}.npz", sm)
                records.append(self._fixation_record(
                    oid, step, len(live["gazes"]) - 1, "returned_local_action", action_gaze,
                    stats2, int(len(patch2.xyz_h)), empty2, not empty2
                ))
                action = {
                    "executed": True,
                    "gaze_deg": [action_gaze[0], action_gaze[1]],
                    "global_step": step,
                    "target_points": int(len(patch2.xyz_h)),
                    "empty_look": bool(empty2),
                    "matched": int(assoc2.get("matched", 0)),
                    "new": int(assoc2.get("new", 0)),
                }
                live["last_ctx"] = ctx2
        else:
            live["last_ctx"] = ctx

        return {
            "object_id": oid,
            "handoff_executed": True,
            "selection_rule": "reused cyclopean1e_gaze.select_epistemic_probe unchanged",
            "probe": {k: v for k, v in selected.items()},
            "handoff_gaze_deg": [gaze[0], gaze[1]],
            "handoff_global_step": int(global_step),
            "handoff_target_points": int(len(patch.xyz_h)),
            "handoff_empty_look": bool(empty),
            "handoff_matched": int(assoc.get("matched", 0)),
            "handoff_new": int(assoc.get("new", 0)),
            "returned_local_policy_decision": returned,
            "returned_local_action": action,
            "returned_local_action_executed": bool(action is not None and action.get("executed")),
            "recursive_handoff": False,
            "map_points_after": int(len(sm.xyz_h)),
            "next_global_step": step + 1,
            "fixation_records": records,
        }

    def finalize_object(self, obj: BenchmarkObject, object_record: dict[str, Any],
                        audit_record: dict[str, Any], handoff_record: dict[str, Any] | None,
                        object_dir: Path) -> dict[str, Any]:
        """Freeze final object map/status and return one scene-inventory row."""
        oid = int(obj.object_id)
        live = self._live.get(oid) or {}
        sm = live.get("map")
        objects_dir = self.out / "objects"
        objects_dir.mkdir(parents=True, exist_ok=True)
        npz = objects_dir / f"object_{oid}.npz"
        ply = objects_dir / f"object_{oid}.ply"

        instantiated = bool(sm is not None and len(sm.xyz_h) > 0)
        if instantiated:
            save_map(npz, sm)
            fsg6run.save_ply(ply, sm)
            if len(sm.instance_id) and set(np.unique(sm.instance_id).tolist()) != {oid}:
                raise AssertionError("frozen object map is not pure")
        else:
            # Preserve the hole explicitly rather than omitting the object, and
            # write it through the frozen map writer so it stays loadable.
            save_map(npz, SurfaceMap(
                np.zeros((0, 3), np.float32), np.zeros((0, 3), np.float32),
                np.zeros(0, np.int32), np.zeros(0, np.int16), np.zeros(0, np.uint64), [],
            ))
            ply.write_text("ply\nformat ascii 1.0\nelement vertex 0\n"
                           "property float x\nproperty float y\nproperty float z\nend_header\n")

        growth = object_record.get("growth") or {}
        return {
            "object_id": oid,
            "label": str(obj.label),
            "oracle_seed_gaze_deg": [float(obj.seed_yaw_deg), float(obj.seed_pitch_deg)],
            "instantiated": instantiated,
            "status": str(audit_record.get("object_status", "LOCAL_GROWTH_STOPPED_OTHER")),
            "termination_reason": object_record.get("termination_reason"),
            "seed_usable": bool(object_record.get("seed_usable")),
            "seed_target_visible_pixels": int((object_record.get("seed") or {}).get("target_visible_pixels", 0)),
            "seed_valid_target_points": int((object_record.get("seed") or {}).get("valid_target_points", 0)),
            "fixation_count": int(len(live.get("gazes", []))),
            "surfel_count": int(len(sm.xyz_h)) if instantiated else 0,
            "support_cells": audit_record.get("support_cells"),
            "raw_support_cells": audit_record.get("raw_support_cells"),
            "attention_residue_cells": audit_record.get("attention_residue_exterior_never_observed_cells"),
            "measurement_residue_cells": audit_record.get("measurement_residue_observed_target_no_depth_cells"),
            "scientific_stop_reached": bool(growth.get("scientific_stop_reached", False)),
            "handoff_executed": bool(handoff_record is not None and handoff_record.get("handoff_executed")),
            "returned_local_action_executed": bool(
                handoff_record is not None and handoff_record.get("returned_local_action_executed")
            ),
            "fusion_new_total": growth.get("fusion_new_total"),
            "fusion_matched_total": growth.get("fusion_matched_total"),
            "empty_steps": growth.get("empty_steps", []),
            "map_npz": str(npz.relative_to(self.out)),
            "map_ply": str(ply.relative_to(self.out)),
        }

    # ---------- exports from observer state (truth still quarantined) ----------

    def export_observer_scene(self, object_rows: list[dict[str, Any]], scene_dir: Path) -> dict[str, Any]:
        """Export combined NPZ/PLY and sparse spherical depth/instance panoramas."""
        xyz_all: list[np.ndarray] = []
        oid_all: list[np.ndarray] = []
        rgb_all: list[np.ndarray] = []
        support_all: list[np.ndarray] = []
        per_object: dict[str, int] = {}
        for row in object_rows:
            oid = int(row["object_id"])
            path = self.out / str(row["map_npz"])
            if not path.is_file():
                raise FileNotFoundError(path)
            if not bool(row.get("instantiated")):
                per_object[str(oid)] = 0
                continue
            sm = load_map(path)
            xyz_all.append(np.asarray(sm.xyz_h, np.float64).reshape(-1, 3))
            oid_all.append(np.full(len(sm.xyz_h), oid, np.int64))
            rgb_all.append(np.asarray(sm.rgb, np.float64).reshape(-1, 3))
            support_all.append(np.asarray(sm.support_count).reshape(-1))
            per_object[str(oid)] = int(len(sm.xyz_h))

        xyz = np.concatenate(xyz_all) if xyz_all else np.zeros((0, 3))
        oids = np.concatenate(oid_all) if oid_all else np.zeros(0, np.int64)
        rgb_lin = np.concatenate(rgb_all) if rgb_all else np.zeros((0, 3))
        support = np.concatenate(support_all) if support_all else np.zeros(0)
        rgb8 = _tone_preview(rgb_lin) if len(rgb_lin) else np.zeros((0, 3), np.uint8)

        export.write_scene_npz(scene_dir / "scene_points.npz", xyz, oids, support, rgb8)
        export.write_ascii_ply(scene_dir / "scene_points.ply", xyz, oids, rgb8)

        yaw, pitch, rng = topo1a.xyz_to_angles(xyz)
        depth, inst = export.spherical_zbuffer(
            yaw, pitch, rng, oids, public.PANO_WIDTH, public.PANO_HEIGHT
        )
        np.save(scene_dir / "observer_depth.npy", depth)
        np.save(scene_dir / "observer_instance.npy", inst)
        valid = np.isfinite(depth) & (depth > 0)
        Image.fromarray((valid.astype(np.uint8) * 255)).save(scene_dir / "observer_valid.png")
        Image.fromarray(export.depth_preview(depth)).save(scene_dir / "observer_depth_preview.png")

        # The surfels carry the acquired left-eye linear RGB of the pixels they
        # came from, so this mosaic is built only from images the observer
        # actually took. It is named as an acquisition mosaic, not as an
        # observer RGB reconstruction, and it is as sparse as the point cloud.
        mosaic = np.zeros((public.PANO_HEIGHT, public.PANO_WIDTH, 3), np.uint8)
        if len(xyz):
            good = np.isfinite(yaw) & np.isfinite(pitch) & np.isfinite(rng) & (rng > 0)
            gx = np.clip(np.floor(((yaw[good] + 180.0) % 360.0) / 360.0 * public.PANO_WIDTH).astype(np.int64),
                         0, public.PANO_WIDTH - 1)
            gy = np.clip(np.floor((90.0 - np.clip(pitch[good], -90.0, 90.0)) / 180.0 * public.PANO_HEIGHT).astype(np.int64),
                         0, public.PANO_HEIGHT - 1)
            order = np.argsort(-rng[good], kind="stable")  # nearest wins, written last
            mosaic[gy[order], gx[order]] = rgb8[good][order]
        Image.fromarray(mosaic).save(scene_dir / "observer_acquisition_rgb_mosaic.png")

        return {
            "scene_points_npz": "scene_points.npz",
            "scene_points_ply": "scene_points.ply",
            "observer_depth": "observer_depth.npy",
            "observer_instance": "observer_instance.npy",
            "observer_valid": "observer_valid.png",
            "observer_depth_preview": "observer_depth_preview.png",
            "observer_acquisition_rgb_mosaic": "observer_acquisition_rgb_mosaic.png",
            "observer_rgb_reconstruction_claimed": False,
            "panorama_wh": [int(public.PANO_WIDTH), int(public.PANO_HEIGHT)],
            "total_surfels": int(len(xyz)),
            "surfels_per_object": per_object,
            "occupied_panorama_pixels": int(valid.sum()),
            "panorama_pixels": int(public.PANO_WIDTH * public.PANO_HEIGHT),
            "blender_launches": int(self.blender_launches),
            "render_seconds": float(self.render_seconds),
        }

    # ---------- evaluator-only phase; called strictly after observer seal ----------

    def render_reference_after_control(self, scene_dir: Path) -> dict[str, Any]:
        """Render evaluator RGB/depth/instance panorama after observer_complete seal."""
        seal = scene_dir / "observer_complete.json"
        if not seal.is_file():
            raise RuntimeError("refusing to open evaluator truth before the observer seal exists")
        helper = self.repo_root / "tools" / "fullscene_real1_reference.py"
        subprocess.run(
            [
                sys.executable, str(helper),
                "--repo", str(self.repo_root),
                "--fixture", self.fixture,
                "--out", str(scene_dir),
                "--width", str(int(public.PANO_WIDTH)),
                "--height", str(int(public.PANO_HEIGHT)),
                "--require-seal", str(seal),
            ],
            cwd=self.repo_root,
            check=True,
        )
        rec = json.loads((scene_dir / "reference_manifest.json").read_text())
        if rec.get("fixture") != self.fixture:
            raise AssertionError("reference panorama fixture mismatch")
        return rec

    def evaluate_against_reference(self, object_rows: list[dict[str, Any]],
                                   observer_exports: dict[str, Any],
                                   reference_exports: dict[str, Any],
                                   scene_dir: Path) -> dict[str, Any]:
        """Compute inventory, coverage, depth-error, purity and efficiency metrics."""
        obs_depth = np.load(scene_dir / "observer_depth.npy")
        obs_inst = np.load(scene_dir / "observer_instance.npy")
        ref_depth = np.load(scene_dir / "reference_depth.npy")
        ref_inst = np.load(scene_dir / "reference_instance.npy")
        if obs_depth.shape != ref_depth.shape or obs_inst.shape != ref_inst.shape:
            raise AssertionError("observer and reference panoramas disagree in shape")

        obs_valid = np.isfinite(obs_depth) & (obs_depth > 0)
        ref_valid = np.isfinite(ref_depth) & (ref_depth > 0)

        per_object: list[dict[str, Any]] = []
        for row in object_rows:
            oid = int(row["object_id"])
            ref_m = ref_valid & (ref_inst == oid)
            obs_m = obs_valid & (obs_inst == oid)
            both = ref_m & obs_m
            err = np.abs(obs_depth[both].astype(np.float64) - ref_depth[both].astype(np.float64))
            ref_px = int(ref_m.sum())
            obs_px = int(obs_m.sum())
            wrong = obs_valid & (obs_inst == oid) & ref_valid & (ref_inst != oid)
            per_object.append({
                "object_id": oid,
                "label": row.get("label"),
                "status": row.get("status"),
                "instantiated": bool(row.get("instantiated")),
                "fixation_count": row.get("fixation_count"),
                "surfel_count": row.get("surfel_count"),
                "reference_visible_pixels": ref_px,
                "observer_labelled_pixels": obs_px,
                "observer_correct_pixels": int(both.sum()),
                "sparse_pixel_coverage_fraction": (float(both.sum() / ref_px) if ref_px else None),
                "purity_fraction": (float(both.sum() / obs_px) if obs_px else None),
                "contaminated_pixels": int(wrong.sum()),
                "contamination_fraction": (float(wrong.sum() / obs_px) if obs_px else None),
                "depth_abs_error_median_m": (float(np.median(err)) if len(err) else None),
                "depth_abs_error_p95_m": (float(np.percentile(err, 95)) if len(err) else None),
                "depth_comparable_pixels": int(len(err)),
                "audit_support_cells": row.get("support_cells"),
                "audit_raw_support_cells": row.get("raw_support_cells"),
                "attention_residue_cells": row.get("attention_residue_cells"),
                "measurement_residue_cells": row.get("measurement_residue_cells"),
                "handoff_executed": row.get("handoff_executed"),
                "returned_local_action_executed": row.get("returned_local_action_executed"),
            })

        enumerated = [int(r["object_id"]) for r in object_rows]
        instantiated = [int(r["object_id"]) for r in object_rows if bool(r.get("instantiated"))]
        statuses: dict[str, int] = {}
        for r in object_rows:
            statuses[str(r.get("status"))] = statuses.get(str(r.get("status")), 0) + 1

        summary = {
            "schema": "FullSceneREAL1-evaluation-v1",
            "metric_semantics": (
                "coverage/purity are sparse spherical z-buffer pixel measures of a point cloud at "
                f"{public.PANO_WIDTH}x{public.PANO_HEIGHT}, not surface completeness; attention and measurement "
                "residues are separate audit quantities; none of these is combined into a single score"
            ),
            "single_quality_score_synthesized": False,
            "objects_enumerated": enumerated,
            "objects_attempted": len(enumerated),
            "objects_instantiated": instantiated,
            "objects_not_instantiated": [x for x in enumerated if x not in set(instantiated)],
            "status_counts": statuses,
            "total_fixations": int(sum(int(r.get("fixation_count", 0)) for r in object_rows)),
            "total_surfels": int(sum(int(r.get("surfel_count", 0)) for r in object_rows)),
            "blender_launches": int(self.blender_launches),
            "render_seconds": float(self.render_seconds),
            "observer_occupied_panorama_pixels": int(obs_valid.sum()),
            "reference_occupied_panorama_pixels": int(ref_valid.sum()),
            "reference_instance_ids_present": [int(i) for i in np.unique(ref_inst) if int(i) > 0],
            "handoffs_executed": int(sum(1 for r in object_rows if r.get("handoff_executed"))),
            "returned_local_actions_executed": int(
                sum(1 for r in object_rows if r.get("returned_local_action_executed"))
            ),
            "per_object": per_object,
        }

        (scene_dir / "per_object_metrics.json").write_text(
            json.dumps(per_object, indent=2, sort_keys=True) + "\n"
        )
        (scene_dir / "evaluation_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n"
        )
        self._coverage_preview(scene_dir, obs_valid, ref_valid, obs_inst, ref_inst)
        return summary

    @staticmethod
    def _coverage_preview(scene_dir: Path, obs_valid, ref_valid, obs_inst, ref_inst) -> None:
        """Green = observer agrees, red = observer disagrees, grey = reference only."""
        h, w = ref_valid.shape
        img = np.zeros((h, w, 3), np.uint8)
        img[ref_valid] = (60, 60, 60)
        agree = obs_valid & ref_valid & (obs_inst == ref_inst)
        disagree = obs_valid & ref_valid & (obs_inst != ref_inst)
        outside = obs_valid & ~ref_valid
        img[disagree] = (220, 60, 60)
        img[outside] = (230, 180, 40)
        img[agree] = (60, 220, 90)
        Image.fromarray(img).save(scene_dir / "coverage_preview.png")
