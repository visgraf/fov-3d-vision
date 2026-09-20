"""Evaluator-only rolled cylindrical ribbons for FSG6d.

FSG6d uses fresh non-mirror curved fixtures and an evaluator-side analytic
preflight that exercises the SAME projected-frontier corridor semantics as
the runtime policy.  The host loop and frontier policy must not import this
module.  Rendering uses a fine piecewise-planar strip approximation; evaluation
uses the continuous analytic cylinder.
"""
from __future__ import annotations
import hashlib
import json
import math
import numpy as np
from fsg_scene import quad, texture
import fsg6d_public as public

BACKGROUND_Z_M = -3.95
BACKGROUND_SIZE_M = (4.8, 3.6)
STRIP_COUNT = 48
TRUTH_GRID_WH = (256, 64)
TRUTH_COVER_RADIUS_M = 0.015

FIXTURE = {
    "corridor_up_right": {
        "centre_z_m": -2.86,
        "radius_m": 0.74,
        "theta_min_deg": -58.0,
        "theta_max_deg": +55.0,
        "height_m": 0.252,
        "roll_deg": +29.0,
        "texture_tag": 73,
    },
    "corridor_down_left": {
        "centre_z_m": -2.70,
        "radius_m": 0.70,
        "theta_min_deg": -50.0,
        "theta_max_deg": +63.0,
        "height_m": 0.246,
        "roll_deg": +211.0,
        "texture_tag": 79,
    },
}

# Geometry-only construction traces; never prescribed to the runtime policy.
PREFLIGHT_TRACE = {
    "corridor_up_right": [(-8.0,-7.0), (-3.0,-2.0), (2.0,3.0), (7.0,8.0)],
    "corridor_down_left": [(8.0,7.0), (3.0,2.0), (-2.0,-3.0), (-7.0,-8.0)],
}

def spec(fixture: str) -> dict:
    if fixture not in public.FIXTURES:
        raise ValueError(f"unknown fixture {fixture}")
    return FIXTURE[fixture]


def _rz(deg: float) -> np.ndarray:
    a = math.radians(float(deg)); c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]], dtype=float)


def cylinder_point(fixture: str, theta_rad: np.ndarray, y_m: np.ndarray | float) -> np.ndarray:
    s = spec(fixture)
    th = np.asarray(theta_rad, float); yy = np.asarray(y_m, float)
    th, yy = np.broadcast_arrays(th, yy)
    local = np.stack((s["radius_m"] * np.sin(th), yy,
                      s["centre_z_m"] + s["radius_m"] * np.cos(th)), axis=-1)
    return local @ _rz(s["roll_deg"]).T


def to_local(fixture: str, xyz_h: np.ndarray) -> np.ndarray:
    p = np.asarray(xyz_h, float).reshape(-1, 3)
    return p @ _rz(spec(fixture)["roll_deg"])


def _strip_quad(fixture: str, j: int) -> dict:
    s = spec(fixture)
    a0 = math.radians(s["theta_min_deg"] + (s["theta_max_deg"] - s["theta_min_deg"]) * j / STRIP_COUNT)
    a1 = math.radians(s["theta_min_deg"] + (s["theta_max_deg"] - s["theta_min_deg"]) * (j + 1) / STRIP_COUNT)
    y0, y1 = -s["height_m"] / 2.0, s["height_m"] / 2.0
    verts = np.array([
        cylinder_point(fixture, a0, y0), cylinder_point(fixture, a1, y0),
        cylinder_point(fixture, a1, y1), cylinder_point(fixture, a0, y1),
    ], dtype=float)
    u0, u1 = j / STRIP_COUNT, (j + 1) / STRIP_COUNT
    return {
        "name": f"fsg6d_{fixture}_strip_{j:02d}",
        "vertices_h": verts,
        "instance_id": public.OBJECT_ID,
        "uv": np.array([[u0, 0.0], [u1, 0.0], [u1, 1.0], [u0, 1.0]], dtype=float),
    }


def scene_objects(fixture: str) -> list[dict]:
    out = [_strip_quad(fixture, j) for j in range(STRIP_COUNT)]
    out.append(quad([0.0, 0.0, BACKGROUND_Z_M], [1, 0, 0], [0, 1, 0],
                    BACKGROUND_SIZE_M[0], BACKGROUND_SIZE_M[1],
                    public.BACKGROUND_ID, f"fsg6d_{fixture}_background"))
    return out


def scene_texture(fixture: str, instance: int, size: int = 512) -> np.ndarray:
    tag = int(spec(fixture)["texture_tag"])
    return texture(int(instance) + 121000 + 181 * tag, size)


