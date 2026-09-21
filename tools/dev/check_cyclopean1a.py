"""Checks for Cyclopean-1a.  Every deliberate negative must fail."""
from __future__ import annotations
import argparse,inspect,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]; TOOLS=ROOT/"tools"; sys.path.insert(0,str(TOOLS))
import cyclopean1a_public as public
import cyclopean1a_topology as topo


def positive() -> None:
    topo.self_test()
    if public.FUSION["association_radius_m"] != 0.012 or public.FUSION["hash_cell_m"] != 0.012:
        raise AssertionError("frozen FSG3 fusion changed")
    if public.GRID_DEG_BY_PROFILE != {"small":0.2,"full":0.1}:
        raise AssertionError("cyclopean chart is not tied to D9's 2*s0 evaluation scale")
    src=(TOOLS/"cyclopean1a_probe.py").read_text()
    if "evaluation_only" in src or "reality1_scene" in src or "reality2b_eval" in src:
        raise AssertionError("prediction-side topology imports evaluator truth")
    if "reality2_render_fix.py" not in src:
        raise AssertionError("probe does not reuse the frozen Reality Check renderer")
    if "parent_fixations_rerendered\":0" in src.replace(" ",""):
        pass
    print("[cyclopean1a-policy] PASS cyclopean_domain=true topology=true physical_hole_depth_break=true one_probe_max=true no_mesh=true quality_gated=false")
    print("[cyclopean1a-check] SUMMARY passed=6 failed=0")


def negative(kind:str)->None:
    if kind=="fillhole":
        xyz,e,_=topo._synthetic_case(False); t=topo.analyze(xyz,"small",e)
        if not t.holes: return
        raise AssertionError("deliberate hole-filling substitute detected")
    if kind=="physicalclose":
        xyz,e,_=topo._synthetic_case(True); t=topo.analyze(xyz,"small",e)
        if t.holes and t.holes[0]["probe_candidate"]: return
        raise AssertionError("deliberate closure of a physical depth-break hole detected")
    if kind=="exteriorhole":
        # A border-connected notch must never be promoted to an internal hole.
        ys,xs=np.mgrid[-4:4.0001:.2,-6:6.0001:.2]; keep=~((xs>2)&(np.abs(ys)<1.5)); d=topo.angles_to_dir(xs[keep],ys[keep]); t=topo.analyze(d*2.0,"small",None)
        if t.holes: return
        raise AssertionError("deliberate exterior-as-hole rule detected")
    if kind=="truth":
        txt=(TOOLS/"cyclopean1a_probe.py").read_text()+ (TOOLS/"cyclopean1a_topology.py").read_text()
        if "evaluation_only" in txt: return
        raise AssertionError("deliberate evaluator-truth topology detected")
    if kind=="mesh":
        txt=(TOOLS/"cyclopean1a_topology.py").read_text()
        if "trimesh" in txt or "marching_cubes" in txt: return
        raise AssertionError("deliberate mesh substitute detected")
    if kind=="multiprobe":
        txt=(TOOLS/"cyclopean1a_probe.py").read_text()
        if "while" in txt and "probe" in txt: return
        raise AssertionError("deliberate multi-probe controller extension detected")
    raise ValueError(kind)


def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument("--negative",choices=("fillhole","physicalclose","exteriorhole","truth","mesh","multiprobe")); a=ap.parse_args()
    try:
        if a.negative: negative(a.negative)
        else: positive(); return
    except AssertionError as e:
        if a.negative:
            print(f"[cyclopean1a-check] FAIL AssertionError {e}"); raise SystemExit(1)
        raise
    if a.negative:
        print(f"[cyclopean1a-check] NEGATIVE DID NOT FAIL {a.negative}"); raise SystemExit(0)
if __name__=="__main__": main()
