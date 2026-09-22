"""Read-only audit of the MultiObject-3e frozen-frontier reactivation.

The audit reproduces the exact FSG6f state immediately before and immediately
after the single epistemic handoff, then decomposes the frontier and candidate
changes without rendering, fusing, tuning, or executing another action.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

import fsg6f_frontier as frozen_frontier
import fsg6f_public as frozen_public
from fsg3_surface_map import load_map
from fsg_geometry import json_write
from fsg_stereo_supported import check_kernel_equivalence

import multiobject2c_policy as policy
import multiobject3d_audit as audit3d
import multiobject3e_public as parent_public
import multiobject3f_progress as progress
import multiobject3f_public as public


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _resolve(path_like: str, base: Path) -> Path:
    p = Path(path_like)
    return p.resolve() if p.is_absolute() else (base / p).resolve()


def _same_optional_gaze(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return bool(np.allclose(np.asarray(a, float), np.asarray(b, float), atol=1e-9, rtol=0.0))


def _validate_parent(parent: Path) -> tuple[dict, Path, dict, int, dict[int, dict]]:
    m3e = json.loads((parent / "prediction_manifest.json").read_text())
    if m3e.get("schema") != public.PARENT_SPEC_ID:
        raise AssertionError("MultiObject-3f requires a completed MultiObject-3e parent")
    if m3e.get("public_spec_sha256") != parent_public.public_digest():
        raise AssertionError("MultiObject-3e public digest mismatch")
    if int(m3e.get("seed", -1)) != public.SEED or m3e.get("truth_opened") is not False:
        raise AssertionError("wrong seed or truth integrity broken")
    if int(m3e.get("added_fixations", -1)) != 1 or int(m3e.get("returned_local_policy_decisions", -1)) != 1:
        raise AssertionError("parent is not the bounded one-handoff experiment")
    if m3e.get("returned_local_action_executed") is not False or m3e.get("automatic_handoff_loop") is not False:
        raise AssertionError("parent executed beyond the bounded handoff")
    if m3e.get("return_status") != "LOCAL_POLICY_REACTIVATED":
        raise AssertionError("MultiObject-3f requires the reactivated MultiObject-3e outcome")
    if m3e.get("structural_fails") not in ([], None):
        raise AssertionError("MultiObject-3e parent has structural failures")
    target_id = int(m3e.get("selected_object_id", -1))
    if target_id <= 0:
        raise AssertionError("parent selected-object id missing")

    parent3c = _resolve(m3e["scene_parent_record"], parent)
    pm3c, target3c, objects = audit3d._validate_parent(parent3c)
    if int(target3c) != target_id:
        raise AssertionError("MultiObject-3e and MultiObject-3c active-object ids disagree")
    if pm3c.get("termination_reason") != "no_frontier" or pm3c.get("scientific_stop_reached") is not True:
        raise AssertionError("pre-handoff parent is not the declared frozen no_frontier stop")
    return m3e, parent3c, pm3c, target_id, objects


def _exact_decision_replay(saved: dict, replay: dict, label: str) -> None:
    exact_keys = (
        "stop", "reason", "frontier_voxel_count", "frontier_count", "frontier_raw_count",
        "frontier_map_resolved_count", "frontier_boundary_resolved_count", "frontier_open_count",
        "candidates_before_consensus_count", "consensus_rejected_candidate_count",
    )
    for k in exact_keys:
        if replay.get(k) != saved.get(k):
            raise AssertionError(f"{label} frozen-policy replay mismatch for {k}: {replay.get(k)} != {saved.get(k)}")
    if not _same_optional_gaze(replay.get("next_gaze_deg"), saved.get("next_gaze_deg")):
        raise AssertionError(f"{label} frozen-policy replay mismatch for next_gaze_deg")


def _voxel_keys(xyz_h: np.ndarray, cell: float) -> np.ndarray:
    """Exact integer identity on the already-frozen FSG6f voxel grid."""
    p = np.asarray(xyz_h, float).reshape(-1, 3)
    good = np.isfinite(p).all(1) & (p[:, 2] < -1e-6)
    p = p[good]
    if not len(p):
        return np.empty((0, 3), np.int64)
    return np.unique(np.floor(p / float(cell)).astype(np.int64), axis=0)


def _frontier_keys(frontier: dict, cell: float) -> np.ndarray:
    p = np.asarray(frontier["xyz_h"], float).reshape(-1, 3)
    keys = np.floor(p / float(cell)).astype(np.int64)
    if len(keys) != len({tuple(map(int, k)) for k in keys}):
        raise AssertionError("frontier source voxel keys are not unique")
    return keys


def _state_name(frontier_state: dict, i: int) -> str:
    vals = {
        "OPEN": bool(frontier_state["open"][i]),
        "MAP_RESOLVED": bool(frontier_state["map_resolved"][i]),
        "BOUNDARY_RESOLVED": bool(frontier_state["boundary_resolved"][i]),
    }
    names = [k for k, v in vals.items() if v]
    if len(names) != 1:
        raise AssertionError(f"frontier state partition is not exclusive at index {i}: {vals}")
    return names[0]


def _spherical_sep_deg(yaw0: float, pitch0: float, yaw1: float, pitch1: float) -> float:
    y0, p0, y1, p1 = map(math.radians, (yaw0, pitch0, yaw1, pitch1))
    a = np.array([math.cos(p0) * math.sin(y0), math.sin(p0), -math.cos(p0) * math.cos(y0)])
    b = np.array([math.cos(p1) * math.sin(y1), math.sin(p1), -math.cos(p1) * math.cos(y1)])
    return math.degrees(math.acos(float(np.clip(np.dot(a, b), -1.0, 1.0))))


def _summary_stats(values: list[float]) -> dict:
    if not values:
        return {"count": 0, "min": None, "median": None, "max": None, "mean": None}
    a = np.asarray(values, float)
    return {
        "count": int(len(a)),
        "min": float(np.min(a)),
        "median": float(np.median(a)),
        "max": float(np.max(a)),
        "mean": float(np.mean(a)),
    }


def _nearest_distances(points: np.ndarray, refs: np.ndarray) -> np.ndarray:
    p = np.asarray(points, float).reshape(-1, 3)
    r = np.asarray(refs, float).reshape(-1, 3)
    if not len(p):
        return np.empty(0, float)
    if not len(r):
        return np.full(len(p), np.nan, float)
    out = np.empty(len(p), float)
    for i, x in enumerate(p):
        out[i] = float(np.min(np.linalg.norm(r - x, axis=1)))
    return out


def _frontier_lineage(pre_frontier: dict, pre_state: dict, post_frontier: dict, post_state: dict,
                      pre_map_keys: set[tuple[int, int, int]], patch_keys: set[tuple[int, int, int]],
                      pre_map_post_gaze_frontier_keys: set[tuple[int, int, int]],
                      handoff_patch_xyz: np.ndarray, voxel_m: float) -> tuple[dict, list[dict], dict[tuple[int, int, int], str]]:
    pre_keys_arr = _frontier_keys(pre_frontier, voxel_m)
    post_keys_arr = _frontier_keys(post_frontier, voxel_m)
    pre_idx = {tuple(map(int, k)): i for i, k in enumerate(pre_keys_arr)}
    post_idx = {tuple(map(int, k)): i for i, k in enumerate(post_keys_arr)}
    pre_keys, post_keys = set(pre_idx), set(post_idx)
    persistent = sorted(pre_keys & post_keys)
    appeared = sorted(post_keys - pre_keys)
    disappeared = sorted(pre_keys - post_keys)

    transitions: dict[str, dict[str, int]] = {
        s: {t: 0 for t in ("OPEN", "MAP_RESOLVED", "BOUNDARY_RESOLVED")}
        for s in ("OPEN", "MAP_RESOLVED", "BOUNDARY_RESOLVED")
    }
    source_shift, target_shift, target_angular_shift = [], [], []
    persistent_rows = []
    origin_by_post_key: dict[tuple[int, int, int], str] = {}
    for key in persistent:
        a, b = pre_idx[key], post_idx[key]
        ps, qs = _state_name(pre_state, a), _state_name(post_state, b)
        transitions[ps][qs] += 1
        ds = float(np.linalg.norm(np.asarray(post_frontier["xyz_h"])[b] - np.asarray(pre_frontier["xyz_h"])[a]))
        dt = float(np.linalg.norm(np.asarray(post_frontier["target_xyz_h"])[b] - np.asarray(pre_frontier["target_xyz_h"])[a]))
        da = _spherical_sep_deg(
            float(pre_frontier["target_yaw_deg"][a]), float(pre_frontier["target_pitch_deg"][a]),
            float(post_frontier["target_yaw_deg"][b]), float(post_frontier["target_pitch_deg"][b]),
        )
        source_shift.append(ds); target_shift.append(dt); target_angular_shift.append(da)
        origin_by_post_key[key] = "PERSISTENT"
        persistent_rows.append({
            "voxel_key": list(key), "pre_state": ps, "post_state": qs,
            "source_shift_m": ds, "target_shift_m": dt, "target_angular_shift_deg": da,
            "pre_strength": float(pre_frontier["strength"][a]),
            "post_strength": float(post_frontier["strength"][b]),
        })

    appeared_src = np.asarray([post_frontier["xyz_h"][post_idx[k]] for k in appeared], float) if appeared else np.empty((0, 3))
    appeared_tgt = np.asarray([post_frontier["target_xyz_h"][post_idx[k]] for k in appeared], float) if appeared else np.empty((0, 3))
    near_src = _nearest_distances(appeared_src, handoff_patch_xyz)
    near_tgt = _nearest_distances(appeared_tgt, handoff_patch_xyz)
    appeared_rows = []
    appeared_state_counts = {"OPEN": 0, "MAP_RESOLVED": 0, "BOUNDARY_RESOLVED": 0}
    appeared_from_preexisting = 0
    appeared_same_patch_voxel = 0
    appeared_exposed_by_post_gaze_on_pre_map = 0
    appeared_created_by_map_update_on_preexisting_voxel = 0
    appeared_from_new_map_voxel = 0
    for j, key in enumerate(appeared):
        i = post_idx[key]
        st = _state_name(post_state, i)
        appeared_state_counts[st] += 1
        preexisting = key in pre_map_keys
        same_patch = key in patch_keys
        gaze_exposed = key in pre_map_post_gaze_frontier_keys
        if gaze_exposed:
            appearance_class = "EXPOSED_BY_POST_GAZE_ON_PRE_MAP"
            appeared_exposed_by_post_gaze_on_pre_map += 1
        elif preexisting:
            appearance_class = "CREATED_BY_MAP_UPDATE_ON_PREEXISTING_VOXEL"
            appeared_created_by_map_update_on_preexisting_voxel += 1
        else:
            appearance_class = "FRONTIER_FROM_NEW_MAP_VOXEL"
            appeared_from_new_map_voxel += 1
        appeared_from_preexisting += int(preexisting)
        appeared_same_patch_voxel += int(same_patch)
        origin_by_post_key[key] = appearance_class
        appeared_rows.append({
            "voxel_key": list(key), "post_state": st,
            "appearance_class": appearance_class,
            "source_was_frontier_on_pre_map_at_post_gaze": bool(gaze_exposed),
            "source_map_voxel_preexisting": bool(preexisting),
            "source_map_voxel_new_after_handoff": bool(not preexisting),
            "source_voxel_contains_handoff_patch_sample": bool(same_patch),
            "source_xyz_h": [float(x) for x in np.asarray(post_frontier["xyz_h"])[i]],
            "target_xyz_h": [float(x) for x in np.asarray(post_frontier["target_xyz_h"])[i]],
            "source_yaw_deg": float(post_frontier["yaw_deg"][i]),
            "source_pitch_deg": float(post_frontier["pitch_deg"][i]),
            "target_yaw_deg": float(post_frontier["target_yaw_deg"][i]),
            "target_pitch_deg": float(post_frontier["target_pitch_deg"][i]),
            "strength": float(post_frontier["strength"][i]),
            "nearest_handoff_patch_source_m": float(near_src[j]),
            "nearest_handoff_patch_target_m": float(near_tgt[j]),
        })

    disappeared_state_counts = {"OPEN": 0, "MAP_RESOLVED": 0, "BOUNDARY_RESOLVED": 0}
    disappeared_rows = []
    for key in disappeared:
        i = pre_idx[key]
        st = _state_name(pre_state, i)
        disappeared_state_counts[st] += 1
        disappeared_rows.append({
            "voxel_key": list(key), "pre_state": st,
            "source_xyz_h": [float(x) for x in np.asarray(pre_frontier["xyz_h"])[i]],
            "target_xyz_h": [float(x) for x in np.asarray(pre_frontier["target_xyz_h"])[i]],
            "strength": float(pre_frontier["strength"][i]),
        })

    changed_state = sum(v for s, row in transitions.items() for t, v in row.items() if s != t)
    lineage = {
        "identity_rule": "exact frozen source voxel key floor(source_xyz_h / voxel_m); no tolerance",
        "voxel_m": float(voxel_m),
        "pre_frontier_count": int(len(pre_keys)),
        "post_frontier_count": int(len(post_keys)),
        "persistent_frontier_source_voxels": int(len(persistent)),
        "appeared_frontier_source_voxels": int(len(appeared)),
        "disappeared_frontier_source_voxels": int(len(disappeared)),
        "persistent_state_transition_counts": transitions,
        "persistent_state_changed_count": int(changed_state),
        "persistent_source_shift_m": _summary_stats(source_shift),
        "persistent_target_shift_m": _summary_stats(target_shift),
        "persistent_target_angular_shift_deg": _summary_stats(target_angular_shift),
        "appeared_state_counts": appeared_state_counts,
        "disappeared_state_counts": disappeared_state_counts,
        "appeared_sources_on_preexisting_map_voxels": int(appeared_from_preexisting),
        "appeared_sources_exposed_by_post_gaze_on_pre_map": int(appeared_exposed_by_post_gaze_on_pre_map),
        "appeared_sources_created_by_map_update_on_preexisting_voxel": int(appeared_created_by_map_update_on_preexisting_voxel),
        "appeared_sources_on_new_map_voxels": int(appeared_from_new_map_voxel),
        "appeared_sources_same_voxel_as_handoff_patch": int(appeared_same_patch_voxel),
        "appeared_source_nearest_handoff_patch_m": _summary_stats(near_src.tolist()),
        "appeared_target_nearest_handoff_patch_m": _summary_stats(near_tgt.tolist()),
    }
    detail_rows = persistent_rows + appeared_rows + disappeared_rows
    return lineage, detail_rows, origin_by_post_key


def _candidate_gate_table(current_yaw: float, current_pitch: float, calibration: dict, observation: dict,
                          map_xyz_h: np.ndarray, visited_gazes: list[tuple[float, float]], history: list[dict],
                          target_id: int, frontier: dict, frontier_state: dict,
                          origin_by_key: dict[tuple[int, int, int], str] | None = None) -> dict:
    """Replay the eight frozen lattice directions as diagnostics, not a policy."""
    cfg = frozen_public.SURFACE_FRONTIER
    step = float(cfg["component_step_deg"])
    seen = np.asarray(visited_gazes, float).reshape(-1, 2) if visited_gazes else np.empty((0, 2))
    ids_L = policy.relabel_instances(observation["instance_id"], target_id)
    ids_R = policy.relabel_instances(observation["instance_R"], target_id)
    raw_L = np.asarray(observation["raw_support_L"], bool)
    raw_R = np.asarray(observation["raw_support_R"], bool)
    projected_all = frozen_frontier._project_frontier_pairs(
        calibration, frontier["xyz_h"], frontier["target_xyz_h"]
    )
    fy, fp = np.asarray(frontier["yaw_deg"]), np.asarray(frontier["pitch_deg"])
    fty, ftp = np.asarray(frontier["target_yaw_deg"]), np.asarray(frontier["target_pitch_deg"])
    fs = np.asarray(frontier["strength"])
    fkeys = _frontier_keys(frontier, float(cfg["voxel_m"]))

    rows = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            yaw = float(current_yaw + dx * step)
            pitch = float(current_pitch + dy * step)
            row = {
                "direction": [int(dx), int(dy)],
                "candidate_gaze_deg": [yaw, pitch],
                "within_policy_bounds": False,
                "already_visited": False,
                "raw_frontier_support_count": 0,
                "open_frontier_support_count": 0,
                "map_resolved_support_count": 0,
                "boundary_resolved_support_count": 0,
                "minimum_open_support_required": int(cfg["minimum_candidate_frontier_support"]),
                "minimum_open_support_pass": False,
                "continuation_allowed": None,
                "continuation_combined_fraction": None,
                "state_consensus_allowed": None,
                "candidate_before_consensus": False,
                "admissible_candidate": False,
                "first_blocker": None,
                "open_support_by_frontier_origin": {},
                "appeared_open_support_by_map_voxel_origin": {},
            }
            in_bounds = bool(
                cfg["yaw_min_deg"] - 1e-9 <= yaw <= cfg["yaw_max_deg"] + 1e-9
                and cfg["pitch_min_deg"] - 1e-9 <= pitch <= cfg["pitch_max_deg"] + 1e-9
            )
            row["within_policy_bounds"] = in_bounds
            if not in_bounds:
                row["first_blocker"] = "POLICY_BOUNDS"
                rows.append(row); continue
            already = bool(len(seen) and np.any(np.all(np.isclose(seen, [yaw, pitch], atol=1e-9), axis=1)))
            row["already_visited"] = already
            if already:
                row["first_blocker"] = "ALREADY_VISITED"
                rows.append(row); continue

            u = np.array([dx, dy], float); u /= np.linalg.norm(u)
            if len(fs):
                delta = np.c_[fty - fy, ftp - fp]
                dn = np.linalg.norm(delta, axis=1)
                good = dn > 1e-12
                align = np.zeros(len(delta), float)
                align[good] = (delta[good] / dn[good, None]) @ u
                raw_support = align >= cfg["alignment_cos_min"]
                open_support = raw_support & np.asarray(frontier_state["open"], bool)
            else:
                align = np.empty(0, float)
                raw_support = np.zeros(0, bool)
                open_support = np.zeros(0, bool)
            nraw = int(raw_support.sum())
            nopen = int(open_support.sum())
            nmap = int((raw_support & np.asarray(frontier_state["map_resolved"], bool)).sum())
            nbound = int((raw_support & np.asarray(frontier_state["boundary_resolved"], bool)).sum())
            if nraw != nopen + nmap + nbound:
                raise AssertionError("candidate frontier-state partition is not exhaustive")
            row.update({
                "raw_frontier_support_count": nraw,
                "open_frontier_support_count": nopen,
                "map_resolved_support_count": nmap,
                "boundary_resolved_support_count": nbound,
            })

            if origin_by_key is not None and nopen:
                by_origin: dict[str, int] = {}
                appeared_voxel_origin = {"PREEXISTING_MAP_VOXEL": 0, "NEW_MAP_VOXEL": 0}
                for i in np.flatnonzero(open_support):
                    key = tuple(map(int, fkeys[i]))
                    origin = origin_by_key.get(key, "UNKNOWN")
                    by_origin[origin] = by_origin.get(origin, 0) + 1
                    if origin == "APPEARED":
                        # The caller stores this suffix in origin_by_key for appeared keys when useful.
                        pass
                row["open_support_by_frontier_origin"] = by_origin
                row["appeared_open_support_by_map_voxel_origin"] = appeared_voxel_origin

            min_pass = bool(nopen >= int(cfg["minimum_candidate_frontier_support"]))
            row["minimum_open_support_pass"] = min_pass
            consensus = frozen_frontier.candidate_state_consensus(nopen, nmap, nbound)
            row["state_consensus_allowed"] = bool(consensus["allowed"])
            if not min_pass:
                row["first_blocker"] = "MINIMUM_OPEN_SUPPORT"
                rows.append(row); continue

            continuation = frozen_frontier._candidate_continuation_from_projected(
                dx, dy, ids_L, raw_L, ids_R, raw_R, projected_all, open_support, frozen_public.OBJECT_ID
            )
            row["continuation_allowed"] = bool(continuation["allowed"])
            row["continuation_combined_fraction"] = float(continuation["combined_fraction"])
            if not continuation["allowed"]:
                row["first_blocker"] = "CONTINUATION_CORRIDOR"
                rows.append(row); continue

            row["candidate_before_consensus"] = True
            if not consensus["allowed"]:
                row["first_blocker"] = "STATE_CONSENSUS"
                rows.append(row); continue
            row["admissible_candidate"] = True
            row["first_blocker"] = None
            rows.append(row)

    return {
        "rule": "diagnostic replay of the eight frozen FSG6f lattice directions; no action selected or executed here",
        "rows": rows,
        "candidate_before_consensus_count": int(sum(bool(r["candidate_before_consensus"]) for r in rows)),
        "admissible_candidate_count": int(sum(bool(r["admissible_candidate"]) for r in rows)),
        "consensus_rejected_candidate_count": int(sum(bool(r["candidate_before_consensus"] and not r["admissible_candidate"]) for r in rows)),
        "first_blocker_counts": {
            **{
                name: int(sum(r["first_blocker"] == name for r in rows))
                for name in ("POLICY_BOUNDS", "ALREADY_VISITED", "MINIMUM_OPEN_SUPPORT", "CONTINUATION_CORRIDOR", "STATE_CONSENSUS")
            },
            "NONE_ADMISSIBLE": int(sum(r["first_blocker"] is None for r in rows)),
        },
    }


def _decorate_post_candidate_origins(table: dict, frontier: dict, frontier_state: dict,
                                     origin_by_key: dict[tuple[int, int, int], str],
                                     pre_map_keys: set[tuple[int, int, int]], voxel_m: float) -> None:
    """Add origin counts to post rows using exactly the support masks of the frozen geometry."""
    cfg = frozen_public.SURFACE_FRONTIER
    fy, fp = np.asarray(frontier["yaw_deg"]), np.asarray(frontier["pitch_deg"])
    fty, ftp = np.asarray(frontier["target_yaw_deg"]), np.asarray(frontier["target_pitch_deg"])
    fkeys = _frontier_keys(frontier, voxel_m)
    for row in table["rows"]:
        dx, dy = row["direction"]
        if row["first_blocker"] in ("POLICY_BOUNDS", "ALREADY_VISITED"):
            continue
        u = np.array([dx, dy], float); u /= np.linalg.norm(u)
        delta = np.c_[fty - fy, ftp - fp]
        dn = np.linalg.norm(delta, axis=1)
        good = dn > 1e-12
        align = np.zeros(len(delta), float)
        align[good] = (delta[good] / dn[good, None]) @ u
        support = (align >= cfg["alignment_cos_min"]) & np.asarray(frontier_state["open"], bool)
        by_origin = {"PERSISTENT": 0, "UNKNOWN": 0}
        by_map_origin = {"PREEXISTING_MAP_VOXEL": 0, "NEW_MAP_VOXEL": 0}
        for i in np.flatnonzero(support):
            key = tuple(map(int, fkeys[i]))
            origin = origin_by_key.get(key, "UNKNOWN")
            by_origin[origin] = by_origin.get(origin, 0) + 1
            if origin not in ("PERSISTENT", "UNKNOWN"):
                by_map_origin["PREEXISTING_MAP_VOXEL" if key in pre_map_keys else "NEW_MAP_VOXEL"] += 1
        row["open_support_by_frontier_origin"] = by_origin
        row["appeared_open_support_by_map_voxel_origin"] = by_map_origin


def _gate_change_rows(pre_table: dict, post_table: dict) -> list[dict]:
    pre = {tuple(r["direction"]): r for r in pre_table["rows"]}
    post = {tuple(r["direction"]): r for r in post_table["rows"]}
    rows = []
    for key in sorted(pre):
        a, b = pre[key], post[key]
        rows.append({
            "direction": list(key),
            "candidate_gaze_before_deg": a["candidate_gaze_deg"],
            "candidate_gaze_after_deg": b["candidate_gaze_deg"],
            "first_blocker_before": a["first_blocker"],
            "first_blocker_after": b["first_blocker"],
            "open_support_before": a["open_frontier_support_count"],
            "open_support_after": b["open_frontier_support_count"],
            "map_resolved_support_before": a["map_resolved_support_count"],
            "map_resolved_support_after": b["map_resolved_support_count"],
            "boundary_resolved_support_before": a["boundary_resolved_support_count"],
            "boundary_resolved_support_after": b["boundary_resolved_support_count"],
            "minimum_open_support_pass_before": a["minimum_open_support_pass"],
            "minimum_open_support_pass_after": b["minimum_open_support_pass"],
            "continuation_allowed_before": a["continuation_allowed"],
            "continuation_allowed_after": b["continuation_allowed"],
            "state_consensus_allowed_before": a["state_consensus_allowed"],
            "state_consensus_allowed_after": b["state_consensus_allowed"],
            "candidate_before_consensus_before": a["candidate_before_consensus"],
            "candidate_before_consensus_after": b["candidate_before_consensus"],
            "admissible_before": a["admissible_candidate"],
            "admissible_after": b["admissible_candidate"],
            "post_open_support_by_frontier_origin": b["open_support_by_frontier_origin"],
            "post_appeared_open_support_by_map_voxel_origin": b["appeared_open_support_by_map_voxel_origin"],
        })
    return rows


def execute(args) -> dict:
    args.parent = Path(args.parent).resolve()
    args.out = Path(args.out).resolve()
    if args.out.exists():
        raise FileExistsError("output must be new")
    args.out.mkdir(parents=True)
    check_kernel_equivalence()

    m3e, parent3c, pm3c, target_id, objects = _validate_parent(args.parent)

    # Pin all relevant inherited artifacts before the read-only audit.
    parent3e_names = (
        "prediction_manifest.json", m3e["handoff_report"], m3e["active_object_map"],
        f"object_{target_id}_policy_trace.json", "handoff_patch.npz", "scene_graph.json",
    )
    parent3e_hashes = {n: _sha256(args.parent / n) for n in parent3e_names}
    parent3c_names = (
        "prediction_manifest.json", "scene_graph.json", f"object_{target_id}_surface_map.npz",
        f"object_{target_id}_policy_trace.json",
    )
    parent3c_hashes = {n: _sha256(parent3c / n) for n in parent3c_names}

    object_sources: dict[int, Path] = {}
    object_hashes: dict[int, str] = {}
    for oid, obj in objects.items():
        src = _resolve(obj["source"], parent3c)
        object_sources[int(oid)] = src
        object_hashes[int(oid)] = _sha256(src)

    cases = audit3d._all_cases(parent3c, pm3c)
    case_hashes_before = audit3d._case_hashes(cases)
    pre_observations = [audit3d._saved_observation(step, case) for step, case in cases]
    pre_gazes = [tuple(map(float, g)) for g in pm3c.get("selected_object_fixation_gazes_deg", [])]
    if len(pre_gazes) != len(pre_observations):
        raise AssertionError("pre-handoff gaze/history length mismatch")

    handoff_step = int(m3e.get("global_step", -1))
    handoff_case = args.parent / "acquisition" / f"fix_{handoff_step:02d}"
    if not (handoff_case / "calibration.json").is_file() or not (handoff_case / "observation.npz").is_file():
        raise FileNotFoundError("MultiObject-3e handoff acquisition missing")
    handoff_hashes_before = {
        "calibration.json": _sha256(handoff_case / "calibration.json"),
        "observation.npz": _sha256(handoff_case / "observation.npz"),
    }
    handoff_observation = audit3d._saved_observation(handoff_step, handoff_case)
    post_observations = pre_observations + [handoff_observation]
    post_gazes = [tuple(map(float, g)) for g in m3e.get("selected_object_fixation_gazes_deg", [])]
    if len(post_gazes) != len(post_observations) or post_gazes[:-1] != pre_gazes:
        raise AssertionError("post-handoff selected-object history does not extend the pre-state by exactly one gaze")
    if not _same_optional_gaze(post_gazes[-1], m3e.get("handoff_gaze_deg")):
        raise AssertionError("post-handoff final gaze disagrees with handoff gaze")

    sm_pre = load_map(parent3c / f"object_{target_id}_surface_map.npz")
    sm_post = load_map(args.parent / m3e["active_object_map"])
    if set(np.unique(sm_pre.instance_id).tolist()) != {target_id} or set(np.unique(sm_post.instance_id).tolist()) != {target_id}:
        raise AssertionError("selected-object map purity broken")

    pre_history = audit3d._policy_history(pre_observations, target_id)
    post_history = audit3d._policy_history(post_observations, target_id)
    pre_last = pre_observations[-1]
    post_last = post_observations[-1]

    pre_replay = policy.choose_next(
        pre_gazes[-1][0], pre_gazes[-1][1], pre_last["calibration"],
        pre_last["instance_id"], pre_last["raw_support_L"], pre_last["instance_R"], pre_last["raw_support_R"],
        sm_pre.xyz_h, pre_gazes, pre_history, target_id,
    )
    pre_trace = json.loads((parent3c / f"object_{target_id}_policy_trace.json").read_text())
    pre_saved = pre_trace.get("trace", [])[-1]
    _exact_decision_replay(pre_saved, pre_replay, "pre-handoff")

    post_replay = policy.choose_next(
        post_gazes[-1][0], post_gazes[-1][1], post_last["calibration"],
        post_last["instance_id"], post_last["raw_support_L"], post_last["instance_R"], post_last["raw_support_R"],
        sm_post.xyz_h, post_gazes, post_history, target_id,
    )
    post_saved = m3e.get("returned_local_policy_decision", {})
    _exact_decision_replay(post_saved, post_replay, "post-handoff")
    status = progress.reactivation_status(pre_replay, post_replay)
    if status != "LOCAL_POLICY_REACTIVATION_REPRODUCED":
        raise AssertionError("parent reactivation did not reproduce from saved data")

    # Read-only causal counterfactuals.  They return decisions but execute nothing.
    # ATTENTION_ONLY asks what the handoff gaze/evidence would have done without fusion.
    attention_only_replay = policy.choose_next(
        post_gazes[-1][0], post_gazes[-1][1], post_last["calibration"],
        post_last["instance_id"], post_last["raw_support_L"], post_last["instance_R"], post_last["raw_support_R"],
        sm_pre.xyz_h, post_gazes, post_history, target_id,
    )
    # GEOMETRY_ONLY asks what the fused map would have done under the old local attention context.
    geometry_only_replay = policy.choose_next(
        pre_gazes[-1][0], pre_gazes[-1][1], pre_last["calibration"],
        pre_last["instance_id"], pre_last["raw_support_L"], pre_last["instance_R"], pre_last["raw_support_R"],
        sm_post.xyz_h, pre_gazes, pre_history, target_id,
    )

    pre_frontier = frozen_frontier.extract_frontier(
        sm_pre.xyz_h, pre_gazes[-1][0], pre_gazes[-1][1], pre_last["calibration"]
    )
    pre_state = frozen_frontier.classify_frontier_state(pre_frontier, sm_pre.xyz_h, pre_history)
    post_frontier = frozen_frontier.extract_frontier(
        sm_post.xyz_h, post_gazes[-1][0], post_gazes[-1][1], post_last["calibration"]
    )
    post_state = frozen_frontier.classify_frontier_state(post_frontier, sm_post.xyz_h, post_history)

    # The frontier extractor is gaze-local.  These two extractions separate the
    # moved current-view window from the fused-map change without taking action.
    pre_map_post_gaze_frontier = frozen_frontier.extract_frontier(
        sm_pre.xyz_h, post_gazes[-1][0], post_gazes[-1][1], post_last["calibration"]
    )
    post_map_pre_gaze_frontier = frozen_frontier.extract_frontier(
        sm_post.xyz_h, pre_gazes[-1][0], pre_gazes[-1][1], pre_last["calibration"]
    )
    geometric_frontier_factorial = {
        "PRE_MAP_PRE_GAZE": int(len(pre_frontier["strength"])),
        "PRE_MAP_POST_GAZE": int(len(pre_map_post_gaze_frontier["strength"])),
        "POST_MAP_PRE_GAZE": int(len(post_map_pre_gaze_frontier["strength"])),
        "POST_MAP_POST_GAZE": int(len(post_frontier["strength"])),
        "interpretation": "2x2 read-only decomposition of map state and current-gaze extraction window",
    }

    for label, frontier, state, replay in (
        ("pre", pre_frontier, pre_state, pre_replay), ("post", post_frontier, post_state, post_replay)
    ):
        if int(len(frontier["strength"])) != int(replay["frontier_count"]):
            raise AssertionError(f"{label} frontier extraction count mismatch")
        for got, want, name in (
            (state["open_count"], replay["frontier_open_count"], "open"),
            (state["map_resolved_count"], replay["frontier_map_resolved_count"], "map_resolved"),
            (state["boundary_resolved_count"], replay["frontier_boundary_resolved_count"], "boundary_resolved"),
        ):
            if int(got) != int(want):
                raise AssertionError(f"{label} frontier state mismatch for {name}")

    voxel_m = float(frozen_public.SURFACE_FRONTIER["voxel_m"])
    pre_map_arr = _voxel_keys(sm_pre.xyz_h, voxel_m)
    post_map_arr = _voxel_keys(sm_post.xyz_h, voxel_m)
    pre_map_keys = {tuple(map(int, k)) for k in pre_map_arr}
    post_map_keys = {tuple(map(int, k)) for k in post_map_arr}
    if len(pre_map_keys) != int(pre_replay["frontier_voxel_count"]) or len(post_map_keys) != int(post_replay["frontier_voxel_count"]):
        raise AssertionError("frozen map-voxel occupancy does not reproduce frontier_voxel_count")

    patch = np.load(args.parent / "handoff_patch.npz", allow_pickle=False)
    handoff_patch_xyz = np.asarray(patch["xyz_h"], float).reshape(-1, 3)
    patch_key_arr = _voxel_keys(handoff_patch_xyz, voxel_m)
    patch_keys = {tuple(map(int, k)) for k in patch_key_arr}

    pre_map_post_gaze_keys_arr = _frontier_keys(pre_map_post_gaze_frontier, voxel_m)
    pre_map_post_gaze_frontier_keys = {tuple(map(int, k)) for k in pre_map_post_gaze_keys_arr}
    lineage, frontier_details, origin_by_key = _frontier_lineage(
        pre_frontier, pre_state, post_frontier, post_state,
        pre_map_keys, patch_keys, pre_map_post_gaze_frontier_keys, handoff_patch_xyz, voxel_m,
    )
    map_voxel_change = {
        "voxel_m": voxel_m,
        "pre_occupied_voxels": int(len(pre_map_keys)),
        "post_occupied_voxels": int(len(post_map_keys)),
        "persistent_occupied_voxels": int(len(pre_map_keys & post_map_keys)),
        "added_occupied_voxels": int(len(post_map_keys - pre_map_keys)),
        "removed_occupied_voxels": int(len(pre_map_keys - post_map_keys)),
        "handoff_patch_occupied_voxels": int(len(patch_keys)),
        "added_occupied_voxels_directly_present_in_handoff_patch": int(len((post_map_keys - pre_map_keys) & patch_keys)),
    }

    pre_table = _candidate_gate_table(
        pre_gazes[-1][0], pre_gazes[-1][1], pre_last["calibration"], pre_last,
        sm_pre.xyz_h, pre_gazes, pre_history, target_id, pre_frontier, pre_state,
    )
    post_table = _candidate_gate_table(
        post_gazes[-1][0], post_gazes[-1][1], post_last["calibration"], post_last,
        sm_post.xyz_h, post_gazes, post_history, target_id, post_frontier, post_state,
        origin_by_key,
    )
    _decorate_post_candidate_origins(post_table, post_frontier, post_state, origin_by_key, pre_map_keys, voxel_m)
    for label, table, replay in (("pre", pre_table, pre_replay), ("post", post_table, post_replay)):
        if int(table["candidate_before_consensus_count"]) != int(replay["candidates_before_consensus_count"]):
            raise AssertionError(f"{label} candidate gate ledger disagrees on before-consensus count")
        if int(table["consensus_rejected_candidate_count"]) != int(replay["consensus_rejected_candidate_count"]):
            raise AssertionError(f"{label} candidate gate ledger disagrees on consensus-rejected count")
        if int(table["admissible_candidate_count"]) != int(len(replay.get("candidates", []))):
            raise AssertionError(f"{label} candidate gate ledger disagrees on admissible count")

    gate_changes = _gate_change_rows(pre_table, post_table)
    reactivated_rows = [r for r in gate_changes if (not r["candidate_before_consensus_before"] and r["candidate_before_consensus_after"])]
    admissible_new_rows = [r for r in gate_changes if (not r["admissible_before"] and r["admissible_after"])]

    report = {
        "selected_object_id": int(target_id),
        "question": public.PUBLIC_SPEC["question"],
        "reactivation_status": status,
        "pre_policy_decision": pre_replay,
        "post_policy_decision": post_replay,
        "counterfactual_policy_decisions": {
            "ATTENTION_ONLY_PRE_FUSION_MAP": attention_only_replay,
            "GEOMETRY_ONLY_OLD_ATTENTION_CONTEXT": geometry_only_replay,
        },
        "geometric_frontier_factorial": geometric_frontier_factorial,
        "pre_policy_replayed_exactly": True,
        "post_policy_replayed_exactly": True,
        "map_points_before": int(len(sm_pre.xyz_h)),
        "map_points_after": int(len(sm_post.xyz_h)),
        "map_point_gain": int(len(sm_post.xyz_h) - len(sm_pre.xyz_h)),
        "map_voxel_change": map_voxel_change,
        "frontier_lineage": lineage,
        "candidate_gate_before": pre_table,
        "candidate_gate_after": post_table,
        "candidate_gate_changes": gate_changes,
        "directions_newly_reaching_before_consensus": [r["direction"] for r in reactivated_rows],
        "directions_newly_admissible": [r["direction"] for r in admissible_new_rows],
        "handoff_patch_points": int(len(handoff_patch_xyz)),
        "handoff_gaze_deg": m3e.get("handoff_gaze_deg"),
        "returned_next_gaze_deg": post_replay.get("next_gaze_deg"),
        "returned_action_executed": False,
        "interpretation_is_descriptive": True,
        "experiment_stop": progress.experiment_stop(),
        "next_stage": progress.next_stage(),
    }
    report_name = f"object_{target_id}_frontier_reactivation_report.json"
    json_write(args.out / report_name, report)

    # Machine-readable frontier lineage for later audits; still read-only.
    pre_keys = _frontier_keys(pre_frontier, voxel_m)
    post_keys = _frontier_keys(post_frontier, voxel_m)
    pre_codes = np.array([{"OPEN": 0, "MAP_RESOLVED": 1, "BOUNDARY_RESOLVED": 2}[_state_name(pre_state, i)] for i in range(len(pre_keys))], np.uint8)
    post_codes = np.array([{"OPEN": 0, "MAP_RESOLVED": 1, "BOUNDARY_RESOLVED": 2}[_state_name(post_state, i)] for i in range(len(post_keys))], np.uint8)
    np.savez_compressed(
        args.out / "frontier_reactivation.npz",
        pre_source_voxel_key=pre_keys,
        pre_source_xyz_h=np.asarray(pre_frontier["xyz_h"]),
        pre_target_xyz_h=np.asarray(pre_frontier["target_xyz_h"]),
        pre_state_code=pre_codes,
        post_source_voxel_key=post_keys,
        post_source_xyz_h=np.asarray(post_frontier["xyz_h"]),
        post_target_xyz_h=np.asarray(post_frontier["target_xyz_h"]),
        post_state_code=post_codes,
    )
    json_write(args.out / "frontier_reactivation_details.json", {"rows": frontier_details})

    # Verify no inherited artifact changed during this read-only audit.
    if {n: _sha256(args.parent / n) for n in parent3e_names} != parent3e_hashes:
        raise AssertionError("MultiObject-3e parent changed during audit")
    if {n: _sha256(parent3c / n) for n in parent3c_names} != parent3c_hashes:
        raise AssertionError("MultiObject-3c scene parent changed during audit")
    if audit3d._case_hashes(cases) != case_hashes_before:
        raise AssertionError("pre-handoff selected-object history changed during audit")
    if {
        "calibration.json": _sha256(handoff_case / "calibration.json"),
        "observation.npz": _sha256(handoff_case / "observation.npz"),
    } != handoff_hashes_before:
        raise AssertionError("handoff acquisition changed during audit")
    for oid, src in object_sources.items():
        if _sha256(src) != object_hashes[oid]:
            raise AssertionError(f"scene object {oid} changed during audit")

    manifest = {
        "schema": public.SPEC_ID,
        "public_spec_sha256": public.public_digest(),
        "parent_spec": public.PARENT_SPEC_ID,
        "parent_record": str(args.parent),
        "scene_parent_record": str(parent3c),
        "seed": public.SEED,
        "fixture": public.FIXTURE,
        "fixed_head": True,
        "static_scene": True,
        "truth_opened": False,
        "selected_object_id": int(target_id),
        "preexisting_object_ids": [int(x) for x in m3e.get("preexisting_object_ids", [])],
        "no_acquisition": True,
        "acquisitions_added": 0,
        "fusion_iterations_added": 0,
        "growth_iterations_added": 0,
        "returned_local_action_executed": False,
        "automatic_handoff_loop": False,
        "automatic_scene_scheduler": False,
        "revisit_scheduler_used": False,
        "watchdog_changed": False,
        "quality_gate_used": False,
        "new_threshold_added": False,
        "preexisting_objects_read_only": True,
        "selected_object_read_only": True,
        "pre_policy_replayed_exactly": True,
        "post_policy_replayed_exactly": True,
        "frontier_identity_rule": public.PUBLIC_SPEC["frontier_identity"],
        "frozen_frontier_voxel_m": voxel_m,
        "reactivation_status": status,
        "counterfactual_policy_summary": {
            "ATTENTION_ONLY_PRE_FUSION_MAP": {
                "stop": attention_only_replay.get("stop"),
                "reason": attention_only_replay.get("reason"),
                "frontier_count": attention_only_replay.get("frontier_count"),
                "frontier_open_count": attention_only_replay.get("frontier_open_count"),
                "candidates_before_consensus_count": attention_only_replay.get("candidates_before_consensus_count"),
                "next_gaze_deg": attention_only_replay.get("next_gaze_deg"),
            },
            "GEOMETRY_ONLY_OLD_ATTENTION_CONTEXT": {
                "stop": geometry_only_replay.get("stop"),
                "reason": geometry_only_replay.get("reason"),
                "frontier_count": geometry_only_replay.get("frontier_count"),
                "frontier_open_count": geometry_only_replay.get("frontier_open_count"),
                "candidates_before_consensus_count": geometry_only_replay.get("candidates_before_consensus_count"),
                "next_gaze_deg": geometry_only_replay.get("next_gaze_deg"),
            },
        },
        "geometric_frontier_factorial": geometric_frontier_factorial,
        "map_points_before": int(len(sm_pre.xyz_h)),
        "map_points_after": int(len(sm_post.xyz_h)),
        "map_voxel_change": map_voxel_change,
        "frontier_lineage_summary": lineage,
        "candidate_before_consensus_before": int(pre_table["candidate_before_consensus_count"]),
        "candidate_before_consensus_after": int(post_table["candidate_before_consensus_count"]),
        "admissible_candidates_before": int(pre_table["admissible_candidate_count"]),
        "admissible_candidates_after": int(post_table["admissible_candidate_count"]),
        "directions_newly_reaching_before_consensus": [r["direction"] for r in reactivated_rows],
        "directions_newly_admissible": [r["direction"] for r in admissible_new_rows],
        "returned_next_gaze_deg": post_replay.get("next_gaze_deg"),
        "report": report_name,
        "frontier_npz": "frontier_reactivation.npz",
        "frontier_details": "frontier_reactivation_details.json",
        "parent3e_hashes": parent3e_hashes,
        "parent3c_hashes": parent3c_hashes,
        "scene_object_sha256_before": {str(k): v for k, v in object_hashes.items()},
        "scene_object_sha256_after": {str(k): _sha256(v) for k, v in object_sources.items()},
        "pre_observation_input_hashes": case_hashes_before,
        "handoff_observation_input_hashes": handoff_hashes_before,
        "experiment_stop": progress.experiment_stop(),
        "next_stage": public.NEXT_STAGE,
        "structural_fails": [],
    }
    json_write(args.out / "prediction_manifest.json", manifest)
    print("[multiobject3f-audit] MULTIOBJECT3F_COMPLETE " + json.dumps({
        "selected_object_id": int(target_id),
        "reactivation_status": status,
        "map_voxels_before": map_voxel_change["pre_occupied_voxels"],
        "map_voxels_after": map_voxel_change["post_occupied_voxels"],
        "frontier_before": lineage["pre_frontier_count"],
        "frontier_after": lineage["post_frontier_count"],
        "frontier_appeared": lineage["appeared_frontier_source_voxels"],
        "frontier_persistent": lineage["persistent_frontier_source_voxels"],
        "frontier_disappeared": lineage["disappeared_frontier_source_voxels"],
        "frontier_factorial": geometric_frontier_factorial,
        "attention_only_candidates": attention_only_replay.get("candidates_before_consensus_count"),
        "geometry_only_candidates": geometry_only_replay.get("candidates_before_consensus_count"),
        "candidates_before": pre_table["candidate_before_consensus_count"],
        "candidates_after": post_table["candidate_before_consensus_count"],
        "structural_fails": [],
    }, sort_keys=True), flush=True)
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--parent", required=True)
    ap.add_argument("--out", required=True)
    execute(ap.parse_args())


if __name__ == "__main__":
    main()
