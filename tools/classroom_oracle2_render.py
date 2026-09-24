"""Blender-side bootstrap for Classroom-Oracle-2 boundary ablation.

The wide-domain seed scan is used only to generate evaluation truth.  The
controller-visible target set and seed gazes are replaced with the exact 25
Classroom-Oracle-1 seeds supplied by ``--baseline-seeds``.

Fixation rendering delegates to Classroom-Oracle-1 because the binocular sensor
and local oracle measurement are intentionally unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import traceback

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import classroom_oracle2_public as public
import classroom_oracle2_domain as domain

# Must happen before the inherited renderer imports/uses FSG6f state.
DOMAIN_AUDIT = domain.apply_wide_domain()
import classroom_oracle1_render as base


def _script_args() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def _json(path: Path):
    return json.loads(path.read_text())


def _write(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _validate_baseline_seeds(doc: dict) -> list[dict]:
    d = doc.get("controller_domain_deg", {})
    got = {
        "yaw_min_deg": float(d.get("yaw", [float("nan"), float("nan")])[0]),
        "yaw_max_deg": float(d.get("yaw", [float("nan"), float("nan")])[1]),
        "pitch_min_deg": float(d.get("pitch", [float("nan"), float("nan")])[0]),
        "pitch_max_deg": float(d.get("pitch", [float("nan"), float("nan")])[1]),
    }
    if got != public.ORIGINAL_DOMAIN:
        raise RuntimeError(f"baseline seeds are not from the original controller domain: {got}")
    instances = list(doc.get("instances", []))
    if len(instances) != public.TARGET_INSTANCE_COUNT:
        raise RuntimeError(
            f"expected {public.TARGET_INSTANCE_COUNT} baseline seeds, got {len(instances)}"
        )
    ids = [int(x["instance_id"]) for x in instances]
    if ids != sorted(ids) or len(set(ids)) != len(ids):
        raise RuntimeError("baseline instance ids must be unique and sorted")
    for item in instances:
        gaze = list(item.get("seed_gaze_deg", []))
        if len(gaze) != 2:
            raise RuntimeError(f"bad baseline seed gaze for instance {item.get('instance_id')}")
    return instances


def seed_scan(args) -> None:
    baseline_seeds = Path(args.baseline_seeds).resolve()
    if not baseline_seeds.exists():
        raise FileNotFoundError(baseline_seeds)
    baseline_doc = _json(baseline_seeds)
    baseline_instances = _validate_baseline_seeds(baseline_doc)

    # Inherited seed_scan now sees the widened FSG6f SURFACE_FRONTIER.  Its dense
    # first-hit sample cloud is evaluation-only.  We replace its generated seed
    # list immediately afterwards with the frozen Oracle-1 seed list.
    base.seed_scan(args)

    out = Path(args.out).resolve()
    wide_doc = _json(out / "seeds.json")
    wide_instances = list(wide_doc.get("instances", []))
    evdir = out / "evaluation_only"
    truth_path = evdir / "reachable_samples.npz"
    with np.load(truth_path, allow_pickle=False) as z:
        wide_ids = set(int(x) for x in np.unique(np.asarray(z["instance_id"], np.int32)) if int(x) > 0)

    baseline_ids = {int(x["instance_id"]) for x in baseline_instances}
    missing = sorted(baseline_ids - wide_ids)
    if missing:
        raise RuntimeError(f"baseline targets missing from widened-domain truth: {missing}")

    # Retain every widened-domain seed candidate under evaluation_only so the
    # controller cannot mistake newly visible objects for experiment targets.
    _write(evdir / "wide_visible_seed_candidates.json", {
        "schema": "ClassroomOracle2-wide-visible-candidates-v1",
        "spec_id": public.SPEC_ID,
        "controller_input": False,
        "instances": wide_instances,
    })

    baseline_truth = baseline_seeds.parent / "evaluation_only" / "reachable_samples.npz"
    if not baseline_truth.exists():
        raise FileNotFoundError(
            "baseline original-domain truth is required next to seeds.json: " + str(baseline_truth)
        )
    copied_truth = evdir / "original_domain_reachable_samples.npz"
    shutil.copy2(baseline_truth, copied_truth)

    replacement = {
        "schema": "ClassroomOracle2-seeds-v1",
        "spec_id": public.SPEC_ID,
        "profile": args.profile,
        "eye_note": wide_doc.get("eye_note"),
        "head_origin_w_m": wide_doc.get("head_origin_w_m"),
        "head_R_wh": wide_doc.get("head_R_wh"),
        "controller_domain_deg": {
            "yaw": [public.WIDE_DOMAIN["yaw_min_deg"], public.WIDE_DOMAIN["yaw_max_deg"]],
            "pitch": [public.WIDE_DOMAIN["pitch_min_deg"], public.WIDE_DOMAIN["pitch_max_deg"]],
        },
        "baseline_controller_domain_deg": {
            "yaw": [public.ORIGINAL_DOMAIN["yaw_min_deg"], public.ORIGINAL_DOMAIN["yaw_max_deg"]],
            "pitch": [public.ORIGINAL_DOMAIN["pitch_min_deg"], public.ORIGINAL_DOMAIN["pitch_max_deg"]],
        },
        "seed_scan_step_deg": float(args.seed_step),
        "seed_source": "exact Classroom-Oracle-1 full-run seeds; no reselection",
        "baseline_seeds_path": str(baseline_seeds),
        "baseline_seeds_sha256": _sha256(baseline_seeds),
        "wide_visible_instance_count": len(wide_instances),
        "target_instance_count": len(baseline_instances),
        "instances": baseline_instances,
        "domain_audit": DOMAIN_AUDIT,
    }
    _write(out / "seeds.json", replacement)

    ev_manifest_path = evdir / "manifest.json"
    ev_manifest = _json(ev_manifest_path)
    ev_manifest.update({
        "schema": "ClassroomOracle2-evaluation-truth-v1",
        "spec_id": public.SPEC_ID,
        "controller_input": False,
        "wide_domain_deg": replacement["controller_domain_deg"],
        "original_domain_deg": replacement["baseline_controller_domain_deg"],
        "target_instance_count": len(baseline_instances),
        "wide_visible_instance_count": len(wide_instances),
        "original_domain_truth_file": copied_truth.name,
        "original_domain_truth_sha256": _sha256(copied_truth),
        "wide_domain_truth_file": truth_path.name,
        "wide_domain_truth_sha256": _sha256(truth_path),
        "note": "both dense truth arrays are evaluation-only and are never opened during control",
    })
    _write(ev_manifest_path, ev_manifest)

    print("[classroom-oracle2-render] SEEDS", json.dumps({
        "targets": len(baseline_instances),
        "wide_visible_instances": len(wide_instances),
        "same_baseline_seeds": True,
        "domain": replacement["controller_domain_deg"],
    }, sort_keys=True), flush=True)


def fixation(args) -> None:
    base.fixation(args)
    # The acquisition itself is deliberately the Oracle-1 sensor.  Add the
    # ablation identity as provenance without altering the saved observation.
    p = Path(args.out).resolve() / "acquisition.json"
    if p.exists():
        doc = _json(p)
        doc["experiment_spec_id"] = public.SPEC_ID
        doc["scientific_delta"] = "controller angular domain only"
        _write(p, doc)


def parse_args(argv: list[str]):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", required=True, choices=("seeds", "fixation"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--profile", choices=("small", "full"), default=public.DEFAULT_PROFILE)
    ap.add_argument("--device", choices=("OPTIX", "CUDA", "CPU"), default=public.DEFAULT_DEVICE)
    ap.add_argument("--spp", type=int, default=None)
    ap.add_argument("--seed-step", type=float, default=public.SEED_SCAN_STEP_DEG)
    ap.add_argument("--max-range", type=float, default=1000.0)
    ap.add_argument("--baseline-seeds", default=None)
    ap.add_argument("--yaw", type=float, default=0.0)
    ap.add_argument("--pitch", type=float, default=0.0)
    ap.add_argument("--object-id", type=int, default=0)
    ap.add_argument("--step", type=int, default=0)
    args = ap.parse_args(argv)
    if args.seed_step <= 0 or args.max_range <= 0:
        ap.error("--seed-step and --max-range must be positive")
    if args.mode == "seeds" and not args.baseline_seeds:
        ap.error("--baseline-seeds is required in seeds mode")
    if args.spp is None:
        import fsg6f_public as frozen
        args.spp = int(frozen.DEFAULT_SPP[args.profile])
    if args.spp <= 0:
        ap.error("--spp must be positive")
    return args


def main() -> None:
    domain.assert_wide_domain()
    args = parse_args(_script_args())
    if args.mode == "seeds":
        seed_scan(args)
    else:
        fixation(args)


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        if isinstance(exc, SystemExit) and exc.code in (0, None):
            raise
        traceback.print_exc()
        print("[classroom-oracle2-render] FAILED", flush=True)
        sys.stdout.flush(); sys.stderr.flush(); os._exit(1)
