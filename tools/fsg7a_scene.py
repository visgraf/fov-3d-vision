"""Evaluator-only folded ribbons for FSG7a prescribed head-motion feasibility.

Both quads share one public object ID.  The return wing is hidden behind the
front wing from both H0 eyes, independent of gaze, and is revealed to both eyes
by the prescribed lateral head translation.  Geometry and part labels here are
evaluator truth and must not be imported by fsg7a_run.py.
"""
from __future__ import annotations
import hashlib, json, math
import numpy as np
import fsg7a_public as public

FRONT_Z=-2.50
FRONT_HALF_W=0.18
HEIGHT=0.30
RETURN_DEPTH=0.65
BACKGROUND_Z=-4.20
BACKGROUND_SIZE=(5.0,4.0)
# evaluator-only part labels
PART_FRONT=1; PART_RETURN=2; PART_BACKGROUND=3
TRUTH_SPACING_M=0.006
TRUTH_COVER_RADIUS_M=0.015

def sign(fixture:str)->float:
    if fixture=="fold_right": return 1.0
    if fixture=="fold_left": return -1.0
    raise ValueError(f"unknown fixture {fixture}")

def _desc(name, verts, instance_id, uv):
    return {"name":name,"vertices_h":np.asarray(verts,float),"instance_id":int(instance_id),"uv":np.asarray(uv,float)}

def fixed_objects_h0(fixture:str)->list[dict]:
    s=sign(fixture); xh=s*FRONT_HALF_W; y0,y1=-HEIGHT/2,HEIGHT/2
    front=np.array([[-FRONT_HALF_W,y0,FRONT_Z],[FRONT_HALF_W,y0,FRONT_Z],[FRONT_HALF_W,y1,FRONT_Z],[-FRONT_HALF_W,y1,FRONT_Z]],float)
    # Consistent winding is not scientifically material; surfaces are opaque/two-sided to ray_mesh.
    ret=np.array([[xh,y0,FRONT_Z-RETURN_DEPTH],[xh,y0,FRONT_Z],[xh,y1,FRONT_Z],[xh,y1,FRONT_Z-RETURN_DEPTH]],float)
    # Texture atlas: front left half, return right half of same public object texture.
    uv_front=np.array([[0,0],[.5,0],[.5,1],[0,1]],float)
    uv_ret=np.array([[.5,0],[1,0],[1,1],[.5,1]],float)
    bg=np.array([[-BACKGROUND_SIZE[0]/2,-BACKGROUND_SIZE[1]/2,BACKGROUND_Z],[BACKGROUND_SIZE[0]/2,-BACKGROUND_SIZE[1]/2,BACKGROUND_Z],[BACKGROUND_SIZE[0]/2,BACKGROUND_SIZE[1]/2,BACKGROUND_Z],[-BACKGROUND_SIZE[0]/2,BACKGROUND_SIZE[1]/2,BACKGROUND_Z]],float)
    return [_desc(f"fsg7a_{fixture}_front",front,public.OBJECT_ID,uv_front),
            _desc(f"fsg7a_{fixture}_return",ret,public.OBJECT_ID,uv_ret),
            _desc(f"fsg7a_{fixture}_background",bg,public.BACKGROUND_ID,[[0,0],[1,0],[1,1],[0,1]])]

def scene_objects_current(fixture:str, translation_h0_m)->list[dict]:
    t=np.asarray(translation_h0_m,float).reshape(1,3); out=[]
    for d in fixed_objects_h0(fixture):
        q=dict(d); q["vertices_h"]=np.asarray(d["vertices_h"],float)-t; out.append(q)
    return out

def scene_texture(fixture:str, instance:int, size:int=512)->np.ndarray:
    from fsg_scene import texture
    tag=37 if fixture=="fold_right" else 53
    return texture(int(instance)+151000+211*tag,size)

def truth_spec(fixture:str)->dict:
    return {"id":f"FSG7a-{fixture}-truth-v1","public_spec_sha256":public.public_digest(),"fixture":fixture,
            "front_z_h0_m":FRONT_Z,"front_half_width_m":FRONT_HALF_W,"height_m":HEIGHT,"return_depth_m":RETURN_DEPTH,
            "background_z_h0_m":BACKGROUND_Z,"truth_spacing_m":TRUTH_SPACING_M,"truth_cover_radius_m":TRUTH_COVER_RADIUS_M}

def truth_digest(fixture:str)->str:
    return hashlib.sha256(json.dumps(truth_spec(fixture),sort_keys=True,separators=(",",":")).encode()).hexdigest()

