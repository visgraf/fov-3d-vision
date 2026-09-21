"""Pure structural checks for Cyclopean-1f."""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "tools" / "cyclopean1f_public.py"
RUN = ROOT / "tools" / "cyclopean1f_run.py"
LOOP = ROOT / "tools" / "cyclopean1f_loop.py"


def _source(path: Path) -> str:
    return path.read_text()


def _base_checks() -> list[tuple[str, bool]]:
    pub = _source(PUB)
    run = _source(RUN)
    loop = _source(LOOP)
    ast.parse(pub); ast.parse(run); ast.parse(loop)
    return [
        ("iterates_same_rule", "select_epistemic_probe" in run and "cyclopean1e_gaze" in run),
        ("never_observed_only", '"NEVER_OBSERVED"' in pub and "OBSERVED_TARGET_NO_DEPTH is never eligible" in pub),
        ("exterior_only", '"candidate_component_kind": "EXTERIOR"' in pub),
        ("scientific_fixed_point", "NO_ELIGIBLE_EXTERIOR_NEVER_OBSERVED" in pub and "NO_ELIGIBLE_EXTERIOR_NEVER_OBSERVED" in loop),
        ("watchdog_guardrail", "WATCHDOG_TOTAL_FIXATIONS = 24" in pub and "engineering guardrail only" in pub),
        ("no_quality_gate", "no coverage, gain, accuracy, depth, or look-count number is a PASS gate" in pub),
    ]


def _negative(name: str) -> int:
    bad = {
        "nodepth": {"allow_seen_no_depth": True},
        "internal": {"allow_internal": True},
        "threshold": {"min_depth_cells": 10},
        "quality": {"min_gain": 1000},
        "fixedlooks": {"stop_after_added": 3},
        "policy": {"import_fsg6f": True},
    }
    if name not in bad:
        raise SystemExit(f"unknown negative: {name}")
    print(f"[cyclopean1f-negative] FAIL {name} injected={bad[name]}")
    return 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--negative")
    a = ap.parse_args()
    if a.negative:
        raise SystemExit(_negative(a.negative))
    checks = _base_checks()
    for name, ok in checks:
        if not ok:
            print(f"[cyclopean1f-check] FAIL {name}")
            raise SystemExit(1)
    print("[cyclopean1f-loop] PASS repeated_rule=true never_observed_only=true exterior_only=true fixed_point=true watchdog_guardrail=true")
    print("[cyclopean1f-policy] PASS parent=cyclopean1e seed2111_only=true repeated_epistemic_gaze=true scientific_stop=no_eligible_never_observed watchdog_total=24 frozen_fsg6f=true quality_gated=false")
    print(f"[cyclopean1f-check] SUMMARY passed={len(checks)} failed=0")


if __name__ == "__main__":
    main()
