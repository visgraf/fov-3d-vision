"""Host-side check of the analysis in tools/noise_floor.py, on synthetic data with known answers.

    python tools/check_noise_floor_stats.py

Needs only numpy. It imports the analysis functions from noise_floor.py, which import
nothing from Blender; the Blender-side path (rendering, reading tiles back, the two
--control modes) can only be exercised on the workstation.

Checks, each with a known answer and a tolerance that a wrong implementation misses:
  1. sigma recovers the true noise of a synthetic pair to 2 %, and is independent of the
     image content (the mean cancels).
  2. rel_p99 and rel_rms are on the same scale: for Gaussian per-channel noise their ratio
     is the p99 of a 3-dof chi distribution over sqrt(3), 1.944; the old mean-absolute
     per_px gave 1.74 (measured here), i.e. the statistic this replaces.
  3. The identical-seed guard fires on a same-seed pair and stays silent on a real pair.
  4. fit_timing recovers the slope of seconds = max(floor, b*spp) + noise to 3 %, reports
     the floor, and does not let a warm-up on tile 0 poison the result; the old straight
     a + b*spp fit on the same data is shown to be wrong about the intercept.
  5. choose_spp picks the smallest measured spp meeting the target, and extrapolates when
     none does, with the extrapolated rel_rms landing on the target.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from noise_floor import (check_pair_differs, choose_spp, fit_timing,  # noqa: E402
                         noise_from_pair, sqrt2_check)

failures = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"[{'ok' if ok else 'FAIL'}] {name}: {detail}")
    if not ok:
        failures.append(name)


rng = np.random.default_rng(0)
H, W = 96, 128
truth = 0.2 + 0.6 * rng.random((H, W, 3)).astype(np.float32)   # arbitrary image content

# 1. sigma
sig = 0.05
a = truth + rng.normal(0, sig, truth.shape).astype(np.float32)
b = truth + rng.normal(0, sig, truth.shape).astype(np.float32)
st = noise_from_pair(a, b)
check("sigma recovers known noise", abs(st["sigma"] - sig) / sig < 0.02,
      f"sigma {st['sigma']:.5f} vs true {sig}")
a2 = truth * 3 + rng.normal(0, sig, truth.shape).astype(np.float32)
b2 = truth * 3 + rng.normal(0, sig, truth.shape).astype(np.float32)
st2 = noise_from_pair(a2, b2)
check("sigma independent of content", abs(st2["sigma"] - sig) / sig < 0.02,
      f"sigma {st2['sigma']:.5f} on 3x brighter content; rel_rms {st2['rel_rms']:.4f} vs "
      f"{st['rel_rms']:.4f} (should be 1/3: {st2['rel_rms'] * 3 / st['rel_rms']:.3f})")

# 2. same scale
ratio = st["rel_p99"] / st["rel_rms"]
# p99 of sqrt(chi2_3 / 3): chi2_3 p99 = 11.345
expected = math.sqrt(11.345 / 3.0)
diff = (a - b)
old_per_px = np.abs(diff).mean(-1) / math.sqrt(2.0)
old_ratio = np.percentile(old_per_px, 99) / st["sigma"]
check("rel_p99 on the sigma scale", abs(ratio - expected) < 0.06,
      f"p99/rms {ratio:.3f}, expected {expected:.3f} for Gaussian; old mean-abs statistic gave {old_ratio:.3f}")

# 3. guard
same = noise_from_pair(a, a + np.float32(1e-7) * rng.standard_normal(a.shape).astype(np.float32))
fired = False
try:
    check_pair_differs(same, (0, 0))
except RuntimeError:
    fired = True
check("guard fires on identical renders", fired, f"rel_rms {same['rel_rms']:.3g}")
quiet = True
try:
    check_pair_differs(st, (0, 1))
except RuntimeError:
    quiet = False
check("guard silent on a real pair", quiet, f"rel_rms {st['rel_rms']:.3g}")

# 4. timing fit
spps = [16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]
floor, b_true = 0.030, 1.5e-4
rows = []
for ti in range(6):
    px = 16384 if ti % 2 == 0 else 16256
    for i, spp in enumerate(spps):
        t = max(floor, b_true * spp * px / 16384) * (1 + 0.02 * rng.standard_normal())
        rows.append({"tile": ti, "spp": spp, "seconds": t, "pixels": px})
timing = fit_timing(rows, 256)
ns = timing["ns_per_pixel_sample"]
ns_true = b_true / 16384 * 1e9
check("slope recovered from linear regime", abs(ns["median"] - ns_true) / ns_true < 0.03,
      f"{ns['median']:.3f} ns/px-sample vs true {ns_true:.3f}; spread {ns['spread_frac_of_median']:.1%}")
fl = timing["floor_seconds"]
check("floor reported", abs(fl["median"] - floor) / floor < 0.05,
      f"{fl['median']:.4f}s vs true {floor}")
old_a = [np.polyfit([x["spp"] for x in rows if x["tile"] == t],
                    [x["seconds"] for x in rows if x["tile"] == t], 1)[1] for t in range(6)]
check("old straight-line intercept is wrong (documenting why it was replaced)",
      abs(np.median(old_a) - floor) / floor > 0.3,
      f"old a + b*spp intercept {np.median(old_a):.4f}s vs floor {floor} "
      f"({abs(np.median(old_a) - floor) / floor:.0%} off)")

# 5. choice
by = {s: {"rel_rms_median": 0.12 * math.sqrt(16 / s), "rel_rms_worst": 0.15 * math.sqrt(16 / s)}
      for s in spps}
ch = choose_spp(by, spps, 0.03)
check("choose smallest measured spp meeting target", ch["how"] == "measured" and ch["spp"] == 512,
      f"chose {ch['spp']} ({ch['how']}); worst at 256 {by[256]['rel_rms_worst']:.4f}, at 512 {by[512]['rel_rms_worst']:.4f}")
ch2 = choose_spp(by, spps, 0.005)
implied = by[8192]["rel_rms_worst"] * math.sqrt(8192 / ch2["unrounded_spp"])
check("extrapolate when no spp meets target", ch2["how"].startswith("assumed") and abs(implied - 0.005) < 1e-9
      and ch2["spp"] == 16384, f"needs {ch2['unrounded_spp']:.0f} -> {ch2['spp']} spp, implied rel_rms {implied:.4f}")
sc = sqrt2_check(by)
check("sqrt2 check passes on 1/sqrt(spp) data", sc["ok"] is True, f"median normalised ratio {sc['median']}")
by_bad = {s: {"rel_rms_median": 0.12 * (16 / s) ** 0.25, "rel_rms_worst": 0.15} for s in spps}
check("sqrt2 check flags spp^-1/4 scaling", sqrt2_check(by_bad)["ok"] is False,
      f"median normalised ratio {sqrt2_check(by_bad)['median']}")

print()
if failures:
    print(f"FAILED: {len(failures)} check(s): {failures}")
    sys.exit(1)
print("all checks passed")
