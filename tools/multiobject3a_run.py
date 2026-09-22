"""Read-only next-object selection from the complete updated MultiObject scene history."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

import multiobject1c_audit as old_history
import multiobject2d_audit as new_history
import multiobject3a_public as public
from multiobject3a_select import accumulate_candidate_support, select_next_object
from fsg_geometry import json_write
from fsg3_surface_map import load_map


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _resolve(path_like: str, base: Path) -> Path:
    p = Path(path_like)
    return p.resolve() if p.is_absolute() else (base / p).resolve()


def _validate_parent(parent: Path) -> tuple[dict, Path, dict, dict[int, dict]]:
    m = json.loads((parent / "prediction_manifest.json").read_text())
    if m.get("schema") != public.PARENT_SPEC_ID:
        raise AssertionError("MultiObject-3a requires a completed MultiObject-2d parent")
    if int(m.get("seed", -1)) != public.SEED or m.get("truth_opened") is not False:
        raise AssertionError("wrong seed or truth integrity broken")
    if int(m.get("acquisitions_added", -1)) != 0 or int(m.get("growth_iterations_added", -1)) != 0:
        raise AssertionError("MultiObject-2d parent was not read-only")
    if m.get("summary", {}).get("scene_disposition") != "MOVE_TO_NEXT_OBJECT":
        raise AssertionError("MultiObject-2d did not release scene progress")
    if not m.get("scene_objects_read_only") or not m.get("selected_object_read_only"):
        raise AssertionError("MultiObject-2d object integrity contract broken")

    growth = _resolve(m["parent_record"], parent)
    gm = json.loads((growth / "prediction_manifest.json").read_text())
    if gm.get("schema") != "MultiObject2c-grow-selected-object-v1":
        raise AssertionError("MultiObject-2d parent_record is not completed MultiObject-2c")
    if gm.get("truth_opened") is not False or not gm.get("preexisting_objects_read_only"):
        raise AssertionError("MultiObject-2c scene integrity broken")
    graph = json.loads((growth / "scene_graph.json").read_text())
    objects = {int(o["object_id"]): o for o in graph.get("objects", [])}
    if len(objects) < 3:
        raise AssertionError("updated scene does not contain at least three instantiated objects")
    if int(gm.get("selected_object_id", -1)) not in objects:
        raise AssertionError("MultiObject-2c selected object missing from scene graph")
    return m, growth, gm, objects


def _old_scene_history(growth: Path, gm: dict) -> tuple[Path, dict]:
    seed_parent = _resolve(gm["parent_record"], growth)
    bm = json.loads((seed_parent / "prediction_manifest.json").read_text())
    if bm.get("schema") != "MultiObject2b-seed-selected-object-v1":
        raise AssertionError("MultiObject-2c parent is not completed MultiObject-2b")
    scene = _resolve(bm["scene_history_record"], seed_parent)
    sm = json.loads((scene / "prediction_manifest.json").read_text())
    if sm.get("schema") != "MultiObject1b2-resume-object143-growth-v2":
        raise AssertionError("MultiObject-2b scene history is not completed MultiObject-1b2")
    if sm.get("truth_opened") is not False:
        raise AssertionError("old scene history opened truth")
    return scene, sm


def _case_hashes(cases: list[tuple[int, Path]]) -> dict[str, dict[str, str]]:
    return {
        f"fix_{step:02d}": {
            "calibration.json": _sha256(case / "calibration.json"),
            "observation.npz": _sha256(case / "observation.npz"),
        }
        for step, case in cases
    }


def _object_sources(growth: Path, objects: dict[int, dict]) -> tuple[dict[int, Path], dict[int, str]]:
    paths: dict[int, Path] = {}
    hashes: dict[int, str] = {}
    for oid, obj in objects.items():
        src = _resolve(obj["source"], growth)
        if not src.is_file():
            raise FileNotFoundError(src)
        sm = load_map(src)
        if set(np.unique(sm.instance_id).tolist()) != {int(oid)}:
            raise AssertionError(f"scene object {oid} lost instance-id purity")
        paths[int(oid)] = src
        hashes[int(oid)] = _sha256(src)
    return paths, hashes


def execute(args) -> dict:
    parent = Path(args.parent).resolve()
    out = Path(args.out).resolve()
    if out.exists():
        raise FileExistsError("output must be new")
    out.mkdir(parents=True)

    pm, growth, gm, objects = _validate_parent(parent)
    instantiated_ids = tuple(sorted(objects))
    old_scene, old_manifest = _old_scene_history(growth, gm)

    parent_files = ["prediction_manifest.json", pm["report"], pm["visual"]]
    parent_hashes_before = {n: _sha256(parent / n) for n in parent_files}
    growth_files = ["prediction_manifest.json", "scene_graph.json", f"object_{int(gm['selected_object_id'])}_surface_map.npz"]
    growth_hashes_before = {n: _sha256(growth / n) for n in growth_files}
    object_paths, object_hashes_before = _object_sources(growth, objects)

    old_cases = old_history._all_cases(old_scene, old_manifest)
    new_cases = new_history._all_cases(growth, gm)
    all_cases = sorted(old_cases + new_cases, key=lambda x: int(x[0]))
    steps = [int(s) for s, _ in all_cases]
    if len(set(steps)) != len(steps):
        raise AssertionError("updated scene history contains duplicate global steps")
    if steps != list(range(min(steps), max(steps) + 1)):
        raise AssertionError("updated scene history is not globally contiguous")

    observation_hashes_before = _case_hashes(all_cases)
    observations = []
    for step, case in old_cases:
        ob = old_history._saved_observation(step, case)
        observations.append({
            "step": int(step),
            "instance_id": np.asarray(ob["instance_id"]).copy(),
            "valid": np.asarray(ob["valid"], bool).copy(),
        })
    for step, case in new_cases:
        ob = new_history._saved_observation(step, case)
        observations.append({
            "step": int(step),
            "instance_id": np.asarray(ob["instance_id"]).copy(),
            "valid": np.asarray(ob["valid"], bool).copy(),
        })
    observations.sort(key=lambda ob: int(ob["step"]))

    candidates = accumulate_candidate_support(observations, instantiated_ids)
    selection = select_next_object(candidates)
    report = {
        "schema": public.SPEC_ID,
        "instantiated_object_ids": list(instantiated_ids),
        "evidence_scope_global_steps": steps,
        "observation_count": len(observations),
        "candidate_rule": public.PUBLIC_SPEC["candidate_rule"],
        "selection_rule": public.PUBLIC_SPEC["selection_rule"],
        "candidates": candidates,
        **selection,
        "new_object_instantiated": False,
        "retained_existing_object_states": {
            str(int(pm["selected_object_id"])): pm.get("summary", {}).get("object_status")
        },
        "next_stage": public.NEXT_STAGE,
    }
    json_write(out / "next_object_selection.json", report)

    if {n: _sha256(parent / n) for n in parent_files} != parent_hashes_before:
        raise AssertionError("MultiObject-2d parent changed during selection")
    if {n: _sha256(growth / n) for n in growth_files} != growth_hashes_before:
        raise AssertionError("MultiObject-2c scene record changed during selection")
    if {oid: _sha256(path) for oid, path in object_paths.items()} != object_hashes_before:
        raise AssertionError("instantiated scene-object geometry changed during selection")
    if _case_hashes(all_cases) != observation_hashes_before:
        raise AssertionError("saved updated scene observations changed during selection")

    manifest = {
        "schema": public.SPEC_ID,
        "public_spec_sha256": public.public_digest(),
        "parent_spec": public.PARENT_SPEC_ID,
        "parent_record": str(parent),
        "scene_growth_record": str(growth),
        "old_scene_history_record": str(old_scene),
        "seed": public.SEED,
        "profile": gm.get("profile", "full"),
        "fixture": public.FIXTURE,
        "fixed_head": True,
        "static_scene": True,
        "truth_opened": False,
        "instantiated_object_ids": list(instantiated_ids),
        "candidate_object_ids": [int(r["object_id"]) for r in candidates],
        "selected_object_id": selection["selected_object_id"],
        "selection_status": selection["selection_status"],
        "selected_valid_depth_samples": selection["selected_valid_depth_samples"],
        "selection_rule": public.PUBLIC_SPEC["selection_rule"],
        "observation_count": len(observations),
        "observation_steps": steps,
        "acquisitions_added": 0,
        "fusion_iterations_added": 0,
        "growth_iterations_added": 0,
        "new_object_instantiated": False,
        "scene_objects_read_only": True,
        "automatic_candidate_selection": True,
        "semantic_ranking_used": False,
        "quality_gate_used": False,
        "revisit_scheduler_used": False,
        "parent_hashes": parent_hashes_before,
        "scene_growth_hashes": growth_hashes_before,
        "scene_object_sha256": {str(k): v for k, v in object_hashes_before.items()},
        "observation_hashes": observation_hashes_before,
        "selection_report": "next_object_selection.json",
        "next_stage": public.NEXT_STAGE,
        "structural_fails": [],
    }
    json_write(out / "prediction_manifest.json", manifest)
    print("[multiobject3a-run] MULTIOBJECT3A_COMPLETE " + json.dumps({
        "instantiated_object_ids": manifest["instantiated_object_ids"],
        "candidate_object_ids": manifest["candidate_object_ids"],
        "selected_object_id": manifest["selected_object_id"],
        "selected_valid_depth_samples": manifest["selected_valid_depth_samples"],
        "observation_count": manifest["observation_count"],
        "next_stage": manifest["next_stage"],
    }, sort_keys=True))
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--parent", required=True)
    ap.add_argument("--out", required=True)
    execute(ap.parse_args())


if __name__ == "__main__":
    main()
