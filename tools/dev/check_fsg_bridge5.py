"""Static checks for Bridge-5 controlled factorial package."""
from __future__ import annotations
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[2]
GEN = ROOT / "tools" / "fsg_bridge5_factorial.py"
ANA = ROOT / "tools" / "fsg_bridge5_analyze.py"
DOC = ROOT / "docs" / "fsg-blend-bridge-5.md"
CHK = ROOT / "docs" / "fsg-blend-bridge-5-checks.md"


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def main() -> None:
    passed = 0
    for p in (GEN, ANA, DOC, CHK):
        require(p.is_file(), f"missing {p}"); passed += 1
    ast.parse(GEN.read_text()); ast.parse(ANA.read_text()); passed += 2
    g = GEN.read_text(); a = ANA.read_text()
    require('FAR_BASE_DEPTH_M = 2.40' in g, "far depth must remain 2.40 m"); passed += 1
    require('"slanted": 1.8' in g and '"flat": 0.0' in g, "slant levels changed"); passed += 1
    require('"equal": 1.0' in g and '"near2x": 0.44' in g, "texture levels changed"); passed += 1
    require('TEXTURE_SEEDS = (2111, 2112, 2113)' in g, "texture seeds changed"); passed += 1
    require('CAPTURE_ALPHA_THRESHOLD = 0.5' in a, "capture definition changed"); passed += 1
    require('tools/fsg_stereo.py unchanged' in g, "frozen matcher contract missing"); passed += 1
    require('truth_in_observation' in g and 'evaluation_only' in g, "provenance contract missing"); passed += 1
    print(f"[fsg-bridge5-check] SUMMARY passed={passed} failed=0")


if __name__ == "__main__":
    main()
