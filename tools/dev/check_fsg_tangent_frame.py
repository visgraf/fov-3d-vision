"""Regression check for the FSG 360-degree baseline-projected tangent frame."""
from __future__ import annotations

from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fsg_geometry import make_calibration
from fsg_stereo import rectification

SELECTED = (179.912109375, -89.912109375)
LEGACY = ((0.0, 0.0), (14.0, -7.0), (-24.0, 11.0))
YAWS = (-179.9, -150.0, -120.0, -90.1, -89.9, -60.0, 0.0,
        60.0, 89.9, 90.1, 120.0, 150.0, 179.9)
PITCHES = (-89.9, -80.0, -45.0, 0.0, 45.0, 80.0, 89.9)


def main() -> None:
    fails: list[str] = []

    # Backward compatibility: omitting tangent_frame must remain exactly the
    # legacy calibration prescription for the historical FSG operating region.
    for yaw, pitch in LEGACY:
        a = make_calibration("small", yaw, pitch)
        b = make_calibration("small", yaw, pitch, tangent_frame="legacy_upright")
        if a != b:
            fails.append(f"legacy output changed at ({yaw},{pitch})")

    cases = [(y, p) for p in PITCHES for y in YAWS]
    cases.append(SELECTED)
    checked = 0
    for yaw, pitch in cases:
        try:
            c = make_calibration("small", yaw, pitch,
                                 tangent_frame="baseline_projected")
            r = rectification(c)
        except Exception as e:
            fails.append(f"non-degenerate case refused ({yaw},{pitch}): {type(e).__name__}: {e}")
            continue
        p2 = np.asarray(r["P2"], float)
        if abs(float(p2[1, 3])) > 1e-7 or not float(p2[0, 3]) < 0:
            fails.append(f"noncanonical rectification ({yaw},{pitch}) P2=({p2[0,3]},{p2[1,3]})")
        for eye in c["eyes"]:
            x = np.asarray(eye["R_hc"], float)[:, 0]
            if not float(np.dot(x, np.array([1.0, 0.0, 0.0]))) > 0:
                fails.append(f"camera +X opposes baseline ({yaw},{pitch}) {eye['name']}")
        checked += 1

    for yaw in (-90.0, 90.0):
        try:
            make_calibration("small", yaw, 0.0,
                             tangent_frame="baseline_projected")
        except ValueError as e:
            if "stereo baseline" not in str(e):
                fails.append(f"wrong degeneracy error at ({yaw},0): {e}")
        else:
            fails.append(f"physical look-along-baseline degeneracy accepted at ({yaw},0)")

    for f in fails:
        print("[fsg-tangent-frame] FAIL", f)
    print(f"[fsg-tangent-frame] SUMMARY checked={checked} failed={len(fails)} selected={SELECTED}")
    raise SystemExit(1 if fails else 0)


if __name__ == "__main__":
    main()
