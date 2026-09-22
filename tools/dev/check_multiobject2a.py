"""Pure structural checks with genuine source-mutation negatives for MultiObject-2a."""
from __future__ import annotations
import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "tools" / "multiobject2a_public.py"
SEL = ROOT / "tools" / "multiobject2a_select.py"
RUN = ROOT / "tools" / "multiobject2a_run.py"


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
            "uninstantiated_candidates_only",
            "oid <= 0 or oid in instantiated" in sel
            and '"instantiated_object_ids": list(public.INSTANTIATED_OBJECT_IDS)' in run
            and "already-instantiated object" in pub,
        ),
        (
            "valid_depth_support_only",
            'valid = np.asarray(ob["valid"], dtype=bool)' in sel
            and 'np.count_nonzero((ids == oid) & valid)' in sel
            and "Visibility without" in sel,
        ),
        (
            "deterministic_argmax_no_threshold",
            'key=lambda r: (-int(r["valid_depth_samples"]), int(r["object_id"]))' in sel
            and "MIN_VALID_SUPPORT" not in pub + sel + run
            and "support_threshold" not in (pub + sel + run).lower(),
        ),
        (
            "selection_not_handpicked",
            "select_next_object(candidates)" in run
            and "SELECTED_OBJECT_ID" not in pub + sel + run
            and "selected_object_id = 142" not in (pub + sel + run),
        ),
        (
            "seed_deferred_no_scheduler",
            "NEW_OBJECT_INSTANTIATED = False" in pub
            and '"new_object_instantiated": False' in run
            and "seed the selected next object with one prescribed fixation" in pub
            and "scene scheduler beyond this single next-object selection" in pub,
        ),
    ]


def _mutate(name: str, pub: str, sel: str, run: str):
    if name == "acquire":
        run = run.replace("import argparse", "import argparse\nimport subprocess", 1)
    elif name == "instantiated":
        sel = sel.replace("if oid <= 0 or oid in instantiated:", "if oid <= 0:", 1)
    elif name == "visibleonly":
        sel = sel.replace('valid = np.asarray(ob["valid"], dtype=bool)', 'valid = np.ones_like(ids, dtype=bool)', 1)
    elif name == "threshold":
        sel = sel.replace("import numpy as np", "import numpy as np\nMIN_VALID_SUPPORT = 1000", 1)
    elif name == "handpick":
        run = run.replace("selection = select_next_object(candidates)", 'selection = {"selection_status": "NEXT_OBJECT_SELECTED", "selected_object_id": 142, "selected_valid_depth_samples": 0}', 1)
    elif name == "grow":
        pub = pub.replace("NEW_OBJECT_INSTANTIATED = False", "NEW_OBJECT_INSTANTIATED = True", 1)
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
        escaped = [name for (name, before), (_, after) in zip(base, changed) if before and not after]
        if not escaped:
            print(f"[multiobject2a-negative] ERROR {a.negative} mutation escaped detection")
            raise SystemExit(2)
        print(f"[multiobject2a-negative] PASS {a.negative} detected_by={','.join(escaped)}")
        raise SystemExit(1)
    failed = [n for n, ok in base if not ok]
    print("[multiobject2a-selection] " + ("PASS" if not failed else "FAIL") + " read_only=true uninstantiated_only=true valid_depth_support=true deterministic_argmax=true")
    print("[multiobject2a-progress] " + ("PASS" if not failed else "FAIL") + " handpicked=false seed_deferred=true scheduler=false quality_gated=false")
    print(f"[multiobject2a-check] SUMMARY passed={len(base)-len(failed)} failed={len(failed)}")
    if failed:
        print("[multiobject2a-check] FAIL " + ",".join(failed))
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
