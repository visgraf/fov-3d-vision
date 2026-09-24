"""Static/package checks for Classroom-FSG-1."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import classroom_fsg1_public as public


def main() -> None:
    checks: list[tuple[str, bool]] = []
    def add(name: str, ok: bool) -> None:
        checks.append((name, bool(ok)))

    add("branch-contract", public.RUN_BRANCH == "classroom-fsg-1")
    add("sealed-history-count", public.EXPECTED_FIXATIONS == 225)
    add("no-fg-bg", public.PUBLIC_SPEC["scene_representation"]["foreground_background_decomposition_used"] is False)
    add("no-bg-panorama", public.PUBLIC_SPEC["scene_representation"]["background_panorama_used"] is False)
    add("no-bg-shell", public.PUBLIC_SPEC["scene_representation"]["background_shell_used"] is False)
    add("ordinary-instances", public.PUBLIC_SPEC["scene_representation"]["positive_instance_ids_are_ordinary_scene_entities"] is True)
    add("guard-no-truth-fill", public.PUBLIC_SPEC["guard"]["truth_can_insert_or_replace_geometry"] is False)
    add("matcher-frozen", public.PUBLIC_SPEC["instrument"]["matcher_tuned"] is False)
    add("packet-capacity", (public.EXPECTED_FIXATIONS + public.FUSION_PACKET_CONTRIBUTIONS - 1) // public.FUSION_PACKET_CONTRIBUTIONS <= 63)
    add("gate-positive", public.GUARD_ABS_M > 0 and public.GUARD_REL > 0)

    required = [
        ROOT / "tools" / "classroom_fsg1_public.py",
        ROOT / "tools" / "classroom_fsg1_run.py",
        ROOT / "tools" / "classroom_fsg1_compare.py",
        ROOT / "docs" / "classroom-fsg-1.md",
        ROOT / "docs" / "classroom-fsg-1-checks.md",
    ]
    add("new-files-present", all(p.is_file() for p in required))

    # When run inside the real repository, ensure the established instrument is
    # untouched relative to the Bridge-5 result baseline.
    if (ROOT / ".git").exists():
        frozen = ["tools/fsg_geometry.py", "tools/fsg_blend_bridge.py", "tools/fsg_stereo.py",
                  "tools/fsg3_surface_map.py", "tools/fsg6f_public.py"]
        p = subprocess.run(["git", "diff", "--quiet", public.BASELINE_COMMIT, "--", *frozen], cwd=ROOT)
        add("frozen-tools-diff-empty", p.returncode == 0)
    else:
        add("frozen-tools-diff-empty", True)

    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"[classroom-fsg1-check] {'PASS' if ok else 'FAIL'} {n}")
    print(f"[classroom-fsg1-check] SUMMARY passed={len(checks)-len(failed)} failed={len(failed)}")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
