"""Evaluator-only convex cylindrical-ribbon fixtures for FSG5.

The active host and policy must not import this module.  Blender acquisition uses
it to build the opaque scene; post-hoc evaluation uses the analytic cylinder.
The rendered object is a fine piecewise-planar approximation (40 quad strips),
whose maximum chord deviation from the analytic cylinder is checked below 0.2 mm.
"""
from __future__ import annotations
import hashlib
import json
import math
import numpy as np
from fsg_scene import quad, texture
import fsg5_public as public

BACKGROUND_Z_M = -3.80
BACKGROUND_SIZE_M = (4.4, 3.0)
STRIP_COUNT = 40
TRUTH_GRID_WH = (256, 84)
TRUTH_COVER_RADIUS_M = 0.015

FIXTURE = {
    # Object boundary is near -8.49 deg; seed -7 deg sees background on the
    # left and unresolved object through the right edge, so the frozen policy
    # must walk right.  Curvature spans 75 cylinder degrees.
    "curve_right": {
        "centre_x_m": +0.15,
        "centre_z_m": -2.80,
        "radius_m": 0.75,
        "theta_min_deg": -40.0,
        "theta_max_deg": +35.0,
        "height_m": 0.34,
        "texture_tag": 17,
    },
    # Exact horizontal mirror with a different texture; seed +7 deg must walk left.
    "curve_left": {
        "centre_x_m": -0.15,
        "centre_z_m": -2.80,
        "radius_m": 0.75,
        "theta_min_deg": -35.0,
        "theta_max_deg": +40.0,
        "height_m": 0.34,
        "texture_tag": 23,
    },
}


def spec(fixture: str) -> dict:
    if fixture not in public.FIXTURES:
        raise ValueError(f"unknown fixture {fixture}")
    return FIXTURE[fixture]


def cylinder_point(fixture: str, theta_rad: np.ndarray, y_m: np.ndarray | float) -> np.ndarray:
    s = spec(fixture)
    th = np.asarray(theta_rad, float)
    y = np.asarray(y_m, float)
    th, y = np.broadcast_arrays(th, y)
    x = s["centre_x_m"] + s["radius_m"] * np.sin(th)
    z = s["centre_z_m"] + s["radius_m"] * np.cos(th)
    return np.stack((x, y, z), axis=-1)


def _strip_quad(fixture: str, j: int) -> dict:
    s = spec(fixture)
    a0 = math.radians(s["theta_min_deg"] + (s["theta_max_deg"] - s["theta_min_deg"]) * j / STRIP_COUNT)
    a1 = math.radians(s["theta_min_deg"] + (s["theta_max_deg"] - s["theta_min_deg"]) * (j + 1) / STRIP_COUNT)
    y0, y1 = -s["height_m"] / 2.0, s["height_m"] / 2.0
    verts = np.array([
        cylinder_point(fixture, a0, y0),
        cylinder_point(fixture, a1, y0),
        cylinder_point(fixture, a1, y1),
        cylinder_point(fixture, a0, y1),
    ], dtype=float)
    u0, u1 = j / STRIP_COUNT, (j + 1) / STRIP_COUNT
    return {
        "name": f"fsg5_{fixture}_strip_{j:02d}",
        "vertices_h": verts,
        "instance_id": public.OBJECT_ID,
        "uv": np.array([[u0, 0.0], [u1, 0.0], [u1, 1.0], [u0, 1.0]], dtype=float),
    }


def scene_objects(fixture: str) -> list[dict]:
    strips = [_strip_quad(fixture, j) for j in range(STRIP_COUNT)]
    strips.append(quad([0.0, 0.0, BACKGROUND_Z_M], [1, 0, 0], [0, 1, 0],
                       BACKGROUND_SIZE_M[0], BACKGROUND_SIZE_M[1],
                       public.BACKGROUND_ID, f"fsg5_{fixture}_background"))
    return strips


def scene_texture(fixture: str, instance: int, size: int = 512) -> np.ndarray:
    tag = int(spec(fixture)["texture_tag"])
    return texture(int(instance) + 95000 + 173 * tag, size)


def truth_spec(fixture: str) -> dict:
    s = spec(fixture)
    return {
        "id": f"FSG5-{fixture}-truth-v1",
        "public_spec_sha256": public.public_digest(),
        "fixture": fixture,
        "cylinder_centre_xz_h_m": [s["centre_x_m"], s["centre_z_m"]],
        "radius_m": s["radius_m"],
        "theta_deg": [s["theta_min_deg"], s["theta_max_deg"]],
        "height_m": s["height_m"],
        "background_z_h_m": BACKGROUND_Z_M,
        "strip_count": STRIP_COUNT,
        "truth_grid_wh": list(TRUTH_GRID_WH),
        "truth_cover_radius_m": TRUTH_COVER_RADIUS_M,
        "texture_tag": s["texture_tag"],
    }


