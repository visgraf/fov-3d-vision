"""Aggregate the four prospectively fixed full FSG5 curved-surface trials."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import cv2

import fsg5_public as public
from fsg_geometry import json_write

EXPECTED = {(f, s) for f in public.FIXTURES for s in public.SEEDS}


def write_visual(path: Path, rows: list[dict]) -> None:
    W, H = 720, 190 * len(rows)
    canvas = np.full((H, W, 3), 245, np.uint8)
    for j, r in enumerate(rows):
        y0 = j * 190
        cv2.putText(canvas, f"{r['fixture']} seed {r['seed']}", (20, y0 + 22), cv2.FONT_HERSHEY_SIMPLEX, .55, (20,20,20), 1, cv2.LINE_AA)
        cv2.rectangle(canvas, (55, y0 + 42), (685, y0 + 160), (210,210,210), 1)
        c = r["truth_coverage_by_fixation"]
        pts = [(55 + int(i * 630 / max(1, len(c)-1)), int(y0 + 160 - float(v) * 118)) for i, v in enumerate(c)]
        for p, q in zip(pts[:-1], pts[1:]): cv2.line(canvas, p, q, (30,30,30), 2)
        for p in pts: cv2.circle(canvas, p, 3, (30,30,30), -1)
        cv2.putText(canvas, f"final {100*c[-1]:.1f}%  med/p95 {1000*r['map_surface_median_m']:.1f}/{1000*r['map_surface_p95_m']:.1f} mm",
                    (55, y0 + 182), cv2.FONT_HERSHEY_SIMPLEX, .45, (20,20,20), 1, cv2.LINE_AA)
    cv2.imwrite(str(path), canvas)


def compare(metric_files: list[Path], out: Path) -> dict:
    out = out.resolve()
    if out.exists():
        raise FileExistsError("comparison output must be new")
    rows = []; seen = set()
    for p in metric_files:
        r = json.loads(p.resolve().read_text()); key = (r["fixture"], int(r["seed"]))
        if key in seen:
            raise ValueError("duplicate FSG5 trial")
        seen.add(key); rows.append(r)
    if seen != EXPECTED:
        raise ValueError(f"FSG5 full set incomplete: got {sorted(seen)} expected {sorted(EXPECTED)}")
    rows.sort(key=lambda r: (r["fixture"], r["seed"]))
    fails = []
    for r in rows:
        if r["profile"] != "full": fails.append(f"{r['fixture']}/{r['seed']} is not full profile")
        if r["status"] != "FSG5_CURVED_RUN_PASS" or r["fails"]:
            fails.append(f"{r['fixture']}/{r['seed']} curved run failed")
    final_cov = [float(r["truth_coverage_final"]) for r in rows]
    med = [float(r["map_surface_median_m"]) for r in rows]
    p95 = [float(r["map_surface_p95_m"]) for r in rows]
    bias = [float(r["supported_signed_radial_median_m"]) for r in rows]
    result = {
        "schema": "FSG5-comparison-v1",
        "trials": rows,
        "trial_passes": sum(not r["fails"] for r in rows),
        "mean_final_coverage": float(np.mean(final_cov)),
        "surface_median_range_m": [float(np.min(med)), float(np.max(med))],
        "surface_p95_range_m": [float(np.min(p95)), float(np.max(p95))],
        "supported_signed_radial_median_range_m": [float(np.min(bias)), float(np.max(bias))],
        "fails": fails,
        "status": "FSG5_INCREMENT5_PASS" if not fails else "FSG5_INCREMENT5_FAIL",
    }
    out.mkdir(parents=True)
    json_write(out / "comparison.json", result)
    write_visual(out / "coverage_curved.png", rows)
    print("[fsg5-compare] " + result["status"], json.dumps(result, sort_keys=True), flush=True)
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("metrics", nargs=4, type=Path)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    r = compare(a.metrics, a.out)
    raise SystemExit(0 if not r["fails"] else 2)


if __name__ == "__main__":
    main()
