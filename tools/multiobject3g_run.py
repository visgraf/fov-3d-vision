"""Execute exactly one local action returned by the MultiObject-3e/3f handoff."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

import fsg6_run as fsg6run
import fsg_stereo_hdr as hdr
from fsg3_surface_map import Patch, fuse, load_map, save_map
from fsg_geometry import json_write
from fsg_stereo import rectification, support_mask
from fsg_stereo_supported import check_kernel_equivalence, compute_once
from reality1_run import _tone_preview
from multiobject3b_run import _shared_chart, _write_scene_png, _overlap_counts

import multiobject2c_policy as policy
import multiobject3d_audit as audit3d
import multiobject3f_audit as audit3f
import multiobject3f_public as parent_public
import multiobject3e_public as state_public
import multiobject3g_progress as progress
import multiobject3g_public as public


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _resolve(path_like: str, base: Path) -> Path:
    p = Path(path_like)
    return p.resolve() if p.is_absolute() else (base / p).resolve()


def _same_optional_gaze(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return bool(np.allclose(np.asarray(a, float), np.asarray(b, float), atol=1e-9, rtol=0.0))


def _validate_parent(parent3f: Path):
    m3f = json.loads((parent3f / "prediction_manifest.json").read_text())
    if m3f.get("schema") != public.PARENT_SPEC_ID:
        raise AssertionError("MultiObject-3g requires a completed MultiObject-3f parent")
    if m3f.get("public_spec_sha256") != parent_public.public_digest():
        raise AssertionError("MultiObject-3f public digest mismatch")
    if int(m3f.get("seed", -1)) != public.SEED or m3f.get("truth_opened") is not False:
        raise AssertionError("wrong seed or truth integrity broken")
    if m3f.get("reactivation_status") != public.PUBLIC_SPEC["required_parent_reactivation_status"]:
        raise AssertionError("MultiObject-3f did not reproduce local-policy reactivation")
    if int(m3f.get("acquisitions_added", -1)) != 0 or int(m3f.get("fusion_iterations_added", -1)) != 0:
        raise AssertionError("MultiObject-3f parent was not read-only")
    if m3f.get("returned_local_action_executed") is not False:
        raise AssertionError("MultiObject-3f unexpectedly executed the returned action")
    if m3f.get("structural_fails") not in ([], None):
        raise AssertionError("MultiObject-3f parent has structural failures")

    gaze = m3f.get("returned_next_gaze_deg")
    if gaze is None or len(gaze) != 2:
        raise AssertionError("MultiObject-3f returned gaze missing")
    gaze = tuple(map(float, gaze))

    # Require the causal decomposition established by 3f, without turning its
    # measured magnitudes into a new threshold or score.
    cf = m3f.get("counterfactual_policy_summary", {})
    att = cf.get("ATTENTION_ONLY_PRE_FUSION_MAP", {})
    geo = cf.get("GEOMETRY_ONLY_OLD_ATTENTION_CONTEXT", {})
    if att.get("stop") is not False or not _same_optional_gaze(att.get("next_gaze_deg"), gaze):
        raise AssertionError("MultiObject-3f attention-only counterfactual does not reproduce the returned gaze")
    if geo.get("stop") is not True or geo.get("reason") != "no_frontier":
        raise AssertionError("MultiObject-3f geometry-only counterfactual does not reproduce the old stop")

    parent3e = _resolve(m3f["parent_record"], parent3f)
    m3e, parent3c, pm3c, target_id, objects = audit3f._validate_parent(parent3e)
    if m3e.get("schema") != public.EXECUTION_PARENT_SPEC_ID:
        raise AssertionError("MultiObject-3g execution state is not MultiObject-3e")
    if m3e.get("public_spec_sha256") != state_public.public_digest():
        raise AssertionError("MultiObject-3e public digest mismatch")
    if m3e.get("return_status") != "LOCAL_POLICY_REACTIVATED":
        raise AssertionError("MultiObject-3e did not return a live local action")
    if m3e.get("returned_local_action_executed") is not False:
        raise AssertionError("MultiObject-3e returned action was already executed")
    saved = m3e.get("returned_local_policy_decision", {})
    if saved.get("stop") is not False or not _same_optional_gaze(saved.get("next_gaze_deg"), gaze):
        raise AssertionError("MultiObject-3e returned decision disagrees with MultiObject-3f")
    if int(m3f.get("selected_object_id", -1)) != int(target_id):
        raise AssertionError("MultiObject-3f selected object disagrees with execution state")
    return m3f, parent3e, m3e, parent3c, pm3c, int(target_id), objects, gaze


def _right_state(c: dict, rec: dict, state: dict) -> tuple[np.ndarray, np.ndarray]:
    x, y, cw, ch = map(int, rec["crop_xywh"])
    sl = np.s_[y:y+ch, x:x+cw]
    ids_R = np.asarray(state["ids_right"])[sl]
    raw_R = np.asarray(support_mask(c, rec, "R"), bool)[sl]
    if not np.array_equal(np.asarray(rec["instance_id"]), np.asarray(state["ids_left"])[sl]):
        raise AssertionError("left rectified ID replay mismatch")
    return ids_R.copy(), raw_R.copy()


def _new_observation(step: int, case: Path, c: dict, rec: dict, ids_R: np.ndarray, raw_R: np.ndarray) -> dict:
    return {
        "step": int(step),
        "label": f"fix_{step:02d}",
        "case": str(case),
        "calibration": c,
        "rectification": rectification(c),
        "instance_id": np.asarray(rec["instance_id"]).copy(),
        "instance_R": np.asarray(ids_R).copy(),
        "valid": np.asarray(rec["valid"], bool).copy(),
        "raw_support_L": np.asarray(rec["raw_support_L"], bool).copy(),
        "raw_support_R": np.asarray(raw_R, bool).copy(),
        "xyz_h": np.asarray(rec["xyz_h"]).copy(),
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
        raise RuntimeError("MultiObject-3g returned-action render failed; see render.log")
    case = out / f"fix_{step:02d}"
    if not (case / "calibration.json").is_file() or not (case / "observation.npz").is_file():
        raise RuntimeError("MultiObject-3g acquisition is incomplete")
    return case


def _load_scene_sources(parent3e: Path, m3e: dict, target_id: int):
    graph = json.loads((parent3e / m3e["scene_graph"]).read_text())
    rows = graph.get("objects", [])
    objects = {int(r["object_id"]): r for r in rows}
    if target_id not in objects:
        raise AssertionError("active object missing from MultiObject-3e scene graph")
    sources: dict[int, Path] = {}
    maps: dict[int, object] = {}
    hashes: dict[int, str] = {}
    for oid, row in objects.items():
        src = _resolve(row["source"], parent3e)
        sm = load_map(src)
        if len(sm.instance_id) and set(np.unique(sm.instance_id).tolist()) != {oid}:
            raise AssertionError(f"scene object {oid} source lost id purity")
        sources[oid] = src
        maps[oid] = sm
        hashes[oid] = _sha256(src)
    return objects, sources, maps, hashes


def _write_scene_graph(path: Path, parent3e: Path, target_id: int, objects: dict[int, dict],
                       object_sources: dict[int, Path], object_maps: dict[int, object],
                       target_path: Path, target_points: int, global_step: int, target_fixations: int,
                       chart: dict, footprint_counts: dict[str, int], measurement_status: str,
                       next_policy_status: str) -> None:
    rows = []
    for oid in sorted(objects):
        if oid == target_id:
            rows.append({
                "object_id": int(oid),
                "geometry": "SURFEL_MAP",
                "source": str(target_path),
                "point_count": int(target_points),
                "read_only": False,
                "resume_parent": str(parent3e / f"object_{target_id}_surface_map.npz"),
                "executed_returned_action_global_step": int(global_step),
                "measurement_status": measurement_status,
                "subsequent_policy_status": next_policy_status,
                "active_fixations": int(target_fixations),
            })
        else:
            rows.append({
                "object_id": int(oid),
                "geometry": str(objects[oid].get("geometry", "SURFEL_MAP")),
                "source": str(object_sources[oid]),
                "source_sha256": _sha256(object_sources[oid]),
                "point_count": int(len(object_maps[oid].xyz_h)),
                "read_only": True,
            })
    json_write(path, {
        "schema": "MultiObject3g-scene-graph-v1",
        "fixed_head": True,
        "static_scene": True,
        "objects": rows,
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
    check_kernel_equivalence()

    m3f, parent3e, m3e, parent3c, pm3c, target_id, _old_objects, action_gaze = _validate_parent(args.parent)
    profile = str(m3e.get("profile", pm3c.get("profile", "full")))

    # Pin the read-only causal audit, execution state, selected-object history,
    # and all persistent scene-object sources before taking the one action.
    parent3f_names = ("prediction_manifest.json", m3f["report"], m3f["frontier_npz"], m3f["frontier_details"])
    parent3f_hashes = {n: _sha256(args.parent / n) for n in parent3f_names}
    parent3e_names = (
        "prediction_manifest.json", m3e["handoff_report"], m3e["active_object_map"],
        f"object_{target_id}_policy_trace.json", m3e["scene_graph"],
    )
    parent3e_hashes = {n: _sha256(parent3e / n) for n in parent3e_names}

    objects, object_sources, object_maps, object_hashes_before = _load_scene_sources(parent3e, m3e, target_id)
    sm = object_maps[target_id]
    if set(np.unique(sm.instance_id).tolist()) != {target_id}:
        raise AssertionError("active-object map lost id purity before returned action")

    pre_cases = audit3d._all_cases(parent3c, pm3c)
    pre_case_hashes = audit3d._case_hashes(pre_cases)
    observations = [audit3d._saved_observation(step, case) for step, case in pre_cases]
    handoff_step = int(m3e["global_step"])
    handoff_case = parent3e / "acquisition" / f"fix_{handoff_step:02d}"
    if not (handoff_case / "calibration.json").is_file() or not (handoff_case / "observation.npz").is_file():
        raise FileNotFoundError("MultiObject-3e handoff acquisition missing")
    handoff_hashes_before = {
        "calibration.json": _sha256(handoff_case / "calibration.json"),
        "observation.npz": _sha256(handoff_case / "observation.npz"),
    }
    handoff_ob = audit3d._saved_observation(handoff_step, handoff_case)
    observations.append(handoff_ob)

    gazes = [tuple(map(float, g)) for g in m3e.get("selected_object_fixation_gazes_deg", [])]
    if len(gazes) != len(observations):
        raise AssertionError("MultiObject-3e gaze/history length mismatch")
    if not _same_optional_gaze(gazes[-1], m3e.get("handoff_gaze_deg")):
        raise AssertionError("MultiObject-3e final gaze is not the handoff gaze")

    history = audit3d._policy_history(observations[:-1], target_id)
    history.append(policy.history_entry(
        handoff_ob["calibration"], handoff_ob["instance_id"], handoff_ob["raw_support_L"],
        handoff_ob["instance_R"], handoff_ob["raw_support_R"], target_id,
    ))

    # Reproduce the unexecuted decision exactly before acting on it.
    current = handoff_ob
    pre_action_replay = policy.choose_next(
        gazes[-1][0], gazes[-1][1], current["calibration"],
        current["instance_id"], current["raw_support_L"], current["instance_R"], current["raw_support_R"],
        sm.xyz_h, gazes, history, target_id,
    )
    audit3f._exact_decision_replay(m3e["returned_local_policy_decision"], pre_action_replay, "pre-action")
    if not _same_optional_gaze(pre_action_replay.get("next_gaze_deg"), action_gaze):
        raise AssertionError("exact replay does not return the MultiObject-3f action gaze")

    global_step = int(m3e.get("last_global_step", handoff_step)) + 1
    case = _run_scene_blender(args, profile, global_step, action_gaze)
    c, obs = hdr.read_observation(case)
    rec, _meta, state = compute_once(c, obs)
    ids_R, raw_R = _right_state(c, rec, state)
    target_mask = np.asarray(rec["valid"], bool) & (np.asarray(rec["instance_id"]) == target_id)
    patch = Patch(
        f"returned_local_action_{global_step:02d}",
        np.asarray(rec["xyz_h"])[target_mask],
        np.asarray(rec["rgb_left"])[target_mask],
        np.asarray(rec["instance_id"])[target_mask],
    )
    np.savez_compressed(
        args.out / "returned_action_patch.npz",
        xyz_h=np.asarray(patch.xyz_h, np.float32),
        rgb=np.asarray(patch.rgb, np.float32),
        instance_id=np.asarray(patch.instance_id),
        valid=np.asarray(rec["valid"], bool),
        oracle_instance_id=np.asarray(rec["instance_id"]),
        raw_support_L=np.asarray(rec["raw_support_L"], bool),
        oracle_instance_id_R=np.asarray(ids_R),
        raw_support_R=np.asarray(raw_R, bool),
    )
    Image.fromarray(_tone_preview(rec["rgb_left"])).save(args.out / "returned_action_rgb.png")

    empty = len(patch.xyz_h) < public.MIN_TARGET_POINTS
    sm_after = sm
    assoc = {"input_points": int(len(patch.xyz_h)), "matched": 0, "new": 0, "duplicate_patch": False}
    idempotent = True
    if not empty:
        sm_after, assoc = fuse(
            sm, patch, target_id,
            public.FUSION["association_radius_m"], public.FUSION["hash_cell_m"],
        )
        replay, dup = fuse(
            sm_after, patch, target_id,
            public.FUSION["association_radius_m"], public.FUSION["hash_cell_m"],
        )
        idempotent = bool(
            dup["duplicate_patch"]
            and np.array_equal(sm_after.xyz_h, replay.xyz_h)
            and np.array_equal(sm_after.support_count, replay.support_count)
            and np.array_equal(sm_after.provenance_mask, replay.provenance_mask)
        )
        if not idempotent:
            raise AssertionError("returned-action patch replay is not idempotent")
    if len(sm_after.instance_id) and set(np.unique(sm_after.instance_id).tolist()) != {target_id}:
        raise AssertionError("returned local action contaminated the active-object map")

    target_map_name = f"object_{target_id}_surface_map.npz"
    target_map_path = args.out / target_map_name
    save_map(target_map_path, sm_after)
    fsg6run.save_ply(args.out / f"object_{target_id}_surface_map.ply", sm_after)

    new_ob = _new_observation(global_step, case, c, rec, ids_R, raw_R)
    gazes_after = gazes + [action_gaze]
    history_after = history + [policy.history_entry(c, rec["instance_id"], rec["raw_support_L"], ids_R, raw_R, target_id)]
    subsequent = policy.choose_next(
        action_gaze[0], action_gaze[1], c,
        rec["instance_id"], rec["raw_support_L"], ids_R, raw_R,
        sm_after.xyz_h, gazes_after, history_after, target_id,
    )
    measurement_status = progress.measurement_status(empty, int(assoc.get("new", 0)), int(assoc.get("matched", 0)))
    next_policy_status = progress.subsequent_policy_status(subsequent)

    subsequent_record = dict(subsequent)
    subsequent_record["object_fixation_index"] = int(len(gazes_after) - 1)
    subsequent_record["global_step"] = int(global_step)
    parent_trace = json.loads((parent3e / f"object_{target_id}_policy_trace.json").read_text())
    trace = list(parent_trace.get("trace", [])) + [subsequent_record]
    json_write(args.out / f"object_{target_id}_policy_trace.json", {
        "policy": "frozen_fsg6f_via_reused_multiobject2c_target_label_adapter",
        "target_object_id": int(target_id),
        "trace": trace,
        "executed_parent_returned_action": True,
        "executed_action_gaze_deg": [float(action_gaze[0]), float(action_gaze[1])],
        "executed_action_global_step": int(global_step),
        "last_action_executed": False,
        "bounded_resume": True,
    })

    scene_objects = []
    for oid in sorted(objects):
        xyz = sm_after.xyz_h if oid == target_id else object_maps[oid].xyz_h
        scene_objects.append((oid, xyz))
    scene_chart, fps = _shared_chart(scene_objects, public.GRID_DEG)
    np.savez_compressed(
        args.out / "scene_cyclopean_footprints.npz",
        **{f"object_{oid}": fp for oid, fp in fps.items()},
        **scene_chart,
    )
    _write_scene_png(args.out / "scene_cyclopean_footprints.png", fps)
    footprint_counts = _overlap_counts(fps)
    _write_scene_graph(
        args.out / "scene_graph.json", parent3e, target_id, objects,
        object_sources, object_maps, target_map_path, len(sm_after.xyz_h),
        global_step, len(gazes_after), scene_chart, footprint_counts,
        measurement_status, next_policy_status,
    )

    visible_target = int(np.count_nonzero(np.asarray(rec["instance_id"]) == target_id))
    valid_target = int(np.count_nonzero(target_mask))
    recovery = float(valid_target / visible_target) if visible_target else None
    action_report = {
        "selected_object_id": int(target_id),
        "action_source": "MultiObject-3f returned_next_gaze_deg, cross-checked to exact MultiObject-3e replay",
        "executed_gaze_deg": [float(action_gaze[0]), float(action_gaze[1])],
        "global_step": int(global_step),
        "pre_action_policy_replayed_exactly": True,
        "pre_action_policy_decision": pre_action_replay,
        "target_visible_pixels": visible_target,
        "target_valid_depth_points": valid_target,
        "target_depth_recovery_fraction": recovery,
        "empty_look": bool(empty),
        "fused": bool(not empty),
        "new_surfels": int(assoc.get("new", 0)),
        "matched_surfels": int(assoc.get("matched", 0)),
        "idempotent_replay": bool(idempotent),
        "map_points_before": int(len(sm.xyz_h)),
        "map_points_after": int(len(sm_after.xyz_h)),
        "measurement_status": measurement_status,
        "subsequent_local_policy_decision": subsequent_record,
        "subsequent_policy_status": next_policy_status,
        "subsequent_local_action_executed": False,
        "experiment_stop": progress.experiment_stop(),
    }
    json_write(args.out / "returned_action_report.json", action_report)

    # Verify the entire inherited state remained immutable.
    if {n: _sha256(args.parent / n) for n in parent3f_names} != parent3f_hashes:
        raise AssertionError("MultiObject-3f parent changed during returned-action execution")
    if {n: _sha256(parent3e / n) for n in parent3e_names} != parent3e_hashes:
        raise AssertionError("MultiObject-3e execution parent changed during returned-action execution")
    if audit3d._case_hashes(pre_cases) != pre_case_hashes:
        raise AssertionError("selected-object pre-handoff history changed")
    if {
        "calibration.json": _sha256(handoff_case / "calibration.json"),
        "observation.npz": _sha256(handoff_case / "observation.npz"),
    } != handoff_hashes_before:
        raise AssertionError("epistemic handoff acquisition changed")
    for oid, src in object_sources.items():
        if _sha256(src) != object_hashes_before[oid]:
            raise AssertionError(f"scene object {oid} source changed during returned-action execution")

    manifest = {
        "schema": public.SPEC_ID,
        "public_spec_sha256": public.public_digest(),
        "parent_spec": public.PARENT_SPEC_ID,
        "parent_record": str(args.parent),
        "execution_parent_spec": public.EXECUTION_PARENT_SPEC_ID,
        "execution_parent_record": str(parent3e),
        "scene_parent_record": str(parent3c),
        "seed": public.SEED,
        "profile": profile,
        "fixture": public.FIXTURE,
        "fixed_head": True,
        "static_scene": True,
        "truth_opened": False,
        "selected_object_id": int(target_id),
        "preexisting_object_ids": [int(x) for x in m3e.get("preexisting_object_ids", [])],
        "parent_reactivation_status": m3f.get("reactivation_status"),
        "parent_attention_only_reproduced_action": True,
        "parent_geometry_only_reproduced_stop": True,
        "pre_action_policy_replayed_exactly": True,
        "executed_returned_local_action": True,
        "executed_action_gaze_deg": [float(action_gaze[0]), float(action_gaze[1])],
        "executed_action_source_global_step": int(m3e.get("global_step", -1)),
        "global_step": int(global_step),
        "added_fixations": 1,
        "parent_fixations_rerendered": 0,
        "fusion_iterations_added": int(0 if empty else 1),
        "growth_loop_iterations_added": 0,
        "subsequent_local_policy_decisions": 1,
        "subsequent_local_action_executed": False,
        "automatic_handoff_loop": False,
        "automatic_local_loop": False,
        "automatic_scene_scheduler": False,
        "revisit_scheduler_used": False,
        "watchdog_changed": False,
        "quality_gate_used": False,
        "new_threshold_added": False,
        "renderer_entrypoint": public.SCENE_RENDERER,
        "policy_adapter_source": public.POLICY_ADAPTER,
        "policy_source_modified": False,
        "fusion_rule": public.FUSION,
        "empty_look_min_target_points": public.MIN_TARGET_POINTS,
        "empty_look": bool(empty),
        "selected_object_visible_pixels": visible_target,
        "selected_object_valid_depth_points": valid_target,
        "selected_object_depth_recovery_fraction": recovery,
        "selected_object_map_points_before": int(len(sm.xyz_h)),
        "selected_object_map_points_after": int(len(sm_after.xyz_h)),
        "selected_object_map_pure": True,
        "preexisting_objects_read_only": True,
        "measurement_status": measurement_status,
        "subsequent_local_policy_decision": subsequent_record,
        "subsequent_policy_status": next_policy_status,
        "selected_object_fixation_gazes_deg": [list(map(float, g)) for g in gazes_after],
        "selected_object_fixations_total": int(len(gazes_after)),
        "last_global_step": int(global_step),
        "returned_action_report": "returned_action_report.json",
        "active_object_map": target_map_name,
        "scene_graph": "scene_graph.json",
        "scene_footprints": "scene_cyclopean_footprints.npz",
        "scene_footprint_counts": footprint_counts,
        "parent3f_hashes": parent3f_hashes,
        "parent3e_hashes": parent3e_hashes,
        "scene_object_sha256_before": {str(k): v for k, v in object_hashes_before.items()},
        "scene_object_sha256_after": {str(k): _sha256(v) for k, v in object_sources.items()},
        "pre_handoff_observation_input_hashes": pre_case_hashes,
        "handoff_observation_input_hashes": handoff_hashes_before,
        "experiment_stop": progress.experiment_stop(),
        "next_stage": public.PUBLIC_SPEC["next_stage"],
        "structural_fails": [],
    }
    json_write(args.out / "prediction_manifest.json", manifest)
    print("[multiobject3g-run] MULTIOBJECT3G_COMPLETE " + json.dumps({
        "selected_object_id": int(target_id),
        "executed_gaze_deg": manifest["executed_action_gaze_deg"],
        "empty_look": bool(empty),
        "valid_target_points": valid_target,
        "map_points_before": int(len(sm.xyz_h)),
        "map_points_after": int(len(sm_after.xyz_h)),
        "measurement_status": measurement_status,
        "subsequent_policy_status": next_policy_status,
        "subsequent_next_gaze_deg": subsequent.get("next_gaze_deg"),
        "structural_fails": [],
    }, sort_keys=True), flush=True)
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--parent", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", choices=("OPTIX", "CUDA", "CPU"), default="OPTIX")
    ap.add_argument("--blender", default="blender")
    execute(ap.parse_args())


if __name__ == "__main__":
    main()
