"""Prospective structural checker for the repaired FullScene-REAL-1 binding."""
from __future__ import annotations

import argparse
import ast
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
FILES = [
    TOOLS / "fullscene_real1_public.py",
    TOOLS / "fullscene_real1_oracle_scaffold.py",
    TOOLS / "fullscene_real1_repo_adapter.py",
    TOOLS / "fullscene_real1_run.py",
    TOOLS / "fullscene_real1_export.py",
    TOOLS / "fullscene_real1_compare.py",
]


def text(path: Path) -> str:
    return path.read_text()


def imports_module(path: Path, module: str) -> bool:
    tree = ast.parse(text(path), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name == module for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if node.module == module:
                return True
    return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mutation", default="")
    a = ap.parse_args()
    fails: list[str] = []
    for f in FILES:
        if not f.is_file():
            fails.append(f"missing:{f.name}")
            continue
        try:
            ast.parse(text(f), filename=str(f))
        except SyntaxError as e:
            fails.append(f"syntax:{f.name}:{e}")

    pub = text(TOOLS / "fullscene_real1_public.py")
    run = text(TOOLS / "fullscene_real1_run.py")
    adp = text(TOOLS / "fullscene_real1_repo_adapter.py")
    ora = text(TOOLS / "fullscene_real1_oracle_scaffold.py")

    checks = {
        "branch_isolated": "fullscene-real-1" in pub and "main and fullscene-calibration-1 remain untouched" in pub,
        "procedural_fixture": "--fixture" in run and "--scene" not in run and "DEFAULT_FIXTURE" in pub,
        "fixture_provenance": "fixture_truth_digest" in run and "enumeration_oracle_sha256" in run,
        "dynamic_ids": "never hard-code scene IDs" in pub and "objects_from_scaffold" in adp,
        "oracle_isolated": imports_module(TOOLS / "fullscene_real1_oracle_scaffold.py", "reality1_scene") and not imports_module(TOOLS / "fullscene_real1_repo_adapter.py", "reality1_scene") and not imports_module(TOOLS / "fullscene_real1_run.py", "reality1_scene"),
        "oracle_whitelist": all(x in pub and x in ora for x in ("object_id", "seed_yaw_deg", "seed_pitch_deg", "label")) and "vertices" in pub,
        "fresh_run": "do not reuse accumulated object maps" in pub,
        "frozen_local": "multiobject2c_policy" in pub and "12 mm" in pub and "24 selected-object fixations" in pub,
        "bounded_handoff": "at most one established cyclopean epistemic handoff" in pub and "No recursive handoff" in adp,
        "truth_quarantined": "observer_complete" in run and run.find("seal_path = _observer_seal") < run.find("reference_exports = dict(adapter.render_reference_after_control"),
        "outputs": all(s in pub for s in ("scene_points.ply", "observer_depth.npy", "reference_rgb.png", "evaluation_summary.json")),
        "separate_metrics": "do not synthesize a single quality/completeness score" in pub,
        "resume": "--resume" in run and "object_complete.json" in run,
    }

    mut = a.mutation
    if mut:
        table = {
            "blend_input": "procedural_fixture",
            "false_provenance": "fixture_provenance",
            "hardcode": "dynamic_ids",
            "oracle_import": "oracle_isolated",
            "oracle_leak": "oracle_whitelist",
            "truth_early": "truth_quarantined",
            "recursive": "bounded_handoff",
            "reuse_maps": "fresh_run",
            "touch_main": "branch_isolated",
            "score": "separate_metrics",
            "noresume": "resume",
            "noexports": "outputs",
        }
        if mut not in table:
            print(f"unknown mutation {mut}", file=sys.stderr)
            raise SystemExit(2)
        checks[table[mut]] = False

    for k, ok in checks.items():
        if not ok:
            fails.append(k)

    print(f"[fullscene-real1-binding] {'PASS' if checks['procedural_fixture'] and checks['fixture_provenance'] else 'FAIL'} "
          f"procedural_fixture={str(checks['procedural_fixture']).lower()} truthful_provenance={str(checks['fixture_provenance']).lower()}")
    print(f"[fullscene-real1-oracle] {'PASS' if checks['oracle_isolated'] and checks['oracle_whitelist'] and checks['dynamic_ids'] else 'FAIL'} "
          f"isolated={str(checks['oracle_isolated']).lower()} whitelist={str(checks['oracle_whitelist']).lower()} dynamic_ids={str(checks['dynamic_ids']).lower()}")
    print(f"[fullscene-real1-truth] {'PASS' if checks['truth_quarantined'] else 'FAIL'} "
          f"observer_sealed_before_full_evaluator={str(checks['truth_quarantined']).lower()} separate_metrics={str(checks['separate_metrics']).lower()}")
    print(f"[fullscene-real1-check] SUMMARY passed={sum(checks.values())} failed={len(checks)-sum(checks.values())}")
    raise SystemExit(0 if not fails else 1)


if __name__ == "__main__":
    main()
