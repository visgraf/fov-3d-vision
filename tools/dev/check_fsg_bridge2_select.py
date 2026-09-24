"""Static/smoke checks for the Bridge-2 pre-stereo selector."""
from __future__ import annotations
import ast
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "tools" / "fsg_bridge2_select.py"


def main() -> int:
    fails = []
    text = SRC.read_text()
    tree = ast.parse(text)
    imports = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imports |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            imports.add(n.module)
    if "subprocess" in imports:
        fails.append("selector must not execute stereo or acquisition")
    if any(name == "fsg_stereo" or name.startswith("fsg_stereo.") or name == "stereo_field" or name.startswith("stereo_field.") for name in imports):
        fails.append("selector must not import a stereo matcher")
    analyze = ROOT / "tools" / "fsg_bridge2_analyze.py"
    if not analyze.is_file():
        fails.append("missing evaluator-only Bridge-2 analysis module")
    required = [
        "selection_is_pre_stereo",
        "MIN_SECOND_INSTANCE_FRACTION = 0.10",
        "MIN_RANGE_SPAN_M = 0.40",
        "MIN_BOUNDARY_JUMP_MEDIAN_M = 0.20",
        "MIN_GRAY_STD_U8 = 8.0",
        'if (run / "stereo").exists()',
        'tangent_frame_mode") != "baseline_projected"',
    ]
    for s in required:
        if s not in text:
            fails.append("missing contract token: " + s)
    rc = subprocess.call([sys.executable, str(SRC), "--self-test"], cwd=ROOT)
    if rc != 0:
        fails.append("selector self-test failed")
    for f in fails:
        print("[fsg-bridge2-check] FAIL", f)
    print(f"[fsg-bridge2-check] SUMMARY passed={8-len(fails)} failed={len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
