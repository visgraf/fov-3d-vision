"""Quarantined pre-control enumeration oracle for FullScene-REAL-1.

This is the ONLY new REAL-1 module allowed to inspect the evaluator-side
procedural scene specification before observer control. Its output is a strict
declassification boundary: each object record contains ONLY
  object_id, seed_yaw_deg, seed_pitch_deg, label
plus top-level fixture/provenance metadata.

Exact vertices/surfaces, depth, normals, range, coverage, extent and masks must
never be written to the sidecar.

Claude Code should bind _extract_rows() to the live analytic-quad structure.
No pre-REAL-1 source may be edited for this purpose.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ALLOWED_OBJECT_FIELDS = ["object_id", "seed_yaw_deg", "seed_pitch_deg", "label"]
SCHEMA = "FullSceneREAL1-enumeration-oracle-v1"


def _json_write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def _extract_rows(scene_objects: Any) -> list[dict[str, Any]]:
    """Return one sanitized row per positive instance id.

    LIVE-INTEGRATION SEAM. Inspect the analytic quads only inside this function,
    group by positive instance id, and derive one deterministic cyclopean seed
    direction from the object's center/bounds in the established camera frame.
    Return ONLY the four ALLOWED_OBJECT_FIELDS. Do not return geometry used to
    obtain the direction.
    """
    raise NotImplementedError("Bind REAL-1 enumeration oracle to live reality1_scene analytic quads")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--fixture", required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()

    tools = (a.repo.resolve() / "tools")
    sys.path.insert(0, str(tools))

    # Deliberately quarantined imports. Prediction/control modules must NOT do this.
    import reality1_public as reality_public  # type: ignore
    import reality1_scene as scene_spec  # type: ignore

    fixture = str(a.fixture)
    established = str(reality_public.FIXTURE)
    if fixture != established:
        raise RuntimeError(
            f"REAL-1 fixture must match established renderer fixture {established!r}; got {fixture!r}"
        )

    rows = _extract_rows(scene_spec.scene_objects(fixture))
    rows = sorted(rows, key=lambda r: int(r["object_id"]))
    if not rows:
        raise AssertionError("enumeration oracle produced no benchmark objects")
    seen: set[int] = set()
    for r in rows:
        if set(r) != set(ALLOWED_OBJECT_FIELDS):
            raise AssertionError(f"oracle row crosses whitelist: keys={sorted(r)}")
        oid = int(r["object_id"])
        if oid <= 0 or oid in seen:
            raise AssertionError(f"invalid/duplicate positive object id: {oid}")
        seen.add(oid)
        r["object_id"] = oid
        r["seed_yaw_deg"] = float(r["seed_yaw_deg"])
        r["seed_pitch_deg"] = float(r["seed_pitch_deg"])
        r["label"] = str(r["label"])

    digest_fn = getattr(scene_spec, "truth_digest", None)
    if not callable(digest_fn):
        raise RuntimeError("established evaluator scene spec exposes no truth_digest()")

    payload = {
        "schema": SCHEMA,
        "fixture": fixture,
        "fixture_truth_digest": str(digest_fn()),
        "fields_exposed": list(ALLOWED_OBJECT_FIELDS),
        "objects": rows,
    }
    _json_write(a.out.resolve(), payload)
    print(f"[fullscene-real1-oracle] fixture={fixture} objects={len(rows)} out={a.out.resolve()}")


if __name__ == "__main__":
    main()
