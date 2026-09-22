"""Read-only cyclopean epistemic audit of the MultiObject-3c selected object.

This step adds no view and takes no action.  It rebuilds selected-object
support on the inherited 0.1-degree cyclopean scale, classifies the shoreline
with the existing Cyclopean-1b boundary semantics, then refines only base
UNOBSERVED cells with the existing Cyclopean-1d observation-versus-measurement
semantics.  It also replays the final frozen FSG6f decision from saved data to
verify the no_frontier stop exactly, then relates the final 3D look-ahead
frontier targets to the cyclopean epistemic field descriptively.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

import cyclopean1a_topology as topo1a
import cyclopean1b_boundary as boundary
import cyclopean1d_epistemic as epi
import fsg_stereo_hdr as hdr
import fsg6f_frontier as frozen_frontier
from fsg_stereo import rectification, support_mask
from fsg_stereo_supported import compute_once, check_kernel_equivalence
from fsg3_surface_map import load_map
from fsg_geometry import json_write

import multiobject2c_policy as policy
import multiobject3d_public as public
import multiobject3d_progress as progress


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _resolve(path_like: str, base: Path) -> Path:
    p = Path(path_like)
    return p.resolve() if p.is_absolute() else (base / p).resolve()


def _validate_parent(parent: Path) -> tuple[dict, int, dict[int, dict]]:
    m = json.loads((parent / "prediction_manifest.json").read_text())
    if m.get("schema") != public.PARENT_SPEC_ID:
        raise AssertionError("MultiObject-3d requires a completed MultiObject-3c parent")
    if int(m.get("seed", -1)) != public.SEED or m.get("truth_opened") is not False:
        raise AssertionError("wrong seed or truth integrity broken")
    if not m.get("fixed_head") or not m.get("static_scene"):
        raise AssertionError("fixed-head/static-scene invariant broken")
    target_id = int(m.get("selected_object_id", -1))
    if target_id <= 0:
        raise AssertionError("parent selected-object id missing")
    pre = tuple(int(x) for x in m.get("preexisting_object_ids", []))
    if target_id in set(pre) or len(pre) < 2:
        raise AssertionError("selected-object/pre-existing object contract broken")
    if not m.get("preexisting_objects_read_only") or not m.get("selected_object_map_pure"):
        raise AssertionError("parent object separation/purity contract broken")
    if int(m.get("selected_object_fixations_total", -1)) <= 0:
        raise AssertionError("parent has no selected-object history")
    if m.get("termination_reason") != "no_frontier" or m.get("scientific_stop_reached") is not True:
        raise AssertionError("MultiObject-3d requires the declared MultiObject-3c no_frontier scientific stop")
    if int(m.get("selected_object_fixations_total", 0)) >= int(m.get("watchdog_selected_object_fixations", 0)):
        raise AssertionError("MultiObject-3c stop was not before its engineering watchdog")
    target_map = parent / f"object_{target_id}_surface_map.npz"
    if not target_map.is_file():
        raise FileNotFoundError("parent selected-object surface map missing")
    graph = json.loads((parent / "scene_graph.json").read_text())
    objs = {int(o["object_id"]): o for o in graph.get("objects", [])}
    expected = set(pre + (target_id,))
    if set(objs) != expected:
        raise AssertionError("parent scene graph/object ids disagree")
    return m, target_id, objs


def _seed_case(parent: Path, pm: dict) -> tuple[int, Path]:
    seed_step = int(pm.get("global_step_seed", -1))
    if seed_step < 0:
        raise AssertionError("selected-object seed step missing")
    seed_parent = _resolve(pm["parent_record"], parent)
    case = seed_parent / "acquisition" / f"fix_{seed_step:02d}"
    if not (case / "calibration.json").is_file() or not (case / "observation.npz").is_file():
        raise FileNotFoundError("selected-object seed acquisition missing")
    return seed_step, case


def _all_cases(parent: Path, pm: dict) -> list[tuple[int, Path]]:
    seed_step, seed_case = _seed_case(parent, pm)
    found: dict[int, Path] = {seed_step: seed_case}
    last = int(pm.get("last_global_step", seed_step))
    for step in range(seed_step + 1, last + 1):
        c = parent / "acquisitions" / f"fix_{step:02d}" / f"fix_{step:02d}"
        if not (c / "calibration.json").is_file() or not (c / "observation.npz").is_file():
            raise FileNotFoundError(f"missing selected-object acquisition {step}")
        found[step] = c
    expected_n = int(pm["selected_object_fixations_total"])
    cases = sorted(found.items())
    if len(cases) != expected_n:
        raise AssertionError(f"selected-object observation count mismatch: {len(cases)} != {expected_n}")
    steps = [s for s, _ in cases]
    if steps != list(range(seed_step, seed_step + expected_n)):
        raise AssertionError(f"selected-object global history is not contiguous: {steps}")
    return cases


def _case_hashes(cases: list[tuple[int, Path]]) -> dict[str, dict[str, str]]:
    return {
        f"fix_{step:02d}": {
            "calibration.json": _sha256(case / "calibration.json"),
            "observation.npz": _sha256(case / "observation.npz"),
        }
        for step, case in cases
    }


def _saved_observation(step: int, case: Path) -> dict:
    c, obs = hdr.read_observation(case)
    rec, _meta, state = compute_once(c, obs)
    r = rectification(c)
    x, y, cw, ch = map(int, rec["crop_xywh"])
    sl = np.s_[y:y+ch, x:x+cw]
    ids_R = np.asarray(state["ids_right"])[sl]
    raw_R = np.asarray(support_mask(c, rec, "R"), bool)[sl]
    if not np.array_equal(np.asarray(rec["instance_id"]), np.asarray(state["ids_left"])[sl]):
        raise AssertionError("left rectified ID replay mismatch")
    return {
        "step": int(step),
        "label": f"fix_{step:02d}",
        "case": str(case),
        "calibration": c,
        "rectification": r,
        "instance_id": np.asarray(rec["instance_id"]).copy(),
        "instance_R": ids_R.copy(),
        "valid": np.asarray(rec["valid"], bool).copy(),
        "raw_support_L": np.asarray(rec["raw_support_L"], bool).copy(),
        "raw_support_R": raw_R.copy(),
        "xyz_h": np.asarray(rec["xyz_h"]).copy(),
    }


def _cell_point(chart, y: int, x: int, rho: float) -> np.ndarray:
    yaw = chart.yaw0_deg + x * chart.grid_deg
    pitch = chart.pitch0_deg + y * chart.grid_deg
    return topo1a.angles_to_dir(float(yaw), float(pitch)) * float(rho)


def _components(mask: np.ndarray) -> list[np.ndarray]:
    m = np.asarray(mask, bool)
    h, w = m.shape
    seen = np.zeros_like(m)
    out = []
    nbr = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    for y0, x0 in zip(*np.nonzero(m)):
        if seen[y0, x0]:
            continue
        stack = [(int(y0), int(x0))]
        seen[y0, x0] = True
        cells = []
        while stack:
            y, x = stack.pop()
            cells.append((y, x))
            for dy, dx in nbr:
                yy, xx = y + dy, x + dx
                if 0 <= yy < h and 0 <= xx < w and m[yy, xx] and not seen[yy, xx]:
                    seen[yy, xx] = True
                    stack.append((yy, xx))
        out.append(np.asarray(cells, np.int32))
    return out


def _refine_unobserved(chart, audit, observations: list[dict], target_id: int):
    refined = np.zeros(audit.shoreline.shape, np.uint8)
    evidence_by_cell = {}
    unobs_code = boundary.STATE_CODE["UNOBSERVED"]
    for y, x in zip(*np.nonzero(audit.shoreline & (audit.state_code == unobs_code))):
        rho = float(audit.local_target_range_m[y, x])
        if not np.isfinite(rho) or rho <= 0:
            refined[y, x] = epi.STATE_CODE["NO_RANGE_REFERENCE"]
            evidence_by_cell[(int(y), int(x))] = epi.ProjectedEvidence()
            continue
        point = _cell_point(chart, int(y), int(x), rho)[None, :]
        total = epi.ProjectedEvidence()
        for ob in observations:
            e = epi.sample_projected_evidence(
                ob["calibration"], ob["rectification"], ob["instance_id"], ob["valid"],
                ob["raw_support_L"], point, int(target_id),
            )[0]
            total = epi.add_evidence(total, e)
        state = epi.classify_counts(total, True)
        refined[y, x] = epi.STATE_CODE[state]
        evidence_by_cell[(int(y), int(x))] = total
    return refined, evidence_by_cell


def _refined_arcs(chart, audit, refined, cell_ev):
    rows = []
    arc_id = 0
    for code, name in epi.CODE_STATE.items():
        for comp in audit.components:
            cid = int(comp["component_id"])
            mask = audit.shoreline & (audit.component_labels == cid) & (refined == code)
            for cells in _components(mask):
                if len(cells) == 0:
                    continue
                yaw = chart.yaw0_deg + cells[:, 1] * chart.grid_deg
                pitch = chart.pitch0_deg + cells[:, 0] * chart.grid_deg
                total = epi.ProjectedEvidence()
                for y, x in cells:
                    total = epi.add_evidence(total, cell_ev[(int(y), int(x))])
                d = audit.exterior_distance_cells[cells[:, 0], cells[:, 1]]
                kind = comp["kind"]
                rows.append({
                    "arc_id": int(arc_id),
                    "component_id": cid,
                    "component_kind": kind,
                    "state": name,
                    "cell_count": int(len(cells)),
                    "centroid_yaw_deg": float(np.mean(yaw)),
                    "centroid_pitch_deg": float(np.mean(pitch)),
                    "yaw_span_deg": float((cells[:,1].max()-cells[:,1].min()+1) * chart.grid_deg),
                    "pitch_span_deg": float((cells[:,0].max()-cells[:,0].min()+1) * chart.grid_deg),
                    "target_seen_samples": int(total.target_seen),
                    "target_depth_valid_samples": int(total.target_depth_valid),
                    "nontarget_seen_samples": int(total.nontarget_seen),
                    "supported_projection_samples": int(total.supported_projections),
                    "border_distance_cells_max": int(np.max(d)) if kind == "EXTERIOR" else None,
                })
                arc_id += 1
    rows.sort(key=lambda r: (
        0 if r["component_kind"] == "EXTERIOR" else 1,
        -int(r["border_distance_cells_max"] or -1),
        -r["cell_count"], r["state"],
    ))
    return rows



def _policy_history(observations: list[dict], target_id: int) -> list[dict]:
    return [
        policy.history_entry(
            ob["calibration"], ob["instance_id"], ob["raw_support_L"],
            ob["instance_R"], ob["raw_support_R"], target_id,
        )
        for ob in observations
    ]


def _same_optional_gaze(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return bool(np.allclose(np.asarray(a, float), np.asarray(b, float), atol=1e-9, rtol=0.0))


def _cell_epistemic_label(y: int, x: int, support: np.ndarray, audit, refined: np.ndarray) -> tuple[str, str | None]:
    if support[y, x]:
        return "SUPPORT", None
    if not audit.shoreline[y, x]:
        return "COMPLEMENT_NONSHORELINE", None
    base = boundary.CODE_STATE[int(audit.state_code[y, x])]
    comp_kind = None
    cid = int(audit.component_labels[y, x])
    for c in audit.components:
        if int(c["component_id"]) == cid:
            comp_kind = str(c["kind"])
            break
    if base != "UNOBSERVED":
        return base, comp_kind
    code = int(refined[y, x])
    return epi.CODE_STATE.get(code, "UNOBSERVED_UNREFINED"), comp_kind


def _frontier_relation(chart, support: np.ndarray, audit, refined: np.ndarray,
                       frontier: dict, frontier_state: dict,
                       visited_gazes: list[tuple[float, float]]) -> dict:
    yaw_t, pitch_t, _rho = topo1a.xyz_to_angles(frontier["target_xyz_h"])
    yy, xx, inside = topo1a._indices(chart, yaw_t, pitch_t)
    gy = np.asarray([g[0] for g in visited_gazes], float) if visited_gazes else np.empty(0)
    gp = np.asarray([g[1] for g in visited_gazes], float) if visited_gazes else np.empty(0)
    gaze_env = {
        "yaw_min_deg": float(np.min(gy)) if len(gy) else None,
        "yaw_max_deg": float(np.max(gy)) if len(gy) else None,
        "pitch_min_deg": float(np.min(gp)) if len(gp) else None,
        "pitch_max_deg": float(np.max(gp)) if len(gp) else None,
    }

    masks = {
        "OPEN": np.asarray(frontier_state["open"], bool),
        "MAP_RESOLVED": np.asarray(frontier_state["map_resolved"], bool),
        "BOUNDARY_RESOLVED": np.asarray(frontier_state["boundary_resolved"], bool),
    }
    by_state = {}
    open_rows = []
    for state_name, mask in masks.items():
        counts: dict[str, int] = {}
        for i in np.flatnonzero(mask):
            if not bool(inside[i]):
                label, kind = "OUT_OF_CHART", None
            else:
                label, kind = _cell_epistemic_label(int(yy[i]), int(xx[i]), support, audit, refined)
            counts[label] = counts.get(label, 0) + 1
            if state_name == "OPEN":
                if len(gy):
                    nearest = float(np.min(np.hypot(gy - yaw_t[i], gp - pitch_t[i])))
                    in_env = bool(
                        gaze_env["yaw_min_deg"] <= yaw_t[i] <= gaze_env["yaw_max_deg"]
                        and gaze_env["pitch_min_deg"] <= pitch_t[i] <= gaze_env["pitch_max_deg"]
                    )
                else:
                    nearest = None; in_env = False
                row = {
                    "frontier_index": int(i),
                    "target_yaw_deg": float(yaw_t[i]),
                    "target_pitch_deg": float(pitch_t[i]),
                    "chart_inside": bool(inside[i]),
                    "chart_y": int(yy[i]) if inside[i] else None,
                    "chart_x": int(xx[i]) if inside[i] else None,
                    "cyclopean_cell_state": label,
                    "component_kind": kind,
                    "inside_visited_gaze_envelope": in_env,
                    "nearest_visited_gaze_l2_deg": nearest,
                }
                if inside[i] and kind == "EXTERIOR":
                    row["exterior_border_distance_cells"] = int(audit.exterior_distance_cells[int(yy[i]), int(xx[i])])
                open_rows.append(row)
        by_state[state_name] = counts
    return {
        "method": "angularly quantize each frozen FSG6f look-ahead target onto the unchanged cyclopean 0.1-degree chart; descriptive only",
        "visited_gaze_envelope_deg": gaze_env,
        "frontier_state_to_cyclopean_cell_counts": by_state,
        "open_frontier_targets": open_rows,
        "open_targets_inside_visited_gaze_envelope": int(sum(bool(r["inside_visited_gaze_envelope"]) for r in open_rows)),
        "open_targets_outside_visited_gaze_envelope": int(sum(not bool(r["inside_visited_gaze_envelope"]) for r in open_rows)),
    }


def _reconstruct_final_policy_stop(pm: dict, sm, observations: list[dict], target_id: int,
                                   chart, support: np.ndarray, audit, refined: np.ndarray,
                                   saved_final: dict) -> dict:
    if not observations or saved_final is None:
        raise AssertionError("missing observations or saved final policy decision")
    gazes = [tuple(map(float, g)) for g in pm.get("selected_object_fixation_gazes_deg", [])]
    if len(gazes) != len(observations):
        raise AssertionError("selected-object gaze/history length mismatch")
    last = observations[-1]
    current = saved_final.get("current_gaze_deg")
    if current is None or not _same_optional_gaze(current, gazes[-1]):
        raise AssertionError("saved final policy current gaze disagrees with selected-object history")
    history = _policy_history(observations, target_id)
    replay = policy.choose_next(
        gazes[-1][0], gazes[-1][1], last["calibration"],
        last["instance_id"], last["raw_support_L"], last["instance_R"], last["raw_support_R"],
        sm.xyz_h, gazes, history, target_id,
    )
    exact_keys = (
        "stop", "reason", "frontier_voxel_count", "frontier_count",
        "frontier_raw_count", "frontier_map_resolved_count",
        "frontier_boundary_resolved_count", "frontier_open_count",
        "candidates_before_consensus_count", "consensus_rejected_candidate_count",
    )
    for k in exact_keys:
        if replay.get(k) != saved_final.get(k):
            raise AssertionError(f"final frozen policy replay mismatch for {k}: {replay.get(k)} != {saved_final.get(k)}")
    if not _same_optional_gaze(replay.get("next_gaze_deg"), saved_final.get("next_gaze_deg")):
        raise AssertionError("final frozen policy replay mismatch for next_gaze_deg")
    if replay.get("stop") is not True or replay.get("reason") != "no_frontier":
        raise AssertionError("replayed parent final decision is not the declared no_frontier stop")

    frontier = frozen_frontier.extract_frontier(sm.xyz_h, gazes[-1][0], gazes[-1][1], last["calibration"])
    fstate = frozen_frontier.classify_frontier_state(frontier, sm.xyz_h, history)
    if int(len(frontier["strength"])) != int(replay["frontier_count"]):
        raise AssertionError("frontier extraction count does not reproduce saved final decision")
    for a, b, name in (
        (fstate["open_count"], replay["frontier_open_count"], "open"),
        (fstate["map_resolved_count"], replay["frontier_map_resolved_count"], "map_resolved"),
        (fstate["boundary_resolved_count"], replay["frontier_boundary_resolved_count"], "boundary_resolved"),
    ):
        if int(a) != int(b):
            raise AssertionError(f"frontier-state replay mismatch for {name}: {a} != {b}")

    relation = _frontier_relation(chart, support, audit, refined, frontier, fstate, gazes)
    return {
        "saved_final_decision": saved_final,
        "replayed_final_decision_summary": {k: replay.get(k) for k in exact_keys + ("next_gaze_deg",)},
        "exact_replay": True,
        "relation": relation,
    }

def _write_visual(path: Path, support: np.ndarray, audit, refined: np.ndarray) -> None:
    h, w = support.shape
    im = np.full((h, w, 3), 245, np.uint8)
    im[support] = (150, 150, 150)
    im[audit.state_code == boundary.STATE_CODE["PHYSICAL_DEPTH_BREAK"]] = (70, 125, 220)
    im[audit.state_code == boundary.STATE_CODE["AMBIGUOUS"]] = (175, 105, 185)
    colours = {
        "NEVER_OBSERVED": (235, 80, 70),
        "OBSERVED_TARGET_NO_DEPTH": (245, 155, 55),
        "OBSERVED_TARGET_WITH_DEPTH": (235, 205, 55),
        "OBSERVED_NONTARGET_ONLY": (75, 190, 190),
        "MIXED_OBSERVATION": (220, 95, 170),
        "NO_RANGE_REFERENCE": (100, 100, 100),
    }
    for name, code in epi.STATE_CODE.items():
        im[refined == code] = colours[name]
    Image.fromarray(np.flipud(im)).resize(
        (max(1, w * 3), max(1, h * 3)), Image.Resampling.NEAREST
    ).save(path)


def execute(args) -> dict:
    args.parent = Path(args.parent).resolve()
    args.out = Path(args.out).resolve()
    if args.out.exists():
        raise FileExistsError("output must be new")
    args.out.mkdir(parents=True)
    check_kernel_equivalence()
    pm, target_id, objects = _validate_parent(args.parent)

    pinned_names = (
        "prediction_manifest.json", f"object_{target_id}_surface_map.npz", "scene_graph.json",
        "scene_cyclopean_footprints.npz", f"object_{target_id}_policy_trace.json",
    )
    pinned = {n: _sha256(args.parent / n) for n in pinned_names}

    object_sources: dict[int, Path] = {}
    object_hashes_before: dict[int, str] = {}
    for oid, obj in objects.items():
        src = _resolve(obj["source"], args.parent)
        if not src.is_file():
            raise FileNotFoundError(src)
        sm_i = load_map(src)
        if set(np.unique(sm_i.instance_id).tolist()) != {int(oid)}:
            raise AssertionError(f"scene object {oid} source lost id purity")
        object_sources[int(oid)] = src
        object_hashes_before[int(oid)] = _sha256(src)

    sm = load_map(args.parent / f"object_{target_id}_surface_map.npz")
    if set(np.unique(sm.instance_id).tolist()) != {target_id}:
        raise AssertionError("selected-object map lost id purity")

    profile = str(pm.get("profile", "full"))
    chart, footprint_cells, footprint_deg = topo1a.build_chart(sm.xyz_h, profile)
    if abs(float(chart.grid_deg) - public.GRID_DEG) > 1e-12:
        raise AssertionError("selected-object cyclopean grid changed from established 0.1 degree scale")

    raw, support, target_range = topo1a.rasterize_target(sm.xyz_h, chart, footprint_cells)
    evidence = topo1a.empty_evidence(chart)
    observations = []
    cases = _all_cases(args.parent, pm)
    observation_hashes_before = _case_hashes(cases)
    for step, case in cases:
        ob = _saved_observation(step, case)
        observations.append(ob)
        topo1a.add_observation(
            evidence, chart, ob["xyz_h"], ob["instance_id"], ob["valid"], target_id
        )

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
    refined, cell_ev = _refine_unobserved(chart, audit, observations, target_id)
    arcs = _refined_arcs(chart, audit, refined, cell_ev)
    visited_gazes = [tuple(map(float, g)) for g in pm.get("selected_object_fixation_gazes_deg", [])]
    if len(visited_gazes) != len(observations):
        raise AssertionError("selected-object gaze/history length mismatch")
    if visited_gazes:
        gy = np.asarray([g[0] for g in visited_gazes], float)
        gp = np.asarray([g[1] for g in visited_gazes], float)
        gaze_envelope = {
            "yaw_min_deg": float(np.min(gy)), "yaw_max_deg": float(np.max(gy)),
            "pitch_min_deg": float(np.min(gp)), "pitch_max_deg": float(np.max(gp)),
        }
        for r in arcs:
            cy = float(r["centroid_yaw_deg"]); cp = float(r["centroid_pitch_deg"])
            r["centroid_inside_visited_gaze_envelope"] = bool(
                gaze_envelope["yaw_min_deg"] <= cy <= gaze_envelope["yaw_max_deg"]
                and gaze_envelope["pitch_min_deg"] <= cp <= gaze_envelope["pitch_max_deg"]
            )
            r["centroid_nearest_visited_gaze_l2_deg"] = float(np.min(np.hypot(gy-cy, gp-cp)))
    else:
        gaze_envelope = {"yaw_min_deg": None, "yaw_max_deg": None, "pitch_min_deg": None, "pitch_max_deg": None}

    counts = {name: int((refined == code).sum()) for name, code in epi.STATE_CODE.items()}
    exterior = {name: 0 for name in epi.STATE_CODE}
    internal = {name: 0 for name in epi.STATE_CODE}
    for r in arcs:
        (exterior if r["component_kind"] == "EXTERIOR" else internal)[r["state"]] += int(r["cell_count"])

    base_counts = {
        name: int((audit.state_code == code).sum()) for name, code in boundary.STATE_CODE.items()
    }
    ext_components = [c for c in audit.components if c["kind"] == "EXTERIOR"]
    object_state = progress.object_status(exterior, counts)
    disposition = progress.scene_disposition()
    trace_payload = json.loads((args.parent / f"object_{target_id}_policy_trace.json").read_text())
    trace = trace_payload.get("trace", [])
    final_policy_decision = trace[-1] if trace else None
    policy_stop = _reconstruct_final_policy_stop(
        pm, sm, observations, target_id, chart, support, audit, refined, final_policy_decision
    )
    stop_interpretation = progress.stop_interpretation(exterior, counts, final_policy_decision)

    report_name = f"object_{target_id}_epistemic_stop_report.json"
    visual_name = f"object_{target_id}_epistemic_stop_shoreline.png"
    report = {
        "seed": int(pm["seed"]),
        "profile": profile,
        "object_id": int(target_id),
        "parent_termination_reason": pm.get("termination_reason"),
        "parent_scientific_stop_reached": pm.get("scientific_stop_reached"),
        "parent_final_policy_decision": final_policy_decision,
        "policy_stop_reconstruction": policy_stop,
        "observation_count": len(observations),
        "observation_steps": [int(o["step"]) for o in observations],
        "visited_gaze_envelope_deg": gaze_envelope,
        "chart": {
            "yaw0_deg": chart.yaw0_deg, "pitch0_deg": chart.pitch0_deg,
            "grid_deg": chart.grid_deg, "width": chart.width, "height": chart.height,
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
        "refined_unobserved_cells_by_state": counts,
        "exterior_refined_cells_by_state": exterior,
        "internal_refined_cells_by_state": internal,
        "components": audit.components,
        "refined_arcs": arcs,
        "object_status": object_state,
        "stop_interpretation": stop_interpretation,
        "scene_disposition": disposition,
        "next_stage": public.NEXT_STAGE,
    }
    json_write(args.out / report_name, report)
    _write_visual(args.out / visual_name, support, audit, refined)

    after = {n: _sha256(args.parent / n) for n in pinned_names}
    if after != pinned:
        raise AssertionError("MultiObject-3c parent changed during read-only audit")
    for oid, src in object_sources.items():
        if _sha256(src) != object_hashes_before[oid]:
            raise AssertionError(f"scene object {oid} changed during selected-object audit")
    if _case_hashes(cases) != observation_hashes_before:
        raise AssertionError("saved selected-object observations changed during read-only audit")

    manifest = {
        "schema": public.SPEC_ID,
        "public_spec_sha256": public.public_digest(),
        "parent_spec": public.PARENT_SPEC_ID,
        "parent_record": str(args.parent),
        "parent_hashes": pinned,
        "scene_object_sources": {str(k): str(v) for k, v in object_sources.items()},
        "scene_object_sha256_before": {str(k): v for k, v in object_hashes_before.items()},
        "scene_object_sha256_after": {str(k): _sha256(v) for k, v in object_sources.items()},
        "observation_input_hashes": observation_hashes_before,
        "seed": int(pm["seed"]),
        "profile": profile,
        "fixture": public.FIXTURE,
        "fixed_head": True,
        "static_scene": True,
        "truth_opened": False,
        "selected_object_id": int(target_id),
        "preexisting_object_ids": [int(x) for x in pm.get("preexisting_object_ids", [])],
        "acquisitions_added": 0,
        "growth_iterations_added": 0,
        "watchdog_changed": False,
        "parent_files_modified": False,
        "scene_objects_read_only": True,
        "selected_object_read_only": True,
        "selected_object_map_pure": True,
        "parent_termination_reason": pm.get("termination_reason"),
        "parent_scientific_stop_reached": pm.get("scientific_stop_reached"),
        "final_policy_stop_replayed_exactly": True,
        "observation_count": len(observations),
        "summary": {
            "shoreline_cells": report["shoreline_cells"],
            "max_exterior_border_distance_cells": report["max_exterior_border_distance_cells"],
            "base_shoreline_cells_by_state": base_counts,
            "refined_unobserved_cells_by_state": counts,
            "exterior_refined_cells_by_state": exterior,
            "internal_refined_cells_by_state": internal,
            "object_status": object_state,
            "stop_interpretation": stop_interpretation,
            "final_open_frontier_to_cyclopean_cell_counts": policy_stop["relation"]["frontier_state_to_cyclopean_cell_counts"]["OPEN"],
            "final_open_targets_inside_visited_gaze_envelope": policy_stop["relation"]["open_targets_inside_visited_gaze_envelope"],
            "final_open_targets_outside_visited_gaze_envelope": policy_stop["relation"]["open_targets_outside_visited_gaze_envelope"],
            "scene_disposition": disposition,
        },
        "report": report_name,
        "visual": visual_name,
        "automatic_object_discovery": False,
        "automatic_scene_scheduler": False,
        "quality_gate_used": False,
        "next_stage": public.NEXT_STAGE,
        "structural_fails": [],
    }
    json_write(args.out / "prediction_manifest.json", manifest)
    print("[multiobject3d-audit] MULTIOBJECT3D_COMPLETE " + json.dumps({
        "selected_object_id": int(target_id),
        "object_status": object_state,
        "stop_interpretation": stop_interpretation,
        "scene_disposition": disposition,
        "shoreline_cells": report["shoreline_cells"],
        "exterior_never_observed": exterior["NEVER_OBSERVED"],
        "observed_target_no_depth": counts["OBSERVED_TARGET_NO_DEPTH"],
        "max_exterior_border_distance_cells": report["max_exterior_border_distance_cells"],
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
