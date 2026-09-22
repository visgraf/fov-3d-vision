"""Pure descriptive summary helpers for MultiObject-3d.

No fitted threshold is used.  Object attention status depends only on literal
zero/non-zero epistemic counts.  The stop interpretation distinguishes a frozen
policy stop with genuinely unseen exterior territory from an attention-complete
stop.  Scene progress is deliberately independent of those labels.
"""
from __future__ import annotations


def object_status(exterior_counts: dict[str, int], all_counts: dict[str, int]) -> str:
    unseen = int(exterior_counts.get("NEVER_OBSERVED", 0))
    no_depth = int(all_counts.get("OBSERVED_TARGET_NO_DEPTH", 0))
    if unseen > 0:
        return "ATTENTION_INCOMPLETE_RETAIN_FOR_REVISIT"
    if no_depth > 0:
        return "ATTENTION_COMPLETE_MEASUREMENT_PARTIAL"
    return "ATTENTION_COMPLETE_NO_TARGET_NO_DEPTH_RESIDUE"


def stop_interpretation(exterior_counts: dict[str, int], all_counts: dict[str, int], final_policy: dict) -> str:
    if final_policy.get("reason") != "no_frontier" or final_policy.get("stop") is not True:
        return "PARENT_NOT_AT_DECLARED_POLICY_STOP"
    if int(exterior_counts.get("NEVER_OBSERVED", 0)) > 0:
        return "POLICY_EXHAUSTED_WITH_UNSEEN_TERRITORY"
    if int(all_counts.get("OBSERVED_TARGET_NO_DEPTH", 0)) > 0:
        return "ATTENTION_COMPLETE_MEASUREMENT_PARTIAL_AT_POLICY_STOP"
    return "ATTENTION_COMPLETE_AT_POLICY_STOP"


def scene_disposition() -> str:
    return "MOVE_TO_NEXT_OBJECT"


def self_test() -> None:
    f = {"stop": True, "reason": "no_frontier"}
    assert stop_interpretation({"NEVER_OBSERVED": 4}, {"OBSERVED_TARGET_NO_DEPTH": 0}, f) == "POLICY_EXHAUSTED_WITH_UNSEEN_TERRITORY"
    assert stop_interpretation({"NEVER_OBSERVED": 0}, {"OBSERVED_TARGET_NO_DEPTH": 2}, f) == "ATTENTION_COMPLETE_MEASUREMENT_PARTIAL_AT_POLICY_STOP"
    assert stop_interpretation({"NEVER_OBSERVED": 0}, {"OBSERVED_TARGET_NO_DEPTH": 0}, f) == "ATTENTION_COMPLETE_AT_POLICY_STOP"
    assert scene_disposition() == "MOVE_TO_NEXT_OBJECT"
    print("[multiobject3d-progress] PASS no_threshold=true stop_interpretation=true scene_progress_unblocked=true")


if __name__ == "__main__":
    self_test()
