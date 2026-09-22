"""Resume blocked MultiObject-1b object-143 growth with generic scene acquisition."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
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
from multiobject1b_run import _patch_from_record, _right_state, _seed_case, _sha256, _validate_parent
import multiobject1b2_public as public


def _tree_hashes(root: Path, rels: list[Path]) -> dict[str, str]:
    return {str(p): _sha256(root / p) for p in rels}


def _same_map(sm, saved_path: Path) -> bool:
    saved = load_map(saved_path)
    return bool(
        np.array_equal(np.asarray(sm.xyz_h, np.float32), saved.xyz_h)
        and np.array_equal(np.asarray(sm.rgb, np.float32), saved.rgb)
        and np.array_equal(sm.instance_id, saved.instance_id)
        and np.array_equal(sm.support_count, saved.support_count)
        and np.array_equal(sm.provenance_mask, saved.provenance_mask)
        and list(sm.patch_ids) == list(saved.patch_ids)
    )


def _partial_layout(partial: Path, seed_step: int) -> tuple[list[int], list[Path]]:
    if (partial / "prediction_manifest.json").exists():
        raise AssertionError("MultiObject-1b2 expects the blocked partial record, not a completed 1b manifest")
    map_steps = []
    map_rels = []
    for p in sorted((partial / "maps").glob("map_*.npz")):
        try:
            step = int(p.stem.split("_")[-1])
        except ValueError:
            continue
        map_steps.append(step)
        map_rels.append(p.relative_to(partial))
    expected = list(range(seed_step, public.LEGACY_LAST_GLOBAL_STEP + 1))
    if map_steps != expected:
        raise AssertionError(f"blocked 1b maps must be exactly steps {expected}, found {map_steps}")
    for step in expected[1:]:
        case = partial / "acquisitions" / f"fix_{step:02d}" / f"fix_{step:02d}"
        if not (case / "calibration.json").is_file() or not (case / "observation.npz").is_file():
            raise AssertionError(f"missing completed blocked acquisition step {step}")
    if (partial / "acquisitions" / f"fix_{public.RESUME_FIRST_GLOBAL_STEP:02d}" / f"fix_{public.RESUME_FIRST_GLOBAL_STEP:02d}" / "observation.npz").exists():
        raise AssertionError("partial record unexpectedly contains a completed step 24")
    return expected, map_rels


def _run_scene_blender(args, step: int, gaze: tuple[float, float], root: Path, log_name: str) -> Path:
    out = root / f"fix_{step:02d}"
    yaw, pitch = map(float, gaze)
    cmd = [
        args.blender, "-b", "--python-exit-code", "1",
        "-P", public.SCENE_RENDERER, "--",
        "--out", str(out), "--profile", args.profile, "--seed", str(public.SEED),
        "--step", str(step), "--yaw", f"{yaw:.12g}", "--pitch", f"{pitch:.12g}",
        "--device", args.device,
    ]
    p = subprocess.run(cmd, cwd=args.repo, text=True, capture_output=True)
    (args.out / "logs" / log_name).write_text(p.stdout + "\n--- STDERR ---\n" + p.stderr)
    if p.returncode != 0:
        raise RuntimeError(f"MultiObject-1b2 Blender fixation {step} failed; see {log_name}")
    rr = json.loads((out / "run.json").read_text())
    case = out / f"fix_{step:02d}"
    if not rr.get("complete") or int(rr.get("seed", -1)) != public.SEED:
        raise RuntimeError("incomplete or wrong generic scene acquisition")
    if int(rr.get("step", -1)) != step:
        raise RuntimeError("generic scene acquisition step mismatch")
    if abs(float(rr["yaw_deg"]) - yaw) > 1e-8 or abs(float(rr["pitch_deg"]) - pitch) > 1e-8:
        raise RuntimeError("generic scene acquisition gaze mismatch")
    return case


def _raw_observation(path: Path) -> dict[str, np.ndarray]:
    with np.load(path / "observation.npz", allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def _rgb_diagnostics(old: np.ndarray, new: np.ndarray) -> dict:
    if old.shape != new.shape:
        raise AssertionError(f"RGB shape changed: {old.shape} != {new.shape}")
    if old.dtype != new.dtype:
        raise AssertionError(f"RGB dtype changed: {old.dtype} != {new.dtype}")
    if not np.isfinite(old).all() or not np.isfinite(new).all():
        raise AssertionError("RGB equivalence diagnostic encountered non-finite values")
    delta = np.abs(old.astype(np.float64) - new.astype(np.float64))
    different = int(np.count_nonzero(old != new))
    return {
        "shape": list(old.shape),
        "dtype": str(old.dtype),
        "bitwise_equal": bool(different == 0),
        "different_elements": different,
        "different_fraction": float(different / old.size) if old.size else 0.0,
        "max_abs": float(delta.max()) if delta.size else 0.0,
        "mean_abs": float(delta.mean()) if delta.size else 0.0,
        "rms": float(np.sqrt(np.mean(delta * delta))) if delta.size else 0.0,
        "p99_abs": float(np.percentile(delta, 99)) if delta.size else 0.0,
    }


def _equivalence_acquisition_contract(case: Path) -> dict:
    a = json.loads((case / "acquisition.json").read_text())
    # These are physical/configuration quantities shared by the legacy and generic
    # entry points.  Schema/renderer labels and wall-time fields are intentionally
    # excluded because the entry point itself is the authorized plumbing change.
    fields = (
        "source", "fixture", "profile", "yaw_deg", "pitch_deg", "spp", "seeds_lr",
        "blender_version", "device", "primary_camera_samples", "nominal_camera_samples",
        "adaptive_sampling", "segmentation",
    )
    missing = [k for k in fields if k not in a]
    if missing:
        raise AssertionError(f"renderer acquisition metadata missing contract fields: {missing}")
    return {k: a[k] for k in fields}


def _verify_renderer_equivalence(args, old_case: Path, step: int, gaze: tuple[float, float]) -> dict:
    """Verify instrument identity without asking OPTIX radiance to be bit deterministic.

    The blocked first 1b2 run established that the frozen legacy renderer fails
    bit-exact RGB self-reproduction on this platform by the same ~ulp-scale as the
    generic renderer, while calibration and oracle masks remain exact.  Therefore
    this gate uses exact equality only where the instrument is deterministic and
    records RGB re-render differences as measurements with no epsilon or threshold.
    """
    eq_root = args.out / "renderer_equivalence"
    eq_root.mkdir()
    new_case = _run_scene_blender(args, step, gaze, eq_root, f"renderer_equivalence_{step:02d}.log")

    old_cal = json.loads((old_case / "calibration.json").read_text())
    new_cal = json.loads((new_case / "calibration.json").read_text())
    cal_equal = old_cal == new_cal
    if not cal_equal:
        raise AssertionError("generic scene renderer changed calibration")

    old_contract = _equivalence_acquisition_contract(old_case)
    new_contract = _equivalence_acquisition_contract(new_case)
    contract_equal = old_contract == new_contract
    if not contract_equal:
        differing = sorted(k for k in old_contract if old_contract[k] != new_contract[k])
        raise AssertionError(f"generic scene renderer changed deterministic acquisition contract: {differing}")

    old_obs = _raw_observation(old_case)
    new_obs = _raw_observation(new_case)
    keys_equal = set(old_obs) == set(new_obs)
    if not keys_equal:
        raise AssertionError(
            f"generic scene renderer changed observation keys: old={sorted(old_obs)} new={sorted(new_obs)}"
        )

    shape_dtype_exact = True
    for k in old_obs:
        if old_obs[k].shape != new_obs[k].shape or old_obs[k].dtype != new_obs[k].dtype:
            shape_dtype_exact = False
            break
    if not shape_dtype_exact:
        raise AssertionError("generic scene renderer changed observation shape or dtype")

    instance_keys = sorted(k for k in old_obs if k.startswith("instance_"))
    rgb_keys = sorted(k for k in old_obs if k.startswith("rgb_"))
    if instance_keys != ["instance_L", "instance_R"] or rgb_keys != ["rgb_L", "rgb_R"]:
        raise AssertionError(
            f"unexpected observation contract: instance={instance_keys} rgb={rgb_keys}"
        )

    instance_exact = {k: bool(np.array_equal(old_obs[k], new_obs[k])) for k in instance_keys}
    if not all(instance_exact.values()):
        raise AssertionError(f"generic scene renderer changed oracle instance masks: {instance_exact}")

    rgb = {k: _rgb_diagnostics(old_obs[k], new_obs[k]) for k in rgb_keys}

    return {
        "global_step": int(step),
        "gaze_deg": list(map(float, gaze)),
        "criterion_revision": "deterministic-instrument-contract-v2",
        "calibration_exact": True,
        "acquisition_contract_exact": True,
        "observation_keys_exact": True,
        "observation_shape_dtype_exact": True,
        "instance_arrays_exact": True,
        "instance_arrays": instance_exact,
        "rgb_is_diagnostic_not_gate": True,
        "rgb_tolerance_used": False,
        "rgb": rgb,
        "passed": True,
    }

def _patch_from_record143(pid: str, rec: dict) -> Patch:
    m = rec["valid"] & (rec["instance_id"] == public.OBJECT_ID_2)
    return Patch(pid, rec["xyz_h"][m], rec["rgb_left"][m], rec["instance_id"][m])


def _scene_graph(object1_source: Path, object1_hash: str, object1_points: int,
                 object2_path: Path, object2_points: int, chart: dict,
                 fp1: np.ndarray, fp2: np.ndarray, object2_fixations: int,
                 termination: str, partial: Path) -> dict:
    return {
        "schema": "MultiObject1b2-scene-graph-v1",
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
                "resume_source": str(partial),
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
    args.partial = Path(args.partial).resolve()
    args.out = Path(args.out).resolve()
    if args.out.exists():
        raise FileExistsError("output must be new")
    args.out.mkdir(parents=True)
    for d in ("logs", "acquisitions", "maps", "rgb"):
        (args.out / d).mkdir()

    check_kernel_equivalence()
    if public.FUSION != dict(frozen_public.FUSION):
        raise AssertionError("MultiObject-1b2 changed the frozen 12 mm fusion rule")

    pm, _parent_scene, object1_source = _validate_parent(args.parent)
    args.profile = str(pm.get("profile", "full"))
    object1_hash_before = _sha256(object1_source)
    object1 = load_map(object1_source)
    if set(np.unique(object1.instance_id).tolist()) != {public.OBJECT_ID_1}:
        raise AssertionError("inherited object-141 map is not pure")

    seed_step, seed_case = _seed_case(args.parent)
    if seed_step != 18:
        raise AssertionError(f"expected MultiObject-1a seed at global step 18, found {seed_step}")
    partial_steps, partial_map_rels = _partial_layout(args.partial, seed_step)
    parent_rels = [Path("prediction_manifest.json"), Path("scene_graph.json"), Path("object_143_seed_patch.npz")]
    parent_hash_before = _tree_hashes(args.parent, parent_rels)
    partial_key_rels = list(partial_map_rels)
    for step in partial_steps[1:]:
        partial_key_rels += [
            Path("acquisitions") / f"fix_{step:02d}" / "run.json",
            Path("acquisitions") / f"fix_{step:02d}" / f"fix_{step:02d}" / "calibration.json",
            Path("acquisitions") / f"fix_{step:02d}" / f"fix_{step:02d}" / "observation.npz",
        ]
    partial_hash_before = _tree_hashes(args.partial, partial_key_rels)

    c, obs = hdr.read_observation(seed_case)
    rec, _meta, state = compute_once(c, obs)
    ids_R, raw_R = _right_state(c, rec, state)
    p0 = _patch_from_record143(f"fix_{seed_step:02d}", rec)
    sm = initialize(p0, public.OBJECT_ID_2)
    if not _same_map(sm, args.partial / "maps" / f"map_{seed_step:02d}.npz"):
        raise AssertionError("blocked 1b seed map does not replay exactly")

    gazes = [tuple(map(float, pm["probe_gaze_deg"]))]
    history = [policy.history_entry(c, rec["instance_id"], rec["raw_support_L"], ids_R, raw_R)]
    snapshots = [sm.xyz_h.copy()]
    supports = [sm.support_count.copy()]
    patch_stats = [{
        "global_step": seed_step, "object_fixation_index": 0, "patch_id": f"fix_{seed_step:02d}",
        "yaw_deg": gazes[0][0], "pitch_deg": gazes[0][1], "point_count": int(len(p0.xyz_h)),
        "source": "MultiObject-1a prescribed seed",
    }]
    association_stats = [{
        "global_step": seed_step, "object_fixation_index": 0, "input_points": int(len(p0.xyz_h)),
        "matched": 0, "new": int(len(p0.xyz_h)), "empty_look": False, "idempotent_replay": True,
        "source": "reused blocked MultiObject-1b",
    }]
    policy_trace = []
    empty_steps: list[int] = []
    shutil.copy2(args.partial / "maps" / f"map_{seed_step:02d}.npz", args.out / "maps" / f"map_{seed_step:02d}.npz")

    decision = policy.choose_next(
        gazes[-1][0], gazes[-1][1], c,
        rec["instance_id"], rec["raw_support_L"], ids_R, raw_R,
        sm.xyz_h, gazes, history,
    )
    decision["object_fixation_index"] = 0
    decision["global_step"] = seed_step
    decision["source"] = "replayed blocked MultiObject-1b"
    policy_trace.append(decision)

    # Replay and verify every successful blocked growth fixation without rerendering.
    for step in partial_steps[1:]:
        if decision.get("stop"):
            raise AssertionError(f"blocked 1b contains step {step} after frozen policy already stopped")
        expected_gaze = tuple(map(float, decision["next_gaze_deg"]))
        run_path = args.partial / "acquisitions" / f"fix_{step:02d}" / "run.json"
        rr = json.loads(run_path.read_text())
        saved_gaze = (float(rr["yaw_deg"]), float(rr["pitch_deg"]))
        if not np.allclose(expected_gaze, saved_gaze, atol=1e-9):
            raise AssertionError(f"blocked step {step} gaze does not replay frozen policy")
        case = args.partial / "acquisitions" / f"fix_{step:02d}" / f"fix_{step:02d}"
        c, obs = hdr.read_observation(case)
        rec, _meta, state = compute_once(c, obs)
        ids_R, raw_R = _right_state(c, rec, state)
        pid = f"fix_{step:02d}"
        p = _patch_from_record143(pid, rec)
        empty = len(p.xyz_h) < public.MIN_TARGET_POINTS
        if empty:
            empty_steps.append(step)
            assoc = {"input_points": int(len(p.xyz_h)), "matched": 0, "new": 0, "distances_m": np.empty(0)}
            idempotent = True
        else:
            sm, assoc = fuse(sm, p, public.OBJECT_ID_2, public.FUSION["association_radius_m"], public.FUSION["hash_cell_m"])
            replay, dup = fuse(sm, p, public.OBJECT_ID_2, public.FUSION["association_radius_m"], public.FUSION["hash_cell_m"])
            idempotent = bool(
                dup["duplicate_patch"] and np.array_equal(sm.xyz_h, replay.xyz_h)
                and np.array_equal(sm.support_count, replay.support_count)
                and np.array_equal(sm.provenance_mask, replay.provenance_mask)
            )
        if not _same_map(sm, args.partial / "maps" / f"map_{step:02d}.npz"):
            raise AssertionError(f"blocked 1b map_{step:02d} does not replay exactly")
        if set(np.unique(sm.instance_id).tolist()) != {public.OBJECT_ID_2}:
            raise AssertionError("cross-object contamination in replayed object-143 map")
        shutil.copy2(args.partial / "maps" / f"map_{step:02d}.npz", args.out / "maps" / f"map_{step:02d}.npz")
        gazes.append(saved_gaze)
        history.append(policy.history_entry(c, rec["instance_id"], rec["raw_support_L"], ids_R, raw_R))
        snapshots.append(sm.xyz_h.copy())
        supports.append(sm.support_count.copy())
        dist = np.asarray(assoc.get("distances_m", np.empty(0)))
        association_stats.append({
            "global_step": step, "object_fixation_index": len(gazes)-1,
            "input_points": int(len(p.xyz_h)), "matched": int(assoc.get("matched", 0)),
            "new": int(assoc.get("new", 0)), "empty_look": bool(empty),
            "overlap_median_distance_m": float(np.median(dist)) if len(dist) else None,
            "overlap_p95_distance_m": float(np.percentile(dist, 95)) if len(dist) else None,
            "idempotent_replay": bool(idempotent), "source": "reused blocked MultiObject-1b",
        })
        patch_stats.append({
            "global_step": step, "object_fixation_index": len(gazes)-1, "patch_id": pid,
            "yaw_deg": saved_gaze[0], "pitch_deg": saved_gaze[1], "point_count": int(len(p.xyz_h)),
            "empty_look": bool(empty), "source": "reused blocked MultiObject-1b",
        })
        decision = policy.choose_next(
            saved_gaze[0], saved_gaze[1], c,
            rec["instance_id"], rec["raw_support_L"], ids_R, raw_R,
            sm.xyz_h, gazes, history,
        )
        decision["object_fixation_index"] = len(gazes)-1
        decision["global_step"] = step
        decision["source"] = "replayed blocked MultiObject-1b"
        policy_trace.append(decision)

    if partial_steps[-1] != public.LEGACY_LAST_GLOBAL_STEP:
        raise AssertionError("resume boundary changed")
    if decision.get("stop"):
        raise AssertionError("blocked state unexpectedly reaches policy stop before resume")

    last_case = args.partial / "acquisitions" / f"fix_{partial_steps[-1]:02d}" / f"fix_{partial_steps[-1]:02d}"
    equivalence = _verify_renderer_equivalence(args, last_case, partial_steps[-1], gazes[-1])

    resumed_from_points = int(len(sm.xyz_h))
    resumed_from_fixations = int(len(gazes))
    new_steps: list[int] = []
    t0 = time.perf_counter()
    termination = None

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
        if global_step < public.RESUME_FIRST_GLOBAL_STEP:
            raise AssertionError("new scene renderer attempted to rerender blocked history")
        case = _run_scene_blender(args, global_step, gaze, args.out / "acquisitions", f"render_{global_step:02d}.log")
        new_steps.append(global_step)
        c, obs = hdr.read_observation(case)
        rec, _meta, state = compute_once(c, obs)
        ids_R, raw_R = _right_state(c, rec, state)
        pid = f"fix_{global_step:02d}"
        p = _patch_from_record143(pid, rec)
        Image.fromarray(_tone_preview(rec["rgb_left"])).save(args.out / "rgb" / f"{pid}.png")

        empty = len(p.xyz_h) < public.MIN_TARGET_POINTS
        if empty:
            empty_steps.append(global_step)
            assoc = {"input_points": int(len(p.xyz_h)), "matched": 0, "new": 0, "distances_m": np.empty(0)}
            idempotent = True
        else:
            sm, assoc = fuse(sm, p, public.OBJECT_ID_2, public.FUSION["association_radius_m"], public.FUSION["hash_cell_m"])
            replay, dup = fuse(sm, p, public.OBJECT_ID_2, public.FUSION["association_radius_m"], public.FUSION["hash_cell_m"])
            idempotent = bool(
                dup["duplicate_patch"] and np.array_equal(sm.xyz_h, replay.xyz_h)
                and np.array_equal(sm.support_count, replay.support_count)
                and np.array_equal(sm.provenance_mask, replay.provenance_mask)
            )
            if not idempotent:
                raise AssertionError("object-143 resumed patch replay is not idempotent")
        if set(np.unique(sm.instance_id).tolist()) != {public.OBJECT_ID_2}:
            raise AssertionError("cross-object contamination entered resumed object-143 map")
        save_map(args.out / "maps" / f"map_{global_step:02d}.npz", sm)
        gazes.append(gaze)
        history.append(policy.history_entry(c, rec["instance_id"], rec["raw_support_L"], ids_R, raw_R))
        snapshots.append(sm.xyz_h.copy())
        supports.append(sm.support_count.copy())
        dist = np.asarray(assoc.get("distances_m", np.empty(0)))
        association_stats.append({
            "global_step": global_step, "object_fixation_index": len(gazes)-1,
            "input_points": int(len(p.xyz_h)), "matched": int(assoc.get("matched", 0)),
            "new": int(assoc.get("new", 0)), "empty_look": bool(empty),
            "overlap_median_distance_m": float(np.median(dist)) if len(dist) else None,
            "overlap_p95_distance_m": float(np.percentile(dist, 95)) if len(dist) else None,
            "idempotent_replay": bool(idempotent), "source": "generic scene renderer",
        })
        patch_stats.append({
            "global_step": global_step, "object_fixation_index": len(gazes)-1, "patch_id": pid,
            "yaw_deg": gaze[0], "pitch_deg": gaze[1], "point_count": int(len(p.xyz_h)),
            "empty_look": bool(empty), "source": "generic scene renderer",
        })
        decision = policy.choose_next(
            gaze[0], gaze[1], c,
            rec["instance_id"], rec["raw_support_L"], ids_R, raw_R,
            sm.xyz_h, gazes, history,
        )
        decision["object_fixation_index"] = len(gazes)-1
        decision["global_step"] = global_step
        decision["source"] = "generic scene renderer"
        policy_trace.append(decision)

    object2_path = args.out / "object_143_surface_map.npz"
    save_map(object2_path, sm)
    fsg6run.save_ply(args.out / "object_143_surface_map.ply", sm)
    fsg6run.write_growth(args.out / "object_143_growth.png", snapshots, supports, gazes)
    json_write(args.out / "object_143_policy_trace.json", {
        "policy": "frozen_fsg6f_via_existing_multiobject1b_adapter",
        "trace": policy_trace,
    })

    chart, fp1, fp2 = _scene_chart(object1.xyz_h, sm.xyz_h, parent_public.GRID_DEG)
    np.savez_compressed(args.out / "scene_cyclopean_footprints.npz", object_141=fp1, object_143=fp2, **chart)
    _write_scene_png(args.out / "scene_cyclopean_footprints.png", fp1, fp2)
    scene = _scene_graph(
        object1_source, object1_hash_before, len(object1.xyz_h), object2_path, len(sm.xyz_h),
        chart, fp1, fp2, len(gazes), termination, args.partial,
    )
    json_write(args.out / "scene_graph.json", scene)

    parent_hash_after = _tree_hashes(args.parent, parent_rels)
    partial_hash_after = _tree_hashes(args.partial, partial_key_rels)
    object1_hash_after = _sha256(object1_source)
    if parent_hash_after != parent_hash_before:
        raise AssertionError("MultiObject-1a parent was modified")
    if partial_hash_after != partial_hash_before:
        raise AssertionError("blocked MultiObject-1b partial record was modified")
    if object1_hash_after != object1_hash_before:
        raise AssertionError("object-141 geometry was modified")

    manifest = {
        "schema": public.SPEC_ID,
        "public_spec_sha256": public.public_digest(),
        "parent_spec": public.PARENT_SPEC_ID,
        "parent_record": str(args.parent),
        "partial_record": str(args.partial),
        "parent_hashes": parent_hash_before,
        "partial_key_hashes": partial_hash_before,
        "seed": public.SEED,
        "profile": args.profile,
        "fixture": public.FIXTURE,
        "fixed_head": True,
        "static_scene": True,
        "truth_opened": False,
        "object_ids": list(public.OBJECT_IDS),
        "renderer_entrypoint": public.SCENE_RENDERER,
        "renderer_equivalence": equivalence,
        "reused_global_steps": partial_steps,
        "reused_partial_fixations_total": resumed_from_fixations,
        "new_global_steps": new_steps,
        "global_history_renumbered": False,
        "object_1_source": str(object1_source),
        "object_1_sha256_before": object1_hash_before,
        "object_1_sha256_after": object1_hash_after,
        "object_1_map_points": int(len(object1.xyz_h)),
        "object_1_read_only": True,
        "object_2_resume_points": resumed_from_points,
        "object_2_map_points": int(len(sm.xyz_h)),
        "object_2_map_pure": True,
        "object_2_fixation_gazes_deg": [list(map(float, g)) for g in gazes],
        "object_2_fixations_total": int(len(gazes)),
        "added_fixations": int(len(new_steps)),
        "partial_fixations_rerendered": 0,
        "empty_steps": empty_steps,
        "termination_reason": termination,
        "scientific_stop_reached": bool(termination != "object2_watchdog"),
        "watchdog_object2_fixations": public.OBJECT2_WATCHDOG_FIXATIONS,
        "policy_adapter": "reuse unchanged multiobject1b_policy id143_to_frozen_fsg6f_target_label",
        "policy_source_modified": False,
        "patch_stats": patch_stats,
        "association_stats": association_stats,
        "scene_graph": "scene_graph.json",
        "scene_footprints": "scene_cyclopean_footprints.npz",
        "scene_footprint_overlap_cells": int((fp1 & fp2).sum()),
        "loop_wall_seconds_after_resume": float(time.perf_counter() - t0),
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
    ap.add_argument("--partial", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", choices=("OPTIX", "CUDA", "CPU"), default="OPTIX")
    ap.add_argument("--blender", default="blender")
    m = execute(ap.parse_args())
    print("[multiobject1b2-run] MULTIOBJECT1B2_COMPLETE " + json.dumps({
        "object_1_map_points": m["object_1_map_points"],
        "object_2_resume_points": m["object_2_resume_points"],
        "object_2_map_points": m["object_2_map_points"],
        "reused_global_steps": m["reused_global_steps"],
        "new_global_steps": m["new_global_steps"],
        "object_2_fixations_total": m["object_2_fixations_total"],
        "empty_steps": m["empty_steps"],
        "termination_reason": m["termination_reason"],
        "scientific_stop_reached": m["scientific_stop_reached"],
        "renderer_equivalence": m["renderer_equivalence"]["passed"],
        "footprint_overlap_cells": m["scene_footprint_overlap_cells"],
        "structural_fails": m["structural_fails"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
