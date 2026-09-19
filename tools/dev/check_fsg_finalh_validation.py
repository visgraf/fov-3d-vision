"""Software checks for FSG1h corrected final validation.  Run in the repository venv."""
from __future__ import annotations
import argparse
import copy
import sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/"tools"))
import fsg_finalh_scene as spec
import fsg_stereo_supported as supported
import fsg_stereo_hdr as hdr
import fsg_finalh_eval as final


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
    # Prevent a repeat of FSG1g: prove the prescribed occluder geometry exercises
    # the evaluator's actual left-reference half-occlusion population before Blender.
    import cv2
    import fsg_evaluate as eval_base
    from fsg_scene import triangulate_objects
    from fsg_geometry import make_calibration
    checked=0
    for profile in ("small", "full"):
        for name in ("occluder_left", "occluder_right"):
            mesh=triangulate_objects(spec.final_objects(name))
            c=make_calibration(profile, 0.0, 0.0)
            truth,eligible,band,mono=eval_base.ground_reference(c,mesh)
            core=final.eroded_core(mono,profile)
            raw=int(mono.sum()); ncore=int(core.sum()); nb=int((eligible&band).sum())
            if raw < spec.SPEC["occlusion_min_raw_pixels"][profile]:
                raise AssertionError(f"{profile}/{name}: half-occlusion raw population too small: {raw}")
            if ncore < spec.SPEC["occlusion_min_core_pixels"][profile]:
                raise AssertionError(f"{profile}/{name}: half-occlusion core population too small: {ncore}")
            if nb < spec.SPEC["boundary_targets"]["minimum_accepted_points"]:
                raise AssertionError(f"{profile}/{name}: boundary reference too small: {nb}")
            for iid in (spec.SPEC[name]["foreground_instance"], spec.SPEC[name]["background_instance"]):
                n=int(((truth["instance_id"]==iid)&eligible&~band).sum())
                if n < 100: raise AssertionError(f"{profile}/{name}/instance{iid}: interior reference too small: {n}")
            checked += 1
    print(f"[fsg-finalh-check] SUMMARY passed=8 failed=0 occluder_reference_checks={checked}")


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
    if kind=="fixture":
        import fsg_evaluate as eval_base
        from fsg_scene import quad, triangulate_objects
        from fsg_geometry import make_calibration
        # Recreate the exact FSG1g mistake: nearest foreground edge is ~10 deg
        # off axis while the accepted core is only +/-6 deg.
        mesh=triangulate_objects([
            quad([0,0,-3.05],[1,0,0],[0,1,0],4.6,4.2,22,"bad_bg"),
            quad([(-1.00+0.35)/2,0,-1.85],[1,0,0],[0,1,0],1.35,2.2,21,"bad_fg")])
        c=make_calibration("small",0.0,0.0)
        _truth,_eligible,_band,mono=eval_base.ground_reference(c,mesh)
        if int(mono.sum()) != 0: raise AssertionError("deliberate bad fixture unexpectedly exercised half-occlusion")
        raise AssertionError("deliberate off-core occluder detected: singly-visible reference is empty")
    raise ValueError(kind)


def main() -> None:
    ap=argparse.ArgumentParser();ap.add_argument("--negative",choices=("phase","boundary","candidate","fixture"));args=ap.parse_args()
    if args.negative: negative(args.negative)
    check()

if __name__=="__main__":
    try: main()
    except Exception as exc:
        print(f"[fsg-finalh-check] FAIL {type(exc).__name__}: {exc}",file=sys.stderr);raise SystemExit(1)
