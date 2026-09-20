"""Evaluator-only geometry for Stage II / Scene-1a small static scenes.

Each fixture contains three non-occluding known objects: one planar patch and two
convex cylindrical ribbons.  Rendering uses quads/strip meshes; evaluation uses
analytic plane/cylinder surfaces.  Prediction-side code must not import this file.
"""
from __future__ import annotations
import hashlib
import json
import math
import numpy as np
from fsg_scene import quad, texture
import scene1a_public as public

BACKGROUND_Z_M = -4.0
BACKGROUND_SIZE_M = (5.2, 4.0)
CYLINDER_STRIPS = 48
TRUTH_COVER_RADIUS_M = 0.015
PLANE_GRID_WH = (192, 96)
CYL_GRID_WH = (224, 72)

FIXTURE = {
    "triad_a": {
        201: {"type": "plane", "yaw_deg": -15.0, "pitch_deg": +8.0, "depth_m": 2.12,
              "width_m": 0.55, "height_m": 0.30, "roll_deg": +10.0, "texture_tag": 11},
        202: {"type": "cylinder", "yaw_deg": 0.0, "pitch_deg": -10.0,
              "centre_z_local_m": -2.82, "radius_m": 0.72, "theta_min_deg": -42.0,
              "theta_max_deg": +48.0, "height_m": 0.22, "roll_deg": -12.0, "texture_tag": 17},
        203: {"type": "cylinder", "yaw_deg": +14.0, "pitch_deg": +8.0,
              "centre_z_local_m": -2.76, "radius_m": 0.68, "theta_min_deg": -38.0,
              "theta_max_deg": +35.0, "height_m": 0.22, "roll_deg": +18.0, "texture_tag": 23},
    },
    "triad_b": {
        201: {"type": "plane", "yaw_deg": +14.0, "pitch_deg": +8.0, "depth_m": 2.06,
              "width_m": 0.56, "height_m": 0.31, "roll_deg": -20.0, "texture_tag": 29},
        202: {"type": "cylinder", "yaw_deg": -13.5, "pitch_deg": +7.5,
              "centre_z_local_m": -2.78, "radius_m": 0.69, "theta_min_deg": -38.0,
              "theta_max_deg": +36.0, "height_m": 0.22, "roll_deg": +12.0, "texture_tag": 31},
        203: {"type": "cylinder", "yaw_deg": 0.0, "pitch_deg": -9.5,
              "centre_z_local_m": -2.84, "radius_m": 0.73, "theta_min_deg": -40.0,
              "theta_max_deg": +44.0, "height_m": 0.20, "roll_deg": -22.0, "texture_tag": 37},
    },
}


def spec(fixture: str, object_id: int) -> dict:
    if fixture not in public.FIXTURES or object_id not in public.OBJECT_IDS:
        raise ValueError("unknown Scene-1a fixture/object")
    return FIXTURE[fixture][int(object_id)]


def _frame(yaw_deg: float, pitch_deg: float, roll_deg: float) -> np.ndarray:
    """Columns are local +X, +Y, +Z axes expressed in fixed head frame H."""
    y = math.radians(float(yaw_deg)); p = math.radians(float(pitch_deg))
    d = np.array([math.cos(p) * math.sin(y), math.sin(p), -math.cos(p) * math.cos(y)], float)
    right = np.cross(d, np.array([0.0, 1.0, 0.0])); right /= np.linalg.norm(right)
    up = np.cross(right, d); up /= np.linalg.norm(up)
    r = math.radians(float(roll_deg)); cr, sr = math.cos(r), math.sin(r)
    rr = cr * right + sr * up
    uu = -sr * right + cr * up
    return np.column_stack((rr, uu, -d))


def _to_world(fixture: str, object_id: int, xyz_local: np.ndarray) -> np.ndarray:
    s = spec(fixture, object_id)
    return np.asarray(xyz_local, float).reshape(-1, 3) @ _frame(s["yaw_deg"], s["pitch_deg"], s["roll_deg"]).T


def _to_local(fixture: str, object_id: int, xyz_h: np.ndarray) -> np.ndarray:
    s = spec(fixture, object_id)
    return np.asarray(xyz_h, float).reshape(-1, 3) @ _frame(s["yaw_deg"], s["pitch_deg"], s["roll_deg"])


def _plane_vertices(fixture: str, object_id: int) -> np.ndarray:
    s = spec(fixture, object_id); w, h, d = s["width_m"], s["height_m"], s["depth_m"]
    local = np.array([[-w/2,-h/2,-d],[+w/2,-h/2,-d],[+w/2,+h/2,-d],[-w/2,+h/2,-d]], float)
    return _to_world(fixture, object_id, local)


def _cylinder_point_local(s: dict, theta_rad: np.ndarray, y_m: np.ndarray | float) -> np.ndarray:
    th = np.asarray(theta_rad, float); yy = np.asarray(y_m, float); th, yy = np.broadcast_arrays(th, yy)
    return np.stack((s["radius_m"] * np.sin(th), yy,
                     s["centre_z_local_m"] + s["radius_m"] * np.cos(th)), axis=-1)


