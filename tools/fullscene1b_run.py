"""Seed the FullScene-1a selected next object with exactly one prescribed fixation."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

import fullscene1a_public as parent_public
import fullscene1a_run as fs1a_run
import fullscene1b_public as public
from multiobject3b_seed import select_seed_from_saved_evidence
from multiobject3b_run import _shared_chart, _overlap_counts, _write_scene_png

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
    p = parent / "prediction_manifest.json"
    if not p.is_file():
        raise FileNotFoundError(p)
    m = json.loads(p.read_text())
    if m.get("schema") != public.PARENT_SPEC_ID:
        raise AssertionError("FullScene-1b requires a completed FullScene-1a S0 parent")
    if m.get("public_spec_sha256") != parent_public.public_digest():
        raise AssertionError("FullScene-1a public digest mismatch")
    if int(m.get("seed", -1)) != public.SEED or m.get("truth_opened") is not False:
        raise AssertionError("wrong seed or truth integrity broken")
    if m.get("snapshot_id") != parent_public.SNAPSHOT_ID or m.get("fullscene_initial_condition") is not True:
        raise AssertionError("parent is not the declared FullScene S0 initial condition")
    if m.get("selection_status") != "NEXT_OBJECT_SELECTED":
        raise AssertionError("FullScene-1a did not select a next object")
    if int(m.get("acquisitions_added", -1)) != 0 or int(m.get("fusion_iterations_added", -1)) != 0:
        raise AssertionError("FullScene-1a parent was not read-only")
    if m.get("deferred_local_action_executed") is not False:
        raise AssertionError("deferred prior-object action was already executed")
    if m.get("automatic_scene_scheduler") is not False or m.get("revisit_scheduler_used") is not False:
        raise AssertionError("FullScene-1a unexpectedly introduced a scheduler")
    selected = int(m.get("selected_object_id", -1))
    existing = tuple(int(x) for x in m.get("instantiated_object_ids", []))
    if selected <= 0 or not existing or selected in set(existing):
        raise AssertionError("invalid S0 selected or instantiated object ids")
    report = json.loads((parent / m["snapshot_report"]).read_text())
    if int(report.get("selected_object_id", -1)) != selected:
        raise AssertionError("FullScene-1a report/manifest selected id mismatch")
    if int(report.get("selected_valid_depth_samples", -1)) != int(m.get("selected_valid_depth_samples", -2)):
        raise AssertionError("FullScene-1a selected support mismatch")
    return m, report


def _case_hashes(cases: list[tuple[int, Path]]) -> dict[str, dict[str, str]]:
    return {
        f"fix_{step:02d}": {
            "calibration.json": _sha256(case / "calibration.json"),
            "observation.npz": _sha256(case / "observation.npz"),
        }
        for step, case in cases
    }


def _rebuild_s0_history(parent: Path, pm: dict):
    parent3h = _resolve(pm["parent_record"], parent)
    m3h = fs1a_run._validate_parent(parent3h)
    chain = fs1a_run._ancestry(parent3h, m3h)
    cases, observations, groups = fs1a_run._history(parent3h, m3h, chain)
    steps = [int(s) for s, _ in cases]
    if steps != [int(x) for x in pm.get("observation_steps", [])]:
        raise AssertionError("reconstructed S0 history steps differ from FullScene-1a")
    if len(observations) != int(pm.get("observation_count", -1)):
        raise AssertionError("reconstructed S0 history count differs from FullScene-1a")
    # FullScene-1a only ever needed instance ids and valid masks, so its history
    # builder projects each observation down to those two arrays.  The frozen
    # multiobject3b_seed evidence rule additionally needs the reconstructed xyz,
    # so re-read exactly the same declared cases through the unchanged stereo
    # front end and attach it.  The scope is not widened: the cases, their order
    # and their count are the ones _history already returned and validated.
    by_step = {int(step): case for step, case in cases}
    for ob in observations:
        if "xyz_h" in ob:
            continue
        c, obs = hdr.read_observation(by_step[int(ob["step"])])
        rec, _meta, _state = compute_once(c, obs)
        if not np.array_equal(np.asarray(rec["instance_id"]), np.asarray(ob["instance_id"])):
            raise AssertionError("S0 history re-read disagrees with FullScene-1a instance ids")
        if not np.array_equal(np.asarray(rec["valid"], bool), np.asarray(ob["valid"], bool)):
            raise AssertionError("S0 history re-read disagrees with FullScene-1a valid mask")
        ob["xyz_h"] = np.asarray(rec["xyz_h"]).copy()
    return parent3h, cases, observations, groups


def _scene_objects(parent: Path, pm: dict, expected_ids: tuple[int, ...]):
    graph_path = _resolve(pm["scene_graph_source"], parent)
    graph = json.loads(graph_path.read_text())
    by_id = {int(row["object_id"]): row for row in graph.get("objects", [])}
    if tuple(sorted(by_id)) != tuple(sorted(expected_ids)):
        raise AssertionError("live S0 scene graph ids differ from FullScene-1a instantiated ids")
    paths: dict[int, Path] = {}
    maps: dict[int, object] = {}
    hashes: dict[int, str] = {}
    for oid in expected_ids:
        src = _resolve(by_id[oid]["source"], graph_path.parent)
        if not src.is_file():
            raise FileNotFoundError(src)
        sm = load_map(src)
        if len(sm.instance_id) and set(np.unique(sm.instance_id).tolist()) != {int(oid)}:
            raise AssertionError(f"persistent scene object {oid} is not instance-id pure")
        paths[oid] = src
        maps[oid] = sm
        hashes[oid] = _sha256(src)
    return graph_path, graph, paths, maps, hashes


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
        raise RuntimeError("FullScene-1b Blender seed fixation failed; see render.log")
    return out / f"fix_{step:02d}"


def execute(args) -> dict:
    args.repo = Path(args.repo).resolve()
    args.parent = Path(args.parent).resolve()
    args.out = Path(args.out).resolve()
    if args.out.exists():
        raise FileExistsError("output must be new")
    args.out.mkdir(parents=True)
    check_kernel_equivalence()

    pm, snapshot = _validate_parent(args.parent)
    existing_ids = tuple(int(x) for x in pm["instantiated_object_ids"])
    selected_id = int(pm["selected_object_id"])

    parent3h, cases, observations, history_groups = _rebuild_s0_history(args.parent, pm)
    steps = [int(s) for s, _ in cases]
    graph_path, _graph, object_paths, object_maps, object_hash_before = _scene_objects(
        args.parent, pm, existing_ids
    )

    parent_files = ["prediction_manifest.json", pm["snapshot_report"]]
    parent_hash_before = {n: _sha256(args.parent / n) for n in parent_files}
    graph_hash_before = _sha256(graph_path)
    observation_hash_before = _case_hashes(cases)

    seed_selection = select_seed_from_saved_evidence(observations, selected_id, public.GRID_DEG)
    if int(seed_selection["valid_depth_evidence_points"]) != int(pm["selected_valid_depth_samples"]):
        raise AssertionError("seed evidence does not reproduce FullScene-1a selected support")
    candidate = next((r for r in snapshot.get("candidates", []) if int(r["object_id"]) == selected_id), None)
    if candidate is None or int(candidate["valid_depth_samples"]) != int(seed_selection["valid_depth_evidence_points"]):
        raise AssertionError("selected-object evidence changed between FullScene-1a and FullScene-1b")

    gaze = tuple(map(float, seed_selection["probe_gaze_deg"]))
    global_step = int(max(steps) + 1)
    profile = str(pm.get("profile", "full"))
    case = _run_scene_blender(args, profile, global_step, gaze)
    c, obs = hdr.read_observation(case)
    rec, _meta, _state = compute_once(c, obs)

    valid = np.asarray(rec["valid"], dtype=bool)
    instance_id = np.asarray(rec["instance_id"])
    target = valid & (instance_id == selected_id)
    xyz = np.asarray(rec["xyz_h"][target], dtype=np.float32)
    rgb = np.asarray(rec["rgb_left"][target], dtype=np.float32)
    ids = np.asarray(instance_id[target])

    patch_name = f"object_{selected_id}_seed_patch.npz"
    preview_name = f"object_{selected_id}_seed_rgb.png"
    np.savez_compressed(
        args.out / patch_name,
        xyz_h=xyz,
        rgb=rgb,
        instance_id=ids,
        valid=valid,
        oracle_instance_id=instance_id,
        raw_support_L=np.asarray(rec["raw_support_L"], bool),
    )
    Image.fromarray(_tone_preview(rec["rgb_left"])).save(args.out / preview_name)

    scene_objects = [(oid, object_maps[oid].xyz_h) for oid in existing_ids]
    scene_objects.append((selected_id, xyz))
    chart, fps = _shared_chart(scene_objects, public.GRID_DEG)
    np.savez_compressed(
        args.out / "scene_cyclopean_footprints.npz",
        **{f"object_{oid}": fp for oid, fp in fps.items()},
        **chart,
    )
    _write_scene_png(args.out / "scene_cyclopean_footprints.png", fps)
    footprint_counts = _overlap_counts(fps)

    valid_ids, valid_counts = np.unique(instance_id[valid], return_counts=True)
    valid_by_instance = {
        str(int(i)): int(n) for i, n in zip(valid_ids, valid_counts) if int(i) > 0
    }
    visible_selected = int(np.count_nonzero(instance_id == selected_id))
    valid_selected = int(np.count_nonzero(target))
    recovery = float(valid_selected / visible_selected) if visible_selected else None

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
        "selection_source": str(args.parent / pm["snapshot_report"]),
        "seed_global_step": global_step,
    })
    scene_graph = {
        "schema": "FullScene1b-scene-graph-v1",
        "fixed_head": True,
        "static_scene": True,
        "objects": graph_objects,
        "cyclopean_chart": chart,
        "raw_footprint_cells": footprint_counts,
    }
    json_write(args.out / "scene_graph.json", scene_graph)

    # Full input-integrity guards after the only new physical action.
    if {n: _sha256(args.parent / n) for n in parent_files} != parent_hash_before:
        raise AssertionError("FullScene-1a parent changed during FullScene-1b")
    if _sha256(graph_path) != graph_hash_before:
        raise AssertionError("S0 live scene graph changed during FullScene-1b")
    if {oid: _sha256(path) for oid, path in object_paths.items()} != object_hash_before:
        raise AssertionError("pre-existing persistent object changed during FullScene-1b")
    if _case_hashes(cases) != observation_hash_before:
        raise AssertionError("saved S0 observation history changed during FullScene-1b")

    object_ids_after = [*existing_ids, selected_id]
    manifest = {
        "schema": public.SPEC_ID,
        "public_spec_sha256": public.public_digest(),
        "parent_spec": public.PARENT_SPEC_ID,
        "parent_record": str(args.parent),
        "source_snapshot_id": pm["snapshot_id"],
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
        "history_groups": history_groups,
        "global_step": global_step,
        "added_fixations": 1,
        "parent_fixations_rerendered": 0,
        "fusion_iterations_added": 0,
        "growth_iterations_added": 0,
        "epistemic_handoffs_added": 0,
        "new_object_instantiated": True,
        "existing_objects_read_only": True,
        "deferred_prior_object_action_executed": False,
        "selected_object_seed_points": int(len(xyz)),
        "selected_object_visible_pixels": visible_selected,
        "selected_object_depth_recovery_fraction": recovery,
        "selected_object_patch_pure": bool(len(ids) == 0 or set(np.unique(ids).tolist()) == {selected_id}),
        "valid_points_by_instance_in_seed_view": valid_by_instance,
        "existing_object_sha256_before": {str(k): v for k, v in object_hash_before.items()},
        "existing_object_sha256_after": {str(k): _sha256(object_paths[k]) for k in object_paths},
        "parent_hashes": parent_hash_before,
        "scene_graph_source_hash": graph_hash_before,
        "observation_hashes": observation_hash_before,
        "seed_patch": patch_name,
        "seed_preview": preview_name,
        "scene_graph": "scene_graph.json",
        "scene_footprints": "scene_cyclopean_footprints.npz",
        "scene_footprint_counts": footprint_counts,
        "renderer_entrypoint": public.SCENE_RENDERER,
        "quality_gate_used": False,
        "new_threshold_added": False,
        "semantic_ranking_used": False,
        "automatic_object_discovery": False,
        "automatic_scene_scheduler": False,
        "revisit_scheduler_used": False,
        "next_stage": public.NEXT_STAGE,
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
    print("[fullscene1b-run] FULLSCENE1B_COMPLETE " + json.dumps({
        "selected_object_id": m["selected_object_id"],
        "global_step": m["global_step"],
        "probe_gaze_deg": m["probe_gaze_deg"],
        "selected_object_seed_points": m["selected_object_seed_points"],
        "object_ids_after": m["object_ids_after"],
        "structural_fails": m["structural_fails"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
