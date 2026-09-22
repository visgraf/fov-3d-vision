"""Read-only epistemic audit of the FullScene-1c locally resolved selected object."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

import cyclopean1a_topology as topo1a
import cyclopean1b_boundary as boundary
import cyclopean1d_epistemic as epi
from fsg3_surface_map import load_map
from fsg_geometry import json_write
from fsg_stereo_supported import check_kernel_equivalence

import fullscene1c_public as parent_public
import fullscene1d_public as public
import multiobject3d_audit as inherited_audit


def _validate_parent(parent: Path) -> tuple[dict, int, tuple[int, ...], dict[int, dict], dict]:
    manifest_path = parent / "prediction_manifest.json"
    scene_path = parent / "scene_graph.json"
    trace_path_hint = None
    if not manifest_path.is_file() or not scene_path.is_file():
        raise FileNotFoundError("FullScene-1c parent manifest/scene graph missing")
    m = json.loads(manifest_path.read_text())
    if m.get("schema") != public.PARENT_SPEC_ID:
        raise AssertionError("FullScene-1d requires a completed FullScene-1c parent")
    if m.get("public_spec_sha256") != parent_public.public_digest():
        raise AssertionError("FullScene-1c public digest mismatch")
    if int(m.get("seed", -1)) != public.SEED or m.get("truth_opened") is not False:
        raise AssertionError("wrong seed or truth integrity broken")
    if not m.get("fixed_head") or not m.get("static_scene"):
        raise AssertionError("fixed-head/static-scene invariant broken")
    if m.get("structural_fails") != []:
        raise AssertionError("FullScene-1c parent is structurally incomplete")
    if m.get("termination_reason") != "no_frontier" or m.get("scientific_stop_reached") is not True:
        raise AssertionError("FullScene-1d requires the FullScene-1c no_frontier scientific stop")
    total = int(m.get("selected_object_fixations_total", -1))
    watchdog = int(m.get("watchdog_selected_object_fixations", -1))
    if total <= 0 or watchdog <= 0 or total >= watchdog:
        raise AssertionError("FullScene-1c did not stop before its engineering watchdog")
    if m.get("preexisting_objects_read_only") is not True or m.get("selected_object_map_pure") is not True:
        raise AssertionError("FullScene-1c object separation/purity contract broken")
    if m.get("deferred_prior_object_action_executed") is not False:
        raise AssertionError("prior object's deferred local action was executed")
    if int(m.get("epistemic_handoffs_added", -1)) != 0:
        raise AssertionError("FullScene-1c unexpectedly added an epistemic handoff")
    if m.get("automatic_scene_scheduler") is not False or m.get("revisit_scheduler_used") is not False:
        raise AssertionError("FullScene-1c unexpectedly introduced a scheduler")
    if m.get("quality_gate_used") is not False or m.get("new_threshold_added") is not False:
        raise AssertionError("FullScene-1c unexpectedly introduced a quality/threshold gate")

    target_id = int(m.get("selected_object_id", -1))
    pre = tuple(int(x) for x in m.get("preexisting_object_ids", []))
    object_ids = tuple(int(x) for x in m.get("object_ids", []))
    if target_id <= 0 or not pre or target_id in set(pre):
        raise AssertionError("invalid selected/pre-existing object ids")
    if object_ids != pre + (target_id,):
        raise AssertionError("FullScene-1c object set/order changed")

    trace_path_hint = parent / f"object_{target_id}_policy_trace.json"
    if not trace_path_hint.is_file():
        raise FileNotFoundError("FullScene-1c policy trace missing")
    trace_payload = json.loads(trace_path_hint.read_text())
    trace = trace_payload.get("trace", [])
    if not trace:
        raise AssertionError("FullScene-1c policy trace is empty")
    final = trace[-1]
    if final.get("stop") is not True or final.get("reason") != "no_frontier":
        raise AssertionError("saved final FullScene-1c decision is not no_frontier")
    if int(final.get("frontier_open_count", -1)) != 0:
        raise AssertionError("FullScene-1d is specifically the zero-OPEN locally resolved stop audit")
    if int(final.get("candidates_before_consensus_count", -1)) != 0:
        raise AssertionError("saved final FullScene-1c stop still has admissible candidates")

    sg = json.loads(scene_path.read_text())
    objs = {int(o["object_id"]): o for o in sg.get("objects", [])}
    if set(objs) != set(object_ids):
        raise AssertionError("FullScene-1c scene graph/object ids disagree")
    if objs[target_id].get("geometry") != "SURFEL_MAP":
        raise AssertionError("selected object is not a grown surfel map")
    return m, target_id, pre, objs, final


def _all_cases(parent: Path, pm: dict) -> list[tuple[int, Path]]:
    seed_step = int(pm.get("global_step_seed", -1))
    last_step = int(pm.get("last_global_step", -1))
    expected_n = int(pm.get("selected_object_fixations_total", -1))
    if seed_step < 0 or last_step < seed_step or expected_n <= 0:
        raise AssertionError("FullScene-1c selected-object chronology missing")
    seed_parent = inherited_audit._resolve(pm["parent_record"], parent)
    seed_case = seed_parent / "acquisition" / f"fix_{seed_step:02d}"
    if not (seed_case / "calibration.json").is_file() or not (seed_case / "observation.npz").is_file():
        raise FileNotFoundError("FullScene-1b seed acquisition missing")
    cases: list[tuple[int, Path]] = [(seed_step, seed_case)]
    for step in range(seed_step + 1, last_step + 1):
        case = parent / "acquisitions" / f"fix_{step:02d}" / f"fix_{step:02d}"
        if not (case / "calibration.json").is_file() or not (case / "observation.npz").is_file():
            raise FileNotFoundError(f"FullScene-1c selected-object acquisition {step} missing")
        cases.append((step, case))
    if len(cases) != expected_n:
        raise AssertionError(f"selected-object observation count mismatch: {len(cases)} != {expected_n}")
    steps = [s for s, _ in cases]
    if steps != list(range(seed_step, seed_step + expected_n)):
        raise AssertionError(f"selected-object global history is not contiguous: {steps}")
    return cases


def _object_status(exterior: dict[str, int], all_counts: dict[str, int]) -> str:
    if int(exterior.get("NEVER_OBSERVED", 0)) > 0:
        return "ATTENTION_INCOMPLETE_RETAIN_FOR_REVISIT"
    if int(all_counts.get("OBSERVED_TARGET_NO_DEPTH", 0)) > 0:
        return "ATTENTION_COMPLETE_MEASUREMENT_PARTIAL"
    return "ATTENTION_COMPLETE_NO_TARGET_NO_DEPTH_RESIDUE"


def _stop_interpretation(exterior: dict[str, int], all_counts: dict[str, int], final: dict) -> str:
    if final.get("stop") is not True or final.get("reason") != "no_frontier":
        return "PARENT_NOT_AT_DECLARED_POLICY_STOP"
    if int(final.get("frontier_open_count", -1)) != 0:
        return "PARENT_NOT_ZERO_OPEN_FRONTIER_STOP"
    if int(exterior.get("NEVER_OBSERVED", 0)) > 0:
        return "LOCAL_FRONTIER_RESOLVED_BUT_ATTENTION_INCOMPLETE"
    if int(all_counts.get("OBSERVED_TARGET_NO_DEPTH", 0)) > 0:
        return "LOCAL_FRONTIER_RESOLVED_ATTENTION_COMPLETE_MEASUREMENT_PARTIAL"
    return "LOCAL_FRONTIER_AND_ATTENTION_RESOLVED_UNDER_CURRENT_REPRESENTATION"


def execute(args) -> dict:
    args.parent = Path(args.parent).resolve()
    args.out = Path(args.out).resolve()
    if args.out.exists():
        raise FileExistsError("output must be new")
    args.out.mkdir(parents=True)
    check_kernel_equivalence()

    pm, target_id, preexisting_ids, objects, final_policy_decision = _validate_parent(args.parent)

    pinned_names = (
        "prediction_manifest.json",
        "scene_graph.json",
        "scene_cyclopean_footprints.npz",
        f"object_{target_id}_surface_map.npz",
        f"object_{target_id}_policy_trace.json",
    )
    pinned = {n: inherited_audit._sha256(args.parent / n) for n in pinned_names}

    object_sources: dict[int, Path] = {}
    object_hashes_before: dict[int, str] = {}
    for oid, obj in objects.items():
        src = inherited_audit._resolve(obj["source"], args.parent)
        if not src.is_file():
            raise FileNotFoundError(src)
        sm_i = load_map(src)
        if len(sm_i.instance_id) and set(np.unique(sm_i.instance_id).tolist()) != {int(oid)}:
            raise AssertionError(f"scene object {oid} source lost id purity")
        object_sources[int(oid)] = src
        object_hashes_before[int(oid)] = inherited_audit._sha256(src)

    target_path = args.parent / f"object_{target_id}_surface_map.npz"
    sm = load_map(target_path)
    if len(sm.instance_id) and set(np.unique(sm.instance_id).tolist()) != {target_id}:
        raise AssertionError("selected-object map lost id purity")

    profile = str(pm.get("profile", "full"))
    chart, footprint_cells, footprint_deg = topo1a.build_chart(sm.xyz_h, profile)
    if abs(float(chart.grid_deg) - public.GRID_DEG) > 1e-12:
        raise AssertionError("selected-object cyclopean grid changed from established 0.1 degree scale")

    raw, support, target_range = topo1a.rasterize_target(sm.xyz_h, chart, footprint_cells)
    evidence = topo1a.empty_evidence(chart)
    cases = _all_cases(args.parent, pm)
    observation_hashes_before = inherited_audit._case_hashes(cases)
    observations = []
    for step, case in cases:
        ob = inherited_audit._saved_observation(step, case)
        observations.append(ob)
        topo1a.add_observation(evidence, chart, ob["xyz_h"], ob["instance_id"], ob["valid"], target_id)

    ev = boundary.EvidenceArrays(
        evidence.seen_target,
        evidence.seen_nontarget,
        evidence.target_range_m,
        evidence.nontarget_range_m,
    )
    audit = boundary.analyze_boundary(
        raw_support=raw,
        support=support,
        target_range_m=target_range,
        evidence=ev,
        grid_deg=chart.grid_deg,
        yaw0_deg=chart.yaw0_deg,
        pitch0_deg=chart.pitch0_deg,
        footprint_cells=footprint_cells,
        association_radius_m=float(public.FUSION["association_radius_m"]),
    )
    refined, cell_ev = inherited_audit._refine_unobserved(chart, audit, observations, target_id)
    arcs = inherited_audit._refined_arcs(chart, audit, refined, cell_ev)

    visited_gazes = [tuple(map(float, g)) for g in pm.get("selected_object_fixation_gazes_deg", [])]
    if len(visited_gazes) != len(observations):
        raise AssertionError("selected-object gaze/history length mismatch")
    gy = np.asarray([g[0] for g in visited_gazes], float)
    gp = np.asarray([g[1] for g in visited_gazes], float)
    gaze_envelope = {
        "yaw_min_deg": float(np.min(gy)), "yaw_max_deg": float(np.max(gy)),
        "pitch_min_deg": float(np.min(gp)), "pitch_max_deg": float(np.max(gp)),
    }
    for row in arcs:
        cy = float(row["centroid_yaw_deg"])
        cp = float(row["centroid_pitch_deg"])
        row["centroid_inside_visited_gaze_envelope"] = bool(
            gaze_envelope["yaw_min_deg"] <= cy <= gaze_envelope["yaw_max_deg"]
            and gaze_envelope["pitch_min_deg"] <= cp <= gaze_envelope["pitch_max_deg"]
        )
        row["centroid_nearest_visited_gaze_l2_deg"] = float(np.min(np.hypot(gy - cy, gp - cp)))

    refined_counts = {name: int((refined == code).sum()) for name, code in epi.STATE_CODE.items()}
    exterior = {name: 0 for name in epi.STATE_CODE}
    internal = {name: 0 for name in epi.STATE_CODE}
    for row in arcs:
        (exterior if row["component_kind"] == "EXTERIOR" else internal)[row["state"]] += int(row["cell_count"])
    base_counts = {name: int((audit.state_code == code).sum()) for name, code in boundary.STATE_CODE.items()}
    ext_components = [c for c in audit.components if c["kind"] == "EXTERIOR"]

    policy_stop = inherited_audit._reconstruct_final_policy_stop(
        pm, sm, observations, target_id, chart, support, audit, refined, final_policy_decision
    )
    replay_summary = policy_stop["replayed_final_decision_summary"]
    if int(replay_summary.get("frontier_open_count", -1)) != 0:
        raise AssertionError("replayed final policy stop is not zero-OPEN")

    object_status = _object_status(exterior, refined_counts)
    stop_interpretation = _stop_interpretation(exterior, refined_counts, final_policy_decision)
    scene_disposition = "RETURN_TO_SCENE_INVENTORY"

    report_name = f"object_{target_id}_fullscene1d_epistemic_audit.json"
    visual_name = f"object_{target_id}_fullscene1d_epistemic_shoreline.png"
    report = {
        "seed": int(pm["seed"]),
        "profile": profile,
        "object_id": int(target_id),
        "audit_history_scope": public.AUDIT_HISTORY_SCOPE,
        "parent_termination_reason": pm.get("termination_reason"),
        "parent_scientific_stop_reached": pm.get("scientific_stop_reached"),
        "parent_final_policy_decision": final_policy_decision,
        "policy_stop_reconstruction": policy_stop,
        "local_stop_subtype": "ZERO_OPEN_FRONTIER_BOUNDARY_RESOLVED_STOP",
        "observation_count": len(observations),
        "observation_steps": [int(o["step"]) for o in observations],
        "visited_gaze_envelope_deg": gaze_envelope,
        "chart": {
            "yaw0_deg": chart.yaw0_deg,
            "pitch0_deg": chart.pitch0_deg,
            "grid_deg": chart.grid_deg,
            "width": chart.width,
            "height": chart.height,
        },
        "footprint_cells": int(footprint_cells),
        "footprint_radius_deg": float(footprint_deg),
        "map_points": int(len(sm.xyz_h)),
        "raw_support_cells": int(raw.sum()),
        "support_cells": int(support.sum()),
        "complement_cells": int((~support).sum()),
        "shoreline_cells": int(audit.shoreline.sum()),
        "max_exterior_border_distance_cells": max(
            (int(c["max_border_distance_cells"]) for c in ext_components if c["max_border_distance_cells"] is not None),
            default=None,
        ),
        "base_shoreline_cells_by_state": base_counts,
        "refined_unobserved_cells_by_state": refined_counts,
        "exterior_refined_cells_by_state": exterior,
        "internal_refined_cells_by_state": internal,
        "components": audit.components,
        "refined_arcs": arcs,
        "object_status": object_status,
        "stop_interpretation": stop_interpretation,
        "scene_disposition": scene_disposition,
        "next_stage": public.NEXT_STAGE,
    }
    json_write(args.out / report_name, report)
    inherited_audit._write_visual(args.out / visual_name, support, audit, refined)

    after = {n: inherited_audit._sha256(args.parent / n) for n in pinned_names}
    if after != pinned:
        raise AssertionError("FullScene-1c parent changed during read-only audit")
    for oid, src in object_sources.items():
        if inherited_audit._sha256(src) != object_hashes_before[oid]:
            raise AssertionError(f"scene object {oid} changed during FullScene-1d audit")
    if inherited_audit._case_hashes(cases) != observation_hashes_before:
        raise AssertionError("saved selected-object observations changed during read-only audit")

    manifest = {
        "schema": public.SPEC_ID,
        "public_spec_sha256": public.public_digest(),
        "parent_spec": public.PARENT_SPEC_ID,
        "parent_record": str(args.parent),
        "parent_hashes": pinned,
        "scene_object_sources": {str(k): str(v) for k, v in object_sources.items()},
        "scene_object_sha256_before": {str(k): v for k, v in object_hashes_before.items()},
        "scene_object_sha256_after": {str(k): inherited_audit._sha256(v) for k, v in object_sources.items()},
        "observation_input_hashes": observation_hashes_before,
        "seed": int(pm["seed"]),
        "profile": profile,
        "fixture": public.FIXTURE,
        "fixed_head": True,
        "static_scene": True,
        "truth_opened": False,
        "selected_object_id": int(target_id),
        "preexisting_object_ids": [int(x) for x in preexisting_ids],
        "object_ids": [int(x) for x in pm.get("object_ids", [])],
        "acquisitions_added": 0,
        "growth_iterations_added": 0,
        "fusion_iterations_added": 0,
        "epistemic_handoffs_added": 0,
        "watchdog_changed": False,
        "parent_files_modified": False,
        "scene_objects_read_only": True,
        "selected_object_read_only": True,
        "selected_object_map_pure": True,
        "deferred_prior_object_action_executed": False,
        "parent_termination_reason": pm.get("termination_reason"),
        "parent_scientific_stop_reached": pm.get("scientific_stop_reached"),
        "parent_frontier_open_count": int(final_policy_decision.get("frontier_open_count", -1)),
        "parent_frontier_boundary_resolved_count": int(final_policy_decision.get("frontier_boundary_resolved_count", -1)),
        "final_policy_stop_replayed_exactly": True,
        "replayed_frontier_open_count": int(replay_summary.get("frontier_open_count", -1)),
        "observation_count": len(observations),
        "observation_steps": [int(o["step"]) for o in observations],
        "older_s0_scene_history_added_to_audit": False,
        "reused_multiobject3d_audit_helpers": True,
        "summary": {
            "shoreline_cells": report["shoreline_cells"],
            "max_exterior_border_distance_cells": report["max_exterior_border_distance_cells"],
            "base_shoreline_cells_by_state": base_counts,
            "refined_unobserved_cells_by_state": refined_counts,
            "exterior_refined_cells_by_state": exterior,
            "internal_refined_cells_by_state": internal,
            "object_status": object_status,
            "stop_interpretation": stop_interpretation,
            "local_stop_subtype": report["local_stop_subtype"],
            "frontier_state_to_cyclopean_cell_counts": policy_stop["relation"]["frontier_state_to_cyclopean_cell_counts"],
            "scene_disposition": scene_disposition,
        },
        "report": report_name,
        "visual": visual_name,
        "automatic_object_discovery": False,
        "automatic_scene_scheduler": False,
        "revisit_scheduler_used": False,
        "quality_gate_used": False,
        "new_threshold_added": False,
        "next_stage": public.NEXT_STAGE,
        "structural_fails": [],
    }
    json_write(args.out / "prediction_manifest.json", manifest)
    print("[fullscene1d-run] FULLSCENE1D_COMPLETE " + json.dumps({
        "selected_object_id": int(target_id),
        "shoreline_cells": report["shoreline_cells"],
        "exterior_never_observed": exterior["NEVER_OBSERVED"],
        "observed_target_no_depth": refined_counts["OBSERVED_TARGET_NO_DEPTH"],
        "object_status": object_status,
        "stop_interpretation": stop_interpretation,
        "scene_disposition": scene_disposition,
        "structural_fails": [],
    }, sort_keys=True), flush=True)
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--parent", required=True)
    ap.add_argument("--out", required=True)
    execute(ap.parse_args())


if __name__ == "__main__":
    main()
