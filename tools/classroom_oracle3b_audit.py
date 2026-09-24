"""Post-hoc gap anatomy for Classroom-Oracle-3b.

This program never imports or calls the controller.  It consumes the completed
Oracle-3 audit and the frozen Oracle-1 reachable-surface reference.  Its target
is the dominant Oracle-3 residue: truth misses classified
NOT_SHORELINE / COMPLEMENT_NONSHORELINE.

The central diagnostic is *ring depth*: on the frozen 0.1-degree Cyclopean
chart, support has depth 0, the current one-ring shoreline has depth 1, and a
miss at depth k would require k successive 8-connected support dilations before
it became adjacent to support.  This is a measurement, not a proposed policy.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import classroom_oracle3b_public as public
import classroom_oracle3_public as o3public


def _json(path: Path) -> Any:
    return json.loads(path.read_text())


def _write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def _new_dir(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        raise FileExistsError(f"output must be new or empty: {path}")
    path.mkdir(parents=True, exist_ok=True)


def _load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def _decode(codes: np.ndarray, names: tuple[str, ...]) -> np.ndarray:
    a = np.asarray(codes, np.int64)
    if a.size and (int(a.min()) < 0 or int(a.max()) >= len(names)):
        raise ValueError("code outside declared Oracle-3 vocabulary")
    return np.asarray([names[int(v)] for v in a], dtype=object)


def _positive_step(values: np.ndarray) -> float | None:
    u = np.unique(np.round(np.asarray(values, float), 9))
    if len(u) < 2:
        return None
    d = np.diff(u)
    d = d[d > 1e-7]
    if not len(d):
        return None
    # The reference is a regular lattice.  The smallest repeated increment is
    # the safest estimate when some angles are absent for individual objects.
    return float(np.min(d))


def _reference_lattice(truth_path: Path) -> dict[str, float]:
    with np.load(truth_path, allow_pickle=False) as z:
        a = np.asarray(z["yaw_pitch_deg"], float)
    if a.ndim != 2 or a.shape[1] != 2 or not len(a):
        raise ValueError("bad reachable-sample angular reference")
    ys = _positive_step(a[:, 0])
    ps = _positive_step(a[:, 1])
    if ys is None or ps is None or not math.isclose(ys, ps, rel_tol=0.0, abs_tol=1e-6):
        raise ValueError(f"reachable reference is not a common regular angular lattice: yaw={ys}, pitch={ps}")
    return {
        "yaw0_deg": float(np.min(a[:, 0])),
        "pitch0_deg": float(np.min(a[:, 1])),
        "step_deg": float((ys + ps) / 2.0),
    }


def _cell_indices(angles: np.ndarray, lattice: dict[str, float]) -> tuple[np.ndarray, np.ndarray]:
    a = np.asarray(angles, float)
    step = float(lattice["step_deg"])
    x = np.rint((a[:, 0] - float(lattice["yaw0_deg"])) / step).astype(np.int64)
    y = np.rint((a[:, 1] - float(lattice["pitch0_deg"])) / step).astype(np.int64)
    return y, x


def _component_labels(angles: np.ndarray, lattice: dict[str, float]) -> tuple[np.ndarray, dict[int, dict[str, int]]]:
    if not len(angles):
        return np.empty(0, np.int32), {}
    y, x = _cell_indices(angles, lattice)
    y0, x0 = int(y.min()), int(x.min())
    h, w = int(y.max() - y0 + 1), int(x.max() - x0 + 1)
    mask = np.zeros((h, w), np.uint8)
    mask[y - y0, x - x0] = 1
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    labels = lab[y - y0, x - x0].astype(np.int32)
    meta: dict[int, dict[str, int]] = {}
    for k in range(1, n):
        meta[k] = {
            "cell_count": int(stats[k, cv2.CC_STAT_AREA]),
            "x_min_lattice": int(x0 + stats[k, cv2.CC_STAT_LEFT]),
            "x_max_lattice": int(x0 + stats[k, cv2.CC_STAT_LEFT] + stats[k, cv2.CC_STAT_WIDTH] - 1),
            "y_min_lattice": int(y0 + stats[k, cv2.CC_STAT_TOP]),
            "y_max_lattice": int(y0 + stats[k, cv2.CC_STAT_TOP] + stats[k, cv2.CC_STAT_HEIGHT] - 1),
        }
    return labels, meta


def _distance_fields(state: dict[str, np.ndarray]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    support = np.asarray(state["support"], bool)
    shoreline = np.asarray(state["shoreline"], bool)
    if not support.any():
        raise ValueError("controller support mask is empty")
    # distanceTransform measures distance from non-zero cells to the nearest zero.
    # Therefore ~support gives zero exactly on support. DIST_C is Chebyshev
    # distance: the exact number of 8-connected one-cell dilations required.
    ring = cv2.distanceTransform((~support).astype(np.uint8), cv2.DIST_C, 3)
    euclid_support = cv2.distanceTransform((~support).astype(np.uint8), cv2.DIST_L2, 5)
    if shoreline.any():
        euclid_shore = cv2.distanceTransform((~shoreline).astype(np.uint8), cv2.DIST_L2, 5)
    else:
        euclid_shore = np.full(support.shape, np.nan, np.float32)
    return ring, euclid_support, euclid_shore


def _nearest_fixation_deg(centroid: tuple[float, float], gazes: list[list[float]]) -> float | None:
    if not gazes:
        return None
    g = np.asarray(gazes, float)
    d = g - np.asarray(centroid, float)[None, :]
    return float(np.sqrt(np.sum(d * d, axis=1)).min())


def _quantiles(a: np.ndarray) -> dict[str, float | None]:
    x = np.asarray(a, float)
    x = x[np.isfinite(x)]
    if not len(x):
        return {"min": None, "median": None, "p90": None, "max": None}
    return {
        "min": float(np.min(x)),
        "median": float(np.median(x)),
        "p90": float(np.quantile(x, 0.90)),
        "max": float(np.max(x)),
    }


def _obs_label(state: dict[str, np.ndarray], y: int, x: int) -> str:
    if bool(state["target_no_depth"][y, x]):
        return "TARGET_SEEN_NO_DEPTH"
    if bool(state["target_with_depth"][y, x]):
        return "TARGET_SEEN_WITH_DEPTH"
    if bool(state["mixed"][y, x]):
        return "MIXED_TARGET_NONTARGET"
    if bool(state["nontarget_only"][y, x]):
        return "NONTARGET_ONLY"
    if bool(state["never"][y, x]):
        return "NEVER_OBSERVED"
    if bool(state["seen_any"][y, x]):
        return "OTHER_OBSERVED"
    return "UNCLASSIFIED"


def _hist(values: list[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for v in values:
        out[v] = out.get(v, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))


def _ring_curve(rings: np.ndarray) -> list[dict[str, float | int]]:
    r = np.asarray(rings, float)
    r = r[np.isfinite(r)]
    if not len(r):
        return []
    ri = np.ceil(r - 1e-7).astype(int)
    max_k = int(ri.max())
    # Preserve the full curve when compact; otherwise report 1..20 and the max.
    ks = list(range(1, min(max_k, 20) + 1))
    if max_k > 20:
        ks.append(max_k)
    return [{"rings": int(k), "samples_reached": int((ri <= k).sum()), "fraction": float((ri <= k).mean())} for k in ks]


def _audit_object(iid: int, o3: Path, lattice: dict[str, float]) -> dict[str, Any]:
    od = o3 / "objects" / f"instance_{iid:04d}"
    state = _load_npz(od / "controller_state.npz")
    misses = _load_npz(od / "truth_misses.npz")
    truth_audit = _json(od / "truth_audit.json")
    control = _json(od / "control_audit.json")

    reasons = _decode(misses["first_reason_code"], tuple(o3public.CYCLOPEAN_FIRST_REJECTION_REASONS))
    subtypes = _decode(misses["subtype_code"], tuple(o3public.TRUTH_SUBTYPES))
    select = (reasons == public.TARGET_FIRST_REASON) & (subtypes == public.TARGET_SUBTYPE)

    angles = np.asarray(misses["yaw_pitch_deg"], float)[select]
    xyz = np.asarray(misses["xyz_h"], float)[select]
    cy = np.asarray(misses["cell_y"], np.int64)[select]
    cx = np.asarray(misses["cell_x"], np.int64)[select]
    ok = np.asarray(misses["cell_in_chart"], bool)[select]
    if not np.all(ok):
        raise RuntimeError(f"instance {iid}: complement-nonshoreline sample unexpectedly out of chart")

    ring_field, support_dist, shore_dist = _distance_fields(state)
    grid = float(np.asarray(state["grid_deg"]).item())
    rings = ring_field[cy, cx]
    support_deg = support_dist[cy, cx] * grid
    shore_deg = shore_dist[cy, cx] * grid
    obs = [_obs_label(state, int(y), int(x)) for y, x in zip(cy, cx)]

    labels, meta = _component_labels(angles, lattice)
    components: list[dict[str, Any]] = []
    for label in sorted(meta):
        s = labels == label
        aa = angles[s]
        rr = rings[s]
        sd = support_deg[s]
        shd = shore_deg[s]
        oo = [obs[j] for j in np.flatnonzero(s)]
        cen = (float(np.mean(aa[:, 0])), float(np.mean(aa[:, 1])))
        row = {
            "component_id": int(label),
            "truth_sample_count": int(s.sum()),
            "unique_reference_cells": int(meta[label]["cell_count"]),
            "centroid_yaw_pitch_deg": [cen[0], cen[1]],
            "yaw_span_deg": [float(np.min(aa[:, 0])), float(np.max(aa[:, 0]))],
            "pitch_span_deg": [float(np.min(aa[:, 1])), float(np.max(aa[:, 1]))],
            "bbox_width_deg": float(np.max(aa[:, 0]) - np.min(aa[:, 0]) + lattice["step_deg"]),
            "bbox_height_deg": float(np.max(aa[:, 1]) - np.min(aa[:, 1]) + lattice["step_deg"]),
            "support_ring_depth": _quantiles(rr),
            "support_distance_deg": _quantiles(sd),
            "shoreline_distance_deg": _quantiles(shd),
            "observation_state_histogram": _hist(oo),
            "never_observed_fraction": float(sum(v == "NEVER_OBSERVED" for v in oo) / len(oo)),
            "target_seen_fraction": float(sum(v.startswith("TARGET_SEEN") or v == "MIXED_TARGET_NONTARGET" for v in oo) / len(oo)),
            "nearest_completed_fixation_deg": _nearest_fixation_deg(cen, control.get("visited_gazes_deg", [])),
        }
        components.append(row)
    components.sort(key=lambda r: (-int(r["truth_sample_count"]), int(r["component_id"])))

    return {
        "instance_id": int(iid),
        "object_name": truth_audit.get("object_name"),
        "oracle3_missed_samples": int(truth_audit.get("missed_samples", len(misses.get("xyz_h", [])))),
        "complement_nonshoreline_samples": int(len(angles)),
        "fraction_of_object_misses": float(len(angles) / max(1, int(truth_audit.get("missed_samples", 0)))),
        "component_count": int(len(components)),
        "reference_lattice_step_deg": float(lattice["step_deg"]),
        "cyclopean_grid_deg": grid,
        "support_ring_depth_all_samples": _quantiles(rings),
        "support_distance_deg_all_samples": _quantiles(support_deg),
        "shoreline_distance_deg_all_samples": _quantiles(shore_deg),
        "observation_state_histogram_all_samples": _hist(obs),
        "never_observed_fraction_all_samples": float(sum(v == "NEVER_OBSERVED" for v in obs) / len(obs)) if obs else None,
        "target_seen_fraction_all_samples": float(sum(v.startswith("TARGET_SEEN") or v == "MIXED_TARGET_NONTARGET" for v in obs) / len(obs)) if obs else None,
        "halo_reach_curve": _ring_curve(rings),
        "components": components,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--oracle3-audit", type=Path, default=Path(public.ORACLE3_AUDIT_DEFAULT))
    ap.add_argument("--oracle1-run", type=Path, default=Path(public.ORACLE1_RUN_DEFAULT))
    ap.add_argument("--out", type=Path, default=Path(public.DEFAULT_OUT))
    args = ap.parse_args()

    bad = public.self_test()
    if bad:
        raise RuntimeError("public self-test failed: " + "; ".join(bad))

    o3 = args.oracle3_audit.resolve()
    o1 = args.oracle1_run.resolve()
    out = args.out.resolve()
    _new_dir(out)
    (out / "objects").mkdir()

    m3 = _json(o3 / "manifest.json")
    a3 = _json(o3 / "audit.json")
    if not m3.get("controller_phase_complete") or not m3.get("truth_phase_complete"):
        raise RuntimeError("Oracle-3 audit is not complete")
    if not a3.get("all_final_fsg6f_replays_exact"):
        raise RuntimeError("Oracle-3 replay baseline is not exact")
    focus_ids = [int(v) for v in a3.get("focus_instance_ids", [])]
    if len(focus_ids) != 6:
        raise RuntimeError(f"Oracle-3 focus set must contain six objects, got {focus_ids}")

    truth_path = o1 / "bootstrap" / "evaluation_only" / "reachable_samples.npz"
    if not truth_path.exists():
        raise FileNotFoundError(truth_path)
    lattice = _reference_lattice(truth_path)

    object_ids = [int(r["instance_id"]) for r in a3.get("objects", [])]
    if len(object_ids) != 25:
        raise RuntimeError(f"Oracle-3 must contain 25 object rows, got {len(object_ids)}")

    manifest = {
        "schema": "ClassroomOracle3b-gap-anatomy-v1",
        "spec_id": public.SPEC_ID,
        "public_digest": public.public_digest(),
        "oracle3_audit": str(o3),
        "oracle1_run": str(o1),
        "focus_instance_ids": focus_ids,
        "focus_source": public.FOCUS_SOURCE,
        "reference_lattice": lattice,
        "posthoc_only": True,
        "controller_executed": False,
        "new_acquisitions": 0,
        "new_fixations": 0,
        "new_fusion": 0,
        "blender_launched": False,
    }
    _write(out / "manifest.json", manifest)

    rows: list[dict[str, Any]] = []
    for iid in object_ids:
        row = _audit_object(iid, o3, lattice)
        _write(out / "objects" / f"instance_{iid:04d}" / "gap_anatomy.json", row)
        rows.append(row)

    focus_rows = [next(r for r in rows if r["instance_id"] == iid) for iid in focus_ids]
    all_ring: list[float] = []
    all_obs: list[str] = []
    total_misses = 0
    total_gap = 0
    total_components = 0
    for row in rows:
        total_misses += int(row["oracle3_missed_samples"])
        total_gap += int(row["complement_nonshoreline_samples"])
        total_components += int(row["component_count"])
        # Re-load compact arrays to preserve exact sample weighting in aggregate.
        od = o3 / "objects" / f"instance_{int(row['instance_id']):04d}"
        st = _load_npz(od / "controller_state.npz")
        tm = _load_npz(od / "truth_misses.npz")
        reasons = _decode(tm["first_reason_code"], tuple(o3public.CYCLOPEAN_FIRST_REJECTION_REASONS))
        subtypes = _decode(tm["subtype_code"], tuple(o3public.TRUTH_SUBTYPES))
        sel = (reasons == public.TARGET_FIRST_REASON) & (subtypes == public.TARGET_SUBTYPE)
        cy = np.asarray(tm["cell_y"], int)[sel]
        cx = np.asarray(tm["cell_x"], int)[sel]
        if len(cy):
            ring, _, _ = _distance_fields(st)
            all_ring.extend(ring[cy, cx].astype(float).tolist())
            all_obs.extend(_obs_label(st, int(y), int(x)) for y, x in zip(cy, cx))

    result = {
        "schema": "ClassroomOracle3b-result-v1",
        "spec_id": public.SPEC_ID,
        "target_reason": public.TARGET_FIRST_REASON,
        "target_subtype": public.TARGET_SUBTYPE,
        "objects": rows,
        "focus_instance_ids": focus_ids,
        "focus_objects": focus_rows,
        "aggregate": {
            "oracle3_missed_samples": int(total_misses),
            "complement_nonshoreline_samples": int(total_gap),
            "fraction_of_all_misses": float(total_gap / max(1, total_misses)),
            "component_count": int(total_components),
            "support_ring_depth_all_samples": _quantiles(np.asarray(all_ring, float)),
            "observation_state_histogram": _hist(all_obs),
            "never_observed_fraction": float(sum(v == "NEVER_OBSERVED" for v in all_obs) / len(all_obs)) if all_obs else None,
            "target_seen_fraction": float(sum(v.startswith("TARGET_SEEN") or v == "MIXED_TARGET_NONTARGET" for v in all_obs) / len(all_obs)) if all_obs else None,
            "halo_reach_curve": _ring_curve(np.asarray(all_ring, float)),
        },
        "interpretation_contract": [
            "Ring depth is descriptive: k means k successive 8-connected support dilations would be required before that miss became adjacent to support.",
            "The halo reach curve is a counterfactual geometry measurement only; Oracle-3b does not change the Cyclopean eligibility rule.",
            "Connected components are defined on the frozen reachable-sample angular lattice, not the finer Cyclopean raster, so 0.25-degree truth sampling is not spuriously fragmented on a 0.1-degree chart.",
            "Observation-state composition distinguishes genuinely unseen detached surface from detached surface already imaged but not represented in the map.",
            "No numerical value is a PASS/FAIL threshold.",
        ],
    }
    _write(out / "gap_anatomy.json", result)
    print("[classroom-oracle3b] COMPLETE", json.dumps({
        "objects": len(rows),
        "focus": focus_ids,
        "gap_samples": total_gap,
        "components": total_components,
        "ring_depth": result["aggregate"]["support_ring_depth_all_samples"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
