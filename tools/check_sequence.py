"""Check a fixation sequence against the scene's reference panorama. Host side (venv).

    .venv/bin/python tools/check_sequence.py previews/sequence/calib_room \
        --reference previews/reference_small/calib_room --noise-fix 0.0733 --noise-ref 0.0176

Checks, each of which can fail (exit 1), written to <sequence>/check.json:
  reader     samples.npz values and distances equal fix.exr's Combined and Depth at the stored
             raster indices (OpenEXR reader here vs exr_lite inside Blender): exact
  (a) warp   the stored EYE-frame directions (analytic warp composed with the gaze) land in
             the reference panorama within one reference pixel (p99.9) of where the Position
             pass says the ray went; samples that hit nothing are excluded
  (b) fovea  samples within --fovea-deg of the gaze agree with the reference looked up at
             their directions: median relative difference below the combined noise
             sqrt(noise_fix^2 + noise_ref^2) of a fixation sample and a reference pixel
  (c) control  (b) with the directions rotated --control-yaw degrees about the EYE's up axis
             must FAIL on every fixation; if the texture were featureless it could not
  (d) cap    footprints over a fixation's disc sum to 2*pi*(1 - cos e_max) to 1%

On (b)'s threshold: the fixation and the reference are independent renders, so their
relative noises add in quadrature. A2's table gives, per scene, the median-tile rel_rms at
the fixation spp and at the reference spp (small profile: 64 and 1024 spp). For Gaussian noise
the median |difference| is 0.674 of the RMS, so a passing median sits well below the bound;
what the bound does not include is sub-pixel misalignment between a fixation sample and the
reference pixel it is compared to, which adds at texture edges. That is why the statistic is
a median.
"""
from __future__ import annotations

import argparse
import json
import math
import os

import numpy as np
import OpenEXR


def read_exr(path: str) -> dict[str, np.ndarray]:
    chans: dict[str, np.ndarray] = {}
    with OpenEXR.File(path) as f:
        for part in f.parts:
            for name, ch in part.channels.items():
                chans[name] = np.asarray(ch.pixels)
    return chans


def find(chans, suffix):
    for k, v in chans.items():
        if k.endswith(suffix):
            return v
    raise KeyError(f"no channel ending in {suffix!r}; have {sorted(chans)}")


def eye_rotation(eye: dict) -> np.ndarray:
    """EYE local axes as world columns: x = right = forward x up, y = up, z = -forward."""
    fwd, up = np.array(eye["forward"], float), np.array(eye["up"], float)
    right = np.cross(fwd, up)
    return np.stack([right, up, -fwd], axis=1)


def to_equirect_px(d: np.ndarray, w: int, h: int) -> np.ndarray:
    """EYE-frame unit directions -> continuous pixel coordinates in the reference."""
    lon = np.arctan2(d[:, 0], -d[:, 2])
    lat = np.arcsin(np.clip(d[:, 1], -1.0, 1.0))
    return np.stack([(lon / (2 * np.pi) + 0.5) * w, (0.5 - lat / np.pi) * h], axis=1)


def rot_y(deg: float) -> np.ndarray:
    a = math.radians(deg)
    return np.array([[math.cos(a), 0.0, math.sin(a)], [0.0, 1.0, 0.0], [-math.sin(a), 0.0, math.cos(a)]])


def rel_diff_median(value: np.ndarray, d: np.ndarray, ref: np.ndarray) -> tuple[float, int]:
    h, w = ref.shape[:2]
    p = to_equirect_px(d, w, h)
    x = np.clip(np.floor(p[:, 0]).astype(int) % w, 0, w - 1)
    y = np.clip(np.floor(p[:, 1]).astype(int), 0, h - 1)
    r = ref[y, x, :3].mean(-1)
    v = value.mean(-1)
    rel = np.abs(v - r) / np.maximum(r, 1e-3)
    return float(np.median(rel)), int(len(rel))


