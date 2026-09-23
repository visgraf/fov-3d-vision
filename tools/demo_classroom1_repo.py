"""Repository seam for Demo-Classroom-1, oracle-attention mode.

This is deliberately a concept demo rather than a controller experiment.
Blender truth may guide object grouping, ALL gaze choices, and rejection.
The hard boundary is unchanged: evaluator/reference xyz/depth must never be
inserted as metric foreground reconstruction.

Only new Demo-Classroom-1 files may be changed to bind this seam unless a
new genuine blocker is reported first.

BOUND TO THE LIVE REPOSITORY.

Acquisition and stereo are the established Classroom (Phase A-C) path, used
unchanged: tools/fixation_pairs.py PairRenderer/foveated warp for the verged
binocular fixation, and tools/stereo_field.py field_of_pair for the
established Classroom foveated stereo front end. Their rows are converted to
the existing FSG Patch/head-xyz convention and fused by the established 12 mm
surface map, which is representation-independent.

Attention is ORACLE_REFERENCE_SUPPORT for every fixation. The previously
reported absence of an FSG6f/.blend controller bridge is not worked around
here: no local controller is invoked at all, by ruling. FSG6f, cyclopean1a
select_probe and belief.Policy are all deliberately untouched.

THE HARD BOUNDARY, enforced per fixation in acquire_and_validate():
  * foreground xyz comes only from field_of_pair rows (dir / rho);
  * the accepted set is a boolean FILTER of that array, checked bitwise as a
    row-subset and by array hash;
  * reference range/instance only reject; the reference-derived position is
    computed solely to record that it was never adopted.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import time
from typing import Any

import numpy as np
from PIL import Image

import cyclopean1a_topology as topo1a
import demo_classroom1_public as public
import demo_tabletop1_reference as gaze_helpers          # scene-independent Tabletop helpers
import fsg6f_public as frozen_public
import fullscene_real1_export as export
import multiobject3d_audit as components
from fsg3_surface_map import Patch, SurfaceMap, fuse, initialize, load_map, save_map
from fsg_geometry import gaze_direction
from reality1_run import _tone_preview
from rig import eye_offsets_local
from stereo_field import field_of_pair

# --- Demo constants. Fixed for every object; none is tuned per object. ---
# Sparse point clouds never fill a panorama cell-for-cell, so "covered" is the
# accepted-foreground projection dilated by a fixed radius before comparison.
COVERED_DILATION_CELLS = 3
MIN_REDIRECT_COMPONENT_CELLS = 50
# The established renderer refuses a frame with too little geometry; the same
# lesson the Tabletop demo learned, applied here to oracle candidates.
FRAME_DEG = 12.8
MIN_FRAME_SCENE_FRACTION = 0.50
# Frozen FSG3 initialize() AND fuse() both refuse fewer than 100 points; this
# is also the inherited empty-look limit. No new threshold is introduced.
EMPTY_LOOK_LIMIT = 100
REFERENCE_SPP = 128
PAIR_DEVICE = "OPTIX"


@dataclass(frozen=True)
class DemoObject:
    object_id: int
    label: str
    source_group: str


def _sha256_array(a: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _rows_subset(sub: np.ndarray, sup: np.ndarray) -> bool:
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
        self.device = PAIR_DEVICE
        self.blender_launches = 0
        self.render_seconds = 0.0
        self._ref: dict[str, Any] = {}
        self._live: dict[int, dict[str, Any]] = {}
        self._plan: dict[str, Any] = {}
        # Bind the frozen 12 mm rule from its own source rather than restating it.
        self.fusion = dict(frozen_public.FUSION)

    # ---------- preflight ----------

    def _blender(self, script: str, extra: list[str], tag: str) -> None:
        cmd = [self.blender, "-b", "--python-exit-code", "1", "-P", script, "--"] + extra
        t0 = time.perf_counter()
        p = subprocess.run(cmd, cwd=self.repo_root, text=True, capture_output=True)
        self.blender_launches += 1
        self.render_seconds += time.perf_counter() - t0
        logs = self.out / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        (logs / f"{tag}.log").write_text(p.stdout + "\n--- STDERR ---\n" + p.stderr)
        if p.returncode != 0:
            raise RuntimeError(f"Blender step {tag!r} failed; see {logs / (tag + '.log')}")

    def preflight_scene(self) -> dict[str, Any]:
        """Verify the live Classroom binding and acquisition/reference paths.

        This includes the .blend hash, metric EYE convention, renderability,
        dynamic grouping support, established Classroom foveated-pair renderer,
        stereo-field conversion, and reference-panorama path.  The previously
        reported lack of an FSG6f/.blend controller bridge is NOT a blocker in
        this mode because Classroom attention is explicitly oracle-driven.
        """
        blend = (self.repo_root / public.BLEND_REL).resolve()
        if not blend.is_file():
            raise FileNotFoundError(f"Classroom blend missing: {blend}")
        manifest = json.loads((self.repo_root / "scenes" / "manifest.json").read_text())
        entry = next((s for s in manifest["scenes"] if s.get("id") == public.SCENE_ID), None)
        if entry is None:
            raise AssertionError("scene manifest has no classroom entry")
        if entry.get("blend") != public.BLEND_REL:
            raise AssertionError("manifest blend path differs from the Classroom contract")

        work = self.out / "preflight"
        work.mkdir(parents=True, exist_ok=True)
        self._blender("tools/demo_classroom1_scene_blender.py",
                      ["--mode", "inspect", "--blend", str(blend), "--out", str(work)],
                      "preflight_inspect")
        facts = json.loads((work / "scene_inspect.json").read_text())

        if abs(float(facts["unit_scale"]) - 1.0) > 1e-9 or facts["unit_system"] != "METRIC":
            raise AssertionError("Classroom is not metric with unit scale 1.0")
        if not facts["eye"]["exists"]:
            raise AssertionError("no EYE camera in the Classroom blend")
        loc = np.asarray(facts["eye"]["location_m"], float)
        declared = np.asarray(entry["eye_position_m"], float)
        if np.max(np.abs(loc - declared)) > 1e-4:
            raise AssertionError(f"EYE pose {loc} differs from manifest {declared}")
        if int(facts["mesh_renderable"]) <= 0:
            raise AssertionError("no renderable mesh in the Classroom blend")

        ready = True
        return {
            "schema": "DemoClassroom1-scene-preflight-v2",
            "ready": ready,
            "controller_mode": public.CONTROLLER_MODE,
            "scene_rel": public.BLEND_REL,
            "scene_sha256": _sha256_file(blend),
            "scene_bytes": blend.stat().st_size,
            "manifest": {
                "id": entry["id"], "kind": entry["kind"], "tier": entry["tier"],
                "license": entry["license"], "eye_position_m": entry["eye_position_m"],
                "eye_yaw_deg": entry["eye_yaw_deg"], "eye_pitch_deg": entry["eye_pitch_deg"],
                "declared_checks": entry.get("checks"),
            },
            "live": facts,
            "eye_pose_matches_manifest": True,
            "acquisition_path": "tools/fixation_pairs.py PairRenderer (established Classroom foveated warp)",
            "stereo_path": "tools/stereo_field.py field_of_pair (established Classroom foveated stereo front end)",
            "fusion_path": "tools/fsg3_surface_map.py initialize/fuse, 12 mm, unchanged",
            "attention_path": f"{public.CONTROLLER_MODE}; no local controller is invoked",
            "local_controller_invoked": None,
            "fsg6f_bridge_built": False,
            "established_source_modified": False,
        }

    # ---------- reference + guidance ----------

    @staticmethod
    def _read_reference_exr(path: Path, layer: str) -> dict[str, np.ndarray]:
        import OpenEXR
        f = OpenEXR.File(str(path))
        ch = f.channels()

        def pick(suffix: str) -> np.ndarray:
            key = next(k for k in ch if k.endswith(suffix) and k.startswith(layer))
            return np.asarray(ch[key].pixels)

        return {
            "position": np.stack([pick("Position." + a) for a in "XYZ"], -1),
            "depth": pick("Depth.Z"),
            "index": np.asarray(next(v for k, v in ch.items() if "Object Index" in k).pixels),
            "rgb": np.asarray(next(v for k, v in ch.items() if k.endswith("Combined")).pixels)[..., :3],
        }

    def build_reference_and_guidance(self, preflight: dict[str, Any]) -> dict[str, Any]:
        """Build 2048x1024 reference RGB/depth/instance and oracle metadata.

        Truth is intentionally available before control in Demo Mode. Object
        identities/groups must be derived dynamically from the live .blend and
        the exact grouping rule must be recorded.
        """
        work = self.out / "preflight"
        blend = (self.repo_root / public.BLEND_REL).resolve()
        self._blender("tools/demo_classroom1_scene_blender.py",
                      ["--mode", "reference", "--blend", str(blend), "--out", str(work),
                       "--width", str(public.PANO_WIDTH), "--spp", str(REFERENCE_SPP),
                       "--device", self.device],
                      "reference_render")
        meta = json.loads((work / "reference_meta.json").read_text())
        arrays = self._read_reference_exr(work / "reference.exr", meta["view_layer"])

        origin = np.asarray(meta["head_origin_m"], float)
        rot = np.asarray(meta["head_rot3_world_from_local"], float)
        self._head_origin = origin
        self._head_rot3 = rot

        z = arrays["depth"]
        hit = np.isfinite(z) & (z > 0) & (z < 1e9)
        pos_head = (arrays["position"][hit] - origin) @ rot          # world -> head frame
        yaw, pitch, rng = topo1a.xyz_to_angles(pos_head)
        gid = arrays["index"][hit].astype(np.int64)
        rgb = arrays["rgb"][hit].astype(np.float64)

        W, H = public.PANO_WIDTH, public.PANO_HEIGHT
        depth_p, inst_p = export.spherical_zbuffer(yaw, pitch, rng, gid, W, H)
        # Re-bin RGB with the same nearest-range ordering the z-buffer uses.
        rgb_p = np.zeros((H, W, 3), np.float64)
        good = np.isfinite(yaw) & np.isfinite(pitch) & (rng > 0)
        gx = np.clip(np.floor(((yaw[good] + 180.0) % 360.0) / 360.0 * W).astype(np.int64), 0, W - 1)
        gy = np.clip(np.floor((90.0 - np.clip(pitch[good], -90.0, 90.0)) / 180.0 * H).astype(np.int64), 0, H - 1)
        order = np.argsort(-rng[good], kind="stable")
        rgb_p[gy[order], gx[order]] = rgb[good][order]

        np.save(self.out / "reference_depth.npy", depth_p)
        np.save(self.out / "reference_instance.npy", inst_p)
        Image.fromarray(_tone_preview(rgb_p)).save(self.out / "reference_rgb.png")
        self._ref = {"depth": depth_p, "instance": inst_p, "rgb": rgb_p}

        occupied = np.isfinite(depth_p) & (depth_p > 0)
        groups = {int(g["id"]): g for g in meta["groups"]}
        rows: list[dict[str, Any]] = []
        for g in sorted(np.unique(inst_p[occupied]).tolist()):
            g = int(g)
            mask = occupied & (inst_p == g)
            d = depth_p[mask].astype(np.float64)
            rows.append({
                "group_id": g,
                "root": groups.get(g, {}).get("root", "__UNASSIGNED__"),
                "members": int(groups.get(g, {}).get("members", 0)),
                "visible_cells": int(mask.sum()),
                "visible_fraction": float(mask.sum() / occupied.sum()),
                "range_median_m": float(np.median(d)),
                "range_p10_m": float(np.percentile(d, 10)),
                "range_p90_m": float(np.percentile(d, 90)),
            })

        ys, xs = np.nonzero(occupied)
        pad = 24
        crop = [int(max(0, ys.min() - pad)), int(min(H, ys.max() + 1 + pad)),
                int(max(0, xs.min() - pad)), int(min(W, xs.max() + 1 + pad))]

        return {
            "schema": "DemoClassroom1-oracle-guidance-v2",
            "scene_rel": public.BLEND_REL,
            "panorama_wh": [W, H],
            "reference_spp": REFERENCE_SPP,
            "built_before_observer_control": True,
            "head_origin_m": origin.tolist(),
            "head_rot3_world_from_local": rot.tolist(),
            "grouping_rule": meta["grouping_rule"],
            "grouping_source": "live .blend hierarchy; no Classroom object name is written in any Demo source",
            "mesh_renderable": int(meta["mesh_renderable"]),
            "group_count": int(meta["group_count"]),
            "groups_visible": int(len(rows)),
            "occupied_cells": int(occupied.sum()),
            "occupied_fraction": float(occupied.mean()),
            "unassigned_index_present": bool(any(r["group_id"] == 0 for r in rows)),
            "seed_rule": (
                "deepest interior cell of the group's largest 8-connected reference component under the "
                "shared fixed chamfer transform; identical rule for seed and continuation"
            ),
            "validation_rule": (
                "reference instance must equal the target group and "
                f"|range_stereo - range_ref| <= max({public.DEPTH_GATE_ABS_M}, {public.DEPTH_GATE_REL}*range_ref); "
                "ranges are measured from the fixed head origin"
            ),
            "covered_dilation_cells": COVERED_DILATION_CELLS,
            "demo_target_coverage": public.DEMO_TARGET_COVERAGE,
            "min_redirect_component_cells": MIN_REDIRECT_COMPONENT_CELLS,
            "min_frame_scene_fraction": MIN_FRAME_SCENE_FRACTION,
            "occupied_crop_y0y1x0x1": crop,
            "group_rows": rows,
            "reference_products": {"rgb": "reference_rgb.png", "depth": "reference_depth.npy",
                                   "instance": "reference_instance.npy"},
        }

    # ---------- scene-adaptive plan ----------

    def build_scene_plan(self, guidance: dict[str, Any]) -> dict[str, Any]:
        """Partition visible support into foreground entities + ONE background.

        Preferred rule: occupied reference-depth q70..q90 defines a soft far
        band; sufficiently supported nearer structural groups are explicit
        foreground targets; far/contextual support and otherwise-unassigned
        visible support are aggregated into __BACKGROUND__. Do not hand-pick
        Classroom object names.
        """
        depth = self._ref["depth"]
        occupied = np.isfinite(depth) & (depth > 0)
        d = depth[occupied].astype(np.float64)
        d_near = float(np.quantile(d, public.BACKGROUND_NEAR_QUANTILE))
        d_far = float(np.quantile(d, public.BACKGROUND_FAR_QUANTILE))
        span = max(d_far - d_near, 1e-9)

        def bg_weight(x: np.ndarray) -> np.ndarray:
            t = np.clip((np.asarray(x, float) - d_near) / span, 0.0, 1.0)
            return t * t * (3.0 - 2.0 * t)          # smoothstep across [d_near, d_far]

        fg_rows: list[dict[str, Any]] = []
        bg_groups: list[dict[str, Any]] = []
        considered: list[dict[str, Any]] = []
        for r in guidance["group_rows"]:
            g = int(r["group_id"])
            mask = occupied & (self._ref["instance"] == g)
            w = float(np.mean(bg_weight(depth[mask].astype(np.float64)))) if mask.any() else 1.0
            rec = dict(r, mean_background_weight=w)
            enough = r["visible_fraction"] >= public.MIN_FOREGROUND_SUPPORT_FRACTION
            unassigned = (g == 0)
            foregroundish = w < 0.5
            rec.update({"has_min_support": bool(enough), "foreground_like": bool(foregroundish),
                        "unassigned_group": bool(unassigned)})
            considered.append(rec)
            if enough and foregroundish and not unassigned:
                fg_rows.append(rec)
            else:
                bg_groups.append(rec)

        fg_rows.sort(key=lambda x: int(x["group_id"]))
        objects = [{"object_id": int(r["group_id"]), "label": str(r["root"]),
                    "source_group": str(r["root"]), "visible_cells": int(r["visible_cells"]),
                    "visible_fraction": float(r["visible_fraction"]),
                    "range_median_m": float(r["range_median_m"]),
                    "mean_background_weight": float(r["mean_background_weight"])}
                   for r in fg_rows]

        bg_ids = sorted(int(r["group_id"]) for r in bg_groups)
        bg_mask = occupied & np.isin(self._ref["instance"], bg_ids)
        self._plan = {"background_ids": bg_ids, "bg_mask": bg_mask}

        return {
            "schema": "DemoClassroom1-scene-plan-v2",
            "foreground_objects": objects,
            "background": {
                "object_key": public.BACKGROUND_OBJECT_KEY,
                "aggregated_group_ids": bg_ids,
                "aggregated_group_count": len(bg_ids),
                "aggregated_roots": [str(r["root"]) for r in sorted(bg_groups, key=lambda x: int(x["group_id"]))],
                "visible_cells": int(bg_mask.sum()),
                "visible_fraction": float(bg_mask.sum() / occupied.sum()),
                "includes_unassigned_index0": bool(any(int(r["group_id"]) == 0 for r in bg_groups)),
            },
            "decomposition": {
                "rule": (
                    "occupied reference depth quantiles define a soft far band; a structural group is an explicit "
                    "foreground target when its visible fraction reaches min_foreground_support_fraction AND its "
                    "mean smoothstep background weight over the band is below 0.5; every other visible group, "
                    "including any unassigned index-0 support, is aggregated into the single background object"
                ),
                "near_quantile": public.BACKGROUND_NEAR_QUANTILE,
                "far_quantile": public.BACKGROUND_FAR_QUANTILE,
                "d_near_m": d_near,
                "d_far_m": d_far,
                "band_weight": "smoothstep t*t*(3-2t) on (range - d_near)/(d_far - d_near)",
                "min_foreground_support_fraction": public.MIN_FOREGROUND_SUPPORT_FRACTION,
                "occupied_cells": int(occupied.sum()),
                "occupied_range_median_m": float(np.median(d)),
                "groups_considered": len(considered),
                "groups_foreground": len(objects),
                "groups_background": len(bg_ids),
                "per_group": considered,
            },
        }

    # ---------- oracle attention ----------

    def _scene_occupancy(self) -> np.ndarray:
        occ = self._ref.get("_occ")
        if occ is None:
            occ = np.isfinite(self._ref["depth"]) & (self._ref["depth"] > 0)
            self._ref["_occ"] = occ
        return occ

    def _frame_scene_fraction(self, yaw: float, pitch: float) -> float:
        occ = self._scene_occupancy()
        h, w = occ.shape
        half = int(round(FRAME_DEG / (360.0 / w) / 2.0))
        x = int(np.floor(((float(yaw) + 180.0) % 360.0) / 360.0 * w))
        y = int(np.floor((90.0 - float(pitch)) / 180.0 * h))
        win = occ[max(0, y - half):min(h, y + half + 1), max(0, x - half):min(w, x + half + 1)]
        return float(win.mean()) if win.size else 0.0

    def _pick_gaze(self, mask: np.ndarray, visited: list[tuple[float, float]]) -> dict[str, Any]:
        cands = gaze_helpers.interior_cells_deepest_first(mask, limit=64)
        skipped_visited = skipped_frame = 0
        for gy, gx in cands:
            yaw, pitch = gaze_helpers.cell_to_gaze(gy, gx, public.PANO_WIDTH, public.PANO_HEIGHT)
            if any(abs(v[0] - yaw) < 1e-9 and abs(v[1] - pitch) < 1e-9 for v in visited):
                skipped_visited += 1
                continue
            frac = self._frame_scene_fraction(yaw, pitch)
            if frac < MIN_FRAME_SCENE_FRACTION:
                skipped_frame += 1
                continue
            return {"cell_yx": [int(gy), int(gx)], "gaze_deg": [float(yaw), float(pitch)],
                    "frame_scene_fraction": frac, "candidates_considered": len(cands),
                    "skipped_already_visited": skipped_visited, "skipped_frame_too_empty": skipped_frame}
        return {"gaze_deg": None, "candidates_considered": len(cands),
                "skipped_already_visited": skipped_visited, "skipped_frame_too_empty": skipped_frame}

    def _target_mask(self, oid: int) -> np.ndarray:
        occ = self._scene_occupancy()
        return occ & (self._ref["instance"] == int(oid))

    def choose_oracle_seed_gaze(self, obj: DemoObject, guidance: dict[str, Any]) -> tuple[float, float]:
        """Choose a deterministic visible/deep-interior seed from reference support."""
        mask = self._target_mask(obj.object_id)
        comps = components._components(mask)
        if not comps:
            raise AssertionError(f"group {obj.object_id} has no visible reference support to seed from")
        comps.sort(key=len, reverse=True)
        big = np.zeros_like(mask)
        big[comps[0][:, 0], comps[0][:, 1]] = True
        pick = self._pick_gaze(big, [])
        if pick.get("gaze_deg") is None:
            raise AssertionError(f"group {obj.object_id} has no admissible seed gaze")
        self._live.setdefault(int(obj.object_id), {"map": None, "gazes": [], "steps": [], "rgb": []})
        return float(pick["gaze_deg"][0]), float(pick["gaze_deg"][1])

    def _covered_mask(self, oid: int) -> np.ndarray:
        sm = self._live.get(int(oid), {}).get("map")
        blank = np.zeros((public.PANO_HEIGHT, public.PANO_WIDTH), bool)
        if sm is None or not len(sm.xyz_h):
            return blank
        yaw, pitch, rng = topo1a.xyz_to_angles(np.asarray(sm.xyz_h, np.float64))
        d, _i = export.spherical_zbuffer(yaw, pitch, rng, np.full(len(yaw), int(oid), np.int64),
                                         public.PANO_WIDTH, public.PANO_HEIGHT)
        return topo1a.dilate(np.isfinite(d) & (d > 0), COVERED_DILATION_CELLS)

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
        oid = int(obj.object_id)
        ref_mask = self._target_mask(oid)
        total = int(ref_mask.sum())
        covered = self._covered_mask(oid) & ref_mask
        uncovered = ref_mask & ~covered
        frac = float(covered.sum() / total) if total else 0.0
        live = self._live.get(oid, {})
        rec: dict[str, Any] = {
            "object_id": oid,
            "action_source": "ORACLE_UNCOVERED_SUPPORT",
            "reference_support_cells": total,
            "covered_cells": int(covered.sum()),
            "uncovered_cells": int(uncovered.sum()),
            "reference_coverage": frac,
            "demo_target_coverage": public.DEMO_TARGET_COVERAGE,
            "covered_dilation_cells": COVERED_DILATION_CELLS,
            "demo_target_satisfied": bool(frac >= public.DEMO_TARGET_COVERAGE),
            "next_gaze_deg": None,
        }
        if rec["demo_target_satisfied"] or not uncovered.any():
            return rec
        comps = components._components(uncovered)
        comps.sort(key=len, reverse=True)
        rec["largest_uncovered_component_cells"] = int(len(comps[0]))
        if len(comps[0]) < MIN_REDIRECT_COMPONENT_CELLS:
            rec["reason"] = "largest uncovered component below the fixed minimum"
            return rec
        big = np.zeros_like(uncovered)
        big[comps[0][:, 0], comps[0][:, 1]] = True
        pick = self._pick_gaze(big, list(live.get("gazes", [])))
        rec.update({k: v for k, v in pick.items() if k != "gaze_deg"})
        if pick.get("gaze_deg") is None:
            rec["reason"] = "no unvisited candidate satisfied the renderer scene-occupancy precondition"
            return rec
        rec["next_cell_yx"] = pick["cell_yx"]
        rec["next_gaze_deg"] = list(pick["gaze_deg"])
        return rec

    # ---------- acquisition through the established Classroom path ----------

    def _fixation_point_world(self, gaze_deg: tuple[float, float]) -> tuple[list[float], float]:
        """Oracle gaze + reference range -> the world point the established rig verges on."""
        yaw, pitch = float(gaze_deg[0]), float(gaze_deg[1])
        W, H = public.PANO_WIDTH, public.PANO_HEIGHT
        x = int(np.clip(np.floor(((yaw + 180.0) % 360.0) / 360.0 * W), 0, W - 1))
        y = int(np.clip(np.floor((90.0 - pitch) / 180.0 * H), 0, H - 1))
        z = float(self._ref["depth"][y, x])
        if not np.isfinite(z) or z <= 0:
            z = float(np.nanmedian(self._ref["depth"][self._scene_occupancy()]))
        d_head = gaze_direction(yaw, pitch)
        p = self._head_origin + self._head_rot3 @ (d_head * z)
        return [float(v) for v in p], z

    def acquire_and_validate(self, obj: DemoObject, gaze_deg: tuple[float, float], global_step: int,
                             object_dir: Path, guidance: dict[str, Any]) -> dict[str, Any]:
        """Render one Classroom foveated stereo fixation and validate with truth.

        Reuse the established Classroom PairRenderer/foveated warp and stereo
        field. Convert valid target stereo samples to the FSG Patch convention,
        then apply the demo reference-depth gate. The returned record must prove
        accepted xyz is a pure row-subset/filter of stereo xyz and that no
        reference xyz was substituted.
        """
        oid = int(obj.object_id)
        blend = (self.repo_root / public.BLEND_REL).resolve()
        pair_dir = object_dir / "acquisition" / f"fix_{global_step:03d}"
        point, ref_z = self._fixation_point_world(gaze_deg)
        self._blender(
            "tools/fixation_pairs.py",
            ["--blend", str(blend), "--out", str(pair_dir),
             f"--points={point[0]:.9g},{point[1]:.9g},{point[2]:.9g}",
             "--profile", public.PROFILE, "--device", self.device, "--seed-pair"],
            f"pair_{global_step:03d}")

        pj = json.loads((pair_dir / "pairs.json").read_text())
        p0 = pj["pairs"][0]
        s0 = float(pj["warp"]["s0_deg"]); E2 = float(pj["warp"]["E2_deg"])
        emax = float(pj["warp"]["e_max_deg"]); ipd = float(pj["rig"]["ipd_m"])

        from stereo_field import load as load_eye
        L = load_eye(str(pair_dir / "L" / "f000"), True)
        R = load_eye(str(pair_dir / "R" / "f000"), True)
        vals = np.load(pair_dir / "L" / "f000" / "samples.npz")["value"].astype(np.float64)
        extras = {"r": vals[:, 0], "g": vals[:, 1], "b": vals[:, 2]}
        gL = gaze_direction(p0["eyes"][0]["yaw"], p0["eyes"][0]["pitch"])
        gR = gaze_direction(p0["eyes"][1]["yaw"], p0["eyes"][1]["pitch"])
        f = field_of_pair(L, R, gL, gR, s0, E2, emax, ipd, extras=extras)

        con = np.asarray(f["consistent"], bool)
        rho = np.asarray(f["rho"], float)
        good = con & np.isfinite(rho) & (rho > 0)
        dirs = np.asarray(f["dir"], float)[good]
        offset_L = np.asarray(eye_offsets_local(ipd), float)[0]
        # THE ONLY SOURCE OF FOREGROUND XYZ. rho is inverse distance from C_L.
        stereo_xyz = offset_L[None, :] + dirs * (1.0 / rho[good])[:, None]
        stereo_rgb = np.stack([np.asarray(f["x_r"], float)[good],
                               np.asarray(f["x_g"], float)[good],
                               np.asarray(f["x_b"], float)[good]], -1)
        stereo_hash = _sha256_array(stereo_xyz)

        rgb_dir = object_dir / "rgb"
        rgb_dir.mkdir(parents=True, exist_ok=True)
        rgb_name = f"fix_{global_step:03d}.png"
        self._save_look_preview(pair_dir, rgb_dir / rgb_name)

        base = {
            "object_id": oid, "label": obj.label, "source_group": obj.source_group,
            "acquisition": str(pair_dir), "rgb": str(rgb_dir / rgb_name),
            "fixation_point_world_m": point, "fixation_reference_range_m": ref_z,
            "stereo_rows_total": int(len(rho)), "stereo_rows_consistent": int(con.sum()),
            "raw_valid_stereo_count": int(len(stereo_xyz)),
            "stereo_xyz_sha256": stereo_hash, "stereo_xyz_shape": list(stereo_xyz.shape),
            "reference_depth_supplied_foreground_values": False,
            "reference_arrays_used_for": ["rejection", "instance_check", "gaze_guidance"],
        }
        if not len(stereo_xyz):
            return {**base, "accepted_count": 0, "oracle_rejected_count": 0,
                    "accepted_is_row_subset_of_stereo": True, "accepted_patch": None,
                    "raw_depth_error_median_m": None, "raw_depth_error_p95_m": None,
                    "accepted_depth_error_median_m": None, "accepted_depth_error_p95_m": None,
                    "target_visible_reference_cells": int(self._target_mask(oid).sum())}

        # Validation: look the reconstructed point up in the reference panorama
        # along its OWN direction from the fixed head origin.
        yaw, pitch, rng = topo1a.xyz_to_angles(stereo_xyz)
        W, H = public.PANO_WIDTH, public.PANO_HEIGHT
        gx = np.clip(np.floor(((yaw + 180.0) % 360.0) / 360.0 * W).astype(np.int64), 0, W - 1)
        gy = np.clip(np.floor((90.0 - np.clip(pitch, -90.0, 90.0)) / 180.0 * H).astype(np.int64), 0, H - 1)
        ref_rng = self._ref["depth"][gy, gx].astype(np.float64)
        ref_id = self._ref["instance"][gy, gx].astype(np.int64)
        err = np.abs(rng - ref_rng)
        gate = np.maximum(public.DEPTH_GATE_ABS_M, public.DEPTH_GATE_REL * ref_rng)
        accept = np.isfinite(ref_rng) & (ref_rng > 0) & (ref_id == oid) & (err <= gate)

        accepted_xyz = stereo_xyz[accept]
        accepted_rgb = stereo_rgb[accept]
        subset_ok = _rows_subset(accepted_xyz, stereo_xyz)
        filter_ok = bool(np.array_equal(accepted_xyz, stereo_xyz[accept]))
        if not (subset_ok and filter_ok):
            raise AssertionError("accepted foreground xyz is not a pure filter of the stereo array")
        # Reference-derived positions, computed ONLY to record they were not adopted.
        ref_xyz = (stereo_xyz / np.maximum(rng, 1e-12)[:, None]) * np.where(np.isfinite(ref_rng), ref_rng, 0.0)[:, None]
        differs = int(np.count_nonzero(~np.all(accepted_xyz == ref_xyz[accept], axis=1))) if int(accept.sum()) else 0

        patch_path = None
        if int(accept.sum()):
            patches = object_dir / "patches"
            patches.mkdir(parents=True, exist_ok=True)
            patch_path = patches / f"fix_{global_step:03d}.npz"
            np.savez_compressed(patch_path,
                                xyz_h=np.asarray(accepted_xyz, np.float32),
                                rgb=np.asarray(accepted_rgb, np.float32),
                                instance_id=np.full(len(accepted_xyz), oid, np.int32),
                                accepted_mask=np.asarray(accept, bool))

        live = self._live.setdefault(oid, {"map": None, "gazes": [], "steps": [], "rgb": []})
        live["gazes"].append((float(gaze_deg[0]), float(gaze_deg[1])))
        live["steps"].append(int(global_step))
        live["rgb"].append(str(rgb_dir / rgb_name))

        a_err = err[accept]
        return {
            **base,
            "target_visible_reference_cells": int(self._target_mask(oid).sum()),
            "accepted_count": int(accept.sum()),
            "oracle_rejected_count": int((~accept).sum()),
            "rejected_wrong_instance": int(np.count_nonzero(np.isfinite(ref_rng) & (ref_id != oid))),
            "rejected_gate": int(np.count_nonzero(np.isfinite(ref_rng) & (ref_id == oid) & (err > gate))),
            "rejected_no_reference": int(np.count_nonzero(~np.isfinite(ref_rng) | (ref_rng <= 0))),
            "raw_depth_error_median_m": float(np.median(err[np.isfinite(err)])) if np.isfinite(err).any() else None,
            "raw_depth_error_p95_m": float(np.percentile(err[np.isfinite(err)], 95)) if np.isfinite(err).any() else None,
            "accepted_depth_error_median_m": float(np.median(a_err)) if len(a_err) else None,
            "accepted_depth_error_p95_m": float(np.percentile(a_err, 95)) if len(a_err) else None,
            "accepted_xyz_sha256": _sha256_array(accepted_xyz),
            "accepted_xyz_shape": list(accepted_xyz.shape),
            "accepted_is_row_subset_of_stereo": bool(subset_ok),
            "accepted_is_boolean_filter_of_stereo": bool(filter_ok),
            "accepted_rows_differing_from_reference_position": differs,
            "accepted_patch": (str(patch_path) if patch_path else None),
        }

    @staticmethod
    def _save_look_preview(pair_dir: Path, dest: Path) -> None:
        """Left-eye foveated raster as an 8-bit preview, from the saved samples."""
        s = np.load(pair_dir / "L" / "f000" / "samples.npz")
        cols = json.loads((pair_dir / "L" / "f000" / "columns.json").read_text()) \
            if (pair_dir / "L" / "f000" / "columns.json").is_file() else {}
        idx = np.asarray(s["raster_index"], np.int64)      # (N, 2) row/col in the foveated raster
        val = np.asarray(s["value"], np.float64)
        n = int(idx.max()) + 1 if len(idx) else 1
        img = np.zeros((n, n, 3), np.float64)
        img[np.clip(idx[:, 0], 0, n - 1), np.clip(idx[:, 1], 0, n - 1)] = val
        Image.fromarray(_tone_preview(img)).save(dest)
        del cols

    # ---------- fusion, established 12 mm surface map ----------

    def initialize_or_fuse(self, obj: DemoObject, measurement: dict[str, Any], object_dir: Path,
                           existing_map: Path | None) -> dict[str, Any]:
        """Use established 12 mm surface-map initialize/fuse on accepted stereo xyz only."""
        oid = int(obj.object_id)
        p = measurement.get("accepted_patch")
        live = self._live[oid]
        if not p:
            return {"map_path": (str(existing_map) if existing_map else None), "fused": False,
                    "reason": "no accepted stereo geometry", "new": 0, "matched": 0}
        with np.load(p, allow_pickle=False) as z:
            patch = Patch(f"fix_{int(measurement['global_step']):03d}",
                          np.asarray(z["xyz_h"], np.float64), np.asarray(z["rgb"], np.float64),
                          np.asarray(z["instance_id"]))
        # Inherited empty-look semantics; frozen initialize() and fuse() share
        # the same 100-point floor, so the rule is applied identically to both.
        if len(patch.xyz_h) < EMPTY_LOOK_LIMIT:
            return {"map_path": (str(existing_map) if existing_map else None), "fused": False,
                    "empty_look": True, "new": 0, "matched": 0,
                    "reason": f"accepted {len(patch.xyz_h)} < inherited empty-look limit {EMPTY_LOOK_LIMIT}"}
        maps = object_dir / "maps"
        maps.mkdir(parents=True, exist_ok=True)
        if existing_map is None:
            sm = initialize(patch, oid)
            assoc = {"matched": 0, "new": int(len(sm.xyz_h))}
            idem = True
        else:
            sm = live["map"]
            sm, assoc = fuse(sm, patch, oid, self.fusion["association_radius_m"], self.fusion["hash_cell_m"])
            replay, dup = fuse(sm, patch, oid, self.fusion["association_radius_m"], self.fusion["hash_cell_m"])
            idem = bool(dup["duplicate_patch"] and np.array_equal(sm.xyz_h, replay.xyz_h))
            if not idem:
                raise AssertionError("accepted-geometry fusion is not idempotent")
        if len(sm.instance_id) and set(np.unique(sm.instance_id).tolist()) != {oid}:
            raise AssertionError("Classroom foreground map lost instance purity")
        live["map"] = sm
        mp = maps / f"map_{int(measurement['global_step']):03d}.npz"
        save_map(mp, sm)
        return {"map_path": str(mp), "fused": True, "idempotent_replay": bool(idem),
                "matched": int(assoc.get("matched", 0)), "new": int(assoc.get("new", 0)),
                "map_points": int(len(sm.xyz_h))}

    def finalize_foreground_object(self, obj: DemoObject, object_dir: Path, current_map: Path | None,
                                   history: list[dict[str, Any]], stop_reason: str) -> dict[str, Any]:
        oid = int(obj.object_id)
        live = self._live.get(oid, {})
        sm = live.get("map")
        objects_dir = self.out / "objects"
        objects_dir.mkdir(parents=True, exist_ok=True)
        npz, ply = objects_dir / f"object_{oid}.npz", objects_dir / f"object_{oid}.ply"
        instantiated = bool(sm is not None and len(sm.xyz_h))
        if instantiated:
            save_map(npz, sm)
            export.write_ascii_ply(ply, np.asarray(sm.xyz_h, np.float64),
                                   np.full(len(sm.xyz_h), oid, np.int64), _tone_preview(np.asarray(sm.rgb, np.float64)))
        else:
            save_map(npz, SurfaceMap(np.zeros((0, 3), np.float32), np.zeros((0, 3), np.float32),
                                     np.zeros(0, np.int32), np.zeros(0, np.int16), np.zeros(0, np.uint64), []))
            ply.write_text("ply\nformat ascii 1.0\nelement vertex 0\n"
                           "property float x\nproperty float y\nproperty float z\nend_header\n")
        sup = self.oracle_uncovered_support(obj, {}, current_map, history)
        return {
            "instantiated": instantiated,
            "foreground_surfels": int(len(sm.xyz_h)) if instantiated else 0,
            "reference_support_cells": sup["reference_support_cells"],
            "reference_coverage": sup["reference_coverage"],
            "uncovered_cells": sup["uncovered_cells"],
            "raw_valid_stereo_total": int(sum(int(h.get("raw_valid_stereo_count", 0)) for h in history)),
            "accepted_total": int(sum(int(h.get("accepted_count", 0)) for h in history)),
            "oracle_rejected_total": int(sum(int(h.get("oracle_rejected_count", 0)) for h in history)),
            "map_npz": f"objects/object_{oid}.npz", "map_ply": f"objects/object_{oid}.ply",
        }

    # ---------- the single adaptive background object ----------

    def build_background_scaffold(self, background_plan: dict[str, Any], guidance: dict[str, Any],
                                  out: Path) -> dict[str, Any]:
        """Export the ONE adaptive special background object.

        It may use Blender RGB/reference depth and trivial spherical/shell
        geometry. It must remain separate from foreground point counts, stereo
        depth-error metrics, and any claim of observer-inferred geometry.
        """
        mask = self._plan["bg_mask"]
        depth, rgb = self._ref["depth"], self._ref["rgb"]
        d = depth[mask].astype(np.float64)
        Image.fromarray((mask.astype(np.uint8) * 255)).save(out / "background_mask.png")
        tex = np.zeros_like(rgb)
        tex[mask] = rgb[mask]
        Image.fromarray(_tone_preview(tex)).save(out / "background_rgb.png")

        shell_range = float(np.median(d)) if len(d) else None
        pts = np.zeros((0, 3))
        if len(d):
            ys, xs = np.nonzero(mask)
            take = np.arange(0, len(ys), max(1, len(ys) // 40000))
            yaws = (xs[take] + 0.5) / public.PANO_WIDTH * 360.0 - 180.0
            pitches = 90.0 - (ys[take] + 0.5) / public.PANO_HEIGHT * 180.0
            pts = topo1a.angles_to_dir(yaws, pitches) * shell_range
            export.write_ascii_ply(out / "background_shell.ply", pts,
                                   np.zeros(len(pts), np.int64), _tone_preview(rgb[ys[take], xs[take]]))
        soft = {
            "schema": "DemoClassroom1-background-soft-depth-v2",
            "object_key": public.BACKGROUND_OBJECT_KEY,
            "layer": "BACKGROUND_SCAFFOLD",
            "provenance": "ORACLE_REFERENCE_DEPTH_AND_RGB",
            "is_stereo_reconstruction": False,
            "counted_in_foreground_totals": False,
            "how_computed": (
                "reference first-hit range at every panorama cell whose group was aggregated into the single "
                "background object by the scene plan; robust quantiles over those cells; no stereo sample contributes"
            ),
            "aggregated_group_ids": background_plan.get("aggregated_group_ids", []),
            "aggregated_group_count": background_plan.get("aggregated_group_count", 0),
            "includes_unassigned_index0": background_plan.get("includes_unassigned_index0", False),
            "cells": int(mask.sum()),
            "range_quantiles_m": {f"p{k}": float(np.percentile(d, k)) for k in (5, 25, 50, 75, 95)} if len(d) else {},
            "range_median_m": shell_range,
            "range_mean_m": float(d.mean()) if len(d) else None,
            "range_std_m": float(d.std()) if len(d) else None,
            "range_min_m": float(d.min()) if len(d) else None,
            "range_max_m": float(d.max()) if len(d) else None,
            "shell_kind": "constant-range spherical shell at the median, visualization only",
            "shell_range_m": shell_range,
            "shell_points": int(len(pts)),
        }
        (out / "background_soft_depth.json").write_text(json.dumps(soft, indent=2, sort_keys=True) + "\n")
        return {**soft, "background_mask": "background_mask.png", "background_rgb": "background_rgb.png",
                "background_soft_depth": "background_soft_depth.json",
                "background_shell": "background_shell.ply", "foreground_surfels": 0, "fixations": 0}

    # ---------- exports ----------

    def export_demo(self, object_rows: list[dict[str, Any]], background_row: dict[str, Any],
                    guidance: dict[str, Any], fixation_history: list[dict[str, Any]], out: Path) -> dict[str, Any]:
        """Export foreground, background, composite, provenance, timeline, movie and report."""
        xyz_all, oid_all, rgb_all, sup_all = [], [], [], []
        per_object: dict[str, int] = {}
        for r in object_rows:
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

        W, H = public.PANO_WIDTH, public.PANO_HEIGHT
        yaw, pitch, rng = topo1a.xyz_to_angles(xyz)
        fdepth, finst = export.spherical_zbuffer(yaw, pitch, rng, oids, W, H)
        np.save(out / "foreground_depth.npy", fdepth)
        np.save(out / "foreground_instance.npy", finst)
        fvalid = np.isfinite(fdepth) & (fdepth > 0)
        Image.fromarray((fvalid.astype(np.uint8) * 255)).save(out / "foreground_valid.png")
        Image.fromarray(export.depth_preview(fdepth)).save(out / "foreground_depth_preview.png")

        mosaic = np.zeros((H, W, 3), np.uint8)
        if len(xyz):
            good = np.isfinite(yaw) & np.isfinite(pitch) & (rng > 0)
            gx = np.clip(np.floor(((yaw[good] + 180.0) % 360.0) / 360.0 * W).astype(np.int64), 0, W - 1)
            gy = np.clip(np.floor((90.0 - np.clip(pitch[good], -90.0, 90.0)) / 180.0 * H).astype(np.int64), 0, H - 1)
            order = np.argsort(-rng[good], kind="stable")
            mosaic[gy[order], gx[order]] = rgb8[good][order]
        Image.fromarray(mosaic).save(out / "foreground_rgb_mosaic.png")

        bg_mask = self._plan["bg_mask"]
        bg_range = background_row.get("shell_range_m")
        ref_rgb8 = _tone_preview(self._ref["rgb"])
        demo_rgb = np.zeros_like(ref_rgb8)
        demo_rgb[bg_mask] = ref_rgb8[bg_mask]
        demo_rgb[fvalid] = mosaic[fvalid]
        Image.fromarray(demo_rgb).save(out / "demo_rgb.png")

        demo_depth = np.full((H, W), np.nan, np.float32)
        if bg_range is not None:
            demo_depth[bg_mask] = np.float32(bg_range)
        demo_depth[fvalid] = fdepth[fvalid]
        np.save(out / "demo_depth.npy", demo_depth)
        Image.fromarray(export.depth_preview(demo_depth)).save(out / "demo_depth_preview.png")

        demo_inst = np.zeros((H, W), np.int32)
        demo_inst[bg_mask] = np.int32(-1)
        demo_inst[fvalid] = finst[fvalid]
        np.save(out / "demo_instance.npy", demo_inst)

        layer = np.zeros((H, W), np.uint8)
        layer[bg_mask] = 2
        layer[fvalid] = 1
        np.save(out / "demo_layer.npy", layer)
        prov = {
            "schema": "DemoClassroom1-layer-provenance-v2",
            "controller_mode": public.CONTROLLER_MODE,
            "layers": {
                "0": {"name": "EMPTY", "source": "none"},
                "1": {"name": "STEREO_FOREGROUND",
                      "source": "oracle gaze -> established Classroom foveated binocular render -> "
                                "established stereo field -> oracle validity gate -> 12 mm fusion",
                      "metric_geometry_from": "stereo", "pixels": int(fvalid.sum())},
                "2": {"name": "BACKGROUND_SCAFFOLD",
                      "source": "declared oracle background: reference RGB and reference soft-depth range",
                      "metric_geometry_from": "reference (NOT stereo)", "pixels": int((layer == 2).sum())},
            },
            "composite_is_autonomous_reconstruction": False,
            "attention_is_oracle_scaffolding": True,
            "foreground_surfels_total": int(len(xyz)),
            "foreground_surfels_per_object": per_object,
            "background_surfels_counted_in_foreground": 0,
            "layer_raster": "demo_layer.npy",
        }
        (out / "demo_layer_provenance.json").write_text(json.dumps(prov, indent=2, sort_keys=True) + "\n")

        timeline = self._timeline(fixation_history, guidance, out)
        movie = self._movie(out, timeline)
        return {
            "foreground_scene_points_npz": "foreground_scene_points.npz",
            "foreground_scene_points_ply": "foreground_scene_points.ply",
            "foreground_depth": "foreground_depth.npy", "foreground_instance": "foreground_instance.npy",
            "foreground_valid": "foreground_valid.png", "foreground_depth_preview": "foreground_depth_preview.png",
            "foreground_rgb_mosaic": "foreground_rgb_mosaic.png",
            "background_mask": "background_mask.png", "background_rgb": "background_rgb.png",
            "background_soft_depth": "background_soft_depth.json", "background_shell": "background_shell.ply",
            "demo_rgb": "demo_rgb.png", "demo_depth": "demo_depth.npy",
            "demo_depth_preview": "demo_depth_preview.png", "demo_instance": "demo_instance.npy",
            "demo_layer": "demo_layer.npy", "demo_layer_provenance": "demo_layer_provenance.json",
            "reference_rgb": "reference_rgb.png", "reference_depth": "reference_depth.npy",
            "reference_instance": "reference_instance.npy",
            "timeline_frames": len(timeline), "timeline_dir": "timeline", "movie": movie,
            "foreground_surfels_total": int(len(xyz)), "foreground_surfels_per_object": per_object,
            "foreground_panorama_pixels": int(fvalid.sum()),
            "blender_launches": int(self.blender_launches), "render_seconds": float(self.render_seconds),
        }

    def _timeline(self, fixation_history: list[dict[str, Any]], guidance: dict[str, Any], out: Path) -> list[str]:
        tl = out / "timeline"
        tl.mkdir(parents=True, exist_ok=True)
        y0, y1, x0, x1 = guidance.get("occupied_crop_y0y1x0x1",
                                      [0, public.PANO_HEIGHT, 0, public.PANO_WIDTH])
        blank = np.zeros((y1 - y0, x1 - x0, 3), np.uint8)
        acc_xyz: list[np.ndarray] = []
        acc_rgb: list[np.ndarray] = []
        frames: list[str] = []
        for m in sorted(fixation_history, key=lambda r: int(r["global_step"])):
            p = m.get("accepted_patch")
            if p and Path(p).is_file():
                with np.load(p, allow_pickle=False) as z:
                    acc_xyz.append(np.asarray(z["xyz_h"], np.float64))
                    acc_rgb.append(np.asarray(z["rgb"], np.float64))
            if acc_xyz:
                X = np.concatenate(acc_xyz)
                C = _tone_preview(np.concatenate(acc_rgb))
                yaw, pitch, rng = topo1a.xyz_to_angles(X)
                good = np.isfinite(yaw) & np.isfinite(pitch) & (rng > 0)
                canvas = np.zeros((public.PANO_HEIGHT, public.PANO_WIDTH, 3), np.uint8)
                gx = np.clip(np.floor(((yaw[good] + 180.0) % 360.0) / 360.0 * public.PANO_WIDTH).astype(np.int64),
                             0, public.PANO_WIDTH - 1)
                gy = np.clip(np.floor((90.0 - np.clip(pitch[good], -90.0, 90.0)) / 180.0 * public.PANO_HEIGHT).astype(np.int64),
                             0, public.PANO_HEIGHT - 1)
                order = np.argsort(-rng[good], kind="stable")
                canvas[gy[order], gx[order]] = C[good][order]
                scene = canvas[y0:y1, x0:x1]
            else:
                scene = blank
            if not m.get("rgb") or not Path(m["rgb"]).is_file():
                continue
            look = np.asarray(Image.open(m["rgb"]).convert("RGB"))
            h = max(look.shape[0], scene.shape[0])
            sc = Image.fromarray(scene)
            sc = sc.resize((max(1, int(sc.width * h / sc.height)), h), Image.NEAREST)
            lk = Image.fromarray(look).resize((max(1, int(look.shape[1] * h / look.shape[0])), h), Image.NEAREST)
            frame = Image.new("RGB", (lk.width + sc.width + 12, h), (16, 16, 18))
            frame.paste(lk, (0, 0))
            frame.paste(sc, (lk.width + 12, 0))
            name = f"fix_{int(m['global_step']):03d}.png"
            frame.save(tl / name)
            frames.append(f"timeline/{name}")
        return frames

    def _movie(self, out: Path, frames: list[str]) -> str | None:
        if not frames or shutil.which("ffmpeg") is None:
            return None
        first = Image.open(out / frames[0])
        w, h = first.width - first.width % 2, first.height - first.height % 2
        cmd = ["ffmpeg", "-y", "-framerate", "2", "-pattern_type", "glob",
               "-i", str(out / "timeline" / "fix_*.png"),
               "-vf", f"crop={w}:{h}:0:0,format=yuv420p", "-c:v", "libx264", "-preset", "medium",
               str(out / "demo.mp4")]
        p = subprocess.run(cmd, capture_output=True, text=True)
        (out / "logs").mkdir(parents=True, exist_ok=True)
        (out / "logs" / "ffmpeg.log").write_text(p.stdout + "\n--- STDERR ---\n" + p.stderr)
        return "demo.mp4" if p.returncode == 0 and (out / "demo.mp4").is_file() else None

    # ---------- report ----------

    def write_report(self, manifest: dict[str, Any], out: Path) -> dict[str, Any]:
        rows = manifest["foreground_object_rows"]
        bg = manifest["background_row"]
        hist = json.loads((out / "fixation_history.json").read_text())
        prov = json.loads((out / "demo_layer_provenance.json").read_text())
        dec = manifest["decomposition"]
        raw = sum(int(f.get("raw_valid_stereo_count", 0)) for f in hist)
        acc = sum(int(f.get("accepted_count", 0)) for f in hist)
        rej = sum(int(f.get("oracle_rejected_count", 0)) for f in hist)
        report = {
            "schema": "DemoClassroom1-report-v2",
            "what_this_is": "oracle-attention concept demonstration in the realistic Blender Classroom",
            "controller_mode": public.CONTROLLER_MODE,
            "attention": {
                "oracle_attention_fixation_count": manifest["oracle_attention_fixation_count"],
                "fixation_count": manifest["fixation_count"],
                "local_fsg_attention_actions": 0,
                "action_source_counts": {
                    k: sum(1 for f in hist if f.get("action_source") == k)
                    for k in ("ORACLE_SEED", "ORACLE_UNCOVERED_SUPPORT")},
            },
            "layers": {
                "A_stereo_foreground": {"surfels": prov["foreground_surfels_total"],
                                        "panorama_pixels": prov["layers"]["1"]["pixels"],
                                        "metric_geometry_from": "stereo"},
                "B_background_scaffold": {"panorama_pixels": prov["layers"]["2"]["pixels"],
                                          "aggregated_groups": bg.get("aggregated_group_count"),
                                          "soft_depth_median_m": bg.get("range_median_m"),
                                          "metric_geometry_from": "reference (NOT stereo)",
                                          "surfels_counted_as_foreground": 0},
                "C_reference_truth": {"products": ["reference_rgb.png", "reference_depth.npy",
                                                   "reference_instance.npy"]},
                "D_demo_composite": {"is_autonomous_reconstruction": False,
                                     "attention_is_oracle_scaffolding": True},
            },
            "decomposition": dec,
            "measurement": {
                "raw_valid_stereo_total": raw, "accepted_total": acc, "oracle_rejected_total": rej,
                "oracle_rejected_fraction": (float(rej / raw) if raw else None),
                "gate": f"|range_stereo-range_ref| <= max({public.DEPTH_GATE_ABS_M}, {public.DEPTH_GATE_REL}*range_ref)",
                "accepted_is_row_subset_all_fixations": all(
                    f.get("accepted_is_row_subset_of_stereo", True) for f in hist),
                "reference_supplied_foreground_values_count": sum(
                    1 for f in hist if f.get("reference_depth_supplied_foreground_values")),
            },
            "objects": rows,
            "not_established": list(public.PUBLIC_SPEC["scientific_claims_not_made"]),
        }
        (out / "demo_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

        m = report["measurement"]
        lines = [
            "# Demo-Classroom-1 — oracle-attention concept demonstration",
            "",
            "**Attention in this demo is entirely oracle scaffolding.** Every Classroom fixation",
            f"was chosen from Blender reference support (`{public.CONTROLLER_MODE}`); the local FSG",
            "controller was **not invoked at all**. The composite is **not** an autonomous",
            "reconstruction, and nothing here tests a gaze policy.",
            "",
            "The story is: **oracle gaze → foveated binocular observation → established stereo →",
            "validation → 12 mm fusion → persistent room scene.**",
            "",
            "## Layers",
            "",
            "| layer | metric geometry from | extent |",
            "|---|---|---|",
            f"| **A** stereo foreground | established Classroom stereo + 12 mm fusion | "
            f"{report['layers']['A_stereo_foreground']['surfels']:,} surfels, "
            f"{report['layers']['A_stereo_foreground']['panorama_pixels']:,} px |",
            f"| **B** background scaffold | reference soft depth (NOT stereo) | "
            f"{report['layers']['B_background_scaffold']['panorama_pixels']:,} px, "
            f"{bg.get('aggregated_group_count')} groups, median "
            f"{bg.get('range_median_m'):.3f} m |",
            "| **C** reference truth | evaluator render before control | 2048×1024 |",
            "| **D** demo composite | A where present, else B | `demo_layer.npy` |",
            "",
            f"Background surfels counted as foreground: **0**.",
            "",
            "## Scene-adaptive decomposition",
            "",
            f"- occupied reference cells: **{dec['occupied_cells']:,}**, median range {dec['occupied_range_median_m']:.3f} m",
            f"- **d_near = q{int(public.BACKGROUND_NEAR_QUANTILE*100)} = {dec['d_near_m']:.3f} m**, "
            f"**d_far = q{int(public.BACKGROUND_FAR_QUANTILE*100)} = {dec['d_far_m']:.3f} m**",
            f"- band weight: `{dec['band_weight']}`",
            f"- groups considered **{dec['groups_considered']}** → foreground **{dec['groups_foreground']}**, "
            f"background **{dec['groups_background']}**",
            "",
            "## Foreground objects",
            "",
            "| id | group | fixations | stop | surfels | reference coverage |",
            "|---:|---|---:|---|---:|---:|",
        ]
        for r in rows:
            lines.append(f"| {r['object_id']} | `{r['source_group']}` | {r.get('fixations',0)} | "
                         f"{r.get('stop_reason')} | {r.get('foreground_surfels',0):,} | "
                         f"{r.get('reference_coverage',0.0):.4f} |")
        lines += [
            "",
            "## Measurement validation",
            "",
            f"- gate: `{m['gate']}`",
            f"- raw valid stereo **{m['raw_valid_stereo_total']:,}**, accepted **{m['accepted_total']:,}**, "
            f"oracle-rejected **{m['oracle_rejected_total']:,}**"
            + (f" ({m['oracle_rejected_fraction']*100:.2f}%)" if m["oracle_rejected_fraction"] is not None else ""),
            f"- accepted set is a bitwise row-subset of the stereo array on every fixation: "
            f"**{m['accepted_is_row_subset_all_fixations']}**",
            f"- fixations where reference depth supplied a foreground value: "
            f"**{m['reference_supplied_foreground_values_count']}**",
            "",
            "## Attention",
            "",
            f"- oracle attention fixations: **{report['attention']['oracle_attention_fixation_count']}** "
            f"of **{report['attention']['fixation_count']}**",
            f"- **local FSG attention actions: 0**",
            f"- sources: {report['attention']['action_source_counts']}",
            "",
            "## Not established",
            "",
        ] + [f"- {x}" for x in report["not_established"]] + [""]
        (out / "demo_report.md").write_text("\n".join(lines))
        return report
