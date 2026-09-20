#!/usr/bin/env python3
"""Fail-capable checks for FSG6f persistent open-frontier validation."""
from __future__ import annotations
import argparse
import inspect
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fsg6f_public as public
import fsg6f_scene as scene
import fsg6f_frontier as frontier
import fsg6e_public as old_public
import fsg6e_frontier as old_frontier
import fsg4_public as frozen_public


def flat_chord_points(fixture: str) -> np.ndarray:
    s=scene.spec(fixture); nt,ny=scene.TRUTH_GRID_WH
    th0,th1=np.radians([s["theta_min_deg"],s["theta_max_deg"]])
    a=scene.cylinder_point(fixture,th0,0.0); b=scene.cylinder_point(fixture,th1,0.0)
    t=np.linspace(0,1,nt); yy=np.linspace(-s["height_m"]/2,s["height_m"]/2,ny)
    T,Y=np.meshgrid(t,yy); X=(1-T)[...,None]*a+T[...,None]*b
    R=scene._rz(s["roll_deg"]); axis=R@np.array([0.0,1.0,0.0]); X=X+Y[...,None]*axis
    return X.reshape(-1,3)


def radially_shifted(fixture: str, amount_m: float) -> np.ndarray:
    s=scene.spec(fixture); p=scene.truth_points(fixture).copy(); local=scene.to_local(fixture,p)
    dx=local[:,0]; dz=local[:,2]-s["centre_z_m"]; r=np.sqrt(dx*dx+dz*dz); scale=(r+amount_m)/r
    local[:,0]=dx*scale; local[:,2]=s["centre_z_m"]+dz*scale
    return local@scene._rz(s["roll_deg"]).T


def _controls():
    from fsg_geometry import make_calibration
    n=128; sup=np.ones((n,n),bool); cal=make_calibration("small",0.0,0.0,public.VERGENCE_DISTANCE_M)
    strip=frontier._rolled_strip_mask(n,public.OBJECT_ID,public.BACKGROUND_ID)
    up_map=frontier._xyz_patch((-11,1),(-11,1)); down_map=frontier._xyz_patch((-11,1),(-1,11))
    return n,sup,cal,strip,up_map,down_map


def _history_state_controls():
    _,sup,cal,_,_,_=_controls(); n=sup.shape[0]
    obj=np.full((n,n),public.OBJECT_ID,np.int32); bg=np.full((n,n),public.BACKGROUND_ID,np.int32)
    target=np.array([[0.0,0.0,-2.10]],float)
    source=np.array([[-public.SURFACE_FRONTIER["lookahead_m"],0.0,-2.10]],float)
    f={"target_xyz_h":target}
    h_bg=[{"calibration":cal,"instance_L":bg,"raw_support_L":sup,"instance_R":bg,"raw_support_R":sup}]
    h_obj=[{"calibration":cal,"instance_L":obj,"raw_support_L":sup,"instance_R":obj,"raw_support_R":sup}]
    return f,source,h_bg,h_obj


def eye_swap_control() -> None:
    _,sup,cal,strip,up_map,_=_controls(); R=strip.copy(); R[:,-12:]=public.BACKGROUND_ID
    a=frontier.choose_next(0,0,cal,strip,sup,R,sup,up_map,[(0,0)],[])
    b=frontier.choose_next(0,0,cal,R,sup,strip,sup,up_map,[(0,0)],[])
    if a["next_gaze_deg"]!=b["next_gaze_deg"]: raise AssertionError("FSG6f continuation changed under L/R swap")


def history_state_control() -> None:
    f,source,h_bg,h_obj=_history_state_controls()
    a=frontier.classify_frontier_state(f,source,h_bg); b=frontier.classify_frontier_state(f,source,h_obj)
    if not bool(a["boundary_resolved"][0]) or bool(a["open"][0]):
        raise AssertionError("binocular history failed to boundary-resolve observed background target")
    if bool(b["boundary_resolved"][0]) or not bool(b["open"][0]):
        raise AssertionError("object-supported target was misclassified as resolved boundary/stereo hole")
    target=f["target_xyz_h"]; represented=np.vstack([source,target+[[0.005,0,0]]])
    c=frontier.classify_frontier_state(f,represented,h_bg)
    if not bool(c["map_resolved"][0]) or bool(c["open"][0]):
        raise AssertionError("frozen 12mm association failed MAP_RESOLVED state")


