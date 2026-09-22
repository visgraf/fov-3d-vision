"""Read-only next-object selection from saved MultiObject scene evidence."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

import multiobject1c_audit as parent_audit
import multiobject2a_public as public
from multiobject2a_select import accumulate_candidate_support, select_next_object
from fsg_geometry import json_write


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _resolve(path_like: str, base: Path) -> Path:
    p = Path(path_like)
    return p if p.is_absolute() else (base / p).resolve()


def _validate_parent(parent: Path) -> dict:
    m = json.loads((parent / "prediction_manifest.json").read_text())
    if m.get("schema") != public.PARENT_SPEC_ID:
        raise AssertionError("MultiObject-2a requires a completed MultiObject-1c parent")
    if int(m.get("seed", -1)) != public.SEED or m.get("truth_opened") is not False:
        raise AssertionError("wrong seed or truth integrity broken")
    if int(m.get("acquisitions_added", -1)) != 0 or int(m.get("growth_iterations_added", -1)) != 0:
        raise AssertionError("MultiObject-1c parent was not read-only")
    if m.get("summary", {}).get("scene_disposition") != "MOVE_TO_NEXT_OBJECT":
        raise AssertionError("parent did not release scene progress")
    if not m.get("object_1_read_only") or not m.get("object_2_read_only") or not m.get("object_2_map_pure"):
        raise AssertionError("parent object integrity contract broken")
    return m


def _scene_history_parent(parent: Path, pm: dict) -> tuple[Path, dict]:
    scene_parent = _resolve(pm["parent_record"], parent)
    sm = json.loads((scene_parent / "prediction_manifest.json").read_text())
    if sm.get("schema") != "MultiObject1b2-resume-object143-growth-v2":
        raise AssertionError("MultiObject-1c parent_record is not the completed MultiObject-1b2 scene history")
    if sm.get("truth_opened") is not False or sm.get("object_ids") != list(public.INSTANTIATED_OBJECT_IDS):
        raise AssertionError("scene-history parent has unexpected truth/object ids")
    return scene_parent, sm


def _case_hashes(cases: list[tuple[int, Path]]) -> dict[str, dict[str, str]]:
    return {
        f"fix_{step:02d}": {
            "calibration.json": _sha256(case / "calibration.json"),
            "observation.npz": _sha256(case / "observation.npz"),
        }
        for step, case in cases
    }


def execute(args) -> dict:
    parent = Path(args.parent).resolve()
    out = Path(args.out).resolve()
    if out.exists():
        raise FileExistsError("output must be new")
    out.mkdir(parents=True)

    pm = _validate_parent(parent)
    scene_parent, scene_manifest = _scene_history_parent(parent, pm)

    parent_files = ["prediction_manifest.json", "object_143_epistemic_report.json", "object_143_epistemic_shoreline.png"]
    parent_hashes_before = {n: _sha256(parent / n) for n in parent_files}
    scene_files = ["prediction_manifest.json", "scene_graph.json", "object_143_surface_map.npz"]
    scene_hashes_before = {n: _sha256(scene_parent / n) for n in scene_files}

    cases = parent_audit._all_cases(scene_parent, scene_manifest)
    observation_hashes_before = _case_hashes(cases)
    observations = []
    for step, case in cases:
        ob = parent_audit._saved_observation(step, case)
        observations.append({
            "step": int(step),
            "instance_id": np.asarray(ob["instance_id"]).copy(),
            "valid": np.asarray(ob["valid"], bool).copy(),
        })

    candidates = accumulate_candidate_support(observations, public.INSTANTIATED_OBJECT_IDS)
    selection = select_next_object(candidates)
    report = {
        "schema": public.SPEC_ID,
        "instantiated_object_ids": list(public.INSTANTIATED_OBJECT_IDS),
        "evidence_scope_global_steps": [int(step) for step, _ in cases],
        "observation_count": len(cases),
        "candidate_rule": public.PUBLIC_SPEC["candidate_rule"],
        "selection_rule": public.PUBLIC_SPEC["selection_rule"],
        "candidates": candidates,
        **selection,
        "new_object_instantiated": False,
        "next_stage": public.NEXT_STAGE,
    }
    json_write(out / "next_object_selection.json", report)

    # Read-only integrity after all evidence has been consumed.
    if {n: _sha256(parent / n) for n in parent_files} != parent_hashes_before:
        raise AssertionError("MultiObject-1c parent changed during selection")
    if {n: _sha256(scene_parent / n) for n in scene_files} != scene_hashes_before:
        raise AssertionError("scene-history parent changed during selection")
    if _case_hashes(cases) != observation_hashes_before:
        raise AssertionError("saved scene observations changed during selection")

    manifest = {
        "schema": public.SPEC_ID,
        "public_spec_sha256": public.public_digest(),
        "parent_spec": public.PARENT_SPEC_ID,
        "parent_record": str(parent),
        "scene_history_record": str(scene_parent),
        "seed": public.SEED,
        "profile": scene_manifest.get("profile", "full"),
        "fixture": public.FIXTURE,
        "fixed_head": True,
        "static_scene": True,
        "truth_opened": False,
        "instantiated_object_ids": list(public.INSTANTIATED_OBJECT_IDS),
        "candidate_object_ids": [int(r["object_id"]) for r in candidates],
        "selected_object_id": selection["selected_object_id"],
        "selection_status": selection["selection_status"],
        "selected_valid_depth_samples": selection["selected_valid_depth_samples"],
        "selection_rule": public.PUBLIC_SPEC["selection_rule"],
        "observation_count": len(cases),
        "observation_steps": [int(step) for step, _ in cases],
        "acquisitions_added": 0,
        "fusion_iterations_added": 0,
        "growth_iterations_added": 0,
        "new_object_instantiated": False,
        "objects_141_143_read_only": True,
        "automatic_candidate_selection": True,
        "semantic_ranking_used": False,
        "quality_gate_used": False,
        "parent_hashes": parent_hashes_before,
        "scene_history_hashes": scene_hashes_before,
        "observation_hashes": observation_hashes_before,
        "selection_report": "next_object_selection.json",
        "next_stage": public.NEXT_STAGE,
        "structural_fails": [],
    }
    json_write(out / "prediction_manifest.json", manifest)
    print("[multiobject2a-run] MULTIOBJECT2A_COMPLETE " + json.dumps({
        "candidate_object_ids": manifest["candidate_object_ids"],
        "selected_object_id": manifest["selected_object_id"],
        "selected_valid_depth_samples": manifest["selected_valid_depth_samples"],
        "next_stage": manifest["next_stage"],
    }, sort_keys=True))
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--parent", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    execute(args)


if __name__ == "__main__":
    main()
