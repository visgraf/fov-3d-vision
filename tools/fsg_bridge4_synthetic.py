"""Bridge-4 controlled analytic two-plane acquisition generator.

Purpose
-------
Generate a family of FSG observation directories in which the camera, tangent frame,
near-object silhouette, textures, matcher contract, baseline, and vergence are fixed,
while ONLY the farther plane depth is swept. Three deterministic texture realizations
are repeated at every depth to reduce dependence on one accidental pattern.

No Blender and no stereo are run here. The generated observation contract is exactly:
    rgb_L, rgb_R, instance_L, instance_R
Evaluator truth lives only under evaluation_only/.

Geometry
--------
H frame: +X right, +Y up, -Z forward. The near surface is a finite fronto-parallel
rectangle at z=-NEAR_DEPTH_M. The far surface is a full fronto-parallel plane at
z=-far_depth. A ray sees the near rectangle if its near-plane hit falls inside the
fixed rectangle; otherwise it sees the far plane.

The near rectangle is fixed across the sweep, so the instance masks are identical for
all far depths. The surface textures are deterministic continuous functions of
(x/depth, y/depth), keeping angular texture scale comparable while preserving proper
binocular parallax.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
from typing import Any

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fsg_geometry import json_write, make_calibration, pixels, rays_h

SCHEMA = "FSG-BLEND-BRIDGE4-synthetic-v1"
SOURCE = "analytic_two_plane_tangent_perspective"
PROFILE = "small"
YAW_DEG = 0.0
PITCH_DEG = 0.0
VERGENCE_M = 2.10
IPD_M = 0.063
NEAR_DEPTH_M = 1.40
FAR_DEPTHS_M = (1.60, 1.80, 2.00, 2.20, 2.40, 2.80, 3.20)
TEXTURE_SEEDS = (2111, 2112, 2113)
NEAR_CENTER_ANGLE_X_DEG = 2.0
NEAR_WIDTH_DEG = 5.0
NEAR_HEIGHT_DEG = 6.0
NEAR_ID = 1
FAR_ID = 2


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _surface_texture(xyz: np.ndarray, depth: float, seed: int, role: str) -> np.ndarray:
    """Continuous aperiodic-ish RGB texture with fixed angular scale.

    The function is deterministic and evaluated in normalized plane coordinates. Near
    and far surfaces use independent coefficient sets for the same texture seed.
    """
    role_offset = 0 if role == "near" else 100_000
    rng = np.random.default_rng(int(seed) + role_offset)
    u = np.asarray(xyz[..., 0], np.float64) / float(depth)
    v = np.asarray(xyz[..., 1], np.float64) / float(depth)
    # A sum of oblique Fourier components: rich, continuous and non-axis-aligned.
    rgb = np.zeros(u.shape + (3,), np.float64)
    base = np.array([0.47, 0.39, 0.31]) if role == "near" else np.array([0.34, 0.40, 0.46])
    rgb[...] = base
    for channel in range(3):
        for _ in range(10):
            fx = rng.uniform(12.0, 58.0)
            fy = rng.uniform(9.0, 51.0)
            phase = rng.uniform(-math.pi, math.pi)
            amp = rng.uniform(0.018, 0.055)
            rgb[..., channel] += amp * np.sin(2.0 * math.pi * (fx * u + fy * v) + phase)
        # A low-frequency term keeps broad photometric structure without periodic stripes.
        fx = rng.uniform(2.0, 6.0)
        fy = rng.uniform(2.0, 6.0)
        phase = rng.uniform(-math.pi, math.pi)
        rgb[..., channel] += 0.045 * np.sin(2.0 * math.pi * (fx * u + fy * v) + phase)
    # Mild deterministic cross-channel modulation.
    rgb[..., 0] += 0.025 * np.sin(2.0 * math.pi * (17.0 * u - 11.0 * v) + 0.4)
    rgb[..., 1] += 0.020 * np.sin(2.0 * math.pi * (13.0 * u + 19.0 * v) - 0.7)
    rgb[..., 2] += 0.022 * np.sin(2.0 * math.pi * (23.0 * u - 7.0 * v) + 1.1)
    return np.clip(rgb, 0.02, 0.98).astype(np.float32)


def _plane_hit(centre: np.ndarray, dirs: np.ndarray, depth: float) -> tuple[np.ndarray, np.ndarray]:
    """Intersect unit rays with z=-depth in H. Returns t/range and xyz."""
    centre = np.asarray(centre, np.float64)
    dirs = np.asarray(dirs, np.float64)
    dz = dirs[..., 2]
    with np.errstate(divide="ignore", invalid="ignore"):
        t = (-float(depth) - centre[2]) / dz
    xyz = centre + dirs * t[..., None]
    ok = np.isfinite(t) & (t > 0.0) & (dz < -1e-8)
    t = np.where(ok, t, np.nan)
    xyz = np.where(ok[..., None], xyz, np.nan)
    return t, xyz


def _near_rectangle(depth: float) -> tuple[float, float, float, float]:
    cx = float(depth) * math.tan(math.radians(NEAR_CENTER_ANGLE_X_DEG))
    cy = 0.0
    hw = float(depth) * math.tan(math.radians(NEAR_WIDTH_DEG / 2.0))
    hh = float(depth) * math.tan(math.radians(NEAR_HEIGHT_DEG / 2.0))
    return cx, cy, hw, hh


def render_eye(cal: dict[str, Any], eye: dict[str, Any], far_depth: float, texture_seed: int) -> dict[str, np.ndarray]:
    w, h = map(int, cal["image_size_wh"])
    uv = pixels(w, h)
    dirs = rays_h(eye, uv)
    centre = np.asarray(eye["centre_h_m"], np.float64)
    near_range, near_xyz = _plane_hit(centre, dirs, NEAR_DEPTH_M)
    far_range, far_xyz = _plane_hit(centre, dirs, far_depth)
    cx, cy, hw, hh = _near_rectangle(NEAR_DEPTH_M)
    near_hit = (
        np.isfinite(near_range)
        & (np.abs(near_xyz[..., 0] - cx) <= hw)
        & (np.abs(near_xyz[..., 1] - cy) <= hh)
    )
    if not np.isfinite(far_range).all():
        raise RuntimeError("far plane failed to cover the declared tangent raster")
    ids = np.where(near_hit, NEAR_ID, FAR_ID).astype(np.int32)
    ranges = np.where(near_hit, near_range, far_range).astype(np.float32)
    xyz = np.where(near_hit[..., None], near_xyz, far_xyz).astype(np.float32)
    rgb_near = _surface_texture(near_xyz, NEAR_DEPTH_M, texture_seed, "near")
    rgb_far = _surface_texture(far_xyz, far_depth, texture_seed, "far")
    rgb = np.where(near_hit[..., None], rgb_near, rgb_far).astype(np.float32)
    return {"rgb": rgb, "instance_id": ids, "range_m": ranges, "xyz_h": xyz}


def _linear_to_u8(rgb: np.ndarray) -> np.ndarray:
    a = np.clip(np.asarray(rgb, np.float64), 0.0, 1.0)
    a = np.where(a <= 0.0031308, 12.92 * a, 1.055 * np.power(a, 1 / 2.4) - 0.055)
    return np.rint(255.0 * a).astype(np.uint8)


def condition_name(far_depth: float, texture_seed: int) -> str:
    return f"far-{far_depth:.2f}m-seed{int(texture_seed)}".replace(".", "p")


def generate_condition(root: Path, far_depth: float, texture_seed: int) -> dict[str, Any]:
    out = root / condition_name(far_depth, texture_seed)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"condition output must be new or empty: {out}")
    out.mkdir(parents=True, exist_ok=True)
    eval_dir = out / "evaluation_only"
    eval_dir.mkdir()

    cal = make_calibration(
        PROFILE,
        YAW_DEG,
        PITCH_DEG,
        vergence_distance=VERGENCE_M,
        ipd=IPD_M,
        tangent_frame="baseline_projected",
    )
    obs: dict[str, np.ndarray] = {}
    truth_summary: dict[str, Any] = {}
    mask_hashes: dict[str, str] = {}
    for eye in cal["eyes"]:
        side = eye["name"]
        r = render_eye(cal, eye, float(far_depth), int(texture_seed))
        obs[f"rgb_{side}"] = r["rgb"]
        obs[f"instance_{side}"] = r["instance_id"]
        truth_path = eval_dir / f"truth_{side}.npz"
        np.savez_compressed(
            truth_path,
            instance_id=r["instance_id"],
            range_m=r["range_m"],
            xyz_h=r["xyz_h"],
        )
        Image.fromarray(_linear_to_u8(r["rgb"])).save(out / f"{side}.png")
        mask_hashes[side] = hashlib.sha256(r["instance_id"].tobytes()).hexdigest()
        truth_summary[side] = {
            "near_pixels": int((r["instance_id"] == NEAR_ID).sum()),
            "far_pixels": int((r["instance_id"] == FAR_ID).sum()),
            "range_median_near": float(np.median(r["range_m"][r["instance_id"] == NEAR_ID])),
            "range_median_far": float(np.median(r["range_m"][r["instance_id"] == FAR_ID])),
        }

    if set(obs) != {"rgb_L", "rgb_R", "instance_L", "instance_R"}:
        raise RuntimeError("observation contract changed")
    np.savez_compressed(out / "observation.npz", **obs)
    json_write(out / "calibration.json", cal)
    acquisition = {
        "schema": SCHEMA,
        "source": SOURCE,
        "profile": PROFILE,
        "gaze_yaw_pitch_deg": [YAW_DEG, PITCH_DEG],
        "vergence_m": VERGENCE_M,
        "ipd_m": IPD_M,
        "near_depth_m": NEAR_DEPTH_M,
        "far_depth_m": float(far_depth),
        "texture_seed": int(texture_seed),
        "near_instance_id": NEAR_ID,
        "far_instance_id": FAR_ID,
        "near_rectangle": {
            "center_angle_x_deg": NEAR_CENTER_ANGLE_X_DEG,
            "width_deg": NEAR_WIDTH_DEG,
            "height_deg": NEAR_HEIGHT_DEG,
        },
        "tangent_frame_mode": "baseline_projected",
        "sensor_contract": "analytic local padded perspective pair using the native FSG camera geometry",
        "stereo_contract": "host tools/fsg_stereo.py unchanged",
        "truth_in_observation": False,
        "foveated_warp_used": False,
        "stereo_field_used": False,
        "blender_used": False,
        "controller_used": False,
        "fusion_used": False,
        "instance_mask_sha256": mask_hashes,
        "truth_summary": truth_summary,
    }
    json_write(out / "acquisition.json", acquisition)
    json_write(out / "run.json", {
        "schema": "FSG-BLEND-BRIDGE4-run-v1",
        "complete": True,
        "case": "controlled_two_plane_condition",
        "source": SOURCE,
        "profile": PROFILE,
        "far_depth_m": float(far_depth),
        "texture_seed": int(texture_seed),
    })
    return acquisition


def generate_sweep(root: Path, overwrite_empty: bool = False) -> dict[str, Any]:
    root = root.resolve()
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"sweep root must be new or empty: {root}")
    root.mkdir(parents=True, exist_ok=True)
    conditions: list[dict[str, Any]] = []
    for seed in TEXTURE_SEEDS:
        for far in FAR_DEPTHS_M:
            conditions.append(generate_condition(root, far, seed))
    # Strong control: near/far first-hit masks do not change with the far-plane depth.
    for side in ("L", "R"):
        hashes = {c["instance_mask_sha256"][side] for c in conditions}
        if len(hashes) != 1:
            raise RuntimeError(f"instance silhouette changed across controlled depth sweep for eye {side}")
    manifest = {
        "schema": "FSG-BLEND-BRIDGE4-sweep-v1",
        "scientific_question": "does epipolar foreground disparity-capture reach scale with controlled disparity separation?",
        "only_manipulated_scene_variable": "far_plane_depth_m",
        "near_depth_m": NEAR_DEPTH_M,
        "far_depths_m": list(FAR_DEPTHS_M),
        "texture_seeds": list(TEXTURE_SEEDS),
        "condition_count": len(conditions),
        "fixed": {
            "profile": PROFILE,
            "yaw_deg": YAW_DEG,
            "pitch_deg": PITCH_DEG,
            "vergence_m": VERGENCE_M,
            "ipd_m": IPD_M,
            "near_rectangle_center_angle_x_deg": NEAR_CENTER_ANGLE_X_DEG,
            "near_rectangle_width_deg": NEAR_WIDTH_DEG,
            "near_rectangle_height_deg": NEAR_HEIGHT_DEG,
            "tangent_frame": "baseline_projected",
            "matcher": "tools/fsg_stereo.py unchanged",
        },
        "mask_sha256": {
            side: conditions[0]["instance_mask_sha256"][side] for side in ("L", "R")
        },
        "truth_used_only_for_evaluation": True,
        "stereo_run_during_generation": False,
    }
    json_write(root / "bridge4_manifest.json", manifest)
    print(
        "[fsg-bridge4-synthetic] COMPLETE "
        f"conditions={len(conditions)} depths={len(FAR_DEPTHS_M)} textures={len(TEXTURE_SEEDS)} "
        f"near={NEAR_DEPTH_M:.2f}m"
    )
    return manifest


def self_test() -> None:
    cal = make_calibration(
        PROFILE, YAW_DEG, PITCH_DEG, vergence_distance=VERGENCE_M,
        ipd=IPD_M, tangent_frame="baseline_projected"
    )
    a = render_eye(cal, cal["eyes"][0], 1.8, 17)
    b = render_eye(cal, cal["eyes"][0], 2.8, 17)
    assert a["instance_id"].shape == tuple(reversed(cal["image_size_wh"]))
    assert np.array_equal(a["instance_id"], b["instance_id"])
    assert set(np.unique(a["instance_id"])) == {NEAR_ID, FAR_ID}
    assert float(np.std(_linear_to_u8(a["rgb"]))) > 10.0
    assert float(np.median(b["range_m"][b["instance_id"] == FAR_ID])) > float(np.median(a["range_m"][a["instance_id"] == FAR_ID]))
    near_fraction = float((a["instance_id"] == NEAR_ID).mean())
    assert 0.02 < near_fraction < 0.30
    print(f"[fsg-bridge4-synthetic] self-test PASS near_fraction={near_fraction:.4f}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.root is None:
        ap.error("--root is required unless --self-test is used")
    generate_sweep(args.root)


if __name__ == "__main__":
    main()
