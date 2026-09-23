"""Run the oracle-attention Classroom concept demonstration."""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any

import demo_classroom1_public as public
from demo_classroom1_repo import DemoObject, RepositoryAdapter


def _write(path: Path, x: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(x, indent=2, sort_keys=True) + "\n")


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=public.SEED)
    a = ap.parse_args()

    repo = a.repo.resolve()
    out = a.out.resolve()
    if _git(repo, "branch", "--show-current") != public.RUN_BRANCH:
        raise RuntimeError(f"run on {public.RUN_BRANCH}")
    if _git(repo, "status", "--porcelain"):
        raise RuntimeError("Classroom demo requires a clean tree before execution")
    if subprocess.call(["git", "merge-base", "--is-ancestor", public.BASELINE_COMMIT, "HEAD"], cwd=repo) != 0:
        raise RuntimeError("HEAD does not descend from the completed Tabletop demo baseline")

    out.mkdir(parents=True, exist_ok=True)
    adapter = RepositoryAdapter(repo, out, a.seed)
    started = time.time()

    preflight = dict(adapter.preflight_scene())
    _write(out / "scene_preflight.json", preflight)
    if not bool(preflight.get("ready", False)):
        raise RuntimeError("Classroom preflight did not establish a safe live binding; stop and report")
    if preflight.get("scene_rel") != public.BLEND_REL:
        raise RuntimeError("preflight scene binding differs from public Classroom contract")

    guidance = dict(adapter.build_reference_and_guidance(preflight))
    _write(out / "oracle_guidance.json", guidance)
    plan = dict(adapter.build_scene_plan(guidance))
    _write(out / "scene_plan.json", plan)

    obj_rows = list(plan.get("foreground_objects", []))
    objs = [DemoObject(int(r["object_id"]), str(r["label"]), str(r.get("source_group", r["label"]))) for r in obj_rows]
    if not objs:
        raise RuntimeError("scene plan produced no foreground objects")
    if any(o.object_id <= 0 for o in objs):
        raise AssertionError("foreground ids must be positive")
    if len({o.object_id for o in objs}) != len(objs):
        raise AssertionError("duplicate foreground object ids")
    if [o.object_id for o in objs] != sorted(o.object_id for o in objs):
        raise AssertionError("foreground object order must be deterministic ascending id")

    background_plan = dict(plan.get("background", {}))
    if background_plan.get("object_key") != public.BACKGROUND_OBJECT_KEY:
        raise RuntimeError("scene plan must contain the single special background object")
    background_row = dict(adapter.build_background_scaffold(background_plan, guidance, out))
    background_row.update({"object_key": public.BACKGROUND_OBJECT_KEY, "role": "BACKGROUND_SCAFFOLD"})
    _write(out / "background_complete.json", background_row)

    rows: list[dict[str, Any]] = []
    all_fix: list[dict[str, Any]] = []
    step = 0
    global_guard_hit = False

    for obj in objs:
        if step >= public.MAX_TOTAL_FIXATIONS:
            global_guard_hit = True
            break

        od = out / "objects" / f"object_{obj.object_id}"
        od.mkdir(parents=True, exist_ok=True)
        gaze = tuple(adapter.choose_oracle_seed_gaze(obj, guidance))
        current_map: Path | None = None
        history: list[dict[str, Any]] = []
        stop_reason = "UNSET"

        while len(history) < public.MAX_OBJECT_FIXATIONS and step < public.MAX_TOTAL_FIXATIONS:
            action_source = "ORACLE_SEED" if not history else "ORACLE_UNCOVERED_SUPPORT"
            meas = dict(adapter.acquire_and_validate(obj, gaze, step, od, guidance))
            meas["global_step"] = step
            meas["object_id"] = obj.object_id
            meas["gaze_deg"] = [float(gaze[0]), float(gaze[1])]
            meas["action_source"] = action_source
            history.append(meas)
            all_fix.append(meas)
            step += 1

            fused = dict(adapter.initialize_or_fuse(obj, meas, od, current_map))
            mp = fused.get("map_path")
            if mp:
                current_map = Path(mp)
            # Keep fusion provenance in the same per-fixation ledger.
            for k, v in fused.items():
                if k != "map_path":
                    meas[f"fusion_{k}"] = v
            if mp:
                meas["map_path"] = str(mp)

            rem = dict(adapter.oracle_uncovered_support(obj, guidance, current_map, history))
            meas["oracle_after_fixation"] = rem
            if bool(rem.get("demo_target_satisfied", False)):
                stop_reason = "DEMO_TARGET_SATISFIED"
                break
            ng = rem.get("next_gaze_deg")
            if ng is None:
                stop_reason = "ORACLE_SUPPORT_EXHAUSTED"
                break
            gaze = (float(ng[0]), float(ng[1]))
        else:
            stop_reason = "DEMO_OBJECT_GUARDRAIL" if len(history) >= public.MAX_OBJECT_FIXATIONS else "DEMO_GLOBAL_GUARDRAIL"

        row = dict(adapter.finalize_foreground_object(obj, od, current_map, history, stop_reason))
        row.update({
            "object_id": obj.object_id,
            "label": obj.label,
            "source_group": obj.source_group,
            "role": "STEREO_FOREGROUND",
            "attention_mode": public.CONTROLLER_MODE,
            "fixations": len(history),
            "oracle_attention_fixations": len(history),
            "local_fsg_attention_actions": 0,
            "stop_reason": stop_reason,
        })
        rows.append(row)
        _write(od / "object_complete.json", row)

    if step >= public.MAX_TOTAL_FIXATIONS and len(rows) < len(objs):
        global_guard_hit = True

    _write(out / "fixation_history.json", all_fix)
    exports = dict(adapter.export_demo(rows, background_row, guidance, all_fix, out))
    manifest = {
        "schema": public.SPEC_ID,
        "public_spec_sha256": public.public_digest(),
        "oracle_assisted_demo": True,
        "truth_available_to_control": True,
        "controller_mode": public.CONTROLLER_MODE,
        "oracle_attention_for_all_fixations": True,
        "local_fsg_attention_actions": 0,
        "discovery_tested": False,
        "autonomous_controller_tested": False,
        "fsg6f_generalization_tested": False,
        "autonomous_background_decomposition_tested": False,
        "foreground_reference_depth_fused": False,
        "scene_id": public.SCENE_ID,
        "scene_rel": public.BLEND_REL,
        "scene_sha256": preflight.get("scene_sha256"),
        "seed": int(a.seed),
        "profile": public.PROFILE,
        "baseline_commit": public.BASELINE_COMMIT,
        "repo_head": _git(repo, "rev-parse", "HEAD"),
        "decomposition": plan.get("decomposition"),
        "foreground_object_rows": rows,
        "foreground_objects_planned": len(objs),
        "foreground_objects_processed": len(rows),
        "background_row": background_row,
        "fixation_count": len(all_fix),
        "oracle_attention_fixation_count": len(all_fix),
        "global_guard_hit": global_guard_hit,
        "exports": exports,
        "started_unix": started,
        "finished_unix": time.time(),
    }
    _write(out / "demo_manifest.json", manifest)
    adapter.write_report(manifest, out)
    print(
        f"DEMO_CLASSROOM1_COMPLETE foreground={len(rows)}/{len(objs)} "
        f"fixations={len(all_fix)} attention=oracle global_guard={global_guard_hit}"
    )


if __name__ == "__main__":
    main()
