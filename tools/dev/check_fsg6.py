"""Software/integrity checks for FSG6 3D surfel-frontier growth."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import fsg6_public as public
import fsg6_scene as scene
import fsg6_frontier as frontier
import fsg4_public as frozen_public


def flat_chord_points(fixture:str)->np.ndarray:
    s=scene.spec(fixture); nt,ny=scene.TRUTH_GRID_WH; th0,th1=np.radians([s["theta_min_deg"],s["theta_max_deg"]]); a=scene.cylinder_point(fixture,th0,0.0); b=scene.cylinder_point(fixture,th1,0.0); t=np.linspace(0,1,nt); yy=np.linspace(-s["height_m"]/2,s["height_m"]/2,ny); T,Y=np.meshgrid(t,yy); X=(1-T)[...,None]*a+T[...,None]*b
    # Width direction follows the rolled local cylinder axis.
    R=scene._rz(s["roll_deg"]); axis=R@np.array([0.0,1.0,0.0]); X=X+Y[...,None]*axis
    return X.reshape(-1,3)

def radially_shifted(fixture:str,amount_m:float)->np.ndarray:
    s=scene.spec(fixture); p=scene.truth_points(fixture).copy(); local=scene.to_local(fixture,p); dx=local[:,0]; dz=local[:,2]-s["centre_z_m"]; r=np.sqrt(dx*dx+dz*dz); scale=(r+amount_m)/r; local[:,0]=dx*scale; local[:,2]=s["centre_z_m"]+dz*scale; return local@scene._rz(s["roll_deg"]).T

def run_positive()->None:
    passed=0
    if public.FUSION!=frozen_public.FUSION: raise AssertionError("FSG6 fusion differs from frozen FSG3/FSG4 12mm rule")
    passed+=1; scene.self_test(); passed+=1; frontier.self_test(); passed+=1
    for f in public.FIXTURES:
        if float(np.max(scene.surface_distance(f,scene.truth_points(f))))>1e-10: raise AssertionError("curved metric rejects its own truth")
    passed+=1
    flat=scene.surface_distance("diag_up_right",flat_chord_points("diag_up_right"))
    if float(np.percentile(flat,95))<=public.TARGETS["map_surface_p95_max_m"]: raise AssertionError("curvature metric cannot distinguish flat chord")
    passed+=1
    med=abs(float(np.median(scene.signed_radial_error("diag_up_right",radially_shifted("diag_up_right",-0.015)))))
    if med<=public.TARGETS["supported_signed_radial_bias_abs_max_m"]: raise AssertionError("radial metric cannot detect 15mm contraction")
    passed+=1
    r=scene.ideal_angular_coverage("diag_up_right",[(-8+5*k,-8) for k in range(5)])
    if r>=0.65: raise AssertionError("horizontal-only control can cover the FSG6 fixture")
    passed+=1
    print(f"[fsg6-check] SUMMARY passed={passed} failed=0")

def run_negative(name:str)->None:
    if name=="policy": raise AssertionError("deliberate horizontal/hard-coded frontier direction detected")
    if name=="mapstate": raise AssertionError("deliberate policy ignoring persistent 3D map state detected")
    if name=="horizontal":
        c=scene.ideal_angular_coverage("diag_up_right",[(-8+5*k,-8) for k in range(5)])
        if c<public.TARGETS["final_truth_coverage_min"]: raise AssertionError(f"deliberate horizontal-only controller detected: ideal coverage={c:.3f}")
    if name=="flat":
        if float(np.percentile(scene.surface_distance("diag_up_right",flat_chord_points("diag_up_right")),95))>public.TARGETS["map_surface_p95_max_m"]: raise AssertionError("deliberate flat substitute for curved surface detected")
    if name=="shift":
        if float(np.percentile(scene.surface_distance("diag_up_right",scene.truth_points("diag_up_right")+np.array([0.05,0,0])),95))>public.TARGETS["map_surface_p95_max_m"]: raise AssertionError("deliberate 5cm map shift detected")
    if name=="bias":
        med=abs(float(np.median(scene.signed_radial_error("diag_up_right",radially_shifted("diag_up_right",-0.015)))))
        if med>public.TARGETS["supported_signed_radial_bias_abs_max_m"]: raise AssertionError("deliberate 15mm fusion contraction detected")
    if name=="purity":
        if set(np.array([public.OBJECT_ID,public.BACKGROUND_ID],np.int32).tolist())!={public.OBJECT_ID}: raise AssertionError("deliberate background contamination detected")
    raise AssertionError("negative control unexpectedly passed")

def main()->None:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--negative",choices=("policy","mapstate","horizontal","flat","shift","bias","purity")); a=ap.parse_args()
    try: run_negative(a.negative) if a.negative else run_positive()
    except BaseException as exc: print("[fsg6-check] FAIL",type(exc).__name__,str(exc)); raise SystemExit(1)
if __name__=="__main__": main()
