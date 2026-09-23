"""Structural comparator for Demo-Classroom-1 oracle-attention outputs."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import demo_classroom1_public as public


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out", type=Path)
    a = ap.parse_args()
    m = json.loads((a.out / "demo_manifest.json").read_text())
    fails: list[str] = []
    if m.get("schema") != public.SPEC_ID: fails.append("schema")
    if not m.get("oracle_assisted_demo"): fails.append("oracle_flag")
    if not m.get("truth_available_to_control"): fails.append("truth_flag")
    if m.get("controller_mode") != public.CONTROLLER_MODE: fails.append("controller_mode")
    if m.get("oracle_attention_for_all_fixations") is not True: fails.append("oracle_attention")
    if int(m.get("local_fsg_attention_actions", -1)) != 0: fails.append("local_attention_used")
    if int(m.get("oracle_attention_fixation_count", -1)) != int(m.get("fixation_count", -2)):
        fails.append("attention_count")
    if m.get("foreground_reference_depth_fused") is not False: fails.append("foreground_truth_fused")
    if m.get("discovery_tested") is not False: fails.append("discovery_claim")
    if m.get("autonomous_controller_tested") is not False: fails.append("controller_claim")
    if m.get("fsg6f_generalization_tested") is not False: fails.append("fsg6f_claim")
    if m.get("autonomous_background_decomposition_tested") is not False: fails.append("background_claim")
    if m.get("scene_rel") != public.BLEND_REL: fails.append("scene_binding")
    if not m.get("foreground_object_rows"): fails.append("no_foreground")
    if m.get("background_row", {}).get("role") != "BACKGROUND_SCAFFOLD": fails.append("no_background")
    print("DEMO_CLASSROOM1_COMPLETE structural_fails:", fails)
    raise SystemExit(1 if fails else 0)


if __name__ == "__main__":
    main()
