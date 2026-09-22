"""Execute exactly one cyclopean-to-local epistemic handoff after MultiObject-3d."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

import cyclopean1a_topology as topo1a
import cyclopean1b_boundary as boundary
import cyclopean1d_epistemic as epi
import cyclopean1e_gaze as epistemic_gaze
import fsg6_run as fsg6run
import fsg_stereo_hdr as hdr
from fsg3_surface_map import Patch, fuse, load_map, save_map
from fsg_geometry import json_write
from fsg_stereo import rectification, support_mask
from fsg_stereo_supported import check_kernel_equivalence, compute_once
from reality1_run import _tone_preview
from multiobject3b_run import _shared_chart, _write_scene_png, _overlap_counts

import multiobject2c_policy as policy
import multiobject3d_audit as parent_audit
import multiobject3d_public as parent_public
import multiobject3e_progress as progress
import multiobject3e_public as public


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _resolve(path_like: str, base: Path) -> Path:
    p = Path(path_like)
    return p.resolve() if p.is_absolute() else (base / p).resolve()


def _validate_parent(parent: Path) -> tuple[dict, dict, Path, int, dict[int, dict]]:
    m3d = json.loads((parent / "prediction_manifest.json").read_text())
    if m3d.get("schema") != public.PARENT_SPEC_ID:
        raise AssertionError("MultiObject-3e requires a completed MultiObject-3d parent")
    if m3d.get("public_spec_sha256") != parent_public.public_digest():
        raise AssertionError("MultiObject-3d public digest mismatch")
    if m3d.get("truth_opened") is not False or int(m3d.get("acquisitions_added", -1)) != 0:
        raise AssertionError("MultiObject-3d parent was not the declared read-only audit")
    if m3d.get("final_policy_stop_replayed_exactly") is not True:
        raise AssertionError("MultiObject-3d did not establish an exact frozen-policy stop replay")
    summary = m3d.get("summary", {})
    if summary.get("stop_interpretation") != public.PUBLIC_SPEC["required_parent_interpretation"]:
        raise AssertionError("MultiObject-3e requires POLICY_EXHAUSTED_WITH_UNSEEN_TERRITORY")
    if int(summary.get("exterior_refined_cells_by_state", {}).get("NEVER_OBSERVED", 0)) <= 0:
        raise AssertionError("parent has no exterior NEVER_OBSERVED territory to hand off")
    target_id = int(m3d.get("selected_object_id", -1))
    if target_id <= 0:
        raise AssertionError("parent selected-object id missing")
    parent3c = _resolve(m3d["parent_record"], parent)
    pm3c, target3c, objects = parent_audit._validate_parent(parent3c)
    if int(target3c) != target_id:
        raise AssertionError("MultiObject-3d active object disagrees with its MultiObject-3c parent")
    if pm3c.get("termination_reason") != "no_frontier" or pm3c.get("scientific_stop_reached") is not True:
        raise AssertionError("underlying local policy is not at the declared no_frontier stop")
    report_name = m3d.get("report")
    if not report_name or not (parent / report_name).is_file():
        raise FileNotFoundError("MultiObject-3d epistemic report missing")
    report3d = json.loads((parent / report_name).read_text())
    if int(report3d.get("object_id", -1)) != target_id:
        raise AssertionError("MultiObject-3d report object id mismatch")
    return m3d, pm3c, parent3c, target_id, objects


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
        raise RuntimeError("MultiObject-3e epistemic handoff render failed; see render.log")
    case = out / f"fix_{step:02d}"
    if not (case / "calibration.json").is_file() or not (case / "observation.npz").is_file():
        raise RuntimeError("MultiObject-3e handoff acquisition is incomplete")
    return case


def _rebuild_epistemic(parent3c: Path, pm3c: dict, target_id: int):
    sm = load_map(parent3c / f"object_{target_id}_surface_map.npz")
    if set(np.unique(sm.instance_id).tolist()) != {target_id}:
        raise AssertionError("selected-object map lost id purity")
    profile = str(pm3c.get("profile", "full"))
    chart, footprint_cells, footprint_deg = topo1a.build_chart(sm.xyz_h, profile)
    if abs(float(chart.grid_deg) - public.GRID_DEG) > 1e-12:
        raise AssertionError("cyclopean grid changed from established scale")
    raw, support, target_range = topo1a.rasterize_target(sm.xyz_h, chart, footprint_cells)
    evidence = topo1a.empty_evidence(chart)
    observations = []
    cases = parent_audit._all_cases(parent3c, pm3c)
    for step, case in cases:
        ob = parent_audit._saved_observation(step, case)
        observations.append(ob)
        topo1a.add_observation(evidence, chart, ob["xyz_h"], ob["instance_id"], ob["valid"], target_id)
    ev = boundary.EvidenceArrays(
        evidence.seen_target, evidence.seen_nontarget,
        evidence.target_range_m, evidence.nontarget_range_m,
    )
    audit = boundary.analyze_boundary(
        raw_support=raw, support=support, target_range_m=target_range, evidence=ev,
        grid_deg=chart.grid_deg, yaw0_deg=chart.yaw0_deg, pitch0_deg=chart.pitch0_deg,
        footprint_cells=footprint_cells,
        association_radius_m=float(public.FUSION["association_radius_m"]),
    )
    refined, cell_ev = parent_audit._refine_unobserved(chart, audit, observations, target_id)
    return sm, profile, chart, footprint_cells, footprint_deg, raw, support, audit, refined, cell_ev, cases, observations


def _rebuild_after_same_chart(sm, chart, footprint_cells: int, observations: list[dict], target_id: int):
    raw, support, target_range = topo1a.rasterize_target(sm.xyz_h, chart, footprint_cells)
    evidence = topo1a.empty_evidence(chart)
    for ob in observations:
        topo1a.add_observation(evidence, chart, ob["xyz_h"], ob["instance_id"], ob["valid"], target_id)
    ev = boundary.EvidenceArrays(
        evidence.seen_target, evidence.seen_nontarget,
        evidence.target_range_m, evidence.nontarget_range_m,
    )
    audit = boundary.analyze_boundary(
        raw_support=raw, support=support, target_range_m=target_range, evidence=ev,
        grid_deg=chart.grid_deg, yaw0_deg=chart.yaw0_deg, pitch0_deg=chart.pitch0_deg,
        footprint_cells=footprint_cells,
        association_radius_m=float(public.FUSION["association_radius_m"]),
    )
    refined, cell_ev = parent_audit._refine_unobserved(chart, audit, observations, target_id)
    return raw, support, audit, refined, cell_ev


def _state_counts(refined: np.ndarray, audit) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    all_counts = {name: int((refined == code).sum()) for name, code in epi.STATE_CODE.items()}
    exterior = {name: 0 for name in epi.STATE_CODE}
    internal = {name: 0 for name in epi.STATE_CODE}
    # Split directly by component labels to avoid introducing a new state rule.
    kind_by_id = {int(c["component_id"]): str(c["kind"]) for c in audit.components}
    for y, x in zip(*np.nonzero(audit.shoreline & (audit.state_code == boundary.STATE_CODE["UNOBSERVED"]))):
        name = epi.CODE_STATE[int(refined[y, x])]
        kind = kind_by_id.get(int(audit.component_labels[y, x]))
        if kind == "EXTERIOR":
            exterior[name] += 1
        elif kind == "INTERNAL":
            internal[name] += 1
    return all_counts, exterior, internal


def _selected_cell_class(chart, gaze: tuple[float, float], support: np.ndarray, audit, refined: np.ndarray) -> dict:
    d = topo1a.angles_to_dir(float(gaze[0]), float(gaze[1]))[None, :]
    yaw, pitch, _rho = topo1a.xyz_to_angles(d)
    yy, xx, inside = topo1a._indices(chart, yaw, pitch)
    if not bool(inside[0]):
        return {"chart_inside": False, "cell_state": "OUT_OF_CHART", "chart_y": None, "chart_x": None}
    y = int(yy[0]); x = int(xx[0])
    label, kind = parent_audit._cell_epistemic_label(y, x, support, audit, refined)
    return {"chart_inside": True, "cell_state": label, "component_kind": kind, "chart_y": y, "chart_x": x}


def _write_scene_graph(path: Path, parent3c: Path, target_id: int, objects: dict[int, dict],
                       object_sources: dict[int, Path], object_maps: dict[int, object],
                       target_path: Path, target_points: int, global_step: int, target_fixations: int,
                       chart: dict, footprint_counts: dict[str, int], return_status: str) -> None:
    rows = []
    for oid in sorted(objects):
        if oid == target_id:
            rows.append({
                "object_id": int(oid),
                "geometry": "SURFEL_MAP",
                "source": str(target_path),
                "point_count": int(target_points),
                "read_only": False,
                "handoff_parent": str(parent3c / f"object_{target_id}_surface_map.npz"),
                "handoff_global_step": int(global_step),
                "handoff_return_status": return_status,
                "active_fixations": int(target_fixations),
            })
        else:
            rows.append({
                "object_id": int(oid),
                "geometry": "SURFEL_MAP",
                "source": str(object_sources[oid]),
                "source_sha256": _sha256(object_sources[oid]),
                "point_count": int(len(object_maps[oid].xyz_h)),
                "read_only": True,
            })
    json_write(path, {
        "schema": "MultiObject3e-scene-graph-v1",
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

    m3d, pm3c, parent3c, target_id, objects = _validate_parent(args.parent)
    report3d = json.loads((args.parent / m3d["report"]).read_text())

    # Pin both the epistemic audit and the scene state it audited.
    parent3d_names = ("prediction_manifest.json", m3d["report"], m3d["visual"])
    parent3d_hashes = {n: _sha256(args.parent / n) for n in parent3d_names}
    parent3c_names = (
        "prediction_manifest.json", "scene_graph.json",
        f"object_{target_id}_surface_map.npz", f"object_{target_id}_policy_trace.json",
    )
    parent3c_hashes = {n: _sha256(parent3c / n) for n in parent3c_names}

    object_sources: dict[int, Path] = {}
    object_maps: dict[int, object] = {}
    object_hashes_before: dict[int, str] = {}
    for oid, obj in objects.items():
        src = _resolve(obj["source"], parent3c)
        sm_i = load_map(src)
        if set(np.unique(sm_i.instance_id).tolist()) != {int(oid)}:
            raise AssertionError(f"scene object {oid} source lost id purity")
        object_sources[int(oid)] = src
        object_maps[int(oid)] = sm_i
        object_hashes_before[int(oid)] = _sha256(src)

    (sm, profile, chart, footprint_cells, footprint_deg, raw_before, support_before,
     audit_before, refined_before, _cell_ev_before, cases, observations) = _rebuild_epistemic(
        parent3c, pm3c, target_id
    )
    observation_hashes_before = parent_audit._case_hashes(cases)
    old_gazes = [tuple(map(float, g)) for g in pm3c.get("selected_object_fixation_gazes_deg", [])]
    if len(old_gazes) != len(observations):
        raise AssertionError("selected-object gaze/history length mismatch")

    before_all, before_ext, before_int = _state_counts(refined_before, audit_before)
    expected_ext = int(m3d.get("summary", {}).get("exterior_refined_cells_by_state", {}).get("NEVER_OBSERVED", -1))
    if before_ext["NEVER_OBSERVED"] != expected_ext or expected_ext <= 0:
        raise AssertionError("reconstructed pre-handoff epistemic field disagrees with MultiObject-3d")
    if int(report3d.get("exterior_refined_cells_by_state", {}).get("NEVER_OBSERVED", -1)) != expected_ext:
        raise AssertionError("MultiObject-3d report/manifest epistemic count mismatch")

    selected = epistemic_gaze.select_epistemic_probe(
        shoreline=audit_before.shoreline,
        component_labels=audit_before.component_labels,
        components=audit_before.components,
        exterior_distance_cells=audit_before.exterior_distance_cells,
        refined_state=refined_before,
        never_observed_code=epi.STATE_CODE["NEVER_OBSERVED"],
        chart=chart,
        existing_gazes=old_gazes,
    )
    if selected is None:
        raise AssertionError("no eligible exterior NEVER_OBSERVED handoff gaze remains")
    gaze = tuple(map(float, selected["probe_gaze_deg"]))
    if any(np.allclose(np.asarray(g), np.asarray(gaze), atol=1e-9, rtol=0.0) for g in old_gazes):
        raise AssertionError("epistemic handoff selected an already visited gaze")
    before_cell = _selected_cell_class(chart, gaze, support_before, audit_before, refined_before)
    if before_cell.get("cell_state") != "NEVER_OBSERVED" or before_cell.get("component_kind") != "EXTERIOR":
        raise AssertionError("handoff gaze is not an exterior NEVER_OBSERVED cell")

    gy = np.asarray([g[0] for g in old_gazes], float)
    gp = np.asarray([g[1] for g in old_gazes], float)
    in_old_envelope = bool(
        float(np.min(gy)) <= gaze[0] <= float(np.max(gy))
        and float(np.min(gp)) <= gaze[1] <= float(np.max(gp))
    ) if len(old_gazes) else False
    nearest_old_gaze = float(np.min(np.hypot(gy - gaze[0], gp - gaze[1]))) if len(old_gazes) else None

    global_step = int(pm3c.get("last_global_step", max(int(o["step"]) for o in observations)) + 1)
    case = _run_scene_blender(args, profile, global_step, gaze)
    c, obs = hdr.read_observation(case)
    rec, _meta, state = compute_once(c, obs)
    ids_R, raw_R = _right_state(c, rec, state)
    target_mask = np.asarray(rec["valid"], bool) & (np.asarray(rec["instance_id"]) == target_id)
    patch = Patch(
        f"epistemic_handoff_{global_step:02d}",
        np.asarray(rec["xyz_h"])[target_mask],
        np.asarray(rec["rgb_left"])[target_mask],
        np.asarray(rec["instance_id"])[target_mask],
    )
    np.savez_compressed(
        args.out / "handoff_patch.npz",
        xyz_h=np.asarray(patch.xyz_h, np.float32),
        rgb=np.asarray(patch.rgb, np.float32),
        instance_id=np.asarray(patch.instance_id),
        valid=np.asarray(rec["valid"], bool),
        oracle_instance_id=np.asarray(rec["instance_id"]),
        raw_support_L=np.asarray(rec["raw_support_L"], bool),
        oracle_instance_id_R=np.asarray(ids_R),
        raw_support_R=np.asarray(raw_R, bool),
    )
    Image.fromarray(_tone_preview(rec["rgb_left"])).save(args.out / "handoff_rgb.png")

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
            raise AssertionError("handoff patch replay is not idempotent")
    if len(sm_after.instance_id) and set(np.unique(sm_after.instance_id).tolist()) != {target_id}:
        raise AssertionError("epistemic handoff contaminated the active-object map")

    target_map_name = f"object_{target_id}_surface_map.npz"
    target_map_path = args.out / target_map_name
    save_map(target_map_path, sm_after)
    fsg6run.save_ply(args.out / f"object_{target_id}_surface_map.ply", sm_after)

    new_ob = _new_observation(global_step, case, c, rec, ids_R, raw_R)
    observations_after = observations + [new_ob]
    raw_after, support_after, audit_after, refined_after, _cell_ev_after = _rebuild_after_same_chart(
        sm_after, chart, footprint_cells, observations_after, target_id
    )
    after_all, after_ext, after_int = _state_counts(refined_after, audit_after)
    after_cell = _selected_cell_class(chart, gaze, support_after, audit_after, refined_after)
    parent_audit._write_visual(args.out / "epistemic_before.png", support_before, audit_before, refined_before)
    parent_audit._write_visual(args.out / "epistemic_after.png", support_after, audit_after, refined_after)

    gazes_after = old_gazes + [gaze]
    history_after = parent_audit._policy_history(observations, target_id)
    history_after.append(policy.history_entry(c, rec["instance_id"], rec["raw_support_L"], ids_R, raw_R, target_id))
    returned = policy.choose_next(
        gaze[0], gaze[1], c,
        rec["instance_id"], rec["raw_support_L"], ids_R, raw_R,
        sm_after.xyz_h, gazes_after, history_after, target_id,
    )
    return_status = progress.classify_return(returned)
    returned_record = dict(returned)
    returned_record["object_fixation_index"] = int(len(gazes_after) - 1)
    returned_record["global_step"] = int(global_step)
    parent_trace_payload = json.loads((parent3c / f"object_{target_id}_policy_trace.json").read_text())
    updated_trace = list(parent_trace_payload.get("trace", [])) + [returned_record]
    json_write(args.out / f"object_{target_id}_policy_trace.json", {
        "policy": "frozen_fsg6f_via_reused_multiobject2c_target_label_adapter",
        "target_object_id": int(target_id),
        "trace": updated_trace,
        "last_action_executed": False,
        "bounded_handoff": True,
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
        args.out / "scene_graph.json", parent3c, target_id, objects,
        object_sources, object_maps, target_map_path, len(sm_after.xyz_h),
        global_step, len(gazes_after), scene_chart, footprint_counts, return_status,
    )

    visible_target = int(np.count_nonzero(np.asarray(rec["instance_id"]) == target_id))
    valid_target = int(np.count_nonzero(target_mask))
    recovery = float(valid_target / visible_target) if visible_target else None
    handoff_report = {
        "selected_object_id": int(target_id),
        "parent_stop_interpretation": m3d["summary"]["stop_interpretation"],
        "selection_rule": "reused cyclopean1e_gaze.select_epistemic_probe unchanged",
        "selected_epistemic_region": selected,
        "handoff_gaze_deg": [float(gaze[0]), float(gaze[1])],
        "handoff_gaze_inside_previous_envelope": in_old_envelope,
        "handoff_gaze_nearest_previous_gaze_l2_deg": nearest_old_gaze,
        "selected_cell_before": before_cell,
        "selected_cell_after": after_cell,
        "global_step": int(global_step),
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
        "exterior_never_observed_before": int(before_ext["NEVER_OBSERVED"]),
        "exterior_never_observed_after": int(after_ext["NEVER_OBSERVED"]),
        "all_refined_before": before_all,
        "all_refined_after": after_all,
        "exterior_refined_before": before_ext,
        "exterior_refined_after": after_ext,
        "internal_refined_before": before_int,
        "internal_refined_after": after_int,
        "returned_local_policy_decision": returned_record,
        "return_status": return_status,
        "returned_action_executed": False,
        "experiment_stop": progress.experiment_stop(),
    }
    json_write(args.out / "handoff_report.json", handoff_report)

    # Verify the bounded intervention touched only the new active-object output.
    if {n: _sha256(args.parent / n) for n in parent3d_names} != parent3d_hashes:
        raise AssertionError("MultiObject-3d parent changed during handoff")
    if {n: _sha256(parent3c / n) for n in parent3c_names} != parent3c_hashes:
        raise AssertionError("MultiObject-3c scene parent changed during handoff")
    if parent_audit._case_hashes(cases) != observation_hashes_before:
        raise AssertionError("selected-object saved history changed during handoff")
    for oid, src in object_sources.items():
        if _sha256(src) != object_hashes_before[oid]:
            raise AssertionError(f"scene object {oid} source changed during handoff")

    manifest = {
        "schema": public.SPEC_ID,
        "public_spec_sha256": public.public_digest(),
        "parent_spec": public.PARENT_SPEC_ID,
        "parent_record": str(args.parent),
        "scene_parent_record": str(parent3c),
        "seed": public.SEED,
        "profile": profile,
        "fixture": public.FIXTURE,
        "fixed_head": True,
        "static_scene": True,
        "truth_opened": False,
        "selected_object_id": int(target_id),
        "preexisting_object_ids": [int(x) for x in pm3c.get("preexisting_object_ids", [])],
        "parent_stop_interpretation": m3d["summary"]["stop_interpretation"],
        "parent_final_policy_stop_replayed_exactly": bool(m3d.get("final_policy_stop_replayed_exactly")),
        "epistemic_selector_source": public.EPISTEMIC_SELECTOR,
        "epistemic_selector_reused_unchanged": True,
        "selected_epistemic_region": selected,
        "handoff_gaze_deg": [float(gaze[0]), float(gaze[1])],
        "handoff_gaze_inside_previous_envelope": in_old_envelope,
        "handoff_gaze_nearest_previous_gaze_l2_deg": nearest_old_gaze,
        "global_step": int(global_step),
        "added_fixations": 1,
        "parent_fixations_rerendered": 0,
        "fusion_iterations_added": int(0 if empty else 1),
        "growth_loop_iterations_added": 0,
        "returned_local_policy_decisions": 1,
        "returned_local_action_executed": False,
        "automatic_handoff_loop": False,
        "automatic_scene_scheduler": False,
        "revisit_scheduler_used": False,
        "watchdog_changed": False,
        "quality_gate_used": False,
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
        "selected_object_fixation_gazes_deg": [list(map(float, g)) for g in gazes_after],
        "selected_object_fixations_total": int(len(gazes_after)),
        "last_global_step": int(global_step),
        "epistemic_before": {
            "exterior_never_observed": int(before_ext["NEVER_OBSERVED"]),
            "selected_cell": before_cell,
        },
        "epistemic_after": {
            "exterior_never_observed": int(after_ext["NEVER_OBSERVED"]),
            "selected_cell": after_cell,
        },
        "returned_local_policy_decision": returned_record,
        "return_status": return_status,
        "experiment_stop": progress.experiment_stop(),
        "handoff_report": "handoff_report.json",
        "active_object_map": target_map_name,
        "scene_graph": "scene_graph.json",
        "scene_footprints": "scene_cyclopean_footprints.npz",
        "scene_footprint_counts": footprint_counts,
        "parent3d_hashes": parent3d_hashes,
        "parent3c_hashes": parent3c_hashes,
        "scene_object_sha256_before": {str(k): v for k, v in object_hashes_before.items()},
        "scene_object_sha256_after": {str(k): _sha256(v) for k, v in object_sources.items()},
        "observation_input_hashes": observation_hashes_before,
        "next_stage": public.PUBLIC_SPEC["next_stage"],
        "structural_fails": [],
    }
    json_write(args.out / "prediction_manifest.json", manifest)
    print("[multiobject3e-run] MULTIOBJECT3E_COMPLETE " + json.dumps({
        "selected_object_id": int(target_id),
        "handoff_gaze_deg": manifest["handoff_gaze_deg"],
        "empty_look": bool(empty),
        "map_points_before": int(len(sm.xyz_h)),
        "map_points_after": int(len(sm_after.xyz_h)),
        "exterior_never_observed_before": int(before_ext["NEVER_OBSERVED"]),
        "exterior_never_observed_after": int(after_ext["NEVER_OBSERVED"]),
        "return_status": return_status,
        "returned_next_gaze_deg": returned.get("next_gaze_deg"),
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
