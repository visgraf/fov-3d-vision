"""Pure structural checks with genuine source-mutation negatives for MultiObject-1b."""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "tools" / "multiobject1b_public.py"
POL = ROOT / "tools" / "multiobject1b_policy.py"
RUN = ROOT / "tools" / "multiobject1b_run.py"


def _source(p: Path) -> str: return p.read_text()


def _checks(pub: str, pol: str, run: str) -> list[tuple[str, bool]]:
    ast.parse(pub); ast.parse(pol); ast.parse(run)
    return [
        ("object141_read_only", "object-141 geometry source remain read only" in pub and '"object_1_read_only": True' in run),
        ("object143_only_growth", "grow only id 143" in pub and "rec[\"instance_id\"] == public.OBJECT_ID_2" in run and "cross-object contamination" in run),
        ("frozen_fsg6f_adapter", "import fsg6f_frontier as frozen_policy" in pol and "return frozen_policy.choose_next(" in pol and "FSG6f frontier/controller source" in pub),
        ("seed_scoped_history", "growth-policy history" in pub and "history = [policy.history_entry" in run and "earlier incidental id-143 observations" in pub),
        ("empty_look_is_evidence", "valid negative evidence" in pub and "if empty:" in run and "empty_steps.append(global_step)" in run and "history.append(policy.history_entry" in run),
        ("no_discovery_or_quality_gate", "no automatic object discovery" in pub and '"automatic_object_discovery": False' in run and "measurements, not PASS gates" in pub),
    ]


def _mutate(name: str, pub: str, pol: str, run: str):
    if name == "object1grow":
        pub = pub.replace("object-141 geometry source remain read only", "object-141 geometry may be modified", 1)
    elif name == "crossfuse":
        pub = pub.replace("grow only id 143", "grow ids 141 and 143", 1)
        run = run.replace('rec["instance_id"] == public.OBJECT_ID_2', 'np.isin(rec["instance_id"], public.OBJECT_IDS)', 1)
    elif name == "copypolicy":
        pol = pol.replace("import fsg6f_frontier as frozen_policy", "# copied local policy instead", 1)
    elif name == "priorhistory":
        pub = pub.replace("earlier incidental id-143 observations", "earlier incidental observations are replayed", 1)
    elif name == "emptyabort":
        pub = pub.replace("valid negative evidence", "runtime failure", 1)
        run = run.replace("empty_steps.append(global_step)", "raise RuntimeError('empty object-143 look')", 1)
    elif name == "autodiscover":
        pub = pub.replace("no automatic object discovery", "automatic object discovery", 1)
        run = run.replace('"automatic_object_discovery": False', '"automatic_object_discovery": True', 1)
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
        escaped = [name for (name, before), (_, after) in zip(base, changed) if before and not after]
        if not escaped:
            print(f"[multiobject1b-negative] ERROR {a.negative} mutation escaped detection")
            raise SystemExit(2)
        print(f"[multiobject1b-negative] PASS {a.negative} detected_by={','.join(escaped)}")
        raise SystemExit(1)
    failed = [n for n, ok in base if not ok]
    print("[multiobject1b-growth] " + ("PASS" if not failed else "FAIL") + " object141_read_only=true object143_only=true frozen_fsg6f=true seed_scoped_history=true empty_evidence=true")
    print("[multiobject1b-policy] " + ("PASS" if not failed else "FAIL") + " parent=multiobject1a independent_growth=true auto_discovery=false quality_gated=false")
    print(f"[multiobject1b-check] SUMMARY passed={len(base)-len(failed)} failed={len(failed)}")
    if failed:
        print("[multiobject1b-check] FAIL " + ",".join(failed))
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__": main()
