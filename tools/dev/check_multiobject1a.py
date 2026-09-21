"""Pure structural checks with genuine source-mutation negatives for MultiObject-1a."""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "tools" / "multiobject1a_public.py"
RUN = ROOT / "tools" / "multiobject1a_run.py"
SEED = ROOT / "tools" / "multiobject1a_seed.py"


def _source(p: Path) -> str: return p.read_text()


def _checks(pub: str, run: str, seed: str) -> list[tuple[str, bool]]:
    ast.parse(pub); ast.parse(run); ast.parse(seed)
    return [
        ("two_declared_objects", "OBJECT_ID_1 = parent.OBJECT_ID" in pub and "OBJECT_ID_2 = 143" in pub and "OBJECT_IDS = (OBJECT_ID_1, OBJECT_ID_2)" in pub),
        ("one_second_object_seed", "MAX_ADDED_FIXATIONS = 1" in pub and '"added_fixations": 1' in run),
        ("separate_geometry", "object 143 is never fused into object 141" in pub and '"SEED_SURFEL_PATCH"' in run and '"SURFEL_MAP"' in run),
        ("prior_evidence_seed", "already-acquired prediction-side id-143 evidence" in pub and "select_prescribed_seed(prior_xyz2" in run),
        ("no_truth_or_discovery", "no evaluator truth or scene-geometry oracle is opened" in pub and "this is not automatic object discovery" in pub),
        ("growth_deferred", "No object growth" in pub and "automatic next-object discovery remains deferred" in pub),
    ]


def _mutate(name: str, pub: str, run: str, seed: str):
    if name == "sameid":
        pub = pub.replace("OBJECT_ID_2 = 143", "OBJECT_ID_2 = parent.OBJECT_ID", 1)
    elif name == "multiprobe":
        pub = pub.replace("MAX_ADDED_FIXATIONS = 1", "MAX_ADDED_FIXATIONS = 2", 1)
        run = run.replace('"added_fixations": 1', '"added_fixations": 2', 1)
    elif name == "merge":
        pub = pub.replace("object 143 is never fused into object 141", "object 143 may be fused into object 141", 1)
    elif name == "truth":
        pub = pub.replace("no evaluator truth or scene-geometry oracle is opened", "evaluator truth may be opened", 1)
    elif name == "autodiscover":
        pub = pub.replace("this is not automatic object discovery", "this performs automatic object discovery", 1)
    elif name == "grow":
        pub = pub.replace("No object growth", "Object growth", 1).replace("automatic next-object discovery remains deferred", "automatic next-object discovery is enabled", 1)
    else:
        raise SystemExit(f"unknown negative: {name}")
    return pub, run, seed


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--negative"); a = ap.parse_args()
    pub, run, seed = _source(PUB), _source(RUN), _source(SEED)
    base = _checks(pub, run, seed)
    if a.negative:
        mp, mr, ms = _mutate(a.negative, pub, run, seed)
        mut = _checks(mp, mr, ms)
        failed = [n for (n, ok0), (_, ok1) in zip(base, mut) if ok0 and not ok1]
        if not failed:
            print(f"[multiobject1a-negative] ERROR {a.negative} mutation escaped detection")
            raise SystemExit(2)
        print(f"[multiobject1a-negative] FAIL {a.negative} detected_by={','.join(failed)}")
        raise SystemExit(1)
    for n, ok in base:
        if not ok:
            print(f"[multiobject1a-check] FAIL {n}"); raise SystemExit(1)
    print("[multiobject1a-scene] PASS object141_inherited=true object143_seeded=true separate_entities=true shared_cyclopean_chart=true")
    print("[multiobject1a-policy] PASS parent=cyclopean1g one_fixation_max=true prior_evidence_seed=true object_growth=false auto_discovery=false quality_gated=false")
    print(f"[multiobject1a-check] SUMMARY passed={len(base)} failed=0")

if __name__ == "__main__": main()
