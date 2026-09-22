"""Pure structural checks with genuine source-mutation negatives for MultiObject-3g."""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "tools" / "multiobject3g_public.py"
RUN = ROOT / "tools" / "multiobject3g_run.py"
PROG = ROOT / "tools" / "multiobject3g_progress.py"


def _source(p: Path) -> str:
    return p.read_text()


def _checks(pub: str, run: str, prog: str) -> list[tuple[str, bool]]:
    ast.parse(pub); ast.parse(run); ast.parse(prog)
    return [
        (
            "parent_reactivation_action_consumed_not_handpicked",
            'required_parent_reactivation_status": "LOCAL_POLICY_REACTIVATION_REPRODUCED"' in pub
            and 'gaze = m3f.get("returned_next_gaze_deg")' in run
            and 'target_id = int(m3e.get("selected_object_id", -1))' not in run
            and "ACTION_GAZE =" not in pub and "ACTION_GAZE =" not in run,
        ),
        (
            "attention_causal_parent_required",
            'ATTENTION_ONLY_PRE_FUSION_MAP' in run
            and 'GEOMETRY_ONLY_OLD_ATTENTION_CONTEXT' in run
            and 'if att.get("stop") is not False or not _same_optional_gaze(att.get("next_gaze_deg"), gaze):' in run
            and 'MultiObject-3f attention-only counterfactual does not reproduce the returned gaze' in run,
        ),
        (
            "exact_pre_action_policy_replay",
            'audit3f._exact_decision_replay(m3e["returned_local_policy_decision"], pre_action_replay, "pre-action")' in run
            and '"pre_action_policy_replayed_exactly": True' in run,
        ),
        (
            "one_returned_action_generic_renderer_no_history_rerender",
            "MAX_NEW_FIXATIONS = 1" in pub
            and '"added_fixations": 1' in run
            and '"parent_fixations_rerendered": 0' in run
            and '"-P", public.SCENE_RENDERER' in run
            and "reality2_render_fix.py" not in run,
        ),
        (
            "selected_only_fusion_existing_objects_read_only",
            'target_mask = np.asarray(rec["valid"], bool) & (np.asarray(rec["instance_id"]) == target_id)' in run
            and '"preexisting_objects_read_only": True' in run
            and "scene object {oid} source changed during returned-action execution" in run,
        ),
        (
            "inherited_empty_look_and_fusion_rule",
            "MIN_TARGET_POINTS = int(state_parent.MIN_TARGET_POINTS)" in pub
            and "FUSION = dict(state_parent.FUSION)" in pub
            and "empty = len(patch.xyz_h) < public.MIN_TARGET_POINTS" in run
            and "if not empty:" in run,
        ),
        (
            "single_subsequent_frozen_policy_decision_unexecuted",
            "SUBSEQUENT_POLICY_DECISIONS = 1" in pub
            and run.count("policy.choose_next(") == 2
            and '"subsequent_local_policy_decisions": 1' in run
            and '"subsequent_local_action_executed": False' in run,
        ),
        (
            "bounded_no_scheduler_threshold_or_auto_loop",
            '"automatic_handoff_loop": False' in run
            and '"automatic_local_loop": False' in run
            and '"automatic_scene_scheduler": False' in run
            and '"revisit_scheduler_used": False' in run
            and '"quality_gate_used": False' in run
            and '"new_threshold_added": False' in run
            and '"watchdog_changed": False' in run,
        ),
        (
            "descriptive_outcomes_not_quality_gates",
            'measurement_status = progress.measurement_status(' in run
            and 'next_policy_status = progress.subsequent_policy_status(subsequent)' in run
            and 'return "LOCAL_EXPLORATION_CONTINUES"' in prog
            and "recovery_threshold" not in run.lower(),
        ),
    ]


def _mutate(name: str, pub: str, run: str, prog: str):
    if name == "handpick":
        run = run.replace('gaze = m3f.get("returned_next_gaze_deg")', 'gaze = [18.7, -10.5]', 1)
    elif name == "ignorecausal":
        run = run.replace('if att.get("stop") is not False or not _same_optional_gaze(att.get("next_gaze_deg"), gaze):', 'if False:', 1)
    elif name == "skipreplay":
        run = run.replace('audit3f._exact_decision_replay(m3e["returned_local_policy_decision"], pre_action_replay, "pre-action")', 'pass  # replay skipped', 1)
    elif name == "multiprobe":
        pub = pub.replace("MAX_NEW_FIXATIONS = 1", "MAX_NEW_FIXATIONS = 2", 1)
    elif name == "legacyrenderer":
        run = run.replace('"-P", public.SCENE_RENDERER', '"-P", "tools/reality2_render_fix.py"', 1)
    elif name == "crossfuse":
        run = run.replace('target_mask = np.asarray(rec["valid"], bool) & (np.asarray(rec["instance_id"]) == target_id)', 'target_mask = np.asarray(rec["valid"], bool)', 1)
    elif name == "skipempty":
        run = run.replace("if not empty:", "if True:", 1)
    elif name == "executeagain":
        run = run.replace('"subsequent_local_action_executed": False', '"subsequent_local_action_executed": True')
    elif name == "autoloop":
        run = run.replace('"automatic_local_loop": False', '"automatic_local_loop": True', 1)
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
            print(f"[multiobject3g-negative] ERROR {a.negative} mutation escaped detection")
            raise SystemExit(2)
        print(f"[multiobject3g-negative] PASS {a.negative} detected_by={','.join(detected)}")
        raise SystemExit(1)
    failed = [name for name, ok in base if not ok]
    print("[multiobject3g-action] " + ("PASS" if not failed else "FAIL") + " parent_action_consumed=true one_fixation=true generic_renderer=true selected_only=true")
    print("[multiobject3g-return] " + ("PASS" if not failed else "FAIL") + " pre_action_replay=true one_next_decision=true next_action_executed=false auto_loop=false")
    print(f"[multiobject3g-check] SUMMARY passed={len(base)-len(failed)} failed={len(failed)}")
    if failed:
        print("[multiobject3g-check] FAIL " + ",".join(failed))
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
