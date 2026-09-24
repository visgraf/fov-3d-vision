"""Create the Classroom-Oracle-2 demonstration package.

The demo is observational only.  It consumes completed run artifacts after the
control loop and never feeds information back into fixation selection.

Outputs under RUN/demo/ include:
  Demo.md
  overview.png
  panoramas/{rgb_observed,depth_reference,instance_reference,coverage_comparison}.png
  pointclouds/scene_final.ply and one PLY per object
  frames/frame_XXXX.png
  classroom-oracle-2-demo.mp4 when OpenCV has an MP4 writer
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import classroom_oracle2_public as public
import classroom_oracle2_eval as evaluation

WIDE = public.WIDE_DOMAIN
OLD = public.ORIGINAL_DOMAIN


def _json(path: Path) -> Any:
    return json.loads(path.read_text())


def _load_map(path: Path) -> np.ndarray:
    if not path.exists():
        return np.empty((0, 3), np.float32)
    with np.load(path, allow_pickle=False) as z:
        x = np.asarray(z["xyz_h"], np.float32)
    return x.reshape(-1, 3)[np.isfinite(x.reshape(-1, 3)).all(axis=1)]


def _load_truth(path: Path):
    with np.load(path, allow_pickle=False) as z:
        return (
            np.asarray(z["instance_id"], np.int32),
            np.asarray(z["xyz_h"], np.float32),
            np.asarray(z["yaw_pitch_deg"], np.float32),
        )


def _iid_color(iid: int) -> tuple[int, int, int]:
    h = np.uint8((int(iid) * 47) % 180)
    hsv = np.array([[[h, 210, 235]]], np.uint8)
    bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0, 0]
    return int(bgr[0]), int(bgr[1]), int(bgr[2])


def _put(img, text: str, xy=(12, 28), scale=0.65, thickness=1) -> None:
    cv2.putText(img, text, xy, cv2.FONT_HERSHEY_SIMPLEX, scale, (255, 255, 255), thickness, cv2.LINE_AA)


def _panel(title: str, body: np.ndarray, size=(640, 360)) -> np.ndarray:
    w, h = size
    canvas = np.zeros((h, w, 3), np.uint8)
    body = np.asarray(body, np.uint8)
    max_h = h - 42
    if body.size:
        s = min(w / max(1, body.shape[1]), max_h / max(1, body.shape[0]))
        nw = max(1, int(round(body.shape[1] * s)))
        nh = max(1, int(round(body.shape[0] * s)))
        r = cv2.resize(body, (nw, nh), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_NEAREST)
        x0 = (w - nw) // 2
        y0 = 38 + (max_h - nh) // 2
        canvas[y0:y0 + nh, x0:x0 + nw] = r
    _put(canvas, title, (12, 26), 0.65, 1)
    return canvas


def _grid_shape(bounds: dict[str, float], step: float) -> tuple[int, int]:
    w = int(round((bounds["yaw_max_deg"] - bounds["yaw_min_deg"]) / step)) + 1
    h = int(round((bounds["pitch_max_deg"] - bounds["pitch_min_deg"]) / step)) + 1
    return h, w


def _angle_pixels(angles: np.ndarray, bounds: dict[str, float], step: float):
    a = np.asarray(angles, float)
    x = np.rint((a[:, 0] - bounds["yaw_min_deg"]) / step).astype(np.int64)
    y = np.rint((bounds["pitch_max_deg"] - a[:, 1]) / step).astype(np.int64)
    h, w = _grid_shape(bounds, step)
    ok = (x >= 0) & (x < w) & (y >= 0) & (y < h)
    return y, x, ok


def _draw_domain_rect(img: np.ndarray, inner: dict[str, float], outer: dict[str, float], step: float) -> None:
    a = np.array([
        [inner["yaw_min_deg"], inner["pitch_max_deg"]],
        [inner["yaw_max_deg"], inner["pitch_min_deg"]],
    ], float)
    y, x, ok = _angle_pixels(a, outer, step)
    if bool(np.all(ok)):
        cv2.rectangle(img, (int(x[0]), int(y[0])), (int(x[1]), int(y[1])), (255, 255, 255), 1, cv2.LINE_AA)


def _instance_panorama(ids: np.ndarray, angles: np.ndarray, target_ids: set[int], step=0.25) -> np.ndarray:
    h, w = _grid_shape(WIDE, step)
    img = np.zeros((h, w, 3), np.uint8)
    y, x, ok = _angle_pixels(angles, WIDE, step)
    for iid in np.unique(ids[ok]):
        if int(iid) <= 0:
            continue
        m = ok & (ids == iid)
        color = _iid_color(int(iid)) if int(iid) in target_ids else (55, 55, 55)
        img[y[m], x[m]] = color
    _draw_domain_rect(img, OLD, WIDE, step)
    return img


def _depth_panorama(xyz: np.ndarray, angles: np.ndarray, step=0.25) -> np.ndarray:
    h, w = _grid_shape(WIDE, step)
    depth = np.full((h, w), np.nan, np.float32)
    r = np.linalg.norm(np.asarray(xyz, np.float32), axis=1)
    y, x, ok = _angle_pixels(angles, WIDE, step)
    depth[y[ok], x[ok]] = r[ok]
    finite = np.isfinite(depth)
    out = np.zeros((h, w, 3), np.uint8)
    if finite.any():
        lo, hi = np.percentile(depth[finite], [2, 98])
        norm = np.zeros_like(depth, np.uint8)
        if hi > lo:
            norm[finite] = np.clip((depth[finite] - lo) * 255.0 / (hi - lo), 0, 255).astype(np.uint8)
        out = cv2.applyColorMap(norm, cv2.COLORMAP_TURBO)
        out[~finite] = 0
    _draw_domain_rect(out, OLD, WIDE, step)
    return out


def _coverage_comparison(baseline: Path, run: Path, ids: np.ndarray, xyz: np.ndarray, angles: np.ndarray, target_ids: list[int], step=0.25) -> np.ndarray:
    h, w = _grid_shape(OLD, step)
    img = np.zeros((h, w, 3), np.uint8)
    radius = float(public.FUSION["association_radius_m"])
    for iid in target_ids:
        m = ids == iid
        ref = xyz[m]
        ang = angles[m]
        bmap = _load_map(baseline / "objects" / f"instance_{iid:04d}" / "final_map.npz")
        omap = _load_map(run / "objects" / f"instance_{iid:04d}" / "final_map.npz")
        b = evaluation.covered(ref, bmap, radius)
        o = evaluation.covered(ref, omap, radius)
        y, x, ok = _angle_pixels(ang, OLD, step)
        state = np.zeros(len(ref), np.uint8)
        state[b & o] = 1       # stable covered
        state[~b & o] = 2      # recovered
        state[~b & ~o] = 3     # still missed
        state[b & ~o] = 4      # regression
        colors = {
            1: (145, 145, 145),
            2: (60, 220, 60),
            3: (40, 40, 230),
            4: (220, 60, 220),
        }
        for s, c in colors.items():
            q = ok & (state == s)
            img[y[q], x[q]] = c
    return img


def _read_bgr(path: Path) -> np.ndarray:
    x = cv2.imread(str(path), cv2.IMREAD_COLOR)
    return np.zeros((64, 64, 3), np.uint8) if x is None else x


def _observed_rgb_panorama(run: Path, manifest: dict, step=0.10) -> tuple[np.ndarray, int]:
    try:
        import classroom_oracle1_epistemic as epi
    except Exception:
        h, w = _grid_shape(WIDE, step)
        return np.zeros((h, w, 3), np.uint8), 0

    h, w = _grid_shape(WIDE, step)
    sums = np.zeros((h, w, 3), np.float64)
    counts = np.zeros((h, w), np.int32)
    used = 0
    for obj in manifest.get("objects", []):
        iid = int(obj["instance_id"])
        odir = run / "objects" / f"instance_{iid:04d}"
        for row in obj.get("trajectory", []):
            k = int(row["step"])
            cpath = odir / "acquisitions" / f"fix_{k:02d}" / "calibration.json"
            ipath = odir / "benchmark" / f"fix_{k:02d}_L.png"
            if not cpath.exists() or not ipath.exists():
                continue
            cal = _json(cpath)
            bgr = _read_bgr(ipath)
            try:
                d = epi._rectified_core_directions_h(cal, "L")
            except Exception:
                continue
            if d.shape[:2] != bgr.shape[:2]:
                continue
            flat = d.reshape(-1, 3)
            yaw = np.degrees(np.arctan2(flat[:, 0], -flat[:, 2]))
            pitch = np.degrees(np.arctan2(flat[:, 1], np.hypot(flat[:, 0], flat[:, 2])))
            ang = np.c_[yaw, pitch]
            yy, xx, ok = _angle_pixels(ang, WIDE, step)
            pix = bgr.reshape(-1, 3).astype(np.float64)
            yy = yy[ok]; xx = xx[ok]; pix = pix[ok]
            np.add.at(sums, (yy, xx, slice(None)), pix)
            np.add.at(counts, (yy, xx), 1)
            used += 1
    out = np.zeros((h, w, 3), np.uint8)
    m = counts > 0
    out[m] = np.clip(sums[m] / counts[m, None], 0, 255).astype(np.uint8)
    _draw_domain_rect(out, OLD, WIDE, step)
    return out, used


def _write_ply(path: Path, xyz: np.ndarray, labels: np.ndarray | None = None) -> None:
    p = np.asarray(xyz, np.float32).reshape(-1, 3)
    if labels is None:
        labels = np.zeros(len(p), np.int32)
    labels = np.asarray(labels, np.int32).reshape(-1)
    if len(labels) != len(p):
        raise ValueError("PLY label count mismatch")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        header = (
            "ply\nformat binary_little_endian 1.0\n"
            f"element vertex {len(p)}\n"
            "property float x\nproperty float y\nproperty float z\n"
            "property uchar red\nproperty uchar green\nproperty uchar blue\n"
            "end_header\n"
        )
        f.write(header.encode("ascii"))
        rec = np.empty(len(p), dtype=[("x", "<f4"), ("y", "<f4"), ("z", "<f4"), ("r", "u1"), ("g", "u1"), ("b", "u1")])
        rec["x"], rec["y"], rec["z"] = p[:, 0], p[:, 1], p[:, 2]
        for iid in np.unique(labels):
            b, g, r = _iid_color(int(iid))
            m = labels == iid
            rec["r"][m], rec["g"][m], rec["b"][m] = r, g, b
        rec.tofile(f)


def _project_cloud(xyz: np.ndarray, labels: np.ndarray, bounds: tuple[np.ndarray, np.ndarray], size=(640, 310), max_points=120000) -> np.ndarray:
    w, h = size
    img = np.zeros((h, w, 3), np.uint8)
    p = np.asarray(xyz, np.float32).reshape(-1, 3)
    lab = np.asarray(labels, np.int32).reshape(-1)
    if len(p) == 0:
        return img
    if len(p) > max_points:
        idx = np.linspace(0, len(p) - 1, max_points).astype(np.int64)
        p, lab = p[idx], lab[idx]
    # Fixed oblique projection in head coordinates, stable over all frames.
    u = 0.82 * p[:, 0] - 0.58 * p[:, 2]
    v = -p[:, 1] + 0.16 * p[:, 0] + 0.18 * p[:, 2]
    lo, hi = bounds
    uu = (u - lo[0]) / max(float(hi[0] - lo[0]), 1e-6)
    vv = (v - lo[1]) / max(float(hi[1] - lo[1]), 1e-6)
    x = np.clip(np.rint(uu * (w - 1)), 0, w - 1).astype(np.int32)
    y = np.clip(np.rint(vv * (h - 1)), 0, h - 1).astype(np.int32)
    for iid in np.unique(lab):
        m = lab == iid
        img[y[m], x[m]] = _iid_color(int(iid))
    return img


def _projection_bounds(final_xyz: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if not len(final_xyz):
        return np.array([-1.0, -1.0]), np.array([1.0, 1.0])
    p = np.asarray(final_xyz, np.float32)
    u = 0.82 * p[:, 0] - 0.58 * p[:, 2]
    v = -p[:, 1] + 0.16 * p[:, 0] + 0.18 * p[:, 2]
    a = np.c_[u, v]
    lo = np.percentile(a, 0.5, axis=0)
    hi = np.percentile(a, 99.5, axis=0)
    pad = np.maximum((hi - lo) * 0.05, 1e-3)
    return lo - pad, hi + pad


def _cyclopean_panel(iid: int, truth_ids: np.ndarray, truth_xyz: np.ndarray, truth_angles: np.ndarray,
                     current_map: np.ndarray, visited: list[list[float]], current_gaze: list[float], step=0.25) -> np.ndarray:
    m = truth_ids == iid
    ref = truth_xyz[m]
    ang = truth_angles[m]
    cov = evaluation.covered(ref, current_map, float(public.FUSION["association_radius_m"]))
    h, w = _grid_shape(WIDE, step)
    img = np.zeros((h, w, 3), np.uint8)
    y, x, ok = _angle_pixels(ang, WIDE, step)
    q = ok & cov
    img[y[q], x[q]] = (70, 210, 70)
    q = ok & ~cov
    img[y[q], x[q]] = (50, 50, 220)
    _draw_domain_rect(img, OLD, WIDE, step)
    if visited:
        va = np.asarray(visited, float)
        yy, xx, vok = _angle_pixels(va, WIDE, step)
        pts = np.c_[xx[vok], yy[vok]].astype(np.int32)
        if len(pts) >= 2:
            cv2.polylines(img, [pts], False, (255, 180, 0), 1, cv2.LINE_AA)
        for px, py in pts:
            cv2.circle(img, (int(px), int(py)), 2, (255, 180, 0), -1)
    ga = np.asarray([current_gaze], float)
    gy, gx, gok = _angle_pixels(ga, WIDE, step)
    if bool(gok[0]):
        cv2.drawMarker(img, (int(gx[0]), int(gy[0])), (255, 255, 255), cv2.MARKER_CROSS, 9, 1)
    return img


def _reference_panel(base_img: np.ndarray, iid: int, ids: np.ndarray, angles: np.ndarray, gaze: list[float], step=0.25) -> np.ndarray:
    img = base_img.copy()
    m = ids == iid
    y, x, ok = _angle_pixels(angles[m], WIDE, step)
    img[y[ok], x[ok]] = (0, 255, 255)
    gy, gx, gok = _angle_pixels(np.asarray([gaze], float), WIDE, step)
    if bool(gok[0]):
        cv2.drawMarker(img, (int(gx[0]), int(gy[0])), (255, 255, 255), cv2.MARKER_CROSS, 11, 1)
    return img


def _stereo_panel(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    h = max(left.shape[0], right.shape[0])
    if left.shape[0] != h:
        left = cv2.resize(left, (left.shape[1], h))
    if right.shape[0] != h:
        right = cv2.resize(right, (right.shape[1], h))
    gap = np.zeros((h, 8, 3), np.uint8)
    body = np.hstack([left, gap, right])
    _put(body, "L", (6, 22), 0.6, 1)
    _put(body, "R", (left.shape[1] + 14, 22), 0.6, 1)
    return body


def _compose_four(p1, p2, p3, p4, footer: str) -> np.ndarray:
    a = np.hstack([p1, p2])
    b = np.hstack([p3, p4])
    frame = np.vstack([a, b])
    bar = np.zeros((34, frame.shape[1], 3), np.uint8)
    _put(bar, footer, (10, 23), 0.55, 1)
    return np.vstack([frame, bar])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True, type=Path)
    ap.add_argument("--baseline-run", type=Path, default=Path(public.BASELINE_RUN_DEFAULT))
    ap.add_argument("--fps", type=float, default=4.0)
    ap.add_argument("--reference-rgb", type=Path, default=None, help="optional external Blender RGB panorama for panel 1")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    run = args.run.resolve()
    baseline = args.baseline_run.resolve()
    manifest = _json(run / "manifest.json")
    evaluation_doc = _json(run / "evaluation.json")
    if not manifest.get("control_complete") or manifest.get("smoke"):
        raise RuntimeError("demo requires a completed full Oracle-2 run")

    demo = run / "demo"
    if demo.exists() and any(demo.iterdir()) and not args.overwrite:
        raise FileExistsError(f"demo exists; pass --overwrite to regenerate: {demo}")
    demo.mkdir(parents=True, exist_ok=True)
    frames_dir = demo / "frames"; frames_dir.mkdir(exist_ok=True)
    pano_dir = demo / "panoramas"; pano_dir.mkdir(exist_ok=True)
    pc_dir = demo / "pointclouds"; pc_dir.mkdir(exist_ok=True)

    wide_ids, wide_xyz, wide_angles = _load_truth(run / "bootstrap" / "evaluation_only" / "reachable_samples.npz")
    old_ids, old_xyz, old_angles = _load_truth(run / "bootstrap" / "evaluation_only" / "original_domain_reachable_samples.npz")
    target_ids = [int(o["instance_id"]) for o in manifest["objects"]]
    target_set = set(target_ids)

    instance_ref = _instance_panorama(wide_ids, wide_angles, target_set)
    depth_ref = _depth_panorama(wide_xyz, wide_angles)
    compare = _coverage_comparison(baseline, run, old_ids, old_xyz, old_angles, target_ids)
    rgb_observed, rgb_looks = _observed_rgb_panorama(run, manifest)
    cv2.imwrite(str(pano_dir / "instance_reference.png"), instance_ref)
    cv2.imwrite(str(pano_dir / "depth_reference.png"), depth_ref)
    cv2.imwrite(str(pano_dir / "coverage_comparison.png"), compare)
    cv2.imwrite(str(pano_dir / "rgb_observed.png"), rgb_observed)

    final_points = []
    final_labels = []
    object_final: dict[int, np.ndarray] = {}
    for obj in manifest["objects"]:
        iid = int(obj["instance_id"])
        pts = _load_map(run / "objects" / f"instance_{iid:04d}" / "final_map.npz")
        object_final[iid] = pts
        _write_ply(pc_dir / f"instance_{iid:04d}.ply", pts, np.full(len(pts), iid, np.int32))
        if len(pts):
            final_points.append(pts)
            final_labels.append(np.full(len(pts), iid, np.int32))
    scene_xyz = np.concatenate(final_points) if final_points else np.empty((0, 3), np.float32)
    scene_lab = np.concatenate(final_labels) if final_labels else np.empty(0, np.int32)
    _write_ply(pc_dir / "scene_final.ply", scene_xyz, scene_lab)
    proj_bounds = _projection_bounds(scene_xyz)
    final_scene = _project_cloud(scene_xyz, scene_lab, proj_bounds, (640, 360))
    cv2.imwrite(str(demo / "final_scene.png"), final_scene)

    optional_ref = None
    if args.reference_rgb is not None and args.reference_rgb.exists():
        optional_ref = _read_bgr(args.reference_rgb.resolve())

    completed_xyz = []
    completed_lab = []
    frame_index = 0
    first_frame = None
    last_frame = None
    video_path = demo / "classroom-oracle-2-demo.mp4"
    writer = None
    video_ok = False

    for obj in manifest["objects"]:
        iid = int(obj["instance_id"])
        odir = run / "objects" / f"instance_{iid:04d}"
        visited: list[list[float]] = []
        for row in obj.get("trajectory", []):
            k = int(row["step"])
            gaze = list(map(float, row["gaze_deg"]))
            visited.append(gaze)
            left = _read_bgr(odir / "benchmark" / f"fix_{k:02d}_L.png")
            right = _read_bgr(odir / "benchmark" / f"fix_{k:02d}_R.png")
            current = _load_map(odir / "maps" / f"fix_{k:02d}.npz")

            ref_body = optional_ref if optional_ref is not None else _reference_panel(instance_ref, iid, wide_ids, wide_angles, gaze)
            stereo = _stereo_panel(left, right)
            cyclo = _cyclopean_panel(iid, wide_ids, wide_xyz, wide_angles, current, visited, gaze)

            pts_parts = list(completed_xyz)
            lab_parts = list(completed_lab)
            if len(current):
                pts_parts.append(current)
                lab_parts.append(np.full(len(current), iid, np.int32))
            sx = np.concatenate(pts_parts) if pts_parts else np.empty((0, 3), np.float32)
            sl = np.concatenate(lab_parts) if lab_parts else np.empty(0, np.int32)
            recon = _project_cloud(sx, sl, proj_bounds, (640, 310))

            p1 = _panel("1  Blender reference / target + gaze", ref_body)
            p2 = _panel("2  Current binocular tangent observation", stereo)
            p3 = _panel("3  Cyclopean state: covered green, unseen red", cyclo)
            p4 = _panel("4  Accumulating 3-D reconstruction", recon)
            footer = (
                f"object {iid} {obj.get('object_name','')} | look {k} | {row.get('action_source')} | "
                f"gaze ({gaze[0]:.2f},{gaze[1]:.2f}) | surfels {int(row.get('map_size_after',0))}"
            )
            frame = _compose_four(p1, p2, p3, p4, footer)
            fpath = frames_dir / f"frame_{frame_index:04d}.png"
            cv2.imwrite(str(fpath), frame)
            if first_frame is None:
                first_frame = frame.copy()
            last_frame = frame.copy()
            if writer is None:
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(str(video_path), fourcc, float(args.fps), (frame.shape[1], frame.shape[0]))
                video_ok = bool(writer.isOpened())
            if video_ok:
                writer.write(frame)
            frame_index += 1

        pts = object_final[iid]
        if len(pts):
            completed_xyz.append(pts)
            completed_lab.append(np.full(len(pts), iid, np.int32))

    if writer is not None:
        writer.release()
    if not video_ok and video_path.exists():
        video_path.unlink()

    if last_frame is not None:
        cv2.imwrite(str(demo / "last_frame.png"), last_frame)

    overview = np.vstack([
        np.hstack([_panel("Observed RGB panorama", rgb_observed), _panel("Blender depth reference", depth_ref)]),
        np.hstack([_panel("Blender instance reference", instance_ref), _panel("Oracle-1 vs Oracle-2 old-domain coverage", compare)]),
    ])
    cv2.imwrite(str(demo / "overview.png"), overview)

    old_eval = evaluation_doc["original_domain"]
    wide_eval = evaluation_doc["wide_domain"]
    demo_md = f"""# Classroom-Oracle-2 demonstration\n\nThis is an observational demonstration of the completed boundary-ablation run.  It does not feed Blender truth or demo products back into the controller.\n\n## Scientific result shown\n\n- Oracle-1 original-domain coverage: {old_eval.get('baseline_coverage_fraction')}\n- Oracle-2 coverage on the exact same original-domain samples: {old_eval.get('oracle2_coverage_fraction')}\n- Fraction of Oracle-1 misses recovered: {old_eval.get('baseline_miss_recovery_fraction')}\n- Oracle-2 wide-domain coverage: {wide_eval.get('coverage_fraction')}\n- Oracle-2 fixations: {evaluation_doc.get('oracle2_total_fixations')}\n- Controller looks outside the old domain: {evaluation_doc.get('oracle2_looks_outside_original_domain')}\n\n## Narrative\n\nEach sequential frame tells the active-perception story:\n\n1. Blender-derived reference / selected target and current gaze.\n2. Current left + right tangent observation.\n3. Cyclopean angular state, with current object surface samples covered in green and still uncovered in red; the white rectangle marks the original +/-25,+/-20 domain inside the widened +/-35,+/-30 domain.\n4. Accumulating metric 3-D reconstruction.\n\nThe frame sequence therefore shows: fixation -> local binocular observation -> surface growth -> persistent scene memory -> next controller-selected fixation.\n\n## Files\n\n- `overview.png` - summary montage.\n- `panoramas/rgb_observed.png` - RGB panorama accumulated only from saved left-eye observations ({rgb_looks} usable looks).\n- `panoramas/depth_reference.png` - Blender dense first-hit depth reference over the widened domain.\n- `panoramas/instance_reference.png` - Blender dense instance reference; non-target newly visible instances are gray.\n- `panoramas/coverage_comparison.png` - on the original domain: gray=covered by both, green=Oracle-1 miss recovered by Oracle-2, red=still missed, magenta=baseline hit not covered by Oracle-2.\n- `pointclouds/instance_XXXX.ply` - final object point clouds.\n- `pointclouds/scene_final.ply` - combined final scene cloud.\n- `frames/frame_XXXX.png` - synchronized four-view sequence.\n- `classroom-oracle-2-demo.mp4` - synchronized video, if the local OpenCV build provides an MP4 writer.\n\nIf `--reference-rgb` was supplied, panel 1 uses that external Blender RGB panorama.  Otherwise it uses the Blender-derived dense instance reference; no photorealistic reference is fabricated.\n\n## Regenerate\n\n```bash\npython tools/classroom_oracle2_demo.py \\\n  --run {run} \\\n  --baseline-run {baseline} \\\n  --overwrite\n```\n"""
    (demo / "Demo.md").write_text(demo_md)
    summary = {
        "frames": frame_index,
        "video_written": bool(video_ok),
        "video": str(video_path) if video_ok else None,
        "rgb_looks_used": rgb_looks,
        "pointcloud_points": int(len(scene_xyz)),
        "demo_dir": str(demo),
    }
    (demo / "demo_manifest.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print("[classroom-oracle2-demo] COMPLETE", json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
