"""Instantiate the MultiObject-3a selected object with one prescribed seed fixation."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

import multiobject1c_audit as old_history
import multiobject2d_audit as new_history
import multiobject3a_public as parent_public
import multiobject3b_public as public
from multiobject3b_seed import select_seed_from_saved_evidence
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
    return p.resolve() if p.is_absolute() else (base / p).resolve()


def _validate_parent(parent: Path) -> tuple[dict, dict]:
    m = json.loads((parent / "prediction_manifest.json").read_text())
    if m.get("schema") != public.PARENT_SPEC_ID:
        raise AssertionError("MultiObject-3b requires a completed MultiObject-3a parent")
    if m.get("public_spec_sha256") != parent_public.public_digest():
        raise AssertionError("MultiObject-3a public digest mismatch")
    if int(m.get("seed", -1)) != public.SEED or m.get("truth_opened") is not False:
        raise AssertionError("wrong seed or truth integrity broken")
    if int(m.get("acquisitions_added", -1)) != 0 or int(m.get("growth_iterations_added", -1)) != 0:
        raise AssertionError("MultiObject-3a parent was not read-only")
    if m.get("new_object_instantiated") is not False or not m.get("scene_objects_read_only"):
        raise AssertionError("MultiObject-3a changed the scene")
    if m.get("selection_status") != "NEXT_OBJECT_SELECTED":
        raise AssertionError("MultiObject-3a did not select a next object")
    selected = int(m.get("selected_object_id", -1))
    existing_ids = tuple(int(x) for x in m.get("instantiated_object_ids", []))
    if selected <= 0 or not existing_ids or selected in set(existing_ids):
        raise AssertionError("parent selected id is invalid or already instantiated")
    report = json.loads((parent / m["selection_report"]).read_text())
    if int(report.get("selected_object_id", -1)) != selected:
        raise AssertionError("MultiObject-3a report/manifest selected id mismatch")
    if int(report.get("selected_valid_depth_samples", -1)) != int(m.get("selected_valid_depth_samples", -2)):
        raise AssertionError("MultiObject-3a selected support mismatch")
    return m, report


def _scene_records(parent: Path, pm: dict) -> tuple[Path, dict, Path, dict]:
    growth = _resolve(pm["scene_growth_record"], parent)
    gm = json.loads((growth / "prediction_manifest.json").read_text())
    if gm.get("schema") != "MultiObject2c-grow-selected-object-v1":
        raise AssertionError("MultiObject-3a scene_growth_record is not completed MultiObject-2c")
    if gm.get("truth_opened") is not False:
        raise AssertionError("scene growth record opened truth")
    old_scene = _resolve(pm["old_scene_history_record"], parent)
    om = json.loads((old_scene / "prediction_manifest.json").read_text())
    if om.get("schema") != "MultiObject1b2-resume-object143-growth-v2":
        raise AssertionError("MultiObject-3a old_scene_history_record is not completed MultiObject-1b2")
    if om.get("truth_opened") is not False:
        raise AssertionError("old scene history opened truth")
    return growth, gm, old_scene, om


def _scene_object_sources(growth: Path, expected_ids: tuple[int, ...]) -> tuple[dict[int, dict], dict[int, Path], dict[int, object], dict[int, str]]:
    graph = json.loads((growth / "scene_graph.json").read_text())
    by_id = {int(o["object_id"]): o for o in graph.get("objects", [])}
    if tuple(sorted(by_id)) != tuple(sorted(expected_ids)):
        raise AssertionError("live scene graph ids differ from MultiObject-3a instantiated ids")
    paths: dict[int, Path] = {}
    maps: dict[int, object] = {}
    hashes: dict[int, str] = {}
    for oid in expected_ids:
        src = _resolve(by_id[oid]["source"], growth)
        if not src.is_file():
            raise FileNotFoundError(src)
        sm = load_map(src)
        if set(np.unique(sm.instance_id).tolist()) != {int(oid)}:
            raise AssertionError(f"scene object {oid} source is not pure")
        paths[oid] = src
        maps[oid] = sm
        hashes[oid] = _sha256(src)
    return by_id, paths, maps, hashes


def _case_hashes(cases: list[tuple[int, Path]]) -> dict[str, dict[str, str]]:
    return {
        f"fix_{step:02d}": {
            "calibration.json": _sha256(case / "calibration.json"),
            "observation.npz": _sha256(case / "observation.npz"),
        }
        for step, case in cases
    }


def _combined_history(growth: Path, gm: dict, old_scene: Path, om: dict, pm: dict):
    old_cases = old_history._all_cases(old_scene, om)
    new_cases = new_history._all_cases(growth, gm)
    cases = sorted(old_cases + new_cases, key=lambda x: int(x[0]))
    steps = [int(s) for s, _ in cases]
    if len(set(steps)) != len(steps):
        raise AssertionError("combined MultiObject-3a evidence scope has duplicate steps")
    if steps != [int(x) for x in pm.get("observation_steps", [])]:
        raise AssertionError("combined evidence steps no longer match MultiObject-3a")
    if len(cases) != int(pm.get("observation_count", -1)):
        raise AssertionError("combined evidence observation count changed")
    observations = []
    for step, case in old_cases:
        observations.append(old_history._saved_observation(step, case))
    for step, case in new_cases:
        observations.append(new_history._saved_observation(step, case))
    observations.sort(key=lambda ob: int(ob["step"]))
    return cases, observations


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
        raise RuntimeError("MultiObject-3b Blender seed fixation failed; see render.log")
    return out / f"fix_{step:02d}"


def _shared_chart(objects: list[tuple[int, np.ndarray]], grid_deg: float):
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
    if len(ids) >= 2:
        all_claim = np.ones_like(next(iter(fps.values())), dtype=bool)
        for oid in ids:
            all_claim &= fps[oid]
        out["overlap_all"] = int(all_claim.sum())
    return out


def _write_scene_png(path: Path, fps: dict[int, np.ndarray]) -> None:
    ids = sorted(fps)
    shape = next(iter(fps.values())).shape
    im = np.zeros(shape, dtype=np.uint8)
    levels = np.linspace(50, 220, num=max(1, len(ids))).astype(np.uint8)
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
    existing_ids = tuple(int(x) for x in pm["instantiated_object_ids"])
    selected_id = int(pm["selected_object_id"])
    growth, gm, old_scene, om = _scene_records(args.parent, pm)
    _graph, object_paths, object_maps, object_hash_before = _scene_object_sources(growth, existing_ids)

    parent_files = ["prediction_manifest.json", pm["selection_report"]]
    parent_hash_before = {n: _sha256(args.parent / n) for n in parent_files}
    growth_files = ["prediction_manifest.json", "scene_graph.json"]
    growth_hash_before = {n: _sha256(growth / n) for n in growth_files}

    cases, observations = _combined_history(growth, gm, old_scene, om, pm)
    steps = [int(s) for s, _ in cases]
    observation_hash_before = _case_hashes(cases)

    seed_selection = select_seed_from_saved_evidence(observations, selected_id, public.GRID_DEG)
    if int(seed_selection["valid_depth_evidence_points"]) != int(pm["selected_valid_depth_samples"]):
        raise AssertionError("seed evidence does not reproduce MultiObject-3a selected support")
    candidate = next((r for r in selection_report["candidates"] if int(r["object_id"]) == selected_id), None)
    if candidate is None or int(candidate["valid_depth_samples"]) != int(seed_selection["valid_depth_evidence_points"]):
        raise AssertionError("selected-object candidate evidence changed between 3a and 3b")

    gaze = tuple(map(float, seed_selection["probe_gaze_deg"]))
    global_step = int(max(steps) + 1)
    profile = str(pm.get("profile", "full"))
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

    scene_objects = [(oid, object_maps[oid].xyz_h) for oid in existing_ids]
    scene_objects.append((selected_id, xyz))
    chart, fps = _shared_chart(scene_objects, public.GRID_DEG)
    fp_payload = {f"object_{oid}": fp for oid, fp in fps.items()}
    np.savez_compressed(args.out / "scene_cyclopean_footprints.npz", **fp_payload, **chart)
    _write_scene_png(args.out / "scene_cyclopean_footprints.png", fps)
    footprint_counts = _overlap_counts(fps)

    valid_ids, valid_counts = np.unique(
        np.asarray(rec["instance_id"])[np.asarray(rec["valid"], bool)], return_counts=True
    )
    valid_by_instance = {str(int(i)): int(n) for i, n in zip(valid_ids, valid_counts) if int(i) > 0}
    visible_selected = int(np.count_nonzero(np.asarray(rec["instance_id"]) == selected_id))
    valid_selected = int(np.count_nonzero(target))
    recovered_fraction = float(valid_selected / visible_selected) if visible_selected else None

    graph_objects = []
    for oid in existing_ids:
        graph_objects.append({
            "object_id": int(oid),
            "geometry": "SURFEL_MAP",
            "source": str(object_paths[oid]),
            "source_sha256": object_hash_before[oid],
            "point_count": int(len(object_maps[oid].xyz_h)),
            "read_only": True,
        })
    graph_objects.append({
        "object_id": int(selected_id),
        "geometry": "SEED_SURFEL_PATCH",
        "source": str(args.out / patch_name),
        "point_count": int(len(xyz)),
        "read_only": False,
        "selection_source": str(args.parent / pm["selection_report"]),
        "seed_global_step": global_step,
    })
    scene_graph = {
        "schema": "MultiObject3b-scene-graph-v1",
        "fixed_head": True,
        "static_scene": True,
        "objects": graph_objects,
        "cyclopean_chart": chart,
        "raw_footprint_cells": footprint_counts,
    }
    json_write(args.out / "scene_graph.json", scene_graph)

    if {n: _sha256(args.parent / n) for n in parent_files} != parent_hash_before:
        raise AssertionError("MultiObject-3a parent changed during seed acquisition")
    if {n: _sha256(growth / n) for n in growth_files} != growth_hash_before:
        raise AssertionError("current scene record changed during seed acquisition")
    if {oid: _sha256(path) for oid, path in object_paths.items()} != object_hash_before:
        raise AssertionError("existing object geometry changed during fourth-object seed")
    if _case_hashes(cases) != observation_hash_before:
        raise AssertionError("saved updated evidence history changed during fourth-object seed")

    object_ids_after = [*existing_ids, selected_id]
    manifest = {
        "schema": public.SPEC_ID,
        "public_spec_sha256": public.public_digest(),
        "parent_spec": public.PARENT_SPEC_ID,
        "parent_record": str(args.parent),
        "scene_growth_record": str(growth),
        "old_scene_history_record": str(old_scene),
        "seed": public.SEED,
        "profile": profile,
        "fixture": public.FIXTURE,
        "fixed_head": True,
        "static_scene": True,
        "truth_opened": False,
        "existing_object_ids_before": list(existing_ids),
        "selected_object_id": selected_id,
        "object_ids_after": object_ids_after,
        "selection_consumed_from_parent": True,
        "selected_valid_depth_samples": int(pm["selected_valid_depth_samples"]),
        "seed_selection": seed_selection,
        "probe_gaze_deg": [float(gaze[0]), float(gaze[1])],
        "evidence_observation_steps": steps,
        "evidence_observation_count": len(steps),
        "global_step": global_step,
        "added_fixations": 1,
        "parent_fixations_rerendered": 0,
        "fusion_iterations_added": 0,
        "growth_iterations_added": 0,
        "new_object_instantiated": True,
        "existing_objects_read_only": True,
        "selected_object_seed_points": int(len(xyz)),
        "selected_object_visible_pixels": visible_selected,
        "selected_object_depth_recovery_fraction": recovered_fraction,
        "selected_object_patch_pure": bool(len(ids) == 0 or set(np.unique(ids).tolist()) == {selected_id}),
        "valid_points_by_instance_in_seed_view": valid_by_instance,
        "existing_object_sha256_before": {str(k): v for k, v in object_hash_before.items()},
        "existing_object_sha256_after": {str(k): _sha256(object_paths[k]) for k in object_paths},
        "parent_hashes": parent_hash_before,
        "scene_growth_hashes": growth_hash_before,
        "observation_hashes": observation_hash_before,
        "seed_patch": patch_name,
        "seed_preview": preview_name,
        "scene_graph": "scene_graph.json",
        "scene_footprints": "scene_cyclopean_footprints.npz",
        "scene_footprint_counts": footprint_counts,
        "renderer_entrypoint": public.SCENE_RENDERER,
        "quality_gate_used": False,
        "automatic_scene_scheduler": False,
        "revisit_scheduler_used": False,
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
    print("[multiobject3b-run] MULTIOBJECT3B_COMPLETE " + json.dumps({
        "selected_object_id": m["selected_object_id"],
        "global_step": m["global_step"],
        "probe_gaze_deg": m["probe_gaze_deg"],
        "selected_object_seed_points": m["selected_object_seed_points"],
        "object_ids_after": m["object_ids_after"],
        "structural_fails": m["structural_fails"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
