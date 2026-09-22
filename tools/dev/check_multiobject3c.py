"""Pure structural checks with genuine source-mutation negatives for MultiObject-3c."""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "tools" / "multiobject3c_public.py"
RUN = ROOT / "tools" / "multiobject3c_run.py"
CMP = ROOT / "tools" / "multiobject3c_compare.py"


def _source(p: Path) -> str:
    return p.read_text()


def _checks(pub: str, run: str, cmp: str) -> list[tuple[str, bool]]:
    ast.parse(pub); ast.parse(run); ast.parse(cmp)
    joined = pub + run + cmp
    return [
        (
            "parent_selected_target_and_scene_ids_not_handpicked",
            'target_id = int(m.get("selected_object_id", -1))' in run
            and 'existing_ids = tuple(int(x) for x in m.get("existing_object_ids_before", []))' in run
            and "selected_object_id = 145" not in joined
            and "TARGET_OBJECT_ID = 145" not in joined
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
            and "multiobject3c_policy" not in joined,
        ),
        (
            "seed_scoped_history",
            "active growth begins at the prescribed MultiObject-3b seed observation" in pub
            and "history = [policy.history_entry(" in run
            and "the earlier scene-memory " in pub
            and "observations used for selection and seed placement are not replayed as growth-policy history" in pub,
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
            "empty_evidence_texture_diagnostic_no_scheduler_gate",
            "valid negative evidence" in pub
            and "if empty:" in run
            and "empty_steps.append(global_step)" in run
            and '"texture_diagnostics_are_gates": False' in run
            and '"automatic_scene_scheduler": False' in run
            and '"revisit_scheduler_used": False' in run
            and '"quality_gate_used": False' in run
            and "descriptive only" in pub,
        ),
    ]


def _mutate(name: str, pub: str, run: str, cmp: str):
    if name == "handpick":
        run = run.replace('target_id = int(m.get("selected_object_id", -1))', 'target_id = 145', 1)
    elif name == "crossfuse":
        run = run.replace(
            'mask = np.asarray(rec["valid"], bool) & (np.asarray(rec["instance_id"]) == int(target_id))',
            'mask = np.asarray(rec["valid"], bool)',
            1,
        )
    elif name == "copypolicy":
        run = run.replace("import multiobject2c_policy as policy", "import multiobject3c_policy as policy", 1)
    elif name == "priorhistory":
        pub = pub.replace("observations used for selection and seed placement are not replayed as growth-policy history", "observations used for selection and seed placement are replayed as growth-policy history", 1)
    elif name == "legacyrenderer":
        pub = pub.replace(
            'SCENE_RENDERER = "tools/scene_render_fix.py"',
            'SCENE_RENDERER = "tools/reality2_render_fix.py"',
            1,
        )
    elif name == "globalwatchdog":
        run = run.replace(
            "if len(gazes) >= public.SELECTED_OBJECT_WATCHDOG_FIXATIONS:",
            "if global_step >= public.SELECTED_OBJECT_WATCHDOG_FIXATIONS:",
            1,
        )
    elif name == "texturegate":
        run = run.replace('"texture_diagnostics_are_gates": False', '"texture_diagnostics_are_gates": True', 1)
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
            print(f"[multiobject3c-negative] ERROR {a.negative} mutation escaped detection")
            raise SystemExit(2)
        print(f"[multiobject3c-negative] PASS {a.negative} detected_by={','.join(detected)}")
        raise SystemExit(1)
    failed = [n for n, ok in base if not ok]
    print("[multiobject3c-growth] " + ("PASS" if not failed else "FAIL") +
          " parent_selected=true preexisting_read_only=true selected_only=true reused_frozen_adapter=true seed_scoped_history=true")
    print("[multiobject3c-instrument] " + ("PASS" if not failed else "FAIL") +
          " generic_renderer=true object_scoped_watchdog=true empty_evidence=true texture_diagnostic=true scheduler=false")
    print(f"[multiobject3c-check] SUMMARY passed={len(base)-len(failed)} failed={len(failed)}")
    if failed:
        print("[multiobject3c-check] FAIL " + ",".join(failed))
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
