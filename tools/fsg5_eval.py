"""Post-hoc evaluation of one FSG5 active curved-surface run."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import cv2

import fsg5_public as public
import fsg5_scene as scene
from fsg3_surface_map import load_map
from fsg_geometry import json_write


def spatial_coverage(fixture: str, xyz: np.ndarray) -> float:
    truth = scene.truth_points(fixture)
    cell = scene.TRUTH_COVER_RADIUS_M
    bins: dict[tuple[int, int, int], list[np.ndarray]] = {}
    for p in np.asarray(xyz, float):
        if np.isfinite(p).all():
            bins.setdefault(tuple(np.floor(p / cell).astype(int)), []).append(p)
    hit = 0
    for q in truth:
        k = tuple(np.floor(q / cell).astype(int)); best = cell
        for a in (-1, 0, 1):
            for b in (-1, 0, 1):
                for c in (-1, 0, 1):
                    for p in bins.get((k[0] + a, k[1] + b, k[2] + c), ()):
                        best = min(best, float(np.linalg.norm(q - p)))
        hit += best < cell
    return float(hit / len(truth))


def write_visual(path: Path, fixture: str, maps: list, coverage: list[float], yaws: list[float]) -> None:
    n = len(maps); W = 300 * n; H = 330
    canvas = np.full((H, W, 3), 245, np.uint8)
    s = scene.spec(fixture)
    t0, t1 = float(s["theta_min_deg"]), float(s["theta_max_deg"])
    for k, (m, cov, yaw) in enumerate(zip(maps, coverage, yaws)):
        th, yy, _ = scene.surface_parameters(fixture, m.xyz_h)
        th = np.degrees(th); x0 = 300 * k
        cv2.rectangle(canvas, (x0 + 20, 45), (x0 + 280, 285), (210, 210, 210), 1)
        cv2.putText(canvas, f"active {k}: yaw {yaw:.1f}", (x0 + 25, 20), cv2.FONT_HERSHEY_SIMPLEX, .42, (20, 20, 20), 1, cv2.LINE_AA)
        cv2.putText(canvas, f"coverage {100 * cov:.1f}%", (x0 + 25, 38), cv2.FONT_HERSHEY_SIMPLEX, .42, (20, 20, 20), 1, cv2.LINE_AA)
        px = np.clip((th - t0) / (t1 - t0) * 240 + x0 + 30, x0 + 30, x0 + 270).astype(int)
        py = np.clip((.5 - yy / s["height_m"]) * 210 + 60, 60, 270).astype(int)
        strong = m.support_count > 1
        for X, Y, S in zip(px[::2], py[::2], strong[::2]):
            canvas[Y, X] = (25, 25, 25) if S else (145, 145, 145)
    cv2.imwrite(str(path), canvas)


def evaluate(root: Path, out: Path, mode: str) -> dict:
    root = root.resolve(); out = out.resolve()
    if out.exists():
        raise FileExistsError("output must be new")
    manifest = json.loads((root / "prediction_manifest.json").read_text())
    if manifest.get("truth_opened") is not False or manifest.get("public_spec_sha256") != public.public_digest():
        raise ValueError("prediction provenance invalid")
    fixture = manifest.get("fixture"); seed = int(manifest.get("seed"))
    if fixture not in public.FIXTURES or seed not in public.SEEDS:
        raise ValueError("wrong FSG5 fixture/seed")
    if manifest.get("instrument") != public.INSTRUMENT_ID:
        raise ValueError("wrong FSG1 instrument")
    yaws = [float(x) for x in manifest["fixation_yaws_deg"]]
    maps = []
    for step in range(len(yaws)):
        maps.append(load_map(root / "maps" / f"map_{step:02d}.npz"))
        acq = root / "acquisitions" / f"fix_{step:02d}"; case = acq / f"fix_{step:02d}"
        rr = json.loads((acq / "run.json").read_text())
        if (rr.get("truth_spec_sha256") != scene.truth_digest(fixture) or rr.get("fixture") != fixture
                or int(rr.get("seed")) != seed or abs(float(rr["yaw_deg"]) - yaws[step]) > 1e-8):
            raise ValueError("acquisition truth spec/fixture/seed/yaw mismatch")
        with np.load(case / "evaluation_only" / "mesh.npz", allow_pickle=False) as f:
            mesh = {k: f[k] for k in f.files}
        scene.validate_mesh(fixture, mesh)
    out.mkdir(parents=True)
    cov = [spatial_coverage(fixture, m.xyz_h) for m in maps]
    gains = [cov[0]] + [cov[i] - cov[i - 1] for i in range(1, len(cov))]
    closure = [None]
    for i in range(1, len(cov)):
        rem = max(0.0, 1.0 - cov[i - 1])
        closure.append(None if rem <= 1e-12 else float(gains[i] / rem))
    final = maps[-1]
    err = scene.surface_distance(fixture, final.xyz_h)
    signed = scene.signed_radial_error(fixture, final.xyz_h)
    supported = final.support_count >= 2
    supported_count = int(supported.sum())
    supported_bias = float(np.median(signed[supported])) if supported_count else None
    patch = manifest["patch_stats"]; assoc = manifest["association_stats"]
    metrics = {
        "schema": "FSG5-run-evaluation-v1",
        "profile": manifest["profile"], "fixture": fixture, "seed": seed,
        "instrument": manifest["instrument"], "fixation_count": len(yaws),
        "fixation_yaws_deg": yaws, "termination_reason": manifest["termination_reason"],
        "patch_stats": patch, "association_stats": assoc,
        "truth_coverage_by_fixation": cov, "truth_coverage_gain_by_fixation": gains,
        "residual_closure_fraction_by_fixation": closure,
        "truth_coverage_seed": cov[0], "truth_coverage_final": cov[-1],
        "truth_coverage_gain_over_seed": cov[-1] - cov[0],
        "map_points": int(len(final.xyz_h)),
        "map_support_histogram": {str(int(k)): int(v) for k, v in zip(*np.unique(final.support_count, return_counts=True))},
        "map_surface_median_m": float(np.median(err)),
        "map_surface_p95_m": float(np.percentile(err, 95)),
        "map_signed_radial_median_m": float(np.median(signed)),
        "supported_surfels": supported_count,
        "supported_signed_radial_median_m": supported_bias,
        "primary_camera_samples": int(manifest["primary_camera_samples"]),
        "per_fixation_novelty_and_gain_gated": False,
    }
    t = public.TARGETS; fails = []
    if metrics["map_surface_median_m"] > t["map_surface_median_max_m"]:
        fails.append("final map median curved-surface error")
    if metrics["map_surface_p95_m"] > t["map_surface_p95_max_m"]:
        fails.append("final map p95 curved-surface error")
    if set(final.instance_id.tolist()) != {public.OBJECT_ID}:
        fails.append("map contains non-object instance")
    if supported_count < t["supported_surfels_min"]:
        fails.append("too few multi-look surfels for curvature-bias check")
    elif abs(float(supported_bias)) > t["supported_signed_radial_bias_abs_max_m"]:
        fails.append("multi-look fusion radially biases curved surface")
    if not (t["active_fixation_count_min"] <= len(yaws) <= t["active_fixation_count_max"]):
        fails.append("active fixation count outside prospective range")
    if manifest["termination_reason"] != "no_frontier":
        fails.append("active policy did not terminate by resolving the frontier")
    dy = np.abs(np.diff(yaws))
    if len(dy) and (np.any(dy <= 0) or not np.allclose(dy, public.POLICY["step_deg"], atol=1e-8)):
        fails.append("active saccade differs from frozen 5-degree step or revisits")
    for p in patch:
        if p["object_reference_count"] < 100:
            fails.append(f"{p['patch_id']} too little oracle object support")
        if p["object_measurement_fraction"] is None or p["object_measurement_fraction"] < t["patch_object_coverage_min"]:
            fails.append(f"{p['patch_id']} object measurement coverage")
    for i, a in enumerate(assoc[1:], start=1):
        if a["matched"] < t["minimum_matched_points_each"]:
            fails.append(f"{a['patch_id']} too few overlap matches")
        if a["overlap_median_distance_m"] is None or a["overlap_median_distance_m"] > t["overlap_median_distance_max_m"]:
            fails.append(f"{a['patch_id']} overlap median")
        if a["overlap_p95_distance_m"] is None or a["overlap_p95_distance_m"] > t["overlap_p95_distance_max_m"]:
            fails.append(f"{a['patch_id']} overlap p95")
        if not a.get("idempotent_replay", False):
            fails.append(f"{a['patch_id']} replay not idempotent")
        if gains[i] < -t["coverage_drop_tolerance"]:
            fails.append(f"coverage decreased materially at fixation {i}")
    if cov[-1] < t["final_truth_coverage_min"]:
        fails.append("active final curved-surface coverage")
    if cov[-1] - cov[0] < t["truth_coverage_gain_over_seed_min"]:
        fails.append("active curved-surface coverage gain over seed")
    metrics["fails"] = fails
    metrics["status"] = "FSG5_CURVED_RUN_PASS" if not fails else "FSG5_CURVED_RUN_FAIL"
    json_write(out / "metrics.json", metrics)
    write_visual(out / "growth_truth.png", fixture, maps, cov, yaws)
    print("[fsg5-eval] " + metrics["status"], json.dumps(metrics, sort_keys=True), flush=True)
    return metrics


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("record", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--mode", choices=("smoke", "full"), required=True)
    a = ap.parse_args()
    m = evaluate(a.record, a.out, a.mode)
    raise SystemExit(0 if not m["fails"] else 2)


if __name__ == "__main__":
    main()
