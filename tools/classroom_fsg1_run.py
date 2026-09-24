"""Run Classroom-FSG-1: controlled gaze replay through tangent-plane FSG stereo.

Example full run:

  .venv/bin/python tools/classroom_fsg1_run.py \
    --out previews/classroom-fsg1/full-seed2111 \
    --history previews/demo-classroom1/full-seed2111/fixation_history.json \
    --source-manifest previews/demo-classroom1/full-seed2111/demo_manifest.json

The source history is used ONLY for gaze yaw/pitch and ordering.  Historical
foreground/background roles and target ids are provenance, not scene partitioning.
Every positive instance id measured by the generic bridge is an ordinary scene
entity in this experiment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

import cv2
import numpy as np

import classroom_fsg1_public as public


FROZEN_TOOLS = (
    "tools/fsg_geometry.py",
    "tools/fsg_blend_bridge.py",
    "tools/fsg_stereo.py",
    "tools/fsg3_surface_map.py",
    "tools/fsg6f_public.py",
)


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _sha256_array(a: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def _linear_to_u8(rgb: np.ndarray) -> np.ndarray:
    a = np.clip(np.asarray(rgb, np.float64), 0.0, 1.0)
    a = np.where(a <= 0.0031308, 12.92 * a, 1.055 * np.power(a, 1.0 / 2.4) - 0.055)
    return np.rint(255.0 * a).astype(np.uint8)


def _write_ply(path: Path, xyz: np.ndarray, rgb: np.ndarray, ids: np.ndarray) -> None:
    xyz = np.asarray(xyz, np.float64).reshape(-1, 3)
    rgb8 = _linear_to_u8(np.asarray(rgb, np.float64).reshape(-1, 3))
    ids = np.asarray(ids).reshape(-1)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write("ply\nformat ascii 1.0\n")
        f.write("comment Classroom-FSG-1 fixed head frame; metres\n")
        f.write(f"element vertex {len(xyz)}\n")
        f.write("property float x\nproperty float y\nproperty float z\n")
        f.write("property uchar red\nproperty uchar green\nproperty uchar blue\n")
        f.write("property int instance_id\nend_header\n")
        for p, c, oid in zip(xyz, rgb8, ids):
            f.write(f"{p[0]:.8g} {p[1]:.8g} {p[2]:.8g} {int(c[0])} {int(c[1])} {int(c[2])} {int(oid)}\n")


def _source_history(history_path: Path, manifest_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    history = json.loads(history_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    if not isinstance(history, list) or len(history) != public.EXPECTED_FIXATIONS:
        raise RuntimeError(f"expected sealed {public.EXPECTED_FIXATIONS}-fixation history, got {len(history) if isinstance(history, list) else type(history)}")
    if int(manifest.get("fixation_count", -1)) != public.EXPECTED_FIXATIONS:
        raise RuntimeError("source manifest fixation_count does not match sealed Classroom demo")
    if manifest.get("oracle_attention_for_all_fixations") is not True:
        raise RuntimeError("source manifest does not certify all-oracle attention")
    out = []
    for i, row in enumerate(history):
        g = row.get("gaze_deg")
        if not isinstance(g, (list, tuple)) or len(g) != 2:
            raise RuntimeError(f"history row {i} has no gaze_deg pair")
        yaw, pitch = float(g[0]), float(g[1])
        if not (math.isfinite(yaw) and math.isfinite(pitch)):
            raise RuntimeError(f"history row {i} gaze is non-finite")
        step = int(row.get("global_step", i))
        if step != i:
            raise RuntimeError(f"history order changed at row {i}: global_step={step}")
        out.append({
            "global_step": i,
            "gaze_deg": [yaw, pitch],
            "historical_object_id": row.get("object_id"),
            "historical_action_source": row.get("action_source"),
        })
    return out, manifest


def _rectified_truth_core(run_dir: Path, result: dict[str, np.ndarray]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    with np.load(run_dir / "evaluation_only" / "truth_L.npz", allow_pickle=False) as z:
        raw_id = np.asarray(z["instance_id"], np.int32)
        raw_range = np.asarray(z["range_m"], np.float32)
        raw_xyz = np.asarray(z["xyz_h"], np.float32)
    mx = np.asarray(result["map_Lx"], np.float32)
    my = np.asarray(result["map_Ly"], np.float32)
    rid = cv2.remap(raw_id.astype(np.float32), mx, my, cv2.INTER_NEAREST,
                    borderMode=cv2.BORDER_CONSTANT, borderValue=0).astype(np.int32)
    rr = cv2.remap(np.nan_to_num(raw_range, nan=0.0), mx, my, cv2.INTER_NEAREST,
                   borderMode=cv2.BORDER_CONSTANT, borderValue=0).astype(np.float32)
    xyz = np.empty((*mx.shape, 3), np.float32)
    for k in range(3):
        xyz[..., k] = cv2.remap(np.nan_to_num(raw_xyz[..., k], nan=0.0), mx, my, cv2.INTER_NEAREST,
                                borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    x, y, w, h = map(int, np.asarray(result["crop_xywh"]).tolist())
    sl = np.s_[y:y+h, x:x+w]
    return rid[sl], rr[sl], xyz[sl]


def _evaluate_fixation(run_dir: Path) -> tuple[dict[str, Any], dict[str, dict[str, np.ndarray]]]:
    with np.load(run_dir / "stereo" / "result.npz", allow_pickle=False) as z:
        result = {k: z[k] for k in z.files}
    valid = np.asarray(result["valid"], bool)
    ids = np.asarray(result["instance_id"], np.int32)
    xyz = np.asarray(result["xyz_h"], np.float32)
    rgb = np.asarray(result["rgb_left"], np.float32)
    est_range = np.asarray(result["range_left_m"], np.float32)
    truth_id, truth_range, truth_xyz = _rectified_truth_core(run_dir, result)

    # The evaluator remaps the exact same raw left-eye oracle ids used in the
    # observation.  If this fails, the truth alignment is not trustworthy.
    if not np.array_equal(truth_id, ids):
        mismatch = int(np.count_nonzero(truth_id != ids))
        raise AssertionError(f"rectified evaluator instance ids disagree with estimator ids at {mismatch} core pixels")

    native = valid & (ids > 0) & np.isfinite(xyz).all(axis=-1) & np.isfinite(est_range)
    has_truth = (truth_id > 0) & np.isfinite(truth_range) & (truth_range > 0)
    err = np.abs(est_range - truth_range)
    tol = np.maximum(public.GUARD_ABS_M, public.GUARD_REL * truth_range)
    guarded = native & has_truth & (err <= tol)
    if np.any(guarded & ~native):
        raise AssertionError("guarded mask is not a subset of native stereo validity")

    ni = np.flatnonzero(native.ravel())
    gi = np.flatnonzero(guarded.ravel())
    flat_xyz = xyz.reshape(-1, 3)
    flat_rgb = rgb.reshape(-1, 3)
    flat_id = ids.reshape(-1)
    native_patch = {
        "xyz_h": flat_xyz[ni], "rgb": flat_rgb[ni], "instance_id": flat_id[ni],
        "flat_index": ni.astype(np.int32),
    }
    guarded_patch = {
        "xyz_h": flat_xyz[gi], "rgb": flat_rgb[gi], "instance_id": flat_id[gi],
        "flat_index": gi.astype(np.int32),
    }
    np.savez_compressed(run_dir / "native_patch.npz", **native_patch)
    np.savez_compressed(run_dir / "guarded_patch.npz", **guarded_patch)

    native_err = err[native & has_truth]
    guarded_err = err[guarded]
    def stats(a: np.ndarray) -> dict[str, Any]:
        a = np.asarray(a, np.float64)
        if len(a) == 0:
            return {"n": 0, "median_m": None, "p95_m": None, "p99_m": None, "gt100mm_fraction": None}
        return {
            "n": int(len(a)),
            "median_m": float(np.median(a)),
            "p95_m": float(np.percentile(a, 95)),
            "p99_m": float(np.percentile(a, 99)),
            "gt100mm_fraction": float(np.mean(a > 0.10)),
        }

    meta = {
        "native_count": int(native.sum()),
        "guarded_count": int(guarded.sum()),
        "guard_rejected_count": int(native.sum() - guarded.sum()),
        "guard_rejected_fraction_of_native": float(1.0 - guarded.sum() / max(1, native.sum())),
        "native_truth_error": stats(native_err),
        "guarded_truth_error": stats(guarded_err),
        "native_instance_count": int(len(np.unique(ids[native]))),
        "guarded_instance_count": int(len(np.unique(ids[guarded]))),
        "guarded_is_boolean_subset_of_native": True,
        "guarded_xyz_sha256": _sha256_array(guarded_patch["xyz_h"]),
        "native_xyz_sha256": _sha256_array(native_patch["xyz_h"]),
        "truth_used_only_after_stereo": True,
        "truth_inserted_or_substituted_geometry": False,
        "truth_xyz_was_not_used_for_patch_geometry": True,
        "truth_alignment_instance_exact": True,
        "truth_xyz_shape": list(truth_xyz.shape),
    }
    _write_json(run_dir / "measurement_evaluation.json", meta)
    return meta, {"native": native_patch, "guarded": guarded_patch}


class _Accumulator:
    def __init__(self, stream: str):
        self.stream = stream
        self.maps: dict[int, Any] = {}
        self.buffers: dict[int, dict[str, Any]] = {}
        self.packet_counts: dict[int, int] = {}
        self.source_points: dict[int, int] = {}
        self.source_contributions: dict[int, int] = {}
        self.leftover_points: dict[int, int] = {}
        self.fusion_rows: list[dict[str, Any]] = []

    def add(self, step: int, patch: dict[str, np.ndarray]) -> None:
        ids = np.asarray(patch["instance_id"], np.int32)
        for oid in sorted(int(x) for x in np.unique(ids) if int(x) > 0):
            m = ids == oid
            n = int(m.sum())
            if n == 0:
                continue
            b = self.buffers.setdefault(oid, {"steps": [], "xyz": [], "rgb": []})
            b["steps"].append(int(step))
            b["xyz"].append(np.asarray(patch["xyz_h"][m], np.float32))
            b["rgb"].append(np.asarray(patch["rgb"][m], np.float32))
            self.source_points[oid] = self.source_points.get(oid, 0) + n
            self.source_contributions[oid] = self.source_contributions.get(oid, 0) + 1
            points = sum(len(a) for a in b["xyz"])
            if len(b["steps"]) >= public.FUSION_PACKET_CONTRIBUTIONS and points >= public.FSG3_MIN_PATCH_POINTS:
                self._flush(oid)

    def _flush(self, oid: int) -> None:
        from fsg3_surface_map import Patch, fuse, initialize
        import fsg6f_public as frozen_public

        b = self.buffers[oid]
        xyz = np.concatenate(b["xyz"], axis=0) if b["xyz"] else np.zeros((0, 3), np.float32)
        rgb = np.concatenate(b["rgb"], axis=0) if b["rgb"] else np.zeros((0, 3), np.float32)
        if len(xyz) < public.FSG3_MIN_PATCH_POINTS:
            return
        packet_no = self.packet_counts.get(oid, 0)
        if packet_no >= 63:
            raise RuntimeError(f"object {oid} exceeded fsg3 uint64 provenance packet capacity")
        first, last = b["steps"][0], b["steps"][-1]
        pid = f"{self.stream[0]}_o{oid}_b{packet_no:02d}_s{first:03d}-{last:03d}"
        patch = Patch(pid, xyz, rgb, np.full(len(xyz), oid, np.int32))
        if oid not in self.maps:
            sm = initialize(patch, oid)
            replay, dup = fuse(sm, patch, oid, frozen_public.FUSION["association_radius_m"], frozen_public.FUSION["hash_cell_m"])
            idem = bool(dup.get("duplicate_patch") and np.array_equal(sm.xyz_h, replay.xyz_h))
            assoc = {"matched": 0, "new": int(len(sm.xyz_h)), "input_points": int(len(xyz))}
        else:
            base = self.maps[oid]
            sm, assoc = fuse(base, patch, oid, frozen_public.FUSION["association_radius_m"], frozen_public.FUSION["hash_cell_m"])
            replay, dup = fuse(sm, patch, oid, frozen_public.FUSION["association_radius_m"], frozen_public.FUSION["hash_cell_m"])
            idem = bool(dup.get("duplicate_patch") and np.array_equal(sm.xyz_h, replay.xyz_h) and
                        np.array_equal(sm.rgb, replay.rgb) and np.array_equal(sm.support_count, replay.support_count))
        if not idem:
            raise AssertionError(f"{self.stream} fusion replay was not idempotent for object {oid}")
        self.maps[oid] = sm
        self.packet_counts[oid] = packet_no + 1
        self.fusion_rows.append({
            "stream": self.stream, "object_id": oid, "packet": packet_no,
            "steps": list(b["steps"]), "input_points": int(len(xyz)),
            "matched": int(assoc.get("matched", 0)), "new": int(assoc.get("new", 0)),
            "map_points": int(len(sm.xyz_h)), "idempotent_replay": True,
        })
        self.buffers[oid] = {"steps": [], "xyz": [], "rgb": []}

    def finish(self) -> None:
        for oid in sorted(self.buffers):
            b = self.buffers[oid]
            n = sum(len(a) for a in b["xyz"])
            if n >= public.FSG3_MIN_PATCH_POINTS:
                self._flush(oid)
            else:
                self.leftover_points[oid] = int(n)
        if any(v > 63 for v in self.packet_counts.values()):
            raise AssertionError("packetization failed to respect fsg3 provenance capacity")

    def export(self, out: Path, labels: dict[int, str]) -> dict[str, Any]:
        from fsg3_surface_map import save_map

        obj_dir = out / "objects" / self.stream
        obj_dir.mkdir(parents=True, exist_ok=True)
        xyz_all: list[np.ndarray] = []
        rgb_all: list[np.ndarray] = []
        id_all: list[np.ndarray] = []
        sup_all: list[np.ndarray] = []
        rows = []
        all_ids = sorted(set(self.source_points) | set(self.maps) | set(self.leftover_points))
        for oid in all_ids:
            sm = self.maps.get(oid)
            if sm is not None:
                save_map(obj_dir / f"object_{oid}.npz", sm)
                _write_ply(obj_dir / f"object_{oid}.ply", sm.xyz_h, sm.rgb, sm.instance_id)
                xyz_all.append(np.asarray(sm.xyz_h))
                rgb_all.append(np.asarray(sm.rgb))
                id_all.append(np.asarray(sm.instance_id))
                sup_all.append(np.asarray(sm.support_count))
                surfels = int(len(sm.xyz_h))
            else:
                surfels = 0
            rows.append({
                "object_id": oid, "label": labels.get(oid, f"instance_{oid}"),
                "source_points": int(self.source_points.get(oid, 0)),
                "source_fixation_contributions": int(self.source_contributions.get(oid, 0)),
                "fusion_packets": int(self.packet_counts.get(oid, 0)),
                "leftover_unfused_points": int(self.leftover_points.get(oid, 0)),
                "surfels": surfels,
            })
        xyz = np.concatenate(xyz_all, axis=0) if xyz_all else np.zeros((0, 3), np.float32)
        rgb = np.concatenate(rgb_all, axis=0) if rgb_all else np.zeros((0, 3), np.float32)
        ids = np.concatenate(id_all, axis=0) if id_all else np.zeros(0, np.int32)
        sup = np.concatenate(sup_all, axis=0) if sup_all else np.zeros(0, np.int16)
        np.savez_compressed(out / f"{self.stream}_scene_points.npz", xyz_h=xyz.astype(np.float32),
                            rgb=rgb.astype(np.float32), instance_id=ids.astype(np.int32),
                            support_count=sup.astype(np.int16))
        _write_ply(out / f"{self.stream}_scene_points.ply", xyz, rgb, ids)
        _write_json(out / f"{self.stream}_objects.json", rows)
        return {
            "stream": self.stream,
            "source_points": int(sum(self.source_points.values())),
            "instantiated_objects": int(sum(r["surfels"] > 0 for r in rows)),
            "objects_seen": int(len(rows)),
            "surfels": int(len(xyz)),
            "fusion_packets": int(sum(self.packet_counts.values())),
            "leftover_unfused_points": int(sum(self.leftover_points.values())),
            "object_rows": rows,
        }


def _aggregate_errors(fix_rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    # Per-fixation summaries are aggregated descriptively with counts; exact pooled
    # errors are intentionally not reconstructed from summary quantiles.
    n = sum(int(r["measurement"][key]["n"]) for r in fix_rows)
    medians = [r["measurement"][key]["median_m"] for r in fix_rows if r["measurement"][key]["median_m"] is not None]
    p95s = [r["measurement"][key]["p95_m"] for r in fix_rows if r["measurement"][key]["p95_m"] is not None]
    return {
        "compared_points": int(n),
        "fixations_with_truth": int(len(medians)),
        "median_of_fixation_medians_m": float(np.median(medians)) if medians else None,
        "median_of_fixation_p95_m": float(np.median(p95s)) if p95s else None,
        "note": "descriptive across fixations; per-fixation raw errors remain in measurement_evaluation.json",
    }


def _self_test() -> None:
    # Test the core damage-control invariant without importing any repository module.
    est = np.array([[1.00, 2.00, 1.30, 2.50]], np.float32)
    truth = np.array([[1.02, 2.30, 1.31, 2.00]], np.float32)
    native = np.array([[True, True, True, False]])
    tol = np.maximum(public.GUARD_ABS_M, public.GUARD_REL * truth)
    guarded = native & (np.abs(est - truth) <= tol)
    if guarded.tolist() != [[True, False, True, False]]:
        raise AssertionError("guard subset self-test failed")
    if np.any(guarded & ~native):
        raise AssertionError("guard created geometry")
    if math.ceil(public.EXPECTED_FIXATIONS / public.FUSION_PACKET_CONTRIBUTIONS) > 63:
        raise AssertionError("fusion packetization exceeds fsg3 provenance capacity")
    print("[classroom-fsg1] self-test PASS")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--out", type=Path)
    ap.add_argument("--history", type=Path, default=Path(public.DEFAULT_FIXATION_HISTORY))
    ap.add_argument("--source-manifest", type=Path, default=Path(public.DEFAULT_SOURCE_MANIFEST))
    ap.add_argument("--blender", default="blender")
    ap.add_argument("--limit", type=int, default=0, help="integration smoke-test prefix only; 0 means all 225")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        _self_test(); return
    if a.out is None:
        ap.error("--out is required unless --self-test")

    repo = a.repo.resolve(); out = a.out.resolve()
    history_path = a.history if a.history.is_absolute() else repo / a.history
    manifest_path = a.source_manifest if a.source_manifest.is_absolute() else repo / a.source_manifest
    scene = repo / public.SCENE_REL
    if _git(repo, "branch", "--show-current") != public.RUN_BRANCH:
        raise RuntimeError(f"run on branch {public.RUN_BRANCH}")
    if _git(repo, "status", "--porcelain"):
        raise RuntimeError("Classroom-FSG-1 requires a clean tracked tree before execution")
    if subprocess.call(["git", "merge-base", "--is-ancestor", public.BASELINE_COMMIT, "HEAD"], cwd=repo) != 0:
        raise RuntimeError(f"HEAD must descend from {public.BASELINE_COMMIT}")
    for p in [history_path, manifest_path, scene]:
        if not p.is_file():
            raise FileNotFoundError(p)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"output must be new or empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    source_history, source_manifest = _source_history(history_path, manifest_path)
    limit = int(a.limit)
    if limit < 0 or limit > public.EXPECTED_FIXATIONS:
        raise ValueError("--limit must be 0..225")
    replay = source_history if limit == 0 else source_history[:limit]
    full_run = len(replay) == public.EXPECTED_FIXATIONS

    frozen_before = {rel: _sha256_file(repo / rel) for rel in FROZEN_TOOLS}
    native_acc = _Accumulator("native")
    guarded_acc = _Accumulator("guarded")
    fix_rows: list[dict[str, Any]] = []
    group_hash: str | None = None
    labels: dict[int, str] = {}
    started = time.time()

    # Import only after preflight so --self-test remains package-local.
    sys.path.insert(0, str(repo / "tools"))
    import fsg_stereo

    for row in replay:
        step = int(row["global_step"]); yaw, pitch = map(float, row["gaze_deg"])
        rd = out / "fixations" / f"fix_{step:03d}"
        rd.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            a.blender, "-b", str(scene), "--python-exit-code", "1",
            "-P", "tools/fsg_blend_bridge.py", "--",
            "--out", str(rd), "--profile", public.PROFILE,
            "--yaw-deg", f"{yaw:.12g}", "--pitch-deg", f"{pitch:.12g}",
            "--vergence-m", str(public.VERGENCE_M), "--ipd-m", str(public.IPD_M),
            "--device", public.DEVICE, "--spp", str(public.SPP), "--seed", str(public.SEED),
        ]
        t0 = time.time()
        p = subprocess.run(cmd, cwd=repo, text=True, capture_output=True)
        (rd.parent / f"fix_{step:03d}.blender.log").write_text(p.stdout + "\n--- STDERR ---\n" + p.stderr)
        if p.returncode != 0:
            raise RuntimeError(f"Blender acquisition failed at fixation {step}; see log")
        stereo_summary = fsg_stereo.process_pair(rd)
        meas, patches = _evaluate_fixation(rd)

        gp = rd / "evaluation_only" / "instance_groups.json"
        gh = _sha256_file(gp)
        if group_hash is None:
            group_hash = gh
            grouping = json.loads(gp.read_text())
            labels = {int(g["id"]): str(g["root"]) for g in grouping.get("groups", [])}
            _write_json(out / "instance_groups.json", grouping)
        elif gh != group_hash:
            raise AssertionError(f"instance grouping changed at fixation {step}")

        native_acc.add(step, patches["native"])
        guarded_acc.add(step, patches["guarded"])
        fr = {
            **row,
            "measurement_dir": str(rd.relative_to(out)),
            "acquisition_seconds_wall": float(time.time() - t0),
            "stereo_summary": stereo_summary,
            "measurement": meas,
        }
        fix_rows.append(fr)
        print(
            f"[classroom-fsg1] fix={step:03d} gaze=({yaw:.3f},{pitch:.3f}) "
            f"native={meas['native_count']} guarded={meas['guarded_count']} "
            f"reject={meas['guard_rejected_fraction_of_native']:.3f}", flush=True
        )

    native_acc.finish(); guarded_acc.finish()
    native_summary = native_acc.export(out, labels)
    guarded_summary = guarded_acc.export(out, labels)
    _write_json(out / "native_fusion_packets.json", native_acc.fusion_rows)
    _write_json(out / "guarded_fusion_packets.json", guarded_acc.fusion_rows)
    _write_json(out / "replayed_fixations.json", fix_rows)

    frozen_after = {rel: _sha256_file(repo / rel) for rel in FROZEN_TOOLS}
    if frozen_before != frozen_after:
        raise AssertionError("a frozen measurement/fusion source changed during execution")

    native_total = sum(r["measurement"]["native_count"] for r in fix_rows)
    guarded_total = sum(r["measurement"]["guarded_count"] for r in fix_rows)
    report = {
        "schema": public.SPEC_ID,
        "full_run": full_run,
        "fixations_replayed": len(fix_rows),
        "source_fixations_available": len(source_history),
        "attention_replayed_not_reselected": True,
        "source_history_sha256": _sha256_file(history_path),
        "source_manifest_sha256": _sha256_file(manifest_path),
        "historical_foreground_background_roles_ignored": True,
        "foreground_background_decomposition_used": False,
        "background_panorama_used": False,
        "background_shell_used": False,
        "special_background_object_used": False,
        "native_measurement_points": int(native_total),
        "guarded_measurement_points": int(guarded_total),
        "guard_rejected_points": int(native_total - guarded_total),
        "guard_rejected_fraction": float(1.0 - guarded_total / max(1, native_total)),
        "native_measurement_error": _aggregate_errors(fix_rows, "native_truth_error"),
        "guarded_measurement_error": _aggregate_errors(fix_rows, "guarded_truth_error"),
        "native_scene": native_summary,
        "guarded_scene": guarded_summary,
        "guarded_is_subset_only": True,
        "truth_inserted_or_substituted_geometry": False,
        "truth_used_only_after_stereo_for_guard_and_evaluation": True,
        "frozen_tools_unchanged_during_run": True,
        "instance_grouping_sha256": group_hash,
        "elapsed_seconds": float(time.time() - started),
    }
    _write_json(out / "classroom_fsg1_report.json", report)

    manifest = {
        "schema": public.SPEC_ID,
        "public_spec_sha256": public.public_digest(),
        "repo_head": _git(repo, "rev-parse", "HEAD"),
        "baseline_commit": public.BASELINE_COMMIT,
        "scene": public.SCENE_REL,
        "scene_sha256": _sha256_file(scene),
        "profile": public.PROFILE, "spp": public.SPP, "seed": public.SEED,
        "vergence_m": public.VERGENCE_M, "ipd_m": public.IPD_M,
        "fixations_replayed": len(fix_rows), "full_run": full_run,
        "attention_source_branch": public.SOURCE_DEMO_BRANCH,
        "attention_source_commit": public.SOURCE_DEMO_FINAL_COMMIT,
        "attention_policy_reexecuted": False,
        "gazes_reselected": False,
        "foreground_background_decomposition_used": False,
        "background_panorama_used": False,
        "native_stream_truth_free_inference": True,
        "guarded_stream_truth_rejection_only": True,
        "truth_geometry_inserted": False,
        "matcher_tuned": False,
        "frozen_tool_sha256_before": frozen_before,
        "frozen_tool_sha256_after": frozen_after,
        "report": "classroom_fsg1_report.json",
    }
    _write_json(out / "classroom_fsg1_manifest.json", manifest)

    md = [
        "# Classroom-FSG-1 result", "",
        f"- full run: **{full_run}** ({len(fix_rows)}/{public.EXPECTED_FIXATIONS} sealed gazes)",
        "- attention: exact replay; no controller rerun or gaze reselection",
        "- scene partition: **none** — no foreground/background decomposition, panorama, shell, or special background object",
        f"- native measurements: **{native_total:,}**",
        f"- guarded measurements: **{guarded_total:,}**",
        f"- oracle damage-control rejection: **{(native_total-guarded_total):,} ({report['guard_rejected_fraction']:.2%})**",
        f"- native fused scene: **{native_summary['surfels']:,} surfels / {native_summary['instantiated_objects']} instantiated objects**",
        f"- guarded fused scene: **{guarded_summary['surfels']:,} surfels / {guarded_summary['instantiated_objects']} instantiated objects**",
        "", "## Provenance", "",
        "Native geometry comes only from unchanged `fsg_stereo.py`. The guarded stream is a boolean row-subset of native stereo output; Blender truth rejects gross range errors after stereo and never supplies xyz.",
        "", "## Interpretation boundary", "",
        "This experiment tests the completed tangent-plane measurement bridge under a frozen attention sequence. It does not test autonomous attention, foreground/background decomposition, truth-free guarded validity, or matcher optimality.",
    ]
    (out / "classroom_fsg1_report.md").write_text("\n".join(md) + "\n")
    print(
        f"CLASSROOM_FSG1_COMPLETE full={full_run} fixations={len(fix_rows)} "
        f"native={native_total} guarded={guarded_total} "
        f"native_surfels={native_summary['surfels']} guarded_surfels={guarded_summary['surfels']}",
        flush=True,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[classroom-fsg1] FAIL {type(e).__name__}: {e}", file=sys.stderr)
        raise SystemExit(1)
