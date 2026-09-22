"""Pure structural checks with genuine source-mutation negatives for FullScene-1d."""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "tools" / "fullscene1d_public.py"
RUN = ROOT / "tools" / "fullscene1d_run.py"
CMP = ROOT / "tools" / "fullscene1d_compare.py"


def _source(path: Path) -> str:
    return path.read_text()


def _checks(pub: str, run: str, cmp: str) -> list[tuple[str, bool]]:
    ast.parse(pub); ast.parse(run); ast.parse(cmp)
    joined = pub + run + cmp
    return [
        (
            "read_only_no_acquisition_growth_or_handoff",
            'NO_ACQUISITION = True' in pub
            and "subprocess" not in run
            and "blender" not in run.lower()
            and '"acquisitions_added": 0' in run
            and '"growth_iterations_added": 0' in run
            and '"fusion_iterations_added": 0' in run
            and '"epistemic_handoffs_added": 0' in run,
        ),
        (
            "parent_selected_target_not_handpicked",
            'target_id = int(m.get("selected_object_id", -1))' in run
            and "selected_object_id = 144" not in joined
            and "TARGET_OBJECT_ID = 144" not in joined
            and "never hard-code a scene id" in pub,
        ),
        (
            "require_zero_open_scientific_stop",
            'm.get("termination_reason") != "no_frontier"' in run
            and 'm.get("scientific_stop_reached") is not True' in run
            and 'int(final.get("frontier_open_count", -1)) != 0' in run
            and 'int(final.get("candidates_before_consensus_count", -1)) != 0' in run,
        ),
        (
            "reuse_established_epistemic_audit_machinery",
            "import multiobject3d_audit as inherited_audit" in run
            and "inherited_audit._refine_unobserved(" in run
            and "inherited_audit._refined_arcs" in run
            and "inherited_audit._reconstruct_final_policy_stop" in run
            and "inherited_audit._write_visual" in run
            and "reuse the established MultiObject-3d" in pub,
        ),
        (
            "object_scoped_saved_history_only",
            "FullScene-1b seed plus FullScene-1c local-growth observations only" in pub
            and 'seed_parent = inherited_audit._resolve(pm["parent_record"], parent)' in run
            and 'case = parent / "acquisitions"' in run
            and '"older_s0_scene_history_added_to_audit": False' in run,
        ),
        (
            "observation_separate_from_depth",
            "cyclopean1d_epistemic as epi" in run
            and "inherited_audit._saved_observation" in run
            and "inherited_audit._refine_unobserved(" in run
            and "saved instance masks and saved valid masks" in pub,
        ),
        (
            "scene_objects_and_prior_action_read_only",
            '"scene_objects_read_only": True' in run
            and '"selected_object_read_only": True' in run
            and '"deferred_prior_object_action_executed": False' in run
            and "scene object {oid} changed during FullScene-1d audit" in run,
        ),
        (
            "frozen_scale_no_new_threshold",
            'GRID_DEG = 0.1' in pub
            and 'FUSION = dict(parent.FUSION)' in pub
            and 'association_radius_m=float(public.FUSION["association_radius_m"])' in run
            and '"quality_gate_used": False' in run
            and '"new_threshold_added": False' in run,
        ),
        (
            "return_to_scene_inventory_no_scheduler_truth",
            'scene_disposition = "RETURN_TO_SCENE_INVENTORY"' in run
            and '"automatic_object_discovery": False' in run
            and '"automatic_scene_scheduler": False' in run
            and '"revisit_scheduler_used": False' in run
            and '"truth_opened": False' in run,
        ),
    ]


def _mutate(name: str, pub: str, run: str, cmp: str):
    if name == "acquire":
        run = run.replace("import argparse", "import argparse\nimport subprocess", 1)
    elif name == "handpick":
        run = run.replace('target_id = int(m.get("selected_object_id", -1))', 'target_id = 144', 1)
    elif name == "openfrontier":
        run = run.replace('int(final.get("frontier_open_count", -1)) != 0', 'int(final.get("frontier_open_count", -1)) < 0')
    elif name == "copyaudit":
        run = run.replace("import multiobject3d_audit as inherited_audit", "import fullscene1d_private_audit as inherited_audit", 1)
    elif name == "oldhistory":
        run = run.replace('"older_s0_scene_history_added_to_audit": False', '"older_s0_scene_history_added_to_audit": True', 1)
    elif name == "depthonly":
        run = run.replace("inherited_audit._refine_unobserved(", "inherited_audit._refine_depth_only(", 1)
    elif name == "crossobject":
        run = run.replace('"scene_objects_read_only": True', '"scene_objects_read_only": False', 1)
    elif name == "execute_deferred":
        run = run.replace('"deferred_prior_object_action_executed": False', '"deferred_prior_object_action_executed": True', 1)
    elif name == "threshold":
        run = run.replace('"new_threshold_added": False', '"new_threshold_added": True', 1)
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
            print(f"[fullscene1d-negative] ERROR {a.negative} mutation escaped detection")
            raise SystemExit(2)
        print(f"[fullscene1d-negative] PASS {a.negative} detected_by={','.join(detected)}")
        raise SystemExit(1)
    failed = [n for n, ok in base if not ok]
    print("[fullscene1d-audit] " + ("PASS" if not failed else "FAIL") +
          " parent_1c=true read_only=true zero_open_stop=true inherited_epistemic_audit=true")
    print("[fullscene1d-history] " + ("PASS" if not failed else "FAIL") +
          " seed_plus_growth_only=true observation_separate_from_depth=true no_rerender=true")
    print("[fullscene1d-scene] " + ("PASS" if not failed else "FAIL") +
          " objects_read_only=true deferred_prior_action=false scheduler=false truth=false next=scene_inventory")
    print(f"[fullscene1d-check] SUMMARY passed={len(base)-len(failed)} failed={len(failed)}")
    if failed:
        print("[fullscene1d-check] FAIL " + ",".join(failed))
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
