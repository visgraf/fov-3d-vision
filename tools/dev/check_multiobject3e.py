"""Pure structural checks with genuine source-mutation negatives for MultiObject-3e."""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "tools" / "multiobject3e_public.py"
RUN = ROOT / "tools" / "multiobject3e_run.py"
PROG = ROOT / "tools" / "multiobject3e_progress.py"


def _source(p: Path) -> str:
    return p.read_text()


def _checks(pub: str, run: str, prog: str) -> list[tuple[str, bool]]:
    ast.parse(pub); ast.parse(run); ast.parse(prog)
    return [
        (
            "parent_policy_exhausted_target_consumed_not_handpicked",
            'required_parent_interpretation": "POLICY_EXHAUSTED_WITH_UNSEEN_TERRITORY"' in pub
            and 'target_id = int(m3d.get("selected_object_id", -1))' in run
            and "TARGET_OBJECT_ID =" not in pub
            and "TARGET_OBJECT_ID =" not in run,
        ),
        (
            "reuse_established_epistemic_selector",
            'EPISTEMIC_SELECTOR = "tools/cyclopean1e_gaze.py"' in pub
            and "import cyclopean1e_gaze as epistemic_gaze" in run
            and "epistemic_gaze.select_epistemic_probe(" in run
            and "def select_epistemic_probe" not in run,
        ),
        (
            "bounded_one_fixation_one_return_decision",
            "MAX_HANDOFF_FIXATIONS = 1" in pub
            and "RETURN_POLICY_DECISIONS = 1" in pub
            and '"added_fixations": 1' in run
            and '"returned_local_policy_decisions": 1' in run
            and '"returned_local_action_executed": False' in run
            and '"automatic_handoff_loop": False' in run,
        ),
        (
            "generic_renderer_no_history_rerender",
            'SCENE_RENDERER = growth_parent.SCENE_RENDERER' in pub
            and '"parent_fixations_rerendered": 0' in run
            and "reality2_render_fix.py" not in run,
        ),
        (
            "selected_only_fusion_existing_objects_read_only",
            'target_mask = np.asarray(rec["valid"], bool) & (np.asarray(rec["instance_id"]) == target_id)' in run
            and '"preexisting_objects_read_only": True' in run
            and "scene object {oid} source changed during handoff" in run,
        ),
        (
            "inherited_empty_look_and_fusion_rule",
            "MIN_TARGET_POINTS = int(growth_parent.MIN_TARGET_POINTS)" in pub
            and "FUSION = dict(parent.FUSION)" in pub
            and "empty = len(patch.xyz_h) < public.MIN_TARGET_POINTS" in run
            and "if not empty:" in run,
        ),
        (
            "single_return_to_frozen_local_policy",
            "import multiobject2c_policy as policy" in run
            and run.count("policy.choose_next(") == 1
            and 'policy_adapter_source": public.POLICY_ADAPTER' in run
            and '"policy_source_modified": False' in run,
        ),
        (
            "no_threshold_quality_gate_or_scheduler",
            "texture_threshold" not in run.lower()
            and "new_threshold" not in run.lower()
            and '"quality_gate_used": False' in run
            and '"automatic_scene_scheduler": False' in run
            and '"revisit_scheduler_used": False' in run
            and 'return "LOCAL_POLICY_REACTIVATED"' in prog,
        ),
    ]


def _mutate(name: str, pub: str, run: str, prog: str):
    if name == "handpick":
        run = run.replace('target_id = int(m3d.get("selected_object_id", -1))', 'target_id = 999', 1)
    elif name == "newselector":
        run = run.replace("epistemic_gaze.select_epistemic_probe(", "select_epistemic_probe(", 1)
        run = run.replace("import cyclopean1e_gaze as epistemic_gaze", "def select_epistemic_probe(*args, **kwargs): return None", 1)
    elif name == "multiprobe":
        pub = pub.replace("MAX_HANDOFF_FIXATIONS = 1", "MAX_HANDOFF_FIXATIONS = 2", 1)
    elif name == "legacyrenderer":
        run = run.replace('"-P", public.SCENE_RENDERER', '"-P", "tools/reality2_render_fix.py"', 1)
    elif name == "crossfuse":
        run = run.replace('target_mask = np.asarray(rec["valid"], bool) & (np.asarray(rec["instance_id"]) == target_id)', 'target_mask = np.asarray(rec["valid"], bool)', 1)
    elif name == "skipempty":
        run = run.replace("if not empty:", "if True:", 1)
    elif name == "autoloop":
        run = run.replace('"automatic_handoff_loop": False', '"automatic_handoff_loop": True', 1)
    elif name == "qualitygate":
        run = run.replace('"quality_gate_used": False', '"quality_gate_used": True', 1)
    else:
        raise SystemExit(f"unknown negative: {name}")
    return pub, run, prog


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--negative")
    a = ap.parse_args()
    pub, run, prog = _source(PUB), _source(RUN), _source(PROG)
    base = _checks(pub, run, prog)
    if a.negative:
        mp, mr, mg = _mutate(a.negative, pub, run, prog)
        changed = _checks(mp, mr, mg)
        detected = [name for (name, before), (_, after) in zip(base, changed) if before and not after]
        if not detected:
            print(f"[multiobject3e-negative] ERROR {a.negative} mutation escaped detection")
            raise SystemExit(2)
        print(f"[multiobject3e-negative] PASS {a.negative} detected_by={','.join(detected)}")
        raise SystemExit(1)
    failed = [name for name, ok in base if not ok]
    print("[multiobject3e-handoff] " + ("PASS" if not failed else "FAIL") + " parent_policy_exhausted=true epistemic_selector_reused=true one_fixation=true")
    print("[multiobject3e-return] " + ("PASS" if not failed else "FAIL") + " frozen_local_policy=true one_decision=true returned_action_executed=false auto_loop=false")
    print(f"[multiobject3e-check] SUMMARY passed={len(base)-len(failed)} failed={len(failed)}")
    if failed:
        print("[multiobject3e-check] FAIL " + ",".join(failed))
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
