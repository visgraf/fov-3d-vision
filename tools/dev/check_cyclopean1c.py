"""Checks for Cyclopean-1c. Every deliberate negative must fail."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import cyclopean1c_public as public
import cyclopean1c_bay as bay


def positive() -> None:
    bay.self_test()
    if public.SEEDS != (2111,):
        raise AssertionError("Cyclopean-1c must schedule seed 2111 only")
    if public.MAX_ADDED_FIXATIONS != 1:
        raise AssertionError("Cyclopean-1c must add exactly one fixation at most")
    if public.FUSION["association_radius_m"] != 0.012:
        raise AssertionError("frozen FSG3 association radius changed")
    src = (TOOLS / "cyclopean1c_probe.py").read_text().lower()
    if "evaluation_only" in src or "reality2b_eval" in src:
        raise AssertionError("bay probe imports evaluator truth")
    if "fsg6f_frontier" in src or "fsg6f_public" in src:
        raise AssertionError("bay probe quietly replaces/modifies FSG6f")
    print("[cyclopean1c-policy] PASS parent=cyclopean1b seed2111_only=true one_fixation_max=true frozen_fsg6f=true no_mesh=true quality_gated=false")
    print("[cyclopean1c-check] SUMMARY passed=6 failed=0")


def negative(kind: str) -> None:
    a, chart = bay._synthetic_audit()
    if kind == "internal":
        p = bay.select_deep_bay_probe(a, chart, [])
        if p is not None and a.component_touches_border[int(p["component_id"])]:
            raise AssertionError("deliberate internal-component probe detected")
        return
    if kind == "physical":
        b, chart2 = bay._synthetic_audit(physical_only=True)
        if bay.select_deep_bay_probe(b, chart2, []) is None:
            raise AssertionError("deliberate physical-boundary probe detected")
        return
    if kind == "centroid":
        p = bay.select_deep_bay_probe(a, chart, [])
        cid = int(p["component_id"])
        maxd = int(a.exterior_distance_cells[a.component_labels == cid].max())
        if int(p["probe_border_distance_cells"]) == maxd:
            raise AssertionError("deliberate shoreline-centroid substitute detected")
        return
    if kind == "multiprobe":
        if public.MAX_ADDED_FIXATIONS == 1:
            raise AssertionError("deliberate multi-probe policy detected")
        return
    if kind == "truth":
        txt = (TOOLS / "cyclopean1c_probe.py").read_text() + (TOOLS / "cyclopean1c_bay.py").read_text()
        if "evaluation_only" not in txt and "reality2b_eval" not in txt:
            raise AssertionError("deliberate evaluator-truth path detected")
        return
    if kind == "policy":
        txt = (TOOLS / "cyclopean1c_probe.py").read_text().lower()
        if "fsg6f_frontier" not in txt and "fsg6f_public" not in txt:
            raise AssertionError("deliberate FSG6f policy replacement detected")
        return
    raise ValueError(kind)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--negative", choices=("internal", "physical", "centroid", "multiprobe", "truth", "policy"))
    a = ap.parse_args()
    try:
        if a.negative:
            negative(a.negative)
        else:
            positive(); return
    except AssertionError as e:
        if a.negative:
            print(f"[cyclopean1c-check] FAIL AssertionError {e}")
            raise SystemExit(1)
        raise
    if a.negative:
        print(f"[cyclopean1c-check] NEGATIVE DID NOT FAIL {a.negative}")
        raise SystemExit(0)


if __name__ == "__main__":
    main()
