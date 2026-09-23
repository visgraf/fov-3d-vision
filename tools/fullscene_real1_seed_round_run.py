"""Run one bounded 5-degree visibility-survey ring for failed REAL-1 seeds."""
from __future__ import annotations
import argparse, json, subprocess
from pathlib import Path
from typing import Any
import fullscene_real1_seed_round_public as public
from fullscene_real1_seed_round_repo import SeedRoundRepository

def _write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")

def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--baseline", type=Path, default=Path(public.BASELINE_OUT))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=public.SEED)
    a = ap.parse_args()
    repo = a.repo.resolve(); baseline = (repo / a.baseline).resolve() if not a.baseline.is_absolute() else a.baseline.resolve(); out = a.out.resolve()
    if _git(repo, "branch", "--show-current") != public.RUN_BRANCH:
        raise RuntimeError("wrong branch")
    if _git(repo, "status", "--porcelain"):
        raise RuntimeError("working tree must be clean")
    if subprocess.call(["git", "merge-base", "--is-ancestor", public.BASELINE_RESULT_COMMIT, "HEAD"], cwd=repo) != 0:
        raise RuntimeError("HEAD does not descend from REAL-1 result baseline")
    out.mkdir(parents=True, exist_ok=False)
    rr = SeedRoundRepository(repo, baseline, out, a.seed)
    base = rr.load_baseline()
    rows = [r for r in base["object_rows"] if r.get("status") == public.TARGET_BASELINE_STATUS]
    if not rows:
        raise RuntimeError("baseline contains no failed-centre seed target")
    next_step = int(max(base["fixation_steps"])) + 1
    all_targets = []
    for row in rows:
        oid = int(row["object_id"]); cy = float(row["seed_yaw_deg"]); cp = float(row["seed_pitch_deg"])
        obj_dir = out / f"object_{oid}"; obj_dir.mkdir(parents=True)
        probes = []
        for order, (dx, dy) in enumerate(public.RING_OFFSETS):
            gaze = (cy + dx * public.GRID_STEP_DEG, cp + dy * public.GRID_STEP_DEG)
            rec = rr.acquire_probe(row, gaze, next_step, obj_dir / f"probe_{order:02d}")
            rec.update({"ring_order": order, "gaze_deg": [gaze[0], gaze[1]], "global_step": next_step})
            probes.append(rec); next_step += 1
        # All probes are rendered before selection: no early stop/order bias.
        winner = max(probes, key=lambda p: (int(p.get("target_valid_depth_count", 0)), int(p.get("target_visible_pixels", 0)), -int(p["ring_order"])))
        recovered = None
        if int(winner.get("target_valid_depth_count", 0)) > 0:
            recovered = rr.materialize_seed_from_probe(row, winner, obj_dir)
        result = {
            "object_id": oid,
            "baseline_status": row.get("status"),
            "baseline_seed_gaze_deg": [cy, cp],
            "probe_count": len(probes),
            "probes": probes,
            "winner_ring_order": int(winner["ring_order"]),
            "winner_gaze_deg": winner["gaze_deg"],
            "winner_target_visible_pixels": int(winner.get("target_visible_pixels", 0)),
            "winner_target_valid_depth_count": int(winner.get("target_valid_depth_count", 0)),
            "recovered_seed": recovered,
            "recovery_status": "RECOVERED_SEED" if recovered else "ONE_RING_EXHAUSTED_NO_SEED",
        }
        all_targets.append(result)
    # The baseline is input, not workspace: re-hash every pinned artifact and
    # every per-object map and refuse any difference.
    baseline_proof = rr.verify_baseline_unchanged()
    manifest = {
        "schema": public.SPEC_ID,
        "public_spec_sha256": public.public_digest(),
        "baseline_result_commit": public.BASELINE_RESULT_COMMIT,
        "baseline_out": str(baseline),
        "baseline_seal_sha256": base["baseline_seal_sha256"],
        "baseline_read_only_verified": True,
        **baseline_proof,
        "one_round_complete": True,
        "rendered_probe_count": sum(x["probe_count"] for x in all_targets),
        "blender_launches": int(rr.blender_launches),
        "render_seconds": float(rr.render_seconds),
        "extra_seed_renders": 0,
        "ring_offsets": [list(o) for o in public.RING_OFFSETS],
        "lattice_step_deg": public.GRID_STEP_DEG,
        "probe_global_steps": [int(pp["global_step"]) for x in all_targets for pp in x["probes"]],
        "growth_actions": 0,
        "audit_actions": 0,
        "handoff_actions": 0,
        "truth_opened": False,
        "targets": all_targets,
    }
    # One render per probe and no ninth seed fixation, counted rather than asserted.
    if int(rr.blender_launches) != int(manifest["rendered_probe_count"]):
        raise AssertionError(
            f"render count {rr.blender_launches} != probe count {manifest['rendered_probe_count']}"
        )
    _write(out / "probe_ledger.json", all_targets)
    _write(out / "seed_recovery_report.json", manifest)
    _write(out / "seed_recovery_manifest.json", manifest)
    print("[real1-seed-round] COMPLETE " + json.dumps({"targets": len(all_targets), "probes": manifest["rendered_probe_count"]}))

if __name__ == "__main__": main()
