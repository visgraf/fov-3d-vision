"""Pure structural checks with genuine source-mutation negatives for MultiObject-1c."""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "tools" / "multiobject1c_public.py"
AUD = ROOT / "tools" / "multiobject1c_audit.py"
PROG = ROOT / "tools" / "multiobject1c_progress.py"


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
            "object143_only_object141_read_only",
            '"active_object": OBJECT_ID_2' in pub
            and 'public.OBJECT_ID_2' in aud
            and '"object_1_read_only": True' in aud
            and '"object_2_read_only": True' in aud
            and "object 141 changed" in aud,
        ),
        (
            "observation_separate_from_depth",
            "cyclopean1d_epistemic as epi" in aud
            and 'ob["calibration"], ob["rectification"], ob["instance_id"], ob["valid"],' in aud
            and 'ob["raw_support_L"]' in aud
            and "sample_projected_evidence" in aud,
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
            "watchdog_not_extended_no_policy_loop",
            '"watchdog_changed": False' in aud
            and "choose_next(" not in aud
            and "OBJECT2_WATCHDOG_FIXATIONS" not in aud,
        ),
        (
            "scene_progress_not_quality_gated",
            'return "MOVE_TO_NEXT_OBJECT"' in prog
            and "scene progress to the next-object stage is not quality-gated" in pub
            and '"next_stage": public.NEXT_STAGE' in aud,
        ),
    ]


def _mutate(name: str, pub: str, aud: str, prog: str):
    if name == "acquire":
        aud = aud.replace("import argparse", "import argparse\nimport subprocess", 1)
    elif name == "object1active":
        pub = pub.replace('"active_object": OBJECT_ID_2', '"active_object": OBJECT_ID_1', 1)
    elif name == "depthonly":
        aud = aud.replace('ob["instance_id"], ob["valid"]', 'ob["instance_id"], ob["instance_id"] == public.OBJECT_ID_2', 1)
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
            print(f"[multiobject1c-negative] ERROR {a.negative} mutation escaped detection")
            raise SystemExit(2)
        print(f"[multiobject1c-negative] PASS {a.negative} detected_by={','.join(escaped)}")
        raise SystemExit(1)
    failed = [n for n, ok in base if not ok]
    print("[multiobject1c-audit] " + ("PASS" if not failed else "FAIL") + " read_only=true object143_only=true observation_separate_from_depth=true no_watchdog_extension=true")
    print("[multiobject1c-progress] " + ("PASS" if not failed else "FAIL") + " descriptive_only=true scene_progress_unblocked=true next=next_object")
    print(f"[multiobject1c-check] SUMMARY passed={len(base)-len(failed)} failed={len(failed)}")
    if failed:
        print("[multiobject1c-check] FAIL " + ",".join(failed))
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
