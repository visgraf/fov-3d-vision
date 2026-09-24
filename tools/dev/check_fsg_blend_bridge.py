"""Static contract check for FSG Blend Bridge 1.

This intentionally checks architectural boundaries rather than Blender behavior.
Real camera/raycast behavior is checked on the workstation by the bridge run.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys


REQUIRED = {
    "make_calibration": "make_calibration(",
    "perspective_camera": 'data.type = "PERSP"',
    "fsg_observation": '{"rgb_L", "rgb_R", "instance_L", "instance_R"}',
    "truth_separate": 'eval_dir / f"truth_{eye[\'name\']}.npz"',
    "no_truth_flag": '"truth_in_observation": False',
    "no_warp_flag": '"foveated_warp_used": False',
    "no_field_flag": '"stereo_field_used": False',
    "parent_root": '"rule": "topmost parent root over renderable mesh objects; sorted root names; ids 1..N"',
    "nonzero_fail": "os._exit(1)",
}
FORBIDDEN = {
    "warp_import": "import warp",
    "stereo_field_import": "import stereo_field",
    "truth_in_observation_key": 'obs["depth',
    "reference_xyz_in_observation": 'obs["xyz',
}


def check_text(text: str) -> list[str]:
    fails = []
    for name, token in REQUIRED.items():
        if token not in text:
            fails.append("missing " + name)
    for name, token in FORBIDDEN.items():
        if token in text:
            fails.append("forbidden " + name)
    if "fsg_stereo" in text and "host tools/fsg_stereo.py unchanged" not in text:
        fails.append("bridge should not import or embed the stereo estimator")
    return fails


def mutate(text: str, which: str) -> str:
    if which == "warp":
        return text + "\nimport warp\n"
    if which == "truthfill":
        return text + '\nobs["depth_L"] = np.zeros((1,1))\n'
    if which == "nonperspective":
        return text.replace('data.type = "PERSP"', 'data.type = "PANO"', 1)
    if which == "nostereo_contract":
        return text.replace('"stereo_field_used": False', '"stereo_field_used": True', 1)
    if which == "nogrouping":
        return text.replace("topmost parent root over renderable mesh objects; sorted root names; ids 1..N", "object names", 1)
    raise ValueError("unknown negative")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--negative", choices=("warp", "truthfill", "nonperspective", "nostereo_contract", "nogrouping"))
    ap.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1] / "fsg_blend_bridge.py")
    args = ap.parse_args()
    text = args.source.read_text()
    if args.negative:
        text = mutate(text, args.negative)
    fails = check_text(text)
    for f in fails:
        print("[fsg-blend-bridge-check] FAIL", f)
    passed = len(REQUIRED) + len(FORBIDDEN) - len(fails)
    print(f"[fsg-blend-bridge-check] SUMMARY passed={passed} failed={len(fails)}")
    raise SystemExit(1 if fails else 0)


if __name__ == "__main__":
    main()
