"""Repository seam for Demo-Tabletop-1.

Unlike REAL-1 research runs, this DEMO seam is explicitly allowed to use evaluator
truth for guidance and rejection. It must still preserve one hard boundary:
reference depth/xyz may not be inserted as metric foreground reconstruction.

Claude Code should bind these methods to the live repository while changing only
new Demo-Tabletop-1 files unless a genuine blocker is reported first.

BOUND TO THE LIVE REPOSITORY. Every mechanism below is an established one used
unchanged: the procedural `tabletop_cloth` acquisition path
(tools/scene_render_fix.py), the current foveated stereo front end
(fsg_stereo_supported.compute_once), the FullScene-1b selected-object
extraction, the frozen 12 mm FSG3 association with idempotent replay, the frozen
local FSG policy through the unchanged MultiObject-2c target-label adapter, and
the REAL-1 spherical projection/export helpers.

THE HARD BOUNDARY, enforced at runtime in acquire_and_validate():
  * foreground xyz is read from the stereo record only;
  * the accepted set is a boolean FILTER of that array, verified bitwise as a
    row-subset and by array hash, never a reference-derived array;
  * reference range is used to REJECT samples and is also reported as the
    would-be replacement, so the manifest can show it was not adopted.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
from typing import Any

import numpy as np
from PIL import Image

import cyclopean1a_topology as topo1a
import demo_tabletop1_public as public
import demo_tabletop1_reference as ref_builder
import fsg6f_public as frozen_public
import fsg6f_run as fsg6run
import fsg_stereo_hdr as hdr
import fullscene_real1_export as export
import multiobject2c_policy as policy
import multiobject3d_audit as inherited_audit
from fsg3_surface_map import Patch, fuse, initialize, load_map, save_map
from fsg_stereo import support_mask
from fsg_stereo_supported import check_kernel_equivalence, compute_once
from reality1_run import _tone_preview

PROFILE = "full"
RENDERER = "tools/scene_render_fix.py"

# --- Demo-only constants. Fixed for every object; none is tuned per object. ---
# Sparse point clouds never fill a panorama cell-for-cell, so "covered" is the
# accepted-foreground projection dilated by a fixed radius before comparison.
COVERED_DILATION_CELLS = 3
# The demo stops an object once this much of its reference angular support is
# covered. It is a DEMO presentation condition, not a completion claim.
DEMO_COVERAGE_TARGET = 0.90
# A redirect is only worth a fixation if the largest uncovered blob is this big.
MIN_REDIRECT_COMPONENT_CELLS = 50
# The frozen FSG3 initialize() itself refuses fewer than 100 points.
MIN_MAP_INIT_POINTS = 100


@dataclass(frozen=True)
class DemoObject:
    object_id: int
    label: str
    is_background: bool


def _sha256_array(a: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def _rows_subset(sub: np.ndarray, sup: np.ndarray) -> bool:
    """True when every row of `sub` appears bitwise in `sup`."""
    sub = np.ascontiguousarray(sub)
    sup = np.ascontiguousarray(sup)
    if len(sub) == 0:
        return True
    have = {r.tobytes() for r in sup}
    return all(r.tobytes() in have for r in sub)


class RepositoryAdapter:
    def __init__(self, repo_root: Path, out: Path, seed: int):
        self.repo_root = Path(repo_root).resolve()
        self.out = Path(out).resolve()
        self.seed = int(seed)
        self.blender = "blender"
        self.device = "OPTIX"
        self.blender_launches = 0
        self.render_seconds = 0.0
        # Bind the frozen 12 mm rule from its own source rather than restating it.
        self.fusion = dict(frozen_public.FUSION)
        self._ref: dict[str, Any] = {}
        self._live: dict[int, dict[str, Any]] = {}
        self._kernel_checked = False

    # ---------- 1. reference and guidance, before control (Demo Mode) ----------

    def build_reference_and_guidance(self) -> dict[str, Any]:
        """Create reference RGB/depth/instance plus guidance metadata for tabletop_cloth.

        This is intentionally truth-side and happens before control in Demo Mode.
        The returned record must enumerate positive objects dynamically and expose
        enough information to choose visible seed/redirect gazes. Record provenance.
        """
        ref = ref_builder.build_reference(public.FIXTURE, public.PANO_WIDTH, public.PANO_HEIGHT)
        self._ref = ref
        self.out.mkdir(parents=True, exist_ok=True)
        np.save(self.out / "reference_depth.npy", ref["depth"])
        np.save(self.out / "reference_instance.npy", ref["instance"])
        Image.fromarray(_tone_preview(ref["rgb_linear"])).save(self.out / "reference_rgb.png")

        inst = ref["instance"]
        depth = ref["depth"]
        rv = np.isfinite(depth) & (depth > 0)
        rows: list[dict[str, Any]] = []
        # Dynamic enumeration: ids come from the live scene spec, never literals.
        for oid in sorted(ref["labels"]):
            mask = rv & (inst == int(oid))
            comps = inherited_audit._components(mask)
            comps.sort(key=len, reverse=True)
            entry: dict[str, Any] = {
                "object_id": int(oid),
                "label": str(ref["labels"][oid]),
                "reference_visible_cells": int(mask.sum()),
                "reference_components": len(comps),
                "largest_component_cells": int(len(comps[0])) if comps else 0,
            }
            if comps:
                big = np.zeros_like(mask)
                big[comps[0][:, 0], comps[0][:, 1]] = True
                cell = ref_builder.deepest_interior_cell(big)
                if cell is not None:
                    gy, gx = cell
                    yaw, pitch = ref_builder.cell_to_gaze(gy, gx, public.PANO_WIDTH, public.PANO_HEIGHT)
                    entry.update({
                        "seed_cell_yx": [int(gy), int(gx)],
                        "seed_gaze_deg": [float(yaw), float(pitch)],
                        "seed_reference_range_m": float(depth[gy, gx]),
                    })
                d = depth[mask]
                entry.update({
                    "reference_range_min_m": float(d.min()),
                    "reference_range_median_m": float(np.median(d)),
                    "reference_range_max_m": float(d.max()),
                })
            rows.append(entry)

        # Deterministic crop of the occupied region, used only for visuals.
        ys, xs = np.nonzero(rv)
        pad = 24
        crop = [int(max(0, ys.min() - pad)), int(min(public.PANO_HEIGHT, ys.max() + 1 + pad)),
                int(max(0, xs.min() - pad)), int(min(public.PANO_WIDTH, xs.max() + 1 + pad))]

        guidance = {
            "schema": "DemoTabletop1-oracle-guidance-v1",
            "fixture": public.FIXTURE,
            "fixture_truth_digest": ref["truth_digest"],
            "panorama_wh": [public.PANO_WIDTH, public.PANO_HEIGHT],
            "built_before_observer_control": True,
            "enumeration_source": "live reality1_scene.scene_objects(); ids and labels read, never hard-coded",
            "seed_rule": (
                "largest 8-connected component of the object's reference mask, then the deepest interior cell "
                "under a fixed 3/4 chamfer transform, ties by (-distance, y, x); identical rule for every object "
                "and for redirects; deliberately NOT the object centre"
            ),
            "validation_rule": (
                "reference first-hit range along each stereo sample's own direction; a sample is accepted when its "
                "first-hit instance matches the target and |range_stereo - range_ref| <= "
                f"max({public.DEPTH_GATE_ABS_M}, {public.DEPTH_GATE_REL}*range_ref)"
            ),
            "depth_semantics": "range = Euclidean distance from the fixed head origin, matching the project convention",
            "covered_dilation_cells": COVERED_DILATION_CELLS,
            "demo_coverage_target": DEMO_COVERAGE_TARGET,
            "min_redirect_component_cells": MIN_REDIRECT_COMPONENT_CELLS,
            "background_labels": list(public.BACKGROUND_LABELS),
            "occupied_crop_y0y1x0x1": crop,
            "objects": rows,
            "reference_products": {
                "rgb": "reference_rgb.png", "depth": "reference_depth.npy", "instance": "reference_instance.npy",
            },
        }
        return guidance

    def enumerate_objects(self, guidance: dict[str, Any]) -> list[DemoObject]:
        """Return deterministic positive objects; mark declared background labels."""
        bg = {str(x) for x in public.BACKGROUND_LABELS}
        objs = [
            DemoObject(int(r["object_id"]), str(r["label"]), str(r["label"]) in bg)
            for r in guidance["objects"] if int(r["object_id"]) > 0
        ]
        return sorted(objs, key=lambda o: o.object_id)

    def choose_oracle_seed_gaze(self, obj: DemoObject, guidance: dict[str, Any]) -> tuple[float, float]:
        """Choose a visible seed direction from reference support, not object centre by fiat."""
        for r in guidance["objects"]:
            if int(r["object_id"]) == int(obj.object_id):
                g = r.get("seed_gaze_deg")
                if g is None:
                    raise AssertionError(f"object {obj.object_id} has no visible reference support to seed from")
                return float(g[0]), float(g[1])
        raise AssertionError(f"object {obj.object_id} missing from guidance")

    # ---------- acquisition through the established path ----------

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
        p = subprocess.run(cmd, cwd=self.repo_root, text=True, capture_output=True)
        self.blender_launches += 1
        self.render_seconds += time.perf_counter() - t0
        (logs / f"render_{step:02d}.log").write_text(p.stdout + "\n--- STDERR ---\n" + p.stderr)
        if p.returncode != 0:
            raise RuntimeError(f"demo Blender fixation {step} failed; see {logs}")
        rr = json.loads((out / "run.json").read_text())
        if not rr.get("complete") or int(rr.get("step", -1)) != step:
            raise RuntimeError("incomplete or wrong demo acquisition record")
        if rr.get("fixture") != public.FIXTURE:
            raise RuntimeError(f"renderer fixture {rr.get('fixture')!r} is not {public.FIXTURE!r}")
        return out / f"fix_{step:02d}"

    def acquire_and_validate(self, obj: DemoObject, gaze_deg: tuple[float, float], global_step: int,
                             object_dir: Path, guidance: dict[str, Any]) -> dict[str, Any]:
        """Render one foveated binocular fixation, run established stereo, validate against truth.

        Required record: visible target pixels, raw valid stereo count, accepted/rejected
        counts, depth-error distribution for raw stereo, accepted geometry path, RGB paths,
        and proof that accepted xyz comes from stereo rather than reference depth.
        """
        if not self._kernel_checked:
            check_kernel_equivalence()
            self._kernel_checked = True
        oid = int(obj.object_id)
        case = self._render(int(global_step), gaze_deg, object_dir)
        c, obs = hdr.read_observation(case)
        rec, _meta, state = compute_once(c, obs)

        x, y, cw, ch = map(int, rec["crop_xywh"])
        sl = np.s_[y:y + ch, x:x + cw]
        ids_R = np.asarray(state["ids_right"])[sl]
        raw_R = np.asarray(support_mask(c, rec, "R"), bool)[sl]

        ids = np.asarray(rec["instance_id"])
        valid = np.asarray(rec["valid"], bool)
        target = valid & (ids == oid)

        # THE ONLY SOURCE OF FOREGROUND XYZ.
        stereo_xyz = np.asarray(rec["xyz_h"])[target]
        stereo_rgb = np.asarray(rec["rgb_left"])[target]
        stereo_ids = np.asarray(ids)[target]
        stereo_hash = _sha256_array(np.asarray(stereo_xyz, np.float64))

        n_raw = int(len(stereo_xyz))
        rgb_dir = object_dir / "rgb"
        rgb_dir.mkdir(parents=True, exist_ok=True)
        rgb_name = f"fix_{global_step:02d}.png"
        Image.fromarray(_tone_preview(rec["rgb_left"])).save(rgb_dir / rgb_name)

        if n_raw == 0:
            return {
                "object_id": oid, "case": str(case), "rgb": str(rgb_dir / rgb_name),
                "target_visible_pixels": int((ids == oid).sum()),
                "raw_valid_stereo_count": 0, "accepted_count": 0, "oracle_rejected_count": 0,
                "raw_depth_error_median_m": None, "raw_depth_error_p95_m": None,
                "accepted_depth_error_median_m": None, "accepted_depth_error_p95_m": None,
                "frame_valid_fraction": float(valid.mean()),
                "stereo_xyz_sha256": stereo_hash, "accepted_xyz_sha256": None,
                "accepted_is_row_subset_of_stereo": True,
                "reference_depth_supplied_foreground_values": False,
                "accepted_patch": None,
            }

        # Reference range along each stereo sample's OWN direction. Used to reject.
        rng_stereo = np.linalg.norm(np.asarray(stereo_xyz, np.float64), axis=1)
        dirs = np.asarray(stereo_xyz, np.float64) / np.maximum(rng_stereo, 1e-12)[:, None]
        rng_ref, ids_ref = ref_builder.reference_range_along(self._ref["mesh"], dirs)

        err = np.abs(rng_stereo - rng_ref)
        gate = np.maximum(public.DEPTH_GATE_ABS_M, public.DEPTH_GATE_REL * rng_ref)
        accept = np.isfinite(rng_ref) & (ids_ref == oid) & (err <= gate)

        accepted_xyz = stereo_xyz[accept]
        accepted_rgb = stereo_rgb[accept]
        accepted_ids = stereo_ids[accept]

        # --- runtime proof of the hard boundary ---
        subset_ok = _rows_subset(np.asarray(accepted_xyz, np.float64), np.asarray(stereo_xyz, np.float64))
        filter_ok = bool(np.array_equal(accepted_xyz, stereo_xyz[accept]))
        if not (subset_ok and filter_ok):
            raise AssertionError("accepted foreground xyz is not a pure filter of the stereo array")
        # The reference-derived positions are computed only to show they were NOT adopted.
        ref_xyz = dirs * np.where(np.isfinite(rng_ref), rng_ref, 0.0)[:, None]
        differs = int(np.count_nonzero(~np.all(np.isclose(accepted_xyz, ref_xyz[accept], rtol=0, atol=0), axis=1))) \
            if int(accept.sum()) else 0

        patch_path = None
        if int(accept.sum()):
            patches = object_dir / "patches"
            patches.mkdir(parents=True, exist_ok=True)
            patch_path = patches / f"fix_{global_step:02d}.npz"
            np.savez_compressed(
                patch_path,
                xyz_h=np.asarray(accepted_xyz, np.float32), rgb=np.asarray(accepted_rgb, np.float32),
                instance_id=np.asarray(accepted_ids), valid=valid, oracle_instance_id=ids,
                raw_support_L=np.asarray(rec["raw_support_L"], bool),
                oracle_instance_id_R=np.asarray(ids_R), raw_support_R=np.asarray(raw_R, bool),
                accepted_mask=np.asarray(accept, bool),
            )

        self._live.setdefault(oid, {"map": None, "gazes": [], "history": [], "rgb": [], "steps": []})
        live = self._live[oid]
        live["gazes"].append((float(gaze_deg[0]), float(gaze_deg[1])))
        live["steps"].append(int(global_step))
        live["rgb"].append(str(rgb_dir / rgb_name))
        live["history"].append(policy.history_entry(c, rec["instance_id"], rec["raw_support_L"], ids_R, raw_R, oid))

        a_err = err[accept]
        return {
            "object_id": oid,
            "case": str(case),
            "rgb": str(rgb_dir / rgb_name),
            "target_visible_pixels": int((ids == oid).sum()),
            "raw_valid_stereo_count": n_raw,
            "accepted_count": int(accept.sum()),
            "oracle_rejected_count": int((~accept).sum()),
            "rejected_wrong_instance": int(np.count_nonzero(np.isfinite(rng_ref) & (ids_ref != oid))),
            "rejected_gate": int(np.count_nonzero(np.isfinite(rng_ref) & (ids_ref == oid) & (err > gate))),
            "rejected_no_reference_hit": int(np.count_nonzero(~np.isfinite(rng_ref))),
            "raw_depth_error_median_m": float(np.median(err[np.isfinite(err)])) if np.isfinite(err).any() else None,
            "raw_depth_error_p95_m": float(np.percentile(err[np.isfinite(err)], 95)) if np.isfinite(err).any() else None,
            "accepted_depth_error_median_m": float(np.median(a_err)) if len(a_err) else None,
            "accepted_depth_error_p95_m": float(np.percentile(a_err, 95)) if len(a_err) else None,
            "frame_valid_fraction": float(valid.mean()),
            "target_depth_recovery_fraction": (float(n_raw / int((ids == oid).sum())) if int((ids == oid).sum()) else None),
            # hard-boundary provenance
            "stereo_xyz_sha256": stereo_hash,
            "stereo_xyz_shape": list(np.shape(stereo_xyz)),
            "accepted_xyz_sha256": _sha256_array(np.asarray(accepted_xyz, np.float64)),
            "accepted_xyz_shape": list(np.shape(accepted_xyz)),
            "accepted_is_row_subset_of_stereo": bool(subset_ok),
            "accepted_is_boolean_filter_of_stereo": bool(filter_ok),
            "accepted_rows_differing_from_reference_position": differs,
            "reference_depth_supplied_foreground_values": False,
            "reference_arrays_used_for": ["rejection", "instance_check"],
            "accepted_patch": (str(patch_path) if patch_path else None),
        }

    # ---------- fusion on accepted stereo only ----------

    def initialize_or_fuse(self, obj: DemoObject, measurement: dict[str, Any], object_dir: Path,
                           existing_map: Path | None) -> dict[str, Any]:
        """Use established surface-map initialization/fusion on ACCEPTED stereo geometry only."""
        oid = int(obj.object_id)
        p = measurement.get("accepted_patch")
        if not p:
            return {"map_path": (str(existing_map) if existing_map else None), "fused": False,
                    "reason": "no accepted stereo geometry", "new": 0, "matched": 0}
        with np.load(p, allow_pickle=False) as z:
            patch = Patch(f"fix_{int(measurement['global_step']):02d}",
                          np.asarray(z["xyz_h"], np.float64), np.asarray(z["rgb"], np.float64),
                          np.asarray(z["instance_id"]))
        maps = object_dir / "maps"
        maps.mkdir(parents=True, exist_ok=True)
        live = self._live[oid]

        if existing_map is None:
            if len(patch.xyz_h) < MIN_MAP_INIT_POINTS:
                return {"map_path": None, "fused": False,
                        "reason": f"accepted {len(patch.xyz_h)} < frozen initialize() minimum {MIN_MAP_INIT_POINTS}",
                        "new": 0, "matched": 0}
            sm = initialize(patch, oid)
            assoc = {"matched": 0, "new": int(len(sm.xyz_h))}
            idem = True
        else:
            sm = live["map"]
            sm, assoc = fuse(sm, patch, oid, self.fusion["association_radius_m"], self.fusion["hash_cell_m"])
            replay, dup = fuse(sm, patch, oid, self.fusion["association_radius_m"], self.fusion["hash_cell_m"])
            idem = bool(dup["duplicate_patch"] and np.array_equal(sm.xyz_h, replay.xyz_h)
                        and np.array_equal(sm.support_count, replay.support_count))
            if not idem:
                raise AssertionError("accepted-geometry fusion is not idempotent")
        if len(sm.instance_id) and set(np.unique(sm.instance_id).tolist()) != {oid}:
            raise AssertionError("demo foreground map lost instance purity")
        live["map"] = sm
        mp = maps / f"map_{int(measurement['global_step']):02d}.npz"
        save_map(mp, sm)
        return {"map_path": str(mp), "fused": True, "idempotent_replay": bool(idem),
                "matched": int(assoc.get("matched", 0)), "new": int(assoc.get("new", 0)),
                "map_points": int(len(sm.xyz_h))}

    # ---------- established frozen local FSG policy ----------

    def local_next_action(self, obj: DemoObject, object_dir: Path, history: list[dict[str, Any]],
                          current_map: Path) -> dict[str, Any]:
        """Replay/use established frozen local FSG policy; no new local controller here."""
        oid = int(obj.object_id)
        live = self._live[oid]
        sm = live["map"]
        if sm is None or not len(sm.xyz_h):
            return {"stop": True, "reason": "no_map", "next_gaze_deg": None}
        case = Path(history[-1]["case"])
        c, obs = hdr.read_observation(case)
        rec, _meta, state = compute_once(c, obs)
        x, y, cw, ch = map(int, rec["crop_xywh"])
        sl = np.s_[y:y + ch, x:x + cw]
        ids_R = np.asarray(state["ids_right"])[sl]
        raw_R = np.asarray(support_mask(c, rec, "R"), bool)[sl]
        g = live["gazes"][-1]
        d = policy.choose_next(g[0], g[1], c, rec["instance_id"], rec["raw_support_L"], ids_R, raw_R,
                               sm.xyz_h, live["gazes"], live["history"], oid)
        out = dict(d)
        ng = out.get("next_gaze_deg")
        if ng is not None and any(np.allclose(np.asarray(v), np.asarray(ng), atol=1e-9) for v in live["gazes"]):
            out["stop"] = True
            out["reason"] = "local_revisit_blocked"
            out["next_gaze_deg"] = None
        out["action_source"] = "LOCAL_FSG"
        return out

    # ---------- bounded oracle redirect ----------

    def _covered_mask(self, oid: int) -> np.ndarray:
        sm = self._live.get(oid, {}).get("map")
        covered = np.zeros((public.PANO_HEIGHT, public.PANO_WIDTH), bool)
        if sm is None or not len(sm.xyz_h):
            return covered
        yaw, pitch, rng = topo1a.xyz_to_angles(np.asarray(sm.xyz_h, np.float64))
        d, _i = export.spherical_zbuffer(yaw, pitch, rng, np.full(len(yaw), oid, np.int64),
                                         public.PANO_WIDTH, public.PANO_HEIGHT)
        covered = np.isfinite(d) & (d > 0)
        return topo1a.dilate(covered, COVERED_DILATION_CELLS)

    def oracle_uncovered_support(self, obj: DemoObject, guidance: dict[str, Any], current_map: Path | None,
                                 history: list[dict[str, Any]]) -> dict[str, Any]:
        """Measure remaining reference angular support and propose one deterministic redirect gaze."""
        oid = int(obj.object_id)
        inst = self._ref["instance"]
        depth = self._ref["depth"]
        ref_mask = np.isfinite(depth) & (depth > 0) & (inst == oid)
        total = int(ref_mask.sum())
        covered = self._covered_mask(oid) & ref_mask
        uncovered = ref_mask & ~covered
        frac = (float(covered.sum() / total) if total else 0.0)

        rec: dict[str, Any] = {
            "object_id": oid,
            "reference_support_cells": total,
            "covered_cells": int(covered.sum()),
            "uncovered_cells": int(uncovered.sum()),
            "reference_angular_coverage": frac,
            "demo_coverage_target": DEMO_COVERAGE_TARGET,
            "covered_dilation_cells": COVERED_DILATION_CELLS,
            "demo_target_satisfied": bool(frac >= DEMO_COVERAGE_TARGET),
            "next_gaze_deg": None,
            "action_source": "ORACLE_REDIRECT",
        }
        if rec["demo_target_satisfied"] or not uncovered.any():
            return rec
        comps = inherited_audit._components(uncovered)
        comps.sort(key=len, reverse=True)
        rec["largest_uncovered_component_cells"] = int(len(comps[0]))
        if len(comps[0]) < MIN_REDIRECT_COMPONENT_CELLS:
            rec["reason"] = "largest uncovered component below the fixed redirect minimum"
            return rec
        big = np.zeros_like(uncovered)
        big[comps[0][:, 0], comps[0][:, 1]] = True
        cell = ref_builder.deepest_interior_cell(big)
        if cell is None:
            return rec
        gy, gx = cell
        yaw, pitch = ref_builder.cell_to_gaze(gy, gx, public.PANO_WIDTH, public.PANO_HEIGHT)
        live = self._live.get(oid, {})
        for g in live.get("gazes", []):
            if abs(g[0] - yaw) < 1e-9 and abs(g[1] - pitch) < 1e-9:
                rec["reason"] = "deterministic redirect cell already visited"
                return rec
        rec["redirect_cell_yx"] = [int(gy), int(gx)]
        rec["next_gaze_deg"] = [float(yaw), float(pitch)]
        return rec

    def finalize_foreground_object(self, obj: DemoObject, object_dir: Path, current_map: Path | None,
                                   history: list[dict[str, Any]], stop_reason: str) -> dict[str, Any]:
        oid = int(obj.object_id)
        live = self._live.get(oid, {})
        sm = live.get("map")
        objects_dir = self.out / "objects"
        objects_dir.mkdir(parents=True, exist_ok=True)
        npz = objects_dir / f"object_{oid}.npz"
        ply = objects_dir / f"object_{oid}.ply"
        instantiated = bool(sm is not None and len(sm.xyz_h))
        if instantiated:
            save_map(npz, sm)
            fsg6run.save_ply(ply, sm)
        else:
            from fsg3_surface_map import SurfaceMap
            save_map(npz, SurfaceMap(np.zeros((0, 3), np.float32), np.zeros((0, 3), np.float32),
                                     np.zeros(0, np.int32), np.zeros(0, np.int16), np.zeros(0, np.uint64), []))
            ply.write_text("ply\nformat ascii 1.0\nelement vertex 0\n"
                           "property float x\nproperty float y\nproperty float z\nend_header\n")
        sup = self.oracle_uncovered_support(obj, {}, current_map, history)
        return {
            "instantiated": instantiated,
            "foreground_surfels": int(len(sm.xyz_h)) if instantiated else 0,
            "reference_support_cells": sup["reference_support_cells"],
            "reference_angular_coverage": sup["reference_angular_coverage"],
            "uncovered_cells": sup["uncovered_cells"],
            "raw_valid_stereo_total": int(sum(int(h.get("raw_valid_stereo_count", 0)) for h in history)),
            "accepted_total": int(sum(int(h.get("accepted_count", 0)) for h in history)),
            "oracle_rejected_total": int(sum(int(h.get("oracle_rejected_count", 0)) for h in history)),
            "map_npz": f"objects/object_{oid}.npz",
            "map_ply": f"objects/object_{oid}.ply",
        }

    # ---------- declared background scaffold ----------

    def build_background_scaffold(self, obj: DemoObject, guidance: dict[str, Any], object_dir: Path) -> dict[str, Any]:
        """Build explicitly oracle-sourced visual background with soft depth metadata.

        It must be exported separately and must not enter foreground point counts or purity metrics.
        """
        oid = int(obj.object_id)
        inst = self._ref["instance"]
        depth = self._ref["depth"]
        rgb = self._ref["rgb_linear"]
        mask = np.isfinite(depth) & (depth > 0) & (inst == oid)
        d = depth[mask].astype(np.float64)

        Image.fromarray((mask.astype(np.uint8) * 255)).save(self.out / "background_mask.png")
        tex = np.zeros_like(rgb)
        tex[mask] = rgb[mask]
        Image.fromarray(_tone_preview(tex)).save(self.out / "background_rgb.png")

        q = [5, 25, 50, 75, 95]
        soft = {
            "schema": "DemoTabletop1-background-soft-depth-v1",
            "object_id": oid,
            "label": obj.label,
            "layer": "BACKGROUND_SCAFFOLD",
            "provenance": "ORACLE_REFERENCE_DEPTH",
            "is_stereo_reconstruction": False,
            "counted_in_foreground_totals": False,
            "how_computed": (
                "reference first-hit range sampled at every panorama cell whose reference instance equals this "
                "object; robust quantiles over those cells; no stereo measurement contributes"
            ),
            "cells": int(mask.sum()),
            "range_quantiles_m": {f"p{k}": float(np.percentile(d, k)) for k in q} if len(d) else {},
            "range_median_m": float(np.median(d)) if len(d) else None,
            "range_mean_m": float(d.mean()) if len(d) else None,
            "range_std_m": float(d.std()) if len(d) else None,
            "range_min_m": float(d.min()) if len(d) else None,
            "range_max_m": float(d.max()) if len(d) else None,
            "shell_kind": "constant-range spherical shell at the median, visualization only",
            "shell_range_m": float(np.median(d)) if len(d) else None,
        }
        (self.out / "background_soft_depth.json").write_text(json.dumps(soft, indent=2, sort_keys=True) + "\n")

        # Trivial visualization shell: the background mask at one constant range.
        shell_pts = np.zeros((0, 3), np.float64)
        if len(d):
            ys, xs = np.nonzero(mask)
            take = np.arange(0, len(ys), max(1, len(ys) // 20000))
            yaws = (xs[take] + 0.5) / public.PANO_WIDTH * 360.0 - 180.0
            pitches = 90.0 - (ys[take] + 0.5) / public.PANO_HEIGHT * 180.0
            shell_pts = topo1a.angles_to_dir(yaws, pitches) * float(np.median(d))
            export.write_ascii_ply(object_dir / f"object_{oid}_background_shell.ply", shell_pts,
                                   np.full(len(shell_pts), oid, np.int64))
        return {
            "layer": "BACKGROUND_SCAFFOLD",
            "provenance": "ORACLE_REFERENCE_DEPTH",
            "is_stereo_reconstruction": False,
            "counted_in_foreground_totals": False,
            "background_mask": "background_mask.png",
            "background_rgb": "background_rgb.png",
            "background_soft_depth": "background_soft_depth.json",
            "background_shell_ply": f"objects/object_{oid}/object_{oid}_background_shell.ply",
            "shell_points": int(len(shell_pts)),
            "reference_support_cells": int(mask.sum()),
            "foreground_surfels": 0,
            "fixations": 0,
            "oracle_redirects": 0,
            "stop_reason": "DECLARED_BACKGROUND_NO_CONTROL",
        }

    # ---------- exports ----------

    def export_demo(self, object_rows: list[dict[str, Any]], guidance: dict[str, Any],
                    fixation_history: list[dict[str, Any]], out: Path) -> dict[str, Any]:
        """Export observer foreground, oracle background, provenance-preserving composite and timeline."""
        fg_rows = [r for r in object_rows if r.get("role") == "STEREO_FOREGROUND"]
        bg_rows = [r for r in object_rows if r.get("role") == "BACKGROUND_SCAFFOLD"]

        xyz_all, oid_all, rgb_all, sup_all = [], [], [], []
        per_object: dict[str, int] = {}
        for r in fg_rows:
            oid = int(r["object_id"])
            sm = self._live.get(oid, {}).get("map")
            if sm is None or not len(sm.xyz_h):
                per_object[str(oid)] = 0
                continue
            xyz_all.append(np.asarray(sm.xyz_h, np.float64).reshape(-1, 3))
            oid_all.append(np.full(len(sm.xyz_h), oid, np.int64))
            rgb_all.append(np.asarray(sm.rgb, np.float64).reshape(-1, 3))
            sup_all.append(np.asarray(sm.support_count).reshape(-1))
            per_object[str(oid)] = int(len(sm.xyz_h))

        xyz = np.concatenate(xyz_all) if xyz_all else np.zeros((0, 3))
        oids = np.concatenate(oid_all) if oid_all else np.zeros(0, np.int64)
        rgb_lin = np.concatenate(rgb_all) if rgb_all else np.zeros((0, 3))
        sup = np.concatenate(sup_all) if sup_all else np.zeros(0)
        rgb8 = _tone_preview(rgb_lin) if len(rgb_lin) else np.zeros((0, 3), np.uint8)

        export.write_scene_npz(out / "foreground_scene_points.npz", xyz, oids, sup, rgb8)
        export.write_ascii_ply(out / "foreground_scene_points.ply", xyz, oids, rgb8)

        yaw, pitch, rng = topo1a.xyz_to_angles(xyz)
        fdepth, finst = export.spherical_zbuffer(yaw, pitch, rng, oids, public.PANO_WIDTH, public.PANO_HEIGHT)
        np.save(out / "foreground_depth.npy", fdepth)
        np.save(out / "foreground_instance.npy", finst)
        fvalid = np.isfinite(fdepth) & (fdepth > 0)
        Image.fromarray((fvalid.astype(np.uint8) * 255)).save(out / "foreground_valid.png")
        Image.fromarray(export.depth_preview(fdepth)).save(out / "foreground_depth_preview.png")

        mosaic = np.zeros((public.PANO_HEIGHT, public.PANO_WIDTH, 3), np.uint8)
        if len(xyz):
            good = np.isfinite(yaw) & np.isfinite(pitch) & (rng > 0)
            gx = np.clip(np.floor(((yaw[good] + 180.0) % 360.0) / 360.0 * public.PANO_WIDTH).astype(np.int64),
                         0, public.PANO_WIDTH - 1)
            gy = np.clip(np.floor((90.0 - np.clip(pitch[good], -90.0, 90.0)) / 180.0 * public.PANO_HEIGHT).astype(np.int64),
                         0, public.PANO_HEIGHT - 1)
            order = np.argsort(-rng[good], kind="stable")
            mosaic[gy[order], gx[order]] = rgb8[good][order]
        Image.fromarray(mosaic).save(out / "foreground_rgb_mosaic.png")

        # --- composite: foreground first, background scaffold only where foreground is absent ---
        ref_rgb8 = _tone_preview(self._ref["rgb_linear"])
        bg_mask = np.zeros((public.PANO_HEIGHT, public.PANO_WIDTH), bool)
        bg_range = None
        for r in bg_rows:
            oid = int(r["object_id"])
            bg_mask |= (self._ref["instance"] == oid) & np.isfinite(self._ref["depth"])
            soft = json.loads((out / "background_soft_depth.json").read_text())
            bg_range = soft.get("shell_range_m")

        demo_rgb = np.zeros_like(ref_rgb8)
        demo_rgb[bg_mask] = ref_rgb8[bg_mask]
        fg_px = fvalid.copy()
        demo_rgb[fg_px] = mosaic[fg_px]
        Image.fromarray(demo_rgb).save(out / "demo_rgb.png")

        demo_depth = np.full((public.PANO_HEIGHT, public.PANO_WIDTH), np.nan, np.float32)
        if bg_range is not None:
            demo_depth[bg_mask] = np.float32(bg_range)
        demo_depth[fg_px] = fdepth[fg_px]
        np.save(out / "demo_depth.npy", demo_depth)
        Image.fromarray(export.depth_preview(demo_depth)).save(out / "demo_depth_preview.png")

        demo_inst = np.zeros((public.PANO_HEIGHT, public.PANO_WIDTH), np.int32)
        for r in bg_rows:
            demo_inst[bg_mask] = np.int32(int(r["object_id"]))
        demo_inst[fg_px] = finst[fg_px]
        np.save(out / "demo_instance.npy", demo_inst)

        # Per-pixel layer provenance: 0 empty, 1 stereo foreground, 2 oracle background.
        layer = np.zeros((public.PANO_HEIGHT, public.PANO_WIDTH), np.uint8)
        layer[bg_mask] = 2
        layer[fg_px] = 1
        np.save(out / "demo_layer.npy", layer)
        prov = {
            "schema": "DemoTabletop1-layer-provenance-v1",
            "layers": {
                "0": {"name": "EMPTY", "source": "none"},
                "1": {"name": "STEREO_FOREGROUND",
                      "source": "foveated binocular render -> established stereo -> oracle validity gate -> 12 mm fusion",
                      "metric_geometry_from": "stereo", "pixels": int(fg_px.sum())},
                "2": {"name": "BACKGROUND_SCAFFOLD",
                      "source": "declared oracle background: reference RGB texture and reference soft-depth range",
                      "metric_geometry_from": "reference (NOT stereo)", "pixels": int((layer == 2).sum())},
            },
            "composite_is_autonomous_reconstruction": False,
            "foreground_pixels": int(fg_px.sum()),
            "background_pixels": int((layer == 2).sum()),
            "foreground_surfels_total": int(len(xyz)),
            "foreground_surfels_per_object": per_object,
            "background_surfels_counted_in_foreground": 0,
            "background_labels": list(public.BACKGROUND_LABELS),
            "layer_raster": "demo_layer.npy",
        }
        (out / "demo_layer_provenance.json").write_text(json.dumps(prov, indent=2, sort_keys=True) + "\n")

        timeline = self._timeline(fixation_history, guidance, out)
        movie = self._movie(out, timeline)

        return {
            "foreground_scene_points_npz": "foreground_scene_points.npz",
            "foreground_scene_points_ply": "foreground_scene_points.ply",
            "foreground_depth": "foreground_depth.npy",
            "foreground_instance": "foreground_instance.npy",
            "foreground_valid": "foreground_valid.png",
            "foreground_depth_preview": "foreground_depth_preview.png",
            "foreground_rgb_mosaic": "foreground_rgb_mosaic.png",
            "background_mask": "background_mask.png",
            "background_rgb": "background_rgb.png",
            "background_soft_depth": "background_soft_depth.json",
            "demo_rgb": "demo_rgb.png",
            "demo_depth": "demo_depth.npy",
            "demo_depth_preview": "demo_depth_preview.png",
            "demo_instance": "demo_instance.npy",
            "demo_layer_provenance": "demo_layer_provenance.json",
            "reference_rgb": "reference_rgb.png",
            "reference_depth": "reference_depth.npy",
            "reference_instance": "reference_instance.npy",
            "timeline_frames": len(timeline),
            "timeline_dir": "timeline",
            "movie": movie,
            "foreground_surfels_total": int(len(xyz)),
            "foreground_surfels_per_object": per_object,
            "foreground_panorama_pixels": int(fvalid.sum()),
            "blender_launches": int(self.blender_launches),
            "render_seconds": float(self.render_seconds),
        }

    # ---------- visual story ----------

    def _timeline(self, fixation_history: list[dict[str, Any]], guidance: dict[str, Any], out: Path) -> list[str]:
        """One frame per fixation: the look, and the scene accumulated up to it."""
        tl = out / "timeline"
        tl.mkdir(parents=True, exist_ok=True)
        y0, y1, x0, x1 = guidance.get("occupied_crop_y0y1x0x1", [0, public.PANO_HEIGHT, 0, public.PANO_WIDTH])
        ref_rgb8 = _tone_preview(self._ref["rgb_linear"])[y0:y1, x0:x1]
        acc_xyz: list[np.ndarray] = []
        acc_oid: list[np.ndarray] = []
        acc_rgb: list[np.ndarray] = []
        frames: list[str] = []
        for m in sorted(fixation_history, key=lambda r: int(r["global_step"])):
            p = m.get("accepted_patch")
            if p and Path(p).is_file():
                with np.load(p, allow_pickle=False) as z:
                    acc_xyz.append(np.asarray(z["xyz_h"], np.float64))
                    acc_oid.append(np.full(len(z["xyz_h"]), int(m["object_id"]), np.int64))
                    acc_rgb.append(np.asarray(z["rgb"], np.float64))
            if acc_xyz:
                X = np.concatenate(acc_xyz); O = np.concatenate(acc_oid); R = _tone_preview(np.concatenate(acc_rgb))
                yaw, pitch, rng = topo1a.xyz_to_angles(X)
                good = np.isfinite(yaw) & np.isfinite(pitch) & (rng > 0)
                canvas = np.zeros((public.PANO_HEIGHT, public.PANO_WIDTH, 3), np.uint8)
                gx = np.clip(np.floor(((yaw[good] + 180.0) % 360.0) / 360.0 * public.PANO_WIDTH).astype(np.int64), 0, public.PANO_WIDTH - 1)
                gy = np.clip(np.floor((90.0 - np.clip(pitch[good], -90.0, 90.0)) / 180.0 * public.PANO_HEIGHT).astype(np.int64), 0, public.PANO_HEIGHT - 1)
                order = np.argsort(-rng[good], kind="stable")
                canvas[gy[order], gx[order]] = R[good][order]
                scene = canvas[y0:y1, x0:x1]
            else:
                scene = np.zeros_like(ref_rgb8)
            look = np.asarray(Image.open(m["rgb"]).convert("RGB"))
            h = max(look.shape[0], scene.shape[0])
            sc = Image.fromarray(scene)
            sc = sc.resize((int(sc.width * h / sc.height), h), Image.NEAREST)
            lk = Image.fromarray(look).resize((int(look.shape[1] * h / look.shape[0]), h), Image.NEAREST)
            frame = Image.new("RGB", (lk.width + sc.width + 12, h), (16, 16, 18))
            frame.paste(lk, (0, 0)); frame.paste(sc, (lk.width + 12, 0))
            name = f"fix_{int(m['global_step']):03d}.png"
            frame.save(tl / name)
            frames.append(f"timeline/{name}")
        return frames

    def _movie(self, out: Path, frames: list[str]) -> str | None:
        if not frames or shutil.which("ffmpeg") is None:
            return None
        first = Image.open(out / frames[0])
        w, h = first.width - first.width % 2, first.height - first.height % 2
        cmd = ["ffmpeg", "-y", "-framerate", "2", "-i", str(out / "timeline" / "fix_%03d.png"),
               "-vf", f"crop={w}:{h}:0:0,format=yuv420p", "-c:v", "libx264", "-preset", "medium",
               str(out / "demo.mp4")]
        p = subprocess.run(cmd, capture_output=True, text=True)
        (out / "logs").mkdir(parents=True, exist_ok=True)
        (out / "logs" / "ffmpeg.log").write_text(p.stdout + "\n--- STDERR ---\n" + p.stderr)
        return "demo.mp4" if p.returncode == 0 and (out / "demo.mp4").is_file() else None
