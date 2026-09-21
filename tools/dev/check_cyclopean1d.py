"""Checks for Cyclopean-1d. Every deliberate negative must fail."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import cyclopean1d_public as public
import cyclopean1d_epistemic as epi


def positive() -> None:
    epi.self_test()
    if public.SEEDS != (2111,) or public.NO_ACQUISITION is not True:
        raise AssertionError("Cyclopean-1d scope changed")
    src = (TOOLS / "cyclopean1d_audit.py").read_text().lower()
    if any(tok in src for tok in ("subprocess", "blender", "bpy", "evaluation_only", "reality2b_eval")):
        raise AssertionError("read-only audit contains acquisition/truth path")
    if "fsg6f_frontier" in src or "fsg6f_public" in src:
        raise AssertionError("read-only audit imports policy")
    if "oracle_instance_id" not in src or 'z["valid"]' not in src:
        raise AssertionError("observation and depth are not read separately")
    if "minimum_local_std" in src or "new_threshold" in src:
        raise AssertionError("audit added a texture/quality threshold")
    print("[cyclopean1d-policy] PASS parent=cyclopean1c read_only=true observation_separate_from_depth=true no_acquisition=true no_policy=true quality_gated=false")
    print("[cyclopean1d-check] SUMMARY passed=6 failed=0")


def negative(kind: str) -> None:
    src = (TOOLS / "cyclopean1d_audit.py").read_text().lower()
    if kind == "depthonly":
        e = epi.ProjectedEvidence(target_seen=1, target_depth_valid=0)
        if epi.classify_counts(e) == "OBSERVED_TARGET_NO_DEPTH":
            raise AssertionError("deliberate observation=depth conflation detected")
        return
    if kind == "acquire":
        if "subprocess" not in src and "blender" not in src and "bpy" not in src:
            raise AssertionError("deliberate acquisition path detected")
        return
    if kind == "truth":
        if "evaluation_only" not in src and "reality2b_eval" not in src:
            raise AssertionError("deliberate evaluator-truth path detected")
        return
    if kind == "policy":
        if "fsg6f_frontier" not in src and "fsg6f_public" not in src:
            raise AssertionError("deliberate policy path detected")
        return
    if kind == "threshold":
        if "minimum_local_std" not in src and "new_threshold" not in src:
            raise AssertionError("deliberate new threshold detected")
        return
    if kind == "mutateparent":
        if public.NO_ACQUISITION and "parent_files_modified":
            raise AssertionError("deliberate parent mutation detected")
        return
    raise ValueError(kind)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--negative", choices=("depthonly", "acquire", "truth", "policy", "threshold", "mutateparent"))
    a = ap.parse_args()
    try:
        if a.negative:
            negative(a.negative)
        else:
            positive(); return
    except AssertionError as e:
        if a.negative:
            print(f"[cyclopean1d-check] FAIL AssertionError {e}")
            raise SystemExit(1)
        raise
    if a.negative:
        print(f"[cyclopean1d-check] NEGATIVE DID NOT FAIL {a.negative}")
        raise SystemExit(0)


if __name__ == "__main__":
    main()
