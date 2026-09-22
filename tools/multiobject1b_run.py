"""Grow the MultiObject-1a object-143 seed with frozen FSG6f local exploration."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

import numpy as np
from PIL import Image

import fsg6f_public as frozen_public
import fsg6f_run as fsg6run
import fsg_stereo_hdr as hdr
from fsg3_surface_map import Patch, fuse, initialize, load_map, save_map
from fsg_geometry import json_write
from fsg_stereo import support_mask
from fsg_stereo_supported import check_kernel_equivalence, compute_once
from reality1_run import _tone_preview

import multiobject1a_public as parent_public
from multiobject1a_run import _scene_chart, _write_scene_png
import multiobject1b_policy as policy
import multiobject1b_public as public


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _resolve_source(parent: Path, source: str) -> Path:
    p = Path(source)
    if not p.is_absolute():
        p = (parent / p).resolve()
    return p.resolve()


def _validate_parent(parent: Path) -> tuple[dict, dict, Path]:
    m = json.loads((parent / "prediction_manifest.json").read_text())
    if m.get("schema") != "MultiObject1a-second-object-seed-v1":
        raise AssertionError("MultiObject-1b requires the completed MultiObject-1a parent")
    if m.get("public_spec_sha256") != parent_public.public_digest():
        raise AssertionError("MultiObject-1a public digest mismatch")
    if int(m.get("seed", -1)) != public.SEED or m.get("truth_opened") is not False:
        raise AssertionError("wrong seed or truth integrity broken")
    if not m.get("fixed_head") or not m.get("static_scene"):
        raise AssertionError("fixed-head/static-scene invariant broken")
    if m.get("object_ids") != list(public.OBJECT_IDS):
        raise AssertionError("parent object ids changed")
    if int(m.get("added_fixations", -1)) != 1:
        raise AssertionError("MultiObject-1a did not contain exactly one second-object seed")
    sg = json.loads((parent / "scene_graph.json").read_text())
    objs = {int(o["object_id"]): o for o in sg.get("objects", [])}
    if set(objs) != set(public.OBJECT_IDS):
        raise AssertionError("parent scene graph does not contain exactly objects 141 and 143")
    o1 = objs[public.OBJECT_ID_1]
    if not o1.get("read_only") or o1.get("geometry") != "SURFEL_MAP":
        raise AssertionError("object 141 is not the inherited read-only surfel entity")
    object1_source = _resolve_source(parent, o1["source"])
    if not object1_source.is_file():
        raise FileNotFoundError(object1_source)
    if o1.get("source_sha256") and _sha256(object1_source) != o1["source_sha256"]:
        raise AssertionError("object-141 source hash differs from MultiObject-1a scene graph")
    return m, sg, object1_source


def _seed_case(parent: Path) -> tuple[int, Path]:
    rows = []
    root = parent / "acquisition"
    for p in root.glob("fix_*"):
        if p.is_dir() and (p / "calibration.json").is_file():
            try:
                step = int(p.name.split("_")[-1])
            except ValueError:
                continue
            rows.append((step, p))
    if len(rows) != 1:
        raise AssertionError(f"expected exactly one MultiObject-1a seed acquisition, found {len(rows)}")
    return rows[0]


def _right_state(c: dict, rec: dict, state: dict) -> tuple[np.ndarray, np.ndarray]:
    x, y, cw, ch = map(int, rec["crop_xywh"])
    sl = np.s_[y:y+ch, x:x+cw]
    ids_R = state["ids_right"][sl]
    raw_R = support_mask(c, rec, "R")[sl]
    if not np.array_equal(rec["instance_id"], state["ids_left"][sl]):
        raise AssertionError("left rectified ID replay mismatch")
    return ids_R, raw_R


def _patch_from_record(pid: str, rec: dict) -> Patch:
    m = rec["valid"] & (rec["instance_id"] == public.OBJECT_ID_2)
    return Patch(pid, rec["xyz_h"][m], rec["rgb_left"][m], rec["instance_id"][m])


def _save_patch(path: Path, p: Patch, rec: dict, ids_R: np.ndarray, raw_R: np.ndarray) -> None:
    np.savez_compressed(
        path,
        xyz_h=np.asarray(p.xyz_h, np.float32), rgb=np.asarray(p.rgb, np.float32),
        instance_id=np.asarray(p.instance_id), valid=rec["valid"],
        oracle_instance_id=rec["instance_id"], raw_support_L=rec["raw_support_L"],
        oracle_instance_id_R=ids_R, raw_support_R=raw_R,
    )


def _run_blender(args, step: int, gaze: tuple[float, float]) -> Path:
    out = args.out / "acquisitions" / f"fix_{step:02d}"
    yaw, pitch = map(float, gaze)
    cmd = [
        args.blender, "-b", "--python-exit-code", "1",
        "-P", "tools/reality2_render_fix.py", "--",
        "--out", str(out), "--profile", args.profile, "--seed", str(public.SEED),
        "--step", str(step), "--yaw", f"{yaw:.12g}", "--pitch", f"{pitch:.12g}",
        "--device", args.device,
    ]
    p = subprocess.run(cmd, cwd=args.repo, text=True, capture_output=True)
    (args.out / "logs" / f"render_{step:02d}.log").write_text(p.stdout + "\n--- STDERR ---\n" + p.stderr)
    if p.returncode != 0:
        raise RuntimeError(f"MultiObject-1b Blender fixation {step} failed; see render log")
    rr = json.loads((out / "run.json").read_text())
    case = out / f"fix_{step:02d}"
    if not rr.get("complete") or int(rr.get("seed", -1)) != public.SEED:
        raise RuntimeError("incomplete or wrong MultiObject-1b Blender record")
    if abs(float(rr["yaw_deg"]) - yaw) > 1e-8 or abs(float(rr["pitch_deg"]) - pitch) > 1e-8:
        raise RuntimeError("Blender record gaze mismatch")
    return case


def _scene_graph(parent: Path, object1_source: Path, object1_hash: str,
                 object1_points: int, object2_path: Path, object2_points: int,
                 chart: dict, fp1: np.ndarray, fp2: np.ndarray,
                 object2_fixations: int, termination: str) -> dict:
    return {
        "schema": "MultiObject1b-scene-graph-v1",
        "fixed_head": True,
        "static_scene": True,
        "objects": [
            {
                "object_id": public.OBJECT_ID_1,
                "geometry": "SURFEL_MAP",
                "source": str(object1_source),
                "source_sha256": object1_hash,
                "point_count": int(object1_points),
                "read_only": True,
            },
            {
                "object_id": public.OBJECT_ID_2,
                "geometry": "SURFEL_MAP",
                "source": str(object2_path),
                "point_count": int(object2_points),
                "read_only": False,
                "growth_parent": str(parent / "object_143_seed_patch.npz"),
                "active_fixations": int(object2_fixations),
                "termination_reason": str(termination),
            },
        ],
        "cyclopean_chart": chart,
        "raw_footprint_cells": {
            "141": int(fp1.sum()), "143": int(fp2.sum()), "overlap": int((fp1 & fp2).sum())
        },
    }


def execute(args) -> dict:
    args.repo = Path(args.repo).resolve()
    args.parent = Path(args.parent).resolve()
    args.out = Path(args.out).resolve()
    if args.out.exists():
        raise FileExistsError("output must be new")
    args.out.mkdir(parents=True)
    for d in ("logs", "acquisitions", "patches", "maps", "rgb"):
        (args.out / d).mkdir()

    check_kernel_equivalence()
    if public.FUSION != dict(frozen_public.FUSION):
        raise AssertionError("MultiObject-1b changed the frozen 12 mm FSG6f fusion rule")

    pm, _parent_scene, object1_source = _validate_parent(args.parent)
    args.profile = str(pm.get("profile", "full"))
    object1_hash_before = _sha256(object1_source)
    parent_hash_before = {
        n: _sha256(args.parent / n)
        for n in ("prediction_manifest.json", "scene_graph.json", "object_143_seed_patch.npz")
    }
    object1 = load_map(object1_source)
    if set(np.unique(object1.instance_id).tolist()) != {public.OBJECT_ID_1}:
        raise AssertionError("inherited object-141 map is not pure")

    seed_step, seed_case = _seed_case(args.parent)
    c, obs = hdr.read_observation(seed_case)
    rec, _meta, state = compute_once(c, obs)
    ids_R, raw_R = _right_state(c, rec, state)
    p0 = _patch_from_record(f"fix_{seed_step:02d}", rec)
    if set(np.unique(p0.instance_id).tolist()) != {public.OBJECT_ID_2}:
        raise AssertionError("MultiObject-1a seed acquisition is not pure id 143")
    with np.load(args.parent / "object_143_seed_patch.npz", allow_pickle=False) as z:
        if len(z["xyz_h"]) != len(p0.xyz_h):
            raise AssertionError("saved MultiObject-1a seed patch no longer matches its acquisition")

    sm = initialize(p0, public.OBJECT_ID_2)
    save_map(args.out / "maps" / f"map_{seed_step:02d}.npz", sm)
    gazes = [tuple(map(float, pm["probe_gaze_deg"]))]
    snapshots = [sm.xyz_h.copy()]
    supports = [sm.support_count.copy()]
    history = [policy.history_entry(c, rec["instance_id"], rec["raw_support_L"], ids_R, raw_R)]
    policy_trace = []
    patch_stats = [{
        "global_step": int(seed_step), "object_fixation_index": 0, "patch_id": f"fix_{seed_step:02d}",
        "yaw_deg": gazes[0][0], "pitch_deg": gazes[0][1], "point_count": int(len(p0.xyz_h)),
        "source": "MultiObject-1a prescribed seed",
    }]
    association_stats = [{
        "global_step": int(seed_step), "object_fixation_index": 0, "input_points": int(len(p0.xyz_h)),
        "matched": 0, "new": int(len(p0.xyz_h)), "empty_look": False, "idempotent_replay": True,
    }]
    empty_steps: list[int] = []
    Image.fromarray(_tone_preview(rec["rgb_left"])).save(args.out / "rgb" / f"fix_{seed_step:02d}.png")

    decision = policy.choose_next(
        gazes[-1][0], gazes[-1][1], c,
        rec["instance_id"], rec["raw_support_L"], ids_R, raw_R,
        sm.xyz_h, gazes, history,
    )
    decision["object_fixation_index"] = 0
    decision["global_step"] = int(seed_step)
    policy_trace.append(decision)

    termination = None
    t0 = time.perf_counter()
    while True:
        if decision.get("stop"):
            termination = str(decision.get("reason", "policy_stop"))
            break
        if len(gazes) >= public.OBJECT2_WATCHDOG_FIXATIONS:
            termination = "object2_watchdog"
            break

        gaze = tuple(map(float, decision["next_gaze_deg"]))
        if any(np.allclose(g, gaze, atol=1e-9) for g in gazes):
            raise AssertionError("object-143 policy revisited an existing fixation")
        global_step = int(seed_step + len(gazes))
        case = _run_blender(args, global_step, gaze)
        c, obs = hdr.read_observation(case)
        rec, _meta, state = compute_once(c, obs)
        ids_R, raw_R = _right_state(c, rec, state)
        pid = f"fix_{global_step:02d}"
        p = _patch_from_record(pid, rec)
        _save_patch(args.out / "patches" / f"{pid}.npz", p, rec, ids_R, raw_R)
        Image.fromarray(_tone_preview(rec["rgb_left"])).save(args.out / "rgb" / f"{pid}.png")

        empty = len(p.xyz_h) < public.MIN_TARGET_POINTS
        if empty:
            empty_steps.append(global_step)
            assoc = {
                "input_points": int(len(p.xyz_h)), "matched": 0, "new": 0,
                "affected_surfels": 0, "distances_m": np.empty(0), "duplicate_patch": False,
            }
            idempotent = True
        else:
            sm, assoc = fuse(
                sm, p, public.OBJECT_ID_2,
                public.FUSION["association_radius_m"], public.FUSION["hash_cell_m"],
            )
            replay, dup = fuse(
                sm, p, public.OBJECT_ID_2,
                public.FUSION["association_radius_m"], public.FUSION["hash_cell_m"],
            )
            idempotent = bool(
                dup["duplicate_patch"] and np.array_equal(sm.xyz_h, replay.xyz_h)
                and np.array_equal(sm.support_count, replay.support_count)
                and np.array_equal(sm.provenance_mask, replay.provenance_mask)
            )
            if not idempotent:
                raise AssertionError("object-143 patch replay is not idempotent")

        if set(np.unique(sm.instance_id).tolist()) != {public.OBJECT_ID_2}:
            raise AssertionError("cross-object contamination entered object-143 map")
        save_map(args.out / "maps" / f"map_{global_step:02d}.npz", sm)
        gazes.append(gaze)
        snapshots.append(sm.xyz_h.copy())
        supports.append(sm.support_count.copy())
        history.append(policy.history_entry(c, rec["instance_id"], rec["raw_support_L"], ids_R, raw_R))
        dist = np.asarray(assoc.get("distances_m", np.empty(0)))
        association_stats.append({
            "global_step": global_step, "object_fixation_index": len(gazes)-1,
            "input_points": int(len(p.xyz_h)), "matched": int(assoc.get("matched", 0)),
            "new": int(assoc.get("new", 0)), "empty_look": bool(empty),
            "overlap_median_distance_m": float(np.median(dist)) if len(dist) else None,
            "overlap_p95_distance_m": float(np.percentile(dist, 95)) if len(dist) else None,
            "idempotent_replay": bool(idempotent),
        })
        patch_stats.append({
            "global_step": global_step, "object_fixation_index": len(gazes)-1, "patch_id": pid,
            "yaw_deg": gaze[0], "pitch_deg": gaze[1], "point_count": int(len(p.xyz_h)),
            "empty_look": bool(empty),
        })
        decision = policy.choose_next(
            gaze[0], gaze[1], c,
            rec["instance_id"], rec["raw_support_L"], ids_R, raw_R,
            sm.xyz_h, gazes, history,
        )
        decision["object_fixation_index"] = len(gazes)-1
        decision["global_step"] = global_step
        policy_trace.append(decision)

    if set(np.unique(sm.instance_id).tolist()) != {public.OBJECT_ID_2}:
        raise AssertionError("final object-143 map is not pure")
    object2_path = args.out / "object_143_surface_map.npz"
    save_map(object2_path, sm)
    fsg6run.save_ply(args.out / "object_143_surface_map.ply", sm)
    fsg6run.write_growth(args.out / "object_143_growth.png", snapshots, supports, gazes)
    json_write(args.out / "object_143_policy_trace.json", {
        "policy": "frozen_fsg6f_via_id143_to_target_label_adapter", "trace": policy_trace,
    })

    chart, fp1, fp2 = _scene_chart(object1.xyz_h, sm.xyz_h, parent_public.GRID_DEG)
    np.savez_compressed(args.out / "scene_cyclopean_footprints.npz", object_141=fp1, object_143=fp2, **chart)
    _write_scene_png(args.out / "scene_cyclopean_footprints.png", fp1, fp2)
    scene = _scene_graph(
        args.parent, object1_source, object1_hash_before, len(object1.xyz_h),
        object2_path, len(sm.xyz_h), chart, fp1, fp2, len(gazes), termination,
    )
    json_write(args.out / "scene_graph.json", scene)

    parent_hash_after = {n: _sha256(args.parent / n) for n in parent_hash_before}
    object1_hash_after = _sha256(object1_source)
    if parent_hash_after != parent_hash_before:
        raise AssertionError("MultiObject-1a parent was modified")
    if object1_hash_after != object1_hash_before:
        raise AssertionError("object-141 geometry was modified")

    manifest = {
        "schema": public.SPEC_ID,
        "public_spec_sha256": public.public_digest(),
        "parent_spec": public.PARENT_SPEC_ID,
        "parent_record": str(args.parent),
        "parent_hashes": parent_hash_before,
        "seed": public.SEED,
        "profile": args.profile,
        "fixture": public.FIXTURE,
        "fixed_head": True,
        "static_scene": True,
        "truth_opened": False,
        "object_ids": list(public.OBJECT_IDS),
        "object_1_source": str(object1_source),
        "object_1_sha256_before": object1_hash_before,
        "object_1_sha256_after": object1_hash_after,
        "object_1_map_points": int(len(object1.xyz_h)),
        "object_1_read_only": True,
        "object_2_seed_points": int(len(p0.xyz_h)),
        "object_2_map_points": int(len(sm.xyz_h)),
        "object_2_map_pure": True,
        "object_2_fixation_gazes_deg": [list(map(float, g)) for g in gazes],
        "object_2_fixations_total": int(len(gazes)),
        "added_fixations": int(len(gazes) - 1),
        "parent_fixations_rerendered": 0,
        "empty_steps": empty_steps,
        "termination_reason": termination,
        "scientific_stop_reached": bool(termination != "object2_watchdog"),
        "watchdog_object2_fixations": public.OBJECT2_WATCHDOG_FIXATIONS,
        "policy_adapter": "id143_to_frozen_fsg6f_target_label",
        "policy_source_modified": False,
        "growth_history_starts_at_multiobject1a_seed": True,
        "patch_stats": patch_stats,
        "association_stats": association_stats,
        "scene_graph": "scene_graph.json",
        "scene_footprints": "scene_cyclopean_footprints.npz",
        "scene_footprint_overlap_cells": int((fp1 & fp2).sum()),
        "loop_wall_seconds": float(time.perf_counter() - t0),
        "automatic_object_discovery": False,
        "next_stage": "cyclopean completion for object 143; automatic next-object discovery remains deferred",
        "structural_fails": [],
    }
    json_write(args.out / "prediction_manifest.json", manifest)
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--parent", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", choices=("OPTIX", "CUDA", "CPU"), default="OPTIX")
    ap.add_argument("--blender", default="blender")
    m = execute(ap.parse_args())
    print("[multiobject1b-run] MULTIOBJECT1B_COMPLETE " + json.dumps({
        "object_1_map_points": m["object_1_map_points"],
        "object_2_seed_points": m["object_2_seed_points"],
        "object_2_map_points": m["object_2_map_points"],
        "object_2_fixations_total": m["object_2_fixations_total"],
        "added_fixations": m["added_fixations"],
        "empty_steps": m["empty_steps"],
        "termination_reason": m["termination_reason"],
        "footprint_overlap_cells": m["scene_footprint_overlap_cells"],
        "structural_fails": m["structural_fails"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
