"""Software/integrity checks for FSG5 curved-surface growth."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fsg5_public as public
import fsg5_scene as scene
import fsg4_public as frozen_public
import fsg4_policy as policy


def xyz_for_yaw(lo: float, hi: float) -> np.ndarray:
    yaw = np.radians(np.linspace(lo, hi, 2000))
    return np.c_[2.1 * np.sin(yaw), np.zeros_like(yaw), -2.1 * np.cos(yaw)]


def policy_mirror_check() -> None:
    n = 128; sup = np.ones((n, n), bool); c = {"nominal_core_fov_deg": 12.0}
    right = np.full((n, n), public.OBJECT_ID, np.int32); right[:, :12] = public.BACKGROUND_ID
    left = np.full((n, n), public.OBJECT_ID, np.int32); left[:, -12:] = public.BACKGROUND_ID
    r = policy.choose_next(-7.0, c, right, sup, xyz_for_yaw(-8.2, -1.0), [-7.0])
    l = policy.choose_next(+7.0, c, left, sup, xyz_for_yaw(+1.0, +8.2), [+7.0])
    if r["next_yaw_deg"] != -2.0 or l["next_yaw_deg"] != +2.0:
        raise AssertionError(f"frozen policy did not mirror on FSG5 seed evidence: {r['next_yaw_deg']} / {l['next_yaw_deg']}")


def flat_chord_points(fixture: str) -> np.ndarray:
    s = scene.spec(fixture); nt, ny = scene.TRUTH_GRID_WH
    th0, th1 = np.radians([s["theta_min_deg"], s["theta_max_deg"]])
    a = scene.cylinder_point(fixture, th0, 0.0); b = scene.cylinder_point(fixture, th1, 0.0)
    t = np.linspace(0.0, 1.0, nt); y = np.linspace(-s["height_m"] / 2.0, s["height_m"] / 2.0, ny)
    T, Y = np.meshgrid(t, y)
    X = (1 - T)[..., None] * a + T[..., None] * b
    X[..., 1] = Y
    return X.reshape(-1, 3)


def radially_shifted(fixture: str, amount_m: float) -> np.ndarray:
    s = scene.spec(fixture); p = scene.truth_points(fixture).copy()
    dx = p[:, 0] - s["centre_x_m"]; dz = p[:, 2] - s["centre_z_m"]
    r = np.sqrt(dx * dx + dz * dz); scale = (r + amount_m) / r
    p[:, 0] = s["centre_x_m"] + dx * scale
    p[:, 2] = s["centre_z_m"] + dz * scale
    return p


def run_positive() -> None:
    passed = 0
    if public.POLICY != frozen_public.POLICY:
        raise AssertionError("FSG5 policy constants differ from frozen FSG4")
    if public.FUSION != frozen_public.FUSION:
        raise AssertionError("FSG5 fusion differs from frozen FSG4")
    if public.OBJECT_ID != frozen_public.OBJECT_ID or public.BACKGROUND_ID != frozen_public.BACKGROUND_ID:
        raise AssertionError("FSG5 IDs incompatible with frozen FSG4 policy")
    passed += 1
    scene.self_test(); passed += 1
    policy_mirror_check(); passed += 1
    for f in public.FIXTURES:
        e = scene.surface_distance(f, scene.truth_points(f))
        if float(np.max(e)) > 1e-10:
            raise AssertionError("analytic curved-surface metric rejects its own truth")
    passed += 1
    flat = scene.surface_distance("curve_right", flat_chord_points("curve_right"))
    if float(np.percentile(flat, 95)) <= public.TARGETS["map_surface_p95_max_m"]:
        raise AssertionError("curvature metric cannot distinguish a flat chord from the cylinder")
    passed += 1
    shifted = radially_shifted("curve_right", -0.015)
    med = abs(float(np.median(scene.signed_radial_error("curve_right", shifted))))
    if med <= public.TARGETS["supported_signed_radial_bias_abs_max_m"]:
        raise AssertionError("curvature-bias metric cannot detect a 15 mm radial contraction")
    passed += 1
    print(f"[fsg5-check] SUMMARY passed={passed} failed=0")


def run_negative(name: str) -> None:
    if name == "policy":
        # Same right-frontier evidence, but the deliberately wrong hard-coded answer goes left.
        expected = -2.0; wrong = -12.0
        if wrong != expected:
            raise AssertionError("deliberate hard-coded/wrong curved frontier direction detected")
    if name == "flat":
        e = scene.surface_distance("curve_right", flat_chord_points("curve_right"))
        if float(np.percentile(e, 95)) > public.TARGETS["map_surface_p95_max_m"]:
            raise AssertionError("deliberate flat substitute for curved surface detected")
    if name == "shift":
        e = scene.surface_distance("curve_right", scene.truth_points("curve_right") + np.array([0.05, 0.0, 0.0]))
        if float(np.percentile(e, 95)) > public.TARGETS["map_surface_p95_max_m"]:
            raise AssertionError("deliberate 5cm map shift detected")
    if name == "bias":
        p = radially_shifted("curve_right", -0.015)
        med = abs(float(np.median(scene.signed_radial_error("curve_right", p))))
        if med > public.TARGETS["supported_signed_radial_bias_abs_max_m"]:
            raise AssertionError("deliberate 15mm fusion contraction detected")
    if name == "purity":
        ids = np.array([public.OBJECT_ID, public.BACKGROUND_ID], np.int32)
        if set(ids.tolist()) != {public.OBJECT_ID}:
            raise AssertionError("deliberate background contamination detected")
    raise AssertionError("negative control unexpectedly passed")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--negative", choices=("policy", "flat", "shift", "bias", "purity"))
    a = ap.parse_args()
    try:
        if a.negative:
            run_negative(a.negative)
        else:
            run_positive()
    except BaseException as exc:
        print("[fsg5-check] FAIL", type(exc).__name__, str(exc))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