def _cylinder_strip(fixture: str, object_id: int, j: int) -> dict:
    s = spec(fixture, object_id)
    a0 = math.radians(s["theta_min_deg"] + (s["theta_max_deg"] - s["theta_min_deg"]) * j / CYLINDER_STRIPS)
    a1 = math.radians(s["theta_min_deg"] + (s["theta_max_deg"] - s["theta_min_deg"]) * (j + 1) / CYLINDER_STRIPS)
    y0, y1 = -s["height_m"] / 2.0, s["height_m"] / 2.0
    local = np.array([_cylinder_point_local(s, a0, y0), _cylinder_point_local(s, a1, y0),
                      _cylinder_point_local(s, a1, y1), _cylinder_point_local(s, a0, y1)], float).reshape(4,3)
    u0, u1 = j / CYLINDER_STRIPS, (j + 1) / CYLINDER_STRIPS
    return {"name": f"scene1a_{fixture}_{object_id}_strip_{j:02d}", "vertices_h": _to_world(fixture, object_id, local),
            "instance_id": int(object_id), "uv": np.array([[u0,0],[u1,0],[u1,1],[u0,1]], float)}


def scene_objects(fixture: str) -> list[dict]:
    out = []
    for oid in public.OBJECT_IDS:
        s = spec(fixture, oid)
        if s["type"] == "plane":
            out.append({"name": f"scene1a_{fixture}_{oid}_plane", "vertices_h": _plane_vertices(fixture, oid),
                        "instance_id": int(oid), "uv": np.array([[0,0],[1,0],[1,1],[0,1]], float)})
        elif s["type"] == "cylinder":
            out.extend(_cylinder_strip(fixture, oid, j) for j in range(CYLINDER_STRIPS))
        else:
            raise ValueError("unknown object type")
    out.append(quad([0.0,0.0,BACKGROUND_Z_M],[1,0,0],[0,1,0],BACKGROUND_SIZE_M[0],BACKGROUND_SIZE_M[1],
                    public.BACKGROUND_ID,f"scene1a_{fixture}_background"))
    return out


def scene_texture(fixture: str, instance: int, size: int = 512) -> np.ndarray:
    if instance == public.BACKGROUND_ID:
        tag = 97
    else:
        tag = int(spec(fixture, int(instance))["texture_tag"])
    return texture(int(instance) + 151000 + 193 * tag, size)


def truth_points(fixture: str, object_id: int) -> np.ndarray:
    s = spec(fixture, object_id)
    if s["type"] == "plane":
        nx, ny = PLANE_GRID_WH
        x = np.linspace(-s["width_m"]/2, s["width_m"]/2, nx)
        y = np.linspace(-s["height_m"]/2, s["height_m"]/2, ny)
        X,Y = np.meshgrid(x,y)
        local = np.c_[X.ravel(),Y.ravel(),np.full(X.size,-s["depth_m"])]
    else:
        nt, ny = CYL_GRID_WH
        th = np.radians(np.linspace(s["theta_min_deg"], s["theta_max_deg"], nt))
        y = np.linspace(-s["height_m"]/2, s["height_m"]/2, ny)
        T,Y = np.meshgrid(th,y)
        local = _cylinder_point_local(s,T,Y).reshape(-1,3)
    return _to_world(fixture, object_id, local)


