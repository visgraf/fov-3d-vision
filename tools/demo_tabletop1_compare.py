"""Structural comparator for Demo-Tabletop-1 outputs."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import demo_tabletop1_public as public


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out", type=Path)
    a = ap.parse_args()
    m = json.loads((a.out / "demo_manifest.json").read_text())
    fails = []
    if m.get("schema") != public.SPEC_ID: fails.append("schema")
    if not m.get("oracle_assisted_demo"): fails.append("oracle_flag")
    if not m.get("truth_available_to_control"): fails.append("truth_flag")
    if m.get("discovery_tested") is not False: fails.append("discovery_claim")
    roles = {r.get("role") for r in m.get("object_rows", [])}
    if "STEREO_FOREGROUND" not in roles: fails.append("no_foreground")
    if "BACKGROUND_SCAFFOLD" not in roles: fails.append("no_background")
    print("DEMO_TABLETOP1_COMPLETE structural_fails:", fails)
    raise SystemExit(1 if fails else 0)

if __name__ == "__main__": main()
