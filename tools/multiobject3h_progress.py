"""Threshold-free descriptive outcome helpers for MultiObject-3h."""
from __future__ import annotations


def measurement_status(empty: bool, new_surfels: int, matched_surfels: int) -> str:
    if empty:
        return "VALID_NEGATIVE_EVIDENCE"
    if int(new_surfels) > 0:
        return "SECOND_LOCAL_ACTION_ADDED_GEOMETRY"
    if int(matched_surfels) > 0:
        return "SECOND_LOCAL_ACTION_REMEASURED_EXISTING_GEOMETRY"
    return "SECOND_LOCAL_ACTION_MEASURED_NO_ASSOCIATION"


def subsequent_policy_status(decision: dict) -> str:
    if decision.get("stop") is False and decision.get("next_gaze_deg") is not None:
        return "LOCAL_EXPLORATION_CONTINUES"
    if decision.get("stop") is True and decision.get("reason") == "no_frontier":
        return "LOCAL_POLICY_RESTOPS_NO_FRONTIER"
    return "LOCAL_POLICY_RETURNS_OTHER_STOP"


def experiment_stop() -> str:
    return "BOUNDED_AFTER_SECOND_POST_HANDOFF_LOCAL_ACTION_AND_ONE_NEXT_DECISION"


def self_test() -> None:
    assert measurement_status(False, 3, 4) == "SECOND_LOCAL_ACTION_ADDED_GEOMETRY"
    assert measurement_status(False, 0, 4) == "SECOND_LOCAL_ACTION_REMEASURED_EXISTING_GEOMETRY"
    assert measurement_status(True, 0, 0) == "VALID_NEGATIVE_EVIDENCE"
    assert subsequent_policy_status({"stop": False, "next_gaze_deg": [1.0, 2.0]}) == "LOCAL_EXPLORATION_CONTINUES"
    assert subsequent_policy_status({"stop": True, "reason": "no_frontier", "next_gaze_deg": None}) == "LOCAL_POLICY_RESTOPS_NO_FRONTIER"
    print("[multiobject3h-progress] PASS threshold_free=true one_action=true productivity_diagnostic=true auto_loop=false")


if __name__ == "__main__":
    self_test()
