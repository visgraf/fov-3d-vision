"""Run one FSG5 active curved-surface growth trial.

The host loop imports no FSG5 fixture geometry or evaluator-only asset.  It uses
only the frozen FSG1 RGB-D instrument, the existing FSG4 frontier policy, the
persistent FSG3 surface map, oracle instance masks and calibration.
"""
from __future__ import annotations
import argparse
import json
import subprocess
import time
from pathlib import Path
import numpy as np
import cv2
from PIL import Image

import fsg5_public as public
import fsg4_public as frozen_public
import fsg4_policy as policy
from fsg3_surface_map import Patch, SurfaceMap, initialize, fuse, save_map
import fsg_stereo_hdr as hdr
from fsg_stereo_supported import compute_once, check_kernel_equivalence
from fsg_geometry import json_write


def patch_from_record(pid: str, rec: dict) -> Patch:
    m = rec["valid"] & (rec["instance_id"] == public.OBJECT_ID)
    return Patch(pid, rec["xyz_h"][m], rec["rgb_left"][m], rec["instance_id"][m])


def object_measurement_stats(rec: dict) -> tuple[int, int, float | None]:
    ref = (rec["instance_id"] == public.OBJECT_ID) & rec["raw_support_L"]
    nref = int(ref.sum())
    nvalid = int((rec["valid"] & ref).sum())
    return nref, nvalid, (float(nvalid / nref) if nref else None)


def write_patch_visual(path: Path, rec: dict) -> None:
    obj = (rec["instance_id"] == public.OBJECT_ID) & rec["raw_support_L"]
    valid = rec["valid"] & obj
    im = np.zeros((*obj.shape, 3), np.uint8)
    im[obj] = (120, 120, 120)
    im[valid] = (255, 255, 255)
    Image.fromarray(im).save(path)


def write_growth(path: Path, snapshots: list[np.ndarray], supports: list[np.ndarray], yaws: list[float]) -> None:
    h = 300; w = 360 * len(snapshots)
    canvas = np.full((h, w, 3), 245, np.uint8)
    for k, (xyz, sup, g) in enumerate(zip(snapshots, supports, yaws)):
        yaw = np.degrees(np.arctan2(xyz[:, 0], -xyz[:, 2]))
        pitch = np.degrees(np.arctan2(xyz[:, 1], np.sqrt(xyz[:, 0] ** 2 + xyz[:, 2] ** 2)))
        x0 = k * 360
        cv2.rectangle(canvas, (x0 + 20, 30), (x0 + 340, 280), (210, 210, 210), 1)
        cv2.putText(canvas, f"active {k}: yaw {g:.1f}", (x0 + 28, 22), cv2.FONT_HERSHEY_SIMPLEX, .45, (20, 20, 20), 1, cv2.LINE_AA)
        px = np.clip(((yaw + 28) / 56) * 300 + x0 + 30, x0 + 30, x0 + 330).astype(int)
        py = np.clip(((7 - pitch) / 14) * 220 + 45, 45, 265).astype(int)
        strong = sup > 1
        for X, Y, S in zip(px[::2], py[::2], strong[::2]):
            canvas[Y, X] = (25, 25, 25) if S else (145, 145, 145)
    cv2.imwrite(str(path), canvas)


def save_ply(path: Path, sm: SurfaceMap) -> None:
    xyz = np.asarray(sm.xyz_h, float); rgb = np.clip(np.asarray(sm.rgb, float), 0.0, 1.0)
    c = np.rint(255.0 * rgb).astype(np.uint8)
    with path.open("w", encoding="ascii") as f:
        f.write("ply\nformat ascii 1.0\ncomment fixed head frame H\n")
        f.write(f"element vertex {len(xyz)}\n")
        f.write("property float x\nproperty float y\nproperty float z\n")
        f.write("property uchar red\nproperty uchar green\nproperty uchar blue\n")
        f.write("property ushort support\nend_header\n")
        for p, q, n in zip(xyz, c, sm.support_count):
            f.write(f"{p[0]:.8g} {p[1]:.8g} {p[2]:.8g} {int(q[0])} {int(q[1])} {int(q[2])} {int(n)}\n")


