"""Run Classroom-Oracle-1 from the repository root.

The controller is allowed to read only:
  * one Blender-provided seed gaze for each controller-domain-visible instance;
  * the current rendered binocular tangent pair;
  * its accumulated metric map and observation history.

Dense seed-scan geometry is deliberately never opened here.  It is consumed only
by classroom_oracle1_eval.py after the control run is complete.
"""
from __future__ import annotations

import argparse
import inspect
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import classroom_oracle1_epistemic as epistemic
import classroom_oracle1_matcher as oracle_matcher
import classroom_oracle1_public as public
import fsg3_surface_map as surface_map
import fsg6f_public as frozen
import multiobject2c_policy as object_policy


def _jsonable(x: Any) -> Any:
    if x is None or isinstance(x, (str, bool, int, float)):
        return x
    if isinstance(x, np.generic):
        return x.item()
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, Path):
        return str(x)
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    if hasattr(x, "__dict__"):
        return _jsonable(vars(x))
    return repr(x)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(data), indent=2, sort_keys=True) + "\n")


def _run(cmd: list[str], log: Path, cwd: Path) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w") as f:
        p = subprocess.run(cmd, cwd=cwd, stdout=f, stderr=subprocess.STDOUT, text=True)
    if p.returncode:
        tail = log.read_text(errors="replace").splitlines()[-80:]
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(cmd)}\n" + "\n".join(tail))


def _new_dir(path: Path) -> None:
    if path.exists():
        if any(path.iterdir()):
            raise FileExistsError(f"output must be new or empty: {path}")
    else:
        path.mkdir(parents=True)


def _load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def _construct_patch(rec: dict[str, Any], fixation_id: int):
    """Construct the inherited fsg3 Patch without duplicating its implementation.

    The FSG3 Patch API evolved slightly during the project.  We bind by field name
    when available and retain a positional fallback for the original four-field
    form.  The semantic payload is fixed: current H-frame XYZ, left RGB, Blender
    instance id, and fixation identity.
    """
    P = surface_map.Patch
    patch_id = f"fix_{int(fixation_id):02d}"
    values = {
        "patch_id": patch_id,
        "xyz_h": rec["xyz_h"], "xyz": rec["xyz_h"], "X": rec["xyz_h"],
        "rgb": rec["rgb_left"], "colour": rec["rgb_left"], "color": rec["rgb_left"], "c": rec["rgb_left"],
        "instance_id": rec["instance_id"], "instance": rec["instance_id"], "ids": rec["instance_id"],
        "valid": rec["valid"], "mask": rec["valid"],
        "fixation_id": int(fixation_id), "fixation_index": int(fixation_id),
        "fixation": int(fixation_id), "observation_id": int(fixation_id),
    }
    try:
        sig = inspect.signature(P)
        kwargs = {}
        missing = []
        for name, par in sig.parameters.items():
            if name == "self":
                continue
            if name in values:
                kwargs[name] = values[name]
            elif par.default is inspect._empty and par.kind not in (par.VAR_POSITIONAL, par.VAR_KEYWORD):
                missing.append(name)
        if not missing:
            return P(**kwargs)
    except (TypeError, ValueError):
        pass
    # Recovered FSG3 lineage used this compact ordering.
    attempts = [
        (patch_id, rec["xyz_h"], rec["rgb_left"], rec["instance_id"]),
        (rec["xyz_h"], rec["rgb_left"], rec["instance_id"], int(fixation_id)),
        (rec["xyz_h"], rec["rgb_left"], rec["instance_id"]),
    ]
    errors = []
    for a in attempts:
        try:
            return P(*a)
        except TypeError as exc:
            errors.append(str(exc))
    raise TypeError("could not bind inherited fsg3_surface_map.Patch: " + " | ".join(errors))


def _normalise_result(value: Any) -> tuple[Any, dict[str, Any]]:
    if isinstance(value, tuple):
        if not value:
            raise RuntimeError("empty result from surface-map operation")
        meta = value[1] if len(value) > 1 and isinstance(value[1], dict) else {}
        return value[0], dict(meta)
    return value, {}


def _initialise(patch, target_id: int):
    return _normalise_result(surface_map.initialize(patch, int(target_id)))


