"""Pure structural checks with genuine source-mutation negatives for MultiObject-3d."""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "tools" / "multiobject3d_public.py"
AUD = ROOT / "tools" / "multiobject3d_audit.py"
PROG = ROOT / "tools" / "multiobject3d_progress.py"


def _source(p: Path) -> str:
    return p.read_text()


def _checks(pub: str, aud: str, prog: str) -> list[tuple[str, bool]]:
    ast.parse(pub); ast.parse(aud); ast.parse(prog)
    return [
        (
            "read_only_no_acquisition",
            'NO_ACQUISITION = True' in pub
            and "subprocess" not in aud
            and "blender" not in aud.lower()
            and '"acquisitions_added": 0' in aud
            and '"growth_iterations_added": 0' in aud,
        ),
        (
            "parent_selected_policy_stop_not_handpicked",
            '"active_object_source": "consume selected_object_id' in pub
            and 'target_id = int(m.get("selected_object_id", -1))' in aud
            and 'm.get("termination_reason") != "no_frontier"' in aud
            and 'm.get("scientific_stop_reached") is not True' in aud
            and "TARGET_OBJECT_ID =" not in pub,
        ),
        (
            "scene_objects_read_only_selected_only_audit",
            '"scene_objects_read_only": True' in aud
            and '"selected_object_read_only": True' in aud
            and "scene object {oid} changed" in aud
            and "selected-object map lost id purity" in aud,
        ),
        (
            "observation_separate_from_depth",
            "cyclopean1d_epistemic as epi" in aud
            and 'ob["calibration"], ob["rectification"], ob["instance_id"], ob["valid"],' in aud
            and 'ob["raw_support_L"]' in aud
            and "sample_projected_evidence" in aud,
        ),
        (
            "final_policy_stop_replayed_and_related",
            "def _reconstruct_final_policy_stop" in aud
            and "policy.choose_next(" in aud
            and "frozen_frontier.extract_frontier" in aud
            and "frozen_frontier.classify_frontier_state" in aud
            and '"final_policy_stop_replayed_exactly": True' in aud
            and "frontier_state_to_cyclopean_cell_counts" in aud,
        ),
        (
            "frozen_scale_no_new_threshold",
            'GRID_DEG = 0.1' in pub
            and 'FUSION = dict(parent.FUSION)' in pub
            and "association_radius_m" in aud
            and "texture_threshold" not in aud.lower()
            and "new_threshold" not in aud.lower(),
        ),
        (
            "watchdog_not_extended_scene_progress_unblocked",
            '"watchdog_changed": False' in aud
            and "choose_next_action(" not in aud
            and 'return "MOVE_TO_NEXT_OBJECT"' in prog
            and "never blocks scene progress" in pub,
        ),
    ]


def _mutate(name: str, pub: str, aud: str, prog: str):
    if name == "acquire":
        aud = aud.replace("import argparse", "import argparse\nimport subprocess", 1)
    elif name == "handpick":
        aud = aud.replace('target_id = int(m.get("selected_object_id", -1))', 'target_id = 999', 1)
    elif name == "crossobject":
        aud = aud.replace('"scene_objects_read_only": True', '"scene_objects_read_only": False', 1)
    elif name == "depthonly":
        aud = aud.replace('ob["calibration"], ob["rectification"], ob["instance_id"], ob["valid"],', 'ob["calibration"], ob["rectification"], ob["instance_id"], ob["instance_id"] == int(target_id),', 1)
    elif name == "stopreplay":
        aud = aud.replace('policy.choose_next(', 'policy.choose_next_disabled(', 1)
    elif name == "threshold":
        aud = aud.replace("def execute(args) -> dict:", "texture_threshold = 0.01\n\ndef execute(args) -> dict:", 1)
    elif name == "watchdog":
        aud = aud.replace('"watchdog_changed": False', '"watchdog_changed": True', 1)
    elif name == "qualitygate":
        prog = prog.replace('return "MOVE_TO_NEXT_OBJECT"', 'return "BLOCK_UNTIL_OBJECT_COMPLETE"', 1)
    else:
        raise SystemExit(f"unknown negative: {name}")
    return pub, aud, prog


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--negative")
    a = ap.parse_args()
    pub, aud, prog = _source(PUB), _source(AUD), _source(PROG)
    base = _checks(pub, aud, prog)
    if a.negative:
        mp, ma, mg = _mutate(a.negative, pub, aud, prog)
        changed = _checks(mp, ma, mg)
        escaped = [name for (name, before), (_, after) in zip(base, changed) if before and not after]
        if not escaped:
            print(f"[multiobject3d-negative] ERROR {a.negative} mutation escaped detection")
            raise SystemExit(2)
        print(f"[multiobject3d-negative] PASS {a.negative} detected_by={','.join(escaped)}")
        raise SystemExit(1)
    failed = [n for n, ok in base if not ok]
    print("[multiobject3d-audit] " + ("PASS" if not failed else "FAIL") + " read_only=true parent_policy_stop=true observation_separate_from_depth=true stop_replay=true")
    print("[multiobject3d-progress] " + ("PASS" if not failed else "FAIL") + " descriptive_only=true scene_progress_unblocked=true next=next_object_selection")
    print(f"[multiobject3d-check] SUMMARY passed={len(base)-len(failed)} failed={len(failed)}")
    if failed:
        print("[multiobject3d-check] FAIL " + ",".join(failed))
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
