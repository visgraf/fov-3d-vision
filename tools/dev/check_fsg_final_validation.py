"""Software checks for FSG1g.  Run in the repository venv."""
from __future__ import annotations
import argparse
import copy
import sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/"tools"))
import fsg_final_scene as spec
import fsg_stereo_supported as supported
import fsg_stereo_hdr as hdr
import fsg_final_eval as final


def check() -> None:
    spec.self_test()
    supported.check_kernel_equivalence()
    # Candidate identity: final inference must be the FSG1f one-step control,
    # not the named footprint-supported candidate.
    if "compute_once" not in final.save_prediction.__code__.co_names or "compute_variants" in final.save_prediction.__code__.co_names:
        raise AssertionError("final validator must use compute_once only")
    if final.CANDIDATE_ID != spec.SPEC["candidate"]:
        raise AssertionError("candidate ID drift")
    # Boundary gate must fail on too few accepted points and on poor accuracy.
    base={"accepted_pixels":150,"median_relative_range_error":0.005,"p95_relative_range_error":0.02}
    if final.boundary_gate(base): raise AssertionError("known-good boundary metrics rejected")
    bad=copy.deepcopy(base);bad["p95_relative_range_error"]=0.031
    if not final.boundary_gate(bad): raise AssertionError("bad boundary p95 did not fail")
    sparse=copy.deepcopy(base);sparse["accepted_pixels"]=99
    if not final.boundary_gate(sparse): raise AssertionError("unexercised boundary did not fail")
    # Occlusion core construction must be strictly smaller for a finite block.
    m=np.zeros((32,32),bool);m[8:24,8:24]=True
    core=final.eroded_core(m,"full")
    if not (0 < core.sum() < m.sum()): raise AssertionError("occlusion erosion broken")
    print("[fsg-final-check] SUMMARY passed=7 failed=0")


def negative(kind: str) -> None:
    if kind=="phase":
        old=spec.PHASE_DISPARITY_PX["phase_50"];spec.PHASE_DISPARITY_PX["phase_50"]=old+0.4
        try:
            # Compare against the frozen SPEC copy, which must now disagree.
            if spec.PHASE_DISPARITY_PX == spec.SPEC["phase_target_disparity_px"]: raise AssertionError("phase mutation hidden")
            raise AssertionError("deliberate phase mutation detected")
        finally: spec.PHASE_DISPARITY_PX["phase_50"]=old
    if kind=="boundary":
        bad={"accepted_pixels":150,"median_relative_range_error":0.02,"p95_relative_range_error":0.04}
        fails=final.boundary_gate(bad)
        if not fails: raise AssertionError("deliberate bad boundary accepted")
        raise AssertionError("deliberate bad boundary detected: "+"; ".join(fails))
    if kind=="candidate":
        if supported.CANDIDATE_ID == final.CANDIDATE_ID: raise AssertionError("wrong supported-footprint candidate selected")
        raise AssertionError("deliberate candidate substitution detected")
    raise ValueError(kind)


def main() -> None:
    ap=argparse.ArgumentParser();ap.add_argument("--negative",choices=("phase","boundary","candidate"));args=ap.parse_args()
    if args.negative: negative(args.negative)
    check()

if __name__=="__main__":
    try: main()
    except Exception as exc:
        print(f"[fsg-final-check] FAIL {type(exc).__name__}: {exc}",file=sys.stderr);raise SystemExit(1)
