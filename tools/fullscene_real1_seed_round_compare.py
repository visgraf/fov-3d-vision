"""Structural comparator for one-round visible-seed recovery."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import fullscene_real1_seed_round_public as public

def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("out", type=Path); a=ap.parse_args()
    m=json.loads((a.out/"seed_recovery_manifest.json").read_text())
    fails=[]
    if m.get("schema") != public.SPEC_ID: fails.append("schema")
    if not m.get("one_round_complete"): fails.append("one_round")
    if m.get("growth_actions") != 0: fails.append("growth")
    if m.get("audit_actions") != 0 or m.get("handoff_actions") != 0: fails.append("extra_control")
    if m.get("truth_opened") is not False: fails.append("truth")
    for t in m.get("targets", []):
        if int(t.get("probe_count", -1)) != 8: fails.append("probe_count")
    print("FULLSCENE_REAL1_SEED_ROUND_COMPLETE structural_fails:", fails)
    raise SystemExit(1 if fails else 0)
if __name__ == "__main__": main()
