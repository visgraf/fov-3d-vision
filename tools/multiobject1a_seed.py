"""Pure second-object seed selection for MultiObject-1a.

The selector knows only 3D samples already labelled with the declared second
object id.  It has no renderer, no scene fixture and no truth access.
"""
from __future__ import annotations

import numpy as np


def xyz_to_yaw_pitch_deg(xyz_h: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    p = np.asarray(xyz_h, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3:
        raise ValueError("xyz_h must be Nx3")
    good = np.all(np.isfinite(p), axis=1)
    p = p[good]
    if len(p) == 0:
        return np.empty(0), np.empty(0)
    r = np.linalg.norm(p, axis=1)
    p = p[r > 0]
    if len(p) == 0:
        return np.empty(0), np.empty(0)
    yaw = np.degrees(np.arctan2(p[:, 0], -p[:, 2]))
    pitch = np.degrees(np.arctan2(p[:, 1], np.hypot(p[:, 0], p[:, 2])))
    return yaw, pitch


def _unit_from_angles(yaw_deg: np.ndarray, pitch_deg: np.ndarray) -> np.ndarray:
    y = np.radians(np.asarray(yaw_deg, float))
    p = np.radians(np.asarray(pitch_deg, float))
    cp = np.cos(p)
    return np.column_stack((cp * np.sin(y), np.sin(p), -cp * np.cos(y)))


def _angles_from_unit(v: np.ndarray) -> tuple[float, float]:
    a = np.asarray(v, float)
    a = a / np.linalg.norm(a)
    yaw = float(np.degrees(np.arctan2(a[0], -a[2])))
    pitch = float(np.degrees(np.arctan2(a[1], np.hypot(a[0], a[2]))))
    return yaw, pitch


def select_prescribed_seed(xyz_h: np.ndarray, grid_deg: float) -> dict:
    """Choose one occupied angular cell nearest the spherical mean.

    Quantizing first prevents a repeatedly observed sliver from dominating only
    because it contributed more pixels.  The returned gaze is the mean direction
    of one actually occupied cell, so it remains anchored in prior object evidence.
    """
    yaw, pitch = xyz_to_yaw_pitch_deg(xyz_h)
    if len(yaw) == 0:
        raise ValueError("no finite second-object evidence")
    g = float(grid_deg)
    if not np.isfinite(g) or g <= 0:
        raise ValueError("grid_deg must be positive")
    qx = np.rint(yaw / g).astype(np.int64)
    qy = np.rint(pitch / g).astype(np.int64)
    keys = np.column_stack((qy, qx))
    uniq, inv = np.unique(keys, axis=0, return_inverse=True)

    cell_dirs = []
    cell_angles = []
    for i, key in enumerate(uniq):
        m = inv == i
        dirs = _unit_from_angles(yaw[m], pitch[m])
        d = dirs.mean(axis=0)
        d /= np.linalg.norm(d)
        cell_dirs.append(d)
        cell_angles.append(_angles_from_unit(d))
    cell_dirs = np.asarray(cell_dirs)
    mean_dir = cell_dirs.mean(axis=0)
    mean_dir /= np.linalg.norm(mean_dir)
    dots = cell_dirs @ mean_dir
    best_dot = float(np.max(dots))
    cand = np.flatnonzero(np.isclose(dots, best_dot, rtol=0.0, atol=1e-15))
    if len(cand) > 1:
        order = np.lexsort((uniq[cand, 1], uniq[cand, 0]))
        bi = int(cand[order[0]])
    else:
        bi = int(cand[0])
    yaw_g, pitch_g = cell_angles[bi]
    mean_yaw, mean_pitch = _angles_from_unit(mean_dir)
    return {
        "probe_gaze_deg": [float(yaw_g), float(pitch_g)],
        "occupied_cells": int(len(uniq)),
        "sample_count": int(len(yaw)),
        "spherical_mean_deg": [float(mean_yaw), float(mean_pitch)],
        "selected_quantized_cell": [int(uniq[bi, 1]), int(uniq[bi, 0])],
        "selected_cell_dot_to_mean": float(dots[bi]),
    }
