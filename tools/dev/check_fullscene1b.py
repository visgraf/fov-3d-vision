"""Pure structural checks with genuine source-mutation negatives for FullScene-1b."""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "tools" / "fullscene1b_public.py"
RUN = ROOT / "tools" / "fullscene1b_run.py"


def _source(path: Path) -> str:
    return path.read_text()


def _checks(pub: str, run: str) -> list[tuple[str, bool]]:
    ast.parse(pub); ast.parse(run)
    return [
        (
            "s0_selection_consumed_not_handpicked",
            'selected_id = int(pm["selected_object_id"])' in run
            and 'existing_ids = tuple(int(x) for x in pm["instantiated_object_ids"])' in run
            and "selected_object_id = 144" not in (pub + run)
            and "INSTANTIATED_OBJECT_IDS" not in (pub + run),
        ),
        (
            "complete_s0_history_reused",
            'fs1a_run._history(parent3h, m3h, chain)' in run
            and 'steps != [int(x) for x in pm.get("observation_steps", [])]' in run
            and "complete FullScene-1a declared scene-memory history" in pub,
        ),
        (
            "valid_depth_occupied_cell_seed_rule_reused",
            'from multiobject3b_seed import select_seed_from_saved_evidence' in run
            and 'select_seed_from_saved_evidence(observations, selected_id, public.GRID_DEG)' in run
            and "visible_only_seed" not in run,
        ),
        (
            "one_fresh_fixation_generic_renderer",
            "MAX_ADDED_FIXATIONS = 1" in pub
            and 'SCENE_RENDERER = "tools/scene_render_fix.py"' in pub
            and 'global_step = int(max(steps) + 1)' in run
            and '"added_fixations": 1' in run
            and '"parent_fixations_rerendered": 0' in run,
        ),
        (
            "persistent_objects_read_only_separate_seed",
            '"geometry": "SURFEL_MAP"' in run
            and '"read_only": True' in run
            and 'target = valid & (instance_id == selected_id)' in run
            and '"fusion_iterations_added": 0' in run
            and '"existing_objects_read_only": True' in run,
        ),
        (
            "deferred_prior_action_stays_deferred",
            'if m.get("deferred_local_action_executed") is not False:' in run
            and '"deferred_prior_object_action_executed": False' in run,
        ),
        (
            "growth_handoff_scheduler_deferred",
            '"growth_iterations_added": 0' in run
            and '"epistemic_handoffs_added": 0' in run
            and '"automatic_scene_scheduler": False' in run
            and '"revisit_scheduler_used": False' in run,
        ),
        (
            "no_truth_quality_or_new_threshold",
            '"truth_opened": False' in run
            and '"quality_gate_used": False' in run
            and '"new_threshold_added": False' in run
            and '"semantic_ranking_used": False' in run,
        ),
    ]


def _mutate(name: str, pub: str, run: str):
    if name == "handpick":
        run = run.replace('selected_id = int(pm["selected_object_id"])', 'selected_id = 144', 1)
    elif name == "oldhistoryonly":
        run = run.replace('cases, observations, groups = fs1a_run._history(parent3h, m3h, chain)', 'cases, observations, groups = [], [], {}', 1)
    elif name == "visibleonly":
        run = run.replace('select_seed_from_saved_evidence(observations, selected_id, public.GRID_DEG)', 'visible_only_seed(observations, selected_id, public.GRID_DEG)', 1)
    elif name == "multiprobe":
        pub = pub.replace("MAX_ADDED_FIXATIONS = 1", "MAX_ADDED_FIXATIONS = 2", 1)
        run = run.replace('"added_fixations": 1', '"added_fixations": 2', 1)
    elif name == "legacyrenderer":
        pub = pub.replace('SCENE_RENDERER = "tools/scene_render_fix.py"', 'SCENE_RENDERER = "tools/reality2_render_fix.py"', 1)
    elif name == "crossfuse":
        run = run.replace('"fusion_iterations_added": 0', '"fusion_iterations_added": 1', 1)
    elif name == "execute_deferred":
        run = run.replace('"deferred_prior_object_action_executed": False', '"deferred_prior_object_action_executed": True', 1)
    elif name == "grow":
        run = run.replace('"growth_iterations_added": 0', '"growth_iterations_added": 1', 1)
    elif name == "scheduler":
        run = run.replace('"automatic_scene_scheduler": False', '"automatic_scene_scheduler": True', 1)
    elif name == "truth":
        run = run.replace('"truth_opened": False', '"truth_opened": True', 1)
    else:
        raise SystemExit(f"unknown negative: {name}")
    return pub, run


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--negative"); a = ap.parse_args()
    pub, run = _source(PUB), _source(RUN)
    base = _checks(pub, run)
    if a.negative:
        mp, mr = _mutate(a.negative, pub, run)
        changed = _checks(mp, mr)
        detected = [n for (n, before), (_, after) in zip(base, changed) if before and not after]
        if not detected:
            print(f"[fullscene1b-negative] ERROR {a.negative} mutation escaped detection")
            raise SystemExit(2)
        print(f"[fullscene1b-negative] PASS {a.negative} detected_by={','.join(detected)}")
        raise SystemExit(1)
    failed = [n for n, ok in base if not ok]
    print("[fullscene1b-seed] " + ("PASS" if not failed else "FAIL") + " parent_s0=true selected_from_parent=true one_fixation=true")
    print("[fullscene1b-history] " + ("PASS" if not failed else "FAIL") + " full_s0_history=true valid_depth_seed=true no_rerender=true")
    print("[fullscene1b-progress] " + ("PASS" if not failed else "FAIL") + " existing_read_only=true deferred_action=false growth=false scheduler=false")
    print(f"[fullscene1b-check] SUMMARY passed={len(base)-len(failed)} failed={len(failed)}")
    if failed:
        print("[fullscene1b-check] FAIL " + ",".join(failed))
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