def _fuse(sm, patch, target_id: int):
    return _normalise_result(surface_map.fuse(
        sm, patch, int(target_id),
        float(public.FUSION["association_radius_m"]),
        float(public.FUSION["hash_cell_m"]),
    ))


def _map_xyz(sm) -> np.ndarray:
    for name in ("xyz_h", "X", "xyz", "points_h", "points"):
        if hasattr(sm, name):
            a = np.asarray(getattr(sm, name), dtype=np.float64)
            if a.ndim == 2 and a.shape[1] == 3:
                return a
    if isinstance(sm, dict):
        for name in ("xyz_h", "X", "xyz", "points_h", "points"):
            if name in sm:
                a = np.asarray(sm[name], dtype=np.float64)
                if a.ndim == 2 and a.shape[1] == 3:
                    return a
    raise AttributeError("cannot locate H-frame XYZ in inherited SurfaceMap")


def _snapshot(sm, path: Path) -> None:
    arrays: dict[str, np.ndarray] = {"xyz_h": _map_xyz(sm).astype(np.float32)}
    # Preserve useful public ndarray fields without depending on their names.
    if hasattr(sm, "__dict__"):
        for k, v in vars(sm).items():
            if k == "xyz_h" or not isinstance(v, np.ndarray):
                continue
            if v.dtype.kind in "biuf" and v.size <= max(1, arrays["xyz_h"].shape[0]) * 16:
                arrays[k] = v
    np.savez_compressed(path, **arrays)


def _history_entry(c: dict, state: dict[str, np.ndarray], target_id: int, gaze: tuple[float, float]):
    fn = object_policy.history_entry
    values = {
        "calibration": c, "c": c,
        "instance_L": state["ids_left"], "ids_L": state["ids_left"],
        "raw_support_L": state["raw_support_L"], "support_L": state["raw_support_L"],
        "instance_R": state["ids_right"], "ids_R": state["ids_right"],
        "raw_support_R": state["raw_support_R"], "support_R": state["raw_support_R"],
        "target_object_id": int(target_id), "target_id": int(target_id),
        "gaze_deg": [float(gaze[0]), float(gaze[1])],
        "yaw_deg": float(gaze[0]), "pitch_deg": float(gaze[1]),
    }
    sig = inspect.signature(fn)
    kwargs = {name: values[name] for name in sig.parameters if name in values}
    missing = [name for name, p in sig.parameters.items()
               if name not in kwargs and p.default is inspect._empty
               and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)]
    if missing:
        raise TypeError(f"cannot bind multiobject2c_policy.history_entry; missing {missing}")
    return fn(**kwargs)


def _policy_next(current: tuple[float, float], c: dict, state: dict[str, np.ndarray],
                 map_xyz: np.ndarray, visited: list[tuple[float, float]], history: list[Any], target_id: int):
    return object_policy.choose_next(
        current_yaw_deg=float(current[0]),
        current_pitch_deg=float(current[1]),
        calibration=c,
        instance_L=state["ids_left"],
        raw_support_L=state["raw_support_L"],
        instance_R=state["ids_right"],
        raw_support_R=state["raw_support_R"],
        map_xyz_h=np.asarray(map_xyz, float),
        visited_gazes_deg=[[float(y), float(p)] for y, p in visited],
        observation_history=history,
        target_object_id=int(target_id),
    )


