"""Pure descriptive status helpers for MultiObject-3f.

No scientific threshold is introduced.  These helpers only verify the literal
pre/post control-state transition already claimed by the completed parent and
state where the bounded audit stops.
"""
from __future__ import annotations


def reactivation_status(pre: dict, post: dict) -> str:
    if (
        pre.get("stop") is True
        and pre.get("reason") == "no_frontier"
        and int(pre.get("candidates_before_consensus_count", -1)) == 0
        and post.get("stop") is False
        and post.get("reason") == "continue"
        and post.get("next_gaze_deg") is not None
        and int(post.get("candidates_before_consensus_count", 0)) > 0
    ):
        return "LOCAL_POLICY_REACTIVATION_REPRODUCED"
    return "PARENT_REACTIVATION_NOT_REPRODUCED"


def experiment_stop() -> str:
    return "READ_ONLY_AFTER_FRONTIER_REACTIVATION_AUDIT"


def next_stage() -> str:
    return "INTERPRET_BEFORE_ANY_SECOND_ACTION"


def self_test() -> None:
    pre = {"stop": True, "reason": "no_frontier", "candidates_before_consensus_count": 0}
    post = {"stop": False, "reason": "continue", "next_gaze_deg": [1.0, 2.0], "candidates_before_consensus_count": 1}
    assert reactivation_status(pre, post) == "LOCAL_POLICY_REACTIVATION_REPRODUCED"
    assert experiment_stop() == "READ_ONLY_AFTER_FRONTIER_REACTIVATION_AUDIT"
    print("[multiobject3f-progress] PASS threshold_free=true pre_post_reactivation=true no_action=true")


if __name__ == "__main__":
    self_test()
