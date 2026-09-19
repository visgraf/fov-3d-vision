"""Software checks for FSG2 Increment 2. Every negative must actually fail."""
from __future__ import annotations
import argparse,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import fsg2_scene as scene
from fsg2_surface_map import Patch,initialize,fuse,self_test as map_test

def run()->int:
    passed=failed=0
    tests=[]
    tests.append(("scene self test",lambda: scene.self_test()))
    tests.append(("map self test",lambda: map_test()))
    def same_geometry():
        a=scene.scene_objects("fix_left");b=scene.scene_objects("fix_right")
        assert all(np.array_equal(x["vertices_h"],y["vertices_h"]) and x["instance_id"]==y["instance_id"] for x,y in zip(a,b))
    tests.append(("same scene across fixations",same_geometry))
    def fixed_frame():
        assert scene.SPEC["fixed_head_frame"] and scene.SPEC["no_icp"]
    tests.append(("fixed head map frame",fixed_frame))
    for name,fn in tests:
        try:fn();print("[fsg2-check] PASS",name);passed+=1
        except Exception as e:print("[fsg2-check] FAIL",name,type(e).__name__,e);failed+=1
    print(f"[fsg2-check] SUMMARY passed={passed} failed={failed}");return failed

def negative(kind:str)->None:
    rng=np.random.default_rng(9); x=np.c_[rng.uniform(-.1,.1,600),rng.uniform(-.1,.1,600),-2*np.ones(600)]
    a=Patch("A",x,np.ones_like(x)*.3,np.full(600,61));m=initialize(a,61)
    if kind=="shift":
        b=Patch("B",x+np.array([0,0,.05]),np.ones_like(x)*.5,np.full(600,61));_,s=fuse(m,b,61,.012,.012)
        assert s["matched"]>100,"deliberate 5cm shift detected: overlap collapses"
    elif kind=="instance":
        b=Patch("B",x,np.ones_like(x)*.5,np.full(600,62));_,s=fuse(m,b,61,.012,.012)
        assert s["matched"]>100,"deliberate wrong-instance patch detected"
    elif kind=="duplicate":
        b=Patch("A",x+1e-4,np.ones_like(x)*.5,np.full(600,61));m2,s=fuse(m,b,61,.012,.012)
        assert not s["duplicate_patch"],"duplicate patch correctly refused to alter map"
    else: raise ValueError(kind)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--self-test",action="store_true");ap.add_argument("--negative",choices=("shift","instance","duplicate"));a=ap.parse_args()
    if a.negative:
        try:negative(a.negative)
        except Exception as e:print("[fsg2-check] FAIL",type(e).__name__,e);raise SystemExit(1)
        raise SystemExit(0)
    raise SystemExit(run())
if __name__=="__main__":main()
