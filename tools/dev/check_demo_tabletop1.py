"""Prospective source-contract checks for Demo-Tabletop-1."""
from __future__ import annotations
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = [
    ROOT / "tools/demo_tabletop1_public.py",
    ROOT / "tools/demo_tabletop1_repo.py",
    ROOT / "tools/demo_tabletop1_run.py",
]


def texts():
    return "\n".join(p.read_text() for p in FILES)


def checks(src: str):
    return {
        "oracle_explicit": '"oracle_assisted_demo": True' in src and '"truth_available_to_control": True' in src,
        "foreground_truth_not_fused": "reference_depth_inserted_into_metric_foreground\": False" in src and "may reject a stereo point but may not replace" in src,
        "background_separate": "BACKGROUND_SCAFFOLD" in src and "must never be counted as stereo-reconstructed foreground geometry" in src,
        "procedural_fixture": "tabletop_cloth" in src and ".blend test scene" not in src,
        "bounded_demo": "MAX_OBJECT_FIXATIONS" in src and "MAX_ORACLE_REDIRECTS" in src,
        "local_reused": "established frozen local FSG policy" in src,
        "transparent_nonclaims": '"autonomous_controller_tested": False' in src and '"discovery_tested": False' in src,
        "story_outputs": "demo.mp4" in src and "timeline/fix_<step>.png" in src,
        "baseline": "0e09f5b" in src and "demo-tabletop-1" in src,
    }

MUT = {
    "truthfill": ("reference_depth_inserted_into_metric_foreground\": False", "reference_depth_inserted_into_metric_foreground\": True"),
    "hideoracle": ("oracle_assisted_demo\": True", "oracle_assisted_demo\": False"),
    "nobackground": ("BACKGROUND_SCAFFOLD", "BACKGROUND_REMOVED"),
    "unbounded": ("MAX_ORACLE_REDIRECTS", "UNBOUNDED_REDIRECTS"),
    "autonomyclaim": ("autonomous_controller_tested\": False", "autonomous_controller_tested\": True"),
}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--mutation", choices=list(MUT)); a=ap.parse_args()
    src=texts()
    if a.mutation:
        old,new=MUT[a.mutation]
        if old not in src: raise SystemExit(2)
        src=src.replace(old,new)
    c=checks(src); failed=[k for k,v in c.items() if not v]
    print(f"[demo-tabletop1-contract] PASS oracle_explicit={str(c['oracle_explicit']).lower()} foreground_truth_not_fused={str(c['foreground_truth_not_fused']).lower()} background_separate={str(c['background_separate']).lower()}") if not failed else None
    print(f"[demo-tabletop1-bounds] PASS bounded_demo={str(c['bounded_demo']).lower()} local_reused={str(c['local_reused']).lower()} nonclaims={str(c['transparent_nonclaims']).lower()}") if not failed else None
    print(f"[demo-tabletop1-check] SUMMARY passed={len(c)-len(failed)} failed={len(failed)}")
    if failed: print("FAIL", ",".join(failed)); raise SystemExit(1)

if __name__=="__main__": main()
