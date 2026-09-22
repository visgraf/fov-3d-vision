"""Pure structural checks with genuine source-mutation negatives for FullScene-1a."""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "tools" / "fullscene1a_public.py"
RUN = ROOT / "tools" / "fullscene1a_run.py"


def _source(path: Path) -> str:
    return path.read_text()


def _checks(pub: str, run: str) -> list[tuple[str, bool]]:
    ast.parse(pub); ast.parse(run)
    return [
        (
            "post_3h_parent_snapshot_no_deferred_action",
            'PARENT_SPEC_ID = parent.SPEC_ID' in pub
            and 'if m.get("subsequent_local_action_executed") is not False:' in run
            and '"deferred_local_action_executed": False' in run,
        ),
        (
            "live_scene_ids_consumed_not_hardcoded",
            'by_id = {int(r["object_id"]): r for r in rows}' in run
            and 'instantiated = tuple(sorted(by_id))' in run
            and "INSTANTIATED_OBJECT_IDS =" not in pub
            and "INSTANTIATED_OBJECT_IDS =" not in run,
        ),
        (
            "complete_declared_history_through_3h",
            'history_143._all_cases(old_scene, m1b2)' in run
            and 'history_142._all_cases(growth142, m2c)' in run
            and 'history_145._all_cases(parent3c, m3c)' in run
            and 'tail = [(handoff_step, handoff_case), (action80_step, action80_case), (action81_step, action81_case)]' in run
            and 'expected = list(range(18, expected_last + 1))' in run,
        ),
        (
            "reuse_valid_depth_scene_selector",
            'import multiobject3a_select as selector' in run
            and 'selector.accumulate_candidate_support(observations, instantiated)' in run
            and 'selector.select_next_object(candidates)' in run
            and "def accumulate_candidate_support" not in run,
        ),
        (
            "persistent_scene_objects_read_only",
            '"scene_objects_read_only": True' in run
            and 'persistent scene-object geometry changed during FullScene-1a' in run
            and '"read_only_in_snapshot": True' in run,
        ),
        (
            "no_acquisition_fusion_or_growth",
            '"acquisitions_added": 0' in run
            and '"fusion_iterations_added": 0' in run
            and '"growth_iterations_added": 0' in run
            and "subprocess.run(" not in run
            and "fuse(" not in run,
        ),
        (
            "selection_and_status_are_descriptive",
            '"quality_gate_used": False' in run
            and '"new_threshold_added": False' in run
            and '"semantic_ranking_used": False' in run
            and "novelty_threshold" not in run.lower()
            and "recovery_threshold" not in run.lower(),
        ),
        (
            "no_truth_scheduler_or_discovery",
            '"truth_opened": False' in run
            and '"automatic_object_discovery": False' in run
            and '"automatic_scene_scheduler": False' in run
            and '"revisit_scheduler_used": False' in run,
        ),
        (
            "fullscene_initial_condition_only",
            '"fullscene_initial_condition": True' in run
            and '"snapshot_id": public.SNAPSHOT_ID' in run
            and '"new_object_instantiated": False' in run
            and 'NEXT_STAGE_IF_SELECTED' in pub,
        ),
    ]


def _mutate(name: str, pub: str, run: str):
    if name == "acquire":
        run = run.replace('out.mkdir(parents=True)', 'out.mkdir(parents=True)\n    subprocess.run(["blender"])', 1)
    elif name == "hardcode":
        run = run.replace('instantiated = tuple(sorted(by_id))', 'instantiated = (141, 142, 143, 145)', 1)
    elif name == "oldhistoryonly":
        run = run.replace('groups.append(("selected_object_145_base", history_145._all_cases(parent3c, m3c), history_145._saved_observation))', '# omitted current-object history', 1)
    elif name == "visibleonly":
        run = run.replace('selector.accumulate_candidate_support(observations, instantiated)', 'visible_only_support(observations, instantiated)', 1)
    elif name == "crossobject":
        run = run.replace('"scene_objects_read_only": True', '"scene_objects_read_only": False', 1)
    elif name == "execute_deferred":
        run = run.replace('"deferred_local_action_executed": False', '"deferred_local_action_executed": True', 1)
    elif name == "scheduler":
        run = run.replace('"automatic_scene_scheduler": False', '"automatic_scene_scheduler": True')
    elif name == "truth":
        run = run.replace('"truth_opened": False', '"truth_opened": True')
    elif name == "threshold":
        run = run.replace('"new_threshold_added": False', '"new_threshold_added": True', 1)
    else:
        raise SystemExit(f"unknown negative: {name}")
    return pub, run


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--negative")
    a = ap.parse_args()
    pub, run = _source(PUB), _source(RUN)
    base = _checks(pub, run)
    if a.negative:
        mp, mr = _mutate(a.negative, pub, run)
        changed = _checks(mp, mr)
        detected = [name for (name, before), (_, after) in zip(base, changed) if before and not after]
        if not detected:
            print(f"[fullscene1a-negative] ERROR {a.negative} mutation escaped detection")
            raise SystemExit(2)
        print(f"[fullscene1a-negative] PASS {a.negative} detected_by={','.join(detected)}")
        raise SystemExit(1)
    failed = [name for name, ok in base if not ok]
    print("[fullscene1a-snapshot] " + ("PASS" if not failed else "FAIL") + " parent_3h=true read_only=true history_through_3h=true")
    print("[fullscene1a-inventory] " + ("PASS" if not failed else "FAIL") + " live_scene_graph=true object_maps_read_only=true status_descriptive=true")
    print("[fullscene1a-selection] " + ("PASS" if not failed else "FAIL") + " valid_depth_only=true frozen_selector=true no_threshold=true")
    print(f"[fullscene1a-check] SUMMARY passed={len(base)-len(failed)} failed={len(failed)}")
    if failed:
        print("[fullscene1a-check] FAIL " + ",".join(failed))
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
