"""FSG4 Increment-4 evaluation fixtures.

Two opaque planar objects are mirror placements of the same basic FSG3 surface.
Their public identifiers are opaque. Geometry and truth are unavailable to the
active host/policy and are used only by Blender acquisition and post-hoc eval.
"""
from __future__ import annotations
import hashlib
import json
import math
import numpy as np
from fsg_scene import quad, texture
import fsg4_public as public

OBJECT_Z_M = -2.10
OBJECT_WIDTH_M = 0.95
OBJECT_HEIGHT_M = 0.32
TILT_DEG = 10.0
BACKGROUND_Z_M = -3.50
BACKGROUND_SIZE_M = (4.0, 2.8)
TRUTH_GRID_WH = (238, 80)
TRUTH_COVER_RADIUS_M = 0.015

# Opaque fixture names intentionally do not reveal the direction of the frontier.
# The two placements are mirrored and use distinct procedural textures.
FIXTURE = {
    "case_a": {"centre_x_m": -0.32, "texture_tag": 0},
    "case_b": {"centre_x_m": +0.32, "texture_tag": 1},
}


def object_centre(fixture: str) -> np.ndarray:
    return np.array([FIXTURE[fixture]["centre_x_m"], 0.0, OBJECT_Z_M], dtype=float)


def object_axes() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    a = math.radians(TILT_DEG)
    right = np.array([math.cos(a), 0.0, math.sin(a)], dtype=float)
    up = np.array([0.0, 1.0, 0.0], dtype=float)
    normal = np.cross(right, up)
    normal /= np.linalg.norm(normal)
    return right, up, normal


def scene_objects(fixture: str) -> list[dict]:
    if fixture not in public.FIXTURES:
        raise ValueError(f"unknown fixture {fixture}")
    r, u, _ = object_axes()
    return [
        quad(object_centre(fixture), r, u, OBJECT_WIDTH_M, OBJECT_HEIGHT_M,
             public.OBJECT_ID, f"fsg4_{fixture}_object"),
        quad([0.0, 0.0, BACKGROUND_Z_M], [1, 0, 0], [0, 1, 0],
             BACKGROUND_SIZE_M[0], BACKGROUND_SIZE_M[1],
             public.BACKGROUND_ID, f"fsg4_{fixture}_background"),
    ]


def scene_texture(fixture: str, instance: int, size: int = 512) -> np.ndarray:
    if fixture not in public.FIXTURES:
        raise ValueError(f"unknown fixture {fixture}")
    tag = int(FIXTURE[fixture]["texture_tag"])
    # fsg_scene.texture is deterministic; offset both object IDs by a fixture tag
    # so case_a and case_b are distinct textures, fixed across MC rendering seeds.
    return texture(int(instance) + 80000 + 100 * tag, size)


def truth_spec(fixture: str) -> dict:
    return {
        "id": f"FSG4-{fixture}-truth-v1",
        "public_spec_sha256": public.public_digest(),
        "fixture": fixture,
        "object_centre_h_m": object_centre(fixture).tolist(),
        "object_size_m": [OBJECT_WIDTH_M, OBJECT_HEIGHT_M],
        "object_tilt_deg": TILT_DEG,
        "background_z_h_m": BACKGROUND_Z_M,
        "truth_grid_wh": list(TRUTH_GRID_WH),
        "truth_cover_radius_m": TRUTH_COVER_RADIUS_M,
        "texture_tag": int(FIXTURE[fixture]["texture_tag"]),
    }


def truth_digest(fixture: str) -> str:
    return hashlib.sha256(
        json.dumps(truth_spec(fixture), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def validate_mesh(fixture: str, mesh: dict) -> None:
    wanted = scene_objects(fixture)
    triangles = mesh["triangles_h"]
    ids = mesh["instance_ids"]
    if triangles.shape != (4, 3, 3) or ids.shape != (4,):
        raise ValueError("unexpected FSG4 mesh size")
    if set(ids.tolist()) != {public.OBJECT_ID, public.BACKGROUND_ID}:
        raise ValueError("unexpected FSG4 object IDs")
    for obj in wanted:
        exp = np.asarray(obj["vertices_h"], float)
        got = triangles[ids == obj["instance_id"]]
        if len(got) != 2:
            raise ValueError("two triangles required per quad")
        d = np.linalg.norm(got[:, :, None, :] - exp[None, None, :, :], axis=-1)
        if np.max(np.min(d, axis=-1)) > 2e-5:
            raise ValueError("exported Blender mesh disagrees with FSG4 specification")


def surface_coordinates(fixture: str, xyz: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    r, u, n = object_axes()
    q = np.asarray(xyz, float) - object_centre(fixture)
    return q @ r, q @ u, q @ n


def angular_span_deg(fixture: str) -> tuple[float, float]:
    r, _, _ = object_axes()
    c = object_centre(fixture)
    a = c - 0.5 * OBJECT_WIDTH_M * r
    b = c + 0.5 * OBJECT_WIDTH_M * r
    return tuple(float(np.degrees(np.arctan2(x[0], -x[2]))) for x in (a, b))


def _interval_coverage(span: tuple[float, float], yaws: list[float], half: float = 6.0) -> float:
    lo, hi = span
    ints = []
    for y in yaws:
        a, b = max(lo, y-half), min(hi, y+half)
        if b > a:
            ints.append((a, b))
    if not ints:
        return 0.0
    ints.sort()
    total = 0.0
    s, e = ints[0]
    for a, b in ints[1:]:
        if a <= e:
            e = max(e, b)
        else:
            total += e-s
            s, e = a, b
    total += e-s
    return total / (hi-lo)


def self_test() -> None:
    r, u, n = object_axes()
    if not np.allclose([np.linalg.norm(r), np.linalg.norm(u), np.linalg.norm(n)], [1, 1, 1], atol=1e-12):
        raise AssertionError("axes not unit")
    if max(abs(r@u), abs(r@n), abs(u@n)) > 1e-12:
        raise AssertionError("axes not orthogonal")
    spans = {f: angular_span_deg(f) for f in public.FIXTURES}
    # At the common seed one fixture must expose only a left frontier and the
    # mirrored fixture only a right frontier. Keep a safe margin from +/-6 deg.
    la = spans["case_a"]; lb = spans["case_b"]
    if not (la[0] < -6.0 and la[1] < 5.0 and la[1] > 2.0):
        raise AssertionError(f"case_a seed geometry wrong: {la}")
    if not (lb[0] > -5.0 and lb[0] < -2.0 and lb[1] > 6.0):
        raise AssertionError(f"case_b seed geometry wrong: {lb}")
    # Five local active looks can bracket each far edge.
    if not (-20.0-6.0 < la[0] < -20.0+6.0):
        raise AssertionError("case_a five-look active reach wrong")
    if not (20.0-6.0 < lb[1] < 20.0+6.0):
        raise AssertionError("case_b five-look active reach wrong")
    # The fixed symmetric scan is deliberately a reasonable but incomplete
    # non-adaptive baseline on this one-sided-frontier family.
    scan = list(public.SCAN_YAWS_DEG)
    scan_cov = {f: _interval_coverage(spans[f], scan) for f in public.FIXTURES}
    if not all(0.70 < v < 0.90 for v in scan_cov.values()):
        raise AssertionError(f"fixed-scan analytic design outside intended range: {scan_cov}")
    print("[fsg4-scene] PASS " + " ".join(
        f"{f}=[{spans[f][0]:.3f},{spans[f][1]:.3f}] scan_ideal={scan_cov[f]:.3f}"
        for f in public.FIXTURES))


if __name__ == "__main__":
    self_test()
