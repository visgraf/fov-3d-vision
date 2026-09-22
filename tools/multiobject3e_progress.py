"""Threshold-free interpretation of the one returned local-policy decision."""
from __future__ import annotations


def classify_return(decision: dict) -> str:
    """Describe, never gate, what frozen FSG6f says after the epistemic handoff."""
    if decision.get("stop") is False and decision.get("next_gaze_deg") is not None:
        return "LOCAL_POLICY_REACTIVATED"
    if decision.get("stop") is True and decision.get("reason") == "no_frontier":
        return "LOCAL_POLICY_STILL_EXHAUSTED"
    return "LOCAL_POLICY_RETURNED_OTHER_STOP"


def experiment_stop() -> str:
    return "BOUNDED_AFTER_ONE_HANDOFF_AND_ONE_RETURN_DECISION"


def self_test() -> None:
    assert classify_return({"stop": False, "next_gaze_deg": [1.0, 2.0]}) == "LOCAL_POLICY_REACTIVATED"
    assert classify_return({"stop": True, "reason": "no_frontier", "next_gaze_deg": None}) == "LOCAL_POLICY_STILL_EXHAUSTED"
    assert classify_return({"stop": True, "reason": "other", "next_gaze_deg": None}) == "LOCAL_POLICY_RETURNED_OTHER_STOP"
    assert experiment_stop() == "BOUNDED_AFTER_ONE_HANDOFF_AND_ONE_RETURN_DECISION"
    print("[multiobject3e-progress] PASS threshold_free=true one_return_decision=true auto_loop=false")


if __name__ == "__main__":
    self_test()
