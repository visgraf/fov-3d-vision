"""Evaluator-only rolled cylindrical ribbons for FSG6.

The active host and 3D frontier policy must not import this module.  The visible
surface is a finite convex cylinder ribbon rolled in the head image plane, so a
successful exploration must change both yaw and pitch.  Evaluation uses the
continuous analytic cylinder after undoing the rigid roll; rendering uses a fine
piecewise-planar strip approximation.
"""
from __future__ import annotations
import hashlib
import json
import math
import numpy as np
from fsg_scene import quad, texture
import fsg6_public as public

BACKGROUND_Z_M = -3.90
BACKGROUND_SIZE_M = (4.6, 3.4)
STRIP_COUNT = 48
TRUTH_GRID_WH = (256, 64)
TRUTH_COVER_RADIUS_M = 0.015

FIXTURE = {
    "diag_up_right": {
        "centre_z_m": -2.80,
        "radius_m": 0.75,
        "theta_min_deg": -55.0,
        "theta_max_deg": +55.0,
        "height_m": 0.20,
        "roll_deg": +35.0,
        "texture_tag": 31,
    },
    # Exact 180-degree image-plane rotation of the first ribbon, with a distinct texture.
    "diag_down_left": {
        "centre_z_m": -2.80,
        "radius_m": 0.75,
        "theta_min_deg": -55.0,
        "theta_max_deg": +55.0,
        "height_m": 0.20,
        "roll_deg": +215.0,
        "texture_tag": 37,
    },
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
        "name": f"fsg6_{fixture}_strip_{j:02d}",
        "vertices_h": verts,
        "instance_id": public.OBJECT_ID,
        "uv": np.array([[u0, 0.0], [u1, 0.0], [u1, 1.0], [u0, 1.0]], dtype=float),
    }


def scene_objects(fixture: str) -> list[dict]:
    out = [_strip_quad(fixture, j) for j in range(STRIP_COUNT)]
    out.append(quad([0.0, 0.0, BACKGROUND_Z_M], [1, 0, 0], [0, 1, 0],
                    BACKGROUND_SIZE_M[0], BACKGROUND_SIZE_M[1],
                    public.BACKGROUND_ID, f"fsg6_{fixture}_background"))
    return out


def scene_texture(fixture: str, instance: int, size: int = 512) -> np.ndarray:
    tag = int(spec(fixture)["texture_tag"])
    return texture(int(instance) + 111000 + 179 * tag, size)


def truth_spec(fixture: str) -> dict:
    s = spec(fixture)
    return {
        "id": f"FSG6-{fixture}-truth-v1",
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
        raise ValueError("unexpected FSG6 exported triangle counts")
    if set(ids.tolist()) != {public.OBJECT_ID, public.BACKGROUND_ID}:
        raise ValueError("unexpected FSG6 object IDs")
    wanted = scene_objects(fixture)
    exp_obj = _unique_rows(np.concatenate([x["vertices_h"] for x in wanted[:-1]], axis=0))
    got_obj = _unique_rows(tri[ids == public.OBJECT_ID])
    exp_bg = _unique_rows(wanted[-1]["vertices_h"]); got_bg = _unique_rows(tri[ids == public.BACKGROUND_ID])
    if exp_obj.shape != got_obj.shape or exp_bg.shape != got_bg.shape:
        raise ValueError("exported FSG6 mesh vertex population disagrees")
    if np.max(np.linalg.norm(exp_obj - got_obj, axis=1)) > 2e-5 or np.max(np.linalg.norm(exp_bg - got_bg, axis=1)) > 2e-5:
        raise ValueError("exported Blender mesh disagrees with FSG6 specification")


def truth_points(fixture: str) -> np.ndarray:
    s = spec(fixture); nt, ny = TRUTH_GRID_WH
    th = np.linspace(math.radians(s["theta_min_deg"]), math.radians(s["theta_max_deg"]), nt)
    yy = np.linspace(-s["height_m"] / 2.0, s["height_m"] / 2.0, ny)
    T, Y = np.meshgrid(th, yy)
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


def self_test() -> None:
    ru = angular_bounds("diag_up_right"); dl = angular_bounds("diag_down_left")
    if not (-14.0 < ru[0] < -12.5 and 12.5 < ru[1] < 14.0 and -11.0 < ru[2] < -9.0 and 9.0 < ru[3] < 11.0):
        raise AssertionError(f"diag_up_right angular design drifted: {ru}")
    if not np.allclose(np.array(dl), np.array([-ru[1], -ru[0], -ru[3], -ru[2]]), atol=1e-9):
        raise AssertionError("FSG6 fixtures are no longer 180-degree image-plane mirrors")
    diag_r = [(-8,-8), (-3,-3), (2,2), (7,7)]
    diag_l = [(8,8), (3,3), (-2,-2), (-7,-7)]
    if ideal_angular_coverage("diag_up_right", diag_r) < 0.97 or ideal_angular_coverage("diag_down_left", diag_l) < 0.97:
        raise AssertionError("prospective diagonal four-look trace no longer spans the FSG6 surface")
    horiz_r = [(-8 + 5*k, -8) for k in range(5)]
    horiz_l = [(8 - 5*k, 8) for k in range(5)]
    hc = max(ideal_angular_coverage("diag_up_right", horiz_r), ideal_angular_coverage("diag_down_left", horiz_l))
    if hc >= 0.65:
        raise AssertionError("FSG6 fixture no longer requires two-dimensional gaze")
    chord = max(max_strip_chord_error_m(f) for f in public.FIXTURES)
    if chord > 0.0002:
        raise AssertionError(f"FSG6 render tessellation too coarse: {chord} m")
    for f in public.FIXTURES:
        if float(np.max(surface_distance(f, truth_points(f)))) > 1e-10:
            raise AssertionError("FSG6 analytic truth points reject themselves")
    print(f"[fsg6-scene] PASS up_right=[{ru[0]:.3f},{ru[1]:.3f}]x[{ru[2]:.3f},{ru[3]:.3f}] horizontal_ideal_max={hc:.3f} chord_max_mm={1000*chord:.3f}")


if __name__ == "__main__":
    self_test()
