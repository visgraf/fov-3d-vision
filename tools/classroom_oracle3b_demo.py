"""Generate the post-hoc Classroom-Oracle-3b Gap Anatomy demonstration."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import classroom_oracle3b_public as public
import classroom_oracle3_public as o3public

W, H = 640, 390


def _json(p: Path):
    return json.loads(p.read_text())


def _load_npz(p: Path):
    with np.load(p, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def _decode(codes, names):
    return np.asarray([names[int(v)] for v in np.asarray(codes, int)], dtype=object)


def _norm_img(a: np.ndarray, invert: bool = False) -> np.ndarray:
    x = np.asarray(a, float)
    finite = np.isfinite(x)
    out = np.zeros(x.shape, np.uint8)
    if finite.any():
        lo, hi = float(np.nanmin(x[finite])), float(np.nanmax(x[finite]))
        if hi > lo:
            out[finite] = np.clip((x[finite] - lo) * 255.0 / (hi - lo), 0, 255).astype(np.uint8)
    if invert:
        out = 255 - out
    return out


def _base_canvas(title: str) -> np.ndarray:
    im = np.full((H, W, 3), 245, np.uint8)
    cv2.putText(im, title, (14, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.66, (20, 20, 20), 2, cv2.LINE_AA)
    return im


def _fit(mask: np.ndarray, out_shape=(320, 560)) -> np.ndarray:
    h, w = mask.shape[:2]
    oh, ow = out_shape
    s = min(ow / max(1, w), oh / max(1, h))
    nw, nh = max(1, int(round(w * s))), max(1, int(round(h * s)))
    r = cv2.resize(mask, (nw, nh), interpolation=cv2.INTER_NEAREST)
    canvas = np.zeros((oh, ow, 3), np.uint8) if r.ndim == 3 else np.zeros((oh, ow), np.uint8)
    y = (oh - nh) // 2; x = (ow - nw) // 2
    canvas[y:y+nh, x:x+nw] = r
    return canvas


def _panel_support(state, misses, select, title):
    support = np.asarray(state["support"], bool)
    shore = np.asarray(state["shoreline"], bool)
    img = np.full((*support.shape, 3), 255, np.uint8)
    img[support] = (170, 170, 170)
    img[shore] = (0, 165, 255)
    cy = np.asarray(misses["cell_y"], int)[select]; cx = np.asarray(misses["cell_x"], int)[select]
    good = (cy >= 0) & (cy < support.shape[0]) & (cx >= 0) & (cx < support.shape[1])
    img[cy[good], cx[good]] = (0, 0, 220)
    p = _base_canvas(title); p[55:375, 40:600] = _fit(img)
    return p


def _panel_ring(state, misses, select, title):
    support = np.asarray(state["support"], bool)
    ring = cv2.distanceTransform((~support).astype(np.uint8), cv2.DIST_C, 3)
    g = _norm_img(ring)
    heat = cv2.applyColorMap(g, cv2.COLORMAP_TURBO)
    heat[support] = (60, 60, 60)
    cy = np.asarray(misses["cell_y"], int)[select]; cx = np.asarray(misses["cell_x"], int)[select]
    good = (cy >= 0) & (cy < support.shape[0]) & (cx >= 0) & (cx < support.shape[1])
    heat[cy[good], cx[good]] = (255, 255, 255)
    p = _base_canvas(title); p[55:375, 40:600] = _fit(heat)
    return p


def _panel_components(state, misses, select, lattice, title):
    support = np.asarray(state["support"], bool)
    img = np.full((*support.shape, 3), 250, np.uint8)
    img[support] = (205, 205, 205)
    angles = np.asarray(misses["yaw_pitch_deg"], float)[select]
    if len(angles):
        step = float(lattice["step_deg"])
        ry = np.rint((angles[:, 1] - float(lattice["pitch0_deg"])) / step).astype(int)
        rx = np.rint((angles[:, 0] - float(lattice["yaw0_deg"])) / step).astype(int)
        y0, x0 = ry.min(), rx.min(); h, w = ry.max()-y0+1, rx.max()-x0+1
        m = np.zeros((h, w), np.uint8); m[ry-y0, rx-x0] = 1
        n, lab = cv2.connectedComponents(m, connectivity=8)
        # Deterministic palette generated from label arithmetic, avoiding external state.
        cy = np.asarray(misses["cell_y"], int)[select]; cx = np.asarray(misses["cell_x"], int)[select]
        lbl = lab[ry-y0, rx-x0]
        for yy, xx, ll in zip(cy, cx, lbl):
            if 0 <= yy < img.shape[0] and 0 <= xx < img.shape[1]:
                img[yy, xx] = ((37*int(ll))%220+20, (83*int(ll))%220+20, (149*int(ll))%220+20)
    p = _base_canvas(title); p[55:375, 40:600] = _fit(img)
    return p


def _panel_observation(state, misses, select, title):
    support = np.asarray(state["support"], bool)
    img = np.full((*support.shape, 3), 250, np.uint8)
    img[support] = (190, 190, 190)
    cy = np.asarray(misses["cell_y"], int)[select]; cx = np.asarray(misses["cell_x"], int)[select]
    for y, x in zip(cy, cx):
        if not (0 <= y < img.shape[0] and 0 <= x < img.shape[1]):
            continue
        if bool(state["target_no_depth"][y, x]): c = (0, 140, 255)
        elif bool(state["target_with_depth"][y, x]): c = (0, 180, 0)
        elif bool(state["mixed"][y, x]): c = (180, 0, 180)
        elif bool(state["nontarget_only"][y, x]): c = (255, 180, 0)
        elif bool(state["never"][y, x]): c = (0, 0, 220)
        else: c = (80, 80, 80)
        img[y, x] = c
    p = _base_canvas(title); p[55:375, 40:600] = _fit(img)
    return p


def _frame(iid, name, o3, anatomy, lattice):
    od = o3 / "objects" / f"instance_{iid:04d}"
    state = _load_npz(od / "controller_state.npz")
    misses = _load_npz(od / "truth_misses.npz")
    reasons = _decode(misses["first_reason_code"], tuple(o3public.CYCLOPEAN_FIRST_REJECTION_REASONS))
    subtypes = _decode(misses["subtype_code"], tuple(o3public.TRUTH_SUBTYPES))
    select = (reasons == public.TARGET_FIRST_REASON) & (subtypes == public.TARGET_SUBTYPE)
    panels = [
        _panel_support(state, misses, select, "1 support / shoreline / detached misses"),
        _panel_ring(state, misses, select, "2 support-expansion ring depth"),
        _panel_components(state, misses, select, lattice, "3 disconnected missed-surface components"),
        _panel_observation(state, misses, select, "4 saved observation state (post-hoc)"),
    ]
    top = np.hstack(panels[:2]); bot = np.hstack(panels[2:]); frame = np.vstack([top, bot])
    header = np.full((58, frame.shape[1], 3), 245, np.uint8)
    cv2.putText(header, f"Classroom-Oracle-3b Gap Anatomy | {iid} {name}", (18, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (20,20,20), 2, cv2.LINE_AA)
    q = anatomy["support_ring_depth_all_samples"]
    cv2.putText(header, f"gap samples={anatomy['complement_nonshoreline_samples']} components={anatomy['component_count']} ring depth min/med/max={q['min']}/{q['median']}/{q['max']}", (18, 49), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (50,50,50), 1, cv2.LINE_AA)
    return np.vstack([header, frame])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--audit", type=Path, default=Path(public.DEFAULT_OUT))
    ap.add_argument("--oracle3-audit", type=Path, default=Path(public.ORACLE3_AUDIT_DEFAULT))
    args = ap.parse_args()
    root = args.audit.resolve(); o3 = args.oracle3_audit.resolve()
    result = _json(root / "gap_anatomy.json"); manifest = _json(root / "manifest.json")
    demo = root / "demo"; frames = demo / "frames"; objects = demo / "objects"
    frames.mkdir(parents=True, exist_ok=True); objects.mkdir(parents=True, exist_ok=True)
    lattice = manifest["reference_lattice"]
    rows = {int(r["instance_id"]): r for r in result["objects"]}
    focus = [int(v) for v in result["focus_instance_ids"]]
    frame_paths=[]
    for k,iid in enumerate(focus):
        row=rows[iid]; im=_frame(iid, row.get("object_name") or "", o3, row, lattice)
        fp=frames/f"frame_{k:04d}.png"; cv2.imwrite(str(fp), im); frame_paths.append(fp)
        cv2.imwrite(str(objects/f"instance_{iid:04d}_gap_anatomy.png"), im)
    # Overview is a 2x3 contact sheet of the focus objects.
    thumbs=[]
    for p in frame_paths:
        im=cv2.imread(str(p)); thumbs.append(cv2.resize(im,(640,405),interpolation=cv2.INTER_AREA))
    overview=np.vstack([np.hstack(thumbs[:3]),np.hstack(thumbs[3:6])])
    cv2.imwrite(str(demo/"overview.png"), overview)
    video_written=False
    if frame_paths:
        first=cv2.imread(str(frame_paths[0])); h,w=first.shape[:2]
        fourcc=cv2.VideoWriter_fourcc(*"mp4v")
        vw=cv2.VideoWriter(str(demo/"classroom-oracle-3b-demo.mp4"),fourcc,1.0,(w,h))
        if vw.isOpened():
            for p in frame_paths:
                vw.write(cv2.imread(str(p)))
            vw.release(); video_written=(demo/"classroom-oracle-3b-demo.mp4").exists() and (demo/"classroom-oracle-3b-demo.mp4").stat().st_size>0
        else:
            vw.release()
    agg=result["aggregate"]
    lines=[
        "# Classroom-Oracle-3b Demo - Gap Anatomy","",
        "This is a post-hoc diagnostic visualization. No panel participated in gaze selection.","",
        "The four panels show: (1) final angular support, current one-ring shoreline and detached misses; "
        "(2) the number of 0.1-degree 8-connected support-expansion rings required to reach each location; "
        "(3) connected missed-surface components measured on the frozen reachable-sample angular lattice; "
        "and (4) the saved observation-history state on the detached miss cells.","",
        f"Aggregate detached complement-nonshoreline misses: {agg['complement_nonshoreline_samples']} of {agg['oracle3_missed_samples']} Oracle-3 misses.",
        f"Aggregate ring-depth summary: {agg['support_ring_depth_all_samples']}",
        f"Aggregate observation-state histogram: {agg['observation_state_histogram']}","",
        "The halo-reach curve in gap_anatomy.json is descriptive only. It asks how many successive support dilations would be required before each detached miss became adjacent to support; it does not modify the controller.","",
        f"MP4 written: {str(video_written).lower()}.",
    ]
    (demo/"Demo.md").write_text("\n".join(lines)+"\n")
    print("[classroom-oracle3b-demo] COMPLETE", json.dumps({"frames":len(frame_paths),"mp4":video_written,"demo":str(demo)},sort_keys=True))

if __name__ == "__main__":
    main()