def truth_digest(fixture: str) -> str:
    return hashlib.sha256(json.dumps(truth_spec(fixture), sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _unique_rows(a: np.ndarray, decimals: int = 8) -> np.ndarray:
    q = np.round(np.asarray(a, float).reshape(-1, 3), decimals=decimals)
    return np.unique(q, axis=0)


def validate_mesh(fixture: str, mesh: dict) -> None:
    tri = np.asarray(mesh["triangles_h"], float)
    ids = np.asarray(mesh["instance_ids"], np.int32)
    expected_obj_tri = 2 * STRIP_COUNT
    if int((ids == public.OBJECT_ID).sum()) != expected_obj_tri or int((ids == public.BACKGROUND_ID).sum()) != 2:
        raise ValueError("unexpected FSG5 exported triangle counts")
    if set(ids.tolist()) != {public.OBJECT_ID, public.BACKGROUND_ID}:
        raise ValueError("unexpected FSG5 object IDs")
    wanted = scene_objects(fixture)
    exp_obj = _unique_rows(np.concatenate([x["vertices_h"] for x in wanted[:-1]], axis=0))
    got_obj = _unique_rows(tri[ids == public.OBJECT_ID])
    exp_bg = _unique_rows(wanted[-1]["vertices_h"])
    got_bg = _unique_rows(tri[ids == public.BACKGROUND_ID])
    if exp_obj.shape != got_obj.shape or exp_bg.shape != got_bg.shape:
        raise ValueError("exported FSG5 mesh vertex population disagrees")
    if np.max(np.linalg.norm(exp_obj - got_obj, axis=1)) > 2e-5 or np.max(np.linalg.norm(exp_bg - got_bg, axis=1)) > 2e-5:
        raise ValueError("exported Blender mesh disagrees with FSG5 specification")


def angular_span_deg(fixture: str) -> tuple[float, float]:
    s = spec(fixture)
    a = cylinder_point(fixture, math.radians(s["theta_min_deg"]), 0.0)
    b = cylinder_point(fixture, math.radians(s["theta_max_deg"]), 0.0)
    return tuple(float(np.degrees(np.arctan2(p[0], -p[2]))) for p in (a, b))


def truth_points(fixture: str) -> np.ndarray:
    s = spec(fixture)
    nt, ny = TRUTH_GRID_WH
    th = np.linspace(math.radians(s["theta_min_deg"]), math.radians(s["theta_max_deg"]), nt)
    y = np.linspace(-s["height_m"] / 2.0, s["height_m"] / 2.0, ny)
    T, Y = np.meshgrid(th, y)
    return cylinder_point(fixture, T, Y).reshape(-1, 3)


def surface_parameters(fixture: str, xyz: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    s = spec(fixture)
    p = np.asarray(xyz, float).reshape(-1, 3)
    dx = p[:, 0] - s["centre_x_m"]
    dz = p[:, 2] - s["centre_z_m"]
    theta = np.arctan2(dx, dz)
    radial = np.sqrt(dx * dx + dz * dz)
    return theta, p[:, 1], radial


def signed_radial_error(fixture: str, xyz: np.ndarray) -> np.ndarray:
    _, _, r = surface_parameters(fixture, xyz)
    return r - float(spec(fixture)["radius_m"])


def surface_distance(fixture: str, xyz: np.ndarray) -> np.ndarray:
    """Euclidean distance to the finite analytic cylindrical ribbon."""
    s = spec(fixture)
    p = np.asarray(xyz, float).reshape(-1, 3)
    theta, y, _ = surface_parameters(fixture, p)
    t0, t1 = math.radians(s["theta_min_deg"]), math.radians(s["theta_max_deg"])
    tc = np.clip(theta, t0, t1)
    yc = np.clip(y, -s["height_m"] / 2.0, s["height_m"] / 2.0)
    q = cylinder_point(fixture, tc, yc)
    return np.linalg.norm(p - q, axis=1)


def _interval_coverage(span: tuple[float, float], yaws: list[float], half: float = 6.0) -> float:
    lo, hi = span
    ints = []
    for y in yaws:
        a, b = max(lo, y - half), min(hi, y + half)
        if b > a:
            ints.append((a, b))
    if not ints:
        return 0.0
    ints.sort(); start, end = ints[0]; total = 0.0
    for a, b in ints[1:]:
        if a <= end:
            end = max(end, b)
        else:
            total += end - start; start, end = a, b
    total += end - start
    return total / (hi - lo)


def max_strip_chord_error_m(fixture: str) -> float:
    s = spec(fixture)
    dtheta = math.radians((s["theta_max_deg"] - s["theta_min_deg"]) / STRIP_COUNT)
    return float(s["radius_m"] * (1.0 - math.cos(dtheta / 2.0)))


def self_test() -> None:
    r = angular_span_deg("curve_right")
    l = angular_span_deg("curve_left")
    if not (-9.0 < r[0] < -8.0 and 14.0 < r[1] < 16.0):
        raise AssertionError(f"curve_right angular design drifted: {r}")
    if not (-16.0 < l[0] < -14.0 and 8.0 < l[1] < 9.0):
        raise AssertionError(f"curve_left angular design drifted: {l}")
    if not np.allclose(np.array(l), -np.array(r[::-1]), atol=1e-9):
        raise AssertionError("curved fixtures are no longer horizontal mirrors")
    if _interval_coverage(r, [-7, -2, 3, 8, 13]) < 0.99:
        raise AssertionError("five-look rightward trace no longer spans curved fixture")
    if _interval_coverage(l, [7, 2, -3, -8, -13]) < 0.99:
        raise AssertionError("five-look leftward trace no longer spans curved fixture")
    chord = max(max_strip_chord_error_m(f) for f in public.FIXTURES)
    if chord > 0.0002:
        raise AssertionError(f"curved render tessellation too coarse: {chord} m")
    for f in public.FIXTURES:
        e = surface_distance(f, truth_points(f))
        if float(np.max(e)) > 1e-10:
            raise AssertionError("analytic truth points do not lie on FSG5 cylinder")
    print(f"[fsg5-scene] PASS right=[{r[0]:.3f},{r[1]:.3f}] left=[{l[0]:.3f},{l[1]:.3f}] chord_max_mm={1000*chord:.3f}")


if __name__ == "__main__":
    self_test()
