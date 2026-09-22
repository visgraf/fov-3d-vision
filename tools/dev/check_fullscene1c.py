"""Pure structural checks with genuine source-mutation negatives for FullScene-1c."""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "tools" / "fullscene1c_public.py"
RUN = ROOT / "tools" / "fullscene1c_run.py"
CMP = ROOT / "tools" / "fullscene1c_compare.py"


def _source(path: Path) -> str:
    return path.read_text()


def _checks(pub: str, run: str, cmp: str) -> list[tuple[str, bool]]:
    ast.parse(pub); ast.parse(run); ast.parse(cmp)
    joined = pub + run + cmp
    return [
        (
            "parent_selected_target_and_scene_ids_not_handpicked",
            'target_id = int(m.get("selected_object_id", -1))' in run
            and 'existing_ids = tuple(int(x) for x in m.get("existing_object_ids_before", []))' in run
            and "selected_object_id = 144" not in joined
            and "TARGET_OBJECT_ID = 144" not in joined
            and "do not hand-pick or hard-code" in pub,
        ),
        (
            "preexisting_read_only_selected_only_growth",
            '"preexisting_objects_read_only": True' in run
            and 'mask = np.asarray(rec["valid"], bool) & (np.asarray(rec["instance_id"]) == int(target_id))' in run
            and 'fuse(\n                sm, p, target_id,' in run
            and "cross-object contamination" in run,
        ),
        (
            "reuse_existing_frozen_adapter",
            "import multiobject2c_policy as policy" in run
            and 'POLICY_ADAPTER = "tools/multiobject2c_policy.py"' in pub
            and "reuse tools/multiobject2c_policy.py unchanged" in pub
            and "fullscene1c_policy" not in joined,
        ),
        (
            "seed_scoped_local_history",
            "active local growth begins at the saved FullScene-1b seed observation only" in pub
            and "history = [policy.history_entry(" in run
            and '"growth_history_starts_at_fullscene1b_seed": True' in run
            and '"older_scene_history_replayed_into_local_policy": False' in run,
        ),
        (
            "generic_renderer_object_scoped_watchdog",
            'SCENE_RENDERER = "tools/scene_render_fix.py"' in pub
            and '"-P", public.SCENE_RENDERER' in run
            and "reality2_render_fix.py" not in run
            and "if len(gazes) >= public.SELECTED_OBJECT_WATCHDOG_FIXATIONS:" in run
            and 'termination = "selected_object_watchdog"' in run,
        ),
        (
            "empty_look_is_negative_evidence_not_abort",
            "valid negative evidence" in pub
            and "if empty:" in run
            and "empty_steps.append(global_step)" in run
            and '"matched": 0, "new": 0' in run
            and "continue_on_empty = False" not in run,
        ),
        (
            "prior_deferred_action_and_handoff_remain_deferred",
            'if m.get("deferred_prior_object_action_executed") is not False:' in run
            and '"deferred_prior_object_action_executed": False' in run
            and '"epistemic_handoffs_added": 0' in run,
        ),
        (
            "diagnostics_separate_no_productivity_gate",
            '"texture_diagnostics_are_gates": False' in run
            and '"productivity_score_synthesized": False' in run
            and '"quality_gate_used": False' in run
            and '"new_threshold_added": False' in run
            and "none becomes a combined productivity score or gate" in pub,
        ),
        (
            "no_scene_scheduler_discovery_truth",
            '"automatic_object_discovery": False' in run
            and '"automatic_scene_scheduler": False' in run
            and '"revisit_scheduler_used": False' in run
            and '"semantic_ranking_used": False' in run
            and '"truth_opened": False' in run,
        ),
    ]


def _mutate(name: str, pub: str, run: str, cmp: str):
    if name == "handpick":
        run = run.replace('target_id = int(m.get("selected_object_id", -1))', 'target_id = 144', 1)
    elif name == "crossfuse":
        run = run.replace(
            'mask = np.asarray(rec["valid"], bool) & (np.asarray(rec["instance_id"]) == int(target_id))',
            'mask = np.asarray(rec["valid"], bool)',
            1,
        )
    elif name == "copypolicy":
        run = run.replace("import multiobject2c_policy as policy", "import fullscene1c_policy as policy", 1)
    elif name == "priorhistory":
        run = run.replace('"older_scene_history_replayed_into_local_policy": False', '"older_scene_history_replayed_into_local_policy": True', 1)
    elif name == "legacyrenderer":
        pub = pub.replace('SCENE_RENDERER = "tools/scene_render_fix.py"', 'SCENE_RENDERER = "tools/reality2_render_fix.py"', 1)
    elif name == "globalwatchdog":
        run = run.replace(
            "if len(gazes) >= public.SELECTED_OBJECT_WATCHDOG_FIXATIONS:",
            "if global_step >= public.SELECTED_OBJECT_WATCHDOG_FIXATIONS:",
            1,
        )
    elif name == "emptyabort":
        run = run.replace("if empty:\n            empty_steps.append(global_step)", "if empty:\n            continue_on_empty = False\n            empty_steps.append(global_step)", 1)
    elif name == "execute_deferred":
        run = run.replace('"deferred_prior_object_action_executed": False', '"deferred_prior_object_action_executed": True', 1)
    elif name == "handoff":
        run = run.replace('"epistemic_handoffs_added": 0', '"epistemic_handoffs_added": 1', 1)
    elif name == "productivitygate":
        run = run.replace('"productivity_score_synthesized": False', '"productivity_score_synthesized": True', 1)
    elif name == "scheduler":
        run = run.replace('"automatic_scene_scheduler": False', '"automatic_scene_scheduler": True', 1)
    elif name == "truth":
        run = run.replace('"truth_opened": False', '"truth_opened": True', 1)
    else:
        raise SystemExit(f"unknown negative: {name}")
    return pub, run, cmp


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--negative"); a = ap.parse_args()
    pub, run, cmp = _source(PUB), _source(RUN), _source(CMP)
    base = _checks(pub, run, cmp)
    if a.negative:
        mp, mr, mc = _mutate(a.negative, pub, run, cmp)
        changed = _checks(mp, mr, mc)
        detected = [n for (n, before), (_, after) in zip(base, changed) if before and not after]
        if not detected:
            print(f"[fullscene1c-negative] ERROR {a.negative} mutation escaped detection")
            raise SystemExit(2)
        print(f"[fullscene1c-negative] PASS {a.negative} detected_by={','.join(detected)}")
        raise SystemExit(1)
    failed = [n for n, ok in base if not ok]
    print("[fullscene1c-growth] " + ("PASS" if not failed else "FAIL") +
          " parent_seed=true selected_from_parent=true preexisting_read_only=true selected_only=true frozen_adapter=true")
    print("[fullscene1c-control] " + ("PASS" if not failed else "FAIL") +
          " seed_scoped_history=true generic_renderer=true object_watchdog=true empty_evidence=true handoff=false")
    print("[fullscene1c-scene] " + ("PASS" if not failed else "FAIL") +
          " deferred_prior_action=false scheduler=false truth=false productivity_gate=false")
    print(f"[fullscene1c-check] SUMMARY passed={len(base)-len(failed)} failed={len(failed)}")
    if failed:
        print("[fullscene1c-check] FAIL " + ",".join(failed))
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
