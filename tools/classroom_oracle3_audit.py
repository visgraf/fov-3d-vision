"""Read-only eligibility audit for Classroom-Oracle-3.

The program has two deliberately separated phases:

1. Controller replay phase: rebuild every Oracle-1 object's final observation
   history, replay the frozen FSG6f decision, reconstruct the Cyclopean chart,
   and save only controller-derived masks and diagnostics.  Dense evaluation
   truth is not opened in this phase.
2. Truth audit phase: after every controller replay succeeded, open the frozen
   Oracle-1 reachable-surface reference and classify each reachable-but-uncovered
   sample by the first Cyclopean eligibility rule that excludes its angular cell.

No Blender process is launched and no acquisition or fusion is performed.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import inspect
import json
import math
from pathlib import Path
import sys
import types
from typing import Any, Callable

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import classroom_oracle3_public as public
import classroom_oracle1_epistemic as epistemic
import classroom_oracle1_matcher as oracle_matcher
import multiobject2c_policy as object_policy


def _json(path: Path) -> Any:
    return json.loads(path.read_text())


def _jsonable(x: Any, depth: int = 0) -> Any:
    if x is None or isinstance(x, (str, bool, int, float)):
        return x
    if isinstance(x, np.generic):
        return x.item()
    if isinstance(x, Path):
        return str(x)
    if isinstance(x, np.ndarray):
        a = np.asarray(x)
        if a.size <= 24:
            return a.tolist()
        out: dict[str, Any] = {"shape": list(a.shape), "dtype": str(a.dtype), "size": int(a.size)}
        if a.dtype.kind == "b":
            out["true"] = int(a.sum())
        elif a.dtype.kind in "iu":
            out["min"] = int(a.min()) if a.size else None
            out["max"] = int(a.max()) if a.size else None
        elif a.dtype.kind == "f":
            finite = np.isfinite(a)
            out["finite"] = int(finite.sum())
            if finite.any():
                out["min"] = float(np.nanmin(a))
                out["max"] = float(np.nanmax(a))
        return out
    if depth >= 4:
        return repr(x)
    if isinstance(x, dict):
        return {str(k): _jsonable(v, depth + 1) for k, v in list(x.items())[:80]}
    if isinstance(x, (list, tuple)):
        if len(x) > 40:
            return {"length": len(x), "head": [_jsonable(v, depth + 1) for v in x[:12]]}
        return [_jsonable(v, depth + 1) for v in x]
    if hasattr(x, "__dict__"):
        return _jsonable(vars(x), depth + 1)
    return repr(x)


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(value), indent=2, sort_keys=True) + "\n")


def _new_dir(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        raise FileExistsError(f"output must be new or empty: {path}")
    path.mkdir(parents=True, exist_ok=True)


def _sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def _load_map(path: Path) -> np.ndarray:
    if not path.exists():
        return np.empty((0, 3), np.float64)
    with np.load(path, allow_pickle=False) as z:
        x = np.asarray(z["xyz_h"], np.float64)
    if x.ndim != 2 or x.shape[1] != 3:
        raise ValueError(f"bad map XYZ in {path}: {x.shape}")
    return x[np.isfinite(x).all(axis=1)]


def _make_evidence(bounds: dict[str, float]) -> epistemic.Evidence:
    g = float(public.CYCLOPEAN_GRID_DEG)
    y0 = float(bounds["yaw_min_deg"])
    y1 = float(bounds["yaw_max_deg"])
    p0 = float(bounds["pitch_min_deg"])
    p1 = float(bounds["pitch_max_deg"])
    w = int(round((y1 - y0) / g)) + 1
    h = int(round((p1 - p0) / g)) + 1
    z = np.zeros((h, w), bool)
    return epistemic.Evidence(y0, y1, p0, p1, g, z.copy(), z.copy(), z.copy(), z.copy())


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


def _policy_kwargs(current: tuple[float, float], c: dict, state: dict[str, np.ndarray],
                   map_xyz: np.ndarray, visited: list[tuple[float, float]], history: list[Any],
                   target_id: int) -> dict[str, Any]:
    return {
        "current_yaw_deg": float(current[0]),
        "current_pitch_deg": float(current[1]),
        "calibration": c,
        "instance_L": state["ids_left"],
        "raw_support_L": state["raw_support_L"],
        "instance_R": state["ids_right"],
        "raw_support_R": state["raw_support_R"],
        "map_xyz_h": np.asarray(map_xyz, float),
        "visited_gazes_deg": [[float(y), float(p)] for y, p in visited],
        "observation_history": history,
        "target_object_id": int(target_id),
    }


def _get(obj: Any, key: str, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _decision_summary(d: Any) -> dict[str, Any]:
    keys = (
        "stop", "reason", "next_gaze_deg", "current_gaze_deg",
        "frontier_voxel_count", "frontier_count", "raw_frontier_count",
        "frontier_raw_count", "frontier_open_count",
        "frontier_map_resolved_count", "frontier_boundary_resolved_count",
        "candidates_before_consensus_count", "consensus_rejected_candidate_count",
        "frontier_state_radius_m",
    )
    out = {k: _jsonable(_get(d, k)) for k in keys if _get(d, k, None) is not None}
    if "frontier_count" not in out:
        for k in ("raw_frontier_count", "frontier_raw_count"):
            if k in out:
                out["frontier_count"] = out[k]
                break
    return out


def _number(d: dict[str, Any], key: str, default: int = 0) -> int:
    try:
        return int(d.get(key, default) or 0)
    except (TypeError, ValueError):
        return int(default)


def _fsg_terminal_stage(summary: dict[str, Any]) -> str:
    if not bool(summary.get("stop", False)):
        return "ACTIVE"
    n_open = _number(summary, "frontier_open_count")
    before = _number(summary, "candidates_before_consensus_count")
    rejected = _number(summary, "consensus_rejected_candidate_count")
    if n_open == 0:
        return "NO_OPEN_FRONTIER"
    if before == 0:
        return "OPEN_BUT_NO_CANDIDATE"
    if rejected >= before:
        return "CANDIDATES_REJECTED_BY_CONSENSUS"
    return "STOP_OTHER"


def _allowed_value(x: Any) -> bool | None:
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, dict):
        for k in ("allowed", "accept", "accepted", "ok", "continue"):
            if k in x and isinstance(x[k], (bool, np.bool_)):
                return bool(x[k])
    if isinstance(x, (tuple, list)) and x and isinstance(x[0], (bool, np.bool_)):
        return bool(x[0])
    return None


TRACE_NAMES = (
    "extract_frontier",
    "classify_frontier_state",
    "_candidate_continuation_from_projected",
    "candidate_state_consensus",
    "_new_box_area",
    "edge_evidence",
    "binocular_edge_evidence",
)


@contextmanager
def _policy_trace_capture(fn: Callable[..., Any]):
    events: list[dict[str, Any]] = []
    patches: list[tuple[Any, str, Any, bool]] = []
    seen: set[tuple[int, str]] = set()

    globals_dict = getattr(fn, "__globals__", {})
    containers: list[Any] = [globals_dict]
    for value in globals_dict.values():
        if isinstance(value, types.ModuleType):
            containers.append(value)

    def get(container: Any, name: str):
        if isinstance(container, dict):
            return container.get(name, None), name in container
        return getattr(container, name, None), hasattr(container, name)

    def setv(container: Any, name: str, value: Any) -> None:
        if isinstance(container, dict):
            container[name] = value
        else:
            setattr(container, name, value)

    for container in containers:
        for name in TRACE_NAMES:
            original, exists = get(container, name)
            if not exists or not callable(original):
                continue
            key = (id(container), name)
            if key in seen:
                continue
            seen.add(key)

            def make_wrapper(label: str, target: Callable[..., Any]):
                def wrapper(*args, **kwargs):
                    result = target(*args, **kwargs)
                    events.append({
                        "name": label,
                        "args": _jsonable(args),
                        "kwargs": _jsonable(kwargs),
                        "result": _jsonable(result),
                        "allowed": _allowed_value(result),
                    })
                    return result
                wrapper.__name__ = getattr(target, "__name__", label)
                wrapper.__doc__ = getattr(target, "__doc__", None)
                return wrapper

            patches.append((container, name, original, exists))
            setv(container, name, make_wrapper(name, original))
    try:
        yield events
    finally:
        for container, name, original, _ in reversed(patches):
            setv(container, name, original)


def _compare_decisions(saved: dict[str, Any] | None, replay: dict[str, Any]) -> list[str]:
    if not saved:
        return ["saved final fsg6f_decision missing"]
    a = _decision_summary(saved)
    b = _decision_summary(replay)
    keys = sorted(set(a) & set(b))
    required = {
        "stop", "reason", "frontier_open_count", "frontier_map_resolved_count",
        "frontier_boundary_resolved_count", "candidates_before_consensus_count",
        "consensus_rejected_candidate_count",
    }
    missing_required = sorted(required - set(keys))
    mismatches = [f"missing comparable required fields: {missing_required}"] if missing_required else []
    for k in keys:
        av, bv = a[k], b[k]
        if k == "next_gaze_deg" and av is not None and bv is not None:
            aa = np.asarray(av, float)
            bb = np.asarray(bv, float)
            if aa.shape != bb.shape or not np.allclose(aa, bb, rtol=0.0, atol=1e-8, equal_nan=True):
                mismatches.append(f"{k}: saved={av} replay={bv}")
        elif av != bv:
            mismatches.append(f"{k}: saved={av} replay={bv}")
    return mismatches


def _visited_mask(ev: epistemic.Evidence, visited: list[tuple[float, float]]) -> np.ndarray:
    out = np.zeros(ev.shape, bool)
    if not visited:
        return out
    yaw = np.asarray([g[0] for g in visited], float)
    pitch = np.asarray([g[1] for g in visited], float)
    y, x, ok = epistemic._cells(ev, yaw, pitch)
    out[y[ok], x[ok]] = True
    return out


def _state_masks(ev: epistemic.Evidence, map_xyz: np.ndarray,
                 visited: list[tuple[float, float]]) -> dict[str, np.ndarray | int | float]:
    support, footprint_cells, median_range = epistemic._map_support(ev, map_xyz)
    complement = ~support
    exterior, border_distance = epistemic._exterior_and_distance(complement)
    shoreline = complement & cv2.dilate(support.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    never = ~ev.seen_any
    target_no_depth = ev.seen_target & ~ev.target_depth_valid
    target_with_depth = ev.target_depth_valid
    nontarget_only = ev.seen_nontarget & ~ev.seen_target
    mixed = ev.seen_target & ev.seen_nontarget
    visited_mask = _visited_mask(ev, visited)
    eligible = shoreline & exterior & never & ~visited_mask
    return {
        "support": support,
        "complement": complement,
        "exterior": exterior,
        "border_distance": border_distance,
        "shoreline": shoreline,
        "never": never,
        "target_no_depth": target_no_depth,
        "target_with_depth": target_with_depth,
        "nontarget_only": nontarget_only,
        "mixed": mixed,
        "seen_any": ev.seen_any,
        "seen_target": ev.seen_target,
        "seen_nontarget": ev.seen_nontarget,
        "visited_gaze_cell": visited_mask,
        "eligible": eligible,
        "footprint_cells": int(footprint_cells),
        "median_range_m": float(median_range),
    }


def _rebuild_object(run_root: Path, result: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    iid = int(result["instance_id"])
    odir = run_root / "objects" / f"instance_{iid:04d}"
    trajectory = list(result["trajectory"])
    if not trajectory:
        raise RuntimeError(f"instance {iid} has no trajectory")

    ev = _make_evidence(public.ORIGINAL_DOMAIN)
    history: list[Any] = []
    visited: list[tuple[float, float]] = []
    last_c = None
    last_state = None
    for row in trajectory:
        step = int(row["step"])
        gaze = tuple(map(float, row["gaze_deg"]))
        adir = odir / "acquisitions" / f"fix_{step:02d}"
        c = _json(adir / "calibration.json")
        obs = _load_npz(adir / "oracle_observation.npz")
        rec, _, state = oracle_matcher.compute(c, obs)
        epistemic.add_observation(
            ev, c,
            state["ids_left"], state["raw_support_L"],
            state["ids_right"], state["raw_support_R"],
            rec["valid"], iid,
        )
        history.append(_history_entry(c, state, iid, gaze))
        visited.append(gaze)
        last_c, last_state = c, state

    map_xyz = _load_map(odir / "final_map.npz")
    if last_c is None or last_state is None or not len(map_xyz):
        raise RuntimeError(f"instance {iid} lacks final replay state/map")

    kwargs = _policy_kwargs(visited[-1], last_c, last_state, map_xyz, visited, history, iid)
    with _policy_trace_capture(object_policy.choose_next) as trace_events:
        replay_decision = object_policy.choose_next(**kwargs)
    replay_summary = _decision_summary(replay_decision)
    saved_decision = trajectory[-1].get("fsg6f_decision")
    mismatches = _compare_decisions(saved_decision, replay_decision)
    if mismatches:
        raise RuntimeError(f"instance {iid} final FSG6f replay mismatch: " + " | ".join(mismatches))

    masks = _state_masks(ev, map_xyz, visited)
    cycaudit = epistemic.audit(ev, map_xyz, visited)
    np.savez_compressed(
        out_dir / "controller_state.npz",
        yaw_min_deg=np.float64(ev.yaw_min_deg), yaw_max_deg=np.float64(ev.yaw_max_deg),
        pitch_min_deg=np.float64(ev.pitch_min_deg), pitch_max_deg=np.float64(ev.pitch_max_deg),
        grid_deg=np.float64(ev.grid_deg),
        support=np.asarray(masks["support"], bool),
        complement=np.asarray(masks["complement"], bool),
        exterior=np.asarray(masks["exterior"], bool),
        border_distance=np.asarray(masks["border_distance"], np.int32),
        shoreline=np.asarray(masks["shoreline"], bool),
        never=np.asarray(masks["never"], bool),
        target_no_depth=np.asarray(masks["target_no_depth"], bool),
        target_with_depth=np.asarray(masks["target_with_depth"], bool),
        nontarget_only=np.asarray(masks["nontarget_only"], bool),
        mixed=np.asarray(masks["mixed"], bool),
        seen_any=np.asarray(masks["seen_any"], bool),
        seen_target=np.asarray(masks["seen_target"], bool),
        seen_nontarget=np.asarray(masks["seen_nontarget"], bool),
        visited_gaze_cell=np.asarray(masks["visited_gaze_cell"], bool),
        eligible=np.asarray(masks["eligible"], bool),
    )

    gate_summary: dict[str, Any] = {}
    for name in TRACE_NAMES:
        evs = [e for e in trace_events if e["name"] == name]
        if not evs:
            continue
        allowed = [e.get("allowed") for e in evs if e.get("allowed") is not None]
        gate_summary[name] = {
            "calls": len(evs),
            "allowed_true": int(sum(bool(v) for v in allowed)),
            "allowed_false": int(sum(not bool(v) for v in allowed)),
            "events": evs,
        }

    report = {
        "instance_id": iid,
        "object_name": result.get("object_name"),
        "fixation_count": int(result.get("fixation_count", len(trajectory))),
        "termination": result.get("termination"),
        "visited_gazes_deg": [list(map(float, g)) for g in visited],
        "saved_final_fsg6f_decision": _decision_summary(saved_decision or {}),
        "replayed_final_fsg6f_decision": replay_summary,
        "fsg_terminal_stage": _fsg_terminal_stage(replay_summary),
        "replay_mismatches": mismatches,
        "trace_gate_summary": gate_summary,
        "cyclopean_audit": cycaudit,
        "controller_state_counts": {
            "support_cells": int(np.asarray(masks["support"]).sum()),
            "shoreline_cells": int(np.asarray(masks["shoreline"]).sum()),
            "exterior_shoreline_cells": int((np.asarray(masks["shoreline"]) & np.asarray(masks["exterior"])).sum()),
            "eligible_never_observed_exterior_shoreline_cells": int(np.asarray(masks["eligible"]).sum()),
            "never_observed_cells": int(np.asarray(masks["never"]).sum()),
            "target_no_depth_cells": int(np.asarray(masks["target_no_depth"]).sum()),
            "visited_gaze_cells": int(np.asarray(masks["visited_gaze_cell"]).sum()),
            "footprint_cells": int(masks["footprint_cells"]),
            "median_range_m": float(masks["median_range_m"]),
        },
        "truth_opened": False,
    }
    _write(out_dir / "control_audit.json", report)
    return report


def _covered(reference: np.ndarray, surfels: np.ndarray, radius: float) -> np.ndarray:
    ref = np.asarray(reference, np.float64)
    pts = np.asarray(surfels, np.float64)
    out = np.zeros(len(ref), bool)
    if not len(ref) or not len(pts):
        return out
    cell = float(radius)
    q = np.floor(pts / cell).astype(np.int64)
    table: dict[tuple[int, int, int], list[int]] = {}
    for i, c in enumerate(q):
        table.setdefault(tuple(map(int, c)), []).append(i)
    qr = np.floor(ref / cell).astype(np.int64)
    r2 = radius * radius
    for i, c in enumerate(qr):
        cx, cy, cz = map(int, c)
        candidates: list[int] = []
        for dz in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    candidates.extend(table.get((cx + dx, cy + dy, cz + dz), ()))
        if candidates:
            d = pts[np.asarray(candidates)] - ref[i]
            out[i] = bool(np.any(np.einsum("ij,ij->i", d, d) <= r2))
    return out


def _cells_from_angles(state: dict[str, np.ndarray], angles: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    y0 = float(np.asarray(state["yaw_min_deg"]).item())
    p0 = float(np.asarray(state["pitch_min_deg"]).item())
    g = float(np.asarray(state["grid_deg"]).item())
    h, w = np.asarray(state["support"]).shape
    a = np.asarray(angles, float)
    x = np.rint((a[:, 0] - y0) / g).astype(np.int64)
    y = np.rint((a[:, 1] - p0) / g).astype(np.int64)
    ok = np.isfinite(a).all(axis=1) & (x >= 0) & (x < w) & (y >= 0) & (y < h)
    return y, x, ok


def _classify_truth_cells(state: dict[str, np.ndarray], angles: np.ndarray) -> tuple[list[str], list[str], np.ndarray, np.ndarray, np.ndarray]:
    y, x, ok = _cells_from_angles(state, angles)
    first: list[str] = []
    subtype: list[str] = []
    for i in range(len(angles)):
        if not ok[i]:
            first.append("OUT_OF_CHART")
            subtype.append("OUT_OF_CHART")
            continue
        yy, xx = int(y[i]), int(x[i])
        support = bool(state["support"][yy, xx])
        shoreline = bool(state["shoreline"][yy, xx])
        exterior = bool(state["exterior"][yy, xx])
        never = bool(state["never"][yy, xx])
        visited = bool(state["visited_gaze_cell"][yy, xx])
        tnd = bool(state["target_no_depth"][yy, xx])
        twd = bool(state["target_with_depth"][yy, xx])
        non = bool(state["nontarget_only"][yy, xx])
        mix = bool(state["mixed"][yy, xx])

        if not shoreline:
            first.append("NOT_SHORELINE")
            subtype.append("ANGULAR_SUPPORT_BUT_3D_UNCOVERED" if support else "COMPLEMENT_NONSHORELINE")
            continue
        if not exterior:
            first.append("INTERNAL_COMPONENT")
            if never:
                subtype.append("INTERNAL_NEVER_OBSERVED")
            elif tnd:
                subtype.append("INTERNAL_TARGET_NO_DEPTH")
            elif twd:
                subtype.append("INTERNAL_TARGET_WITH_DEPTH")
            elif non:
                subtype.append("INTERNAL_NONTARGET_ONLY")
            elif mix:
                subtype.append("INTERNAL_MIXED")
            else:
                subtype.append("INTERNAL_OTHER_OBSERVED")
            continue
        if not never:
            first.append("ALREADY_OBSERVED")
            if tnd:
                subtype.append("EXTERIOR_TARGET_NO_DEPTH")
            elif twd:
                subtype.append("EXTERIOR_TARGET_WITH_DEPTH")
            elif non:
                subtype.append("EXTERIOR_NONTARGET_ONLY")
            elif mix:
                subtype.append("EXTERIOR_MIXED")
            else:
                subtype.append("EXTERIOR_OTHER_OBSERVED")
            continue
        if visited:
            first.append("PREVIOUSLY_FIXATED_CELL")
            subtype.append("EXTERIOR_NEVER_OBSERVED_VISITED")
            continue
        first.append("ELIGIBLE_NEVER_OBSERVED_EXTERIOR")
        subtype.append("EXTERIOR_NEVER_OBSERVED_ELIGIBLE")
    return first, subtype, y, x, ok


def _hist(values: list[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for v in values:
        out[v] = out.get(v, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))


def _trajectory_signature(result: dict[str, Any]) -> list[tuple[tuple[float, float], str]]:
    out = []
    for row in result.get("trajectory", []):
        g = tuple(round(float(v), 9) for v in row.get("gaze_deg", ()))
        out.append((g, str(row.get("action_source"))))
    return out


def _validate_runs(o1: Path, o2: Path) -> tuple[dict, dict, dict]:
    m1 = _json(o1 / "manifest.json")
    m2 = _json(o2 / "manifest.json")
    e2 = _json(o2 / "evaluation.json")
    if not m1.get("control_complete") or m1.get("smoke"):
        raise RuntimeError("Oracle-1 baseline is not a completed full run")
    if not m2.get("control_complete") or m2.get("smoke"):
        raise RuntimeError("Oracle-2 baseline is not a completed full run")
    if int(m1.get("attempted_instance_count", 0)) != 25 or len(m1.get("objects", [])) != 25:
        raise RuntimeError("Oracle-1 does not contain the frozen 25-object set")
    if len(m2.get("objects", [])) != 25:
        raise RuntimeError("Oracle-2 does not contain the same 25 targets")
    if bool(m1.get("dense_evaluation_truth_opened_during_control", True)):
        raise RuntimeError("Oracle-1 manifest does not certify truth isolation")
    if bool(m2.get("dense_evaluation_truth_opened_during_control", True)):
        raise RuntimeError("Oracle-2 manifest does not certify truth isolation")
    return m1, m2, e2


def _source_audit() -> dict[str, Any]:
    items = {}
    fn = object_policy.choose_next
    try:
        src = inspect.getsource(fn)
    except (OSError, TypeError):
        src = ""
    items["multiobject2c_policy.choose_next"] = {
        "sha256": _sha256_text(src),
        "lines": len(src.splitlines()),
        "source_available": bool(src),
    }
    gl = getattr(fn, "__globals__", {})
    for name, obj in gl.items():
        if isinstance(obj, types.ModuleType) and "fsg6f" in getattr(obj, "__name__", ""):
            try:
                mod_src = inspect.getsource(obj)
            except (OSError, TypeError):
                mod_src = ""
            items[obj.__name__] = {
                "sha256": _sha256_text(mod_src),
                "lines": len(mod_src.splitlines()),
                "source_available": bool(mod_src),
            }
    return items


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--oracle1-run", type=Path, default=Path(public.ORACLE1_RUN_DEFAULT))
    ap.add_argument("--oracle2-run", type=Path, default=Path(public.ORACLE2_RUN_DEFAULT))
    ap.add_argument("--out", type=Path, default=Path(public.DEFAULT_OUT))
    args = ap.parse_args()

    o1 = args.oracle1_run.resolve()
    o2 = args.oracle2_run.resolve()
    out = args.out.resolve()
    _new_dir(out)
    (out / "objects").mkdir()

    bad = public.self_test()
    if bad:
        raise RuntimeError("public self-test failed: " + "; ".join(bad))
    m1, m2, e2 = _validate_runs(o1, o2)
    o1_by_id = {int(o["instance_id"]): o for o in m1["objects"]}
    o2_by_id = {int(o["instance_id"]): o for o in m2["objects"]}
    rows2 = {int(o["instance_id"]): o for o in e2["objects"]}
    target_ids = [int(o["instance_id"]) for o in m1["objects"]]
    ranked = sorted(target_ids, key=lambda iid: (-int(rows2[iid].get("baseline_misses", 0)), iid))
    focus_ids = ranked[:public.FOCUS_OBJECT_COUNT]

    phase_manifest = {
        "schema": "ClassroomOracle3-audit-v1",
        "spec_id": public.SPEC_ID,
        "public_digest": public.public_digest(),
        "oracle1_run": str(o1),
        "oracle2_run": str(o2),
        "focus_instance_ids": focus_ids,
        "focus_selection": public.SCIENTIFIC_CONTRACT["focus_selection"],
        "controller_phase_complete": False,
        "truth_phase_started": False,
        "truth_opened_during_controller_replay": False,
        "new_acquisitions": 0,
        "new_fixations": 0,
        "new_fusion": 0,
        "source_audit": _source_audit(),
    }
    _write(out / "manifest.json", phase_manifest)

    # Phase 1: controller replay only.  Dense reference files are intentionally
    # not named or opened anywhere above this point.
    control_reports: dict[int, dict[str, Any]] = {}
    for iid in target_ids:
        od = out / "objects" / f"instance_{iid:04d}"
        od.mkdir()
        control_reports[iid] = _rebuild_object(o1, o1_by_id[iid], od)

    phase_manifest["controller_phase_complete"] = True
    _write(out / "manifest.json", phase_manifest)

    # Phase 2: truth may be opened only now, after every replay matched.
    phase_manifest["truth_phase_started"] = True
    _write(out / "manifest.json", phase_manifest)
    truth_path = o1 / "bootstrap" / "evaluation_only" / "reachable_samples.npz"
    if not truth_path.exists():
        raise FileNotFoundError(f"Oracle-1 evaluation truth missing: {truth_path}")
    with np.load(truth_path, allow_pickle=False) as z:
        truth_ids = np.asarray(z["instance_id"], np.int32)
        truth_xyz = np.asarray(z["xyz_h"], np.float64)
        truth_angles = np.asarray(z["yaw_pitch_deg"], np.float64)

    aggregate_first: list[str] = []
    aggregate_sub: list[str] = []
    object_rows: list[dict[str, Any]] = []
    radius = float(public.COVERAGE_RADIUS_M)

    for iid in target_ids:
        od = out / "objects" / f"instance_{iid:04d}"
        state = _load_npz(od / "controller_state.npz")
        sel = truth_ids == iid
        xyz = truth_xyz[sel]
        angles = truth_angles[sel]
        surfels = _load_map(o1 / "objects" / f"instance_{iid:04d}" / "final_map.npz")
        cov = _covered(xyz, surfels, radius)
        miss_xyz = xyz[~cov]
        miss_angles = angles[~cov]
        first, subtype, y, x, ok = _classify_truth_cells(state, miss_angles)
        aggregate_first.extend(first)
        aggregate_sub.extend(subtype)

        first_hist = _hist(first)
        sub_hist = _hist(subtype)
        unique_cells = set((int(y[i]), int(x[i])) for i in range(len(first)) if ok[i])
        dominant = next(iter(first_hist), None)
        eligible_misses = int(first_hist.get("ELIGIBLE_NEVER_OBSERVED_EXTERIOR", 0))
        if control_reports[iid]["termination"] == "attention_complete" and eligible_misses:
            raise RuntimeError(
                f"instance {iid}: truth maps {eligible_misses} missed samples to controller-eligible cells, "
                "but attention_complete replay reported no eligible Cyclopean action"
            )

        reason_codes = np.asarray([public.CYCLOPEAN_FIRST_REJECTION_REASONS.index(v) for v in first], np.int16) if first else np.empty(0, np.int16)
        subtype_codes = np.asarray([public.TRUTH_SUBTYPES.index(v) for v in subtype], np.int16) if subtype else np.empty(0, np.int16)
        np.savez_compressed(
            od / "truth_misses.npz",
            xyz_h=np.asarray(miss_xyz, np.float32),
            yaw_pitch_deg=np.asarray(miss_angles, np.float32),
            cell_y=np.asarray(y, np.int32), cell_x=np.asarray(x, np.int32), cell_in_chart=np.asarray(ok, bool),
            first_reason_code=reason_codes, subtype_code=subtype_codes,
        )

        sig1 = _trajectory_signature(o1_by_id[iid])
        sig2 = _trajectory_signature(o2_by_id[iid])
        row = {
            "instance_id": iid,
            "object_name": o1_by_id[iid].get("object_name"),
            "focus": iid in focus_ids,
            "reachable_samples": int(len(xyz)),
            "covered_samples": int(cov.sum()),
            "coverage_fraction": float(cov.mean()) if len(cov) else None,
            "missed_samples": int((~cov).sum()),
            "missed_unique_chart_cells": len(unique_cells),
            "cyclopean_first_rejection_histogram": first_hist,
            "truth_subtype_histogram": sub_hist,
            "dominant_first_rejection_reason": dominant,
            "fsg_terminal_stage": control_reports[iid]["fsg_terminal_stage"],
            "fsg_final_decision": control_reports[iid]["replayed_final_fsg6f_decision"],
            "cyclopean_eligible_cells_final": control_reports[iid]["controller_state_counts"]["eligible_never_observed_exterior_shoreline_cells"],
            "oracle1_oracle2_trajectory_identical": sig1 == sig2,
            "oracle1_fixations": len(sig1),
            "oracle2_fixations": len(sig2),
            "oracle2_termination": o2_by_id[iid].get("termination"),
            "oracle2_looks_outside_old_domain": int(o2_by_id[iid].get("domain_audit", {}).get("looks_outside_original_domain", 0)),
            "truth_opened_after_controller_phase": True,
        }
        _write(od / "truth_audit.json", row)
        object_rows.append(row)

    focus_rows = [r for r in object_rows if r["focus"]]
    focus_rows.sort(key=lambda r: focus_ids.index(int(r["instance_id"])))
    result = {
        "schema": "ClassroomOracle3-result-v1",
        "spec_id": public.SPEC_ID,
        "controller_phase_replays": len(control_reports),
        "all_final_fsg6f_replays_exact": all(not control_reports[i]["replay_mismatches"] for i in target_ids),
        "truth_opened_during_controller_replay": False,
        "truth_opened_only_after_controller_phase": True,
        "target_instance_count": len(target_ids),
        "focus_instance_ids": focus_ids,
        "focus_objects": focus_rows,
        "aggregate_all_objects": {
            "missed_samples": len(aggregate_first),
            "cyclopean_first_rejection_histogram": _hist(aggregate_first),
            "truth_subtype_histogram": _hist(aggregate_sub),
        },
        "objects": object_rows,
        "interpretation_contract": [
            "This audit diagnoses representation and eligibility only; it does not change a controller rule.",
            "A truth miss classified NOT_SHORELINE is invisible to the Cyclopean shoreline selector before any exterior/observation test is reached.",
            "A truth miss classified INTERNAL_COMPONENT reaches the shoreline but is rejected by the exterior-only topology rule.",
            "A truth miss classified ALREADY_OBSERVED reaches exterior shoreline but is rejected because the current handoff explores only NEVER_OBSERVED cells.",
            "FSG terminal-stage diagnostics distinguish no OPEN frontier from OPEN-with-no-candidate and consensus rejection.",
            "No numerical outcome is a PASS/FAIL threshold.",
        ],
    }
    _write(out / "audit.json", result)
    phase_manifest["truth_phase_complete"] = True
    phase_manifest["truth_opened_after_controller_phase"] = True
    _write(out / "manifest.json", phase_manifest)

    print("[classroom-oracle3] COMPLETE", json.dumps({
        "objects": len(object_rows),
        "focus": focus_ids,
        "missed_samples": len(aggregate_first),
        "first_rejection": result["aggregate_all_objects"]["cyclopean_first_rejection_histogram"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
