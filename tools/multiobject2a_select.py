"""Pure evidence aggregation and deterministic next-object selection for MultiObject-2a."""
from __future__ import annotations
from collections import defaultdict

import numpy as np


def accumulate_candidate_support(observations: list[dict], instantiated_ids) -> list[dict]:
    """Aggregate valid-depth support by uninstantiated positive instance id.

    `observations` contain saved prediction-side arrays only.  Visibility without
    valid stereo depth is recorded diagnostically but never contributes to the
    selection support.
    """
    instantiated = {int(x) for x in instantiated_ids}
    valid_total: dict[int, int] = defaultdict(int)
    visible_total: dict[int, int] = defaultdict(int)
    valid_by_step: dict[int, dict[int, int]] = defaultdict(dict)
    visible_by_step: dict[int, dict[int, int]] = defaultdict(dict)

    for ob in observations:
        step = int(ob["step"])
        ids = np.asarray(ob["instance_id"])
        valid = np.asarray(ob["valid"], dtype=bool)
        if ids.shape != valid.shape:
            raise ValueError("instance_id/valid shape mismatch")
        for oid in np.unique(ids):
            oid = int(oid)
            if oid <= 0 or oid in instantiated:
                continue
            visible_n = int(np.count_nonzero(ids == oid))
            valid_n = int(np.count_nonzero((ids == oid) & valid))
            if visible_n:
                visible_total[oid] += visible_n
                visible_by_step[oid][step] = visible_n
            if valid_n:
                valid_total[oid] += valid_n
                valid_by_step[oid][step] = valid_n

    candidate_ids = sorted(valid_total)
    rows = []
    for oid in candidate_ids:
        rows.append({
            "object_id": int(oid),
            "valid_depth_samples": int(valid_total[oid]),
            "visible_samples": int(visible_total.get(oid, 0)),
            "valid_depth_by_step": {str(k): int(v) for k, v in sorted(valid_by_step[oid].items())},
            "visible_by_step": {str(k): int(v) for k, v in sorted(visible_by_step[oid].items())},
        })
    rows.sort(key=lambda r: (-int(r["valid_depth_samples"]), int(r["object_id"])))
    return rows


def select_next_object(candidate_rows: list[dict]) -> dict:
    if not candidate_rows:
        return {
            "selection_status": "NO_UNINSTANTIATED_VALID_DEPTH_EVIDENCE",
            "selected_object_id": None,
            "selected_valid_depth_samples": 0,
        }
    ordered = sorted(
        candidate_rows,
        key=lambda r: (-int(r["valid_depth_samples"]), int(r["object_id"])),
    )
    winner = ordered[0]
    return {
        "selection_status": "NEXT_OBJECT_SELECTED",
        "selected_object_id": int(winner["object_id"]),
        "selected_valid_depth_samples": int(winner["valid_depth_samples"]),
        "tie_break": "largest_valid_depth_support_then_smaller_object_id",
    }


def self_test() -> None:
    obs = [
        {"step": 1, "instance_id": np.array([[7, 7, 8], [2, 8, 9]]), "valid": np.array([[1, 0, 1], [1, 1, 0]], bool)},
        {"step": 2, "instance_id": np.array([[8, 9, 9], [7, 8, 8]]), "valid": np.array([[1, 1, 0], [1, 0, 1]], bool)},
    ]
    rows = accumulate_candidate_support(obs, instantiated_ids=(2, 7))
    assert [r["object_id"] for r in rows] == [8, 9]
    assert rows[0]["valid_depth_samples"] == 4
    sel = select_next_object(rows)
    assert sel["selected_object_id"] == 8
    tie = select_next_object([
        {"object_id": 5, "valid_depth_samples": 10},
        {"object_id": 4, "valid_depth_samples": 10},
    ])
    assert tie["selected_object_id"] == 4
    print("[multiobject2a-select] PASS valid_depth_only=true deterministic_argmax=true no_threshold=true")


if __name__ == "__main__":
    self_test()
