"""Perfect *local* stereo matcher for Classroom-Oracle-1.

The input is one rendered binocular tangent observation containing RGB, per-pixel
Blender instance ids and the Position pass for both eyes.  Truth is consumed only
for this observation.  A left truth point is accepted when it is inside the
rectified left core and its reprojection is inside supported right-eye core data
with the same instance id.  No SGBM disparity/depth search bound is applied.

The returned record deliberately mirrors the subset of ``fsg_stereo.compute``
used by the FSG6f / persistent-map stack.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from fsg_geometry import head_to_world, make_calibration, pixels, rays_h, world_to_head
from fsg_stereo import rectification, remap, support_mask


def _validate_observation(c: dict, obs: dict[str, np.ndarray]) -> None:
    expected = {
        "rgb_L", "rgb_R", "instance_L", "instance_R",
        "position_w_L", "position_w_R",
    }
    if set(obs) != expected:
        raise ValueError(f"oracle observation must contain exactly {sorted(expected)}")
    w, h = c["image_size_wh"]
    for side in ("L", "R"):
        rgb = np.asarray(obs[f"rgb_{side}"])
        ids = np.asarray(obs[f"instance_{side}"])
        pos = np.asarray(obs[f"position_w_{side}"])
        if rgb.shape != (h, w, 3) or pos.shape != (h, w, 3) or ids.shape != (h, w):
            raise ValueError(f"bad {side} observation shape")
        if not np.isfinite(rgb).all():
            raise ValueError(f"non-finite {side} RGB")
        if ids.dtype.kind not in "iu" or np.any(ids < 0):
            raise ValueError(f"bad {side} instance ids")


def _project_rectified_full(c: dict, r: dict, xyz_h: np.ndarray, side: str) -> tuple[np.ndarray, np.ndarray]:
    """Project H-frame points to the full rectified raster for one eye."""
    if side not in ("L", "R"):
        raise ValueError("side must be L or R")
    eye = c["eyes"][0 if side == "L" else 1]
    p = np.asarray(xyz_h, float).reshape(-1, 3)
    xyz_c = (p - np.asarray(eye["centre_h_m"], float)) @ np.asarray(eye["R_hc"], float)
    rr = np.asarray(r["R1" if side == "L" else "R2"], float)
    xyz_rect = xyz_c @ rr.T
    krect = np.asarray(r["P1" if side == "L" else "P2"], float)[:, :3]
    a = xyz_rect @ krect.T
    with np.errstate(divide="ignore", invalid="ignore"):
        uv = a[:, :2] / a[:, 2:3]
    return uv, xyz_rect[:, 2]


def compute(c: dict, obs: dict[str, np.ndarray]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Return oracle record, metadata and binocular state for one current look."""
    _validate_observation(c, obs)
    r = rectification(c)
    w, h = c["image_size_wh"]

    colours: dict[str, np.ndarray] = {}
    ids: dict[str, np.ndarray] = {}
    pos_w: dict[str, np.ndarray] = {}
    raw_support: dict[str, np.ndarray] = {}
    for side in ("L", "R"):
        colours[side] = remap(np.asarray(obs[f"rgb_{side}"], np.float32), r, side, cv2.INTER_LINEAR)
        ids[side] = remap(np.asarray(obs[f"instance_{side}"], np.float32), r, side, cv2.INTER_NEAREST).astype(np.int32)
        # Position is sampled rather than interpolated.  Mixing world positions at a depth edge
        # would manufacture geometry that Blender never observed.
        pos_w[side] = remap(np.asarray(obs[f"position_w_{side}"], np.float32), r, side, cv2.INTER_NEAREST)
        raw_support[side] = support_mask(c, r, side)

    x, y, cw, ch = map(int, r["crop_xywh"])
    sl = np.s_[y:y + ch, x:x + cw]

    left_w = pos_w["L"][sl].astype(np.float64)
    left_h = world_to_head(c, left_w)
    left_ids = ids["L"][sl]
    left_support = raw_support["L"][sl]
    finite_left = np.isfinite(left_h).all(axis=-1) & (left_ids > 0) & left_support

    flat_h = left_h.reshape(-1, 3)
    uv_r_full, z_r = _project_rectified_full(c, r, flat_h, "R")
    uv_r = uv_r_full - np.array([x, y], float)
    ur = uv_r[:, 0]
    vr = uv_r[:, 1]
    inside = np.isfinite(uv_r).all(axis=1) & np.isfinite(z_r) & (z_r > 1e-9)
    inside &= (ur >= 0.0) & (ur <= cw - 1.0) & (vr >= 0.0) & (vr <= ch - 1.0)

    # Reprojection is sampled at the nearest rectified right pixel.  The oracle's binocular
    # visibility rule is semantic: that supported right pixel must see the same instance.
    # This is the recovered Classroom-Oracle-1 contract and rejects ordinary half-occlusion.
    ur_safe = np.where(np.isfinite(ur), np.clip(ur, 0, cw - 1), 0.0)
    vr_safe = np.where(np.isfinite(vr), np.clip(vr, 0, ch - 1), 0.0)
    ui = np.rint(ur_safe).astype(np.int32)
    vi = np.rint(vr_safe).astype(np.int32)
    ids_r_core = ids["R"][sl]
    sup_r_core = raw_support["R"][sl]
    sampled_r_id = ids_r_core[vi, ui]
    sampled_r_support = sup_r_core[vi, ui]

    same_instance = sampled_r_id == left_ids.reshape(-1)
    valid_flat = finite_left.reshape(-1) & inside & sampled_r_support & same_instance
    valid = valid_flat.reshape(ch, cw)

    point = left_h.astype(np.float32)
    point[~valid] = np.nan
    eye_l = np.asarray(c["eyes"][0]["centre_h_m"], float)
    rng = np.linalg.norm(left_h - eye_l, axis=-1)
    rng = np.where(valid, rng, np.nan).astype(np.float32)

    # Right RGB is the same rectified/cropped tangent raster, not a correspondence warp.
    record: dict[str, Any] = {
        "xyz_h": point,
        "valid": valid,
        "range_left_m": rng,
        "instance_id": left_ids.astype(np.int32, copy=True),
        "rgb_left": colours["L"][sl].astype(np.float32, copy=True),
        "rgb_right": colours["R"][sl].astype(np.float32, copy=True),
        "raw_support_L": left_support.astype(bool, copy=True),
        "raw_support_R": raw_support["R"][sl].astype(bool, copy=True),
        "instance_id_R": ids_r_core.astype(np.int32, copy=True),
        "right_reprojection_uv": uv_r.reshape(ch, cw, 2).astype(np.float32),
        "right_reprojection_instance": sampled_r_id.reshape(ch, cw).astype(np.int32),
        "crop_xywh": np.asarray(r["crop_xywh"], np.int32),
    }
    metadata = {
        "schema": "ClassroomOracle1-local-perfect-stereo-v1",
        "valid_count": int(valid.sum()),
        "core_pixels": int(valid.size),
        "valid_fraction_core": float(valid.mean()),
        "oracle": "left Blender Position + right supported same-instance reprojection",
        "depth_search_bound_applied": False,
        "sgbm_called": False,
        "half_occlusion_rule": "right reprojection must be in supported core and see same instance",
        "point_frame": c["map_frame"],
    }
    state = {
        "ids_left": left_ids.astype(np.int32, copy=True),
        "ids_right": ids_r_core.astype(np.int32, copy=True),
        "raw_support_L": left_support.astype(bool, copy=True),
        "raw_support_R": raw_support["R"][sl].astype(bool, copy=True),
    }
    return record, metadata, state


