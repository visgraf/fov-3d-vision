"""Pure structural checks with genuine source-mutation negatives for MultiObject-2c."""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "tools" / "multiobject2c_public.py"
POL = ROOT / "tools" / "multiobject2c_policy.py"
RUN = ROOT / "tools" / "multiobject2c_run.py"


def _source(p: Path) -> str:
    return p.read_text()


def _checks(pub: str, pol: str, run: str) -> list[tuple[str, bool]]:
    ast.parse(pub); ast.parse(pol); ast.parse(run)
    return [
        (
            "parent_selected_target_not_handpicked",
            'target_id = int(m.get("selected_object_id", -1))' in run
            and "selected_object_id = 142" not in (pub + pol + run)
            and "TARGET_OBJECT_ID = 142" not in (pub + pol + run)
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
            "frozen_fsg6f_adapter",
            "import fsg6f_frontier as frozen_policy" in pol
            and "return frozen_policy.choose_next(" in pol
            and "FSG6f frontier/controller source" in pub,
        ),
        (
            "seed_scoped_history",
            "active growth begins at the prescribed MultiObject-2b seed observation" in pub
            and "history = [policy.history_entry(" in run
            and "earlier observations used" in pub,
        ),
        (
            "generic_renderer_object_scoped_watchdog",
            'SCENE_RENDERER = "tools/scene_render_fix.py"' in pub
            and '"-P", public.SCENE_RENDERER' in run
            and "reality2_render_fix.py" not in run
            and "if len(gazes) >= public.OBJECT3_WATCHDOG_FIXATIONS:" in run
            and 'termination = "object3_watchdog"' in run,
        ),
        (
            "empty_evidence_texture_diagnostic_no_scheduler_gate",
            "valid negative evidence" in pub
            and "if empty:" in run
            and "empty_steps.append(global_step)" in run
            and '"texture_diagnostics_are_gates": False' in run
            and '"automatic_scene_scheduler": False' in run
            and '"quality_gate_used": False' in run
            and "descriptive measurements" in pub,
        ),
    ]


def _mutate(name: str, pub: str, pol: str, run: str):
    if name == "handpick":
        run = run.replace('target_id = int(m.get("selected_object_id", -1))', 'target_id = 142', 1)
    elif name == "crossfuse":
        run = run.replace(
            'mask = np.asarray(rec["valid"], bool) & (np.asarray(rec["instance_id"]) == int(target_id))',
            'mask = np.asarray(rec["valid"], bool) & np.isin(np.asarray(rec["instance_id"]), [141, 142, 143])',
            1,
        )
    elif name == "copypolicy":
        pol = pol.replace("import fsg6f_frontier as frozen_policy", "# copied local policy instead", 1)
    elif name == "priorhistory":
        pub = pub.replace("earlier observations used", "all earlier observations replayed", 1)
    elif name == "legacyrenderer":
        pub = pub.replace(
            'SCENE_RENDERER = "tools/scene_render_fix.py"',
            'SCENE_RENDERER = "tools/reality2_render_fix.py"',
            1,
        )
    elif name == "globalwatchdog":
        run = run.replace(
            "if len(gazes) >= public.OBJECT3_WATCHDOG_FIXATIONS:",
            "if global_step >= public.OBJECT3_WATCHDOG_FIXATIONS:",
            1,
        )
    elif name == "texturegate":
        run = run.replace('"texture_diagnostics_are_gates": False', '"texture_diagnostics_are_gates": True', 1)
    else:
        raise SystemExit(f"unknown negative: {name}")
    return pub, pol, run


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--negative"); a = ap.parse_args()
    pub, pol, run = _source(PUB), _source(POL), _source(RUN)
    base = _checks(pub, pol, run)
    if a.negative:
        mp, ml, mr = _mutate(a.negative, pub, pol, run)
        changed = _checks(mp, ml, mr)
        detected = [n for (n, before), (_, after) in zip(base, changed) if before and not after]
        if not detected:
            print(f"[multiobject2c-negative] ERROR {a.negative} mutation escaped detection")
            raise SystemExit(2)
        print(f"[multiobject2c-negative] PASS {a.negative} detected_by={','.join(detected)}")
        raise SystemExit(1)
    failed = [n for n, ok in base if not ok]
    print("[multiobject2c-growth] " + ("PASS" if not failed else "FAIL") +
          " parent_selected=true preexisting_read_only=true selected_only=true frozen_fsg6f=true seed_scoped_history=true")
    print("[multiobject2c-instrument] " + ("PASS" if not failed else "FAIL") +
          " generic_renderer=true object_scoped_watchdog=true empty_evidence=true texture_diagnostic=true scheduler=false")
    print(f"[multiobject2c-check] SUMMARY passed={len(base)-len(failed)} failed={len(failed)}")
    if failed:
        print("[multiobject2c-check] FAIL " + ",".join(failed))
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
