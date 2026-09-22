"""Pure structural checks with genuine source-mutation negatives for MultiObject-3a."""
from __future__ import annotations
import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "tools" / "multiobject3a_public.py"
SEL = ROOT / "tools" / "multiobject3a_select.py"
RUN = ROOT / "tools" / "multiobject3a_run.py"


def _source(p: Path) -> str:
    return p.read_text()


def _checks(pub: str, sel: str, run: str) -> list[tuple[str, bool]]:
    ast.parse(pub); ast.parse(sel); ast.parse(run)
    return [
        (
            "read_only_no_acquisition",
            "NO_ACQUISITION = True" in pub
            and "subprocess" not in run
            and "blender" not in run.lower()
            and '"acquisitions_added": 0' in run
            and '"fusion_iterations_added": 0' in run,
        ),
        (
            "instantiated_ids_consumed_not_hardcoded",
            "instantiated_ids = tuple(sorted(objects))" in run
            and "len(objects) < 3" in run
            and "INSTANTIATED_OBJECT_IDS" not in pub + sel + run
            and "selected_object_id = 145" not in (pub + sel + run),
        ),
        (
            "updated_history_combined",
            "old_history._all_cases(old_scene, old_manifest)" in run
            and "new_history._all_cases(growth, gm)" in run
            and "old_cases + new_cases" in run
            and "updated scene history is not globally contiguous" in run,
        ),
        (
            "valid_depth_support_only",
            'valid = np.asarray(ob["valid"], dtype=bool)' in sel
            and 'np.count_nonzero((ids == oid) & valid)' in sel
            and "Only valid stereo depth" in sel,
        ),
        (
            "deterministic_argmax_no_threshold",
            'key=lambda r: (-int(r["valid_depth_samples"]), int(r["object_id"]))' in sel
            and "MIN_VALID_SUPPORT" not in pub + sel + run
            and "support_threshold" not in (pub + sel + run).lower(),
        ),
        (
            "progress_without_revisit_scheduler",
            "NEW_OBJECT_INSTANTIATED = False" in pub
            and '"new_object_instantiated": False' in run
            and '"revisit_scheduler_used": False' in run
            and "seed the selected fourth object with one prescribed fixation" in pub,
        ),
    ]


def _mutate(name: str, pub: str, sel: str, run: str):
    if name == "acquire":
        run = run.replace("import argparse", "import argparse\nimport subprocess", 1)
    elif name == "hardcode":
        run = run.replace("instantiated_ids = tuple(sorted(objects))", "instantiated_ids = tuple(sorted(objects))\n    selected_object_id = 145", 1)
    elif name == "oldhistoryonly":
        run = run.replace("all_cases = sorted(old_cases + new_cases, key=lambda x: int(x[0]))", "all_cases = sorted(old_cases, key=lambda x: int(x[0]))", 1)
    elif name == "visibleonly":
        sel = sel.replace('valid = np.asarray(ob["valid"], dtype=bool)', 'valid = np.ones_like(ids, dtype=bool)', 1)
    elif name == "threshold":
        sel = sel.replace("import numpy as np", "import numpy as np\nMIN_VALID_SUPPORT = 1000", 1)
    elif name == "scheduler":
        run = run.replace('"revisit_scheduler_used": False', '"revisit_scheduler_used": True', 1)
    else:
        raise SystemExit(f"unknown negative: {name}")
    return pub, sel, run


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--negative")
    a = ap.parse_args()
    pub, sel, run = _source(PUB), _source(SEL), _source(RUN)
    base = _checks(pub, sel, run)
    if a.negative:
        mp, ms, mr = _mutate(a.negative, pub, sel, run)
        changed = _checks(mp, ms, mr)
        detected = [name for (name, before), (_, after) in zip(base, changed) if before and not after]
        if not detected:
            print(f"[multiobject3a-negative] ERROR {a.negative} mutation escaped detection")
            raise SystemExit(2)
        print(f"[multiobject3a-negative] PASS {a.negative} detected_by={','.join(detected)}")
        raise SystemExit(1)
    failed = [n for n, ok in base if not ok]
    print("[multiobject3a-selection] " + ("PASS" if not failed else "FAIL") + " read_only=true updated_history=true uninstantiated_only=true valid_depth_support=true")
    print("[multiobject3a-progress] " + ("PASS" if not failed else "FAIL") + " handpicked=false seed_deferred=true revisit_scheduler=false quality_gated=false")
    print(f"[multiobject3a-check] SUMMARY passed={len(base)-len(failed)} failed={len(failed)}")
    if failed:
        print("[multiobject3a-check] FAIL " + ",".join(failed))
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
