"""Run Classroom-Oracle-2, the controller-domain boundary ablation.

Scientific delta from Classroom-Oracle-1:
    yaw domain   +/-25 deg -> +/-35 deg
    pitch domain +/-20 deg -> +/-30 deg

Everything else is inherited.  In particular, the 25 target instances and each
object's initial oracle seed are read verbatim from the completed Oracle-1 full
run.  Dense Blender truth remains evaluation-only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import classroom_oracle2_public as public
import classroom_oracle2_domain as domain

# This must precede the inherited runner import.  classroom_oracle1_run imports
# multiobject2c_policy and the Cyclopean module at import time.
DOMAIN_AUDIT = domain.apply_wide_domain()
import classroom_oracle1_run as base


def _json(path: Path):
    return json.loads(path.read_text())


def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(base._jsonable(value), indent=2, sort_keys=True) + "\n")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _run(cmd: list[str], log: Path, cwd: Path) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w") as f:
        p = subprocess.run(cmd, cwd=cwd, stdout=f, stderr=subprocess.STDOUT, text=True)
    if p.returncode:
        tail = log.read_text(errors="replace").splitlines()[-100:]
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(cmd)}\n" + "\n".join(tail))


def _validate_baseline(root: Path) -> tuple[dict, dict]:
    manifest_path = root / "manifest.json"
    seeds_path = root / "bootstrap" / "seeds.json"
    eval_truth = root / "bootstrap" / "evaluation_only" / "reachable_samples.npz"
    for p in (manifest_path, seeds_path, eval_truth):
        if not p.exists():
            raise FileNotFoundError(f"required Oracle-1 baseline artifact missing: {p}")

    manifest = _json(manifest_path)
    seeds = _json(seeds_path)
    if not manifest.get("control_complete") or manifest.get("smoke"):
        raise RuntimeError("baseline must be the completed non-smoke Classroom-Oracle-1 run")
    if bool(manifest.get("dense_evaluation_truth_opened_during_control", True)):
        raise RuntimeError("baseline manifest does not certify truth isolation")
    objects = list(manifest.get("objects", []))
    if len(objects) != public.TARGET_INSTANCE_COUNT:
        raise RuntimeError(f"baseline manifest must contain exactly {public.TARGET_INSTANCE_COUNT} objects")
    instances = list(seeds.get("instances", []))
    if len(instances) != public.TARGET_INSTANCE_COUNT:
        raise RuntimeError(f"baseline seeds must contain exactly {public.TARGET_INSTANCE_COUNT} instances")

    md = {int(o["instance_id"]): o for o in objects}
    sd = {int(s["instance_id"]): s for s in instances}
    if set(md) != set(sd):
        raise RuntimeError("baseline manifest and seed target sets disagree")

    domain_doc = seeds.get("controller_domain_deg", {})
    got = {
        "yaw_min_deg": float(domain_doc["yaw"][0]),
        "yaw_max_deg": float(domain_doc["yaw"][1]),
        "pitch_min_deg": float(domain_doc["pitch"][0]),
        "pitch_max_deg": float(domain_doc["pitch"][1]),
    }
    if got != public.ORIGINAL_DOMAIN:
        raise RuntimeError(f"baseline seed domain mismatch: {got}")
    return manifest, seeds


def _bootstrap(repo: Path, scene: Path, blender: str, args, root: Path) -> dict:
    boot = root / "bootstrap"
    boot.mkdir()
    baseline_seeds = args.baseline_run / "bootstrap" / "seeds.json"
    cmd = [
        blender, "-b", str(scene), "--python-exit-code", "1",
        "-P", str(repo / "tools/classroom_oracle2_render.py"), "--",
        "--mode", "seeds", "--out", str(boot), "--profile", args.profile,
        "--device", args.device, "--seed-step", str(public.SEED_SCAN_STEP_DEG),
        "--baseline-seeds", str(baseline_seeds),
    ]
    _run(cmd, root / "logs/bootstrap.blender.log", repo)
    return _json(boot / "seeds.json")


def _in_domain(gaze, bounds: dict[str, float]) -> bool:
    y, p = map(float, gaze)
    return (
        bounds["yaw_min_deg"] - 1e-9 <= y <= bounds["yaw_max_deg"] + 1e-9
        and bounds["pitch_min_deg"] - 1e-9 <= p <= bounds["pitch_max_deg"] + 1e-9
    )


def _trajectory_audit(result: dict[str, Any]) -> dict[str, int]:
    old_out = 0
    wide_out = 0
    post_seed = 0
    for i, row in enumerate(result.get("trajectory", [])):
        gaze = row.get("gaze_deg", [float("nan"), float("nan")])
        if not _in_domain(gaze, public.WIDE_DOMAIN):
            wide_out += 1
        if not _in_domain(gaze, public.ORIGINAL_DOMAIN):
            old_out += 1
        if i > 0:
            post_seed += 1
            if str(row.get("action_source")) not in {"fsg6f", "cyclopean_epistemic"}:
                raise RuntimeError(
                    f"post-seed gaze was not controller-selected for instance {result.get('instance_id')}"
                )
    if wide_out:
        raise RuntimeError(
            f"controller emitted {wide_out} fixation(s) outside the widened domain for instance {result.get('instance_id')}"
        )
    return {
        "post_seed_looks": post_seed,
        "looks_outside_original_domain": old_out,
        "looks_outside_wide_domain": wide_out,
    }


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--scene", default=public.SCENE)
    ap.add_argument("--baseline-run", type=Path, default=Path(public.BASELINE_RUN_DEFAULT))
    ap.add_argument("--out", required=True)
    ap.add_argument("--blender", default="blender")
    ap.add_argument("--profile", choices=("small", "full"), default=public.DEFAULT_PROFILE)
    ap.add_argument("--device", choices=("OPTIX", "CUDA", "CPU"), default=public.DEFAULT_DEVICE)
    ap.add_argument("--spp", type=int, default=None)
    ap.add_argument("--smoke", action="store_true", help="same repaired Oracle-1 smoke semantics under the widened domain")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    repo = Path(args.repo).resolve()
    root = Path(args.out).resolve()
    args.baseline_run = (repo / args.baseline_run).resolve() if not args.baseline_run.is_absolute() else args.baseline_run.resolve()
    scene = (repo / args.scene).resolve() if not Path(args.scene).is_absolute() else Path(args.scene).resolve()
    if not scene.exists():
        raise FileNotFoundError(scene)
    base._new_dir(root)
    (root / "logs").mkdir()

    baseline_manifest, baseline_seeds_doc = _validate_baseline(args.baseline_run)
    domain.assert_wide_domain()
    bad = public.self_test() + base.public.self_test() + base.self_test()
    if bad:
        raise RuntimeError("public/run self-test failed: " + "; ".join(bad))

    seeds_doc = _bootstrap(repo, scene, args.blender, args, root)
    seeds = list(seeds_doc["instances"])
    if len(seeds) != public.TARGET_INSTANCE_COUNT:
        raise RuntimeError("Oracle-2 bootstrap did not preserve the 25-object target set")

    baseline_seed_by_id = {int(s["instance_id"]): s for s in baseline_seeds_doc["instances"]}
    for seed in seeds:
        b = baseline_seed_by_id.get(int(seed["instance_id"]))
        if b is None or seed.get("object_name") != b.get("object_name") or list(seed.get("seed_gaze_deg", [])) != list(b.get("seed_gaze_deg", [])):
            raise RuntimeError(f"Oracle-2 seed changed for instance {seed.get('instance_id')}")

    manifest = {
        "schema": "ClassroomOracle2-run-v1",
        "spec_id": public.SPEC_ID,
        "public_digest": public.public_digest(),
        "parent_commit": public.PARENT_COMMIT,
        "baseline_run": str(args.baseline_run),
        "baseline_manifest_sha256": _sha256(args.baseline_run / "manifest.json"),
        "baseline_seeds_sha256": _sha256(args.baseline_run / "bootstrap" / "seeds.json"),
        "baseline_total_fixations": int(baseline_manifest.get("total_fixations", 0)),
        "scene": str(scene.relative_to(repo) if scene.is_relative_to(repo) else scene),
        "profile": args.profile,
        "device": args.device,
        "spp_override": args.spp,
        "smoke": bool(args.smoke),
        "scientific_delta": "controller angular extent only",
        "original_domain_deg": public.SCIENTIFIC_CONTRACT["baseline_domain_deg"],
        "wide_domain_deg": public.SCIENTIFIC_CONTRACT["wide_domain_deg"],
        "domain_audit": DOMAIN_AUDIT,
        "target_instance_count": len(seeds),
        "same_target_instances_as_baseline": True,
        "same_seed_gazes_as_baseline": True,
        "controller_truth_scope": "same Oracle-1 seed per target + current tangent pair only",
        "dense_evaluation_truth_opened_during_control": False,
        "foreground_background_decomposition": False,
        "objects": [],
        "control_complete": False,
    }
    _write(root / "manifest.json", manifest)

    smoke_transition = False
    smoke_primary_ids = [int(s["instance_id"]) for s in seeds[:2]] if args.smoke else []
    total_outside_old = 0
    total_post_seed = 0

    for seed in seeds:
        result = base._run_object(repo, scene, args.blender, args, root, seed)
        audit = _trajectory_audit(result)
        result["domain_audit"] = audit
        total_outside_old += int(audit["looks_outside_original_domain"])
        total_post_seed += int(audit["post_seed_looks"])
        _write(root / "objects" / f"instance_{int(result['instance_id']):04d}" / "result.json", result)
        manifest["objects"].append(result)
        manifest["attempted_instance_count"] = len(manifest["objects"])
        manifest["looks_outside_original_domain"] = total_outside_old
        manifest["post_seed_looks"] = total_post_seed

        if args.smoke:
            ok, transition, errors = base._smoke_result_audit(result)
            if not ok:
                raise RuntimeError(
                    f"smoke trajectory contract failed for instance {result.get('instance_id')}: "
                    + "; ".join(errors)
                )
            smoke_transition = smoke_transition or transition
            manifest["smoke_gate"] = {
                "contract": "Oracle-1 repaired smoke gate, with exact baseline seeds and widened domain",
                "primary_instance_ids": smoke_primary_ids,
                "controller_transition_exercised": bool(smoke_transition),
                "objects_examined": len(manifest["objects"]),
                "all_post_seed_looks_controller_selected": True,
            }

        _write(root / "manifest.json", manifest)
        if args.smoke and len(manifest["objects"]) >= 2 and smoke_transition:
            break

    if args.smoke:
        if len(manifest["objects"]) < 2:
            raise RuntimeError("smoke gate did not retain the first two baseline targets")
        if not smoke_transition:
            manifest["smoke_gate"]["status"] = "PASS_NO_CONTROLLER_TRANSITION_REQUESTED"
            manifest["smoke_gate"]["exhausted_target_set"] = len(manifest["objects"]) == len(seeds)
        else:
            manifest["smoke_gate"]["status"] = "PASS_CONTROLLER_TRANSITION_EXERCISED"
            manifest["smoke_gate"]["exhausted_target_set"] = False

    manifest["control_complete"] = True
    manifest["total_fixations"] = sum(int(o["fixation_count"]) for o in manifest["objects"])
    manifest["termination_counts"] = {}
    manifest["action_source_counts"] = {}
    for obj in manifest["objects"]:
        t = str(obj["termination"])
        manifest["termination_counts"][t] = manifest["termination_counts"].get(t, 0) + 1
        for row in obj.get("trajectory", []):
            src = str(row.get("action_source"))
            manifest["action_source_counts"][src] = manifest["action_source_counts"].get(src, 0) + 1
    _write(root / "manifest.json", manifest)
    print("[classroom-oracle2] COMPLETE", json.dumps({
        "objects": len(manifest["objects"]),
        "fixations": manifest["total_fixations"],
        "post_seed_looks": manifest.get("post_seed_looks", 0),
        "looks_outside_original_domain": manifest.get("looks_outside_original_domain", 0),
        "terminations": manifest["termination_counts"],
        "smoke": bool(args.smoke),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
