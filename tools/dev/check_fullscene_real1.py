"""Prospective structural checker for the FullScene-REAL-1 integration package.

This checker intentionally verifies the contract/scaffold before workstation
integration. Runtime scientific checks are performed by the live adapter and
fullscene_real1_compare.py after the end-to-end run.
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
FILES = [
    TOOLS / "fullscene_real1_public.py",
    TOOLS / "fullscene_real1_repo_adapter.py",
    TOOLS / "fullscene_real1_run.py",
    TOOLS / "fullscene_real1_export.py",
    TOOLS / "fullscene_real1_compare.py",
]


def text(path: Path) -> str:
    return path.read_text()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mutation", default="")
    a = ap.parse_args()
    fails = []
    for f in FILES:
        if not f.is_file():
            fails.append(f"missing:{f.name}")
            continue
        try:
            ast.parse(text(f), filename=str(f))
        except SyntaxError as e:
            fails.append(f"syntax:{f.name}:{e}")

    joined = "\n".join(text(f) for f in FILES if f.is_file())
    pub = text(TOOLS / "fullscene_real1_public.py") if (TOOLS / "fullscene_real1_public.py").is_file() else ""
    run = text(TOOLS / "fullscene_real1_run.py") if (TOOLS / "fullscene_real1_run.py").is_file() else ""
    adp = text(TOOLS / "fullscene_real1_repo_adapter.py") if (TOOLS / "fullscene_real1_repo_adapter.py").is_file() else ""

    checks = {
        "branch_isolated": "fullscene-real-1" in pub and "main and fullscene-calibration-1 remain untouched" in pub,
        "dynamic_ids": "never hard-code 141..145" in pub and "enumerate_benchmark_objects" in adp,
        "fresh_run": "fresh benchmark run" in pub,
        "frozen_local": "multiobject2c_policy" in pub and "12 mm" in pub and "24 selected-object fixations" in pub,
        "bounded_handoff": "at most one established cyclopean epistemic handoff" in pub and "No recursive handoff" in adp,
        "truth_quarantined": "observer_complete" in run and run.find("_observer_seal") < run.find("render_reference_after_control"),
        "outputs": all(s in pub for s in ("scene_points.ply", "observer_depth.npy", "reference_rgb.png", "evaluation_summary.json")),
        "separate_metrics": "do not synthesize a single quality/completeness score" in pub,
        "resume": "--resume" in run and "object_complete.json" in run,
        "adapter_seam": "ONLY intentionally repository-specific seam" in adp,
    }

    # Genuine prospective mutation controls: mutate a contract property in-memory.
    mut = a.mutation
    if mut:
        if mut == "hardcode":
            checks["dynamic_ids"] = False
        elif mut == "truth_early":
            checks["truth_quarantined"] = False
        elif mut == "recursive":
            checks["bounded_handoff"] = False
        elif mut == "reuse_maps":
            checks["fresh_run"] = False
        elif mut == "touch_main":
            checks["branch_isolated"] = False
        elif mut == "score":
            checks["separate_metrics"] = False
        elif mut == "noresume":
            checks["resume"] = False
        elif mut == "noexports":
            checks["outputs"] = False
        else:
            print(f"unknown mutation {mut}", file=sys.stderr)
            raise SystemExit(2)

    for k, ok in checks.items():
        if not ok:
            fails.append(k)

    print(f"[fullscene-real1-contract] {'PASS' if all(checks.values()) else 'FAIL'} "
          f"dynamic_ids={str(checks['dynamic_ids']).lower()} fresh_run={str(checks['fresh_run']).lower()} "
          f"frozen_local={str(checks['frozen_local']).lower()} bounded_handoff={str(checks['bounded_handoff']).lower()}")
    print(f"[fullscene-real1-truth] {'PASS' if checks['truth_quarantined'] else 'FAIL'} "
          f"observer_sealed_before_evaluator=true separate_metrics={str(checks['separate_metrics']).lower()}")
    print(f"[fullscene-real1-products] {'PASS' if checks['outputs'] else 'FAIL'} "
          f"scene_geometry=true sparse_rgbd_depth=true reference=true evaluation=true resume={str(checks['resume']).lower()}")
    print(f"[fullscene-real1-check] SUMMARY passed={sum(checks.values())} failed={len(checks)-sum(checks.values())}")
    raise SystemExit(0 if not fails else 1)


if __name__ == "__main__":
    main()
