"""Descriptive evaluation of Reality Check 2b empty-look recovery records."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

import reality2b_public as public
import reality1_public as parent_public
import reality1_scene as scene
import reality1_eval as base_eval
from fsg3_surface_map import load_map
from fsg_geometry import json_write


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _same_map(a, b) -> bool:
    return (
        np.array_equal(a.xyz_h, b.xyz_h)
        and np.array_equal(a.rgb, b.rgb)
        and np.array_equal(a.instance_id, b.instance_id)
        and np.array_equal(a.support_count, b.support_count)
        and np.array_equal(a.provenance_mask, b.provenance_mask)
    )


def evaluate(root: Path, out: Path) -> dict:
    root = root.resolve()
    out = out.resolve()
    if out.exists():
        raise FileExistsError("output must be new")

    manifest = json.loads((root / "prediction_manifest.json").read_text())
    fails: list[str] = []
    if manifest.get("truth_opened") is not False:
        fails.append("prediction opened evaluator truth")
    if manifest.get("public_spec_sha256") != public.public_digest():
        fails.append("public spec digest mismatch")
    if manifest.get("parent_reality1_public_spec_sha256") != parent_public.public_digest():
        fails.append("parent public spec digest mismatch")
    if manifest.get("instrument") != public.INSTRUMENT_ID:
        fails.append("wrong stereo instrument")
    if manifest.get("frozen_object_policy") != public.FROZEN_POLICY_ID:
        fails.append("wrong object policy")
    if not manifest.get("fixed_head") or not manifest.get("static_scene"):
        fails.append("fixed-head/static-scene contract broken")
    if manifest.get("continued_from_parent_without_rerender") is not True:
        fails.append("parent was not reused as exact continuation state")
    if int(manifest.get("parent_fixation_count", -1)) != public.PARENT_FIXATIONS:
        fails.append("wrong parent fixation count")
    if int(manifest.get("watchdog_total_fixations", -1)) != public.WATCHDOG_TOTAL_FIXATIONS:
        fails.append("watchdog drifted")
    if int(manifest.get("empty_target_point_limit", -1)) != public.EMPTY_TARGET_POINT_LIMIT:
        fails.append("empty-observation point limit drifted from the retired Reality Check 2 guard")

    seed = int(manifest.get("seed"))
    if seed not in public.SEEDS:
        fails.append("seed outside prospective schedule")
    gazes = [tuple(map(float, g)) for g in manifest["fixation_gazes_deg"]]
    if len(gazes) < public.PARENT_FIXATIONS:
        fails.append("combined record lost parent fixations")
    if len(gazes) > public.WATCHDOG_TOTAL_FIXATIONS:
        fails.append("combined record exceeded watchdog")
    if len({(round(a, 8), round(b, 8)) for a, b in gazes}) != len(gazes):
        fails.append("repeated physical fixation")

    parent = Path(manifest["parent_record"]).resolve()
    if not parent.exists():
        fails.append("parent Reality Check 1 record missing")
    else:
        for name, want in manifest.get("parent_hashes", {}).items():
            p = parent / name
            if not p.exists() or _sha256(p) != want:
                fails.append(f"parent {name} changed after continuation")
        pm = json.loads((parent / "prediction_manifest.json").read_text())
        pg = [tuple(map(float, g)) for g in pm.get("fixation_gazes_deg", [])]
        if pg != gazes[:public.PARENT_FIXATIONS]:
            fails.append("combined first six gazes differ from exact parent")
        for step in range(public.PARENT_FIXATIONS):
            if (root / "acquisitions" / f"fix_{step:02d}").exists():
                fails.append(f"parent fix_{step:02d} was rerendered")
            src = parent / "maps" / f"map_{step:02d}.npz"
            dst = root / "maps" / f"map_{step:02d}.npz"
            if not src.exists() or not dst.exists() or _sha256(src) != _sha256(dst):
                fails.append(f"combined map_{step:02d} is not an exact copy of the parent state")

    maps = []
    for step in range(len(gazes)):
        mp = root / "maps" / f"map_{step:02d}.npz"
        if not mp.exists():
            fails.append(f"missing combined map_{step:02d}")
            continue
        maps.append(load_map(mp))
        if step < public.PARENT_FIXATIONS:
            continue
        acq = root / "acquisitions" / f"fix_{step:02d}"
        case = acq / f"fix_{step:02d}"
        rr = json.loads((acq / "run.json").read_text())
        if rr.get("truth_spec_sha256") != scene.truth_digest() or rr.get("fixture") != public.FIXTURE:
            fails.append(f"fix_{step:02d} truth/fixture provenance mismatch")
        with np.load(case / "evaluation_only" / "mesh.npz", allow_pickle=False) as f:
            mesh = {k: f[k] for k in f.files}
        try:
            scene.validate_mesh(mesh)
        except Exception as exc:
            fails.append(f"fix_{step:02d} exported scene mesh invalid: {exc}")

    if len(maps) != len(gazes):
        fails.append("map sequence incomplete")
    final = maps[-1] if maps else None
    if final is None or len(final.xyz_h) < 100:
        fails.append("final target map is effectively empty")
    elif len(final.instance_id) and set(final.instance_id.tolist()) != {public.OBJECT_ID}:
        fails.append("map contains non-target instance")

    assoc = manifest["association_stats"]
    by_step = {int(a["step"]): a for a in assoc if "step" in a}
    empty_steps = [int(x) for x in manifest.get("empty_observation_steps", [])]
    for step in empty_steps:
        a = by_step.get(step)
        if a is None:
            fails.append(f"empty fix_{step:02d} missing association record")
            continue
        if a.get("fused") is not False or a.get("empty_target_observation") is not True:
            fails.append(f"empty fix_{step:02d} was not recorded as no-fusion negative evidence")
        if int(a.get("input_points", public.EMPTY_TARGET_POINT_LIMIT)) >= public.EMPTY_TARGET_POINT_LIMIT:
            fails.append(f"empty fix_{step:02d} does not satisfy inherited point-count condition")
        if step <= 0 or step >= len(maps):
            fails.append(f"empty fix_{step:02d} cannot be checked for map invariance")
        elif not _same_map(maps[step - 1], maps[step]):
            fails.append(f"empty fix_{step:02d} changed the persistent map")

    for a in assoc:
        if a.get("fused") is False:
            continue
        # Parent RC1 entries predate the explicit 'fused' flag and are real fusions.
        if a.get("idempotent_replay", False) is not True:
            fails.append(f"{a.get('patch_id', 'unknown patch')} replay not idempotent")

    patch = manifest["patch_stats"]
    empty_patch_steps = [int(p["step"]) for p in patch if p.get("empty_target_observation")]
    if sorted(empty_patch_steps) != sorted(empty_steps):
        fails.append("empty-observation manifest and patch records disagree")

    trace = json.loads((root / "policy_trace.json").read_text())["trace"]
    for step in empty_steps:
        d = next((x for x in trace if int(x.get("step", -1)) == step), None)
        if d is None:
            fails.append(f"empty fix_{step:02d} missing policy decision")
        elif d.get("observation_was_empty_target") is not True:
            fails.append(f"empty fix_{step:02d} was not retained in policy history")

    cov = [base_eval.spatial_coverage(m.xyz_h) for m in maps]
    err = base_eval.approximate_surface_distance(final.xyz_h) if final is not None else np.empty(0)
    supported = np.asarray(final.support_count) >= 2 if final is not None else np.zeros(0, dtype=bool)
    mf = [p["object_measurement_fraction"] for p in patch if p.get("object_measurement_fraction") is not None]
    overlap_med = [a["overlap_median_distance_m"] for a in assoc if a.get("overlap_median_distance_m") is not None]
    overlap_p95 = [a["overlap_p95_distance_m"] for a in assoc if a.get("overlap_p95_distance_m") is not None]
    at6 = cov[public.PARENT_FIXATIONS - 1] if len(cov) >= public.PARENT_FIXATIONS else None

    first_empty = min(empty_steps) if empty_steps else None
    recovered_steps = []
    if first_empty is not None:
        for a in assoc:
            s = int(a.get("step", -1))
            if s > first_empty and a.get("fused") is True and int(a.get("input_points", 0)) >= public.EMPTY_TARGET_POINT_LIMIT:
                recovered_steps.append(s)

    metrics = {
        "schema": "RealityCheck2b-evaluation-v1",
        "status": "REALITY2B_OBSERVATION_COMPLETE" if not fails else "REALITY2B_INTEGRITY_FAIL",
        "integrity_fails": fails,
        "profile": manifest["profile"],
        "seed": seed,
        "fixture": public.FIXTURE,
        "fixation_count": len(gazes),
        "new_fixation_count": max(0, len(gazes) - public.PARENT_FIXATIONS),
        "fixation_gazes_deg": [list(g) for g in gazes],
        "termination_reason": manifest["termination_reason"],
        "terminated_by_no_frontier": manifest["termination_reason"] == "no_frontier",
        "watchdog_reached": manifest["termination_reason"] == "watchdog_max_fixations",
        "empty_observation_count": len(empty_steps),
        "empty_observation_steps": empty_steps,
        "first_empty_observation_step": first_empty,
        "recovered_after_first_empty": bool(recovered_steps),
        "post_empty_fused_steps": recovered_steps,
        "visible_truth_coverage_by_fixation": cov,
        "visible_truth_coverage_seed": cov[0] if cov else None,
        "visible_truth_coverage_at_reality1_stop": at6,
        "visible_truth_coverage_final": cov[-1] if cov else None,
        "visible_truth_coverage_gain_after_reality1_stop": (cov[-1] - at6) if cov and at6 is not None else None,
        "map_points": int(len(final.xyz_h)) if final is not None else 0,
        "supported_surfels": int(supported.sum()),
        "approx_surface_median_m": float(np.median(err)) if len(err) else None,
        "approx_surface_p95_m": float(np.percentile(err, 95)) if len(err) else None,
        "measurement_fraction_min": float(min(mf)) if mf else None,
        "measurement_fraction_median": float(np.median(mf)) if mf else None,
        "overlap_median_max_m": float(max(overlap_med)) if overlap_med else None,
        "overlap_p95_max_m": float(max(overlap_p95)) if overlap_p95 else None,
        "patch_stats": patch,
        "association_stats": assoc,
        "policy_trace": trace,
        "parent_primary_camera_samples": int(manifest["parent_primary_camera_samples"]),
        "continuation_primary_camera_samples": int(manifest["continuation_primary_camera_samples"]),
        "primary_camera_samples": int(manifest["primary_camera_samples"]),
        "quality_gated": False,
        "interpretation": "descriptive recovery experiment; an empty look is negative perceptual evidence, no_frontier is the scientific stop, and the watchdog is only a guard",
    }
    out.mkdir(parents=True)
    json_write(out / "metrics.json", metrics)
    if maps:
        base_eval.write_growth_truth(out / "growth_truth.png", maps, cov, gazes)
    print("[reality2b-eval] " + metrics["status"], json.dumps({k: metrics[k] for k in (
        "seed", "fixation_count", "new_fixation_count", "termination_reason", "terminated_by_no_frontier",
        "watchdog_reached", "empty_observation_count", "empty_observation_steps", "recovered_after_first_empty",
        "visible_truth_coverage_at_reality1_stop", "visible_truth_coverage_final",
        "visible_truth_coverage_gain_after_reality1_stop", "approx_surface_median_m",
        "approx_surface_p95_m", "supported_surfels", "measurement_fraction_min",
        "overlap_median_max_m", "integrity_fails",
    )}, sort_keys=True), flush=True)
    return metrics


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("record", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    m = evaluate(a.record, a.out)
    raise SystemExit(0 if not m["integrity_fails"] else 2)


if __name__ == "__main__":
    main()
