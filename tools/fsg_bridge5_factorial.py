"""Bridge-5 controlled 2x2 texture-asymmetry x background-slant generator.

Purpose
-------
Bridge-4 showed that disparity separation alone does not create the detached
foreground-disparity capture seen in the Classroom. Bridge-5 holds the gap near the
Classroom value and independently manipulates two measured Classroom differences:

  1. far/background disparity slant; and
  2. foreground/background local texture-strength asymmetry.

The experiment is a predeclared 2x2 factorial, repeated for three deterministic
texture seeds. No stereo is run by this generator. Observation keys remain exactly
rgb_L, rgb_R, instance_L, instance_R. Analytic truth is quarantined under
evaluation_only/.

H frame: +X right, +Y up, -Z forward.
Near surface: fixed finite fronto-parallel rectangle at 1.40 m.
Far surface: full plane with equation z + Z0 + k*y = 0, where k=0 (flat) or 1.8
(slanted). k=1.8 was chosen prospectively from camera geometry because it produces a
vertical true-disparity slope of about 0.047 px/px, matching the sealed Classroom
measurement (~0.0478 px/px), without consulting any Bridge-5 stereo result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fsg_geometry import json_write, make_calibration, pixels, rays_h

SCHEMA = "FSG-BLEND-BRIDGE5-factorial-v1"
SOURCE = "analytic_texture_slant_factorial"
PROFILE = "small"
YAW_DEG = 0.0
PITCH_DEG = 0.0
VERGENCE_M = 2.10
IPD_M = 0.063
NEAR_DEPTH_M = 1.40
FAR_BASE_DEPTH_M = 2.40
TEXTURE_SEEDS = (2111, 2112, 2113)
NEAR_CENTER_ANGLE_X_DEG = 2.0
NEAR_WIDTH_DEG = 5.0
NEAR_HEIGHT_DEG = 6.0
NEAR_ID = 1
FAR_ID = 2

# Factor A: far-plane geometry.  k=1.8 gives ~0.047 px/px vertical disparity slant.
SLANT_LEVELS = {
    "flat": 0.0,
    "slanted": 1.8,
}
# Factor B: texture evidence. Near texture is frozen; far texture contrast is reduced.
TEXTURE_LEVELS = {
    "equal": 1.0,
    "near2x": 0.44,
}


def _surface_base(role: str) -> np.ndarray:
    return np.array([0.47, 0.39, 0.31], np.float64) if role == "near" else np.array([0.34, 0.40, 0.46], np.float64)


def _surface_texture(xyz: np.ndarray, reference_depth: float, seed: int, role: str, contrast_gain: float = 1.0) -> np.ndarray:
    """Continuous deterministic world-attached texture with controlled contrast.

    Coordinates are normalized by a fixed reference depth, not by local slanted depth,
    so changing far-plane slant produces the geometric warp expected of a physical
    surface instead of a view-locked texture. Contrast gain is applied around the
    role's fixed base colour and therefore changes evidence strength without changing
    the declared mean/base colour.
    """
    role_offset = 0 if role == "near" else 100_000
    rng = np.random.default_rng(int(seed) + role_offset)
    u = np.asarray(xyz[..., 0], np.float64) / float(reference_depth)
    v = np.asarray(xyz[..., 1], np.float64) / float(reference_depth)
    base = _surface_base(role)
    rgb = np.zeros(u.shape + (3,), np.float64)
    rgb[...] = base
    detail = np.zeros_like(rgb)
    for channel in range(3):
        for _ in range(10):
            fx = rng.uniform(12.0, 58.0)
            fy = rng.uniform(9.0, 51.0)
            phase = rng.uniform(-math.pi, math.pi)
            amp = rng.uniform(0.018, 0.055)
            detail[..., channel] += amp * np.sin(2.0 * math.pi * (fx * u + fy * v) + phase)
        fx = rng.uniform(2.0, 6.0)
        fy = rng.uniform(2.0, 6.0)
        phase = rng.uniform(-math.pi, math.pi)
        detail[..., channel] += 0.045 * np.sin(2.0 * math.pi * (fx * u + fy * v) + phase)
    detail[..., 0] += 0.025 * np.sin(2.0 * math.pi * (17.0 * u - 11.0 * v) + 0.4)
    detail[..., 1] += 0.020 * np.sin(2.0 * math.pi * (13.0 * u + 19.0 * v) - 0.7)
    detail[..., 2] += 0.022 * np.sin(2.0 * math.pi * (23.0 * u - 7.0 * v) + 1.1)
    rgb = base + float(contrast_gain) * detail
    return np.clip(rgb, 0.02, 0.98).astype(np.float32)


def _fronto_plane_hit(centre: np.ndarray, dirs: np.ndarray, depth: float) -> tuple[np.ndarray, np.ndarray]:
    centre = np.asarray(centre, np.float64)
    dirs = np.asarray(dirs, np.float64)
    dz = dirs[..., 2]
    with np.errstate(divide="ignore", invalid="ignore"):
        t = (-float(depth) - centre[2]) / dz
    xyz = centre + dirs * t[..., None]
    ok = np.isfinite(t) & (t > 0.0) & (dz < -1e-8)
    return np.where(ok, t, np.nan), np.where(ok[..., None], xyz, np.nan)


def _slanted_far_hit(centre: np.ndarray, dirs: np.ndarray, base_depth: float, slope_k: float) -> tuple[np.ndarray, np.ndarray]:
    """Intersect z + base_depth + slope_k*y = 0."""
    centre = np.asarray(centre, np.float64)
    dirs = np.asarray(dirs, np.float64)
    denom = dirs[..., 2] + float(slope_k) * dirs[..., 1]
    numer = -(centre[2] + float(base_depth) + float(slope_k) * centre[1])
    with np.errstate(divide="ignore", invalid="ignore"):
        t = numer / denom
    xyz = centre + dirs * t[..., None]
    ok = np.isfinite(t) & (t > 0.0) & (denom < -1e-8)
    return np.where(ok, t, np.nan), np.where(ok[..., None], xyz, np.nan)


def _near_rectangle(depth: float) -> tuple[float, float, float, float]:
    cx = float(depth) * math.tan(math.radians(NEAR_CENTER_ANGLE_X_DEG))
    cy = 0.0
    hw = float(depth) * math.tan(math.radians(NEAR_WIDTH_DEG / 2.0))
    hh = float(depth) * math.tan(math.radians(NEAR_HEIGHT_DEG / 2.0))
    return cx, cy, hw, hh


def render_eye(
    cal: dict[str, Any], eye: dict[str, Any], texture_seed: int,
    far_slope_k: float, far_texture_gain: float,
) -> dict[str, np.ndarray]:
    w, h = map(int, cal["image_size_wh"])
    uv = pixels(w, h)
    dirs = rays_h(eye, uv)
    centre = np.asarray(eye["centre_h_m"], np.float64)
    near_range, near_xyz = _fronto_plane_hit(centre, dirs, NEAR_DEPTH_M)
    far_range, far_xyz = _slanted_far_hit(centre, dirs, FAR_BASE_DEPTH_M, far_slope_k)
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
    rgb_near = _surface_texture(near_xyz, NEAR_DEPTH_M, texture_seed, "near", 1.0)
    rgb_far = _surface_texture(far_xyz, FAR_BASE_DEPTH_M, texture_seed, "far", far_texture_gain)
    rgb = np.where(near_hit[..., None], rgb_near, rgb_far).astype(np.float32)
    return {"rgb": rgb, "instance_id": ids, "range_m": ranges, "xyz_h": xyz}


def _linear_to_u8(rgb: np.ndarray) -> np.ndarray:
    a = np.clip(np.asarray(rgb, np.float64), 0.0, 1.0)
    a = np.where(a <= 0.0031308, 12.92 * a, 1.055 * np.power(a, 1 / 2.4) - 0.055)
    return np.rint(255.0 * a).astype(np.uint8)


def condition_name(slant_level: str, texture_level: str, texture_seed: int) -> str:
    return f"{slant_level}-{texture_level}-seed{int(texture_seed)}"


def generate_condition(root: Path, slant_level: str, texture_level: str, texture_seed: int) -> dict[str, Any]:
    slope_k = float(SLANT_LEVELS[slant_level])
    far_gain = float(TEXTURE_LEVELS[texture_level])
    out = root / condition_name(slant_level, texture_level, texture_seed)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"condition output must be new or empty: {out}")
    out.mkdir(parents=True, exist_ok=True)
    eval_dir = out / "evaluation_only"
    eval_dir.mkdir()

    cal = make_calibration(
        PROFILE, YAW_DEG, PITCH_DEG,
        vergence_distance=VERGENCE_M, ipd=IPD_M,
        tangent_frame="baseline_projected",
    )
    obs: dict[str, np.ndarray] = {}
    truth_summary: dict[str, Any] = {}
    mask_hashes: dict[str, str] = {}
    for eye in cal["eyes"]:
        side = eye["name"]
        r = render_eye(cal, eye, int(texture_seed), slope_k, far_gain)
        obs[f"rgb_{side}"] = r["rgb"]
        obs[f"instance_{side}"] = r["instance_id"]
        np.savez_compressed(
            eval_dir / f"truth_{side}.npz",
            instance_id=r["instance_id"], range_m=r["range_m"], xyz_h=r["xyz_h"],
        )
        Image.fromarray(_linear_to_u8(r["rgb"])).save(out / f"{side}.png")
        mask_hashes[side] = hashlib.sha256(r["instance_id"].tobytes()).hexdigest()
        truth_summary[side] = {
            "near_pixels": int((r["instance_id"] == NEAR_ID).sum()),
            "far_pixels": int((r["instance_id"] == FAR_ID).sum()),
            "range_median_near": float(np.median(r["range_m"][r["instance_id"] == NEAR_ID])),
            "range_median_far": float(np.median(r["range_m"][r["instance_id"] == FAR_ID])),
            "range_p05_far": float(np.percentile(r["range_m"][r["instance_id"] == FAR_ID], 5)),
            "range_p95_far": float(np.percentile(r["range_m"][r["instance_id"] == FAR_ID], 95)),
        }

    if set(obs) != {"rgb_L", "rgb_R", "instance_L", "instance_R"}:
        raise RuntimeError("observation contract changed")
    np.savez_compressed(out / "observation.npz", **obs)
    json_write(out / "calibration.json", cal)
    acq = {
        "schema": SCHEMA,
        "source": SOURCE,
        "profile": PROFILE,
        "gaze_yaw_pitch_deg": [YAW_DEG, PITCH_DEG],
        "vergence_m": VERGENCE_M,
        "ipd_m": IPD_M,
        "near_depth_m": NEAR_DEPTH_M,
        "far_base_depth_m": FAR_BASE_DEPTH_M,
        "texture_seed": int(texture_seed),
        "slant_level": slant_level,
        "far_plane_slope_k": slope_k,
        "texture_level": texture_level,
        "near_texture_gain": 1.0,
        "far_texture_gain": far_gain,
        "near_instance_id": NEAR_ID,
        "far_instance_id": FAR_ID,
        "near_rectangle": {
            "center_angle_x_deg": NEAR_CENTER_ANGLE_X_DEG,
            "width_deg": NEAR_WIDTH_DEG,
            "height_deg": NEAR_HEIGHT_DEG,
        },
        "tangent_frame_mode": "baseline_projected",
        "sensor_contract": "analytic local padded perspective pair using native FSG camera geometry",
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
    json_write(out / "acquisition.json", acq)
    json_write(out / "run.json", {
        "schema": "FSG-BLEND-BRIDGE5-run-v1",
        "complete": True,
        "case": "controlled_texture_slant_factorial",
        "source": SOURCE,
        "profile": PROFILE,
        "slant_level": slant_level,
        "texture_level": texture_level,
        "texture_seed": int(texture_seed),
    })
    return acq


def generate_factorial(root: Path) -> dict[str, Any]:
    root = root.resolve()
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"factorial root must be new or empty: {root}")
    root.mkdir(parents=True, exist_ok=True)
    conditions: list[dict[str, Any]] = []
    for seed in TEXTURE_SEEDS:
        for slant in SLANT_LEVELS:
            for texture in TEXTURE_LEVELS:
                conditions.append(generate_condition(root, slant, texture, seed))
    for side in ("L", "R"):
        hashes = {c["instance_mask_sha256"][side] for c in conditions}
        if len(hashes) != 1:
            raise RuntimeError(f"near silhouette changed across factorial for eye {side}")
    manifest = {
        "schema": "FSG-BLEND-BRIDGE5-factorial-manifest-v1",
        "scientific_question": "are far-surface slant and/or foreground/background texture asymmetry sufficient to trigger detached epipolar foreground-disparity capture?",
        "design": "2x2 factorial x 3 predeclared texture seeds",
        "factors": {
            "far_geometry": SLANT_LEVELS,
            "far_texture_gain": TEXTURE_LEVELS,
        },
        "texture_seeds": list(TEXTURE_SEEDS),
        "condition_count": len(conditions),
        "fixed": {
            "profile": PROFILE,
            "yaw_deg": YAW_DEG,
            "pitch_deg": PITCH_DEG,
            "vergence_m": VERGENCE_M,
            "ipd_m": IPD_M,
            "near_depth_m": NEAR_DEPTH_M,
            "far_base_depth_m": FAR_BASE_DEPTH_M,
            "near_rectangle_center_angle_x_deg": NEAR_CENTER_ANGLE_X_DEG,
            "near_rectangle_width_deg": NEAR_WIDTH_DEG,
            "near_rectangle_height_deg": NEAR_HEIGHT_DEG,
            "near_texture_gain": 1.0,
            "tangent_frame": "baseline_projected",
            "matcher": "tools/fsg_stereo.py unchanged",
            "capture_alpha_threshold": 0.5,
        },
        "prospective_rationale": {
            "far_base_depth": "2.40 m gives ~11.4 px gap in Bridge-4, bracketing Classroom ~12.2 px",
            "slanted_k": "1.8 chosen from camera geometry to yield ~0.047 px/px true-disparity slope, matching sealed Classroom ~0.0478 px/px",
            "near2x_texture": "far contrast gain 0.44 with near frozen at 1.0 targets the sealed Classroom near/far local-texture ratio ~2:1",
        },
        "mask_sha256": {side: conditions[0]["instance_mask_sha256"][side] for side in ("L", "R")},
        "truth_used_only_for_evaluation": True,
        "stereo_run_during_generation": False,
    }
    json_write(root / "bridge5_manifest.json", manifest)
    print(f"[fsg-bridge5-factorial] COMPLETE conditions={len(conditions)} cells=4 seeds={len(TEXTURE_SEEDS)}")
    return manifest


def self_test() -> None:
    cal = make_calibration(
        PROFILE, YAW_DEG, PITCH_DEG,
        vergence_distance=VERGENCE_M, ipd=IPD_M,
        tangent_frame="baseline_projected",
    )
    eye = cal["eyes"][0]
    flat = render_eye(cal, eye, 17, 0.0, 1.0)
    slant = render_eye(cal, eye, 17, 1.8, 1.0)
    weak = render_eye(cal, eye, 17, 0.0, TEXTURE_LEVELS["near2x"])
    assert np.array_equal(flat["instance_id"], slant["instance_id"])
    assert np.array_equal(flat["instance_id"], weak["instance_id"])
    far = flat["instance_id"] == FAR_ID
    assert float(np.ptp(flat["range_m"][far])) > 0.0  # ray range varies even for a plane
    # Slant must change far-surface range substantially from top to bottom.
    h = slant["range_m"].shape[0]
    assert abs(float(np.nanmedian(slant["range_m"][h//4])) - float(np.nanmedian(slant["range_m"][3*h//4]))) > 0.4
    # Contrast manipulation changes far RGB but leaves near RGB exactly fixed.
    near = flat["instance_id"] == NEAR_ID
    assert np.array_equal(flat["rgb"][near], weak["rgb"][near])
    assert float(np.std(weak["rgb"][far])) < float(np.std(flat["rgb"][far]))
    assert set(np.unique(flat["instance_id"])) == {NEAR_ID, FAR_ID}
    print("[fsg-bridge5-factorial] self-test PASS")


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
    generate_factorial(args.root)


if __name__ == "__main__":
    main()
