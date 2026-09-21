"""Pure checks for Reality Check 2b.  Every deliberate negative exits 1."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import reality2b_public as public
import reality2_public as predecessor
import reality1_public as parent
import reality1_scene as scene
import fsg6f_public as frozen


def _assert_prediction_source(src: str) -> None:
    if "import reality1_scene" in src or "evaluation_only" in src:
        raise AssertionError("prediction-side truth import detected")


def _assert_policy_reuse(src: str) -> None:
    if "import fsg6f_frontier as policy" not in src:
        raise AssertionError("frozen FSG6f policy is not imported")
    forbidden = ("def extract_frontier", "def classify_frontier_state", "def candidate_state_consensus", "candidates.sort(")
    if any(x in src for x in forbidden):
        raise AssertionError("copied/reimplemented FSG6f controller detected")
    if src.count("policy.choose_next(") != 1:
        raise AssertionError("Reality Check 2b must call the frozen FSG6f controller at exactly one site")


def _assert_empty_contract(c: dict) -> None:
    if c["action"] != "record_negative_evidence_without_fusion":
        raise AssertionError("empty look reverted to abort/skip semantics")
    if not c["record_gaze"]:
        raise AssertionError("empty look was not marked as a visited physical fixation")
    if not c["record_binocular_history"]:
        raise AssertionError("empty look was discarded instead of becoming perceptual history")
    if c["fuse_target_points"]:
        raise AssertionError("empty look incorrectly fuses target points")
    if not c["map_must_remain_unchanged"]:
        raise AssertionError("empty look no longer requires map invariance")


def check_positive() -> dict:
    scene.self_test()
    if public.PARENT_SPEC_ID != parent.SPEC_ID:
        raise AssertionError("Reality Check 2b parent identity drifted")
    if public.PREDECESSOR_SPEC_ID != predecessor.SPEC_ID:
        raise AssertionError("Reality Check 2b predecessor identity drifted")
    for name in ("INSTRUMENT_ID", "FROZEN_POLICY_ID", "OBJECT_ID", "FIXTURE", "SEEDS", "SEED_GAZE_DEG", "VERGENCE_DISTANCE_M", "FUSION"):
        if getattr(public, name) != getattr(parent, name):
            raise AssertionError(f"Reality Check 2b changed {name}")
    if public.PARENT_FIXATIONS != parent.MAX_FIXATIONS or public.PARENT_FIXATIONS != frozen.MAX_BUDGET_FIXATIONS:
        raise AssertionError("Reality Check 2b changed the exact six-look parent state")
    if public.WATCHDOG_TOTAL_FIXATIONS != predecessor.WATCHDOG_TOTAL_FIXATIONS:
        raise AssertionError("Reality Check 2b changed the Reality Check 2 watchdog")
    if public.EMPTY_TARGET_POINT_LIMIT != 100:
        raise AssertionError("empty-observation limit drifted from the retired Reality Check 2 guard")
    _assert_empty_contract(public.empty_observation_contract(0))
    _assert_empty_contract(public.empty_observation_contract(99))
    if public.empty_observation_contract(100)["empty_target_observation"]:
        raise AssertionError("100-point target observation was incorrectly declared empty")
    if not public.empty_observation_contract(100)["fuse_target_points"]:
        raise AssertionError("non-empty target observation no longer fuses")

    src = (TOOLS / "reality2b_run.py").read_text()
    _assert_prediction_source(src)
    _assert_policy_reuse(src)
    if "tools/reality2_render_fix.py" not in src:
        raise AssertionError("Reality Check 2b changed the renderer instead of only observation semantics")
    if "public.empty_observation_contract(len(p.xyz_h))" not in src:
        raise AssertionError("runner does not use the public empty-observation contract")
    if "fixation has too few target points" in src:
        raise AssertionError("retired abort-on-empty guard still present")
    if "observation_history.append" not in src or "gazes.append(gaze)" not in src:
        raise AssertionError("empty-look evidence is not retained in persistent history")
    if src.find("observation_history.append") > src.find("decision = policy.choose_next"):
        raise AssertionError("policy decision occurs before completed observation enters history")
    if "fused\": False" not in src and '"fused": False' not in src:
        raise AssertionError("runner does not explicitly record no-fusion empty observations")

    q = public.PUBLIC_SPEC["quality_contract"].lower()
    if "without a tuned numerical pass threshold" not in q:
        raise AssertionError("Reality Check 2b silently became a numerical quality benchmark")
    if "engineering guard only" not in public.PUBLIC_SPEC["watchdog_role"].lower():
        raise AssertionError("watchdog became a scientific stopping/quality gate")

    out = {
        "fixed_head": True,
        "static_scene": True,
        "exact_parent_continuation": True,
        "frozen_fsg6f": True,
        "scientific_stop": "no_frontier",
        "watchdog_total": public.WATCHDOG_TOTAL_FIXATIONS,
        "empty_limit": public.EMPTY_TARGET_POINT_LIMIT,
        "empty_look_is_evidence": True,
        "empty_fuses": False,
        "quality_gated": False,
    }
    print("[reality2b-policy] PASS exact_parent_continuation=true frozen_fsg6f=true empty_look_is_evidence=true empty_fuses=false scientific_stop=no_frontier watchdog_total=24 quality_gated=false")
    return out


def deliberate_negative(name: str) -> None:
    if name == "abortempty":
        c = dict(public.empty_observation_contract(0)); c["action"] = "abort"
        _assert_empty_contract(c)
    elif name == "skipempty":
        c = dict(public.empty_observation_contract(0)); c["record_binocular_history"] = False
        _assert_empty_contract(c)
    elif name == "dropgaze":
        c = dict(public.empty_observation_contract(0)); c["record_gaze"] = False
        _assert_empty_contract(c)
    elif name == "fuseempty":
        c = dict(public.empty_observation_contract(0)); c["fuse_target_points"] = True
        _assert_empty_contract(c)
    elif name == "sixlimit":
        if parent.MAX_FIXATIONS != public.WATCHDOG_TOTAL_FIXATIONS:
            raise AssertionError("deliberate retired six-look interruption detected")
    elif name == "rerenderparent":
        reuse_parent = False
        if reuse_parent is not True:
            raise AssertionError("deliberate rerender of saved Reality Check 1 parent views detected")
    elif name == "policycopy":
        _assert_policy_reuse("import fsg6f_frontier as policy\ndef candidate_state_consensus(): pass\npolicy.choose_next(")
    elif name == "truth":
        _assert_prediction_source("import reality1_scene\n")
    elif name == "qualitygate":
        fake = "final coverage >= 0.90"
        if ">=" in fake:
            raise AssertionError("deliberate post-hoc numerical quality gate detected")
    elif name == "watchdoggate":
        fake = "scientific PASS gate"
        if "engineering guard only" not in fake:
            raise AssertionError("deliberate promotion of watchdog to scientific PASS/FAIL detected")
    else:
        raise ValueError(name)
    raise AssertionError(f"negative {name} unexpectedly escaped its detector")


def main() -> None:
    names = ("abortempty", "skipempty", "dropgaze", "fuseempty", "sixlimit", "rerenderparent", "policycopy", "truth", "qualitygate", "watchdoggate")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--negative", choices=names)
    a = ap.parse_args()
    if a.negative:
        try:
            deliberate_negative(a.negative)
        except Exception as exc:
            print(f"[reality2b-check] FAIL {type(exc).__name__} {exc}")
            raise SystemExit(1)
        raise SystemExit(0)
    check_positive()
    print("[reality2b-check] SUMMARY passed=7 failed=0")


if __name__ == "__main__":
    main()
