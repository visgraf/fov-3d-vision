"""Apply the Classroom-Oracle-2 controller-domain ablation.

The helper mutates only the four angular extent entries in
``fsg6f_public.SURFACE_FRONTIER``.  Call it before importing the inherited
controller adapters so any import-time derived state sees the widened domain.
"""
from __future__ import annotations

import copy
import json
from typing import Any

import classroom_oracle2_public as public

DOMAIN_KEYS = ("yaw_min_deg", "yaw_max_deg", "pitch_min_deg", "pitch_max_deg")


def _same(a: Any, b: Any) -> bool:
    try:
        return json.dumps(a, sort_keys=True, default=repr) == json.dumps(b, sort_keys=True, default=repr)
    except TypeError:
        return repr(a) == repr(b)


def _domain_from(cfg: dict) -> dict[str, float]:
    return {k: float(cfg[k]) for k in DOMAIN_KEYS}


def apply_wide_domain() -> dict[str, Any]:
    import fsg6f_public as frozen

    cfg = frozen.SURFACE_FRONTIER
    before = copy.deepcopy(cfg)
    before_domain = _domain_from(cfg)
    expected = public.ORIGINAL_DOMAIN
    wide = public.WIDE_DOMAIN

    if before_domain != expected and before_domain != wide:
        raise RuntimeError(
            "unexpected inherited FSG6f domain before Oracle-2 override: "
            f"got {before_domain}, expected {expected}"
        )

    for key, value in wide.items():
        cfg[key] = float(value)

    after = copy.deepcopy(cfg)
    after_domain = _domain_from(cfg)
    if after_domain != wide:
        raise RuntimeError(f"failed to install wide domain: {after_domain}")

    changed = []
    keys = sorted(set(before) | set(after))
    for key in keys:
        if not _same(before.get(key), after.get(key)):
            changed.append(key)
    if before_domain == expected and sorted(changed) != sorted(DOMAIN_KEYS):
        raise RuntimeError(
            "Oracle-2 changed more than the four domain bounds: " + ", ".join(changed)
        )
    if before_domain == wide and changed:
        raise RuntimeError("idempotent wide-domain activation unexpectedly changed config")

    return {
        "before_domain": before_domain,
        "after_domain": after_domain,
        "changed_keys": changed,
        "only_domain_extent_changed": (before_domain == wide and not changed)
        or sorted(changed) == sorted(DOMAIN_KEYS),
    }


def assert_wide_domain() -> None:
    import fsg6f_public as frozen
    got = _domain_from(frozen.SURFACE_FRONTIER)
    if got != public.WIDE_DOMAIN:
        raise RuntimeError(f"controller domain is not widened: {got}")


if __name__ == "__main__":
    audit = apply_wide_domain()
    assert_wide_domain()
    print("[classroom-oracle2-domain] PASS", json.dumps(audit, sort_keys=True))
