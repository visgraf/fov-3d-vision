"""Fail-capable software checks for FSG3 Increment 3."""
from __future__ import annotations
import argparse, inspect, sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import fsg3_public as public
import fsg3_scene as scene
import fsg3_policy as policy
from fsg3_surface_map import Patch,initialize,fuse,self_test as map_test


def run()->int:
    passed=failed=0
    tests=[]
    tests.append(("scene self test",scene.self_test));tests.append(("map self test",map_test));tests.append(("policy self test",policy.self_test))
    def truth_free_host():
        import fsg3_loop
        src=inspect.getsource(fsg3_loop)+inspect.getsource(policy)
        assert "import fsg3_scene" not in src and "evaluation_only" not in inspect.getsource(fsg3_loop),"active host/policy can see evaluation geometry"
    tests.append(("active host is truth-free",truth_free_host))
    def public_contract():
        assert public.PUBLIC_SPEC["fixed_head_frame"] and public.PUBLIC_SPEC["oracle_instance_segmentation"] and public.PUBLIC_SPEC["horizontal_frontier_only"]
    tests.append(("public active contract",public_contract))
    for name,fn in tests:
        try:fn();print("[fsg3-check] PASS",name);passed+=1
        except Exception as e:print("[fsg3-check] FAIL",name,type(e).__name__,e);failed+=1
    print(f"[fsg3-check] SUMMARY passed={passed} failed={failed}");return failed

def negative(kind:str)->None:
    if kind=="frontier":
        n=128;ids=np.full((n,n),public.OBJECT_ID,np.int32);sup=np.ones((n,n),bool);c={"nominal_core_fov_deg":12.0}
        yaw=np.radians(np.linspace(-10,4,1500));xyz=np.c_[2*np.sin(yaw),np.zeros_like(yaw),-2*np.cos(yaw)]
        d=policy.choose_next(-2,c,ids,sup,xyz,[-7,-2])
        assert d["next_yaw_deg"]==-7.0,"deliberate hard-coded/wrong frontier direction detected"
    elif kind=="resolved":
        n=128;ids=np.full((n,n),public.OBJECT_ID,np.int32);ids[:,-8:]=0;sup=np.ones((n,n),bool);c={"nominal_core_fov_deg":12.0}
        yaw=np.radians(np.linspace(-10,15,1500));xyz=np.c_[2*np.sin(yaw),np.zeros_like(yaw),-2*np.cos(yaw)]
        d=policy.choose_next(13,c,ids,sup,xyz,[-7,-2,3,8,13])
        assert not d["stop"],"deliberate failure to stop at resolved boundary detected"
    elif kind=="shift":
        rng=np.random.default_rng(4);x=np.c_[rng.uniform(-.1,.1,800),rng.uniform(-.08,.08,800),-2*np.ones(800)]
        a=Patch("A",x,np.ones_like(x)*.3,np.full(800,public.OBJECT_ID));m=initialize(a,public.OBJECT_ID)
        b=Patch("B",x+np.array([0,0,.05]),np.ones_like(x)*.4,np.full(800,public.OBJECT_ID));_,s=fuse(m,b,public.OBJECT_ID,.012,.012)
        assert s["matched"]>100,"deliberate 5cm registration error detected"
    elif kind=="duplicate":
        x=np.c_[np.linspace(-.1,.1,400),np.zeros(400),-2*np.ones(400)];a=Patch("A",x,np.ones_like(x),np.full(400,public.OBJECT_ID));m=initialize(a,public.OBJECT_ID);m2,s=fuse(m,a,public.OBJECT_ID,.012,.012)
        assert not s["duplicate_patch"],"duplicate patch correctly refused to change map"
    else:raise ValueError(kind)

def main()->None:
    ap=argparse.ArgumentParser();ap.add_argument("--self-test",action="store_true");ap.add_argument("--negative",choices=("frontier","resolved","shift","duplicate"));a=ap.parse_args()
    if a.negative:
        try:negative(a.negative)
        except Exception as e:print("[fsg3-check] FAIL",type(e).__name__,e);raise SystemExit(1)
        raise SystemExit(0)
    raise SystemExit(run())
if __name__=="__main__":main()
