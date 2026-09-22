"""FullScene-REAL-1 end-to-end benchmark orchestrator.

The established benchmark scene is procedural. REAL-1 binds to its fixture
name and to a sanitized pre-control enumeration sidecar; it never pretends an
unrelated .blend file is the input scene.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import fullscene_real1_public as public
from fullscene_real1_repo_adapter import RepositoryAdapter


def _json_write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def _status_from_audit(object_record: dict[str, Any], audit: dict[str, Any]) -> str:
    for key in ("object_status", "status", "stop_interpretation"):
        v = audit.get(key)
        if isinstance(v, str) and v:
            return v
    if object_record.get("seed_usable") is False:
        return "SEED_MEASUREMENT_FAILED"
    if object_record.get("termination_reason") == "watchdog":
        return "WATCHDOG_REACHED_RETAIN_FOR_REVISIT"
    return "LOCAL_GROWTH_STOPPED_OTHER"


def _record_checkpoint(path: Path, record: dict[str, Any]) -> None:
    record["checkpoint_schema"] = public.SPEC_ID
    record["public_spec_sha256"] = public.public_digest()
    _json_write(path, record)


def _load_checkpoint(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    rec = json.loads(path.read_text())
    if rec.get("checkpoint_schema") != public.SPEC_ID:
        raise AssertionError(f"wrong checkpoint schema: {path}")
    if rec.get("public_spec_sha256") != public.public_digest():
        raise AssertionError(f"checkpoint public digest mismatch: {path}")
    return rec


def _observer_seal(out: Path, payload: dict[str, Any]) -> Path:
    seal = out / "observer_complete.json"
    if seal.exists():
        raise RuntimeError("observer_complete already exists; refuse to overwrite sealed observer state")
    _json_write(seal, payload)
    return seal


def _validate_scaffold(scaffold: dict[str, Any], fixture: str) -> None:
    required_top = {"schema", "fixture", "fixture_truth_digest", "fields_exposed", "objects"}
    if set(scaffold) != required_top:
        raise AssertionError(f"enumeration oracle top-level keys crossed contract: {sorted(scaffold)}")
    if scaffold["fixture"] != fixture:
        raise AssertionError("enumeration oracle fixture mismatch")
    if set(scaffold["fields_exposed"]) != set(public.ENUMERATION_OBJECT_FIELDS):
        raise AssertionError("enumeration oracle exposed-field contract mismatch")
    if not isinstance(scaffold["fixture_truth_digest"], str) or not scaffold["fixture_truth_digest"]:
        raise AssertionError("enumeration oracle missing fixture truth digest")
    ids: list[int] = []
    for row in scaffold["objects"]:
        if set(row) != set(public.ENUMERATION_OBJECT_FIELDS):
            raise AssertionError(f"enumeration oracle object row crossed whitelist: {sorted(row)}")
        ids.append(int(row["object_id"]))
    if not ids or any(x <= 0 for x in ids) or len(ids) != len(set(ids)) or ids != sorted(ids):
        raise AssertionError(f"invalid deterministic positive object id list: {ids}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--fixture", default=public.DEFAULT_FIXTURE,
                    help="Established procedural renderer fixture name")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=public.SEED)
    ap.add_argument("--resume", action="store_true", help="Resume completed-object checkpoints")
    ap.add_argument("--no-handoff", action="store_true", help="Disable the one established bounded handoff")
    a = ap.parse_args()

    repo = a.repo.resolve()
    fixture = str(a.fixture)
    out = a.out.resolve()

    branch = _git(repo, "branch", "--show-current")
    if branch != public.RUN_BRANCH:
        raise RuntimeError(f"REAL-1 must run on {public.RUN_BRANCH!r}, got {branch!r}")
    if _git(repo, "status", "--porcelain"):
        raise RuntimeError("REAL-1 requires a clean working tree before execution")
    if subprocess.call(["git", "merge-base", "--is-ancestor", public.BASELINE_PARENT_COMMIT, "HEAD"], cwd=repo) != 0:
        raise RuntimeError(f"HEAD does not descend from required baseline {public.BASELINE_PARENT_COMMIT}")

    out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    adapter = RepositoryAdapter(repo, fixture, out, a.seed)

    # Pre-control oracle declassification boundary: a separate truth-side helper
    # may inspect the procedural spec, but ONLY the sanitized sidecar is consumed here.
    scaffold = dict(adapter.enumeration_scaffold())
    _validate_scaffold(scaffold, fixture)
    canonical_sidecar = out / "enumeration_oracle.json"
    _json_write(canonical_sidecar, scaffold)
    sidecar_hash = _sha256(canonical_sidecar)
    objects = adapter.objects_from_scaffold(scaffold)
    ids = [int(o.object_id) for o in objects]

    run_header = {
        "schema": public.SPEC_ID,
        "public_spec_sha256": public.public_digest(),
        "seed": int(a.seed),
        "fixture": fixture,
        "fixture_kind": "procedural",
        "fixture_truth_digest": scaffold["fixture_truth_digest"],
        "enumeration_oracle_sha256": sidecar_hash,
        "enumeration_oracle_fields": list(public.ENUMERATION_OBJECT_FIELDS),
        "repo_head_at_start": _git(repo, "rev-parse", "HEAD"),
        "branch": branch,
        "baseline_parent_commit": public.BASELINE_PARENT_COMMIT,
        "fixed_head": True,
        "static_scene": True,
        "discovery_tested": False,
        "instance_oracle_used_for_enumeration": True,
        "seed_direction_oracle_used": True,
        "evaluator_geometry_truth_available_to_control": False,
        "object_order": ids,
        "handoff_enabled": not a.no_handoff,
        "started_unix": started,
        "python": sys.version,
        "platform": platform.platform(),
    }
    _json_write(out / "run_header.json", run_header)

    object_rows: list[dict[str, Any]] = []
    fixation_history: list[dict[str, Any]] = []
    global_step = 0

    for ordinal, obj in enumerate(objects):
        od = out / "objects" / f"object_{obj.object_id}"
        od.mkdir(parents=True, exist_ok=True)
        checkpoint = od / "object_complete.json"
        previous = _load_checkpoint(checkpoint) if a.resume else None
        if previous is not None:
            object_rows.append(previous["scene_row"])
            fixation_history.extend(previous.get("fixation_records", []))
            global_step = max(global_step, int(previous.get("next_global_step", global_step)))
            continue

        seed_rec = dict(adapter.seed_object(obj, global_step, od))
        seed_rec.setdefault("object_id", int(obj.object_id))
        seed_fix = list(seed_rec.get("fixation_records", []))
        fixation_history.extend(seed_fix)
        global_step = int(seed_rec.get("next_global_step", global_step + max(1, len(seed_fix))))

        object_record: dict[str, Any] = {
            "object_id": int(obj.object_id),
            "ordinal": ordinal,
            "seed": seed_rec,
            "seed_usable": bool(seed_rec.get("seed_usable", seed_rec.get("valid_target_points", 0) > 0)),
        }

        if object_record["seed_usable"]:
            grow = dict(adapter.grow_object(obj, seed_rec, global_step, od))
            object_record["growth"] = grow
            object_record["termination_reason"] = grow.get("termination_reason")
            grows = list(grow.get("fixation_records", []))
            fixation_history.extend(grows)
            global_step = int(grow.get("next_global_step", global_step + len(grows)))
        else:
            object_record["growth"] = None
            object_record["termination_reason"] = "seed_measurement_failed"

        audit = dict(adapter.audit_object(obj, object_record, od))
        object_record["audit"] = audit

        handoff = None
        exterior = audit.get("exterior_refined_cells_by_state", {}) or {}
        should_handoff = (
            not a.no_handoff
            and object_record.get("termination_reason") == "no_frontier"
            and int(exterior.get("NEVER_OBSERVED", 0)) > 0
        )
        if should_handoff:
            handoff = adapter.maybe_one_handoff(obj, object_record, audit, global_step, od)
            if handoff is not None:
                handoff = dict(handoff)
                hfix = list(handoff.get("fixation_records", []))
                fixation_history.extend(hfix)
                global_step = int(handoff.get("next_global_step", global_step + len(hfix)))
                object_record["handoff"] = handoff
                audit = dict(adapter.audit_object(obj, object_record, od))
                object_record["audit_after_handoff"] = audit
        object_record["handoff"] = handoff

        row = dict(adapter.finalize_object(obj, object_record, audit, handoff, od))
        row.setdefault("object_id", int(obj.object_id))
        row.setdefault("status", _status_from_audit(object_record, audit))
        object_record["scene_row"] = row
        object_record["fixation_records"] = (
            seed_fix
            + list((object_record.get("growth") or {}).get("fixation_records", []))
            + list((handoff or {}).get("fixation_records", []))
        )
        object_record["next_global_step"] = global_step
        _record_checkpoint(checkpoint, object_record)
        object_rows.append(row)

    # Observer products are sealed before full evaluator truth is rendered/opened.
    observer_exports = dict(adapter.export_observer_scene(object_rows, out))
    _json_write(out / "fixation_history.json", fixation_history)
    _json_write(out / "object_status_table.json", object_rows)
    seal_payload = {
        "schema": public.SPEC_ID,
        "public_spec_sha256": public.public_digest(),
        "observer_sealed": True,
        "fixture": fixture,
        "fixture_truth_digest": scaffold["fixture_truth_digest"],
        "enumeration_oracle_sha256": sidecar_hash,
        "object_ids": ids,
        "attempted_object_count": len(ids),
        "object_rows": object_rows,
        "fixation_count": len(fixation_history),
        "observer_exports": observer_exports,
        "evaluator_truth_opened": False,
        "sealed_unix": time.time(),
    }
    seal_path = _observer_seal(out, seal_payload)
    seal_hash = _sha256(seal_path)

    # Full evaluation oracle phase starts here and only here.
    reference_exports = dict(adapter.render_reference_after_control(out))
    evaluation = dict(adapter.evaluate_against_reference(object_rows, observer_exports, reference_exports, out))

    manifest = {
        **run_header,
        "observer_complete_sha256": seal_hash,
        "observer_sealed_before_truth": True,
        "evaluator_truth_opened": True,
        "object_ids": ids,
        "attempted_object_count": len(ids),
        "instantiated_object_ids": [int(r["object_id"]) for r in object_rows if bool(r.get("instantiated", False))],
        "object_statuses": {str(r["object_id"]): r.get("status") for r in object_rows},
        "fixation_count": len(fixation_history),
        "observer_exports": observer_exports,
        "reference_exports": reference_exports,
        "evaluation_summary": evaluation,
        "finished_unix": time.time(),
        "wall_seconds": time.time() - started,
        "structural_fails": [],
    }
    _json_write(out / "scene_manifest.json", manifest)
    _json_write(out / "scene_report.json", evaluation)

    lines = [
        "# FullScene-REAL-1 scene report",
        "",
        f"- Procedural fixture: `{fixture}`",
        f"- Fixture truth digest: `{scaffold['fixture_truth_digest']}`",
        f"- Objects enumerated/attempted: **{len(ids)}** — {ids}",
        f"- Total fixations: **{len(fixation_history)}**",
        f"- Observer sealed before evaluator truth: **yes** (`{seal_hash[:16]}...`)",
        f"- Wall time: **{manifest['wall_seconds']:.1f} s**",
        "",
        "## Object statuses",
        "",
        "| id | instantiated | status | fixations | surfels |",
        "|---:|:---:|---|---:|---:|",
    ]
    for r in object_rows:
        lines.append(
            f"| {r.get('object_id')} | {'yes' if r.get('instantiated') else 'no'} | {r.get('status','')} | "
            f"{r.get('fixation_count','')} | {r.get('surfel_count','')} |"
        )
    lines += ["", "## Evaluation summary", "", "```json", json.dumps(evaluation, indent=2, sort_keys=True), "```", ""]
    (out / "scene_report.md").write_text("\n".join(lines))

    print("[fullscene-real1] COMPLETE " + json.dumps({
        "fixture": fixture,
        "objects": ids,
        "attempted": len(ids),
        "instantiated": manifest["instantiated_object_ids"],
        "fixations": len(fixation_history),
        "wall_seconds": round(manifest["wall_seconds"], 3),
        "out": str(out),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