def angular_coordinates(xyz_h: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
    p = np.asarray(xyz_h,float).reshape(-1,3)
    yaw = np.degrees(np.arctan2(p[:,0],-p[:,2]))
    pitch = np.degrees(np.arctan2(p[:,1],np.sqrt(p[:,0]**2+p[:,2]**2)))
    return yaw,pitch


def angular_bounds(fixture: str, object_id: int) -> tuple[float,float,float,float]:
    y,p = angular_coordinates(truth_points(fixture,object_id))
    return float(y.min()),float(y.max()),float(p.min()),float(p.max())


def surface_distance(fixture: str, object_id: int, xyz_h: np.ndarray) -> np.ndarray:
    s = spec(fixture,object_id); p = _to_local(fixture,object_id,xyz_h)
    if s["type"] == "plane":
        q = np.c_[np.clip(p[:,0],-s["width_m"]/2,s["width_m"]/2),
                  np.clip(p[:,1],-s["height_m"]/2,s["height_m"]/2),
                  np.full(len(p),-s["depth_m"])]
    else:
        th = np.arctan2(p[:,0],p[:,2]-s["centre_z_local_m"])
        tc = np.clip(th,math.radians(s["theta_min_deg"]),math.radians(s["theta_max_deg"]))
        yc = np.clip(p[:,1],-s["height_m"]/2,s["height_m"]/2)
        q = np.c_[s["radius_m"]*np.sin(tc),yc,s["centre_z_local_m"]+s["radius_m"]*np.cos(tc)]
    return np.linalg.norm(p-q,axis=1)


def signed_radial_error(fixture: str, object_id: int, xyz_h: np.ndarray) -> np.ndarray | None:
    s = spec(fixture,object_id)
    if s["type"] != "cylinder": return None
    p = _to_local(fixture,object_id,xyz_h)
    return np.sqrt(p[:,0]**2+(p[:,2]-s["centre_z_local_m"])**2)-s["radius_m"]


def truth_spec(fixture: str) -> dict:
    return {"id":f"Scene1a-{fixture}-truth-v1","public_spec_sha256":public.public_digest(),"fixture":fixture,
            "objects":{str(oid):spec(fixture,oid) for oid in public.OBJECT_IDS},
            "background_z_h_m":BACKGROUND_Z_M,"cylinder_strips":CYLINDER_STRIPS,
            "truth_cover_radius_m":TRUTH_COVER_RADIUS_M}


def truth_digest(fixture: str) -> str:
    return hashlib.sha256(json.dumps(truth_spec(fixture),sort_keys=True,separators=(",",":")).encode()).hexdigest()


def _unique_rows(a: np.ndarray, decimals: int = 8) -> np.ndarray:
    return np.unique(np.round(np.asarray(a,float).reshape(-1,3),decimals=decimals),axis=0)


def validate_mesh(fixture: str, mesh: dict) -> None:
    tri=np.asarray(mesh["triangles_h"],float); ids=np.asarray(mesh["instance_ids"],np.int32)
    expected_ids=set(public.OBJECT_IDS)|{public.BACKGROUND_ID}
    if set(ids.tolist()) != expected_ids: raise ValueError("unexpected Scene-1a instance IDs")
    objs=scene_objects(fixture)
    for oid in public.OBJECT_IDS:
        wanted=[o for o in objs if int(o["instance_id"])==oid]
        exp=_unique_rows(np.concatenate([o["vertices_h"] for o in wanted],axis=0)); got=_unique_rows(tri[ids==oid])
        expected_tri = 2 if spec(fixture,oid)["type"]=="plane" else 2*CYLINDER_STRIPS
        if int((ids==oid).sum()) != expected_tri: raise ValueError(f"unexpected triangle count for object {oid}")
        if exp.shape!=got.shape or np.max(np.linalg.norm(exp-got,axis=1))>2e-5: raise ValueError(f"mesh mismatch for object {oid}")
    bg=[o for o in objs if int(o["instance_id"])==public.BACKGROUND_ID]
    if int((ids==public.BACKGROUND_ID).sum())!=2 or len(bg)!=1: raise ValueError("background triangle count mismatch")


def ideal_box_coverage(fixture: str, object_id: int, gaze: tuple[float,float], fov_deg: float = 12.0) -> float:
    y,p=angular_coordinates(truth_points(fixture,object_id)); half=fov_deg/2
    return float(np.mean((np.abs(y-float(gaze[0]))<=half)&(np.abs(p-float(gaze[1]))<=half)))


def preflight() -> dict:
    rows={}; yaw_lim=(-25.0,25.0); pitch_lim=(-20.0,20.0)
    for f in public.FIXTURES:
        b={oid:angular_bounds(f,oid) for oid in public.OBJECT_IDS}
        for oid,(yl,yh,pl,ph) in b.items():
            if yl<yaw_lim[0] or yh>yaw_lim[1] or pl<pitch_lim[0] or ph>pitch_lim[1]:
                raise AssertionError(f"{f}/{oid} leaves frozen FSG6f policy domain")
        # No object-object angular rectangle overlap in this base scene.
        for i,a in enumerate(public.OBJECT_IDS):
            for c in public.OBJECT_IDS[i+1:]:
                A=b[a]; B=b[c]
                iw=max(0.0,min(A[1],B[1])-max(A[0],B[0])); ih=max(0.0,min(A[3],B[3])-max(A[2],B[2]))
                if iw*ih>1e-9: raise AssertionError(f"{f} objects {a}/{c} angularly overlap in Scene-1a base case")
        seed_rows={}
        seed_map=dict(public.SEED_SEQUENCE[f])
        for oid in public.OBJECT_IDS:
            g=seed_map[oid]; c0=ideal_box_coverage(f,oid,g); best=c0; bestg=g
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    if dx==0 and dy==0: continue
                    gg=(g[0]+5*dx,g[1]+5*dy); cc=ideal_box_coverage(f,oid,gg)
                    if cc>best: best,bestg=cc,gg
            if not (0.20<=c0<=0.75): raise AssertionError(f"{f}/{oid} seed is not a genuinely partial object view")
            if best<c0+0.04: raise AssertionError(f"{f}/{oid} has no useful neighbouring active view")
            seed_rows[oid]={"seed_ideal_coverage":c0,"best_neighbour_ideal_coverage":best,"best_neighbour_gaze":list(bestg)}
        rows[f]={"bounds":{str(k):list(v) for k,v in b.items()},"seeds":seed_rows}
    return rows


def self_test() -> None:
    pf=preflight()
    if set(pf)!=set(public.FIXTURES): raise AssertionError("Scene-1a preflight fixture set wrong")