def run_blender(args, step: int, yaw: float, acq_root: Path) -> tuple[Path, dict]:
    out = acq_root / f"fix_{step:02d}"
    cmd = [args.blender, "-b", "--python-exit-code", "1", "-P", "tools/fsg5_render_fix.py", "--",
           "--out", str(out), "--profile", args.profile, "--fixture", args.fixture,
           "--seed", str(args.seed), "--step", str(step), "--yaw", f"{yaw:.12g}", "--device", args.device]
    if args.save_blend:
        cmd.append("--save-blend")
    p = subprocess.run(cmd, cwd=args.repo, text=True, capture_output=True)
    log = args.out / "logs" / f"render_{step:02d}.log"
    log.write_text(p.stdout + "\n--- STDERR ---\n" + p.stderr)
    if p.returncode != 0:
        raise RuntimeError(f"Blender fixation {step} failed; see {log}")
    run = json.loads((out / "run.json").read_text())
    case = out / f"fix_{step:02d}"
    if (not run.get("complete") or run.get("fixture") != args.fixture or int(run.get("seed")) != args.seed
            or abs(float(run["yaw_deg"]) - yaw) > 1e-8):
        raise RuntimeError("incomplete or wrong FSG5 Blender record")
    return case, run


def execute(args) -> dict:
    args.repo = Path(args.repo).resolve(); args.out = Path(args.out).resolve()
    if args.out.exists():
        raise FileExistsError("output must be new")
    args.out.mkdir(parents=True)
    for d in ("logs", "acquisitions", "patches", "maps"):
        (args.out / d).mkdir()
    check_kernel_equivalence()
    if public.POLICY != frozen_public.POLICY:
        raise AssertionError("FSG5 must use the existing frozen FSG4 frontier policy constants")
    if public.FUSION != frozen_public.FUSION:
        raise AssertionError("FSG5 must use the existing frozen 12 mm fusion rule")
    if public.OBJECT_ID != frozen_public.OBJECT_ID or public.BACKGROUND_ID != frozen_public.BACKGROUND_ID:
        raise AssertionError("FSG5 object IDs must remain compatible with existing fsg4_policy")
    if args.fixture not in public.FIXTURES or args.seed not in public.SEEDS:
        raise ValueError("fixture/seed outside frozen FSG5 schedule")

    yaws = []; patch_stats = []; assoc_stats = []; policy_trace = []
    samples = 0; render_seconds = 0.0; snapshots = []; supports = []; sm = None
    yaw = float(public.SEED_GAZE_YAW_DEG[args.fixture])
    termination = None
    t0 = time.perf_counter()
    for step in range(public.MAX_BUDGET_FIXATIONS):
        if any(abs(yaw - z) < 1e-9 for z in yaws):
            raise AssertionError("policy revisited an existing fixation")
        case, rr = run_blender(args, step, yaw, args.out / "acquisitions")
        samples += int(rr["primary_camera_samples"])
        render_seconds += float(rr["total_wall_seconds"])
        c, obs = hdr.read_observation(case)
        rec, meta, _ = compute_once(c, obs)
        pid = f"fix_{step:02d}"
        p = patch_from_record(pid, rec)
        nref, nvalid, cov = object_measurement_stats(rec)
        np.savez_compressed(args.out / "patches" / f"{pid}.npz",
                            xyz_h=p.xyz_h.astype(np.float32), rgb=p.rgb.astype(np.float32),
                            instance_id=p.instance_id, valid=rec["valid"],
                            oracle_instance_id=rec["instance_id"], raw_support_L=rec["raw_support_L"])
        write_patch_visual(args.out / "patches" / f"{pid}_mask.png", rec)
        if len(p.xyz_h) < 100:
            raise ValueError("active FSG5 fixation has too few object points")
        if sm is None:
            sm = initialize(p, public.OBJECT_ID)
            assoc = {"duplicate_patch": False, "matched": 0, "new": len(p.xyz_h), "affected_surfels": 0,
                     "distances_m": np.empty(0), "input_points": len(p.xyz_h), "base_points": 0}
            idempotent = True
        else:
            sm, assoc = fuse(sm, p, public.OBJECT_ID, public.FUSION["association_radius_m"], public.FUSION["hash_cell_m"])
            replay, dup = fuse(sm, p, public.OBJECT_ID, public.FUSION["association_radius_m"], public.FUSION["hash_cell_m"])
            idempotent = bool(dup["duplicate_patch"] and np.array_equal(sm.xyz_h, replay.xyz_h)
                              and np.array_equal(sm.support_count, replay.support_count)
                              and np.array_equal(sm.provenance_mask, replay.provenance_mask))
            if not idempotent:
                raise AssertionError("patch replay is not idempotent")
        save_map(args.out / "maps" / f"map_{step:02d}.npz", sm)
        snapshots.append(sm.xyz_h.copy()); supports.append(sm.support_count.copy()); yaws.append(float(yaw))
        dist = assoc["distances_m"]
        assoc_stats.append({
            "step": step, "patch_id": pid, "input_points": int(assoc["input_points"]),
            "matched": int(assoc["matched"]), "new": int(assoc["new"]),
            "affected_surfels": int(assoc["affected_surfels"]),
            "new_fraction": float(assoc["new"] / max(1, assoc["input_points"])),
            "overlap_median_distance_m": float(np.median(dist)) if len(dist) else None,
            "overlap_p95_distance_m": float(np.percentile(dist, 95)) if len(dist) else None,
            "idempotent_replay": idempotent,
        })
        patch_stats.append({
            "step": step, "patch_id": pid, "yaw_deg": float(yaw),
            "object_reference_count": nref, "object_valid_count": nvalid,
            "object_measurement_fraction": cov, "point_count": len(p.xyz_h),
            "instrument": public.INSTRUMENT_ID,
        })
        decision = policy.choose_next(yaw, c, rec["instance_id"], rec["raw_support_L"], sm.xyz_h, yaws)
        decision["step"] = step; policy_trace.append(decision)
        if decision["stop"]:
            termination = decision["reason"]
            break
        yaw = float(decision["next_yaw_deg"])
    if termination is None:
        termination = "max_fixations"
    save_map(args.out / "surface_map.npz", sm)
    save_ply(args.out / "surface_map.ply", sm)
    write_growth(args.out / "growth.png", snapshots, supports, yaws)
    json_write(args.out / "policy_trace.json", {"policy": "frozen_fsg4_frontier", "trace": policy_trace})
    manifest = {
        "schema": "FSG5-prediction-v1",
        "instrument": public.INSTRUMENT_ID,
        "public_spec_sha256": public.public_digest(),
        "profile": args.profile,
        "fixture": args.fixture,
        "seed": args.seed,
        "fixation_yaws_deg": yaws,
        "termination_reason": termination,
        "patch_stats": patch_stats,
        "association_stats": assoc_stats,
        "truth_opened": False,
        "policy_inputs": ["persistent map xyz_h", "current rectified oracle instance mask", "raw calibration support", "calibration", "fixation history"],
        "primary_camera_samples": samples,
        "blender_recorded_wall_seconds": render_seconds,
        "loop_wall_seconds": time.perf_counter() - t0,
    }
    json_write(args.out / "prediction_manifest.json", manifest)
    print("[fsg5-run] COMPLETE", json.dumps({"fixture": args.fixture, "seed": args.seed, "fixations": len(yaws),
          "yaws": yaws, "termination": termination, "samples": samples}, sort_keys=True), flush=True)
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--out", required=True)
    ap.add_argument("--profile", choices=("small", "full"), required=True)
    ap.add_argument("--fixture", choices=public.FIXTURES, required=True)
    ap.add_argument("--seed", type=int, choices=public.SEEDS, required=True)
    ap.add_argument("--device", choices=("OPTIX", "CUDA", "CPU"), default="OPTIX")
    ap.add_argument("--blender", default="blender")
    ap.add_argument("--save-blend", action="store_true")
    execute(ap.parse_args())


if __name__ == "__main__":
    main()
