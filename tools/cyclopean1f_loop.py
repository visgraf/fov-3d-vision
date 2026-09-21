"""Pure loop semantics for Cyclopean-1f.

This module deliberately knows nothing about Blender, stereo, truth, or FSG6f.
It only distinguishes the scientific fixed point from the engineering watchdog.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LoopDecision:
    action: str
    reason: str


def decide(*, eligible_probe_exists: bool, total_fixations: int, watchdog_total_fixations: int) -> LoopDecision:
    if not eligible_probe_exists:
        return LoopDecision("STOP", "NO_ELIGIBLE_EXTERIOR_NEVER_OBSERVED")
    if int(total_fixations) >= int(watchdog_total_fixations):
        return LoopDecision("STOP", "WATCHDOG_TOTAL_FIXATIONS")
    return LoopDecision("ACQUIRE", "ELIGIBLE_EXTERIOR_NEVER_OBSERVED")


def self_test() -> None:
    a = decide(eligible_probe_exists=False, total_fixations=15, watchdog_total_fixations=24)
    b = decide(eligible_probe_exists=True, total_fixations=24, watchdog_total_fixations=24)
    c = decide(eligible_probe_exists=True, total_fixations=15, watchdog_total_fixations=24)
    assert (a.action, a.reason) == ("STOP", "NO_ELIGIBLE_EXTERIOR_NEVER_OBSERVED")
    assert (b.action, b.reason) == ("STOP", "WATCHDOG_TOTAL_FIXATIONS")
    assert (c.action, c.reason) == ("ACQUIRE", "ELIGIBLE_EXTERIOR_NEVER_OBSERVED")
    print("[cyclopean1f-loop] PASS fixed_point=true watchdog_guardrail=true acquire=true")


if __name__ == "__main__":
    self_test()
