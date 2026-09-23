"""Pre-control reference/guidance builder for Demo-Tabletop-1.

NEW Demo-Tabletop-1 helper (documented addition). In Demo Mode evaluator truth
is explicitly permitted on the control path, so unlike REAL-1 this builder runs
BEFORE observer control and needs no observer seal. It exists so the demo does
not have to copy the REAL-1 reference renderer: the two pure geometry helpers
are imported from `fullscene_real1_reference` unchanged, and the scene comes
from the same evaluator-side `reality1_scene` the acquisition renderer uses.

It produces, for the procedural `tabletop_cloth` fixture:
  - reference RGB / depth(range) / instance panoramas on the fixed grid;
  - a dynamic positive-object enumeration with live labels;
  - per-object deterministic visibility guidance.

Nothing here supplies foreground metric geometry. Reference depth is used only
to mask, to validate, and to describe the declared background layer.
"""
from __future__ import annotations

from typing import Any

import numpy as np

# Reused unchanged from the established REAL-1 reference renderer.
from fullscene_real1_reference import _equirect_directions, _sample_texture


def chamfer_interior_distance(mask: np.ndarray) -> np.ndarray:
    """Deterministic 3x4 chamfer distance to the complement of `mask`.

    Two sequential passes over the raster, integer weights 3 (orthogonal) and 4
    (diagonal). Cells outside `mask` are 0. No SciPy dependency, no randomness,
    and identical for every object: the same transform is applied to seed masks
    and to uncovered-support masks.
    """
    m = np.asarray(mask, bool)
    BIG = np.int32(1 << 28)
    d = np.where(m, BIG, np.int32(0)).astype(np.int32)
    h, w = d.shape
    # Forward pass.
    for y in range(h):
        row = d[y]
        prev = d[y - 1] if y > 0 else None
        for x in range(w):
            if row[x] == 0:
                continue
            best = row[x]
            if x > 0:
                best = min(best, row[x - 1] + 3)
            if prev is not None:
                best = min(best, prev[x] + 3)
                if x > 0:
                    best = min(best, prev[x - 1] + 4)
                if x + 1 < w:
                    best = min(best, prev[x + 1] + 4)
            row[x] = best
    # Backward pass.
    for y in range(h - 1, -1, -1):
        row = d[y]
        nxt = d[y + 1] if y + 1 < h else None
        for x in range(w - 1, -1, -1):
            if row[x] == 0:
                continue
            best = row[x]
            if x + 1 < w:
                best = min(best, row[x + 1] + 3)
            if nxt is not None:
                best = min(best, nxt[x] + 3)
                if x + 1 < w:
                    best = min(best, nxt[x + 1] + 4)
                if x > 0:
                    best = min(best, nxt[x - 1] + 4)
            row[x] = best
    return d


def _chamfer_fast(mask: np.ndarray) -> np.ndarray:
    """Vectorised equivalent of the chamfer transform above.

    Same 3/4 weights and same fixed point; iterated min-plus relaxation over the
    8-neighbourhood until nothing changes. Used because the scalar version is
    too slow on a 2048x1024 raster. Agreement with the scalar reference is
    asserted by self_test() on small rasters.
    """
    m = np.asarray(mask, bool)
    BIG = np.int32(1 << 28)
    d = np.where(m, BIG, np.int32(0)).astype(np.int32)
    if not m.any():
        return d
    while True:
        prev = d
        cand = [d]
        for dy, dx, wgt in ((-1, 0, 3), (1, 0, 3), (0, -1, 3), (0, 1, 3),
                            (-1, -1, 4), (-1, 1, 4), (1, -1, 4), (1, 1, 4)):
            s = np.full_like(d, BIG)
            ys = slice(max(0, dy), d.shape[0] + min(0, dy))
            yd = slice(max(0, -dy), d.shape[0] + min(0, -dy))
            xs = slice(max(0, dx), d.shape[1] + min(0, dx))
            xd = slice(max(0, -dx), d.shape[1] + min(0, -dx))
            s[yd, xd] = np.minimum(BIG, d[ys, xs] + wgt)
            cand.append(s)
        d = np.minimum.reduce(cand)
        d[~m] = 0
        if np.array_equal(d, prev):
            return d


def deepest_interior_cell(mask: np.ndarray) -> tuple[int, int] | None:
    """Deepest interior cell of `mask`, ties broken by (-distance, y, x).

    This is the demo's single deterministic "look here" rule. It is used for
    both the oracle seed gaze and the oracle redirect gaze so no object gets a
    bespoke rule, and it deliberately avoids the object-centre default that
    REAL-1S showed can land on an occluder.
    """
    m = np.asarray(mask, bool)
    if not m.any():
        return None
    d = _chamfer_fast(m)
    best = int(d.max())
    ys, xs = np.nonzero(d == best)
    order = np.lexsort((xs, ys))
    return int(ys[order[0]]), int(xs[order[0]])


def cell_to_gaze(y: int, x: int, width: int, height: int) -> tuple[float, float]:
    """Inverse of the fixed equirect convention used by spherical_zbuffer."""
    yaw = (float(x) + 0.5) / float(width) * 360.0 - 180.0
    pitch = 90.0 - (float(y) + 0.5) / float(height) * 180.0
    return yaw, pitch


