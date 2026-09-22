"""Grow the FullScene-1b seeded object with the frozen FSG6f mechanism."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

import numpy as np
from PIL import Image

import fsg6f_public as frozen_public
import fsg6f_run as fsg6run
import fsg_stereo_hdr as hdr
from fsg3_surface_map import Patch, fuse, initialize, load_map, save_map
from fsg_geometry import json_write
from fsg_stereo import support_mask
from fsg_stereo_supported import check_kernel_equivalence, compute_once
from reality1_run import _tone_preview
import fullscene1b_public as parent_public
from multiobject3b_run import _shared_chart, _write_scene_png, _overlap_counts
import multiobject2c_policy as policy
import fullscene1c_public as public


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _resolve(path_like: str, base: Path) -> Path:
    p = Path(path_like)
    return p.resolve() if p.is_absolute() else (base / p).resolve()


def _validate_parent(parent: Path) -> tuple[dict, dict, int, tuple[int, ...], dict[int, dict]]:
    manifest_path = parent / "prediction_manifest.json"
    scene_path = parent / "scene_graph.json"
    if not manifest_path.is_file() or not scene_path.is_file():
        raise FileNotFoundError("FullScene-1b parent manifest/scene graph missing")
    m = json.loads(manifest_path.read_text())
    if m.get("schema") != public.PARENT_SPEC_ID:
        raise AssertionError("FullScene-1c requires a completed FullScene-1b parent")
    if m.get("public_spec_sha256") != parent_public.public_digest():
        raise AssertionError("FullScene-1b public digest mismatch")
    if int(m.get("seed", -1)) != public.SEED or m.get("truth_opened") is not False:
        raise AssertionError("wrong seed or truth integrity broken")
    if not m.get("fixed_head") or not m.get("static_scene"):
        raise AssertionError("fixed-head/static-scene invariant broken")
    if m.get("structural_fails") != []:
        raise AssertionError("FullScene-1b parent is structurally incomplete")
    if int(m.get("added_fixations", -1)) != 1 or int(m.get("parent_fixations_rerendered", -1)) != 0:
        raise AssertionError("FullScene-1b is not the declared one-look seed experiment")
    if int(m.get("fusion_iterations_added", -1)) != 0 or int(m.get("growth_iterations_added", -1)) != 0:
        raise AssertionError("FullScene-1b unexpectedly fused or grew the seed")
    if int(m.get("epistemic_handoffs_added", -1)) != 0:
        raise AssertionError("FullScene-1b unexpectedly added a handoff")
    if not m.get("new_object_instantiated") or not m.get("existing_objects_read_only"):
        raise AssertionError("FullScene-1b did not preserve the existing scene while seeding")
    if m.get("deferred_prior_object_action_executed") is not False:
        raise AssertionError("prior object's deferred action was executed")
    if m.get("automatic_scene_scheduler") is not False or m.get("revisit_scheduler_used") is not False:
        raise AssertionError("FullScene-1b unexpectedly introduced a scheduler")
    if m.get("quality_gate_used") is not False or m.get("new_threshold_added") is not False:
        raise AssertionError("FullScene-1b unexpectedly introduced a quality/threshold gate")

    target_id = int(m.get("selected_object_id", -1))
    existing_ids = tuple(int(x) for x in m.get("existing_object_ids_before", []))
    ids_after = tuple(int(x) for x in m.get("object_ids_after", []))
    if target_id <= 0 or not existing_ids or target_id in set(existing_ids):
        raise AssertionError("invalid parent-selected target object id")
    if ids_after != existing_ids + (target_id,):
        raise AssertionError("FullScene-1b object order/set changed")
    if int(m.get("selected_object_seed_points", -1)) <= 0 or not m.get("selected_object_patch_pure"):
        raise AssertionError("FullScene-1b selected-object seed is empty or impure")

    sg = json.loads(scene_path.read_text())
    objs = {int(o["object_id"]): o for o in sg.get("objects", [])}
    if set(objs) != set(ids_after):
        raise AssertionError("FullScene-1b scene graph/object ids disagree")
    for oid in existing_ids:
        if not objs[oid].get("read_only") or objs[oid].get("geometry") != "SURFEL_MAP":
            raise AssertionError(f"pre-existing object {oid} is not a read-only surfel map")
    if objs[target_id].get("geometry") != "SEED_SURFEL_PATCH":
        raise AssertionError("parent-selected object is not a seed patch")
    return m, sg, target_id, existing_ids, objs


def _seed_case(parent: Path, pm: dict) -> tuple[int, Path]:
    step = int(pm.get("global_step", -1))
    if step < 0:
        raise AssertionError("FullScene-1b seed global step missing")
    case = parent / "acquisition" / f"fix_{step:02d}"
    if not (case / "calibration.json").is_file() or not (case / "observation.npz").is_file():
        raise FileNotFoundError("FullScene-1b seed acquisition missing")
    return step, case


def _right_state(c: dict, rec: dict, state: dict) -> tuple[np.ndarray, np.ndarray]:
    x, y, cw, ch = map(int, rec["crop_xywh"])
    sl = np.s_[y:y+ch, x:x+cw]
    ids_R = state["ids_right"][sl]
    raw_R = support_mask(c, rec, "R")[sl]
    if not np.array_equal(rec["instance_id"], state["ids_left"][sl]):
        raise AssertionError("left rectified ID replay mismatch")
    return ids_R, raw_R


def _patch_from_record(pid: str, rec: dict, target_id: int) -> Patch:
    mask = np.asarray(rec["valid"], bool) & (np.asarray(rec["instance_id"]) == int(target_id))
    return Patch(
        pid,
        np.asarray(rec["xyz_h"])[mask],
        np.asarray(rec["rgb_left"])[mask],
        np.asarray(rec["instance_id"])[mask],
    )


def _save_patch(path: Path, p: Patch, rec: dict, ids_R: np.ndarray, raw_R: np.ndarray) -> None:
    np.savez_compressed(
        path,
        xyz_h=np.asarray(p.xyz_h, np.float32),
        rgb=np.asarray(p.rgb, np.float32),
        instance_id=np.asarray(p.instance_id),
        valid=np.asarray(rec["valid"], bool),
        oracle_instance_id=np.asarray(rec["instance_id"]),
        raw_support_L=np.asarray(rec["raw_support_L"], bool),
        oracle_instance_id_R=np.asarray(ids_R),
        raw_support_R=np.asarray(raw_R, bool),
    )


def _texture_stats(rec: dict, target_id: int) -> dict:
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


def _run_scene_blender(args, step: int, gaze: tuple[float, float], profile: str) -> Path:
    out = args.out / "acquisitions" / f"fix_{step:02d}"
    yaw, pitch = map(float, gaze)
    cmd = [
        args.blender, "-b", "--python-exit-code", "1",
        "-P", public.SCENE_RENDERER, "--",
        "--out", str(out), "--profile", profile, "--seed", str(public.SEED),
        "--step", str(step), "--yaw", f"{yaw:.12g}", "--pitch", f"{pitch:.12g}",
        "--device", args.device,
    ]
    p = subprocess.run(cmd, cwd=args.repo, text=True, capture_output=True)
    (args.out / "logs" / f"render_{step:02d}.log").write_text(p.stdout + "\n--- STDERR ---\n" + p.stderr)
    if p.returncode != 0:
        raise RuntimeError(f"FullScene-1c Blender fixation {step} failed; see render log")
    rr = json.loads((out / "run.json").read_text())
    case = out / f"fix_{step:02d}"
    if not rr.get("complete") or int(rr.get("seed", -1)) != public.SEED or int(rr.get("step", -1)) != step:
        raise RuntimeError("incomplete or wrong FullScene-1c Blender record")
    if abs(float(rr["yaw_deg"]) - yaw) > 1e-8 or abs(float(rr["pitch_deg"]) - pitch) > 1e-8:
        raise RuntimeError("Blender record gaze mismatch")
    return case


def _load_scene_maps(parent: Path, pm: dict, objs: dict[int, dict], existing_ids: tuple[int, ...], target_id: int):
    maps = {}
    paths = {}
    hashes = {}
    for oid in existing_ids:
        src = _resolve(objs[oid]["source"], parent)
        if not src.is_file():
            raise FileNotFoundError(src)
        sm = load_map(src)
        if len(sm.instance_id) and set(np.unique(sm.instance_id).tolist()) != {oid}:
            raise AssertionError(f"pre-existing object {oid} source is not pure")
        maps[oid] = sm
        paths[oid] = src
        hashes[oid] = _sha256(src)
    seed_path = _resolve(pm["seed_patch"], parent)
    graph_seed_path = _resolve(objs[target_id]["source"], parent)
    if seed_path != graph_seed_path:
        raise AssertionError("FullScene-1b manifest/scene-graph seed paths disagree")
    if not seed_path.is_file():
        raise FileNotFoundError(seed_path)
    return maps, paths, hashes, seed_path


def _write_scene_graph(path: Path, seed_patch_path: Path, target_id: int, existing_ids: tuple[int, ...],
                       existing_maps: dict[int, object], existing_paths: dict[int, Path],
                       existing_hashes: dict[int, str], target_path: Path, target_points: int,
                       target_fixations: int, termination: str, chart: dict,
                       footprint_counts: dict[str, int]) -> None:
    objects = []
    for oid in existing_ids:
        objects.append({
            "object_id": int(oid),
            "geometry": "SURFEL_MAP",
            "source": str(existing_paths[oid]),
            "source_sha256": existing_hashes[oid],
            "point_count": int(len(existing_maps[oid].xyz_h)),
            "read_only": True,
        })
    objects.append({
        "object_id": int(target_id),
        "geometry": "SURFEL_MAP",
        "source": str(target_path),
        "point_count": int(target_points),
        "read_only": False,
        "growth_parent": str(seed_patch_path),
        "active_fixations": int(target_fixations),
        "termination_reason": str(termination),
    })
    json_write(path, {
        "schema": "FullScene1c-scene-graph-v1",
        "fixed_head": True,
        "static_scene": True,
        "objects": objects,
        "cyclopean_chart": chart,
        "raw_footprint_cells": footprint_counts,
    })


def execute(args) -> dict:
    args.repo = Path(args.repo).resolve()
    args.parent = Path(args.parent).resolve()
    args.out = Path(args.out).resolve()
    if args.out.exists():
        raise FileExistsError("output must be new")
    args.out.mkdir(parents=True)
    for d in ("logs", "acquisitions", "patches", "maps", "rgb"):
        (args.out / d).mkdir()

    check_kernel_equivalence()
    if public.FUSION != dict(frozen_public.FUSION):
        raise AssertionError("FullScene-1c changed the frozen 12 mm FSG6f fusion rule")

    pm, _parent_scene, target_id, existing_ids, objs = _validate_parent(args.parent)
    profile = str(pm.get("profile", "full"))
    seed_step, seed_case = _seed_case(args.parent, pm)
    seed_patch_name = str(pm["seed_patch"])
    parent_files = [
        "prediction_manifest.json",
        "scene_graph.json",
        seed_patch_name,
        f"acquisition/fix_{seed_step:02d}/calibration.json",
        f"acquisition/fix_{seed_step:02d}/observation.npz",
    ]
    parent_hash_before = {n: _sha256(args.parent / n) for n in parent_files}
    existing_maps, existing_paths, existing_hash_before, seed_patch_path = _load_scene_maps(
        args.parent, pm, objs, existing_ids, target_id
    )

    c, obs = hdr.read_observation(seed_case)
    rec, _meta, state = compute_once(c, obs)
    ids_R, raw_R = _right_state(c, rec, state)
    p0 = _patch_from_record(f"fix_{seed_step:02d}", rec, target_id)
    if len(p0.instance_id) and set(np.unique(p0.instance_id).tolist()) != {target_id}:
        raise AssertionError("FullScene-1b seed acquisition is not pure for selected object")
    if int(len(p0.xyz_h)) != int(pm.get("selected_object_seed_points", -1)):
        raise AssertionError("FullScene-1b saved seed count no longer matches its acquisition")
    with np.load(seed_patch_path, allow_pickle=False) as z:
        if not np.array_equal(np.asarray(z["xyz_h"], np.float32), np.asarray(p0.xyz_h, np.float32)):
            raise AssertionError("saved FullScene-1b seed xyz no longer matches its acquisition")
        if not np.array_equal(np.asarray(z["instance_id"]), np.asarray(p0.instance_id)):
            raise AssertionError("saved FullScene-1b seed ids no longer match its acquisition")

    sm = initialize(p0, target_id)
    save_map(args.out / "maps" / f"map_{seed_step:02d}.npz", sm)
    gazes = [tuple(map(float, pm["probe_gaze_deg"]))]
    snapshots = [sm.xyz_h.copy()]
    supports = [sm.support_count.copy()]
    history = [policy.history_entry(
        c, rec["instance_id"], rec["raw_support_L"], ids_R, raw_R, target_id
    )]
    policy_trace = []
    patch_stats = [{
        "global_step": int(seed_step),
        "object_fixation_index": 0,
        "patch_id": f"fix_{seed_step:02d}",
        "yaw_deg": gazes[0][0],
        "pitch_deg": gazes[0][1],
        "point_count": int(len(p0.xyz_h)),
        "source": "FullScene-1b prescribed S0-selected seed",
        **_texture_stats(rec, target_id),
    }]
    association_stats = [{
        "global_step": int(seed_step),
        "object_fixation_index": 0,
        "input_points": int(len(p0.xyz_h)),
        "matched": 0,
        "new": int(len(p0.xyz_h)),
        "empty_look": False,
        "idempotent_replay": True,
    }]
    empty_steps: list[int] = []
    Image.fromarray(_tone_preview(rec["rgb_left"])).save(args.out / "rgb" / f"fix_{seed_step:02d}.png")

    decision = policy.choose_next(
        gazes[-1][0], gazes[-1][1], c,
        rec["instance_id"], rec["raw_support_L"], ids_R, raw_R,
        sm.xyz_h, gazes, history, target_id,
    )
    decision["object_fixation_index"] = 0
    decision["global_step"] = int(seed_step)
    policy_trace.append(decision)

    termination = None
    t0 = time.perf_counter()
    while True:
        if decision.get("stop"):
            termination = str(decision.get("reason", "policy_stop"))
            break
        if len(gazes) >= public.SELECTED_OBJECT_WATCHDOG_FIXATIONS:
            termination = "selected_object_watchdog"
            break
        gaze = tuple(map(float, decision["next_gaze_deg"]))
        if any(np.allclose(g, gaze, atol=1e-9) for g in gazes):
            raise AssertionError("selected-object policy revisited an existing fixation")
        global_step = int(seed_step + len(gazes))
        case = _run_scene_blender(args, global_step, gaze, profile)
        c, obs = hdr.read_observation(case)
        rec, _meta, state = compute_once(c, obs)
        ids_R, raw_R = _right_state(c, rec, state)
        pid = f"fix_{global_step:02d}"
        p = _patch_from_record(pid, rec, target_id)
        _save_patch(args.out / "patches" / f"{pid}.npz", p, rec, ids_R, raw_R)
        Image.fromarray(_tone_preview(rec["rgb_left"])).save(args.out / "rgb" / f"{pid}.png")

        empty = len(p.xyz_h) < public.MIN_TARGET_POINTS
        if empty:
            empty_steps.append(global_step)
            assoc = {
                "input_points": int(len(p.xyz_h)), "matched": 0, "new": 0,
                "affected_surfels": 0, "distances_m": np.empty(0), "duplicate_patch": False,
            }
            idempotent = True
        else:
            sm, assoc = fuse(
                sm, p, target_id,
                public.FUSION["association_radius_m"], public.FUSION["hash_cell_m"],
            )
            replay, dup = fuse(
                sm, p, target_id,
                public.FUSION["association_radius_m"], public.FUSION["hash_cell_m"],
            )
            idempotent = bool(
                dup["duplicate_patch"]
                and np.array_equal(sm.xyz_h, replay.xyz_h)
                and np.array_equal(sm.support_count, replay.support_count)
                and np.array_equal(sm.provenance_mask, replay.provenance_mask)
            )
            if not idempotent:
                raise AssertionError("selected-object patch replay is not idempotent")

        if len(sm.instance_id) and set(np.unique(sm.instance_id).tolist()) != {target_id}:
            raise AssertionError("cross-object contamination entered selected-object map")
        save_map(args.out / "maps" / f"map_{global_step:02d}.npz", sm)
        gazes.append(gaze)
        snapshots.append(sm.xyz_h.copy())
        supports.append(sm.support_count.copy())
        history.append(policy.history_entry(
            c, rec["instance_id"], rec["raw_support_L"], ids_R, raw_R, target_id
        ))
        dist = np.asarray(assoc.get("distances_m", np.empty(0)))
        association_stats.append({
            "global_step": global_step,
            "object_fixation_index": len(gazes) - 1,
            "input_points": int(len(p.xyz_h)),
            "matched": int(assoc.get("matched", 0)),
            "new": int(assoc.get("new", 0)),
            "empty_look": bool(empty),
            "overlap_median_distance_m": float(np.median(dist)) if len(dist) else None,
            "overlap_p95_distance_m": float(np.percentile(dist, 95)) if len(dist) else None,
            "idempotent_replay": bool(idempotent),
        })
        patch_stats.append({
            "global_step": global_step,
            "object_fixation_index": len(gazes) - 1,
            "patch_id": pid,
            "yaw_deg": gaze[0],
            "pitch_deg": gaze[1],
            "point_count": int(len(p.xyz_h)),
            "empty_look": bool(empty),
            **_texture_stats(rec, target_id),
        })
        decision = policy.choose_next(
            gaze[0], gaze[1], c,
            rec["instance_id"], rec["raw_support_L"], ids_R, raw_R,
            sm.xyz_h, gazes, history, target_id,
        )
        decision["object_fixation_index"] = len(gazes) - 1
        decision["global_step"] = global_step
        policy_trace.append(decision)

    if len(sm.instance_id) and set(np.unique(sm.instance_id).tolist()) != {target_id}:
        raise AssertionError("final selected-object map is not pure")

    target_path = args.out / f"object_{target_id}_surface_map.npz"
    save_map(target_path, sm)
    fsg6run.save_ply(args.out / f"object_{target_id}_surface_map.ply", sm)
    fsg6run.write_growth(args.out / f"object_{target_id}_growth.png", snapshots, supports, gazes)
    json_write(args.out / f"object_{target_id}_policy_trace.json", {
        "policy": "frozen_fsg6f_via_reused_multiobject2c_target_label_adapter",
        "target_object_id": int(target_id),
        "trace": policy_trace,
    })

    chart_objects = [(oid, existing_maps[oid].xyz_h) for oid in existing_ids]
    chart_objects.append((target_id, sm.xyz_h))
    chart, fps = _shared_chart(chart_objects, parent_public.GRID_DEG)
    np.savez_compressed(
        args.out / "scene_cyclopean_footprints.npz",
        **{f"object_{oid}": fp for oid, fp in fps.items()},
        **chart,
    )
    _write_scene_png(args.out / "scene_cyclopean_footprints.png", fps)
    footprint_counts = _overlap_counts(fps)
    _write_scene_graph(
        args.out / "scene_graph.json", seed_patch_path, target_id, existing_ids,
        existing_maps, existing_paths, existing_hash_before,
        target_path, len(sm.xyz_h), len(gazes), termination,
        chart, footprint_counts,
    )

    parent_hash_after = {n: _sha256(args.parent / n) for n in parent_hash_before}
    if parent_hash_after != parent_hash_before:
        raise AssertionError("FullScene-1b parent changed during growth")
    for oid in existing_ids:
        if _sha256(existing_paths[oid]) != existing_hash_before[oid]:
            raise AssertionError(f"pre-existing object {oid} geometry was modified")

    scientific_stop = bool(termination != "selected_object_watchdog" and policy_trace[-1].get("stop"))
    recovery_values = [
        float(r["target_depth_recovery_fraction"])
        for r in patch_stats if r.get("target_depth_recovery_fraction") is not None
    ]
    total_matched = int(sum(int(r.get("matched", 0)) for r in association_stats[1:]))
    total_new = int(sum(int(r.get("new", 0)) for r in association_stats[1:]))
    manifest = {
        "schema": public.SPEC_ID,
        "public_spec_sha256": public.public_digest(),
        "parent_spec": public.PARENT_SPEC_ID,
        "parent_record": str(args.parent),
        "parent_hashes": parent_hash_before,
        "seed": public.SEED,
        "profile": profile,
        "fixture": public.FIXTURE,
        "fixed_head": True,
        "static_scene": True,
        "truth_opened": False,
        "preexisting_object_ids": list(existing_ids),
        "selected_object_id": int(target_id),
        "object_ids": list(existing_ids + (target_id,)),
        "preexisting_objects_read_only": True,
        "preexisting_object_hashes_before": {str(k): v for k, v in existing_hash_before.items()},
        "preexisting_object_hashes_after": {str(k): _sha256(existing_paths[k]) for k in existing_paths},
        "deferred_prior_object_action_executed": False,
        "selected_object_seed_points": int(len(p0.xyz_h)),
        "selected_object_map_points": int(len(sm.xyz_h)),
        "selected_object_map_pure": True,
        "selected_object_fixation_gazes_deg": [list(map(float, g)) for g in gazes],
        "selected_object_fixations_total": int(len(gazes)),
        "added_fixations": int(len(gazes) - 1),
        "parent_fixations_rerendered": 0,
        "empty_steps": empty_steps,
        "termination_reason": termination,
        "scientific_stop_reached": scientific_stop,
        "watchdog_selected_object_fixations": public.SELECTED_OBJECT_WATCHDOG_FIXATIONS,
        "policy_adapter": "reuse_multiobject2c_policy_target_label_adapter",
        "policy_adapter_source": public.POLICY_ADAPTER,
        "policy_source_modified": False,
        "growth_history_starts_at_fullscene1b_seed": True,
        "older_scene_history_replayed_into_local_policy": False,
        "global_step_seed": int(seed_step),
        "first_new_global_step": int(seed_step + 1) if len(gazes) > 1 else None,
        "last_global_step": int(seed_step + len(gazes) - 1),
        "patch_stats": patch_stats,
        "association_stats": association_stats,
        "fusion_matched_total_after_seed": total_matched,
        "fusion_new_total_after_seed": total_new,
        "texture_diagnostics_are_gates": False,
        "productivity_score_synthesized": False,
        "target_depth_recovery_fraction_min": min(recovery_values) if recovery_values else None,
        "target_depth_recovery_fraction_median": float(np.median(recovery_values)) if recovery_values else None,
        "target_depth_recovery_fraction_max": max(recovery_values) if recovery_values else None,
        "scene_graph": "scene_graph.json",
        "scene_footprints": "scene_cyclopean_footprints.npz",
        "scene_footprint_counts": footprint_counts,
        "renderer_entrypoint": public.SCENE_RENDERER,
        "fusion_rule": public.FUSION,
        "epistemic_handoffs_added": 0,
        "automatic_object_discovery": False,
        "automatic_scene_scheduler": False,
        "revisit_scheduler_used": False,
        "semantic_ranking_used": False,
        "quality_gate_used": False,
        "new_threshold_added": False,
        "next_stage": public.NEXT_STAGE,
        "loop_wall_seconds": float(time.perf_counter() - t0),
        "structural_fails": [],
    }
    json_write(args.out / "prediction_manifest.json", manifest)
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--parent", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", choices=("OPTIX", "CUDA", "CPU"), default="OPTIX")
    ap.add_argument("--blender", default="blender")
    m = execute(ap.parse_args())
    print("[fullscene1c-run] FULLSCENE1C_COMPLETE " + json.dumps({
        "selected_object_id": m["selected_object_id"],
        "selected_object_seed_points": m["selected_object_seed_points"],
        "selected_object_map_points": m["selected_object_map_points"],
        "selected_object_fixations_total": m["selected_object_fixations_total"],
        "added_fixations": m["added_fixations"],
        "empty_steps": m["empty_steps"],
        "termination_reason": m["termination_reason"],
        "scientific_stop_reached": m["scientific_stop_reached"],
        "fusion_new_total_after_seed": m["fusion_new_total_after_seed"],
        "structural_fails": m["structural_fails"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
