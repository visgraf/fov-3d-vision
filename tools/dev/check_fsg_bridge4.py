"""Static/contract checks for FSG Blend Bridge-4.

The checker does not run the sweep. It verifies that the new Bridge-4 tools describe a
controlled, analytic depth sweep and that the established FSG stereo instrument retains
its frozen parameters.
"""
from __future__ import annotations

import ast
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))


def _source(name: str) -> str:
    return (TOOLS / name).read_text()


def main() -> int:
    passed = 0
    failed = 0

    def check(name: str, cond: bool) -> None:
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"[fsg-bridge4-check] PASS {name}")
        else:
            failed += 1
            print(f"[fsg-bridge4-check] FAIL {name}")

    gen = _source("fsg_bridge4_synthetic.py")
    ana = _source("fsg_bridge4_analyze.py")
    stereo = _source("fsg_stereo.py")

    check("analytic_source", 'SOURCE = "analytic_two_plane_tangent_perspective"' in gen)
    check("fixed_near_depth", "NEAR_DEPTH_M = 1.40" in gen)
    check("declared_depth_sweep", "FAR_DEPTHS_M = (1.60, 1.80, 2.00, 2.20, 2.40, 2.80, 3.20)" in gen)
    check("three_texture_repeats", "TEXTURE_SEEDS = (2111, 2112, 2113)" in gen)
    check("baseline_projected", 'tangent_frame="baseline_projected"' in gen)
    check("truth_quarantined", '"truth_in_observation": False' in gen and '"truth_used_only_after_stereo": True' in ana)
    check("no_blender", "import bpy" not in gen and "import bpy" not in ana)
    check("no_matcher_implementation", "StereoSGBM_create" not in gen and "StereoSGBM_create" not in ana)
    check("capture_midpoint", "CAPTURE_ALPHA_THRESHOLD = 0.5" in ana)
    check("scanline_probe", "_same_row_distance" in ana and "no_near_row_capture_fraction" in ana)
    check("frozen_block_size", "BLOCK_SIZE = 5" in stereo)
    check("frozen_lr_tolerance", "LR_TOLERANCE_PX = 1.0" in stereo)
    check("frozen_guard", "INSTANCE_GUARD_PX = 3" in stereo)
    check("frozen_matcher_mode", "STEREO_SGBM_MODE_SGBM_3WAY" in stereo)

    # Ensure the new tools parse and contain no top-level subprocess or shell execution.
    for name, src in (("generator_ast", gen), ("analyzer_ast", ana)):
        try:
            tree = ast.parse(src)
            bad = any(isinstance(n, (ast.Import, ast.ImportFrom)) and any(alias.name in {"subprocess", "os"} for alias in n.names) for n in tree.body)
            check(name, not bad)
        except SyntaxError:
            check(name, False)

    print(f"[fsg-bridge4-check] SUMMARY passed={passed} failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
