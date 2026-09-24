#!/usr/bin/env python3
"""Fail-capable acceptance checks for Classroom-Oracle-1."""
from __future__ import annotations

import inspect
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import classroom_oracle1_epistemic as epi
import classroom_oracle1_matcher as matcher
import classroom_oracle1_public as public
import classroom_oracle1_run as run
import fsg6f_public as frozen
import multiobject2c_policy as object_policy


PASSED = 0
FAILED = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"[classroom-oracle1-check] PASS {name}")
    else:
        FAILED += 1
        print(f"[classroom-oracle1-check] FAIL {name}: {detail}")


def no_fail(fn) -> tuple[bool, str]:
    try:
        x = fn()
        return len(x) == 0, "; ".join(map(str, x))
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def main() -> int:
    p = (TOOLS / "classroom_oracle1_public.py").read_text()
    m = (TOOLS / "classroom_oracle1_matcher.py").read_text()
    r = (TOOLS / "classroom_oracle1_run.py").read_text()
    br = (TOOLS / "classroom_oracle1_render.py").read_text()

    ok, detail = no_fail(public.self_test)
    check("01-public-contract", ok, detail)

    ok, detail = no_fail(matcher.self_test)
    check("02-perfect-matcher-self-test", ok, detail)

    ok, detail = no_fail(epi.self_test)
    check("03-cyclopean-self-test", ok, detail)

    ok, detail = no_fail(run.self_test)
    check("04-runner-inherited-constants", ok, detail)

    check(
        "05-no-sgbm-in-oracle",
        "StereoSGBM" not in m and "depth_search_z_rect_m" not in m and "fsg_stereo.compute(" not in m,
        "oracle matcher must not call SGBM or its range-search path",
    )

    check(
        "06-binocular-same-instance-rule",
        "same_instance" in m and "sampled_r_id == left_ids" in m,
        "right-eye reprojection must see the same instance",
    )

    check(
        "07-control-does-not-open-dense-truth",
        "evaluation_only" not in r,
        "control runner must never name/open the evaluation-only truth directory",
    )

    check(
        "08-blender-only-seeds-plus-current-pair",
        "one seed direction" in br and "multiobject2c_policy" not in br and "choose_next(" not in br,
        "Blender renderer must not contain the autonomous gaze policy",
    )

    check(
        "09-no-foreground-background-decomposition",
        public.ORACLE_CONTRACT.get("foreground_background_decomposition") is False
        and "foreground_background_decomposition\": False" in r,
        "all scene surfaces must remain ordinary entities",
    )

    frozen_fusion = getattr(frozen, "FUSION", {})
    check(
        "10-12mm-fusion-and-24-watchdog",
        public.MAX_OBJECT_FIXATIONS == 24
        and float(public.FUSION["association_radius_m"]) == 0.012
        and float(public.FUSION["hash_cell_m"]) == 0.012
        and float(frozen_fusion["association_radius_m"]) == 0.012
        and float(frozen_fusion["hash_cell_m"]) == 0.012,
        "Classroom-Oracle-1 must inherit the frozen 12 mm fusion rule and 24-look watchdog",
    )

    check(
        "11-benchmark-is-preserved",
        "raw_left_exr" in r and "raw_right_exr" in r
        and "rectified_left_png" in r and "rectified_right_png" in r
        and "oracle_patch" in r,
        "every controller-selected pair and oracle patch must be retained",
    )

    adapter_src = inspect.getsource(object_policy)
    check(
        "12-empty-looks-and-frozen-policy-adapter",
        "empty_look" in r and "fuse zero" in public.CONTROL_CONTRACT["empty_look_semantics"]
        and "fsg6f_frontier" in adapter_src,
        "empty looks must remain observations and target-label adapter must delegate to frozen FSG6f",
    )

    print(f"[classroom-oracle1-check] SUMMARY passed={PASSED} failed={FAILED}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
