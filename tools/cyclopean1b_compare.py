"""Aggregate completed Cyclopean-1b shoreline audits without a quality gate."""
from __future__ import annotations
import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("records", nargs="+")
    args = ap.parse_args()
    rows = []
    structural = []
    for p in map(Path, args.records):
        m = json.loads((p / "prediction_manifest.json").read_text())
        if (m.get("schema") != "Cyclopean1b-boundary-audit-v1" or
                m.get("truth_opened") is not False or
                m.get("acquisitions_added") != 0 or
                m.get("parent_files_modified") is not False):
            structural.append(f"{p}: integrity")
            continue
        s = m["summary"]
        rows.append({"seed": m["seed"], **s})
    status = "CYCLOPEAN1B_COMPLETE" if not structural else "CYCLOPEAN1B_INTEGRITY_FAIL"
    print("[cyclopean1b-compare]", status,
          json.dumps({"records": rows, "structural_fails": structural}, sort_keys=True))
    raise SystemExit(0 if not structural else 2)


if __name__ == "__main__":
    main()
