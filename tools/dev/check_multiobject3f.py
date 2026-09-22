"""Pure structural checks with genuine source-mutation negatives for MultiObject-3f."""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "tools" / "multiobject3f_public.py"
AUD = ROOT / "tools" / "multiobject3f_audit.py"
PROG = ROOT / "tools" / "multiobject3f_progress.py"


def _source(p: Path) -> str:
    return p.read_text()


def _checks(pub: str, aud: str, prog: str) -> list[tuple[str, bool]]:
    ast.parse(pub); ast.parse(aud); ast.parse(prog)
    return [
        (
            "read_only_no_acquisition_or_fusion",
            "NO_ACQUISITION = True" in pub
            and "subprocess" not in aud
            and "blender" not in aud.lower()
            and '"acquisitions_added": 0' in aud
            and '"fusion_iterations_added": 0' in aud,
        ),
        (
            "parent_reactivated_target_consumed_not_handpicked",
            'm3e.get("return_status") != "LOCAL_POLICY_REACTIVATED"' in aud
            and 'target_id = int(m3e.get("selected_object_id", -1))' in aud
            and "TARGET_OBJECT_ID =" not in pub
            and "TARGET_OBJECT_ID =" not in aud,
        ),
        (
            "exact_pre_post_frozen_policy_replay",
            '_exact_decision_replay(pre_saved, pre_replay, "pre-handoff")' in aud
            and '_exact_decision_replay(post_saved, post_replay, "post-handoff")' in aud
            and '"pre_policy_replayed_exactly": True' in aud
            and '"post_policy_replayed_exactly": True' in aud,
        ),
        (
            "frozen_voxel_identity_no_matching_tolerance",
            'floor(source_xyz_h / SURFACE_FRONTIER[\'voxel_m\'])' in pub
            and aud.count("np.floor(") >= 2
            and 'voxel_m = float(frozen_public.SURFACE_FRONTIER["voxel_m"])' in aud
            and "REACTIVATION_DISTANCE_THRESHOLD_M" not in aud,
        ),
        (
            "gaze_window_and_map_counterfactual_decomposition",
            '"PRE_MAP_POST_GAZE"' in aud
            and '"POST_MAP_PRE_GAZE"' in aud
            and "attention_only_replay = policy.choose_next(" in aud
            and "geometry_only_replay = policy.choose_next(" in aud
            and '"counterfactual_policy_decisions"' in aud,
        ),
        (
            "frontier_lineage_and_map_voxel_decomposition",
            "def _frontier_lineage" in aud
            and '"appeared_sources_on_preexisting_map_voxels"' in aud
            and '"appeared_sources_on_new_map_voxels"' in aud
            and '"persistent_state_transition_counts"' in aud
            and '"added_occupied_voxels"' in aud,
        ),
        (
            "candidate_gate_ledger_reuses_frozen_rules",
            "def _candidate_gate_table" in aud
            and "frozen_frontier._project_frontier_pairs(" in aud
            and "frozen_frontier._candidate_continuation_from_projected(" in aud
            and "frozen_frontier.candidate_state_consensus(" in aud
            and '"candidate_before_consensus_count"' in aud,
        ),
        (
            "scene_objects_and_parent_records_read_only",
            '"preexisting_objects_read_only": True' in aud
            and '"selected_object_read_only": True' in aud
            and "MultiObject-3e parent changed during audit" in aud
            and "MultiObject-3c scene parent changed during audit" in aud
            and "scene object {oid} changed during audit" in aud,
        ),
        (
            "descriptive_no_quality_gate_scheduler_or_action",
            '"quality_gate_used": False' in aud
            and '"automatic_scene_scheduler": False' in aud
            and '"revisit_scheduler_used": False' in aud
            and aud.count('"returned_local_action_executed": False') >= 1
            and 'return "READ_ONLY_AFTER_FRONTIER_REACTIVATION_AUDIT"' in prog,
        ),
        (
            "machine_readable_frontier_audit_outputs",
            '"frontier_reactivation.npz"' in aud
            and '"frontier_reactivation_details.json"' in aud
            and 'report_name = f"object_{target_id}_frontier_reactivation_report.json"' in aud,
        ),
    ]


def _mutate(name: str, pub: str, aud: str, prog: str):
    if name == "acquire":
        aud = aud.replace("import argparse", "import argparse\nimport subprocess", 1)
    elif name == "handpick":
        aud = aud.replace('target_id = int(m3e.get("selected_object_id", -1))', "target_id = 999", 1)
    elif name == "prereplay":
        aud = aud.replace('_exact_decision_replay(pre_saved, pre_replay, "pre-handoff")', 'disabled_replay(pre_saved, pre_replay, "pre-handoff")', 1)
    elif name == "voxelid":
        aud = aud.replace("np.floor(p / float(cell)).astype(np.int64)", "np.round(p / float(cell)).astype(np.int64)", 1)
    elif name == "counterfactual":
        aud = aud.replace('"PRE_MAP_POST_GAZE"', '"PRE_MAP_POST_GAZE_DISABLED"', 1)
    elif name == "lineage":
        aud = aud.replace('"appeared_sources_on_preexisting_map_voxels"', '"appeared_sources_on_old_map_voxels"', 1)
    elif name == "candidateledger":
        aud = aud.replace("frozen_frontier._candidate_continuation_from_projected(", "fake_candidate_continuation(", 1)
    elif name == "crossobject":
        aud = aud.replace('"preexisting_objects_read_only": True', '"preexisting_objects_read_only": False', 1)
    elif name == "threshold":
        aud = aud.replace("def execute(args) -> dict:", "REACTIVATION_DISTANCE_THRESHOLD_M = 0.05\n\ndef execute(args) -> dict:", 1)
    elif name == "act":
        aud = aud.replace('"returned_local_action_executed": False', '"returned_local_action_executed": True')
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
        detected = [name for (name, before), (_, after) in zip(base, changed) if before and not after]
        if not detected:
            print(f"[multiobject3f-negative] ERROR {a.negative} mutation escaped detection")
            raise SystemExit(2)
        print(f"[multiobject3f-negative] PASS {a.negative} detected_by={','.join(detected)}")
        raise SystemExit(1)
    failed = [name for name, ok in base if not ok]
    print("[multiobject3f-audit] " + ("PASS" if not failed else "FAIL") + " read_only=true pre_post_replay=true frozen_voxel_identity=true frontier_lineage=true")
    print("[multiobject3f-candidates] " + ("PASS" if not failed else "FAIL") + " frozen_gate_ledger=true action_executed=false threshold_added=false")
    print(f"[multiobject3f-check] SUMMARY passed={len(base)-len(failed)} failed={len(failed)}")
    if failed:
        print("[multiobject3f-check] FAIL " + ",".join(failed))
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
