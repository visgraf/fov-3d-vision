"""Repository-neutral export helpers for FullScene-REAL-1.

The live adapter is responsible for converting repository/world coordinates to
cyclopean yaw/pitch using the project's established convention. These helpers
then provide deterministic spherical z-buffering and simple NPZ/PLY output.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np


def spherical_zbuffer(yaw_deg: np.ndarray, pitch_deg: np.ndarray, range_m: np.ndarray,
                      object_id: np.ndarray, width: int = 2048, height: int = 1024):
    yaw = np.asarray(yaw_deg, dtype=np.float64).reshape(-1)
    pitch = np.asarray(pitch_deg, dtype=np.float64).reshape(-1)
    rng = np.asarray(range_m, dtype=np.float64).reshape(-1)
    oid = np.asarray(object_id, dtype=np.int64).reshape(-1)
    if not (yaw.shape == pitch.shape == rng.shape == oid.shape):
        raise ValueError("yaw/pitch/range/object_id shape mismatch")
    valid = np.isfinite(yaw) & np.isfinite(pitch) & np.isfinite(rng) & (rng > 0)
    yaw, pitch, rng, oid = yaw[valid], pitch[valid], rng[valid], oid[valid]
    # Equirect convention: yaw [-180,180), pitch [-90,90], top row +90.
    x = np.floor(((yaw + 180.0) % 360.0) / 360.0 * width).astype(np.int64)
    y = np.floor((90.0 - np.clip(pitch, -90.0, 90.0)) / 180.0 * height).astype(np.int64)
    x = np.clip(x, 0, width - 1)
    y = np.clip(y, 0, height - 1)
    flat = y * width + x
    order = np.lexsort((rng, flat))
    flat_s = flat[order]
    first = np.empty(len(order), dtype=bool)
    if len(order):
        first[0] = True
        first[1:] = flat_s[1:] != flat_s[:-1]
    sel = order[first]
    depth = np.full(width * height, np.nan, dtype=np.float32)
    inst = np.zeros(width * height, dtype=np.int32)
    depth[flat[sel]] = rng[sel].astype(np.float32)
    inst[flat[sel]] = oid[sel].astype(np.int32)
    return depth.reshape(height, width), inst.reshape(height, width)


def write_ascii_ply(path: Path, xyz: np.ndarray, object_id: np.ndarray | None = None,
                    rgb: np.ndarray | None = None) -> None:
    path = Path(path)
    xyz = np.asarray(xyz, dtype=np.float64).reshape(-1, 3)
    n = len(xyz)
    if object_id is not None:
        object_id = np.asarray(object_id, dtype=np.int64).reshape(-1)
        if len(object_id) != n:
            raise ValueError("object_id length mismatch")
    if rgb is not None:
        rgb = np.asarray(rgb).reshape(-1, 3)
        if len(rgb) != n:
            raise ValueError("rgb length mismatch")
        rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write("ply\nformat ascii 1.0\n")
        f.write(f"element vertex {n}\n")
        f.write("property float x\nproperty float y\nproperty float z\n")
        if rgb is not None:
            f.write("property uchar red\nproperty uchar green\nproperty uchar blue\n")
        if object_id is not None:
            f.write("property int object_id\n")
        f.write("end_header\n")
        for i, p in enumerate(xyz):
            fields = [f"{p[0]:.9g}", f"{p[1]:.9g}", f"{p[2]:.9g}"]
            if rgb is not None:
                fields += [str(int(v)) for v in rgb[i]]
            if object_id is not None:
                fields.append(str(int(object_id[i])))
            f.write(" ".join(fields) + "\n")


def write_scene_npz(path: Path, xyz: np.ndarray, object_id: np.ndarray,
                    support: np.ndarray | None = None, rgb: np.ndarray | None = None) -> None:
    payload = {
        "xyz": np.asarray(xyz, dtype=np.float32),
        "object_id": np.asarray(object_id, dtype=np.int32),
    }
    if support is not None:
        payload["support"] = np.asarray(support)
    if rgb is not None:
        payload["rgb"] = np.asarray(rgb, dtype=np.uint8)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **payload)


def depth_preview(depth: np.ndarray) -> np.ndarray:
    """Return an 8-bit grayscale depth preview without imposing a scientific metric."""
    d = np.asarray(depth, dtype=np.float32)
    out = np.zeros(d.shape, dtype=np.uint8)
    v = np.isfinite(d) & (d > 0)
    if not np.any(v):
        return out
    lo, hi = np.percentile(d[v], [2.0, 98.0])
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        out[v] = 255
        return out
    t = np.clip((d - lo) / (hi - lo), 0.0, 1.0)
    out[v] = np.round(255.0 * (1.0 - t[v])).astype(np.uint8)
    return out
