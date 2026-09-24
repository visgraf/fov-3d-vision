"""Structural comparator for Classroom-FSG-1 outputs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import classroom_fsg1_public as public


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("out", type=Path)
    ap.add_argument("--allow-partial", action="store_true")
    a = ap.parse_args()
    out = a.out
    m = json.loads((out / "classroom_fsg1_manifest.json").read_text())
    r = json.loads((out / "classroom_fsg1_report.json").read_text())
    fails: list[str] = []
    if m.get("schema") != public.SPEC_ID: fails.append("schema")
    if m.get("attention_policy_reexecuted") is not False: fails.append("attention_policy")
    if m.get("gazes_reselected") is not False: fails.append("gaze_reselection")
    if m.get("foreground_background_decomposition_used") is not False: fails.append("fgbg")
    if m.get("background_panorama_used") is not False: fails.append("background_panorama")
    if m.get("native_stream_truth_free_inference") is not True: fails.append("native_truth")
    if m.get("guarded_stream_truth_rejection_only") is not True: fails.append("guard_truth")
    if m.get("truth_geometry_inserted") is not False: fails.append("truth_fill")
    if m.get("matcher_tuned") is not False: fails.append("matcher_tuned")
    if r.get("guarded_is_subset_only") is not True: fails.append("subset")
    if r.get("truth_inserted_or_substituted_geometry") is not False: fails.append("truth_geometry")
    if int(r.get("guarded_measurement_points", 0)) > int(r.get("native_measurement_points", -1)):
        fails.append("guard_count")
    if not a.allow_partial and int(m.get("fixations_replayed", -1)) != public.EXPECTED_FIXATIONS:
        fails.append("fixation_count")
    for name in ("native_scene_points.npz", "native_scene_points.ply", "guarded_scene_points.npz",
                 "guarded_scene_points.ply", "replayed_fixations.json", "instance_groups.json"):
        if not (out / name).is_file(): fails.append("missing:" + name)
    print(f"CLASSROOM_FSG1_COMPARE full={m.get('full_run')} structural_fails={fails}")
    raise SystemExit(1 if fails else 0)


if __name__ == "__main__":
    main()
