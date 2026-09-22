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


def _segment_label(names: list[str]) -> str:
    """Longest underscore-segment prefix shared by an instance's piece names.

    The live target is one instance split across many analytic pieces named
    rc1_cloth_<row>_<col>; a raw character common prefix would keep a dangling
    digit ("rc1_cloth_0"). Splitting on "_" keeps whole segments only.
    """
    parts = [n.split("_") for n in names if n]
    if not parts:
        return ""
    shared: list[str] = []
    for seg in zip(*parts):
        if len(set(seg)) != 1:
            break
        shared.append(seg[0])
    return "_".join(shared) if shared else str(sorted(names)[0])


def _extract_rows(scene_objects: Any) -> list[dict[str, Any]]:
    """Return one sanitized row per positive instance id.

    DECLASSIFICATION BOUNDARY. The live evaluator representation is a list of
    analytic quads, each carrying vertices_h (4x3), instance_id, uv and name.
    Several quads may share one instance id (the target surface is a grid of
    them), so pieces are grouped by id and each object's centre is the mean of
    its pieces' own centres. For a single-quad object that mean reproduces the
    quad's declared centre exactly; for a multi-piece object it is an equal-
    weight mean over pieces rather than over shared vertices.

    The centre is converted to one seed direction using the project's
    established cyclopean convention (yaw = atan2(x, -z),
    pitch = atan2(y, hypot(x, z))). Only that direction, the id and the label
    leave this function: the vertices, extent, range and surface shape used to
    compute it stay here.
    """
    import numpy as np  # local: the observer process never reaches this module

    piece_centres: dict[int, list[Any]] = {}
    piece_names: dict[int, list[str]] = {}
    for piece in scene_objects:
        oid = int(piece["instance_id"])
        if oid <= 0:
            continue
        verts = np.asarray(piece["vertices_h"], dtype=float).reshape(-1, 3)
        if verts.shape[0] < 3 or not np.isfinite(verts).all():
            raise AssertionError(f"degenerate analytic piece for instance {oid}")
        piece_centres.setdefault(oid, []).append(verts.mean(axis=0))
        piece_names.setdefault(oid, []).append(str(piece.get("name", "")))

    rows: list[dict[str, Any]] = []
    for oid in sorted(piece_centres):
        centre = np.asarray(piece_centres[oid], dtype=float).mean(axis=0)
        if not np.isfinite(centre).all() or float(np.linalg.norm(centre)) <= 0.0:
            raise AssertionError(f"instance {oid} centre gives no usable seed direction")
        yaw = float(np.degrees(np.arctan2(centre[0], -centre[2])))
        pitch = float(np.degrees(np.arctan2(centre[1], np.hypot(centre[0], centre[2]))))
        rows.append({
            "object_id": int(oid),
            "seed_yaw_deg": yaw,
            "seed_pitch_deg": pitch,
            "label": _segment_label(piece_names[oid]),
        })
    return rows


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