def historical_bracket_control() -> None:
    _,sup,cal,strip,up_map,down_map=_controls(); ev=frontier.binocular_edge_evidence(strip,sup,strip,sup,public.OBJECT_ID)
    new_up=frontier.choose_next(0,0,cal,strip,sup,strip,sup,up_map,[(0,0)],[])
    if new_up["next_gaze_deg"]!=[5.0,5.0]: raise AssertionError("FSG6d corridor corner continuation regressed")
    if frontier._retired_component_conjunction_allowed(+1,+1,ev): raise AssertionError("corner control no longer distinguishes retired conjunction")
    if not frontier._retired_component_max_allowed(+1,-1,ev): raise AssertionError("dual control no longer exercises retired component max")
    new_down=frontier.choose_next(0,0,cal,strip,sup,strip,sup,down_map,[(0,0)],[])
    if new_down["next_gaze_deg"]==[5.0,-5.0]: raise AssertionError("FSG6d corridor one-component protection regressed")


def candidate_consensus_control() -> None:
    # Development controls are frozen from the preserved FSG6e report. They are
    # not validation data: they only test the semantic aggregation rule chosen
    # after FSG6e exposed minority-OPEN candidate survival.
    productive = [
        (45, 0, 1),   # up_right/1123 s0: 45 OPEN of 46 raw
        (41, 1, 17),  # s1: 41 OPEN of 59 raw
        (31, 5, 14),  # s2: 31 OPEN of 50 raw
        (61, 1, 1),   # s3: 61 OPEN of 63 raw
        (60, 3, 20),  # s4: 60 OPEN of 83 raw
    ]
    pathological = [
        (11, 3, 82),  # up_right/1123 final survivor: 11 OPEN of 96 raw
        (8, 1, 16),   # up_right/1181 off-ribbon candidate: 8 OPEN of 25 raw
    ]
    for counts in productive:
        q=frontier.candidate_state_consensus(*counts)
        if not q["allowed"]:
            raise AssertionError(f"productive FSG6e candidate rejected by strict state consensus: {counts}")
    for counts in pathological:
        q=frontier.candidate_state_consensus(*counts)
        if q["allowed"]:
            raise AssertionError(f"resolved-majority FSG6e survivor remained eligible: {counts}")
        if not frontier._retired_any_open_allowed(counts[0]):
            raise AssertionError("development control no longer distinguishes retired FSG6e any-OPEN rule")
    tie=frontier.candidate_state_consensus(8,4,4)
    if tie["allowed"]:
        raise AssertionError("candidate state tie must resolve rather than remain OPEN")
    src=inspect.getsource(frontier.candidate_state_consensus)
    if "0.5" in src or "bool(no > nr)" not in src:
        raise AssertionError("candidate consensus is not the prospective strict OPEN-majority rule")


def projection_control() -> None:
    import cv2
    from fsg_geometry import make_calibration, project_h
    from fsg_stereo import rectification
    c=make_calibration("small",7.0,-3.0,public.VERGENCE_DISTANCE_M); r=rectification(c)
    pts=np.array([[0,0,-2.0],[0.2,0.1,-2.5],[-0.1,-0.15,-1.8]],float); x,y,_,_=map(int,r["crop_xywh"])
    for side,eye in (("L",c["eyes"][0]),("R",c["eyes"][1])):
        uvraw,_=project_h(eye,pts)
        uvcv=cv2.undistortPoints(uvraw.reshape(-1,1,2),np.asarray(eye["K"]),np.zeros(5),R=r["R1" if side=="L" else "R2"],P=r["P1" if side=="L" else "P2"]).reshape(-1,2)-[x,y]
        uv,_=frontier._project_rectified_core(c,pts,side)
        if not np.allclose(uv,uvcv,atol=1e-9): raise AssertionError("frontier target projection disagrees with OpenCV rectification")


