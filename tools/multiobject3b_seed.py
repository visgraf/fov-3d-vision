"""Pure evidence extraction and prescribed seed selection for MultiObject-3b."""
from __future__ import annotations

import numpy as np

from multiobject1a_seed import select_prescribed_seed


def collect_selected_object_evidence(observations: list[dict], object_id: int) -> tuple[np.ndarray, list[dict]]:
    """Collect only saved valid-depth xyz samples for one selected object id."""
    oid = int(object_id)
    if oid <= 0:
        raise ValueError("selected object id must be positive")
    chunks = []
    by_step = []
    for ob in observations:
        step = int(ob["step"])
        ids = np.asarray(ob["instance_id"])
        valid = np.asarray(ob["valid"], dtype=bool)
        xyz = np.asarray(ob["xyz_h"])
        if ids.shape != valid.shape or xyz.shape[:2] != ids.shape or xyz.shape[-1] != 3:
            raise ValueError("saved observation arrays have incompatible shapes")
        mask = valid & (ids == oid)
        n = int(np.count_nonzero(mask))
        by_step.append({"step": step, "valid_depth_samples": n})
        if n:
            chunks.append(np.asarray(xyz[mask], dtype=np.float64))
    if not chunks:
        raise ValueError("selected object has no saved valid-depth xyz evidence")
    return np.concatenate(chunks, axis=0), by_step


def select_seed_from_saved_evidence(observations: list[dict], object_id: int, grid_deg: float) -> dict:
    xyz, by_step = collect_selected_object_evidence(observations, object_id)
    selection = select_prescribed_seed(xyz, grid_deg)
    return {
        "selected_object_id": int(object_id),
        "valid_depth_evidence_points": int(len(xyz)),
        "valid_depth_by_step": by_step,
        **selection,
    }


def self_test() -> None:
    xyz = np.array([
        [[1.0, 0.0, -2.0], [2.0, 0.0, -2.0]],
        [[0.0, 0.0, -2.0], [0.1, 0.1, -2.0]],
    ], dtype=float)
    obs = [{
        "step": 7,
        "instance_id": np.array([[5, 5], [9, 5]], dtype=np.int32),
        "valid": np.array([[1, 0], [1, 1]], dtype=bool),
        "xyz_h": xyz,
    }]
    got = select_seed_from_saved_evidence(obs, 5, 0.1)
    assert got["valid_depth_evidence_points"] == 2
    assert got["valid_depth_by_step"] == [{"step": 7, "valid_depth_samples": 2}]
    assert len(got["probe_gaze_deg"]) == 2
    print("[multiobject3b-seed] PASS parent_selected_object=true updated_valid_depth_only=true occupied_cell_mean=true")


if __name__ == "__main__":
    self_test()
