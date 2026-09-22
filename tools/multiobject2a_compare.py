"""Structural comparator for completed MultiObject-2a next-object selections."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import multiobject2a_public as public


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("records", nargs="+")
    a = ap.parse_args()
    rows = []
    fails = []
    for p in map(Path, a.records):
        m = json.loads((p / "prediction_manifest.json").read_text())
        if m.get("schema") != public.SPEC_ID:
            fails.append(f"{p}: wrong schema")
            continue
        if m.get("public_spec_sha256") != public.public_digest():
            fails.append(f"{p}: public digest mismatch")
        if m.get("truth_opened") is not False or int(m.get("acquisitions_added", -1)) != 0:
            fails.append(f"{p}: selection acquired data or opened truth")
        if int(m.get("fusion_iterations_added", -1)) != 0 or int(m.get("growth_iterations_added", -1)) != 0:
            fails.append(f"{p}: selection fused/grew an object")
        if m.get("new_object_instantiated") is not False or not m.get("objects_141_143_read_only"):
            fails.append(f"{p}: object state changed during selection")
        selected = m.get("selected_object_id")
        if selected is not None and int(selected) in set(public.INSTANTIATED_OBJECT_IDS):
            fails.append(f"{p}: selected an already-instantiated object")
        report = json.loads((p / m["selection_report"]).read_text())
        cands = report.get("candidates", [])
        if cands:
            expected = sorted(cands, key=lambda r: (-int(r["valid_depth_samples"]), int(r["object_id"])))[0]
            if int(report.get("selected_object_id")) != int(expected["object_id"]):
                fails.append(f"{p}: selected object is not deterministic valid-depth argmax")
        elif report.get("selected_object_id") is not None:
            fails.append(f"{p}: selected object despite empty candidate set")
        rows.append({
            "seed": m.get("seed"),
            "observation_count": m.get("observation_count"),
            "candidate_object_ids": m.get("candidate_object_ids"),
            "selected_object_id": m.get("selected_object_id"),
            "selected_valid_depth_samples": m.get("selected_valid_depth_samples"),
            "next_stage": m.get("next_stage"),
        })
    status = "MULTIOBJECT2A_COMPLETE" if not fails else "MULTIOBJECT2A_INTEGRITY_FAIL"
    print("[multiobject2a-compare]", status, json.dumps({"records": rows, "structural_fails": fails}, sort_keys=True))
    raise SystemExit(0 if not fails else 2)


if __name__ == "__main__":
    main()
