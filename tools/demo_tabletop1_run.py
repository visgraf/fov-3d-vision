"""Run the oracle-assisted Tabletop concept demonstration."""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any

import demo_tabletop1_public as public
from demo_tabletop1_repo import RepositoryAdapter


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
    out.mkdir(parents=True, exist_ok=True)
    if _git(repo, "branch", "--show-current") != public.RUN_BRANCH:
        raise RuntimeError(f"run on {public.RUN_BRANCH}")
    if _git(repo, "status", "--porcelain"):
        raise RuntimeError("Demo requires a clean tree before execution")
    if subprocess.call(["git", "merge-base", "--is-ancestor", public.BASELINE_COMMIT, "HEAD"], cwd=repo) != 0:
        raise RuntimeError("HEAD does not descend from the required REAL-1W baseline")

    adapter = RepositoryAdapter(repo, out, a.seed)
    started = time.time()
    guidance = dict(adapter.build_reference_and_guidance())
    _write(out / "oracle_guidance.json", guidance)

    objs = adapter.enumerate_objects(guidance)
    if len({o.object_id for o in objs}) != len(objs):
        raise AssertionError("duplicate object ids")
    if [o.object_id for o in objs] != sorted(o.object_id for o in objs):
        raise AssertionError("object order must be deterministic ascending id")

    rows: list[dict[str, Any]] = []
    all_fix: list[dict[str, Any]] = []
    step = 0

    for obj in objs:
        od = out / "objects" / f"object_{obj.object_id}"
        od.mkdir(parents=True, exist_ok=True)
        if obj.is_background:
            bg = dict(adapter.build_background_scaffold(obj, guidance, od))
            row = {"object_id": obj.object_id, "label": obj.label, "role": "BACKGROUND_SCAFFOLD", **bg}
            rows.append(row)
            _write(od / "object_complete.json", row)
            continue

        gaze = tuple(adapter.choose_oracle_seed_gaze(obj, guidance))
        action_source = "ORACLE_SEED"
        current_map: Path | None = None
        history: list[dict[str, Any]] = []
        redirects = 0
        stop_reason = "UNSET"

        while len(history) < public.MAX_OBJECT_FIXATIONS:
            meas = dict(adapter.acquire_and_validate(obj, gaze, step, od, guidance))
            meas["global_step"] = step
            meas["gaze_deg"] = [float(gaze[0]), float(gaze[1])]
            meas["action_source"] = action_source
            history.append(meas)
            all_fix.append(meas)
            step += 1

            fused = dict(adapter.initialize_or_fuse(obj, meas, od, current_map))
            # Per-fixation fusion ledger travels with the measurement record.
            meas["fused"] = bool(fused.get("fused", False))
            meas["fused_new"] = int(fused.get("new", 0))
            meas["fused_matched"] = int(fused.get("matched", 0))
            meas["map_points_after"] = fused.get("map_points")
            meas["empty_look"] = bool(fused.get("empty_look", False))
            meas["fusion_note"] = fused.get("reason")
            mp = fused.get("map_path")
            if mp:
                current_map = Path(mp)

            if current_map is None:
                rem = dict(adapter.oracle_uncovered_support(obj, guidance, current_map, history))
                ng = rem.get("next_gaze_deg")
                if ng is None or redirects >= public.MAX_ORACLE_REDIRECTS:
                    stop_reason = "NO_TRUSTWORTHY_SEED_AFTER_ORACLE_GUIDANCE"
                    break
                redirects += 1
                gaze = (float(ng[0]), float(ng[1]))
                action_source = "ORACLE_REDIRECT"
                continue

            local = dict(adapter.local_next_action(obj, od, history, current_map))
            ng = local.get("next_gaze_deg")
            if ng is not None and not bool(local.get("stop", False)):
                gaze = (float(ng[0]), float(ng[1]))
                action_source = "LOCAL_FSG"
                continue

            # Demo-mode rescue: local machinery has stopped/stalled, but Blender may
            # direct attention to still-uncovered target support. This is explicitly
            # oracle assistance and not presented as the learned/general controller.
            rem = dict(adapter.oracle_uncovered_support(obj, guidance, current_map, history))
            if bool(rem.get("demo_target_satisfied", False)):
                stop_reason = "DEMO_TARGET_SATISFIED"
                break
            ng = rem.get("next_gaze_deg")
            if ng is None or redirects >= public.MAX_ORACLE_REDIRECTS:
                stop_reason = "ORACLE_GUIDANCE_EXHAUSTED"
                break
            redirects += 1
            gaze = (float(ng[0]), float(ng[1]))
            action_source = "ORACLE_REDIRECT"
        else:
            stop_reason = "DEMO_OBJECT_GUARDRAIL"

        row = dict(adapter.finalize_foreground_object(obj, od, current_map, history, stop_reason))
        row.update({"object_id": obj.object_id, "label": obj.label, "role": "STEREO_FOREGROUND",
                    "fixations": len(history), "oracle_redirects": redirects, "stop_reason": stop_reason})
        rows.append(row)
        _write(od / "object_complete.json", row)

    _write(out / "fixation_history.json", all_fix)
    exports = dict(adapter.export_demo(rows, guidance, all_fix, out))
    manifest = {
        "schema": public.SPEC_ID,
        "public_spec_sha256": public.public_digest(),
        "oracle_assisted_demo": True,
        "truth_available_to_control": True,
        "discovery_tested": False,
        "autonomous_controller_tested": False,
        "fixture": public.FIXTURE,
        "seed": int(a.seed),
        "baseline_commit": public.BASELINE_COMMIT,
        "repo_head": _git(repo, "rev-parse", "HEAD"),
        "object_rows": rows,
        "fixation_count": len(all_fix),
        "fixation_history": "fixation_history.json",
        "action_source_counts": {
            k: sum(1 for f in all_fix if f.get("action_source") == k)
            for k in ("ORACLE_SEED", "LOCAL_FSG", "ORACLE_REDIRECT")
        },
        "renderer_precondition_refusals": sum(
            1 for f in all_fix if f.get("renderer_precondition_refused")),
        "empty_looks": sum(1 for f in all_fix if f.get("empty_look")),
        "raw_valid_stereo_total": sum(int(f.get("raw_valid_stereo_count", 0)) for f in all_fix),
        "accepted_total": sum(int(f.get("accepted_count", 0)) for f in all_fix),
        "oracle_rejected_total": sum(int(f.get("oracle_rejected_count", 0)) for f in all_fix),
        "exports": exports,
        "started_unix": started,
        "finished_unix": time.time(),
    }
    _write(out / "demo_manifest.json", manifest)
    adapter.write_report(manifest, out)
    print(f"DEMO_TABLETOP1_COMPLETE objects={len(rows)} fixations={len(all_fix)}")


if __name__ == "__main__":
    main()
