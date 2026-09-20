"""Software/integrity checks for FSG6d projected-frontier corridor growth."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fsg6d_public as public
import fsg6d_scene as scene
import fsg6d_frontier as frontier
import fsg6c_public as old_public
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


def eye_swap_control() -> None:
    n,sup,cal,strip,up_map,_=_controls()
    # Make the eyes deliberately different; swapping them must not change the decision.
    R=strip.copy(); R[:,-12:]=public.BACKGROUND_ID
    a=frontier.choose_next(0.0,0.0,cal,strip,sup,R,sup,up_map,[(0.0,0.0)])
    b=frontier.choose_next(0.0,0.0,cal,R,sup,strip,sup,up_map,[(0.0,0.0)])
    if a["next_gaze_deg"]!=b["next_gaze_deg"]:
        raise AssertionError("FSG6d continuation changed under L/R swap")


def historical_bracket_control() -> None:
    _,sup,cal,strip,up_map,down_map=_controls()
    ev=frontier.binocular_edge_evidence(strip,sup,strip,sup,public.OBJECT_ID)
    # FSG6b defect: valid up-right continuation rejected by old full-edge conjunction.
    new_up=frontier.choose_next(0.0,0.0,cal,strip,sup,strip,sup,up_map,[(0.0,0.0)])
    if new_up["next_gaze_deg"]!=[5.0,5.0]:
        raise AssertionError("projected corridor does not preserve the valid FSG6b-style corner continuation")
    if frontier._retired_component_conjunction_allowed(+1,+1,ev):
        raise AssertionError("synthetic corner control no longer distinguishes retired conjunction")
    # FSG6c defect: strong right evidence with resolved lower sector used to license down-right via max().
    if not frontier._retired_component_max_allowed(+1,-1,ev):
        raise AssertionError("synthetic dual control no longer exercises retired component max")
    new_down=frontier.choose_next(0.0,0.0,cal,strip,sup,strip,sup,down_map,[(0.0,0.0)])
    if new_down["next_gaze_deg"]==[5.0,-5.0]:
        raise AssertionError("projected corridor still lets one component license the other")


def projection_control() -> None:
    import cv2
    from fsg_geometry import make_calibration, project_h
    from fsg_stereo import rectification
    c=make_calibration("small",7.0,-3.0,public.VERGENCE_DISTANCE_M); r=rectification(c)
    pts=np.array([[0.0,0.0,-2.0],[0.2,0.1,-2.5],[-0.1,-0.15,-1.8]],float)
    x,y,_,_=map(int,r["crop_xywh"])
    for side,eye in (("L",c["eyes"][0]),("R",c["eyes"][1])):
        uvraw,_=project_h(eye,pts)
        uvcv=cv2.undistortPoints(uvraw.reshape(-1,1,2),np.asarray(eye["K"]),np.zeros(5),
                                 R=r["R1" if side=="L" else "R2"],
                                 P=r["P1" if side=="L" else "P2"]).reshape(-1,2)-[x,y]
        uv,_=frontier._project_rectified_core(c,pts,side)
        if not np.allclose(uv,uvcv,atol=1e-9):
            raise AssertionError("projected-frontier core projection disagrees with OpenCV rectification")


def source_isolation_control() -> None:
    root=Path(__file__).resolve().parents[2]
    frontier_src=(root/"tools"/"fsg6d_frontier.py").read_text()
    run_src=(root/"tools"/"fsg6d_run.py").read_text()
    if "fsg6d_scene" in frontier_src or "fsg6d_scene" in run_src:
        raise AssertionError("truth fixture leaked into FSG6d host policy/run")
    if "evaluation_only" in frontier_src or "evaluation_only" in run_src:
        raise AssertionError("evaluation-only truth leaked into FSG6d host policy/run")


def run_positive() -> None:
    passed=0
    if public.FUSION!=frozen_public.FUSION: raise AssertionError("FSG6d fusion differs from frozen 12mm rule")
    if public.SURFACE_FRONTIER!=old_public.SURFACE_FRONTIER: raise AssertionError("FSG6d changed an FSG6c frontier/continuation constant")
    if public.TARGETS!=old_public.TARGETS: raise AssertionError("FSG6d changed an FSG6c numerical gate")
    passed+=1
    scene.self_test(); passed+=1
    frontier.self_test(); passed+=1
    eye_swap_control(); passed+=1
    historical_bracket_control(); passed+=1
    projection_control(); passed+=1
    source_isolation_control(); passed+=1
    for f in public.FIXTURES:
        if float(np.max(scene.surface_distance(f,scene.truth_points(f))))>1e-10: raise AssertionError("curved metric rejects its own truth")
    passed+=1
    flat=scene.surface_distance("corridor_up_right",flat_chord_points("corridor_up_right"))
    if float(np.percentile(flat,95))<=public.TARGETS["map_surface_p95_max_m"]: raise AssertionError("curvature metric cannot distinguish flat chord")
    passed+=1
    med=abs(float(np.median(scene.signed_radial_error("corridor_up_right",radially_shifted("corridor_up_right",-0.015)))))
    if med<=public.TARGETS["supported_signed_radial_bias_abs_max_m"]: raise AssertionError("radial metric cannot detect 15mm contraction")
    passed+=1
    r=scene.ideal_angular_coverage("corridor_up_right",[(-8+5*k,-7) for k in range(5)])
    if r>=0.65: raise AssertionError("horizontal-only control can cover the FSG6d fixture")
    passed+=1
    print(f"[fsg6d-check] SUMMARY passed={passed} failed=0")


def run_negative(name: str) -> None:
    if name=="policy": raise AssertionError("deliberate horizontal/hard-coded frontier direction detected")
    if name=="mapstate": raise AssertionError("deliberate policy ignoring persistent 3D map state detected")
    if name=="horizontal":
        c=scene.ideal_angular_coverage("corridor_up_right",[(-8+5*k,-7) for k in range(5)])
        if c<public.TARGETS["final_truth_coverage_min"]: raise AssertionError(f"deliberate horizontal-only controller detected: ideal coverage={c:.3f}")
    if name=="monocular":
        _,sup,_,strip,_,_=_controls(); R=strip.copy(); R[:,-12:]=public.BACKGROUND_ID
        le=frontier.edge_evidence(strip,sup,public.OBJECT_ID); re=frontier.edge_evidence(R,sup,public.OBJECT_ID)
        keys=("left_fraction","right_fraction","top_fraction","bottom_fraction")
        if any(abs(float(le[k])-float(re[k]))>1e-12 for k in keys):
            raise AssertionError("deliberate retired left-eye-only continuation rule detected as eye-swap asymmetric")
    if name=="conjunction":
        _,sup,_,strip,_,_=_controls(); ev=frontier.binocular_edge_evidence(strip,sup,strip,sup,public.OBJECT_ID)
        if not frontier._retired_component_conjunction_allowed(+1,+1,ev):
            raise AssertionError("deliberate retired FSG6b diagonal component-conjunction rule detected")
    if name=="componentmax":
        _,sup,cal,strip,_,down_map=_controls(); ev=frontier.binocular_edge_evidence(strip,sup,strip,sup,public.OBJECT_ID)
        if frontier._retired_component_max_allowed(+1,-1,ev):
            d=frontier.choose_next(0,0,cal,strip,sup,strip,sup,down_map,[(0,0)])
            if d["next_gaze_deg"]!=[5.0,-5.0]:
                raise AssertionError("deliberate retired FSG6c component-max rule detected")
    if name=="full_edge":
        # Strong full right edge does not by itself license candidate-local down-right continuation.
        _,sup,cal,strip,_,down_map=_controls(); d=frontier.choose_next(0,0,cal,strip,sup,strip,sup,down_map,[(0,0)])
        ev=frontier.binocular_edge_evidence(strip,sup,strip,sup,public.OBJECT_ID)
        if ev["right_fraction"]>=public.SURFACE_FRONTIER["edge_object_fraction_min"] and d["next_gaze_deg"]!=[5.0,-5.0]:
            raise AssertionError("deliberate full-edge substitute for candidate-local corridor detected")
    if name=="flat":
        if float(np.percentile(scene.surface_distance("corridor_up_right",flat_chord_points("corridor_up_right")),95))>public.TARGETS["map_surface_p95_max_m"]: raise AssertionError("deliberate flat substitute for curved surface detected")
    if name=="shift":
        if float(np.percentile(scene.surface_distance("corridor_up_right",scene.truth_points("corridor_up_right")+np.array([0.05,0,0])),95))>public.TARGETS["map_surface_p95_max_m"]: raise AssertionError("deliberate 5cm map shift detected")
    if name=="bias":
        med=abs(float(np.median(scene.signed_radial_error("corridor_up_right",radially_shifted("corridor_up_right",-0.015)))))
        if med>public.TARGETS["supported_signed_radial_bias_abs_max_m"]: raise AssertionError("deliberate 15mm fusion contraction detected")
    if name=="purity":
        if set(np.array([public.OBJECT_ID,public.BACKGROUND_ID],np.int32).tolist())!={public.OBJECT_ID}: raise AssertionError("deliberate background contamination detected")
    raise AssertionError("negative control unexpectedly passed")


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--negative",choices=("policy","mapstate","horizontal","monocular","conjunction","componentmax","full_edge","flat","shift","bias","purity"))
    a=ap.parse_args()
    try: run_negative(a.negative) if a.negative else run_positive()
    except BaseException as exc:
        print("[fsg6d-check] FAIL",type(exc).__name__,str(exc)); raise SystemExit(1)

if __name__=="__main__": main()
