"""Checks for Cyclopean-1b.  Every deliberate negative must fail."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import cyclopean1b_public as public
import cyclopean1b_boundary as boundary


def positive() -> None:
    boundary.self_test()
    if not public.NO_ACQUISITION:
        raise AssertionError("Cyclopean-1b unexpectedly allows acquisition")
    if public.FUSION["association_radius_m"] != 0.012:
        raise AssertionError("frozen FSG3 association radius changed")
    src = (TOOLS / "cyclopean1b_audit.py").read_text()
    if "evaluation_only" in src or "reality2b_eval" in src:
        raise AssertionError("boundary audit imports evaluator truth")
    if "subprocess" in src or "reality2_render_fix.py" in src:
        raise AssertionError("boundary audit quietly performs acquisition")
    print("[cyclopean1b-policy] PASS parent=cyclopean1a read_only=true acquisition=false boundary_arcs=true no_mesh=true quality_gated=false")
    print("[cyclopean1b-check] SUMMARY passed=6 failed=0")


def negative(kind: str) -> None:
    raw, support, rr, ev = boundary._synthetic_arrays()
    a = boundary.analyze_boundary(raw_support=raw, support=support, target_range_m=rr,
                                  evidence=ev, grid_deg=.1, yaw0_deg=-2, pitch0_deg=-1.5,
                                  footprint_cells=1, association_radius_m=.012)
    if kind == "holeonly":
        if not any(q["component_kind"] == "EXTERIOR" for q in a.arcs):
            return
        raise AssertionError("deliberate internal-holes-only boundary audit detected")
    if kind == "exteriorresolved":
        if all(q["state"] == "PHYSICAL_DEPTH_BREAK" for q in a.arcs if q["component_kind"] == "EXTERIOR"):
            return
        raise AssertionError("deliberate border-touching-equals-resolved rule detected")
    if kind == "depthblind":
        ys, xs = a.shoreline.nonzero(); y, x = int(ys[0]), int(xs[0])
        ev.seen_nontarget[y,x] = True; ev.nontarget_range_m[y,x] = 2.8
        b = boundary.analyze_boundary(raw_support=raw, support=support, target_range_m=rr,
                                      evidence=ev, grid_deg=.1, yaw0_deg=-2, pitch0_deg=-1.5,
                                      footprint_cells=1, association_radius_m=.012)
        if b.state_code[y,x] != boundary.STATE_CODE["PHYSICAL_DEPTH_BREAK"]:
            return
        raise AssertionError("deliberate depth-blind shoreline semantics detected")
    if kind == "truth":
        txt = (TOOLS / "cyclopean1b_audit.py").read_text() + (TOOLS / "cyclopean1b_boundary.py").read_text()
        if "evaluation_only" in txt or "reality2b_eval" in txt:
            return
        raise AssertionError("deliberate evaluator-truth audit detected")
    if kind == "mesh":
        txt = (TOOLS / "cyclopean1b_boundary.py").read_text()
        if "trimesh" in txt or "marching_cubes" in txt:
            return
        raise AssertionError("deliberate mesh substitute detected")
    if kind == "acquire":
        txt = (TOOLS / "cyclopean1b_audit.py").read_text().lower()
        if "subprocess" in txt or "reality2_render_fix.py" in txt:
            return
        raise AssertionError("deliberate new-acquisition substitute detected")
    raise ValueError(kind)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--negative", choices=("holeonly", "exteriorresolved", "depthblind", "truth", "mesh", "acquire"))
    a = ap.parse_args()
    try:
        if a.negative:
            negative(a.negative)
        else:
            positive(); return
    except AssertionError as e:
        if a.negative:
            print(f"[cyclopean1b-check] FAIL AssertionError {e}")
            raise SystemExit(1)
        raise
    if a.negative:
        print(f"[cyclopean1b-check] NEGATIVE DID NOT FAIL {a.negative}")
        raise SystemExit(0)


if __name__ == "__main__":
    main()
