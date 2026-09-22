"""Instantiate the MultiObject-2a selected object with one prescribed seed fixation."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

import multiobject1c_audit as history_audit
import multiobject2a_public as parent_public
import multiobject2b_public as public
from multiobject2b_seed import select_seed_from_saved_evidence
from multiobject1a_seed import xyz_to_yaw_pitch_deg

import fsg_stereo_hdr as hdr
from fsg_stereo_supported import compute_once, check_kernel_equivalence
from fsg3_surface_map import load_map
from fsg_geometry import json_write
from reality1_run import _tone_preview


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _resolve(path_like: str, base: Path) -> Path:
    p = Path(path_like)
    return p if p.is_absolute() else (base / p).resolve()


def _validate_parent(parent: Path) -> tuple[dict, dict]:
    m = json.loads((parent / "prediction_manifest.json").read_text())
    if m.get("schema") != public.PARENT_SPEC_ID:
        raise AssertionError("MultiObject-2b requires a completed MultiObject-2a parent")
    if m.get("public_spec_sha256") != parent_public.public_digest():
        raise AssertionError("MultiObject-2a public digest mismatch")
    if int(m.get("seed", -1)) != public.SEED or m.get("truth_opened") is not False:
        raise AssertionError("wrong seed or truth integrity broken")
    if int(m.get("acquisitions_added", -1)) != 0 or int(m.get("growth_iterations_added", -1)) != 0:
        raise AssertionError("MultiObject-2a parent was not read-only")
    if m.get("new_object_instantiated") is not False or not m.get("objects_141_143_read_only"):
        raise AssertionError("MultiObject-2a changed existing scene objects")
    if m.get("selection_status") != "NEXT_OBJECT_SELECTED":
        raise AssertionError("MultiObject-2a did not select a next object")
    selected = int(m.get("selected_object_id", -1))
    if selected <= 0 or selected in set(public.EXISTING_OBJECT_IDS):
        raise AssertionError("parent selected id is invalid or already instantiated")
    report = json.loads((parent / m["selection_report"]).read_text())
    if int(report.get("selected_object_id", -1)) != selected:
        raise AssertionError("MultiObject-2a report/manifest selected id mismatch")
    if int(report.get("selected_valid_depth_samples", -1)) != int(m.get("selected_valid_depth_samples", -2)):
        raise AssertionError("MultiObject-2a selected support mismatch")
    return m, report


def _scene_history(parent: Path, pm: dict) -> tuple[Path, dict]:
    scene = _resolve(pm["scene_history_record"], parent)
    sm = json.loads((scene / "prediction_manifest.json").read_text())
    if sm.get("schema") != "MultiObject1b2-resume-object143-growth-v2":
        raise AssertionError("MultiObject-2a scene history is not completed MultiObject-1b2")
    if sm.get("truth_opened") is not False or sm.get("object_ids") != list(public.EXISTING_OBJECT_IDS):
        raise AssertionError("scene-history truth/object contract changed")
    if not sm.get("object_1_read_only") or not sm.get("object_2_map_pure"):
        raise AssertionError("scene-history object integrity broken")
    return scene, sm


def _audit_parent(parent: Path, pm: dict) -> tuple[Path, dict]:
    audit = _resolve(pm["parent_record"], parent)
    am = json.loads((audit / "prediction_manifest.json").read_text())
    if am.get("schema") != "MultiObject1c-object143-epistemic-audit-v1":
        raise AssertionError("MultiObject-2a parent_record is not MultiObject-1c")
    if am.get("summary", {}).get("scene_disposition") != "MOVE_TO_NEXT_OBJECT":
        raise AssertionError("scene progress was not released by MultiObject-1c")
    return audit, am


def _scene_object_sources(scene: Path) -> tuple[Path, Path]:
    graph = json.loads((scene / "scene_graph.json").read_text())
    by_id = {int(o["object_id"]): o for o in graph.get("objects", [])}
    if set(public.EXISTING_OBJECT_IDS) - set(by_id):
        raise AssertionError("scene graph is missing an existing object")
    s1 = _resolve(by_id[141]["source"], scene)
    s2 = _resolve(by_id[143]["source"], scene)
    if not s1.is_file() or not s2.is_file():
        raise FileNotFoundError("existing scene-object geometry source missing")
    return s1, s2


def _case_hashes(cases: list[tuple[int, Path]]) -> dict[str, dict[str, str]]:
    return {
        f"fix_{step:02d}": {
            "calibration.json": _sha256(case / "calibration.json"),
            "observation.npz": _sha256(case / "observation.npz"),
        }
        for step, case in cases
    }


def _run_scene_blender(args, profile: str, step: int, gaze: tuple[float, float]) -> Path:
    out = args.out / "acquisition"
    cmd = [
        args.blender, "-b", "--python-exit-code", "1",
        "-P", public.SCENE_RENDERER, "--",
        "--out", str(out), "--profile", profile, "--seed", str(public.SEED),
        "--step", str(step), "--yaw", f"{gaze[0]:.12g}",
        "--pitch", f"{gaze[1]:.12g}", "--device", args.device,
    ]
    p = subprocess.run(cmd, cwd=args.repo, text=True, capture_output=True)
    (args.out / "render.log").write_text(p.stdout + "\n--- STDERR ---\n" + p.stderr)
    if p.returncode != 0:
        raise RuntimeError("MultiObject-2b Blender seed fixation failed; see render.log")
    return out / f"fix_{step:02d}"


def _shared_chart(objects: list[tuple[int, np.ndarray]], grid_deg: float):
    # Existing scene objects define the chart even if the one-look seed happens to
    # yield zero valid target points.  Seed point count is a measurement, not a gate.
    angles = []
    nonempty = []
    for oid, xyz in objects:
        yaw, pitch = xyz_to_yaw_pitch_deg(xyz)
        angles.append((int(oid), yaw, pitch))
        if len(yaw):
            nonempty.append((int(oid), yaw, pitch))
    if not nonempty:
        raise AssertionError("scene has no finite angular support")
    g = float(grid_deg)
    ymin = np.floor((min(float(y.min()) for _, y, _ in nonempty) - 0.5) / g) * g
    ymax = np.ceil((max(float(y.max()) for _, y, _ in nonempty) + 0.5) / g) * g
    pmin = np.floor((min(float(p.min()) for _, _, p in nonempty) - 0.5) / g) * g
    pmax = np.ceil((max(float(p.max()) for _, _, p in nonempty) + 0.5) / g) * g
    w = int(round((ymax - ymin) / g)) + 1
    h = int(round((pmax - pmin) / g)) + 1
    fps = {}
    for oid, yaw, pitch in angles:
        fp = np.zeros((h, w), dtype=bool)
        if len(yaw):
            x = np.rint((yaw - ymin) / g).astype(int)
            y = np.rint((pitch - pmin) / g).astype(int)
            good = (x >= 0) & (x < w) & (y >= 0) & (y < h)
            fp[y[good], x[good]] = True
        fps[int(oid)] = fp
    chart = {
        "yaw0_deg": float(ymin), "pitch0_deg": float(pmin), "grid_deg": g,
        "width": int(w), "height": int(h),
    }
    return chart, fps


def _overlap_counts(fps: dict[int, np.ndarray]) -> dict[str, int]:
    ids = sorted(fps)
    out = {str(oid): int(fps[oid].sum()) for oid in ids}
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            out[f"overlap_{a}_{b}"] = int((fps[a] & fps[b]).sum())
    if len(ids) >= 3:
        both = np.ones_like(next(iter(fps.values())), dtype=bool)
        for oid in ids:
            both &= fps[oid]
        out["overlap_all"] = int(both.sum())
    return out


def _write_scene_png(path: Path, fps: dict[int, np.ndarray]) -> None:
    ids = sorted(fps)
    shape = next(iter(fps.values())).shape
    im = np.zeros(shape, dtype=np.uint8)
    levels = np.linspace(70, 210, num=max(1, len(ids))).astype(np.uint8)
    claims = np.zeros(shape, dtype=np.uint8)
    for level, oid in zip(levels, ids):
        im[fps[oid]] = level
        claims += fps[oid].astype(np.uint8)
    im[claims > 1] = 255
    Image.fromarray(np.flipud(im), mode="L").resize(
        (shape[1] * 3, shape[0] * 3), Image.Resampling.NEAREST
    ).save(path)


def execute(args) -> dict:
    args.repo = Path(args.repo).resolve()
    args.parent = Path(args.parent).resolve()
    args.out = Path(args.out).resolve()
    if args.out.exists():
        raise FileExistsError("output must be new")
    args.out.mkdir(parents=True)
    check_kernel_equivalence()

    pm, selection_report = _validate_parent(args.parent)
    scene, sm = _scene_history(args.parent, pm)
    audit, audit_manifest = _audit_parent(args.parent, pm)
    selected_id = int(pm["selected_object_id"])

    parent_files = ["prediction_manifest.json", "next_object_selection.json"]
    parent_hash_before = {n: _sha256(args.parent / n) for n in parent_files}
    scene_files = ["prediction_manifest.json", "scene_graph.json", "object_143_surface_map.npz"]
    scene_hash_before = {n: _sha256(scene / n) for n in scene_files}
    audit_files = ["prediction_manifest.json", "object_143_epistemic_report.json"]
    audit_hash_before = {n: _sha256(audit / n) for n in audit_files}

    object1_source, object2_source = _scene_object_sources(scene)
    object1_hash_before = _sha256(object1_source)
    object2_hash_before = _sha256(object2_source)
    object1 = load_map(object1_source)
    object2 = load_map(object2_source)
    if set(np.unique(object1.instance_id).tolist()) != {141}:
        raise AssertionError("object 141 source is not pure")
    if set(np.unique(object2.instance_id).tolist()) != {143}:
        raise AssertionError("object 143 source is not pure")

    cases = history_audit._all_cases(scene, sm)
    steps = [int(s) for s, _ in cases]
    if steps != [int(x) for x in pm.get("observation_steps", [])]:
        raise AssertionError("MultiObject-2a evidence-step scope no longer matches scene history")
    if len(cases) != int(pm.get("observation_count", -1)):
        raise AssertionError("MultiObject-2a evidence observation count changed")
    observation_hash_before = _case_hashes(cases)
    observations = [history_audit._saved_observation(step, case) for step, case in cases]

    seed_selection = select_seed_from_saved_evidence(observations, selected_id, public.GRID_DEG)
    if int(seed_selection["valid_depth_evidence_points"]) != int(pm["selected_valid_depth_samples"]):
        raise AssertionError("seed evidence does not reproduce MultiObject-2a selected support")
    candidate = next((r for r in selection_report["candidates"] if int(r["object_id"]) == selected_id), None)
    if candidate is None or int(candidate["valid_depth_samples"]) != int(seed_selection["valid_depth_evidence_points"]):
        raise AssertionError("selected-object candidate evidence changed between 2a and 2b")

    gaze = tuple(map(float, seed_selection["probe_gaze_deg"]))
    global_step = int(max(steps) + 1)
    profile = str(sm.get("profile", "full"))
    case = _run_scene_blender(args, profile, global_step, gaze)
    c, obs = hdr.read_observation(case)
    rec, _meta, _state = compute_once(c, obs)
    target = np.asarray(rec["valid"], bool) & (np.asarray(rec["instance_id"]) == selected_id)
    xyz = np.asarray(rec["xyz_h"][target], dtype=np.float32)
    rgb = np.asarray(rec["rgb_left"][target], dtype=np.float32)
    ids = np.asarray(rec["instance_id"][target])

    patch_name = f"object_{selected_id}_seed_patch.npz"
    preview_name = f"object_{selected_id}_seed_rgb.png"
    np.savez_compressed(
        args.out / patch_name,
        xyz_h=xyz, rgb=rgb, instance_id=ids,
        valid=np.asarray(rec["valid"], bool),
        oracle_instance_id=np.asarray(rec["instance_id"]),
        raw_support_L=np.asarray(rec["raw_support_L"], bool),
    )
    Image.fromarray(_tone_preview(rec["rgb_left"])).save(args.out / preview_name)

    chart, fps = _shared_chart(
        [(141, object1.xyz_h), (143, object2.xyz_h), (selected_id, xyz)], public.GRID_DEG
    )
    fp_payload = {f"object_{oid}": fp for oid, fp in fps.items()}
    np.savez_compressed(args.out / "scene_cyclopean_footprints.npz", **fp_payload, **chart)
    _write_scene_png(args.out / "scene_cyclopean_footprints.png", fps)
    footprint_counts = _overlap_counts(fps)

    valid_ids, valid_counts = np.unique(np.asarray(rec["instance_id"])[np.asarray(rec["valid"], bool)], return_counts=True)
    valid_by_instance = {str(int(i)): int(n) for i, n in zip(valid_ids, valid_counts) if int(i) > 0}

    scene_graph = {
        "schema": "MultiObject2b-scene-graph-v1",
        "fixed_head": True,
        "static_scene": True,
        "objects": [
            {
                "object_id": 141,
                "geometry": "SURFEL_MAP",
                "source": str(object1_source),
                "source_sha256": object1_hash_before,
                "point_count": int(len(object1.xyz_h)),
                "read_only": True,
            },
            {
                "object_id": 143,
                "geometry": "SURFEL_MAP",
                "source": str(object2_source),
                "source_sha256": object2_hash_before,
                "point_count": int(len(object2.xyz_h)),
                "read_only": True,
                "retained_status": audit_manifest.get("summary", {}).get("object_143_status"),
            },
            {
                "object_id": selected_id,
                "geometry": "SEED_SURFEL_PATCH",
                "source": str(args.out / patch_name),
                "point_count": int(len(xyz)),
                "read_only": False,
                "selection_source": str(args.parent / "next_object_selection.json"),
                "seed_global_step": global_step,
            },
        ],
        "cyclopean_chart": chart,
        "raw_footprint_cells": footprint_counts,
    }
    json_write(args.out / "scene_graph.json", scene_graph)

    if {n: _sha256(args.parent / n) for n in parent_files} != parent_hash_before:
        raise AssertionError("MultiObject-2a parent changed during seed acquisition")
    if {n: _sha256(scene / n) for n in scene_files} != scene_hash_before:
        raise AssertionError("scene-history record changed during seed acquisition")
    if {n: _sha256(audit / n) for n in audit_files} != audit_hash_before:
        raise AssertionError("MultiObject-1c audit changed during seed acquisition")
    if _sha256(object1_source) != object1_hash_before or _sha256(object2_source) != object2_hash_before:
        raise AssertionError("existing object geometry changed during third-object seed")
    if _case_hashes(cases) != observation_hash_before:
        raise AssertionError("saved evidence history changed during third-object seed")

    object_ids_after = [141, 143, selected_id]
    manifest = {
        "schema": public.SPEC_ID,
        "public_spec_sha256": public.public_digest(),
        "parent_spec": public.PARENT_SPEC_ID,
        "parent_record": str(args.parent),
        "scene_history_record": str(scene),
        "audit_record": str(audit),
        "seed": public.SEED,
        "profile": profile,
        "fixture": public.FIXTURE,
        "fixed_head": True,
        "static_scene": True,
        "truth_opened": False,
        "existing_object_ids_before": list(public.EXISTING_OBJECT_IDS),
        "selected_object_id": selected_id,
        "object_ids_after": object_ids_after,
        "selection_consumed_from_parent": True,
        "selected_valid_depth_samples": int(pm["selected_valid_depth_samples"]),
        "seed_selection": seed_selection,
        "probe_gaze_deg": [float(gaze[0]), float(gaze[1])],
        "evidence_observation_steps": steps,
        "global_step": global_step,
        "added_fixations": 1,
        "parent_fixations_rerendered": 0,
        "fusion_iterations_added": 0,
        "growth_iterations_added": 0,
        "new_object_instantiated": True,
        "existing_objects_read_only": True,
        "selected_object_seed_points": int(len(xyz)),
        "selected_object_patch_pure": bool(len(ids) == 0 or set(np.unique(ids).tolist()) == {selected_id}),
        "valid_points_by_instance_in_seed_view": valid_by_instance,
        "object_141_sha256_before": object1_hash_before,
        "object_141_sha256_after": _sha256(object1_source),
        "object_143_sha256_before": object2_hash_before,
        "object_143_sha256_after": _sha256(object2_source),
        "parent_hashes": parent_hash_before,
        "scene_history_hashes": scene_hash_before,
        "audit_hashes": audit_hash_before,
        "observation_hashes": observation_hash_before,
        "seed_patch": patch_name,
        "seed_preview": preview_name,
        "scene_graph": "scene_graph.json",
        "scene_footprints": "scene_cyclopean_footprints.npz",
        "scene_footprint_counts": footprint_counts,
        "renderer_entrypoint": public.SCENE_RENDERER,
        "quality_gate_used": False,
        "automatic_scene_scheduler": False,
        "next_stage": public.PUBLIC_SPEC["next_stage"],
        "structural_fails": [],
    }
    json_write(args.out / "prediction_manifest.json", manifest)
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--parent", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--blender", default="blender")
    ap.add_argument("--device", choices=("OPTIX", "CUDA", "CPU"), default="OPTIX")
    m = execute(ap.parse_args())
    print("[multiobject2b-run] MULTIOBJECT2B_COMPLETE " + json.dumps({
        "selected_object_id": m["selected_object_id"],
        "global_step": m["global_step"],
        "probe_gaze_deg": m["probe_gaze_deg"],
        "selected_object_seed_points": m["selected_object_seed_points"],
        "object_ids_after": m["object_ids_after"],
        "structural_fails": m["structural_fails"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
