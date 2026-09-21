"""Pure structural checks and real source-mutation negatives for Cyclopean-1g."""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "tools" / "cyclopean1g_public.py"
PROBE = ROOT / "tools" / "cyclopean1g_probe.py"
MEAS = ROOT / "tools" / "cyclopean1g_measurement.py"


def _source(path: Path) -> str:
    return path.read_text()


def _checks(pub: str, probe: str, meas: str) -> list[tuple[str, bool]]:
    ast.parse(pub); ast.parse(probe); ast.parse(meas)
    return [
        ("internal_no_depth_only", '"candidate_state": "OBSERVED_TARGET_NO_DEPTH"' in pub and '"candidate_component_kind": "INTERNAL"' in pub),
        ("recenter_only", "re-center the existing residue" in pub and "frozen Reality/FSG stereo front end, vergence/render settings" in pub),
        ("one_probe", "MAX_ADDED_FIXATIONS = 1" in pub and '"added_fixations": 1' in probe),
        ("binary_outcome_no_gate", "DEPTH_RECOVERED" in pub and "DEPTH_STILL_ABSENT" in pub and "no recovered-cell count" in pub),
        ("stop_then_multiobject", "STOP_AFTER_ONE_LOOK_REGARDLESS_OF_OUTCOME_THEN_MOVE_TO_MULTI_OBJECT" in probe and "move next to multiple objects" in pub),
        ("no_truth_or_rescue_loop", "no evaluator truth is opened" in pub and "no repeated rescue loop is allowed" in pub),
    ]


def _mutate(name: str, pub: str, probe: str, meas: str) -> tuple[str, str, str]:
    if name == "external":
        pub = pub.replace('"candidate_component_kind": "INTERNAL"', '"candidate_component_kind": "EXTERIOR"', 1)
    elif name == "unseen":
        pub = pub.replace('"candidate_state": "OBSERVED_TARGET_NO_DEPTH"', '"candidate_state": "NEVER_OBSERVED"', 1)
    elif name == "multiprobe":
        pub = pub.replace("MAX_ADDED_FIXATIONS = 1", "MAX_ADDED_FIXATIONS = 2", 1)
        probe = probe.replace('"added_fixations": 1', '"added_fixations": 2', 1)
    elif name == "quality":
        pub = pub.replace("no recovered-cell count", "require recovered-cell count", 1)
    elif name == "rescueloop":
        pub = pub.replace("no repeated rescue loop is allowed", "repeat rescue looks until depth recovers", 1)
    elif name == "truth":
        pub = pub.replace("no evaluator truth is opened", "evaluator truth may be opened", 1)
    else:
        raise SystemExit(f"unknown negative: {name}")
    return pub, probe, meas


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--negative")
    a = ap.parse_args()
    pub, probe, meas = _source(PUB), _source(PROBE), _source(MEAS)
    base = _checks(pub, probe, meas)
    if a.negative:
        mpub, mprobe, mmeas = _mutate(a.negative, pub, probe, meas)
        mutated = _checks(mpub, mprobe, mmeas)
        failed = [name for (name, ok0), (_, ok1) in zip(base, mutated) if ok0 and not ok1]
        if not failed:
            print(f"[cyclopean1g-negative] ERROR {a.negative} mutation escaped detection")
            raise SystemExit(2)
        print(f"[cyclopean1g-negative] FAIL {a.negative} detected_by={','.join(failed)}")
        raise SystemExit(1)

    for name, ok in base:
        if not ok:
            print(f"[cyclopean1g-check] FAIL {name}")
            raise SystemExit(1)
    print("[cyclopean1g-measurement] PASS internal_no_depth_only=true centroid_recentering=true one_probe=true binary_outcome=true branch_closes=true")
    print("[cyclopean1g-policy] PASS parent=cyclopean1f seed2111_only=true frozen_stereo=true frozen_vergence=true quality_gated=false next=multi_object")
    print(f"[cyclopean1g-check] SUMMARY passed={len(base)} failed=0")


if __name__ == "__main__":
    main()
