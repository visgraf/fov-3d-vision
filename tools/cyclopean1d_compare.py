"""Aggregate completed Cyclopean-1d read-only audit records."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import cyclopean1d_public as public


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("records", nargs="+")
    a = ap.parse_args()
    rows = []
    structural = []
    for item in a.records:
        p = Path(item)
        m = json.loads((p / "prediction_manifest.json").read_text())
        if m.get("schema") != "Cyclopean1d-observation-measurement-audit-v1":
            structural.append(f"{p}: wrong schema")
            continue
        if m.get("public_spec_sha256") != public.public_digest():
            structural.append(f"{p}: public digest mismatch")
        if m.get("truth_opened") is not False or int(m.get("acquisitions_added", -1)) != 0 or m.get("parent_files_modified") is not False:
            structural.append(f"{p}: integrity fields")
        s = m["summary"]
        rows.append({
            "seed": m["seed"],
            "observation_count": m["observation_count"],
            "base_unobserved_shoreline_cells": s["base_unobserved_shoreline_cells"],
            "refined": s["refined_unobserved_cells_by_state"],
            "internal_refined": s["internal_refined_cells_by_state"],
            "exterior_refined": s["exterior_refined_cells_by_state"],
        })
    status = "CYCLOPEAN1D_COMPLETE" if not structural else "CYCLOPEAN1D_INTEGRITY_FAIL"
    print("[cyclopean1d-compare]", status,
          json.dumps({"records": rows, "structural_fails": structural}, sort_keys=True))
    raise SystemExit(0 if not structural else 2)


if __name__ == "__main__":
    main()
