"""Build the read-only FullScene-1 initial condition from the post-3h state."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

import multiobject1c_audit as history_143
import multiobject2d_audit as history_142
import multiobject3d_audit as history_145
import multiobject3a_select as selector
import multiobject3h_public as parent_public
import fullscene1a_public as public
from fsg3_surface_map import load_map
from fsg_geometry import json_write


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _resolve(path_like: str, base: Path) -> Path:
    p = Path(path_like)
    return p.resolve() if p.is_absolute() else (base / p).resolve()


def _manifest(record: Path, expected_schema: str | None = None) -> dict:
    p = record / "prediction_manifest.json"
    if not p.is_file():
        raise FileNotFoundError(p)
    m = json.loads(p.read_text())
    if expected_schema is not None and m.get("schema") != expected_schema:
        raise AssertionError(f"wrong schema at {record}: {m.get('schema')} != {expected_schema}")
    if m.get("truth_opened") is not False:
        raise AssertionError(f"truth integrity broken at {record}")
    if m.get("structural_fails") not in (None, []):
        raise AssertionError(f"structural failures present at {record}")
    return m


def _validate_parent(parent3h: Path) -> dict:
    m = _manifest(parent3h, public.PARENT_SPEC_ID)
    if m.get("public_spec_sha256") != parent_public.public_digest():
        raise AssertionError("MultiObject-3h public digest mismatch")
    if int(m.get("seed", -1)) != public.SEED:
        raise AssertionError("wrong seed")
    if int(m.get("added_fixations", -1)) != 1:
        raise AssertionError("MultiObject-3h must contain exactly its one bounded fixation")
    if int(m.get("subsequent_local_policy_decisions", -1)) != 1:
        raise AssertionError("MultiObject-3h must contain exactly one subsequent local decision")
    if m.get("subsequent_local_action_executed") is not False:
        raise AssertionError("MultiObject-3h deferred local action was already executed")
    if not m.get("scene_graph") or not m.get("scene_footprints"):
        raise AssertionError("MultiObject-3h current scene artifacts missing from manifest")
    return m


def _ancestry(parent3h: Path, m3h: dict) -> dict:
    parent3g = _resolve(m3h["parent_record"], parent3h)
    m3g = _manifest(parent3g, "MultiObject3g-one-returned-local-action-v1")

    parent3c = _resolve(m3g["scene_parent_record"], parent3g)
    m3c = _manifest(parent3c, "MultiObject3c-grow-selected-object-v1")

    parent3b = _resolve(m3c["parent_record"], parent3c)
    m3b = _manifest(parent3b, "MultiObject3b-seed-selected-object-v1")

    parent3a = _resolve(m3b["parent_record"], parent3b)
    m3a = _manifest(parent3a, "MultiObject3a-next-object-selection-v1")

    growth142 = _resolve(m3a["scene_growth_record"], parent3a)
    m2c = _manifest(growth142, "MultiObject2c-grow-selected-object-v1")

    old_scene = _resolve(m3a["old_scene_history_record"], parent3a)
    m1b2 = _manifest(old_scene, "MultiObject1b2-resume-object143-growth-v2")

    parent3e = _resolve(m3g["execution_parent_record"], parent3g)
    m3e = _manifest(parent3e, "MultiObject3e-one-epistemic-handoff-v1")

    # Reach the completed object-143 epistemic audit for retained-state evidence.
    parent2b = _resolve(m2c["parent_record"], growth142)
    m2b = _manifest(parent2b, "MultiObject2b-seed-selected-object-v1")
    parent2a = _resolve(m2b["parent_record"], parent2b)
    m2a = _manifest(parent2a, "MultiObject2a-next-object-selection-v1")
    parent1c = _resolve(m2a["parent_record"], parent2a)
    m1c = _manifest(parent1c, "MultiObject1c-object143-epistemic-audit-v1")

    # Reach the completed object-142 epistemic audit through 3a's parent.
    parent2d = _resolve(m3a["parent_record"], parent3a)
    m2d = _manifest(parent2d, "MultiObject2d-selected-object-epistemic-audit-v1")

    return {
        "parent3g": (parent3g, m3g),
        "parent3c": (parent3c, m3c),
        "parent3b": (parent3b, m3b),
        "parent3a": (parent3a, m3a),
        "growth142": (growth142, m2c),
        "old_scene": (old_scene, m1b2),
        "parent3e": (parent3e, m3e),
        "parent1c": (parent1c, m1c),
        "parent2d": (parent2d, m2d),
    }


def _case_hashes(cases: list[tuple[int, Path]]) -> dict[str, dict[str, str]]:
    return {
        f"fix_{step:02d}": {
            "calibration.json": _sha256(case / "calibration.json"),
            "observation.npz": _sha256(case / "observation.npz"),
        }
        for step, case in cases
    }


def _history(parent3h: Path, m3h: dict, chain: dict):
    old_scene, m1b2 = chain["old_scene"]
    growth142, m2c = chain["growth142"]
    parent3c, m3c = chain["parent3c"]
    parent3e, m3e = chain["parent3e"]
    parent3g, m3g = chain["parent3g"]

    groups: list[tuple[str, list[tuple[int, Path]], object]] = []
    groups.append(("scene_history_143", history_143._all_cases(old_scene, m1b2), history_143._saved_observation))
    groups.append(("selected_object_142", history_142._all_cases(growth142, m2c), history_142._saved_observation))
    groups.append(("selected_object_145_base", history_145._all_cases(parent3c, m3c), history_145._saved_observation))

    handoff_step = int(m3e["global_step"])
    handoff_case = parent3e / "acquisition" / f"fix_{handoff_step:02d}"
    action80_step = int(m3g["global_step"])
    action80_case = parent3g / "acquisition" / f"fix_{action80_step:02d}"
    action81_step = int(m3h["global_step"])
    action81_case = parent3h / "acquisition" / f"fix_{action81_step:02d}"
    tail = [(handoff_step, handoff_case), (action80_step, action80_case), (action81_step, action81_case)]
    for step, case in tail:
        if not (case / "calibration.json").is_file() or not (case / "observation.npz").is_file():
            raise FileNotFoundError(f"missing FullScene tail observation {step}: {case}")
    groups.append(("handoff_and_post_handoff", tail, history_145._saved_observation))

    cases: list[tuple[int, Path]] = []
    observations = []
    group_steps = {}
    for name, rows, reader in groups:
        group_steps[name] = [int(step) for step, _ in rows]
        for step, case in rows:
            cases.append((int(step), case))
            ob = reader(int(step), case)
            observations.append({
                "step": int(step),
                "instance_id": np.asarray(ob["instance_id"]).copy(),
                "valid": np.asarray(ob["valid"], dtype=bool).copy(),
            })

    cases.sort(key=lambda x: int(x[0]))
    observations.sort(key=lambda x: int(x["step"]))
    steps = [int(s) for s, _ in cases]
    if len(set(steps)) != len(steps):
        raise AssertionError("FullScene-1a declared history contains duplicate global steps")
    expected_last = int(m3h["global_step"])
    expected = list(range(18, expected_last + 1))
    if steps != expected:
        raise AssertionError(f"FullScene-1a evidence scope is not contiguous 18..{expected_last}: {steps}")
    if [int(o["step"]) for o in observations] != steps:
        raise AssertionError("FullScene-1a observation ordering differs from case ordering")
    return cases, observations, group_steps


def _scene_inventory(parent3h: Path, m3h: dict, chain: dict):
    graph_path = parent3h / m3h["scene_graph"]
    graph = json.loads(graph_path.read_text())
    rows = graph.get("objects", [])
    by_id = {int(r["object_id"]): r for r in rows}
    if not by_id:
        raise AssertionError("current scene graph is empty")
    if len(by_id) != len(rows):
        raise AssertionError("current scene graph contains duplicate object ids")

    footprint_counts = m3h.get("scene_footprint_counts", {})
    object_paths: dict[int, Path] = {}
    object_hashes: dict[int, str] = {}
    inventory = []

    m3a = chain["parent3a"][1]
    m1c = chain["parent1c"][1]
    m2d = chain["parent2d"][1]
    target_id = int(m3h.get("selected_object_id", -1))

    known_epistemic = {}
    audit1c_path = chain["parent1c"][0] / m1c.get("report", "")
    if audit1c_path.is_file():
        audit1c = json.loads(audit1c_path.read_text())
        audit_oid = int(audit1c.get("object_id", -1))
        audit_status = audit1c.get("object_143_status")
        if audit_oid > 0 and audit_status:
            known_epistemic[audit_oid] = {
                "status": audit_status,
                "source_schema": m1c.get("schema"),
                "still_current_geometry": True,
            }
    # MultiObject-3a records the retained per-object epistemic states inside its
    # selection report, which is where its own comparator reads them; the manifest
    # carries only the pointer.  Read the report first and keep the manifest as a
    # fallback so either layout resolves.
    retained = m3a.get("retained_existing_object_states", {})
    if not retained:
        report3a_path = chain["parent3a"][0] / m3a.get("selection_report", "")
        if report3a_path.is_file():
            retained = json.loads(report3a_path.read_text()).get(
                "retained_existing_object_states", {}
            )
    for key, value in retained.items():
        try:
            oid = int(key)
        except (TypeError, ValueError):
            continue
        if value:
            known_epistemic[oid] = {"status": value, "source_schema": m2d.get("schema"), "still_current_geometry": True}

    for oid in sorted(by_id):
        row = by_id[oid]
        src = _resolve(row["source"], parent3h)
        if not src.is_file():
            raise FileNotFoundError(src)
        sm = load_map(src)
        if len(sm.instance_id) and set(np.unique(sm.instance_id).tolist()) != {oid}:
            raise AssertionError(f"scene object {oid} lost instance-id purity")
        object_paths[oid] = src
        object_hashes[oid] = _sha256(src)
        item = {
            "object_id": int(oid),
            "geometry": str(row.get("geometry", "SURFEL_MAP")),
            "point_count": int(len(sm.xyz_h)),
            "raw_footprint_cells": int(footprint_counts.get(str(oid), 0)),
            "persistent": True,
            "read_only_in_snapshot": True,
        }
        if oid in known_epistemic:
            item["prior_epistemic_status"] = known_epistemic[oid]
        if oid == target_id:
            item["current_local_control_status"] = m3h.get("subsequent_policy_status")
            item["latest_measurement_status"] = m3h.get("measurement_status")
            item["deferred_local_action_deg"] = m3h.get("subsequent_local_policy_decision", {}).get("next_gaze_deg")
            item["deferred_local_action_executed"] = False
        inventory.append(item)

    instantiated = tuple(sorted(by_id))
    if tuple(sorted(int(x) for x in m3h.get("preexisting_object_ids", []) + [target_id])) != instantiated:
        # The scene graph is authoritative, but this catches accidental ancestry drift.
        raise AssertionError("MultiObject-3h scene graph ids disagree with inherited object-id set")
    return graph_path, graph, instantiated, inventory, object_paths, object_hashes


def _positive_ids(observations: list[dict], require_valid: bool) -> list[int]:
    ids = set()
    for ob in observations:
        arr = np.asarray(ob["instance_id"])
        mask = np.asarray(ob["valid"], dtype=bool) if require_valid else np.ones(arr.shape, dtype=bool)
        for raw in np.unique(arr[mask]):
            oid = int(raw)
            if oid > 0:
                ids.add(oid)
    return sorted(ids)


def execute(args) -> dict:
    parent = Path(args.parent).resolve()
    out = Path(args.out).resolve()
    if out.exists():
        raise FileExistsError("output must be new")
    out.mkdir(parents=True)

    m3h = _validate_parent(parent)
    chain = _ancestry(parent, m3h)
    graph_path, graph, instantiated, inventory, object_paths, object_hashes_before = _scene_inventory(parent, m3h, chain)
    cases, observations, group_steps = _history(parent, m3h, chain)

    parent_files = [
        "prediction_manifest.json",
        m3h["productivity_report"],
        m3h["scene_graph"],
        m3h["scene_footprints"],
        m3h["active_object_map"],
    ]
    parent_hashes_before = {name: _sha256(parent / name) for name in parent_files}
    observation_hashes_before = _case_hashes(cases)

    observed_ids = _positive_ids(observations, require_valid=False)
    valid_depth_ids = _positive_ids(observations, require_valid=True)
    candidates = selector.accumulate_candidate_support(observations, instantiated)
    selection = selector.select_next_object(candidates)

    uninstantiated_observed = sorted(set(observed_ids) - set(instantiated))
    candidate_ids = [int(r["object_id"]) for r in candidates]
    if set(candidate_ids) != (set(valid_depth_ids) - set(instantiated)):
        raise AssertionError("candidate set no longer matches uninstantiated valid-depth evidence")

    next_stage = public.NEXT_STAGE_IF_SELECTED if selection["selection_status"] == "NEXT_OBJECT_SELECTED" else public.NEXT_STAGE_IF_NONE
    snapshot = {
        "schema": public.SPEC_ID,
        "snapshot_id": public.SNAPSHOT_ID,
        "seed": public.SEED,
        "fixed_head": True,
        "static_scene": True,
        "truth_opened": False,
        "last_global_step": int(m3h["global_step"]),
        "observation_count": int(len(observations)),
        "observation_steps": [int(s) for s, _ in cases],
        "history_groups": group_steps,
        "instantiated_object_ids": list(instantiated),
        "scene_object_count": int(len(instantiated)),
        "objects": inventory,
        "positive_observed_instance_ids": observed_ids,
        "valid_depth_instance_ids": valid_depth_ids,
        "uninstantiated_observed_instance_ids": uninstantiated_observed,
        "candidate_rule": public.PUBLIC_SPEC["candidate_rule"],
        "selection_rule": public.PUBLIC_SPEC["selection_rule"],
        "candidates": candidates,
        **selection,
        "deferred_local_action": {
            "object_id": int(m3h.get("selected_object_id", -1)),
            "next_gaze_deg": m3h.get("subsequent_local_policy_decision", {}).get("next_gaze_deg"),
            "policy_status": m3h.get("subsequent_policy_status"),
            "executed": False,
            "disposition": "DEFERRED_DURING_FULLSCENE_SNAPSHOT",
        },
        "automatic_scene_scheduler": False,
        "revisit_scheduler_used": False,
        "new_object_instantiated": False,
        "next_stage": next_stage,
    }
    json_write(out / "scene_state_snapshot.json", snapshot)

    # Verify every consumed source remained untouched.
    if {name: _sha256(parent / name) for name in parent_files} != parent_hashes_before:
        raise AssertionError("MultiObject-3h parent changed during FullScene-1a")
    if _case_hashes(cases) != observation_hashes_before:
        raise AssertionError("saved scene observations changed during FullScene-1a")
    if {oid: _sha256(path) for oid, path in object_paths.items()} != object_hashes_before:
        raise AssertionError("persistent scene-object geometry changed during FullScene-1a")

    manifest = {
        "schema": public.SPEC_ID,
        "public_spec_sha256": public.public_digest(),
        "parent_spec": public.PARENT_SPEC_ID,
        "parent_record": str(parent),
        "seed": public.SEED,
        "profile": m3h.get("profile", "full"),
        "fixture": public.FIXTURE,
        "fixed_head": True,
        "static_scene": True,
        "truth_opened": False,
        "snapshot_id": public.SNAPSHOT_ID,
        "fullscene_initial_condition": True,
        "last_global_step": int(m3h["global_step"]),
        "observation_count": int(len(observations)),
        "observation_steps": [int(s) for s, _ in cases],
        "history_groups": group_steps,
        "instantiated_object_ids": list(instantiated),
        "candidate_object_ids": candidate_ids,
        "selected_object_id": selection["selected_object_id"],
        "selection_status": selection["selection_status"],
        "selected_valid_depth_samples": selection["selected_valid_depth_samples"],
        "positive_observed_instance_ids": observed_ids,
        "valid_depth_instance_ids": valid_depth_ids,
        "uninstantiated_observed_instance_ids": uninstantiated_observed,
        "selection_source": public.SELECTION_SOURCE,
        "scene_graph_source": str(graph_path),
        "scene_objects_read_only": True,
        "parent_files_modified": False,
        "acquisitions_added": 0,
        "parent_fixations_rerendered": 0,
        "fusion_iterations_added": 0,
        "growth_iterations_added": 0,
        "epistemic_handoffs_added": 0,
        "deferred_local_action_executed": False,
        "new_object_instantiated": False,
        "automatic_object_discovery": False,
        "automatic_scene_scheduler": False,
        "revisit_scheduler_used": False,
        "semantic_ranking_used": False,
        "quality_gate_used": False,
        "new_threshold_added": False,
        "parent_hashes": parent_hashes_before,
        "observation_hashes": observation_hashes_before,
        "scene_object_sha256": {str(k): v for k, v in object_hashes_before.items()},
        "snapshot_report": "scene_state_snapshot.json",
        "next_stage": next_stage,
        "structural_fails": [],
    }
    json_write(out / "prediction_manifest.json", manifest)
    print("[fullscene1a-run] FULLSCENE1A_COMPLETE " + json.dumps({
        "snapshot_id": manifest["snapshot_id"],
        "instantiated_object_ids": manifest["instantiated_object_ids"],
        "positive_observed_instance_ids": manifest["positive_observed_instance_ids"],
        "candidate_object_ids": manifest["candidate_object_ids"],
        "selected_object_id": manifest["selected_object_id"],
        "selected_valid_depth_samples": manifest["selected_valid_depth_samples"],
        "observation_count": manifest["observation_count"],
        "last_global_step": manifest["last_global_step"],
        "next_stage": manifest["next_stage"],
    }, sort_keys=True))
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--parent", required=True, help="completed MultiObject-3h record")
    ap.add_argument("--out", required=True, help="new FullScene-1a output record")
    execute(ap.parse_args())


if __name__ == "__main__":
    main()
