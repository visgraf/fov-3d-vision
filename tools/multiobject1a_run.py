"""Add one prescribed second-object seed to the completed Cyclopean-1g scene."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

import cyclopean1g_public as parent_public
import fsg_stereo_hdr as hdr
from fsg_stereo_supported import compute_once, check_kernel_equivalence
from fsg3_surface_map import load_map
from fsg_geometry import json_write
from reality1_run import _tone_preview

import multiobject1a_public as public
from multiobject1a_seed import select_prescribed_seed, xyz_to_yaw_pitch_deg


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _validate_parent(parent: Path) -> dict:
    m = json.loads((parent / "prediction_manifest.json").read_text())
    if m.get("schema") != "Cyclopean1g-recentered-measurement-v1":
        raise AssertionError("MultiObject-1a requires the completed Cyclopean-1g parent")
    if m.get("public_spec_sha256") != parent_public.public_digest():
        raise AssertionError("Cyclopean-1g public digest mismatch")
    if int(m.get("seed", -1)) != public.SEED or m.get("truth_opened") is not False:
        raise AssertionError("wrong seed or truth integrity broken")
    if not m.get("fixed_head") or not m.get("static_scene"):
        raise AssertionError("fixed-head/static-scene invariant broken")
    # Cyclopean-1g records the diagnostic label inside probe_result, which is
    # where its own comparator reads it; there is no top-level copy.
    if m.get("probe_result", {}).get("measurement_outcome") not in ("DEPTH_RECOVERED", "DEPTH_STILL_ABSENT"):
        raise AssertionError("Cyclopean-1g did not complete its declared one-look diagnostic")
    return m


def _record_chain(parent: Path) -> list[Path]:
    out = []
    seen = set()
    cur = parent.resolve()
    while cur not in seen and (cur / "prediction_manifest.json").is_file():
        seen.add(cur); out.append(cur)
        m = json.loads((cur / "prediction_manifest.json").read_text())
        p = m.get("parent_record")
        if not p:
            break
        nxt = Path(p)
        if not nxt.is_absolute():
            nxt = (cur / nxt).resolve()
        cur = nxt.resolve()
    out.reverse()
    return out


def _acquisition_cases(chain: list[Path]) -> list[tuple[int, Path]]:
    found = {}
    for rec in chain:
        for p in rec.rglob("fix_*"):
            if not p.is_dir() or not (p / "calibration.json").is_file():
                continue
            try:
                step = int(p.name.split("_")[-1])
            except ValueError:
                continue
            if step in found and found[step] != p:
                raise AssertionError(f"duplicate acquisition for fixation {step}: {found[step]} vs {p}")
            found[step] = p
    if not found:
        raise AssertionError("no completed acquisitions found in Cyclopean-1g ancestry")
    return sorted(found.items())


def _collect_second_object_evidence(cases: list[tuple[int, Path]]) -> tuple[np.ndarray, list[dict]]:
    chunks = []
    per_fix = []
    for step, case in cases:
        c, obs = hdr.read_observation(case)
        rec, _, _ = compute_once(c, obs)
        mask = rec["valid"] & (rec["instance_id"] == public.OBJECT_ID_2)
        n = int(mask.sum())
        per_fix.append({"step": int(step), "path": str(case), "valid_object2_points": n})
        if n:
            chunks.append(np.asarray(rec["xyz_h"][mask], dtype=np.float64))
    if not chunks:
        raise AssertionError("declared second object 143 has no prior valid prediction-side evidence")
    return np.concatenate(chunks, axis=0), per_fix


def _run_blender(args, profile: str, step: int, gaze: tuple[float, float]) -> Path:
    out = args.out / "acquisition"
    out.mkdir()
    cmd = [
        args.blender, "-b", "--python-exit-code", "1",
        "-P", "tools/reality2_render_fix.py", "--",
        "--out", str(out), "--profile", profile, "--seed", str(public.SEED),
        "--step", str(step), "--yaw", f"{gaze[0]:.12g}",
        "--pitch", f"{gaze[1]:.12g}", "--device", args.device,
    ]
    p = subprocess.run(cmd, cwd=args.repo, text=True, capture_output=True)
    (args.out / "render.log").write_text(p.stdout + "\n--- STDERR ---\n" + p.stderr)
    if p.returncode != 0:
        raise RuntimeError("MultiObject-1a Blender seed fixation failed; see render.log")
    return out / f"fix_{step:02d}"


def _scene_chart(obj1_xyz: np.ndarray, obj2_xyz: np.ndarray, grid_deg: float):
    y1, p1 = xyz_to_yaw_pitch_deg(obj1_xyz)
    y2, p2 = xyz_to_yaw_pitch_deg(obj2_xyz)
    if not len(y1) or not len(y2):
        raise AssertionError("both objects need finite angular support")
    g = float(grid_deg)
    ymin = np.floor((min(float(y1.min()), float(y2.min())) - 0.5) / g) * g
    ymax = np.ceil((max(float(y1.max()), float(y2.max())) + 0.5) / g) * g
    pmin = np.floor((min(float(p1.min()), float(p2.min())) - 0.5) / g) * g
    pmax = np.ceil((max(float(p1.max()), float(p2.max())) + 0.5) / g) * g
    w = int(round((ymax - ymin) / g)) + 1
    h = int(round((pmax - pmin) / g)) + 1
    a = np.zeros((h, w), bool); b = np.zeros((h, w), bool)
    def put(arr, yy, pp):
        x = np.rint((yy - ymin) / g).astype(int)
        y = np.rint((pp - pmin) / g).astype(int)
        good = (x >= 0) & (x < w) & (y >= 0) & (y < h)
        arr[y[good], x[good]] = True
    put(a, y1, p1); put(b, y2, p2)
    return {
        "yaw0_deg": float(ymin), "pitch0_deg": float(pmin), "grid_deg": g,
        "width": int(w), "height": int(h),
    }, a, b


def _write_scene_png(path: Path, a: np.ndarray, b: np.ndarray) -> None:
    # neutral grayscale for object 141, distinct intensity for 143; overlap brightest.
    im = np.zeros(a.shape, dtype=np.uint8)
    im[a] = 110
    im[b] = 190
    im[a & b] = 255
    Image.fromarray(np.flipud(im), mode="L").resize((im.shape[1]*3, im.shape[0]*3), Image.Resampling.NEAREST).save(path)


def execute(args) -> dict:
    args.repo = Path(args.repo).resolve(); args.parent = Path(args.parent).resolve(); args.out = Path(args.out).resolve()
    if args.out.exists():
        raise FileExistsError("output must be new")
    args.out.mkdir(parents=True)
    check_kernel_equivalence()

    pm = _validate_parent(args.parent)
    parent_hash_before = {n: _sha256(args.parent / n) for n in ("prediction_manifest.json", "surface_map.npz")}
    object1 = load_map(args.parent / "surface_map.npz")
    if set(np.unique(object1.instance_id).tolist()) != {public.OBJECT_ID_1}:
        raise AssertionError("inherited object-141 map is not pure")

    chain = _record_chain(args.parent)
    cases = _acquisition_cases(chain)
    prior_xyz2, per_fix = _collect_second_object_evidence(cases)
    selection = select_prescribed_seed(prior_xyz2, public.GRID_DEG)
    gaze = tuple(map(float, selection["probe_gaze_deg"]))

    profile = str(pm.get("profile", "full"))
    step = int(pm.get("total_fixations_after", len(cases)))
    case = _run_blender(args, profile, step, gaze)
    c, obs = hdr.read_observation(case)
    rec, _, _ = compute_once(c, obs)
    target2 = rec["valid"] & (rec["instance_id"] == public.OBJECT_ID_2)
    target1 = rec["valid"] & (rec["instance_id"] == public.OBJECT_ID_1)
    xyz2 = np.asarray(rec["xyz_h"][target2], dtype=np.float32)
    rgb2 = np.asarray(rec["rgb_left"][target2], dtype=np.float32)
    ids2 = np.asarray(rec["instance_id"][target2])
    np.savez_compressed(
        args.out / "object_143_seed_patch.npz",
        xyz_h=xyz2, rgb=rgb2, instance_id=ids2,
        valid=rec["valid"], oracle_instance_id=rec["instance_id"], raw_support_L=rec["raw_support_L"],
    )
    Image.fromarray(_tone_preview(rec["rgb_left"])).save(args.out / "second_object_seed_rgb.png")

    chart, footprint1, footprint2 = _scene_chart(object1.xyz_h, xyz2, public.GRID_DEG)
    np.savez_compressed(args.out / "scene_cyclopean_footprints.npz", object_141=footprint1, object_143=footprint2, **chart)
    _write_scene_png(args.out / "scene_cyclopean_footprints.png", footprint1, footprint2)

    scene_graph = {
        "schema": "MultiObject1a-scene-graph-v1",
        "fixed_head": True,
        "static_scene": True,
        "objects": [
            {
                "object_id": public.OBJECT_ID_1,
                "geometry": "SURFEL_MAP",
                "source": str(args.parent / "surface_map.npz"),
                "source_sha256": parent_hash_before["surface_map.npz"],
                "point_count": int(len(object1.xyz_h)),
                "read_only": True,
            },
            {
                "object_id": public.OBJECT_ID_2,
                "geometry": "SEED_SURFEL_PATCH",
                "source": str(args.out / "object_143_seed_patch.npz"),
                "point_count": int(len(xyz2)),
                "read_only": False,
            },
        ],
        "cyclopean_chart": chart,
        "raw_footprint_cells": {
            "141": int(footprint1.sum()),
            "143": int(footprint2.sum()),
            "overlap": int((footprint1 & footprint2).sum()),
        },
    }
    json_write(args.out / "scene_graph.json", scene_graph)

    parent_hash_after = {n: _sha256(args.parent / n) for n in parent_hash_before}
    if parent_hash_after != parent_hash_before:
        raise AssertionError("Cyclopean-1g parent was modified")

    manifest = {
        "schema": "MultiObject1a-second-object-seed-v1",
        "public_spec_sha256": public.public_digest(),
        "parent_spec": public.PARENT_SPEC_ID,
        "parent_record": str(args.parent),
        "parent_hashes": parent_hash_before,
        "seed": public.SEED,
        "profile": profile,
        "fixture": public.FIXTURE,
        "fixed_head": True,
        "static_scene": True,
        "truth_opened": False,
        "object_ids": list(public.OBJECT_IDS),
        "object_1_map_points": int(len(object1.xyz_h)),
        "object_2_prior_evidence_points": int(len(prior_xyz2)),
        "object_2_prior_evidence_by_fixation": per_fix,
        "selection": selection,
        "probe_gaze_deg": [float(gaze[0]), float(gaze[1])],
        "added_fixations": 1,
        "parent_fixations_rerendered": 0,
        "object_2_seed_target_points": int(len(xyz2)),
        "object_1_points_in_seed_view": int(target1.sum()),
        "object_2_patch_pure": bool(len(ids2) == 0 or set(np.unique(ids2).tolist()) == {public.OBJECT_ID_2}),
        "object_1_parent_pure": True,
        "scene_graph": "scene_graph.json",
        "scene_footprints": "scene_cyclopean_footprints.npz",
        "scene_footprint_overlap_cells": int((footprint1 & footprint2).sum()),
        "next_stage": "grow object 143 independently; automatic next-object discovery still deferred",
        "structural_fails": [],
    }
    json_write(args.out / "prediction_manifest.json", manifest)
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--parent", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--blender", default="blender")
    ap.add_argument("--device", default="OPTIX")
    a = ap.parse_args()
    m = execute(a)
    print("[multiobject1a-run] MULTIOBJECT1A_COMPLETE " + json.dumps({
        "object_ids": m["object_ids"],
        "object_1_map_points": m["object_1_map_points"],
        "object_2_seed_target_points": m["object_2_seed_target_points"],
        "probe_gaze_deg": m["probe_gaze_deg"],
        "footprint_overlap_cells": m["scene_footprint_overlap_cells"],
        "structural_fails": m["structural_fails"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
