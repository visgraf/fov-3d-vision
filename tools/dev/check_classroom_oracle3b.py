"""Structural checks for Classroom-Oracle-3b."""
from __future__ import annotations
import ast
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import classroom_oracle3b_public as p

FILES = [
    ROOT / "classroom_oracle3b_public.py",
    ROOT / "classroom_oracle3b_audit.py",
    ROOT / "classroom_oracle3b_demo.py",
]

def main() -> int:
    checks=[]
    checks.append(("public_self_test", not p.self_test()))
    checks.append(("parent_is_oracle3_result", p.PARENT_COMMIT == "9c13905"))
    checks.append(("dominant_residue_targeted", p.TARGET_FIRST_REASON == "NOT_SHORELINE" and p.TARGET_SUBTYPE == "COMPLEMENT_NONSHORELINE"))
    checks.append(("posthoc_read_only", p.SCIENTIFIC_CONTRACT["posthoc_only"] and p.SCIENTIFIC_CONTRACT["read_only"]))
    checks.append(("zero_actions", all(p.SCIENTIFIC_CONTRACT[k] == 0 for k in ("new_acquisitions","new_fixations","new_fusion","blender_launches"))))
    checks.append(("no_controller_execution", not p.SCIENTIFIC_CONTRACT["controller_replay"] and not p.SCIENTIFIC_CONTRACT["controller_action"]))
    checks.append(("no_rule_change", not any(p.SCIENTIFIC_CONTRACT[k] for k in ("fsg6f_rule_modified","cyclopean_rule_modified","fusion_rule_modified","watchdog_modified","domain_modified"))))
    checks.append(("focus_inherited", "Oracle-3 focus_instance_ids" in p.FOCUS_SOURCE))
    checks.append(("no_quality_gate", p.SCIENTIFIC_CONTRACT["no_quality_pass_fail_threshold"]))
    checks.append(("demo_posthoc", p.DEMO_CONTRACT["posthoc_only"] and p.DEMO_CONTRACT["four_panel_anatomy"]))
    src="\n".join(f.read_text() for f in FILES)
    low=src.lower()
    checks.append(("no_blender_or_subprocess", "import bpy" not in low and "import subprocess" not in low and "subprocess." not in low))
    audit_src=(ROOT/"classroom_oracle3b_audit.py").read_text()
    checks.append(("no_choose_next", "choose_next(" not in audit_src and "object_policy" not in audit_src))
    checks.append(("ring_depth_defined_by_support", "cv2.DIST_C" in audit_src and "successive 8-connected support dilations" in audit_src))
    checks.append(("components_on_reference_lattice", "_reference_lattice" in audit_src and "connectedComponentsWithStats" in audit_src))
    checks.append(("no_hardcoded_focus_ids", all(str(v) not in audit_src for v in (178225210166115123,))))
    for f in FILES:
        ast.parse(f.read_text(), filename=str(f))
    failed=[name for name,ok in checks if not ok]
    for name,ok in checks:
        print(f"[classroom-oracle3b-check] {'PASS' if ok else 'FAIL'} {name}")
    print(f"[classroom-oracle3b-check] SUMMARY passed={len(checks)-len(failed)} failed={len(failed)}")
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
