"""Read-only cyclopean epistemic audit of the MultiObject-2c selected object.

This step adds no view and runs no controller.  It rebuilds selected-object
support on the inherited 0.1-degree cyclopean scale, classifies the shoreline
with the existing Cyclopean-1b boundary semantics, then refines only base
UNOBSERVED cells with the existing Cyclopean-1d observation-versus-measurement
semantics.
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
from fsg_stereo import rectification
from fsg_stereo_supported import compute_once, check_kernel_equivalence
from fsg3_surface_map import load_map
from fsg_geometry import json_write

import multiobject2d_public as public
import multiobject2d_progress as progress


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
        raise AssertionError("MultiObject-2d requires a completed MultiObject-2c parent")
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
    rec, _meta, _state = compute_once(c, obs)
    r = rectification(c)
    return {
        "step": int(step),
        "label": f"fix_{step:02d}",
        "case": str(case),
        "calibration": c,
        "rectification": r,
        "instance_id": np.asarray(rec["instance_id"]).copy(),
        "valid": np.asarray(rec["valid"], bool).copy(),
        "raw_support_L": np.asarray(rec["raw_support_L"], bool).copy(),
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

    report_name = f"object_{target_id}_epistemic_report.json"
    visual_name = f"object_{target_id}_epistemic_shoreline.png"
    report = {
        "seed": int(pm["seed"]),
        "profile": profile,
        "object_id": int(target_id),
        "parent_termination_reason": pm.get("termination_reason"),
        "parent_scientific_stop_reached": pm.get("scientific_stop_reached"),
        "parent_final_policy_decision": final_policy_decision,
        "observation_count": len(observations),
        "observation_steps": [int(o["step"]) for o in observations],
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
        "scene_disposition": disposition,
        "next_stage": public.NEXT_STAGE,
    }
    json_write(args.out / report_name, report)
    _write_visual(args.out / visual_name, support, audit, refined)

    after = {n: _sha256(args.parent / n) for n in pinned_names}
    if after != pinned:
        raise AssertionError("MultiObject-2c parent changed during read-only audit")
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
        "observation_count": len(observations),
        "summary": {
            "shoreline_cells": report["shoreline_cells"],
            "max_exterior_border_distance_cells": report["max_exterior_border_distance_cells"],
            "base_shoreline_cells_by_state": base_counts,
            "refined_unobserved_cells_by_state": counts,
            "exterior_refined_cells_by_state": exterior,
            "internal_refined_cells_by_state": internal,
            "object_status": object_state,
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
    print("[multiobject2d-audit] MULTIOBJECT2D_COMPLETE " + json.dumps({
        "selected_object_id": int(target_id),
        "object_status": object_state,
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