def truth_spec(fixture: str) -> dict:
    s = spec(fixture)
    return {
        "id": f"FSG6d-{fixture}-truth-v1",
        "public_spec_sha256": public.public_digest(),
        "fixture": fixture,
        "centre_z_local_m": s["centre_z_m"],
        "radius_m": s["radius_m"],
        "theta_deg": [s["theta_min_deg"], s["theta_max_deg"]],
        "height_m": s["height_m"],
        "roll_deg": s["roll_deg"],
        "background_z_h_m": BACKGROUND_Z_M,
        "strip_count": STRIP_COUNT,
        "truth_grid_wh": list(TRUTH_GRID_WH),
        "truth_cover_radius_m": TRUTH_COVER_RADIUS_M,
        "texture_tag": s["texture_tag"],
    }


def truth_digest(fixture: str) -> str:
    return hashlib.sha256(json.dumps(truth_spec(fixture), sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _unique_rows(a: np.ndarray, decimals: int = 8) -> np.ndarray:
    return np.unique(np.round(np.asarray(a, float).reshape(-1, 3), decimals=decimals), axis=0)


def validate_mesh(fixture: str, mesh: dict) -> None:
    tri = np.asarray(mesh["triangles_h"], float); ids = np.asarray(mesh["instance_ids"], np.int32)
    if int((ids == public.OBJECT_ID).sum()) != 2 * STRIP_COUNT or int((ids == public.BACKGROUND_ID).sum()) != 2:
        raise ValueError("unexpected FSG6d exported triangle counts")
    if set(ids.tolist()) != {public.OBJECT_ID, public.BACKGROUND_ID}:
        raise ValueError("unexpected FSG6d object IDs")
    wanted = scene_objects(fixture)
    exp_obj = _unique_rows(np.concatenate([x["vertices_h"] for x in wanted[:-1]], axis=0))
    got_obj = _unique_rows(tri[ids == public.OBJECT_ID])
    exp_bg = _unique_rows(wanted[-1]["vertices_h"]); got_bg = _unique_rows(tri[ids == public.BACKGROUND_ID])
    if exp_obj.shape != got_obj.shape or exp_bg.shape != got_bg.shape:
        raise ValueError("exported FSG6d mesh vertex population disagrees")
    if np.max(np.linalg.norm(exp_obj - got_obj, axis=1)) > 2e-5 or np.max(np.linalg.norm(exp_bg - got_bg, axis=1)) > 2e-5:
        raise ValueError("exported Blender mesh disagrees with FSG6d specification")


def truth_points(fixture: str) -> np.ndarray:
    s = spec(fixture); nt, ny = TRUTH_GRID_WH
    t = np.radians(np.linspace(s["theta_min_deg"], s["theta_max_deg"], nt))
    y = np.linspace(-s["height_m"] / 2.0, s["height_m"] / 2.0, ny)
    T, Y = np.meshgrid(t, y)
    return cylinder_point(fixture, T, Y).reshape(-1, 3)


def surface_parameters(fixture: str, xyz_h: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    s = spec(fixture); p = to_local(fixture, xyz_h)
    theta = np.arctan2(p[:, 0], p[:, 2] - s["centre_z_m"])
    radial = np.sqrt(p[:, 0] ** 2 + (p[:, 2] - s["centre_z_m"]) ** 2)
    return theta, p[:, 1], radial


def signed_radial_error(fixture: str, xyz_h: np.ndarray) -> np.ndarray:
    return surface_parameters(fixture, xyz_h)[2] - float(spec(fixture)["radius_m"])


def surface_distance(fixture: str, xyz_h: np.ndarray) -> np.ndarray:
    s = spec(fixture); p = to_local(fixture, xyz_h)
    theta, yy, _ = surface_parameters(fixture, xyz_h)
    t0, t1 = math.radians(s["theta_min_deg"]), math.radians(s["theta_max_deg"])
    tc = np.clip(theta, t0, t1); yc = np.clip(yy, -s["height_m"] / 2.0, s["height_m"] / 2.0)
    q_local = np.stack((s["radius_m"] * np.sin(tc), yc,
                        s["centre_z_m"] + s["radius_m"] * np.cos(tc)), axis=1)
    return np.linalg.norm(p - q_local, axis=1)


def angular_coordinates(xyz_h: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    p = np.asarray(xyz_h, float).reshape(-1, 3)
    yaw = np.degrees(np.arctan2(p[:, 0], -p[:, 2]))
    pitch = np.degrees(np.arctan2(p[:, 1], np.sqrt(p[:, 0] ** 2 + p[:, 2] ** 2)))
    return yaw, pitch


def angular_bounds(fixture: str) -> tuple[float, float, float, float]:
    yaw, pitch = angular_coordinates(truth_points(fixture))
    return float(yaw.min()), float(yaw.max()), float(pitch.min()), float(pitch.max())


def ideal_angular_coverage(fixture: str, gazes: list[tuple[float, float]], half: float = 6.0) -> float:
    p = truth_points(fixture); yaw, pitch = angular_coordinates(p); seen = np.zeros(len(p), bool)
    for gy, gp in gazes:
        seen |= (np.abs(yaw - gy) <= half) & (np.abs(pitch - gp) <= half)
    return float(seen.mean())


def max_strip_chord_error_m(fixture: str) -> float:
    s = spec(fixture)
    dt = math.radians((s["theta_max_deg"] - s["theta_min_deg"]) / STRIP_COUNT)
    return float(s["radius_m"] * (1.0 - math.cos(dt / 2.0)))


def _analytic_raw_object_ids(fixture: str, eye: dict, uv: np.ndarray) -> np.ndarray:
    """Continuous-cylinder first-hit object mask for evaluator-only preflight."""
    from fsg_geometry import rays_h
    s = spec(fixture); R = _rz(s["roll_deg"])
    o = np.asarray(eye["centre_h_m"], float) @ R
    d = rays_h(eye, uv) @ R
    ox, oy, oz = o; dx, dy, dz = d[..., 0], d[..., 1], d[..., 2]
    zz = oz - s["centre_z_m"]
    A = dx * dx + dz * dz
    B = 2.0 * (ox * dx + zz * dz)
    C = ox * ox + zz * zz - s["radius_m"] ** 2
    disc = B * B - 4.0 * A * C
    sq = np.sqrt(np.maximum(disc, 0.0))
    t0, t1 = math.radians(s["theta_min_deg"]), math.radians(s["theta_max_deg"])
    ymin, ymax = -s["height_m"] / 2.0, s["height_m"] / 2.0
    hit = np.zeros(dx.shape, bool)
    for t in ((-B - sq) / (2.0 * A), (-B + sq) / (2.0 * A)):
        x = ox + t * dx; y = oy + t * dy; z = oz + t * dz
        th = np.arctan2(x, z - s["centre_z_m"])
        hit |= ((disc >= 0.0) & (t > 1e-6) & (y >= ymin) & (y <= ymax) &
                (th >= t0) & (th <= t1))
    return np.where(hit, public.OBJECT_ID, public.BACKGROUND_ID).astype(np.int32)


def analytic_rectified_oracles(fixture: str, gaze: tuple[float, float], profile: str = "small") -> tuple[dict, dict, dict]:
    """Exact-policy preflight masks from analytic cylinder + repository rectification.

    Imports are deliberately local so Blender-side scene construction does not
    depend on host OpenCV/Pillow packages merely by importing this module.
    """
    import cv2
    from fsg_geometry import make_calibration, pixels
    from fsg_stereo import rectification, remap, support_mask
    c = make_calibration(profile, float(gaze[0]), float(gaze[1]), public.VERGENCE_DISTANCE_M)
    w, h = c["image_size_wh"]; uv = pixels(w, h); r = rectification(c)
    x, y, cw, ch = map(int, r["crop_xywh"]); sl = np.s_[y:y+ch, x:x+cw]
    out = {}
    for eye in c["eyes"]:
        name = eye["name"]
        raw = _analytic_raw_object_ids(fixture, eye, uv)
        ids = remap(raw.astype(np.float32), r, name, cv2.INTER_NEAREST).astype(np.int32)[sl]
        sup = support_mask(c, r, name)[sl]
        out[name] = (ids, sup)
    return c, out["L"], out["R"]


def _direction_probe_one_eye(ids: np.ndarray, sup: np.ndarray, dx: int, dy: int) -> dict:
    """Evaluator-only mask probe using the SAME exit-corridor rasterizer as runtime.

    We choose object pixels at the forward extremum of the current analytic mask,
    within one already-frozen legacy band width, and extend them in the requested
    candidate direction.  This does not predict the 3D frontier; it only checks
    whether the fixture/segmentation makes that directional continuation physically
    possible under the exact FSG6d corridor semantics.
    """
    import fsg6d_frontier as policy
    ids=np.asarray(ids); sup=np.asarray(sup,bool); h,w=ids.shape
    obj=np.argwhere((ids==public.OBJECT_ID)&sup)
    if len(obj)==0:
        return {"fraction":0.0,"object_pixels":0,"support_pixels":0,"projected_frontier_rays":0,"corridor_pixels":0}
    # uv order is x,y; +pitch means up, hence image direction (dx,-dy).
    uv=np.c_[obj[:,1],obj[:,0]].astype(float); v=np.array([float(dx),float(-dy)])
    v/=np.linalg.norm(v)
    centre=np.array([(w-1)/2.0,(h-1)/2.0]); score=(uv-centre)@v
    band=max(2,int(round(min(h,w)*public.SURFACE_FRONTIER["edge_band_fraction"])))
    front=uv[score>=float(score.max())-float(band)]
    target=front+v*float(band)
    return policy._corridor_eye_evidence(ids,sup,public.OBJECT_ID,front,target,dx,dy)


def preflight_direction_probe(fixture: str, gaze: tuple[float,float], dx: int, dy: int) -> dict:
    _,L,R=analytic_rectified_oracles(fixture,gaze,profile="small")
    a=_direction_probe_one_eye(L[0],L[1],dx,dy); b=_direction_probe_one_eye(R[0],R[1],dx,dy)
    value=max(float(a["fraction"]),float(b["fraction"]))
    th=float(public.SURFACE_FRONTIER["edge_object_fraction_min"])
    return {"direction":[int(dx),int(dy)],"per_eye":{"L":a,"R":b},"combined_fraction":value,
            "threshold":th,"allowed":bool(value>=th)}


def _candidate_reference_pixels(fixture: str, gaze: tuple[float,float]) -> tuple[int,int]:
    _,L,R=analytic_rectified_oracles(fixture,gaze,profile="small")
    return (int(((L[0]==public.OBJECT_ID)&L[1]).sum()),int(((R[0]==public.OBJECT_ID)&R[1]).sum()))


def self_test() -> None:
    ur=angular_bounds("corridor_up_right"); dl=angular_bounds("corridor_down_left")
    for name,b in (("corridor_up_right",ur),("corridor_down_left",dl)):
        if not (-16.0<b[0]<-10.0 and 10.0<b[1]<16.0 and -12.0<b[2]<-7.0 and 7.0<b[3]<12.0):
            raise AssertionError(f"{name} angular design drifted: {b}")
    if np.allclose(np.array(dl),np.array([-ur[1],-ur[0],-ur[3],-ur[2]]),atol=1e-3):
        raise AssertionError("FSG6d fixtures unexpectedly collapsed to an exact mirror pair")

    # Every geometry-only construction transition must be physically reachable
    # under the exact runtime exit-corridor rasterizer and unchanged 0.15 threshold.
    for f in public.FIXTURES:
        trace=PREFLIGHT_TRACE[f]
        if ideal_angular_coverage(f,trace)<0.95:
            raise AssertionError(f"geometry-only diagonal construction no longer spans {f}")
        for a,b in zip(trace[:-1],trace[1:]):
            dx=int(round((b[0]-a[0])/public.SURFACE_FRONTIER["component_step_deg"]))
            dy=int(round((b[1]-a[1])/public.SURFACE_FRONTIER["component_step_deg"]))
            q=preflight_direction_probe(f,a,dx,dy)
            if not q["allowed"]:
                raise AssertionError(f"runtime corridor semantics reject construction transition: {f} {a}->{b} {q}")
        # Enumerate every neighbour at every construction state.  Any direction
        # the segmentation corridor permits must at least land on a next view with
        # the evaluator's already-frozen >=100 oracle-reference population.
        for a in trace:
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    if dx==0 and dy==0: continue
                    q=preflight_direction_probe(f,a,dx,dy)
                    if not q["allowed"]: continue
                    dest=(a[0]+dx*public.SURFACE_FRONTIER["component_step_deg"],
                          a[1]+dy*public.SURFACE_FRONTIER["component_step_deg"])
                    nL,nR=_candidate_reference_pixels(f,dest)
                    if min(nL,nR)<100:
                        raise AssertionError(f"corridor preflight exposes unsafe legal neighbour: {f} from={a} dest={dest} refs={nL}/{nR} evidence={q}")

    horiz_r=[(-8+5*k,-7) for k in range(5)]; horiz_l=[(8-5*k,7) for k in range(5)]
    hc=max(ideal_angular_coverage("corridor_up_right",horiz_r),ideal_angular_coverage("corridor_down_left",horiz_l))
    if hc>=0.65:
        raise AssertionError("FSG6d fixture no longer requires two-dimensional gaze")
    chord=max(max_strip_chord_error_m(f) for f in public.FIXTURES)
    if chord>0.0002: raise AssertionError(f"FSG6d render tessellation too coarse: {chord} m")
    for f in public.FIXTURES:
        if float(np.max(surface_distance(f,truth_points(f))))>1e-10:
            raise AssertionError("FSG6d analytic truth points reject themselves")
    print(f"[fsg6d-scene] PASS up_right=[{ur[0]:.3f},{ur[1]:.3f}]x[{ur[2]:.3f},{ur[3]:.3f}] "
          f"down_left=[{dl[0]:.3f},{dl[1]:.3f}]x[{dl[2]:.3f},{dl[3]:.3f}] horizontal_ideal_max={hc:.3f} "
          f"chord_max_mm={1000*chord:.3f} corridor_preflight=true all_permitted_neighbours_population_checked=true")


if __name__=="__main__": self_test()