def alignment_floor(d: np.ndarray, ref: np.ndarray) -> float:
    h, w = ref.shape[:2]
    p = to_equirect_px(d, w, h)
    x = np.floor(p[:, 0]).astype(int) % w; y = np.clip(np.floor(p[:, 1]).astype(int), 0, h - 1)
    xs = np.floor(p[:, 0] + 0.5).astype(int) % w; ys = np.clip(np.floor(p[:, 1] + 0.5).astype(int), 0, h - 1)
    r0, r1 = ref[y, x, :3].mean(-1), ref[ys, xs, :3].mean(-1)
    return float(np.median(np.abs(r0 - r1) / np.maximum(r0, 1e-3)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sequence")
    ap.add_argument("--reference", required=True, help="preview360 folder of the same scene and profile")
    ap.add_argument("--noise-fix", type=float, required=True, help="median-tile rel_rms at the fixation spp (A2 table)")
    ap.add_argument("--noise-ref", type=float, required=True, help="median-tile rel_rms at the reference spp (A2 table)")
    ap.add_argument("--fovea-deg", type=float, default=2.0)
    ap.add_argument("--control-yaw", type=float, default=90.0)
    ap.add_argument("--px-tol", type=float, default=1.0, help="reference pixels, on the p99.9")
    ap.add_argument("--cap-tol", type=float, default=0.01)
    args = ap.parse_args()

    seq = json.load(open(os.path.join(args.sequence, "sequence.json")))
    ref_meta = json.load(open(os.path.join(args.reference, "meta.json")))
    ref = find(read_exr(os.path.join(args.reference, "pano.exr")), "Combined")
    H, W = ref.shape[:2]
    R_eye = eye_rotation(ref_meta["eye"])
    eye_pos = np.array(ref_meta["eye"]["position_m"], float)
    threshold = math.sqrt(args.noise_fix ** 2 + args.noise_ref ** 2)
    emax = seq["warp"]["e_max_deg"]
    cap = 2 * math.pi * (1 - math.cos(math.radians(emax)))
    fails = []
    per = []

    for f in seq["fixations"]:
        fdir = os.path.join(args.sequence, f"f{f['id']:03d}")
        s = np.load(os.path.join(fdir, "samples.npz"))
        meta = json.load(open(os.path.join(fdir, "meta.json")))
        ch = read_exr(os.path.join(fdir, "fix.exr"))
        comb, z = find(ch, "Combined"), find(ch, "Depth.Z")
        pos = np.stack([find(ch, f"Position.{a}") for a in "XYZ"], -1)
        z = z[..., 0] if z.ndim == 3 else z
        ri = s["raster_index"]
        rows, cols = ri[:, 0], ri[:, 1]
        d = s["direction"].astype(np.float64)
        rec = {"id": f["id"], "name": f["name"], "samples": int(len(d))}

        # reader: the values in the record are the file's values
        rec["reader_max_abs_diff"] = float(max(np.abs(s["value"] - comb[rows, cols, :3]).max(),
                                               np.abs(s["distance"] - z[rows, cols]).max()))
        if rec["reader_max_abs_diff"] != 0.0:
            fails.append(f"f{f['id']:03d}: samples.npz differs from fix.exr by {rec['reader_max_abs_diff']:.3e}")
        if not np.allclose(s["origin"], eye_pos, atol=1e-5):
            fails.append(f"f{f['id']:03d}: origin {s['origin']} is not the eye position {eye_pos}")

        # (a) analytic direction vs Position pass, in reference pixels
        hit = s["distance"] < 1e9
        dw = pos[rows, cols] - eye_pos
        dp = (dw / np.maximum(np.linalg.norm(dw, axis=-1, keepdims=True), 1e-12)) @ R_eye   # world -> EYE
        pa, pb = to_equirect_px(d[hit], W, H), to_equirect_px(dp[hit], W, H)
        dx = np.abs(pa[:, 0] - pb[:, 0]); dx = np.minimum(dx, W - dx)
        dist = np.hypot(dx, pa[:, 1] - pb[:, 1])
        rec["warp_px_p999"] = float(np.percentile(dist, 99.9)); rec["warp_px_max"] = float(dist.max())
        rec["hits"] = int(hit.sum())
        if not (rec["warp_px_p999"] <= args.px_tol):
            fails.append(f"f{f['id']:03d}: (a) directions off the Position pass by {rec['warp_px_p999']:.2f} px at p99.9")

        # (b) fovea vs reference; (c) the same after a rotation, must fail
        fwd_eye = R_eye.T @ np.array(meta["camera_forward"], float)
        ecc = np.degrees(np.arccos(np.clip(d @ fwd_eye, -1.0, 1.0)))
        fov = (ecc <= args.fovea_deg) & hit
        rec["fovea_samples"] = int(fov.sum())
        rec["fovea_rel_median"], _ = rel_diff_median(s["value"][fov], d[fov], ref)
        rec["control_rel_median"], _ = rel_diff_median(s["value"][fov], d[fov] @ rot_y(args.control_yaw).T, ref)
        # Diagnostic, not a criterion: how much the reference disagrees with itself half a pixel
        # away at these directions. Where this exceeds the noise bound, (b) is measuring
        # sub-pixel alignment on texture edges rather than noise (calib room cards, 2026-09-13).
        rec["align_floor_rel_median"] = alignment_floor(d[fov], ref)
        if not (rec["fovea_rel_median"] < threshold):
            fails.append(f"f{f['id']:03d}: (b) foveal median rel diff {rec['fovea_rel_median']:.4f} >= {threshold:.4f}")
        if not (rec["control_rel_median"] >= threshold):
            fails.append(f"f{f['id']:03d}: (c) control at {args.control_yaw} deg yaw still passes "
                         f"({rec['control_rel_median']:.4f} < {threshold:.4f})")

        # (d) footprints sum to the cap
        rec["footprint_sum_sr"] = float(s["footprint"].astype(np.float64).sum())
        rec["cap_rel_err"] = abs(rec["footprint_sum_sr"] - cap) / cap
        if not (rec["cap_rel_err"] <= args.cap_tol):
            fails.append(f"f{f['id']:03d}: (d) footprints sum to {rec['footprint_sum_sr']:.4f} sr vs cap {cap:.4f}")
        per.append(rec)

    def agg(key):
        v = np.array([r[key] for r in per], float)
        return {"median": float(np.median(v)), "min": float(v.min()), "max": float(v.max())}

    report = {
        "sequence": args.sequence, "reference": args.reference, "fixations": len(per),
        "threshold_rel": threshold, "threshold_how": f"sqrt({args.noise_fix}^2 + {args.noise_ref}^2)",
        "cap_sr": cap, "px_tol": args.px_tol,
        "warp_px_p999": agg("warp_px_p999"), "warp_px_max": agg("warp_px_max"),
        "fovea_rel_median": agg("fovea_rel_median"), "control_rel_median": agg("control_rel_median"),
        "fovea_samples": agg("fovea_samples"), "align_floor_rel_median": agg("align_floor_rel_median"),
        "fovea_pass_count": int(sum(r["fovea_rel_median"] < threshold for r in per)),
        "control_fail_count": int(sum(r["control_rel_median"] >= threshold for r in per)),
        "cap_rel_err": agg("cap_rel_err"),
        "reader_max_abs_diff": agg("reader_max_abs_diff"),
        "per_fixation": per, "checks_failed": fails,
    }
    with open(os.path.join(args.sequence, "check.json"), "w") as fh:
        json.dump(report, fh, indent=1)
    print(json.dumps({k: v for k, v in report.items() if k != "per_fixation"}, indent=1))
    raise SystemExit(1 if fails else 0)


if __name__ == "__main__":
    main()