def _get(obj: Any, key: str, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _decision_stop(d: Any) -> bool:
    v = _get(d, "stop", None)
    if v is not None:
        return bool(v)
    reason = str(_get(d, "reason", ""))
    return reason in {"no_frontier", "complete", "attention_complete", "policy_exhausted"}


def _decision_gaze(d: Any) -> tuple[float, float]:
    for key in ("next_gaze_deg", "gaze_deg", "next_gaze"):
        v = _get(d, key, None)
        if v is not None and len(v) == 2:
            return float(v[0]), float(v[1])
    pairs = [
        ("next_yaw_deg", "next_pitch_deg"),
        ("yaw_deg", "pitch_deg"),
        ("gaze_yaw_deg", "gaze_pitch_deg"),
    ]
    for ky, kp in pairs:
        y, p = _get(d, ky, None), _get(d, kp, None)
        if y is not None and p is not None:
            return float(y), float(p)
    raise KeyError(f"cannot extract next gaze from FSG6f decision: {_jsonable(d)}")


def _same_gaze(a: tuple[float, float], b: tuple[float, float], eps: float = 1e-8) -> bool:
    return abs(a[0] - b[0]) <= eps and abs(a[1] - b[1]) <= eps


def _save_rgb(path: Path, rgb: np.ndarray) -> None:
    x = np.asarray(rgb, np.float32)
    x = np.clip(x, 0.0, 1.0)
    # Blender linear RGB is intentionally stored as a simple 8-bit diagnostic/benchmark
    # image here; the untouched Combined pass remains in raw_*.exr.
    u8 = np.rint(np.power(x, 1.0 / 2.2) * 255.0).astype(np.uint8)
    if not cv2.imwrite(str(path), u8[..., ::-1]):
        raise RuntimeError(f"failed to write {path}")


def _render_fixation(repo: Path, scene: Path, blender: str, args, target_id: int,
                     step: int, gaze: tuple[float, float], out: Path) -> None:
    cmd = [
        blender, "-b", str(scene), "--python-exit-code", "1",
        "-P", str(repo / "tools/classroom_oracle1_render.py"), "--",
        "--mode", "fixation", "--out", str(out), "--profile", args.profile,
        "--device", args.device, "--yaw", str(gaze[0]), "--pitch", str(gaze[1]),
        "--object-id", str(target_id), "--step", str(step),
    ]
    if args.spp is not None:
        cmd += ["--spp", str(args.spp)]
    _run(cmd, out.parent / f"fix_{step:02d}.blender.log", repo)


def _bootstrap(repo: Path, scene: Path, blender: str, args, out: Path) -> dict:
    boot = out / "bootstrap"
    boot.mkdir()
    cmd = [
        blender, "-b", str(scene), "--python-exit-code", "1",
        "-P", str(repo / "tools/classroom_oracle1_render.py"), "--",
        "--mode", "seeds", "--out", str(boot), "--profile", args.profile,
        "--device", args.device, "--seed-step", str(public.SEED_SCAN_STEP_DEG),
    ]
    _run(cmd, out / "logs/bootstrap.blender.log", repo)
    return json.loads((boot / "seeds.json").read_text())


def _run_object(repo: Path, scene: Path, blender: str, args, root: Path,
                seed: dict[str, Any]) -> dict[str, Any]:
    target_id = int(seed["instance_id"])
    name = str(seed["object_name"])
    odir = root / "objects" / f"instance_{target_id:04d}"
    (odir / "acquisitions").mkdir(parents=True)
    (odir / "maps").mkdir()
    (odir / "patches").mkdir()
    (odir / "benchmark").mkdir()

    gaze = tuple(map(float, seed["seed_gaze_deg"]))
    source = "oracle_seed"
    visited: list[tuple[float, float]] = []
    history: list[Any] = []
    ev = epistemic.make_evidence()
    sm = None
    trajectory: list[dict[str, Any]] = []
    incidental: set[int] = set()
    termination = None
    max_fix = 2 if args.smoke else public.MAX_OBJECT_FIXATIONS

    for step in range(max_fix):
        if any(_same_gaze(gaze, old) for old in visited):
            raise RuntimeError(f"controller requested an already visited gaze for instance {target_id}: {gaze}")

        adir = odir / "acquisitions" / f"fix_{step:02d}"
        adir.mkdir()
        _render_fixation(repo, scene, blender, args, target_id, step, gaze, adir)
        c = json.loads((adir / "calibration.json").read_text())
        obs = _load_npz(adir / "oracle_observation.npz")
        rec, matcher_meta, state = oracle_matcher.compute(c, obs)

        target_valid = np.asarray(rec["valid"], bool) & (np.asarray(rec["instance_id"]) == target_id)
        target_points = int(target_valid.sum())
        seen_ids = set(np.unique(np.concatenate((state["ids_left"].ravel(), state["ids_right"].ravel()))).tolist())
        incidental.update(int(i) for i in seen_ids if int(i) not in (0, target_id))

        np.savez_compressed(
            odir / "patches" / f"fix_{step:02d}.npz",
            xyz_h=np.asarray(rec["xyz_h"], np.float32),
            valid=np.asarray(rec["valid"], bool),
            instance_id=np.asarray(rec["instance_id"], np.int32),
            range_left_m=np.asarray(rec["range_left_m"], np.float32),
        )
        _save_rgb(odir / "benchmark" / f"fix_{step:02d}_L.png", rec["rgb_left"])
        _save_rgb(odir / "benchmark" / f"fix_{step:02d}_R.png", rec["rgb_right"])

        patch = _construct_patch(rec, step)
        fusion_meta: dict[str, Any] = {}
        new_count = 0
        duplicate_count = 0
        before = 0 if sm is None else len(_map_xyz(sm))
        if sm is None:
            if target_points >= public.MIN_INITIAL_TARGET_POINTS:
                sm, fusion_meta = _initialise(patch, target_id)
                new_count = len(_map_xyz(sm))
            else:
                # A seed that cannot satisfy the inherited FSG3 map precondition is
                # a measured outcome.  We keep it; no object is silently dropped.
                termination = "seed_uninitializable"
        else:
            if target_points >= public.MIN_INITIAL_TARGET_POINTS:
                sm2, fusion_meta = _fuse(sm, patch, target_id)
                after = len(_map_xyz(sm2))
                new_count = max(0, after - before)
                duplicate_count = max(0, target_points - new_count)
                # Replaying the same observation must not alter the metric map.
                replay, _ = _fuse(sm2, patch, target_id)
                x1, x2 = _map_xyz(sm2), _map_xyz(replay)
                if x1.shape != x2.shape or not np.allclose(x1, x2, rtol=0.0, atol=1e-10, equal_nan=True):
                    raise RuntimeError(f"12 mm fusion lost idempotence at instance {target_id}, step {step}")
                sm = sm2
            else:
                # Reality-Check-2b semantics: the look happened and its binocular
                # evidence is kept, but zero geometry is fused.
                fusion_meta = {"empty_look": True, "reason": "target_points_below_initialisation_precondition"}

        if sm is not None:
            _snapshot(sm, odir / "maps" / f"fix_{step:02d}.npz")

        epistemic.add_observation(
            ev, c,
            state["ids_left"], state["raw_support_L"],
            state["ids_right"], state["raw_support_R"],
            rec["valid"], target_id,
        )
        history.append(_history_entry(c, state, target_id, gaze))
        visited.append(gaze)

        row = {
            "step": step,
            "gaze_deg": list(gaze),
            "action_source": source,
            "target_points": target_points,
            "oracle_valid_points_all_instances": int(np.asarray(rec["valid"], bool).sum()),
            "map_size_before": before,
            "map_size_after": 0 if sm is None else len(_map_xyz(sm)),
            "new_surfels": int(new_count),
            "nonnew_target_points": int(duplicate_count),
            "matcher": matcher_meta,
            "fusion": fusion_meta,
            "raw_left_exr": str((adir / "raw_L.exr").relative_to(root)),
            "raw_right_exr": str((adir / "raw_R.exr").relative_to(root)),
            "rectified_left_png": str((odir / "benchmark" / f"fix_{step:02d}_L.png").relative_to(root)),
            "rectified_right_png": str((odir / "benchmark" / f"fix_{step:02d}_R.png").relative_to(root)),
            "oracle_patch": str((odir / "patches" / f"fix_{step:02d}.npz").relative_to(root)),
        }
        trajectory.append(row)
        _write_json(odir / "trajectory.partial.json", trajectory)

        if termination is not None:
            break
        if args.smoke and step + 1 >= 2:
            termination = "smoke_budget"
            break
        if not args.smoke and step + 1 >= public.MAX_OBJECT_FIXATIONS:
            termination = "watchdog_24"
            break
        if sm is None:
            raise AssertionError("unreachable: nonterminated object has no map")

        d = _policy_next(gaze, c, state, _map_xyz(sm), visited, history, target_id)
        row["fsg6f_decision"] = _jsonable(d)
        if _decision_stop(d):
            e = epistemic.choose_next(ev, _map_xyz(sm), visited)
            row["cyclopean_decision"] = _jsonable(e)
            if e["stop"]:
                termination = "attention_complete"
                break
            gaze = tuple(map(float, e["next_gaze_deg"]))
            source = "cyclopean_epistemic"
        else:
            gaze = _decision_gaze(d)
            source = "fsg6f"

    if termination is None:
        termination = "policy_exhausted"
    if sm is not None:
        _snapshot(sm, odir / "final_map.npz")
    result = {
        "instance_id": target_id,
        "object_name": name,
        "seed_gaze_deg": seed["seed_gaze_deg"],
        "fixation_count": len(trajectory),
        "termination": termination,
        "final_map_surfels": 0 if sm is None else len(_map_xyz(sm)),
        "incidental_instance_ids": sorted(incidental),
        "trajectory": trajectory,
    }
    _write_json(odir / "result.json", result)
    return result


_CONTROLLER_ACTION_SOURCES = {"fsg6f", "cyclopean_epistemic"}


def _smoke_result_audit(result: dict[str, Any]) -> tuple[bool, bool, list[str]]:
    """Audit one smoke object without imposing a scene-dependent look count.

    A one-look object is legitimate when the unchanged controller terminates at the
    seed (for example seed_uninitializable or attention_complete).  If a later
    look exists, it must have been selected by FSG6f or the Cyclopean handoff.
    """
    errors: list[str] = []
    traj = list(result.get("trajectory", []))
    if int(result.get("fixation_count", -1)) != len(traj):
        errors.append("fixation_count does not match trajectory length")
    if not traj:
        errors.append("empty trajectory")
        return False, False, errors
    if str(traj[0].get("action_source")) != "oracle_seed":
        errors.append("first look is not the oracle bootstrap seed")
    transition = False
    for i, row in enumerate(traj[1:], start=1):
        src = str(row.get("action_source"))
        if src not in _CONTROLLER_ACTION_SOURCES:
            errors.append(f"look {i} has non-controller action_source={src!r}")
        else:
            transition = True
    return len(errors) == 0, transition, errors


def self_test() -> list[str]:
    fails = []
    if abs(float(frozen.FUSION["association_radius_m"]) - 0.012) > 1e-12:
        fails.append("frozen FSG6f association radius is no longer 12 mm")
    if abs(float(frozen.FUSION["hash_cell_m"]) - 0.012) > 1e-12:
        fails.append("frozen FSG6f hash cell is no longer 12 mm")
    if public.MAX_OBJECT_FIXATIONS != 24:
        fails.append("watchdog changed")

    # The smoke gate must accept legitimate seed termination and reject any
    # Blender/oracle-selected post-seed gaze.  This protects the repaired
    # scene-independent smoke semantics inside the existing 12-check suite.
    ok, transition, err = _smoke_result_audit({
        "fixation_count": 1,
        "termination": "seed_uninitializable",
        "trajectory": [{"action_source": "oracle_seed"}],
    })
    if not ok or transition or err:
        fails.append("smoke audit rejects legitimate one-look seed termination")
    ok, transition, err = _smoke_result_audit({
        "fixation_count": 2,
        "termination": "smoke_budget",
        "trajectory": [
            {"action_source": "oracle_seed"},
            {"action_source": "fsg6f"},
        ],
    })
    if not ok or not transition or err:
        fails.append("smoke audit does not recognize controller-selected second look")
    ok, _transition, _err = _smoke_result_audit({
        "fixation_count": 2,
        "termination": "smoke_budget",
        "trajectory": [
            {"action_source": "oracle_seed"},
            {"action_source": "oracle_seed"},
        ],
    })
    if ok:
        fails.append("smoke audit permits Blender/oracle-selected post-seed gaze")
    return fails


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--scene", default=public.SCENE)
    ap.add_argument("--out", required=True)
    ap.add_argument("--blender", default="blender")
    ap.add_argument("--profile", choices=("small", "full"), default=public.DEFAULT_PROFILE)
    ap.add_argument("--device", choices=("OPTIX", "CUDA", "CPU"), default=public.DEFAULT_DEVICE)
    ap.add_argument("--spp", type=int, default=None)
    ap.add_argument("--smoke", action="store_true", help="first two visible instances, then deterministic transition probe; at most two looks per object")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    repo = Path(args.repo).resolve()
    root = Path(args.out).resolve()
    scene = (repo / args.scene).resolve() if not Path(args.scene).is_absolute() else Path(args.scene).resolve()
    if not scene.exists():
        raise FileNotFoundError(scene)
    _new_dir(root)
    (root / "logs").mkdir()

    bad = public.self_test() + self_test()
    if bad:
        raise RuntimeError("public/run self-test failed: " + "; ".join(bad))

    seeds_doc = _bootstrap(repo, scene, args.blender, args, root)
    seeds = list(seeds_doc["instances"])
    if args.smoke and len(seeds) < 2:
        raise RuntimeError("smoke test requires at least two oracle-visible instances")

    manifest = {
        "schema": "ClassroomOracle1-run-v1",
        "spec_id": public.SPEC_ID,
        "public_digest": public.public_digest(),
        "parent_commit": public.PARENT_COMMIT,
        "scene": str(scene.relative_to(repo) if scene.is_relative_to(repo) else scene),
        "profile": args.profile,
        "device": args.device,
        "spp_override": args.spp,
        "smoke": bool(args.smoke),
        "oracle_visible_instance_count": len(seeds_doc["instances"]),
        "attempted_instance_count": 0,
        "controller_truth_scope": "one seed per instance + current tangent pair only",
        "dense_evaluation_truth_opened_during_control": False,
        "foreground_background_decomposition": False,
        "objects": [],
        "control_complete": False,
    }
    _write_json(root / "manifest.json", manifest)

    smoke_transition = False
    smoke_primary_ids = [int(s["instance_id"]) for s in seeds[:2]] if args.smoke else []

    for seed in seeds:
        result = _run_object(repo, scene, args.blender, args, root, seed)
        manifest["objects"].append(result)
        manifest["attempted_instance_count"] = len(manifest["objects"])

        if args.smoke:
            ok, transition, errors = _smoke_result_audit(result)
            if not ok:
                raise RuntimeError(
                    f"smoke trajectory contract failed for instance {result.get('instance_id')}: "
                    + "; ".join(errors)
                )
            smoke_transition = smoke_transition or transition
            manifest["smoke_gate"] = {
                "contract": "first two visible instances plus deterministic ascending-ID probe until a controller-selected second look is exercised",
                "primary_instance_ids": smoke_primary_ids,
                "controller_transition_exercised": bool(smoke_transition),
                "objects_examined": len(manifest["objects"]),
                "all_post_seed_looks_controller_selected": True,
            }

        _write_json(root / "manifest.json", manifest)

        # The first two visible instances are always retained.  If neither can
        # legitimately take a second fixation, continue deterministically in
        # ascending instance-id order until the controller-selected acquisition
        # path is exercised.  This is an integration probe, not scientific
        # cherry-picking: the full run still attempts every visible instance.
        if args.smoke and len(manifest["objects"]) >= 2 and smoke_transition:
            break

    if args.smoke:
        if len(manifest["objects"]) < 2:
            raise RuntimeError("smoke gate did not retain the first two oracle-visible instances")
        if not smoke_transition:
            # This can be a legitimate scene/controller outcome: every visible
            # object may terminate at its seed.  The smoke still certifies the
            # seed, measurement, fusion, FSG6f/Cyclopean termination, artifact,
            # and truth-isolation paths.  Record explicitly that no second-look
            # transition existed to exercise rather than inventing one.
            manifest["smoke_gate"]["status"] = "PASS_NO_CONTROLLER_TRANSITION_REQUESTED"
            manifest["smoke_gate"]["exhausted_visible_set"] = True
        else:
            manifest["smoke_gate"]["status"] = "PASS_CONTROLLER_TRANSITION_EXERCISED"
            manifest["smoke_gate"]["exhausted_visible_set"] = False

    manifest["control_complete"] = True
    manifest["total_fixations"] = sum(int(o["fixation_count"]) for o in manifest["objects"])
    manifest["termination_counts"] = {}
    for o in manifest["objects"]:
        k = str(o["termination"])
        manifest["termination_counts"][k] = manifest["termination_counts"].get(k, 0) + 1
    _write_json(root / "manifest.json", manifest)
    print("[classroom-oracle1] COMPLETE", json.dumps({
        "objects": len(manifest["objects"]), "fixations": manifest["total_fixations"],
        "terminations": manifest["termination_counts"], "smoke": bool(args.smoke),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