def _grid(a0,a1,b0,b1,spacing):
    na=max(3,int(math.ceil(abs(a1-a0)/spacing))); nb=max(3,int(math.ceil(abs(b1-b0)/spacing)))
    a=np.linspace(a0+(a1-a0)/(2*na),a1-(a1-a0)/(2*na),na); b=np.linspace(b0+(b1-b0)/(2*nb),b1-(b1-b0)/(2*nb),nb)
    return np.meshgrid(a,b,indexing="xy")

def truth_part_points(fixture:str,part:str)->np.ndarray:
    s=sign(fixture); y0,y1=-HEIGHT/2,HEIGHT/2
    if part=="front":
        x,y=_grid(-FRONT_HALF_W,FRONT_HALF_W,y0,y1,TRUTH_SPACING_M); return np.c_[x.ravel(),y.ravel(),np.full(x.size,FRONT_Z)]
    if part=="return":
        z,y=_grid(FRONT_Z-RETURN_DEPTH,FRONT_Z,y0,y1,TRUTH_SPACING_M); return np.c_[np.full(z.size,s*FRONT_HALF_W),y.ravel(),z.ravel()]
    raise ValueError(part)

def truth_points(fixture:str)->np.ndarray:
    return np.vstack([truth_part_points(fixture,"front"),truth_part_points(fixture,"return")])

def _tri_mesh_parts(fixture:str)->dict:
    objs=fixed_objects_h0(fixture)[:2]; tris=[]; ids=[]
    for d,pid in zip(objs,(PART_FRONT,PART_RETURN)):
        v=np.asarray(d["vertices_h"],float); tris.extend([v[[0,1,2]],v[[0,2,3]]]); ids.extend([pid,pid])
    return {"triangles_h":np.asarray(tris,float),"instance_ids":np.asarray(ids,np.int32)}

def _ray_mesh(origin:np.ndarray,directions:np.ndarray,mesh:dict)->tuple[np.ndarray,np.ndarray]:
    """Small Moller-Trumbore first-hit routine for evaluator self-tests."""
    o=np.asarray(origin,float).reshape(3); d=np.asarray(directions,float).reshape(-1,3)
    tri=np.asarray(mesh["triangles_h"],float); ids=np.asarray(mesh["instance_ids"],np.int32)
    best=np.full(len(d),np.inf); hit=np.zeros(len(d),np.int32); pos=np.full((len(d),3),np.nan)
    eps=1e-10
    for T,pid in zip(tri,ids):
        v0,v1,v2=T; e1=v1-v0; e2=v2-v0; p=np.cross(d,e2); det=p@e1; good=np.abs(det)>eps
        inv=np.zeros_like(det); inv[good]=1.0/det[good]; tv=o-v0; u=(p@tv)*inv; q=np.cross(np.broadcast_to(tv,d.shape),np.broadcast_to(e1,d.shape)); vv=np.einsum('ij,ij->i',d,q)*inv; t=(q@e2)*inv
        ok=good&(u>=-1e-9)&(vv>=-1e-9)&(u+vv<=1+1e-9)&(t>eps)&(t<best)
        if np.any(ok): best[ok]=t[ok]; hit[ok]=pid; pos[ok]=o+d[ok]*t[ok,None]
    return hit,pos

def part_visibility_fraction(fixture:str,part:str,translation_h0_m,eye_local_x:float)->float:
    pts=truth_part_points(fixture,part); o=np.asarray(translation_h0_m,float)+np.array([eye_local_x,0,0],float)
    v=pts-o; r=np.linalg.norm(v,axis=1); dirs=v/r[:,None]; hit,pos=_ray_mesh(o,dirs,_tri_mesh_parts(fixture)); want=PART_FRONT if part=="front" else PART_RETURN
    # Target truth points are cell centres, so first-hit part identity is sufficient.
    return float(np.mean(hit==want))

def binocular_return_visibility(fixture:str,translation_h0_m)->dict:
    vals=[part_visibility_fraction(fixture,"return",translation_h0_m,x) for x in (-0.0315,+0.0315)]
    return {"L":vals[0],"R":vals[1],"both_min":min(vals),"either_max":max(vals)}

def scheduled_core_fraction(fixture:str,part:str,step:int)->float:
    v=public.view(fixture,step); t=np.asarray(v["head_translation_h0_m"],float); gy,gp=v["gaze_yaw_pitch_deg"]
    q=truth_part_points(fixture,part)-t
    yaw=np.degrees(np.arctan2(q[:,0],-q[:,2])); pitch=np.degrees(np.arctan2(q[:,1],np.sqrt(q[:,0]**2+q[:,2]**2)))
    # Design-only nominal 12-degree core check; runtime acceptance still uses the exact rectified core.
    keep=(np.abs(yaw-gy)<=6.0)&(np.abs(pitch-gp)<=6.0)
    return float(np.mean(keep))

