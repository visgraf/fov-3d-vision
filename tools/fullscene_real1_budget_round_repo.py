"""Live-repository seam for one extra watchdog-continuation round.

Claude Code may complete this NEW file only. The completed REAL-1 baseline and
all established mechanisms remain frozen/read-only.

Everything below composes already-established mechanisms unchanged: the generic
procedural renderer (tools/scene_render_fix.py), the current stereo front end,
frozen FSG6f through the unchanged MultiObject-2c target-label adapter, the
frozen 12 mm FSG3 association with idempotent replay, the inherited <100-point
empty-look rule, the MultiObject-3d cyclopean audit helpers, and the
MultiObject-3f exact frozen-decision replay.

Only the completed REAL-1 baseline is read. Data from any seed-recovery
follow-up round is explicitly refused.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import time
from typing import Any

import numpy as np
from PIL import Image

import cyclopean1a_topology as topo1a
import cyclopean1b_boundary as boundary
import cyclopean1d_epistemic as epi
import fsg6f_public as frozen_public
import fsg6f_run as fsg6run
import fsg_stereo_hdr as hdr
import fullscene_real1_export as export
import multiobject2c_policy as policy
import multiobject3d_audit as inherited_audit
import multiobject3f_audit as replay_audit
from fsg3_surface_map import Patch, fuse, load_map, save_map
from fsg_stereo import support_mask
from fsg_stereo_supported import check_kernel_equivalence, compute_once
from reality1_run import _tone_preview

PROFILE = "full"
RENDERER = "tools/scene_render_fix.py"
GRID_DEG = 0.1
EMPTY_TARGET_VALID_LIMIT = 100
PANO_WIDTH = 2048
PANO_HEIGHT = 1024
# Any path component that would mean a different experiment's data.
FORBIDDEN_BASELINE_MARKERS = ("seed-round", "seed_round", "budget-round", "budget_round")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


class BudgetRoundRepository:
    def __init__(self, repo: Path, baseline_out: Path, out: Path, seed: int):
        self.repo = Path(repo).resolve()
        self.baseline_out = Path(baseline_out).resolve()
        self.out = Path(out).resolve()
        self.seed = int(seed)
        self.blender = "blender"
        self.device = "OPTIX"
        self.blender_launches = 0
        self.render_seconds = 0.0
        self._live: dict[int, dict[str, Any]] = {}
        self._baseline_hashes: dict[str, str] = {}
        self._kernel_checked = False
        self.fusion = dict(frozen_public.FUSION)

    # ---------- baseline (strictly read-only) ----------

    def load_baseline(self) -> dict[str, Any]:
        """Return the sealed REAL-1 baseline; refuse any other round's output."""
        name = str(self.baseline_out).lower()
        for marker in FORBIDDEN_BASELINE_MARKERS:
            if marker in name:
                raise AssertionError(
                    f"REAL-1W must consume the original REAL-1 baseline, not {self.baseline_out}"
                )
        manifest_path = self.baseline_out / "scene_manifest.json"
        seal_path = self.baseline_out / "observer_complete.json"
        status_path = self.baseline_out / "object_status_table.json"
        history_path = self.baseline_out / "fixation_history.json"
        for p in (manifest_path, seal_path, status_path, history_path):
            if not p.is_file():
                raise FileNotFoundError(f"baseline REAL-1 artifact missing: {p}")

        manifest = json.loads(manifest_path.read_text())
        seal = json.loads(seal_path.read_text())
        rows = json.loads(status_path.read_text())
        history = json.loads(history_path.read_text())

        if seal.get("observer_sealed") is not True:
            raise AssertionError("baseline REAL-1 observer is not sealed")
        if manifest.get("observer_sealed_before_truth") is not True:
            raise AssertionError("baseline REAL-1 did not seal before opening truth")
        if manifest.get("structural_fails") != []:
            raise AssertionError("baseline REAL-1 record is structurally incomplete")
        if int(manifest.get("seed", -1)) != self.seed:
            raise AssertionError("baseline REAL-1 seed does not match this round")

        pinned = [
            "scene_manifest.json", "observer_complete.json", "object_status_table.json",
            "fixation_history.json", "enumeration_oracle.json", "scene_points.npz",
            "observer_depth.npy", "observer_instance.npy",
            "reference_depth.npy", "reference_instance.npy", "reference_rgb.png",
            "evaluation_summary.json", "per_object_metrics.json",
        ]
        for r in rows:
            for key in ("map_npz", "map_ply"):
                if r.get(key):
                    pinned.append(str(r[key]))
            pinned.append(f"objects/object_{int(r['object_id'])}/object_complete.json")
        self._baseline_hashes = {
            n: _sha256(self.baseline_out / n)
            for n in pinned if (self.baseline_out / n).is_file()
        }

        return {
            "object_rows": rows,
            "fixation_steps": [int(f["global_step"]) for f in history],
            "manifest": manifest,
            "baseline_seal_sha256": _sha256(seal_path),
            "baseline_hashes": dict(self._baseline_hashes),
        }

    def verify_baseline_unchanged(self) -> dict[str, Any]:
        if not self._baseline_hashes:
            raise AssertionError("baseline was never pinned")
        after = {n: _sha256(self.baseline_out / n) for n in self._baseline_hashes}
        changed = [n for n in after if after[n] != self._baseline_hashes[n]]
        if changed:
            raise AssertionError(f"baseline REAL-1 artifacts changed during the round: {changed}")
        return {"baseline_files_pinned": len(after), "baseline_files_changed": 0}

    # ---------- acquisition ----------

    def _render(self, step: int, gaze: tuple[float, float], object_dir: Path) -> Path:
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
        p = subprocess.run(cmd, cwd=self.repo, text=True, capture_output=True)
        self.blender_launches += 1
        self.render_seconds += time.perf_counter() - t0
        (logs / f"render_{step:02d}.log").write_text(p.stdout + "\n--- STDERR ---\n" + p.stderr)
        if p.returncode != 0:
            raise RuntimeError(f"continuation Blender fixation {step} failed; see {logs}")
        rr = json.loads((out / "run.json").read_text())
        if not rr.get("complete") or int(rr.get("seed", -1)) != self.seed or int(rr.get("step", -1)) != step:
            raise RuntimeError("incomplete or wrong continuation acquisition record")
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

    # ---------- replay the saved stop, then one bounded block ----------

    def replay_and_continue(self, target_row: dict[str, Any], max_fresh_fixations: int,
                            first_global_step: int, object_dir: Path) -> dict[str, Any]:
        """Replay saved final policy exactly, then execute at most max_fresh_fixations frozen local actions.

        Stop early only if frozen FSG6f reaches its own scientific stop. No handoff,
        no new threshold, no re-seed, and no reference/evaluator access.
        """
        if not self._kernel_checked:
            check_kernel_equivalence()
            self._kernel_checked = True
        oid = int(target_row["object_id"])
        src = self.baseline_out / "objects" / f"object_{oid}"
        checkpoint = json.loads((src / "object_complete.json").read_text())
        growth = checkpoint.get("growth") or {}
        saved_final = growth.get("final_policy_decision") or {}
        if checkpoint.get("termination_reason") != "object_watchdog":
            raise AssertionError(f"object {oid} did not terminate on the watchdog")

        gazes = [tuple(map(float, g)) for g in growth["gazes_deg"]]
        steps = [int(f["global_step"]) for f in checkpoint["fixation_records"]]
        if len(steps) != len(gazes):
            raise AssertionError("baseline gaze/fixation length mismatch")

        # Resume the SAVED FINAL map. It is not re-fused and the baseline copy is
        # never written to; old acquisitions are re-read from disk, never re-rendered.
        baseline_map_path = self.baseline_out / str(target_row["map_npz"])
        sm = load_map(baseline_map_path)
        if len(sm.instance_id) and set(np.unique(sm.instance_id).tolist()) != {oid}:
            raise AssertionError("resumed baseline map is not pure")
        points_before = int(len(sm.xyz_h))

        cases = [src / "acquisition" / f"fix_{s:02d}" / f"fix_{s:02d}" for s in steps]
        observations = [inherited_audit._saved_observation(s, c) for s, c in zip(steps, cases)]
        history = inherited_audit._policy_history(observations, oid)

        # Reproduce the saved final frozen decision BEFORE any fresh render.
        last = observations[-1]
        replayed = policy.choose_next(
            gazes[-1][0], gazes[-1][1], last["calibration"],
            last["instance_id"], last["raw_support_L"], last["instance_R"], last["raw_support_R"],
            sm.xyz_h, gazes, history, oid,
        )
        replay_audit._exact_decision_replay(saved_final, replayed, f"object {oid} pre-continuation")
        if replayed.get("stop"):
            raise AssertionError(f"object {oid} saved stop was not a continue; nothing to continue")

        maps_dir = object_dir / "maps"
        maps_dir.mkdir(parents=True, exist_ok=True)
        patches_dir = object_dir / "patches"
        patches_dir.mkdir(parents=True, exist_ok=True)
        rgb_dir = object_dir / "rgb"
        rgb_dir.mkdir(parents=True, exist_ok=True)

        decision = dict(replayed)
        ledger: list[dict[str, Any]] = []
        fresh_gazes: list[tuple[float, float]] = []
        fresh_steps: list[int] = []
        empty_steps: list[int] = []
        trace: list[dict[str, Any]] = [dict(replayed)]
        snapshots = [sm.xyz_h.copy()]
        supports = [sm.support_count.copy()]
        step = int(first_global_step)
        termination: str | None = None
        t0 = time.perf_counter()

        while True:
            if decision.get("stop"):
                termination = str(decision.get("reason", "policy_stop"))
                break
            if len(fresh_gazes) >= int(max_fresh_fixations):
                # Mechanical end of the single diagnostic block. Not a scientific stop.
                termination = "one_round_block_exhausted"
                break
            gaze = tuple(map(float, decision["next_gaze_deg"]))
            if any(np.allclose(np.asarray(g), np.asarray(gaze), atol=1e-9) for g in gazes):
                raise AssertionError("continuation policy revisited an existing fixation")

            case = self._render(step, gaze, object_dir)
            c, obs = hdr.read_observation(case)
            rec, _meta, state = compute_once(c, obs)
            ids_R, raw_R = self._right_state(c, rec, state)
            pid = f"fix_{step:02d}"
            mask = np.asarray(rec["valid"], bool) & (np.asarray(rec["instance_id"]) == oid)
            patch = Patch(pid, np.asarray(rec["xyz_h"])[mask], np.asarray(rec["rgb_left"])[mask],
                          np.asarray(rec["instance_id"])[mask])
            np.savez_compressed(
                patches_dir / f"{pid}.npz",
                xyz_h=np.asarray(patch.xyz_h, np.float32), rgb=np.asarray(patch.rgb, np.float32),
                instance_id=np.asarray(patch.instance_id), valid=np.asarray(rec["valid"], bool),
                oracle_instance_id=np.asarray(rec["instance_id"]),
                raw_support_L=np.asarray(rec["raw_support_L"], bool),
                oracle_instance_id_R=np.asarray(ids_R), raw_support_R=np.asarray(raw_R, bool),
            )
            Image.fromarray(_tone_preview(rec["rgb_left"])).save(rgb_dir / f"{pid}.png")

            before = int(len(sm.xyz_h))
            empty = len(patch.xyz_h) < EMPTY_TARGET_VALID_LIMIT
            if empty:
                empty_steps.append(step)
                assoc = {"matched": 0, "new": 0, "distances_m": np.empty(0)}
                idem = True
            else:
                sm, assoc = fuse(sm, patch, oid,
                                 self.fusion["association_radius_m"], self.fusion["hash_cell_m"])
                replay_map, dup = fuse(sm, patch, oid,
                                       self.fusion["association_radius_m"], self.fusion["hash_cell_m"])
                idem = bool(dup["duplicate_patch"]
                            and np.array_equal(sm.xyz_h, replay_map.xyz_h)
                            and np.array_equal(sm.support_count, replay_map.support_count)
                            and np.array_equal(sm.provenance_mask, replay_map.provenance_mask))
                if not idem:
                    raise AssertionError("continuation patch replay is not idempotent")
            if len(sm.instance_id) and set(np.unique(sm.instance_id).tolist()) != {oid}:
                raise AssertionError("continuation contaminated the object map")
            save_map(maps_dir / f"map_{step:02d}.npz", sm)

            gazes.append(gaze)
            fresh_gazes.append(gaze)
            fresh_steps.append(step)
            observations.append(inherited_audit._saved_observation(step, case))
            history.append(policy.history_entry(c, rec["instance_id"], rec["raw_support_L"], ids_R, raw_R, oid))
            snapshots.append(sm.xyz_h.copy())
            supports.append(sm.support_count.copy())

            ids = np.asarray(rec["instance_id"])
            valid = np.asarray(rec["valid"], bool)
            visible = int((ids == oid).sum())
            dist = np.asarray(assoc.get("distances_m", np.empty(0)))
            ledger.append({
                "global_step": step,
                "fresh_index": len(fresh_gazes) - 1,
                "object_fixation_index": len(gazes) - 1,
                "yaw_deg": gaze[0], "pitch_deg": gaze[1],
                "target_visible_pixels": visible,
                "target_valid_depth_points": int(len(patch.xyz_h)),
                "target_depth_recovery_fraction": (float(len(patch.xyz_h) / visible) if visible else None),
                "frame_valid_fraction": float(valid.mean()),
                "empty_look": bool(empty),
                "matched": int(assoc.get("matched", 0)),
                "new": int(assoc.get("new", 0)),
                "overlap_median_distance_m": (float(np.median(dist)) if len(dist) else None),
                "overlap_p95_distance_m": (float(np.percentile(dist, 95)) if len(dist) else None),
                "idempotent_replay": bool(idem),
                "map_points_before": before,
                "map_points_after": int(len(sm.xyz_h)),
            })

            decision = policy.choose_next(
                gaze[0], gaze[1], c, rec["instance_id"], rec["raw_support_L"], ids_R, raw_R,
                sm.xyz_h, gazes, history, oid,
            )
            decision["object_fixation_index"] = len(gazes) - 1
            decision["global_step"] = step
            trace.append(dict(decision))
            step += 1

        continued_npz = object_dir / f"object_{oid}_continued_surface_map.npz"
        save_map(continued_npz, sm)
        fsg6run.save_ply(object_dir / f"object_{oid}_continued_surface_map.ply", sm)
        if len(fresh_gazes):
            fsg6run.write_growth(object_dir / f"object_{oid}_continuation_growth.png",
                                 snapshots, supports, gazes[-(len(fresh_gazes) + 1):])

        self._live[oid] = {"map": sm, "observations": observations, "gazes": gazes}
        scientific = bool(termination != "one_round_block_exhausted" and decision.get("stop"))
        return {
            "object_id": oid,
            "resumed_from_baseline_map": str(target_row["map_npz"]),
            "resumed_map_sha256": _sha256(baseline_map_path),
            "reseeded": False,
            "historical_rerenders": 0,
            "baseline_fixation_count": len(steps),
            "baseline_last_gaze_deg": [gazes[len(steps) - 1][0], gazes[len(steps) - 1][1]],
            "saved_final_policy_decision": saved_final,
            "replayed_final_policy_decision": replayed,
            "replay_exact": True,
            "round_fixation_limit": int(max_fresh_fixations),
            "fresh_fixation_count": len(fresh_gazes),
            "fresh_gazes_deg": [[g[0], g[1]] for g in fresh_gazes],
            "fresh_global_steps": fresh_steps,
            "empty_steps": empty_steps,
            "ledger": ledger,
            "termination_reason": termination,
            "scientific_stop_reached": scientific,
            "block_exhausted": bool(termination == "one_round_block_exhausted"),
            "final_policy_decision_after_round": decision,
            "policy_trace": trace,
            "map_points_before": points_before,
            "map_points_after": int(len(sm.xyz_h)),
            "map_points_gained": int(len(sm.xyz_h)) - points_before,
            "fusion_new_total": int(sum(int(r["new"]) for r in ledger)),
            "fusion_matched_total": int(sum(int(r["matched"]) for r in ledger)),
            "continued_map_npz": continued_npz.name,
            "handoff_actions": 0,
            "returned_handoff_actions": 0,
            "second_block": False,
            "adaptive_budget_rule_used": False,
            "loop_wall_seconds": float(time.perf_counter() - t0),
        }

    # ---------- established read-only audit ----------

    def audit_after_round(self, target_row: dict[str, Any], continuation: dict[str, Any],
                          object_dir: Path) -> dict[str, Any]:
        """Run established read-only epistemic audit after the continuation block."""
        oid = int(target_row["object_id"])
        live = self._live[oid]
        sm = live["map"]
        observations = live["observations"]

        chart, footprint_cells, footprint_deg = topo1a.build_chart(sm.xyz_h, PROFILE)
        if abs(float(chart.grid_deg) - GRID_DEG) > 1e-12:
            raise AssertionError("local cyclopean grid changed from the established 0.1 degree scale")
        raw, support, target_range = topo1a.rasterize_target(sm.xyz_h, chart, footprint_cells)
        evidence = topo1a.empty_evidence(chart)
        for ob in observations:
            topo1a.add_observation(evidence, chart, ob["xyz_h"], ob["instance_id"], ob["valid"], oid)
        ev = boundary.EvidenceArrays(evidence.seen_target, evidence.seen_nontarget,
                                     evidence.target_range_m, evidence.nontarget_range_m)
        audit = boundary.analyze_boundary(
            raw_support=raw, support=support, target_range_m=target_range, evidence=ev,
            grid_deg=chart.grid_deg, yaw0_deg=chart.yaw0_deg, pitch0_deg=chart.pitch0_deg,
            footprint_cells=footprint_cells,
            association_radius_m=float(self.fusion["association_radius_m"]),
        )
        refined, cell_ev = inherited_audit._refine_unobserved(chart, audit, observations, oid)
        arcs = inherited_audit._refined_arcs(chart, audit, refined, cell_ev)
        refined_counts = {n: int((refined == c).sum()) for n, c in epi.STATE_CODE.items()}
        exterior = {n: 0 for n in epi.STATE_CODE}
        internal = {n: 0 for n in epi.STATE_CODE}
        for row in arcs:
            (exterior if row["component_kind"] == "EXTERIOR" else internal)[row["state"]] += int(row["cell_count"])
        base_counts = {n: int((audit.state_code == c).sum()) for n, c in boundary.STATE_CODE.items()}
        inherited_audit._write_visual(object_dir / f"object_{oid}_continued_shoreline.png",
                                      support, audit, refined)

        # Baseline residues for a like-for-like delta, read from the sealed record.
        b_audit = (json.loads((self.baseline_out / "objects" / f"object_{oid}" /
                               "object_complete.json").read_text()).get("audit") or {})
        b_ext = b_audit.get("exterior_refined_cells_by_state", {}) or {}
        b_ref = b_audit.get("refined_cells_by_state", {}) or {}
        return {
            "object_id": oid,
            "audit_triggered_action": False,
            "observation_count": len(observations),
            "chart": {"yaw0_deg": chart.yaw0_deg, "pitch0_deg": chart.pitch0_deg,
                      "grid_deg": chart.grid_deg, "width": chart.width, "height": chart.height},
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
            "measurement_residue_observed_target_no_depth_cells": int(refined_counts.get("OBSERVED_TARGET_NO_DEPTH", 0)),
            "baseline_support_cells": target_row.get("support_cells"),
            "baseline_raw_support_cells": target_row.get("raw_support_cells"),
            "baseline_attention_residue_cells": b_ext.get("NEVER_OBSERVED"),
            "baseline_measurement_residue_cells": b_ref.get("OBSERVED_TARGET_NO_DEPTH"),
            "support_cells_delta": int(support.sum()) - int(target_row.get("support_cells") or 0),
            "raw_support_cells_delta": int(raw.sum()) - int(target_row.get("raw_support_cells") or 0),
            "attention_residue_delta": int(exterior.get("NEVER_OBSERVED", 0)) - int(b_ext.get("NEVER_OBSERVED") or 0),
            "measurement_residue_delta": int(refined_counts.get("OBSERVED_TARGET_NO_DEPTH", 0)) - int(b_ref.get("OBSERVED_TARGET_NO_DEPTH") or 0),
            "visual": f"object_{oid}_continued_shoreline.png",
        }

    # ---------- evaluator phase, strictly after the continuation seal ----------

    def _panorama(self, maps: dict[int, Any]) -> tuple[np.ndarray, np.ndarray]:
        xyz = [np.asarray(m.xyz_h, np.float64).reshape(-1, 3) for m in maps.values() if len(m.xyz_h)]
        oid = [np.full(len(m.xyz_h), o, np.int64) for o, m in maps.items() if len(m.xyz_h)]
        if not xyz:
            return (np.full((PANO_HEIGHT, PANO_WIDTH), np.nan, np.float32),
                    np.zeros((PANO_HEIGHT, PANO_WIDTH), np.int32))
        p = np.concatenate(xyz)
        o = np.concatenate(oid)
        yaw, pitch, rng = topo1a.xyz_to_angles(p)
        return export.spherical_zbuffer(yaw, pitch, rng, o, PANO_WIDTH, PANO_HEIGHT)

    @staticmethod
    def _metrics(oid: int, depth: np.ndarray, inst: np.ndarray,
                 ref_depth: np.ndarray, ref_inst: np.ndarray) -> dict[str, Any]:
        rv = np.isfinite(ref_depth) & (ref_depth > 0)
        ov = np.isfinite(depth) & (depth > 0)
        ref_m = rv & (ref_inst == oid)
        obs_m = ov & (inst == oid)
        both = ref_m & obs_m
        err = np.abs(depth[both].astype(np.float64) - ref_depth[both].astype(np.float64))
        wrong = obs_m & rv & (ref_inst != oid)
        return {
            "reference_visible_pixels": int(ref_m.sum()),
            "observer_labelled_pixels": int(obs_m.sum()),
            "observer_correct_pixels": int(both.sum()),
            "sparse_pixel_coverage_fraction": (float(both.sum() / ref_m.sum()) if ref_m.sum() else None),
            "purity_fraction": (float(both.sum() / obs_m.sum()) if obs_m.sum() else None),
            "contamination_fraction": (float(wrong.sum() / obs_m.sum()) if obs_m.sum() else None),
            "depth_abs_error_median_m": (float(np.median(err)) if len(err) else None),
            "depth_abs_error_p95_m": (float(np.percentile(err, 95)) if len(err) else None),
            "depth_comparable_pixels": int(len(err)),
        }

    def evaluate_after_seal(self, results: list[dict[str, Any]], seal_path: Path,
                            eval_dir: Path) -> dict[str, Any]:
        """After seal only, compare baseline-vs-continued observer products to immutable REAL-1 reference arrays."""
        seal_path = Path(seal_path)
        if not seal_path.is_file():
            raise RuntimeError("refusing to open evaluator products before the continuation seal exists")
        sealed = json.loads(seal_path.read_text())
        if sealed.get("truth_opened_before_seal") is not False or sealed.get("one_round_complete") is not True:
            raise RuntimeError("continuation seal is not a sealed, truth-closed record")
        eval_dir.mkdir(parents=True, exist_ok=True)

        ref_depth = np.load(self.baseline_out / "reference_depth.npy")
        ref_inst = np.load(self.baseline_out / "reference_instance.npy")
        rows = json.loads((self.baseline_out / "object_status_table.json").read_text())
        targets = {int(r["object_id"]) for r in results}

        baseline_maps: dict[int, Any] = {}
        continued_maps: dict[int, Any] = {}
        for r in rows:
            oid = int(r["object_id"])
            if not r.get("instantiated"):
                continue
            bm = load_map(self.baseline_out / str(r["map_npz"]))
            baseline_maps[oid] = bm
            continued_maps[oid] = self._live[oid]["map"] if oid in targets else bm

        b_depth, b_inst = self._panorama(baseline_maps)
        c_depth, c_inst = self._panorama(continued_maps)
        np.save(eval_dir / "continued_observer_depth.npy", c_depth)
        np.save(eval_dir / "continued_observer_instance.npy", c_inst)
        Image.fromarray(export.depth_preview(c_depth)).save(eval_dir / "continued_observer_depth_preview.png")

        per_object = []
        for oid in sorted(targets):
            b = self._metrics(oid, b_depth, b_inst, ref_depth, ref_inst)
            c = self._metrics(oid, c_depth, c_inst, ref_depth, ref_inst)
            delta = {}
            for k in ("sparse_pixel_coverage_fraction", "purity_fraction",
                      "depth_abs_error_median_m", "depth_abs_error_p95_m"):
                delta[k] = (None if b[k] is None or c[k] is None else float(c[k] - b[k]))
            delta["observer_correct_pixels"] = int(c["observer_correct_pixels"] - b["observer_correct_pixels"])
            delta["observer_labelled_pixels"] = int(c["observer_labelled_pixels"] - b["observer_labelled_pixels"])
            per_object.append({"object_id": oid, "baseline": b, "continued": c, "delta": delta})

        # Non-target objects must be bit-identical between the two panoramas.
        untouched_ok = True
        for oid in sorted(set(baseline_maps) - targets):
            if not np.array_equal(baseline_maps[oid].xyz_h, continued_maps[oid].xyz_h):
                untouched_ok = False
        summary = {
            "schema": "FullSceneREAL1W-postseal-evaluation-v1",
            "metric_semantics": (
                "sparse spherical z-buffer pixel measures at "
                f"{PANO_WIDTH}x{PANO_HEIGHT} against the immutable REAL-1 reference; coverage is not surface "
                "completeness; attention and measurement residues are separate audit quantities; no score is "
                "synthesized and no budget formula is fitted"
            ),
            "score_synthesized": False,
            "budget_formula_fitted": False,
            "reference_depth": "baseline reference_depth.npy (immutable REAL-1 product)",
            "reference_instance": "baseline reference_instance.npy (immutable REAL-1 product)",
            "non_target_objects_unchanged": bool(untouched_ok),
            "per_object": per_object,
        }
        (eval_dir / "postseal_evaluation.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
        return summary
