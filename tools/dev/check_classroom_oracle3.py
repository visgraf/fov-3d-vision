"""Structural checks for Classroom-Oracle-3."""
from __future__ import annotations

import ast
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import classroom_oracle3_public as public


def _source(name: str) -> str:
    return (HERE / name).read_text()


def main() -> None:
    checks: list[tuple[str, bool]] = []
    checks.append(("public_self_test", not public.self_test()))
    checks.append(("read_only_contract", public.SCIENTIFIC_CONTRACT["read_only"]))
    checks.append(("zero_acquisition", public.SCIENTIFIC_CONTRACT["new_acquisitions"] == 0))
    checks.append(("zero_fixation", public.SCIENTIFIC_CONTRACT["new_fixations"] == 0))
    checks.append(("zero_fusion", public.SCIENTIFIC_CONTRACT["new_fusion"] == 0))
    checks.append(("truth_phase_separated", public.SCIENTIFIC_CONTRACT["truth_allowed_only_after_controller_phase"]))
    checks.append(("twelve_mm_evaluation", public.COVERAGE_RADIUS_M == 0.012))
    checks.append(("six_focus_objects", public.FOCUS_OBJECT_COUNT == 6))

    audit_src = _source("classroom_oracle3_audit.py")
    demo_src = _source("classroom_oracle3_demo.py")
    tree = ast.parse(audit_src)
    imports = {n.names[0].name for n in ast.walk(tree) if isinstance(n, ast.Import) and n.names}
    imports |= {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    checks.append(("no_subprocess_import", "subprocess" not in imports))
    checks.append(("no_blender_python_import", "bpy" not in imports))
    checks.append(("audit_has_two_phase_guard", "controller_phase_complete" in audit_src and "truth_phase_started" in audit_src))
    checks.append(("demo_is_posthoc", "truth_rejection_overlay" in repr(public.DEMO_CONTRACT) and "oracle_observation.npz" in demo_src))

    failed = []
    for name, ok in checks:
        if not ok:
            failed.append(name)
            print("[classroom-oracle3-check] FAIL", name)
    print(f"[classroom-oracle3-check] SUMMARY passed={len(checks)-len(failed)} failed={len(failed)}")
    raise SystemExit(bool(failed))


if __name__ == "__main__":
    main()