def _plane_observation(c: dict, z_h: float, left_id: int = 7, right_id: int = 7) -> dict[str, np.ndarray]:
    """Synthetic truth fixture for the self-test: a head-frame fronto-parallel plane."""
    w, h = c["image_size_wh"]
    uv = pixels(w, h)
    out: dict[str, np.ndarray] = {}
    for side_i, side in enumerate(("L", "R")):
        eye = c["eyes"][side_i]
        d = rays_h(eye, uv)
        o = np.asarray(eye["centre_h_m"], float)
        with np.errstate(divide="ignore", invalid="ignore"):
            t = (z_h - o[2]) / d[..., 2]
        p_h = o + d * t[..., None]
        p_w = head_to_world(c, p_h)
        u = uv[..., 0] / max(1, w - 1)
        v = uv[..., 1] / max(1, h - 1)
        rgb = np.stack((0.2 + 0.6 * u, 0.2 + 0.6 * v, 0.3 + 0.2 * u * v), axis=-1)
        out[f"rgb_{side}"] = rgb.astype(np.float32)
        iid = left_id if side == "L" else right_id
        out[f"instance_{side}"] = np.full((h, w), iid, np.int32)
        out[f"position_w_{side}"] = p_w.astype(np.float32)
    return out


def self_test() -> list[str]:
    fails: list[str] = []
    c = make_calibration("small", 3.0, -2.0, 2.1)
    rec, meta, _ = compute(c, _plane_observation(c, -2.0))
    if int(rec["valid"].sum()) < 0.75 * rec["valid"].size:
        fails.append("near plane lost too much binocular-valid support")
    if meta["depth_search_bound_applied"] or meta["sgbm_called"]:
        fails.append("oracle metadata claims a matcher/range restriction")

    # Farther than the retired SGBM 4.5 m bound must remain measurable.
    far, _, _ = compute(c, _plane_observation(c, -8.0))
    if int(far["valid"].sum()) < 0.70 * far["valid"].size:
        fails.append("8 m plane was incorrectly rejected by a hidden range bound")

    # Same-instance reprojection is load-bearing: changing only the right id kills support.
    occ, _, _ = compute(c, _plane_observation(c, -2.0, left_id=7, right_id=8))
    if int(occ["valid"].sum()) != 0:
        fails.append("right-eye different instance did not reject the left truth point")

    finite = rec["valid"] & np.isfinite(rec["xyz_h"]).all(axis=-1)
    if finite.any() and abs(float(np.nanmedian(rec["xyz_h"][..., 2])) + 2.0) > 2e-4:
        fails.append("oracle metric geometry is not the truth plane")
    return fails


def _main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--case", type=Path, help="folder containing calibration.json and oracle_observation.npz")
    args = ap.parse_args()
    if args.self_test:
        bad = self_test()
        for item in bad:
            print("[classroom-oracle1-matcher] FAIL", item)
        print("[classroom-oracle1-matcher] self-test", "FAILED" if bad else "PASS")
        raise SystemExit(bool(bad))
    if args.case is None:
        ap.error("pass --self-test or --case")
    c = json.loads((args.case / "calibration.json").read_text())
    with np.load(args.case / "oracle_observation.npz", allow_pickle=False) as z:
        obs = {k: z[k] for k in z.files}
    rec, meta, state = compute(c, obs)
    np.savez_compressed(args.case / "oracle_result.npz", **rec)
    (args.case / "oracle_summary.json").write_text(json.dumps(meta, indent=2) + "\n")
    np.savez_compressed(args.case / "oracle_state.npz", **state)
    print("[classroom-oracle1-matcher] COMPLETE", json.dumps(meta, sort_keys=True))


if __name__ == "__main__":
    _main()
