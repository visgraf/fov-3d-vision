"""Minimal persistent head-frame surfel map for FSG2.

No truth access.  First patch initializes the map.  A later patch associates only
against the pre-existing map snapshot, so samples from one patch are never collapsed
with each other.  Same-instance + Euclidean proximity are the only association cues.
"""
from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path
import numpy as np

@dataclass
class Patch:
    patch_id: str
    xyz_h: np.ndarray
    rgb: np.ndarray
    instance_id: np.ndarray

@dataclass
class SurfaceMap:
    xyz_h: np.ndarray
    rgb: np.ndarray
    instance_id: np.ndarray
    support_count: np.ndarray
    provenance_mask: np.ndarray
    patch_ids: list[str]


def _clean_patch(p: Patch, wanted_instance: int) -> Patch:
    xyz=np.asarray(p.xyz_h,float).reshape(-1,3); rgb=np.asarray(p.rgb,float).reshape(-1,3); ids=np.asarray(p.instance_id).reshape(-1)
    m=np.isfinite(xyz).all(axis=1)&np.isfinite(rgb).all(axis=1)&(ids==wanted_instance)
    return Patch(p.patch_id,xyz[m],rgb[m],ids[m].astype(np.int32))

def initialize(p: Patch,wanted_instance:int)->SurfaceMap:
    q=_clean_patch(p,wanted_instance)
    if len(q.xyz_h)<100: raise ValueError("too few object points to initialize map")
    return SurfaceMap(q.xyz_h.copy(),q.rgb.copy(),q.instance_id.copy(),np.ones(len(q.xyz_h),np.int16),np.ones(len(q.xyz_h),np.uint64),[q.patch_id])

def _key(x:np.ndarray,cell:float)->tuple[int,int,int]: return tuple(np.floor(x/cell).astype(np.int64).tolist())

def fuse(m:SurfaceMap,p:Patch,wanted_instance:int,radius:float,cell:float)->tuple[SurfaceMap,dict]:
    if p.patch_id in m.patch_ids:
        return SurfaceMap(m.xyz_h.copy(),m.rgb.copy(),m.instance_id.copy(),m.support_count.copy(),m.provenance_mask.copy(),list(m.patch_ids)),{"duplicate_patch":True,"matched":0,"new":0,"distances_m":np.empty(0)}
    q=_clean_patch(p,wanted_instance)
    base_n=len(m.xyz_h); bins={}
    for i,x in enumerate(m.xyz_h): bins.setdefault(_key(x,cell),[]).append(i)
    matched_idx=np.full(len(q.xyz_h),-1,np.int64); dist=np.full(len(q.xyz_h),np.inf,float)
    offsets=[(a,b,c) for a in (-1,0,1) for b in (-1,0,1) for c in (-1,0,1)]
    for j,x in enumerate(q.xyz_h):
        k=_key(x,cell); best=-1; bd=radius
        for o in offsets:
            for i in bins.get((k[0]+o[0],k[1]+o[1],k[2]+o[2]),()):
                if m.instance_id[i]!=wanted_instance: continue
                d=float(np.linalg.norm(x-m.xyz_h[i]))
                if d<bd: bd=d;best=i
        if best>=0: matched_idx[j]=best;dist[j]=bd
    out=SurfaceMap(m.xyz_h.copy(),m.rgb.copy(),m.instance_id.copy(),m.support_count.copy(),m.provenance_mask.copy(),list(m.patch_ids)+[p.patch_id])
    bit=np.uint64(1<<len(m.patch_ids))
    # Multiple new observations may choose the same old surfel; average all contributions once.
    for i in np.unique(matched_idx[matched_idx>=0]):
        js=np.flatnonzero(matched_idx==i); old_xyz=out.xyz_h[i].copy(); old_rgb=out.rgb[i].copy(); neww=float(len(js))
        out.xyz_h[i]=(old_xyz+q.xyz_h[js].sum(axis=0))/(1.0+neww)
        out.rgb[i]=(old_rgb+q.rgb[js].sum(axis=0))/(1.0+neww)
        out.support_count[i]=np.int16(2); out.provenance_mask[i]|=bit
    un=matched_idx<0
    if np.any(un):
        out.xyz_h=np.vstack((out.xyz_h,q.xyz_h[un])); out.rgb=np.vstack((out.rgb,q.rgb[un])); out.instance_id=np.concatenate((out.instance_id,q.instance_id[un])); out.support_count=np.concatenate((out.support_count,np.ones(un.sum(),np.int16))); out.provenance_mask=np.concatenate((out.provenance_mask,np.full(un.sum(),bit,np.uint64)))
    return out,{"duplicate_patch":False,"matched":int((~un).sum()),"new":int(un.sum()),"distances_m":dist[~un],"input_points":int(len(q.xyz_h)),"base_points":int(base_n)}

def save_map(path:Path,m:SurfaceMap)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(path,xyz_h=m.xyz_h.astype(np.float32),rgb=m.rgb.astype(np.float32),instance_id=m.instance_id,support_count=m.support_count,provenance_mask=m.provenance_mask,patch_ids=np.array(m.patch_ids,dtype="U64"))

def self_test()->None:
    rng=np.random.default_rng(4)
    a=np.stack(np.meshgrid(np.linspace(-.2,.05,50),np.linspace(-.1,.1,30)),axis=-1).reshape(-1,2); a=np.c_[a,-2*np.ones(len(a))]
    b=np.stack(np.meshgrid(np.linspace(-.05,.2,50),np.linspace(-.1,.1,30)),axis=-1).reshape(-1,2); b=np.c_[b,-2*np.ones(len(b))]
    a+=rng.normal(scale=.0005,size=a.shape);b+=rng.normal(scale=.0005,size=b.shape)
    pa=Patch("A",a,np.ones_like(a)*.4,np.full(len(a),61));pb=Patch("B",b,np.ones_like(b)*.6,np.full(len(b),61))
    m=initialize(pa,61);m2,s=fuse(m,pb,61,.008,.008)
    if s["matched"]<500 or s["new"]<500: raise AssertionError("synthetic overlap/new support not recovered")
    before=(m2.xyz_h.copy(),m2.support_count.copy());m3,d=fuse(m2,pb,61,.008,.008)
    if not d["duplicate_patch"] or not np.array_equal(before[0],m3.xyz_h) or not np.array_equal(before[1],m3.support_count): raise AssertionError("duplicate patch not idempotent")
    print(f"[fsg2-map] PASS matched={s['matched']} new={s['new']} idempotent=true")

if __name__=="__main__": self_test()
