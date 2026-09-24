"""Static/package checks for Classroom-Oracle-2 boundary ablation."""
from __future__ import annotations

import ast
import json
from pathlib import Path
import py_compile
import sys

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
DOCS = ROOT / "docs"

EXPECTED = [
    TOOLS / "classroom_oracle2_public.py",
    TOOLS / "classroom_oracle2_domain.py",
    TOOLS / "classroom_oracle2_render.py",
    TOOLS / "classroom_oracle2_run.py",
    TOOLS / "classroom_oracle2_eval.py",
    TOOLS / "classroom_oracle2_demo.py",
    DOCS / "classroom-oracle-2.md",
]


def main() -> None:
    checks = []

    missing = [str(p.relative_to(ROOT)) for p in EXPECTED if not p.exists()]
    checks.append(("package_files_present", not missing, missing))

    compile_errors = []
    for p in EXPECTED:
        if p.suffix == ".py" and p.exists():
            try:
                py_compile.compile(str(p), doraise=True)
            except Exception as exc:
                compile_errors.append(f"{p.name}: {exc}")
    checks.append(("python_compiles", not compile_errors, compile_errors))

    public_text = (TOOLS / "classroom_oracle2_public.py").read_text() if (TOOLS / "classroom_oracle2_public.py").exists() else ""
    run_text = (TOOLS / "classroom_oracle2_run.py").read_text() if (TOOLS / "classroom_oracle2_run.py").exists() else ""
    render_text = (TOOLS / "classroom_oracle2_render.py").read_text() if (TOOLS / "classroom_oracle2_render.py").exists() else ""
    eval_text = (TOOLS / "classroom_oracle2_eval.py").read_text() if (TOOLS / "classroom_oracle2_eval.py").exists() else ""
    demo_text = (TOOLS / "classroom_oracle2_demo.py").read_text() if (TOOLS / "classroom_oracle2_demo.py").exists() else ""

    checks.append(("domain_is_35_30", all(s in public_text for s in ["-35.0", "35.0", "-30.0", "30.0"]), None))
    checks.append(("baseline_domain_is_25_20", all(s in public_text for s in ["-25.0", "25.0", "-20.0", "20.0"]), None))
    checks.append(("fusion_is_12mm", "0.012" in public_text and "association_radius_m" in public_text, None))
    checks.append(("watchdog_is_24", "MAX_OBJECT_FIXATIONS = 24" in public_text, None))
    checks.append(("target_set_is_25", "TARGET_INSTANCE_COUNT = 25" in public_text, None))
    checks.append(("exact_baseline_seeds_required", "same_seed_gazes_as_baseline" in run_text and "seed changed" in run_text, None))
    checks.append(("domain_patch_precedes_inherited_runner", run_text.find("apply_wide_domain()") < run_text.find("import classroom_oracle1_run"), None))
    checks.append(("dense_truth_evaluation_only", "evaluation_only" in render_text and "dense_evaluation_truth_opened_during_control" in run_text, None))
    checks.append(("two_evaluation_scopes", "original_domain" in eval_text and "wide_domain" in eval_text and "baseline_misses_recovered" in eval_text, None))
    checks.append(("no_scientific_quality_gate", "scientific_pass_fail_threshold" in eval_text and "None" in eval_text, None))
    checks.append(("demo_contract_implemented", all(s in demo_text for s in ["Demo.md", "scene_final.ply", "rgb_observed.png", "depth_reference.png", "instance_reference.png", "coverage_comparison.png", "classroom-oracle-2-demo.mp4"]), None))
    checks.append(("demo_is_posthoc", "observational" in demo_text.lower() and "control loop" in demo_text.lower(), None))

    ast_errors = []
    for p in EXPECTED:
        if p.suffix == ".py" and p.exists():
            try:
                ast.parse(p.read_text(), filename=str(p))
            except SyntaxError as exc:
                ast_errors.append(f"{p.name}: {exc}")
    checks.append(("ast_parse_clean", not ast_errors, ast_errors))

    failed = []
    for name, ok, detail in checks:
        print(f"[classroom-oracle2-check] {'PASS' if ok else 'FAIL'} {name}" + (f" {json.dumps(detail)}" if detail else ""))
        if not ok:
            failed.append(name)
    print(f"[classroom-oracle2-check] SUMMARY passed={len(checks)-len(failed)} failed={len(failed)}")
    raise SystemExit(bool(failed))


if __name__ == "__main__":
    main()
