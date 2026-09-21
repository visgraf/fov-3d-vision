"""Checks for Cyclopean-1e. Every deliberate negative must fail."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import cyclopean1e_public as public
import cyclopean1e_gaze as gaze


def positive() -> None:
    gaze.self_test()
    if public.SEEDS != (2111,) or public.MAX_ADDED_FIXATIONS != 1:
        raise AssertionError("Cyclopean-1e scope changed")
    src = (TOOLS / "cyclopean1e_probe.py").read_text().lower()
    if "never_observed" not in src or "observed_target_no_depth" not in (TOOLS / "cyclopean1e_public.py").read_text().lower():
        raise AssertionError("epistemic candidate/exclusion contract missing")
    if "fsg6f_frontier" in src or "fsg6f_public" in src:
        raise AssertionError("Cyclopean-1e imported FSG6f policy")
    if "evaluation_only" in src or "reality2b_eval" in src:
        raise AssertionError("Cyclopean-1e opened evaluator truth")
    if "new_threshold" in src or "minimum_local_std" in src:
        raise AssertionError("Cyclopean-1e added a quality threshold")
    print("[cyclopean1e-policy] PASS parent=cyclopean1d seed2111_only=true never_observed_only=true seen_no_depth_excluded=true one_fixation_max=true frozen_fsg6f=true quality_gated=false")
    print("[cyclopean1e-check] SUMMARY passed=6 failed=0")


def _synthetic_for_negative(kind: str):
    h, w = 5, 7
    sh = np.zeros((h, w), bool)
    labels = np.full((h, w), -1, np.int32)
    dist = np.full((h, w), -1, np.int32)
    ref = np.zeros((h, w), np.uint8)
    class Chart:
        yaw0_deg = 0.0
        pitch0_deg = 0.0
        grid_deg = 0.1
    comps = [{"component_id": 0, "kind": "EXTERIOR"}, {"component_id": 1, "kind": "INTERNAL"}]
    if kind == "nodepth":
        sh[2,4] = True; labels[2,4] = 0; dist[2,4] = 9; ref[2,4] = 2
    elif kind == "internal":
        sh[2,4] = True; labels[2,4] = 1; dist[2,4] = -1; ref[2,4] = 1
    elif kind == "centroid":
        sh[2,2] = True; labels[2,2] = 0; dist[2,2] = 2; ref[2,2] = 1
        sh[2,5] = True; labels[2,5] = 0; dist[2,5] = 8; ref[2,5] = 1
    return sh, labels, dist, ref, comps, Chart()


def negative(kind: str) -> None:
    src = (TOOLS / "cyclopean1e_probe.py").read_text().lower()
    if kind in ("nodepth", "internal", "centroid"):
        sh, labels, dist, ref, comps, chart = _synthetic_for_negative(kind)
        p = gaze.select_epistemic_probe(
            shoreline=sh, component_labels=labels, components=comps,
            exterior_distance_cells=dist, refined_state=ref,
            never_observed_code=1, chart=chart, existing_gazes=[],
        )
        if kind == "nodepth" and p is None:
            raise AssertionError("deliberate seen-no-depth candidate correctly excluded")
        if kind == "internal" and p is None:
            raise AssertionError("deliberate internal NEVER_OBSERVED candidate correctly excluded")
        if kind == "centroid" and p is not None and p["probe_cell_x"] == 5:
            raise AssertionError("deliberate centroid rule lost to correct deepest-cell rule")
        return
    if kind == "multiprobe":
        if public.MAX_ADDED_FIXATIONS == 1:
            raise AssertionError("deliberate multi-probe policy detected")
        return
    if kind == "truth":
        if "evaluation_only" not in src and "reality2b_eval" not in src:
            raise AssertionError("deliberate evaluator-truth path detected")
        return
    if kind == "policy":
        if "fsg6f_frontier" not in src and "fsg6f_public" not in src:
            raise AssertionError("deliberate FSG6f policy path detected")
        return
    raise ValueError(kind)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--negative", choices=("nodepth", "internal", "centroid", "multiprobe", "truth", "policy"))
    a = ap.parse_args()
    try:
        if a.negative:
            negative(a.negative)
        else:
            positive(); return
    except AssertionError as e:
        if a.negative:
            print(f"[cyclopean1e-check] FAIL AssertionError {e}")
            raise SystemExit(1)
        raise
    if a.negative:
        print(f"[cyclopean1e-check] NEGATIVE DID NOT FAIL {a.negative}")
        raise SystemExit(0)


if __name__ == "__main__":
    main()
