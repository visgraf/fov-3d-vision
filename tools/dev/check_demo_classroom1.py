"""Prospective source-contract checks for Demo-Classroom-1."""
from __future__ import annotations
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = [
    ROOT / "tools/demo_classroom1_public.py",
    ROOT / "tools/demo_classroom1_repo.py",
    ROOT / "tools/demo_classroom1_run.py",
]


def texts() -> str:
    return "\n".join(p.read_text() for p in FILES)


def checks(src: str) -> dict[str, bool]:
    return {
        "oracle_explicit": '"oracle_assisted_demo": True' in src and '"truth_available_to_control": True' in src,
        "foreground_truth_not_fused": 'reference_depth_inserted_into_metric_foreground": False' in src and "may reject a stereo point but may not replace" in src,
        "classroom_blend": "scenes/classroom/classroom_eye.blend" in src and 'SCENE_ID = "classroom"' in src,
        "preflight": "preflight_scene" in src and "scene_preflight.json" in src and 'preflight.get("ready", False)' in src,
        "adaptive_background": "BACKGROUND_NEAR_QUANTILE" in src and "BACKGROUND_FAR_QUANTILE" in src and "scene-adaptive soft background" in src,
        "single_background": 'BACKGROUND_OBJECT_KEY = "__BACKGROUND__"' in src and "ONE special background" in src,
        "bounded_demo": "MAX_OBJECT_FIXATIONS" in src and "MAX_ORACLE_REDIRECTS" in src and "MAX_TOTAL_FIXATIONS" in src,
        "local_reused": "established local FSG controller" in src and "established Classroom pair renderer/rig and stereo front end" in src,
        "transparent_nonclaims": '"autonomous_controller_tested": False' in src and '"discovery_tested": False' in src and '"autonomous_background_decomposition_tested": False' in src,
        "baseline": 'BASELINE_COMMIT = "cafad30"' in src and 'RUN_BRANCH = "demo-classroom-1"' in src,
        "story_outputs": "demo.mp4" in src and "timeline/fix_<step>.png" in src,
    }


MUT = {
    "truthfill": ('reference_depth_inserted_into_metric_foreground": False', 'reference_depth_inserted_into_metric_foreground": True'),
    "wrongscene": ("scenes/classroom/classroom_eye.blend", "scenes/classroom/classroom.blend"),
    "nopreflight": ("preflight_scene", "skip_preflight"),
    "noadaptivebg": ("BACKGROUND_NEAR_QUANTILE", "FIXED_BACKGROUND_DEPTH"),
    "nobackground": ('BACKGROUND_OBJECT_KEY = "__BACKGROUND__"', 'BACKGROUND_OBJECT_KEY = ""'),
    "unbounded": ("MAX_TOTAL_FIXATIONS", "UNBOUNDED_TOTAL_FIXATIONS"),
    "autonomyclaim": ('"autonomous_controller_tested": False', '"autonomous_controller_tested": True'),
    "oldbaseline": ('BASELINE_COMMIT = "cafad30"', 'BASELINE_COMMIT = "0e09f5b"'),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mutation", choices=list(MUT))
    a = ap.parse_args()
    src = texts()
    if a.mutation:
        old, new = MUT[a.mutation]
        if old not in src:
            raise SystemExit(2)
        src = src.replace(old, new)
    c = checks(src)
    failed = [k for k, v in c.items() if not v]
    if not failed:
        print(f"[demo-classroom1-contract] PASS oracle_explicit={str(c['oracle_explicit']).lower()} foreground_truth_not_fused={str(c['foreground_truth_not_fused']).lower()} classroom_blend={str(c['classroom_blend']).lower()}")
        print(f"[demo-classroom1-scene] PASS preflight={str(c['preflight']).lower()} adaptive_background={str(c['adaptive_background']).lower()} single_background={str(c['single_background']).lower()}")
        print(f"[demo-classroom1-bounds] PASS bounded_demo={str(c['bounded_demo']).lower()} local_reused={str(c['local_reused']).lower()} nonclaims={str(c['transparent_nonclaims']).lower()}")
    print(f"[demo-classroom1-check] SUMMARY passed={len(c)-len(failed)} failed={len(failed)}")
    if failed:
        print("FAIL", ",".join(failed))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