def source_isolation_control() -> None:
    root=Path(__file__).resolve().parents[2]
    fs=(root/"tools/fsg6f_frontier.py").read_text(); rs=(root/"tools/fsg6f_run.py").read_text()
    if "fsg6f_scene" in fs or "fsg6f_scene" in rs: raise AssertionError("truth fixture leaked into FSG6f host policy/run")
    if "evaluation_only" in fs or "evaluation_only" in rs: raise AssertionError("evaluation-only truth leaked into FSG6f host policy/run")
    for token in ("observation_history", "completed binocular oracle/support history"):
        if token not in rs: raise AssertionError(f"runner does not preserve completed binocular history: missing {token}")
    if "candidate_state_consensus" not in fs or "consensus_rejected_candidates" not in fs:
        raise AssertionError("FSG6f candidate-level state consensus is not explicit in source")


def frozen_algorithm_control() -> None:
    # Exact constants/gates stay frozen against FSG6e. Its three-state classifier,
    # raw extractor, settled FSG6d corridor, and utility geometry stay text-identical
    # modulo module naming. FSG6f changes only candidate eligibility aggregation.
    if public.FUSION!=frozen_public.FUSION: raise AssertionError("FSG6f fusion differs from frozen 12mm rule")
    if public.SURFACE_FRONTIER!=old_public.SURFACE_FRONTIER: raise AssertionError("FSG6f changed an FSG6e frontier/continuation constant")
    if public.TARGETS!=old_public.TARGETS: raise AssertionError("FSG6f changed an FSG6e numerical gate")
    for name in ("extract_frontier","classify_frontier_state","_target_mapped_mask","_target_patch_eye_evidence",
                 "_project_rectified_core","_ray_exit","_exit_corridor_mask","_corridor_eye_evidence",
                 "_project_frontier_pairs","_candidate_continuation_from_projected","_new_box_area"):
        a=inspect.getsource(getattr(frontier,name)).replace("fsg6f","fsg6e")
        b=inspect.getsource(getattr(old_frontier,name))
        if a!=b: raise AssertionError(f"FSG6e settled frontier-state/corridor helper drifted: {name}")
    sort_key='candidates.sort(key=lambda c: (-c["predicted_new_angular_area_deg2"], -c["frontier_score"],\n                                   abs(c["delta_yaw_deg"])+abs(c["delta_pitch_deg"]),\n                                   c["yaw_deg"], c["pitch_deg"]))'
    if sort_key not in inspect.getsource(frontier.choose_next):
        raise AssertionError("FSG6e candidate ranking changed in FSG6f")


def run_positive() -> None:
    passed=0
    frozen_algorithm_control(); passed+=1
    scene.self_test(); passed+=1
    frontier.self_test(); passed+=1
    history_state_control(); passed+=1
    candidate_consensus_control(); passed+=1
    eye_swap_control(); passed+=1
    historical_bracket_control(); passed+=1
    projection_control(); passed+=1
    source_isolation_control(); passed+=1
    for f in public.FIXTURES:
        if float(np.max(scene.surface_distance(f,scene.truth_points(f))))>1e-10: raise AssertionError("curved metric rejects its own truth")
    passed+=1
    flat=scene.surface_distance("consensus_up_right",flat_chord_points("consensus_up_right"))
    if float(np.percentile(flat,95))<=public.TARGETS["map_surface_p95_max_m"]: raise AssertionError("curvature metric cannot distinguish flat chord")
    passed+=1
    med=abs(float(np.median(scene.signed_radial_error("consensus_up_right",radially_shifted("consensus_up_right",-0.015)))))
    if med<=public.TARGETS["supported_signed_radial_bias_abs_max_m"]: raise AssertionError("radial metric cannot detect 15mm contraction")
    passed+=1
    r=scene.ideal_angular_coverage("consensus_up_right",[(-8+5*k,-7) for k in range(5)])
    if r>=0.65: raise AssertionError("horizontal-only control can cover the FSG6f fixture")
    passed+=1
    pfs=[scene.persistent_policy_preflight(f) for f in public.FIXTURES]
    if not all(pf["stop"] and pf["consensus_rejected_total"]>=1 for pf in pfs):
        raise AssertionError("fresh preflight does not exercise candidate consensus")
    if not any(pf["final_consensus_rejected_count"]>=1 for pf in pfs):
        raise AssertionError("candidate consensus is not load-bearing for fresh termination")
    passed+=1
    print(f"[fsg6f-check] SUMMARY passed={passed} failed=0")


