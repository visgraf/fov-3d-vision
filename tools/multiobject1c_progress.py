"""Pure summary helpers for MultiObject-1c.

No thresholds are used.  The object status is a literal description of whether
any exterior NEVER_OBSERVED cells remain and whether any target-no-depth cells
remain.  Scene disposition is deliberately independent of those labels: move
to the next-object stage and retain object 143 for later revisit if useful.
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


def scene_disposition() -> str:
    return "MOVE_TO_NEXT_OBJECT"


def self_test() -> None:
    assert object_status({"NEVER_OBSERVED": 5}, {"OBSERVED_TARGET_NO_DEPTH": 0}) == "ATTENTION_INCOMPLETE_RETAIN_FOR_REVISIT"
    assert object_status({"NEVER_OBSERVED": 0}, {"OBSERVED_TARGET_NO_DEPTH": 7}) == "ATTENTION_COMPLETE_MEASUREMENT_PARTIAL"
    assert object_status({"NEVER_OBSERVED": 0}, {"OBSERVED_TARGET_NO_DEPTH": 0}) == "ATTENTION_COMPLETE_NO_TARGET_NO_DEPTH_RESIDUE"
    assert scene_disposition() == "MOVE_TO_NEXT_OBJECT"
    print("[multiobject1c-progress] PASS no_threshold=true descriptive_object_status=true scene_progress_unblocked=true")


if __name__ == "__main__":
    self_test()
