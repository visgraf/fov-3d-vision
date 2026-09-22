"""Evaluator-phase reference panorama for FullScene-REAL-1.

This module opens FULL evaluator truth: exact surface geometry, first-hit
instance identity and photometric-side texture. It is therefore a strictly
post-seal tool, run as a separate process only after observer_complete.json
exists, so that neither fullscene_real1_run.py nor fullscene_real1_repo_adapter.py
ever imports the evaluator-side scene specification.

It reproduces the established acquisition truth path rather than inventing one:
the same analytic mesh the acquisition renderer feeds to its oracle first-hit
masks (fsg_scene.triangulate_objects / ray_mesh), the same procedural textures
(reality1_scene.scene_texture) and the same tone curve used for observer RGB
previews. The only new thing is the viewing geometry: one equirectangular
sphere about the fixed head origin, in the same convention as
fullscene_real1_export.spherical_zbuffer.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np


def _equirect_directions(width: int, height: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Pixel-centre yaw/pitch and unit directions matching the observer panorama.

    spherical_zbuffer maps a sample to x = floor(((yaw+180) % 360)/360*W) and
    y = floor((90-pitch)/180*H), so the centre of pixel (y, x) is the inverse of
    that at the half-cell offset. Using the identical convention is what makes
    observer and reference panoramas comparable pixel for pixel.
    """
    xs = (np.arange(width, dtype=np.float64) + 0.5) / width * 360.0 - 180.0
    ys = 90.0 - (np.arange(height, dtype=np.float64) + 0.5) / height * 180.0
    yaw = np.broadcast_to(xs[None, :], (height, width))
    pitch = np.broadcast_to(ys[:, None], (height, width))
    y = np.radians(yaw)
    p = np.radians(pitch)
    cp = np.cos(p)
    dirs = np.stack((np.sin(y) * cp, np.sin(p), -np.cos(y) * cp), axis=-1)
    return yaw, pitch, dirs


def _sample_texture(tex: np.ndarray, uv: np.ndarray) -> np.ndarray:
    """Bilinear texture lookup, identical to fsg_scene.synthetic_rgb's sampler."""
    n = len(tex)
    x = np.clip(uv[:, 0] * n - 0.5, 0, n - 1 - 1e-6)
    y = np.clip(uv[:, 1] * n - 0.5, 0, n - 1 - 1e-6)
    x0 = np.floor(x).astype(int)
    y0 = np.floor(y).astype(int)
    ax = (x - x0)[:, None]
    ay = (y - y0)[:, None]
    return ((1 - ay) * ((1 - ax) * tex[y0, x0] + ax * tex[y0, x0 + 1])
            + ay * ((1 - ax) * tex[y0 + 1, x0] + ax * tex[y0 + 1, x0 + 1]))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--fixture", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--width", type=int, required=True)
    ap.add_argument("--height", type=int, required=True)
    ap.add_argument("--require-seal", type=Path, required=True,
                    help="observer_complete.json that must already exist")
    ap.add_argument("--chunk", type=int, default=65536)
    a = ap.parse_args()

    seal = a.require_seal.resolve()
    if not seal.is_file():
        raise RuntimeError("refusing to open evaluator truth before the observer seal exists")
    sealed = json.loads(seal.read_text())
    if sealed.get("observer_sealed") is not True or sealed.get("evaluator_truth_opened") is not False:
        raise RuntimeError("observer seal is not a sealed, truth-closed record")

    sys.path.insert(0, str((a.repo.resolve() / "tools")))
    from PIL import Image

    # Post-seal, deliberately quarantined truth imports.
    import reality1_public as reality_public  # type: ignore
    import reality1_scene as scene_spec  # type: ignore
    from fsg_scene import ray_mesh, triangulate_objects  # type: ignore
    from reality1_run import _tone_preview  # type: ignore

    fixture = str(a.fixture)
    if fixture != str(reality_public.FIXTURE):
        raise RuntimeError(f"reference fixture {fixture!r} is not the established fixture")

    objects = scene_spec.scene_objects(fixture)
    mesh = triangulate_objects(objects)
    scene_spec.validate_mesh(mesh)

    w, h = int(a.width), int(a.height)
    _yaw, _pitch, dirs = _equirect_directions(w, h)
    flat = dirs.reshape(-1, 3)
    origin = np.zeros(3)

    depth = np.full(w * h, np.nan, dtype=np.float32)
    inst = np.zeros(w * h, dtype=np.int32)
    lin = np.zeros((w * h, 3), dtype=np.float32)
    textures: dict[int, np.ndarray] = {}

    # Chunked so a 2048x1024 sphere against the analytic mesh stays in memory.
    for lo in range(0, len(flat), int(a.chunk)):
        hi = min(lo + int(a.chunk), len(flat))
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
            m = good & (ids == i)
            if int(i) not in textures:
                textures[int(i)] = np.asarray(scene_spec.scene_texture(fixture, int(i)), np.float32)
            uv = np.einsum("ni,nij->nj", np.asarray(hit["barycentric"])[m], mesh["triangle_uv"][tri[m]])
            lin[lo:hi][m] = _sample_texture(textures[int(i)], uv)

    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    np.save(out / "reference_depth.npy", depth.reshape(h, w))
    np.save(out / "reference_instance.npy", inst.reshape(h, w))
    Image.fromarray(_tone_preview(lin.reshape(h, w, 3))).save(out / "reference_rgb.png")

    ids_present = sorted(int(i) for i in np.unique(inst) if int(i) > 0)
    summary = {
        "schema": "FullSceneREAL1-reference-panorama-v1",
        "fixture": fixture,
        "fixture_truth_digest": str(scene_spec.truth_digest()),
        "observer_seal_consumed": str(seal),
        "width": w,
        "height": h,
        "hit_pixels": int(np.isfinite(depth).sum()),
        "total_pixels": int(w * h),
        "instance_ids_present": ids_present,
        "instance_pixel_counts": {str(i): int((inst == i).sum()) for i in ids_present},
        "depth_min_m": float(np.nanmin(depth)) if np.isfinite(depth).any() else None,
        "depth_max_m": float(np.nanmax(depth)) if np.isfinite(depth).any() else None,
        "reference_rgb": "reference_rgb.png",
        "reference_depth": "reference_depth.npy",
        "reference_instance": "reference_instance.npy",
    }
    (out / "reference_manifest.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print("[fullscene-real1-reference] " + json.dumps(
        {"fixture": fixture, "ids": ids_present, "hit_pixels": summary["hit_pixels"]}, sort_keys=True))


if __name__ == "__main__":
    main()