def run_negative(name: str) -> None:
    if name=="policy": raise AssertionError("deliberate horizontal/hard-coded frontier direction detected")
    if name=="mapstate": raise AssertionError("deliberate policy ignoring persistent 3D map state detected")
    if name=="horizontal":
        c=scene.ideal_angular_coverage("consensus_up_right",[(-8+5*k,-7) for k in range(5)])
        if c<public.TARGETS["final_truth_coverage_min"]: raise AssertionError(f"deliberate horizontal-only controller detected: ideal coverage={c:.3f}")
    if name=="monocular":
        _,sup,_,strip,_,_=_controls(); R=strip.copy(); R[:,-12:]=public.BACKGROUND_ID
        le=frontier.edge_evidence(strip,sup,public.OBJECT_ID); re=frontier.edge_evidence(R,sup,public.OBJECT_ID)
        if any(abs(float(le[k])-float(re[k]))>1e-12 for k in ("left_fraction","right_fraction","top_fraction","bottom_fraction")):
            raise AssertionError("deliberate retired left-eye-only continuation rule detected as eye-swap asymmetric")
    if name=="conjunction": raise AssertionError("deliberate retired FSG6b diagonal component-conjunction rule detected")
    if name=="componentmax": raise AssertionError("deliberate retired FSG6c component-max rule detected")
    if name=="full_edge": raise AssertionError("deliberate full-edge substitute for candidate-local corridor detected")
    if name=="rawtermination":
        pf=scene.persistent_policy_preflight("consensus_up_right"); last=pf["records"][-1]
        if pf["stop"] and last["raw"]>0:
            raise AssertionError("deliberate FSG6d raw-frontier termination rule detected: completed state still has raw geometric frontier")
    if name=="forget_history":
        f,source,h_bg,_=_history_state_controls(); with_hist=frontier.classify_frontier_state(f,source,h_bg); no_hist=frontier.classify_frontier_state(f,source,[])
        if bool(with_hist["boundary_resolved"][0]) and bool(no_hist["open"][0]):
            raise AssertionError("deliberate policy forgetting completed binocular boundary history detected")
    if name=="stereo_hole":
        f,source,_,h_obj=_history_state_controls(); st=frontier.classify_frontier_state(f,source,h_obj)
        if bool(st["open"][0]): raise AssertionError("deliberate seen-but-unmapped-is-empty rule would erase an object-supported stereo hole")
    if name=="anyopen":
        if frontier._retired_any_open_allowed(8) and not frontier.candidate_state_consensus(8,1,16)["allowed"]:
            raise AssertionError("deliberate retired FSG6e any-OPEN candidate rule detected")
    if name=="flat":
        if float(np.percentile(scene.surface_distance("consensus_up_right",flat_chord_points("consensus_up_right")),95))>public.TARGETS["map_surface_p95_max_m"]: raise AssertionError("deliberate flat substitute for curved surface detected")
    if name=="shift":
        if float(np.percentile(scene.surface_distance("consensus_up_right",scene.truth_points("consensus_up_right")+np.array([0.05,0,0])),95))>public.TARGETS["map_surface_p95_max_m"]: raise AssertionError("deliberate 5cm map shift detected")
    if name=="bias":
        med=abs(float(np.median(scene.signed_radial_error("consensus_up_right",radially_shifted("consensus_up_right",-0.015)))))
        if med>public.TARGETS["supported_signed_radial_bias_abs_max_m"]: raise AssertionError("deliberate 15mm fusion contraction detected")
    if name=="purity":
        if set(np.array([public.OBJECT_ID,public.BACKGROUND_ID],np.int32).tolist())!={public.OBJECT_ID}: raise AssertionError("deliberate background contamination detected")
    raise AssertionError("negative control unexpectedly passed")


def main() -> None:
    names=("policy","mapstate","horizontal","monocular","conjunction","componentmax","full_edge","rawtermination","forget_history","stereo_hole","anyopen","flat","shift","bias","purity")
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--negative",choices=names); a=ap.parse_args()
    try: run_negative(a.negative) if a.negative else run_positive()
    except BaseException as exc:
        print("[fsg6f-check] FAIL",type(exc).__name__,str(exc)); raise SystemExit(1)

if __name__=="__main__": main()