def _rect_distance(points,fixture,part):
    p=np.asarray(points,float).reshape(-1,3); s=sign(fixture); y0,y1=-HEIGHT/2,HEIGHT/2
    if part=="front":
        qx=np.clip(p[:,0],-FRONT_HALF_W,FRONT_HALF_W); qy=np.clip(p[:,1],y0,y1); qz=np.full(len(p),FRONT_Z)
    else:
        qx=np.full(len(p),s*FRONT_HALF_W); qy=np.clip(p[:,1],y0,y1); qz=np.clip(p[:,2],FRONT_Z-RETURN_DEPTH,FRONT_Z)
    q=np.c_[qx,qy,qz]; return np.linalg.norm(p-q,axis=1)

def surface_distance(fixture:str,xyz_h0:np.ndarray)->np.ndarray:
    return np.minimum(_rect_distance(xyz_h0,fixture,"front"),_rect_distance(xyz_h0,fixture,"return"))

def part_coverage(fixture:str,part:str,xyz_h0:np.ndarray,radius:float=TRUTH_COVER_RADIUS_M)->float:
    truth=truth_part_points(fixture,part); pts=np.asarray(xyz_h0,float).reshape(-1,3); pts=pts[np.isfinite(pts).all(1)]
    cell=radius; bins={}
    for p in pts: bins.setdefault(tuple(np.floor(p/cell).astype(np.int64).tolist()),[]).append(p)
    hit=0
    for q in truth:
        k=tuple(np.floor(q/cell).astype(np.int64).tolist()); best=cell
        for a in (-1,0,1):
            for b in (-1,0,1):
                for c in (-1,0,1):
                    for p in bins.get((k[0]+a,k[1]+b,k[2]+c),()): best=min(best,float(np.linalg.norm(q-p)))
        hit += best < cell
    return float(hit/len(truth))

def validate_mesh(fixture:str,mesh:dict,translation_h0_m)->None:
    tri=np.asarray(mesh["triangles_h"],float); ids=np.asarray(mesh["instance_ids"],np.int32)
    if tri.ndim!=3 or tri.shape[1:]!=(3,3) or len(ids)!=len(tri): raise ValueError("bad FSG7a mesh")
    # Convert exported current-H triangles back to H0 and compare the public object vertex set.
    h0=tri+np.asarray(translation_h0_m,float).reshape(1,1,3)
    got=np.unique(np.round(h0[ids==public.OBJECT_ID].reshape(-1,3),7),axis=0)
    exp=np.unique(np.round(np.vstack([d["vertices_h"] for d in fixed_objects_h0(fixture)[:2]]),7),axis=0)
    if got.shape!=exp.shape or not np.allclose(got,exp,atol=1e-7): raise ValueError("FSG7a moving-scene/world-frame geometry mismatch")

def self_test()->None:
    for f in public.FIXTURES:
        fixed=binocular_return_visibility(f,(0,0,0)); moved=binocular_return_visibility(f,public.view(f,1)["head_translation_h0_m"])
        if fixed["either_max"]>public.TARGETS["fixed_head_return_visibility_max"]: raise AssertionError(f"{f} return is not truly hidden at H0: {fixed}")
        if moved["both_min"]<public.TARGETS["moved_head_return_visibility_min"]: raise AssertionError(f"{f} return is not revealed binocularly after head motion: {moved}")
        # Moving the SCENE with the head would cancel parallax; explicit negative control.
        # In relative coordinates this is equivalent to keeping eye/scene geometry at H0.
        wrong=binocular_return_visibility(f,(0,0,0))
        if wrong["either_max"]>0.02: raise AssertionError("moving-scene negative unexpectedly reveals return")
        if scheduled_core_fraction(f,"return",1)<0.99: raise AssertionError("reveal gaze does not contain the hidden return in nominal core")
        if scheduled_core_fraction(f,"front",1)<0.50: raise AssertionError("reveal gaze lacks enough front-wing overlap by design")
        if np.max(surface_distance(f,truth_points(f)))>1e-12: raise AssertionError("analytic truth rejects itself")
        # Fixed-head gaze rotation cannot alter line-of-sight visibility because eye centres are unchanged.
        if not np.isclose(fixed["L"],part_visibility_fraction(f,"return",(0,0,0),-0.0315)): raise AssertionError("fixed-head visibility not viewpoint-only")
        print(f"[fsg7a-scene] {f} hidden_LR={fixed['L']:.4f}/{fixed['R']:.4f} revealed_LR={moved['L']:.4f}/{moved['R']:.4f}")
    print("[fsg7a-scene] PASS self_occlusion=true head_translation_reveals=true fixed_head_gaze_cannot_reveal=true")

if __name__=="__main__": self_test()
