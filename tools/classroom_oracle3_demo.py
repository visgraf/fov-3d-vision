"""Generate the post-hoc Classroom-Oracle-3 eligibility-audit demonstration.

The demo consumes saved Oracle-1 observations plus Oracle-3 audit outputs.  It
never participates in control.  For the six deterministic focus objects it
creates sequential fixation frames with four panels:

1. angular trajectory and reachable reference;
2. current saved left/right binocular tangent observation;
3. evolving Cyclopean support/shoreline/epistemic state;
4. final reachable-but-uncovered truth colored by the rule that rejected it.
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

import classroom_oracle3_public as public
import classroom_oracle1_epistemic as epistemic
import classroom_oracle1_matcher as oracle_matcher

PANEL_W = 640
PANEL_H = 390
FONT = cv2.FONT_HERSHEY_SIMPLEX


def _json(path: Path) -> Any:
    return json.loads(path.read_text())


def _load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def _make_evidence() -> epistemic.Evidence:
    b = public.ORIGINAL_DOMAIN
    g = public.CYCLOPEAN_GRID_DEG
    w = int(round((b["yaw_max_deg"] - b["yaw_min_deg"]) / g)) + 1
    h = int(round((b["pitch_max_deg"] - b["pitch_min_deg"]) / g)) + 1
    z = np.zeros((h, w), bool)
    return epistemic.Evidence(b["yaw_min_deg"], b["yaw_max_deg"], b["pitch_min_deg"], b["pitch_max_deg"], g,
                              z.copy(), z.copy(), z.copy(), z.copy())


def _load_map(path: Path) -> np.ndarray:
    with np.load(path, allow_pickle=False) as z:
        x = np.asarray(z["xyz_h"], np.float64)
    return x[np.isfinite(x).all(axis=1)]


def _fit(img: np.ndarray, w: int, h: int) -> np.ndarray:
    if img is None or img.size == 0:
        return np.zeros((h, w, 3), np.uint8)
    x = np.asarray(img)
    if x.ndim == 2:
        x = cv2.cvtColor(x.astype(np.uint8), cv2.COLOR_GRAY2BGR)
    ih, iw = x.shape[:2]
    s = min(w / max(1, iw), h / max(1, ih))
    nw, nh = max(1, int(round(iw * s))), max(1, int(round(ih * s)))
    r = cv2.resize(x, (nw, nh), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_NEAREST)
    canvas = np.zeros((h, w, 3), np.uint8)
    y0, x0 = (h - nh) // 2, (w - nw) // 2
    canvas[y0:y0 + nh, x0:x0 + nw] = r
    return canvas


def _title(panel: np.ndarray, text: str) -> np.ndarray:
    out = panel.copy()
    cv2.rectangle(out, (0, 0), (out.shape[1], 34), (20, 20, 20), -1)
    cv2.putText(out, text, (12, 24), FONT, 0.63, (240, 240, 240), 1, cv2.LINE_AA)
    return out


def _chart_to_panel(chart: np.ndarray) -> np.ndarray:
    return _fit(chart, PANEL_W, PANEL_H)


def _trajectory_panel(angles: np.ndarray, gazes: list[list[float]], upto: int, iid: int, name: str) -> np.ndarray:
    b = public.ORIGINAL_DOMAIN
    img = np.full((PANEL_H, PANEL_W, 3), 245, np.uint8)
    margin = 38
    def xy(yaw: float, pitch: float) -> tuple[int, int]:
        x = margin + int(round((yaw - b["yaw_min_deg"]) / (b["yaw_max_deg"] - b["yaw_min_deg"]) * (PANEL_W - 2 * margin)))
        y = PANEL_H - margin - int(round((pitch - b["pitch_min_deg"]) / (b["pitch_max_deg"] - b["pitch_min_deg"]) * (PANEL_H - 2 * margin)))
        return x, y
    if len(angles):
        step = max(1, len(angles) // 2500)
        for yaw, pitch in angles[::step]:
            x, y = xy(float(yaw), float(pitch))
            if 0 <= x < PANEL_W and 0 <= y < PANEL_H:
                img[y, x] = (205, 205, 205)
    pts = [xy(float(g[0]), float(g[1])) for g in gazes[:upto + 1]]
    for a, c in zip(pts[:-1], pts[1:]):
        cv2.line(img, a, c, (70, 70, 70), 2, cv2.LINE_AA)
    for j, p in enumerate(pts):
        cv2.circle(img, p, 6 if j == len(pts) - 1 else 4, (40, 40, 220) if j == len(pts) - 1 else (50, 120, 50), -1)
    cv2.rectangle(img, (margin, margin), (PANEL_W - margin, PANEL_H - margin), (80, 80, 80), 1)
    cv2.putText(img, f"id {iid} {name} | fixation {upto + 1}/{len(gazes)}", (12, PANEL_H - 12), FONT, 0.52, (30, 30, 30), 1, cv2.LINE_AA)
    return _title(img, "1  trajectory + reachable reference")


def _binocular_panel(left_path: Path, right_path: Path) -> np.ndarray:
    L = cv2.imread(str(left_path), cv2.IMREAD_COLOR)
    R = cv2.imread(str(right_path), cv2.IMREAD_COLOR)
    half = PANEL_W // 2
    canvas = np.zeros((PANEL_H, PANEL_W, 3), np.uint8)
    canvas[:, :half] = _fit(L, half, PANEL_H)
    canvas[:, half:] = _fit(R, PANEL_W - half, PANEL_H)
    cv2.line(canvas, (half, 0), (half, PANEL_H), (255, 255, 255), 2)
    cv2.putText(canvas, "L", (12, PANEL_H - 14), FONT, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(canvas, "R", (half + 12, PANEL_H - 14), FONT, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
    return _title(canvas, "2  current saved binocular observation")


def _state_panel(ev: epistemic.Evidence, map_xyz: np.ndarray, visited: list[tuple[float, float]]) -> np.ndarray:
    support, _, _ = epistemic._map_support(ev, map_xyz)
    complement = ~support
    exterior, _ = epistemic._exterior_and_distance(complement)
    shoreline = complement & cv2.dilate(support.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    never = ~ev.seen_any
    target_no_depth = ev.seen_target & ~ev.target_depth_valid
    eligible = shoreline & exterior & never
    for yaw, pitch in visited:
        yy, xx, ok = epistemic._cells(ev, np.asarray([yaw]), np.asarray([pitch]))
        if ok[0]:
            eligible[int(yy[0]), int(xx[0])] = False
    img = np.full((*support.shape, 3), 255, np.uint8)
    img[support] = (180, 180, 180)
    img[shoreline] = (70, 150, 230)
    img[shoreline & target_no_depth] = (0, 165, 255)
    img[shoreline & never] = (40, 40, 220)
    img[eligible] = (20, 180, 20)
    panel = _chart_to_panel(img)
    cv2.putText(panel, "gray support | orange shoreline | red never | green eligible", (10, PANEL_H - 12), FONT, 0.43, (230, 230, 230), 1, cv2.LINE_AA)
    return _title(panel, "3  evolving Cyclopean state")


def _rejection_panel(state_path: Path, misses_path: Path) -> np.ndarray:
    state = _load_npz(state_path)
    miss = _load_npz(misses_path)
    support = np.asarray(state["support"], bool)
    img = np.full((*support.shape, 3), 248, np.uint8)
    img[support] = (205, 205, 205)
    palette = {
        "NOT_SHORELINE": (80, 80, 220),
        "INTERNAL_COMPONENT": (180, 80, 180),
        "ALREADY_OBSERVED": (0, 150, 255),
        "PREVIOUSLY_FIXATED_CELL": (220, 120, 40),
        "ELIGIBLE_NEVER_OBSERVED_EXTERIOR": (40, 180, 40),
        "OUT_OF_CHART": (0, 0, 0),
    }
    y = np.asarray(miss["cell_y"], int)
    x = np.asarray(miss["cell_x"], int)
    ok = np.asarray(miss["cell_in_chart"], bool)
    codes = np.asarray(miss["first_reason_code"], int)
    for i in range(len(codes)):
        if not ok[i]:
            continue
        reason = public.CYCLOPEAN_FIRST_REJECTION_REASONS[int(codes[i])]
        img[int(y[i]), int(x[i])] = palette[reason]
    panel = _chart_to_panel(img)
    cv2.putText(panel, "red not-shoreline | purple internal | orange observed | green eligible", (10, PANEL_H - 12), FONT, 0.41, (20, 20, 20), 1, cv2.LINE_AA)
    return _title(panel, "4  final truth misses by first rejection rule")


def _compose(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray, p4: np.ndarray) -> np.ndarray:
    top = np.concatenate((p1, p2), axis=1)
    bot = np.concatenate((p3, p4), axis=1)
    return np.concatenate((top, bot), axis=0)


def _write_demo_md(path: Path, audit_root: Path, o1: Path, frames: int, video_ok: bool, focus: list[int]) -> None:
    text = f"""# Classroom-Oracle-3 demo\n\nThis is the post-hoc visual demonstration for the **Eligibility Audit**.  It does not run the controller and it does not expose Blender reference truth to control.\n\nThe deterministic focus objects are: `{focus}`.\n\nEach synchronized frame has four panels:\n\n1. **trajectory + reachable reference** -- saved Oracle-1 gaze sequence over the frozen reachable-sample domain;\n2. **current binocular observation** -- the saved left/right tangent images for that fixation;\n3. **evolving Cyclopean state** -- support and shoreline reconstructed only from observations available up to that fixation;\n4. **final rejection diagnosis** -- post-hoc reachable-but-uncovered truth, colored by the first Cyclopean eligibility rule that excludes its cell.\n\nThe fourth panel is deliberately post-hoc and diagnostic.  It never participated in gaze selection.\n\nArtifacts:\n\n- `overview.png` -- final diagnostic frame for each focus object;\n- `objects/instance_XXXX_final.png` -- one final frame per focus object;\n- `frames/frame_XXXX.png` -- all {frames} synchronized sequential-fixation frames;\n- `classroom-oracle-3-demo.mp4` -- {'written successfully' if video_ok else 'not available; PNG frames are authoritative'}.\n\nRegenerate from repository root with:\n\n```bash\npython tools/classroom_oracle3_demo.py \\\n  --audit {audit_root} \\\n  --oracle1-run {o1}\n```\n"""
    path.write_text(text)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--audit", type=Path, default=Path(public.DEFAULT_OUT))
    ap.add_argument("--oracle1-run", type=Path, default=Path(public.ORACLE1_RUN_DEFAULT))
    args = ap.parse_args()
    audit_root = args.audit.resolve()
    o1 = args.oracle1_run.resolve()
    audit = _json(audit_root / "audit.json")
    manifest = _json(o1 / "manifest.json")
    by_id = {int(o["instance_id"]): o for o in manifest["objects"]}
    focus = [int(x) for x in audit["focus_instance_ids"]]

    truth_path = o1 / "bootstrap" / "evaluation_only" / "reachable_samples.npz"
    with np.load(truth_path, allow_pickle=False) as z:
        truth_ids = np.asarray(z["instance_id"], np.int32)
        truth_angles = np.asarray(z["yaw_pitch_deg"], np.float64)

    demo = audit_root / "demo"
    frames_dir = demo / "frames"
    objects_dir = demo / "objects"
    frames_dir.mkdir(parents=True, exist_ok=True)
    objects_dir.mkdir(parents=True, exist_ok=True)

    frame_paths: list[Path] = []
    final_frames: list[np.ndarray] = []
    frame_id = 0
    for iid in focus:
        result = by_id[iid]
        name = str(result.get("object_name", ""))
        traj = list(result["trajectory"])
        gazes = [list(map(float, r["gaze_deg"])) for r in traj]
        ref_ang = truth_angles[truth_ids == iid]
        ev = _make_evidence()
        visited: list[tuple[float, float]] = []
        obj_root = o1 / "objects" / f"instance_{iid:04d}"
        state_path = audit_root / "objects" / f"instance_{iid:04d}" / "controller_state.npz"
        misses_path = audit_root / "objects" / f"instance_{iid:04d}" / "truth_misses.npz"
        for k, row in enumerate(traj):
            step = int(row["step"])
            gaze = tuple(map(float, row["gaze_deg"]))
            adir = obj_root / "acquisitions" / f"fix_{step:02d}"
            c = _json(adir / "calibration.json")
            obs = _load_npz(adir / "oracle_observation.npz")
            rec, _, st = oracle_matcher.compute(c, obs)
            epistemic.add_observation(ev, c, st["ids_left"], st["raw_support_L"], st["ids_right"], st["raw_support_R"], rec["valid"], iid)
            visited.append(gaze)
            map_path = obj_root / "maps" / f"fix_{step:02d}.npz"
            map_xyz = _load_map(map_path) if map_path.exists() else _load_map(obj_root / "final_map.npz")
            p1 = _trajectory_panel(ref_ang, gazes, k, iid, name)
            p2 = _binocular_panel(obj_root / "benchmark" / f"fix_{step:02d}_L.png", obj_root / "benchmark" / f"fix_{step:02d}_R.png")
            p3 = _state_panel(ev, map_xyz, visited)
            p4 = _rejection_panel(state_path, misses_path)
            frame = _compose(p1, p2, p3, p4)
            fp = frames_dir / f"frame_{frame_id:04d}.png"
            cv2.imwrite(str(fp), frame)
            frame_paths.append(fp)
            frame_id += 1
            if k == len(traj) - 1:
                outp = objects_dir / f"instance_{iid:04d}_final.png"
                cv2.imwrite(str(outp), frame)
                final_frames.append(frame)

    if not final_frames:
        raise RuntimeError("no demo frames generated")
    thumb_w, thumb_h = 640, 390
    thumbs = [_fit(x, thumb_w, thumb_h) for x in final_frames]
    while len(thumbs) < 6:
        thumbs.append(np.zeros((thumb_h, thumb_w, 3), np.uint8))
    overview = np.concatenate((np.concatenate(thumbs[:3], axis=1), np.concatenate(thumbs[3:6], axis=1)), axis=0)
    cv2.imwrite(str(demo / "overview.png"), overview)

    video_ok = False
    if frame_paths:
        first = cv2.imread(str(frame_paths[0]), cv2.IMREAD_COLOR)
        h, w = first.shape[:2]
        writer = cv2.VideoWriter(str(demo / "classroom-oracle-3-demo.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), 4.0, (w, h))
        if writer.isOpened():
            for fp in frame_paths:
                img = cv2.imread(str(fp), cv2.IMREAD_COLOR)
                writer.write(img)
            writer.release()
            video_ok = (demo / "classroom-oracle-3-demo.mp4").exists() and (demo / "classroom-oracle-3-demo.mp4").stat().st_size > 0
        else:
            writer.release()

    _write_demo_md(demo / "Demo.md", audit_root, o1, len(frame_paths), video_ok, focus)
    print("[classroom-oracle3-demo] COMPLETE", json.dumps({"frames": len(frame_paths), "focus": focus, "video": video_ok}, sort_keys=True))


if __name__ == "__main__":
    main()
