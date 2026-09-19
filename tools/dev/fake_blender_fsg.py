"""TEST ONLY: execute FSG acquisition orchestration without Blender.

Uses an analytic textured-triangle backend. It tests records, masks, rectification
and stereo plumbing, NOT Cycles, Blender optics/API, material appearance, or actual
ray costs. Outputs are prominently marked synthetic_stub; production gates reject
this provenance. No synthetic data are installed or committed to the repository.
"""
from __future__ import annotations
from pathlib import Path
import sys
import time
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import fsg_render
from fsg_geometry import pixels,rays_h
from fsg_scene import case_objects,triangulate_objects,ray_mesh,synthetic_rgb


class SyntheticBackend:
    source="synthetic_stub"
    version="NOT BLENDER: analytic texture-only test backend"
    device="CPU synthetic fixture"
    checks={"independent_blender_checks":False,"fixture_only":True}

    def prepare(self,case,c,folder,spp):
        self.mesh=triangulate_objects(case_objects(case))
        return self.mesh

    def render_eye(self,eye_id,c,folder,spp,seed):
        t0=time.perf_counter(); eye=c["eyes"][eye_id]
        w,h=c["image_size_wh"]
        hit=ray_mesh(np.asarray(eye["centre_h_m"]),rays_h(eye,pixels(w,h)),self.mesh)
        rgb=synthetic_rgb(hit,self.mesh)
        rgb+=np.random.default_rng(seed).normal(0,.001,rgb.shape).astype(np.float32)
        return np.clip(rgb,0,1),time.perf_counter()-t0


def main():
    args=fsg_render.parse_args(sys.argv[1:])
    if args.spp is None: args.spp={"small":64,"full":256}[args.profile]
    fsg_render.acquire(args,SyntheticBackend())


if __name__=="__main__":
    main()