def build_reference(fixture: str, width: int, height: int, chunk: int = 65536) -> dict[str, Any]:
    """Render the evaluator reference panorama and enumerate positive objects."""
    import reality1_public as reality_public
    import reality1_scene as scene_spec
    from fsg_scene import ray_mesh, triangulate_objects

    if str(fixture) != str(reality_public.FIXTURE):
        raise RuntimeError(f"demo fixture {fixture!r} is not the established fixture")

    objects = scene_spec.scene_objects(fixture)
    mesh = triangulate_objects(objects)
    scene_spec.validate_mesh(mesh)

    # Live label lookup, enumerated dynamically; no numeric id is written here.
    labels: dict[int, str] = {}
    for piece in objects:
        oid = int(piece["instance_id"])
        if oid <= 0:
            continue
        name = str(piece.get("name", ""))
        parts = name.split("_")
        prev = labels.get(oid)
        if prev is None:
            labels[oid] = name
        else:
            shared = []
            for a, b in zip(prev.split("_"), parts):
                if a != b:
                    break
                shared.append(a)
            labels[oid] = "_".join(shared) if shared else prev

    _yaw, _pitch, dirs = _equirect_directions(width, height)
    flat = dirs.reshape(-1, 3)
    origin = np.zeros(3)
    depth = np.full(width * height, np.nan, np.float32)
    inst = np.zeros(width * height, np.int32)
    lin = np.zeros((width * height, 3), np.float32)
    textures: dict[int, np.ndarray] = {}

    for lo in range(0, len(flat), int(chunk)):
        hi = min(lo + int(chunk), len(flat))
        hit = ray_mesh(origin, flat[lo:hi], mesh)
        ids = np.asarray(hit["instance_id"], np.int32)
        rng = np.asarray(hit["range_m"], np.float64)
        tri = np.asarray(hit["triangle"], np.int64)
        good = (tri >= 0) & np.isfinite(rng)
        depth[lo:hi][good] = rng[good].astype(np.float32)
        inst[lo:hi] = ids
        for i in np.unique(ids[good]):
            if int(i) <= 0:
                continue
            sel = good & (ids == i)
            if int(i) not in textures:
                textures[int(i)] = np.asarray(scene_spec.scene_texture(fixture, int(i)), np.float32)
            uv = np.einsum("ni,nij->nj", np.asarray(hit["barycentric"])[sel], mesh["triangle_uv"][tri[sel]])
            lin[lo:hi][sel] = _sample_texture(textures[int(i)], uv)

    return {
        "depth": depth.reshape(height, width),
        "instance": inst.reshape(height, width),
        "rgb_linear": lin.reshape(height, width, 3),
        "labels": labels,
        "mesh": mesh,
        "truth_digest": str(scene_spec.truth_digest()),
        "width": int(width),
        "height": int(height),
    }


def reference_range_along(mesh: dict, directions: np.ndarray, chunk: int = 65536) -> tuple[np.ndarray, np.ndarray]:
    """Exact reference first-hit range and instance along arbitrary directions.

    Used only to VALIDATE stereo samples. It never returns a coordinate that is
    written into foreground geometry.
    """
    from fsg_scene import ray_mesh
    d = np.asarray(directions, float).reshape(-1, 3)
    rng = np.full(len(d), np.nan)
    ids = np.zeros(len(d), np.int32)
    origin = np.zeros(3)
    for lo in range(0, len(d), int(chunk)):
        hi = min(lo + int(chunk), len(d))
        hit = ray_mesh(origin, d[lo:hi], mesh)
        tri = np.asarray(hit["triangle"], np.int64)
        good = tri >= 0
        r = np.asarray(hit["range_m"], float)
        rng[lo:hi][good] = r[good]
        ids[lo:hi] = np.asarray(hit["instance_id"], np.int32)
    return rng, ids


def self_test() -> None:
    rng = np.random.default_rng(11)
    for _ in range(6):
        m = rng.random((17, 23)) < 0.55
        a = chamfer_interior_distance(m)
        b = _chamfer_fast(m)
        if not np.array_equal(a, b):
            raise AssertionError("fast chamfer disagrees with the scalar reference")
    m = np.zeros((9, 9), bool)
    m[2:7, 2:7] = True
    cell = deepest_interior_cell(m)
    if cell != (4, 4):
        raise AssertionError(f"deepest interior of a square block should be its centre, got {cell}")
    if deepest_interior_cell(np.zeros((4, 4), bool)) is not None:
        raise AssertionError("empty mask must yield no cell")
    y, x = 0, 0
    yaw, pitch = cell_to_gaze(y, x, 2048, 1024)
    if not (abs(yaw + 179.912) < 1e-2 and abs(pitch - 89.912) < 1e-2):
        raise AssertionError(f"cell_to_gaze convention drifted: {yaw} {pitch}")
    print("[demo-tabletop1-reference] PASS chamfer_agrees=true deepest_interior=true gaze_convention=true")


if __name__ == "__main__":
    self_test()
