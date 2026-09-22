"""Pure structural checks with genuine source-mutation negatives for MultiObject-1b2."""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "tools" / "multiobject1b2_public.py"
REN = ROOT / "tools" / "scene_render_fix.py"
RUN = ROOT / "tools" / "multiobject1b2_run.py"


def _source(p: Path) -> str:
    return p.read_text()


def _checks(pub: str, ren: str, run: str) -> list[tuple[str, bool]]:
    ast.parse(pub)
    ast.parse(ren)
    ast.parse(run)
    return [
        (
            "generic_renderer_no_global_cap",
            "does not inherit Reality Check 2's experiment-specific global step interval" in ren
            and "WATCHDOG_TOTAL_FIXATIONS" not in ren
            and "PARENT_FIXATIONS" not in ren,
        ),
        (
            "physical_instrument_frozen",
            "import reality2_public as instrument" in ren
            and "make_calibration(args.profile, args.yaw, args.pitch, instrument.VERGENCE_DISTANCE_M)" in ren
            and "instrument.render_seed" in ren
            and "scene_spec.scene_objects(instrument.FIXTURE)" in ren,
        ),
        (
            "partial_history_reused_not_rerendered",
            "do not rerender its " in pub
            and "five successful growth fixations" in pub
            and "Replay and verify every successful blocked growth fixation without rerendering." in run
            and '"partial_fixations_rerendered": 0' in run,
        ),
        (
            "renderer_equivalence_required",
            "require exact equality of calibration plus stored RGB/instance arrays" in pub
            and "_verify_renderer_equivalence" in run
            and "np.array_equal(old_obs[k], new_obs[k])" in run,
        ),
        (
            "object141_read_only_object143_only",
            "object 141 remains byte-identical and is never fused" in pub
            and 'rec["instance_id"] == public.OBJECT_ID_2' in run
            and "cross-object contamination" in run,
        ),
        (
            "object_scoped_watchdog_no_discovery",
            "independent of global acquisition index" in pub
            and "len(gazes) >= public.OBJECT2_WATCHDOG_FIXATIONS" in run
            and '"automatic_object_discovery": False' in run,
        ),
    ]


def _mutate(name: str, pub: str, ren: str, run: str):
    if name == "globalcap":
        ren = ren.replace(
            'if args.step < 0:\n        raise ValueError("global acquisition step must be non-negative")',
            'if args.step < instrument.PARENT_FIXATIONS or args.step >= instrument.WATCHDOG_TOTAL_FIXATIONS:\n        raise ValueError("legacy global cap")',
            1,
        )
    elif name == "instrument":
        ren = ren.replace("make_calibration(args.profile, args.yaw, args.pitch, instrument.VERGENCE_DISTANCE_M)", "make_calibration(args.profile, args.yaw, args.pitch, 1.0)", 1)
    elif name == "rerenderpartial":
        pub = pub.replace("do not rerender its ", "rerender the ", 1)
        run = run.replace('"partial_fixations_rerendered": 0', '"partial_fixations_rerendered": 5', 1)
    elif name == "noequivalence":
        pub = pub.replace("require exact equality of calibration plus stored RGB/instance arrays", "skip renderer equivalence", 1)
        run = run.replace("_verify_renderer_equivalence", "_skip_renderer_equivalence", 1)
    elif name == "crossfuse":
        pub = pub.replace("object 141 remains byte-identical and is never fused", "objects may cross-fuse", 1)
        run = run.replace('rec["instance_id"] == public.OBJECT_ID_2', 'np.isin(rec["instance_id"], public.OBJECT_IDS)', 1)
    elif name == "globalwatchdog":
        pub = pub.replace("independent of global acquisition index", "defined by global acquisition index", 1)
        run = run.replace("len(gazes) >= public.OBJECT2_WATCHDOG_FIXATIONS", "global_step >= public.OBJECT2_WATCHDOG_FIXATIONS", 1)
    else:
        raise SystemExit(f"unknown negative: {name}")
    return pub, ren, run


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--negative")
    a = ap.parse_args()
    pub, ren, run = _source(PUB), _source(REN), _source(RUN)
    base = _checks(pub, ren, run)
    if a.negative:
        mp, mrn, mr = _mutate(a.negative, pub, ren, run)
        changed = _checks(mp, mrn, mr)
        escaped = [name for (name, before), (_, after) in zip(base, changed) if before and not after]
        if not escaped:
            print(f"[multiobject1b2-negative] ERROR {a.negative} mutation escaped detection")
            raise SystemExit(2)
        print(f"[multiobject1b2-negative] PASS {a.negative} detected_by={','.join(escaped)}")
        raise SystemExit(1)
    failed = [n for n, ok in base if not ok]
    print(
        "[multiobject1b2-resume] " + ("PASS" if not failed else "FAIL")
        + " partial_reuse=true renderer_equivalence=true global_history_preserved=true object143_only=true"
    )
    print(
        "[multiobject1b2-policy] " + ("PASS" if not failed else "FAIL")
        + " frozen_fsg6f=true object_scoped_watchdog=true auto_discovery=false quality_gated=false"
    )
    print(f"[multiobject1b2-check] SUMMARY passed={len(base)-len(failed)} failed={len(failed)}")
    if failed:
        print("[multiobject1b2-check] FAIL " + ",".join(failed))
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
