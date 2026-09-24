"""Static/prospective checks for FSG Blend Bridge-3 fattening audit."""
from __future__ import annotations

import ast
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "fsg_bridge3_fattening.py"


def main() -> int:
    failures: list[str] = []
    if not TOOL.is_file():
        failures.append("missing tools/fsg_bridge3_fattening.py")
    else:
        text = TOOL.read_text()
        try:
            ast.parse(text)
        except SyntaxError as e:
            failures.append(f"syntax: {e}")
        required = [
            'SCHEMA = "FSG-BLEND-BRIDGE3-fattening-v1"',
            "CAPTURE_ALPHA_THRESHOLD = 0.5",
            "analysis_only",
            "stereo_rerun",
            "truth_used_only_after_stereo",
            "distance_profile",
            "true_disparity_gap_quartiles",
            "distance_x_gap_interaction",
            "bridge3_capture_map.png",
        ]
        for token in required:
            if token not in text:
                failures.append(f"missing contract token {token}")
        forbidden = [
            "StereoSGBM_create(",
            "fsg_blend_bridge.py --",
            "bpy.ops.render",
            "ORACLE_REDIRECT",
            "fsg6f",
        ]
        for token in forbidden:
            if token in text:
                failures.append(f"forbidden Bridge-3 scope token {token}")

    if not failures:
        p = subprocess.run([sys.executable, str(TOOL), "--self-test"], cwd=ROOT)
        if p.returncode != 0:
            failures.append("Bridge-3 self-test failed")

    if failures:
        for f in failures:
            print("[fsg-bridge3-check] FAIL", f)
        print(f"[fsg-bridge3-check] SUMMARY passed=0 failed={len(failures)}")
        return 1
    print("[fsg-bridge3-check] SUMMARY passed=7 failed=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
